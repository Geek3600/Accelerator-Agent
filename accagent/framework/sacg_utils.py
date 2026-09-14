"""Small helpers for SACG-transforming stages."""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def copy_state(src: Path, dst: Path) -> dict[str, Any]:
    state = copy.deepcopy(read_json(src))
    write_json(dst, state)
    return state


def run_dir_from_state(path: Path) -> Path:
    return path.resolve().parents[1]


def safe_id(text: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_]+", "_", text).strip("_").lower()
    return value or "unnamed"


def by_id(items: list[dict[str, Any]], item_id: str) -> dict[str, Any]:
    for item in items:
        if item.get("id") == item_id:
            return item
    raise KeyError(item_id)


def upsert(items: list[dict[str, Any]], item: dict[str, Any]) -> None:
    item_id = item["id"]
    for index, existing in enumerate(items):
        if existing.get("id") == item_id:
            items[index] = item
            return
    items.append(item)


def constraint_facts(state: dict[str, Any], constraint_id: str) -> dict[str, Any]:
    return by_id(state.get("constraints", []), constraint_id).get("facts", {})


def artifact_path(state: dict[str, Any], artifact_id: str) -> Path:
    return Path(by_id(state.get("artifacts", []), artifact_id)["path"])


def artifact_producer_status(state: dict[str, Any], artifact_id: str) -> str | None:
    artifact = by_id(state.get("artifacts", []), artifact_id)
    producer = artifact.get("producer_transition")
    if not producer:
        return None
    for transition in state.get("transitions", []):
        if transition.get("id") == producer:
            return str(transition.get("status"))
    return None


def artifact_trust_status(state: dict[str, Any], artifact_id: str) -> str:
    artifact = by_id(state.get("artifacts", []), artifact_id)
    return str(artifact.get("trust_status") or "unknown")


def require_promoted_artifacts(state: dict[str, Any], artifact_ids: list[str]) -> list[str]:
    errors: list[str] = []
    for artifact_id in artifact_ids:
        try:
            producer_status = artifact_producer_status(state, artifact_id)
            trust_status = artifact_trust_status(state, artifact_id)
        except KeyError:
            errors.append(f"{artifact_id} is missing")
            continue
        if producer_status and producer_status != "promoted":
            errors.append(f"{artifact_id} producer transition is {producer_status}, expected promoted")
        if trust_status == "rejected_producer":
            errors.append(f"{artifact_id} is marked rejected_producer and cannot be used as validated downstream input")
    return errors


def sacg_memory_summary(state: dict[str, Any], limit: int = 8) -> dict[str, Any]:
    memory = state.get("memory", {}) if isinstance(state.get("memory"), dict) else {}

    def tail(name: str) -> list[dict[str, Any]]:
        values = memory.get(name, []) if isinstance(memory.get(name), list) else []
        return [item for item in values[-limit:] if isinstance(item, dict)]

    return {
        "schema_version": memory.get("schema_version", "spatialaccagent.sacg_memory.v0"),
        "recent_stage_outcomes": tail("stage_outcomes"),
        "recent_failure_lessons": tail("failure_lessons"),
        "open_retry_requests": [item for item in tail("retry_requests") if item.get("status") == "open"],
        "open_backtrack_requests": [item for item in tail("backtrack_requests") if item.get("status") == "open"],
        "active_contamination_barriers": [
            item
            for item in tail("contamination_barriers")
            if item.get("status", "active") == "active"
        ],
        "recent_contamination_barriers": tail("contamination_barriers"),
        "policy": "SACG memory is the long-context design memory for preserving goals, failures, lessons, retry needs, and cross-layer consistency across stages.",
    }


