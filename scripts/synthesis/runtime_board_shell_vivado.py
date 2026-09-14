#!/usr/bin/env python3
"""Run a contract-driven Vivado flow for a generated board-shell wrapper."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from accagent.framework.semantic_simulator import persistent_remote_tool_workdir


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def nonblank(value: Any) -> bool:
    return value is not None and value != "" and value != [] and str(value).strip().lower() not in {"none", "null"}


def clean_ident(value: Any) -> str | None:
    if not nonblank(value):
        return None
    text = str(value).strip().strip("`'\"").rstrip("*").rstrip("_")
    return text if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", text) else None


def int_value(value: Any, default: int | None = None) -> int | None:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return int(value.strip(), 0)
        except ValueError:
            return default
    return default


def canonical_part_candidates(raw: Any) -> list[str]:
    if not nonblank(raw):
        return []
    text = str(raw).strip().strip("`'\"")
    candidates = [text]
    match = re.match(r"^(xc[a-z0-9]+)_[A-Za-z0-9]+-(.+)$", text, re.I)
    if match:
        candidates.append(f"{match.group(1)}-{match.group(2)}")
    lowered = [item.lower() for item in candidates]
    return list(dict.fromkeys(lowered))


def contract_board_profile(contract: dict[str, Any]) -> dict[str, Any]:
    source = contract.get("source_artifacts", {}) if isinstance(contract.get("source_artifacts"), dict) else {}
    path = Path(str(source.get("resolved_target_board_profile") or ""))
    return read_json(path) if str(path) and path.is_file() else {}


def part_candidates(contract: dict[str, Any]) -> list[str]:
    profile = contract_board_profile(contract)
    board = profile.get("board", {}) if isinstance(profile.get("board"), dict) else {}
    return canonical_part_candidates(board.get("fpga_part"))


def clock_port(contract: dict[str, Any]) -> str | None:
    board = contract.get("board_interface", {}) if isinstance(contract.get("board_interface"), dict) else {}
    return clean_ident(board.get("clock"))


def top_module_from_wrapper(path: Path) -> str | None:
    text = read_text(path)
    match = re.search(r"\bmodule\s+([A-Za-z_][A-Za-z0-9_]*)\b", text)
    return match.group(1) if match else None


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


def drc_structural_blockers(text: str) -> list[str]:
    blockers: list[str] = []
    if not text:
        return blockers
    io_match = re.search(
        r"CIV Device exceeds SE IO Count Limit.*?limited to a total of\s+([0-9]+).*?but\s+([0-9]+)\s+are used",
        text,
        re.I | re.S,
    )
    if io_match:
        blockers.append(
            "standalone board-shell top exposes too many physical IOs: "
            f"used={io_match.group(2)} limit={io_match.group(1)}; "
            "the accelerator must be integrated inside the board app_shell/DDR AXI subsystem instead of treating the AXI bus as top-level FPGA pins"
        )
    if "Unspecified I/O Standard" in text:
        blockers.append("top-level board-shell ports lack IOSTANDARD constraints; app_shell integration or board XDC is required")
    if "Unconstrained Logical Port" in text:
        blockers.append("top-level board-shell ports lack LOC constraints; app_shell integration or board XDC is required")
    return blockers


def check_file(path: Path, label: str) -> tuple[bool, dict[str, Any]]:
    exists = path.exists()
    size = path.stat().st_size if exists else 0
    return exists and size > 0, {"name": label, "status": "pass" if exists and size > 0 else "fail", "path": str(path), "size_bytes": size}


def build_tcl(
    *,
    mode: str,
    part_values: list[str],
    top_name: str,
    clock_name: str | None,
    clock_period_ns: str,
    out_dir: str,
    strict_io: bool,
) -> str:
    part_list = " ".join(part_values)
    strict = "1" if strict_io else "0"
    clock_block = ""
    if clock_name:
        clock_block = f"""
if {{[llength [get_ports -quiet {clock_name}]] > 0 && [llength [get_clocks -quiet runtime_board_shell_clk]] == 0}} {{
  create_clock -name runtime_board_shell_clk -period $clock_period_ns [get_ports {clock_name}]
}}
"""
    return f"""# Generated by SpatialAccAgent runtime_board_shell_vivado.py.
set mode "{mode}"
set clock_period_ns "{clock_period_ns}"
set top_name "{top_name}"
set out_dir [file normalize "{out_dir}"]
set strict_io_drc {strict}
set candidate_parts {{{part_list}}}

