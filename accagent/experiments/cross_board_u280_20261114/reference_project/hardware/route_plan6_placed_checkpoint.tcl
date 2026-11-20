if {$argc != 2} {
    error "usage: route_plan6_placed_checkpoint.tcl <placed-checkpoint> <output-dir>"
}

set checkpoint [file normalize [lindex $argv 0]]
set output_dir [file normalize [lindex $argv 1]]
file mkdir $output_dir
set_param general.maxThreads 8

proc sha256_file {path} {
    return [lindex [exec sha256sum [file normalize $path]] 0]
}

open_checkpoint $checkpoint
route_design
write_checkpoint -force [file join $output_dir app_shell_9p_wrapper_routed.dcp]
report_utilization -file [file join $output_dir utilization_postroute.rpt]
report_utilization -hierarchical -file [file join $output_dir utilization_hierarchical_postroute.rpt]
report_timing_summary -delay_type min_max -report_unconstrained \
    -file [file join $output_dir timing_postroute.rpt]
report_clocks -file [file join $output_dir clocks_postroute.rpt]
report_route_status -file [file join $output_dir route_status_postroute.rpt]
report_drc -file [file join $output_dir drc_postroute.rpt]
report_power -file [file join $output_dir power_postroute.rpt]

set core_clocks {}
foreach clock [get_clocks] {
    set name [get_property NAME $clock]
    if {![string match -nocase "*rtwsr*" $name]} {
        continue
    }
    set period [get_property PERIOD $clock]
    set registers [all_registers -clock $clock]
    set paths [get_timing_paths -quiet -delay_type max -from $registers -to $registers -max_paths 1]
    if {[llength $paths] == 0} {
        lappend core_clocks "$name PERIOD_NS $period TIMING_PATHS 0"
    } else {
        set slack [get_property SLACK [lindex $paths 0]]
        set fmax [expr {1000.0 / ($period - $slack)}]
        lappend core_clocks "$name PERIOD_NS $period WNS_NS $slack FMAX_MHZ $fmax"
    }
}

set bitstream [file join $output_dir app_shell_9p_wrapper.bit]
write_bitstream -force $bitstream
set status [open [file join $output_dir route_status.txt] w]
puts $status "STATE ROUTED_FROM_PLACED_CHECKPOINT"
puts $status "SOURCE_CHECKPOINT $checkpoint"
puts $status "SOURCE_CHECKPOINT_SHA256 [sha256_file $checkpoint]"
puts $status "ROUTED_DCP_SHA256 [sha256_file [file join $output_dir app_shell_9p_wrapper_routed.dcp]]"
puts $status "BITSTREAM_PATH $bitstream"
puts $status "BITSTREAM_SHA256 [sha256_file $bitstream]"
puts $status "CORE_CLOCKS $core_clocks"
close $status
close_design
puts "PLAN6_ROUTE_FROM_PLACED_COMPLETE"