def scoped_sacg_memory_summary(
    state: dict[str, Any],
    *,
    verification_scope: str = "",
    debug_layer: str = "",
    limit: int = 8,
) -> dict[str, Any]:
    """Project only hierarchy-bound history into an operational stage prompt."""

    if not verification_scope and not debug_layer:
        return sacg_memory_summary(state, limit=limit)
    memory = state.get("memory", {}) if isinstance(state.get("memory"), dict) else {}

    def values(name: str) -> list[dict[str, Any]]:
        rows = memory.get(name, []) if isinstance(memory.get(name), list) else []
        return [row for row in rows if isinstance(row, dict)]

    def matches(row: dict[str, Any]) -> bool:
        if verification_scope and row.get("verification_scope") != verification_scope:
            return False
        if debug_layer and row.get("debug_layer") != debug_layer:
            return False
        return True

    def candidates(name: str, *, status: str | None = None) -> list[dict[str, Any]]:
        rows = values(name)
        if status is not None:
            rows = [row for row in rows if row.get("status") == status]
        return rows

    def selected(name: str, *, status: str | None = None) -> list[dict[str, Any]]:
        return [row for row in candidates(name, status=status) if matches(row)][-limit:]

    selected_outcomes = selected("stage_outcomes")
    selected_lessons = selected("failure_lessons")
    selected_retries = selected("retry_requests", status="open")
    selected_backtracks = selected("backtrack_requests", status="open")
    barrier_candidates = [
        row
        for row in values("contamination_barriers")
        if row.get("status", "active") == "active"
    ]
    selected_barriers = [row for row in barrier_candidates if matches(row)][-limit:]
    return {
        "schema_version": "spatialaccagent.scoped_sacg_memory.v1",
        "source_schema_version": memory.get(
            "schema_version", "spatialaccagent.sacg_memory.v0"
        ),
        "verification_scope": verification_scope or None,
        "debug_layer": debug_layer or None,
        "recent_stage_outcomes": selected_outcomes,
        "recent_failure_lessons": selected_lessons,
        "open_retry_requests": selected_retries,
        "open_backtrack_requests": selected_backtracks,
        "active_contamination_barriers": selected_barriers,
        "omitted_unscoped_cross_layer_or_limit_counts": {
            "stage_outcomes": len(values("stage_outcomes")) - len(selected_outcomes),
            "failure_lessons": len(values("failure_lessons")) - len(selected_lessons),
            "retry_requests": len(candidates("retry_requests", status="open"))
            - len(selected_retries),
            "backtrack_requests": len(candidates("backtrack_requests", status="open"))
            - len(selected_backtracks),
            "contamination_barriers": len(barrier_candidates) - len(selected_barriers),
        },
        "policy": (
            "Only hierarchy-bound records matching this prompt scope are operational context. "
            "Omitted records remain persisted recovery history; sacg_memory_truth separately "
            "carries the complete authoritative current blocker set."
        ),
    }


_VERIFICATION_SCOPE_BY_DEBUG_LAYER = {
    "operator_leaf_modules": "operator_leaf_closure",
    "single_transformer_layer_kernel": "single_layer_closure",
    "board_axi_ddr_wrapped_system": "board_axi_ddr_closure",
}
_DEBUG_LAYER_BY_VERIFICATION_SCOPE = {
    value: key for key, value in _VERIFICATION_SCOPE_BY_DEBUG_LAYER.items()
}
_VERIFICATION_SCOPE_ALIASES = {
    "operator_leaf": "operator_leaf_closure",
    "leaf": "operator_leaf_closure",
    "single_layer": "single_layer_closure",
    "stage7_single_layer": "single_layer_closure",
    "board_axi_ddr": "board_axi_ddr_closure",
    "stage7_board_axi_ddr": "board_axi_ddr_closure",
    "functional": "board_axi_ddr_closure",
    "functional_sim": "board_axi_ddr_closure",
    "stage7_functional": "board_axi_ddr_closure",
}


def hierarchy_memory_context(
    *,
    verification_scope: Any = "",
    debug_layer: Any = "",
    failed_gates: Any = None,
    source_fingerprint_sha256: Any = "",
) -> dict[str, Any]:
    """Build a canonical hierarchy binding for persistent SACG experience."""

    scope = str(verification_scope or "").strip().lower()
    scope = _VERIFICATION_SCOPE_ALIASES.get(scope, scope)
    layer = str(debug_layer or "").strip()
    if not scope:
        scope = _VERIFICATION_SCOPE_BY_DEBUG_LAYER.get(layer, "")
    if not layer:
        layer = _DEBUG_LAYER_BY_VERIFICATION_SCOPE.get(scope, "")
    gate_names: list[str] = []
    for row in failed_gates if isinstance(failed_gates, list) else []:
        if isinstance(row, dict):
            if row.get("status") not in (None, "fail"):
                continue
            name = row.get("name") or row.get("checker") or row.get("id")
        else:
            name = row
        text = str(name or "").strip()
        if text and text not in gate_names:
            gate_names.append(text)
    fingerprint = str(source_fingerprint_sha256 or "").strip().lower()
    return {
        key: value
        for key, value in {
            "verification_scope": scope,
            "debug_layer": layer,
            "failed_gates": gate_names,
            "source_fingerprint_sha256": fingerprint
            if re.fullmatch(r"[0-9a-f]{64}", fingerprint)
            else "",
        }.items()
        if value not in (None, "", [])
    }


