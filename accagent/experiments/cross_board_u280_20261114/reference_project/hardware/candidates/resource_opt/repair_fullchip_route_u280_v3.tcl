set source_dcp /home/hyyuan/loopquant_fullchip_route_20261106/reports/route_local_repair_20261107_v2/full_shell_repaired.dcp
set output_dir /home/hyyuan/loopquant_fullchip_route_20261106/reports/route_local_repair_20261107_v3
set target_name "u_plan6_huginn_hbm_shell/u_recurrent_core/u_weight_memory/u_primary_pool/xpm_memory_base_inst_i_1848_n_0"
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
    open_checkpoint $source_dcp
    set target_net [get_nets -top_net_of_hierarchical_group -hierarchical -filter "NAME == \"$target_name\""]
    if {[llength $target_net] != 1} {error "Expected one target net; found [llength $target_net]"}
    set stage ALTERNATE_LOCAL_REROUTE
    write_status RUNNING $stage
    route_design -unroute -nets $target_net
    route_design -nets $target_net -directive AlternateCLBRouting
    set stage REPORTS
    write_status RUNNING $stage
    report_route_status -file [file join $output_dir route_status_local.rpt]
    report_drc -file [file join $output_dir drc_postroute.rpt]
    write_checkpoint -force [file join $output_dir full_shell_repaired.dcp]
    report_utilization -file [file join $output_dir utilization_postroute.rpt]
    write_status COMPLETE REPORTS_GENERATED
    close_design
} message options]
if {$result != 0} {
    write_status FAILED $stage
    puts stderr $message
    return -options $options $message
}
exit
