if {$argc != 1} {
    error "usage: set_plan6_control_d.tcl <project-dir>"
}

set project_dir [file normalize [lindex $argv 0]]
open_project [file join $project_dir app_shell_9p.xpr]
open_bd_design [file join $project_dir app_shell_9p.srcs/sources_1/bd/app_shell_9p/app_shell_9p.bd]

set target_space [get_bd_addr_spaces /axi_combine_v1_0_1/m00_axi]
set control_segment [get_bd_addr_segs /rtwsr_9p_axi_0/S_AXI/reg0]
if {[llength $target_space] != 1 || [llength $control_segment] != 1} {
    error "Plan6 control address segment or target space is missing"
}
assign_bd_address -offset 0x00D0000000 -range 0x00001000 \
    -target_address_space $target_space $control_segment -force
validate_bd_design
save_bd_design
generate_target -force all [get_files [file join $project_dir app_shell_9p.srcs/sources_1/bd/app_shell_9p/app_shell_9p.bd]]
save_bd_design

set report [open [file join $project_dir plan6_control_address_validation.txt] w]
puts $report "CONTROL_BASE 0x00D0000000"
puts $report "CONTROL_RANGE 0x00001000"
puts $report "CONTROL_SEGMENT [get_property OFFSET $control_segment] [get_property RANGE $control_segment]"
puts $report "TARGET_SPACE [get_property NAME $target_space]"
puts $report "VALIDATE_BD_DESIGN PASS"
close $report
close_project
puts "PLAN6_CONTROL_D_ADDRESS_COMPLETE"
