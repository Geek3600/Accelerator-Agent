"""Create a bounded repair plan from verification results."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from accagent.framework.case_adapter import build_case_adapter, refresh_builtin_case_adapter
from accagent.framework.flow_action_handoff import validate_stage6_flow_handoff
from accagent.framework.board_backtrack_evidence import (
    board_to_lower_layer_contradiction_from_diagnosis,
)
from accagent.framework.repair_loop import build_repair_loop_report
from accagent.framework.sacg_store import SACGStore
from accagent.framework.sacg_utils import (
    artifact_path,
    copy_state,
    hierarchy_memory_context,
    read_json,
    run_dir_from_state,
    write_json,
)
from accagent.framework.stage_entry import run_sacg_stage
from accagent.framework.stage_llm import llm_enforce, run_stage_agent
from accagent.framework.stage_team import run_design_team, team_summary


TOUCHED_CONSTRAINTS = [
    "constraint.verification.plan",
    "constraint.tool.protocols",
    "constraint.human.boundary",
    "constraint.case.adapter",
]

DIAGNOSIS_APPLICABILITY_BINDING_SCHEMA_VERSION = (
    "spatialaccagent.diagnosis_applicability_binding.v1"
)
REPAIR_EXECUTION_AGENT_CONTEXT_SCHEMA_VERSION = (
    "spatialaccagent.repair_execution_agent_context.v1"
)
REPAIR_FEEDBACK_ARTIFACT_REF_SCHEMA_VERSION = (
    "spatialaccagent.repair_feedback_artifact_ref.v1"
)
HIERARCHICAL_DEBUG_LAYERS = {
    "operator_leaf_modules",
    "single_transformer_layer_kernel",
    "board_axi_ddr_wrapped_system",
}
BOARD_LOWER_LAYER_RECHECK_LEDGER_SCHEMA_VERSION = (
    "spatialaccagent.board_lower_layer_recheck_ledger.v1"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def is_sha256(value: Any) -> bool:
    text = str(value or "")
    return len(text) == 64 and all(character in "0123456789abcdef" for character in text)


def board_lower_layer_recheck_ledger_path(run_dir: Path) -> Path:
    """Return the durable record for completed board-triggered layer checks."""

    return (
        run_dir.resolve()
        / "verification"
        / "repair_history"
        / "board_lower_layer_recheck_ledger.json"
    )


def board_lower_layer_recheck_source_binding(
    contradiction: dict[str, Any] | None,
) -> dict[str, str] | None:
    """Extract the source identity that makes a board-triggered recheck reusable."""

    if not isinstance(contradiction, dict) or contradiction.get("status") != "proven":
        return None
    evidence = contradiction.get("evidence", {})
    evidence = evidence if isinstance(evidence, dict) else {}
    binding = evidence.get("source_binding", {})
    binding = binding if isinstance(binding, dict) else {}
    fields = (
        "input_fingerprint_sha256",
        "board_trace_sha256",
        "lower_layer_certificate_sha256",
    )
    if not all(is_sha256(binding.get(field)) for field in fields):
        return None
    return {field: str(binding[field]) for field in fields}


def board_lower_layer_recheck_key(source_binding: dict[str, str]) -> str:
    return canonical_sha256(source_binding)


def _passing_single_layer_report_reference(
    capability_reports: list[dict[str, Any]] | None,
) -> dict[str, Any] | None:
    """Return one live, hash-bound passing single-layer report reference."""

    for row in capability_reports or []:
        if not isinstance(row, dict) or row.get("status") != "pass":
            continue
        path = Path(str(row.get("path") or ""))
        if not path.is_file():
            continue
        digest = sha256_file(path)
        try:
            report = read_json(path)
        except Exception:
            continue
        schema = str(report.get("schema_version") or "")
        if report.get("status") != "pass" or "single_layer" not in schema:
            continue
        return {
            "path": str(path.resolve()),
            "sha256": digest,
            "schema_version": schema,
        }
    return None


def record_board_lower_layer_recheck(
    run_dir: Path,
    contradiction: dict[str, Any] | None,
    *,
    capability_reports: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    """Persist a passing lower-layer recheck for exactly one board evidence set."""

    source_binding = board_lower_layer_recheck_source_binding(contradiction)
    if source_binding is None:
        return {
            "status": "invalid",
            "reason": "the board contradiction has no complete source binding",
        }
    report = _passing_single_layer_report_reference(capability_reports)
    if report is None:
        return {
            "status": "invalid",
            "reason": "the passing single-layer recheck report is unavailable",
        }

    path = board_lower_layer_recheck_ledger_path(run_dir)
    try:
        ledger = read_json(path) if path.is_file() else {}
    except Exception:
        ledger = {}
    entries = ledger.get("entries", {}) if isinstance(ledger.get("entries"), dict) else {}
    key = board_lower_layer_recheck_key(source_binding)
    entries[key] = {
        "status": "pass",
        "target_debug_layer": contradiction.get("target_debug_layer"),
        "source_binding": source_binding,
        "single_layer_recheck_report": report,
    }
    write_json(
        path,
        {
            "schema_version": BOARD_LOWER_LAYER_RECHECK_LEDGER_SCHEMA_VERSION,
            "entries": entries,
        },
    )
    return {
        "status": "pass",
        "path": str(path),
        "sha256": sha256_file(path),
        "source_binding": source_binding,
        "single_layer_recheck_report": report,
    }


def completed_board_lower_layer_recheck(
    run_dir: Path | None,
    contradiction: dict[str, Any] | None,
) -> dict[str, Any]:
    """Return a matching completed recheck only while its report remains valid."""

    source_binding = board_lower_layer_recheck_source_binding(contradiction)
    if run_dir is None or source_binding is None:
        return {"status": "not_found"}
    path = board_lower_layer_recheck_ledger_path(run_dir)
    if not path.is_file():
        return {"status": "not_found", "path": str(path)}
    try:
        ledger = read_json(path)
    except Exception:
        return {"status": "invalid", "path": str(path)}
    if ledger.get("schema_version") != BOARD_LOWER_LAYER_RECHECK_LEDGER_SCHEMA_VERSION:
        return {"status": "invalid", "path": str(path)}
    entries = ledger.get("entries", {})
    if not isinstance(entries, dict):
        return {"status": "invalid", "path": str(path)}
    entry = entries.get(board_lower_layer_recheck_key(source_binding))
    if not isinstance(entry, dict) or entry.get("status") != "pass":
        return {"status": "not_found", "path": str(path)}
    if entry.get("source_binding") != source_binding:
        return {"status": "invalid", "path": str(path)}
    report = (
        entry.get("single_layer_recheck_report", {})
        if isinstance(entry.get("single_layer_recheck_report"), dict)
        else {}
    )
    report_path = Path(str(report.get("path") or ""))
    report_sha256 = str(report.get("sha256") or "")
    if (
        not report_path.is_file()
        or not is_sha256(report_sha256)
        or sha256_file(report_path) != report_sha256
    ):
        return {"status": "invalid", "path": str(path)}
    try:
        report_value = read_json(report_path)
    except Exception:
        return {"status": "invalid", "path": str(path)}
    if (
        report_value.get("status") != "pass"
        or "single_layer" not in str(report_value.get("schema_version") or "")
    ):
        return {"status": "invalid", "path": str(path)}
    return {
        "status": "pass",
        "path": str(path),
        "sha256": sha256_file(path),
        "source_binding": source_binding,
        "single_layer_recheck_report": copy.deepcopy(report),
    }


def exact_board_identity_contract_passed(run_dir: Path) -> bool:
    """Return whether the current exact-board identity is reusable.

    Stage 6 may carry an older capability-refresh request in SACG state even
    after the discovery producer has completed.  Reusing the persisted,
    checker-visible identity avoids launching the same Vivado discovery again;
    any missing or malformed identity remains fail-closed.
    """

    if run_dir is None:
        return False
    path = (
        run_dir.resolve()
        / "verification"
        / "board_interface"
        / "board_source_identity.json"
    )
    if not path.is_file():
        return False
    try:
        value = read_json(path)
    except (OSError, ValueError, json.JSONDecodeError):
        return False
    if not isinstance(value, dict) or value.get("status") != "pass":
        return False
    validation = value.get("identity_contract_validation")
    if isinstance(validation, dict) and validation.get("status") != "pass":
        return False
    # A passing identity must retain the physical selection and source closure
    # that downstream exact-board integration consumes.
    selected = value.get("discovery_selected_source_ids")
    closure = value.get("selected_simulation_source_closure")
    closure_sources = (
        closure.get("source_files")
        if isinstance(closure, dict)
        else closure
    )
    return bool(
        value.get("compute_slot_abi")
        and value.get("axi_interfaces")
        and isinstance(selected, list)
        and selected
        and isinstance(closure_sources, list)
        and closure_sources
    )


def exact_reference_path(value: Any, base_dir: Path) -> Path:
    path = Path(str(value or ""))
    return path.resolve() if path.is_absolute() else (base_dir / path).resolve()


def prior_repair_execution_artifact(state: dict[str, Any]) -> dict[str, Any] | None:
    matches = [
        row
        for row in state.get("artifacts", [])
        if isinstance(row, dict) and row.get("id") == "artifact.stage6.repair_execution_report"
    ]
    if not matches:
        return None
    if len(matches) != 1:
        return {
            "id": "artifact.stage6.repair_execution_report",
            "_artifact_error": "source SACG contains duplicate repair execution report artifacts",
        }
    return matches[0]


def invalid_prior_repair_execution_feedback(
    blockers: list[str],
    *,
    report_path: Path | None = None,
    report_sha256: str | None = None,
) -> dict[str, Any]:
    identity = {
        "report_path": str(report_path) if report_path else None,
        "report_sha256": report_sha256,
        "validation_blockers": blockers,
    }
    return {
        "schema_version": "spatialaccagent.prior_repair_execution_feedback.v1",
        "status": "invalid",
        "summary": "prior repair execution feedback failed closed integrity validation",
        "blockers": blockers,
        "required_capabilities": [],
        "repair_execution_status": None,
        "execution_errors": [],
        "report": {
            "path": str(report_path) if report_path else None,
            "sha256": report_sha256,
        },
        "llm_records": [],
        "input_fingerprint_sha256": canonical_sha256(identity),
        "validation": {"status": "fail", "errors": blockers},
    }


def normalized_repair_execution_context(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    debug_layer = str(value.get("debug_layer") or "")
    if debug_layer not in HIERARCHICAL_DEBUG_LAYERS:
        return {}
    return {
        "schema_version": value.get("schema_version"),
        "repair_step_id": value.get("repair_step_id"),
        "repair_scope": value.get("repair_scope"),
        "verification_scope": value.get("verification_scope"),
        "debug_layer": debug_layer,
    }


def repair_execution_agent_context(record: dict[str, Any]) -> dict[str, Any]:
    """Return a validated hierarchy identity from a persisted Stage-6 LLM record."""

    for field in ("repair_execution_context", "capability_repair_context"):
        context = normalized_repair_execution_context(record.get(field))
        if context:
            return context
    return {}


def repair_execution_step_context(step: dict[str, Any]) -> dict[str, Any]:
    return normalized_repair_execution_context(
        step.get("repair_execution_context")
    )


def contexts_match(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return bool(left and right and left.get("debug_layer") == right.get("debug_layer"))


def validated_repair_feedback_artifacts(
    result: dict[str, Any],
    *,
    report_path: Path,
    expected_context: dict[str, Any],
    validation_errors: list[str],
    step_index: int,
) -> list[dict[str, Any]]:
    """Load hash-bound deterministic executor feedback for a subsequent LLM turn."""

    references = result.get("repair_feedback_artifacts", [])
    if references is None:
        return []
    if not isinstance(references, list):
        validation_errors.append(
            f"step_results[{step_index}] repair_feedback_artifacts is not a list"
        )
        return []
    observations: list[dict[str, Any]] = []
    for artifact_index, reference in enumerate(references):
        prefix = f"step_results[{step_index}].repair_feedback_artifacts[{artifact_index}]"
        if not isinstance(reference, dict):
            validation_errors.append(f"{prefix} is not an object")
            continue
        if reference.get("schema_version") != REPAIR_FEEDBACK_ARTIFACT_REF_SCHEMA_VERSION:
            validation_errors.append(f"{prefix} has an unsupported schema")
            continue
        kind = str(reference.get("kind") or "")
        path_value = reference.get("path")
        declared_sha256 = reference.get("sha256")
        context = normalized_repair_execution_context(
            reference.get("repair_execution_context")
        )
        if not kind or not isinstance(path_value, str) or not is_sha256(declared_sha256):
            validation_errors.append(f"{prefix} has an incomplete identity")
            continue
        if not context:
            validation_errors.append(f"{prefix} has no valid hierarchy context")
            continue
        if expected_context and not contexts_match(context, expected_context):
            validation_errors.append(
                f"{prefix} hierarchy context does not match its repair execution record"
            )
            continue
        path = exact_reference_path(path_value, report_path.parent)
        if not path.is_file():
            validation_errors.append(f"{prefix} referenced feedback artifact is missing: {path}")
            continue
        actual_sha256 = sha256_file(path)
        if actual_sha256 != declared_sha256:
            validation_errors.append(
                f"{prefix} referenced feedback artifact SHA-256 does not match"
            )
            continue
        try:
            artifact = read_json(path)
        except Exception as exc:
            validation_errors.append(
                f"{prefix} referenced feedback artifact is unreadable: {exc}"
            )
            continue
        status = str(artifact.get("status") or "")
        summary = str(artifact.get("summary") or "")
        blockers = artifact.get("blockers", [])
        validation = artifact.get("validation_errors", [])
        if not status or not isinstance(blockers, list) or any(
            not isinstance(value, str) for value in blockers
        ):
            validation_errors.append(f"{prefix} feedback artifact has invalid status or blockers")
            continue
        if not isinstance(validation, list) or any(
            not isinstance(value, str) for value in validation
        ):
            validation_errors.append(f"{prefix} feedback artifact has invalid validation_errors")
            continue
        observations.append(
            {
                "kind": kind,
                "status": status,
                "summary": summary,
                "blockers": [value for value in blockers if value],
                "validation_errors": [value for value in validation if value],
                "path": str(path),
                "sha256": actual_sha256,
                "repair_execution_context": context,
            }
        )
    return observations


def scope_prior_repair_execution_feedback(
    feedback: dict[str, Any],
    expected_debug_layer: str | None,
) -> dict[str, Any]:
    """Reuse prior Stage-6 results only when their producer layer matches exactly."""

    if (
        not expected_debug_layer
        or expected_debug_layer not in HIERARCHICAL_DEBUG_LAYERS
        or feedback.get("validation", {}).get("status") != "pass"
    ):
        return feedback
    records = (
        feedback.get("llm_records", [])
        if isinstance(feedback.get("llm_records"), list)
        else []
    )
    matching = [
        row
        for row in records
        if isinstance(row, dict)
        and isinstance(row.get("repair_execution_context"), dict)
        and row["repair_execution_context"].get("debug_layer")
        == expected_debug_layer
    ]
    selection = {
        "required_debug_layer": expected_debug_layer,
        "selected_record_count": len(matching),
        "excluded_unbound_or_other_layer_record_count": len(records) - len(matching),
        "policy": (
            "Only prior Stage-6 LLM records with an explicit matching debug layer "
            "are reusable. Historical unbound or other-layer records remain on disk "
            "but are not repair-planning evidence."
        ),
    }
    if not matching:
        identity = {
            "report": feedback.get("report", {}),
            "required_debug_layer": expected_debug_layer,
            "selection": selection,
        }
        return {
            "schema_version": "spatialaccagent.prior_repair_execution_feedback.v1",
            "status": "historical_only",
            "summary": (
                "no prior repair-execution LLM feedback is bound to the current "
                "hierarchy layer"
            ),
            "blockers": [],
            "required_capabilities": [],
            "repair_execution_status": "historical_only",
            "execution_errors": [],
            "report": copy.deepcopy(feedback.get("report", {})),
            "llm_records": [],
            "deterministic_feedback": [],
            "input_fingerprint_sha256": canonical_sha256(identity),
            "validation": {"status": "pass", "errors": []},
            "scope_selection": selection,
        }

    blockers: list[str] = []
    capabilities: list[dict[str, Any]] = []
    summaries: list[str] = []
    deterministic_feedback: list[dict[str, Any]] = []
    execution_errors: list[str] = []
    for record in matching:
        for blocker in record.get("blockers", []):
            if isinstance(blocker, str) and blocker and blocker not in blockers:
                blockers.append(blocker)
        for capability in record.get("required_capabilities", []):
            if not isinstance(capability, dict):
                continue
            if capability not in capabilities:
                capabilities.append(copy.deepcopy(capability))
        summary = str(record.get("summary") or "")
        if summary:
            summaries.append(summary)
        for observation in record.get("deterministic_feedback", []):
            if not isinstance(observation, dict):
                continue
            if observation not in deterministic_feedback:
                deterministic_feedback.append(copy.deepcopy(observation))
            for field in ("blockers", "validation_errors"):
                for blocker in observation.get(field, []):
                    if isinstance(blocker, str) and blocker and blocker not in blockers:
                        blockers.append(blocker)
                    if field == "validation_errors" and isinstance(blocker, str) and blocker and blocker not in execution_errors:
                        execution_errors.append(blocker)
            observation_summary = str(observation.get("summary") or "")
            if observation_summary:
                summaries.append(
                    f"{observation.get('kind')}: {observation_summary}"
                )
    statuses = {str(record.get("status") or "") for record in matching}
    if any(
        str(observation.get("status") or "").lower() in {"blocked", "fail"}
        for observation in deterministic_feedback
    ):
        feedback_status = "blocked"
    else:
        feedback_status = next(iter(statuses)) if len(statuses) == 1 else "mixed"
    identity = {
        "report": feedback.get("report", {}),
        "records": [
            {
                "path": row.get("path"),
                "sha256": row.get("sha256"),
                "input_fingerprint_sha256": row.get("input_fingerprint_sha256"),
            }
            for row in matching
        ],
        "deterministic_feedback": [
            {
                "kind": row.get("kind"),
                "path": row.get("path"),
                "sha256": row.get("sha256"),
                "repair_execution_context": row.get("repair_execution_context"),
            }
            for row in deterministic_feedback
        ],
        "selection": selection,
    }
    return {
        **feedback,
        "status": feedback_status,
        "summary": "; ".join(summaries),
        "blockers": blockers,
        "required_capabilities": capabilities,
        "execution_errors": execution_errors,
        "llm_records": matching,
        "deterministic_feedback": deterministic_feedback,
        "input_fingerprint_sha256": canonical_sha256(identity),
        "scope_selection": selection,
    }


def required_capability_repair_actions(
    feedback: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Materialize only explicitly requested, executor-supported producers."""

    if (
        not isinstance(feedback, dict)
        or feedback.get("validation", {}).get("status") != "pass"
        or feedback.get("status") != "blocked"
    ):
        return []
    actions: list[dict[str, Any]] = []
    for capability in feedback.get("required_capabilities", []):
        if not isinstance(capability, dict):
            return []
        capability_id = str(capability.get("capability_id") or "")
        debug_layer = str(capability.get("debug_layer") or "")
        producer_scope = str(capability.get("producer_scope") or "")
        target_modules = [
            str(value)
            for value in capability.get("target_modules", [])
            if str(value)
        ]
        required_evidence = [
            str(value)
            for value in capability.get("required_evidence", [])
            if str(value)
        ]
        empty_target_modules_allowed = (
            capability_id
            == "repair.reconcile_exact_board_lifecycle_cctg_observation_contract"
            and producer_scope == "causal_repair_context_pack"
            and debug_layer == "board_axi_ddr_wrapped_system"
        )
        if (
            not capability_id
            or not debug_layer
            or (not target_modules and not empty_target_modules_allowed)
            or not required_evidence
            or not str(capability.get("rationale") or "")
        ):
            return []
        action_debug_layer = debug_layer
        if (
            capability_id == "vcs_remote_stage_pruning_environment_recovery"
            and producer_scope == "remote_vcs_stage_pruning_environment"
            and debug_layer == "board_axi_ddr_wrapped_system"
        ):
            action_scope = "regression_rerun"
            repair_kind = capability_id
            producer_binding = {
                "tool": "case_vcs_functional_sim",
                "repair_gate": "case_vcs_functional_sim",
                "requested_producer_scope": producer_scope,
                "requested_capability_id": capability_id,
                "environment_recovery_required": True,
            }
        elif empty_target_modules_allowed:
            # This producer reconciles already recorded lifecycle facts. It has
            # no hardware module target by design and must never edit sources or
            # launch VCS.
            action_scope = "verification_capability_repair"
            repair_kind = capability_id
            producer_binding = {
                "repair_tool_role": "exact_board_lifecycle_cctg_reconciliation",
                "repair_gate": "case_vcs_functional_sim",
                "requested_producer_scope": producer_scope,
                "requested_capability_id": capability_id,
                "read_only_evidence_reconciliation": True,
            }
        elif (
            capability_id
            in {
                "planned_tool.operator_leaf_static_inventory_trace",
                "planned_checker.operator_leaf_static_inventory_trace_check",
            }
            and producer_scope == "operator_leaf_closure"
            and debug_layer == "operator_leaf_modules"
        ):
            action_scope = "verification_capability_repair"
            repair_kind = {
                "planned_tool.operator_leaf_static_inventory_trace": (
                    "operator_leaf_static_inventory_trace"
                ),
                "planned_checker.operator_leaf_static_inventory_trace_check": (
                    "operator_leaf_static_inventory_trace_check"
                ),
            }[capability_id]
            producer_binding = {
                "repair_gate": "case_stage_leaf_static",
                "requested_producer_scope": producer_scope,
                "requested_capability_id": capability_id,
                "read_only_generated_rtl_inventory": True,
            }
        elif producer_scope == "verification_capability_repair":
            action_scope = producer_scope
            repair_kind = capability_id
            producer_binding: dict[str, Any] = {}
        elif (
            capability_id == "exact_board_vivado_identity_authority_refresh.v1"
            and producer_scope
            == "real_vivado_exact_sample_project_discovery_selector_and_compile_authority"
            and debug_layer == "board_axi_ddr_wrapped_system"
        ):
            action_scope = "verification_capability_repair"
            repair_kind = "exact_board_interface_discovery"
            producer_binding = {
                "repair_tool_role": "board_interface_discovery",
                "repair_gate": "case_board_interface_discovery",
                "requested_producer_scope": producer_scope,
                "requested_capability_id": capability_id,
            }
        elif (
            capability_id
            == "exact_board_vcs_zero_time_toggle_cone_localization"
            and producer_scope == "real_board_vcs_runner_and_failure_analyzer"
            and debug_layer == "board_axi_ddr_wrapped_system"
        ):
            action_scope = "verification_capability_repair"
            repair_kind = capability_id
            producer_binding = {
                "repair_tool_role": "exact_board_vcs_and_failure_analyzer",
                "requested_producer_scope": producer_scope,
                "requested_capability_id": capability_id,
            }
        elif (
            capability_id
            in {
                # The signal/provenance spelling is the current name. Keep
                # the older port/provenance spelling as a compatibility alias
                # for already persisted Agent requests.
                "connected_kernel_current_dag_boundary_port_provenance",
                "connected_kernel_current_dag_boundary_signal_provenance",
            }
            and producer_scope
            in {
                "certified_connected_kernel_hierarchical_port_provenance",
                "certified_connected_kernel_hierarchy_provenance",
            }
            and debug_layer == "board_axi_ddr_wrapped_system"
        ):
            # The Agent needs source-bound internal signal names before it can
            # add a complete read-only board testbench observer. This producer
            # only reads generated sources and current hierarchy evidence.
            action_scope = "verification_capability_repair"
            repair_kind = "connected_kernel_current_dag_boundary_signal_map"
            producer_binding = {
                "repair_tool_role": "connected_kernel_boundary_signal_map",
                "repair_gate": "case_vcs_functional_sim",
                "requested_producer_scope": producer_scope,
                "requested_capability_id": capability_id,
                "capability_alias": (
                    "connected_kernel_current_dag_boundary_signal_provenance"
                    if capability_id
                    == "connected_kernel_current_dag_boundary_signal_provenance"
                    else "connected_kernel_current_dag_boundary_port_provenance"
                ),
                "read_only_source_mapping": True,
            }
        elif (
            capability_id == "connected_kernel_boundary_targeted_replay"
            and producer_scope == "certified_connected_kernel_real_vcs_targeted_replay"
            and debug_layer == "board_axi_ddr_wrapped_system"
        ):
            # Reuse the existing causal replay executor.  This is a read-only
            # lower-scope experiment requested by the Agent, not permission to
            # edit the certified connected kernel.
            action_scope = "causal_slice_repair"
            repair_kind = capability_id
            producer_binding = {
                "repair_tool_role": "connected_kernel_boundary_targeted_replay",
                "repair_gate": "case_vcs_functional_sim",
                "requested_producer_scope": producer_scope,
                "requested_capability_id": capability_id,
                "targeted_replay": True,
            }
        elif (
            capability_id == "cctg_connected_kernel_boundary_replay"
            and producer_scope == "real_vcs_single_layer_boundary_localization"
            and debug_layer == "single_transformer_layer_functional"
        ):
            # This is the lower-layer form of the same read-only CCTG request.
            # Normalize the externally reported layer name to the framework's
            # connected-kernel replay scope; do not infer a root RTL module.
            action_scope = "causal_slice_repair"
            repair_kind = capability_id
            action_debug_layer = "single_transformer_layer_kernel"
            producer_binding = {
                "repair_tool_role": "connected_kernel_boundary_targeted_replay",
                "repair_gate": "case_single_layer_functional",
                "requested_producer_scope": producer_scope,
                "requested_capability_id": capability_id,
                "targeted_replay": True,
                "targeted_replay_plan": {
                    "schema_version": "spatialaccagent.targeted_replay_plan.v0",
                    "status": "needs_boundary_trace",
                    "strategy": "replay_the_declared_connected_kernel_cctg_boundaries",
                    "rerun_env": {
                        "SPATIALACC_BOUNDARY_TRACE": "1",
                        "SPATIALACC_TARGETED_REPLAY": "1",
                    },
                },
            }
        elif (
            capability_id == "connected_kernel_cctg_contradiction_targeted_replay"
            and producer_scope == "certified_connected_kernel_current_layer_replay"
            and debug_layer == "single_transformer_layer_connected_kernel"
        ):
            # A board-level Agent may request the certified connected-kernel
            # CCTG result that resolves a cross-layer contradiction.  Stage 6
            # first reuses an already-completed fresh execution when its raw
            # logs can be safely rematerialized; otherwise the same executor
            # performs exactly one fresh real VCS replay.
            action_scope = "causal_slice_repair"
            repair_kind = capability_id
            action_debug_layer = "single_transformer_layer_kernel"
            producer_binding = {
                "repair_tool_role": "connected_kernel_boundary_targeted_replay",
                "repair_gate": "case_single_layer_functional",
                "requested_producer_scope": producer_scope,
                "requested_capability_id": capability_id,
                "targeted_replay": True,
                "targeted_replay_plan": {
                    "schema_version": "spatialaccagent.targeted_replay_plan.v0",
                    "status": "needs_boundary_trace",
                    "strategy": "replay_or_rematerialize_the_declared_connected_kernel_cctg_boundaries",
                    "rerun_env": {
                        "SPATIALACC_BOUNDARY_TRACE": "1",
                        "SPATIALACC_TARGETED_REPLAY": "1",
                    },
                },
            }
        elif (
            capability_id == "vcs_timescale_error_localization"
            and producer_scope
            in {"real_board_vcs_compile_provenance", "remote_vcs_runner"}
            and debug_layer == "board_axi_ddr_wrapped_system"
        ):
            action_scope = "verification_capability_repair"
            repair_kind = "vcs_timescale_error_localization"
            producer_binding = {
                "repair_tool_role": "exact_board_vcs_compile_provenance",
                "repair_gate": "case_vcs_functional_sim",
                "requested_producer_scope": producer_scope,
                "requested_capability_id": capability_id,
            }
        elif (
            capability_id
            in {
                "vcs_compile_diagnostic_source_provenance",
                # Compatibility for an already persisted Agent request. New
                # prompts use the canonical capability ID below.
                "board_vcs_itsfm_source_provenance",
            }
            and producer_scope
            in {"real_board_vcs_compile_provenance", "remote_vcs_runner"}
            and debug_layer == "board_axi_ddr_wrapped_system"
        ):
            action_scope = "verification_capability_repair"
            # Keep the requested capability generic.  A timescale-specific
            # producer is selected only after a preserved compile log proves
            # the actual Illegal `timescale diagnostic.
            repair_kind = "vcs_compile_diagnostic_source_provenance"
            producer_binding = {
                "repair_tool_role": "exact_board_vcs_compile_provenance",
                "repair_gate": "case_vcs_functional_sim",
                "requested_producer_scope": producer_scope,
                "requested_capability_id": capability_id,
            }
        else:
            return []
        actions.append(
            {
                "scope": action_scope,
                "repair_kind": repair_kind,
                "debug_layer": action_debug_layer,
                "target_modules": target_modules,
                "required_evidence": required_evidence,
                "reason": str(capability["rationale"]),
                "approval_required": False,
                "source": "prior_nonfallback_llm_required_capability",
                "source_feedback_fingerprint_sha256": feedback.get(
                    "input_fingerprint_sha256"
                ),
                **producer_binding,
            }
        )
    return actions


