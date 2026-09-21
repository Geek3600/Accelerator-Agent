"""Create backend and board closure plan."""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import time
import zipfile
from pathlib import Path
from typing import Any

from accagent.framework.case_adapter import adapter_tool, build_case_adapter
from accagent.framework.dse_ledger import (
    EXACT_TARGET_BOARD_APP_SHELL_SCOPE,
    QOR_KEYS,
    append_measurement,
    candidate_fingerprint,
    complete_metrics,
    ledger_path,
    load_latest,
)
from accagent.framework.llm_config import resolved_llm_cfg
from accagent.framework.llm_io import build_prompt, parse_json_object, repair_prompt, validate_schema
from accagent.framework.sacg_store import SACGStore
from accagent.framework.sacg_utils import (
    add_constraint,
    add_invariant,
    copy_state,
    constraint_facts,
    artifact_path,
    read_json,
    run_dir_from_state,
    safe_id,
    write_json,
)
from accagent.framework.stage_entry import run_sacg_stage
from accagent.framework.stage_input import (
    merge_board_profile_field_evidence,
    prompt_field_evidence_summary,
)
from accagent.framework.stage_llm import ACTION_GROUNDING_REGISTRY, call_llm_with_retry, llm_timeout_sec, run_stage_agent
from accagent.framework.stage_llm import STAGE_AGENT_SCHEMA
from accagent.framework.stage_team import run_design_team, team_failure_errors, team_summary
from accagent.framework.tool_runner import run_tools


TOUCHED_CONSTRAINTS = [
    "constraint.backend_board.plan",
    "constraint.backend.package",
    "constraint.backend.real_tool_evidence",
    "constraint.backend.app_shell_integration",
    "constraint.backend.recovery_actions",
]
RESOLVED_BOARD_CONSTRAINT = "constraint.backend.resolved_board_profile"
APP_SHELL_INTEGRATION_CONSTRAINT = "constraint.backend.app_shell_integration"
BACKEND_RECOVERY_CONSTRAINT = "constraint.backend.recovery_actions"

TEXT_SUFFIXES = {".md", ".rst", ".txt", ".json", ".yaml", ".yml", ".tcl", ".xdc", ".sv", ".v", ".vh", ".sh", ".py", ".cfg", ".ini"}


BACKEND_RECOVERY_ACTION_SCHEMA = {
    "type": "object",
    "additionalProperties": True,
    "properties": {
        "schema_version": {"type": "string"},
        "status": {"type": "string"},
        "decision": {"type": "string"},
        "summary": {"type": "string"},
        "rationale": {"type": "string"},
        "evidence_citations": {"type": "array", "items": {"type": "object", "additionalProperties": True}},
        "bounded_recovery_actions": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": True,
                "properties": {
                    "id": {"type": "string"},
                    "stage": {"type": "string"},
                    "action_type": {"type": "string"},
                    "rationale": {"type": "string"},
                    "consumes": {"type": "array", "items": {"type": "string"}},
                    "produces": {"type": "array", "items": {"type": "string"}},
                    "tool_roles": {"type": "array", "items": {"type": "string"}},
                    "acceptance_checkers": {"type": "array", "items": {"type": "string"}},
                    "preconditions": {"type": "array", "items": {"type": "string"}},
                    "blocked_until": {"type": "array", "items": {"type": "string"}},
                    "requires_approval": {"type": "boolean"},
                    "approval_boundary": {"type": "array", "items": {"type": "string"}},
                    "on_success": {"type": "string"},
                    "on_failure": {"type": "string"},
                },
                "required": [
                    "id",
                    "stage",
                    "action_type",
                    "rationale",
                    "consumes",
                    "produces",
                    "tool_roles",
                    "acceptance_checkers",
                    "preconditions",
                    "blocked_until",
                    "requires_approval",
                    "approval_boundary",
                    "on_success",
                    "on_failure",
                ],
            },
        },
        "forbidden_actions": {"type": "array", "items": {"type": "string"}},
        "sacg_updates": {"type": "array", "items": {"type": "object", "additionalProperties": True}},
        "next_stage": {"type": "string"},
    },
    "required": [
        "schema_version",
        "status",
        "decision",
        "summary",
        "rationale",
        "evidence_citations",
        "bounded_recovery_actions",
        "forbidden_actions",
        "sacg_updates",
        "next_stage",
    ],
}


QOR_ROUTER_SCHEMA = {
    "type": "object",
    "additionalProperties": True,
    "properties": {
        **STAGE_AGENT_SCHEMA["properties"],
        "qor_decision": {"type": "string", "enum": ["local_optimization", "dse_backtrack", "pass"]},
        "decision_rationale": {"type": "string"},
        "target_misses": {"type": "array", "items": {"type": "object", "additionalProperties": True}},
    },
    "required": [
        *STAGE_AGENT_SCHEMA["required"],
        "qor_decision",
        "decision_rationale",
        "target_misses",
    ],
}


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def backend_execution_scope() -> str:
    return os.environ.get("SPATIALACC_BACKEND_EXECUTION_SCOPE", "all").strip().lower() or "all"


def board_runtime_enabled() -> bool:
    value = os.environ.get("SPATIALACC_RUN_BOARD_TOOLS", "0").strip().lower()
    return value in {"1", "true", "yes", "on"}


