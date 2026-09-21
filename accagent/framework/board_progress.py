"""Structured live-progress evidence for long-running exact-board simulation."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


BOARD_DEBUG_OBSERVABILITY_SCHEMA_VERSION = (
    "spatialaccagent.board_debug_observability.v1"
)
BOARD_PROGRESS_EVENT_SCHEMA_VERSION = "spatialaccagent.board_progress_event.v1"
PIPELINE_BOUNDARY_OBSERVATION_SCHEMA_VERSION = (
    "spatialaccagent.pipeline_boundary_observation.v1"
)
PIPELINE_STAGE_TRACE_SCHEMA_VERSION = "spatialaccagent.pipeline_stage_trace.v1"

# These are the small, stable fields needed to locate a blocked ready/valid
# boundary without retaining an unbounded waveform or every transferred word.
PIPELINE_BOUNDARY_OBSERVATION_FIELDS = (
    "valid",
    "ready",
    "fire",
    "accepted_count",
    "first_accepted_payload_digest",
    "last_accepted_payload_digest",
)
# These fields are optional diagnostic context. They never replace the six
# required transfer fields above and never affect the functional pass rule.
# A generated board testbench may add other scalar signals from the current
# DUT hierarchy; the summary keeps those signals in a bounded form as well.
PIPELINE_BOUNDARY_DIAGNOSTIC_FIELDS = (
    "start",
    "last",
    "received_count",
    "current_payload_unknown",
    "current_payload_digest",
    "waiting_after_upstream_progress",
)
MAX_BOUNDARY_OBSERVATION_RECORDS = 16
MAX_UNEXPECTED_BOUNDARIES = 32
# Observation records are emitted only at meaningful boundary transitions by
# the testbench. Preserve every declared key scalar and every such transition;
# the framework must not silently discard a signal selected by the Agent.

PIPELINE_TRACE_RE = re.compile(
    r"SPATIALACC_PIPELINE_TRACE\s+"
    r"boundary=(?P<boundary>\S+)\s+cycle=\s*(?P<cycle>\d+)\s+"
    r"token=\s*(?P<token>\d+)\s+beat=\s*(?P<beat>\d+)\s+"
    r"st=\s*(?P<start>[01])\s+last=\s*(?P<last>[01])\s+"
    r"valid=\s*(?P<valid>[01])\s+ready=\s*(?P<ready>[01])"
)

PIPELINE_STAGE_TRACE_RE = re.compile(
    r"SPATIALACC_STAGE_TRACE\s+"
    r"stage=(?P<stage>\S+)\s+cycle=\s*(?P<cycle>\d+)\s+"
    r"token=\s*(?P<token>-?\d+)\s+beat=\s*(?P<beat>-?\d+)\s+"
    r"event=(?P<event>\S+)\s+signal=(?P<signal>\S+)\s+"
    r"(?:value|scalar_value)=(?P<value>\S+)"
)

STAGE_TRACE_VECTOR_KNOWN_RE = re.compile(
    r"^(?P<base>.+)\[(?P<index>\d+)\]\.known$"
)

REQUIRED_DEBUG_EVENT_KINDS = {
    "lifecycle",
    "semantic_progress",
    "heartbeat",
    "stall_snapshot",
    "terminal",
}

REQUIRED_DEBUG_SEMANTIC_ROLES = {
    "kernel_lifecycle",
    "scheduler",
    "pipeline_boundary",
    "weight_prefetch",
    "weight_bank",
    "activation_bank",
    "runtime_loader",
    "axi",
    "final_writeback",
}

REQUIRED_PROGRESS_EVENT_FIELDS = {
    "schema_version",
    "sequence",
    "cycle",
    "event_kind",
    "phase",
    "semantic_progress",
    "progress_epoch",
    "last_semantic_progress_cycle",
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
}

_TRANSIENT_AXI_CONTROL_SUFFIXES = ("valid", "ready")
_ADAPTIVE_SEMANTIC_GAP_MULTIPLIER = 32
_ADAPTIVE_TARGET_WORK_MULTIPLIER = 512
_ADAPTIVE_HEARTBEAT_MULTIPLIER = 16384
_MIN_STALL_SNAPSHOT_COUNT = 8
_CCTG_FRONTIER_BUDGET_MULTIPLIER = 32

_BARE_UNKNOWN_JSON_TOKEN_RE = re.compile(
    r"(?P<prefix>[:\[,])\s*(?P<value>[xXzZ])\s*(?P<suffix>[,\]}])"
)


def read_complete_jsonl(path: Path) -> dict[str, Any]:
    """Read only newline-committed JSON objects from a file being written."""

    if not path.is_file():
        return {
            "status": "missing",
            "path": str(path),
            "byte_count": 0,
            "committed_byte_count": 0,
            "trailing_partial_byte_count": 0,
            "records": [],
            "invalid_records": [],
        }
    raw = path.read_bytes()
    committed_byte_count = raw.rfind(b"\n") + 1
    committed = raw[:committed_byte_count]
    records: list[dict[str, Any]] = []
    invalid: list[dict[str, Any]] = []
    recovered_nonstandard_json_count = 0
    for line_number, line in enumerate(committed.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            # Older board wrappers wrote four-state unknown values as bare
            # x/z tokens inside JSONL.  Recover only those exact scalar
            # tokens; do not apply a broad JSON repair that could hide a
            # malformed record.
            try:
                text = line.decode("utf-8")
                repaired = _BARE_UNKNOWN_JSON_TOKEN_RE.sub(
                    lambda match: (
                        f'{match.group("prefix")}\"{match.group("value").lower()}\"'
                        f'{match.group("suffix")}'
                    ),
                    text,
                )
                value = json.loads(repaired)
                recovered_nonstandard_json_count += 1
            except (UnicodeDecodeError, json.JSONDecodeError):
                invalid.append({"line": line_number, "error": str(exc)[:500]})
                continue
        if isinstance(value, dict):
            records.append(value)
        else:
            invalid.append(
                {"line": line_number, "error": "progress event is not a JSON object"}
            )
    return {
        "status": "ready",
        "path": str(path),
        "byte_count": len(raw),
        "committed_byte_count": committed_byte_count,
        "trailing_partial_byte_count": len(raw) - committed_byte_count,
        "records": records,
        "invalid_records": invalid[:64],
        "recovered_nonstandard_json_count": recovered_nonstandard_json_count,
    }


def _stage_trace_value(raw_value: str) -> Any:
    """Convert one emitted scalar without treating an unknown as a number."""

    if raw_value.lower() in {"x", "z", "xx", "zz", "unknown"}:
        return raw_value
    if raw_value.lower() in {"true", "false"}:
        return raw_value.lower() == "true"
    try:
        return int(raw_value, 0)
    except ValueError:
        return raw_value[:128]


def parse_stage_trace_line(line: str) -> dict[str, Any] | None:
    """Parse one VCS stage-trace line emitted by the generated testbench."""

    match = PIPELINE_STAGE_TRACE_RE.search(line)
    if match is None:
        return None
    return {
        "schema_version": PIPELINE_STAGE_TRACE_SCHEMA_VERSION,
        "stage_id": match.group("stage"),
        "cycle": int(match.group("cycle")),
        "token": int(match.group("token")),
        "beat": int(match.group("beat")),
        "event": match.group("event"),
        "signal": match.group("signal"),
        "value": _stage_trace_value(match.group("value")),
        "source": "simulation_log",
    }


def read_pipeline_trace_log(path: Path) -> dict[str, Any]:
    """Read bounded internal ready/valid records already emitted by VCS."""

    if not path.is_file():
        return {
            "status": "missing",
            "path": str(path),
            "records": [],
            "stage_records": [],
            "unparsed": 0,
            "stage_unparsed": 0,
        }
    records: list[dict[str, Any]] = []
    stage_records: list[dict[str, Any]] = []
    unparsed = 0
    stage_unparsed = 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "SPATIALACC_PIPELINE_TRACE" in line:
            match = PIPELINE_TRACE_RE.search(line)
            if match is None:
                unparsed += 1
                continue
            valid = bool(int(match.group("valid")))
            ready = bool(int(match.group("ready")))
            records.append(
                {
                    "boundary_id": match.group("boundary"),
                    "cycle": int(match.group("cycle")),
                    "token": int(match.group("token")),
                    "beat": int(match.group("beat")),
                    "start": bool(int(match.group("start"))),
                    "last": bool(int(match.group("last"))),
                    "valid": valid,
                    "ready": ready,
                    "fire": valid and ready,
                    "source": "simulation_log",
                }
            )
        elif "SPATIALACC_STAGE_TRACE" in line:
            stage_record = parse_stage_trace_line(line)
            if stage_record is None:
                stage_unparsed += 1
                continue
            stage_records.append(stage_record)
    return {
        "status": "ready",
        "path": str(path),
        "records": records,
        "stage_records": stage_records,
        "unparsed": unparsed,
        "stage_unparsed": stage_unparsed,
    }


def _stage_trace_sample(record: dict[str, Any]) -> dict[str, Any]:
    return {
        key: record.get(key)
        for key in ("cycle", "token", "beat", "event", "value")
    }


def _value_is_known(value: Any) -> bool:
    """Return whether a ``...[bit].known`` probe says its bit is known."""

    return value is True or (
        isinstance(value, int) and not isinstance(value, bool) and value == 1
    )


def _integer_ranges(values: list[int]) -> list[list[int]]:
    """Compact sorted bit positions into inclusive ranges."""

    if not values:
        return []
    ranges: list[list[int]] = []
    start = values[0]
    previous = values[0]
    for value in values[1:]:
        if value == previous + 1:
            previous = value
            continue
        ranges.append([start, previous])
        start = value
        previous = value
    ranges.append([start, previous])
    return ranges


def _normalized_signal_name(value: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


_BOUNDARY_STAGE_IDS = {
    "stage_00_rms_norm_1",
    "stage_01_self_attention",
    "stage_02_residual_add_1",
    "stage_03_rms_norm_2",
    "stage_04_mlp_gate_proj",
    "stage_05_mlp_up_proj",
    "stage_06_activation_mul",
    "stage_07_mlp_down_proj",
    "stage_08_residual_add_2",
}


_BOUNDARY_FIELD_ALIASES: dict[str, dict[str, tuple[str, ...]]] = {
    "stage_01_self_attention": {
        "collect_beat": ("collectbeat",),
        "emit_head": ("emithead",),
        "emit_beat": ("emitbeat",),
        "start": ("iostart",),
        "weight_valid": ("ioweightvalid",),
        "weight_ready": ("ioweightready",),
        "bias_valid": ("iobiasvalid",),
        "bias_ready": ("iobiasready",),
        "projection_output_valid": ("projectioniooutvalid",),
        "projection_output_last": ("projectioniooutbitslast",),
        "output_head": ("iooutbitshead",),
        "output_last": ("iooutbitslast",),
        "state": ("state",),
    },
    "stage_02_residual_add_1": {
        "residual_skip_full": ("maybe_full",),
        "held_valid": ("heldvalid",),
        "pair_valid": ("pairvalid",),
        "output_queue_full": ("maybe_full",),
        "residual_queue_read_ready": ("residualqiodeqready",),
        "computed_queue_read_ready": ("computedqiodeqready",),
        "output_queue_write_ready": ("outputqioenqready",),
        "computed_queue_write_pointer": ("computedqenqptrvalue",),
        "beat_in_token": ("beatinToken", "beatinsequence"),
        "token_in_sequence": ("tokeninsequence",),
        "token_final_beat": ("tokenfinalbeat",),
        "sequence_final_beat": ("sequencefinalbeat",),
    },
    "stage_08_residual_add_2": {
        "held_valid": ("heldvalid",),
        "pair_valid": ("pairvalid",),
        "output_queue_full": ("maybe_full",),
        "token_final_beat": ("tokenfinalbeat",),
        "sequence_final_beat": ("sequencefinalbeat",),
        "token_in_sequence": ("tokeninsequence",),
    },
}


def _load_runtime_signal_rows(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.is_file():
        return []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return []
    if not isinstance(value, dict):
        return []
    rows = value.get("selected_signals", [])
    if not isinstance(rows, list):
        rows = value.get("signals", [])
    return [row for row in rows if isinstance(row, dict) and row.get("expression")]


def _signal_row_matches_field(
    row: dict[str, Any],
    *,
    stage_id: str | None,
    field_name: str,
) -> bool:
    if stage_id and str(row.get("stage") or "") != stage_id:
        return False
    expression = str(row.get("expression") or "")
    leaf = _normalized_signal_name(expression.rsplit(".", 1)[-1])
    aliases = set(
        _BOUNDARY_FIELD_ALIASES.get(stage_id or "", {}).get(
            field_name, ()
        )
    )
    aliases.add(_normalized_signal_name(field_name))
    return leaf in aliases


def _boundary_signal_rows(
    rows: list[dict[str, Any]],
    boundary_id: str,
    field_name: str,
) -> list[dict[str, Any]]:
    normalized_field = _normalized_signal_name(field_name)
    matches: list[dict[str, Any]] = []
    for row in rows:
        if str(row.get("boundary") or "") != boundary_id:
            continue
        expression = str(row.get("expression") or "")
        leaf = _normalized_signal_name(expression.rsplit(".", 1)[-1])
        if leaf == normalized_field or leaf.endswith(normalized_field):
            matches.append(row)
    return matches


def _record_runtime_scalar(
    stages: dict[str, dict[str, Any]],
    all_signal_names: set[str],
    *,
    stage_id: str,
    signal: str,
    sample: dict[str, Any],
) -> None:
    stage = stages.setdefault(
        stage_id,
        {
            "record_count": 0,
            "first_cycle": None,
            "last_cycle": None,
            "event_counts": Counter(),
            "scalar_signals": {},
            "known_bit_vectors": {},
        },
    )
    stage["record_count"] += 1
    cycle = int(sample.get("cycle") or 0)
    if stage["first_cycle"] is None or cycle < stage["first_cycle"]:
        stage["first_cycle"] = cycle
    if stage["last_cycle"] is None or cycle > stage["last_cycle"]:
        stage["last_cycle"] = cycle
    stage["event_counts"][str(sample.get("event") or "boundary_snapshot")] += 1
    scalar = stage["scalar_signals"].setdefault(
        signal,
        {
            "sample_count": 0,
            "change_count": 0,
            "first_sample": None,
            "last_sample": None,
            "last_change": None,
        },
    )
    if scalar["first_sample"] is None:
        scalar["first_sample"] = sample
    elif scalar["last_sample"]["value"] != sample["value"]:
        scalar["change_count"] += 1
        scalar["last_change"] = sample
    scalar["sample_count"] += 1
    scalar["last_sample"] = sample
    all_signal_names.add(signal)


def _merge_boundary_trace_scalars(
    stages: dict[str, dict[str, Any]],
    all_signal_names: set[str],
    boundary_trace_path: Path,
    catalog_path: Path | None,
) -> dict[str, Any]:
    parsed = read_complete_jsonl(boundary_trace_path)
    rows = _load_runtime_signal_rows(catalog_path)
    recovered = int(parsed.get("recovered_nonstandard_json_count") or 0)
    scalar_count = 0
    unmapped: Counter[str] = Counter()
    for record in parsed.get("records", []):
        if not isinstance(record, dict):
            continue
        observed = record.get("observed_value")
        if not isinstance(observed, dict):
            continue
        cycle = int(record.get("cycle") or 0)
        token = int(record.get("logical_index") or -1)
        event = str(observed.get("event") or record.get("event") or "boundary_snapshot")
        boundary_id = str(record.get("boundary_id") or "")
        sample_base = {"cycle": cycle, "token": token, "beat": -1, "event": event}

        # Boundary valid/ready are the actual input/output handshake signals
        # for the selected DUT expressions.  This is the missing QKV input
        # and output evidence in the old runtime-only summary.
        boundary_values = observed.get("boundary")
        if isinstance(boundary_values, dict):
            for field_name in ("valid", "ready"):
                if field_name not in boundary_values:
                    continue
                for row in _boundary_signal_rows(rows, boundary_id, field_name):
                    sample = {**sample_base, "value": boundary_values[field_name]}
                    _record_runtime_scalar(
                        stages,
                        all_signal_names,
                        stage_id=str(row.get("stage") or "board_control"),
                        signal=str(row["expression"]),
                        sample=sample,
                    )
                    scalar_count += 1

        for section_name, section in observed.items():
            if not isinstance(section, dict):
                continue
            if section_name in _BOUNDARY_STAGE_IDS:
                stage_id = section_name
                for field_name, value in section.items():
                    if isinstance(value, (dict, list)):
                        continue
                    matched = [
                        row
                        for row in rows
                        if _signal_row_matches_field(
                            row,
                            stage_id=stage_id,
                            field_name=str(field_name),
                        )
                    ]
                    if not matched:
                        unmapped[f"{stage_id}.{field_name}"] += 1
                        continue
                    for row in matched:
                        _record_runtime_scalar(
                            stages,
                            all_signal_names,
                            stage_id=stage_id,
                            signal=str(row["expression"]),
                            sample={**sample_base, "value": value},
                        )
                        scalar_count += 1
                continue

            if section_name not in {"adapter", "axi"}:
                continue
            for field_name, value in section.items():
                if isinstance(value, (dict, list)):
                    continue
                matched = [
                    row
                    for row in rows
                    if _signal_row_matches_field(
                        row,
                        stage_id=None,
                        field_name=str(field_name),
                    )
                    and (
                        section_name == "axi"
                        and str(row.get("stage") or "") == "axi_ddr"
                        or section_name == "adapter"
                        and str(row.get("stage") or "")
                        in {"board_control", "board_output", "runtime_loader", "weight_loader"}
                    )
                ]
                if not matched:
                    unmapped[f"{section_name}.{field_name}"] += 1
                    continue
                for row in matched:
                    _record_runtime_scalar(
                        stages,
                        all_signal_names,
                        stage_id=str(row.get("stage") or "board_control"),
                        signal=str(row["expression"]),
                        sample={**sample_base, "value": value},
                    )
                    scalar_count += 1
    return {
        "status": "ready" if parsed.get("records") else parsed.get("status", "empty"),
        "record_count": len(parsed.get("records", [])),
        "invalid_record_count": len(parsed.get("invalid_records", [])),
        "recovered_nonstandard_json_count": recovered,
        "merged_scalar_sample_count": scalar_count,
        "unmapped_scalar_count": sum(unmapped.values()),
        "unmapped_scalar_fields": sorted(unmapped)[:128],
    }


def summarize_runtime_stage_trace_log(
    path: Path,
    *,
    boundary_trace_path: Path | None = None,
    selection_path: Path | None = None,
) -> dict[str, Any]:
    """Compact all current-run internal stage signals from a VCS text log.

    The testbench emits one line per selected scalar at meaningful transitions.
    A full run can therefore contain hundreds of thousands of rows.  This
    reader processes the file line-by-line and keeps every non-vector control
    signal while collapsing ``...[bit].known`` probes into one vector summary.
    It is diagnostic evidence only and never changes functional acceptance.
    """

    summary: dict[str, Any] = {
        "schema_version": "spatialaccagent.runtime_stage_trace_summary.v1",
        "status": "missing" if not path.is_file() else "ready",
        "raw_stage_record_count": 0,
        "parsed_stage_record_count": 0,
        "unparsed_stage_record_count": 0,
        "distinct_signal_count": 0,
        "stage_count": 0,
        "stage_summaries": [],
        "boundary_trace_merge": {
            "status": "not_requested",
            "record_count": 0,
            "merged_scalar_sample_count": 0,
        },
        "policy": {
            "current_log_only": True,
            "all_non_vector_scalar_signals_retained": True,
            "known_bit_vectors_are_grouped_without_raw_payload_values": True,
            "raw_trace_rows_are_not_embedded": True,
        },
    }
    if not path.is_file():
        return summary

    stages: dict[str, dict[str, Any]] = {}
    all_signal_names: set[str] = set()
    with path.open("r", encoding="utf-8", errors="replace") as stream:
        for line in stream:
            if "SPATIALACC_STAGE_TRACE" not in line:
                continue
            summary["raw_stage_record_count"] += 1
            record = parse_stage_trace_line(line)
            if record is None:
                summary["unparsed_stage_record_count"] += 1
                continue
            summary["parsed_stage_record_count"] += 1
            stage_id = str(record["stage_id"])
            signal = str(record["signal"])
            all_signal_names.add(signal)
            stage = stages.setdefault(
                stage_id,
                {
                    "record_count": 0,
                    "first_cycle": None,
                    "last_cycle": None,
                    "event_counts": Counter(),
                    "scalar_signals": {},
                    "known_bit_vectors": {},
                },
            )
            vector_match = STAGE_TRACE_VECTOR_KNOWN_RE.match(signal)
            if vector_match is None:
                _record_runtime_scalar(
                    stages,
                    all_signal_names,
                    stage_id=stage_id,
                    signal=signal,
                    sample=_stage_trace_sample(record),
                )
                continue

            base = vector_match.group("base")
            index = int(vector_match.group("index"))
            vector = stage["known_bit_vectors"].setdefault(
                base,
                {
                    "sample_count": 0,
                    "change_count": 0,
                    "first_sample": None,
                    "last_sample": None,
                    "last_change": None,
                    "bits": {},
                },
            )
            sample = _stage_trace_sample(record)
            bit = vector["bits"].setdefault(
                index,
                {"last_value": None, "last_sample": None},
            )
            if bit["last_sample"] is not None and bit["last_value"] != sample["value"]:
                vector["change_count"] += 1
                vector["last_change"] = sample
            bit["last_value"] = sample["value"]
            bit["last_sample"] = sample
            if vector["first_sample"] is None:
                vector["first_sample"] = sample
            vector["sample_count"] += 1
            vector["last_sample"] = sample

    if boundary_trace_path is not None and boundary_trace_path.is_file():
        summary["boundary_trace_merge"] = _merge_boundary_trace_scalars(
            stages,
            all_signal_names,
            boundary_trace_path,
            selection_path,
        )

    selected_rows = _load_runtime_signal_rows(selection_path)
    selected_expressions = {
        str(row.get("expression"))
        for row in selected_rows
        if row.get("expression")
    }
    observed_expressions = set(all_signal_names)
    missing_selected = sorted(selected_expressions - observed_expressions)
    summary["selected_signal_coverage"] = {
        "selection_path": str(selection_path) if selection_path else None,
        "selected_signal_count": len(selected_expressions),
        "observed_selected_signal_count": len(
            selected_expressions & observed_expressions
        ),
        "missing_selected_signal_count": len(missing_selected),
        "coverage_ratio": (
            len(selected_expressions & observed_expressions)
            / len(selected_expressions)
            if selected_expressions
            else None
        ),
        "missing_selected_signals": missing_selected[:256],
    }

    stage_summaries: list[dict[str, Any]] = []
    for stage_id in sorted(stages):
        stage = stages[stage_id]
        scalar_signals = [
            {"signal": signal, **stats}
            for signal, stats in sorted(stage["scalar_signals"].items())
        ]
        known_bit_signal_count = sum(
            len(stats["bits"])
            for stats in stage["known_bit_vectors"].values()
        )
        vectors: list[dict[str, Any]] = []
        for signal, stats in sorted(stage["known_bit_vectors"].items()):
            bits = stats["bits"]
            indices = sorted(bits)
            width = indices[-1] + 1 if indices else 0
            unknown_indices = [
                index
                for index in indices
                if not _value_is_known(bits[index]["last_value"])
            ]
            observed_bit_count = len(indices)
            vectors.append(
                {
                    "signal": signal,
                    "width": width,
                    "observed_bit_count": observed_bit_count,
                    "unobserved_bit_count": max(width - observed_bit_count, 0),
                    "known_bit_count": observed_bit_count - len(unknown_indices),
                    "unknown_bit_count": len(unknown_indices),
                    "unknown_bit_ranges": _integer_ranges(unknown_indices),
                    "sample_count": stats["sample_count"],
                    "change_count": stats["change_count"],
                    "first_sample": stats["first_sample"],
                    "last_sample": stats["last_sample"],
                    "last_change": stats["last_change"],
                }
            )
        stage_summaries.append(
            {
                "stage_id": stage_id,
                "record_count": stage["record_count"],
                "distinct_signal_count": len(stage["scalar_signals"])
                + known_bit_signal_count,
                "scalar_signal_count": len(scalar_signals),
                "known_bit_vector_count": len(vectors),
                "first_cycle": stage["first_cycle"],
                "last_cycle": stage["last_cycle"],
                "event_counts": dict(sorted(stage["event_counts"].items())),
                "scalar_signals": scalar_signals,
                "known_bit_vectors": vectors,
            }
        )
    summary["distinct_signal_count"] = len(all_signal_names)
    summary["stage_count"] = len(stage_summaries)
    summary["stage_summaries"] = stage_summaries
    return summary


def stage_internal_records_from_boundary_observations(
    records: list[dict[str, Any]],
    authority: dict[str, Any],
) -> list[dict[str, Any]]:
    """Project stage snapshots already present in boundary records.

    Some generated testbenches write all stage-local scalar values into their
    existing JSON boundary records instead of duplicating them as console
    lines.  Treat those snapshots as the same read-only stage evidence so the
    repair loop can use every declared internal signal from the current run.
    """

    required_rows = authority.get("required_stages", [])
    required_rows = required_rows if isinstance(required_rows, list) else []
    stage_ids = {
        str(row.get("stage_id") or "")
        for row in required_rows
        if isinstance(row, dict) and str(row.get("stage_id") or "")
    }
    if not stage_ids:
        return []

    projected: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        observed = record.get("observed_value")
        observed = observed if isinstance(observed, dict) else {}
        cycle = record.get("cycle")
        token = record.get("token", record.get("logical_index"))
        beat = record.get("beat")
        event = str(
            observed.get("event")
            or record.get("status")
            or record.get("boundary_id")
            or "snapshot"
        )
        for stage_id in sorted(stage_ids):
            values = observed.get(stage_id)
            if not isinstance(values, dict):
                continue
            for signal, value in values.items():
                if not isinstance(signal, str) or not signal:
                    continue
                if isinstance(value, (dict, list)):
                    continue
                projected.append(
                    {
                        "schema_version": PIPELINE_STAGE_TRACE_SCHEMA_VERSION,
                        "stage_id": stage_id,
                        "cycle": cycle,
                        "token": token,
                        "beat": beat,
                        "event": event,
                        "signal": signal,
                        "value": value,
                        "source": "boundary_trace_stage_snapshot",
                    }
                )
    return projected


def summarize_stage_internal_observations(
    records: list[dict[str, Any]],
    authority: dict[str, Any],
) -> dict[str, Any]:
    """Summarize sparse scalar observations emitted from inside each stage.

    Stage records are diagnostic evidence only.  The summary keeps every
    signal name and groups values emitted at the same transition, while the
    boundary summary remains the authority for functional completion.
    """

    required_rows = authority.get("required_stages", [])
    required_rows = required_rows if isinstance(required_rows, list) else []
    required_ids = [
        str(row.get("stage_id") or "")
        for row in required_rows
        if isinstance(row, dict) and str(row.get("stage_id") or "")
    ]
    by_stage: dict[str, list[dict[str, Any]]] = {}
    invalid_count = 0
    for row in records:
        if not isinstance(row, dict):
            invalid_count += 1
            continue
        stage_id = str(row.get("stage_id") or "")
        signal = str(row.get("signal") or "")
        if not stage_id or not signal:
            invalid_count += 1
            continue
        by_stage.setdefault(stage_id, []).append(row)

    summaries: list[dict[str, Any]] = []
    for row in required_rows:
        if not isinstance(row, dict):
            continue
        stage_id = str(row.get("stage_id") or "")
        stage_rows = by_stage.get(stage_id, [])
        grouped: dict[tuple[Any, Any, Any, Any], dict[str, Any]] = {}
        signal_names: set[str] = set()
        token_ids: set[int] = set()
        for stage_row in stage_rows:
            signal = str(stage_row.get("signal") or "")
            signal_names.add(signal)
            token = stage_row.get("token")
            if isinstance(token, int) and not isinstance(token, bool):
                token_ids.add(token)
            key = (
                stage_row.get("cycle"),
                stage_row.get("token"),
                stage_row.get("beat"),
                stage_row.get("event"),
            )
            snapshot = grouped.setdefault(
                key,
                {
                    "cycle": key[0],
                    "token": key[1],
                    "beat": key[2],
                    "event": key[3],
                    "signals": {},
                },
            )
            snapshot["signals"][signal] = stage_row.get("value")
        snapshots = list(grouped.values())
        snapshots.sort(
            key=lambda item: (
                item.get("cycle") if isinstance(item.get("cycle"), int) else -1,
                item.get("token") if isinstance(item.get("token"), int) else -1,
                item.get("beat") if isinstance(item.get("beat"), int) else -1,
                str(item.get("event") or ""),
            )
        )
        summaries.append(
            {
                "stage_id": stage_id,
                "input_boundary_ids": list(row.get("input_boundary_ids", [])),
                "output_boundary_ids": list(row.get("output_boundary_ids", [])),
                "record_count": len(stage_rows),
                "signal_count": len(signal_names),
                "signal_names": sorted(signal_names),
                "token_ids": sorted(token_ids),
                "first_cycle": snapshots[0].get("cycle") if snapshots else None,
                "last_cycle": snapshots[-1].get("cycle") if snapshots else None,
                "snapshots": snapshots,
                "observed": bool(stage_rows),
            }
        )
    observed_ids = set(by_stage)
    return {
        "schema_version": PIPELINE_STAGE_TRACE_SCHEMA_VERSION,
        "status": "ready" if required_ids else "not_applicable",
        "required_stage_count": len(required_ids),
        "observed_stage_count": len(set(required_ids) & observed_ids),
        "missing_stage_ids": sorted(set(required_ids) - observed_ids),
        "unexpected_stage_ids": sorted(observed_ids - set(required_ids)),
        "record_count": len(records),
        "invalid_record_count": invalid_count,
        "stage_summaries": summaries,
        "policy": {
            "diagnostic_only": True,
            "all_declared_scalar_signal_names_are_retained": True,
            "records_are_sparse_transition_records": True,
            "boundary_trace_stage_snapshots_are_accepted": True,
            "raw_payload_vectors_and_every_cycle_waveforms_are_not_required": True,
        },
    }


def _json_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    import hashlib

    return hashlib.sha256(payload).hexdigest()


def pipeline_boundary_observation_authority(
    semantic_manifest: dict[str, Any],
    *,
    semantic_manifest_path: Path | None = None,
    testbench_source: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Derive the current model's complete boundary-monitoring authority.

    The source is the current semantic pipeline contract.  No stage or
    boundary name is embedded here, so a different model can supply a
    different DAG without changing framework code.
    """

    single_layer = semantic_manifest.get("single_layer", {})
    single_layer = single_layer if isinstance(single_layer, dict) else {}
    contract = single_layer.get("pipeline_overlap_contract", {})
    contract = contract if isinstance(contract, dict) else {}
    trace_contract = contract.get("trace_contract", {})
    trace_contract = trace_contract if isinstance(trace_contract, dict) else {}
    expected_token_count = contract.get("token_count")
    if not isinstance(expected_token_count, int) or isinstance(
        expected_token_count, bool
    ) or expected_token_count <= 0:
        expected_token_count = trace_contract.get("token_count")
    if not isinstance(expected_token_count, int) or isinstance(
        expected_token_count, bool
    ) or expected_token_count <= 0:
        expected_token_count = None
    expected_beats_per_token = contract.get("beats_per_token")
    if not isinstance(expected_beats_per_token, int) or isinstance(
        expected_beats_per_token, bool
    ) or expected_beats_per_token <= 0:
        expected_beats_per_token = trace_contract.get("beats_per_token")
    if not isinstance(expected_beats_per_token, int) or isinstance(
        expected_beats_per_token, bool
    ) or expected_beats_per_token <= 0:
        expected_beats_per_token = None
    raw_boundaries = contract.get("boundary_contracts", [])
    raw_boundaries = raw_boundaries if isinstance(raw_boundaries, list) else []
    boundaries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in raw_boundaries:
        if not isinstance(row, dict):
            continue
        boundary_id = str(row.get("boundary_id") or "").strip()
        if not boundary_id or boundary_id in seen:
            continue
        seen.add(boundary_id)
        boundaries.append(
            {
                "boundary_id": boundary_id,
                "src_stage": str(row.get("src_stage") or ""),
                "dst_stage": str(row.get("dst_stage") or ""),
                "kind": str(row.get("kind") or ""),
                "flow_control": str(row.get("flow_control") or ""),
                "beats_per_token": row.get("beats_per_token"),
                "required_fields": list(PIPELINE_BOUNDARY_OBSERVATION_FIELDS),
                "optional_diagnostic_fields": list(
                    PIPELINE_BOUNDARY_DIAGNOSTIC_FIELDS
                ),
                "read_only": True,
                "unavailable_reason_required": True,
            }
        )
    required_ids = [
        str(value).strip()
        for value in contract.get("required_boundaries", [])
        if str(value).strip()
    ]
    if required_ids:
        required_set = set(required_ids)
        boundaries = [row for row in boundaries if row["boundary_id"] in required_set]
        missing_contract_rows = [value for value in required_ids if value not in seen]
    else:
        missing_contract_rows = []

    source_stage_ids = {
        str(row.get("src_stage") or "")
        for row in boundaries
        if str(row.get("src_stage") or "")
    }
    sink_stage_ids = {
        str(row.get("dst_stage") or "")
        for row in boundaries
        if str(row.get("dst_stage") or "")
    }
    compute_stage_ids = (source_stage_ids & sink_stage_ids)
    required_stages = [
        {
            "stage_id": stage_id,
            "input_boundary_ids": sorted(
                str(row.get("boundary_id") or "")
                for row in boundaries
                if row.get("dst_stage") == stage_id
            ),
            "output_boundary_ids": sorted(
                str(row.get("boundary_id") or "")
                for row in boundaries
                if row.get("src_stage") == stage_id
            ),
        }
        for stage_id in sorted(compute_stage_ids)
    ]

    source = testbench_source if isinstance(testbench_source, dict) else {}
    authority = {
        "schema_version": PIPELINE_BOUNDARY_OBSERVATION_SCHEMA_VERSION,
        "status": "ready" if boundaries and not missing_contract_rows else "unavailable",
        "source": {
            "semantic_manifest_path": str(semantic_manifest_path)
            if semantic_manifest_path is not None
            else None,
            "semantic_manifest_sha256": (
                _file_sha256(semantic_manifest_path)
                if semantic_manifest_path is not None and semantic_manifest_path.is_file()
                else None
            ),
            "pipeline_overlap_contract_sha256": contract.get("contract_sha256"),
            "trace_contract_sha256": contract.get("trace_contract_sha256"),
            "pipeline_plan_sha256": contract.get("pipeline_plan_sha256"),
            "testbench_source_id": source.get("source_id"),
            "testbench_source_sha256": source.get("sha256")
            or source.get("local_sha256"),
        },
        "required_boundaries": boundaries,
        "required_stages": required_stages,
        "required_fields": list(PIPELINE_BOUNDARY_OBSERVATION_FIELDS),
        "optional_diagnostic_fields": list(PIPELINE_BOUNDARY_DIAGNOSTIC_FIELDS),
        "expected_token_count": expected_token_count,
        "expected_beats_per_token": expected_beats_per_token,
        "missing_contract_rows": missing_contract_rows,
        "record_policy": {
            "capture": "per_token_first_last_and_waiting_summary",
            "keep_first_and_last_accepted_record_per_token": True,
            "keep_first_and_last_accepted_record_per_boundary": True,
            "max_records_per_boundary_in_summary": MAX_BOUNDARY_OBSERVATION_RECORDS,
            "token_count_is_read_from_current_model_contract": True,
            "zero_transfer_requires_first_waiting_after_upstream_progress": True,
            "zero_transfer_requires_final_waiting_or_summary": True,
            "unbounded_waveform_not_required": True,
            "extra_internal_signal_snapshots_are_optional": True,
            "stage_internal_signal_plan_required": True,
            "stage_plan_covers_every_current_compute_stage": True,
            "stage_plan_signal_count_has_no_fixed_upper_bound": True,
            "retain_all_declared_key_scalar_signals": True,
            "retain_all_emitted_boundary_transition_snapshots": True,
            "extra_signals_do_not_change_functional_acceptance": True,
            "observation_only": True,
            "no_dut_signal_drive": True,
            "no_synthesizable_state_or_ports": True,
        },
        "plain_language": {
            "boundary": "相邻计算阶段之间的数据通路",
            "valid": "发送方有数据",
            "ready": "接收方可以接收",
            "fire": "本周期确实完成一次传输",
            "accepted_count": "已经接收的数据次数",
            "first_accepted_payload_digest": "第一条数据的摘要",
            "last_accepted_payload_digest": "最后一条数据的摘要",
            "extra_signal_snapshot": "同一数据边界附近的少量内部状态、队列、缓冲、调度或 AXI 信号摘要",
            "stage_internal_signal_plan": "每个计算阶段内部可见信号的观测计划",
            "stage_internal_snapshot": "每个计算阶段在关键时刻的内部标量信号快照",
        },
    }
    authority["authority_sha256"] = _json_sha256(authority)
    return authority


