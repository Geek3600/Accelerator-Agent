set project_dir "/home/hyyuan/workspace/rtwsr_plan5_shell_20261020"
set bd_file [file join $project_dir \
    app_shell_9p.srcs/sources_1/bd/app_shell_9p/app_shell_9p.bd]

open_project [file join $project_dir app_shell_9p.xpr]
open_bd_design $bd_file
current_bd_design app_shell_9p

set rtwsr_map [get_bd_addr_segs -quiet \
    /axi_combine_v1_0_1/m00_axi/SEG_rtwsr_9p_axi_0_reg0]
if {[llength $rtwsr_map] != 1} {
    error "Expected one RTWSR master mapping, found [llength $rtwsr_map]"
}
set_property OFFSET 0x00F0000000 $rtwsr_map
set_property RANGE 4K $rtwsr_map
validate_bd_design
save_bd_design
generate_target all [get_files $bd_file]

set report [open [file join $project_dir plan5_rtwsr_bd_validation.txt] w]
puts $report "CORE_CLOCK_BD_CONFIG_HZ 225000000"
puts $report "CORE_CLOCK_PIN rtwsr_9p_axi_0/s_axi_aclk"
puts $report "M02_INTERCONNECT_CLOCK_HZ 200000000"
puts $report "M02_TARGET_CLOCK_HZ 225000000"
puts $report "M02_AXI_CDC_HZ 200000000 225000000"
puts $report "M02_AXI_DATA_WIDTH 256 32"
puts $report "M02_AXI_PROTOCOL AXI4 AXI4LITE"
puts $report "RTWSR_ADDRESS [get_property OFFSET $rtwsr_map] [get_property RANGE $rtwsr_map]"
puts $report "AXI_INTERFACE [get_bd_intf_pins axi_interconnect_0/M02_AXI] -> [get_bd_intf_pins rtwsr_9p_axi_0/S_AXI]"
close $report

close_project
