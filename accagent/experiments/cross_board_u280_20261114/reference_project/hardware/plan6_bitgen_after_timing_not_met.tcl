set project_dir "/home/hyyuan/workspace/rtwsr_plan6_huginn_vu9p_direct_20261026"
set report_dir [file join $project_dir plan6_reports_attn_qkv_100mhz]
set status_path [file join $report_dir huginn_vu9p_shell_status.txt]
set source_manifest [file join $project_dir source_inputs.sha256]
set shell_manifest [file join /home/hyyuan/workspace/rtwsr_plan6_huginn_vu9p_shell_20261025_ctrl_d plan6_reports_ctrl_d_full shell_inputs.sha256]
set clone_manifest [file join $report_dir writable_shell_inputs.sha256]
set implementation_manifest [file join $report_dir implementation_inputs.sha256]
set expected_source_sha "899bbb48b2393cef695f15c2b0e16265254316926e928e73a8b801872c2a8558"
set expected_shell_sha "25dfadd6d2918db51387a5fd328b5635a41bcfa5700f87d94db94602c61c2bdc"
set expected_implementation_sha "93577122d99d4db86f76b39d902c8f484df25117a8e5813c10c2aa4f4574badb"

proc sha256_file {path} {
    return [lindex [exec sha256sum [file normalize $path]] 0]
}

set status_channel [open $status_path r]
set status_text [read $status_channel]
close $status_channel
set status [dict create]
foreach line [split $status_text "\n"] {
    if {[regexp {^(\S+)\s+(.+)$} $line -> key value]} {
        dict set status $key $value
    }
}
if {[dict get $status STATE] ne "CORE_TIMING_NOT_MET"} {
    error "Expected the direct100 run to record CORE_TIMING_NOT_MET"
}
if {[dict get $status PROJECT_DIR] ne $project_dir ||
    [dict get $status INPUT_MANIFEST_SHA256] ne $expected_source_sha ||
    [dict get $status IMPLEMENTATION_INPUTS_SHA256] ne $expected_implementation_sha} {
    error "The routed implementation identity does not match direct100"
}
if {[sha256_file $source_manifest] ne $expected_source_sha ||
    [sha256_file $shell_manifest] ne $expected_shell_sha ||
    [sha256_file $implementation_manifest] ne $expected_implementation_sha} {
    error "A source or implementation manifest changed before bitstream generation"
}
exec sha256sum -c --status $source_manifest
exec sha256sum -c --status $shell_manifest
exec sha256sum -c --status $clone_manifest
exec sha256sum -c --status $implementation_manifest

set routed_checkpoint [dict get $status ROUTED_CHECKPOINT_PATH]
if {[sha256_file $routed_checkpoint] ne [dict get $status ROUTED_CHECKPOINT_SHA256]} {
    error "The routed checkpoint hash does not match the implementation status"
}
set timing_report [file join $report_dir timing_postroute.rpt]
set route_report [file join $report_dir route_status_postroute.rpt]
set drc_report [file join $report_dir drc_postroute.rpt]
foreach path [list $timing_report $route_report $drc_report \
                   [file join $report_dir utilization_postroute.rpt] \
                   [file join $report_dir utilization_hierarchical_postroute.rpt] \
                   [file join $report_dir clocks_postroute.rpt] \
                   [file join $report_dir power_postroute.rpt]] {
    if {![file exists $path]} { error "A required Post-Route report is missing: $path" }
}
set channel [open $route_report r]
set route_text [read $channel]
close $channel
if {![regexp {# of routable nets\.+\s*:\s*([0-9]+)} $route_text -> routable] ||
    ![regexp {# of fully routed nets\.+\s*:\s*([0-9]+)} $route_text -> routed] ||
    ![regexp {# of nets with routing errors\.+\s*:\s*([0-9]+)} $route_text -> route_errors] ||
    $routable == 0 || $routable != $routed || $route_errors != 0} {
    error "The Post-Route report does not show a fully routed netlist"
}
set channel [open $drc_report r]
set drc_text [read $channel]
close $channel
if {[string first "Design State : Fully Routed" $drc_text] < 0 ||
    [regexp {\|\s*Error\s*\|} $drc_text]} {
    error "The Post-Route DRC report is not eligible for bitstream generation"
}

set timing_channel [open $timing_report r]
set timing_text [read $timing_channel]
close $timing_channel
if {[string first "Timing constraints are not met." $timing_text] < 0} {
    error "The timing report does not confirm the recorded timing failure"
}
open_checkpoint $routed_checkpoint
set bitstream [file join $report_dir app_shell_9p_wrapper.bit]
write_bitstream -force $bitstream
exec sha256sum -c --status $source_manifest
exec sha256sum -c --status $shell_manifest
exec sha256sum -c --status $clone_manifest
exec sha256sum -c --status $implementation_manifest

dict set status STATE CORE_TIMING_NOT_MET_BITSTREAM_READY
dict set status UTILIZATION_POSTROUTE_SHA256 [sha256_file [file join $report_dir utilization_postroute.rpt]]
dict set status HIERARCHY_POSTROUTE_SHA256 [sha256_file [file join $report_dir utilization_hierarchical_postroute.rpt]]
dict set status TIMING_POSTROUTE_SHA256 [sha256_file $timing_report]
dict set status CLOCKS_POSTROUTE_SHA256 [sha256_file [file join $report_dir clocks_postroute.rpt]]
dict set status ROUTE_STATUS_SHA256 [sha256_file $route_report]
dict set status DRC_SHA256 [sha256_file $drc_report]
dict set status POWER_SHA256 [sha256_file [file join $report_dir power_postroute.rpt]]
dict set status BITSTREAM_PATH $bitstream
dict set status BITSTREAM_SHA256 [sha256_file $bitstream]
set status_channel [open "${status_path}.pending" w]
dict for {key value} $status { puts $status_channel "$key $value" }
close $status_channel
file rename -force "${status_path}.pending" $status_path
puts "PLAN6_TIMING_NOT_MET_BITSTREAM_READY $bitstream [sha256_file $bitstream]"
close_project
