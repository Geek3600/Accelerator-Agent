#!/usr/bin/env python3
"""Analyze case VCS functional-sim evidence and emit repair handoff JSON."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from accagent.framework.board_progress import (
    BOARD_PROGRESS_EVENT_SCHEMA_VERSION,
    normalize_adaptive_semantic_stall_evidence,
    read_complete_jsonl,
    summarize_progress_events,
)
from accagent.framework.board_backtrack_evidence import (
    board_to_lower_layer_contradiction_from_runner,
)
from accagent.framework.board_validation_scope import (
    BoardValidationScopeError,
    resolve_board_validation_scope,
    validation_scope_record_errors,
)
from accagent.framework.sacg_cctg_causal_slice import (
    build_sacg_cctg_causal_slice,
)
from accagent.framework.semantic_simulator import (
    REMOTE_JOB_RETRY_REQUEST,
    ZERO_TIME_LIVELOCK_EXIT_CODE,
)


DIAGNOSIS_APPLICABILITY_BINDING_SCHEMA_VERSION = (
    "spatialaccagent.diagnosis_applicability_binding.v1"
)


PROGRESS_RE = re.compile(r"case_axi_board_tb progress (?P<fields>.*)")
FATAL_RE = re.compile(r"case_axi_board_tb (?P<kind>NO_PROGRESS|TIMEOUT|FAIL)(?P<fields>.*)")
PASS_RE = re.compile(r"case_axi_board_tb PASS real functional ddr path (?P<fields>.*)")
FIELD_RE = re.compile(r"(?P<key>[A-Za-z_][A-Za-z0-9_]*)=(?P<value>[^ \n]+)")


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def load_boundary_trace_evidence(path: Path) -> dict[str, Any]:
    """Normalize either the legacy JSON envelope or an incrementally flushed JSONL trace."""

    if not path.is_file():
        return {"status": "missing", "records": [], "source_path": str(path)}
    try:
        value = read_json(path)
    except Exception:
        parsed = read_complete_jsonl(path)
        records = [
            row for row in parsed.get("records", []) if isinstance(row, dict)
        ]
        progress_records = [
            row
            for row in records
            if row.get("schema_version") == BOARD_PROGRESS_EVENT_SCHEMA_VERSION
        ]
        return {
            "status": "ready" if records else "empty",
            "schema_version": "spatialaccagent.normalized_boundary_trace.v1",
            "source_format": "jsonl",
            "source_path": str(path),
            "record_count": len(records),
            "records": records,
            "invalid_records": parsed.get("invalid_records", []),
            "trailing_partial_byte_count": parsed.get(
                "trailing_partial_byte_count", 0
            ),
            "progress_summary": (
                summarize_progress_events(progress_records)
                if progress_records and len(progress_records) == len(records)
                else {}
            ),
        }
    records = value.get("boundary_trace")
    if not isinstance(records, list):
        records = value.get("records", [])
    records = [row for row in records if isinstance(row, dict)]
    return {
        **value,
        "status": "ready" if records else "empty",
        "source_format": "json_envelope",
        "source_path": str(path),
        "record_count": len(records),
        "records": records,
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def board_validation_scope_summary(
    run_dir: Path,
    binding: dict[str, Any],
    manifest: dict[str, Any],
) -> dict[str, Any]:
    """Return the common scope proof used by board result analysis.

    A one-layer or prefix board run is complete when it covers every configured
    validation layer.  ``all_target_layers`` only records whether that range is
    also the full model.
    """

    task_path = run_dir / "input" / "task_card.json"
    model_path = run_dir / "input" / "model_config.json"
    try:
        scope = resolve_board_validation_scope(read_json(task_path), read_json(model_path))
    except (BoardValidationScopeError, FileNotFoundError, json.JSONDecodeError) as exc:
        return {"status": "fail", "errors": [f"board validation scope is invalid: {exc}"], "scope": {}}

    errors = validation_scope_record_errors(
        scope,
        binding,
        allowed_statuses={"pass"},
        require_accelerator_scope=True,
    )
    errors.extend(
        "simulation " + error
        for error in validation_scope_record_errors(
            scope,
            manifest,
            allowed_statuses={"ready", "pass"},
        )
    )
    return {
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "scope": scope.as_dict(),
    }


def decode_semantic_memh(path: Path, bits: int, lanes: int) -> Any:
    import torch

    values = []
    mask = (1 << bits) - 1
    for raw in path.read_text(encoding="ascii").splitlines():
        packed = int(raw.strip(), 16)
        values.extend((packed >> (lane * bits)) & mask for lane in range(lanes))
    if bits == 16:
        signed = [value - 0x10000 if value & 0x8000 else value for value in values]
        return torch.tensor(signed, dtype=torch.int16).view(torch.float16).float()
    if bits == 32:
        signed = [value - 0x100000000 if value & 0x80000000 else value for value in values]
        return torch.tensor(signed, dtype=torch.int32).view(torch.float32)
    raise ValueError(f"unsupported semantic vector width {bits}")


def semantic_compare(actual_path: Path, expected: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    import torch

    expected_path = Path(str(expected.get("path") or ""))
    if not actual_path.is_file() or not expected_path.is_file() or sha256_file(expected_path) != expected.get("sha256"):
        return {"passed": False, "error": "RTL or expected board semantic output file/hash is missing"}
    actual = decode_semantic_memh(actual_path, int(expected.get("bits") or 0), int(expected.get("lanes") or 0))
    golden = decode_semantic_memh(expected_path, int(expected.get("bits") or 0), int(expected.get("lanes") or 0))
    if actual.numel() != golden.numel():
        return {"passed": False, "num_actual": actual.numel(), "num_expected": golden.numel(), "error": "board output shape mismatch"}
    atol = float(policy.get("atol"))
    rtol = float(policy.get("rtol"))
    max_fraction = float(policy.get("max_mismatch_fraction"))
    close = torch.isclose(actual, golden, atol=atol, rtol=rtol, equal_nan=False) & torch.isfinite(actual) & torch.isfinite(golden)
    mismatch = ~close
    mismatch_count = int(mismatch.sum().item())
    difference = torch.abs(actual - golden)
    finite_difference = difference[torch.isfinite(difference)]
    fraction = mismatch_count / max(1, actual.numel())
    return {
        "passed": fraction <= max_fraction,
        "num_elements": int(actual.numel()),
        "num_mismatch": mismatch_count,
        "mismatch_fraction": fraction,
        "max_mismatch_fraction": max_fraction,
        "max_abs_error": float(finite_difference.max().item()) if finite_difference.numel() else float("inf"),
        "mean_abs_error": float(finite_difference.mean().item()) if finite_difference.numel() else float("inf"),
        "atol": atol,
        "rtol": rtol,
    }


REAL_ERROR_RE = re.compile(
    r"(?i)(?:error(?:-\[[^\]]+\])?\s*[: ]|fatal(?:-\[[^\]]+\])?\s*[: ]|"
    r"\*E,|undefined (?:module|entity|symbol|reference)|unresolved (?:module|entity|reference)|"
    r"cannot (?:find|open|resolve)|no such file|permission denied)"
)
LIBRARY_ERROR_RE = re.compile(
    r"(?i)(?:logical library|library mapping[^\n]*(?:failed|missing|not found)|"
    r"library\s+[^\n]*\s(?:is not defined|not found|cannot be opened)|"
    r"cannot (?:find|open|resolve)[^\n]*\blibrary\b|"
    r"(?:error|failed|missing|not found|cannot[^\n]*)[^\n]*synopsys_sim\.setup|"
    r"synopsys_sim\.setup[^\n]*(?:failed|missing|not found|cannot))"
)
ELABORATION_ERROR_RE = re.compile(
    r"(?i)(?:\belaborat(?:e|ion|ing)[^\n]*(?:error|fail|unresolved|not found)|"
    r"top (?:module|entity)[^\n]*(?:not found|unresolved)|"
    r"undefined (?:module|entity)|unresolved (?:module|entity)|"
    r"error-\[(?:TMENF|URMI|IUWI)\])"
)
EXECUTION_ENVIRONMENT_ERROR_RE = re.compile(
    r"(?i)(?:no space left on device|disk quota exceeded)"
)
TRANSPORT_FAILURE_CLASSES = {
    "remote_transport_failure",
    "remote_semantic_recovery_indeterminate",
    "remote_recovery_indeterminate",
}
SEMANTIC_STALL_EXIT_CODE = 86


def read_optional_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return read_json(path)
    except Exception:
        return {}


def read_optional_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def ordered_strings(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value or "").strip()
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result


def board_consumed_tensor_hashes(
    runner: dict[str, Any],
    board_manifest: dict[str, Any],
    binding: dict[str, Any],
) -> tuple[list[str], str | None]:
    candidates = [
        (binding.get("board_consumed_tensor_hashes"), "dut_weight_binding_manifest.board_consumed_tensor_hashes"),
        (board_manifest.get("board_consumed_tensor_hashes"), "board_simulation_manifest.board_consumed_tensor_hashes"),
        (
            (
                runner.get("weight_binding_evidence", {}).get("binding_hashes")
                if isinstance(runner.get("weight_binding_evidence"), dict)
                else None
            ),
            "case_board_vcs_functional.weight_binding_evidence.binding_hashes",
        ),
    ]
    for values, source in candidates:
        hashes = ordered_strings(values)
        if hashes:
            return hashes, source
    return [], None


def report_path(run_dir: Path, value: Any, fallback: Path) -> Path:
    text = str(value or "").strip()
    if not text:
        return fallback
    path = Path(text)
    return path if path.is_absolute() else run_dir / path


def first_real_error(text: str, fallback_errors: Any = None) -> str | None:
    if isinstance(fallback_errors, list):
        for value in fallback_errors:
            error = str(value or "").strip()
            if error:
                return error[:2000]
    for raw in text.splitlines():
        line = raw.strip()
        if not line or re.search(r"(?i)\b(?:0|no)\s+errors?\b", line):
            continue
        if REAL_ERROR_RE.search(line):
            return line[:2000]
    return None


def real_error_context(text: str, following_lines: int = 6) -> str:
    lines = text.splitlines()
    for index, raw in enumerate(lines):
        line = raw.strip()
        if line and not re.search(r"(?i)\b(?:0|no)\s+errors?\b", line) and REAL_ERROR_RE.search(line):
            return "\n".join(lines[index : index + following_lines])
    return text[-4000:]


def log_tail(*texts: str, limit: int = 8000) -> str:
    combined = "\n".join(text.strip() for text in texts if text and text.strip())
    return combined[-limit:]


def nested_tool_text(row: Any) -> str:
    if not isinstance(row, dict):
        return ""
    return log_tail(
        str(row.get("stdout_tail") or ""),
        str(row.get("stderr_tail") or ""),
        str(row.get("summary") or ""),
    )


def source_rows(board_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows = board_manifest.get("source_files", [])
    return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []


def planned_source_ids(board_manifest: dict[str, Any]) -> set[str]:
    plan = (
        board_manifest.get("vcs_compile_plan", {})
        if isinstance(board_manifest.get("vcs_compile_plan"), dict)
        else {}
    )
    commands = plan.get("ordered_commands", [])
    if not isinstance(commands, list):
        return set()
    return {
        str(source_id)
        for command in commands
        if isinstance(command, dict) and isinstance(command.get("source_ids"), list)
        for source_id in command["source_ids"]
        if str(source_id)
    }


def related_source_ids(text: str, board_manifest: dict[str, Any]) -> list[str]:
    if not text:
        return []
    lowered = text.lower()
    rows = source_rows(board_manifest)
    planned = planned_source_ids(board_manifest)
    basename_owners: dict[str, set[str]] = {}
    for row in rows:
        source_id = str(row.get("source_id") or "").strip()
        if not source_id or (planned and source_id not in planned):
            continue
        for field in ("path", "local_path", "staged_path"):
            value = str(row.get(field) or "").strip()
            if value:
                basename_owners.setdefault(Path(value).name.lower(), set()).add(source_id)

    matched: list[str] = []
    for row in rows:
        source_id = str(row.get("source_id") or "").strip()
        if not source_id or (planned and source_id not in planned):
            continue
        exact_tokens = [source_id]
        unique_basenames: list[str] = []
        for field in ("path", "local_path", "staged_path"):
            value = str(row.get(field) or "").strip()
            if value:
                exact_tokens.append(value.replace("\\", "/"))
                basename = Path(value).name.lower()
                if basename and basename_owners.get(basename) == {source_id}:
                    unique_basenames.append(basename)
        if any(token.lower() in lowered for token in exact_tokens if token) or any(
            basename in lowered for basename in unique_basenames
        ):
            matched.append(source_id)
    return ordered_strings(matched)


def failed_acceptance_checks(runner: dict[str, Any]) -> list[dict[str, Any]]:
    acceptance = (
        runner.get("exact_board_acceptance", {})
        if isinstance(runner.get("exact_board_acceptance"), dict)
        else {}
    )
    checks = acceptance.get("checks", [])
    if not isinstance(checks, list):
        return []
    keys = ("name", "status", "summary", "error", "errors", "blockers")
    return [
        {key: row.get(key) for key in keys if key in row}
        for row in checks
        if isinstance(row, dict) and str(row.get("status") or "").lower() not in {"pass", "ready"}
    ][:64]


def structured_failures(
    runner: dict[str, Any], executed_manifest: dict[str, Any]
) -> dict[str, Any]:
    monitor_rows = (
        runner.get("structured_monitor_results", {})
        if isinstance(runner.get("structured_monitor_results"), dict)
        else {}
    )
    failed_monitors = [
        {"monitor_id": monitor_id, **row}
        for monitor_id, row in monitor_rows.items()
        if isinstance(row, dict) and row.get("status") != "pass"
    ]
    protocol_runtime = (
        executed_manifest.get("protocol_monitor_results", {})
        if isinstance(executed_manifest.get("protocol_monitor_results"), dict)
        else {}
    )
    runtime_interfaces = protocol_runtime.get("interfaces", [])
    if isinstance(runtime_interfaces, list):
        for row in runtime_interfaces:
            if not isinstance(row, dict):
                continue
            violations = row.get("violations")
            if row.get("status") == "pass" and not violations:
                continue
            runtime_failure = {
                key: row.get(key)
                for key in (
                    "interface",
                    "status",
                    "violations",
                    "transaction_counts",
                    "structured_report",
                )
                if key in row
            }
            existing = next(
                (
                    failure
                    for failure in failed_monitors
                    if failure.get("interface") == row.get("interface")
                ),
                None,
            )
            if existing is None:
                failed_monitors.append(runtime_failure)
            else:
                existing.update(runtime_failure)

    hierarchy = (
        executed_manifest.get("elaborated_hierarchy", {})
        if isinstance(executed_manifest.get("elaborated_hierarchy"), dict)
        else {}
    )
    hierarchy_failure: dict[str, Any] = {}
    if runner.get("elaborated_hierarchy_report_valid") is False or (
        hierarchy and hierarchy.get("status") != "pass"
    ):
        hierarchy_failure = {
            "report_valid": runner.get("elaborated_hierarchy_report_valid"),
            **{
                key: hierarchy.get(key)
                for key in ("status", "errors", "blockers", "failed_checks", "evidence_refs")
                if key in hierarchy
            },
        }

    pipeline = (
        executed_manifest.get("pipeline_overlap_results", {})
        if isinstance(executed_manifest.get("pipeline_overlap_results"), dict)
        else {}
    )
    pipeline_failure: dict[str, Any] = {}
    if runner.get("pipeline_overlap_passed") is False or (
        pipeline and pipeline.get("status") != "pass"
    ):
        pipeline_failure = {
            "report_valid": runner.get("pipeline_overlap_passed"),
            **{
                key: pipeline.get(key)
                for key in (
                    "status",
                    "errors",
                    "blockers",
                    "failed_checks",
                    "pipeline_semantics",
                    "required_dependency_overlap_complete",
                    "all_planned_stages_participate_in_required_overlap",
                    "token_order_preserved",
                    "serial_leaf_execution_observed",
                    "observed_different_token_overlap_count",
                    "stage_turnover_gaps_are_diagnostic",
                    "all_stages_same_cycle_concurrency_required",
                    "diagnostic_maximum_concurrent_stage_count",
                    "all_spatial_stages_concurrent_observed",
                    "whole_sequence_barrier_observed",
                    "structured_trace_report",
                )
                if key in pipeline
            },
        }
    return {
        "protocol_monitors": failed_monitors[:64],
        "elaborated_hierarchy": hierarchy_failure,
        "pipeline_overlap": pipeline_failure,
        "exact_board_acceptance_checks": failed_acceptance_checks(runner),
    }


def first_structured_error(structured: dict[str, Any]) -> str | None:
    for row in structured.get("protocol_monitors", []):
        if not isinstance(row, dict):
            continue
        violations = row.get("violations")
        if isinstance(violations, list) and violations:
            return (
                f"protocol monitor {row.get('monitor_id') or row.get('interface') or 'unknown'} "
                f"violation: {json.dumps(violations[0], sort_keys=True, ensure_ascii=True)}"
            )[:2000]
        if row.get("status") == "fail":
            return f"protocol monitor {row.get('monitor_id') or row.get('interface') or 'unknown'} failed"
    hierarchy = structured.get("elaborated_hierarchy", {})
    if isinstance(hierarchy, dict) and hierarchy:
        for field in ("errors", "blockers", "failed_checks"):
            values = hierarchy.get(field)
            if isinstance(values, list) and values:
                return f"elaborated hierarchy {field}: {values[0]}"[:2000]
        return "elaborated hierarchy report is invalid"
    pipeline = structured.get("pipeline_overlap", {})
    if isinstance(pipeline, dict) and pipeline:
        for field in ("errors", "blockers", "failed_checks"):
            values = pipeline.get(field)
            if isinstance(values, list) and values:
                return f"pipeline overlap {field}: {values[0]}"[:2000]
        if pipeline.get("status") == "fail":
            return "pipeline overlap report failed"
    checks = structured.get("exact_board_acceptance_checks", [])
    if isinstance(checks, list) and checks:
        return f"exact board acceptance check failed: {checks[0].get('name') or checks[0]}"[:2000]
    return None


def adaptive_semantic_stall_from_runner(runner: dict[str, Any]) -> dict[str, Any]:
    run_result = runner.get("run", {}) if isinstance(runner.get("run"), dict) else {}
    progress_summary = (
        runner.get("progress_event_summary", {})
        if isinstance(runner.get("progress_event_summary"), dict)
        else {}
    )
    live_progress = (
        runner.get("live_progress", {})
        if isinstance(runner.get("live_progress"), dict)
        else {}
    )
    live_latest = (
        live_progress.get("latest", {})
        if isinstance(live_progress.get("latest"), dict)
        else {}
    )
    candidates = (
        runner.get("adaptive_semantic_stall_evidence"),
        run_result.get("adaptive_semantic_stall_evidence"),
        progress_summary.get("adaptive_semantic_stall_evidence"),
        live_latest.get("adaptive_semantic_stall_evidence"),
    )
    for value in candidates:
        normalized = normalize_adaptive_semantic_stall_evidence(value)
        if normalized.get("status") == "proven_semantic_stall":
            return normalized
    return {}


def zero_time_livelock_from_runner(runner: dict[str, Any]) -> dict[str, Any]:
    run_result = runner.get("run", {}) if isinstance(runner.get("run"), dict) else {}
    live_progress = (
        runner.get("live_progress", {})
        if isinstance(runner.get("live_progress"), dict)
        else {}
    )
    live_latest = (
        live_progress.get("latest", {})
        if isinstance(live_progress.get("latest"), dict)
        else {}
    )
    candidates = (
        runner.get("zero_time_livelock_evidence"),
        run_result.get("zero_time_livelock_evidence"),
        live_latest.get("zero_time_livelock_evidence"),
    )
    return next(
        (
            value
            for value in candidates
            if isinstance(value, dict)
            and value.get("status") == "proven_zero_time_livelock"
        ),
        {},
    )


def intra_layer_pipeline_violation_from_runner(
    runner: dict[str, Any],
) -> dict[str, Any]:
    run_result = runner.get("run", {}) if isinstance(runner.get("run"), dict) else {}
    progress_summary = (
        runner.get("progress_event_summary", {})
        if isinstance(runner.get("progress_event_summary"), dict)
        else {}
    )
    live_progress = (
        runner.get("live_progress", {})
        if isinstance(runner.get("live_progress"), dict)
        else {}
    )
    live_latest = (
        live_progress.get("latest", {})
        if isinstance(live_progress.get("latest"), dict)
        else {}
    )
    candidates = (
        runner.get("intra_layer_pipeline_violation_evidence"),
        run_result.get("intra_layer_pipeline_violation_evidence"),
        progress_summary.get("intra_layer_pipeline_violation_evidence"),
        live_latest.get("intra_layer_pipeline_violation_evidence"),
    )
    return next(
        (
            value
            for value in candidates
            if isinstance(value, dict)
            and value.get("status") == "proven_pipeline_violation"
        ),
        {},
    )


def checkpoint_runtime_capability_failure(runner: dict[str, Any]) -> dict[str, Any]:
    """Return only an executed, trigger-bound checkpoint capability failure."""

    checkpoint_artifacts = (
        runner.get("checkpoint_artifacts", {})
        if isinstance(runner.get("checkpoint_artifacts"), dict)
        else {}
    )
    candidates = (
        runner.get("checkpoint_runtime_execution_failure"),
        checkpoint_artifacts.get("runtime_execution_failure"),
    )
    for value in candidates:
        if not isinstance(value, dict) or value.get("status") != "ready":
            continue
        trigger = (
            value.get("trigger_observation", {})
            if isinstance(value.get("trigger_observation"), dict)
            else {}
        )
        mode = str(value.get("mode") or checkpoint_artifacts.get("mode") or "")
        if mode != "cold_capture" or trigger.get("status") == "observed":
            return value
    return {}


def termination_provenance_from_runner(
    runner: dict[str, Any],
) -> dict[str, Any]:
    """Return the runner's single bounded simulator termination record."""

    run_result = (
        runner.get("run", {}) if isinstance(runner.get("run"), dict) else {}
    )
    for candidate in (
        run_result.get("termination_provenance"),
        runner.get("termination_provenance"),
    ):
        if isinstance(candidate, dict) and candidate:
            return candidate
    return {}


