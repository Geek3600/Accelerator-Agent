"""Audit stale LLM fallback evidence in a SpatialAccAgent run directory."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from accagent.framework.sacg_utils import read_json, write_json


DEFAULT_STAGE_DIRS = [
    "verification_artifacts",
    "verification",
    "repair",
    "backend_board",
]


def read_json_or_empty(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return read_json(path)
    except Exception:
        return {}


def stale_llm_record(path: Path, data: dict[str, Any]) -> dict[str, Any] | None:
    if not data:
        return None
    mode = str(data.get("mode") or "").strip().lower()
    used_fallback = bool(data.get("used_fallback"))
    error = data.get("error")
    output = data.get("output", {}) if isinstance(data.get("output"), dict) else {}
    output_status = str(output.get("status") or "").strip().lower()
    reasons = []
    if mode in {"off", "none", "disabled"}:
        reasons.append(f"llm mode was {mode}")
    if used_fallback:
        reasons.append("record used fallback")
    if error:
        reasons.append(f"record has error: {error}")
    if output_status in {"fallback", "unavailable"}:
        reasons.append(f"output status is {output_status}")
    if not reasons:
        return None
    return {
        "path": str(path),
        "kind": "llm_worker_record",
        "mode": data.get("mode"),
        "used_fallback": used_fallback,
        "error": error,
        "output_status": output.get("status"),
        "reasons": reasons,
    }


def stale_team_record(path: Path, data: dict[str, Any]) -> dict[str, Any] | None:
    if not data:
        return None
    fallback_count = int(data.get("used_fallback_count", 0) or 0)
    errors = data.get("errors", []) if isinstance(data.get("errors"), list) else []
    status = str(data.get("status") or "").strip().lower()
    reasons = []
    if fallback_count:
        reasons.append(f"team used {fallback_count} fallback sub-agent(s)")
    if errors:
        reasons.append(f"team has {len(errors)} error(s)")
    if status in {"fallback", "unavailable"}:
        reasons.append(f"team status is {status}")
    if not reasons:
        return None
    return {
        "path": str(path),
        "kind": "team_aggregate",
        "status": data.get("status"),
        "used_fallback_count": fallback_count,
        "errors": errors,
        "reasons": reasons,
    }


def audit_stage(run_dir: Path, stage_dir: str) -> list[dict[str, Any]]:
    root = run_dir / stage_dir
    stale = []
    for path in sorted((root / "llm").glob("*_result.json")):
        item = stale_llm_record(path, read_json_or_empty(path))
        if item:
            item["stage_dir"] = stage_dir
            stale.append(item)
    team_item = stale_team_record(root / "team" / "team_aggregate.json", read_json_or_empty(root / "team" / "team_aggregate.json"))
    if team_item:
        team_item["stage_dir"] = stage_dir
        stale.append(team_item)
    return stale


def build_audit(run_dir: Path, stage_dirs: list[str], invalidate: bool) -> dict[str, Any]:
    stale_records = []
    for stage_dir in stage_dirs:
        stale_records.extend(audit_stage(run_dir, stage_dir))
    status = "fail" if stale_records else "pass"
    return {
        "schema_version": "spatialaccagent.llm_fallback_audit.v0",
        "status": status,
        "summary": "no stale LLM fallback evidence found" if not stale_records else f"{len(stale_records)} stale fallback record(s)",
        "run_dir": str(run_dir),
        "stage_dirs": stage_dirs,
        "stale_records": stale_records,
        "invalidated": invalidate,
        "invalidation_policy": (
            "Historical fallback records are preserved on disk but must be treated as stale diagnostics, "
            "not as successful LLM planning or verification evidence."
        ),
        "next_required_action": (
            "rerun the affected stage(s) with mandatory LLM enabled and bind fresh executable_actions to SACG"
            if stale_records
            else None
        ),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit stale LLM fallback evidence in a SpatialAccAgent run.")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--stage-dir", action="append", dest="stage_dirs")
    parser.add_argument("--invalidate", action="store_true")
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    stage_dirs = args.stage_dirs or DEFAULT_STAGE_DIRS
    report = build_audit(args.run_dir.resolve(), stage_dirs, args.invalidate)
    write_json(args.out, report)
    if args.invalidate:
        write_json(args.out.parent / "llm_fallback_invalidation.json", report)
    print(report["summary"])
    return 1 if report["status"] != "pass" else 0


if __name__ == "__main__":
    raise SystemExit(main())