def _file_sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _bool_signal(row: dict[str, Any], key: str) -> bool | None:
    value = row.get(key)
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    return None


def _normalized_boundary_key(value: str) -> str:
    """Compare independently-produced trace IDs without model-specific aliases."""

    normalized = value.lower().strip()
    if normalized.startswith("boundary."):
        normalized = normalized[len("boundary.") :]
    return "".join(
        character if character.isalnum() else "_" for character in normalized
    ).strip("_")


def _normalized_boundary_trace_row(row: dict[str, Any]) -> dict[str, Any]:
    """Lift common JSONL trace payload fields without depending on a DUT name."""

    normalized = dict(row)
    observed = row.get("observed_value")
    if not isinstance(observed, dict):
        return normalized
    for key in (
        "valid",
        "ready",
        "fire",
        "accepted_count",
        "payload_digest",
        "first_accepted_payload_digest",
        "last_accepted_payload_digest",
        "first_accepted_payload_seen",
        "last_accepted_payload_seen",
        "first_accepted_payload_digest_unknown",
        "last_accepted_payload_digest_unknown",
        "payload_unknown",
    ):
        if key in observed and key not in normalized:
            normalized[key] = observed[key]
    endpoint_aliases = {
        "valid": ("core_egress_valid", "output_valid"),
        "ready": ("core_egress_ready", "output_ready"),
        "accepted_count": (
            "core_egress_accepted_count",
            "output_accept_count",
            "output_accepted_count",
        ),
    }
    for canonical, aliases in endpoint_aliases.items():
        if canonical in normalized:
            continue
        for alias in aliases:
            if alias in observed:
                normalized[canonical] = observed[alias]
                break
    if "payload_digest" not in normalized and "current_payload_digest" in observed:
        normalized["payload_digest"] = observed["current_payload_digest"]
    if "payload_unknown" not in normalized and "current_payload_unknown" in observed:
        normalized["payload_unknown"] = observed["current_payload_unknown"]
    if "fire" not in normalized:
        valid = _bool_signal(normalized, "valid")
        ready = _bool_signal(normalized, "ready")
        if valid is not None and ready is not None:
            normalized["fire"] = valid and ready
    if "payload_digest" not in normalized:
        digest_keys = sorted(
            key
            for key, value in observed.items()
            if isinstance(value, str) and key.endswith("payload_digest")
        )
        if digest_keys:
            normalized["payload_digest"] = observed[digest_keys[0]]
    return normalized