def read_docx_text(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as zf:
            xml = zf.read("word/document.xml").decode("utf-8", errors="replace")
    except Exception:
        return ""
    text = re.sub(r"<[^>]+>", " ", xml)
    text = text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    return re.sub(r"\s+", " ", text).strip()


def read_material_text(path: Path) -> str:
    if not path.exists():
        return ""
    if path.is_file():
        if path.suffix.lower() == ".docx":
            return read_docx_text(path)
        if path.suffix.lower() in TEXT_SUFFIXES or not path.suffix:
            return path.read_text(encoding="utf-8", errors="replace")
        return ""
    chunks = []
    for item in sorted(p for p in path.rglob("*") if p.is_file()):
        if item.name.startswith("."):
            continue
        text = read_material_text(item)
        if text:
            chunks.append(f"### {item}\n```text\n{text}\n```")
    return "\n\n".join(chunks)


def source_material_text(source_specs: dict[str, Any], key: str) -> str:
    value = source_specs.get(key)
    if value in {None, ""}:
        return ""
    return read_material_text(Path(str(value)))


def combine_field_evidence(*items: dict[str, Any]) -> dict[str, Any]:
    evidence = []
    seen = set()
    for item in items:
        for entry in item.get("evidence", []) if isinstance(item, dict) else []:
            key = (
                entry.get("field"),
                str(entry.get("value")),
                entry.get("source"),
                entry.get("excerpt"),
            )
            if key in seen:
                continue
            seen.add(key)
            evidence.append(entry)
    return {
        "schema_version": "spatialaccagent.field_evidence.v0",
        "policy": {
            "critical_fields_must_match_evidence_when_present": True,
            "llm_output_is_not_accepted_as_evidence_without_source": True,
        },
        "evidence": evidence,
    }


def changed_profile_fields(before: dict[str, Any], after: dict[str, Any]) -> list[str]:
    fields = [
        ("memory_system.core_side_interface_name", before.get("memory_system", {}).get("core_side_interface_name"), after.get("memory_system", {}).get("core_side_interface_name")),
        ("memory_system.axi_clock", before.get("memory_system", {}).get("axi_clock"), after.get("memory_system", {}).get("axi_clock")),
        ("memory_system.axi_reset", before.get("memory_system", {}).get("axi_reset"), after.get("memory_system", {}).get("axi_reset")),
        ("memory_system.calibration_done_signal", before.get("memory_system", {}).get("calibration_done_signal"), after.get("memory_system", {}).get("calibration_done_signal")),
        ("memory_system.real_board_reference_rtl", before.get("memory_system", {}).get("real_board_reference_rtl"), after.get("memory_system", {}).get("real_board_reference_rtl")),
        ("runtime_interface.mimic_dir", before.get("runtime_interface", {}).get("mimic_dir"), after.get("runtime_interface", {}).get("mimic_dir")),
        ("runtime_interface.xdma_id_default", before.get("runtime_interface", {}).get("xdma_id_default"), after.get("runtime_interface", {}).get("xdma_id_default")),
        ("runtime_interface.ctrl_base", before.get("runtime_interface", {}).get("ctrl_base"), after.get("runtime_interface", {}).get("ctrl_base")),
        ("runtime_interface.ddr_base", before.get("runtime_interface", {}).get("ddr_base"), after.get("runtime_interface", {}).get("ddr_base")),
        ("runtime_interface.output_abs", before.get("runtime_interface", {}).get("output_abs"), after.get("runtime_interface", {}).get("output_abs")),
        ("runtime_interface.ddr_image_default", before.get("runtime_interface", {}).get("ddr_image_default"), after.get("runtime_interface", {}).get("ddr_image_default")),
    ]
    return [name for name, old, new in fields if (old in {None, ""} or str(old).strip().lower() in {"none", "null"}) and new not in {None, ""}]


def nonblank(value: Any) -> bool:
    return value is not None and value != "" and value != [] and str(value).strip().lower() not in {"none", "null"}


def first_nonblank(*values: Any) -> Any:
    for value in values:
        if nonblank(value):
            return value
    return None


def int_or_none(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return int(value.strip(), 0)
        except ValueError:
            return None
    return None


def normalized_axi_prefix(value: Any) -> str | None:
    if not nonblank(value):
        return None
    return str(value).strip().strip("`'\"").rstrip("*").rstrip("_")


def merged_runtime_interface(profile_runtime: dict[str, Any], runtime_config_interface: dict[str, Any]) -> dict[str, Any]:
    merged = dict(profile_runtime)
    for key, value in runtime_config_interface.items():
        if nonblank(value):
            merged[key] = value
    return merged


def resolve_board_profile(state: dict[str, Any], run_dir: Path, out_dir: Path) -> dict[str, Any]:
    original_path = artifact_path(state, "artifact.input.target_board_profile")
    original = read_json(original_path)
    evidence_items = []
    try:
        evidence_items.append(read_json(artifact_path(state, "artifact.input.field_evidence")))
    except Exception:
        pass

    combined = combine_field_evidence(*evidence_items)
    summary = prompt_field_evidence_summary(combined)
    resolved = merge_board_profile_field_evidence(original, summary)
    profile_path = out_dir / "resolved_target_board_profile.json"
    record = {
        **resolved,
        "_stage7_resolution": {
            "schema_version": "spatialaccagent.resolved_target_board_profile.v0",
            "source_target_board_profile": str(original_path),
            "source_field_evidence_count": sum(len(item.get("evidence", [])) for item in evidence_items if isinstance(item, dict)),
            "stage0_field_evidence": str(artifact_path(state, "artifact.input.field_evidence")),
            "filled_fields": changed_profile_fields(original, resolved),
            "policy": "fill only blank board/runtime ABI fields from current-run source evidence; do not invent board facts",
        },
    }
    write_json(profile_path, record)
    return {"path": str(profile_path), "profile": record}


def case_adapter_for_state(state: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    try:
        return read_json(artifact_path(state, "artifact.input.case_adapter"))
    except Exception:
        try:
            model = read_json(artifact_path(state, "artifact.input.model_config"))
        except Exception:
            model = {}
        return build_case_adapter(model, run_dir, Path.cwd() / "accagent" / "framework" / "input_materials" / "tools")


def script_exists(argv: list[str]) -> bool:
    if not argv:
        return False
    script = argv[1] if argv[0] == "python3" and len(argv) > 1 else argv[0]
    return Path(script).exists()


def roles_for_scope(scope: str) -> list[str]:
    exact_app_shell_roles = [
        "board_shell_wrapper_generate",
        "compute_slot_adapter_generate",
        "app_shell_target_discovery_contract",
        "app_shell_target_hint_synthesis",
        "app_shell_target_discovery_after_hint",
        "app_shell_runtime_bitstream",
        "runtime_abi_check",
        "stage7_metrics",
    ]
    if scope in {"none", "plan", "dry_run"}:
        return []
    if scope in {"legacy_standalone", "standalone_backend"}:
        return ["vivado_synthesis", "vivado_synthesis_report_check", "vivado_implementation", "vivado_implementation_report_check", "vivado_power", "stage7_metrics"]
    if scope in {
        "synth",
        "synthesis",
        "vivado_synthesis",
        "impl",
        "implementation",
        "bitstream",
        "vivado_implementation",
        "backend",
        "vivado",
        "runtime_bitstream",
        "runtime",
        "app_shell",
        "app_shell_runtime",
        "app_shell_runtime_bitstream",
        "all",
        "*",
        "backend_board",
        "final",
    }:
        return exact_app_shell_roles
    if scope in {"board", "board_runtime"}:
        return ["board_runtime"]
    return exact_app_shell_roles


def protocol_tool_by_name(tools: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    for tool in tools:
        if str(tool.get("name") or "") == name:
            return tool
    return None


def protocol_tool_by_kind(tools: list[dict[str, Any]], kind: str) -> dict[str, Any] | None:
    for tool in tools:
        if str(tool.get("kind") or "") == kind:
            return tool
    return None


def materialize_case_tool(spec: dict[str, Any], protocols: list[dict[str, Any]], role: str) -> dict[str, Any] | None:
    argv = [str(item) for item in spec.get("argv", [])]
    if not argv:
        return None
    legacy_name = str(spec.get("legacy_name") or "")
    legacy = (
        protocol_tool_by_name(protocols, legacy_name)
        or protocol_tool_by_name(protocols, role)
        or protocol_tool_by_kind(protocols, str(spec.get("kind") or ""))
    )
    legacy_execution = dict(legacy.get("execution") or {}) if isinstance(legacy, dict) else {}
    env = dict(legacy_execution.get("env") or {})
    env.update({str(k): str(v) for k, v in dict(spec.get("env") or {}).items() if v is not None and v != ""})
    execution = {
        "argv": argv,
        "cwd": str(Path.cwd()),
        "env": env,
        "timeout_sec": legacy_execution.get("timeout_sec"),
    }
    return {
        "name": str(spec.get("name")),
        "kind": str(spec.get("kind")),
        "scope": str(spec.get("scope") or "local"),
        "command": " ".join(argv),
        "execution": execution,
        "script_exists": script_exists(argv),
        "required": bool(spec.get("required", False)),
        "required_group": spec.get("required_group"),
        "consumes": list(spec.get("consumes") or []),
        "produces": list(spec.get("produces") or []),
        "adapter_role": role,
        "legacy_name": legacy_name,
    }


def rewrite_board_profile_arg(tool: dict[str, Any], resolved_board_profile_path: Path | None) -> dict[str, Any]:
    if not resolved_board_profile_path:
        return tool
    execution = tool.get("execution") if isinstance(tool.get("execution"), dict) else {}
    argv = list(execution.get("argv") or [])
    if "--board-profile" not in argv:
        return tool
    index = argv.index("--board-profile")
    if index + 1 >= len(argv):
        return tool
    argv[index + 1] = str(resolved_board_profile_path)
    updated = dict(tool)
    updated_execution = dict(execution)
    updated_execution["argv"] = argv
    updated["execution"] = updated_execution
    updated["command"] = " ".join(str(item) for item in argv)
    consumes = list(updated.get("consumes") or [])
    if str(resolved_board_profile_path) not in consumes:
        consumes.append(str(resolved_board_profile_path))
    updated["consumes"] = consumes
    return updated


def rewrite_board_wrapper_arg(tool: dict[str, Any], board_wrapper_path: Path | None) -> dict[str, Any]:
    if not board_wrapper_path:
        return tool
    execution = tool.get("execution") if isinstance(tool.get("execution"), dict) else {}
    argv = list(execution.get("argv") or [])
    if "--board-wrapper" not in argv:
        return tool
    index = argv.index("--board-wrapper")
    if index + 1 >= len(argv):
        return tool
    argv[index + 1] = str(board_wrapper_path)
    updated = dict(tool)
    updated_execution = dict(execution)
    updated_execution["argv"] = argv
    updated["execution"] = updated_execution
    updated["command"] = " ".join(str(item) for item in argv)
    consumes = list(updated.get("consumes") or [])
    if str(board_wrapper_path) not in consumes:
        consumes.append(str(board_wrapper_path))
    updated["consumes"] = consumes
    return updated


def board_shell_contract_path(run_dir: Path) -> Path:
    return run_dir / "generated" / "backend" / "constraints" / "board_shell_contract.json"


def board_shell_wrapper_rtl_path(run_dir: Path) -> Path:
    return run_dir / "generated" / "backend" / "rtl" / "SpatialAccBoardShellRuntimeTop.sv"


def board_shell_wrapper_manifest_path(run_dir: Path) -> Path:
    return run_dir / "generated" / "backend" / "reports" / "board_shell_wrapper_manifest.json"


def compute_slot_adapter_rtl_path(run_dir: Path) -> Path:
    contract = read_json_if_exists(app_shell_integration_contract_path(run_dir))
    target = contract.get("integration_target", {}) if isinstance(contract.get("integration_target"), dict) else {}
    abi = contract.get("compute_slot_abi", {}) if isinstance(contract.get("compute_slot_abi"), dict) else {}
    module = first_nonblank(
        target.get("replacement_module_identity"),
        target.get("ip_name"),
        abi.get("replacement_module_identity"),
        abi.get("slot_module"),
        "compute_slot_adapter",
    )
    return run_dir / "generated" / "backend" / "rtl" / f"{module}.v"


def compute_slot_adapter_manifest_path(run_dir: Path) -> Path:
    return run_dir / "generated" / "backend" / "reports" / "compute_slot_adapter_manifest.json"


def app_shell_integration_contract_path(run_dir: Path) -> Path:
    return run_dir / "generated" / "backend" / "constraints" / "app_shell_integration_contract.json"


def board_source_identity_path(run_dir: Path) -> Path:
    return run_dir / "verification" / "board_interface" / "board_source_identity.json"


def dut_weight_binding_requirements_path(run_dir: Path) -> Path:
    return run_dir / "verification" / "semantic_testbench" / "dut_weight_binding_requirements.json"


def semantic_testbench_manifest_path(run_dir: Path) -> Path:
    return run_dir / "verification" / "semantic_testbench" / "semantic_testbench_manifest.json"


def current_app_shell_binding_artifacts(run_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Read the current-run physical slot and loader contracts.

    These are generated verification artifacts, not a board/model default.  Keeping
    this lookup in the backend stage makes every later app-shell step consume the
    same source of truth and prevents an old discovery result from becoming the
    integration target by accident.
    """
    identity = read_json_if_exists(board_source_identity_path(run_dir))
    requirements = read_json_if_exists(dut_weight_binding_requirements_path(run_dir))
    manifest = read_json_if_exists(semantic_testbench_manifest_path(run_dir))
    if isinstance(manifest.get("single_layer"), dict):
        harness = manifest["single_layer"].get("dut_harness", {})
        if isinstance(harness, dict) and isinstance(harness.get("loader_route_contract"), dict):
            requirements = dict(requirements)
            requirements["loader_route_contract"] = harness["loader_route_contract"]
    return identity, requirements


def backend_recovery_approval_path(run_dir: Path) -> Path | None:
    value = os.environ.get("SPATIALACC_BACKEND_APPROVAL_ARTIFACT", "").strip()
    path = Path(value) if value else run_dir / "backend_board" / "recovery" / "approval.json"
    return path if path.is_file() else None


def protocol_env_for_vivado(protocols: list[dict[str, Any]]) -> dict[str, str]:
    for name in ["vivado_implementation", "vivado_synthesis"]:
        tool = protocol_tool_by_name(protocols, name)
        execution = tool.get("execution") if isinstance(tool, dict) and isinstance(tool.get("execution"), dict) else {}
        env = execution.get("env") if isinstance(execution.get("env"), dict) else {}
        if env:
            return {str(k): str(v) for k, v in env.items() if v is not None and v != ""}
    return {}


def builtin_backend_tool(role: str, run_dir: Path, protocols: list[dict[str, Any]]) -> dict[str, Any] | None:
    contract = board_shell_contract_path(run_dir)
    app_shell_contract = app_shell_integration_contract_path(run_dir)
    wrapper_rtl = board_shell_wrapper_rtl_path(run_dir)
    adapter_rtl = compute_slot_adapter_rtl_path(run_dir)
    adapter_manifest = compute_slot_adapter_manifest_path(run_dir)
    if role == "compute_slot_adapter_generate":
        script = Path("scripts/synthesis/compute_slot_adapter_generator.py")
        generated_top = run_dir / "generated" / "chisel" / "vivado" / "GeneratedAxiDdrTop.sv"
        current_contract = read_json_if_exists(app_shell_contract)
        target = current_contract.get("integration_target", {}) if isinstance(current_contract.get("integration_target"), dict) else {}
        abi = current_contract.get("compute_slot_abi", {}) if isinstance(current_contract.get("compute_slot_abi"), dict) else {}
        module = first_nonblank(
            target.get("replacement_module_identity"),
            target.get("ip_name"),
            abi.get("replacement_module_identity"),
            abi.get("slot_module"),
            "compute_slot_adapter",
        )
        legacy = run_dir / "generated" / "board_integration" / f"{module}.v"
        argv = [
            "python3",
            str(script),
            "--contract",
            str(app_shell_contract),
            "--legacy-adapter",
            str(legacy),
            "--generated-top",
            str(generated_top),
            "--output",
            str(adapter_rtl),
            "--manifest",
            str(adapter_manifest),
        ]
        return {
            "name": "case_compute_slot_adapter_generate",
            "kind": "compute_slot_adapter_generate",
            "scope": "local",
            "command": " ".join(argv),
            "execution": {"argv": argv, "cwd": str(Path.cwd()), "env": {}, "timeout_sec": None},
            "script_exists": script.exists(),
            "required": True,
            "required_group": None,
            "consumes": [str(app_shell_contract), str(legacy), str(generated_top)],
            "produces": [str(adapter_rtl), str(adapter_manifest)],
            "adapter_role": role,
            "legacy_name": None,
        }
    if role == "stage7_metrics":
        script = Path("scripts/synthesis/case_stage7_metrics.py")
        report = run_dir / "backend_board" / "qor" / "qor_metrics.json"
        argv = ["python3", str(script), "--run-dir", str(run_dir), "--out", str(report)]
        return {
            "name": "case_stage7_metrics",
            "kind": "stage7_metrics",
            "scope": "local",
            "command": " ".join(argv),
            "execution": {"argv": argv, "cwd": str(Path.cwd()), "env": {}, "timeout_sec": None},
            "script_exists": script.exists(),
            "required": True,
            "required_group": None,
            "consumes": [
                str(run_dir / "app_shell_runtime_bitstream" / "app_shell_impl_utilization.rpt"),
                str(run_dir / "app_shell_runtime_bitstream" / "app_shell_impl_timing.rpt"),
                str(run_dir / "app_shell_runtime_bitstream" / "app_shell_impl_power.rpt"),
                str(run_dir / "verification" / "board_simulation" / "reports" / "performance_counter_report.json"),
            ],
            "produces": [str(report)],
            "adapter_role": role,
            "legacy_name": None,
        }
    if role == "board_shell_wrapper_generate":
        script = Path("scripts/synthesis/board_shell_wrapper_generator.py")
        generated_top = run_dir / "generated" / "chisel" / "GeneratedAxiDdrTop.sv"
        wrapper_manifest = board_shell_wrapper_manifest_path(run_dir)
        argv = [
            "python3",
            str(script),
            "--contract",
            str(contract),
            "--generated-top",
            str(generated_top),
            "--out-rtl",
            str(wrapper_rtl),
            "--out",
            str(wrapper_manifest),
        ]
        return {
            "name": "case_board_shell_wrapper_generate",
            "kind": "board_shell_wrapper_generate",
            "scope": "local",
            "command": " ".join(argv),
            "execution": {"argv": argv, "cwd": str(Path.cwd()), "env": {}, "timeout_sec": None},
            "script_exists": script.exists(),
            "required": True,
            "required_group": None,
            "consumes": [str(contract), str(generated_top)],
            "produces": [str(wrapper_rtl), str(wrapper_manifest)],
            "adapter_role": role,
            "legacy_name": None,
        }
    if role == "app_shell_runtime_bitstream":
        script = Path("scripts/synthesis/app_shell_runtime_vivado.py")
        report = run_dir / "backend_board" / "case_diagnostics" / "app_shell_runtime_vivado.json"
        generated_vivado_dir = run_dir / "generated" / "chisel" / "vivado"
        ip_module_manifest = run_dir / "generated" / "chisel" / "simulation" / "fpga_ip_modules.txt"
        ip_generation_tcl = run_dir / "generated" / "chisel" / "scripts" / "gen_xilinx_fp_ips_23.tcl"
        ip_closure = read_json_if_exists(run_dir / "generated" / "chisel" / "simulation" / "fpga_ip_simulation_closure.json")
        fpga_part = str(first_nonblank(ip_closure.get("fpga_part"), ""))
        parameter_binding = read_json_if_exists(run_dir / "parameter_binding" / "parameter_binding.json")
        global_params = parameter_binding.get("global_params", {}) if isinstance(parameter_binding.get("global_params"), dict) else {}
        clock_target_mhz = first_nonblank(
            global_params.get("clock_target_mhz"),
            os.environ.get("SPATIALACC_CLOCK_TARGET_MHZ"),
        )
        argv = [
            "python3",
            str(script),
            "--run-dir",
            str(run_dir),
            "--contract",
            str(app_shell_contract),
            "--wrapper-rtl",
            str(adapter_rtl if adapter_rtl.is_file() else wrapper_rtl),
            "--generated-vivado-dir",
            str(generated_vivado_dir),
            "--ip-module-manifest",
            str(ip_module_manifest),
            "--ip-generation-tcl",
            str(ip_generation_tcl),
            "--fpga-part",
            fpga_part,
            "--clock-target-mhz",
            str(clock_target_mhz or ""),
            "--mode",
            os.environ.get("SPATIALACC_APP_SHELL_MODE", "bitstream"),
            "--out",
            str(report),
        ]
        return {
            "name": "app_shell_runtime_bitstream",
            "kind": "app_shell_runtime_bitstream",
            "scope": "remote",
            "command": " ".join(argv),
            "execution": {"argv": argv, "cwd": str(Path.cwd()), "env": protocol_env_for_vivado(protocols), "timeout_sec": None},
            "script_exists": script.exists(),
            "required": True,
            "required_group": None,
            "consumes": [
                str(app_shell_contract),
                str(adapter_rtl if adapter_rtl.is_file() else wrapper_rtl),
                str(generated_vivado_dir),
                str(ip_module_manifest),
                str(ip_generation_tcl),
            ],
            "produces": [str(run_dir / "app_shell_runtime_bitstream"), str(report)],
            "adapter_role": role,
            "legacy_name": None,
        }
    if role in {"app_shell_target_discovery_contract", "app_shell_target_discovery_after_hint"}:
        script = Path("scripts/synthesis/app_shell_target_discovery.py")
        report_name = "app_shell_target_discovery_after_hint.json" if role == "app_shell_target_discovery_after_hint" else "app_shell_target_discovery.json"
        report = run_dir / "backend_board" / "case_diagnostics" / report_name
        app_shell_report = run_dir / "backend_board" / "case_diagnostics" / "app_shell_runtime_vivado.json"
        argv = [
            "python3",
            str(script),
            "--run-dir",
            str(run_dir),
            "--contract",
            str(app_shell_contract),
            "--app-shell-report",
            str(app_shell_report),
            "--out-contract",
            str(app_shell_contract),
            "--out",
            str(report),
        ]
        return {
            "name": role,
            "kind": "app_shell_target_discovery_contract",
            "scope": "remote",
            "command": " ".join(argv),
            "execution": {"argv": argv, "cwd": str(Path.cwd()), "env": protocol_env_for_vivado(protocols), "timeout_sec": None},
            "script_exists": script.exists(),
            "required": True,
            "required_group": None,
            "consumes": [str(app_shell_contract), str(app_shell_report)],
            "produces": [str(app_shell_contract), str(report)],
            "adapter_role": role,
            "legacy_name": None,
        }
    if role == "app_shell_target_hint_synthesis":
        script = Path("scripts/synthesis/app_shell_target_hint_synthesis.py")
        report = run_dir / "backend_board" / "case_diagnostics" / "app_shell_target_hint_synthesis.json"
        discovery_report = run_dir / "backend_board" / "case_diagnostics" / "app_shell_target_discovery.json"
        app_shell_report = run_dir / "backend_board" / "case_diagnostics" / "app_shell_runtime_vivado.json"
        decision = run_dir / "generated" / "backend" / "reports" / "app_shell_target_selection_decision.json"
        argv = [
            "python3",
            str(script),
            "--run-dir",
            str(run_dir),
            "--contract",
            str(app_shell_contract),
            "--target-discovery-report",
            str(discovery_report),
            "--app-shell-report",
            str(app_shell_report),
            "--out-contract",
            str(app_shell_contract),
            "--out-decision",
            str(decision),
            "--out",
            str(report),
        ]
        return {
            "name": "app_shell_target_hint_synthesis",
            "kind": "app_shell_target_hint_synthesis",
            "scope": "llm",
            "command": " ".join(argv),
            "execution": {"argv": argv, "cwd": str(Path.cwd()), "env": {}, "timeout_sec": None},
            "script_exists": script.exists(),
            "required": True,
            "required_group": None,
            "consumes": [
                str(app_shell_contract),
                str(discovery_report),
                str(app_shell_report),
                str(run_dir / "input" / "field_evidence.json"),
                str(run_dir / "input" / "target_board_profile.json"),
                str(run_dir / "input" / "material_index_board.json"),
            ],
            "produces": [str(app_shell_contract), str(decision), str(report)],
            "adapter_role": role,
            "legacy_name": None,
        }
    if role == "backend_recovery_approval_ingest":
        approval = backend_recovery_approval_path(run_dir)
        if approval is None:
            return None
        script = Path("scripts/synthesis/backend_recovery_approval_ingest.py")
        request = run_dir / "backend_board" / "recovery" / "request_exact_app_shell_target_approval.json"
        report = run_dir / "backend_board" / "case_diagnostics" / "backend_recovery_approval_ingest.json"
        argv = [
            "python3",
            str(script),
            "--request",
            str(request),
            "--approval",
            str(approval),
            "--contract",
            str(app_shell_contract),
            "--out-contract",
            str(app_shell_contract),
            "--out",
            str(report),
        ]
        return {
            "name": "backend_recovery_approval_ingest",
            "kind": "backend_recovery_approval_ingest",
            "scope": "llm",
            "command": " ".join(argv),
            "execution": {"argv": argv, "cwd": str(Path.cwd()), "env": {}, "timeout_sec": None},
            "script_exists": script.exists(),
            "required": True,
            "required_group": None,
            "consumes": [str(request), str(approval), str(app_shell_contract)],
            "produces": [str(app_shell_contract), str(report)],
            "adapter_role": role,
            "legacy_name": None,
        }
    if role == "runtime_bitstream":
        script = Path("scripts/synthesis/runtime_board_shell_vivado.py")
        report = run_dir / "backend_board" / "case_diagnostics" / "runtime_board_shell_vivado.json"
        argv = [
            "python3",
            str(script),
            "--run-dir",
            str(run_dir),
            "--contract",
            str(contract),
            "--wrapper-rtl",
            str(wrapper_rtl),
            "--mode",
            "bitstream",
            "--clock-period-ns",
            os.environ.get("SPATIALACC_RUNTIME_CLOCK_PERIOD_NS", "20.000"),
            "--out",
            str(report),
        ]
        return {
            "name": "case_runtime_bitstream",
            "kind": "runtime_board_shell_vivado",
            "scope": "remote",
            "command": " ".join(argv),
            "execution": {"argv": argv, "cwd": str(Path.cwd()), "env": protocol_env_for_vivado(protocols), "timeout_sec": None},
            "script_exists": script.exists(),
            "required": True,
            "required_group": None,
            "consumes": [str(contract), str(wrapper_rtl), str(run_dir / "generated" / "chisel")],
            "produces": [str(run_dir / "runtime_board_shell_bitstream" / "runtime_board_shell.bit"), str(report)],
            "adapter_role": role,
            "legacy_name": None,
        }
    return None


def backend_tools_for_scope(
    state: dict[str, Any],
    run_dir: Path,
    scope: str,
    resolved_board_profile_path: Path | None,
    board_wrapper_path: Path | None,
) -> tuple[list[dict[str, Any]], list[str]]:
    tool_protocols = read_json(artifact_path(state, "artifact.input.tool_protocols"))
    protocols = tool_protocols.get("tools", []) if isinstance(tool_protocols.get("tools"), list) else []
    case_adapter = case_adapter_for_state(state, run_dir)
    tools: list[dict[str, Any]] = []
    blockers: list[str] = []
    roles = roles_for_scope(scope)
    if backend_recovery_approval_path(run_dir) is not None and "app_shell_target_discovery_after_hint" in roles:
        index = roles.index("app_shell_target_discovery_after_hint")
        roles = [*roles[:index], "backend_recovery_approval_ingest", *roles[index:]]
    for role in roles:
        if role == "board_runtime" and not board_runtime_enabled():
            blockers.append("board runtime tool execution is disabled; set SPATIALACC_RUN_BOARD_TOOLS=1 when a configured board is available")
            continue
        if role in {
            "board_shell_wrapper_generate",
            "compute_slot_adapter_generate",
            "stage7_metrics",
            "runtime_bitstream",
            "app_shell_target_discovery_contract",
            "app_shell_target_hint_synthesis",
            "backend_recovery_approval_ingest",
            "app_shell_target_discovery_after_hint",
            "app_shell_runtime_bitstream",
        }:
            builtin = builtin_backend_tool(role, run_dir, protocols)
            if builtin:
                tools.append(builtin)
                continue
        spec = adapter_tool(case_adapter, role)
        if spec:
            materialized = materialize_case_tool(spec, protocols, role)
            if materialized:
                updated = rewrite_board_profile_arg(materialized, resolved_board_profile_path)
                updated = rewrite_board_wrapper_arg(updated, board_wrapper_path)
                tools.append(updated)
                continue
        protocol = protocol_tool_by_name(protocols, role)
        if protocol:
            updated = rewrite_board_profile_arg(protocol, resolved_board_profile_path)
            updated = rewrite_board_wrapper_arg(updated, board_wrapper_path)
            tools.append(updated)
            continue
        builtin = builtin_backend_tool(role, run_dir, protocols)
        if builtin:
            tools.append(builtin)
            continue
        blockers.append(f"backend tool role is not configured: {role}")
    return tools, blockers


def backend_tool_report_digest(path_value: Any) -> dict[str, Any]:
    path_text = str(path_value or "")
    if not path_text:
        return {}
    path = Path(path_text)
    if not path.is_file():
        return {"path": path_text, "status": "missing"}
    try:
        report = read_json(path)
    except Exception as exc:
        return {"path": path_text, "status": "unreadable", "error": str(exc)}
    checks = []
    for item in report.get("checks", []) if isinstance(report.get("checks"), list) else []:
        if not isinstance(item, dict):
            continue
        checks.append(
            {
                "name": item.get("name"),
                "status": item.get("status"),
                "summary": str(item.get("summary") or "")[:260],
            }
        )
    digest = {
        "path": path_text,
        "status": report.get("status"),
        "summary": report.get("summary"),
        "blockers": [str(value)[:420] for value in report.get("blockers", [])[:8]]
        if isinstance(report.get("blockers"), list)
        else [],
        "checks": checks[:16],
    }
    candidate_discovery = report.get("candidate_discovery")
    if isinstance(candidate_discovery, dict):
        digest["candidate_discovery"] = {
            "total_intf_pins": candidate_discovery.get("total_intf_pins"),
            "total_axi_intf_pins": candidate_discovery.get("total_axi_intf_pins"),
            "intf_pin_samples": candidate_discovery.get("intf_pin_samples", [])[:12]
            if isinstance(candidate_discovery.get("intf_pin_samples"), list)
            else [],
            "axi_intf_pin_samples": candidate_discovery.get("axi_intf_pin_samples", [])[:12]
            if isinstance(candidate_discovery.get("axi_intf_pin_samples"), list)
            else [],
            "cell_samples": candidate_discovery.get("cell_samples", [])[:12]
            if isinstance(candidate_discovery.get("cell_samples"), list)
            else [],
            "axi_candidate_cell_samples": candidate_discovery.get("axi_candidate_cell_samples", [])[:12]
            if isinstance(candidate_discovery.get("axi_candidate_cell_samples"), list)
            else [],
        }
    for key in [
        "target_discovery_policy",
        "target_selection_decision",
        "decision",
        "recovery_status",
        "selection_reason",
        "selected_target",
        "target_candidates",
        "allowed_options",
        "normalized_approval",
        "bounded_recovery_actions",
        "updated_contract",
        "resources",
        "power_w",
        "clock_frequency_mhz",
        "performance_tokens_per_second",
    ]:
        value = report.get(key)
        if isinstance(value, list):
            digest[key] = value[:12]
        elif isinstance(value, dict):
            digest[key] = value
        elif value is not None:
            digest[key] = value
    return digest


def _qor_number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None


def exact_app_shell_qor_evidence_paths(run_dir: Path) -> list[Path]:
    """Return the sole evidence set accepted by the formal DSE campaign."""

    return [
        run_dir / "backend_board" / "case_diagnostics" / "app_shell_runtime_vivado.json",
        run_dir / "app_shell_runtime_bitstream" / "app_shell_impl_utilization.rpt",
        run_dir / "app_shell_runtime_bitstream" / "app_shell_impl_timing.rpt",
        run_dir / "app_shell_runtime_bitstream" / "app_shell_impl_power.rpt",
        run_dir / "verification" / "board_simulation" / "reports" / "performance_counter_report.json",
        run_dir / "backend_board" / "qor" / "qor_metrics.json",
    ]


def selected_dse_parameters(state: dict[str, Any]) -> tuple[dict[str, Any], str]:
    """Read the current Stage 4 candidate without reconstructing it from reports."""

    try:
        binding_path = artifact_path(state, "artifact.stage4.parameter_binding")
        binding = read_json(binding_path)
    except Exception:
        return {}, ""
    selected = binding.get("selected_architecture", {}) if isinstance(binding.get("selected_architecture"), dict) else {}
    parameters = selected.get("parameters", {}) if isinstance(selected.get("parameters"), dict) else {}
    return parameters, str(binding_path)


def app_shell_implementation_failure(report: dict[str, Any]) -> bool:
    """Accept only an explicit real Vivado implementation failure as infeasible.

    Transport, source-copy, missing-file, or remote-environment failures are not
    design-space outcomes and must not remove a candidate from the campaign.
    """

    if str(report.get("mode") or "") != "bitstream" or str(report.get("status") or "") != "fail":
        return False
    inspection = report.get("inspection", {}) if isinstance(report.get("inspection"), dict) else {}
    implementation_status = str(inspection.get("top_impl_status") or "").strip()
    if not implementation_status:
        return False
    return "complete" not in implementation_status.lower()


def record_exact_dse_measurement(state: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    """Persist one exact app-shell DSE outcome when its evidence is complete."""

    parameters, binding_path = selected_dse_parameters(state)
    if not parameters:
        return {"status": "not_recorded", "reason": "current Stage4 selected architecture is unavailable"}

    report_path, *evidence_paths = exact_app_shell_qor_evidence_paths(run_dir)
    expected_paths = [str(path.resolve()) for path in [report_path, *evidence_paths]]
    app_shell_report = read_json_if_exists(report_path)
    if str(app_shell_report.get("mode") or "") != "bitstream":
        return {"status": "not_recorded", "reason": "current app-shell implementation report is unavailable"}

    if app_shell_implementation_failure(app_shell_report):
        measurement_status = "infeasible"
        metrics: dict[str, Any] | None = None
        reason = str(app_shell_report.get("summary") or "real app-shell implementation failed")
        paths = [str(report_path.resolve())]
    elif str(app_shell_report.get("status") or "") == "pass":
        metric_report = read_json_if_exists(evidence_paths[-1])
        if metric_report.get("measurement_scope") != EXACT_TARGET_BOARD_APP_SHELL_SCOPE:
            return {
                "status": "not_recorded",
                "reason": "QoR report is not explicitly scoped to the exact target-board app-shell flow",
            }
        metric_evidence_paths = metric_report.get("evidence_paths")
        if metric_evidence_paths != expected_paths:
            return {
                "status": "not_recorded",
                "reason": "QoR report evidence paths do not match the current exact app-shell report set",
            }
        metrics = {key: metric_report.get(key) for key in QOR_KEYS}
        if not complete_metrics(metrics):
            return {
                "status": "not_recorded",
                "reason": "exact app-shell implementation completed but the four-metric measurement is incomplete",
            }
        if not all(path.is_file() and path.stat().st_size > 0 for path in evidence_paths):
            return {
                "status": "not_recorded",
                "reason": "exact app-shell report set is incomplete",
            }
        measurement_status = "measured"
        reason = "exact target-board app-shell Vivado and hardware-counter QoR measurement"
        paths = expected_paths
    else:
        return {
            "status": "not_recorded",
            "reason": "app-shell execution did not prove either implementation completion or implementation infeasibility",
        }

    latest = load_latest(ledger_path(run_dir)).get(candidate_fingerprint(parameters))
    if (
        latest
        and latest.get("measurement_status") == measurement_status
        and latest.get("metrics") == metrics
        and latest.get("evidence_paths") == paths
    ):
        return {
            "status": "reused",
            "measurement_status": measurement_status,
            "candidate_id": latest.get("candidate_id"),
            "reason": "the current exact evidence is already recorded for this candidate",
        }

    row = append_measurement(
        ledger_path(run_dir),
        parameters=parameters,
        measurement_status=measurement_status,
        measurement_scope=EXACT_TARGET_BOARD_APP_SHELL_SCOPE,
        metrics=metrics,
        evidence_paths=paths,
        binding_path=binding_path,
        reason=reason,
    )
    return {
        "status": "recorded",
        "measurement_status": measurement_status,
        "candidate_id": row["candidate_id"],
        "reason": reason,
        "evidence_paths": paths,
    }


def exact_dse_campaign(state: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    """Re-evaluate campaign completion from the current ledger and candidate space."""

    try:
        from accagent.framework.stage_params import build_dse_search

        search = build_dse_search(state, run_dir)
    except Exception as exc:
        return {"status": "unavailable", "reason": str(exc)}
    summary = search.get("measurement_summary", {}) if isinstance(search.get("measurement_summary"), dict) else {}
    return {
        "status": search.get("status"),
        "measurement_summary": summary,
        "unmeasured_candidate_ids": list(search.get("unmeasured_candidate_ids", [])),
        "pareto_candidate_ids": list(search.get("pareto_candidate_ids", [])),
    }


def classify_qor_optimization(
    state: dict[str, Any],
    metrics: dict[str, Any],
    campaign: dict[str, Any] | None = None,
    measurement: dict[str, Any] | None = None,
    llm_decision: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Route only measured four-metric QoR misses.

    The framework computes exact metric misses but does not classify their
    repair scope.  Once a measured miss exists, the LLM must select either a
    local RTL/implementation repair or a formal Stage4 DSE backtrack.
    """

    campaign = campaign or {}
    measurement = measurement or {}
    unmeasured = [str(value) for value in campaign.get("unmeasured_candidate_ids", []) if str(value)]
    if measurement.get("measurement_status") == "infeasible" and unmeasured:
        return {
            "status": "campaign_pending",
            "decision": "dse_backtrack",
            "reason": "the current candidate is implementation-infeasible; exact DSE has remaining legal candidates",
            "next_stage": "stage4.parameter_binding",
            "campaign": campaign,
        }

    resources = metrics.get("resources") if isinstance(metrics.get("resources"), dict) else None
    power = _qor_number(metrics.get("power_w"))
    clock = _qor_number(metrics.get("clock_frequency_mhz"))
    performance = _qor_number(metrics.get("performance_tokens_per_second"))
    if not resources or power is None or clock is None or performance is None:
        return {
            "status": "unavailable",
            "decision": "continue_backend",
            "reason": "all four measured QoR metrics are required before optimization routing",
            "metrics": metrics,
            "campaign": campaign,
        }

    if unmeasured:
        return {
            "status": "campaign_pending",
            "decision": "dse_backtrack",
            "reason": "exact DSE campaign has remaining legal candidates that require real app-shell measurement",
            "metrics": metrics,
            "next_stage": "stage4.parameter_binding",
            "campaign": campaign,
        }

    try:
        design_space = constraint_facts(state, "constraint.arch.design_space")
    except (KeyError, ValueError):
        design_space = {}
    try:
        binding = read_json(artifact_path(state, "artifact.stage4.parameter_binding"))
    except (KeyError, OSError, ValueError):
        binding = {}
    board = constraint_facts(state, "constraint.deployment.board").get("board", {})
    board_budget = board.get("resource_budget", {}) if isinstance(board, dict) else {}
    targets = design_space.get("qor_targets", {}) if isinstance(design_space.get("qor_targets"), dict) else {}
    global_params = binding.get("global_params", {}) if isinstance(binding.get("global_params"), dict) else {}
    requested_clock = _qor_number(targets.get("clock_frequency_mhz")) or _qor_number(global_params.get("clock_target_mhz"))
    requested_performance = _qor_number(targets.get("performance_tokens_per_second"))
    requested_power = _qor_number(targets.get("power_w"))

    ratios: list[tuple[str, float]] = []
    for name in ["lut", "ff", "uram", "dsp", "bram36", "bram18"]:
        limit = _qor_number(board_budget.get(name))
        actual = _qor_number(resources.get(name))
        if limit and actual is not None:
            ratios.append((f"resources.{name}", actual / limit))
    bram_limit = _qor_number(board_budget.get("bram"))
    if bram_limit and not (_qor_number(board_budget.get("bram36")) or _qor_number(board_budget.get("bram18"))):
        bram_actual = (_qor_number(resources.get("bram36")) or 0.0) + (_qor_number(resources.get("bram18")) or 0.0)
        ratios.append(("resources.bram", bram_actual / bram_limit))
    if requested_power:
        ratios.append(("power_w", power / requested_power))
    if requested_clock:
        ratios.append(("clock_frequency_mhz", requested_clock / clock))
    if requested_performance:
        ratios.append(("performance_tokens_per_second", requested_performance / performance))

    performance_comparison = str(targets.get("performance_comparison") or ">=").strip()
    misses = [{"metric": name, "ratio": ratio} for name, ratio in ratios if ratio > 1.0]
    if (
        requested_performance is not None
        and performance_comparison == ">"
        and performance <= requested_performance
        and not any(item["metric"] == "performance_tokens_per_second" for item in misses)
    ):
        misses.append(
            {
                "metric": "performance_tokens_per_second",
                "ratio": requested_performance / performance if performance else float("inf"),
                "comparison": ">",
            }
        )
    if not misses:
        return {
            "status": "pass",
            "decision": "pass",
            "reason": "measured QoR meets every supplied four-metric target",
            "metrics": metrics,
            "targets_checked": [name for name, _ in ratios],
            "campaign": campaign,
        }
    requested_decision = str((llm_decision or {}).get("qor_decision") or "").strip()
    if requested_decision not in {"local_optimization", "dse_backtrack"}:
        return {
            "status": "needs_optimization",
            "decision": "llm_required",
            "reason": "measured QoR misses require an LLM decision between local hardware repair and Stage4 DSE backtrack",
            "metrics": metrics,
            "misses": misses,
            "next_stage": None,
            "preserve_existing_hardware": True,
            "campaign": campaign,
        }
    decision = requested_decision
    return {
        "status": "needs_optimization",
        "decision": decision,
        "reason": str((llm_decision or {}).get("decision_rationale") or (
            "LLM selected a local hardware optimization" if decision == "local_optimization"
            else "LLM selected a formal Stage4 DSE backtrack"
        )),
        "metrics": metrics,
        "misses": misses,
        "next_stage": "stage5.code_generation" if decision == "local_optimization" else "stage4.parameter_binding",
        # Both routes are incremental: a local fix adjusts only the existing
        # RTL/implementation; DSE adjusts its existing parameter binding and
        # regenerates from that design rather than discarding the hardware.
        "preserve_existing_hardware": True,
        "campaign": campaign,
    }


def normalize_tool_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for item in results:
        status = str(item.get("status") or "not_run")
        if status == "pass":
            failure_class = "passed_real_tool"
        elif status == "fail":
            failure_class = "required_backend_tool_failure" if item.get("required") else "backend_tool_failure"
        elif item.get("required"):
            failure_class = "pending_required_backend_tool"
        else:
            failure_class = "not_executed"
        normalized.append(
            {
                "checker": f"real_tool.{item.get('name')}",
                "status": status,
                "summary": item.get("summary", ""),
                "failure_class": failure_class,
                "required": bool(item.get("required", False)),
                "kind": item.get("kind"),
                "command": item.get("command"),
                "log_path": item.get("log_path"),
                "tool_report_path": item.get("tool_report_path"),
                "tool_report_status": item.get("tool_report_status"),
                "tool_report_summary": item.get("tool_report_summary"),
                "tool_report_blockers": item.get("tool_report_blockers", []),
                "tool_report_digest": backend_tool_report_digest(item.get("tool_report_path")),
            }
        )
    return normalized


def existing_real_tool_evidence(state: dict[str, Any]) -> list[dict[str, Any]]:
    latest_by_checker: dict[str, dict[str, Any]] = {}
    for item in state.get("evidence", []):
        checker = str(item.get("checker") or "")
        if not checker.startswith("real_tool."):
            continue
        if any(
            token in checker
            for token in [
                "app_shell_runtime_bitstream",
                "app_shell_target_discovery_contract",
                "app_shell_target_hint_synthesis",
                "app_shell_target_discovery_after_hint",
                "backend_recovery_approval_ingest",
                "runtime_abi",
                "stage7_metrics",
            ]
        ):
            latest_by_checker[checker] = item
    return [
        {
            "checker": checker,
            "status": item.get("status", "unknown"),
            "summary": item.get("summary", ""),
            "failure_class": "carried_forward_real_tool_evidence",
            "required": True,
            "kind": None,
            "command": None,
            "log_path": item.get("log_path"),
        }
        for checker, item in sorted(latest_by_checker.items())
    ]


def artifact_producer_transition(state: dict[str, Any], artifact_id: str) -> dict[str, Any] | None:
    producer = None
    for artifact in state.get("artifacts", []):
        if artifact.get("id") == artifact_id:
            producer = artifact.get("producer_transition")
            break
    if not producer:
        return None
    for transition in state.get("transitions", []):
        if transition.get("id") == producer:
            return transition
    return None


def check_upstream_hierarchical_verification_closure(state: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    run_dir = run_dir_from_state(Path(str(state.get("_state_path") or ""))) if state.get("_state_path") else None
    if run_dir is None:
        # Stage state normally carries no self-path. The current Stage 7
        # artifact is the only valid source for a run directory; a historical
        # run must never be selected as a hidden backend fallback.
        try:
            run_dir = artifact_path(state, "artifact.stage6.verification_result").parents[1]
        except Exception as exc:
            return {
                "schema_version": "spatialaccagent.stage7_upstream_hierarchy_gate.v1",
                "status": "fail",
                "backend_ready": False,
                "closure_mode": "unresolved_current_run",
                "verification_result": None,
                "stage7_transition_status": "missing",
                "board_bringup_ready": False,
                "board_bringup_readiness": {
                    "status": "fail",
                    "board_bringup_ready": False,
                    "checks": [],
                    "blockers": [
                        "unable to resolve the current run from Stage 6 verification evidence: "
                        f"{exc}"
                    ],
                    "strict_output_diagnostics": {},
                },
                "blockers": [
                    "Stage 6 verification result is required to resolve the current backend run"
                ],
            }

    # Stage 7 only needs the real-board bring-up contract before synthesis and
    # implementation.  Strict output/writeback closure remains diagnostic and
    # is still preserved in the returned evidence when available.
    try:
        from accagent.framework.stage_verification import build_board_bringup_readiness

        board_bringup_readiness = build_board_bringup_readiness(state, run_dir)
    except Exception as exc:
        board_bringup_readiness = {
            "status": "fail",
            "board_bringup_ready": False,
            "checks": [],
            "blockers": [f"unable to evaluate board bring-up readiness: {exc}"],
            "strict_output_diagnostics": {},
        }

    try:
        verification = read_json(artifact_path(state, "artifact.stage6.verification_result"))
        verification_path = str(artifact_path(state, "artifact.stage6.verification_result"))
    except Exception as exc:
        verification = {}
        verification_path = None
        if not board_bringup_readiness.get("board_bringup_ready"):
            blockers.append(f"Stage7 verification result is missing or unreadable: {exc}")
    transition = artifact_producer_transition(state, "artifact.stage6.verification_result")
    transition_status = str((transition or {}).get("status") or "missing")

    if board_bringup_readiness.get("board_bringup_ready") is True:
        return {
            "schema_version": "spatialaccagent.stage7_upstream_hierarchy_gate.v1",
            "status": "pass",
            "backend_ready": True,
            "closure_mode": "board_bringup_to_implementation",
            "verification_result": verification_path,
            "stage7_transition_status": transition_status,
            "board_bringup_ready": True,
            "board_bringup_readiness": board_bringup_readiness,
            "strict_output_diagnostics": board_bringup_readiness.get("strict_output_diagnostics", {}),
            "maturity": verification.get("hierarchical_maturity", {}) if isinstance(verification, dict) else {},
            "debug_closure": verification.get("debug_closure", {}) if isinstance(verification, dict) else {},
            "blockers": [],
            "policy": {
                "stage7_accepts_real_board_bringup_for_vivado": True,
                "stage7_does_not_require_complete_token_output_before_vivado": True,
                "stage7_does_not_require_final_ddr_writeback_before_vivado": True,
                "strict_output_and_writeback_remain_diagnostic": True,
                "stage7_must_not_execute_board_runtime_in_backend_scope": True,
            },
        }

    blockers.extend(
        str(item)
        for item in board_bringup_readiness.get("blockers", [])
        if str(item)
    )
    if transition_status != "promoted":
        blockers.append(f"Stage7 verification transition is {transition_status}, expected promoted")
    if verification.get("status") != "pass":
        blockers.append(f"Stage7 verification status is {verification.get('status')}, expected pass")
    maturity = verification.get("hierarchical_maturity", {}) if isinstance(verification.get("hierarchical_maturity"), dict) else {}
    if not maturity:
        blockers.append("Stage7 verification lacks hierarchical_maturity; rerun Stage7 with strict bottom-up verification contract")
    elif maturity.get("status") != "pass" or maturity.get("backend_ready") is not True:
        blockers.extend(str(item) for item in maturity.get("blockers", [])[:12])
        if not maturity.get("blockers"):
            blockers.append(f"Stage7 hierarchical_maturity is not backend-ready: status={maturity.get('status')} backend_ready={maturity.get('backend_ready')}")
    debug_closure = verification.get("debug_closure", {}) if isinstance(verification.get("debug_closure"), dict) else {}
    if not debug_closure.get("failure_localization"):
        blockers.append("Stage7 debug-closure localization artifact is missing")
    try:
        board_axi_ddr_cert_path = artifact_path(state, "artifact.stage6.board_axi_ddr_promotion_certificate")
        board_axi_ddr_cert = read_json(board_axi_ddr_cert_path)
    except Exception as exc:
        board_axi_ddr_cert_path = None
        board_axi_ddr_cert = {}
        blockers.append(f"Stage7 board AXI/DDR wrapped-system promotion certificate is missing or unreadable: {exc}")
    if board_axi_ddr_cert:
        cert_transition = artifact_producer_transition(state, "artifact.stage6.board_axi_ddr_promotion_certificate")
        cert_transition_status = str((cert_transition or {}).get("status") or "missing")
        if cert_transition_status != "promoted":
            blockers.append(f"Stage7 board AXI/DDR promotion certificate transition is {cert_transition_status}, expected promoted")
        if board_axi_ddr_cert.get("status") != "pass":
            blockers.append(f"Stage7 board AXI/DDR promotion certificate status is {board_axi_ddr_cert.get('status')}, expected pass")
    required_levels = {
        "operator_leaf_functional",
        "single_layer_functional",
        "multilayer_pipeline_functional",
        "axi_ddr_functional",
    }
    passed_levels = {
        str(item.get("id"))
        for item in maturity.get("levels", [])
        if isinstance(item, dict) and item.get("status") == "pass"
    }
    missing_levels = sorted(required_levels - passed_levels)
    if missing_levels:
        blockers.append(f"Stage7 hierarchical maturity missing pass levels before backend: {missing_levels}")
    return {
        "schema_version": "spatialaccagent.stage7_upstream_hierarchy_gate.v1",
        "status": "pass" if not blockers else "fail",
        "backend_ready": not blockers,
        "closure_mode": "strict_hierarchical",
        "verification_result": verification_path,
        "stage7_transition_status": transition_status,
        "board_bringup_ready": False,
        "board_bringup_readiness": board_bringup_readiness,
        "board_axi_ddr_promotion_certificate": str(board_axi_ddr_cert_path) if board_axi_ddr_cert_path else None,
        "maturity": maturity,
        "debug_closure": debug_closure,
        "blockers": blockers,
        "policy": {
            "stage7_must_not_execute_vivado_or_board_tools_before_strict_hierarchical_maturity": True,
            "stage7_requires_board_axi_ddr_wrapped_system_promotion_certificate": True,
            "blocked_stage7_records_sacg_recovery_instead_of_running_backend": True,
            "board_bringup_readiness_is_required_before_vivado": True,
        },
    }


def run_backend_real_tools(
    state: dict[str, Any],
    run_dir: Path,
    out_dir: Path,
    resolved_board_profile_path: Path | None,
    board_wrapper_path: Path | None,
) -> tuple[list[dict[str, Any]], list[str]]:
    scope = backend_execution_scope()
    (out_dir / "real_tools").mkdir(parents=True, exist_ok=True)
    tools, blockers = backend_tools_for_scope(state, run_dir, scope, resolved_board_profile_path, board_wrapper_path)
    results = run_tools(tools, Path.cwd(), out_dir / "real_tools") if tools else []
    return normalize_tool_results(results), blockers


def backend_tool_blockers(tool_results: list[dict[str, Any]], selection_blockers: list[str]) -> list[str]:
    blockers = list(selection_blockers)
    for item in tool_results:
        if item.get("required") and item.get("status") != "pass":
            blockers.append(f"{item['checker'].removeprefix('real_tool.')}={item.get('status')}: {item.get('summary')}")
    return blockers


def scope_passed(scope: str, tool_results: list[dict[str, Any]], selection_blockers: list[str]) -> bool:
    if selection_blockers:
        return False
    required = [item for item in tool_results if item.get("required")]
    if not required:
        return scope in {"none", "plan", "dry_run"}
    return all(item.get("status") == "pass" for item in required)


def backend_llm_record_errors(record: dict[str, Any], prefix: str = "backend_closure_agent") -> list[str]:
    errors: list[str] = []
    if record.get("used_fallback"):
        errors.append(f"{prefix}: used fallback output")
    if record.get("error"):
        errors.append(f"{prefix}: {record.get('error')}")
    output = record.get("output", {}) if isinstance(record.get("output"), dict) else {}
    status = str(output.get("status") or "").strip().lower()
    if status in {"", "fallback", "unavailable"}:
        errors.append(f"{prefix}: output status is {output.get('status')}")
    return errors


def build_backend_agent_gate_status(
    design_team_summary: dict[str, Any],
    llm_record: dict[str, Any],
    recovery_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    team_errors = team_failure_errors(design_team_summary, prefix="backend_board.design_team")
    llm_errors = backend_llm_record_errors(llm_record, prefix="backend_board.backend_closure")
    recovery_report = recovery_report or {}
    recovery_errors = []
    if recovery_report.get("status") != "pass":
        recovery_errors.extend(str(value) for value in recovery_report.get("blockers", []))
        if not recovery_errors:
            recovery_errors.append(f"backend bounded recovery status is {recovery_report.get('status')}")
    checks = [
        {
            "checker": "backend_team_llm_check",
            "status": "pass" if not team_errors else "fail",
            "summary": "backend design team LLM outputs are valid" if not team_errors else "; ".join(team_errors),
        },
        {
            "checker": "backend_closure_llm_check",
            "status": "pass" if not llm_errors else "fail",
            "summary": "backend closure LLM output is valid" if not llm_errors else "; ".join(llm_errors),
        },
        {
            "checker": "backend_bounded_recovery_action_check",
            "status": "pass" if not recovery_errors else "fail",
            "summary": "backend bounded recovery action is valid" if not recovery_errors else "; ".join(recovery_errors),
        },
    ]
    return {
        "schema_version": "spatialaccagent.backend_agent_gate_status.v0",
        "status": "pass" if not team_errors and not llm_errors and not recovery_errors else "fail",
        "checks": checks,
        "errors": [*team_errors, *llm_errors, *recovery_errors],
    }


def backend_llm_decision_packet(plan: dict[str, Any]) -> dict[str, Any]:
    package = plan.get("backend_package", {}) if isinstance(plan.get("backend_package"), dict) else {}
    real = plan.get("real_tool_status", {}) if isinstance(plan.get("real_tool_status"), dict) else {}
    selected = real.get("backend_selected", []) if isinstance(real.get("backend_selected"), list) else []
    app_shell_contract_path = str(package.get("app_shell_integration_contract") or "")
    app_shell_contract = read_json_if_exists(Path(app_shell_contract_path)) if app_shell_contract_path else {}
    return {
        "schema_version": "spatialaccagent.backend_llm_decision_packet.v0",
        "stage": plan.get("stage"),
        "execution_scope": plan.get("execution_scope"),
        "final_design_pass": plan.get("final_design_pass"),
        "final_design_pass_blockers": plan.get("final_design_pass_blockers", [])[:12],
        "missing_final_tools": real.get("missing_final_tools", []),
        "upstream_hierarchy_gate": real.get("upstream_hierarchy_gate", plan.get("upstream_hierarchy_gate", {})),
        "backend_selected_tool_blockers": real.get("backend_selected_tool_blockers", []),
        "selected_real_tools": [
            {
                "checker": item.get("checker"),
                "status": item.get("status"),
                "kind": item.get("kind"),
                "summary": item.get("summary"),
                "tool_report_status": item.get("tool_report_status"),
                "tool_report_summary": item.get("tool_report_summary"),
                "tool_report_blockers": item.get("tool_report_blockers", [])[:8],
                "tool_report_digest": item.get("tool_report_digest", {}),
                "log_path": item.get("log_path"),
                "tool_report_path": item.get("tool_report_path"),
            }
            for item in selected
        ],
        "contracts": {
            "board_shell_contract": package.get("board_shell_contract"),
            "board_shell_wrapper_rtl": package.get("board_shell_wrapper_rtl"),
            "app_shell_integration_contract": package.get("app_shell_integration_contract"),
            "app_shell_integration_contract_summary": {
                "status": app_shell_contract.get("status"),
                "integration_target": app_shell_contract.get("integration_target"),
                "target_discovery_policy": app_shell_contract.get("target_discovery_policy"),
                "target_discovery": {
                    "status": (app_shell_contract.get("target_discovery") or {}).get("status")
                    if isinstance(app_shell_contract.get("target_discovery"), dict)
                    else None,
                    "selection_reason": (app_shell_contract.get("target_discovery") or {}).get("selection_reason")
                    if isinstance(app_shell_contract.get("target_discovery"), dict)
                    else None,
                    "candidate_count": (app_shell_contract.get("target_discovery") or {}).get("candidate_count")
                    if isinstance(app_shell_contract.get("target_discovery"), dict)
                    else None,
                    "top_candidates": (app_shell_contract.get("target_discovery") or {}).get("candidates", [])[:8]
                    if isinstance((app_shell_contract.get("target_discovery") or {}).get("candidates"), list)
                    else [],
                },
            },
        },
        "bounded_recovery_actions": plan.get("bounded_recovery_actions", {}),
        "paper_alignment": "SACG-guided, template-constrained, checker-verified backend/board closure for LLM spatial accelerators.",
    }


def backend_qor_decision_packet(plan: dict[str, Any]) -> dict[str, Any]:
    """Expose only current exact QoR evidence to the QoR routing agent."""

    qor = plan.get("qor", {}) if isinstance(plan.get("qor"), dict) else {}
    optimization = plan.get("qor_optimization", {}) if isinstance(plan.get("qor_optimization"), dict) else {}
    return {
        "schema_version": "spatialaccagent.backend_qor_decision_packet.v0",
        "stage": "backend_board",
        "measurement_scope": EXACT_TARGET_BOARD_APP_SHELL_SCOPE,
        "qor_outputs": ["resources", "power_w", "clock_frequency_mhz", "performance_tokens_per_second"],
        "measured_qor": {
            "resources": qor.get("resources"),
            "power_w": qor.get("power_w"),
            "clock_frequency_mhz": qor.get("clock_frequency_mhz"),
            "performance_tokens_per_second": qor.get("performance_tokens_per_second"),
        },
        "misses": optimization.get("misses", []),
        "targets_checked": optimization.get("targets_checked", []),
        "dse_campaign": {
            "status": (plan.get("dse_campaign") or {}).get("status") if isinstance(plan.get("dse_campaign"), dict) else None,
            "unmeasured_candidate_ids": (plan.get("dse_campaign") or {}).get("unmeasured_candidate_ids", []) if isinstance(plan.get("dse_campaign"), dict) else [],
            "pareto_candidate_ids": (plan.get("dse_campaign") or {}).get("pareto_candidate_ids", []) if isinstance(plan.get("dse_campaign"), dict) else [],
        },
        "routing_policy": {
            "local_optimization": "Use when the current architecture can plausibly satisfy the exact miss by a bounded RTL, pipeline, or implementation repair without changing Stage4 physical parameters.",
            "dse_backtrack": "Use when the exact miss requires changing a legal physical architecture parameter and measuring another candidate through the same app-shell Vivado closure.",
            "pass": "Use only when all supplied hard targets are met.",
            "framework_must_not_choose_by_ratio": True,
        },
    }


def compact_report(path: Path, extra_keys: list[str] | None = None) -> dict[str, Any]:
    if not path.is_file():
        return {"path": str(path), "status": "missing"}
    report = read_json_if_exists(path)
    keys = [
        "schema_version",
        "status",
        "summary",
        "blockers",
        "errors",
        "checks",
        "decision",
        "target_selection_decision",
        "target_discovery_policy",
        "target_discovery",
        "selection_reason",
        "selected_target",
        "target_candidates",
        "runtime_abi",
        "missing_fields",
    ]
    if extra_keys:
        keys.extend(extra_keys)
    compacted = {"path": str(path)}
    for key in keys:
        if key not in report:
            continue
        value = report.get(key)
        if isinstance(value, list):
            compacted[key] = value[:12]
        elif isinstance(value, dict):
            compacted[key] = compact_prompt_for_recovery(value)
        else:
            compacted[key] = value
    return compacted


def compact_prompt_for_recovery(value: Any, depth: int = 0) -> Any:
    if isinstance(value, str):
        return value[:500]
    if isinstance(value, bool) or value is None or isinstance(value, (int, float)):
        return value
    if isinstance(value, list):
        if depth >= 2:
            return {"_type": "list", "_size": len(value)}
        return [compact_prompt_for_recovery(item, depth + 1) for item in value[:12]]
    if isinstance(value, dict):
        if depth >= 3:
            return {"_type": "dict", "_size": len(value), "_keys": sorted(str(key) for key in value.keys())[:12]}
        return {
            str(key): compact_prompt_for_recovery(value[key], depth + 1)
            for key in sorted(value.keys())[:24]
        }
    return str(value)[:500]


def recovery_tool_and_checker_names() -> tuple[set[str], set[str]]:
    tool_names = {str(item) for item in ACTION_GROUNDING_REGISTRY.get("tool_roles", [])}
    checker_names = {str(item) for item in ACTION_GROUNDING_REGISTRY.get("acceptance_checkers", [])}
    return tool_names, checker_names


def backend_recovery_context(
    run_dir: Path,
    plan: dict[str, Any],
    design_team_summary: dict[str, Any],
    backend_closure_llm: dict[str, Any],
) -> dict[str, Any]:
    backend_package = plan.get("backend_package", {}) if isinstance(plan.get("backend_package"), dict) else {}
    app_shell_contract = read_json_if_exists(Path(str(backend_package.get("app_shell_integration_contract") or "")))
    board_shell_contract = read_json_if_exists(Path(str(backend_package.get("board_shell_contract") or "")))
    report_dir = run_dir / "backend_board" / "case_diagnostics"
    return {
        "paper_problem_definition": "Cross-Layer Consistency Problem in Agentic LLM Spatial Accelerator Design",
        "method_boundary": "SACG-guided, template-constrained, checker-verified board/backend closure.",
        "backend_plan": compact_prompt_for_recovery(
            {
                "execution_scope": plan.get("execution_scope"),
                "final_design_pass": plan.get("final_design_pass"),
                "final_design_pass_blockers": plan.get("final_design_pass_blockers", [])[:16],
                "real_tool_status": plan.get("real_tool_status", {}),
                "resolved_board_profile": plan.get("resolved_board_profile", {}),
                "upstream_hierarchy_gate": plan.get("upstream_hierarchy_gate", {}),
            }
        ),
        "contracts": {
            "board_shell_contract": compact_prompt_for_recovery(board_shell_contract),
            "app_shell_integration_contract": compact_prompt_for_recovery(app_shell_contract),
        },
        "tool_evidence": {
            "app_shell_target_discovery": compact_report(report_dir / "app_shell_target_discovery.json"),
            "app_shell_target_hint_synthesis": compact_report(report_dir / "app_shell_target_hint_synthesis.json"),
            "app_shell_target_discovery_after_hint": compact_report(report_dir / "app_shell_target_discovery_after_hint.json"),
            "board_shell_wrapper_manifest": compact_report(run_dir / "generated" / "backend" / "reports" / "board_shell_wrapper_manifest.json"),
            "app_shell_runtime_vivado": compact_report(report_dir / "app_shell_runtime_vivado.json", ["candidate_discovery"]),
            "runtime_abi_check": compact_report(report_dir / "runtime_abi_check.json"),
        },
        "design_team": compact_prompt_for_recovery(design_team_summary),
        "backend_closure_agent": compact_prompt_for_recovery(backend_closure_llm.get("output", {})),
        "action_grounding_registry": ACTION_GROUNDING_REGISTRY,
    }


def prompt_for_backend_recovery(context: dict[str, Any]) -> str:
    return build_prompt(
        agent="backend_bounded_recovery_agent",
        task=(
            "Generate the next bounded recovery action for Stage-7 backend/app-shell closure. "
            "Use the multi-agent design-team outputs and real tool evidence; do not guess board, model, or target names."
        ),
        inputs=context,
        output_schema=BACKEND_RECOVERY_ACTION_SCHEMA,
        rules=[
            "Return one JSON object only.",
            "The output is a recovery action contract, not a hardware pass claim.",
            "Use only tool_roles and acceptance_checkers from action_grounding_registry unless declaring planned_tool.* or planned_checker.*.",
            "Do not use static keyword matching or built-in project/model/board tokens to resolve user intent.",
            "If target identity is ambiguous, the first action must request bounded human/design-team approval or collect additional cited evidence; do not set integration_target.",
            "If upstream_hierarchy_gate is fail, do not schedule Vivado, bitstream, or board runtime; the next action must backtrack to Stage7/Stage6 to complete the three verification repair-loop layers: operator leaf modules, single transformer-layer kernel, and board AXI/DDR wrapped-system closure.",
            "If a target is not approved, runtime bitstream and board runtime actions must be blocked behind explicit preconditions.",
            "Every action must list consumed evidence artifacts and produced artifacts.",
            "Every action that changes a semantic contract must explain approval_boundary and requires_approval.",
            "Tie each action back to SACG evidence gates and the paper story: LLM reasoning plus checker/tool evidence closes cross-layer consistency.",
        ],
    )


def call_backend_recovery_llm(prompt: str, out_dir: Path) -> dict[str, Any]:
    llm = resolved_llm_cfg()
    if str(llm.mode).strip().lower() in {"", "off", "none", "disabled"}:
        raise RuntimeError(f"LLM mode is disabled: {llm.mode}")
    if not llm.endpoint or not llm.api_key or not llm.model:
        raise RuntimeError("missing LLM endpoint, API key, or model")
    llm_dir = out_dir / "llm"
    llm_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = llm_dir / "backend_bounded_recovery_agent_prompt.md"
    result_path = llm_dir / "backend_bounded_recovery_agent_result.json"
    prompt_path.write_text(prompt, encoding="utf-8")
    expected_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    if result_path.is_file():
        try:
            cached = read_json(result_path)
            if (
                cached.get("prompt_hash") == expected_hash
                and not cached.get("error")
                and not cached.get("used_fallback")
                and isinstance(cached.get("output"), dict)
            ):
                print(f"[stage:backend_board:llm] reuse cached backend_bounded_recovery_agent: {result_path}", flush=True)
                return cached
        except Exception:
            pass
    started = time.monotonic()
    raw_text = ""
    retry_errors: list[str] = []
    try:
        raw_text, retry_errors = call_llm_with_retry(
            llm.endpoint,
            llm.api_key,
            llm.model,
            prompt,
            "backend_bounded_recovery_json",
            BACKEND_RECOVERY_ACTION_SCHEMA,
            llm_timeout_sec(),
            reasoning_effort=llm.reasoning_effort,
        )
        try:
            output = parse_json_object(raw_text)
            validate_schema(output, BACKEND_RECOVERY_ACTION_SCHEMA, "backend_bounded_recovery")
        except Exception as exc:
            repair = repair_prompt("backend_bounded_recovery_agent", prompt, raw_text, str(exc), BACKEND_RECOVERY_ACTION_SCHEMA)
            repair_text, repair_retry_errors = call_llm_with_retry(
                llm.endpoint,
                llm.api_key,
                llm.model,
                repair,
                "backend_bounded_recovery_repair_json",
                BACKEND_RECOVERY_ACTION_SCHEMA,
                llm_timeout_sec(),
                reasoning_effort=llm.reasoning_effort,
            )
            retry_errors.extend(repair_retry_errors)
            output = parse_json_object(repair_text)
            validate_schema(output, BACKEND_RECOVERY_ACTION_SCHEMA, "backend_bounded_recovery_repair")
        record = {
            "schema_version": "spatialaccagent.backend_bounded_recovery_llm_record.v0",
            "request_path": str(prompt_path),
            "prompt_hash": expected_hash,
            "result_path": str(result_path),
            "used_fallback": False,
            "error": None,
            "retry_errors": retry_errors,
            "duration_sec": time.monotonic() - started,
            "output": output,
        }
        write_json(result_path, record)
        return record
    except Exception as exc:
        record = {
            "schema_version": "spatialaccagent.backend_bounded_recovery_llm_record.v0",
            "request_path": str(prompt_path),
            "prompt_hash": expected_hash,
            "result_path": str(result_path),
            "used_fallback": False,
            "error": str(exc),
            "retry_errors": retry_errors,
            "duration_sec": time.monotonic() - started,
            "raw_text_tail": raw_text[-2000:],
            "output": None,
        }
        write_json(result_path, record)
        raise


def validate_backend_recovery_actions(output: dict[str, Any], context: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    actions = output.get("bounded_recovery_actions", []) if isinstance(output.get("bounded_recovery_actions"), list) else []
    if not actions:
        errors.append("bounded_recovery_actions is empty")
        return errors
    tool_names, checker_names = recovery_tool_and_checker_names()
    contract = context.get("contracts", {}).get("app_shell_integration_contract", {})
    target_decision = contract.get("target_selection_decision", {}) if isinstance(contract, dict) and isinstance(contract.get("target_selection_decision"), dict) else {}
    target_approved = str(target_decision.get("decision") or "") == "approved_target"
    target_blocked_roles = {"app_shell_runtime_bitstream", "case_runtime_bitstream", "board_runtime"}
    backend_execution_roles = {
        "case_vivado_synthesis",
        "case_vivado_implementation",
        "case_runtime_bitstream",
        "app_shell_runtime_bitstream",
        "board_runtime",
    }
    backend_plan = context.get("backend_plan", {}) if isinstance(context.get("backend_plan"), dict) else {}
    upstream_gate = backend_plan.get("upstream_hierarchy_gate", {}) if isinstance(backend_plan.get("upstream_hierarchy_gate"), dict) else {}
    upstream_failed = upstream_gate.get("status") == "fail"
    for index, action in enumerate(actions):
        if not isinstance(action, dict):
            errors.append(f"action[{index}] is not an object")
            continue
        tool_roles = [str(item) for item in action.get("tool_roles", []) if str(item)]
        checkers = [str(item) for item in action.get("acceptance_checkers", []) if str(item)]
        if not tool_roles:
            errors.append(f"action[{index}] has no tool_roles")
        if not checkers:
            errors.append(f"action[{index}] has no acceptance_checkers")
        for role in tool_roles:
            if role not in tool_names and not role.startswith("planned_tool."):
                errors.append(f"action[{index}] unknown tool_role={role}")
        for checker in checkers:
            if checker not in checker_names and not checker.startswith("planned_checker."):
                errors.append(f"action[{index}] unknown acceptance_checker={checker}")
        if upstream_failed and backend_execution_roles.intersection(tool_roles):
            errors.append(
                f"action[{index}] schedules backend/runtime/board tool roles before upstream hierarchical verification is backend-ready"
            )
        if not target_approved and target_blocked_roles.intersection(tool_roles):
            blocked_until = action.get("blocked_until", []) if isinstance(action.get("blocked_until"), list) else []
            preconditions = action.get("preconditions", []) if isinstance(action.get("preconditions"), list) else []
            if not blocked_until and not preconditions and not action.get("requires_approval"):
                errors.append(
                    f"action[{index}] schedules runtime/board execution without approved target preconditions"
                )
    return errors


def path_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def safe_recovery_output_path(path_value: Any, run_dir: Path, out_dir: Path, fallback_name: str) -> Path | None:
    if not nonblank(path_value):
        return out_dir / "recovery" / fallback_name
    path = Path(str(path_value))
    if not path.is_absolute():
        path = run_dir / path
    if path_within(path, run_dir):
        return path
    return None


def materialize_backend_recovery_outputs(
    run_dir: Path,
    out_dir: Path,
    recovery_output: dict[str, Any],
) -> list[dict[str, Any]]:
    produced: list[dict[str, Any]] = []
    actions = recovery_output.get("bounded_recovery_actions", []) if isinstance(recovery_output.get("bounded_recovery_actions"), list) else []
    citations = recovery_output.get("evidence_citations", []) if isinstance(recovery_output.get("evidence_citations"), list) else []
    for index, action in enumerate(actions):
        if not isinstance(action, dict):
            continue
        action_id = safe_id(str(action.get("id") or f"action_{index}"))
        requested_paths = action.get("produces", []) if isinstance(action.get("produces"), list) else []
        if not requested_paths:
            requested_paths = [str(out_dir / "recovery" / f"{action_id}.json")]
        for produce_index, path_value in enumerate(requested_paths):
            target = safe_recovery_output_path(
                path_value,
                run_dir,
                out_dir,
                f"{action_id}_{produce_index}.json",
            )
            if target is None:
                produced.append(
                    {
                        "requested_path": str(path_value),
                        "status": "skipped",
                        "reason": "recovery output path is outside the current run directory",
                    }
                )
                continue
            request = {
                "schema_version": "spatialaccagent.backend_recovery_handoff.v0",
                "status": "pending_approval" if action.get("requires_approval") else "pending_execution",
                "run_dir": str(run_dir),
                "decision": recovery_output.get("decision"),
                "next_stage": recovery_output.get("next_stage"),
                "action": action,
                "evidence_citations": citations[:12],
                "approval_record_schema": {
                    "schema_version": "spatialaccagent.human_boundary_approval.v0",
                    "decision": "approved | rejected | request_more_evidence",
                    "selected_option": "required only when approving exactly one option from the cited action boundary",
                    "rationale": "required source/evidence-grounded reason",
                    "approver": "human or delegated design-team authority",
                    "timestamp": "ISO-8601 timestamp supplied by the approval recorder",
                },
                "policy": (
                    "This handoff materializes an LLM-derived bounded recovery action. "
                    "It does not modify semantic contracts or claim backend/board pass."
                ),
            }
            write_json(target, request)
            produced.append({"path": str(target), "status": "written", "action_id": action.get("id")})
    return produced


def generate_backend_bounded_recovery_actions(
    run_dir: Path,
    out_dir: Path,
    plan: dict[str, Any],
    design_team_summary: dict[str, Any],
    backend_closure_llm: dict[str, Any],
) -> tuple[Path, dict[str, Any]]:
    recovery_path = out_dir / "bounded_recovery_actions.json"
    context = backend_recovery_context(run_dir, plan, design_team_summary, backend_closure_llm)
    prompt = prompt_for_backend_recovery(context)
    blockers: list[str] = []
    llm_record: dict[str, Any] = {}
    output: dict[str, Any] = {}
    try:
        llm_record = call_backend_recovery_llm(prompt, out_dir)
        output = llm_record.get("output", {}) if isinstance(llm_record.get("output"), dict) else {}
        blockers.extend(validate_backend_recovery_actions(output, context))
    except Exception as exc:
        blockers.append(f"backend bounded recovery LLM failed: {exc}")
    produced_files = materialize_backend_recovery_outputs(run_dir, out_dir, output) if output and not blockers else []
    report = {
        "schema_version": "spatialaccagent.backend_bounded_recovery_actions.v0",
        "status": "pass" if output and not blockers else "fail",
        "summary": output.get("summary") if output and not blockers else f"{len(blockers)} blocker(s)",
        "decision": output.get("decision"),
        "bounded_recovery_actions": output.get("bounded_recovery_actions", []) if output else [],
        "forbidden_actions": output.get("forbidden_actions", []) if output else [],
        "sacg_updates": output.get("sacg_updates", []) if output else [],
        "next_stage": output.get("next_stage") if output else None,
        "evidence_citations": output.get("evidence_citations", []) if output else [],
        "produced_files": produced_files,
        "llm_record_path": llm_record.get("result_path"),
        "checks": [
            {
                "name": "backend_bounded_recovery_llm_output",
                "status": "pass" if output else "fail",
                "summary": output.get("decision") if output else "missing output",
            },
            {
                "name": "backend_bounded_recovery_action_contract",
                "status": "pass" if output and not blockers else "fail",
                "summary": "; ".join(blockers[:4]) if blockers else "bounded recovery action contract is valid",
            },
        ],
        "blockers": blockers,
        "policy": "Pass means the LLM design team produced a bounded, machine-checkable recovery action; it is not backend/board pass evidence.",
    }
    write_json(recovery_path, report)
    return recovery_path, report


def write_board_shell_contract(run_dir: Path, state: dict[str, Any], resolved_board_profile: dict[str, Any]) -> Path:
    contract_path = board_shell_contract_path(run_dir)
    runtime_cfg = run_dir / "generated" / "chisel" / "runtime" / "runtime_config.json"
    memory_layout = run_dir / "generated" / "chisel" / "memory" / "memory_layout.json"
    contract = build_board_shell_contract(
        state,
        {"resolved_board_profile": {"path": resolved_board_profile.get("path") if isinstance(resolved_board_profile, dict) else None}},
        runtime_cfg,
        memory_layout,
    )
    write_json(contract_path, contract)
    return contract_path


def write_initial_app_shell_integration_contract(run_dir: Path, state: dict[str, Any], resolved_board_profile: dict[str, Any]) -> Path:
    contract_path = app_shell_integration_contract_path(run_dir)
    board_contract_path = board_shell_contract_path(run_dir)
    board_contract = read_json(board_contract_path) if board_contract_path.exists() else {}
    seed_plan = {
        "resolved_board_profile": {
            "path": resolved_board_profile.get("path") if isinstance(resolved_board_profile, dict) else None,
        },
        "real_tool_status": {
            "backend_selected": [],
        },
    }
    write_json(contract_path, build_app_shell_integration_contract(run_dir, state, seed_plan, board_contract))
    return contract_path


def build_board_shell_contract(
    state: dict[str, Any],
    plan: dict[str, Any],
    runtime_cfg_path: Path,
    memory_layout_path: Path,
) -> dict[str, Any]:
    resolved_info = plan.get("resolved_board_profile", {}) if isinstance(plan.get("resolved_board_profile"), dict) else {}
    resolved_path_value = str(resolved_info.get("path") or "")
    resolved_path = Path(resolved_path_value)
    resolved_profile = read_json(resolved_path) if resolved_path_value and resolved_path.is_file() else {}
    runtime_cfg = read_json(runtime_cfg_path) if runtime_cfg_path.exists() else {}
    memory_layout = read_json(memory_layout_path) if memory_layout_path.exists() else {}

    memory = resolved_profile.get("memory_system", {}) if isinstance(resolved_profile.get("memory_system"), dict) else {}
    shell = resolved_profile.get("shell", {}) if isinstance(resolved_profile.get("shell"), dict) else {}
    profile_runtime = resolved_profile.get("runtime_interface", {}) if isinstance(resolved_profile.get("runtime_interface"), dict) else {}
    runtime_cfg_interface = runtime_cfg.get("runtime_interface", {}) if isinstance(runtime_cfg.get("runtime_interface"), dict) else {}
    runtime = merged_runtime_interface(profile_runtime, runtime_cfg_interface)

    raw_prefix = first_nonblank(memory.get("core_side_interface_name"), shell.get("core_ddr_axi_interface"))
    prefix = normalized_axi_prefix(raw_prefix)
    data_bits = int_or_none(first_nonblank(memory.get("axi_data_width_bits"), memory.get("ddr_word_width_bits"), memory_layout.get("axi_data_width_bits")))
    data_bytes = int_or_none(first_nonblank(memory.get("axi_data_bytes"), memory_layout.get("alignment_bytes"), data_bits // 8 if data_bits else None))
    address_map = memory.get("address_map", {}) if isinstance(memory.get("address_map"), dict) else {}
    regions = memory_layout.get("regions", []) if isinstance(memory_layout.get("regions"), list) else []

    required_contract_fields = {
        "board_interface_prefix": prefix,
        "board_axi_data_width_bits": data_bits,
        "board_axi_clock": first_nonblank(memory.get("axi_clock"), shell.get("axi_clock")),
        "board_axi_reset": first_nonblank(memory.get("axi_reset"), shell.get("axi_reset")),
        "runtime_control_protocol": runtime.get("control_protocol"),
        "runtime_board_run_command": runtime.get("board_run_command"),
        "memory_layout_regions": regions,
    }
    missing_fields = [name for name, value in required_contract_fields.items() if not nonblank(value)]
    return {
        "schema_version": "spatialaccagent.board_shell_contract.v0",
        "design_id": state.get("design_id"),
        "status": "ready_for_generation" if not missing_fields else "incomplete",
        "source_artifacts": {
            "resolved_target_board_profile": str(resolved_path) if resolved_path_value and resolved_path.is_file() else None,
            "runtime_config": str(runtime_cfg_path),
            "memory_layout": str(memory_layout_path),
        },
        "board_interface": {
            "protocol": first_nonblank(memory.get("axi_protocol"), "AXI"),
            "raw_interface_name": raw_prefix,
            "signal_prefix": prefix,
            "data_width_bits": data_bits,
            "beat_bytes": data_bytes,
            "addr_width_bits": int_or_none(memory.get("axi_addr_width_bits")),
            "id_width_bits": int_or_none(memory.get("axi_id_width_bits")),
            "wstrb_width_bits": int_or_none(first_nonblank(memory.get("axi_wstrb_width_bits"), data_bytes)),
            "clock": required_contract_fields["board_axi_clock"],
            "reset": required_contract_fields["board_axi_reset"],
            "calibration_done": first_nonblank(memory.get("calibration_done_signal"), shell.get("init_calibration_done_signal")),
            "reference_rtl": first_nonblank(memory.get("real_board_reference_rtl"), shell.get("real_board_axi_reference_rtl")),
        },
        "generated_core": {
            "top_module": runtime_cfg.get("top_module"),
            "chisel_top": runtime_cfg.get("chisel_top"),
            "params": runtime_cfg.get("params", {}),
            "current_runtime_config": str(runtime_cfg_path),
        },
        "runtime_abi": {
            "control_protocol": runtime.get("control_protocol"),
            "board_run_command": runtime.get("board_run_command"),
            "remote_host": first_nonblank(runtime.get("remote_host"), runtime.get("runtime_machine")),
            "xdma_id_default": first_nonblank(runtime.get("xdma_id_default"), runtime.get("xdma_id_variable")),
            "h2c_device_template": runtime.get("h2c_device_template"),
            "c2h_device_template": runtime.get("c2h_device_template"),
            "ctrl_base": first_nonblank(runtime.get("ctrl_base"), runtime.get("control_base"), address_map.get("control_registers")),
            "ddr_base": first_nonblank(runtime.get("ddr_base"), address_map.get("ddr_base"), address_map.get("input_abs")),
            "output_abs": first_nonblank(runtime.get("output_abs"), address_map.get("output_abs")),
            "ddr_image_default": first_nonblank(runtime.get("ddr_image_default"), runtime.get("default_ddr_image_path_observed")),
        },
        "memory_layout": {
            "axi_data_width_bits": memory_layout.get("axi_data_width_bits"),
            "alignment_bytes": memory_layout.get("alignment_bytes"),
            "total_bytes": memory_layout.get("total_bytes"),
            "regions": [
                {
                    "name": item.get("name"),
                    "role": item.get("role"),
                    "base_addr": item.get("base_addr"),
                    "size_bytes": item.get("size_bytes"),
                    "alignment_bytes": item.get("alignment_bytes"),
                }
                for item in regions
                if isinstance(item, dict)
            ],
        },
        "adapter_requirements": [
            "Expose the board DDR AXI interface using board_interface.signal_prefix and the exact board clock/reset/calibration signals.",
            "Bridge the generated core memory/runtime protocol to the board AXI data width and byte-strobe width without changing the model-level memory layout.",
            "Drive control/status behavior according to runtime_abi.control_protocol and the declared address map.",
            "Generate runtime bitstream evidence and board runtime logs before claiming backend or board pass.",
        ],
        "pass_criteria": {
            "contract_complete": not missing_fields,
            "runtime_abi_check_pass": False,
            "runtime_board_shell_bitstream_exists": False,
            "board_runtime_log_pass": False,
        },
        "missing_fields": missing_fields,
        "policy": "The contract is derived from current-run artifacts and source-evidence-resolved board profile; it must not encode case-specific constants in the Stage-7 core.",
    }


def read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return read_json(path)
    except Exception:
        return {}


def runtime_bitstream_tool_result(plan: dict[str, Any]) -> dict[str, Any]:
    real_status = plan.get("real_tool_status", {}) if isinstance(plan.get("real_tool_status"), dict) else {}
    selected = real_status.get("backend_selected", []) if isinstance(real_status.get("backend_selected"), list) else []
    for item in selected:
        if not isinstance(item, dict):
            continue
        if item.get("checker") == "real_tool.case_runtime_bitstream" or item.get("kind") == "runtime_board_shell_vivado":
            return item
    return {}


def structural_app_shell_blockers(blockers: list[Any]) -> list[str]:
    result = []
    for blocker in blockers:
        text = str(blocker)
        if any(token in text for token in ["app_shell", "too many physical IOs", "IOSTANDARD", "LOC constraints", "top-level board-shell ports"]):
            result.append(text)
    return result


def text_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    if not text:
        return []
    return [item for item in (part.strip() for part in re.split(r"[,;\n]+", text)) if item]


def add_policy_values(values: list[str], sources: list[dict[str, str]], value: Any, source: str) -> None:
    for item in text_list(value):
        if len(item) < 3:
            continue
        if item not in values:
            values.append(item)
            sources.append({"source": source, "value": item})


def bool_from_profile(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def int_from_profile(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def build_target_discovery_policy(
    existing_contract: dict[str, Any],
    shell: dict[str, Any],
    sample_project: dict[str, Any],
    integration_target: dict[str, Any],
) -> dict[str, Any]:
    existing_policy = existing_contract.get("target_discovery_policy", {}) if isinstance(existing_contract.get("target_discovery_policy"), dict) else {}
    shell_policy = shell.get("target_discovery_policy", {}) if isinstance(shell.get("target_discovery_policy"), dict) else {}
    sample_policy = sample_project.get("target_discovery_policy", {}) if isinstance(sample_project.get("target_discovery_policy"), dict) else {}
    hints: list[str] = []
    hint_sources: list[dict[str, str]] = []
    excludes: list[str] = []
    exclude_sources: list[dict[str, str]] = []

    add_policy_values(hints, hint_sources, integration_target.get("ip_name"), "integration_target.ip_name")
    add_policy_values(hints, hint_sources, integration_target.get("bd_cell"), "integration_target.bd_cell")
    for scope_name, scope in [("shell", shell), ("sample_project", sample_project)]:
        for key in ["target_ip_name", "target_bd_cell", "accelerator_ip_name", "accelerator_bd_cell", "compute_ip_name", "compute_bd_cell"]:
            add_policy_values(hints, hint_sources, scope.get(key), f"{scope_name}.{key}")
    for scope_name, policy in [("existing_contract", existing_policy), ("shell", shell_policy), ("sample_project", sample_policy)]:
        for key in ["candidate_name_hints", "target_name_hints", "hint_keywords", "keywords", "target_ip_hints", "target_bd_cell_hints"]:
            add_policy_values(hints, hint_sources, policy.get(key), f"{scope_name}.target_discovery_policy.{key}")
        for key in ["exclude_keywords", "exclude_name_hints"]:
            add_policy_values(excludes, exclude_sources, policy.get(key), f"{scope_name}.target_discovery_policy.{key}")

    auto_select = bool_from_profile(
        first_nonblank(
            existing_policy.get("auto_select"),
            existing_policy.get("auto_select_enabled"),
            shell_policy.get("auto_select"),
            shell_policy.get("auto_select_enabled"),
            sample_policy.get("auto_select"),
            sample_policy.get("auto_select_enabled"),
        ),
        False,
    )
    return {
        "schema_version": "spatialaccagent.app_shell_target_discovery_policy.v0",
        "auto_select": auto_select,
        "candidate_name_hints": hints,
        "exclude_keywords": excludes,
        "hint_sources": hint_sources,
        "exclude_sources": exclude_sources,
        "score_threshold": int_from_profile(first_nonblank(existing_policy.get("score_threshold"), shell_policy.get("score_threshold"), sample_policy.get("score_threshold")), 30),
        "selection_margin": int_from_profile(first_nonblank(existing_policy.get("selection_margin"), shell_policy.get("selection_margin"), sample_policy.get("selection_margin")), 8),
        "no_default_model_or_board_keywords": True,
        "llm_expected_role": (
            "When profile fields are incomplete, the multi-agent design team must infer candidate_name_hints "
            "from user-supplied board/app-shell materials and real Vivado evidence with cited sources; "
            "Stage-7 scripts must not invent Qwen/OPT/app-shell/project-specific keywords."
        ),
    }


def build_app_shell_integration_contract(
    run_dir: Path,
    state: dict[str, Any],
    plan: dict[str, Any],
    board_shell_contract: dict[str, Any],
) -> dict[str, Any]:
    resolved_info = plan.get("resolved_board_profile", {}) if isinstance(plan.get("resolved_board_profile"), dict) else {}
    resolved_path_value = str(resolved_info.get("path") or "")
    resolved_profile = read_json_if_exists(Path(resolved_path_value)) if resolved_path_value else {}
    board = resolved_profile.get("board", {}) if isinstance(resolved_profile.get("board"), dict) else {}
    shell = resolved_profile.get("shell", {}) if isinstance(resolved_profile.get("shell"), dict) else {}
    runtime = resolved_profile.get("runtime_interface", {}) if isinstance(resolved_profile.get("runtime_interface"), dict) else {}
    sample_project = board.get("sample_project", {}) if isinstance(board.get("sample_project"), dict) else {}
    board_interface = board_shell_contract.get("board_interface", {}) if isinstance(board_shell_contract.get("board_interface"), dict) else {}
    generated_core = board_shell_contract.get("generated_core", {}) if isinstance(board_shell_contract.get("generated_core"), dict) else {}
    runtime_abi = board_shell_contract.get("runtime_abi", {}) if isinstance(board_shell_contract.get("runtime_abi"), dict) else {}
    existing_contract = read_json_if_exists(app_shell_integration_contract_path(run_dir))
    board_identity, binding_requirements = current_app_shell_binding_artifacts(run_dir)
    compute_slot_abi = board_identity.get("compute_slot_abi", {}) if isinstance(board_identity.get("compute_slot_abi"), dict) else {}
    connected_weight = binding_requirements.get("connected_weight_stream_contract", {}) if isinstance(binding_requirements.get("connected_weight_stream_contract"), dict) else {}
    connected_runtime = binding_requirements.get("connected_runtime_stream_contract", {}) if isinstance(binding_requirements.get("connected_runtime_stream_contract"), dict) else {}
    existing_target = existing_contract.get("integration_target", {}) if isinstance(existing_contract.get("integration_target"), dict) else {}
    existing_discovery = existing_contract.get("target_discovery", {}) if isinstance(existing_contract.get("target_discovery"), dict) else {}
    existing_target_selection_decision = (
        existing_contract.get("target_selection_decision", {})
        if isinstance(existing_contract.get("target_selection_decision"), dict)
        else {}
    )

    runtime_tool = runtime_bitstream_tool_result(plan)
    runtime_report_path = first_nonblank(
        runtime_tool.get("tool_report_path"),
        str(run_dir / "backend_board" / "case_diagnostics" / "runtime_board_shell_vivado.json"),
    )
    runtime_report = read_json_if_exists(Path(str(runtime_report_path))) if nonblank(runtime_report_path) else {}
    runtime_blockers = runtime_report.get("blockers", []) if isinstance(runtime_report.get("blockers"), list) else runtime_tool.get("tool_report_blockers", [])
    structural_blockers = structural_app_shell_blockers(runtime_blockers)

    shell_project = first_nonblank(shell.get("vivado_project_path"), sample_project.get("source_path"))
    remote_host = first_nonblank(runtime.get("remote_host"), sample_project.get("host"), runtime_abi.get("remote_host"))
    remote_port = first_nonblank(runtime.get("remote_ssh_port"), sample_project.get("ssh_port"))
    slot_module = first_nonblank(compute_slot_abi.get("replacement_module_identity"), compute_slot_abi.get("slot_module"))
    slot_instance = first_nonblank(compute_slot_abi.get("replacement_instance_boundary"), compute_slot_abi.get("slot_instance_path"))
    slot_cell = compute_slot_abi.get("selected_cell_id")
    slot_ooc_run = first_nonblank(
        compute_slot_abi.get("ooc_run"),
        f"{slot_module}_synth_1" if nonblank(slot_module) else None,
    )
    identity_ready = compute_slot_abi.get("status") == "pass" and bool(compute_slot_abi.get("all_required_ports_bound"))
    integration_target = {
        "ip_name": first_nonblank(
            slot_module,
            existing_target.get("ip_name"),
            shell.get("accelerator_ip_name"),
            shell.get("compute_ip_name"),
            shell.get("target_ip_name"),
            sample_project.get("accelerator_ip_name"),
            sample_project.get("target_ip_name"),
        ),
        "bd_cell": first_nonblank(
            slot_instance,
            existing_target.get("bd_cell"),
            shell.get("accelerator_bd_cell"),
            shell.get("compute_bd_cell"),
            shell.get("target_bd_cell"),
            sample_project.get("accelerator_bd_cell"),
            sample_project.get("target_bd_cell"),
        ),
        "bd_path": first_nonblank(existing_target.get("bd_path"), shell.get("bd_path"), sample_project.get("bd_path"), board_identity.get("top_module")),
        "adapter_contract": first_nonblank(existing_target.get("adapter_contract"), shell.get("adapter_contract"), sample_project.get("adapter_contract"), "compute_slot_abi"),
        "replacement_module_identity": slot_module,
        "replacement_instance_boundary": slot_instance,
        "selected_cell_id": slot_cell,
        "ooc_run": slot_ooc_run,
    }
    identity_selection = {
        "decision": "approved_target" if identity_ready else "unresolved_target",
        "selection_reason": "selected from current board_source_identity.compute_slot_abi",
        "selected_target": {
            "module": slot_module,
            "instance_path": slot_instance,
            "selected_cell_id": slot_cell,
            "ooc_run": slot_ooc_run,
        },
        "evidence": [
            str(board_source_identity_path(run_dir)),
            f"compute_slot_abi_sha256={board_identity.get('compute_slot_abi_sha256')}",
        ],
    }
    target_discovery_policy = build_target_discovery_policy(existing_contract, shell, sample_project, integration_target)
    required_fields = {
        "shell.vivado_project_path": shell_project,
        "board_interface.signal_prefix": board_interface.get("signal_prefix"),
        "board_interface.clock": board_interface.get("clock"),
        "board_interface.reset": board_interface.get("reset"),
        "board_interface.data_width_bits": board_interface.get("data_width_bits"),
        "generated_core.top_module": generated_core.get("top_module"),
        "runtime_abi.control_protocol": runtime_abi.get("control_protocol"),
        "remote_host": remote_host,
        "compute_slot_abi.status": compute_slot_abi.get("status"),
        "compute_slot_abi.replacement_module_identity": slot_module,
        "compute_slot_abi.replacement_instance_boundary": slot_instance,
    }
    missing_fields = [name for name, value in required_fields.items() if not nonblank(value)]
    target_selected = identity_ready and nonblank(first_nonblank(integration_target.get("ip_name"), integration_target.get("bd_cell")))
    if missing_fields:
        status = "incomplete"
    elif target_selected:
        status = "ready_for_app_shell_generation"
    elif existing_discovery and not identity_ready:
        status = "target_discovery_needs_approval"
    else:
        status = "target_discovery_required"
    return {
        "schema_version": "spatialaccagent.app_shell_integration_contract.v0",
        "design_id": state.get("design_id"),
        "status": status,
        "integration_mode": "existing_shell_project_internal_axi_integration",
        "source_artifacts": {
            "resolved_target_board_profile": resolved_path_value or None,
            "board_shell_contract": str(board_shell_contract_path(run_dir)),
            "board_shell_wrapper_rtl": str(board_shell_wrapper_rtl_path(run_dir)),
            "board_shell_wrapper_manifest": str(board_shell_wrapper_manifest_path(run_dir)),
            "runtime_board_shell_vivado_report": str(runtime_report_path) if nonblank(runtime_report_path) else None,
            "board_source_identity": str(board_source_identity_path(run_dir)),
            "dut_weight_binding_requirements": str(dut_weight_binding_requirements_path(run_dir)),
            "semantic_testbench_manifest": str(semantic_testbench_manifest_path(run_dir)),
        },
        "shell_project": {
            "name": first_nonblank(shell.get("name"), shell.get("base_shell_name")),
            "base_shell_name": shell.get("base_shell_name"),
            "vivado_project_path": shell_project,
            "sample_project_root": sample_project.get("root"),
            "remote_host": remote_host,
            "remote_ssh_port": remote_port,
            "reference_rtl": first_nonblank(shell.get("real_board_axi_reference_rtl"), board_interface.get("reference_rtl")),
            "ddr_axi_interface": first_nonblank(shell.get("core_ddr_axi_interface"), board_interface.get("raw_interface_name")),
        },
        "integration_target": integration_target,
        "compute_slot_abi": compute_slot_abi,
        "loader_route_contract": {
            "weight": connected_weight,
            "runtime": connected_runtime,
        },
        "dut_loader_route_contract": binding_requirements.get("loader_route_contract", {}),
        "source_identity": {
            "schema_version": board_identity.get("schema_version"),
            "status": board_identity.get("status"),
            "compute_slot_abi_sha256": board_identity.get("compute_slot_abi_sha256"),
            "selected_simulation_source_closure_sha256": board_identity.get("selected_simulation_source_closure_sha256"),
        },
        "target_discovery_policy": target_discovery_policy,
        "target_discovery": existing_discovery,
        "target_selection_decision": existing_target_selection_decision or identity_selection,
        "board_interface": board_interface,
        "generated_core": generated_core,
        "runtime_abi": runtime_abi,
        "previous_runtime_board_shell_vivado": {
            "status": runtime_report.get("status") or runtime_tool.get("tool_report_status"),
            "summary": runtime_report.get("summary") or runtime_tool.get("tool_report_summary"),
            "out_dir": runtime_report.get("out_dir"),
            "strict_io_drc": runtime_report.get("strict_io_drc"),
            "structural_blockers": structural_blockers,
            "blockers": runtime_blockers,
        },
        "required_actions": [
            "Open or clone the shell_project.vivado_project_path supplied by the board profile.",
            "Use the LLM design-team roles to convert user board/app-shell material and real Vivado evidence into target_discovery_policy updates with cited source fields.",
            "Integrate the generated runtime wrapper as an internal compute block behind the existing shell DDR/AXI subsystem.",
            "Generate the replacement module named by compute_slot_abi.replacement_module_identity and match compute_slot_abi.required_ports exactly.",
            "Use loader_route_contract from the current real-weight/runtime contracts to connect GeneratedAxiDdrTop; do not instantiate a semantic harness substitute.",
            "Connect board_interface.signal_prefix, clock, reset, and calibration signals inside the shell instead of exposing them as top-level FPGA pins.",
            "Preserve runtime_abi register/DDRx address semantics and memory_layout offsets from the current run.",
            "Run shell-level synthesis, implementation, timing, DRC, bitstream generation, and board runtime log collection before claiming pass.",
        ],
        "pass_criteria": {
            "standalone_board_shell_vivado_synth_is_not_enough": True,
            "top_level_axi_pins_must_not_exceed_board_io_limit": True,
            "shell_level_timing_drc_clean": True,
            "app_shell_bitstream_exists": True,
            "board_runtime_log_pass": True,
            "compute_slot_abi_status_pass": True,
            "generated_adapter_exact_port_match": True,
        },
        "missing_fields": missing_fields,
        "policy": "This contract is derived from current-run board/profile/evidence artifacts and must not encode Qwen, OPT, or a fixed board in the Stage-7 core.",
    }


def generate_backend_package(run_dir: Path, state: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    package_dir = run_dir / "generated" / "backend"
    constraints_dir = package_dir / "constraints"
    reports_dir = package_dir / "reports"
    rtl_dir = package_dir / "rtl"
    constraints_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    rtl_dir.mkdir(parents=True, exist_ok=True)

    artifacts = read_json(artifact_path(state, "artifact.stage5.design_artifact_manifest"))
    code_root = artifacts.get("generated_package_root", str(run_dir / "generated" / "chisel"))
    runtime_cfg = run_dir / "generated" / "chisel" / "runtime" / "runtime_config.json"
    memory_layout = run_dir / "generated" / "chisel" / "memory" / "memory_layout.json"

    # Real execution belongs exclusively to the current case adapter's exact
    # app-shell Vivado tool. Do not emit placeholder Tcl or smoke scripts that
    # look executable but cannot produce valid board evidence.
    stale_scripts_dir = package_dir / "scripts"
    if stale_scripts_dir.is_dir():
        for name in ("vivado_synth.tcl", "vivado_impl.tcl", "board_smoke.sh", "collect_reports.sh"):
            path = stale_scripts_dir / name
            if path.exists():
                path.unlink()
        try:
            stale_scripts_dir.rmdir()
        except OSError:
            pass
    write_json(
        constraints_dir / "backend_handoff.json",
        {
            "schema_version": "spatialaccagent.backend_handoff.v0",
            "design_id": state.get("design_id"),
            "code_root": code_root,
            "top_name": "GeneratedAxiDdrTop",
            "runtime_config": str(runtime_cfg),
            "memory_layout": str(memory_layout),
            "qor_outputs": plan.get("qor_outputs", []),
            "pass_criteria": plan.get("pass_criteria", {}),
            "final_design_pass_blockers": plan.get("final_design_pass_blockers", []),
            "execution_authority": "case_adapter.app_shell_runtime_bitstream",
            "rule": "Only the current case adapter's exact app-shell Vivado tool may execute backend work or establish final board evidence.",
        },
    )
    board_shell_contract = build_board_shell_contract(state, plan, runtime_cfg, memory_layout)
    board_shell_contract_path = constraints_dir / "board_shell_contract.json"
    write_json(board_shell_contract_path, board_shell_contract)
    app_shell_contract = build_app_shell_integration_contract(run_dir, state, plan, board_shell_contract)
    app_shell_contract_path = constraints_dir / "app_shell_integration_contract.json"
    write_json(app_shell_contract_path, app_shell_contract)
    files = sorted(str(path.relative_to(run_dir)) for path in package_dir.rglob("*") if path.is_file())
    return {
        "root": str(package_dir),
        "files": files,
        "board_shell_contract": str(board_shell_contract_path),
        "board_shell_wrapper_rtl": str(board_shell_wrapper_rtl_path(run_dir)),
        "board_shell_wrapper_manifest": str(board_shell_wrapper_manifest_path(run_dir)),
        "app_shell_integration_contract": str(app_shell_contract_path),
        "app_shell_target_selection_decision": str(reports_dir / "app_shell_target_selection_decision.json"),
    }


def build_plan(
    state: dict[str, Any],
    tool_results: list[dict[str, Any]],
    tool_selection_blockers: list[str],
    resolved_board_profile: dict[str, Any],
    upstream_hierarchy_gate: dict[str, Any] | None = None,
    dse_measurement: dict[str, Any] | None = None,
    dse_campaign: dict[str, Any] | None = None,
) -> dict[str, Any]:
    deployment = constraint_facts(state, "constraint.deployment.board")
    memory = constraint_facts(state, "constraint.memory.board")
    runtime = constraint_facts(state, "constraint.runtime.board")
    resolved_profile = resolved_board_profile.get("profile", {}) if isinstance(resolved_board_profile, dict) else {}
    resolved_memory = resolved_profile.get("memory_system", {}) if isinstance(resolved_profile.get("memory_system"), dict) else memory.get("memory_system", {})
    resolved_runtime = resolved_profile.get("runtime_interface", {}) if isinstance(resolved_profile.get("runtime_interface"), dict) else runtime
    resolved_board = resolved_profile.get("board", {}) if isinstance(resolved_profile.get("board"), dict) else deployment.get("board", {})
    resolved_shell = resolved_profile.get("shell", {}) if isinstance(resolved_profile.get("shell"), dict) else deployment.get("shell", {})
    resolved_pass_criteria = resolved_profile.get("board_pass_criteria", {}) if isinstance(resolved_profile.get("board_pass_criteria"), dict) else deployment.get("board_pass_criteria", {})
    try:
        repair = read_json(artifact_path(state, "artifact.stage6.repair_plan"))
    except KeyError:
        repair = {
            "schema_version": "spatialaccagent.repair_plan.v0",
            "stage": "repair",
            "status": "not_required",
            "pending_evidence": [],
            "summary": "No Stage-6 repair plan is required when upstream verification is already promoted.",
        }
    verification = read_json(artifact_path(state, "artifact.stage6.verification_result"))
    artifacts = read_json(artifact_path(state, "artifact.stage5.design_artifact_manifest"))
    pending = repair.get("pending_evidence", [])
    verification_tools = [item for item in verification.get("results", []) if str(item.get("checker", "")).startswith("real_tool.")]
    current_by_checker = {str(item.get("checker")): item for item in tool_results}
    carried_backend_tools = [
        item for item in existing_real_tool_evidence(state)
        if str(item.get("checker")) not in current_by_checker
    ]
    backend_tools = [*carried_backend_tools, *tool_results]
    real_tools = [*verification_tools, *backend_tools]
    failed_tools = [item for item in real_tools if item.get("status") == "fail"]
    passed_tools = [item for item in real_tools if item.get("status") == "pass"]
    pending_tools = [item for item in real_tools if item.get("status") == "not_run"]
    promoted = [item for item in state.get("transitions", []) if item.get("status") == "promoted"]
    failed_invariants = [item for item in state.get("invariants", []) if item.get("status") == "fail"]
    selected_tool_blockers = backend_tool_blockers(tool_results, tool_selection_blockers)
    upstream_hierarchy_gate = upstream_hierarchy_gate or {}
    upstream_blockers = [
        f"upstream hierarchical verification blocker: {value}"
        for value in upstream_hierarchy_gate.get("blockers", [])
    ] if upstream_hierarchy_gate.get("status") != "pass" else []
    passed_tool_names = {str(item.get("checker", "")).removeprefix("real_tool.") for item in passed_tools}
    final_required_tools = [
        "case_board_shell_wrapper_generate",
        "case_compute_slot_adapter_generate",
        "app_shell_target_discovery_contract",
        "app_shell_target_hint_synthesis",
        "app_shell_target_discovery_after_hint",
        "app_shell_runtime_bitstream",
        "case_runtime_abi_check",
        "case_stage7_metrics",
    ]
    implementation_required_tools = [
        "app_shell_runtime_bitstream",
        "case_stage7_metrics",
    ]
    missing_final_tools = [name for name in final_required_tools if name not in passed_tool_names]
    missing_implementation_tools = [
        name for name in implementation_required_tools if name not in passed_tool_names
    ]
    board_bringup_ready = upstream_hierarchy_gate.get("board_bringup_ready") is True
    implementation_closure_blockers = [
        *(["current Stage7 board bring-up readiness is not established"] if not board_bringup_ready else []),
        *[f"implementation evidence missing: {name}" for name in missing_implementation_tools],
    ]
    implementation_closure = {
        "status": "pass" if not implementation_closure_blockers else "pending",
        "required_upstream": "artifact.stage6.board_bringup_certificate",
        "board_bringup_ready": board_bringup_ready,
        "required_tools": implementation_required_tools,
        "missing_tools": missing_implementation_tools,
        "blockers": implementation_closure_blockers,
        "acceptance": [
            "real runtime and full weight loading completed",
            "real Layer-3 board VCS compile and startup completed without syntax failure",
            "Vivado synthesis completed",
            "Vivado implementation completed",
            "Vivado synthesis/implementation reports are readable",
        ],
        "does_not_require": [
            "complete token output",
            "final DDR writeback",
            "bitstream generation",
            "physical-board runtime",
        ],
    }
    stage7_metrics_result = next(
        (
            item.get("tool_report_digest", {})
            for item in real_tools
            if item.get("checker") == "real_tool.case_stage7_metrics"
        ),
        {},
    )
    dse_measurement = dse_measurement or {}
    dse_campaign = dse_campaign or {}
    qor_optimization = classify_qor_optimization(
        state,
        stage7_metrics_result,
        campaign=dse_campaign,
        measurement=dse_measurement,
    )
    blockers = [
        f"pending real tool: {item['checker']}"
        for item in pending_tools
    ] + [
        f"failed real tool: {item['checker']}"
        for item in failed_tools
    ] + [
        f"final backend/board evidence missing: {name}"
        for name in missing_final_tools
    ] + upstream_blockers + selected_tool_blockers + artifacts.get("target_model_artifact_status", {}).get("missing_for_target", [])
    if qor_optimization.get("decision") == "llm_required":
        blockers.append("exact QoR miss requires an LLM routing decision before Stage4/Stage5 backtrack")
    return {
        "schema_version": "spatialaccagent.backend_board_plan.v0",
        "stage": "backend_board",
        "status": "planned",
        "execution_scope": backend_execution_scope(),
        "board": resolved_board,
        "shell": resolved_shell,
        "memory_system": resolved_memory,
        "runtime_interface": resolved_runtime,
        "resolved_board_profile": {
            "path": resolved_board_profile.get("path") if isinstance(resolved_board_profile, dict) else None,
            "filled_fields": resolved_profile.get("_stage7_resolution", {}).get("filled_fields", []),
            "policy": resolved_profile.get("_stage7_resolution", {}).get("policy"),
        },
        "design_closure_metrics": {
            "nodes": len(state.get("nodes", [])),
            "edges": len(state.get("edges", [])),
            "constraints": len(state.get("constraints", [])),
            "artifacts": len(state.get("artifacts", [])),
            "evidence": len(state.get("evidence", [])),
            "transitions": len(state.get("transitions", [])),
            "promoted_transitions": len(promoted),
            "failed_invariants": len(failed_invariants),
            "pending_real_tool_evidence": len(pending),
            "pending_real_tools": len(pending_tools),
            "failed_real_tools": len(failed_tools),
            "passed_real_tools": len(passed_tools),
        },
        "real_tool_status": {
            "passed": [item["checker"] for item in passed_tools],
            "pending": [item["checker"] for item in pending_tools],
            "failed": [item["checker"] for item in failed_tools],
            "backend_selected": tool_results,
            "backend_tool_selection_blockers": tool_selection_blockers,
            "backend_selected_tool_blockers": selected_tool_blockers,
            "final_required_tools": final_required_tools,
            "missing_final_tools": missing_final_tools,
            "upstream_hierarchy_gate": upstream_hierarchy_gate,
        },
        "upstream_hierarchy_gate": upstream_hierarchy_gate,
        "implementation_closure": implementation_closure,
        "qor": stage7_metrics_result,
        "dse_measurement": dse_measurement,
        "dse_campaign": dse_campaign,
        "qor_optimization": qor_optimization,
        "target_model_artifact_status": artifacts.get("target_model_artifact_status", {}),
        "final_design_pass": not blockers and not failed_invariants,
        "final_design_pass_blockers": blockers,
        "qor_outputs": [
            "resources",
            "power_w",
            "clock_frequency_mhz",
            "performance_tokens_per_second",
        ],
        "pass_criteria": resolved_pass_criteria,
        "generated_code_package": artifacts.get("generated_package_root"),
        "note": "This stage records backend/board closure requirements and evidence gaps; it does not claim final hardware pass.",
    }


def update_sacg(
    source_state: Path,
    target_state: Path,
    plan_path: Path,
    plan: dict[str, Any],
    tool_results: list[dict[str, Any]],
    scope_is_pass: bool,
) -> str:
    state = copy_state(source_state, target_state)
    add_constraint(
        state,
        "constraint.backend_board.plan",
        "backend",
        ["node.target_board"],
        [],
        ["artifact.stage7.backend_board_plan"],
        {"qor_outputs": plan["qor_outputs"], "pass_criteria": plan["pass_criteria"]},
    )
    add_constraint(
        state,
        "constraint.backend.package",
        "backend",
        ["node.target_board"],
        [],
        [
            "artifact.stage7.backend_board_plan",
            "artifact.stage7.backend_package",
            "artifact.stage7.board_shell_contract",
            "artifact.stage7.board_shell_wrapper_rtl",
            "artifact.stage7.board_shell_wrapper_manifest",
            "artifact.stage7.app_shell_integration_contract",
            "artifact.stage7.app_shell_target_selection_decision",
            "artifact.stage7.backend_bounded_recovery_actions",
        ],
        {
            "backend_package": plan.get("backend_package", {}),
            "qor_outputs": plan["qor_outputs"],
            "real_tool_status": plan.get("real_tool_status", {}),
            "board_shell_contract": plan.get("backend_package", {}).get("board_shell_contract"),
            "board_shell_wrapper_rtl": plan.get("backend_package", {}).get("board_shell_wrapper_rtl"),
            "app_shell_integration_contract": plan.get("backend_package", {}).get("app_shell_integration_contract"),
            "bounded_recovery_actions": plan.get("bounded_recovery_actions", {}),
        },
    )
    add_constraint(
        state,
        "constraint.backend.real_tool_evidence",
        "backend",
        ["node.target_board"],
        [],
        ["artifact.stage7.backend_board_plan", "artifact.stage7.backend_real_tool_results"],
        {
            "execution_scope": plan.get("execution_scope"),
            "real_tool_status": plan.get("real_tool_status", {}),
            "rule": "Backend and board claims require executed tool evidence; scoped backend passes do not imply final board pass.",
        },
    )
    add_constraint(
        state,
        BACKEND_RECOVERY_CONSTRAINT,
        "backend",
        ["node.target_board"],
        [],
        ["artifact.stage7.backend_bounded_recovery_actions"],
        {
            "bounded_recovery_actions": plan.get("bounded_recovery_actions", {}),
            "rule": "When backend/app-shell closure needs repair, Stage 7 must emit an LLM-derived bounded recovery action before the next tool attempt.",
        },
    )
    add_constraint(
        state,
        APP_SHELL_INTEGRATION_CONSTRAINT,
        "backend",
        ["node.target_board"],
        [],
        [
            "artifact.stage7.app_shell_integration_contract",
            "artifact.stage7.app_shell_target_selection_decision",
            "artifact.stage7.board_shell_contract",
        ],
        {
            "app_shell_integration_contract": plan.get("backend_package", {}).get("app_shell_integration_contract"),
            "app_shell_target_selection_decision": plan.get("backend_package", {}).get("app_shell_target_selection_decision"),
            "rule": "If standalone board-shell Vivado exposes board AXI as top-level FPGA pins or fails board IO DRC, Stage 7 must move to existing shell internal integration rather than demoting DRC.",
        },
    )
    resolved_profile_info = plan.get("resolved_board_profile", {}) if isinstance(plan.get("resolved_board_profile"), dict) else {}
    resolved_profile_path = str(resolved_profile_info.get("path") or "")
    add_constraint(
        state,
        RESOLVED_BOARD_CONSTRAINT,
        "backend",
        ["node.target_board"],
        [],
        ["artifact.stage7.resolved_target_board_profile"],
        {
            "resolved_board_profile": resolved_profile_info,
            "rule": "Backend tools consume a board profile resolved from current-run source evidence; blank fields may be filled, but board facts must not be invented.",
        },
    )
    add_invariant(
        state,
        "invariant.backend_resolved_board_profile_check",
        "backend_resolved_board_profile_check",
        [RESOLVED_BOARD_CONSTRAINT],
    )
    execution_scope = str(plan.get("execution_scope") or backend_execution_scope())
    scoped_constraint = f"constraint.backend.scope.{safe_id(execution_scope)}"
    scoped_constraints = (
        [RESOLVED_BOARD_CONSTRAINT, scoped_constraint]
        if execution_scope not in {"all", "*", "backend_board", "final"}
        else [*TOUCHED_CONSTRAINTS, RESOLVED_BOARD_CONSTRAINT]
    )
    add_constraint(
        state,
        scoped_constraint,
        "backend",
        ["node.target_board"],
        [],
        [
            "artifact.stage7.backend_board_plan",
            "artifact.stage7.backend_package",
            "artifact.stage7.backend_real_tool_results",
            "artifact.stage7.app_shell_integration_contract",
            "artifact.stage7.app_shell_target_selection_decision",
            "artifact.stage7.backend_bounded_recovery_actions",
        ],
        {
            "execution_scope": execution_scope,
            "scope_pass": scope_is_pass,
            "rule": "Scoped backend evidence records partial closure progress and does not imply final board pass.",
        },
    )
    write_json(target_state, state)

    store = SACGStore(target_state)

    def require_transition_checker(checker: str) -> None:
        required = transition.setdefault("required_checkers", [])
        if checker not in required:
            required.append(checker)
            required.sort()

    transition = store.declare_transition(
        action_type="backend_board",
        touched_nodes=["node.target_board"],
        touched_edges=[],
        touched_constraints=scoped_constraints,
        note=f"Ran backend and board closure stage for scope={execution_scope}.",
    )
    store.bind_artifact(
        "artifact.stage7.resolved_target_board_profile",
        resolved_profile_path,
        "stage.resolved_target_board_profile",
        ["node.target_board"],
        [],
        [RESOLVED_BOARD_CONSTRAINT],
        transition["id"],
    )
    store.bind_artifact(
        "artifact.stage7.backend_board_plan",
        str(plan_path),
        "stage.backend_board_plan",
        ["node.target_board"],
        [],
        scoped_constraints,
        transition["id"],
    )
    store.bind_artifact(
        "artifact.stage7.backend_package",
        str(plan.get("backend_package", {}).get("root", "")),
        "stage.backend_package",
        ["node.target_board"],
        [],
        scoped_constraints,
        transition["id"],
    )
    board_shell_contract_path = str(plan.get("backend_package", {}).get("board_shell_contract", ""))
    store.bind_artifact(
        "artifact.stage7.board_shell_contract",
        board_shell_contract_path,
        "stage.board_shell_contract",
        ["node.target_board"],
        [],
        scoped_constraints,
        transition["id"],
    )
    board_shell_wrapper_rtl = str(plan.get("backend_package", {}).get("board_shell_wrapper_rtl", ""))
    board_shell_wrapper_manifest = str(plan.get("backend_package", {}).get("board_shell_wrapper_manifest", ""))
    store.bind_artifact(
        "artifact.stage7.board_shell_wrapper_rtl",
        board_shell_wrapper_rtl,
        "stage.board_shell_wrapper_rtl",
        ["node.target_board"],
        [],
        scoped_constraints,
        transition["id"],
    )
    store.bind_artifact(
        "artifact.stage7.board_shell_wrapper_manifest",
        board_shell_wrapper_manifest,
        "stage.board_shell_wrapper_manifest",
        ["node.target_board"],
        [],
        scoped_constraints,
        transition["id"],
    )
    app_shell_integration_contract = str(plan.get("backend_package", {}).get("app_shell_integration_contract", ""))
    store.bind_artifact(
        "artifact.stage7.app_shell_integration_contract",
        app_shell_integration_contract,
        "stage.app_shell_integration_contract",
        ["node.target_board"],
        [],
        [APP_SHELL_INTEGRATION_CONSTRAINT],
        transition["id"],
    )
    app_shell_target_selection_decision = str(plan.get("backend_package", {}).get("app_shell_target_selection_decision", ""))
    store.bind_artifact(
        "artifact.stage7.app_shell_target_selection_decision",
        app_shell_target_selection_decision,
        "stage.app_shell_target_selection_decision",
        ["node.target_board"],
        [],
        [APP_SHELL_INTEGRATION_CONSTRAINT],
        transition["id"],
    )
    bounded_recovery_actions = str(plan.get("bounded_recovery_actions", {}).get("path", ""))
    store.bind_artifact(
        "artifact.stage7.backend_bounded_recovery_actions",
        bounded_recovery_actions,
        "stage.backend_bounded_recovery_actions",
        ["node.target_board"],
        [],
        [BACKEND_RECOVERY_CONSTRAINT],
        transition["id"],
    )
    tool_log_dir = plan_path.parent / "real_tools"
    tool_log_dir.mkdir(parents=True, exist_ok=True)
    store.bind_artifact(
        "artifact.stage7.backend_real_tool_results",
        str(tool_log_dir),
        "stage.backend_real_tool_results",
        ["node.target_board"],
        [],
        scoped_constraints,
        transition["id"],
    )
    add_invariant(
        store.state,
        "invariant.backend_board_plan_static",
        "backend_board_plan_static_check",
        scoped_constraints,
    )
    add_invariant(
        store.state,
        "invariant.backend_package_static",
        "backend_package_static_check",
        scoped_constraints,
    )
    add_invariant(
        store.state,
        "invariant.backend_board_shell_contract_static",
        "backend_board_shell_contract_static_check",
        scoped_constraints,
    )
    add_invariant(
        store.state,
        "invariant.backend_board_shell_wrapper_static",
        "backend_board_shell_wrapper_static_check",
        scoped_constraints,
    )
    add_invariant(
        store.state,
        "invariant.backend_app_shell_integration_contract_static",
        "backend_app_shell_integration_contract_static_check",
        [APP_SHELL_INTEGRATION_CONSTRAINT],
    )
    add_invariant(
        store.state,
        "invariant.backend_app_shell_target_hint_synthesis",
        "backend_app_shell_target_hint_synthesis_check",
        [APP_SHELL_INTEGRATION_CONSTRAINT],
    )
    add_invariant(
        store.state,
        "invariant.backend_bounded_recovery_action_check",
        "backend_bounded_recovery_action_check",
        [BACKEND_RECOVERY_CONSTRAINT],
    )
    add_invariant(
        store.state,
        "invariant.backend_real_tool_evidence_check",
        "backend_real_tool_evidence_check",
        scoped_constraints,
    )
    add_invariant(
        store.state,
        "invariant.backend_upstream_hierarchy_check",
        "backend_upstream_hierarchy_check",
        scoped_constraints,
    )
    add_invariant(
        store.state,
        "invariant.backend_team_llm_check",
        "backend_team_llm_check",
        scoped_constraints,
    )
    add_invariant(
        store.state,
        "invariant.backend_closure_llm_check",
        "backend_closure_llm_check",
        scoped_constraints,
    )
    for checker in [
        "backend_board_plan_static_check",
        "backend_board_shell_contract_static_check",
        "backend_board_shell_wrapper_static_check",
        "backend_app_shell_integration_contract_static_check",
        "backend_app_shell_target_hint_synthesis_check",
        "backend_bounded_recovery_action_check",
        "backend_package_static_check",
        "backend_real_tool_evidence_check",
        "backend_resolved_board_profile_check",
        "backend_upstream_hierarchy_check",
        "backend_team_llm_check",
        "backend_closure_llm_check",
    ]:
        require_transition_checker(checker)
    resolved_path = Path(resolved_profile_path)
    store.attach_evidence(
        checker="backend_resolved_board_profile_check",
        status="pass" if resolved_path.exists() else "fail",
        invariant="invariant.backend_resolved_board_profile_check",
        constraints=[RESOLVED_BOARD_CONSTRAINT],
        artifacts=["artifact.stage7.resolved_target_board_profile"],
        log_path=resolved_profile_path or str(plan_path),
        transition_id=transition["id"],
        summary=f"resolved board profile path={resolved_profile_path} filled_fields={resolved_profile_info.get('filled_fields', [])}",
    )
    store.attach_evidence(
        checker="backend_board_plan_static_check",
        status="pass",
        invariant="invariant.backend_board_plan_static",
        constraints=scoped_constraints,
        artifacts=["artifact.stage7.backend_board_plan"],
        log_path=str(plan_path),
        transition_id=transition["id"],
        summary="backend board plan artifact generated",
    )
    package_root = Path(str(plan.get("backend_package", {}).get("root", "")))
    store.attach_evidence(
        checker="backend_package_static_check",
        status="pass" if package_root.exists() else "fail",
        invariant="invariant.backend_package_static",
        constraints=scoped_constraints,
        artifacts=["artifact.stage7.backend_package"],
        log_path=str(plan_path),
        transition_id=transition["id"],
        summary=f"backend package root={package_root}",
    )
    contract_path = Path(board_shell_contract_path)
    contract = read_json(contract_path) if board_shell_contract_path and contract_path.is_file() else {}
    store.attach_evidence(
        checker="backend_board_shell_contract_static_check",
        status="pass" if contract_path.is_file() and contract.get("status") == "ready_for_generation" else "fail",
        invariant="invariant.backend_board_shell_contract_static",
        constraints=scoped_constraints,
        artifacts=["artifact.stage7.board_shell_contract"],
        log_path=board_shell_contract_path or str(plan_path),
        transition_id=transition["id"],
        summary=f"board shell contract status={contract.get('status')} missing_fields={contract.get('missing_fields', [])}",
    )
    wrapper_manifest_path = Path(board_shell_wrapper_manifest)
    wrapper_manifest = read_json(wrapper_manifest_path) if board_shell_wrapper_manifest and wrapper_manifest_path.is_file() else {}
    wrapper_rtl_path = Path(board_shell_wrapper_rtl)
    store.attach_evidence(
        checker="backend_board_shell_wrapper_static_check",
        status="pass" if wrapper_rtl_path.is_file() and wrapper_manifest.get("status") == "pass" else "fail",
        invariant="invariant.backend_board_shell_wrapper_static",
        constraints=scoped_constraints,
        artifacts=["artifact.stage7.board_shell_wrapper_rtl", "artifact.stage7.board_shell_wrapper_manifest"],
        log_path=board_shell_wrapper_manifest or str(plan_path),
        transition_id=transition["id"],
        summary=f"board shell wrapper manifest status={wrapper_manifest.get('status')} rtl_exists={wrapper_rtl_path.is_file()}",
    )
    app_shell_contract_path = Path(app_shell_integration_contract)
    app_shell_contract = read_json(app_shell_contract_path) if app_shell_integration_contract and app_shell_contract_path.is_file() else {}
    app_shell_ready_statuses = {"ready_for_app_shell_generation", "ready_for_generation"}
    store.attach_evidence(
        checker="backend_app_shell_integration_contract_static_check",
        status="pass" if app_shell_contract_path.is_file() and app_shell_contract.get("status") in app_shell_ready_statuses else "fail",
        invariant="invariant.backend_app_shell_integration_contract_static",
        constraints=[APP_SHELL_INTEGRATION_CONSTRAINT],
        artifacts=["artifact.stage7.app_shell_integration_contract"],
        log_path=app_shell_integration_contract or str(plan_path),
        transition_id=transition["id"],
        summary=(
            f"app shell integration contract status={app_shell_contract.get('status')} "
            f"missing_fields={app_shell_contract.get('missing_fields', [])}"
        ),
    )
    decision_path = Path(app_shell_target_selection_decision)
    decision = read_json(decision_path) if app_shell_target_selection_decision and decision_path.is_file() else {}
    decision_kind = str(decision.get("decision") or "")
    store.attach_evidence(
        checker="backend_app_shell_target_hint_synthesis_check",
        status="pass" if decision_path.is_file() and decision_kind in {"approved_target", "approved_policy_hints", "defer"} else "fail",
        invariant="invariant.backend_app_shell_target_hint_synthesis",
        constraints=[APP_SHELL_INTEGRATION_CONSTRAINT],
        artifacts=["artifact.stage7.app_shell_target_selection_decision"],
        log_path=app_shell_target_selection_decision or str(plan_path),
        transition_id=transition["id"],
        summary=f"target selection decision={decision_kind or '<missing>'} path={app_shell_target_selection_decision}",
    )
    recovery_path = Path(bounded_recovery_actions)
    recovery_report = read_json(recovery_path) if bounded_recovery_actions and recovery_path.is_file() else {}
    store.attach_evidence(
        checker="backend_bounded_recovery_action_check",
        status="pass" if recovery_path.is_file() and recovery_report.get("status") == "pass" else "fail",
        invariant="invariant.backend_bounded_recovery_action_check",
        constraints=[BACKEND_RECOVERY_CONSTRAINT],
        artifacts=["artifact.stage7.backend_bounded_recovery_actions"],
        log_path=bounded_recovery_actions or str(plan_path),
        transition_id=transition["id"],
        summary=f"bounded recovery status={recovery_report.get('status')} decision={recovery_report.get('decision')}",
    )
    store.attach_evidence(
        checker="backend_real_tool_evidence_check",
        status="pass" if scope_is_pass else "fail",
        invariant="invariant.backend_real_tool_evidence_check",
        constraints=scoped_constraints,
        artifacts=["artifact.stage7.backend_board_plan"],
        log_path=str(plan_path),
        transition_id=transition["id"],
        summary=f"backend execution scope={plan.get('execution_scope')} scope_pass={scope_is_pass}",
    )
    upstream_gate = plan.get("upstream_hierarchy_gate", {}) if isinstance(plan.get("upstream_hierarchy_gate"), dict) else {}
    store.attach_evidence(
        checker="backend_upstream_hierarchy_check",
        status="pass" if upstream_gate.get("status") == "pass" else "fail",
        invariant="invariant.backend_upstream_hierarchy_check",
        constraints=scoped_constraints,
        artifacts=["artifact.stage7.backend_board_plan"],
        log_path=str(plan_path),
        transition_id=transition["id"],
        summary="Stage7 hierarchical maturity is backend-ready" if upstream_gate.get("status") == "pass" else "; ".join(str(item) for item in upstream_gate.get("blockers", [])[:8]),
    )
    agent_gate_status = plan.get("agent_gate_status", {}) if isinstance(plan.get("agent_gate_status"), dict) else {}
    for item in agent_gate_status.get("checks", []):
        checker = str(item.get("checker") or "")
        if checker not in {"backend_team_llm_check", "backend_closure_llm_check", "backend_bounded_recovery_action_check"}:
            continue
        invariant_id = f"invariant.{checker}"
        status = str(item.get("status") or "fail")
        store.attach_evidence(
            checker=checker,
            status=status if status in {"pass", "fail"} else "fail",
            invariant=invariant_id,
            constraints=scoped_constraints,
            artifacts=["artifact.stage7.backend_board_plan"],
            log_path=str(plan_path),
            transition_id=transition["id"],
            summary=str(item.get("summary") or ""),
        )
    for item in tool_results:
        checker = str(item.get("checker") or "")
        if not checker:
            continue
        invariant_id = f"invariant.{checker}"
        add_invariant(store.state, invariant_id, checker, scoped_constraints)
        require_transition_checker(checker)
        status = str(item.get("status") or "unknown")
        evidence_status = status if status in {"pass", "fail"} else "unknown"
        store.attach_evidence(
            checker=checker,
            status=evidence_status,
            invariant=invariant_id,
            constraints=scoped_constraints,
            artifacts=["artifact.stage7.backend_board_plan"],
            log_path=str(item.get("log_path") or plan_path),
            transition_id=transition["id"],
            summary=str(item.get("summary") or ""),
        )
    attached_checkers = {
        evidence.get("checker")
        for evidence in store.state.get("evidence", [])
        if evidence.get("id") in transition.get("evidence", [])
        and evidence.get("status") == "pass"
    }
    for checker in transition.get("required_checkers", []):
        if checker in attached_checkers:
            continue
        invariant = next(
            (
                item for item in store.state.get("invariants", [])
                if item.get("checker") == checker and item.get("status") == "pass"
            ),
            None,
        )
        if not invariant:
            continue
        latest = next(
            (
                item for item in store.state.get("evidence", [])
                if item.get("id") == invariant.get("latest_evidence")
            ),
            {},
        )
        store.attach_evidence(
            checker=checker,
            status="pass",
            invariant=str(invariant["id"]),
            constraints=list(invariant.get("constraints") or []),
            artifacts=["artifact.stage7.backend_board_plan"],
            log_path=str(latest.get("log_path") or plan_path),
            transition_id=transition["id"],
            summary=f"carried forward existing pass evidence: {latest.get('summary', '')}",
        )
    if scope_is_pass:
        store.promote(transition["id"])
    else:
        store.reject(transition["id"], "backend/board execution scope did not pass")
        blockers = list(plan.get("final_design_pass_blockers", [])[:8])
        blockers.extend(
            f"{item.get('checker')}: {item.get('summary')}"
            for item in tool_results
            if item.get("status") == "fail"
        )
        store.record_failure_lesson(
            stage="stage7.backend_board",
            failure_class="backend_board_gate",
            summary="; ".join(blockers[:8]) or "Stage-7 backend/board execution scope did not pass",
            violated_constraints=scoped_constraints,
            artifacts=[
                "artifact.stage7.backend_board_plan",
                "artifact.stage7.app_shell_integration_contract",
                "artifact.stage7.backend_bounded_recovery_actions",
            ],
            recommended_action="Consume backend_bounded_recovery_actions, resolve required design-team/tool evidence gaps, then rerun Stage 7 without claiming board pass.",
            retry_scope="stage7_or_human_boundary",
        )
        store.record_retry_request(
            stage="stage7.backend_board",
            reason="Backend/board real-tool scope did not pass",
            target_stage="stage7.backend_board",
            required_inputs=["artifact.stage7.backend_bounded_recovery_actions", "artifact.stage7.app_shell_integration_contract"],
            blocked_artifacts=["artifact.stage7.backend_board_plan", "artifact.stage7.backend_real_tool_results"],
        )
        recovery = plan.get("bounded_recovery_actions", {}) if isinstance(plan.get("bounded_recovery_actions"), dict) else {}
        if recovery.get("next_stage"):
            store.record_backtrack_request(
                stage="stage7.backend_board",
                target_stage=str(recovery.get("next_stage")),
                reason=str(recovery.get("summary") or "Stage 7 requires bounded recovery before the next backend/board attempt"),
                missing_or_invalid_contracts=plan.get("final_design_pass_blockers", [])[:8],
                evidence=["artifact.stage7.backend_bounded_recovery_actions", "artifact.stage7.backend_real_tool_results"],
            )
        upstream_gate = plan.get("upstream_hierarchy_gate", {}) if isinstance(plan.get("upstream_hierarchy_gate"), dict) else {}
        if upstream_gate.get("status") == "fail":
            store.record_backtrack_request(
                stage="stage7.backend_board",
                target_stage="stage6.verification",
                reason="Stage-7 backend tools require hierarchical verification maturity before backend execution",
                missing_or_invalid_contracts=[str(value) for value in upstream_gate.get("blockers", [])[:12]],
                evidence=["artifact.stage6.verification_result", "artifact.stage7.backend_board_plan"],
            )
    qor_optimization = plan.get("qor_optimization", {}) if isinstance(plan.get("qor_optimization"), dict) else {}
    if qor_optimization.get("decision") in {"local_optimization", "dse_backtrack"}:
        store.record_backtrack_request(
            stage="stage7.vivado_implementation_and_qor",
            target_stage=str(qor_optimization.get("next_stage")),
            reason=str(qor_optimization.get("reason")),
            missing_or_invalid_contracts=[str(item.get("metric")) for item in qor_optimization.get("misses", []) if isinstance(item, dict)],
            evidence=["artifact.stage7.backend_real_tool_results"],
            context={
                "verification_scope": "formal_dse_campaign"
                if qor_optimization.get("decision") == "dse_backtrack"
                else "local_qor_optimization",
            },
        )
    store.record_stage_outcome(
        stage="stage7.backend_board",
        status="scope_ready" if scope_is_pass else "incomplete",
        transition_id=transition["id"],
        summary=f"execution_scope={execution_scope} scope_pass={scope_is_pass}",
        errors=plan.get("final_design_pass_blockers", [])[:16],
        artifacts=[
            "artifact.stage7.backend_board_plan",
            "artifact.stage7.app_shell_integration_contract",
            "artifact.stage7.backend_bounded_recovery_actions",
        ],
        next_actions=[] if scope_is_pass else [str((plan.get("bounded_recovery_actions") or {}).get("next_stage") or "rerun stage7.backend_board after resolving blockers")],
        retryable=not scope_is_pass,
    )
    store.save()
    return transition["id"]


def plan_backend_board(args: argparse.Namespace) -> tuple[Path, dict[str, Any]]:
    source_state = args.sacg_state.resolve()
    run_dir = run_dir_from_state(source_state)
    out_dir = run_dir / "backend_board"
    plan_path = out_dir / "backend_board_plan.json"
    state_path = out_dir / "sacg_state.json"
    report_path = out_dir / "backend_board_report.json"

    source_data = read_json(source_state)
    resolved_board_profile = resolve_board_profile(source_data, run_dir, out_dir)
    write_board_shell_contract(run_dir, source_data, resolved_board_profile)
    write_initial_app_shell_integration_contract(run_dir, source_data, resolved_board_profile)
    upstream_hierarchy_gate = check_upstream_hierarchical_verification_closure(source_data)
    dse_measurement = {"status": "not_recorded", "reason": "Stage7 implementation has not run"}
    if upstream_hierarchy_gate.get("status") == "pass":
        tool_results, tool_selection_blockers = run_backend_real_tools(
            source_data,
            run_dir,
            out_dir,
            Path(str(resolved_board_profile.get("path"))),
            board_shell_wrapper_rtl_path(run_dir),
        )
        if any(item.get("checker") == "real_tool.app_shell_runtime_bitstream" for item in tool_results):
            dse_measurement = record_exact_dse_measurement(source_data, run_dir)
    else:
        tool_results = []
        tool_selection_blockers = [
            "Stage-7 backend tools require Stage-6 hierarchical maturity before execution",
            *[str(value) for value in upstream_hierarchy_gate.get("blockers", [])],
        ]
    dse_campaign = exact_dse_campaign(source_data, run_dir)
    plan = build_plan(
        source_data,
        tool_results,
        tool_selection_blockers,
        resolved_board_profile,
        upstream_hierarchy_gate,
        dse_measurement,
        dse_campaign,
    )
    backend_package = generate_backend_package(run_dir, source_data, plan)
    plan["backend_package"] = backend_package
    plan["llm_decision_packet"] = backend_llm_decision_packet(plan)
    qor_router = None
    qor_router_error = None
    if plan.get("qor_optimization", {}).get("decision") == "llm_required":
        try:
            qor_router = run_stage_agent(
                agent="qor_router_agent",
                stage="backend_board",
                task=(
                    "Route the current exact four-metric QoR miss. Choose exactly one of "
                    "local_optimization or dse_backtrack. Do not estimate or invent QoR; "
                    "use only the supplied current app-shell Vivado and hardware-counter evidence."
                ),
                inputs={
                    "backend_qor_decision_packet": backend_qor_decision_packet(plan),
                    "source_sacg_state": str(source_state),
                },
                out_dir=out_dir / "qor_router",
                fallback_summary="Exact QoR routing requires an LLM decision.",
                output_schema=QOR_ROUTER_SCHEMA,
                prompt_rules=[
                    "Return one structured decision with qor_decision=local_optimization or dse_backtrack.",
                    "Do not use a ratio threshold or any framework heuristic to choose the route.",
                    "Use local_optimization only for a bounded RTL/implementation repair that preserves the Stage4 physical candidate.",
                    "Use dse_backtrack when a physical parameter, memory layout, lane count, FIFO depth, or other Stage4 candidate dimension must change.",
                    "The framework will execute only the selected legal route and will reject any decision unsupported by the current exact evidence.",
                ],
            )
            qor_output = qor_router.get("output", {}) if isinstance(qor_router, dict) else {}
            plan["qor_optimization"] = classify_qor_optimization(
                source_data,
                plan.get("qor", {}),
                campaign=plan.get("dse_campaign", {}),
                measurement=plan.get("dse_measurement", {}),
                llm_decision=qor_output if isinstance(qor_output, dict) else None,
            )
        except Exception as exc:
            qor_router_error = str(exc)
    if plan.get("qor_optimization", {}).get("decision") != "pass":
        plan["final_design_pass_blockers"] = [
            blocker
            for blocker in plan.get("final_design_pass_blockers", [])
            if not str(blocker).startswith("exact QoR miss requires an LLM routing decision")
            and not str(blocker).startswith("QoR routing requires")
        ]
        route = plan.get("qor_optimization", {}).get("decision")
        if route == "llm_required":
            plan["final_design_pass_blockers"].append(
                "exact QoR miss requires an LLM routing decision before Stage4/Stage5 backtrack"
            )
        elif route in {"local_optimization", "dse_backtrack"}:
            plan["final_design_pass_blockers"].append(
                f"QoR routing requires {route} before final design pass"
            )
        plan["final_design_pass"] = False
    plan["qor_router"] = {
        "result_path": qor_router.get("result_path") if isinstance(qor_router, dict) else None,
        "decision": plan.get("qor_optimization", {}).get("decision"),
        "error": qor_router_error,
    }
    write_json(plan_path, plan)
    team_error = None
    try:
        team = run_design_team(
            stage="backend_board",
            objective="Prepare and audit backend, timing, bitstream, board runtime, and evidence-gate handoff for final design closure.",
            state=source_data,
            candidate_artifact=plan,
            out_dir=out_dir,
        )
        design_team_summary = team_summary(team)
        team_paths = {
            "team_subtask_plan": team["subtask_plan_path"],
            "team_aggregate": team["aggregate_path"],
        }
    except Exception as exc:
        team_error = str(exc)
        design_team_summary = {
            "status": "unavailable",
            "errors": [team_error],
            "subtask_count": 0,
            "completed_subtasks": 0,
        }
        team_paths = {"team_subtask_plan": None, "team_aggregate": None}

    llm_error = None
    try:
        llm = run_stage_agent(
            agent="backend_closure_agent",
            stage="backend_board",
            task="Review backend and board closure blockers, generated backend package, and team decomposition before final SACG validation.",
            inputs={
                "backend_closure_decision_packet": plan.get("llm_decision_packet"),
                "backend_board_plan_path": str(plan_path),
                "design_team": design_team_summary,
                "source_sacg_state": str(source_state),
            },
            out_dir=out_dir,
            fallback_summary="Backend and board closure plan generated from SACG evidence.",
        )
    except Exception as exc:
        llm_error = str(exc)
        llm_path = out_dir / "llm" / "backend_closure_agent_result.json"
        llm_output = {
            "schema_version": "spatialaccagent.stage_worker_output.v0",
            "agent": "backend_closure_agent",
            "stage": "backend_board",
            "status": "llm_error",
            "summary": "LLM backend closure agent unavailable; Stage 7 must retry after the provider recovers.",
            "sacg_focus": {"nodes": ["node.target_board"], "edges": [], "constraints": TOUCHED_CONSTRAINTS, "artifacts": ["artifact.stage7.backend_board_plan"]},
            "observations": [f"LLM backend closure agent failed: {llm_error}"],
            "risks": ["LLM outage blocks backend promotion; deterministic backend tool logs alone are not an agentic board-closure decision."],
            "proposed_actions": ["Rerun Stage 7 with the configured LLM provider available, preserving the same backend/app-shell tool evidence."],
            "executable_actions": [],
            "approval_required_for": [],
        }
        llm = {
            "schema_version": "spatialaccagent.stage_worker_record.v0",
            "agent": "backend_closure_agent",
            "stage": "backend_board",
            "mode": "llm",
            "result_path": str(llm_path),
            "used_fallback": False,
            "error": llm_error,
            "output": llm_output,
        }
        write_json(llm_path, llm)

    recovery_path, recovery_report = generate_backend_bounded_recovery_actions(
        run_dir,
        out_dir,
        plan,
        design_team_summary,
        llm,
    )
    plan["bounded_recovery_actions"] = {
        "path": str(recovery_path),
        "status": recovery_report.get("status"),
        "summary": recovery_report.get("summary"),
        "decision": recovery_report.get("decision"),
        "next_stage": recovery_report.get("next_stage"),
        "actions": recovery_report.get("bounded_recovery_actions", []),
    }
    plan["llm_decision_packet"] = backend_llm_decision_packet(plan)
    write_json(plan_path, plan)

    scope = backend_execution_scope()
    selected_tool_blockers = backend_tool_blockers(tool_results, tool_selection_blockers)
    agent_gate_status = build_backend_agent_gate_status(design_team_summary, llm, recovery_report)
    plan["agent_gate_status"] = agent_gate_status
    plan["llm_decision_packet"] = backend_llm_decision_packet(plan)
    write_json(plan_path, plan)
    scope_is_pass = scope_passed(scope, tool_results, tool_selection_blockers) and agent_gate_status.get("status") == "pass"
    transition_id = update_sacg(source_state, state_path, plan_path, plan, tool_results, scope_is_pass)
    # A completed exact app-shell measurement is a successful Stage 7 action
    # even while the formal DSE campaign deliberately routes to another
    # candidate.  The flow controller consumes the explicit SACG backtrack
    # request; it must not mistake this normal campaign transition for a stage
    # failure and stop before Stage 4 can select the next measurement.
    report_status = "ready" if scope_is_pass else "incomplete"
    all_scope = scope in {"all", "*", "backend_board", "final"}
    report_errors = plan.get("final_design_pass_blockers", []) if all_scope else selected_tool_blockers
    report_errors = [*report_errors, *agent_gate_status.get("errors", [])]
    report = {
        "schema_version": "spatialaccagent.backend_board_report.v0",
        "stage": "backend_board",
        "status": report_status,
        "execution_scope": scope,
        "source_sacg_state": str(source_state),
        "outputs": {
            "backend_board_plan": str(plan_path),
            "backend_package": backend_package["root"],
            "resolved_target_board_profile": str(resolved_board_profile.get("path")),
            "sacg_state": str(state_path),
            "llm_agent": llm["result_path"],
            "bounded_recovery_actions": str(recovery_path),
            "real_tool_results": str(out_dir / "real_tools"),
            **team_paths,
        },
        "llm_agent": llm["output"],
        "llm_executable_actions": llm["output"].get("executable_actions", []),
        "llm_error": llm_error,
        "design_team": design_team_summary,
        "team_executable_actions": design_team_summary.get("executable_actions", []),
        "bounded_recovery_actions": recovery_report,
        "team_error": team_error,
        "agent_gate_status": agent_gate_status,
        "llm_decision_packet": plan.get("llm_decision_packet"),
        "qor_outputs": plan["qor_outputs"],
        "final_design_pass": plan.get("final_design_pass"),
        "final_design_pass_blockers": plan.get("final_design_pass_blockers", []),
        "qor": plan.get("qor", {}),
        "qor_optimization": plan.get("qor_optimization", {}),
        "qor_router": plan.get("qor_router", {}),
        "scope_pass": scope_is_pass,
        "scope_tool_blockers": selected_tool_blockers,
        "real_tool_results": tool_results,
        "backend_package_files": backend_package["files"],
        "sacg_transition_id": transition_id,
        "errors": report_errors,
    }
    write_json(report_path, report)
    return report_path, report


def main(argv: list[str] | None = None) -> int:
    return run_sacg_stage("Backend and board closure planning stage", plan_backend_board, argv)


if __name__ == "__main__":
    raise SystemExit(main())
