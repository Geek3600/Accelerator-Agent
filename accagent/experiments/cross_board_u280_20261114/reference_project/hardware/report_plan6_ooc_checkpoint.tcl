if {$argc != 2} {
    error "usage: vivado -mode batch -source report_plan6_ooc_checkpoint.tcl -tclargs <checkpoint> <report_dir>"
}
set checkpoint [file normalize [lindex $argv 0]]
set report_dir [file normalize [lindex $argv 1]]
file mkdir $report_dir
open_checkpoint $checkpoint
report_utilization -file [file join $report_dir checkpoint_utilization_synth.rpt]
report_utilization -hierarchical -file [file join $report_dir checkpoint_utilization_hierarchical_synth.rpt]
report_timing_summary -delay_type min_max -report_unconstrained -file [file join $report_dir checkpoint_timing_synth.rpt]
close_design
