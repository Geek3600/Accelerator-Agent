"""Reconcile optimized source schedules with the DSE DDR overlap model."""

from __future__ import annotations

import math
import json
import shutil
import tarfile
from pathlib import Path
from typing import Any

from accagent.framework.source_cycle_analysis import pipeline_cycle_total


def calibrated_cycle_terms(proxy: dict[str, Any], analysis: dict[str, Any]) -> dict[str, Any]:
    """Replace the compute term, retaining initial refill and exposed prefetch."""
    layers = analysis["model_layers"]
    compute_total = pipeline_cycle_total(
        analysis["pipeline_schedule"], analysis["processed_tokens"], layers,
    )
    if analysis.get("latency_cycles") != compute_total:
        raise ValueError("source schedule and analyzed compute cycles disagree")
    values = [proxy.get(key) for key in (
        "initial_refill_cycles", "cache_refill_service_cycles_per_layer", "compute_cycles_per_layer",
    )]
    if any(type(value) not in (int, float) or not math.isfinite(value) or value < 0 for value in values):
        raise ValueError("DSE calibration requires finite refill and compute terms")
    initial, refill, old_compute = values
    compute = compute_total // layers
    exposed = max(0, math.ceil(refill) - compute)
    total = math.ceil(initial) + compute_total + (layers - 1) * exposed
    return {
        "method": "source_schedule_compute_with_dse_ddr_overlap_v1",
        "original_dse_cycles": math.ceil(proxy["cycles"]),
        "original_compute_cycles_per_layer": old_compute,
        "compute_cycles_per_layer": compute,
        "initial_refill_cycles": math.ceil(initial),
        "cache_refill_service_cycles_per_layer": math.ceil(refill),
        "overlapped_refill_stall_cycles_per_layer": exposed,
        "latency_cycles": total,
        "source_analysis": analysis,
        "limitations": [
            "Source-derived analytical schedule, not RTL simulation or board measurement.",
            "DDR service retains the DSE estimate; external stalls and board-shell overhead are unmeasured.",
        ],
    }


def snapshot_best_measurement(run_dir: Path, destination: Path) -> Path:
    """Analyze a saved source/report pair without touching an in-flight build."""
    groups = json.loads((run_dir / "backend_board/best_qor.json").read_text())["groups"]
    observations = [group["best_clock"] for group in groups.values() if "best_clock" in group]
    best = max(observations, key=lambda item: item["clock_frequency_mhz"])
    measured = Path(best["qor_report"]).parent
    destination.mkdir(parents=True, exist_ok=True)
    for name in ("selected_architecture.json", "parameter_binding.json"):
        target = destination / "parameter_binding" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(run_dir / "parameter_binding" / name, target)
    runtime = json.loads(Path(best["runtime_report"]).read_text())
    archive = Path(best["source_archive"])
    runtime["closure_archive"] = str(archive.resolve())
    with tarfile.open(archive, "r:gz") as bundle:
        source = bundle.extractfile("analysis_context/runtime/runtime_config.json")
        if source is None:
            raise ValueError("measurement archive has no runtime configuration")
        target = destination / "generated/chisel/runtime/runtime_config.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read())
    target = destination / "backend_board/case_diagnostics/app_shell_runtime_vivado.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(runtime, indent=2) + "\n")
    reports = destination / "app_shell_runtime_bitstream"
    reports.mkdir(parents=True, exist_ok=True)
    for name in ("app_shell_synth_timing.rpt", "app_shell_synth_utilization.rpt"):
        shutil.copy2(measured / name, reports / name)
    request = destination / "backend_board/optimization_request.json"
    request.write_text(json.dumps({"calibrate_timing_cycles": True}) + "\n")
    return destination


def compiled_source_context(run_dir: Path) -> dict[str, Any]:
    """Current compile-verified sources for cycle analysis before synthesis."""
    import hashlib
    from accagent.framework.source_cycle_analysis import source_context
    from accagent.framework.stage_repair_execute import stage2_compile_only_authority

    if stage2_compile_only_authority(run_dir).get("status") != "ready":
        raise ValueError("current source VCS compilation must pass before schedule analysis")
    reference = snapshot_best_measurement(run_dir, run_dir / "backend_board/qor/cycle_reference")
    context = source_context(reference)
    root = run_dir / "generated/chisel"
    files = [*sorted((root / "src/main/scala").rglob("*.scala")),
             *sorted((root / "vivado").rglob("*.sv")), root / "runtime/runtime_config.json",
             root / "scripts/gen_xilinx_fp_ips_23.tcl", root / "simulation/fpga_ip_modules.txt"]
    sources = {str(path.relative_to(run_dir)): path.read_text(errors="replace")
               for path in files if path.is_file()}
    old_runtime = json.loads(context["sources"]["generated/chisel/runtime/runtime_config.json"])
    runtime = json.loads(sources["generated/chisel/runtime/runtime_config.json"])
    if (runtime.get("params") != old_runtime.get("params")
            or runtime.get("memory_layout") != old_runtime.get("memory_layout")):
        raise ValueError("existing-design cycle analysis requires unchanged workload and architecture parameters")
    context.update(sources=sources, synthesis_source_archive_sha256=None,
                   compiled_source_snapshot_sha256=hashlib.sha256(
                       json.dumps(sources, sort_keys=True).encode()).hexdigest(),
                   compile_evidence={"status": "ready", "validation_policy": "vcs_compile_only"})
    return context


if __name__ == "__main__":
    import argparse
    from scripts.synthesis.case_stage7_metrics import main

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--snapshot-dir", type=Path, required=True)
    args = parser.parse_args()
    snapshot = snapshot_best_measurement(args.run_dir.resolve(), args.snapshot_dir.resolve())
    raise SystemExit(main(["--run-dir", str(snapshot)]))
