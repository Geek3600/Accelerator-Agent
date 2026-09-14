# Standalone Vivado synthesis for the generated Qwen2 spatial accelerator RTL.
#
# Run on server 23 from /home/hyyuan/workspace/qwen2_synth_fixed:
#   vivado -mode batch -source qwen2_standalone_synth_23.tcl

set part_name "xcvu9p-flga2104-2-i"
set top_name "Top"
set out_dir "vivado_qwen2_standalone_real"

file mkdir $out_dir

if {![file exists "Top.sv"]} {
  error "Top.sv not found in [pwd]"
}

if {![file exists "layers-Top-Verification.sv"]} {
  set stub_fh [open "layers-Top-Verification.sv" w]
  puts $stub_fh "`ifndef layers_Top_Verification"
  puts $stub_fh "  `define layers_Top_Verification"
  puts $stub_fh "`endif"
  close $stub_fh
  puts "Created synthesis stub include: layers-Top-Verification.sv"
}

create_project -in_memory -part $part_name
set_property target_language Verilog [current_project]

read_verilog -sv Top.sv
if {[file exists "constraints_debug.xdc"]} {
  read_xdc constraints_debug.xdc
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

report_utilization -hierarchical -hierarchical_depth 3 -file "$out_dir/qwen2_standalone_utilization_hier.rpt"
report_timing_summary -delay_type max -max_paths 50 -nworst 3 -report_unconstrained -file "$out_dir/qwen2_standalone_timing_summary.rpt"
report_drc -file "$out_dir/qwen2_standalone_drc.rpt"
write_checkpoint -force "$out_dir/qwen2_standalone_synth.dcp"

puts "Qwen2 standalone synthesis completed: $out_dir/qwen2_standalone_synth.dcp"
