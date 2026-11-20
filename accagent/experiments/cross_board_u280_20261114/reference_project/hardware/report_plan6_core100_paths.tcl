set project_dir "/home/hyyuan/workspace/rtwsr_plan6_huginn_vu9p_shell_20261025_ctrl_d"
set report_dir [file join $project_dir plan6_core100_path_reports]
file mkdir $report_dir
set_param general.maxThreads 8
open_checkpoint [file join $project_dir app_shell_9p.runs impl_1 app_shell_9p_wrapper_physopt.dcp]

set core_mmcm [get_cells -hier -filter {REF_NAME == MMCME4_ADV && NAME =~ *rtwsr_core_clk_wiz*}]
if {[llength $core_mmcm] != 1} {
    error "Expected one accelerator core MMCM, found [llength $core_mmcm]"
}
report_property $core_mmcm -file [file join $report_dir core_mmcm_before.rpt]
set input_clock [get_clocks -of_objects [get_pins $core_mmcm/CLKIN1]]
if {[llength $input_clock] != 1} { error "The core MMCM input clock is missing" }
set input_period [get_property PERIOD $input_clock]
set input_divider [get_property DIVCLK_DIVIDE $core_mmcm]
set output_divider [expr {round(10.0 / $input_period *
    [get_property CLKFBOUT_MULT_F $core_mmcm] / $input_divider)}]
set feedback_multiplier [expr {$output_divider * $input_period * $input_divider / 10.0}]
if {$output_divider < 1.0 || $output_divider > 128.0 ||
    $feedback_multiplier < 2.0 || $feedback_multiplier > 64.0 ||
    abs($feedback_multiplier * 8.0 - round($feedback_multiplier * 8.0)) > 0.00001} {
    error "The core MMCM parameters cannot generate 100 MHz"
}
set_property -dict [list CLKFBOUT_MULT_F $feedback_multiplier \
    CLKOUT0_DIVIDE_F $output_divider] $core_mmcm
report_property $core_mmcm -file [file join $report_dir core_mmcm_100mhz.rpt]
report_clocks -file [file join $report_dir clocks_100mhz.rpt]
set core_clock [get_clocks -of_objects [get_pins $core_mmcm/CLKOUT0]]
if {[llength $core_clock] != 1 || abs([get_property PERIOD $core_clock] - 10.0) > 0.001} {
    error "The core generated clock did not change to 10 ns"
}
set core_registers [all_registers -clock $core_clock]
report_timing -delay_type max -from $core_registers -to $core_registers \
    -max_paths 20 -nworst 1 -file [file join $report_dir core_paths_100mhz.rpt]
set other_registers [filter $core_registers {NAME !~ *u_attention*}]
report_timing -delay_type max -from $other_registers -to $other_registers \
    -max_paths 20 -nworst 1 -file [file join $report_dir core_non_attention_paths_100mhz.rpt]
puts "PLAN6_CORE100_PATH_REPORTS_COMPLETE"
close_design
