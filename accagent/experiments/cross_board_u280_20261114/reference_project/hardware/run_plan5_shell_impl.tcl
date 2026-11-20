set project_dir "/home/hyyuan/workspace/rtwsr_plan5_shell_20261020_next"
set report_dir [file join $project_dir plan5_reports]
set synth_status_path [file join $report_dir storagefix_shell_status.txt]
set impl_status_path [file join $report_dir storagefix_shell_impl_status.txt]
set input_manifest [file join $report_dir storagefix_shell_inputs.sha256]

proc write_status {path values} {
    set channel [open ${path}.pending w]
    dict for {key value} $values {
        puts $channel "$key $value"
    }
    close $channel
    file rename -force ${path}.pending $path
}

proc status_value {content key} {
    foreach line [split $content "\n"] {
        if {[string match "$key *" $line]} {
            return [string range $line [expr {[string length $key] + 1}] end]
        }
    }
    return ""
}

set impl_state "RUNNING"
set impl_result [catch {
    if {![file exists $synth_status_path] || ![file exists $input_manifest]} {
        error "Verified synthesis status or input manifest is missing"
    }
    set status_channel [open $synth_status_path r]
    set synth_status_content [read $status_channel]
    close $status_channel
    if {[status_value $synth_status_content VERIFICATION] ne "VERIFIED_COMPLETE" ||
        [status_value $synth_status_content PROJECT_DIR] ne $project_dir ||
        [status_value $synth_status_content SYNTH_TOP] ne "app_shell_9p_wrapper"} {
        error "The full-shell synthesis verification does not match this project"
    }
    set input_manifest_sha [lindex [exec sha256sum $input_manifest] 0]
    if {$input_manifest_sha ne [status_value $synth_status_content INPUT_MANIFEST_SHA256]} {
        error "The verified synthesis input manifest has changed"
    }
    foreach {report_key report_name} {
        UTILIZATION_SHA256 verified_current_shell_utilization_synth.rpt
        HIERARCHY_SHA256 verified_current_shell_utilization_hierarchical_synth.rpt
    } {
        set report_path [file join $report_dir $report_name]
        if {![file exists $report_path] ||
            [lindex [exec sha256sum $report_path] 0] ne
            [status_value $synth_status_content $report_key]} {
            error "The verified synthesis report is missing or changed: $report_name"
        }
    }
    exec sh -c {cd "$1" && sha256sum --check "$2"} sh $project_dir $input_manifest

    open_project [file join $project_dir app_shell_9p.xpr]
    set_param general.maxThreads 1
    set source_set [get_filesets sources_1]
    set_property top_auto_set false $source_set
    set_property top app_shell_9p_wrapper $source_set
    update_compile_order -fileset sources_1
    if {[get_property top $source_set] ne "app_shell_9p_wrapper"} {
        error "The implementation top is not app_shell_9p_wrapper"
    }
    set synth_run [get_runs synth_1]
    set synth_run_status [get_property STATUS $synth_run]
    if {![string match "*Complete*" $synth_run_status]} {
        error "The full-shell synthesis run is incomplete: $synth_run_status"
    }
    set impl_run [get_runs impl_1]
    if {[llength $impl_run] != 1} {
        error "The full-shell implementation run is missing"
    }

    launch_runs impl_1 -to_step write_bitstream -jobs 1
    wait_on_run impl_1
    set impl_run_status [get_property STATUS $impl_run]
    if {![string match "*Complete*" $impl_run_status]} {
        error "The full-shell implementation run is incomplete: $impl_run_status"
    }

    open_run impl_1
    if {[current_design] ne "app_shell_9p_wrapper"} {
        error "Opened implementation design is not app_shell_9p_wrapper"
    }
    set utilization_path [file join $report_dir verified_current_shell_utilization_postroute.rpt]
    set hierarchy_path [file join $report_dir verified_current_shell_utilization_hierarchical_postroute.rpt]
    set timing_path [file join $report_dir verified_current_shell_timing_postroute.rpt]
    set clocks_path [file join $report_dir verified_current_shell_clocks_postroute.rpt]
    set route_path [file join $report_dir verified_current_shell_route_status.rpt]
    set drc_path [file join $report_dir verified_current_shell_drc.rpt]
    set power_path [file join $report_dir verified_current_shell_power.rpt]
    report_utilization -file $utilization_path
    report_utilization -hierarchical -file $hierarchy_path
    report_timing_summary -delay_type min_max -report_unconstrained -file $timing_path
    report_clocks -file $clocks_path
    report_route_status -file $route_path
    report_drc -file $drc_path
    report_power -file $power_path

    set core_clock_records {}
    set core_clock_index 0
    foreach clock [get_clocks] {
        set clock_name [get_property NAME $clock]
        if {![string match -nocase "*rtwsr*" $clock_name]} {
            continue
        }
        set period_ns [get_property PERIOD $clock]
        set registers [all_registers -clock $clock]
        set paths [get_timing_paths -quiet -delay_type max -from $registers -to $registers -max_paths 1]
        if {[llength $paths] == 0} {
            lappend core_clock_records "CORE_CLOCK_${core_clock_index}_NAME $clock_name"
            lappend core_clock_records "CORE_CLOCK_${core_clock_index}_PERIOD_NS $period_ns"
            lappend core_clock_records "CORE_CLOCK_${core_clock_index}_TIMING_PATHS 0"
        } else {
            set slack_ns [get_property SLACK [lindex $paths 0]]
            set limiting_period_ns [expr {$period_ns - $slack_ns}]
            set fmax_mhz [expr {1000.0 / $limiting_period_ns}]
            lappend core_clock_records "CORE_CLOCK_${core_clock_index}_NAME $clock_name"
            lappend core_clock_records "CORE_CLOCK_${core_clock_index}_PERIOD_NS $period_ns"
            lappend core_clock_records "CORE_CLOCK_${core_clock_index}_WNS_NS $slack_ns"
            lappend core_clock_records "CORE_CLOCK_${core_clock_index}_FMAX_MHZ $fmax_mhz"
            report_timing -delay_type max -from $registers -to $registers -max_paths 10 -nworst 1 \
                -path_type full_clock_expanded \
                -file [file join $report_dir verified_current_core_clock_${core_clock_index}_paths_postroute.rpt]
        }
        incr core_clock_index
    }
    if {$core_clock_index == 0} {
        error "No RTWSR core clock was found in the routed design"
    }

    set bit_files [glob -nocomplain [file join $project_dir app_shell_9p.runs impl_1 *.bit]]
    if {[llength $bit_files] != 1} {
        error "Expected one full-shell bitstream, found [llength $bit_files]"
    }
    set bit_file [file normalize [lindex $bit_files 0]]
    set bit_sha [lindex [exec sha256sum $bit_file] 0]
    set result_status [dict create \
        VERIFICATION VERIFIED_COMPLETE \
        PROJECT_DIR $project_dir \
        IMPLEMENTATION_TOP [current_design] \
        SYNTH_STATUS $synth_run_status \
        IMPLEMENTATION_STATUS $impl_run_status \
        INPUT_MANIFEST_SHA256 $input_manifest_sha \
        BITSTREAM_PATH $bit_file \
        BITSTREAM_SHA256 $bit_sha \
        UTILIZATION_POSTROUTE_SHA256 [lindex [exec sha256sum $utilization_path] 0] \
        HIERARCHY_POSTROUTE_SHA256 [lindex [exec sha256sum $hierarchy_path] 0] \
        TIMING_POSTROUTE_SHA256 [lindex [exec sha256sum $timing_path] 0] \
        CLOCKS_POSTROUTE_SHA256 [lindex [exec sha256sum $clocks_path] 0] \
        ROUTE_STATUS_SHA256 [lindex [exec sha256sum $route_path] 0] \
        DRC_SHA256 [lindex [exec sha256sum $drc_path] 0] \
        POWER_SHA256 [lindex [exec sha256sum $power_path] 0]]
    foreach record $core_clock_records {
        lappend result_status {*}$record
    }
    write_status $impl_status_path $result_status
    set impl_state "VERIFIED_COMPLETE"
    close_project
} impl_error impl_options]

if {$impl_result != 0} {
    write_status $impl_status_path [dict create \
        VERIFICATION IMPLEMENTATION_FAILED \
        PROJECT_DIR $project_dir \
        IMPLEMENTATION_STATE $impl_state]
    catch {close_project}
    return -options $impl_options $impl_error
}
