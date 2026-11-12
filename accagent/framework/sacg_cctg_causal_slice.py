"""Project exact-board runtime evidence onto the SACG and CCTG debug frontier."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, deque
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "spatialaccagent.sacg_cctg_causal_slice.v1"
PROGRESS_SCHEMA_VERSION = "spatialaccagent.board_progress_event.v1"
STATIC_CONTEXT_SCHEMA_VERSION = "spatialaccagent.sacg_static_failure_context.v1"


def _static_node_specificity(node_id: str) -> tuple[int, str]:
    """Rank concrete generated-stage nodes ahead of abstract semantic nodes.

    The rank only orders already evidence-bound candidates; it never creates a
    candidate from a filename alone.  Keeping the original node id as a
    tiebreaker makes the projection deterministic across Python versions.
    """
    value = str(node_id)
    if value.startswith("node.pipeline."):
        return (0, value)
    if value.startswith("node.stream."):
        return (1, value)
    if value.startswith("node.design_space."):
        return (2, value)
    if value.startswith("node.model_op."):
        return (3, value)
    return (4, value)


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


def _materialization_aliases(node: dict[str, Any]) -> set[str]:
    """Return evidence-derived aliases for a pipeline node.

    Generated RTL has several implementation names for one semantic stage
    (for example ``IntegerVectorNorm`` and ``VectorNorm``).  The aliases are
    derived from the node's recorded source/template/op facts; they are not a
    case-specific fault table.
    """

    facts = node.get("facts") if isinstance(node.get("facts"), dict) else {}
    values = {
        str(facts.get(key) or "")
        for key in ("source", "template_id", "op", "kind", "stage_id")
    }
    values.add(str(node.get("name") or ""))
    aliases: set[str] = set()
    for value in values:
        if not value:
            continue
        stem = Path(value).stem.casefold()
        aliases.add(stem)
        aliases.update(part for part in re.split(r"[^a-z0-9]+", stem) if part)
    # These generated modules implement the semantic template recorded by the
    # graph.  Shared implementations deliberately retain every matching stage.
    implementations = {
        "attention": {"integerattention", "qkvprojection"},
        "ffn": {"linear", "denseffn"},
        "residual": {"residualadd"},
    }
    for template, modules in implementations.items():
        if template in aliases:
            aliases.update(modules)
    return aliases


def _materialization_node_bindings(
    *,
    source_path: Path,
    source_artifact_id: str,
    nodes: dict[str, dict[str, Any]],
    artifacts: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Map a generated source to graph nodes using recorded materialization facts.

    The mapping is deliberately conservative: a source is first bound to a
    generated package artifact, then its module stem is compared with aliases
    recorded on pipeline nodes.  Wrapper and shared physical sources retain a
    bounded candidate set instead of being assigned an invented root cause.
    """

    stem = source_path.stem.casefold()
    pipeline = {
        node_id: node for node_id, node in nodes.items()
        if node_id.startswith("node.pipeline.")
    }
    exact = [
        node_id for node_id, node in pipeline.items()
        if stem in _materialization_aliases(node)
    ]
    role = "pipeline_stage"
    if stem in {"generatedacceleratortop", "generatedaxiddrtop", "gpt2prelnblock"}:
        role = "integration_boundary"
        exact = [
            node_id for node_id, node in pipeline.items()
            if node_id.endswith("block_input") or node_id.endswith("block_output")
        ]
    elif stem.startswith("physical") or stem in {"weighttilecache", "weighttileservicemux"}:
        role = "shared_physical_resource"
        if not exact:
            exact = [node_id for node_id in pipeline if not node_id.endswith(("block_input", "block_output"))]
    return [
        {
            "source_path": str(source_path),
            "artifact_id": source_artifact_id,
            "role": role,
            "candidate_node_ids": sorted(exact),
            "mapping_basis": "generated-source-module-stem_to_recorded_pipeline-facts",
        }
    ]


