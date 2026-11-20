if {$argc != 2} {
    error "usage: run_fullchip_route_reduced_u280.tcl <snapshot-root> <output-dir>"
}

set snapshot_root [file normalize [lindex $argv 0]]
set output_dir [file normalize [lindex $argv 1]]
set hw_root [file join $snapshot_root hardware]
set rtl_root [file join $hw_root candidates resource_opt rtl_integrated]
set part xcu280-fsvh2892-2L-e
file mkdir $output_dir
set_param general.maxThreads 8

set status_path [file join $output_dir implementation_status.txt]
set stage PREFLIGHT

proc sha256_file {path} {
    return [lindex [exec sha256sum [file normalize $path]] 0]
}

proc write_state {path state stage message} {
    set fh [open $path w]
    puts $fh "STATE $state"
    puts $fh "STAGE $stage"
    puts $fh "MESSAGE $message"
    puts $fh "UTC [clock format [clock seconds] -format {%Y-%m-%dT%H:%M:%SZ} -gmt 1]"
    close $fh
}

set sources [list \
    [file join $hw_root rtwsr_plan6_huginn_u280_hbm_shell.sv] \
    [file join $hw_root rtwsr_plan6_huginn_shell.sv] \
    [file join $hw_root rtwsr_weight_dma.sv] \
    [file join $hw_root candidates u280_hbm rtwsr_huginn_u280_hbm_descriptor.sv] \
    [file join $hw_root candidates u280_hbm rtwsr_hbm_read_dma_27pc.sv] \
    [file join $hw_root candidates u280_hbm rtwsr_hbm_gearbox_27lane.sv] \
    [file join $hw_root candidates u280_hbm rtwsr_hbm_weight_pool_adapter_27to24.sv] \
    [file join $hw_root candidates u280_hbm rtwsr_plan6_huginn_u280_hbm_weight_path.sv] \
    [file join $hw_root candidates resource_opt rtwsr_attention_gemv_unit_dsp_shared.sv]]
foreach source [glob -directory $rtl_root *.sv] {
    if {[file tail $source] ne "rtwsr_attention_gemv_unit.sv"} {
        lappend sources $source
    }
}

set manifest [file join $output_dir implementation_inputs.sha256]
set mf [open $manifest w]
foreach source $sources {
    if {![file isfile $source]} {
        error "Missing source: $source"
    }
    puts $mf "[sha256_file $source]  $source"
}
close $mf

write_state $status_path RUNNING $stage "full U280 shell route candidate: 96ch/128trit, 2-head, half-depth HBM ring"
set result [catch {
    create_project -in_memory -part $part
    set_property verilog_define {SYNTH_CARRY8 XILINX_XPM} [current_fileset]
    add_files -norecurse $sources
    set_property file_type SystemVerilog [get_files $sources]
    update_compile_order -fileset sources_1

    set stage SYNTH_DESIGN
    write_state $status_path RUNNING $stage "synth_design full shell top"
    synth_design -mode out_of_context -top rtwsr_plan6_huginn_u280_hbm_shell -part $part \
        -generic {LINEAR_CHANNELS=96 MAX_CONTEXT=2048 HBM_PCS=32 HBM_POOL_LANES=24 HBM_MAX_OUTSTANDING=16 HBM_RING_RECORDS=36864 CORE_TIMING_CANDIDATE=1 CORE_128TRIT_CANDIDATE=1 POOL_READ_PARALLEL_SLOTS=0 GAMMA_PARALLEL_LOAD=1 RESIDUAL_NORM_FUSION=1 RESIDUAL_NORM_TILE_PRELOAD=0 NORM_GAMMA_FROM_HOST=1 ATTENTION_PARALLEL_CANDIDATE=1 ADAPTER_STATIC_REUSE=1 ATTENTION_PARALLEL_HEADS=2 ATTENTION_QUANT_STREAM_PIPELINE=1 RECURRENCES_OVERRIDE=32}
    create_clock -period 4.444 -name core_clk [get_ports core_clk]
    create_clock -period 2.222 -name hbm_axi_clk [get_ports hbm_axi_clk]
    report_utilization -file [file join $output_dir utilization_synth.rpt]
    report_utilization -hierarchical -file [file join $output_dir utilization_hierarchical_synth.rpt]
    report_timing_summary -delay_type min_max -report_unconstrained -file [file join $output_dir timing_synth.rpt]

    set stage OPT_DESIGN
    write_state $status_path RUNNING $stage "opt_design"
    opt_design
    report_utilization -file [file join $output_dir utilization_opt.rpt]

    set stage PLACE_DESIGN
    write_state $status_path RUNNING $stage "place_design SSI_SpreadSLLs"
    place_design -directive SSI_SpreadSLLs
    report_utilization -file [file join $output_dir utilization_placed.rpt]
    report_timing_summary -delay_type min_max -report_unconstrained \
        -file [file join $output_dir timing_placed.rpt]
    write_checkpoint -force [file join $output_dir full_shell_placed.dcp]

    set stage PHYS_OPT_DESIGN
    write_state $status_path RUNNING $stage "phys_opt_design Explore"
    phys_opt_design -directive Explore
    report_utilization -file [file join $output_dir utilization_physopt.rpt]
    report_timing_summary -delay_type min_max -report_unconstrained \
        -file [file join $output_dir timing_physopt.rpt]

    set stage ROUTE_DESIGN
    write_state $status_path RUNNING $stage "route_design Explore without timing-driven optimization"
    set route_result [catch {route_design -no_timing_driven -directive Explore} route_message route_options]
    report_utilization -file [file join $output_dir utilization_route_attempt.rpt]
    report_utilization -hierarchical -file [file join $output_dir utilization_hierarchical_route_attempt.rpt]
    report_route_status -file [file join $output_dir route_status_route_attempt.rpt]
    report_drc -file [file join $output_dir drc_route_attempt.rpt]
    report_timing_summary -delay_type min_max -report_unconstrained \
        -file [file join $output_dir timing_route_attempt.rpt]
    if {$route_result != 0} {
        return -options $route_options $route_message
    }

    write_checkpoint -force [file join $output_dir full_shell_routed.dcp]
    report_utilization -file [file join $output_dir utilization_postroute.rpt]
    report_utilization -hierarchical -file [file join $output_dir utilization_hierarchical_postroute.rpt]
    report_timing_summary -delay_type min_max -report_unconstrained \
        -file [file join $output_dir timing_postroute.rpt]
    report_route_status -file [file join $output_dir route_status_postroute.rpt]
    report_drc -file [file join $output_dir drc_postroute.rpt]
    report_power -file [file join $output_dir power_postroute.rpt]
    write_state $status_path COMPLETE $stage "full shell route and post-route power report generated"
    close_design
} message options]

if {$result != 0} {
    write_state $status_path FAILED $stage $message
    catch {close_design}
    return -options $options $message
}

puts "FULLCHIP_ROUTE_REDUCED_U280_COMPLETE $output_dir"
