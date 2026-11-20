set project_dir "/home/hyyuan/workspace/rtwsr_plan6_huginn_vu9p_direct_20261026"
set source_tcl [file join $project_dir plan6_reports_attn_qkv_ssi_spread_100mhz continue_plan6_ssi_spread_from_opt.tcl]
set report_dir [file join $project_dir plan6_reports_attn_qkv_ssi_balance_slls_100mhz]
set generated_tcl [file join $report_dir continue_plan6_ssi_balance_slls_effective.tcl]

file mkdir $report_dir
set input [open $source_tcl r]
set source [read $input]
close $input

set replacements [list \
    "plan6_reports_attn_qkv_ssi_spread_100mhz" "plan6_reports_attn_qkv_ssi_balance_slls_100mhz" \
    "saved_opt_project_ssi_spread" "saved_opt_project_ssi_balance_slls" \
    "plan6_ssi_spread_from_opt" "plan6_ssi_balance_slls_from_opt" \
    "SSI spreading candidate status already exists" "SSI balance candidate status already exists" \
    "PLACEMENT_DIRECTIVE SSI_SpreadSLLs" "PLACEMENT_DIRECTIVE SSI_BalanceSLLs" \
    "place_design -directive SSI_SpreadSLLs" "place_design -directive SSI_BalanceSLLs" \
    "app_shell_9p_wrapper_placed_ssi_spread.dcp" "app_shell_9p_wrapper_placed_ssi_balance_slls.dcp" \
    "app_shell_9p_wrapper_physopt_ssi_spread.dcp" "app_shell_9p_wrapper_physopt_ssi_balance_slls.dcp" \
    "app_shell_9p_wrapper_routed_ssi_spread.dcp" "app_shell_9p_wrapper_routed_ssi_balance_slls.dcp"]
set source [string map $replacements $source]

set output [open $generated_tcl w]
puts -nonewline $output $source
close $output
source $generated_tcl
