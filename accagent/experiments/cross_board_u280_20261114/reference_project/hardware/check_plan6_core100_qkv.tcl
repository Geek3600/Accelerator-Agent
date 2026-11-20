set project_dir "/home/hyyuan/workspace/rtwsr_plan6_huginn_vu9p_shell_20261025_ctrl_d"
set report_dir [file join $project_dir plan6_core100_qkv_audit]
set integration_script "/home/hyyuan/workspace/rtwsr_plan6_huginn_vu9p_shell_20261026_attn_pipeline/replace_plan6_qkv_checkpoint.tcl"
file mkdir $report_dir
set_param general.maxThreads 8
open_project -read_only [file join $project_dir app_shell_9p.xpr]
open_run synth_1
source $integration_script
set core_mmcm [get_cells -hier -filter {REF_NAME == MMCME4_ADV && NAME =~ *rtwsr_core_clk_wiz*}]
if {[llength $core_mmcm] != 1} { error "Expected one accelerator core MMCM" }
set_property -dict {CLKFBOUT_MULT_F 48.0 CLKOUT0_DIVIDE_F 12} $core_mmcm
set core_clock [get_clocks -of_objects [get_pins $core_mmcm/CLKOUT0]]
if {[llength $core_clock] != 1 || abs([get_property PERIOD $core_clock] - 10.0) > 0.001} {
    error "The complete shell core clock must have a 10 ns period"
}
report_clocks -file [file join $report_dir clocks.rpt]
report_utilization -file [file join $report_dir utilization.rpt]
report_utilization -hierarchical -file [file join $report_dir utilization_hierarchical.rpt]
set core_registers [all_registers -clock $core_clock]
set other_registers [filter $core_registers {NAME !~ *u_attention*}]
report_timing -delay_type max -from $other_registers -to $other_registers \
    -max_paths 20 -nworst 1 -file [file join $report_dir core_non_attention_paths.rpt]
set qkv_registers [filter $core_registers {NAME =~ *u_qkv_head_buffer*}]
report_timing -delay_type max -from $qkv_registers -to $qkv_registers \
    -max_paths 10 -nworst 1 -file [file join $report_dir qkv_internal_paths.rpt]
set channel [open [file join $report_dir inputs.sha256] w]
foreach path [list [info script] $integration_script $qkv_checkpoint $qkv_manifest $qkv_rtl \
    [file join $project_dir app_shell_9p.runs synth_1 app_shell_9p_wrapper.dcp] \
    [file join $project_dir app_shell_9p.gen sources_1 bd app_shell_9p ip \
        app_shell_9p_rtwsr_9p_axi_0_6 app_shell_9p_rtwsr_9p_axi_0_6.dcp]] {
    puts $channel [exec sha256sum [file normalize $path]]
}
close $channel
puts "PLAN6_CORE100_QKV_AUDIT_COMPLETE"
close_project
