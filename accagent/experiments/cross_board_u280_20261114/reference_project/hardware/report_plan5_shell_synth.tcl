set project_dir "/home/hyyuan/workspace/rtwsr_plan5_shell_20261020_next"
set report_dir [file join $project_dir plan5_reports]
set input_manifest [file join $report_dir storagefix_shell_inputs.sha256]
set status_path [file join $report_dir storagefix_shell_status.txt]

if {[current_project -quiet] eq ""} {
    open_project [file join $project_dir app_shell_9p.xpr]
}
set_param general.maxThreads 1
if {[file normalize [get_property DIRECTORY [current_project]]] ne $project_dir ||
    [get_property top [get_filesets sources_1]] ne "app_shell_9p_wrapper"} {
    error "Unexpected full-shell project or synthesis top"
}
set source_set [get_filesets sources_1]
set legacy_bank_files [get_files -quiet -of_objects $source_set *uram_pingpong_bank.sv]
if {[llength $legacy_bank_files] != 0} {
    error "Legacy uram_pingpong_bank source remains in the full-shell fileset"
}
foreach source_name {
    uram_active_pool_bank.sv
    uram_shadow_ring.sv
    rtwsr_streaming_weight_store.sv
    rtwsr_9p_axi_bd.v
} {
    if {[llength [get_files -quiet -of_objects $source_set "*$source_name"]] != 1} {
        error "Current storage-path source missing or duplicated: $source_name"
    }
}
if {![file exists $input_manifest]} {
    set input_files [get_files -quiet -of_objects $source_set]
    set input_files [lsort -unique [concat $input_files [list [file join $project_dir \
        app_shell_9p.srcs/sources_1/bd/app_shell_9p/app_shell_9p.bd]]]]
    set manifest [open $input_manifest w]
    foreach source_file $input_files {
        set normalized_file [file normalize $source_file]
        puts $manifest "[lindex [exec sha256sum $normalized_file] 0]  $normalized_file"
    }
    close $manifest
}
if {![file exists $input_manifest]} {
    error "Missing synthesis source snapshot: $input_manifest"
}
exec sh -c {cd "$1" && sha256sum --check "$2"} sh $project_dir $input_manifest
set run_status [get_property STATUS [get_runs synth_1]]
if {![string match "*synth_design Complete*" $run_status]} {
    error "Full-shell synthesis is not complete: $run_status"
}
open_run synth_1
if {[current_design] ne "app_shell_9p_wrapper"} {
    error "Opened design is not the full-shell synthesis top"
}
set blackboxes [get_cells -quiet -hier -filter {IS_BLACKBOX == 1}]

set expected_instances [list \
    uram_active_pool_bank 24 \
    uram_shadow_ring 1 \
    rtwsr_streaming_weight_store 1 \
    rtwsr_top 3 \
    uram_pingpong_bank 0]
set instance_counts {}
foreach {reference expected_count} $expected_instances {
    set instances [get_cells -quiet -hier -filter "REF_NAME =~ ${reference}*"]
    set observed_count [llength $instances]
    if {$observed_count != $expected_count} {
        error "Unexpected $reference instance count: $observed_count, expected $expected_count"
    }
    lappend instance_counts $reference $observed_count
}
set cnn_instances [get_cells -quiet -hier -filter {NAME =~ *cnn_core_0}]
if {[llength $cnn_instances] != 1 ||
    [llength [get_cells -quiet -hier -filter {NAME =~ *cnn_core_1}]] != 0} {
    error "Expected exactly one retained cnn_core_0 and no cnn_core_1"
}

set utilization_path [file join $report_dir verified_current_shell_utilization_synth.rpt]
set hierarchy_path [file join $report_dir verified_current_shell_utilization_hierarchical_synth.rpt]
report_utilization -file ${utilization_path}.pending
report_utilization -hierarchical -file ${hierarchy_path}.pending
exec sh -c {cd "$1" && sha256sum --check "$2"} sh $project_dir $input_manifest
file rename -force ${utilization_path}.pending $utilization_path
file rename -force ${hierarchy_path}.pending $hierarchy_path

set status [open ${status_path}.pending w]
puts $status "VERIFICATION VERIFIED_COMPLETE"
puts $status "PROJECT_DIR $project_dir"
puts $status "SYNTH_TOP [current_design]"
puts $status "SYNTH_STATUS $run_status"
puts $status "VERIFIED_UTC [clock format [clock seconds] -gmt 1 -format {%Y-%m-%dT%H:%M:%SZ}]"
puts $status "CORE_CLOCK_BD_CONFIG_HZ 225000000"
puts $status "BLACK_BOX_COUNT [llength $blackboxes]"
puts $status "CNN_CORE_COUNT [llength $cnn_instances]"
foreach {reference observed_count} $instance_counts {
    puts $status "INSTANCE_COUNT_$reference $observed_count"
}
puts $status "INPUT_MANIFEST_SHA256 [lindex [exec sha256sum $input_manifest] 0]"
puts $status "UTILIZATION_SHA256 [lindex [exec sha256sum $utilization_path] 0]"
puts $status "HIERARCHY_SHA256 [lindex [exec sha256sum $hierarchy_path] 0]"
close $status
file rename -force ${status_path}.pending $status_path
close_project
