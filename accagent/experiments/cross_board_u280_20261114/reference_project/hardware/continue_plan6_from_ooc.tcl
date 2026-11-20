if {$argc != 3} {
    error "usage: vivado -mode batch -source continue_plan6_from_ooc.tcl -tclargs <project_dir> <run_tag> <ooc_checkpoint>"
}
set project_dir [file normalize [lindex $argv 0]]
set run_tag [lindex $argv 1]
set checkpoint [file normalize [lindex $argv 2]]
set report_dir [file join $project_dir "plan6_reports_$run_tag"]
set ip_output_repo [file join $project_dir "plan6_ip_cache_$run_tag"]
set status_path [file join $report_dir huginn_vu9p_shell_status.txt]
set ip_dir [file join $project_dir app_shell_9p.gen/sources_1/bd/app_shell_9p/ip/app_shell_9p_rtwsr_9p_axi_0_6]
if {![file isfile $checkpoint]} {
    error "OOC checkpoint is missing: $checkpoint"
}
file mkdir $report_dir
proc sha256_file {path} { return [lindex [exec sha256sum [file normalize $path]] 0] }
proc write_status {path values} {
    set ch [open "${path}.pending" w]
    dict for {key value} $values { puts $ch "$key $value" }
    close $ch
    file rename -force "${path}.pending" $path
}
set result [catch {
    open_project [file join $project_dir app_shell_9p.xpr]
    set_param general.maxThreads 8
    set_property verilog_define {SYNTH_CARRY8 XILINX_XPM} [current_fileset]
    set_property ip_output_repo $ip_output_repo [current_project]

    # The checkpoint was produced by the current fresh OOC synthesis. Copy only
    # the artifacts required by the shell IP; simulation VHDL is not required.
    file mkdir $ip_dir
    file copy -force $checkpoint [file join $ip_dir app_shell_9p_rtwsr_9p_axi_0_6.dcp]
    foreach artifact {
        app_shell_9p_rtwsr_9p_axi_0_6_stub.v
        app_shell_9p_rtwsr_9p_axi_0_6_stub.vhdl
        app_shell_9p_rtwsr_9p_axi_0_6_sim_netlist.v
    } {
        set source [file join [file dirname $checkpoint] $artifact]
        if {[file isfile $source]} {
            file copy -force $source [file join $ip_dir $artifact]
        }
    }

    foreach pair {
        {checkpoint_reports/checkpoint_utilization_synth.rpt ooc_utilization_synth.rpt}
        {checkpoint_reports/checkpoint_utilization_hierarchical_synth.rpt ooc_utilization_hierarchical_synth.rpt}
        {checkpoint_reports/checkpoint_timing_synth.rpt ooc_timing_synth.rpt}
    } {
        set source [file join $report_dir [lindex $pair 0]]
        set target [file join $report_dir [lindex $pair 1]]
        if {![file isfile $source]} { error "checkpoint report is missing: $source" }
        file copy -force $source $target
    }
    set core_utilization [file join $report_dir ooc_utilization_synth.rpt]
    set core_hierarchy [file join $report_dir ooc_utilization_hierarchical_synth.rpt]
    set core_timing [file join $report_dir ooc_timing_synth.rpt]
    set utilization_text [read [open $core_utilization r]]
    set hierarchy_text [read [open $core_hierarchy r]]
    if {![regexp {\|\s*CLB LUTs\*\s*\|\s*([0-9]+)} $utilization_text -> core_lut] ||
        ![regexp {\|\s*Block RAM Tile\s*\|\s*([0-9]+)} $utilization_text -> core_bram] ||
        ![regexp {\|\s*URAM\s*\|\s*([0-9]+)} $utilization_text -> core_uram] ||
        [string first "rtwsr_runtime_tile_gemv" $hierarchy_text] < 0} {
        error "checkpoint OOC report cannot be parsed"
    }
    if {$core_lut > 1182240 || $core_bram > 648 || $core_uram > 832} {
        error "OOC resource gate failed: LUT=$core_lut BRAM=$core_bram URAM=$core_uram"
    }
    set manifest_path [file join $report_dir shell_inputs.sha256]
    set manifest_sha [sha256_file $manifest_path]
    set validation_path [file join $project_dir plan6_huginn_rtwsr_bd_validation.txt]
    set validation_sha [sha256_file $validation_path]
    write_status $status_path [dict create \
        STATE CORE_OOC_RESOURCE_REPORT_COMPLETE PROJECT_DIR $project_dir \
        CORE_OOC_STATUS CHECKPOINT_RECOVERY_BYPASS \
        BD_VALIDATION_SHA256 $validation_sha INPUT_MANIFEST_SHA256 $manifest_sha \
        OOC_UTILIZATION_SHA256 [sha256_file $core_utilization] \
        OOC_HIERARCHY_SHA256 [sha256_file $core_hierarchy] \
        OOC_LUT $core_lut OOC_BRAM_TILES $core_bram OOC_URAM $core_uram]

    set synth_run [get_runs synth_1]
    set impl_run [get_runs impl_1]
    reset_run synth_1
    reset_run impl_1
    set_property STEPS.SYNTH_DESIGN.ARGS.DIRECTIVE Default $synth_run
    set_property STEPS.SYNTH_DESIGN.ARGS.CONTROL_SET_OPT_THRESHOLD 16 $synth_run
    set_property STEPS.SYNTH_DESIGN.ARGS.RETIMING false $synth_run
    set_property STEPS.PLACE_DESIGN.ARGS.DIRECTIVE ExtraPostPlacementOpt $impl_run
    set_property STEPS.PHYS_OPT_DESIGN.ARGS.DIRECTIVE AggressiveExplore $impl_run
    set_property STEPS.ROUTE_DESIGN.ARGS.DIRECTIVE AlternateCLBRouting $impl_run

    write_status $status_path [dict create STATE SYNTHESIS_RUNNING PROJECT_DIR $project_dir \
        CORE_OOC_STATUS CHECKPOINT_RECOVERY_BYPASS BD_VALIDATION_SHA256 $validation_sha \
        INPUT_MANIFEST_SHA256 $manifest_sha]
    launch_runs synth_1 -jobs 1
    wait_on_run synth_1
    if {![string match "*Complete*" [get_property STATUS $synth_run]]} {
        error "shell synthesis did not complete: [get_property STATUS $synth_run]"
    }
    open_run synth_1
    set synth_utilization [file join $report_dir utilization_synth.rpt]
    set synth_hierarchy [file join $report_dir utilization_hierarchical_synth.rpt]
    set synth_timing [file join $report_dir timing_synth.rpt]
    report_utilization -file $synth_utilization
    report_utilization -hierarchical -file $synth_hierarchy
    report_timing_summary -delay_type min_max -report_unconstrained -file $synth_timing
    set synth_text [read [open $synth_utilization r]]
    set shell_lut 0
    set shell_bram 0
    set shell_uram 0
    if {![regexp {\|\s*CLB LUTs\*\s*\|\s*([0-9]+)} $synth_text -> shell_lut] ||
        ![regexp {\|\s*Block RAM Tile\s*\|\s*([0-9]+)} $synth_text -> shell_bram] ||
        ![regexp {\|\s*URAM\s*\|\s*([0-9]+)} $synth_text -> shell_uram]} {
        error "shell utilization report cannot be parsed"
    }
    if {$shell_lut > 1182240 || $shell_bram > 648 || $shell_uram > 832} {
        error "shell pre-route resource gate failed: LUT=$shell_lut BRAM=$shell_bram URAM=$shell_uram"
    }
    close_design

    write_status $status_path [dict create STATE IMPLEMENTATION_RUNNING PROJECT_DIR $project_dir \
        SYNTH_STATUS COMPLETE CORE_OOC_STATUS CHECKPOINT_RECOVERY_BYPASS CNN_CORE_COUNT 0 \
        BD_VALIDATION_SHA256 $validation_sha INPUT_MANIFEST_SHA256 $manifest_sha \
        UTILIZATION_SYNTH_SHA256 [sha256_file $synth_utilization] \
        HIERARCHY_SYNTH_SHA256 [sha256_file $synth_hierarchy] \
        TIMING_SYNTH_SHA256 [sha256_file $synth_timing]]
    launch_runs impl_1 -to_step write_bitstream -jobs 1
    wait_on_run impl_1
    set impl_status [get_property STATUS $impl_run]
    if {![string match "*Complete*" $impl_status]} {
        error "shell implementation did not complete: $impl_status"
    }
    open_run impl_1
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
    set bit_files [glob -nocomplain [file join $project_dir app_shell_9p.runs impl_1 *.bit]]
    if {[llength $bit_files] != 1} { error "expected one bitstream, found [llength $bit_files]" }
    set bitstream [file normalize [lindex $bit_files 0]]
    write_status $status_path [dict create STATE VERIFIED_COMPLETE PROJECT_DIR $project_dir \
        IMPLEMENTATION_TOP app_shell_9p_wrapper SYNTH_STATUS COMPLETE IMPLEMENTATION_STATUS $impl_status \
        BD_VALIDATION_SHA256 $validation_sha CNN_CORE_COUNT 0 INPUT_MANIFEST_SHA256 $manifest_sha \
        BITSTREAM_PATH $bitstream BITSTREAM_SHA256 [sha256_file $bitstream] \
        UTILIZATION_POSTROUTE_SHA256 [sha256_file $utilization] \
        HIERARCHY_POSTROUTE_SHA256 [sha256_file $hierarchy] TIMING_POSTROUTE_SHA256 [sha256_file $timing] \
        CLOCKS_POSTROUTE_SHA256 [sha256_file $clocks] ROUTE_STATUS_SHA256 [sha256_file $route_status] \
        DRC_SHA256 [sha256_file $drc] POWER_SHA256 [sha256_file $power]]
    close_design
    close_project
} error_text error_options]
if {$result != 0} {
    write_status $status_path [dict create STATE FAILED PROJECT_DIR $project_dir ERROR $error_text]
    catch {close_project}
    return -options $error_options $error_text
}
