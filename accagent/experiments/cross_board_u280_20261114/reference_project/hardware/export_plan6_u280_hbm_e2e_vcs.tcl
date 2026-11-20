set project_dir /tmp/loopquant_plan6_u280_hbm_e2e_20261028/project/hbm_u280_ex
set stage_dir /tmp/loopquant_plan6_u280_hbm_e2e_20261028/rtl
set export_dir /tmp/loopquant_plan6_u280_hbm_e2e_20261028/export
set xpm_fifo_file /home/EDA/Xilinx/Vivado/2021.1/data/ip/xpm/xpm_fifo/hdl/xpm_fifo.sv

open_project [file join $project_dir hbm_u280_ex.xpr]
set_property target_simulator VCS [current_project]

set rtl_files [list \
    [file join $stage_dir rtwsr_plan6_huginn_shell.sv] \
    [file join $stage_dir rtwsr_transformer_top.sv] \
    [file join $stage_dir rtwsr_linear_command_dispatch.sv] \
    [file join $stage_dir rtwsr_linear_tile_controller.sv] \
    [file join $stage_dir rtwsr_recurrent_command_scheduler.sv] \
    [file join $stage_dir rtwsr_recurrent_sequencer.sv] \
    [file join $stage_dir rtwsr_recurrent_attention_bridge.sv] \
    [file join $stage_dir rtwsr_recurrent_attention_bridge4.sv] \
    [file join $stage_dir rtwsr_qkv_head_buffer.sv] \
    [file join $stage_dir rtwsr_qkv_head_buffer_banked.sv] \
    [file join $stage_dir rtwsr_runtime_tile_gemv.sv] \
    [file join $stage_dir rtwsr_adapter_static_cache.sv] \
    [file join $stage_dir rtwsr_runtime_gamma_pool.sv] \
    [file join $stage_dir rtwsr_dual_track_gemv_array.sv] \
    [file join $stage_dir rtwsr_runtime_weight_subsystem.sv] \
    [file join $stage_dir rtwsr_runtime_weight_pool.sv] \
    [file join $stage_dir rtwsr_runtime_weight_ring.sv] \
    [file join $stage_dir uram_active_pool_bank.sv] \
    [file join $stage_dir radix3_5trit_decoder.sv] \
    [file join $stage_dir scale_hoisted_ternary_lane.sv] \
    [file join $stage_dir usw512_word_decoder.sv] \
    [file join $stage_dir usw512_dual_track_channel.sv] \
    [file join $stage_dir usw512_channel_array.sv] \
    [file join $stage_dir rtwsr_rope_kv_cache.sv] \
    [file join $stage_dir rtwsr_attention_gemv_unit.sv] \
    [file join $stage_dir rtwsr_rmsnorm_quant_unit.sv] \
    [file join $stage_dir rtwsr_swiglu_residual_unit.sv] \
    [file join $stage_dir rtwsr_huginn_ffn_pipeline.sv] \
    [file join $stage_dir rtwsr_huginn_payload_descriptor.sv] \
    [file join $stage_dir rtwsr_weight_dma.sv] \
    [file join $stage_dir rtwsr_round_divider_7bit.sv] \
    [file join $stage_dir candidates/u280_hbm/rtwsr_huginn_u280_hbm_descriptor.sv] \
    [file join $stage_dir candidates/u280_hbm/rtwsr_hbm_read_dma_27pc.sv] \
    [file join $stage_dir candidates/u280_hbm/rtwsr_hbm_gearbox_27lane.sv] \
    [file join $stage_dir candidates/u280_hbm/rtwsr_hbm_weight_pool_adapter_27to24.sv] \
    [file join $stage_dir candidates/u280_hbm/rtwsr_plan6_huginn_u280_hbm_weight_path.sv] \
    [file join $stage_dir rtwsr_plan6_huginn_u280_hbm_shell.sv] \
    [file join $stage_dir candidates/u280_hbm/rtwsr_u280_hbm_shell_e2e_tb.sv] \
    [file join $stage_dir tests/rtwsr_u280_hbm_e2e_bfms.sv]]

add_files -fileset sim_1 -norecurse $rtl_files
if {[llength [get_files -quiet $xpm_fifo_file]] == 0} {
    add_files -fileset sim_1 -norecurse $xpm_fifo_file
}
set_property library xpm [get_files -quiet $xpm_fifo_file]
set_property top_auto_set false [get_filesets sim_1]
set_property top rtwsr_u280_hbm_shell_e2e_tb [get_filesets sim_1]
update_compile_order -fileset sim_1
export_simulation -of_objects [get_filesets sim_1] \
    -directory $export_dir -simulator VCS -force

close_project
puts "PLAN6_U280_HBM_E2E_VCS_EXPORTED"
