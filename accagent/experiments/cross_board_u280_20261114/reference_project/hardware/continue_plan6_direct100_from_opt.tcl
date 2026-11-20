set project_dir "/home/hyyuan/workspace/rtwsr_plan6_huginn_vu9p_direct_20261026"
set report_dir [file join $project_dir plan6_reports_attn_qkv_100mhz]
set shell_base_dir "/home/hyyuan/workspace/rtwsr_plan6_huginn_vu9p_shell_20261025_ctrl_d"
set shell_base_manifest [file join $shell_base_dir plan6_reports_ctrl_d_full shell_inputs.sha256]
set clone_manifest [file join $report_dir writable_shell_inputs.sha256]
set source_manifest [file join $project_dir source_inputs.sha256]
set core_run_dir [file join $project_dir core_synth]
set core_checkpoint [file join $core_run_dir app_shell_9p_rtwsr_9p_axi_0_6.dcp]
set opt_checkpoint [file join $report_dir app_shell_9p_wrapper_opt_direct100.dcp]
set prior_manifest [file join $report_dir implementation_inputs_pre_recovery.sha256]
set implementation_manifest [file join $report_dir implementation_inputs.sha256]
set saved_project_dir [file join $report_dir saved_opt_project_direct100]
set status_path [file join $report_dir huginn_vu9p_shell_status.txt]
set expected_source_sha "899bbb48b2393cef695f15c2b0e16265254316926e928e73a8b801872c2a8558"
set expected_shell_sha "25dfadd6d2918db51387a5fd328b5635a41bcfa5700f87d94db94602c61c2bdc"
set expected_clone_sha "1f6c695fb1dab5c14aba9b90d732d67b9e916440cdfe5569eb5a35aad9835405"
set expected_core_sha "b3f063d1802539ce9eaf8d5a519f26148191d0060897de20692ae7685c5c1d88"
set expected_prior_manifest_sha "15df2d438ea41e4716d3520390e80efd32aa6f3b726f17b974f5ba35fdc6e492"
set expected_opt_sha "1c9e84ed49a75b881013c16ac11a54931e7149441b5dcd259ff2de6544baa007"

proc sha256_file {path} {
    return [lindex [exec sha256sum [file normalize $path]] 0]
}

proc record_state {state args} {
    global status_path project_dir expected_source_sha expected_shell_sha expected_core_sha
    set channel [open "${status_path}.pending" w]
    puts $channel "STATE $state"
    puts $channel "PROJECT_DIR $project_dir"
    puts $channel "INPUT_MANIFEST_SHA256 $expected_source_sha"
    puts $channel "SHELL_BASE_INPUT_MANIFEST_SHA256 $expected_shell_sha"
    puts $channel "SOURCE_CORE_CHECKPOINT_SHA256 $expected_core_sha"
    puts $channel "CORE_CLOCK_TARGET_MHZ 100"
    puts $channel "CNN_CORE_COUNT 0"
    puts $channel "QKV_IMPLEMENTATION PIPELINED_BRAM"
    foreach {key value} $args { puts $channel "$key $value" }
    close $channel
    file rename -force "${status_path}.pending" $status_path
}

