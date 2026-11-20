set project_dir "/home/hyyuan/workspace/rtwsr_plan6_huginn_vu9p_shell_20261023_r17_no_cnn"
open_project [file join $project_dir app_shell_9p.xpr]
set_param general.maxThreads 8
set impl [get_runs impl_1]
set_property STEPS.PLACE_DESIGN.ARGS.DIRECTIVE SSI_SpreadLogic_high $impl
set_property STEPS.PHYS_OPT_DESIGN.IS_ENABLED true $impl
set_property STEPS.PHYS_OPT_DESIGN.ARGS.DIRECTIVE AggressiveFanoutOpt $impl
set_property STEPS.ROUTE_DESIGN.ARGS.DIRECTIVE Explore $impl
set_property STEPS.WRITE_BITSTREAM.ARGS.BIN_FILE true $impl
reset_run impl_1
launch_runs impl_1 -to_step write_bitstream -jobs 1
wait_on_run impl_1
set status [get_property STATUS [get_runs impl_1]]
puts "PLAN6_RETRY_STATUS $status"
exit

