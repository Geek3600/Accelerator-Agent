#!/usr/bin/env python3
"""Check case-level deadlock and AXI/DDR evidence from real tool logs."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


FIELD_RE = re.compile(r"(?P<key>[A-Za-z_][A-Za-z0-9_]*)=(?P<value>[^ \n]+)")
PASS_RE = re.compile(r"PASS real functional ddr path (?P<fields>.*)")
FATAL_RE = re.compile(r"\b(?:NO_PROGRESS|TIMEOUT)\b|\b\w*_tb\s+FAIL\b")


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


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def resolve_path(run_dir: Path, value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    repo_path = Path.cwd() / path
    if repo_path.exists():
        return repo_path
    return run_dir / path


def parse_value(raw: str) -> Any:
    try:
        return int(raw, 0)
    except ValueError:
        return raw


def parse_fields(text: str) -> dict[str, Any]:
    return {match.group("key"): parse_value(match.group("value")) for match in FIELD_RE.finditer(text)}


def nested_int(data: dict[str, Any], path: list[str], default: int = 0) -> int:
    item: Any = data
    for key in path:
        if not isinstance(item, dict):
            return default
        item = item.get(key)
    return item if isinstance(item, int) else default


def check_item(name: str, passed: bool, summary: str, **extra: Any) -> dict[str, Any]:
    return {"name": name, "status": "pass" if passed else "fail", "summary": summary, **extra}


def load_vcs_result(run_dir: Path, override: str | None) -> tuple[Path, dict[str, Any]]:
    path = resolve_path(run_dir, override) if override else run_dir / "verification" / "real_tools" / "case_vcs_functional_sim.json"
    if path is None or not path.exists():
        raise FileNotFoundError(f"VCS functional result missing: {path}")
    return path, read_json(path)


def load_diagnosis(run_dir: Path, override: str | None) -> tuple[Path, dict[str, Any]]:
    candidates = []
    if override:
        resolved = resolve_path(run_dir, override)
        if resolved:
            candidates.append(resolved)
    candidates.extend(
        [
            run_dir / "verification" / "case_diagnostics" / "vcs_functional_diagnosis.json",
            run_dir / "verification" / "qwen_vcs" / "qwen_vcs_functional_diagnosis.json",
        ]
    )
    for path in candidates:
        if path.exists():
            return path, read_json(path)
    raise FileNotFoundError(f"VCS diagnosis missing; checked {[str(path) for path in candidates]}")


def expected_vector_beats(runtime: dict[str, Any], memory_layout: dict[str, Any]) -> int:
    params = runtime.get("params", {}) if isinstance(runtime.get("params"), dict) else {}
    tensor = memory_layout.get("tensor_shape", {}) if isinstance(memory_layout.get("tensor_shape"), dict) else {}
    seq_len = int(params.get("max_seq_len") or tensor.get("seq_len") or 0)
    hidden = int(params.get("hidden_size") or tensor.get("hidden_size") or 0)
    lanes = int(params.get("lanes") or 0)
    if seq_len <= 0 or hidden <= 0 or lanes <= 0:
        return 0
    return seq_len * ((hidden + lanes - 1) // lanes)


def memory_alignment_check(memory_layout: dict[str, Any]) -> tuple[bool, list[str]]:
    blockers: list[str] = []
    alignment = int(memory_layout.get("alignment_bytes") or 0)
    regions = memory_layout.get("regions") if isinstance(memory_layout.get("regions"), list) else []
    if alignment <= 0:
        blockers.append("alignment_bytes is missing or non-positive")
    if not regions:
        blockers.append("regions are missing")
    roles = {str(region.get("role")) for region in regions if isinstance(region, dict)}
    for role in ["activation_input", "activation_output", "weight_buffer", "runtime_status"]:
        if role not in roles:
            blockers.append(f"required memory role missing: {role}")
    for region in regions:
        if not isinstance(region, dict):
            blockers.append("malformed memory region entry")
            continue
        base = int(region.get("base_addr") or 0)
        size = int(region.get("size_bytes") or 0)
        if alignment > 0 and (base % alignment or size % alignment):
            blockers.append(f"region is not aligned: {region.get('name')}")
        if size <= 0:
            blockers.append(f"region has non-positive size: {region.get('name')}")
    if regions:
        last = max(int(region.get("base_addr") or 0) + int(region.get("size_bytes") or 0) for region in regions if isinstance(region, dict))
        total = int(memory_layout.get("total_bytes") or 0)
        if total < last:
            blockers.append("total_bytes is smaller than the last region end")
    return not blockers, blockers


def token_check(label: str, text: str, required_tokens: list[str]) -> tuple[bool, list[str]]:
    missing = [token for token in required_tokens if token not in text]
    return not missing, [f"{label} missing token {token}" for token in missing]


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    run_dir = args.run_dir.resolve()
    checks: list[dict[str, Any]] = []
    blockers: list[str] = []

    vcs_path, vcs = load_vcs_result(run_dir, args.vcs_result)
    vcs_pass = vcs.get("status") == "pass" and vcs.get("returncode") == 0
    checks.append(check_item("vcs_functional_result_pass", vcs_pass, f"status={vcs.get('status')} returncode={vcs.get('returncode')}", path=str(vcs_path)))
    if not vcs_pass:
        blockers.append("case_vcs_functional_sim did not pass")

    tool_text = "\n".join(str(vcs.get(name) or "") for name in ["stdout_tail", "stderr_tail", "summary"])
    fatal_match = FATAL_RE.search(tool_text)
    checks.append(check_item("no_deadlock_or_timeout_marker", fatal_match is None, "no NO_PROGRESS/TIMEOUT/FAIL fatal marker in VCS evidence"))
    if fatal_match:
        blockers.append(f"VCS evidence contains fatal marker: {fatal_match.group(0)}")

    pass_fields = {}
    for match in PASS_RE.finditer(tool_text):
        pass_fields = parse_fields(match.group("fields"))
    checks.append(check_item("real_ddr_pass_line_present", bool(pass_fields), "PASS real functional ddr path line parsed", pass_fields=pass_fields))
    if not pass_fields:
        blockers.append("real DDR functional pass line is missing")

    diagnosis_path, diagnosis = load_diagnosis(run_dir, args.diagnosis)
    diagnosis_pass = diagnosis.get("status") == "pass" and diagnosis.get("sim_pass") is True and diagnosis.get("root_cause_class") in {None, "none"}
    checks.append(
        check_item(
            "diagnosis_pass_no_root_cause",
            diagnosis_pass,
            f"status={diagnosis.get('status')} sim_pass={diagnosis.get('sim_pass')} root={diagnosis.get('root_cause_class')}",
            path=str(diagnosis_path),
        )
    )
    if not diagnosis_pass:
        blockers.append("VCS diagnosis is not a clean functional pass")

    observed = diagnosis.get("observed", {}) if isinstance(diagnosis.get("observed"), dict) else {}
    observed_pass_fields = observed.get("pass_fields", {}) if isinstance(observed.get("pass_fields"), dict) else {}
    merged_pass_fields = {**observed_pass_fields, **pass_fields}
    input_beats = int(merged_pass_fields.get("input_beats") or observed.get("input_read_beats") or 0)
    weight_beats = int(merged_pass_fields.get("weight_beats") or observed.get("weight_read_beats") or 0)
    out_valid = int(merged_pass_fields.get("out_valid") or observed.get("output_valid_beats") or 0)
    out_write = int(merged_pass_fields.get("out_write") or observed.get("output_write_beats") or 0)
    data_counters_pass = input_beats > 0 and weight_beats > 0 and out_valid > 0 and out_write > 0
    checks.append(
        check_item(
            "real_ddr_counters_positive",
            data_counters_pass,
            f"input={input_beats} weight={weight_beats} out_valid={out_valid} out_write={out_write}",
            input_beats=input_beats,
            weight_beats=weight_beats,
            out_valid=out_valid,
            out_write=out_write,
        )
    )
    if not data_counters_pass:
        blockers.append("real DDR input/weight/output counters are not all positive")
    if out_write > out_valid:
        blockers.append("output write beats exceed output valid beats")
        checks.append(check_item("output_write_within_valid", False, f"out_write={out_write} out_valid={out_valid}"))
    else:
        checks.append(check_item("output_write_within_valid", True, f"out_write={out_write} out_valid={out_valid}"))

    runtime_path = resolve_path(run_dir, args.runtime_config) or run_dir / "generated" / "chisel" / "runtime" / "runtime_config.json"
    memory_path = resolve_path(run_dir, args.memory_layout) or run_dir / "generated" / "chisel" / "memory" / "memory_layout.json"
    runtime = read_json(runtime_path)
    memory_layout = read_json(memory_path)
    required_criteria = set(runtime.get("pass_criteria", {}).get("required", [])) if isinstance(runtime.get("pass_criteria"), dict) else set()
    criteria_missing = sorted({"no_deadlock", "done_asserted", "valid_output_bytes"} - required_criteria)
    checks.append(check_item("runtime_pass_criteria_declared", not criteria_missing, "runtime pass criteria include deadlock/done/output", missing=criteria_missing, path=str(runtime_path)))
    blockers.extend(f"runtime pass criterion missing: {item}" for item in criteria_missing)

    expected_beats = expected_vector_beats(runtime, memory_layout)
    if expected_beats:
        scaled_output_pass = out_write >= expected_beats and out_valid >= expected_beats
        checks.append(check_item("output_scale_matches_runtime_shape", scaled_output_pass, f"expected_beats={expected_beats} out_valid={out_valid} out_write={out_write}"))
        if not scaled_output_pass:
            blockers.append(f"output beats are smaller than runtime shape expectation: expected {expected_beats}")
    else:
        checks.append(check_item("output_scale_matches_runtime_shape", True, "runtime shape unavailable; positive output counters checked"))

    aligned, alignment_blockers = memory_alignment_check(memory_layout)
    checks.append(check_item("memory_layout_aligned_static_regions", aligned, "memory layout regions are aligned and contain required roles", blockers=alignment_blockers, path=str(memory_path)))
    blockers.extend(alignment_blockers)

    last_progress = observed.get("last_progress", {}) if isinstance(observed.get("last_progress"), dict) else {}
    pipeline_keys = ["pipe_l0_out_beats", "pipe_l1_out_beats", "pipe_last_out_beats", "pipe_probe_a_beats", "pipe_probe_b_beats", "pipe_probe_c_beats"]
    present_pipeline = {key: last_progress.get(key) for key in pipeline_keys if isinstance(last_progress.get(key), int)}
    if present_pipeline:
        internal_progress_pass = all(int(value) > 0 for value in present_pipeline.values())
        checks.append(check_item("internal_pipeline_progress_counters", internal_progress_pass, "internal pipeline counters are present and positive", counters=present_pipeline))
        if not internal_progress_pass:
            blockers.append("one or more internal pipeline progress counters are zero")
    else:
        checks.append(check_item("internal_pipeline_progress_counters", True, "no adapter-specific internal pipeline counters were present; DDR pass counters remain authoritative"))

    rtl_paths = [path for value in args.rtl_wrapper for path in [resolve_path(run_dir, value)] if path]
    tb_paths = [path for value in args.testbench for path in [resolve_path(run_dir, value)] if path]
    rtl_text = "\n".join(read_text(path) for path in rtl_paths)
    tb_text = "\n".join(read_text(path) for path in tb_paths)
    missing_files = [str(path) for path in [*rtl_paths, *tb_paths] if not path.exists()]
    checks.append(check_item("rtl_tb_files_present", not missing_files, "RTL wrapper and testbench files are present", missing=missing_files))
    blockers.extend(f"required RTL/TB file missing: {path}" for path in missing_files)

    axi_tokens = [
        "io_m_axi_arvalid",
        "io_m_axi_arready",
        "io_m_axi_rvalid",
        "io_m_axi_rready",
        "io_m_axi_awvalid",
        "io_m_axi_awready",
        "io_m_axi_wvalid",
        "io_m_axi_wready",
        "io_m_axi_bvalid",
        "io_m_axi_bready",
        "io_input_base_addr",
        "io_weight_base_addr",
        "io_output_base_addr",
    ]
    axi_ok, axi_blockers = token_check("RTL/TB AXI interface", f"{rtl_text}\n{tb_text}", axi_tokens)
    checks.append(check_item("axi_ddr_interface_tokens", axi_ok, "AXI read/write and base-address signals are exposed", missing=axi_blockers))
    blockers.extend(axi_blockers)

    tb_tokens = ["$readmemh", "$value$plusargs", "INPUT_MEMH", "WEIGHT_MEMH", "$fatal", "NO_PROGRESS", "TIMEOUT", "PASS real functional ddr path"]
    tb_ok, tb_blockers = token_check("testbench", tb_text, tb_tokens)
    checks.append(check_item("tb_loads_real_artifacts_and_has_watchdog", tb_ok, "testbench loads real DDR images and has fatal watchdog checks", missing=tb_blockers))
    blockers.extend(tb_blockers)

    return {
        "schema_version": "spatialaccagent.case_deadlock_axi_check.v0",
        "status": "pass" if not blockers else "fail",
        "run_dir": str(run_dir),
        "checks": checks,
        "blockers": blockers,
        "evidence": {
            "vcs_result": str(vcs_path),
            "diagnosis": str(diagnosis_path),
            "runtime_config": str(runtime_path),
            "memory_layout": str(memory_path),
            "rtl_wrappers": [str(path) for path in rtl_paths],
            "testbenches": [str(path) for path in tb_paths],
        },
        "summary": "deadlock/AXI/DDR evidence passed" if not blockers else f"{len(blockers)} blocker(s)",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check real functional deadlock and AXI/DDR evidence for a verification case.")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--vcs-result")
    parser.add_argument("--diagnosis")
    parser.add_argument("--runtime-config", default="generated/chisel/runtime/runtime_config.json")
    parser.add_argument("--memory-layout", default="generated/chisel/memory/memory_layout.json")
    parser.add_argument("--rtl-wrapper", action="append", default=[])
    parser.add_argument("--testbench", action="append", default=[])
    args = parser.parse_args(argv)
    out_path = args.out or args.run_dir / "verification" / "case_diagnostics" / "deadlock_axi_check.json"
    try:
        report = build_report(args)
    except Exception as exc:
        report = {
            "schema_version": "spatialaccagent.case_deadlock_axi_check.v0",
            "status": "fail",
            "run_dir": str(args.run_dir),
            "checks": [],
            "blockers": [str(exc)],
            "summary": str(exc),
        }
    write_json(out_path, report)
    if report["status"] != "pass":
        print(report["summary"], file=sys.stderr)
        return 1
    print(report["summary"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
