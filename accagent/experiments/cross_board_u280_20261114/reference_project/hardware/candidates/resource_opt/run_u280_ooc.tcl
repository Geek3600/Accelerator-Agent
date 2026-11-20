set run_root [file normalize [file dirname [info script]]]
set rtl_root [file join $run_root rtl]
set report_root [file join $run_root reports]
set part xcu280-fsvh2892-2L-e
file mkdir $report_root

proc sha256_file {path} {
    return [lindex [exec sha256sum [file normalize $path]] 0]
}

set sources [list \
    radix3_5trit_decoder.sv \
    scale_hoisted_ternary_lane.sv \
    usw512_word_decoder.sv \
    usw512_dual_track_channel.sv \
    usw512_channel_array.sv \
    rtwsr_dual_track_gemv_array.sv]

set manifest [open [file join $report_root inputs.sha256] w]
set source_paths {}
foreach source $sources {
    set source_path [file join $rtl_root $source]
    if {![file isfile $source_path]} {
        error "Missing resource optimization source: $source_path"
    }
    puts $manifest "[sha256_file $source_path]  $source_path"
    lappend source_paths $source_path
}
close $manifest

create_project -in_memory -part $part
set_param general.maxThreads 4
set_property verilog_define {SYNTH_CARRY8 XILINX_XPM} [current_fileset]
add_files -norecurse $source_paths
set_property file_type SystemVerilog [get_files $source_paths]
update_compile_order -fileset sources_1
synth_design -top rtwsr_dual_track_gemv_array -part $part \
    -generic {SLR_COUNT=3 CHANNELS_PER_SLR=64 TRITS_PER_CYCLE=128 ACT_W=8 ACC_W=24 STATIC_REUSE=0}
create_clock -name clk_core -period 5.000 [get_ports clk]
report_utilization -file [file join $report_root utilization_synth.rpt]
report_utilization -hierarchical -file [file join $report_root utilization_hierarchical_synth.rpt]
close_design
puts "RESOURCE_OPT_U280_GEMV192_OOC_SYNTH_COMPLETE"
