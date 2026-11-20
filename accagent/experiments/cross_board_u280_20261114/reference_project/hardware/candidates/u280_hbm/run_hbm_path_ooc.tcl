set run_root [file normalize [file dirname [info script]]]
set report_root [file join $run_root reports]
set part xcu280-fsvh2892-2L-e
file mkdir $report_root
create_project -in_memory -part $part
set_param general.maxThreads 4
set_property verilog_define {XILINX_XPM} [current_fileset]
set sources {}
foreach source {
    rtwsr_huginn_u280_hbm_descriptor.sv
    rtwsr_hbm_read_dma_27pc.sv
    rtwsr_hbm_gearbox_27lane.sv
    rtwsr_hbm_weight_pool_adapter_27to24.sv
    rtwsr_plan6_huginn_u280_hbm_weight_path.sv
} {
    lappend sources [file join $run_root $source]
}
add_files -norecurse $sources
set_property file_type SystemVerilog [get_files $sources]
update_compile_order -fileset sources_1
synth_design -top rtwsr_plan6_huginn_u280_hbm_weight_path -part $part \
    -generic {HBM_PCS=32 POOL_LANES=32 RING_RECORDS=147456 MAX_OUTSTANDING=16 ADAPTER_STATIC_REUSE=1}
create_clock -name core_clk -period 4.444 [get_ports core_clk]
create_clock -name hbm_clk -period 2.222 [get_ports axi_clk]
report_utilization -file [file join $report_root hbm_path_utilization_synth.rpt]
report_utilization -hierarchical -file [file join $report_root hbm_path_hierarchical_synth.rpt]
close_project
puts "HBM_PATH_OOC_COMPLETE"