_HIERARCHICAL_PROMOTION_LEVELS = (
    (
        "operator_leaf_closure",
        "operator_leaf_modules",
        "artifact.stage7.operator_leaf_promotion_certificate",
        "operator_leaf_functional",
    ),
    (
        "single_layer_closure",
        "single_transformer_layer_kernel",
        "artifact.stage7.single_layer_promotion_certificate",
        "single_layer_functional",
    ),
    (
        "board_axi_ddr_closure",
        "board_axi_ddr_wrapped_system",
        "artifact.stage7.board_axi_ddr_promotion_certificate",
        "axi_ddr_functional",
    ),
)


def _file_sha256_if_current(path: Path, expected: Any = "") -> str | None:
    if not path.is_file():
        return None
    import hashlib

    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError:
        return None
    actual = digest.hexdigest()
    expected_text = str(expected or "").lower()
    return actual if not expected_text or actual == expected_text else None


def _resolved_hierarchy_learning_record(path: Path, expected_sha256: Any) -> dict[str, Any] | None:
    """Project a hash-bound resolved-evidence lesson without importing raw logs."""

    actual = _file_sha256_if_current(path, expected_sha256)
    if actual is None or path.suffix.lower() != ".json":
        return None
    try:
        document = read_json(path)
    except Exception:
        return None
    if document.get("status") != "pass":
        return None
    schema = str(document.get("schema_version") or "")
    record: dict[str, Any] | None = None
    if schema == "spatialaccagent.historical_semantic_execution_recovery.v1":
        closure = (
            document.get("static_source_closure", {})
            if isinstance(document.get("static_source_closure"), dict)
            else {}
        )
        record = {
            "kind": "historical_semantic_execution_recovery",
            "stage_id": document.get("stage_id"),
            "reachable_source_set_sha256": closure.get("reachable_source_set_sha256"),
            "removed_historical_source_count": len(
                document.get("removed_historical_sources", [])
                if isinstance(document.get("removed_historical_sources"), list)
                else []
            ),
            "lesson": (
                "A completed real-tool execution may be reused only through this hash-bound "
                "reachable-source proof; removed historical-only compile units are not a current RTL failure."
            ),
        }
    elif schema == "spatialaccagent.operator_leaf_certificate_continuity.v1":
        record = {
            "kind": "lower_scope_certificate_continuity",
            "live_operator_leaf_file_count": len(
                document.get("live_operator_leaf_files", [])
                if isinstance(document.get("live_operator_leaf_files"), list)
                else []
            ),
            "lesson": (
                "A higher-scope binding update was proven not to alter certified leaf evidence; "
                "do not replay or reopen leaf operators without a current contradictory trace."
            ),
        }
    elif schema == "spatialaccagent.lower_layer_certificate_scaffold_bridge.v1":
        record = {
            "kind": "lower_layer_certificate_scaffold_bridge",
            "bridge_fingerprint_sha256": document.get("bridge_fingerprint_sha256"),
            "lesson": (
                "The connected-layer scaffold has a live lower-layer certificate bridge; "
                "do not regenerate certified leaf testbenches merely to satisfy a legacy scaffold checker."
            ),
        }
    if record is None:
        return None
    return {
        **record,
        "path": str(path.resolve()),
        "file_sha256": actual,
    }


