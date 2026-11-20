if {$argc != 2} {
    error "usage: report_plan6_control_sets.tcl <opt-checkpoint> <report>"
}

set checkpoint [file normalize [lindex $argv 0]]
set report_path [file normalize [lindex $argv 1]]
file mkdir [file dirname $report_path]
set_param general.maxThreads 8
open_checkpoint $checkpoint
report_control_sets -file $report_path
set hierarchy_path "${report_path}.hierarchical"
report_control_sets -hierarchical -file $hierarchy_path
set suggestions_path "${report_path}.qor_suggestions"
report_qor_suggestions -file $suggestions_path
close_design
puts "PLAN6_CONTROL_SET_REPORT_COMPLETE $report_path"