def classify_manifest_runner_failure(
    runner: dict[str, Any], compile_text: str, simulation_text: str
) -> tuple[str, str]:
    phase = str(runner.get("phase") or "unknown")
    run_result = (
        runner.get("run", {}) if isinstance(runner.get("run"), dict) else {}
    )

    # A fast-replay restore check is still a real VCS execution.  Its runtime
    # conclusion must win over the execution-layer phase name, otherwise a
    # proven simulator livelock is mislabeled as a generic board-runner error.
    if phase == "fast_replay_restore_check":
        zero_time_livelock = zero_time_livelock_from_runner(runner)
        if (
            run_result.get("returncode") == ZERO_TIME_LIVELOCK_EXIT_CODE
            and run_result.get("failure_class") == "zero_time_simulation_livelock"
            and zero_time_livelock.get("status")
            == "proven_zero_time_livelock"
        ):
            return "vcs_runtime_zero_time_livelock", "board_rtl_or_testbench"
        semantic_stall = adaptive_semantic_stall_from_runner(runner)
        if (
            run_result.get("returncode") == SEMANTIC_STALL_EXIT_CODE
            and semantic_stall.get("status") == "proven_semantic_stall"
        ):
            return "vcs_runtime_semantic_stall", "board_rtl_or_testbench"

    if runner.get("failure_class") == "remote_artifact_persistence_failure":
        return "remote_artifact_persistence_failure", "remote_transport_retry"
    if phase == "manifest_validation":
        return "manifest_validation_failure", "verification_capability"
    if phase == "tool_resolution":
        return "tool_resolution_failure", "verification_capability"
    if phase == "remote_recovery_indeterminate":
        failure_class = str(runner.get("failure_class") or "remote_recovery_indeterminate")
        return failure_class, "remote_transport_retry"
    if phase in {"remote_prepare", "remote_sync", "remote_extract"}:
        return "remote_transport_failure", "remote_transport_retry"
    if phase != "remote_vcs":
        return str(runner.get("failure_class") or "board_runner_failure"), "verification_capability"

    checkpoint_execution = (
        runner.get("checkpoint_execution", {})
        if isinstance(runner.get("checkpoint_execution"), dict)
        else {}
    )
    checkpoint_artifacts = (
        runner.get("checkpoint_artifacts", {})
        if isinstance(runner.get("checkpoint_artifacts"), dict)
        else {}
    )
    compile_result = (
        runner.get("compile", {})
        if isinstance(runner.get("compile"), dict)
        else {}
    )
    if (
        checkpoint_execution.get("enabled") is True
        and checkpoint_execution.get("required_for_stage3_repair") is True
        and checkpoint_artifacts.get("status") == "fail"
        and checkpoint_runtime_capability_failure(runner)
        and run_result.get("status") == "pass"
    ):
        return (
            "simulation_checkpoint_capability_missing_or_invalid",
            "verification_capability",
        )

    if compile_result.get("status") != "pass":
        nested_class = str(compile_result.get("failure_class") or "")
        if nested_class in TRANSPORT_FAILURE_CLASSES:
            return "remote_transport_failure", "remote_transport_retry"
        if nested_class == "remote_tool_poll_budget_exhausted":
            return nested_class, "remote_transport_retry"
        if nested_class == "remote_stage_cleanup_failure":
            return "vcs_execution_environment_failure", "execution_environment_retry"
        compile_diagnostic = real_error_context(compile_text)
        if EXECUTION_ENVIRONMENT_ERROR_RE.search(compile_diagnostic):
            return "vcs_execution_environment_failure", "execution_environment_retry"
        if LIBRARY_ERROR_RE.search(compile_diagnostic):
            return "vcs_library_resolution_failure", "simulation_environment"
        if ELABORATION_ERROR_RE.search(compile_diagnostic):
            return "vcs_elaboration_failure", "board_binding_or_generated_rtl"
        return "vcs_compile_failure", "generated_source_or_compile_plan"
    termination_provenance = termination_provenance_from_runner(runner)
    termination_source = str(
        termination_provenance.get("termination_source") or ""
    )
    if run_result.get("status") != "pass" and termination_provenance:
        causal_classification = (
            termination_provenance.get("causal_classification", {})
            if isinstance(
                termination_provenance.get("causal_classification"), dict
            )
            else {}
        )
        if (
            causal_classification.get("classification")
            == "simulator_process_crash"
            and causal_classification.get(
                "simulator_infrastructure_failure_proven"
            )
            is True
            and causal_classification.get("source_semantic_repair_eligible")
            is False
        ):
            return "vcs_simulator_process_crash", "simulation_environment"
        if termination_source == "remote_transport_indeterminate":
            return "remote_transport_failure", "remote_transport_retry"
        if termination_provenance.get("status") != "complete":
            return (
                "vcs_termination_provenance_incomplete",
                "verification_capability",
            )
        if termination_source in {
            "wall_clock_poll_budget_expired",
            "remote_process_disappeared_without_exit_record",
        }:
            return (
                "vcs_execution_environment_failure",
                "execution_environment_retry",
            )
        if termination_source == "non_framework_signal_exit":
            return (
                "vcs_external_or_signal_termination",
                "execution_environment_retry",
            )
        if termination_source == "runner_owned_simulator_signal_exit":
            return (
                "vcs_simulator_signal_exit_unattributed",
                "verification_capability",
            )
    pipeline_violation = intra_layer_pipeline_violation_from_runner(runner)
    if pipeline_violation:
        contradiction = board_to_lower_layer_contradiction_from_runner(
            runner,
            target_debug_layer="single_transformer_layer_kernel",
        )
        if contradiction.get("status") == "proven":
            return (
                "intra_layer_spatial_pipeline_violation",
                "single_transformer_layer_kernel",
            )
        return "board_output_lifecycle_frontier_violation", "board_rtl_or_testbench"
    if run_result.get("status") != "pass":
        nested_class = str(run_result.get("failure_class") or "")
        if nested_class in TRANSPORT_FAILURE_CLASSES:
            return "remote_transport_failure", "remote_transport_retry"
        if nested_class == "remote_tool_poll_budget_exhausted":
            return nested_class, "remote_transport_retry"
        zero_time_livelock = zero_time_livelock_from_runner(runner)
        if (
            run_result.get("returncode") == ZERO_TIME_LIVELOCK_EXIT_CODE
            and nested_class == "zero_time_simulation_livelock"
            and zero_time_livelock.get("status")
            == "proven_zero_time_livelock"
        ):
            return "vcs_runtime_zero_time_livelock", "board_rtl_or_testbench"
        semantic_stall = adaptive_semantic_stall_from_runner(runner)
        if (
            run_result.get("returncode") == SEMANTIC_STALL_EXIT_CODE
            and semantic_stall.get("status") == "proven_semantic_stall"
        ):
            return "vcs_runtime_semantic_stall", "board_rtl_or_testbench"
        terminal_log = termination_provenance.get(
            "simulator_terminal_log", {}
        )
        terminal_log = terminal_log if isinstance(terminal_log, dict) else {}
        if (
            termination_source == "nonzero_process_exit"
            and terminal_log.get("status") != "observed"
        ):
            return "vcs_runtime_unclassified_exit", "verification_capability"
        return "vcs_runtime_failure", "board_rtl_or_testbench"
    if runner.get("elaborated_hierarchy_report_valid") is False:
        return "elaborated_hierarchy_failure", "board_binding_or_generated_rtl"
    if runner.get("structured_monitors_passed") is False:
        return "protocol_monitor_failure", "board_rtl_or_testbench"
    if runner.get("pipeline_overlap_passed") is False:
        return "pipeline_overlap_failure", "board_rtl_or_testbench"
    if runner.get("required_outputs_copied") is False:
        return "runtime_output_capture_failure", "board_rtl_or_testbench"
    if runner.get("pass_regex_matched") is False:
        return "vcs_runtime_completion_failure", "board_rtl_or_testbench"
    if runner.get("exact_board_acceptance_passed") is False:
        return "exact_board_acceptance_failure", "board_binding_or_generated_rtl"
    return "board_execution_contract_failure", "board_rtl_or_testbench"