def _payload_digest(row: dict[str, Any]) -> str | None:
    if row.get("payload_unknown") is True:
        return None
    for key in (
        "payload_digest",
        "data_digest",
        "accepted_payload_digest",
    ):
        value = row.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _explicit_accepted_payload_digest(
    rows: list[dict[str, Any]],
    *,
    position: str,
) -> str | None:
    key = f"{position}_accepted_payload_digest"
    unknown_key = f"{key}_unknown"
    ordered_rows = rows if position == "first" else reversed(rows)
    for row in ordered_rows:
        value = row.get(key)
        if (
            isinstance(value, str)
            and value
            and row.get(unknown_key) is not True
        ):
            return value
    return None


def _explicit_accepted_payload_observation(
    rows: list[dict[str, Any]],
    *,
    position: str,
) -> tuple[bool, bool]:
    key = f"{position}_accepted_payload_digest"
    seen_key = f"{position}_accepted_payload_seen"
    unknown_key = f"{key}_unknown"
    ordered_rows = rows if position == "first" else reversed(rows)
    for row in ordered_rows:
        if row.get(seen_key) is True or key in row:
            return True, row.get(unknown_key) is True
    return False, False


def _boundary_record_snapshot(row: dict[str, Any]) -> dict[str, Any]:
    """Keep only scalar, bounded evidence from one trace record."""

    keys = (
        "schema_version",
        "cycle",
        "boundary_id",
        "token",
        "beat",
        "valid",
        "ready",
        "fire",
        "accepted_count",
        "received_count",
        "start",
        "last",
        "payload_digest",
        "data_digest",
        "accepted_payload_digest",
        "current_payload_unknown",
        "current_payload_digest",
        "waiting_after_upstream_progress",
        "status",
    )
    return {key: row[key] for key in keys if key in row}


