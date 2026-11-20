if {$argc > 0} {
    set project_dir [file normalize [lindex $argv 0]]
} else {
    set project_dir "/home/hyyuan/workspace/rtwsr_plan6_huginn_vu9p_shell_20261021"
}
set rtl_dir [file join $project_dir plan6_rtl]
if {$argc > 1} {
    set run_tag [lindex $argv 1]
} else {
    set run_tag "resourcefix_r9"
}
set core_ooc_report_dir ""
if {$argc > 2} {
    set core_ooc_report_dir [file normalize [lindex $argv 2]]
}
if {![regexp {^[A-Za-z0-9_]+$} $run_tag]} {
    error "Invalid Plan 6 run tag: $run_tag"
}
set synth_run_name "synth_1"
set impl_run_name "impl_1"
set core_run_name ""
set report_dir [file join $project_dir "plan6_reports_$run_tag"]
set ip_output_repo [file join $project_dir "plan6_ip_cache_$run_tag"]
set status_path [file join $report_dir huginn_vu9p_shell_status.txt]
set synth_state "NOT_STARTED"
set impl_state "NOT_STARTED"
file mkdir $report_dir

proc write_plan6_status {path values} {
    set channel [open "${path}.pending" w]
    dict for {key value} $values {
        puts $channel "$key $value"
    }
    close $channel
    file rename -force "${path}.pending" $path
}

proc sha256_file {path} {
    return [lindex [exec sha256sum [file normalize $path]] 0]
}

