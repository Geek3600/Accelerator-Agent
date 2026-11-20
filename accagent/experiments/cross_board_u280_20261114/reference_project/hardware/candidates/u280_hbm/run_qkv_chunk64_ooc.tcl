set run_root [file normalize [file dirname [info script]]]
set rtl_root [file join $run_root rtl]
set report_root [file join $run_root reports]
set part xcu280-fsvh2892-2L-e
file mkdir $report_root

proc sha256_file {path} {
    return [lindex [exec sha256sum [file normalize $path]] 0]
}

set sources [list rtwsr_qkv_head_buffer.sv rtwsr_qkv_head_buffer_banked.sv]
set source_paths {}
set manifest [open [file join $report_root inputs.sha256] w]
foreach source $sources {
    set source_path [file join $rtl_root $source]
    if {![file isfile $source_path]} {
        error "Missing QKV chunked source: $source_path"
    }
    puts $manifest "[sha256_file $source_path]  $source_path"
    lappend source_paths $source_path
}
close $manifest

create_project -in_memory -part $part
set_param general.maxThreads 4
set_property file_type SystemVerilog [add_files -norecurse $source_paths]
update_compile_order -fileset sources_1
synth_design -top rtwsr_qkv_head_buffer_banked -part $part \
    -generic {QUERY_SIZE=5280 KV_SIZE=5280 HEAD_DIM=96 WRITE_LANES=96 PARALLEL_READ_PORTS=8}
create_clock -name clk_core -period 4.444 [get_ports clk]
report_utilization -file [file join $report_root qkv_chunk64_utilization_synth.rpt]
report_utilization -hierarchical -file [file join $report_root qkv_chunk64_utilization_hierarchical_synth.rpt]
report_timing_summary -file [file join $report_root qkv_chunk64_timing_synth.rpt]
puts "PLAN6_U280_QKV_CHUNK64_OOC_COMPLETE"
