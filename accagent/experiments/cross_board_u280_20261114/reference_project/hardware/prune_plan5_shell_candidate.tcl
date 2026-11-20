set_param general.maxThreads 1

set project_dir "/home/hyyuan/workspace/rtwsr_plan5_shell_20261020"
set bd_file [file join $project_dir \
    app_shell_9p.srcs/sources_1/bd/app_shell_9p/app_shell_9p.bd]
set report_file [file join $project_dir plan5_shell_prune_validation.txt]

open_project [file join $project_dir app_shell_9p.xpr]
open_bd_design $bd_file
current_bd_design app_shell_9p
source [file join [file dirname [info script]] prune_plan5_shell_bd.tcl]

foreach cell_name {cnn_core_1 cnncore_sys_config_1 axi_register_slice_5} {
    if {[llength [get_bd_cells -quiet $cell_name]] != 0} {
        error "Unexpected retained cell: $cell_name"
    }
}
foreach cell_name {cnn_core_0 cnncore_sys_config_0 ddr4_0 ddr4_1 \
                  axi_chip2chip_0to3_l_0 axi_combine_v1_0_1 rtwsr_9p_axi_0} {
    if {[llength [get_bd_cells -quiet $cell_name]] != 1} {
        error "Required shell cell missing: $cell_name"
    }
}
if {[get_property CONFIG.NUM_MI [get_bd_cells axi_interconnect_0]] != 4 ||
    [get_property CONFIG.NUM_SI [get_bd_cells axi_interconnect_2]] != 1} {
    error "AXI interconnect pruning did not apply"
}
if {[llength [get_bd_cells -quiet rtwsr_dma_cc]] == 1 &&
    [get_property CONFIG.NUM_SI [get_bd_cells axi_interconnect_1]] != 3} {
    error "RTWSR DMA AXI slave slot was not retained"
}

assign_bd_address
set rtwsr_map [get_bd_addr_segs -quiet \
    /axi_combine_v1_0_1/m00_axi/SEG_rtwsr_9p_axi_0_reg0]
if {[llength $rtwsr_map] != 1} {
    error "Expected one RTWSR master mapping, found [llength $rtwsr_map]"
}
set_property OFFSET 0x00F0000000 $rtwsr_map
set_property RANGE 4K $rtwsr_map
set ddr0_map [get_bd_addr_segs -quiet \
    /axi_combine_v1_0_1/m00_axi/SEG_ddr4_0_C0_DDR4_ADDRESS_BLOCK]
set ddr1_map [get_bd_addr_segs -quiet \
    /axi_combine_v1_0_1/m00_axi/SEG_ddr4_1_C0_DDR4_ADDRESS_BLOCK]
if {[llength $ddr0_map] != 1 || [llength $ddr1_map] != 1} {
    error "Both host DDR address maps must remain available"
}

validate_bd_design
save_bd_design
generate_target all [get_files $bd_file]

set report [open $report_file w]
puts $report "RETAINED_CNN_CORE cnn_core_0"
puts $report "CNN_CORE_COUNT [llength $retained_cnn_cells]"
puts $report "REMOVED_CELLS cnn_core_1 cnncore_sys_config_1 axi_register_slice_5"
puts $report "AXI_INTERCONNECT_0_NUM_MI [get_property CONFIG.NUM_MI [get_bd_cells axi_interconnect_0]]"
puts $report "AXI_INTERCONNECT_2_NUM_SI [get_property CONFIG.NUM_SI [get_bd_cells axi_interconnect_2]]"
puts $report "DDR_CONTROLLERS [get_bd_cells ddr4_0] [get_bd_cells ddr4_1]"
puts $report "HOST_DDR0_MAP [get_property OFFSET $ddr0_map] [get_property RANGE $ddr0_map]"
puts $report "HOST_DDR1_MAP [get_property OFFSET $ddr1_map] [get_property RANGE $ddr1_map]"
puts $report "HOST_LINK [get_bd_intf_pins axi_chip2chip_0to3_l_0/m0_axi] [get_bd_intf_pins axi_combine_v1_0_1/s00_axi]"
puts $report "RTWSR_CONTROL [get_bd_intf_pins axi_interconnect_0/M02_AXI] [get_bd_intf_pins rtwsr_auto_cc/S_AXI] [get_bd_intf_pins rtwsr_auto_pc/M_AXI] [get_bd_intf_pins rtwsr_9p_axi_0/S_AXI]"
if {[llength [get_bd_cells -quiet rtwsr_dma_cc]] == 1} {
    puts $report "RTWSR_DMA_INTERFACE [get_bd_intf_pins rtwsr_9p_axi_0/M_AXI] [get_bd_intf_pins rtwsr_dma_cc/S_AXI] [get_bd_intf_pins rtwsr_dma_cc/M_AXI] [get_bd_intf_pins axi_interconnect_1/S02_AXI]"
    puts $report "AXI_INTERCONNECT_1_NUM_SI [get_property CONFIG.NUM_SI [get_bd_cells axi_interconnect_1]]"
}
puts $report "RTWSR_ADDRESS [get_property OFFSET $rtwsr_map] [get_property RANGE $rtwsr_map]"
puts $report "BD_CELLS"
foreach cell [get_bd_cells -hier] {
    puts $report $cell
}
close $report

close_project