def _pipeline_overlap_learning_record(path: Path, expected_sha256: Any) -> dict[str, Any] | None:
    """Project connected-kernel timing facts from a live certificate binding.

    The full trace can be large and includes case-specific cycle numbers and
    stage identifiers.  A board-level reasoning agent needs the verified
    execution semantics, not an unbounded trace dump or an accidental timing
    constant from an earlier workload.
    """

    actual = _file_sha256_if_current(path, expected_sha256)
    if actual is None or path.suffix.lower() != ".json":
        return None
    try:
        document = read_json(path)
    except Exception:
        return None
    evidence = document.get("pipeline_overlap_evidence")
    if not isinstance(evidence, dict):
        return None
    if evidence.get("status") != "pass" or document.get("status") != "pass":
        return None

    boundary_rows = [
        row for row in evidence.get("boundary_order_evidence", []) if isinstance(row, dict)
    ]
    required_direct_rows = [
        row
        for row in evidence.get("dependency_overlap_evidence", [])
        if isinstance(row, dict)
        and row.get("relationship") == "direct_dataflow"
        and (
            row.get("required_for_acceptance") is True
            or row.get("overlap_requirement") == "required"
        )
    ]
    return {
        "kind": "connected_kernel_pipeline_timing",
        "path": str(path.resolve()),
        "file_sha256": actual,
        "evidence_schema_version": evidence.get("schema_version"),
        "pipeline_semantics": evidence.get("pipeline_semantics"),
        "accepted_trace_record_count": evidence.get("accepted_trace_record_count"),
        "trace_record_count": evidence.get("trace_record_count"),
        "planned_stage_count": evidence.get("planned_stage_count"),
        "maximum_concurrent_stage_count": evidence.get("maximum_concurrent_stage_count"),
        "all_planned_stages_concurrent_observed": evidence.get(
            "all_planned_stages_concurrent_observed"
        ),
        "all_planned_stages_participate_in_required_overlap": evidence.get(
            "all_planned_stages_participate_in_required_overlap"
        ),
        "all_planned_stages_same_cycle_concurrency_required": evidence.get(
            "all_planned_stages_same_cycle_concurrency_required"
        ),
        "required_dependency_overlap_complete": evidence.get(
            "required_dependency_overlap_complete"
        ),
        "stage_turnover_gaps_are_diagnostic": evidence.get(
            "stage_turnover_gaps_are_diagnostic"
        ),
        "boundary_order_summary": {
            "boundary_count": len(boundary_rows),
            "complete_count": sum(row.get("complete") is True for row in boundary_rows),
            "all_first_token_order_preserved": bool(boundary_rows)
            and all(row.get("token_first_transfer_order_preserved") is True for row in boundary_rows),
            "all_last_token_order_preserved": bool(boundary_rows)
            and all(row.get("token_last_transfer_order_preserved") is True for row in boundary_rows),
        },
        "required_direct_dependency_overlap_summary": {
            "boundary_count": len(required_direct_rows),
            "all_different_token_overlap_observed": bool(required_direct_rows)
            and all(
                row.get("different_token_overlap_observed") is True
                for row in required_direct_rows
            ),
        },
        "trace_sha256": evidence.get("trace_sha256"),
        "contract_sha256": evidence.get("contract_sha256"),
        "lesson": (
            "The connected kernel is an elastic, variable-latency token pipeline. "
            "Preserve verified boundary order and required adjacent-stage cross-token overlap; "
            "do not diagnose unequal stage durations as a failure merely because all stages do not "
            "start or finish on the same cycle."
        ),
    }


