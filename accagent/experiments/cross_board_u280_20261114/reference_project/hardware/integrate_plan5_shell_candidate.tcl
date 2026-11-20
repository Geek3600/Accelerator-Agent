set_param general.maxThreads 1

if {![info exists project_dir]} {
    set project_dir "/home/hyyuan/workspace/rtwsr_plan5_shell_20261020_next"
}
if {![info exists rtl_dir]} {
    set rtl_dir [file join $project_dir rtwsr_hdl]
}
if {![info exists report_prefix]} {
    set report_prefix "plan5"
}
if {![info exists wrapper_module_reference]} {
    set wrapper_module_reference "rtwsr_9p_axi_bd"
}
if {![info exists wrapper_file_type]} {
    set wrapper_file_type "Verilog"
}
set bd_file [file join $project_dir \
    app_shell_9p.srcs/sources_1/bd/app_shell_9p/app_shell_9p.bd]

open_project [file join $project_dir app_shell_9p.xpr]
open_bd_design $bd_file
current_bd_design app_shell_9p

if {![info exists rtl_files]} {
set rtl_files [list \
    [file join $rtl_dir radix3_5trit_decoder.sv] \
    [file join $rtl_dir usw512_word_decoder.sv] \
    [file join $rtl_dir scale_hoisted_ternary_lane.sv] \
    [file join $rtl_dir usw512_dual_track_channel.sv] \
    [file join $rtl_dir usw512_channel_array.sv] \
    [file join $rtl_dir uram_active_pool_bank.sv] \
    [file join $rtl_dir uram_shadow_ring.sv] \
    [file join $rtl_dir rtwsr_weight_dma.sv] \
    [file join $rtl_dir rtwsr_streaming_weight_store.sv] \
    [file join $rtl_dir rtwsr_top.sv] \
    [file join $rtl_dir rtwsr_9p_axi.sv]]
}
if {[info exists replace_project_rtl] && $replace_project_rtl} {
    set old_rtl_dirs [list \
        [file normalize [file join $project_dir rtwsr_hdl]] \
        [file normalize $rtl_dir]]
    foreach existing_file [get_files -quiet -of_objects [get_filesets sources_1]] {
        set normalized_file [file normalize $existing_file]
        foreach old_rtl_dir $old_rtl_dirs {
            if {[string first "$old_rtl_dir/" "$normalized_file/"] == 0} {
                remove_files -fileset sources_1 $existing_file
                break
            }
        }
    }
}
set wrapper_file [file join $rtl_dir rtwsr_9p_axi_bd.v]
if {[info exists plan6_wrapper_file]} {
    set wrapper_file $plan6_wrapper_file
}
set legacy_bank_files [get_files -quiet -of_objects [get_filesets sources_1] *uram_pingpong_bank.sv]
if {[llength $legacy_bank_files] > 0} {
    remove_files -fileset sources_1 $legacy_bank_files
}
add_files -norecurse [concat $rtl_files [list $wrapper_file]]
set_property file_type SystemVerilog [get_files $rtl_files]
set_property file_type $wrapper_file_type [get_files $wrapper_file]
set_property verilog_define {SYNTH_CARRY8 XILINX_XPM} [current_fileset]
update_compile_order -fileset sources_1

set replace_cells {rtwsr_9p_axi_0 rtwsr_core_clk_wiz rtwsr_proc_sys_reset \
                   rtwsr_reset_zero rtwsr_auto_cc rtwsr_auto_ds rtwsr_auto_pc rtwsr_dma_cc}
set old_scalar_nets {}
set old_interface_nets {}
foreach cell_name $replace_cells {
    set old_cell [get_bd_cells -quiet $cell_name]
    if {[llength $old_cell] == 1} {
        foreach pin [get_bd_pins -quiet -of_objects $old_cell] {
            set net [get_bd_nets -quiet -of_objects $pin]
            if {[llength $net] == 1 && [lsearch -exact $old_scalar_nets $net] < 0} {
                lappend old_scalar_nets $net
            }
        }
        foreach pin [get_bd_intf_pins -quiet -of_objects $old_cell] {
            set net [get_bd_intf_nets -quiet -of_objects $pin]
            if {[llength $net] == 1 && [lsearch -exact $old_interface_nets $net] < 0} {
                lappend old_interface_nets $net
            }
        }
        delete_bd_objs $old_cell
    }
}

