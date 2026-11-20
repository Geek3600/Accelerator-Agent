set run_root [file normalize [file dirname [info script]]]
set rtl_path [file join $run_root rtwsr_qkv_head_buffer_timing_candidate.sv]
set report_dir [file join $run_root reports]
set part xcvu9p_CIV-flgb2104-2-i
file mkdir $report_dir

proc record_state {state args} {
    global report_dir
    set channel [open [file join $report_dir status.txt] w]
    puts $channel "STATE $state"
    puts $channel "DESIGN_SCOPE QKV_HUGINN_QUERY5280_KV5280_HEAD96"
    foreach {key value} $args { puts $channel "$key $value" }
    close $channel
}

set manifest [open [file join $report_dir inputs.sha256] w]
foreach source_path [list $rtl_path [info script]] {
    puts $manifest [exec sha256sum [file normalize $source_path]]
}
close $manifest

set result [catch {
    create_project -in_memory -part $part
    set_param general.maxThreads 8
    read_verilog -sv $rtl_path
    record_state SYNTHESIS_RUNNING
    synth_design -mode out_of_context -top rtwsr_qkv_head_buffer -part $part \
        -generic {QUERY_SIZE=5280 KV_SIZE=5280 HEAD_DIM=96} -control_set_opt_threshold 16
    report_utilization -file [file join $report_dir utilization_synth.rpt]
    set checkpoint [file join $report_dir rtwsr_qkv_head_buffer_synth.dcp]
    write_checkpoint -force $checkpoint
    create_clock -name plan6_qkv_ooc_clk -period 10.0 [get_ports clk]
    report_timing_summary -delay_type min_max -file [file join $report_dir timing_synth.rpt]
    record_state IMPLEMENTATION_RUNNING CHECKPOINT_PATH $checkpoint \
        CHECKPOINT_SHA256 [lindex [exec sha256sum $checkpoint] 0]
    opt_design
    place_design -directive Explore
    phys_opt_design -directive Explore
    route_design -directive Explore
    report_utilization -file [file join $report_dir utilization_postroute.rpt]
    report_timing_summary -delay_type min_max -file [file join $report_dir timing_postroute.rpt]
    report_route_status -file [file join $report_dir route_status_postroute.rpt]
    report_drc -file [file join $report_dir drc_postroute.rpt]
    record_state REPORTS_COMPLETE CHECKPOINT_PATH $checkpoint \
        CHECKPOINT_SHA256 [lindex [exec sha256sum $checkpoint] 0]
    close_design
} error_text error_options]
if {$result != 0} {
    record_state FAILED OPERATION_RESULT $error_text
    return -options $error_options $error_text
}
