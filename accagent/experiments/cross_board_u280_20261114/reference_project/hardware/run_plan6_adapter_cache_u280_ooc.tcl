set report_dir /tmp/loopquant_adapter_cache_u280_ooc_20261029
file mkdir $report_dir
create_project -in_memory -part xcu280-fsvh2892-2L-e
set_property file_type SystemVerilog [add_files [file normalize [file join [file dirname [info script]] rtwsr_adapter_static_cache.sv]]]
synth_design -top rtwsr_adapter_static_cache -part xcu280-fsvh2892-2L-e
report_utilization -file [file join $report_dir utilization.rpt]
report_utilization -hierarchical -file [file join $report_dir utilization_hierarchical.rpt]
report_timing_summary -file [file join $report_dir timing.rpt]
puts "PLAN6_ADAPTER_CACHE_U280_OOC_SYNTH_COMPLETE"
