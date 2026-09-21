"""Team-style subtask decomposition and parallel stage agents."""

from __future__ import annotations

import json
import hashlib
import os
import socket
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from accagent.framework.sacg_utils import (
    hierarchical_learning_context,
    hierarchy_memory_context,
    sacg_memory_summary,
    sacg_memory_truth,
    safe_id,
    scoped_sacg_memory_summary,
    scoped_sacg_memory_truth,
    write_json,
)
from accagent.framework.llm_config import resolved_llm_cfg
from accagent.framework.llm_io import (
    PROMPT_PROTOCOL,
    build_prompt,
    parse_json_object,
    read_response_text,
    repair_prompt,
    response_payload,
    validate_schema,
)
from accagent.framework.stage_llm import (
    ACTION_GROUNDING_REGISTRY,
    ACTION_CONTRACT_EXAMPLES,
    llm_mode,
    llm_enforce,
    llm_policy_summary,
    llm_timeout_sec,
    run_stage_agent,
    retry_sleep_seconds,
    transient_llm_error,
    llm_transient_attempts,
    llm_transient_retry_unbounded,
)


TEAM_RULES = [
    "Act as an AI chip design team for FPGA spatial accelerator automatic design, not as isolated static scripts.",
    "Stay inside the SpatialAccAgent paper story: cross-layer consistency for LLM spatial accelerators.",
    "Treat SACG as the design team's shared memory and evidence ledger; do not rely on natural-language memory as correctness evidence.",
    "Treat sacg_memory_truth as the authoritative current blocker set; closed, superseded, or historical memory records are recovery evidence only.",
    "Use trusted templates and bounded glue code; do not propose free-form RTL rewrites outside approved repair boundaries.",
    "Map every observation to model, shape, numeric precision, data order, transfer unit, memory, runtime, implementation, or deployment constraints.",
    "Do not bypass checkers, modify golden outputs, loosen tolerance, or claim hardware pass without tool evidence.",
    "For functional verification, random generation may create input stimulus only; expected output must come from real target-model inference on the same immutable checkpoint and input.",
    "A weight manifest or memory image is not proof of DUT consumption; require complete tensor coverage, bound loader/harness hashes, and executed simulator evidence.",
    "Keep checkpoint, stimulus, reference-output, numeric-policy, tolerance, and semantic-testbench hashes immutable during repair; repair the DUT or integration instead.",
    "Require the exact user sample-project wrapper and source identity at board level, and keep model/board/example names out of framework-core decisions.",
    "The accelerator scope is Transformer blocks only; exclude embedding/tokenization, final model norm, LM head/logits, and sampling from DUT weight and golden requirements.",
    "For board/app-shell integration, use LLM reasoning to synthesize profile/contract policy from user-supplied materials and real tool evidence; do not encode board or model names as framework defaults.",
    "Use hash-validated hierarchical learning context to preserve certified lower-layer timing invariants; only a current named trace contradiction may reopen a lower layer.",
    "At board scope, keep independent AXI/prefetch progress separate from output/lifecycle-frontier progress, and treat a frontier stall as localization evidence rather than a root-cause or pass claim.",
    "Do not reopen a certified lower layer from a board output symptom alone; require current hash-bound direct core start/ingress/egress evidence, a named causal boundary, and the current lower-layer certificate binding.",
]


ROLE_CATALOG = [
    {
        "family": "model_shape",
        "keywords": ["model", "shape", "graph", "operator", "intake"],
        "capabilities": ["extract model semantics", "audit shape and head mapping", "track residual/operator order"],
        "constraint_focus": ["constraint.model.decoder", "constraint.shape.model"],
    },
    {
        "family": "numeric_template",
        "keywords": ["numeric", "template", "parameter", "dse", "resource"],
        "capabilities": ["bind trusted templates", "audit numeric policy", "check resource-risk assumptions"],
        "constraint_focus": [
            "constraint.numeric.policy",
            "constraint.template.library",
            "constraint.parameter.binding",
        ],
    },
    {
        "family": "data_memory_runtime",
        "keywords": ["data order", "transfer", "memory", "runtime", "dataflow", "stream", "beat"],
        "capabilities": ["audit data order", "check transfer-count/liveness risks", "bind DDR/runtime layout"],
        "constraint_focus": [
            "constraint.stream.order",
            "constraint.beat.pipeline",
            "constraint.memory.board",
            "constraint.runtime.board",
        ],
    },
    {
        "family": "verification_repair",
        "keywords": ["verification", "checker", "failure", "repair", "boundary", "auditor", "gate"],
        "capabilities": ["classify evidence", "map failures to violated constraints", "enforce repair boundaries"],
        "constraint_focus": ["constraint.verification.plan", "constraint.human.boundary"],
    },
    {
        "family": "implementation_deployment",
        "keywords": ["backend", "synthesis", "implementation", "timing", "board", "deployment"],
        "capabilities": ["prepare implementation handoff", "audit timing/board evidence", "block unsupported pass claims"],
        "constraint_focus": [
            "constraint.backend_board.plan",
            "constraint.backend.package",
            "constraint.deployment.board",
        ],
    },
]


TEAM_DECOMPOSER_SYSTEM = """You are the SpatialAccAgent design-team decomposer.

SpatialAccAgent is an FPGA spatial accelerator automatic design multi-agent
system modeled after an AI chip design team. The software framework is only the
execution substrate. Your job is to read the current request, stage state,
SACG memory, and tool evidence, then decide whether the design team needs
independent specialist agents. If it should, create a small set of parallel
sub-agents with clear roles and handoff boundaries. If it should not, return
split_required=false and no subtasks.

Keep every subtask aligned with the paper story: SACG-guided, template-
constrained, checker-verified design closure for cross-layer consistency.
Prefer an AI-chip-design-team plan: independent specialists in
parallel_group=0, then optional auditor/evidence-gate roles in parallel_group=1
if synthesis is needed. Every subtask must have a clear handoff rule and
acceptance checkers.
Return one JSON object only. No markdown.
"""


TEAM_DECOMPOSITION_SCHEMA = {
    "type": "object",
    "additionalProperties": True,
    "properties": {
        "schema_version": {"type": "string"},
        "stage": {"type": "string"},
        "split_required": {"type": "boolean"},
        "reason": {"type": "string"},
        "subtasks": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": True,
                "properties": {
                    "id": {"type": "string"},
                    "agent": {"type": "string"},
                    "role": {"type": "string"},
                    "role_profile": {"type": "object", "additionalProperties": True},
                    "role_assignment": {"type": "object", "additionalProperties": True},
                    "title": {"type": "string"},
                    "objective": {"type": "string"},
                    "constraints": {"type": "array", "items": {"type": "string"}},
                    "artifact_focus": {"type": "array", "items": {"type": "string"}},
                    "parallel_group": {"type": "integer"},
                    "handoff_required": {"type": "boolean"},
                    "action_type": {"type": "string"},
                    "expected_artifacts": {"type": "array", "items": {"type": "string"}},
                    "acceptance_checkers": {"type": "array", "items": {"type": "string"}},
                    "handoff_to": {"type": "array", "items": {"type": "string"}},
                    "handoff_rule": {"type": "object", "additionalProperties": True},
                },
                "required": [
                    "id",
                    "agent",
                "role",
                "title",
                "objective",
                    "constraints",
                    "artifact_focus",
                    "parallel_group",
                "handoff_required",
            ],
        },
    },
    },
    "required": ["schema_version", "stage", "split_required", "reason", "subtasks"],
}


class TeamDecompositionError(ValueError):
    pass


