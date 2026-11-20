if {$argc != 2} {
    error "usage: place_route_plan6_control_merge.tcl <checkpoint> <output-dir>"
}

set checkpoint [file normalize [lindex $argv 0]]
set output_dir [file normalize [lindex $argv 1]]
file mkdir $output_dir
set_param general.maxThreads 8
set status_path [file join $output_dir implementation_status.txt]
set stage OPEN_CHECKPOINT

proc sha256_file {path} {
    return [lindex [exec sha256sum [file normalize $path]] 0]
}

set result [catch {
    open_checkpoint $checkpoint

    set stage PLACE_DESIGN
    place_design -directive SSI_SpreadLogic_high
    set placed_checkpoint [file join $output_dir app_shell_9p_wrapper_placed.dcp]
    write_checkpoint -force $placed_checkpoint
    report_control_sets -file [file join $output_dir control_sets_placed.rpt]
    report_utilization -file [file join $output_dir utilization_placed.rpt]
    report_timing_summary -delay_type min_max -report_unconstrained \
        -file [file join $output_dir timing_placed.rpt]

    set stage PHYS_OPT_DESIGN
    phys_opt_design -directive AggressiveFanoutOpt
    write_checkpoint -force [file join $output_dir app_shell_9p_wrapper_physopt.dcp]

    set stage ROUTE_DESIGN
    route_design -directive Explore
    set routed_checkpoint [file join $output_dir app_shell_9p_wrapper_routed.dcp]
    write_checkpoint -force $routed_checkpoint
    report_utilization -file [file join $output_dir utilization_postroute.rpt]
    report_utilization -hierarchical -file \
        [file join $output_dir utilization_hierarchical_postroute.rpt]
    report_timing_summary -delay_type min_max -report_unconstrained \
        -file [file join $output_dir timing_postroute.rpt]
    report_clocks -file [file join $output_dir clocks_postroute.rpt]
    report_route_status -file [file join $output_dir route_status_postroute.rpt]
    report_drc -file [file join $output_dir drc_postroute.rpt]
    report_power -file [file join $output_dir power_postroute.rpt]

    set stage WRITE_BITSTREAM
    set bitstream [file join $output_dir app_shell_9p_wrapper.bit]
    write_bitstream -force $bitstream

    set core_clocks {}
    foreach clock [get_clocks] {
        set name [get_property NAME $clock]
        if {![string match -nocase "*rtwsr*" $name]} {
            continue
        }
        set period [get_property PERIOD $clock]
        set registers [all_registers -clock $clock]
        set paths [get_timing_paths -quiet -delay_type max -from $registers \
            -to $registers -max_paths 1]
        if {[llength $paths] == 0} {
            lappend core_clocks "$name PERIOD_NS $period TIMING_PATHS 0"
        } else {
            set slack [get_property SLACK [lindex $paths 0]]
            set fmax [expr {1000.0 / ($period - $slack)}]
            lappend core_clocks "$name PERIOD_NS $period WNS_NS $slack FMAX_MHZ $fmax"
        }
    }

    set status [open $status_path w]
    puts $status "STATE ROUTED"
    puts $status "SOURCE_CHECKPOINT $checkpoint"
    puts $status "SOURCE_CHECKPOINT_SHA256 [sha256_file $checkpoint]"
    puts $status "PLACED_CHECKPOINT_SHA256 [sha256_file $placed_checkpoint]"
    puts $status "ROUTED_CHECKPOINT_SHA256 [sha256_file $routed_checkpoint]"
    puts $status "BITSTREAM_PATH $bitstream"
    puts $status "BITSTREAM_SHA256 [sha256_file $bitstream]"
    puts $status "CORE_CLOCKS $core_clocks"
    close $status
    close_design
} message options]

if {$result} {
    set status [open $status_path w]
    puts $status "STATE FAILED"
    puts $status "FAILED_STAGE $stage"
    puts $status "MESSAGE $message"
    close $status
    catch {close_design}
    puts stderr $message
    exit 1
}

puts "PLAN6_CONTROL_MERGE_IMPLEMENTATION_COMPLETE $output_dir"
