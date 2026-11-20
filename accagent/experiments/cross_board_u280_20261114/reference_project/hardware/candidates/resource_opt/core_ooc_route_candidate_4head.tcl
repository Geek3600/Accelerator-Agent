if {$argc != 2} {
    error "usage: core_ooc_route_candidate_4head.tcl <snapshot-root> <output-dir>"
}

set snapshot_root [file normalize [lindex $argv 0]]
set output_dir [file normalize [lindex $argv 1]]
set hw_root [file join $snapshot_root hardware]
set rtl_root $hw_root
set part xcu280-fsvh2892-2L-e
file mkdir $output_dir
set_param general.maxThreads 8
set status_path [file join $output_dir implementation_status.txt]
set stage PREFLIGHT

proc sha256_file {path} {
    return [lindex [exec sha256sum [file normalize $path]] 0]
}
proc write_state {path state stage message} {
    set fh [open $path w]
    puts $fh "STATE $state"
    puts $fh "STAGE $stage"
    puts $fh "MESSAGE $message"
    puts $fh "UTC [clock format [clock seconds] -format {%Y-%m-%dT%H:%M:%SZ} -gmt 1]"
    close $fh
}

set source_names [list \
    rtwsr_transformer_top.sv \
    rtwsr_linear_command_dispatch.sv \
    rtwsr_linear_tile_controller.sv \
    rtwsr_recurrent_command_scheduler.sv \
    rtwsr_recurrent_sequencer.sv \
    rtwsr_recurrent_attention_bridge.sv \
    rtwsr_recurrent_attention_bridge4.sv \
    rtwsr_qkv_head_buffer.sv \
    rtwsr_qkv_head_buffer_banked.sv \
    rtwsr_runtime_tile_gemv.sv \
    rtwsr_adapter_static_cache.sv \
    rtwsr_runtime_gamma_pool.sv \
    rtwsr_dual_track_gemv_array.sv \
    rtwsr_runtime_weight_subsystem.sv \
    rtwsr_runtime_weight_pool.sv \
    rtwsr_runtime_weight_ring.sv \
    uram_active_pool_bank.sv \
    radix3_5trit_decoder.sv \
    scale_hoisted_ternary_lane.sv \
    usw512_word_decoder.sv \
    usw512_dual_track_channel.sv \
    usw512_channel_array.sv \
    rtwsr_rope_kv_cache.sv \
    rtwsr_attention_gemv_unit_dsp_shared.sv \
    rtwsr_round_divider_7bit.sv \
    rtwsr_round_divider_stream7.sv \
    rtwsr_rmsnorm_quant_unit.sv \
    rtwsr_swiglu_residual_unit.sv \
    rtwsr_huginn_ffn_pipeline.sv \
    rtwsr_huginn_payload_descriptor.sv]
set sources {}
set manifest [open [file join $output_dir implementation_inputs.sha256] w]
foreach name $source_names {
    if {$name eq "rtwsr_attention_gemv_unit_dsp_shared.sv"} {
        set path [file join $hw_root candidates resource_opt $name]
    } elseif {[file isfile [file join $hw_root candidates resource_opt rtl_integrated $name]]} {
        set path [file join $hw_root candidates resource_opt rtl_integrated $name]
    } else {
        set path [file join $rtl_root $name]
    }
    if {![file isfile $path]} {
        error "Missing core source: $path"
    }
    lappend sources $path
    puts $manifest "[sha256_file $path]  $path"
}
close $manifest

write_state $status_path RUNNING $stage "core-only OOC 96-channel 128-trit 4-head"
set result [catch {
    create_project -in_memory -part $part
    set_property verilog_define {SYNTH_CARRY8 XILINX_XPM} [current_fileset]
    add_files -norecurse $sources
    set_property file_type SystemVerilog [get_files $sources]
    update_compile_order -fileset sources_1

    set stage SYNTH_DESIGN
    write_state $status_path RUNNING $stage "synth_design rtwsr_transformer_top"
    synth_design -mode out_of_context -top rtwsr_transformer_top -part $part \
        -generic {MODEL_ID=0 LINEAR_CHANNELS=96 MAX_CONTEXT=2048 HBM_PARALLEL_LOAD=1 GAMMA_PARALLEL_LOAD=1 CORE_TIMING_CANDIDATE=1 CORE_128TRIT_CANDIDATE=1 RESIDUAL_NORM_FUSION=1 RESIDUAL_NORM_TILE_PRELOAD=0 POOL_READ_PARALLEL_SLOTS=0 ATTENTION_PARALLEL_CANDIDATE=1 ATTENTION_QUANT_STREAM_PIPELINE=1 ADAPTER_STATIC_REUSE=1 ATTENTION_PARALLEL_HEADS=4 RECURRENCES_OVERRIDE=32}
    create_clock -period 4.444 -name clk_core [get_ports clk]
    report_utilization -file [file join $output_dir utilization_synth.rpt]
    report_utilization -hierarchical -file [file join $output_dir utilization_hierarchical_synth.rpt]
    report_timing_summary -delay_type min_max -report_unconstrained -file [file join $output_dir timing_synth.rpt]
    write_checkpoint -force [file join $output_dir core_4head_synth.dcp]

    set stage OPT_DESIGN
    write_state $status_path RUNNING $stage "opt_design"
    opt_design
    report_utilization -file [file join $output_dir utilization_opt.rpt]
    write_checkpoint -force [file join $output_dir core_4head_opt.dcp]

    set stage PLACE_DESIGN
    write_state $status_path RUNNING $stage "place_design SSI_SpreadSLLs"
    place_design -directive SSI_SpreadSLLs
    report_utilization -file [file join $output_dir utilization_placed.rpt]
    report_timing_summary -delay_type min_max -report_unconstrained -file [file join $output_dir timing_placed.rpt]
    write_checkpoint -force [file join $output_dir core_4head_placed.dcp]

    set stage PHYS_OPT_DESIGN
    write_state $status_path RUNNING $stage "phys_opt_design Explore"
    phys_opt_design -directive Explore
    report_utilization -file [file join $output_dir utilization_physopt.rpt]
    report_timing_summary -delay_type min_max -report_unconstrained -file [file join $output_dir timing_physopt.rpt]
    write_checkpoint -force [file join $output_dir core_4head_physopt.dcp]

    set stage ROUTE_DESIGN
    write_state $status_path RUNNING $stage "route_design no_timing_driven"
    set route_result [catch {route_design -no_timing_driven} route_message route_options]
    report_utilization -file [file join $output_dir utilization_route_attempt.rpt]
    report_utilization -hierarchical -file [file join $output_dir utilization_hierarchical_route_attempt.rpt]
    report_route_status -file [file join $output_dir route_status_route_attempt.rpt]
    report_drc -file [file join $output_dir drc_route_attempt.rpt]
    report_timing_summary -delay_type min_max -report_unconstrained -file [file join $output_dir timing_route_attempt.rpt]
    report_power -file [file join $output_dir power_route_attempt.rpt]
    if {$route_result != 0} {
        return -options $route_options $route_message
    }
    write_checkpoint -force [file join $output_dir core_4head_routed.dcp]
    write_state $status_path COMPLETE $stage "core-only route and reports completed"
    close_design
} message options]

if {$result != 0} {
    write_state $status_path FAILED $stage $message
    catch {close_design}
    return -options $options $message
}
puts "CORE_OOC_ROUTE_CANDIDATE_4HEAD_COMPLETE $output_dir"