def build_static_failure_context(
    *,
    sacg_state_path: Path,
    failure_report_path: Path,
) -> dict[str, Any]:
    """Return exact-evidence SACG context for compile, contract, or timing reports.

    This is a static dependency projection, not a runtime CCTG causal slice.
    The failure report must bind the exact SACG snapshot it was produced with.
    """
    sacg_state_path = sacg_state_path.resolve()
    failure_report_path = failure_report_path.resolve()
    sacg = _read_json(sacg_state_path)
    report = _read_json(failure_report_path)
    sacg_sha256 = _sha256(sacg_state_path)
    declared_sacg_sha256 = report.get("sacg_state_sha256")
    failure_domain = report.get("failure_domain")
    if not failure_domain:
        failure_domain = {
            "vcs_compile_failure": "compile_time",
            "vcs_elaboration_failure": "compile_time",
            "contract_check_failure": "contract",
            "contract_violation": "contract",
            "synthesis_timing_failure": "synthesis_timing",
            "timing_constraint_failure": "synthesis_timing",
            "timing_violation": "synthesis_timing",
        }.get(str(report.get("failure_class") or ""))
    result: dict[str, Any] = {
        "schema_version": STATIC_CONTEXT_SCHEMA_VERSION,
        "status": "insufficient_evidence",
        "diagnostic_domain": failure_domain,
        "runtime_causal_claim": False,
        "evidence_binding": {
            "failure_report": _artifact(failure_report_path),
            "sacg_state": _artifact(sacg_state_path),
            "sacg_binding_matches": bool(sacg_sha256 and declared_sacg_sha256 == sacg_sha256),
        },
        "failure_summary": report.get("summary") or report.get("first_real_error"),
        "mapped_failure_sources": [],
        "materialization_node_bindings": [],
        "root_cause_candidates": [],
        "upstream_dependency_context": [],
        "upstream_root_candidate": None,
        "primary_stage_candidate": None,
        "violated_dependency_edges": [],
        "candidate_repair_scope": [],
        "authorized_repair_scope": [],
        "blockers": [],
    }
    if not sacg:
        result["blockers"].append("SACG state is missing or invalid")
        return result
    if not report:
        result["blockers"].append("failure report is missing or invalid")
        return result
    if failure_domain not in {"compile_time", "contract", "synthesis_timing"}:
        result["blockers"].append("failure report has no supported static diagnostic domain")
        return result
    if str(report.get("status") or "").lower() in {"pass", "ready", "complete"}:
        result["blockers"].append("successful report cannot seed a static failure context")
        return result
    if not sacg_sha256 or declared_sacg_sha256 != sacg_sha256:
        result["blockers"].append("failure report does not bind the exact SACG snapshot")
        return result

    # An isolated fault copy can be analyzed against its original artifact path,
    # but only when the report binds the exact bytes actually inspected.
    copy_value = report.get("fault_copy_path")
    if copy_value:
        copy_path = Path(str(copy_value)).resolve()
        observed = _sha256(copy_path)
        declared = report.get("fault_copy_sha256")
        source_value = report.get("source_file")
        source_path = Path(str(source_value)).resolve() if source_value else None
        source_sha = _sha256(source_path) if source_path else None
        result["evidence_binding"]["fault_copy"] = _artifact(copy_path)
        result["evidence_binding"]["fault_copy_binding_matches"] = bool(observed and observed == declared)
        result["evidence_binding"]["analyzed_source_matches_fault_copy"] = bool(source_sha and source_sha == declared)
        if not observed or observed != declared or source_sha != declared:
            result["blockers"].append("failure report does not bind the exact fault copy")
            return result
        if not report.get("origin_artifact_path"):
            result["blockers"].append("fault copy requires its original artifact path")
            return result

    node_rows = [row for row in sacg.get("nodes", []) if isinstance(row, dict)]
    edge_rows = [row for row in sacg.get("edges", []) if isinstance(row, dict)]
    constraint_rows = [row for row in sacg.get("constraints", []) if isinstance(row, dict)]
    artifact_rows = [row for row in sacg.get("artifacts", []) if isinstance(row, dict)]
    nodes = {str(row.get("id")): row for row in node_rows if row.get("id")}
    edges = {str(row.get("id")): row for row in edge_rows if row.get("id")}
    constraints = {str(row.get("id")): row for row in constraint_rows if row.get("id")}
    artifacts = {str(row.get("id")): row for row in artifact_rows if row.get("id")}

    references = report.get("sacg_references")
    references = references if isinstance(references, dict) else {}
    def reference_values(key: str) -> set[str]:
        values = references.get(key, [])
        if isinstance(values, str):
            values = [values]
        return {str(value) for value in values if value} if isinstance(values, list) else set()

    node_ids = reference_values("node_ids")
    root_candidate_ids = reference_values("root_cause_candidate_node_ids")
    edge_ids = reference_values("edge_ids")
    constraint_ids = reference_values("constraint_ids")
    artifact_ids = reference_values("artifact_ids")
    node_ids.intersection_update(nodes)
    root_candidate_ids.intersection_update(nodes)
    node_ids.update(root_candidate_ids)
    edge_ids.intersection_update(edges)
    constraint_ids.intersection_update(constraints)
    artifact_ids.intersection_update(artifacts)

    # Checker messages can identify an actual violated edge.  An upstream
    # candidate is warranted only for a unique reported edge; ordinary upstream
    # reachability alone is not a root-cause diagnosis.
    diagnostics = "\n".join(str(report.get(key) or "") for key in ("summary", "first_real_error", "errors"))
    violated = [edge for edge in edge_rows if edge.get("id") and str(edge["id"]) in diagnostics]
    if len(violated) == 1 and "src_output_bits" in diagnostics:
        edge = violated[0]
        src, dst = str(edge.get("src") or ""), str(edge.get("dst") or "")
        if src in nodes and dst in nodes:
            result["violated_dependency_edges"] = [edge]
            result["upstream_root_candidate"] = nodes[src]
            result["primary_stage_candidate"] = nodes[dst]
            root_candidate_ids.add(dst)
            node_ids.update((src, dst))
            edge_ids.add(str(edge["id"]))

    source_values: list[str] = []
    direct_source = report.get("origin_artifact_path") if copy_value else report.get("source_file")
    if isinstance(direct_source, str) and direct_source.strip():
        source_values.append(direct_source.strip())
    affected_paths = [] if copy_value else report.get("affected_source_paths", [])
    if isinstance(affected_paths, list):
        for value in affected_paths:
            if isinstance(value, str) and value.strip() and value.strip() not in source_values:
                source_values.append(value.strip())

    matched_source_artifacts: set[str] = set()
    for source_value in source_values:
        source_path = Path(source_value)
        if not source_path.is_absolute():
            source_path = failure_report_path.parent / source_path
        source_path = source_path.resolve()
        source_bound = False
        for artifact_id, artifact in artifacts.items():
            raw_path = artifact.get("path")
            if not isinstance(raw_path, str) or not raw_path:
                continue
            artifact_path = Path(raw_path).resolve()
            try:
                exact_match = source_path == artifact_path or source_path.is_relative_to(artifact_path)
            except (OSError, ValueError):
                exact_match = False
            if exact_match:
                source_bound = True
                matched_source_artifacts.add(artifact_id)
                result["mapped_failure_sources"].append({
                    "source_path": str(source_path),
                    "artifact_id": artifact_id,
                    "artifact_path": str(artifact_path),
                })
                bindings = _materialization_node_bindings(
                    source_path=source_path,
                    source_artifact_id=artifact_id,
                    nodes=nodes,
                    artifacts=artifacts,
                )
                result["materialization_node_bindings"].extend(bindings)
                for binding in bindings:
                    node_ids.update(
                        str(value) for value in binding.get("candidate_node_ids", [])
                        if str(value) in nodes
                    )
                    root_candidate_ids.update(
                        str(value) for value in binding.get("candidate_node_ids", [])
                        if str(value) in nodes
                    )
        # Pipeline-stage facts carry the template source that produced each stage.
        # Match the exact basename only after the source is bound to a generated
        # package artifact; ambiguous owners remain a candidate set.
        if source_bound:
            source_stems = {source_path.stem.casefold()}
            failure_symbols = report.get("failure_symbols", [])
            if isinstance(failure_symbols, str):
                failure_symbols = [failure_symbols]
            if isinstance(failure_symbols, list):
                source_stems.update(
                    Path(str(value)).stem.casefold()
                    for value in failure_symbols
                    if isinstance(value, str) and value.strip()
                )
            for node_id, node in nodes.items():
                facts = node.get("facts")
                if not isinstance(facts, dict):
                    facts = {}
                source_names = (
                    facts.get("source"),
                    facts.get("template_id"),
                    facts.get("op"),
                    facts.get("kind"),
                    node.get("name"),
                )
                if any(
                    value and Path(str(value)).stem.casefold() in source_stems
                    for value in source_names
                ):
                    root_candidate_ids.add(node_id)
                    node_ids.add(node_id)
    artifact_ids.update(matched_source_artifacts)
    if copy_value and not matched_source_artifacts:
        result["blockers"].append("fault copy origin is not bound to a SACG artifact")
        return result

    for artifact_id in artifact_ids:
        artifact = artifacts[artifact_id]
        node_ids.update(str(value) for value in artifact.get("nodes", []) if str(value) in nodes)
        for node_id, node in nodes.items():
            if artifact_id in node.get("artifacts", []):
                node_ids.add(node_id)
        for constraint_id, constraint in constraints.items():
            if artifact_id in constraint.get("artifacts", []):
                constraint_ids.add(constraint_id)
                node_ids.update(str(value) for value in constraint.get("nodes", []) if str(value) in nodes)
                edge_ids.update(str(value) for value in constraint.get("edges", []) if str(value) in edges)

    for constraint_id in constraint_ids:
        constraint = constraints[constraint_id]
        node_ids.update(str(value) for value in constraint.get("nodes", []) if str(value) in nodes)
        edge_ids.update(str(value) for value in constraint.get("edges", []) if str(value) in edges)
    for edge_id in edge_ids:
        edge = edges[edge_id]
        node_ids.update(str(edge.get(key)) for key in ("src", "dst") if str(edge.get(key)) in nodes)

    if not node_ids:
        result["blockers"].append("failure evidence has no exact SACG node, edge, constraint, or artifact mapping")
        return result

    upstream = set(node_ids)
    queue = deque(node_ids)
    while queue:
        current = queue.popleft()
        for edge in edge_rows:
            if edge.get("dst") != current:
                continue
            source_id = str(edge.get("src") or "")
            if source_id in nodes and source_id not in upstream:
                upstream.add(source_id)
                queue.append(source_id)
                edge_ids.add(str(edge.get("id") or ""))

    selected_constraints = {
        constraint_id
        for constraint_id, constraint in constraints.items()
        if constraint_id in constraint_ids
        or bool(set(constraint.get("nodes", [])) & upstream)
        or bool(set(constraint.get("edges", [])) & edge_ids)
    }
    candidate_artifact_ids = set(artifact_ids)
    for node_id in upstream:
        candidate_artifact_ids.update(
            str(value) for value in nodes[node_id].get("artifacts", []) if str(value) in artifacts
        )
    for constraint_id in selected_constraints:
        candidate_artifact_ids.update(
            str(value) for value in constraints[constraint_id].get("artifacts", []) if str(value) in artifacts
        )

    # A consumer instance can refine file-level shared-module ownership. It
    # must refer to a real instance in an exact, graph-bound source copy; a
    # caller-provided stage ID alone never grants a unique root candidate.
    consumer_context = report.get("consumer_context")
    consumer_projection: dict[str, Any] = {"status": "not_supplied"}
    if isinstance(consumer_context, dict):
        consumer_path = Path(str(consumer_context.get("source_file") or ""))
        origin = Path(str(consumer_context.get("origin_artifact_path") or "")).resolve()
        consumer_module = str(consumer_context.get("module") or "")
        producer_module = str(consumer_context.get("producer_module") or "")
        instance = str(consumer_context.get("instance_name") or "")
        bound = any(origin == Path(str(a.get("path") or "")).resolve()
                    or origin.is_relative_to(Path(str(a.get("path") or "")).resolve())
                    for a in artifacts.values() if a.get("path"))
        valid = (bound and consumer_path.is_file()
                 and _sha256(consumer_path) == consumer_context.get("source_sha256")
                 and _sha256(Path(str(report.get("tool_log") or ""))) == report.get("tool_log_sha256"))
        matched = None
        if valid:
            text = consumer_path.read_text()
            matched = re.search(r"\b" + re.escape(producer_module) + r"\s+" + re.escape(instance)
                                + r"\s*\((.*?)\);", text, re.S)
            valid = bool(matched and re.search(r"\bmodule\s+" + re.escape(consumer_module) + r"\b", text))
        if valid:
            # Consumer context must be supported by the same compiler report,
            # not merely by a caller-supplied instance from the source tree.
            tool_log = Path(str(report.get("tool_log") or "")).read_text(errors="replace")
            diagnostic = re.search(
                r"Port\s+\"([^\"]+)\"\s+is not defined in module\s+'([^']+)'",
                tool_log,
                re.S,
            )
            locations = re.findall(r"([A-Za-z0-9_./-]+\.sv),\s*\d+", tool_log)
            consumer_reported = bool(locations and Path(locations[0]).name == consumer_path.name)
            instance_reported = bool(re.search(
                r"Module instance:\s*" + re.escape(producer_module) + r"\s+"
                + re.escape(instance) + r"\s*\(", tool_log,
            ))
            valid = bool(diagnostic and diagnostic.group(2) == producer_module
                         and consumer_reported and instance_reported)
        pipeline_roots = {n for n in root_candidate_ids if n.startswith("node.pipeline.")
                          and not n.endswith(("block_input", "block_output"))}
        owners = {n for n, node in nodes.items() if n.startswith("node.pipeline.")
                  and consumer_module.casefold() in _materialization_aliases(node)} if valid else set()
        refined = pipeline_roots & owners
        basis = "producer_consumer_owner_intersection"
        if not refined and len(owners) == 1:
            # A unique semantic consumer can own a helper missing from a prior
            # broad filename alias (e.g. a linear helper inside QKV).
            refined = owners
            basis = "unique_graph_bound_consumer_owner"
        if valid and not refined and pipeline_roots and matched:
            # Resolve a direct predecessor only through actual data connections.
            input_expressions = set(re.findall(r"\.\w*(?:in|computed)\w*bits_data\s*\(\s*(\w+)\s*\)", matched.group(1)))
            predecessor_ids = set()
            for child in re.finditer(r"(?m)^\s*(\w+)\s+(\w+)\s*\((.*?)\);", text, re.S):
                outputs = set(re.findall(r"\.\w*out\w*bits_data\s*\(\s*(\w+)\s*\)", child.group(3)))
                if outputs & input_expressions:
                    predecessor_ids.update(n for n, node in nodes.items() if n.startswith("node.pipeline.")
                                           and child.group(1).casefold() in _materialization_aliases(node))
            refined = {e.get("dst") for e in edge_rows if e.get("src") in predecessor_ids and e.get("dst") in pipeline_roots}
            basis = "consumer_instance_data_connection_and_graph_predecessor"
        if valid and not refined:
            refined = pipeline_roots
            basis = "no_unique_consumer_ownership_keep_candidates"
        consumer_projection = {"status": "verified" if valid else "invalid_evidence",
                               "producer_candidates_before": sorted(root_candidate_ids),
                               "consumer_candidates": sorted(owners), "candidates_after": sorted(refined),
                               "basis": basis, "consumer_module": consumer_module, "instance_name": instance}
        if valid and refined:
            root_candidate_ids = set(refined)
            node_ids.update(refined)
    result["consumer_instance_projection"] = consumer_projection
    ordered_root_ids = sorted(root_candidate_ids, key=_static_node_specificity)
    primary_root_id = ordered_root_ids[0] if ordered_root_ids else None
    if result["primary_stage_candidate"] is None and primary_root_id:
        result["primary_stage_candidate"] = nodes[primary_root_id]
    # Static projection can suggest candidate artifacts, but it cannot grant
    # write authority. The repair gate must authorize any actual patch.
    if primary_root_id:
        candidate_artifact_ids.update(
            str(value) for value in nodes[primary_root_id].get("artifacts", [])
            if str(value) in artifacts
        )
    result.update({
        "status": "static_context_ready",
        "failure_domain": failure_domain,
        "affected_graph_nodes": [nodes[node_id] for node_id in sorted(node_ids)],
        "root_cause_candidates": [nodes[node_id] for node_id in ordered_root_ids],
        "primary_root_cause_candidate": (
            nodes[primary_root_id] if primary_root_id else None
        ),
        "upstream_dependency_context": [nodes[node_id] for node_id in sorted(upstream)],
        "dependency_edges": [
            edge
            for edge in edge_rows
            if edge.get("id") in edge_ids
            or (edge.get("src") in upstream and edge.get("dst") in upstream)
        ],
        "related_constraints": [constraints[key] for key in sorted(selected_constraints)],
        "candidate_repair_scope": [
            {
                "artifact_id": artifact_id,
                "path": artifacts[artifact_id].get("path"),
                "type": artifacts[artifact_id].get("type"),
            }
            for artifact_id in sorted(candidate_artifact_ids)
        ],
        "authorized_repair_scope": [],
        "repair_scope_policy": "static projection proposes candidate_repair_scope only; the repair authorization gate must grant write scope",
        "blockers": [],
    })
    return result


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