def failure_summary(failure_class: str, first_error: str | None) -> str:
    if first_error:
        return f"{failure_class}: {first_error}"
    summaries = {
        "manifest_validation_failure": "exact-board VCS manifest failed validation before remote execution",
        "tool_resolution_failure": "the configured VCS tool binding could not be resolved",
        "remote_transport_failure": "remote VCS transport or staging failed before a determinate tool result",
        "remote_artifact_persistence_failure": "real-tool evidence could not be durably archived or acknowledged",
        "simulation_checkpoint_capability_missing_or_invalid": "required simulation checkpoint capture or restore evidence is missing or invalid",
        "vcs_library_resolution_failure": "VCS could not resolve a required compiled simulation library",
        "vcs_execution_environment_failure": "the remote VCS execution environment exhausted required storage",
        "vcs_compile_failure": "VCS source compilation failed",
        "vcs_elaboration_failure": "VCS elaboration of the exact-board hierarchy failed",
        "vcs_runtime_failure": "the compiled exact-board simulator exited with failure",
        "vcs_simulator_process_crash": (
            "the exact-board simulator process crashed without evidence authorizing a semantic source repair"
        ),
        "vcs_runtime_unclassified_exit": (
            "the exact-board simulator exited nonzero without a terminal diagnostic"
        ),
        "vcs_termination_provenance_incomplete": (
            "the exact-board runner could not determine how the simulator ended"
        ),
        "vcs_external_or_signal_termination": (
            "the exact-board simulator was terminated by a non-framework signal"
        ),
        "vcs_simulator_signal_exit_unattributed": (
            "the runner observed a simulator-process signal exit without a deterministic HDL or testbench event"
        ),
        "vcs_runtime_zero_time_livelock": (
            "the exact-board simulator remained alive while simulation time stopped advancing"
        ),
        "vcs_runtime_semantic_stall": "the exact-board simulator proved semantic stagnation before terminal output",
        "elaborated_hierarchy_failure": "the structured elaborated-hierarchy contract failed",
        "protocol_monitor_failure": "one or more structured AXI protocol monitors failed",
        "pipeline_overlap_failure": "the structured pipeline-overlap contract failed",
        "intra_layer_spatial_pipeline_violation": (
            "the executed kernel drained all input tokens before producing its first output, "
            "contradicting the required spatial operator pipeline"
        ),
        "board_output_lifecycle_frontier_violation": (
            "the board trace reached a ready output frontier without output progress, but does not yet "
            "contain the direct core-boundary evidence required to reopen a certified lower layer"
        ),
        "runtime_output_capture_failure": "required exact-board runtime outputs were not captured",
        "vcs_runtime_completion_failure": "the simulator completed without the required pass marker",
        "rtl_semantic_mismatch": "exact-board RTL output failed target-model semantic comparison",
        "semantic_evidence_missing": "semantic comparison inputs or hashes are missing",
    }
    return summaries.get(failure_class, failure_class.replace("_", " "))


