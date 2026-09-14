"""Evidence contract for a board trace that reopens a certified lower layer."""

from __future__ import annotations

import copy
import hashlib
from pathlib import Path
from typing import Any


BOARD_TO_LOWER_LAYER_CONTRADICTION_SCHEMA_VERSION = (
    "spatialaccagent.board_to_lower_layer_contradiction_evidence.v1"
)


def _is_sha256(value: Any) -> bool:
    text = str(value or "").lower()
    return len(text) == 64 and all(character in "0123456789abcdef" for character in text)


def _sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError:
        return None
    return digest.hexdigest()


def _runner_input_fingerprint(runner: dict[str, Any]) -> str:
    for value in (
        runner.get("input_fingerprint_sha256"),
        (runner.get("run") or {}).get("input_fingerprint_sha256")
        if isinstance(runner.get("run"), dict)
        else "",
    ):
        text = str(value or "").lower()
        if _is_sha256(text):
            return text
    return ""


def _read_json_object(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        import json

        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def _current_trace_binding(runner: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    summary = (
        runner.get("pipeline_boundary_observation_summary")
        if isinstance(runner.get("pipeline_boundary_observation_summary"), dict)
        else {}
    )
    trace_sha256 = str(summary.get("trace_sha256") or "").lower()
    trace_path = Path(str(summary.get("trace_path") or ""))
    if not _is_sha256(trace_sha256) or _sha256_file(trace_path) != trace_sha256:
        return "", {}
    return trace_sha256, {
        key: copy.deepcopy(summary.get(key))
        for key in (
            "status",
            "record_count",
            "required_boundary_count",
            "observed_boundary_count",
            "missing_boundary_ids",
            "incomplete_boundary_ids",
        )
        if key in summary
    }


def _current_lower_layer_certificate_sha256(runner: dict[str, Any]) -> str:
    executed_manifest_path = Path(str(runner.get("executed_manifest") or ""))
    executed_manifest = _read_json_object(executed_manifest_path)
    harness = (
        executed_manifest.get("multilayer_harness")
        if isinstance(executed_manifest, dict)
        and isinstance(executed_manifest.get("multilayer_harness"), dict)
        else {}
    )
    certificate = (
        harness.get("single_layer_promotion_certificate")
        if isinstance(harness.get("single_layer_promotion_certificate"), dict)
        else {}
    )
    certificate_sha256 = str(certificate.get("sha256") or "").lower()
    certificate_path = Path(str(certificate.get("path") or ""))
    if not _is_sha256(certificate_sha256):
        return ""
    return (
        certificate_sha256
        if _sha256_file(certificate_path) == certificate_sha256
        else ""
    )


def _latest_direct_kernel_observation(runner: dict[str, Any]) -> dict[str, Any]:
    progress = (
        runner.get("progress_event_summary")
        if isinstance(runner.get("progress_event_summary"), dict)
        else {}
    )
    live = runner.get("live_progress") if isinstance(runner.get("live_progress"), dict) else {}
    latest = live.get("latest") if isinstance(live.get("latest"), dict) else {}
    for container in (progress, latest):
        for field in ("latest_stall_snapshot", "last_complete_record"):
            row = container.get(field)
            if not isinstance(row, dict):
                continue
            inner_cone = row.get("connected_kernel_inner_cone_observation")
            internal_pipeline = row.get(
                "connected_kernel_internal_pipeline_observation"
            )
            if isinstance(inner_cone, dict) or isinstance(internal_pipeline, dict):
                return {
                    **(
                        inner_cone
                        if isinstance(inner_cone, dict)
                        else {}
                    ),
                    **(
                        internal_pipeline
                        if isinstance(internal_pipeline, dict)
                        else {}
                    ),
                }
    return {}


def _first_observed_stopped_boundary(observation: dict[str, Any]) -> str:
    candidates: list[str] = []
    for field, value in observation.items():
        if not field.endswith("_input_accepted_count") or not isinstance(value, int):
            continue
        if value <= 0:
            continue
        prefix = field[: -len("_input_accepted_count")]
        output_count = observation.get(f"{prefix}_output_accepted_count")
        output_ready = observation.get(f"{prefix}_output_ready")
        if output_count == 0 and output_ready in {True, 1}:
            candidates.append(prefix)
    if not candidates:
        return ""
    return f"kernel.{sorted(candidates)[0]}.output"


def _candidate_from_current_runner_evidence(
    runner: dict[str, Any],
    *,
    target_debug_layer: str,
) -> dict[str, Any] | None:
    """Build a contradiction candidate from source-bound board observations.

    This only packages observed lifecycle and boundary facts. It does not infer
    a hardware root cause; SACG/CCTG and the repair Agent keep that role.
    """

    input_fingerprint_sha256 = _runner_input_fingerprint(runner)
    board_trace_sha256, trace_summary = _current_trace_binding(runner)
    lower_layer_certificate_sha256 = _current_lower_layer_certificate_sha256(runner)
    observation = _latest_direct_kernel_observation(runner)
    if not (
        input_fingerprint_sha256
        and board_trace_sha256
        and lower_layer_certificate_sha256
        and observation
    ):
        return None
    ingress_count = observation.get("core_ingress_accepted_count")
    outer_ingress_count = observation.get("outer_input_accepted_count")
    kernel_start_accepted = (
        observation.get("start_edge_count", 0) > 0
        or observation.get("invocation_launched") in {True, 1}
    )
    kernel_ingress_complete = (
        isinstance(ingress_count, int)
        and ingress_count > 0
        and (
            observation.get("all_outer_ingress_accepted") is True
            or (
                isinstance(outer_ingress_count, int)
                and outer_ingress_count == ingress_count
            )
        )
    )
    kernel_egress_ready = observation.get("core_egress_ready") in {True, 1}
    named_boundary_id = _first_observed_stopped_boundary(observation)
    if not named_boundary_id:
        return None
    return {
        "schema_version": BOARD_TO_LOWER_LAYER_CONTRADICTION_SCHEMA_VERSION,
        "status": "proven",
        "target_debug_layer": target_debug_layer,
        "source_binding": {
            "input_fingerprint_sha256": input_fingerprint_sha256,
            "board_trace_sha256": board_trace_sha256,
            "lower_layer_certificate_sha256": lower_layer_certificate_sha256,
        },
        "direct_kernel_boundary_observations": {
            "kernel_start_accepted": kernel_start_accepted,
            "kernel_ingress_complete": kernel_ingress_complete,
            "kernel_egress_ready": kernel_egress_ready,
        },
        "causal_localization": {
            "earliest_causal_owner": target_debug_layer,
            "named_contract_boundary_id": named_boundary_id,
            "localization_basis": "first_direct_boundary_with_accepted_input_and_ready_zero_output",
        },
        "observation_context": {
            "pipeline_boundary_observation": trace_summary,
            "direct_kernel_observation_fields": {
                key: copy.deepcopy(observation.get(key))
                for key in (
                    "core_ingress_accepted_count",
                    "core_egress_accepted_count",
                    "core_egress_ready",
                    "core_egress_valid",
                )
                if key in observation
            },
        },
    }


def _candidate_from_runner(runner: dict[str, Any]) -> dict[str, Any] | None:
    run = runner.get("run") if isinstance(runner.get("run"), dict) else {}
    summary = (
        runner.get("progress_event_summary")
        if isinstance(runner.get("progress_event_summary"), dict)
        else {}
    )
    live = runner.get("live_progress") if isinstance(runner.get("live_progress"), dict) else {}
    latest = live.get("latest") if isinstance(live.get("latest"), dict) else {}
    for value in (
        runner.get("board_to_lower_layer_contradiction_evidence"),
        run.get("board_to_lower_layer_contradiction_evidence"),
        summary.get("board_to_lower_layer_contradiction_evidence"),
        latest.get("board_to_lower_layer_contradiction_evidence"),
    ):
        if isinstance(value, dict):
            return value
    return None


def _raw_contradiction_evidence(candidate: Any) -> dict[str, Any] | None:
    """Return the raw proof from either a proof or its validation envelope.

    Board runners produce raw proof records.  Downstream diagnosis artifacts
    may persist the result returned by ``validate_*`` instead, where the same
    proof is stored in ``evidence``.  Both forms describe one current board
    result and must follow the same hash-bound validation path.
    """

    if not isinstance(candidate, dict):
        return None
    embedded = candidate.get("evidence")
    if (
        candidate.get("status") == "proven"
        and isinstance(embedded, dict)
        and embedded.get("schema_version")
        == BOARD_TO_LOWER_LAYER_CONTRADICTION_SCHEMA_VERSION
    ):
        return embedded
    return candidate


def validate_board_to_lower_layer_contradiction(
    candidate: dict[str, Any] | None,
    *,
    target_debug_layer: str,
    runner_input_fingerprint_sha256: str = "",
    expected_lower_layer_certificate_path: Path | None = None,
) -> dict[str, Any]:
    """Validate the direct causal proof required to reopen a lower layer.

    A board-level missing output is deliberately insufficient.  The proof must
    bind a current trace, current lower-layer certificate, and direct core-side
    observations; otherwise the failure remains a board integration/localization
    problem even though it is still a real failure.
    """

    result = {
        "schema_version": BOARD_TO_LOWER_LAYER_CONTRADICTION_SCHEMA_VERSION,
        "status": "insufficient_evidence",
        "target_debug_layer": target_debug_layer,
        "required_observation_contract": {
            "current_trace_and_lower_certificate_hashes_required": True,
            "kernel_start_accepted_required": True,
            "kernel_ingress_complete_required": True,
            "kernel_egress_ready_required": True,
            "named_earliest_causal_boundary_required": True,
            "earliest_causal_owner_must_match_target_layer": True,
        },
        "validation_errors": [],
    }
    if not isinstance(candidate, dict):
        result["validation_errors"].append(
            "board trace contains no explicit lower-layer contradiction evidence"
        )
        return result
    if candidate.get("schema_version") != BOARD_TO_LOWER_LAYER_CONTRADICTION_SCHEMA_VERSION:
        result["validation_errors"].append(
            "board lower-layer contradiction evidence schema is not current"
        )
    if candidate.get("status") != "proven":
        result["validation_errors"].append(
            "board lower-layer contradiction evidence is not proven"
        )
    if str(candidate.get("target_debug_layer") or "") != target_debug_layer:
        result["validation_errors"].append(
            "board lower-layer contradiction targets a different hierarchy layer"
        )
    binding = (
        candidate.get("source_binding")
        if isinstance(candidate.get("source_binding"), dict)
        else {}
    )
    for field in ("board_trace_sha256", "lower_layer_certificate_sha256"):
        if not _is_sha256(binding.get(field)):
            result["validation_errors"].append(
                f"board lower-layer contradiction lacks {field}"
            )
    expected_input = str(runner_input_fingerprint_sha256 or "").lower()
    observed_input = str(binding.get("input_fingerprint_sha256") or "").lower()
    if expected_input:
        if observed_input != expected_input:
            result["validation_errors"].append(
                "board lower-layer contradiction does not bind the current runner input fingerprint"
            )
    elif not _is_sha256(observed_input):
        result["validation_errors"].append(
            "board lower-layer contradiction lacks input_fingerprint_sha256"
        )
    if expected_lower_layer_certificate_path is not None:
        current_certificate_sha = _sha256_file(expected_lower_layer_certificate_path)
        if current_certificate_sha is None:
            result["validation_errors"].append(
                "current lower-layer promotion certificate is unavailable for contradiction binding"
            )
        elif str(binding.get("lower_layer_certificate_sha256") or "").lower() != current_certificate_sha:
            result["validation_errors"].append(
                "board lower-layer contradiction does not bind the current lower-layer certificate"
            )
    observations = (
        candidate.get("direct_kernel_boundary_observations")
        if isinstance(candidate.get("direct_kernel_boundary_observations"), dict)
        else {}
    )
    for field in (
        "kernel_start_accepted",
        "kernel_ingress_complete",
        "kernel_egress_ready",
    ):
        if observations.get(field) is not True:
            result["validation_errors"].append(
                f"board lower-layer contradiction lacks direct observation {field}"
            )
    localization = (
        candidate.get("causal_localization")
        if isinstance(candidate.get("causal_localization"), dict)
        else {}
    )
    if str(localization.get("earliest_causal_owner") or "") != target_debug_layer:
        result["validation_errors"].append(
            "board lower-layer contradiction does not localize the earliest causal owner to the target layer"
        )
    if not str(localization.get("named_contract_boundary_id") or "").strip():
        result["validation_errors"].append(
            "board lower-layer contradiction lacks a named causal contract boundary"
        )
    if result["validation_errors"]:
        return result
    return {
        **result,
        "status": "proven",
        "evidence": copy.deepcopy(candidate),
    }


def board_to_lower_layer_contradiction_from_runner(
    runner: dict[str, Any],
    *,
    target_debug_layer: str,
) -> dict[str, Any]:
    candidate = _candidate_from_runner(runner)
    if not isinstance(candidate, dict) or candidate.get("status") != "proven":
        candidate = _candidate_from_current_runner_evidence(
            runner,
            target_debug_layer=target_debug_layer,
        )
    return validate_board_to_lower_layer_contradiction(
        candidate,
        target_debug_layer=target_debug_layer,
        runner_input_fingerprint_sha256=_runner_input_fingerprint(runner),
    )


def board_to_lower_layer_contradiction_from_diagnosis(
    diagnosis: dict[str, Any] | None,
    *,
    target_debug_layer: str,
    expected_lower_layer_certificate_path: Path | None = None,
) -> dict[str, Any]:
    if not isinstance(diagnosis, dict):
        return validate_board_to_lower_layer_contradiction(
            None,
            target_debug_layer=target_debug_layer,
            expected_lower_layer_certificate_path=expected_lower_layer_certificate_path,
        )
    failure_evidence = (
        diagnosis.get("failure_evidence")
        if isinstance(diagnosis.get("failure_evidence"), dict)
        else {}
    )
    handoff = (
        diagnosis.get("repair_handoff")
        if isinstance(diagnosis.get("repair_handoff"), dict)
        else {}
    )
    binding = (
        diagnosis.get("applicability_binding")
        if isinstance(diagnosis.get("applicability_binding"), dict)
        else {}
    )
    candidate = failure_evidence.get("board_to_lower_layer_contradiction_evidence")
    if not isinstance(candidate, dict):
        candidate = handoff.get("board_to_lower_layer_contradiction_evidence")
    candidate = _raw_contradiction_evidence(candidate)
    if not isinstance(candidate, dict) or candidate.get("status") != "proven":
        for source in binding.get("source_artifacts", []):
            if not isinstance(source, dict) or source.get("role") != "board_vcs_runner_report":
                continue
            runner_path = Path(str(source.get("path") or ""))
            runner_sha256 = str(source.get("sha256") or "").lower()
            if not _is_sha256(runner_sha256) or _sha256_file(runner_path) != runner_sha256:
                continue
            runner = _read_json_object(runner_path)
            if isinstance(runner, dict):
                candidate = _candidate_from_current_runner_evidence(
                    runner,
                    target_debug_layer=target_debug_layer,
                )
                if isinstance(candidate, dict):
                    break
    return validate_board_to_lower_layer_contradiction(
        candidate if isinstance(candidate, dict) else None,
        target_debug_layer=target_debug_layer,
        runner_input_fingerprint_sha256=str(binding.get("input_fingerprint_sha256") or ""),
        expected_lower_layer_certificate_path=expected_lower_layer_certificate_path,
    )
