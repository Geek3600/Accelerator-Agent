if {$argc != 2} { error "usage: place_route_candidate_4head_sll.tcl <opt-dcp> <output-dir>" }
set source_dcp [file normalize [lindex $argv 0]]
set output_dir [file normalize [lindex $argv 1]]
file mkdir $output_dir
set_param general.maxThreads 8
set status_path [file join $output_dir implementation_status.txt]
set stage OPEN_CHECKPOINT
proc write_state {path state stage message} {
    set fh [open $path w]
    puts $fh "STATE $state"
    puts $fh "STAGE $stage"
    puts $fh "MESSAGE $message"
    puts $fh "UTC [clock format [clock seconds] -format {%Y-%m-%dT%H:%M:%SZ} -gmt 1]"
    close $fh
}
set result [catch {
    open_checkpoint $source_dcp
    set stage PLACE_DESIGN
    write_state $status_path RUNNING $stage "SSI_SpreadSLLs from optimized checkpoint"
    place_design -directive SSI_SpreadSLLs
    write_checkpoint -force [file join $output_dir candidate_4head_sll_placed.dcp]
    report_utilization -file [file join $output_dir utilization_placed.rpt]
    report_utilization -hierarchical -file [file join $output_dir utilization_hierarchical_placed.rpt]
    report_timing_summary -delay_type min_max -report_unconstrained -file [file join $output_dir timing_placed.rpt]
    set stage PHYS_OPT_DESIGN
    write_state $status_path RUNNING $stage "Explore from SSI_SpreadSLLs placement"
    phys_opt_design -directive Explore
    write_checkpoint -force [file join $output_dir candidate_4head_sll_physopt.dcp]
    report_utilization -file [file join $output_dir utilization_physopt.rpt]
    report_timing_summary -delay_type min_max -report_unconstrained -file [file join $output_dir timing_physopt.rpt]
    set stage ROUTE_DESIGN
    write_state $status_path RUNNING $stage "Explore route from SSI_SpreadSLLs placement"
    set route_result [catch {route_design -directive Explore} route_message route_options]
    report_utilization -file [file join $output_dir utilization_route_attempt.rpt]
    report_utilization -hierarchical -file [file join $output_dir utilization_hierarchical_route_attempt.rpt]
    report_route_status -file [file join $output_dir route_status_route_attempt.rpt]
    report_drc -file [file join $output_dir drc_route_attempt.rpt]
    report_timing_summary -delay_type min_max -report_unconstrained -file [file join $output_dir timing_route_attempt.rpt]
    if {$route_result != 0} { return -options $route_options $route_message }
    write_checkpoint -force [file join $output_dir candidate_4head_sll_routed.dcp]
    write_state $status_path COMPLETE $stage "route and reports completed"
    close_design
} message options]
if {$result != 0} {
    write_state $status_path FAILED $stage $message
    catch {close_design}
    return -options $options $message
}
puts "PLACE_ROUTE_CANDIDATE_4HEAD_SLL_COMPLETE $output_dir"
