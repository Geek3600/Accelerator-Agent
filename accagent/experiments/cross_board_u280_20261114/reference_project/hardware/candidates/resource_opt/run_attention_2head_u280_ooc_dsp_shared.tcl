set run_root [file normalize [file dirname [info script]]]
set report_root [file join $run_root reports_attention_2head_dsp_shared]
set part xcu280-fsvh2892-2L-e
file mkdir $report_root

proc sha256_file {path} {
    return [lindex [exec sha256sum [file normalize $path]] 0]
}

set sources [list \
    [file join $run_root rtwsr_attention_gemv_unit_dsp_shared.sv] \
    [file join $run_root rtwsr_attention_2head_ooc_top.sv]]
set manifest [open [file join $report_root inputs.sha256] w]
foreach source $sources {
    if {![file isfile $source]} {
        error "Missing Attention OOC source: $source"
    }
    puts $manifest "[sha256_file $source]  $source"
}
close $manifest

create_project -in_memory -part $part
set_param general.maxThreads 4
set_property verilog_define {SYNTH_CARRY8 XILINX_XPM} [current_fileset]
add_files -norecurse $sources
set_property file_type SystemVerilog [get_files $sources]
update_compile_order -fileset sources_1
synth_design -top rtwsr_attention_2head_ooc_top -part $part -flatten_hierarchy none
create_clock -name clk_core -period 5.000 [get_ports clk]
report_utilization -file [file join $report_root utilization_synth.rpt]
report_utilization -hierarchical -file [file join $report_root utilization_hierarchical_synth.rpt]
report_timing_summary -file [file join $report_root timing_synth.rpt]
close_design
puts "RESOURCE_OPT_U280_ATTENTION_2HEAD_DSP_SHARED_OOC_COMPLETE"
