if {$argc != 2} {
    error "usage: route_candidate_4head_recover.tcl <placed-dcp> <output-dir>"
}
set checkpoint [file normalize [lindex $argv 0]]
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
    set help_file [open [file join $output_dir route_design_help.txt] w]
    set route_help [help route_design -verbose]
    puts $help_file $route_help
    close $help_file
    if {[string first "MoreGlobalIterations" $route_help] < 0 ||
        [string first "-no_timing_driven" $route_help] < 0} {
        error "Required congestion recovery options absent from installed route_design help"
    }
    write_state $status_path RUNNING $stage $checkpoint
    open_checkpoint $checkpoint
    report_utilization -file [file join $output_dir utilization_source_placed.rpt]
    report_drc -file [file join $output_dir drc_source_placed.rpt]

    set stage ROUTE_DESIGN
    write_state $status_path RUNNING $stage "no_timing_driven from placed checkpoint"
    set route_result [catch {route_design -no_timing_driven} route_message route_options]
    report_utilization -file [file join $output_dir utilization_route_attempt.rpt]
    report_utilization -hierarchical -file [file join $output_dir utilization_hierarchical_route_attempt.rpt]
    report_route_status -file [file join $output_dir route_status_route_attempt.rpt]
    report_drc -file [file join $output_dir drc_route_attempt.rpt]
    report_timing_summary -delay_type min_max -report_unconstrained -file [file join $output_dir timing_route_attempt.rpt]
    if {$route_result != 0} {
        return -options $route_options $route_message
    }
    write_checkpoint -force [file join $output_dir candidate_4head_routed.dcp]
    write_state $status_path COMPLETE $stage "Route completed; inspect route status and DRC"
    close_design
} message options]
if {$result != 0} {
    write_state $status_path FAILED $stage $message
    catch {close_design}
    return -options $options $message
}
puts "ROUTE_CANDIDATE_4HEAD_RECOVERY_COMPLETE $output_dir"