set selected_part ""
foreach part_name $candidate_parts {{
  if {{[llength [get_parts -quiet $part_name]] > 0}} {{
    set selected_part $part_name
    break
  }}
}}
if {{$selected_part eq ""}} {{
  error "no Vivado-recognized FPGA part found in candidate list: $candidate_parts"
}}
puts "SpatialAccAgent runtime board-shell selected_part=$selected_part"

file delete -force $out_dir
file mkdir $out_dir
create_project -in_memory -part $selected_part
set_property target_language Verilog [current_project]
set sv_files [lsort [glob -nocomplain "*.sv"]]
if {{[llength $sv_files] == 0}} {{
  error "no SystemVerilog files found in [pwd]"
}}
foreach sv $sv_files {{
  read_verilog -sv $sv
}}
synth_design -top $top_name -part $selected_part -flatten_hierarchy rebuilt -directive RuntimeOptimized -resource_sharing off -keep_equivalent_registers -no_lc -shreg_min_size 5
{clock_block}
report_utilization -hierarchical -hierarchical_depth 3 -file "$out_dir/runtime_board_shell_synth_utilization.rpt"
report_timing_summary -delay_type max -max_paths 50 -nworst 3 -report_unconstrained -file "$out_dir/runtime_board_shell_synth_timing.rpt"
report_drc -file "$out_dir/runtime_board_shell_pre_place_drc.rpt"
write_checkpoint -force "$out_dir/runtime_board_shell_synth.dcp"
if {{$mode eq "synth"}} {{
  puts "SpatialAccAgent runtime board-shell synthesis completed"
  close_project
  exit 0
}}

opt_design
set place_status [catch {{place_design -directive Quick}} place_message]
if {{$place_status != 0}} {{
  set fh [open "$out_dir/runtime_board_shell_place_error.txt" "w"]
  puts $fh $place_message
  close $fh
  report_drc -file "$out_dir/runtime_board_shell_place_drc.rpt"
  error "place_design failed: $place_message"
}}
phys_opt_design -directive AggressiveExplore
route_design -directive Quick
report_utilization -hierarchical -hierarchical_depth 3 -file "$out_dir/runtime_board_shell_impl_utilization.rpt"
report_timing_summary -delay_type max -max_paths 50 -nworst 3 -report_unconstrained -file "$out_dir/runtime_board_shell_impl_timing.rpt"
report_route_status -file "$out_dir/runtime_board_shell_route_status.rpt"
report_drc -file "$out_dir/runtime_board_shell_drc.rpt"
write_checkpoint -force "$out_dir/runtime_board_shell_routed.dcp"

