set candidate_root [file normalize [file dirname [info script]]]
set report_root [file join $candidate_root reports]
set part xcu280-fsvh2892-2L-e
set sources [list \
    [file join $candidate_root rtwsr_hbm_weight_ring_24lane.sv] \
    [file join $candidate_root rtwsr_hbm_weight_pool_adapter_24lane.sv]]

file mkdir $report_root
foreach source $sources {
    if {![file isfile $source]} {
        error "Missing candidate source: $source"
    }
}

create_project -in_memory -part $part
set_param general.maxThreads 2
set_property verilog_define {XILINX_XPM} [current_fileset]
add_files -norecurse $sources
set_property file_type SystemVerilog [get_files $sources]
update_compile_order -fileset sources_1
synth_design -mode out_of_context -top rtwsr_hbm_weight_pool_adapter_24lane \
    -part $part -flatten_hierarchy none
create_clock -name core_clk -period 4.444 [get_ports clk]
report_utilization -file [file join $report_root ring_adapter_utilization_synth.rpt]
report_utilization -hierarchical -file \
    [file join $report_root ring_adapter_utilization_hierarchical_synth.rpt]
report_timing_summary -file [file join $report_root ring_adapter_timing_synth.rpt]
close_design
puts "U280_HBM_RING_ADAPTER_OOC_SYNTH_COMPLETE"
