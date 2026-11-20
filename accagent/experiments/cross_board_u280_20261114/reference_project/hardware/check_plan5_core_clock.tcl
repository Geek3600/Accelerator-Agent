set project_dir "/tmp/loopquant_plan5_core_clock_check"
if {[file exists $project_dir]} {
    error "Refusing to overwrite existing directory: $project_dir"
}

create_project loopquant_plan5_core_clock_check $project_dir \
    -part xcvu9p_CIV-flgb2104-2-i
set_param general.maxThreads 1

create_ip -name clk_wiz -vendor xilinx.com -library ip -version 6.0 \
    -module_name rtwsr_core_clk_wiz
set_property -dict [list \
    CONFIG.PRIM_IN_FREQ {100.000} \
    CONFIG.CLKOUT1_REQUESTED_OUT_FREQ {225.000} \
    CONFIG.CLKOUT1_USED {true} \
    CONFIG.USE_LOCKED {true} \
    CONFIG.USE_RESET {true} \
] [get_ips rtwsr_core_clk_wiz]

validate_ip [get_ips rtwsr_core_clk_wiz]
generate_target all [get_ips rtwsr_core_clk_wiz]
report_property [get_ips rtwsr_core_clk_wiz]
report_ip_status -file [file join $project_dir clock_ip_status.rpt]
close_project
