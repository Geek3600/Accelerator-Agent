"""Minimal SACG state store.

The runtime deliberately starts small. It treats SACG as the source of truth
for agent actions: edits become valid design updates only after a transition
declares touched constraints and receives the required evidence or approval.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


AUTO_ALLOWED_REPAIR_SCOPES = {
    "parameter_sync",
    "signal_connection",
    "script_path",
    "trace_parser",
    "wrapper_runtime_sync",
    "valid_delay",
    "address_offset",
    "ddr_image_regen",
    "small_fifo_depth",
    "regression_rerun",
}

APPROVAL_REQUIRED_REPAIR_SCOPES = {
    "pipeline_stage_change",
    "tile_size_change",
    "parallelism_change",
    "memory_layout_change",
    "data_packing_change",
    "numeric_policy_change",
    "major_template_rewrite",
    "timing_pipeline_stage",
    "axi_ddr_access_change",
    "major_buffer_structure",
}

FORBIDDEN_REPAIR_SCOPES = {
    "delete_failing_test",
    "modify_golden_to_pass",
    "loosen_tolerance_without_approval",
    "change_model_semantics",
    "treat_gqa_as_mha",
    "bypass_checker",
    "mark_failed_regression_pass",
    "claim_root_cause_without_evidence",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"SACG state must be a JSON object: {path}")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def ensure_state_defaults(state: dict[str, Any]) -> dict[str, Any]:
    state.setdefault("sacg_version", "1.0-min")
    state.setdefault("design_id", "unnamed_design")
    state.setdefault("nodes", [])
    state.setdefault("edges", [])
    state.setdefault("constraints", [])
    state.setdefault("invariants", [])
    state.setdefault("artifacts", [])
    state.setdefault("evidence", [])
    state.setdefault("failures", [])
    state.setdefault("repairs", [])
    state.setdefault("approvals", [])
    state.setdefault("transitions", [])
    memory = state.setdefault("memory", {})
    memory.setdefault("schema_version", "spatialaccagent.sacg_memory.v0")
    memory.setdefault("design_goal_trace", [])
    memory.setdefault("stage_outcomes", [])
    memory.setdefault("failure_lessons", [])
    memory.setdefault("retry_requests", [])
    memory.setdefault("backtrack_requests", [])
    memory.setdefault("contamination_barriers", [])
    memory.setdefault("reconciliation_events", [])
    return state


def list_ids(items: list[dict[str, Any]], kind: str) -> set[str]:
    ids: set[str] = set()
    for item in items:
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id:
            raise ValueError(f"{kind} item missing non-empty id: {item}")
        if item_id in ids:
            raise ValueError(f"duplicate {kind} id: {item_id}")
        ids.add(item_id)
    return ids


def get_item(state: dict[str, Any], collection: str, item_id: str) -> dict[str, Any]:
    for item in state.get(collection, []):
        if item.get("id") == item_id:
            return item
    raise KeyError(f"unknown {collection} id: {item_id}")


def validate_references(state: dict[str, Any]) -> list[str]:
    state = ensure_state_defaults(state)
    errors: list[str] = []

    try:
        node_ids = list_ids(state["nodes"], "node")
        edge_ids = list_ids(state["edges"], "edge")
        constraint_ids = list_ids(state["constraints"], "constraint")
        invariant_ids = list_ids(state["invariants"], "invariant")
        artifact_ids = list_ids(state["artifacts"], "artifact")
        evidence_ids = list_ids(state["evidence"], "evidence")
        list_ids(state["repairs"], "repair")
        list_ids(state["approvals"], "approval")
        list_ids(state["transitions"], "transition")
    except ValueError as exc:
        return [str(exc)]

    for edge in state["edges"]:
        if edge.get("src") not in node_ids:
            errors.append(f"edge {edge['id']} has unknown src {edge.get('src')}")
        if edge.get("dst") not in node_ids:
            errors.append(f"edge {edge['id']} has unknown dst {edge.get('dst')}")
        for cid in edge.get("constraints", []):
            if cid not in constraint_ids:
                errors.append(f"edge {edge['id']} references unknown constraint {cid}")

    for node in state["nodes"]:
        for cid in node.get("constraints", []):
            if cid not in constraint_ids:
                errors.append(f"node {node['id']} references unknown constraint {cid}")
        for aid in node.get("artifacts", []):
            if aid not in artifact_ids:
                errors.append(f"node {node['id']} references unknown artifact {aid}")

    for constraint in state["constraints"]:
        for nid in constraint.get("nodes", []):
            if nid not in node_ids:
                errors.append(f"constraint {constraint['id']} references unknown node {nid}")
        for eid in constraint.get("edges", []):
            if eid not in edge_ids:
                errors.append(f"constraint {constraint['id']} references unknown edge {eid}")
        for aid in constraint.get("artifacts", []):
            if aid not in artifact_ids:
                errors.append(f"constraint {constraint['id']} references unknown artifact {aid}")

    for invariant in state["invariants"]:
        for cid in invariant.get("constraints", []):
            if cid not in constraint_ids:
                errors.append(f"invariant {invariant['id']} references unknown constraint {cid}")
        eid = invariant.get("latest_evidence")
        if eid and eid not in evidence_ids:
            errors.append(f"invariant {invariant['id']} references unknown evidence {eid}")

    for artifact in state["artifacts"]:
        for nid in artifact.get("nodes", []):
            if nid not in node_ids:
                errors.append(f"artifact {artifact['id']} references unknown node {nid}")
        for eid in artifact.get("edges", []):
            if eid not in edge_ids:
                errors.append(f"artifact {artifact['id']} references unknown edge {eid}")
        for cid in artifact.get("constraints", []):
            if cid not in constraint_ids:
                errors.append(f"artifact {artifact['id']} references unknown constraint {cid}")

    return errors


def next_id(state: dict[str, Any], collection: str, prefix: str) -> str:
    existing = {item.get("id") for item in state.get(collection, [])}
    index = len(existing) + 1
    while True:
        item_id = f"{prefix}.{index:04d}"
        if item_id not in existing:
            return item_id
        index += 1


def next_memory_id(state: dict[str, Any], collection: str, prefix: str) -> str:
    memory = ensure_state_defaults(state).setdefault("memory", {})
    existing = {item.get("id") for item in memory.get(collection, []) if isinstance(item, dict)}
    index = len(existing) + 1
    while True:
        item_id = f"{prefix}.{index:04d}"
        if item_id not in existing:
            return item_id
        index += 1


def classify_repair_scope(scopes: list[str]) -> str:
    scope_set = set(scopes)
    if scope_set & FORBIDDEN_REPAIR_SCOPES:
        return "forbidden"
    if scope_set & APPROVAL_REQUIRED_REPAIR_SCOPES:
        return "approval_required"
    if scope_set and scope_set <= AUTO_ALLOWED_REPAIR_SCOPES:
        return "auto_allowed"
    if not scope_set:
        return "not_repair"
    return "approval_required"


def required_checkers(state: dict[str, Any], constraint_ids: list[str]) -> list[str]:
    checkers: set[str] = set()
    constraint_set = set(constraint_ids)
    for invariant in state.get("invariants", []):
        if constraint_set & set(invariant.get("constraints", [])):
            checker = invariant.get("checker")
            if checker:
                checkers.add(str(checker))
    return sorted(checkers)


def _normalized_memory_values(values: Any) -> tuple[str, ...]:
    if not isinstance(values, list):
        return ()
    return tuple(sorted({str(value).strip() for value in values if str(value).strip()}))


def _memory_context_key(context: dict[str, Any] | None) -> tuple[str, str, tuple[str, ...]]:
    context = context if isinstance(context, dict) else {}
    return (
        str(context.get("verification_scope") or ""),
        str(context.get("debug_layer") or ""),
        _normalized_memory_values(context.get("failed_gates")),
    )


def _retry_request_key(
    *,
    stage: Any,
    target_stage: Any,
    reason: Any,
    required_inputs: Any,
    blocked_artifacts: Any,
    context: dict[str, Any] | None,
) -> tuple[Any, ...]:
    return (
        str(stage or ""),
        str(target_stage or ""),
        str(reason or ""),
        _normalized_memory_values(required_inputs),
        _normalized_memory_values(blocked_artifacts),
        *_memory_context_key(context),
    )


def _backtrack_request_key(
    *,
    stage: Any,
    target_stage: Any,
    reason: Any,
    missing_or_invalid_contracts: Any,
    evidence: Any,
    context: dict[str, Any] | None,
) -> tuple[Any, ...]:
    return (
        str(stage or ""),
        str(target_stage or ""),
        str(reason or ""),
        _normalized_memory_values(missing_or_invalid_contracts),
        _normalized_memory_values(evidence),
        *_memory_context_key(context),
    )


def _contamination_barrier_key(
    *,
    artifact_id: Any,
    reason: Any,
    context: dict[str, Any] | None,
) -> tuple[Any, ...]:
    return (
        str(artifact_id or ""),
        str(reason or ""),
        *_memory_context_key(context),
    )


def _context_from_memory_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        key: record.get(key)
        for key in (
            "verification_scope",
            "debug_layer",
            "failed_gates",
            "source_fingerprint_sha256",
        )
        if record.get(key) not in (None, "", [])
    }


def _merge_observation_metadata(
    primary: dict[str, Any],
    duplicate: dict[str, Any],
) -> None:
    primary["observation_count"] = int(primary.get("observation_count") or 1) + int(
        duplicate.get("observation_count") or 1
    )
    fingerprints = [
        str(value)
        for value in primary.get("observed_source_fingerprint_sha256s", [])
        if str(value)
    ]
    for record in (primary, duplicate):
        value = str(record.get("source_fingerprint_sha256") or "")
        if value and value not in fingerprints:
            fingerprints.append(value)
        for value in record.get("observed_source_fingerprint_sha256s", []):
            value = str(value)
            if value and value not in fingerprints:
                fingerprints.append(value)
    if fingerprints:
        primary["observed_source_fingerprint_sha256s"] = fingerprints[-16:]
        primary["source_fingerprint_sha256"] = fingerprints[-1]
    transitions = [
        str(value)
        for value in primary.get("observed_transition_ids", [])
        if str(value)
    ]
    for record in (primary, duplicate):
        value = str(record.get("transition_id") or "")
        if value and value not in transitions:
            transitions.append(value)
        for value in record.get("observed_transition_ids", []):
            value = str(value)
            if value and value not in transitions:
                transitions.append(value)
    if transitions:
        primary["observed_transition_ids"] = transitions[-32:]


def _record_reobservation(
    record: dict[str, Any],
    *,
    context: dict[str, Any] | None,
    transition_id: str = "",
) -> None:
    record["observation_count"] = int(record.get("observation_count") or 1) + 1
    record["last_observed_at"] = utc_now()
    context = context if isinstance(context, dict) else {}
    fingerprint = str(context.get("source_fingerprint_sha256") or "")
    if fingerprint:
        fingerprints = [
            str(value)
            for value in record.get("observed_source_fingerprint_sha256s", [])
            if str(value)
        ]
        if fingerprint not in fingerprints:
            fingerprints.append(fingerprint)
        record["observed_source_fingerprint_sha256s"] = fingerprints[-16:]
        record["source_fingerprint_sha256"] = fingerprint
    if transition_id:
        transitions = [
            str(value)
            for value in record.get("observed_transition_ids", [])
            if str(value)
        ]
        if transition_id not in transitions:
            transitions.append(transition_id)
        record["observed_transition_ids"] = transitions[-32:]


class SACGStore:
    def __init__(self, path: Path):
        self.path = path
        self.state = ensure_state_defaults(read_json(path))

    def save(self) -> None:
        write_json(self.path, self.state)

    def validate(self) -> list[str]:
        return validate_references(self.state)

    def deduplicate_active_memory_records(self) -> dict[str, Any]:
        """Coalesce legacy repeated open obligations without losing their audit trail."""

        memory = self.state.setdefault("memory", {})
        report: dict[str, Any] = {
            "schema_version": "spatialaccagent.sacg_memory_idempotence.v1",
            "status": "pass",
            "deduplicated_retry_requests": [],
            "deduplicated_backtrack_requests": [],
            "deduplicated_contamination_barriers": [],
        }

        def collapse(
            rows: list[dict[str, Any]],
            *,
            key_for: Any,
            active_status: str,
            duplicate_status: str,
            report_key: str,
            reason: str,
        ) -> None:
            groups: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
            for row in rows:
                if not isinstance(row, dict) or row.get("status", active_status) != active_status:
                    continue
                groups.setdefault(key_for(row), []).append(row)
            for group in groups.values():
                if len(group) < 2:
                    continue
                primary = group[0]
                merged_ids: list[str] = []
                for duplicate in group[1:]:
                    _merge_observation_metadata(primary, duplicate)
                    duplicate["status"] = duplicate_status
                    duplicate["deduplicated_at"] = utc_now()
                    duplicate["deduplicated_into"] = primary.get("id")
                    duplicate["resolution_reason"] = reason
                    merged_ids.append(str(duplicate.get("id") or ""))
                report[report_key].append(
                    {
                        "canonical_id": primary.get("id"),
                        "deduplicated_ids": [value for value in merged_ids if value],
                        "observation_count": primary.get("observation_count"),
                    }
                )

        collapse(
            [row for row in memory.get("retry_requests", []) if isinstance(row, dict)],
            key_for=lambda row: _retry_request_key(
                stage=row.get("stage"),
                target_stage=row.get("target_stage"),
                reason=row.get("reason"),
                required_inputs=row.get("required_inputs"),
                blocked_artifacts=row.get("blocked_artifacts"),
                context=_context_from_memory_record(row),
            ),
            active_status="open",
            duplicate_status="closed",
            report_key="deduplicated_retry_requests",
            reason=(
                "idempotent duplicate of an active retry request for the same "
                "stage, scope, failed gates, and blocked artifacts"
            ),
        )
        collapse(
            [row for row in memory.get("backtrack_requests", []) if isinstance(row, dict)],
            key_for=lambda row: _backtrack_request_key(
                stage=row.get("stage"),
                target_stage=row.get("target_stage"),
                reason=row.get("reason"),
                missing_or_invalid_contracts=row.get("missing_or_invalid_contracts"),
                evidence=row.get("evidence"),
                context=_context_from_memory_record(row),
            ),
            active_status="open",
            duplicate_status="closed",
            report_key="deduplicated_backtrack_requests",
            reason=(
                "idempotent duplicate of an active backtrack request for the same "
                "stage, scope, failed gates, and evidence"
            ),
        )
        collapse(
            [
                row
                for row in memory.get("contamination_barriers", [])
                if isinstance(row, dict)
            ],
            key_for=lambda row: _contamination_barrier_key(
                artifact_id=row.get("artifact_id"),
                reason=row.get("reason"),
                context=_context_from_memory_record(row),
            ),
            active_status="active",
            duplicate_status="superseded",
            report_key="deduplicated_contamination_barriers",
            reason=(
                "idempotent duplicate of an active contamination barrier for the "
                "same rejected artifact, scope, and failed gates"
            ),
        )
        report["changed"] = any(
            bool(report[key])
            for key in (
                "deduplicated_retry_requests",
                "deduplicated_backtrack_requests",
                "deduplicated_contamination_barriers",
            )
        )
        return report

    def declare_transition(
        self,
        action_type: str,
        touched_nodes: list[str],
        touched_edges: list[str],
        touched_constraints: list[str],
        actor: str = "agent",
        note: str = "",
        repair_scopes: list[str] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not touched_constraints:
            raise ValueError("transition rejected: touched_constraints must be non-empty")

        for node_id in touched_nodes:
            get_item(self.state, "nodes", node_id)
        for edge_id in touched_edges:
            get_item(self.state, "edges", edge_id)
        for constraint_id in touched_constraints:
            get_item(self.state, "constraints", constraint_id)

        scopes = repair_scopes or []
        repair_scope = classify_repair_scope(scopes)
        approval_required = repair_scope == "approval_required"

        transition = {
            "id": next_id(self.state, "transitions", "transition"),
            "timestamp": utc_now(),
            "actor": actor,
            "action_type": action_type,
            "touched_nodes": touched_nodes,
            "touched_edges": touched_edges,
            "touched_constraints": touched_constraints,
            "required_checkers": required_checkers(self.state, touched_constraints),
            "repair_scopes": scopes,
            "repair_scope_class": repair_scope,
            "approval_required": approval_required,
            "approval_id": None,
            "artifacts_changed": [],
            "artifacts_generated": [],
            "evidence": [],
            "status": "declared",
            "note": note,
            **{
                key: value
                for key in (
                    "verification_scope",
                    "debug_layer",
                    "failed_gates",
                    "source_fingerprint_sha256",
                )
                for value in [(context or {}).get(key)]
                if value not in (None, "", [])
            },
        }
        self.state["transitions"].append(transition)
        return transition

    def bind_artifact(
        self,
        artifact_id: str,
        path: str,
        artifact_type: str,
        nodes: list[str],
        edges: list[str],
        constraints: list[str],
        producer_transition: str,
    ) -> dict[str, Any]:
        for node_id in nodes:
            get_item(self.state, "nodes", node_id)
        for edge_id in edges:
            get_item(self.state, "edges", edge_id)
        for constraint_id in constraints:
            get_item(self.state, "constraints", constraint_id)

        artifact = {
            "id": artifact_id,
            "path": path,
            "type": artifact_type,
            "nodes": nodes,
            "edges": edges,
            "constraints": constraints,
            "freshness": "fresh",
            "trust_status": "pending_transition",
            "producer_transition": producer_transition,
        }

        replaced = False
        for index, existing in enumerate(self.state["artifacts"]):
            if existing.get("id") == artifact_id:
                self.state["artifacts"][index] = artifact
                replaced = True
                break
        if not replaced:
            self.state["artifacts"].append(artifact)

        transition = get_item(self.state, "transitions", producer_transition)
        if artifact_id not in transition["artifacts_generated"]:
            transition["artifacts_generated"].append(artifact_id)
        return artifact

    def record_stage_outcome(
        self,
        *,
        stage: str,
        status: str,
        transition_id: str | None,
        summary: str,
        errors: list[str] | None = None,
        artifacts: list[str] | None = None,
        next_actions: list[str] | None = None,
        retryable: bool = True,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        memory = self.state.setdefault("memory", {})
        outcome = {
            "id": next_memory_id(self.state, "stage_outcomes", "stage_outcome"),
            "timestamp": utc_now(),
            "stage": stage,
            "status": status,
            "transition_id": transition_id,
            "summary": summary,
            "errors": list(errors or [])[:16],
            "artifacts": list(artifacts or [])[:24],
            "next_actions": list(next_actions or [])[:12],
            "retryable": retryable,
            **{
                key: value
                for key in (
                    "verification_scope",
                    "debug_layer",
                    "failed_gates",
                    "source_fingerprint_sha256",
                )
                for value in [(context or {}).get(key)]
                if value not in (None, "", [])
            },
        }
        memory.setdefault("stage_outcomes", []).append(outcome)
        if status in {"ready", "pass", "approved"} and transition_id:
            self.resolve_open_requests_for_stage(
                target_stage=stage,
                transition_id=transition_id,
                summary=summary,
            )
        return outcome

    def resolve_open_requests_for_stage(
        self,
        *,
        target_stage: str,
        transition_id: str,
        summary: str,
    ) -> int:
        memory = self.state.setdefault("memory", {})
        closed = 0
        for collection in ["retry_requests", "backtrack_requests"]:
            for request in memory.get(collection, []):
                if not isinstance(request, dict):
                    continue
                if request.get("status") != "open":
                    continue
                if request.get("target_stage") != target_stage:
                    continue
                request["status"] = "closed"
                request["closed_at"] = utc_now()
                request["closed_by_transition"] = transition_id
                request["resolution_summary"] = summary
                closed += 1
        return closed

    def record_failure_lesson(
        self,
        *,
        stage: str,
        failure_class: str,
        summary: str,
        violated_constraints: list[str] | None = None,
        artifacts: list[str] | None = None,
        recommended_action: str = "",
        retry_scope: str = "same_stage",
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        memory = self.state.setdefault("memory", {})
        lesson = {
            "id": next_memory_id(self.state, "failure_lessons", "failure_lesson"),
            "timestamp": utc_now(),
            "stage": stage,
            "failure_class": failure_class,
            "summary": summary,
            "violated_constraints": list(violated_constraints or [])[:12],
            "artifacts": list(artifacts or [])[:12],
            "recommended_action": recommended_action,
            "retry_scope": retry_scope,
            **{
                key: value
                for key in (
                    "verification_scope",
                    "debug_layer",
                    "failed_gates",
                    "source_fingerprint_sha256",
                )
                for value in [(context or {}).get(key)]
                if value not in (None, "", [])
            },
        }
        memory.setdefault("failure_lessons", []).append(lesson)
        return lesson

    def record_retry_request(
        self,
        *,
        stage: str,
        reason: str,
        target_stage: str,
        required_inputs: list[str] | None = None,
        blocked_artifacts: list[str] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        memory = self.state.setdefault("memory", {})
        context = context if isinstance(context, dict) else {}
        request_key = _retry_request_key(
            stage=stage,
            target_stage=target_stage,
            reason=reason,
            required_inputs=required_inputs,
            blocked_artifacts=blocked_artifacts,
            context=context,
        )
        matching = [
            row
            for row in memory.get("retry_requests", [])
            if isinstance(row, dict)
            and row.get("status") == "open"
            and _retry_request_key(
                stage=row.get("stage"),
                target_stage=row.get("target_stage"),
                reason=row.get("reason"),
                required_inputs=row.get("required_inputs"),
                blocked_artifacts=row.get("blocked_artifacts"),
                context=_context_from_memory_record(row),
            )
            == request_key
        ]
        if matching:
            primary = matching[0]
            for duplicate in matching[1:]:
                _merge_observation_metadata(primary, duplicate)
                duplicate["status"] = "closed"
                duplicate["closed_at"] = utc_now()
                duplicate["deduplicated_into"] = primary.get("id")
                duplicate["resolution_reason"] = (
                    "idempotent duplicate of an active retry request for the same "
                    "stage, scope, failed gates, and blocked artifacts"
                )
            _record_reobservation(primary, context=context)
            return primary
        request = {
            "id": next_memory_id(self.state, "retry_requests", "retry_request"),
            "timestamp": utc_now(),
            "stage": stage,
            "target_stage": target_stage,
            "reason": reason,
            "required_inputs": list(required_inputs or [])[:16],
            "blocked_artifacts": list(blocked_artifacts or [])[:16],
            **{
                key: value
                for key in (
                    "verification_scope",
                    "debug_layer",
                    "failed_gates",
                    "source_fingerprint_sha256",
                )
                for value in [(context or {}).get(key)]
                if value not in (None, "", [])
            },
            "status": "open",
            "observation_count": 1,
        }
        fingerprint = str(context.get("source_fingerprint_sha256") or "")
        if fingerprint:
            request["observed_source_fingerprint_sha256s"] = [fingerprint]
        memory.setdefault("retry_requests", []).append(request)
        return request

    def record_backtrack_request(
        self,
        *,
        stage: str,
        target_stage: str,
        reason: str,
        missing_or_invalid_contracts: list[str] | None = None,
        evidence: list[str] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        memory = self.state.setdefault("memory", {})
        context = context if isinstance(context, dict) else {}
        request_key = _backtrack_request_key(
            stage=stage,
            target_stage=target_stage,
            reason=reason,
            missing_or_invalid_contracts=missing_or_invalid_contracts,
            evidence=evidence,
            context=context,
        )
        matching = [
            row
            for row in memory.get("backtrack_requests", [])
            if isinstance(row, dict)
            and row.get("status") == "open"
            and _backtrack_request_key(
                stage=row.get("stage"),
                target_stage=row.get("target_stage"),
                reason=row.get("reason"),
                missing_or_invalid_contracts=row.get(
                    "missing_or_invalid_contracts"
                ),
                evidence=row.get("evidence"),
                context=_context_from_memory_record(row),
            )
            == request_key
        ]
        if matching:
            primary = matching[0]
            for duplicate in matching[1:]:
                _merge_observation_metadata(primary, duplicate)
                duplicate["status"] = "closed"
                duplicate["closed_at"] = utc_now()
                duplicate["deduplicated_into"] = primary.get("id")
                duplicate["resolution_reason"] = (
                    "idempotent duplicate of an active backtrack request for the "
                    "same stage, scope, failed gates, and evidence"
                )
            _record_reobservation(primary, context=context)
            return primary
        request = {
            "id": next_memory_id(self.state, "backtrack_requests", "backtrack_request"),
            "timestamp": utc_now(),
            "stage": stage,
            "target_stage": target_stage,
            "reason": reason,
            "missing_or_invalid_contracts": list(missing_or_invalid_contracts or [])[:16],
            "evidence": list(evidence or [])[:16],
            **{
                key: value
                for key in (
                    "verification_scope",
                    "debug_layer",
                    "failed_gates",
                    "source_fingerprint_sha256",
                )
                for value in [(context or {}).get(key)]
                if value not in (None, "", [])
            },
            "status": "open",
            "observation_count": 1,
        }
        fingerprint = str(context.get("source_fingerprint_sha256") or "")
        if fingerprint:
            request["observed_source_fingerprint_sha256s"] = [fingerprint]
        memory.setdefault("backtrack_requests", []).append(request)
        return request

    def attach_evidence(
        self,
        checker: str,
        status: str,
        invariant: str,
        constraints: list[str],
        artifacts: list[str],
        log_path: str,
        transition_id: str | None = None,
        summary: str = "",
    ) -> dict[str, Any]:
        if status not in {"pass", "fail", "unknown"}:
            raise ValueError("evidence status must be pass, fail, or unknown")
        get_item(self.state, "invariants", invariant)
        for constraint_id in constraints:
            get_item(self.state, "constraints", constraint_id)
        for artifact_id in artifacts:
            get_item(self.state, "artifacts", artifact_id)

        evidence = {
            "id": next_id(self.state, "evidence", "evidence"),
            "timestamp": utc_now(),
            "checker": checker,
            "status": status,
            "invariant": invariant,
            "constraints": constraints,
            "artifacts": artifacts,
            "log_path": log_path,
            "summary": summary,
        }
        self.state["evidence"].append(evidence)

        invariant_item = get_item(self.state, "invariants", invariant)
        invariant_item["status"] = status
        invariant_item["latest_evidence"] = evidence["id"]

        if transition_id:
            transition = get_item(self.state, "transitions", transition_id)
            transition["evidence"].append(evidence["id"])
        return evidence

    def approve(self, transition_id: str, approver: str, decision: str, note: str = "") -> dict[str, Any]:
        if decision not in {"approved", "rejected"}:
            raise ValueError("approval decision must be approved or rejected")
        transition = get_item(self.state, "transitions", transition_id)
        approval = {
            "id": next_id(self.state, "approvals", "approval"),
            "timestamp": utc_now(),
            "transition_id": transition_id,
            "approver": approver,
            "decision": decision,
            "note": note,
        }
        self.state["approvals"].append(approval)
        transition["approval_id"] = approval["id"]
        if decision == "rejected":
            transition["status"] = "rejected"
        return approval

    def promote(self, transition_id: str) -> dict[str, Any]:
        transition = get_item(self.state, "transitions", transition_id)
        if transition.get("status") == "rejected":
            raise ValueError(f"transition is rejected: {transition_id}")
        if transition.get("repair_scope_class") == "forbidden":
            raise ValueError(f"transition contains forbidden repair scope: {transition_id}")
        if transition.get("approval_required"):
            approval_id = transition.get("approval_id")
            if not approval_id:
                raise ValueError(f"transition requires approval: {transition_id}")
            approval = get_item(self.state, "approvals", approval_id)
            if approval.get("decision") != "approved":
                raise ValueError(f"transition approval is not approved: {transition_id}")

        required = set(transition.get("required_checkers", []))
        evidence_ids = transition.get("evidence", [])
        evidence_checkers = {
            get_item(self.state, "evidence", evidence_id).get("checker")
            for evidence_id in evidence_ids
            if get_item(self.state, "evidence", evidence_id).get("status") == "pass"
        }
        missing = required - evidence_checkers
        if missing:
            raise ValueError(f"transition missing passing checker evidence: {sorted(missing)}")

        transition["status"] = "promoted"
        transition["promoted_at"] = utc_now()
        for artifact_id in transition.get("artifacts_generated", []):
            artifact = get_item(self.state, "artifacts", artifact_id)
            artifact["trust_status"] = "validated"
            artifact["validated_by_transition"] = transition_id
            memory = self.state.setdefault("memory", {})
            for barrier in memory.get("contamination_barriers", []):
                if not isinstance(barrier, dict):
                    continue
                if barrier.get("artifact_id") != artifact_id:
                    continue
                if barrier.get("status") in {"superseded", "closed"}:
                    continue
                barrier["status"] = "superseded"
                barrier["closed_at"] = utc_now()
                barrier["superseded_by_transition"] = transition_id
        return transition

    def reconcile_retry_and_barriers(
        self,
        transition_id: str,
        *,
        target_stage: str,
        superseded_artifacts: list[str],
        reason: str,
        retry_request_ids: list[str] | None = None,
        contamination_barrier_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        memory = self.state.setdefault("memory", {})
        artifact_set = set(superseded_artifacts)
        allowed_retry_ids = set(str(value) for value in retry_request_ids or [])
        allowed_barrier_ids = set(
            str(value) for value in contamination_barrier_ids or []
        )
        explicit_retry_selection = retry_request_ids is not None
        explicit_barrier_selection = contamination_barrier_ids is not None
        closed_retries: list[str] = []
        superseded_barriers: list[str] = []
        for request in memory.get("retry_requests", []):
            if not isinstance(request, dict) or request.get("status") != "open":
                continue
            if explicit_retry_selection:
                if str(request.get("id") or "") not in allowed_retry_ids:
                    continue
            else:
                blocked = set(request.get("blocked_artifacts", []))
                if request.get("target_stage") != target_stage and not (blocked & artifact_set):
                    continue
            request["status"] = "closed"
            request["closed_at"] = utc_now()
            request["resolved_by_transition"] = transition_id
            request["resolution_reason"] = reason
            closed_retries.append(str(request.get("id")))
        for barrier in memory.get("contamination_barriers", []):
            if not isinstance(barrier, dict) or barrier.get("status", "active") != "active":
                continue
            if explicit_barrier_selection:
                if str(barrier.get("id") or "") not in allowed_barrier_ids:
                    continue
            elif barrier.get("artifact_id") not in artifact_set:
                continue
            barrier["status"] = "superseded"
            barrier["closed_at"] = utc_now()
            barrier["superseded_by_transition"] = transition_id
            barrier["resolution_reason"] = reason
            superseded_barriers.append(str(barrier.get("id")))
        event = {
            "id": next_memory_id(self.state, "reconciliation_events", "reconciliation"),
            "timestamp": utc_now(),
            "transition_id": transition_id,
            "target_stage": target_stage,
            "superseded_artifacts": sorted(artifact_set),
            "closed_retry_requests": closed_retries,
            "superseded_contamination_barriers": superseded_barriers,
            "reason": reason,
        }
        memory.setdefault("reconciliation_events", []).append(event)
        return event

    def reject(self, transition_id: str, reason: str) -> dict[str, Any]:
        transition = get_item(self.state, "transitions", transition_id)
        transition["status"] = "rejected"
        transition["reject_reason"] = reason
        transition["rejected_at"] = utc_now()
        memory = self.state.setdefault("memory", {})
        for artifact_id in transition.get("artifacts_generated", []):
            artifact = get_item(self.state, "artifacts", artifact_id)
            artifact["freshness"] = "suspect"
            artifact["trust_status"] = "rejected_producer"
            artifact["rejection_reason"] = reason
            context = _context_from_memory_record(transition)
            barrier_key = _contamination_barrier_key(
                artifact_id=artifact_id,
                reason=reason,
                context=context,
            )
            matching = [
                row
                for row in memory.get("contamination_barriers", [])
                if isinstance(row, dict)
                and row.get("status", "active") == "active"
                and _contamination_barrier_key(
                    artifact_id=row.get("artifact_id"),
                    reason=row.get("reason"),
                    context=_context_from_memory_record(row),
                )
                == barrier_key
            ]
            if matching:
                primary = matching[0]
                for duplicate in matching[1:]:
                    _merge_observation_metadata(primary, duplicate)
                    duplicate["status"] = "superseded"
                    duplicate["superseded_at"] = utc_now()
                    duplicate["deduplicated_into"] = primary.get("id")
                    duplicate["resolution_reason"] = (
                        "idempotent duplicate of an active contamination barrier for "
                        "the same rejected artifact, scope, and failed gates"
                    )
                _record_reobservation(
                    primary,
                    context=context,
                    transition_id=transition_id,
                )
                continue
            barrier = {
                "id": next_memory_id(
                    self.state,
                    "contamination_barriers",
                    "contamination_barrier",
                ),
                "timestamp": utc_now(),
                "transition_id": transition_id,
                "artifact_id": artifact_id,
                "reason": reason,
                "status": "active",
                "observation_count": 1,
                "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
                **{
                    key: transition[key]
                    for key in (
                        "verification_scope",
                        "debug_layer",
                        "failed_gates",
                        "source_fingerprint_sha256",
                    )
                    if transition.get(key) not in (None, "", [])
                },
            }
            fingerprint = str(context.get("source_fingerprint_sha256") or "")
            if fingerprint:
                barrier["observed_source_fingerprint_sha256s"] = [fingerprint]
            barrier["observed_transition_ids"] = [transition_id]
            memory.setdefault("contamination_barriers", []).append(barrier)
        return transition

    def export_report(self) -> dict[str, Any]:
        return {
            "design_id": self.state.get("design_id"),
            "sacg_version": self.state.get("sacg_version"),
            "num_nodes": len(self.state.get("nodes", [])),
            "num_edges": len(self.state.get("edges", [])),
            "num_constraints": len(self.state.get("constraints", [])),
            "num_artifacts": len(self.state.get("artifacts", [])),
            "num_evidence": len(self.state.get("evidence", [])),
            "num_transitions": len(self.state.get("transitions", [])),
            "open_failures": [
                inv for inv in self.state.get("invariants", []) if inv.get("status") == "fail"
            ],
            "promoted_transitions": [
                t for t in self.state.get("transitions", []) if t.get("status") == "promoted"
            ],
        }


def init_state(path: Path, design_id: str) -> None:
    state = ensure_state_defaults({"design_id": design_id})
    write_json(path, state)


def load_store(path: Path) -> SACGStore:
    return SACGStore(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Minimal SACG runtime")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init")
    p_init.add_argument("path")
    p_init.add_argument("--design-id", default="unnamed_design")

    p_validate = sub.add_parser("validate")
    p_validate.add_argument("path")

    p_report = sub.add_parser("report")
    p_report.add_argument("path")

    args = parser.parse_args(argv)

    try:
        if args.cmd == "init":
            init_state(Path(args.path), args.design_id)
            return 0
        if args.cmd == "validate":
            store = load_store(Path(args.path))
            errors = store.validate()
            if errors:
                for error in errors:
                    print(error, file=sys.stderr)
                return 1
            print("SACG state OK")
            return 0
        if args.cmd == "report":
            store = load_store(Path(args.path))
            json.dump(store.export_report(), sys.stdout, indent=2, sort_keys=True)
            print()
            return 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