def _trace_row_order(row: dict[str, Any], fallback: int) -> tuple[int, int]:
    """Order records by simulation cycle, then preserve input order."""

    cycle = row.get("cycle")
    if isinstance(cycle, int) and not isinstance(cycle, bool):
        return cycle, fallback
    sequence = row.get("sequence")
    if isinstance(sequence, int) and not isinstance(sequence, bool):
        return sequence, fallback
    return fallback, fallback


def _row_observation_phase(row: dict[str, Any]) -> str:
    value = row.get("observation_phase")
    if not isinstance(value, str):
        observed = row.get("observed_value")
        value = observed.get("observation_phase") if isinstance(observed, dict) else ""
    return str(value or "").strip().lower()


def _row_status(row: dict[str, Any]) -> str:
    return str(row.get("status") or "").strip().lower()


def _payload_observation(row: dict[str, Any]) -> tuple[bool, bool, str | None]:
    """Return (seen, unknown, digest) for a single transfer record."""

    digest = _payload_digest(row)
    if digest is not None:
        return True, False, digest
    if row.get("payload_unknown") is True:
        return True, True, None
    return False, False, None


_DIAGNOSTIC_METADATA_FIELDS = {
    "probe_id",
    "probe_revision",
    "source_marker",
    "observational_only",
    "coverage_status",
    "availability",
    "required_coverage",
    "event",
}


def _diagnostic_scalar(value: Any) -> Any | None:
    """Keep a JSON-safe scalar without retaining full data payloads."""

    if isinstance(value, bool):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, float):
        return value
    if isinstance(value, str):
        return value[:128]
    return None


def _diagnostic_signal_values(row: dict[str, Any]) -> dict[str, Any]:
    """Flatten all declared read-only scalar trace values from one record.

    Testbench probes can expose different internal names for different models.
    The parser keeps the Agent-selected scalar values generically instead of
    embedding MLP-, FIFO-, or board-specific names in the framework.
    """

    values: dict[str, Any] = {}

    def add(name: str, value: Any) -> None:
        if not name or name in _DIAGNOSTIC_METADATA_FIELDS or name in values:
            return
        scalar = _diagnostic_scalar(value)
        if scalar is not None:
            values[name] = scalar

    for key in (
        *PIPELINE_BOUNDARY_OBSERVATION_FIELDS[:4],
        *PIPELINE_BOUNDARY_DIAGNOSTIC_FIELDS,
        "scheduler_state",
        "layer",
        "active_weight_bank",
        "preload_weight_bank",
        "activation_read_bank",
        "activation_write_bank",
    ):
        if key in row:
            add(key, row[key])

    sources = {
        "observed_value": row.get("observed_value"),
        "active_boundary_observation": row.get("active_boundary_observation"),
        "prefetch_progress": row.get("prefetch_progress"),
        "runtime_load_progress": row.get("runtime_load_progress"),
        "final_writeback_progress": row.get("final_writeback_progress"),
        "axi_read": row.get("axi_read"),
        "axi_write": row.get("axi_write"),
    }
    for source_name, observed in sources.items():
        if not isinstance(observed, dict):
            continue
        for key, value in observed.items():
            if key in _DIAGNOSTIC_METADATA_FIELDS:
                continue
            prefix = "" if source_name == "observed_value" else f"{source_name}."
            if isinstance(value, dict):
                for child_key, child_value in value.items():
                    add(f"{prefix}{key}.{child_key}", child_value)
            else:
                add(f"{prefix}{key}", value)
    return values


def _diagnostic_snapshot(
    row: dict[str, Any],
    *,
    snapshot_kind: str,
) -> dict[str, Any]:
    """Create one compact internal-state snapshot for Agent analysis."""

    snapshot = {
        "snapshot_kind": snapshot_kind,
        "cycle": row.get("cycle"),
        "token": row.get("token"),
        "beat": row.get("beat"),
        "event": (
            row.get("event")
            if isinstance(row.get("event"), str)
            else (
                row.get("observed_value", {}).get("event")
                if isinstance(row.get("observed_value"), dict)
                else None
            )
        ),
        "status": row.get("status"),
        "observation_phase": _row_observation_phase(row) or None,
        "signals": _diagnostic_signal_values(row),
    }
    return {key: value for key, value in snapshot.items() if value is not None}


