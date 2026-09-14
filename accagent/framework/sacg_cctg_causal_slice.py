"""Project exact-board runtime evidence onto the SACG and CCTG debug frontier."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, deque
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "spatialaccagent.sacg_cctg_causal_slice.v1"
PROGRESS_SCHEMA_VERSION = "spatialaccagent.board_progress_event.v1"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "sha256": _sha256(path),
        "byte_count": path.stat().st_size if path.is_file() else None,
        "exists": path.is_file(),
    }


def _positive_int(value: Any) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool) and value > 0:
        return value
    return None


def _first_positive(*values: Any) -> int | None:
    for value in values:
        parsed = _positive_int(value)
        if parsed is not None:
            return parsed
    return None


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _iter_complete_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    """Stream newline-committed records so a large VCS trace is never loaded whole."""

    if not path.is_file():
        return
    with path.open("rb") as stream:
        for raw in stream:
            if not raw.endswith(b"\n"):
                continue
            try:
                value = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            if isinstance(value, dict):
                yield value


def _project_event(row: dict[str, Any]) -> dict[str, Any]:
    projection = {
        key: row.get(key)
        for key in (
            "sequence",
            "cycle",
            "event_kind",
            "phase",
            "progress_epoch",
            "scheduler_state",
            "layer",
            "token",
            "beat",
            "stage_or_boundary",
            "active_weight_bank",
            "preload_weight_bank",
            "activation_read_bank",
            "activation_write_bank",
            "prefetch_progress",
            "runtime_load_progress",
            "final_writeback_progress",
            "axi_read",
            "axi_write",
            "active_boundary_observation",
        )
        if key in row
    }
    return projection


def _event_position(row: dict[str, Any]) -> dict[str, Any]:
    return {
        key: row.get(key)
        for key in (
            "sequence",
            "cycle",
            "event_kind",
            "phase",
            "scheduler_state",
            "layer",
            "token",
            "beat",
            "stage_or_boundary",
        )
        if key in row
    }


def _phase_is(phase: str, *parts: str) -> bool:
    lowered = phase.lower()
    return all(part in lowered for part in parts)


def _event_summary(path: Path) -> dict[str, Any]:
    phases: Counter[str] = Counter()
    phase_first: dict[str, dict[str, Any]] = {}
    phase_last: dict[str, dict[str, Any]] = {}
    semantic_tail: deque[dict[str, Any]] = deque(maxlen=16)
    semantic_count = 0
    record_count = 0
    invalid_schema_count = 0
    latest: dict[str, Any] = {}
    token_events: dict[int, dict[str, set[int]]] = {}
    layer_flags: dict[int, Counter[str]] = {}
    completion_beats: list[int] = []

    for row in _iter_complete_jsonl(path):
        record_count += 1
        latest = row
        if row.get("schema_version") != PROGRESS_SCHEMA_VERSION:
            invalid_schema_count += 1
            continue
        phase = str(row.get("phase") or "")
        if phase:
            phases[phase] += 1
            phase_first.setdefault(phase, _event_position(row))
            phase_last[phase] = _event_position(row)
        if row.get("semantic_progress") is not True:
            continue
        semantic_count += 1
        semantic_tail.append(_project_event(row))
        layer = row.get("layer")
        layer = layer if isinstance(layer, int) and not isinstance(layer, bool) and layer >= 0 else 0
        token = row.get("token")
        token = token if isinstance(token, int) and not isinstance(token, bool) and token >= 0 else None
        per_layer = token_events.setdefault(
            layer,
            {
                "input_started": set(),
                "input_completed": set(),
                "output_started": set(),
                "output_completed": set(),
                "rearmed": set(),
            },
        )
        flags = layer_flags.setdefault(layer, Counter())
        lowered = phase.lower()
        if token is not None and _phase_is(lowered, "kernel", "input", "token", "start"):
            per_layer["input_started"].add(token)
        if token is not None and _phase_is(lowered, "kernel", "input", "token", "complete"):
            per_layer["input_completed"].add(token)
            beat = row.get("beat")
            if isinstance(beat, int) and not isinstance(beat, bool) and beat >= 0:
                completion_beats.append(beat)
        if token is not None and _phase_is(lowered, "kernel", "output", "token", "start"):
            per_layer["output_started"].add(token)
        if token is not None and _phase_is(lowered, "kernel", "output", "token", "complete"):
            per_layer["output_completed"].add(token)
            beat = row.get("beat")
            if isinstance(beat, int) and not isinstance(beat, bool) and beat >= 0:
                completion_beats.append(beat)
        if "token_rearm" in lowered:
            per_layer["rearmed"].add(token if token is not None else phases[phase])
        for name, parts in (
            ("runtime_load_start", ("runtime", "load", "start")),
            ("runtime_load_complete", ("runtime", "load", "complete")),
            ("weight_prefetch_start", ("weight", "prefetch", "start")),
            ("weight_prefetch_complete", ("weight", "prefetch", "complete")),
            ("weight_bank_switch", ("weight", "bank", "switch")),
            ("activation_bank_switch", ("activation", "bank", "switch")),
            ("layer_output_complete", ("layer", "output", "complete")),
            ("final_writeback_start", ("final", "writeback", "start")),
            ("final_writeback_complete", ("final", "writeback", "complete")),
        ):
            if _phase_is(lowered, *parts):
                flags[name] += 1
        if lowered == "kernel_start" or lowered.endswith(".kernel_start"):
            flags["kernel_start"] += 1

    compact_layers: dict[str, Any] = {}
    for layer in sorted(set(token_events) | set(layer_flags)):
        tokens = token_events.get(layer, {})
        flags = layer_flags.get(layer, Counter())
        compact_layers[str(layer)] = {
            **{key: len(values) for key, values in tokens.items()},
            **dict(flags),
        }
    return {
        "status": "ready" if record_count else "missing",
        "record_count": record_count,
        "invalid_schema_record_count": invalid_schema_count,
        "semantic_event_count": semantic_count,
        "phase_counts": dict(sorted(phases.items())),
        "phase_first_event": phase_first,
        "phase_last_event": phase_last,
        "semantic_event_tail": list(semantic_tail),
        "latest_event": _project_event(latest) if latest else {},
        "layers": compact_layers,
        "observed_token_completion_beat": max(completion_beats, default=-1),
    }


def _runtime_targets(executed_manifest: dict[str, Any]) -> dict[str, Any]:
    harness = _dict(executed_manifest.get("multilayer_harness"))
    activation = _dict(harness.get("activation_schedule"))
    scheduler = _dict(_dict(executed_manifest.get("board_integration_contract")).get("scheduler"))
    target_layers = _first_positive(
        harness.get("target_layer_count"),
        harness.get("bound_layer_count"),
        scheduler.get("layer_count"),
        scheduler.get("bound_layer_count"),
        executed_manifest.get("target_layer_count"),
        executed_manifest.get("bound_layer_count"),
    )
    input_beats = _first_positive(
        harness.get("accepted_input_beats_per_layer"),
        activation.get("accepted_input_beats_per_layer"),
    )
    output_beats = _first_positive(
        harness.get("accepted_output_beats_per_layer"),
        activation.get("accepted_output_beats_per_layer"),
    )
    return {
        "target_layer_count": target_layers,
        "accepted_input_beats_per_layer": input_beats,
        "accepted_output_beats_per_layer": output_beats,
    }


def _frontier(
    events: dict[str, Any], targets: dict[str, Any], failure_class: str
) -> dict[str, Any]:
    if events.get("status") != "ready":
        return {
            "frontier_id": "runtime_evidence_unavailable",
            "status": "unproven",
            "reason": "no complete structured progress event is available",
        }
    phase_counts = _dict(events.get("phase_counts"))
    terminal_pass = any(
        phase.lower() == "pass"
        and _dict(events.get("phase_last_event")).get(phase, {}).get("event_kind")
        == "terminal"
        for phase in phase_counts
    )
    if terminal_pass:
        return {"frontier_id": "none", "status": "proven", "reason": "terminal pass event observed"}

    layer_rows = _dict(events.get("layers"))
    target_layers = targets.get("target_layer_count")
    observed_layers = sorted(int(key) for key in layer_rows if str(key).isdigit())
    active_layer = next(
        (
            layer
            for layer in observed_layers
            if _dict(layer_rows.get(str(layer))).get("layer_output_complete", 0) == 0
        ),
        observed_layers[-1] if observed_layers else 0,
    )
    row = _dict(layer_rows.get(str(active_layer)))
    beats_per_token = _positive_int(events.get("observed_token_completion_beat", -1) + 1)
    expected_input_tokens = None
    expected_output_tokens = None
    if beats_per_token:
        input_beats = targets.get("accepted_input_beats_per_layer")
        output_beats = targets.get("accepted_output_beats_per_layer")
        if _positive_int(input_beats) and input_beats % beats_per_token == 0:
            expected_input_tokens = input_beats // beats_per_token
        if _positive_int(output_beats) and output_beats % beats_per_token == 0:
            expected_output_tokens = output_beats // beats_per_token

    observed = {
        "active_layer": active_layer,
        "target_layer_count": target_layers,
        "beats_per_token_inferred_from_trace": beats_per_token,
        "expected_input_tokens": expected_input_tokens,
        "expected_output_tokens": expected_output_tokens,
        **row,
    }

    def result(frontier_id: str, reason: str, *, domain: str = "board_lifecycle") -> dict[str, Any]:
        return {
            "frontier_id": frontier_id,
            "status": "earliest_unproven",
            "causal_domain": domain,
            "reason": reason,
            "observed": observed,
            "failure_class": failure_class,
        }

    if row.get("runtime_load_complete", 0) == 0:
        return result("runtime_loader_completion", "runtime loading has not reached its completion contract")
    if row.get("kernel_start", 0) == 0:
        return result("runtime_load_to_kernel_start", "runtime load completed but no kernel start was observed")
    if expected_input_tokens and row.get("input_completed", 0) < expected_input_tokens:
        return result("board_input_to_connected_kernel", "the connected kernel did not accept the complete layer input")
    output_started = int(row.get("output_started", 0))
    output_completed = int(row.get("output_completed", 0))
    if output_completed == 0:
        if output_started:
            return result("kernel_output_stream_completion", "kernel output started but no complete token output was observed", domain="connected_kernel_boundary")
        return result("connected_kernel_input_to_output", "complete kernel input was observed but no kernel output token started", domain="connected_kernel_boundary")
    if expected_output_tokens and output_completed < expected_output_tokens:
        if output_started > output_completed:
            return result("kernel_output_stream_completion", "a later kernel output token started but did not complete", domain="connected_kernel_boundary")
        if int(row.get("rearmed", 0)) > 0:
            return result("kernel_rearm_to_next_output", "a committed output and an explicit rearm were observed, but the next output token did not start")
        return result(
            "kernel_output_token_sequence_continuation",
            (
                "a complete non-final output token was observed but the next output "
                "token did not start; the current bound lifecycle contract and source "
                "must determine whether continuation is autonomous or explicitly rearmed"
            ),
            domain="kernel_wrapper_lifecycle",
        )
    if row.get("layer_output_complete", 0) == 0:
        return result("kernel_output_to_layer_commit", "the complete layer output stream was not committed as layer completion")

    prefetch_complete = int(row.get("weight_prefetch_complete", 0)) > 0
    latest = _dict(events.get("latest_event"))
    prefetch_progress = _dict(latest.get("prefetch_progress"))
    if (
        _positive_int(prefetch_progress.get("target_beats"))
        and prefetch_progress.get("accepted_beats") == prefetch_progress.get("target_beats")
    ):
        prefetch_complete = True
    if target_layers and active_layer + 1 < target_layers and not prefetch_complete:
        return result("prefetch_to_layer_join", "layer compute completed before the required next-layer prefetch completion")
    if target_layers and active_layer + 1 < target_layers and (
        row.get("weight_bank_switch", 0) == 0
        or row.get("activation_bank_switch", 0) == 0
    ):
        return result("layer_commit_to_bank_switch", "layer completion did not advance both weight and activation banks")
    if target_layers and active_layer + 1 >= target_layers and row.get("final_writeback_complete", 0) == 0:
        return result("final_writeback", "the final layer completed without complete final DDR writeback")
    return result("next_layer_scheduler_entry", "the proven layer boundary did not enter the next scheduler invocation")


def _boundary_failures(run_dir: Path) -> list[str]:
    candidates = (
        run_dir / "verification" / "debug_closure" / "boundary_trace.json",
        run_dir / "verification" / "board_simulation" / "boundary_trace.json",
        run_dir / "verification" / "board_simulation" / "boundary_trace.jsonl",
    )
    failed: list[str] = []
    for path in candidates:
        if not path.is_file():
            continue
        value = _read_json(path)
        records = value.get("boundary_trace") or value.get("records") or []
        if not isinstance(records, list) or not records:
            records = list(_iter_complete_jsonl(path))
        for row in records:
            if not isinstance(row, dict) or str(row.get("status") or "").lower() != "fail":
                continue
            boundary_id = str(row.get("boundary_id") or row.get("boundary") or "").strip()
            if boundary_id and boundary_id not in failed:
                failed.append(boundary_id)
        if failed:
            break
    return failed


def _select_graph(
    sacg: dict[str, Any], cctg: dict[str, Any], frontier: dict[str, Any], failed_boundaries: list[str]
) -> dict[str, Any]:
    edges = [row for row in sacg.get("edges", []) if isinstance(row, dict)]
    stream_edges = [row for row in edges if row.get("type") == "stream"]
    boundaries = [row for row in cctg.get("boundaries", []) if isinstance(row, dict)]
    frontier_id = str(frontier.get("frontier_id") or "")
    if failed_boundaries:
        selected_boundaries = [
            row
            for row in boundaries
            if row.get("boundary_id") in failed_boundaries
            or row.get("boundary") in failed_boundaries
        ]
    elif frontier_id in {"connected_kernel_input_to_output", "kernel_output_stream_completion"}:
        selected_boundaries = boundaries
    elif frontier_id == "board_input_to_connected_kernel":
        selected_boundaries = [row for row in boundaries if row.get("src_stage") == "block_input"]
    else:
        selected_boundaries = [row for row in boundaries if row.get("dst_stage") == "block_output"]
    selected_edge_ids = {str(row.get("edge_id") or "") for row in selected_boundaries}
    selected_edges = [
        row
        for row in stream_edges
        if str(row.get("id") or "").replace(".", "_") in selected_edge_ids
        or str(row.get("id") or "") in selected_edge_ids
    ]
    if selected_boundaries and not selected_edges:
        boundary_pairs = {
            (str(row.get("src_stage")), str(row.get("dst_stage")))
            for row in selected_boundaries
        }
        selected_edges = [
            row
            for row in stream_edges
            if (
                str(row.get("src") or "").split(".")[-1],
                str(row.get("dst") or "").split(".")[-1],
            )
            in boundary_pairs
        ]
    node_ids = {
        str(value)
        for row in selected_edges
        for value in (row.get("src"), row.get("dst"))
        if value
    }
    nodes = [
        row
        for row in sacg.get("nodes", [])
        if isinstance(row, dict) and row.get("id") in node_ids
    ]
    constraint_ids = {
        str(value)
        for row in selected_edges
        for value in row.get("constraints", [])
        if value
    }
    selected_edge_ids = {str(row.get("id") or "") for row in selected_edges}
    constraints = [
        _project_constraint(row, selected_edge_ids)
        for row in sacg.get("constraints", [])
        if isinstance(row, dict) and row.get("id") in constraint_ids
    ]
    return {
        "sacg_nodes": nodes,
        "sacg_edges": selected_edges,
        "sacg_constraints": constraints,
        "cctg_boundaries": selected_boundaries,
        "cctg_causal_paths": cctg.get("causal_paths", []),
    }


def _project_constraint(row: dict[str, Any], selected_edge_ids: set[str]) -> dict[str, Any]:
    """Keep frontier-scoped facts while the artifact hash binds the complete SACG."""

    def project(value: Any) -> Any:
        if isinstance(value, dict):
            edge_id = value.get("edge_id")
            if edge_id and str(edge_id) not in selected_edge_ids:
                return None
            result = {}
            for key, child in value.items():
                nested = project(child)
                if nested is not None:
                    result[str(key)] = nested
            return result
        if isinstance(value, list):
            result = []
            for child in value:
                nested = project(child)
                if nested is not None:
                    result.append(nested)
            return result
        return value

    facts = project(row.get("facts", {}))
    return {
        "id": row.get("id"),
        "type": row.get("type"),
        "artifacts": row.get("artifacts", []),
        "nodes": row.get("nodes", []),
        "edges": [
            edge_id
            for edge_id in row.get("edges", [])
            if str(edge_id) in selected_edge_ids
        ],
        "frontier_scoped_facts": facts,
    }


def _certificate_projection(run_dir: Path, frontier: dict[str, Any], failed_boundaries: list[str]) -> dict[str, Any]:
    certificate_path = run_dir / "verification" / "certificates" / "single_layer_promotion_certificate.json"
    functional_path = run_dir / "verification" / "single_layer" / "single_layer_functional_report.json"
    stats_path = run_dir / "verification" / "single_layer" / "single_layer_sim_stats.json"
    certificate = _read_json(certificate_path)
    functional = _read_json(functional_path)
    stats = _read_json(stats_path)
    overlap = _dict(functional.get("pipeline_overlap_evidence"))
    frontier_id = str(frontier.get("frontier_id") or "")
    lower_layer_frontier = frontier_id in {
        "connected_kernel_input_to_output",
        "kernel_output_stream_completion",
        "cctg_boundary_invariant_failure",
    }
    reopen = bool(failed_boundaries)
    return {
        "single_layer_certificate": {
            **_artifact(certificate_path),
            "status": certificate.get("status"),
            "required_gates": certificate.get("required_gates", []),
            "policy": certificate.get("policy", {}),
        },
        "single_layer_real_tool_evidence": {
            "functional_report": _artifact(functional_path),
            "sim_stats": _artifact(stats_path),
            "status": stats.get("status"),
            "input_beats": stats.get("input_beats"),
            "output_beats": stats.get("output_beats"),
            "cycles": stats.get("cycles"),
            "pipeline_overlap_status": overlap.get("status"),
            "pipeline_transition_count": len(overlap.get("transition_evidence", []))
            if isinstance(overlap.get("transition_evidence"), list)
            else 0,
        },
        "current_board_evidence_contradicts_lower_certificate": reopen,
        "lower_layer_reopen_policy": (
            "reopen the failed CCTG boundary and replay the affected lower layer"
            if reopen
            else (
                "lower-layer evidence remains reusable but not absolute; reopen only when the current trace supplies an explicit invariant contradiction"
                if lower_layer_frontier
                else "reuse the passed lower-layer certificate; the current frontier is outside its claimed scope"
            )
        ),
    }


def build_sacg_cctg_causal_slice(
    *,
    run_dir: Path,
    runner: dict[str, Any],
    executed_manifest: dict[str, Any],
    failure_class: str,
    executed_manifest_path: Path | None = None,
    progress_event_path: Path | None = None,
) -> dict[str, Any]:
    run_dir = run_dir.resolve()
    sacg_path = run_dir / "repair" / "sacg_state.json"
    cctg_path = run_dir / "verification" / "debug_closure" / "boundary_contracts.json"
    if progress_event_path is None:
        progress_event_path = (
            run_dir
            / "verification"
            / "board_simulation"
            / "reports"
            / "progress_event_log.jsonl"
        )
    if executed_manifest_path is None:
        executed_manifest_path = (
            run_dir
            / "verification"
            / "board_simulation"
            / "board_simulation_executed_manifest.json"
        )
    sacg = _read_json(sacg_path)
    cctg = _read_json(cctg_path)
    events = _event_summary(progress_event_path)
    targets = _runtime_targets(executed_manifest)
    failed_boundaries = _boundary_failures(run_dir)
    frontier = _frontier(events, targets, failure_class)
    if failed_boundaries:
        frontier = {
            "frontier_id": "cctg_boundary_invariant_failure",
            "status": "earliest_unproven",
            "causal_domain": "connected_kernel_boundary",
            "reason": "the current trace explicitly failed one or more CCTG boundary invariants",
            "failed_boundary_ids": failed_boundaries,
            "prior_runtime_frontier": frontier,
            "failure_class": failure_class,
        }
    graph = _select_graph(sacg, cctg, frontier, failed_boundaries)
    certificates = _certificate_projection(run_dir, frontier, failed_boundaries)
    ready = (
        events.get("status") == "ready"
        and bool(sacg.get("nodes"))
        and bool(cctg.get("boundaries"))
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "ready" if ready else "insufficient_evidence",
        "run_dir": str(run_dir),
        "input_fingerprint_sha256": runner.get("input_fingerprint_sha256"),
        "remote_workdir": runner.get("remote_workdir"),
        "failure_class": failure_class,
        "evidence_binding": {
            "progress_event_log": _artifact(progress_event_path),
            "executed_manifest": _artifact(executed_manifest_path),
            "sacg_state": _artifact(sacg_path),
            "cctg_boundary_contracts": _artifact(cctg_path),
        },
        "runtime_targets_from_executed_manifest": targets,
        "earliest_unproven_frontier": frontier,
        "parallel_branch_status": {
            "latest_prefetch_progress": _dict(_dict(events.get("latest_event")).get("prefetch_progress")),
            "latest_runtime_load_progress": _dict(_dict(events.get("latest_event")).get("runtime_load_progress")),
            "latest_final_writeback_progress": _dict(_dict(events.get("latest_event")).get("final_writeback_progress")),
            "policy": "independent branch progress is supporting evidence and does not move the primary dataflow frontier",
        },
        "runtime_evidence_projection": events,
        "causal_graph_slice": graph,
        "hierarchical_certificate_projection": certificates,
        "llm_analysis_contract": {
            "graph_frontier_is_primary_search_scope": True,
            "root_cause_is_not_pre_decided": True,
            "must_correlate_control_and_payload_at_frontier": True,
            "must_use_complete_hash_bound_source_before_edit": True,
            "must_not_edit_hardware_for_transport_or_tool_environment_failure": True,
            "must_rerun_same_hierarchical_layer_with_real_tool_after_repair": True,
            "may_reopen_lower_layer_only_on_explicit_current_trace_contradiction": True,
            "preserve_full_model_workload_and_exact_board_axi_ddr_contract": True,
        },
    }
