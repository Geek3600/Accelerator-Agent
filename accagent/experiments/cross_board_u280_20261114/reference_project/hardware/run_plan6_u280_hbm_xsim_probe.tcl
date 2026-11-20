set project_root [file normalize /tmp/loopquant_plan6_u280_hbm_xsim_probe_20261028]
set output_root [file join $project_root reports]
file mkdir $output_root

create_project -force loopquant_u280_hbm_xsim_probe $project_root \
    -part xcu280-fsvh2892-2L-e
set_property target_language Verilog [current_project]
create_ip -name hbm -vendor xilinx.com -library ip -version 1.0 \
    -module_name hbm_u280

set hbm_config [list \
    CONFIG.USER_HBM_DENSITY {4GB} \
    CONFIG.USER_HBM_STACK {2} \
    CONFIG.USER_AXI_CLK_FREQ {450} \
    CONFIG.USER_AXI_INPUT_CLK_FREQ {100} \
    CONFIG.USER_SWITCH_ENABLE_00 {TRUE} \
    CONFIG.USER_SWITCH_ENABLE_01 {TRUE}]
for {set channel 0} {$channel < 32} {incr channel} {
    if {$channel < 28} {
        lappend hbm_config CONFIG.USER_SAXI_[format %02d $channel] {TRUE}
    } else {
        lappend hbm_config CONFIG.USER_SAXI_[format %02d $channel] {FALSE}
    }
}
set_property -dict $hbm_config [get_ips hbm_u280]
generate_target simulation [get_ips hbm_u280]
export_ip_user_files -of_objects [get_ips hbm_u280] -no_script -sync -force

set report [open [file join $output_root ip_configuration.txt] w]
puts $report "vivado_version=[version -short]"
puts $report "part=[get_property PART [current_project]]"
puts $report "ip=xilinx.com:ip:hbm:1.0"
set enabled_ports 0
foreach property [lsort [list_property [get_ips hbm_u280]]] {
    if {[string match CONFIG.USER_* $property]} {
        set value [get_property $property [get_ips hbm_u280]]
        puts $report "$property=$value"
        if {[string match CONFIG.USER_SAXI_* $property] && $value eq "true"} {
            incr enabled_ports
        }
    }
}
puts $report "enabled_saxi_ports=$enabled_ports"
puts $report "simulation_files:"
foreach source [get_files -all -of_objects [get_ips hbm_u280]] {
    if {[string match *.mem $source] || [string match *.sv $source] ||
        [string match *.v $source] || [string match *.vp $source]} {
        puts $report $source
    }
}
close $report
open_example_project -force -dir [file join $project_root example] -in_process \
    [get_ips hbm_u280]
set example_report [open [file join $output_root example_project.txt] w]
puts $example_report "project=[get_property DIRECTORY [current_project]]"
puts $example_report "filesets=[get_filesets]"
puts $example_report "simulation_top=[get_property TOP [get_filesets sim_1]]"
puts $example_report "simulator=[get_property TARGET_SIMULATOR [get_filesets sim_1]]"
close $example_report
puts "PLAN6_U280_HBM_XSIM_IP_GENERATED"
