set run_root [file normalize [file dirname [info script]]]
set rtl_path [file join $run_root rtwsr_attention_gemv_unit_timing_candidate.sv]
set report_dir [file join $run_root reports]
set part xcvu9p_CIV-flgb2104-2-i
set core_period_ns 4.444
file mkdir $report_dir

proc record_state {state} {
    global report_dir
    set channel [open [file join $report_dir status.txt] w]
    puts $channel "STATE $state"
    puts $channel "DESIGN_SCOPE ATTENTION_HUGINN_HEAD96_LANES128_CONTEXT2048"
    close $channel
}

set manifest [open [file join $report_dir inputs.sha256] w]
foreach source_path [list $rtl_path [info script]] {
    puts $manifest [exec sha256sum [file normalize $source_path]]
}
close $manifest
set constraint_path [file join $report_dir core_clock.xdc]
set channel [open $constraint_path w]
puts $channel "create_clock -name clk_core -period $core_period_ns \[get_ports clk\]"
close $channel

set result [catch {
    create_project -in_memory -part $part
    set_param general.maxThreads 8
    read_verilog -sv $rtl_path
    read_xdc $constraint_path
    record_state SYNTHESIS_RUNNING
    synth_design -mode out_of_context -top rtwsr_attention_gemv_unit -part $part \
        -generic {HEAD_DIM=96 LANES=128 MAX_CONTEXT=2048 ATTN_SCALE_Q15=3344} \
        -control_set_opt_threshold 16
    report_utilization -file [file join $report_dir utilization_synth.rpt]
    report_timing_summary -delay_type min_max -file [file join $report_dir timing_synth.rpt]
    record_state IMPLEMENTATION_RUNNING
    opt_design
    place_design -directive Explore
    phys_opt_design -directive Explore
    route_design -directive Explore
    report_utilization -file [file join $report_dir utilization_postroute.rpt]
    report_timing_summary -delay_type min_max -file [file join $report_dir timing_postroute.rpt]
    report_route_status -file [file join $report_dir route_status_postroute.rpt]
    report_drc -file [file join $report_dir drc_postroute.rpt]
    record_state REPORTS_COMPLETE
    close_design
} error_text error_options]
if {$result != 0} {
    record_state FAILED
    return -options $error_options $error_text
}
