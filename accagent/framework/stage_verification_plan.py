"""Create verification artifact/checker plan."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from accagent.framework.case_adapter import (
    adapter_tool,
    build_case_adapter,
    gate_name,
    generic_required_gate_names,
    planned_evidence_paths_from_adapter,
    refresh_builtin_case_adapter,
)
from accagent.framework.debug_closure import build_boundary_contracts
from accagent.framework.repair_loop import hierarchical_debug_loop_contract
from accagent.framework.sacg_store import SACGStore
from accagent.framework.sacg_utils import (
    add_constraint,
    add_invariant,
    artifact_path,
    copy_state,
    read_json,
    run_dir_from_state,
    sacg_memory_summary,
    safe_id,
    write_json,
)
from accagent.framework.stage_entry import run_sacg_stage
from accagent.framework.llm_action_audit import build_audit_from_outputs
from accagent.framework.llm_io_quality import build_quality_report, rows_from_stage_records
from accagent.framework.stage_llm import run_stage_agent
from accagent.framework.stage_pipeline import normalize_attention_contract
from accagent.framework.stage_team import (
    compact_prompt_value,
    compact_prompt_text,
    run_design_team,
    team_failure_errors,
    team_summary,
)
from accagent.framework.verification_evidence_contract import (
    EVIDENCE_CONTRACT_VERSION,
    evidence_contract_for_level,
    tool_evidence_contract_errors,
)


TOUCHED_CONSTRAINTS = [
    "constraint.verification.plan",
    "constraint.verification.hierarchy",
    "constraint.verification.artifacts",
]

STAGE6_PROMOTION_CHECKERS = [
    "hierarchical_verification_plan_check",
    "human_boundary_check",
    "llm_io_quality_check",
    "required_real_tool_evidence_check",
    "verification_action_audit_check",
    "verification_artifact_contract_check",
    "verification_plan_static_check",
]

REFERENCED_CONSTRAINTS = [
    "constraint.task.goal",
    "constraint.model.decoder",
    "constraint.shape.model",
    "constraint.numeric.policy",
    "constraint.template.library",
    "constraint.parameter.binding",
    "constraint.codegen.package",
    "constraint.pipeline.structure",
    "constraint.stream.order",
    "constraint.beat.pipeline",
    "constraint.memory.board",
    "constraint.runtime.board",
    "constraint.tool.protocols",
    "constraint.deployment.board",
    "constraint.human.boundary",
    *TOUCHED_CONSTRAINTS,
]


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


def leaf_module_checks(
    stage: dict[str, Any], model_config: dict[str, Any] | None = None
) -> list[str]:
    """Return generated RTL modules required by one model-derived leaf stage."""

    kind = str(stage.get("kind", ""))
    op = str(stage.get("op", ""))
    model_config = model_config if isinstance(model_config, dict) else {}
    norm = model_config.get("norm", {})
    norm = norm if isinstance(norm, dict) else {}
    attention = model_config.get("attention", {})
    attention = attention if isinstance(attention, dict) else {}
    position_encoding = attention.get("position_encoding", {})
    position_encoding = (
        position_encoding if isinstance(position_encoding, dict) else {}
    )
    mlp = model_config.get("mlp", {})
    mlp = mlp if isinstance(mlp, dict) else {}

    if kind == "norm":
        return ["RMSNorm"] if norm.get("type") == "rms_norm" else ["VectorNorm"]
    if kind == "attention":
        checks = ["QKVProjection"]
        attention_kind = str(attention.get("kind") or "mha").lower()
        checks.append(
            {
                "gqa": "AttentionGQA",
                "mqa": "AttentionMQA",
            }.get(attention_kind, "Attention")
        )
        if position_encoding.get("type") == "rope":
            checks.append("RoPE")
        checks.append("Linear_1")
        return checks
    if kind == "residual":
        return ["ResidualAdd", "PhysicalStreamFifo"]
    if mlp.get("type") == "dense":
        if kind == "mlp":
            return ["DenseFFN"]
        if kind == "activation":
            return ["Activation"]
    if op == "mlp_gate_proj":
        return ["GatedMLP.gate:Linear"]
    if op == "mlp_up_proj":
        return ["GatedMLP.up:Linear"]
    if op == "mlp_down_proj":
        return ["GatedMLP.down:Linear"]
    if op == "activation_mul" or kind in {"activation", "activation_mul"}:
        return ["GatedMLP.act:Activation", "GatedMLP.mul:ElementwiseMul"]
    if kind == "mlp":
        return ["GatedMLP.*:Linear"]
    return []


def build_hierarchical_verification_plan(
    pipeline: dict[str, Any],
    case_adapter: dict[str, Any],
    model_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    stages = pipeline.get("stages", [])
    stage_leaf_gate = gate_name(case_adapter, "stage_leaf_static")
    leaf_functional_gate = gate_name(case_adapter, "leaf_functional")
    leaf_golden_gate = gate_name(case_adapter, "leaf_golden_compare")
    operator_leaf_semantic_gate = gate_name(case_adapter, "operator_leaf_semantic_evidence")
    boundary_contract_gate = gate_name(case_adapter, "boundary_contract")
    real_weight_gate = gate_name(case_adapter, "real_weight_artifacts")
    target_model_reference_gate = gate_name(case_adapter, "target_model_reference")
    semantic_testbench_gate = gate_name(case_adapter, "semantic_testbench")
    tb_scaffold_gate = gate_name(case_adapter, "tb_scaffold")
    single_layer_gate = gate_name(case_adapter, "single_layer_kernel")
    single_layer_functional_gate = gate_name(case_adapter, "single_layer_functional")
    single_layer_golden_gate = gate_name(case_adapter, "single_layer_golden_compare")
    single_layer_semantic_gate = gate_name(case_adapter, "single_layer_semantic_evidence")
    multilayer_gate = gate_name(case_adapter, "multilayer_pipeline")
    multilayer_functional_gate = gate_name(case_adapter, "multilayer_functional")
    pipeline_deadlock_gate = gate_name(case_adapter, "pipeline_deadlock")
    axi_gate = gate_name(case_adapter, "axi_ddr_interface")
    axi_protocol_gate = gate_name(case_adapter, "axi_protocol")
    ddr_roundtrip_gate = gate_name(case_adapter, "ddr_image_roundtrip")
    board_semantic_gate = gate_name(case_adapter, "board_semantic_evidence")
    board_bringup_gate = gate_name(case_adapter, "board_bringup")
    functional_gate = gate_name(case_adapter, "functional_sim")
    board_discovery_gate = gate_name(case_adapter, "board_interface_discovery")
    vivado_synth_gate = gate_name(case_adapter, "vivado_synthesis")
    vivado_impl_gate = gate_name(case_adapter, "vivado_implementation")
    runtime_abi_gate = gate_name(case_adapter, "runtime_abi")
    runtime_gate = gate_name(case_adapter, "runtime_bitstream")
    board_gate = gate_name(case_adapter, "board_runtime")
    stage_agents = [
        {
            "id": f"verify.{stage['stage_id']}",
            "stage_id": stage["stage_id"],
            "role": f"{stage['stage_id']} verification agent",
            "objective": "Validate one pipeline stage boundary before merge.",
            "parallel_group": 0,
            "op": stage.get("op"),
            "kind": stage.get("kind"),
            "input_shape": stage.get("input_shape", {}),
            "output_shape": stage.get("output_shape", {}),
            "module_checks": leaf_module_checks(stage, model_config),
            "required_evidence": [
                real_weight_gate,
                target_model_reference_gate,
                semantic_testbench_gate,
                stage_leaf_gate,
                boundary_contract_gate,
                leaf_functional_gate,
                leaf_golden_gate,
                operator_leaf_semantic_gate,
            ],
            "acceptance": [
                "declared modules exist in generated RTL",
                "ready/valid/last boundary is statically identifiable",
                "transfer shape matches the pipeline plan",
                "operator-local functional simulation passes with real/generated boundary stimuli",
                "operator-local golden comparison passes under the numeric policy and tolerance contract",
                "boundary trace schema can identify failing transactions for causal debug closure",
            ],
        }
        for stage in stages
    ]
    stage_by_op = {stage.get("op"): stage.get("stage_id") for stage in stages}
    stage_ids = [stage["stage_id"] for stage in stages]
    merge_agents = [
        {
            "id": "merge.self_attention",
            "role": "self-attention merge agent",
            "parallel_group": 1,
            "depends_on": [
                stage_by_op.get("rms_norm_1"),
                stage_by_op.get("self_attention"),
                stage_by_op.get("residual_add_1"),
            ],
            "required_evidence": [target_model_reference_gate, semantic_testbench_gate, stage_leaf_gate, leaf_functional_gate, leaf_golden_gate, operator_leaf_semantic_gate],
        },
        {
            "id": "merge.mlp",
            "role": "MLP merge agent",
            "parallel_group": 1,
            "depends_on": [
                stage_by_op.get("rms_norm_2"),
                stage_by_op.get("mlp_gate_proj"),
                stage_by_op.get("mlp_up_proj"),
                stage_by_op.get("activation_mul"),
                stage_by_op.get("mlp_down_proj"),
                stage_by_op.get("residual_add_2"),
            ],
            "required_evidence": [target_model_reference_gate, semantic_testbench_gate, stage_leaf_gate, leaf_functional_gate, leaf_golden_gate, operator_leaf_semantic_gate],
        },
        {
            "id": "merge.single_decoder_block",
            "role": "single block merge agent",
            "parallel_group": 2,
            "depends_on": ["merge.self_attention", "merge.mlp"],
            "required_evidence": [
                real_weight_gate,
                target_model_reference_gate,
                semantic_testbench_gate,
                tb_scaffold_gate,
                single_layer_gate,
                single_layer_functional_gate,
                single_layer_golden_gate,
                single_layer_semantic_gate,
            ],
        },
        {
            "id": "merge.multi_layer_pipeline",
            "role": "multi-layer pipeline agent",
            "parallel_group": 3,
            "depends_on": ["merge.single_decoder_block"],
            "required_evidence": [board_discovery_gate, multilayer_gate],
        },
        {
            "id": "merge.axi_ddr_runtime",
            "role": "AXI DDR runtime agent",
            "parallel_group": 4,
            "depends_on": ["merge.multi_layer_pipeline"],
            "required_evidence": [
                board_discovery_gate,
                axi_gate,
                functional_gate,
                multilayer_functional_gate,
                pipeline_deadlock_gate,
                axi_protocol_gate,
                ddr_roundtrip_gate,
                board_semantic_gate,
            ],
        },
        {
            "id": "merge.runtime_bitstream",
            "role": "runtime bitstream and board agent",
            "parallel_group": 5,
            "depends_on": ["merge.axi_ddr_runtime"],
            "required_evidence": [vivado_synth_gate, vivado_impl_gate, runtime_gate, runtime_abi_gate, board_gate],
        },
    ]
    for item in merge_agents:
        item["depends_on"] = [value for value in item["depends_on"] if value]
    evidence_gates = [
        {
            "name": real_weight_gate,
            "required": True,
            "description": "The complete target checkpoint tensor catalog and hashes are available; sampled/default weights are not acceptance evidence.",
        },
        {
            "name": target_model_reference_gate,
            "required": True,
            "description": "The real target model runs on the reproducible random input and emits independent per-operator, single-layer, and all-target-Transformer-block boundary golden tensors.",
        },
        {
            "name": semantic_testbench_gate,
            "required": True,
            "description": "Generated semantic testbenches encode the numeric policy and prove that the DUT consumes every required checkpoint-derived weight tensor.",
        },
        {
            "name": stage_leaf_gate,
            "required": True,
            "description": "Generated case RTL exposes expected leaf stage modules and stream boundaries.",
        },
        {
            "name": boundary_contract_gate,
            "required": True,
            "description": "Each module boundary has a case-adapter-independent contract and trace schema for failure slicing.",
        },
        {
            "name": leaf_functional_gate,
            "required": True,
            "description": "Every spatial operator leaf module has independent functional simulation evidence before any layer merge.",
        },
        {
            "name": leaf_golden_gate,
            "required": True,
            "description": "Every spatial operator leaf module has a golden comparison or equivalent numeric contract evidence.",
        },
        {
            "name": operator_leaf_semantic_gate,
            "required": True,
            "description": "One checker-bound semantic aggregate reconciles all operator-leaf simulator, golden, real-weight-consumption, and immutable identity evidence before promotion.",
        },
        {
            "name": tb_scaffold_gate,
            "required": True,
            "description": "A reproducible testbench/RTL scaffold loads declared manifests and is hashable before functional simulation.",
        },
        {
            "name": single_layer_gate,
            "required": True,
            "description": "Verified leaf modules are merged into one transformer layer/block kernel before multilayer or board wrapper gates.",
        },
        {
            "name": single_layer_functional_gate,
            "required": True,
            "description": "A single transformer layer/block kernel passes real functional verification before multi-layer pipeline verification.",
        },
        {
            "name": single_layer_golden_gate,
            "required": True,
            "description": "The single transformer layer/block has golden comparison or declared numeric-tolerance evidence.",
        },
        {
            "name": single_layer_semantic_gate,
            "required": True,
            "description": "One checker-bound semantic aggregate reconciles the connected single-layer simulator, golden, weight-consumption, and immutable identity evidence before promotion.",
        },
        {
            "name": board_discovery_gate,
            "required": True,
            "description": "A board-interface LLM agent interprets Vivado-exported sample-project facts and emits a hash-bound compute-slot, AXI, clock/reset/calibration, and recursive simulation-closure contract before board RTL generation.",
        },
        {
            "name": multilayer_gate,
            "required": True,
            "description": "A model-adaptive multi-layer scheduler and board-slot integration wrapper is generated only after the exact sample-project contract is available.",
        },
        {
            "name": axi_gate,
            "required": True,
            "description": "The multi-layer kernel is wrapped with the target board AXI/DDR runtime interface before simulation.",
        },
        {
            "name": functional_gate,
            "required": True,
            "description": "A real board-wrapped simulator runs with the immutable random input, complete Transformer-block weights, target-model boundary golden, and runtime artifacts.",
        },
        {
            "name": multilayer_functional_gate,
            "required": True,
            "description": "Multi-layer functionality is classified from the real board-wrapped simulator evidence.",
        },
        {
            "name": pipeline_deadlock_gate,
            "required": True,
            "description": "Pipeline liveness and deadlock status are classified from real simulator counters and traces.",
        },
        {
            "name": axi_protocol_gate,
            "required": True,
            "description": "AXI protocol, order, and address behavior is classified from real simulator evidence.",
        },
        {
            "name": ddr_roundtrip_gate,
            "required": True,
            "description": "Real input, weight, and output DDR image transfers are classified from real simulator evidence.",
        },
        {
            "name": board_semantic_gate,
            "required": True,
            "description": "One board semantic aggregate reconciles the canonical run, exact wrapper identity, all third-layer classifiers, real weights, and target-model output before backend release.",
        },
        {
            "name": vivado_synth_gate,
            "required": True,
            "description": "Vivado synthesis evidence is collected for the runtime/board shell target.",
        },
        {
            "name": vivado_impl_gate,
            "required": True,
            "description": "Vivado implementation, timing, route, and DRC evidence are collected before runtime bitstream promotion.",
        },
        {
            "name": runtime_abi_gate,
            "required": True,
            "description": "Runtime ABI, DDR layout, register map, and bitstream artifacts are cross-checked before board runtime.",
        },
        {
            "name": runtime_gate,
            "required": True,
            "description": "Vivado produces a board-runtime case bitstream, not only a standalone core bitstream.",
        },
        {
            "name": "board_runtime",
            "required": True,
            "description": "Board runtime executes the generated bitstream with real packed inputs/weights and emits valid output bytes; liveness-only smoke is not final acceptance.",
        },
    ]
    return {
        "schema_version": "spatialaccagent.hierarchical_verification.v0",
        "strategy": "three_layer_repair_loop: operator_leaf_modules -> single_transformer_layer_kernel -> board_axi_ddr_wrapped_system",
        "debug_loop_contract": hierarchical_debug_loop_contract(),
        "stage_agents": stage_agents,
        "merge_agents": merge_agents,
        "evidence_gates": evidence_gates,
        "policy": {
            "stage_agents_parallel": True,
            "debug_layers": [
                "operator_leaf_modules",
                "single_transformer_layer_kernel",
                "board_axi_ddr_wrapped_system",
            ],
            "merge_order": "operator_leaf_modules_then_single_transformer_layer_kernel_then_board_axi_ddr_wrapped_system_then_backend",
            "do_not_claim_final_pass_with_pending_or_failed_required_gate": True,
            "do_not_use_default_generated_weights_as_real_weight_evidence": True,
            "strict_bottom_up_functional_closure_before_backend": True,
            "operator_leaf_functional_before_single_layer": True,
            "single_layer_functional_before_board_axi_ddr_wrapper": True,
            "board_axi_ddr_functional_before_backend": True,
            "contract_guided_debug_closure_required_for_repair": True,
            "lower_layer_pass_evidence_is_reusable_not_absolute": True,
            "higher_layer_trace_can_trigger_targeted_lower_layer_backtrack": True,
            "do_not_reopen_passed_lower_layer_without_contradicting_boundary_trace": True,
        },
        "maturity_contract": {
            "schema_version": "spatialaccagent.hierarchical_verification_maturity.v0",
            "promotion_rule": (
                "A later verification layer may not execute or promote until every earlier layer has pass evidence. "
                "That pass evidence is reusable but not absolute: a current-layer CCTG/boundary trace may trigger "
                "targeted lower-layer backtrack only when it explicitly contradicts the earlier pass evidence and binds "
                "the contradiction to a challenged gate or module."
            ),
            "levels": [
                {
                    "id": "operator_leaf_functional",
                    "debug_layer": "operator_leaf_modules",
                    "required_before": "single_transformer_layer_kernel",
                    "required_gates": [
                        real_weight_gate,
                        target_model_reference_gate,
                        semantic_testbench_gate,
                        stage_leaf_gate,
                        boundary_contract_gate,
                        leaf_functional_gate,
                        leaf_golden_gate,
                        operator_leaf_semantic_gate,
                    ],
                    "required_tool_roles": [
                        "weight_manifest_generate",
                        "target_model_reference_generate",
                        "semantic_testbench_generate",
                        "stage_leaf_static",
                        "boundary_contract_check",
                        "leaf_functional_sim",
                        "leaf_golden_compare",
                        "operator_leaf_semantic_evidence",
                    ],
                },
                {
                    "id": "single_layer_functional",
                    "debug_layer": "single_transformer_layer_kernel",
                    "required_before": "board_axi_ddr_wrapped_system",
                    "required_gates": [tb_scaffold_gate, single_layer_gate, single_layer_functional_gate, single_layer_golden_gate, single_layer_semantic_gate],
                    "required_tool_roles": [
                        "single_layer_kernel",
                        "single_layer_functional_sim",
                        "single_layer_golden_compare",
                        "single_layer_semantic_evidence",
                    ],
                },
                {
                    "id": "multilayer_pipeline_functional",
                    "debug_layer": "board_axi_ddr_wrapped_system",
                    "required_before": "board_axi_ddr_wrapped_system_promotion",
                    "required_gates": [multilayer_gate, functional_gate, multilayer_functional_gate, pipeline_deadlock_gate],
                    "required_tool_roles": [
                        "multilayer_pipeline",
                        "vcs_functional_sim",
                        "vcs_evidence_analyzer",
                        "multilayer_functional_sim",
                        "pipeline_deadlock_check",
                    ],
                    "note": "Third-layer internal view: multi-layer ordering and liveness are derived from the real board-wrapped simulator evidence.",
                },
                {
                    "id": "axi_ddr_functional",
                    "debug_layer": "board_axi_ddr_wrapped_system",
                    "required_before": "backend_board",
                    "required_gates": [board_discovery_gate, axi_gate, functional_gate, axi_protocol_gate, ddr_roundtrip_gate, board_semantic_gate],
                    "required_tool_roles": [
                        "board_interface_discovery",
                        "axi_ddr_interface",
                        "vcs_functional_sim",
                        "vcs_evidence_analyzer",
                        "deadlock_axi_check",
                        "axi_protocol_check",
                        "ddr_image_roundtrip",
                        "board_semantic_evidence",
                    ],
                    "note": "Third-layer internal view: AXI/DDR protocol and transfers are derived from the same real board-wrapped simulator evidence before backend promotion.",
                },
                {
                    "id": "contract_guided_debug_closure",
                    "required_before": "repair_or_backend_handoff",
                    "required_gates": [boundary_contract_gate],
                    "required_tool_roles": ["boundary_contract_check", "failure_slice_localization", "boundary_trace_rerun", "targeted_replay"],
                },
            ],
        },
    }


def build_verification_plan(state: dict[str, Any]) -> dict[str, Any]:
    pipeline = read_json(artifact_path(state, "artifact.stage3.pipeline_plan"))
    run_dir = Path(str(artifact_path(state, "artifact.stage3.pipeline_plan"))).resolve().parents[1]
    case_adapter = case_adapter_for_state(state, run_dir)
    model_config = read_json(artifact_path(state, "artifact.input.model_config"))
    hierarchy = build_hierarchical_verification_plan(
        pipeline, case_adapter, model_config
    )
    return {
        "schema_version": "spatialaccagent.verification_plan.v0",
        "stage": "verification_artifacts",
        "status": "ready",
        "checker_plan": [
            {"checker": "task_card_check", "constraints": ["constraint.task.goal"]},
            {"checker": "model_config_check", "constraints": ["constraint.model.decoder", "constraint.shape.model"]},
            {"checker": "numeric_policy_check", "constraints": ["constraint.numeric.policy"]},
            {"checker": "template_coverage_check", "constraints": ["constraint.template.library", "constraint.codegen.package"]},
            {"checker": "stream_plan_check", "constraints": ["constraint.stream.order", "constraint.beat.pipeline"]},
            {"checker": "parameter_binding_static_check", "constraints": ["constraint.parameter.binding"]},
            {"checker": "code_generation_manifest_static_check", "constraints": ["constraint.codegen.package"]},
            {"checker": "codegen_package_static_check", "constraints": ["constraint.codegen.package"]},
            {"checker": "verification_plan_static_check", "constraints": ["constraint.verification.plan"]},
            {"checker": "tool_protocol_check", "constraints": ["constraint.tool.protocols"]},
            {"checker": "human_boundary_check", "constraints": ["constraint.human.boundary"]},
            {"checker": "memory_runtime_plan_check", "constraints": ["constraint.memory.board", "constraint.runtime.board"]},
            {"checker": "hierarchical_verification_plan_check", "constraints": ["constraint.verification.hierarchy", "constraint.pipeline.structure"]},
            {"checker": "verification_artifact_contract_check", "constraints": ["constraint.verification.artifacts"]},
            {"checker": "required_real_tool_evidence_check", "constraints": ["constraint.verification.hierarchy", "constraint.tool.protocols", "constraint.deployment.board"]},
            {"checker": "sacg_reference_check", "constraints": ["constraint.pipeline.structure"]},
            {"checker": "data_order_trace_check", "constraints": ["constraint.stream.order", "constraint.beat.pipeline"]},
            {"checker": "deadlock_watchdog", "constraints": ["constraint.verification.hierarchy", "constraint.tool.protocols"]},
            {"checker": "implementation_package_static", "constraints": ["constraint.backend.package", "constraint.deployment.board"]},
            {"checker": "board_runtime", "constraints": ["constraint.deployment.board", "constraint.human.boundary"]},
        ],
        "stage_test_targets": [stage["stage_id"] for stage in pipeline.get("stages", [])],
        "hierarchical_verification": hierarchy,
        "case_adapter": {
            "case_id": case_adapter.get("case_id"),
            "model_family": case_adapter.get("model_family"),
            "status": case_adapter.get("status"),
            "source": case_adapter.get("source"),
        },
        "system_test_policy": "required_before_backend_board",
        "board_test_policy": "required_for_final_design_closure",
        "constraints_touched": TOUCHED_CONSTRAINTS,
        "constraints_referenced": sorted(set(REFERENCED_CONSTRAINTS)),
    }


def summarize_pipeline_plan(state: dict[str, Any]) -> dict[str, Any]:
    try:
        plan = read_json(artifact_path(state, "artifact.stage3.pipeline_plan"))
    except KeyError as exc:
        return {"stage": "pipeline_planning", "status": "missing", "error": str(exc)}
    checks = plan.get("checker_summary", {}) if isinstance(plan.get("checker_summary"), dict) else {}
    attention_semantics = normalize_attention_contract(
        plan.get("attention_contract", {}) if isinstance(plan.get("attention_contract"), dict) else {}
    )
    return {
        "stage": plan.get("stage"),
        "status": plan.get("status"),
        "checker_summary": checks,
        "stage_count": len(plan.get("stages", [])),
        "data_edge_count": len(plan.get("data_edges", [])),
        "stream_edge_count": len(plan.get("stream_edges", [])),
        "attention_semantics": attention_semantics,
        "numeric_stream_policy": plan.get("numeric_stream_policy", {}),
        "memory_policy": plan.get("memory_policy", {}),
    }


def summarize_parameter_binding(state: dict[str, Any]) -> dict[str, Any]:
    try:
        bindings = read_json(artifact_path(state, "artifact.stage4.parameter_binding"))
    except KeyError as exc:
        return {"stage": "parameter_binding", "status": "missing", "error": str(exc)}
    rows = []
    for row in bindings.get("bindings", []):
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "stage_id": row.get("stage_id"),
                "op": row.get("op"),
                "template_id": row.get("template_id"),
                "params": row.get("params", {}),
                "status": row.get("status"),
                "legality_errors": row.get("legality_errors", []),
            }
        )
    return {
        "stage": bindings.get("stage"),
        "status": bindings.get("status"),
        "checker_summary": bindings.get("checker_summary", {}),
        "global_params": bindings.get("global_params", {}),
        "numeric_binding_plan": bindings.get("numeric_binding_plan", {}),
        "stream_contract_trace": bindings.get("stream_contract_trace", []),
        "parameter_bindings": rows,
    }


def summarize_codegen_manifest(state: dict[str, Any]) -> dict[str, Any]:
    try:
        manifest = read_json(artifact_path(state, "artifact.stage5.design_artifact_manifest"))
    except KeyError as exc:
        return {"stage": "code_generation", "status": "missing", "error": str(exc)}
    compile_gate = manifest.get("compile_gate", {}) if isinstance(manifest.get("compile_gate"), dict) else {}
    contract_check = manifest.get("contract_check", {}) if isinstance(manifest.get("contract_check"), dict) else {}
    package_static_check = manifest.get("package_static_check", {}) if isinstance(manifest.get("package_static_check"), dict) else {}
    return {
        "stage": manifest.get("stage"),
        "status": manifest.get("status"),
        "target_model_artifact_status": manifest.get("target_model_artifact_status", {}),
        "generated_package_root": manifest.get("generated_package_root"),
        "generated_files_count": len(manifest.get("generated_files", [])),
        "template_sources": manifest.get("template_sources", []),
        "selected_operator_template_sources": manifest.get("selected_operator_template_sources", []),
        "compile_gate": {
            "status": compile_gate.get("status"),
            "summary": compile_gate.get("summary"),
            "steps": [
                {
                    "command": step.get("command"),
                    "status": step.get("status"),
                    "returncode": step.get("returncode"),
                }
                for step in compile_gate.get("steps", [])
            ],
        },
        "contract_check": {
            "status": contract_check.get("status"),
            "summary": contract_check.get("summary"),
            "errors": contract_check.get("errors", []),
        },
        "package_static_check": {
            "status": package_static_check.get("status"),
            "summary": package_static_check.get("summary"),
            "errors": package_static_check.get("errors", []),
        },
    }


def constraint_exists(state: dict[str, Any], constraint_id: str) -> bool:
    return any(item.get("id") == constraint_id for item in state.get("constraints", []))


def check_row(
    checker: str,
    ok: bool,
    summary: str,
    constraints: list[str],
    errors: list[str] | None = None,
    warnings: list[str] | None = None,
    evidence_phase: str = "current_stage_static_check",
    execution_status: str = "not_applicable",
    status: str | None = None,
) -> dict[str, Any]:
    row_status = status or ("pass" if ok else "fail")
    return {
        "checker": checker,
        "status": row_status,
        "summary": summary,
        "constraints": constraints,
        "errors": [] if row_status in {"pass", "pending_downstream", "not_run"} else list(errors or [summary]),
        "warnings": list(warnings or []),
        "evidence_phase": evidence_phase,
        "execution_status": execution_status,
    }


def checker_summary(checker_results: list[dict[str, Any]]) -> dict[str, Any]:
    passed = [row for row in checker_results if row.get("status") == "pass"]
    pending = [row for row in checker_results if row.get("status") in {"pending_downstream", "not_run"}]
    failed = [row for row in checker_results if row.get("status") not in {"pass", "pending_downstream", "not_run"}]
    return {
        "passed": len(passed),
        "pending_downstream": len(pending),
        "failed": len(failed),
        "errors": [error for row in failed for error in row.get("errors", [])],
        "warnings": [warning for row in checker_results for warning in row.get("warnings", [])],
        "pending": [
            {
                "checker": row.get("checker"),
                "summary": row.get("summary"),
                "execution_status": row.get("execution_status"),
            }
            for row in pending
        ],
    }


def status_from_summary(summary: dict[str, Any]) -> str:
    if str(summary.get("status") or "").lower() == "missing":
        return "fail"
    checker_summary = summary.get("checker_summary", {}) if isinstance(summary.get("checker_summary"), dict) else {}
    failed = checker_summary.get("failed")
    if failed is not None:
        return "pass" if int(failed or 0) == 0 else "fail"
    return "pass" if str(summary.get("status") or "").lower() in {"ready", "pass", "promoted"} else "fail"


def planned_evidence_paths(run_dir: Path, tool_name: str, case_adapter: dict[str, Any] | None = None) -> dict[str, Any]:
    if case_adapter is not None:
        return planned_evidence_paths_from_adapter(case_adapter, run_dir, tool_name)
    return {"planned_consumes": [], "planned_produces": []}


def build_review_checker_results(
    state: dict[str, Any],
    plan: dict[str, Any],
    pipeline_summary: dict[str, Any],
    parameter_summary: dict[str, Any],
    codegen_summary: dict[str, Any],
    artifact_contract: dict[str, Any],
) -> list[dict[str, Any]]:
    compile_gate = codegen_summary.get("compile_gate", {}) if isinstance(codegen_summary.get("compile_gate"), dict) else {}
    contract_check = codegen_summary.get("contract_check", {}) if isinstance(codegen_summary.get("contract_check"), dict) else {}
    package_static_check = codegen_summary.get("package_static_check", {}) if isinstance(codegen_summary.get("package_static_check"), dict) else {}
    target_status = codegen_summary.get("target_model_artifact_status", {}) if isinstance(codegen_summary.get("target_model_artifact_status"), dict) else {}
    hierarchy = plan.get("hierarchical_verification", {}) if isinstance(plan.get("hierarchical_verification"), dict) else {}
    tool_rows = artifact_contract.get("required_tool_protocols", [])
    all_tools_configured = bool(tool_rows) and all(bool(row.get("configured")) for row in tool_rows)
    generated_artifacts = artifact_contract.get("required_generated_artifacts", [])
    generated_artifacts_present = bool(generated_artifacts) and all(bool(row.get("exists")) for row in generated_artifacts)
    evidence_gate_names = {str(row.get("name")) for row in artifact_contract.get("required_evidence_gates", [])}
    policy = artifact_contract.get("policy", {}) if isinstance(artifact_contract.get("policy"), dict) else {}
    debug_loop_contract = hierarchy.get("debug_loop_contract", {}) if isinstance(hierarchy.get("debug_loop_contract"), dict) else {}
    artifact_debug_loop_contract = (
        artifact_contract.get("debug_loop_contract", {})
        if isinstance(artifact_contract.get("debug_loop_contract"), dict)
        else {}
    )
    debug_contract_ok = (
        debug_loop_contract.get("layer_order")
        == ["operator_leaf_modules", "single_transformer_layer_kernel", "board_axi_ddr_wrapped_system"]
        and artifact_debug_loop_contract.get("layer_order")
        == ["operator_leaf_modules", "single_transformer_layer_kernel", "board_axi_ddr_wrapped_system"]
        and isinstance(debug_loop_contract.get("anti_spin_policy"), dict)
        and debug_loop_contract["anti_spin_policy"].get("lower_layer_pass_evidence_is_reusable_not_absolute") is True
        and debug_loop_contract["anti_spin_policy"].get("passed_lower_layer_can_be_challenged_by_current_layer_trace") is True
        and debug_loop_contract["anti_spin_policy"].get("do_not_reopen_passed_lower_layer_without_contradicting_current_layer_trace") is True
    )
    stage3_pass = status_from_summary(pipeline_summary) == "pass"
    stage4_pass = status_from_summary(parameter_summary) == "pass"
    return [
        check_row(
            "task_card_check",
            constraint_exists(state, "constraint.task.goal"),
            "task goal constraint is present in SACG",
            ["constraint.task.goal"],
        ),
        check_row(
            "model_config_check",
            constraint_exists(state, "constraint.model.decoder") and constraint_exists(state, "constraint.shape.model") and bool(pipeline_summary.get("attention_semantics")),
            "model, shape, and attention semantics are visible",
            ["constraint.model.decoder", "constraint.shape.model"],
        ),
        check_row(
            "numeric_policy_check",
            bool(parameter_summary.get("numeric_binding_plan")) and bool(parameter_summary.get("global_params")),
            "Stage 4 numeric binding plan and global params are visible",
            ["constraint.numeric.policy", "constraint.parameter.binding"],
        ),
        check_row(
            "template_coverage_check",
            bool(codegen_summary.get("template_sources")) and package_static_check.get("status") == "pass",
            "Stage 5 template provenance and package static check are visible",
            ["constraint.template.library", "constraint.codegen.package"],
        ),
        check_row(
            "stream_plan_check",
            stage3_pass and int(pipeline_summary.get("data_edge_count") or 0) > 0 and int(pipeline_summary.get("stream_edge_count") or 0) > 0,
            "Stage 3 stream/data-edge plan passed static checks",
            ["constraint.stream.order", "constraint.beat.pipeline"],
        ),
        check_row(
            "parameter_binding_static_check",
            stage4_pass,
            "Stage 4 parameter binding static checks passed",
            ["constraint.parameter.binding"],
            errors=parameter_summary.get("checker_summary", {}).get("errors", []) if isinstance(parameter_summary.get("checker_summary"), dict) else [],
        ),
        check_row(
            "code_generation_manifest_static_check",
            bool(target_status.get("current_artifacts_match_target")) and not target_status.get("missing_for_target"),
            "Stage 5 manifest targets the current case artifact set",
            ["constraint.codegen.package"],
        ),
        check_row(
            "codegen_package_static_check",
            package_static_check.get("status") == "pass",
            str(package_static_check.get("summary") or "Stage 5 package static check passed"),
            ["constraint.codegen.package"],
            errors=package_static_check.get("errors", []),
        ),
        check_row(
            "codegen_compile_gate",
            compile_gate.get("status") == "pass",
            str(compile_gate.get("summary") or "Stage 5 compile/elaboration gate passed"),
            ["constraint.codegen.package"],
        ),
        check_row(
            "codegen_contract_check",
            contract_check.get("status") == "pass",
            str(contract_check.get("summary") or "Stage 5 code generation contract passed"),
            ["constraint.codegen.package"],
            errors=contract_check.get("errors", []),
        ),
        check_row(
            "verification_plan_static_check",
            bool(plan.get("checker_plan")) and bool(hierarchy.get("stage_agents")) and bool(hierarchy.get("merge_agents")),
            "Stage 5 plan declares checker list, leaf stage agents, and merge agents",
            ["constraint.verification.plan", "constraint.verification.hierarchy"],
        ),
        check_row(
            "tool_protocol_check",
            all_tools_configured,
            "all required verification tool protocols are configured; planned evidence paths are declared for downstream execution",
            ["constraint.tool.protocols"],
        ),
        check_row(
            "human_boundary_check",
            bool(policy.get("smoke_is_not_acceptance")) and bool(policy.get("board_runtime_required_for_final_pass")),
            "human-boundary policy forbids smoke-only acceptance and requires board runtime before final pass",
            ["constraint.human.boundary", "constraint.verification.artifacts"],
        ),
        check_row(
            "memory_runtime_plan_check",
            generated_artifacts_present,
            "generated code package, memory layout, and runtime config exist for verification handoff",
            ["constraint.memory.board", "constraint.runtime.board"],
        ),
        check_row(
            "hierarchical_verification_plan_check",
            len(hierarchy.get("stage_agents", [])) >= 1
            and len(hierarchy.get("merge_agents", [])) >= 1
            and len(hierarchy.get("evidence_gates", [])) >= 1
            and debug_contract_ok,
            "three-layer repair-loop hierarchy and anti-spin debug contract are declared",
            ["constraint.verification.hierarchy", "constraint.pipeline.structure"],
            errors=[] if debug_contract_ok else ["missing or invalid three-layer debug-loop/anti-spin contract"],
        ),
        check_row(
            "verification_artifact_contract_check",
            artifact_contract.get("status") == "pass",
            str(artifact_contract.get("summary") or "verification artifact contract passed"),
            ["constraint.verification.artifacts"],
            errors=artifact_contract.get("errors", []),
        ),
        check_row(
            "required_real_tool_evidence_check",
            {"case_real_weight_artifacts", "functional_sim", "case_runtime_bitstream", "board_runtime"}.issubset(evidence_gate_names)
            and bool(policy.get("real_weight_artifacts_required"))
            and bool(policy.get("real_functional_sim_required"))
            and bool(policy.get("board_runtime_required_for_final_pass")),
            "real weights, functional simulation, bitstream, and board runtime are required downstream gates; no final pass is claimed",
            ["constraint.verification.hierarchy", "constraint.tool.protocols", "constraint.deployment.board"],
        ),
        check_row(
            "sacg_reference_check",
            stage3_pass and stage4_pass and codegen_summary.get("status") == "ready",
            "Stage 3, Stage 4, and Stage 5 artifacts referenced by SACG are ready/promoted inputs",
            ["constraint.pipeline.structure"],
        ),
        check_row(
            "data_order_trace_check",
            stage3_pass and bool(pipeline_summary.get("numeric_stream_policy")),
            "Stage 3 stream order and numeric stream policy are available for downstream trace checks",
            ["constraint.stream.order", "constraint.beat.pipeline"],
            evidence_phase="current_stage_static_trace_ledger",
            execution_status="static_only_downstream_sim_required",
        ),
        check_row(
            "deadlock_watchdog",
            "functional_sim" in evidence_gate_names,
            "deadlock watchdog is required through the downstream functional_sim gate and must emit tool evidence",
            ["constraint.verification.hierarchy", "constraint.tool.protocols"],
            evidence_phase="downstream_gate_declared",
            execution_status="not_run_required_downstream",
            status="pending_downstream",
        ),
        check_row(
            "implementation_package_static",
            "case_runtime_bitstream" in evidence_gate_names,
            "implementation package evidence is required through the case_runtime_bitstream downstream gate",
            ["constraint.backend.package", "constraint.deployment.board"],
            evidence_phase="downstream_gate_declared",
            execution_status="not_run_required_downstream",
            status="pending_downstream",
        ),
        check_row(
            "board_runtime",
            "board_runtime" in evidence_gate_names and bool(policy.get("board_runtime_required_for_final_pass")),
            "board runtime evidence is required for final closure and is not claimed by Stage 5",
            ["constraint.deployment.board", "constraint.human.boundary"],
            evidence_phase="downstream_gate_declared",
            execution_status="not_run_required_downstream",
            status="pending_downstream",
        ),
    ]


def build_template_source_checks(codegen_summary: dict[str, Any]) -> list[dict[str, Any]]:
    template_sources = codegen_summary.get("template_sources", [])
    selected_sources = codegen_summary.get("selected_operator_template_sources", [])
    return [
        {
            "checker": "stage5_template_source_manifest_check",
            "status": "pass" if template_sources else "fail",
            "summary": {
                "template_sources_count": len(template_sources),
                "selected_operator_template_sources_count": len(selected_sources),
            },
            "errors": [] if template_sources else ["Stage 5 manifest has no template_sources"],
        }
    ]


def current_certificate_validation_summary(state: dict[str, Any]) -> dict[str, Any]:
    from accagent.framework.stage_debug_loop import (
        SCOPE_PROMOTION_CERTIFICATES,
        validated_scope_certificate,
    )

    scopes = ["operator_leaf_closure", "single_layer_closure", "board_axi_ddr_closure"]
    artifacts = {
        str(item.get("id")): item
        for item in state.get("artifacts", [])
        if isinstance(item, dict) and item.get("id")
    }
    rows = []
    for scope in scopes:
        artifact_id = SCOPE_PROMOTION_CERTIFICATES[scope]
        artifact = artifacts.get(artifact_id)
        validated = validated_scope_certificate(state, scope)
        rows.append(
            {
                "scope": scope,
                "artifact_id": artifact_id,
                "artifact_present": artifact is not None,
                "producer_transition": artifact.get("producer_transition") if artifact else None,
                "trust_status": artifact.get("trust_status") if artifact else None,
                "current_contract_valid": validated is not None,
                "reuse_allowed": validated is not None,
                "validation_status": "valid" if validated is not None else "missing_or_stale_for_current_contract",
            }
        )
    return {
        "schema_version": "spatialaccagent.current_certificate_validation_summary.v0",
        "evidence_contract_version": EVIDENCE_CONTRACT_VERSION,
        "scopes": rows,
        "policy": "Artifact presence is not certificate validity. Reuse is allowed only when the current validator returns current_contract_valid=true.",
    }


def build_verification_review_artifact(
    state: dict[str, Any],
    plan: dict[str, Any],
    artifact_contract: dict[str, Any],
) -> dict[str, Any]:
    pipeline_summary = summarize_pipeline_plan(state)
    parameter_summary = summarize_parameter_binding(state)
    codegen_summary = summarize_codegen_manifest(state)
    checker_results = build_review_checker_results(
        state,
        plan,
        pipeline_summary,
        parameter_summary,
        codegen_summary,
        artifact_contract,
    )
    summary = checker_summary(checker_results)
    plan["checker_results"] = checker_results
    plan["checker_summary"] = summary
    plan["status"] = "ready" if summary["failed"] == 0 and artifact_contract.get("status") == "pass" else "incomplete"
    certificate_validation = current_certificate_validation_summary(state)
    return {
        "schema_version": "spatialaccagent.verification_artifacts_review.v0",
        "stage": "verification_artifacts",
        "status": plan["status"],
        "checker_plan": plan.get("checker_plan", []),
        "checker_summary": summary,
        "hierarchical_verification": plan.get("hierarchical_verification", {}),
        "stage_test_targets": plan.get("stage_test_targets", []),
        "system_test_policy": plan.get("system_test_policy"),
        "board_test_policy": plan.get("board_test_policy"),
        "verification_plan": plan,
        "verification_artifact_contract": artifact_contract,
        "checker_results": checker_results,
        "parameter_bindings": parameter_summary.get("parameter_bindings", []),
        "template_source_checks": build_template_source_checks(codegen_summary),
        "attention_semantics": pipeline_summary.get("attention_semantics", {}),
        "upstream_evidence": {
            "stage3_pipeline_plan": pipeline_summary,
            "stage4_parameter_binding": parameter_summary,
            "stage5_code_generation": codegen_summary,
        },
        "stage_gate_policy": {
            "current_certificate_validation": certificate_validation,
            "current_stage_acceptance": [
                "verification_plan must declare the three debug/repair layers: operator leaf modules, single transformer-layer kernel, and board AXI/DDR wrapped system",
                "verification_artifact_contract must pass before the Stage 5 transition can be promoted",
                "required tool protocols and generated handoff artifacts must be configured and present",
                "upstream Stage 3, Stage 4, and Stage 5 static gates must be visible as evidence",
                "lower-layer pass evidence is reusable but can be challenged by a bound current-layer CCTG/boundary trace",
            ],
            "later_stage_obligations": [
                "Stage7 executes real tools for the three-layer verification closures; Vivado synthesis/implementation, timing, bitstream, and board runtime are downstream after verification closure",
                "smoke or default generated weights cannot be used as functional correctness acceptance",
            ],
            "risk_classification_rule": (
                "If verification_artifact_contract_check and upstream static gates pass, do not report later "
                "VCS/Vivado/board execution obligations as current-stage risks; keep them as required gates "
                "or proposed_actions."
            ),
        },
        "constraints_touched": TOUCHED_CONSTRAINTS,
        "constraints_referenced": sorted(set(REFERENCED_CONSTRAINTS)),
    }


def tool_by_name(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    try:
        tools = read_json(artifact_path(state, "artifact.input.tool_protocols"))
    except KeyError:
        return {}
    return {str(item.get("name")): item for item in tools.get("tools", []) if isinstance(item, dict) and item.get("name")}


def tool_configured(tool: dict[str, Any] | None) -> bool:
    if not isinstance(tool, dict):
        return False
    command = tool.get("command")
    argv = tool.get("argv")
    return bool(command) or (isinstance(argv, list) and bool(argv))


def tool_capabilities(tool: dict[str, Any] | None) -> set[str]:
    if not isinstance(tool, dict):
        return set()
    value = tool.get("capabilities", [])
    if isinstance(value, dict):
        return {str(key) for key, enabled in value.items() if enabled}
    if isinstance(value, list):
        return {str(item) for item in value}
    return set()


def tool_produces(tool: dict[str, Any] | None) -> list[str]:
    if not isinstance(tool, dict):
        return []
    produces = tool.get("produces", [])
    return [str(item) for item in produces] if isinstance(produces, list) else []


def supports_boundary_trace(tool: dict[str, Any] | None) -> bool:
    caps = tool_capabilities(tool)
    if caps.intersection({"boundary_trace", "boundary_trace_rerun", "contract_boundary_trace"}):
        return True
    return any("boundary_trace" in item or "failure_localization" in item for item in tool_produces(tool))


def role_capability_errors(role: str, spec: dict[str, Any]) -> list[str]:
    caps = tool_capabilities(spec)
    checker_only = "gate_checker_only" in caps or bool(spec.get("checker_only"))
    errors: list[str] = []
    if role == "single_layer_functional_sim":
        if checker_only:
            errors.append(
                "single_layer_functional_sim is declared as gate_checker_only; "
                "Stage 6/8 requires a real current-layer simulation tool, not a report-presence checker"
            )
        if not caps.intersection(
            {
                "single_layer_functional_sim",
                "real_single_layer_functional_sim",
                "single_transformer_layer_functional_sim",
            }
        ):
            errors.append(
                "single_layer_functional_sim must declare a real single-layer functional simulation capability"
            )
        if not supports_boundary_trace(spec):
            errors.append(
                "single_layer_functional_sim must support boundary_trace output for contract-guided debug closure"
            )
    if role == "single_layer_golden_compare":
        if checker_only:
            errors.append(
                "single_layer_golden_compare is declared as gate_checker_only; "
                "Stage 6 promotion requires an independent single-layer golden/numeric comparison"
            )
        if not caps.intersection({"single_layer_golden_compare", "independent_golden_compare", "numeric_compare"}):
            errors.append(
                "single_layer_golden_compare must declare independent golden or numeric comparison capability"
            )
    errors.extend(tool_evidence_contract_errors(role, spec))
    return errors


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


def build_verification_gate_dag(case_adapter: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    real_weight_gate = gate_name(case_adapter, "real_weight_artifacts")
    target_model_reference_gate = gate_name(case_adapter, "target_model_reference")
    semantic_testbench_gate = gate_name(case_adapter, "semantic_testbench")
    stage_leaf_gate = gate_name(case_adapter, "stage_leaf_static")
    boundary_contract_gate = gate_name(case_adapter, "boundary_contract")
    leaf_functional_gate = gate_name(case_adapter, "leaf_functional")
    leaf_golden_gate = gate_name(case_adapter, "leaf_golden_compare")
    operator_leaf_semantic_gate = gate_name(case_adapter, "operator_leaf_semantic_evidence")
    tb_scaffold_gate = gate_name(case_adapter, "tb_scaffold")
    single_layer_gate = gate_name(case_adapter, "single_layer_kernel")
    single_layer_functional_gate = gate_name(case_adapter, "single_layer_functional")
    single_layer_golden_gate = gate_name(case_adapter, "single_layer_golden_compare")
    single_layer_semantic_gate = gate_name(case_adapter, "single_layer_semantic_evidence")
    multilayer_gate = gate_name(case_adapter, "multilayer_pipeline")
    multilayer_functional_gate = gate_name(case_adapter, "multilayer_functional")
    pipeline_deadlock_gate = gate_name(case_adapter, "pipeline_deadlock")
    axi_gate = gate_name(case_adapter, "axi_ddr_interface")
    axi_protocol_gate = gate_name(case_adapter, "axi_protocol")
    ddr_roundtrip_gate = gate_name(case_adapter, "ddr_image_roundtrip")
    board_semantic_gate = gate_name(case_adapter, "board_semantic_evidence")
    board_bringup_gate = gate_name(case_adapter, "board_bringup")
    functional_gate = gate_name(case_adapter, "functional_sim")
    board_discovery_gate = gate_name(case_adapter, "board_interface_discovery")
    vivado_synth_gate = gate_name(case_adapter, "vivado_synthesis")
    vivado_impl_gate = gate_name(case_adapter, "vivado_implementation")
    runtime_abi_gate = gate_name(case_adapter, "runtime_abi")
    runtime_gate = gate_name(case_adapter, "runtime_bitstream")
    board_gate = gate_name(case_adapter, "board_runtime")
    pipeline_path = next(
        (
            path for path in [
                run_dir / "pipeline_planning" / "pipeline_plan.json",
                run_dir / "pipeline" / "pipeline_plan.json",
            ]
            if path.is_file()
        ),
        None,
    )
    pipeline = read_json(pipeline_path) if pipeline_path else {}
    pipeline_stages = pipeline.get("stages", []) if isinstance(pipeline.get("stages"), list) else []
    leaf_gates = [
        {
            "name": f"leaf_stage.{safe_id(str(stage.get('stage_id') or index))}",
            "stage_id": stage.get("stage_id"),
            "op": stage.get("op"),
            "kind": stage.get("kind"),
        }
        for index, stage in enumerate(pipeline_stages)
        if isinstance(stage, dict)
    ]
    def node(
        name: str,
        depends_on: list[str],
        role: str,
        evidence_status: str = "required_pending_execution",
        phase: str = "unspecified",
        **extra: Any,
    ) -> dict[str, Any]:
        paths = planned_evidence_paths(run_dir, name, case_adapter)
        result = {
            "name": name,
            "role": role,
            "phase": phase,
            "depends_on": depends_on,
            "planned_consumes": paths["planned_consumes"],
            "planned_produces": paths["planned_produces"],
            "evidence_status": evidence_status,
            "tool_roles": stage5_gate_tool_roles(case_adapter, name),
        }
        result.update(extra)
        return result

    leaf_nodes = [
        node(
            item["name"],
            [],
            f"verify spatial operator module {item.get('stage_id')} before any layer/block merge",
            phase="operator_leaf_module",
            required_maturity="operator_leaf_functional",
            stage_id=item.get("stage_id"),
            op=item.get("op"),
            kind=item.get("kind"),
            shared_tool_gate=stage_leaf_gate,
            planned_consumes=[
                str(run_dir / "pipeline_planning" / "pipeline_plan.json"),
                str(run_dir / "parameter_binding" / "parameter_binding.json"),
                str(run_dir / "generated" / "chisel"),
            ],
            planned_produces=[
                str(run_dir / "verification" / "leaf_stage" / f"{safe_id(str(item.get('stage_id') or item['name']))}.json"),
                str(run_dir / "verification" / "real_tools" / f"case_stage_leaf_static__{safe_id(item['name'])}.json"),
            ],
        )
        for item in leaf_gates
    ]
    leaf_names = [item["name"] for item in leaf_gates]
    nodes = [
        node(
            real_weight_gate,
            [],
            "catalog the complete target checkpoint and bind every tensor to immutable source hashes",
            phase="real_weight_catalog",
            required_maturity="operator_leaf_functional",
        ),
        node(
            target_model_reference_gate,
            [real_weight_gate],
            "run the real target model on a reproducible random input and capture independent operator/single-layer/all-Transformer-block boundary golden tensors",
            phase="target_model_reference",
            required_maturity="operator_leaf_functional",
        ),
        node(
            semantic_testbench_gate,
            [target_model_reference_gate],
            "generate numeric-policy-bound semantic vectors/testbenches and validate complete DUT real-weight consumption",
            phase="semantic_testbench_generation",
            required_maturity="operator_leaf_functional",
        ),
        node(
            boundary_contract_gate,
            [],
            "materialize boundary contracts and trace schema used by contract-guided debug closure",
            phase="debug_boundary_contract",
            required_maturity="contract_guided_debug_closure",
        ),
        *leaf_nodes,
        node(
            stage_leaf_gate,
            leaf_names,
            "aggregate all per-operator leaf module checks; every spatial stage must pass before layer merge",
            phase="operator_leaf_aggregate",
            required_maturity="operator_leaf_functional",
        ),
        node(
            leaf_functional_gate,
            [stage_leaf_gate, boundary_contract_gate, semantic_testbench_gate],
            "prove every spatial operator leaf module with independent functional simulation before layer merge",
            phase="operator_leaf_functional",
            required_maturity="operator_leaf_functional",
        ),
        node(
            leaf_golden_gate,
            [leaf_functional_gate, boundary_contract_gate, target_model_reference_gate, semantic_testbench_gate],
            "compare every spatial operator leaf module against golden/reference boundary values",
            phase="operator_leaf_golden_compare",
            required_maturity="operator_leaf_functional",
        ),
        node(
            operator_leaf_semantic_gate,
            [leaf_golden_gate, leaf_functional_gate, stage_leaf_gate, boundary_contract_gate, target_model_reference_gate, semantic_testbench_gate],
            "assemble checker-bound evidence for all operator leaves, complete real-weight consumption, independent target-model golden values, and immutable semantic identities",
            phase="operator_leaf_semantic_aggregate",
            required_maturity="operator_leaf_functional",
        ),
        node(
            tb_scaffold_gate,
            [operator_leaf_semantic_gate, semantic_testbench_gate],
            "materialize and audit testbench/RTL scaffold that loads the declared input and weight artifacts",
            phase="testbench_scaffold",
        ),
        node(
            single_layer_gate,
            [operator_leaf_semantic_gate, tb_scaffold_gate, semantic_testbench_gate],
            "connect verified spatial operator modules into one transformer-layer/block kernel and validate layer-level stream/data-order behavior",
            phase="single_layer_kernel",
            required_maturity="single_layer_functional",
        ),
        node(
            single_layer_functional_gate,
            [single_layer_gate, operator_leaf_semantic_gate, tb_scaffold_gate, semantic_testbench_gate],
            "run one transformer-layer/block functional verification before any multi-layer pipeline claim",
            phase="single_layer_functional",
            required_maturity="single_layer_functional",
        ),
        node(
            single_layer_golden_gate,
            [single_layer_functional_gate],
            "compare the single transformer-layer/block against golden/reference outputs or numeric tolerance contract",
            phase="single_layer_golden_compare",
            required_maturity="single_layer_functional",
        ),
        node(
            single_layer_semantic_gate,
            [single_layer_golden_gate, single_layer_functional_gate, operator_leaf_semantic_gate, target_model_reference_gate, semantic_testbench_gate],
            "assemble checker-bound connected single-layer semantic, golden, real-weight-consumption, and immutable identity evidence",
            phase="single_layer_semantic_aggregate",
            required_maturity="single_layer_functional",
        ),
        node(
            board_discovery_gate,
            [single_layer_semantic_gate],
            "use an LLM board-interface agent to interpret Vivado-exported sample-project structure before generating board integration RTL",
            phase="board_interface_discovery",
            required_maturity="axi_ddr_functional",
        ),
        node(
            multilayer_gate,
            [single_layer_semantic_gate, semantic_testbench_gate, board_discovery_gate],
            "generate and prove the model-adaptive multi-layer scheduler against the discovered exact compute-slot contract",
            phase="multilayer_pipeline",
        ),
        node(
            axi_gate,
            [multilayer_gate, board_discovery_gate],
            "prove AXI/DDR runtime interface scaffold around the multi-layer kernel before simulation",
            phase="board_wrapper_interface",
        ),
        node(
            functional_gate,
            [semantic_testbench_gate, single_layer_semantic_gate, multilayer_gate, board_discovery_gate, axi_gate],
            "run the real board-wrapped simulator with the exact sample wrapper, immutable input, and complete Transformer-block weight image before derived evidence checks",
            phase="functional_simulation",
        ),
        node(
            multilayer_functional_gate,
            [functional_gate, multilayer_gate],
            "classify real simulator evidence for multi-layer pipeline functionality",
            phase="multilayer_functional",
            required_maturity="multilayer_pipeline_functional",
        ),
        node(
            pipeline_deadlock_gate,
            [functional_gate, multilayer_functional_gate],
            "classify real simulator liveness/deadlock evidence for the multi-layer pipeline",
            phase="multilayer_deadlock_liveness",
            required_maturity="multilayer_pipeline_functional",
        ),
        node(
            axi_protocol_gate,
            [functional_gate, axi_gate, board_discovery_gate],
            "classify dynamic AXI protocol/order/address evidence from the real simulator",
            phase="axi_protocol_check",
            required_maturity="axi_ddr_functional",
        ),
        node(
            ddr_roundtrip_gate,
            [functional_gate, axi_protocol_gate, real_weight_gate],
            "classify real input, weight, and output DDR transfer evidence from the real simulator",
            phase="ddr_image_roundtrip",
            required_maturity="axi_ddr_functional",
        ),
        node(
            board_semantic_gate,
            [
                functional_gate,
                multilayer_functional_gate,
                pipeline_deadlock_gate,
                axi_protocol_gate,
                ddr_roundtrip_gate,
                board_discovery_gate,
                real_weight_gate,
                target_model_reference_gate,
                semantic_testbench_gate,
            ],
            "assemble the canonical board-run identity, exact wrapper, all third-layer classifier, complete real-weight-consumption, and target-model output evidence",
            phase="board_semantic_aggregate",
            required_maturity="axi_ddr_functional",
        ),
        node(
            board_bringup_gate,
            [single_layer_semantic_gate, board_discovery_gate, functional_gate],
            "record board bring-up readiness from the passed single-layer certificate, validated exact board identity, current workload binding, complete real weight loading, and real VCS execution provenance; output/writeback remains diagnostic only",
            phase="board_bringup",
        ),
        node(
            vivado_synth_gate,
            [board_bringup_gate],
            "run Vivado synthesis and collect utilization/timing evidence after real board bring-up readiness; strict output/writeback functionality remains a separate Layer-3 diagnostic track",
            phase="vivado_synthesis",
        ),
        node(vivado_impl_gate, [vivado_synth_gate], "run Vivado implementation/route/DRC/timing evidence", phase="vivado_implementation"),
        node(runtime_gate, [vivado_impl_gate, board_bringup_gate], "run runtime/app-shell bitstream flow only after board bring-up readiness and Vivado implementation pass", phase="vivado_bitstream"),
        node(runtime_abi_gate, [runtime_gate], "cross-check runtime ABI, register map, DDR layout, and bitstream artifacts", phase="runtime_abi"),
        node(board_gate, [runtime_gate, runtime_abi_gate, board_bringup_gate, real_weight_gate], "program board/runtime and collect valid output evidence", phase="board_runtime"),
    ]
    node_names = {str(item.get("name")) for item in nodes if isinstance(item, dict) and item.get("name")}
    edges = [
        {
            "from": str(dep),
            "to": str(item.get("name")),
            "type": "gate_dependency",
            "policy": "producer gate must pass before consumer gate can execute",
        }
        for item in nodes
        if isinstance(item, dict) and item.get("name")
        for dep in item.get("depends_on", [])
        if str(dep) in node_names
    ]
    return {
        "schema_version": "spatialaccagent.verification_gate_dag.v0",
        "debug_loop_contract": hierarchical_debug_loop_contract(),
        "policy": {
            "three_debug_layers": [
                "operator_leaf_modules",
                "single_transformer_layer_kernel",
                "board_axi_ddr_wrapped_system",
            ],
            "layer1_operator_leaf_closure": [
                "real_weight_catalog",
                "target_model_reference",
                "semantic_testbench_generation",
                "operator_leaf_module",
                "debug_boundary_contract",
                "operator_leaf_functional",
                "operator_leaf_golden_compare",
                "operator_leaf_semantic_aggregate",
            ],
            "layer2_single_layer_kernel_closure": [
                "testbench_scaffold",
                "single_layer_kernel",
                "single_layer_functional",
                "single_layer_golden_compare",
                "single_layer_semantic_aggregate",
            ],
            "layer3_board_axi_ddr_wrapper_closure": [
                "board_interface_discovery",
                "multilayer_pipeline",
                "board_wrapper_interface",
                "functional_simulation",
                "multilayer_functional",
                "multilayer_deadlock_liveness",
                "axi_protocol_check",
                "ddr_image_roundtrip",
                "board_semantic_aggregate",
                "board_bringup",
            ],
            "hierarchical_order": [
                "real_weight_catalog",
                "target_model_reference",
                "semantic_testbench_generation",
                "operator_leaf_module",
                "debug_boundary_contract",
                "operator_leaf_functional",
                "operator_leaf_golden_compare",
                "operator_leaf_semantic_aggregate",
                "testbench_scaffold",
                "single_layer_kernel",
                "single_layer_functional",
                "single_layer_golden_compare",
                "single_layer_semantic_aggregate",
                "board_interface_discovery",
                "multilayer_pipeline",
                "board_wrapper_interface",
                "functional_simulation",
                "multilayer_functional",
                "multilayer_deadlock_liveness",
                "axi_protocol_check",
                "ddr_image_roundtrip",
                "board_semantic_aggregate",
                "board_bringup",
                "vivado_synthesis",
                "vivado_implementation",
                "vivado_bitstream",
                "runtime_abi",
                "board_runtime",
            ],
            "each_spatial_operator_module_must_have_leaf_gate": True,
            "single_layer_kernel_after_leaf_modules": True,
            "operator_leaf_functional_before_single_layer_kernel": True,
            "single_layer_functional_before_board_axi_ddr_wrapped_system": True,
            "third_layer_contains_multilayer_pipeline_and_board_axi_ddr_wrapper_subgates": True,
            "board_axi_ddr_functional_before_backend": True,
            "vivado_implementation_requires_board_bringup_readiness": True,
            "strict_board_output_functionality_remains_diagnostic_until_separately_closed": True,
            "all_gate_tool_roles_must_pass": True,
            "semantic_evidence_aggregators_are_mandatory_gate_tools": True,
            "vivado_report_checkers_are_mandatory_gate_tools": True,
            "testbench_scaffold_before_functional_sim": True,
            "multilayer_pipeline_before_axi_ddr": True,
            "llm_board_interface_discovery_before_multilayer_generation": True,
            "functional_sim_before_derived_third_layer_checkers": True,
            "backend_discovery_before_vivado_bitstream": True,
            "functional_sim_before_backend": True,
            "board_runtime_after_bitstream": True,
            "real_input_and_weight_artifacts_required": True,
            "real_model_inference_golden_required": True,
            "dut_real_weight_consumption_proof_required": True,
            "complete_transformer_block_weight_scope_required": True,
            "transformer_blocks_are_the_only_accelerator_scope": True,
            "explicit_numeric_comparison_policy_required": True,
            "rtl_derived_or_random_expected_output_forbidden": True,
            "smoke_is_not_acceptance": True,
            "do_not_promote_final_design_with_pending_required_node": True,
            "lower_layer_pass_evidence_is_reusable_not_absolute": True,
            "higher_layer_trace_can_trigger_targeted_lower_layer_backtrack": True,
            "do_not_reopen_passed_lower_layer_without_contradicting_boundary_trace": True,
        },
        "nodes": nodes,
        "edges": edges,
    }


def build_verification_artifact_contract(state: dict[str, Any], plan: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    tools = tool_by_name(state)
    case_adapter = case_adapter_for_state(state, run_dir)
    if case_adapter.get("status") not in {"ready", "pass"}:
        errors.append(f"case adapter is not ready: status={case_adapter.get('status')} errors={case_adapter.get('errors', [])}")
    try:
        manifest = read_json(artifact_path(state, "artifact.stage5.design_artifact_manifest"))
    except KeyError:
        manifest = {}
        errors.append("missing Stage 5 code generation manifest")

    for artifact_id in [
        "artifact.stage3.pipeline_plan",
        "artifact.stage4.parameter_binding",
        "artifact.stage5.design_artifact_manifest",
    ]:
        status = artifact_producer_status(state, artifact_id)
        if status and status != "promoted":
            errors.append(f"{artifact_id} producer transition is {status}, expected promoted")

    if (manifest.get("contract_check") or {}).get("status") != "pass":
        errors.append(f"Stage 5 codegen contract is not pass: {(manifest.get('contract_check') or {}).get('summary')}")

    required_roles = [
        "weight_manifest_generate",
        "target_model_reference_generate",
        "semantic_testbench_generate",
        "tb_scaffold_generate",
        "tb_scaffold",
        "stage_leaf_static",
        "boundary_contract_check",
        "leaf_functional_sim",
        "leaf_golden_compare",
        "operator_leaf_semantic_evidence",
        "real_weight_artifacts",
        "single_layer_kernel",
        "single_layer_functional_sim",
        "single_layer_golden_compare",
        "single_layer_semantic_evidence",
        "multilayer_pipeline",
        "multilayer_functional_sim",
        "pipeline_deadlock_check",
        "board_interface_discovery",
        "axi_ddr_interface",
        "axi_protocol_check",
        "ddr_image_roundtrip",
        "vcs_functional_sim",
        "vcs_evidence_analyzer",
        "deadlock_axi_check",
        "board_semantic_evidence",
        "vivado_synthesis",
        "vivado_synthesis_report_check",
        "vivado_implementation",
        "vivado_implementation_report_check",
        "runtime_abi_check",
        "runtime_bitstream",
    ]
    required_tool_specs = []
    for role in required_roles:
        spec = adapter_tool(case_adapter, role)
        if not spec:
            errors.append(f"required case adapter tool role is missing: {role}")
            continue
        required_tool_specs.append((role, spec))
    required_tool_names = [str(spec.get("name")) for _, spec in required_tool_specs if spec]
    required_tool_specs.append(("board_runtime", {"name": "board_runtime"}))
    tool_status = []
    for role, adapter_spec in required_tool_specs:
        name = str(adapter_spec.get("name"))
        tool = tools.get(name)
        if not tool:
            legacy_name = None
            if adapter_spec:
                legacy_name = adapter_spec.get("legacy_name")
            if legacy_name:
                tool = tools.get(str(legacy_name))
        configured = tool_configured(tool) or tool_configured(adapter_spec)
        resolved_tool = tool if isinstance(tool, dict) else adapter_spec
        planned_paths = planned_evidence_paths(run_dir, name, case_adapter)
        capabilities = sorted(tool_capabilities(adapter_spec).union(tool_capabilities(tool)))
        boundary_trace_capable = supports_boundary_trace(adapter_spec) or supports_boundary_trace(tool)
        tool_status.append(
            {
                "name": name,
                "role": role,
                "resolved_protocol_name": tool.get("name") if isinstance(tool, dict) else adapter_spec.get("name"),
                "configured_from": "tool_protocols" if isinstance(tool, dict) else "case_adapter",
                "configured": configured,
                "scope": resolved_tool.get("scope") if isinstance(resolved_tool, dict) else None,
                "kind": resolved_tool.get("kind") if isinstance(resolved_tool, dict) else None,
                "required": resolved_tool.get("required") if isinstance(resolved_tool, dict) else None,
                "produces": resolved_tool.get("produces", []) if isinstance(resolved_tool, dict) else [],
                "consumes": resolved_tool.get("consumes", []) if isinstance(resolved_tool, dict) else [],
                "capabilities": capabilities,
                "supports_boundary_trace": boundary_trace_capable,
                "planned_consumes": planned_paths["planned_consumes"],
                "planned_produces": planned_paths["planned_produces"],
                "evidence_status": "required_pending_execution",
            }
        )
        if not configured:
            errors.append(f"required verification tool protocol is missing or unconfigured: {name}")
        for message in role_capability_errors(role, adapter_spec):
            errors.append(f"case adapter role {role} capability contract failed: {message}")

    functional_group = [
        item for item in tools.values()
        if item.get("required_group") == "functional_sim" and tool_configured(item)
    ]
    if not functional_group:
        errors.append("functional_sim required group has no configured VCS/Verilator tool")

    generated_root = Path(str(manifest.get("generated_package_root", "")))
    required_existing = [
        ("generated_code_package", generated_root),
        ("memory_layout", Path(str(manifest.get("generated_memory_layout", "")))),
        ("runtime_config", Path(str(manifest.get("generated_runtime_config", "")))),
    ]
    artifact_status = []
    for name, path in required_existing:
        exists = path.exists() if str(path) else False
        artifact_status.append({"name": name, "path": str(path), "exists": exists})
        if not exists:
            errors.append(f"required generated artifact missing for verification: {name} at {path}")

    gates = plan.get("hierarchical_verification", {}).get("evidence_gates", [])
    stage_leaf_gate = gate_name(case_adapter, "stage_leaf_static")
    functional_gate = gate_name(case_adapter, "functional_sim")
    functional_sim_paths = planned_evidence_paths(run_dir, functional_gate, case_adapter)
    runtime_gate = gate_name(case_adapter, "runtime_bitstream")
    board_gate = gate_name(case_adapter, "board_runtime")
    gate_dag = build_verification_gate_dag(case_adapter, run_dir)
    gate_nodes = gate_dag.get("nodes", []) if isinstance(gate_dag.get("nodes"), list) else []
    leaf_node_names = sorted(
        str(row.get("name"))
        for row in gate_nodes
        if isinstance(row, dict) and str(row.get("name") or "").startswith("leaf_stage.")
    )
    node_by_name = {str(row.get("name")): row for row in gate_nodes if isinstance(row, dict) and row.get("name")}
    leaf_aggregate = node_by_name.get(stage_leaf_gate, {})
    leaf_aggregate_deps = [str(value) for value in leaf_aggregate.get("depends_on", [])] if isinstance(leaf_aggregate, dict) else []
    gate_protocol_coverage = {
        "schema_version": "spatialaccagent.stage5_gate_protocol_coverage.v0",
        "required_gate_count": len(gates),
        "required_gate_names": [str(gate.get("name")) for gate in gates if isinstance(gate, dict) and gate.get("name")],
        "configured_tool_protocol_names": [str(row.get("name")) for row in tool_status if isinstance(row, dict) and row.get("configured")],
        "functional_sim_candidates": [
            {
                "name": item.get("name"),
                "scope": item.get("scope"),
                "kind": item.get("kind"),
                "required_group": item.get("required_group"),
            }
            for item in functional_group
        ],
        "functional_sim_bound": bool(functional_group),
        "board_runtime_bound": any(row.get("name") == "board_runtime" and row.get("configured") for row in tool_status),
        "leaf_stage_count": len(leaf_node_names),
        "leaf_stage_names": leaf_node_names,
        "leaf_aggregate_gate": stage_leaf_gate,
        "leaf_aggregate_dependency_count": len(leaf_aggregate_deps),
        "leaf_aggregate_dependencies": leaf_aggregate_deps,
        "leaf_aggregate_covers_all_leaf_stages": set(leaf_node_names).issubset(set(leaf_aggregate_deps)),
    }
    memory_summary = sacg_memory_summary(state, limit=12)
    stage5_retry_requests = [
        item
        for item in memory_summary.get("open_retry_requests", [])
        if item.get("target_stage") == "stage5.verification_artifacts"
    ]
    stage5_barriers = [
        item
        for item in memory_summary.get("active_contamination_barriers", [])
        if str(item.get("artifact_id", "")).startswith("artifact.stage5.")
    ]
    return {
        "schema_version": "spatialaccagent.verification_artifact_contract.v0",
        "status": "pass" if not errors else "fail",
        "design_id": state.get("design_id"),
        "summary": "all verification artifact contracts are satisfiable" if not errors else f"{len(errors)} verification artifact blocker(s)",
        "errors": errors,
        "warnings": warnings,
        "required_evidence_gates": gates,
        "required_tool_protocols": tool_status,
        "functional_sim_candidates": [
            {
                "name": item.get("name"),
                "scope": item.get("scope"),
                "kind": item.get("kind"),
                "acceptance_role": "required_real_functional_sim_gate_not_smoke_acceptance",
                "candidate_label_is_not_acceptance": True,
                "planned_consumes": functional_sim_paths["planned_consumes"],
                "planned_produces": functional_sim_paths["planned_produces"],
                "evidence_status": "required_pending_execution",
            }
            for item in functional_group
        ],
        "gate_protocol_coverage": gate_protocol_coverage,
        "required_generated_artifacts": artifact_status,
        "evidence_path_requirements": [
            {
                "gate": node.get("name"),
                "phase": node.get("phase"),
                "acceptance_role": (
                    "required_real_functional_sim_gate_not_smoke_acceptance"
                    if node.get("name") == functional_gate
                    else "required_backend_implementation_gate"
                    if node.get("name") in {runtime_gate, board_gate}
                    else "required_hierarchical_verification_gate"
                ),
                "planned_consumes": node.get("planned_consumes", []),
                "planned_produces": node.get("planned_produces", []),
                "evidence_status": node.get("evidence_status", "required_pending_execution"),
            }
            for node in gate_dag.get("nodes", [])
            if isinstance(node, dict)
        ],
        "verification_gate_dag": gate_dag,
        "debug_loop_contract": hierarchical_debug_loop_contract(),
        "retry_reconciliation_contract": {
            "schema_version": "spatialaccagent.stage_retry_reconciliation.v0",
            "stage": "stage5.verification_artifacts",
            "source_open_retry_requests": stage5_retry_requests,
            "source_active_contamination_barriers": stage5_barriers,
            "same_stage_retry_policy": (
                "Open retry requests and active contamination barriers produced by prior rejected Stage6 "
                "transitions are expected inputs to a Stage6 retry. They are blockers for downstream "
                "Stage7 consumption, but they are not independent blockers for promoting the refined "
                "Stage6 transition when all current Stage6 contract, LLM, action-audit, and quality "
                "checks pass. SACG promotion of the new Stage6 transition closes matching retry "
                "requests and supersedes barriers for regenerated Stage6 artifacts."
            ),
            "promotion_preconditions": [
                "verification_plan_static_check passes",
                "hierarchical_verification_plan_check passes",
                "verification_artifact_contract_check passes",
                "verification_action_audit_check passes",
                "llm_io_quality_check passes",
                "LLM/team outputs do not report current-stage blockers after seeing this reconciliation contract",
            ],
        },
        "backtrack_contract": {
            "target_stage": "stage5.verification_artifacts",
            "trigger_conditions": [
                "a selected gate has no executable tool role",
                "a real-tool gate lacks planned consumed or produced evidence paths",
                "a later stage discovers missing operator-leaf, single-layer, multilayer, AXI/DDR, functional-sim, bitstream, or board-runtime coverage",
                "a generated artifact is marked rejected_producer or blocked by an active SACG contamination barrier",
                "a current-layer CCTG/boundary trace contradicts lower-layer pass evidence and binds the contradiction to a lower-layer gate or module",
                "a trace asserts lower-layer contradiction but lacks challenged gate/module binding; rerun the current-layer trace before any lower-layer backtrack",
            ],
            "required_action": (
                "Record a SACG backtrack_request with the missing contract/tool/evidence facts or the explicit "
                "contradicted lower-layer gate/module. Rerun only the challenged lower-layer scope when the trace "
                "is bound; otherwise rerun the failed current-layer trace first. Stage7 or later stages may retry "
                "only after the repaired lower/current layer revalidates."
            ),
            "policy": {
                "lower_layer_pass_evidence_is_reusable_not_absolute": True,
                "targeted_lower_layer_backtrack_requires_contradicting_current_layer_trace": True,
                "unbound_lower_layer_contradiction_requires_debug_trace_rerun": True,
                "do_not_broadly_reopen_all_lower_layers": True,
            },
        },
        "case_adapter": {
            "case_id": case_adapter.get("case_id"),
            "model_family": case_adapter.get("model_family"),
            "status": case_adapter.get("status"),
            "source": case_adapter.get("source"),
        },
        "existing_stage5_refinements": stage5_refinement_artifacts_for_state(state),
        "run_dir": str(run_dir),
        "policy": {
            "smoke_is_not_acceptance": True,
            "real_weight_artifacts_required": True,
            "complete_transformer_block_weight_consumption_required": True,
            "transformer_blocks_are_the_only_accelerator_scope": True,
            "real_target_model_reference_required": True,
            "random_or_rtl_derived_expected_output_forbidden": True,
            "explicit_numeric_comparison_policy_required": True,
            "real_axi_ddr_runtime_required": True,
            "real_functional_sim_required": True,
            "board_runtime_required_for_final_pass": True,
            "contract_guided_debug_closure_required": True,
            "downstream_failure_requires_failure_slice": True,
            "later_stage_missing_gate_or_tool_requires_stage5_backtrack": True,
            "same_stage_retry_can_supersede_prior_stage5_barriers_after_promotion": True,
            "lower_layer_pass_evidence_is_reusable_not_absolute": True,
            "higher_layer_trace_can_trigger_targeted_lower_layer_backtrack": True,
            "do_not_reopen_passed_lower_layer_without_contradicting_boundary_trace": True,
        },
        "debug_closure_contract": build_boundary_contracts(state, run_dir),
    }


def stage5_refinement_actions_materialized(
    output: dict[str, Any],
    refinement_materialization: dict[str, Any] | None,
) -> bool:
    if not isinstance(refinement_materialization, dict):
        return False
    if refinement_materialization.get("status") != "ready":
        return False
    manifest_path = str(refinement_materialization.get("manifest") or "")
    if not manifest_path:
        return False
    required = {
        str(action.get("id"))
        for action in output.get("executable_actions", [])
        if isinstance(action, dict)
        and str(action.get("id") or "").startswith("stage5.")
    }
    if not required:
        return False
    try:
        manifest = read_json(Path(manifest_path))
    except Exception:
        return False
    materialized = {
        str(action_id)
        for action_id in manifest.get("materialized_stage5_action_ids", [])
    }
    coverage = manifest.get("action_coverage", {}) if isinstance(manifest.get("action_coverage"), dict) else {}
    covered = {
        str(row.get("id"))
        for row in coverage.get("actions", [])
        if isinstance(row, dict) and row.get("status") == "pass"
    }
    return (
        manifest.get("status") == "ready"
        and coverage.get("status") == "ready"
        and required.issubset(materialized)
        and required.issubset(covered)
    )


def stage_worker_errors(
    output: dict[str, Any],
    existing_refinements: dict[str, Any] | None = None,
    refinement_materialization: dict[str, Any] | None = None,
) -> list[str]:
    if not output:
        return []
    errors = []
    status = str(output.get("status") or "").strip().lower()
    existing_refinement_ready = (
        isinstance(existing_refinements, dict)
        and existing_refinements.get("status") == "present"
        and any(
            isinstance(item, dict) and item.get("exists")
            for item in (existing_refinements.get("artifacts", {}) or {}).values()
        )
    )
    current_materialization_ready = (
        isinstance(refinement_materialization, dict)
        and refinement_materialization.get("status") == "ready"
        and bool(refinement_materialization.get("manifest"))
    )
    reviewed_refinement_ready = existing_refinement_ready and current_materialization_ready
    current_stage5_refinements_cover_planner = stage5_refinement_actions_materialized(
        output,
        refinement_materialization,
    )
    accepted_statuses = {
        "ready",
        "pass",
        "approved",
        "ready_with_bounded_risks",
        "ready_with_later_stage_risks",
        "ready_with_nonblocking_risks",
        "ready_with_required_downstream_gates",
        "ready_with_stage6_obligations",
    }
    if current_materialization_ready:
        accepted_statuses.add("needs_stage5_refinement_before_stage6_retry")
        accepted_statuses.add("needs_stage5_contract_refinement_before_stage6")
    has_stage5_refinement_actions = any(
        isinstance(action, dict) and str(action.get("id") or "").startswith("stage5.")
        for action in output.get("executable_actions", [])
    )
    refinement_required_status = (
        ("stage5" in status or has_stage5_refinement_actions)
        and "refinement" in status
        and ("required" in status or "need" in status)
    )
    status_accepted = (
        status in accepted_statuses
        or status.startswith("ready_with_")
        or status.startswith("ready_for_")
        or (refinement_required_status and current_stage5_refinements_cover_planner)
    )
    if status and not status_accepted:
        errors.append(f"verification_planner_agent status is {output.get('status')}")
    risks = output.get("risks", [])
    if isinstance(risks, list) and risks:
        blocking = []
        for risk in risks:
            text = str(risk).strip().lower()
            if not text:
                continue
            if (
                "no current-stage blocking" in text
                or "no current-stage blocker" in text
                or "no current stage blocking" in text
                or "no current stage blocker" in text
            ):
                continue
            explicit_current_stage_blocker = (
                "current-stage blocking" in text
                or "current stage blocking" in text
                or "current-stage blocker" in text
                or "current stage blocker" in text
                or "blocking risk" in text
                or "unresolved current-stage" in text
                or "unresolved current stage" in text
                or "missing current-stage" in text
                or "missing current stage" in text
                or "cannot promote stage5" in text
                or "cannot promote stage 6" in text
                or "stage5 promotion blocked" in text
                or "stage 6 promotion blocked" in text
                or "block stage5" in text
                or "block stage 6" in text
            )
            if (
                "later-stage" in text
                or "downstream" in text
                or "later tools" in text
                or "later stages" in text
                or "later checker" in text
                or "later board" in text
                or "later functional" in text
                or "later simulation" in text
                or "later artifact" in text
                or "later closure" in text
            ):
                continue
            if "vcs" in text or "vivado" in text or "bitstream" in text or "board" in text:
                if "current-stage" not in text and "blocking" not in text:
                    continue
            if current_stage5_refinements_cover_planner:
                materialization_failure = (
                    "unmaterialized" in text
                    or "materialization failed" in text
                    or "failed to materialize" in text
                    or "materialization incomplete" in text
                    or "action coverage failed" in text
                    or "current-stage static check failed" in text
                    or "current stage static check failed" in text
                )
                if not materialization_failure:
                    continue
            if status_accepted and not explicit_current_stage_blocker:
                continue
            if reviewed_refinement_ready and (
                "current-stage refinement risk" in text
                or "stage5 refinement" in text
                or "refined contract" in text
                or "missing action/llm quality audit" in text
            ):
                continue
            blocking.append(str(risk))
        if blocking:
            errors.append(f"verification_planner_agent reported {len(blocking)} current-stage unresolved risk(s)")
    return errors


def action_audit_errors(action_audit: dict[str, Any]) -> list[str]:
    if action_audit.get("status") == "pass":
        return []
    return [
        f"LLM executable action grounding failed: {action_audit.get('summary')}",
        *[
            f"ungrounded action {item.get('id')}: tools={item.get('unknown_tool_roles')} checkers={item.get('unknown_acceptance_checkers')}"
            for item in action_audit.get("ungrounded_actions", [])[:6]
        ],
    ]


def llm_quality_errors(llm_quality: dict[str, Any]) -> list[str]:
    if llm_quality.get("status") != "fail":
        return []
    summary = llm_quality.get("summary", {}) if isinstance(llm_quality.get("summary"), dict) else {}
    return [
        f"LLM I/O quality failed: {summary.get('failed_agents', 0)} failed agent(s)",
        *[str(error) for error in summary.get("errors", [])[:8]],
    ]


def compact_action_for_planner(action: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": action.get("id"),
        "stage": action.get("stage"),
        "action_type": action.get("action_type"),
        "tool_roles": action.get("tool_roles", []),
        "acceptance_checkers": action.get("acceptance_checkers", []),
        "consumes_count": len(action.get("consumes", [])),
        "produces_count": len(action.get("produces", [])),
        "requires_approval": action.get("requires_approval"),
        "on_failure": compact_prompt_text(str(action.get("on_failure") or ""), 180),
    }


def compact_debug_closure_for_planner(contract: dict[str, Any]) -> dict[str, Any]:
    debug_contract = contract.get("debug_closure_contract", {}) if isinstance(contract.get("debug_closure_contract"), dict) else {}
    trace_schema = debug_contract.get("trace_record_schema", {}) if isinstance(debug_contract.get("trace_record_schema"), dict) else {}
    instrumentation = debug_contract.get("instrumentation_contract", {}) if isinstance(debug_contract.get("instrumentation_contract"), dict) else {}
    replay = debug_contract.get("targeted_replay", {}) if isinstance(debug_contract.get("targeted_replay"), dict) else {}
    repair = debug_contract.get("repair_handoff_contract", {}) if isinstance(debug_contract.get("repair_handoff_contract"), dict) else {}
    paths = trace_schema.get("path_binding", {}) if isinstance(trace_schema.get("path_binding"), dict) else {}
    return {
        "schema_version": debug_contract.get("schema_version"),
        "contract_type": debug_contract.get("contract_type"),
        "boundary_count": len(debug_contract.get("boundaries", [])) if isinstance(debug_contract.get("boundaries"), list) else 0,
        "causal_path_count": len(debug_contract.get("causal_paths", [])) if isinstance(debug_contract.get("causal_paths"), list) else 0,
        "trace_required_fields": trace_schema.get("required_fields", []),
        "trace_paths": paths,
        "instrumentation_monitor_points": instrumentation.get("monitor_points", []),
        "instrumentation_modes": instrumentation.get("modes", []),
        "targeted_replay_strategy": replay.get("strategy"),
        "repair_handoff_required_fields": repair.get("required_fields", []),
        "policy": debug_contract.get("policy", {}),
    }


def compact_team_summary_for_planner(design_team: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": design_team.get("status"),
        "split_required": design_team.get("split_required"),
        "decomposition_source": design_team.get("decomposition_source"),
        "decomposer_used_fallback": design_team.get("decomposer_used_fallback"),
        "subtask_count": design_team.get("subtask_count"),
        "completed_subtasks": design_team.get("completed_subtasks"),
        "used_fallback_count": design_team.get("used_fallback_count"),
        "errors": design_team.get("errors", [])[:8],
        "approval_required_for": [
            compact_prompt_text(str(value), 180)
            for value in design_team.get("approval_required_for", [])[:8]
        ],
        "executable_actions": [
            compact_action_for_planner(action)
            for action in design_team.get("executable_actions", [])[:32]
            if isinstance(action, dict)
        ],
        "llm_io_metrics": design_team.get("llm_io_metrics", {}),
    }


def compact_plan_for_planner(plan: dict[str, Any]) -> dict[str, Any]:
    hierarchy = plan.get("hierarchical_verification", {}) if isinstance(plan.get("hierarchical_verification"), dict) else {}
    maturity = hierarchy.get("maturity_contract", {}) if isinstance(hierarchy.get("maturity_contract"), dict) else {}
    return {
        "schema_version": plan.get("schema_version"),
        "stage": plan.get("stage"),
        "status": plan.get("status"),
        "checker_summary": plan.get("checker_summary", {}),
        "checker_plan": plan.get("checker_plan", []),
        "constraints_touched": plan.get("constraints_touched", []),
        "constraints_referenced": plan.get("constraints_referenced", []),
        "hierarchical_verification": {
            "strategy": hierarchy.get("strategy"),
            "stage_agent_count": len(hierarchy.get("stage_agents", [])),
            "merge_agent_count": len(hierarchy.get("merge_agents", [])),
            "evidence_gate_names": [gate.get("name") for gate in hierarchy.get("evidence_gates", []) if isinstance(gate, dict)],
            "policy": hierarchy.get("policy", {}),
            "maturity_levels": [
                {
                    "id": level.get("id"),
                    "required_before": level.get("required_before"),
                    "required_gates": level.get("required_gates", []),
                    "required_tool_roles": level.get("required_tool_roles", []),
                }
                for level in maturity.get("levels", [])
                if isinstance(level, dict)
            ],
        },
        "stage_gate_policy": plan.get("stage_gate_policy", {}),
    }


def compact_review_for_planner(review: dict[str, Any]) -> dict[str, Any]:
    upstream = review.get("upstream_evidence", {}) if isinstance(review.get("upstream_evidence"), dict) else {}
    stage3 = upstream.get("stage3_pipeline_plan", {}) if isinstance(upstream.get("stage3_pipeline_plan"), dict) else {}
    stage4 = upstream.get("stage4_parameter_binding", {}) if isinstance(upstream.get("stage4_parameter_binding"), dict) else {}
    stage5 = upstream.get("stage5_code_generation", {}) if isinstance(upstream.get("stage5_code_generation"), dict) else {}
    return {
        "schema_version": review.get("schema_version"),
        "stage": review.get("stage"),
        "status": review.get("status"),
        "checker_summary": review.get("checker_summary", {}),
        "checker_results": [
            {
                "checker": row.get("checker"),
                "status": row.get("status"),
                "execution_status": row.get("execution_status"),
                "evidence_phase": row.get("evidence_phase"),
                "summary": compact_prompt_text(str(row.get("summary") or ""), 180),
                "errors": row.get("errors", [])[:4],
            }
            for row in review.get("checker_results", [])
            if isinstance(row, dict)
        ],
        "stage_gate_policy": review.get("stage_gate_policy", {}),
        "upstream_evidence": {
            "stage3_pipeline_plan": {
                "status": stage3.get("status"),
                "checker_summary": stage3.get("checker_summary", {}),
                "stage_count": stage3.get("stage_count"),
                "data_edge_count": stage3.get("data_edge_count"),
                "stream_edge_count": stage3.get("stream_edge_count"),
                "attention_semantics_present": bool(stage3.get("attention_semantics")),
            },
            "stage4_parameter_binding": {
                "status": stage4.get("status"),
                "checker_summary": stage4.get("checker_summary", {}),
                "global_params": stage4.get("global_params", {}),
                "numeric_binding_plan": stage4.get("numeric_binding_plan", {}),
            },
            "stage5_code_generation": {
                "status": stage5.get("status"),
                "compile_gate": stage5.get("compile_gate", {}),
                "contract_check": stage5.get("contract_check", {}),
                "package_static_check": stage5.get("package_static_check", {}),
                "generated_files_count": stage5.get("generated_files_count"),
            },
        },
        "parameter_binding_count": len(review.get("parameter_bindings", [])) if isinstance(review.get("parameter_bindings"), list) else 0,
        "attention_semantics_present": bool(review.get("attention_semantics")),
        "constraints_touched": review.get("constraints_touched", []),
        "constraints_referenced": review.get("constraints_referenced", []),
    }


def compact_contract_for_planner(contract: dict[str, Any]) -> dict[str, Any]:
    dag = contract.get("verification_gate_dag", {}) if isinstance(contract.get("verification_gate_dag"), dict) else {}
    nodes = [row for row in dag.get("nodes", []) if isinstance(row, dict)]
    leaf_nodes = [row for row in nodes if str(row.get("name") or "").startswith("leaf_stage.")]
    critical_nodes = [row for row in nodes if not str(row.get("name") or "").startswith("leaf_stage.")]
    evidence_rows = [row for row in contract.get("evidence_path_requirements", []) if isinstance(row, dict)]
    return {
        "schema_version": contract.get("schema_version"),
        "status": contract.get("status"),
        "summary": contract.get("summary"),
        "errors": [compact_prompt_text(str(value), 240) for value in contract.get("errors", [])[:16]],
        "warnings": [compact_prompt_text(str(value), 240) for value in contract.get("warnings", [])[:12]],
        "policy": contract.get("policy", {}),
        "retry_reconciliation_contract": compact_prompt_value(contract.get("retry_reconciliation_contract", {}), max_dict_depth=2, max_list_depth=1, max_items=8, max_str_len=180),
        "backtrack_contract": compact_prompt_value(contract.get("backtrack_contract", {}), max_dict_depth=2, max_list_depth=1, max_items=8, max_str_len=180),
        "case_adapter": contract.get("case_adapter", {}),
        "required_evidence_gate_names": [
            str(gate.get("name"))
            for gate in contract.get("required_evidence_gates", [])
            if isinstance(gate, dict) and gate.get("name")
        ],
        "required_tool_protocols": [
            {
                "name": row.get("name"),
                "role": row.get("role"),
                "scope": row.get("scope"),
                "kind": row.get("kind"),
                "configured": row.get("configured"),
                "evidence_status": row.get("evidence_status"),
            }
            for row in contract.get("required_tool_protocols", [])
            if isinstance(row, dict)
        ],
        "functional_sim_candidates": [
            {
                "name": row.get("name"),
                "scope": row.get("scope"),
                "kind": row.get("kind"),
                "acceptance_role": row.get("acceptance_role"),
            }
            for row in contract.get("functional_sim_candidates", [])
            if isinstance(row, dict)
        ],
        "gate_protocol_coverage": compact_prompt_value(
            contract.get("gate_protocol_coverage", {}),
            max_dict_depth=3,
            max_list_depth=1,
            max_items=64,
            max_str_len=160,
        ),
        "evidence_path_requirements_summary": {
            "count": len(evidence_rows),
            "gate_names": [str(row.get("gate")) for row in evidence_rows[:64] if row.get("gate")],
            "phases": sorted({str(row.get("phase")) for row in evidence_rows if row.get("phase")}),
        },
        "verification_gate_dag": {
            "policy": compact_prompt_value(dag.get("policy", {}), max_dict_depth=2, max_list_depth=1, max_items=16, max_str_len=120),
            "node_count": len(nodes),
            "edge_count": len(dag.get("edges", [])) if isinstance(dag.get("edges"), list) else 0,
            "leaf_node_count": len(leaf_nodes),
            "phase_order": dag.get("policy", {}).get("hierarchical_order", []) if isinstance(dag.get("policy"), dict) else [],
            "critical_nodes": [
                {
                    "name": row.get("name"),
                    "phase": row.get("phase"),
                    "depends_on": row.get("depends_on", [])[:32],
                    "tool_roles": row.get("tool_roles", [])[:24],
                    "required_maturity": row.get("required_maturity"),
                    "evidence_status": row.get("evidence_status"),
                }
                for row in critical_nodes[:32]
            ],
        },
        "debug_closure_contract": compact_debug_closure_for_planner(contract),
        "existing_stage5_refinements": compact_prompt_value(
            contract.get("existing_stage5_refinements", {}),
            max_dict_depth=2,
            max_list_depth=1,
            max_items=24,
            max_str_len=160,
        ),
        "stage5_refinement_materialization": compact_prompt_value(
            contract.get("stage5_refinement_materialization", {}),
            max_dict_depth=2,
            max_list_depth=1,
            max_items=24,
            max_str_len=160,
        ),
    }


def stage5_refinement_artifacts_for_state(state: dict[str, Any]) -> dict[str, Any]:
    ids = [
        "artifact.stage5.refinement_manifest",
        "artifact.stage5.stage6_gate_selector_contract",
        "artifact.stage5.downstream_artifact_blocklist",
        "artifact.stage5.dependency_blocked_manifest_schema",
        "artifact.stage5.functional_sim_real_tool_nodes",
        "artifact.stage5.debug_trace_manifest_schema",
        "artifact.stage5.failure_localization_schema",
        "artifact.stage5.backend_app_shell_target_discovery_policy",
        "artifact.stage5.canonical_gate_dag_refinement",
        "artifact.stage5.semantic_promotion_gate_matrix",
        "artifact.stage5.immutable_semantic_identity_contract",
        "artifact.stage5.canonical_functional_sim_binding_contract",
        "artifact.stage5.backend_eligibility_gate_contract",
        "artifact.stage5.failed_node_repair_route_matrix",
        "artifact.stage5.certificate_reuse_and_target_discovery_contract",
        "artifact.stage5.action_materialization_coverage",
    ]
    found = {}
    by_id = {str(item.get("id")): item for item in state.get("artifacts", []) if isinstance(item, dict)}
    for artifact_id in ids:
        item = by_id.get(artifact_id)
        if not item:
            continue
        path = item.get("path")
        found[artifact_id] = {
            "path": path,
            "exists": Path(str(path)).exists() if path else False,
            "producer_transition": item.get("producer_transition"),
        }
    return {
        "schema_version": "spatialaccagent.stage5_existing_refinements.v0",
        "status": "present" if found else "missing",
        "artifacts": found,
    }


def stage5_gate_tool_roles(case_adapter: dict[str, Any], gate: str) -> list[str]:
    def include_if_present(role: str) -> list[str]:
        return [role] if adapter_tool(case_adapter, role) else []

    if gate.startswith("leaf_stage."):
        return ["stage_leaf_static"]
    role_by_gate = {
        gate_name(case_adapter, "real_weight_artifacts"): ["weight_manifest_generate", "real_weight_artifacts"],
        gate_name(case_adapter, "target_model_reference"): ["target_model_reference_generate"],
        gate_name(case_adapter, "semantic_testbench"): ["semantic_testbench_generate"],
        gate_name(case_adapter, "boundary_contract"): ["boundary_contract_check"],
        gate_name(case_adapter, "stage_leaf_static"): ["stage_leaf_static"],
        gate_name(case_adapter, "leaf_functional"): ["leaf_functional_sim"],
        gate_name(case_adapter, "leaf_golden_compare"): ["leaf_golden_compare"],
        gate_name(case_adapter, "operator_leaf_semantic_evidence"): ["operator_leaf_semantic_evidence"],
        gate_name(case_adapter, "tb_scaffold"): ["tb_scaffold_generate", "tb_scaffold"],
        gate_name(case_adapter, "single_layer_kernel"): [
            "tb_scaffold_generate",
            "stage_leaf_static",
            "leaf_functional_sim",
            "leaf_golden_compare",
            "tb_scaffold",
            "single_layer_kernel",
        ],
        gate_name(case_adapter, "single_layer_functional"): ["single_layer_functional_sim"],
        gate_name(case_adapter, "single_layer_golden_compare"): ["single_layer_golden_compare"],
        gate_name(case_adapter, "single_layer_semantic_evidence"): ["single_layer_semantic_evidence"],
        gate_name(case_adapter, "multilayer_pipeline"): [
            "tb_scaffold_generate",
            "single_layer_kernel",
            "single_layer_functional_sim",
            "single_layer_golden_compare",
            "multilayer_pipeline",
        ],
        gate_name(case_adapter, "multilayer_functional"): ["multilayer_functional_sim"],
        gate_name(case_adapter, "pipeline_deadlock"): ["pipeline_deadlock_check"],
        gate_name(case_adapter, "board_interface_discovery"): ["board_interface_discovery"],
        gate_name(case_adapter, "axi_ddr_interface"): [
            "axi_ddr_interface",
        ],
        gate_name(case_adapter, "axi_protocol"): ["axi_protocol_check"],
        gate_name(case_adapter, "ddr_image_roundtrip"): ["ddr_image_roundtrip"],
        gate_name(case_adapter, "board_semantic_evidence"): ["board_semantic_evidence"],
        gate_name(case_adapter, "functional_sim"): ["vcs_functional_sim", "vcs_evidence_analyzer", "deadlock_axi_check"],
        gate_name(case_adapter, "vivado_synthesis"): ["vivado_synthesis", "vivado_synthesis_report_check"],
        gate_name(case_adapter, "vivado_implementation"): ["vivado_implementation", "vivado_implementation_report_check"],
        gate_name(case_adapter, "runtime_bitstream"): ["runtime_bitstream"],
        gate_name(case_adapter, "runtime_abi"): ["runtime_abi_check"],
        gate_name(case_adapter, "board_runtime"): ["board_runtime"],
    }
    return role_by_gate.get(gate, [])


def later_gates_after(contract: dict[str, Any], gate: str) -> list[str]:
    dag = contract.get("verification_gate_dag", {}) if isinstance(contract.get("verification_gate_dag"), dict) else {}
    names = [str(node.get("name")) for node in dag.get("nodes", []) if isinstance(node, dict) and node.get("name")]
    if gate not in names:
        return []
    return names[names.index(gate) + 1 :]


def build_semantic_promotion_gate_matrix(
    case_adapter: dict[str, Any],
    gate_selector: dict[str, Any],
) -> dict[str, Any]:
    bindings = [
        {
            "level": "operator_leaf_functional",
            "certificate": gate_selector.get("operator_leaf_promotion_certificate", {}),
            "aggregate_gate": gate_name(case_adapter, "operator_leaf_semantic_evidence"),
            "semantic_tool_role": "operator_leaf_semantic_evidence",
        },
        {
            "level": "single_layer_functional",
            "certificate": gate_selector.get("single_layer_promotion_certificate", {}),
            "aggregate_gate": gate_name(case_adapter, "single_layer_semantic_evidence"),
            "semantic_tool_role": "single_layer_semantic_evidence",
        },
        {
            "level": "axi_ddr_functional",
            "certificate": gate_selector.get("board_axi_ddr_promotion_certificate", {}),
            "aggregate_gate": gate_name(case_adapter, "board_semantic_evidence"),
            "semantic_tool_role": "board_semantic_evidence",
        },
    ]
    errors = []
    for binding in bindings:
        roles = stage5_gate_tool_roles(case_adapter, str(binding["aggregate_gate"]))
        binding["mandatory_gate_tool_roles"] = roles
        if binding["semantic_tool_role"] not in roles:
            errors.append(
                f"{binding['level']} semantic role {binding['semantic_tool_role']} "
                f"is not mandatory in gate {binding['aggregate_gate']}"
            )
    return {
        "schema_version": "spatialaccagent.semantic_promotion_gate_matrix.v0",
        "status": "ready" if not errors else "incomplete",
        "errors": errors,
        "policy": {
            "all_gate_tool_roles_must_pass": True,
            "semantic_aggregate_is_required_for_promotion": True,
            "raw_simulator_or_compare_output_alone_cannot_promote": True,
            "complete_transformer_block_weight_consumption_required": True,
            "same_checkpoint_input_reference_numeric_and_testbench_identity_required": True,
        },
        "levels": bindings,
    }


def build_immutable_semantic_identity_contract(
    case_adapter: dict[str, Any],
    gate_selector: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "spatialaccagent.immutable_semantic_identity_contract.v0",
        "status": "ready",
        "accelerator_scope": "transformer_blocks_only",
        "required_identity_fields": [
            "checkpoint_manifest_hash",
            "complete_checkpoint_tensor_catalog_hash",
            "required_transformer_block_tensor_set_hash",
            "input_seed_shape_dtype_and_hash",
            "target_model_reference_manifest_hash",
            "numeric_policy_hash",
            "comparison_tolerance_hash",
            "model_semantic_adapter_hash",
            "semantic_testbench_manifest_hash",
            "generated_testbench_and_harness_hashes",
            "generated_dut_source_hash",
            "dut_weight_binding_manifest_hash",
            "executed_weight_consumption_evidence_hash",
        ],
        "required_preparation_gates": [
            gate_name(case_adapter, "real_weight_artifacts"),
            gate_name(case_adapter, "target_model_reference"),
            gate_name(case_adapter, "semantic_testbench"),
        ],
        "promotion_contracts": {
            "operator_leaf": gate_selector.get("operator_leaf_promotion_certificate", {}).get("evidence_contract", {}),
            "single_layer": gate_selector.get("single_layer_promotion_certificate", {}).get("evidence_contract", {}),
            "board_axi_ddr": gate_selector.get("board_axi_ddr_promotion_certificate", {}).get("evidence_contract", {}),
        },
        "policy": {
            "identity_mismatch_invalidates_affected_certificate": True,
            "expected_output_only_from_real_target_model_same_input_and_checkpoint": True,
            "random_or_rtl_derived_expected_output_forbidden": True,
            "embedding_final_norm_lm_head_logits_and_sampling_out_of_scope": True,
            "same_loop_mutation_forbidden": True,
        },
    }


def build_canonical_functional_sim_binding_contract(
    case_adapter: dict[str, Any],
    contract: dict[str, Any],
) -> dict[str, Any]:
    dag = contract.get("verification_gate_dag", {}) if isinstance(contract.get("verification_gate_dag"), dict) else {}
    nodes = {
        str(node.get("name")): node
        for node in dag.get("nodes", [])
        if isinstance(node, dict) and node.get("name")
    }
    functional_gate = gate_name(case_adapter, "functional_sim")
    derived_gates = [
        gate_name(case_adapter, "multilayer_functional"),
        gate_name(case_adapter, "pipeline_deadlock"),
        gate_name(case_adapter, "axi_protocol"),
        gate_name(case_adapter, "ddr_image_roundtrip"),
    ]
    candidates = [
        row for row in contract.get("functional_sim_candidates", [])
        if isinstance(row, dict)
    ]
    accepted_candidates = [
        str(row.get("name"))
        for row in candidates
        if "real_functional_sim" in str(row.get("kind") or "").lower()
        and "liveness" not in str(row.get("kind") or "").lower()
    ]
    rejected_candidates = [
        str(row.get("name"))
        for row in candidates
        if "liveness" in str(row.get("kind") or "").lower()
        or "smoke" in str(row.get("kind") or "").lower()
    ]
    errors = []
    if functional_gate not in nodes:
        errors.append(f"missing canonical functional gate {functional_gate}")
    if not accepted_candidates:
        errors.append("no real functional-simulation candidate is bound")
    for gate in derived_gates:
        node = nodes.get(gate, {})
        if functional_gate not in node.get("depends_on", []):
            errors.append(f"derived gate {gate} does not depend on {functional_gate}")
    return {
        "schema_version": "spatialaccagent.canonical_functional_sim_binding_contract.v0",
        "status": "ready" if not errors else "incomplete",
        "errors": errors,
        "canonical_gate": functional_gate,
        "accepted_real_tool_candidates": accepted_candidates,
        "diagnostic_only_candidates": rejected_candidates,
        "mandatory_gate_tool_roles": stage5_gate_tool_roles(case_adapter, functional_gate),
        "derived_consumer_gates": derived_gates,
        "run_identity_required_fields": [
            "run_id",
            "checkpoint_hash",
            "stimulus_hash",
            "target_model_reference_hash",
            "numeric_policy_and_tolerance_hash",
            "semantic_testbench_hash",
            "dut_source_and_weight_binding_hash",
            "exact_sample_wrapper_and_simulation_source_hashes",
            "ddr_input_weight_output_image_hashes",
            "simulator_command_and_log_hashes",
        ],
        "policy": {
            "one_canonical_board_wrapped_run_per_repair_iteration": True,
            "all_derived_gates_must_consume_the_same_run_identity": True,
            "exact_user_sample_wrapper_required": True,
            "simplified_or_wrapper_free_simulation_forbidden": True,
            "liveness_only_candidate_cannot_satisfy_functional_acceptance": True,
        },
    }


def build_backend_eligibility_gate_contract(
    case_adapter: dict[str, Any],
    contract: dict[str, Any],
    gate_selector: dict[str, Any],
) -> dict[str, Any]:
    dag = contract.get("verification_gate_dag", {}) if isinstance(contract.get("verification_gate_dag"), dict) else {}
    nodes = {
        str(node.get("name")): node
        for node in dag.get("nodes", [])
        if isinstance(node, dict) and node.get("name")
    }
    strict_board_gates = list(
        gate_selector.get("board_axi_ddr_promotion_certificate", {}).get("required_gates", [])
    )
    board_bringup_gate = gate_name(case_adapter, "board_bringup")
    synth_gate = gate_name(case_adapter, "vivado_synthesis")
    impl_gate = gate_name(case_adapter, "vivado_implementation")
    runtime_gate = gate_name(case_adapter, "runtime_bitstream")
    runtime_abi_gate = gate_name(case_adapter, "runtime_abi")
    board_gate = gate_name(case_adapter, "board_runtime")
    synth_node = nodes.get(synth_gate, {})
    impl_node = nodes.get(impl_gate, {})
    runtime_node = nodes.get(runtime_gate, {})
    runtime_abi_node = nodes.get(runtime_abi_gate, {})
    board_node = nodes.get(board_gate, {})
    # Vivado implementation is admitted by the minimal real-board bring-up
    # contract.  The strict board-functional certificate remains available for
    # diagnostics and later runtime closure, but is not a prerequisite for
    # synthesis/implementation under the current acceptance policy.
    implementation_entry_gates = [board_bringup_gate]
    missing_dependencies = sorted(set(implementation_entry_gates).difference(synth_node.get("depends_on", [])))
    synth_roles = list(synth_node.get("tool_roles", []))
    impl_roles = list(impl_node.get("tool_roles", []))
    errors = [f"Vivado synthesis bypasses required third-layer gate {gate}" for gate in missing_dependencies]
    if "vivado_synthesis_report_check" not in synth_roles:
        errors.append("Vivado synthesis report checker is not a mandatory synthesis-gate tool")
    if "vivado_implementation_report_check" not in impl_roles:
        errors.append("Vivado implementation report checker is not a mandatory implementation-gate tool")
    runtime_identity_gates = [
        gate_name(case_adapter, "real_weight_artifacts"),
        gate_name(case_adapter, "target_model_reference"),
        gate_name(case_adapter, "semantic_testbench"),
        gate_name(case_adapter, "board_interface_discovery"),
        gate_name(case_adapter, "axi_ddr_interface"),
        gate_name(case_adapter, "board_semantic_evidence"),
    ]
    runtime_missing = sorted(set(runtime_identity_gates).difference(runtime_node.get("depends_on", [])))
    board_missing = sorted(set(runtime_identity_gates).difference(board_node.get("depends_on", [])))
    abi_identity_gates = [
        runtime_gate,
        gate_name(case_adapter, "board_interface_discovery"),
        gate_name(case_adapter, "axi_ddr_interface"),
        gate_name(case_adapter, "board_semantic_evidence"),
    ]
    abi_missing = sorted(set(abi_identity_gates).difference(runtime_abi_node.get("depends_on", [])))
    errors.extend(f"runtime bitstream gate lacks explicit identity dependency {gate}" for gate in runtime_missing)
    errors.extend(f"runtime ABI gate lacks explicit identity dependency {gate}" for gate in abi_missing)
    errors.extend(f"board runtime gate lacks explicit semantic identity dependency {gate}" for gate in board_missing)
    return {
        "schema_version": "spatialaccagent.backend_eligibility_gate_contract.v0",
        "status": "ready" if not errors else "incomplete",
        "errors": errors,
        "required_board_closure_gates": strict_board_gates,
        "implementation_entry_gates": implementation_entry_gates,
        "backend_entry_gate": synth_gate,
        "backend_entry_dependencies": synth_node.get("depends_on", []),
        "synthesis_mandatory_tool_roles": synth_roles,
        "implementation_mandatory_tool_roles": impl_roles,
        "runtime_bitstream_gate": runtime_gate,
        "runtime_bitstream_dependencies": runtime_node.get("depends_on", []),
        "runtime_abi_gate": runtime_abi_gate,
        "runtime_abi_dependencies": runtime_abi_node.get("depends_on", []),
        "board_runtime_gate": board_gate,
        "board_runtime_dependencies": board_node.get("depends_on", []),
        "runtime_identity_gates": runtime_identity_gates,
        "policy": {
            "board_bringup_certificate_required_before_vivado": True,
            "all_strict_third_layer_subgates_required_before_vivado": False,
            "complete_token_output_required_before_vivado": False,
            "final_ddr_writeback_required_before_vivado": False,
            "vivado_exit_code_without_report_checks_is_not_acceptance": True,
            "implementation_package_timing_resource_and_drc_evidence_required": True,
            "board_runtime_requires_deployment_identity_and_target_model_output_validity": True,
        },
    }


def build_failed_node_repair_route_matrix(
    case_adapter: dict[str, Any],
    contract: dict[str, Any],
) -> dict[str, Any]:
    dag = contract.get("verification_gate_dag", {}) if isinstance(contract.get("verification_gate_dag"), dict) else {}
    routes = []
    for node in dag.get("nodes", []):
        if not isinstance(node, dict) or not node.get("name"):
            continue
        gate = str(node["name"])
        routes.append(
            {
                "gate": gate,
                "phase": node.get("phase"),
                "tool_roles": node.get("tool_roles", stage5_gate_tool_roles(case_adapter, gate)),
                "failure_evidence": node.get("planned_produces", []),
                "first_action": "classify_real_tool_failure_and_collect_boundary_trace_or_trace_unavailable_record",
                "localization": "CCTG earliest violated boundary and causal slice",
                "repair_authority": "bounded contract-preserving repair only",
                "rerun": gate,
                "lower_layer_backtrack": "allowed only with a current-layer trace naming the contradicted lower-layer gate or module",
            }
        )
    node_count = len([node for node in dag.get("nodes", []) if isinstance(node, dict) and node.get("name")])
    return {
        "schema_version": "spatialaccagent.failed_node_repair_route_matrix.v0",
        "status": "ready" if node_count > 0 and len(routes) == node_count else "incomplete",
        "route_count": len(routes),
        "dag_node_count": node_count,
        "routes": routes,
        "trace_unavailable_classification": {
            "required_when_tool_fails_before_dut_observation": True,
            "must_not_fabricate_boundary_trace": True,
            "next_action": "repair tool/harness/contract capability or rerun the same gate with trace instrumentation",
        },
        "repair_authority": {
            "architecture_numeric_memory_layout_runtime_abi_or_wrapper_change_requires_approval": True,
            "golden_tolerance_checkpoint_stimulus_or_testbench_mutation_forbidden_inside_same_loop": True,
        },
    }


def build_certificate_reuse_and_target_discovery_contract(
    gate_selector: dict[str, Any],
    backend_policy: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "spatialaccagent.certificate_reuse_and_target_discovery_contract.v0",
        "status": "ready",
        "certificate_contracts": {
            "operator_leaf": gate_selector.get("operator_leaf_promotion_certificate", {}),
            "single_layer": gate_selector.get("single_layer_promotion_certificate", {}),
            "board_axi_ddr": gate_selector.get("board_axi_ddr_promotion_certificate", {}),
        },
        "certificate_reuse_policy": {
            "reuse_only_when_all_immutable_identity_hashes_match": True,
            "select_earliest_stale_or_unclosed_layer": True,
            "passed_lower_layer_is_reusable_not_absolute": True,
            "targeted_backtrack_requires_bound_contradicting_trace": True,
        },
        "exact_sample_project_target_discovery": {
            "policy": backend_policy.get("policy", {}),
            "required_facts": [
                "sample_project_root_identity",
                "exact_top_and_wrapper_source_hashes",
                "exact_simulation_source_hashes",
                "clock_reset_and_constraint_source_hashes",
                "AXI_DDR_port_address_width_burst_and_data_order_facts",
            ],
            "ambiguous_target_requires_explicit_approval": True,
            "framework_default_or_guessed_target_forbidden": True,
        },
    }


def build_stage5_action_materialization_coverage(
    planner_actions: list[dict[str, Any]],
    materialized: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    requirements = {
        "cross_layer_semantic_gate_refinement": [
            "semantic_promotion_gate_matrix",
            "immutable_semantic_identity_contract",
        ],
        "board_functional_gate_dag_refinement": [
            "canonical_functional_sim_binding_contract",
            "backend_eligibility_gate_contract",
        ],
        "downstream_tool_gate_hardening": ["backend_eligibility_gate_contract"],
        "repair_boundary_contract_review": ["failed_node_repair_route_matrix"],
        "stage6_gate_selector_contract_refinement": [
            "stage6_gate_selector_contract",
            "certificate_reuse_and_target_discovery_contract",
        ],
        "verification_gate_dag_refinement": [
            "canonical_gate_dag_refinement",
            "stage6_gate_selector_contract",
            "semantic_promotion_gate_matrix",
            "immutable_semantic_identity_contract",
            "canonical_functional_sim_binding_contract",
            "backend_eligibility_gate_contract",
            "certificate_reuse_and_target_discovery_contract",
        ],
        "board_and_backend_gate_dag_refinement": [
            "canonical_gate_dag_refinement",
            "canonical_functional_sim_binding_contract",
            "backend_eligibility_gate_contract",
            "certificate_reuse_and_target_discovery_contract",
            "failed_node_repair_route_matrix",
        ],
        "verification_artifact_contract_refinement": [
            "semantic_promotion_gate_matrix",
            "immutable_semantic_identity_contract",
            "failed_node_repair_route_matrix",
        ],
        "gate_enablement_check": [
            "stage6_gate_selector_contract",
            "backend_eligibility_gate_contract",
        ],
        "sacg_constraint_review": ["certificate_reuse_and_target_discovery_contract"],
    }
    rows = []
    promotion_actions = []
    for action in planner_actions:
        action_id = str(action.get("id") or "")
        action_type = str(action.get("action_type") or "").strip().lower()
        if action_type in {"verification_contract_promotion", "stage_contract_validation"}:
            promotion_actions.append(action)
            continue
        required_artifacts = requirements.get(action_type)
        if required_artifacts is None:
            rows.append(
                {
                    "id": action_id,
                    "action_type": action_type,
                    "status": "unmaterialized",
                    "required_artifacts": [],
                    "errors": [f"unsupported Stage6 refinement action_type: {action_type or '<missing>'}"],
                }
            )
            continue
        missing = [name for name in required_artifacts if name not in materialized]
        incomplete = [
            name for name in required_artifacts
            if name in materialized and materialized[name].get("status") not in {"ready", "pass"}
        ]
        errors = [f"missing materialized artifact {name}" for name in missing]
        errors.extend(f"materialized artifact {name} is not ready" for name in incomplete)
        rows.append(
            {
                "id": action_id,
                "action_type": action_type,
                "status": "pass" if not errors else "unmaterialized",
                "required_artifacts": required_artifacts,
                "errors": errors,
            }
        )
    prior_errors = [error for row in rows for error in row.get("errors", [])]
    for action in promotion_actions:
        action_type = str(action.get("action_type") or "verification_contract_promotion").strip().lower()
        rows.append(
            {
                "id": str(action.get("id") or ""),
                "action_type": action_type,
                "status": "pass" if not prior_errors else "unmaterialized",
                "required_artifacts": sorted(materialized),
                "errors": list(prior_errors),
                "fulfillment": "ready_for_stage5_static_checks_and_transition_promotion",
            }
        )
    errors = [error for row in rows for error in row.get("errors", [])]
    return {
        "schema_version": "spatialaccagent.stage5_action_materialization_coverage.v0",
        "status": "ready" if rows and not errors else "incomplete",
        "errors": errors,
        "actions": rows,
    }


def materialize_canonical_gate_dag_refinement(
    contract: dict[str, Any],
    case_adapter: dict[str, Any],
    planner_actions: list[dict[str, Any]],
) -> dict[str, Any]:
    action_types = {
        str(action.get("action_type") or "").strip().lower()
        for action in planner_actions
        if isinstance(action, dict)
    }
    semantic_types = {
        "cross_layer_semantic_gate_refinement",
        "verification_gate_dag_refinement",
        "verification_artifact_contract_refinement",
    }
    board_backend_types = {
        "board_and_backend_gate_dag_refinement",
        "board_functional_gate_dag_refinement",
        "downstream_tool_gate_hardening",
        "verification_gate_dag_refinement",
    }
    dag = contract.get("verification_gate_dag", {}) if isinstance(contract.get("verification_gate_dag"), dict) else {}
    nodes = [node for node in dag.get("nodes", []) if isinstance(node, dict) and node.get("name")]
    by_name = {str(node.get("name")): node for node in nodes}
    errors: list[str] = []
    additions: list[dict[str, str]] = []

    def require_dependencies(gate: str, dependencies: list[str], reason: str) -> None:
        node = by_name.get(gate)
        if node is None:
            errors.append(f"canonical DAG refinement target gate is missing: {gate}")
            return
        current = [str(dep) for dep in node.get("depends_on", []) if str(dep)]
        for dependency in dependencies:
            if dependency not in by_name:
                errors.append(f"canonical DAG refinement dependency is missing: {dependency} -> {gate}")
                continue
            if dependency not in current:
                current.append(dependency)
                additions.append({"from": dependency, "to": gate, "reason": reason})
        node["depends_on"] = current

    if action_types.intersection(semantic_types):
        require_dependencies(
            gate_name(case_adapter, "single_layer_golden_compare"),
            [
                gate_name(case_adapter, "real_weight_artifacts"),
                gate_name(case_adapter, "target_model_reference"),
                gate_name(case_adapter, "semantic_testbench"),
            ],
            "bind connected-layer golden comparison directly to the immutable real-weight semantic baseline",
        )

    if action_types.intersection(board_backend_types):
        runtime_identity_gates = [
            gate_name(case_adapter, "real_weight_artifacts"),
            gate_name(case_adapter, "target_model_reference"),
            gate_name(case_adapter, "semantic_testbench"),
            gate_name(case_adapter, "board_interface_discovery"),
            gate_name(case_adapter, "axi_ddr_interface"),
            gate_name(case_adapter, "board_semantic_evidence"),
        ]
        require_dependencies(
            gate_name(case_adapter, "vivado_implementation"),
            [gate_name(case_adapter, "board_interface_discovery"), gate_name(case_adapter, "board_semantic_evidence")],
            "preserve exact board-source and semantic identity through implementation",
        )
        require_dependencies(
            gate_name(case_adapter, "runtime_bitstream"),
            runtime_identity_gates,
            "bind the runtime bitstream to the exact board and immutable semantic baseline",
        )
        require_dependencies(
            gate_name(case_adapter, "runtime_abi"),
            [
                gate_name(case_adapter, "runtime_bitstream"),
                gate_name(case_adapter, "board_interface_discovery"),
                gate_name(case_adapter, "axi_ddr_interface"),
                gate_name(case_adapter, "board_semantic_evidence"),
            ],
            "bind runtime ABI acceptance to the exact board interface and board semantic certificate",
        )
        require_dependencies(
            gate_name(case_adapter, "board_runtime"),
            runtime_identity_gates,
            "require final board runtime to retain checkpoint, reference, testbench, wrapper, and weight identity",
        )

    node_names = set(by_name)
    dag["edges"] = [
        {
            "from": str(dependency),
            "to": str(node.get("name")),
            "type": "gate_dependency",
            "policy": "producer gate must pass before consumer gate can execute",
        }
        for node in nodes
        for dependency in node.get("depends_on", [])
        if str(dependency) in node_names
    ]
    contract["verification_gate_dag"] = dag
    return {
        "schema_version": "spatialaccagent.canonical_gate_dag_refinement.v0",
        "status": "ready" if not errors else "incomplete",
        "errors": errors,
        "applied_action_types": sorted(action_types.intersection(semantic_types | board_backend_types)),
        "canonical_contract_mutated": True,
        "dependency_additions": additions,
        "policy": {
            "semantic_identity_edges_are_explicit": True,
            "exact_board_source_identity_flows_through_backend_and_runtime": True,
            "final_board_runtime_has_direct_semantic_identity_dependencies": True,
            "planner_actions_are_materialized_not_only_listed": True,
        },
    }


def write_stage5_refinement_artifacts(
    out_dir: Path,
    state: dict[str, Any],
    plan: dict[str, Any],
    contract: dict[str, Any],
    planner_output: dict[str, Any],
    design_team: dict[str, Any],
    case_adapter: dict[str, Any],
) -> dict[str, Any]:
    refined_dir = out_dir / "refinements"
    refined_dir.mkdir(parents=True, exist_ok=True)
    planner_actions = [
        action for action in planner_output.get("executable_actions", [])
        if isinstance(action, dict)
        and (
            str(action.get("stage") or "").startswith("stage5")
            or str(action.get("id") or "").startswith("stage5.")
        )
    ]
    canonical_gate_dag_refinement = materialize_canonical_gate_dag_refinement(
        contract,
        case_adapter,
        planner_actions,
    )
    dag = contract.get("verification_gate_dag", {}) if isinstance(contract.get("verification_gate_dag"), dict) else {}
    nodes = [node for node in dag.get("nodes", []) if isinstance(node, dict) and node.get("name")]
    single_layer_required = [
        gate_name(case_adapter, "tb_scaffold"),
        gate_name(case_adapter, "single_layer_kernel"),
        gate_name(case_adapter, "single_layer_functional"),
        gate_name(case_adapter, "single_layer_golden_compare"),
        gate_name(case_adapter, "single_layer_semantic_evidence"),
    ]
    operator_leaf_required = [
        gate_name(case_adapter, "real_weight_artifacts"),
        gate_name(case_adapter, "target_model_reference"),
        gate_name(case_adapter, "semantic_testbench"),
        gate_name(case_adapter, "stage_leaf_static"),
        gate_name(case_adapter, "boundary_contract"),
        gate_name(case_adapter, "leaf_functional"),
        gate_name(case_adapter, "leaf_golden_compare"),
        gate_name(case_adapter, "operator_leaf_semantic_evidence"),
    ]
    single_layer_aliases = {
        "single_layer_kernel": {
            "canonical_gate": gate_name(case_adapter, "single_layer_kernel"),
            "aliases": sorted(
                {
                    "single_transformer_layer",
                    "case_single_transformer_layer",
                    gate_name(case_adapter, "single_layer_kernel"),
                }
            ),
            "policy": "all aliases refer to the connected single transformer-layer kernel gate; pass evidence must bind to the canonical gate",
        }
    }
    axi_ddr_subchecks = [
        {
            "gate": gate_name(case_adapter, "axi_ddr_interface"),
            "required_checkers": [
                "addr_map_check",
                "transfer_count_check",
                "data_order_trace_check",
                "memory_runtime_plan_check",
            ],
            "required_tool_roles": ["board_interface_discovery", "axi_ddr_interface"],
        },
        {
            "gate": gate_name(case_adapter, "axi_protocol"),
            "required_checkers": ["axi_protocol_check", "data_order_trace_check", "deadlock_watchdog"],
            "required_tool_roles": ["axi_protocol_check"],
        },
        {
            "gate": gate_name(case_adapter, "ddr_image_roundtrip"),
            "required_checkers": ["ddr_image_roundtrip", "transfer_count_check", "artifact_hash_check"],
            "required_tool_roles": ["ddr_image_roundtrip"],
        },
    ]
    multilayer_gate = gate_name(case_adapter, "multilayer_pipeline")
    operator_leaf_blocklist = later_gates_after(contract, gate_name(case_adapter, "operator_leaf_semantic_evidence"))
    single_layer_blocklist = later_gates_after(contract, gate_name(case_adapter, "single_layer_semantic_evidence"))
    memory = sacg_memory_summary(state, limit=24)
    debug_contract = contract.get("debug_closure_contract", {}) if isinstance(contract.get("debug_closure_contract"), dict) else {}
    trace_schema = debug_contract.get("trace_record_schema", {}) if isinstance(debug_contract.get("trace_record_schema"), dict) else {}

    gate_selector = {
        "schema_version": "spatialaccagent.stage6_gate_selector_contract.v0",
        "status": "ready",
        "source": "stage5_planner_action_materialization",
        "debug_loop_contract": hierarchical_debug_loop_contract(),
        "debug_layers": [
            "operator_leaf_modules",
            "single_transformer_layer_kernel",
            "board_axi_ddr_wrapped_system",
        ],
        "hierarchical_order": dag.get("policy", {}).get("hierarchical_order", []) if isinstance(dag.get("policy"), dict) else [],
        "debug_scope_order": ["operator_leaf_closure", "single_layer_closure", "board_axi_ddr_closure"],
        "selector_rules": [
            "execute a gate only when every declared dependency gate has pass evidence from the current trusted run",
            "when a gate fails, stop at that debug layer and route evidence to the Stage-6 repair loop before any higher-layer gate runs",
            "later verification/repair artifacts may be used as debug clues only, never as pass certificates",
            "lower-layer pass evidence is reusable evidence, not an absolute truth claim",
            "reopen a passed lower-layer gate only when current-layer CCTG/boundary trace explicitly contradicts it and names the challenged gate or module",
            "if a trace claims lower-layer contradiction without a challenged gate/module binding, rerun the failed current-layer trace before backtracking",
        ],
        "operator_leaf_promotion_certificate": {
            "required_gates": operator_leaf_required,
            "required_artifact": "artifact.stage6.operator_leaf_promotion_certificate",
            "blocks_until_present": operator_leaf_blocklist,
            "evidence_contract": evidence_contract_for_level("operator_leaf_functional"),
            "evidence_semantics": {
                "allows_next_hierarchical_layer": "single_transformer_layer_kernel",
                "does_not_claim_full_model_semantic_correctness": True,
                "does_not_claim_integration_or_board_correctness": True,
                "higher_layer_cctg_trace_may_challenge_leaf_only_with_bound_gate_or_module": True,
            },
        },
        "single_layer_promotion_certificate": {
            "required_gates": single_layer_required,
            "required_artifact": "artifact.stage6.single_layer_promotion_certificate",
            "blocks_until_present": single_layer_blocklist,
            "evidence_contract": evidence_contract_for_level("single_layer_functional"),
        },
        "gate_aliases": single_layer_aliases,
        "axi_ddr_memory_runtime_subchecks": axi_ddr_subchecks,
        "multilayer_promotion_certificate": {
            "required_gates": [
                multilayer_gate,
                gate_name(case_adapter, "multilayer_functional"),
                gate_name(case_adapter, "pipeline_deadlock"),
            ],
            "required_artifact": "artifact.stage6.multilayer_pipeline_promotion_certificate",
            "blocks_until_present": later_gates_after(contract, gate_name(case_adapter, "pipeline_deadlock")),
            "third_layer_subgate": True,
            "debug_layer": "board_axi_ddr_wrapped_system",
            "evidence_contract": evidence_contract_for_level("multilayer_pipeline_functional"),
        },
        "board_axi_ddr_promotion_certificate": {
            "required_gates": [
                multilayer_gate,
                gate_name(case_adapter, "board_interface_discovery"),
                gate_name(case_adapter, "axi_ddr_interface"),
                gate_name(case_adapter, "functional_sim"),
                gate_name(case_adapter, "multilayer_functional"),
                gate_name(case_adapter, "pipeline_deadlock"),
                gate_name(case_adapter, "axi_protocol"),
                gate_name(case_adapter, "ddr_image_roundtrip"),
                gate_name(case_adapter, "board_semantic_evidence"),
            ],
            "required_artifact": "artifact.stage6.board_axi_ddr_promotion_certificate",
            "debug_layer": "board_axi_ddr_wrapped_system",
            "blocks_until_present": later_gates_after(contract, gate_name(case_adapter, "board_semantic_evidence")),
            "evidence_contract": evidence_contract_for_level("axi_ddr_functional"),
        },
        "gates": [
            {
                "name": str(node.get("name")),
                "phase": node.get("phase"),
                "depends_on": node.get("depends_on", []),
                "tool_roles": stage5_gate_tool_roles(case_adapter, str(node.get("name"))),
                "evidence_status": node.get("evidence_status"),
            }
            for node in nodes
        ],
    }
    downstream_blocklist = {
        "schema_version": "spatialaccagent.downstream_artifact_blocklist.v0",
        "status": "ready",
        "source_active_contamination_barriers": memory.get("active_contamination_barriers", []),
        "source_open_retry_requests": memory.get("open_retry_requests", []),
        "policy": {
            "lower_layer_pass_evidence_is_reusable_not_absolute": True,
            "targeted_lower_layer_backtrack_requires_contradicting_current_layer_trace": True,
            "do_not_reopen_passed_lower_layer_without_contradicting_boundary_trace": True,
        },
        "blocklist_rules": [
            {
                "blocked_gates": operator_leaf_blocklist,
                "until_artifact": "artifact.stage6.operator_leaf_promotion_certificate",
                "reason": "operator-leaf functional/static/golden gates must pass before single-layer, multilayer, AXI/DDR, backend, bitstream, or board runtime gates",
            },
            {
                "blocked_gates": single_layer_blocklist,
                "until_artifact": "artifact.stage6.single_layer_promotion_certificate",
                "reason": "single-layer functional and golden comparison must pass before multilayer, AXI/DDR, backend, bitstream, or board runtime gates",
            },
            {
                "blocked_artifacts": [
                    "artifact.stage6.verification_result",
                    "artifact.stage6.real_tool_results",
                    "artifact.stage6.debug_closure",
                    "artifact.stage6.repair_plan",
                ],
                "allowed_use": "planning_or_debug_only_until_superseded_by_current_trusted_rerun",
            },
        ],
    }
    dependency_schema = {
        "schema_version": "spatialaccagent.dependency_blocked_manifest_schema.v0",
        "required_fields": ["gate", "blocked_by", "reason", "required_artifact", "source_gate_selector"],
        "status_values": ["blocked", "not_run", "ready_after_dependency_pass", "pass", "fail"],
        "policy": "dependency-blocked gates are not failures and must not trigger downstream RTL repair",
    }
    functional_nodes = {
        "schema_version": "spatialaccagent.functional_sim_real_tool_nodes.v0",
        "status": "ready",
        "functional_sim_candidates": contract.get("functional_sim_candidates", []),
        "required_tool_roles": ["vcs_functional_sim", "vcs_evidence_analyzer", "deadlock_axi_check"],
        "debug_layer": "board_axi_ddr_wrapped_system",
        "required_evidence": {
            "simulator": "real remote VCS/Verilator execution over generated RTL, immutable input, complete Transformer-block weight image, target-model boundary golden, exact sample wrapper, runtime config, and debug trace manifest",
            "analyzer": "evidence analyzer report that classifies timeout, deadlock, AXI, DDR, data-order, numeric, and boundary-trace failures",
            "non_acceptance": ["smoke", "compile-only", "report-presence-only", "liveness-without-functional-output"],
        },
        "acceptance_policy": {
            "real_functional_sim_required": True,
            "smoke_or_scaffold_liveness_is_not_acceptance": True,
            "requires_real_input_weight_and_runtime_abi_artifacts": True,
            "requires_target_model_reference_and_complete_transformer_block_weight_hashes": True,
        },
        "planned_gate": gate_name(case_adapter, "functional_sim"),
    }
    trace_manifest_schema = {
        "schema_version": "spatialaccagent.debug_trace_manifest_schema.v0",
        "status": "ready",
        "trace_record_schema": trace_schema,
        "instrumentation_contract": debug_contract.get("instrumentation_contract", {}),
        "targeted_replay": debug_contract.get("targeted_replay", {}),
        "required_outputs": [
            "verification/debug_closure/boundary_trace.json",
            "verification/debug_closure/failure_localization.json",
            "verification/debug_closure/targeted_replay_plan.json",
        ],
    }
    failure_localization_schema = {
        "schema_version": "spatialaccagent.failure_localization_schema.v0",
        "status": "ready",
        "required_fields": [
            "status",
            "failing_transaction",
            "causal_path",
            "earliest_failed_boundary",
            "root_candidate_module",
            "violated_contract",
            "minimal_repair_context",
        ],
        "policy": {
            "downstream_failure_requires_upstream_boundary_localization": True,
            "repair_agent_receives_causal_slice_not_full_rtl_by_default": True,
            "unlocalized_failure_backtracks_to_stage5_or_tool_capability_repair": True,
            "lower_layer_pass_evidence_is_reusable_not_absolute": True,
            "targeted_lower_layer_backtrack_requires_bound_contradicting_trace": True,
        },
    }
    backend_policy = {
        "schema_version": "spatialaccagent.backend_app_shell_target_discovery_policy.v0",
        "status": "ready",
        "policy": {
            "do_not_guess_app_shell_target_names": True,
            "require_cited_board_or_vivado_discovery_evidence": True,
            "runtime_bitstream_blocked_until_axi_ddr_and_functional_sim_pass": True,
            "ambiguous_target_requires_bounded_recovery_action": True,
        },
        "consumes_constraints": ["constraint.deployment.board", "constraint.runtime.board", "constraint.backend.package"],
    }
    semantic_gate_matrix = build_semantic_promotion_gate_matrix(case_adapter, gate_selector)
    semantic_identity = build_immutable_semantic_identity_contract(case_adapter, gate_selector)
    canonical_functional_sim = build_canonical_functional_sim_binding_contract(case_adapter, contract)
    backend_eligibility = build_backend_eligibility_gate_contract(case_adapter, contract, gate_selector)
    failed_node_routes = build_failed_node_repair_route_matrix(case_adapter, contract)
    certificate_reuse_and_target = build_certificate_reuse_and_target_discovery_contract(
        gate_selector,
        backend_policy,
    )
    materialized = {
        "canonical_gate_dag_refinement": canonical_gate_dag_refinement,
        "stage6_gate_selector_contract": gate_selector,
        "downstream_artifact_blocklist": downstream_blocklist,
        "dependency_blocked_manifest_schema": dependency_schema,
        "functional_sim_real_tool_nodes": functional_nodes,
        "debug_trace_manifest_schema": trace_manifest_schema,
        "failure_localization_schema": failure_localization_schema,
        "backend_app_shell_target_discovery_policy": backend_policy,
        "semantic_promotion_gate_matrix": semantic_gate_matrix,
        "immutable_semantic_identity_contract": semantic_identity,
        "canonical_functional_sim_binding_contract": canonical_functional_sim,
        "backend_eligibility_gate_contract": backend_eligibility,
        "failed_node_repair_route_matrix": failed_node_routes,
        "certificate_reuse_and_target_discovery_contract": certificate_reuse_and_target,
    }
    action_coverage = build_stage5_action_materialization_coverage(planner_actions, materialized)
    materialized["stage5_action_materialization_coverage"] = action_coverage
    paths: dict[str, str] = {}
    for name, data in materialized.items():
        path = refined_dir / f"{name}.json"
        write_json(path, data)
        paths[name] = str(path)
    manifest = {
        "schema_version": "spatialaccagent.stage5_refinement_manifest.v0",
        "status": "ready" if action_coverage.get("status") == "ready" else "incomplete",
        "errors": action_coverage.get("errors", []),
        "source": "verification_planner_agent_and_design_team_actions",
        "planner_status": planner_output.get("status"),
        "planner_action_ids": [str(action.get("id")) for action in planner_output.get("executable_actions", []) if isinstance(action, dict)],
        "materialized_stage5_action_ids": [
            str(row.get("id"))
            for row in action_coverage.get("actions", [])
            if isinstance(row, dict) and row.get("status") == "pass"
        ],
        "unmaterialized_stage5_actions": [
            row
            for row in action_coverage.get("actions", [])
            if isinstance(row, dict) and row.get("status") != "pass"
        ],
        "action_coverage": action_coverage,
        "design_team_status": design_team.get("status"),
        "policy": {
            "materialization_is_not_hardware_pass": True,
            "stage6_must_rerun_real_tools_after_stage5_promotion": True,
            "higher_layers_remain_blocked_until_lower_layer_certificates_exist": True,
            "lower_layer_pass_evidence_is_reusable_not_absolute": True,
            "higher_layer_trace_can_trigger_targeted_lower_layer_backtrack": True,
            "do_not_reopen_passed_lower_layer_without_contradicting_boundary_trace": True,
        },
        "artifacts": paths,
    }
    manifest_path = refined_dir / "stage5_refinement_manifest.json"
    write_json(manifest_path, manifest)
    return {
        "schema_version": "spatialaccagent.stage5_refinement_materialization.v0",
        "status": manifest["status"],
        "errors": manifest.get("errors", []),
        "manifest": str(manifest_path),
        "artifacts": paths,
    }


def update_sacg(
    source_state: Path,
    target_state: Path,
    plan_path: Path,
    contract_path: Path,
    review_path: Path,
    action_audit_path: Path,
    llm_quality_path: Path,
    refinement_materialization: dict[str, Any],
    plan: dict[str, Any],
    artifact_contract: dict[str, Any],
    action_audit: dict[str, Any],
    llm_quality: dict[str, Any],
    errors: list[str],
) -> str:
    state = copy_state(source_state, target_state)
    add_constraint(
        state,
        "constraint.verification.plan",
        "verification",
        [],
        [],
        ["artifact.stage5.verification_plan"],
        {"checkers": [item["checker"] for item in plan["checker_plan"]]},
    )
    add_constraint(
        state,
        "constraint.verification.hierarchy",
        "verification",
        [],
        [],
        ["artifact.stage5.verification_plan"],
        {
            "strategy": plan["hierarchical_verification"]["strategy"],
            "stage_agents": [item["id"] for item in plan["hierarchical_verification"]["stage_agents"]],
            "merge_agents": [item["id"] for item in plan["hierarchical_verification"]["merge_agents"]],
            "evidence_gates": [item["name"] for item in plan["hierarchical_verification"]["evidence_gates"]],
        },
    )
    add_constraint(
        state,
        "constraint.verification.artifacts",
        "verification",
        [],
        [],
        [
            "artifact.stage5.verification_artifact_contract",
            "artifact.stage5.verification_review_artifact",
            "artifact.stage5.refinement_manifest",
        ],
        {
            "status": artifact_contract.get("status"),
            "summary": artifact_contract.get("summary"),
            "required_tool_protocols": [item.get("name") for item in artifact_contract.get("required_tool_protocols", [])],
            "policy": artifact_contract.get("policy", {}),
            "refinement_materialization_status": refinement_materialization.get("status"),
            "refinement_manifest": refinement_materialization.get("manifest"),
            "llm_action_audit_status": action_audit.get("status"),
            "llm_action_audit_summary": action_audit.get("summary"),
            "llm_io_quality_status": llm_quality.get("status"),
            "llm_io_quality_summary": llm_quality.get("summary"),
        },
    )
    write_json(target_state, state)

    store = SACGStore(target_state)
    transition = store.declare_transition(
        action_type="verification_artifacts",
        touched_nodes=[],
        touched_edges=[],
        touched_constraints=TOUCHED_CONSTRAINTS,
        note="Created verification checker plan.",
    )
    transition["required_checkers"] = STAGE6_PROMOTION_CHECKERS
    store.bind_artifact(
        "artifact.stage5.verification_plan",
        str(plan_path),
        "stage.verification_plan",
        [],
        [],
        TOUCHED_CONSTRAINTS,
        transition["id"],
    )
    store.bind_artifact(
        "artifact.stage5.verification_review_artifact",
        str(review_path),
        "stage.verification_review_artifact",
        [],
        [],
        ["constraint.verification.artifacts", "constraint.verification.plan", "constraint.verification.hierarchy"],
        transition["id"],
    )
    store.bind_artifact(
        "artifact.stage5.verification_artifact_contract",
        str(contract_path),
        "stage.verification_artifact_contract",
        [],
        [],
        ["constraint.verification.artifacts"],
        transition["id"],
    )
    store.bind_artifact(
        "artifact.stage5.llm_action_audit",
        str(action_audit_path),
        "stage.llm_action_audit",
        [],
        [],
        ["constraint.verification.artifacts"],
        transition["id"],
    )
    store.bind_artifact(
        "artifact.stage5.llm_io_quality",
        str(llm_quality_path),
        "stage.llm_io_quality",
        [],
        [],
        ["constraint.verification.artifacts"],
        transition["id"],
    )
    refinement_ids = {
        "manifest": ("artifact.stage5.refinement_manifest", "stage.stage5_refinement_manifest"),
        "stage6_gate_selector_contract": (
            "artifact.stage5.stage6_gate_selector_contract",
            "stage.stage6_gate_selector_contract",
        ),
        "downstream_artifact_blocklist": (
            "artifact.stage5.downstream_artifact_blocklist",
            "stage.downstream_artifact_blocklist",
        ),
        "dependency_blocked_manifest_schema": (
            "artifact.stage5.dependency_blocked_manifest_schema",
            "stage.dependency_blocked_manifest_schema",
        ),
        "functional_sim_real_tool_nodes": (
            "artifact.stage5.functional_sim_real_tool_nodes",
            "stage.functional_sim_real_tool_nodes",
        ),
        "debug_trace_manifest_schema": (
            "artifact.stage5.debug_trace_manifest_schema",
            "stage.debug_trace_manifest_schema",
        ),
        "failure_localization_schema": (
            "artifact.stage5.failure_localization_schema",
            "stage.failure_localization_schema",
        ),
        "backend_app_shell_target_discovery_policy": (
            "artifact.stage5.backend_app_shell_target_discovery_policy",
            "stage.backend_app_shell_target_discovery_policy",
        ),
        "canonical_gate_dag_refinement": (
            "artifact.stage5.canonical_gate_dag_refinement",
            "stage.canonical_gate_dag_refinement",
        ),
        "semantic_promotion_gate_matrix": (
            "artifact.stage5.semantic_promotion_gate_matrix",
            "stage.semantic_promotion_gate_matrix",
        ),
        "immutable_semantic_identity_contract": (
            "artifact.stage5.immutable_semantic_identity_contract",
            "stage.immutable_semantic_identity_contract",
        ),
        "canonical_functional_sim_binding_contract": (
            "artifact.stage5.canonical_functional_sim_binding_contract",
            "stage.canonical_functional_sim_binding_contract",
        ),
        "backend_eligibility_gate_contract": (
            "artifact.stage5.backend_eligibility_gate_contract",
            "stage.backend_eligibility_gate_contract",
        ),
        "failed_node_repair_route_matrix": (
            "artifact.stage5.failed_node_repair_route_matrix",
            "stage.failed_node_repair_route_matrix",
        ),
        "certificate_reuse_and_target_discovery_contract": (
            "artifact.stage5.certificate_reuse_and_target_discovery_contract",
            "stage.certificate_reuse_and_target_discovery_contract",
        ),
        "stage5_action_materialization_coverage": (
            "artifact.stage5.action_materialization_coverage",
            "stage.stage5_action_materialization_coverage",
        ),
    }
    refinement_paths = {
        "manifest": refinement_materialization.get("manifest"),
        **(
            refinement_materialization.get("artifacts", {})
            if isinstance(refinement_materialization.get("artifacts"), dict)
            else {}
        ),
    }
    for key, value in refinement_paths.items():
        if not value or key not in refinement_ids:
            continue
        artifact_id, kind = refinement_ids[key]
        store.bind_artifact(
            artifact_id,
            str(value),
            kind,
            [],
            [],
            ["constraint.verification.artifacts", "constraint.verification.plan", "constraint.verification.hierarchy"],
            transition["id"],
        )
    existing_constraint_ids = {str(item.get("id")) for item in store.state.get("constraints", [])}

    def valid_constraints(values: list[Any], fallback: list[str]) -> list[str]:
        result = [str(value) for value in values if str(value) in existing_constraint_ids]
        return result if result else fallback

    for checker in plan["checker_plan"]:
        add_invariant(
            store.state,
            f"invariant.{checker['checker']}",
            checker["checker"],
            valid_constraints(checker.get("constraints", []), TOUCHED_CONSTRAINTS),
        )
    for checker in plan.get("checker_results", []):
        checker_name = str(checker.get("checker") or "")
        if not checker_name:
            continue
        add_invariant(
            store.state,
            f"invariant.{checker_name}",
            checker_name,
            valid_constraints(checker.get("constraints", []), ["constraint.verification.artifacts"]),
        )
    add_invariant(
        store.state,
        "invariant.verification_artifact_contract_check",
        "verification_artifact_contract_check",
        ["constraint.verification.artifacts"],
        "pass" if artifact_contract.get("status") == "pass" else "fail",
    )
    add_invariant(
        store.state,
        "invariant.verification_action_audit_check",
        "verification_action_audit_check",
        ["constraint.verification.artifacts"],
        "pass" if action_audit.get("status") == "pass" else "fail",
    )
    add_invariant(
        store.state,
        "invariant.llm_io_quality_check",
        "llm_io_quality_check",
        ["constraint.verification.artifacts"],
        "pass" if llm_quality.get("status") != "fail" else "fail",
    )
    for checker in plan.get("checker_results", []):
        checker_name = str(checker.get("checker") or "")
        if not checker_name:
            continue
        status = str(checker.get("status") or "unknown")
        if status not in {"pass", "fail", "unknown"}:
            status = "unknown"
        artifacts = ["artifact.stage5.verification_review_artifact"]
        if checker_name == "verification_artifact_contract_check":
            artifacts.append("artifact.stage5.verification_artifact_contract")
        if checker_name in {"verification_plan_static_check", "hierarchical_verification_plan_check", "sacg_reference_check"}:
            artifacts.append("artifact.stage5.verification_plan")
        store.attach_evidence(
            checker_name,
            status=status,
            invariant=f"invariant.{checker_name}",
            constraints=valid_constraints(checker.get("constraints", []), ["constraint.verification.artifacts"]),
            artifacts=artifacts,
            log_path=str(review_path if checker_name != "verification_artifact_contract_check" else contract_path),
            transition_id=transition["id"],
            summary=str(checker.get("summary") or ""),
        )
    store.attach_evidence(
        "verification_action_audit_check",
        status="pass" if action_audit.get("status") == "pass" else "fail",
        invariant="invariant.verification_action_audit_check",
        constraints=["constraint.verification.artifacts"],
        artifacts=["artifact.stage5.llm_action_audit"],
        log_path=str(action_audit_path),
        transition_id=transition["id"],
        summary=str(action_audit.get("summary") or ""),
    )
    llm_quality_summary = llm_quality.get("summary", {}) if isinstance(llm_quality.get("summary"), dict) else {}
    store.attach_evidence(
        "llm_io_quality_check",
        status="pass" if llm_quality.get("status") != "fail" else "fail",
        invariant="invariant.llm_io_quality_check",
        constraints=["constraint.verification.artifacts"],
        artifacts=["artifact.stage5.llm_io_quality"],
        log_path=str(llm_quality_path),
        transition_id=transition["id"],
        summary=str(llm_quality_summary),
    )
    if errors:
        store.reject(transition["id"], f"verification artifact planning failed gate checks: {errors[:8]}")
        store.record_failure_lesson(
            stage="stage5.verification_artifacts",
            failure_class="verification_gate_contract",
            summary=f"verification artifact planning failed gate checks: {errors[:8]}",
            violated_constraints=TOUCHED_CONSTRAINTS,
            artifacts=[
                "artifact.stage5.verification_plan",
                "artifact.stage5.verification_artifact_contract",
                "artifact.stage5.llm_action_audit",
            ],
            recommended_action="Backtrack to Stage6 and regenerate/refine the gate DAG/tool protocol contract before Stage7 executes real tools.",
            retry_scope="same_stage",
        )
        store.record_retry_request(
            stage="stage5.verification_artifacts",
            reason="Stage6 verification gate DAG or tool protocol contract is incomplete",
            target_stage="stage5.verification_artifacts",
            required_inputs=["artifact.stage5.design_artifact_manifest", "artifact.input.tool_protocols", "artifact.input.case_adapter"],
            blocked_artifacts=["artifact.stage5.verification_plan", "artifact.stage5.verification_artifact_contract"],
        )
    else:
        store.promote(transition["id"])
    store.record_stage_outcome(
        stage="stage5.verification_artifacts",
        status="ready" if not errors else "incomplete",
        transition_id=transition["id"],
        summary=str(artifact_contract.get("summary") or action_audit.get("summary") or "verification artifact planning completed"),
        errors=errors,
        artifacts=[
            "artifact.stage5.verification_plan",
            "artifact.stage5.verification_artifact_contract",
            "artifact.stage5.llm_action_audit",
            "artifact.stage5.llm_io_quality",
        ],
        next_actions=[] if not errors else ["retry stage5.verification_artifacts before Stage7 real-tool execution"],
        retryable=bool(errors),
    )
    store.save()
    return transition["id"]


def plan_verification(args: argparse.Namespace) -> tuple[Path, dict[str, Any]]:
    source_state = args.sacg_state.resolve()
    run_dir = run_dir_from_state(source_state)
    out_dir = run_dir / "verification_artifacts"
    plan_path = out_dir / "verification_plan.json"
    contract_path = out_dir / "verification_artifact_contract.json"
    review_path = out_dir / "verification_review_artifact.json"
    action_audit_path = out_dir / "llm_action_audit.json"
    llm_quality_path = out_dir / "llm_io_quality.json"
    state_path = out_dir / "sacg_state.json"
    report_path = out_dir / "verification_artifacts_report.json"

    source_data = read_json(source_state)
    plan = build_verification_plan(source_data)
    artifact_contract = build_verification_artifact_contract(source_data, plan, run_dir)
    review_artifact = build_verification_review_artifact(source_data, plan, artifact_contract)
    write_json(plan_path, plan)
    write_json(contract_path, artifact_contract)
    write_json(review_path, review_artifact)
    team = run_design_team(
        stage="verification_artifacts",
        objective=(
            "Plan and refine the real-tool verification gate DAG for the three repair-loop layers: "
            "operator leaf modules, a connected single transformer-layer kernel, and the board AXI/DDR "
            "wrapped system. Multi-layer pipeline, AXI/DDR, DDR image, and functional-simulation checks "
            "are third-layer subgates; Vivado bitstream and board runtime remain downstream after verification closure."
        ),
        state=source_data,
        candidate_artifact=review_artifact,
        out_dir=out_dir,
    )
    llm = run_stage_agent(
        agent="verification_planner_agent",
        stage="verification_artifacts",
        task="Review and refine the checker/tool gate DAG for real hierarchical verification; if later stages would lack coverage, propose bounded Stage6 contract updates before Stage7 runs real tools.",
        inputs={
            "candidate_verification_plan": compact_plan_for_planner(plan),
            "candidate_verification_artifact_contract": compact_contract_for_planner(artifact_contract),
            "candidate_verification_review_artifact": compact_review_for_planner(review_artifact),
            "retry_reconciliation_contract": artifact_contract.get("retry_reconciliation_contract", {}),
            "stage5_gate_dag_refinement_policy": {
                "required_order": [
                    "operator leaf modules",
                    "single transformer-layer LLM compute kernel",
                    "real target-board AXI/DDR wrapped system",
                ],
                "third_layer_internal_subgates": [
                    "LLM interpretation of Vivado-exported exact sample-project board facts",
                    "model-adaptive multi-layer spatial scheduler generation, ordering, and liveness",
                    "target-board AXI/DDR wrapper and protocol checks",
                    "DDR image roundtrip",
                    "remote VCS/Verilator functional simulation with real input/weight/runtime artifacts",
                ],
                "downstream_after_three_layer_closure": ["Vivado bitstream", "board runtime log"],
                "llm_role": "Use current SACG memory, generated artifacts, case adapter, and tool protocols to find missing real-world verification gates. If coverage is incomplete, return executable_actions that update Stage6 gate/tool contracts rather than allowing Stage7 to run with a weak plan.",
                "materializable_action_contract": {
                    "required_id_prefix": "stage5.",
                    "required_stage": "verification_artifacts",
                    "supported_action_types": [
                        "cross_layer_semantic_gate_refinement",
                        "board_functional_gate_dag_refinement",
                        "downstream_tool_gate_hardening",
                        "repair_boundary_contract_review",
                        "stage6_gate_selector_contract_refinement",
                        "verification_gate_dag_refinement",
                        "board_and_backend_gate_dag_refinement",
                        "verification_artifact_contract_refinement",
                        "gate_enablement_check",
                        "sacg_constraint_review",
                        "verification_contract_promotion",
                        "stage_contract_validation",
                    ],
                    "policy": (
                        "Every executable action that requests current Stage6 contract materialization must use the exact "
                        "stage, ID prefix, and one supported action_type above; do not invent aliases. Conditional future "
                        "or approval-required actions are proposed_actions, not current Stage6 materialization actions."
                    ),
                },
                "backtrack_rule": (
                    "Later stages may request a Stage6 contract backtrack when a missing gate/tool/evidence path is discovered. "
                    "A passed lower verification layer may be reopened only when the current-layer CCTG/boundary trace explicitly "
                    "contradicts that pass evidence and binds the contradiction to a challenged lower-layer gate or module; otherwise "
                    "rerun the failed current-layer trace first."
                ),
                "anti_spin_rule": "Do not treat lower-layer pass evidence as absolute, and do not broadly reopen lower layers without bound contradictory trace evidence.",
            },
            "design_team": compact_team_summary_for_planner(team_summary(team)),
            "source_sacg_state": str(source_state),
        },
        out_dir=out_dir,
        fallback_summary="Verification plan generated from pipeline and artifact manifest.",
    )
    design_team = team_summary(team)
    case_adapter = case_adapter_for_state(source_data, run_dir)
    refinement_materialization = write_stage5_refinement_artifacts(
        out_dir,
        source_data,
        plan,
        artifact_contract,
        llm["output"],
        design_team,
        case_adapter,
    )
    artifact_contract["stage5_refinement_materialization"] = refinement_materialization
    write_json(contract_path, artifact_contract)
    action_audit = build_audit_from_outputs(
        [
            ("verification_planner_agent", llm["output"]),
            ("design_team", design_team),
        ],
        case_adapter,
    )
    llm_quality = build_quality_report(rows_from_stage_records(llm, team))
    write_json(action_audit_path, action_audit)
    write_json(llm_quality_path, llm_quality)
    errors = list(artifact_contract.get("errors", []))
    errors.extend(team_failure_errors(design_team))
    errors.extend(
        stage_worker_errors(
            llm["output"],
            artifact_contract.get("existing_stage5_refinements", {}),
            refinement_materialization,
        )
    )
    errors.extend(action_audit_errors(action_audit))
    errors.extend(llm_quality_errors(llm_quality))
    transition_id = update_sacg(
        source_state,
        state_path,
        plan_path,
        contract_path,
        review_path,
        action_audit_path,
        llm_quality_path,
        refinement_materialization,
        plan,
        artifact_contract,
        action_audit,
        llm_quality,
        errors,
    )
    report = {
        "schema_version": "spatialaccagent.verification_artifacts_report.v0",
        "stage": "verification_artifacts",
        "status": "ready" if not errors else "incomplete",
        "source_sacg_state": str(source_state),
        "outputs": {
            "verification_plan": str(plan_path),
            "verification_artifact_contract": str(contract_path),
            "verification_review_artifact": str(review_path),
            "llm_action_audit": str(action_audit_path),
            "llm_io_quality": str(llm_quality_path),
            "stage5_refinement_manifest": refinement_materialization.get("manifest"),
            "stage5_refinement_artifacts": refinement_materialization.get("artifacts", {}),
            "sacg_state": str(state_path),
            "llm_agent": llm["result_path"],
            "team_subtask_plan": team["subtask_plan_path"],
            "team_aggregate": team["aggregate_path"],
        },
        "llm_agent": llm["output"],
        "llm_executable_actions": llm["output"].get("executable_actions", []),
        "design_team": design_team,
        "team_executable_actions": design_team.get("executable_actions", []),
        "llm_io_metrics": {
            "planner_prompt_bytes": llm.get("prompt_bytes"),
            "planner_duration_sec": llm.get("duration_sec"),
            "planner_executable_action_count": len(llm["output"].get("executable_actions", [])),
            "team": design_team.get("llm_io_metrics", {}),
        },
        "llm_action_audit": action_audit,
        "llm_io_quality": llm_quality,
        "stage5_refinement_materialization": refinement_materialization,
        "checkers": [item["checker"] for item in plan["checker_plan"]],
        "verification_artifact_contract": artifact_contract,
        "sacg_transition_id": transition_id,
        "errors": errors,
    }
    write_json(report_path, report)
    return report_path, report


def main(argv: list[str] | None = None) -> int:
    return run_sacg_stage("Verification artifact planning stage", plan_verification, argv)


if __name__ == "__main__":
    raise SystemExit(main())