def prior_repair_execution_feedback(
    state: dict[str, Any],
    run_dir: Path,
    *,
    expected_debug_layer: str | None = None,
) -> dict[str, Any] | None:
    """Load only the current SACG-bound Stage-6 report and its exact LLM records."""

    artifact = prior_repair_execution_artifact(state)
    if artifact is None:
        return None
    artifact_error = str(artifact.get("_artifact_error") or "")
    if artifact_error:
        return invalid_prior_repair_execution_feedback([artifact_error])
    if not artifact.get("path"):
        return invalid_prior_repair_execution_feedback(
            ["current SACG repair execution report artifact has no path"]
        )

    report_path = exact_reference_path(artifact["path"], Path.cwd())
    if not report_path.is_file():
        return invalid_prior_repair_execution_feedback(
            [f"current SACG repair execution report is missing: {report_path}"],
            report_path=report_path,
        )
    report_sha256 = sha256_file(report_path)
    declared_report_sha256 = artifact.get("sha256") or artifact.get("file_sha256")
    if declared_report_sha256 and declared_report_sha256 != report_sha256:
        return invalid_prior_repair_execution_feedback(
            ["current SACG repair execution report SHA-256 does not match its artifact binding"],
            report_path=report_path,
            report_sha256=report_sha256,
        )
    try:
        report = read_json(report_path)
    except Exception as exc:
        return invalid_prior_repair_execution_feedback(
            [f"current SACG repair execution report is unreadable: {exc}"],
            report_path=report_path,
            report_sha256=report_sha256,
        )

    report_errors: list[str] = []
    if report.get("stage") != "repair_execution":
        report_errors.append("current SACG repair execution report has the wrong stage")
    if not str(report.get("schema_version") or "").startswith(
        "spatialaccagent.repair_execution_report."
    ):
        report_errors.append("current SACG repair execution report has an unsupported schema")
    step_results = report.get("step_results")
    if not isinstance(step_results, list):
        report_errors.append("current SACG repair execution report step_results is not a list")
        step_results = []
    if not str(report.get("status") or ""):
        report_errors.append("current SACG repair execution report has no status")
    if not isinstance(report.get("errors", []), list) or any(
        not isinstance(value, str) for value in report.get("errors", [])
    ):
        report_errors.append("current SACG repair execution report errors is not a string list")
    if report_errors:
        return invalid_prior_repair_execution_feedback(
            report_errors,
            report_path=report_path,
            report_sha256=report_sha256,
        )

    semantic_records: list[dict[str, Any]] = []
    record_identities: list[dict[str, Any]] = []
    validation_errors: list[str] = []
    aggregate_blockers: list[str] = []
    aggregate_capabilities: list[Any] = []
    summaries: list[str] = []

    def append_unique(rows: list[Any], value: Any) -> None:
        key = json.dumps(value, sort_keys=True, separators=(",", ":"))
        if all(json.dumps(row, sort_keys=True, separators=(",", ":")) != key for row in rows):
            rows.append(copy.deepcopy(value))

    for index, step in enumerate(step_results):
        if not isinstance(step, dict):
            validation_errors.append(f"step_results[{index}] is not an object")
            continue
        result = step.get("result")
        if not isinstance(result, dict):
            validation_errors.append(f"step_results[{index}].result is not an object")
            continue
        step_context = repair_execution_step_context(step)
        record_ref = result.get("llm_record")
        if record_ref is None or record_ref == "":
            continue
        declared_record_sha256 = result.get("llm_record_sha256")
        if isinstance(record_ref, dict):
            declared_record_sha256 = record_ref.get("sha256") or declared_record_sha256
            record_ref = record_ref.get("path")
        if not isinstance(record_ref, str) or not record_ref:
            validation_errors.append(f"step_results[{index}] has an invalid llm_record reference")
            continue
        record_path = exact_reference_path(record_ref, report_path.parent)
        if not record_path.is_file():
            validation_errors.append(
                f"step_results[{index}] referenced LLM record is missing: {record_path}"
            )
            continue
        record_sha256 = sha256_file(record_path)
        if declared_record_sha256 and declared_record_sha256 != record_sha256:
            validation_errors.append(
                f"step_results[{index}] referenced LLM record SHA-256 does not match"
            )
            continue
        try:
            record = read_json(record_path)
        except Exception as exc:
            validation_errors.append(
                f"step_results[{index}] referenced LLM record is unreadable: {exc}"
            )
            continue

        self_path = record.get("result_path")
        if not self_path or exact_reference_path(self_path, record_path.parent) != record_path:
            validation_errors.append(
                f"step_results[{index}] referenced LLM record result_path does not match"
            )
            continue
        if record.get("llm_skipped") is True:
            record_identities.append(
                {
                    "step_id": step.get("step_id"),
                    "path": str(record_path),
                    "sha256": record_sha256,
                    "record_kind": "non_llm",
                }
            )
            continue
        if record.get("mode") != "llm":
            validation_errors.append(
                f"step_results[{index}] referenced record is neither an LLM record nor an explicit skipped review"
            )
            continue
        if record.get("used_fallback") is not False or record.get("error"):
            validation_errors.append(
                f"step_results[{index}] referenced LLM record is fallback or errored"
            )
            continue
        output = record.get("output")
        if not isinstance(output, dict):
            validation_errors.append(
                f"step_results[{index}] referenced LLM record output is not an object"
            )
            continue
        if not str(output.get("status") or ""):
            validation_errors.append(
                f"step_results[{index}] referenced LLM record output has no status"
            )
            continue
        if output.get("agent") and output.get("agent") != record.get("agent"):
            validation_errors.append(
                f"step_results[{index}] referenced LLM record output agent does not match"
            )
            continue
        if output.get("stage") and output.get("stage") != record.get("stage"):
            validation_errors.append(
                f"step_results[{index}] referenced LLM record output stage does not match"
            )
            continue

        raw_text = record.get("repair_raw_text") or record.get("raw_text")
        try:
            raw_output = json.loads(raw_text) if isinstance(raw_text, str) else None
        except json.JSONDecodeError:
            raw_output = None
        if raw_output != output:
            validation_errors.append(
                f"step_results[{index}] referenced LLM record output differs from raw LLM JSON"
            )
            continue

        if record.get("compact_retry_request_path"):
            prompt_path_value = record.get("compact_retry_request_path")
            input_fingerprint = record.get("compact_retry_prompt_hash")
        else:
            prompt_path_value = record.get("request_path")
            input_fingerprint = record.get("prompt_hash")
        if not prompt_path_value or not is_sha256(input_fingerprint):
            validation_errors.append(
                f"step_results[{index}] referenced LLM record has no valid input fingerprint"
            )
            continue
        prompt_path = exact_reference_path(prompt_path_value, record_path.parent)
        if not prompt_path.is_file() or sha256_file(prompt_path) != input_fingerprint:
            validation_errors.append(
                f"step_results[{index}] referenced LLM input does not match its fingerprint"
            )
            continue

        record_context = repair_execution_agent_context(record)
        if record_context and step_context and not contexts_match(
            record_context,
            step_context,
        ):
            validation_errors.append(
                f"step_results[{index}] repair execution contexts disagree"
            )
            continue
        effective_context = record_context or step_context

        output_blockers: list[str] = []
        for field in ("blocked_reasons", "blockers"):
            values = output.get(field, [])
            if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
                validation_errors.append(
                    f"step_results[{index}] LLM output {field} is not a string list"
                )
                continue
            for value in values:
                if value and value not in output_blockers:
                    output_blockers.append(value)
                    if value not in aggregate_blockers:
                        aggregate_blockers.append(value)
        required_capabilities = output.get("required_capabilities", [])
        if not isinstance(required_capabilities, list) or any(
            not isinstance(value, dict) for value in required_capabilities
        ):
            validation_errors.append(
                f"step_results[{index}] LLM output required_capabilities is not an object list"
            )
            continue
        for capability in required_capabilities:
            append_unique(aggregate_capabilities, capability)
        deterministic_feedback = validated_repair_feedback_artifacts(
            result,
            report_path=report_path,
            expected_context=effective_context,
            validation_errors=validation_errors,
            step_index=index,
        )
        for observation in deterministic_feedback:
            for field in ("blockers", "validation_errors"):
                for value in observation.get(field, []):
                    if value and value not in output_blockers:
                        output_blockers.append(value)
                    if value and value not in aggregate_blockers:
                        aggregate_blockers.append(value)
        summary = str(output.get("summary") or "")
        if summary:
            summaries.append(summary)
        record_feedback = {
            "step_id": step.get("step_id"),
            "scope": step.get("scope"),
            "agent": record.get("agent"),
            "stage": record.get("stage"),
            "status": output.get("status"),
            "summary": summary,
            "blockers": output_blockers,
            "required_capabilities": copy.deepcopy(required_capabilities),
            "path": str(record_path),
            "sha256": record_sha256,
            "input_fingerprint_sha256": input_fingerprint,
            "repair_execution_context": effective_context,
            "deterministic_feedback": deterministic_feedback,
        }
        semantic_records.append(record_feedback)
        record_identities.append(
            {
                "step_id": step.get("step_id"),
                "path": str(record_path),
                "sha256": record_sha256,
                "input_fingerprint_sha256": input_fingerprint,
            }
        )

    if validation_errors:
        return invalid_prior_repair_execution_feedback(
            validation_errors,
            report_path=report_path,
            report_sha256=report_sha256,
        )

    output_statuses = [str(row.get("status") or "") for row in semantic_records]
    feedback_status = (
        output_statuses[0]
        if output_statuses and len(set(output_statuses)) == 1
        else str(report.get("status") or "unknown")
    )
    execution_errors = [str(value) for value in report.get("errors", []) if str(value)]
    identity = {
        "report": {"path": str(report_path), "sha256": report_sha256},
        "llm_records": record_identities,
        "deterministic_feedback": [
            {
                "kind": observation.get("kind"),
                "path": observation.get("path"),
                "sha256": observation.get("sha256"),
                "repair_execution_context": observation.get(
                    "repair_execution_context"
                ),
            }
            for record in semantic_records
            for observation in record.get("deterministic_feedback", [])
            if isinstance(observation, dict)
        ],
    }
    feedback = {
        "schema_version": "spatialaccagent.prior_repair_execution_feedback.v1",
        "status": feedback_status,
        "summary": "; ".join(summaries) or str(report.get("summary") or ""),
        "blockers": aggregate_blockers,
        "required_capabilities": aggregate_capabilities,
        "repair_execution_status": report.get("status"),
        "execution_errors": execution_errors,
        "report": {
            "path": str(report_path),
            "sha256": report_sha256,
            "schema_version": report.get("schema_version"),
        },
        "llm_records": semantic_records,
        "deterministic_feedback": [
            copy.deepcopy(observation)
            for record in semantic_records
            for observation in record.get("deterministic_feedback", [])
            if isinstance(observation, dict)
        ],
        "input_fingerprint_sha256": canonical_sha256(identity),
        "validation": {"status": "pass", "errors": []},
    }
    return scope_prior_repair_execution_feedback(
        feedback,
        expected_debug_layer,
    )


