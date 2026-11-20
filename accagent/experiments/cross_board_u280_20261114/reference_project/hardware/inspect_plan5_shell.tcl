set project_dir "/home/hyyuan/workspace/rtwsr_plan5_shell_20261020"
set report_file "/tmp/loopquant_plan5_shell_inspection.txt"

open_project [file join $project_dir app_shell_9p.xpr]
open_bd_design [file join $project_dir \
    app_shell_9p.srcs/sources_1/bd/app_shell_9p/app_shell_9p.bd]

set report [open $report_file w]
puts $report "BLOCK_DESIGN_CELLS"
foreach cell [get_bd_cells -hier] {
    puts $report $cell
}

puts $report "\nRELEVANT_PINS"
foreach pin [get_bd_pins -hier] {
    set name [get_property NAME $pin]
    if {[string match "*M02*" $name] || [string match "*m02*" $name] ||
        [string match "*clk_wiz_0*" $name] ||
        [string match "*proc_sys_reset_3*" $name]} {
        puts $report "$name [get_property DIR $pin] [get_property TYPE $pin]"
    }
}

puts $report "\nRELEVANT_INTERFACES"
foreach intf [get_bd_intf_pins -hier] {
    set name [get_property NAME $intf]
    if {[string match "*M02*" $name] || [string match "*m02*" $name]} {
        puts $report "$name [get_property MODE $intf]"
    }
}

puts $report "\nRELEVANT_NETS"
foreach net [get_bd_nets -hier] {
    set name [get_property NAME $net]
    set ports [get_bd_pins -of_objects $net]
    set interfaces [get_bd_intf_pins -of_objects $net]
    set joined "$ports $interfaces"
    if {[string match "*M02*" $joined] || [string match "*m02*" $joined] ||
        [string match "*clk_wiz_0*" $joined] ||
        [string match "*proc_sys_reset_3*" $joined]} {
        puts $report "$name | $joined"
    }
}

puts $report "\nM00_CONVERTER_CONFIG"
foreach cell_path [list \
    /axi_interconnect_0/m00_couplers/auto_cc \
    /axi_interconnect_0/m00_couplers/auto_ds \
    /axi_interconnect_0/m00_couplers/auto_pc] {
    set cell [get_bd_cells $cell_path]
    puts $report "CELL $cell_path"
    foreach property [list_property $cell] {
        if {[string match "CONFIG.*" $property]} {
            puts $report "$property [get_property $property $cell]"
        }
    }
}

puts $report "\nRTWSR_ADDRESS_SEGMENT"
set rtwsr_addr [get_bd_addr_segs -quiet /rtwsr_9p_axi_0/S_AXI/reg0]
foreach property [list_property $rtwsr_addr] {
    puts $report "$property [get_property $property $rtwsr_addr]"
}

puts $report "\nADDRESS_SPACE_SEGMENTS"
foreach segment [get_bd_addr_segs -hier] {
    puts $report "$segment NAME=[get_property NAME $segment] OFFSET=[get_property OFFSET $segment] RANGE=[get_property RANGE $segment] PATH=[get_property PATH $segment]"
}

close $report
close_project
