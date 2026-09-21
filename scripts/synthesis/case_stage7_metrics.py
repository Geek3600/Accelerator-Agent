#!/usr/bin/env python3
"""Collect the four public Stage 7 QoR metrics from exact app-shell evidence."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


EXACT_TARGET_BOARD_APP_SHELL_SCOPE = "exact_target_board_app_shell"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _integer(text: str) -> int:
    return int(text.strip().replace(",", ""))


def parse_resources(path: Path) -> dict[str, int] | None:
    header: list[str] = []
    row: list[str] = []
    for line in _text(path).splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if "Instance" in cells and "Total LUTs" in cells:
            header = cells
        elif header and cells and cells[0] and set(cells[0]) != {"-"}:
            row = cells
            break
    if not header or len(header) != len(row):
        return None
    values = dict(zip(header, row))
    try:
        return {
            "lut": _integer(values["Total LUTs"]),
            "ff": _integer(values["FFs"]),
            "bram36": _integer(values["RAMB36"]),
            "bram18": _integer(values["RAMB18"]),
            "uram": _integer(values["URAM"]),
            "dsp": _integer(values["DSP Blocks"]),
        }
    except (KeyError, ValueError):
        return None


def parse_power_w(path: Path) -> float | None:
    match = re.search(r"\|\s*Total On-Chip Power \(W\)\s*\|\s*([0-9.]+)", _text(path), re.I)
    return float(match.group(1)) if match else None


def parse_achieved_frequency_mhz(path: Path, override_period_ns: float | None) -> float | None:
    text = _text(path)
    wns = re.search(r"WNS\(ns\).*?\n\s*-+.*?\n\s*(-?[0-9.]+)", text, re.S)
    clock = re.search(r"\n[^\s]+\s+\{[^}]+\}\s+([0-9.]+)\s+([0-9.]+)\s*\n", text)
    period_ns = override_period_ns or (float(clock.group(1)) if clock else None)
    if period_ns is None or period_ns <= 0:
        return None
    wns_ns = float(wns.group(1)) if wns else 0.0
    critical_path_ns = period_ns - wns_ns
    return 1000.0 / critical_path_ns if critical_path_ns > 0 else None


def parse_performance_tokens_per_second(
    path: Path,
    clock_frequency_mhz: float | None,
    processed_tokens_override: int | None,
) -> float | None:
    report = _json(path)
    if report.get("status") != "pass" or report.get("counter_source") != "synthesizable_dut_counter":
        return None
    cycles = report.get("latency_cycles")
    tokens = processed_tokens_override or report.get("processed_tokens")
    if not isinstance(cycles, int) or cycles <= 0 or not isinstance(tokens, int) or tokens <= 0:
        return None
    if clock_frequency_mhz is None or clock_frequency_mhz <= 0:
        return None
    return tokens * clock_frequency_mhz * 1_000_000.0 / cycles


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    run_dir = args.run_dir.resolve()
    utilization = args.utilization_report or (
        run_dir / "app_shell_runtime_bitstream" / "app_shell_impl_utilization.rpt"
    )
    timing = args.timing_report or (
        run_dir / "app_shell_runtime_bitstream" / "app_shell_impl_timing.rpt"
    )
    power = args.power_report or (
        run_dir / "app_shell_runtime_bitstream" / "app_shell_impl_power.rpt"
    )
    performance = args.performance_report or (
        run_dir / "verification" / "board_simulation" / "reports" / "performance_counter_report.json"
    )
    clock_mhz = (
        args.clock_frequency_hz / 1_000_000.0
        if args.clock_frequency_hz
        else parse_achieved_frequency_mhz(timing, args.clock_period_ns)
    )
    result = {
        "resources": parse_resources(utilization),
        "power_w": parse_power_w(power),
        "clock_frequency_mhz": clock_mhz,
        "performance_tokens_per_second": parse_performance_tokens_per_second(
            performance,
            clock_mhz,
            args.processed_tokens,
        ),
    }
    if any(value is None for value in result.values()):
        missing = [key for key, value in result.items() if value is None]
        raise ValueError(f"missing required QoR metric(s): {', '.join(missing)}")
    return result


def measurement_provenance(args: argparse.Namespace) -> dict[str, Any]:
    """Bind the four public QoR values to one exact app-shell evidence set."""

    run_dir = args.run_dir.resolve()
    app_shell_report = args.app_shell_report or (
        run_dir / "backend_board" / "case_diagnostics" / "app_shell_runtime_vivado.json"
    )
    utilization = args.utilization_report or (
        run_dir / "app_shell_runtime_bitstream" / "app_shell_impl_utilization.rpt"
    )
    timing = args.timing_report or (
        run_dir / "app_shell_runtime_bitstream" / "app_shell_impl_timing.rpt"
    )
    power = args.power_report or (
        run_dir / "app_shell_runtime_bitstream" / "app_shell_impl_power.rpt"
    )
    performance = args.performance_report or (
        run_dir / "verification" / "board_simulation" / "reports" / "performance_counter_report.json"
    )
    return {
        "measurement_scope": EXACT_TARGET_BOARD_APP_SHELL_SCOPE,
        "evidence_paths": [
            str(path.resolve())
            for path in [app_shell_report, utilization, timing, power, performance, args.out or (run_dir / "backend_board" / "qor" / "qor_metrics.json")]
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--utilization-report", type=Path)
    parser.add_argument("--timing-report", type=Path)
    parser.add_argument("--power-report", type=Path)
    parser.add_argument("--performance-report", type=Path)
    parser.add_argument("--app-shell-report", type=Path)
    parser.add_argument("--clock-frequency-hz", type=float)
    parser.add_argument("--clock-period-ns", type=float)
    parser.add_argument("--processed-tokens", type=int)
    args = parser.parse_args(argv)
    try:
        report = {**build_report(args), **measurement_provenance(args)}
    except ValueError as exc:
        print(exc)
        return 1
    out = args.out or args.run_dir / "backend_board" / "qor" / "qor_metrics.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