def _bounded_diagnostic_snapshots(
    rows: list[dict[str, Any]],
    accepted: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Retain every emitted key transition without retaining a waveform.

    The testbench itself is responsible for emitting first/last token beats,
    waiting transitions, state changes, and terminal records. These records
    are already sparse. Dropping any of them in the Python summary hides
    exactly the internal change that the Agent requested to inspect.
    """

    accepted_ids = {id(row) for row in accepted}
    candidates: list[tuple[str, dict[str, Any]]] = []
    for row in rows:
        phase = _row_observation_phase(row)
        status = _row_status(row)
        waiting = row.get("waiting_after_upstream_progress") is True or (
            isinstance(row.get("observed_value"), dict)
            and row["observed_value"].get("waiting_after_upstream_progress")
            is True
        )
        if status in {"terminal", "fail", "stalled", "warning"} or phase in {
            "final_waiting_summary",
            "terminal_summary",
            "terminal",
            "stalled",
        }:
            snapshot_kind = "terminal"
        elif waiting:
            snapshot_kind = "waiting"
        elif id(row) in accepted_ids:
            snapshot_kind = "transfer"
        else:
            snapshot_kind = "state_change"
        candidates.append((snapshot_kind, row))

    snapshots: list[dict[str, Any]] = []
    seen: set[int] = set()
    for snapshot_kind, row in candidates:
        if id(row) in seen:
            continue
        seen.add(id(row))
        snapshot = _diagnostic_snapshot(row, snapshot_kind=snapshot_kind)
        if snapshot.get("signals"):
            snapshots.append(snapshot)
    return snapshots


def _per_token_boundary_coverage(
    accepted: list[dict[str, Any]],
    *,
    expected_token_count: int | None,
    expected_beats_per_token: int | None,
) -> dict[str, Any]:
    """Check token edge coverage without retaining an unbounded waveform."""

    if expected_token_count is None:
        return {
            "status": "not_bound",
            "complete": True,
            "expected_token_count": None,
            "expected_beats_per_token": expected_beats_per_token,
            "observed_token_ids": [],
            "missing_token_ids": [],
            "unexpected_token_ids": [],
            "token_summaries": [],
        }

    by_token: dict[int, list[dict[str, Any]]] = {}
    unexpected: set[int] = set()
    missing_token_metadata_count = 0
    for row in accepted:
        token = row.get("token")
        if not isinstance(token, int) or isinstance(token, bool):
            missing_token_metadata_count += 1
            continue
        if 0 <= token < expected_token_count:
            by_token.setdefault(token, []).append(row)
        else:
            unexpected.add(token)

    required_record_fields = (
        "token",
        "beat",
        "valid",
        "ready",
        "fire",
        "accepted_count",
    )
    token_summaries: list[dict[str, Any]] = []
    incomplete: list[int] = []
    completed: list[int] = []
    partial: list[int] = []
    for token in sorted(by_token):
        rows = sorted(by_token.get(token, []), key=lambda row: _trace_row_order(row, 0))
        first = rows[0] if rows else None
        last = rows[-1] if rows else None
        first_seen, first_unknown, first_digest = (
            _payload_observation(first) if first else (False, False, None)
        )
        last_seen, last_unknown, last_digest = (
            _payload_observation(last) if last else (False, False, None)
        )
        first_beat = first.get("beat") if first else None
        last_beat = last.get("beat") if last else None
        first_fields_present = bool(
            first and all(field in first for field in required_record_fields)
        )
        last_fields_present = bool(
            last and all(field in last for field in required_record_fields)
        )
        complete = bool(
            len(rows) >= (2 if (expected_beats_per_token or 0) > 1 else 1)
            and first_fields_present
            and last_fields_present
            and first_seen
            and last_seen
            and isinstance(first_beat, int)
            and not isinstance(first_beat, bool)
            and isinstance(last_beat, int)
            and not isinstance(last_beat, bool)
            and (first_beat == 0 if expected_beats_per_token is not None else True)
        )
        if not complete:
            incomplete.append(token)
        if (
            expected_beats_per_token is not None
            and last_beat == expected_beats_per_token - 1
        ):
            completed.append(token)
        elif complete:
            partial.append(token)
        token_summaries.append(
            {
                "token": token,
                "accepted_record_count": len(rows),
                "first_accepted_record": _boundary_record_snapshot(first)
                if first
                else None,
                "last_accepted_record": _boundary_record_snapshot(last)
                if last
                else None,
                "first_accepted_beat": first_beat,
                "last_accepted_beat": last_beat,
                "first_accepted_payload_digest": first_digest,
                "last_accepted_payload_digest": last_digest,
                "first_accepted_payload_unknown": first_unknown,
                "last_accepted_payload_unknown": last_unknown,
                "complete": complete,
            }
        )
    coverage_complete = bool(
        not incomplete
        and not unexpected
        and missing_token_metadata_count == 0
        and (bool(by_token) or not accepted)
    )
    return {
        "status": "complete" if coverage_complete else "incomplete",
        "complete": coverage_complete,
        "expected_token_count": expected_token_count,
        "expected_beats_per_token": expected_beats_per_token,
        "observed_token_ids": sorted(by_token),
        "absent_token_ids": sorted(set(range(expected_token_count)) - set(by_token)),
        "incomplete_observed_token_ids": incomplete,
        "missing_token_ids": incomplete,
        "completed_token_ids": completed,
        "partial_token_ids": partial,
        "unexpected_token_ids": sorted(unexpected),
        "transfer_records_missing_token_metadata": missing_token_metadata_count,
        "token_summaries": token_summaries,
    }


def summarize_pipeline_boundary_observations(
    records: list[dict[str, Any]],
    authority: dict[str, Any],
    declaration: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Summarize every current-DAG boundary using bounded trace evidence."""

    authority_status = str(authority.get("status") or "unavailable")
    required_rows = authority.get("required_boundaries", [])
    required_rows = required_rows if isinstance(required_rows, list) else []
    required = {
        _normalized_boundary_key(str(row.get("boundary_id"))): row
        for row in required_rows
        if isinstance(row, dict) and str(row.get("boundary_id") or "")
    }
    declared_rows = (
        declaration.get("pipeline_boundary_observations")
        if isinstance(declaration, dict)
        else []
    )
    declared_rows = declared_rows if isinstance(declared_rows, list) else []
    unavailable: dict[str, str] = {}
    for row in declared_rows:
        if not isinstance(row, dict):
            continue
        boundary_id = _normalized_boundary_key(str(row.get("boundary_id") or ""))
        reason = str(row.get("unavailable_reason") or "").strip()
        if boundary_id and reason:
            unavailable[boundary_id] = reason

    by_boundary: dict[str, list[dict[str, Any]]] = {}
    unexpected: set[str] = set()
    invalid_rows = 0
    for row in records:
        if not isinstance(row, dict):
            invalid_rows += 1
            continue
        normalized_row = _normalized_boundary_trace_row(row)
        boundary_id = _normalized_boundary_key(
            str(normalized_row.get("boundary_id") or "")
        )
        if not boundary_id:
            invalid_rows += 1
            continue
        if boundary_id not in required:
            unexpected.add(str(normalized_row.get("boundary_id") or ""))
            continue
        by_boundary.setdefault(boundary_id, []).append(normalized_row)

    boundary_summaries: list[dict[str, Any]] = []
    expected_token_count = authority.get("expected_token_count")
    expected_token_count = (
        expected_token_count
        if isinstance(expected_token_count, int)
        and not isinstance(expected_token_count, bool)
        and expected_token_count > 0
        else None
    )
    expected_beats_per_token = authority.get("expected_beats_per_token")
    expected_beats_per_token = (
        expected_beats_per_token
        if isinstance(expected_beats_per_token, int)
        and not isinstance(expected_beats_per_token, bool)
        and expected_beats_per_token > 0
        else None
    )
    for normalized_id, contract_row in required.items():
        boundary_id = str(contract_row.get("boundary_id") or normalized_id)
        rows = by_boundary.get(normalized_id, [])
        accepted: list[dict[str, Any]] = []
        for row in rows:
            fire = _bool_signal(row, "fire")
            if fire is True or (
                fire is None
                and _bool_signal(row, "valid") is True
                and _bool_signal(row, "ready") is True
            ):
                accepted.append(row)
        accepted_count_values = [
            row.get("accepted_count")
            for row in rows
            if isinstance(row.get("accepted_count"), int)
            and not isinstance(row.get("accepted_count"), bool)
            and row.get("accepted_count") >= 0
        ]
        first = accepted[0] if accepted else (rows[0] if rows else None)
        last = accepted[-1] if accepted else (rows[-1] if rows else None)
        first_payload_observed, first_payload_unknown = (
            _explicit_accepted_payload_observation(rows, position="first")
        )
        first_digest = _explicit_accepted_payload_digest(rows, position="first")
        if first_digest is None and not first_payload_observed:
            first_digest = _payload_digest(first) if first else None
            first_payload_observed = first_digest is not None
        last_payload_observed, last_payload_unknown = (
            _explicit_accepted_payload_observation(rows, position="last")
        )
        last_digest = _explicit_accepted_payload_digest(rows, position="last")
        if last_digest is None and not last_payload_observed:
            last_digest = _payload_digest(last) if last else None
            last_payload_observed = last_digest is not None
        zero_transfers_observed = (
            bool(rows)
            and not accepted
            and bool(accepted_count_values)
            and max(accepted_count_values) == 0
        )
        transfer_observed = bool(accepted)
        # A terminal counter snapshot can describe where a boundary ended, but
        # it does not prove that the board testbench observed the boundary
        # while tokens were moving.  Require a direct transfer event for a
        # boundary that made progress.  A boundary with no transfer needs an
        # explicit post-progress waiting/terminal observation so the Agent can
        # distinguish a real stopped edge from a probe that ran too early.
        temporal_transfer_observed = transfer_observed
        def complete_waiting_record(row: dict[str, Any]) -> bool:
            required_fields = (
                "token",
                "beat",
                "valid",
                "ready",
                "fire",
                "accepted_count",
            )
            payload_seen, _, _ = _payload_observation(row)
            return bool(
                all(field in row for field in required_fields)
                and _bool_signal(row, "fire") is False
                and payload_seen
            )

        first_waiting_rows = [
            row
            for row in rows
            if _row_status(row) in {"waiting", "stall", "stalled", "warning"}
            and _row_observation_phase(row)
            in {
                "waiting_after_upstream_progress",
                "post_upstream_progress_wait",
                "post_input_stall",
            }
            and complete_waiting_record(row)
        ]
        final_waiting_rows = [
            row
            for row in rows
            if _row_status(row) in {"waiting", "stall", "stalled", "warning", "terminal", "fail"}
            and _row_observation_phase(row)
            in {"final_waiting_summary", "terminal_summary", "terminal", "stalled"}
            and complete_waiting_record(row)
        ]
        distinct_waiting_records = bool(
            first_waiting_rows
            and final_waiting_rows
            and first_waiting_rows[0] is not final_waiting_rows[-1]
            and _trace_row_order(first_waiting_rows[0], 0)
            != _trace_row_order(final_waiting_rows[-1], 0)
        )
        temporal_no_transfer_observed = distinct_waiting_records
        zero_transfer_waiting_coverage = {
            "first_waiting_after_upstream_progress": bool(first_waiting_rows),
            "final_waiting_or_summary": bool(final_waiting_rows),
            "records_are_distinct_in_time": distinct_waiting_records,
            "complete": distinct_waiting_records,
            "first_waiting_record": _boundary_record_snapshot(first_waiting_rows[0])
            if first_waiting_rows
            else None,
            "final_waiting_record": _boundary_record_snapshot(final_waiting_rows[-1])
            if final_waiting_rows
            else None,
        }
        temporal_observation_complete = (
            temporal_transfer_observed
            if (accepted_count_values and max(accepted_count_values) > 0)
            or transfer_observed
            else temporal_no_transfer_observed
        )
        token_coverage = _per_token_boundary_coverage(
            accepted,
            expected_token_count=expected_token_count,
            expected_beats_per_token=contract_row.get("beats_per_token")
            if isinstance(contract_row.get("beats_per_token"), int)
            else expected_beats_per_token,
        )
        explicit_accepted_count_max = (
            max(accepted_count_values) if accepted_count_values else None
        )
        # A ready/valid fire proves at least one transfer even when the
        # separately emitted counter snapshot is an earlier zero.  Keep the
        # counter fields exact; expose the lower bound separately instead of
        # pretending that one observed fire is the final accepted count.
        accepted_count_lower_bound = explicit_accepted_count_max
        if transfer_observed:
            accepted_count_lower_bound = max(
                accepted_count_lower_bound or 0,
                1,
            )
        accepted_count_source = (
            "counter_and_ready_valid_fire"
            if transfer_observed and accepted_count_values
            else "ready_valid_fire"
            if transfer_observed
            else "counter_snapshot"
            if accepted_count_values
            else None
        )
        field_coverage = {
            field: any(field in row for row in rows)
            for field in PIPELINE_BOUNDARY_OBSERVATION_FIELDS[:4]
        }
        field_coverage["first_accepted_payload_digest"] = (
            first_payload_observed or zero_transfers_observed
        )
        field_coverage["last_accepted_payload_digest"] = (
            last_payload_observed or zero_transfers_observed
        )
        diagnostic_snapshots = _bounded_diagnostic_snapshots(rows, accepted)
        diagnostic_signal_names = sorted(
            {
                signal_name
                for snapshot in diagnostic_snapshots
                for signal_name in snapshot.get("signals", {})
                if isinstance(signal_name, str)
            }
        )
        boundary_summaries.append(
            {
                "boundary_id": boundary_id,
                "src_stage": contract_row.get("src_stage"),
                "dst_stage": contract_row.get("dst_stage"),
                "kind": contract_row.get("kind"),
                "flow_control": contract_row.get("flow_control"),
                "beats_per_token": contract_row.get("beats_per_token"),
                "trace_record_count": len(rows),
                "accepted_record_count": len(accepted),
                "accepted_count_min": min(accepted_count_values)
                if accepted_count_values
                else None,
                "accepted_count_max": explicit_accepted_count_max,
                "accepted_count_lower_bound": accepted_count_lower_bound,
                "accepted_count_source": accepted_count_source,
                "transfer_observed": transfer_observed,
                "temporal_transfer_observed": temporal_transfer_observed,
                "temporal_no_transfer_observed": temporal_no_transfer_observed,
                "temporal_observation_complete": temporal_observation_complete,
                "zero_transfer_waiting_coverage": zero_transfer_waiting_coverage,
                "token_coverage": token_coverage,
                "field_coverage": field_coverage,
                "first_accepted_payload_digest": first_digest,
                "last_accepted_payload_digest": last_digest,
                "payload_absent_due_to_zero_transfers": zero_transfers_observed,
                "first_accepted_payload_unknown": first_payload_unknown,
                "last_accepted_payload_unknown": last_payload_unknown,
                "payload_unavailable_due_to_unknown_bits": (
                    first_payload_unknown or last_payload_unknown
                ),
                "first_accepted_record": _boundary_record_snapshot(first)
                if first
                else None,
                "last_accepted_record": _boundary_record_snapshot(last)
                if last
                else None,
                "extra_signal_observed": bool(diagnostic_signal_names),
                "extra_signal_names": diagnostic_signal_names,
                "extra_signal_snapshots": diagnostic_snapshots,
                "unavailable_reason": unavailable.get(normalized_id),
                "observation_complete": (
                    bool(rows)
                    and all(field_coverage.values())
                    and temporal_observation_complete
                    and token_coverage.get("complete") is True
                    if rows
                    else bool(unavailable.get(normalized_id))
                ),
            }
        )
    observed_ids = set(by_boundary)
    missing_ids = sorted(
        str(required[value].get("boundary_id") or value)
        for value in set(required) - observed_ids - set(unavailable)
    )
    incomplete_ids = sorted(
        row["boundary_id"]
        for row in boundary_summaries
        if row.get("observation_complete") is not True
    )
    status = (
        "not_applicable"
        if authority_status != "ready"
        else "complete"
        if required and not missing_ids and not incomplete_ids
        else "incomplete"
    )
    return {
        "schema_version": PIPELINE_BOUNDARY_OBSERVATION_SCHEMA_VERSION,
        "status": status,
        "authority_status": authority_status,
        "authority_sha256": authority.get("authority_sha256"),
        "pipeline_overlap_contract_sha256": authority.get("source", {}).get(
            "pipeline_overlap_contract_sha256"
        ),
        "trace_contract_sha256": authority.get("source", {}).get(
            "trace_contract_sha256"
        ),
        "record_count": len(records),
        "invalid_record_count": invalid_rows,
        "required_boundary_count": len(required),
        "observed_boundary_count": len(observed_ids),
        "missing_boundary_ids": missing_ids,
        "unavailable_boundary_ids": sorted(set(unavailable) & set(required)),
        "incomplete_boundary_ids": incomplete_ids,
        "unexpected_boundary_ids": sorted(unexpected)[:MAX_UNEXPECTED_BOUNDARIES],
        "boundary_summaries": boundary_summaries,
        "policy": {
            "summary_is_bounded": True,
            "first_and_last_accepted_records_only": True,
            "accepted_transfer_inference_from_valid_ready_is_legacy_compatible": True,
            "ready_valid_fire_is_independent_transfer_evidence": True,
            "accepted_count_max_preserves_only_explicit_counter_snapshots": True,
            "accepted_count_lower_bound_may_include_observed_fire": True,
            "one_time_counter_snapshot_is_not_temporal_coverage": True,
            "zero_transfer_boundary_requires_explicit_waiting_or_terminal_record": True,
            "zero_transfer_boundary_requires_first_and_final_waiting_records": True,
            "per_token_first_and_last_records_required_when_token_count_is_bound": True,
            "per_token_records_must_include_token_beat_and_payload_observation": True,
            "extra_signal_snapshots_are_bounded_and_diagnostic_only": True,
            "extra_signal_snapshots_do_not_change_observation_completion": True,
            "incomplete_coverage_is_not_pass_evidence": True,
        },
    }


def _nonnegative_int(value: Any) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    return None


def _positive_int(value: Any) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool) and value > 0:
        return value
    return None


