if {$argc != 5} {
    error "usage: route_plan6_fanoutopt_candidate.tcl <placed-checkpoint> <output-dir> <input-manifest> <manifest-sha256> <postroute-path-report>"
}

set checkpoint [file normalize [lindex $argv 0]]
set output_dir [file normalize [lindex $argv 1]]
set input_manifest [file normalize [lindex $argv 2]]
set expected_manifest_sha [lindex $argv 3]
set postroute_path_report [file normalize [lindex $argv 4]]
set status_path [file join $output_dir implementation_status.txt]
set snapshot_dir [file normalize [file join [file dirname $input_manifest] .. snapshot]]
set snapshot_source_manifest [file join $snapshot_dir source_inputs.sha256]
set original_source_manifest [file join $snapshot_dir original_source_inputs.sha256]
set original_implementation_manifest [file join $snapshot_dir spread_implementation_inputs.sha256]
file mkdir $output_dir
set_param general.maxThreads 8

proc sha256_file {path} {
    return [lindex [exec sha256sum [file normalize $path]] 0]
}

proc record_state {path state args} {
    set channel [open "${path}.pending" w]
    puts $channel "STATE $state"
    foreach {key value} $args { puts $channel "$key $value" }
    close $channel
    file rename -force "${path}.pending" $path
}

proc check_memory_caps {} {
    set uram_count [llength [get_cells -hier -quiet -filter {REF_NAME == URAM288}]]
    set bram_count [llength [get_cells -hier -quiet -filter {REF_NAME == RAMB36E2}]]
    if {$uram_count > 832 || $bram_count > 648} {
        error "Plan 6 memory cap exceeded: URAM=$uram_count/832 RAMB36E2=$bram_count/648"
    }
    return [list $uram_count $bram_count]
}