def hierarchical_learning_context(
    state: dict[str, Any],
    *,
    verification_scope: Any = "",
    debug_layer: Any = "",
) -> dict[str, Any]:
    """Return compact, live-validated lower-layer experience for an LLM prompt.

    This is deliberately evidence-first rather than a chronological chat summary.
    It gives a higher-layer agent only facts that are still validated by the
    promotion contract, plus compact lessons from content-addressed recovery
    proofs.  Historical logs and closed failures remain on disk but cannot bias
    a new board-level root-cause decision.
    """

    context = hierarchy_memory_context(
        verification_scope=verification_scope,
        debug_layer=debug_layer,
    )
    scope = str(context.get("verification_scope") or "")
    target_index = next(
        (
            index
            for index, (known_scope, _, _, _) in enumerate(_HIERARCHICAL_PROMOTION_LEVELS)
            if known_scope == scope
        ),
        0,
    )
    artifacts = {
        str(item.get("id")): item
        for item in state.get("artifacts", [])
        if isinstance(item, dict) and item.get("id")
    }
    certificates: list[dict[str, Any]] = []
    lessons: list[dict[str, Any]] = []
    seen_lessons: set[str] = set()
    timing_knowledge: list[dict[str, Any]] = []
    seen_timing_identities: set[tuple[str, str, str]] = set()
    for index, (certificate_scope, certificate_layer, artifact_id, level_id) in enumerate(
        _HIERARCHICAL_PROMOTION_LEVELS
    ):
        if index >= target_index:
            break
        artifact = artifacts.get(artifact_id, {})
        try:
            producer_status = artifact_producer_status(state, artifact_id)
        except KeyError:
            continue
        if artifact.get("trust_status") == "rejected_producer" or producer_status != "promoted":
            continue
        path = Path(str(artifact.get("path") or ""))
        if not path.is_file():
            continue
        try:
            certificate = read_json(path)
        except Exception:
            continue
        required_gates = [
            str(row.get("name"))
            for row in certificate.get("required_gates", [])
            if isinstance(row, dict) and row.get("name")
        ]
        if certificate.get("status") != "pass" or not required_gates:
            continue
        try:
            from accagent.framework.verification_evidence_contract import certificate_contract_errors

            if certificate_contract_errors(certificate, level_id, required_gates):
                continue
        except Exception:
            continue
        binding = (
            certificate.get("evidence_binding", {})
            if isinstance(certificate.get("evidence_binding"), dict)
            else {}
        )
        binding_rows = [
            row for row in binding.get("file_bindings", []) if isinstance(row, dict)
        ]
        role_counts: dict[str, int] = {}
        for row in binding_rows:
            role = str(row.get("role") or "unknown")
            role_counts[role] = role_counts.get(role, 0) + 1
            timing = _pipeline_overlap_learning_record(
                Path(str(row.get("path") or "")), row.get("sha256")
            )
            timing_identity = (
                str(timing.get("trace_sha256") or ""),
                str(timing.get("contract_sha256") or ""),
                str(timing.get("pipeline_semantics") or ""),
            ) if timing else ("", "", "")
            if timing and timing_identity not in seen_timing_identities:
                seen_timing_identities.add(timing_identity)
                timing_knowledge.append(timing)
            lesson = _resolved_hierarchy_learning_record(
                Path(str(row.get("path") or "")), row.get("sha256")
            )
            if lesson and lesson["path"] not in seen_lessons:
                seen_lessons.add(lesson["path"])
                lessons.append(lesson)
        derivation = (
            certificate.get("certificate_derivation", {})
            if isinstance(certificate.get("certificate_derivation"), dict)
            else {}
        )
        continuity = (
            derivation.get("continuity_proof", {})
            if isinstance(derivation.get("continuity_proof"), dict)
            else {}
        )
        if continuity.get("path"):
            lesson = _resolved_hierarchy_learning_record(
                Path(str(continuity.get("path"))), continuity.get("sha256")
            )
            if lesson and lesson["path"] not in seen_lessons:
                seen_lessons.add(lesson["path"])
                lessons.append(lesson)
        semantics = (
            certificate.get("evidence_semantics", {})
            if isinstance(certificate.get("evidence_semantics"), dict)
            else {}
        )
        certificates.append(
            {
                "scope": certificate_scope,
                "debug_layer": certificate_layer,
                "artifact_id": artifact_id,
                "path": str(path.resolve()),
                "file_sha256": _file_sha256_if_current(path),
                "level_id": level_id,
                "required_gates": required_gates,
                "evidence_binding_sha256": binding.get("binding_sha256"),
                "evidence_binding_file_count": len(binding_rows),
                "evidence_binding_roles": role_counts,
                "claim": semantics.get("claim"),
                "does_not_claim": semantics.get("does_not_claim", []),
                "derivation_kind": derivation.get("kind"),
            }
        )
    board_debug_policy = {}
    if scope == "board_axi_ddr_closure":
        board_debug_policy = {
            "accepted_input_handshake_required_before_kernel_lifecycle_start": True,
            "independent_prefetch_or_axi_progress_is_not_output_frontier_progress": True,
            "current_output_or_lifecycle_frontier_evidence_required_for_board_liveness_claim": True,
            "frontier_stall_is_localization_evidence_not_a_root_cause_or_pass_claim": True,
            "repeat_repair_class_requires_fresh_intervention_response_evidence": True,
        }
    return {
        "schema_version": "spatialaccagent.hierarchical_learning_context.v1",
        "status": "pass" if certificates else "no_validated_lower_layer_evidence",
        "status_bar_contract": {
            "maintainer": "framework_deterministic_hash_bound_projection",
            "not_an_llm_generated_history_summary": True,
            "raw_evidence_remains_retrievable_by_path_and_sha256": True,
            "covers_only_live_validated_lower_layer_certificates": True,
            "does_not_replace_current_scope_tool_results": True,
        },
        "verification_scope": scope or None,
        "debug_layer": context.get("debug_layer"),
        "validated_lower_layer_certificates": certificates,
        "resolved_evidence_lessons": lessons[:8],
        "kernel_timing_knowledge": timing_knowledge[:4],
        "decision_policy": {
            "use_only_live_validated_lower_layer_evidence": True,
            "do_not_repeat_certified_lower_layer_tools_or_prompt_analysis": True,
            "lower_layer_reopen_requires_current_trace_named_contradiction": True,
            "resolved_artifact_identity_lessons_are_not_rtl_failures": True,
            "lower_layer_pass_does_not_claim_board_axi_ddr_or_backend_readiness": True,
            "current_scope_tools_and_exact_board_wrapper_remain_required": True,
            **board_debug_policy,
        },
    }


