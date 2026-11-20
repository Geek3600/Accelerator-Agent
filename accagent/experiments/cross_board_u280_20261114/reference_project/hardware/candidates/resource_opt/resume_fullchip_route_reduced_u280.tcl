if {$argc != 2} {
    error "usage: resume_fullchip_route_reduced_u280.tcl <placed-checkpoint> <output-dir>"
}

set checkpoint [file normalize [lindex $argv 0]]
set output_dir [file normalize [lindex $argv 1]]
file mkdir $output_dir
set_param general.maxThreads 32
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

write_state $status_path RUNNING $stage "resume routing from saved full-shell placed checkpoint"
set result [catch {
    open_checkpoint $checkpoint
    set stage ROUTE_DESIGN
    write_state $status_path RUNNING $stage "route_design -no_timing_driven -ultrathreads"
    route_design -no_timing_driven -ultrathreads

    set stage POST_ROUTE_REPORTS
    write_checkpoint -force [file join $output_dir full_shell_routed.dcp]
    report_utilization -file [file join $output_dir utilization_postroute.rpt]
    report_utilization -hierarchical -file [file join $output_dir utilization_hierarchical_postroute.rpt]
    report_timing_summary -delay_type min_max -report_unconstrained \
        -file [file join $output_dir timing_postroute.rpt]
    report_route_status -file [file join $output_dir route_status_postroute.rpt]
    report_drc -file [file join $output_dir drc_postroute.rpt]
    report_power -file [file join $output_dir power_postroute.rpt]
    write_state $status_path COMPLETE $stage "route and post-route reports generated"
    close_design
} message options]

if {$result != 0} {
    write_state $status_path FAILED $stage $message
    catch {close_design}
    return -options $options $message
}

puts "FULLCHIP_ROUTE_REDUCED_U280_RESUME_COMPLETE $output_dir"
