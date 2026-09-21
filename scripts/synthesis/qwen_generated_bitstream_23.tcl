# Vivado closure for the SpatialAccAgent-generated Qwen accelerator wrapper.
#
# This is a standalone VU9P bitstream path for the generated FPGA-facing
# AXI/DDR top. It does not claim app_shell board runtime integration.
#
# Usage on server 23 from the remote work directory:
#   vivado -mode batch -source qwen_generated_bitstream_23.tcl \
#     -tclargs <synth|bitstream|power> <clock_period_ns> <fpga_part>

proc get_arg_or_default {idx default_value} {
  if {[llength $::argv] > $idx} {
    return [lindex $::argv $idx]
  }
  return $default_value
}

set mode [get_arg_or_default 0 "bitstream"]
set clock_period_ns [get_arg_or_default 1 "10.000"]
set part_name [get_arg_or_default 2 "xcvu9p_CIV-flgb2104-2-i"]
set top_name "GeneratedAxiDdrTop"
set top_sv [file normalize "GeneratedAxiDdrTop.sv"]
set out_dir [file normalize "vivado_qwen_generated_${mode}"]
set ip_root [file normalize "fpga_ip/vivado_ip"]

if {$mode ni {"synth" "bitstream" "power"}} {
  error "unsupported mode '$mode'; use synth, bitstream, or power"
}
if {$mode eq "power"} {
  set routed_dcp [file normalize "vivado_qwen_generated_bitstream/qwen_generated_routed.dcp"]
  if {![file exists $routed_dcp]} {
    error "missing routed checkpoint: $routed_dcp"
  }
  file delete -force $out_dir
  file mkdir $out_dir
  open_checkpoint $routed_dcp
  report_power -file "$out_dir/qwen_generated_impl_power.rpt"
  puts "Qwen generated power report completed: $out_dir/qwen_generated_impl_power.rpt"
  close_project
  exit 0
}
if {![file exists $top_sv]} {
  error "missing generated top: $top_sv"
}
proc collect_xci_files {root} {
  set files [glob -nocomplain -types f -directory $root *.xci]
  foreach child [glob -nocomplain -types d -directory $root *] {
    set files [concat $files [collect_xci_files $child]]
  }
  return $files
}

set ip_xci_files [lsort [collect_xci_files $ip_root]]
if {[llength $ip_xci_files] == 0} {
  error "no Vivado floating-point IP .xci files found below $ip_root"
}
set sv_files [lsort [glob -nocomplain "*.sv"]]
if {[llength $sv_files] == 0} {
  error "no generated SystemVerilog files found in [pwd]"
}

file delete -force $out_dir
file mkdir $out_dir

create_project -in_memory -part $part_name
set_property target_language Verilog [current_project]
foreach ip_xci $ip_xci_files {
  read_ip $ip_xci
  set ip_file [get_files -quiet $ip_xci]
  if {[llength $ip_file] != 1} {
    error "failed to add Vivado IP to the synthesis fileset: $ip_xci"
  }
  set_property generate_synth_checkpoint false $ip_file
}
generate_target all [get_ips]
export_ip_user_files -of_objects [get_ips] -no_script -sync -force -quiet
foreach sv $sv_files {
  read_verilog -sv $sv
}

proc require_non_io_logic {phase} {
  set logic_cells [get_cells -hier -quiet -filter {REF_NAME !~ IBUF* && REF_NAME !~ OBUF* && REF_NAME !~ IOBUF* && REF_NAME !~ BUFG*}]
  set logic_count [llength $logic_cells]
  puts "Qwen generated $phase non-IO cell count: $logic_count"
  if {$logic_count == 0} {
    error "generated Qwen core collapsed to IO-only logic during $phase"
  }
}

proc ensure_core_clock {} {
  global clock_period_ns
  if {[llength [get_ports -quiet clock]] > 0 && [llength [get_clocks -quiet qwen_core_clk]] == 0} {
    create_clock -name qwen_core_clk -period $clock_period_ns [get_ports clock]
  }
}

synth_design \
  -top $top_name \
  -part $part_name \
  -flatten_hierarchy rebuilt \
  -directive RuntimeOptimized \
  -resource_sharing off \
  -keep_equivalent_registers \
  -no_lc \
  -shreg_min_size 5

ensure_core_clock
require_non_io_logic "synthesis"
report_utilization -hierarchical -hierarchical_depth 3 -file "$out_dir/qwen_generated_synth_utilization.rpt"
report_timing_summary -delay_type max -max_paths 50 -nworst 3 -report_unconstrained -file "$out_dir/qwen_generated_synth_timing.rpt"
write_checkpoint -force "$out_dir/qwen_generated_synth.dcp"

if {$mode eq "synth"} {
  puts "Qwen generated synthesis completed: $out_dir/qwen_generated_synth.dcp"
  close_project
  exit 0
}

opt_design
place_design -directive Quick
phys_opt_design -directive AggressiveExplore
route_design -directive Quick

require_non_io_logic "implementation"
report_utilization -hierarchical -hierarchical_depth 3 -file "$out_dir/qwen_generated_impl_utilization.rpt"
report_timing_summary -delay_type max -max_paths 50 -nworst 3 -report_unconstrained -file "$out_dir/qwen_generated_impl_timing.rpt"
report_route_status -file "$out_dir/qwen_generated_route_status.rpt"
report_drc -file "$out_dir/qwen_generated_drc.rpt"
write_checkpoint -force "$out_dir/qwen_generated_routed.dcp"

# The generated core is standalone and intentionally not assigned to board pins
# yet. Demote pin-planning DRCs so Vivado can still produce a real routed
# device bitstream for the VU9P part. Board-runtime pass remains blocked until
# the Qwen core is wrapped into the app_shell AXI/DDR interface.
foreach drc_id {NSTD-1 UCIO-1} {
  set check [get_drc_checks -quiet $drc_id]
  if {[llength $check] > 0} {
    set_property SEVERITY Warning $check
  }
}
set_property BITSTREAM.GENERAL.COMPRESS TRUE [current_design]
write_bitstream -force "$out_dir/qwen_generated_core.bit"

puts "Qwen generated bitstream completed: $out_dir/qwen_generated_core.bit"
close_project