def analyze_manifest_board(run_dir: Path) -> dict[str, Any]:
    runner_path = run_dir / "verification" / "vcs" / "case_board_vcs_functional.json"
    board_manifest_path = run_dir / "verification" / "board_simulation" / "board_simulation_manifest.json"
    semantic_path = run_dir / "verification" / "semantic_testbench" / "semantic_testbench_manifest.json"
    binding_path = run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"
    identity_path = run_dir / "verification" / "board_interface" / "board_source_identity.json"
    runner = read_json(runner_path)
    stall_sidecar_path = (
        run_dir / "verification" / "vcs" / "live" / "adaptive_semantic_stall.json"
    )
    stall_sidecar = read_optional_json(stall_sidecar_path)
    sidecar_evidence = (
        stall_sidecar.get("evidence", {})
        if isinstance(stall_sidecar.get("evidence"), dict)
        else {}
    )
    if (
        sidecar_evidence.get("status") == "proven_semantic_stall"
        and stall_sidecar.get("input_fingerprint_sha256")
        == runner.get("input_fingerprint_sha256")
        and stall_sidecar.get("remote_workdir") == runner.get("remote_workdir")
    ):
        runner = {
            **runner,
            "adaptive_semantic_stall_evidence": sidecar_evidence,
            "adaptive_semantic_stall_evidence_source": {
                "path": str(stall_sidecar_path),
                "sha256": sha256_file(stall_sidecar_path),
            },
        }
    board_manifest = read_optional_json(board_manifest_path)
    semantic = read_optional_json(semantic_path)
    binding = read_optional_json(binding_path)
    identity = read_optional_json(identity_path)
    executed_manifest_path = report_path(
        run_dir,
        runner.get("executed_manifest"),
        run_dir / "verification" / "board_simulation" / "board_simulation_executed_manifest.json",
    )
    executed_manifest = read_optional_json(executed_manifest_path)
    compile_log_path = report_path(
        run_dir,
        runner.get("compile_log"),
        run_dir / "verification" / "board_simulation" / "compile.log",
    )
    simulation_log_path = report_path(
        run_dir,
        runner.get("sim_log"),
        run_dir / "verification" / "board_simulation" / "simulation.log",
    )
    compile_text = log_tail(
        read_optional_text(compile_log_path),
        nested_tool_text(runner.get("compile")),
    )
    simulation_text = log_tail(
        read_optional_text(simulation_log_path),
        nested_tool_text(runner.get("run")),
    )
    output_path = run_dir / "verification" / "board_simulation" / "rtl_output.memh"
    expected = semantic.get("board", {}).get("expected_output", {}) if isinstance(semantic.get("board"), dict) else {}
    compile_result = runner.get("compile", {}) if isinstance(runner.get("compile"), dict) else {}
    run_result = runner.get("run", {}) if isinstance(runner.get("run"), dict) else {}
    causal_simulation_text = (
        simulation_text if compile_result.get("status") == "pass" else ""
    )
    execution_completed = runner.get("status") == "pass" or (
        runner.get("phase") == "remote_vcs"
        and compile_result.get("status") == "pass"
        and run_result.get("status") == "pass"
    )
    if execution_completed:
        try:
            metrics = semantic_compare(
                output_path,
                expected,
                semantic.get("numeric_comparison_policy", {}),
            )
        except Exception as exc:
            metrics = {"passed": False, "error": f"semantic comparison could not run: {exc}"}
        semantic_status = "pass" if metrics.get("passed") is True else "fail"
    else:
        metrics = {
            "passed": False,
            "not_run_reason": "exact-board VCS execution did not complete",
        }
        semantic_status = "not_run"
    consumed, consumed_source = board_consumed_tensor_hashes(runner, board_manifest, binding)
    testbench = board_manifest.get("testbench", {}) if isinstance(board_manifest.get("testbench"), dict) else {}
    semantic_comparison = {
        "status": semantic_status,
        "passed": metrics.get("passed") is True,
        "expected_output_source": "target_model_inference",
        "expected_output_sha256": expected.get("sha256"),
        "rtl_output_sha256": sha256_file(output_path) if output_path.is_file() else None,
        "testbench_sha256": testbench.get("sha256"),
        "consumed_tensor_hashes": consumed,
        "consumed_tensor_hash_source": consumed_source,
        "numeric_metrics": metrics,
    }
    copied_outputs = (
        runner.get("outputs", {}) if isinstance(runner.get("outputs"), dict) else {}
    )
    copied_boundary = (
        copied_outputs.get("boundary_trace_file", {})
        if isinstance(copied_outputs.get("boundary_trace_file"), dict)
        else {}
    )
    trace_source = report_path(
        run_dir,
        copied_boundary.get("path"),
        run_dir / "verification" / "board_simulation" / "boundary_trace.json",
    )
    if not trace_source.is_file():
        jsonl_fallback = (
            run_dir / "verification" / "board_simulation" / "boundary_trace.jsonl"
        )
        if jsonl_fallback.is_file():
            trace_source = jsonl_fallback
    trace_target = run_dir / "verification" / "debug_closure" / "boundary_trace.json"
    trace = load_boundary_trace_evidence(trace_source)
    trace_records = trace.get("records", [])
    trace_ready = isinstance(trace_records, list) and bool(trace_records)
    validation_scope = board_validation_scope_summary(
        run_dir, binding, board_manifest
    )
    if trace_ready:
        write_json(
            trace_target,
            {
                "schema_version": "spatialaccagent.normalized_boundary_trace.v1",
                "status": "ready",
                "source_format": trace.get("source_format"),
                "source_path": str(trace_source),
                "record_count": len(trace_records),
                "invalid_records": trace.get("invalid_records", []),
                "boundary_trace": trace_records,
                "progress_summary": trace.get("progress_summary", {}),
            },
        )
    runner_passed = runner.get("status") == "pass"
    passed = (
        runner_passed
        and semantic_comparison["passed"]
        and identity.get("exact_user_sample_wrapper") is True
        and identity.get("simulation_hashes_match_source") is True
        and validation_scope["status"] == "pass"
        and trace_ready
    )
    runner_tail = log_tail(
        compile_text if compile_result.get("status") != "pass" else "",
        causal_simulation_text,
        str(runner.get("stderr_tail") or ""),
    )
    if runner_passed:
        if semantic_status == "fail":
            failure_class = (
                "semantic_evidence_missing"
                if metrics.get("error")
                else "rtl_semantic_mismatch"
            )
            repair_scope = "board_rtl_or_testbench"
        elif identity.get("exact_user_sample_wrapper") is not True or identity.get("simulation_hashes_match_source") is not True:
            failure_class, repair_scope = "board_wrapper_identity_failure", "board_binding_or_generated_rtl"
        elif validation_scope["status"] != "pass":
            failure_class, repair_scope = "real_weight_binding_failure", "board_rtl_or_testbench"
        elif not trace_ready:
            failure_class, repair_scope = "boundary_trace_failure", "board_rtl_or_testbench"
        else:
            failure_class, repair_scope = "none", "none"
    else:
        failure_class, repair_scope = classify_manifest_runner_failure(
            runner, compile_text, simulation_text
        )
    first_error = first_real_error(
        compile_text if compile_result.get("status") != "pass" else simulation_text,
        runner.get("errors"),
    )
    adaptive_semantic_stall = adaptive_semantic_stall_from_runner(runner)
    zero_time_livelock = zero_time_livelock_from_runner(runner)
    intra_layer_pipeline_violation = intra_layer_pipeline_violation_from_runner(
        runner
    )
    lower_layer_contradiction = board_to_lower_layer_contradiction_from_runner(
        runner,
        target_debug_layer="single_transformer_layer_kernel",
    )
    termination_provenance = termination_provenance_from_runner(runner)
    if failure_class == "vcs_simulator_process_crash":
        terminal_log = (
            termination_provenance.get("simulator_terminal_log", {})
            if isinstance(
                termination_provenance.get("simulator_terminal_log"), dict
            )
            else {}
        )
        crash_lines = ordered_strings(terminal_log.get("simulator_crash_lines"))
        first_error = (
            crash_lines[0]
            if crash_lines
            else "the exact-board simulator process crashed"
        )
    elif failure_class == "vcs_runtime_zero_time_livelock":
        first_error = (
            "VCS simulation time stopped advancing after cycle "
            f"{zero_time_livelock.get('last_cycle')} while the remote simulator "
            "remained alive; this is a proven zero-time simulation livelock, not "
            "a semantic-stall timeout"
        )
    elif failure_class == "vcs_runtime_semantic_stall":
        first_error = (
            "semantic progress stopped at cycle "
            f"{adaptive_semantic_stall.get('last_semantic_event_cycle')} and cumulative "
            "scheduler/layer/bank/workload/AXI state remained unchanged through cycle "
            f"{adaptive_semantic_stall.get('latest_cycle')}"
        )
    elif failure_class == "intra_layer_spatial_pipeline_violation":
        first_error = (
            "all "
            f"{intra_layer_pipeline_violation.get('completed_input_tokens')} input tokens "
            "completed by cycle "
            f"{intra_layer_pipeline_violation.get('final_input_cycle')} while the ready "
            "kernel output accepted zero beats"
        )
    elif failure_class == "board_output_lifecycle_frontier_violation":
        first_error = (
            "the board trace completed current-layer ingress while the ready output frontier "
            "accepted zero beats; direct core-boundary contradiction evidence is still required "
            "before reopening the connected kernel"
        )
    elif failure_class == "simulation_checkpoint_capability_missing_or_invalid":
        checkpoint_artifacts = (
            runner.get("checkpoint_artifacts", {})
            if isinstance(runner.get("checkpoint_artifacts"), dict)
            else {}
        )
        checkpoint_errors = [
            str(value)
            for value in checkpoint_artifacts.get("errors", [])
            if str(value)
        ]
        first_error = (
            checkpoint_errors[0]
            if checkpoint_errors
            else "required checkpoint execution produced no passing capture or restore report"
        )
    runtime_frontier_failure = failure_class in {
        "vcs_runtime_semantic_stall",
        "vcs_runtime_zero_time_livelock",
    }
    structured = (
        {}
        if runtime_frontier_failure
        else structured_failures(runner, executed_manifest)
    )
    if first_error is None:
        first_error = first_structured_error(structured)
    if first_error is None and semantic_status == "fail":
        first_error = str(metrics.get("error") or "") or None
    source_text = "\n".join(
        value
        for value in (first_error or "", compile_text, causal_simulation_text)
        if value
    )
    related_sources = related_source_ids(source_text, board_manifest)
    summary = (
        "exact sample-wrapper board simulation and semantic comparison passed"
        if passed
        else failure_summary(failure_class, first_error)
    )
    blockers = [] if passed else [summary]
    if semantic_status == "fail" and failure_class not in {"rtl_semantic_mismatch", "semantic_evidence_missing"}:
        blockers.append(failure_summary("rtl_semantic_mismatch", None))
    if execution_completed and not trace_ready:
        blockers.append("board testbench did not emit a CCTG boundary trace")
    causal_slice_path = (
        run_dir
        / "verification"
        / "case_diagnostics"
        / "sacg_cctg_causal_slice.json"
    )
    runtime_attempted = (
        compile_result.get("status") == "pass"
        and run_result.get("status") in {"pass", "fail"}
    )
    if runtime_attempted:
        causal_slice = build_sacg_cctg_causal_slice(
            run_dir=run_dir,
            runner=runner,
            executed_manifest=executed_manifest,
            failure_class="none" if passed else failure_class,
            executed_manifest_path=executed_manifest_path,
        )
    else:
        causal_slice = {
            "schema_version": "spatialaccagent.sacg_cctg_causal_slice.v1",
            "status": "not_applicable_before_runtime_execution",
            "run_dir": str(run_dir),
            "input_fingerprint_sha256": runner.get("input_fingerprint_sha256"),
            "remote_workdir": runner.get("remote_workdir"),
            "failure_class": failure_class,
            "reason": (
                "SACG/CCTG runtime frontier selection requires a completed VCS "
                "compile and an attempted simulator execution"
            ),
            "llm_analysis_contract": {
                "use_earliest_real_tool_error_before_runtime_graph": True,
                "must_not_reuse_a_prior_fingerprint_runtime_slice": True,
                "must_not_edit_hardware_for_transport_or_tool_environment_failure": True,
            },
        }
    write_json(causal_slice_path, causal_slice)
    causal_slice_binding = {
        "path": str(causal_slice_path),
        "sha256": sha256_file(causal_slice_path),
        "value": causal_slice,
    }
    sources = [
        str(path)
        for path in (
            runner_path,
            board_manifest_path,
            identity_path,
            binding_path,
            semantic_path,
            compile_log_path,
            simulation_log_path if causal_simulation_text else Path(),
            executed_manifest_path,
            trace_source,
            stall_sidecar_path,
            causal_slice_path,
        )
        if path.is_file()
    ]
    supplemental_observation_artifacts = (
        runner.get("supplemental_observation_artifacts", [])
        if isinstance(runner.get("supplemental_observation_artifacts"), list)
        else []
    )
    sources.extend(
        str(path)
        for row in supplemental_observation_artifacts
        if isinstance(row, dict)
        and row.get("copied") is True
        and (path := Path(str(row.get("path") or ""))).is_file()
    )
    agent_should_apply_code_changes = not passed and repair_scope not in {
        "none",
        "remote_transport_retry",
        "simulation_environment",
        "execution_environment_retry",
    }
    failure_evidence = {
        "runner_phase": str(runner.get("phase") or "unknown"),
        "failure_class": failure_class,
        "repair_scope": repair_scope,
        "first_real_error": first_error,
        "log_tail": runner_tail,
        "related_source_ids": related_sources,
        "compile": {
            key: compile_result.get(key)
            for key in ("status", "returncode", "failure_class", "remote_state", "duration_sec")
            if key in compile_result
        },
        "simulation": {
            key: run_result.get(key)
            for key in ("status", "returncode", "failure_class", "remote_state", "duration_sec", "summary")
            if key in run_result
        },
        "termination_provenance": termination_provenance,
        "structured_failures": structured,
        "live_progress": runner.get("live_progress", {}),
        "progress_event_summary": runner.get("progress_event_summary", {}),
        "supplemental_observation_artifacts": supplemental_observation_artifacts,
        "vcs_native_loop_report": runner.get("vcs_native_loop_report", {}),
        "adaptive_semantic_stall_evidence": adaptive_semantic_stall,
        "zero_time_livelock_evidence": zero_time_livelock,
        "intra_layer_pipeline_violation_evidence": (
            intra_layer_pipeline_violation
        ),
        "board_to_lower_layer_contradiction_evidence": lower_layer_contradiction,
        "checkpoint_execution": runner.get("checkpoint_execution", {}),
        "checkpoint_artifacts": runner.get("checkpoint_artifacts", {}),
        "checkpoint_runtime_execution_failure": (
            checkpoint_runtime_capability_failure(runner)
        ),
    }
    failure_evidence["sacg_cctg_causal_slice"] = causal_slice_binding
    target_debug_layer = (
        "single_transformer_layer_kernel"
        if failure_class == "intra_layer_spatial_pipeline_violation"
        else "board_axi_ddr_wrapped_system"
    )
    applicable_rerun_gates = (
        [
            "case_single_layer_functional",
            "case_vcs_functional_sim",
            "case_vcs_evidence_analyzer",
        ]
        if failure_class == "intra_layer_spatial_pipeline_violation"
        else ["case_vcs_functional_sim", "case_vcs_evidence_analyzer"]
    )
    critical_sources = [
        ("board_vcs_runner_report", runner_path),
        ("board_simulation_manifest", board_manifest_path),
        ("board_source_identity", identity_path),
        ("semantic_testbench_manifest", semantic_path),
        ("dut_weight_binding_manifest", binding_path),
        ("executed_board_manifest", executed_manifest_path),
        ("sacg_cctg_causal_slice", causal_slice_path),
    ]
    source_artifacts = [
        {"role": role, "path": str(path), "sha256": sha256_file(path)}
        for role, path in critical_sources
        if path.is_file()
    ]
    report = {
        "schema_version": "spatialaccagent.case_vcs_functional_diagnosis.v4",
        "status": "pass" if passed else "needs_repair",
        "diagnosis_status": "ready",
        "run_dir": str(run_dir),
        "sources": sources,
        "sim_pass": runner_passed,
        "runner_phase": failure_evidence["runner_phase"],
        "failure_class": "none" if passed else failure_class,
        "root_cause_class": "none" if passed else failure_class,
        "summary": summary,
        "applicability_binding": {
            "schema_version": DIAGNOSIS_APPLICABILITY_BINDING_SCHEMA_VERSION,
            "origin_layer": "board_axi_ddr_wrapped_system",
            "target_layer": target_debug_layer,
            "origin_gates": ["case_vcs_functional_sim"],
            "applicable_rerun_gates": applicable_rerun_gates,
            "diagnosed_failure_class": "none" if passed else failure_class,
            "input_fingerprint_sha256": runner.get("input_fingerprint_sha256"),
            "preflight_manifest_projection_sha256": runner.get(
                "preflight_manifest_projection_sha256"
            ),
            "source_identity_sha256": (
                runner.get("source_identity_sha256")
                or (
                    sha256_file(identity_path)
                    if identity_path.is_file()
                    else None
                )
            ),
            "source_artifacts": source_artifacts,
            "policy": {
                "live_source_artifact_hashes_must_match": True,
                "current_failed_gate_must_match_origin_or_target_rerun_gate": True,
                "cross_layer_reuse_is_read_only_without_an_explicit_targeted_backtrack": True,
            },
        },
        "failure_evidence": failure_evidence,
        "semantic_comparison": semantic_comparison,
        "real_weight_provenance": {
            "binding_manifest": str(binding_path),
            "all_target_layers": binding.get("all_target_layers") is True,
            "all_validation_layers": validation_scope["status"] == "pass",
            "board_validation_scope": validation_scope,
            "consumed_tensor_hashes": consumed,
            "consumed_tensor_hash_source": consumed_source,
        },
        "board_wrapper_identity": {
            "path": str(identity_path),
            "sha256": sha256_file(identity_path) if identity_path.is_file() else None,
            **{
                key: identity.get(key)
                for key in (
                    "schema_version",
                    "status",
                    "exact_user_sample_wrapper",
                    "simulation_hashes_match_source",
                    "selected_simulation_source_closure_sha256",
                    "compute_slot_abi_sha256",
                    "timing_contract_sha256",
                    "axi_interfaces_sha256",
                    "vivado_facts_sha256",
                )
                if key in identity
            },
            "complete_identity_bound_by_path_and_sha256": True,
        },
        "debug_closure": {
            "status": "pass" if passed else ("trace_ready" if trace_ready else "needs_boundary_trace"),
            "boundary_trace_path": str(trace_target),
            "boundary_trace_record_count": len(trace_records),
            "boundary_trace_failed_count": sum(1 for row in trace_records if isinstance(row, dict) and row.get("status") == "fail"),
            "progress_event_summary": trace.get("progress_summary", {}),
            "live_progress": runner.get("live_progress", {}),
        },
        "repair_handoff": {
            "repair_patterns": [],
            "next_stage": None if passed else "repair",
            "agent_should_apply_code_changes": agent_should_apply_code_changes,
            "runner_phase": failure_evidence["runner_phase"],
            "failure_class": "none" if passed else failure_class,
            "repair_scope": repair_scope,
            "debug_layer": (
                target_debug_layer if not passed else None
            ),
            "first_real_error": first_error,
            "termination_causal_classification": (
                termination_provenance.get("causal_classification", {})
                if isinstance(
                    termination_provenance.get("causal_classification"), dict
                )
                else {}
            ),
            "log_tail": runner_tail,
            "related_source_ids": related_sources,
            "structured_failures": structured,
            "sacg_cctg_causal_frontier": {
                "status": causal_slice_binding["value"].get("status"),
                "artifact_path": causal_slice_binding["path"],
                "artifact_sha256": causal_slice_binding["sha256"],
                "earliest_unproven_frontier": causal_slice_binding["value"].get(
                    "earliest_unproven_frontier", {}
                ),
                "hierarchical_certificate_projection": causal_slice_binding[
                    "value"
                ].get("hierarchical_certificate_projection", {}),
            },
            "board_to_lower_layer_contradiction_evidence": lower_layer_contradiction,
            "must_rerun": applicable_rerun_gates,
            "acceptance_contracts_to_revalidate": (
                ["single_layer_pipeline_overlap"]
                if failure_class == "intra_layer_spatial_pipeline_violation"
                else []
            ),
            "acceptance_reminder": "Keep checkpoint, random input, golden, numeric policy, and exact sample wrapper hashes unchanged during repair.",
        },
        "blockers": blockers,
    }
    retry_request_path = runner_path.parent / REMOTE_JOB_RETRY_REQUEST
    remote_workdir = str(
        compile_result.get("remote_workdir")
        or runner.get("remote_workdir")
        or ""
    )
    if (
        failure_class == "vcs_execution_environment_failure"
        and runner.get("input_fingerprint_sha256")
        and remote_workdir
    ):
        write_json(
            retry_request_path,
            {
                "schema_version": "spatialaccagent.remote_job_retry_request.v1",
                "status": "ready",
                "action": (
                    "discard_completed_remote_workdir_and_retry_same_fingerprint"
                ),
                "failure_class": failure_class,
                "input_fingerprint_sha256": runner.get(
                    "input_fingerprint_sha256"
                ),
                "remote_workdir": remote_workdir,
                "runner_report_path": str(runner_path),
                "runner_report_sha256": sha256_file(runner_path),
                "compile_log_path": str(compile_log_path),
                "compile_log_sha256": (
                    sha256_file(compile_log_path)
                    if compile_log_path.is_file()
                    else None
                ),
                "policy": {
                    "hardware_edits_forbidden": True,
                    "remove_only_completed_inactive_exact_fingerprint_job": True,
                    "rerun_current_exact_board_vcs_unchanged": True,
                },
            },
        )
    elif retry_request_path.is_file():
        prior_retry = read_optional_json(retry_request_path)
        if prior_retry.get("input_fingerprint_sha256") == runner.get(
            "input_fingerprint_sha256"
        ):
            retry_request_path.unlink()
    return report


