set project_dir /tmp/loopquant_plan6_u280_hbm_xsim_probe_20261028/example/hbm_u280_ex
open_project [file join $project_dir hbm_u280_ex.xpr]

# Vivado 2021.1's generated XSim example references an unavailable legacy VIP checker.
set axi_vip_file [file join $project_dir imports axi_top.sv]
set axi_vip_handle [open $axi_vip_file r]
set axi_vip_source [read $axi_vip_handle]
close $axi_vip_handle
set checker_start [string first {`ifdef XILINX_SIMULATOR} $axi_vip_source]
set checker_end [string first {`endif} $axi_vip_source $checker_start]
if {$checker_start < 0 || $checker_end < 0} {
    error "Could not locate the optional legacy AXI protocol checker"
}
set checker_end [expr {$checker_end + [string length {`endif}] - 1}]
set axi_vip_source [string replace $axi_vip_source $checker_start $checker_end \
    "// Legacy AXI protocol checker is unavailable in Vivado 2021.1 XSim."]
set axi_vip_handle [open $axi_vip_file w]
puts -nonewline $axi_vip_handle $axi_vip_source
close $axi_vip_handle

set_property target_simulator XSim [current_project]
update_compile_order -fileset sim_1
launch_simulation -simset sim_1 -mode behavioral
run all
close_sim
close_project
puts "PLAN6_U280_HBM_OFFICIAL_XSIM_COMPLETED"
