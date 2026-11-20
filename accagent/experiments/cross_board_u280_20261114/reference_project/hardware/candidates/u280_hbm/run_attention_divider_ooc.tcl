set_param general.maxThreads 2
set root /home/hyyuan/workspace/flightloop_plan2_attention_divider_ooc_20261030
read_verilog -sv $root/rtwsr_round_divider_7bit.sv
synth_design -top rtwsr_round_divider_7bit -part xcu280-fsvh2892-2L-e -mode out_of_context -generic FAST=1
create_clock -period 4.444 -name core_clk [get_ports clk]
set_input_delay 0 -clock core_clk [get_ports {rst_n start dividend[*] divisor[*]}]
set_output_delay 0 -clock core_clk [get_ports {ready done quotient[*]}]
opt_design
place_design
route_design
report_utilization -file $root/utilization.rpt
report_timing_summary -delay_type max -max_paths 10 -file $root/timing_summary.rpt
report_timing -delay_type max -max_paths 10 -file $root/timing_paths.rpt
exit