def parse_value(raw: str) -> Any:
    if "/" in raw:
        parts = raw.split("/", 1)
        if all(part.isdigit() for part in parts):
            return {"valid": int(parts[0]), "ready": int(parts[1])}
        return raw
    try:
        return int(raw, 0)
    except ValueError:
        return raw


def parse_fields(text: str) -> dict[str, Any]:
    return {match.group("key"): parse_value(match.group("value")) for match in FIELD_RE.finditer(text)}


def load_tool_text(run_dir: Path) -> tuple[str, list[str]]:
    case_paths = [
        run_dir / "verification" / "real_tools" / "case_vcs_functional_sim.json",
        run_dir / "verification" / "real_tools" / "case_vcs_liveness.json",
    ]
    legacy_paths = [
        run_dir / "verification" / "real_tools" / "case_vcs_functional_sim.json",
        run_dir / "verification" / "real_tools" / "case_vcs_smoke.json",
    ]
    paths = case_paths if any(path.exists() for path in case_paths) else legacy_paths
    chunks: list[str] = []
    sources: list[str] = []
    for path in paths:
        if not path.exists():
            continue
        data = read_json(path)
        sources.append(str(path))
        chunks.extend(
            str(data.get(name) or "")
            for name in ["stdout_tail", "stderr_tail", "summary"]
            if data.get(name)
        )
    case_logs = [
        run_dir / "verification" / "vcs" / "case_functional_sim.log",
    ]
    legacy_logs = [
        run_dir / "verification" / "vcs" / "case_functional_sim.log",
    ]
    for remote_sim_log in case_logs if any(path.exists() for path in case_logs) else legacy_logs:
        if remote_sim_log.exists():
            sources.append(str(remote_sim_log))
            chunks.append(remote_sim_log.read_text(encoding="utf-8", errors="ignore"))
    return "\n".join(chunks), sources


