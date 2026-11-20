set run_root /home/hyyuan/loopquant_fullchip_route_20261106
set output_dir [file join $run_root reports route_local_repair_20261107_v2]
file mkdir $output_dir
set_param general.maxThreads 32
set status_file [file join $output_dir implementation_status.txt]
proc write_status {state stage} {
    global status_file
    set handle [open $status_file w]
    puts $handle "STATE $state\nSTAGE $stage\nUTC [clock format [clock seconds] -gmt 1 -format {%Y-%m-%dT%H:%M:%SZ}]"
    close $handle
}
set stage OPEN_CHECKPOINT
set result [catch {
write_status RUNNING $stage
open_checkpoint [file join $run_root reports route_retry_20261106_ultrathreads full_shell_routed.dcp]
set problem_names {
    u_plan6_huginn_hbm_shell/u_recurrent_core/u_linear_engine/activation_q_reg_0_1_1260_1273/DOE1
    u_plan6_huginn_hbm_shell/u_recurrent_core/u_linear_engine/u_array/gen_slr_array[0].u_channel_array/gen_channel[23].u_channel/u_dense_track/p_0_in78_out[0]
    u_plan6_huginn_hbm_shell/u_recurrent_core/u_weight_memory/u_primary_pool/xpm_memory_base_inst_i_1848_n_0
}
set filters {}
foreach name $problem_names {
    lappend filters "NAME == \"$name\""
}
set problem_nets [get_nets -top_net_of_hierarchical_group -hierarchical -filter [join $filters { || }]]
if {[llength $problem_nets] != 3} {error "Expected three route net objects; found [llength $problem_nets]"}
set stage LOCAL_REROUTE
write_status RUNNING $stage
route_design -unroute -nets $problem_nets
route_design -nets $problem_nets
set stage REPORTS
write_status RUNNING $stage
report_route_status -file [file join $output_dir route_status_local.rpt]
write_checkpoint -force [file join $output_dir full_shell_repaired.dcp]
report_utilization -file [file join $output_dir utilization_postroute.rpt]
report_drc -file [file join $output_dir drc_postroute.rpt]
report_power -file [file join $output_dir power_postroute.rpt]
write_status COMPLETE REPORTS_GENERATED
close_design
} message options]
if {$result != 0} {
    write_status FAILED $stage
    puts stderr $message
    return -options $options $message
}
exit