set result [catch {
    set report_resource [file join $report_dir utilization_linked_synth.rpt]
    if {[sha256_file $source_manifest] ne $expected_source_sha ||
        [sha256_file $shell_base_manifest] ne $expected_shell_sha ||
        [sha256_file $clone_manifest] ne $expected_clone_sha ||
        [sha256_file $core_checkpoint] ne $expected_core_sha ||
        [sha256_file $opt_checkpoint] ne $expected_opt_sha ||
        [sha256_file $implementation_manifest] ne $expected_prior_manifest_sha} {
        error "A direct100 source, shell, core, opt checkpoint, or prior manifest hash changed"
    }
    exec sha256sum -c --status $source_manifest
    exec sha256sum -c --status $shell_base_manifest
    exec sha256sum -c --status $clone_manifest
    exec sha256sum -c --status $implementation_manifest
    if {[sha256_file $report_resource] ne "416d1555043f0e97045f85a45e47ebb71bd4cc4ff95632577ef698a2196ddfec"} {
        error "The linked shell resource report does not match the direct100 run"
    }
    if {![file exists $prior_manifest]} {
        file copy $implementation_manifest $prior_manifest
    }
    if {[sha256_file $prior_manifest] ne $expected_prior_manifest_sha} {
        error "The preserved pre-recovery manifest identity changed"
    }

    record_state RECOVERING_FROM_OPT CORE_CLOCK_CONFIG_MHZ 100 \
        IMPLEMENTATION_INPUTS_SHA256 $expected_prior_manifest_sha \
        OPT_CHECKPOINT_PATH $opt_checkpoint OPT_CHECKPOINT_SHA256 $expected_opt_sha
    open_checkpoint $opt_checkpoint
    file mkdir $saved_project_dir
    save_project_as -force plan6_direct100_from_opt $saved_project_dir
    implement_debug_core
    if {[llength [get_cells -hier -quiet -filter {IS_BLACKBOX == 1}]] != 0} {
        error "The saved opt checkpoint still contains a black box"
    }

    set core_mmcm [get_cells -hier -filter {REF_NAME == MMCME4_ADV && NAME =~ *rtwsr_core_clk_wiz*}]
    if {[llength $core_mmcm] != 1} { error "Expected one recurrent-core MMCM" }
    set core_clock [get_clocks -of_objects [get_pins $core_mmcm/CLKOUT0]]
    if {[llength $core_clock] != 1 || abs([get_property PERIOD $core_clock] - 10.0) > 0.001} {
        error "The saved checkpoint does not carry the recurrent-core 100 MHz clock"
    }
    set core_registers [filter [all_registers -clock $core_clock] {NAME =~ *u_recurrent_core/*}]
    set core_setup_path [get_timing_paths -delay_type max -from $core_registers \
        -to $core_registers -max_paths 1]
    if {[llength $core_registers] == 0 || [llength $core_setup_path] != 1} {
        error "The saved checkpoint has no constrained recurrent-core setup path"
    }
    report_clocks -file [file join $report_dir clocks_before_placement.rpt]
    report_timing_summary -delay_type min_max -report_unconstrained \
        -file [file join $report_dir timing_before_placement.rpt]

    set channel [open $implementation_manifest w]
    set input_channel [open $prior_manifest r]
    while {[gets $input_channel line] >= 0} {
        if {[string trim $line] ne ""} { puts $channel $line }
    }
    close $input_channel
    foreach path [list [info script] $prior_manifest $opt_checkpoint] {
        puts $channel "[sha256_file $path]  [file normalize $path]"
    }
    close $channel
    set implementation_sha [sha256_file $implementation_manifest]
    exec sha256sum -c --status $implementation_manifest
    exec sha256sum -c --status $source_manifest
    exec sha256sum -c --status $shell_base_manifest
    exec sha256sum -c --status $clone_manifest

    record_state PLACEMENT_RUNNING CORE_CLOCK_CONFIG_MHZ 100 \
        CORE_REGISTER_COUNT [llength $core_registers] \
        IMPLEMENTATION_INPUTS_SHA256 $implementation_sha \
        OPT_CHECKPOINT_PATH $opt_checkpoint OPT_CHECKPOINT_SHA256 $expected_opt_sha
    place_design -directive ExtraPostPlacementOpt
    report_utilization -file [file join $report_dir utilization_placed.rpt]
    set placed_checkpoint [file join $report_dir app_shell_9p_wrapper_placed_direct100.dcp]
    write_checkpoint -force $placed_checkpoint
    record_state PLACEMENT_COMPLETE CORE_CLOCK_CONFIG_MHZ 100 \
        IMPLEMENTATION_INPUTS_SHA256 $implementation_sha \
        PLACED_CHECKPOINT_PATH $placed_checkpoint \
        PLACED_CHECKPOINT_SHA256 [sha256_file $placed_checkpoint]

    record_state PHYS_OPT_RUNNING CORE_CLOCK_CONFIG_MHZ 100 \
        IMPLEMENTATION_INPUTS_SHA256 $implementation_sha
    phys_opt_design -directive AggressiveExplore
    set physopt_checkpoint [file join $report_dir app_shell_9p_wrapper_physopt_direct100.dcp]
    write_checkpoint -force $physopt_checkpoint
    record_state PHYS_OPT_COMPLETE CORE_CLOCK_CONFIG_MHZ 100 \
        IMPLEMENTATION_INPUTS_SHA256 $implementation_sha \
        PHYSOPT_CHECKPOINT_PATH $physopt_checkpoint \
        PHYSOPT_CHECKPOINT_SHA256 [sha256_file $physopt_checkpoint]

    record_state ROUTE_RUNNING CORE_CLOCK_CONFIG_MHZ 100 \
        IMPLEMENTATION_INPUTS_SHA256 $implementation_sha
    route_design -directive AlternateCLBRouting
    report_timing_summary -delay_type min_max -report_unconstrained \
        -file [file join $report_dir timing_postroute.rpt]
    report_utilization -file [file join $report_dir utilization_postroute.rpt]
    report_utilization -hierarchical -file [file join $report_dir utilization_hierarchical_postroute.rpt]
    report_route_status -file [file join $report_dir route_status_postroute.rpt]
    report_drc -file [file join $report_dir drc_postroute.rpt]
    report_clocks -file [file join $report_dir clocks_postroute.rpt]
    report_power -file [file join $report_dir power_postroute.rpt]
    report_timing -delay_type max -from $core_registers -to $core_registers \
        -max_paths 20 -nworst 1 -file [file join $report_dir core_paths_postroute.rpt]
    set setup_path [get_timing_paths -delay_type max -from $core_registers \
        -to $core_registers -max_paths 1]
    set hold_path [get_timing_paths -delay_type min -from $core_registers \
        -to $core_registers -max_paths 1]
    if {[llength $setup_path] != 1 || [llength $hold_path] != 1} {
        error "The routed design has no complete core setup/hold paths"
    }
    set setup_slack [get_property SLACK $setup_path]
    set hold_slack [get_property SLACK $hold_path]
    set timing_channel [open [file join $report_dir timing_postroute.rpt] r]
    set timing_text [read $timing_channel]
    close $timing_channel
    set shell_timing_met [expr {[string first "All user specified timing constraints are met." $timing_text] >= 0}]
    set routed_checkpoint [file join $report_dir app_shell_9p_wrapper_routed_direct100.dcp]
    write_checkpoint -force $routed_checkpoint
    if {$setup_slack < 0 || $hold_slack < 0} {
        record_state CORE_TIMING_NOT_MET CORE_CLOCK_CONFIG_MHZ 100 \
            CORE_SETUP_WNS_NS $setup_slack CORE_HOLD_WHS_NS $hold_slack \
            SHELL_TIMING_CONSTRAINTS_MET $shell_timing_met \
            IMPLEMENTATION_INPUTS_SHA256 $implementation_sha \
            ROUTED_CHECKPOINT_PATH $routed_checkpoint \
            ROUTED_CHECKPOINT_SHA256 [sha256_file $routed_checkpoint]
    } else {
        set bitstream [file join $report_dir app_shell_9p_wrapper.bit]
        write_bitstream -force $bitstream
        exec sha256sum -c --status $source_manifest
        exec sha256sum -c --status $shell_base_manifest
        exec sha256sum -c --status $clone_manifest
        exec sha256sum -c --status $implementation_manifest
        record_state CORE_100MHZ_ROUTED CORE_CLOCK_CONFIG_MHZ 100 \
            CORE_SETUP_WNS_NS $setup_slack CORE_HOLD_WHS_NS $hold_slack \
            SHELL_TIMING_CONSTRAINTS_MET $shell_timing_met \
            IMPLEMENTATION_INPUTS_SHA256 $implementation_sha \
            UTILIZATION_POSTROUTE_SHA256 [sha256_file [file join $report_dir utilization_postroute.rpt]] \
            HIERARCHY_POSTROUTE_SHA256 [sha256_file [file join $report_dir utilization_hierarchical_postroute.rpt]] \
            TIMING_POSTROUTE_SHA256 [sha256_file [file join $report_dir timing_postroute.rpt]] \
            CLOCKS_POSTROUTE_SHA256 [sha256_file [file join $report_dir clocks_postroute.rpt]] \
            ROUTE_STATUS_SHA256 [sha256_file [file join $report_dir route_status_postroute.rpt]] \
            DRC_SHA256 [sha256_file [file join $report_dir drc_postroute.rpt]] \
            POWER_SHA256 [sha256_file [file join $report_dir power_postroute.rpt]] \
            BITSTREAM_PATH $bitstream BITSTREAM_SHA256 [sha256_file $bitstream]
    }
    close_project
} error_text error_options]
if {$result != 0} {
    record_state FAILED OPERATION_RESULT $error_text
    catch {close_project}
    return -options $error_options $error_text
}