def max_counter(progress: list[dict[str, Any]], key: str) -> int:
    values = [item.get(key) for item in progress if isinstance(item.get(key), int)]
    return max(values) if values else 0


def latest(progress: list[dict[str, Any]]) -> dict[str, Any]:
    return progress[-1] if progress else {}


def write_pipeline_boundary_trace(
    run_dir: Path,
    progress: list[dict[str, Any]],
    fatal: dict[str, Any] | None,
    pass_fields: dict[str, Any] | None,
    sim_pass: bool,
    root_cause: str,
) -> Path:
    final = latest(progress)
    fatal_fields = fatal or {}
    pass_values = pass_fields or {}
    cycle = int(final.get("cycle") or fatal_fields.get("cycle") or 0)
    counters = [
        ("input_read_beats", "input_beats", "boundary.board.input_ddr_read", "GeneratedAxiDdrTop.read_path"),
        ("weight_read_beats", "weight_beats", "boundary.board.weight_ddr_read", "GeneratedAxiDdrTop.weight_prefetch"),
        ("output_valid_beats", "out_valid", "boundary.board.output_valid", "CaseAxiBoardSystemTop.output_capture"),
        ("output_write_beats", "out_write", "boundary.board.output_ddr_write", "GeneratedAxiDdrTop.write_path"),
    ]
    records = []
    for index, (progress_key, pass_key, boundary_id, module) in enumerate(counters):
        observed = max(max_counter(progress, progress_key), int(fatal_fields.get(progress_key, 0) or 0))
        if pass_key:
            observed = max(observed, int(pass_values.get(pass_key, 0) or 0))
        if observed > 0:
            status = "pass"
        elif sim_pass:
            status = "warning"
        else:
            status = "fail"
        records.append(
            {
                "cycle": cycle,
                "boundary_id": boundary_id,
                "tx_id": "board_run.final_progress",
                "tile_id": None,
                "logical_index": index,
                "observed_value": observed,
                "expected_value": ">0 accepted beats",
                "contract": "board_wrapped_pipeline_boundary_must_make_progress",
                "status": status,
                "module": module,
                "root_cause_class": root_cause if status == "fail" else None,
            }
        )
    path = run_dir / "verification" / "debug_closure" / "boundary_trace.json"
    write_json(
        path,
        {
            "schema_version": "spatialaccagent.boundary_trace.v0",
            "status": "pass" if sim_pass else "ready",
            "source": "case_vcs_functional_sim",
            "failure_scope": "board_axi_ddr_runtime_boundary",
            "record_count": len(records),
            "failed_count": sum(1 for item in records if item["status"] == "fail"),
            "boundary_trace": records,
        },
    )
    return path


