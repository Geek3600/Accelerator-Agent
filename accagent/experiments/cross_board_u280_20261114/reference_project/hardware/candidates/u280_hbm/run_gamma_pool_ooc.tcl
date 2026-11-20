set run_root [file normalize [file dirname [info script]]]
set rtl_path [file join $run_root rtl rtwsr_runtime_gamma_pool.sv]
set report_root [file join $run_root reports]
set part xcu280-fsvh2892-2L-e

file mkdir $report_root

proc sha256_file {path} {
    return [lindex [exec sha256sum [file normalize $path]] 0]
}

if {![file isfile $rtl_path]} {
    error "Missing Gamma pool RTL: $rtl_path"
}

set manifest [open [file join $report_root inputs.sha256] w]
puts $manifest "[sha256_file $rtl_path]  $rtl_path"
close $manifest

set_param general.maxThreads 2
create_project -in_memory -part $part
read_verilog -sv $rtl_path
synth_design -top rtwsr_runtime_gamma_pool -part $part -mode out_of_context \
    -generic {MAX_ROWS=17920 CHANNELS=192 PARALLEL_LOAD=1}
create_clock -name clk_core -period 4.444 [get_ports clk]
report_utilization -file [file join $report_root utilization_synth.rpt]
report_timing_summary -file [file join $report_root timing_synth.rpt]
puts "GAMMA_POOL_U280_OOC_SYNTH_COMPLETE"
exit