def _progress_phase(row: dict[str, Any]) -> str:
    return str(row.get("phase") or "").lower()


def _active_boundary(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("active_boundary_observation")
    return value if isinstance(value, dict) else {}


def _output_accept_count(row: dict[str, Any]) -> int | None:
    return _nonnegative_int(_active_boundary(row).get("output_accept_count"))


def intra_layer_pipeline_violation_evidence(
    records: list[dict[str, Any]],
    progress_contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Prove that a claimed token pipeline produced nothing before input drain."""

    base = {
        "schema_version": "spatialaccagent.intra_layer_pipeline_violation_evidence.v1",
        "status": "observing",
        "failure_class": "intra_layer_spatial_pipeline_violation",
        "fixed_wall_clock_timeout": False,
        "fixed_cycle_timeout": False,
    }
    contract = progress_contract if isinstance(progress_contract, dict) else {}
    pipeline_contract = contract.get("intra_layer_pipeline_contract", {})
    pipeline_contract = (
        pipeline_contract if isinstance(pipeline_contract, dict) else {}
    )
    if (
        pipeline_contract.get("required") is not True
        or pipeline_contract.get("first_output_no_later_than_final_input") is not True
    ):
        return {**base, "status": "unavailable", "reason": "dynamic token-pipeline contract is not bound"}

    target_input = _positive_int(contract.get("target_input_beats"))
    target_output = _positive_int(contract.get("target_output_beats"))
    if target_input is None or target_output is None:
        return {**base, "status": "unavailable", "reason": "target input/output counts are not bound"}
    ordered = [
        row
        for row in records
        if isinstance(row, dict)
        and row.get("schema_version") == BOARD_PROGRESS_EVENT_SCHEMA_VERSION
        and _nonnegative_int(row.get("cycle")) is not None
    ]
    input_complete = [
        row
        for row in ordered
        if row.get("semantic_progress") is True
        and "kernel" in _progress_phase(row)
        and "input" in _progress_phase(row)
        and "token" in _progress_phase(row)
        and "complete" in _progress_phase(row)
        and _nonnegative_int(row.get("token")) is not None
        and _nonnegative_int(row.get("beat")) is not None
    ]
    beats_per_token = max(
        (int(row["beat"]) + 1 for row in input_complete),
        default=0,
    )
    if not beats_per_token or target_input % beats_per_token:
        return {**base, "reason": "complete token-input geometry is not yet observable"}
    expected_tokens = target_input // beats_per_token
    completed_tokens = {int(row["token"]) for row in input_complete}
    if len(completed_tokens) < expected_tokens:
        return {
            **base,
            "reason": "the current layer has not accepted every input token",
            "expected_input_tokens": expected_tokens,
            "completed_input_tokens": len(completed_tokens),
        }
    final_input_cycle = max(int(row["cycle"]) for row in input_complete)
    through_final_input = [
        row for row in ordered if int(row["cycle"]) <= final_input_cycle
    ]
    observed_output_beats = max(
        (
            int(value)
            for row in through_final_input
            if (value := _output_accept_count(row)) is not None
        ),
        default=0,
    )
    output_events = [
        row
        for row in through_final_input
        if row.get("semantic_progress") is True
        and "kernel" in _progress_phase(row)
        and "output" in _progress_phase(row)
        and "token" in _progress_phase(row)
    ]
    first_output_cycle = (
        min(int(row["cycle"]) for row in output_events)
        if output_events
        else None
    )
    if observed_output_beats > 0 or first_output_cycle is not None:
        return {
            **base,
            "status": "contract_not_violated_by_this_observation",
            "reason": "an output transfer was observed no later than final input acceptance",
            "expected_input_tokens": expected_tokens,
            "completed_input_tokens": len(completed_tokens),
            "final_input_cycle": final_input_cycle,
            "first_output_cycle": first_output_cycle,
            "observed_output_beats": observed_output_beats,
            "target_output_beats": target_output,
        }
    final_rows = [
        row for row in through_final_input if int(row["cycle"]) == final_input_cycle
    ]
    output_ready = next(
        (
            _active_boundary(row).get("output_ready")
            for row in reversed(final_rows)
            if _active_boundary(row).get("output_ready") is not None
        ),
        None,
    )
    if output_ready not in {1, True}:
        return {
            **base,
            "reason": "the output boundary was backpressured or unobserved at final input acceptance",
            "final_input_cycle": final_input_cycle,
            "output_ready": output_ready,
        }
    return {
        **base,
        "status": "proven_pipeline_violation",
        "reason": (
            "all current-layer input tokens completed while the ready output boundary "
            "had accepted zero beats"
        ),
        "expected_input_tokens": expected_tokens,
        "completed_input_tokens": len(completed_tokens),
        "beats_per_input_token": beats_per_token,
        "final_input_cycle": final_input_cycle,
        "first_output_cycle": None,
        "observed_output_beats": 0,
        "target_output_beats": target_output,
        "output_ready": output_ready,
        "pipeline_contract": pipeline_contract,
    }


def _frontier_signature(row: dict[str, Any]) -> str:
    """Project only the current output frontier, excluding independent branches."""

    active = _active_boundary(row)
    projection = {
        "scheduler_state": row.get("scheduler_state"),
        "layer": row.get("layer"),
        "token": row.get("token"),
        "active_weight_bank": row.get("active_weight_bank"),
        "activation_read_bank": row.get("activation_read_bank"),
        "activation_write_bank": row.get("activation_write_bank"),
        "output_accept_count": active.get("output_accept_count"),
        "output_ready": active.get("output_ready"),
    }
    return json.dumps(projection, sort_keys=True, separators=(",", ":"))


def _cctg_frontier_stall_evidence(
    records: list[dict[str, Any]],
    progress_contract: dict[str, Any] | None,
) -> dict[str, Any]:
    """Find a certificate-bounded stall at the active CCTG frontier.

    The ordinary adaptive proof intentionally includes every cumulative branch.  A
    board run can, however, keep prefetching while the output continuation edge is
    already frozen.  This secondary proof uses only a hash-bound lower-layer cycle
    budget and the active output contract; it never replaces the ordinary proof
    when the certificate-bound contract is unavailable.
    """

    base = {
        "schema_version": "spatialaccagent.cctg_frontier_stall_evidence.v1",
        "status": "unavailable",
        "frontier_id": None,
        "fixed_wall_clock_timeout": False,
        "fixed_cycle_timeout": False,
        "budget_multiplier": _CCTG_FRONTIER_BUDGET_MULTIPLIER,
    }
    contract = progress_contract if isinstance(progress_contract, dict) else {}
    target_output = _positive_int(contract.get("target_output_beats"))
    lower_cycles = _positive_int(contract.get("single_layer_cycles"))
    certificate_sha256 = str(contract.get("certificate_sha256") or "")
    stats_sha256 = str(contract.get("single_layer_stats_sha256") or "")
    if not target_output or not lower_cycles or not certificate_sha256 or not stats_sha256:
        return {**base, "reason": "a hash-bound target and lower-layer cycle certificate are required"}

    ordered = [
        row
        for row in records
        if isinstance(row, dict)
        and row.get("schema_version") == BOARD_PROGRESS_EVENT_SCHEMA_VERSION
        and _nonnegative_int(row.get("cycle")) is not None
    ]
    if not ordered or any(row.get("event_kind") == "terminal" for row in ordered):
        return {**base, "reason": "complete non-terminal progress records are required"}

    runtime_complete = any(
        "runtime" in _progress_phase(row)
        and "load" in _progress_phase(row)
        and "complete" in _progress_phase(row)
        and row.get("semantic_progress") is True
        for row in ordered
    )
    kernel_started = any(
        row.get("semantic_progress") is True
        and ("kernel_start" in _progress_phase(row) or _progress_phase(row).endswith(".kernel_start"))
        for row in ordered
    )
    if not runtime_complete or not kernel_started:
        return {**base, "reason": "runtime load and kernel start have not both been observed"}

    target_input = _positive_int(contract.get("target_input_beats"))
    input_complete = [
        row
        for row in ordered
        if row.get("semantic_progress") is True
        and "kernel" in _progress_phase(row)
        and "input" in _progress_phase(row)
        and "token" in _progress_phase(row)
        and "complete" in _progress_phase(row)
    ]
    beats_per_token = max(
        (
            int(row.get("beat")) + 1
            for row in input_complete
            if _nonnegative_int(row.get("beat")) is not None
        ),
        default=0,
    )
    expected_input_tokens = (
        target_input // beats_per_token
        if target_input and beats_per_token and target_input % beats_per_token == 0
        else None
    )
    observed_input_tokens = {
        row.get("token")
        for row in input_complete
        if _nonnegative_int(row.get("token")) is not None
    }
    if expected_input_tokens and len(observed_input_tokens) < expected_input_tokens:
        return {
            **base,
            "reason": "the complete current-layer input is not yet observed",
            "expected_input_tokens": expected_input_tokens,
            "observed_input_tokens": len(observed_input_tokens),
        }

    output_events = [
        row
        for row in ordered
        if row.get("semantic_progress") is True
        and "kernel" in _progress_phase(row)
        and "output" in _progress_phase(row)
        and "token" in _progress_phase(row)
    ]
    output_count = _output_accept_count(ordered[-1])
    if output_count is None:
        output_count = max(
            (
                _output_accept_count(row)
                for row in ordered
                if _output_accept_count(row) is not None
            ),
            default=0,
        )
    zero_output_frontier = output_count == 0
    if output_count >= target_output:
        return {
            **base,
            "reason": "the output continuation frontier is not incomplete",
            "observed_output_beats": output_count,
            "target_output_beats": target_output,
        }

    prefetch_complete_cycle: int | None = None
    for row in ordered:
        progress = row.get("prefetch_progress")
        progress = progress if isinstance(progress, dict) else {}
        accepted = _nonnegative_int(progress.get("accepted_beats"))
        target = _positive_int(progress.get("target_beats"))
        phase = _progress_phase(row)
        if (
            prefetch_complete_cycle is None
            and
            target
            and accepted == target
            and ("weight_prefetch_complete" in phase or row.get("event_kind") != "heartbeat")
        ):
            prefetch_complete_cycle = int(row["cycle"])
    if prefetch_complete_cycle is None:
        return {
            **base,
            "reason": "independent weight-prefetch branch has not reached its contract target",
            "observed_output_beats": output_count,
            "target_output_beats": target_output,
        }

    kernel_start_cycles = [
        int(row["cycle"])
        for row in ordered
        if row.get("semantic_progress") is True
        and (
            "kernel_start" in _progress_phase(row)
            or _progress_phase(row).endswith(".kernel_start")
        )
    ]
    kernel_start_cycle = min(kernel_start_cycles) if kernel_start_cycles else None
    if zero_output_frontier and kernel_start_cycle is None:
        return {
            **base,
            "reason": "zero-output input-to-output frontier lacks an observed kernel start",
            "observed_output_beats": output_count,
            "target_output_beats": target_output,
        }

    frontier_rows: list[dict[str, Any]] = []
    if zero_output_frontier:
        # With no accepted output beat, the active graph edge is the complete
        # kernel-input-to-output transition.  Start after the independent
        # prefetch cutover and retain only semantic frontier events; heartbeats
        # remain in the full trace and provide the silent/stability evidence.
        zero_frontier_start = max(kernel_start_cycle, prefetch_complete_cycle)
        frontier_rows = [
            row
            for row in ordered
            if int(row["cycle"]) >= zero_frontier_start
            and row.get("semantic_progress") is True
        ]
    else:
        previous_count: int | None = None
        for row in ordered:
            count = _output_accept_count(row)
            # A flushed board trace reports output_accept_count=0 throughout runtime
            # loading and input launch.  That startup interval belongs to the kernel
            # invocation frontier, not to output-token continuation.  Keep it in the
            # full trace, but start the continuation budget only at an explicit output
            # event or the first positive accepted-output count.
            if row in output_events or (
                count is not None
                and count > 0
                and (previous_count is None or count != previous_count)
            ):
                frontier_rows.append(row)
            if count is not None:
                previous_count = count
    if not frontier_rows:
        return {
            **base,
            "reason": (
                "no zero-output input-to-output frontier event is available"
                if zero_output_frontier
                else "no output frontier event is available"
            ),
            "observed_output_beats": output_count,
            "target_output_beats": target_output,
        }
    last_frontier = frontier_rows[-1]
    first_frontier_cycle = int(frontier_rows[0]["cycle"])
    last_frontier_cycle = int(last_frontier["cycle"])
    latest_cycle = int(ordered[-1]["cycle"])
    # A changing ready signal means the memory-side contract is still exercising
    # the frontier; do not classify that as a DUT stall.
    for row in ordered:
        if int(row["cycle"]) < last_frontier_cycle:
            continue
        ready = _active_boundary(row).get("output_ready")
        if ready not in {None, 1, True}:
            return {
                **base,
                "reason": "output frontier remains backpressured or unobserved",
                "observed_output_beats": output_count,
                "target_output_beats": target_output,
            }

    frontier_observation_start = max(last_frontier_cycle, prefetch_complete_cycle)
    latest_signature = _frontier_signature(ordered[-1])
    stable_start = latest_cycle
    for row in reversed(ordered[:-1]):
        if _frontier_signature(row) != latest_signature:
            break
        stable_start = int(row["cycle"])
    stable_start = max(stable_start, frontier_observation_start)

    # Once prefetch is complete, any accepted AXI transaction belongs to the
    # active output/lifecycle path.  Keep that branch in the frontier contract;
    # only VALID/READY transients are intentionally ignored.
    def axi_signature(row: dict[str, Any]) -> str:
        projection = {
            key: _stable_progress_value(row.get(key), axi=True)
            for key in ("axi_read", "axi_write")
        }
        return json.dumps(projection, sort_keys=True, separators=(",", ":"))

    latest_axi_signature = axi_signature(ordered[-1])
    for row in ordered:
        if int(row["cycle"]) < frontier_observation_start:
            continue
        if axi_signature(row) != latest_axi_signature:
            return {
                **base,
                "reason": "frontier-relevant AXI transaction progress is still changing",
                "observed_output_beats": output_count,
                "target_output_beats": target_output,
                "independent_branch_cutover_cycle": frontier_observation_start,
            }

    frontier_cycles = [int(row["cycle"]) for row in frontier_rows]
    frontier_gaps = [
        later - earlier
        for earlier, later in zip(frontier_cycles, frontier_cycles[1:])
        if later > earlier
    ]
    heartbeat_cycles = [
        int(row["cycle"])
        for row in ordered
        if row.get("event_kind") == "heartbeat"
    ]
    heartbeat_gaps = [
        later - earlier
        for earlier, later in zip(heartbeat_cycles, heartbeat_cycles[1:])
        if later > earlier
    ]
    observed_gap = max([*frontier_gaps, *heartbeat_gaps, 0])
    budget = max(lower_cycles, observed_gap) * _CCTG_FRONTIER_BUDGET_MULTIPLIER
    silent_cycles = latest_cycle - last_frontier_cycle
    stable_cycles = latest_cycle - stable_start
    snapshots = [
        row
        for row in ordered
        if row.get("event_kind") == "stall_snapshot"
        and int(row["cycle"]) > last_frontier_cycle
    ]
    result = {
        **base,
        "frontier_id": (
            "connected_kernel_input_to_output"
            if zero_output_frontier
            else "kernel_output_token_sequence_continuation"
        ),
        "frontier_type": "zero_output_input_to_output" if zero_output_frontier else "output_continuation",
        "status": "observing",
        "target_output_beats": target_output,
        "observed_output_beats": output_count,
        "first_output_frontier_cycle": None if zero_output_frontier else first_frontier_cycle,
        "last_frontier_cycle": last_frontier_cycle,
        "kernel_start_cycle": kernel_start_cycle,
        "startup_latency_cycles": (
            first_frontier_cycle - kernel_start_cycle
            if kernel_start_cycle is not None and not zero_output_frontier
            else None
        ),
        "startup_latency_excluded_from_continuation_budget": True,
        "independent_branch_cutover_cycle": frontier_observation_start,
        "latest_cycle": latest_cycle,
        "silent_cycles": silent_cycles,
        "stable_state_start_cycle": stable_start,
        "stable_state_cycles": stable_cycles,
        "frontier_gap_cycles": observed_gap,
        "single_layer_cycles": lower_cycles,
        "adaptive_frontier_cycle_bound": budget,
        "stall_snapshot_count": len(snapshots),
        "certificate_sha256": certificate_sha256,
        "single_layer_stats_sha256": stats_sha256,
        "independent_branch_progress": {
            "latest_prefetch_progress": ordered[-1].get("prefetch_progress"),
            "latest_axi_read": ordered[-1].get("axi_read"),
            "latest_axi_write": ordered[-1].get("axi_write"),
        },
    }
    if (
        silent_cycles >= budget
        and stable_cycles >= budget
        and len(snapshots) >= _MIN_STALL_SNAPSHOT_COUNT
    ):
        result.update(
            {
                "status": "proven_frontier_stall",
                "reason": (
                    "the output continuation frontier stayed unchanged beyond a hash-bound "
                    "lower-layer cycle budget while independent branches were projected separately"
                ),
            }
        )
    else:
        result["reason"] = "certificate-bounded CCTG frontier evidence is not yet complete"
    return result


def summarize_progress_events(
    records: list[dict[str, Any]],
    progress_contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Summarize evidence without inferring a stall from elapsed wall-clock time."""

    validation_errors: list[str] = []
    previous_sequence: int | None = None
    previous_cycle: int | None = None
    semantic_records: list[dict[str, Any]] = []
    latest_by_kind: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(records):
        missing = sorted(REQUIRED_PROGRESS_EVENT_FIELDS - set(row))
        if missing:
            validation_errors.append(
                f"record[{index}] lacks required fields: {missing}"
            )
        if row.get("schema_version") != BOARD_PROGRESS_EVENT_SCHEMA_VERSION:
            validation_errors.append(f"record[{index}] has an unsupported schema_version")
        sequence = row.get("sequence")
        cycle = row.get("cycle")
        if not isinstance(sequence, int) or sequence < 0:
            validation_errors.append(f"record[{index}].sequence is not a non-negative integer")
        elif previous_sequence is not None and sequence <= previous_sequence:
            validation_errors.append(f"record[{index}].sequence is not strictly monotonic")
        else:
            previous_sequence = sequence
        if not isinstance(cycle, int) or cycle < 0:
            validation_errors.append(f"record[{index}].cycle is not a non-negative integer")
        elif previous_cycle is not None and cycle < previous_cycle:
            validation_errors.append(f"record[{index}].cycle is not monotonic")
        else:
            previous_cycle = cycle
        event_kind = str(row.get("event_kind") or "")
        if event_kind:
            latest_by_kind[event_kind] = row
        if row.get("semantic_progress") is True and event_kind != "heartbeat":
            semantic_records.append(row)
        elif event_kind == "heartbeat" and row.get("semantic_progress") is not False:
            validation_errors.append(
                f"record[{index}] heartbeat is incorrectly marked as semantic progress"
            )

    last = records[-1] if records else {}
    last_semantic = semantic_records[-1] if semantic_records else {}
    last_cycle = last.get("cycle") if isinstance(last.get("cycle"), int) else None
    last_semantic_cycle = (
        last_semantic.get("cycle")
        if isinstance(last_semantic.get("cycle"), int)
        else None
    )
    silent_cycles = (
        last_cycle - last_semantic_cycle
        if last_cycle is not None
        and last_semantic_cycle is not None
        and last_cycle >= last_semantic_cycle
        else None
    )
    stall_snapshot = latest_by_kind.get("stall_snapshot", {})
    adaptive_stall = adaptive_semantic_stall_evidence(records, progress_contract)
    pipeline_violation = intra_layer_pipeline_violation_evidence(
        records, progress_contract
    )
    progress_snapshot_rows: list[tuple[str, dict[str, Any]]] = []
    if last_semantic:
        progress_snapshot_rows.append(("last_semantic_progress", last_semantic))
    if stall_snapshot and stall_snapshot is not last_semantic:
        progress_snapshot_rows.append(("latest_stall", stall_snapshot))
    if last and last is not last_semantic and last is not stall_snapshot:
        progress_snapshot_rows.append(("latest_record", last))
    extra_signal_snapshots = [
        _diagnostic_snapshot(row, snapshot_kind=kind)
        for kind, row in progress_snapshot_rows
    ]
    extra_signal_snapshots = [
        snapshot
        for snapshot in extra_signal_snapshots
        if snapshot.get("signals")
    ]
    extra_signal_names = sorted(
        {
            signal_name
            for snapshot in extra_signal_snapshots
            for signal_name in snapshot.get("signals", {})
            if isinstance(signal_name, str)
        }
    )
    return {
        "schema_version": "spatialaccagent.board_live_progress_summary.v1",
        "status": "observing",
        "record_count": len(records),
        "semantic_progress_event_count": len(semantic_records),
        "heartbeat_event_count": sum(
            1 for row in records if row.get("event_kind") == "heartbeat"
        ),
        "progress_epoch": max(
            (
                int(row["progress_epoch"])
                for row in records
                if isinstance(row.get("progress_epoch"), int)
            ),
            default=0,
        ),
        "last_cycle": last_cycle,
        "last_semantic_progress_cycle": last_semantic_cycle,
        "silent_cycles": silent_cycles,
        "last_complete_record": last,
        "last_semantic_progress_event": last_semantic,
        "latest_event_by_kind": latest_by_kind,
        "latest_stall_snapshot": stall_snapshot,
        "first_stalled_boundary": (
            stall_snapshot.get("stalled_boundary")
            or stall_snapshot.get("boundary_id")
            or stall_snapshot.get("stage_or_boundary")
        ),
        "terminal_event_seen": "terminal" in latest_by_kind,
        "validation_errors": validation_errors[:128],
        "causal_event_tail": records[-32:],
        "extra_signal_names": extra_signal_names,
        "extra_signal_snapshots": extra_signal_snapshots,
        "adaptive_semantic_stall_evidence": adaptive_stall,
        "intra_layer_pipeline_violation_evidence": pipeline_violation,
        "policy": {
            "heartbeat_proves_clock_activity_not_semantic_progress": True,
            "wall_clock_elapsed_never_classifies_a_hardware_stall": True,
            "extra_signal_snapshots_are_bounded_and_diagnostic_only": True,
        },
    }


def _stable_progress_value(value: Any, *, axi: bool = False) -> Any:
    if isinstance(value, dict):
        return {
            str(key): _stable_progress_value(child)
            for key, child in sorted(value.items(), key=lambda item: str(item[0]))
            if not (
                axi
                and str(key).lower().endswith(_TRANSIENT_AXI_CONTROL_SUFFIXES)
            )
        }
    if isinstance(value, list):
        return [_stable_progress_value(child) for child in value]
    return value


def _stable_progress_signature(row: dict[str, Any]) -> str:
    projection = {
        key: _stable_progress_value(
            row.get(key), axi=key in {"axi_read", "axi_write"}
        )
        for key in (
            "semantic_progress",
            "progress_epoch",
            "last_semantic_progress_cycle",
            "scheduler_state",
            "layer",
            "token",
            "beat",
            "active_weight_bank",
            "preload_weight_bank",
            "activation_read_bank",
            "activation_write_bank",
            "prefetch_progress",
            "runtime_load_progress",
            "final_writeback_progress",
            "axi_read",
            "axi_write",
        )
    }
    return json.dumps(projection, sort_keys=True, separators=(",", ":"))


def _target_work_units(value: Any, key: str = "") -> list[int]:
    if isinstance(value, dict):
        units: list[int] = []
        for child_key, child in value.items():
            units.extend(_target_work_units(child, str(child_key)))
        return units
    if isinstance(value, list):
        units = []
        for child in value:
            units.extend(_target_work_units(child, key))
        return units
    if (
        "target" in key.lower()
        and isinstance(value, int)
        and not isinstance(value, bool)
        and value > 0
    ):
        return [value]
    return []


def adaptive_semantic_stall_evidence(
    records: list[dict[str, Any]],
    progress_contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Prove semantic stagnation without a wall-clock or fixed cycle timeout."""

    ordered = [
        row
        for row in records
        if isinstance(row, dict)
        and row.get("schema_version") == BOARD_PROGRESS_EVENT_SCHEMA_VERSION
        and isinstance(row.get("cycle"), int)
        and not isinstance(row.get("cycle"), bool)
        and int(row["cycle"]) >= 0
    ]
    base = {
        "schema_version": "spatialaccagent.adaptive_semantic_stall_evidence.v1",
        "status": "observing",
        "fixed_wall_clock_timeout": False,
        "fixed_cycle_timeout": False,
        "policy": {
            "semantic_gap_multiplier": _ADAPTIVE_SEMANTIC_GAP_MULTIPLIER,
            "target_work_multiplier": _ADAPTIVE_TARGET_WORK_MULTIPLIER,
            "heartbeat_multiplier": _ADAPTIVE_HEARTBEAT_MULTIPLIER,
            "minimum_stall_snapshot_count": _MIN_STALL_SNAPSHOT_COUNT,
        },
    }
    if not ordered:
        return {**base, "reason": "no complete progress events"}
    if any(row.get("event_kind") == "terminal" for row in ordered):
        return {**base, "reason": "terminal event already exists"}

    progress_contract = (
        progress_contract if isinstance(progress_contract, dict) else {}
    )
    equivalence_oracle = progress_contract.get(
        "same_source_equivalence_oracle", {}
    )
    if (
        isinstance(equivalence_oracle, dict)
        and equivalence_oracle.get("status") == "ready"
    ):
        capture_sequence = equivalence_oracle.get("capture_sequence")
        capture_cycle = equivalence_oracle.get("capture_cycle")
        expected = equivalence_oracle.get("expected_semantic_records", [])
        cold_terminal_cycle = equivalence_oracle.get("cold_terminal_cycle")
        if (
            isinstance(capture_sequence, int)
            and not isinstance(capture_sequence, bool)
            and isinstance(capture_cycle, int)
            and not isinstance(capture_cycle, bool)
            and isinstance(expected, list)
            and all(isinstance(row, dict) for row in expected)
            and isinstance(cold_terminal_cycle, int)
            and not isinstance(cold_terminal_cycle, bool)
        ):
            observed = [
                row
                for row in ordered
                if row.get("semantic_progress") is True
                and row.get("event_kind") == "semantic_progress"
                and (
                    (
                        isinstance(row.get("sequence"), int)
                        and row["sequence"] >= capture_sequence
                    )
                    or (
                        not isinstance(row.get("sequence"), int)
                        and isinstance(row.get("cycle"), int)
                        and row["cycle"] >= capture_cycle
                    )
                )
            ]
            latest_cycle = int(ordered[-1]["cycle"])
            mismatch_index = next(
                (
                    index
                    for index, (actual, reference) in enumerate(
                        zip(observed, expected)
                    )
                    if json.dumps(
                        actual,
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                    != json.dumps(
                        reference,
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                ),
                None,
            )
            unexpected_extra = len(observed) > len(expected)
            missing_next = len(observed) < len(expected)
            next_expected = expected[len(observed)] if missing_next else {}
            next_expected_cycle = next_expected.get("cycle")
            overdue_next = bool(
                missing_next
                and isinstance(next_expected_cycle, int)
                and latest_cycle > next_expected_cycle
            )
            all_expected_observed = len(observed) == len(expected)
            cold_terminal_reached = bool(
                all_expected_observed and latest_cycle >= cold_terminal_cycle
            )
            divergence = bool(
                mismatch_index is not None or unexpected_extra or overdue_next
            )
            proven = divergence or cold_terminal_reached
            reason = (
                f"restored semantic record {mismatch_index} differs from the exact cold suffix"
                if mismatch_index is not None
                else "restored suffix produced an extra semantic record"
                if unexpected_extra
                else (
                    "restored suffix did not produce the next exact cold semantic record "
                    f"by its executed cold cycle {next_expected_cycle}"
                )
                if overdue_next
                else "restored suffix reproduced every cold semantic record through the cold terminal cycle"
                if cold_terminal_reached
                else "same-source equivalence oracle is waiting for the next cold semantic record"
            )
            return {
                **base,
                "status": "proven_semantic_stall" if proven else "observing",
                "proof_mode": "same_source_equivalence_oracle",
                "reason": reason,
                "latest_cycle": latest_cycle,
                "capture_sequence": capture_sequence,
                "capture_cycle": capture_cycle,
                "cold_terminal_cycle": cold_terminal_cycle,
                "expected_semantic_record_count": len(expected),
                "observed_semantic_record_count": len(observed),
                "next_expected_semantic_record": next_expected,
                "next_expected_cycle": next_expected_cycle,
                "mismatch_index": mismatch_index,
                "same_source_equivalence_divergence": divergence,
                "cold_terminal_match_candidate": (
                    cold_terminal_reached and not divergence
                ),
                "oracle_sha256": equivalence_oracle.get("oracle_sha256"),
                "cold_progress_sha256": equivalence_oracle.get(
                    "cold_progress_sha256"
                ),
                "policy": {
                    **base["policy"],
                    "bound_is_the_exact_executed_cold_suffix_not_a_fixed_timeout": True,
                    "missing_or_different_next_semantic_event_proves_divergence": True,
                    "hardware_acceptance_is_not_inferred_from_calibration": True,
                },
            }

    pipeline_violation = intra_layer_pipeline_violation_evidence(
        ordered, progress_contract
    )
    if pipeline_violation.get("status") == "proven_pipeline_violation":
        return {
            **base,
            "status": "proven_semantic_stall",
            "proof_mode": "intra_layer_pipeline_contract",
            "failure_class": "intra_layer_spatial_pipeline_violation",
            "reason": pipeline_violation.get("reason"),
            "latest_cycle": int(ordered[-1]["cycle"]),
            "last_semantic_event_cycle": int(ordered[-1]["cycle"]),
            "intra_layer_pipeline_violation_evidence": pipeline_violation,
            "policy": {
                **base["policy"],
                "all_target_inputs_and_ready_zero_output_required": True,
                "pipeline_contract_violation_is_not_a_timeout": True,
            },
        }

    semantic = [
        row for row in ordered if row.get("event_kind") == "semantic_progress"
    ]
    if len(semantic) < 2:
        return {
            **base,
            "reason": "fewer than two observed semantic transitions",
            "semantic_event_count": len(semantic),
        }
    semantic_cycles = [int(row["cycle"]) for row in semantic]
    if semantic_cycles != sorted(semantic_cycles):
        return {**base, "reason": "semantic event cycles are not monotonic"}
    semantic_gaps = [
        later - earlier
        for earlier, later in zip(semantic_cycles, semantic_cycles[1:])
        if later > earlier
    ]
    if not semantic_gaps:
        return {**base, "reason": "no positive semantic transition gap"}

    latest = ordered[-1]
    latest_cycle = int(latest["cycle"])
    last_semantic_cycle = semantic_cycles[-1]
    declared_last_semantic = latest.get("last_semantic_progress_cycle")
    if (
        not isinstance(declared_last_semantic, int)
        or isinstance(declared_last_semantic, bool)
        or int(declared_last_semantic) != last_semantic_cycle
    ):
        return {
            **base,
            "reason": "latest event does not bind the last semantic event cycle",
            "last_semantic_event_cycle": last_semantic_cycle,
            "declared_last_semantic_progress_cycle": declared_last_semantic,
        }

    latest_signature = _stable_progress_signature(latest)
    stable_start_cycle = latest_cycle
    for row in reversed(ordered[:-1]):
        if _stable_progress_signature(row) != latest_signature:
            break
        stable_start_cycle = int(row["cycle"])

    heartbeat_cycles = [
        int(row["cycle"])
        for row in ordered
        if row.get("event_kind") == "heartbeat"
    ]
    heartbeat_gaps = sorted(
        later - earlier
        for earlier, later in zip(heartbeat_cycles, heartbeat_cycles[1:])
        if later > earlier
    )
    heartbeat_interval = (
        heartbeat_gaps[len(heartbeat_gaps) // 2] if heartbeat_gaps else 0
    )
    targets = _target_work_units(latest)
    max_target_work = max(targets, default=0)
    adaptive_bound = max(
        max(semantic_gaps) * _ADAPTIVE_SEMANTIC_GAP_MULTIPLIER,
        max_target_work * _ADAPTIVE_TARGET_WORK_MULTIPLIER,
        heartbeat_interval * _ADAPTIVE_HEARTBEAT_MULTIPLIER,
    )
    if adaptive_bound <= 0:
        return {**base, "reason": "adaptive evidence bound is unavailable"}

    silent_cycles = latest_cycle - last_semantic_cycle
    stable_cycles = latest_cycle - stable_start_cycle
    stall_snapshots = [
        row
        for row in ordered
        if row.get("event_kind") == "stall_snapshot"
        and int(row.get("cycle") or -1) > last_semantic_cycle
    ]
    evidence = {
        **base,
        "semantic_event_count": len(semantic),
        "last_semantic_event_cycle": last_semantic_cycle,
        "latest_cycle": latest_cycle,
        "silent_cycles": silent_cycles,
        "stable_state_start_cycle": stable_start_cycle,
        "stable_state_cycles": stable_cycles,
        "stall_snapshot_count": len(stall_snapshots),
        "max_observed_semantic_gap": max(semantic_gaps),
        "max_target_work_units": max_target_work,
        "observed_heartbeat_interval": heartbeat_interval,
        "adaptive_silent_cycle_bound": adaptive_bound,
        "last_semantic_progress_event": semantic[-1],
        "latest_stall_snapshot": stall_snapshots[-1] if stall_snapshots else {},
        "latest_complete_event": latest,
        "semantic_progress_field_schema_valid": all(
            isinstance(row.get("semantic_progress"), bool) for row in ordered
        ),
    }
    frontier_evidence = _cctg_frontier_stall_evidence(ordered, progress_contract)
    evidence["cctg_frontier_stall_evidence"] = frontier_evidence
    if frontier_evidence.get("status") == "proven_frontier_stall":
        evidence.update(
            {
                "status": "proven_semantic_stall",
                "proof_mode": "cctg_frontier",
                "adaptive_silent_cycle_bound": frontier_evidence[
                    "adaptive_frontier_cycle_bound"
                ],
                "reason": frontier_evidence["reason"],
            }
        )
        return evidence
    proven = (
        silent_cycles >= adaptive_bound
        and stable_cycles >= adaptive_bound
        and len(stall_snapshots) >= _MIN_STALL_SNAPSHOT_COUNT
    )
    if proven:
        evidence["status"] = "proven_semantic_stall"
        evidence["reason"] = (
            "all cumulative scheduler, layer, bank, workload and AXI state remained "
            "unchanged beyond the adaptive bound derived from this run"
        )
    else:
        evidence["reason"] = "adaptive semantic-stall evidence is not yet complete"
    return evidence


def normalize_adaptive_semantic_stall_evidence(value: Any) -> dict[str, Any]:
    """Normalize a persisted recovered-job stall into the live evidence schema.

    A controller can be interrupted after a remote runner has already emitted a
    complete progress log.  Recovery deliberately retains only bounded semantic
    evidence, whose compact schema predates the regular live-observer schema.
    This adapter preserves the original values while restoring the fields used
    by diagnosis and LLM handoff.  It never infers a stall from partial data.
    """

    if not isinstance(value, dict):
        return {}
    if (
        value.get("schema_version")
        == "spatialaccagent.adaptive_semantic_stall_evidence.v1"
    ):
        return dict(value)
    if value.get("status") != "proven_semantic_stall":
        return {}
    last_event = value.get("last_semantic_event")
    latest_event = value.get("latest_complete_remote_event")
    bound = value.get("adaptive_bound")
    last_cycle = last_event.get("cycle") if isinstance(last_event, dict) else None
    latest_cycle = latest_event.get("cycle") if isinstance(latest_event, dict) else None
    silent_cycles = value.get("observed_silent_cycles")
    cycle_bound = bound.get("cycles") if isinstance(bound, dict) else None
    numbers = (last_cycle, latest_cycle, silent_cycles, cycle_bound)
    if any(not isinstance(item, int) or isinstance(item, bool) or item < 0 for item in numbers):
        return {}
    if latest_cycle < last_cycle or silent_cycles != latest_cycle - last_cycle:
        return {}
    return {
        "schema_version": "spatialaccagent.adaptive_semantic_stall_evidence.v1",
        "status": "proven_semantic_stall",
        "proof_mode": "recovered_remote_semantic_progress",
        "reason": value.get("reason") or "recovered remote semantic stall",
        "fixed_wall_clock_timeout": bool(
            bound.get("fixed_wall_clock_timeout", False)
            if isinstance(bound, dict)
            else False
        ),
        "fixed_cycle_timeout": bool(
            bound.get("fixed_cycle_timeout", False)
            if isinstance(bound, dict)
            else False
        ),
        "last_semantic_event_cycle": last_cycle,
        "latest_cycle": latest_cycle,
        "silent_cycles": silent_cycles,
        "stable_state_start_cycle": last_cycle,
        "stable_state_cycles": silent_cycles,
        "adaptive_silent_cycle_bound": cycle_bound,
        "stall_snapshot_count": value.get("observed_stall_snapshot_count", 0),
        "last_semantic_progress_event": dict(last_event),
        "latest_complete_event": dict(latest_event),
        "latest_stall_snapshot": dict(value.get("latest_stall_snapshot", {})),
        "recovered_evidence_schema_version": value.get("schema_version"),
    }