def load_boundary_trace(run_dir: Path) -> dict[str, Any]:
    path = run_dir / "verification" / "debug_closure" / "boundary_trace.json"
    if not path.exists():
        return {"status": "missing", "path": str(path), "boundary_trace": []}
    try:
        data = read_json(path)
    except Exception as exc:
        return {"status": "unreadable", "path": str(path), "error": str(exc), "boundary_trace": []}
    records = data.get("boundary_trace") if isinstance(data.get("boundary_trace"), list) else data.get("records", [])
    records = [item for item in records if isinstance(item, dict)] if isinstance(records, list) else []
    failed = [item for item in records if str(item.get("status") or "").lower() == "fail"]
    return {
        "status": "ready",
        "path": str(path),
        "record_count": len(records),
        "failed_count": len(failed),
        "boundary_trace": records[:256],
    }


def classify(
    progress: list[dict[str, Any]],
    fatal: dict[str, Any] | None,
    sim_pass: bool,
    run_dir: Path,
) -> tuple[str, str]:
    """Classify only board-level facts from the legacy text fallback.

    Current runs use the manifest-driven analyzer and compiled runtime signal
    catalog.  This fallback intentionally does not infer model-specific RTL
    edits from coarse progress counters.
    """

    del run_dir
    if sim_pass:
        return "none", "functional simulation passed with real DDR path evidence"
    if not progress and not fatal:
        return "missing_sim_log", "VCS tool did not emit parseable case_axi_board_tb progress or fatal evidence"
    input_beats = max(max_counter(progress, "input_read_beats"), int((fatal or {}).get("input_read_beats", 0) or 0))
    weight_beats = max(max_counter(progress, "weight_read_beats"), int((fatal or {}).get("weight_read_beats", 0) or 0))
    output_beats = max(max_counter(progress, "output_valid_beats"), int((fatal or {}).get("output_valid_beats", 0) or 0))
    if input_beats == 0 or weight_beats == 0:
        return "real_ddr_path_not_exercised", "functional simulation did not consume both input and weight DDR images"
    if output_beats > 0:
        return "output_started_but_completion_failed", "top-level output appeared but completion/done evidence failed"
    if fatal and str(fatal.get("kind")) in {"NO_PROGRESS", "TIMEOUT"}:
        return "board_pipeline_or_output_stall", "real DDR input and weight paths ran, but board output was not observed before the watchdog"
    return "board_pipeline_or_output_not_observed", "board-level progress is incomplete; use the current compiled signal catalog to localize the earliest stopped boundary"

