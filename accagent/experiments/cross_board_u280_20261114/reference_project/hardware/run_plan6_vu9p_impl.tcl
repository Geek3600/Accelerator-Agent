set run_root [file normalize [file dirname [info script]]]
set source_root [file join $run_root rtl]
if {[info exists ::argv] && [llength $::argv] > 0} {
    set part [lindex $::argv 0]
} else {
    set part xcvu9p-flga2104-2L-e
}
if {$part eq "xcvu9p-flga2104-2L-e"} {
    set device_name vu9p
} elseif {$part eq "xcu280-fsvh2892-2L-e"} {
    set device_name u280
} else {
    error "unsupported Plan 6 part: $part"
}
if {[info exists ::argv] && [llength $::argv] > 1} {
    set model_id [lindex $::argv 1]
} else {
    set model_id 0
}
if {$model_id ni {0 1 2}} {
    error "unsupported Plan 6 MODEL_ID: $model_id"
}
set output_root [file join $run_root output_$device_name model_$model_id]

file mkdir $output_root
set_param general.maxThreads 8
create_project -in_memory -part $part
set_property verilog_define {SYNTH_CARRY8 XILINX_XPM} [current_fileset]

set rtl_sources [list \
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
    rtwsr_rmsnorm_quant_unit.sv \
    rtwsr_swiglu_residual_unit.sv \
    rtwsr_huginn_ffn_pipeline.sv \
    rtwsr_huginn_payload_descriptor.sv]

set rtl_files {}
foreach source $rtl_sources {
    lappend rtl_files [file join $source_root $source]
}
add_files -norecurse $rtl_files
set_property file_type SystemVerilog [get_files $rtl_files]
update_compile_order -fileset sources_1

synth_design -top rtwsr_transformer_top -part $part -generic MODEL_ID=$model_id
create_clock -name clk_core -period 5.000 [get_ports clk]
write_checkpoint -force [file join $output_root rtwsr_transformer_top_synth.dcp]
report_utilization -file [file join $output_root utilization_synth.rpt]
report_timing_summary -file [file join $output_root timing_synth.rpt]

opt_design
place_design
phys_opt_design
route_design
write_checkpoint -force [file join $output_root rtwsr_transformer_top_routed.dcp]
report_utilization -file [file join $output_root utilization_routed.rpt]
report_timing_summary -file [file join $output_root timing_routed.rpt]
report_power -file [file join $output_root power_routed.rpt]

puts "PLAN6_VU9P_IMPL_COMPLETE"