if {{$strict_io_drc == 0}} {{
  foreach drc_id {{NSTD-1 UCIO-1}} {{
    set check [get_drc_checks -quiet $drc_id]
    if {{[llength $check] > 0}} {{
      set_property SEVERITY Warning $check
    }}
  }}
}}
set_property BITSTREAM.GENERAL.COMPRESS TRUE [current_design]
write_bitstream -force "$out_dir/runtime_board_shell.bit"
puts "SpatialAccAgent runtime board-shell bitstream completed"
close_project
"""


def run_cmd(argv: list[str], timeout_sec: int | None = None) -> dict[str, Any]:
    started = time.monotonic()
    try:
        proc = subprocess.run(argv, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout_sec, check=False)
        return {
            "argv": argv,
            "returncode": proc.returncode,
            "stdout_tail": proc.stdout[-8000:],
            "stderr_tail": proc.stderr[-8000:],
            "duration_sec": time.monotonic() - started,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "argv": argv,
            "returncode": 124,
            "stdout_tail": (exc.stdout or "")[-8000:] if isinstance(exc.stdout, str) else "",
            "stderr_tail": (exc.stderr or "")[-8000:] if isinstance(exc.stderr, str) else "",
            "duration_sec": time.monotonic() - started,
        }


def summarize_reports(out_dir: Path, mode: str) -> tuple[list[dict[str, Any]], list[str]]:
    checks: list[dict[str, Any]] = []
    blockers: list[str] = []
    required = [
        (out_dir / "runtime_board_shell_synth.dcp", "synth_checkpoint"),
        (out_dir / "runtime_board_shell_synth_timing.rpt", "synth_timing_report"),
        (out_dir / "runtime_board_shell_synth_utilization.rpt", "synth_utilization_report"),
        (out_dir / "runtime_board_shell_pre_place_drc.rpt", "pre_place_drc_report"),
    ]
    if mode == "bitstream":
        required.extend(
            [
                (out_dir / "runtime_board_shell_routed.dcp", "routed_checkpoint"),
                (out_dir / "runtime_board_shell_impl_timing.rpt", "implementation_timing_report"),
                (out_dir / "runtime_board_shell_impl_utilization.rpt", "implementation_utilization_report"),
                (out_dir / "runtime_board_shell_route_status.rpt", "route_status_report"),
                (out_dir / "runtime_board_shell_drc.rpt", "drc_report"),
                (out_dir / "runtime_board_shell.bit", "runtime_bitstream"),
            ]
        )
    for path, label in required:
        ok, item = check_file(path, label)
        checks.append(item)
        if not ok:
            blockers.append(f"missing or empty {label}: {path}")
    if mode == "bitstream":
        place_error = read_text(out_dir / "runtime_board_shell_place_error.txt")
        if place_error:
            checks.append({"name": "place_design_error", "status": "fail", "summary": place_error[:1000], "path": str(out_dir / "runtime_board_shell_place_error.txt")})
            blockers.append(f"place_design failed: {place_error.strip()[:300]}")
        place_drc_text = read_text(out_dir / "runtime_board_shell_place_drc.rpt") or read_text(out_dir / "runtime_board_shell_pre_place_drc.rpt")
        ok, summary = drc_ok(place_drc_text)
        checks.append({"name": "place_or_pre_place_drc_no_error_or_critical_warning", "status": "pass" if ok else "fail", "summary": summary})
        if not ok:
            blockers.append(f"pre/place DRC is not clean: {summary}")
            blockers.extend(drc_structural_blockers(place_drc_text))
        ok, summary = route_status_ok(read_text(out_dir / "runtime_board_shell_route_status.rpt"))
        checks.append({"name": "route_fully_routed", "status": "pass" if ok else "fail", "summary": summary})
        if not ok:
            blockers.append(f"route status is not clean: {summary}")
        ok, summary = timing_ok(read_text(out_dir / "runtime_board_shell_impl_timing.rpt"))
        checks.append({"name": "implementation_timing_met", "status": "pass" if ok else "fail", "summary": summary})
        if not ok:
            blockers.append(f"implementation timing is not met: {summary}")
        ok, summary = drc_ok(read_text(out_dir / "runtime_board_shell_drc.rpt"))
        checks.append({"name": "drc_no_error_or_critical_warning", "status": "pass" if ok else "fail", "summary": summary})
        if not ok:
            blockers.append(f"DRC is not clean: {summary}")
    return checks, blockers


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run runtime board-shell Vivado flow.")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--wrapper-rtl", type=Path, required=True)
    parser.add_argument("--mode", choices=["synth", "bitstream"], default="bitstream")
    parser.add_argument("--clock-period-ns", default="20.000")
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    run_dir = args.run_dir.resolve()
    contract = read_json(args.contract) if args.contract.exists() else {}
    remote_host = os.environ.get("REMOTE_HOST", "").strip()
    remote_port = os.environ.get("REMOTE_PORT", "22").strip()
    vivado_bin = os.environ.get("VIVADO_BIN", "").strip()
    remote_known_hosts = os.environ.get("REMOTE_KNOWN_HOSTS", "/tmp/codex_ssh_known_hosts").strip()
    remote_workdir = os.environ.get(
        "REMOTE_WORKDIR",
        persistent_remote_tool_workdir(
            remote_host, "vivado_runtime_board_shell", run_dir.name
        ),
    ).strip()
    strict_io = os.environ.get("SPATIALACC_RUNTIME_STRICT_IO_DRC", "1").strip().lower() not in {"0", "false", "no", "off"}
    out_dir = run_dir / f"runtime_board_shell_{args.mode}"
    scripts_dir = run_dir / "generated" / "backend" / "scripts"
    tcl_path = scripts_dir / "runtime_board_shell_vivado.tcl"
    checks: list[dict[str, Any]] = []
    blockers: list[str] = []
    for label, path in [("contract", args.contract), ("wrapper_rtl", args.wrapper_rtl)]:
        ok, item = check_file(path, label)
        checks.append(item)
        if not ok:
            blockers.append(f"missing or empty {label}: {path}")
    sv_dir = run_dir / "generated" / "chisel"
    sv_files = sorted(sv_dir.glob("*.sv"))
    if not sv_files:
        blockers.append(f"no generated core RTL files found: {sv_dir}")
    part_values = part_candidates(contract)
    if not part_values:
        blockers.append("no FPGA part candidates found in resolved board profile")
    top_name = top_module_from_wrapper(args.wrapper_rtl)
    if not top_name:
        blockers.append(f"could not parse top module from wrapper RTL: {args.wrapper_rtl}")
    for name, value in [("REMOTE_HOST", remote_host), ("VIVADO_BIN", vivado_bin)]:
        if not value:
            blockers.append(f"{name} is not configured")

    commands: list[dict[str, Any]] = []
    if not blockers:
        assert top_name is not None
        tcl_text = build_tcl(
            mode=args.mode,
            part_values=part_values,
            top_name=top_name,
            clock_name=clock_port(contract),
            clock_period_ns=args.clock_period_ns,
            out_dir=f"runtime_board_shell_{args.mode}",
            strict_io=strict_io,
        )
        tcl_path.parent.mkdir(parents=True, exist_ok=True)
        tcl_path.write_text(tcl_text, encoding="utf-8")
        ssh_base = [
            "ssh",
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            f"UserKnownHostsFile={remote_known_hosts}",
            "-p",
            remote_port,
            remote_host,
        ]
        scp_base = [
            "scp",
            "-q",
            "-P",
            remote_port,
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            f"UserKnownHostsFile={remote_known_hosts}",
        ]
        remote_prepare = f"mkdir -p {shlex.quote(remote_workdir)} && rm -f {shlex.quote(remote_workdir)}/*.sv {shlex.quote(remote_workdir)}/runtime_board_shell_vivado.tcl"
        commands.append(run_cmd([*ssh_base, remote_prepare], 120))
        sv_sources = [str(path) for path in sv_files] + [str(args.wrapper_rtl), str(tcl_path)]
        commands.append(run_cmd([*scp_base, *sv_sources, f"{remote_host}:{remote_workdir}/"], 300))
        stamp = time.strftime("%Y%m%d_%H%M%S")
        remote_vivado = (
            f"cd {shlex.quote(remote_workdir)} && "
            f"{shlex.quote(vivado_bin)} -mode batch -source runtime_board_shell_vivado.tcl "
            f"-log runtime_board_shell_{args.mode}_{stamp}.log -journal runtime_board_shell_{args.mode}.jou"
        )
        commands.append(run_cmd([*ssh_base, remote_vivado], None))
        out_dir.parent.mkdir(parents=True, exist_ok=True)
        if out_dir.exists():
            shutil.rmtree(out_dir)
        commands.append(run_cmd([*scp_base, "-r", f"{remote_host}:{remote_workdir}/runtime_board_shell_{args.mode}", str(run_dir / f"runtime_board_shell_{args.mode}")], 300))
        nested_out_dir = out_dir / out_dir.name
        if nested_out_dir.is_dir():
            for item in nested_out_dir.iterdir():
                shutil.move(str(item), str(out_dir / item.name))
            nested_out_dir.rmdir()
        for command in commands:
            if command.get("returncode") not in {0, None}:
                blockers.append(f"command failed returncode={command.get('returncode')}: {' '.join(command.get('argv', [])[:3])}")
                break

    report_checks, report_blockers = summarize_reports(out_dir, args.mode)
    checks.extend(report_checks)
    blockers.extend(report_blockers)
    report = {
        "schema_version": "spatialaccagent.runtime_board_shell_vivado.v0",
        "status": "pass" if not blockers else "fail",
        "summary": "runtime board-shell Vivado flow passed" if not blockers else f"{len(blockers)} blocker(s)",
        "run_dir": str(run_dir),
        "mode": args.mode,
        "contract": str(args.contract),
        "wrapper_rtl": str(args.wrapper_rtl),
        "out_dir": str(out_dir),
        "tcl": str(tcl_path),
        "remote_host": remote_host,
        "remote_workdir": remote_workdir,
        "vivado_bin": vivado_bin,
        "part_candidates": part_values,
        "strict_io_drc": strict_io,
        "checks": checks,
        "blockers": list(dict.fromkeys(blockers)),
        "commands": commands,
        "acceptance_policy": "Pass requires real Vivado artifacts for the generated board-shell wrapper. Standalone generated-core bitstreams do not satisfy this gate.",
    }
    write_json(args.out, report)
    if report["status"] != "pass":
        print(report["summary"], file=sys.stderr)
        return 1
    print(report["summary"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
