#!/usr/bin/env python3
"""Check Vivado backend artifacts for a case run."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


INT_RE = re.compile(r":\s*([0-9]+)\s*:")
WNS_RE = re.compile(r"\bWNS\(ns\).*?\n[-\s|A-Za-z().]*\n\s*(-?[0-9]+(?:\.[0-9]+)?)", re.S)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def check(name: str, passed: bool, summary: str, **extra: Any) -> dict[str, Any]:
    return {"name": name, "status": "pass" if passed else "fail", "summary": summary, **extra}


def file_check(path: Path, label: str) -> tuple[bool, dict[str, Any]]:
    exists = path.exists()
    size = path.stat().st_size if exists else 0
    return exists and size > 0, check(label, exists and size > 0, f"path={path} size={size}", path=str(path), size_bytes=size)


def route_status_ok(text: str) -> tuple[bool, str]:
    if not text:
        return False, "route status report is empty"
    errors = re.search(r"# of nets with routing errors\.+\s*:\s*([0-9]+)", text)
    routable = re.search(r"# of routable nets\.+\s*:\s*([0-9]+)", text)
    fully = re.search(r"# of fully routed nets\.+\s*:\s*([0-9]+)", text)
    values = {
        "routing_errors": int(errors.group(1)) if errors else -1,
        "routable": int(routable.group(1)) if routable else -1,
        "fully_routed": int(fully.group(1)) if fully else -1,
    }
    ok = values["routing_errors"] == 0 and values["routable"] >= 0 and values["fully_routed"] == values["routable"]
    return ok, ", ".join(f"{key}={value}" for key, value in values.items())


def timing_ok(text: str) -> tuple[bool, str]:
    if not text:
        return False, "timing report is empty"
    if "Timing constraints are not met" in text or "Slack (VIOLATED)" in text:
        setup = re.search(r"Setup\s*:\s*([0-9]+)\s+Failing Endpoints,\s+Worst Slack\s+(-?[0-9.]+)ns,\s+Total Violation\s+(-?[0-9.]+)ns", text)
        if setup:
            return False, f"setup_failing_endpoints={setup.group(1)} wns={setup.group(2)}ns tns={setup.group(3)}ns"
        return False, "timing constraints are not met"
    if "Timing constraints are met" in text:
        return True, "timing constraints are met"
    return True, "no violated timing marker found"


def drc_ok(text: str) -> tuple[bool, str]:
    if not text:
        return False, "DRC report is empty"
    if re.search(r"\bERROR\b|Critical Warning", text, re.I):
        return False, "DRC report contains error or critical warning marker"
    return True, "no DRC error or critical warning marker found"


def build_report(run_dir: Path, mode: str) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    blockers: list[str] = []
    closure_blockers: list[str] = []
    out_dir = run_dir / "app_shell_runtime_bitstream"
    if mode == "synth":
        required_files = [
            (run_dir / "backend_board" / "case_diagnostics" / "app_shell_runtime_vivado.json", "app_shell_synthesis_report"),
            (out_dir / "app_shell_runtime_inspection.txt", "app_shell_inspection"),
        ]
        for path, label in required_files:
            ok, item = file_check(path, label)
            checks.append(item)
            if not ok:
                blockers.append(f"missing or empty {label}: {path}")
        return {
            "schema_version": "spatialaccagent.case_vivado_report_check.v0",
            "mode": mode,
            "run_dir": str(run_dir),
            "status": "pass" if not blockers else "fail",
            "checks": checks,
            "blockers": blockers,
            "summary": "Vivado synthesis artifacts are present" if not blockers else f"{len(blockers)} blocker(s)",
        }

    required_files = [
        (out_dir / "app_shell.bit", "bitstream"),
        (out_dir / "app_shell_routed.dcp", "routed_checkpoint"),
        (out_dir / "app_shell_impl_timing.rpt", "implementation_timing_report"),
        (out_dir / "app_shell_impl_utilization.rpt", "implementation_utilization_report"),
        (out_dir / "app_shell_impl_power.rpt", "implementation_power_report"),
        (out_dir / "app_shell_route_status.rpt", "route_status_report"),
        (out_dir / "app_shell_drc.rpt", "drc_report"),
    ]
    for path, label in required_files:
        ok, item = file_check(path, label)
        checks.append(item)
        if not ok:
            blockers.append(f"missing or empty {label}: {path}")

    route_text = read_text(out_dir / "app_shell_route_status.rpt")
    ok, summary = route_status_ok(route_text)
    checks.append(check("route_fully_routed", ok, summary))
    if not ok:
        blockers.append(f"route status is not clean: {summary}")

    timing_text = read_text(out_dir / "app_shell_impl_timing.rpt")
    ok, summary = timing_ok(timing_text)
    checks.append(check("implementation_timing_met", ok, summary))
    if not ok:
        closure_blockers.append(f"implementation timing is not met: {summary}")

    drc_text = read_text(out_dir / "app_shell_drc.rpt")
    ok, summary = drc_ok(drc_text)
    checks.append(check("drc_no_error_or_critical_warning", ok, summary))
    if not ok:
        closure_blockers.append(f"DRC is not clean: {summary}")

    return {
        "schema_version": "spatialaccagent.case_vivado_report_check.v0",
        "mode": mode,
        "run_dir": str(run_dir),
        "status": "pass" if not blockers else "fail",
        "closure_status": "pass" if not closure_blockers else "needs_optimization",
        "checks": checks,
        "blockers": blockers,
        "closure_blockers": closure_blockers,
        "summary": (
            "Vivado implementation characterization completed"
            if not blockers
            else f"{len(blockers)} implementation artifact blocker(s)"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check Vivado case artifacts and reports.")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--mode", choices=["synth", "bitstream"], required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    out = args.out or args.run_dir / "backend_board" / "case_diagnostics" / f"vivado_{args.mode}_report_check.json"
    report = build_report(args.run_dir.resolve(), args.mode)
    write_json(out, report)
    if report["status"] != "pass":
        print(report["summary"], file=sys.stderr)
        return 1
    print(report["summary"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
