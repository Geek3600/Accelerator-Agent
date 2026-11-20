set project_dir "/home/hyyuan/workspace/rtwsr_plan6_huginn_vu9p_shell_20261026_attn_pipeline"
set source_report_dir [file join $project_dir plan6_reports_attn_pipeline_full]
set shell_base_dir "/home/hyyuan/workspace/rtwsr_plan6_huginn_vu9p_shell_20261025_ctrl_d"
set shell_base_report_dir [file join $shell_base_dir plan6_reports_ctrl_d_full]
set shell_base_manifest_sha "25dfadd6d2918db51387a5fd328b5635a41bcfa5700f87d94db94602c61c2bdc"
set core_run_dir [file join $project_dir app_shell_9p.runs app_shell_9p_rtwsr_9p_axi_0_6_synth_1]
set core_checkpoint [file join $core_run_dir app_shell_9p_rtwsr_9p_axi_0_6.dcp]
set expected_core_checkpoint_sha "d2ab37db079f4a1792154d7e9740831e7f2fdb9d4ba6da4132bf456ec378a5bd"
set report_dir [file join $project_dir plan6_reports_attn_qkv_100mhz]
set qkv_integration_script [file join $project_dir replace_plan6_qkv_checkpoint.tcl]
set expected_manifest_sha "a186091fb9d5a2ce1a1a7454ea0fafb887cf51c8935cf52ae44e5bb52a1d878c"
set expected_attention_sha "26cd495dc998fa9d444787c5a1c514bc8486fd72e2b4b71af304673ac59bef6a"
set status_path [file join $report_dir huginn_vu9p_shell_status.txt]
file mkdir $report_dir

proc sha256_file {path} {
    return [lindex [exec sha256sum [file normalize $path]] 0]
}

proc record_state {state args} {
    global status_path project_dir expected_manifest_sha shell_base_manifest_sha expected_core_checkpoint_sha
    set channel [open "${status_path}.pending" w]
    puts $channel "STATE $state"
    puts $channel "PROJECT_DIR $project_dir"
    puts $channel "INPUT_MANIFEST_SHA256 $expected_manifest_sha"
    puts $channel "SHELL_BASE_INPUT_MANIFEST_SHA256 $shell_base_manifest_sha"
    puts $channel "SOURCE_CORE_CHECKPOINT_SHA256 $expected_core_checkpoint_sha"
    puts $channel "CORE_CLOCK_TARGET_MHZ 100"
    puts $channel "CNN_CORE_COUNT 0"
    puts $channel "QKV_IMPLEMENTATION PIPELINED_BRAM"
    foreach {key value} $args { puts $channel "$key $value" }
    close $channel
    file rename -force "${status_path}.pending" $status_path
}