def prompt_hash(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def llm_cache_ignore_prompt_hash() -> bool:
    return os.environ.get("SPATIALACC_LLM_CACHE_IGNORE_PROMPT_HASH", "0").strip().lower() in {"1", "true", "yes", "on"}


def cached_successful_record(path: Path, expected_prompt_hash: str) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if data.get("error") or data.get("used_fallback"):
        return None
    if data.get("prompt_hash") != expected_prompt_hash and not llm_cache_ignore_prompt_hash():
        return None
    return data if isinstance(data.get("output"), dict) else None


def team_failure_errors(summary: dict[str, Any], prefix: str = "design_team") -> list[str]:
    errors = [f"{prefix}: {error}" for error in summary.get("errors", [])]
    if summary.get("decomposition_source") == "fallback" or summary.get("decomposer_used_fallback"):
        detail = summary.get("decomposer_error") or "LLM decomposition was unavailable"
        errors.append(f"{prefix}: team decomposer used fallback: {detail}")
    status = summary.get("status")
    if status not in {"ready", "no_split"}:
        errors.append(f"{prefix}: status is {status}")
    fallback_count = int(summary.get("used_fallback_count", 0) or 0)
    if fallback_count:
        errors.append(f"{prefix}: {fallback_count} subtask(s) used fallback")
    return errors


def candidate_hierarchy_context(candidate: dict[str, Any] | None) -> dict[str, str]:
    candidate = candidate if isinstance(candidate, dict) else {}
    repair_loop = (
        candidate.get("hierarchical_repair_loop", {})
        if isinstance(candidate.get("hierarchical_repair_loop"), dict)
        else {}
    )
    if not repair_loop:
        diagnostics = (
            candidate.get("diagnostics", {})
            if isinstance(candidate.get("diagnostics"), dict)
            else {}
        )
        repair_loop = (
            diagnostics.get("hierarchical_repair_loop", {})
            if isinstance(diagnostics.get("hierarchical_repair_loop"), dict)
            else {}
        )
    current_layer = (
        repair_loop.get("current_layer", {})
        if isinstance(repair_loop.get("current_layer"), dict)
        else {}
    )
    context = hierarchy_memory_context(
        verification_scope=candidate.get("execution_scope")
        or candidate.get("gate_execution_scope"),
        debug_layer=current_layer.get("id"),
    )
    return {
        key: str(context[key])
        for key in ("verification_scope", "debug_layer")
        if context.get(key)
    }


def compact_state_summary(
    state: dict[str, Any],
    candidate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    constraints = state.get("constraints", [])
    artifacts = state.get("artifacts", [])
    invariants = state.get("invariants", [])
    memory_scope = candidate_hierarchy_context(candidate)
    return {
        "design_id": state.get("design_id"),
        "nodes": len(state.get("nodes", [])),
        "edges": len(state.get("edges", [])),
        "constraints": [{"id": item.get("id"), "type": item.get("type")} for item in constraints],
        "artifacts": [{"id": item.get("id"), "type": item.get("type")} for item in artifacts],
        "failed_invariants": [
            {"id": item.get("id"), "checker": item.get("checker")}
            for item in invariants
            if item.get("status") == "fail"
        ],
        "sacg_memory": (
            scoped_sacg_memory_summary(state, limit=5, **memory_scope)
            if memory_scope
            else sacg_memory_summary(state, limit=5)
        ),
        "sacg_memory_truth": (
            scoped_sacg_memory_truth(state, **memory_scope)
            if memory_scope
            else sacg_memory_truth(state)
        ),
        "hierarchical_learning_context": hierarchical_learning_context(
            state, **memory_scope
        ),
    }


def compact_prompt_text(text: str, limit: int = 160) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"...<len={len(text)}>"


def compact_prompt_value(
    value: Any,
    *,
    depth: int = 0,
    max_dict_depth: int = 2,
    max_list_depth: int = 2,
    max_items: int = 5,
    max_str_len: int = 160,
) -> Any:
    if isinstance(value, str):
        return compact_prompt_text(value, max_str_len)
    if isinstance(value, bool) or value is None or isinstance(value, (int, float)):
        return value
    if isinstance(value, dict):
        if depth >= max_dict_depth:
            return {
                "_type": "dict",
                "_size": len(value),
                "_keys": sorted(str(key) for key in value.keys())[:max_items],
            }
        compacted: dict[str, Any] = {}
        for key in sorted(value.keys())[:max_items]:
            compacted[str(key)] = compact_prompt_value(
                value[key],
                depth=depth + 1,
                max_dict_depth=max_dict_depth,
                max_list_depth=max_list_depth,
                max_items=max_items,
                max_str_len=max_str_len,
            )
        if len(value) > max_items:
            compacted["_more_keys"] = len(value) - max_items
        return compacted
    if isinstance(value, list):
        if depth >= max_list_depth:
            return {"_type": "list", "_size": len(value)}
        items = [
            compact_prompt_value(
                item,
                depth=depth + 1,
                max_dict_depth=max_dict_depth,
                max_list_depth=max_list_depth,
                max_items=max_items,
                max_str_len=max_str_len,
            )
            for item in value[:max_items]
        ]
        if len(value) > max_items:
            items.append({"_more_items": len(value) - max_items})
        return items
    return compact_prompt_text(str(value), max_str_len)


def compact_subtask_plan_for_prompt(subtasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    compacted: list[dict[str, Any]] = []
    for item in subtasks[:12]:
        compacted.append(
            {
                "id": item.get("id"),
                "role": item.get("role"),
                "title": item.get("title"),
                "objective": compact_prompt_text(str(item.get("objective") or ""), 180),
                "role_profile": item.get("role_profile", {}),
                "role_assignment": compact_prompt_value(
                    item.get("role_assignment", {}),
                    max_dict_depth=2,
                    max_list_depth=1,
                    max_items=6,
                    max_str_len=120,
                ),
                "constraints": [str(value) for value in item.get("constraints", [])[:4]],
                "artifact_focus": [str(value) for value in item.get("artifact_focus", [])[:4]],
                "parallel_group": item.get("parallel_group"),
                "action_type": item.get("action_type"),
                "acceptance_checkers": [str(value) for value in item.get("acceptance_checkers", [])[:6]],
            }
        )
    if len(subtasks) > 12:
        compacted.append({"_more_subtasks": len(subtasks) - 12})
    return compacted


def compact_template_selection_for_prompt(candidate: dict[str, Any]) -> dict[str, Any]:
    def binding_row(row: dict[str, Any]) -> dict[str, Any]:
        bound = row.get("bound_params", {}) if isinstance(row.get("bound_params"), dict) else {}
        return {
            "op": row.get("op"),
            "template_id": row.get("template_id"),
            "source": row.get("source"),
            "status": row.get("status"),
            "missing_params": row.get("missing_params", []),
            "legality_errors": row.get("legality_errors", []),
            "bound_params": {
                key: {
                    "value": value.get("value"),
                    "status": value.get("status"),
                    "source": compact_prompt_text(str(value.get("source") or ""), 100),
                }
                for key, value in bound.items()
                if isinstance(value, dict)
            },
        }

    def source_row(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "op": row.get("op"),
            "template_id": row.get("template_id"),
            "source": row.get("source"),
            "path": row.get("path"),
            "sha256": row.get("sha256"),
            "exists": row.get("exists"),
            "case_class": row.get("case_class"),
            "status": row.get("status"),
            "errors": row.get("errors", []),
            "missing_required_params_in_constructor": row.get("missing_required_params_in_constructor", []),
            "source_required_params_missing_from_metadata": row.get("source_required_params_missing_from_metadata", []),
            "numeric_constructor_params_not_bound_by_metadata": row.get("numeric_constructor_params_not_bound_by_metadata", []),
        }

    return {
        "schema_version": candidate.get("schema_version"),
        "stage": candidate.get("stage"),
        "status": candidate.get("status"),
        "library_id": candidate.get("library_id"),
        "model_type": candidate.get("model_type"),
        "operator_sequence": candidate.get("operator_sequence", []),
        "selected_templates": [
            {
                "role": item.get("role"),
                "op": item.get("op"),
                "matched_op": item.get("matched_op"),
                "template_id": item.get("template_id"),
                "source": item.get("source"),
                "required_params": item.get("required_params", []),
            }
            for item in candidate.get("selected_templates", [])
        ],
        "coverage": candidate.get("coverage", {}),
        "missing_ops": candidate.get("missing_ops", []),
        "stage_gate_policy": candidate.get("stage_gate_policy", {}),
        "checker_results": [
            {
                "checker": item.get("checker"),
                "status": item.get("status"),
                "errors": item.get("errors", []),
                "warnings": item.get("warnings", []),
            }
            for item in candidate.get("checker_results", [])
        ],
        "parameter_bindings": [binding_row(row) for row in candidate.get("parameter_bindings", [])],
        "template_source_checks": [source_row(row) for row in candidate.get("template_source_checks", [])],
        "attention_semantics": candidate.get("attention_semantics", {}),
        "cross_layer_trace": candidate.get("cross_layer_trace", {}),
        "unsupported_bindings": candidate.get("unsupported_bindings", []),
        "required_adapters": candidate.get("required_adapters", []),
        "forbidden_edits": candidate.get("forbidden_edits", []),
        "errors": candidate.get("errors", []),
    }


def compact_pipeline_plan_for_prompt(candidate: dict[str, Any]) -> dict[str, Any]:
    def edge_row(edge: dict[str, Any]) -> dict[str, Any]:
        contract = edge.get("stream_contract", {}) if isinstance(edge.get("stream_contract"), dict) else {}
        return {
            "edge_id": edge.get("edge_id"),
            "src_stage": edge.get("src_stage"),
            "dst_stage": edge.get("dst_stage"),
            "kind": edge.get("kind"),
            "src_port": edge.get("src_port"),
            "dst_port": edge.get("dst_port"),
            "transfer_order": edge.get("transfer_order", []),
            "flow_control": edge.get("flow_control"),
            "element_bits": contract.get("element_bits"),
            "tensor": contract.get("tensor"),
            "transfer_count_bytes": contract.get("transfer_count_bytes"),
            "axi_beats": contract.get("axi_beats"),
            "stream_beats_per_axi_beat": contract.get("stream_beats_per_axi_beat"),
            "valid_byte_policy": contract.get("valid_byte_policy"),
        }

    def buffer_row(buffer: dict[str, Any]) -> dict[str, Any]:
        return {
            "buffer_id": buffer.get("buffer_id"),
            "edge_id": buffer.get("edge_id"),
            "kind": buffer.get("kind"),
            "implementation": buffer.get("implementation"),
            "depth": buffer.get("depth"),
            "resource_class": buffer.get("resource_class"),
            "purpose": buffer.get("purpose"),
        }

    def stage_row(stage: dict[str, Any]) -> dict[str, Any]:
        contract = stage.get("numeric_contract", {}) if isinstance(stage.get("numeric_contract"), dict) else {}
        return {
            "stage_id": stage.get("stage_id"),
            "index": stage.get("index"),
            "op": stage.get("op"),
            "template_id": stage.get("template_id"),
            "source": stage.get("source"),
            "input_shape": stage.get("input_shape"),
            "output_shape": stage.get("output_shape"),
            "numeric_contract": {
                "input_bits": contract.get("input_bits"),
                "internal_elem_bits": contract.get("internal_elem_bits"),
                "output_bits": contract.get("output_bits"),
                "accumulator_bits": contract.get("accumulator_bits"),
            },
            "latency": stage.get("latency"),
        }

    return {
        "schema_version": candidate.get("schema_version"),
        "stage": candidate.get("stage"),
        "status": candidate.get("status"),
        "model_type": candidate.get("model_type"),
        "pipeline_style": candidate.get("pipeline_style"),
        "stage_gate_policy": candidate.get("stage_gate_policy", {}),
        "stages": [stage_row(stage) for stage in candidate.get("stages", [])],
        "data_edges": [edge_row(edge) for edge in candidate.get("data_edges", [])],
        "stream_edges": [edge_row(edge) for edge in candidate.get("stream_edges", [])],
        "buffer_plan": [buffer_row(buffer) for buffer in candidate.get("buffer_plan", [])],
        "flow_control": candidate.get("flow_control", {}),
        "branch_join_contracts": candidate.get("branch_join_contracts", {}),
        "attention_contract": candidate.get("attention_contract", {}),
        "numeric_stream_policy": candidate.get("numeric_stream_policy", {}),
        "memory_schedule": {
            "policy": (candidate.get("memory_schedule") or {}).get("policy"),
            "num_layers": (candidate.get("memory_schedule") or {}).get("num_layers"),
            "target_seq_len": (candidate.get("memory_schedule") or {}).get("target_seq_len"),
            "sequence_semantics": (candidate.get("memory_schedule") or {}).get("sequence_semantics", {}),
            "required_regions": (candidate.get("memory_schedule") or {}).get("required_regions", []),
            "board_axi": (candidate.get("memory_schedule") or {}).get("board_axi", {}),
            "runtime_config_requirements": (candidate.get("memory_schedule") or {}).get("runtime_config_requirements", {}),
        },
        "checker_summary": candidate.get("checker_summary", {}),
        "checker_results": [
            {
                "checker": row.get("checker"),
                "status": row.get("status"),
                "summary": row.get("summary"),
                "errors": row.get("errors", []),
                "warnings": row.get("warnings", []),
            }
            for row in candidate.get("checker_results", [])
        ],
        "constraints_touched": candidate.get("constraints_touched", []),
    }


def compact_parameter_binding_for_prompt(candidate: dict[str, Any]) -> dict[str, Any]:
    def binding_row(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "stage_id": row.get("stage_id"),
            "op": row.get("op"),
            "template_id": row.get("template_id"),
            "params": row.get("params", {}),
            "legality_errors": row.get("legality_errors", []),
            "structural_dimensions": row.get("structural_dimensions", {}),
            "status": row.get("status"),
        }

    return {
        "schema_version": candidate.get("schema_version"),
        "stage": candidate.get("stage"),
        "status": candidate.get("status"),
        "binding_policy": candidate.get("binding_policy"),
        "stage_gate_policy": candidate.get("stage_gate_policy", {}),
        "global_params": candidate.get("global_params", {}),
        "global_param_scope": candidate.get("global_param_scope", {}),
        "bindings": [binding_row(row) for row in candidate.get("bindings", [])],
        "numeric_binding_plan": candidate.get("numeric_binding_plan", {}),
        "stream_contract_trace": candidate.get("stream_contract_trace", []),
        "axi_transfer_layout": candidate.get("axi_transfer_layout", {}),
        "checker_summary": candidate.get("checker_summary", {}),
        "checker_results": [
            {
                "checker": row.get("checker"),
                "status": row.get("status"),
                "summary": row.get("summary"),
                "errors": row.get("errors", []),
                "warnings": row.get("warnings", []),
            }
            for row in candidate.get("checker_results", [])
        ],
        "legality_errors": candidate.get("legality_errors", []),
        "constraints_touched": candidate.get("constraints_touched", []),
    }


def compact_code_generation_manifest_for_prompt(candidate: dict[str, Any]) -> dict[str, Any]:
    compile_gate = candidate.get("compile_gate", {}) if isinstance(candidate.get("compile_gate"), dict) else {}
    contract_check = candidate.get("contract_check", {}) if isinstance(candidate.get("contract_check"), dict) else {}
    package_static_check = candidate.get("package_static_check", {}) if isinstance(candidate.get("package_static_check"), dict) else {}
    return {
        "schema_version": candidate.get("schema_version"),
        "stage": candidate.get("stage"),
        "status": candidate.get("status"),
        "generation_policy": candidate.get("generation_policy"),
        "model_type": candidate.get("model_type"),
        "stage_gate_policy": candidate.get("stage_gate_policy", {}),
        "target_model_artifact_status": candidate.get("target_model_artifact_status", {}),
        "generated_package_root": candidate.get("generated_package_root"),
        "generated_top": candidate.get("generated_top", {}),
        "generated_memory_layout": candidate.get("generated_memory_layout"),
        "generated_runtime_config": candidate.get("generated_runtime_config"),
        "planned_code_outputs": [
            {
                "id": item.get("id"),
                "kind": item.get("kind"),
                "status": item.get("status"),
                "depends_on": item.get("depends_on", []),
                "template_sources": item.get("template_sources", []),
                "selected_operator_template_sources": item.get("selected_operator_template_sources", []),
            }
            for item in candidate.get("planned_code_outputs", [])
        ],
        "template_sources": candidate.get("template_sources", []),
        "selected_operator_template_sources": candidate.get("selected_operator_template_sources", []),
        "generated_files": candidate.get("generated_files", []),
        "compile_gate": {
            "status": compile_gate.get("status"),
            "summary": compile_gate.get("summary"),
            "enabled": compile_gate.get("enabled"),
            "elaboration_enabled": compile_gate.get("elaboration_enabled"),
            "returncode": compile_gate.get("returncode"),
            "cwd": compile_gate.get("cwd"),
            "log_path": compile_gate.get("log_path"),
            "steps": [
                {
                    "command": step.get("command"),
                    "status": step.get("status"),
                    "returncode": step.get("returncode"),
                    "stderr_tail": compact_prompt_text(str(step.get("stderr_tail") or ""), 120),
                    "stdout_tail": compact_prompt_text(str(step.get("stdout_tail") or ""), 240),
                }
                for step in compile_gate.get("steps", [])
            ],
        },
        "contract_check": {
            "checker": contract_check.get("checker"),
            "status": contract_check.get("status"),
            "summary": contract_check.get("summary"),
            "errors": contract_check.get("errors", []),
            "warnings": contract_check.get("warnings", []),
            "checked_contracts": contract_check.get("checked_contracts", []),
            "log_path": contract_check.get("log_path"),
        },
        "package_static_check": {
            "checker": package_static_check.get("checker"),
            "status": package_static_check.get("status"),
            "summary": package_static_check.get("summary"),
            "errors": package_static_check.get("errors", []),
            "warnings": package_static_check.get("warnings", []),
            "checked_contracts": package_static_check.get("checked_contracts", []),
            "log_path": package_static_check.get("log_path"),
        },
        "constraints_touched": candidate.get("constraints_touched", []),
    }


def compact_debug_closure_for_prompt(contract: dict[str, Any]) -> dict[str, Any]:
    debug_contract = contract.get("debug_closure_contract", {}) if isinstance(contract.get("debug_closure_contract"), dict) else {}
    trace_schema = debug_contract.get("trace_record_schema", {}) if isinstance(debug_contract.get("trace_record_schema"), dict) else {}
    instrumentation = debug_contract.get("instrumentation_contract", {}) if isinstance(debug_contract.get("instrumentation_contract"), dict) else {}
    replay = debug_contract.get("targeted_replay", {}) if isinstance(debug_contract.get("targeted_replay"), dict) else {}
    repair = debug_contract.get("repair_handoff_contract", {}) if isinstance(debug_contract.get("repair_handoff_contract"), dict) else {}
    return {
        "schema_version": debug_contract.get("schema_version"),
        "contract_type": debug_contract.get("contract_type"),
        "boundary_count": len(debug_contract.get("boundaries", [])) if isinstance(debug_contract.get("boundaries"), list) else 0,
        "causal_path_count": len(debug_contract.get("causal_paths", [])) if isinstance(debug_contract.get("causal_paths"), list) else 0,
        "trace_required_fields": trace_schema.get("required_fields", []),
        "trace_paths": trace_schema.get("path_binding", {}),
        "monitor_points": instrumentation.get("monitor_points", []),
        "instrumentation_modes": instrumentation.get("modes", []),
        "targeted_replay_strategy": replay.get("strategy"),
        "targeted_replay_outputs": replay.get("outputs", []),
        "repair_handoff_required_fields": repair.get("required_fields", []),
        "policy": debug_contract.get("policy", {}),
    }


def compact_verification_artifacts_for_prompt(candidate: dict[str, Any]) -> dict[str, Any]:
    contract = candidate.get("verification_artifact_contract", {}) if isinstance(candidate.get("verification_artifact_contract"), dict) else {}
    hierarchy = candidate.get("hierarchical_verification", {}) if isinstance(candidate.get("hierarchical_verification"), dict) else {}
    upstream = candidate.get("upstream_evidence", {}) if isinstance(candidate.get("upstream_evidence"), dict) else {}
    stage3 = upstream.get("stage3_pipeline_plan", {}) if isinstance(upstream.get("stage3_pipeline_plan"), dict) else {}
    stage4 = upstream.get("stage4_parameter_binding", {}) if isinstance(upstream.get("stage4_parameter_binding"), dict) else {}
    stage5 = upstream.get("stage5_code_generation", {}) if isinstance(upstream.get("stage5_code_generation"), dict) else {}

    def checker_row(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "checker": row.get("checker"),
            "status": row.get("status"),
            "summary": compact_prompt_value(row.get("summary"), max_dict_depth=2, max_list_depth=1, max_items=6, max_str_len=120),
            "errors": row.get("errors", []),
            "evidence_phase": row.get("evidence_phase"),
            "execution_status": row.get("execution_status"),
        }

    def binding_row(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "stage_id": row.get("stage_id"),
            "op": row.get("op"),
            "template_id": row.get("template_id"),
            "params": row.get("params", {}),
            "status": row.get("status"),
            "legality_errors": row.get("legality_errors", []),
        }

    def tool_row(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "name": row.get("name"),
            "role": row.get("role"),
            "kind": row.get("kind"),
            "scope": row.get("scope"),
            "required": row.get("required"),
            "configured": row.get("configured"),
            "produces_count": len(row.get("produces", [])),
            "consumes_count": len(row.get("consumes", [])),
            "planned_produces_count": len(row.get("planned_produces", [])),
            "planned_consumes_count": len(row.get("planned_consumes", [])),
            "evidence_status": row.get("evidence_status"),
        }

    def compact_dag(dag: dict[str, Any]) -> dict[str, Any]:
        nodes = [row for row in dag.get("nodes", []) if isinstance(row, dict)]
        leaf_nodes = [row for row in nodes if str(row.get("name") or "").startswith("leaf_stage.")]
        critical_nodes = [row for row in nodes if not str(row.get("name") or "").startswith("leaf_stage.")]
        return {
            "policy": compact_prompt_value(dag.get("policy", {}), depth=0, max_dict_depth=2, max_list_depth=1, max_items=16, max_str_len=120),
            "node_count": len(nodes),
            "leaf_node_count": len(leaf_nodes),
            "phase_order": dag.get("policy", {}).get("hierarchical_order", []) if isinstance(dag.get("policy"), dict) else [],
            "critical_nodes": [
                {
                    "name": row.get("name"),
                    "phase": row.get("phase"),
                    "depends_on": row.get("depends_on", [])[:8],
                    "required_maturity": row.get("required_maturity"),
                }
                for row in critical_nodes[:32]
            ],
        }

    return {
        "schema_version": candidate.get("schema_version"),
        "stage": candidate.get("stage"),
        "status": candidate.get("status"),
        "checker_summary": candidate.get("checker_summary", {}),
        "system_test_policy": candidate.get("system_test_policy"),
        "board_test_policy": candidate.get("board_test_policy"),
        "stage_gate_policy": candidate.get("stage_gate_policy", {}),
        "checker_plan": [
            {
                "checker": row.get("checker"),
                "constraints": row.get("constraints", []),
            }
            for row in candidate.get("checker_plan", [])
        ],
        "checker_results": [checker_row(row) for row in candidate.get("checker_results", [])],
        "verification_artifact_contract": {
            "schema_version": contract.get("schema_version"),
            "status": contract.get("status"),
            "summary": contract.get("summary"),
            "errors": [compact_prompt_text(str(value), 240) for value in contract.get("errors", [])[:16]],
            "warnings": [compact_prompt_text(str(value), 240) for value in contract.get("warnings", [])[:12]],
            "policy": contract.get("policy", {}),
            "required_evidence_gate_names": [
                str(gate.get("name"))
                for gate in contract.get("required_evidence_gates", [])
                if isinstance(gate, dict) and gate.get("name")
            ],
            "required_tool_protocols": [tool_row(row) for row in contract.get("required_tool_protocols", [])],
            "functional_sim_candidates": [
                {
                    "name": row.get("name"),
                    "scope": row.get("scope"),
                    "kind": row.get("kind"),
                    "acceptance_role": row.get("acceptance_role"),
                    "candidate_label_is_not_acceptance": row.get("candidate_label_is_not_acceptance"),
                }
                for row in contract.get("functional_sim_candidates", [])
                if isinstance(row, dict)
            ],
            "required_generated_artifacts": contract.get("required_generated_artifacts", []),
            "evidence_path_requirements_summary": {
                "count": len(contract.get("evidence_path_requirements", [])) if isinstance(contract.get("evidence_path_requirements"), list) else 0,
                "gate_names": [
                    str(row.get("gate"))
                    for row in contract.get("evidence_path_requirements", [])[:64]
                    if isinstance(row, dict) and row.get("gate")
                ],
                "phases": sorted({
                    str(row.get("phase"))
                    for row in contract.get("evidence_path_requirements", [])
                    if isinstance(row, dict) and row.get("phase")
                }),
            },
            "verification_gate_dag": compact_dag(contract.get("verification_gate_dag", {}) if isinstance(contract.get("verification_gate_dag"), dict) else {}),
            "debug_closure_contract": compact_debug_closure_for_prompt(contract),
        },
        "hierarchical_verification": {
            "strategy": hierarchy.get("strategy"),
            "policy": hierarchy.get("policy", {}),
            "maturity_contract": compact_prompt_value(
                hierarchy.get("maturity_contract", {}),
                depth=0,
                max_dict_depth=3,
                max_list_depth=2,
                max_items=24,
                max_str_len=180,
            ),
            "stage_agents": [
                {
                    "id": row.get("id"),
                    "stage_id": row.get("stage_id"),
                    "op": row.get("op"),
                    "kind": row.get("kind"),
                    "module_checks": row.get("module_checks", []),
                    "required_evidence": row.get("required_evidence", []),
                }
                for row in hierarchy.get("stage_agents", [])
            ],
            "merge_agents": [
                {
                    "id": row.get("id"),
                    "role": row.get("role"),
                    "depends_on": row.get("depends_on", []),
                    "required_evidence": row.get("required_evidence", []),
                }
                for row in hierarchy.get("merge_agents", [])
            ],
            "evidence_gates": [
                {
                    "name": row.get("name"),
                    "required": row.get("required"),
                    "description": compact_prompt_text(str(row.get("description") or ""), 160),
                }
                for row in hierarchy.get("evidence_gates", [])
                if isinstance(row, dict)
            ],
        },
        "parameter_bindings": [binding_row(row) for row in candidate.get("parameter_bindings", [])[:24]],
        "template_source_checks": [checker_row(row) for row in candidate.get("template_source_checks", [])],
        "attention_semantics": compact_prompt_value(candidate.get("attention_semantics", {}), depth=0, max_dict_depth=2, max_list_depth=1, max_items=12, max_str_len=180),
        "upstream_evidence": {
            "stage3_pipeline_plan": {
                "stage": stage3.get("stage"),
                "status": stage3.get("status"),
                "checker_summary": stage3.get("checker_summary", {}),
                "stage_count": stage3.get("stage_count"),
                "data_edge_count": stage3.get("data_edge_count"),
                "stream_edge_count": stage3.get("stream_edge_count"),
                "attention_semantics": stage3.get("attention_semantics", {}),
            },
            "stage4_parameter_binding": {
                "stage": stage4.get("stage"),
                "status": stage4.get("status"),
                "checker_summary": stage4.get("checker_summary", {}),
                "global_params": stage4.get("global_params", {}),
                "numeric_binding_plan": stage4.get("numeric_binding_plan", {}),
            },
            "stage5_code_generation": {
                "stage": stage5.get("stage"),
                "status": stage5.get("status"),
                "target_model_artifact_status": stage5.get("target_model_artifact_status", {}),
                "generated_package_root": stage5.get("generated_package_root"),
                "generated_files_count": stage5.get("generated_files_count"),
                "compile_gate": stage5.get("compile_gate", {}),
                "contract_check": stage5.get("contract_check", {}),
                "package_static_check": stage5.get("package_static_check", {}),
            },
        },
        "constraints_touched": candidate.get("constraints_touched", []),
    }


def compact_candidate_artifact_for_prompt(candidate: dict[str, Any]) -> dict[str, Any]:
    if candidate.get("stage") == "template_selection":
        return compact_template_selection_for_prompt(candidate)
    if candidate.get("stage") == "pipeline_planning":
        return compact_pipeline_plan_for_prompt(candidate)
    if candidate.get("stage") == "parameter_binding":
        return compact_parameter_binding_for_prompt(candidate)
    if candidate.get("stage") == "code_generation":
        return compact_code_generation_manifest_for_prompt(candidate)
    if candidate.get("stage") == "verification_artifacts":
        return compact_verification_artifacts_for_prompt(candidate)
    if candidate.get("stage") == "backend_board":
        return compact_backend_board_for_prompt(candidate)
    return compact_prompt_value(candidate, depth=0, max_dict_depth=2, max_list_depth=2, max_items=5, max_str_len=140)


def compact_backend_board_for_prompt(candidate: dict[str, Any]) -> dict[str, Any]:
    packet = candidate.get("llm_decision_packet", {}) if isinstance(candidate.get("llm_decision_packet"), dict) else {}
    real = candidate.get("real_tool_status", {}) if isinstance(candidate.get("real_tool_status"), dict) else {}
    package = candidate.get("backend_package", {}) if isinstance(candidate.get("backend_package"), dict) else {}
    selected = packet.get("selected_real_tools") if isinstance(packet.get("selected_real_tools"), list) else real.get("backend_selected", [])
    compact_selected = []
    for item in selected[:8] if isinstance(selected, list) else []:
        if not isinstance(item, dict):
            continue
        digest = item.get("tool_report_digest", {}) if isinstance(item.get("tool_report_digest"), dict) else {}
        compact_selected.append(
            {
                "checker": item.get("checker"),
                "status": item.get("status"),
                "summary": compact_prompt_text(str(item.get("summary") or ""), 220),
                "tool_report_status": item.get("tool_report_status"),
                "tool_report_summary": item.get("tool_report_summary"),
                "tool_report_blockers": [
                    compact_prompt_text(str(value), 260)
                    for value in item.get("tool_report_blockers", [])[:6]
                ]
                if isinstance(item.get("tool_report_blockers"), list)
                else [],
                "tool_report_digest": {
                    "status": digest.get("status"),
                    "summary": digest.get("summary"),
                    "blockers": [
                        compact_prompt_text(str(value), 260)
                        for value in digest.get("blockers", [])[:6]
                    ]
                    if isinstance(digest.get("blockers"), list)
                    else [],
                    "candidate_discovery": digest.get("candidate_discovery", {}),
                    "target_discovery_policy": digest.get("target_discovery_policy", {}),
                    "target_selection_decision": digest.get("target_selection_decision", {}),
                    "decision": digest.get("decision", {}),
                    "recovery_status": digest.get("recovery_status"),
                    "selection_reason": digest.get("selection_reason"),
                    "selected_target": digest.get("selected_target"),
                    "target_candidates": digest.get("target_candidates", [])[:8]
                    if isinstance(digest.get("target_candidates"), list)
                    else [],
                    "bounded_recovery_actions": digest.get("bounded_recovery_actions", [])[:6]
                    if isinstance(digest.get("bounded_recovery_actions"), list)
                    else [],
                    "checks": digest.get("checks", [])[:12] if isinstance(digest.get("checks"), list) else [],
                },
            }
        )
    return {
        "stage": candidate.get("stage"),
        "status": candidate.get("status"),
        "execution_scope": candidate.get("execution_scope"),
        "final_design_pass": candidate.get("final_design_pass"),
        "final_design_pass_blockers": [
            compact_prompt_text(str(value), 260)
            for value in candidate.get("final_design_pass_blockers", [])[:12]
        ],
        "missing_final_tools": packet.get("missing_final_tools", real.get("missing_final_tools", []))[:12]
        if isinstance(packet.get("missing_final_tools", real.get("missing_final_tools", [])), list)
        else [],
        "backend_selected_tool_blockers": [
            compact_prompt_text(str(value), 280)
            for value in packet.get("backend_selected_tool_blockers", real.get("backend_selected_tool_blockers", []))[:8]
        ]
        if isinstance(packet.get("backend_selected_tool_blockers", real.get("backend_selected_tool_blockers", [])), list)
        else [],
        "selected_real_tools": compact_selected,
        "contracts": packet.get("contracts", {}),
        "backend_package": {
            "root": package.get("root"),
            "board_shell_wrapper_rtl": package.get("board_shell_wrapper_rtl"),
            "board_shell_contract": package.get("board_shell_contract"),
            "app_shell_integration_contract": package.get("app_shell_integration_contract"),
        },
        "bounded_recovery_actions": candidate.get("bounded_recovery_actions", {}),
        "paper_alignment": packet.get("paper_alignment")
        or "SACG-guided, template-constrained, checker-verified backend/board closure.",
    }


def compact_verification_artifacts_for_worker(candidate: dict[str, Any], subtask: dict[str, Any]) -> dict[str, Any]:
    base = compact_verification_artifacts_for_prompt(candidate)
    full_contract = candidate.get("verification_artifact_contract", {}) if isinstance(candidate.get("verification_artifact_contract"), dict) else {}
    full_hierarchy = candidate.get("hierarchical_verification", {}) if isinstance(candidate.get("hierarchical_verification"), dict) else {}
    focus_values = [str(value) for value in subtask.get("artifact_focus", [])]
    focus_text = " ".join(
        [
            str(subtask.get("role") or ""),
            str(subtask.get("title") or ""),
            str(subtask.get("objective") or ""),
            *[str(value) for value in subtask.get("constraints", [])],
            *focus_values,
            *[str(value) for value in subtask.get("acceptance_checkers", [])],
        ]
    ).lower()
    wanted_checkers = {str(value) for value in subtask.get("acceptance_checkers", [])}
    wanted_checkers.update(
        value
        for value in [
            "verification_plan_static_check",
            "verification_artifact_contract_check",
            "required_real_tool_evidence_check",
            "human_boundary_check",
        ]
        if value in focus_text
    )

    def relevant_checker(row: dict[str, Any]) -> bool:
        checker = str(row.get("checker") or "")
        if checker in wanted_checkers:
            return True
        row_text = " ".join([checker, *[str(value) for value in row.get("constraints", [])]]).lower()
        return any(term in row_text for term in focus_text.split() if term.startswith("constraint."))

    def limit_rows(rows: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
        selected = [row for row in rows if relevant_checker(row)]
        if not selected:
            selected = rows[: min(limit, len(rows))]
        return selected[:limit]

    hierarchy = base.get("hierarchical_verification", {}) if isinstance(base.get("hierarchical_verification"), dict) else {}
    stage_id = None
    merge_id = None
    gates: set[str] = set()
    for value in focus_values:
        if value.startswith("stage_id:"):
            stage_id = value.split(":", 1)[1]
        if value.startswith("merge_id:"):
            merge_id = value.split(":", 1)[1]
        if value.startswith("gate:") or value.startswith("evidence:"):
            gates.add(value.split(":", 1)[1])

    stage_agents = hierarchy.get("stage_agents", [])
    merge_agents = hierarchy.get("merge_agents", [])
    if stage_id:
        stage_agents = [row for row in stage_agents if row.get("stage_id") == stage_id]
    else:
        stage_agents = stage_agents[:3]
    if merge_id:
        merge_agents = [row for row in merge_agents if row.get("id") == merge_id]
    elif gates:
        merge_agents = [
            row
            for row in merge_agents
            if gates & {str(value) for value in row.get("required_evidence", [])}
        ][:3]
    else:
        merge_agents = merge_agents[:3]

    contract = base.get("verification_artifact_contract", {}) if isinstance(base.get("verification_artifact_contract"), dict) else {}
    tools = contract.get("required_tool_protocols", [])
    paths = contract.get("evidence_path_requirements", [])
    if gates:
        paths = [row for row in paths if str(row.get("gate")) in gates or str(row.get("gate")).replace("case_", "") in gates]
        tools = [
            row for row in tools
            if str(row.get("name")) in gates
            or any(str(gate) in " ".join(row.get("planned_produces", []) + row.get("planned_consumes", [])) for gate in gates)
        ] or tools[:4]
    elif any(term in focus_text for term in ["runtime", "memory", "axi", "ddr", "board", "backend", "vivado", "functional"]):
        tools = tools[:6]
        paths = paths[:4]
    else:
        tools = []
        paths = paths[:2]

    def compact_path_list(values: list[Any], limit: int = 5) -> list[str]:
        return [compact_prompt_text(str(value), 120) for value in values[:limit]]

    def compact_tool(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "name": row.get("name"),
            "kind": row.get("kind"),
            "scope": row.get("scope"),
            "required": row.get("required"),
            "configured": row.get("configured"),
            "evidence_status": row.get("evidence_status"),
            "planned_consumes": compact_path_list(row.get("planned_consumes", []), 4),
            "planned_produces": compact_path_list(row.get("planned_produces", []), 4),
        }

    def compact_path_requirement(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "gate": row.get("gate"),
            "acceptance_role": row.get("acceptance_role"),
            "evidence_status": row.get("evidence_status"),
            "planned_consumes": compact_path_list(row.get("planned_consumes", []), 6),
            "planned_produces": compact_path_list(row.get("planned_produces", []), 4),
        }

    def compact_gate_dag(dag: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(dag, dict):
            return {}
        return {
            "schema_version": dag.get("schema_version"),
            "policy": dag.get("policy", {}),
            "nodes": [
                {
                    "name": row.get("name"),
                    "role": compact_prompt_text(str(row.get("role") or ""), 140),
                    "depends_on": row.get("depends_on", []),
                    "evidence_status": row.get("evidence_status"),
                }
                for row in dag.get("nodes", [])
            ],
        }

    include_bindings = any(term in focus_text for term in ["numeric", "template", "parameter", "codegen"])
    include_upstream = any(term in focus_text for term in ["model", "pipeline", "numeric", "stream", "memory", "runtime", "codegen"])
    all_parameter_bindings = candidate.get("parameter_bindings", []) if isinstance(candidate.get("parameter_bindings"), list) else []
    all_attention_semantics = candidate.get("attention_semantics", {}) if isinstance(candidate.get("attention_semantics"), dict) else {}
    gate_dag = full_contract.get("verification_gate_dag") if isinstance(full_contract.get("verification_gate_dag"), dict) else contract.get("verification_gate_dag", {})
    full_evidence_paths = full_contract.get("evidence_path_requirements", []) if isinstance(full_contract.get("evidence_path_requirements"), list) else []
    full_tool_protocols = full_contract.get("required_tool_protocols", []) if isinstance(full_contract.get("required_tool_protocols"), list) else []
    debug_contract_summary = compact_debug_closure_for_prompt(full_contract)
    return {
        "schema_version": base.get("schema_version"),
        "stage": base.get("stage"),
        "status": base.get("status"),
        "role_slice_policy": {
            "sliced_for_subtask": subtask.get("id"),
            "do_not_infer_missing_from_omitted_details": True,
            "use_presence_summary_before_reporting_current_stage_missing_field_risks": True,
        },
        "presence_summary": {
            "stage_agent_count": len(full_hierarchy.get("stage_agents", [])) if isinstance(full_hierarchy.get("stage_agents"), list) else len(hierarchy.get("stage_agents", [])),
            "stage_agent_ids": [
                str(row.get("stage_id") or row.get("id"))
                for row in (full_hierarchy.get("stage_agents", []) if isinstance(full_hierarchy.get("stage_agents"), list) else hierarchy.get("stage_agents", []))
            ],
            "merge_agent_count": len(full_hierarchy.get("merge_agents", [])) if isinstance(full_hierarchy.get("merge_agents"), list) else len(hierarchy.get("merge_agents", [])),
            "evidence_gate_count": len(full_hierarchy.get("evidence_gates", [])) if isinstance(full_hierarchy.get("evidence_gates"), list) else len(hierarchy.get("evidence_gates", [])),
            "evidence_path_requirement_count": len(full_evidence_paths),
            "required_tool_protocol_count": len(full_tool_protocols),
            "verification_gate_dag_node_count": len(gate_dag.get("nodes", [])) if isinstance(gate_dag, dict) else 0,
            "parameter_binding_count": len(all_parameter_bindings),
            "parameter_binding_stage_ids": [str(row.get("stage_id")) for row in all_parameter_bindings if isinstance(row, dict) and row.get("stage_id")],
            "attention_semantics_present": bool(all_attention_semantics),
            "debug_boundary_contract_count": debug_contract_summary.get("boundary_count"),
            "debug_trace_schema_present": bool(debug_contract_summary.get("trace_required_fields")),
        },
        "checker_summary": base.get("checker_summary", {}),
        "stage_gate_policy": base.get("stage_gate_policy", {}),
        "checker_plan": limit_rows(base.get("checker_plan", []), 8),
        "checker_results": limit_rows(base.get("checker_results", []), 8),
        "verification_artifact_contract": {
            "schema_version": contract.get("schema_version"),
            "status": contract.get("status"),
            "summary": contract.get("summary"),
            "errors": contract.get("errors", []),
            "policy": contract.get("policy", {}),
            "required_evidence_gates": [
                gate for gate in contract.get("required_evidence_gates", [])
                if not gates or str(gate.get("name")) in gates
            ][:8],
            "required_tool_protocols": [compact_tool(row) for row in tools],
            "functional_sim_candidates": contract.get("functional_sim_candidates", [])[:3],
            "evidence_path_requirements": [compact_path_requirement(row) for row in paths],
            "verification_gate_dag": compact_gate_dag(gate_dag),
            "debug_closure_contract": debug_contract_summary,
        },
        "hierarchical_verification": {
            "strategy": hierarchy.get("strategy"),
            "policy": hierarchy.get("policy", {}),
            "stage_agents": stage_agents,
            "merge_agents": merge_agents,
            "evidence_gates": [
                gate for gate in hierarchy.get("evidence_gates", [])
                if not gates or str(gate.get("name")) in gates
            ][:8],
        },
        "parameter_bindings": base.get("parameter_bindings", [])[:8] if include_bindings else {"omitted_in_role_slice": True, "count": len(all_parameter_bindings)},
        "attention_semantics": base.get("attention_semantics", {}) if "attention" in focus_text or "model" in focus_text else {"omitted_in_role_slice": True, "present": bool(all_attention_semantics)},
        "upstream_evidence": base.get("upstream_evidence", {}) if include_upstream else {},
        "constraints_touched": base.get("constraints_touched", []),
        "constraints_referenced": candidate.get("constraints_referenced", []),
    }


def compact_candidate_artifact_for_worker(candidate: dict[str, Any], subtask: dict[str, Any]) -> dict[str, Any]:
    if candidate.get("stage") == "verification_artifacts":
        return compact_verification_artifacts_for_worker(candidate, subtask)
    return compact_candidate_artifact_for_prompt(candidate)


def compact_subtask_for_worker(subtask: dict[str, Any]) -> dict[str, Any]:
    rule = subtask.get("handoff_rule", {})
    if not isinstance(rule, dict):
        rule = {}
    return {
        "id": subtask.get("id"),
        "agent": subtask.get("agent"),
        "role": subtask.get("role"),
        "role_profile": subtask.get("role_profile", {}),
        "role_assignment": subtask.get("role_assignment", {}),
        "title": subtask.get("title"),
        "objective": compact_prompt_text(str(subtask.get("objective") or ""), 220),
        "constraints": [str(value) for value in subtask.get("constraints", [])],
        "artifact_focus": [str(value) for value in subtask.get("artifact_focus", [])],
        "action_type": subtask.get("action_type"),
        "expected_artifacts": [str(value) for value in subtask.get("expected_artifacts", [])[:6]],
        "acceptance_checkers": [str(value) for value in subtask.get("acceptance_checkers", [])[:8]],
        "handoff_to": [str(value) for value in subtask.get("handoff_to", [])[:5]],
        "handoff_rule": {
            "produces": [str(value) for value in rule.get("produces", [])[:6]],
            "evidence_rule": compact_prompt_text(str(rule.get("evidence_rule") or ""), 220),
            "completion_criteria": [
                compact_prompt_text(str(value), 160)
                for value in rule.get("completion_criteria", [])[:3]
            ],
        },
    }


def compact_team_context_for_worker(plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "stage": plan["stage"],
        "objective": compact_prompt_text(str(plan["objective"]), 260),
        "paper_alignment": plan["paper_alignment"],
        "collaboration_contract": plan.get("collaboration_contract", {}),
        "team_rules": [compact_prompt_text(str(rule), 140) for rule in plan["team_rules"]],
    }


def has_kind(items: list[dict[str, Any]], *kinds: str) -> bool:
    kind_set = set(kinds)
    return any(str(item.get("kind")) in kind_set for item in items)


def role_profile(role: str) -> dict[str, Any]:
    role_text = role.lower()
    for item in ROLE_CATALOG:
        if any(keyword in role_text for keyword in item["keywords"]):
            return {
                "family": item["family"],
                "capabilities": list(item["capabilities"]),
                "constraint_focus": list(item["constraint_focus"]),
            }
    return {
        "family": "stage_specialist",
        "capabilities": ["audit stage-local artifact", "map observations to SACG constraints"],
        "constraint_focus": [],
    }


def default_parallel_group(role: str) -> int:
    role_text = role.lower()
    serial_keywords = ["auditor", "gate", "liaison", "taxonomy", "boundary"]
    return 1 if any(keyword in role_text for keyword in serial_keywords) else 0


def action_type_for(role: str, artifact_focus: list[str]) -> str:
    text = " ".join([role] + artifact_focus).lower()
    if any(keyword in text for keyword in ["synthesis", "implementation", "timing", "board", "backend"]):
        return "implementation_evidence_review"
    if any(keyword in text for keyword in ["verification", "checker", "test", "failure", "repair"]):
        return "evidence_and_repair_review"
    if any(keyword in text for keyword in ["chisel", "top", "codegen", "wrapper", "runtime", "memory_layout"]):
        return "template_bound_artifact_review"
    if any(keyword in text for keyword in ["data order", "transfer", "stream", "beat", "dataflow", "memory"]):
        return "cross_layer_rule_review"
    return "sacg_constraint_review"


def acceptance_checkers_for(constraints: list[str], artifact_focus: list[str]) -> list[str]:
    text = " ".join(constraints + artifact_focus).lower()
    checkers = ["sacg_static_check"]
    if any(keyword in text for keyword in ["shape", "model", "template", "parameter"]):
        checkers.append("template_binding_static_check")
    if any(keyword in text for keyword in ["data order", "transfer", "stream", "beat", "liveness", "fifo"]):
        checkers.extend(["data_order_trace_check", "transfer_count_check", "deadlock_watchdog"])
    if any(keyword in text for keyword in ["memory", "runtime", "ddr", "axi"]):
        checkers.append("addr_map_check")
    if any(keyword in text for keyword in ["numeric", "scale", "quant"]):
        checkers.append("numeric_compare")
    if any(keyword in text for keyword in ["codegen", "chisel", "top_wrapper"]):
        checkers.append("codegen_package_static_check")
    if any(keyword in text for keyword in ["backend", "synthesis", "implementation", "timing", "board", "deployment"]):
        checkers.extend(["implementation_package_static", "real_tool_evidence_check"])
    if any(keyword in text for keyword in ["human", "approval", "boundary", "repair"]):
        checkers.append("repair_boundary_check")
    return sorted(set(checkers))


def handoff_rule_for(
    stage: str,
    role: str,
    constraints: list[str],
    artifact_focus: list[str],
) -> dict[str, Any]:
    return {
        "schema_version": "spatialaccagent.team_handoff_rule.v0",
        "stage": stage,
        "role": role,
        "consumes": {
            "sacg_constraints": constraints,
            "candidate_artifact_fields": artifact_focus,
        },
        "produces": [
            "sacg_focus",
            "observations",
            "risks",
            "proposed_actions",
            "approval_required_for",
        ],
        "acceptance_checkers": acceptance_checkers_for(constraints, artifact_focus),
        "handoff_to": ["team_aggregate", "stage_report", "sacg_validate"],
        "evidence_rule": "Do not claim pass unless evidence is bound to SACG constraints or explicitly recorded as not_run.",
    }


def role_assignment_for(
    stage: str,
    role: str,
    title: str,
    objective: str,
    constraints: list[str],
    artifact_focus: list[str],
    handoff_rule: dict[str, Any],
    profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    profile = profile or role_profile(role)
    return {
        "schema_version": "spatialaccagent.team_role_assignment.v0",
        "team_model": "chip_design_team",
        "stage": stage,
        "role": role,
        "title": title,
        "mission": objective,
        "professional_family": profile.get("family", "stage_specialist"),
        "primary_responsibilities": [
            *[str(value) for value in profile.get("capabilities", [])],
            "own only the constraints and artifact fields assigned to this subtask",
            "turn observations into bounded executable actions with named acceptance checkers",
        ],
        "decision_authority": [
            "classify current-stage risks inside the assigned responsibility boundary",
            "propose bounded repairs or handoff actions for downstream agents/tools",
            "request approval when a proposal changes architecture, numeric policy, memory layout, runtime ABI, templates, or board integration",
        ],
        "collaboration_interfaces": {
            "consumes": {
                "constraints": constraints,
                "artifact_focus": artifact_focus,
            },
            "produces": handoff_rule.get("produces", []),
            "handoff_to": handoff_rule.get("handoff_to", []),
            "acceptance_checkers": handoff_rule.get("acceptance_checkers", []),
        },
        "out_of_scope": [
            "do not replace another specialist's decision without an explicit handoff action",
            "do not claim hardware correctness without real checker/tool evidence",
            "do not change model semantics, numeric policy, template library, memory layout, runtime ABI, or board target outside approved boundaries",
        ],
    }


def make_subtask(
    stage: str,
    role: str,
    title: str,
    objective: str,
    constraints: list[str],
    artifact_focus: list[str],
    parallel_group: int | None = None,
) -> dict[str, Any]:
    role_id = safe_id(role)
    profile = role_profile(role)
    group = default_parallel_group(role) if parallel_group is None else parallel_group
    handoff_rule = handoff_rule_for(stage, role, constraints, artifact_focus)
    role_assignment = role_assignment_for(stage, role, title, objective, constraints, artifact_focus, handoff_rule, profile)
    return {
        "id": f"{stage}.{role_id}",
        "agent": f"{stage}_{role_id}_agent",
        "role": role,
        "role_profile": profile,
        "role_assignment": role_assignment,
        "title": title,
        "objective": objective,
        "constraints": constraints,
        "artifact_focus": artifact_focus,
        "parallel_group": group,
        "handoff_required": True,
        "action_type": action_type_for(role, artifact_focus),
        "expected_artifacts": artifact_focus,
        "acceptance_checkers": handoff_rule["acceptance_checkers"],
        "handoff_to": handoff_rule["handoff_to"],
        "handoff_rule": handoff_rule,
    }


def attach_required_evidence(
    subtask: dict[str, Any],
    required_evidence: list[str],
    hierarchy_metadata: dict[str, Any],
) -> dict[str, Any]:
    rule = dict(subtask.get("handoff_rule", {}))
    rule["required_evidence"] = required_evidence
    rule["hierarchy_metadata"] = hierarchy_metadata
    subtask["handoff_rule"] = rule
    subtask["expected_artifacts"] = sorted(set(subtask.get("expected_artifacts", []) + required_evidence))
    subtask["acceptance_checkers"] = sorted(
        set(subtask.get("acceptance_checkers", []) + required_evidence + ["hierarchical_verification_plan_check"])
    )
    return subtask


def input_preparation_subtasks(stage: str, candidate: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        make_subtask(
            stage,
            "model intake engineer",
            "Validate model-facing inputs",
            "Check whether model_config and task_card expose enough decoder-block, shape, attention, and sequence facts for SACG extraction.",
            ["constraint.model.decoder", "constraint.shape.model", "constraint.task.goal"],
            ["model_config", "task_card"],
        ),
        make_subtask(
            stage,
            "platform numeric engineer",
            "Validate numeric and board inputs",
            "Check whether numeric_policy and target_board_profile expose enough numeric, DDR/AXI, runtime, and deployment facts without inventing missing board details.",
            [
                "constraint.numeric.policy",
                "constraint.memory.board",
                "constraint.runtime.board",
                "constraint.deployment.board",
            ],
            ["numeric_policy", "target_board_profile"],
        ),
        make_subtask(
            stage,
            "input evidence engineer",
            "Validate current-run materials and evidence",
            "Check whether material_index, sample_project_index, field_evidence, tool_profile, and tool_availability capture the user-provided board, quantization, sample-project, and EDA-tool materials for this run.",
            [
                "constraint.source.materials",
                "constraint.source.evidence",
                "constraint.tool.profile",
                "constraint.cross_layer.input_consistency",
            ],
            ["material_index", "sample_project_index", "field_evidence", "tool_profile", "tool_availability"],
        ),
        make_subtask(
            stage,
            "toolchain boundary engineer",
            "Validate tool and human-boundary inputs",
            "Check whether tool_protocols, template_library, design_space, and human_agent_boundary define a checker-verified template-constrained run.",
            ["constraint.template.library", "constraint.tool.protocols", "constraint.human.boundary"],
            ["template_library", "design_space", "tool_protocols", "human_agent_boundary"],
        ),
    ]


def constraint_extraction_subtasks(stage: str, candidate: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        make_subtask(
            stage,
            "model graph engineer",
            "Review model and shape constraints",
            "Check that model operators, residual order, attention facts, head mapping, hidden sizes, and sequence facts are explicit design-graph nodes and constraints.",
            ["constraint.model.decoder", "constraint.shape.model"],
            ["candidate_design_graph_summary", "model_operator_nodes"],
        ),
        make_subtask(
            stage,
            "input evidence engineer",
            "Review current-run materials and evidence",
            "Check that user-provided board materials, quantization materials, sample projects, extracted field evidence, tool profiles, and real tool probe results are represented in the initial design graph.",
            [
                "constraint.source.materials",
                "constraint.source.evidence",
                "constraint.tool.profile",
                "constraint.cross_layer.input_consistency",
            ],
            ["candidate_design_graph_summary", "input_artifacts"],
        ),
        make_subtask(
            stage,
            "template platform engineer",
            "Review template/platform constraints",
            "Check that template library, design space, board, memory, runtime, and tool protocols are represented as design-graph constraints.",
            [
                "constraint.template.library",
                "constraint.arch.design_space",
                "constraint.memory.board",
                "constraint.runtime.board",
                "constraint.tool.profile",
                "constraint.tool.protocols",
            ],
            ["candidate_design_graph_summary", "input_artifacts"],
        ),
        make_subtask(
            stage,
            "constraint graph auditor",
            "Review design graph reference integrity",
            "Check whether the initial design graph can act as shared design state for later agent subtasks and checker evidence.",
            ["constraint.human.boundary", "constraint.cross_layer.input_consistency"],
            ["candidate_design_graph_summary", "validation_errors"],
        ),
    ]


def template_selection_subtasks(stage: str, candidate: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        make_subtask(
            stage,
            "operator coverage engineer",
            "Review operator-template coverage",
            "Check every decoder operator maps to a trusted template and missing coverage is explicit rather than hidden; verify the coverage matrix is backed by checker results, not only a count.",
            ["constraint.model.decoder", "constraint.shape.model", "constraint.template.library"],
            ["selected_templates", "missing_ops", "coverage", "checker_results"],
        ),
        make_subtask(
            stage,
            "template binding engineer",
            "Review strict template bindings",
            "Check concrete parameter bindings, source file hashes, constructor/interface matches, unsupported bindings, required adapters, and forbidden edits.",
            ["constraint.shape.model", "constraint.numeric.policy", "constraint.template.library", "constraint.arch.design_space"],
            ["parameter_bindings", "template_source_checks", "supported_bindings", "unsupported_bindings", "required_adapters", "forbidden_edits"],
        ),
        make_subtask(
            stage,
            "attention semantic engineer",
            "Review attention semantic expansion",
            "Check Q/K/V projection, RoPE, GQA head mapping, softmax, output projection, KV-cache scope, and causal mask binding before the stage can pass.",
            [
                "constraint.model.decoder",
                "constraint.shape.model",
                "constraint.numeric.policy",
                "constraint.cross_layer.input_consistency",
            ],
            ["attention_semantics", "parameter_bindings", "checker_results"],
        ),
        make_subtask(
            stage,
            "cross layer gate engineer",
            "Review cross-layer template gate",
            "Check numeric, board memory, runtime, deployment, and input-consistency constraints are in the template-binding trace and that unresolved risks block the stage.",
            [
                "constraint.numeric.policy",
                "constraint.memory.board",
                "constraint.runtime.board",
                "constraint.deployment.board",
                "constraint.cross_layer.input_consistency",
            ],
            ["cross_layer_trace", "checker_results", "template_source_checks"],
        ),
    ]


def pipeline_planning_subtasks(stage: str, candidate: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        make_subtask(
            stage,
            "pipeline architect",
            "Review stage decomposition",
            "Check whether pipeline stages preserve decoder operator order and expose residual, attention, and template boundaries.",
            ["constraint.pipeline.structure", "constraint.model.decoder", "constraint.template.library"],
            ["stages"],
        ),
        make_subtask(
            stage,
            "data transfer engineer",
            "Review data order and transfer-unit constraints",
            "Check token/tile/lane/transfer-unit order, valid/ready assumptions, and producer-consumer handoff risks.",
            ["constraint.stream.order", "constraint.beat.pipeline", "constraint.liveness.pipeline"],
            ["data_order_edges", "memory_policy"],
        ),
        make_subtask(
            stage,
            "memory dataflow engineer",
            "Review memory/runtime dataflow implications",
            "Check that pipeline planning leaves explicit hooks for weights, activations, DDR layout, runtime config, and later implementation evidence.",
            ["constraint.memory.board", "constraint.runtime.board"],
            ["memory_policy", "stages"],
        ),
    ]


def parameter_binding_subtasks(stage: str, candidate: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        make_subtask(
            stage,
            "template parameter engineer",
            "Review template parameter binding",
            "Check that every selected stage receives required shape, attention, lane, tile, FIFO, and clock parameters.",
            ["constraint.parameter.binding", "constraint.shape.model", "constraint.template.library"],
            ["bindings", "global_params"],
        ),
        make_subtask(
            stage,
            "dse resource engineer",
            "Review design-space risks",
            "Check whether first-point DSE choices have explicit resource/timing risks and do not silently change model or numeric semantics.",
            ["constraint.arch.design_space", "constraint.numeric.policy", "constraint.deployment.board"],
            ["binding_policy", "global_params"],
        ),
    ]


def code_generation_subtasks(stage: str, candidate: dict[str, Any]) -> list[dict[str, Any]]:
    planned = candidate.get("planned_code_outputs", []) + candidate.get("generated_code_outputs", [])
    tasks: list[dict[str, Any]] = []
    if has_kind(planned, "model_ir", "architecture_plan", "chisel", "top_wrapper", "fpga_axi_ddr_top_wrapper"):
        tasks.append(
            make_subtask(
                stage,
                "template codegen engineer",
                "Generate template-bound Chisel package",
                "Check that generated Chisel/top/wrapper code is derived from selected templates, parameter bindings, and SACG constraints rather than free RTL.",
                [
                    "constraint.model.decoder",
                    "constraint.shape.model",
                    "constraint.template.library",
                    "constraint.parameter.binding",
                    "constraint.codegen.package",
                    "constraint.memory.board",
                    "constraint.runtime.board",
                    "constraint.deployment.board",
                ],
                ["generated.chisel_modules", "generated.top_wrapper", "generated.fpga_axi_ddr_top_wrapper"],
            )
        )
    tasks.append(
        make_subtask(
            stage,
            "cross layer consistency auditor",
            "Audit design story alignment",
            "Identify whether code generation is drifting away from the model, shape, numeric, template, and board rules established in earlier stages.",
            [
                "constraint.model.decoder",
                "constraint.stream.order",
                "constraint.memory.board",
                "constraint.runtime.board",
                "constraint.human.boundary",
            ],
            ["artifact.stage5.design_artifact_manifest"],
        )
    )
    return tasks


def verification_artifacts_subtasks(stage: str, candidate: dict[str, Any]) -> list[dict[str, Any]]:
    hierarchy = candidate.get("hierarchical_verification")
    if isinstance(hierarchy, dict) and hierarchy.get("stage_agents"):
        tasks: list[dict[str, Any]] = []
        for agent in hierarchy.get("stage_agents", []):
            required_evidence = [str(value) for value in agent.get("required_evidence", [])]
            module_checks = [str(value) for value in agent.get("module_checks", [])]
            artifact_focus = [
                f"stage_id:{agent.get('stage_id')}",
                f"op:{agent.get('op')}",
                f"kind:{agent.get('kind')}",
                *[f"module:{name}" for name in module_checks],
                *[f"evidence:{name}" for name in required_evidence],
            ]
            subtask = make_subtask(
                stage,
                f"{agent.get('stage_id')} stage verification engineer",
                f"Validate {agent.get('stage_id')} leaf stage",
                (
                    "Validate one case-adapter pipeline leaf stage before merge: target-model operator semantics, "
                    "complete real-weight DUT binding, generated semantic testbench, resolved numeric comparison "
                    "(provided values or frozen framework loose defaults), "
                    "ready/valid boundary, transfer-unit shape, and required evidence gates. File existence, sampled "
                    "weights, default/identity weights, random expected output, or RTL-derived golden data cannot pass."
                ),
                [
                    "constraint.verification.hierarchy",
                    "constraint.pipeline.structure",
                    "constraint.stream.order",
                    "constraint.beat.pipeline",
                    "constraint.tool.protocols",
                ],
                artifact_focus,
                int(agent.get("parallel_group", 0) or 0),
            )
            tasks.append(
                attach_required_evidence(
                    subtask,
                    required_evidence,
                    {
                        "node_type": "stage_agent",
                        "id": agent.get("id"),
                        "stage_id": agent.get("stage_id"),
                        "input_shape": agent.get("input_shape"),
                        "output_shape": agent.get("output_shape"),
                    },
                )
            )
        for agent in hierarchy.get("merge_agents", []):
            required_evidence = [str(value) for value in agent.get("required_evidence", [])]
            depends_on = [str(value) for value in agent.get("depends_on", [])]
            artifact_focus = [
                f"merge_id:{agent.get('id')}",
                *[f"depends_on:{value}" for value in depends_on],
                *[f"evidence:{name}" for name in required_evidence],
            ]
            constraints = [
                "constraint.verification.hierarchy",
                "constraint.pipeline.structure",
                "constraint.stream.order",
                "constraint.beat.pipeline",
                "constraint.tool.protocols",
            ]
            if any("axi" in value or "ddr" in value or "runtime" in value for value in artifact_focus):
                constraints.extend(["constraint.memory.board", "constraint.runtime.board", "constraint.deployment.board"])
            subtask = make_subtask(
                stage,
                str(agent.get("role") or agent.get("id")),
                f"Validate {agent.get('id')} merge gate",
                (
                    "Validate the assigned chip-design-team merge boundary. Keep the main repair-loop "
                    "hierarchy as operator leaf modules, single transformer-layer kernel, then board AXI/DDR "
                    "wrapped system; multi-layer, AXI/DDR, DDR image, and functional-simulation gates are "
                    "third-layer subchecks rather than separate promotion layers."
                ),
                sorted(set(constraints)),
                artifact_focus,
                int(agent.get("parallel_group", 1) or 1),
            )
            tasks.append(
                attach_required_evidence(
                    subtask,
                    required_evidence,
                    {
                        "node_type": "merge_agent",
                        "id": agent.get("id"),
                        "depends_on": depends_on,
                    },
                )
            )
        tasks.append(
            make_subtask(
                stage,
                "hierarchical evidence gate auditor",
                "Audit required case evidence gates",
                (
                    "Check that the three-layer verification closure requires real weights, operator-leaf "
                    "functional evidence, single transformer-layer functional/golden evidence, and board "
                    "AXI/DDR wrapped-system evidence from multi-layer pipeline, AXI/DDR runtime interface, "
                    "DDR image roundtrip, and remote simulator subgates. Bitstream and board runtime stay "
                    "downstream and cannot replace verification evidence. Every level must bind the same current "
                    "checkpoint and stimulus to target-model inference golden tensors, a resolved immutable numeric "
                    "tolerance, generated testbench hashes, and executed DUT weight-consumption evidence."
                ),
                ["constraint.verification.hierarchy", "constraint.tool.protocols", "constraint.deployment.board"],
                [f"gate:{gate.get('name')}" for gate in hierarchy.get("evidence_gates", [])],
                6,
            )
        )
        debug_task = make_subtask(
            stage,
            "contract guided debug closure engineer",
            "Audit failure localization and targeted replay contracts",
            (
                "Check that downstream system-level failures will be routed through boundary contracts, "
                "failure-slice localization, targeted replay, and causal repair handoff before any symptom-driven patch. "
                "A passed lower layer may be reopened only when the current-layer CCTG/boundary trace explicitly "
                "contradicts it and names the challenged lower-layer gate or module."
            ),
            [
                "constraint.verification.hierarchy",
                "constraint.verification.artifacts",
                "constraint.stream.order",
                "constraint.human.boundary",
                "constraint.tool.protocols",
            ],
            [
                "debug_closure_contract",
                "boundary_contracts",
                "boundary_trace_manifest",
                "failure_localization",
                "targeted_replay",
                "minimal_repair_context",
                "lower_layer_evidence_challenge",
            ],
            6,
        )
        debug_task["acceptance_checkers"] = sorted(
            set(debug_task.get("acceptance_checkers", []))
            | {
                "boundary_contract_check",
                "failure_localization_check",
                "targeted_replay_check",
                "causal_repair_context_check",
            }
        )
        tasks.append(debug_task)
        return tasks

    return [
        make_subtask(
            stage,
            "checker planner",
            "Review checker coverage",
            "Check whether the verification plan covers model, numeric precision, template, data order, transfer-unit, memory/runtime, human-boundary, and tool-protocol constraints.",
            ["constraint.verification.plan"],
            ["checker_plan"],
        ),
        make_subtask(
            stage,
            "test artifact engineer",
            "Review stage/top/system test artifact needs",
            "Check whether planned artifacts include complete target-checkpoint weights, real target-model reference inference, deterministic input provenance, resolved numeric tolerance (provided values or frozen framework loose defaults), semantic testbenches, DUT weight binding, and exact sample-wrapper board simulation evidence at the proper hierarchy level.",
            ["constraint.pipeline.structure", "constraint.codegen.package", "constraint.verification.plan"],
            ["stage_test_targets", "system_test_policy", "board_test_policy"],
        ),
    ]


def verification_subtasks(stage: str, candidate: dict[str, Any]) -> list[dict[str, Any]]:
    tasks = []
    maturity = candidate.get("hierarchical_maturity")
    if isinstance(maturity, dict) and maturity.get("status") != "pass":
        tasks.append(
            make_subtask(
                stage,
                "hierarchical maturity auditor",
                "Audit strict bottom-up verification maturity",
                (
                    "Block backend handoff until the three verification repair-loop layers are closed: "
                    "operator-leaf functional/golden, single transformer-layer functional/golden, and board "
                    "AXI/DDR wrapped-system closure including multi-layer pipeline/deadlock, AXI/DDR protocol, "
                    "DDR image transfer, and real functional simulation subgates. Each pass must prove complete "
                    "real-weight DUT consumption and comparison against target-model inference for the same input "
                    "and checkpoint under a resolved immutable numeric policy."
                ),
                [
                    "constraint.verification.hierarchy",
                    "constraint.tool.protocols",
                    "constraint.stream.order",
                    "constraint.memory.board",
                    "constraint.runtime.board",
                ],
                ["hierarchical_maturity", "hierarchical_gate_summary", "gate_execution_plan"],
                0,
            )
        )
    gate_summary = candidate.get("hierarchical_gate_summary")
    if isinstance(gate_summary, dict) and gate_summary.get("missing_or_failed"):
        missing = gate_summary.get("missing_or_failed", [])
        tasks.append(
            make_subtask(
                stage,
                "required evidence gate auditor",
                "Review failed required case gates",
                (
                    "Classify pending or failed required case evidence gates and prevent final pass claims "
                    f"until they pass. Current blockers: {missing}"
                ),
                [
                    "constraint.verification.hierarchy",
                    "constraint.tool.protocols",
                    "constraint.memory.board",
                    "constraint.runtime.board",
                    "constraint.deployment.board",
                ],
                ["hierarchical_gate_summary", "results"],
                0,
            )
        )
    tasks.extend([
        make_subtask(
            stage,
            "static checker engineer",
            "Review deterministic checker results",
            "Classify failed system checks and tool evidence into violated model, shape, numeric precision, data order, memory, runtime, tool, or human-boundary constraints.",
            ["constraint.verification.plan"],
            ["results"],
        ),
        make_subtask(
            stage,
            "real tool evidence engineer",
            "Review real tool evidence gaps",
            "Classify not-run or failed Verilator/VCS/Vivado/board tools as evidence gaps or true closure blockers. Reject status-only passes and require hashes for target-model reference, semantic testbench, RTL output, complete consumed weights, and exact board sources where applicable.",
            ["constraint.tool.protocols", "constraint.deployment.board"],
            ["results"],
        ),
        make_subtask(
            stage,
            "failure taxonomy engineer",
            "Review cross-layer failure taxonomy",
            "Map ambiguous symptoms to failure classes and avoid symptom-driven repair without violated-constraint evidence.",
            ["constraint.human.boundary", "constraint.verification.plan"],
            ["results"],
        ),
    ])
    return tasks


def repair_subtasks(stage: str, candidate: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        make_subtask(
            stage,
            "root cause engineer",
            "Review failed checks and root-cause candidates",
            "Check whether each repair action is tied to evidence and a violated constraint rather than a raw symptom.",
            ["constraint.verification.plan", "constraint.human.boundary"],
            ["failures", "repair_actions"],
        ),
        make_subtask(
            stage,
            "repair boundary engineer",
            "Review repair permission boundaries",
            "Check whether proposed repair scopes are auto-allowed, approval-required, or forbidden under the human-agent boundary.",
            ["constraint.human.boundary"],
            ["repair_actions"],
        ),
    ]


def backend_board_subtasks(stage: str, candidate: dict[str, Any]) -> list[dict[str, Any]]:
    status = candidate.get("real_tool_status", {})
    failed = status.get("failed", [])
    pending = status.get("pending", [])
    upstream = candidate.get("upstream_hierarchy_gate", {})
    common = [
        "constraint.backend_board.plan",
        "constraint.deployment.board",
        "constraint.tool.protocols",
    ]
    tasks = []
    if isinstance(upstream, dict) and upstream.get("status") != "pass":
        tasks.append(
            make_subtask(
                stage,
                "upstream verification maturity auditor",
                "Block backend tools until Stage7 hierarchy is closed",
                (
                    "Check Stage7 hierarchical_maturity and route recovery back to Stage7/Stage6 when "
                    "operator-leaf, single transformer-layer, board AXI/DDR wrapped-system, or debug-closure "
                    "evidence is missing. Treat multi-layer pipeline, AXI/DDR protocol, DDR image, and real "
                    "functional simulation as third-layer subgate evidence, not separate promotion layers."
                ),
                common + ["constraint.verification.hierarchy"],
                ["upstream_hierarchy_gate", "final_design_pass_blockers"],
                0,
            )
        )
    tasks.extend([
        make_subtask(
            stage,
            "synthesis engineer",
            "Prepare synthesis closure handoff",
            "Check synthesis scripts, top module expectations, generated source package, and missing evidence for Vivado synthesis.",
            common + ["constraint.codegen.package", "constraint.backend.package"],
            ["synthesis", "timing_report", "resource_report"],
        ),
        make_subtask(
            stage,
            "implementation timing engineer",
            "Prepare implementation and timing closure handoff",
            "Check whether implementation scripts preserve pipeline and data-order semantics and whether timing fixes would require human approval.",
            common + ["constraint.stream.order", "constraint.beat.pipeline", "constraint.backend.package"],
            ["implementation", "bitstream_generation"],
        ),
        make_subtask(
            stage,
            "board runtime engineer",
            "Prepare board smoke and runtime handoff",
            "Check runtime launch, DDR/AXI configuration, result collection, and board pass criteria against deployment constraints.",
            common + ["constraint.memory.board", "constraint.runtime.board", "constraint.backend.package"],
            ["board_runtime_smoke", "benchmark_report"],
        ),
        make_subtask(
            stage,
            "evidence gate auditor",
            "Audit final design pass blockers",
            f"Classify implementation blockers. Pending tools: {pending}. Failed tools: {failed}. Do not allow final pass without required evidence.",
            common + ["constraint.verification.plan", "constraint.human.boundary"],
            ["real_tool_status", "final_design_pass_blockers"],
        ),
    ])
    return tasks


def fallback_subtasks(stage: str, candidate: dict[str, Any]) -> list[dict[str, Any]]:
    if stage == "input_preparation":
        return input_preparation_subtasks(stage, candidate)
    if stage == "constraint_extraction":
        return constraint_extraction_subtasks(stage, candidate)
    if stage == "template_selection":
        return template_selection_subtasks(stage, candidate)
    if stage == "pipeline_planning":
        return pipeline_planning_subtasks(stage, candidate)
    if stage == "parameter_binding":
        return parameter_binding_subtasks(stage, candidate)
    if stage == "code_generation":
        return code_generation_subtasks(stage, candidate)
    if stage == "verification_artifacts":
        return verification_artifacts_subtasks(stage, candidate)
    if stage == "verification":
        return verification_subtasks(stage, candidate)
    if stage == "repair":
        return repair_subtasks(stage, candidate)
    if stage == "backend_board":
        return backend_board_subtasks(stage, candidate)
    return [
        make_subtask(
            stage,
            "stage specialist",
            "Review stage-local artifact",
            "Check whether this stage artifact satisfies its declared SACG constraints and has explicit handoff fields for later stages.",
            [],
            list(candidate.keys())[:8],
        ),
        make_subtask(
            stage,
            "verification liaison",
            "Review evidence needs",
            "Identify which checkers or real tools must validate this stage before it can be trusted.",
            ["constraint.verification.plan"],
            list(candidate.keys())[:8],
        ),
        make_subtask(
            stage,
            "consistency auditor",
            "Review cross-layer risk",
            "Identify possible model/shape/numeric/data-order/memory/runtime/implementation consistency drift introduced by this stage.",
            [],
            list(candidate.keys())[:8],
        ),
    ]


def normalize_llm_subtasks(stage: str, subtasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    seen: set[str] = set()
    raw_agents: list[str] = []
    for index, item in enumerate(subtasks):
        role = str(item.get("role") or item.get("agent") or f"subagent_{index}")
        role_id = safe_id(role)
        raw_agents.append(str(item.get("agent") or f"{stage}_{role_id}_agent"))
    duplicate_agents = {agent for agent in raw_agents if raw_agents.count(agent) > 1}
    seen_agents: set[str] = set()
    for index, item in enumerate(subtasks):
        role = str(item.get("role") or item.get("agent") or f"subagent_{index}")
        role_id = safe_id(role)
        item_id = str(item.get("id") or f"{stage}.{role_id}")
        if item_id in seen:
            item_id = f"{item_id}_{index}"
        seen.add(item_id)
        raw_agent = str(item.get("agent") or f"{stage}_{role_id}_agent")
        agent = raw_agent
        if raw_agent in duplicate_agents:
            agent = f"{safe_id(raw_agent)}__{role_id}"
        if agent in seen_agents:
            agent = f"{agent}_{index}"
        seen_agents.add(agent)
        constraints = [str(value) for value in item.get("constraints", [])]
        artifact_focus = [str(value) for value in item.get("artifact_focus", [])]
        default_rule = handoff_rule_for(stage, role, constraints, artifact_focus)
        handoff_rule = item.get("handoff_rule") or item.get("handoff_contract")
        if not isinstance(handoff_rule, dict):
            handoff_rule = default_rule
        else:
            merged_rule = dict(default_rule)
            merged_rule.update(handoff_rule)
            for key in ["consumes", "produces", "acceptance_checkers", "handoff_to", "evidence_rule"]:
                if not merged_rule.get(key):
                    merged_rule[key] = default_rule[key]
            handoff_rule = merged_rule
        acceptance_checkers = item.get("acceptance_checkers")
        if not isinstance(acceptance_checkers, list) or not acceptance_checkers:
            acceptance_checkers = handoff_rule.get("acceptance_checkers", [])
        try:
            parallel_group = int(item.get("parallel_group", default_parallel_group(role)) or 0)
        except (TypeError, ValueError):
            parallel_group = default_parallel_group(role)
        title = str(item.get("title") or role)
        objective = str(item.get("objective") or "Review this stage artifact against SACG constraints.")
        profile = item.get("role_profile") if isinstance(item.get("role_profile"), dict) else role_profile(role)
        role_assignment = item.get("role_assignment") if isinstance(item.get("role_assignment"), dict) else {}
        if not role_assignment:
            role_assignment = role_assignment_for(stage, role, title, objective, constraints, artifact_focus, handoff_rule, profile)
        normalized.append(
            {
                "id": item_id,
                "agent": agent,
                "source_agent": raw_agent if agent != raw_agent else None,
                "role": role,
                "role_profile": profile,
                "role_assignment": role_assignment,
                "title": title,
                "objective": objective,
                "constraints": constraints,
                "artifact_focus": artifact_focus,
                "parallel_group": max(0, parallel_group),
                "handoff_required": bool(item.get("handoff_required", True)),
                "action_type": str(item.get("action_type") or action_type_for(role, artifact_focus)),
                "expected_artifacts": [
                    str(value) for value in item.get("expected_artifacts", artifact_focus)
                ],
                "acceptance_checkers": [str(value) for value in acceptance_checkers],
                "handoff_to": [str(value) for value in item.get("handoff_to", handoff_rule.get("handoff_to", []))],
                "handoff_rule": handoff_rule,
            }
        )
    return normalized


def call_decomposer(prompt: str, out_dir: Path) -> dict[str, Any]:
    llm = resolved_llm_cfg()
    mode = llm.mode
    enforce = llm.enforce
    result_path = out_dir / "team" / "decomposer_result.json"
    result_path.parent.mkdir(parents=True, exist_ok=True)
    current_prompt_hash = prompt_hash(prompt)
    cached = cached_successful_record(result_path, current_prompt_hash)
    if cached is not None:
        print(f"[team:decomposer] reuse cached {result_path}", file=sys.stderr, flush=True)
        return cached
    record: dict[str, Any] = {
        "schema_version": "spatialaccagent.team_decomposer_record.v0",
        "prompt_protocol": PROMPT_PROTOCOL,
        "prompt_hash": current_prompt_hash,
        "mode": mode,
        "stream": llm.stream,
        "transport": "responses_sse_stream" if llm.stream else "responses_json",
        "http_transport": llm.http_transport,
        "used_fallback": False,
        "error": None,
        "output": None,
    }
    if mode.strip().lower() in {"", "off", "none", "disabled"}:
        record["error"] = f"LLM mode is disabled: {mode}"
        write_json(result_path, record)
        if enforce:
            raise TeamDecompositionError(record["error"])
        return record

    if llm.configuration_error:
        record["error"] = llm.configuration_error
        write_json(result_path, record)
        if enforce:
            raise TeamDecompositionError(record["error"])
        return record

    key = llm.api_key
    endpoint = llm.endpoint
    model = llm.model
    if not key or not endpoint:
        record["error"] = "missing LLM endpoint or API key"
        write_json(result_path, record)
        if enforce:
            raise TeamDecompositionError(record["error"])
        return record
    if not model:
        record["error"] = "missing LLM model"
        write_json(result_path, record)
        if enforce:
            raise TeamDecompositionError(record["error"])
        return record

    started = time.monotonic()
    raw_text = ""
    try:
        decomposer_effort = team_decomposer_reasoning_effort(llm)
        record["reasoning_effort"] = decomposer_effort or llm.reasoning_effort
        payload = response_payload(
            model,
            TEAM_DECOMPOSER_SYSTEM,
            prompt,
            "team_decomposition_json",
            TEAM_DECOMPOSITION_SCHEMA,
            strict=False,
            store=llm.store,
            reasoning_effort=decomposer_effort,
            text_verbosity=llm.text_verbosity,
            max_output_tokens=llm.max_output_tokens,
            stream=llm.stream,
        )
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "Accept": "text/event-stream" if llm.stream else "application/json",
                "Connection": "close",
            },
            method="POST",
        )
        print("[team:decomposer] start", file=sys.stderr, flush=True)
        raw_text, retry_errors = post_decomposer_json(req, llm_timeout_sec(), "team_decomposition_json", llm.stream)
        if retry_errors:
            record["retry_errors"] = retry_errors
        record["raw_text"] = raw_text
        try:
            output = parse_json_object(raw_text)
            validate_schema(output, TEAM_DECOMPOSITION_SCHEMA, "team_decomposer")
        except Exception as parse_exc:
            record["parse_error"] = str(parse_exc)
            fix_prompt = repair_prompt("team_decomposer", prompt, raw_text, str(parse_exc), TEAM_DECOMPOSITION_SCHEMA)
            repair_payload = response_payload(
                model,
                TEAM_DECOMPOSER_SYSTEM,
                fix_prompt,
                "team_decomposition_repair_json",
                TEAM_DECOMPOSITION_SCHEMA,
                strict=False,
                store=llm.store,
                reasoning_effort=decomposer_effort,
                text_verbosity=llm.text_verbosity,
                max_output_tokens=llm.max_output_tokens,
                stream=llm.stream,
            )
            repair_req = urllib.request.Request(
                endpoint,
                data=json.dumps(repair_payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream" if llm.stream else "application/json",
                    "Connection": "close",
                },
                method="POST",
            )
            repair_text, repair_retry_errors = post_decomposer_json(
                repair_req,
                llm_timeout_sec(),
                "team_decomposition_repair_json",
                llm.stream,
            )
            if repair_retry_errors:
                record["repair_retry_errors"] = repair_retry_errors
            record["repair_raw_text"] = repair_text
            output = parse_json_object(repair_text)
            validate_schema(output, TEAM_DECOMPOSITION_SCHEMA, "team_decomposer")
        record["used_fallback"] = False
        record["duration_sec"] = time.monotonic() - started
        record["output"] = output
        write_json(result_path, record)
        print(f"[team:decomposer] done ({record['duration_sec']:.1f}s)", file=sys.stderr, flush=True)
        return record
    except (TimeoutError, socket.timeout, urllib.error.URLError, OSError, ValueError, json.JSONDecodeError) as exc:
        record["error"] = str(exc)
        record["used_fallback"] = False
        record["duration_sec"] = time.monotonic() - started
        if raw_text:
            record["raw_text"] = raw_text
        write_json(result_path, record)
        print(f"[team:decomposer] failed: {exc}", file=sys.stderr, flush=True)
        if enforce:
            raise TeamDecompositionError(str(exc)) from exc
        return record


def post_decomposer_json(req: urllib.request.Request, timeout_sec: int, label: str, stream: bool) -> tuple[str, list[str]]:
    errors: list[str] = []
    max_attempts = None if llm_transient_retry_unbounded() else llm_transient_attempts()
    attempt = 1
    while True:
        try:
            return read_response_text(req, timeout_sec, stream), errors
        except Exception as exc:
            errors.append(f"attempt {attempt}: {exc}")
            if not transient_llm_error(exc):
                raise
            if max_attempts is not None and attempt >= max_attempts:
                raise
            delay = retry_sleep_seconds(exc, attempt)
            retry_mode = "unbounded" if max_attempts is None else f"{attempt}/{max_attempts}"
            print(
                f"[team:decomposer] retry {label} after transient error "
                f"({retry_mode}): {exc}; sleep {delay:.1f}s",
                file=sys.stderr,
                flush=True,
            )
            time.sleep(delay)
            attempt += 1


def team_decomposer_reasoning_effort(llm: Any) -> str | None:
    raw = os.environ.get("SPATIALACC_TEAM_DECOMPOSER_REASONING_EFFORT", "").strip()
    if raw:
        return raw
    return "medium" if llm.reasoning_effort else None


def llm_or_fallback_decomposition(
    stage: str,
    objective: str,
    state: dict[str, Any],
    candidate: dict[str, Any],
    out_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    fallback = fallback_subtasks(stage, candidate)
    candidate_prompt = compact_candidate_artifact_for_prompt(candidate)
    fallback_prompt = compact_subtask_plan_for_prompt(fallback)
    prompt = build_prompt(
        agent="team_decomposer",
        task="Decide whether this stage should be decomposed into parallel specialist sub-agents, then produce the subtask plan.",
        inputs={
            "stage": stage,
            "objective": objective,
            "paper_problem_definition": "Cross-Layer Consistency Problem in Agentic LLM Spatial Accelerator Design",
            "method_boundary": "SACG-guided, template-constrained, checker-verified design closure; not free-form RTL generation.",
            "role_catalog": ROLE_CATALOG,
            "state_summary": compact_state_summary(state, candidate),
            "candidate_stage_artifact": candidate_prompt,
            "reference_subtask_plan_if_split_is_needed": fallback_prompt,
            "action_grounding_registry": ACTION_GROUNDING_REGISTRY,
            "action_contract_examples": ACTION_CONTRACT_EXAMPLES,
            "llm_policy": llm_policy_summary(),
        },
        output_schema=TEAM_DECOMPOSITION_SCHEMA,
        rules=[
            "Use split_required=false only when the stage is atomic and no independent specialist can add value.",
            "If split_required=true, create 2 to 6 subtasks. Put independent specialists in parallel_group=0 and optional auditors/evidence gates in parallel_group=1.",
            "Each subtask must have a chip-design-team role and a bounded objective.",
            "Each subtask must explicitly define role_profile and role_assignment: mission, primary_responsibilities, decision_authority, collaboration_interfaces, and out_of_scope.",
            "Each subtask must declare action_type, expected_artifacts, acceptance_checkers, handoff_to, and handoff_rule.",
            "Role assignments must make cooperation explicit: what this sub-agent consumes, what it produces, which downstream agents/tools consume its output, and which checker accepts it.",
            "Every subtask must focus on cross-layer consistency, template binding, checker evidence, implementation/deployment evidence, or repair boundaries.",
            "Ground acceptance_checkers and tool-oriented roles in action_grounding_registry. Use exact canonical names whenever possible; do not invent Qwen/OPT-specific core names unless they are supplied by the case adapter or tool protocol.",
            "Use state_summary.sacg_memory_truth, not historical memory text, to decide whether retry requests, backtrack requests, or contamination barriers are currently active blockers.",
            "If a required checker/tool is missing, mark the subtask handoff as requiring planned_tool.<short_name> or planned_checker.<short_name> implementation.",
            "Do not create agents for generic brainstorming, paper writing, marketing, or unrelated code cleanup.",
            "Use the reference subtask plan as a formatting and role-coverage guide; the actual split decision must come from the LLM response.",
        ],
    )
    prompt_path = out_dir / "team" / "decomposer_prompt.md"
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(prompt, encoding="utf-8")
    record = call_decomposer(prompt, out_dir)
    output = record.get("output")
    if not isinstance(output, dict) and llm_enforce():
        raise TeamDecompositionError(str(record.get("error") or "LLM team decomposer did not produce a valid output"))
    if not isinstance(output, dict):
        output = {
            "schema_version": "spatialaccagent.team_decomposition.v0",
            "stage": stage,
            "split_required": bool(fallback),
            "reason": "fallback decomposition used because LLM decomposition was unavailable",
            "subtasks": fallback,
        }
    if output.get("split_required") and not output.get("subtasks"):
        if llm_enforce():
            raise TeamDecompositionError("LLM team decomposer requested a split but produced no subtasks")
        output["subtasks"] = fallback
    output["subtasks"] = normalize_llm_subtasks(stage, output.get("subtasks", []))
    return output, record


def decompose_subtasks(stage: str, objective: str, state: dict[str, Any], candidate: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    decomposition, decomposer_record = llm_or_fallback_decomposition(stage, objective, state, candidate, out_dir)
    subtasks = decomposition.get("subtasks", []) if decomposition.get("split_required") else []
    return {
        "schema_version": "spatialaccagent.team_subtask_plan.v0",
        "stage": stage,
        "objective": objective,
        "decomposition_policy": "sacg_and_artifact_kind_driven",
        "decomposition_source": "llm" if not decomposer_record.get("used_fallback") else "fallback",
        "split_required": bool(decomposition.get("split_required")),
        "split_reason": decomposition.get("reason"),
        "parallel_execution": bool(subtasks),
        "paper_alignment": {
            "problem": "Cross-Layer Consistency Problem in Agentic LLM Spatial Accelerator Design",
            "method": "SACG-guided, template-constrained, checker-verified design closure",
        },
        "collaboration_contract": {
            "schema_version": "spatialaccagent.team_collaboration_contract.v0",
            "team_model": "chip_design_team",
            "rule": "Each sub-agent owns its explicit role_assignment and hands off only checker-grounded observations, risks, approval needs, and executable actions.",
            "coordination_policy": [
                "parallel specialists may disagree, but disagreement must be surfaced as bounded risks or handoff actions",
                "auditor/evidence-gate roles consume specialist outputs and must not silently rewrite them",
                "downstream stages consume the aggregate only after all required specialist roles completed without fallback",
            ],
        },
        "team_rules": TEAM_RULES,
        "role_catalog": ROLE_CATALOG,
        "subtasks": subtasks,
        "state_summary": compact_state_summary(state, candidate),
        "decomposer": {
            "record_path": str(out_dir / "team" / "decomposer_result.json"),
            "used_fallback": decomposer_record.get("used_fallback", True),
            "error": decomposer_record.get("error"),
        },
    }


def log_team_event(path: Path, event: str, payload: dict[str, Any] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "schema_version": "spatialaccagent.team_event.v0",
        "time_sec": time.time(),
        "event": event,
    }
    if payload:
        record.update(payload)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True))
        f.write("\n")


def run_one_subagent(
    subtask: dict[str, Any],
    plan: dict[str, Any],
    candidate: dict[str, Any],
    team_dir: Path,
) -> dict[str, Any]:
    stage_name = f"{plan['stage']}.{subtask['role']}"
    failure_summary = f"{subtask['role']} LLM-unavailable diagnostic for {plan['stage']}."
    try:
        result = run_stage_agent(
            agent=subtask["agent"],
            stage=stage_name,
            task=subtask["objective"],
            inputs={
                "team_context": compact_team_context_for_worker(plan),
                "subtask": compact_subtask_for_worker(subtask),
                "state_summary": plan["state_summary"],
                "candidate_stage_artifact": compact_candidate_artifact_for_worker(candidate, subtask),
            },
            out_dir=team_dir,
            fallback_summary=failure_summary,
        )
    except Exception as exc:
        result_path = team_dir / "llm" / f"{subtask['agent']}_result.json"
        prompt_path = team_dir / "llm" / f"{subtask['agent']}_prompt.md"
        output = {
            "schema_version": "spatialaccagent.stage_worker_output.v0",
            "agent": subtask["agent"],
            "stage": stage_name,
            "status": "llm_error",
            "summary": f"LLM sub-agent failed; {plan['stage']} cannot consume this role as a successful decision.",
            "sacg_focus": {
                "nodes": [],
                "edges": [],
                "constraints": [str(value) for value in subtask.get("constraints", [])],
                "artifacts": [str(value) for value in subtask.get("artifact_focus", [])],
            },
            "observations": [f"Sub-agent LLM call failed: {exc}"],
            "risks": [
                "current stage must remain blocked until this LLM role is rerun successfully",
                "deterministic tool evidence alone is not a complete agentic team decision",
            ],
            "proposed_actions": [
                "rerun this stage with the configured LLM provider available and preserve the same tool evidence"
            ],
            "executable_actions": [],
            "approval_required_for": [],
        }
        output["risks"] = [
            *output["risks"],
            failure_summary,
        ]
        write_json(
            result_path,
            {
                "schema_version": "spatialaccagent.stage_worker_record.v0",
                "prompt_protocol": PROMPT_PROTOCOL,
                "agent": subtask["agent"],
                "stage": stage_name,
                "request_path": str(prompt_path) if prompt_path.exists() else None,
                "result_path": str(result_path),
                "mode": llm_mode(),
                "used_fallback": False,
                "error": str(exc),
                "output": output,
            },
        )
        return {
            "subtask": subtask,
            "result_path": str(result_path),
            "used_fallback": False,
            "error": str(exc),
            "output": output,
            "llm_io": {
                "prompt_bytes": None,
                "duration_sec": None,
                "executable_action_count": 0,
                "used_fallback": False,
            },
        }
    output = result.get("output", {})
    return {
        "subtask": subtask,
        "result_path": result["result_path"],
        "used_fallback": result.get("used_fallback", True),
        "error": result.get("error"),
        "output": output,
        "llm_io": {
            "prompt_bytes": result.get("prompt_bytes"),
            "compact_retry_prompt_bytes": result.get("compact_retry_prompt_bytes"),
            "duration_sec": result.get("duration_sec"),
            "executable_action_count": len(output.get("executable_actions", [])) if isinstance(output, dict) else 0,
            "used_fallback": result.get("used_fallback", True),
        },
    }


def aggregate_results(plan: dict[str, Any], results: list[dict[str, Any]], errors: list[str]) -> dict[str, Any]:
    observations: list[str] = []
    risks: list[str] = []
    actions: list[str] = []
    executable_actions: list[dict[str, Any]] = []
    approvals: list[str] = []
    for item in results:
        output = item.get("output", {})
        observations.extend(str(value) for value in output.get("observations", []))
        risks.extend(str(value) for value in output.get("risks", []))
        actions.extend(str(value) for value in output.get("proposed_actions", []))
        for action in output.get("executable_actions", []):
            if isinstance(action, dict):
                executable_actions.append(action)
        approvals.extend(str(value) for value in output.get("approval_required_for", []))
    result_errors = [
        f"{item.get('subtask', {}).get('id', '<unknown>')}: {item.get('error')}"
        for item in results
        if item.get("error")
    ]
    all_errors = [*errors, *result_errors]
    prompt_bytes = [
        int(item.get("llm_io", {}).get("prompt_bytes") or 0)
        for item in results
        if item.get("llm_io", {}).get("prompt_bytes") is not None
    ]
    durations = [
        float(item.get("llm_io", {}).get("duration_sec") or 0.0)
        for item in results
        if item.get("llm_io", {}).get("duration_sec") is not None
    ]
    return {
        "schema_version": "spatialaccagent.team_aggregate.v0",
        "stage": plan["stage"],
        "status": "incomplete" if all_errors else ("no_split" if not plan.get("split_required") else "ready"),
        "subtask_count": len(plan["subtasks"]),
        "completed_subtasks": len(results),
        "parallel_execution": bool(plan.get("subtasks")),
        "execution_groups": sorted({int(item.get("parallel_group", 0)) for item in plan.get("subtasks", [])}),
        "split_reason": plan.get("split_reason"),
        "decomposition_source": plan.get("decomposition_source"),
        "used_fallback_count": sum(1 for item in results if item.get("used_fallback")),
        "errors": all_errors,
        "observations": observations,
        "risks": risks,
        "proposed_actions": actions,
        "executable_actions": executable_actions,
        "llm_io_metrics": {
            "result_count": len(results),
            "total_prompt_bytes": sum(prompt_bytes),
            "max_prompt_bytes": max(prompt_bytes) if prompt_bytes else 0,
            "total_duration_sec": sum(durations),
            "max_duration_sec": max(durations) if durations else 0.0,
            "executable_action_count": len(executable_actions),
            "subtasks_without_executable_actions": [
                item.get("subtask", {}).get("id")
                for item in results
                if int(item.get("llm_io", {}).get("executable_action_count") or 0) == 0
            ],
        },
        "role_assignments": [
            {
                "subtask_id": item.get("id"),
                "agent": item.get("agent"),
                "role": item.get("role"),
                "role_assignment": item.get("role_assignment", {}),
            }
            for item in plan.get("subtasks", [])
        ],
        "approval_required_for": sorted(set(approvals)),
    }


def run_design_team(
    *,
    stage: str,
    objective: str,
    state: dict[str, Any],
    candidate_artifact: dict[str, Any],
    out_dir: Path,
    max_workers: int = 6,
) -> dict[str, Any]:
    """Decompose a stage into parallel sub-agents and aggregate their outputs."""

    max_workers = max(1, int(os.environ.get("SPATIALACC_TEAM_LLM_WORKERS", "1") or "1"))
    team_dir = out_dir / "team"
    team_dir.mkdir(parents=True, exist_ok=True)
    plan_path = team_dir / "subtask_plan.json"
    aggregate_path = team_dir / "team_aggregate.json"
    event_log_path = team_dir / "event_log.jsonl"
    event_log_path.write_text("", encoding="utf-8")
    try:
        plan = decompose_subtasks(stage, objective, state, candidate_artifact, out_dir)
    except Exception as exc:
        error = str(exc)
        plan = {
            "schema_version": "spatialaccagent.team_subtask_plan.v0",
            "stage": stage,
            "objective": objective,
            "decomposition_policy": "sacg_and_artifact_kind_driven",
            "decomposition_source": "llm_error",
            "split_required": False,
            "split_reason": f"LLM team decomposer failed: {error}",
            "parallel_execution": False,
            "paper_alignment": {
                "problem": "Cross-Layer Consistency Problem in Agentic LLM Spatial Accelerator Design",
                "method": "SACG-guided, template-constrained, checker-verified design closure",
            },
            "collaboration_contract": {
                "schema_version": "spatialaccagent.team_collaboration_contract.v0",
                "team_model": "chip_design_team",
                "rule": "No specialist role completed; downstream stages must not consume this failed team result as design evidence.",
                "coordination_policy": ["rerun decomposition with real LLM before promotion"],
            },
            "team_rules": TEAM_RULES,
            "state_summary": compact_state_summary(state, candidate_artifact),
            "subtasks": [],
            "decomposer": {"used_fallback": False, "error": error},
        }
        aggregate = aggregate_results(plan, [], [error])
        aggregate["event_log_path"] = str(event_log_path)
        write_json(plan_path, plan)
        write_json(aggregate_path, aggregate)
        log_team_event(
            event_log_path,
            "decomposition_failed",
            {"stage": stage, "error": error, "aggregate_path": str(aggregate_path)},
        )
        return {
            "schema_version": "spatialaccagent.design_team_run.v0",
            "stage": stage,
            "subtask_plan_path": str(plan_path),
            "aggregate_path": str(aggregate_path),
            "event_log_path": str(event_log_path),
            "subtask_plan": plan,
            "aggregate": aggregate,
            "results": [],
        }
    write_json(plan_path, plan)
    write_json(
        aggregate_path,
        {
            "schema_version": "spatialaccagent.team_aggregate.v0",
            "stage": stage,
            "status": "running",
            "subtask_count": len(plan["subtasks"]),
            "completed_subtasks": 0,
            "parallel_execution": bool(plan.get("subtasks")),
            "decomposition_source": plan.get("decomposition_source"),
            "used_fallback_count": 0,
            "errors": [],
            "observations": [],
            "risks": [],
            "proposed_actions": [],
            "executable_actions": [],
            "llm_io_metrics": {
                "result_count": 0,
                "total_prompt_bytes": 0,
                "max_prompt_bytes": 0,
                "total_duration_sec": 0.0,
                "max_duration_sec": 0.0,
                "executable_action_count": 0,
                "subtasks_without_executable_actions": [],
            },
            "approval_required_for": [],
            "event_log_path": str(event_log_path),
        },
    )
    log_team_event(
        event_log_path,
        "plan_created",
        {
            "stage": stage,
            "split_required": plan["split_required"],
            "decomposition_source": plan["decomposition_source"],
            "subtask_count": len(plan["subtasks"]),
            "plan_path": str(plan_path),
        },
    )

    results: list[dict[str, Any]] = []
    errors: list[str] = []
    if plan["subtasks"]:
        for group in sorted({int(subtask.get("parallel_group", 0)) for subtask in plan["subtasks"]}):
            group_subtasks = [subtask for subtask in plan["subtasks"] if int(subtask.get("parallel_group", 0)) == group]
            workers = max(1, min(max_workers, len(group_subtasks)))
            log_team_event(
                event_log_path,
                "parallel_group_started",
                {"stage": stage, "parallel_group": group, "subtasks": [subtask["id"] for subtask in group_subtasks]},
            )
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = {}
                for subtask in group_subtasks:
                    log_team_event(
                        event_log_path,
                        "subtask_started",
                        {
                            "stage": stage,
                            "parallel_group": group,
                            "subtask_id": subtask["id"],
                            "agent": subtask["agent"],
                            "role": subtask["role"],
                            "action_type": subtask.get("action_type"),
                            "handoff_rule": subtask.get("handoff_rule"),
                        },
                    )
                    futures[pool.submit(run_one_subagent, subtask, plan, candidate_artifact, team_dir)] = subtask
            for future in as_completed(futures):
                subtask = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    log_team_event(
                        event_log_path,
                        "subtask_completed",
                        {
                            "stage": stage,
                            "parallel_group": group,
                            "subtask_id": subtask["id"],
                            "agent": subtask["agent"],
                            "used_fallback": result.get("used_fallback", True),
                            "error": result.get("error"),
                            "result_path": result.get("result_path"),
                        },
                    )
                except Exception as exc:
                    message = f"{subtask['id']}: {exc}"
                    errors.append(message)
                    log_team_event(
                        event_log_path,
                        "subtask_failed",
                        {
                            "stage": stage,
                            "parallel_group": group,
                            "subtask_id": subtask["id"],
                            "agent": subtask["agent"],
                            "error": str(exc),
                        },
                    )
            log_team_event(
                event_log_path,
                "parallel_group_completed",
                {"stage": stage, "parallel_group": group},
            )
    else:
        log_team_event(event_log_path, "no_split", {"stage": stage, "reason": plan.get("split_reason")})

    results.sort(key=lambda item: (int(item["subtask"].get("parallel_group", 0)), item["subtask"]["id"]))
    aggregate = aggregate_results(plan, results, errors)
    aggregate["event_log_path"] = str(event_log_path)
    write_json(aggregate_path, aggregate)
    log_team_event(
        event_log_path,
        "aggregate_written",
        {"stage": stage, "status": aggregate["status"], "aggregate_path": str(aggregate_path), "errors": errors},
    )
    return {
        "schema_version": "spatialaccagent.design_team_run.v0",
        "stage": stage,
        "subtask_plan_path": str(plan_path),
        "aggregate_path": str(aggregate_path),
        "event_log_path": str(event_log_path),
        "subtask_plan": plan,
        "aggregate": aggregate,
        "results": results,
    }


def team_summary(team: dict[str, Any]) -> dict[str, Any]:
    aggregate = team.get("aggregate", {})
    plan = team.get("subtask_plan", {})
    return {
        "subtask_plan": team.get("subtask_plan_path"),
        "aggregate": team.get("aggregate_path"),
        "event_log": team.get("event_log_path"),
        "split_required": plan.get("split_required"),
        "decomposition_source": plan.get("decomposition_source"),
        "decomposer_used_fallback": (plan.get("decomposer") or {}).get("used_fallback", True),
        "decomposer_error": (plan.get("decomposer") or {}).get("error"),
        "subtask_count": aggregate.get("subtask_count", 0),
        "completed_subtasks": aggregate.get("completed_subtasks", 0),
        "execution_groups": aggregate.get("execution_groups", []),
        "status": aggregate.get("status"),
        "used_fallback_count": aggregate.get("used_fallback_count", 0),
        "approval_required_for": aggregate.get("approval_required_for", []),
        "executable_actions": aggregate.get("executable_actions", []),
        "llm_io_metrics": aggregate.get("llm_io_metrics", {}),
        "errors": aggregate.get("errors", []),
    }
