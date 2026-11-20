if {$argc > 0} {
    set project_dir [file normalize [lindex $argv 0]]
} else {
    set project_dir "/home/hyyuan/workspace/rtwsr_plan6_huginn_vu9p_shell_20261022_r14_no_cnn"
}
set rtl_dir [file join $project_dir plan6_rtl]
set report_prefix "plan6_huginn"
set replace_project_rtl 1
set plan6_remove_cnn 1
set wrapper_module_reference "rtwsr_plan6_huginn_9p_axi_bd"
set wrapper_file_type "Verilog"
set plan6_wrapper_file [file join $rtl_dir rtwsr_plan6_huginn_9p_axi_bd.v]
set rtl_files [list \
    [file join $rtl_dir rtwsr_transformer_top.sv] \
    [file join $rtl_dir rtwsr_linear_command_dispatch.sv] \
    [file join $rtl_dir rtwsr_linear_tile_controller.sv] \
    [file join $rtl_dir rtwsr_recurrent_command_scheduler.sv] \
    [file join $rtl_dir rtwsr_recurrent_sequencer.sv] \
    [file join $rtl_dir rtwsr_recurrent_attention_bridge.sv] \
    [file join $rtl_dir rtwsr_recurrent_attention_bridge4.sv] \
    [file join $rtl_dir rtwsr_qkv_head_buffer.sv] \
    [file join $rtl_dir rtwsr_qkv_head_buffer_banked.sv] \
    [file join $rtl_dir rtwsr_runtime_tile_gemv.sv] \
    [file join $rtl_dir rtwsr_runtime_gamma_pool.sv] \
    [file join $rtl_dir rtwsr_dual_track_gemv_array.sv] \
    [file join $rtl_dir rtwsr_runtime_weight_subsystem.sv] \
    [file join $rtl_dir rtwsr_runtime_weight_pool.sv] \
    [file join $rtl_dir rtwsr_runtime_weight_ring.sv] \
    [file join $rtl_dir uram_active_pool_bank.sv] \
    [file join $rtl_dir radix3_5trit_decoder.sv] \
    [file join $rtl_dir scale_hoisted_ternary_lane.sv] \
    [file join $rtl_dir usw512_word_decoder.sv] \
    [file join $rtl_dir usw512_dual_track_channel.sv] \
    [file join $rtl_dir usw512_channel_array.sv] \
    [file join $rtl_dir rtwsr_rope_kv_cache.sv] \
    [file join $rtl_dir rtwsr_attention_gemv_unit.sv] \
    [file join $rtl_dir rtwsr_round_divider_7bit.sv] \
    [file join $rtl_dir rtwsr_rmsnorm_quant_unit.sv] \
    [file join $rtl_dir rtwsr_swiglu_residual_unit.sv] \
    [file join $rtl_dir rtwsr_huginn_ffn_pipeline.sv] \
    [file join $rtl_dir rtwsr_huginn_payload_descriptor.sv] \
    [file join $rtl_dir rtwsr_weight_dma.sv] \
    [file join $rtl_dir rtwsr_plan6_huginn_shell.sv]]

source [file join [file dirname [info script]] integrate_plan5_shell_candidate.tcl]
