#!/usr/bin/env python3
"""Synthesize the generated kernel with external ports for Stage-7 QoR.

Board implementation, when requested, uses an immutable sample-project copy
with its selected compute slot replaced. Kernel synthesis excludes that shell
so inactive adapter connections cannot trim the measured accelerator.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import tarfile
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from accagent.framework.semantic_simulator import persistent_remote_tool_workdir
from accagent.framework.dse_ledger import SYNTHESIS_KERNEL_SCOPE
from scripts.synthesis.compute_slot_adapter_generator import _module_name, _module_port_directions


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def nonblank(value: Any) -> bool:
    return value is not None and value != "" and value != [] and str(value).strip().lower() not in {"none", "null"}


def first_nonblank(*values: Any) -> Any:
    return next((value for value in values if nonblank(value)), None)


def tcl_quote(value: Any) -> str:
    return "{" + str(value or "").replace("\\", "\\\\").replace("}", "\\}") + "}"


def check_file(path: Path, label: str) -> tuple[bool, dict[str, Any]]:
    ok = path.is_file() and path.stat().st_size > 0
    return ok, {
        "name": label,
        "status": "pass" if ok else "fail",
        "path": str(path),
        "size_bytes": path.stat().st_size if path.exists() else 0,
    }


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


def parse_kv_report(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    if not path.is_file():
        return result
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            result[key.strip()] = value.strip()
    return result


def build_kernel_synthesis_tcl(top_module: str, clock_port: str, part: str, clock_target_mhz: float, jobs: int) -> str:
    return f'''set work_dir [lindex $::argv 1]
set generated_root [lindex $::argv 3]
set fp_ip_root [lindex $::argv 4]
set out_dir [file join $work_dir app_shell_runtime_bitstream]
file mkdir $out_dir
create_project -in_memory -part {tcl_quote(part)}
set_param general.maxThreads {min(jobs, 32)}
foreach source [lsort [glob -directory $generated_root *.sv]] {{ read_verilog -sv $source }}
proc collect_xci {{root}} {{
  set files [glob -nocomplain -types f -directory $root *.xci]
  foreach child [glob -nocomplain -types d -directory $root *] {{
    set files [concat $files [collect_xci $child]]
  }}
  return $files
}}
foreach source [collect_xci $fp_ip_root] {{
  read_ip $source
  set_property generate_synth_checkpoint false [get_files $source]
}}
if {{[llength [get_ips -quiet]] > 0}} {{ generate_target all [get_ips] }}
set clock_xdc [file join $work_dir kernel_clock.xdc]
set fh [open $clock_xdc w]
puts $fh {{create_clock -name spatialacc_kernel_clock -period {1000.0 / clock_target_mhz:.6f} [get_ports {tcl_quote(clock_port)}]}}
close $fh
read_xdc -mode out_of_context $clock_xdc
synth_design -top {tcl_quote(top_module)} -part {tcl_quote(part)} -mode out_of_context
if {{[llength [get_cells -hierarchical -filter {{IS_BLACKBOX == 1}}]] > 0}} {{
  error "Generated kernel synthesis contains unresolved black boxes"
}}
report_utilization -hierarchical -hierarchical_depth 9 -file [file join $out_dir app_shell_synth_utilization.rpt]
report_timing_summary -delay_type max -max_paths 50 -nworst 3 -report_unconstrained -file [file join $out_dir app_shell_synth_timing.rpt]
set fh [open [file join $work_dir app_shell_runtime_inspection.txt] w]
puts $fh "kernel_synthesis_completed=1"
puts $fh "kernel_top={top_module}"
puts $fh "measurement_scope={SYNTHESIS_KERNEL_SCOPE}"
puts $fh "integration_ready=1"
close $fh
close_project
'''


def build_tcl(
    target_ip_name: str,
    target_ooc_run: str,
    jobs: int,
    target_bd_cell: str = "",
    clock_port: str = "",
    clock_target_mhz: float | None = None,
) -> str:
    clock_period_ns = (1000.0 / float(clock_target_mhz)) if clock_target_mhz and float(clock_target_mhz) > 0 else None
    clock_period_text = f"{clock_period_ns:.6f}" if clock_period_ns is not None else ""
    return f'''# Generated by SpatialAccAgent app_shell_runtime_vivado.py.
set source_project_xpr [lindex $::argv 0]
set work_dir [lindex $::argv 1]
set adapter_path [lindex $::argv 2]
set generated_root [lindex $::argv 3]
set fp_ip_root [lindex $::argv 4]
set execution_mode "bitstream"
if {{[llength $::argv] > 5}} {{ set execution_mode [lindex $::argv 5] }}
set target_ip_name {tcl_quote(target_ip_name)}
set target_ooc_run {tcl_quote(target_ooc_run)}
set target_bd_cell {tcl_quote(target_bd_cell)}
set spatialacc_clock_port {tcl_quote(clock_port)}
set spatialacc_clock_target_mhz {tcl_quote(clock_target_mhz if clock_target_mhz is not None else "")}
set spatialacc_clock_period_ns {tcl_quote(clock_period_text)}
set jobs {int(jobs)}
set report_path [file join $work_dir app_shell_runtime_inspection.txt]
set out_dir [file join $work_dir app_shell_runtime_bitstream]

proc record {{fh key value}} {{
  set clean [string map [list "\\n" " " "\\r" " " "=" ":"] $value]
  puts $fh "$key=$clean"
  puts "SPATIALACC_APP_SHELL $key=$clean"
}}

proc run_complete {{run}} {{
  set status [get_property STATUS $run]
  return [expr {{[string match "*Complete*" $status] || [string match "*complete*" $status]}}]
}}

proc write_ooc_pre_hook {{path generated_root fp_ip_root adapter_path target_xci activation_marker clock_xdc}} {{
  set fh [open $path w]
  puts $fh "# SpatialAccAgent current compute-slot RTL/IP closure"
  puts $fh "set generated_root [list $generated_root]"
  puts $fh {{foreach f [lsort [glob -nocomplain -directory $generated_root *.sv]] {{ read_verilog -sv $f }}}}
  puts $fh "set fp_ip_root [list $fp_ip_root]"
  puts $fh {{proc spatialacc_collect_xci_files {{root}} {{
  set files [glob -nocomplain -types f -directory $root *.xci]
  foreach child [glob -nocomplain -types d -directory $root *] {{
    set files [concat $files [spatialacc_collect_xci_files $child]]
  }}
  return $files
}}}}
  puts $fh {{foreach f [lsort [spatialacc_collect_xci_files $fp_ip_root]] {{
  read_ip $f
  set o [get_files -quiet $f]
  if {{[llength $o] > 0}} {{ set_property generate_synth_checkpoint false $o }}
}}}}
  puts $fh {{set fp_ips [get_ips -quiet fp_*]}}
  puts $fh {{if {{[llength $fp_ips] > 0}} {{ generate_target all $fp_ips; export_ip_user_files -of_objects $fp_ips -no_script -sync -force -quiet }}}}
  puts $fh "set spatialacc_clock_xdc [list [file normalize $clock_xdc]]"
  puts $fh {{if {{[file exists $::spatialacc_clock_xdc]}} {{ read_xdc -mode out_of_context $::spatialacc_clock_xdc }} }}
  puts $fh "set spatialacc_target_xci [list [file normalize $target_xci]]"
  puts $fh "set spatialacc_adapter_path [list [file normalize $adapter_path]]"
  puts $fh "set spatialacc_activation_marker [list [file normalize $activation_marker]]"
  puts $fh {{set spatialacc_adapter_loaded 0}}
  puts $fh {{rename read_ip spatialacc_original_read_ip}}
  puts $fh {{proc read_ip {{args}} {{
  foreach arg $args {{
    if {{[file normalize $arg] eq $::spatialacc_target_xci}} {{
      if {{!$::spatialacc_adapter_loaded}} {{
        read_verilog -sv $::spatialacc_adapter_path
        set marker [open $::spatialacc_activation_marker w]
        puts $marker "adapter=$::spatialacc_adapter_path"
        puts $marker "generated_top=[file join $::generated_root GeneratedAxiDdrTop.sv]"
        close $marker
        puts "SPATIALACC_COMPUTE_SLOT_ADAPTER_ACTIVE $::spatialacc_adapter_path"
        set ::spatialacc_adapter_loaded 1
      }}
      return
    }}
  }}
  return [uplevel 1 [linsert $args 0 spatialacc_original_read_ip]]
}}}}
  puts $fh {{rename set_property spatialacc_original_set_property}}
  puts $fh {{proc set_property {{args}} {{
  if {{[llength $args] == 3 && [lindex $args 0] eq "used_in_implementation" && [lindex $args 1] eq "false" && [llength [lindex $args 2]] == 0}} {{
    puts "SPATIALACC_REPLACED_SLOT_XDC_OMITTED"
    return
  }}
  return [uplevel 1 [linsert $args 0 spatialacc_original_set_property]]
}}}}
  close $fh
}}

proc file_contains {{path needle}} {{
  if {{![file exists $path]}} {{ return 0 }}
  set fh [open $path r]
  set data [read $fh]
  close $fh
  return [expr {{[string first $needle $data] >= 0}}]
}}

proc same_file_contents {{left right}} {{
  if {{![file exists $left] || ![file exists $right]}} {{ return 0 }}
  set fh [open $left r]
  set left_data [read $fh]
  close $fh
  set fh [open $right r]
  set right_data [read $fh]
  close $fh
  return [expr {{$left_data eq $right_data}}]
}}

file mkdir $out_dir
set fh [open $report_path w]
record $fh source_project_xpr $source_project_xpr
record $fh target_ip_name $target_ip_name
record $fh target_ooc_run $target_ooc_run
record $fh target_bd_cell $target_bd_cell
record $fh adapter_path $adapter_path
record $fh generated_root $generated_root
record $fh fp_ip_root $fp_ip_root
record $fh execution_mode $execution_mode
record $fh clock_port $spatialacc_clock_port
record $fh clock_target_mhz $spatialacc_clock_target_mhz
record $fh clock_period_ns $spatialacc_clock_period_ns

if {{![file exists $source_project_xpr] || ![file exists $adapter_path] || ![file isdirectory $generated_root] || ![file isdirectory $fp_ip_root]}} {{
  record $fh integration_ready 0
  record $fh integration_blocker "required project, adapter, generated RTL, or generated FP IP closure is missing"
  close $fh
  exit 1
}}

# The board sample is immutable.  All target regeneration and OOC state lives
# in this per-run project copy.
set open_status [catch {{open_project $source_project_xpr}} open_message]
record $fh source_open_status $open_status
record $fh source_open_message $open_message
if {{$open_status != 0}} {{ close $fh; exit 1 }}
set project_name [file rootname [file tail $source_project_xpr]]
set clone_root [file join $work_dir project]
file delete -force $clone_root
file mkdir $clone_root
set clone_status [catch {{save_project_as -force -dir $clone_root $project_name}} clone_message]
record $fh project_clone_status $clone_status
record $fh project_clone_message $clone_message
close_project
if {{$clone_status != 0}} {{ close $fh; exit 1 }}
set project_xpr [file join $clone_root "${{project_name}}.xpr"]
set open_status [catch {{open_project $project_xpr}} open_message]
record $fh open_project_status $open_status
record $fh open_project_message $open_message
if {{$open_status != 0}} {{ close $fh; exit 1 }}
record $fh project_dir [file dirname $project_xpr]
record $fh fpga_part [get_property PART [current_project]]

set bd_files [get_files -quiet *.bd]
record $fh bd_count [llength $bd_files]
set target_matches {{}}
set target_bd ""
foreach bd $bd_files {{
  if {{[catch {{open_bd_design $bd}}] != 0}} {{ continue }}
  if {{$target_bd_cell ne ""}} {{
    set target_matches [get_bd_cells -quiet $target_bd_cell]
  }}
  if {{[llength $target_matches] == 0}} {{
    set target_matches [get_bd_cells -quiet -hier *$target_ip_name*]
  }}
  if {{[llength $target_matches] > 0}} {{
    set target_bd $bd
    break
  }}
}}
record $fh target_match_count [llength $target_matches]
if {{[llength $target_matches] > 0}} {{ record $fh target_matches [join $target_matches ","] }}
record $fh target_bd $target_bd
set ip [get_ips -quiet $target_ip_name]
set ip_file [lindex [get_files -all -quiet */$target_ip_name/$target_ip_name.xci] 0]
if {{[llength $bd_files] == 0 || [llength $target_matches] == 0 || [llength $ip] == 0 || $ip_file eq ""}} {{
  record $fh integration_ready 0
  record $fh integration_blocker "selected app-shell compute slot was not found in the copied project"
  close_project
  close $fh
  exit 1
}}
record $fh target_xci $ip_file

# The cloned project already contains the board-generated targets.  Regenerating
# the parent BD here would rebuild unrelated DDR/interconnect IP and makes a
# single compute-slot replacement unnecessarily expensive.
set ooc_run [get_runs -quiet $target_ooc_run]
if {{[llength $ooc_run] == 0}} {{ create_ip_run $ip; set ooc_run [get_runs -quiet $target_ooc_run] }}
if {{[llength $ooc_run] == 0}} {{
  record $fh integration_ready 0
  record $fh integration_blocker "selected compute-slot OOC run was not found or created"
  close_project
  close $fh
  exit 1
}}
# The board OOC script is regenerated at launch.  Replace only the generated
# compute-slot wrapper in this private project, then use the documented run
# pre-hook for the generated RTL/IP dependency closure.  This is the same
# persistent project-level mechanism used by the prior OPT board integration.
set slot_wrapper_files [get_files -all -quiet "*/${{target_ip_name}}/synth/${{target_ip_name}}.v"]
if {{[llength $slot_wrapper_files] != 1}} {{
  record $fh integration_ready 0
  record $fh integration_blocker "selected compute-slot generated wrapper was not uniquely found"
  close_project
  close $fh
  exit 1
}}
set slot_wrapper [lindex $slot_wrapper_files 0]
file copy -force $adapter_path $slot_wrapper
set generated_root [file normalize $generated_root]
set fp_ip_root [file normalize $fp_ip_root]
set ooc_pre_hook [file join $work_dir "${{target_ip_name}}_ooc_pre.tcl"]
set ooc_activation_marker [file join $work_dir "${{target_ip_name}}_adapter_active.txt"]
set ooc_clock_xdc [file join $work_dir spatialacc_dut_clock.xdc]
if {{$spatialacc_clock_port ne "" && $spatialacc_clock_period_ns ne ""}} {{
  set clock_fh [open $ooc_clock_xdc w]
  puts $clock_fh [format {{create_clock -name spatialacc_dut_clock -period %s [get_ports {{%s}}]}} $spatialacc_clock_period_ns $spatialacc_clock_port]
  close $clock_fh
}} else {{
  file delete -force $ooc_clock_xdc
}}
file delete -force $ooc_activation_marker
write_ooc_pre_hook $ooc_pre_hook $generated_root $fp_ip_root $adapter_path $ip_file $ooc_activation_marker $ooc_clock_xdc
set_property STEPS.SYNTH_DESIGN.TCL.PRE $ooc_pre_hook $ooc_run
set ooc_dir [get_property DIRECTORY $ooc_run]
set ooc_tcl [file join $ooc_dir "${{target_ip_name}}.tcl"]
record $fh ooc_run_directory $ooc_dir
record $fh ooc_script $ooc_tcl
record $fh ooc_slot_wrapper $slot_wrapper
record $fh ooc_pre_hook $ooc_pre_hook
record $fh ooc_clock_xdc $ooc_clock_xdc
record $fh ooc_clock_xdc_exists [file exists $ooc_clock_xdc]
record $fh ooc_activation_marker $ooc_activation_marker
record $fh ooc_adapter_copied [same_file_contents $adapter_path $slot_wrapper]
record $fh ooc_pre_hook_bound [expr {{[get_property STEPS.SYNTH_DESIGN.TCL.PRE $ooc_run] eq $ooc_pre_hook}}]
record $fh ooc_pre_hook_marked [file_contains $ooc_pre_hook "# SpatialAccAgent current compute-slot RTL/IP closure"]
if {{$execution_mode eq "preflight"}} {{
  reset_run $ooc_run
  launch_runs $ooc_run -scripts_only
  record $fh ooc_pre_hook_in_script [file_contains $ooc_tcl $ooc_pre_hook]
  record $fh integration_ready [expr {{[same_file_contents $adapter_path $slot_wrapper] && [file_contains $ooc_tcl $ooc_pre_hook] && [file_contains $ooc_pre_hook "# SpatialAccAgent current compute-slot RTL/IP closure"]}}]
  close_project
  close $fh
  exit 0
}}
reset_run $ooc_run
set ooc_resource_source [file join $work_dir src]
if {{[file isdirectory $ooc_resource_source]}} {{
  file copy -force $ooc_resource_source $ooc_dir
}}
launch_runs $ooc_run -jobs $jobs
wait_on_run $ooc_run
record $fh ooc_pre_hook_in_script [file_contains $ooc_tcl $ooc_pre_hook]
record $fh ooc_status [get_property STATUS $ooc_run]
record $fh ooc_synthesis_completed [run_complete $ooc_run]
record $fh ooc_adapter_active [file exists $ooc_activation_marker]
if {{![run_complete $ooc_run]}} {{
  record $fh integration_ready 0
  record $fh integration_blocker "compute-slot OOC synthesis failed"
  close_project
  close $fh
  exit 1
}}
if {{![file exists $ooc_activation_marker]}} {{
  record $fh integration_ready 0
  record $fh integration_blocker "compute-slot OOC did not activate the generated adapter"
  close_project
  close $fh
  exit 1
}}
if {{$execution_mode eq "ooc"}} {{
  record $fh integration_ready 1
  close_project
  close $fh
  exit 0
}}

update_compile_order -fileset sources_1
set top_synth [get_runs -quiet synth_1]
set top_impl [get_runs -quiet impl_1]
if {{[llength $top_synth] == 0 || [llength $top_impl] == 0}} {{
  record $fh integration_ready 0
  record $fh integration_blocker "copied app-shell is missing synth_1 or impl_1"
  close_project
  close $fh
  exit 1
}}
record $fh top_synth_run $top_synth
record $fh top_impl_run $top_impl
reset_run $top_synth
reset_run $top_impl
launch_runs $top_synth -jobs $jobs
wait_on_run $top_synth
record $fh top_synth_status [get_property STATUS $top_synth]
if {{![run_complete $top_synth]}} {{
  record $fh integration_ready 0
  record $fh integration_blocker "app-shell top synthesis failed"
  close_project
  close $fh
  exit 1
}}
if {{$execution_mode eq "synth"}} {{
  open_run $top_synth
  report_utilization -hierarchical -hierarchical_depth 3 -file [file join $out_dir app_shell_synth_utilization.rpt]
  report_timing_summary -delay_type max -max_paths 50 -nworst 3 -report_unconstrained -file [file join $out_dir app_shell_synth_timing.rpt]
  report_power -file [file join $out_dir app_shell_synth_power.rpt]
  record $fh synthesis_reports_ready [expr {{[file exists [file join $out_dir app_shell_synth_utilization.rpt]] && [file exists [file join $out_dir app_shell_synth_timing.rpt]]}}]
  if {{![file exists [file join $out_dir app_shell_synth_utilization.rpt]] || ![file exists [file join $out_dir app_shell_synth_timing.rpt]]}} {{
    record $fh integration_ready 0
    record $fh integration_blocker "app-shell synthesis reports are missing"
    close_project
    close $fh
    exit 1
  }}
  record $fh integration_ready 1
  close_project
  close $fh
  exit 0
}}
launch_runs $top_impl -to_step write_bitstream -jobs $jobs
wait_on_run $top_impl
record $fh top_impl_status [get_property STATUS $top_impl]
if {{![run_complete $top_impl]}} {{
  record $fh integration_ready 0
  record $fh integration_blocker "app-shell implementation or bitstream failed"
  close_project
  close $fh
  exit 1
}}

open_run $top_impl
report_utilization -hierarchical -hierarchical_depth 3 -file [file join $out_dir app_shell_impl_utilization.rpt]
report_timing_summary -delay_type max -max_paths 50 -nworst 3 -report_unconstrained -file [file join $out_dir app_shell_impl_timing.rpt]
report_power -file [file join $out_dir app_shell_impl_power.rpt]
report_route_status -file [file join $out_dir app_shell_route_status.rpt]
report_drc -file [file join $out_dir app_shell_drc.rpt]
write_checkpoint -force [file join $out_dir app_shell_routed.dcp]
set bits [glob -nocomplain -directory [get_property DIRECTORY $top_impl] *.bit]
if {{[llength $bits] > 0}} {{ file copy -force [lindex $bits 0] [file join $out_dir app_shell.bit] }}
record $fh app_shell_bitstream_exists [file exists [file join $out_dir app_shell.bit]]
record $fh implementation_reports_ready [expr {{[file exists [file join $out_dir app_shell_impl_utilization.rpt]] && [file exists [file join $out_dir app_shell_impl_timing.rpt]] && [file exists [file join $out_dir app_shell_impl_power.rpt]]}}]
record $fh integration_ready [expr {{[file exists [file join $out_dir app_shell.bit]]}}]
if {{![file exists [file join $out_dir app_shell.bit]]}} {{ record $fh integration_blocker "implementation completed without copied bitstream" }}
close_project
close $fh
exit 0
'''


def create_source_closure_archive(
    archive: Path,
    generated_vivado_dir: Path,
    ip_module_manifest: Path | None,
    ip_generation_tcl: Path | None,
) -> None:
    archive.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, "w:gz") as bundle:
        bundle.add(generated_vivado_dir, arcname="generated_vivado")
        chisel_root = generated_vivado_dir.parent
        scala_sources = chisel_root / "src" / "main" / "scala"
        runtime_config = chisel_root / "runtime" / "runtime_config.json"
        if scala_sources.is_dir():
            bundle.add(scala_sources, arcname="analysis_context/src/main/scala")
        if runtime_config.is_file():
            bundle.add(runtime_config, arcname="analysis_context/runtime/runtime_config.json")
        resources = generated_vivado_dir.parent / "src" / "main" / "resources"
        if resources.is_dir():
            bundle.add(resources, arcname="src/main/resources")
        if ip_module_manifest is not None:
            bundle.add(ip_module_manifest, arcname="fpga_ip_modules.txt")
        if ip_generation_tcl is not None:
            bundle.add(ip_generation_tcl, arcname="gen_xilinx_fp_ips_23.tcl")
        closure = chisel_root / "simulation" / "fpga_ip_simulation_closure.json"
        if closure.is_file():
            bundle.add(closure, arcname="analysis_context/fpga_ip_simulation_closure.json")


def requires_generated_ip(generated_vivado_dir: Path) -> bool:
    """Only an explicit integer closure may omit generated arithmetic IP."""
    closure_path = generated_vivado_dir.parent / "simulation" / "fpga_ip_simulation_closure.json"
    if not closure_path.is_file():
        return True
    closure = read_json(closure_path)
    return not (
        closure.get("status") in {"ready", "pass"}
        and closure.get("compute_backend") == "integer_dsp"
        and closure.get("required_ip_modules") == []
    )


def kernel_synthesis_reuse_basis(args: argparse.Namespace) -> dict[str, Any] | None:
    """Reuse QoR only when every actual synthesis input is unchanged."""
    if args.mode != "synth" or args.collect_only or not args.out.is_file():
        return None
    prior = read_json(args.out)
    if (prior.get("status") != "pass" or prior.get("mode") != "synth"
            or prior.get("measurement_scope") != SYNTHESIS_KERNEL_SCOPE
            or prior.get("collect_only") is True or prior.get("fpga_part") != args.fpga_part
            or prior.get("clock_target_mhz") != args.clock_target_mhz):
        return None
    archive = Path(str(prior.get("closure_archive") or ""))
    digest = str(prior.get("synthesis_source_archive_sha256") or "")
    preserved_archive = args.run_dir / "backend_board" / "measurements" / digest / archive.name
    archive = next((candidate for candidate in (archive, preserved_archive)
                    if candidate.is_file() and hashlib.sha256(candidate.read_bytes()).hexdigest() == digest), None)
    reports = args.run_dir / "app_shell_runtime_bitstream"
    if (archive is None
            or any(not (reports / name).is_file() or not (reports / name).stat().st_size
                   for name in ["app_shell_synth_utilization.rpt", "app_shell_synth_timing.rpt"])):
        return None
    root = args.generated_vivado_dir.parent
    current = {}
    for directory, prefix in [(args.generated_vivado_dir, "generated_vivado"),
                              (root / "src/main/scala", "analysis_context/src/main/scala"),
                              (root / "src/main/resources", "src/main/resources")]:
        if directory.is_dir():
            current.update({f"{prefix}/{p.relative_to(directory).as_posix()}": p
                            for p in directory.rglob("*") if p.is_file()})
    for path, name in [(root / "runtime/runtime_config.json", "analysis_context/runtime/runtime_config.json"),
                       (root / "simulation/fpga_ip_simulation_closure.json", "analysis_context/fpga_ip_simulation_closure.json")]:
        if path.is_file():
            current[name] = path
    if requires_generated_ip(args.generated_vivado_dir):
        current["fpga_ip_modules.txt"] = args.ip_module_manifest
        current["gen_xilinx_fp_ips_23.tcl"] = args.ip_generation_tcl
    try:
        with tarfile.open(archive, "r:gz") as bundle:
            members = {member.name: member for member in bundle.getmembers() if member.isfile()}
            generator_context = "analysis_context/src/main/scala/"
            archived_inputs = {name: member for name, member in members.items()
                               if not name.startswith(generator_context)}
            current_inputs = {name: path for name, path in current.items()
                              if not name.startswith(generator_context)}
            if set(archived_inputs) != set(current_inputs):
                return None
            if not all(
                current_inputs[name].is_file()
                and bundle.extractfile(member).read() == current_inputs[name].read_bytes()
                for name, member in archived_inputs.items()
            ):
                return None
            complete_match = set(members) == set(current) and all(
                current[name].is_file() and bundle.extractfile(member).read() == current[name].read_bytes()
                for name, member in members.items()
            )
            return {
                "complete_source_payload_matches": complete_match,
                "synthesized_source_payload_matches": True,
                "generator_source_context_matches": complete_match,
                "closure_archive": str(archive),
            }
    except (OSError, tarfile.TarError):
        return None


def reusable_kernel_synthesis(args: argparse.Namespace) -> bool:
    """Reuse a report only when the synthesized implementation payload matches."""
    return kernel_synthesis_reuse_basis(args) is not None


def preserve_successful_synthesis(run_dir: Path, report_path: Path) -> Path | None:
    """Keep completed measurements before a changed design reuses output paths."""
    if not report_path.is_file():
        return None
    prior = read_json(report_path)
    digest = str(prior.get("synthesis_source_archive_sha256") or "")
    if prior.get("status") != "pass" or len(digest) != 64:
        return None
    folder = run_dir / "backend_board/measurements" / digest
    folder.mkdir(parents=True, exist_ok=True)
    paths = [report_path, *sorted((run_dir / "app_shell_runtime_bitstream").glob("app_shell_synth*.rpt")),
             run_dir / "backend_board/qor/qor_metrics.json", run_dir / "backend_board/qor/dse_cycle_estimate.json"]
    archive = Path(str(prior.get("closure_archive") or ""))
    archive_matches = archive.is_file() and hashlib.sha256(archive.read_bytes()).hexdigest() == digest
    if archive_matches:
        paths.append(archive)
    for path in paths:
        target = folder / path.name
        if path.name in {"qor_metrics.json", "dse_cycle_estimate.json"} and path.is_file():
            metric = read_json(path)
            metric_digest = metric.get("synthesis_source_archive_sha256") or metric.get("performance_estimation", {}).get("synthesis_source_archive_sha256")
            if metric_digest != digest:
                continue
        if path.suffix == ".rpt" and path.stat().st_mtime_ns > report_path.stat().st_mtime_ns:
            continue
        if path.is_file() and not target.exists():
            shutil.copy2(path, target)
    if not (folder / "snapshot.json").exists():
        write_json(folder / "snapshot.json", {"synthesis_source_archive_sha256": digest,
                   "original_archive_preserved": archive_matches, "measurement_report": report_path.name})
    return folder


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run real app-shell compute-slot Vivado synthesis or implementation.")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--wrapper-rtl", type=Path, required=True)
    parser.add_argument("--generated-vivado-dir", type=Path, required=True)
    parser.add_argument("--ip-module-manifest", type=Path, required=True)
    parser.add_argument("--ip-generation-tcl", type=Path, required=True)
    parser.add_argument("--fpga-part", required=True)
    parser.add_argument("--clock-target-mhz", type=float, default=None)
    parser.add_argument("--mode", choices=["preflight", "ooc", "synth", "bitstream"], default="synth")
    parser.add_argument("--collect-only", action="store_true")
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    reuse_basis = kernel_synthesis_reuse_basis(args)
    if reuse_basis is not None:
        prior = read_json(args.out)
        prior.setdefault("original_synthesis_report_sha256", hashlib.sha256(args.out.read_bytes()).hexdigest())
        prior["closure_archive"] = reuse_basis.pop("closure_archive")
        prior["synthesis_reuse"] = {
            "validated_at_unix_ns": time.time_ns(),
            **reuse_basis,
            "new_synthesis_executed": False,
        }
        write_json(args.out, prior)
        print("Reusing successful kernel synthesis: synthesis inputs, part, clock and reports match; no Vivado rerun.")
        return 0
    run_dir = args.run_dir.resolve()
    preserve_successful_synthesis(run_dir, args.out)
    contract = read_json(args.contract) if args.contract.is_file() else {}
    shell = contract.get("shell_project", {}) if isinstance(contract.get("shell_project"), dict) else {}
    target = contract.get("integration_target", {}) if isinstance(contract.get("integration_target"), dict) else {}
    abi = contract.get("compute_slot_abi", {}) if isinstance(contract.get("compute_slot_abi"), dict) else {}

    remote_host = str(first_nonblank(os.environ.get("REMOTE_HOST"), shell.get("remote_host"), ""))
    remote_port = str(first_nonblank(os.environ.get("REMOTE_PORT"), shell.get("remote_ssh_port"), "22"))
    vivado_bin = str(first_nonblank(os.environ.get("VIVADO_BIN"), ""))
    remote_known_hosts = os.environ.get("REMOTE_KNOWN_HOSTS", "/tmp/codex_ssh_known_hosts").strip()
    remote_workdir = os.environ.get(
        "REMOTE_WORKDIR",
        persistent_remote_tool_workdir(remote_host, "vivado_app_shell_runtime", run_dir.name),
    ).strip()
    project_xpr = str(first_nonblank(os.environ.get("SPATIALACC_APP_SHELL_PROJECT_XPR"), shell.get("vivado_project_path"), ""))
    target_ip_name = str(first_nonblank(target.get("replacement_module_identity"), target.get("ip_name"), abi.get("replacement_module_identity"), ""))
    target_ooc_run = str(first_nonblank(target.get("ooc_run"), abi.get("ooc_run"), f"{target_ip_name}_synth_1" if target_ip_name else ""))
    target_bd_cell = str(first_nonblank(target.get("bd_cell"), target.get("replacement_instance_boundary"), abi.get("replacement_instance_boundary"), abi.get("slot_instance_path"), ""))
    board_interface = contract.get("board_interface", {}) if isinstance(contract.get("board_interface"), dict) else {}
    board_clock = str(first_nonblank(board_interface.get("clock"), ""))
    control_abi = abi.get("control_abi", {}) if isinstance(abi.get("control_abi"), dict) else {}
    control_clock = str(first_nonblank(control_abi.get("clock_domain"), ""))
    clock_port = board_clock or control_clock
    clock_domain_mismatch = board_clock and control_clock and board_clock != control_clock
    jobs = int(os.environ.get("SPATIALACC_VIVADO_JOBS", "16"))

    out_dir = run_dir / "app_shell_runtime_bitstream"
    script_dir = run_dir / "generated" / "backend" / "scripts"
    tcl_path = script_dir / "app_shell_runtime_vivado.tcl"
    archive = script_dir / "app_shell_generated_vivado_closure.tar.gz"
    inspection_path = out_dir / "app_shell_runtime_inspection.txt"
    checks: list[dict[str, Any]] = []
    blockers: list[str] = []
    kernel_top = ""
    kernel_clock = ""
    if args.mode == "synth":
        top_path = args.generated_vivado_dir / "GeneratedAxiDdrTop.sv"
        try:
            top_text = top_path.read_text(encoding="utf-8")
            kernel_top = _module_name(top_text)
            kernel_clock = str(contract.get("generated_core", {}).get("clock_port") or "clock")
            if _module_port_directions(top_text).get(kernel_clock) != "input":
                raise ValueError(f"generated top has no input clock port {kernel_clock!r}")
        except (OSError, ValueError) as exc:
            blockers.append(str(exc))
        if not args.clock_target_mhz or args.clock_target_mhz <= 0:
            blockers.append("kernel synthesis requires a positive --clock-target-mhz")
    generated_ip_required = requires_generated_ip(args.generated_vivado_dir)
    required_sources = [("generated_vivado_dir", args.generated_vivado_dir)]
    if generated_ip_required:
        required_sources.extend([
            ("fp_ip_module_manifest", args.ip_module_manifest),
            ("fp_ip_generation_tcl", args.ip_generation_tcl),
        ])
    if args.mode != "synth":
        required_sources.extend([("contract", args.contract), ("compute_slot_adapter", args.wrapper_rtl)])
    for label, path in required_sources:
        ok, item = check_file(path, label) if path.is_file() else (path.is_dir() and any(path.iterdir()), {"name": label, "status": "pass" if path.is_dir() and any(path.iterdir()) else "fail", "path": str(path)})
        checks.append(item)
        if not ok:
            blockers.append(f"missing or empty {label}: {path}")
    if not args.collect_only:
        required_config = [("REMOTE_HOST", remote_host), ("VIVADO_BIN", vivado_bin)]
        if args.mode != "synth":
            required_config.extend([("shell_project.vivado_project_path", project_xpr), ("target compute IP", target_ip_name), ("target compute BD cell", target_bd_cell), ("target OOC run", target_ooc_run)])
        for name, value in required_config:
            if not nonblank(value):
                blockers.append(f"{name} is not configured")
    if clock_domain_mismatch and args.mode != "synth":
        blockers.append(f"board clock {board_clock!r} does not match compute-slot control clock {control_clock!r}")
    if args.clock_target_mhz is not None and args.clock_target_mhz <= 0:
        blockers.append("--clock-target-mhz must be positive")

    commands: list[dict[str, Any]] = []
    inspection: dict[str, str] = {}
    source_archive_sha256 = None
    if not blockers and not args.collect_only:
        script_dir.mkdir(parents=True, exist_ok=True)
        tcl_path.write_text(
            build_kernel_synthesis_tcl(kernel_top, kernel_clock, args.fpga_part, args.clock_target_mhz, jobs)
            if args.mode == "synth" else build_tcl(
                target_ip_name,
                target_ooc_run,
                jobs,
                target_bd_cell,
                clock_port,
                args.clock_target_mhz,
            ),
            encoding="utf-8",
        )
        create_source_closure_archive(
            archive, args.generated_vivado_dir,
            args.ip_module_manifest if generated_ip_required else None,
            args.ip_generation_tcl if generated_ip_required else None,
        )
        source_archive_sha256 = hashlib.sha256(archive.read_bytes()).hexdigest()
        ssh_base = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", f"UserKnownHostsFile={remote_known_hosts}", "-p", remote_port, remote_host]
        scp_base = ["scp", "-q", "-P", remote_port, "-o", "StrictHostKeyChecking=no", "-o", f"UserKnownHostsFile={remote_known_hosts}"]
        def run_step(argv: list[str], timeout_sec: int | None) -> bool:
            command = run_cmd(argv, timeout_sec)
            commands.append(command)
            if command["returncode"] == 0:
                return True
            blockers.append(f"command failed returncode={command['returncode']}: {' '.join(command['argv'][:3])}")
            return False

        remote_prepare = (
            f"rm -rf {shlex.quote(remote_workdir)} && "
            f"mkdir -p {shlex.quote(remote_workdir)}/fpga_ip/vivado_ip"
        )
        ready = run_step([*ssh_base, remote_prepare], 300)
        if ready:
            upload_sources = [tcl_path, archive]
            if args.mode != "synth":
                upload_sources.extend([args.contract, args.wrapper_rtl])
            ready = run_step(
                [*scp_base, *[str(path) for path in upload_sources], f"{remote_host}:{remote_workdir}/"],
                600,
            )
        if ready:
            remote_unpack = f"cd {shlex.quote(remote_workdir)} && tar -xzf {shlex.quote(archive.name)}"
            ready = run_step([*ssh_base, remote_unpack], 300)
        if ready and args.mode != "preflight" and generated_ip_required:
            remote_ip = (
                f"cd {shlex.quote(remote_workdir)} && {shlex.quote(vivado_bin)} -mode batch -nojournal -nolog "
                f"-source gen_xilinx_fp_ips_23.tcl -tclargs fpga_ip_project fpga_ip/vivado_ip {shlex.quote(args.fpga_part)} fpga_ip_modules.txt"
            )
            ready = run_step([*ssh_base, remote_ip], None)
        if ready:
            remote_vivado = (
                f"cd {shlex.quote(remote_workdir)} && {shlex.quote(vivado_bin)} -mode batch "
                f"-source {shlex.quote(tcl_path.name)} -tclargs {shlex.quote(project_xpr)} {shlex.quote(remote_workdir)} "
                f"{shlex.quote(args.wrapper_rtl.name)} generated_vivado fpga_ip/vivado_ip {shlex.quote(args.mode)}"
            )
            ready = run_step([*ssh_base, remote_vivado], None)
        out_dir.parent.mkdir(parents=True, exist_ok=True)
        if out_dir.exists():
            shutil.rmtree(out_dir)
        if ready:
            ready = run_step([*scp_base, "-r", f"{remote_host}:{remote_workdir}/app_shell_runtime_bitstream", str(run_dir)], 600)
        if ready:
            run_step([*scp_base, f"{remote_host}:{remote_workdir}/app_shell_runtime_inspection.txt", str(inspection_path)], 300)
        inspection = parse_kv_report(inspection_path)
    elif args.collect_only and not blockers:
        collected_inspection = inspection_path
        if not collected_inspection.is_file():
            collected_inspection = run_dir / "app_shell_runtime_inspection.txt"
        inspection = parse_kv_report(collected_inspection)

    required_artifacts: list[tuple[Path, str]] = []
    if args.mode == "bitstream":
        required_artifacts = [
            (out_dir / "app_shell_impl_utilization.rpt", "implementation_utilization"),
            (out_dir / "app_shell_impl_timing.rpt", "implementation_timing"),
            (out_dir / "app_shell_impl_power.rpt", "implementation_power"),
            (out_dir / "app_shell_route_status.rpt", "route_status"),
            (out_dir / "app_shell_drc.rpt", "drc"),
            (out_dir / "app_shell_routed.dcp", "routed_checkpoint"),
            (out_dir / "app_shell.bit", "app_shell_bitstream"),
        ]
    elif args.mode == "synth":
        required_artifacts = [
            (out_dir / "app_shell_synth_utilization.rpt", "synthesis_utilization"),
            (out_dir / "app_shell_synth_timing.rpt", "synthesis_timing"),
        ]
    for path, label in required_artifacts:
        ok, item = check_file(path, label)
        checks.append(item)
        if not ok:
            blockers.append(f"missing or empty {label}: {path}")
    if inspection:
        if args.mode != "synth":
            checks.append({"name": "app_shell_project_opened", "status": "pass" if inspection.get("open_project_status") == "0" else "fail", "summary": inspection.get("open_project_message", "")})
        if args.mode == "preflight":
            checks.append({"name": "compute_slot_ooc_binding", "status": "pass" if inspection.get("ooc_adapter_copied") == "1" and inspection.get("ooc_pre_hook_bound") == "1" and inspection.get("ooc_pre_hook_in_script") == "1" else "fail", "summary": inspection.get("ooc_script", "")})
        elif args.mode == "ooc":
            checks.append({"name": "compute_slot_ooc", "status": "pass" if inspection.get("ooc_synthesis_completed") == "1" and inspection.get("ooc_adapter_active") == "1" else "fail", "summary": inspection.get("ooc_status", "")})
        elif args.mode == "synth":
            if inspection.get("kernel_synthesis_completed") != "1" or inspection.get("kernel_top") != kernel_top:
                blockers.append("current generated kernel OOC synthesis evidence is missing")
            checks.append({"name": "generated_kernel_synthesis", "status": "pass" if not blockers else "fail", "summary": kernel_top})
        else:
            checks.append({"name": "compute_slot_ooc", "status": "pass" if inspection.get("ooc_synthesis_completed") == "1" and inspection.get("ooc_adapter_active") == "1" else "fail", "summary": inspection.get("ooc_status", "")})
            checks.append({"name": "app_shell_top_synthesis", "status": "pass" if "Complete" in inspection.get("top_synth_status", "") else "fail", "summary": inspection.get("top_synth_status", "")})
        if args.mode == "bitstream":
            checks.append({"name": "app_shell_implementation", "status": "pass" if "Complete" in inspection.get("top_impl_status", "") else "fail", "summary": inspection.get("top_impl_status", "")})
        if inspection.get("integration_ready") != "1":
            blockers.append(f"app-shell integration did not complete: {inspection.get('integration_blocker', 'missing completion state')}")
    elif not blockers:
        blockers.append("app-shell runtime inspection report is missing")

    report = {
        "schema_version": "spatialaccagent.app_shell_runtime_vivado.v1",
        "status": "pass" if not blockers else "fail",
        "summary": ("real generated-kernel OOC synthesis passed" if args.mode == "synth" else f"real app-shell Vivado {args.mode} flow passed") if not blockers else f"{len(list(dict.fromkeys(blockers)))} blocker(s)",
        "run_dir": str(run_dir),
        "mode": args.mode,
        "measurement_scope": SYNTHESIS_KERNEL_SCOPE if args.mode == "synth" else "exact_target_board_app_shell",
        "synthesis_top": kernel_top if args.mode == "synth" else target_ip_name,
        "synthesis_boundary": "generated_top_with_external_ports" if args.mode == "synth" else "board_app_shell",
        "timing_clock": "spatialacc_kernel_clock" if args.mode == "synth" else None,
        "collect_only": args.collect_only,
        "contract": str(args.contract),
        "compute_slot_adapter": str(args.wrapper_rtl),
        "generated_vivado_dir": str(args.generated_vivado_dir),
        "ip_module_manifest": str(args.ip_module_manifest),
        "ip_generation_tcl": str(args.ip_generation_tcl),
        "fpga_part": args.fpga_part,
        "closure_archive": str(archive),
        "synthesis_source_archive_sha256": source_archive_sha256,
        "out_dir": str(out_dir),
        "tcl": str(tcl_path),
        "remote_host": remote_host,
        "remote_workdir": remote_workdir,
        "vivado_bin": vivado_bin,
        "shell_project_xpr": project_xpr,
        "target_ip_name": target_ip_name,
        "target_ooc_run": target_ooc_run,
        "target_bd_cell": target_bd_cell,
        "clock_port": kernel_clock if args.mode == "synth" else clock_port,
        "control_clock": control_clock,
        "clock_target_mhz": args.clock_target_mhz,
        "clock_period_ns": (1000.0 / args.clock_target_mhz) if args.clock_target_mhz else None,
        "inspection": inspection,
        "checks": checks,
        "blockers": list(dict.fromkeys(blockers)),
        "commands": commands,
        "acceptance_policy": {
            "preflight": "Pass requires opening a private app-shell copy and patching the selected compute-slot OOC Tcl; it performs no synthesis or implementation.",
            "ooc": "Pass requires real selected compute-slot OOC synthesis with the generated adapter activated; it performs no app-shell top synthesis or implementation.",
            "synth": "Pass requires real generated-kernel OOC synthesis with external input/output ports and resolved IP; excludes the sample board shell and unrelated compute slots.",
            "bitstream": "Pass requires real compute-slot OOC synthesis and app-shell implementation reports/bitstream. Timing and QoR are reported as measurements, not a tool-flow completion blocker.",
        }[args.mode],
    }
    write_json(args.out, report)
    if report["status"] != "pass":
        print(report["summary"], file=sys.stderr)
        return 1
    print(report["summary"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
