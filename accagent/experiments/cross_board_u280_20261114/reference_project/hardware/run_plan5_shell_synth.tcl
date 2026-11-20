set project_dir "/home/hyyuan/workspace/rtwsr_plan5_shell_20261020_next"
set report_dir [file join $project_dir plan5_reports]
file mkdir $report_dir
set status_path [file join $report_dir storagefix_shell_status.txt]
set status_file [open $status_path w]
puts $status_file "VERIFICATION RUNNING"
puts $status_file "PROJECT_DIR $project_dir"
puts $status_file "SYNTH_TOP app_shell_9p_wrapper"
puts $status_file "STARTED_UTC [clock format [clock seconds] -gmt 1 -format {%Y-%m-%dT%H:%M:%SZ}]"
close $status_file

open_project [file join $project_dir app_shell_9p.xpr]
set_param general.maxThreads 1

set source_set [get_filesets sources_1]
set_property top_auto_set false $source_set
set_property top app_shell_9p_wrapper $source_set
update_compile_order -fileset sources_1
if {[get_property top $source_set] ne "app_shell_9p_wrapper"} {
    error "The full-shell synthesis top is not app_shell_9p_wrapper"
}

foreach source_name {
    uram_active_pool_bank.sv
    uram_shadow_ring.sv
    rtwsr_streaming_weight_store.sv
    rtwsr_9p_axi_bd.v
} {
    set source_matches [get_files -quiet -of_objects $source_set "*$source_name"]
    if {[llength $source_matches] != 1} {
        error "Expected exactly one current storage-path source: $source_name"
    }
}
set legacy_bank_files [get_files -quiet -of_objects $source_set *uram_pingpong_bank.sv]
if {[llength $legacy_bank_files] != 0} {
    error "Legacy uram_pingpong_bank source remains in the full-shell fileset"
}

set input_files [get_files -quiet -of_objects $source_set]
set input_files [lsort -unique [concat $input_files [list [file join $project_dir \
    app_shell_9p.srcs/sources_1/bd/app_shell_9p/app_shell_9p.bd]]]]
set manifest [open [file join $report_dir storagefix_shell_inputs.sha256] w]
foreach source_file [lsort $input_files] {
    set normalized_file [file normalize $source_file]
    puts $manifest "[lindex [exec sha256sum $normalized_file] 0]  $normalized_file"
}
close $manifest

reset_run synth_1
launch_runs synth_1 -jobs 1
wait_on_run synth_1

source [file join [file dirname [info script]] report_plan5_shell_synth.tcl]
