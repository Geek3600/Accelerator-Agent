"""Source-bound synthesis samples for the existing DSE estimation agent."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

from accagent.framework.dse_ledger import SYNTHESIS_KERNEL_SCOPE, DSE_ESTIMATED_CYCLE_MODEL, complete_metrics, utc_now
from accagent.framework.dse_estimator import cost_features
from accagent.framework.source_cycle_analysis import PERFORMANCE_MODEL, pipeline_cycle_total, source_context, source_fingerprint


SAMPLE_DIR = Path(__file__).resolve().parents[1] / "runs" / "_shared_experience" / "dse_qor_samples"


def invalidate_noncompleting_sample(run_dir: Path, diagnosis: dict[str, Any]) -> None:
    """Retain historical data, but do not train DSE on a deadlocked schedule."""
    if diagnosis.get("blocker_kind") != "noncompleting_hardware_schedule":
        return
    try:
        fingerprint = source_fingerprint(run_dir)
        path = SAMPLE_DIR / f"{fingerprint}.json"
        if path.is_file():
            sample = json.loads(path.read_text())
            sample.update(cycle_analysis_status="noncompleting_hardware_schedule", source_schedule_diagnosis=diagnosis)
            path.write_text(json.dumps(sample, indent=2, sort_keys=True) + "\n")
    except (OSError, ValueError):
        return


def publish_sample(run_dir: Path, report: dict[str, Any]) -> Path | None:
    if (
        report.get("status") != "pass"
        or report.get("measurement_scope") != SYNTHESIS_KERNEL_SCOPE
        or report.get("performance_model") not in {
            PERFORMANCE_MODEL, DSE_ESTIMATED_CYCLE_MODEL, "synthesizable_dut_counter",
        }
        or not complete_metrics(report, SYNTHESIS_KERNEL_SCOPE)
    ):
        return None
    raw_performance = report.get("performance_estimation")
    if not isinstance(raw_performance, dict):
        return None
    performance = dict(raw_performance)
    performance_model = report["performance_model"]
    cycle_evidence_kind = {
        PERFORMANCE_MODEL: "analytical_source_schedule",
        DSE_ESTIMATED_CYCLE_MODEL: "analytical_dse_proxy",
        "synthesizable_dut_counter": "rtl_counter",
    }[performance_model]
    if performance_model == "synthesizable_dut_counter":
        if (
            performance.get("counter_source") != "synthesizable_dut_counter"
            or performance.get("rtl_cycles_measured") is not True
            or performance.get("measurement_complete") is not True
            or performance.get("count_is_latency") is not True
        ):
            return None
    else:
        performance["rtl_cycles_measured"] = False
    try:
        cycles = (
            performance["latency_cycles"] if report["performance_model"] == DSE_ESTIMATED_CYCLE_MODEL
            else performance["latency_cycles"] if performance_model == "synthesizable_dut_counter"
            else pipeline_cycle_total(performance.get("pipeline_schedule"), performance["processed_tokens"], performance["model_layers"])
        )
        if cycles != performance.get("latency_cycles"):
            return None
        expected_tps = performance["processed_tokens"] * report["clock_frequency_mhz"] * 1_000_000 / cycles
        if not math.isclose(expected_tps, report["performance_tokens_per_second"], rel_tol=1e-9):
            return None
        context = source_context(run_dir)
        if any(
            context["workload"].get(key) != performance.get(key)
            for key in ("processed_tokens", "model_layers")
        ):
            return None
        fingerprint = source_fingerprint(run_dir)
        if fingerprint != performance.get("source_fingerprint"):
            return None
        archive_sha256 = context["synthesis_source_archive_sha256"]
        if performance.get("synthesis_source_archive_sha256") not in (None, archive_sha256):
            return None
        performance["synthesis_source_archive_sha256"] = archive_sha256
        runtime = json.loads(context["sources"]["generated/chisel/runtime/runtime_config.json"])
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return None
    parameters = dict(runtime.get("params", {}))
    for name, source in context["sources"].items():
        if Path(name).name != "GeneratedDesignParams.scala":
            continue
        for key, kind, value in re.findall(r'val\s+(\w+)\s*:\s*(Int|String)\s*=\s*(\d+|"[^"\n]*")', source):
            snake_key = re.sub(r"(?<!^)(?=[A-Z])", "_", key).lower()
            parameters[snake_key] = int(value) if kind == "Int" else value.strip('"')
    try:
        features = cost_features(
            parameters, context["workload"], runtime["memory_layout"]["weight_storage_terms"],
            str(parameters["model_type"]), str(runtime["board"]["fpga_part"]),
            linear_source=next((source for name, source in context["sources"].items() if name.endswith("/templates/Linear.scala")), ""),
        )
    except (KeyError, TypeError, ValueError):
        return None
    sample = {
        "schema_version": "spatialaccagent.dse_qor_sample.v1",
        "timestamp": utc_now(),
        "source_fingerprint": fingerprint,
        "synthesis_source_archive_sha256": context["synthesis_source_archive_sha256"],
        "measurement_scope": SYNTHESIS_KERNEL_SCOPE,
        "performance_model": performance_model,
        "cycle_evidence": {
            "kind": cycle_evidence_kind,
            "status": "pass",
            "is_rtl_counter_measurement": performance_model == "synthesizable_dut_counter",
        },
        "metric_quality": report.get("metric_quality"),
        "workload": context["workload"],
        "parameters": parameters,
        "cost_features": features,
        "board": runtime.get("board", {}),
        "design_parameters_source": {
            name: source for name, source in context["sources"].items()
            if Path(name).name == "GeneratedDesignParams.scala"
        },
        "resources": report["resources"],
        "clock_frequency_mhz": report["clock_frequency_mhz"],
        "performance_tokens_per_second": expected_tps,
        "performance_estimation": performance,
        "evidence_paths": report.get("evidence_paths", []),
    }
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    path = SAMPLE_DIR / f"{fingerprint}.json"
    temporary = path.with_suffix(".pending")
    temporary.write_text(json.dumps(sample, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)
    return path


def load_samples() -> list[dict[str, Any]]:
    samples = []
    for path in sorted(SAMPLE_DIR.glob("*.json")):
        try:
            sample = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if (
            isinstance(sample, dict)
            and sample.get("schema_version") == "spatialaccagent.dse_qor_sample.v1"
            and sample.get("performance_model") in {
                PERFORMANCE_MODEL, DSE_ESTIMATED_CYCLE_MODEL, "synthesizable_dut_counter",
            }
            and sample.get("source_fingerprint") == path.stem
            and sample.get("measurement_scope") == SYNTHESIS_KERNEL_SCOPE
            and sample.get("cycle_analysis_status") != "noncompleting_hardware_schedule"
            and isinstance(sample.get("cost_features"), dict)
            and complete_metrics(sample, SYNTHESIS_KERNEL_SCOPE)
        ):
            samples.append(sample)
    return samples