foreach net $old_scalar_nets {
    set has_driver 0
    foreach pin [get_bd_pins -quiet -of_objects $net] {
        if {[get_property DIR $pin] in {O IO}} {
            set has_driver 1
        }
    }
    if {!$has_driver && [llength [get_bd_ports -quiet -of_objects $net]] == 0} {
        delete_bd_objs $net
    }
}
foreach net $old_interface_nets {
    if {[llength [get_bd_intf_pins -quiet -of_objects $net]] < 2} {
        delete_bd_objs $net
    }
}

create_bd_cell -type module -reference $wrapper_module_reference rtwsr_9p_axi_0

create_bd_cell -type ip -vlnv xilinx.com:ip:clk_wiz:6.0 rtwsr_core_clk_wiz
set_property -dict [list \
    CONFIG.PRIM_IN_FREQ {100.000} \
    CONFIG.PRIM_SOURCE {No_buffer} \
    CONFIG.CLKOUT1_REQUESTED_OUT_FREQ {225.000} \
    CONFIG.CLKOUT1_USED {true} \
    CONFIG.USE_LOCKED {true} \
    CONFIG.USE_RESET {true}] [get_bd_cells rtwsr_core_clk_wiz]

create_bd_cell -type ip -vlnv xilinx.com:ip:proc_sys_reset:5.0 rtwsr_proc_sys_reset
create_bd_cell -type ip -vlnv xilinx.com:ip:xlconstant:1.1 rtwsr_reset_zero
set_property -dict [list CONFIG.CONST_WIDTH {1} CONFIG.CONST_VAL {0}] \
    [get_bd_cells rtwsr_reset_zero]

create_bd_cell -type ip -vlnv xilinx.com:ip:axi_clock_converter:2.1 rtwsr_auto_cc
set_property -dict [list \
    CONFIG.PROTOCOL {AXI4} \
    CONFIG.DATA_WIDTH {256} \
    CONFIG.ADDR_WIDTH {37} \
    CONFIG.ID_WIDTH {20} \
    CONFIG.ACLK_ASYNC {1} \
    CONFIG.SYNCHRONIZATION_STAGES {3} \
    CONFIG.READ_WRITE_MODE {READ_WRITE}] [get_bd_cells rtwsr_auto_cc]

create_bd_cell -type ip -vlnv xilinx.com:ip:axi_clock_converter:2.1 rtwsr_dma_cc
set_property -dict [list \
    CONFIG.PROTOCOL {AXI4} \
    CONFIG.DATA_WIDTH {512} \
    CONFIG.ADDR_WIDTH {37} \
    CONFIG.ID_WIDTH {5} \
    CONFIG.ACLK_ASYNC {1} \
    CONFIG.SYNCHRONIZATION_STAGES {3} \
    CONFIG.READ_WRITE_MODE {READ_ONLY}] [get_bd_cells rtwsr_dma_cc]
set_property CONFIG.NUM_SI {3} [get_bd_cells axi_interconnect_1]

create_bd_cell -type ip -vlnv xilinx.com:ip:axi_dwidth_converter:2.1 rtwsr_auto_ds
set_property -dict [list \
    CONFIG.PROTOCOL {AXI4} \
    CONFIG.ADDR_WIDTH {37} \
    CONFIG.SI_DATA_WIDTH {256} \
    CONFIG.MI_DATA_WIDTH {32} \
    CONFIG.SI_ID_WIDTH {20} \
    CONFIG.READ_WRITE_MODE {READ_WRITE}] [get_bd_cells rtwsr_auto_ds]

create_bd_cell -type ip -vlnv xilinx.com:ip:axi_protocol_converter:2.1 rtwsr_auto_pc
set_property -dict [list \
    CONFIG.SI_PROTOCOL {AXI4} \
    CONFIG.MI_PROTOCOL {AXI4LITE} \
    CONFIG.DATA_WIDTH {32} \
    CONFIG.ADDR_WIDTH {37} \
    CONFIG.ID_WIDTH {0} \
    CONFIG.READ_WRITE_MODE {READ_WRITE}] [get_bd_cells rtwsr_auto_pc]

connect_bd_intf_net [get_bd_intf_pins axi_interconnect_0/M02_AXI] \
    [get_bd_intf_pins rtwsr_auto_cc/S_AXI]
connect_bd_intf_net [get_bd_intf_pins rtwsr_auto_cc/M_AXI] \
    [get_bd_intf_pins rtwsr_auto_ds/S_AXI]
connect_bd_intf_net [get_bd_intf_pins rtwsr_auto_ds/M_AXI] \
    [get_bd_intf_pins rtwsr_auto_pc/S_AXI]
connect_bd_intf_net [get_bd_intf_pins rtwsr_auto_pc/M_AXI] \
    [get_bd_intf_pins rtwsr_9p_axi_0/S_AXI]
