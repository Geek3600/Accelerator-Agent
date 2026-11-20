proc run_resource_opt_candidate {candidate trits_per_cycle} {
    set repo_root [file normalize [file join [file dirname [info script]] ../../..]]
    set rtl_root [file join $repo_root hardware candidates resource_opt rtl_integrated]
    set report_root [file join $repo_root results resource_opt_20261030 candidates $candidate]
    set part xcu280-fsvh2892-2L-e
    file mkdir $report_root

    proc sha256_file {path} {
        return [lindex [exec sha256sum [file normalize $path]] 0]
    }

    set sources [list \
        [file join $repo_root hardware rtwsr_plan6_huginn_u280_hbm_shell.sv] \
        [file join $repo_root hardware rtwsr_plan6_huginn_shell.sv] \
        [file join $repo_root hardware rtwsr_weight_dma.sv] \
        [file join $repo_root hardware candidates u280_hbm rtwsr_huginn_u280_hbm_descriptor.sv] \
        [file join $repo_root hardware candidates u280_hbm rtwsr_hbm_read_dma_27pc.sv] \
        [file join $repo_root hardware candidates u280_hbm rtwsr_hbm_gearbox_27lane.sv] \
        [file join $repo_root hardware candidates u280_hbm rtwsr_hbm_weight_pool_adapter_27to24.sv] \
        [file join $repo_root hardware candidates u280_hbm rtwsr_plan6_huginn_u280_hbm_weight_path.sv] \
        [file join $repo_root hardware candidates resource_opt rtwsr_attention_gemv_unit_dsp_shared.sv]]
    foreach source [glob -directory $rtl_root *.sv] {
        if {[file tail $source] ne "rtwsr_attention_gemv_unit.sv"} {
            lappend sources $source
        }
    }

    set manifest [open [file join $report_root inputs.sha256] w]
    foreach source $sources {
        if {![file isfile $source]} {
            error "Missing source: $source"
        }
        puts $manifest "[sha256_file $source]  $source"
    }
    close $manifest

    create_project -in_memory -part $part
    set_param general.maxThreads 4
    set_property verilog_define {SYNTH_CARRY8 XILINX_XPM} [current_fileset]
    add_files -norecurse $sources
    set_property file_type SystemVerilog [get_files $sources]
    update_compile_order -fileset sources_1
    synth_design -mode out_of_context -top rtwsr_plan6_huginn_u280_hbm_shell -part $part \
        -generic "LINEAR_CHANNELS=96 MAX_CONTEXT=2048 HBM_PCS=32 HBM_POOL_LANES=24 HBM_MAX_OUTSTANDING=16 HBM_RING_RECORDS=73728 CORE_TIMING_CANDIDATE=1 CORE_128TRIT_CANDIDATE=$trits_per_cycle POOL_READ_PARALLEL_SLOTS=0 GAMMA_PARALLEL_LOAD=1 RESIDUAL_NORM_FUSION=1 RESIDUAL_NORM_TILE_PRELOAD=0 NORM_GAMMA_FROM_HOST=1 ATTENTION_PARALLEL_CANDIDATE=1 ADAPTER_STATIC_REUSE=1 ATTENTION_PARALLEL_HEADS=2 ATTENTION_QUANT_STREAM_PIPELINE=1 RECURRENCES_OVERRIDE=32"
    create_clock -name core_clk -period 4.444 [get_ports core_clk]
    create_clock -name hbm_axi_clk -period 2.222 [get_ports hbm_axi_clk]
    report_utilization -file [file join $report_root utilization_synth.rpt]
    report_utilization -hierarchical -file [file join $report_root utilization_hierarchical_synth.rpt]
    report_timing_summary -file [file join $report_root timing_synth.rpt]
    report_power -file [file join $report_root power_synth.rpt]
    close_design
    puts "RESOURCE_OPT_U280_${candidate}_OOC_COMPLETE"
}