set result [catch {
    set source_manifest [file join $source_report_dir shell_inputs.sha256]
    if {[sha256_file $source_manifest] ne $expected_manifest_sha ||
        [sha256_file [file join $project_dir plan6_rtl rtwsr_attention_gemv_unit.sv]] ne $expected_attention_sha} {
        error "The full-shell synthesis inputs do not match the pipelined Attention version"
    }
    exec sha256sum -c --status $source_manifest
    set shell_base_manifest [file join $shell_base_report_dir shell_inputs.sha256]
    if {[sha256_file $shell_base_manifest] ne $shell_base_manifest_sha} {
        error "The reusable full-shell checkpoint identity changed"
    }
    exec sha256sum -c --status $shell_base_manifest
    set source_status [open [file join $source_report_dir huginn_vu9p_shell_status.txt] r]
    set source_status_text [read $source_status]
    close $source_status
    if {[string first "INPUT_MANIFEST_SHA256 $expected_manifest_sha" $source_status_text] < 0 ||
        ![file isfile [file join $core_run_dir .vivado.end.rst]] ||
        [sha256_file $core_checkpoint] ne $expected_core_checkpoint_sha} {
        error "The matching pipelined core synthesis checkpoint is not complete"
    }
    set core_utilization [file join $core_run_dir app_shell_9p_rtwsr_9p_axi_0_6_utilization_synth.rpt]
    set channel [open $core_utilization r]
    set synthesis_text [read $channel]
    close $channel
    foreach {resource limit} {{CLB LUTs\*} 1182240 {Block RAM Tile} 648 URAM 832} {
        if {![regexp [format {\|\s*%s\s*\|\s*([0-9.]+)} $resource] $synthesis_text -> used] || $used > $limit} {
            error "The source core resource gate did not pass for $resource"
        }
    }

    record_state OPENING_SYNTHESIS
    open_project -read_only [file join $shell_base_dir app_shell_9p.xpr]
    set_param general.maxThreads 8
    open_run synth_1
    set synthesis_blackboxes [get_cells -hier -quiet -filter {IS_BLACKBOX == 1}]
    set shell_top [get_property TOP [current_fileset]]
    puts "PLAN6_SHELL_TOP $shell_top INTERNAL_DESIGN [current_design]"
    foreach cell $synthesis_blackboxes {
        puts "PLAN6_SYNTH_BLACKBOX [get_property NAME $cell] [get_property REF_NAME $cell]"
    }
    if {$shell_top ne "app_shell_9p_wrapper" ||
        [llength [get_cells -hier -quiet -filter {IS_BLACKBOX == 1 && REF_NAME != dbg_hub_CV}]] != 0 ||
        [llength [get_cells -hier -quiet -filter {NAME =~ *cnn_core*}]] != 0} {
        error "The linked synthesis must contain the complete CNN-free board shell"
    }
    set accelerator_cell [get_cells -hier -filter {NAME == app_shell_9p_i/rtwsr_9p_axi_0}]
    if {[llength $accelerator_cell] != 1} { error "Expected one accelerator shell instance" }
    foreach shell_cell {app_shell_9p_i/ddr4_0 app_shell_9p_i/ddr4_1} {
        if {[llength [get_cells -quiet $shell_cell]] != 1} {
            error "Missing complete-shell instance: $shell_cell"
        }
    }
    puts "PLAN6_COMPLETE_SHELL_CHECK_PASSED"
    set accelerator_cell_name [get_property NAME $accelerator_cell]
    update_design -cell $accelerator_cell -black_box
    read_checkpoint -cell $accelerator_cell_name $core_checkpoint
    source $qkv_integration_script
    set linked_utilization [file join $report_dir utilization_linked_synth.rpt]
    report_utilization -file $linked_utilization
    report_utilization -hierarchical -file [file join $report_dir utilization_hierarchical_linked_synth.rpt]
    set channel [open $linked_utilization r]
    set linked_utilization_text [read $channel]
    close $channel
    foreach {resource limit} {{CLB LUTs\*} 1182240 {Block RAM Tile} 648 URAM 832} {
        if {![regexp [format {\|\s*%s\s*\|\s*([0-9.]+)} $resource] $linked_utilization_text -> used] || $used > $limit} {
            error "The complete shell resource gate did not pass after QKV replacement: $resource"
        }
    }
    set core_mmcm [get_cells -hier -filter {REF_NAME == MMCME4_ADV && NAME =~ *rtwsr_core_clk_wiz*}]
    if {[llength $core_mmcm] != 1} { error "Expected one accelerator core MMCM" }
    report_clocks -file [file join $report_dir clocks_before.rpt]
    set input_clock [get_clocks -of_objects [get_pins $core_mmcm/CLKIN1]]
    if {[llength $input_clock] != 1} { error "The core MMCM input clock is missing" }
    set input_period [get_property PERIOD $input_clock]
    set input_divider [get_property DIVCLK_DIVIDE $core_mmcm]
    set output_divider [expr {round(10.0 / $input_period *
        [get_property CLKFBOUT_MULT_F $core_mmcm] / $input_divider)}]
    set feedback_multiplier [expr {$output_divider * $input_period * $input_divider / 10.0}]
    if {$output_divider < 1.0 || $output_divider > 128.0 ||
        $feedback_multiplier < 2.0 || $feedback_multiplier > 64.0 ||
        abs($feedback_multiplier * 8.0 - round($feedback_multiplier * 8.0)) > 0.00001} {
        error "The core MMCM parameters cannot generate 100 MHz"
    }
    set_property -dict [list CLKFBOUT_MULT_F $feedback_multiplier \
        CLKOUT0_DIVIDE_F $output_divider] $core_mmcm
    set clock_xdc [file join $report_dir core_clock_configuration.xdc]
    set channel [open $clock_xdc w]
    puts $channel [format {set_property -dict {CLKFBOUT_MULT_F %s CLKOUT0_DIVIDE_F %s} [get_cells {%s}]} \
        $feedback_multiplier $output_divider [get_property NAME $core_mmcm]]
    close $channel
    report_property $core_mmcm -file [file join $report_dir core_mmcm.rpt]
    report_clocks -file [file join $report_dir clocks_100mhz.rpt]
    set core_clock [get_clocks -of_objects [get_pins $core_mmcm/CLKOUT0]]
    if {[llength $core_clock] != 1 || abs([get_property PERIOD $core_clock] - 10.0) > 0.001} {
        error "The actual core generated clock must have a 10 ns period"
    }
    set accelerator_registers [filter [all_registers] {NAME =~ *u_recurrent_core/*}]
    set clocked_accelerator_registers [filter [all_registers -clock $core_clock] {NAME =~ *u_recurrent_core/*}]
    if {[llength $accelerator_registers] == 0 ||
        [llength $accelerator_registers] != [llength $clocked_accelerator_registers]} {
        error "The entire recurrent core must be constrained by the actual 100 MHz clock"
    }
    set manifest_path [file join $report_dir implementation_inputs.sha256]
    set channel [open $manifest_path w]
    foreach path [list [info script] $source_manifest $shell_base_manifest $clock_xdc \
        $qkv_integration_script $qkv_rtl $qkv_manifest $qkv_checkpoint \
        [file join $qkv_run_dir run_plan6_qkv_pipeline.tcl] $qkv_status_path \
        $linked_utilization \
        $core_utilization [file join $core_run_dir runme.log] \
        [file join $shell_base_dir app_shell_9p.runs synth_1 app_shell_9p_wrapper.dcp] \
        $core_checkpoint] {
        puts $channel "[sha256_file $path]  [file normalize $path]"
    }
    close $channel
    set implementation_sha [sha256_file $manifest_path]
    report_timing_summary -delay_type min_max -report_unconstrained \
        -file [file join $report_dir timing_before_implementation.rpt]
    set core_registers [all_registers -clock $core_clock]
    report_timing -delay_type max -from $core_registers -to $core_registers \
        -max_paths 20 -nworst 1 -file [file join $report_dir core_paths_before_implementation.rpt]

    record_state IMPLEMENTATION_RUNNING CORE_CLOCK_CONFIG_MHZ 100 \
        CORE_REGISTER_COUNT [llength $clocked_accelerator_registers] \
        IMPLEMENTATION_INPUTS_SHA256 $implementation_sha
    opt_design
    if {[llength [get_debug_cores -quiet]] > 0} {
        implement_debug_core
    }
    if {[llength [get_cells -hier -quiet -filter {IS_BLACKBOX == 1}]] != 0} {
        error "The complete shell must have no black boxes before placement"
    }
    place_design -directive ExtraPostPlacementOpt
    report_utilization -file [file join $report_dir utilization_placed.rpt]
    phys_opt_design -directive AggressiveExplore
    route_design -directive AlternateCLBRouting
    report_timing_summary -delay_type min_max -report_unconstrained -file [file join $report_dir timing_postroute.rpt]
    report_utilization -file [file join $report_dir utilization_postroute.rpt]
    report_utilization -hierarchical -file [file join $report_dir utilization_hierarchical_postroute.rpt]
    report_route_status -file [file join $report_dir route_status_postroute.rpt]
    report_drc -file [file join $report_dir drc_postroute.rpt]
    report_clocks -file [file join $report_dir clocks_postroute.rpt]
    report_power -file [file join $report_dir power_postroute.rpt]
    set core_registers [all_registers -clock $core_clock]
    report_timing -delay_type max -from $core_registers -to $core_registers \
        -max_paths 20 -nworst 1 -file [file join $report_dir core_paths_postroute.rpt]
    set setup_path [get_timing_paths -delay_type max -from $core_registers -to $core_registers -max_paths 1]
    set hold_path [get_timing_paths -delay_type min -from $core_registers -to $core_registers -max_paths 1]
    if {[llength $setup_path] != 1 || [llength $hold_path] != 1} {
        error "The routed design has no complete core setup/hold paths"
    }
    set setup_slack [get_property SLACK $setup_path]
    set hold_slack [get_property SLACK $hold_path]
    set channel [open [file join $report_dir timing_postroute.rpt] r]
    set timing_text [read $channel]
    close $channel
    set shell_timing_met [expr {[string first "All user specified timing constraints are met." $timing_text] >= 0}]
    write_checkpoint -force [file join $report_dir app_shell_9p_wrapper_routed.dcp]
    if {$setup_slack < 0 || $hold_slack < 0} {
        record_state CORE_TIMING_NOT_MET CORE_CLOCK_CONFIG_MHZ 100 \
            CORE_SETUP_WNS_NS $setup_slack CORE_HOLD_WHS_NS $hold_slack \
            SHELL_TIMING_CONSTRAINTS_MET $shell_timing_met \
            IMPLEMENTATION_INPUTS_SHA256 $implementation_sha
    } else {
        set bitstream [file join $report_dir app_shell_9p_wrapper.bit]
        write_bitstream -force $bitstream
        exec sha256sum -c --status $source_manifest
        exec sha256sum -c --status $shell_base_manifest
        exec sha256sum -c --status $manifest_path
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