def _hash_bound_json_reference(
    reference: Any,
    *,
    expected_schema: str,
) -> tuple[dict[str, Any] | None, str | None]:
    """Load one status-bearing evidence artifact through its declared hash."""

    if not isinstance(reference, dict):
        return None, "artifact reference is not an object"
    path = Path(str(reference.get("path") or "")).expanduser()
    expected_sha256 = str(reference.get("sha256") or "")
    if not path.is_file() or not is_sha256(expected_sha256):
        return None, "artifact reference has no readable hash-bound path"
    if sha256_file(path) != expected_sha256:
        return None, "artifact reference SHA-256 does not match"
    try:
        artifact = read_json(path)
    except Exception as exc:
        return None, f"artifact reference is unreadable: {exc}"
    if artifact.get("schema_version") != expected_schema:
        return None, "artifact reference has an unexpected schema"
    if artifact.get("status") != "pass":
        return None, "artifact reference is not passing"
    return artifact, None


def rematerialized_lower_layer_capability_evidence(run_dir: Path) -> list[dict[str, Any]]:
    """Project current passing lower-layer evidence into the next board plan.

    A completed direct replay can be reclassified after an evidence-decoder fix.
    Its original Stage-6 report remains historically failed, so planner inputs
    must validate the refreshed package itself instead of trusting that stale
    aggregate status. This is read-only and accepts only hash-bound evidence.
    """

    package_paths = sorted(
        (run_dir / "repair_execution").glob(
            "*_current_layer_causal_repair_context_package.json"
        ),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    evidence: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for package_path in package_paths:
        package = read_json(package_path)
        if (
            package.get("schema_version")
            != "spatialaccagent.current_layer_causal_repair_context_package.v0"
            or package.get("status") != "pass"
            or str(package.get("capability_id") or "")
            not in {
                "cctg_connected_kernel_boundary_replay",
                "connected_kernel_cctg_contradiction_targeted_replay",
            }
        ):
            continue
        package_run_dir = Path(str(package.get("run_dir") or "")).expanduser()
        if not package_run_dir.is_absolute():
            package_run_dir = (package_path.parent / package_run_dir).resolve()
        if package_run_dir != run_dir.resolve():
            continue
        cctg = (
            package.get("cctg_boundary_replay_evidence", {})
            if isinstance(package.get("cctg_boundary_replay_evidence"), dict)
            else {}
        )
        if not (
            cctg.get("schema_version") == "spatialaccagent.cctg_boundary_replay.v1"
            and cctg.get("status") == "pass"
            and cctg.get("fresh_remote_vcs_execution_observed") is True
            and cctg.get("boundary_liveness_status") == "pass"
        ):
            continue

        direct_rows: dict[str, dict[str, Any]] = {}
        direct_errors: list[str] = []
        for name, schema in (
            (
                "connected_kernel_cctg_targeted_replay_trace",
                "spatialaccagent.connected_kernel_cctg_targeted_replay_trace.v1",
            ),
            (
                "connected_kernel_targeted_replay_causal_context",
                "spatialaccagent.connected_kernel_targeted_replay_causal_context.v1",
            ),
            (
                "connected_kernel_cctg_contradiction_reconciliation",
                "spatialaccagent.connected_kernel_cctg_contradiction_reconciliation.v1",
            ),
        ):
            artifact, error = _hash_bound_json_reference(
                package.get(name), expected_schema=schema
            )
            if error:
                direct_errors.append(f"{name}: {error}")
            elif artifact is not None:
                direct_rows[name] = artifact
        if direct_errors:
            continue

        trace = direct_rows["connected_kernel_cctg_targeted_replay_trace"]
        lifecycle = trace.get("lifecycle", {}) if isinstance(trace.get("lifecycle"), dict) else {}
        if not (
            lifecycle.get("ingress_complete") is True
            and lifecycle.get("egress_complete") is True
            and lifecycle.get("terminal_egress_last") is True
        ):
            continue
        package_sha256 = sha256_file(package_path)
        identity = (str(package_path.resolve()), package_sha256)
        if identity in seen:
            continue
        seen.add(identity)
        evidence.append(
            {
                "schema_version": "spatialaccagent.rematerialized_lower_layer_capability_evidence.v1",
                "status": "pass",
                "capability_id": package.get("capability_id"),
                "source_debug_layer": package.get("debug_layer"),
                "source_verification_scope": (
                    package.get("current_layer_replay", {}).get("debug_layer")
                    if isinstance(package.get("current_layer_replay"), dict)
                    else "single_layer_closure"
                ),
                "context_package": {
                    "path": str(package_path.resolve()),
                    "sha256": package_sha256,
                },
                "cctg_boundary_replay": {
                    "status": cctg.get("status"),
                    "fresh_remote_vcs_execution_observed": cctg.get(
                        "fresh_remote_vcs_execution_observed"
                    ),
                    "boundary_liveness_status": cctg.get(
                        "boundary_liveness_status"
                    ),
                    "accepted_trace_record_count": cctg.get(
                        "accepted_trace_record_count"
                    ),
                },
                "direct_lifecycle": {
                    "start_witness": trace.get("start_witness"),
                    "expected_ingress_beats": trace.get("expected_ingress_beats"),
                    "ingress_complete": lifecycle.get("ingress_complete"),
                    "egress_accepted_count": lifecycle.get("egress_accepted_count"),
                    "egress_complete": lifecycle.get("egress_complete"),
                    "terminal_egress_last": lifecycle.get("terminal_egress_last"),
                },
                "planning_policy": (
                    "This completed lower-layer experiment is closed evidence. Do not request or "
                    "rerun the same connected-kernel replay unless a new current trace explicitly "
                    "contradicts a named certified invariant; choose only the next causally distinct "
                    "board AXI/DDR action."
                ),
            }
        )
    return evidence


def failure_class(checker: str) -> str:
    if "shape" in checker:
        return "shape_model"
    if "template" in checker:
        return "template_coverage"
    if "stream" in checker:
        return "stream_order"
    if "beat" in checker:
        return "beat_count"
    if "case" in checker or "verification" in checker:
        return "runtime_harness"
    if "tool" in checker:
        return "runtime_harness"
    if "backend" in checker:
        return "backend_repair"
    return "framework_consistency"


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


def tool_protocols_for_state(state: dict[str, Any]) -> dict[str, Any]:
    try:
        data = read_json(artifact_path(state, "artifact.input.tool_protocols"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def human_boundary_for_state(state: dict[str, Any]) -> dict[str, Any]:
    try:
        data = read_json(artifact_path(state, "artifact.input.human_agent_boundary"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def case_tool_aliases(case_adapter: dict[str, Any]) -> dict[str, str]:
    aliases: dict[str, str] = {}
    tools = case_adapter.get("tools", {}) if isinstance(case_adapter.get("tools"), dict) else {}
    for role, spec in tools.items():
        if not isinstance(spec, dict):
            continue
        name = str(spec.get("name") or "")
        if not name:
            continue
        aliases[str(role)] = name
        aliases[name] = name
        legacy = spec.get("legacy_name")
        if legacy:
            aliases[str(legacy)] = name
    return aliases


def adapter_specs_by_name(case_adapter: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    tools = case_adapter.get("tools", {}) if isinstance(case_adapter.get("tools"), dict) else {}
    for role, spec in tools.items():
        if not isinstance(spec, dict):
            continue
        name = str(spec.get("name") or "")
        if name:
            result[name] = spec
            result[str(role)] = spec
        legacy = spec.get("legacy_name")
        if legacy:
            result[str(legacy)] = spec
    return result


def normalize_case_tool_name(tool_name: Any, case_adapter: dict[str, Any]) -> str:
    aliases = case_tool_aliases(case_adapter)
    value = str(tool_name or "").strip()
    return aliases.get(value, value)


def tool_by_name(tool_protocols: dict[str, Any], case_adapter: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    aliases = case_tool_aliases(case_adapter)
    for tool in tool_protocols.get("tools", []):
        if not isinstance(tool, dict):
            continue
        name = str(tool.get("name") or "")
        if not name:
            continue
        result[name] = tool
        result[aliases.get(name, name)] = tool
        legacy = tool.get("legacy_name")
        if legacy:
            result[str(legacy)] = tool
            result[aliases.get(str(legacy), str(legacy))] = tool
    return result


def file_status(path_value: Any) -> dict[str, Any]:
    path = Path(str(path_value))
    repo_path = path if path.is_absolute() else Path.cwd() / path
    return {
        "path": str(path),
        "exists": repo_path.exists(),
        "is_repo_relative": not path.is_absolute(),
    }


def tool_capabilities(spec: dict[str, Any] | None) -> set[str]:
    if not isinstance(spec, dict):
        return set()
    value = spec.get("capabilities", [])
    if isinstance(value, dict):
        return {str(k) for k, enabled in value.items() if enabled}
    if isinstance(value, list):
        return {str(item) for item in value}
    return set()


def tool_produces(spec: dict[str, Any] | None) -> list[str]:
    if not isinstance(spec, dict):
        return []
    produces = spec.get("produces", [])
    return [str(item) for item in produces] if isinstance(produces, list) else []


def resolve_run_path(run_dir: Path, value: Any) -> Path:
    path = Path(str(value))
    if path.is_absolute():
        return path
    repo_path = Path.cwd() / path
    if repo_path.exists():
        return repo_path
    return run_dir / path


def json_report_candidates_for_tool(
    run_dir: Path,
    row: dict[str, Any],
    case_adapter: dict[str, Any],
) -> list[Path]:
    checker = str(row.get("checker") or "")
    tool_name = checker.removeprefix("real_tool.")
    adapter_specs = adapter_specs_by_name(case_adapter)
    candidates: list[Path] = []
    for value in [row.get("tool_report_path")]:
        if value:
            candidates.append(resolve_run_path(run_dir, value))
    stdout = str(row.get("stdout_tail") or "")
    for line in stdout.splitlines():
        text = line.strip()
        if text.endswith(".json"):
            candidates.append(resolve_run_path(run_dir, text))
    log_path = row.get("log_path")
    if log_path:
        try:
            log = read_json(resolve_run_path(run_dir, log_path))
            if log.get("tool_report_path"):
                candidates.append(resolve_run_path(run_dir, log.get("tool_report_path")))
            for line in str(log.get("stdout_tail") or "").splitlines():
                text = line.strip()
                if text.endswith(".json"):
                    candidates.append(resolve_run_path(run_dir, text))
        except Exception:
            pass
    spec = adapter_specs.get(tool_name)
    for value in tool_produces(spec):
        path = resolve_run_path(run_dir, value)
        if path.suffix.lower() == ".json":
            candidates.append(path)
    seen: set[str] = set()
    result: list[Path] = []
    for path in candidates:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        result.append(path)
    return result


def enrich_verification_with_tool_reports(
    verification: dict[str, Any],
    run_dir: Path,
    case_adapter: dict[str, Any],
) -> dict[str, Any]:
    enriched = copy.deepcopy(verification)
    rows = enriched.get("results", []) if isinstance(enriched.get("results"), list) else []
    for row in rows:
        if not isinstance(row, dict) or not str(row.get("checker") or "").startswith("real_tool."):
            continue
        produced_reports = list(row.get("produced_reports", [])) if isinstance(row.get("produced_reports"), list) else []
        for path in json_report_candidates_for_tool(run_dir, row, case_adapter):
            if not path.exists():
                continue
            try:
                data = read_json(path)
            except Exception:
                continue
            report = {
                "path": str(path),
                "schema_version": data.get("schema_version"),
                "status": data.get("status"),
                "summary": data.get("summary"),
                "blockers": data.get("blockers", []) if isinstance(data.get("blockers"), list) else [],
            }
            if not any(item.get("path") == report["path"] for item in produced_reports if isinstance(item, dict)):
                produced_reports.append(report)
            if not row.get("tool_report_path"):
                row["tool_report_path"] = str(path)
            if not row.get("tool_report_status"):
                row["tool_report_status"] = data.get("status")
            if data.get("summary") and not row.get("tool_report_summary"):
                row["tool_report_summary"] = data.get("summary")
            blockers = data.get("blockers", []) if isinstance(data.get("blockers"), list) else []
            if blockers and not row.get("tool_report_blockers"):
                row["tool_report_blockers"] = blockers
            if blockers and "blockers=" not in str(row.get("summary") or ""):
                row["summary"] = f"{row.get('summary', '')} report_status={data.get('status')} blockers={'; '.join(str(item) for item in blockers[:4])}".strip()
        if produced_reports:
            row["produced_reports"] = produced_reports
    return enriched


def tool_supports_boundary_trace(*specs: dict[str, Any] | None) -> bool:
    trace_caps = {"boundary_trace", "boundary_trace_rerun", "contract_boundary_trace"}
    for spec in specs:
        caps = tool_capabilities(spec)
        if caps.intersection(trace_caps):
            return True
        if any("boundary_trace" in item or "failure_localization" in item for item in tool_produces(spec)):
            return True
    return False


def tool_capability_summary(*specs: dict[str, Any] | None) -> dict[str, Any]:
    capabilities: set[str] = set()
    produces: list[str] = []
    for spec in specs:
        capabilities.update(tool_capabilities(spec))
        produces.extend(tool_produces(spec))
    return {
        "capabilities": sorted(capabilities),
        "produces": sorted(set(produces)),
        "supports_boundary_trace": tool_supports_boundary_trace(*specs),
    }


def boundary_trace_scope_error(debug_layer: Any, capability_summary: dict[str, Any]) -> str | None:
    layer = str(debug_layer or "")
    capabilities = set(str(item) for item in capability_summary.get("capabilities", []))
    board_only = bool(
        capabilities.intersection(
            {
                "all_target_layers",
                "board_wrapper_functional_sim",
                "exact_sample_board_wrapper_simulation",
            }
        )
    )
    if layer == "operator_leaf_modules" and board_only:
        return "operator-leaf trace rerun cannot use an all-layer board-wrapper simulator"
    if layer == "single_transformer_layer_kernel" and board_only:
        return "single-layer trace rerun cannot use an all-layer board-wrapper simulator"
    return None


def is_targetless_read_only_lifecycle_reconciliation(
    action: dict[str, Any],
) -> bool:
    """Recognize the one supported board capability with no module target.

    This action only reconciles existing hash-bound lifecycle records. It never
    edits a source file or launches a simulator, so a hardware module target
    would be artificial. All other verification capability repairs still need
    an explicit target module.
    """

    return bool(
        action.get("repair_kind")
        == "repair.reconcile_exact_board_lifecycle_cctg_observation_contract"
        and action.get("debug_layer") == "board_axi_ddr_wrapped_system"
        and action.get("requested_producer_scope") == "causal_repair_context_pack"
        and action.get("read_only_evidence_reconciliation") is True
        and action.get("approval_required") is False
        and not action.get("target_modules")
    )


def build_repair_workflow(
    actions: list[dict[str, Any]],
    state: dict[str, Any],
    run_dir: Path,
    case_adapter: dict[str, Any],
) -> dict[str, Any]:
    tool_protocols = tool_protocols_for_state(state)
    human_boundary = human_boundary_for_state(state)
    tools = tool_by_name(tool_protocols, case_adapter)
    adapter_specs = adapter_specs_by_name(case_adapter)
    auto_allowed = set(str(item) for item in human_boundary.get("auto_allowed", []))
    approval_required = set(str(item) for item in human_boundary.get("approval_required", []))
    workflow_steps: list[dict[str, Any]] = []
    blockers: list[str] = []
    approvals: list[str] = []
    for index, action in enumerate(actions):
        scope = str(action.get("scope") or "")
        step: dict[str, Any] = {
            "id": f"repair_step.{index:02d}",
            "scope": scope,
            "source": action.get("source"),
            "approval_required": bool(action.get("approval_required", False)),
            "status": "pending",
            "action": action,
        }
        if scope == "regression_rerun":
            normalized_tool = normalize_case_tool_name(action.get("tool"), case_adapter)
            tool = tools.get(normalized_tool)
            adapter_spec = adapter_specs.get(normalized_tool)
            step["tool"] = normalized_tool
            adapter_argv = (
                [str(item) for item in adapter_spec.get("argv", [])]
                if isinstance(adapter_spec, dict)
                else []
            )
            use_current_exact_board_runner = (
                normalized_tool == "case_vcs_functional_sim"
                and any(
                    Path(item).name == "case_board_vcs_functional.py"
                    for item in adapter_argv
                )
            )
            if use_current_exact_board_runner:
                script = Path(
                    adapter_argv[1]
                    if adapter_argv and adapter_argv[0] == "python3" and len(adapter_argv) > 1
                    else adapter_argv[0]
                )
                step["resolved_protocol_name"] = adapter_spec.get("name")
                step["execution"] = {
                    "argv": adapter_argv,
                    "cwd": str(Path.cwd()),
                    "env": dict(adapter_spec.get("env") or {}),
                    "source": "current_exact_board_case_adapter",
                }
                argv = adapter_argv
                script_exists = script.exists()
            elif isinstance(tool, dict):
                step["resolved_protocol_name"] = tool.get("name")
                step["execution"] = tool.get("execution")
                argv = tool.get("execution", {}).get("argv")
                script_exists = bool(tool.get("script_exists"))
            elif isinstance(adapter_spec, dict):
                argv = [str(item) for item in adapter_spec.get("argv", [])]
                script = Path(argv[1] if argv and argv[0] == "python3" and len(argv) > 1 else argv[0]) if argv else Path("")
                script_exists = script.exists()
                step["resolved_protocol_name"] = adapter_spec.get("name")
                step["execution"] = {"argv": argv, "cwd": str(Path.cwd()), "env": {}, "source": "case_adapter_fallback"}
            else:
                argv = []
                script_exists = False
                step["resolved_protocol_name"] = None
                step["execution"] = None
            if argv and script_exists:
                step["status"] = "ready_to_execute"
            else:
                step["status"] = "blocked"
                blockers.append(f"{step['id']} tool {normalized_tool} is not configured with an existing executable")
        elif scope == "debug_trace_rerun":
            normalized_tool = normalize_case_tool_name(action.get("tool"), case_adapter)
            tool = tools.get(normalized_tool)
            adapter_spec = adapter_specs.get(normalized_tool)
            step["tool"] = normalized_tool
            step["boundary_trace_required"] = True
            step["debug_layer"] = action.get("debug_layer")
            step["failed_current_layer_gates"] = action.get("failed_current_layer_gates", [])
            step["lower_layer_pass_evidence"] = action.get("lower_layer_pass_evidence", [])
            step["repair_context"] = action.get("minimal_repair_context", {})
            if isinstance(tool, dict):
                step["resolved_protocol_name"] = tool.get("name")
                execution = dict(tool.get("execution") or {})
                env = dict(execution.get("env") or {})
                env["SPATIALACC_BOUNDARY_TRACE"] = "1"
                env["SPATIALACC_TARGETED_REPLAY"] = "1"
                if action.get("debug_layer"):
                    env["SPATIALACC_DEBUG_LAYER"] = str(action.get("debug_layer"))
                execution["env"] = env
                step["execution"] = execution
                argv = tool.get("execution", {}).get("argv")
                script_exists = bool(tool.get("script_exists"))
            elif isinstance(adapter_spec, dict):
                argv = [str(item) for item in adapter_spec.get("argv", [])]
                script = Path(argv[1] if argv and argv[0] == "python3" and len(argv) > 1 else argv[0]) if argv else Path("")
                script_exists = script.exists()
                env = dict(adapter_spec.get("env") or {})
                env["SPATIALACC_BOUNDARY_TRACE"] = "1"
                env["SPATIALACC_TARGETED_REPLAY"] = "1"
                if action.get("debug_layer"):
                    env["SPATIALACC_DEBUG_LAYER"] = str(action.get("debug_layer"))
                step["resolved_protocol_name"] = adapter_spec.get("name")
                step["execution"] = {"argv": argv, "cwd": str(Path.cwd()), "env": env, "source": "case_adapter_fallback"}
            else:
                argv = []
                script_exists = False
                step["resolved_protocol_name"] = None
                step["execution"] = None
            capability_summary = tool_capability_summary(tool, adapter_spec)
            step["tool_capability"] = capability_summary
            scope_error = boundary_trace_scope_error(action.get("debug_layer"), capability_summary)
            if scope_error:
                step["status"] = "blocked"
                step["tool_scope_mismatch"] = {
                    "reason": scope_error,
                    "debug_layer": action.get("debug_layer"),
                    "resolved_protocol_name": step.get("resolved_protocol_name"),
                }
                blockers.append(f"{step['id']} {scope_error}")
            elif not capability_summary["supports_boundary_trace"]:
                step["status"] = "blocked"
                step["tool_capability_gap"] = {
                    "required_capability": "boundary_trace",
                    "reason": (
                        "debug_trace_rerun requires a tool that can generate boundary trace or "
                        "failure-localization evidence for the current debug layer"
                    ),
                    "policy": "backtrack_to_stage6_tool_contract_before_retrying_stage6_or_patching_rtl",
                }
                blockers.append(f"{step['id']} tool {normalized_tool} lacks boundary_trace capability")
            elif argv and script_exists:
                step["status"] = "ready_to_execute"
            else:
                step["status"] = "blocked"
                blockers.append(f"{step['id']} boundary-trace tool {normalized_tool} is not configured with an existing executable")
        elif scope == "code_repair":
            target_files = [file_status(path) for path in action.get("target_files", [])]
            step["target_files"] = target_files
            missing = [item["path"] for item in target_files if not item["exists"]]
            if missing:
                step["status"] = "blocked"
                blockers.append(f"{step['id']} target files missing: {missing}")
            elif step["approval_required"]:
                step["status"] = "approval_required"
                approvals.append(step["id"])
            elif str(action.get("risk") or "") in auto_allowed or "testbench" in " ".join(item["path"] for item in target_files):
                step["status"] = "ready_for_agent_patch"
            elif str(action.get("risk") or "") in approval_required:
                step["status"] = "approval_required"
                approvals.append(step["id"])
            else:
                step["status"] = "ready_for_agent_patch"
        elif scope == "causal_slice_repair":
            context = action.get("minimal_repair_context", {}) if isinstance(action.get("minimal_repair_context"), dict) else {}
            if action.get("root_candidate_module") or context.get("root_candidate_module"):
                step["status"] = "ready_for_agent_patch"
                step["repair_context"] = context
                step["targeted_replay_plan"] = action.get("targeted_replay_plan", {})
            elif action.get("targeted_replay") is True:
                # An explicitly supported capability can request a read-only
                # causal replay before any root module is known.  The replay,
                # not this workflow constructor, determines the first failing
                # boundary; no source-edit authority is granted here.
                step["status"] = "ready_to_execute"
                step["repair_context"] = context
                step["target_modules"] = action.get("target_modules", [])
                step["debug_layer"] = action.get("debug_layer")
                step["targeted_replay_plan"] = action.get("targeted_replay_plan", {})
            else:
                step["status"] = "blocked"
                blockers.append(f"{step['id']} causal slice repair has no root candidate module")
        elif scope == "verification_capability_repair":
            targetless_read_only_lifecycle_reconciliation = (
                is_targetless_read_only_lifecycle_reconciliation(action)
            )
            if action.get("repair_kind") and (
                action.get("target_modules")
                or targetless_read_only_lifecycle_reconciliation
            ):
                step["status"] = "ready_for_agent_patch"
                step["repair_context"] = action.get("minimal_repair_context", {})
                step["target_modules"] = action.get("target_modules", [])
                step["debug_layer"] = action.get("debug_layer")
            else:
                step["status"] = "blocked"
                blockers.append(f"{step['id']} verification capability repair lacks repair_kind or target_modules")
        elif scope == "targeted_lower_layer_backtrack":
            challenge = action.get("lower_layer_evidence_challenge", {}) if isinstance(action.get("lower_layer_evidence_challenge"), dict) else {}
            challenged: list[str] = []
            if isinstance(challenge.get("challenged_gates"), list):
                challenged.extend(str(item) for item in challenge.get("challenged_gates", []) if str(item))
            if isinstance(challenge.get("challenged_modules"), list):
                challenged.extend(str(item) for item in challenge.get("challenged_modules", []) if str(item))
            step["debug_layer"] = action.get("debug_layer")
            step["lower_layer_evidence_challenge"] = challenge
            step["lower_layer_pass_evidence"] = action.get("lower_layer_pass_evidence", [])
            step["repair_context"] = action.get("minimal_repair_context", {})
            if challenged and challenge.get("status") == "challenge_present":
                step["status"] = "ready_for_agent_patch"
            else:
                step["status"] = "blocked"
                blockers.append(f"{step['id']} targeted lower-layer backtrack lacks bound challenge evidence")
        elif scope == "agent_runtime_repair":
            step["status"] = "blocked"
            blockers.append(
                f"{step['id']} agent runtime/LLM configuration is invalid; set a supported LLM model/provider and rerun the same repair loop"
            )
        elif scope == "stage6_gate_dag_repair":
            step["status"] = "ready_for_agent_patch"
            step["debug_layer"] = action.get("debug_layer")
            step["out_of_order_executed_higher_layer_gates"] = action.get("out_of_order_executed_higher_layer_gates", [])
        else:
            step["status"] = "blocked"
            blockers.append(f"{step['id']} unsupported repair scope: {scope}")
        workflow_steps.append(step)
    return {
        "schema_version": "spatialaccagent.repair_workflow.v0",
        "status": "blocked" if blockers else ("approval_required" if approvals else "ready"),
        "run_dir": str(run_dir),
        "case_adapter": {
            "case_id": case_adapter.get("case_id"),
            "model_family": case_adapter.get("model_family"),
            "status": case_adapter.get("status"),
        },
        "steps": workflow_steps,
        "blockers": blockers,
        "approval_steps": approvals,
        "policy": {
            "do_not_apply_unbounded_code_changes": True,
            "do_not_rerun_smoke_as_acceptance": True,
            "regression_reruns_must_use_case_tool_protocols": True,
            "repair_output_must_return_to_stage6": True,
            "same_debug_layer_must_rerun_until_functionally_correct_before_promotion": True,
            "cctg_boundary_trace_or_localization_required_before_code_repair": True,
            "lower_layer_pass_evidence_is_reusable_not_absolute": True,
            "targeted_lower_layer_backtrack_requires_contradicting_current_layer_trace": True,
            "do_not_reopen_passed_lower_layer_without_contradicting_current_layer_trace": True,
        },
    }


def resolve_run_artifact_path(path: Path, run_dir: Path) -> Path | None:
    candidates = [path] if path.is_absolute() else [path, run_dir / path]
    return next((candidate for candidate in candidates if candidate.exists()), None)


def load_vcs_diagnosis(state: dict[str, Any], run_dir: Path) -> dict[str, Any] | None:
    case_adapter = case_adapter_for_state(state, run_dir)
    diagnosis = case_adapter.get("diagnosis", {}) if isinstance(case_adapter.get("diagnosis"), dict) else {}
    candidates = [
        Path(str(diagnosis.get("path"))) if diagnosis.get("path") else run_dir / "verification" / "case_diagnostics" / "vcs_functional_diagnosis.json",
    ]
    if diagnosis.get("legacy_path"):
        candidates.append(Path(str(diagnosis.get("legacy_path"))))
    path = next(
        (
            resolved
            for candidate in candidates
            for resolved in [resolve_run_artifact_path(candidate, run_dir)]
            if resolved is not None
        ),
        None,
    )
    if path is None:
        return None
    try:
        data = read_json(path)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def load_debug_closure_localization(state: dict[str, Any], run_dir: Path) -> dict[str, Any] | None:
    candidates = [
        run_dir / "verification" / "debug_closure" / "failure_localization.json",
    ]
    try:
        verification = read_json(artifact_path(state, "artifact.stage6.verification_result"))
        debug_paths = verification.get("debug_closure", {}) if isinstance(verification.get("debug_closure"), dict) else {}
        if debug_paths.get("failure_localization"):
            candidates.insert(0, Path(str(debug_paths["failure_localization"])))
    except Exception:
        pass
    for candidate in candidates:
        path = resolve_run_artifact_path(candidate, run_dir)
        if path is None:
            continue
        try:
            data = read_json(path)
            return data if isinstance(data, dict) else None
        except Exception:
            continue
    return None


def exact_board_diagnosis_repair_kind(
    diagnosis: dict[str, Any] | None,
) -> str | None:
    """Route structured board-VCS evidence without guessing from log text."""

    if not isinstance(diagnosis, dict):
        return None
    status = str(diagnosis.get("status") or "").lower()
    failure_class = str(
        diagnosis.get("failure_class")
        or diagnosis.get("root_cause_class")
        or ""
    ).lower()
    handoff = (
        diagnosis.get("repair_handoff", {})
        if isinstance(diagnosis.get("repair_handoff"), dict)
        else {}
    )
    failure_evidence = (
        diagnosis.get("failure_evidence", {})
        if isinstance(diagnosis.get("failure_evidence"), dict)
        else {}
    )
    repair_scope = str(
        handoff.get("repair_scope")
        or failure_evidence.get("repair_scope")
        or ""
    ).lower()
    debug_layer = str(handoff.get("debug_layer") or "").lower()
    if status in {"", "pass", "ready"} and failure_class in {
        "",
        "none",
        "no_failure",
    }:
        return None
    if repair_scope == "execution_environment_retry" or failure_class == "vcs_execution_environment_failure":
        return "exact_board_environment_retry"
    if repair_scope == "remote_transport_retry" or failure_class in {
        "remote_transport_failure",
        "remote_recovery_indeterminate",
        "remote_tool_poll_budget_exhausted",
    }:
        return "remote_tool_transport_contract"
    if repair_scope == "simulation_environment" or failure_class in {
        "tool_resolution_failure",
        "vcs_library_resolution_failure",
    }:
        return "tool_runtime_environment_contract"
    lower_layer_contradiction = board_to_lower_layer_contradiction_from_diagnosis(
        diagnosis,
        target_debug_layer="single_transformer_layer_kernel",
    )
    # A current hash-bound board trace is stronger than a repair handoff that
    # may have been written before the trace was collected.
    if lower_layer_contradiction.get("status") == "proven":
        return "single_layer_spatial_pipeline_backtrack"
    if handoff.get("agent_should_apply_code_changes") is True:
        return "exact_board_integration_harness"
    return None


def diagnosis_target_layer(diagnosis: dict[str, Any]) -> str:
    handoff = (
        diagnosis.get("repair_handoff", {})
        if isinstance(diagnosis.get("repair_handoff"), dict)
        else {}
    )
    binding = (
        diagnosis.get("applicability_binding", {})
        if isinstance(diagnosis.get("applicability_binding"), dict)
        else {}
    )
    board_origin = binding.get("origin_layer") == "board_axi_ddr_wrapped_system"
    lower_layer_contradiction = (
        board_to_lower_layer_contradiction_from_diagnosis(
            diagnosis,
            target_debug_layer="single_transformer_layer_kernel",
        )
        if board_origin
        else {}
    )
    if lower_layer_contradiction.get("status") == "proven":
        return "single_transformer_layer_kernel"
    for value in (handoff.get("debug_layer"), handoff.get("repair_scope")):
        layer = str(value or "")
        if (
            board_origin
            and layer == "single_transformer_layer_kernel"
            and lower_layer_contradiction.get("status") != "proven"
        ):
            continue
        if layer in HIERARCHICAL_DEBUG_LAYERS:
            return layer
    return ""


def failed_gate_names_for_diagnosis(repair_loop: dict[str, Any] | None) -> set[str]:
    rows = (
        (repair_loop or {}).get("failed_current_layer_gates", [])
        if isinstance((repair_loop or {}).get("failed_current_layer_gates"), list)
        else []
    )
    return {
        str(row.get("name"))
        for row in rows
        if isinstance(row, dict)
        and row.get("name")
        and row.get("status") == "fail"
    }


def diagnosis_applicability_report(
    diagnosis: dict[str, Any] | None,
    repair_loop: dict[str, Any] | None,
    *,
    run_dir: Path | None = None,
) -> dict[str, Any]:
    current_layer = (
        (repair_loop or {}).get("current_layer", {})
        if isinstance((repair_loop or {}).get("current_layer"), dict)
        else {}
    )
    current_layer_id = str(current_layer.get("id") or "")
    failed_gate_names = failed_gate_names_for_diagnosis(repair_loop)
    base = {
        "schema_version": "spatialaccagent.diagnosis_applicability_report.v1",
        "current_layer": current_layer_id or None,
        "current_failed_gates": sorted(failed_gate_names),
    }
    if not isinstance(diagnosis, dict):
        return base | {
            "status": "not_present",
            "executable": False,
            "reason": "no VCS diagnosis artifact is available",
        }

    diagnosis_status = str(diagnosis.get("status") or "").lower()
    root_cause = str(
        diagnosis.get("failure_class")
        or diagnosis.get("root_cause_class")
        or ""
    ).lower()
    if diagnosis_status in {"", "pass", "ready"} and root_cause in {
        "",
        "none",
        "no_failure",
    }:
        return base | {
            "status": "not_actionable",
            "executable": False,
            "reason": "diagnosis does not describe a current failure",
        }

    handoff = (
        diagnosis.get("repair_handoff", {})
        if isinstance(diagnosis.get("repair_handoff"), dict)
        else {}
    )
    target_layer = diagnosis_target_layer(diagnosis)
    binding = (
        diagnosis.get("applicability_binding", {})
        if isinstance(diagnosis.get("applicability_binding"), dict)
        else {}
    )
    diagnosis_schema = str(diagnosis.get("schema_version") or "")
    lower_layer_contradiction = board_to_lower_layer_contradiction_from_diagnosis(
        diagnosis,
        target_debug_layer="single_transformer_layer_kernel",
        expected_lower_layer_certificate_path=(
            run_dir.resolve()
            / "verification"
            / "certificates"
            / "single_layer_promotion_certificate.json"
            if run_dir is not None
            else None
        ),
    )
    proven_lower_layer_backtrack = (
        lower_layer_contradiction.get("status") == "proven"
        and current_layer_id == "board_axi_ddr_wrapped_system"
    )

    # Unversioned in-memory diagnoses remain usable by callers that construct a
    # current diagnosis directly. Persisted diagnosis artifacts must be source-bound.
    if not binding:
        if diagnosis_schema:
            return base | {
                "status": "historical_only",
                "executable": False,
                "target_layer": target_layer or None,
                "reason": "persisted diagnosis lacks a source-bound applicability binding",
                "validation_errors": [
                    "applicability_binding is required for executable reuse"
                ],
            }
        rerun_gates = {
            str(value)
            for value in handoff.get("must_rerun", [])
            if str(value)
        }
        layer_matches = target_layer == current_layer_id
        board_origin_matches = current_layer_id == "board_axi_ddr_wrapped_system"
        gate_matches = not rerun_gates or bool(rerun_gates & failed_gate_names)
        executable = bool(
            current_layer_id
            and failed_gate_names
            and gate_matches
            and (layer_matches or board_origin_matches)
        )
        return base | {
            "status": "applicable" if executable else "historical_only",
            "executable": executable,
            "target_layer": target_layer or None,
            "relation": "legacy_unversioned_current_call" if executable else None,
            "reason": (
                "unversioned caller-provided diagnosis matches the current layer and failed gate"
                if executable
                else "unversioned diagnosis does not match the current layer and failed gate"
            ),
        }

    errors: list[str] = []
    if binding.get("schema_version") != DIAGNOSIS_APPLICABILITY_BINDING_SCHEMA_VERSION:
        errors.append("unsupported diagnosis applicability binding schema")
    origin_layer = str(binding.get("origin_layer") or "")
    bound_target_layer = str(binding.get("target_layer") or "")
    if origin_layer not in HIERARCHICAL_DEBUG_LAYERS:
        errors.append("origin_layer is missing or unsupported")
    if bound_target_layer not in HIERARCHICAL_DEBUG_LAYERS:
        errors.append("target_layer is missing or unsupported")
    if target_layer and bound_target_layer != target_layer and not proven_lower_layer_backtrack:
        errors.append("binding target_layer does not match repair handoff")
    bound_failure_class = str(binding.get("diagnosed_failure_class") or "").lower()
    if not bound_failure_class or bound_failure_class != root_cause:
        errors.append("binding diagnosed_failure_class does not match diagnosis")

    origin_gates = {
        str(value)
        for value in binding.get("origin_gates", [])
        if str(value)
    }
    applicable_rerun_gates = {
        str(value)
        for value in binding.get("applicable_rerun_gates", [])
        if str(value)
    }
    if not origin_gates:
        errors.append("origin_gates is empty")
    if not applicable_rerun_gates:
        errors.append("applicable_rerun_gates is empty")

    source_artifacts = binding.get("source_artifacts", [])
    if not isinstance(source_artifacts, list) or not source_artifacts:
        errors.append("source_artifacts is empty")
        source_artifacts = []
    elif run_dir is None:
        errors.append("run_dir is required to validate diagnosis source artifacts")
    else:
        for index, artifact in enumerate(source_artifacts):
            if not isinstance(artifact, dict):
                errors.append(f"source_artifacts[{index}] is not an object")
                continue
            declared_sha256 = str(artifact.get("sha256") or "")
            raw_path = artifact.get("path")
            path = (
                resolve_run_artifact_path(Path(str(raw_path)), run_dir)
                if raw_path
                else None
            )
            if path is None or not path.is_file():
                errors.append(f"source_artifacts[{index}] is missing")
            elif not is_sha256(declared_sha256):
                errors.append(f"source_artifacts[{index}] sha256 is invalid")
            elif sha256_file(path) != declared_sha256:
                errors.append(f"source_artifacts[{index}] live sha256 changed")

    board_functional_aggregate_relation = (
        current_layer_id == "board_axi_ddr_wrapped_system"
        and origin_layer == "board_axi_ddr_wrapped_system"
        and bound_target_layer == "board_axi_ddr_wrapped_system"
        and "case_vcs_functional_sim" in origin_gates
        and "functional_sim" in failed_gate_names
    )
    origin_relation = (
        current_layer_id == origin_layer
        and bool(origin_gates & failed_gate_names)
    ) or board_functional_aggregate_relation
    target_relation = (
        current_layer_id == bound_target_layer
        and bool(applicable_rerun_gates & failed_gate_names)
    ) or board_functional_aggregate_relation
    if proven_lower_layer_backtrack:
        # The board layer remains the evidence source, while the current
        # hash-bound contradiction explicitly reopens the connected kernel.
        target_relation = True
    if not origin_relation and not target_relation:
        errors.append("diagnosis layer/gate binding does not match the current failed gate")
    executable = not errors
    return base | {
        "status": "applicable" if executable else "historical_only",
        "executable": executable,
        "origin_layer": origin_layer or None,
        "target_layer": (
            target_layer
            if proven_lower_layer_backtrack
            else bound_target_layer or target_layer or None
        ),
        "origin_gates": sorted(origin_gates),
        "applicable_rerun_gates": sorted(applicable_rerun_gates),
        "relation": (
            "current_targeted_backtrack"
            if proven_lower_layer_backtrack
            else
            "current_board_functional_aggregate"
            if board_functional_aggregate_relation
            else "current_origin_failure"
            if origin_relation
            else "current_targeted_backtrack"
            if target_relation
            else None
        ),
        "reason": (
            "diagnosis is bound to the current source artifact, hierarchy layer, and failed gate"
            if executable
            else "diagnosis remains read-only history because its evidence binding is not current"
        ),
        "validation_errors": errors,
    }


def diagnosis_prompt_projection(
    diagnosis: dict[str, Any] | None,
    applicability: dict[str, Any],
) -> dict[str, Any] | None:
    """Keep non-applicable diagnoses as audit metadata, not LLM repair evidence."""

    if not isinstance(diagnosis, dict):
        return None
    if applicability.get("executable") is True:
        return diagnosis
    return {
        "schema_version": "spatialaccagent.repair_diagnosis_prompt_projection.v1",
        "status": "historical_only",
        "source_schema_version": diagnosis.get("schema_version"),
        "applicability": {
            key: applicability.get(key)
            for key in (
                "schema_version",
                "status",
                "executable",
                "current_layer",
                "current_failed_gates",
                "target_layer",
                "relation",
                "reason",
                "validation_errors",
            )
        },
        "policy": (
            "The raw diagnosis is durable project history but is omitted from the "
            "repair-agent prompt because it is not bound to the current hierarchy "
            "layer, failed gate, and live source artifacts."
        ),
    }


def build_repair_actions(
    failures: list[dict[str, Any]],
    diagnosis: dict[str, Any] | None,
    case_adapter: dict[str, Any],
    debug_localization: dict[str, Any] | None = None,
    repair_loop: dict[str, Any] | None = None,
    run_dir: Path | None = None,
    diagnosis_applicability: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    diagnosis_applicability = diagnosis_applicability or diagnosis_applicability_report(
        diagnosis,
        repair_loop,
        run_dir=run_dir,
    )
    # A pre-launch environment failure is executable only as a same-source
    # tool retry.  It never grants source-repair authority, so it remains safe
    # even when the normal source-diagnosis applicability binding is stale.
    environment_retry = (
        exact_board_diagnosis_repair_kind(diagnosis)
        == "exact_board_environment_retry"
    )
    if diagnosis_applicability.get("executable") is not True and not environment_retry:
        diagnosis = None
    failure_kind = str((repair_loop or {}).get("failure_kind") or "")
    current_layer = (repair_loop or {}).get("current_layer", {}) if isinstance((repair_loop or {}).get("current_layer"), dict) else {}
    out_of_order = (repair_loop or {}).get("out_of_order_executed_higher_layer_gates", [])
    failed_current_layer_gates = (
        (repair_loop or {}).get("failed_current_layer_gates", [])
        if isinstance((repair_loop or {}).get("failed_current_layer_gates"), list)
        else []
    )
    lower_layer_pass_evidence = (
        (repair_loop or {}).get("lower_layer_pass_evidence", [])
        if isinstance((repair_loop or {}).get("lower_layer_pass_evidence"), list)
        else []
    )
    lower_layer_challenge = (
        (repair_loop or {}).get("lower_layer_evidence_challenge", {})
        if isinstance((repair_loop or {}).get("lower_layer_evidence_challenge"), dict)
        else {}
    )
    board_diagnosis_kind = (
        exact_board_diagnosis_repair_kind(diagnosis)
        if current_layer.get("id") == "board_axi_ddr_wrapped_system"
        else None
    )
    if board_diagnosis_kind:
        current_board_contradiction = board_to_lower_layer_contradiction_from_diagnosis(
            diagnosis,
            target_debug_layer="single_transformer_layer_kernel",
            expected_lower_layer_certificate_path=(
                run_dir.resolve()
                / "verification"
                / "certificates"
                / "single_layer_promotion_certificate.json"
                if run_dir is not None
                else None
            ),
        )
        failed_gate_names = [
            str(item.get("name"))
            for item in failed_current_layer_gates
            if isinstance(item, dict) and item.get("name") and item.get("status") == "fail"
        ]
        lower_layer_backtrack = (
            board_diagnosis_kind == "single_layer_spatial_pipeline_backtrack"
        )
        completed_lower_layer_recheck = (
            completed_board_lower_layer_recheck(
                run_dir,
                current_board_contradiction,
            )
            if lower_layer_backtrack
            else {"status": "not_applicable"}
        )
        if completed_lower_layer_recheck.get("status") == "pass":
            # The current board evidence already triggered and consumed one
            # matching lower-layer recheck. Continue at the exact board layer
            # unless one of the three source hashes changes.
            lower_layer_backtrack = False
            # A completed matching lower-layer recheck does not make the
            # current board failure a board-shell problem.  If the current
            # diagnosis is an internal pipeline stop, route the next Agent
            # turn to the compiled kernel RTL closure.  The executor performs
            # the full evidence and source-closure check before granting that
            # write authority.
            if str(
                (diagnosis or {}).get("failure_class")
                or (diagnosis or {}).get("root_cause_class")
                or ""
            ).lower() in {
                "intra_layer_spatial_pipeline_violation",
                "board_output_lifecycle_frontier_violation",
            }:
                board_diagnosis_kind = "board_semantic_rtl_repair"
            else:
                board_diagnosis_kind = "exact_board_integration_harness"
        target_modules = (
            [
                "connected_single_transformer_layer_kernel",
                "single_layer_pipeline_overlap_contract",
            ]
            if lower_layer_backtrack
            else failed_gate_names or ["board_axi_ddr_wrapped_system"]
        )
        failure_class_name = str(
            (diagnosis or {}).get("failure_class")
            or (diagnosis or {}).get("root_cause_class")
            or "unknown_board_vcs_failure"
        )
        environment_retry = board_diagnosis_kind == "exact_board_environment_retry"
        actions.append(
            {
                "scope": "regression_rerun" if environment_retry else "verification_capability_repair",
                "repair_kind": (
                    "case_single_layer_functional"
                    if lower_layer_backtrack
                    else board_diagnosis_kind
                ),
                "tool": "case_vcs_functional_sim" if environment_retry else None,
                "debug_layer": (
                    "single_transformer_layer_kernel"
                    if lower_layer_backtrack
                    else "board_axi_ddr_wrapped_system"
                ),
                "repair_gate": (
                    "case_single_layer_functional"
                    if lower_layer_backtrack
                    else failed_gate_names[0] if failed_gate_names else None
                ),
                "failed_current_layer_gates": failed_current_layer_gates,
                "root_candidate_module": None,
                "target_modules": target_modules,
                "violated_contract": (
                    "all_spatial_operators_must_form_a_token_level_pipeline"
                    if lower_layer_backtrack
                    else "exact_board_real_vcs_and_analyzer_must_pass"
                ),
                "failure_signature": {
                    "failure_class": failure_class_name,
                    "repair_scope": (
                        (diagnosis or {}).get("repair_handoff", {}).get("repair_scope")
                        if isinstance((diagnosis or {}).get("repair_handoff"), dict)
                        else None
                    ),
                    "summary": (diagnosis or {}).get("summary"),
                    "current_board_to_lower_layer_contradiction": (
                        copy.deepcopy(current_board_contradiction)
                        if lower_layer_backtrack
                        else None
                    ),
                    "completed_board_lower_layer_recheck": (
                        copy.deepcopy(completed_lower_layer_recheck)
                        if completed_lower_layer_recheck.get("status") == "pass"
                        else None
                    ),
                },
                "minimal_repair_context": {
                    "failed_current_layer_gates": failed_current_layer_gates,
                    "vcs_diagnosis_status": (diagnosis or {}).get("status"),
                    "vcs_failure_class": failure_class_name,
                    "current_board_to_lower_layer_contradiction": (
                        copy.deepcopy(current_board_contradiction)
                        if lower_layer_backtrack
                        else None
                    ),
                    "completed_board_lower_layer_recheck": (
                        copy.deepcopy(completed_lower_layer_recheck)
                        if completed_lower_layer_recheck.get("status") == "pass"
                        else None
                    ),
                },
                "reason": (
                    "the current exact-board trace contradicts the prior single-layer pipeline certificate; rerun and repair the connected single-layer kernel before returning to Stage 3"
                    if lower_layer_backtrack
                    else
                    "the matching single-layer recheck passed and the current exact-board trace is an internal pipeline stop; let the Agent repair only the dynamically derived compiled RTL closure"
                    if board_diagnosis_kind == "board_semantic_rtl_repair"
                    else
                    "the current exact-board trace already consumed its matching single-layer recheck; continue with the exact-wrapper causal replay"
                    if completed_lower_layer_recheck.get("status") == "pass"
                    else
                    "the current exact-board VCS/analyzer evidence authorizes a bounded repair of the existing "
                    "agent-created board integration sources"
                    if board_diagnosis_kind == "exact_board_integration_harness"
                    else "the current exact-board VCS/analyzer evidence proves a pre-launch environment failure; "
                    "retry the same real-tool chain after framework recovery without changing RTL"
                ),
                "approval_required": False,
                "source": "case_vcs_functional_diagnosis",
            }
        )
        return actions
    if out_of_order:
        actions.append(
            {
                "scope": "stage6_gate_dag_repair",
                "repair_kind": "hierarchical_dependency_backtrack",
                "debug_layer": current_layer.get("id"),
                "out_of_order_executed_higher_layer_gates": out_of_order,
                "reason": "higher-layer verification gates executed before the current debug layer passed; repair Stage6 gate dependencies before promotion",
                "approval_required": False,
                "source": "hierarchical_repair_loop",
            }
        )
    if debug_localization:
        status = str(debug_localization.get("status") or "")
        if failure_kind in {"verification_capability_gap", "verification_tool_transport_failure"}:
            failed_gate_names = [
                str(item.get("name"))
                for item in failed_current_layer_gates
                if isinstance(item, dict) and item.get("name") and item.get("status") == "fail"
            ]
            target_modules = list(failed_gate_names)
            if not target_modules and current_layer.get("id"):
                target_modules = [str(current_layer["id"])]
            failure_text = " ".join(str(item.get("summary") or "") for item in failures).lower()
            runtime_environment_gap = any(
                token in failure_text
                for token in ("python environment", "required python", "no module named", "module not found")
            )
            remote_transport_gap = failure_kind == "verification_tool_transport_failure"
            semantic_binding_gap = any(
                token in failure_text
                for token in (
                    "semantic testbench",
                    "weight-binding manifest",
                    "real-weight binding manifest",
                    "atol/rtol/max_mismatch_fraction",
                    "real-weight semantic evidence",
                )
            )
            board_integration_gap = (
                current_layer.get("id") == "board_axi_ddr_wrapped_system"
                and bool(
                    {
                        "case_multilayer_pipeline",
                        "case_multilayer_functional",
                        "case_axi_ddr_interface",
                    }
                    & set(failed_gate_names)
                )
            )
            if (
                current_layer.get("id") == "board_axi_ddr_wrapped_system"
                and exact_board_identity_contract_passed(run_dir)
                and not board_integration_gap
            ):
                # Discovery is complete, so any remaining board-layer
                # not-run/functional gates belong to the integration harness
                # and must advance to the real board VCS chain.
                board_integration_gap = any(
                    isinstance(item, dict)
                    and str(item.get("name") or "") != "case_board_interface_discovery"
                    and str(item.get("status") or "") in {"fail", "not_run"}
                    for item in failed_current_layer_gates
                )
            board_discovery_gap = (
                current_layer.get("id") == "board_axi_ddr_wrapped_system"
                and "case_board_interface_discovery" in set(failed_gate_names)
                and not exact_board_identity_contract_passed(run_dir)
            )
            repair_kind = (
                "remote_tool_transport_contract"
                if remote_transport_gap
                else ("tool_runtime_environment_contract"
                if runtime_environment_gap
                else (
                    "exact_board_interface_discovery"
                    if board_discovery_gap
                    else "exact_board_integration_harness"
                    if board_integration_gap
                    else ("semantic_loader_harness_binding" if semantic_binding_gap else "independent_golden_reference")
                )
                )
            )
            actions.append(
                {
                    "scope": "verification_capability_repair",
                    "repair_kind": repair_kind,
                    "debug_layer": current_layer.get("id") or "operator_leaf_modules",
                    "repair_gate": failed_gate_names[0] if failed_gate_names else None,
                    "failed_current_layer_gates": failed_current_layer_gates,
                    "root_candidate_module": None,
                    "target_modules": target_modules,
                    "violated_contract": "current_verification_capability_must_execute_before_hardware_repair",
                    "failure_signature": {"failed_gates": failed_gate_names, "summaries": [str(item.get("summary") or "") for item in failures[:8]]},
                    "minimal_repair_context": {"failed_current_layer_gates": failed_current_layer_gates},
                    "reason": (
                        "remote simulator transport failed before a hardware verdict; recover or rerun the same remote job before any DUT action"
                        if remote_transport_gap
                        else (
                        "current tool runtime does not satisfy the declared Python environment contract; repair tool execution before any hardware action"
                        if runtime_environment_gap
                        else (
                        "current layer lacks a valid semantic loader/harness, immutable numeric comparison contract, or executed weight-consumption evidence"
                        if semantic_binding_gap
                        else (
                            "current board layer lacks a complete LLM-interpreted, Vivado-fact-validated exact sample-project interface contract; rerun the board discovery agent without editing DUT or sample sources"
                            if board_discovery_gap
                            else "current board layer lacks a model-derived multi-layer scheduler and exact sample compute-slot integration; generate and bind the board integration harness before functional simulation"
                            if board_integration_gap
                            else "current layer lacks independent golden/checker capability; implement or bind the independent golden reference before hardware promotion"
                        )
                        )
                        )
                    ),
                    "approval_required": False,
                    "source": "hierarchical_repair_loop",
                }
            )
        elif status == "localized" and failure_kind == "agent_runtime_llm_configuration":
            actions.append(
                {
                    "scope": "agent_runtime_repair",
                    "repair_kind": "llm_provider_configuration",
                    "debug_layer": current_layer.get("id"),
                    "reason": "LLM provider/model configuration failed; agentic repair decisions cannot be promoted without a valid LLM run",
                    "approval_required": False,
                    "source": "hierarchical_repair_loop",
                }
            )
        elif (
            status == "localized"
            and failure_kind == "hardware_value_mismatch"
            and current_layer.get("id") == "operator_leaf_modules"
        ):
            context = (
                debug_localization.get("minimal_repair_context", {})
                if isinstance(debug_localization.get("minimal_repair_context"), dict)
                else {}
            )
            trace_record = context.get("trace_record", {}) if isinstance(context.get("trace_record"), dict) else {}
            root_candidate = str(
                trace_record.get("module") or debug_localization.get("root_candidate_module") or ""
            ).strip()
            numeric_failure = next(
                (
                    row
                    for row in debug_localization.get("failed_boundaries", [])
                    if isinstance(row, dict)
                    and row.get("status") == "fail"
                    and row.get("evidence_type") == "semantic_numeric_compare"
                    and row.get("stage_id") == trace_record.get("stage_id")
                    and row.get("failure_class")
                ),
                None,
            )
            localized_trace_ready = trace_record.get("evidence_type") == "semantic_numeric_compare" or (
                trace_record.get("evidence_type") == "semantic_internal_boundary_trace"
                and trace_record.get("failure_class") == "unknown_logic_value"
                and numeric_failure is not None
            )
            if localized_trace_ready and root_candidate:
                actions.append(
                    {
                        "scope": "verification_capability_repair",
                        "repair_kind": "localized_semantic_dut_repair",
                        "debug_layer": current_layer.get("id"),
                        "repair_gate": "case_leaf_golden_compare",
                        "failed_current_layer_gates": failed_current_layer_gates,
                        "root_candidate_module": root_candidate,
                        "target_modules": [root_candidate],
                        "violated_contract": debug_localization.get("violated_contract"),
                        "failure_signature": debug_localization.get("failure_signature"),
                        "targeted_replay_plan": debug_localization.get("targeted_replay_plan", {}),
                        "minimal_repair_context": context,
                        "corroborating_semantic_numeric_failure": numeric_failure,
                        "reason": (
                            "current real-tool leaf output has a localized target-model semantic failure; "
                            "run an agent-owned bounded DUT/harness repair and rerun the same golden gate"
                        ),
                        "approval_required": False,
                        "source": "contract_guided_debug_closure",
                    }
                )
            else:
                actions.append(
                    {
                        "scope": "causal_slice_repair",
                        "debug_layer": current_layer.get("id"),
                        "root_candidate_module": debug_localization.get("root_candidate_module"),
                        "violated_contract": debug_localization.get("violated_contract"),
                        "failure_signature": debug_localization.get("failure_signature"),
                        "targeted_replay_plan": debug_localization.get("targeted_replay_plan", {}),
                        "minimal_repair_context": context,
                        "reason": "numeric failure lacks a complete semantic trace record; keep repair local to the causal slice",
                        "approval_required": False,
                        "source": "contract_guided_debug_closure",
                    }
                )
        elif status == "localized" and lower_layer_challenge.get("status") == "challenge_present":
            actions.append(
                {
                    "scope": "targeted_lower_layer_backtrack",
                    "repair_kind": "contradicted_lower_layer_evidence",
                    "debug_layer": current_layer.get("id"),
                    "failure_kind": failure_kind,
                    "lower_layer_evidence_challenge": lower_layer_challenge,
                    "lower_layer_pass_evidence": lower_layer_pass_evidence,
                    "failed_current_layer_gates": failed_current_layer_gates,
                    "minimal_repair_context": debug_localization.get("minimal_repair_context", {}),
                    "reason": (
                        "current-layer CCTG/boundary trace contradicts lower-layer pass evidence; "
                        "reopen only the challenged lower-layer gate/module, then rerun the current layer"
                    ),
                    "approval_required": False,
                    "source": "hierarchical_repair_loop",
                }
            )
        elif status == "localized" and lower_layer_challenge.get("status") == "insufficient_challenge_evidence":
            actions.append(
                {
                    "scope": "debug_trace_rerun",
                    "tool": debug_localization.get("recommended_trace_gate") or "case_vcs_functional_sim",
                    "debug_layer": current_layer.get("id"),
                    "failure_kind": failure_kind,
                    "failed_current_layer_gates": failed_current_layer_gates,
                    "lower_layer_pass_evidence": lower_layer_pass_evidence,
                    "minimal_repair_context": debug_localization.get("minimal_repair_context", {}),
                    "reason": (
                        "trace asserts a lower-layer contradiction but does not bind the challenged "
                        "gate/module; rerun current-layer boundary trace to make the backtrack target explicit"
                    ),
                    "approval_required": False,
                    "source": "contract_guided_debug_closure",
                }
            )
        elif status == "localized":
            actions.append(
                {
                    "scope": "causal_slice_repair",
                    "debug_layer": current_layer.get("id"),
                    "root_candidate_module": debug_localization.get("root_candidate_module"),
                    "violated_contract": debug_localization.get("violated_contract"),
                    "failure_signature": debug_localization.get("failure_signature"),
                    "targeted_replay_plan": debug_localization.get("targeted_replay_plan", {}),
                    "minimal_repair_context": debug_localization.get("minimal_repair_context", {}),
                    "reason": "contract-guided debug closure localized an upstream root-cause candidate",
                    "approval_required": False,
                    "source": "contract_guided_debug_closure",
                }
            )
        elif status == "needs_boundary_trace":
            recommended_tool = (
                debug_localization.get("recommended_trace_gate")
                or next(
                    (
                        item.get("name")
                        for item in failed_current_layer_gates
                        if isinstance(item, dict)
                        and item.get("status") == "fail"
                        and ("functional" in str(item.get("name")) or str(item.get("name")) == "single_transformer_layer")
                    ),
                    None,
                )
                or "case_vcs_functional_sim"
            )
            context = debug_localization.get("minimal_repair_context", {}) if isinstance(debug_localization.get("minimal_repair_context"), dict) else {}
            actions.append(
                {
                    "scope": "debug_trace_rerun",
                    "tool": recommended_tool,
                    "debug_layer": current_layer.get("id"),
                    "failure_kind": failure_kind,
                    "failed_current_layer_gates": failed_current_layer_gates,
                    "lower_layer_pass_evidence": lower_layer_pass_evidence,
                    "minimal_repair_context": context,
                    "reason": (
                        "current debug layer lacks boundary trace; rerun the failed current-layer gate "
                        "with boundary-contract tracing enabled before reopening lower layers that already passed"
                    ),
                    "approval_required": False,
                    "source": "contract_guided_debug_closure",
                }
            )
    if diagnosis:
        diagnosis_status = str(diagnosis.get("status") or "").lower()
        root_cause = str(diagnosis.get("root_cause_class") or "").strip().lower()
        actionable_diagnosis = diagnosis_status not in {"", "pass", "ready"} or root_cause not in {"", "none", "no_failure"}
    else:
        actionable_diagnosis = False
    if diagnosis and actionable_diagnosis:
        handoff = diagnosis.get("repair_handoff", {}) if isinstance(diagnosis.get("repair_handoff"), dict) else {}
        for pattern in handoff.get("repair_patterns", []):
            if not isinstance(pattern, dict):
                continue
            actions.append(
                {
                    "scope": "code_repair",
                    "pattern_id": pattern.get("pattern_id"),
                    "target_files": pattern.get("target_files", []),
                    "reason": pattern.get("summary"),
                    "approval_required": bool(pattern.get("approval_required", False)),
                    "risk": pattern.get("risk"),
                    "source": "case_vcs_functional_diagnosis",
                }
            )
        current_failed_gate_names = failed_gate_names_for_diagnosis(repair_loop)
        for rerun in handoff.get("must_rerun", []):
            tool_name = normalize_case_tool_name(rerun, case_adapter)
            if tool_name not in current_failed_gate_names:
                continue
            actions.append(
                {
                    "scope": "regression_rerun",
                    "tool": tool_name,
                    "reason": "rerun required after applying VCS diagnosis repair pattern",
                    "approval_required": False,
                    "source": "case_vcs_functional_diagnosis",
                }
            )
    if failures and not actions:
        actions.append(
            {
                "scope": "regression_rerun",
                "reason": "framework static checker failed; rerun after inspecting failed constraint",
                "approval_required": False,
            }
        )
    return actions


def build_repair_plan(
    state: dict[str, Any],
    run_dir: Path,
    flow_controller_handoff: dict[str, Any] | None = None,
) -> dict[str, Any]:
    verification = read_json(artifact_path(state, "artifact.stage6.verification_result"))
    case_adapter = case_adapter_for_state(state, run_dir)
    verification = enrich_verification_with_tool_reports(verification, run_dir, case_adapter)
    failures = [item for item in verification.get("results", []) if item.get("status") == "fail"]
    pending = [item for item in verification.get("results", []) if item.get("status") == "not_run"]
    diagnosis = load_vcs_diagnosis(state, run_dir)
    debug_localization = load_debug_closure_localization(state, run_dir)
    repair_loop = build_repair_loop_report(
        verification_result=verification,
        debug_localization=debug_localization or {},
    )
    current_layer = (
        repair_loop.get("current_layer", {})
        if isinstance(repair_loop.get("current_layer"), dict)
        else {}
    )
    prior_execution_feedback = prior_repair_execution_feedback(
        state,
        run_dir,
        expected_debug_layer=str(current_layer.get("id") or "") or None,
    )
    completed_lower_layer_capabilities = (
        rematerialized_lower_layer_capability_evidence(run_dir)
    )
    diagnosis_applicability = diagnosis_applicability_report(
        diagnosis,
        repair_loop,
        run_dir=run_dir,
    )
    classified = [
        item | {
            "failure_class": failure_class(str(item.get("checker", ""))),
            "repair_hint": "inspect violated constraint and rerun the related checker",
        }
        for item in failures
    ]
    # A completed generic provenance producer may leave the prior LLM request
    # in the persistent feedback record.  If the current structured diagnosis
    # proves VCS never launched because of environment housekeeping, retrying
    # the exact same tool chain is the only admissible next action; replaying
    # the already-completed producer would create an LLM loop.
    environment_retry_active = (
        exact_board_diagnosis_repair_kind(diagnosis) == "exact_board_environment_retry"
    )
    repair_actions = (
        []
        if environment_retry_active
        else required_capability_repair_actions(prior_execution_feedback)
    )
    # A capability-refresh request can outlive its producer.  Once the current
    # exact-board identity is checker-valid, do not replay the obsolete
    # discovery action; rebuild actions from the live verification evidence so
    # the next step is the actual board integration/VCS repair.
    if exact_board_identity_contract_passed(run_dir):
        repair_actions = [
            action
            for action in repair_actions
            if str(action.get("repair_kind") or "")
            != "exact_board_interface_discovery"
        ]
    if completed_lower_layer_capabilities:
        repair_actions = [
            action
            for action in repair_actions
            if str(action.get("repair_kind") or "")
            not in {
                "cctg_connected_kernel_boundary_replay",
                "connected_kernel_cctg_contradiction_targeted_replay",
            }
        ]
    if not repair_actions:
        repair_actions = build_repair_actions(
            classified,
            diagnosis,
            case_adapter,
            debug_localization,
            repair_loop,
            run_dir,
            diagnosis_applicability,
        )
    repair_workflow = build_repair_workflow(repair_actions, state, run_dir, case_adapter)
    repair_routing_priority = authoritative_repair_routing_priority(
        {"repair_actions": repair_actions}
    )
    diagnostics = {
        "case_vcs_functional": diagnosis_prompt_projection(
            diagnosis,
            diagnosis_applicability,
        ),
        "case_vcs_functional_applicability": diagnosis_applicability,
        "contract_guided_debug_closure": debug_localization,
        "hierarchical_repair_loop": repair_loop,
    }
    if prior_execution_feedback is not None:
        diagnostics["prior_repair_execution_feedback"] = prior_execution_feedback
    if completed_lower_layer_capabilities:
        diagnostics["completed_lower_layer_capabilities"] = (
            completed_lower_layer_capabilities
        )
    if flow_controller_handoff is not None:
        handoff_errors = validate_stage6_flow_handoff(flow_controller_handoff, run_dir)
        if handoff_errors:
            raise ValueError(
                "invalid Stage-6 flow-controller handoff: " + "; ".join(handoff_errors)
            )
        diagnostics["flow_controller_handoff"] = copy.deepcopy(flow_controller_handoff)
    return {
        "schema_version": "spatialaccagent.repair_plan.v0",
        "stage": "repair",
        "status": "ready" if not failures else "needs_repair",
        "verification_status": verification.get("status"),
        "case_adapter": {
            "case_id": case_adapter.get("case_id"),
            "model_family": case_adapter.get("model_family"),
            "status": case_adapter.get("status"),
            "source": case_adapter.get("source"),
        },
        "failures": classified,
        "pending_evidence": pending,
        "diagnostics": diagnostics,
        "repair_actions": repair_actions,
        "repair_workflow": repair_workflow,
        "repair_routing_priority": repair_routing_priority,
        "note": "Failing checkers are classified; not_run real tools are evidence gaps, not automatic repair failures.",
    }


def validation_llm_team_mode() -> str:
    value = os.environ.get("SPATIALACC_VALIDATION_LLM_TEAM_MODE", "conditional").strip().lower()
    return value if value in {"conditional", "full"} else "conditional"


def repair_specialist_trigger(repair_plan: dict[str, Any]) -> str | None:
    if validation_llm_team_mode() == "full":
        return "full_team_requested"
    diagnostics = repair_plan.get("diagnostics", {}) if isinstance(repair_plan.get("diagnostics"), dict) else {}
    loop = diagnostics.get("hierarchical_repair_loop", {}) if isinstance(diagnostics.get("hierarchical_repair_loop"), dict) else {}
    kind = str(loop.get("failure_kind") or "")
    challenge = loop.get("lower_layer_evidence_challenge", {}) if isinstance(loop.get("lower_layer_evidence_challenge"), dict) else {}
    if challenge.get("status") in {"challenge_present", "insufficient_challenge_evidence"}:
        return f"lower_layer_evidence_{challenge.get('status')}"
    localized_semantic_action = any(
        isinstance(action, dict)
        and action.get("repair_kind") == "localized_semantic_dut_repair"
        and action.get("scope") == "verification_capability_repair"
        for action in repair_plan.get("repair_actions", [])
    )
    single_layer_pipeline_backtrack = any(
        isinstance(action, dict)
        and action.get("repair_kind") == "case_single_layer_functional"
        and action.get("scope") == "verification_capability_repair"
        and action.get("debug_layer") == "single_transformer_layer_kernel"
        for action in repair_plan.get("repair_actions", [])
    )
    if single_layer_pipeline_backtrack:
        return None
    if kind == "hardware_value_mismatch" and localized_semantic_action:
        return None
    if kind in {
        "unclassified_debug_failure",
        "lower_layer_evidence_contradicted",
        "integration_boundary_or_layer_interconnect",
        "board_wrapper_or_pipeline_integration",
        "hardware_value_mismatch",
        "hardware_liveness_or_handshake",
        "board_interface_or_runtime",
    }:
        return kind
    return None


def authoritative_repair_routing_priority(
    repair_plan: dict[str, Any],
) -> dict[str, Any]:
    """Return the current trace proof that must control repair routing.

    A board run may carry older static or audit-only failures in the same
    plan.  Those records remain useful for later promotion checks, but a
    current hash-bound contradiction is stronger evidence for deciding which
    repair worker runs next.  Keep this projection generic: it validates the
    target named by the current action instead of hardcoding a model, board,
    module, or boundary name.
    """

    actions = [
        action
        for action in repair_plan.get("repair_actions", [])
        if isinstance(action, dict)
    ]
    if len(actions) != 1:
        return {
            "schema_version": "spatialaccagent.repair_routing_priority.v1",
            "status": "not_applicable",
            "reason": "repair plan does not contain one bounded repair action",
        }
    action = actions[0]
    context = (
        action.get("minimal_repair_context", {})
        if isinstance(action.get("minimal_repair_context"), dict)
        else {}
    )
    contradiction = context.get("current_board_to_lower_layer_contradiction")
    if not isinstance(contradiction, dict) or contradiction.get("status") != "proven":
        return {
            "schema_version": "spatialaccagent.repair_routing_priority.v1",
            "status": "not_applicable",
            "reason": "no proven current board-to-lower-layer contradiction",
        }
    evidence = contradiction.get("evidence", {})
    evidence = evidence if isinstance(evidence, dict) else {}
    source_binding = evidence.get("source_binding", {})
    source_binding = source_binding if isinstance(source_binding, dict) else {}
    direct = evidence.get("direct_kernel_boundary_observations", {})
    direct = direct if isinstance(direct, dict) else {}
    causal = evidence.get("causal_localization", {})
    causal = causal if isinstance(causal, dict) else {}
    target_layer = str(contradiction.get("target_debug_layer") or "")
    named_boundary = str(causal.get("named_contract_boundary_id") or "")
    valid = (
        evidence.get("status") == "proven"
        and target_layer
        and target_layer == str(action.get("debug_layer") or "")
        and target_layer == str(causal.get("earliest_causal_owner") or "")
        and named_boundary
        and direct.get("kernel_start_accepted") is True
        and direct.get("kernel_ingress_complete") is True
        and direct.get("kernel_egress_ready") is True
        and all(
            is_sha256(source_binding.get(name))
            for name in (
                "input_fingerprint_sha256",
                "board_trace_sha256",
                "lower_layer_certificate_sha256",
            )
        )
    )
    if not valid:
        return {
            "schema_version": "spatialaccagent.repair_routing_priority.v1",
            "status": "not_applicable",
            "reason": "current contradiction lacks the required target, direct-boundary, or hash binding",
        }
    return {
        "schema_version": "spatialaccagent.repair_routing_priority.v1",
        "status": "authoritative",
        "policy": {
            "current_hash_bound_trace_controls_repair_target": True,
            "older_static_or_audit_failures_remain_recorded_but_do_not_reroute": True,
            "board_layer_remains_non_passing_until_a_later_full_rerun": True,
        },
        "required_repair_action": {
            key: copy.deepcopy(action.get(key))
            for key in (
                "scope",
                "repair_kind",
                "debug_layer",
                "repair_gate",
                "target_modules",
                "violated_contract",
            )
        },
        "proof": {
            "target_debug_layer": target_layer,
            "earliest_boundary": named_boundary,
            "direct_boundary_facts": {
                "kernel_start_accepted": True,
                "kernel_ingress_complete": True,
                "kernel_egress_ready": True,
            },
            "source_binding": {
                name: source_binding[name]
                for name in (
                    "input_fingerprint_sha256",
                    "board_trace_sha256",
                    "lower_layer_certificate_sha256",
                )
            },
        },
        "instruction": (
            "The required_repair_action is the only permitted next repair target. "
            "Do not redirect it to an older static or audit-only board failure."
        ),
    }


def exact_localized_repair_route(repair_plan: dict[str, Any]) -> bool:
    if validation_llm_team_mode() != "conditional":
        return False
    actions = [row for row in repair_plan.get("repair_actions", []) if isinstance(row, dict)]
    if len(actions) != 1:
        return False
    action = actions[0]
    routing_priority = authoritative_repair_routing_priority(repair_plan)
    if routing_priority.get("status") == "authoritative":
        # A current, hash-bound board trace can conclusively reopen a lower
        # layer.  Do not spend another large planning call on older board
        # metadata: the implementation Agent still receives and diagnoses the
        # bounded current-layer repair package.
        return True
    if (
        action.get("repair_kind") == "board_semantic_rtl_repair"
        and action.get("scope") == "verification_capability_repair"
        and action.get("debug_layer") == "board_axi_ddr_wrapped_system"
        and action.get("approval_required") is not True
    ):
        # The executor still fail-closes on stale/missing evidence.  This
        # direct route only avoids a second broad planner call after the
        # matching lower-layer recheck has already been consumed.
        return True
    # A VCS compiler diagnostic already identifies the current board layer and
    # its generated integration owner.  A second generic planner cannot add
    # evidence before the exact-board implementation Agent sees that same
    # diagnostic, so route directly to that Agent.  The Agent still decides
    # whether the source contract supports a patch and the real VCS rerun
    # remains mandatory after any accepted transaction.
    diagnosis = (
        repair_plan.get("diagnostics", {}).get("case_vcs_functional", {})
        if isinstance(repair_plan.get("diagnostics"), dict)
        else {}
    )
    if (
        action.get("repair_kind") == "exact_board_integration_harness"
        and action.get("scope") == "verification_capability_repair"
        and action.get("debug_layer") == "board_axi_ddr_wrapped_system"
        and action.get("approval_required") is not True
        and diagnosis.get("failure_class") == "vcs_compile_failure"
        and diagnosis.get("failure_evidence", {}).get("first_real_error")
    ):
        return True
    context = (
        action.get("minimal_repair_context", {})
        if isinstance(action.get("minimal_repair_context"), dict)
        else {}
    )
    trace = context.get("trace_record", {}) if isinstance(context.get("trace_record"), dict) else {}
    numeric = (
        action.get("corroborating_semantic_numeric_failure", {})
        if isinstance(action.get("corroborating_semantic_numeric_failure"), dict)
        else {}
    )
    diagnostics = repair_plan.get("diagnostics", {}) if isinstance(repair_plan.get("diagnostics"), dict) else {}
    loop = (
        diagnostics.get("hierarchical_repair_loop", {})
        if isinstance(diagnostics.get("hierarchical_repair_loop"), dict)
        else {}
    )
    challenge = (
        loop.get("lower_layer_evidence_challenge", {})
        if isinstance(loop.get("lower_layer_evidence_challenge"), dict)
        else {}
    )
    return bool(
        action.get("repair_kind") == "localized_semantic_dut_repair"
        and action.get("scope") == "verification_capability_repair"
        and action.get("approval_required") is not True
        and trace.get("status") == "fail"
        and trace.get("evidence_type") == "semantic_internal_boundary_trace"
        and trace.get("stage_id")
        and trace.get("module")
        and trace.get("violated_contract")
        and numeric.get("status") == "fail"
        and numeric.get("evidence_type") == "semantic_numeric_compare"
        and numeric.get("stage_id") == trace.get("stage_id")
        and challenge.get("status") == "no_lower_layer_challenge"
    )


def deterministic_localized_repair_record(
    repair_plan: dict[str, Any],
    out_dir: Path,
) -> dict[str, Any]:
    action = repair_plan["repair_actions"][0]
    routing_priority = authoritative_repair_routing_priority(repair_plan)
    if routing_priority.get("status") == "authoritative":
        target = routing_priority["required_repair_action"]
        output = {
            "schema_version": "spatialaccagent.stage_worker_output.v0",
            "agent": "repair_agent",
            "stage": "repair",
            "status": "ready",
            "summary": (
                "The current board run provides hash-bound proof for the next repair target. "
                "Execute the existing bounded repair workflow; older board audit failures "
                "remain recorded but cannot change this target."
            ),
            "sacg_focus": {
                "nodes": [target["debug_layer"]],
                "edges": [],
                "constraints": TOUCHED_CONSTRAINTS,
                "artifacts": ["artifact.stage6.repair_plan"],
            },
            "observations": [
                "current board proof is authoritative for repair routing",
                f"debug_layer={target['debug_layer']}",
                f"earliest_boundary={routing_priority['proof']['earliest_boundary']}",
            ],
            "risks": [
                "The current target must complete its bounded repair and rerun before the board layer resumes."
            ],
            "proposed_actions": [
                "Run the existing bounded repair workflow without another broad planning review."
            ],
            "executable_actions": [],
            "approval_required_for": [],
        }
        path = out_dir / "llm" / "repair_agent_deterministic_current_trace_route.json"
        record = {
            "schema_version": "spatialaccagent.stage_worker_record.v0",
            "agent": "repair_agent",
            "stage": "repair",
            "mode": "deterministic_current_trace_route",
            "result_path": str(path),
            "used_fallback": False,
            "error": None,
            "llm_skipped": True,
            "output": output,
        }
        write_json(path, record)
        return record
    if action.get("repair_kind") in {
        "exact_board_integration_harness",
        "board_semantic_rtl_repair",
    }:
        semantic_rtl = action.get("repair_kind") == "board_semantic_rtl_repair"
        output = {
            "schema_version": "spatialaccagent.stage_worker_output.v0",
            "agent": "repair_agent",
            "stage": "repair",
            "status": "ready",
            "summary": (
                "The current board trace is localized to the compiled internal RTL closure; "
                "invoke the bounded semantic RTL Agent directly with the preserved evidence package."
                if semantic_rtl
                else
                "The current exact-board VCS compile diagnostic is already localized to "
                "the generated integration workflow; invoke the exact-board implementation "
                "Agent directly with the preserved evidence package."
            ),
            "sacg_focus": {
                "nodes": [
                    "connected_kernel_internal_pipeline"
                    if semantic_rtl
                    else "board_axi_ddr_wrapped_system"
                ],
                "edges": [],
                "constraints": TOUCHED_CONSTRAINTS,
                "artifacts": ["artifact.stage6.repair_plan"],
            },
            "observations": [
                f"repair_kind={action.get('repair_kind')}",
                "failure_class=internal_pipeline_stop"
                if semantic_rtl
                else "failure_class=vcs_compile_failure",
                "the implementation Agent must reject any non-contract-derived patch",
            ],
            "risks": [
                "The exact user wrapper, ABI, model artifacts, and numeric policy remain read-only."
            ],
            "proposed_actions": [
                "Execute the existing exact-board implementation workflow without a second planning LLM call."
            ],
            "executable_actions": [],
            "approval_required_for": [],
        }
        path = out_dir / "llm" / (
            "repair_agent_deterministic_board_semantic_rtl_route.json"
            if semantic_rtl
            else "repair_agent_deterministic_exact_board_compile_route.json"
        )
        record = {
            "schema_version": "spatialaccagent.stage_worker_record.v0",
            "agent": "repair_agent",
            "stage": "repair",
            "mode": "deterministic_exact_board_compile_route",
            "result_path": str(path),
            "used_fallback": False,
            "error": None,
            "llm_skipped": True,
            "output": output,
        }
        write_json(path, record)
        return record
    trace = action["minimal_repair_context"]["trace_record"]
    output = {
        "schema_version": "spatialaccagent.stage_worker_output.v0",
        "agent": "repair_agent",
        "stage": "repair",
        "status": "ready",
        "summary": (
            "The deterministic CCTG action is complete and unambiguous: invoke the bounded implementation agent for "
            f"{trace.get('stage_id')} module {trace.get('module')} at {trace.get('boundary_id')}."
        ),
        "sacg_focus": {
            "nodes": [],
            "edges": [],
            "constraints": TOUCHED_CONSTRAINTS,
            "artifacts": ["artifact.stage6.repair_plan"],
        },
        "observations": [
            f"evidence_type={trace.get('evidence_type')}",
            f"violated_contract={trace.get('violated_contract')}",
            "same-stage independent semantic numeric failure is present",
        ],
        "risks": ["Only the authorized causal slice may be edited; the same golden gate must be rerun."],
        "proposed_actions": ["Execute the existing localized repair workflow step without another planning review."],
        "executable_actions": [],
        "approval_required_for": [],
    }
    path = out_dir / "llm" / "repair_agent_deterministic_localized_route.json"
    record = {
        "schema_version": "spatialaccagent.stage_worker_record.v0",
        "agent": "repair_agent",
        "stage": "repair",
        "mode": "deterministic_exact_localized_route",
        "result_path": str(path),
        "used_fallback": False,
        "error": None,
        "llm_skipped": True,
        "output": output,
    }
    write_json(path, record)
    return record


def no_split_repair_summary(reason: str) -> dict[str, Any]:
    return {
        "schema_version": "spatialaccagent.conditional_review_summary.v0",
        "stage": "repair",
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


def repair_llm_record_errors(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if record.get("used_fallback"):
        errors.append("repair targeted specialist used fallback output")
    if record.get("error"):
        errors.append(str(record.get("error")))
    output = record.get("output", {}) if isinstance(record.get("output"), dict) else {}
    if str(output.get("status") or "").strip().lower() in {"", "fallback", "unavailable"}:
        errors.append(f"repair targeted specialist status is {output.get('status')}")
    return errors


def run_repair_review_team(
    state: dict[str, Any],
    repair_plan: dict[str, Any],
    out_dir: Path,
    *,
    source_sacg_state: Path | None = None,
) -> tuple[dict[str, Any], dict[str, str | None]]:
    trigger = repair_specialist_trigger(repair_plan)
    if trigger == "full_team_requested":
        team = run_design_team(
            stage="repair",
            objective="Classify failed evidence into bounded repair actions while respecting human approval boundaries.",
            state=state,
            candidate_artifact=repair_plan,
            out_dir=out_dir,
        )
        return team_summary(team), {
            "team_subtask_plan": team["subtask_plan_path"],
            "team_aggregate": team["aggregate_path"],
        }
    if trigger is None:
        return no_split_repair_summary(
            "deterministic failure class is unambiguous; the primary repair agent owns the bounded action decision"
        ), {"team_subtask_plan": None, "team_aggregate": None}
    specialist = run_stage_agent(
        agent="repair_targeted_specialist_agent",
        stage="repair.targeted_specialist",
        task=(
            "Review only the routed repair ambiguity using the current CCTG slice, SACG evidence, current-layer "
            "gate states, and human boundary. Identify the earliest violated contract and the smallest legal repair. "
            "Do not reopen lower layers without a bound contradiction or run higher-layer tools before current closure."
        ),
        inputs={
            "routing_trigger": trigger,
            "candidate_repair_plan": repair_plan,
            **(
                {"source_sacg_state": str(source_sacg_state)}
                if source_sacg_state is not None
                else {}
            ),
        },
        out_dir=out_dir,
        fallback_summary="Targeted repair ambiguity review was unavailable.",
    )
    errors = repair_llm_record_errors(specialist)
    output = specialist.get("output", {}) if isinstance(specialist.get("output"), dict) else {}
    summary = {
        "schema_version": "spatialaccagent.conditional_review_summary.v0",
        "stage": "repair",
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


def approved_repair_action_ids() -> set[str]:
    """Return explicitly approved exact repair action IDs, without wildcards."""

    raw = os.environ.get("SPATIALACC_APPROVED_REPAIR_ACTION_IDS", "")
    values = raw.replace(",", " ").split()
    return {
        value
        for value in values
        if value
        and all(character.isalnum() or character in "._-" for character in value)
    }


def approval_action_is_currently_required(
    action: dict[str, Any],
    *,
    actions: list[dict[str, Any]] | None = None,
) -> bool:
    """Return whether an LLM approval action blocks the current workflow.

    A conditional approval describes a future branch, not a prerequisite for the
    work that establishes whether that branch is needed.  It becomes active only
    when an agent explicitly marks its condition as met; unconditional approval
    actions remain fail-closed.
    """
    if action.get("requires_approval") is not True:
        return False
    action_id = str(action.get("id") or "")
    if action_id and action_id in approved_repair_action_ids():
        return False
    for key in ("approval_condition_met", "condition_met", "activation_required"):
        if action.get(key) is True:
            return True
    activation_status = str(
        action.get("approval_activation_status")
        or action.get("approval_condition_status")
        or ""
    ).strip().lower()
    if activation_status in {"active", "met", "triggered", "required"}:
        return True
    consumes = action.get("consumes", [])
    consumes = consumes if isinstance(consumes, list) else []
    consumed_outputs = {str(value).strip() for value in consumes if str(value).strip()}
    for candidate in actions or []:
        candidate_id = str(candidate.get("id") or "")
        if not candidate_id or candidate_id == str(action.get("id") or ""):
            continue
        if candidate.get("status") in {"pass", "passed", "complete", "completed"}:
            continue
        if any(candidate_id in str(value) for value in consumes):
            return False
        produces = candidate.get("produces", [])
        produces = produces if isinstance(produces, list) else []
        if consumed_outputs.intersection(
            str(value).strip() for value in produces if str(value).strip()
        ):
            return False
    action_type = str(action.get("action_type") or "")
    conditional = action_type.startswith("conditional_") or bool(
        action.get("approval_condition")
    )
    return not conditional


def read_only_capability_action_is_auto_executable(
    action: dict[str, Any],
    workflow: dict[str, Any],
) -> bool:
    """Keep an LLM approval label from blocking a framework read-only producer.

    The Agent may require a human for a subsequent generated-source repair, but
    it must first be able to consume already-produced compiler evidence.  This
    deliberately recognizes only capability kinds whose executor is a
    read-only artifact producer; it grants no source-write or VCS authority.
    """

    action_text = " ".join(
        str(action.get(key) or "")
        for key in ("id", "action_type", "rationale")
    ).lower()
    read_only_capability_markers = {
        "operator_leaf_static_inventory_trace",
        "vcs_compile_diagnostic_source_provenance",
        "connected_kernel_current_dag_boundary_port_provenance",
        "connected_kernel_current_dag_boundary_signal_provenance",
        "connected_kernel_current_dag_boundary_signal_map",
        "repair.reconcile_exact_board_lifecycle_cctg_observation_contract",
        "exact_board_lifecycle_cctg_reconciliation",
    }
    if not any(marker in action_text for marker in read_only_capability_markers):
        return False
    for step in workflow.get("steps", []):
        if not isinstance(step, dict):
            continue
        deterministic_action = step.get("action", {})
        if not isinstance(deterministic_action, dict):
            continue
        if (
            deterministic_action.get("repair_kind")
            in {
                "operator_leaf_static_inventory_trace",
                "operator_leaf_static_inventory_trace_check",
                "vcs_compile_diagnostic_source_provenance",
                "connected_kernel_current_dag_boundary_signal_map",
                "repair.reconcile_exact_board_lifecycle_cctg_observation_contract",
            }
            and deterministic_action.get("approval_required") is False
            and step.get("scope") == "verification_capability_repair"
        ):
            return True
    return False


def reconcile_repair_workflow_with_llm(
    repair_plan: dict[str, Any],
    llm_output: dict[str, Any],
) -> dict[str, Any]:
    workflow = repair_plan.get("repair_workflow", {}) if isinstance(repair_plan.get("repair_workflow"), dict) else {}
    actions = [action for action in llm_output.get("executable_actions", []) if isinstance(action, dict)]
    auto_executable_capability_ids = [
        str(action.get("id") or action.get("action_type") or "read_only_capability")
        for action in actions
        if read_only_capability_action_is_auto_executable(action, workflow)
    ]
    approvals = [
        str(action.get("id") or action.get("action_type") or "approval")
        for action in actions
        if action.get("requires_approval")
        and str(action.get("id") or action.get("action_type") or "approval")
        not in set(auto_executable_capability_ids)
    ]
    configured_approvals = approved_repair_action_ids()
    approved_approvals = [
        str(action.get("id"))
        for action in actions
        if action.get("requires_approval")
        and str(action.get("id") or action.get("action_type") or "approval")
        not in set(auto_executable_capability_ids)
        and action.get("id")
        and str(action.get("id")) in configured_approvals
    ]
    active_approvals = [
        str(action.get("id") or action.get("action_type") or "approval")
        for action in actions
        if (
            str(action.get("id") or action.get("action_type") or "approval")
            not in set(auto_executable_capability_ids)
            and approval_action_is_currently_required(action, actions=actions)
        )
    ]
    deferred_approvals = [
        approval
        for approval in approvals
        if approval not in set(active_approvals)
        and approval not in set(approved_approvals)
    ]
    status = str(llm_output.get("status") or "").strip().lower()
    summary = str(llm_output.get("summary") or "")
    localized_steps = [
        step
        for step in workflow.get("steps", [])
        if isinstance(step, dict)
        and isinstance(step.get("action"), dict)
        and step["action"].get("repair_kind") == "localized_semantic_dut_repair"
        and step.get("status") == "ready_for_agent_patch"
    ]
    localization_ambiguous_steps = [
        step
        for step in localized_steps
        if step["action"].get("minimal_repair_context", {}).get("trace_record", {}).get("evidence_type")
        != "semantic_internal_boundary_trace"
    ]
    disposition_text = f"{status} {summary}".lower()
    instrumentation_first = bool(localization_ambiguous_steps) and not approvals and any(
        token in disposition_text
        for token in (
            "current_layer_localization",
            "current-layer localization",
            "targeted boundary replay",
            "earliest-causal-boundary",
            "earliest causal boundary",
        )
    )
    unresolved_approvals = set(approvals) - set(approved_approvals)
    textual_veto = any(
        token in disposition_text
        for token in (
            "reject the candidate plan",
            "first obtain approval",
            "pending_approved",
            "pending_human",
        )
    ) and not instrumentation_first and (not approvals or bool(unresolved_approvals))
    veto = bool(active_approvals) or textual_veto
    if instrumentation_first:
        for step in localization_ambiguous_steps:
            step["action"]["repair_phase"] = "instrumentation_first"
            step["action"]["template_repair_requires_internal_boundary_trace"] = True
            step["llm_disposition_constraint"] = (
                "instrument the existing semantic harness and rerun the same real golden stage; "
                "do not edit operator templates until the resulting internal trace identifies the earliest failure"
            )
    workflow["llm_disposition"] = {
        "status": status,
        "summary": summary,
        "executable_actions": copy.deepcopy(actions),
        "approval_action_ids": approvals,
        "approved_action_ids": approved_approvals,
        "auto_executable_read_only_capability_action_ids": auto_executable_capability_ids,
        "active_approval_action_ids": active_approvals,
        "deferred_approval_action_ids": deferred_approvals,
        "vetoed_pre_llm_execution": veto,
        "converted_to_instrumentation_first": instrumentation_first,
    }
    if veto:
        workflow["pre_llm_status"] = workflow.get("status")
        workflow["status"] = "approval_required" if active_approvals else "blocked"
        workflow["approval_steps"] = sorted(
            set([*workflow.get("approval_steps", []), *active_approvals])
        )
        reason = summary or "LLM repair disposition blocks the deterministic candidate workflow"
        blockers = list(workflow.get("blockers", []))
        if reason not in blockers:
            blockers.append(reason)
        workflow["blockers"] = blockers
        for step in workflow.get("steps", []):
            if not isinstance(step, dict) or step.get("status") not in {"ready_to_execute", "ready_for_agent_patch"}:
                continue
            step["pre_llm_status"] = step.get("status")
            step["status"] = "blocked_by_llm_disposition"
            step["llm_veto_reason"] = reason
    elif deferred_approvals:
        workflow["deferred_approval_steps"] = sorted(
            set([*workflow.get("deferred_approval_steps", []), *deferred_approvals])
        )
    if not veto:
        # A previous planner invocation may have persisted blocked_by_llm
        # statuses.  Once the active veto is removed, restore the deterministic
        # pre-LLM status instead of carrying a stale block into execution.
        for step in workflow.get("steps", []):
            if not isinstance(step, dict) or step.get("status") != "blocked_by_llm_disposition":
                continue
            prior_status = step.get("pre_llm_status")
            if prior_status in {"ready_to_execute", "ready_for_agent_patch", "blocked", "pending"}:
                step["status"] = prior_status
                step.pop("llm_veto_reason", None)
    repair_plan["repair_workflow"] = workflow
    repair_plan["llm_reconciliation"] = workflow.get("llm_disposition", {})
    return repair_plan


def restore_persisted_read_only_capability_steps(
    repair_plan: dict[str, Any],
) -> bool:
    """Recover only stale planner vetoes for framework-owned read-only steps.

    Stage-6 may be resumed from a persisted repair plan rather than regenerated
    after a controller restart.  Reapply the same narrow policy used during
    reconciliation so a historical approval label cannot indefinitely prevent
    a preserved-evidence producer from running.  This never restores a source
    repair, compile-plan rewrite, or VCS invocation.
    """

    workflow = repair_plan.get("repair_workflow")
    if not isinstance(workflow, dict):
        return False
    disposition = workflow.get("llm_disposition")
    if not isinstance(disposition, dict):
        disposition = repair_plan.get("llm_reconciliation", {})
    actions = (
        [action for action in disposition.get("executable_actions", []) if isinstance(action, dict)]
        if isinstance(disposition, dict)
        else []
    )
    read_only_ids = {
        str(action.get("id") or action.get("action_type") or "read_only_capability")
        for action in actions
        if read_only_capability_action_is_auto_executable(action, workflow)
    }
    if not read_only_ids:
        return False
    restored = False
    for step in workflow.get("steps", []):
        if not isinstance(step, dict) or step.get("status") != "blocked_by_llm_disposition":
            continue
        action = step.get("action", {})
        if not isinstance(action, dict) or action.get("repair_kind") not in {
            "operator_leaf_static_inventory_trace",
            "operator_leaf_static_inventory_trace_check",
            "vcs_compile_diagnostic_source_provenance",
            "connected_kernel_current_dag_boundary_signal_map",
            "repair.reconcile_exact_board_lifecycle_cctg_observation_contract",
        }:
            continue
        prior_status = step.get("pre_llm_status")
        if prior_status not in {"ready_for_agent_patch", "ready_to_execute"}:
            continue
        step["status"] = prior_status
        step.pop("llm_veto_reason", None)
        restored = True
    if not restored:
        return False
    if isinstance(disposition, dict):
        disposition["auto_executable_read_only_capability_action_ids"] = sorted(read_only_ids)
        disposition["active_approval_action_ids"] = [
            value
            for value in disposition.get("active_approval_action_ids", [])
            if str(value) not in read_only_ids
        ]
        disposition["vetoed_pre_llm_execution"] = bool(
            disposition.get("active_approval_action_ids")
        )
        workflow["llm_disposition"] = disposition
        repair_plan["llm_reconciliation"] = disposition
    if workflow.get("status") == "approval_required" and not workflow["llm_disposition"].get("active_approval_action_ids"):
        workflow["status"] = "ready"
        workflow["approval_steps"] = [
            value for value in workflow.get("approval_steps", []) if str(value) not in read_only_ids
        ]
        veto_reason = str(workflow["llm_disposition"].get("summary") or "")
        workflow["blockers"] = [
            value for value in workflow.get("blockers", []) if str(value) != veto_reason
        ]
    return True


def update_sacg(source_state: Path, target_state: Path, repair_path: Path, repair_plan: dict[str, Any]) -> str:
    copy_state(source_state, target_state)
    store = SACGStore(target_state)
    existing_constraint_ids = {str(item.get("id")) for item in store.state.get("constraints", [])}
    touched_constraints = [cid for cid in TOUCHED_CONSTRAINTS if cid in existing_constraint_ids] or ["constraint.verification.plan"]
    scopes = [item["scope"] for item in repair_plan.get("repair_actions", [])]
    diagnostics = (
        repair_plan.get("diagnostics", {})
        if isinstance(repair_plan.get("diagnostics"), dict)
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
    first_action = next(
        (
            row
            for row in repair_plan.get("repair_actions", [])
            if isinstance(row, dict)
        ),
        {},
    )
    memory_context = hierarchy_memory_context(
        debug_layer=current_layer.get("id") or first_action.get("debug_layer"),
        failed_gates=repair_loop.get("failed_current_layer_gates", [])
        or first_action.get("failed_current_layer_gates", []),
    )
    transition = store.declare_transition(
        action_type="repair",
        touched_nodes=[],
        touched_edges=[],
        touched_constraints=touched_constraints,
        repair_scopes=scopes,
        note="Planned bounded repair actions from verification result.",
        context=memory_context,
    )
    store.bind_artifact(
        "artifact.stage6.repair_plan",
        str(repair_path),
        "stage.repair_plan",
        [],
        [],
        touched_constraints,
        transition["id"],
    )
    if repair_plan["status"] == "ready":
        invariant = next(
            (
                item
                for item in store.state.get("invariants", [])
                if item.get("checker") == "verification_plan_static_check"
            ),
            None,
        )
        if invariant:
            store.attach_evidence(
                checker="verification_plan_static_check",
                status="pass",
                invariant=invariant["id"],
                constraints=invariant.get("constraints", []),
                artifacts=["artifact.stage6.repair_plan"],
                log_path=str(repair_path),
                transition_id=transition["id"],
                summary="verification result has no failed checks; no bounded repair action is required",
            )
        store.promote(transition["id"])
    else:
        store.reject(transition["id"], "repair actions are required before promotion")
        failures = [
            f"{item.get('checker')}: {item.get('summary')}"
            for item in repair_plan.get("failures", [])[:8]
        ]
        store.record_failure_lesson(
            stage="stage6.repair",
            failure_class="bounded_repair_required",
            summary="; ".join(failures) or "Stage6 found repair actions are required",
            violated_constraints=touched_constraints,
            artifacts=["artifact.stage6.repair_plan"],
            recommended_action="Execute the bounded repair workflow, then rerun Stage6. Do not continue to backend/board closure with unresolved verification failures.",
            retry_scope="repair_then_stage6_rerun",
            context=memory_context,
        )
        store.record_retry_request(
            stage="stage6.repair",
            reason="Bounded repair actions must be completed before verification can be promoted",
            target_stage="stage6.verification",
            required_inputs=["artifact.stage6.repair_plan"],
            blocked_artifacts=["artifact.stage6.repair_plan"],
            context=memory_context,
        )
    store.record_stage_outcome(
        stage="stage6.repair",
        status=repair_plan["status"],
        transition_id=transition["id"],
        summary=f"repair_status={repair_plan.get('status')} workflow_status={(repair_plan.get('repair_workflow') or {}).get('status')}",
        errors=[f"{item.get('checker')}: {item.get('summary')}" for item in repair_plan.get("failures", [])],
        artifacts=["artifact.stage6.repair_plan"],
        next_actions=[] if repair_plan["status"] == "ready" else ["complete bounded repair workflow and rerun Stage6"],
        retryable=repair_plan["status"] != "ready",
        context=memory_context,
    )
    store.save()
    return transition["id"]


def plan_repair(args: argparse.Namespace) -> tuple[Path, dict[str, Any]]:
    source_state = args.sacg_state.resolve()
    run_dir = run_dir_from_state(source_state)
    out_dir = run_dir / "repair"
    repair_path = out_dir / "repair_plan.json"
    state_path = out_dir / "sacg_state.json"
    report_path = out_dir / "repair_report.json"

    source_data = read_json(source_state)
    flow_controller_handoff = getattr(args, "flow_controller_handoff", None)
    repair_plan = build_repair_plan(
        source_data,
        run_dir,
        flow_controller_handoff=(
            flow_controller_handoff
            if isinstance(flow_controller_handoff, dict)
            else None
        ),
    )
    write_json(repair_path, repair_plan)
    team_error = None
    try:
        design_team_summary, team_paths = run_repair_review_team(
            source_data,
            repair_plan,
            out_dir,
            source_sacg_state=source_state,
        )
    except Exception as exc:
        if llm_enforce():
            raise
        team_error = str(exc)
        design_team_summary = {
            "status": "unavailable",
            "errors": [team_error],
            "subtask_count": 0,
            "completed_subtasks": 0,
        }
        team_paths = {"team_subtask_plan": None, "team_aggregate": None}

    llm_error = None
    deterministic_localized_route = exact_localized_repair_route(repair_plan)
    if deterministic_localized_route:
        llm = deterministic_localized_repair_record(repair_plan, out_dir)
    else:
        try:
            completed_lower_layer_capabilities = (
                repair_plan.get("diagnostics", {}).get(
                    "completed_lower_layer_capabilities", []
                )
                if isinstance(repair_plan.get("diagnostics"), dict)
                else []
            )
            replay_guard = (
                "The candidate plan contains hash-bound completed lower-layer capability evidence. "
                "Treat it as closed: do not request, rerun, or repair the connected-kernel replay "
                "unless a new current trace explicitly contradicts its certified invariant. Select only "
                "the next causally distinct exact-board AXI/DDR action."
                if completed_lower_layer_capabilities
                else ""
            )
            llm = run_stage_agent(
                agent="repair_agent",
                stage="repair",
                task=(
                    "Make the authoritative bounded-repair decision from verification failures, SACG/CCTG evidence, and the "
                    "conditional specialist review when one was triggered, without bypassing checkers. "
                    "Respect the hierarchical repair loop: if lower layers already passed and the current layer failed, "
                    "request current-layer boundary trace/targeted replay first; reopen lower-layer modules only "
                    "when the trace explicitly contradicts their pass evidence. "
                    + replay_guard
                ),
                inputs={
                    "candidate_repair_plan": repair_plan,
                    "design_team": design_team_summary,
                    "source_sacg_state": str(source_state),
                    "completed_lower_layer_capabilities": completed_lower_layer_capabilities,
                    "flow_controller_handoff": (
                        repair_plan.get("diagnostics", {}).get("flow_controller_handoff")
                        if isinstance(repair_plan.get("diagnostics"), dict)
                        else None
                    ),
                },
                out_dir=out_dir,
                fallback_summary="Repair plan generated from failed verification results.",
            )
        except Exception as exc:
            if llm_enforce():
                raise
            llm_error = str(exc)
            llm_path = out_dir / "llm" / "repair_agent_result.json"
            llm_output = {
                "schema_version": "spatialaccagent.stage_worker_output.v0",
                "agent": "repair_agent",
                "stage": "repair",
                "status": "unavailable",
                "summary": "LLM repair reviewer unavailable; deterministic repair plan remains authoritative.",
                "sacg_focus": {"nodes": [], "edges": [], "constraints": TOUCHED_CONSTRAINTS, "artifacts": ["artifact.stage6.repair_plan"]},
                "observations": [f"LLM repair reviewer failed: {llm_error}"],
                "risks": ["LLM outage must not remove deterministic repair actions."],
                "proposed_actions": [],
                "executable_actions": [],
                "approval_required_for": [],
            }
            write_json(
                llm_path,
                {
                    "schema_version": "spatialaccagent.stage_worker_record.v0",
                    "agent": "repair_agent",
                    "stage": "repair",
                    "mode": "llm",
                    "used_fallback": True,
                    "error": llm_error,
                    "output": llm_output,
                },
            )
            llm = {"result_path": str(llm_path), "output": llm_output, "error": llm_error, "used_fallback": True}
    llm_output = llm["output"]
    if exact_board_identity_contract_passed(run_dir):
        # The discovery producer is already checker-valid.  Older repair
        # prompts may still ask for a human-approved identity rebind; remove
        # only that obsolete action so it cannot veto the real integration
        # repair or trigger another redundant Vivado discovery.
        llm_output = copy.deepcopy(llm_output)
        llm_output["executable_actions"] = [
            action
            for action in llm_output.get("executable_actions", [])
            if not (
                isinstance(action, dict)
                and "rebind_exact_board_contract"
                in str(action.get("id") or "")
            )
        ]
        llm["output"] = llm_output
    repair_plan = reconcile_repair_workflow_with_llm(repair_plan, llm_output)
    write_json(repair_path, repair_plan)
    transition_id = update_sacg(source_state, state_path, repair_path, repair_plan)
    report_status = "ready" if repair_plan["status"] == "ready" else repair_plan["status"]
    report = {
        "schema_version": "spatialaccagent.repair_report.v0",
        "stage": "repair",
        "status": report_status,
        "source_sacg_state": str(source_state),
        "outputs": {
            "repair_plan": str(repair_path),
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
            "specialist_trigger": repair_specialist_trigger(repair_plan),
            "primary_agent_required": not deterministic_localized_route,
            "deterministic_exact_localized_route": deterministic_localized_route,
            "fixed_decomposer_and_multi_specialist_fanout_removed": validation_llm_team_mode() == "conditional",
        },
        "team_executable_actions": design_team_summary.get("executable_actions", []),
        "team_error": team_error,
        "repair_status": repair_plan["status"],
        "sacg_transition_id": transition_id,
        "errors": [] if repair_plan["status"] == "ready" else [
            f"{item.get('checker')}: {item.get('summary')}" for item in repair_plan.get("failures", [])
        ],
    }
    write_json(report_path, report)
    return report_path, report


def main(argv: list[str] | None = None) -> int:
    return run_sacg_stage("Repair planning stage", plan_repair, argv)


if __name__ == "__main__":
    raise SystemExit(main())
