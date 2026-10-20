#!/usr/bin/env python3
"""Export every retained synthesis attempt, including timing regressions."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path

if str(Path(__file__).resolve().parents[2]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def _read(path: Path) -> dict:
    try:
        value = json.loads(path.read_text())
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def export_timing_history(run_dir: Path) -> Path:
    from scripts.synthesis.case_stage7_metrics import (
        parse_achieved_frequency_mhz, parse_timing_bottleneck,
    )

    backend = run_dir / "backend_board"
    repairs = []
    for path in (backend / "timing_optimization").glob("**/application.json"):
        patch = _read(path.with_name("agent_patch_application.json"))
        files = patch.get("files", [])
        if patch.get("status") == "pass" and files:
            repairs.append((path, _read(path), files))
    rows = []
    for folder in (backend / "measurements").glob("*"):
        report = folder / "app_shell_runtime_vivado.json"
        runtime = _read(report)
        digest = runtime.get("synthesis_source_archive_sha256")
        archive = folder / Path(runtime.get("closure_archive") or "missing").name
        if runtime.get("status") != "pass" or not digest:
            continue
        archive_present = archive.is_file()
        if archive_present and hashlib.sha256(archive.read_bytes()).hexdigest() != digest:
            continue
        metric = _read(folder / "qor_metrics.json")
        estimate = metric.get("performance_estimation", {})
        bound = estimate.get("synthesis_source_archive_sha256") == digest
        timing = folder / "app_shell_synth_timing.rpt"
        frequency = metric.get("clock_frequency_mhz") if bound else None
        if not frequency:
            frequency = parse_achieved_frequency_mhz(
                timing, runtime.get("clock_period_ns"), runtime.get("timing_clock"))
        if not isinstance(frequency, (int, float)) or not math.isfinite(frequency) or frequency <= 0:
            continue
        recorded_at = report.stat().st_mtime
        timing_date = None
        if timing.is_file():
            match = re.search(r"(?m)^\| Date\s*:\s*(.+)$", timing.read_text(errors="replace"))
            if match:
                try:
                    timing_date = datetime.strptime(match.group(1).strip(), "%a %b %d %H:%M:%S %Y").isoformat()
                except ValueError:
                    pass
        matched = []
        candidates = [(p, app, files) for p, app, files in repairs
                      if p.stat().st_mtime <= recorded_at]
        if candidates and archive_present:
            try:
                with tarfile.open(archive, "r:gz") as bundle:
                    source_hashes = {}
                    for member in bundle.getmembers():
                        if member.isfile() and member.name.endswith(".scala"):
                            source = bundle.extractfile(member)
                            source_hashes[member.name] = hashlib.sha256(source.read()).hexdigest()
                for path, app, files in candidates:
                    if all(source_hashes.get("analysis_context/" + str(item.get("path", "")).split(
                            "/generated/chisel/", 1)[-1]) == item.get("after_sha256") for item in files):
                        matched.append((path, app))
            except (OSError, tarfile.TarError):
                pass
        # A cumulative design can still contain several older repairs.
        matched.sort(key=lambda item: item[0].stat().st_mtime)
        path, app = matched[-1] if matched else (None, {})
        bottleneck = metric.get("critical_timing_path") if bound else None
        bottleneck = bottleneck or parse_timing_bottleneck(timing)
        usable_throughput = bound and metric.get("status") == "pass"
        rows.append({
            "recorded_at_utc": datetime.fromtimestamp(recorded_at, timezone.utc).isoformat(),
            "synthesis_report_time": timing_date,
            "timestamp_basis": "Vivado report Date (server local time, timezone unspecified)" if timing_date else "retained_synthesis_report_file_mtime",
            "source_sha256": digest,
            "evidence_status": "source_archive_verified" if archive_present else "reports_only_source_archive_missing",
            "clock_frequency_mhz": frequency,
            "measurement_scope": runtime.get("measurement_scope"),
            "metric_quality": metric.get("metric_quality") if bound else "clock_only",
            "estimated_tokens_per_second": metric.get("performance_tokens_per_second") if usable_throughput else None,
            "estimated_cycles": estimate.get("latency_cycles") if usable_throughput else None,
            "resources": metric.get("resources", {}) if bound else {},
            "critical_path_source": bottleneck.get("source"),
            "critical_path_destination": bottleneck.get("destination"),
            "agent_repair_summary": app.get("implementation_summary"),
            "agent_repair_report": str(path) if path else None,
            "source_archive": str(archive) if archive_present else None,
            "runtime_report": str(report),
            "timing_report": str(timing),
            "utilization_report": str(folder / "app_shell_synth_utilization.rpt"),
        })
    rows.sort(key=lambda row: (row["synthesis_report_time"] or row["recorded_at_utc"], row["source_sha256"]))
    best = 0.0
    for index, row in enumerate(rows, 1):
        row["measurement_index"] = index
        row["new_best_clock"] = row["clock_frequency_mhz"] > best
        best = max(best, row["clock_frequency_mhz"])
        row["best_clock_so_far_mhz"] = best
    out = backend / "timing_history"
    out.mkdir(parents=True, exist_ok=True)
    policy = (
        "All retained synthesis reports, including regressions. Missing historical source archives "
        "are explicitly labeled reports_only_source_archive_missing, never reconstructed from a newer design. Measurement index is "
        "not an LLM iteration count. OOC Fmax is not post-route or board frequency. Historical "
        "throughput estimates may use different cycle models; compare metric_quality before use. "
        "Repair summaries are matched to archive source hashes, not inferred from temporal proximity."
    )
    artifacts = {"history.json": json.dumps({"policy": policy, "measurements": rows}, indent=2) + "\n"}
    stream = io.StringIO()
    fields = list(rows[0]) if rows else ["measurement_index", "clock_frequency_mhz"]
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    for row in rows:
        writer.writerow({**row, "resources": json.dumps(row["resources"], sort_keys=True)})
    artifacts["history.csv"] = stream.getvalue()
    milestones = [row for row in rows if row["new_best_clock"]]
    lines = ["# Retained timing optimization history", "", policy, "",
             "| Measurement | Fmax MHz | Source |", "|---:|---:|---|"]
    lines.extend(f"| {r['measurement_index']} | {r['clock_frequency_mhz']:.6f} | {r['source_sha256']} |"
                 for r in milestones)
    artifacts["README.md"] = "\n".join(lines) + "\n"
    for name, content in artifacts.items():
        target = out / name
        temporary = target.with_suffix(target.suffix + ".new")
        temporary.write_text(content)
        temporary.replace(target)
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    print(export_timing_history(args.run_dir.resolve()))
