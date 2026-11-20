set run_root [file normalize [file dirname [info script]]]
set rtl_root [file join $run_root rtl_integrated]
set report_root [file join $run_root reports_integrated]
set part xcu280-fsvh2892-2L-e
file mkdir $report_root

proc sha256_file {path} {
    return [lindex [exec sha256sum [file normalize $path]] 0]
}

set sources [list \
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
    rtwsr_attention_gemv_unit.sv \
    rtwsr_round_divider_7bit.sv \
    rtwsr_round_divider_stream7.sv \
    rtwsr_rmsnorm_quant_unit.sv \
    rtwsr_swiglu_residual_unit.sv \
    rtwsr_huginn_ffn_pipeline.sv \
    rtwsr_huginn_payload_descriptor.sv]

set manifest [open [file join $report_root inputs.sha256] w]
set source_paths {}
foreach source $sources {
    set source_path [file join $rtl_root $source]
    if {![file isfile $source_path]} {
        error "Missing integrated resource optimization source: $source_path"
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
synth_design -mode out_of_context -top rtwsr_transformer_top -part $part \
    -generic {MODEL_ID=0 LINEAR_CHANNELS=192 HBM_PARALLEL_LOAD=1 GAMMA_PARALLEL_LOAD=1 CORE_TIMING_CANDIDATE=1 CORE_128TRIT_CANDIDATE=1 RESIDUAL_NORM_FUSION=1 RESIDUAL_NORM_TILE_PRELOAD=1 POOL_READ_PARALLEL_SLOTS=1 ATTENTION_PARALLEL_CANDIDATE=1 ATTENTION_QUANT_STREAM_PIPELINE=1 ADAPTER_STATIC_REUSE=1 ATTENTION_PARALLEL_HEADS=8}
create_clock -name clk_core -period 5.000 [get_ports clk]
report_utilization -file [file join $report_root utilization_synth.rpt]
report_utilization -hierarchical -file [file join $report_root utilization_hierarchical_synth.rpt]
report_timing_summary -file [file join $report_root timing_synth.rpt]
close_design
puts "RESOURCE_OPT_U280_INTEGRATED_192CH_8HEAD_OOC_SYNTH_COMPLETE"
