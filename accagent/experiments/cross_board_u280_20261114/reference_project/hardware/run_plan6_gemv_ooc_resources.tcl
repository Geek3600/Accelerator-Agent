set run_root [file normalize [file dirname [info script]]]
set rtl_root [file join $run_root rtl]
set report_root [file join $run_root reports]
set part xcvu9p_CIV-flgb2104-2-i
file mkdir $report_root

proc sha256_file {path} {
    return [lindex [exec sha256sum [file normalize $path]] 0]
}

set sources [list \
    rtwsr_runtime_tile_gemv.sv \
    rtwsr_dual_track_gemv_array.sv \
    usw512_channel_array.sv \
    usw512_dual_track_channel.sv \
    usw512_word_decoder.sv \
    radix3_5trit_decoder.sv \
    scale_hoisted_ternary_lane.sv]

set manifest [open [file join $report_root inputs.sha256] w]
set source_paths {}
foreach source $sources {
    set source_path [file join $rtl_root $source]
    if {![file isfile $source_path]} {
        error "Missing Plan 6 GEMV source: $source_path"
    }
    puts $manifest "[sha256_file $source_path]  $source_path"
    lappend source_paths $source_path
}
close $manifest

create_project -in_memory -part $part
set_param general.maxThreads 8
set_property verilog_define SYNTH_CARRY8 [current_fileset]
read_verilog -sv $source_paths
synth_design -top rtwsr_runtime_tile_gemv -part $part
report_utilization -file [file join $report_root gemv_utilization_synth.rpt]
report_utilization -hierarchical -file \
    [file join $report_root gemv_utilization_hierarchical_synth.rpt]
close_design
puts "PLAN6_GEMV_OOC_SYNTH_COMPLETE"