set stage PREFLIGHT
set result [catch {
    if {[file exists $status_path] || ![file isfile $checkpoint] ||
        ![file isfile $postroute_path_report] || ![file isfile $input_manifest] ||
        ![file isfile $snapshot_source_manifest] || ![file isfile $original_source_manifest] ||
        ![file isfile $original_implementation_manifest] ||
        [sha256_file $input_manifest] ne $expected_manifest_sha} {
        error "The candidate output already exists or an immutable input is missing or changed"
    }
    exec sha256sum -c --status $input_manifest
    exec sha256sum -c --status $snapshot_source_manifest
    exec sha256sum -c --status $original_source_manifest
    exec sha256sum -c --status $original_implementation_manifest

    open_checkpoint $checkpoint
    lassign [check_memory_caps] uram_before bram_before
    set core_mmcm [get_cells -hier -quiet -filter {REF_NAME == MMCME4_ADV && NAME =~ *rtwsr_core_clk_wiz*}]
    if {[llength $core_mmcm] != 1} {
        error "Expected one recurrent-core MMCM in the placed checkpoint"
    }
    set core_clock [get_clocks -of_objects [get_pins [lindex $core_mmcm 0]/CLKOUT0]]
    if {[llength $core_clock] != 1 || abs([get_property PERIOD $core_clock] - 10.0) > 0.001} {
        error "The placed checkpoint does not carry the Plan 6 100 MHz core clock"
    }
    set core_registers [filter [all_registers -clock $core_clock] {NAME =~ *u_recurrent_core/*}]
    set setup_path [get_timing_paths -quiet -delay_type max -from $core_registers \
        -to $core_registers -max_paths 1]
    if {[llength $core_registers] == 0 || [llength $setup_path] != 1} {
        error "The placed checkpoint has no constrained recurrent-core setup path"
    }
    set start_slack [get_property SLACK [lindex $setup_path 0]]
    set start_fmax [expr {1000.0 / (10.0 - $start_slack)}]
    report_utilization -file [file join $output_dir utilization_before_physopt.rpt]
    report_timing_summary -delay_type min_max -report_unconstrained \
        -file [file join $output_dir timing_before_physopt.rpt]
    report_timing -delay_type max -from $core_registers -to $core_registers \
        -max_paths 20 -nworst 1 -file [file join $output_dir core_paths_before_physopt.rpt]

    set stage_report [open $postroute_path_report r]
    set evidence [read $stage_report]
    close $stage_report
    if {[string first "net (fo=336, routed)" $evidence] < 0 ||
        [string first "read_error_q6/DSP_A_B_DATA_INST" $evidence] < 0 ||
        [string first "gen_pool_bank\[17\].u_pool_bank/gen_uram_lane\[5\]" $evidence] < 0} {
        error "The immutable route report does not identify the reported high-fanout pool address path"
    }

    set stage PHYS_OPT_DESIGN
    record_state $status_path PHYS_OPT_RUNNING \
        SOURCE_CHECKPOINT $checkpoint SOURCE_CHECKPOINT_SHA256 [sha256_file $checkpoint] \
        INPUT_MANIFEST $input_manifest INPUT_MANIFEST_SHA256 $expected_manifest_sha \
        CORE_CLOCK_TARGET_MHZ 100 CORE_START_WNS_NS $start_slack CORE_START_FMAX_MHZ $start_fmax \
        URAM_BEFORE $uram_before RAMB36E2_BEFORE $bram_before \
        TARGET_ADDRESS_NET_FANOUT 336 PHYS_OPT_DIRECTIVE AggressiveFanoutOpt \
        ROUTE_DIRECTIVE AlternateCLBRouting
    phys_opt_design -directive AggressiveFanoutOpt
    set physopt_checkpoint [file join $output_dir app_shell_9p_wrapper_physopt_fanoutopt.dcp]
    write_checkpoint -force $physopt_checkpoint
    report_timing_summary -delay_type min_max -report_unconstrained \
        -file [file join $output_dir timing_physopt.rpt]
    record_state $status_path PHYS_OPT_COMPLETE \
        SOURCE_CHECKPOINT $checkpoint SOURCE_CHECKPOINT_SHA256 [sha256_file $checkpoint] \
        INPUT_MANIFEST_SHA256 $expected_manifest_sha \
        PHYSOPT_CHECKPOINT $physopt_checkpoint PHYSOPT_CHECKPOINT_SHA256 [sha256_file $physopt_checkpoint]

    set stage ROUTE_DESIGN
    record_state $status_path ROUTE_RUNNING \
        SOURCE_CHECKPOINT $checkpoint SOURCE_CHECKPOINT_SHA256 [sha256_file $checkpoint] \
        INPUT_MANIFEST_SHA256 $expected_manifest_sha \
        PHYSOPT_CHECKPOINT $physopt_checkpoint PHYSOPT_CHECKPOINT_SHA256 [sha256_file $physopt_checkpoint] \
        PHYS_OPT_DIRECTIVE AggressiveFanoutOpt ROUTE_DIRECTIVE AlternateCLBRouting
    route_design -directive AlternateCLBRouting
    report_timing_summary -delay_type min_max -report_unconstrained \
        -file [file join $output_dir timing_postroute.rpt]
    report_utilization -file [file join $output_dir utilization_postroute.rpt]
    report_utilization -hierarchical -file [file join $output_dir utilization_hierarchical_postroute.rpt]
    report_route_status -file [file join $output_dir route_status_postroute.rpt]
    report_drc -file [file join $output_dir drc_postroute.rpt]
    report_clocks -file [file join $output_dir clocks_postroute.rpt]
    report_power -file [file join $output_dir power_postroute.rpt]
    report_timing -delay_type max -from $core_registers -to $core_registers \
        -max_paths 20 -nworst 1 -file [file join $output_dir core_paths_postroute.rpt]
    lassign [check_memory_caps] uram_after bram_after
    set setup_path [get_timing_paths -quiet -delay_type max -from $core_registers \
        -to $core_registers -max_paths 1]
    set hold_path [get_timing_paths -quiet -delay_type min -from $core_registers \
        -to $core_registers -max_paths 1]
    if {[llength $setup_path] != 1 || [llength $hold_path] != 1} {
        error "The routed checkpoint has no complete recurrent-core setup/hold paths"
    }
    set setup_slack [get_property SLACK [lindex $setup_path 0]]
    set hold_slack [get_property SLACK [lindex $hold_path 0]]
    set fmax [expr {1000.0 / (10.0 - $setup_slack)}]
    set route_report [file join $output_dir route_status_postroute.rpt]
    set drc_report [file join $output_dir drc_postroute.rpt]
    set channel [open $route_report r]
    set route_text [read $channel]
    close $channel
    set channel [open $drc_report r]
    set drc_text [read $channel]
    close $channel
    if {![regexp {# of routable nets\.+\s*:\s*([0-9]+)} $route_text -> routable] ||
        ![regexp {# of fully routed nets\.+\s*:\s*([0-9]+)} $route_text -> routed] ||
        ![regexp {# of nets with routing errors\.+\s*:\s*([0-9]+)} $route_text -> route_errors] ||
        $routable == 0 || $routable != $routed || $route_errors != 0 ||
        [string first "Design State : Fully Routed" $drc_text] < 0 ||
        [regexp {\|\s*Error\s*\|\s*[1-9]} $drc_text]} {
        error "Post-Route checks did not confirm fully routed nets and zero DRC errors"
    }
    set routed_checkpoint [file join $output_dir app_shell_9p_wrapper_routed_fanoutopt.dcp]
    write_checkpoint -force $routed_checkpoint

    set stage WRITE_BITSTREAM
    set bitstream [file join $output_dir app_shell_9p_wrapper_fanoutopt.bit]
    write_bitstream -force $bitstream
    exec sha256sum -c --status $input_manifest
    set final_state CORE_TIMING_NOT_MET_BITSTREAM_READY
    if {$setup_slack >= 0 && $hold_slack >= 0} {
        set final_state CORE_100MHZ_ROUTED_BITSTREAM_READY
    }
    record_state $status_path $final_state \
        SOURCE_CHECKPOINT $checkpoint SOURCE_CHECKPOINT_SHA256 [sha256_file $checkpoint] \
        INPUT_MANIFEST $input_manifest INPUT_MANIFEST_SHA256 $expected_manifest_sha \
        PHYS_OPT_DIRECTIVE AggressiveFanoutOpt ROUTE_DIRECTIVE AlternateCLBRouting \
        CORE_CLOCK_CONFIG_MHZ 100 CORE_SETUP_WNS_NS $setup_slack CORE_HOLD_WHS_NS $hold_slack \
        CORE_FMAX_MHZ $fmax URAM_POSTROUTE $uram_after RAMB36E2_POSTROUTE $bram_after \
        ROUTABLE_NETS $routable FULLY_ROUTED_NETS $routed ROUTING_ERRORS $route_errors \
        ROUTED_CHECKPOINT $routed_checkpoint ROUTED_CHECKPOINT_SHA256 [sha256_file $routed_checkpoint] \
        BITSTREAM_PATH $bitstream BITSTREAM_SHA256 [sha256_file $bitstream] \
        TIMING_REPORT_SHA256 [sha256_file [file join $output_dir timing_postroute.rpt]] \
        ROUTE_REPORT_SHA256 [sha256_file $route_report] DRC_REPORT_SHA256 [sha256_file $drc_report]
    close_design
} error_text error_options]

if {$result != 0} {
    regsub -all {\s+} $error_text { } error_text
    record_state $status_path FAILED FAILED_STAGE $stage OPERATION_RESULT $error_text \
        SOURCE_CHECKPOINT $checkpoint SOURCE_CHECKPOINT_SHA256 [sha256_file $checkpoint] \
        INPUT_MANIFEST $input_manifest INPUT_MANIFEST_SHA256 $expected_manifest_sha
    catch {close_design}
    return -options $error_options $error_text
}

puts "PLAN6_FANOUTOPT_CANDIDATE_COMPLETE $output_dir"
