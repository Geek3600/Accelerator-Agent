"""Stage-local LLM worker helpers."""

from __future__ import annotations

import json
import hashlib
import copy
import ast
import os
import re
import shlex
import socket
import ssl
import sys
import time
import urllib.error
import urllib.request
import uuid
import fcntl
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable

from accagent.framework.agent_common import compact_json, write_json
from accagent.framework.llm_config import resolved_llm_cfg
from accagent.framework.llm_io import (
    PROMPT_PROTOCOL,
    ResponseDecodeError,
    ResponseIncompleteError,
    build_prompt,
    parse_json_object,
    read_response_text,
    repair_prompt,
    response_payload,
    validate_schema,
)
from accagent.framework.sacg_utils import (
    hierarchical_learning_context,
    hierarchy_memory_context,
    read_json as read_sacg_json,
    sacg_memory_summary,
    sacg_memory_truth,
    scoped_sacg_memory_summary,
    scoped_sacg_memory_truth,
)


SYSTEM = """You are a SpatialAccAgent AI-chip-design-team stage agent.
SpatialAccAgent is an FPGA spatial accelerator automatic design multi-agent
system. The code framework is only the execution substrate; the LLM agents are
the design-team reasoning and planning roles. Review supplied natural-language
requests, structured stage artifacts, tool logs, and SACG constraints. Convert
messy evidence into bounded next actions. Do not bypass checkers, modify golden
outputs, loosen tolerance, or claim hardware pass without tool evidence.

Functional correctness requires an independent target-model reference run on
the same immutable checkpoint and stimulus used by the DUT. A deterministic
random generator may create the input stimulus, but expected outputs must come
from executing the real target model, never from random data or RTL output.
Weight files or manifests existing on disk do not prove that the DUT consumed
them: require complete-scope tensor hashes, a bound loader/harness, and executed
tool evidence. Keep the numeric comparison policy and its tolerance immutable
during a repair loop. At board level, require the exact user-supplied sample
project wrapper and source hashes rather than a simplified substitute. The
accelerator scope is Transformer blocks only: embedding/tokenization, final
model norm, LM head/logits, sampling, and other model-tail work are outside the
DUT and must not be added to its golden or weight-consumption requirements.
Return one JSON object only. No markdown.
"""

PROMPT_COMPACTION_PROTOCOL = "spatialaccagent.evidence_preserving_prompt_compaction.v10"

# The runner stages every exact-board job under this framework-owned relative
# directory. These transport values are not part of the agent's design output.
FRAMEWORK_VCS_COMMAND_CWD = "vcs_work"
FRAMEWORK_VCS_OUTPUT = "simv"


ACTION_GROUNDING_REGISTRY = {
    "schema_version": "spatialaccagent.action_grounding_registry.v0",
    "policy": (
        "Executable actions should use these tool/checker names when applicable. "
        "If a required capability is missing, name it as planned_tool.<short_name> "
        "and make the rationale say that multi-agent system capability implementation is required."
    ),
    "tool_roles": [
        "sacg_validate",
        "sacg_static_check",
        "task_card_check",
        "model_config_check",
        "numeric_policy_check",
        "template_coverage_check",
        "template_binding_static_check",
        "parameter_binding_static_check",
        "code_generation_manifest_static_check",
        "stream_plan_check",
        "memory_runtime_plan_check",
        "repair_boundary_check",
        "boundary_contract_generate",
        "failure_slice_localization",
        "boundary_trace_rerun",
        "targeted_replay",
        "connected_kernel_cctg_contradiction_targeted_replay",
        "connected_kernel_targeted_replay_check",
        "causal_repair_context_pack",
        "verification_plan_static_check",
        "tool_protocol_check",
        "human_boundary_check",
        "hierarchical_verification_plan_check",
        "verification_artifact_contract_check",
        "sacg_reference_check",
        "codegen_compile_gate",
        "codegen_contract_check",
        "codegen_package_static_check",
        "verification_artifact_contract_check",
        "required_real_tool_evidence_check",
        "real_tool_evidence_check",
        "case_real_weight_artifacts",
        "case_target_model_reference",
        "case_semantic_testbench",
        "case_operator_leaf_semantic_evidence",
        "case_single_layer_semantic_evidence",
        "case_board_semantic_evidence",
        "case_stage_leaf_static",
        "boundary_contract_check",
        "case_leaf_functional",
        "case_leaf_golden_compare",
        "case_single_transformer_layer",
        "case_single_layer_functional",
        "case_single_layer_golden_compare",
        "single_transformer_layer",
        "case_multilayer_pipeline",
        "case_multilayer_functional",
        "case_pipeline_deadlock_check",
        "case_tb_scaffold",
        "case_vcs_functional_sim",
        "functional_sim",
        "functional_sim_contract_check",
        "case_verilator_functional_sim",
        "case_weight_manifest_generate",
        "case_tb_scaffold_generate",
        "case_vcs_evidence_analyzer",
        "deadlock_watchdog",
        "data_order_trace_check",
        "transfer_count_check",
        "addr_map_check",
        "numeric_compare",
        "artifact_hash_check",
        "case_deadlock_axi_check",
        "case_board_interface_discovery",
        "case_axi_ddr_interface",
        "case_axi_protocol_check",
        "case_ddr_image_roundtrip",
        "case_vivado_synthesis",
        "case_vivado_synthesis_report_check",
        "case_vivado_implementation",
        "case_vivado_implementation_report_check",
        "case_board_shell_wrapper_generate",
        "case_runtime_abi_check",
        "case_runtime_bitstream",
        "app_shell_target_discovery_contract",
        "app_shell_target_hint_synthesis",
        "app_shell_target_discovery_after_hint",
        "backend_bounded_recovery_action",
        "backend_recovery_approval_ingest",
        "implementation_package_static",
        "timing_resource_check",
        "deployment_board_check",
        "board_runtime",
        "output_validity_check",
        "targeted_failed_checker_rerun",
        "bounded_template_repair",
        "pipeline_repair",
        "memory_runtime_repair",
        "architecture_review",
        "team_aggregate",
        "verification_action_audit",
        "llm_io_quality_check",
        "llm_semantic_extraction",
        "no_static_keyword_semantic_matching",
        "sacg_memory_update",
        "stage_retry_request",
        "stage_backtrack_request",
        "stage_artifact_trust_barrier",
        "app_shell_runtime_bitstream",
    ],
    "acceptance_checkers": [
        "sacg_static_check",
        "task_card_check",
        "model_config_check",
        "numeric_policy_check",
        "template_coverage_check",
        "parameter_binding_static_check",
        "code_generation_manifest_static_check",
        "stream_plan_check",
        "memory_runtime_plan_check",
        "boundary_contract_check",
        "failure_localization_check",
        "targeted_replay_check",
        "connected_kernel_targeted_replay_check",
        "connected_kernel_cctg_contradiction_reconciliation_check",
        "causal_repair_context_check",
        "template_binding_static_check",
        "repair_boundary_check",
        "verification_plan_static_check",
        "tool_protocol_check",
        "human_boundary_check",
        "hierarchical_verification_plan_check",
        "verification_artifact_contract_check",
        "sacg_reference_check",
        "case_stage_leaf_static",
        "boundary_contract_check",
        "case_leaf_functional",
        "case_leaf_golden_compare",
        "case_single_transformer_layer",
        "case_single_layer_functional",
        "case_single_layer_golden_compare",
        "single_transformer_layer",
        "case_multilayer_pipeline",
        "case_multilayer_functional",
        "case_pipeline_deadlock_check",
        "case_real_weight_artifacts",
        "case_target_model_reference",
        "case_semantic_testbench",
        "case_operator_leaf_semantic_evidence",
        "case_single_layer_semantic_evidence",
        "case_board_semantic_evidence",
        "real_weight_semantic_evidence_check",
        "case_tb_scaffold",
        "case_board_interface_discovery",
        "case_axi_ddr_interface",
        "case_axi_protocol_check",
        "case_ddr_image_roundtrip",
        "case_runtime_abi_check",
        "case_runtime_bitstream",
        "board_runtime",
        "functional_sim",
        "deadlock_watchdog",
        "data_order_trace_check",
        "transfer_count_check",
        "addr_map_check",
        "numeric_compare",
        "artifact_hash_check",
        "codegen_compile_gate_check",
        "codegen_contract_check",
        "codegen_package_static_check",
        "verification_artifact_contract_check",
        "required_real_tool_evidence_check",
        "real_tool.case_real_weight_artifacts",
        "real_tool.boundary_contract_check",
        "real_tool.case_leaf_functional",
        "real_tool.case_leaf_golden_compare",
        "real_tool.case_tb_scaffold",
        "real_tool.case_single_transformer_layer",
        "real_tool.case_single_layer_functional",
        "real_tool.case_single_layer_golden_compare",
        "real_tool.case_multilayer_functional",
        "real_tool.case_pipeline_deadlock_check",
        "real_tool.case_vcs_functional_sim",
        "real_tool.case_verilator_functional_sim",
        "real_tool.case_deadlock_axi_check",
        "real_tool.case_board_interface_discovery",
        "real_tool.case_axi_ddr_interface",
        "real_tool.case_axi_protocol_check",
        "real_tool.case_ddr_image_roundtrip",
        "real_tool.case_vivado_synthesis",
        "real_tool.case_vivado_synthesis_report_check",
        "real_tool.case_vivado_implementation",
        "real_tool.case_vivado_implementation_report_check",
        "real_tool.case_board_shell_wrapper_generate",
        "real_tool.case_runtime_abi_check",
        "real_tool.case_runtime_bitstream",
        "real_tool.app_shell_target_discovery_contract",
        "real_tool.app_shell_target_hint_synthesis",
        "real_tool.app_shell_target_discovery_after_hint",
        "real_tool.board_runtime",
        "real_tool.app_shell_runtime_bitstream",
        "implementation_package_static",
        "timing_resource_check",
        "deployment_board_check",
        "output_validity_check",
        "targeted_failed_checker_rerun",
        "verification_action_audit_check",
        "llm_io_quality_check",
        "llm_semantic_extraction_check",
        "no_static_keyword_semantic_matching_check",
        "sacg_memory_check",
        "stage_retry_request_check",
        "stage_backtrack_request_check",
        "stage_artifact_trust_barrier_check",
        "backend_app_shell_integration_contract_static_check",
        "backend_app_shell_target_discovery_check",
        "backend_app_shell_target_hint_synthesis_check",
        "backend_bounded_recovery_action_check",
        "backend_recovery_approval_ingest_check",
    ],
}


ACTION_CONTRACT_EXAMPLES = [
    {
        "id": "example.prepare_real_model_semantic_verification",
        "stage": "verification",
        "action_type": "verification_evidence_preparation",
        "rationale": "Build immutable semantic evidence from the current case adapter before any hardware correctness claim.",
        "consumes": [
            "artifact.input.model_config",
            "artifact.input.numeric_policy",
            "artifact.stage3.pipeline_plan",
            "current case-adapter target checkpoint",
            "generated/memory/dut_weight_binding_manifest.json",
        ],
        "produces": [
            "verification/real_weights/full_tensor_catalog.json",
            "verification/model_reference/reference_manifest.json",
            "verification/semantic_testbench/semantic_testbench_manifest.json",
            "verification/semantic_testbench/dut_weight_binding_requirements.json",
        ],
        "tool_roles": [
            "case_weight_manifest_generate",
            "case_target_model_reference",
            "case_semantic_testbench",
        ],
        "acceptance_checkers": [
            "case_real_weight_artifacts",
            "case_target_model_reference",
            "case_semantic_testbench",
        ],
        "on_failure": "treat missing reference, explicit tolerance, semantic harness, or DUT weight consumption as a verification-capability/code-generation blocker; do not run a legacy fallback test or promote the layer.",
        "requires_approval": False,
    },
    {
        "id": "example.run_real_functional_sim",
        "stage": "verification",
        "action_type": "real_tool_execution",
        "rationale": "Run a real simulator after static hierarchy and artifact gates pass.",
        "consumes": [
            "artifact.stage6.verification_artifact_contract",
            "verification/model_reference/reference_manifest.json",
            "verification/semantic_testbench/semantic_testbench_manifest.json",
            "generated/memory/dut_weight_binding_manifest.json",
            "verification/board_simulation/board_simulation_manifest.json",
        ],
        "produces": [
            "verification/vcs/case_functional_sim.log",
            "verification/board_simulation/rtl_output.memh",
            "verification/debug_closure/boundary_trace.json",
            "verification/case_diagnostics/vcs_functional_diagnosis.json",
            "verification/semantic_evidence/board_axi_ddr.json",
        ],
        "tool_roles": [
            "case_vcs_functional_sim",
            "case_vcs_evidence_analyzer",
            "case_board_semantic_evidence",
        ],
        "acceptance_checkers": [
            "functional_sim",
            "data_order_trace_check",
            "deadlock_watchdog",
            "real_weight_semantic_evidence_check",
        ],
        "on_failure": "route simulator evidence to the Stage-6 repair loop with the violated SACG constraints; do not proceed to Vivado.",
        "requires_approval": False,
    },
    {
        "id": "example.declare_missing_capability",
        "stage": "verification",
        "action_type": "system_capability_gap",
        "rationale": "The design team needs a checker not yet implemented by the multi-agent system.",
        "consumes": ["artifact.stage6.verification_plan"],
        "produces": ["planned checker implementation task"],
        "tool_roles": ["planned_tool.formal_axi_property_runner"],
        "acceptance_checkers": ["planned_checker.formal_axi_property_check"],
        "on_failure": "block promotion until the planned checker is implemented or an approved equivalent exists.",
        "requires_approval": True,
    },
    {
        "id": "example.ambiguous_backend_target_recovery",
        "stage": "backend_board",
        "action_type": "bounded_recovery",
        "rationale": "Real backend evidence produced multiple plausible shell integration targets, so the design team must not guess.",
        "consumes": [
            "artifact.stage7.app_shell_integration_contract",
            "artifact.stage7.app_shell_target_selection_decision",
            "backend_board/case_diagnostics/app_shell_target_discovery_after_hint.json",
        ],
        "produces": ["artifact.stage7.backend_bounded_recovery_actions"],
        "tool_roles": ["app_shell_target_hint_synthesis", "app_shell_target_discovery_after_hint"],
        "acceptance_checkers": [
            "backend_app_shell_target_hint_synthesis_check",
            "backend_bounded_recovery_action_check",
            "human_boundary_check",
        ],
        "on_failure": "keep runtime bitstream and board runtime blocked until the target contract has cited evidence or explicit approval",
        "requires_approval": True,
    },
]


STAGE_AGENT_SCHEMA = {
    "type": "object",
    "additionalProperties": True,
    "properties": {
        "schema_version": {"type": "string"},
        "agent": {"type": "string"},
        "stage": {"type": "string"},
        "status": {"type": "string"},
        "summary": {"type": "string"},
        "sacg_focus": {
            "type": "object",
            "additionalProperties": True,
            "properties": {
                "nodes": {"type": "array", "items": {"type": "string"}},
                "edges": {"type": "array", "items": {"type": "string"}},
                "constraints": {"type": "array", "items": {"type": "string"}},
                "artifacts": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["nodes", "edges", "constraints", "artifacts"],
        },
        "observations": {"type": "array", "items": {"type": "string"}},
        "risks": {"type": "array", "items": {"type": "string"}},
        "proposed_actions": {"type": "array", "items": {"type": "string"}},
        "executable_actions": {
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
                    "on_failure": {"type": "string"},
                    "requires_approval": {"type": "boolean"},
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
                    "on_failure",
                    "requires_approval",
                ],
            },
        },
        "approval_required_for": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "schema_version",
        "agent",
        "stage",
        "status",
        "summary",
        "sacg_focus",
        "observations",
        "risks",
        "proposed_actions",
        "executable_actions",
        "approval_required_for",
    ],
}


class StageLLMError(ValueError):
    pass


class PromptCompactionNeeded(RuntimeError):
    pass


def prompt_hash(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def llm_cache_ignore_prompt_hash() -> bool:
    return os.environ.get("SPATIALACC_LLM_CACHE_IGNORE_PROMPT_HASH", "0").strip().lower() in {"1", "true", "yes", "on"}


def llm_cache_disabled(agent: str | None = None) -> bool:
    if os.environ.get("SPATIALACC_LLM_DISABLE_CACHE", "0").strip().lower() in {"1", "true", "yes", "on"}:
        return True
    disabled_agents = {
        item.strip()
        for item in os.environ.get("SPATIALACC_LLM_DISABLE_CACHE_AGENTS", "").split(",")
        if item.strip()
    }
    return bool(agent and ("*" in disabled_agents or agent in disabled_agents))


def cached_stage_worker_record(
    path: Path,
    expected_prompt_hash: str,
    agent: str | None = None,
    output_schema: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    if llm_cache_disabled(agent):
        return None
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
    if data.get("compact_retry_request_path") and data.get("prompt_compaction_protocol") != PROMPT_COMPACTION_PROTOCOL:
        return None
    output = data.get("output")
    if not isinstance(output, dict):
        return None
    if isinstance(output_schema, dict):
        try:
            validate_schema(output, output_schema, agent or "cached_output")
        except ValueError:
            return None
    if not stage_worker_output_cacheable(output):
        return None
    return data


ARTIFACT_HISTORY_SCHEMA = "spatialaccagent.stage_worker_artifact_snapshot.v1"
LIVE_LLM_TRANSACTION_SCHEMA = "spatialaccagent.stage_worker_live_transaction.v1"
LIVE_LLM_TRANSACTION_HISTORY_SCHEMA = (
    "spatialaccagent.stage_worker_live_transaction_archive.v1"
)


def _utc_timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _bounded_live_error(value: Any, limit: int = 1200) -> str:
    text = str(value).replace("\x00", " ")
    return text if len(text) <= limit else text[:limit] + "..."


def _file_sha256_if_readable(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _live_transaction_context_binding(
    source_state: Any,
    learning_context: dict[str, Any],
) -> dict[str, Any]:
    binding: dict[str, Any] = {
        "hierarchical_learning_context_sha256": hashlib.sha256(
            json.dumps(
                learning_context,
                ensure_ascii=True,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest(),
        "hierarchical_learning_context_status": learning_context.get("status"),
        "validated_lower_layer_certificate_count": len(
            learning_context.get("validated_lower_layer_certificates", [])
        )
        if isinstance(learning_context.get("validated_lower_layer_certificates"), list)
        else 0,
    }
    if not source_state:
        return binding
    path = Path(str(source_state))
    binding["source_sacg_state_path"] = str(path)
    binding["source_sacg_state_sha256"] = _file_sha256_if_readable(path)
    return binding


def live_llm_transaction_path(llm_dir: Path, agent: str) -> Path:
    return llm_dir / f"{agent}_live_transaction.json"


def _publish_live_llm_status(path: Path, transaction: dict[str, Any]) -> None:
    """Mirror one active request into the fixed cross-module live state."""

    try:
        from accagent.framework.live_state import (
            activate_live_state_slot,
            run_dir_from_live_artifact,
            update_live_state_slot,
        )

        run_dir = run_dir_from_live_artifact(path)
        transaction_id = str(transaction.get("transaction_id") or "")
        if run_dir is None or not transaction_id:
            return
        payload = {
            key: transaction.get(key)
            for key in (
                "agent",
                "stage",
                "status",
                "owner_pid",
                "attempt_count",
                "retry_count",
                "last_event",
                "last_attempt",
                "started_at",
                "updated_at",
                "completed_at",
                "output_status",
            )
            if transaction.get(key) is not None
        }
        if transaction.get("status") == "inflight":
            activate_live_state_slot(
                run_dir,
                "agent",
                payload,
                binding=transaction_id,
            )
        else:
            update_live_state_slot(
                run_dir,
                "agent",
                payload,
                binding=transaction_id,
            )
    except Exception as exc:
        print(
            f"[stage:llm] shared live status update failed: {_bounded_live_error(exc)}",
            file=sys.stderr,
            flush=True,
        )


def _read_live_llm_transaction(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise StageLLMError(
            f"cannot read live LLM transaction ledger: {path}: {exc}"
        ) from exc
    if not isinstance(data, dict):
        raise StageLLMError(f"live LLM transaction ledger is not an object: {path}")
    return data


def ensure_no_active_live_llm_transaction(path: Path) -> None:
    """Reject a duplicate controller before it can overwrite prompt evidence."""

    previous = _read_live_llm_transaction(path)
    if previous is None or previous.get("status") != "inflight":
        return
    owner_pid = previous.get("owner_pid")
    if process_alive(owner_pid):
        raise StageLLMError(
            "refusing duplicate LLM transaction while the prior transaction is "
            f"still live: {path}; owner_pid={owner_pid}; "
            f"prompt_hash={previous.get('prompt_hash')}"
        )


def _write_live_llm_transaction(path: Path, data: dict[str, Any]) -> None:
    """Atomically persist a framework-owned, credential-free LLM ledger."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)
            f.write("\n")
        temporary.replace(path)
    except OSError as exc:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise StageLLMError(
            f"cannot persist live LLM transaction ledger: {path}: {exc}"
        ) from exc


def _archive_live_llm_transaction(
    path: Path,
    transaction: dict[str, Any],
    *,
    reason: str,
    replacement_prompt_hash: str,
) -> Path:
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    history_dir = path.parent / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    archive_path = history_dir / f"{path.stem}.{digest[:16]}.live.json"
    archive = {
        "schema_version": LIVE_LLM_TRANSACTION_HISTORY_SCHEMA,
        "archive_reason": reason,
        "archived_at": (
            transaction.get("updated_at")
            or transaction.get("started_at")
            or _utc_timestamp()
        ),
        "replacement_prompt_hash": replacement_prompt_hash,
        "source_path": str(path),
        "source_sha256": digest,
        "transaction": transaction,
    }
    if archive_path.exists():
        existing = _read_live_llm_transaction(archive_path)
        if existing != archive:
            raise StageLLMError(
                f"immutable live LLM transaction history collision: {archive_path}"
            )
    else:
        _write_live_llm_transaction(archive_path, archive)
    path.unlink()
    return archive_path


def begin_live_llm_transaction(
    path: Path,
    *,
    agent: str,
    stage: str,
    prompt_hash_value: str,
    prompt_path: Path,
    prompt_bytes: int,
    result_path: Path,
    model: str,
    reasoning_effort: str | None,
    stream: bool,
    context_binding: dict[str, Any],
    http_transport: str = "urllib",
) -> dict[str, Any]:
    """Create one durable transaction before the first provider request.

    A live transaction is deliberately separate from the terminal result record.
    A restarted controller can therefore distinguish an owned, still-running
    request from a stale request that may be safely retried without overwriting
    the previous Agent evidence.
    """

    previous = _read_live_llm_transaction(path)
    if previous is not None:
        active = previous.get("status") == "inflight"
        owner_pid = previous.get("owner_pid")
        if active and process_alive(owner_pid):
            ensure_no_active_live_llm_transaction(path)
        _archive_live_llm_transaction(
            path,
            previous,
            reason="stale_inflight" if active else "terminal_transaction_replaced",
            replacement_prompt_hash=prompt_hash_value,
        )

    now = _utc_timestamp()
    transaction = {
        "schema_version": LIVE_LLM_TRANSACTION_SCHEMA,
        "transaction_id": uuid.uuid4().hex,
        "status": "inflight",
        "agent": agent,
        "stage": stage,
        "owner_pid": os.getpid(),
        "prompt_hash": prompt_hash_value,
        "prompt_path": str(prompt_path),
        "prompt_sha256": _file_sha256_if_readable(prompt_path),
        "prompt_bytes": prompt_bytes,
        "result_path": str(result_path),
        "model": model,
        "reasoning_effort": reasoning_effort,
        "initial_transport": "responses_sse_stream" if stream else "responses_json",
        "http_transport": http_transport,
        "attempt_count": 0,
        "retry_count": 0,
        "last_event": "transaction_started",
        "last_attempt": None,
        "retry_event_history": [],
        "started_at": now,
        "updated_at": now,
        "context_binding": context_binding,
    }
    _write_live_llm_transaction(path, transaction)
    _publish_live_llm_status(path, transaction)
    return transaction


def update_live_llm_transaction(
    path: Path,
    transaction_id: str,
    event: dict[str, Any],
) -> None:
    """Record a bounded retry heartbeat without changing Agent semantics."""

    try:
        transaction = _read_live_llm_transaction(path)
        if (
            transaction is None
            or transaction.get("transaction_id") != transaction_id
            or transaction.get("status") != "inflight"
        ):
            return
        event_kind = str(event.get("kind") or "unknown")
        now = _utc_timestamp()
        safe_event = {
            key: _bounded_live_error(value) if key == "error" else value
            for key, value in event.items()
            if key in {
                "kind",
                "attempt",
                "schema_name",
                "transport",
                "next_transport",
                "delay_sec",
                "error",
            }
        }
        safe_event["at"] = now
        transaction["updated_at"] = now
        transaction["last_event"] = event_kind
        transaction["last_attempt"] = safe_event
        if event_kind == "attempt_started":
            transaction["attempt_count"] = int(transaction.get("attempt_count", 0)) + 1
        if event_kind == "retry_scheduled":
            transaction["retry_count"] = int(transaction.get("retry_count", 0)) + 1
        history = transaction.get("retry_event_history")
        history = history if isinstance(history, list) else []
        history.append(safe_event)
        transaction["retry_event_history"] = history[-32:]
        _write_live_llm_transaction(path, transaction)
        _publish_live_llm_status(path, transaction)
    except Exception as exc:
        print(
            f"[stage:llm] live transaction ledger update failed: {_bounded_live_error(exc)}",
            file=sys.stderr,
            flush=True,
        )


def finish_live_llm_transaction(
    path: Path,
    transaction_id: str,
    *,
    status: str,
    result_path: Path,
    output_status: str | None = None,
    error: str | None = None,
) -> None:
    transaction = _read_live_llm_transaction(path)
    if transaction is None or transaction.get("transaction_id") != transaction_id:
        return
    now = _utc_timestamp()
    transaction.update(
        {
            "status": status,
            "completed_at": now,
            "updated_at": now,
            "last_event": "transaction_completed" if status == "completed" else "transaction_failed",
            "result_path": str(result_path),
            "result_sha256": _file_sha256_if_readable(result_path),
        }
    )
    if output_status is not None:
        transaction["output_status"] = output_status
    if error:
        transaction["error"] = _bounded_live_error(error)
    _write_live_llm_transaction(path, transaction)
    _publish_live_llm_status(path, transaction)


def _history_local_path(path: Path, root: Path) -> Path | None:
    """Return a resolved generated-artifact path only when it stays in ``root``."""
    try:
        resolved = path.resolve()
        resolved.relative_to(root.resolve())
    except (OSError, ValueError):
        return None
    return resolved


def archive_replaced_stage_worker_artifacts(
    result_path: Path,
    prompt_path: Path,
    retry_prompt_path: Path,
    next_prompt_hash: str,
) -> dict[str, Any] | None:
    """Snapshot prior local LLM evidence before a non-cached request replaces it.

    A retry or a changed prompt used to overwrite the only result and prompt
    paths.  The immutable snapshot keeps the prior decision, its exact prompt,
    and schema-repair text together without allowing artifact paths outside the
    framework-owned LLM directory to be copied.
    """
    if not result_path.exists():
        return None
    try:
        result_bytes = result_path.read_bytes()
    except OSError as exc:
        raise StageLLMError(
            f"cannot preserve prior LLM result before replacement: {result_path}: {exc}"
        ) from exc

    result_sha256 = hashlib.sha256(result_bytes).hexdigest()
    try:
        prior_record = json.loads(result_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        prior_record = {}
    if not isinstance(prior_record, dict):
        prior_record = {}
    prior_prompt_hash = str(prior_record.get("prompt_hash") or "no_prompt_hash")
    snapshot_id = ".".join(
        (
            result_sha256[:16],
            hashlib.sha256(prior_prompt_hash.encode("utf-8")).hexdigest()[:16],
            next_prompt_hash[:16],
        )
    )

    llm_dir = result_path.parent.resolve()
    source_paths: list[Path] = [result_path, prompt_path, retry_prompt_path]
    for key in ("request_path", "full_prompt_path", "compact_retry_request_path"):
        value = prior_record.get(key)
        if isinstance(value, str) and value:
            local = _history_local_path(Path(value), llm_dir)
            if local is not None:
                source_paths.append(local)
    repair_attempts = prior_record.get("schema_repair_attempts")
    if isinstance(repair_attempts, list):
        for attempt in repair_attempts:
            if not isinstance(attempt, dict):
                continue
            value = attempt.get("output_path")
            if isinstance(value, str) and value:
                local = _history_local_path(Path(value), llm_dir)
                if local is not None:
                    source_paths.append(local)

    unique_sources: list[Path] = []
    seen_sources: set[Path] = set()
    for source in source_paths:
        local = _history_local_path(source, llm_dir)
        if local is None or local in seen_sources:
            continue
        seen_sources.add(local)
        unique_sources.append(local)

    history_dir = llm_dir / "history"
    try:
        history_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise StageLLMError(
            f"cannot create LLM artifact history directory: {history_dir}: {exc}"
        ) from exc

    archived_files: list[dict[str, Any]] = []
    for source in unique_sources:
        if not source.is_file():
            continue
        try:
            content = result_bytes if source == result_path.resolve() else source.read_bytes()
        except OSError as exc:
            raise StageLLMError(
                f"cannot preserve prior LLM artifact before replacement: {source}: {exc}"
            ) from exc
        content_sha256 = hashlib.sha256(content).hexdigest()
        destination = history_dir / (
            f"{source.stem}.{snapshot_id}.{content_sha256[:16]}{source.suffix}"
        )
        try:
            if destination.exists():
                if destination.read_bytes() != content:
                    raise StageLLMError(
                        f"immutable LLM artifact history collision: {destination}"
                    )
            else:
                destination.write_bytes(content)
        except OSError as exc:
            raise StageLLMError(
                f"cannot write LLM artifact history: {destination}: {exc}"
            ) from exc
        archived_files.append(
            {
                "source_path": str(source),
                "source_sha256": content_sha256,
                "snapshot_path": str(destination),
            }
        )

    manifest_path = history_dir / f"{result_path.stem}.{snapshot_id}.snapshot.json"
    manifest = {
        "schema_version": ARTIFACT_HISTORY_SCHEMA,
        "snapshot_id": snapshot_id,
        "replaced_result_path": str(result_path),
        "replaced_result_sha256": result_sha256,
        "replaced_prompt_hash": prior_prompt_hash,
        "replacement_prompt_hash": next_prompt_hash,
        "archived_files": archived_files,
    }
    try:
        if manifest_path.exists():
            existing_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if existing_manifest != manifest:
                manifest_identity = hashlib.sha256(
                    json.dumps(
                        manifest,
                        ensure_ascii=True,
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode("utf-8")
                ).hexdigest()[:16]
                manifest_path = history_dir / (
                    f"{result_path.stem}.{snapshot_id}.{manifest_identity}.snapshot.json"
                )
                if manifest_path.exists():
                    existing_manifest = json.loads(
                        manifest_path.read_text(encoding="utf-8")
                    )
                    if existing_manifest != manifest:
                        raise StageLLMError(
                            "immutable LLM artifact history variant collision: "
                            f"{manifest_path}"
                        )
                else:
                    write_json(manifest_path, manifest)
        else:
            write_json(manifest_path, manifest)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise StageLLMError(
            f"cannot write LLM artifact history manifest: {manifest_path}: {exc}"
        ) from exc
    return {
        "schema_version": ARTIFACT_HISTORY_SCHEMA,
        "snapshot_id": snapshot_id,
        "manifest_path": str(manifest_path),
        "replaced_result_sha256": result_sha256,
        "replaced_prompt_hash": prior_prompt_hash,
        "archived_file_count": len(archived_files),
    }


def stage_worker_output_cacheable(output: dict[str, Any]) -> bool:
    status = str(output.get("status") or "").strip().lower()
    if not status:
        return False
    # A non-promoting review is diagnostic evidence for its own attempt only.
    # Reusing it on a same-stage retry replays an old decision without any new
    # observation or repair artifact, which can create an endless controller
    # loop. Cache only conclusions that may advance their public stage.
    return status in {"ready", "pass", "proceed", "accepted", "complete", "completed"}


def llm_mode() -> str:
    return resolved_llm_cfg().mode


def llm_enforce() -> bool:
    return resolved_llm_cfg().enforce


def llm_timeout_sec() -> int:
    return resolved_llm_cfg().timeout_sec


def llm_transient_attempts(default: int = 4) -> int:
    raw = os.environ.get("SPATIALACC_LLM_TRANSIENT_ATTEMPTS", "")
    if not raw:
        return default
    try:
        return max(1, int(raw))
    except ValueError:
        return default


def retry_bool_env(name: str, default: bool) -> bool:
    raw = os.environ.get(name, "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


def llm_transient_retry_unbounded() -> bool:
    return retry_bool_env("SPATIALACC_LLM_TRANSIENT_RETRY_UNBOUNDED", True)


def retry_404_model_route_errors() -> bool:
    return retry_bool_env("SPATIALACC_LLM_RETRY_404_MODEL_ROUTE", True)


def provider_capacity_error(exc: Exception) -> bool:
    """Recognize explicit provider quota exhaustion without masking 403 auth errors."""

    if not isinstance(exc, urllib.error.HTTPError) or exc.code != 403:
        return False
    text = str(exc).lower()
    return any(
        term in text
        for term in (
            "daily usage limit",
            "daily quota",
            "quota exceeded",
            "usage limit exceeded",
            "billing_error",
            "capacity exhausted",
        )
    )


def llm_stream_transport_fallback() -> bool:
    return retry_bool_env("SPATIALACC_LLM_STREAM_TRANSPORT_FALLBACK", True)


def llm_auto_compact_retry() -> bool:
    return retry_bool_env("SPATIALACC_LLM_AUTO_COMPACT_RETRY", True)


def llm_auto_compact_min_prompt_bytes() -> int:
    raw = os.environ.get("SPATIALACC_LLM_AUTO_COMPACT_MIN_PROMPT_BYTES", "").strip()
    if not raw:
        return 2_000_000
    try:
        return max(1, int(raw))
    except ValueError:
        return 2_000_000


def checkpoint_specialist_auto_compact_min_prompt_bytes() -> int:
    raw = os.environ.get(
        "SPATIALACC_CHECKPOINT_SPECIALIST_COMPACT_MIN_PROMPT_BYTES",
        "",
    ).strip()
    if not raw:
        return 256_000
    try:
        return max(1, int(raw))
    except ValueError:
        return 256_000


def llm_auto_compact_after_attempts() -> int:
    raw = os.environ.get("SPATIALACC_LLM_AUTO_COMPACT_AFTER_ATTEMPTS", "").strip()
    if not raw:
        return 2
    try:
        return max(1, int(raw))
    except ValueError:
        return 2


def retry_float_env(name: str, default: float) -> float:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return max(0.0, float(raw))
    except ValueError:
        return default


def llm_max_inflight() -> int:
    raw = os.environ.get("SPATIALACC_LLM_MAX_INFLIGHT", "1").strip()
    try:
        return max(1, min(10, int(raw)))
    except ValueError:
        return 1


def process_alive(pid: Any) -> bool:
    try:
        pid_int = int(pid)
    except (TypeError, ValueError):
        return False
    if pid_int <= 0:
        return False
    try:
        os.kill(pid_int, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def llm_limiter_dir() -> Path:
    return Path(os.environ.get("SPATIALACC_LLM_LIMITER_DIR", "/tmp/spatialaccagent_llm_limiter"))


def llm_slot_wait_sec() -> float:
    return retry_float_env("SPATIALACC_LLM_SLOT_WAIT_SEC", 2.0)


def llm_timeout_slot_hold_sec() -> float:
    return retry_float_env("SPATIALACC_LLM_TIMEOUT_SLOT_HOLD_SEC", 180.0)


def timeout_like_exception(exc: BaseException | None) -> bool:
    if exc is None:
        return False
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return True
    text = str(exc).lower()
    return "timed out" in text or "timeout" in text


def read_limiter_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "schema_version": "spatialaccagent.llm_inflight_limiter.v1",
            "leases": {},
            "waiters": [],
        }
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {
            "schema_version": "spatialaccagent.llm_inflight_limiter.v1",
            "leases": {},
            "waiters": [],
        }
    if not isinstance(data, dict):
        return {
            "schema_version": "spatialaccagent.llm_inflight_limiter.v1",
            "leases": {},
            "waiters": [],
        }
    leases = data.get("leases")
    if not isinstance(leases, dict):
        data["leases"] = {}
    waiters = data.get("waiters")
    if not isinstance(waiters, list):
        data["waiters"] = []
    data["schema_version"] = "spatialaccagent.llm_inflight_limiter.v1"
    return data


def write_limiter_state(path: Path, data: dict[str, Any]) -> None:
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")
    tmp.replace(path)


def prune_limiter_state(state: dict[str, Any], now: float) -> bool:
    """Drop stale limiter leases and FIFO waiters from a persisted state."""

    changed = False
    leases = state.setdefault("leases", {})
    for key, lease in list(leases.items()):
        if (
            not isinstance(lease, dict)
            or float(lease.get("expires_at", 0.0)) <= now
            or not process_alive(lease.get("pid"))
        ):
            leases.pop(key, None)
            changed = True

    waiters = state.setdefault("waiters", [])
    valid_waiters: list[dict[str, Any]] = []
    seen_waiter_ids: set[str] = set()
    for waiter in waiters:
        if not isinstance(waiter, dict):
            changed = True
            continue
        waiter_id = str(waiter.get("waiter_id") or "")
        if (
            not waiter_id
            or waiter_id in seen_waiter_ids
            or not process_alive(waiter.get("pid"))
        ):
            changed = True
            continue
        seen_waiter_ids.add(waiter_id)
        valid_waiters.append(waiter)
    if valid_waiters != waiters:
        state["waiters"] = valid_waiters
        changed = True
    return changed


def remove_limiter_waiter(state: dict[str, Any], waiter_id: str) -> bool:
    waiters = state.setdefault("waiters", [])
    retained = [
        waiter
        for waiter in waiters
        if not (
            isinstance(waiter, dict) and waiter.get("waiter_id") == waiter_id
        )
    ]
    if retained == waiters:
        return False
    state["waiters"] = retained
    return True


@contextmanager
def llm_inflight_slot(schema_name: str):
    """Cross-process limiter for outbound LLM HTTP requests.

    Client-side timeouts may leave an upstream request running after our process
    retries. Timeout leases are therefore held briefly instead of being released
    immediately, which prevents a retry storm from exceeding account limits.
    """

    limiter_dir = llm_limiter_dir()
    limiter_dir.mkdir(parents=True, exist_ok=True)
    lock_path = limiter_dir / "inflight.lock"
    state_path = limiter_dir / "inflight.json"
    lease_id = f"{os.getpid()}-{uuid.uuid4().hex}"
    acquired = False
    queued = False
    try:
        while not acquired:
            now = time.time()
            with lock_path.open("a+", encoding="utf-8") as lock_file:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
                state = read_limiter_state(state_path)
                changed = prune_limiter_state(state, now)
                leases = state.setdefault("leases", {})
                waiters = state.setdefault("waiters", [])
                if not queued:
                    waiters.append(
                        {
                            "waiter_id": lease_id,
                            "pid": os.getpid(),
                            "schema_name": schema_name,
                            "enqueued_at": now,
                        }
                    )
                    queued = True
                    changed = True
                if (
                    waiters
                    and waiters[0].get("waiter_id") == lease_id
                    and len(leases) < llm_max_inflight()
                ):
                    waiters.pop(0)
                    leases[lease_id] = {
                        "pid": os.getpid(),
                        "schema_name": schema_name,
                        "started_at": now,
                        "expires_at": now
                        + max(60.0, llm_timeout_sec() + llm_timeout_slot_hold_sec()),
                    }
                    state["max_inflight"] = llm_max_inflight()
                    changed = True
                    acquired = True
                if changed:
                    write_limiter_state(state_path, state)
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            if not acquired:
                time.sleep(llm_slot_wait_sec())
    except BaseException:
        if queued and not acquired:
            with lock_path.open("a+", encoding="utf-8") as lock_file:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
                state = read_limiter_state(state_path)
                changed = prune_limiter_state(state, time.time())
                changed = remove_limiter_waiter(state, lease_id) or changed
                if changed:
                    write_limiter_state(state_path, state)
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        raise
    exc: BaseException | None = None
    try:
        yield
    except BaseException as caught:
        exc = caught
        raise
    finally:
        with lock_path.open("a+", encoding="utf-8") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            state = read_limiter_state(state_path)
            leases = state.setdefault("leases", {})
            if lease_id in leases:
                if timeout_like_exception(exc):
                    leases[lease_id]["expires_at"] = time.time() + llm_timeout_slot_hold_sec()
                    leases[lease_id]["timeout_hold"] = True
                else:
                    leases.pop(lease_id, None)
            write_limiter_state(state_path, state)
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def retry_after_seconds(exc: Exception) -> float | None:
    if not isinstance(exc, urllib.error.HTTPError):
        return None
    value = exc.headers.get("Retry-After") if exc.headers else None
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        return None


def retry_sleep_seconds(exc: Exception, attempt: int) -> float:
    base = retry_float_env("SPATIALACC_LLM_RETRY_BASE_SEC", 8.0)
    max_delay = retry_float_env("SPATIALACC_LLM_RETRY_MAX_SEC", 90.0)
    retry_after = retry_after_seconds(exc)
    delay = min(max_delay, base * (2 ** max(0, attempt - 1)))
    if isinstance(exc, urllib.error.HTTPError) and exc.code == 429:
        delay = min(max_delay, max(delay, base * attempt * attempt))
    if provider_capacity_error(exc):
        delay = max(
            delay,
            retry_float_env("SPATIALACC_LLM_CAPACITY_RETRY_SEC", 900.0),
        )
    if retry_after is not None:
        delay = min(max_delay, max(delay, retry_after))
    return delay


def record_retry_error(errors: list[str], message: str, cap: int = 64) -> None:
    if len(errors) < cap:
        errors.append(message)
        return
    errors[-1] = f"... additional transient retry errors suppressed; latest: {message}"


def fallback_output(agent: str, stage: str, summary: str) -> dict[str, Any]:
    return {
        "schema_version": "spatialaccagent.stage_worker_output.v0",
        "agent": agent,
        "stage": stage,
        "status": "fallback",
        "summary": summary,
        "sacg_focus": {"nodes": [], "edges": [], "constraints": [], "artifacts": []},
        "observations": ["LLM stage worker was not executed"],
        "risks": ["fallback mode is not valid for the AI-chip-design-team multi-agent system"],
        "proposed_actions": [],
        "executable_actions": [],
        "approval_required_for": [],
    }


def llm_error_output(agent: str, stage: str, error: str, summary: str) -> dict[str, Any]:
    return {
        "schema_version": "spatialaccagent.stage_worker_output.v0",
        "agent": agent,
        "stage": stage,
        "status": "llm_error",
        "summary": summary,
        "sacg_focus": {"nodes": [], "edges": [], "constraints": [], "artifacts": []},
        "observations": [f"LLM worker failed: {error}"],
        "risks": [
            "this stage cannot consume the worker output as an agentic decision",
            "rerun the stage with a working LLM provider and preserve existing tool evidence",
        ],
        "proposed_actions": ["rerun the current stage after the LLM provider/configuration is available"],
        "executable_actions": [],
        "approval_required_for": [],
    }


def llm_policy_summary() -> dict[str, Any]:
    llm = resolved_llm_cfg()
    return {
        "schema_version": "spatialaccagent.llm_policy.v0",
        "mode": llm.mode,
        "enforce": llm.enforce,
        "model": llm.model,
        "configured_model": llm.configured_model,
        "requested_model_override": llm.requested_model_override,
        "model_selection_policy": (
            "An explicit runtime model selection is authoritative and is recorded "
            "with the stage worker; it does not require a duplicate approval artifact."
        ),
        "configuration_error": llm.configuration_error,
        "endpoint_configured": bool(llm.endpoint),
        "api_key_configured": bool(llm.api_key),
        "reasoning_effort": llm.reasoning_effort,
        "policy": "LLM planning/review is mandatory for agentic stages when enforce=true; fallback records are diagnostics only and must not be consumed as successful agent decisions.",
    }


def call_llm(
    endpoint: str,
    key: str,
    model: str,
    prompt: str,
    schema_name: str,
    schema: dict[str, Any],
    timeout_sec: int,
    reasoning_effort: str | None = None,
    stream_override: bool | None = None,
) -> str:
    llm = resolved_llm_cfg()
    effort = llm.reasoning_effort if reasoning_effort is None else reasoning_effort
    stream = llm.stream if stream_override is None else stream_override
    payload = response_payload(
        model,
        SYSTEM,
        prompt,
        schema_name,
        schema,
        strict=False,
        store=llm.store,
        reasoning_effort=effort or None,
        text_verbosity=llm.text_verbosity,
        max_output_tokens=llm.max_output_tokens,
        stream=stream,
    )
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream" if stream else "application/json",
            "Connection": "close",
        },
        method="POST",
    )
    with llm_inflight_slot(schema_name):
        return read_response_text(req, timeout_sec, stream)


def transient_llm_error(exc: Exception) -> bool:
    if isinstance(exc, PromptCompactionNeeded):
        return True
    if isinstance(exc, ResponseIncompleteError):
        return True
    if isinstance(exc, ResponseDecodeError):
        return True
    if isinstance(exc, urllib.error.HTTPError):
        if exc.code == 404 and retry_404_model_route_errors():
            return True
        if provider_capacity_error(exc):
            return True
        return exc.code in {408, 409, 425, 426, 429, 500, 502, 503, 504}
    if isinstance(exc, (TimeoutError, socket.timeout, ssl.SSLError, urllib.error.URLError)):
        return True
    text = str(exc).lower()
    deterministic_request_errors = [
        "context_length_exceeded",
        "input exceeds the context window",
        "maximum context length",
        "request too large",
    ]
    if any(term in text for term in deterministic_request_errors):
        return False
    transient_terms = [
        "timed out",
        "bad record mac",
        "bad gateway",
        "decryption failed",
        "http error 502",
        "http error 503",
        "http error 504",
        "http error 426",
        "upgrade required",
        "websocket upgrade required",
        "remote end closed",
        "connection reset",
        "connection aborted",
        "ssl",
        "rate_limit_exceeded",
        "server_error",
        "upstream_error",
        "upstream request failed",
        "response.failed",
        "response.incomplete",
        "max_output_tokens",
        "llm returned no output text",
        "streaming llm response returned no output text",
        "service unavailable",
        "concurrency limit exceeded",
        "please retry later",
    ]
    return any(term in text for term in transient_terms)


def llm_context_window_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return any(
        term in text
        for term in (
            "context_length_exceeded",
            "input exceeds the context window",
            "maximum context length",
            "request too large",
        )
    )


def stream_transport_fallback_error(exc: Exception) -> bool:
    if not llm_stream_transport_fallback():
        return False
    if isinstance(exc, ResponseIncompleteError):
        return False
    if isinstance(exc, ResponseDecodeError):
        return True
    if isinstance(exc, urllib.error.HTTPError):
        return exc.code in {408, 426, 500, 502, 503, 504}
    text = str(exc).lower()
    fallback_terms = [
        "bad gateway",
        "http error 502",
        "http error 503",
        "http error 504",
        "http error 426",
        "upgrade required",
        "websocket upgrade required",
        "response.failed",
        "streaming llm response returned no output text",
        "remote end closed",
        "connection reset",
        "connection aborted",
        "upstream_error",
        "upstream request failed",
    ]
    return any(term in text for term in fallback_terms)


def llm_output_budget_error(exc: Exception) -> bool:
    if isinstance(exc, ResponseIncompleteError):
        return exc.reason == "max_output_tokens"
    text = str(exc).lower()
    return "response.incomplete" in text and "max_output_tokens" in text


def call_llm_with_retry(
    endpoint: str,
    key: str,
    model: str,
    prompt: str,
    schema_name: str,
    schema: dict[str, Any],
    timeout_sec: int,
    attempts: int | None = None,
    reasoning_effort: str | None = None,
    allow_auto_compact: bool = True,
    transaction_observer: Callable[[dict[str, Any]], None] | None = None,
) -> tuple[str, list[str]]:
    errors: list[str] = []
    max_attempts = None if attempts is None and llm_transient_retry_unbounded() else (
        llm_transient_attempts() if attempts is None else max(1, attempts)
    )
    attempt = 1
    stream_override: bool | None = None

    def observe(kind: str, **fields: Any) -> None:
        if transaction_observer is None:
            return
        transaction_observer({"kind": kind, **fields})

    while True:
        use_stream = (
            resolved_llm_cfg().stream
            if stream_override is None
            else stream_override
        )
        transport = "responses_sse_stream" if use_stream else "responses_json"
        observe(
            "attempt_started",
            attempt=attempt,
            schema_name=schema_name,
            transport=transport,
        )
        try:
            text = call_llm(
                endpoint,
                key,
                model,
                prompt,
                schema_name,
                schema,
                timeout_sec,
                reasoning_effort=reasoning_effort,
                stream_override=stream_override,
            )
            observe(
                "response_received",
                attempt=attempt,
                schema_name=schema_name,
                transport=transport,
            )
            return text, errors
        except Exception as exc:
            record_retry_error(errors, f"attempt {attempt}: {exc}")
            observe(
                "attempt_failed",
                attempt=attempt,
                schema_name=schema_name,
                transport=transport,
                error=str(exc),
            )
            if not transient_llm_error(exc):
                raise
            if max_attempts is not None and attempt >= max_attempts:
                raise
            delay = retry_sleep_seconds(exc, attempt)
            retry_mode = "unbounded" if max_attempts is None else f"{attempt}/{max_attempts}"
            print(
                f"[stage:llm] retry {schema_name} after transient error "
                f"({retry_mode}): {exc}; sleep {delay:.1f}s",
                file=sys.stderr,
                flush=True,
            )
            if stream_transport_fallback_error(exc):
                current_stream = (
                    resolved_llm_cfg().stream
                    if stream_override is None
                    else stream_override
                )
                stream_override = not current_stream
                if stream_override:
                    transport = "responses_sse_stream"
                    reason = "after responses_json transport failure"
                else:
                    transport = "responses_json"
                    reason = "after streaming/upstream transport failure"
                print(
                    f"[stage:llm] switching {schema_name} retry transport to {transport} "
                    f"{reason}",
                    file=sys.stderr,
                    flush=True,
                )
            if (
                allow_auto_compact
                and llm_auto_compact_retry()
                and len(prompt.encode("utf-8")) >= llm_auto_compact_min_prompt_bytes()
                and attempt >= llm_auto_compact_after_attempts()
                and (
                    stream_transport_fallback_error(exc)
                    or llm_output_budget_error(exc)
                )
            ):
                recovery = (
                    "exhausted its output budget"
                    if llm_output_budget_error(exc)
                    else "failed"
                )
                raise PromptCompactionNeeded(
                    f"large LLM prompt ({len(prompt.encode('utf-8'))} bytes) {recovery} after "
                    f"{attempt} transient attempt(s); use evidence-preserving compact retry"
                ) from exc
            next_stream = (
                resolved_llm_cfg().stream
                if stream_override is None
                else stream_override
            )
            observe(
                "retry_scheduled",
                attempt=attempt,
                schema_name=schema_name,
                transport=transport,
                next_transport=(
                    "responses_sse_stream" if next_stream else "responses_json"
                ),
                delay_sec=delay,
                error=str(exc),
            )
            time.sleep(delay)
            attempt += 1


def compact_param_binding_for_retry(row: dict[str, Any]) -> dict[str, Any]:
    bound = row.get("bound_params", {}) if isinstance(row.get("bound_params"), dict) else {}
    return {
        "role": row.get("role"),
        "op": row.get("op"),
        "matched_op": row.get("matched_op"),
        "template_id": row.get("template_id"),
        "source": row.get("source"),
        "required_params": row.get("required_params", []),
        "status": row.get("status"),
        "missing_params": row.get("missing_params", []),
        "legality_errors": row.get("legality_errors", []),
        "bound_params": {
            str(key): {
                "value": value.get("value"),
                "status": value.get("status"),
                "source": value.get("source"),
                "candidate_values": value.get("candidate_values"),
                "legal_values": value.get("legal_values"),
            }
            for key, value in bound.items()
            if isinstance(value, dict)
        },
    }


def compact_source_check_for_retry(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "op": row.get("op"),
        "template_id": row.get("template_id"),
        "source": row.get("source"),
        "path": row.get("path"),
        "exists": row.get("exists"),
        "sha256": row.get("sha256"),
        "case_class": row.get("case_class"),
        "metadata_required_params": row.get("metadata_required_params", []),
        "status": row.get("status"),
        "errors": row.get("errors", []),
        "missing_required_params_in_constructor": row.get("missing_required_params_in_constructor", []),
        "source_required_params_missing_from_metadata": row.get("source_required_params_missing_from_metadata", []),
        "numeric_constructor_params_not_bound_by_metadata": row.get("numeric_constructor_params_not_bound_by_metadata", []),
    }


def retry_focus_text(inputs: dict[str, Any]) -> str:
    parts = [str(inputs.get("stage") or ""), str(inputs.get("agent") or "")]
    subtask = inputs.get("subtask")
    if isinstance(subtask, dict):
        for key in ["role", "title", "objective"]:
            parts.append(str(subtask.get(key) or ""))
            parts.extend(str(value) for value in subtask.get("artifact_focus", []) if value is not None)
    return " ".join(parts).lower()


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _canonical_json_sha256(value: Any) -> str:
    return _hash_text(_canonical_json(value))


def _python_source_contract(source: str) -> dict[str, Any] | None:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    functions: list[dict[str, Any]] = []
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        strings: list[str] = []
        calls: list[str] = []
        for child in ast.walk(node):
            if isinstance(child, ast.Constant) and isinstance(child.value, str):
                value = child.value
                if value and len(value) <= 240 and value not in strings:
                    strings.append(value)
            elif isinstance(child, ast.Call):
                try:
                    name = ast.unparse(child.func)
                except (AttributeError, ValueError):
                    continue
                if name and name not in calls:
                    calls.append(name)
        try:
            signature = ast.unparse(node.args)
            returns = ast.unparse(node.returns) if node.returns is not None else None
        except (AttributeError, ValueError):
            signature = ""
            returns = None
        functions.append(
            {
                "name": node.name,
                "signature": signature,
                "returns": returns,
                "calls": calls,
                "contract_strings": strings,
            }
        )
    if not functions:
        return None
    call_dictionary: list[str] = []
    call_indices: dict[str, int] = {}
    token_dictionary: list[str] = []
    token_indices: dict[str, int] = {}
    compact_functions: list[dict[str, Any]] = []
    for function in functions:
        function_calls: list[int] = []
        for call in function.pop("calls", []):
            if call not in call_indices:
                call_indices[call] = len(call_dictionary)
                call_dictionary.append(call)
            function_calls.append(call_indices[call])
        tokens: list[int] = []
        prose: list[str] = []
        for value in function.pop("contract_strings", []):
            if any(character.isspace() for character in value):
                prose.append(value)
                continue
            if value not in token_indices:
                token_indices[value] = len(token_dictionary)
                token_dictionary.append(value)
            tokens.append(token_indices[value])
        function["call_indices"] = function_calls
        function["contract_token_indices"] = tokens
        if prose:
            function["omitted_prose_contract"] = {
                "count": len(prose),
                "canonical_sha256": _canonical_json_sha256(prose),
            }
        compact_functions.append(function)
    return {
        "encoding": "spatialaccagent.python_ast_consumer_contract.v1",
        "function_count": len(compact_functions),
        "call_dictionary": call_dictionary,
        "contract_token_dictionary": token_dictionary,
        "functions": _lossless_columnar_rows(compact_functions),
        "policy": {
            "function_names_signatures_returns_calls_and_nonprose_contract_tokens_preserved": True,
            "redundant_runtime_error_and_help_prose_omitted_by_count_and_hash": True,
        },
    }


def _bounded_projection_value(value: Any, *, head_chars: int = 800, tail_chars: int = 200) -> Any:
    if not isinstance(value, str) or len(value) <= head_chars + tail_chars:
        return value
    projection = {
        "text_chars": len(value),
        "text_sha256": _hash_text(value),
        "text_head": value[:head_chars],
        "text_tail": value[-tail_chars:] if tail_chars else "",
    }
    source_contract = _python_source_contract(value)
    if source_contract is not None:
        projection["python_ast_contract"] = source_contract
    return projection


def _columnar_projection(rows: Any, columns: list[str] | None = None) -> dict[str, Any]:
    records = [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []
    if columns is None:
        columns = sorted({str(key) for row in records for key in row})
    return {
        "encoding": "spatialaccagent.lossless_columnar_rows.v0",
        "columns": columns,
        "row_count": len(records),
        "rows_sha256": _canonical_json_sha256(records),
        "rows": [[row.get(key) for key in columns] for row in records],
    }


def _encoded_column(values: list[Any]) -> dict[str, Any]:
    """Choose the smallest JSON-readable, lossless encoding for one column."""

    candidates: list[dict[str, Any]] = [{"encoding": "values", "values": values}]
    dictionary: list[Any] = []
    indices: list[int] = []
    value_indices: dict[str, int] = {}
    for value in values:
        key = _canonical_json(value)
        if key not in value_indices:
            value_indices[key] = len(dictionary)
            dictionary.append(value)
        indices.append(value_indices[key])
    if len(dictionary) == 1 and values:
        candidates.append(
            {"encoding": "constant", "value": dictionary[0], "row_count": len(values)}
        )
    else:
        candidates.append(
            {"encoding": "dictionary", "dictionary": dictionary, "indices": indices}
        )

    if values and all(isinstance(value, int) and not isinstance(value, bool) for value in values):
        step = values[1] - values[0] if len(values) > 1 else 0
        if all(value == values[0] + index * step for index, value in enumerate(values)):
            candidates.append(
                {
                    "encoding": "arithmetic_sequence",
                    "start": values[0],
                    "step": step,
                    "row_count": len(values),
                }
            )

    if values and all(isinstance(value, str) for value in values):
        prefix = os.path.commonprefix(values)
        if len(prefix) >= 4:
            candidates.append(
                {
                    "encoding": "common_prefix_strings",
                    "prefix": prefix,
                    "suffixes": [value[len(prefix) :] for value in values],
                }
            )
        if all("/" in value for value in values):
            component_dictionary: list[str] = []
            component_indices: dict[str, int] = {}
            rows: list[list[int]] = []
            for value in values:
                row: list[int] = []
                for component in value.split("/"):
                    if component not in component_indices:
                        component_indices[component] = len(component_dictionary)
                        component_dictionary.append(component)
                    row.append(component_indices[component])
                rows.append(row)
            candidates.append(
                {
                    "encoding": "slash_component_strings",
                    "component_dictionary": component_dictionary,
                    "rows": rows,
                }
            )
    return min(candidates, key=lambda value: len(_canonical_json(value).encode("utf-8")))


def _decode_encoded_column(encoded: dict[str, Any]) -> list[Any]:
    encoding = str(encoded.get("encoding") or "")
    if encoding == "values":
        return list(encoded.get("values", []))
    if encoding == "dictionary":
        dictionary = encoded.get("dictionary", [])
        return [dictionary[index] for index in encoded.get("indices", [])]
    if encoding == "constant":
        return [copy.deepcopy(encoded.get("value")) for _ in range(int(encoded.get("row_count", 0)))]
    if encoding == "arithmetic_sequence":
        start = int(encoded.get("start", 0))
        step = int(encoded.get("step", 0))
        return [start + index * step for index in range(int(encoded.get("row_count", 0)))]
    if encoding == "common_prefix_strings":
        prefix = str(encoded.get("prefix") or "")
        return [prefix + str(suffix) for suffix in encoded.get("suffixes", [])]
    if encoding == "slash_component_strings":
        dictionary = encoded.get("component_dictionary", [])
        return ["/".join(str(dictionary[index]) for index in row) for row in encoded.get("rows", [])]
    raise ValueError(f"unsupported compact column encoding: {encoding}")


def _dictionary_column_projection(records: list[dict[str, Any]]) -> tuple[list[str], dict[str, Any]]:
    columns = sorted({str(key) for row in records for key in row})
    encoded_columns = {
        column: _encoded_column([row.get(column) for row in records])
        for column in columns
    }
    return columns, encoded_columns


def _lossless_columnar_rows(records: list[dict[str, Any]]) -> dict[str, Any]:
    columns, encoded_columns = _dictionary_column_projection(records)
    return {
        "encoding": "spatialaccagent.lossless_dictionary_column_rows.v1",
        "row_count": len(records),
        "column_order": columns,
        "columns": encoded_columns,
        "sparse_presence": _sparse_row_presence(records, columns),
        "canonical_sha256": _canonical_json_sha256(records),
    }


def _decode_lossless_columnar_rows(table: dict[str, Any]) -> list[dict[str, Any]]:
    row_count = int(table.get("row_count", 0))
    columns = [str(value) for value in table.get("column_order", [])]
    sparse = table.get("sparse_presence", {})
    decoded = {
        column: _decode_encoded_column(table.get("columns", {}).get(column, {}))
        for column in columns
    }
    rows: list[dict[str, Any]] = []
    for index in range(row_count):
        row: dict[str, Any] = {}
        for column in columns:
            presence = sparse.get(column)
            if isinstance(presence, str) and (index >= len(presence) or presence[index] != "1"):
                continue
            values = decoded[column]
            if index >= len(values):
                raise ValueError(f"compact column {column} is shorter than row_count")
            row[column] = copy.deepcopy(values[index])
        rows.append(row)
    return rows


def _decode_lossless_columnar_rows_if_present(value: Any) -> list[dict[str, Any]]:
    """Return editable rows from either their normal or compact form."""

    if isinstance(value, list):
        return [row for row in value if isinstance(row, dict)]
    if not (
        isinstance(value, dict)
        and value.get("encoding")
        == "spatialaccagent.lossless_dictionary_column_rows.v1"
    ):
        return []
    try:
        rows = _decode_lossless_columnar_rows(value)
    except (TypeError, ValueError):
        return []
    return [row for row in rows if isinstance(row, dict)]


def _lossless_hierarchical_rows(
    records: list[dict[str, Any]],
    nested_fields: dict[str, Any],
) -> dict[str, Any]:
    """Columnize repeated objects while retaining ordered nested child lists."""

    base_rows = [copy.deepcopy(row) for row in records]
    nested: dict[str, Any] = {}
    for field, child_fields in nested_fields.items():
        if not all(field not in row or isinstance(row.get(field), list) for row in base_rows):
            continue
        children: list[dict[str, Any]] = []
        offsets = [0]
        presence = []
        valid = True
        for row in base_rows:
            present = field in row
            presence.append("1" if present else "0")
            values = row.pop(field, []) if present else []
            if not all(isinstance(value, dict) for value in values):
                valid = False
                break
            children.extend(copy.deepcopy(values))
            offsets.append(len(children))
        if not valid:
            base_rows = [copy.deepcopy(row) for row in records]
            nested = {}
            break
        nested[field] = {
            "parent_row_offsets": offsets,
            "field_presence": "".join(presence),
            "rows": _lossless_hierarchical_rows(children, child_fields),
        }
    return {
        "encoding": "spatialaccagent.lossless_hierarchical_column_rows.v1",
        "row_count": len(records),
        "canonical_sha256": _canonical_json_sha256(records),
        "rows": _lossless_columnar_rows(base_rows),
        "nested_fields": nested,
    }


def _decode_lossless_hierarchical_rows(table: dict[str, Any]) -> list[dict[str, Any]]:
    rows = _decode_lossless_columnar_rows(table.get("rows", {}))
    for field, child in table.get("nested_fields", {}).items():
        child_rows = _decode_lossless_hierarchical_rows(child.get("rows", {}))
        offsets = child.get("parent_row_offsets", [])
        presence = str(child.get("field_presence") or "")
        if len(offsets) != len(rows) + 1:
            raise ValueError(f"invalid parent offsets for compact nested field {field}")
        for index, row in enumerate(rows):
            if index < len(presence) and presence[index] == "1":
                row[str(field)] = copy.deepcopy(child_rows[int(offsets[index]) : int(offsets[index + 1])])
    return rows


def _lossless_mapping_rows(mapping: dict[str, Any]) -> dict[str, Any]:
    keys = list(mapping)
    values = [mapping[key] for key in keys]
    if all(isinstance(value, dict) for value in values):
        encoded_values: Any = _lossless_columnar_rows(values)
    else:
        encoded_values = _encoded_column(values)
    return {
        "encoding": "spatialaccagent.lossless_ordered_mapping.v1",
        "keys": _encoded_column(keys),
        "values": encoded_values,
        "canonical_sha256": _canonical_json_sha256(mapping),
    }


def _decode_lossless_mapping_rows(table: dict[str, Any]) -> dict[str, Any]:
    keys = _decode_encoded_column(table.get("keys", {}))
    values_table = table.get("values", {})
    if str(values_table.get("encoding") or "").startswith("spatialaccagent.lossless_dictionary_column_rows"):
        values = _decode_lossless_columnar_rows(values_table)
    else:
        values = _decode_encoded_column(values_table)
    return {str(key): copy.deepcopy(value) for key, value in zip(keys, values)}


def _sparse_row_presence(records: list[Any], columns: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for column in columns:
        bits = "".join("1" if isinstance(row, dict) and column in row else "0" for row in records)
        if "0" in bits:
            result[column] = bits
    return result


def _bound_artifact_value(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    artifact_value = value.get("value")
    return artifact_value if isinstance(artifact_value, dict) else value


def _shared_board_source_index(
    identity: dict[str, Any],
    compile_authority: dict[str, Any],
) -> dict[str, Any]:
    closure = identity.get("selected_simulation_source_closure", {})
    identity_rows = closure.get("source_files", []) if isinstance(closure, dict) else []
    compile_rows = compile_authority.get("compile_sources", [])
    hash_rows = identity.get("source_hashes", [])
    source_index_authority = "vivado_vcs_compile_authority"
    if not compile_rows:
        compile_rows = copy.deepcopy(identity_rows)
        source_index_authority = (
            "frozen_compute_slot_identity_source_closure"
            if compile_authority.get("schema_version")
            == "spatialaccagent.frozen_compute_slot_vcs_compile_authority.v1"
            else "exact_board_identity_source_closure"
        )
    if not all(isinstance(rows, list) and rows for rows in (identity_rows, compile_rows, hash_rows)):
        return {}

    def keyed(rows: list[Any]) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        for row in rows:
            if not isinstance(row, dict) or not row.get("source_id"):
                return {}
            source_id = str(row["source_id"])
            if source_id in result:
                return {}
            result[source_id] = row
        return result

    identity_by_id = keyed(identity_rows)
    compile_by_id = keyed(compile_rows)
    hashes_by_id = keyed(hash_rows)
    if not identity_by_id or not compile_by_id or not hashes_by_id:
        return {}
    def source_order(source_id: str) -> tuple[int, str]:
        raw = compile_by_id.get(source_id, {}).get(
            "compile_order", identity_by_id.get(source_id, {}).get("compile_order", 1 << 60)
        )
        try:
            order = int(raw)
        except (TypeError, ValueError):
            order = 1 << 60
        return order, source_id

    source_ids = sorted(set(identity_by_id) | set(compile_by_id) | set(hashes_by_id), key=source_order)
    merged_rows: list[dict[str, Any]] = []
    for source_id in source_ids:
        identity_row = identity_by_id.get(source_id, {})
        compile_row = compile_by_id.get(source_id, {})
        hash_row = hashes_by_id.get(source_id, {})
        merged: dict[str, Any] = {"source_id": source_id}
        for key, value in identity_row.items():
            if key in {"source_id", "path"}:
                continue
            merged[key] = value
        identity_path = identity_row.get("path")
        if identity_path != merged.get("local_path"):
            merged["identity_path"] = identity_path
        for key, value in compile_row.items():
            if key == "source_id":
                continue
            if key == "file_type" and value == merged.get("language"):
                continue
            if key not in merged:
                merged[key] = value
            elif merged[key] != value:
                merged[f"compile_{key}"] = value
        source_hash_path = hash_row.get("path")
        if source_hash_path != merged.get("remote_path"):
            merged["source_hash_path"] = source_hash_path
        for key in ("role", "sha256"):
            value = hash_row.get(key)
            if value != merged.get(key):
                merged[f"source_hash_{key}"] = value
        merged_rows.append(merged)

    path_prefixes: dict[str, str] = {}
    path_columns = sorted(
        {
            key
            for row in merged_rows
            for key, value in row.items()
            if isinstance(value, str)
            and value.startswith("/")
            and (key.endswith("path") or key == "parent_composite_file")
        }
    )
    for key in path_columns:
        values = [str(row[key]) for row in merged_rows if isinstance(row.get(key), str) and str(row[key]).startswith("/")]
        if len(values) < 4:
            continue
        try:
            prefix = os.path.commonpath(values)
        except ValueError:
            continue
        if len(prefix) < 20:
            continue
        alias = f"@{key}_root"
        path_prefixes[alias] = prefix
        for row in merged_rows:
            value = row.get(key)
            if isinstance(value, str) and (value == prefix or value.startswith(prefix + "/")):
                row[key] = alias + value[len(prefix) :]

    derived_fields: dict[str, Any] = {}
    for field, canonical in (
        ("local_sha256", "sha256"),
        ("remote_sha256", "sha256"),
        ("file_type", "language"),
    ):
        if all(row.get(field) == row.get(canonical) for row in merged_rows):
            derived_fields[field] = {"copy_from": canonical}
            for row in merged_rows:
                row.pop(field, None)
    if all(row.get("evidence_refs") == [row.get("source_id")] for row in merged_rows):
        derived_fields["evidence_refs"] = {"expression": "[source_id]"}
        for row in merged_rows:
            row.pop("evidence_refs", None)
    if all(row.get("compile_order") == index for index, row in enumerate(merged_rows)):
        derived_fields["compile_order"] = {"expression": "row_index"}
        for row in merged_rows:
            row.pop("compile_order", None)
    staged_paths = [row.get("staged_path") for row in merged_rows]
    local_paths = [row.get("local_path") for row in merged_rows]
    if (
        all(isinstance(value, str) for value in staged_paths + local_paths)
        and len({str(Path(value).parent) for value in staged_paths}) == 1
        and all(Path(str(staged)).name == Path(str(local)).name for staged, local in zip(staged_paths, local_paths))
    ):
        staged_parent = str(Path(str(staged_paths[0])).parent)
        derived_fields["staged_path"] = {
            "expression": "join(staged_parent, basename(local_path))",
            "staged_parent": staged_parent,
        }
        for row in merged_rows:
            row.pop("staged_path", None)
    columns, encoded_columns = _dictionary_column_projection(merged_rows)
    identity_source_ids = [str(row.get("source_id")) for row in identity_rows]
    identity_columns = sorted({str(key) for row in identity_rows if isinstance(row, dict) for key in row})
    compile_columns = sorted({str(key) for row in compile_rows if isinstance(row, dict) for key in row})
    hash_columns = sorted({str(key) for row in hash_rows if isinstance(row, dict) for key in row})
    identity_path_field = (
        "local_path"
        if all(row.get("path") == row.get("local_path") for row in identity_rows if isinstance(row, dict))
        else "identity_path"
    )
    source_hash_path_field = (
        "remote_path"
        if all(
            hashes_by_id[source_id].get("path") == compile_by_id.get(source_id, {}).get("remote_path")
            for source_id in hashes_by_id
        )
        else "source_hash_path"
    )
    compile_field_aliases: dict[str, str] = {}
    for column in compile_columns:
        if column == "file_type" and all(
            row.get("file_type") == row.get("language") for row in compile_rows if isinstance(row, dict)
        ):
            compile_field_aliases[column] = "language"
        elif any(
            source_id in identity_by_id
            and column in identity_by_id[source_id]
            and compile_by_id[source_id].get(column) != identity_by_id[source_id].get(column)
            for source_id in compile_by_id
        ):
            compile_field_aliases[column] = f"compile_{column}"
    hash_field_aliases: dict[str, str] = {"path": source_hash_path_field}
    for column in ("role", "sha256"):
        if any(
            source_id in identity_by_id
            and hashes_by_id[source_id].get(column) != identity_by_id[source_id].get(column)
            for source_id in hashes_by_id
        ):
            hash_field_aliases[column] = f"source_hash_{column}"
    views: dict[str, Any] = {
        "identity_source_files": {
            "columns": identity_columns,
            "field_aliases": {"path": identity_path_field},
            "sparse_presence": _sparse_row_presence(identity_rows, identity_columns),
            "row_count": len(identity_rows),
            "canonical_sha256": _canonical_json_sha256(identity_rows),
        },
        "compile_sources": {
            "columns": compile_columns,
            "field_aliases": compile_field_aliases,
            "sparse_presence": _sparse_row_presence(compile_rows, compile_columns),
            "row_count": len(compile_rows),
            "canonical_sha256": _canonical_json_sha256(compile_rows),
        },
        "source_hashes": {
            "columns": hash_columns,
            "field_aliases": hash_field_aliases,
            "sparse_presence": _sparse_row_presence(hash_rows, hash_columns),
            "row_count": len(hash_rows),
            "canonical_sha256": _canonical_json_sha256(hash_rows),
        },
        "source_ids": {
            "column": "source_id",
            "row_count": len(identity_source_ids),
            "canonical_sha256": _canonical_json_sha256(identity_source_ids),
        },
        "compiler_input_source_ids": {
            "column": "source_id",
            "row_ranges_inclusive": _contiguous_index_ranges(
                [source_ids.index(str(row.get("source_id"))) for row in compile_rows]
            ),
            "row_count": len(compile_rows),
            "canonical_sha256": _canonical_json_sha256(
                [str(row.get("source_id")) for row in compile_rows]
            ),
        },
    }
    replacement = identity.get("compute_slot_abi", {}).get("replacement_boundary", {})
    if isinstance(replacement, dict):
        evidence = replacement.get("source_module_evidence", [])
        excluded = {
            str(row.get("source_id"))
            for row in evidence
            if isinstance(row, dict) and row.get("source_id")
        }
        retained = replacement.get("retained_source_ids", [])
        expected_retained = [source_id for source_id in identity_source_ids if source_id not in excluded]
        if isinstance(retained, list) and [str(item) for item in retained] == expected_retained:
            views["retained_source_ids"] = {
                "column": "source_id",
                "exclude_source_ids": sorted(excluded),
                "row_count": len(retained),
                "canonical_sha256": _canonical_json_sha256(retained),
            }
    return {
        "encoding": "spatialaccagent.lossless_dictionary_column_source_index.v0",
        "source_index_authority": source_index_authority,
        "row_count": len(merged_rows),
        "column_order": columns,
        "columns": encoded_columns,
        "sparse_presence": _sparse_row_presence(merged_rows, columns),
        "rows_sha256": _canonical_json_sha256(merged_rows),
        "path_prefixes": path_prefixes,
        "derived_fields": derived_fields,
        "views": views,
    }


def _compact_shared_board_source_index_for_generation(
    index: dict[str, Any],
) -> dict[str, Any]:
    retained_columns = {
        "source_id",
        "language",
        "library",
        "role",
        "closure_role",
        "declared_modules",
        "dependencies",
        "file_set",
        "source_set",
        "used_in",
        "hashes_match",
        "is_global_include",
    }
    original_columns = [str(value) for value in index.get("column_order", [])]
    selected_columns = [value for value in original_columns if value in retained_columns]
    columns = index.get("columns", {}) if isinstance(index.get("columns"), dict) else {}
    projected = {
        key: copy.deepcopy(index.get(key))
        for key in (
            "encoding",
            "source_index_authority",
            "row_count",
            "rows_sha256",
            "sparse_presence",
            "views",
        )
        if key in index
    }
    if isinstance(projected.get("views"), dict):
        projected["views"].pop("source_hashes", None)
        if (
            projected.get("source_index_authority")
            == "exact_board_identity_source_closure"
        ):
            projected["views"].pop("compile_sources", None)
    projected["column_order"] = selected_columns
    projected["columns"] = {
        key: copy.deepcopy(columns[key]) for key in selected_columns if key in columns
    }
    projected["sparse_presence"] = {
        key: value
        for key, value in projected.get("sparse_presence", {}).items()
        if key in selected_columns
    }
    derived = index.get("derived_fields", {}) if isinstance(index.get("derived_fields"), dict) else {}
    projected["derived_fields"] = {
        key: copy.deepcopy(value)
        for key, value in derived.items()
        if key in {"compile_order", "evidence_refs"}
    }
    available_view_fields = set(selected_columns) | set(projected["derived_fields"])
    for view in projected.get("views", {}).values():
        if not isinstance(view, dict) or not isinstance(view.get("columns"), list):
            continue
        original_view_columns = [str(value) for value in view["columns"]]
        field_aliases = (
            view.get("field_aliases", {})
            if isinstance(view.get("field_aliases"), dict)
            else {}
        )
        retained_view_columns = [
            field
            for field in original_view_columns
            if field in available_view_fields
            or str(field_aliases.get(field) or "") in available_view_fields
        ]
        view["columns"] = retained_view_columns
        view["field_aliases"] = {
            field: alias
            for field, alias in field_aliases.items()
            if field in retained_view_columns and alias in available_view_fields
        }
        view["projection_contract"] = {
            "omitted_columns": [
                field for field in original_view_columns if field not in retained_view_columns
            ],
            "complete_view_is_bound_by_its_canonical_sha256": True,
            "omitted_transport_and_integrity_fields_are_framework_owned": True,
        }
    omitted = [value for value in original_columns if value not in selected_columns]
    projected["omitted_path_and_owner_alias_contract"] = {
        "columns": omitted,
        "canonical_sha256": _canonical_json_sha256(
            {key: columns.get(key) for key in omitted}
        ),
        "full_rows_are_bound_by_identity_and_compile_authority_hashes": True,
        "generation_uses_source_ids_and_structured_module_metadata_not_host_paths": True,
    }
    projected["per_source_integrity_contract"] = {
        "omitted_columns": [
            value for value in ("sha256", "size_bytes") if value in omitted
        ],
        "canonical_sha256": _canonical_json_sha256(
            {key: columns.get(key) for key in ("sha256", "size_bytes") if key in columns}
        ),
        "full_rows_are_bound_by_board_identity_and_compile_authority_artifact_sha256": True,
        "integrity_metadata_is_not_a_generation_decision": True,
    }
    projected["projection_policy"] = {
        "every_source_id_preserved": True,
        "language_library_role_and_module_identity_preserved": True,
        "per_source_integrity_is_hash_bound_once_not_repeated_in_prompt": True,
        "host_path_aliases_are_not_generation_decisions": True,
    }
    return projected


def _contiguous_index_ranges(indices: list[int]) -> list[list[int]]:
    if not indices:
        return []
    ranges: list[list[int]] = []
    start = previous = indices[0]
    for value in indices[1:]:
        if value == previous + 1:
            previous = value
            continue
        ranges.append([start, previous])
        start = previous = value
    ranges.append([start, previous])
    return ranges


def _vcs_export_semantic_ast(
    text: str,
    compile_sources: list[dict[str, Any]],
    *,
    compile_source_view: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Retain executable VCS semantics while omitting shell help/error boilerplate."""

    source_rows = {
        str(row.get("source_id")): index
        for index, row in enumerate(compile_sources)
        if isinstance(row, dict) and row.get("source_id")
    }
    physical_lines = [line for line in text.splitlines() if line.strip()]
    logical_lines: list[str] = []
    pending = ""
    for line in physical_lines:
        stripped = line.strip()
        if pending:
            stripped = pending + " " + stripped
        if stripped.endswith("\\"):
            pending = stripped[:-1].rstrip()
            continue
        logical_lines.append(stripped)
        pending = ""
    if pending:
        logical_lines.append(pending)

    assignments: list[dict[str, str]] = []
    function_signatures: list[str] = []
    commands: list[dict[str, Any]] = []
    include_directories: list[str] = []
    include_indices: dict[str, int] = {}
    for line in logical_lines:
        assignment = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$", line)
        if assignment:
            name, expression = assignment.groups()
            if name in {
                "vlogan_opts",
                "vhdlan_opts",
                "vcs_elab_opts",
                "vcs_sim_opts",
                "design_libs",
                "sim_lib_dir",
            }:
                assignments.append({"name": name, "expression": expression})
            continue
        signature = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\(\)$", line)
        if signature:
            function_signatures.append(signature.group(1))
            continue
        command_line = re.split(
            r"\s+(?:\|\||&&|\|&|\||;)(?:\s+|$)",
            line,
            maxsplit=1,
        )[0]
        command_line = re.sub(
            r"(?:^|\s)(?:\d+)?(?:>>?|<<?|>&|<&)\S*",
            "",
            command_line,
        ).strip()
        command_match = re.search(
            r"(?:^|\s)(vlogan|vhdlan|vcs|\./[^\s]+)(?:\s|$)",
            command_line,
        )
        if not command_match:
            continue
        tool = command_match.group(1)
        source_ids = re.findall(r"@source:([^\s\"']+)", command_line)
        source_indices = [source_rows[source_id] for source_id in source_ids if source_id in source_rows]
        skeleton = re.sub(
            r"[\"']?@source:[^\s\"']+[\"']?",
            "@source_rows",
            command_line,
        )

        def replace_include(match: re.Match[str]) -> str:
            value = match.group(1) or match.group(2) or ""
            if value not in include_indices:
                include_indices[value] = len(include_directories)
                include_directories.append(value)
            return f"@include:{include_indices[value]}"

        skeleton = re.sub(
            r"\+incdir\+\"([^\"]+)\"|\+incdir\+([^\s]+)",
            replace_include,
            skeleton,
        )
        skeleton = re.sub(r"(?:\s+@source_rows)+", " @source_rows", skeleton)
        skeleton = re.sub(r"\s+", " ", skeleton).strip()
        row: dict[str, Any] = {"tool": tool, "command_skeleton": skeleton}
        if source_ids:
            if len(source_indices) != len(source_ids):
                row["unresolved_source_ids"] = [
                    source_id for source_id in source_ids if source_id not in source_rows
                ]
            row["source_row_ranges"] = _contiguous_index_ranges(source_indices)
            row["source_count"] = len(source_ids)
        commands.append(row)
    return {
        "encoding": "spatialaccagent.vcs_export_semantic_ast.v1",
        "assignments": _lossless_columnar_rows(assignments),
        "function_signatures": function_signatures,
        "include_directories": _encoded_column(include_directories),
        "commands": _lossless_columnar_rows(commands),
        "compile_source_view": compile_source_view or _projection_ref("compile_sources"),
        "policy": {
            "source_row_ranges_are_inclusive_and_follow_compile_source_order": True,
            "comments_help_text_error_text_and_library_setup_boilerplate_omitted": True,
            "tool_options_include_paths_source_groups_elaboration_and_simulation_preserved": True,
        },
    }


def _compact_export_contexts(contexts: Any, compile_sources: Any) -> list[dict[str, Any]]:
    rows = contexts if isinstance(contexts, list) else []
    aliases = sorted(
        (
            (str(row.get("remote_path")), f"@source:{row.get('source_id')}")
            for row in (compile_sources if isinstance(compile_sources, list) else [])
            if isinstance(row, dict) and row.get("remote_path") and row.get("source_id")
        ),
        key=lambda item: len(item[0]),
        reverse=True,
    )
    result: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        original = str(row.get("text") or "")
        text = original
        for path, alias in aliases:
            text = text.replace(path, alias)
        base = {
            "remote_path": row.get("remote_path"),
            "sha256": row.get("sha256"),
            "original_text_chars": len(original),
            "original_text_sha256": _hash_text(original),
        }
        if len(text.encode("utf-8")) <= 4096:
            base["command_text"] = text
            base["command_text_encoding"] = "complete_text"
        else:
            base["semantic_ast"] = _vcs_export_semantic_ast(
                text,
                [row for row in compile_sources if isinstance(row, dict)],
            )
            base["command_text_encoding"] = (
                "semantic_ast; @source row ranges and @include indexes expand through named tables"
            )
        result.append(base)
    return result


def expanded_vcs_command_rewrite_authority(
    sample_compile_authority: dict[str, Any],
    external_fixture: dict[str, Any],
    manifest: dict[str, Any],
    certified_kernel_source_ids: list[str],
    current_generated_source_ids: list[str],
    *,
    framework_command_env: dict[str, str] | None = None,
    compiler_timescale: str | None = None,
) -> dict[str, Any]:
    """Expand hash-bound Vivado command boundaries into manifest source groups."""

    plan = (
        manifest.get("board_simulation_preflight_plan", {})
        if isinstance(manifest.get("board_simulation_preflight_plan"), dict)
        else {}
    )
    validation_mode = str(plan.get("validation_mode") or "exact_sample_physical_ddr")
    compute_slot_axi_mode = validation_mode == "compute_slot_axi"
    replacement_rows = (
        plan.get("source_replacements", [])
        if isinstance(plan.get("source_replacements"), list)
        else []
    )
    replacement_ids = {
        str(row.get("replaced_source_id") or row.get("replace_source_id") or ""):
        str(row.get("generated_source_id") or "")
        for row in replacement_rows
        if isinstance(row, dict)
        and str(row.get("replaced_source_id") or row.get("replace_source_id") or "")
        and str(row.get("generated_source_id") or "")
    }
    sample_sources = [
        row
        for row in sample_compile_authority.get("compile_sources", [])
        if isinstance(row, dict) and row.get("source_id")
    ]
    sample_source_ids = [str(row["source_id"]) for row in sample_sources]
    sample_groups: list[dict[str, Any]] = []
    sample_include_directories: list[str] = []
    sample_assignments: list[dict[str, Any]] = []
    elaboration_templates: list[dict[str, Any]] = []
    sample_authority_refs: list[str] = []
    for context in _compact_export_contexts(
        sample_compile_authority.get("export_contexts", []),
        sample_sources,
    ):
        ast = context.get("semantic_ast", {})
        if (not isinstance(ast, dict) or not ast.get("encoding")) and context.get(
            "command_text"
        ):
            ast = _vcs_export_semantic_ast(
                str(context.get("command_text") or ""), sample_sources
            )
        if not isinstance(ast, dict) or not ast.get("encoding"):
            continue
        include_directories = _decode_encoded_column(ast.get("include_directories", {}))
        if include_directories and not sample_include_directories:
            sample_include_directories = [str(value) for value in include_directories]
        if not sample_assignments:
            sample_assignments = _decode_lossless_columnar_rows(
                ast.get("assignments", {})
            )
        authority_ref = str(context.get("sha256") or "")
        if authority_ref and authority_ref not in sample_authority_refs:
            sample_authority_refs.append(authority_ref)
        for command in _decode_lossless_columnar_rows(ast.get("commands", {})):
            if not isinstance(command, dict):
                continue
            ranges = command.get("source_row_ranges")
            ranges = ranges if isinstance(ranges, list) else []
            source_ids = [
                sample_source_ids[index]
                for first, last in ranges
                if isinstance(first, int) and isinstance(last, int)
                for index in range(first, last + 1)
                if 0 <= index < len(sample_source_ids)
            ]
            transformed_ids = [replacement_ids.get(value, value) for value in source_ids]
            if transformed_ids:
                sample_groups.append(
                    {
                        "group_index": len(sample_groups),
                        "driver": command.get("tool"),
                        "command_skeleton": command.get("command_skeleton"),
                        "source_ids": transformed_ids,
                        "sample_include_directory_indexes": list(
                            range(len(sample_include_directories))
                        )
                        if "@include:" in str(command.get("command_skeleton") or "")
                        else [],
                        "authority_refs": [authority_ref] if authority_ref else [],
                    }
                )
            elif command.get("tool") == "vcs" and "vcs " in str(
                command.get("command_skeleton") or ""
            ):
                elaboration_templates.append(
                    {
                        "command_skeleton": command.get("command_skeleton"),
                        "authority_refs": [authority_ref] if authority_ref else [],
                    }
                )

    # Functional board repair is performed at the exact compute-slot AXI
    # boundary. Vivado's full wrapper/MIG closure remains identity evidence for
    # later implementation, but it is not part of this functional VCS compile.
    if compute_slot_axi_mode:
        sample_groups = []

    fixture_compile = (
        external_fixture.get("compile_authority", {})
        if isinstance(external_fixture.get("compile_authority"), dict)
        else {}
    )
    selected_component_ids = {
        str(value)
        for value in (
            plan.get("external_simulation_fixture", {}).get("selected_source_ids", [])
            if isinstance(plan.get("external_simulation_fixture"), dict)
            else []
        )
        if str(value)
    }
    global_fixture_ids = {
        str(row.get("source_id"))
        for row in fixture_compile.get("hdl_export_artifacts", [])
        if isinstance(row, dict)
        and row.get("source_id")
        and row.get("invoked_by_compile") is not False
    }
    if compute_slot_axi_mode:
        selected_component_ids = set()
        global_fixture_ids = set()
    selected_fixture_ids = selected_component_ids | global_fixture_ids
    context_hash_by_artifact = {
        str(row.get("artifact_id")): str(row.get("sha256"))
        for row in fixture_compile.get("export_contexts", [])
        if isinstance(row, dict) and row.get("artifact_id") and row.get("sha256")
    }
    fixture_groups: list[dict[str, Any]] = []
    emitted_fixture_ids: set[str] = set()
    for invocation in fixture_compile.get("compile_invocations", []):
        if not isinstance(invocation, dict):
            continue
        source_ids = [
            str(value)
            for value in invocation.get("input_source_ids", [])
            if str(value) in selected_fixture_ids and str(value) not in emitted_fixture_ids
        ]
        if not source_ids:
            continue
        emitted_fixture_ids.update(source_ids)
        projected = _fixture_invocation_projection(invocation, {})
        authority_ref = context_hash_by_artifact.get(
            str(invocation.get("script_artifact_id") or ""), ""
        )
        fixture_groups.append(
            {
                "group_index": len(fixture_groups),
                "driver": invocation.get("driver"),
                "work_library": invocation.get("work_library"),
                "compiler_options": projected.get("compiler_options", []),
                "include_directory_ids": [
                    str(value)
                    for value in invocation.get("include_directory_ids", [])
                    if str(value)
                ],
                "source_ids": source_ids,
                "authority_refs": [authority_ref] if authority_ref else [],
            }
        )
    ordered_fixture_ids = [
        value for group in fixture_groups for value in group["source_ids"]
    ]

    replacement_targets = (
        set() if compute_slot_axi_mode else set(replacement_ids.values())
    )
    additional_generated_ids = [
        str(value)
        for value in [*certified_kernel_source_ids, *current_generated_source_ids]
        if str(value) and str(value) not in replacement_targets
    ]
    ordered_source_ids = [
        *ordered_fixture_ids,
        *[value for group in sample_groups for value in group["source_ids"]],
        *additional_generated_ids,
    ]
    assignment_tokens: dict[str, list[str]] = {}
    for row in sample_assignments:
        if not isinstance(row, dict) or not row.get("name"):
            continue
        tokens = shlex.split(str(row.get("expression") or ""))
        # Vivado exports some option bundles as one quoted shell-assignment value.
        # The manifest runner consumes argv directly, so preserve the shell's
        # second word-splitting step without carrying a shell into execution.
        if len(tokens) == 1 and any(character.isspace() for character in tokens[0]):
            tokens = shlex.split(tokens[0])
        assignment_tokens[str(row.get("name"))] = tokens
    default_cwd = FRAMEWORK_VCS_COMMAND_CWD
    default_env = (
        copy.deepcopy(framework_command_env)
        if isinstance(framework_command_env, dict)
        else {}
    )
    compiler_timescale_option = str(compiler_timescale or "").strip()
    if re.fullmatch(
        r"-timescale=[1-9][0-9]*(?:s|ms|us|ns|ps|fs)/[1-9][0-9]*(?:s|ms|us|ns|ps|fs)",
        compiler_timescale_option,
    ) is None:
        compiler_timescale_option = ""

    def sample_manifest_argv(group: dict[str, Any]) -> list[Any]:
        tokens = shlex.split(str(group.get("command_skeleton") or ""))
        driver = str(group.get("driver") or "")
        if tokens and tokens[0] == driver:
            tokens = tokens[1:]
        result: list[Any] = []
        for token in tokens:
            if token.startswith("$") and token[1:] in assignment_tokens:
                result.extend(assignment_tokens[token[1:]])
            elif token.startswith("@include:"):
                try:
                    index = int(token.split(":", 1)[1])
                except ValueError:
                    continue
                if 0 <= index < len(sample_include_directories):
                    result.append(f"+incdir+{sample_include_directories[index]}")
            elif token == "@source_rows":
                result.extend(
                    {"source_id": source_id}
                    for source_id in group.get("source_ids", [])
                )
            else:
                result.append(token)
        return result

    ordered_command_templates: list[dict[str, Any]] = []
    for group in fixture_groups:
        source_ids = [str(value) for value in group.get("source_ids", [])]
        ordered_command_templates.append(
            {
                "order": len(ordered_command_templates),
                "phase": "compile",
                "tool_role": "functional_verification",
                "executable": str(group.get("driver") or ""),
                "argv": [
                    "-work",
                    str(group.get("work_library") or ""),
                    *copy.deepcopy(group.get("compiler_options", [])),
                    *(
                        {"include_dir_id": str(value)}
                        for value in group.get("include_directory_ids", [])
                    ),
                    *({"source_id": value} for value in source_ids),
                ],
                "source_ids": source_ids,
                "cwd": default_cwd,
                "env": copy.deepcopy(default_env),
                "shell": False,
                "authority_refs": copy.deepcopy(group.get("authority_refs", [])),
            }
        )
    for group in sample_groups:
        source_ids = [str(value) for value in group.get("source_ids", [])]
        ordered_command_templates.append(
            {
                "order": len(ordered_command_templates),
                "phase": "compile",
                "tool_role": "functional_verification",
                "executable": str(group.get("driver") or ""),
                "argv": sample_manifest_argv(group),
                "source_ids": source_ids,
                "cwd": default_cwd,
                "env": copy.deepcopy(default_env),
                "shell": False,
                "authority_refs": copy.deepcopy(group.get("authority_refs", [])),
            }
        )
    additional_authority_refs = sorted(
        {
            str(ref)
            for group in sample_groups
            for ref in group.get("authority_refs", [])
            if str(ref)
        }
        | {str(ref) for ref in sample_authority_refs if str(ref)}
    )[:1]
    if additional_generated_ids:
        ordered_command_templates.append(
            {
                "order": len(ordered_command_templates),
                "phase": "compile",
                "tool_role": "functional_verification",
                "executable": "vlogan",
                "argv": [
                    "-work",
                    "xil_defaultlib",
                    "-full64",
                    "-sverilog",
                    *([compiler_timescale_option] if compiler_timescale_option else []),
                    "+incdir+../sources",
                    *({"source_id": value} for value in additional_generated_ids),
                ],
                "source_ids": additional_generated_ids,
                "cwd": default_cwd,
                "env": copy.deepcopy(default_env),
                "shell": False,
                "authority_refs": additional_authority_refs,
            }
        )
    top_module = str(
        plan.get("top_module")
        or (
            plan.get("testbench", {}).get("top_module")
            if isinstance(plan.get("testbench"), dict)
            else ""
        )
        or ""
    )
    output = FRAMEWORK_VCS_OUTPUT
    all_authority_refs = sorted(
        {
            str(ref)
            for command in ordered_command_templates
            for ref in command.get("authority_refs", [])
            if str(ref)
        }
    )
    elaboration_argv = [
        *assignment_tokens.get("vcs_elab_opts", []),
        top_module,
        *(["xil_defaultlib.glbl"] if global_fixture_ids else []),
        "-o",
        output,
    ]
    ordered_command_templates.append(
        {
            "order": len(ordered_command_templates),
            "phase": "elaborate",
            "tool_role": "functional_verification",
            "executable": "vcs",
            "argv": elaboration_argv,
            "source_ids": [],
            "cwd": default_cwd,
            "env": copy.deepcopy(default_env),
            "shell": False,
            "authority_refs": all_authority_refs,
        }
    )
    return {
        "schema_version": "spatialaccagent.expanded_vcs_command_rewrite_authority.v1",
        "validation_mode": validation_mode,
        "sample": {
            "compiler_assignments": sample_assignments,
            "include_directories": sample_include_directories,
            "command_groups": sample_groups,
        },
        "external_fixture": {
            "command_groups": fixture_groups,
            "selected_source_ids": ordered_fixture_ids,
            "selected_component_source_ids": [
                value for value in ordered_fixture_ids if value in selected_component_ids
            ],
            "required_global_simulator_source_ids": [
                value for value in ordered_fixture_ids if value in global_fixture_ids
            ],
            "all_selected_sources_grouped_once": emitted_fixture_ids
            == selected_fixture_ids,
        },
        "additional_generated_group": {
            "driver": "vlogan",
            "work_library": "xil_defaultlib",
            "compiler_options": [
                "-full64",
                "-sverilog",
                *([compiler_timescale_option] if compiler_timescale_option else []),
                "+incdir+../sources",
            ],
            "source_ids": additional_generated_ids,
            "authority_refs": sorted(
                {
                    str(ref)
                    for group in sample_groups
                    for ref in group.get("authority_refs", [])
                    if str(ref)
                }
            )[:1],
        },
        "elaboration_templates": elaboration_templates,
        "manifest_ready_ordered_commands": ordered_command_templates,
        "ordered_source_ids": ordered_source_ids,
        "counts": {
            "sample_command_groups": len(sample_groups),
            "sample_sources_after_replacement": sum(
                len(group["source_ids"]) for group in sample_groups
            ),
            "external_fixture_command_groups": len(fixture_groups),
            "external_fixture_sources": len(emitted_fixture_ids),
            "additional_generated_sources": len(additional_generated_ids),
            "total_sources": len(ordered_source_ids),
            "unique_sources": len(set(ordered_source_ids)),
        },
        "manifest_token_contract": {
            "source_placeholder": {"source_id": "<source_ids entry>"},
            "fixture_include_placeholder": {
                "include_dir_id": "<include_directory_ids entry>"
            },
            "sample_include_placeholder": "+incdir+<include_directories entry>",
            "source_ids_must_equal_structured_argv_tokens_in_order": True,
            "shell_transport_tokens_forbidden": True,
        },
    }


def _projection_ref(view: str) -> dict[str, Any]:
    return {
        "$ref": "#/verification_capability_repair_package/exact_board_integration_repair_context/adaptive_design_inputs/shared_board_source_index",
        "view": view,
    }


def _apply_shared_board_source_index(
    identity_projection: dict[str, Any],
    compile_projection: dict[str, Any],
    identity: dict[str, Any],
    compile_authority: dict[str, Any],
    shared_index: dict[str, Any],
) -> None:
    identity_value = identity_projection.get("value")
    compile_value = compile_projection.get("value")
    if not isinstance(identity_value, dict):
        return
    closure = identity_value.get("selected_simulation_source_closure", {})
    original_closure = identity.get("selected_simulation_source_closure", {})
    if isinstance(closure, dict) and isinstance(original_closure, dict):
        closure["source_files"] = _projection_ref("identity_source_files")
        source_ids = [
            str(row.get("source_id"))
            for row in original_closure.get("source_files", [])
            if isinstance(row, dict) and row.get("source_id")
        ]
        if original_closure.get("root_source_ids") == source_ids:
            closure["root_source_ids"] = _projection_ref("source_ids")
        if identity.get("selected_simulation_source_roots") == source_ids:
            identity_value["selected_simulation_source_roots"] = _projection_ref("source_ids")
        validation = identity_value.get("identity_contract_validation", {})
        for check in validation.get("checks", []) if isinstance(validation, dict) else []:
            if isinstance(check, dict) and check.get("root_source_ids") == source_ids:
                check["root_source_ids"] = _projection_ref("source_ids")
    source_hashes = identity.get("source_hashes", [])
    identity_value["source_hashes"] = {
        "row_count": len(source_hashes) if isinstance(source_hashes, list) else 0,
        "canonical_sha256": _canonical_json_sha256(source_hashes),
        "full_rows_are_integrity_metadata_bound_by_identity_artifact_sha256": True,
    }
    compute_slot = identity_value.get("compute_slot_abi", {})
    if isinstance(compute_slot, dict) and compute_slot.get("control_abi") == identity_value.get("control_abi"):
        compute_slot["control_abi"] = {
            "$ref": "#/verification_capability_repair_package/exact_board_integration_repair_context/adaptive_design_inputs/exact_board_source_identity/value/control_abi"
        }
    replacement = compute_slot.get("replacement_boundary", {}) if isinstance(compute_slot, dict) else {}
    if isinstance(replacement, dict) and "retained_source_ids" in shared_index.get("views", {}):
        replacement["retained_source_ids"] = _projection_ref("retained_source_ids")
    if not isinstance(compile_value, dict):
        return
    compile_value["compile_sources"] = _projection_ref("compile_sources")
    compile_value["export_contexts"] = _compact_export_contexts(
        compile_authority.get("export_contexts", []), compile_authority.get("compile_sources", [])
    )


def _compact_sample_project_vcs_input_projection(
    projection: Any,
    shared_index: dict[str, Any],
) -> Any:
    if not isinstance(projection, dict):
        return compact_for_retry(projection)
    compact = copy.deepcopy(projection)
    source_ids = compact.get("compiler_input_source_ids")
    view = shared_index.get("views", {}).get("compiler_input_source_ids", {})
    if (
        isinstance(source_ids, list)
        and isinstance(view, dict)
        and view.get("canonical_sha256") == _canonical_json_sha256(source_ids)
    ):
        compact["compiler_input_source_ids"] = {
            **_projection_ref("compiler_input_source_ids"),
            "row_count": len(source_ids),
            "canonical_sha256": _canonical_json_sha256(source_ids),
        }
    runtime_auxiliary = compact.get("runtime_auxiliary_files")
    if isinstance(runtime_auxiliary, list) and all(
        isinstance(row, dict) and row.get("source_id") for row in runtime_auxiliary
    ):
        runtime_source_ids = [str(row["source_id"]) for row in runtime_auxiliary]
        indexed_source_ids = {
            str(value)
            for value in shared_index.get("views", {}).get("source_ids", {}).get(
                "values", []
            )
            if str(value)
        }
        if not indexed_source_ids:
            try:
                indexed_source_ids = {
                    str(value)
                    for value in _decode_encoded_column(
                        shared_index.get("columns", {}).get("source_id", {})
                    )
                    if str(value)
                }
            except (TypeError, ValueError):
                indexed_source_ids = set()
        if set(runtime_source_ids).issubset(indexed_source_ids):
            compact["runtime_auxiliary_files"] = {
                **_projection_ref("identity_source_files"),
                "source_ids": _encoded_column(runtime_source_ids),
                "selected_fields": [
                    "source_id",
                    "language",
                    "library",
                    "role",
                    "closure_role",
                ],
                "row_count": len(runtime_auxiliary),
                "canonical_sha256": _canonical_json_sha256(runtime_auxiliary),
                "policy": (
                    "the same hash-bound sample sources are already present in the shared "
                    "board source index; this projection selects only their runtime/staging view"
                ),
            }
    return compact


def _compact_sample_source_rewrite_authority(
    rows: Any,
    shared_index: Any,
) -> Any:
    records = [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []
    if not isinstance(rows, list) or len(records) != len(rows):
        return _columnarize_record_lists(rows)

    classifications: dict[str, list[str]] = {}
    dispositions: dict[str, list[str]] = {}
    for row in records:
        source_id = str(row.get("source_id") or "")
        if not source_id:
            return _columnarize_record_lists(rows)
        classifications.setdefault(str(row.get("classification") or ""), []).append(
            source_id
        )
        dispositions.setdefault(
            str(row.get("transformed_disposition") or ""), []
        ).append(source_id)

    compiler_ids = classifications.get("compiler_input", [])
    compiler_view = (
        shared_index.get("views", {}).get("compiler_input_source_ids", {})
        if isinstance(shared_index, dict)
        else {}
    )

    def source_id_projection(values: list[str], *, compiler_view_ok: bool = False) -> Any:
        if (
            compiler_view_ok
            and isinstance(compiler_view, dict)
            and compiler_view.get("row_count") == len(values)
            and compiler_view.get("canonical_sha256") == _canonical_json_sha256(values)
        ):
            return {
                **_projection_ref("compiler_input_source_ids"),
                "row_count": len(values),
                "canonical_sha256": _canonical_json_sha256(values),
            }
        return {
            "encoding": "spatialaccagent.source_id_selection.v1",
            "source_ids": _encoded_column(values),
            "row_count": len(values),
            "canonical_sha256": _canonical_json_sha256(values),
        }

    classification_views = {
        classification: source_id_projection(
            values,
            compiler_view_ok=classification == "compiler_input",
        )
        for classification, values in sorted(classifications.items())
    }
    disposition_views: dict[str, Any] = {}
    replaced_ids = dispositions.get("replace", [])
    for disposition, values in sorted(dispositions.items()):
        if disposition == "preserve" and compiler_ids:
            expected = [value for value in compiler_ids if value not in set(replaced_ids)]
            if values == expected:
                disposition_views[disposition] = {
                    **_projection_ref("compiler_input_source_ids"),
                    "exclude_source_ids": _encoded_column(replaced_ids),
                    "row_count": len(values),
                    "canonical_sha256": _canonical_json_sha256(values),
                }
                continue
        disposition_views[disposition] = source_id_projection(values)

    return {
        "encoding": "spatialaccagent.sample_source_rewrite_join.v1",
        "row_count": len(records),
        "canonical_sha256": _canonical_json_sha256(records),
        "source_semantic_fields": {
            **_projection_ref("identity_source_files"),
            "selected_fields": [
                "source_id",
                "compile_order",
                "language",
                "library",
                "role",
                "closure_role",
                "declared_modules",
                "dependencies",
                "file_set",
                "source_set",
                "used_in",
                "hashes_match",
                "is_global_include",
            ],
        },
        "classification_views": classification_views,
        "transformed_disposition_views": disposition_views,
        "join_key": "source_id",
        "policy": (
            "join the classification and disposition views to the shared semantic source "
            "index by source_id; per-source path and digest transport metadata remains bound "
            "by the immutable identity/compile artifacts and is materialized by the framework; "
            "no filename-based source reclassification is permitted"
        ),
    }


def _compact_external_fixture_source_rewrite_authority(rows: Any) -> Any:
    records = [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []
    if not isinstance(rows, list) or len(records) != len(rows):
        return _columnarize_record_lists(rows)
    selection_roles = [str(row.get("selection_role") or "") for row in records]
    return {
        "encoding": "spatialaccagent.external_fixture_source_rewrite_view.v1",
        "row_count": len(records),
        "canonical_sha256": _canonical_json_sha256(records),
        "source_rows": {
            "$ref": (
                "#/verification_capability_repair_package/exact_board_integration_repair_context/"
                "adaptive_design_inputs/external_simulation_fixture/value/compile_authority/"
                "compile_sources"
            ),
            "selected_fields": [
                "declared_design_units",
                "file_type",
                "invoked_by_compile",
                "language",
                "library",
                "role",
                "source_id",
            ],
        },
        "selection_roles": _encoded_column(selection_roles),
        "selection_roles_canonical_sha256": _canonical_json_sha256(selection_roles),
        "command_semantics": {
            "$ref": (
                "#/verification_capability_repair_package/repair_source_bundle/"
                "editable_contract/board_manifest_rewrite_authority/expanded_source_authority/"
                "vcs_command_rewrite_authority/manifest_ready_vcs_compile_plan"
            )
        },
        "policy": (
            "rows align exactly with the bound fixture compile-source table; selection roles are the "
            "only additional generation semantics. Per-source host/staged paths and digests remain "
            "framework-owned in the immutable fixture artifact, and exact argv ordering is literal in the VCS plan"
        ),
    }


def _compact_compile_source_coverage_authority(
    value: Any,
    *,
    external_fixture_source_authority_available: bool,
) -> Any:
    if not isinstance(value, dict):
        return compact_for_retry(value)
    compact = {
        key: copy.deepcopy(item)
        for key, item in value.items()
        if not isinstance(item, list)
    }
    replaced_ids = [
        str(item)
        for item in value.get("replaced_sample_source_ids", [])
        if str(item)
    ]
    reference_contracts = {
        "certified_kernel_source_ids": {
            "$ref": (
                "#/verification_capability_repair_package/repair_source_bundle/editable_contract/"
                "board_manifest_rewrite_authority/expanded_source_authority/certified_kernel_sources"
            ),
            "selected_field": "source_id",
        },
        "preserved_sample_compile_source_ids": {
            **_projection_ref("compiler_input_source_ids"),
            "exclude_source_ids": _encoded_column(replaced_ids),
        },
    }
    if external_fixture_source_authority_available:
        reference_contracts["available_external_fixture_compile_source_ids"] = {
            "$ref": (
                "#/verification_capability_repair_package/exact_board_integration_repair_context/"
                "adaptive_design_inputs/external_simulation_fixture/value/compile_authority/"
                "compile_sources"
            ),
            "selected_field": "source_id",
        }
    for key, item in value.items():
        if not isinstance(item, list):
            continue
        values = [str(entry) for entry in item]
        if key in reference_contracts and len(values) > 8:
            compact[key] = {
                **reference_contracts[key],
                "row_count": len(values),
                "canonical_sha256": _canonical_json_sha256(values),
            }
        else:
            compact[key] = copy.deepcopy(item)
    compact["compaction_policy"] = {
        "source_id_sets_are_hash_bound_views_of_the_complete_source_authorities": True,
        "small_mutation_sets_remain_literal": True,
    }
    return compact


def _compact_board_rewrite_redundancy(
    compact_bundle: dict[str, Any],
    original_bundle: dict[str, Any],
    context_projection: Any,
) -> None:
    original_editable = original_bundle.get("editable_contract", {})
    compact_editable = compact_bundle.get("editable_contract", {})
    if not isinstance(original_editable, dict) or not isinstance(compact_editable, dict):
        return
    original_rewrite = original_editable.get("board_manifest_rewrite_authority")
    compact_rewrite = compact_editable.get("board_manifest_rewrite_authority")
    if not isinstance(original_rewrite, dict) or not isinstance(compact_rewrite, dict):
        return
    original_expanded = original_rewrite.get("expanded_source_authority")
    compact_expanded = compact_rewrite.get("expanded_source_authority")
    if not isinstance(original_expanded, dict) or not isinstance(compact_expanded, dict):
        return
    adaptive_projection = (
        context_projection.get("adaptive_design_inputs", {})
        if isinstance(context_projection, dict)
        else {}
    )
    shared_index = (
        adaptive_projection.get("shared_board_source_index", {})
        if isinstance(adaptive_projection, dict)
        else {}
    )

    original_sample_sources = original_expanded.get("sample_sources")
    if isinstance(original_sample_sources, list) and original_sample_sources and shared_index:
        compact_expanded["sample_sources"] = _compact_sample_source_rewrite_authority(
            original_sample_sources, shared_index
        )
    original_fixture_sources = original_expanded.get("external_fixture_sources")
    external_fixture_projection = (
        adaptive_projection.get("external_simulation_fixture", {})
        if isinstance(adaptive_projection, dict)
        else {}
    )
    external_fixture_value = _bound_artifact_value(external_fixture_projection)
    external_fixture_compile_authority = (
        external_fixture_value.get("compile_authority", {})
        if isinstance(external_fixture_value, dict)
        else {}
    )
    external_fixture_source_authority_available = isinstance(
        external_fixture_compile_authority.get("compile_sources"),
        (dict, list),
    )
    if (
        isinstance(original_fixture_sources, list)
        and original_fixture_sources
        and external_fixture_projection
    ):
        compact_expanded["external_fixture_sources"] = (
            _compact_external_fixture_source_rewrite_authority(
                original_fixture_sources
            )
        )
    original_coverage = original_rewrite.get("compile_source_coverage_authority")
    if isinstance(original_coverage, dict) and original_coverage:
        compact_rewrite["compile_source_coverage_authority"] = (
            _compact_compile_source_coverage_authority(
                original_coverage,
                external_fixture_source_authority_available=(
                    external_fixture_source_authority_available
                ),
            )
        )

    sample_projection = (
        adaptive_projection.get("sample_project_vcs_input_projection", {})
        if isinstance(adaptive_projection, dict)
        else {}
    )
    runtime_projection = (
        sample_projection.get("runtime_auxiliary_files")
        if isinstance(sample_projection, dict)
        else None
    )
    sample_authority = compact_expanded.get("sample_sources")
    stage_only = (
        sample_authority.get("transformed_disposition_views", {}).get("stage_only")
        if isinstance(sample_authority, dict)
        else None
    )
    if isinstance(runtime_projection, dict) and isinstance(stage_only, dict):
        encoded_runtime_ids = runtime_projection.get("source_ids")
        try:
            runtime_ids = (
                [str(value) for value in _decode_encoded_column(encoded_runtime_ids)]
                if isinstance(encoded_runtime_ids, dict)
                else []
            )
        except (TypeError, ValueError):
            runtime_ids = []
        selection_root = {
            "verification_capability_repair_package": {
                "exact_board_integration_repair_context": context_projection,
            }
        }
        stage_only_ids = _compact_source_id_selection(selection_root, stage_only)
        if runtime_ids and runtime_ids == stage_only_ids:
            sample_projection["runtime_auxiliary_files"] = {
                "$ref": (
                    "#/verification_capability_repair_package/repair_source_bundle/"
                    "editable_contract/board_manifest_rewrite_authority/"
                    "expanded_source_authority/sample_sources/"
                    "transformed_disposition_views/stage_only"
                ),
                "row_count": len(runtime_ids),
                "canonical_sha256": _canonical_json_sha256(runtime_ids),
                "source_rows_canonical_sha256": runtime_projection.get(
                    "canonical_sha256"
                ),
                "selected_fields": ["source_id"],
                "policy": (
                    "complete staging identities are framework-owned and bound by the sample "
                    "identity/compile artifacts; this view is only the exact source-id selection"
                ),
            }

    tensor_contract = original_rewrite.get("complete_transformer_block_tensor_hashes")
    compact_tensor_contract = compact_rewrite.get(
        "complete_transformer_block_tensor_hashes"
    )
    if isinstance(tensor_contract, dict) and isinstance(compact_tensor_contract, dict):
        tensor_hashes = tensor_contract.get("hashes")
        target_field = str(tensor_contract.get("target_field") or "")
        if isinstance(tensor_hashes, list) and target_field:
            for index, document in enumerate(compact_bundle.get("documents", [])):
                if not isinstance(document, dict):
                    continue
                manifest = document.get("json_content")
                if not isinstance(manifest, dict) or manifest.get(target_field) != tensor_hashes:
                    continue
                compact_tensor_contract["hashes"] = {
                    "$ref": (
                        "#/verification_capability_repair_package/repair_source_bundle/"
                        f"documents/{index}/json_content/{target_field}"
                    ),
                    "row_count": len(tensor_hashes),
                    "canonical_sha256": _canonical_json_sha256(tensor_hashes),
                    "literal_values_are_preserved_in_the_editable_manifest": True,
                }
                break

    external_documents = compact_bundle.get(
        "documents_omitted_as_external_fixture_compile_source_index"
    )
    if (
        isinstance(external_documents, dict)
        and external_fixture_source_authority_available
    ):
        external_documents["$ref"] = (
            "#/verification_capability_repair_package/exact_board_integration_repair_context/"
            "adaptive_design_inputs/external_simulation_fixture/value/compile_authority/"
            "compile_sources"
        )
    sample_documents = compact_bundle.get(
        "documents_omitted_as_shared_board_source_index"
    )
    if isinstance(sample_documents, dict):
        sample_documents["$ref"] = (
            "#/verification_capability_repair_package/exact_board_integration_repair_context/"
            "adaptive_design_inputs/shared_board_source_index"
        )
        sample_documents["view"] = "identity_source_files"

    compact_rewrite["redundancy_elimination_contract"] = {
        "editable_manifest_and_manifest_ready_vcs_plan_remain_literal": True,
        "sample_sources_join_shared_board_source_index_by_source_id": True,
        "external_fixture_identity_and_compile_semantics_are_supplied_once": True,
        "compile_coverage_sets_are_hash_bound_source_views": True,
        "complete_tensor_hash_values_remain_literal_in_the_editable_manifest": True,
    }


def _deduplicate_compact_projection(value: Any) -> Any:
    seen: dict[str, str] = {}

    def visit(item: Any, path: str, *, preserve_literal: bool = False) -> Any:
        if preserve_literal:
            return copy.deepcopy(item)
        if isinstance(item, (dict, list)):
            encoded = _canonical_json(item)
            if len(encoded.encode("utf-8")) >= 1024:
                digest = _hash_text(encoded)
                previous = seen.get(digest)
                if previous is not None:
                    return {"$ref": previous, "value_sha256": digest}
                seen[digest] = path
        if isinstance(item, dict):
            return {
                str(key): visit(
                    child,
                    path + "/" + str(key).replace("~", "~0").replace("/", "~1"),
                    preserve_literal=str(key)
                    in {"json_content", "manifest_ready_vcs_compile_plan"},
                )
                for key, child in item.items()
            }
        if isinstance(item, list):
            return [visit(child, f"{path}/{index}") for index, child in enumerate(item)]
        return item

    return visit(value, "#")


def _safe_len(value: Any) -> int:
    try:
        return len(value)
    except TypeError:
        return 0


def _first_items(value: Any, count: int = 8) -> list[Any]:
    if not isinstance(value, list):
        return []
    return value[:count]


def _module_headers(text: str, limit: int = 4, max_chars: int = 4000) -> list[dict[str, Any]]:
    headers: list[dict[str, Any]] = []
    for match in re.finditer(r"(?m)^\s*module\s+([A-Za-z_][A-Za-z0-9_$]*)\b", text):
        if len(headers) >= limit:
            break
        semi = text.find(";", match.end())
        stop = semi + 1 if semi != -1 else min(len(text), match.start() + max_chars)
        snippet = text[match.start() : min(stop, match.start() + max_chars)]
        headers.append({"module": match.group(1), "header": snippet})
    return headers


def _interface_headers(
    text: str, limit: int = 4, max_chars: int = 4000
) -> list[dict[str, Any]]:
    headers: list[dict[str, Any]] = []
    for match in re.finditer(
        r"(?m)^\s*interface\s+([A-Za-z_][A-Za-z0-9_$]*)\b", text
    ):
        if len(headers) >= limit:
            break
        semi = text.find(";", match.end())
        stop = semi + 1 if semi != -1 else min(len(text), match.start() + max_chars)
        headers.append(
            {
                "interface": match.group(1),
                "header": text[match.start() : min(stop, match.start() + max_chars)],
            }
        )
    return headers


def _json_document_projection(parsed: dict[str, Any], max_items: int = 16) -> dict[str, Any]:
    schema = str(parsed.get("schema_version") or "")
    result: dict[str, Any] = {}
    for key in (
            "schema_version",
            "status",
            "summary",
            "accelerator_scope",
            "source",
            "simulation_top",
            "top_module",
            "wrapper_top_module",
            "target_layer_count",
            "tensor_count",
            "per_layer_tensor_count",
            "source_checkpoint_sha256",
            "model_id",
            "revision",
    ):
        if key in parsed:
            result[key] = _bounded_projection_value(parsed.get(key))
    if schema.startswith("spatialaccagent.board_source_identity") or {
        "compute_slot_abi",
        "timing_contract",
        "axi_interfaces",
    }.issubset(parsed.keys()):
        closure = parsed.get("selected_simulation_source_closure", {})
        slim_closure: dict[str, Any] = {}
        if isinstance(closure, dict):
            slim_closure = {
                key: closure.get(key)
                for key in (
                    "closure_sha256",
                    "root_source_ids",
                    "recursive_dependency_scan_complete",
                    "duplicate_module_definitions",
                    "external_library_dependencies",
                    "unresolved_dependencies",
                    "dependency_provenance",
                )
                if key in closure
            }
            rows = closure.get("source_files", [])
            source_files = [
                {
                    key: row.get(key)
                    for key in (
                        "source_id",
                        "compile_order",
                        "path",
                        "local_path",
                        "language",
                        "library",
                        "role",
                        "sha256",
                        "modules",
                        "module_names",
                        "replaced",
                    )
                    if isinstance(row, dict) and key in row
                }
                for row in (rows if isinstance(rows, list) else [])
                if isinstance(row, dict)
            ]
            slim_closure["source_files"] = _columnar_projection(source_files)
        result.update(
            {
                "exact_user_sample_wrapper": parsed.get("exact_user_sample_wrapper"),
                "identity_contract_validation": parsed.get("identity_contract_validation"),
                "compute_slot_abi_sha256": parsed.get("compute_slot_abi_sha256"),
                "timing_contract_sha256": parsed.get("timing_contract_sha256"),
                "axi_interfaces_sha256": parsed.get("axi_interfaces_sha256"),
                "selected_simulation_source_closure_sha256": parsed.get("selected_simulation_source_closure_sha256"),
                "discovery_selected_source_ids": parsed.get("discovery_selected_source_ids", []),
                "compute_slot_abi": parsed.get("compute_slot_abi", {}),
                "timing_contract": parsed.get("timing_contract", {}),
                "axi_interfaces": parsed.get("axi_interfaces", []),
                "control_abi": parsed.get("control_abi", {}),
                "simulator_compile_authority": parsed.get("simulator_compile_authority", {}),
                "policy": parsed.get("policy", {}),
                "source_hashes": _columnar_projection(parsed.get("source_hashes", [])),
                "selected_simulation_source_roots": parsed.get("selected_simulation_source_roots", []),
                "selected_simulation_source_closure": slim_closure,
            }
        )
    elif schema.startswith("spatialaccagent.vivado_vcs_compile_authority") or "compile_sources" in parsed:
        compile_sources = parsed.get("compile_sources", [])
        export_contexts = parsed.get("export_contexts", [])
        result.update(
            {
                "vivado_version": parsed.get("vivado_version"),
                "policy": parsed.get("policy", {}),
                "vivado_facts": parsed.get("vivado_facts", {}),
                "blockers": parsed.get("blockers", []),
                "compile_source_count": len(compile_sources) if isinstance(compile_sources, list) else 0,
                "compile_sources": _columnar_projection(compile_sources),
                "export_context_count": len(export_contexts) if isinstance(export_contexts, list) else 0,
                "export_contexts": _compact_export_contexts(export_contexts, compile_sources),
            }
        )
    elif schema.startswith("spatialaccagent.transformer_block_weight_catalog") or "tensors" in parsed:
        tensors = parsed.get("tensors", [])
        result.update(
            {
                "scope_coverage_complete": parsed.get("scope_coverage_complete"),
                "layer_ids": parsed.get("layer_ids", []),
                "tensor_suffixes": parsed.get("tensor_suffixes", []),
                "semantic_adapter_sha256": parsed.get("semantic_adapter_sha256"),
                "policy": parsed.get("policy", {}),
                "tensor_count": len(tensors) if isinstance(tensors, list) else parsed.get("tensor_count"),
                "tensors": _columnar_projection([
                    {
                        key: row.get(key)
                        for key in (
                            "name",
                            "layer_index",
                            "parameter_suffix",
                            "shape",
                            "dtype",
                            "source_slice_sha256",
                            "source_file_sha256",
                            "source_byte_count",
                        )
                        if isinstance(row, dict) and key in row
                    }
                    for row in (tensors if isinstance(tensors, list) else [])
                    if isinstance(row, dict)
                ]),
            }
        )
    else:
        for key in (
            "blockers",
            "policy",
            "errors",
            "warnings",
            "required_manifest_fields",
            "standard_harness_interface",
            "single_layer_harness",
            "multilayer_harness",
            "materialization",
            "materialization_blockers",
            "numeric_comparison_policy",
            "numeric_comparison_resolution",
            "random_input",
            "real_weight_source",
            "board",
            "single_layer",
            "stage_contracts",
        ):
            if key in parsed:
                result[key] = compact_for_retry(parsed[key])
    return result


def _compact_embedded_python_consumer_contract(projection: dict[str, Any]) -> dict[str, Any]:
    compact = copy.deepcopy(projection)
    source = compact.get("source")
    contract = source.get("python_ast_contract") if isinstance(source, dict) else None
    if not isinstance(contract, dict):
        return compact
    functions = _decode_lossless_columnar_rows(contract.get("functions", {}))
    compact_functions = []
    for function in functions:
        if not isinstance(function, dict):
            continue
        compact_functions.append(
            {
                key: copy.deepcopy(function.get(key))
                for key in (
                    "name",
                    "signature",
                    "returns",
                    "contract_token_indices",
                    "omitted_prose_contract",
                )
                if key in function
            }
        )
    source["python_ast_contract"] = {
        "encoding": "spatialaccagent.python_ast_generation_surface.v1",
        "function_count": len(compact_functions),
        "contract_token_dictionary": copy.deepcopy(
            contract.get("contract_token_dictionary", [])
        ),
        "functions": _lossless_columnar_rows(compact_functions),
        "complete_consumer_contract": {
            "canonical_sha256": _canonical_json_sha256(contract),
            "call_count": len(contract.get("call_dictionary", [])),
            "contract_token_count": len(contract.get("contract_token_dictionary", [])),
            "complete_source_is_bound_by_document_sha256": True,
            "implementation_calls_are_framework_execution_not_generation_inputs": True,
            "exact_validation_field_and_status_tokens_are_generation_inputs": True,
        },
    }
    return compact


def evidence_document_projection(
    document: dict[str, Any],
    *,
    preserve_full_text: bool = False,
) -> dict[str, Any]:
    content = str(document.get("content") or "")
    path = str(document.get("path") or "")
    projection: dict[str, Any] = {
        key: document.get(key)
        for key in (
            "path",
            "source_path",
            "source_sha256",
            "sha256",
            "content_sha256",
            "bytes",
            "truncated",
            "projection",
        )
        if key in document
    }
    projection["content_chars"] = len(content)
    if content:
        projection["content_sha256"] = projection.get("content_sha256") or _hash_text(content)
    existing_json_content = document.get("json_content")
    if isinstance(existing_json_content, dict):
        projection["json_content"] = copy.deepcopy(existing_json_content)
        if document.get("content_encoding"):
            projection["content_encoding"] = copy.deepcopy(
                document["content_encoding"]
            )
        if document.get("content_preservation"):
            projection["content_preservation"] = copy.deepcopy(
                document["content_preservation"]
            )
        if isinstance(document.get("framework_materialized_json_omissions"), list):
            projection["framework_materialized_json_omissions"] = copy.deepcopy(
                document["framework_materialized_json_omissions"]
            )
        return projection
    suffix = Path(path.split("#", 1)[0]).suffix.lower()
    if content and preserve_full_text:
        if suffix in {".json"} or content.lstrip().startswith("{"):
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError:
                pass
            else:
                if isinstance(parsed, dict):
                    projection["json_content"] = parsed
                    projection["content_encoding"] = "complete_json_object_from_current_file"
                    projection["content_preservation"] = (
                        "complete JSON object is selected as exact editable authority required for generation"
                    )
                    return projection
        projection["content"] = content
        projection["content_preservation"] = (
            "complete source is selected as exact interface or certified lifecycle "
            "authority required for generation"
        )
        return projection
    if content and (suffix in {".json"} or content.lstrip().startswith("{")):
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            projection["content_head"] = content[:1200]
        else:
            if isinstance(parsed, dict):
                projection["json_projection"] = _compact_embedded_python_consumer_contract(
                    _json_document_projection(parsed)
                )
            else:
                projection["json_projection"] = {"type": type(parsed).__name__, "size": _safe_len(parsed)}
        return projection
    if suffix in {".sv", ".svh", ".v", ".vh", ".vhd", ".vhdl", ".vp", ".svp"}:
        projection["hdl_modules"] = document.get("modules") or re.findall(
            r"(?m)^\s*(?:module|interface|entity)\s+([A-Za-z_][A-Za-z0-9_$]*)\b",
            content,
        )[:16]
        projection["module_headers"] = _module_headers(content)
        projection["interface_headers"] = _interface_headers(content)
        return projection
    if suffix in {".scala", ".py", ".tcl", ".sh", ".f"}:
        projection["content_head"] = content[:2400]
        if len(content) > 4800:
            projection["content_tail"] = content[-1200:]
        return projection
    projection["content_head"] = content[:1600]
    return projection


def _framework_materialized_vcs_plan_contract(
    plan: Any,
    authority: dict[str, Any],
) -> Any:
    if not isinstance(plan, dict):
        return copy.deepcopy(plan)
    commands = plan.get("ordered_commands")
    if not isinstance(commands, list) or not commands:
        return copy.deepcopy(plan)

    def contains_ref(value: Any) -> bool:
        if isinstance(value, dict):
            return "$ref" in value or any(contains_ref(child) for child in value.values())
        if isinstance(value, list):
            return any(contains_ref(child) for child in value)
        return False

    source_ids: list[str] = []
    compile_count = 0
    elaboration: list[dict[str, Any]] = []
    valid = not contains_ref(plan)
    shell_tokens = {"|", "||", "&&", ";", ">", ">>", "<", "2>&1", "tee"}
    command_fields = {
        "order",
        "phase",
        "tool_role",
        "executable",
        "argv",
        "source_ids",
        "cwd",
        "env",
        "shell",
        "authority_refs",
    }
    tool_binding = plan.get("tool_binding")
    expected_env = (
        tool_binding.get("env", {})
        if isinstance(tool_binding, dict) and isinstance(tool_binding.get("env", {}), dict)
        else {}
    )
    for index, command in enumerate(commands):
        if (
            not isinstance(command, dict)
            or set(command) != command_fields
            or isinstance(command.get("order"), bool)
            or command.get("order") != index
        ):
            valid = False
            continue
        valid = bool(
            valid
            and command.get("tool_role")
            == (tool_binding.get("role") if isinstance(tool_binding, dict) else None)
            and command.get("cwd") == FRAMEWORK_VCS_COMMAND_CWD
            and command.get("env") == expected_env
            and command.get("shell") is False
            and isinstance(command.get("authority_refs"), list)
            and bool(command.get("authority_refs"))
            and all(
                isinstance(value, str)
                and re.fullmatch(r"[0-9a-fA-F]{64}", value)
                for value in command.get("authority_refs", [])
            )
        )
        argv = command.get("argv")
        declared_ids = command.get("source_ids")
        if not isinstance(argv, list) or not isinstance(declared_ids, list):
            valid = False
            continue
        token_ids = [
            str(token.get("source_id") or "")
            for token in argv
            if isinstance(token, dict) and set(token) == {"source_id"}
        ]
        if token_ids != [str(value) for value in declared_ids]:
            valid = False
        executable = str(command.get("executable") or "")
        literal_tokens = [token for token in argv if isinstance(token, str)]
        if (
            not executable
            or executable in literal_tokens[:1]
            or any(token in shell_tokens for token in literal_tokens)
            or any(
                token.startswith("-") and any(char.isspace() for char in token)
                for token in literal_tokens
            )
        ):
            valid = False
        phase = str(command.get("phase") or "")
        if phase == "compile":
            compile_count += 1
            source_ids.extend(token_ids)
            valid = bool(
                valid
                and token_ids
                and literal_tokens.count("-work") == 1
                and not any(source_id in literal_tokens for source_id in token_ids)
            )
        elif phase == "elaborate":
            elaboration.append(command)
            valid = valid and not token_ids
        else:
            valid = False
    expected_count = authority.get("counts", {}).get("total_sources")
    expected_source_ids = authority.get("ordered_source_ids")
    expected_source_ids = (
        [str(value) for value in expected_source_ids]
        if isinstance(expected_source_ids, list)
        else None
    )
    required_globals = [
        str(value)
        for value in authority.get("external_fixture", {}).get(
            "required_global_simulator_source_ids", []
        )
        if str(value)
    ]
    compile_authority = plan.get("compile_authority")
    valid = bool(
        valid
        and plan.get("schema_version") == "spatialaccagent.vcs_compile_plan.v1"
        and plan.get("status") == "ready"
        and isinstance(plan.get("tool_binding"), dict)
        and plan.get("tool_binding")
        and isinstance(compile_authority, dict)
        and all(
            compile_authority.get(field)
            for field in (
                "vivado_facts_path",
                "vivado_facts_sha256",
                "simulator_export_context_sha256s",
                "external_fixture_contract_sha256",
                "external_fixture_export_context_sha256s",
            )
        )
        and len(source_ids) == len(set(source_ids))
        and (not isinstance(expected_count, int) or len(source_ids) == expected_count)
        and (expected_source_ids is not None and source_ids == expected_source_ids)
        and len(elaboration) == 1
        and commands[-1] is elaboration[0]
        and str(plan.get("top_module") or "") in elaboration[0].get("argv", [])
        and str(plan.get("output") or "") in elaboration[0].get("argv", [])
        and plan.get("output") == FRAMEWORK_VCS_OUTPUT
        and set(required_globals).issubset(source_ids)
        and (
            not required_globals
            or "xil_defaultlib.glbl" in elaboration[0].get("argv", [])
        )
    )
    if not valid:
        return copy.deepcopy(plan)
    return {
        "schema_version": "spatialaccagent.framework_vcs_plan_binding.v1",
        "status": "ready",
        "representation": "framework_materialization_certificate",
        "framework_materialized_by": "apply_agent_file_edits.bind_framework_vcs_compile_plan",
        "source_authority": "board_manifest_lossless_rewrite_authority",
        "source_plan_canonical_sha256": _canonical_json_sha256(plan),
        "ordered_command_count": len(commands),
        "compile_command_count": compile_count,
        "compile_source_count": len(source_ids),
        "compile_source_ids_canonical_sha256": _canonical_json_sha256(source_ids),
        "ordered_source_ids_authority_canonical_sha256": _canonical_json_sha256(
            expected_source_ids
        ),
        "required_global_simulator_source_ids": required_globals,
        "top_module": plan.get("top_module"),
        "output": plan.get("output"),
        "tool_binding": copy.deepcopy(plan.get("tool_binding")),
        "compile_authority": copy.deepcopy(compile_authority),
        "final_elaboration_command": copy.deepcopy(elaboration[0]),
        "agent_output_policy": {
            "omit_board_simulation_preflight_plan_vcs_compile_plan": True,
            "do_not_copy_or_reconstruct_ordered_commands": True,
            "framework_regenerates_from_agent_source_selection_and_top": True,
            "framework_rejects_incomplete_or_nonunique_source_coverage": True,
        },
    }


def compact_repair_source_bundle(
    bundle: dict[str, Any],
    *,
    preserve_full_text_modules: set[str] | None = None,
    preserve_full_text_paths: set[str] | None = None,
    preserve_full_text_hashes: set[str] | None = None,
) -> dict[str, Any]:
    documents = bundle.get("documents", [])
    document_rows = documents if isinstance(documents, list) else []
    required_modules = preserve_full_text_modules or set()
    required_paths = preserve_full_text_paths or set()
    required_hashes = preserve_full_text_hashes or set()
    projected_docs = []
    for row in document_rows:
        if not isinstance(row, dict):
            continue
        content = str(row.get("content") or "")
        declared_modules = {
            str(value)
            for value in row.get("modules", [])
            if str(value)
        }
        if required_modules and content:
            declared_modules.update(
                re.findall(
                    r"(?m)^\s*(?:module|class)\s+([A-Za-z_][A-Za-z0-9_$]*)\b",
                    content,
                )
            )
        row_paths = {
            str(row.get(field))
            for field in ("path", "source_path")
            if row.get(field)
        }
        row_hashes = {
            str(row.get(field))
            for field in ("sha256", "source_sha256", "content_sha256")
            if row.get(field)
        }
        preserve_full_text = bool(
            required_modules & declared_modules
            or required_paths & row_paths
            or required_hashes & row_hashes
        )
        projection = evidence_document_projection(
            row,
            preserve_full_text=preserve_full_text,
        )
        if row.get("external_fixture_source") is True and not preserve_full_text:
            projection.pop("module_headers", None)
            projection.pop("interface_headers", None)
            projection["hdl_modules"] = [
                str(value) for value in row.get("modules", []) if str(value)
            ]
            projection["external_fixture_source_id"] = row.get(
                "external_fixture_source_id"
            )
            projection["declaration_authority"] = (
                "external_simulation_fixture.compile_authority.compile_sources"
            )
        projected_docs.append(projection)
    compact_editable = _columnarize_record_lists(bundle.get("editable_contract", {}))
    original_editable = (
        bundle.get("editable_contract", {})
        if isinstance(bundle.get("editable_contract"), dict)
        else {}
    )
    original_rewrite = original_editable.get("board_manifest_rewrite_authority")
    compact_rewrite = compact_editable.get("board_manifest_rewrite_authority")
    framework_materialized = False
    if isinstance(original_rewrite, dict) and isinstance(compact_rewrite, dict):
        original_expanded = original_rewrite.get("expanded_source_authority")
        compact_expanded = compact_rewrite.get("expanded_source_authority")
        original_vcs = (
            original_expanded.get("vcs_command_rewrite_authority")
            if isinstance(original_expanded, dict)
            else None
        )
        compact_vcs = (
            compact_expanded.get("vcs_command_rewrite_authority")
            if isinstance(compact_expanded, dict)
            else None
        )
        ready_plan = (
            original_vcs.get("manifest_ready_vcs_compile_plan")
            if isinstance(original_vcs, dict)
            else None
        )
        if isinstance(compact_vcs, dict) and isinstance(ready_plan, dict):
            executor_contract = original_rewrite.get(
                "executor_preservation_contract", {}
            )
            plan_binding = (
                executor_contract.get("vcs_compile_plan_binding", {})
                if isinstance(executor_contract, dict)
                else {}
            )
            binding_declared = bool(
                isinstance(plan_binding, dict)
                and plan_binding.get(
                    "agent_must_not_copy_or_reconstruct_ordered_commands"
                )
                is True
            )
            plan_projection = (
                _framework_materialized_vcs_plan_contract(ready_plan, original_vcs)
                if binding_declared
                else copy.deepcopy(ready_plan)
            )
            framework_materialized = bool(
                isinstance(plan_projection, dict)
                and plan_projection.get("representation")
                == "framework_materialization_certificate"
            )
            compact_vcs["manifest_ready_vcs_compile_plan"] = plan_projection
            compact_vcs.pop("manifest_ready_ordered_commands", None)
            compact_vcs.pop("ordered_source_ids", None)
            compact_vcs.pop("sample", None)
            compact_vcs.pop("additional_generated_group", None)
            compact_vcs.pop("elaboration_templates", None)
            compact_vcs.pop("manifest_ready_compile_authority", None)
            compact_external = compact_vcs.get("external_fixture")
            if isinstance(compact_external, dict):
                compact_external.pop("command_groups", None)
            compact_vcs["consumer_ready_plan_compaction_policy"] = {
                "framework_materialized_vcs_compile_plan": framework_materialized,
                "manifest_ready_vcs_compile_plan_is_literal_consumer_schema": (
                    not framework_materialized
                ),
                "duplicate_command_groups_ordered_commands_and_source_id_sequence_omitted": True,
                "duplicate_compile_authority_omitted_from_parent": True,
                "all_command_and_source_order_semantics_are_validated_before_compaction": True,
            }
    preservation = (
        original_rewrite.get("executor_preservation_contract", {})
        if isinstance(original_rewrite, dict)
        else {}
    )
    preservation = preservation if isinstance(preservation, dict) else {}
    preserved_hashes = preservation.get("preserved_field_hashes", {})
    preserved_hashes = (
        preserved_hashes if isinstance(preserved_hashes, dict) else {}
    )
    preserved_fields_can_be_omitted = bool(
        preservation.get("guard_satisfied") is True
        and preservation.get("mechanically_preserved_fields")
        and preserved_hashes
    )
    if framework_materialized or preserved_fields_can_be_omitted:
        for document in projected_docs:
            if (
                not isinstance(document, dict)
                or Path(str(document.get("path") or "")).name
                != "dut_weight_binding_manifest.json"
                or not isinstance(document.get("json_content"), dict)
            ):
                continue
            manifest_projection = document["json_content"]
            board_plan = manifest_projection.get("board_simulation_preflight_plan")
            omissions: list[dict[str, Any]] = []
            stale_plan = (
                board_plan.pop("vcs_compile_plan", None)
                if framework_materialized and isinstance(board_plan, dict)
                else None
            )
            if isinstance(stale_plan, dict):
                omissions.append(
                    {
                        "json_pointer": (
                            "/board_simulation_preflight_plan/vcs_compile_plan"
                        ),
                        "omitted_value_canonical_sha256": _canonical_json_sha256(
                            stale_plan
                        ),
                        "materialized_by": (
                            "apply_agent_file_edits.bind_framework_vcs_compile_plan"
                        ),
                    }
                )
            if preserved_fields_can_be_omitted:
                for field in preservation.get("mechanically_preserved_fields", []):
                    field = str(field)
                    value = manifest_projection.get(field)
                    expected_hash = str(preserved_hashes.get(field) or "")
                    if (
                        not field
                        or value is None
                        or not expected_hash
                        or _canonical_json_sha256(value) != expected_hash
                    ):
                        continue
                    manifest_projection.pop(field)
                    omissions.append(
                        {
                            "json_pointer": f"/{field}",
                            "omitted_value_canonical_sha256": expected_hash,
                            "materialized_by": (
                                "apply_agent_file_edits."
                                "preserve_certified_lower_layer_binding_fields"
                            ),
                        }
                    )
            multilayer = (
                manifest_projection.get("multilayer_harness")
                if framework_materialized
                else None
            )
            multilayer_sources = (
                multilayer.get("source_files", [])
                if isinstance(multilayer, dict)
                else []
            )
            certified_rows = (
                original_expanded.get("certified_kernel_sources", [])
                if framework_materialized and isinstance(original_expanded, dict)
                else []
            )
            certified_identities = {
                (
                    str(row.get("source_id") or ""),
                    str(row.get("path") or ""),
                    str(row.get("sha256") or ""),
                )
                for row in certified_rows
                if isinstance(row, dict)
            }
            if isinstance(multilayer_sources, list) and certified_identities:
                framework_rows = [
                    row
                    for row in multilayer_sources
                    if isinstance(row, dict) and row.get("role") == "generated_kernel"
                ]
                framework_row_identities = {
                    (
                        str(row.get("source_id") or ""),
                        str(row.get("path") or ""),
                        str(row.get("sha256") or ""),
                    )
                    for row in framework_rows
                }
                if (
                    framework_rows
                    and len(framework_rows) == len(framework_row_identities)
                    and framework_row_identities.issubset(certified_identities)
                ):
                    multilayer["source_files"] = [
                        row for row in multilayer_sources if row not in framework_rows
                    ]
                    omissions.append(
                        {
                            "json_pointer": "/multilayer_harness/source_files",
                            "omitted_row_selector": {"role": "generated_kernel"},
                            "omitted_row_count": len(framework_rows),
                            "omitted_value_canonical_sha256": _canonical_json_sha256(
                                framework_rows
                            ),
                            "materialized_by": (
                                "finalize_dut_weight_binding_manifest."
                                "board_integration_binding_errors"
                            ),
                        }
                    )
            if not omissions:
                continue
            document["content_encoding"] = (
                "complete_agent_owned_json_with_framework_fields_omitted"
            )
            document["content_preservation"] = (
                "all agent-owned manifest semantics are complete; fields listed in "
                "framework_materialized_json_omissions are hash-bound and restored "
                "mechanically by the named framework operation"
            )
            document["framework_materialized_json_omissions"] = omissions
    return {
        "schema_version": bundle.get("schema_version"),
        "status": bundle.get("status"),
        "verification_scope": bundle.get("verification_scope"),
        "bundle_profile": bundle.get("bundle_profile"),
        "all_documents_complete": bundle.get("all_documents_complete"),
        "document_count": len(document_rows),
        "document_chars": bundle.get("document_chars"),
        "duplicate_documents_removed": bundle.get("duplicate_documents_removed"),
        "editable_contract": compact_editable,
        "generated_module_inventory": _columnarize_record_lists(
            bundle.get("generated_module_inventory", [])
        ),
        "trusted_numeric_support": compact_for_retry(bundle.get("trusted_numeric_support", {})),
        "external_fixture_source_contract": compact_for_retry(
            bundle.get("external_fixture_source_contract", {})
        ),
        "documents": projected_docs,
        "compaction_policy": {
            "full_document_text_or_json_omitted_except_selected_editable_interface_and_certified_lifecycle_sources": True,
            "evidence_preserved_by_path_and_sha256": True,
            "tools_must_read_hash_bound_source_files_for_execution": True,
        },
    }


def _compact_board_preflight_feedback(
    feedback: dict[str, Any],
) -> dict[str, Any]:
    exact_blockers = [
        copy.deepcopy(value)
        for value in feedback.get("blockers", [])
        if isinstance(value, (str, dict))
    ]

    compact = {
        key: copy.deepcopy(feedback.get(key))
        for key in (
            "schema_version",
            "status",
            "evidence_kind",
            "summary",
            "current_validation_mode",
            "required_validation_mode",
            "repair_handoff",
        )
        if key in feedback
    }

    def blocker_indices(values: Any, prefix: str) -> tuple[list[int], list[Any]]:
        indices: list[int] = []
        unmapped: list[Any] = []
        for value in values if isinstance(values, list) else []:
            candidates = [value]
            if isinstance(value, str) and prefix:
                candidates.append(f"{prefix}: {value}")
            index = next(
                (
                    exact_blockers.index(candidate)
                    for candidate in candidates
                    if candidate in exact_blockers
                ),
                None,
            )
            if index is None:
                unmapped.append(copy.deepcopy(value))
            else:
                indices.append(index)
        return indices, unmapped

    def blocker_projection(values: Any, prefix: str) -> dict[str, Any]:
        rows = values if isinstance(values, list) else []
        indices, unmapped = blocker_indices(rows, prefix)
        return {
            "top_level_blocker_indices": indices,
            "unmapped_exact_values": unmapped,
            "row_count": len(rows),
            "canonical_sha256": _canonical_json_sha256(rows),
        }

    def source_sequence_projection(values: Any) -> dict[str, Any]:
        rows = values if isinstance(values, list) else []
        return {
            "shared_source_index_authority": (
                "#/verification_capability_repair_package/"
                "repair_source_bundle/editable_contract/board_manifest_rewrite_authority/"
                "expanded_source_authority"
            ),
            "row_count": len(rows),
            "canonical_sha256": _canonical_json_sha256(rows),
        }

    materialization = feedback.get("materialization")
    if isinstance(materialization, dict):
        value = materialization.get("value")
        value = value if isinstance(value, dict) else {}
        materialized_value = {
            key: copy.deepcopy(value.get(key))
            for key in (
                "schema_version",
                "status",
                "manifest",
                "manifest_sha256",
                "stage_harness_count",
                "single_layer_harness_materialized",
                "board_integration_harness_materialized",
                "board_simulation_preflight_materialized",
                "board_simulation_preflight_manifest",
                "board_simulation_preflight_manifest_sha256",
                "board_simulation_preflight_report",
                "vcs_compile_plan_sha256",
                "source_agent_manifest",
                "source_agent_manifest_sha256",
                "source_patch_application",
                "source_patch_application_sha256",
            )
            if key in value
        }
        materialized_value["blockers"] = blocker_projection(
            value.get("blockers"), ""
        )
        compact["materialization"] = {
            key: copy.deepcopy(materialization.get(key))
            for key in ("path", "sha256")
            if key in materialization
        }
        compact["materialization"]["value"] = materialized_value

    preflight = feedback.get("preflight")
    if isinstance(preflight, dict):
        value = preflight.get("value")
        value = value if isinstance(value, dict) else {}
        preflight_value = {
            key: copy.deepcopy(value.get(key))
            for key in (
                "schema_version",
                "status",
                "manifest",
                "manifest_sha256",
                "manifest_status",
                "vcs_compile_plan_sha256",
            )
            if key in value
        }
        preflight_value["blockers"] = blocker_projection(
            value.get("blockers"), "board_preflight"
        )
        exact = value.get("exact_board_preflight")
        if isinstance(exact, dict):
            exact_projection = {
                key: copy.deepcopy(exact.get(key))
                for key in (
                    "schema_version",
                    "status",
                    "phase",
                    "identity_path",
                    "simulation_manifest_path",
                    "source_closure_sha256",
                    "compile_source_set_sha256",
                    "vcs_compile_plan_sha256",
                )
                if key in exact
            }
            exact_projection["blockers"] = blocker_projection(
                exact.get("blockers"), "board_preflight"
            )
            for field in (
                "external_fixture_source_ids",
                "generated_source_ids",
                "preserved_sample_source_ids",
                "replaced_sample_source_ids",
                "sample_runtime_auxiliary_source_ids",
                "verified_compile_source_ids",
            ):
                if field in exact:
                    exact_projection[field] = source_sequence_projection(exact[field])
            checks = exact.get("checks")
            exact_projection["checks"] = [
                {
                    **{
                        key: copy.deepcopy(row.get(key))
                        for key in ("name", "status", "path")
                        if key in row
                    },
                    "blockers": blocker_projection(
                        row.get("blockers"), "board_preflight"
                    ),
                    **(
                        {
                            "root_source_ids": source_sequence_projection(
                                row.get("root_source_ids")
                            )
                        }
                        if "root_source_ids" in row
                        else {}
                    ),
                }
                for row in checks if isinstance(row, dict)
            ] if isinstance(checks, list) else []
            preflight_value["exact_board_preflight"] = exact_projection
        compact["preflight"] = {
            key: copy.deepcopy(preflight.get(key))
            for key in ("path", "sha256")
            if key in preflight
        }
        compact["preflight"]["value"] = preflight_value
    if len(json.dumps(exact_blockers, sort_keys=True).encode("utf-8")) > 24_000:
        run_roots = sorted(
            {
                match.group(0)
                for value in exact_blockers
                if isinstance(value, str)
                for match in re.finditer(
                    r"/[^\s\"']*/accagent/runs/[^/\s\"']+/[^/\s\"']+/",
                    value,
                )
            },
            key=len,
            reverse=True,
        )
        path_prefixes = {
            f"@run_root_{index}/": root
            for index, root in enumerate(run_roots)
        }

        def alias(value: Any) -> str:
            text = str(value)
            for token, root in path_prefixes.items():
                text = text.replace(root, token)
            return text

        grouped: dict[str, list[str]] = {}
        for value in exact_blockers:
            text = alias(value)
            group, separator, rest = text.partition(": ")
            if separator:
                grouped.setdefault(group, []).append(rest)
            else:
                grouped.setdefault("ungrouped", []).append(text)
        compact["blockers"] = {
            "encoding": "spatialaccagent.lossless_exact_blocker_strings.v1",
            "row_count": len(exact_blockers),
            "first_values": [alias(value) for value in exact_blockers[:16]],
            "path_prefixes": path_prefixes,
            "groups": {
                group: _encoded_column(values)
                for group, values in grouped.items()
            },
            "canonical_sha256": _canonical_json_sha256(exact_blockers),
            "policy": (
                "first_values expose the earliest blockers directly; groups plus path_prefixes "
                "are a lossless encoding of the complete current blocker list"
            ),
        }
    else:
        compact["blockers"] = exact_blockers
    compact["semantic_projection"] = {
        "all_current_failure_strings_preserved_in_blockers_or_lossless_blocker_encoding": True,
        "bound_artifact_paths_and_sha256_preserved": True,
        "repeated_check_blockers_reference_the_exact_top_level_failure_set": True,
        "repeated_source_id_sequences_reference_the_complete_shared_source_index": True,
        "full_bound_artifact_values_omitted_from_prompt_only": True,
    }
    return compact


def _compact_exact_sequence(values: Any, *, limit: int = 128) -> Any:
    if not isinstance(values, list):
        return copy.deepcopy(values)
    rows = copy.deepcopy(values)
    if len(rows) <= limit:
        return rows
    tail_count = min(16, limit // 4)
    return {
        "row_count": len(rows),
        "canonical_sha256": _canonical_json_sha256(rows),
        "first_values": rows[: limit - tail_count],
        "last_values": rows[-tail_count:],
    }


def _compact_causal_log(value: Any, first_error: Any) -> Any:
    if not isinstance(value, str):
        return copy.deepcopy(value)
    if not value:
        return value

    marker = str(first_error or "")
    marker_offset = value.find(marker) if marker else -1
    if marker_offset < 0:
        marker_offset = next(
            (
                offset
                for token in ("Error-[", "Fatal", "Assertion", "FAILED", "failed")
                if (offset := value.find(token)) >= 0
            ),
            -1,
        )
    if marker_offset >= 0:
        # The first real error and its immediate source context are causal.
        # Simulator banners, parsed-file lists and later cascades are not.
        start = max(0, marker_offset - 512)
        end = min(len(value), marker_offset + 4_096)
    else:
        start = max(0, len(value) - 4_096)
        end = len(value)
    if start:
        newline = value.find("\n", start)
        start = newline + 1 if newline >= 0 and newline < end else start
    if end < len(value):
        newline = value.rfind("\n", start, end)
        end = newline if newline > start else end
    excerpt = value[start:end]
    return {
        "text_chars": len(value),
        "text_sha256": _hash_text(value),
        "excerpt_char_start": start,
        "excerpt_char_end": end,
        "excerpt": excerpt,
        "first_error_present_in_excerpt": bool(marker and marker in excerpt),
        "full_log_omitted_from_prompt_only": start > 0 or end < len(value),
    }


def _compact_execution_result(value: Any) -> Any:
    if not isinstance(value, dict):
        return copy.deepcopy(value)
    result = {
        key: copy.deepcopy(value.get(key))
        for key in (
            "status",
            "returncode",
            "failure_class",
            "remote_state",
            "duration_sec",
            "summary",
            "remote_job_preserved",
            "poll_attempts",
            "poll_transport_failures",
        )
        if key in value
    }
    for key in ("stdout_tail", "stderr_tail"):
        if key in value:
            result[key] = _bounded_projection_value(
                value.get(key), head_chars=2_000, tail_chars=2_000
            )
    if isinstance(value.get("termination_provenance"), dict):
        result["termination_provenance"] = _compact_progress_value(
            value.get("termination_provenance")
        )
    return result


def _compact_progress_value(value: Any, *, depth: int = 0) -> Any:
    """Keep live causal evidence useful while bounding agent prompt growth."""

    if isinstance(value, str):
        return _bounded_projection_value(value, head_chars=800, tail_chars=200)
    if value is None or isinstance(value, (bool, int, float)):
        return copy.deepcopy(value)
    if depth >= 3:
        return {
            "canonical_sha256": _canonical_json_sha256(value),
            "omitted_beyond_progress_projection_depth": True,
        }
    if isinstance(value, list):
        rows = value[-32:]
        projected = [
            _compact_progress_value(row, depth=depth + 1) for row in rows
        ]
        if len(value) <= 32:
            return projected
        return {
            "row_count": len(value),
            "canonical_sha256": _canonical_json_sha256(value),
            "last_values": projected,
        }
    if isinstance(value, dict):
        keys = list(value)[:48]
        projected = {
            str(key): _compact_progress_value(value[key], depth=depth + 1)
            for key in keys
        }
        if len(value) > len(keys):
            projected["_omitted_key_count"] = len(value) - len(keys)
            projected["_canonical_sha256"] = _canonical_json_sha256(value)
        return projected
    return _bounded_projection_value(str(value), head_chars=800, tail_chars=200)


def _compact_supplemental_scalar_record(value: Any) -> dict[str, Any]:
    """Preserve the bounded flat probe record emitted by the VCS runner."""

    if not isinstance(value, dict):
        return {}
    keys = list(value)[:128]
    result = {
        str(key): _compact_progress_value(value[key], depth=2)
        for key in keys
    }
    if len(value) > len(keys):
        result["_omitted_scalar_count"] = len(value) - len(keys)
        result["_canonical_sha256"] = _canonical_json_sha256(value)
    return result


def _compact_supplemental_observation_artifacts(value: Any) -> Any:
    """Keep bounded testbench-sidecar observations available to repair agents."""

    if not isinstance(value, list):
        return _compact_progress_value(value)
    artifacts: list[dict[str, Any]] = []
    for row in value[-16:]:
        if not isinstance(row, dict):
            continue
        artifact = {
            key: _compact_progress_value(row.get(key), depth=2)
            for key in (
                "status",
                "artifact_kind",
                "relative_path",
                "evidence_id",
                "sha256",
                "byte_count",
            )
            if key in row
        }
        summary = row.get("summary")
        if isinstance(summary, dict):
            compact_summary = {
                key: _compact_progress_value(summary.get(key), depth=2)
                for key in (
                    "status",
                    "record_count",
                    "invalid_record_count",
                    "trailing_partial_byte_count",
                    "timescale",
                    "variable_count",
                    "timestamp_count",
                    "first_timestamp",
                    "previous_timestamp",
                    "last_timestamp",
                    "simulation_time_advanced",
                    "native_loop_detected",
                    "loop_detection_enabled_observed",
                    "artifact_count",
                )
                if key in summary
            }
            for key in ("schema_versions", "probe_ids", "probe_revisions"):
                if key in summary:
                    compact_summary[key] = _compact_exact_sequence(
                        summary.get(key), limit=16
                    )
            for key in ("matched_markers", "matched_simulation_log_markers"):
                if key in summary:
                    compact_summary[key] = _compact_exact_sequence(
                        summary.get(key), limit=8
                    )
            if "recent_changed_variables" in summary:
                compact_summary["recent_changed_variables"] = (
                    _compact_exact_sequence(
                        summary.get("recent_changed_variables"), limit=64
                    )
                )
            if "excerpt" in summary:
                compact_summary["excerpt"] = _bounded_projection_value(
                    str(summary.get("excerpt") or ""),
                    head_chars=3000,
                    tail_chars=3000,
                )
            for key in ("first_scalar_record", "last_scalar_record"):
                if key in summary:
                    compact_summary[key] = _compact_supplemental_scalar_record(
                        summary.get(key)
                    )
            tail = summary.get("tail_scalar_records")
            if isinstance(tail, list):
                compact_summary["tail_scalar_records"] = [
                    _compact_supplemental_scalar_record(record)
                    for record in tail[-16:]
                    if isinstance(record, dict)
                ]
            artifact["summary"] = compact_summary
        artifacts.append(artifact)
    return artifacts


def _compact_semantic_stall_evidence(value: Any) -> Any:
    if not isinstance(value, dict):
        return copy.deepcopy(value)
    scalar_fields = (
        "schema_version",
        "status",
        "proof_mode",
        "reason",
        "last_semantic_event_cycle",
        "latest_cycle",
        "silent_cycles",
        "stable_state_start_cycle",
        "stable_state_cycles",
        "adaptive_silent_cycle_bound",
        "max_observed_semantic_gap",
        "max_target_work_units",
        "observed_heartbeat_interval",
        "semantic_event_count",
        "stall_snapshot_count",
        "semantic_progress_field_schema_valid",
        "fixed_cycle_timeout",
        "fixed_wall_clock_timeout",
    )
    result = {
        key: copy.deepcopy(value.get(key))
        for key in scalar_fields
        if key in value
    }
    for key in (
        "last_semantic_progress_event",
        "latest_stall_snapshot",
        "latest_complete_event",
        "cctg_frontier_stall_evidence",
        "policy",
    ):
        if key in value:
            result[key] = _compact_progress_value(value.get(key))
    return result


def _compact_repeated_validation_errors(value: Any) -> Any:
    if not isinstance(value, list):
        return copy.deepcopy(value)
    normalized_counts: dict[str, int] = {}
    for row in value:
        normalized = re.sub(r"record\[\d+\]", "record[*]", str(row))
        normalized_counts[normalized] = normalized_counts.get(normalized, 0) + 1
    return {
        "row_count": len(value),
        "canonical_sha256": _canonical_json_sha256(value),
        "normalized_patterns": [
            {"pattern": pattern, "count": count}
            for pattern, count in normalized_counts.items()
        ],
        "first_values": copy.deepcopy(value[:4]),
        "last_values": copy.deepcopy(value[-4:]),
    }


def _compact_repeated_stall_tail(value: Any) -> Any:
    if not isinstance(value, list):
        return _compact_progress_value(value)
    rows = [row for row in value if isinstance(row, dict)]
    kind_counts: dict[str, int] = {}
    representatives: dict[str, Any] = {}
    for row in rows:
        kind = str(row.get("event_kind") or "unknown")
        kind_counts[kind] = kind_counts.get(kind, 0) + 1
        representatives[kind] = _compact_progress_value(row)
    return {
        "row_count": len(value),
        "canonical_sha256": _canonical_json_sha256(value),
        "first_cycle": rows[0].get("cycle") if rows else None,
        "last_cycle": rows[-1].get("cycle") if rows else None,
        "event_kind_counts": kind_counts,
        "last_event_by_kind": representatives,
        "stable_cumulative_state_repetitions_omitted": True,
    }


def _compact_progress_summary(value: Any, *, semantic_stall: bool = False) -> Any:
    if not isinstance(value, dict):
        return copy.deepcopy(value)
    scalar_fields = (
        "schema_version",
        "status",
        "record_count",
        "semantic_progress_event_count",
        "heartbeat_event_count",
        "progress_epoch",
        "last_cycle",
        "last_semantic_progress_cycle",
        "silent_cycles",
        "first_stalled_boundary",
        "terminal_event_seen",
    )
    event_fields = (
        "last_complete_record",
        "last_semantic_progress_event",
        "latest_stall_snapshot",
        "causal_event_tail",
    )
    result = {
        key: copy.deepcopy(value.get(key))
        for key in scalar_fields
        if key in value
    }
    for key in event_fields:
        if key in value:
            result[key] = (
                _compact_repeated_stall_tail(value.get(key))
                if semantic_stall and key == "causal_event_tail"
                else _compact_progress_value(value.get(key))
            )
    if "validation_errors" in value:
        result["validation_errors"] = (
            _compact_repeated_validation_errors(value.get("validation_errors"))
            if semantic_stall
            else _compact_exact_sequence(value.get("validation_errors"), limit=32)
        )
    return result


def _compact_direct_structured_failures(
    value: Any,
    *,
    compile_failed: bool,
) -> Any:
    if not isinstance(value, dict):
        return copy.deepcopy(value)
    if compile_failed:
        return {
            "canonical_sha256": _canonical_json_sha256(value),
            "omitted_as_downstream_of_compile_failure": True,
            "policy": (
                "simulation outputs and acceptance checks cannot be causal when "
                "the current real-tool compile did not complete"
            ),
        }
    result = {
        key: copy.deepcopy(nested)
        for key, nested in value.items()
        if key != "exact_board_acceptance_checks"
    }
    checks = value.get("exact_board_acceptance_checks")
    if isinstance(checks, list):
        failed_checks = [
            {
                "name": row.get("name"),
                "status": row.get("status"),
                "blockers": _compact_exact_sequence(row.get("blockers", []), limit=24),
            }
            for row in checks
            if isinstance(row, dict) and row.get("status") != "pass"
        ]
        result["failed_exact_board_acceptance_checks"] = failed_checks
    return result


def _compact_sacg_cctg_causal_slice(value: Any) -> Any:
    """Keep the current frontier without repeating the full static SACG/CCTG."""

    if not isinstance(value, dict):
        return copy.deepcopy(value)
    source = value.get("value")
    source = source if isinstance(source, dict) else value
    graph = source.get("causal_graph_slice")
    graph = graph if isinstance(graph, dict) else {}
    hierarchy = source.get("hierarchical_certificate_projection")
    hierarchy = hierarchy if isinstance(hierarchy, dict) else {}
    certificate = hierarchy.get("single_layer_certificate")
    certificate = certificate if isinstance(certificate, dict) else {}
    real_tool = hierarchy.get("single_layer_real_tool_evidence")
    real_tool = real_tool if isinstance(real_tool, dict) else {}
    compact_hierarchy = {
        "current_board_evidence_contradicts_lower_certificate": hierarchy.get(
            "current_board_evidence_contradicts_lower_certificate"
        ),
        "lower_layer_reopen_policy": hierarchy.get("lower_layer_reopen_policy"),
        "single_layer_certificate": {
            key: copy.deepcopy(certificate[key])
            for key in ("status", "required_gates", "policy")
            if key in certificate
        },
        "single_layer_real_tool_evidence": {
            key: copy.deepcopy(real_tool[key])
            for key in (
                "status",
                "cycles",
                "input_beats",
                "output_beats",
                "pipeline_overlap_status",
                "pipeline_transition_count",
            )
            if key in real_tool
        },
    }
    projection = {
        key: copy.deepcopy(source[key])
        for key in (
            "schema_version",
            "status",
            "failure_class",
            "earliest_unproven_frontier",
            "parallel_branch_status",
        )
        if key in source
    }
    if any(
        value not in ({}, None)
        for value in compact_hierarchy.values()
    ):
        projection["hierarchical_certificate_projection"] = compact_hierarchy
    causal_paths = graph.get("cctg_causal_paths")
    if isinstance(causal_paths, list) and causal_paths:
        projection["cctg_causal_paths"] = copy.deepcopy(causal_paths)
    # Retain the bound artifact identity so a compact package can be compacted
    # again without changing the current-frontier lock.
    return {
        **{
            key: copy.deepcopy(value.get(key))
            for key in ("path", "sha256", "source_path", "source_sha256")
            if value.get(key) is not None
        },
        "value": projection,
    }


def _current_adaptive_observation_decision_lock(
    package: dict[str, Any],
) -> dict[str, Any]:
    """Expose the current SACG/CCTG stop point as the prompt authority.

    Retry history can contain older frontier names.  Those names remain useful
    as background evidence, but must not compete with the current causal slice
    when the Agent selects its next observation or repair.
    """

    feedback = package.get("current_board_vcs_feedback")
    feedback = feedback if isinstance(feedback, dict) else {}
    diagnosis_artifact = feedback.get("diagnosis")
    diagnosis_artifact = (
        diagnosis_artifact if isinstance(diagnosis_artifact, dict) else {}
    )
    diagnosis = diagnosis_artifact.get("value")
    diagnosis = diagnosis if isinstance(diagnosis, dict) else {}
    failure_evidence = diagnosis.get("failure_evidence")
    failure_evidence = (
        failure_evidence if isinstance(failure_evidence, dict) else {}
    )
    causal_artifact = failure_evidence.get("sacg_cctg_causal_slice")
    causal_artifact = (
        causal_artifact if isinstance(causal_artifact, dict) else {}
    )
    causal = causal_artifact.get("value")
    causal = causal if isinstance(causal, dict) else causal_artifact
    frontier = causal.get("earliest_unproven_frontier")
    frontier = frontier if isinstance(frontier, dict) else {}
    frontier_id = str(frontier.get("frontier_id") or "").strip()
    if not frontier_id:
        return {}

    # This lock is intentionally rebuilt from the current VCS diagnosis on
    # every turn.  A persisted lock can describe an older signal epoch even
    # when its frontier name happens to match, which would let old evidence
    # steer the next hardware decision.
    allowed_modes = [
        "direct_executed_contradiction",
        "direct_tool_failure",
        "deepen_simulation_observation",
    ]

    causal_sha256 = str(causal_artifact.get("sha256") or "").strip()
    lock = {
        "schema_version": "spatialaccagent.adaptive_observation_decision_lock.v1",
        "status": "required",
        "frontier_id": frontier_id,
        "allowed_modes": allowed_modes,
        "source": (
            "current_board_vcs_feedback.diagnosis.value.failure_evidence."
            "sacg_cctg_causal_slice.value.earliest_unproven_frontier"
        ),
        "causal_slice_sha256": causal_sha256 or None,
        "instruction": (
            "Copy this current frontier_id exactly. It was rebuilt from this "
            "VCS epoch. Do not use a prior observation plan, probe, signal "
            "value, or historical frontier as decision evidence."
        ),
    }
    return lock


_LAYER3_EXECUTION_ONLY_TERMS = (
    "checkpoint",
    "fast_replay",
    "fast-replay",
    "cold_capture",
    "cold-capture",
    "native_exact_model",
    "native checkpoint",
    "native_checkpoint",
)


def _strip_layer3_execution_only_context(value: Any) -> Any:
    """Remove replay mechanics from a Layer-3 hardware decision package.

    Replay is an executor optimization.  It must neither explain a hardware
    stop nor influence which RTL or observation edit the Agent selects.
    """

    if isinstance(value, dict):
        result: dict[str, Any] = {}
        # A complete editable source may legitimately contain native VCS
        # checkpoint implementation details.  It is not execution-state
        # evidence, and removing the whole source would leave the Agent
        # unable to make a hash-bound observation edit.  Filter structured
        # execution metadata, but retain the exact source text unchanged.
        source_document = isinstance(value.get("content"), str) and bool(
            value.get("path") or value.get("source_path")
        )
        for key, child in value.items():
            if source_document and key == "content":
                result[str(key)] = copy.deepcopy(child)
                continue
            normalized_key = str(key).lower().replace("-", "_")
            if any(term.replace("-", "_") in normalized_key for term in _LAYER3_EXECUTION_ONLY_TERMS):
                continue
            if normalized_key in {
                "runner_phase",
                "phase",
                "simulation_execution_identity",
                "compile_reused",
                "second_vcs_compile_was_not_launched",
                "weight_load_skipped",
            }:
                continue
            compact_child = _strip_layer3_execution_only_context(child)
            if compact_child is not None:
                result[str(key)] = compact_child
        return result
    if isinstance(value, list):
        return [
            compact_child
            for child in value
            if (compact_child := _strip_layer3_execution_only_context(child))
            is not None
        ]
    if isinstance(value, str):
        lowered = value.lower()
        if any(term in lowered for term in _LAYER3_EXECUTION_ONLY_TERMS):
            return None
    return copy.deepcopy(value)


def _compact_current_layer3_signal_epoch(feedback: dict[str, Any]) -> dict[str, Any]:
    """Return only fresh internal signals from the current Layer-3 VCS epoch."""

    runner_artifact = feedback.get("runner_report")
    runner = (
        runner_artifact.get("value", {})
        if isinstance(runner_artifact, dict)
        else {}
    )
    if not isinstance(runner, dict):
        return {}
    # All values are from the runner's persisted current observation epoch.
    # Keep the full bounded signal records rather than replacing individual
    # internal values with hashes; the Agent needs the actual wave facts.
    signal_fields = (
        "observation_epoch",
        "record_count",
        "semantic_progress_event_count",
        "heartbeat_event_count",
        "last_cycle",
        "last_semantic_progress_cycle",
        "silent_cycles",
        "first_stalled_boundary",
        "terminal_event_seen",
        "last_semantic_progress_event",
        "last_complete_record",
        "latest_stall_snapshot",
        "latest_event_by_kind",
        "causal_event_tail",
        "extra_signal_names",
        "extra_signal_snapshots",
        "testbench_observation_activity",
        "intra_layer_pipeline_violation_evidence",
    )
    live_progress = runner.get("live_progress")
    latest = (
        live_progress.get("latest")
        if isinstance(live_progress, dict)
        and isinstance(live_progress.get("latest"), dict)
        else {}
    )
    result = {
        key: copy.deepcopy(latest[key]) for key in signal_fields if key in latest
    }
    runtime_signal_trace = runner.get("runtime_signal_trace")
    if isinstance(runtime_signal_trace, dict):
        result["runtime_signal_trace"] = copy.deepcopy(runtime_signal_trace)
    result = _strip_layer3_execution_only_context(result)
    if not result:
        return {}
    return {
        "authority": "current_board_vcs_feedback.runner_report.value.live_progress.latest",
        "fresh_epoch_only": True,
        "prior_epoch_signal_values_omitted": True,
        "value": result,
    }


def _compact_current_adaptive_observation_state(
    value: Any,
    *,
    current_vcs_feedback_present: bool,
) -> dict[str, Any]:
    """Keep the current observation plan without repeating the VCS report.

    The durable adaptive state keeps a failed-state recheck containing the
    runner report and the complete boundary summary.  The same report is also
    available in ``current_board_vcs_feedback``.  That recheck is useful on
    disk for recovery, but copying it into the hot-loop prompt duplicates the
    current signal evidence and can exceed the provider context limit.
    """

    if not isinstance(value, dict):
        return {}

    result = {
        key: copy.deepcopy(value[key])
        for key in (
            "schema_version",
            "status",
            "aggregation_mode",
            "frontier_id",
            "probe_ids",
            "required_event_fields",
            "compiled_probe_sources_bound",
            "summary",
            "path",
            "decision_sha256",
            "board_source_edits",
            "source_patch_application",
            "event_match",
            "runner_report",
            "progress_event_logs",
        )
        if value.get(key) is not None
    }

    decision = value.get("decision")
    if isinstance(decision, dict):
        # The decision contains the current signal plan, not a second copy of
        # the emitted VCS signal values, so keep it for the next action.
        result["decision"] = copy.deepcopy(decision)

    failed_recheck = value.get("failed_state_recheck")
    if isinstance(failed_recheck, dict):
        runner = failed_recheck.get("runner")
        runner = runner if isinstance(runner, dict) else {}
        boundary = failed_recheck.get("boundary")
        boundary = boundary if isinstance(boundary, dict) else {}
        # Both locations contain the same complete current signal summary.
        # Keep one canonical copy so the Agent still receives the 300-signal
        # evidence without paying for the duplicated runner/boundary wrapper.
        signal_summary = boundary.get("summary")
        if not isinstance(signal_summary, dict):
            signal_summary = runner.get("pipeline_boundary_observation_summary")
        if isinstance(signal_summary, dict):
            result["current_signal_summary"] = {
                "source": (
                    "adaptive_observation_state.failed_state_recheck.boundary.summary"
                ),
                "value": copy.deepcopy(signal_summary),
            }
        if current_vcs_feedback_present:
            result["durable_evidence"] = {
                "failed_state_recheck_on_disk": True,
                "current_signal_summary_is_the_only_prompt_copy": True,
                "current_vcs_feedback_is_the_only_prompt_copy_of_the_vcs_report": True,
            }
        else:
            # Without a separate current VCS report, preserve the bounded
            # recheck metadata as the only available failure source.
            result["failed_state_recheck_metadata"] = {
                key: copy.deepcopy(failed_recheck.get(key))
                for key in ("status", "blockers", "runner_report")
                if failed_recheck.get(key) is not None
            }

    return result


def _compact_board_vcs_feedback(feedback: dict[str, Any]) -> dict[str, Any]:
    compact = {
        key: copy.deepcopy(feedback.get(key))
        for key in ("schema_version", "status", "blockers")
        if key in feedback
    }

    diagnosis_artifact = feedback.get("diagnosis")
    if isinstance(diagnosis_artifact, dict):
        diagnosis = diagnosis_artifact.get("value")
        diagnosis = diagnosis if isinstance(diagnosis, dict) else {}
        diagnosis_projection = {
            key: copy.deepcopy(diagnosis.get(key))
            for key in (
                "schema_version",
                "status",
                "summary",
                "diagnosis_status",
                "failure_class",
                "root_cause_class",
                "repair_patterns",
                "sim_pass",
            )
            if key in diagnosis
        }
        failure_evidence = diagnosis.get("failure_evidence")
        failure_evidence = failure_evidence if isinstance(failure_evidence, dict) else {}
        first_error = failure_evidence.get("first_real_error") or diagnosis.get(
            "first_real_error"
        )
        compile_result = failure_evidence.get("compile")
        compile_failed = (
            isinstance(compile_result, dict)
            and compile_result.get("status") == "fail"
        )
        failure_class = str(
            failure_evidence.get("failure_class")
            or diagnosis.get("failure_class")
            or ""
        )
        semantic_stall = failure_class == "vcs_runtime_semantic_stall"
        runtime_frontier_failure = (
            failure_class
            if failure_class
            in {
                "vcs_runtime_semantic_stall",
                "vcs_runtime_zero_time_livelock",
            }
            else ""
        )
        causal_projection = {
            key: copy.deepcopy(failure_evidence.get(key))
            for key in ("failure_class", "first_real_error")
            if key in failure_evidence
        }
        for key in ("compile", "simulation"):
            if key in failure_evidence:
                causal_projection[key] = _compact_execution_result(
                    failure_evidence.get(key)
                )
        if isinstance(failure_evidence.get("termination_provenance"), dict):
            causal_projection["termination_provenance"] = (
                _compact_progress_value(
                    failure_evidence.get("termination_provenance")
                )
            )
        if "log_tail" in failure_evidence:
            compact_log = _compact_causal_log(
                failure_evidence.get("log_tail"), first_error
            )
            if runtime_frontier_failure:
                compact_log.pop("excerpt", None)
                compact_log["repetitive_log_text_omitted"] = True
                compact_log["replacement_evidence"] = (
                    "zero_time_livelock_evidence plus progress_event_summary"
                    if failure_class == "vcs_runtime_zero_time_livelock"
                    else "adaptive_semantic_stall_evidence plus progress_event_summary"
                )
            causal_projection["causal_log_excerpt"] = compact_log
        if "related_source_ids" in failure_evidence:
            causal_projection["related_source_ids"] = _compact_exact_sequence(
                failure_evidence.get("related_source_ids")
            )
        structured_failures_value = failure_evidence.get("structured_failures")
        if (
            not compile_failed
            and not runtime_frontier_failure
            and isinstance(structured_failures_value, dict)
            and structured_failures_value
        ):
            causal_projection["structured_failures"] = (
                _compact_direct_structured_failures(
                    structured_failures_value,
                    compile_failed=compile_failed,
                )
            )
        adaptive_semantic_stall_value = failure_evidence.get(
            "adaptive_semantic_stall_evidence"
        )
        if (
            not compile_failed
            and isinstance(adaptive_semantic_stall_value, dict)
            and adaptive_semantic_stall_value
        ):
            causal_projection["adaptive_semantic_stall_evidence"] = (
                _compact_semantic_stall_evidence(
                    adaptive_semantic_stall_value
                )
            )
        zero_time_livelock_value = failure_evidence.get(
            "zero_time_livelock_evidence"
        )
        if (
            not compile_failed
            and isinstance(zero_time_livelock_value, dict)
            and zero_time_livelock_value
        ):
            causal_projection["zero_time_livelock_evidence"] = (
                _compact_progress_value(zero_time_livelock_value)
            )
        if not compile_failed and "progress_event_summary" in failure_evidence:
            causal_projection["progress_event_summary"] = _compact_progress_summary(
                failure_evidence.get("progress_event_summary"),
                semantic_stall=runtime_frontier_failure,
            )
        supplemental_observations = failure_evidence.get(
            "supplemental_observation_artifacts"
        )
        if (
            not compile_failed
            and isinstance(supplemental_observations, list)
            and supplemental_observations
        ):
            causal_projection["supplemental_observation_artifacts"] = (
                _compact_supplemental_observation_artifacts(
                    supplemental_observations
                )
            )
        native_loop_report = failure_evidence.get("vcs_native_loop_report")
        if (
            not compile_failed
            and isinstance(native_loop_report, dict)
            and native_loop_report
        ):
            causal_projection["vcs_native_loop_report"] = _compact_progress_value(
                native_loop_report
            )
        if "sacg_cctg_causal_slice" in failure_evidence:
            causal_projection["sacg_cctg_causal_slice"] = (
                _compact_sacg_cctg_causal_slice(
                    failure_evidence.get("sacg_cctg_causal_slice")
                )
            )
        diagnosis_projection["failure_evidence"] = causal_projection

        compact["diagnosis"] = {"value": diagnosis_projection}

    runner_artifact = feedback.get("runner_report")
    if isinstance(runner_artifact, dict):
        runner = runner_artifact.get("value")
        runner = runner if isinstance(runner, dict) else {}
        runner_projection = {
            key: copy.deepcopy(runner.get(key))
        for key in (
            "schema_version",
            "status",
            "returncode",
            "failure_class",
            "validation_mode",
            "exact_board_preflight_passed",
            "source_identity_bound",
            "all_target_layers",
            "accelerator_scope",
            "runtime_signal_trace",
            )
            if key in runner
        }
        for key in ("compile", "run"):
            if key in runner:
                runner_projection[key] = _compact_execution_result(runner.get(key))
        if isinstance(runner.get("termination_provenance"), dict):
            runner_projection["termination_provenance"] = (
                _compact_progress_value(runner.get("termination_provenance"))
            )
        for key in ("errors", "blockers"):
            if key in runner:
                runner_projection[key] = _compact_exact_sequence(
                    runner.get(key), limit=32
                )
        supplemental_observations = runner.get(
            "supplemental_observation_artifacts"
        )
        if isinstance(supplemental_observations, list) and supplemental_observations:
            runner_projection["supplemental_observation_artifacts"] = (
                _compact_supplemental_observation_artifacts(
                    supplemental_observations
                )
            )
        native_loop_report = runner.get("vcs_native_loop_report")
        if isinstance(native_loop_report, dict) and native_loop_report:
            runner_projection["vcs_native_loop_report"] = _compact_progress_value(
                native_loop_report
            )
        compact["runner_report"] = {"value": runner_projection}

    # Give the repair Agent an exact, low-cost pointer index for adaptive
    # observation decisions.  The full package remains the validation
    # authority; this projection only prevents the model from guessing nested
    # paths after diagnostic evidence has been compacted.
    pointer_guide: list[dict[str, Any]] = []

    def collect_scalars(value: Any, path: str, limit: int = 48) -> None:
        if len(pointer_guide) >= limit:
            return
        if isinstance(value, dict):
            for key, child in value.items():
                if key in {"path", "sha256", "source_path", "source_sha256"}:
                    continue
                child_path = f"{path}/{str(key).replace('~', '~0').replace('/', '~1')}"
                collect_scalars(child, child_path, limit)
            return
        if isinstance(value, (list, tuple)):
            return
        if isinstance(value, (str, int, float, bool)) or value is None:
            leaf = path.rsplit("/", 1)[-1]
            role = "state"
            if any(token in leaf for token in ("count", "cycle", "index", "sequence", "returncode")):
                role = "counter"
            elif any(token in leaf for token in ("failure", "error", "status", "class")):
                role = "error"
            elif "eligible" in leaf or "contract" in leaf:
                role = "contract"
            pointer_guide.append(
                {
                    "evidence_pointer": path,
                    "observed_value": copy.deepcopy(value),
                    "semantic_role": role,
                }
            )

    diagnosis_value = compact.get("diagnosis", {}).get("value")
    if isinstance(diagnosis_value, dict):
        collect_scalars(diagnosis_value, "/current_board_vcs_feedback/diagnosis/value")
    runner_value = compact.get("runner_report", {}).get("value")
    if isinstance(runner_value, dict):
        collect_scalars(runner_value, "/current_board_vcs_feedback/runner_report/value")
    if pointer_guide:
        compact["adaptive_observation_pointer_guide"] = {
            "authority": "current_board_vcs_feedback in the full package",
            "pointers_are_exact_scalars": True,
            "use_these_paths_verbatim": True,
            "entries": pointer_guide,
        }

    current_signal_epoch = _compact_current_layer3_signal_epoch(feedback)
    if current_signal_epoch:
        compact["current_signal_epoch"] = current_signal_epoch

    compact["semantic_projection"] = {
        "earliest_causal_real_tool_failure_preserved": True,
        "bounded_live_semantic_progress_and_stall_evidence_preserved": True,
        "short_first_error_context_preserved": True,
        "full_reports_remain_on_disk_outside_the_llm_prompt": True,
        "compile_failure_downstream_missing_output_cascade_omitted": True,
        "proven_semantic_stall_repetitions_and_noncausal_terminal_cascade_omitted": True,
        "complete_editable_sources_are_preserved_in_repair_source_bundle": True,
    }
    return _strip_layer3_execution_only_context(compact)


def _bootstrap_artifact_projection(
    artifact: Any,
    value_fields: tuple[str, ...],
) -> Any:
    """Keep the board bootstrap's design authority without duplicate catalogs."""

    if not isinstance(artifact, dict):
        return compact_for_retry(artifact)
    result = {
        key: copy.deepcopy(artifact.get(key))
        for key in ("path", "sha256", "source_path", "source_sha256")
        if artifact.get(key) is not None
    }
    value = _bound_artifact_value(artifact)
    if value:
        result["value"] = {
            key: copy.deepcopy(value.get(key))
            for key in value_fields
            if key in value
        }
    return result


def compact_board_bootstrap_repair_package(result: dict[str, Any]) -> dict[str, Any]:
    """Remove historical and duplicate context before the first board VCS run."""

    for key in (
        "current_board_vcs_feedback",
        "exact_board_repair_attempt_history",
        "adaptive_observation_state",
        "current_patch_application_feedback",
        "current_board_preflight_feedback",
    ):
        result.pop(key, None)

    context = result.get("exact_board_integration_repair_context")
    if isinstance(context, dict):
        adaptive = context.get("adaptive_design_inputs")
        if isinstance(adaptive, dict):
            projections = {
                "transformer_block_weight_catalog": (
                    "status",
                    "model_id",
                    "accelerator_scope",
                    "target_layer_count",
                    "layer_ids",
                    "per_layer_tensor_count",
                    "tensor_count",
                    "tensor_suffixes",
                    "tensors",
                    "complete_tensor_integrity_contract",
                    "scope_coverage_complete",
                    "source_checkpoint_sha256",
                ),
                "full_weight_image_manifest": (
                    "status",
                    "accelerator_scope",
                    "all_target_layers",
                    "bound_layer_count",
                    "target_layer_count",
                    "layer_order",
                    "canonical_stage_layouts",
                    "layer_segments",
                    "packed_tensor_hashes",
                    "image_sha256",
                    "word_bits",
                    "word_count",
                    "weight_bank_count",
                    "weight_bank_capacity_bytes",
                    "scope_coverage_complete",
                ),
                "full_layer_runtime_capture_contract": (
                    "status",
                    "accelerator_scope",
                    "target_layer_count",
                    "contract_sha256",
                    "connected_runtime_stream_contract_sha256",
                ),
                "full_runtime_image_manifest": (
                    "status",
                    "accelerator_scope",
                    "target_layer_count",
                    "image_sha256",
                    "layer_bindings",
                    "unique_segments",
                    "word_bits",
                    "word_count",
                    "scope_coverage_complete",
                ),
            }
            for key, fields in projections.items():
                if key in adaptive:
                    adaptive[key] = _bootstrap_artifact_projection(
                        adaptive[key], fields
                    )
            # The source index is a shared target for ABI/compile-plan refs.
            # Keep it once rather than duplicating its rows in every artifact.

    bundle = result.get("repair_source_bundle")
    if not isinstance(bundle, dict):
        return result
    editable = bundle.get("editable_contract")
    editable = editable if isinstance(editable, dict) else {}
    board_root = str(editable.get("board_integration_root") or "").rstrip("/")
    manifest = editable.get("current_board_manifest_file")
    manifest = manifest if isinstance(manifest, dict) else {}
    manifest_path = str(manifest.get("path") or "")
    required_markers = (
        "#board_axi_ddr_closure",
        "#hierarchical_binding_requirements_projection",
        "/input/target_board_profile.json",
    )
    retained_documents = []
    omitted_read_only_count = 0
    for document in bundle.get("documents", []):
        if not isinstance(document, dict):
            retained_documents.append(document)
            continue
        path = str(document.get("path") or "")
        keep = (
            bool(board_root and (path == board_root or path.startswith(board_root + "/")))
            or path == manifest_path
            or any(marker in path for marker in required_markers)
        )
        if keep:
            retained_documents.append(document)
        elif document.get("content_preservation"):
            omitted_read_only_count += 1
    bundle["documents"] = retained_documents
    if omitted_read_only_count:
        bundle["bootstrap_omitted_read_only_source_count"] = omitted_read_only_count
        bundle["bootstrap_omitted_read_only_source_policy"] = (
            "certified kernel interfaces remain in exact_board_integration_repair_context; "
            "the board agent must not edit their implementations"
        )

    authority = editable.get("board_manifest_rewrite_authority")
    if isinstance(authority, dict):
        expanded = authority.get("expanded_source_authority")
        if isinstance(expanded, dict) and "external_fixture_sources" in expanded:
            expanded["external_fixture_sources"] = {
                "status": "not_required",
                "reason": "compute_slot_axi functional boundary",
            }
        # Compile-plan coverage is materialized by the framework after the
        # Agent's bounded source/manifest edits; it is not an Agent decision.
        authority.pop("compile_source_coverage_authority", None)
    return result


def compact_board_preflight_repair_package(result: dict[str, Any]) -> dict[str, Any]:
    """Keep only the current deterministic board-preflight repair boundary.

    Before the first VCS run, historical VCS/adaptive state cannot explain a
    manifest-materialization failure.  The board agent needs the current
    preflight blockers, immutable authorities, and editable sources, not a
    second copy of earlier diagnostic machinery.
    """

    for key in (
        "capability_tool",
        "capability_analyzer_tool",
        "capability_probe",
        "capability_reports",
        "pre_patch_dependency_refresh",
        "failed_current_layer_gates",
        "semantic_template_baseline",
        "target_modules",
        "template_candidates",
        "generated_sources",
        "prior_localized_agent_feedback",
        "reference_builder_probe",
        "reference_builder_tool",
        "trusted_numeric_support",
        "trusted_numeric_support_compile",
        "current_board_vcs_feedback",
        "exact_board_repair_attempt_history",
        "adaptive_observation_state",
        "relevant_repair_experience",
        "relevant_project_knowledge",
    ):
        result.pop(key, None)
    # This phase is fully described by generation_phase_contract.  Exposing a
    # second enum to the Agent has caused label drift without adding authority.
    result.pop("generation_mode", None)
    return result


def _compact_failed_intervention_text(value: str, limit: int) -> str:
    value = re.sub(r"\b[0-9a-fA-F]{64}\b", "<content-id>", value)
    value = re.sub(r"(?<![A-Za-z0-9_])/(?:[^\s\"']+)", "<artifact>", value)
    return _bounded_live_error(value, limit)


def _compact_failed_exact_board_interventions(history: Any) -> list[dict[str, Any]]:
    """Project bounded negative experiments without paths or content identities."""

    if not isinstance(history, dict):
        return []
    response_history = history.get("intervention_response_history", {})
    transitions = (
        response_history.get("transitions", [])
        if isinstance(response_history, dict)
        else []
    )
    compact: list[dict[str, Any]] = []
    for transition in transitions[-3:]:
        if not isinstance(transition, dict):
            continue
        hypothesis = transition.get("agent_hypothesis", {})
        hypothesis = hypothesis if isinstance(hypothesis, dict) else {}
        prediction = hypothesis.get("causal_prediction", {})
        prediction = prediction if isinstance(prediction, dict) else {}
        observed = transition.get("observed_response", {})
        observed = observed if isinstance(observed, dict) else {}
        evaluation = transition.get("causal_prediction_evaluation", {})
        evaluation = evaluation if isinstance(evaluation, dict) else {}
        intervention = {
            key: _compact_failed_intervention_text(value, 1600)
            for key, value in (
                ("summary", hypothesis.get("summary")),
                ("root_cause", hypothesis.get("root_cause")),
                ("family", prediction.get("intervention_family")),
                ("target_frontier", prediction.get("target_frontier_id")),
            )
            if isinstance(value, str) and value.strip()
        }
        outcome = {
            key: copy.deepcopy(observed.get(key))
            for key in (
                "failure_class",
                "frontier_id",
                "zero_time_livelock",
                "frontier_response_metrics",
            )
            if observed.get(key) not in (None, {}, [])
        }
        first_error = observed.get("first_real_error")
        if isinstance(first_error, str) and first_error.strip():
            outcome["first_real_error"] = _compact_failed_intervention_text(
                first_error, 1200
            )
        prediction_result = {
            key: copy.deepcopy(evaluation.get(key))
            for key in ("status", "falsified_if")
            if evaluation.get(key) not in (None, "")
        }
        row = {
            "intervention": intervention,
            "real_tool_outcome": outcome,
            "prediction_result": prediction_result,
        }
        if intervention and outcome and row not in compact:
            compact.append(row)
    return compact


def _compact_current_patch_application_feedback(value: Any) -> dict[str, Any]:
    """Keep only the rejected transaction facts needed by the next Agent turn."""

    if not isinstance(value, dict) or value.get("status") != "ready":
        return {}
    compact = {
        key: copy.deepcopy(value[key])
        for key in ("status", "summary", "blockers")
        if value.get(key) not in (None, "", [])
    }
    application = value.get("patch_application", {})
    report = (
        application.get("value", {}) if isinstance(application, dict) else {}
    )
    if not isinstance(report, dict):
        return compact

    transaction = value.get("agent_transaction_rejection")
    if not isinstance(transaction, dict):
        transaction = report.get("agent_transaction_rejection")
    if isinstance(transaction, dict):
        compact["agent_transaction_rejection"] = {
            key: copy.deepcopy(transaction[key])
            for key in (
                "status",
                "failure_class",
                "blockers",
                "file_edits_were_not_applied",
                "real_tool_replay_required_before_retry",
                "rejected_file_edits",
            )
            if transaction.get(key) not in (None, "", [])
        }

    rejected = value.get("rejected_prior_failed_board_attempt")
    if not isinstance(rejected, dict):
        rejected = report.get("rejected_prior_failed_board_attempt")
    if not isinstance(rejected, dict):
        return compact
    candidate = rejected.get("candidate_board_source_state", {})
    candidate = candidate if isinstance(candidate, dict) else {}
    behavior = rejected.get("behavior_signature", {})
    if not isinstance(behavior, dict) or not behavior:
        behavior = rejected.get("real_tool_outcome", {})
    behavior = behavior if isinstance(behavior, dict) else {}
    compact["rejected_prior_failed_board_attempt"] = {
        **{
            key: copy.deepcopy(rejected[key])
            for key in ("iteration", "board_source_edits")
            if rejected.get(key) not in (None, "", [])
        },
        "candidate_board_source_state": {
            key: copy.deepcopy(candidate[key])
            for key in ("canonical_sha256", "candidate_changed_paths")
            if candidate.get(key) not in (None, "", [])
        },
        "real_tool_outcome": {
            key: copy.deepcopy(behavior[key])
            for key in (
                "failure_class",
                "first_real_error",
                "causal_progress_projection",
                "zero_time_livelock",
            )
            if behavior.get(key) not in (None, "", [])
        },
    }
    return compact


def compact_board_post_vcs_repair_package(result: dict[str, Any]) -> dict[str, Any]:
    """Keep the current board failure and complete source edit boundary.

    Compile/runtime repair does not need generation history, lower-layer source
    bodies, or framework-owned manifest rewrite indexes.  The executor retains
    those durable artifacts on disk and validates the Agent edit atomically.
    """

    # Keep only same-turn atomic edit feedback.  It tells the Agent that an
    # exact edit anchor was mechanically invalid, but carries no historical
    # hardware evidence and no execution/replay state.
    patch_feedback = _compact_current_patch_application_feedback(
        result.get("current_patch_application_feedback")
    )

    for key in (
        "capability_tool",
        "capability_analyzer_tool",
        "capability_probe",
        "capability_reports",
        "pre_patch_dependency_refresh",
        "failed_current_layer_gates",
        "semantic_template_baseline",
        "target_modules",
        "template_candidates",
        "generated_sources",
        "prior_localized_agent_feedback",
        "reference_builder_probe",
        "reference_builder_tool",
        "trusted_numeric_support",
        "trusted_numeric_support_compile",
        "prior_capability_producer_evidence",
        "current_repair_agent_disposition",
        "exact_board_repair_attempt_history",
        "adaptive_observation_state",
        "relevant_repair_experience",
        "relevant_project_knowledge",
        "current_board_preflight_feedback",
        "current_patch_application_feedback",
        "current_fresh_exact_source_provenance_replay",
        "exact_board_generation_policy",
        "policy",
        "run_dir",
        "source_sacg_state",
        "repair_step_id",
        "repair_scope",
        "repair_kind",
        "repair_gate",
        "violated_contract",
        "exact_board_integration_required",
        "single_layer_harness_required",
        "compaction_policy",
    ):
        result.pop(key, None)
    result.pop("generation_mode", None)
    if patch_feedback:
        result["current_patch_application_feedback"] = patch_feedback

    feedback = result.get("current_board_vcs_feedback", {})
    diagnosis_artifact = (
        feedback.get("diagnosis", {}) if isinstance(feedback, dict) else {}
    )
    diagnosis = (
        diagnosis_artifact.get("value", {})
        if isinstance(diagnosis_artifact, dict)
        else {}
    )
    runner_artifact = (
        feedback.get("runner_report", {}) if isinstance(feedback, dict) else {}
    )
    runner = (
        runner_artifact.get("value", {})
        if isinstance(runner_artifact, dict)
        else {}
    )
    failure_evidence = (
        diagnosis.get("failure_evidence", {})
        if isinstance(diagnosis, dict)
        else {}
    )
    compile_result = (
        failure_evidence.get("compile", {})
        if isinstance(failure_evidence, dict)
        else {}
    )
    if not compile_result and isinstance(runner, dict):
        compile_result = runner.get("compile", {})
    failure_class = str(
        (
            failure_evidence.get("failure_class")
            if isinstance(failure_evidence, dict)
            else ""
        )
        or (diagnosis.get("failure_class") if isinstance(diagnosis, dict) else "")
        or (runner.get("failure_class") if isinstance(runner, dict) else "")
        or ""
    )
    compile_phase_failure = bool(
        failure_class in {"vcs_compile_failure", "vcs_elaboration_failure"}
        or (
            isinstance(compile_result, dict)
            and compile_result.get("status") == "fail"
        )
    )

    context = result.get("exact_board_integration_repair_context")
    if isinstance(context, dict):
        adaptive = context.get("adaptive_design_inputs")
        if isinstance(adaptive, dict):
            required_keys = [
                "target_model",
                "connected_kernel_lifecycle_authority",
            ]
            if failure_class == "vcs_runtime_zero_time_livelock":
                required_keys.append("debug_observability_authority")
            elif not compile_phase_failure:
                required_keys.extend(
                    [
                        "model_derived_memory_layout",
                        "semantic_board_reference_artifacts",
                        "debug_observability_authority",
                        "runtime_image_artifact",
                        "board_memory_runtime_preparation",
                    ]
                )
            required_context = {}
            for key in required_keys:
                if key not in adaptive:
                    continue
                value = adaptive[key]
                if (
                    failure_class == "vcs_runtime_zero_time_livelock"
                    and isinstance(value, dict)
                    and isinstance(value.get("value"), dict)
                ):
                    required_context[key] = {
                        "value": copy.deepcopy(value["value"])
                    }
                else:
                    required_context[key] = copy.deepcopy(value)
            context["adaptive_design_inputs"] = required_context
            context["prompt_slice_policy"] = {
                "failure_phase": "compile" if compile_phase_failure else "runtime",
                "compile_phase_omits_runtime_only_context": compile_phase_failure,
                "full_durable_context_remains_on_disk": True,
            }

    bundle = result.get("repair_source_bundle")
    if not isinstance(bundle, dict):
        return result
    editable = bundle.get("editable_contract")
    editable = editable if isinstance(editable, dict) else {}
    compact_editable = {
        key: copy.deepcopy(editable[key])
        for key in (
            "allowed_create_or_replace_roots",
            "allowed_exact_files",
            "board_integration_repair_authorized",
            "board_integration_root",
            "current_board_manifest_file",
            "current_board_source_files",
            "forbidden",
            "read_only_generated_dut_sources",
            "user_sample_project_sources_read_only",
        )
        if key in editable
    }
    manifest = compact_editable.get("current_board_manifest_file")
    manifest_path = (
        str(manifest.get("path") or "") if isinstance(manifest, dict) else ""
    )
    causal_feedback_text = json.dumps(feedback, sort_keys=True)
    manifest_content_required = bool(
        failure_class != "vcs_runtime_zero_time_livelock"
        and (
            not compile_phase_failure
            or (
                manifest_path
                and (
                    manifest_path in causal_feedback_text
                    or Path(manifest_path).name in causal_feedback_text
                )
            )
        )
    )
    current_rows = compact_editable.get("current_board_source_files", [])
    if isinstance(current_rows, dict) and current_rows.get("encoding") == (
        "spatialaccagent.lossless_dictionary_column_rows.v1"
    ):
        try:
            current_rows = _decode_lossless_columnar_rows(current_rows)
        except (TypeError, ValueError):
            current_rows = []
    if isinstance(current_rows, list):
        compact_editable["current_board_source_files"] = copy.deepcopy(
            current_rows
        )
    current_source_paths = {
        str(row.get("path") or "")
        for row in current_rows
        if isinstance(row, dict) and row.get("path")
    }
    documents = []
    for row in bundle.get("documents", []):
        if not isinstance(row, dict):
            continue
        path = str(row.get("path") or "")
        source_path = path.split("#", 1)[0]
        complete_source = isinstance(row.get("content"), str) and bool(
            row.get("content")
        )
        document = copy.deepcopy(row)
        if (
            manifest_content_required
            and manifest_path
            and source_path == manifest_path
            and not isinstance(document.get("json_content"), dict)
            and complete_source
        ):
            try:
                parsed_manifest = json.loads(document["content"])
            except (TypeError, ValueError):
                parsed_manifest = None
            if isinstance(parsed_manifest, dict):
                document["json_content"] = parsed_manifest
        complete_manifest = (
            manifest_content_required
            and bool(manifest_path)
            and source_path == manifest_path
            and isinstance(document.get("json_content"), dict)
        )
        board_source = (
            complete_source
            and source_path in current_source_paths
        )
        cited_read_only_source = bool(
            complete_source
            and source_path not in current_source_paths
            and (
                source_path in causal_feedback_text
                or Path(source_path).name in causal_feedback_text
            )
        )
        if complete_manifest or board_source or cited_read_only_source:
            if board_source:
                document.pop("content_sha256", None)
            documents.append(document)

    if not manifest_content_required:
        compact_editable.pop("current_board_manifest_file", None)

    compact_bundle = {
        key: copy.deepcopy(bundle[key])
        for key in (
            "schema_version",
            "status",
            "verification_scope",
            "bundle_profile",
            "all_documents_complete",
            "trusted_numeric_support",
        )
        if key in bundle
    }
    if (
        failure_class != "vcs_runtime_zero_time_livelock"
        and "generated_module_inventory" in bundle
    ):
        compact_bundle["generated_module_inventory"] = copy.deepcopy(
            bundle["generated_module_inventory"]
        )
    compact_bundle.update(
        {
            "document_count": len(documents),
            "editable_contract": compact_editable,
            "documents": documents,
            "manifest_content_required": manifest_content_required,
            "compaction_policy": {
                "current_real_vcs_failure_only": True,
                "complete_current_board_sources_preserved": True,
                "editable_manifest_included_only_for_runtime_or_manifest_causality": True,
                "framework_owned_rewrite_indexes_omitted": True,
                "passed_lower_layer_source_bodies_omitted": True,
                "read_only_sample_source_bodies_omitted_after_interface_binding": True,
                "causally_cited_read_only_source_body_preserved": True,
            },
        }
    )
    result["repair_source_bundle"] = compact_bundle
    return _strip_layer3_execution_only_context(result)


def current_board_to_lower_layer_contradiction(value: Any) -> dict[str, Any]:
    """Keep the decisive board-to-kernel proof at the front of a repair prompt."""

    if not isinstance(value, dict) or value.get("status") != "proven":
        return {}
    evidence = value.get("evidence", {})
    evidence = evidence if isinstance(evidence, dict) else {}
    return {
        key: copy.deepcopy(value.get(key))
        for key in ("schema_version", "status", "target_debug_layer")
        if value.get(key) is not None
    } | {
        "source_binding": copy.deepcopy(evidence.get("source_binding", {})),
        "direct_kernel_boundary_observations": copy.deepcopy(
            evidence.get("direct_kernel_boundary_observations", {})
        ),
        "causal_localization": copy.deepcopy(
            evidence.get("causal_localization", {})
        ),
    }


def has_proven_board_to_lower_layer_contradiction(package: Any) -> bool:
    return bool(
        isinstance(package, dict)
        and current_board_to_lower_layer_contradiction(
            package.get("current_board_to_lower_layer_contradiction")
        )
    )


def compact_verification_capability_repair_package(package: dict[str, Any]) -> dict[str, Any]:
    board_semantic_rtl_repair = (
        package.get("generation_mode") == "board_semantic_rtl_repair"
    )
    generation_phase = package.get("generation_phase_contract", {})
    bootstrap_board_generation = (
        isinstance(generation_phase, dict)
        and generation_phase.get("status") == "generation_required_before_probe"
    )
    deterministic_preflight_repair = (
        isinstance(generation_phase, dict)
        and generation_phase.get("status") == "repair_deterministic_preflight"
    )
    post_vcs_board_repair = (
        not board_semantic_rtl_repair
        and
        isinstance(generation_phase, dict)
        and generation_phase.get("status") == "repair_existing_board_sources"
        and generation_phase.get("current_vcs_feedback_ready") is True
    )
    result: dict[str, Any] = {
        key: package.get(key)
        for key in (
            "schema_version",
            "stage",
            "repair_step_id",
            "run_dir",
            "verification_scope",
            "debug_layer",
            "repair_scope",
            "repair_kind",
            "repair_gate",
            "violated_contract",
            "exact_board_integration_required",
            "single_layer_harness_required",
            "source_sacg_state",
        )
        if key in package
    }
    for key in (
        "capability_tool",
        "capability_analyzer_tool",
        "capability_probe",
        "capability_reports",
        "pre_patch_dependency_refresh",
        "failed_current_layer_gates",
        "policy",
        "semantic_template_baseline",
        "target_modules",
        "template_candidates",
        "generated_sources",
        "generation_mode",
        "generation_phase_contract",
        "exact_board_generation_policy",
        "prior_localized_agent_feedback",
        "relevant_repair_experience",
        "relevant_project_knowledge",
        "reference_builder_probe",
        "reference_builder_tool",
        "trusted_numeric_support",
        "trusted_numeric_support_compile",
        "current_repair_agent_disposition",
        "prior_capability_producer_evidence",
    ):
        if key in package:
            result[key] = (
                copy.deepcopy(package[key])
                if key
                in {
                    "generation_phase_contract",
                    "relevant_repair_experience",
                    "relevant_project_knowledge",
                    "current_repair_agent_disposition",
                    "prior_capability_producer_evidence",
                }
                else compact_for_retry(package[key])
            )
    contradiction = current_board_to_lower_layer_contradiction(
        package.get("current_board_to_lower_layer_contradiction")
    )
    if contradiction:
        result["current_board_to_lower_layer_contradiction"] = contradiction
        result["repair_routing_priority"] = {
            "status": "authoritative",
            "instruction": (
                "Repair only the current hash-bound lower-layer target. Older "
                "board audit records remain evidence but cannot redirect this repair."
            ),
        }
    if isinstance(package.get("exact_board_repair_attempt_history"), dict):
        result["exact_board_repair_attempt_history"] = copy.deepcopy(
            package["exact_board_repair_attempt_history"]
        )
    current_vcs_feedback_present = isinstance(
        package.get("current_board_vcs_feedback"), dict
    )
    if isinstance(package.get("adaptive_observation_state"), dict):
        if board_semantic_rtl_repair:
            result["adaptive_observation_state"] = (
                _compact_current_adaptive_observation_state(
                    package["adaptive_observation_state"],
                    current_vcs_feedback_present=current_vcs_feedback_present,
                )
            )
        elif not post_vcs_board_repair:
            result["adaptive_observation_state"] = copy.deepcopy(
                package["adaptive_observation_state"]
            )
    if isinstance(package.get("adaptive_observation_routing"), dict):
        result["adaptive_observation_routing"] = copy.deepcopy(
            package["adaptive_observation_routing"]
        )
    if isinstance(package.get("compiled_signal_catalog"), dict):
        result["compiled_signal_catalog"] = copy.deepcopy(
            package["compiled_signal_catalog"]
        )
    if board_semantic_rtl_repair:
        # The hot-loop package already carries current_board_vcs_feedback as
        # the single current evidence source.  These fields are durable
        # producer/recheck copies and add no new decision authority here.
        result.pop("capability_probe", None)
        result.pop("prior_capability_producer_evidence", None)
    observation_lock = _current_adaptive_observation_decision_lock(package)
    if observation_lock:
        result["adaptive_observation_decision_lock"] = observation_lock
    preflight_feedback_ready = (
        isinstance(package.get("current_board_preflight_feedback"), dict)
        and package["current_board_preflight_feedback"].get("status") == "ready"
    )
    if (
        not preflight_feedback_ready
        and isinstance(package.get("current_board_vcs_feedback"), dict)
    ):
        result["current_board_vcs_feedback"] = _compact_board_vcs_feedback(
            package["current_board_vcs_feedback"]
        )
    if isinstance(package.get("current_board_preflight_feedback"), dict):
        result["current_board_preflight_feedback"] = _compact_board_preflight_feedback(
            package["current_board_preflight_feedback"]
        )
    if isinstance(package.get("current_patch_application_feedback"), dict):
        result["current_patch_application_feedback"] = copy.deepcopy(
            package["current_patch_application_feedback"]
        )
    fresh_replay = package.get("current_fresh_exact_source_provenance_replay")
    if isinstance(fresh_replay, dict) and fresh_replay.get("status") == "ready":
        replay_projection = {
            key: copy.deepcopy(fresh_replay.get(key))
            for key in (
                "schema_version",
                "status",
                "replay_status",
                "summary",
                "execution_generation_sha256",
            )
            if fresh_replay.get(key) is not None
        }
        decision = fresh_replay.get("decision")
        if isinstance(decision, dict):
            replay_projection["decision"] = {
                key: copy.deepcopy(decision.get(key))
                for key in (
                    "schema_version",
                    "mode",
                    "frontier_id",
                    "evidence_refs",
                    "field_observations",
                    "rationale",
                )
                if decision.get(key) is not None
            }
        result["current_fresh_exact_source_provenance_replay"] = (
            replay_projection
        )
    context = package.get("exact_board_integration_repair_context", {})
    if isinstance(context, dict):
        result["exact_board_integration_repair_context"] = compact_exact_board_integration_context(context)
    bundle = package.get("repair_source_bundle", {})
    if isinstance(bundle, dict):
        context = package.get("exact_board_integration_repair_context", {})
        adaptive = (
            context.get("adaptive_design_inputs", {})
            if isinstance(context, dict)
            else {}
        )
        certified_binding = _bound_artifact_value(
            adaptive.get("certified_single_layer_binding", {})
            if isinstance(adaptive, dict)
            else {}
        )
        single_layer = (
            certified_binding.get("single_layer_harness", {})
            if isinstance(certified_binding.get("single_layer_harness"), dict)
            else {}
        )
        lifecycle_modules = {
            str(value)
            for value in single_layer.get("generated_dut_modules", [])
            if str(value)
        }
        # A Layer-3 current-signal turn starts with an observation or a small
        # board-source repair. Passing the full certified kernel closure makes
        # the prompt exceed provider context limits before the Agent can act.
        # Keep source identities for the closure, but preserve full text only
        # for the generated board owners selected below.
        if board_semantic_rtl_repair:
            lifecycle_modules = set()
        identity = _bound_artifact_value(
            adaptive.get("exact_board_source_identity", {})
            if isinstance(adaptive, dict)
            else {}
        )
        selected_closure = identity.get("selected_simulation_source_closure", {})
        selected_closure = selected_closure if isinstance(selected_closure, dict) else {}
        selected_source_rows = [
            row
            for row in selected_closure.get("source_files", [])
            if isinstance(row, dict)
            and row.get("closure_role")
            in {"exact_sample_top", "compute_slot_implementation"}
        ]
        selected_source_paths = {
            str(row.get(field))
            for row in selected_source_rows
            for field in ("path", "local_path", "remote_path", "staged_path")
            if row.get(field)
        }
        selected_source_hashes = {
            str(row.get(field))
            for row in selected_source_rows
            for field in ("sha256", "local_sha256", "remote_sha256")
            if row.get(field)
        }
        editable = (
            bundle.get("editable_contract", {})
            if isinstance(bundle.get("editable_contract"), dict)
            else {}
        )
        current_board_sources = _decode_lossless_columnar_rows_if_present(
            editable.get("current_board_source_files", [])
        )
        current_board_manifest = (
            editable.get("current_board_manifest_file", {})
            if isinstance(editable.get("current_board_manifest_file"), dict)
            else {}
        )
        if board_semantic_rtl_repair:
            # The semantic board repair route needs the current generated RTL
            # documents so the Agent can make a source-bound edit.  Keep this
            # bounded to the authority's editable closure; do not restore the
            # full certified kernel/source history.
            selected_source_paths.update(
                str(value)
                for value in editable.get("localized_allowed_exact_files", [])
                if str(value)
            )
        else:
            for field in (
                "read_only_template_sources",
                "approved_bounded_template_repair_exact_files",
                "allowed_exact_files",
            ):
                selected_source_paths.update(
                    str(value)
                    for value in editable.get(field, [])
                    if str(value)
                )
        editable_roots = [
            str(value).rstrip("/")
            for value in editable.get("allowed_create_or_replace_roots", [])
            if str(value).rstrip("/")
        ]
        selected_source_paths.update(
            path
            for row in bundle.get("documents", [])
            if isinstance(row, dict)
            for path in (str(row.get("path") or ""),)
            if path
            and any(path == root or path.startswith(root + "/") for root in editable_roots)
        )
        if package.get("verification_scope") == "operator_leaf_closure":
            exact_operator_contract_markers = (
                "semantic_testbench_manifest.json#operator_leaf_closure_execution_projection",
                "dut_weight_binding_requirements.json#operator_leaf_closure_requirements_projection",
            )
            for row in bundle.get("documents", []):
                if not isinstance(row, dict) or not any(
                    marker in str(row.get("path") or "")
                    for marker in exact_operator_contract_markers
                ):
                    continue
                selected_source_paths.add(str(row.get("path")))
        if current_board_manifest.get("path"):
            selected_source_paths.add(str(current_board_manifest.get("path")))
        if current_board_manifest.get("sha256"):
            selected_source_hashes.add(str(current_board_manifest.get("sha256")))
        selected_source_paths.update(
            str(row.get("path"))
            for row in current_board_sources
            if isinstance(row, dict) and row.get("path")
        )
        selected_source_hashes.update(
            str(row.get("sha256"))
            for row in current_board_sources
            if isinstance(row, dict) and row.get("sha256")
        )
        single_layer_authority_selected = False
        if package.get("verification_scope") == "single_layer_closure":
            exact_names = {
                "ConnectedSingleLayerHarness.scala",
                "DecoderBlock.scala",
                "semantic_testbench_generator.py",
                "single_layer_functional_report.json",
                "single_layer_golden_compare.json",
                "case_single_layer_semantic_evidence.json",
                "agent_patch_application.json",
                "agent_requested_validation.json",
                "dut_weight_binding_materialization.json",
            }
            exact_projection_markers = {
                "#single_layer_closure_execution_projection",
                "#single_layer_closure_requirements_projection",
                "#single_layer_closure_binding_merge_authority",
            }
            for row in bundle.get("documents", []):
                if not isinstance(row, dict):
                    continue
                row_path = str(row.get("path") or "")
                if (
                    Path(row_path.split("#", 1)[0]).name not in exact_names
                    and not any(
                        marker in row_path for marker in exact_projection_markers
                    )
                ):
                    continue
                single_layer_authority_selected = True
                selected_source_paths.update(
                    str(row.get(field))
                    for field in ("path", "source_path")
                    if row.get(field)
                )
                selected_source_hashes.update(
                    str(row.get(field))
                    for field in ("sha256", "source_sha256", "content_sha256")
                    if row.get(field)
                )
        fixture_top_documents = [
            row
            for row in bundle.get("documents", [])
            if isinstance(row, dict) and row.get("external_fixture_example_tops")
        ]
        lifecycle_modules.update(
            str(value)
            for row in fixture_top_documents
            for value in row.get("external_fixture_example_tops", [])
            if str(value)
        )
        selected_source_paths.update(
            str(row.get(field))
            for row in fixture_top_documents
            for field in ("path", "source_path")
            if row.get(field)
        )
        selected_source_hashes.update(
            str(row.get(field))
            for row in fixture_top_documents
            for field in ("sha256", "source_sha256", "content_sha256")
            if row.get(field)
        )
        compact_bundle = compact_repair_source_bundle(
            bundle,
            preserve_full_text_modules=lifecycle_modules,
            preserve_full_text_paths=selected_source_paths,
            preserve_full_text_hashes=selected_source_hashes,
        )
        if package.get("verification_scope") == "single_layer_closure":
            compact_bundle["single_layer_generation_authority"] = {
                "status": (
                    "complete" if single_layer_authority_selected else "missing"
                ),
                "complete_editable_connected_harness_preserved": True,
                "complete_connected_block_interface_preserved": True,
                "complete_v2_pipeline_contract_preserved": True,
                "complete_current_failure_reports_preserved": True,
                "binding_manifest_update_mode": "hash_bound_merge_json",
                "binding_manifest_omitted_siblings_preserved": True,
            }
        adaptive_paths: set[str] = set()
        adaptive_hashes: set[str] = set()
        if isinstance(adaptive, dict):
            for key in (
                "exact_board_source_identity",
                "transformer_block_weight_catalog",
                "vivado_vcs_compile_authority",
                "board_memory_runtime_contract",
                "full_weight_image_manifest",
                "runtime_capture_contract",
                "full_layer_runtime_capture_contract",
                "full_runtime_image_manifest",
                "runtime_image_artifact",
                "board_memory_runtime_preparation",
                "certified_single_layer_binding",
                "external_simulation_fixture",
                "debug_observability_authority",
            ):
                row = adaptive.get(key)
                if isinstance(row, dict) and row.get("path"):
                    adaptive_paths.add(str(row.get("path")))
                if isinstance(row, dict) and row.get("sha256"):
                    adaptive_hashes.add(str(row.get("sha256")))
        if (
            adaptive_paths
            and isinstance(compact_bundle.get("documents"), list)
            and not board_semantic_rtl_repair
        ):
            compact_bundle["documents"] = [
                row
                for row in compact_bundle["documents"]
                if not isinstance(row, dict)
                or row.get("content_preservation")
                or (
                    str(row.get("path") or "") not in adaptive_paths
                    and str(row.get("sha256") or "") not in adaptive_hashes
                    and str(row.get("source_sha256") or "") not in adaptive_hashes
                )
            ]
            compact_bundle["documents_omitted_as_adaptive_context_duplicates"] = sorted(adaptive_paths)
        fixture_document_refs = [
            {
                "source_id": str(row.get("external_fixture_source_id") or ""),
                "path": str(row.get("path") or ""),
                "sha256": str(row.get("sha256") or row.get("content_sha256") or ""),
            }
            for row in compact_bundle.get("documents", [])
            if isinstance(row, dict)
            and row.get("external_fixture_source_id")
            and not row.get("content_preservation")
        ]
        if fixture_document_refs:
            compact_bundle["documents"] = [
                row
                for row in compact_bundle.get("documents", [])
                if not (
                    isinstance(row, dict)
                    and row.get("external_fixture_source_id")
                    and not row.get("content_preservation")
                )
            ]
            compact_bundle[
                "documents_omitted_as_external_fixture_compile_source_index"
            ] = {
                "$ref": (
                    "#/verification_capability_repair_package/repair_source_bundle/"
                    "editable_contract/board_manifest_rewrite_authority/"
                    "expanded_source_authority/external_fixture_sources"
                ),
                "source_count": len(fixture_document_refs),
                "source_ids": _encoded_column(
                    [row["source_id"] for row in fixture_document_refs]
                ),
                "canonical_sha256": _canonical_json_sha256(fixture_document_refs),
                "policy": (
                    "path/hash/module declarations come from the expanded manifest-rewrite source authority; "
                    "the complete selected example top remains in repair_source_bundle"
                ),
            }
        if (
            package.get("verification_scope") == "board_axi_ddr_closure"
            and not board_semantic_rtl_repair
        ):
            board_reference_markers = (
                "#exact_capability_consumer_functions",
                "#board_axi_ddr_closure",
                "#hierarchical_binding_requirements_projection",
                "/input/target_board_profile.json",
            )
            omitted_lower_layer_history = [
                {
                    "path": str(row.get("path") or ""),
                    "sha256": str(
                        row.get("sha256")
                        or row.get("content_sha256")
                        or row.get("source_sha256")
                        or ""
                    ),
                }
                for row in compact_bundle.get("documents", [])
                if isinstance(row, dict)
                and not row.get("content_preservation")
                and not any(
                    marker in str(row.get("path") or "")
                    for marker in board_reference_markers
                )
            ]
            if omitted_lower_layer_history:
                compact_bundle["documents"] = [
                    row
                    for row in compact_bundle.get("documents", [])
                    if not (
                        isinstance(row, dict)
                        and not row.get("content_preservation")
                        and not any(
                            marker in str(row.get("path") or "")
                            for marker in board_reference_markers
                        )
                    )
                ]
                compact_bundle["documents_omitted_as_certified_lower_layer_history"] = {
                    "document_count": len(omitted_lower_layer_history),
                    "canonical_sha256": _canonical_json_sha256(
                        omitted_lower_layer_history
                    ),
                    "policy": (
                        "passed lower-layer history is superseded by the bound promotion certificate, "
                        "complete certified binding and preserved connected-kernel lifecycle source; "
                        "framework checker and runner implementations are execution machinery already "
                        "captured by the task rules and exact consumer contract"
                    ),
                }
        closure = identity.get("selected_simulation_source_closure", {})
        source_rows = closure.get("source_files", []) if isinstance(closure, dict) else []
        board_source_lookup: dict[str, int] = {}
        board_hash_lookup: dict[str, int] = {}
        for index, source in enumerate(source_rows if isinstance(source_rows, list) else []):
            if not isinstance(source, dict):
                continue
            for field in ("path", "local_path", "remote_path", "staged_path"):
                if source.get(field):
                    board_source_lookup[str(source[field])] = index
            for field in ("sha256", "local_sha256", "remote_sha256"):
                if source.get(field):
                    board_hash_lookup[str(source[field])] = index
        represented_rows: list[int] = []
        retained_documents: list[Any] = []
        for document in compact_bundle.get("documents", []):
            if not isinstance(document, dict) or document.get("content_preservation"):
                retained_documents.append(document)
                continue
            candidates = {
                str(document.get(field))
                for field in ("path", "source_path")
                if document.get(field)
            }
            hashes = {
                str(document.get(field))
                for field in ("sha256", "source_sha256", "content_sha256")
                if document.get(field)
            }
            matched = next(
                (board_source_lookup[value] for value in candidates if value in board_source_lookup),
                None,
            )
            if matched is None:
                matched = next(
                    (board_hash_lookup[value] for value in hashes if value in board_hash_lookup),
                    None,
                )
            if matched is None:
                retained_documents.append(document)
            else:
                represented_rows.append(matched)
        if represented_rows and not board_semantic_rtl_repair:
            compact_bundle["documents"] = retained_documents
            compact_bundle["documents_omitted_as_shared_board_source_index"] = {
                "$ref": (
                    "#/verification_capability_repair_package/repair_source_bundle/"
                    "editable_contract/board_manifest_rewrite_authority/"
                    "expanded_source_authority/sample_sources"
                ),
                "source_row_ranges": _contiguous_index_ranges(represented_rows),
                "source_count": len(represented_rows),
                "policy": (
                    "source semantic/module identity comes from the shared index; complete path/hash transport metadata remains "
                    "bound by exact_board_source_identity and the Vivado compile-authority artifact hashes"
                ),
            }
        current_manifest_path = str(current_board_manifest.get("path") or "")
        current_manifest_sha = str(current_board_manifest.get("sha256") or "")
        if current_manifest_path:
            editable_manifest_present = any(
                isinstance(row, dict)
                and row.get("content_preservation")
                and str(row.get("path") or "") == current_manifest_path
                and (
                    isinstance(row.get("json_content"), dict)
                    or bool(row.get("content"))
                )
                for row in compact_bundle.get("documents", [])
            )
            if editable_manifest_present:
                omitted_manifest_projections = [
                    {
                        "path": str(row.get("path") or ""),
                        "source_path": str(row.get("source_path") or ""),
                        "sha256": str(
                            row.get("sha256")
                            or row.get("source_sha256")
                            or row.get("content_sha256")
                            or ""
                        ),
                    }
                    for row in compact_bundle.get("documents", [])
                    if isinstance(row, dict)
                    and row.get("projection")
                    and (
                        str(row.get("path") or "").split("#", 1)[0]
                        == current_manifest_path
                        or str(row.get("source_path") or "") == current_manifest_path
                    )
                ]
                if omitted_manifest_projections:
                    compact_bundle["documents"] = [
                        row
                        for row in compact_bundle.get("documents", [])
                        if not (
                            isinstance(row, dict)
                            and row.get("projection")
                            and (
                                str(row.get("path") or "").split("#", 1)[0]
                                == current_manifest_path
                                or str(row.get("source_path") or "")
                                == current_manifest_path
                            )
                        )
                    ]
                    compact_bundle[
                        "documents_omitted_as_current_editable_manifest_duplicates"
                    ] = {
                        "document_count": len(omitted_manifest_projections),
                        "canonical_sha256": _canonical_json_sha256(
                            omitted_manifest_projections
                        ),
                        "policy": (
                            "the complete current manifest is already supplied as an editable "
                            "hash-bound JSON document; same-source projections are duplicate"
                        ),
                    }
                context_projection = result.get("exact_board_integration_repair_context")
                adaptive_projection = (
                    context_projection.get("adaptive_design_inputs", {})
                    if isinstance(context_projection, dict)
                    else {}
                )
                if isinstance(adaptive_projection, dict):
                    previous_binding = adaptive_projection.get(
                        "certified_single_layer_binding", {}
                    )
                    previous_binding = (
                        previous_binding
                        if isinstance(previous_binding, dict)
                        else {}
                    )
                    adaptive_projection["certified_single_layer_binding"] = {
                        "path": previous_binding.get("path")
                        or current_manifest_path,
                        "sha256": previous_binding.get("sha256")
                        or current_manifest_sha,
                        "editable_manifest_document": {
                            "$ref": (
                                "#/verification_capability_repair_package/"
                                "repair_source_bundle/documents"
                            ),
                            "path": current_manifest_path,
                            "sha256": current_manifest_sha,
                            "complete_agent_owned_json_content_supplied": True,
                            "certified_lower_layer_fields_hash_bound_and_omitted": True,
                            "framework_materialized_vcs_compile_plan_may_be_omitted": True,
                        },
                        "compaction_policy": {
                            "complete_agent_owned_manifest_supplied_once_as_editable_json_document": True,
                            "stage_harnesses_and_single_layer_harness_are_restored_from_pre_edit_manifest": True,
                            "original_manifest_bound_by_path_and_sha256": True,
                        },
                    }
        _compact_board_rewrite_redundancy(
            compact_bundle,
            bundle,
            result.get("exact_board_integration_repair_context"),
        )
        result["repair_source_bundle"] = compact_bundle
    result["compaction_policy"] = {
        "schema_version": PROMPT_COMPACTION_PROTOCOL,
        "full_context_replaced_by_hash_bound_projection": True,
        "semantic_requirements_preserved": True,
        "file_edits_return_complete_create_replace_or_hash_bound_unique_text_replacements": True,
    }
    if bootstrap_board_generation:
        return compact_board_bootstrap_repair_package(result)
    if deterministic_preflight_repair:
        return compact_board_preflight_repair_package(result)
    if post_vcs_board_repair:
        return compact_board_post_vcs_repair_package(result)
    return result


def compact_bound_artifact(value: Any) -> Any:
    if not isinstance(value, dict):
        return compact_for_retry(value)
    if "value" not in value:
        text = json.dumps(value, sort_keys=True)
        return value if len(text.encode("utf-8")) <= 250_000 else compact_for_retry(value)
    artifact_value = value.get("value")
    projected: dict[str, Any] = {
        key: value.get(key)
        for key in ("path", "sha256", "source_path", "source_sha256")
        if key in value
    }
    if isinstance(artifact_value, dict):
        if len(_canonical_json(artifact_value).encode("utf-8")) <= 64_000:
            projected["value"] = artifact_value
        else:
            projected["value"] = _json_document_projection(artifact_value)
    else:
        projected["value"] = compact_for_retry(artifact_value)
    return projected


def _columnarize_record_lists(value: Any, *, minimum_rows: int = 2) -> Any:
    if isinstance(value, list):
        transformed = [_columnarize_record_lists(item, minimum_rows=minimum_rows) for item in value]
        if len(transformed) >= minimum_rows and all(isinstance(item, dict) for item in transformed):
            return _lossless_columnar_rows(transformed)
        return transformed
    if isinstance(value, dict):
        return {
            str(key): _columnarize_record_lists(child, minimum_rows=minimum_rows)
            for key, child in value.items()
        }
    return value


def _decode_columnarized_record_lists(value: Any) -> Any:
    """Inverse used to prove recursive fixture projections remain lossless."""

    if isinstance(value, dict) and value.get("encoding") == (
        "spatialaccagent.lossless_dictionary_column_rows.v1"
    ):
        return [
            _decode_columnarized_record_lists(row)
            for row in _decode_lossless_columnar_rows(value)
        ]
    if isinstance(value, dict):
        return {
            str(key): _decode_columnarized_record_lists(child)
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [_decode_columnarized_record_lists(child) for child in value]
    return value


def _fixture_source_view_reference(
    rows: Any,
    compile_sources: list[dict[str, Any]],
    pointer: str,
) -> Any:
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        return _columnarize_record_lists(rows)
    by_row = {
        _canonical_json(row): index for index, row in enumerate(compile_sources)
    }
    indices = [by_row.get(_canonical_json(row)) for row in rows]
    if any(index is None for index in indices):
        return _columnarize_record_lists(rows)
    return {
        "$ref": pointer,
        "row_indices": [int(index) for index in indices],
        "row_count": len(rows),
        "canonical_sha256": _canonical_json_sha256(rows),
    }


def _fixture_membership_projection(rows: Any) -> dict[str, Any]:
    records = [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []
    return {
        "row_count": len(records),
        "canonical_sha256": _canonical_json_sha256(records),
        "members": _lossless_columnar_rows(
            [
                {
                    key: row.get(key)
                    for key in (
                        "source_id",
                        "classification",
                    )
                    if key in row
                }
                for row in records
            ]
        ),
    }


def _compact_fixture_provider(
    provider: dict[str, Any],
    provider_group_configurations: dict[str, tuple[int, dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    projected = {
        key: copy.deepcopy(provider.get(key))
        for key in (
            "component_name",
            "diagnostic",
            "example",
            "fileset_count",
            "group_id",
            "ip_file",
            "source_part",
            "status",
        )
        if key in provider
    }
    ip_properties = provider.get("ip_properties", {})
    group_match = (provider_group_configurations or {}).get(str(provider.get("group_id") or ""))
    if isinstance(ip_properties, dict) and group_match:
        group_index, group_configuration = group_match
        structured_configuration = group_configuration.get("configuration", {})
        if not isinstance(structured_configuration, dict):
            structured_configuration = {}
        projected["ip_properties"] = {
            "configuration_ref": {
                "$ref": (
                    "#/verification_capability_repair_package/exact_board_integration_repair_context/"
                    "adaptive_design_inputs/external_simulation_fixture/value/authority/"
                    f"provider_groups/{group_index}/configuration/configuration"
                )
            },
            "additional_properties": {
                str(key): copy.deepcopy(child)
                for key, child in ip_properties.items()
                if key not in structured_configuration
            },
            "complete_properties_contract": {
                "property_count": len(ip_properties),
                "canonical_sha256": _canonical_json_sha256(ip_properties),
                "all_structured_configuration_values_preserved_by_authority_ref": True,
            },
        }
    else:
        projected["ip_properties"] = copy.deepcopy(ip_properties)
    filesets = []
    for fileset in provider.get("filesets", []):
        if not isinstance(fileset, dict):
            continue
        row = {
            key: copy.deepcopy(fileset.get(key))
            for key in (
                "compile_order_missing_instance_diagnostics",
                "diagnostic",
                "export_diagnostic",
                "export_status",
                "index",
                "missing_diagnostic",
                "missing_report",
                "missing_status",
                "name",
                "source_set",
                "status",
                "top",
                "top_lib",
            )
            if key in fileset
        }
        row["sources"] = _fixture_membership_projection(fileset.get("sources", []))
        row["export_files"] = _fixture_membership_projection(
            fileset.get("export_files", [])
        )
        filesets.append(row)
    projected["filesets"] = _columnarize_record_lists(filesets)
    return projected


def _fixture_invocation_projection(
    invocation: dict[str, Any],
    compile_source_rows: dict[str, int],
) -> dict[str, Any]:
    projected = {
        key: copy.deepcopy(invocation.get(key))
        for key in (
            "invocation_id",
            "driver",
            "work_library",
            "input_source_ids",
            "include_directory_ids",
            "fileset_index",
        )
        if key in invocation
    }
    input_paths = {
        str(path) for path in invocation.get("input_remote_paths", []) if str(path)
    }
    options: list[str] = []
    skip_next = False
    for index, token_value in enumerate(invocation.get("argv", [])):
        token = str(token_value)
        if index == 0 or skip_next:
            skip_next = False
            continue
        if token == "-work":
            skip_next = True
            continue
        if token in input_paths or token.startswith("+incdir+"):
            continue
        if (
            token in {"|", "|&", "||", "&&", ";", "tee"}
            or re.fullmatch(r"(?:\d+)?(?:>>?|<<?|>&|<&).*", token)
        ):
            break
        options.append(token)
    projected["compiler_options"] = options
    projected["input_count"] = len(invocation.get("input_source_ids", []))
    input_source_ids = [str(value) for value in invocation.get("input_source_ids", [])]
    if input_source_ids and all(value in compile_source_rows for value in input_source_ids):
        projected["input_source_ids"] = {
            "$ref": (
                "#/verification_capability_repair_package/exact_board_integration_repair_context/"
                "adaptive_design_inputs/external_simulation_fixture/value/compile_authority/"
                "compile_sources"
            ),
            "column": "source_id",
            "row_ranges_inclusive": _contiguous_index_ranges(
                [compile_source_rows[value] for value in input_source_ids]
            ),
            "row_count": len(input_source_ids),
            "canonical_sha256": _canonical_json_sha256(input_source_ids),
        }
    return projected


def _fixture_compile_source_projection(source: dict[str, Any]) -> dict[str, Any]:
    return {
        key: copy.deepcopy(source.get(key))
        for key in (
            "source_id",
            "role",
            "language",
            "file_type",
            "library",
            "declared_design_units",
            "compile_order",
            "invoked_by_compile",
        )
        if key in source
    }


def _fixture_export_context_projection(
    context: dict[str, Any],
    compile_sources: list[dict[str, Any]],
) -> dict[str, Any]:
    projected = {
        key: copy.deepcopy(context.get(key))
        for key in (
            "artifact_id",
            "path",
            "remote_path",
            "sha256",
            "source_id",
            "staged_path",
        )
        if key in context
    }
    text = str(context.get("text") or "")
    if not text:
        return projected
    aliased_text = text
    for source in sorted(
        compile_sources,
        key=lambda row: len(str(row.get("remote_path") or "")),
        reverse=True,
    ):
        remote_path = str(source.get("remote_path") or "")
        source_id = str(source.get("source_id") or "")
        if remote_path and source_id:
            aliased_text = aliased_text.replace(remote_path, f"@source:{source_id}")
    semantic_ast = _vcs_export_semantic_ast(
        aliased_text,
        compile_sources,
        compile_source_view={
            "$ref": (
                "#/verification_capability_repair_package/exact_board_integration_repair_context/"
                "adaptive_design_inputs/external_simulation_fixture/value/compile_authority/"
                "compile_sources"
            )
        },
    )
    projected.update(
        {
            "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "text_chars": len(text),
            "semantic_ast": semantic_ast,
            "semantic_ast_policy": (
                "compile source lists resolve through ordered compile_sources; compile invocations remain "
                "authoritative; elaboration/simulation options remain explicit"
            ),
        }
    )
    return projected


def _compact_fixture_setup(setup: Any) -> Any:
    if not isinstance(setup, dict):
        return compact_for_retry(setup)
    projected = {
        key: copy.deepcopy(setup.get(key))
        for key in setup
        if key != "library_mappings"
    }
    mappings = [
        row for row in setup.get("library_mappings", []) if isinstance(row, dict)
    ]
    covered = {
        str(value).lower()
        for value in setup.get("covered_compile_work_libraries", [])
        if str(value)
    }
    projected["covered_library_mappings"] = _columnarize_record_lists(
        [
            row
            for row in mappings
            if str(row.get("library") or "").lower() in covered
        ]
    )
    projected["all_library_mappings_contract"] = {
        "row_count": len(mappings),
        "canonical_sha256": _canonical_json_sha256(mappings),
        "full_setup_is_hash_bound_by_path": True,
    }
    return projected


def _fixture_provider_pin_semantics(pin: Any) -> Any:
    if not isinstance(pin, dict):
        return compact_for_retry(pin)
    properties = pin.get("properties", {})
    properties = properties if isinstance(properties, dict) else {}
    width_bits = pin.get("width_bits")
    if isinstance(width_bits, bool) or not isinstance(width_bits, int) or width_bits <= 0:
        try:
            width_bits = abs(int(properties.get("LEFT")) - int(properties.get("RIGHT"))) + 1
        except (TypeError, ValueError):
            width_bits = 1
    return {
        key: copy.deepcopy(value)
        for key, value in {
            "object_id": pin.get("object_id"),
            "path": pin.get("path"),
            "owner_path": pin.get("owner_path"),
            "name": properties.get("NAME"),
            "direction": properties.get("DIR"),
            "width_bits": width_bits,
            "left": properties.get("LEFT"),
            "right": properties.get("RIGHT"),
            "type": properties.get("TYPE"),
            "default_driver": properties.get("DEFAULT_DRIVER"),
        }.items()
        if value not in (None, "")
    }


def _fixture_external_interface_semantics(interface: Any) -> Any:
    if not isinstance(interface, dict):
        return compact_for_retry(interface)

    def interface_endpoint(value: Any) -> Any:
        if not isinstance(value, dict):
            return compact_for_retry(value)
        properties = value.get("properties", {})
        semantic_properties = {
            str(key): copy.deepcopy(child)
            for key, child in properties.items()
            if key not in {"CLASS", "CAN_DEBUG", "LOCATION", "PATH"}
        } if isinstance(properties, dict) else {}
        return {
            "object_id": value.get("object_id"),
            "path": value.get("path"),
            "owner_path": value.get("owner_path"),
            "properties": semantic_properties,
        }

    interface_net = interface.get("interface_net", {})
    return {
        "interface_net": {
            key: copy.deepcopy(interface_net.get(key))
            for key in ("object_id", "path")
            if isinstance(interface_net, dict) and key in interface_net
        },
        "interface_port": interface_endpoint(interface.get("interface_port", {})),
        "provider_interface_pin": interface_endpoint(
            interface.get("provider_interface_pin", {})
        ),
        "provider_member_pins": _lossless_columnar_rows(
            [
                _fixture_provider_pin_semantics(pin)
                for pin in interface.get("provider_member_pins", [])
                if isinstance(pin, dict)
            ]
        ),
        "complete_interface_contract": {
            "canonical_sha256": _canonical_json_sha256(interface),
            "physical_port_names_directions_width_bounds_types_and_interface_properties_preserved": True,
            "verbose_vivado_graph_provenance_bound_by_fixture_artifact_sha256": True,
        },
    }


def _compact_fixture_provider_groups(groups: Any) -> Any:
    records = [row for row in groups if isinstance(row, dict)] if isinstance(groups, list) else []
    compact_groups: list[dict[str, Any]] = []
    for group in records:
        instances = [
            row for row in group.get("instances", []) if isinstance(row, dict)
        ]
        representative = (
            group.get("representative", {})
            if isinstance(group.get("representative"), dict)
            else {}
        )
        compact_groups.append(
            {
                "configuration": copy.deepcopy(group.get("configuration", {})),
                "configuration_sha256": group.get("configuration_sha256"),
                "instances": _lossless_columnar_rows(
                    [
                        {
                            key: copy.deepcopy(instance.get(key))
                            for key in (
                                "cell_id",
                                "cell_path",
                                "component_name",
                                "configured_ip",
                                "selected_by_runtime_timing_authority",
                            )
                            if key in instance
                        }
                        | {
                            "external_interfaces_contract": {
                                "interface_count": len(instance.get("external_interfaces", [])),
                                "canonical_sha256": _canonical_json_sha256(
                                    instance.get("external_interfaces", [])
                                ),
                            }
                        }
                        for instance in instances
                    ]
                ),
                "representative": {
                    key: copy.deepcopy(representative.get(key))
                    for key in (
                        "cell_id",
                        "cell_path",
                        "component_name",
                        "configured_ip",
                        "selected_by_runtime_timing_authority",
                    )
                    if key in representative
                }
                | {
                    "external_interfaces": [
                        _fixture_external_interface_semantics(interface)
                        for interface in representative.get("external_interfaces", [])
                    ]
                },
                "complete_group_contract": {
                    "canonical_sha256": _canonical_json_sha256(group),
                    "all_instance_identities_preserved": True,
                    "selected_representative_physical_interface_semantics_preserved": True,
                },
            }
        )
    return compact_groups


def _compact_fixture_authority(authority: Any) -> Any:
    if not isinstance(authority, dict):
        return compact_for_retry(authority)
    compact = {
        key: copy.deepcopy(value)
        for key, value in authority.items()
        if key != "provider_groups"
    }
    compact["provider_groups"] = _compact_fixture_provider_groups(
        authority.get("provider_groups", [])
    )
    return compact


def _fixture_artifact_rows(
    rows: Any,
    fields: tuple[str, ...],
) -> Any:
    records = [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []
    return _lossless_columnar_rows(
        [
            {key: copy.deepcopy(row.get(key)) for key in fields if key in row}
            for row in records
        ]
    )


def compact_external_simulation_fixture(value: Any) -> Any:
    """Project complete generation semantics while binding raw duplicate views by hash."""

    if not isinstance(value, dict):
        return compact_for_retry(value)
    fixture = _bound_artifact_value(value)
    if not fixture:
        return compact_bound_artifact(value)
    projected = {
        key: value.get(key)
        for key in ("path", "sha256", "source_path", "source_sha256")
        if key in value
    }
    compile_authority = (
        fixture.get("compile_authority", {})
        if isinstance(fixture.get("compile_authority"), dict)
        else {}
    )
    compile_sources = [
        row
        for row in compile_authority.get("compile_sources", [])
        if isinstance(row, dict)
    ]
    compile_pointer = (
        "#/verification_capability_repair_package/exact_board_integration_repair_context/"
        "adaptive_design_inputs/external_simulation_fixture/value/compile_authority/compile_sources"
    )
    compact_compile_authority = {
        key: copy.deepcopy(compile_authority.get(key))
        for key in (
            "schema_version",
            "status",
            "source",
            "project_part",
            "vivado_version",
            "provider_groups_sha256",
            "classification_policy",
            "compile_authority_sha256",
        )
        if key in compile_authority
    }
    compact_compile_authority["compile_sources"] = _lossless_columnar_rows(
        [_fixture_compile_source_projection(row) for row in compile_sources]
    )
    compact_compile_authority["complete_compile_source_rows_contract"] = {
        "row_count": len(compile_sources),
        "canonical_sha256": _canonical_json_sha256(compile_sources),
        "full_rows_are_bound_by_fixture_contract": True,
        "omitted_paths_invocation_ids_integrity_and_transport_fields_are_not_generation_decisions": True,
    }
    compact_compile_authority["configured_ips"] = _fixture_artifact_rows(
        compile_authority.get("configured_ips", []),
        (
            "artifact_id",
            "cell_id",
            "component_name",
            "source_id",
            "staged_path",
            "provider_configuration_sha256",
        ),
    )
    compact_compile_authority["runtime_auxiliary_files"] = _fixture_artifact_rows(
        compile_authority.get("runtime_auxiliary_files", []),
        (
            "artifact_id",
            "source_id",
            "classification",
            "runtime_staged_path",
            "sha256",
            "size_bytes",
        ),
    )
    compact_compile_authority["include_directories"] = _fixture_artifact_rows(
        compile_authority.get("include_directories", []),
        ("include_dir_id", "staged_path", "member_source_ids"),
    )
    installation = compile_authority.get("vivado_installation_hdl_authority", {})
    if isinstance(installation, dict):
        compact_compile_authority["vivado_installation_hdl_authority"] = {
            key: copy.deepcopy(installation.get(key))
            for key in (
                "status",
                "selected_root",
                "resolved_tool_executable",
                "authority_sha256",
            )
            if key in installation
        }
        compact_compile_authority["vivado_installation_hdl_authority"]["files"] = (
            _fixture_artifact_rows(
                installation.get("files", []),
                ("source_id", "staged_path", "language", "declared_design_units"),
            )
        )
        compact_compile_authority["vivado_installation_hdl_authority"][
            "complete_authority_contract"
        ] = {
            "canonical_sha256": _canonical_json_sha256(installation),
            "selected_installation_sources_are_also_in_compile_sources": True,
        }
    compact_compile_authority["export_artifacts"] = _fixture_artifact_rows(
        compile_authority.get("export_artifacts", []),
        (
            "artifact_id",
            "source_id",
            "classification",
            "role",
            "staged_path",
            "sha256",
        ),
    )
    compact_compile_authority["compiler_inputs"] = _fixture_source_view_reference(
        compile_authority.get("compiler_inputs", []),
        compile_sources,
        compile_pointer,
    )
    compact_compile_authority["hdl_export_artifacts"] = (
        _fixture_source_view_reference(
            compile_authority.get("hdl_export_artifacts", []),
            compile_sources,
            compile_pointer,
        )
    )
    compile_invocations = [
        row
        for row in compile_authority.get("compile_invocations", [])
        if isinstance(row, dict)
    ]
    compact_compile_authority["compile_invocations"] = _columnarize_record_lists(
        [
            _fixture_invocation_projection(
                row,
                {
                    str(source.get("source_id")): index
                    for index, source in enumerate(compile_sources)
                    if source.get("source_id")
                },
            )
            for row in compile_invocations
        ]
    )
    compact_compile_authority["complete_compile_invocations_contract"] = {
        "row_count": len(compile_invocations),
        "canonical_sha256": _canonical_json_sha256(compile_invocations),
        "script_paths_artifact_aliases_line_numbers_and_repeated_configuration_hashes_are_provenance_only": True,
    }
    compact_compile_authority["synopsys_sim_setup"] = _compact_fixture_setup(
        compile_authority.get("synopsys_sim_setup", {})
    )
    export_contexts = [
        row
        for row in compile_authority.get("export_contexts", [])
        if isinstance(row, dict)
    ]
    projected_contexts = [
        _fixture_export_context_projection(row, compile_sources)
        for row in export_contexts
    ]
    semantic_contexts = []
    for row in projected_contexts:
        ast = row.get("semantic_ast", {})
        commands = _decode_lossless_columnar_rows(ast.get("commands", {}))
        if ast.get("assignments", {}).get("row_count", 0) or any(
            str(command.get("tool") or "") in {"vlogan", "vhdlan", "vcs"}
            or "simv" in str(command.get("tool") or "")
            for command in commands
            if isinstance(command, dict)
        ):
            semantic_contexts.append(row)
    compact_compile_authority["export_contexts"] = _columnarize_record_lists(
        semantic_contexts
    )
    compact_compile_authority["complete_export_contexts_contract"] = {
        "row_count": len(export_contexts),
        "canonical_sha256": _canonical_json_sha256(export_contexts),
        "semantic_context_count": len(semantic_contexts),
        "readme_fileinfo_and_runtime_data_contexts_are_bound_by_export_artifact_hashes": True,
    }
    materialized = [
        row for row in fixture.get("materialized_files", []) if isinstance(row, dict)
    ]
    snapshot = (
        fixture.get("vivado_export_snapshot", {})
        if isinstance(fixture.get("vivado_export_snapshot"), dict)
        else {}
    )
    raw_export = snapshot.get("raw_export", {})
    compact_snapshot = {
        key: copy.deepcopy(snapshot.get(key))
        for key in ("schema_version", "status", "export_cache_sha256")
        if key in snapshot
    }
    compact_snapshot["raw_export_contract"] = {
        "canonical_sha256": _canonical_json_sha256(raw_export),
        "metadata": copy.deepcopy(raw_export.get("metadata", {}))
        if isinstance(raw_export, dict)
        else {},
        "full_raw_export_is_bound_by_fixture_contract": True,
    }
    compact_fixture = {
        key: copy.deepcopy(fixture.get(key))
        for key in (
            "schema_version",
            "status",
            "run_dir",
            "authority_sha256",
            "vivado_export_cache",
            "vivado_export_cache_sha256",
            "transport",
            "blockers",
            "policy",
            "contract_sha256",
        )
        if key in fixture
    }
    compact_fixture["authority"] = _compact_fixture_authority(
        fixture.get("authority", {})
    )
    authority_groups = [
        row
        for row in fixture.get("authority", {}).get("provider_groups", [])
        if isinstance(row, dict)
    ] if isinstance(fixture.get("authority"), dict) else []
    provider_group_configurations = {
        str(row.get("configuration_sha256") or ""): (index, row.get("configuration", {}))
        for index, row in enumerate(authority_groups)
        if row.get("configuration_sha256") and isinstance(row.get("configuration"), dict)
    }
    compact_fixture["providers"] = _columnarize_record_lists(
        [
            _compact_fixture_provider(provider, provider_group_configurations)
            for provider in fixture.get("providers", [])
            if isinstance(provider, dict)
        ]
    )
    compact_fixture["materialized_files_contract"] = {
        "row_count": len(materialized),
        "canonical_sha256": _canonical_json_sha256(materialized),
        "classifications": sorted(
            {
                str(row.get("classification") or "")
                for row in materialized
                if str(row.get("classification") or "")
            }
        ),
        "complete_rows_are_covered_by_compile_runtime_setup_install_and_source_bundle": True,
    }
    compact_fixture["compile_authority"] = compact_compile_authority
    compact_fixture["vivado_export_snapshot"] = compact_snapshot
    export_cache = fixture.get("vivado_export_cache", {})
    if isinstance(export_cache, dict):
        compact_fixture["vivado_export_cache"] = {
            key: copy.deepcopy(export_cache.get(key))
            for key in (
                "schema_version",
                "export_schema_version",
                "sample_project",
                "vivado_tool",
                "vivado_tcl_sha256",
            )
            if key in export_cache
        }
        compact_fixture["vivado_export_cache"]["provider_groups_contract"] = {
            "$ref": (
                "#/verification_capability_repair_package/exact_board_integration_repair_context/"
                "adaptive_design_inputs/external_simulation_fixture/value/authority/provider_groups"
            ),
            "canonical_sha256": _canonical_json_sha256(
                export_cache.get("provider_groups", [])
            ),
            "provider_configuration_is_preserved_by_authority": True,
        }
    projected["value"] = compact_fixture
    projected["compaction_policy"] = {
        "complete_generation_semantics_preserved": True,
        "ordered_compile_source_identity_modules_and_invocation_references_preserved": True,
        "provider_component_configuration_and_source_membership_preserved": True,
        "duplicate_raw_views_bound_by_canonical_sha256": True,
        "canonical_fixture_sha256": _canonical_json_sha256(fixture),
        "original_fixture_bound_by_path_and_sha256": True,
    }
    return projected


def _source_file_indexed_binding(manifest: dict[str, Any]) -> dict[str, Any]:
    compact_manifest = copy.deepcopy(manifest)
    unique: list[dict[str, Any]] = []
    indices: dict[str, int] = {}
    pointer = (
        "#/verification_capability_repair_package/exact_board_integration_repair_context/"
        "adaptive_design_inputs/certified_single_layer_binding/value/source_file_index"
    )

    def index_files(container: dict[str, Any]) -> None:
        files = container.get("source_files")
        if not isinstance(files, list) or not all(isinstance(row, dict) for row in files):
            return
        row_indices: list[int] = []
        for row in files:
            key = _canonical_json(row)
            if key not in indices:
                indices[key] = len(unique)
                unique.append(copy.deepcopy(row))
            row_indices.append(indices[key])
        container["source_files"] = {
            "$ref": pointer,
            "row_indices": row_indices,
            "row_count": len(row_indices),
            "canonical_sha256": _canonical_json_sha256(files),
        }

    single_layer = compact_manifest.get("single_layer_harness", {})
    if isinstance(single_layer, dict):
        index_files(single_layer)
    stages = compact_manifest.get("stage_harnesses", {})
    if isinstance(stages, dict):
        for stage in stages.values():
            if isinstance(stage, dict):
                index_files(stage)
        compact_manifest["stage_harnesses"] = _lossless_mapping_rows(stages)
    compact_manifest["source_file_index"] = _lossless_columnar_rows(unique)
    return compact_manifest


def _decode_compact_binding_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    decoded = copy.deepcopy(manifest)
    source_files = _decode_lossless_columnar_rows(decoded.pop("source_file_index", {}))
    stages = decoded.get("stage_harnesses")
    if isinstance(stages, dict) and str(stages.get("encoding") or "").startswith(
        "spatialaccagent.lossless_ordered_mapping"
    ):
        decoded["stage_harnesses"] = _decode_lossless_mapping_rows(stages)

    def expand(container: dict[str, Any]) -> None:
        reference = container.get("source_files")
        if isinstance(reference, dict) and isinstance(reference.get("row_indices"), list):
            container["source_files"] = [
                copy.deepcopy(source_files[int(index)])
                for index in reference["row_indices"]
            ]

    single_layer = decoded.get("single_layer_harness", {})
    if isinstance(single_layer, dict):
        expand(single_layer)
    for stage in decoded.get("stage_harnesses", {}).values():
        if isinstance(stage, dict):
            expand(stage)
    return decoded


def compact_complete_binding_manifest(value: Any) -> Any:
    """Keep the complete binding semantics in a reversible shared-source form."""

    if not isinstance(value, dict):
        return compact_for_retry(value)
    manifest = _bound_artifact_value(value)
    if not manifest:
        return compact_bound_artifact(value)
    projected = {
        key: value.get(key)
        for key in ("path", "sha256", "source_path", "source_sha256")
        if key in value
    }
    projected["value"] = _source_file_indexed_binding(manifest)
    projected["compaction_policy"] = {
        "complete_manifest_preserved_reversibly": True,
        "stage_harness_mapping_and_source_files_are_lossless_indexes": True,
        "canonical_manifest_sha256": _canonical_json_sha256(manifest),
        "required_for_hash_preserving_complete_file_replacement": True,
        "original_manifest_bound_by_path_and_sha256": True,
    }
    return projected


def _weight_segment_tensor_hashes(segment: dict[str, Any]) -> list[str]:
    result: list[str] = []
    for target in segment.get("target_segments", []):
        if not isinstance(target, dict):
            continue
        for source in target.get("source_tensors", []):
            if isinstance(source, dict) and source.get("source_slice_sha256"):
                result.append(str(source["source_slice_sha256"]))
    return result


def _weight_sources_catalog_reference(
    rows: list[dict[str, Any]],
    tensor_catalog: list[dict[str, Any]],
) -> dict[str, Any] | None:
    by_hash: dict[str, list[int]] = {}
    for index, row in enumerate(tensor_catalog):
        digest = str(row.get("source_slice_sha256") or "")
        if digest:
            by_hash.setdefault(digest, []).append(index)
    sources = [
        source
        for layer in rows
        for stage in layer.get("stage_segments", [])
        if isinstance(stage, dict)
        for target in stage.get("target_segments", [])
        if isinstance(target, dict)
        for source in target.get("source_tensors", [])
        if isinstance(source, dict)
    ]
    if not sources:
        return None
    indices: list[int] = []
    fields = sorted({str(key) for source in sources for key in source})
    field_presence = {
        field: "".join("1" if field in source else "0" for source in sources)
        for field in fields
        if not all(field in source for source in sources)
    }
    for source in sources:
        matches: list[int] = []
        for index in by_hash.get(str(source.get("source_slice_sha256") or ""), []):
            catalog = tensor_catalog[index]
            if all(
                catalog.get("name" if key == "tensor" else key) == child
                for key, child in source.items()
            ):
                matches.append(index)
        if len(matches) != 1:
            return None
        indices.append(matches[0])
    pointer = (
        "#/verification_capability_repair_package/exact_board_integration_repair_context/"
        "adaptive_design_inputs/transformer_block_weight_catalog/value/tensors"
    )
    return {
        "$ref": pointer,
        "row_indices": _encoded_column(indices),
        "field_aliases": {"tensor": "name"},
        "selected_fields": fields,
        "field_presence": field_presence,
        "row_count": len(indices),
        "canonical_sha256": _canonical_json_sha256(sources),
    }


def _compact_weight_layer_segments(
    rows: list[dict[str, Any]],
    tensor_catalog: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    projected = copy.deepcopy(rows)
    stages = [
        stage
        for layer in projected
        for stage in layer.get("stage_segments", [])
        if isinstance(stage, dict)
    ]
    stage_hashes_derived = bool(stages) and all(
        "tensor_hashes" in stage
        and stage.get("tensor_hashes") == _weight_segment_tensor_hashes(stage)
        for stage in stages
    )
    layer_hashes_derived = bool(projected) and all(
        "tensor_hashes" in layer
        and layer.get("tensor_hashes")
        == [
            tensor_hash
            for stage in layer.get("stage_segments", [])
            if isinstance(stage, dict)
            for tensor_hash in _weight_segment_tensor_hashes(stage)
        ]
        for layer in projected
    )
    targets = [
        target
        for stage in stages
        for target in stage.get("target_segments", [])
        if isinstance(target, dict)
    ]
    target_hashes_derived = bool(targets) and all(
        target.get("tensor_hashes")
        == [
            str(source.get("source_slice_sha256"))
            for source in target.get("source_tensors", [])
            if isinstance(source, dict) and source.get("source_slice_sha256")
        ]
        for target in targets
    )
    omitted_integrity_fields = {
        "layer_segments[]": ["sha256", "payload_sha256"],
        "stage_segments[]": ["sha256"],
        "target_segments[]": ["sha256"],
    }
    for layer in projected:
        for stage in layer.get("stage_segments", []):
            if not isinstance(stage, dict):
                continue
            stage.pop("sha256", None)
            for target in stage.get("target_segments", []):
                if not isinstance(target, dict):
                    continue
                target.pop("sha256", None)
                if target_hashes_derived:
                    target.pop("tensor_hashes", None)
            if stage_hashes_derived:
                stage.pop("tensor_hashes", None)
        layer.pop("sha256", None)
        layer.pop("payload_sha256", None)
        if layer_hashes_derived:
            layer.pop("tensor_hashes", None)
    catalog_reference = _weight_sources_catalog_reference(
        projected, tensor_catalog or []
    )
    table = _lossless_hierarchical_rows(
        projected,
        {
            "stage_segments": {
                "target_segments": {
                    "source_tensors": {},
                }
            }
        },
    )
    source_child = (
        table.get("nested_fields", {})
        .get("stage_segments", {})
        .get("rows", {})
        .get("nested_fields", {})
        .get("target_segments", {})
        .get("rows", {})
        .get("nested_fields", {})
        .get("source_tensors", {})
    )
    if catalog_reference and isinstance(source_child, dict) and source_child.get("rows"):
        source_child["catalog_rows"] = catalog_reference
        source_child.pop("rows", None)
    return {
        "table": table,
        "derived_fields": {
            "stage_segments[].tensor_hashes": "ordered target source hashes"
            if stage_hashes_derived
            else None,
            "target_segments[].tensor_hashes": "ordered source_tensors source_slice_sha256 values"
            if target_hashes_derived
            else None,
            "layer_segments[].tensor_hashes": "ordered stage tensor hashes"
            if layer_hashes_derived
            else None,
        },
        "omitted_integrity_fields": omitted_integrity_fields,
        "integrity_policy": (
            "per-segment payload digests are validation metadata bound by the complete manifest SHA; "
            "addresses, counts, tensor identities and ordering remain explicit generation semantics"
        ),
        "catalog_source_reference_contract": {
            "factored_source_count": catalog_reference.get("row_count", 0)
            if catalog_reference
            else 0,
            "catalog_row_order_and_tensor_identity_remain_explicit": True,
            "unmatched_source_records_remain_embedded": True,
        },
        "canonical_sha256": _canonical_json_sha256(rows),
    }


def _decode_compact_weight_layer_segments(
    value: dict[str, Any],
    tensor_catalog: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    table = copy.deepcopy(value.get("table", {}))
    catalog = tensor_catalog or []
    source_child = (
        table.get("nested_fields", {})
        .get("stage_segments", {})
        .get("rows", {})
        .get("nested_fields", {})
        .get("target_segments", {})
        .get("rows", {})
        .get("nested_fields", {})
        .get("source_tensors", {})
    )
    source_ref = source_child.get("catalog_rows") if isinstance(source_child, dict) else None
    if isinstance(source_ref, dict):
        if not catalog:
            raise ValueError("tensor_catalog is required to decode catalog-referenced weight sources")
        indices = _decode_encoded_column(source_ref.get("row_indices", {}))
        selected_fields = [str(field) for field in source_ref.get("selected_fields", [])]
        aliases = source_ref.get("field_aliases", {})
        field_presence = source_ref.get("field_presence", {})
        expanded: list[dict[str, Any]] = []
        for row_index, catalog_index in enumerate(indices):
            catalog_row = catalog[int(catalog_index)]
            source: dict[str, Any] = {}
            for output_field in selected_fields:
                presence = field_presence.get(output_field)
                if isinstance(presence, str) and (
                    row_index >= len(presence) or presence[row_index] != "1"
                ):
                    continue
                catalog_field = str(aliases.get(output_field, output_field))
                if catalog_field in catalog_row:
                    source[output_field] = copy.deepcopy(catalog_row[catalog_field])
            expanded.append(source)
        source_child["rows"] = _lossless_hierarchical_rows(expanded, {})
        source_child.pop("catalog_rows", None)
    rows = _decode_lossless_hierarchical_rows(table)
    derived = value.get("derived_fields", {})
    derive_target = bool(derived.get("target_segments[].tensor_hashes"))
    derive_stage = bool(derived.get("stage_segments[].tensor_hashes"))
    derive_layer = bool(derived.get("layer_segments[].tensor_hashes"))
    for layer in rows:
        layer_hashes: list[str] = []
        for stage in layer.get("stage_segments", []):
            if not isinstance(stage, dict):
                continue
            if derive_target:
                for target in stage.get("target_segments", []):
                    if isinstance(target, dict):
                        target["tensor_hashes"] = _weight_segment_tensor_hashes(
                            {"target_segments": [target]}
                        )
            if derive_stage:
                stage["tensor_hashes"] = _weight_segment_tensor_hashes(stage)
            stage_hashes = (
                stage.get("tensor_hashes", [])
                if "tensor_hashes" in stage
                else _weight_segment_tensor_hashes(stage)
            )
            layer_hashes.extend(str(item) for item in stage_hashes)
        if derive_layer:
            layer["tensor_hashes"] = layer_hashes
    return rows


def compact_full_weight_image_manifest(
    value: Any,
    tensor_catalog: list[dict[str, Any]] | None = None,
) -> Any:
    if not isinstance(value, dict):
        return compact_for_retry(value)
    manifest = _bound_artifact_value(value)
    if not manifest:
        return compact_bound_artifact(value)
    projected: dict[str, Any] = {
        key: value.get(key)
        for key in ("path", "sha256", "source_path", "source_sha256")
        if key in value
    }
    scalar_fields = (
        "schema_version",
        "status",
        "accelerator_scope",
        "scope_coverage_complete",
        "all_target_layers",
        "target_layer_count",
        "bound_layer_count",
        "source_checkpoint_sha256",
        "accelerator_weight_catalog_sha256",
        "accelerator_weight_catalog_canonical_sha256",
        "dut_weight_binding_requirements_sha256",
        "dut_weight_binding_requirements_canonical_sha256",
        "board_workload_image_plan_sha256",
        "board_workload_image_plan_file_sha256",
        "connected_weight_stream_contract_sha256",
        "stage_weight_layout_contract_sha256s",
        "canonical_weight_layout_set_sha256",
        "canonical_stage_layouts",
        "canonical_layer_word_count",
        "canonical_layer_byte_count",
        "word_bits",
        "byte_order",
        "image_format",
        "layer_alignment_bytes",
        "weight_bank_count",
        "weight_bank_capacity_bytes",
        "path",
        "sha256",
        "image_sha256",
        "byte_count",
        "total_bytes",
        "word_count",
        "packed_tensor_count",
        "source_checkpoint_files",
        "padding_policy",
        "image",
        "manifest_path",
        "manifest_contract_sha256",
        "layer_order",
    )
    compact_manifest = {
        key: manifest.get(key)
        for key in scalar_fields
        if key in manifest
    }
    packed_tensor_hashes = (
        manifest.get("packed_tensor_hashes", [])
        if isinstance(manifest.get("packed_tensor_hashes"), list)
        else []
    )
    compact_manifest["packed_tensor_hashes"] = {
        "multiset_ref": (
            "#/verification_capability_repair_package/exact_board_integration_repair_context/"
            "adaptive_design_inputs/transformer_block_weight_catalog/value/tensors"
        ),
        "column": "source_slice_sha256",
        "ordering": "reconstruct from layer_segments/stage_segments/target_segments/source_tensors",
        "row_count": len(packed_tensor_hashes),
        "canonical_sha256": _canonical_json_sha256(packed_tensor_hashes),
    }
    layer_segments = [
        row for row in manifest.get("layer_segments", []) if isinstance(row, dict)
    ]
    compact_manifest["layer_segments"] = _compact_weight_layer_segments(
        layer_segments,
        tensor_catalog=tensor_catalog,
    )
    compact_manifest["compaction_policy"] = {
        "all_layer_stage_target_source_generation_records_preserved": True,
        "repeated_tensor_hash_lists_derived_from_ordered_source_records": True,
        "intermediate_integrity_digests_bound_by_complete_manifest_sha": True,
        "packed_tensor_hash_list_reused_from_transformer_catalog": True,
        "original_manifest_bound_by_path_and_sha256": True,
    }
    projected["value"] = compact_manifest
    return projected


def compact_full_runtime_image_manifest(value: Any) -> Any:
    """Keep complete runtime-image semantics as reversible layer/source tables."""

    if not isinstance(value, dict):
        return compact_for_retry(value)
    manifest = _bound_artifact_value(value)
    if not manifest:
        return compact_bound_artifact(value)
    projected: dict[str, Any] = {
        key: value.get(key)
        for key in ("path", "sha256", "source_path", "source_sha256")
        if key in value
    }
    compact_manifest = {
        key: copy.deepcopy(child)
        for key, child in manifest.items()
        if key not in {"layer_bindings", "source_tensor_files", "unique_segments"}
    }
    compact_manifest["unique_segments"] = _lossless_columnar_rows(
        [row for row in manifest.get("unique_segments", []) if isinstance(row, dict)]
    )
    compact_manifest["source_tensor_files"] = _lossless_columnar_rows(
        [row for row in manifest.get("source_tensor_files", []) if isinstance(row, dict)]
    )
    compact_manifest["layer_bindings"] = _lossless_hierarchical_rows(
        [row for row in manifest.get("layer_bindings", []) if isinstance(row, dict)],
        {"stage_bindings": {"targets": {}}},
    )
    projected["value"] = compact_manifest
    projected["compaction_policy"] = {
        "complete_manifest_preserved_once_reversibly": True,
        "all_layers_segments_targets_and_source_tensor_files_preserved": True,
        "canonical_manifest_sha256": _canonical_json_sha256(manifest),
        "runtime_binary_omitted": True,
        "binary_bound_only_by_path_sha256_and_size": True,
        "original_manifest_bound_by_path_and_sha256": True,
    }
    return projected


def _decode_compact_runtime_image_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    decoded = copy.deepcopy(manifest)
    decoded["unique_segments"] = _decode_lossless_columnar_rows(decoded.get("unique_segments", {}))
    decoded["source_tensor_files"] = _decode_lossless_columnar_rows(
        decoded.get("source_tensor_files", {})
    )
    decoded["layer_bindings"] = _decode_lossless_hierarchical_rows(
        decoded.get("layer_bindings", {})
    )
    return decoded


def compact_runtime_capture_contract(value: Any) -> Any:
    if not isinstance(value, dict):
        return compact_for_retry(value)
    contract = _bound_artifact_value(value)
    if not contract:
        return compact_bound_artifact(value)
    projected: dict[str, Any] = {
        key: value.get(key)
        for key in ("path", "sha256", "source_path", "source_sha256")
        if key in value
    }
    compact_contract = {
        key: copy.deepcopy(child)
        for key, child in contract.items()
        if key != "layers"
    }
    compact_contract["layers"] = _lossless_hierarchical_rows(
        [row for row in contract.get("layers", []) if isinstance(row, dict)],
        {"stage_invocations": {"sources": {}}},
    )
    projected["value"] = compact_contract
    projected["compaction_policy"] = {
        "all_layer_invocations_and_source_records_preserved_reversibly": True,
        "canonical_contract_sha256": _canonical_json_sha256(contract),
        "original_contract_bound_by_path_and_sha256": True,
    }
    return projected


def _decode_compact_runtime_capture_contract(contract: dict[str, Any]) -> dict[str, Any]:
    decoded = copy.deepcopy(contract)
    decoded["layers"] = _decode_lossless_hierarchical_rows(decoded.get("layers", {}))
    return decoded


def compact_binary_artifact_descriptor(value: Any) -> Any:
    """Expose binary identity and extent, never binary payload text or words."""

    if not isinstance(value, dict):
        return {}
    artifact = _bound_artifact_value(value)
    projected: dict[str, Any] = {
        key: value.get(key)
        for key in ("path", "sha256", "source_path", "source_sha256")
        if key in value
    }
    if isinstance(artifact, dict):
        projected["value"] = {
            key: artifact.get(key)
            for key in (
                "schema_version",
                "status",
                "path",
                "sha256",
                "image_sha256",
                "byte_count",
                "total_bytes",
                "word_count",
                "format",
                "image_format",
                "word_bits",
                "byte_order",
            )
            if key in artifact
        }
    projected["compaction_policy"] = {
        "binary_payload_omitted": True,
        "identity_and_extent_preserved": True,
    }
    return projected


def compact_transformer_block_weight_catalog(value: Any) -> Any:
    if not isinstance(value, dict):
        return compact_for_retry(value)
    catalog = _bound_artifact_value(value)
    if not catalog:
        return compact_bound_artifact(value)
    projected: dict[str, Any] = {
        key: value.get(key)
        for key in ("path", "sha256", "source_path", "source_sha256")
        if key in value
    }
    compact_catalog = {
        key: copy.deepcopy(child)
        for key, child in catalog.items()
        if key != "tensors"
    }
    tensor_rows = [
        row for row in catalog.get("tensors", []) if isinstance(row, dict)
    ]
    generation_fields = (
        "name",
        "layer_index",
        "parameter_suffix",
        "shape",
        "dtype",
        "source_slice_sha256",
        "source_byte_count",
    )
    compact_catalog["tensors"] = _lossless_columnar_rows(
        [
            {key: copy.deepcopy(row.get(key)) for key in generation_fields if key in row}
            for row in tensor_rows
        ]
    )
    compact_catalog["complete_tensor_integrity_contract"] = {
        "row_count": len(tensor_rows),
        "canonical_sha256": _canonical_json_sha256(tensor_rows),
        "omitted_fields": sorted(
            {
                str(key)
                for row in tensor_rows
                for key in row
                if key not in generation_fields
            }
        ),
        "checkpoint_offsets_paths_and_file_hashes_are_bound_by_catalog_artifact_sha256": True,
    }
    projected["value"] = compact_catalog
    projected["compaction_policy"] = {
        "all_tensor_generation_rows_and_fields_preserved": True,
        "checkpoint_storage_provenance_bound_once_by_catalog_artifact_sha256": True,
        "canonical_catalog_sha256": _canonical_json_sha256(catalog),
        "binary_tensor_payloads_not_embedded": True,
    }
    return projected


_BOARD_IDENTITY_PROVENANCE_KEYS = {
    "evidence_refs",
    "evidence_object_ids",
    "evidence_source_ids",
    "parameter_evidence_refs",
    "signal_evidence_refs",
    "signal_fact_map",
}


def _compact_board_identity_generation_semantics(identity: dict[str, Any]) -> dict[str, Any]:
    """Keep exact ABI decisions while binding verbose discovery provenance once."""

    def project(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                str(key): project(child)
                for key, child in value.items()
                if key not in _BOARD_IDENTITY_PROVENANCE_KEYS
            }
        if isinstance(value, list):
            return [project(child) for child in value]
        return copy.deepcopy(value)

    compact = project(identity)
    compute_slot = compact.get("compute_slot_abi", {})
    if isinstance(compute_slot, dict):
        required_ports = compute_slot.get("required_ports", [])
        port_bindings = compute_slot.get("port_bindings", [])
        by_name = {
            str(row.get("name")): row
            for row in required_ports
            if isinstance(row, dict) and row.get("name")
        }
        derived = bool(port_bindings) and all(
            isinstance(binding, dict)
            and str(binding.get("accelerator_port") or "") in by_name
            and all(
                binding.get(field) == by_name[str(binding["accelerator_port"])].get(field)
                for field in ("direction", "port_id", "width_bits")
            )
            and set(binding).issubset(
                {"accelerator_port", "direction", "port_id", "width_bits"}
            )
            for binding in port_bindings
        )
        if derived:
            compute_slot["port_bindings"] = {
                "$ref": (
                    "#/verification_capability_repair_package/exact_board_integration_repair_context/"
                    "adaptive_design_inputs/exact_board_source_identity/value/compute_slot_abi/"
                    "required_ports"
                ),
                "field_aliases": {"accelerator_port": "name"},
                "selected_fields": ["name", "direction", "port_id", "width_bits"],
                "row_count": len(port_bindings),
                "canonical_sha256": _canonical_json_sha256(port_bindings),
            }
    validation = compact.get("identity_contract_validation", {})
    original_validation = identity.get("identity_contract_validation", {})
    if isinstance(validation, dict) and isinstance(original_validation, dict):
        checks = original_validation.get("checks", [])
        if isinstance(checks, list):
            validation["checks"] = [
                {
                    "name": row.get("name"),
                    "status": row.get("status"),
                    "blockers": copy.deepcopy(row.get("blockers", [])),
                }
                for row in checks
                if isinstance(row, dict)
            ]
            validation["complete_checks_contract"] = {
                "row_count": len(checks),
                "canonical_sha256": _canonical_json_sha256(checks),
                "paths_root_ids_and_repeated_integrity_fields_are_provenance_only": True,
            }
    compact["discovery_provenance_contract"] = {
        "omitted_keys": sorted(_BOARD_IDENTITY_PROVENANCE_KEYS),
        "canonical_identity_sha256": _canonical_json_sha256(identity),
        "exact_abi_axi_timing_and_signal_maps_preserved": True,
        "full_provenance_is_bound_by_identity_artifact_sha256": True,
    }
    return compact


def compact_board_source_identity(value: Any) -> Any:
    if not isinstance(value, dict):
        return compact_for_retry(value)
    identity = _bound_artifact_value(value)
    if not identity:
        return compact_bound_artifact(value)
    projected: dict[str, Any] = {
        key: value.get(key)
        for key in ("path", "sha256", "source_path", "source_sha256")
        if key in value
    }
    identity_projection = _compact_board_identity_generation_semantics(
        _json_document_projection(identity)
    )
    validation = (
        identity_projection.get("identity_contract_validation", {})
        if isinstance(identity_projection.get("identity_contract_validation"), dict)
        else {}
    )
    checks = validation.get("checks", []) if isinstance(validation.get("checks"), list) else []
    for check in checks:
        source_ids = check.get("root_source_ids") if isinstance(check, dict) else None
        if isinstance(source_ids, list):
            check["root_source_ids"] = {
                "$ref": (
                    "#/verification_capability_repair_package/exact_board_integration_repair_context/"
                    "adaptive_design_inputs/shared_board_source_index"
                ),
                "view": "source_ids",
                "row_count": len(source_ids),
                "canonical_sha256": _canonical_json_sha256(source_ids),
            }
    projected["value"] = _columnarize_record_lists(identity_projection)
    projected["compaction_policy"] = {
        "abi_timing_axi_and_validation_semantics_preserved": True,
        "record_lists_are_lossless_columnar_tables": True,
        "full_source_closure_reused_through_shared_board_source_index": True,
        "canonical_identity_sha256": _canonical_json_sha256(identity),
    }
    return projected


def _compact_runtime_plan_record_lists(contract: dict[str, Any]) -> dict[str, Any]:
    compact_contract = copy.deepcopy(contract)
    for field in ("physical_cfg_bindings", "memory_regions", "trace_points"):
        rows = compact_contract.get(field)
        if isinstance(rows, list) and all(isinstance(row, dict) for row in rows):
            compact_contract[field] = _lossless_columnar_rows(rows)
    for parent, field in (
        ("weight_double_buffer", "banks"),
        ("weight_double_buffer", "layer_schedule"),
        ("activation_ping_pong", "banks"),
        ("activation_ping_pong", "layer_schedule"),
        ("runtime_constants", "load_schedule"),
        ("programming_sequence", "steps"),
    ):
        container = compact_contract.get(parent)
        rows = container.get(field) if isinstance(container, dict) else None
        if isinstance(rows, list) and all(isinstance(row, dict) for row in rows):
            container[field] = _lossless_columnar_rows(rows)
    return compact_contract


def compact_board_memory_runtime_contract(value: Any) -> Any:
    if not isinstance(value, dict):
        return compact_for_retry(value)
    contract = _bound_artifact_value(value)
    if not contract:
        return compact_bound_artifact(value)
    projected: dict[str, Any] = {
        key: value.get(key)
        for key in ("path", "sha256", "source_path", "source_sha256")
        if key in value
    }
    compact_contract = _compact_runtime_plan_record_lists(contract)
    workload = (
        compact_contract.get("workload_image", {})
        if isinstance(compact_contract.get("workload_image"), dict)
        else {}
    )
    if workload:
        workload["full_weight_image_manifest"] = {
            "$ref": (
                "#/verification_capability_repair_package/exact_board_integration_repair_context/"
                "adaptive_design_inputs/full_weight_image_manifest/value"
            )
        }
        materialized = (
            workload.get("materialized_projection", {})
            if isinstance(workload.get("materialized_projection"), dict)
            else {}
        )
        if materialized:
            materialized["packed_tensor_hashes"] = {
                "$ref": (
                    "#/verification_capability_repair_package/exact_board_integration_repair_context/"
                    "adaptive_design_inputs/full_weight_image_manifest/value/packed_tensor_hashes"
                )
            }
            materialized["layer_segments"] = {
                "$ref": (
                    "#/verification_capability_repair_package/exact_board_integration_repair_context/"
                    "adaptive_design_inputs/full_weight_image_manifest/value/layer_segments"
                )
            }
    runtime_constants = (
        compact_contract.get("runtime_constants", {})
        if isinstance(compact_contract.get("runtime_constants"), dict)
        else {}
    )
    if runtime_constants:
        runtime_constants["full_runtime_image_manifest"] = {
            "$ref": (
                "#/verification_capability_repair_package/exact_board_integration_repair_context/"
                "adaptive_design_inputs/full_runtime_image_manifest/value"
            )
        }
        materialized = (
            runtime_constants.get("materialized_projection", {})
            if isinstance(runtime_constants.get("materialized_projection"), dict)
            else {}
        )
        if materialized:
            materialized["unique_segments"] = {
                "$ref": (
                    "#/verification_capability_repair_package/exact_board_integration_repair_context/"
                    "adaptive_design_inputs/full_runtime_image_manifest/value/unique_segments"
                )
            }
            materialized["layer_bindings"] = {
                "$ref": (
                    "#/verification_capability_repair_package/exact_board_integration_repair_context/"
                    "adaptive_design_inputs/full_runtime_image_manifest/value/layer_bindings"
                )
            }
    compact_contract["compaction_policy"] = {
        "runtime_semantics_preserved_in_full": True,
        "materialized_image_evidence_reused_by_json_pointer": True,
        "original_contract_bound_by_path_and_sha256": True,
    }
    projected["value"] = compact_contract
    return projected


def compact_exact_board_integration_context(context: dict[str, Any]) -> dict[str, Any]:
    result = {
        key: context.get(key)
        for key in (
            "schema_version",
            "status",
            "blockers",
            "immutable_architecture_mechanisms",
            "adaptive_fields_policy",
            "required_generated_root",
            "required_binding_manifest",
        )
        if key in context
    }
    adaptive = context.get("adaptive_design_inputs", {})
    if isinstance(adaptive, dict):
        tensor_catalog_value = _bound_artifact_value(
            adaptive.get("transformer_block_weight_catalog", {})
        )
        tensor_catalog_rows = [
            row
            for row in tensor_catalog_value.get("tensors", [])
            if isinstance(row, dict)
        ]
        compact_adaptive = {
            "task_card": compact_bound_artifact(adaptive.get("task_card", {})),
            "target_model": compact_bound_artifact(adaptive.get("target_model", {})),
            "model_derived_memory_layout": compact_bound_artifact(adaptive.get("model_derived_memory_layout", {})),
            "current_tool_profile": compact_bound_artifact(adaptive.get("current_tool_profile", {})),
            "certified_single_layer_binding": compact_complete_binding_manifest(
                adaptive.get("certified_single_layer_binding", {})
            ),
            "single_layer_promotion_certificate": compact_bound_artifact(adaptive.get("single_layer_promotion_certificate", {})),
            "connected_kernel_lifecycle_authority": compact_bound_artifact(
                adaptive.get("connected_kernel_lifecycle_authority", {})
            ),
            "semantic_board_reference_artifacts": copy.deepcopy(
                adaptive.get("semantic_board_reference_artifacts", {})
            ),
            "debug_observability_authority": compact_bound_artifact(
                adaptive.get("debug_observability_authority", {})
            ),
            "external_simulation_fixture": compact_external_simulation_fixture(
                adaptive.get("external_simulation_fixture", {})
            ),
            "board_memory_runtime_contract": compact_board_memory_runtime_contract(
                adaptive.get("board_memory_runtime_contract", {})
            ),
            "full_weight_image_manifest": compact_full_weight_image_manifest(
                adaptive.get("full_weight_image_manifest", {}),
                tensor_catalog=tensor_catalog_rows,
            ),
            "runtime_capture_contract": compact_runtime_capture_contract(
                adaptive.get("runtime_capture_contract", {})
            ),
            "full_layer_runtime_capture_contract": compact_runtime_capture_contract(
                adaptive.get("full_layer_runtime_capture_contract", {})
            ),
            "full_runtime_image_manifest": compact_full_runtime_image_manifest(
                adaptive.get("full_runtime_image_manifest", {})
            ),
            "runtime_image_artifact": compact_binary_artifact_descriptor(
                adaptive.get("runtime_image_artifact", {})
            ),
            "board_memory_runtime_preparation": compact_bound_artifact(
                adaptive.get("board_memory_runtime_preparation", {})
            ),
            "exact_board_source_identity": compact_board_source_identity(
                adaptive.get("exact_board_source_identity", {})
            ),
            "transformer_block_weight_catalog": compact_transformer_block_weight_catalog(
                adaptive.get("transformer_block_weight_catalog", {})
            ),
            "vivado_vcs_compile_authority": compact_bound_artifact(adaptive.get("vivado_vcs_compile_authority", {})),
            "sample_project_vcs_input_projection": copy.deepcopy(
                adaptive.get("sample_project_vcs_input_projection", {})
            ),
        }
        identity = _bound_artifact_value(adaptive.get("exact_board_source_identity", {}))
        compile_authority = _bound_artifact_value(adaptive.get("vivado_vcs_compile_authority", {}))
        shared_index = _shared_board_source_index(identity, compile_authority)
        identity_projection = compact_adaptive.get("exact_board_source_identity", {})
        compile_projection = compact_adaptive.get("vivado_vcs_compile_authority", {})
        if (
            shared_index
            and isinstance(identity_projection, dict)
            and isinstance(compile_projection, dict)
        ):
            sample_source_ids = adaptive.get(
                "sample_project_vcs_input_projection", {}
            ).get("compiler_input_source_ids", [])
            all_source_ids = [
                str(row.get("source_id"))
                for row in identity.get("selected_simulation_source_closure", {}).get(
                    "source_files", []
                )
                if isinstance(row, dict) and row.get("source_id")
            ]
            if (
                isinstance(sample_source_ids, list)
                and [value for value in all_source_ids if value in set(sample_source_ids)]
                == sample_source_ids
            ):
                shared_index.setdefault("views", {})[
                    "compiler_input_source_ids"
                ] = {
                    "column": "source_id",
                    "exclude_source_ids": [
                        value for value in all_source_ids if value not in set(sample_source_ids)
                    ],
                    "row_count": len(sample_source_ids),
                    "canonical_sha256": _canonical_json_sha256(sample_source_ids),
                }
            identity_projection = copy.deepcopy(identity_projection)
            compile_projection = copy.deepcopy(compile_projection)
            compact_adaptive["exact_board_source_identity"] = identity_projection
            compact_adaptive["vivado_vcs_compile_authority"] = compile_projection
            compact_adaptive["shared_board_source_index"] = (
                _compact_shared_board_source_index_for_generation(shared_index)
            )
            compact_adaptive["sample_project_vcs_input_projection"] = (
                _compact_sample_project_vcs_input_projection(
                    adaptive.get("sample_project_vcs_input_projection", {}),
                    shared_index,
                )
            )
            _apply_shared_board_source_index(
                identity_projection,
                compile_projection,
                identity,
                compile_authority,
                shared_index,
            )
        result["adaptive_design_inputs"] = compact_adaptive
    return result


def focused_rows(rows: Any, focus_text: str) -> list[dict[str, Any]]:
    if not isinstance(rows, list):
        return []
    if not any(term in focus_text for term in ["attention", "mask", "softmax", "qkv", "rope"]):
        return [item for item in rows if isinstance(item, dict)]
    focused_ops = {"self_attention", "softmax", "causal_mask", "q_proj", "k_proj", "v_proj", "fused_qkv"}
    result = [
        item
        for item in rows
        if isinstance(item, dict)
        and (
            str(item.get("op")) in focused_ops
            or str(item.get("template_id")) in {"attention", "softmax", "mask", "qkv_projection", "rope", "kv_cache"}
        )
    ]
    return result or [item for item in rows if isinstance(item, dict)]


def compact_template_selection_for_retry(candidate: dict[str, Any], focus_text: str = "") -> dict[str, Any]:
    include_all = not focus_text or "template_selection_agent" in focus_text
    is_cross_layer = any(term in focus_text for term in ["cross layer", "cross_layer", "numeric", "board", "runtime", "deployment"])
    is_binding_agent = "template binding engineer" in focus_text or "binding engineer" in focus_text
    include_operator = include_all or any(term in focus_text for term in ["operator", "coverage"])
    include_binding = include_all or is_binding_agent or (
        not is_cross_layer and any(term in focus_text for term in ["binding", "parameter", "source", "interface", "adapter"])
    )
    include_attention = include_all or any(term in focus_text for term in ["attention", "mask", "softmax", "qkv", "rope"])
    include_cross_layer = include_all or is_cross_layer
    result: dict[str, Any] = {
        "schema_version": candidate.get("schema_version"),
        "stage": candidate.get("stage"),
        "status": candidate.get("status"),
        "library_id": candidate.get("library_id"),
        "model_type": candidate.get("model_type"),
        "selected_template_ids": candidate.get("selected_template_ids", []),
        "missing_ops": candidate.get("missing_ops", []),
        "checker_results": candidate.get("checker_results", []),
        "stage_gate_policy": candidate.get("stage_gate_policy", {}),
        "errors": candidate.get("errors", []),
        "warnings": candidate.get("warnings", []),
    }
    if include_operator:
        result["operator_sequence"] = candidate.get("operator_sequence", [])
        result["selected_templates"] = [
            {
                "role": item.get("role"),
                "op": item.get("op"),
                "matched_op": item.get("matched_op"),
                "template_id": item.get("template_id"),
                "source": item.get("source"),
                "required_params": item.get("required_params", []),
            }
            for item in candidate.get("selected_templates", [])
            if isinstance(item, dict)
        ]
        result["coverage"] = candidate.get("coverage", {})
    if include_binding:
        result["parameter_bindings"] = [
            compact_param_binding_for_retry(item)
            for item in focused_rows(candidate.get("parameter_bindings", []), focus_text)
        ]
        result["template_source_checks"] = [
            compact_source_check_for_retry(item)
            for item in focused_rows(candidate.get("template_source_checks", []), focus_text)
        ]
        result["unsupported_bindings"] = candidate.get("unsupported_bindings", [])
        result["required_adapters"] = candidate.get("required_adapters", [])
        result["forbidden_edits"] = candidate.get("forbidden_edits", [])
    if include_attention:
        result["selected_templates"] = result.get("selected_templates") or [
            {
                "role": item.get("role"),
                "op": item.get("op"),
                "matched_op": item.get("matched_op"),
                "template_id": item.get("template_id"),
                "source": item.get("source"),
                "required_params": item.get("required_params", []),
            }
            for item in candidate.get("selected_templates", [])
            if isinstance(item, dict)
        ]
        result["attention_semantics"] = candidate.get("attention_semantics", {})
        result["parameter_bindings"] = [
            compact_param_binding_for_retry(item)
            for item in focused_rows(candidate.get("parameter_bindings", []), focus_text)
        ]
        result["template_source_checks"] = [
            compact_source_check_for_retry(item)
            for item in focused_rows(candidate.get("template_source_checks", []), focus_text)
        ]
        result["required_adapters"] = candidate.get("required_adapters", [])
    if include_cross_layer:
        result["cross_layer_trace"] = candidate.get("cross_layer_trace", {})
    return result


def compact_repair_step_for_retry(value: Any) -> Any:
    if not isinstance(value, dict):
        return compact_for_retry(value)
    action = value.get("action", {})
    return {
        **{
            key: copy.deepcopy(value.get(key))
            for key in ("id", "scope", "status", "debug_layer")
            if key in value
        },
        **(
            {
                "action": {
                    key: copy.deepcopy(action.get(key))
                    for key in (
                        "repair_kind",
                        "repair_gate",
                        "target_modules",
                        "violated_contract",
                        "reason",
                    )
                    if key in action
                }
            }
            if isinstance(action, dict)
            else {}
        ),
    }


def compact_checkpoint_hook_specialist_package(value: Any) -> Any:
    """Preserve the complete specialist authority while removing prior projections."""

    if not isinstance(value, dict):
        return compact_for_retry(value)
    result = copy.deepcopy(value)
    gap = result.get("capability_gap", {})
    gap = gap if isinstance(gap, dict) else {}
    runtime = gap.get("runtime_execution_failure", {})
    runtime = runtime if isinstance(runtime, dict) else {}
    checkpoint = runtime.get("checkpoint_artifacts", {})
    if isinstance(checkpoint, dict):
        checkpoint.pop("runtime_execution_failure", None)
    result["compact_context_policy"] = {
        "complete_current_testbench_source_preserved": True,
        "checkpoint_authority_and_atomic_edit_contract_preserved": True,
        "all_unique_runtime_equivalence_evidence_preserved": True,
        "prior_self_embedded_runtime_projection_removed": True,
        "duplicate_subtrees_are_content_hash_referenced_by_framework": True,
    }
    return result


def compact_for_retry(value: Any, depth: int = 0) -> Any:
    if isinstance(value, str):
        return value if len(value) <= 120 else value[:120] + f"...<len={len(value)}>"
    if isinstance(value, bool) or value is None or isinstance(value, (int, float)):
        return value
    if isinstance(value, list):
        if depth >= 2:
            return {"_type": "list", "_size": len(value)}
        items = [compact_for_retry(item, depth + 1) for item in value[:4]]
        if len(value) > 4:
            items.append({"_more_items": len(value) - 4})
        return items
    if isinstance(value, dict):
        schema = str(value.get("schema_version") or "")
        if "dse_selection_evidence" in value:
            # Stage-4 selection evidence is already a bounded, lossless
            # projection of the eligible candidate set.  The generic retry
            # compactor must not truncate it to the first few candidates.
            result: dict[str, Any] = {}
            for key in (
                "stage",
                "agent",
                "dse_search_space",
                "dse_selection_evidence",
                "formal_dse_campaign",
                "dse_constraint_report",
                "dse_constraint_report_path",
                "current_sacg_memory_truth",
                "source_sacg_state",
            ):
                if key not in value:
                    continue
                if key == "dse_selection_evidence":
                    result[key] = copy.deepcopy(value[key])
                elif key == "dse_constraint_report":
                    report = value[key]
                    if isinstance(report, dict):
                        result[key] = {
                            field: copy.deepcopy(report[field])
                            for field in (
                                "schema_version",
                                "source_schema_version",
                                "status",
                                "candidate_count",
                                "feasible_candidate_count",
                                "infeasible_candidate_count",
                                "hard_constraint_error_counts",
                                "policy",
                                "candidate_materialization",
                            )
                            if field in report
                        }
                    else:
                        result[key] = compact_for_retry(report, depth + 1)
                else:
                    result[key] = compact_for_retry(value[key], depth + 1)
            return result
        if schema == "spatialaccagent.checkpoint_hook_specialist_package.v1":
            return compact_checkpoint_hook_specialist_package(value)
        if "verification_capability_repair_package" in value:
            result: dict[str, Any] = {}
            for key in (
                "stage",
                "agent",
                "source_sacg_state",
                "repair_step",
                "verification_capability_repair_package",
                "stage_gate_policy",
                "state_summary",
                "hierarchical_learning_context",
            ):
                if key in value:
                    result[key] = (
                        compact_repair_step_for_retry(value[key])
                        if key == "repair_step"
                        else compact_for_retry(value[key], depth + 1)
                    )
            return result
        if schema.startswith("spatialaccagent.verification_capability_repair_package") or (
            "repair_source_bundle" in value and "capability_probe" in value
        ):
            return compact_verification_capability_repair_package(value)
        if schema.startswith("spatialaccagent.repair_source_bundle") or (
            "documents" in value and "document_count" in value and "document_chars" in value
        ):
            return compact_repair_source_bundle(value)
        if schema.startswith("spatialaccagent.exact_board_integration_repair_context") or (
            "adaptive_design_inputs" in value and "immutable_architecture_mechanisms" in value
        ):
            return compact_exact_board_integration_context(value)
        if schema.startswith("spatialaccagent.verification_artifact_contract"):
            dag = value.get("verification_gate_dag", {}) if isinstance(value.get("verification_gate_dag"), dict) else {}
            nodes = dag.get("nodes", []) if isinstance(dag.get("nodes"), list) else []
            critical_nodes = dag.get("critical_nodes", []) if isinstance(dag.get("critical_nodes"), list) else []
            visible_nodes = nodes or critical_nodes
            node_count = dag.get("node_count")
            if not isinstance(node_count, int):
                node_count = len(nodes)
            evidence_path_requirements = value.get("evidence_path_requirements", [])
            evidence_path_summary = value.get("evidence_path_requirements_summary", {})
            if isinstance(evidence_path_requirements, list):
                evidence_path_count = len(evidence_path_requirements)
            elif isinstance(evidence_path_summary, dict) and isinstance(evidence_path_summary.get("count"), int):
                evidence_path_count = evidence_path_summary["count"]
            else:
                evidence_path_count = 0
            return {
                "schema_version": value.get("schema_version"),
                "status": value.get("status"),
                "summary": value.get("summary"),
                "errors": value.get("errors", []),
                "policy": value.get("policy", {}),
                "retry_reconciliation_contract": value.get("retry_reconciliation_contract", {}),
                "backtrack_contract": value.get("backtrack_contract", {}),
                "required_evidence_gate_names": value.get("required_evidence_gate_names", []),
                "evidence_path_requirements_summary": evidence_path_summary,
                "gate_protocol_coverage": value.get("gate_protocol_coverage", {}),
                "functional_sim_candidates": value.get("functional_sim_candidates", []),
                "verification_gate_dag": {
                    "policy": dag.get("policy", {}),
                    "node_count": node_count,
                    "edge_count": dag.get("edge_count", len(dag.get("edges", [])) if isinstance(dag.get("edges"), list) else None),
                    "phase_order": dag.get("phase_order", []),
                    "critical_nodes": [
                        {
                            "name": node.get("name"),
                            "phase": node.get("phase"),
                            "depends_on": node.get("depends_on", []),
                            "required_maturity": node.get("required_maturity"),
                            "evidence_status": node.get("evidence_status"),
                            "planned_consumes_count": node.get("planned_consumes_count", len(node.get("planned_consumes", []))),
                            "planned_produces_count": node.get("planned_produces_count", len(node.get("planned_produces", []))),
                        }
                        for node in visible_nodes[:32]
                        if isinstance(node, dict)
                    ],
                },
                "required_tool_protocols": [
                    {
                        "name": row.get("name"),
                        "role": row.get("role"),
                        "configured": row.get("configured"),
                        "configured_from": row.get("configured_from"),
                    }
                    for row in value.get("required_tool_protocols", [])[:64]
                    if isinstance(row, dict)
                ],
                "evidence_path_requirements_count": evidence_path_count,
            }
        if schema.startswith("spatialaccagent.verification_plan"):
            hierarchy = value.get("hierarchical_verification", {}) if isinstance(value.get("hierarchical_verification"), dict) else {}
            evidence_gates = hierarchy.get("evidence_gates", []) if isinstance(hierarchy.get("evidence_gates"), list) else []
            evidence_gate_names = hierarchy.get("evidence_gate_names", []) if isinstance(hierarchy.get("evidence_gate_names"), list) else []
            required_gates = [
                gate.get("name")
                for gate in evidence_gates
                if isinstance(gate, dict) and gate.get("required")
            ] or evidence_gate_names
            stage_agent_count = hierarchy.get("stage_agent_count")
            if not isinstance(stage_agent_count, int):
                stage_agent_count = len(hierarchy.get("stage_agents", [])) if isinstance(hierarchy.get("stage_agents"), list) else 0
            merge_agent_count = hierarchy.get("merge_agent_count")
            if not isinstance(merge_agent_count, int):
                merge_agent_count = len(hierarchy.get("merge_agents", [])) if isinstance(hierarchy.get("merge_agents"), list) else 0
            return {
                "schema_version": value.get("schema_version"),
                "status": value.get("status"),
                "checker_count": len(value.get("checker_plan", [])),
                "stage_test_target_count": value.get("stage_test_target_count", len(value.get("stage_test_targets", []))),
                "hierarchical_verification": {
                    "strategy": hierarchy.get("strategy"),
                    "stage_agents": stage_agent_count,
                    "merge_agents": merge_agent_count,
                    "required_gates": required_gates,
                    "maturity_levels": hierarchy.get("maturity_levels", []),
                    "policy": hierarchy.get("policy", {}),
                },
            }
        if schema.startswith("spatialaccagent.llm_action_audit"):
            return {
                "schema_version": value.get("schema_version"),
                "status": value.get("status"),
                "summary": value.get("summary"),
                "errors": value.get("errors", []),
                "action_count": len(value.get("actions", [])),
            }
        if (value.get("stage") == "template_selection" and "selected_templates" in value) or {
            "selected_templates",
            "parameter_bindings",
            "template_source_checks",
        }.issubset(set(value.keys())):
            return compact_template_selection_for_retry(value)
        if "candidate_stage_artifact" in value or "candidate_template_selection" in value:
            focus_text = retry_focus_text(value)
            result: dict[str, Any] = {}
            for key in [
                "stage",
                "agent",
                "team_context",
                "subtask",
                "state_summary",
                "design_team",
                "stage_gate_policy",
                "hierarchical_learning_context",
            ]:
                if key in value:
                    result[key] = compact_for_retry(value[key], depth + 1)
            for key in ["candidate_stage_artifact", "candidate_template_selection"]:
                candidate = value.get(key)
                if isinstance(candidate, dict):
                    result[key] = compact_template_selection_for_retry(candidate, focus_text)
            if "source_sacg_state" in value:
                result["source_sacg_state"] = value["source_sacg_state"]
            return result
        keys = sorted(value.keys())
        if depth >= 2:
            return {"_type": "dict", "_size": len(value), "_keys": [str(key) for key in keys[:6]]}
        keep = {
            "agent",
            "stage",
            "role",
            "title",
            "objective",
            "constraints",
            "artifact_focus",
            "acceptance_checkers",
            "status",
            "errors",
            "warnings",
            "num_nodes",
            "num_edges",
            "num_constraints",
            "constraint_ids",
            "evidence_fields",
            "tool_names",
            "selected_template_ids",
            "selected_templates",
            "missing_ops",
            "stage_gate_policy",
            "checker_results",
            "parameter_bindings",
            "template_source_checks",
            "attention_semantics",
            "cross_layer_trace",
            "unsupported_bindings",
            "required_adapters",
            "candidate_verification_plan",
            "candidate_verification_artifact_contract",
            "candidate_verification_review_artifact",
            "retry_reconciliation_contract",
            "stage6_gate_dag_refinement_policy",
            "design_team",
            "verification_result",
            "gate_execution_plan",
            "hierarchical_gate_summary",
            "hierarchical_learning_context",
            "source_sacg_state",
            "verification_capability_repair_package",
            "repair_step",
        }
        selected = [key for key in keys if key in keep][:12]
        priority_keys = ("hierarchical_learning_context",)
        for priority_key in priority_keys:
            if priority_key not in keys or priority_key in selected:
                continue
            replacement = next(
                (
                    index
                    for index, selected_key in enumerate(selected)
                    if selected_key not in priority_keys
                ),
                None,
            )
            if replacement is None:
                selected.append(priority_key)
            else:
                selected[replacement] = priority_key
        if not selected:
            selected = keys[:6]
        result = {str(key): compact_for_retry(value[key], depth + 1) for key in selected}
        if len(keys) > len(selected):
            result["_more_keys"] = len(keys) - len(selected)
        return result
    return str(value)


def compact_hierarchical_learning_context(value: Any) -> dict[str, Any]:
    """Project validated lower-layer knowledge into prompt-relevant facts."""

    if not isinstance(value, dict):
        return {}
    certificates = [
        {
            key: copy.deepcopy(row[key])
            for key in ("scope", "level_id", "claim")
            if key in row and row[key] not in (None, "", [])
        }
        | {
            "required_gate_count": len(row.get("required_gates", []))
        }
        for row in value.get("validated_lower_layer_certificates", [])
        if isinstance(row, dict)
    ]
    timing_fields = (
        "kind",
        "pipeline_semantics",
        "accepted_trace_record_count",
        "trace_record_count",
        "planned_stage_count",
        "maximum_concurrent_stage_count",
        "all_planned_stages_concurrent_observed",
        "all_planned_stages_participate_in_required_overlap",
        "all_planned_stages_same_cycle_concurrency_required",
        "required_dependency_overlap_complete",
        "stage_turnover_gaps_are_diagnostic",
        "boundary_order_summary",
        "required_direct_dependency_overlap_summary",
        "lesson",
    )
    timing = [
        {
            key: copy.deepcopy(row[key])
            for key in timing_fields
            if key in row and row[key] not in (None, "", [])
        }
        for row in value.get("kernel_timing_knowledge", [])
        if isinstance(row, dict)
    ]
    lesson_fields = (
        "scope",
        "failure_class",
        "summary",
        "lesson",
        "root_cause",
        "repair",
    )
    lessons: list[dict[str, Any]] = []
    seen_lessons: set[str] = set()
    for row in value.get("resolved_evidence_lessons", []):
        if not isinstance(row, dict):
            continue
        projection = {
            key: copy.deepcopy(row[key])
            for key in lesson_fields
            if key in row and row[key] not in (None, "", [])
        }
        identity = _canonical_json(projection)
        if projection and identity not in seen_lessons:
            seen_lessons.add(identity)
            lessons.append(projection)
    raw_policy = value.get("decision_policy", {})
    raw_policy = raw_policy if isinstance(raw_policy, dict) else {}
    policy = {
        str(key): nested
        for key, nested in raw_policy.items()
        if isinstance(nested, bool)
    }
    result: dict[str, Any] = {}
    if certificates:
        result["validated_lower_layers"] = certificates
    if timing:
        result["connected_kernel_timing"] = timing
    if lessons:
        result["resolved_mechanism_lessons"] = lessons
    if policy:
        result["decision_policy"] = policy
    if result:
        return result
    if value.get("status") == "no_validated_lower_layer_evidence":
        return {}
    return copy.deepcopy(value)


def compact_retry_prompt(
    agent: str,
    stage: str,
    task: str,
    inputs: dict[str, Any],
    output_schema: dict[str, Any],
    prompt_rules: list[str] | None = None,
    *,
    proactive: bool = False,
) -> str:
    retry_inputs = {"stage": stage, "agent": agent, **inputs}
    package = inputs.get("verification_capability_repair_package")
    generation_phase = (
        package.get("generation_phase_contract", {})
        if isinstance(package, dict)
        else {}
    )
    post_vcs_board_repair = bool(
        agent == "exact_board_integration_generation_agent"
        and isinstance(package, dict)
        and isinstance(generation_phase, dict)
        and generation_phase.get("status") == "repair_existing_board_sources"
        and generation_phase.get("current_vcs_feedback_ready") is True
    )
    current_trace_lower_layer_repair = bool(
        agent == "verification_capability_repair_agent"
        and has_proven_board_to_lower_layer_contradiction(package)
    )
    if post_vcs_board_repair or current_trace_lower_layer_repair:
        focused_package = compact_verification_capability_repair_package(
            copy.deepcopy(package)
        )
        focused_package.pop("relevant_repair_experience", None)
        focused_package.pop("relevant_project_knowledge", None)
        compact_inputs = {
            "stage": stage,
            "agent": agent,
            "verification_capability_repair_package": focused_package,
        }
        learning_context = inputs.get("hierarchical_learning_context")
        if not isinstance(learning_context, dict):
            learning_context = {}
        if not learning_context and inputs.get("source_sacg_state"):
            try:
                learning_context = hierarchical_learning_context(
                    read_sacg_json(Path(str(inputs["source_sacg_state"]))),
                    **stage_agent_memory_scope(inputs),
                )
            except Exception:
                learning_context = {}
        compact_learning_context = compact_hierarchical_learning_context(
            learning_context
        )
        if compact_learning_context:
            compact_inputs["hierarchical_learning_context"] = (
                compact_learning_context
            )
    else:
        compact_inputs = _deduplicate_compact_projection(
            compact_for_retry(retry_inputs)
        )
    if agent == "exact_board_integration_generation_agent":
        request_errors = exact_board_compact_request_errors(compact_inputs)
        if request_errors:
            raise ValueError(
                "exact-board compact request preflight failed: "
                + "; ".join(request_errors)
            )
    implementation_schema = "file_edits" in output_schema.get("properties", {})
    prompt_inputs: dict[str, Any] = {
        "stage": stage,
        "agent": agent,
        "compact_inputs": _canonical_json(compact_inputs),
    }
    if not implementation_schema:
        prompt_inputs["action_grounding_registry"] = _canonical_json(ACTION_GROUNDING_REGISTRY)
        prompt_inputs["action_contract_examples"] = _canonical_json(ACTION_CONTRACT_EXAMPLES)
    rules = [
        (
        "This is an evidence-preserving compact implementation request selected before transport because the complete audit prompt exceeds the configured provider-safe size."
            if proactive
            else "This is an evidence-preserving compact retry after transient provider failures or oversized prompt transport failure."
        ),
        "Use only the compact inputs and named constraints. The compact inputs preserve original evidence by path, sha256, schema/status fields, interface summaries, module headers, and source/compile indexes.",
        "For a Layer-3 post-VCS repair, compact_inputs.verification_capability_repair_package.current_board_vcs_feedback.current_signal_epoch is the only dynamic hardware evidence. Use every current internal boundary and stage signal in that object together with the current SACG/CCTG frontier. Do not use prior observation plans, old probe values, old signal epochs, or execution acceleration details as hardware evidence. Complete editable source text is an edit surface only: labels, comments, or helper code inside it are not runtime evidence.",
        "If the output schema requires file_edits, return complete content for create/replace edits. For operation=replace_text on an existing non-JSON source, use content='' and exact unique old_text/new_text anchors; include expected_sha256 whenever the task-specific source contract requires an exact current hash. The framework materializes anchored edits into the complete final file and rejects any missing, ambiguous, overlapping, or stale anchor. Never return ellipses, prose patches, or instructions for a human to finish.",
        "For functional verification, random generation may create only the input stimulus. Expected output must be target-model inference using the same model-weight artifact and input; never accept random or RTL-derived golden data.",
        "Do not infer DUT real-weight consumption from file existence. Require complete-scope tensor hashes, a bound loader/harness, and executed evidence.",
        "If the current-run policy omits atol, rtol, or max_mismatch_fraction, accept the frozen framework loose defaults recorded in numeric_comparison_resolution. This initial resolution is authorized; never derive or loosen it from DUT output.",
        "Preserve the numeric policy, comparison tolerance, model-weight artifact hash, stimulus hash, and expected-output hash throughout repair.",
        "Board-level acceptance requires source-hash identity with the exact user sample-project wrapper; a simplified wrapper is not equivalent.",
        "For board integration, exact simulation behavior is preserved by the hash-bound source files and compile authority; do not replace them with a behavioral or idealized model.",
        "Layer-3 observation must be unconditional: never gate a probe or snapshot on output_accept_count, partial output, upstream progress, valid/ready/fire, stall classification, or any other signal value. Record the selected frontier signals on a fixed sampling cadence and again at every terminal event, even when all counts are zero. Set probe_plan.trigger_condition to 'always' and describe only the fixed cadence/terminal window in bounded_window.",
        "For Layer-3 observation deepening, use the already compiled broad observation source. Select the complete relevant scalar set from compiled_signal_catalog and return file_edits=[]. The executor writes only current_selection.json and restores the same verified snapshot. A missing condition must not suppress observation; zero-valued records are valid evidence.",
        "For every Layer-3 deepen_simulation_observation decision, return an observation_delta that names the missing distinction, candidate root causes, selected real DUT scalar expressions from compiled_signal_catalog, expected signal patterns, and candidate_cause_checks. Walk backward and forward from the first stopped boundary. Every candidate_cause_checks row must map a cause to selected catalog expressions and explain what alternative it separates. Do not modify SystemVerilog merely to change observation focus, and do not return an earlier selection unchanged.",
        "Compact JSON may use lossless columnar indexes and JSON-pointer $ref objects. Resolve column names, path_prefixes, views, and refs before reasoning; expand aliases and refs to real absolute paths in file_edits.",
        "If compact inputs include checker_results, parameter_bindings, template_source_checks, attention_semantics, or cross_layer_trace, treat those fields as supplied evidence.",
        "If compact inputs include candidate_verification_artifact_contract, candidate_verification_plan, retry_reconciliation_contract, or design_team, treat their visible status, summary, policy, node counts, error lists, and checker summaries as supplied Stage6 evidence; do not claim the evidence is absent merely because compact retry omitted full nested details.",
        "If compact inputs include stage_gate_policy, report only current-stage blockers in risks and move later-stage obligations to proposed_actions.",
        "Return conservative review findings; mark evidence as not_run only when the relevant field is absent from compact inputs.",
    ]
    if prompt_rules:
        rules.append(
            "All original task-specific rules below remain authoritative after compaction."
        )
        rules.extend(prompt_rules)
    if not implementation_schema:
        rules.extend(
            [
                "Ground executable_actions in action_grounding_registry. Use exact listed tool_roles and acceptance_checkers whenever possible.",
                "If a missing capability is required, name it planned_tool.<short_name> or planned_checker.<short_name>; do not invent free-form tool roles such as verification_planner or tool_runner.",
                "Before returning, self-check every executable action: each tool_roles entry must be listed in action_grounding_registry.tool_roles or start with planned_tool.; each acceptance_checkers entry must be listed in action_grounding_registry.acceptance_checkers or start with planned_checker.",
            ]
        )
    rules.append("Return one JSON object only.")
    return build_prompt(
        agent=f"{agent}_compact_retry",
        task=task,
        inputs=prompt_inputs,
        output_schema=output_schema,
        rules=rules,
    )


def compact_retry_reasoning_effort(fallback: str | None = None) -> str | None:
    """Keep compact retries at the caller's reasoning level unless overridden."""

    override = os.environ.get("SPATIALACC_COMPACT_RETRY_REASONING_EFFORT", "").strip()
    return override or fallback or stage_worker_reasoning_effort() or resolved_llm_cfg().reasoning_effort


def _json_pointer_lookup(root: Any, pointer: str) -> tuple[bool, Any]:
    if pointer == "#":
        return True, root
    if not pointer.startswith("#/"):
        return False, None
    current = root
    for raw_token in pointer[2:].split("/"):
        token = raw_token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict) and token in current:
            current = current[token]
            continue
        if isinstance(current, list):
            try:
                index = int(token)
            except ValueError:
                return False, None
            if 0 <= index < len(current):
                current = current[index]
                continue
        return False, None
    return True, current


def _resolve_compact_dedup_references(
    root: dict[str, Any], value: Any, stack: set[str] | None = None
) -> Any:
    active = set() if stack is None else set(stack)
    if isinstance(value, dict):
        pointer = value.get("$ref")
        if (
            isinstance(pointer, str)
            and pointer.startswith("#/")
            and set(value).issubset({"$ref", "value_sha256"})
        ):
            if pointer in active:
                raise ValueError(f"cyclic compact JSON pointer: {pointer}")
            found, target = _json_pointer_lookup(root, pointer)
            if not found:
                raise ValueError(f"unresolved compact JSON pointer: {pointer}")
            resolved = _resolve_compact_dedup_references(
                root, target, active | {pointer}
            )
            expected_sha = str(value.get("value_sha256") or "")
            if expected_sha and _hash_text(_canonical_json(resolved)) != expected_sha:
                raise ValueError(f"compact JSON pointer digest differs: {pointer}")
            return resolved
        return {
            str(key): _resolve_compact_dedup_references(root, child, active)
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [
            _resolve_compact_dedup_references(root, child, active) for child in value
        ]
    return value


def _compact_source_id_selection(
    root: dict[str, Any], selection: Any
) -> list[str] | None:
    if isinstance(selection, list) and all(isinstance(value, str) for value in selection):
        return list(selection)
    if not isinstance(selection, dict):
        return None
    encoded_ids = selection.get("source_ids")
    if isinstance(encoded_ids, dict):
        try:
            values = [str(value) for value in _decode_encoded_column(encoded_ids)]
        except (TypeError, ValueError):
            return None
    else:
        pointer = str(selection.get("$ref") or "")
        found, target = _json_pointer_lookup(root, pointer)
        if not found:
            return None
        try:
            target = _resolve_compact_dedup_references(root, target)
        except ValueError:
            return None
        view_name = str(selection.get("view") or "")
        if view_name and isinstance(target, dict):
            view = target.get("views", {}).get(view_name, {})
            if not isinstance(view, dict):
                return None
            column = str(view.get("column") or "source_id")
            try:
                values = [
                    str(value)
                    for value in _decode_encoded_column(
                        _resolve_compact_dedup_references(
                            root, target.get("columns", {}).get(column, {})
                        )
                    )
                ]
            except (TypeError, ValueError):
                return None
            row_ranges = view.get("row_ranges_inclusive")
            if isinstance(row_ranges, list):
                selected_indices = {
                    index
                    for row_range in row_ranges
                    if isinstance(row_range, list)
                    and len(row_range) == 2
                    and all(isinstance(bound, int) for bound in row_range)
                    for index in range(row_range[0], row_range[1] + 1)
                }
                values = [
                    value for index, value in enumerate(values) if index in selected_indices
                ]
            view_excluded = {
                str(value) for value in view.get("exclude_source_ids", [])
            }
            view_included = view.get("include_source_ids")
            if isinstance(view_included, list):
                included = {str(value) for value in view_included}
                values = [value for value in values if value in included]
            values = [value for value in values if value not in view_excluded]
        else:
            selected_field = str(selection.get("selected_field") or "source_id")
            if isinstance(target, dict) and target.get("encoding") == (
                "spatialaccagent.lossless_dictionary_column_rows.v1"
            ):
                try:
                    rows = _decode_lossless_columnar_rows(
                        _resolve_compact_dedup_references(root, target)
                    )
                except (TypeError, ValueError):
                    return None
                values = [
                    str(row[selected_field])
                    for row in rows
                    if isinstance(row, dict) and row.get(selected_field)
                ]
            elif isinstance(target, list):
                values = [
                    str(row[selected_field])
                    for row in target
                    if isinstance(row, dict) and row.get(selected_field)
                ]
            else:
                return None
    excluded = selection.get("exclude_source_ids")
    if isinstance(excluded, dict):
        try:
            excluded_values = {
                str(value) for value in _decode_encoded_column(excluded)
            }
        except (TypeError, ValueError):
            return None
        values = [value for value in values if value not in excluded_values]
    return values


def _compact_vcs_plan_contract_errors(
    plan: Any,
    authority: dict[str, Any],
    rewrite: dict[str, Any],
) -> list[str]:
    if not isinstance(plan, dict):
        return ["manifest_ready_vcs_compile_plan is not an object"]

    def contains_ref(value: Any) -> bool:
        if isinstance(value, dict):
            return "$ref" in value or any(contains_ref(child) for child in value.values())
        if isinstance(value, list):
            return any(contains_ref(child) for child in value)
        return False

    errors: list[str] = []
    validation_mode = str(
        authority.get("validation_mode") or "exact_sample_physical_ddr"
    )

    def compile_authority_is_complete(value: Any) -> bool:
        if not isinstance(value, dict) or not all(
            value.get(field)
            for field in (
                "vivado_facts_path",
                "vivado_facts_sha256",
                "simulator_export_context_sha256s",
            )
        ):
            return False
        if validation_mode == "compute_slot_axi":
            return (
                value.get("external_fixture_contract_sha256") in {None, ""}
                and value.get("external_fixture_export_context_sha256s") == []
            )
        return bool(
            value.get("external_fixture_contract_sha256")
            and value.get("external_fixture_export_context_sha256s")
        )

    if plan.get("representation") == "framework_materialization_certificate":
        binding = rewrite.get("executor_preservation_contract", {}).get(
            "vcs_compile_plan_binding", {}
        )
        if not (
            isinstance(binding, dict)
            and binding.get("agent_must_not_copy_or_reconstruct_ordered_commands")
            is True
        ):
            errors.append("framework VCS plan certificate has no executor binding contract")
        if (
            plan.get("schema_version")
            != "spatialaccagent.framework_vcs_plan_binding.v1"
            or plan.get("status") != "ready"
            or plan.get("framework_materialized_by")
            != "apply_agent_file_edits.bind_framework_vcs_compile_plan"
        ):
            errors.append("framework VCS plan binding certificate is incomplete")
        if re.fullmatch(
            r"[0-9a-f]{64}", str(plan.get("source_plan_canonical_sha256") or "")
        ) is None:
            errors.append("framework VCS plan certificate has no canonical source-plan hash")
        compile_source_hash = str(
            plan.get("compile_source_ids_canonical_sha256") or ""
        )
        authority_source_hash = str(
            plan.get("ordered_source_ids_authority_canonical_sha256") or ""
        )
        if (
            re.fullmatch(r"[0-9a-f]{64}", compile_source_hash) is None
            or compile_source_hash != authority_source_hash
        ):
            errors.append(
                "framework VCS plan certificate source order is not authority-bound"
            )
        command_count = plan.get("ordered_command_count")
        compile_count = plan.get("compile_command_count")
        source_count = plan.get("compile_source_count")
        expected_count = authority.get("counts", {}).get("total_sources")
        if not (
            isinstance(command_count, int)
            and isinstance(compile_count, int)
            and command_count == compile_count + 1
            and isinstance(source_count, int)
            and (not isinstance(expected_count, int) or source_count == expected_count)
        ):
            errors.append("framework VCS plan certificate counts differ from authority")
        final_command = plan.get("final_elaboration_command")
        if not isinstance(final_command, dict) or contains_ref(final_command):
            errors.append("framework VCS plan certificate has no literal final elaboration")
        elif (
            final_command.get("order") != command_count - 1
            or final_command.get("phase") != "elaborate"
            or final_command.get("source_ids") != []
            or str(plan.get("top_module") or "")
            not in final_command.get("argv", [])
            or str(plan.get("output") or "") not in final_command.get("argv", [])
        ):
            errors.append("framework VCS plan certificate final elaboration differs")
        required_globals = authority.get("external_fixture", {}).get(
            "required_global_simulator_source_ids", []
        )
        if (
            isinstance(required_globals, list)
            and required_globals
            and (
                plan.get("required_global_simulator_source_ids")
                != required_globals
                or not isinstance(final_command, dict)
                or "xil_defaultlib.glbl" not in final_command.get("argv", [])
            )
        ):
            errors.append("framework VCS plan certificate omits global simulation binding")
        compile_authority = plan.get("compile_authority")
        if not compile_authority_is_complete(compile_authority):
            errors.append("framework VCS plan certificate compile_authority is incomplete")
        return list(dict.fromkeys(errors))

    if contains_ref(plan):
        errors.append("manifest_ready_vcs_compile_plan contains unresolved $ref values")
    commands = plan.get("ordered_commands")
    if not isinstance(commands, list) or not commands:
        errors.append("manifest_ready_vcs_compile_plan.ordered_commands is not a non-empty list")
        commands = []
    compile_source_ids: list[str] = []
    elaboration: list[dict[str, Any]] = []
    shell_tokens = {"|", "||", "&&", ";", ">", ">>", "<", "2>&1", "tee"}
    for index, command in enumerate(commands):
        if not isinstance(command, dict):
            errors.append(f"ordered_commands[{index}] is not an object")
            continue
        if command.get("order") != index:
            errors.append(f"ordered_commands[{index}].order is not contiguous")
        phase = str(command.get("phase") or "")
        executable = str(command.get("executable") or "")
        argv = command.get("argv")
        source_ids = command.get("source_ids")
        if not executable or not isinstance(argv, list) or not isinstance(source_ids, list):
            errors.append(f"ordered_commands[{index}] lacks executable/argv/source_ids")
            continue
        token_source_ids = [
            str(token.get("source_id") or "")
            for token in argv
            if isinstance(token, dict) and set(token) == {"source_id"}
        ]
        if list(map(str, source_ids)) != token_source_ids:
            errors.append(f"ordered_commands[{index}] source_ids differ from argv source tokens")
        literal_tokens = [token for token in argv if isinstance(token, str)]
        if executable in literal_tokens[:1]:
            errors.append(f"ordered_commands[{index}] duplicates its executable in argv")
        if any(token in shell_tokens for token in literal_tokens):
            errors.append(f"ordered_commands[{index}] contains shell transport tokens")
        if any(
            token.startswith("-") and any(char.isspace() for char in token)
            for token in literal_tokens
        ):
            errors.append(f"ordered_commands[{index}] contains a bundled whitespace option token")
        if phase == "compile":
            if literal_tokens.count("-work") != 1:
                errors.append(
                    f"ordered_commands[{index}] compile argv does not contain exactly one -work"
                )
            if not token_source_ids:
                errors.append(f"ordered_commands[{index}] compile command has no source token")
            compile_source_ids.extend(token_source_ids)
        elif phase == "elaborate":
            elaboration.append(command)
            if token_source_ids:
                errors.append(f"ordered_commands[{index}] elaboration contains source tokens")
        else:
            errors.append(f"ordered_commands[{index}] has unsupported phase {phase!r}")
    if len(compile_source_ids) != len(set(compile_source_ids)):
        errors.append("manifest-ready compile commands contain duplicate source IDs")
    expected_count = authority.get("counts", {}).get("total_sources")
    if isinstance(expected_count, int) and len(compile_source_ids) != expected_count:
        errors.append(
            f"manifest-ready compile source count {len(compile_source_ids)} != authority {expected_count}"
        )
    if len(elaboration) != 1 or not commands or commands[-1] not in elaboration:
        errors.append("manifest-ready plan does not end with exactly one elaboration command")
    elif (
        str(plan.get("top_module") or "") not in elaboration[0].get("argv", [])
        or str(plan.get("output") or "") not in elaboration[0].get("argv", [])
    ):
        errors.append("manifest-ready elaboration does not bind top_module and output")
    compile_authority = plan.get("compile_authority")
    if not compile_authority_is_complete(compile_authority):
        errors.append("manifest-ready compile_authority is incomplete")
    return list(dict.fromkeys(errors))


def _checkpoint_hook_compact_request_errors(
    compact_inputs: dict[str, Any],
    package: dict[str, Any],
) -> list[str]:
    """Validate the specialist's exact two-file authority without board-plan fields."""

    try:
        resolved = _resolve_compact_dedup_references(compact_inputs, package)
    except (TypeError, ValueError) as exc:
        return [f"checkpoint specialist compact references are invalid: {exc}"]
    if not isinstance(resolved, dict):
        return ["checkpoint specialist compact package is not an object"]
    errors: list[str] = []
    if resolved.get("schema_version") != (
        "spatialaccagent.checkpoint_hook_specialist_package.v1"
    ):
        errors.append("checkpoint specialist schema_version is invalid")
    if resolved.get("status") != "ready" or resolved.get("blockers"):
        errors.append("checkpoint specialist package is not ready")

    source = resolved.get("current_testbench_source", {})
    source = source if isinstance(source, dict) else {}
    content = source.get("content")
    source_path = str(source.get("path") or "")
    source_sha256 = str(source.get("sha256") or "")
    if (
        source.get("complete_current_source") is not True
        or not isinstance(content, str)
        or not content
        or not source_path
    ):
        errors.append("checkpoint specialist lacks the complete current testbench source")
    elif hashlib.sha256(content.encode("utf-8")).hexdigest() != source_sha256:
        errors.append("checkpoint specialist testbench content hash differs")

    atomic = resolved.get("atomic_edit_contract", {})
    atomic = atomic if isinstance(atomic, dict) else {}
    manifest = atomic.get("manifest", {})
    manifest = manifest if isinstance(manifest, dict) else {}
    testbench = atomic.get("testbench", {})
    testbench = testbench if isinstance(testbench, dict) else {}
    allowed = atomic.get("allowed_and_required_paths", [])
    allowed_paths = [str(value) for value in allowed] if isinstance(allowed, list) else []
    if (
        atomic.get("all_or_nothing") is not True
        or atomic.get("exact_edit_count") != 2
        or atomic.get("no_production_rtl_edit") is not True
        or len(allowed_paths) != 2
        or len(set(allowed_paths)) != 2
    ):
        errors.append("checkpoint specialist atomic two-file authority is invalid")
    if (
        manifest.get("operation") != "merge_json"
        or manifest.get("required_patch_root")
        != [
            "board_simulation_preflight_plan",
            "testbench",
            "simulation_checkpoint_contract",
        ]
        or str(manifest.get("path") or "") not in allowed_paths
        or not str(manifest.get("expected_sha256") or "")
    ):
        errors.append("checkpoint specialist manifest merge authority is invalid")
    if (
        testbench.get("operation") != "replace_text"
        or str(testbench.get("path") or "") != source_path
        or str(testbench.get("path") or "") not in allowed_paths
        or testbench.get("expected_sha256") != source_sha256
        or testbench.get(
            "one_or_more_nonoverlapping_unique_old_text_new_text_pairs"
        )
        is not True
    ):
        errors.append("checkpoint specialist testbench edit authority is invalid")

    checkpoint_authority = resolved.get("checkpoint_authority", {})
    checkpoint_authority = (
        checkpoint_authority if isinstance(checkpoint_authority, dict) else {}
    )
    if not isinstance(
        checkpoint_authority.get("required_manifest_contract"), dict
    ) or not checkpoint_authority.get("required_manifest_contract"):
        errors.append("checkpoint specialist required manifest contract is missing")
    if not isinstance(resolved.get("capability_gap"), dict):
        errors.append("checkpoint specialist capability gap is missing")
    return list(dict.fromkeys(errors))


def _semantic_rtl_compact_request_errors(package: dict[str, Any]) -> list[str]:
    """Validate the smaller package used by an internal generated-RTL repair."""

    errors: list[str] = []
    bundle = package.get("repair_source_bundle")
    bundle = bundle if isinstance(bundle, dict) else {}
    editable = bundle.get("editable_contract")
    editable = editable if isinstance(editable, dict) else {}
    allowed = editable.get("localized_allowed_exact_files", [])
    allowed_paths = (
        [str(value) for value in allowed if str(value)]
        if isinstance(allowed, list)
        else []
    )
    if not allowed_paths:
        errors.append("semantic RTL repair has no current editable RTL source closure")
    documents = [
        row for row in bundle.get("documents", []) if isinstance(row, dict)
    ]
    document_by_source = {
        str(row.get(field)): row
        for row in documents
        for field in ("path", "source_path")
        if row.get(field)
    }
    if not documents:
        errors.append("semantic RTL repair has no supplied RTL source documents")
    for document in documents:
        path = str(document.get("source_path") or document.get("path") or "")
        content = document.get("content")
        expected_sha256 = str(document.get("sha256") or "")
        if path not in allowed_paths:
            errors.append(f"semantic RTL source is outside the editable closure: {path}")
            continue
        if not isinstance(content, str) or not content:
            errors.append(f"semantic RTL source is not complete: {path}")
            continue
        if (
            not expected_sha256
            or hashlib.sha256(content.encode("utf-8")).hexdigest()
            != expected_sha256
        ):
            errors.append(f"semantic RTL source hash differs: {path}")
    return list(dict.fromkeys(errors))


def exact_board_compact_request_errors(compact_inputs: dict[str, Any]) -> list[str]:
    """Fail fast on compact exact-board inputs that the manifest consumer cannot use."""

    errors: list[str] = []
    package = compact_inputs.get("verification_capability_repair_package")
    if not isinstance(package, dict):
        return ["compact request has no verification_capability_repair_package"]
    if package.get("schema_version") == (
        "spatialaccagent.checkpoint_hook_specialist_package.v1"
    ):
        return _checkpoint_hook_compact_request_errors(compact_inputs, package)
    if package.get("generation_mode") == "board_semantic_rtl_repair":
        return _semantic_rtl_compact_request_errors(package)
    generation_phase = package.get("generation_phase_contract")
    if (
        isinstance(generation_phase, dict)
        and generation_phase.get("status") == "repair_existing_board_sources"
        and generation_phase.get("current_vcs_feedback_ready") is True
    ):
        feedback = package.get("current_board_vcs_feedback")
        if not isinstance(feedback, dict) or feedback.get("status") != "ready":
            errors.append("post-VCS board repair lacks the current real-tool failure")
        bundle = package.get("repair_source_bundle")
        bundle = bundle if isinstance(bundle, dict) else {}
        editable = bundle.get("editable_contract")
        editable = editable if isinstance(editable, dict) else {}
        documents = [
            row for row in bundle.get("documents", []) if isinstance(row, dict)
        ]
        documents_by_path = {
            str(row.get("path") or ""): row
            for row in documents
            if row.get("path")
        }
        current_sources = editable.get("current_board_source_files", [])
        if isinstance(current_sources, dict) and current_sources.get("encoding") == (
            "spatialaccagent.lossless_dictionary_column_rows.v1"
        ):
            try:
                current_sources = _decode_lossless_columnar_rows(current_sources)
            except (TypeError, ValueError):
                current_sources = []
        if not isinstance(current_sources, list) or not current_sources:
            errors.append("post-VCS board repair has no current editable board sources")
            current_sources = []
        for source in current_sources:
            if not isinstance(source, dict):
                errors.append("post-VCS board source identity is not an object")
                continue
            path = str(source.get("path") or "")
            expected_sha256 = str(source.get("sha256") or "")
            document = documents_by_path.get(path, {})
            content = document.get("content")
            if not path or not isinstance(content, str) or not content:
                errors.append(f"post-VCS board source is not complete: {path or '<missing>'}")
                continue
            content_sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
            if (
                not expected_sha256
                or document.get("sha256") != expected_sha256
                or content_sha256 != expected_sha256
            ):
                errors.append(f"post-VCS board source hash differs: {path}")
        manifest_content_required = bundle.get("manifest_content_required") is True
        if manifest_content_required:
            manifest = editable.get("current_board_manifest_file")
            manifest = manifest if isinstance(manifest, dict) else {}
            manifest_path = str(manifest.get("path") or "")
            manifest_document = documents_by_path.get(manifest_path, {})
            if (
                not manifest_path
                or manifest_document.get("sha256") != manifest.get("sha256")
                or not isinstance(manifest_document.get("json_content"), dict)
            ):
                errors.append("post-VCS board repair lacks the complete editable manifest")
        return list(dict.fromkeys(errors))
    bundle = package.get("repair_source_bundle")
    bundle = bundle if isinstance(bundle, dict) else {}
    editable = bundle.get("editable_contract")
    editable = editable if isinstance(editable, dict) else {}
    rewrite = editable.get("board_manifest_rewrite_authority")
    rewrite = rewrite if isinstance(rewrite, dict) else {}
    expanded = rewrite.get("expanded_source_authority")
    expanded = expanded if isinstance(expanded, dict) else {}
    authority = expanded.get("vcs_command_rewrite_authority")
    authority = authority if isinstance(authority, dict) else {}
    plan = authority.get("manifest_ready_vcs_compile_plan")
    errors.extend(_compact_vcs_plan_contract_errors(plan, authority, rewrite))

    def contains_ref(value: Any) -> bool:
        if isinstance(value, dict):
            return "$ref" in value or any(contains_ref(child) for child in value.values())
        if isinstance(value, list):
            return any(contains_ref(child) for child in value)
        return False

    manifest_documents = [
        row
        for row in bundle.get("documents", [])
        if isinstance(row, dict)
        and Path(str(row.get("path") or "")).name == "dut_weight_binding_manifest.json"
    ]
    if len(manifest_documents) != 1 or not isinstance(
        manifest_documents[0].get("json_content") if manifest_documents else None,
        dict,
    ):
        errors.append("compact request does not contain one literal editable board manifest")
    elif contains_ref(manifest_documents[0]["json_content"]):
        errors.append("editable board manifest json_content contains unresolved $ref values")

    def visit_refs(value: Any, path: str = "#") -> None:
        if isinstance(value, dict):
            pointer = value.get("$ref")
            if isinstance(pointer, str) and pointer.startswith("#/"):
                found, _ = _json_pointer_lookup(compact_inputs, pointer)
                if not found:
                    errors.append(f"compact JSON pointer is unresolved at {path}: {pointer}")
            for key, child in value.items():
                visit_refs(
                    child,
                    path + "/" + str(key).replace("~", "~0").replace("/", "~1"),
                )
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit_refs(child, f"{path}/{index}")

    visit_refs(compact_inputs)

    tensor_contract = rewrite.get("complete_transformer_block_tensor_hashes")
    if isinstance(tensor_contract, dict) and isinstance(tensor_contract.get("hashes"), dict):
        tensor_ref = tensor_contract["hashes"]
        found, tensor_hashes = _json_pointer_lookup(
            compact_inputs, str(tensor_ref.get("$ref") or "")
        )
        if not found or not isinstance(tensor_hashes, list):
            errors.append("complete tensor hash reference does not resolve to a literal list")
        elif (
            tensor_ref.get("row_count") != len(tensor_hashes)
            or tensor_ref.get("canonical_sha256")
            != _canonical_json_sha256(tensor_hashes)
        ):
            errors.append("complete tensor hash reference count or canonical hash differs")

    sample_authority = expanded.get("sample_sources")
    if isinstance(sample_authority, dict) and sample_authority.get("encoding") == (
        "spatialaccagent.sample_source_rewrite_join.v1"
    ):
        classification_values: list[str] = []
        for selection in sample_authority.get("classification_views", {}).values():
            values = _compact_source_id_selection(compact_inputs, selection)
            if values is None:
                errors.append("sample source classification view is not resolvable")
                continue
            if (
                selection.get("row_count") != len(values)
                or selection.get("canonical_sha256") != _canonical_json_sha256(values)
            ):
                errors.append("sample source classification view count or hash differs")
            classification_values.extend(values)
        if (
            len(classification_values) != sample_authority.get("row_count")
            or len(classification_values) != len(set(classification_values))
        ):
            errors.append("sample source classification views are not a disjoint complete cover")
        disposition_values: list[str] = []
        for selection in sample_authority.get(
            "transformed_disposition_views", {}
        ).values():
            values = _compact_source_id_selection(compact_inputs, selection)
            if values is None:
                errors.append("sample source disposition view is not resolvable")
                continue
            if (
                selection.get("row_count") != len(values)
                or selection.get("canonical_sha256") != _canonical_json_sha256(values)
            ):
                errors.append("sample source disposition view count or hash differs")
            disposition_values.extend(values)
        if sorted(disposition_values) != sorted(classification_values):
            errors.append("sample source disposition views differ from classification coverage")

    external_authority = expanded.get("external_fixture_sources")
    if isinstance(external_authority, dict) and external_authority.get("encoding") == (
        "spatialaccagent.external_fixture_source_rewrite_view.v1"
    ):
        try:
            selection_roles = _decode_encoded_column(
                _resolve_compact_dedup_references(
                    compact_inputs, external_authority.get("selection_roles", {})
                )
            )
        except (TypeError, ValueError):
            selection_roles = []
        fixture_ids = _compact_source_id_selection(
            compact_inputs,
            {
                **external_authority.get("source_rows", {}),
                "selected_field": "source_id",
            },
        )
        if (
            len(selection_roles) != external_authority.get("row_count")
            or fixture_ids is None
            or len(fixture_ids) != external_authority.get("row_count")
            or external_authority.get("selection_roles_canonical_sha256")
            != _canonical_json_sha256(selection_roles)
        ):
            errors.append("external fixture source view differs from compile-source authority")

    coverage = rewrite.get("compile_source_coverage_authority")
    if isinstance(coverage, dict):
        for field in (
            "available_external_fixture_compile_source_ids",
            "certified_kernel_source_ids",
            "preserved_sample_compile_source_ids",
        ):
            selection = coverage.get(field)
            if not isinstance(selection, dict) or "$ref" not in selection:
                continue
            values = _compact_source_id_selection(compact_inputs, selection)
            if values is None:
                errors.append(f"{field} compact source view is not resolvable")
            elif (
                selection.get("row_count") != len(values)
                or selection.get("canonical_sha256") != _canonical_json_sha256(values)
            ):
                errors.append(f"{field} compact source view count or hash differs")
    return list(dict.fromkeys(errors))


def stage_worker_reasoning_effort() -> str | None:
    raw = os.environ.get("SPATIALACC_STAGE_WORKER_REASONING_EFFORT", "").strip()
    return raw or None


def llm_schema_repair_attempts() -> int:
    try:
        value = int(os.environ.get("SPATIALACC_LLM_SCHEMA_REPAIR_ATTEMPTS", "3"))
    except ValueError:
        value = 3
    return max(1, min(value, 5))


def llm_schema_repair_retry_unbounded() -> bool:
    return retry_bool_env(
        "SPATIALACC_LLM_SCHEMA_REPAIR_RETRY_UNBOUNDED",
        llm_transient_retry_unbounded(),
    )


def llm_schema_repair_retry_sleep_seconds(repair_attempt: int) -> float:
    base = retry_float_env("SPATIALACC_LLM_SCHEMA_REPAIR_RETRY_BASE_SEC", 8.0)
    maximum = retry_float_env("SPATIALACC_LLM_SCHEMA_REPAIR_RETRY_MAX_SEC", 90.0)
    overflow = max(0, repair_attempt - llm_schema_repair_attempts())
    return min(maximum, base * (2 ** overflow))


def stage_agent_memory_scope(inputs: dict[str, Any]) -> dict[str, str]:
    """Resolve hierarchy identity for verification and repair operational history."""

    explicit_debug_layer = str(inputs.get("debug_layer") or "")
    explicit_verification_scope = str(
        inputs.get("verification_scope") or inputs.get("execution_scope") or ""
    )
    package = inputs.get("verification_capability_repair_package", {})
    package = package if isinstance(package, dict) else {}
    step = inputs.get("repair_step", {})
    step = step if isinstance(step, dict) else {}
    action = step.get("action", {}) if isinstance(step.get("action"), dict) else {}
    verification_result = inputs.get("verification_result", {})
    verification_result = (
        verification_result if isinstance(verification_result, dict) else {}
    )
    repair_loop = (
        verification_result.get("hierarchical_repair_loop", {})
        if isinstance(verification_result.get("hierarchical_repair_loop"), dict)
        else {}
    )
    current_layer = (
        repair_loop.get("current_layer", {})
        if isinstance(repair_loop.get("current_layer"), dict)
        else {}
    )
    repair_plan = inputs.get("candidate_repair_plan", {})
    repair_plan = repair_plan if isinstance(repair_plan, dict) else {}
    repair_diagnostics = (
        repair_plan.get("diagnostics", {})
        if isinstance(repair_plan.get("diagnostics"), dict)
        else {}
    )
    planned_repair_loop = (
        repair_diagnostics.get("hierarchical_repair_loop", {})
        if isinstance(repair_diagnostics.get("hierarchical_repair_loop"), dict)
        else {}
    )
    planned_current_layer = (
        planned_repair_loop.get("current_layer", {})
        if isinstance(planned_repair_loop.get("current_layer"), dict)
        else {}
    )
    is_hierarchy_prompt = bool(
        package
        or step
        or verification_result
        or repair_plan
        or explicit_debug_layer
        or explicit_verification_scope
        or isinstance(inputs.get("semantic_template_repair_phase_bundle"), dict)
    )
    if not is_hierarchy_prompt:
        return {}
    debug_layer = str(
        explicit_debug_layer
        or package.get("debug_layer")
        or action.get("debug_layer")
        or step.get("debug_layer")
        or current_layer.get("id")
        or planned_current_layer.get("id")
        or ""
    )
    verification_scope = str(
        explicit_verification_scope
        or package.get("verification_scope")
        or verification_result.get("execution_scope")
        or verification_result.get("gate_execution_scope")
        or ""
    )
    context = hierarchy_memory_context(
        verification_scope=verification_scope,
        debug_layer=debug_layer,
    )
    return {
        key: str(context[key])
        for key in ("verification_scope", "debug_layer")
        if context.get(key)
    }


def build_stage_agent_prompt_inputs(
    inputs: dict[str, Any],
) -> tuple[dict[str, Any], bool, dict[str, Any]]:
    """Build the exact dynamic prompt inputs used by every stage worker."""

    source_state = inputs.get("source_sacg_state")
    repair_package = inputs.get("verification_capability_repair_package", {})
    generation_phase = (
        repair_package.get("generation_phase_contract", {})
        if isinstance(repair_package, dict)
        else {}
    )
    post_vcs_board_repair = bool(
        isinstance(generation_phase, dict)
        and generation_phase.get("status") == "repair_existing_board_sources"
        and generation_phase.get("current_vcs_feedback_ready") is True
    )
    current_trace_lower_layer_repair = has_proven_board_to_lower_layer_contradiction(
        repair_package
    )
    memory_scope = stage_agent_memory_scope(inputs)
    memory_context: dict[str, Any] = {}
    memory_truth: dict[str, Any] = {}
    learning_context: dict[str, Any] = {}
    if source_state:
        try:
            source_data = read_sacg_json(Path(str(source_state)))
            if not post_vcs_board_repair:
                memory_context = (
                    scoped_sacg_memory_summary(source_data, **memory_scope)
                    if memory_scope
                    else sacg_memory_summary(source_data)
                )
                memory_truth = (
                    scoped_sacg_memory_truth(source_data, **memory_scope)
                    if memory_scope
                    else sacg_memory_truth(source_data)
                )
            learning_context = hierarchical_learning_context(source_data, **memory_scope)
        except Exception:
            memory_context = {}
            memory_truth = {}
            learning_context = {}
    checkpoint_hook_specialist = bool(
        isinstance(repair_package, dict)
        and repair_package.get("schema_version")
        == "spatialaccagent.checkpoint_hook_specialist_package.v1"
    )
    if post_vcs_board_repair or current_trace_lower_layer_repair:
        prompt_inputs = {
            key: value
            for key, value in inputs.items()
            if key not in {"repair_step", "source_sacg_state"}
        }
        if isinstance(prompt_inputs.get("verification_capability_repair_package"), dict):
            prompt_inputs["verification_capability_repair_package"] = (
                compact_verification_capability_repair_package(
                    prompt_inputs["verification_capability_repair_package"]
                )
            )
        empty_lower_layer_status = (
            learning_context.get("status") == "no_validated_lower_layer_evidence"
            and not learning_context.get("validated_lower_layer_certificates")
        )
        if learning_context and not empty_lower_layer_status:
            prompt_inputs["hierarchical_learning_context"] = (
                compact_hierarchical_learning_context(learning_context)
            )
        else:
            learning_context = {}
        prompt_inputs["hot_loop_context_policy"] = {
            "current_failure_and_editable_sources_only": True,
            "broad_sacg_history_and_action_catalogs_omitted": True,
            "durable_raw_reports_and_completed_experience_remain_on_disk": True,
        }
    else:
        prompt_inputs = {**inputs, "llm_policy": llm_policy_summary()}
    if not checkpoint_hook_specialist and not post_vcs_board_repair:
        prompt_inputs["sacg_memory"] = memory_context
        prompt_inputs["sacg_memory_truth"] = memory_truth
        prompt_inputs["hierarchical_learning_context"] = learning_context
        prompt_inputs["action_grounding_registry"] = ACTION_GROUNDING_REGISTRY
        prompt_inputs["action_contract_examples"] = ACTION_CONTRACT_EXAMPLES
    elif checkpoint_hook_specialist:
        prompt_inputs["specialist_context_policy"] = {
            "broad_sacg_history_omitted": True,
            "broad_action_registry_omitted": True,
            "current_failure_testbench_checkpoint_authority_and_atomic_edit_contract_are_complete": True,
        }
    return (
        prompt_inputs,
        checkpoint_hook_specialist,
        learning_context,
    )


def run_stage_agent(
    agent: str,
    stage: str,
    task: str,
    inputs: dict[str, Any],
    out_dir: Path,
    fallback_summary: str,
    output_schema: dict[str, Any] | None = None,
    prompt_rules: list[str] | None = None,
) -> dict[str, Any]:
    """Run one stage-local LLM worker and return its structured output record."""

    active_schema = output_schema or STAGE_AGENT_SCHEMA
    active_rules = prompt_rules or [
        "Review only the supplied artifact summary and named constraints.",
        "If inputs include subtask.role_assignment, act as that chip-design-team specialist: stay inside its mission, primary_responsibilities, decision_authority, collaboration_interfaces, and out_of_scope boundaries.",
        "For sub-agent work, make observations, risks, approval_required_for, and executable_actions usable by peer agents through the declared handoff_to and acceptance_checkers; do not silently assume another specialist's responsibility.",
        "Treat sacg_memory as the shared long-context design memory: preserve design goals, failure lessons, retry requests, backtrack requests, and contamination barriers.",
        "Treat sacg_memory_truth as the authoritative current blocker set: only active_contamination_barriers and open retry/backtrack requests listed there are current SACG-memory blockers.",
        "Do not infer active blockers from historical, closed, superseded, rejected, or recently summarized records when sacg_memory_truth shows the corresponding active/open count is zero.",
        "If sacg_memory contains open backtrack_requests or contamination_barriers relevant to this stage, address them explicitly in observations and executable_actions.",
        "If inputs include a retry_reconciliation_contract for the current stage, distinguish previous failed artifacts from the candidate retry artifacts: same-stage retry requests/barriers are downstream-consumption blockers until promotion, but they are not independent blockers for approving a refined current-stage contract that explicitly supersedes them after all current-stage checks pass.",
        "If inputs include stage_gate_policy, use it to classify current-stage blocking risks versus later-stage actions.",
        "If inputs include role_slice_policy or presence_summary, do not infer a field is missing merely because detailed rows were omitted from a compact/role-specific prompt slice.",
        "When presence_summary says an artifact class exists, report missing-detail concerns as handoff/action items unless the visible checker status proves a current-stage blocker.",
        "Report cross-layer consistency risks across model, shape, numeric policy, data order, memory, runtime, implementation, and board facts.",
        "Keep actions bounded and executable by later tools/checkers.",
        "Populate executable_actions with concrete next tool/repair actions; each action must name consumed artifacts, produced artifacts, tool roles, acceptance checkers, failure handling, and approval need.",
        "Ground executable_actions in action_grounding_registry. Use exact listed tool_roles and acceptance_checkers whenever possible; do not invent Qwen/OPT-specific core names unless they are supplied by the case adapter or tool protocol.",
        "For backend/app-shell target discovery, treat the LLM as the adaptive board-integration engineer: convert supplied board materials and real Vivado evidence into target_discovery_policy updates with cited artifacts; if evidence is ambiguous, require bounded approval instead of guessing names.",
        "If a missing capability is required, name it planned_tool.<short_name> or planned_checker.<short_name> and state the implementation gap in rationale.",
        "Before returning, self-check every executable action: each tool_roles entry must be listed in action_grounding_registry.tool_roles or start with planned_tool.; each acceptance_checkers entry must be listed in action_grounding_registry.acceptance_checkers or start with planned_checker.",
        "For verification/backend failures, executable_actions must drive the next stage/tool decision instead of relying on static scripts or human memory.",
        "For hardware debug, enforce the three-layer repair loop: first operator/leaf modules, then the connected single-transformer-layer kernel, then the board-accurate AXI/DDR wrapped system. A failed layer must enter tool-output -> CCTG/contract-guided localization -> bounded repair -> rerun, and must not promote or skip to a higher layer.",
        "When hierarchical_learning_context is supplied, treat it as live hash-validated lower-layer knowledge rather than informal history. Reuse its certified invariants, and reopen a lower layer only for a current trace that explicitly contradicts a named invariant.",
        "When hierarchical_learning_context supplies connected-kernel timing knowledge, preserve its elastic variable-latency token-pipeline semantics: required boundary order and cross-token overlap matter, while strict same-cycle start/end across unequal-latency stages is not required.",
        "At board scope, distinguish independent AXI/prefetch progress from output or lifecycle-frontier progress. A current frontier stall localizes what to observe next, but is neither a pass claim nor a preselected RTL root cause.",
        "A board output-frontier symptom alone cannot reopen a certified connected kernel. Require a current hash-bound lower-layer contradiction with direct core start, ingress, egress, named causal-boundary, and current-certificate evidence before scheduling lower-layer revalidation.",
        "Before any functional pass, require a complete target-checkpoint tensor catalog, deterministic or real input provenance, target-model inference expected outputs for the same input/checkpoint, a resolved numeric comparison tolerance (current-run values first, otherwise frozen framework loose defaults), generated semantic testbench hashes, and proof that the DUT consumed every required bound weight.",
        "Applying the recorded framework loose defaults for initially missing atol, rtol, or max_mismatch_fraction is authorized and is not a repair-time tolerance change. Never derive or loosen those values from DUT output.",
        "A random generator may produce input stimulus only. Never generate expected output randomly, derive it from RTL output, replace model inference with an identity/default implementation, or treat sampled weights as complete evidence.",
        "During repair, keep checkpoint, stimulus, target-model reference, numeric policy, tolerance, testbench contract, and exact board-wrapper source hashes immutable. Repair the DUT, loader/harness, instrumentation, or integration that violated the contract.",
        "At the third layer, use the exact wrapper and simulation sources discovered from the current user-supplied sample project. Do not substitute a simplified AXI/DDR wrapper or hardcode model, board, module, or path names into framework-core actions.",
        "Treat Transformer blocks as the complete accelerator scope. Exclude embedding/tokenization, final model norm, LM head/logits, and sampling from DUT implementation, DUT weight coverage, and acceptance golden boundaries.",
        "When a verifier capability is missing, classify it as a checker/golden-reference repair, not as hardware correctness. When real RTL/tool evidence shows liveness, value, order, or protocol failure, localize the earliest causal boundary/module before proposing a code repair.",
        "Use approval_required_for for architecture, pipeline, memory layout, numeric policy, or major template changes.",
    ]
    llm_dir = out_dir / "llm"
    llm_dir.mkdir(parents=True, exist_ok=True)
    source_state = inputs.get("source_sacg_state")
    (
        prompt_inputs,
        checkpoint_hook_specialist,
        learning_context,
    ) = build_stage_agent_prompt_inputs(inputs)
    prompt_path = llm_dir / f"{agent}_prompt.md"
    retry_prompt_path = llm_dir / f"{agent}_compact_retry_prompt.md"
    result_path = llm_dir / f"{agent}_result.json"
    repair_package = inputs.get("verification_capability_repair_package", {})
    generation_phase = (
        repair_package.get("generation_phase_contract", {})
        if isinstance(repair_package, dict)
        else {}
    )
    exact_board_post_vcs_repair = bool(
        agent == "exact_board_integration_generation_agent"
        and isinstance(generation_phase, dict)
        and generation_phase.get("status") == "repair_existing_board_sources"
        and generation_phase.get("current_vcs_feedback_ready") is True
    )
    current_trace_lower_layer_repair = bool(
        agent == "verification_capability_repair_agent"
        and has_proven_board_to_lower_layer_contradiction(repair_package)
    )
    exact_board_rejected_transaction_retry = bool(
        agent == "exact_board_integration_generation_agent"
        and isinstance(repair_package, dict)
        and isinstance(
            repair_package.get("current_patch_application_feedback"), dict
        )
        and repair_package["current_patch_application_feedback"].get("status")
        == "ready"
    )
    request_path = prompt_path
    # A post-VCS board repair or a proven board-to-kernel contradiction already
    # has a bounded evidence package. Persisting the broad history hides the
    # current causal proof and adds no implementation authority.
    focused_capability_repair_prompt = (
        exact_board_post_vcs_repair or current_trace_lower_layer_repair
    )
    full_prompt: str | None = None
    proactive_compaction = False
    if focused_capability_repair_prompt:
        prompt = compact_retry_prompt(
            agent,
            stage,
            task,
            inputs,
            active_schema,
            active_rules,
            proactive=True,
        )
    else:
        full_prompt = build_prompt(
            agent=agent,
            task=task,
            inputs=prompt_inputs,
            output_schema=active_schema,
            rules=active_rules,
        )
        prompt = full_prompt
        prompt_byte_count = len(prompt.encode("utf-8"))
        proactive_compaction = bool(
            "file_edits" in active_schema.get("properties", {})
            and llm_auto_compact_retry()
            and (
                prompt_byte_count >= llm_auto_compact_min_prompt_bytes()
                or (
                    checkpoint_hook_specialist
                    and prompt_byte_count
                    >= checkpoint_specialist_auto_compact_min_prompt_bytes()
                )
            )
        )
        if proactive_compaction:
            prompt = compact_retry_prompt(
                agent,
                stage,
                task,
                inputs,
                active_schema,
                active_rules,
                proactive=True,
            )
            request_path = retry_prompt_path
    current_prompt_hash = prompt_hash(prompt)

    live_transaction_file = live_llm_transaction_path(llm_dir, agent)
    ensure_no_active_live_llm_transaction(live_transaction_file)
    # Board repair must consume the current Layer-3 trace on every turn.  A
    # cached implementation response can repeat an old rejected decision and
    # prevent the Agent from seeing the latest internal signals.
    cached = None if agent == "exact_board_integration_generation_agent" else (
        cached_stage_worker_record(
            result_path,
            current_prompt_hash,
            agent,
            active_schema,
        )
    )
    if cached is not None:
        print(f"[stage:{stage}:llm] reuse cached {agent}: {result_path}", file=sys.stderr, flush=True)
        return cached

    superseded_artifact_snapshot = archive_replaced_stage_worker_artifacts(
        result_path,
        prompt_path,
        retry_prompt_path,
        current_prompt_hash,
    )
    if focused_capability_repair_prompt:
        prompt_path.write_text(prompt, encoding="utf-8")
        if retry_prompt_path.exists():
            retry_prompt_path.unlink()
    else:
        prompt_path.write_text(full_prompt or "", encoding="utf-8")
    if proactive_compaction:
        retry_prompt_path.write_text(prompt, encoding="utf-8")

    record: dict[str, Any] = {
        "schema_version": "spatialaccagent.stage_worker_record.v0",
        "prompt_protocol": PROMPT_PROTOCOL,
        "prompt_hash": current_prompt_hash,
        "agent": agent,
        "stage": stage,
        "request_path": str(request_path),
        "prompt_bytes": len(prompt.encode("utf-8")),
        "result_path": str(result_path),
        "mode": llm_mode(),
        "used_fallback": False,
        "error": None,
        "output": None,
    }
    if superseded_artifact_snapshot is not None:
        record["supersedes_artifact_snapshot"] = superseded_artifact_snapshot
    if focused_capability_repair_prompt:
        record.update(
            {
                "prompt_compaction_protocol": PROMPT_COMPACTION_PROTOCOL,
                "proactive_prompt_compaction": True,
            }
        )
    elif proactive_compaction:
        record.update(
            {
                "full_prompt_path": str(prompt_path),
                "full_prompt_bytes": len(full_prompt.encode("utf-8")),
                "compact_retry_request_path": str(retry_prompt_path),
                "prompt_compaction_protocol": PROMPT_COMPACTION_PROTOCOL,
                "compact_retry_prompt_hash": current_prompt_hash,
                "compact_retry_prompt_bytes": len(prompt.encode("utf-8")),
                "proactive_prompt_compaction": True,
            }
        )

    mode = llm_mode()
    enforce = llm_enforce()
    if mode.strip().lower() in {"", "off", "none", "disabled"}:
        record["error"] = f"LLM mode is disabled: {mode}"
        record["output"] = llm_error_output(agent, stage, record["error"], fallback_summary)
        write_json(result_path, record)
        if enforce:
            raise StageLLMError(record["error"])
        print(f"[stage:{stage}:llm] skipped {agent}: {record['error']}", file=sys.stderr, flush=True)
        return record

    llm = resolved_llm_cfg()
    record["stream"] = llm.stream
    record["transport"] = "responses_sse_stream" if llm.stream else "responses_json"
    record["http_transport"] = llm.http_transport
    record["max_output_tokens"] = llm.max_output_tokens
    if llm.configuration_error:
        record["error"] = llm.configuration_error
        record["output"] = llm_error_output(agent, stage, record["error"], fallback_summary)
        write_json(result_path, record)
        if enforce:
            raise StageLLMError(record["error"])
        print(f"[stage:{stage}:llm] skipped {agent}: {record['error']}", file=sys.stderr, flush=True)
        return record
    key = llm.api_key
    endpoint = llm.endpoint
    model = llm.model
    record["model"] = model
    timeout_sec = llm_timeout_sec()
    if not key or not endpoint:
        record["error"] = "missing LLM endpoint or API key"
        record["output"] = llm_error_output(agent, stage, record["error"], fallback_summary)
        write_json(result_path, record)
        if enforce:
            raise StageLLMError(record["error"])
        print(f"[stage:{stage}:llm] skipped {agent}: {record['error']}", file=sys.stderr, flush=True)
        return record
    if not model:
        record["error"] = "missing LLM model"
        record["output"] = llm_error_output(agent, stage, record["error"], fallback_summary)
        write_json(result_path, record)
        if enforce:
            raise StageLLMError(record["error"])
        print(f"[stage:{stage}:llm] skipped {agent}: {record['error']}", file=sys.stderr, flush=True)
        return record

    worker_effort = stage_worker_reasoning_effort()
    record["reasoning_effort"] = worker_effort or llm.reasoning_effort
    live_transaction = begin_live_llm_transaction(
        live_transaction_file,
        agent=agent,
        stage=stage,
        prompt_hash_value=current_prompt_hash,
        prompt_path=request_path,
        prompt_bytes=len(prompt.encode("utf-8")),
        result_path=result_path,
        model=model,
        reasoning_effort=worker_effort or llm.reasoning_effort,
        stream=llm.stream,
        context_binding=_live_transaction_context_binding(
            source_state,
            learning_context,
        ),
        http_transport=llm.http_transport,
    )
    live_transaction_id = str(live_transaction["transaction_id"])
    record["live_transaction_path"] = str(live_transaction_file)
    record["live_transaction_id"] = live_transaction_id

    def observe_transaction(event: dict[str, Any]) -> None:
        update_live_llm_transaction(
            live_transaction_file,
            live_transaction_id,
            event,
        )

    def finish_transaction(
        status: str,
        *,
        output_status: str | None = None,
        error: str | None = None,
    ) -> None:
        try:
            finish_live_llm_transaction(
                live_transaction_file,
                live_transaction_id,
                status=status,
                result_path=result_path,
                output_status=output_status,
                error=error,
            )
        except Exception as finish_exc:
            print(
                "[stage:llm] live transaction ledger completion failed: "
                f"{_bounded_live_error(finish_exc)}",
                file=sys.stderr,
                flush=True,
            )

    started = time.monotonic()
    print(f"[stage:{stage}:llm] start {agent}", file=sys.stderr, flush=True)
    print(f"[stage:{stage}:llm] prompt {request_path}", file=sys.stderr, flush=True)
    raw_text = ""
    try:
        try:
            raw_text, retry_errors = call_llm_with_retry(
                endpoint,
                key,
                model,
                prompt,
                f"{agent}_json",
                active_schema,
                timeout_sec,
                reasoning_effort=worker_effort,
                transaction_observer=observe_transaction,
            )
        except Exception as first_exc:
            context_window_failure = llm_context_window_error(first_exc)
            if not transient_llm_error(first_exc) and not context_window_failure:
                raise
            allow_compact_retry = (
                isinstance(first_exc, PromptCompactionNeeded)
                or context_window_failure
                or os.environ.get("SPATIALACC_STAGE_LLM_ALLOW_COMPACT_RETRY", "0").strip().lower()
                in {"1", "true", "yes", "on"}
            )
            if not allow_compact_retry:
                record["compact_retry_disabled_after_error"] = str(first_exc)
                raise
            retry_prompt = compact_retry_prompt(
                agent,
                stage,
                task,
                inputs,
                active_schema,
                active_rules,
            )
            retry_prompt_path.write_text(retry_prompt, encoding="utf-8")
            record["compact_retry_request_path"] = str(retry_prompt_path)
            record["prompt_compaction_protocol"] = PROMPT_COMPACTION_PROTOCOL
            record["compact_retry_prompt_hash"] = prompt_hash(retry_prompt)
            record["compact_retry_prompt_bytes"] = len(retry_prompt.encode("utf-8"))
            record["compact_retry_after_error"] = str(first_exc)
            raw_text, retry_errors = call_llm_with_retry(
                endpoint,
                key,
                model,
                retry_prompt,
                f"{agent}_compact_retry_json",
                active_schema,
                timeout_sec,
                reasoning_effort=compact_retry_reasoning_effort(
                    worker_effort or llm.reasoning_effort
                ),
                allow_auto_compact=False,
                transaction_observer=observe_transaction,
            )
            retry_errors = [f"full prompt failed: {first_exc}", *retry_errors]
        if retry_errors:
            record["retry_errors"] = retry_errors
        record["raw_text"] = raw_text
        try:
            output = parse_json_object(raw_text)
            validate_schema(output, active_schema, agent)
        except Exception as parse_exc:
            record["parse_error"] = str(parse_exc)
            invalid_text = raw_text
            validation_error = str(parse_exc)
            schema_repair_records: list[dict[str, Any]] = []
            output = None
            configured_repair_attempts = llm_schema_repair_attempts()
            max_repair_attempts = (
                None
                if llm_schema_repair_retry_unbounded()
                else configured_repair_attempts
            )
            repair_attempt = 1
            while max_repair_attempts is None or repair_attempt <= max_repair_attempts:
                fix_prompt = repair_prompt(
                    agent,
                    prompt,
                    invalid_text,
                    validation_error,
                    active_schema,
                )
                repair_text, repair_retry_errors = call_llm_with_retry(
                    endpoint,
                    key,
                    model,
                    fix_prompt,
                    f"{agent}_repair_{repair_attempt}_json",
                    active_schema,
                    timeout_sec,
                    reasoning_effort=worker_effort,
                    transaction_observer=observe_transaction,
                )
                repair_artifact_path = (
                    llm_dir / f"{agent}_schema_repair_{repair_attempt:02d}.txt"
                )
                repair_artifact_path.write_text(repair_text, encoding="utf-8")
                repair_record = {
                    "attempt": repair_attempt,
                    "input_validation_error": validation_error,
                    "output_path": str(repair_artifact_path),
                    "output_sha256": hashlib.sha256(
                        repair_text.encode("utf-8")
                    ).hexdigest(),
                    "output_bytes": len(repair_text.encode("utf-8")),
                    "transport_retry_errors": repair_retry_errors,
                }
                record["repair_raw_text"] = repair_text
                if repair_retry_errors:
                    record["repair_retry_errors"] = repair_retry_errors
                try:
                    candidate = parse_json_object(repair_text)
                    validate_schema(candidate, active_schema, agent)
                except Exception as repair_exc:
                    validation_error = str(repair_exc)
                    invalid_text = repair_text
                    repair_record["status"] = "invalid"
                    repair_record["output_validation_error"] = validation_error
                    schema_repair_records.append(repair_record)
                    if (
                        max_repair_attempts is None
                        and repair_attempt >= configured_repair_attempts
                    ):
                        delay = llm_schema_repair_retry_sleep_seconds(
                            repair_attempt
                        )
                        print(
                            f"[stage:{stage}:llm] retry {agent} after "
                            f"schema-invalid output (unbounded attempt "
                            f"{repair_attempt}): {validation_error}; "
                            f"sleep {delay:.1f}s",
                            file=sys.stderr,
                            flush=True,
                        )
                        time.sleep(delay)
                    repair_attempt += 1
                    continue
                repair_record["status"] = "pass"
                schema_repair_records.append(repair_record)
                output = candidate
                break
            record["schema_repair_attempts"] = schema_repair_records
            if output is None:
                raise ValueError(
                    f"{agent} remained schema-invalid after "
                    f"{len(schema_repair_records)} serial repair attempts: "
                    f"{validation_error}"
                )
        record["used_fallback"] = False
        record["duration_sec"] = time.monotonic() - started
        record["output"] = output
        write_json(result_path, record)
        finish_transaction(
            "completed",
            output_status=str(output.get("status") or ""),
        )
        print(f"[stage:{stage}:llm] done {agent} ({record['duration_sec']:.1f}s)", file=sys.stderr, flush=True)
        print(f"[stage:{stage}:llm] output {agent}: {compact_json(output, 900)}", file=sys.stderr, flush=True)
        print(f"[stage:{stage}:llm] log {result_path}", file=sys.stderr, flush=True)
        return record
    except Exception as exc:
        record["error"] = str(exc)
        record["duration_sec"] = time.monotonic() - started
        if raw_text:
            record["raw_text"] = raw_text
        record["used_fallback"] = False
        record["output"] = llm_error_output(agent, stage, str(exc), fallback_summary)
        write_json(result_path, record)
        finish_transaction("failed", error=str(exc))
        print(f"[stage:{stage}:llm] failed {agent}: {exc}", file=sys.stderr, flush=True)
        print(f"[stage:{stage}:llm] log {result_path}", file=sys.stderr, flush=True)
        if enforce:
            raise StageLLMError(str(exc)) from exc
        return record
