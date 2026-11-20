set project_dir /tmp/loopquant_plan6_u280_hbm32_probe_20261028/example/hbm_u280_ex
set export_dir /tmp/loopquant_plan6_u280_hbm32_vcs_example_20261028
open_project [file join $project_dir hbm_u280_ex.xpr]
set_property target_simulator VCS [current_project]
update_compile_order -fileset sim_1
export_simulation -of_objects [get_filesets sim_1] \
    -directory $export_dir -simulator VCS -force
puts "PLAN6_U280_HBM32_VCS_EXAMPLE_EXPORTED"
