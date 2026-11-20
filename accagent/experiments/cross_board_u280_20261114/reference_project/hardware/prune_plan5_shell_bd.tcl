foreach cell_name {cnn_core_1 cnncore_sys_config_1 axi_register_slice_5} {
    set cell [get_bd_cells -quiet $cell_name]
    if {[llength $cell] == 1} {
        delete_bd_objs $cell
    }
}

set_property CONFIG.NUM_MI {4} [get_bd_cells axi_interconnect_0]
set_property CONFIG.NUM_SI {1} [get_bd_cells axi_interconnect_2]

proc require_plan5_interface_link {source_name destination_name} {
    set source_pin [get_bd_intf_pins -quiet $source_name]
    set destination_pin [get_bd_intf_pins -quiet $destination_name]
    if {[llength $source_pin] != 1 || [llength $destination_pin] != 1} {
        error "Required interface pin missing: $source_name or $destination_name"
    }
    set net [get_bd_intf_nets -quiet -of_objects $source_pin]
    if {[llength $net] != 1} {
        error "Required interface route is disconnected: $source_name"
    }
    set found 0
    foreach peer [get_bd_intf_pins -quiet -of_objects $net] {
        if {[string trimleft $peer "/"] eq
            [string trimleft $destination_pin "/"]} {
            set found 1
        }
    }
    if {!$found} {
        error "Required interface route missing: $source_name -> $destination_name"
    }
}

set retained_cnn_cells {}
foreach cell [get_bd_cells -hier] {
    set cell_name [file tail [get_property NAME $cell]]
    if {[regexp {^cnn_core_[^/]+$} $cell_name]} {
        lappend retained_cnn_cells $cell_name
    }
}
if {[llength $retained_cnn_cells] != 1 ||
    [lsearch -exact $retained_cnn_cells cnn_core_0] < 0} {
    error "Expected only cnn_core_0, found $retained_cnn_cells"
}

foreach cell_name {cnn_core_1 cnncore_sys_config_1 axi_register_slice_5} {
    if {[llength [get_bd_cells -quiet $cell_name]] != 0} {
        error "Pruned cell remains in the block design: $cell_name"
    }
}

require_plan5_interface_link \
    /axi_interconnect_0/M02_AXI /rtwsr_auto_cc/S_AXI
require_plan5_interface_link \
    /rtwsr_auto_cc/M_AXI /rtwsr_auto_ds/S_AXI
require_plan5_interface_link \
    /rtwsr_auto_ds/M_AXI /rtwsr_auto_pc/S_AXI
require_plan5_interface_link \
    /rtwsr_auto_pc/M_AXI /rtwsr_9p_axi_0/S_AXI
if {[llength [get_bd_cells -quiet rtwsr_dma_cc]] == 1} {
    require_plan5_interface_link \
        /rtwsr_9p_axi_0/M_AXI /rtwsr_dma_cc/S_AXI
    require_plan5_interface_link \
        /rtwsr_dma_cc/M_AXI /axi_interconnect_1/S02_AXI
}
require_plan5_interface_link \
    /axi_chip2chip_0to3_l_0/m0_axi /axi_combine_v1_0_1/s00_axi
require_plan5_interface_link \
    /axi_chip2chip_0to3_l_0/m1_axi /axi_combine_v1_0_1/s01_axi
require_plan5_interface_link \
    /axi_combine_v1_0_1/m00_axi /axi_register_slice_1/S_AXI
require_plan5_interface_link \
    /axi_register_slice_1/M_AXI /axi_interconnect_0/S00_AXI
require_plan5_interface_link \
    /axi_interconnect_0/M01_AXI /axi_register_slice_0/S_AXI
require_plan5_interface_link \
    /axi_register_slice_0/M_AXI /axi_interconnect_1/S00_AXI
require_plan5_interface_link \
    /axi_interconnect_1/M00_AXI /ddr4_0/C0_DDR4_S_AXI
require_plan5_interface_link \
    /axi_interconnect_0/M03_AXI /axi_register_slice_4/S_AXI
require_plan5_interface_link \
    /axi_register_slice_4/M_AXI /axi_interconnect_2/S00_AXI
require_plan5_interface_link \
    /axi_interconnect_2/M00_AXI /ddr4_1/C0_DDR4_S_AXI
require_plan5_interface_link \
    /axi_interconnect_0/M00_AXI /cnncore_sys_config_0/S00_AXI
require_plan5_interface_link \
    /cnn_core_0/c0_ddr4_s_axi /axi_interconnect_1/S01_AXI

