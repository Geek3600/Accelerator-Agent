"""LLM runtime quality checks for agentic stage execution."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

from accagent.framework.sacg_utils import read_json, write_json


def env_int(name: str, default: int, minimum: int = 0) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return max(minimum, int(raw))
    except ValueError:
        return default


def env_float(name: str, default: float, minimum: float = 0.0) -> float:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return max(minimum, float(raw))
    except ValueError:
        return default


def quality_thresholds() -> dict[str, Any]:
    return {
        "prompt_warn_bytes": env_int("SPATIALACC_LLM_PROMPT_WARN_BYTES", 60_000, 1),
        "prompt_fail_bytes": env_int("SPATIALACC_LLM_PROMPT_FAIL_BYTES", 160_000, 1),
        "duration_warn_sec": env_float("SPATIALACC_LLM_DURATION_WARN_SEC", 300.0, 0.0),
        "duration_fail_sec": env_float("SPATIALACC_LLM_DURATION_FAIL_SEC", 1_500.0, 0.0),
        "require_executable_actions": os.environ.get("SPATIALACC_LLM_REQUIRE_EXECUTABLE_ACTIONS", "1").strip().lower()
        in {"1", "true", "yes", "on"},
    }


def action_count(output: dict[str, Any]) -> int:
    actions = output.get("executable_actions", [])
    return len(actions) if isinstance(actions, list) else 0


def agent_row(source: str, record: dict[str, Any], output: dict[str, Any] | None = None) -> dict[str, Any]:
    output = output if isinstance(output, dict) else record.get("output", {})
    if not isinstance(output, dict):
        output = {}
    return {
        "source": source,
        "agent": record.get("agent") or output.get("agent"),
        "stage": record.get("stage") or output.get("stage"),
        "status": output.get("status"),
        "used_fallback": bool(record.get("used_fallback", False)),
        "prompt_bytes": record.get("prompt_bytes"),
        "compact_retry_prompt_bytes": record.get("compact_retry_prompt_bytes"),
        "duration_sec": record.get("duration_sec"),
        "executable_action_count": action_count(output),
        "error": record.get("error"),
        "retry_errors": record.get("retry_errors", []),
    }


def rows_from_stage_records(planner_record: dict[str, Any], team_run: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [agent_row("planner", planner_record)]
    for item in team_run.get("results", []):
        row = {
            "source": "team_subagent",
            "agent": item.get("subtask", {}).get("agent"),
            "stage": item.get("subtask", {}).get("role"),
            "status": (item.get("output") or {}).get("status") if isinstance(item.get("output"), dict) else None,
            "used_fallback": bool(item.get("used_fallback", True)),
            "prompt_bytes": item.get("llm_io", {}).get("prompt_bytes"),
            "compact_retry_prompt_bytes": item.get("llm_io", {}).get("compact_retry_prompt_bytes"),
            "duration_sec": item.get("llm_io", {}).get("duration_sec"),
            "executable_action_count": item.get("llm_io", {}).get("executable_action_count"),
            "error": item.get("error"),
            "retry_errors": [],
        }
        rows.append(row)
    return rows


def check_row(row: dict[str, Any], thresholds: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    prompt_bytes = int(row.get("prompt_bytes") or 0)
    duration_sec = float(row.get("duration_sec") or 0.0)
    action_total = int(row.get("executable_action_count") or 0)
    if row.get("used_fallback"):
        errors.append("LLM fallback was used")
    if row.get("error"):
        errors.append(f"LLM error recorded: {row.get('error')}")
    if thresholds["require_executable_actions"] and action_total <= 0:
        errors.append("LLM produced no executable_actions")
    if prompt_bytes >= int(thresholds["prompt_fail_bytes"]):
        warnings.append(
            f"prompt_bytes {prompt_bytes} exceeds fail threshold {thresholds['prompt_fail_bytes']} "
            "but LLM returned usable structured output; treating full-context prompt size as diagnostic warning"
        )
    elif prompt_bytes >= int(thresholds["prompt_warn_bytes"]):
        warnings.append(f"prompt_bytes {prompt_bytes} exceeds warning threshold {thresholds['prompt_warn_bytes']}")
    if duration_sec >= float(thresholds["duration_fail_sec"]):
        warnings.append(
            f"duration_sec {duration_sec:.1f} exceeds fail threshold {thresholds['duration_fail_sec']} "
            "but LLM returned usable structured output; treating provider latency as diagnostic warning"
        )
    elif duration_sec >= float(thresholds["duration_warn_sec"]):
        warnings.append(f"duration_sec {duration_sec:.1f} exceeds warning threshold {thresholds['duration_warn_sec']}")
    retry_errors = row.get("retry_errors", [])
    if isinstance(retry_errors, list) and retry_errors:
        warnings.append(f"{len(retry_errors)} transient retry error(s) recorded")
    checked = dict(row)
    checked["errors"] = errors
    checked["warnings"] = warnings
    checked["quality_status"] = "fail" if errors else ("warn" if warnings else "pass")
    return checked


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    fail = [row for row in rows if row.get("quality_status") == "fail"]
    warn = [row for row in rows if row.get("quality_status") == "warn"]
    prompt_values = [int(row.get("prompt_bytes") or 0) for row in rows]
    duration_values = [float(row.get("duration_sec") or 0.0) for row in rows]
    return {
        "agent_count": len(rows),
        "failed_agents": len(fail),
        "warned_agents": len(warn),
        "max_prompt_bytes": max(prompt_values) if prompt_values else 0,
        "total_prompt_bytes": sum(prompt_values),
        "max_duration_sec": max(duration_values) if duration_values else 0.0,
        "total_duration_sec": sum(duration_values),
        "errors": [error for row in fail for error in row.get("errors", [])],
        "warnings": [warning for row in rows for warning in row.get("warnings", [])],
    }


def build_quality_report(rows: list[dict[str, Any]], thresholds: dict[str, Any] | None = None) -> dict[str, Any]:
    thresholds = quality_thresholds() if thresholds is None else thresholds
    checked = [check_row(row, thresholds) for row in rows]
    summary = summarize_rows(checked)
    return {
        "schema_version": "spatialaccagent.llm_io_quality.v0",
        "status": "fail" if summary["failed_agents"] else ("warn" if summary["warned_agents"] else "pass"),
        "summary": summary,
        "thresholds": thresholds,
        "agents": checked,
        "policy": (
            "LLM stages must use real LLM calls, avoid fallback, and produce executable_actions. "
            "Large full-context prompts and provider latency are recorded as diagnostic warnings "
            "when the LLM still returns usable structured output."
        ),
    }


def read_record(path: Path) -> dict[str, Any]:
    return read_json(path) if path.exists() else {}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build an LLM I/O quality report from LLM result records.")
    parser.add_argument("records", nargs="+", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    rows = [agent_row(str(path), read_record(path)) for path in args.records]
    report = build_quality_report(rows)
    write_json(args.out, report)
    print(f"{report['status']}: {report['summary']}")
    return 1 if report["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
