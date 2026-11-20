set_param general.maxThreads 2

set root /tmp/loopquant-plan5-ooc
set source_dir [file join $root hardware]
set run_dir [file join $root vu9p_retimed_5ns]
file mkdir $run_dir

create_project -force -in_memory loopquant_ooc -part xcvu9p-flga2104-2L-e
add_files -norecurse [glob -directory $source_dir *.sv]
set_property file_type SystemVerilog [get_files *.sv]
set_property verilog_define {SYNTH_CARRY8} [current_fileset]
update_compile_order -fileset sources_1

synth_design -top usw512_channel_array \
    -part xcvu9p-flga2104-2L-e \
    -mode out_of_context \
    -flatten_hierarchy rebuilt

create_clock -name core_clk -period 5.000 [get_ports clk]
opt_design
place_design
phys_opt_design
route_design

report_utilization -file [file join $run_dir utilization.rpt]
report_timing_summary -file [file join $run_dir timing.rpt]
report_power -file [file join $run_dir power.rpt]
