"""Generate accelerator code for an independent design run."""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from accagent.framework.sacg_store import SACGStore
from accagent.framework.sacg_utils import (
    add_constraint,
    add_invariant,
    artifact_path,
    constraint_facts,
    copy_state,
    read_json,
    require_promoted_artifacts,
    run_dir_from_state,
    safe_id,
    stage_status_allows_promotion,
    write_json,
)
from accagent.framework.stage_entry import run_sacg_stage
from accagent.framework.stage_llm import run_stage_agent
from accagent.framework.stage_team import run_design_team, team_failure_errors, team_summary


TOUCHED_CONSTRAINTS = [
    "constraint.codegen.package",
    "constraint.codegen.compile_gate",
    "constraint.codegen.contract_check",
    "constraint.memory.board",
    "constraint.runtime.board",
    "constraint.deployment.board",
]


def scalar(value: Any, default: int) -> int:
    if isinstance(value, dict) and "value" in value:
        value = value.get("value")
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def dtype_bits(dtype: Any, default: int) -> int:
    text = str(dtype or "").strip().upper().replace("_", "")
    if text in {"FP16", "FLOAT16", "HALF", "BF16", "BFLOAT16"}:
        return 16
    if text in {"FP32", "FLOAT32", "SINGLE"}:
        return 32
    if text in {"FP64", "FLOAT64", "DOUBLE"}:
        return 64
    for prefix in ["UINT", "INT", "U", "I"]:
        if text.startswith(prefix):
            suffix = text[len(prefix):]
            if suffix.isdigit():
                return int(suffix)
    return default


def numeric_default_bits(state: dict[str, Any], field: str, default: int) -> int:
    try:
        numeric = constraint_facts(state, "constraint.numeric.policy")
    except KeyError:
        return default
    rules = numeric.get("default_rules", {}) if isinstance(numeric.get("default_rules"), dict) else {}
    return dtype_bits(rules.get(field) or numeric.get(field), default)


def model_block_class(model_type: str | None) -> str:
    value = (model_type or "").lower()
    if "llama" in value or "qwen" in value:
        return "LlamaStyleBlock"
    if "gemma" in value:
        return "Gemma3TextBlock"
    if "gpt" in value:
        return "GPT2PreLNBlock"
    return "OPTPreLNBlock"


def model_param_class(model_type: str | None) -> str:
    value = (model_type or "").lower()
    if "llama" in value or "qwen" in value:
        return "LlamaStyleBlockParams"
    if "gemma" in value:
        return "Gemma3TextBlockParams"
    return "DecoderBlockParams"


def quote_list(values: list[str]) -> str:
    return ", ".join(f'"{value}"' for value in values)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stage_summary_lines(plan: dict[str, Any]) -> list[str]:
    return [
        f"{stage['index']}: {stage['stage_id']} op={stage['op']} template={stage['template_id']}"
        for stage in plan.get("stages", [])
    ]