connect_bd_intf_net [get_bd_intf_pins rtwsr_9p_axi_0/M_AXI] \
    [get_bd_intf_pins rtwsr_dma_cc/S_AXI]
connect_bd_intf_net [get_bd_intf_pins rtwsr_dma_cc/M_AXI] \
    [get_bd_intf_pins axi_interconnect_1/S02_AXI]

connect_bd_net [get_bd_pins clk_wiz_0/clk_out100m] \
    [get_bd_pins rtwsr_core_clk_wiz/clk_in1]
connect_bd_net [get_bd_pins proc_sys_reset_3/peripheral_reset] \
    [get_bd_pins rtwsr_core_clk_wiz/reset] \
    [get_bd_pins rtwsr_proc_sys_reset/ext_reset_in]
connect_bd_net [get_bd_pins rtwsr_core_clk_wiz/locked] \
    [get_bd_pins rtwsr_proc_sys_reset/dcm_locked]
connect_bd_net [get_bd_pins rtwsr_core_clk_wiz/clk_out1] \
    [get_bd_pins rtwsr_proc_sys_reset/slowest_sync_clk] \
    [get_bd_pins rtwsr_9p_axi_0/s_axi_aclk] \
    [get_bd_pins rtwsr_auto_cc/m_axi_aclk] \
    [get_bd_pins rtwsr_auto_ds/s_axi_aclk] \
    [get_bd_pins rtwsr_auto_pc/aclk]
connect_bd_net [get_bd_pins rtwsr_core_clk_wiz/clk_out1] \
    [get_bd_pins rtwsr_dma_cc/s_axi_aclk]
connect_bd_net [get_bd_pins ddr4_0/c0_ddr4_ui_clk] \
    [get_bd_pins rtwsr_dma_cc/m_axi_aclk] \
    [get_bd_pins axi_interconnect_1/S02_ACLK]
connect_bd_net [get_bd_pins rtwsr_reset_zero/dout] \
    [get_bd_pins rtwsr_proc_sys_reset/aux_reset_in] \
    [get_bd_pins rtwsr_proc_sys_reset/mb_debug_sys_rst]

set m02_clk_net [get_bd_nets -of_objects \
    [get_bd_pins axi_interconnect_0/M02_ACLK]]
if {[llength $m02_clk_net] != 1} {
    error "Expected one clock net on axi_interconnect_0/M02_ACLK"
}
disconnect_bd_net $m02_clk_net [get_bd_pins axi_interconnect_0/M02_ACLK]
connect_bd_net [get_bd_pins clk_wiz_0/clk_out200m] \
    [get_bd_pins axi_interconnect_0/M02_ACLK] \
    [get_bd_pins rtwsr_auto_cc/s_axi_aclk]

set m02_reset_net [get_bd_nets -of_objects \
    [get_bd_pins axi_interconnect_0/M02_ARESETN]]
if {[llength $m02_reset_net] != 1} {
    error "Expected one reset net on axi_interconnect_0/M02_ARESETN"
}
disconnect_bd_net $m02_reset_net [get_bd_pins axi_interconnect_0/M02_ARESETN]
connect_bd_net [get_bd_pins proc_sys_reset_0/interconnect_aresetn] \
    [get_bd_pins axi_interconnect_0/M02_ARESETN] \
    [get_bd_pins rtwsr_auto_cc/s_axi_aresetn]
connect_bd_net [get_bd_pins rtwsr_proc_sys_reset/peripheral_aresetn] \
    [get_bd_pins rtwsr_9p_axi_0/s_axi_aresetn] \
    [get_bd_pins rtwsr_auto_cc/m_axi_aresetn] \
    [get_bd_pins rtwsr_auto_ds/s_axi_aresetn] \
    [get_bd_pins rtwsr_auto_pc/aresetn]
connect_bd_net [get_bd_pins rtwsr_proc_sys_reset/peripheral_aresetn] \
    [get_bd_pins rtwsr_dma_cc/s_axi_aresetn]
connect_bd_net [get_bd_pins proc_sys_reset_1/interconnect_aresetn] \
    [get_bd_pins rtwsr_dma_cc/m_axi_aresetn] \
    [get_bd_pins axi_interconnect_1/S02_ARESETN]

assign_bd_address
set rtwsr_addr [get_bd_addr_segs -quiet rtwsr_9p_axi_0/S_AXI/reg0]
if {[llength $rtwsr_addr] != 1} {
    error "Expected one RTWSR register address segment, found [llength $rtwsr_addr]"
}
set rtwsr_map [get_bd_addr_segs -quiet \
    /axi_combine_v1_0_1/m00_axi/SEG_rtwsr_9p_axi_0_reg0]
