set_param general.maxThreads 2

set root /tmp/loopquant-plan5-clockopt
set source_dir [file join $root hardware]
set run_dir [file join $root vu9p_array_4p75ns]
file mkdir $run_dir

create_project -force -in_memory loopquant_clockopt -part xcvu9p_CIV-flgb2104-2-i
add_files -norecurse [glob -directory $source_dir *.sv]
set_property file_type SystemVerilog [get_files *.sv]
set_property verilog_define {SYNTH_CARRY8} [current_fileset]
update_compile_order -fileset sources_1

synth_design -top usw512_channel_array \
    -part xcvu9p_CIV-flgb2104-2-i \
    -mode out_of_context \
    -flatten_hierarchy rebuilt

create_clock -name rtwsr_core_clk -period 4.750 [get_ports clk]
opt_design
place_design
phys_opt_design -directive AggressiveFanoutOpt
route_design

report_utilization -file [file join $run_dir utilization.rpt]
report_timing_summary -file [file join $run_dir timing_summary.rpt]
report_timing -delay_type max -max_paths 20 -path_type full_clock_expanded \
    -file [file join $run_dir timing_paths.rpt]
report_power -file [file join $run_dir power.rpt]
