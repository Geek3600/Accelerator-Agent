proc require_plan6_interface_link {source_name destination_name} {
    set source_pin [get_bd_intf_pins -quiet $source_name]
    set destination_pin [get_bd_intf_pins -quiet $destination_name]
    if {[llength $source_pin] != 1 || [llength $destination_pin] != 1} {
        error "Required Plan 6 interface pin missing: $source_name or $destination_name"
    }
    set net [get_bd_intf_nets -quiet -of_objects $source_pin]
    if {[llength $net] != 1} {
        error "Required Plan 6 interface route is disconnected: $source_name"
    }
    set found 0
    foreach peer [get_bd_intf_pins -quiet -of_objects $net] {
        if {[string trimleft $peer "/"] eq [string trimleft $destination_pin "/"]} {
            set found 1
        }
    }
    if {!$found} {
        error "Required Plan 6 interface route missing: $source_name -> $destination_name"
    }
}

proc disconnect_plan6_pin {pin_path interface_pin} {
    if {$interface_pin} {
        set pin [get_bd_intf_pins -quiet $pin_path]
        set net [get_bd_intf_nets -quiet -of_objects $pin]
        if {[llength $pin] != 1 || [llength $net] != 1} {
            error "Expected one connected Plan 6 interface pin: $pin_path"
        }
        disconnect_bd_intf_net $net $pin
    } else {
        set pin [get_bd_pins -quiet $pin_path]
        set net [get_bd_nets -quiet -of_objects $pin]
        if {[llength $pin] != 1 || [llength $net] != 1} {
            error "Expected one connected Plan 6 scalar pin: $pin_path"
        }
        disconnect_bd_net $net $pin
    }
}

foreach cell_name {cnn_core_0 cnncore_sys_config_0 clk_wiz_1} {
    if {[llength [get_bd_cells -quiet $cell_name]] != 1} {
        error "Expected CNN-only shell cell before removal: $cell_name"
    }
}

foreach pin_path {
    /axi_interconnect_0/M00_AXI /axi_interconnect_0/M01_AXI
    /axi_interconnect_0/M02_AXI /axi_interconnect_0/M03_AXI
    /axi_interconnect_1/S01_AXI /axi_interconnect_1/S02_AXI
} {
    disconnect_plan6_pin $pin_path 1
}
foreach pin_path {
    /axi_interconnect_0/M00_ACLK /axi_interconnect_0/M00_ARESETN
    /axi_interconnect_0/M01_ACLK /axi_interconnect_0/M01_ARESETN
    /axi_interconnect_0/M02_ACLK /axi_interconnect_0/M02_ARESETN
    /axi_interconnect_0/M03_ACLK /axi_interconnect_0/M03_ARESETN
    /axi_interconnect_1/S01_ACLK /axi_interconnect_1/S01_ARESETN
    /axi_interconnect_1/S02_ACLK /axi_interconnect_1/S02_ARESETN
} {
    disconnect_plan6_pin $pin_path 0
}

foreach cell_name {cnn_core_0 cnncore_sys_config_0 clk_wiz_1} {
    delete_bd_objs [get_bd_cells $cell_name]
}

set_property CONFIG.NUM_MI {3} [get_bd_cells axi_interconnect_0]
set_property CONFIG.NUM_SI {2} [get_bd_cells axi_interconnect_1]

connect_bd_intf_net [get_bd_intf_pins axi_interconnect_0/M00_AXI] \
    [get_bd_intf_pins axi_register_slice_0/S_AXI]
connect_bd_intf_net [get_bd_intf_pins axi_interconnect_0/M01_AXI] \
    [get_bd_intf_pins rtwsr_auto_cc/S_AXI]
connect_bd_intf_net [get_bd_intf_pins axi_interconnect_0/M02_AXI] \
    [get_bd_intf_pins axi_register_slice_4/S_AXI]
connect_bd_intf_net [get_bd_intf_pins axi_interconnect_1/S01_AXI] \
    [get_bd_intf_pins rtwsr_dma_cc/M_AXI]

connect_bd_net [get_bd_pins ddr4_0/c0_ddr4_ui_clk] \
    [get_bd_pins axi_interconnect_0/M00_ACLK]
connect_bd_net [get_bd_pins proc_sys_reset_1/peripheral_aresetn] \
    [get_bd_pins axi_interconnect_0/M00_ARESETN]
connect_bd_net [get_bd_pins clk_wiz_0/clk_out200m] \
    [get_bd_pins axi_interconnect_0/M01_ACLK]
connect_bd_net [get_bd_pins proc_sys_reset_0/interconnect_aresetn] \
    [get_bd_pins axi_interconnect_0/M01_ARESETN]
