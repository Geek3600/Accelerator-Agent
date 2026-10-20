#!/usr/bin/env python3
"""Collect Stage 7 QoR metrics from app-shell synthesis or implementation evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from accagent.framework.dse_ledger import (
    EXACT_TARGET_BOARD_APP_SHELL_SCOPE,
    SYNTHESIS_APP_SHELL_SCOPE,
    SYNTHESIS_KERNEL_SCOPE,
    DSE_ESTIMATED_CYCLE_MODEL,
)


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


def ensure_dse_cycle_estimate(run_dir: Path) -> Path:
    """Bind the selected DSE estimate to the kernel that was actually synthesized."""
    from accagent.framework.dse_ledger import candidate_fingerprint
    from accagent.framework.source_cycle_analysis import source_context

    context = source_context(run_dir)
    selection_path = run_dir / "parameter_binding" / "selected_architecture.json"
    binding_path = run_dir / "parameter_binding" / "parameter_binding.json"
    selection, binding = _json(selection_path), _json(binding_path)
    parameters = selection.get("parameters")
    if not parameters or parameters != binding.get("selected_architecture_parameters"):
        raise ValueError("DSE cycle estimate does not match the current parameter binding")
    if candidate_fingerprint(parameters) != selection.get("candidate_fingerprint"):
        raise ValueError("DSE cycle estimate has a stale candidate fingerprint")
    runtime = json.loads(context["sources"]["generated/chisel/runtime/runtime_config.json"])
    archived_parameters = dict(runtime.get("params", {}))
    for name, source in context["sources"].items():
        if Path(name).name == "GeneratedDesignParams.scala":
            for key, kind, value in re.findall(r'val\s+(\w+)\s*:\s*(Int|String)\s*=\s*(\d+|"[^"\n]*")', source):
                key = re.sub(r"(?<!^)(?=[A-Z])", "_", key).lower()
                archived_parameters[key] = int(value) if kind == "Int" else value.strip('"')
    if any(archived_parameters.get(key) != value for key, value in parameters.items()):
        raise ValueError("DSE parameters differ from the synthesized source archive")
    cycles = (selection.get("structural_cost_proxy") or {}).get("cycles")
    workload = context["workload"]
    if (type(cycles) not in (int, float) or not math.isfinite(cycles) or cycles <= 0
            or any(type(workload.get(key)) is not int or workload[key] <= 0
                   for key in ("processed_tokens", "model_layers"))):
        raise ValueError("DSE cycle estimate or synthesized workload is missing/invalid")
    report = {
        "status": "pass", "counter_source": "dse_structural_cycle_estimate",
        "performance_model": DSE_ESTIMATED_CYCLE_MODEL,
        "latency_cycles": math.ceil(cycles),
        "processed_tokens": workload["processed_tokens"], "model_layers": workload["model_layers"],
        "source_fingerprint": hashlib.sha256(json.dumps(context, sort_keys=True).encode()).hexdigest(),
        "synthesis_source_archive_sha256": context["synthesis_source_archive_sha256"],
        "selection_sha256": hashlib.sha256(selection_path.read_bytes()).hexdigest(),
        "binding_sha256": hashlib.sha256(binding_path.read_bytes()).hexdigest(),
        "candidate_fingerprint": selection["candidate_fingerprint"],
        "cycle_evidence": str(selection_path),
        "cycles_are_estimated": True, "rtl_cycles_measured": False,
    }
    request = _json(run_dir / "backend_board" / "optimization_request.json")
    if request.get("calibrate_timing_cycles") is True:
        from accagent.framework.source_cycle_analysis import ensure_source_cycle_analysis
        from accagent.framework.dse_timing_calibration import calibrated_cycle_terms

        analysis_path = ensure_source_cycle_analysis(run_dir)
        analysis = _json(analysis_path)
        if analysis.get("source_fingerprint") != report["source_fingerprint"]:
            raise ValueError("timing cycle calibration belongs to a different synthesized source")
        calibration = calibrated_cycle_terms(selection["structural_cost_proxy"], analysis)
        report.update({"latency_cycles": calibration["latency_cycles"], "timing_calibration": calibration})
    path = run_dir / "backend_board" / "qor" / "dse_cycle_estimate.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return path


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


def parse_timing_bottleneck(path: Path) -> dict[str, Any]:
    text = _text(path)
    match = re.search(r"Slack \((?:VIOLATED|MET)\)\s*:\s*(-?[0-9.]+)ns", text)
    if not match:
        return {}
    header = text[match.start():].split("Location", 1)[0]
    result = {"report_path": str(path.resolve()), "slack_ns": float(match.group(1)),
              "report_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "path_header": header}
    for key, pattern in {
        "source": r"Source:\s*([^\n]+)", "destination": r"Destination:\s*([^\n]+)",
        "logic_levels": r"Logic Levels:\s*(\d+)", "data_path_delay_ns": r"Data Path Delay:\s*([0-9.]+)ns",
    }.items():
        value = re.search(pattern, header)
        if value:
            result[key] = int(value.group(1)) if key == "logic_levels" else (
                float(value.group(1)) if key.endswith("_ns") else value.group(1).strip())
    return result


def parse_achieved_frequency_mhz(path: Path, override_period_ns: float | None, clock_name: str | None = None) -> float | None:
    text = _text(path)
    clocks = dict(re.findall(r"(?m)^\s*(\S+)\s+\{[^}]+\}\s+([0-9.]+)\s+[0-9.]+\s*$", text))
    if clock_name:
        table = text.split("Intra Clock Table", 1)[-1].split("Inter Clock Table", 1)[0]
        wns = re.search(rf"(?m)^\s*{re.escape(clock_name)}\s+(-?[0-9.]+)\s+", table)
        period_ns = override_period_ns or (float(clocks[clock_name]) if clock_name in clocks else None)
    else:
        if len(clocks) > 1:
            return None
        wns = re.search(r"WNS\(ns\).*?\n\s*-+.*?\n\s*(-?[0-9.]+)", text, re.S)
        period_ns = override_period_ns or (float(next(iter(clocks.values()))) if clocks else None)
    if period_ns is None or period_ns <= 0:
        return None
    if not wns:
        return None
    wns_ns = float(wns.group(1))
    critical_path_ns = period_ns - wns_ns
    return 1000.0 / critical_path_ns if critical_path_ns > 0 else None


def parse_performance_tokens_per_second(
    path: Path,
    clock_frequency_mhz: float | None,
    processed_tokens_override: int | None,
    run_dir: Path | None = None,
) -> float | None:
    report = _json(path)
    if report.get("status") != "pass":
        return None
    source = report.get("counter_source")
    # RTL/synthesizable DUT counters are retained as diagnostic evidence only;
    # throughput is intentionally based on the DSE/source-cycle model.
    if source == "synthesizable_dut_counter":
        return None
    if source == "dse_structural_cycle_estimate":
        from accagent.framework.source_cycle_analysis import source_fingerprint

        root = run_dir or path.parents[2]
        try:
            if (report.get("performance_model") != DSE_ESTIMATED_CYCLE_MODEL
                    or report.get("source_fingerprint") != source_fingerprint(root)
                    or any(report.get(f"{name}_sha256") != hashlib.sha256(
                        (root / "parameter_binding" / filename).read_bytes()).hexdigest()
                        for name, filename in [("selection", "selected_architecture.json"), ("binding", "parameter_binding.json")])):
                return None
        except (OSError, ValueError, TypeError):
            return None
        if processed_tokens_override is not None and processed_tokens_override != report.get("processed_tokens"):
            return None
        request = _json(root / "backend_board" / "optimization_request.json")
        calibration = report.get("timing_calibration")
        if request.get("calibrate_timing_cycles") is True and not calibration:
            return None
        if calibration:
            from accagent.framework.dse_timing_calibration import calibrated_cycle_terms

            try:
                analysis = calibration["source_analysis"]
                proxy = _json(root / "parameter_binding" / "selected_architecture.json")["structural_cost_proxy"]
                expected = calibrated_cycle_terms(proxy, analysis)
                if (analysis.get("source_fingerprint") != report["source_fingerprint"]
                        or analysis.get("processed_tokens") != report.get("processed_tokens")
                        or analysis.get("model_layers") != report.get("model_layers")
                        or expected != calibration
                        or expected["latency_cycles"] != report.get("latency_cycles")):
                    return None
            except (KeyError, TypeError, ValueError):
                return None
    elif source == "source_schedule_analysis":
        from accagent.framework.source_cycle_analysis import PERFORMANCE_MODEL, pipeline_cycle_total, source_fingerprint

        if report.get("performance_model") != PERFORMANCE_MODEL:
            return None
        try:
            if pipeline_cycle_total(
                report.get("pipeline_schedule"),
                report.get("processed_tokens"),
                report.get("model_layers"),
            ) != report.get("latency_cycles"):
                return None
        except (TypeError, ValueError):
            return None
        try:
            fingerprint = source_fingerprint(path.parents[2])
        except (OSError, TypeError, ValueError):
            return None
        if report.get("source_fingerprint") != fingerprint:
            return None
        if processed_tokens_override is not None and processed_tokens_override != report.get("processed_tokens"):
            return None
    elif source == "synthesizable_dut_counter":
        if run_dir is None or report.get("source_fingerprint") is None:
            return None
        from accagent.framework.source_cycle_analysis import source_fingerprint

        try:
            fingerprint = source_fingerprint(run_dir)
        except (OSError, TypeError, ValueError):
            return None
        if report.get("source_fingerprint") != fingerprint:
            return None
    else:
        return None
    cycles = report.get("latency_cycles")
    tokens = processed_tokens_override or report.get("processed_tokens")
    if type(cycles) is not int or cycles <= 0 or type(tokens) is not int or tokens <= 0:
        return None
    if clock_frequency_mhz is None or clock_frequency_mhz <= 0:
        return None
    return tokens * clock_frequency_mhz * 1_000_000.0 / cycles


def performance_report_path(run_dir: Path, override: Path | None = None) -> Path:
    if override is not None and override.name != "performance_counter_report.json":
        return override
    # Keep RTL counters available as debug evidence, but use the DSE/source
    # cycle analysis as the performance source of truth.
    return run_dir / "backend_board" / "qor" / "dse_cycle_estimate.json"


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    run_dir = args.run_dir.resolve()
    app_shell_report = getattr(args, "app_shell_report", None) or (
        run_dir / "backend_board" / "case_diagnostics" / "app_shell_runtime_vivado.json"
    )
    synthesis = _json(app_shell_report)
    app_shell_mode = synthesis.get("mode")
    synthesis_only = app_shell_mode == "synth"
    report_suffix = "synth" if synthesis_only else "impl"
    utilization = args.utilization_report or (
        run_dir / "app_shell_runtime_bitstream" / f"app_shell_{report_suffix}_utilization.rpt"
    )
    timing = args.timing_report or (
        run_dir / "app_shell_runtime_bitstream" / f"app_shell_{report_suffix}_timing.rpt"
    )
    power = args.power_report or (
        run_dir / "app_shell_runtime_bitstream" / f"app_shell_{report_suffix}_power.rpt"
    )
    performance = performance_report_path(run_dir, args.performance_report)
    clock_mhz = (
        args.clock_frequency_hz / 1_000_000.0
        if args.clock_frequency_hz
        else parse_achieved_frequency_mhz(timing, args.clock_period_ns, synthesis.get("timing_clock"))
    )
    result = {
        "measurement_scope": synthesis.get("measurement_scope") or (SYNTHESIS_APP_SHELL_SCOPE if synthesis_only else EXACT_TARGET_BOARD_APP_SHELL_SCOPE),
        "metric_quality": (
            "post_synthesis_clock_and_rtl_cycle_calculation"
            if synthesis_only
            else "post_implementation_clock_and_rtl_cycle_calculation"
        ),
        "resources": parse_resources(utilization),
        "power_w": parse_power_w(power),
        "clock_frequency_mhz": clock_mhz,
        "performance_tokens_per_second": parse_performance_tokens_per_second(
            performance,
            clock_mhz,
            args.processed_tokens,
            run_dir,
        ),
        "performance_model": _json(performance).get("performance_model") or (
            "synthesizable_dut_counter"
            if _json(performance).get("counter_source") == "synthesizable_dut_counter"
            else None
        ),
    }
    if result["measurement_scope"] == SYNTHESIS_KERNEL_SCOPE:
        result["resource_top"] = synthesis.get("synthesis_top")
        result["resource_boundary"] = "generated_top_with_external_ports_excluding_board_shell"
    bottleneck = parse_timing_bottleneck(timing)
    if bottleneck:
        result["critical_timing_path"] = bottleneck
    if _json(performance).get("counter_source") == "source_schedule_analysis":
        phase = "synthesis" if synthesis_only else "implementation"
        result["metric_quality"] = f"post_{phase}_clock_and_analytical_source_cycles"
        result["performance_estimation"] = _json(performance)
        result["performance_model"] = _json(performance).get("performance_model")
    elif _json(performance).get("counter_source") == "dse_structural_cycle_estimate":
        phase = "synthesis" if synthesis_only else "implementation"
        result["metric_quality"] = f"post_{phase}_clock_and_dse_estimated_cycles"
        result["performance_estimation"] = _json(performance)
        if _json(performance).get("timing_calibration"):
            result["metric_quality"] = f"post_{phase}_clock_and_source_calibrated_dse_cycles"
    required = ("resources", "clock_frequency_mhz", "performance_tokens_per_second") if synthesis_only else (
        "resources", "power_w", "clock_frequency_mhz", "performance_tokens_per_second"
    )
    missing = [key for key in required if result.get(key) is None]
    result.update({"status": "incomplete" if missing else "pass", "missing_metrics": missing})
    return result


def measurement_provenance(args: argparse.Namespace) -> dict[str, Any]:
    """Bind the reported QoR values to their synthesis and cycle evidence."""

    run_dir = args.run_dir.resolve()
    app_shell_report = getattr(args, "app_shell_report", None) or (
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
    performance = performance_report_path(run_dir, args.performance_report)
    mode = _json(app_shell_report).get("mode")
    if mode == "synth":
        utilization = args.utilization_report or run_dir / "app_shell_runtime_bitstream" / "app_shell_synth_utilization.rpt"
        timing = args.timing_report or run_dir / "app_shell_runtime_bitstream" / "app_shell_synth_timing.rpt"
        power = args.power_report or run_dir / "app_shell_runtime_bitstream" / "app_shell_synth_power.rpt"
        evidence = [
            app_shell_report,
            utilization,
            timing,
            power,
            performance,
            args.out or (run_dir / "backend_board" / "qor" / "qor_metrics.json"),
        ]
        scope = _json(app_shell_report).get("measurement_scope") or SYNTHESIS_APP_SHELL_SCOPE
    else:
        evidence = [app_shell_report, utilization, timing, power, performance, args.out or (run_dir / "backend_board" / "qor" / "qor_metrics.json")]
        scope = EXACT_TARGET_BOARD_APP_SHELL_SCOPE
    return {"measurement_scope": scope, "evidence_paths": [str(path.resolve()) for path in evidence]}


def preserve_best_qor(run_dir: Path) -> None:
    """Retain source-bound measurements and index the best observed results."""
    from scripts.synthesis.app_shell_runtime_vivado import preserve_successful_synthesis

    backend = run_dir / "backend_board"
    preserve_successful_synthesis(run_dir, backend / "case_diagnostics/app_shell_runtime_vivado.json")
    groups = {}
    for path in sorted((backend / "measurements").glob("*/qor_metrics.json")):
        metric = _json(path)
        runtime = _json(path.parent / "app_shell_runtime_vivado.json")
        digest = runtime.get("synthesis_source_archive_sha256")
        binding = metric.get("performance_estimation", {}).get("synthesis_source_archive_sha256")
        archive = path.parent / Path(runtime.get("closure_archive") or "missing").name
        if (metric.get("status") != "pass" or runtime.get("status") != "pass"
                or not digest or binding != digest or not archive.is_file()
                or hashlib.sha256(archive.read_bytes()).hexdigest() != digest):
            continue
        scope = metric.get("measurement_scope", "unknown")
        quality = metric.get("metric_quality", "unknown")
        key = scope + ":" + quality
        row = {"synthesis_source_archive_sha256": digest, "source_archive": str(archive),
               "qor_report": str(path), "runtime_report": str(path.parent / "app_shell_runtime_vivado.json"),
               "clock_frequency_mhz": metric.get("clock_frequency_mhz"),
               "performance_tokens_per_second": metric.get("performance_tokens_per_second"),
               "performance_estimation": metric.get("performance_estimation", {}),
               "resources": metric.get("resources", {})}
        group = groups.setdefault(key, {"measurement_scope": scope, "metric_quality": quality})
        for label, field in [("best_clock", "clock_frequency_mhz"), ("best_throughput", "performance_tokens_per_second")]:
            value = row[field]
            if isinstance(value, (int, float)) and math.isfinite(value) and value > 0:
                prior = group.get(label, {})
                if value > (prior.get(field) or 0):
                    group[label] = row
    out = backend / "best_qor.json"
    report = {"schema_version": "spatialaccagent.best_observed_qor.v1",
              "policy": "Historical observations only; source archives retained. Estimated throughput stays labeled; this index does not select or promote hardware.",
              "groups": groups}
    out.parent.mkdir(parents=True, exist_ok=True)
    temporary = out.with_suffix(".json.new")
    temporary.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(out)
    from scripts.synthesis.export_timing_history import export_timing_history

    export_timing_history(run_dir)


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
    out = args.out or args.run_dir / "backend_board" / "qor" / "qor_metrics.json"
    analysis_error = None
    try:
        run_dir = args.run_dir.resolve()
        app_shell = _json(args.app_shell_report or run_dir / "backend_board" / "case_diagnostics" / "app_shell_runtime_vivado.json")
        if app_shell.get("mode") == "synth" and app_shell.get("status") == "pass" and args.performance_report is None:
            performance = performance_report_path(run_dir)
            if parse_performance_tokens_per_second(performance, 1.0, args.processed_tokens, run_dir) is None:
                partial = {**build_report(args), **measurement_provenance(args)}
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(json.dumps(partial, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                try:
                    ensure_dse_cycle_estimate(run_dir)
                except ValueError as exc:
                    analysis_error = str(exc)
        report = {**build_report(args), **measurement_provenance(args)}
        if analysis_error:
            report["performance_estimation_error"] = analysis_error
            diagnosis = _json(run_dir / "backend_board/qor/cycle_analysis/llm/source_cycle_analysis_agent_result.json").get("output", {})
            if diagnosis.get("status") == "blocked":
                report["source_schedule_diagnosis"] = diagnosis
                from accagent.framework.dse_calibration import invalidate_noncompleting_sample

                invalidate_noncompleting_sample(run_dir, diagnosis)
            report["performance_tokens_per_second"] = None
            report["status"] = "incomplete"
            if "performance_tokens_per_second" not in report["missing_metrics"]:
                report["missing_metrics"].append("performance_tokens_per_second")
    except ValueError as exc:
        print(exc)
        return 1
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if report["status"] == "pass" and report.get("performance_estimation"):
        from accagent.framework.dse_calibration import publish_sample

        publish_sample(args.run_dir.resolve(), report)
        preserve_best_qor(args.run_dir.resolve())
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
