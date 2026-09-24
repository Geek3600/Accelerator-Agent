"""Run-specific verification case adapter contracts.

The framework core is model-agnostic: it needs real weights, a real runtime
ABI, a functional simulator, and diagnosable evidence. Concrete model flows
such as the current Qwen2 HF case live behind this adapter contract.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any


CASE_ADAPTER_SCHEMA = "spatialaccagent.case_adapter.v0"

EXACT_BOARD_DISCOVERY_CAPABILITIES = {
    "llm_board_discovery_provenance",
    "vivado_fact_evidence_binding",
    "recursive_simulation_source_closure",
    "compute_slot_abi_contract",
    "compute_slot_control_abi_contract",
    "clock_reset_calibration_timing_contract",
    "complete_axi4_parameter_contract",
}

EXACT_BOARD_ACCEPTANCE_CAPABILITIES = {
    "exact_board_acceptance_fail_closed",
    "preflight_postrun_acceptance_separation",
    "recursive_simulation_source_closure_validation",
    "verified_compute_slot_source_replacement",
    "generated_source_closure_validation",
    "generated_rtl_evidence_namespace_validation",
    "compute_slot_abi_validation",
    "compute_slot_control_abi_validation",
    "exact_board_timing_validation",
    "complete_axi4_parameter_validation",
    "non_behavioral_exact_memory_testbench_validation",
    "elaborated_hierarchy_binding_validation",
    "structured_axi_protocol_monitor_contract_validation",
    "multilayer_board_integration_validation",
    "real_tool_execution_identity_validation",
    "dynamic_axi_protocol_report_validation",
    "dynamic_spatial_pipeline_overlap_validation",
    "typed_dynamic_evidence_validation",
}

GENERIC_EVIDENCE_GATES = {
    "stage_leaf_static": "case_stage_leaf_static",
    "leaf_functional": "case_leaf_functional",
    "leaf_golden_compare": "case_leaf_golden_compare",
    "operator_leaf_semantic_evidence": "case_operator_leaf_semantic_evidence",
    "boundary_contract": "boundary_contract_check",
    "real_weight_artifacts": "case_real_weight_artifacts",
    "target_model_reference": "case_target_model_reference",
    "semantic_testbench": "case_semantic_testbench",
    "tb_scaffold": "case_tb_scaffold",
    "single_layer_kernel": "single_transformer_layer",
    "single_layer_functional": "case_single_layer_functional",
    "single_layer_golden_compare": "case_single_layer_golden_compare",
    "single_layer_semantic_evidence": "case_single_layer_semantic_evidence",
    "multilayer_pipeline": "case_multilayer_pipeline",
    "multilayer_functional": "case_multilayer_functional",
    "pipeline_deadlock": "case_pipeline_deadlock_check",
    "axi_ddr_interface": "case_axi_ddr_interface",
    "axi_protocol": "case_axi_protocol_check",
    "ddr_image_roundtrip": "case_ddr_image_roundtrip",
    "board_semantic_evidence": "case_board_semantic_evidence",
    "board_bringup": "case_board_bringup_ready",
    "functional_sim": "functional_sim",
    "board_interface_discovery": "case_board_interface_discovery",
    "vivado_synthesis": "case_vivado_synthesis",
    "vivado_implementation": "case_vivado_implementation",
    "vivado_power": "case_vivado_power",
    "stage7_metrics": "case_stage7_metrics",
    "runtime_abi": "case_runtime_abi_check",
    "runtime_bitstream": "case_runtime_bitstream",
    "board_runtime": "board_runtime",
}

BUILTIN_SEMANTIC_ADAPTERS = {
    "gpt2": Path("accagent/framework/case_adapters/gpt2_transformer_block.json"),
    "llama": Path("accagent/framework/case_adapters/llama_transformer_block.json"),
    "qwen2": Path("accagent/framework/case_adapters/qwen2_transformer_block.json"),
}


def safe_id(value: Any, default: str = "unknown") -> str:
    text = str(value or default).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_") or default


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def board_testbench_path(run_dir: Path) -> str:
    """Use the current exact-board manifest after it has been materialized."""

    fallback = run_dir / "verification" / "board_simulation" / "board_tb.sv"
    manifest_path = (
        run_dir / "verification" / "board_simulation" / "board_simulation_manifest.json"
    )
    if not manifest_path.is_file():
        return str(fallback)
    try:
        manifest = read_json(manifest_path)
    except (OSError, ValueError, json.JSONDecodeError):
        return str(fallback)
    testbench = manifest.get("testbench", {})
    path = testbench.get("path") if isinstance(testbench, dict) else None
    return str(path) if isinstance(path, str) and path else str(fallback)


def repo_has(path: str) -> bool:
    return (Path.cwd() / path).exists()


def tool(
    *,
    name: str,
    kind: str,
    scope: str,
    argv: list[str],
    required: bool,
    env: dict[str, Any] | None = None,
    consumes: list[str] | None = None,
    produces: list[str] | None = None,
    capabilities: list[str] | None = None,
    required_group: str | None = None,
    legacy_name: str | None = None,
    requires_external_tool: str | None = None,
    targeted_replay: dict[str, Any] | None = None,
    python_modules: list[str] | None = None,
    python_module_versions: dict[str, str | list[str]] | None = None,
    python_environment_group: str | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "name": name,
        "kind": kind,
        "scope": scope,
        "argv": argv,
        "required": required,
        "consumes": consumes or [],
        "produces": produces or [],
        "capabilities": capabilities or [],
    }
    if env:
        result["env"] = {str(k): str(v) for k, v in env.items()}
    if required_group:
        result["required_group"] = required_group
    if legacy_name:
        result["legacy_name"] = legacy_name
    if requires_external_tool:
        result["requires_external_tool"] = requires_external_tool
    if targeted_replay:
        result["targeted_replay"] = targeted_replay
    if python_modules:
        result["python_modules"] = [str(value) for value in python_modules]
    if python_module_versions:
        result["python_module_versions"] = {
            str(name): ([str(value)] if isinstance(versions, str) else [str(value) for value in versions])
            for name, versions in python_module_versions.items()
        }
    if python_environment_group:
        result["python_environment_group"] = str(python_environment_group)
    return result


def user_adapter_path(tool_materials_dir: Path) -> Path | None:
    env_path = os.environ.get("SPATIALACC_CASE_ADAPTER")
    candidates = [Path(env_path)] if env_path else []
    candidates.extend(
        [
            tool_materials_dir / "case_adapter.json",
            tool_materials_dir / "verification_case_adapter.json",
        ]
    )
    for path in candidates:
        if path.exists():
            return path
    return None


def normalize_user_adapter(adapter: dict[str, Any], source_path: Path, run_dir: Path) -> dict[str, Any]:
    result = dict(adapter)
    result.setdefault("schema_version", CASE_ADAPTER_SCHEMA)
    result.setdefault("status", "ready")
    result.setdefault("case_id", safe_id(result.get("case_id") or source_path.stem))
    result.setdefault("model_family", safe_id(result.get("model_family")))
    result.setdefault("source", str(source_path))
    result.setdefault("run_dir", str(run_dir))
    result.setdefault("evidence_gates", GENERIC_EVIDENCE_GATES)
    result.setdefault("tools", {})
    result.setdefault("errors", [])
    result.setdefault("notes", [])
    result["notes"] = [
        *list(result.get("notes") or []),
        "Loaded from user-provided case adapter; framework core must not replace it with built-in Qwen/OPT assumptions.",
    ]
    errors = [str(value) for value in result.get("errors", []) if str(value)]
    tools = result.get("tools")
    if not isinstance(tools, dict):
        errors.append("user case adapter tools must be an object keyed by tool role")
    else:
        for role, spec in tools.items():
            if not isinstance(spec, dict):
                errors.append(f"tool {role}: specification must be an object")
                continue
            argv = spec.get("argv")
            if not isinstance(argv, list) or not all(isinstance(value, str) and value for value in argv):
                errors.append(f"tool {role}: argv must be a non-empty string list")
            modules = spec.get("python_modules", [])
            if modules and (
                not isinstance(modules, list)
                or not all(isinstance(value, str) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]*", value) for value in modules)
            ):
                errors.append(f"tool {role}: python_modules must be a list of valid module names")
            versions = spec.get("python_module_versions", {})
            if versions and not isinstance(versions, dict):
                errors.append(f"tool {role}: python_module_versions must be an object")
            if spec.get("python_environment_group") and not modules:
                errors.append(f"tool {role}: python_environment_group requires declared python_modules")
            if spec.get("env") is not None and not isinstance(spec.get("env"), dict):
                errors.append(f"tool {role}: env must be an object")
        for role, required_capabilities in (
            ("board_interface_discovery", EXACT_BOARD_DISCOVERY_CAPABILITIES),
            ("axi_ddr_interface", EXACT_BOARD_ACCEPTANCE_CAPABILITIES),
        ):
            spec = tools.get(role)
            if not isinstance(spec, dict):
                errors.append(f"user case adapter is missing required exact-board tool role: {role}")
                continue
            capabilities = set(map(str, spec.get("capabilities", [])))
            missing = sorted(required_capabilities - capabilities)
            if missing:
                errors.append(f"tool {role}: missing exact-board capabilities: {missing}")
    result["errors"] = errors
    if errors:
        result["status"] = "incomplete"
    return result


def configured_model_directory(model: dict[str, Any]) -> Path | None:
    """Return only an explicit checkpoint directory from the current run input.

    A model checkpoint is user material, not a framework default.  In
    particular, a Qwen cache location must never become an implicit fallback
    for GPT-2, LLaMA, or another user-selected model.
    """

    value = model.get("model_dir")
    return Path(value).expanduser() if isinstance(value, str) and value.strip() else None


def built_in_transformer_case_adapter(
    model: dict[str, Any],
    run_dir: Path,
    family: str,
) -> dict[str, Any]:
    """Build the common real-tool adapter for supported decoder families.

    The model family selects only a semantic contract.  Real weight cataloging,
    current-run testbench generation, VCS evidence collection, and exact
    app-shell implementation are shared framework capabilities.
    """

    if family not in BUILTIN_SEMANTIC_ADAPTERS:
        raise ValueError(f"unsupported built-in transformer family: {family}")
    real_dir = run_dir / "verification" / "model_weights"
    reference_dir = run_dir / "verification" / "model_reference"
    semantic_tb_dir = run_dir / "verification" / "semantic_testbench"
    semantic_evidence_dir = run_dir / "verification" / "semantic_evidence"
    hierarchy_dir = run_dir / "verification" / "case_hierarchy"
    chisel_dir = run_dir / "generated" / "chisel"
    diagnosis_path = run_dir / "verification" / "case_diagnostics" / "vcs_functional_diagnosis.json"
    deadlock_axi_path = run_dir / "verification" / "case_diagnostics" / "deadlock_axi_check.json"
    debug_dir = run_dir / "verification" / "debug_closure"
    synth_report_check_path = run_dir / "backend_board" / "case_diagnostics" / "vivado_synth_report_check.json"
    bitstream_report_check_path = run_dir / "backend_board" / "case_diagnostics" / "vivado_bitstream_report_check.json"
    runtime_abi_check_path = run_dir / "backend_board" / "case_diagnostics" / "runtime_abi_check.json"
    # This is the one canonical QoR result consumed by Stage 4 feedback and
    # Stage 7 routing.  Do not create a second legacy metrics location: stale
    # reports from a prior implementation run must never be selected instead.
    stage7_metrics_path = run_dir / "backend_board" / "qor" / "qor_metrics.json"
    rtl_wrapper = str(run_dir / "verification" / "board_interface" / "sample_project_sources" / "wrapper.v")
    tb_path = board_testbench_path(run_dir)
    model_id = str(model.get("model_id") or model.get("name") or family)
    model_dir = configured_model_directory(model)
    semantic_adapter = BUILTIN_SEMANTIC_ADAPTERS[family]
    scripts = {
        "weight_manifest": "scripts/verification/target_model_weight_catalog.py",
        "target_model_reference": "scripts/verification/target_model_reference.py",
        "semantic_testbench": "scripts/verification/semantic_testbench_generator.py",
        "semantic_evidence": "scripts/verification/semantic_evidence_assembler.py",
        "board_discovery": "scripts/verification/sample_project_board_interface_discovery.py",
        "tb_generator": "scripts/verification/case_tb_generator.py",
        "hierarchical_check": "scripts/verification/case_hierarchical_check.py",
        "leaf_operator_verify": "scripts/verification/case_leaf_operator_verify.py",
        "single_layer_stream_sim": "scripts/verification/case_single_layer_stream_sim.py",
        "vcs_functional": "scripts/verification/case_board_vcs_functional.py",
        "vcs_analyzer": "scripts/verification/case_vcs_evidence_analyzer.py",
        "deadlock_axi_check": "scripts/verification/case_deadlock_axi_check.py",
        "vivado_app_shell": "scripts/synthesis/case_app_shell_vivado.py",
        "vivado_report_check": "scripts/synthesis/case_vivado_report_check.py",
        "stage7_metrics": "scripts/synthesis/case_stage7_metrics.py",
        "runtime_abi_check": "scripts/synthesis/case_runtime_abi_check.py",
    }
    num_layers = int(model.get("num_layers") or 24)
    remote_sim_timeout_sec = max(900, num_layers * 60)
    oracle_python_modules = ["torch", "transformers", "safetensors"]
    oracle_python_environment_group = "target_model_oracle"
    tools = {
        "weight_manifest_generate": tool(
            name="case_weight_manifest_generate",
            kind="target_model_weight_catalog_generate",
            scope="local",
            argv=[
                "python3",
                scripts["weight_manifest"],
                "--run-dir",
                str(run_dir),
                "--model-id",
                model_id,
                "--model-dir",
                str(model_dir) if model_dir is not None else "",
                "--semantic-adapter",
                str(semantic_adapter),
            ],
            required=True,
            consumes=["target checkpoint safetensors and model config"],
            produces=[
                str(real_dir / "weight_manifest.json"),
                str(real_dir / "full_tensor_catalog.json"),
                str(real_dir / "transformer_block_weight_catalog.json"),
                str(real_dir / "checkpoint_inventory.json"),
                str(real_dir / "artifact_hashes.json"),
            ],
            capabilities=["real_model_weights", "complete_scope_weight_manifest", "artifact_hash_manifest"],
        ),
        "target_model_reference_generate": tool(
            name="case_target_model_reference",
            kind="target_model_reference_generate",
            scope="local",
            argv=["python3", scripts["target_model_reference"], "--run-dir", str(run_dir)],
            required=True,
            consumes=[
                str(real_dir / "weight_manifest.json"),
                str(real_dir / "transformer_block_weight_catalog.json"),
                str(run_dir / "input" / "model_config.json"),
                str(run_dir / "input" / "numeric_policy.json"),
            ],
            produces=[
                str(reference_dir / "reference_manifest.json"),
                str(reference_dir / "random_hidden_input.pt"),
                str(reference_dir / "single_layer_output.pt"),
                str(reference_dir / "full_model_output.pt"),
                str(reference_dir / "operators"),
                str(reference_dir / "weights"),
                str(reference_dir / "golden_provenance.json"),
            ],
            capabilities=[
                "real_model_weights_loaded",
                "deterministic_random_input",
                "target_model_inference",
                "operator_reference_capture",
                "independent_expected_output",
                "numeric_policy_binding",
                "explicit_reference_execution_contract",
            ],
            python_modules=oracle_python_modules,
            python_environment_group=oracle_python_environment_group,
        ),
        "semantic_testbench_generate": tool(
            name="case_semantic_testbench",
            kind="semantic_testbench_generate",
            scope="local",
            argv=["python3", scripts["semantic_testbench"], "--run-dir", str(run_dir)],
            required=True,
            consumes=[
                str(reference_dir / "reference_manifest.json"),
                str(run_dir / "pipeline_planning" / "pipeline_plan.json"),
                str(run_dir / "input" / "numeric_policy.json"),
                str(run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"),
            ],
            produces=[
                str(semantic_tb_dir / "semantic_testbench_manifest.json"),
                str(semantic_tb_dir / "dut_weight_binding_requirements.json"),
                str(semantic_tb_dir / "stages"),
                str(semantic_tb_dir / "single_layer"),
                "semantic testbench vectors",
            ],
            capabilities=[
                "semantic_testbench_generate",
                "reference_vector_encoding",
                "dut_weight_binding_validation",
                "default_weight_rejection",
                "artifact_hash_manifest",
            ],
            python_modules=oracle_python_modules,
            python_environment_group=oracle_python_environment_group,
        ),
        "board_interface_discovery": tool(
            name="case_board_interface_discovery",
            kind="case_board_interface_discovery",
            scope="local",
            argv=["python3", scripts["board_discovery"], "--run-dir", str(run_dir)],
            required=True,
            consumes=[
                str(run_dir / "input" / "target_board_profile.json"),
                str(run_dir / "input" / "sample_project_index.json"),
            ],
            produces=[
                str(run_dir / "verification" / "board_interface" / "board_source_identity.json"),
                str(run_dir / "verification" / "board_interface" / "sample_project_sources"),
                "exact sample board wrapper identity and source hash manifest",
            ],
            capabilities=[
                "board_interface_discovery",
                "exact_sample_board_wrapper_identity",
                "sample_project_source_hashes",
                *sorted(EXACT_BOARD_DISCOVERY_CAPABILITIES),
            ],
        ),
        "tb_scaffold_generate": tool(
            name="case_tb_scaffold_generate",
            kind="case_tb_scaffold_generate",
            scope="local",
            argv=["python3", scripts["semantic_testbench"], "--run-dir", str(run_dir)],
            required=True,
            consumes=[
                str(reference_dir / "reference_manifest.json"),
                str(run_dir / "pipeline_planning" / "pipeline_plan.json"),
                str(run_dir / "input" / "numeric_policy.json"),
                str(run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"),
            ],
            produces=[
                str(semantic_tb_dir / "semantic_testbench_manifest.json"),
                str(semantic_tb_dir / "dut_weight_binding_requirements.json"),
                str(semantic_tb_dir / "stages"),
                str(semantic_tb_dir / "single_layer"),
            ],
            capabilities=["tb_scaffold_generate", "semantic_testbench_generate", "artifact_loading_testbench_generate"],
            python_modules=oracle_python_modules,
            python_environment_group=oracle_python_environment_group,
        ),
        "stage_leaf_static": tool(
            name="case_stage_leaf_static",
            kind="case_stage_leaf_static",
            scope="local",
            argv=["python3", scripts["hierarchical_check"], "--run-dir", str(run_dir), "--gate", "stage_leaf_static"],
            required=True,
            consumes=[str(chisel_dir)],
            capabilities=["gate_checker_only", "stage_leaf_static_check"],
        ),
        "boundary_contract_check": tool(
            name="boundary_contract_check",
            kind="boundary_contract_check",
            scope="local",
            argv=["python3", scripts["hierarchical_check"], "--run-dir", str(run_dir), "--gate", "boundary_contract"],
            required=True,
            consumes=[str(debug_dir / "boundary_contracts.json"), str(debug_dir / "trace_manifest.json")],
            produces=[str(hierarchy_dir / "boundary_contract.json")],
            capabilities=["gate_checker_only", "boundary_contract_check"],
        ),
        "leaf_functional_sim": tool(
            name="case_leaf_functional",
            kind="case_leaf_functional",
            scope="local",
            argv=["python3", scripts["leaf_operator_verify"], "--run-dir", str(run_dir), "--mode", "functional"],
            required=True,
            consumes=[
                str(chisel_dir),
                str(debug_dir / "boundary_contracts.json"),
                str(reference_dir / "random_hidden_input.pt"),
                str(reference_dir / "weights"),
                str(semantic_tb_dir / "semantic_testbench_manifest.json"),
                str(run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"),
            ],
            produces=[
                str(run_dir / "verification" / "operator_leaf_functional"),
                str(hierarchy_dir / "leaf_functional.json"),
                "operator semantic functional report",
            ],
            capabilities=[
                "operator_leaf_functional_sim",
                "real_tool_execution",
                "targeted_leaf_replay",
                "target_model_operator_semantics",
                "real_model_weights_consumed",
                "random_input_stimulus",
            ],
            targeted_replay={"stage_id_arg": "--stage-id", "scope": "operator_leaf_stage"},
            python_modules=oracle_python_modules,
            python_environment_group=oracle_python_environment_group,
        ),
        "leaf_golden_compare": tool(
            name="case_leaf_golden_compare",
            kind="case_leaf_golden_compare",
            scope="local",
            argv=["python3", scripts["leaf_operator_verify"], "--run-dir", str(run_dir), "--mode", "golden"],
            required=True,
            consumes=[
                str(chisel_dir),
                str(reference_dir / "random_hidden_input.pt"),
                str(reference_dir / "weights"),
                str(semantic_tb_dir / "semantic_testbench_manifest.json"),
                str(run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"),
                str(run_dir / "verification" / "operator_leaf_functional"),
            ],
            produces=[
                str(run_dir / "verification" / "operator_leaf_golden"),
                str(hierarchy_dir / "leaf_golden_compare.json"),
                "operator semantic golden report",
            ],
            capabilities=[
                "operator_leaf_golden_compare",
                "independent_golden_compare",
                "targeted_leaf_replay",
                "target_model_operator_semantics",
                "real_model_weights_consumed",
                "independent_expected_output",
            ],
            targeted_replay={"stage_id_arg": "--stage-id", "scope": "operator_leaf_stage"},
            python_modules=oracle_python_modules,
            python_environment_group=oracle_python_environment_group,
        ),
        "operator_leaf_semantic_evidence": tool(
            name="case_operator_leaf_semantic_evidence",
            kind="semantic_evidence_assemble",
            scope="local",
            argv=[
                "python3",
                scripts["semantic_evidence"],
                "--run-dir",
                str(run_dir),
                "--level",
                "operator_leaf_functional",
                "--out",
                str(semantic_evidence_dir / "operator_leaf.json"),
            ],
            required=True,
            consumes=[
                str(reference_dir / "reference_manifest.json"),
                str(semantic_tb_dir / "semantic_testbench_manifest.json"),
                str(run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"),
                str(run_dir / "verification" / "operator_leaf_functional"),
                str(run_dir / "verification" / "operator_leaf_golden"),
                "operator leaf RTL output captures",
            ],
            produces=[str(semantic_evidence_dir / "operator_leaf.json"), "operator semantic evidence report"],
            capabilities=[
                "semantic_comparison_evidence",
                "real_weight_provenance",
                "operator_coverage_evidence",
            ],
        ),
        "tb_scaffold": tool(
            name="case_tb_scaffold",
            kind="case_tb_scaffold",
            scope="local",
            argv=["python3", scripts["hierarchical_check"], "--run-dir", str(run_dir), "--gate", "tb_scaffold"],
            required=True,
            consumes=[
                str(chisel_dir),
                str(semantic_tb_dir / "semantic_testbench_manifest.json"),
                str(semantic_tb_dir / "dut_weight_binding_requirements.json"),
                str(run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"),
            ],
            produces=[str(hierarchy_dir / "tb_scaffold.json")],
            capabilities=["gate_checker_only", "tb_scaffold_check"],
        ),
        "single_layer_kernel": tool(
            name="case_single_transformer_layer",
            kind="case_single_transformer_layer",
            scope="local",
            argv=["python3", scripts["hierarchical_check"], "--run-dir", str(run_dir), "--gate", "single_layer_kernel"],
            required=True,
            consumes=[
                str(chisel_dir),
                str(hierarchy_dir / "stage_leaf_static.json"),
                str(hierarchy_dir / "tb_scaffold.json"),
                str(semantic_tb_dir / "semantic_testbench_manifest.json"),
                str(run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"),
            ],
            produces=[str(hierarchy_dir / "single_layer_kernel.json")],
            capabilities=["gate_checker_only", "single_layer_kernel_static_check"],
        ),
        "single_layer_functional_sim": tool(
            name="case_single_layer_functional",
            kind="case_single_layer_functional",
            scope="local",
            argv=["python3", scripts["single_layer_stream_sim"], "--run-dir", str(run_dir), "--mode", "functional"],
            required=True,
            consumes=[
                str(chisel_dir),
                str(hierarchy_dir / "leaf_functional.json"),
                str(hierarchy_dir / "single_layer_kernel.json"),
                str(reference_dir / "random_hidden_input.pt"),
                str(reference_dir / "weights"),
                str(semantic_tb_dir / "semantic_testbench_manifest.json"),
                str(run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"),
            ],
            produces=[
                str(run_dir / "verification" / "single_layer" / "single_layer_functional_report.json"),
                str(debug_dir / "boundary_trace.json"),
                str(hierarchy_dir / "single_layer_functional.json"),
                "single layer semantic functional report",
            ],
            capabilities=[
                "single_layer_functional_sim",
                "real_single_layer_functional_sim",
                "boundary_trace",
                "targeted_replay",
                "target_model_single_layer_semantics",
                "real_model_weights_consumed",
                "random_input_stimulus",
            ],
            python_modules=oracle_python_modules,
            python_environment_group=oracle_python_environment_group,
        ),
        "single_layer_golden_compare": tool(
            name="case_single_layer_golden_compare",
            kind="case_single_layer_golden_compare",
            scope="local",
            argv=["python3", scripts["single_layer_stream_sim"], "--run-dir", str(run_dir), "--mode", "golden"],
            required=True,
            consumes=[
                str(chisel_dir),
                str(run_dir / "verification" / "single_layer" / "single_layer_functional_report.json"),
                str(reference_dir / "single_layer_output.pt"),
                str(reference_dir / "random_hidden_input.pt"),
                str(reference_dir / "weights"),
                str(semantic_tb_dir / "semantic_testbench_manifest.json"),
                str(run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"),
                "target-model single-layer golden",
            ],
            produces=[
                str(run_dir / "verification" / "single_layer" / "single_layer_golden_compare.json"),
                str(hierarchy_dir / "single_layer_golden_compare.json"),
                "single layer semantic golden report",
            ],
            capabilities=[
                "single_layer_golden_compare",
                "independent_golden_compare",
                "numeric_compare",
                "target_model_single_layer_semantics",
                "real_model_weights_consumed",
                "independent_expected_output",
            ],
            python_modules=oracle_python_modules,
            python_environment_group=oracle_python_environment_group,
        ),
        "single_layer_semantic_evidence": tool(
            name="case_single_layer_semantic_evidence",
            kind="semantic_evidence_assemble",
            scope="local",
            argv=[
                "python3",
                scripts["semantic_evidence"],
                "--run-dir",
                str(run_dir),
                "--level",
                "single_layer_functional",
                "--out",
                str(semantic_evidence_dir / "single_layer.json"),
            ],
            required=True,
            consumes=[
                str(reference_dir / "reference_manifest.json"),
                str(semantic_tb_dir / "semantic_testbench_manifest.json"),
                str(run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"),
                str(run_dir / "verification" / "single_layer"),
                "single layer RTL output capture",
            ],
            produces=[str(semantic_evidence_dir / "single_layer.json"), "single layer semantic evidence report"],
            capabilities=[
                "semantic_comparison_evidence",
                "real_weight_provenance",
                "connected_single_layer_evidence",
            ],
        ),
        "real_weight_artifacts": tool(
            name="case_real_weight_artifacts",
            kind="case_real_weight_artifacts",
            scope="local",
            argv=["python3", scripts["hierarchical_check"], "--run-dir", str(run_dir), "--gate", "real_weights"],
            required=True,
            consumes=[
                str(real_dir / "weight_manifest.json"),
                str(real_dir / "full_tensor_catalog.json"),
                str(real_dir / "transformer_block_weight_catalog.json"),
                str(real_dir / "artifact_hashes.json"),
            ],
            produces=[str(hierarchy_dir / "real_weights.json")],
            capabilities=["complete_real_weight_catalog_check", "artifact_hash_check", "gate_checker_only"],
        ),
        "multilayer_pipeline": tool(
            name="case_multilayer_pipeline",
            kind="case_multilayer_pipeline",
            scope="local",
            argv=["python3", scripts["hierarchical_check"], "--run-dir", str(run_dir), "--gate", "multilayer_pipeline"],
            required=True,
            consumes=[
                str(reference_dir / "reference_manifest.json"),
                str(semantic_tb_dir / "semantic_testbench_manifest.json"),
                str(run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"),
                str(run_dir / "verification" / "board_interface" / "board_source_identity.json"),
            ],
            produces=[str(hierarchy_dir / "multilayer_pipeline.json")],
            capabilities=["gate_checker_only", "multilayer_pipeline_static_check"],
        ),
        "multilayer_functional_sim": tool(
            name="case_multilayer_functional",
            kind="case_multilayer_functional",
            scope="local",
            argv=["python3", scripts["hierarchical_check"], "--run-dir", str(run_dir), "--gate", "multilayer_functional"],
            required=True,
            produces=[str(hierarchy_dir / "multilayer_functional.json")],
            capabilities=["gate_checker_only", "multilayer_functional_report_check"],
        ),
        "pipeline_deadlock_check": tool(
            name="case_pipeline_deadlock_check",
            kind="case_pipeline_deadlock_check",
            scope="local",
            argv=["python3", scripts["hierarchical_check"], "--run-dir", str(run_dir), "--gate", "pipeline_deadlock"],
            required=True,
            produces=[str(hierarchy_dir / "pipeline_deadlock.json")],
            capabilities=["gate_checker_only", "pipeline_deadlock_report_check"],
        ),
        "axi_ddr_interface": tool(
            name="case_axi_ddr_interface",
            kind="case_axi_ddr_interface",
            scope="local",
            argv=["python3", scripts["hierarchical_check"], "--run-dir", str(run_dir), "--gate", "axi_ddr_interface"],
            required=True,
            consumes=[
                str(run_dir / "verification" / "board_interface" / "board_source_identity.json"),
                str(run_dir / "verification" / "board_simulation" / "board_simulation_manifest.json"),
            ],
            produces=[str(hierarchy_dir / "axi_ddr_interface.json")],
            capabilities=[
                "gate_checker_only",
                "axi_ddr_interface_check",
                *sorted(EXACT_BOARD_ACCEPTANCE_CAPABILITIES),
            ],
        ),
        "axi_protocol_check": tool(
            name="case_axi_protocol_check",
            kind="case_axi_protocol_check",
            scope="local",
            argv=["python3", scripts["hierarchical_check"], "--run-dir", str(run_dir), "--gate", "axi_protocol"],
            required=True,
            produces=[str(hierarchy_dir / "axi_protocol.json")],
            capabilities=["gate_checker_only", "axi_protocol_report_check"],
        ),
        "ddr_image_roundtrip": tool(
            name="case_ddr_image_roundtrip",
            kind="case_ddr_image_roundtrip",
            scope="local",
            argv=["python3", scripts["hierarchical_check"], "--run-dir", str(run_dir), "--gate", "ddr_image_roundtrip"],
            required=True,
            consumes=[
                str(run_dir / "verification" / "board_simulation" / "board_simulation_manifest.json"),
                str(diagnosis_path),
                str(deadlock_axi_path),
            ],
            produces=[str(hierarchy_dir / "ddr_image_roundtrip.json")],
            capabilities=["gate_checker_only", "ddr_image_roundtrip_report_check"],
        ),
        "vcs_functional_sim": tool(
            name="case_vcs_functional_sim",
            kind="vcs_real_functional_sim",
            scope="remote",
            argv=["python3", scripts["vcs_functional"], "--run-dir", str(run_dir)],
            required=True,
            env={
                "REMOTE_SIM_TIMEOUT_SEC": remote_sim_timeout_sec,
                "SPATIALACC_MAX_HEAVY_JOBS": "1",
            },
            required_group="functional_sim",
            consumes=[
                str(chisel_dir),
                str(semantic_tb_dir / "board" / "input.memh"),
                str(semantic_tb_dir / "board" / "expected.memh"),
                str(run_dir / "verification" / "board_simulation" / "full_weight_image_manifest.json"),
                str(run_dir / "verification" / "board_simulation" / "board_simulation_manifest.json"),
                str(run_dir / "verification" / "board_interface" / "board_source_identity.json"),
                str(run_dir / "input" / "sample_project_index.json"),
                str(debug_dir / "trace_manifest.json"),
                "exact sample board wrapper and BD simulation sources",
            ],
            produces=[
                str(run_dir / "verification" / "vcs" / "case_functional_compile.log"),
                str(run_dir / "verification" / "vcs" / "case_functional_sim.log"),
                str(run_dir / "verification" / "vcs" / "case_board_vcs_functional.json"),
                str(run_dir / "verification" / "board_simulation" / "rtl_output.memh"),
                str(debug_dir / "boundary_trace.json"),
            ],
            requires_external_tool="vcs",
            capabilities=[
                "real_functional_sim",
                "board_wrapper_functional_sim",
                "boundary_trace",
                "targeted_replay",
                "semantic_checkpoint_capture",
                "checkpoint_replay_screen",
                "content_addressed_checkpoint_retention",
                "single_heavy_job_resource_guard",
                "all_target_layers",
                "real_model_weights_consumed",
                "complete_scope_weight_image",
                "random_input_stimulus",
                "exact_sample_board_wrapper_simulation",
                "exact_sample_clock_reset_calibration_timing",
                "recursive_simulation_source_closure",
                "elaborated_hierarchy_binding",
                "structured_axi_protocol_monitors",
                "multilayer_board_integration",
            ],
        ),
        "vcs_evidence_analyzer": tool(
            name="case_vcs_evidence_analyzer",
            kind="vcs_evidence_analyzer",
            scope="local",
            argv=["python3", scripts["vcs_analyzer"], "--run-dir", str(run_dir), "--out", str(diagnosis_path)],
            required=True,
            consumes=[
                str(run_dir / "verification" / "vcs" / "case_board_vcs_functional.json"),
                str(run_dir / "verification" / "vcs" / "case_functional_sim.log"),
                str(reference_dir / "reference_manifest.json"),
                str(semantic_tb_dir / "board" / "input.memh"),
                str(run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"),
                str(run_dir / "verification" / "board_interface" / "board_source_identity.json"),
                str(debug_dir / "boundary_trace.json"),
            ],
            produces=[
                str(diagnosis_path),
                str(debug_dir / "boundary_trace.json"),
                "board semantic comparison report",
            ],
            capabilities=[
                "vcs_evidence_analyzer",
                "failure_localization_input",
                "semantic_comparison_evidence",
                "real_weight_provenance",
                "exact_sample_board_wrapper_identity",
                "boundary_trace",
            ],
            python_modules=oracle_python_modules,
            python_environment_group=oracle_python_environment_group,
        ),
        "board_semantic_evidence": tool(
            name="case_board_semantic_evidence",
            kind="semantic_evidence_assemble",
            scope="local",
            argv=[
                "python3",
                scripts["semantic_evidence"],
                "--run-dir",
                str(run_dir),
                "--level",
                "axi_ddr_functional",
                "--out",
                str(semantic_evidence_dir / "board_axi_ddr.json"),
            ],
            required=True,
            consumes=[
                str(reference_dir / "reference_manifest.json"),
                str(semantic_tb_dir / "semantic_testbench_manifest.json"),
                str(run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"),
                str(run_dir / "verification" / "board_interface" / "board_source_identity.json"),
                str(diagnosis_path),
                str(deadlock_axi_path),
                "board RTL output capture",
            ],
            produces=[str(semantic_evidence_dir / "board_axi_ddr.json"), "board semantic evidence report"],
            capabilities=[
                "semantic_comparison_evidence",
                "real_weight_provenance",
                "all_target_layers",
                "exact_sample_board_wrapper_identity",
            ],
        ),
        "deadlock_axi_check": tool(
            name="case_deadlock_axi_check",
            kind="case_deadlock_axi_check",
            scope="local",
            argv=[
                "python3",
                scripts["deadlock_axi_check"],
                "--run-dir",
                str(run_dir),
                "--out",
                str(deadlock_axi_path),
                "--rtl-wrapper",
                rtl_wrapper,
                "--testbench",
                tb_path,
            ],
            required=True,
            consumes=[
                str(run_dir / "verification" / "real_tools" / "case_vcs_functional_sim.json"),
                str(diagnosis_path),
                str(chisel_dir / "runtime" / "runtime_config.json"),
                str(chisel_dir / "memory" / "memory_layout.json"),
                rtl_wrapper,
                tb_path,
            ],
            produces=[str(deadlock_axi_path)],
            capabilities=["deadlock_axi_check", "axi_liveness_check"],
        ),
        "vivado_synthesis": tool(
            name="case_vivado_synthesis",
            kind="exact_app_shell_vivado",
            scope="remote",
            argv=[
                "python3",
                scripts["vivado_app_shell"],
                "--run-dir",
                str(run_dir),
                "--mode",
                "synth",
            ],
            required=True,
            consumes=[str(chisel_dir / "vivado"), str(run_dir / "generated" / "backend" / "constraints" / "app_shell_integration_contract.json")],
            produces=[str(run_dir / "app_shell_runtime_bitstream" / "app_shell_runtime_inspection.txt")],
            requires_external_tool="vivado",
            capabilities=["exact_target_board_app_shell", "vivado_synthesis"],
        ),
        "vivado_synthesis_report_check": tool(
            name="case_vivado_synthesis_report_check",
            kind="vivado_report_check",
            scope="local",
            argv=[
                "python3",
                scripts["vivado_report_check"],
                "--run-dir",
                str(run_dir),
                "--mode",
                "synth",
                "--out",
                str(synth_report_check_path),
            ],
            required=True,
            consumes=[
                str(run_dir / "app_shell_runtime_bitstream" / "app_shell_runtime_inspection.txt"),
            ],
            produces=[str(synth_report_check_path)],
            capabilities=["vivado_synthesis_report_check"],
        ),
        "vivado_implementation": tool(
            name="case_vivado_implementation",
            kind="exact_app_shell_vivado",
            scope="remote",
            argv=[
                "python3",
                scripts["vivado_app_shell"],
                "--run-dir",
                str(run_dir),
                "--mode",
                "bitstream",
            ],
            required=True,
            consumes=[str(chisel_dir / "vivado"), str(run_dir / "generated" / "backend" / "constraints" / "app_shell_integration_contract.json")],
            produces=[str(run_dir / "app_shell_runtime_bitstream")],
            requires_external_tool="vivado",
            capabilities=["exact_target_board_app_shell", "vivado_implementation", "bitstream_generate"],
        ),
        "vivado_implementation_report_check": tool(
            name="case_vivado_implementation_report_check",
            kind="vivado_report_check",
            scope="local",
            argv=[
                "python3",
                scripts["vivado_report_check"],
                "--run-dir",
                str(run_dir),
                "--mode",
                "bitstream",
                "--out",
                str(bitstream_report_check_path),
            ],
            required=True,
            consumes=[
                str(run_dir / "app_shell_runtime_bitstream" / "app_shell_runtime_inspection.txt"),
                str(run_dir / "app_shell_runtime_bitstream" / "app_shell_impl_timing.rpt"),
                str(run_dir / "app_shell_runtime_bitstream" / "app_shell_impl_utilization.rpt"),
                str(run_dir / "app_shell_runtime_bitstream" / "app_shell_impl_power.rpt"),
            ],
            produces=[str(bitstream_report_check_path)],
            capabilities=["vivado_implementation_report_check", "timing_drc_report_check"],
        ),
        "vivado_power": tool(
            name="case_vivado_power",
            kind="exact_app_shell_vivado",
            scope="remote",
            argv=["python3", scripts["vivado_app_shell"], "--run-dir", str(run_dir), "--mode", "bitstream"],
            required=False,
            consumes=[str(run_dir / "app_shell_runtime_bitstream" / "app_shell_impl_power.rpt")],
            produces=[str(run_dir / "app_shell_runtime_bitstream" / "app_shell_impl_power.rpt")],
            requires_external_tool="vivado",
            capabilities=["exact_target_board_app_shell", "vivado_post_implementation_power"],
        ),
        "stage7_metrics": tool(
            name="case_stage7_metrics",
            kind="stage7_metrics",
            scope="local",
            argv=[
                "python3",
                scripts["stage7_metrics"],
                "--run-dir",
                str(run_dir),
                "--out",
                str(stage7_metrics_path),
            ],
            required=True,
            consumes=[
                str(run_dir / "app_shell_runtime_bitstream" / "app_shell_impl_utilization.rpt"),
                str(run_dir / "app_shell_runtime_bitstream" / "app_shell_impl_timing.rpt"),
                str(run_dir / "app_shell_runtime_bitstream" / "app_shell_impl_power.rpt"),
                str(run_dir / "verification" / "board_simulation" / "reports" / "performance_counter_report.json"),
            ],
            produces=[str(stage7_metrics_path)],
            capabilities=["latency_cycles", "tokens_per_second", "resource_metrics", "power_metrics"],
        ),
        "runtime_abi_check": tool(
            name="case_runtime_abi_check",
            kind="case_runtime_abi_check",
            scope="local",
            argv=[
                "python3",
                scripts["runtime_abi_check"],
                "--run-dir",
                str(run_dir),
                "--runtime-config",
                str(chisel_dir / "runtime" / "runtime_config.json"),
                "--memory-layout",
                str(chisel_dir / "memory" / "memory_layout.json"),
                "--board-profile",
                str(run_dir / "input" / "target_board_profile.json"),
                "--generated-top",
                str(chisel_dir / "GeneratedAxiDdrTop.sv"),
                "--board-wrapper",
                rtl_wrapper,
                "--vivado-report-check",
                str(bitstream_report_check_path),
                "--out",
                str(runtime_abi_check_path),
            ],
            required=True,
            consumes=[
                str(chisel_dir / "GeneratedAxiDdrTop.sv"),
                str(chisel_dir / "runtime" / "runtime_config.json"),
                str(chisel_dir / "memory" / "memory_layout.json"),
                str(run_dir / "input" / "target_board_profile.json"),
                rtl_wrapper,
                str(bitstream_report_check_path),
            ],
            produces=[str(runtime_abi_check_path)],
            capabilities=["runtime_abi_check", "register_map_check", "ddr_layout_check"],
        ),
        "runtime_bitstream": tool(
            name="case_runtime_bitstream",
            kind="case_runtime_bitstream",
            scope="remote",
            argv=["python3", scripts["hierarchical_check"], "--run-dir", str(run_dir), "--gate", "runtime_bitstream"],
            required=True,
            capabilities=["gate_checker_only", "runtime_bitstream_report_check"],
        ),
    }
    missing_scripts = [path for path in scripts.values() if not repo_has(path)]
    if not repo_has(str(semantic_adapter)):
        missing_scripts.append(str(semantic_adapter))
    adapter_errors = [f"missing adapter script: {path}" for path in missing_scripts]
    if model_dir is None:
        adapter_errors.append(
            "target model checkpoint directory is not configured; supply model_dir in the current run input"
        )
    return {
        "schema_version": CASE_ADAPTER_SCHEMA,
        "status": "ready" if not adapter_errors else "incomplete",
        "case_id": f"{family}_hf_case",
        "model_family": family,
        "model_id": model_id,
        "model_semantic_adapter": {
            "path": str(semantic_adapter),
            "accelerator_scope": "transformer_blocks_only",
            "checkpoint": {
                "model_id": model_id,
                "model_dir": str(model_dir) if model_dir is not None else None,
            },
        },
        "source": "built_in_case_adapter",
        "run_dir": str(run_dir),
        "evidence_gates": GENERIC_EVIDENCE_GATES,
        "tools": tools,
        "paths": {
            "real_artifact_dir": str(real_dir),
            "weight_manifest": str(real_dir / "weight_manifest.json"),
            "input_manifest": str(real_dir / "input_manifest.json"),
            "packed_input_manifest": str(real_dir / "input_manifest.json"),
            "packed_weight_manifest": str(real_dir / "packed_weight_manifest.json"),
            "artifact_hashes": str(real_dir / "artifact_hashes.json"),
            "full_tensor_catalog": str(real_dir / "full_tensor_catalog.json"),
            "accelerator_weight_catalog": str(real_dir / "transformer_block_weight_catalog.json"),
            "target_model_reference_manifest": str(reference_dir / "reference_manifest.json"),
            "semantic_testbench_manifest": str(semantic_tb_dir / "semantic_testbench_manifest.json"),
            "dut_weight_binding_requirements": str(semantic_tb_dir / "dut_weight_binding_requirements.json"),
            "dut_weight_binding_manifest": str(run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"),
            "input_memh": str(real_dir / "input_activation.u32.memh"),
            "weight_memh": str(real_dir / "weight_prefetch.u32.memh"),
            "board_input_memh": str(semantic_tb_dir / "board" / "input.memh"),
            "board_expected_memh": str(semantic_tb_dir / "board" / "expected.memh"),
            "full_weight_image_manifest": str(run_dir / "verification" / "board_simulation" / "full_weight_image_manifest.json"),
            "board_simulation_manifest": str(run_dir / "verification" / "board_simulation" / "board_simulation_manifest.json"),
            "board_source_identity": str(run_dir / "verification" / "board_interface" / "board_source_identity.json"),
            "single_layer_golden_memh": str(run_dir / "verification" / "single_layer" / "single_layer_golden.memh"),
            "single_layer_golden_manifest": str(run_dir / "verification" / "single_layer" / "single_layer_golden_manifest.json"),
            "operator_leaf_semantic_evidence": str(run_dir / "verification" / "semantic_evidence" / "operator_leaf.json"),
            "single_layer_semantic_evidence": str(run_dir / "verification" / "semantic_evidence" / "single_layer.json"),
            "board_axi_ddr_semantic_evidence": str(run_dir / "verification" / "semantic_evidence" / "board_axi_ddr.json"),
            "hierarchy_dir": str(hierarchy_dir),
            "diagnosis_path": str(diagnosis_path),
            "deadlock_axi_path": str(deadlock_axi_path),
            "debug_closure_dir": str(debug_dir),
            "boundary_trace_manifest": str(debug_dir / "trace_manifest.json"),
            "boundary_trace": str(debug_dir / "boundary_trace.json"),
            "synth_report_check_path": str(synth_report_check_path),
            "bitstream_report_check_path": str(bitstream_report_check_path),
            "runtime_abi_check_path": str(runtime_abi_check_path),
            "stage7_metrics_path": str(stage7_metrics_path),
            "rtl_wrapper": rtl_wrapper,
            "testbench": tb_path,
        },
        "preconditions": {
            "required_files": [
                {"label": "real weight manifest", "path": str(real_dir / "weight_manifest.json")},
                {"label": "complete checkpoint tensor catalog", "path": str(real_dir / "full_tensor_catalog.json"), "must_have_status": "pass"},
                {"label": "complete transformer-block weight catalog", "path": str(real_dir / "transformer_block_weight_catalog.json"), "must_have_status": "pass"},
                {"label": "target-model reference manifest", "path": str(reference_dir / "reference_manifest.json"), "must_have_status": "ready"},
                {"label": "semantic testbench manifest", "path": str(semantic_tb_dir / "semantic_testbench_manifest.json"), "must_have_status": "ready"},
                {"label": "DUT real-weight binding manifest", "path": str(run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"), "must_have_status": "pass"},
            ],
            "hierarchy_reports": {
                "case_real_weight_artifacts": str(hierarchy_dir / "real_weights.json"),
                "case_stage_leaf_static": str(hierarchy_dir / "stage_leaf_static.json"),
                "case_leaf_functional": str(hierarchy_dir / "leaf_functional.json"),
                "case_leaf_golden_compare": str(hierarchy_dir / "leaf_golden_compare.json"),
                "case_single_layer_functional": str(hierarchy_dir / "single_layer_functional.json"),
                "case_multilayer_pipeline": str(hierarchy_dir / "multilayer_pipeline.json"),
                "case_multilayer_functional": str(hierarchy_dir / "multilayer_functional.json"),
                "case_axi_ddr_interface": str(hierarchy_dir / "axi_ddr_interface.json"),
                "case_axi_protocol_check": str(hierarchy_dir / "axi_protocol.json"),
                "case_ddr_image_roundtrip": str(hierarchy_dir / "ddr_image_roundtrip.json"),
            },
            "rtl_interface": {
                "files": [
                    str(run_dir / "verification" / "board_interface" / "board_source_identity.json"),
                    rtl_wrapper,
                    str(run_dir / "verification" / "board_interface" / "sample_project_sources" / "bd_sim.v"),
                ],
                "required_tokens": [
                    "selected_simulation_source_closure",
                    "selected_simulation_source_closure_sha256",
                    "discovery_provenance",
                    "evidence_records",
                    "compute_slot_abi",
                    "timing_contract",
                    "axi_interfaces",
                ],
            },
            "testbench_artifact_loading": {
                "files": [
                    str(semantic_tb_dir / "semantic_testbench_manifest.json"),
                    str(semantic_tb_dir / "dut_weight_binding_requirements.json"),
                ],
                "required_tokens": ["target_model_inference", "dut_weight_binding", "numeric_policy_sha256"],
            },
            "board_testbench_artifact_loading": {
                "files": [str(run_dir / "verification" / "board_simulation" / "board_simulation_manifest.json"), tb_path],
                "required_tokens": [
                    "source_identity_sha256",
                    "source_closure_sha256",
                    "compile_source_set_sha256",
                    "compiled_sample_source_ids",
                    "replaced_sample_source_ids",
                    "generated_source_ids",
                    "source_replacements",
                    "multilayer_harness",
                    "board_integration_contract",
                    "generated_evidence_records",
                    "elaborated_hierarchy",
                    "protocol_monitor_contract",
                    "execution_outputs",
                    "exact_sample_top_module",
                    "uses_memory_model_source_ids",
                    "forbidden_construct_scan",
                    "weight_image",
                    "expected_output",
                    "runtime_plusargs",
                ],
            },
        },
        "diagnosis": {
            "path": str(diagnosis_path),
            "trigger_tool_names": ["case_vcs_functional_sim"],
        },
        "acceptance": {
            "functional_sim_accepts_any_one_of": ["case_vcs_functional_sim"],
            "legacy_liveness_tools_not_acceptance": [],
            "pass_regex_source": str(run_dir / "verification" / "board_simulation" / "board_simulation_manifest.json"),
            "pass_regex_policy": "must be supplied by the current case adapter's exact sample-project testbench manifest",
            "exact_board_contract": {
                "preflight_schema_version": "spatialaccagent.exact_board_preflight.v1",
                "post_run_schema_version": "spatialaccagent.exact_board_acceptance.v1",
                "checker_tool_role": "axi_ddr_interface",
                "post_run_validator": "accagent.framework.board_acceptance_contract.validate_exact_board_acceptance",
                "fail_closed": True,
                "required_capabilities": sorted(EXACT_BOARD_ACCEPTANCE_CAPABILITIES),
            },
        },
        "implementation_notes": [
            "The current model family selects semantic rules only; all verification and backend tool roles are generic.",
            "Framework core stages depend on case_* gates and current-run artifacts, never on a prior model family.",
        ],
        "errors": adapter_errors,
    }


def qwen2_hf_case_adapter(model: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    """Compatibility alias for historical callers of the Qwen2 built-in path."""

    return built_in_transformer_case_adapter(model, run_dir, "qwen2")


def missing_case_adapter(model: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    family = safe_id(model.get("model_type"))
    case_id = f"{family}_missing_case_adapter"
    return {
        "schema_version": CASE_ADAPTER_SCHEMA,
        "status": "missing",
        "case_id": case_id,
        "model_family": family,
        "model_id": model.get("model_id") or model.get("name"),
        "source": "no_matching_case_adapter",
        "run_dir": str(run_dir),
        "evidence_gates": GENERIC_EVIDENCE_GATES,
        "tools": {},
        "paths": {},
        "preconditions": {},
        "diagnosis": {},
        "acceptance": {
            "functional_sim_accepts_any_one_of": [],
            "legacy_liveness_tools_not_acceptance": [],
        },
        "errors": [
            "No verification case adapter was provided for this model family. "
            "Provide SPATIALACC_CASE_ADAPTER or a case_adapter.json in tool materials with real weight, TB/RTL, simulator, and diagnosis tools."
        ],
        "implementation_notes": [
            "Qwen/OPT examples are not framework defaults for unrelated models.",
        ],
    }


def semantic_contract_only_case_adapter(model: dict[str, Any], run_dir: Path, family: str) -> dict[str, Any]:
    """Expose a built-in semantic contract without claiming board readiness.

    The framework can already catalog weights and build model references from
    these contracts.  Exact board generation still needs a family-specific
    shell/testbench binding, so the adapter remains incomplete until those
    tools are supplied.  Keeping this state explicit prevents a new model from
    silently taking the wrong Qwen/OPT path.
    """

    semantic_path = BUILTIN_SEMANTIC_ADAPTERS.get(family)
    contract_exists = semantic_path is not None and semantic_path.is_file()
    model_id = model.get("model_id") or model.get("name") or family
    result = missing_case_adapter(model, run_dir)
    result.update(
        {
            "case_id": f"{family}_hf_case",
            "model_family": family,
            "source": "built_in_semantic_contract",
            "status": "incomplete" if contract_exists else "missing",
            "model_semantic_adapter": {
                "path": str(semantic_path) if semantic_path else "",
                "accelerator_scope": "transformer_blocks_only",
                "checkpoint": {"model_id": str(model_id)},
            },
            "paths": {
                "semantic_adapter": str(semantic_path) if semantic_path else "",
                "real_artifact_dir": str(run_dir / "verification" / "model_weights"),
                "target_model_reference_manifest": str(
                    run_dir / "verification" / "model_reference" / "reference_manifest.json"
                ),
            },
            "implementation_notes": [
                "The semantic contract is family-specific and can drive generic weight/reference preparation.",
                "Exact AXI/DDR board-shell, VCS evidence, and Vivado runtime tools must be bound before Stage 5/7 execution.",
            ],
        }
    )
    result["errors"] = [
        f"Built-in {family} semantic contract is ready, but its exact-board tool chain is not bound yet.",
        "Provide a family adapter with real board testbench, hierarchical evidence analyzer, and backend commands before starting a formal run.",
    ] if contract_exists else [f"Built-in semantic contract is missing for model family: {family}"]
    return result


def build_case_adapter(model: dict[str, Any], run_dir: Path, tool_materials_dir: Path) -> dict[str, Any]:
    custom_path = user_adapter_path(tool_materials_dir)
    if custom_path:
        return normalize_user_adapter(read_json(custom_path), custom_path, run_dir)
    family = str(model.get("model_type") or "").strip().lower()
    if family in BUILTIN_SEMANTIC_ADAPTERS:
        return built_in_transformer_case_adapter(model, run_dir, family)
    return missing_case_adapter(model, run_dir)


def refresh_builtin_case_adapter(
    adapter: dict[str, Any],
    model: dict[str, Any],
    run_dir: Path,
    tool_materials_dir: Path,
) -> dict[str, Any]:
    """Refresh framework-owned built-in adapters while preserving user adapters.

    SACG states store the adapter artifact used for a previous run. During
    framework development the built-in adapter may gain new tool contracts. A
    user-provided adapter is part of the run input and must not be replaced, but
    a framework-owned built-in adapter can be regenerated from the current code
    so Stage6/7/8 see the repaired tool capability contract.
    """

    if adapter.get("source") != "built_in_case_adapter":
        return adapter
    refreshed = build_case_adapter(model, run_dir, tool_materials_dir)
    if refreshed.get("source") != "built_in_case_adapter":
        return adapter
    refreshed["refreshed_from_artifact"] = {
        "case_id": adapter.get("case_id"),
        "model_family": adapter.get("model_family"),
        "reason": "framework_owned_builtin_adapter_contract_updated",
    }
    return refreshed


def gate_name(adapter: dict[str, Any], key: str) -> str:
    gates = adapter.get("evidence_gates", {}) if isinstance(adapter.get("evidence_gates"), dict) else {}
    return str(gates.get(key) or GENERIC_EVIDENCE_GATES[key])


def generic_required_gate_names(adapter: dict[str, Any]) -> set[str]:
    return {
        gate_name(adapter, "stage_leaf_static"),
        gate_name(adapter, "leaf_functional"),
        gate_name(adapter, "leaf_golden_compare"),
        gate_name(adapter, "operator_leaf_semantic_evidence"),
        gate_name(adapter, "boundary_contract"),
        gate_name(adapter, "real_weight_artifacts"),
        gate_name(adapter, "target_model_reference"),
        gate_name(adapter, "semantic_testbench"),
        gate_name(adapter, "tb_scaffold"),
        gate_name(adapter, "single_layer_kernel"),
        gate_name(adapter, "single_layer_functional"),
        gate_name(adapter, "single_layer_golden_compare"),
        gate_name(adapter, "single_layer_semantic_evidence"),
        gate_name(adapter, "multilayer_pipeline"),
        gate_name(adapter, "multilayer_functional"),
        gate_name(adapter, "pipeline_deadlock"),
        gate_name(adapter, "axi_ddr_interface"),
        gate_name(adapter, "axi_protocol"),
        gate_name(adapter, "ddr_image_roundtrip"),
        gate_name(adapter, "board_semantic_evidence"),
        gate_name(adapter, "functional_sim"),
        gate_name(adapter, "board_interface_discovery"),
        gate_name(adapter, "vivado_synthesis"),
        gate_name(adapter, "vivado_implementation"),
        gate_name(adapter, "runtime_abi"),
        gate_name(adapter, "runtime_bitstream"),
        gate_name(adapter, "board_runtime"),
    }


def adapter_tool(adapter: dict[str, Any], role: str) -> dict[str, Any] | None:
    tools = adapter.get("tools", {}) if isinstance(adapter.get("tools"), dict) else {}
    item = tools.get(role)
    return item if isinstance(item, dict) else None


def planned_evidence_paths_from_adapter(adapter: dict[str, Any], run_dir: Path, gate_or_tool: str) -> dict[str, Any]:
    paths = adapter.get("paths", {}) if isinstance(adapter.get("paths"), dict) else {}
    real_dir = Path(str(paths.get("real_artifact_dir") or (run_dir / "verification" / "case_real_weights")))
    generated_root = run_dir / "generated" / "chisel"
    debug_dir = Path(str(paths.get("debug_closure_dir") or (run_dir / "verification" / "debug_closure")))
    hierarchy_dir = Path(str(paths.get("hierarchy_dir") or (run_dir / "verification" / "case_hierarchy")))

    def unique(values: list[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for value in values:
            text = str(value)
            if text in seen:
                continue
            seen.add(text)
            result.append(text)
        return result

    table = {
        gate_name(adapter, "real_weight_artifacts"): {
            "planned_consumes": ["current case-adapter target checkpoint and model configuration"],
            "planned_produces": [
                str(paths.get("weight_manifest") or real_dir / "weight_manifest.json"),
                str(paths.get("full_tensor_catalog") or real_dir / "full_tensor_catalog.json"),
                str(paths.get("accelerator_weight_catalog") or real_dir / "transformer_block_weight_catalog.json"),
                str(paths.get("artifact_hashes") or real_dir / "artifact_hashes.json"),
            ],
        },
        gate_name(adapter, "target_model_reference"): {
            "planned_consumes": [
                str(paths.get("weight_manifest") or real_dir / "weight_manifest.json"),
                str(paths.get("accelerator_weight_catalog") or real_dir / "transformer_block_weight_catalog.json"),
                str(run_dir / "input" / "model_config.json"),
                str(run_dir / "input" / "numeric_policy.json"),
            ],
            "planned_produces": [
                str(paths.get("target_model_reference_manifest") or run_dir / "verification" / "model_reference" / "reference_manifest.json"),
                str(run_dir / "verification" / "model_reference" / "random_hidden_input.pt"),
                str(run_dir / "verification" / "model_reference" / "single_layer_output.pt"),
                str(run_dir / "verification" / "model_reference" / "full_model_output.pt"),
            ],
        },
        gate_name(adapter, "semantic_testbench"): {
            "planned_consumes": [
                str(paths.get("target_model_reference_manifest") or run_dir / "verification" / "model_reference" / "reference_manifest.json"),
                str(run_dir / "pipeline_planning" / "pipeline_plan.json"),
                str(run_dir / "input" / "numeric_policy.json"),
                str(paths.get("dut_weight_binding_manifest") or run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"),
            ],
            "planned_produces": [
                str(paths.get("semantic_testbench_manifest") or run_dir / "verification" / "semantic_testbench" / "semantic_testbench_manifest.json"),
                str(paths.get("dut_weight_binding_requirements") or run_dir / "verification" / "semantic_testbench" / "dut_weight_binding_requirements.json"),
                str(run_dir / "verification" / "semantic_testbench" / "stages"),
                str(run_dir / "verification" / "semantic_testbench" / "single_layer"),
            ],
        },
        gate_name(adapter, "stage_leaf_static"): {
            "planned_consumes": [str(generated_root), str(run_dir / "verification_artifacts" / "verification_plan.json")],
            "planned_produces": [str(run_dir / "verification" / "stage_leaf_static" / "stage_leaf_static_report.json")],
        },
        gate_name(adapter, "leaf_functional"): {
            "planned_consumes": [
                str(generated_root),
                str(run_dir / "verification" / "debug_closure" / "boundary_contracts.json"),
                str(paths.get("target_model_reference_manifest") or run_dir / "verification" / "model_reference" / "reference_manifest.json"),
                str(paths.get("semantic_testbench_manifest") or run_dir / "verification" / "semantic_testbench" / "semantic_testbench_manifest.json"),
                str(paths.get("dut_weight_binding_manifest") or generated_root / "memory" / "dut_weight_binding_manifest.json"),
            ],
            "planned_produces": [
                str(run_dir / "verification" / "operator_leaf_functional"),
                str(hierarchy_dir / "leaf_functional.json"),
            ],
        },
        gate_name(adapter, "leaf_golden_compare"): {
            "planned_consumes": [
                str(generated_root),
                str(paths.get("target_model_reference_manifest") or run_dir / "verification" / "model_reference" / "reference_manifest.json"),
                str(paths.get("semantic_testbench_manifest") or run_dir / "verification" / "semantic_testbench" / "semantic_testbench_manifest.json"),
                str(paths.get("dut_weight_binding_manifest") or generated_root / "memory" / "dut_weight_binding_manifest.json"),
                str(run_dir / "verification" / "operator_leaf_functional"),
            ],
            "planned_produces": [
                str(run_dir / "verification" / "operator_leaf_golden"),
                str(hierarchy_dir / "leaf_golden_compare.json"),
            ],
        },
        gate_name(adapter, "boundary_contract"): {
            "planned_consumes": [
                str(run_dir / "pipeline_planning" / "pipeline_plan.json"),
                str(run_dir / "verification" / "debug_closure" / "boundary_contracts.json"),
                str(run_dir / "verification" / "debug_closure" / "trace_manifest.json"),
            ],
            "planned_produces": [str(hierarchy_dir / "boundary_contract.json")],
        },
        gate_name(adapter, "tb_scaffold"): {
            "planned_consumes": [
                str(generated_root),
                str(paths.get("semantic_testbench_manifest") or run_dir / "verification" / "semantic_testbench" / "semantic_testbench_manifest.json"),
                str(paths.get("dut_weight_binding_requirements") or run_dir / "verification" / "semantic_testbench" / "dut_weight_binding_requirements.json"),
                str(paths.get("dut_weight_binding_manifest") or generated_root / "memory" / "dut_weight_binding_manifest.json"),
            ],
            "planned_produces": [
                str(hierarchy_dir / "tb_scaffold.json"),
            ],
        },
        gate_name(adapter, "single_layer_kernel"): {
            "planned_consumes": [
                str(generated_root),
                str(run_dir / "verification" / "stage_leaf_static" / "stage_leaf_static_report.json"),
                str(paths.get("semantic_testbench_manifest") or run_dir / "verification" / "semantic_testbench" / "semantic_testbench_manifest.json"),
                str(paths.get("dut_weight_binding_manifest") or generated_root / "memory" / "dut_weight_binding_manifest.json"),
            ],
            "planned_produces": [
                str(run_dir / "verification" / "single_layer" / "single_transformer_layer_report.json"),
                str(run_dir / "verification" / "trace" / "single_layer_data_order_trace.json"),
                str(run_dir / "verification" / "trace" / "single_layer_transfer_count_check.json"),
            ],
        },
        gate_name(adapter, "single_layer_functional"): {
            "planned_consumes": [
                str(generated_root),
                str(hierarchy_dir / "leaf_functional.json"),
                str(hierarchy_dir / "single_layer_kernel.json"),
                str(paths.get("target_model_reference_manifest") or run_dir / "verification" / "model_reference" / "reference_manifest.json"),
                str(paths.get("semantic_testbench_manifest") or run_dir / "verification" / "semantic_testbench" / "semantic_testbench_manifest.json"),
                str(paths.get("dut_weight_binding_manifest") or generated_root / "memory" / "dut_weight_binding_manifest.json"),
            ],
            "planned_produces": [str(run_dir / "verification" / "single_layer" / "single_layer_functional_report.json")],
        },
        gate_name(adapter, "single_layer_golden_compare"): {
            "planned_consumes": [
                str(run_dir / "verification" / "single_layer" / "single_layer_functional_report.json"),
                str(paths.get("target_model_reference_manifest") or run_dir / "verification" / "model_reference" / "reference_manifest.json"),
                str(paths.get("semantic_testbench_manifest") or run_dir / "verification" / "semantic_testbench" / "semantic_testbench_manifest.json"),
                str(paths.get("dut_weight_binding_manifest") or generated_root / "memory" / "dut_weight_binding_manifest.json"),
            ],
            "planned_produces": [str(run_dir / "verification" / "single_layer" / "single_layer_golden_compare.json")],
        },
        gate_name(adapter, "multilayer_pipeline"): {
            "planned_consumes": [
                str(generated_root),
                str(paths.get("target_model_reference_manifest") or run_dir / "verification" / "model_reference" / "reference_manifest.json"),
                str(paths.get("semantic_testbench_manifest") or run_dir / "verification" / "semantic_testbench" / "semantic_testbench_manifest.json"),
                str(paths.get("dut_weight_binding_manifest") or generated_root / "memory" / "dut_weight_binding_manifest.json"),
            ],
            "planned_produces": [str(run_dir / "verification" / "multilayer_pipeline" / "case_multilayer_pipeline_report.json")],
        },
        gate_name(adapter, "multilayer_functional"): {
            "planned_consumes": [
                str(generated_root),
                str(run_dir / "verification" / "single_layer" / "single_layer_functional_report.json"),
            ],
            "planned_produces": [str(run_dir / "verification" / "multilayer_pipeline" / "multilayer_functional_report.json")],
        },
        gate_name(adapter, "pipeline_deadlock"): {
            "planned_consumes": [str(run_dir / "verification" / "multilayer_pipeline" / "multilayer_functional_report.json")],
            "planned_produces": [str(run_dir / "verification" / "multilayer_pipeline" / "pipeline_deadlock_check.json")],
        },
        gate_name(adapter, "axi_ddr_interface"): {
            "planned_consumes": [
                str(paths.get("board_source_identity") or run_dir / "verification" / "board_interface" / "board_source_identity.json"),
                str(paths.get("board_simulation_manifest") or run_dir / "verification" / "board_simulation" / "board_simulation_manifest.json"),
            ],
            "planned_produces": [str(run_dir / "verification" / "axi_ddr" / "case_axi_ddr_interface_report.json")],
        },
        gate_name(adapter, "axi_protocol"): {
            "planned_consumes": [
                str(run_dir / "verification" / "axi_ddr" / "case_axi_ddr_interface_report.json"),
                str(generated_root / "runtime" / "runtime_config.json"),
            ],
            "planned_produces": [str(run_dir / "verification" / "axi_ddr" / "axi_protocol_check.json")],
        },
        gate_name(adapter, "ddr_image_roundtrip"): {
            "planned_consumes": [
                str(paths.get("board_input_memh") or run_dir / "verification" / "semantic_testbench" / "board" / "input.memh"),
                str(paths.get("board_expected_memh") or run_dir / "verification" / "semantic_testbench" / "board" / "expected.memh"),
                str(paths.get("full_weight_image_manifest") or run_dir / "verification" / "board_simulation" / "full_weight_image_manifest.json"),
                str(paths.get("board_simulation_manifest") or run_dir / "verification" / "board_simulation" / "board_simulation_manifest.json"),
                str(run_dir / "verification" / "axi_ddr" / "axi_protocol_check.json"),
            ],
            "planned_produces": [str(run_dir / "verification" / "axi_ddr" / "ddr_image_roundtrip.json")],
        },
        gate_name(adapter, "functional_sim"): {
            "planned_consumes": [
                str(generated_root),
                str(paths.get("target_model_reference_manifest") or run_dir / "verification" / "model_reference" / "reference_manifest.json"),
                str(paths.get("semantic_testbench_manifest") or run_dir / "verification" / "semantic_testbench" / "semantic_testbench_manifest.json"),
                str(paths.get("dut_weight_binding_manifest") or generated_root / "memory" / "dut_weight_binding_manifest.json"),
                str(paths.get("board_source_identity") or run_dir / "verification" / "board_interface" / "board_source_identity.json"),
                str(paths.get("board_simulation_manifest") or run_dir / "verification" / "board_simulation" / "board_simulation_manifest.json"),
                str(paths.get("full_weight_image_manifest") or run_dir / "verification" / "board_simulation" / "full_weight_image_manifest.json"),
                str(paths.get("boundary_trace_manifest") or debug_dir / "trace_manifest.json"),
            ],
            "planned_produces": [
                str(paths.get("diagnosis_path") or run_dir / "verification" / "case_diagnostics" / "vcs_functional_diagnosis.json"),
                str(paths.get("boundary_trace") or debug_dir / "boundary_trace.json"),
                str(debug_dir / "failure_localization.json"),
                str(run_dir / "verification" / "vcs" / "case_functional_sim.log"),
            ],
        },
        gate_name(adapter, "board_interface_discovery"): {
            "planned_consumes": [
                str(generated_root),
                str(run_dir / "input" / "target_board_profile.json"),
            ],
            "planned_produces": [
                str(paths.get("board_source_identity") or run_dir / "verification" / "board_interface" / "board_source_identity.json"),
            ],
        },
        gate_name(adapter, "vivado_synthesis"): {
            "planned_consumes": [
                str(generated_root),
                str(run_dir / "verification" / "axi_ddr" / "case_axi_ddr_interface_report.json"),
                str(run_dir / "verification" / "board_interface" / "case_board_interface_discovery.json"),
            ],
            "planned_produces": [
                str(run_dir / "backend" / "vivado" / "synthesis_report.json"),
                str(run_dir / "backend" / "vivado" / "timing_synth.rpt"),
                str(run_dir / "backend" / "vivado" / "utilization_synth.rpt"),
            ],
        },
        gate_name(adapter, "vivado_implementation"): {
            "planned_consumes": [
                str(run_dir / "backend" / "vivado" / "synthesis_report.json"),
            ],
            "planned_produces": [
                str(run_dir / "backend" / "vivado" / "implementation_report.json"),
                str(run_dir / "backend" / "vivado" / "timing_impl.rpt"),
                str(run_dir / "backend" / "vivado" / "drc.rpt"),
            ],
        },
        gate_name(adapter, "runtime_abi"): {
            "planned_consumes": [
                str(generated_root / "runtime" / "runtime_config.json"),
                str(generated_root / "memory" / "memory_layout.json"),
                str(run_dir / "backend" / "vivado" / "case_runtime.bit"),
            ],
            "planned_produces": [
                str(run_dir / "backend_board" / "case_diagnostics" / "runtime_abi_check.json"),
            ],
        },
        gate_name(adapter, "runtime_bitstream"): {
            "planned_consumes": [
                str(generated_root),
                str(run_dir / "verification" / "multilayer_pipeline" / "case_multilayer_pipeline_report.json"),
                str(run_dir / "verification" / "axi_ddr" / "case_axi_ddr_interface_report.json"),
            ],
            "planned_produces": [
                str(run_dir / "backend" / "vivado" / "case_runtime_bitstream_manifest.json"),
                str(run_dir / "backend" / "vivado" / "timing_summary.rpt"),
                str(run_dir / "backend" / "vivado" / "utilization.rpt"),
                str(run_dir / "backend" / "vivado" / "case_runtime.bit"),
            ],
        },
        gate_name(adapter, "board_runtime"): {
            "planned_consumes": [
                str(run_dir / "backend" / "vivado" / "case_runtime.bit"),
                str(generated_root / "runtime" / "runtime_config.json"),
                str(paths.get("board_input_memh") or run_dir / "verification" / "semantic_testbench" / "board" / "input.memh"),
                str(paths.get("board_expected_memh") or run_dir / "verification" / "semantic_testbench" / "board" / "expected.memh"),
                str(paths.get("full_weight_image_manifest") or run_dir / "verification" / "board_simulation" / "full_weight_image_manifest.json"),
                str(paths.get("dut_weight_binding_manifest") or generated_root / "memory" / "dut_weight_binding_manifest.json"),
                str(paths.get("board_source_identity") or run_dir / "verification" / "board_interface" / "board_source_identity.json"),
            ],
            "planned_produces": [
                str(run_dir / "board" / "case_board_runtime_report.json"),
                str(run_dir / "board" / "case_output_bytes.bin"),
                str(run_dir / "board" / "case_board_runtime.log"),
            ],
        },
    }
    for entry in table.values():
        entry["planned_consumes"] = unique(entry.get("planned_consumes", []))
        entry["planned_produces"] = unique(entry.get("planned_produces", []))
    for role in (
        "weight_manifest_generate",
        "target_model_reference_generate",
        "semantic_testbench_generate",
        "tb_scaffold_generate",
        "tb_scaffold",
        "boundary_contract_check",
        "leaf_functional_sim",
        "leaf_golden_compare",
        "operator_leaf_semantic_evidence",
        "single_layer_kernel",
        "single_layer_functional_sim",
        "single_layer_golden_compare",
        "single_layer_semantic_evidence",
        "multilayer_functional_sim",
        "pipeline_deadlock_check",
        "axi_protocol_check",
        "ddr_image_roundtrip",
        "board_semantic_evidence",
    ):
        item = adapter_tool(adapter, role)
        if item and gate_or_tool == item.get("name"):
            return {"planned_consumes": unique(item.get("consumes", [])), "planned_produces": unique(item.get("produces", []))}
    return table.get(gate_or_tool, {"planned_consumes": [], "planned_produces": []})