connect_bd_net [get_bd_pins ddr4_1/c0_ddr4_ui_clk] \
    [get_bd_pins axi_interconnect_0/M02_ACLK]
connect_bd_net [get_bd_pins proc_sys_reset_2/interconnect_aresetn] \
    [get_bd_pins axi_interconnect_0/M02_ARESETN]
connect_bd_net [get_bd_pins ddr4_0/c0_ddr4_ui_clk] \
    [get_bd_pins axi_interconnect_1/S01_ACLK]
connect_bd_net [get_bd_pins proc_sys_reset_1/interconnect_aresetn] \
    [get_bd_pins axi_interconnect_1/S01_ARESETN]

set cnn_cells [get_bd_cells -quiet -hier -filter {NAME =~ *cnn*}]
if {[llength $cnn_cells] != 0 ||
    [llength [get_bd_cells -quiet clk_wiz_1]] != 0} {
    error "CNN-only cells remain in the Plan 6 shell: $cnn_cells"
}
if {[get_property CONFIG.NUM_MI [get_bd_cells axi_interconnect_0]] != 3 ||
    [get_property CONFIG.NUM_SI [get_bd_cells axi_interconnect_1]] != 2} {
    error "Plan 6 AXI ports were not compacted after CNN removal"
}

require_plan6_interface_link \
    /axi_interconnect_0/M01_AXI /rtwsr_auto_cc/S_AXI
require_plan6_interface_link \
    /rtwsr_auto_cc/M_AXI /rtwsr_auto_ds/S_AXI
require_plan6_interface_link \
    /rtwsr_auto_ds/M_AXI /rtwsr_auto_pc/S_AXI
require_plan6_interface_link \
    /rtwsr_auto_pc/M_AXI /rtwsr_9p_axi_0/S_AXI
require_plan6_interface_link \
    /rtwsr_9p_axi_0/M_AXI /rtwsr_dma_cc/S_AXI
require_plan6_interface_link \
    /rtwsr_dma_cc/M_AXI /axi_interconnect_1/S01_AXI
require_plan6_interface_link \
    /axi_chip2chip_0to3_l_0/m0_axi /axi_combine_v1_0_1/s00_axi
require_plan6_interface_link \
    /axi_chip2chip_0to3_l_0/m1_axi /axi_combine_v1_0_1/s01_axi
require_plan6_interface_link \
    /axi_combine_v1_0_1/m00_axi /axi_register_slice_1/S_AXI
require_plan6_interface_link \
    /axi_register_slice_1/M_AXI /axi_interconnect_0/S00_AXI
require_plan6_interface_link \
    /axi_interconnect_0/M00_AXI /axi_register_slice_0/S_AXI
require_plan6_interface_link \
    /axi_register_slice_0/M_AXI /axi_interconnect_1/S00_AXI
require_plan6_interface_link \
    /axi_interconnect_1/M00_AXI /ddr4_0/C0_DDR4_S_AXI
require_plan6_interface_link \
    /axi_interconnect_0/M02_AXI /axi_register_slice_4/S_AXI
require_plan6_interface_link \
    /axi_register_slice_4/M_AXI /axi_interconnect_2/S00_AXI
require_plan6_interface_link \
    /axi_interconnect_2/M00_AXI /ddr4_1/C0_DDR4_S_AXI

assign_bd_address
set rtwsr_map [get_bd_addr_segs -quiet \
    /axi_combine_v1_0_1/m00_axi/SEG_rtwsr_9p_axi_0_reg0]
set dma_map [get_bd_addr_segs -quiet \
    /rtwsr_9p_axi_0/M_AXI/SEG_ddr4_0_C0_DDR4_ADDRESS_BLOCK]
set ddr0_map [get_bd_addr_segs -quiet \
    /axi_combine_v1_0_1/m00_axi/SEG_ddr4_0_C0_DDR4_ADDRESS_BLOCK]
set ddr1_map [get_bd_addr_segs -quiet \
    /axi_combine_v1_0_1/m00_axi/SEG_ddr4_1_C0_DDR4_ADDRESS_BLOCK]
if {[llength $rtwsr_map] != 1 || [llength $dma_map] != 1 ||
    [llength $ddr0_map] != 1 || [llength $ddr1_map] != 1} {
    error "RTWSR or host DDR address maps are incomplete after CNN removal"
}
set_property OFFSET 0x00D0000000 $rtwsr_map
set_property RANGE 4K $rtwsr_map
set_property OFFSET 0x0800000000 $dma_map
set_property RANGE 0x0800000000 $dma_map

set retained_cnn_cells {}
set plan6_cnn_cell_count 0
