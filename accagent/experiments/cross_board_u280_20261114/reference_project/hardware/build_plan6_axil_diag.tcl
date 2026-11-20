if {$argc != 3} {
    error "usage: build_plan6_axil_diag.tcl <routed-checkpoint> <probe-rtl> <output-dir>"
}

set routed_checkpoint [file normalize [lindex $argv 0]]
set probe_rtl [file normalize [lindex $argv 1]]
set output_dir [file normalize [lindex $argv 2]]
set part_name xcvu9p_CIV-flgb2104-2-i
set probe_checkpoint [file join $output_dir rtwsr_axil_diag_ooc.dcp]
set bitstream [file join $output_dir plan6_axil_diag.bit]

file mkdir $output_dir
foreach path [list $routed_checkpoint $probe_rtl] {
    if {![file isfile $path]} { error "Required input is missing: $path" }
}

set_param general.maxThreads 8
create_project -in_memory -part $part_name
read_verilog -sv $probe_rtl
synth_design -top rtwsr_plan6_huginn_9p_axi_bd -part $part_name \
    -mode out_of_context -flatten_hierarchy none
report_utilization -file [file join $output_dir probe_utilization.rpt]
write_checkpoint -force $probe_checkpoint
close_design

open_checkpoint $routed_checkpoint
set endpoint_name app_shell_9p_i/rtwsr_9p_axi_0
set endpoint [get_cells -hier -quiet -filter "NAME == $endpoint_name"]
if {[llength $endpoint] != 1} {
    error "Expected one routed accelerator endpoint, found [llength $endpoint]"
}
puts "DIAG_ENDPOINT [get_property NAME $endpoint] [get_property REF_NAME $endpoint]"

update_design -cell $endpoint_name -black_box
set endpoint [get_cells -hier -quiet -filter "NAME == $endpoint_name"]
foreach pin [get_pins -quiet -of_objects $endpoint] {
    puts "DIAG_PIN [get_property NAME $pin] DIRECTION [get_property DIRECTION $pin] WIDTH [get_property WIDTH $pin]"
}
read_checkpoint -cell $endpoint_name $probe_checkpoint
report_utilization -file [file join $output_dir shell_utilization_after_swap.rpt]
opt_design
place_design
route_design -directive AlternateCLBRouting
report_route_status -file [file join $output_dir route_status.rpt]
report_timing_summary -delay_type min_max -report_unconstrained \
    -file [file join $output_dir timing.rpt]
report_drc -file [file join $output_dir drc.rpt]
write_bitstream -force $bitstream

set channel [open [file join $output_dir inputs.sha256] w]
foreach path [list $routed_checkpoint $probe_rtl $probe_checkpoint $bitstream] {
    puts $channel "[lindex [exec sha256sum $path] 0]  $path"
}
close $channel
puts "DIAG_BITSTREAM $bitstream [lindex [exec sha256sum $bitstream] 0]"
close_design