if {[llength $rtwsr_map] != 1} {
    error "Expected one RTWSR master mapping, found [llength $rtwsr_map]"
}
set_property OFFSET 0x00F0000000 $rtwsr_map
set_property RANGE 4K $rtwsr_map
set dma_map [get_bd_addr_segs -quiet \
    /rtwsr_9p_axi_0/M_AXI/SEG_ddr4_0_C0_DDR4_ADDRESS_BLOCK]
if {[llength $dma_map] != 1} {
    error "Expected one RTWSR DMA mapping to DDR4_0, found [llength $dma_map]"
}
set_property OFFSET 0x0800000000 $dma_map
set_property RANGE 0x0800000000 $dma_map

if {[info exists plan6_remove_cnn] && $plan6_remove_cnn} {
    source [file join [file dirname [info script]] prune_plan6_shell_bd.tcl]
} else {
    source [file join [file dirname [info script]] prune_plan5_shell_bd.tcl]
}
set ddr0_map [get_bd_addr_segs -quiet \
    /axi_combine_v1_0_1/m00_axi/SEG_ddr4_0_C0_DDR4_ADDRESS_BLOCK]
set ddr1_map [get_bd_addr_segs -quiet \
    /axi_combine_v1_0_1/m00_axi/SEG_ddr4_1_C0_DDR4_ADDRESS_BLOCK]
if {[llength $ddr0_map] != 1 || [llength $ddr1_map] != 1} {
    error "Both host DDR address maps must remain available"
}

set core_clock_pin [get_bd_pins rtwsr_core_clk_wiz/clk_out1]
set core_clock_net [get_bd_nets -quiet -of_objects $core_clock_pin]
set core_clock_sources {}
foreach pin [get_bd_pins -quiet -of_objects $core_clock_net] {
    if {[get_property DIR $pin] in {O IO}} {
        lappend core_clock_sources $pin
    }
}
if {[llength $core_clock_net] != 1 ||
    [lsearch -exact $core_clock_sources $core_clock_pin] < 0 ||
    [get_property CONFIG.CLKOUT1_REQUESTED_OUT_FREQ [get_bd_cells rtwsr_core_clk_wiz]] != 225.000} {
    error "RTWSR 225 MHz clock must be driven by rtwsr_core_clk_wiz/clk_out1"
}
set core_clock_input_net [get_bd_nets -quiet -of_objects \
    [get_bd_pins rtwsr_core_clk_wiz/clk_in1]]
if {[llength $core_clock_input_net] != 1 ||
    [lsearch -exact [get_bd_pins -quiet -of_objects $core_clock_input_net] \
        [get_bd_pins clk_wiz_0/clk_out100m]] < 0} {
    error "RTWSR clock wizard must be driven by clk_wiz_0/clk_out100m"
}

validate_bd_design
set axi_interconnect_xbar [get_bd_cells axi_interconnect_1/xbar]
set interconnect_id_width [get_property CONFIG.ID_WIDTH $axi_interconnect_xbar]
if {[info exists plan6_remove_cnn] && $plan6_remove_cnn} {
    set dma_id_width [get_property CONFIG.S01_THREAD_ID_WIDTH $axi_interconnect_xbar]
    if {[get_property CONFIG.NUM_SI [get_bd_cells axi_interconnect_1]] != 2 ||
        $dma_id_width != 5} {
        error "Unexpected CNN-free DDR0 AXI configuration: SI=[get_property CONFIG.NUM_SI [get_bd_cells axi_interconnect_1]] DMA_ID_WIDTH=$dma_id_width"
    }
} else {
    set cnn_id_width [get_property CONFIG.S01_THREAD_ID_WIDTH $axi_interconnect_xbar]
    set dma_id_width [get_property CONFIG.S02_THREAD_ID_WIDTH $axi_interconnect_xbar]
    if {$cnn_id_width != 4 || $dma_id_width != 5 || $interconnect_id_width != 7} {
        error "Unexpected DDR0 AXI ID widths: CNN=$cnn_id_width DMA=$dma_id_width xbar=$interconnect_id_width"
    }
}
validate_bd_design
save_bd_design
generate_target all [get_files $bd_file]