def stage_params_by_op(bindings: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result = {}
    for item in bindings.get("bindings", []):
        if isinstance(item, dict) and item.get("op"):
            result[str(item["op"])] = item.get("params", {}) if isinstance(item.get("params"), dict) else {}
    return result


def first_param(params_by_op: dict[str, dict[str, Any]], names: list[str], default: int) -> int:
    for params in params_by_op.values():
        for name in names:
            value = params.get(name)
            if value is not None:
                return scalar(value, default)
    return default


def align_up(value: int, alignment: int) -> int:
    if alignment <= 1:
        return value
    return ((value + alignment - 1) // alignment) * alignment


def bytes_for_elements(elements: int, bits: int) -> int:
    return (max(0, elements) * max(1, bits) + 7) // 8


def allocate_region(regions: list[dict[str, Any]], name: str, size_bytes: int, alignment: int, role: str, meta: dict[str, Any]) -> None:
    base = align_up(regions[-1]["base_addr"] + regions[-1]["size_bytes"], alignment) if regions else 0
    regions.append(
        {
            "name": name,
            "role": role,
            "base_addr": base,
            "size_bytes": align_up(max(size_bytes, alignment), alignment),
            "alignment_bytes": alignment,
            "meta": meta,
        }
    )


def build_memory_layout(state: dict[str, Any], bindings: dict[str, Any], generated_package: dict[str, Any]) -> dict[str, Any]:
    model = constraint_facts(state, "constraint.model.decoder")
    memory = constraint_facts(state, "constraint.memory.board")
    params = generated_package["params"]
    num_layers = scalar(model.get("num_layers"), 1)
    seq_len = params["max_seq_len"]
    hidden = params["hidden_size"]
    intermediate = params["intermediate_size"]
    q_heads = params["num_q_heads"]
    kv_heads = params["num_kv_heads"]
    head_dim = params["head_dim"]
    input_bits = params["input_bits"]
    elem_bits = params["elem_bits"]
    output_bits = params["output_bits"]
    memory_system = memory.get("memory_system", {}) if isinstance(memory.get("memory_system"), dict) else memory
    axi_bits = scalar(memory_system.get("axi_data_width_bits"), params["lanes"] * input_bits)
    alignment = max(1, axi_bits // 8)
    token_hidden = seq_len * hidden
    qkv_elements = hidden * ((q_heads + 2 * kv_heads) * head_dim)
    out_proj_elements = hidden * hidden
    ffn_elements = hidden * intermediate * 2 + intermediate * hidden
    norm_elements = hidden * 2
    per_layer_weight_bytes = bytes_for_elements(qkv_elements + out_proj_elements + ffn_elements, elem_bits) + bytes_for_elements(norm_elements, input_bits)
    activation_bytes = bytes_for_elements(token_hidden, input_bits)
    output_bytes = bytes_for_elements(token_hidden, output_bits)
    intermediate_bytes = bytes_for_elements(seq_len * intermediate, elem_bits)
    regions: list[dict[str, Any]] = []
    allocate_region(regions, "input_tokens", activation_bytes, alignment, "activation_input", {"seq_len": seq_len, "hidden_size": hidden, "bits": input_bits})
    allocate_region(regions, "output_tokens", output_bytes, alignment, "activation_output", {"seq_len": seq_len, "hidden_size": hidden, "bits": output_bits})
    allocate_region(regions, "activation_ping", max(activation_bytes, intermediate_bytes), alignment, "activation_buffer", {"buffer": "ping"})
    allocate_region(regions, "activation_pong", max(activation_bytes, intermediate_bytes), alignment, "activation_buffer", {"buffer": "pong"})
    allocate_region(regions, "weight_buffer_a", per_layer_weight_bytes, alignment, "weight_buffer", {"double_buffer": "a", "bits": elem_bits})
    allocate_region(regions, "weight_buffer_b", per_layer_weight_bytes, alignment, "weight_buffer", {"double_buffer": "b", "bits": elem_bits})
    allocate_region(regions, "runtime_status", alignment, alignment, "runtime_status", {"status_words": alignment // 4 if alignment >= 4 else 1})
    return {
        "schema_version": "spatialaccagent.memory_layout.v0",
        "design_id": state.get("design_id"),
        "layout_policy": "aligned_static_regions_with_double_buffered_layer_weights",
        "num_layers": num_layers,
        "axi_data_width_bits": axi_bits,
        "alignment_bytes": alignment,
        "element_bits": {
            "block_input_bits": input_bits,
            "internal_elem_bits": elem_bits,
            "block_output_bits": output_bits,
        },
        "tensor_shape": {
            "seq_len": seq_len,
            "hidden_size": hidden,
            "intermediate_size": intermediate,
            "num_q_heads": q_heads,
            "num_kv_heads": kv_heads,
            "head_dim": head_dim,
        },
        "regions": regions,
        "total_bytes": regions[-1]["base_addr"] + regions[-1]["size_bytes"] if regions else 0,
        "transfer_rules": [
            "all addresses are byte offsets from the accelerator DDR window base",
            "all transfer byte counts are aligned to axi_data_width_bits",
            "weight_buffer_a and weight_buffer_b alternate by layer to allow prefetch of layer N+1 while layer N computes",
        ],
    }


def build_runtime_config(state: dict[str, Any], memory_layout: dict[str, Any], generated_package: dict[str, Any]) -> dict[str, Any]:
    deployment = constraint_facts(state, "constraint.deployment.board")
    runtime = constraint_facts(state, "constraint.runtime.board")
    return {
        "schema_version": "spatialaccagent.runtime_config.v0",
        "design_id": state.get("design_id"),
        "top_module": generated_package["fpga_wrapper_class"],
        "chisel_top": generated_package["top_class"],
        "params": generated_package["params"],
        "memory_layout": memory_layout,
        "board": deployment.get("board", {}),
        "runtime_interface": runtime,
        "run_sequence": [
            "load input_tokens",
            "load layer 0 weights into weight_buffer_a",
            "start accelerator",
            "prefetch next layer weights into inactive weight buffer while active layer computes",
            "poll runtime_status or done",
            "read output_tokens",
        ],
        "pass_criteria": {
            "required": ["no_deadlock", "done_asserted", "valid_output_bytes"],
            "bit_exact_float_model": False,
        },
    }


def artifact_producer_status(state: dict[str, Any], artifact_id: str) -> str | None:
    producer = None
    for artifact in state.get("artifacts", []):
        if artifact.get("id") == artifact_id:
            producer = artifact.get("producer_transition")
            break
    if not producer:
        return None
    for transition in state.get("transitions", []):
        if transition.get("id") == producer:
            return str(transition.get("status"))
    return None


def region_by_name(memory_layout: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(region.get("name")): region for region in memory_layout.get("regions", []) if isinstance(region, dict)}


def regions_overlap(a: dict[str, Any], b: dict[str, Any]) -> bool:
    a0 = scalar(a.get("base_addr"), 0)
    a1 = a0 + scalar(a.get("size_bytes"), 0)
    b0 = scalar(b.get("base_addr"), 0)
    b1 = b0 + scalar(b.get("size_bytes"), 0)
    return a0 < b1 and b0 < a1


def compile_warning_count(compile_gate: dict[str, Any]) -> int:
    count = 0
    for step in compile_gate.get("steps", []):
        text = f"{step.get('stdout_tail', '')}\n{step.get('stderr_tail', '')}"
        count += text.count("[warn]")
    return count


def build_codegen_contract_check(
    state: dict[str, Any],
    manifest: dict[str, Any],
    generated_package: dict[str, Any],
    memory_layout: dict[str, Any],
    runtime_config: dict[str, Any],
    compile_gate: dict[str, Any],
    log_path: Path,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    model = constraint_facts(state, "constraint.model.decoder")
    shape = constraint_facts(state, "constraint.shape.model")
    memory = constraint_facts(state, "constraint.memory.board")
    template = constraint_facts(state, "constraint.template.library")
    pipeline = read_json(artifact_path(state, "artifact.stage3.pipeline_plan"))
    bindings = read_json(artifact_path(state, "artifact.stage4.parameter_binding"))
    params = generated_package.get("params", {})

    for artifact_id in [
        "artifact.stage2.template_selection",
        "artifact.stage3.pipeline_plan",
        "artifact.stage4.parameter_binding",
    ]:
        status = artifact_producer_status(state, artifact_id)
        if status and status != "promoted":
            errors.append(f"{artifact_id} producer transition is {status}, expected promoted")

    for key, shape_key in [
        ("hidden_size", "hidden_size"),
        ("intermediate_size", "intermediate_size"),
        ("num_q_heads", "num_q_heads"),
        ("num_kv_heads", "num_kv_heads"),
        ("head_dim", "head_dim"),
        ("max_seq_len", "target_max_seq_len"),
    ]:
        if scalar(params.get(key), -1) != scalar(shape.get(shape_key), -2):
            errors.append(f"generated param {key}={params.get(key)} does not match shape.{shape_key}={shape.get(shape_key)}")

    input_bits = scalar(params.get("input_bits"), 0)
    elem_bits = scalar(params.get("elem_bits"), 0)
    output_bits = scalar(params.get("output_bits"), 0)
    expected_input_bits = numeric_default_bits(state, "acc_dtype", 32)
    expected_elem_bits = numeric_default_bits(state, "activation_dtype", 16)
    if input_bits != expected_input_bits:
        errors.append(f"input_bits={input_bits} does not match numeric acc dtype bits={expected_input_bits}")
    if elem_bits != expected_elem_bits:
        errors.append(f"elem_bits={elem_bits} does not match numeric activation dtype bits={expected_elem_bits}")
    if output_bits != input_bits:
        errors.append(f"output_bits={output_bits} must equal input_bits={input_bits} for residual stream consistency")
    if elem_bits > input_bits:
        errors.append(f"elem_bits={elem_bits} exceeds input_bits={input_bits}")

    expected_ops = [str(stage.get("op")) for stage in pipeline.get("stages", [])]
    generated_ops = []
    try:
        params_scala = Path(generated_package["root"]) / "src" / "main" / "scala" / "spatialaccagent" / "generated" / "GeneratedDesignParams.scala"
        params_text = params_scala.read_text(encoding="utf-8")
        generated_ops = [op for op in expected_ops if f'"{op}"' in params_text]
        if len(generated_ops) != len(expected_ops):
            errors.append("GeneratedDesignParams.scala does not contain every pipeline op in order")
    except OSError as exc:
        errors.append(f"failed to read GeneratedDesignParams.scala: {exc}")

    template_src = Path(template.get("template_dir", ""))
    template_dst = Path(generated_package["root"]) / "src" / "main" / "scala" / "spatialaccagent" / "templates"
    for source in template.get("source_files", []):
        source_path = template_src / source
        copied_path = template_dst / Path(source).name
        source_hash = sha256_file(source_path)
        copied_hash = sha256_file(copied_path)
        if not source_hash or not copied_hash:
            errors.append(f"template provenance missing for {source}")
        elif source_hash != copied_hash:
            errors.append(f"copied template hash mismatch for {source}")

    if compile_gate.get("status") != "pass":
        errors.append(f"compile/elaboration gate status is {compile_gate.get('status')}")
    required_compile_labels = [
        "Compile/compile",
        "GeneratedContractCheck",
        "ElaborateGeneratedAccelerator",
        "ElaborateGeneratedAxiDdrTop",
    ]
    command_text = "\n".join(" ".join(step.get("command", [])) for step in compile_gate.get("steps", []))
    for label in required_compile_labels:
        if label not in command_text:
            errors.append(f"compile gate missing required command containing {label}")
    warn_count = compile_warning_count(compile_gate)
    if warn_count:
        errors.append(f"compile/elaboration gate emitted {warn_count} warning marker(s)")

    memory_system = memory.get("memory_system", {}) if isinstance(memory.get("memory_system"), dict) else memory
    axi_bits = scalar(memory_system.get("axi_data_width_bits"), 0)
    alignment = scalar(memory_layout.get("alignment_bytes"), 0)
    if axi_bits and alignment != axi_bits // 8:
        errors.append(f"memory alignment {alignment} does not match axi width {axi_bits}")
    if memory_layout.get("num_layers") != scalar(model.get("num_layers"), 0):
        errors.append(f"memory_layout.num_layers={memory_layout.get('num_layers')} does not match model.num_layers={model.get('num_layers')}")
    bits = memory_layout.get("element_bits", {})
    if bits.get("block_input_bits") != input_bits or bits.get("internal_elem_bits") != elem_bits or bits.get("block_output_bits") != output_bits:
        errors.append("memory layout element_bits do not match generated params")

    regions = memory_layout.get("regions", [])
    by_region = region_by_name(memory_layout)
    for name in ["input_tokens", "output_tokens", "activation_ping", "activation_pong", "weight_buffer_a", "weight_buffer_b", "runtime_status"]:
        if name not in by_region:
            errors.append(f"memory layout missing region {name}")
    for region in regions:
        base = scalar(region.get("base_addr"), -1)
        size = scalar(region.get("size_bytes"), -1)
        if alignment > 0 and (base % alignment != 0 or size % alignment != 0):
            errors.append(f"region {region.get('name')} is not aligned to {alignment} bytes")
        if size <= 0:
            errors.append(f"region {region.get('name')} has non-positive size {size}")
    for index, region in enumerate(regions):
        for other in regions[index + 1:]:
            if regions_overlap(region, other):
                errors.append(f"memory regions overlap: {region.get('name')} and {other.get('name')}")

    ddr_capacity = scalar(memory_system.get("ddr_capacity_bytes"), 0)
    if ddr_capacity and scalar(memory_layout.get("total_bytes"), 0) > ddr_capacity:
        errors.append(f"memory layout total_bytes exceeds DDR capacity {ddr_capacity}")

    if runtime_config.get("memory_layout", {}).get("total_bytes") != memory_layout.get("total_bytes"):
        errors.append("runtime_config memory_layout does not match generated memory_layout")
    if runtime_config.get("top_module") != generated_package.get("fpga_wrapper_class"):
        errors.append("runtime_config top_module does not match generated FPGA wrapper")
    if runtime_config.get("params") != params:
        errors.append("runtime_config params do not match generated params")

    if bindings.get("status") != "ready":
        errors.append(f"parameter binding artifact status is {bindings.get('status')}")
    for item in bindings.get("bindings", []):
        if item.get("status") != "ready":
            errors.append(f"binding for {item.get('stage_id')} is {item.get('status')}")
        if item.get("legality_errors"):
            errors.append(f"binding for {item.get('stage_id')} has legality errors")
        op = str(item.get("op"))
        item_params = item.get("params", {}) if isinstance(item.get("params"), dict) else {}
        if op in {"residual_add_1", "residual_add_2"} and scalar(item_params.get("elem_bits"), -1) != output_bits:
            errors.append(f"{op} elem_bits={item_params.get('elem_bits')} does not match block output_bits={output_bits}")
        if op == "mlp_down_proj" and scalar(item_params.get("output_bits"), -1) != output_bits:
            errors.append(f"{op} output_bits={item_params.get('output_bits')} does not match block output_bits={output_bits}")
        if op in {"rms_norm_1", "rms_norm_2"} and scalar(item_params.get("output_bits"), -1) != elem_bits:
            errors.append(f"{op} output_bits={item_params.get('output_bits')} does not match internal elem_bits={elem_bits}")

    result = {
        "schema_version": "spatialaccagent.codegen_contract_check.v0",
        "status": "pass" if not errors else "fail",
        "checker": "codegen_contract_check",
        "design_id": state.get("design_id"),
        "errors": errors,
        "warnings": warnings,
        "summary": "all code generation contracts passed" if not errors else f"{len(errors)} contract error(s)",
        "checked_contracts": [
            "upstream_transition_status",
            "model_shape_to_generated_params",
            "numeric_policy_to_generated_bits",
            "template_provenance_hashes",
            "compile_and_elaboration_warning_free",
            "memory_layout_alignment_nonoverlap",
            "runtime_config_consistency",
            "parameter_binding_legality",
        ],
        "log_path": str(log_path),
    }
    write_json(log_path, result)
    return result


def build_codegen_package_static_check(manifest: dict[str, Any], log_path: Path) -> dict[str, Any]:
    errors = []
    warnings = []
    root = Path(str(manifest.get("generated_package_root") or ""))
    generated_files = set(str(path) for path in manifest.get("generated_files", []))
    required_files = {
        "generated/chisel/build.sbt",
        "generated/chisel/memory/memory_layout.json",
        "generated/chisel/runtime/runtime_config.json",
        "generated/chisel/src/main/scala/spatialaccagent/generated/GeneratedAcceleratorTop.scala",
        "generated/chisel/src/main/scala/spatialaccagent/generated/GeneratedAxiDdrTop.scala",
        "generated/chisel/src/main/scala/spatialaccagent/generated/GeneratedContractCheck.scala",
        "generated/chisel/src/main/scala/spatialaccagent/generated/GeneratedDesignParams.scala",
        "generated/chisel/src/main/scala/spatialaccagent/generated/GeneratedSACGMetadata.scala",
    }
    if not root.exists():
        errors.append(f"generated_package_root does not exist: {root}")
    missing_files = sorted(required_files - generated_files)
    if missing_files:
        errors.append(f"generated package missing required files: {missing_files}")
    target_status = manifest.get("target_model_artifact_status", {}) if isinstance(manifest.get("target_model_artifact_status"), dict) else {}
    if target_status.get("current_artifacts_match_target") is not True:
        errors.append("target_model_artifact_status.current_artifacts_match_target must be true")
    if target_status.get("missing_for_target"):
        errors.append(f"target model artifacts missing: {target_status.get('missing_for_target')}")
    planned = manifest.get("planned_code_outputs", [])
    bad_status = [
        f"{item.get('id')}={item.get('status')}"
        for item in planned
        if item.get("status") not in {"generated", "pass"}
    ]
    if bad_status:
        errors.append(f"planned_code_outputs have non-ready status: {bad_status}")
    copied_templates = {
        Path(path).name
        for path in generated_files
        if "/spatialaccagent/templates/" in path and path.endswith(".scala")
    }
    manifest_templates = set(str(item) for item in manifest.get("template_sources", []))
    missing_templates = sorted(copied_templates - manifest_templates)
    if missing_templates:
        errors.append(f"manifest.template_sources does not cover copied template files: {missing_templates}")
    if (manifest.get("compile_gate") or {}).get("status") != "pass":
        errors.append(f"compile_gate status is {(manifest.get('compile_gate') or {}).get('status')}")
    if (manifest.get("contract_check") or {}).get("status") != "pass":
        errors.append(f"contract_check status is {(manifest.get('contract_check') or {}).get('status')}")
    result = {
        "schema_version": "spatialaccagent.codegen_package_static_check.v0",
        "checker": "codegen_package_static_check",
        "status": "pass" if not errors else "fail",
        "summary": "generated package manifest is structurally complete" if not errors else f"{len(errors)} package error(s)",
        "errors": errors,
        "warnings": warnings,
        "checked_contracts": [
            "generated_package_required_files",
            "target_artifact_match_explicit",
            "planned_output_status",
            "template_source_coverage",
            "compile_and_contract_gate_status",
        ],
        "log_path": str(log_path),
    }
    write_json(log_path, result)
    return result


def compile_enabled() -> bool:
    value = os.environ.get("SPATIALACC_CODEGEN_COMPILE", "1").strip().lower()
    return value in {"1", "true", "yes", "on"}


def elaborate_enabled() -> bool:
    value = os.environ.get("SPATIALACC_CODEGEN_ELABORATE", "1").strip().lower()
    return value in {"1", "true", "yes", "on"}


def compile_timeout_sec() -> int:
    raw = os.environ.get("SPATIALACC_CODEGEN_COMPILE_TIMEOUT_SEC", "1800").strip()
    try:
        return max(1, int(raw))
    except ValueError:
        return 1800


def run_codegen_compile_gate(root: Path) -> dict[str, Any]:
    log_dir = root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "compile_check.json"
    cache_root = root.parent / ".sbt_codegen_cache"
    sbt_global = cache_root / "sbt"
    sbt_boot = sbt_global / "boot"
    ivy_home = cache_root / "ivy2"
    coursier_cache = cache_root / "coursier"
    started = time.monotonic()
    result: dict[str, Any] = {
        "schema_version": "spatialaccagent.codegen_compile_gate.v0",
        "enabled": compile_enabled(),
        "elaboration_enabled": elaborate_enabled(),
        "commands": [],
        "cwd": str(root),
        "local_sbt_dirs": {
            "sbt_global_base": str(sbt_global),
            "sbt_boot_directory": str(sbt_boot),
            "sbt_ivy_home": str(ivy_home),
            "coursier_cache": str(coursier_cache),
        },
        "timeout_sec": compile_timeout_sec(),
        "returncode": None,
        "status": "not_run",
        "stdout_tail": "",
        "stderr_tail": "",
        "steps": [],
        "duration_sec": 0.0,
        "log_path": str(log_path),
    }
    if not result["enabled"]:
        result["summary"] = "code generation compile gate disabled"
        write_json(log_path, result)
        return result
    commands = [
        ["sbt", "--no-server", "--batch", "--supershell=false", "Compile/compile"],
        ["sbt", "--no-server", "--batch", "--supershell=false", "runMain spatialaccagent.generated.GeneratedContractCheck"],
    ]
    if result["elaboration_enabled"]:
        commands.extend(
            [
                ["sbt", "--no-server", "--batch", "--supershell=false", "runMain spatialaccagent.generated.ElaborateGeneratedAccelerator"],
                ["sbt", "--no-server", "--batch", "--supershell=false", "runMain spatialaccagent.generated.ElaborateGeneratedAxiDdrTop"],
            ]
        )
    result["commands"] = commands
    for path in [sbt_global, sbt_boot, ivy_home, coursier_cache]:
        path.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    local_opts = (
        f"-Dsbt.global.base={sbt_global} "
        f"-Dsbt.boot.directory={sbt_boot} "
        f"-Dsbt.ivy.home={ivy_home} "
        "-Dsbt.server.autostart=false "
        "-Dsbt.server.forcestart=false"
    )
    env["SBT_OPTS"] = f"{env.get('SBT_OPTS', '')} {local_opts}".strip()
    env.setdefault("COURSIER_CACHE", str(coursier_cache))
    try:
        for command in commands:
            proc = subprocess.run(
                command,
                cwd=root,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=result["timeout_sec"],
                check=False,
            )
            step = {
                "command": command,
                "returncode": proc.returncode,
                "status": "pass" if proc.returncode == 0 else "fail",
                "stdout_tail": proc.stdout[-8000:],
                "stderr_tail": proc.stderr[-8000:],
            }
            result["steps"].append(step)
            result["returncode"] = proc.returncode
            result["stdout_tail"] = step["stdout_tail"]
            result["stderr_tail"] = step["stderr_tail"]
            if proc.returncode != 0:
                result["status"] = "fail"
                result["summary"] = f"failed command returncode={proc.returncode}: {' '.join(command)}"
                break
        else:
            result["status"] = "pass"
            result["summary"] = f"completed {len(commands)} compile/elaboration command(s)"
    except FileNotFoundError as exc:
        result["returncode"] = 127
        result["status"] = "fail"
        result["summary"] = f"missing compile tool: {exc}"
    except subprocess.TimeoutExpired as exc:
        result["returncode"] = 124
        result["status"] = "fail"
        result["stdout_tail"] = (exc.stdout or "")[-8000:] if isinstance(exc.stdout, str) else ""
        result["stderr_tail"] = (exc.stderr or "")[-8000:] if isinstance(exc.stderr, str) else ""
        result["summary"] = f"timeout after {result['timeout_sec']}s"
    result["duration_sec"] = time.monotonic() - started
    write_json(log_path, result)
    return result


def codegen_gate_errors(compile_gate: dict[str, Any]) -> list[str]:
    status = compile_gate.get("status")
    if status == "pass":
        return []
    if status == "not_run":
        return ["code generation compile gate did not run"]
    return [f"code generation compile gate failed: {compile_gate.get('summary')}"]


def codegen_contract_errors(contract_check: dict[str, Any]) -> list[str]:
    if contract_check.get("status") == "pass":
        return []
    errors = contract_check.get("errors", [])
    if isinstance(errors, list) and errors:
        return [f"code generation contract check failed: {error}" for error in errors]
    return [f"code generation contract check failed: {contract_check.get('summary')}"]


def codegen_package_errors(package_check: dict[str, Any]) -> list[str]:
    if package_check.get("status") == "pass":
        return []
    errors = package_check.get("errors", [])
    if isinstance(errors, list) and errors:
        return [f"code generation package static check failed: {error}" for error in errors]
    return [f"code generation package static check failed: {package_check.get('summary')}"]


def stage_worker_errors(output: dict[str, Any]) -> list[str]:
    if not output:
        return []
    errors = []
    status = str(output.get("status") or "").strip().lower()
    if not stage_status_allows_promotion(status):
        errors.append(f"code_generation_agent status is {output.get('status')}")
        risks = output.get("risks", [])
        if isinstance(risks, list) and risks:
            errors.append(f"code_generation_agent reported {len(risks)} unresolved risk(s)")
    return errors


def codegen_stage_gate_policy() -> dict[str, Any]:
    return {
        "current_stage_acceptance": [
            "generated package root, Chisel sources, top wrappers, memory layout, runtime config, and contract checker source must exist",
            "compile/elaboration gate must pass every declared SBT command and expose per-command status/returncode",
            "codegen_contract_check must pass upstream transition, model/shape/numeric, template provenance, compile warning, memory layout, runtime config, and parameter legality checks",
            "target_model_artifact_status.current_artifacts_match_target must be true and missing_for_target must be empty",
            "manifest template_sources must cover every template Scala file copied into the generated package",
        ],
        "later_stage_obligations": [
            "VCS/Verilator functional simulation, numerical/model validation, Vivado synthesis/implementation/timing, and board execution are later verification/deployment gates",
            "clock_target_mhz=0 means the board shell clock is unknown; assigning a nonzero target requires board-profile evidence or approval",
            "memory_layout.json and runtime_config.json are generated handoff artifacts; Stage 6+ must validate them against board/runtime tools before hardware pass claims",
        ],
        "risk_classification_rule": "If compile_gate, codegen_contract_check, and codegen_package_static_check pass, do not report resolved current-stage codegen items as risks; later tool obligations belong in proposed_actions.",
    }


def generate_chisel_package(run_dir: Path, state: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    model = constraint_facts(state, "constraint.model.decoder")
    shape = constraint_facts(state, "constraint.shape.model")
    template = constraint_facts(state, "constraint.template.library")
    board = constraint_facts(state, "constraint.deployment.board")
    pipeline = read_json(artifact_path(state, "artifact.stage3.pipeline_plan"))
    bindings = read_json(artifact_path(state, "artifact.stage4.parameter_binding"))

    root = run_dir / "generated" / "chisel"
    template_src = Path(template.get("template_dir", ""))
    template_dst = root / "src" / "main" / "scala" / "spatialaccagent" / "templates"
    generated_dir = root / "src" / "main" / "scala" / "spatialaccagent" / "generated"
    scripts_dir = root / "scripts"
    if root.exists():
        shutil.rmtree(root)
    template_dst.mkdir(parents=True, exist_ok=True)
    for source in template.get("source_files", []):
        src = template_src / source
        if src.exists():
            shutil.copy2(src, template_dst / src.name)

    model_type = str(model.get("model_type") or "unknown")
    top_class = model_block_class(model_type)
    param_class = model_param_class(model_type)
    hidden = scalar(shape.get("hidden_size"), 768)
    intermediate = scalar(shape.get("intermediate_size"), hidden * 4)
    q_heads = scalar(shape.get("num_q_heads"), 12)
    kv_heads = scalar(shape.get("num_kv_heads"), q_heads)
    head_dim = scalar(shape.get("head_dim"), max(1, hidden // max(q_heads, 1)))
    max_seq = scalar(shape.get("target_max_seq_len"), 16)
    global_params = bindings.get("global_params", {})
    params_by_op = stage_params_by_op(bindings)
    lanes = scalar(global_params.get("lanes"), 8)
    clock = scalar(global_params.get("clock_target_mhz"), 0)
    input_bits = first_param(params_by_op, ["block_input_bits", "input_bits"], numeric_default_bits(state, "acc_dtype", 32))
    elem_bits = first_param(params_by_op, ["elem_bits"], numeric_default_bits(state, "activation_dtype", 16))
    output_bits = first_param(params_by_op, ["block_output_bits"], input_bits)
    batch_size = max_seq
    design_name = safe_id(str(state.get("design_id", "spatialaccagent_design")))

    if param_class == "LlamaStyleBlockParams":
        params_expr = (
            f"LlamaStyleBlockParams(hiddenSize = {hidden}, qHeads = {q_heads}, kvHeads = {kv_heads}, "
            f"headDim = {head_dim}, intermediateSize = {intermediate}, lanes = {lanes}, "
            f"batchSize = {batch_size}, maxSeqLen = {max_seq}, "
            f"inputBits = {input_bits}, elemBits = {elem_bits}, outputBits = {output_bits})"
        )
    elif param_class == "Gemma3TextBlockParams":
        params_expr = (
            f"Gemma3TextBlockParams(hiddenSize = {hidden}, qHeads = {q_heads}, kvHeads = {kv_heads}, "
            f"headDim = {head_dim}, intermediateSize = {intermediate}, lanes = {lanes}, "
            f"batchSize = {batch_size}, maxSeqLen = {max_seq}, "
            f"inputBits = {input_bits}, elemBits = {elem_bits}, outputBits = {output_bits})"
        )
    else:
        params_expr = (
            f"DecoderBlockParams(hiddenSize = {hidden}, numHeads = {q_heads}, headDim = {head_dim}, "
            f"intermediateSize = {intermediate}, lanes = {lanes}, batchSize = {batch_size}, maxSeqLen = {max_seq}, "
            f"inputBits = {input_bits}, elemBits = {elem_bits}, outputBits = {output_bits})"
        )

    build_sbt = """ThisBuild / scalaVersion := "2.13.16"
ThisBuild / version := "0.1.0"

val chiselVersion = "7.0.0"

lazy val root = (project in file("."))
  .settings(
    name := "spatialaccagent-generated",
    libraryDependencies += "org.chipsalliance" %% "chisel" % chiselVersion,
    scalacOptions ++= Seq("-language:reflectiveCalls", "-deprecation", "-feature", "-Xcheckinit", "-Ymacro-annotations"),
    addCompilerPlugin("org.chipsalliance" % "chisel-plugin" % chiselVersion cross CrossVersion.full),
  )
"""
    write_text(root / "build.sbt", build_sbt)
    write_text(root / "project" / "build.properties", "sbt.version = 1.9.7\n")

    params_scala = f"""package spatialaccagent.generated

import spatialaccagent.templates._

object GeneratedDesignParams {{
  val designId: String = "{state.get('design_id')}"
  val modelType: String = "{model_type}"
  val targetMaxSeqLen: Int = {max_seq}
  val clockTargetMHz: Int = {clock}
  val inputBits: Int = {input_bits}
  val elemBits: Int = {elem_bits}
  val outputBits: Int = {output_bits}
  val operatorSequence: Seq[String] = Seq({quote_list([stage['op'] for stage in pipeline.get('stages', [])])})
  val stageIds: Seq[String] = Seq({quote_list([stage['stage_id'] for stage in pipeline.get('stages', [])])})
  val params = {params_expr}
}}
"""
    top_scala = f"""package spatialaccagent.generated

import chisel3._
import chisel3.util._
import spatialaccagent.templates._

class GeneratedAcceleratorTop extends Module {{
  private val p = GeneratedDesignParams.params
  private val core = Module(new {top_class}(p))

  val io = IO(chiselTypeOf(core.io))
  io <> core.io
}}

object ElaborateGeneratedAccelerator extends App {{
  _root_.circt.stage.ChiselStage.emitSystemVerilogFile(
    new GeneratedAcceleratorTop,
    firtoolOpts = Array("-disable-all-randomization", "-strip-debug-info")
  )
}}
"""
    position_assignment = "  core.io.position := io.position\n" if top_class in {"LlamaStyleBlock", "Gemma3TextBlock"} else ""
    axi_top_scala = f"""package spatialaccagent.generated

import chisel3._
import chisel3.util._

class GeneratedAxiDdrTop extends Module {{
  private val p = GeneratedDesignParams.params
  private val dataBits = p.lanes * p.inputBits
  private val addrBits = log2Ceil(p.batchSize * (p.hiddenSize / p.lanes) max 2)
  private val cfgBits = log2Ceil(p.maxSeqLen + 1 max 2)
  private val posBits = log2Ceil(p.maxSeqLen max 2)

  val io = IO(new Bundle {{
    val start = Input(Bool())
    val cfgSeqlen = Input(UInt(cfgBits.W))
    val cfgPrefill = Input(Bool())
    val cfgSingleQuery = Input(Bool())
    val position = Input(UInt(posBits.W))

    val axiReadValid = Input(Bool())
    val axiReadReady = Output(Bool())
    val axiReadData = Input(UInt(dataBits.W))
    val axiReadAddr = Input(UInt(addrBits.W))
    val axiReadStart = Input(Bool())
    val axiReadLast = Input(Bool())

    val axiWriteValid = Output(Bool())
    val axiWriteReady = Input(Bool())
    val axiWriteData = Output(UInt(dataBits.W))
    val axiWriteAddr = Output(UInt(addrBits.W))
    val axiWriteStart = Output(Bool())
    val axiWriteLast = Output(Bool())

    val busy = Output(Bool())
    val done = Output(Bool())
  }})

  private val core = Module(new GeneratedAcceleratorTop)
  private val running = RegInit(false.B)
  private val active = running || io.start

  when(io.start) {{
    running := true.B
  }}.elsewhen(core.io.out.fire && core.io.out.bits.last) {{
    running := false.B
  }}

  core.io.start := io.start
  core.io.cfg.seqlen := io.cfgSeqlen
  core.io.cfg.prefill := io.cfgPrefill
  core.io.cfg.singleQuery := io.cfgSingleQuery
  core.io.cfgValid := active
{position_assignment}  core.io.in.valid := io.axiReadValid && active
  core.io.in.bits.data := io.axiReadData
  core.io.in.bits.addr := io.axiReadAddr
  core.io.in.bits.st := io.axiReadStart
  core.io.in.bits.last := io.axiReadLast
  io.axiReadReady := core.io.in.ready && active

  core.io.out.ready := io.axiWriteReady
  io.axiWriteValid := core.io.out.valid
  io.axiWriteData := core.io.out.bits.data
  io.axiWriteAddr := core.io.out.bits.addr
  io.axiWriteStart := core.io.out.bits.st
  io.axiWriteLast := core.io.out.bits.last

  io.busy := active
  io.done := !active
}}

object ElaborateGeneratedAxiDdrTop extends App {{
  _root_.circt.stage.ChiselStage.emitSystemVerilogFile(
    new GeneratedAxiDdrTop,
    firtoolOpts = Array("-disable-all-randomization", "-strip-debug-info")
  )
}}
"""
    contract_check_scala = """package spatialaccagent.generated

object GeneratedContractCheck extends App {
  val p = GeneratedDesignParams.params
  require(p.hiddenSize > 0, "hiddenSize must be positive")
  require(p.intermediateSize > 0, "intermediateSize must be positive")
  require(p.lanes > 0, "lanes must be positive")
  require(p.hiddenSize % p.lanes == 0, "hiddenSize must be divisible by lanes")
  require(p.inputBits == p.outputBits, "block ingress, egress, and residual path must use the same width")
  require(p.elemBits <= p.inputBits, "internal element width must not exceed block stream width")
  println(
    s"GeneratedContractCheck pass: hidden=${p.hiddenSize}, intermediate=${p.intermediateSize}, lanes=${p.lanes}, bits=${p.inputBits}/${p.elemBits}/${p.outputBits}"
  )
}
"""
    metadata_scala = f"""package spatialaccagent.generated

object GeneratedSACGMetadata {{
  val manifestSchema: String = "{manifest['schema_version']}"
  val generationPolicy: String = "{manifest['generation_policy']}"
  val pipelineStyle: String = "{pipeline.get('pipeline_style')}"
  val boardSummary: String = "{board.get('board', {}).get('board_id', 'unknown')}"
}}
"""
    write_text(generated_dir / "GeneratedDesignParams.scala", params_scala)
    write_text(generated_dir / "GeneratedAcceleratorTop.scala", top_scala)
    write_text(generated_dir / "GeneratedAxiDdrTop.scala", axi_top_scala)
    write_text(generated_dir / "GeneratedContractCheck.scala", contract_check_scala)
    write_text(generated_dir / "GeneratedSACGMetadata.scala", metadata_scala)

    readme = f"""# Generated SpatialAccAgent Chisel Package

This package is generated from SACG artifacts for `{state.get('design_id')}`.
It is template-constrained: files under `spatialaccagent/templates` are copied
from the trusted template library, while files under `spatialaccagent/generated`
bind model, pipeline, parameter, and board facts for this run.

Model: `{model_type}`
Top wrapper: `{top_class}`
FPGA AXI/DDR top: `GeneratedAxiDdrTop`
Target sequence length: `{max_seq}`
Clock target MHz: `{clock}`
Bit policy: input `{input_bits}`, internal `{elem_bits}`, output `{output_bits}`

Pipeline stages:
{chr(10).join('- ' + line for line in stage_summary_lines(pipeline))}

Run:

```bash
sbt "runMain spatialaccagent.generated.GeneratedContractCheck"
sbt "runMain spatialaccagent.generated.ElaborateGeneratedAccelerator"
sbt "runMain spatialaccagent.generated.ElaborateGeneratedAxiDdrTop"
```

This package contains the accelerator compute top and the FPGA-facing AXI/DDR
top boundary, plus generated memory/runtime manifests for later verification
and board integration stages. It does not claim DDR image, VCS, Vivado, or
board pass; those must be produced, bound, and verified by later stages. Chisel
compile/elaboration, simulation, synthesis, implementation, and board run
evidence must be attached through SACG checkers before design pass can be
claimed.
"""
    write_text(root / "README.md", readme)
    write_text(
        scripts_dir / "elaborate.sh",
        "#!/usr/bin/env bash\nset -euo pipefail\ncd \"$(dirname \"$0\")/..\"\nsbt --no-server --batch --supershell=false \"runMain spatialaccagent.generated.ElaborateGeneratedAccelerator\"\nsbt --no-server --batch --supershell=false \"runMain spatialaccagent.generated.ElaborateGeneratedAxiDdrTop\"\n",
    )
    (scripts_dir / "elaborate.sh").chmod(0o755)
    write_text(
        scripts_dir / "compile_check.sh",
        "#!/usr/bin/env bash\nset -euo pipefail\ncd \"$(dirname \"$0\")/..\"\nmkdir -p .sbt/boot .ivy2 .cache/coursier\nexport SBT_OPTS=\"${SBT_OPTS:-} -Dsbt.global.base=$PWD/.sbt -Dsbt.boot.directory=$PWD/.sbt/boot -Dsbt.ivy.home=$PWD/.ivy2 -Dsbt.server.autostart=false -Dsbt.server.forcestart=false\"\nexport COURSIER_CACHE=\"${COURSIER_CACHE:-$PWD/.cache/coursier}\"\nsbt --no-server --batch --supershell=false Compile/compile\nsbt --no-server --batch --supershell=false \"runMain spatialaccagent.generated.GeneratedContractCheck\"\nsbt --no-server --batch --supershell=false \"runMain spatialaccagent.generated.ElaborateGeneratedAccelerator\"\nsbt --no-server --batch --supershell=false \"runMain spatialaccagent.generated.ElaborateGeneratedAxiDdrTop\"\n",
    )
    (scripts_dir / "compile_check.sh").chmod(0o755)

    files = sorted(str(path.relative_to(run_dir)) for path in root.rglob("*") if path.is_file())
    return {
        "root": str(root),
        "files": files,
        "top_class": top_class,
        "fpga_wrapper_class": "GeneratedAxiDdrTop",
        "param_class": param_class,
        "params": {
            "hidden_size": hidden,
            "intermediate_size": intermediate,
            "num_q_heads": q_heads,
            "num_kv_heads": kv_heads,
            "head_dim": head_dim,
            "max_seq_len": max_seq,
            "lanes": lanes,
            "clock_target_mhz": clock,
            "input_bits": input_bits,
            "elem_bits": elem_bits,
            "output_bits": output_bits,
        },
    }


def build_manifest(state: dict[str, Any]) -> dict[str, Any]:
    selection = read_json(artifact_path(state, "artifact.stage2.template_selection"))
    bindings = read_json(artifact_path(state, "artifact.stage4.parameter_binding"))
    template = constraint_facts(state, "constraint.template.library")
    model = next(c for c in state.get("constraints", []) if c.get("id") == "constraint.model.decoder")
    model_type = model.get("facts", {}).get("model_type")
    selected_sources = sorted({item.get("source") for item in selection.get("selected_templates", []) if item.get("source")})
    template_sources = sorted(str(source) for source in template.get("source_files", []))
    planned = [
        {"id": "generated.model_ir", "kind": "model_ir", "status": "generated", "depends_on": ["artifact.input.model_config"]},
        {"id": "generated.arch_plan", "kind": "architecture_plan", "status": "generated", "depends_on": ["artifact.stage3.pipeline_plan", "artifact.stage4.parameter_binding"]},
        {"id": "generated.chisel_modules", "kind": "chisel", "status": "generated", "template_sources": template_sources, "selected_operator_template_sources": selected_sources},
        {"id": "generated.top_wrapper", "kind": "top_wrapper", "status": "generated", "depends_on": ["generated.chisel_modules", "artifact.input.target_board_profile"]},
        {"id": "generated.fpga_axi_ddr_top_wrapper", "kind": "fpga_axi_ddr_top_wrapper", "status": "generated", "depends_on": ["generated.top_wrapper", "artifact.input.target_board_profile"]},
        {"id": "generated.memory_layout", "kind": "memory_layout", "status": "generated", "depends_on": ["artifact.stage4.parameter_binding", "artifact.input.target_board_profile"]},
        {"id": "generated.runtime_config", "kind": "runtime_config", "status": "generated", "depends_on": ["generated.memory_layout", "artifact.input.target_board_profile"]},
        {"id": "generated.scala_contract_check", "kind": "scala_contract_check", "status": "generated", "depends_on": ["generated.chisel_modules", "artifact.stage4.parameter_binding"]},
        {"id": "generated.codegen_compile_gate", "kind": "compile_gate", "status": "pending", "depends_on": ["generated.chisel_modules", "generated.top_wrapper", "generated.fpga_axi_ddr_top_wrapper"]},
        {"id": "generated.codegen_contract_check", "kind": "contract_check", "status": "pending", "depends_on": ["generated.chisel_modules", "generated.memory_layout", "generated.runtime_config", "generated.codegen_compile_gate"]},
    ]
    return {
        "schema_version": "spatialaccagent.code_generation_manifest.v0",
        "stage": "code_generation",
        "status": "ready",
        "generation_policy": "from_scratch_target_accelerator_package",
        "model_type": model_type,
        "template_sources": template_sources,
        "selected_operator_template_sources": selected_sources,
        "planned_code_outputs": planned,
        "generated_code_outputs": planned,
        "parameter_binding": bindings.get("global_params", {}),
        "target_model_artifact_status": {
            "model_type": model_type,
            "current_artifacts_match_target": True,
            "missing_for_target": [],
            "planned_for_target": [item["id"] for item in planned],
        },
        "stage_gate_policy": codegen_stage_gate_policy(),
        "note": "This manifest describes template-bound generated accelerator code for the target model; checker/tool evidence is still required before design pass.",
        "constraints_touched": TOUCHED_CONSTRAINTS,
    }


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def begin_manifest_attempt(manifest_path: Path, attempts_dir: Path, source_state: Path) -> Path:
    attempts_dir.mkdir(parents=True, exist_ok=True)
    stamp = utc_stamp()
    if manifest_path.exists():
        archived = attempts_dir / f"{manifest_path.stem}_superseded_{stamp}{manifest_path.suffix}"
        shutil.move(str(manifest_path), str(archived))
        write_json(
            manifest_path,
            {
                "schema_version": "spatialaccagent.code_generation_manifest.v0",
                "stage": "code_generation",
                "status": "incomplete",
                "publish_status": "superseded_by_new_attempt",
                "candidate_only": True,
                "source_sacg_state": str(source_state),
                "archived_previous_manifest": str(archived),
                "policy": "This placeholder is not a validated code-generation manifest. The official manifest is published only after the stage completes SACG gate/update.",
            },
        )
    return attempts_dir / f"{manifest_path.stem}_candidate_{stamp}{manifest_path.suffix}"


def update_sacg(source_state: Path, target_state: Path, manifest_path: Path, manifest: dict[str, Any], errors: list[str]) -> str:
    state = copy_state(source_state, target_state)
    add_constraint(
        state,
        "constraint.codegen.package",
        "codegen",
        ["node.model", "node.template_library", "node.target_board"],
        [],
        ["artifact.stage5.design_artifact_manifest", "artifact.stage5.generated_code_package", "artifact.stage5.codegen_package_static_check"],
        {
            "generation_policy": manifest["generation_policy"],
            "generated_code_outputs": manifest.get("generated_code_outputs", []),
            "generated_memory_layout": manifest.get("generated_memory_layout"),
            "generated_runtime_config": manifest.get("generated_runtime_config"),
            "target_model_artifact_status": manifest.get("target_model_artifact_status", {}),
            "package_static_status": (manifest.get("package_static_check") or {}).get("status"),
            "compile_gate_status": (manifest.get("compile_gate") or {}).get("status"),
            "errors": errors,
        },
    )
    add_invariant(state, "invariant.codegen_package_static", "codegen_package_static_check", ["constraint.codegen.package"])
    add_invariant(state, "invariant.codegen_compile_gate", "codegen_compile_gate", ["constraint.codegen.compile_gate"])
    add_invariant(state, "invariant.codegen_contract_check", "codegen_contract_check", ["constraint.codegen.contract_check"])
    add_constraint(
        state,
        "constraint.codegen.compile_gate",
        "tool_evidence",
        ["node.model", "node.template_library", "node.target_board"],
        [],
        ["artifact.stage5.codegen_compile_gate"],
        {
            "checker": "codegen_compile_gate",
            "status": (manifest.get("compile_gate") or {}).get("status"),
            "summary": (manifest.get("compile_gate") or {}).get("summary"),
            "elaboration_enabled": (manifest.get("compile_gate") or {}).get("elaboration_enabled"),
        },
    )
    add_constraint(
        state,
        "constraint.codegen.contract_check",
        "checker_evidence",
        ["node.model", "node.template_library", "node.target_board"],
        [],
        ["artifact.stage5.codegen_contract_check"],
        {
            "checker": "codegen_contract_check",
            "status": (manifest.get("contract_check") or {}).get("status"),
            "summary": (manifest.get("contract_check") or {}).get("summary"),
            "checked_contracts": (manifest.get("contract_check") or {}).get("checked_contracts", []),
        },
    )
    write_json(target_state, state)
    store = SACGStore(target_state)
    transition = store.declare_transition(
        action_type="code_generation",
        touched_nodes=["node.model", "node.template_library", "node.target_board"],
        touched_edges=[],
        touched_constraints=TOUCHED_CONSTRAINTS,
        note="Generated template-bound accelerator code package.",
    )
    store.bind_artifact(
        "artifact.stage5.design_artifact_manifest",
        str(manifest_path),
        "stage.design_artifact_manifest",
        ["node.model", "node.template_library", "node.target_board"],
        [],
        ["constraint.codegen.package"],
        transition["id"],
    )
    store.bind_artifact(
        "artifact.stage5.generated_code_package",
        str(manifest.get("generated_package_root", "")),
        "stage.generated_code_package",
        ["node.model", "node.template_library", "node.target_board"],
        [],
        ["constraint.codegen.package"],
        transition["id"],
    )
    store.bind_artifact(
        "artifact.stage5.memory_layout",
        str(manifest.get("generated_memory_layout", "")),
        "stage.memory_layout",
        ["node.model", "node.target_board"],
        [],
        ["constraint.codegen.package", "constraint.memory.board"],
        transition["id"],
    )
    store.bind_artifact(
        "artifact.stage5.runtime_config",
        str(manifest.get("generated_runtime_config", "")),
        "stage.runtime_config",
        ["node.model", "node.target_board"],
        [],
        ["constraint.codegen.package", "constraint.runtime.board", "constraint.deployment.board"],
        transition["id"],
    )
    store.bind_artifact(
        "artifact.stage5.codegen_compile_gate",
        str((manifest.get("compile_gate") or {}).get("log_path", "")),
        "stage.codegen_compile_gate",
        ["node.model", "node.template_library", "node.target_board"],
        [],
        ["constraint.codegen.compile_gate"],
        transition["id"],
    )
    store.bind_artifact(
        "artifact.stage5.codegen_contract_check",
        str((manifest.get("contract_check") or {}).get("log_path", "")),
        "stage.codegen_contract_check",
        ["node.model", "node.template_library", "node.target_board"],
        [],
        ["constraint.codegen.contract_check"],
        transition["id"],
    )
    store.bind_artifact(
        "artifact.stage5.codegen_package_static_check",
        str((manifest.get("package_static_check") or {}).get("log_path", "")),
        "stage.codegen_package_static_check",
        ["node.model", "node.template_library", "node.target_board"],
        [],
        ["constraint.codegen.package"],
        transition["id"],
    )
    package_status = "pass" if (manifest.get("package_static_check") or {}).get("status") == "pass" else "fail"
    store.attach_evidence(
        "codegen_package_static_check",
        package_status,
        "invariant.codegen_package_static",
        ["constraint.codegen.package"],
        ["artifact.stage5.codegen_package_static_check"],
        str((manifest.get("package_static_check") or {}).get("log_path", "")),
        transition["id"],
        summary=str((manifest.get("package_static_check") or {}).get("summary", "")),
    )
    compile_status = "pass" if (manifest.get("compile_gate") or {}).get("status") == "pass" else "fail"
    store.attach_evidence(
        "codegen_compile_gate",
        compile_status,
        "invariant.codegen_compile_gate",
        ["constraint.codegen.compile_gate"],
        ["artifact.stage5.codegen_compile_gate"],
        str((manifest.get("compile_gate") or {}).get("log_path", "")),
        transition["id"],
        summary=str((manifest.get("compile_gate") or {}).get("summary", "")),
    )
    contract_status = "pass" if (manifest.get("contract_check") or {}).get("status") == "pass" else "fail"
    store.attach_evidence(
        "codegen_contract_check",
        contract_status,
        "invariant.codegen_contract_check",
        ["constraint.codegen.contract_check"],
        ["artifact.stage5.codegen_contract_check"],
        str((manifest.get("contract_check") or {}).get("log_path", "")),
        transition["id"],
        summary=str((manifest.get("contract_check") or {}).get("summary", "")),
    )
    if errors:
        store.reject(transition["id"], f"code generation failed gate checks: {errors[:8]}")
        store.record_failure_lesson(
            stage="stage5.code_generation",
            failure_class="codegen_gate",
            summary=f"code generation failed gate checks: {errors[:8]}",
            violated_constraints=TOUCHED_CONSTRAINTS,
            artifacts=[
                "artifact.stage5.design_artifact_manifest",
                "artifact.stage5.generated_code_package",
                "artifact.stage5.codegen_compile_gate",
                "artifact.stage5.codegen_contract_check",
            ],
            recommended_action="Rerun Stage5 after fixing compile/contract/package or upstream artifact trust blockers; downstream verification must not consume rejected codegen artifacts as validated inputs.",
            retry_scope="same_stage_or_upstream",
        )
        store.record_retry_request(
            stage="stage5.code_generation",
            reason="Stage5 generated package did not pass compile/contract/package gates",
            target_stage="stage5.code_generation",
            required_inputs=["artifact.stage2.template_selection", "artifact.stage3.pipeline_plan", "artifact.stage4.parameter_binding"],
            blocked_artifacts=["artifact.stage5.design_artifact_manifest", "artifact.stage5.generated_code_package"],
        )
    else:
        store.promote(transition["id"])
    store.record_stage_outcome(
        stage="stage5.code_generation",
        status="ready" if not errors else "incomplete",
        transition_id=transition["id"],
        summary=str((manifest.get("compile_gate") or {}).get("summary") or (manifest.get("contract_check") or {}).get("summary") or "code generation stage completed"),
        errors=errors,
        artifacts=[
            "artifact.stage5.design_artifact_manifest",
            "artifact.stage5.generated_code_package",
            "artifact.stage5.memory_layout",
            "artifact.stage5.runtime_config",
        ],
        next_actions=[] if not errors else ["retry stage5.code_generation or backtrack to the upstream stage named in upstream_gate_errors"],
        retryable=bool(errors),
    )
    store.save()
    return transition["id"]


def generate_code(args: argparse.Namespace) -> tuple[Path, dict[str, Any]]:
    source_state = args.sacg_state.resolve()
    run_dir = run_dir_from_state(source_state)
    out_dir = run_dir / "code_generation"
    manifest_path = out_dir / "code_generation_manifest.json"
    candidate_manifest_path = begin_manifest_attempt(manifest_path, out_dir / "attempts", source_state)
    state_path = out_dir / "sacg_state.json"
    report_path = out_dir / "code_generation_report.json"
    state = read_json(source_state)
    upstream_gate_errors = require_promoted_artifacts(
        state,
        [
            "artifact.stage2.template_selection",
            "artifact.stage3.pipeline_plan",
            "artifact.stage4.parameter_binding",
        ],
    )
    manifest = build_manifest(state)
    manifest["publish_status"] = "candidate_only"
    manifest["candidate_only"] = True
    manifest["final_manifest_path"] = str(manifest_path)
    if upstream_gate_errors:
        manifest["upstream_gate_errors"] = upstream_gate_errors
    generated_package = generate_chisel_package(run_dir, state, manifest)
    package_root = Path(generated_package["root"])
    memory_layout = build_memory_layout(state, bindings=read_json(artifact_path(state, "artifact.stage4.parameter_binding")), generated_package=generated_package)
    memory_layout_path = package_root / "memory" / "memory_layout.json"
    write_json(memory_layout_path, memory_layout)
    runtime_config = build_runtime_config(state, memory_layout, generated_package)
    runtime_config_path = package_root / "runtime" / "runtime_config.json"
    write_json(runtime_config_path, runtime_config)
    generated_package["files"] = sorted(str(path.relative_to(run_dir)) for path in package_root.rglob("*") if path.is_file())
    manifest["generated_package_root"] = generated_package["root"]
    manifest["generated_files"] = generated_package["files"]
    manifest["generated_memory_layout"] = str(memory_layout_path)
    manifest["generated_runtime_config"] = str(runtime_config_path)
    manifest["generated_top"] = {
        "top_class": generated_package["top_class"],
        "fpga_wrapper_class": generated_package["fpga_wrapper_class"],
        "param_class": generated_package["param_class"],
        "params": generated_package["params"],
    }
    compile_gate = run_codegen_compile_gate(package_root)
    manifest["compile_gate"] = compile_gate
    for item in manifest.get("generated_code_outputs", []):
        if item.get("id") == "generated.codegen_compile_gate":
            item["status"] = compile_gate.get("status")
    contract_check_path = package_root / "logs" / "codegen_contract_check.json"
    contract_check = build_codegen_contract_check(
        state,
        manifest,
        generated_package,
        memory_layout,
        runtime_config,
        compile_gate,
        contract_check_path,
    )
    manifest["contract_check"] = contract_check
    for item in manifest.get("generated_code_outputs", []):
        if item.get("id") == "generated.codegen_contract_check":
            item["status"] = contract_check.get("status")
    manifest["generated_files"] = sorted(str(path.relative_to(run_dir)) for path in package_root.rglob("*") if path.is_file())
    package_check_path = package_root / "logs" / "codegen_package_static_check.json"
    package_static_check = build_codegen_package_static_check(manifest, package_check_path)
    manifest["package_static_check"] = package_static_check
    manifest["generated_files"] = sorted(str(path.relative_to(run_dir)) for path in package_root.rglob("*") if path.is_file())
    write_json(candidate_manifest_path, manifest)
    team = run_design_team(
        stage="code_generation",
        objective="Generate and audit a template-bound accelerator code package from SACG.",
        state=state,
        candidate_artifact=manifest,
        out_dir=out_dir,
    )
    llm = run_stage_agent(
        agent="code_generation_agent",
        stage="code_generation",
        task="Review the accelerator code generation manifest, generated code package, and team handoff for missing cross-layer design outputs.",
        inputs={
            "candidate_artifact_manifest": manifest,
            "stage_gate_policy": manifest.get("stage_gate_policy", {}),
            "compile_gate": compile_gate,
            "contract_check": contract_check,
            "package_static_check": package_static_check,
            "design_team": team_summary(team),
            "source_sacg_state": str(source_state),
        },
        out_dir=out_dir,
        fallback_summary="Code generation manifest created for target accelerator package.",
    )
    design_team = team_summary(team)
    errors = []
    errors.extend(upstream_gate_errors)
    errors.extend(codegen_gate_errors(compile_gate))
    errors.extend(codegen_contract_errors(contract_check))
    errors.extend(codegen_package_errors(package_static_check))
    errors.extend(team_failure_errors(design_team))
    errors.extend(stage_worker_errors(llm["output"]))
    manifest["status"] = "ready" if not errors else "incomplete"
    manifest["publish_status"] = "published_after_sacg_gate" if not errors else "published_rejected_after_sacg_gate"
    manifest["candidate_only"] = False
    manifest["candidate_manifest_path"] = str(candidate_manifest_path)
    transition_id = update_sacg(source_state, state_path, manifest_path, manifest, errors)
    write_json(manifest_path, manifest)
    report = {
        "schema_version": "spatialaccagent.code_generation_report.v0",
        "stage": "code_generation",
        "status": "ready" if not errors else "incomplete",
        "source_sacg_state": str(source_state),
        "outputs": {
            "code_generation_manifest": str(manifest_path),
            "generated_code_package": generated_package["root"],
            "memory_layout": str(memory_layout_path),
            "runtime_config": str(runtime_config_path),
            "compile_gate": compile_gate.get("log_path"),
            "contract_check": contract_check.get("log_path"),
            "sacg_state": str(state_path),
            "llm_agent": llm["result_path"],
            "team_subtask_plan": team["subtask_plan_path"],
            "team_aggregate": team["aggregate_path"],
        },
        "llm_agent": llm["output"],
        "llm_executable_actions": llm["output"].get("executable_actions", []),
        "design_team": design_team,
        "team_executable_actions": design_team.get("executable_actions", []),
        "compile_gate": compile_gate,
        "contract_check": contract_check,
        "package_static_check": package_static_check,
        "memory_layout": memory_layout,
        "runtime_config": runtime_config,
        "planned_code_outputs": [item["id"] for item in manifest["planned_code_outputs"]],
        "generated_files": generated_package["files"],
        "sacg_transition_id": transition_id,
        "errors": errors,
    }
    write_json(report_path, report)
    return report_path, report


def main(argv: list[str] | None = None) -> int:
    return run_sacg_stage("Code generation stage", generate_code, argv)


if __name__ == "__main__":
    raise SystemExit(main())
