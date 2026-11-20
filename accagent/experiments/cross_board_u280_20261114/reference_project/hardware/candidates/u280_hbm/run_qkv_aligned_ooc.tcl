set run_root [file normalize [file dirname [info script]]]
set part xcu280-fsvh2892-2L-e
set report_root [file join $run_root reports]
file mkdir $report_root

foreach variant {baseline aligned} {
    create_project -in_memory -part $part
    set_param general.maxThreads 4
    read_verilog -sv [file join $run_root ${variant}.sv]
    synth_design -top rtwsr_qkv_head_buffer -part $part \
        -generic {QUERY_SIZE=5280 KV_SIZE=5280 HEAD_DIM=96 PARALLEL_READ_PORTS=8}
    create_clock -name clk_core -period 4.444 [get_ports clk]
    report_utilization -file [file join $report_root ${variant}_utilization_synth.rpt]
    close_project
}
puts "QKV_ALIGNED_OOC_COMPLETE"