def sacg_memory_truth(state: dict[str, Any], limit: int = 32) -> dict[str, Any]:
    """Return the current SACG memory blockers as machine-checkable facts."""

    memory = state.get("memory", {}) if isinstance(state.get("memory"), dict) else {}

    def items(name: str) -> list[dict[str, Any]]:
        values = memory.get(name, []) if isinstance(memory.get(name), list) else []
        return [item for item in values if isinstance(item, dict)]

    def capped(values: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return values[-limit:]

    active_barriers = [
        item for item in items("contamination_barriers") if item.get("status", "active") == "active"
    ]
    open_retries = [item for item in items("retry_requests") if item.get("status") == "open"]
    open_backtracks = [item for item in items("backtrack_requests") if item.get("status") == "open"]
    return {
        "schema_version": "spatialaccagent.sacg_memory_truth.v0",
        "truth_source": "source_sacg_state.memory",
        "active_contamination_barrier_count": len(active_barriers),
        "active_contamination_barriers": capped(active_barriers),
        "active_contamination_barriers_truncated": len(active_barriers) > limit,
        "open_retry_request_count": len(open_retries),
        "open_retry_requests": capped(open_retries),
        "open_retry_requests_truncated": len(open_retries) > limit,
        "open_backtrack_request_count": len(open_backtracks),
        "open_backtrack_requests": capped(open_backtracks),
        "open_backtrack_requests_truncated": len(open_backtracks) > limit,
        "policy": (
            "Only active_contamination_barriers and open retry/backtrack requests in this object are "
            "current SACG-memory blockers. Historical, closed, superseded, or rejected records are "
            "recovery evidence only and must not be treated as active blockers."
        ),
    }


def scoped_sacg_memory_truth(
    state: dict[str, Any],
    *,
    verification_scope: str = "",
    debug_layer: str = "",
    limit: int = 32,
) -> dict[str, Any]:
    """Return authoritative blockers owned by one hierarchy repair scope."""

    if not verification_scope and not debug_layer:
        return sacg_memory_truth(state, limit=limit)
    memory = state.get("memory", {}) if isinstance(state.get("memory"), dict) else {}

    def values(name: str) -> list[dict[str, Any]]:
        rows = memory.get(name, []) if isinstance(memory.get(name), list) else []
        return [row for row in rows if isinstance(row, dict)]

    def matches(row: dict[str, Any]) -> bool:
        return bool(
            (not verification_scope or row.get("verification_scope") == verification_scope)
            and (not debug_layer or row.get("debug_layer") == debug_layer)
        )

    global_barriers = [
        row
        for row in values("contamination_barriers")
        if row.get("status", "active") == "active"
    ]
    global_retries = [
        row for row in values("retry_requests") if row.get("status") == "open"
    ]
    global_backtracks = [
        row for row in values("backtrack_requests") if row.get("status") == "open"
    ]
    barriers = [row for row in global_barriers if matches(row)]
    retries = [row for row in global_retries if matches(row)]
    backtracks = [row for row in global_backtracks if matches(row)]
    return {
        "schema_version": "spatialaccagent.scoped_sacg_memory_truth.v1",
        "truth_source": "source_sacg_state.memory",
        "verification_scope": verification_scope or None,
        "debug_layer": debug_layer or None,
        "active_contamination_barrier_count": len(barriers),
        "active_contamination_barriers": barriers[-limit:],
        "active_contamination_barriers_truncated": len(barriers) > limit,
        "open_retry_request_count": len(retries),
        "open_retry_requests": retries[-limit:],
        "open_retry_requests_truncated": len(retries) > limit,
        "open_backtrack_request_count": len(backtracks),
        "open_backtrack_requests": backtracks[-limit:],
        "open_backtrack_requests_truncated": len(backtracks) > limit,
        "global_persisted_blocker_counts": {
            "active_contamination_barriers": len(global_barriers),
            "open_retry_requests": len(global_retries),
            "open_backtrack_requests": len(global_backtracks),
        },
        "omitted_unscoped_or_cross_layer_blocker_counts": {
            "active_contamination_barriers": len(global_barriers) - len(barriers),
            "open_retry_requests": len(global_retries) - len(retries),
            "open_backtrack_requests": len(global_backtracks) - len(backtracks),
        },
        "policy": (
            "This is the authoritative current blocker set for the named hierarchy scope. "
            "Unscoped and cross-layer blockers remain persisted in SACG and are enforced by "
            "their owning layer or downstream promotion gates, but they are not executable "
            "blockers for this repair prompt."
        ),
    }


def stage_status_allows_promotion(status: Any) -> bool:
    text = str(status or "").strip().lower()
    if not text:
        return False
    rejected_terms = (
        "blocked",
        "incomplete",
        "llm_error",
        "fallback",
        "retry_required",
        "failed",
        "failure",
        "error",
        "conditional_approval",
    )
    if any(term in text for term in rejected_terms):
        return False
    accepted_exact = {"ready", "pass", "passed", "approved", "complete", "completed"}
    accepted_prefixes = (
        "ready_",
        "ready-with",
        "pass_",
        "passed_",
        "approved_",
        "complete_",
        "completed_",
        "conditional_ready",
        "conditional_pass",
    )
    return text in accepted_exact or text.startswith(accepted_prefixes)


def status_claims_inactive_sacg_memory_blocker(status: Any, memory_truth: dict[str, Any] | None) -> bool:
    """Detect a non-promoting status that cites only inactive SACG-memory blocker classes."""

    text = str(status or "").strip().lower()
    if not text or stage_status_allows_promotion(text):
        return False
    if not any(term in text for term in ("block", "retry_required", "backtrack_required", "stop")):
        return False
    truth = memory_truth or {}
    claimed_counts: list[str] = []
    if any(term in text for term in ("contamination", "barrier", "quarantine")):
        claimed_counts.append("active_contamination_barrier_count")
    if "retry" in text:
        claimed_counts.append("open_retry_request_count")
    if "backtrack" in text:
        claimed_counts.append("open_backtrack_request_count")
    if not claimed_counts:
        return False
    for count_key in claimed_counts:
        try:
            count = int(truth.get(count_key, 0) or 0)
        except (TypeError, ValueError):
            return False
        if count > 0:
            return False
    return True


def add_constraint(
    state: dict[str, Any],
    constraint_id: str,
    constraint_type: str,
    nodes: list[str],
    edges: list[str],
    artifacts: list[str],
    facts: dict[str, Any],
) -> None:
    upsert(
        state.setdefault("constraints", []),
        {
            "id": constraint_id,
            "type": constraint_type,
            "nodes": nodes,
            "edges": edges,
            "artifacts": artifacts,
            "facts": facts,
        },
    )


def add_node(
    state: dict[str, Any],
    node_id: str,
    node_type: str,
    name: str,
    constraints: list[str],
    artifacts: list[str],
    facts: dict[str, Any] | None = None,
) -> None:
    node = {
        "id": node_id,
        "type": node_type,
        "name": name,
        "constraints": constraints,
        "artifacts": artifacts,
    }
    if facts is not None:
        node["facts"] = facts
    upsert(state.setdefault("nodes", []), node)


def add_edge(
    state: dict[str, Any],
    edge_id: str,
    edge_type: str,
    src: str,
    dst: str,
    constraints: list[str],
    artifacts: list[str],
    facts: dict[str, Any] | None = None,
) -> None:
    edge = {
        "id": edge_id,
        "type": edge_type,
        "src": src,
        "dst": dst,
        "constraints": constraints,
        "artifacts": artifacts,
    }
    if facts is not None:
        edge["facts"] = facts
    upsert(state.setdefault("edges", []), edge)


def add_invariant(
    state: dict[str, Any],
    invariant_id: str,
    checker: str,
    constraints: list[str],
    status: str = "unknown",
) -> None:
    upsert(
        state.setdefault("invariants", []),
        {
            "id": invariant_id,
            "checker": checker,
            "constraints": constraints,
            "status": status,
            "latest_evidence": None,
        },
    )