def analyze(run_dir: Path) -> dict[str, Any]:
    if (run_dir / "verification" / "vcs" / "case_board_vcs_functional.json").exists():
        return analyze_manifest_board(run_dir)
    text, sources = load_tool_text(run_dir)
    progress: list[dict[str, Any]] = []
    fatal: dict[str, Any] | None = None
    pass_fields: dict[str, Any] | None = None
    for line in text.splitlines():
        match = PROGRESS_RE.search(line)
        if match:
            progress.append(parse_fields(match.group("fields")))
            continue
        match = FATAL_RE.search(line)
        if match:
            fatal = {"kind": match.group("kind"), **parse_fields(match.group("fields"))}
            continue
        match = PASS_RE.search(line)
        if match:
            pass_fields = parse_fields(match.group("fields"))
    sim_pass = pass_fields is not None
    root_cause, summary = classify(progress, fatal, sim_pass, run_dir)
    write_pipeline_boundary_trace(run_dir, progress, fatal, pass_fields, sim_pass, root_cause)
    boundary_trace = load_boundary_trace(run_dir)
    observed = {
        "progress_samples": len(progress),
        "input_read_beats": max_counter(progress, "input_read_beats"),
        "weight_read_beats": max_counter(progress, "weight_read_beats"),
        "output_valid_beats": max_counter(progress, "output_valid_beats"),
        "output_write_beats": max_counter(progress, "output_write_beats"),
        "last_progress": latest(progress),
        "fatal": fatal,
        "pass_fields": pass_fields,
    }
    debug_status = "pass" if sim_pass else ("trace_ready" if boundary_trace.get("status") == "ready" and boundary_trace.get("record_count", 0) else "needs_boundary_trace")
    return {
        "schema_version": "spatialaccagent.case_vcs_functional_diagnosis.v0",
        "status": "pass" if sim_pass else "needs_repair",
        "diagnosis_status": "ready" if sources else "missing_evidence",
        "run_dir": str(run_dir),
        "sources": sources,
        "sim_pass": sim_pass,
        "root_cause_class": root_cause,
        "summary": summary,
        "debug_closure": {
            "status": debug_status,
            "boundary_trace_path": boundary_trace.get("path"),
            "boundary_trace": boundary_trace.get("boundary_trace", []),
            "boundary_trace_record_count": boundary_trace.get("record_count", 0),
            "boundary_trace_failed_count": boundary_trace.get("failed_count", 0),
            "required_next_action": None if sim_pass or debug_status == "trace_ready" else "rerun case_vcs_functional_sim with SPATIALACC_BOUNDARY_TRACE=1",
        },
        "observed": observed,
        "repair_handoff": {
            "repair_patterns": [],
            "next_stage": "repair",
            "agent_should_apply_code_changes": not sim_pass,
            "must_rerun": ["case_tb_scaffold_generate", "case_stage_leaf_static", "case_axi_ddr_interface", "case_vcs_functional_sim"],
            "acceptance_reminder": "A smoke/liveness pass is not functional acceptance; require case_vcs_functional_sim pass with real DDR path counters.",
        },
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze case VCS functional-sim logs and generate repair handoff")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    run_dir = args.run_dir.resolve()
    out = args.out or run_dir / "verification" / "case_vcs" / "case_vcs_functional_diagnosis.json"
    report = analyze(run_dir)
    write_json(out, report)
    write_json(out.parent / "repair_handoff.json", report["repair_handoff"])
    print(out)
    print(out.parent / "repair_handoff.json")
    return 0 if report["diagnosis_status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
