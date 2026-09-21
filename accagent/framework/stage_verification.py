"""Run lightweight framework-level verification checks."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import uuid
from pathlib import Path
from typing import Any

from accagent.framework.case_adapter import (
    adapter_tool,
    build_case_adapter,
    gate_name,
    generic_required_gate_names,
    refresh_builtin_case_adapter,
)
from accagent.framework.debug_closure import write_debug_closure_artifacts
from accagent.framework.numeric_policy import numeric_comparison
from accagent.framework.repair_loop import build_repair_loop_report
from accagent.framework.sacg_store import SACGStore, validate_references
from accagent.framework.sacg_utils import (
    add_constraint,
    add_invariant,
    artifact_path,
    copy_state,
    hierarchy_memory_context,
    read_json,
    require_promoted_artifacts,
    run_dir_from_state,
    safe_id,
    write_json,
)
from accagent.framework.stage_entry import run_sacg_stage
from accagent.framework.stage_llm import run_stage_agent
from accagent.framework.stage_team import run_design_team, team_failure_errors, team_summary
from accagent.framework.tool_runner import run_tools
from accagent.framework.verification_evidence_contract import (
    PROMOTION_CERTIFICATE_SCHEMA_VERSION,
    PROMOTION_EVIDENCE_BINDING_SCHEMA_VERSION,
    certificate_contract_errors,
    certificate_contract_fingerprint,
    evidence_contract_for_level,
    promotion_evidence_binding_fingerprint,
    semantic_evidence_report_errors,
    sha256_file,
    tool_environment_contract,
    tool_evidence_contract_errors,
)


TOUCHED_CONSTRAINTS = [
    "constraint.verification.plan",
    "constraint.verification.hierarchy",
    "constraint.tool.protocols",
    "constraint.deployment.board",
]

SINGLE_LAYER_TOUCHED_CONSTRAINTS = [
    "constraint.verification.plan",
    "constraint.verification.hierarchy",
    "constraint.tool.protocols",
]

STAGE6_RECONCILED_ARTIFACTS = [
    "artifact.stage6.verification_result",
    "artifact.stage6.real_tool_results",
    "artifact.stage6.debug_closure",
    "artifact.stage6.operator_leaf_promotion_certificate",
    "artifact.stage6.single_layer_promotion_certificate",
    "artifact.stage6.multilayer_pipeline_promotion_certificate",
    "artifact.stage6.board_axi_ddr_promotion_certificate",
    "artifact.stage6.board_bringup_certificate",
    "artifact.stage6.repair_plan",
    "artifact.stage6.repair_execution_report",
]

BOARD_AXI_DDR_CLOSURE_SCOPES = {
    "board_axi_ddr",
    "board_axi_ddr_closure",
    "stage6_board_axi_ddr",
    "functional",
    "functional_sim",
    "stage6_functional",
}

SELECTOR_CERTIFICATE_LEVELS = {
    "operator_leaf_promotion_certificate": "operator_leaf_functional",
    "single_layer_promotion_certificate": "single_layer_functional",
    "multilayer_promotion_certificate": "multilayer_pipeline_functional",
    "board_axi_ddr_promotion_certificate": "axi_ddr_functional",
}

SELECTOR_CERTIFICATE_SCOPES = {
    "operator_leaf_promotion_certificate": "operator_leaf_closure",
    "single_layer_promotion_certificate": "single_layer_closure",
    "multilayer_promotion_certificate": "multilayer_closure",
    "board_axi_ddr_promotion_certificate": "board_axi_ddr_closure",
}

STABLE_PROMOTION_CERTIFICATE_NAMES = {
    "artifact.stage6.operator_leaf_promotion_certificate": "operator_leaf_promotion_certificate.json",
    "artifact.stage6.single_layer_promotion_certificate": "single_layer_promotion_certificate.json",
    "artifact.stage6.multilayer_pipeline_promotion_certificate": "multilayer_pipeline_promotion_certificate.json",
    "artifact.stage6.board_axi_ddr_promotion_certificate": "board_axi_ddr_promotion_certificate.json",
}

BOARD_BRINGUP_CERTIFICATE_SCHEMA_VERSION = "spatialaccagent.stage6_board_bringup_certificate.v1"


def empty(value: Any) -> bool:
    return value is None or value == "" or value == []


def case_adapter_for_state(state: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    tool_materials_dir = Path.cwd() / "accagent" / "framework" / "input_materials" / "tools"
    try:
        adapter = read_json(artifact_path(state, "artifact.input.case_adapter"))
        try:
            model = read_json(artifact_path(state, "artifact.input.model_config"))
        except Exception:
            model = {}
        return refresh_builtin_case_adapter(adapter, model, run_dir, tool_materials_dir)
    except Exception:
        try:
            model = read_json(artifact_path(state, "artifact.input.model_config"))
        except Exception:
            model = {}
        return build_case_adapter(model, run_dir, tool_materials_dir)


def resolve_case_path(run_dir: Path, value: Any) -> Path:
    path = Path(str(value))
    if path.is_absolute():
        return path
    repo_path = Path.cwd() / path
    if repo_path.exists():
        return repo_path
    return run_dir / path


def check_task_card(state: dict[str, Any]) -> tuple[str, str]:
    task = read_json(artifact_path(state, "artifact.input.task_card"))
    required = ["target_model", "target_seq_len", "design_goal"]
    missing = [name for name in required if empty(task.get(name))]
    if missing:
        return "fail", f"task_card missing {missing}"
    return "pass", f"target_model={task.get('target_model')}, seq={task.get('target_seq_len')}"


def check_model_config(state: dict[str, Any]) -> tuple[str, str]:
    model = read_json(artifact_path(state, "artifact.input.model_config"))
    sequence = model.get("block", {}).get("operator_sequence", [])
    attention = model.get("attention", {})
    missing = []
    for name in ["model_type", "num_layers", "hidden_size", "target_max_seq_len"]:
        if empty(model.get(name)):
            missing.append(name)
    for name in ["num_q_heads", "num_kv_heads", "head_dim"]:
        if empty(attention.get(name)):
            missing.append(f"attention.{name}")
    if not sequence:
        missing.append("block.operator_sequence")
    if missing:
        return "fail", f"model_config missing {missing}"
    return "pass", f"ops={len(sequence)}, hidden={model.get('hidden_size')}, heads={attention.get('num_q_heads')}"


def check_numeric_policy(state: dict[str, Any]) -> tuple[str, str]:
    policy = read_json(artifact_path(state, "artifact.input.numeric_policy"))
    rules = policy.get("default_rules", {})
    required = ["weight_dtype", "activation_dtype", "acc_dtype", "scale_dtype", "rounding", "saturation"]
    missing = [name for name in required if name not in rules]
    if missing:
        return "fail", f"numeric_policy.default_rules missing {missing}"
    comparison, resolution = numeric_comparison(policy)
    return (
        "pass",
        f"weight={rules.get('weight_dtype')}, activation={rules.get('activation_dtype')}, "
        f"acc={rules.get('acc_dtype')}, comparison={comparison}, "
        f"defaulted={resolution.get('defaulted_fields', [])}",
    )


def check_template_coverage(state: dict[str, Any]) -> tuple[str, str]:
    selection = read_json(artifact_path(state, "artifact.stage2.template_selection"))
    missing = selection.get("missing_ops", [])
    return ("fail", f"missing_ops={missing}") if missing else ("pass", "all model operators have selected templates")


def check_pipeline_plan(state: dict[str, Any]) -> tuple[str, str]:
    plan = read_json(artifact_path(state, "artifact.stage3.pipeline_plan"))
    stages = plan.get("stages", [])
    stream_edges = plan.get("stream_edges", [])
    data_edges = plan.get("data_edges", [])
    if not stages:
        return "fail", "pipeline has no stages"
    data_ids = [edge.get("edge_id") for edge in data_edges]
    stream_ids = [edge.get("edge_id") for edge in stream_edges]
    if data_ids != stream_ids:
        return "fail", "stream_edges must mirror data_edges including boundary, skip, branch, and join edges"
    endpoints = {(edge.get("src_stage"), edge.get("dst_stage")) for edge in stream_edges}
    if not any(src == "block_input" for src, _ in endpoints):
        return "fail", "pipeline stream graph has no block_input boundary edge"
    if not any(dst == "block_output" for _, dst in endpoints):
        return "fail", "pipeline stream graph has no block_output boundary edge"
    checker_summary = plan.get("checker_summary", {})
    if isinstance(checker_summary, dict) and checker_summary.get("errors"):
        return "fail", f"pipeline checker errors={checker_summary.get('errors')}"
    return "pass", f"stages={len(stages)}, stream_edges={len(stream_edges)}"


def check_parameter_binding(state: dict[str, Any]) -> tuple[str, str]:
    plan = read_json(artifact_path(state, "artifact.stage3.pipeline_plan"))
    bindings = read_json(artifact_path(state, "artifact.stage4.parameter_binding"))
    expected = {stage["stage_id"] for stage in plan.get("stages", [])}
    actual = {item["stage_id"] for item in bindings.get("bindings", [])}
    missing = sorted(expected - actual)
    if missing:
        return "fail", f"missing bindings for {missing}"
    return "pass", f"bindings={len(actual)}"


def check_code_generation_manifest(state: dict[str, Any]) -> tuple[str, str]:
    manifest = read_json(artifact_path(state, "artifact.stage5.design_artifact_manifest"))
    artifacts = manifest.get("planned_code_outputs") or manifest.get("planned_artifacts", [])
    generated_files = manifest.get("generated_files", [])
    package_root = manifest.get("generated_package_root")
    if not artifacts:
        return "fail", "no planned code outputs"
    if not package_root or not generated_files:
        return "fail", "code generation did not produce a code package"
    memory_layout = manifest.get("generated_memory_layout")
    runtime_config = manifest.get("generated_runtime_config")
    compile_gate = manifest.get("compile_gate", {})
    contract_check = manifest.get("contract_check", {})
    if not memory_layout or not Path(memory_layout).exists():
        return "fail", f"code generation missing memory layout: {memory_layout}"
    if not runtime_config or not Path(runtime_config).exists():
        return "fail", f"code generation missing runtime config: {runtime_config}"
    if compile_gate.get("status") != "pass":
        return "fail", f"code generation compile gate is not pass: {compile_gate.get('summary')}"
    if contract_check.get("status") != "pass":
        return "fail", f"code generation contract check is not pass: {contract_check.get('summary')}"
    root = Path(package_root)
    required = [
        root / "build.sbt",
        root / "src" / "main" / "scala" / "spatialaccagent" / "generated" / "GeneratedAcceleratorTop.scala",
        root / "src" / "main" / "scala" / "spatialaccagent" / "generated" / "GeneratedAxiDdrTop.scala",
        root / "src" / "main" / "scala" / "spatialaccagent" / "generated" / "GeneratedDesignParams.scala",
        root / "src" / "main" / "scala" / "spatialaccagent" / "generated" / "GeneratedContractCheck.scala",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        return "fail", f"generated code package missing {missing}"
    return "pass", f"planned_code_outputs={len(artifacts)}, generated_files={len(generated_files)}"


def check_backend_package(state: dict[str, Any]) -> tuple[str, str]:
    try:
        plan = read_json(artifact_path(state, "artifact.stage7.backend_board_plan"))
    except KeyError:
        return "pass", "backend package is checked after backend_board stage"
    package = plan.get("backend_package", {})
    root = Path(package.get("root", ""))
    if not root.exists():
        return "fail", f"backend package root missing: {root}"
    required = [
        root / "constraints" / "backend_handoff.json",
        root / "constraints" / "board_shell_contract.json",
        root / "constraints" / "app_shell_integration_contract.json",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        return "fail", f"backend package missing {missing}"
    return "pass", f"backend_package_files={len(package.get('files', []))}"


def check_verification_plan(state: dict[str, Any]) -> tuple[str, str]:
    upstream_errors = require_promoted_artifacts(
        state,
        [
            "artifact.stage6.verification_plan",
            "artifact.stage6.verification_artifact_contract",
            "artifact.stage6.llm_action_audit",
        ],
    )
    if upstream_errors:
        return "fail", "; ".join(upstream_errors)
    plan = read_json(artifact_path(state, "artifact.stage6.verification_plan"))
    checkers = plan.get("checker_plan", [])
    return ("pass", f"checkers={len(checkers)}") if checkers else ("fail", "checker plan is empty")


def check_verification_artifact_contract(state: dict[str, Any]) -> tuple[str, str]:
    try:
        contract = read_json(artifact_path(state, "artifact.stage6.verification_artifact_contract"))
    except KeyError:
        return "fail", "verification artifact contract is missing"
    if contract.get("status") != "pass":
        return "fail", f"verification artifact contract is not pass: {contract.get('summary')}"
    policy = contract.get("policy", {})
    required_policy_flags = [
        "smoke_is_not_acceptance",
        "real_weight_artifacts_required",
        "complete_transformer_block_weight_consumption_required",
        "transformer_blocks_are_the_only_accelerator_scope",
        "real_target_model_reference_required",
        "random_or_rtl_derived_expected_output_forbidden",
        "explicit_numeric_comparison_policy_required",
        "real_axi_ddr_runtime_required",
        "real_functional_sim_required",
        "board_runtime_required_for_final_pass",
        "contract_guided_debug_closure_required",
        "downstream_failure_requires_failure_slice",
        "later_stage_missing_gate_or_tool_requires_stage6_backtrack",
        "same_stage_retry_can_supersede_prior_stage6_barriers_after_promotion",
        "lower_layer_pass_evidence_is_reusable_not_absolute",
        "higher_layer_trace_can_trigger_targeted_lower_layer_backtrack",
        "do_not_reopen_passed_lower_layer_without_contradicting_boundary_trace",
    ]
    missing = [name for name in required_policy_flags if policy.get(name) is not True]
    if missing:
        return "fail", f"verification artifact contract missing policy flags: {missing}"
    backtrack_contract = contract.get("backtrack_contract", {})
    if not isinstance(backtrack_contract, dict) or backtrack_contract.get("target_stage") != "stage6.verification_artifacts":
        return "fail", "verification artifact contract missing Stage6 backtrack contract"
    debug_loop_contract = contract.get("debug_loop_contract", {})
    if not isinstance(debug_loop_contract, dict):
        return "fail", "verification artifact contract missing hierarchical debug-loop contract"
    layer_order = debug_loop_contract.get("layer_order", [])
    if layer_order != ["operator_leaf_modules", "single_transformer_layer_kernel", "board_axi_ddr_wrapped_system"]:
        return "fail", f"verification artifact contract has invalid debug layer order: {layer_order}"
    anti_spin = debug_loop_contract.get("anti_spin_policy", {}) if isinstance(debug_loop_contract.get("anti_spin_policy"), dict) else {}
    for flag in [
        "lower_layer_pass_evidence_is_reusable_not_absolute",
        "passed_lower_layer_can_be_challenged_by_current_layer_trace",
        "do_not_reopen_passed_lower_layer_without_contradicting_current_layer_trace",
    ]:
        if anti_spin.get(flag) is not True:
            return "fail", f"verification artifact contract missing anti-spin policy flag: {flag}"
    retry_contract = contract.get("retry_reconciliation_contract", {})
    if not isinstance(retry_contract, dict) or retry_contract.get("stage") != "stage6.verification_artifacts":
        return "fail", "verification artifact contract missing Stage6 retry reconciliation contract"
    return "pass", contract.get("summary", "verification artifact contract passed")


def check_hierarchical_verification_plan(state: dict[str, Any]) -> tuple[str, str]:
    plan = read_json(artifact_path(state, "artifact.stage6.verification_plan"))
    run_dir = artifact_path(state, "artifact.stage6.verification_plan").resolve().parents[1]
    case_adapter = case_adapter_for_state(state, run_dir)
    pipeline = read_json(artifact_path(state, "artifact.stage3.pipeline_plan"))
    hierarchy = plan.get("hierarchical_verification", {})
    if not isinstance(hierarchy, dict):
        return "fail", "hierarchical_verification is missing or malformed"
    stage_agents = hierarchy.get("stage_agents", [])
    merge_agents = hierarchy.get("merge_agents", [])
    evidence_gates = hierarchy.get("evidence_gates", [])
    missing = []
    if not stage_agents:
        missing.append("stage_agents")
    if not merge_agents:
        missing.append("merge_agents")
    if not evidence_gates:
        missing.append("evidence_gates")
    if missing:
        return "fail", f"hierarchical_verification missing {missing}"
    pipeline_stage_ids = {stage.get("stage_id") for stage in pipeline.get("stages", [])}
    agent_stage_ids = {agent.get("stage_id") for agent in stage_agents}
    uncovered = sorted(str(value) for value in pipeline_stage_ids - agent_stage_ids if value)
    if uncovered:
        return "fail", f"hierarchical stage agents do not cover pipeline stages: {uncovered}"
    required_gates = {gate.get("name") for gate in evidence_gates if gate.get("required")}
    expected = generic_required_gate_names(case_adapter)
    missing_gates = sorted(str(value) for value in expected - required_gates)
    if missing_gates:
        return "fail", f"required hierarchical evidence gates missing: {missing_gates}"
    return "pass", f"stage_agents={len(stage_agents)}, merge_agents={len(merge_agents)}, required_gates={len(required_gates)}"


def check_tool_protocols(state: dict[str, Any]) -> tuple[str, str]:
    tools = read_json(artifact_path(state, "artifact.input.tool_protocols"))
    items = tools.get("tools", [])
    scopes = {item.get("scope") for item in items}
    kinds = {item.get("kind") for item in items}
    required_scopes = {"local", "remote", "board"}
    missing_scopes = sorted(required_scopes - scopes)
    if missing_scopes:
        return "fail", f"tool protocols missing scopes: {missing_scopes}"
    has_vcs = any("vcs" in str(kind) for kind in kinds)
    has_verilator = any("verilator" in str(kind) for kind in kinds)
    if not (has_vcs or has_verilator):
        return "fail", "tool protocols missing functional simulator tool: configure VCS or Verilator"
    if not any("vivado" in str(kind) for kind in kinds):
        return "fail", "tool protocols missing Vivado tool"
    if not any("board" in str(kind) for kind in kinds):
        return "fail", "tool protocols missing board tool"
    configured = [item["name"] for item in items if item.get("command")]
    return "pass", f"tool_protocols={len(items)}, configured_commands={len(configured)}"


def check_memory_runtime_plan(state: dict[str, Any]) -> tuple[str, str]:
    board = read_json(artifact_path(state, "artifact.input.target_board_profile"))
    memory = board.get("memory_system", {})
    runtime = board.get("runtime_interface", {})
    has_memory_section = "memory_system" in board
    has_runtime_section = "runtime_interface" in board
    if not has_memory_section or not has_runtime_section:
        return "fail", "target_board_profile missing memory_system or runtime_interface"
    known_memory = [name for name, value in memory.items() if not empty(value)]
    known_runtime = [name for name, value in runtime.items() if not empty(value)]
    return "pass", f"memory_fields={known_memory}, runtime_fields={known_runtime}"


def check_human_boundary(state: dict[str, Any]) -> tuple[str, str]:
    boundary = read_json(artifact_path(state, "artifact.input.human_agent_boundary"))
    if not boundary.get("auto_allowed") or not boundary.get("approval_required") or not boundary.get("forbidden"):
        return "fail", "human boundary rule groups incomplete"
    return "pass", "human boundary has auto/approval/forbidden rules"


def verification_execution_scope() -> str:
    return os.environ.get("SPATIALACC_VERIFICATION_EXECUTION_SCOPE", stage6_gate_scope()).strip().lower() or stage6_gate_scope()


def stage6_gate_scope() -> str:
    return os.environ.get("SPATIALACC_STAGE6_GATE_SCOPE", "single_layer_closure").strip().lower() or "single_layer_closure"


def check_stage6_action_audit(state: dict[str, Any]) -> tuple[str, str]:
    try:
        audit = read_json(artifact_path(state, "artifact.stage6.llm_action_audit"))
    except KeyError:
        return "fail", "Stage6 LLM action audit artifact is missing"
    if audit.get("status") != "pass":
        return "fail", f"Stage6 LLM action audit is not pass: {audit.get('summary')}"
    return "pass", str(audit.get("summary") or "Stage6 LLM executable actions are grounded")


def stage6_verification_contract(state: dict[str, Any]) -> dict[str, Any]:
    return read_json(artifact_path(state, "artifact.stage6.verification_artifact_contract"))


def stage6_selector_contract(state: dict[str, Any]) -> dict[str, Any]:
    try:
        data = read_json(artifact_path(state, "artifact.stage5.stage6_gate_selector_contract"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def stage6_selector_contract_path(state: dict[str, Any]) -> str | None:
    try:
        return str(artifact_path(state, "artifact.stage5.stage6_gate_selector_contract"))
    except Exception:
        return None


def debug_loop_reused_scopes() -> set[str]:
    return {
        value.strip()
        for value in os.environ.get("SPATIALACC_DEBUG_LOOP_REUSED_SCOPES", "").split(",")
        if value.strip()
    }


def selector_certificate_reused_at_scope_entry(selector_key: str) -> bool:
    scope = SELECTOR_CERTIFICATE_SCOPES.get(selector_key)
    return bool(scope and scope in debug_loop_reused_scopes())


def stage6_artifact_ready(state: dict[str, Any], artifact_id: str) -> bool:
    try:
        path = artifact_path(state, artifact_id)
    except Exception:
        return False
    if not path.exists():
        return False
    for item in state.get("artifacts", []):
        if item.get("id") == artifact_id:
            return item.get("trust_status") == "validated"
    return False


def stage6_selected_gate_names(contract: dict[str, Any], selector: dict[str, Any] | None = None) -> list[str]:
    selector = selector or {}
    dag = contract.get("verification_gate_dag", {}) if isinstance(contract.get("verification_gate_dag"), dict) else {}
    selector_nodes = selector.get("gates", []) if isinstance(selector.get("gates"), list) else []
    nodes = selector_nodes or (dag.get("nodes", []) if isinstance(dag.get("nodes"), list) else [])
    names = [str(node.get("name")) for node in nodes if isinstance(node, dict) and node.get("name")]
    phase_by_name = {
        str(node.get("name")): str(node.get("phase") or "")
        for node in nodes
        if isinstance(node, dict) and node.get("name")
    }
    scope = stage6_gate_scope()
    if scope in {"all", "*"}:
        return names
    if scope in {"static", "static_gates"}:
        stop = {"functional_sim", "case_runtime_bitstream", "board_runtime"}
        return [name for name in names if name not in stop]
    stop_phase_by_scope = {
        "operator_leaf": "operator_leaf_semantic_aggregate",
        "operator_leaf_closure": "operator_leaf_semantic_aggregate",
        "leaf": "operator_leaf_semantic_aggregate",
        "single_layer": "single_layer_semantic_aggregate",
        "single_layer_closure": "single_layer_semantic_aggregate",
        "stage6_single_layer": "single_layer_semantic_aggregate",
        "multilayer": "multilayer_deadlock_liveness",
        "multilayer_closure": "multilayer_deadlock_liveness",
        "axi_ddr": "board_bringup",
        "axi_ddr_closure": "board_bringup",
        "board_axi_ddr": "board_bringup",
        "board_axi_ddr_closure": "board_bringup",
        "stage6_board_axi_ddr": "board_bringup",
        "functional": "board_bringup",
        "functional_sim": "board_bringup",
        "stage6_functional": "board_bringup",
    }
    if scope in stop_phase_by_scope:
        stop_phase = stop_phase_by_scope[scope]
        selected = []
        for name in names:
            selected.append(name)
            if phase_by_name.get(name) == stop_phase:
                break
        return selected
    requested = {item.strip() for item in scope.split(",") if item.strip()}
    if requested:
        selected = []
        for name in names:
            if name in requested:
                selected.append(name)
        return selected
    return names


def stage6_selector_blockers(state: dict[str, Any], selected_gates: list[str], selector: dict[str, Any]) -> list[str]:
    if not selector:
        return ["Stage6 selector contract is missing; rerun Stage5 verification_artifacts before Stage6"]
    selected = set(selected_gates)
    blockers: list[str] = []
    scope = stage6_gate_scope()
    for key in [
        "operator_leaf_promotion_certificate",
        "single_layer_promotion_certificate",
        "multilayer_promotion_certificate",
        "board_axi_ddr_promotion_certificate",
    ]:
        if key == "multilayer_promotion_certificate" and scope in BOARD_AXI_DDR_CLOSURE_SCOPES:
            continue
        if key == "board_axi_ddr_promotion_certificate" and scope in BOARD_AXI_DDR_CLOSURE_SCOPES:
            continue
        cert = selector.get(key, {}) if isinstance(selector.get(key), dict) else {}
        blocked = {str(gate) for gate in cert.get("blocks_until_present", []) if str(gate)}
        requested_blocked = sorted(selected & blocked)
        if not requested_blocked:
            continue
        artifact_id = str(cert.get("required_artifact") or "")
        certificate_ready = False
        if artifact_id and stage6_artifact_ready(state, artifact_id):
            candidate = stage6_promotion_certificate_payload(state, artifact_id)
            if candidate:
                _, payload = candidate
                required_gates = [str(gate) for gate in cert.get("required_gates", []) if str(gate)]
                level_id = SELECTOR_CERTIFICATE_LEVELS.get(key, str(payload.get("level_id") or ""))
                certificate_ready = selector_certificate_reused_at_scope_entry(key) or (
                    cert.get("evidence_contract") == evidence_contract_for_level(level_id)
                    and not certificate_contract_errors(payload, level_id, required_gates)
                )
        if not certificate_ready:
            blockers.append(
                f"{requested_blocked} blocked until {artifact_id or key} exists as current, live-source-bound SACG evidence"
            )
    return blockers


def selected_gate_dependency_closure(
    state: dict[str, Any],
    selected_gates: list[str],
    satisfied_gates: set[str] | None = None,
) -> set[str]:
    deps = stage6_gate_dependency_map(state)
    satisfied = set(satisfied_gates or set())
    closure = set(str(gate) for gate in selected_gates if str(gate) and str(gate) not in satisfied)
    pending = list(closure)
    while pending:
        gate = pending.pop()
        for dep in deps.get(gate, set()):
            if dep in satisfied:
                continue
            if dep not in closure:
                closure.add(dep)
                pending.append(dep)
    return closure


def stage6_promotion_certificate_payload(state: dict[str, Any], artifact_id: str) -> tuple[Path, dict[str, Any]] | None:
    try:
        path = artifact_path(state, artifact_id)
    except Exception:
        return None
    if not path.exists():
        return None
    artifact = None
    for item in state.get("artifacts", []):
        if isinstance(item, dict) and item.get("id") == artifact_id:
            artifact = item
            break
    if not artifact or artifact.get("trust_status") != "validated":
        return None
    try:
        payload = read_json(path)
    except Exception:
        return None
    if payload.get("status") != "pass":
        return None
    return path, payload


def gate_phase_map(nodes: list[dict[str, Any]]) -> dict[str, str]:
    return {
        str(node.get("name")): str(node.get("phase") or "")
        for node in nodes
        if isinstance(node, dict) and node.get("name")
    }


def gate_dependency_closure_from_map(deps: dict[str, set[str]], roots: list[str]) -> set[str]:
    closure = {str(root) for root in roots if str(root)}
    pending = list(closure)
    while pending:
        gate = pending.pop()
        for dep in deps.get(gate, set()):
            if dep not in closure:
                closure.add(dep)
                pending.append(dep)
    return closure


def reusable_stage6_certificate_evidence(
    state: dict[str, Any],
    selector: dict[str, Any],
    raw_selected_gates: list[str],
    nodes: list[dict[str, Any]],
) -> dict[str, Any]:
    """Return lower-layer gate evidence satisfied by validated certificates.

    Stage6 owns the certificate contract. It interprets the generic
    selector fields: a validated `required_artifact` can satisfy the certificate
    `required_gates` when the current selected gates intersect
    `blocks_until_present`.
    """

    selected = {str(gate) for gate in raw_selected_gates if str(gate)}
    deps = stage6_gate_dependency_map(state)
    phases = gate_phase_map(nodes)
    satisfied: dict[str, dict[str, Any]] = {}
    certificates: list[dict[str, Any]] = []
    rejected_certificates: list[dict[str, Any]] = []
    for key, value in selector.items():
        if not isinstance(value, dict):
            continue
        artifact_id = str(value.get("required_artifact") or "")
        if not artifact_id.startswith("artifact.stage6.") or "promotion_certificate" not in artifact_id:
            continue
        blocked = {str(gate) for gate in value.get("blocks_until_present", []) if str(gate)}
        if selected and not (selected & blocked):
            continue
        cert = stage6_promotion_certificate_payload(state, artifact_id)
        if not cert:
            continue
        path, payload = cert
        required_gates = [str(gate) for gate in value.get("required_gates", []) if str(gate)]
        if not required_gates:
            required_gates = [
                str(row.get("name"))
                for row in payload.get("required_gates", [])
                if isinstance(row, dict) and row.get("name")
            ]
        level_id = SELECTOR_CERTIFICATE_LEVELS.get(key, str(payload.get("level_id") or ""))
        contract_errors = certificate_contract_errors(payload, level_id, required_gates)
        if value.get("evidence_contract") != evidence_contract_for_level(level_id):
            contract_errors.append("Stage6 selector does not contain the current real-weight evidence contract")
        if contract_errors and not selector_certificate_reused_at_scope_entry(key):
            rejected_certificates.append(
                {
                    "selector_key": key,
                    "artifact_id": artifact_id,
                    "artifact_path": str(path),
                    "reasons": contract_errors,
                }
            )
            continue
        certified_gates = gate_dependency_closure_from_map(deps, required_gates)
        certificate_record = {
            "selector_key": key,
            "artifact_id": artifact_id,
            "artifact_path": str(path),
            "required_gates": required_gates,
            "blocks_until_present": sorted(blocked),
        }
        certificates.append(certificate_record)
        for gate in sorted(certified_gates):
            satisfied[gate] = {
                "name": gate,
                "status": "pass",
                "evidence_source": "promotion_certificate",
                "certificate_artifact": artifact_id,
                "certificate_path": str(path),
                "phase": phases.get(gate),
            }
    return {
        "certificates": certificates,
        "rejected_certificates": rejected_certificates,
        "gates": [satisfied[name] for name in sorted(satisfied)],
        "gate_names": set(satisfied),
    }


def reusable_exact_board_identity_evidence(
    run_dir: Path, case_adapter: dict[str, Any]
) -> dict[str, Any] | None:
    """Reuse only a currently validated exact-board discovery result.

    Board discovery is an immutable evidence producer.  Replaying it after a
    successful identity validation rewrites fact artifacts and can invalidate
    the very source closure that later L3 gates need.  This accepts no cached
    status alone: the shared exact-board validator must pass against the
    current files on every Stage-7 plan construction.
    """

    identity_path = run_dir / "verification" / "board_interface" / "board_source_identity.json"
    if not identity_path.is_file():
        return None
    try:
        from accagent.framework.board_acceptance_contract import validate_exact_board_identity

        validation = validate_exact_board_identity(identity_path)
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    if validation.get("status") != "pass":
        return None
    return {
        "name": gate_name(case_adapter, "board_interface_discovery"),
        "status": "pass",
        "evidence_source": "validated_exact_board_identity",
        "identity_path": str(identity_path.resolve()),
        "identity_sha256": sha256_file(identity_path),
        "identity_validation_schema": validation.get("schema_version"),
        "phase": "board_interface_discovery",
    }


def _walk_json_objects(value: Any) -> list[dict[str, Any]]:
    """Return nested JSON objects for bounded evidence extraction."""

    rows: list[dict[str, Any]] = []
    pending = [value]
    while pending:
        current = pending.pop()
        if isinstance(current, dict):
            rows.append(current)
            pending.extend(current.values())
        elif isinstance(current, list):
            pending.extend(current)
    return rows


def build_board_bringup_readiness(state: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    """Evaluate the minimum real-board evidence needed for implementation.

    This is intentionally narrower than strict AXI/DDR functional closure.  It
    proves that the current generated design can be handed to Vivado through
    the real board shell after a real weight-load and VCS execution.  Output
    and writeback failures are reported as diagnostics, never treated as pass
    evidence or silently discarded.
    """

    case_adapter = case_adapter_for_state(state, run_dir)
    paths = case_adapter.get("paths", {}) if isinstance(case_adapter.get("paths"), dict) else {}
    checks: list[dict[str, Any]] = []
    blockers: list[str] = []

    def check(name: str, passed: bool, summary: str, **evidence: Any) -> None:
        checks.append({"name": name, "status": "pass" if passed else "fail", "summary": summary, **evidence})
        if not passed:
            blockers.append(f"{name}: {summary}")

    lower_certificate_path: Path | None = None
    lower_certificate: dict[str, Any] = {}
    try:
        lower_certificate_path = artifact_path(
            state, "artifact.stage6.single_layer_promotion_certificate"
        )
    except Exception:
        candidate = run_dir / "verification" / "certificates" / "single_layer_promotion_certificate.json"
        lower_certificate_path = candidate if candidate.is_file() else None
    if lower_certificate_path is not None and lower_certificate_path.is_file():
        try:
            lower_certificate = read_json(lower_certificate_path)
            required_gates = [
                str(row.get("name"))
                for row in lower_certificate.get("required_gates", [])
                if isinstance(row, dict) and row.get("name")
            ]
            certificate_errors = certificate_contract_errors(
                lower_certificate,
                "single_layer_functional",
                required_gates,
                verify_live_files=False,
            )
            check(
                "single_layer_certificate",
                not certificate_errors,
                "validated passed single-layer certificate" if not certificate_errors else "; ".join(certificate_errors[:4]),
                path=str(lower_certificate_path),
            )
        except Exception as exc:
            check("single_layer_certificate", False, f"unreadable single-layer certificate: {exc}")
    else:
        check("single_layer_certificate", False, "passed single-layer certificate is missing")

    identity_path = resolve_case_path(
        run_dir,
        paths.get("board_source_identity")
        or run_dir / "verification" / "board_interface" / "board_source_identity.json",
    )
    try:
        from accagent.framework.board_acceptance_contract import validate_exact_board_identity

        identity_validation = validate_exact_board_identity(identity_path)
        check(
            "exact_board_identity",
            identity_validation.get("status") == "pass",
            "exact board identity validated" if identity_validation.get("status") == "pass" else "; ".join(str(item) for item in identity_validation.get("blockers", [])[:4]),
            path=str(identity_path),
        )
    except Exception as exc:
        check("exact_board_identity", False, f"exact board identity validation failed: {exc}", path=str(identity_path))

    binding_path = resolve_case_path(
        run_dir,
        paths.get("dut_weight_binding_manifest")
        or run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json",
    )
    binding: dict[str, Any] = {}
    try:
        binding = read_json(binding_path)
        preflight = binding.get("board_simulation_preflight_plan", {})
        preflight = preflight if isinstance(preflight, dict) else {}
        artifacts = preflight.get("artifacts", {}) if isinstance(preflight.get("artifacts"), dict) else {}
        required_images = {"input", "weight_image", "runtime_image"}
        images_present = required_images.issubset(artifacts)
        binding_ready = (
            binding.get("status") == "pass"
            and binding.get("dut_consumes_bound_weights") is True
            and binding.get("default_or_identity_weight_fallback_disabled") is True
            and images_present
        )
        check(
            "current_board_workload_binding",
            binding_ready,
            "current real input, weight, and runtime images are bound to the DUT" if binding_ready else "DUT weight/workload binding is incomplete",
            path=str(binding_path),
        )
    except Exception as exc:
        check("current_board_workload_binding", False, f"unreadable DUT weight binding: {exc}", path=str(binding_path))

    runner_path = run_dir / "verification" / "vcs" / "case_board_vcs_functional.json"
    diagnosis_path = run_dir / "verification" / "case_diagnostics" / "vcs_functional_diagnosis.json"
    runner: dict[str, Any] = {}
    diagnosis: dict[str, Any] = {}
    try:
        runner = read_json(runner_path)
        execution_identity = runner.get("simulation_execution_identity", {})
        execution_identity = execution_identity if isinstance(execution_identity, dict) else {}
        compile_status = (runner.get("compile") or {}).get("status") if isinstance(runner.get("compile"), dict) else None
        run = runner.get("run", {}) if isinstance(runner.get("run"), dict) else {}
        provenance_ready = (
            str(runner.get("verification_layer") or "").startswith("layer3")
            and runner.get("validation_mode") == "compute_slot_axi"
            and compile_status == "pass"
            and bool(execution_identity.get("identity_sha256"))
            and bool(run.get("remote_workdir"))
        )
        check(
            "exact_board_vcs_execution",
            provenance_ready,
            "real Layer-3 exact-board VCS execution provenance is present" if provenance_ready else "real Layer-3 exact-board VCS execution provenance is incomplete",
            path=str(runner_path),
        )
    except Exception as exc:
        check("exact_board_vcs_execution", False, f"unreadable board VCS runner report: {exc}", path=str(runner_path))

    try:
        diagnosis = read_json(diagnosis_path)
        nested = _walk_json_objects(diagnosis.get("failure_evidence", {}))
        runtime_complete = any(
            isinstance(row.get("runtime_load_progress"), dict)
            and int(row["runtime_load_progress"].get("target_words") or 0) > 0
            and int(row["runtime_load_progress"].get("accepted_words") or 0)
            >= int(row["runtime_load_progress"].get("target_words") or 0)
            and "runtime_load_complete" in str(row.get("phase") or "")
            for row in nested
        )
        weight_complete = any(
            int(row.get("weight_load_complete_cycle") or 0) > 0
            and int(row.get("weight_accept_count") or 0) > 0
            for row in nested
        )
        check(
            "complete_real_weight_load",
            runtime_complete and weight_complete,
            "real runtime and weight loading completed before token execution" if runtime_complete and weight_complete else "real runtime/weight-load completion evidence is incomplete",
            path=str(diagnosis_path),
        )
    except Exception as exc:
        check("complete_real_weight_load", False, f"unreadable VCS diagnosis: {exc}", path=str(diagnosis_path))

    output_diagnostics = {
        "runner_status": runner.get("status"),
        "runner_failure_class": (runner.get("run") or {}).get("failure_class") if isinstance(runner.get("run"), dict) else None,
        "diagnosis_status": diagnosis.get("status"),
        "diagnosis_failure_class": diagnosis.get("failure_class"),
    }
    return {
        "schema_version": "spatialaccagent.stage6_board_bringup_readiness.v1",
        "status": "pass" if not blockers else "fail",
        "board_bringup_ready": not blockers,
        "checks": checks,
        "blockers": blockers,
        "strict_output_diagnostics": output_diagnostics,
        "policy": {
            "requires_passed_single_layer_certificate": True,
            "requires_validated_exact_board_identity": True,
            "requires_current_real_workload_weight_binding": True,
            "requires_complete_real_weight_loading": True,
            "requires_real_exact_board_vcs_execution": True,
            "does_not_claim_final_output_or_ddr_writeback_correctness": True,
            "allows_vivado_synthesis_and_implementation_only": True,
        },
    }


def write_board_bringup_certificate(
    run_dir: Path, readiness: dict[str, Any]
) -> Path:
    """Persist the board-bringup evidence without promoting strict output pass."""

    path = run_dir / "verification" / "certificates" / "board_bringup_certificate.json"
    certificate = {
        "schema_version": BOARD_BRINGUP_CERTIFICATE_SCHEMA_VERSION,
        "artifact_id": "artifact.stage6.board_bringup_certificate",
        "status": readiness.get("status"),
        "board_bringup_ready": readiness.get("board_bringup_ready") is True,
        "readiness": readiness,
        "claim": "board bring-up / implementation closure readiness",
        "does_not_claim": [
            "complete transformer-block output correctness",
            "final DDR writeback correctness",
            "bitstream generation",
            "physical-board runtime success",
        ],
    }
    write_json(path, certificate)
    return path


def _stable_json_sha256(value: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _declared_file_identity(path_value: Any, expected_sha256: Any) -> tuple[Path | None, str | None]:
    """Validate a file and its declared byte identity for bridge evidence."""

    path = Path(str(path_value or ""))
    expected = str(expected_sha256 or "").lower()
    if not path.is_file() or len(expected) != 64:
        return None, None
    actual = sha256_file(path)
    if actual != expected:
        return None, None
    return path.resolve(), actual


def _certificate_derivation_contains_hash(certificate: dict[str, Any], expected_sha256: str) -> bool:
    """Accept only an immutable, hash-verified continuity ancestor."""

    expected = str(expected_sha256 or "").lower()
    current = certificate
    seen: set[str] = set()
    for _ in range(8):
        derivation = (
            current.get("certificate_derivation", {})
            if isinstance(current.get("certificate_derivation"), dict)
            else {}
        )
        source = derivation.get("source_certificate", {}) if isinstance(derivation.get("source_certificate"), dict) else {}
        source_path, source_hash = _declared_file_identity(source.get("path"), source.get("sha256"))
        proof = derivation.get("continuity_proof", {}) if isinstance(derivation.get("continuity_proof"), dict) else {}
        proof_path, _ = _declared_file_identity(proof.get("path"), proof.get("sha256"))
        if source_path is None or source_hash is None or proof_path is None or source_hash in seen:
            return False
        try:
            proof_document = read_json(proof_path)
            source_document = read_json(source_path)
        except Exception:
            return False
        proof_source = (
            proof_document.get("source_certificate", {})
            if isinstance(proof_document.get("source_certificate"), dict)
            else {}
        )
        if (
            proof_document.get("status") != "pass"
            or str(proof_source.get("sha256") or "").lower() != source_hash
        ):
            return False
        if source_hash == expected:
            return True
        seen.add(source_hash)
        current = source_document
    return False


def lower_layer_certificate_scaffold_bridge(
    state: dict[str, Any],
    run_dir: Path,
    case_adapter: dict[str, Any],
    selector: dict[str, Any],
    raw_selected_gates: list[str],
    reusable_evidence: dict[str, Any],
) -> dict[str, Any]:
    """Bridge a certified leaf scope to a connected-layer scaffold without replay.

    A semantic-testbench manifest may explicitly state that each isolated
    operator harness is covered by a live lower-layer promotion certificate.
    The legacy per-operator scaffold checker cannot represent that relation: it
    expects a new leaf testbench even though replaying it would be redundant.
    This bridge is deliberately narrower than a verification pass.  It accepts
    only a live lower certificate, an all-reused leaf manifest, and a current
    hash-verified connected testbench/binding.  The connected kernel and real
    functional/golden tools still execute normally afterwards.
    """

    scaffold_gate = gate_name(case_adapter, "tb_scaffold")
    result: dict[str, Any] = {
        "schema_version": "spatialaccagent.lower_layer_certificate_scaffold_bridge.v1",
        "status": "not_applicable",
        "gate": scaffold_gate,
        "reasons": [],
    }
    if scaffold_gate not in {str(gate) for gate in raw_selected_gates if str(gate)}:
        return result

    lower_selector = (
        selector.get("operator_leaf_promotion_certificate", {})
        if isinstance(selector.get("operator_leaf_promotion_certificate"), dict)
        else {}
    )
    artifact_id = str(lower_selector.get("required_artifact") or "")
    lower_pair = stage6_promotion_certificate_payload(state, artifact_id) if artifact_id else None
    if lower_pair is None:
        result.update(
            {
                "status": "rejected",
                "reasons": ["current operator-leaf promotion certificate is unavailable"],
            }
        )
        return result
    certificate_path, certificate = lower_pair
    required_gates = [str(gate) for gate in lower_selector.get("required_gates", []) if str(gate)]
    certificate_errors = certificate_contract_errors(
        certificate,
        "operator_leaf_functional",
        required_gates,
    )
    if certificate_errors:
        result.update({"status": "rejected", "reasons": certificate_errors})
        return result

    certified_gate_names = {
        str(row.get("name"))
        for row in reusable_evidence.get("gates", [])
        if isinstance(row, dict)
        and row.get("certificate_artifact") == artifact_id
        and row.get("name")
    }
    if not set(required_gates).issubset(certified_gate_names):
        result.update(
            {
                "status": "rejected",
                "reasons": ["lower promotion certificate does not satisfy the current dependency closure"],
            }
        )
        return result

    paths = case_adapter.get("paths", {}) if isinstance(case_adapter.get("paths"), dict) else {}
    semantic_manifest_path = resolve_case_path(
        run_dir,
        paths.get("semantic_testbench_manifest")
        or run_dir / "verification" / "semantic_testbench" / "semantic_testbench_manifest.json",
    )
    binding_path = resolve_case_path(
        run_dir,
        paths.get("dut_weight_binding_manifest")
        or run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json",
    )
    hierarchy_dir = resolve_case_path(
        run_dir,
        paths.get("hierarchy_dir") or run_dir / "verification" / "hierarchy",
    )
    if not semantic_manifest_path.is_file() or not binding_path.is_file():
        result.update(
            {
                "status": "rejected",
                "reasons": ["connected semantic manifest or DUT weight-binding manifest is missing"],
            }
        )
        return result
    try:
        manifest = read_json(semantic_manifest_path)
        binding = read_json(binding_path)
    except Exception as exc:
        result.update({"status": "rejected", "reasons": [f"connected scaffold evidence is unreadable: {exc}"]})
        return result

    reasons: list[str] = []
    lower_reference = (
        manifest.get("reused_operator_leaf_promotion_certificate", {})
        if isinstance(manifest.get("reused_operator_leaf_promotion_certificate"), dict)
        else {}
    )
    certificate_sha256 = sha256_file(certificate_path)
    if manifest.get("status") != "ready":
        reasons.append("semantic testbench manifest is not ready")
    if lower_reference.get("status") != "pass":
        reasons.append("semantic testbench manifest does not declare a passed lower certificate")
    if Path(str(lower_reference.get("path") or "")).resolve() != certificate_path.resolve():
        reasons.append("semantic testbench manifest lower certificate path does not match the live certificate")
    manifest_certificate_sha256 = str(lower_reference.get("sha256") or "").lower()
    if (
        manifest_certificate_sha256 != certificate_sha256
        and not _certificate_derivation_contains_hash(certificate, manifest_certificate_sha256)
    ):
        reasons.append("semantic testbench manifest lower certificate hash does not match the live certificate")
    if lower_reference.get("validation_errors") not in ([], None):
        reasons.append("semantic testbench manifest records lower certificate validation errors")

    contract_rows: list[dict[str, Any]] = []
    for row in manifest.get("stage_contracts", []):
        if not isinstance(row, dict):
            reasons.append("semantic testbench manifest contains a malformed operator contract")
            continue
        contract_path = Path(str(row.get("path") or ""))
        if row.get("status") != "reused_lower_layer_certificate":
            reasons.append(f"operator contract is not lower-certificate reused: {row.get('stage_id')}")
            continue
        if not contract_path.is_file():
            reasons.append(f"reused operator contract is missing: {row.get('stage_id')}")
            continue
        try:
            contract = read_json(contract_path)
        except Exception:
            reasons.append(f"reused operator contract is unreadable: {row.get('stage_id')}")
            continue
        if (
            contract.get("status") != "reused_lower_layer_certificate"
            or str(contract.get("stage_id") or "") != str(row.get("stage_id") or "")
        ):
            reasons.append(f"reused operator contract does not match its manifest entry: {row.get('stage_id')}")
            continue
        contract_rows.append(
            {
                "stage_id": str(row.get("stage_id") or ""),
                "path": str(contract_path.resolve()),
                "file_sha256": sha256_file(contract_path),
            }
        )
    if not contract_rows:
        reasons.append("semantic testbench manifest contains no reusable operator contracts")

    single = manifest.get("single_layer", {}) if isinstance(manifest.get("single_layer"), dict) else {}
    single_tb, single_tb_sha256 = _declared_file_identity(
        single.get("testbench"), single.get("testbench_sha256")
    )
    if single.get("status") != "ready" or single.get("real_weight_binding_verified") is not True:
        reasons.append("connected single-layer testbench is not real-weight ready")
    if single_tb is None or single_tb_sha256 is None:
        reasons.append("connected single-layer testbench is missing or hash drifted")

    source_rows: list[dict[str, str]] = []
    single_harness = (
        binding.get("single_layer_harness", {})
        if isinstance(binding.get("single_layer_harness"), dict)
        else {}
    )
    if (
        binding.get("status") != "pass"
        or binding.get("dut_consumes_bound_weights") is not True
        or binding.get("scope_coverage_complete") is not True
        or binding.get("default_or_identity_weight_fallback_disabled") is not True
        or single_harness.get("default_or_identity_weight_fallback_disabled") is not True
        or not str(single_harness.get("top_module") or "")
    ):
        reasons.append("DUT weight binding does not prove a complete connected real-weight harness")
    for row in single_harness.get("source_files", []):
        if not isinstance(row, dict):
            reasons.append("connected harness contains a malformed source declaration")
            continue
        source, source_sha256 = _declared_file_identity(row.get("path"), row.get("sha256"))
        if source is None or source_sha256 is None:
            reasons.append(f"connected harness source is missing or hash drifted: {row.get('path')}")
            continue
        source_rows.append({"path": str(source), "file_sha256": source_sha256})
    if not source_rows:
        reasons.append("connected harness has no hash-verified source files")

    requirements_path = Path(str(manifest.get("dut_weight_binding_requirements") or ""))
    requirements_sha256 = str(manifest.get("dut_weight_binding_requirements_sha256") or "")
    requirements, requirements_identity = _declared_file_identity(requirements_path, requirements_sha256)
    if requirements is None or requirements_identity is None:
        reasons.append("DUT weight-binding requirements are missing or hash drifted")
    if manifest.get("dut_weight_binding_verified") is not True:
        reasons.append("semantic manifest does not prove DUT real-weight binding")

    if reasons:
        result.update({"status": "rejected", "reasons": sorted(set(reasons))})
        return result

    bridge_inputs = {
        "gate": scaffold_gate,
        "lower_certificate": {
            "artifact_id": artifact_id,
            "path": str(certificate_path.resolve()),
            "file_sha256": certificate_sha256,
            "evidence_binding_sha256": certificate.get("evidence_binding", {}).get("binding_sha256"),
        },
        "semantic_manifest": {
            "path": str(semantic_manifest_path.resolve()),
            "file_sha256": sha256_file(semantic_manifest_path),
        },
        "binding_manifest": {"path": str(binding_path.resolve()), "file_sha256": sha256_file(binding_path)},
        "binding_requirements": {"path": str(requirements), "file_sha256": requirements_identity},
        "connected_testbench": {"path": str(single_tb), "file_sha256": single_tb_sha256},
        "reused_operator_contracts": sorted(contract_rows, key=lambda row: row["stage_id"]),
        "connected_harness_sources": sorted(source_rows, key=lambda row: row["path"]),
    }
    bridge_fingerprint = _stable_json_sha256(bridge_inputs)
    immutable_path = (
        run_dir
        / "verification"
        / "certificate_scope_bridges"
        / bridge_fingerprint
        / "tb_scaffold.json"
    )
    bridge_report = {
        "schema_version": "spatialaccagent.lower_layer_certificate_scaffold_bridge.v1",
        "name": "lower_layer_certificate_scaffold_bridge",
        "status": "pass",
        "gate": scaffold_gate,
        "scope": stage6_gate_scope(),
        "bridge_fingerprint_sha256": bridge_fingerprint,
        "inputs": bridge_inputs,
        "policy": {
            "is_not_hardware_tool_execution": True,
            "does_not_claim_connected_kernel_or_functional_correctness": True,
            "requires_live_lower_layer_certificate": True,
            "allows_no_replay_of_certified_operator_leaf_testbenches": True,
            "connected_kernel_and_real_functional_golden_evidence_still_required": True,
        },
    }
    write_json(immutable_path, bridge_report)
    hierarchy_report = {
        "schema_version": "spatialaccagent.lower_layer_certificate_scaffold_pointer.v1",
        "name": scaffold_gate,
        "status": "pass",
        "bridge": {"path": str(immutable_path), "file_sha256": sha256_file(immutable_path)},
        "policy": bridge_report["policy"],
    }
    write_json(hierarchy_dir / "tb_scaffold.json", hierarchy_report)
    result.update(
        {
            "status": "pass",
            "report_path": str(immutable_path),
            "report_sha256": sha256_file(immutable_path),
            "gate_evidence": {
                "name": scaffold_gate,
                "status": "pass",
                "evidence_source": "lower_layer_certificate_scaffold_bridge",
                "certificate_artifact": artifact_id,
                "certificate_path": str(certificate_path),
                "evidence_path": str(immutable_path),
                "bridge_fingerprint_sha256": bridge_fingerprint,
            },
        }
    )
    return result


def selected_gate_phases(gate_execution_plan: dict[str, Any]) -> set[str]:
    phases: set[str] = set()
    for step in gate_execution_plan.get("steps", []):
        if isinstance(step, dict) and step.get("phase"):
            phases.add(str(step.get("phase")))
    return phases


def requires_axi_runtime_preconditions(selected_gates: set[str], phases: set[str]) -> bool:
    gate_tokens = ("axi", "ddr", "runtime", "board", "vivado", "bitstream", "functional_sim")
    phase_tokens = ("axi", "ddr", "runtime", "board", "vivado", "bitstream", "functional_sim")
    return any(any(token in gate for token in gate_tokens) for gate in selected_gates) or any(
        any(token in phase for token in phase_tokens) for phase in phases
    )


def selected_tool_produces(gate_execution_plan: dict[str, Any]) -> set[str]:
    produced: set[str] = set()
    for step in gate_execution_plan.get("steps", []):
        if not isinstance(step, dict):
            continue
        for tool in step.get("tools", []):
            if not isinstance(tool, dict):
                continue
            produced.update(str(path) for path in tool.get("produces", []) if str(path))
    return produced


def is_current_scope_product(path: Path, produced_paths: set[str]) -> bool:
    path_text = str(path)
    return path_text in produced_paths or any(path_text == produced or path_text.startswith(f"{produced}/") for produced in produced_paths)


def gate_tool_roles(case_adapter: dict[str, Any], gate: str) -> list[str]:
    def include_if_present(role: str) -> list[str]:
        return [role] if adapter_tool(case_adapter, role) else []

    if gate.startswith("leaf_stage."):
        return ["stage_leaf_static"]
    if gate == gate_name(case_adapter, "real_weight_artifacts"):
        return ["weight_manifest_generate", "real_weight_artifacts"]
    if gate == gate_name(case_adapter, "target_model_reference"):
        return ["target_model_reference_generate"]
    if gate == gate_name(case_adapter, "semantic_testbench"):
        return ["semantic_testbench_generate"]
    if gate == gate_name(case_adapter, "boundary_contract"):
        return ["boundary_contract_check"]
    if gate == gate_name(case_adapter, "stage_leaf_static"):
        return ["stage_leaf_static"]
    if gate == gate_name(case_adapter, "leaf_functional"):
        return ["leaf_functional_sim"]
    if gate == gate_name(case_adapter, "leaf_golden_compare"):
        return ["leaf_golden_compare"]
    if gate == gate_name(case_adapter, "operator_leaf_semantic_evidence"):
        return ["operator_leaf_semantic_evidence"]
    if gate == gate_name(case_adapter, "tb_scaffold"):
        return ["tb_scaffold_generate", "tb_scaffold"]
    if gate == gate_name(case_adapter, "single_layer_kernel"):
        return ["tb_scaffold_generate", "stage_leaf_static", "leaf_functional_sim", "leaf_golden_compare", "tb_scaffold", "single_layer_kernel"]
    if gate == gate_name(case_adapter, "single_layer_functional"):
        return ["single_layer_functional_sim"]
    if gate == gate_name(case_adapter, "single_layer_golden_compare"):
        return ["single_layer_golden_compare"]
    if gate == gate_name(case_adapter, "single_layer_semantic_evidence"):
        return ["single_layer_semantic_evidence"]
    if gate == gate_name(case_adapter, "multilayer_pipeline"):
        return ["multilayer_pipeline"]
    if gate == gate_name(case_adapter, "multilayer_functional"):
        return ["multilayer_functional_sim"]
    if gate == gate_name(case_adapter, "pipeline_deadlock"):
        return ["pipeline_deadlock_check"]
    if gate == gate_name(case_adapter, "board_interface_discovery"):
        return ["board_interface_discovery"]
    if gate == gate_name(case_adapter, "axi_ddr_interface"):
        return ["axi_ddr_interface"]
    if gate == gate_name(case_adapter, "axi_protocol"):
        return ["axi_protocol_check"]
    if gate == gate_name(case_adapter, "ddr_image_roundtrip"):
        return ["ddr_image_roundtrip"]
    if gate == gate_name(case_adapter, "board_semantic_evidence"):
        return ["board_semantic_evidence"]
    if gate == gate_name(case_adapter, "functional_sim"):
        return ["vcs_functional_sim", "vcs_evidence_analyzer", "deadlock_axi_check"]
    if gate == gate_name(case_adapter, "vivado_synthesis"):
        return ["vivado_synthesis", "vivado_synthesis_report_check"]
    if gate == gate_name(case_adapter, "vivado_implementation"):
        return ["vivado_implementation", "vivado_implementation_report_check"]
    if gate == gate_name(case_adapter, "runtime_bitstream"):
        return ["runtime_bitstream"]
    if gate == gate_name(case_adapter, "runtime_abi"):
        return ["runtime_abi_check"]
    if gate == gate_name(case_adapter, "board_runtime"):
        return ["board_runtime"]
    return []


def reusable_provider_gate_for_role(
    case_adapter: dict[str, Any],
    consumer_gate: str,
    role: str,
) -> str | None:
    """Map duplicate non-board producers to their certified DAG gate."""

    if role == "tb_scaffold_generate" and consumer_gate in {
        gate_name(case_adapter, "tb_scaffold"),
        gate_name(case_adapter, "single_layer_kernel"),
        gate_name(case_adapter, "multilayer_pipeline"),
    }:
        return gate_name(case_adapter, "semantic_testbench")
    return None


def reusable_dependency_tool_role_evidence(
    case_adapter: dict[str, Any],
    consumer_gate: str,
    role: str,
    dependency_closure: set[str],
    reusable_gate_evidence: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    provider_gate = reusable_provider_gate_for_role(case_adapter, consumer_gate, role)
    evidence = reusable_gate_evidence.get(provider_gate or "")
    if not provider_gate or provider_gate not in dependency_closure or not evidence:
        return None
    return {
        "role": role,
        "provider_gate": provider_gate,
        "evidence_source": evidence.get("evidence_source"),
        "certificate_artifact": evidence.get("certificate_artifact"),
        "certificate_path": evidence.get("certificate_path"),
    }


def script_exists_for_argv(argv: list[str]) -> bool:
    if not argv:
        return False
    if re.fullmatch(r"(?:python(?:\d+(?:\.\d+)*)?|pypy(?:\d+)?)", Path(argv[0]).name) and len(argv) > 1:
        return (Path.cwd() / argv[1]).exists() or Path(argv[1]).exists()
    return (Path.cwd() / argv[0]).exists() or Path(argv[0]).exists() or argv[0] in {"bash", "sh", "ssh", "python3"}


def legacy_tool_for_role(role: str, spec: dict[str, Any], all_tools: list[dict[str, Any]]) -> dict[str, Any] | None:
    legacy_name = str(spec.get("legacy_name") or "")
    if legacy_name:
        for tool in all_tools:
            if str(tool.get("name") or "") == legacy_name:
                return tool
    name = str(spec.get("name") or "")
    for tool in all_tools:
        if str(tool.get("name") or "") == name:
            return tool
    if role == "vcs_functional_sim":
        for tool in all_tools:
            if "vcs" in str(tool.get("name") or "").lower() and isinstance(tool.get("execution"), dict):
                return tool
    return None


def execution_from_adapter_tool(
    role: str,
    spec: dict[str, Any],
    all_tools: list[dict[str, Any]],
    gate_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    legacy = legacy_tool_for_role(role, spec, all_tools)
    legacy_execution = dict(legacy.get("execution") or {}) if isinstance(legacy, dict) else {}
    argv = [str(item) for item in spec.get("argv", [])]
    env = dict(legacy_execution.get("env") or {})
    env.update({str(k): str(v) for k, v in dict(spec.get("env") or {}).items() if v is not None and v != ""})
    if gate_context:
        debug_trace_enabled = str(gate_context.get("debug_boundary_trace_enabled") or "0")
        env.update(
            {
                "SPATIALACC_VERIFICATION_GATE": str(gate_context.get("gate") or ""),
                "SPATIALACC_VERIFICATION_PHASE": str(gate_context.get("phase") or ""),
                "SPATIALACC_PIPELINE_STAGE_ID": str(gate_context.get("stage_id") or ""),
                "SPATIALACC_PIPELINE_STAGE_OP": str(gate_context.get("op") or ""),
                "SPATIALACC_PIPELINE_STAGE_KIND": str(gate_context.get("kind") or ""),
                "SPATIALACC_BOUNDARY_TRACE": debug_trace_enabled,
                "SPATIALACC_BOUNDARY_CONTRACTS": str(gate_context.get("debug_boundary_contracts") or ""),
                "SPATIALACC_BOUNDARY_TRACE_MANIFEST": str(gate_context.get("debug_trace_manifest") or ""),
                "SPATIALACC_BOUNDARY_TRACE_OUT": str(gate_context.get("debug_boundary_trace") or ""),
                "SPATIALACC_FAILURE_LOCALIZATION_OUT": str(gate_context.get("debug_failure_localization") or ""),
            }
        )
    timeout_sec = None
    if legacy_execution.get("timeout_sec"):
        timeout_sec = legacy_execution.get("timeout_sec")
    return {
        "argv": argv,
        "cwd": str(spec.get("cwd") or legacy_execution.get("cwd") or Path.cwd()),
        "env": env,
        "timeout_sec": timeout_sec,
    }


def adapter_tool_runner_spec(
    role: str,
    spec: dict[str, Any],
    all_tools: list[dict[str, Any]],
    gate_context: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    argv = [str(item) for item in spec.get("argv", [])]
    if not argv:
        return None
    execution = execution_from_adapter_tool(role, spec, all_tools, gate_context=gate_context)
    legacy = legacy_tool_for_role(role, spec, all_tools)
    base_name = str(spec.get("name"))
    name = base_name
    if gate_context and gate_context.get("phase") == "operator_leaf_module":
        name = f"{base_name}__{safe_id(str(gate_context.get('gate') or 'leaf_gate'))}"
    python_modules = spec.get("python_modules", [])
    return {
        "name": name,
        "base_name": base_name,
        "kind": str(spec.get("kind")),
        "scope": str(spec.get("scope") or "local"),
        "command": " ".join(argv),
        "execution": execution,
        "script_exists": script_exists_for_argv(argv),
        "required": bool(spec.get("required", False)),
        "required_group": spec.get("required_group"),
        "consumes": list(spec.get("consumes") or []),
        "produces": list(spec.get("produces") or []),
        "capabilities": list(spec.get("capabilities") or []),
        "python_modules": list(python_modules) if isinstance(python_modules, list) else python_modules,
        "python_module_versions": dict(spec.get("python_module_versions") or {}) if isinstance(spec.get("python_module_versions", {}), dict) else spec.get("python_module_versions"),
        "python_environment_group": spec.get("python_environment_group"),
        "adapter_role": role,
        "legacy_name": spec.get("legacy_name"),
        "legacy_protocol_name": legacy.get("name") if isinstance(legacy, dict) else None,
        "gate_context": gate_context or {},
    }


def build_stage6_gate_execution_plan(state: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    contract = stage6_verification_contract(state)
    selector = stage6_selector_contract(state)
    case_adapter = case_adapter_for_state(state, run_dir)
    debug_paths = write_debug_closure_artifacts(state, run_dir, run_dir / "verification" / "debug_closure")
    tool_protocols = read_json(artifact_path(state, "artifact.input.tool_protocols"))
    all_tools = [tool for tool in tool_protocols.get("tools", []) if isinstance(tool, dict)]
    dag = contract.get("verification_gate_dag", {}) if isinstance(contract.get("verification_gate_dag"), dict) else {}
    selector_nodes = selector.get("gates", []) if isinstance(selector.get("gates"), list) else []
    dag_nodes = dag.get("nodes", []) if isinstance(dag.get("nodes"), list) else []
    nodes = selector_nodes or dag_nodes
    raw_selected_gates = stage6_selected_gate_names(contract, selector)
    reusable_evidence = reusable_stage6_certificate_evidence(state, selector, raw_selected_gates, nodes)
    reusable_gate_evidence = {
        str(row.get("name")): row
        for row in reusable_evidence.get("gates", [])
        if isinstance(row, dict) and row.get("name")
    }
    exact_board_identity = reusable_exact_board_identity_evidence(run_dir, case_adapter)
    if exact_board_identity is not None:
        reusable_gate_evidence[str(exact_board_identity["name"])] = exact_board_identity
    scaffold_bridge = lower_layer_certificate_scaffold_bridge(
        state,
        run_dir,
        case_adapter,
        selector,
        raw_selected_gates,
        reusable_evidence,
    )
    bridge_evidence = scaffold_bridge.get("gate_evidence")
    if scaffold_bridge.get("status") == "pass" and isinstance(bridge_evidence, dict):
        reusable_gate_evidence[str(bridge_evidence["name"])] = bridge_evidence
    reusable_gate_names = set(reusable_gate_evidence)
    selected_roots = [gate for gate in raw_selected_gates if gate not in reusable_gate_names]
    selected_closure = selected_gate_dependency_closure(state, selected_roots, satisfied_gates=reusable_gate_names)
    selected_gates = [
        str(node.get("name"))
        for node in nodes
        if isinstance(node, dict)
        and node.get("name")
        and str(node.get("name")) in selected_closure
        and str(node.get("name")) not in reusable_gate_names
    ]
    node_by_name = {
        str(node.get("name")): node
        for node in nodes
        if isinstance(node, dict) and node.get("name")
    }
    steps: list[dict[str, Any]] = []
    for gate in selected_gates:
        node = node_by_name.get(gate, {})
        gate_context = {
            "gate": gate,
            "phase": node.get("phase"),
            "stage_id": node.get("stage_id"),
            "op": node.get("op"),
            "kind": node.get("kind"),
            "debug_boundary_trace_enabled": "1",
            "debug_boundary_contracts": debug_paths.get("boundary_contracts"),
            "debug_trace_manifest": debug_paths.get("trace_manifest"),
            "debug_boundary_trace": debug_paths.get("boundary_trace"),
            "debug_failure_localization": debug_paths.get("failure_localization"),
        }
        tool_roles = gate_tool_roles(case_adapter, gate)
        tools = []
        missing_roles = []
        reused_dependency_tool_roles = []
        dependency_closure = selected_gate_dependency_closure(state, [gate])
        for role in tool_roles:
            reused_role = reusable_dependency_tool_role_evidence(
                case_adapter,
                gate,
                role,
                dependency_closure,
                reusable_gate_evidence,
            )
            if reused_role:
                reused_dependency_tool_roles.append(reused_role)
                continue
            spec = adapter_tool(case_adapter, role)
            if not spec:
                missing_roles.append(role)
                continue
            runner_spec = adapter_tool_runner_spec(role, spec, all_tools, gate_context=gate_context)
            if runner_spec:
                tool_gate_name = str(runner_spec.get("base_name") or runner_spec.get("name") or "")
                if tool_gate_name in reusable_gate_names:
                    continue
                tools.append(runner_spec)
            else:
                missing_roles.append(role)
        steps.append(
            {
                "gate": gate,
                "depends_on": node.get("depends_on", []),
                "role": node.get("role"),
                "phase": node.get("phase"),
                "stage_id": node.get("stage_id"),
                "op": node.get("op"),
                "kind": node.get("kind"),
                "evidence_status": node.get("evidence_status"),
                "tool_roles": tool_roles,
                "tools": tools,
                "missing_tool_roles": missing_roles,
                "reused_dependency_tool_roles": reused_dependency_tool_roles,
            }
        )
    blockers = [
        f"{step['gate']} missing adapter tool role(s): {step['missing_tool_roles']}"
        for step in steps
        if step.get("missing_tool_roles")
    ]
    blockers.extend(stage6_selector_blockers(state, selected_gates, selector))
    selector_path = stage6_selector_contract_path(state)
    return {
        "schema_version": "spatialaccagent.stage6_gate_execution_plan.v0",
        "status": "pass" if not blockers else "fail",
        "scope": stage6_gate_scope(),
        "source_contract": str(artifact_path(state, "artifact.stage6.verification_artifact_contract")),
        "selector_contract": selector_path,
        "debug_closure": debug_paths,
        "action_audit": str(artifact_path(state, "artifact.stage6.llm_action_audit")) if any(a.get("id") == "artifact.stage6.llm_action_audit" for a in state.get("artifacts", [])) else None,
        "selected_gates": selected_gates,
        "reused_promotion_certificates": reusable_evidence.get("certificates", []),
        "rejected_promotion_certificates": reusable_evidence.get("rejected_certificates", []),
        "reused_certified_gates": [reusable_gate_evidence[name] for name in sorted(reusable_gate_evidence)],
        "certificate_scope_bridges": [scaffold_bridge],
        "steps": steps,
        "blockers": blockers,
        "policy": {
            "stage6_selector_contract_required": True,
            "stage6_default_stops_after_single_layer_closure": True,
            "debug_loop_target_scope_order": ["operator_leaf_closure", "single_layer_closure", "board_axi_ddr_closure"],
            "board_axi_ddr_closure_executes_multilayer_and_axi_ddr_subgates_in_one_third_layer_repair_loop": True,
            "runtime_bitstream_and_board_runtime_are_stage7_gates_unless_explicit_scope_all": True,
            "tool_execution_is_driven_by_stage6_gate_dag_and_case_adapter_roles": True,
            "selected_higher_layer_gate_still_requires_all_declared_dag_dependencies_to_pass": True,
            "failed_layer_enters_repair_loop_before_any_higher_layer_execution": True,
            "promotion_certificate_required_before_higher_layer_execution": True,
            "validated_lower_layer_certificates_satisfy_gate_dependencies": True,
            "lower_layer_pass_evidence_is_reusable_not_absolute": True,
            "higher_layer_trace_can_trigger_targeted_lower_layer_backtrack": True,
            "do_not_reopen_passed_lower_layer_without_contradicting_boundary_trace": True,
        },
    }


def tools_from_gate_execution_plan(plan: dict[str, Any]) -> list[dict[str, Any]]:
    tools: list[dict[str, Any]] = []
    seen: set[str] = set()
    for step in plan.get("steps", []):
        for tool in step.get("tools", []):
            name = str(tool.get("name") or "")
            if not name or name in seen:
                continue
            seen.add(name)
            tools.append(tool)
    return tools


def tool_selected_for_scope(tool: dict[str, Any], scope: str) -> bool:
    if scope in {"all", "*"}:
        return True
    name = str(tool.get("name") or "")
    kind = str(tool.get("kind") or "")
    if scope in BOARD_AXI_DDR_CLOSURE_SCOPES:
        lower = f"{name} {kind}".lower()
        if "smoke" in lower or "liveness_not_acceptance" in lower:
            return False
        if name in {"chisel_generate", "chisel_compile", "stage_verilator_lint"}:
            return True
        if name.startswith("case_") and not any(token in lower for token in ["vivado", "synthesis", "implementation", "runtime_bitstream", "board"]):
            return True
        return str(tool.get("required_group") or "") == "functional_sim" and "vivado" not in kind and "board" not in kind
    return True


def stage6_gate_dependency_map(state: dict[str, Any]) -> dict[str, set[str]]:
    try:
        contract = read_json(artifact_path(state, "artifact.stage6.verification_artifact_contract"))
    except Exception:
        return {}
    dag = contract.get("verification_gate_dag", {}) if isinstance(contract.get("verification_gate_dag"), dict) else {}
    result: dict[str, set[str]] = {}
    for node in dag.get("nodes", []):
        if not isinstance(node, dict):
            continue
        name = str(node.get("name") or "")
        if name:
            result[name] = {str(dep) for dep in node.get("depends_on", []) if dep}
    return result


def gate_depends_on(gate: str, failed_gate: str, deps: dict[str, set[str]]) -> bool:
    pending = list(deps.get(gate, set()))
    seen: set[str] = set()
    while pending:
        item = pending.pop()
        if item == failed_gate:
            return True
        if item in seen:
            continue
        seen.add(item)
        pending.extend(deps.get(item, set()) - seen)
    return False


def check_case_functional_sim_preconditions(
    state: dict[str, Any],
    run_dir: Path,
    gate_execution_plan: dict[str, Any],
) -> tuple[str, str]:
    case_adapter = case_adapter_for_state(state, run_dir)
    blockers: list[str] = []
    notes: list[str] = []
    if case_adapter.get("status") not in {"ready", "pass"}:
        blockers.append(f"case adapter is not ready: status={case_adapter.get('status')} errors={case_adapter.get('errors', [])}")
    preconditions = case_adapter.get("preconditions", {}) if isinstance(case_adapter.get("preconditions"), dict) else {}
    for item in preconditions.get("required_files", []):
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or "required case artifact")
        path = resolve_case_path(run_dir, item.get("path"))
        if not path.exists():
            blockers.append(f"{label} missing: {path}")
            continue
        if item.get("non_empty") and path.stat().st_size == 0:
            blockers.append(f"{label} is empty: {path}")
            continue
        expected_status = item.get("must_have_status")
        if expected_status:
            try:
                data = read_json(path)
                if data.get("status") != expected_status:
                    blockers.append(f"{label} status is {data.get('status')}, expected {expected_status}: {path}")
            except Exception as exc:
                blockers.append(f"{label} unreadable: {exc}")
    selected_gates = selected_gate_dependency_closure(state, [str(gate) for gate in gate_execution_plan.get("selected_gates", []) if str(gate)])
    phases = selected_gate_phases(gate_execution_plan)
    produced_paths = selected_tool_produces(gate_execution_plan)
    hierarchy_reports = preconditions.get("hierarchy_reports", {}) if isinstance(preconditions.get("hierarchy_reports"), dict) else {}
    hierarchy_blockers: list[str] = []
    deps = stage6_gate_dependency_map(state)
    for gate, value in hierarchy_reports.items():
        if selected_gates and str(gate) not in selected_gates:
            notes.append(f"{gate} is pending later verification scope")
            continue
        blocking_deps = [failed for failed in hierarchy_blockers if gate_depends_on(str(gate), failed, deps)]
        if blocking_deps:
            notes.append(f"{gate} blocked until {blocking_deps} are repaired")
            continue
        path = resolve_case_path(run_dir, value)
        if is_current_scope_product(path, produced_paths):
            notes.append(f"{gate} will be produced and judged by the current Stage7 tool scope")
            continue
        if not path.exists():
            blockers.append(f"{gate} report missing: {path}")
            hierarchy_blockers.append(str(gate))
            continue
        try:
            report = read_json(path)
            if report.get("status") != "pass":
                blockers.append(f"{gate} report is not pass: {report.get('blockers')}")
                hierarchy_blockers.append(str(gate))
        except Exception as exc:
            blockers.append(f"{gate} report unreadable: {exc}")
            hierarchy_blockers.append(str(gate))
    interface_groups = ["testbench_artifact_loading"]
    if requires_axi_runtime_preconditions(selected_gates, phases):
        interface_groups.extend(["board_testbench_artifact_loading", "rtl_interface"])
    for group_name in interface_groups:
        group = preconditions.get(group_name, {}) if isinstance(preconditions.get(group_name), dict) else {}
        files = [resolve_case_path(run_dir, value) for value in group.get("files", [])]
        text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in files if path.exists())
        missing_files = [str(path) for path in files if not path.exists()]
        if missing_files:
            blockers.append(f"{group_name} files missing: {missing_files}")
            continue
        missing_tokens = [str(token) for token in group.get("required_tokens", []) if str(token) not in text]
        if missing_tokens:
            blockers.append(f"{group_name} missing required tokens: {missing_tokens}")
    if blockers:
        suffix = f"; dependency_blocked={notes}" if notes else ""
        return "fail", "real functional simulation preconditions failed: " + "; ".join(blockers) + suffix
    note_suffix = f"; dependency_blocked={notes}" if notes else ""
    return "pass", f"case {case_adapter.get('case_id')} real inputs/weights and current-scope hierarchy prerequisites are present{note_suffix}"


def check_case_vcs_repair_diagnosis(
    state: dict[str, Any],
    run_dir: Path,
    gate_execution_plan: dict[str, Any],
) -> tuple[str, str]:
    case_adapter = case_adapter_for_state(state, run_dir)
    diagnosis = case_adapter.get("diagnosis", {}) if isinstance(case_adapter.get("diagnosis"), dict) else {}
    diagnosis_path = resolve_case_path(run_dir, diagnosis.get("path") or run_dir / "verification" / "case_diagnostics" / "vcs_functional_diagnosis.json")
    legacy_diagnosis_path = resolve_case_path(run_dir, diagnosis.get("legacy_path")) if diagnosis.get("legacy_path") else None
    tool_dir = run_dir / "verification" / "real_tools"
    trigger_names = [str(name) for name in diagnosis.get("trigger_tool_names", [])]
    if not trigger_names:
        trigger_names = ["case_vcs_functional_sim", "case_vcs_liveness"]
    selected_tool_names = {
        str(tool.get("name") or tool.get("base_name") or "")
        for step in gate_execution_plan.get("steps", [])
        if isinstance(step, dict)
        for tool in step.get("tools", [])
        if isinstance(tool, dict)
    }
    if not (selected_tool_names & set(trigger_names)):
        return "pass", "VCS repair diagnosis is not required for the current Stage7 scope"
    vcs_results = [tool_dir / f"{name}.json" for name in trigger_names if (tool_dir / f"{name}.json").exists()]
    failed_or_passed = []
    for path in vcs_results:
        try:
            item = read_json(path)
            if item.get("status") in {"pass", "fail"}:
                failed_or_passed.append(item)
        except Exception:
            continue
    if not failed_or_passed:
        return "pass", "no executed case VCS tool result is available yet; diagnosis will be required after execution"
    if not diagnosis_path.exists() and legacy_diagnosis_path and legacy_diagnosis_path.exists():
        diagnosis_path = legacy_diagnosis_path
    if not diagnosis_path.exists():
        return "fail", f"case VCS tool executed but repair diagnosis is missing: {diagnosis_path}"
    try:
        diagnosis_data = read_json(diagnosis_path)
    except Exception as exc:
        return "fail", f"case VCS repair diagnosis is unreadable: {exc}"
    if diagnosis_data.get("diagnosis_status") != "ready":
        return "fail", f"case VCS repair diagnosis is not ready: {diagnosis_data.get('diagnosis_status')}"
    root = diagnosis_data.get("root_cause_class")
    status = diagnosis_data.get("status")
    patterns = diagnosis_data.get("repair_handoff", {}).get("repair_patterns", []) if isinstance(diagnosis_data.get("repair_handoff"), dict) else []
    if any(item.get("status") == "fail" for item in failed_or_passed) and not root:
        return "fail", "case VCS failed but diagnosis has no root_cause_class"
    return "pass", f"case VCS diagnosis ready: status={status}, root_cause={root}, repair_patterns={len(patterns)}"


def real_tool_evidence(state: dict[str, Any], run_dir: Path, gate_execution_plan: dict[str, Any]) -> list[dict[str, Any]]:
    tool_dir = run_dir / "verification" / "real_tools"
    tool_dir.mkdir(parents=True, exist_ok=True)
    results = run_gate_ordered_tools(gate_execution_plan, tool_dir)
    normalized = []
    for item in results:
        required = bool(item.get("required", False))
        status = item["status"]
        name = str(item.get("name") or "")
        kind = str(item.get("kind") or "")
        acceptance_role = "diagnostic_or_static_tool"
        if item.get("required_group") == "functional_sim":
            acceptance_role = "functional_sim_candidate"
            if "smoke" in name.lower() or "smoke" in kind.lower() or "liveness_not_acceptance" in kind.lower():
                acceptance_role = "scaffold_liveness_not_functional_acceptance"
        if status == "not_run":
            failure_class = "pending_required_evidence" if required else "not_executed"
        elif status == "fail":
            failure_class = "required_real_tool_failure" if required else "real_tool_failure"
        else:
            failure_class = "passed_real_tool"
        normalized.append(
            {
                "checker": f"real_tool.{item['name']}",
                "status": item["status"],
                "summary": item["summary"],
                "failure_class": failure_class,
                "required": required,
                "required_group": item.get("required_group"),
                "kind": item.get("kind"),
                "acceptance_role": acceptance_role,
                "command": item["command"],
                "log_path": item["log_path"],
                "tool_report_path": item.get("tool_report_path"),
                "tool_report_status": item.get("tool_report_status"),
                "tool_report_summary": item.get("tool_report_summary"),
                "tool_report_blockers": item.get("tool_report_blockers", []),
                "python_environment_group": item.get("python_environment_group"),
                "python_environment": item.get("python_environment"),
                "python_environment_fingerprint_sha256": (
                    item.get("python_environment", {}).get("environment_fingerprint_sha256")
                    if isinstance(item.get("python_environment"), dict)
                    else None
                ),
                "execution_fingerprint_sha256": item.get("execution_fingerprint_sha256"),
                "reused_existing_result": bool(item.get("reused_existing_result", False)),
            }
        )
    return normalized


def gate_tools_pass(gate_tools: list[dict[str, Any]]) -> bool:
    if not gate_tools:
        return False
    required = [item for item in gate_tools if item.get("required")]
    if required:
        return all(item.get("status") == "pass" for item in required)
    return all(item.get("status") == "pass" for item in gate_tools)


def skipped_tool_result(tool: dict[str, Any], tool_dir: Path, reason: str) -> dict[str, Any]:
    name = str(tool.get("name") or "")
    log_path = tool_dir / f"{name}.json"
    result = {
        "schema_version": "spatialaccagent.real_tool_result.v0",
        "name": name,
        "kind": tool.get("kind"),
        "command": tool.get("command"),
        "execution": tool.get("execution"),
        "python_environment": None,
        "python_environment_group": tool.get("python_environment_group"),
        "enabled": True,
        "required": bool(tool.get("required", False)),
        "required_group": tool.get("required_group"),
        "script_exists": bool(tool.get("script_exists", False)),
        "timeout_sec": None,
        "returncode": None,
        "status": "not_run",
        "stdout_tail": "",
        "stderr_tail": "",
        "duration_sec": 0.0,
        "summary": reason,
        "log_path": str(log_path),
    }
    write_json(log_path, result)
    return result


def run_gate_ordered_tools(gate_execution_plan: dict[str, Any], tool_dir: Path) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    by_tool: dict[str, dict[str, Any]] = {}
    gate_status: dict[str, str] = {
        str(item.get("name")): "pass"
        for item in gate_execution_plan.get("reused_certified_gates", [])
        if isinstance(item, dict) and item.get("name")
    }
    selected = {str(name) for name in gate_execution_plan.get("selected_gates", [])}
    for step in gate_execution_plan.get("steps", []):
        if not isinstance(step, dict):
            continue
        gate = str(step.get("gate") or "")
        deps = [str(dep) for dep in step.get("depends_on", []) if str(dep)]
        failed_deps = [dep for dep in deps if gate_status.get(dep) != "pass"]
        tools = [tool for tool in step.get("tools", []) if isinstance(tool, dict)]
        if failed_deps:
            gate_results = []
            reason = f"skipped because dependency gate(s) are not pass: {failed_deps}"
            for tool in tools:
                name = str(tool.get("name") or "")
                if name in by_tool:
                    continue
                skipped = skipped_tool_result(tool, tool_dir, reason)
                by_tool[name] = skipped
                gate_results.append(skipped)
                results.append(skipped)
            gate_status[gate] = "blocked"
            continue
        gate_results = []
        runnable = []
        for tool in tools:
            name = str(tool.get("name") or "")
            if name in by_tool:
                gate_results.append(by_tool[name])
            else:
                runnable.append(tool)
        if runnable:
            new_results = run_tools(runnable, Path.cwd(), tool_dir)
            for item in new_results:
                by_tool[str(item.get("name") or "")] = item
            gate_results.extend(new_results)
            results.extend(new_results)
        gate_status[gate] = "pass" if gate_tools_pass(gate_results) else "fail"
    return results


def check_selected_gate_tool_execution(gate_execution_plan: dict[str, Any], tool_results: list[dict[str, Any]]) -> tuple[str, str]:
    expected = {
        str(tool.get("name"))
        for step in gate_execution_plan.get("steps", [])
        for tool in step.get("tools", [])
        if tool.get("name")
    }
    actual = {str(item.get("checker", "")).removeprefix("real_tool.") for item in tool_results}
    missing = sorted(expected - actual)
    dependency_skipped = sorted(
        str(item.get("checker", "")).removeprefix("real_tool.")
        for item in tool_results
        if str(item.get("checker", "")).removeprefix("real_tool.") in expected
        and item.get("status") == "not_run"
        and str(item.get("summary") or "").startswith("skipped because dependency gate")
    )
    not_run = sorted(
        str(item.get("checker", "")).removeprefix("real_tool.")
        for item in tool_results
        if str(item.get("checker", "")).removeprefix("real_tool.") in expected
        and item.get("status") == "not_run"
        and str(item.get("checker", "")).removeprefix("real_tool.") not in dependency_skipped
    )
    if missing or not_run:
        parts = []
        if missing:
            parts.append(f"missing result(s): {missing}")
        if not_run:
            parts.append(f"not executed: {not_run}")
        return "fail", "Stage7 selected gate tools were not executed: " + "; ".join(parts)
    return "pass", f"executed_selected_tools={len(actual & expected) - len(dependency_skipped)}, dependency_skipped_tools={len(dependency_skipped)}"


def check_real_tool_log_consistency(tool_results: list[dict[str, Any]]) -> tuple[str, str]:
    blockers: list[str] = []
    for item in tool_results:
        checker = str(item.get("checker", ""))
        name = checker.removeprefix("real_tool.")
        log_path = Path(str(item.get("log_path") or ""))
        if not log_path.exists():
            blockers.append(f"{name}: log missing at {log_path}")
            continue
        try:
            log = read_json(log_path)
        except Exception as exc:
            blockers.append(f"{name}: log unreadable: {exc}")
            continue
        if log.get("name") != name:
            blockers.append(f"{name}: log name mismatch {log.get('name')}")
        if log.get("status") != item.get("status"):
            blockers.append(f"{name}: result status {item.get('status')} disagrees with log status {log.get('status')}")
        if str(log.get("command") or "") != str(item.get("command") or ""):
            blockers.append(f"{name}: result command disagrees with log command")
        if item.get("status") == "pass" and log.get("enabled") is False:
            blockers.append(f"{name}: pass result points to a disabled tool log")
    if blockers:
        return "fail", "real-tool evidence/log mismatch: " + "; ".join(blockers)
    return "pass", f"real_tool_logs_consistent={len(tool_results)}"


def python_environment_group_fingerprints(
    tool_results: list[dict[str, Any]],
) -> tuple[dict[str, str], list[str], int]:
    blockers: list[str] = []
    groups: dict[str, list[tuple[str, str]]] = {}
    checked = 0
    for item in tool_results:
        environment = item.get("python_environment") if isinstance(item.get("python_environment"), dict) else None
        group = str(item.get("python_environment_group") or "")
        if environment is None and not group:
            continue
        if item.get("status") == "not_run":
            continue
        checked += 1
        name = str(item.get("checker") or "").removeprefix("real_tool.")
        if environment is None or environment.get("status") != "pass":
            blockers.append(f"{name}: declared Python environment contract is not pass")
            continue
        fingerprint = str(environment.get("environment_fingerprint_sha256") or "")
        if not fingerprint:
            blockers.append(f"{name}: Python environment fingerprint is missing")
            continue
        if group:
            groups.setdefault(group, []).append((name, fingerprint))
    for group, rows in sorted(groups.items()):
        fingerprints = {fingerprint for _, fingerprint in rows}
        if len(fingerprints) > 1:
            detail = ", ".join(f"{name}={fingerprint[:12]}" for name, fingerprint in rows)
            blockers.append(f"{group}: non-identical Python oracle environments [{detail}]")
    normalized = {
        group: rows[0][1]
        for group, rows in sorted(groups.items())
        if rows and len({fingerprint for _, fingerprint in rows}) == 1
    }
    return normalized, blockers, checked


def check_python_environment_contract(tool_results: list[dict[str, Any]]) -> tuple[str, str]:
    groups, blockers, checked = python_environment_group_fingerprints(tool_results)
    if blockers:
        return "fail", "Python tool environment contract failed: " + "; ".join(blockers)
    return "pass", f"python_environment_tools={checked}, consistent_groups={sorted(groups)}"


def check_required_real_tool_evidence(tool_results: list[dict[str, Any]]) -> tuple[str, str]:
    dependency_blocked = [
        f"{item['checker'].removeprefix('real_tool.')}={item['status']}"
        for item in tool_results
        if item.get("required")
        and item.get("status") == "not_run"
        and str(item.get("summary") or "").startswith("skipped because dependency gate")
    ]
    blockers = [
        f"{item['checker'].removeprefix('real_tool.')}={item['status']}"
        for item in tool_results
        if item.get("required") and not item.get("required_group") and item.get("status") != "pass"
        and f"{item['checker'].removeprefix('real_tool.')}={item['status']}" not in dependency_blocked
    ]
    groups: dict[str, list[dict[str, Any]]] = {}
    for item in tool_results:
        group = item.get("required_group")
        if group:
            groups.setdefault(str(group), []).append(item)
    for group, items in sorted(groups.items()):
        acceptable_items = items
        if group == "functional_sim":
            acceptable_items = [
                item for item in items
                if item.get("acceptance_role") != "scaffold_liveness_not_functional_acceptance"
            ]
        if not any(item.get("status") == "pass" for item in acceptable_items):
            detail = ", ".join(f"{item['checker'].removeprefix('real_tool.')}={item['status']}" for item in items)
            if all(
                item.get("status") == "not_run"
                and str(item.get("summary") or "").startswith("skipped because dependency gate")
                for item in acceptable_items
            ):
                dependency_blocked.append(f"{group}: blocked by prerequisite gate [{detail}]")
                continue
            if group == "functional_sim":
                blockers.append(f"{group}: need one real functional pass; smoke/liveness candidates are not acceptance evidence [{detail}]")
            else:
                blockers.append(f"{group}: need one pass among [{detail}]")
    if blockers:
        suffix = f"; dependency_blocked={dependency_blocked}" if dependency_blocked else ""
        return "fail", "required real-tool evidence missing or failed: " + ", ".join(blockers) + suffix
    suffix = f"; dependency_blocked={dependency_blocked}" if dependency_blocked else ""
    return "pass", "all executed required real-tool evidence passed" + suffix


def check_debug_closure_artifacts(results: dict[str, Any]) -> tuple[str, str]:
    paths = results.get("debug_closure", {}) if isinstance(results.get("debug_closure"), dict) else {}
    localization_path = Path(str(paths.get("failure_localization") or ""))
    if not localization_path.exists():
        return "fail", f"debug-closure failure localization artifact missing: {localization_path}"
    try:
        localization = read_json(localization_path)
    except Exception as exc:
        return "fail", f"debug-closure failure localization unreadable: {exc}"
    status = str(localization.get("status") or "")
    if results.get("status") == "fail" and status not in {
        "localized",
        "needs_boundary_trace",
        "verification_capability_gap",
    }:
        return "fail", f"debug-closure did not produce a usable failure slice for failed verification: {status}"
    return "pass", f"debug_closure={status}, root_candidate={localization.get('root_candidate_module')}"


def stage6_llm_record_errors(record: dict[str, Any], prefix: str = "evidence_classifier_agent") -> list[str]:
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


def current_scope_required_promotion_artifact(scope: str) -> str | None:
    value = (scope or "").strip().lower()
    if value in {"operator_leaf", "operator_leaf_closure", "leaf"}:
        return "artifact.stage6.operator_leaf_promotion_certificate"
    if value in {"single_layer", "single_layer_closure", "stage6_single_layer"}:
        return "artifact.stage6.single_layer_promotion_certificate"
    if value in {"multilayer", "multilayer_closure"}:
        return "artifact.stage6.multilayer_pipeline_promotion_certificate"
    if value in {
        "board_axi_ddr",
        "board_axi_ddr_closure",
        "stage6_board_axi_ddr",
        "functional",
        "functional_sim",
        "stage6_functional",
    }:
        return "artifact.stage6.board_axi_ddr_promotion_certificate"
    return None


def stage6_candidate_has_current_scope_pass(results: dict[str, Any]) -> bool:
    hard_results = [
        item
        for item in results.get("results", [])
        if isinstance(item, dict)
        and item.get("status") != "not_run"
        and item.get("checker")
        not in {"verification_team_llm_check", "evidence_classifier_llm_check", "verification_agent_decision_check"}
    ]
    if not hard_results or any(item.get("status") != "pass" for item in hard_results):
        return False
    certs = results.get("promotion_certificates", {}) if isinstance(results.get("promotion_certificates"), dict) else {}
    required_artifact = current_scope_required_promotion_artifact(str(results.get("execution_scope") or results.get("gate_execution_scope") or ""))
    if not required_artifact:
        return True
    if required_artifact not in certs:
        return False
    return Path(str(certs[required_artifact])).exists()


def _matching_reconciliation_context(
    row: dict[str, Any],
    *,
    verification_scope: str,
    debug_layer: str,
) -> bool:
    return (
        str(row.get("verification_scope") or "") == verification_scope
        and str(row.get("debug_layer") or "") == debug_layer
    )


def stage6_retry_reconciliation_contract(
    state: dict[str, Any],
    results: dict[str, Any],
) -> dict[str, Any]:
    """Bind only rejected predecessor records that a current certificate may retire.

    A passing rerun must not silently close an arbitrary historical failure with
    the same artifact id.  The contract carries the current certificate hash,
    exact hierarchy context, and the rejected predecessor transition ids before
    an LLM may authorize the bounded SACG reconciliation.
    """

    repair_loop = (
        results.get("hierarchical_repair_loop", {})
        if isinstance(results.get("hierarchical_repair_loop"), dict)
        else {}
    )
    current_layer = (
        repair_loop.get("current_layer", {})
        if isinstance(repair_loop.get("current_layer"), dict)
        else {}
    )
    verification_scope = str(
        results.get("execution_scope") or results.get("gate_execution_scope") or ""
    )
    debug_layer = str(current_layer.get("id") or "")
    required_artifact = current_scope_required_promotion_artifact(verification_scope)
    certificates = (
        results.get("promotion_certificates", {})
        if isinstance(results.get("promotion_certificates"), dict)
        else {}
    )
    certificate_path = Path(str(certificates.get(required_artifact) or ""))
    base = {
        "schema_version": "spatialaccagent.stage6_retry_reconciliation_contract.v1",
        "target_stage": "stage6.verification",
        "verification_scope": verification_scope,
        "debug_layer": debug_layer,
        "current_candidate": {
            "promotion_artifact_id": required_artifact,
            "promotion_certificate_path": str(certificate_path) if certificate_path else "",
            "promotion_certificate_sha256": (
                sha256_file(certificate_path) if certificate_path.is_file() else ""
            ),
        },
        "eligible_retry_request_ids": [],
        "eligible_contamination_barrier_ids": [],
        "predecessor_rejected_transition_ids": [],
        "excluded_unscoped_or_cross_layer_record_count": 0,
        "policy": {
            "current_scope_pass_and_content_addressed_certificate_required": True,
            "only_explicit_same_scope_rejected_predecessors_may_be_superseded": True,
            "unscoped_or_cross_layer_history_remains_preserved": True,
            "does_not_override_current_real_tool_failure": True,
        },
    }
    if not stage6_candidate_has_current_scope_pass(results):
        return {
            **base,
            "status": "not_ready",
            "reason": "current scope does not have a complete passing content-addressed candidate",
        }

    transition_statuses = {
        str(row.get("id") or ""): str(row.get("status") or "")
        for row in state.get("transitions", [])
        if isinstance(row, dict)
    }
    reconciliation_artifacts = set(STAGE6_RECONCILED_ARTIFACTS)
    memory = state.get("memory", {}) if isinstance(state.get("memory"), dict) else {}
    barrier_ids: list[str] = []
    predecessor_transitions: set[str] = set()
    excluded = 0
    for barrier in memory.get("contamination_barriers", []):
        if not isinstance(barrier, dict) or barrier.get("status", "active") != "active":
            continue
        if not _matching_reconciliation_context(
            barrier,
            verification_scope=verification_scope,
            debug_layer=debug_layer,
        ):
            excluded += 1
            continue
        transition_id = str(barrier.get("transition_id") or "")
        if (
            str(barrier.get("artifact_id") or "") not in reconciliation_artifacts
            or transition_statuses.get(transition_id) != "rejected"
        ):
            excluded += 1
            continue
        barrier_ids.append(str(barrier.get("id") or ""))
        predecessor_transitions.add(transition_id)

    retry_ids: list[str] = []
    for request in memory.get("retry_requests", []):
        if not isinstance(request, dict) or request.get("status") != "open":
            continue
        if not _matching_reconciliation_context(
            request,
            verification_scope=verification_scope,
            debug_layer=debug_layer,
        ):
            excluded += 1
            continue
        if str(request.get("target_stage") or "") != "stage6.verification":
            excluded += 1
            continue
        retry_ids.append(str(request.get("id") or ""))

    if not barrier_ids and not retry_ids:
        return {
            **base,
            "status": "not_required",
            "reason": "no active same-scope rejected predecessor records require reconciliation",
            "excluded_unscoped_or_cross_layer_record_count": excluded,
        }
    return {
        **base,
        "status": "ready",
        "reason": "current content-addressed candidate supersedes explicitly listed rejected same-scope predecessors",
        "eligible_retry_request_ids": sorted(set(retry_ids)),
        "eligible_contamination_barrier_ids": sorted(set(barrier_ids)),
        "predecessor_rejected_transition_ids": sorted(predecessor_transitions),
        "excluded_unscoped_or_cross_layer_record_count": excluded,
    }


def stage6_reconciliation_contract_errors(
    state: dict[str, Any],
    contract: dict[str, Any],
    *,
    verification_scope: str,
    debug_layer: str,
) -> list[str]:
    if contract.get("status") != "ready":
        return ["SACG reconciliation contract is not ready"]
    if contract.get("target_stage") != "stage6.verification":
        return ["SACG reconciliation contract has an invalid target stage"]
    if contract.get("verification_scope") != verification_scope or contract.get("debug_layer") != debug_layer:
        return ["SACG reconciliation contract does not match the current hierarchy scope"]
    candidate = contract.get("current_candidate", {}) if isinstance(contract.get("current_candidate"), dict) else {}
    certificate_path = Path(str(candidate.get("promotion_certificate_path") or ""))
    certificate_hash = str(candidate.get("promotion_certificate_sha256") or "").lower()
    if not certificate_path.is_file() or sha256_file(certificate_path) != certificate_hash:
        return ["SACG reconciliation contract candidate certificate is no longer current"]

    errors: list[str] = []
    memory = state.get("memory", {}) if isinstance(state.get("memory"), dict) else {}
    barriers = {
        str(row.get("id") or ""): row
        for row in memory.get("contamination_barriers", [])
        if isinstance(row, dict)
    }
    retries = {
        str(row.get("id") or ""): row
        for row in memory.get("retry_requests", [])
        if isinstance(row, dict)
    }
    transition_statuses = {
        str(row.get("id") or ""): str(row.get("status") or "")
        for row in state.get("transitions", [])
        if isinstance(row, dict)
    }
    for barrier_id in contract.get("eligible_contamination_barrier_ids", []):
        row = barriers.get(str(barrier_id))
        if (
            not row
            or row.get("status", "active") != "active"
            or not _matching_reconciliation_context(
                row,
                verification_scope=verification_scope,
                debug_layer=debug_layer,
            )
            or transition_statuses.get(str(row.get("transition_id") or "")) != "rejected"
        ):
            errors.append(f"SACG reconciliation barrier is no longer an eligible rejected predecessor: {barrier_id}")
    for retry_id in contract.get("eligible_retry_request_ids", []):
        row = retries.get(str(retry_id))
        if (
            not row
            or row.get("status") != "open"
            or row.get("target_stage") != "stage6.verification"
            or not _matching_reconciliation_context(
                row,
                verification_scope=verification_scope,
                debug_layer=debug_layer,
            )
        ):
            errors.append(f"SACG reconciliation retry request is no longer eligible: {retry_id}")
    return errors


def stage6_allows_structured_reconciliation(results: dict[str, Any], status: str, summary: str) -> bool:
    text = f"{status} {summary}".lower()
    if "reconciliation" not in text and "trust-barrier" not in text and "trust barrier" not in text:
        return False
    if "needs_repair" in status or "blocked_current_layer_needs_repair" in text:
        return False
    contract = (
        results.get("retry_reconciliation_contract", {})
        if isinstance(results.get("retry_reconciliation_contract"), dict)
        else {}
    )
    return stage6_candidate_has_current_scope_pass(results) and contract.get("status") == "ready"


def stage6_agent_decision_blockers(
    record: dict[str, Any],
    prefix: str = "evidence_classifier_agent",
    results: dict[str, Any] | None = None,
) -> list[str]:
    output = record.get("output", {}) if isinstance(record.get("output"), dict) else {}
    status = str(output.get("status") or "").strip().lower()
    if not status:
        return [f"{prefix}: missing decision status"]
    blocking_terms = ("blocked", "conflict", "needs_repair", "reconciliation_required", "pending")
    pass_terms = ("pass", "ready", "approved")
    if any(term in status for term in blocking_terms):
        summary = str(output.get("summary") or "LLM decision requires bounded reconciliation before promotion")
        if results is not None and stage6_allows_structured_reconciliation(results, status, summary):
            results.setdefault("sacg_reconciliation", {})
            results["sacg_reconciliation"] = {
                "status": "ready",
                "source": prefix,
                "llm_status": status,
                "summary": summary,
                "policy": {
                    "requires_current_scope_pass": True,
                    "requires_promotion_certificate": True,
                    "does_not_override_real_tool_failure": True,
                },
                "contract": results.get("retry_reconciliation_contract"),
            }
            return []
        return [f"{prefix}: {status}: {summary}"]
    if not any(term in status for term in pass_terms):
        summary = str(output.get("summary") or "LLM decision is not an explicit pass/ready state")
        return [f"{prefix}: unsupported decision status {status}: {summary}"]
    return []


def append_stage6_agent_gate_checks(
    results: dict[str, Any],
    design_team_summary: dict[str, Any],
    llm_record: dict[str, Any],
) -> list[str]:
    team_errors = team_failure_errors(design_team_summary, prefix="verification.design_team")
    llm_errors = stage6_llm_record_errors(llm_record, prefix="verification.evidence_classifier")
    decision_blockers = [] if llm_errors else stage6_agent_decision_blockers(llm_record, prefix="verification.evidence_classifier", results=results)
    retry_contract = (
        results.get("retry_reconciliation_contract", {})
        if isinstance(results.get("retry_reconciliation_contract"), dict)
        else {}
    )
    if not decision_blockers and retry_contract.get("status") == "ready":
        results.setdefault(
            "sacg_reconciliation",
            {
                "status": "ready",
                "source": "verification.evidence_classifier",
                "llm_status": str(
                    (llm_record.get("output") or {}).get("status") or ""
                ).lower(),
                "summary": "LLM accepted the supplied bounded SACG reconciliation contract",
                "policy": {
                    "requires_current_scope_pass": True,
                    "requires_promotion_certificate": True,
                    "does_not_override_real_tool_failure": True,
                },
                "contract": retry_contract,
            },
        )
    reconciliation = results.get("sacg_reconciliation", {}) if isinstance(results.get("sacg_reconciliation"), dict) else {}
    checks = [
        {
            "checker": "verification_team_llm_check",
            "status": "pass" if not team_errors else "fail",
            "summary": "verification design team LLM outputs are valid" if not team_errors else "; ".join(team_errors),
        },
        {
            "checker": "evidence_classifier_llm_check",
            "status": "pass" if not llm_errors else "fail",
            "summary": "evidence classifier LLM output is valid" if not llm_errors else "; ".join(llm_errors),
        },
        {
            "checker": "verification_agent_decision_check",
            "status": "pass" if not decision_blockers else "fail",
            "summary": (
                "evidence classifier decision allows Stage7 promotion"
                if not decision_blockers and not reconciliation
                else (
                    "evidence classifier requested SACG reconciliation; current-scope pass evidence and promotion certificate allow structured reconciliation"
                    if not decision_blockers
                    else "; ".join(decision_blockers)
                )
            ),
        },
    ]
    results.setdefault("results", []).extend(checks)
    hard_results = [item for item in results["results"] if item["status"] != "not_run"]
    results["status"] = "pass" if all(item["status"] == "pass" for item in hard_results) else "fail"
    return [*team_errors, *llm_errors, *decision_blockers]


def validation_llm_team_mode() -> str:
    value = os.environ.get("SPATIALACC_VALIDATION_LLM_TEAM_MODE", "conditional").strip().lower()
    return value if value in {"conditional", "full"} else "conditional"


def verification_specialist_trigger(results: dict[str, Any]) -> str | None:
    if validation_llm_team_mode() == "full":
        return "full_team_requested"
    repair_loop = results.get("hierarchical_repair_loop", {}) if isinstance(results.get("hierarchical_repair_loop"), dict) else {}
    failure_kind = str(repair_loop.get("failure_kind") or "")
    challenge = repair_loop.get("lower_layer_evidence_challenge", {}) if isinstance(repair_loop.get("lower_layer_evidence_challenge"), dict) else {}
    scope = str(results.get("gate_execution_scope") or results.get("execution_scope") or "").lower()
    if challenge.get("status") in {"challenge_present", "insufficient_challenge_evidence"}:
        return f"lower_layer_evidence_{challenge.get('status')}"
    # A missing harness, artifact, or observation capability has one current
    # owner. The primary evidence agent can route it directly; a board-scope
    # specialist adds no cross-layer information until real board evidence exists.
    if failure_kind == "verification_capability_gap":
        return None
    if failure_kind in {
        "unclassified_debug_failure",
        "lower_layer_evidence_contradicted",
        "integration_boundary_or_layer_interconnect",
        "board_wrapper_or_pipeline_integration",
    }:
        return failure_kind
    if scope in BOARD_AXI_DDR_CLOSURE_SCOPES:
        return "board_axi_ddr_cross_layer_evidence"
    return None


def exact_failed_stage6_route(results: dict[str, Any]) -> bool:
    if validation_llm_team_mode() != "conditional" or results.get("status") != "fail":
        return False
    loop = (
        results.get("hierarchical_repair_loop", {})
        if isinstance(results.get("hierarchical_repair_loop"), dict)
        else {}
    )
    current = loop.get("current_layer", {}) if isinstance(loop.get("current_layer"), dict) else {}
    challenge = (
        loop.get("lower_layer_evidence_challenge", {})
        if isinstance(loop.get("lower_layer_evidence_challenge"), dict)
        else {}
    )
    return bool(
        loop.get("failure_kind") == "hardware_value_mismatch"
        and loop.get("status") == "needs_repair"
        and current.get("status") == "needs_repair"
        and loop.get("root_candidate_module")
        and loop.get("violated_contract")
        and loop.get("agent_runtime_llm_blocker") is not True
        and challenge.get("status") == "no_lower_layer_challenge"
    )


def deterministic_failed_stage6_record(results: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    loop = results.get("hierarchical_repair_loop", {})
    output = {
        "schema_version": "spatialaccagent.stage_worker_output.v0",
        "agent": "evidence_classifier_agent",
        "stage": "verification",
        "status": "needs_repair",
        "summary": (
            "Deterministic real-tool and CCTG evidence already proves a current-layer hardware value mismatch at "
            f"{loop.get('root_candidate_module')}; promotion is impossible and the bounded implementation agent "
            "must consume this exact causal slice."
        ),
        "sacg_focus": {
            "nodes": [],
            "edges": [],
            "constraints": TOUCHED_CONSTRAINTS,
            "artifacts": ["artifact.stage6.verification_result"],
        },
        "observations": [
            f"failure_kind={loop.get('failure_kind')}",
            f"root_candidate_module={loop.get('root_candidate_module')}",
            f"violated_contract={loop.get('violated_contract')}",
        ],
        "risks": ["The current verification layer remains blocked until the same real-tool gate passes."],
        "proposed_actions": ["Build the bounded Stage-6 repair action directly from the persisted CCTG slice."],
        "executable_actions": [],
        "approval_required_for": [],
    }
    path = out_dir / "llm" / "evidence_classifier_deterministic_failure_route.json"
    record = {
        "schema_version": "spatialaccagent.stage_worker_record.v0",
        "agent": "evidence_classifier_agent",
        "stage": "verification",
        "mode": "deterministic_exact_failure_route",
        "result_path": str(path),
        "used_fallback": False,
        "error": None,
        "llm_skipped": True,
        "output": output,
    }
    write_json(path, record)
    return record


def no_split_review_summary(stage: str, reason: str) -> dict[str, Any]:
    return {
        "schema_version": "spatialaccagent.conditional_review_summary.v0",
        "stage": stage,
        "status": "no_split",
        "routing_mode": "conditional",
        "reason": reason,
        "errors": [],
        "subtask_count": 0,
        "completed_subtasks": 0,
        "used_fallback_count": 0,
        "decomposition_source": "deterministic_conditional_router",
        "decomposer_used_fallback": False,
        "executable_actions": [],
    }


def run_verification_review_team(
    state: dict[str, Any],
    results: dict[str, Any],
    out_dir: Path,
    *,
    source_sacg_state: Path | None = None,
) -> tuple[dict[str, Any], dict[str, str | None]]:
    trigger = verification_specialist_trigger(results)
    if trigger == "full_team_requested":
        team = run_design_team(
            stage="verification",
            objective="Classify checker and real-tool evidence into SACG constraint status and repair handoff risks.",
            state=state,
            candidate_artifact=results,
            out_dir=out_dir,
        )
        return team_summary(team), {
            "team_subtask_plan": team["subtask_plan_path"],
            "team_aggregate": team["aggregate_path"],
        }
    if trigger is None:
        return no_split_review_summary(
            "verification",
            "deterministic evidence class is unambiguous; the primary evidence classifier owns the agentic decision",
        ), {"team_subtask_plan": None, "team_aggregate": None}
    specialist = run_stage_agent(
        agent="verification_targeted_specialist_agent",
        stage="verification.targeted_specialist",
        task=(
            "Review only the routed verification ambiguity. Reconcile real-tool evidence, SACG/CCTG boundaries, "
            "hierarchical certificate dependencies, and human boundaries. Do not repeat deterministic pass rows, "
            "weaken acceptance, or propose higher-layer execution before the current scope closes."
        ),
        inputs={
            "routing_trigger": trigger,
            "verification_result": results,
            **(
                {"source_sacg_state": str(source_sacg_state)}
                if source_sacg_state is not None
                else {}
            ),
        },
        out_dir=out_dir,
        fallback_summary="Targeted verification ambiguity review was unavailable.",
    )
    errors = stage6_llm_record_errors(specialist, prefix="verification.targeted_specialist")
    output = specialist.get("output", {}) if isinstance(specialist.get("output"), dict) else {}
    summary = {
        "schema_version": "spatialaccagent.conditional_review_summary.v0",
        "stage": "verification",
        "status": "ready" if not errors else "incomplete",
        "routing_mode": "conditional",
        "reason": trigger,
        "errors": errors,
        "subtask_count": 1,
        "completed_subtasks": 1 if not errors else 0,
        "used_fallback_count": 1 if specialist.get("used_fallback") else 0,
        "decomposition_source": "deterministic_conditional_router",
        "decomposer_used_fallback": False,
        "specialist": output,
        "executable_actions": output.get("executable_actions", []),
    }
    return summary, {
        "team_subtask_plan": None,
        "team_aggregate": specialist.get("result_path"),
    }


def stage6_current_scope_required_checkers(results: dict[str, Any]) -> list[str]:
    required: list[str] = []
    seen: set[str] = set()
    for item in results.get("results", []):
        if not isinstance(item, dict):
            continue
        checker = str(item.get("checker") or "").strip()
        if not checker or item.get("status") == "not_run":
            continue
        if checker == "sacg_promotion_gate_check":
            continue
        if checker not in seen:
            seen.add(checker)
            required.append(checker)
    return required


def build_hierarchical_gate_summary(
    state: dict[str, Any],
    tool_results: list[dict[str, Any]],
    gate_execution_plan: dict[str, Any],
) -> dict[str, Any]:
    try:
        plan = read_json(artifact_path(state, "artifact.stage6.verification_plan"))
    except KeyError:
        return {"required_gates": [], "missing_or_failed": []}
    hierarchy = plan.get("hierarchical_verification", {})
    gates = hierarchy.get("evidence_gates", []) if isinstance(hierarchy, dict) else []
    by_name = {item["checker"].removeprefix("real_tool."): item for item in tool_results}
    by_group: dict[str, list[dict[str, Any]]] = {}
    for item in tool_results:
        group = item.get("required_group")
        if group:
            by_group.setdefault(str(group), []).append(item)
    gate_tool_names: dict[str, list[str]] = {}
    for step in gate_execution_plan.get("steps", []):
        if not isinstance(step, dict):
            continue
        gate_name = str(step.get("gate") or "")
        if not gate_name:
            continue
        names = gate_tool_names.setdefault(gate_name, [])
        for tool in step.get("tools", []):
            if not isinstance(tool, dict):
                continue
            tool_name = str(tool.get("name") or tool.get("base_name") or "")
            if tool_name and tool_name not in names:
                names.append(tool_name)

    def summarize_gate_tools(name: str) -> tuple[str, Any]:
        tool_names = gate_tool_names.get(name, [])
        gate_tools = [by_name[tool_name] for tool_name in tool_names if tool_name in by_name]
        missing = [tool_name for tool_name in tool_names if tool_name not in by_name]
        if not tool_names:
            return "not_run", None
        if missing:
            return "not_run", [by_name[item].get("log_path") for item in tool_names if item in by_name]
        if any(item.get("status") == "fail" for item in gate_tools):
            return "fail", [item.get("log_path") for item in gate_tools]
        if all(item.get("status") == "pass" for item in gate_tools):
            return "pass", [item.get("log_path") for item in gate_tools]
        return "not_run", [item.get("log_path") for item in gate_tools]

    required_gates = []
    missing_or_failed = []
    selected = set(str(name) for name in gate_execution_plan.get("selected_gates", []))
    reused = {
        str(item.get("name")): item
        for item in gate_execution_plan.get("reused_certified_gates", [])
        if isinstance(item, dict) and item.get("name")
    }
    for gate in gates:
        name = str(gate.get("name"))
        if not gate.get("required"):
            continue
        if selected and name not in selected:
            if name in reused:
                reuse = reused[name]
                item = {
                    "name": name,
                    "status": "pass",
                    "description": gate.get("description"),
                    "log_path": reuse.get("evidence_path") or reuse.get("certificate_path"),
                    "evidence_source": reuse.get("evidence_source") or "promotion_certificate",
                    "certificate_artifact": reuse.get("certificate_artifact"),
                }
                if reuse.get("bridge_fingerprint_sha256"):
                    item["bridge_fingerprint_sha256"] = reuse.get("bridge_fingerprint_sha256")
                required_gates.append(item)
                continue
            item = {
                "name": name,
                "status": "pending_later_stage",
                "description": gate.get("description"),
                "log_path": None,
            }
            required_gates.append(item)
            continue
        tool = by_name.get(name)
        group_tools = by_group.get(name, [])
        if tool:
            status = tool.get("status")
            log_path = tool.get("log_path")
        elif group_tools:
            status = "pass" if any(item.get("status") == "pass" for item in group_tools) else "fail"
            log_path = [item.get("log_path") for item in group_tools]
        elif name in gate_tool_names:
            status, log_path = summarize_gate_tools(name)
        else:
            status = "not_run"
            log_path = None
        item = {
            "name": name,
            "status": status,
            "description": gate.get("description"),
            "log_path": log_path,
        }
        required_gates.append(item)
        if status != "pass":
            missing_or_failed.append(item)
    return {
        "strategy": hierarchy.get("strategy"),
        "required_gates": required_gates,
        "missing_or_failed": missing_or_failed,
        "selected_gates": sorted(selected),
        "reused_certified_gates": sorted(reused),
    }


def selected_maturity_level_ids(gate_execution_plan: dict[str, Any]) -> set[str]:
    phases = selected_gate_phases(gate_execution_plan)
    level_ids: set[str] = set()
    if phases & {"materialization", "debug_boundary_contract", "operator_leaf_module", "operator_leaf_aggregate", "operator_leaf_functional", "operator_leaf_golden_compare", "operator_leaf_semantic_aggregate"}:
        level_ids.add("operator_leaf_functional")
    if phases & {"testbench_scaffold", "single_layer_kernel", "single_layer_functional", "single_layer_golden_compare", "single_layer_semantic_aggregate"}:
        level_ids.update({"operator_leaf_functional", "single_layer_functional"})
    if phases & {"multilayer_pipeline", "multilayer_functional", "multilayer_deadlock_liveness"}:
        level_ids.update({"operator_leaf_functional", "single_layer_functional", "multilayer_pipeline_functional"})
    if phases & {"board_interface_discovery", "board_wrapper_interface", "axi_protocol_check", "ddr_image_roundtrip", "board_semantic_aggregate"}:
        level_ids.update({"operator_leaf_functional", "single_layer_functional", "multilayer_pipeline_functional", "axi_ddr_functional"})
    if phases & {"functional_simulation", "vivado_synthesis", "vivado_implementation", "vivado_bitstream", "runtime_abi", "board_runtime"}:
        level_ids.update({"operator_leaf_functional", "single_layer_functional", "multilayer_pipeline_functional", "axi_ddr_functional"})
    if phases & {"debug_boundary_contract"}:
        level_ids.add("contract_guided_debug_closure")
    return level_ids or {"operator_leaf_functional"}


def build_hierarchical_maturity_report(
    state: dict[str, Any],
    gate_summary: dict[str, Any],
    gate_execution_plan: dict[str, Any],
) -> dict[str, Any]:
    try:
        plan = read_json(artifact_path(state, "artifact.stage6.verification_plan"))
    except KeyError:
        return {
            "schema_version": "spatialaccagent.hierarchical_maturity_report.v0",
            "status": "fail",
            "blockers": ["missing Stage6 verification plan"],
            "levels": [],
        }
    hierarchy = plan.get("hierarchical_verification", {}) if isinstance(plan.get("hierarchical_verification"), dict) else {}
    contract = hierarchy.get("maturity_contract", {}) if isinstance(hierarchy.get("maturity_contract"), dict) else {}
    required_gate_status = {
        str(item.get("name")): str(item.get("status") or "not_run")
        for item in gate_summary.get("required_gates", [])
        if isinstance(item, dict) and item.get("name")
    }
    levels = []
    blockers = []
    required_level_ids = selected_maturity_level_ids(gate_execution_plan)
    for level in contract.get("levels", []) if isinstance(contract.get("levels"), list) else []:
        if not isinstance(level, dict):
            continue
        level_id = str(level.get("id") or "")
        if level_id not in required_level_ids:
            levels.append(
                {
                    "id": level.get("id"),
                    "status": "pending_later_stage",
                    "required_before": level.get("required_before"),
                    "required_gates": [
                        {"name": str(value), "status": "pending_later_stage"}
                        for value in level.get("required_gates", [])
                        if str(value)
                    ],
                    "required_tool_roles": level.get("required_tool_roles", []),
                }
            )
            continue
        required_gates = [str(value) for value in level.get("required_gates", []) if str(value)]
        gate_rows = [
            {"name": gate, "status": required_gate_status.get(gate, "not_run")}
            for gate in required_gates
        ]
        missing_or_failed = [
            f"{row['name']}={row['status']}"
            for row in gate_rows
            if row["status"] != "pass"
        ]
        status = "pass" if required_gates and not missing_or_failed else "fail"
        if status != "pass":
            blockers.append(f"{level_id}: " + ", ".join(missing_or_failed or ["no required gates declared"]))
        levels.append(
            {
                "id": level.get("id"),
                "status": status,
                "required_before": level.get("required_before"),
                "required_gates": gate_rows,
                "required_tool_roles": level.get("required_tool_roles", []),
            }
        )
    backend_level_ids = {
        "operator_leaf_functional",
        "single_layer_functional",
        "multilayer_pipeline_functional",
        "axi_ddr_functional",
    }
    backend_ready = bool(levels) and all(
        item.get("status") == "pass"
        for item in levels
        if str(item.get("id")) in backend_level_ids
    )
    current_scope_ready = bool(required_level_ids) and not blockers
    return {
        "schema_version": "spatialaccagent.hierarchical_maturity_report.v0",
        "status": "pass" if current_scope_ready else "fail",
        "current_scope_ready": current_scope_ready,
        "backend_ready": backend_ready,
        "required_level_ids": sorted(required_level_ids),
        "levels": levels,
        "blockers": blockers,
        "policy": {
            "stage7_must_not_run_backend_tools_unless_backend_ready": True,
            "static_leaf_checks_are_not_functional_correctness": True,
            "contract_guided_debug_closure_required_for_repair": True,
            "later_levels_are_pending_not_fail_for_current_scope": True,
        },
    }


def gate_status_map(gate_summary: dict[str, Any]) -> dict[str, str]:
    return {
        str(item.get("name")): str(item.get("status") or "not_run")
        for item in gate_summary.get("required_gates", [])
        if isinstance(item, dict) and item.get("name")
    }


def _as_file_paths(value: Any) -> list[str]:
    if isinstance(value, str) and value:
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if isinstance(item, (str, Path)) and str(item)]
    return []


def _resolve_evidence_file(run_dir: Path, value: Any) -> Path | None:
    text = str(value or "").strip()
    if not text:
        return None
    path = Path(text)
    candidates = [path] if path.is_absolute() else [Path.cwd() / path, run_dir / path]
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if resolved.is_file():
            return resolved
    return None


def _promotion_binding_document_rows(
    document: dict[str, Any],
    *,
    document_path: Path,
    gate: str,
    run_dir: Path,
    current_promotion_artifact_id: str | None = None,
    excluded_same_scope_promotion_certificates: list[dict[str, str]] | None = None,
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[str]]:
    rows: list[dict[str, str]] = []
    fingerprints: list[dict[str, str]] = []
    errors: list[str] = []
    source_list_keys = {
        "source_files",
        "rtl_sources",
        "compiled_sources",
        "compile_sources",
        "generated_sources",
    }
    fingerprint_names = {
        "contract_sha256",
        "input_fingerprint_sha256",
        "source_identity_sha256",
        "source_set_sha256",
        "testbench_sha256",
        "trace_sha256",
        "vcs_compile_plan_sha256",
    }
    semantic_hash_names = {
        "tensor_sha256",
        "semantic_sha256",
        "value_sha256",
        "content_sha256",
        "source_tensor_sha256",
        "source_slice_sha256",
    }

    def is_sha256(value: Any) -> bool:
        text = str(value or "").lower()
        return len(text) == 64 and all(char in "0123456789abcdef" for char in text)

    def path_prefix(path_key: str) -> str:
        return path_key[:-5] if path_key.endswith("_path") else ""

    def has_semantic_content_descriptor(value: dict[str, Any]) -> bool:
        return any(
            key in value
            for key in (
                "tensor",
                "parameter_suffix",
                "dtype",
                "shape",
                "tensor_shape",
                "tensor_sha256",
                "semantic_sha256",
                "value_sha256",
                "content_sha256",
                "source_tensor_sha256",
                "source_slice_sha256",
            )
        ) or any(
            str(key).endswith(("_dtype", "_shape", "_tensor_sha256"))
            for key in value
        )

    def declared_file_hash(value: dict[str, Any], path_key: str) -> tuple[str | None, str | None]:
        """Return the byte hash paired with a path, never a tensor-value hash."""

        prefix = path_prefix(path_key)
        candidates: list[str] = []
        if prefix:
            candidates.append(f"{prefix}_file_sha256")
        candidates.append("file_sha256")
        for key in candidates:
            if is_sha256(value.get(key)):
                return key, str(value[key]).lower()

        # Legacy documents use `sha256` (or `source_sha256`) for file bytes.
        # A descriptor that carries tensor shape/dtype/value identity instead
        # uses that field for semantic content, so do not confuse the two.
        legacy_key = f"{prefix}_sha256" if prefix else "sha256"
        if legacy_key not in semantic_hash_names and not has_semantic_content_descriptor(value):
            if is_sha256(value.get(legacy_key)):
                return legacy_key, str(value[legacy_key]).lower()
        return None, None

    def record_nonbyte_content_identities(
        value: dict[str, Any],
        *,
        pointer: str,
        path_value: str,
        file_hash_key: str | None,
    ) -> None:
        semantic_descriptor = has_semantic_content_descriptor(value)
        for key, raw_hash in value.items():
            key_text = str(key)
            if not is_sha256(raw_hash):
                continue
            if key_text in fingerprint_names or key_text.endswith("_fingerprint_sha256"):
                continue
            if key_text.endswith("_file_sha256") or key_text == file_hash_key:
                continue
            is_declared_content_hash = (
                key_text in semantic_hash_names
                or (
                    key_text == "sha256"
                    and (file_hash_key is not None or semantic_descriptor)
                )
                or (
                    key_text.endswith("_sha256")
                    and semantic_descriptor
                    and key_text not in {"source_sha256"}
                )
            )
            if not is_declared_content_hash:
                continue
            fingerprints.append(
                {
                    "name": key_text,
                    "value": str(raw_hash).lower(),
                    "source": f"{document_path}#{pointer}/{key_text}",
                    "kind": "declared_nonbyte_content_identity",
                    "artifact_path": path_value,
                }
            )

    def should_bind_direct_path(
        value: dict[str, Any],
        *,
        path_key: str,
        file_hash_key: str | None,
    ) -> bool:
        # Logs and report-location fields are snapshotted by the caller.  Bind
        # a path discovered inside JSON only when the document actually
        # declares an artifact identity, rather than turning every metadata
        # `*_path` into a second, mutable live dependency.
        return file_hash_key is not None or has_semantic_content_descriptor(value)

    def excludes_current_scope_certificate(
        path: Path,
        *,
        role: str,
        expected: str | None,
        source: str,
    ) -> bool:
        if not current_promotion_artifact_id:
            return False
        try:
            candidate = read_json(path)
        except Exception:
            return False
        if str(candidate.get("artifact_id") or "") != current_promotion_artifact_id:
            return False
        if excluded_same_scope_promotion_certificates is not None:
            excluded_same_scope_promotion_certificates.append(
                {
                    "artifact_id": current_promotion_artifact_id,
                    "path": str(path),
                    "declared_sha256": str(expected or "").lower(),
                    "current_sha256": sha256_file(path),
                    "role": role,
                    "source": source,
                    "reason": "same_scope_promotion_certificate_cannot_be_evidence_for_its_replacement",
                }
            )
        return True

    def add_file(
        value: Any,
        role: str,
        expected: str | None = None,
        source: str = "",
    ) -> None:
        path = _resolve_evidence_file(run_dir, value)
        if path is None:
            if role == "source_file" and str(value or "").strip():
                errors.append(f"{gate}: live source file is missing: {value}")
            return
        if excludes_current_scope_certificate(
            path,
            role=role,
            expected=expected,
            source=source or str(document_path),
        ):
            return
        actual = sha256_file(path)
        normalized_expected = str(expected or "").lower()
        if normalized_expected and normalized_expected != actual:
            errors.append(f"{gate}: live evidence hash already drifted: {path}")
            return
        rows.append(
            {
                "gate": gate,
                "path": str(path),
                "sha256": actual,
                "role": role,
            }
        )

    def walk(value: Any, pointer: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                key_text = str(key)
                child_pointer = f"{pointer}/{key_text}"
                if isinstance(child, str) and (key_text == "path" or key_text.endswith("_path")):
                    file_hash_key, expected_hash = declared_file_hash(value, key_text)
                    if should_bind_direct_path(
                        value,
                        path_key=key_text,
                        file_hash_key=file_hash_key,
                    ):
                        is_ephemeral_debug_artifact = "/verification/debug_closure/" in str(child).replace("\\", "/")
                        role = (
                            "evidence_artifact"
                            if is_ephemeral_debug_artifact
                            or any(
                                token in child_pointer
                                for token in ("/output", "/produced_reports", "/downloads", "/receipt", "/trace")
                            )
                            else "input_artifact"
                        )
                        add_file(child, role, expected_hash, f"{document_path}#{child_pointer}")
                        record_nonbyte_content_identities(
                            value,
                            pointer=pointer,
                            path_value=child,
                            file_hash_key=file_hash_key,
                        )
                if key_text in source_list_keys and isinstance(child, list):
                    for item in child:
                        if isinstance(item, str):
                            add_file(item, "source_file", source=f"{document_path}#{child_pointer}")
                        elif isinstance(item, dict):
                            item_path_key = "source_path" if item.get("source_path") else "path"
                            file_hash_key, expected_hash = declared_file_hash(item, item_path_key)
                            add_file(
                                item.get("source_path") or item.get("path"),
                                "source_file",
                                expected_hash,
                                f"{document_path}#{child_pointer}",
                            )
                            record_nonbyte_content_identities(
                                item,
                                pointer=child_pointer,
                                path_value=str(item.get(item_path_key) or ""),
                                file_hash_key=file_hash_key,
                            )
                if (
                    isinstance(child, str)
                    and is_sha256(child)
                    and (key_text in fingerprint_names or key_text.endswith("_fingerprint_sha256"))
                ):
                    fingerprints.append(
                        {
                            "name": key_text,
                            "value": child.lower(),
                            "source": f"{document_path}#{child_pointer}",
                            "kind": "document_fingerprint",
                            "artifact_path": "",
                        }
                    )
                walk(child, child_pointer)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{pointer}/{index}")

    walk(document, "")
    return rows, fingerprints, errors


def higher_scope_semantic_artifact_for_promotion(
    path_text: str,
    run_dir: Path,
    current_promotion_artifact_id: str | None,
) -> bool:
    """Exclude generated vectors owned by a later verification scope.

    The shared semantic generator emits operator, connected-layer, and board
    vectors in one directory tree.  A promotion certificate only keeps live
    hashes for artifacts in its own scope; later-scope vectors are regenerated
    during normal repair and cannot invalidate an already proven lower scope.
    """

    excluded_directories = {
        "artifact.stage6.operator_leaf_promotion_certificate": {
            "single_layer",
            "board",
        },
        "artifact.stage6.single_layer_promotion_certificate": {"board"},
    }.get(str(current_promotion_artifact_id or ""), set())
    if not excluded_directories or not path_text:
        return False
    path = Path(path_text)
    if not path.is_absolute():
        path = run_dir / path
    try:
        relative = path.resolve().relative_to(
            (run_dir / "verification" / "semantic_testbench").resolve()
        )
    except (OSError, ValueError):
        return False
    return bool(relative.parts and relative.parts[0] in excluded_directories)


def build_promotion_evidence_binding(
    gate_summary: dict[str, Any],
    tool_results: list[dict[str, Any]],
    required_gates: list[str],
    run_dir: Path,
    selector_path: Any,
    snapshot_dir: Path | None = None,
    current_promotion_artifact_id: str | None = None,
) -> tuple[dict[str, Any], list[str]]:
    tool_by_log = {
        str(item.get("log_path")): item
        for item in tool_results
        if isinstance(item, dict) and item.get("log_path")
    }
    gate_rows = {
        str(row.get("name")): row
        for row in gate_summary.get("required_gates", [])
        if isinstance(row, dict) and row.get("name")
    }
    file_rows: list[dict[str, str]] = []
    fingerprints: list[dict[str, str]] = []
    errors: list[str] = []
    excluded_same_scope_promotion_certificates: list[dict[str, str]] = []
    scanned_documents: set[tuple[str, str]] = set()

    if snapshot_dir is not None:
        snapshot_dir.mkdir(parents=True, exist_ok=True)

    def add_bound_file(path: Path, gate: str, role: str) -> None:
        bound_path = path.resolve()
        source_path = ""
        if snapshot_dir is not None and role in {"gate_log", "produced_report", "evidence_artifact"}:
            source_path = str(bound_path)
            destination = snapshot_dir / f"{len(file_rows):04d}_{safe_id(gate)}_{path.name}"
            shutil.copy2(bound_path, destination)
            bound_path = destination.resolve()
        file_rows.append(
            {
                "gate": gate,
                "path": str(bound_path),
                "sha256": sha256_file(bound_path),
                "role": role,
                **({"source_path": source_path} if source_path else {}),
            }
        )

    def add_document_rows(rows: list[dict[str, str]]) -> None:
        for row in rows:
            if higher_scope_semantic_artifact_for_promotion(
                str(row.get("path") or ""),
                run_dir,
                current_promotion_artifact_id,
            ):
                continue
            source = Path(row["path"])
            if row.get("role") == "evidence_artifact" and snapshot_dir is not None:
                add_bound_file(source, row["gate"], row["role"])
            else:
                file_rows.append(row)

    def add_fingerprints(rows: list[dict[str, str]]) -> None:
        fingerprints.extend(
            row
            for row in rows
            if not higher_scope_semantic_artifact_for_promotion(
                str(row.get("artifact_path") or ""),
                run_dir,
                current_promotion_artifact_id,
            )
        )

    def scan_document(path: Path, gate: str, role: str) -> None:
        identity = (str(path.resolve()), gate)
        if identity in scanned_documents:
            return
        scanned_documents.add(identity)
        add_bound_file(path, gate, role)
        try:
            document = read_json(path)
        except Exception as exc:
            errors.append(f"{gate}: bound evidence JSON is unreadable: {path}: {exc}")
            return
        rows, found_fingerprints, found_errors = _promotion_binding_document_rows(
            document,
            document_path=path,
            gate=gate,
            run_dir=run_dir,
            current_promotion_artifact_id=current_promotion_artifact_id,
            excluded_same_scope_promotion_certificates=excluded_same_scope_promotion_certificates,
        )
        add_document_rows(rows)
        add_fingerprints(found_fingerprints)
        errors.extend(found_errors)
        for report in document.get("produced_reports", []):
            if not isinstance(report, dict):
                continue
            report_path = _resolve_evidence_file(run_dir, report.get("path"))
            if report_path is not None:
                scan_document(report_path, gate, "produced_report")

    selector_file = _resolve_evidence_file(run_dir, selector_path)
    for gate in required_gates:
        row = gate_rows.get(gate, {})
        log_paths = _as_file_paths(row.get("log_path"))
        if not log_paths:
            errors.append(f"{gate}: passing gate has no evidence log path")
            continue
        gate_had_file = False
        for value in log_paths:
            log_path = _resolve_evidence_file(run_dir, value)
            if log_path is None:
                errors.append(f"{gate}: evidence log is missing: {value}")
                continue
            gate_had_file = True
            scan_document(log_path, gate, "gate_log")
            tool = tool_by_log.get(str(log_path)) or tool_by_log.get(str(value))
            if isinstance(tool, dict):
                rows, found_fingerprints, found_errors = _promotion_binding_document_rows(
                    tool,
                    document_path=log_path,
                    gate=gate,
                    run_dir=run_dir,
                    current_promotion_artifact_id=current_promotion_artifact_id,
                    excluded_same_scope_promotion_certificates=excluded_same_scope_promotion_certificates,
                )
                add_document_rows(rows)
                add_fingerprints(found_fingerprints)
                errors.extend(found_errors)
        if not gate_had_file:
            errors.append(f"{gate}: no live evidence file could be bound")
        if selector_file is not None:
            add_bound_file(selector_file, gate, "selector_contract")

    deduplicated_rows = {
        (row["gate"], row["path"], row["sha256"], row["role"]): row
        for row in file_rows
    }
    deduplicated_fingerprints = {
        (
            row["name"],
            row["value"],
            row["source"],
            row.get("kind", ""),
            row.get("artifact_path", ""),
        ): row
        for row in fingerprints
    }
    deduplicated_exclusions = {
        (
            row["artifact_id"],
            row["path"],
            row["declared_sha256"],
            row["current_sha256"],
            row["role"],
            row["source"],
            row["reason"],
        ): row
        for row in excluded_same_scope_promotion_certificates
    }
    binding = {
        "schema_version": PROMOTION_EVIDENCE_BINDING_SCHEMA_VERSION,
        "required_gates": sorted(required_gates),
        "file_bindings": [deduplicated_rows[key] for key in sorted(deduplicated_rows)],
        "fingerprints": [
            deduplicated_fingerprints[key] for key in sorted(deduplicated_fingerprints)
        ],
        "excluded_same_scope_promotion_certificates": [
            deduplicated_exclusions[key] for key in sorted(deduplicated_exclusions)
        ],
    }
    binding["binding_sha256"] = promotion_evidence_binding_fingerprint(binding)
    return binding, errors


def write_stage6_promotion_certificates(
    state: dict[str, Any],
    run_dir: Path,
    gate_summary: dict[str, Any],
    maturity: dict[str, Any],
    gate_execution_plan: dict[str, Any],
    tool_results: list[dict[str, Any]],
    all_checks_pass: bool,
) -> tuple[dict[str, str], list[str]]:
    environment_groups, environment_blockers, _ = python_environment_group_fingerprints(tool_results)
    if maturity.get("status") != "pass" or not all_checks_pass or environment_blockers:
        return {}, list(environment_blockers)
    selector = stage6_selector_contract(state)
    statuses = gate_status_map(gate_summary)
    cert_dir = run_dir / "verification" / "certificates"
    cert_dir.mkdir(parents=True, exist_ok=True)
    candidate_dir = cert_dir / "candidates" / uuid.uuid4().hex
    candidate_dir.mkdir(parents=True, exist_ok=False)
    selected = set(str(gate) for gate in gate_execution_plan.get("selected_gates", []) if str(gate))
    written: dict[str, str] = {}
    binding_errors: list[str] = []
    specs = [
        (
            "operator_leaf_promotion_certificate",
            "artifact.stage6.operator_leaf_promotion_certificate",
            "operator_leaf_functional",
            candidate_dir / "operator_leaf_promotion_certificate.json",
        ),
        (
            "single_layer_promotion_certificate",
            "artifact.stage6.single_layer_promotion_certificate",
            "single_layer_functional",
            candidate_dir / "single_layer_promotion_certificate.json",
        ),
        (
            "multilayer_promotion_certificate",
            "artifact.stage6.multilayer_pipeline_promotion_certificate",
            "multilayer_pipeline_functional",
            candidate_dir / "multilayer_pipeline_promotion_certificate.json",
        ),
        (
            "board_axi_ddr_promotion_certificate",
            "artifact.stage6.board_axi_ddr_promotion_certificate",
            "axi_ddr_functional",
            candidate_dir / "board_axi_ddr_promotion_certificate.json",
        ),
    ]
    maturity_levels = {
        str(level.get("id")): str(level.get("status") or "")
        for level in maturity.get("levels", [])
        if isinstance(level, dict) and level.get("id")
    }
    maturity_required_gates = {
        str(level.get("id")): [
            str(row.get("name"))
            for row in level.get("required_gates", [])
            if isinstance(row, dict) and row.get("name")
        ]
        for level in maturity.get("levels", [])
        if isinstance(level, dict) and level.get("id")
    }
    for selector_key, artifact_id, level_id, path in specs:
        cert = selector.get(selector_key, {}) if isinstance(selector.get(selector_key), dict) else {}
        required_gates = [str(gate) for gate in cert.get("required_gates", []) if str(gate)]
        if not required_gates:
            required_gates = maturity_required_gates.get(level_id, [])
        if not required_gates or not selected.intersection(required_gates):
            continue
        gate_rows = [{"name": gate, "status": statuses.get(gate, "not_run")} for gate in required_gates]
        ready = maturity_levels.get(level_id) == "pass" and all(row["status"] == "pass" for row in gate_rows)
        if not ready:
            continue
        evidence_binding, evidence_errors = build_promotion_evidence_binding(
            gate_summary,
            tool_results,
            required_gates,
            run_dir,
            gate_execution_plan.get("selector_contract"),
            candidate_dir / "evidence" / safe_id(level_id),
            current_promotion_artifact_id=artifact_id,
        )
        if evidence_errors:
            binding_errors.extend(f"{level_id}: {error}" for error in evidence_errors)
            continue
        payload = {
            "schema_version": PROMOTION_CERTIFICATE_SCHEMA_VERSION,
            "status": "pass",
            "artifact_id": artifact_id,
            "level_id": level_id,
            "gate_execution_scope": stage6_gate_scope(),
            "required_gates": gate_rows,
            "evidence_contract": evidence_contract_for_level(level_id),
            "evidence_contract_fingerprint": certificate_contract_fingerprint(level_id, required_gates),
            "tool_environment_contract": tool_environment_contract(environment_groups),
            "source_result": str(run_dir / "verification" / "verification_result.json"),
            "source_gate_selector": gate_execution_plan.get("selector_contract"),
            "evidence_binding": evidence_binding,
            "policy": {
                "allows_next_hierarchical_layer": True,
                "does_not_claim_backend_or_board_readiness": level_id != "axi_ddr_functional",
                "does_not_claim_bitstream_or_board_runtime_readiness": True,
                "requires_current_trusted_rerun": True,
                "lower_layer_pass_evidence_is_reusable_not_absolute": True,
            },
        }
        if level_id == "operator_leaf_functional":
            payload["evidence_semantics"] = {
                "claim": (
                    "Every selected operator leaf passed target-model semantic comparison with real target weights, "
                    "auditable input provenance, and an independent expected output, and may be reused as lower-layer "
                    "evidence for single-transformer-layer verification."
                ),
                "does_not_claim": [
                    "full end-to-end model semantic correctness",
                    "single-transformer-layer integration correctness",
                    "board AXI/DDR wrapper correctness",
                    "backend, bitstream, or board-runtime readiness",
                ],
                "coverage_boundary": (
                    "Leaf evidence is checker-bound and tool-bound. It is not absolute: later CCTG or boundary-trace "
                    "evidence may challenge a passed leaf only when the contradiction names the lower-layer gate or module."
                ),
                "misdetection_policy": {
                    "higher_layer_trace_can_trigger_targeted_lower_layer_backtrack": True,
                    "do_not_reopen_without_challenged_gate_or_module": True,
                },
            }
        write_json(path, payload)
        written[artifact_id] = str(path)
    required_artifact = current_scope_required_promotion_artifact(stage6_gate_scope())
    if required_artifact and required_artifact not in written and not binding_errors:
        binding_errors.append(
            f"current scope did not produce required content-addressed certificate {required_artifact}"
        )
    return written, binding_errors


def check_scope_semantic_evidence(
    state: dict[str, Any],
    run_dir: Path,
    gate_execution_plan: dict[str, Any],
) -> tuple[str, str]:
    case_adapter = case_adapter_for_state(state, run_dir)
    paths = case_adapter.get("paths", {}) if isinstance(case_adapter.get("paths"), dict) else {}
    semantic_dir = run_dir / "verification" / "semantic_evidence"
    report_paths = {
        "operator_leaf_functional": resolve_case_path(
            run_dir,
            paths.get("operator_leaf_semantic_evidence") or semantic_dir / "operator_leaf.json",
        ),
        "single_layer_functional": resolve_case_path(
            run_dir,
            paths.get("single_layer_semantic_evidence") or semantic_dir / "single_layer.json",
        ),
        "multilayer_pipeline_functional": resolve_case_path(
            run_dir,
            paths.get("board_axi_ddr_semantic_evidence") or semantic_dir / "board_axi_ddr.json",
        ),
        "axi_ddr_functional": resolve_case_path(
            run_dir,
            paths.get("board_axi_ddr_semantic_evidence") or semantic_dir / "board_axi_ddr.json",
        ),
    }
    roles_by_level = {
        "operator_leaf_functional": [
            "weight_manifest_generate",
            "target_model_reference_generate",
            "semantic_testbench_generate",
            "leaf_functional_sim",
            "leaf_golden_compare",
            "operator_leaf_semantic_evidence",
        ],
        "single_layer_functional": [
            "weight_manifest_generate",
            "target_model_reference_generate",
            "semantic_testbench_generate",
            "single_layer_functional_sim",
            "single_layer_golden_compare",
            "single_layer_semantic_evidence",
        ],
        "multilayer_pipeline_functional": [
            "weight_manifest_generate",
            "target_model_reference_generate",
            "semantic_testbench_generate",
            "vcs_functional_sim",
            "vcs_evidence_analyzer",
            "board_semantic_evidence",
        ],
        "axi_ddr_functional": [
            "board_interface_discovery",
            "weight_manifest_generate",
            "target_model_reference_generate",
            "semantic_testbench_generate",
            "vcs_functional_sim",
            "vcs_evidence_analyzer",
            "board_semantic_evidence",
        ],
    }
    required_levels = selected_maturity_level_ids(gate_execution_plan) - {"contract_guided_debug_closure"}
    blockers: list[str] = []
    checked_reports: set[tuple[Path, str]] = set()
    for level_id in sorted(required_levels):
        for role in roles_by_level.get(level_id, []):
            spec = adapter_tool(case_adapter, role)
            if not spec:
                blockers.append(f"{level_id}: missing case-adapter role {role}")
                continue
            blockers.extend(
                f"{level_id}/{role}: {message}"
                for message in tool_evidence_contract_errors(role, spec)
            )
        report_path = report_paths.get(level_id)
        if report_path is None or (report_path, level_id) in checked_reports:
            continue
        checked_reports.add((report_path, level_id))
        blockers.extend(
            f"{level_id}: {message}"
            for message in semantic_evidence_report_errors(report_path, level_id)
        )
    if blockers:
        return "fail", "real-weight semantic evidence contract failed: " + "; ".join(blockers[:16])
    return "pass", f"real-weight semantic evidence passed for levels={sorted(required_levels)}"


def build_results(state: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    gate_execution_plan = build_stage6_gate_execution_plan(state, run_dir)
    checks = [
        ("sacg_reference_check", lambda: ("pass", "SACG references are valid") if not validate_references(state) else ("fail", "; ".join(validate_references(state)))),
        ("task_card_check", lambda: check_task_card(state)),
        ("model_config_check", lambda: check_model_config(state)),
        ("numeric_policy_check", lambda: check_numeric_policy(state)),
        ("template_coverage_check", lambda: check_template_coverage(state)),
        ("stream_plan_check", lambda: check_pipeline_plan(state)),
        ("parameter_binding_static_check", lambda: check_parameter_binding(state)),
        ("code_generation_manifest_static_check", lambda: check_code_generation_manifest(state)),
        ("codegen_package_static_check", lambda: check_code_generation_manifest(state)),
        ("verification_plan_static_check", lambda: check_verification_plan(state)),
        ("verification_artifact_contract_check", lambda: check_verification_artifact_contract(state)),
        ("verification_action_audit_check", lambda: check_stage6_action_audit(state)),
        ("hierarchical_verification_plan_check", lambda: check_hierarchical_verification_plan(state)),
        ("tool_protocol_check", lambda: check_tool_protocols(state)),
        ("memory_runtime_plan_check", lambda: check_memory_runtime_plan(state)),
        ("human_boundary_check", lambda: check_human_boundary(state)),
    ]
    results = []
    for checker, fn in checks:
        status, summary = fn()
        results.append({"checker": checker, "status": status, "summary": summary})
    if gate_execution_plan.get("status") != "pass":
        results.append(
            {
                "checker": "stage6_gate_execution_plan_check",
                "status": "fail",
                "summary": "; ".join(gate_execution_plan.get("blockers", [])) or "Stage7 gate execution plan is invalid",
            }
        )
    else:
        results.append(
            {
                "checker": "stage6_gate_execution_plan_check",
                "status": "pass",
                "summary": f"selected_gates={gate_execution_plan.get('selected_gates', [])}",
            }
        )
    tool_results = real_tool_evidence(state, run_dir, gate_execution_plan) if gate_execution_plan.get("status") == "pass" else []
    results.extend(tool_results)
    status, summary = check_case_functional_sim_preconditions(state, run_dir, gate_execution_plan)
    results.append({"checker": "case_functional_sim_precondition_check", "status": status, "summary": summary})
    status, summary = check_case_vcs_repair_diagnosis(state, run_dir, gate_execution_plan)
    results.append({"checker": "case_vcs_repair_diagnosis_check", "status": status, "summary": summary})
    status, summary = check_selected_gate_tool_execution(gate_execution_plan, tool_results)
    results.append({"checker": "stage6_selected_gate_tool_execution_check", "status": status, "summary": summary})
    status, summary = check_real_tool_log_consistency(tool_results)
    results.append({"checker": "real_tool_log_consistency_check", "status": status, "summary": summary})
    status, summary = check_python_environment_contract(tool_results)
    results.append({"checker": "python_environment_contract_check", "status": status, "summary": summary})
    status, summary = check_required_real_tool_evidence(tool_results)
    results.append({"checker": "required_real_tool_evidence_check", "status": status, "summary": summary})
    semantic_status, semantic_summary = check_scope_semantic_evidence(state, run_dir, gate_execution_plan)
    results.append(
        {
            "checker": "real_weight_semantic_evidence_check",
            "status": semantic_status,
            "summary": semantic_summary,
        }
    )
    hard_results = [item for item in results if item["status"] != "not_run"]
    gate_summary = build_hierarchical_gate_summary(state, tool_results, gate_execution_plan)
    maturity = build_hierarchical_maturity_report(state, gate_summary, gate_execution_plan)
    if semantic_status != "pass":
        maturity["status"] = "fail"
        maturity["current_scope_ready"] = False
        maturity.setdefault("blockers", []).append(semantic_summary)
    results.append(
        {
            "checker": "hierarchical_verification_maturity_check",
            "status": "pass" if maturity.get("status") == "pass" else "fail",
            "summary": (
                f"current Stage7 scope is closed; backend_ready={maturity.get('backend_ready')}"
                if maturity.get("status") == "pass"
                else "; ".join(maturity.get("blockers", [])[:8])
            ),
        }
    )
    board_bringup_readiness = build_board_bringup_readiness(state, run_dir)
    board_bringup_certificate = write_board_bringup_certificate(
        run_dir, board_bringup_readiness
    )
    payload = {
        "schema_version": "spatialaccagent.verification_result.v0",
        "stage": "verification",
        "status": "pass" if all(item["status"] == "pass" for item in hard_results) else "fail",
        "scope": "static_checks_and_real_tool_evidence",
        "execution_scope": verification_execution_scope(),
        "gate_execution_scope": stage6_gate_scope(),
        "gate_execution_plan": gate_execution_plan,
        "results": results,
        "hierarchical_gate_summary": gate_summary,
        "hierarchical_maturity": maturity,
        "board_bringup_readiness": board_bringup_readiness,
        "board_bringup_certificate": str(board_bringup_certificate),
    }
    promotion_certificates, promotion_certificate_errors = write_stage6_promotion_certificates(
        state,
        run_dir,
        gate_summary,
        maturity,
        gate_execution_plan,
        tool_results,
        all(item["status"] == "pass" for item in hard_results),
    )
    payload["promotion_certificates"] = promotion_certificates
    payload["results"].append(
        {
            "checker": "promotion_certificate_live_evidence_binding_check",
            "status": "pass" if not promotion_certificate_errors else "fail",
            "summary": (
                f"content-addressed promotion certificates={sorted(promotion_certificates)}"
                if not promotion_certificate_errors
                else "; ".join(promotion_certificate_errors[:16])
            ),
        }
    )
    hard_results = [item for item in payload["results"] if item["status"] != "not_run"]
    payload["status"] = "pass" if all(item["status"] == "pass" for item in hard_results) else "fail"
    payload["debug_closure"] = write_debug_closure_artifacts(
        state,
        run_dir,
        run_dir / "verification" / "debug_closure",
        verification_result=payload,
    )
    debug_localization = {}
    try:
        debug_localization = read_json(Path(str(payload["debug_closure"].get("failure_localization"))))
    except Exception:
        debug_localization = {}
    payload["hierarchical_repair_loop"] = build_repair_loop_report(
        verification_result=payload,
        debug_localization=debug_localization,
    )
    payload["retry_reconciliation_contract"] = stage6_retry_reconciliation_contract(
        state,
        payload,
    )
    loop_status = str(payload["hierarchical_repair_loop"].get("status") or "")
    out_of_order = payload["hierarchical_repair_loop"].get("out_of_order_executed_higher_layer_gates", [])
    payload["results"].append(
        {
            "checker": "hierarchical_repair_loop_order_check",
            "status": "fail" if out_of_order else "pass",
            "summary": (
                "hierarchical repair-loop order respected"
                if not out_of_order
                else f"higher-layer gates executed before current layer passed: {out_of_order}"
            ),
        }
    )
    payload["results"].append(
        {
            "checker": "hierarchical_repair_loop_state_check",
            "status": "pass" if loop_status in {"pass", "needs_repair"} else "fail",
            "summary": (
                f"current_layer={payload['hierarchical_repair_loop'].get('current_layer', {}).get('id')} "
                f"failure_kind={payload['hierarchical_repair_loop'].get('failure_kind')}"
            ),
        }
    )
    status, summary = check_debug_closure_artifacts(payload)
    payload["results"].append({"checker": "contract_guided_failure_localization_check", "status": status, "summary": summary})
    hard_results = [item for item in payload["results"] if item["status"] != "not_run"]
    payload["status"] = "pass" if all(item["status"] == "pass" for item in hard_results) else "fail"
    return payload


def stage6_retry_source_fingerprint(
    results: dict[str, Any],
    run_dir: Path,
    *,
    execution_scope: str,
    debug_layer: str,
) -> str:
    """Bind one open Stage7 retry to current semantic inputs, not audit churn."""

    board_identity_path = (
        run_dir / "verification" / "board_interface" / "board_source_identity.json"
    )
    board_identity = read_json(board_identity_path) if board_identity_path.is_file() else {}
    board_identity_projection = {
        key: board_identity.get(key)
        for key in (
            "selected_simulation_source_closure_sha256",
            "compute_slot_abi_sha256",
            "timing_contract_sha256",
            "axi_interfaces_sha256",
        )
    }
    source_paths = (
        run_dir / "input" / "model_config.json",
        run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json",
        run_dir
        / "verification"
        / "semantic_testbench"
        / "semantic_testbench_manifest.json",
    )
    input_hashes = {
        str(path.relative_to(run_dir)): sha256_file(path) if path.is_file() else None
        for path in source_paths
    }
    failed = [
        str(row.get("checker") or "")
        for row in results.get("results", [])
        if isinstance(row, dict) and row.get("status") == "fail"
    ]
    payload = {
        "schema_version": "spatialaccagent.stage6_retry_source_fingerprint.v1",
        "execution_scope": execution_scope,
        "debug_layer": debug_layer,
        "failed_checkers": sorted(set(failed)),
        "selected_gates": sorted(
            str(value)
            for value in results.get("gate_execution_plan", {}).get(
                "selected_gates", []
            )
            if str(value)
        )
        if isinstance(results.get("gate_execution_plan"), dict)
        else [],
        "board_identity": board_identity_projection,
        "input_hashes": input_hashes,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def update_sacg(source_state: Path, target_state: Path, result_path: Path, results: dict[str, Any]) -> str:
    copy_state(source_state, target_state)
    store = SACGStore(target_state)
    execution_scope = str(results.get("execution_scope") or verification_execution_scope())
    repair_loop = (
        results.get("hierarchical_repair_loop", {})
        if isinstance(results.get("hierarchical_repair_loop"), dict)
        else {}
    )
    current_layer = (
        repair_loop.get("current_layer", {})
        if isinstance(repair_loop.get("current_layer"), dict)
        else {}
    )
    memory_context = hierarchy_memory_context(
        verification_scope=execution_scope,
        debug_layer=current_layer.get("id"),
        failed_gates=repair_loop.get("failed_current_layer_gates", []),
        source_fingerprint_sha256=stage6_retry_source_fingerprint(
            results,
            run_dir_from_state(source_state),
            execution_scope=execution_scope,
            debug_layer=str(current_layer.get("id") or ""),
        ),
    )
    touched_constraints = SINGLE_LAYER_TOUCHED_CONSTRAINTS if execution_scope in {"single_layer", "single_layer_closure", "stage6_single_layer"} else TOUCHED_CONSTRAINTS
    if execution_scope in BOARD_AXI_DDR_CLOSURE_SCOPES:
        functional_constraint = "constraint.verification.functional_scope"
        add_constraint(
            store.state,
            functional_constraint,
            "verification",
            [],
            [],
            ["artifact.stage6.verification_result"],
            {
                "scope": execution_scope,
                "meaning": "Scoped Stage 6 board AXI/DDR wrapped-system closure with real functional simulation evidence; backend, bitstream, and board-runtime gates remain later-stage obligations.",
            },
        )
        touched_constraints = [functional_constraint]
    transition = store.declare_transition(
        action_type="verification",
        touched_nodes=[],
        touched_edges=[],
        touched_constraints=touched_constraints,
        note=f"Ran framework-level verification checks for scope={execution_scope}.",
        context=memory_context,
    )
    transition["required_checkers"] = stage6_current_scope_required_checkers(results)
    store.bind_artifact(
        "artifact.stage6.verification_result",
        str(result_path),
        "stage.verification_result",
        [],
        [],
        touched_constraints,
        transition["id"],
    )
    tool_logs = sorted((result_path.parent / "real_tools").glob("*.json"))
    if tool_logs:
        store.bind_artifact(
            "artifact.stage6.real_tool_results",
            str(result_path.parent / "real_tools"),
            "stage.real_tool_results",
            [],
            [],
            touched_constraints,
            transition["id"],
        )
    debug_closure = results.get("debug_closure", {}) if isinstance(results.get("debug_closure"), dict) else {}
    if debug_closure.get("failure_localization"):
        store.bind_artifact(
            "artifact.stage6.debug_closure",
            str(Path(str(debug_closure["failure_localization"])).parent),
            "stage.debug_closure",
            [],
            [],
            touched_constraints,
            transition["id"],
        )
    promotion_certificates = results.get("promotion_certificates", {}) if isinstance(results.get("promotion_certificates"), dict) else {}
    for artifact_id, path in sorted(promotion_certificates.items()):
        store.bind_artifact(
            str(artifact_id),
            str(path),
            "stage.promotion_certificate",
            [],
            [],
            touched_constraints,
            transition["id"],
        )
    board_bringup_certificate = Path(
        str(results.get("board_bringup_certificate") or "")
    )
    if board_bringup_certificate.is_file():
        store.bind_artifact(
            "artifact.stage6.board_bringup_certificate",
            str(board_bringup_certificate),
            "stage.board_bringup_certificate",
            [],
            [],
            touched_constraints,
            transition["id"],
        )
    def stage6_checker_constraints(checker: str) -> list[str]:
        if execution_scope in BOARD_AXI_DDR_CLOSURE_SCOPES:
            return touched_constraints
        if checker == "case_functional_sim_precondition_check":
            return ["constraint.verification.hierarchy", "constraint.tool.protocols", "constraint.deployment.board"]
        if checker == "case_vcs_repair_diagnosis_check":
            return ["constraint.verification.hierarchy", "constraint.tool.protocols"]
        if checker == "required_real_tool_evidence_check":
            return ["constraint.verification.hierarchy", "constraint.tool.protocols", "constraint.deployment.board"]
        if checker == "stage6_gate_execution_plan_check":
            return ["constraint.verification.hierarchy", "constraint.tool.protocols"]
        if checker == "verification_action_audit_check":
            return ["constraint.verification.plan", "constraint.verification.hierarchy"]
        if checker in {"verification_team_llm_check", "evidence_classifier_llm_check"}:
            return ["constraint.verification.plan", "constraint.verification.hierarchy"]
        if checker.startswith("real_tool."):
            return ["constraint.tool.protocols"]
        if checker in {"verification_artifact_contract_check", "human_boundary_check"}:
            return ["constraint.verification.plan"]
        return TOUCHED_CONSTRAINTS

    invariant_map = {
        inv.get("checker"): inv.get("id")
        for inv in store.state.get("invariants", [])
        if inv.get("checker")
    }
    existing_constraint_ids = {item.get("id") for item in store.state.get("constraints", [])}
    for item in results.get("results", []):
        checker = item.get("checker")
        if not checker or checker in invariant_map:
            continue
        constraints = [cid for cid in stage6_checker_constraints(str(checker)) if cid in existing_constraint_ids]
        if not constraints:
            constraints = [cid for cid in touched_constraints if cid in existing_constraint_ids]
        invariant_id = f"invariant.{checker}"
        add_invariant(store.state, invariant_id, str(checker), constraints)
        invariant_map[str(checker)] = invariant_id
    for item in results.get("results", []):
        if item["status"] == "not_run":
            continue
        invariant = invariant_map.get(item["checker"])
        if invariant:
            store.attach_evidence(
                checker=item["checker"],
                status=item["status"],
                invariant=invariant,
                constraints=[cid for inv in store.state["invariants"] if inv["id"] == invariant for cid in inv.get("constraints", [])],
                artifacts=["artifact.stage6.verification_result"],
                log_path=str(result_path),
                transition_id=transition["id"],
                summary=item["summary"],
            )
    if results["status"] == "pass":
        try:
            reconciliation = (
                results.get("sacg_reconciliation", {})
                if isinstance(results.get("sacg_reconciliation"), dict)
                else {}
            )
            if reconciliation:
                contract = (
                    reconciliation.get("contract", {})
                    if isinstance(reconciliation.get("contract"), dict)
                    else {}
                )
                contract_errors = stage6_reconciliation_contract_errors(
                    store.state,
                    contract,
                    verification_scope=execution_scope,
                    debug_layer=str(current_layer.get("id") or ""),
                )
                if contract_errors:
                    raise ValueError("; ".join(contract_errors))
            store.promote(transition["id"])
            stable_certificate_dir = result_path.parent / "certificates"
            stable_certificate_dir.mkdir(parents=True, exist_ok=True)
            for artifact_id, source in sorted(promotion_certificates.items()):
                stable_name = STABLE_PROMOTION_CERTIFICATE_NAMES.get(str(artifact_id))
                source_path = Path(str(source))
                if not stable_name or not source_path.is_file():
                    continue
                stable_path = stable_certificate_dir / stable_name
                shutil.copy2(source_path, stable_path)
                for artifact in store.state.get("artifacts", []):
                    if isinstance(artifact, dict) and artifact.get("id") == artifact_id:
                        artifact["path"] = str(stable_path)
                results.setdefault("stable_promotion_certificates", {})[str(artifact_id)] = str(stable_path)
            if reconciliation:
                contract = reconciliation["contract"]
                store.reconcile_retry_and_barriers(
                    transition["id"],
                    target_stage="stage6.verification",
                    superseded_artifacts=STAGE6_RECONCILED_ARTIFACTS,
                    retry_request_ids=contract.get("eligible_retry_request_ids", []),
                    contamination_barrier_ids=contract.get(
                        "eligible_contamination_barrier_ids", []
                    ),
                    reason=(
                        f"current Stage6 {execution_scope} candidate passed real tools and produced "
                        "a content-addressed promotion certificate"
                    ),
                )
        except ValueError as exc:
            checker = "sacg_promotion_gate_check"
            summary = str(exc)
            results["status"] = "fail"
            results.setdefault("results", []).append({"checker": checker, "status": "fail", "summary": summary})
            if checker not in invariant_map:
                invariant_id = f"invariant.{checker}"
                constraints = [cid for cid in touched_constraints if cid in existing_constraint_ids]
                add_invariant(store.state, invariant_id, checker, constraints)
                invariant_map[checker] = invariant_id
            invariant = invariant_map.get(checker)
            if invariant:
                store.attach_evidence(
                    checker=checker,
                    status="fail",
                    invariant=invariant,
                    constraints=[cid for inv in store.state["invariants"] if inv["id"] == invariant for cid in inv.get("constraints", [])],
                    artifacts=["artifact.stage6.verification_result"],
                    log_path=str(result_path),
                    transition_id=transition["id"],
                    summary=summary,
                )
            write_json(result_path, results)
    if results["status"] != "pass":
        store.reject(transition["id"], "one or more framework static checks failed")
        failed = [item for item in results.get("results", []) if item.get("status") == "fail"]
        summaries = [f"{item.get('checker')}: {item.get('summary')}" for item in failed[:8]]
        store.record_failure_lesson(
            stage="stage6.verification",
            failure_class="verification_real_tool_or_gate",
            summary="; ".join(summaries) or "Stage6 verification failed",
            violated_constraints=touched_constraints,
            artifacts=["artifact.stage6.verification_result"],
            recommended_action="Use contract-guided debug closure first: localize the failing transaction to a boundary/root-candidate slice, then repair only that causal slice or backtrack to Stage5 if the verification contract is incomplete.",
            retry_scope="stage6_or_stage6_backtrack",
            context=memory_context,
        )
        store.record_retry_request(
            stage="stage6.verification",
            reason="Stage6 verification result did not pass all selected real-tool/checker gates",
            target_stage="stage6.verification",
            required_inputs=["artifact.stage6.verification_artifact_contract", "artifact.stage6.llm_action_audit"],
            blocked_artifacts=["artifact.stage6.verification_result"],
            context=memory_context,
        )
        gate_plan = results.get("gate_execution_plan", {}) if isinstance(results.get("gate_execution_plan"), dict) else {}
        if gate_plan.get("status") != "pass":
            store.record_backtrack_request(
                stage="stage6.verification",
                target_stage="stage6.verification_artifacts",
                reason="Stage6 could not execute the selected gates because the Stage5 verification contract is incomplete",
                missing_or_invalid_contracts=gate_plan.get("blockers", []),
                evidence=["artifact.stage6.verification_result", "artifact.stage6.verification_artifact_contract"],
                context=memory_context,
            )
    store.record_stage_outcome(
        stage="stage6.verification",
        status="ready" if results["status"] == "pass" else "needs_repair",
        transition_id=transition["id"],
        summary=f"Stage6 execution_scope={execution_scope} status={results.get('status')}",
        errors=[f"{item.get('checker')}: {item.get('summary')}" for item in results.get("results", []) if item.get("status") == "fail"],
        artifacts=["artifact.stage6.verification_result"],
        next_actions=[] if results["status"] == "pass" else ["run the Stage6 repair loop or backtrack to Stage5 when the gate DAG/tool protocol is incomplete"],
        retryable=results["status"] != "pass",
        context=memory_context,
    )
    store.save()
    return transition["id"]


def run_verification(args: argparse.Namespace) -> tuple[Path, dict[str, Any]]:
    source_state = args.sacg_state.resolve()
    run_dir = run_dir_from_state(source_state)
    out_dir = run_dir / "verification"
    result_path = out_dir / "verification_result.json"
    state_path = out_dir / "sacg_state.json"
    report_path = out_dir / "verification_report.json"

    source_data = read_json(source_state)
    results = build_results(source_data, run_dir)
    write_json(result_path, results)
    deterministic_failure_route = exact_failed_stage6_route(results)
    team_error = None
    if deterministic_failure_route:
        design_team_summary = {
            "status": "no_split",
            "errors": [],
            "subtask_count": 0,
            "completed_subtasks": 0,
            "decomposition_source": "deterministic_real_tool_failure",
        }
        team_paths = {"team_subtask_plan": None, "team_aggregate": None}
    else:
        try:
            design_team_summary, team_paths = run_verification_review_team(
                source_data,
                results,
                out_dir,
                source_sacg_state=source_state,
            )
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
    if deterministic_failure_route:
        llm = deterministic_failed_stage6_record(results, out_dir)
    else:
        try:
            llm = run_stage_agent(
                agent="evidence_classifier_agent",
                stage="verification",
                task=(
                    "Make the authoritative Stage7 evidence decision from checker and real-tool evidence, SACG/CCTG state, "
                    "and the conditional specialist review when one was triggered. Classify cross-layer risks and propose "
                    "only bounded next checks; deterministic pass evidence cannot be replaced by role consensus."
                ),
                inputs={
                    "verification_result": results,
                    "design_team": design_team_summary,
                    "source_sacg_state": str(source_state),
                },
                out_dir=out_dir,
                fallback_summary="Verification results collected by deterministic checkers and tool protocols.",
            )
        except Exception as exc:
            llm_error = str(exc)
            llm_path = out_dir / "llm" / "evidence_classifier_agent_result.json"
            if llm_path.exists():
                try:
                    existing_llm = read_json(llm_path)
                except Exception:
                    existing_llm = {}
            else:
                existing_llm = {}
            llm_output = existing_llm.get("output") if isinstance(existing_llm.get("output"), dict) else {
                "schema_version": "spatialaccagent.stage_worker_output.v0",
                "agent": "evidence_classifier_agent",
                "stage": "verification",
                "status": "unavailable",
                "summary": "LLM evidence classifier unavailable; Stage7 must remain blocked until an LLM review succeeds.",
                "sacg_focus": {"nodes": [], "edges": [], "constraints": TOUCHED_CONSTRAINTS, "artifacts": ["artifact.stage6.verification_result"]},
                "observations": [f"LLM classifier failed: {llm_error}"],
                "risks": ["LLM classifier outage blocks Stage7 promotion; deterministic tool logs alone are not an agentic design decision."],
                "proposed_actions": ["Rerun Stage7 with the configured LLM provider available, preserving the same Stage6 gate/action contract."],
                "executable_actions": [],
                "approval_required_for": [],
            }
            llm = {
                "schema_version": "spatialaccagent.stage_worker_record.v0",
                "agent": "evidence_classifier_agent",
                "stage": "verification",
                "mode": "llm",
                "result_path": str(llm_path),
                "used_fallback": True,
                "error": existing_llm.get("error") or llm_error,
                "output": llm_output,
            }
            if not existing_llm:
                write_json(llm_path, llm)
    agent_gate_errors = append_stage6_agent_gate_checks(results, design_team_summary, llm)
    write_json(result_path, results)
    transition_id = update_sacg(source_state, state_path, result_path, results)
    write_json(result_path, results)
    failed = [item for item in results["results"] if item["status"] == "fail"]
    pending = [item["summary"] for item in results["results"] if item["status"] == "not_run"]
    report_status = "ready" if results["status"] == "pass" else "needs_repair"
    report = {
        "schema_version": "spatialaccagent.verification_report.v0",
        "stage": "verification",
        "status": report_status,
        "source_sacg_state": str(source_state),
        "outputs": {
            "verification_result": str(result_path),
            "sacg_state": str(state_path),
            "llm_agent": llm["result_path"],
            **team_paths,
        },
        "llm_agent": llm["output"],
        "llm_executable_actions": llm["output"].get("executable_actions", []),
        "llm_error": llm_error,
        "design_team": design_team_summary,
        "llm_review_routing": {
            "mode": validation_llm_team_mode(),
            "specialist_trigger": verification_specialist_trigger(results),
            "primary_agent_required": not deterministic_failure_route,
            "deterministic_exact_failure_route": deterministic_failure_route,
            "fixed_decomposer_and_multi_specialist_fanout_removed": validation_llm_team_mode() == "conditional",
        },
        "team_executable_actions": design_team_summary.get("executable_actions", []),
        "team_error": team_error,
        "agent_gate_errors": agent_gate_errors,
        "result_status": results["status"],
        "gate_execution_scope": results.get("gate_execution_scope"),
        "gate_execution_plan": results.get("gate_execution_plan"),
        "hierarchical_gate_summary": results.get("hierarchical_gate_summary"),
        "hierarchical_repair_loop": results.get("hierarchical_repair_loop"),
        "failed_checks": [
            {"checker": item.get("checker"), "summary": item.get("summary")}
            for item in failed
        ],
        "pending_evidence": pending,
        "sacg_transition_id": transition_id,
        "errors": [] if results["status"] == "pass" else [
            f"{item.get('checker')}: {item.get('summary')}" for item in failed
        ],
    }
    write_json(report_path, report)
    return report_path, report


def main(argv: list[str] | None = None) -> int:
    return run_sacg_stage("Verification execution stage", run_verification, argv)


if __name__ == "__main__":
    raise SystemExit(main())