set result [catch {
    set validation_path [file join $project_dir plan6_huginn_rtwsr_bd_validation.txt]
    if {![file exists $validation_path]} {
        error "Plan 6 Block Design validation record is missing"
    }
    set validation_channel [open $validation_path r]
    set validation_text [read $validation_channel]
    close $validation_channel
    if {[string first "CORE_CLOCK_BD_CONFIG_HZ 225000000" $validation_text] < 0 ||
        [string first "RTWSR_DMA_INTERFACE" $validation_text] < 0 ||
        [string first "CNN_CORE_COUNT 0" $validation_text] < 0 ||
        [string first "axi_interconnect_1/S01_AXI" $validation_text] < 0} {
        error "Plan 6 CNN-free shell clock, CNN removal, or DDR DMA validation is missing"
    }

    open_project [file join $project_dir app_shell_9p.xpr]
    set_param general.maxThreads 8
    file mkdir $ip_output_repo
    set_property ip_output_repo $ip_output_repo [current_project]
    set constraint_set [get_filesets constrs_1]
    set board_xdc [file join $project_dir app_shell_9p.srcs/constrs_1/new/app_shell_9p.xdc]
    if {![file isfile $board_xdc]} {
        error "Plan 6 VU9P shell board constraints are missing: $board_xdc"
    }
    set board_constraints [get_files -quiet -of_objects $constraint_set $board_xdc]
    if {[llength $board_constraints] == 0} {
        add_files -fileset constrs_1 -norecurse $board_xdc
        set board_constraints [get_files -quiet -of_objects $constraint_set $board_xdc]
    }
    if {[llength $board_constraints] != 1} {
        error "Expected one active Plan 6 VU9P shell board XDC, found [llength $board_constraints]"
    }
    set cnn_constraints {}
    foreach constraint_file [get_files -quiet -of_objects $constraint_set] {
        if {[regexp -nocase {cnn} [file tail $constraint_file]]} {
            lappend cnn_constraints $constraint_file
        }
    }
    if {[llength $cnn_constraints] > 0} {
        error "CNN-only constraints remain in the Plan 6 shell: $cnn_constraints"
    }
    set bd_path [file join $project_dir \
        app_shell_9p.srcs/sources_1/bd/app_shell_9p/app_shell_9p.bd]
    if {![file exists $bd_path]} {
        error "Plan 6 shell Block Design is missing: $bd_path"
    }
    open_bd_design $bd_path
    validate_bd_design
    set cnn_cells [get_bd_cells -quiet -hier -filter {NAME =~ *cnn*}]
    if {[llength $cnn_cells] != 0 ||
        [llength [get_bd_cells -quiet clk_wiz_1]] != 0} {
        error "CNN-only cells are present in the Plan 6 shell: $cnn_cells"
    }
    set cnn_sources [get_files -quiet -of_objects [get_filesets sources_1] *cnn_core*]
    if {[llength $cnn_sources] != 0} {
        error "CNN core source files remain in the Plan 6 shell fileset: $cnn_sources"
    }
    generate_target -force all [get_files $bd_path]
    save_bd_design
    set accelerator_xci_files [get_files -all -quiet *rtwsr_9p_axi_0*.xci]
    if {[llength $accelerator_xci_files] != 1} {
        error "Expected one generated RTWSR AXI IP XCI, found [llength $accelerator_xci_files]"
    }
    set accelerator_xci [file normalize [lindex $accelerator_xci_files 0]]
    set accelerator_ip_name [file rootname [file tail $accelerator_xci]]
    set accelerator_ip_dir [file tail [file dirname $accelerator_xci]]
    set accelerator_synth [file join $project_dir \
        app_shell_9p.gen/sources_1/bd/app_shell_9p/ip/$accelerator_ip_dir/\
        synth/${accelerator_ip_name}.v]
    set core_run_name "${accelerator_ip_name}_synth_1"
    if {![file exists $accelerator_xci] || ![file exists $accelerator_synth]} {
        generate_target -force all [get_files $bd_path]
        save_bd_design
        if {![file exists $accelerator_xci] || ![file exists $accelerator_synth]} {
            error "Plan 6 AXI IP synthesis products are incomplete: $accelerator_xci $accelerator_synth"
        }
    }

    set source_set [get_filesets sources_1]
    set_property top_auto_set false $source_set
    set_property top app_shell_9p_wrapper $source_set
    set wrapper_files [get_files -quiet -of_objects $source_set *app_shell_9p_wrapper.v]
    if {[llength $wrapper_files] == 0} {
        set wrapper_file [make_wrapper -files [get_files $bd_path] -top]
        add_files -fileset $source_set -norecurse $wrapper_file
        set wrapper_files [get_files -quiet -of_objects $source_set *app_shell_9p_wrapper.v]
    }
    if {[llength $wrapper_files] != 1} {
        error "Expected one generated Plan 6 shell wrapper, found [llength $wrapper_files]"
    }
    set divider_file [file join $rtl_dir rtwsr_round_divider_7bit.sv]
    if {![file isfile $divider_file]} {
        error "Plan 6 pipelined divider source is missing: $divider_file"
    }
    set divider_matches [get_files -quiet -of_objects $source_set $divider_file]
    if {[llength $divider_matches] == 0} {
        add_files -fileset $source_set -norecurse $divider_file
        set_property file_type SystemVerilog [get_files $divider_file]
    } elseif {[llength $divider_matches] != 1} {
        error "Expected one Plan 6 pipelined divider source, found [llength $divider_matches]"
    }
    update_compile_order -fileset sources_1
    if {[get_property top $source_set] ne "app_shell_9p_wrapper"} {
        error "The Plan 6 full-shell top is not app_shell_9p_wrapper"
    }

    foreach source_name {
        rtwsr_plan6_huginn_shell.sv
        rtwsr_transformer_top.sv
        rtwsr_runtime_weight_subsystem.sv
        rtwsr_runtime_gamma_pool.sv
        rtwsr_rope_kv_cache.sv
        rtwsr_attention_gemv_unit.sv
        rtwsr_round_divider_7bit.sv
    } {
        set matches [get_files -quiet -of_objects $source_set "*$source_name"]
        if {[llength $matches] != 1} {
            error "Expected one active Plan 6 source: $source_name"
        }
    }
    set old_accelerator_files [get_files -quiet -of_objects $source_set *rtwsr_hdl/*]
    if {[llength $old_accelerator_files] != 0} {
        error "Plan 5 accelerator sources remain in the Plan 6 fileset"
    }

    set bd_path [file join $project_dir \
        app_shell_9p.srcs/sources_1/bd/app_shell_9p/app_shell_9p.bd]
    set manifest_path [file join $report_dir shell_inputs.sha256]
    set constraint_files [get_files -quiet -of_objects $constraint_set]
    set manifest_files [lsort -unique [concat \
        [get_files -quiet -of_objects $source_set] \
        $constraint_files [list $bd_path [info script]]]]
    set manifest [open $manifest_path w]
    foreach source_file $manifest_files {
        set normalized_file [file normalize $source_file]
        set generated_file 0
        foreach generated_dir {.gen/ .cache/ .runs/ .ip_user_files/ .Xil/} {
            if {[string first $generated_dir $normalized_file] >= 0} {
                set generated_file 1
                break
            }
        }
        if {[file isfile $normalized_file] && !$generated_file} {
            puts $manifest "[sha256_file $normalized_file]  $normalized_file"
        }
    }
    close $manifest
    set manifest_sha [sha256_file $manifest_path]
    set validation_sha [sha256_file $validation_path]

    reset_run $impl_run_name
    reset_run $synth_run_name
    set core_utilization [file join $report_dir ooc_utilization_synth.rpt]
    set core_hierarchy [file join $report_dir ooc_utilization_hierarchical_synth.rpt]
    set core_timing [file join $report_dir ooc_timing_synth.rpt]
    set core_ooc_manifest_sha ""
    set core_input_count 0
    set core_run [get_runs -quiet $core_run_name]
    if {[llength $core_run] == 1} {
        reset_run $core_run_name
        set synth_state "CORE_OOC_RUNNING"
        write_plan6_status $status_path [dict create \
            STATE CORE_OOC_SYNTHESIS_RUNNING PROJECT_DIR $project_dir \
            IP_OUTPUT_REPO $ip_output_repo \
            BD_VALIDATION_SHA256 $validation_sha INPUT_MANIFEST_SHA256 $manifest_sha]
        set ooc_run_dir [file join $project_dir app_shell_9p.runs $core_run_name]
        file mkdir $ooc_run_dir
        set ooc_run_log [file join $ooc_run_dir runme.log]
        set ooc_log_channel [open $ooc_run_log w]
        close $ooc_log_channel
        launch_runs $core_run_name -to_step synth_design -jobs 1
        wait_on_run $core_run_name
        set core_status [get_property STATUS $core_run]
        if {![string match "*Complete*" $core_status]} {
            error "Plan 6 accelerator OOC synthesis did not complete: $core_status"
        }
        set ooc_log_channel [open $ooc_run_log r]
        set ooc_log_text [read $ooc_log_channel]
        close $ooc_log_channel
        if {[string first "synth_design" $ooc_log_text] < 0 ||
            [string first "Synthesis finished" $ooc_log_text] < 0 ||
            [string first "Using cached IP synthesis design" $ooc_log_text] >= 0} {
            error "Plan 6 OOC run log did not prove a fresh RTL synthesis; resource report was rejected"
        }
        open_run $core_run_name
        report_utilization -file $core_utilization
        report_utilization -hierarchical -file $core_hierarchy
        report_timing_summary -file $core_timing
        close_design
        set core_status "FRESH_OOC_SYNTHESIS"
    } else {
        if {$core_ooc_report_dir eq ""} {
            error "Plan 6 accelerator OOC run is absent; provide a source-verified OOC report directory"
        }
        set source_manifest [file join $core_ooc_report_dir inputs.sha256]
        set source_utilization [file join $core_ooc_report_dir core_utilization_synth.rpt]
        set source_hierarchy [file join $core_ooc_report_dir core_utilization_hierarchical_synth.rpt]
        set source_timing [file join $core_ooc_report_dir core_timing_synth.rpt]
        foreach source_file [list $source_manifest $source_utilization $source_hierarchy $source_timing] {
            if {![file isfile $source_file]} {
                error "Plan 6 source-verified OOC report is incomplete: $source_file"
            }
        }
        set manifest_channel [open $source_manifest r]
        while {[gets $manifest_channel line] >= 0} {
            if {![regexp {^([0-9a-fA-F]{64})\s+(.+)$} $line -> expected_hash source_path]} {
                close $manifest_channel
                error "Plan 6 OOC source manifest contains an invalid row"
            }
            set source_name [file tail $source_path]
            set current_source [file join $rtl_dir $source_name]
            if {[file extension $source_name] ne ".sv" || ![file isfile $current_source] ||
                [sha256_file $current_source] ne [string tolower $expected_hash]} {
                close $manifest_channel
                error "Plan 6 OOC source does not match the current shell RTL: $source_name"
            }
            incr core_input_count
        }
        close $manifest_channel
        if {$core_input_count != 26} {
            error "Plan 6 OOC source manifest has an unexpected input count: $core_input_count"
        }
        set source_report_channel [open $source_utilization r]
        set source_report_text [read $source_report_channel]
        close $source_report_channel
        set source_hierarchy_channel [open $source_hierarchy r]
        set source_hierarchy_text [read $source_hierarchy_channel]
        close $source_hierarchy_channel
        if {![regexp {Design\s*:\s*rtwsr_transformer_top} $source_report_text] ||
            ![regexp {Device\s*:\s*xcvu9p[^[:space:]]*} $source_report_text] ||
            [string first "Design State : Synthesized" $source_report_text] < 0 ||
            [string first "rtwsr_runtime_tile_gemv" $source_hierarchy_text] < 0} {
            error "Plan 6 source-verified OOC reports do not match the VU9P recurrent core"
        }
        file copy -force $source_utilization $core_utilization
        file copy -force $source_hierarchy $core_hierarchy
        file copy -force $source_timing $core_timing
        set core_ooc_manifest_sha [sha256_file $source_manifest]
        set core_status "SOURCE_VERIFIED_OOC_REUSE"
    }

    set core_utilization_channel [open $core_utilization r]
    set core_utilization_text [read $core_utilization_channel]
    close $core_utilization_channel
    set core_hierarchy_channel [open $core_hierarchy r]
    set core_hierarchy_text [read $core_hierarchy_channel]
    close $core_hierarchy_channel
    if {![regexp {\|\s*CLB LUTs\*\s*\|\s*([0-9]+)} $core_utilization_text -> core_lut_used] ||
        ![regexp {\|\s*Block RAM Tile\s*\|\s*([0-9]+)} $core_utilization_text -> core_bram_tiles_used] ||
        ![regexp {\|\s*URAM\s*\|\s*([0-9]+)} $core_utilization_text -> core_uram_used] ||
        [string first "rtwsr_runtime_tile_gemv" $core_hierarchy_text] < 0} {
        error "Plan 6 OOC utilization report was incomplete; full-shell synthesis was not launched"
    }
    write_plan6_status $status_path [dict create \
        STATE CORE_OOC_RESOURCE_REPORT_COMPLETE PROJECT_DIR $project_dir \
        CORE_OOC_STATUS $core_status BD_VALIDATION_SHA256 $validation_sha \
        INPUT_MANIFEST_SHA256 $manifest_sha \
        OOC_SOURCE_MANIFEST_SHA256 $core_ooc_manifest_sha OOC_SOURCE_COUNT $core_input_count \
        OOC_UTILIZATION_SHA256 [sha256_file $core_utilization] \
        OOC_HIERARCHY_SHA256 [sha256_file $core_hierarchy] \
        OOC_LUT $core_lut_used OOC_BRAM_TILES $core_bram_tiles_used \
        OOC_URAM $core_uram_used]
    if {$core_lut_used > 1182240 || $core_bram_tiles_used > 648 || $core_uram_used > 832} {
        error "Plan 6 OOC pre-shell resource gate failed: LUT=$core_lut_used/1182240 BRAM_TILES=$core_bram_tiles_used/648 URAM=$core_uram_used/832; full-shell synthesis was not launched"
    }

    set synth_state "RUNNING"
    write_plan6_status $status_path [dict create \
        STATE SYNTHESIS_RUNNING PROJECT_DIR $project_dir \
        IP_OUTPUT_REPO $ip_output_repo \
        CORE_OOC_STATUS $core_status OOC_SOURCE_MANIFEST_SHA256 $core_ooc_manifest_sha \
        BD_VALIDATION_SHA256 $validation_sha \
        INPUT_MANIFEST_SHA256 $manifest_sha]
    launch_runs $synth_run_name -jobs 1
    wait_on_run $synth_run_name
    set synth_run [get_runs $synth_run_name]
    set synth_status [get_property STATUS $synth_run]
    if {![string match "*Complete*" $synth_status]} {
        error "Plan 6 shell synthesis did not complete: $synth_status"
    }
    open_run synth_1
    set synth_utilization [file join $report_dir utilization_synth.rpt]
    set synth_hierarchy [file join $report_dir utilization_hierarchical_synth.rpt]
    set synth_timing [file join $report_dir timing_synth.rpt]
    report_utilization -file $synth_utilization
    report_utilization -hierarchical -file $synth_hierarchy
    report_timing_summary -delay_type min_max -report_unconstrained -file $synth_timing
    set synth_state "COMPLETE"
    close_design

    set utilization_channel [open $synth_utilization r]
    set utilization_text [read $utilization_channel]
    close $utilization_channel
    set hierarchy_channel [open $synth_hierarchy r]
    set hierarchy_text [read $hierarchy_channel]
    close $hierarchy_channel
    if {![regexp {\|\s*CLB LUTs\*\s*\|\s*([0-9]+)} $utilization_text -> lut_used] ||
        ![regexp {\|\s*Block RAM Tile\s*\|\s*([0-9]+)} $utilization_text -> bram_tiles_used] ||
        ![regexp {\|\s*URAM\s*\|\s*([0-9]+)} $utilization_text -> uram_used]} {
        error "Plan 6 full-shell resource report could not be parsed; implementation was not launched"
    }
    if {[string first "rtwsr_runtime_tile_gemv" $hierarchy_text] < 0 ||
        [string first "cnn_core_0" $hierarchy_text] >= 0 ||
        [string first "cnncore_sys_config_0" $hierarchy_text] >= 0 ||
        $lut_used < 100000} {
        error "Plan 6 shell hierarchy report is incomplete: LUT=$lut_used; implementation was not launched"
    }
    if {$lut_used > 1182240 || $bram_tiles_used > 648 || $uram_used > 832} {
        error "Plan 6 full-shell pre-route resource gate failed: LUT=$lut_used/1182240 BRAM_TILES=$bram_tiles_used/648 URAM=$uram_used/832; implementation was not launched"
    }

    set impl_state "RUNNING"
    write_plan6_status $status_path [dict create \
        STATE IMPLEMENTATION_RUNNING PROJECT_DIR $project_dir \
        SYNTH_STATUS $synth_status BD_VALIDATION_SHA256 $validation_sha \
        CNN_CORE_COUNT 0 \
        INPUT_MANIFEST_SHA256 $manifest_sha \
        UTILIZATION_SYNTH_SHA256 [sha256_file $synth_utilization] \
        HIERARCHY_SYNTH_SHA256 [sha256_file $synth_hierarchy] \
        TIMING_SYNTH_SHA256 [sha256_file $synth_timing]]
    launch_runs $impl_run_name -to_step write_bitstream -jobs 1
    wait_on_run $impl_run_name
    set impl_run [get_runs $impl_run_name]
    set impl_status [get_property STATUS $impl_run]
    if {![string match "*Complete*" $impl_status]} {
        error "Plan 6 shell implementation did not complete: $impl_status"
    }
    open_run impl_1
    if {[current_design] ne "app_shell_9p_wrapper"} {
        error "The routed Plan 6 top is not app_shell_9p_wrapper"
    }

    set utilization [file join $report_dir utilization_postroute.rpt]
    set hierarchy [file join $report_dir utilization_hierarchical_postroute.rpt]
    set timing [file join $report_dir timing_postroute.rpt]
    set clocks [file join $report_dir clocks_postroute.rpt]
    set route_status [file join $report_dir route_status_postroute.rpt]
    set drc [file join $report_dir drc_postroute.rpt]
    set power [file join $report_dir power_postroute.rpt]
    report_utilization -file $utilization
    report_utilization -hierarchical -file $hierarchy
    report_timing_summary -delay_type min_max -report_unconstrained -file $timing
    report_clocks -file $clocks
    report_route_status -file $route_status
    report_drc -file $drc
    report_power -file $power

    set core_clocks {}
    foreach clock [get_clocks] {
        set clock_name [get_property NAME $clock]
        if {![string match -nocase "*rtwsr*" $clock_name]} {
            continue
        }
        set period_ns [get_property PERIOD $clock]
        set registers [all_registers -clock $clock]
        set paths [get_timing_paths -quiet -delay_type max -from $registers -to $registers -max_paths 1]
        if {[llength $paths] == 0} {
            lappend core_clocks "$clock_name PERIOD_NS $period_ns TIMING_PATHS 0"
        } else {
            set slack_ns [get_property SLACK [lindex $paths 0]]
            set fmax_mhz [expr {1000.0 / ($period_ns - $slack_ns)}]
            lappend core_clocks "$clock_name PERIOD_NS $period_ns WNS_NS $slack_ns FMAX_MHZ $fmax_mhz"
        }
    }
    if {[llength $core_clocks] == 0} {
        error "No Plan 6 core clock was found after routing"
    }

    set bit_files [glob -nocomplain [file join $project_dir app_shell_9p.runs $impl_run_name *.bit]]
    if {[llength $bit_files] != 1} {
        error "Expected one Plan 6 full-shell bitstream, found [llength $bit_files]"
    }
    set bitstream [file normalize [lindex $bit_files 0]]
    set impl_state "COMPLETE"
    write_plan6_status $status_path [dict create \
        STATE VERIFIED_COMPLETE PROJECT_DIR $project_dir \
        IMPLEMENTATION_TOP [current_design] SYNTH_STATUS $synth_status \
        IMPLEMENTATION_STATUS $impl_status BD_VALIDATION_SHA256 $validation_sha \
        CNN_CORE_COUNT 0 \
        INPUT_MANIFEST_SHA256 $manifest_sha BITSTREAM_PATH $bitstream \
        BITSTREAM_SHA256 [sha256_file $bitstream] \
        UTILIZATION_POSTROUTE_SHA256 [sha256_file $utilization] \
        HIERARCHY_POSTROUTE_SHA256 [sha256_file $hierarchy] \
        TIMING_POSTROUTE_SHA256 [sha256_file $timing] \
        CLOCKS_POSTROUTE_SHA256 [sha256_file $clocks] \
        ROUTE_STATUS_SHA256 [sha256_file $route_status] \
        DRC_SHA256 [sha256_file $drc] POWER_SHA256 [sha256_file $power] \
        CORE_CLOCKS $core_clocks]
    close_project
} error_text error_options]

if {$result != 0} {
    set failure_state "FAILED"
    if {[string first "OOC pre-shell resource gate failed" $error_text] >= 0} {
        set failure_state "STOPPED_OOC_RESOURCE_LIMIT"
    } elseif {[string first "full-shell pre-route resource gate failed" $error_text] >= 0} {
        set failure_state "STOPPED_SHELL_RESOURCE_LIMIT"
    }
    write_plan6_status $status_path [dict create \
        STATE $failure_state SYNTH_STATE $synth_state IMPLEMENTATION_STATE $impl_state \
        PROJECT_DIR $project_dir IP_OUTPUT_REPO $ip_output_repo ERROR $error_text]
    catch {close_project}
    return -options $error_options $error_text
}
