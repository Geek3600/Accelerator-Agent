set_param general.maxThreads 2
set root /home/hyyuan/workspace/flightloop_plan2_attention_divider_stream7_ooc_20261030
read_verilog -sv $root/rtwsr_round_divider_stream7.sv
read_verilog -sv $root/rtwsr_divider_stream7_ooc_top.sv
synth_design -top rtwsr_divider_stream7_ooc_top -part xcu280-fsvh2892-2L-e -mode out_of_context
create_clock -period 4.444 -name core_clk [get_ports clk]
set_false_path -from [get_ports -filter {DIRECTION == IN && NAME != clk}]
set_false_path -to [all_outputs]
opt_design
place_design
route_design
report_utilization -file $root/utilization.rpt
report_timing_summary -delay_type max -max_paths 10 -file $root/timing_summary.rpt
report_timing -delay_type max -max_paths 10 -file $root/timing_paths.rpt
exit
