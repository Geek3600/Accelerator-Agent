set project_dir /tmp/loopquant_plan6_u280_hbm_xsim_probe_20261028/example/hbm_u280_ex
set stage_dir /tmp/loopquant_plan6_u280_hbm27_dataflow_20261028/rtl
set export_dir /tmp/loopquant_plan6_u280_hbm27_dataflow_20261028/export
set xpm_fifo_file /home/EDA/Xilinx/Vivado/2021.1/data/ip/xpm/xpm_fifo/hdl/xpm_fifo.sv

open_project [file join $project_dir hbm_u280_ex.xpr]
set_property target_simulator VCS [current_project]

set rtl_files [list \
    [file join $stage_dir rtwsr_huginn_u280_hbm_descriptor.sv] \
    [file join $stage_dir rtwsr_hbm_read_dma_27pc.sv] \
    [file join $stage_dir rtwsr_hbm_gearbox_27lane.sv] \
    [file join $stage_dir rtwsr_hbm_weight_pool_adapter_27to24.sv] \
    [file join $stage_dir rtwsr_u280_hbm27_dataflow_tb.sv]]
add_files -fileset sim_1 -norecurse $rtl_files
if {[llength [get_files -quiet $xpm_fifo_file]] == 0} {
    add_files -fileset sim_1 -norecurse $xpm_fifo_file
}
set_property library xpm [get_files -quiet $xpm_fifo_file]

set_property top_auto_set false [get_filesets sim_1]
set_property top rtwsr_u280_hbm27_dataflow_tb [get_filesets sim_1]
update_compile_order -fileset sim_1
export_simulation -of_objects [get_filesets sim_1] \
    -directory $export_dir -simulator VCS -force

close_project
puts "PLAN6_U280_HBM27_DATAFLOW_VCS_EXPORTED"
