if {$argc != 2} {
    error "usage: opt_plan6_control_sets.tcl <opt-checkpoint> <output-dir>"
}

set checkpoint [file normalize [lindex $argv 0]]
set output_dir [file normalize [lindex $argv 1]]
file mkdir $output_dir
set_param general.maxThreads 8
open_checkpoint $checkpoint
opt_design -control_set_merge -merge_equivalent_drivers
write_checkpoint -force [file join $output_dir app_shell_9p_wrapper_control_merge.dcp]
report_control_sets -file [file join $output_dir control_sets.rpt]
report_utilization -hierarchical -file [file join $output_dir utilization_hierarchical.rpt]
report_timing_summary -delay_type min_max -report_unconstrained \
    -file [file join $output_dir timing.rpt]
report_qor_suggestions -file [file join $output_dir qor_suggestions.rpt]
close_design
puts "PLAN6_CONTROL_SET_OPT_COMPLETE $output_dir"
