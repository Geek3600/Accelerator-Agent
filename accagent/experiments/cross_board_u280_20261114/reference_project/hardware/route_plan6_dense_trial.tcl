if {$argc != 3} {
    error "usage: route_plan6_dense_trial.tcl <checkpoint> <output-dir> <directive>"
}

set checkpoint [file normalize [lindex $argv 0]]
set output_dir [file normalize [lindex $argv 1]]
set directive [lindex $argv 2]
if {$directive ne "AlternateCLBRouting"} {
    error "Fixplan dense-route trial requires directive AlternateCLBRouting"
}
file mkdir $output_dir
set_param general.maxThreads 8

proc sha256_file {path} {
    return [lindex [exec sha256sum [file normalize $path]] 0]
}

set result [catch {
    open_checkpoint $checkpoint
    route_design -directive $directive
    write_checkpoint -force [file join $output_dir app_shell_9p_wrapper_routed.dcp]
    report_utilization -file [file join $output_dir utilization_postroute.rpt]
    report_utilization -hierarchical -file [file join $output_dir utilization_hierarchical_postroute.rpt]
    report_timing_summary -delay_type min_max -report_unconstrained \
        -file [file join $output_dir timing_postroute.rpt]
    report_clocks -file [file join $output_dir clocks_postroute.rpt]
    report_route_status -file [file join $output_dir route_status_postroute.rpt]
    report_drc -file [file join $output_dir drc_postroute.rpt]
    report_power -file [file join $output_dir power_postroute.rpt]
    set status_file [open [file join $output_dir route_trial_status.txt] w]
    puts $status_file "STATE ROUTED_TRIAL_REPORTS_GENERATED"
    puts $status_file "SOURCE_CHECKPOINT $checkpoint"
    puts $status_file "SOURCE_CHECKPOINT_SHA256 [sha256_file $checkpoint]"
    puts $status_file "DIRECTIVE $directive"
    puts $status_file "ROUTED_CHECKPOINT_SHA256 [sha256_file [file join $output_dir app_shell_9p_wrapper_routed.dcp]]"
    close $status_file
    close_design
} message options]

if {$result != 0} {
    set status_file [open [file join $output_dir route_trial_status.txt] w]
    puts $status_file "STATE ROUTE_TRIAL_FAILED"
    puts $status_file "SOURCE_CHECKPOINT $checkpoint"
    puts $status_file "SOURCE_CHECKPOINT_SHA256 [sha256_file $checkpoint]"
    puts $status_file "DIRECTIVE $directive"
    puts $status_file "ERROR $message"
    close $status_file
    catch {close_design}
    return -options $options $message
}

puts "PLAN6_DENSE_ROUTE_TRIAL_REPORTS_GENERATED"