set report [open [file join $project_dir ${report_prefix}_rtwsr_bd_validation.txt] w]
puts $report "CORE_CLOCK_BD_CONFIG_HZ 225000000"
puts $report "CORE_CLOCK_PIN rtwsr_9p_axi_0/s_axi_aclk"
if {[info exists plan6_remove_cnn] && $plan6_remove_cnn} {
    puts $report "M01_INTERCONNECT_CLOCK_HZ 200000000"
    puts $report "M01_TARGET_CLOCK_HZ 225000000"
    puts $report "M01_AXI_CDC_HZ 200000000 225000000"
    puts $report "M01_AXI_DATA_WIDTH 256 32"
    puts $report "M01_AXI_PROTOCOL AXI4 AXI4LITE"
    puts $report "RTWSR_DMA_INTERFACE [get_bd_intf_pins rtwsr_9p_axi_0/M_AXI] -> [get_bd_intf_pins rtwsr_dma_cc/S_AXI] -> [get_bd_intf_pins axi_interconnect_1/S01_AXI]"
    puts $report "AXI_INTERFACE [get_bd_intf_pins axi_interconnect_0/M01_AXI] -> [get_bd_intf_pins rtwsr_auto_cc/S_AXI]"
} else {
    puts $report "M02_INTERCONNECT_CLOCK_HZ 200000000"
    puts $report "M02_TARGET_CLOCK_HZ 225000000"
    puts $report "M02_AXI_CDC_HZ 200000000 225000000"
    puts $report "M02_AXI_DATA_WIDTH 256 32"
    puts $report "M02_AXI_PROTOCOL AXI4 AXI4LITE"
    puts $report "RTWSR_DMA_INTERFACE [get_bd_intf_pins rtwsr_9p_axi_0/M_AXI] -> [get_bd_intf_pins rtwsr_dma_cc/S_AXI] -> [get_bd_intf_pins axi_interconnect_1/S02_AXI]"
    puts $report "AXI_INTERFACE [get_bd_intf_pins axi_interconnect_0/M02_AXI] -> [get_bd_intf_pins rtwsr_auto_cc/S_AXI]"
}
puts $report "RTWSR_ADDRESS [get_property OFFSET $rtwsr_map] [get_property RANGE $rtwsr_map]"
puts $report "RTWSR_DMA_DDR0 [get_property OFFSET $dma_map] [get_property RANGE $dma_map]"
puts $report "RTWSR_DMA_CLOCKS 225000000 250000000"
puts $report "RTWSR_CORE_CLOCK_SOURCE $core_clock_sources"
puts $report "RTWSR_CORE_CLOCK_INPUT_NET $core_clock_input_net"
puts $report "RTWSR_CORE_CLOCK_NET_ENDPOINTS [get_bd_pins -quiet -of_objects $core_clock_net]"
if {[info exists plan6_remove_cnn] && $plan6_remove_cnn} {
    puts $report "RTWSR_AXI_ID_WIDTHS DMA_S01=$dma_id_width XBAR=$interconnect_id_width"
} else {
    puts $report "RTWSR_AXI_ID_WIDTHS CNN_S01=$cnn_id_width DMA_S02=$dma_id_width XBAR=$interconnect_id_width"
}
puts $report "AXI_INTERCONNECT_1_NUM_SI [get_property CONFIG.NUM_SI [get_bd_cells axi_interconnect_1]]"
puts $report "RTWSR_REGISTERS [get_bd_intf_pins rtwsr_auto_pc/M_AXI] -> [get_bd_intf_pins rtwsr_9p_axi_0/S_AXI]"
if {[info exists plan6_remove_cnn] && $plan6_remove_cnn} {
    puts $report "CNN_CORE_COUNT $plan6_cnn_cell_count"
    puts $report "REMOVED_CELLS cnn_core_0 cnncore_sys_config_0 clk_wiz_1"
} else {
    puts $report "RETAINED_CNN_CORE cnn_core_0"
    puts $report "CNN_CORE_COUNT [llength $retained_cnn_cells]"
    puts $report "REMOVED_CELLS cnn_core_1 cnncore_sys_config_1 axi_register_slice_5"
}
puts $report "AXI_INTERCONNECT_0_NUM_MI [get_property CONFIG.NUM_MI [get_bd_cells axi_interconnect_0]]"
puts $report "AXI_INTERCONNECT_2_NUM_SI [get_property CONFIG.NUM_SI [get_bd_cells axi_interconnect_2]]"
puts $report "DDR_CONTROLLERS [get_bd_cells ddr4_0] [get_bd_cells ddr4_1]"
puts $report "HOST_DDR0_MAP [get_property OFFSET $ddr0_map] [get_property RANGE $ddr0_map]"
puts $report "HOST_DDR1_MAP [get_property OFFSET $ddr1_map] [get_property RANGE $ddr1_map]"
close $report

close_project
