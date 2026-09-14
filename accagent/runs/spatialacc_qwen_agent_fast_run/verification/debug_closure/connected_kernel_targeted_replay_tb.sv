`timescale 1ns/1ps
module semantic_single_transformer_layer_kernel_tb;
  reg clock = 0;
  reg reset = 1;
  reg [255:0] input_mem_0 [0:1791];
  reg input_0_valid = 0;
  wire input_0_ready;
  reg [255:0] input_0_data = 0;
  integer input_0_accepted = 0;
  wire output_valid;
  reg output_ready = 1;
  wire [255:0] output_data;
  integer output_produced = 0;
  integer output_fd;
  integer cycles = 0;
  string input_path_0;
  reg [31:0] weight_mem [0:7457663];
  string weight_path;
  reg weight_valid = 0;
  wire weight_ready;
  reg [31:0] weight_data = 0;
  reg [22:0] weight_addr = 0;
  reg weight_last = 0;
  integer weight_accepted = 0;
  integer weight_stall_cycles = 0;
  reg [31:0] runtime_mem [0:1055];
  string runtime_path;
  reg runtime_valid = 0;
  wire runtime_ready;
  reg [31:0] runtime_data = 0;
  reg [10:0] runtime_addr = 0;
  reg runtime_last = 0;
  integer runtime_accepted = 0;
  integer runtime_stall_cycles = 0;
  reg start = 0;
  string output_path;

  SingleLayerSemanticHarness dut (
    .clock(clock),
    .reset(reset),
    .input_0_valid(input_0_valid),
    .input_0_ready(input_0_ready),
    .input_0_data(input_0_data),
    .output_valid(output_valid),
    .output_ready(output_ready),
    .output_data(output_data),
    .weight_valid(weight_valid),
    .weight_ready(weight_ready),
    .weight_data(weight_data),
    .weight_addr(weight_addr),
    .weight_last(weight_last),
    .runtime_valid(runtime_valid),
    .runtime_ready(runtime_ready),
    .runtime_data(runtime_data),
    .runtime_addr(runtime_addr),
    .runtime_last(runtime_last),
    .start(start)
  );
  always #5 clock = ~clock;

  initial begin
    if (!$value$plusargs("INPUT_0_MEMH=%s", input_path_0))
      input_path_0 = "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_testbench/single_layer/input.memh";
    $readmemh(input_path_0, input_mem_0);
    if (!$value$plusargs("WEIGHT_MEMH=%s", weight_path))
      weight_path = "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_testbench/single_layer/real_weights.u32.memh";
    $readmemh(weight_path, weight_mem);
    if (!$value$plusargs("RUNTIME_MEMH=%s", runtime_path))
      runtime_path = "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_testbench/single_layer/runtime_constants.u32.memh";
    $readmemh(runtime_path, runtime_mem);
    if (!$value$plusargs("OUTPUT_MEMH=%s", output_path))
      output_path = "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_testbench/single_layer/rtl_output.memh";
    output_fd = $fopen(output_path, "w");
    if (!output_fd) $fatal(1, "cannot open semantic RTL output capture");
    repeat (8) @(posedge clock);
    reset = 0;
    while (weight_accepted < 7457664) begin
      @(negedge clock);
      weight_valid = 1;
      weight_data = weight_mem[weight_accepted];
      weight_addr = weight_accepted;
      weight_last = weight_accepted == 7457663;
      @(posedge clock);
      if (weight_valid && weight_ready) begin
        weight_accepted = weight_accepted + 1;
        weight_stall_cycles = 0;
      end else begin
        weight_stall_cycles = weight_stall_cycles + 1;
        if (weight_stall_cycles >= 10000000)
          $fatal(1, "real-weight loader made no progress");
      end
    end
    @(negedge clock);
    weight_valid = 0;
    weight_last = 0;
    if (!(weight_accepted == 7457664)) $fatal(1, "real-weight load did not complete");
    while (runtime_accepted < 1056) begin
      @(negedge clock);
      runtime_valid = 1;
      runtime_data = runtime_mem[runtime_accepted];
      runtime_addr = runtime_accepted;
      runtime_last = runtime_accepted == 1055;
      @(posedge clock);
      if (runtime_valid && runtime_ready) begin
        runtime_accepted = runtime_accepted + 1;
        runtime_stall_cycles = 0;
      end else begin
        runtime_stall_cycles = runtime_stall_cycles + 1;
        if (runtime_stall_cycles >= 10000000)
          $fatal(1, "runtime-constant loader made no progress");
      end
    end
    @(negedge clock);
    runtime_valid = 0;
    runtime_last = 0;
    if (!(runtime_accepted == 1056)) $fatal(1, "runtime-constant load did not complete");
    start = 1;
    @(posedge clock);
    start = 0;
    while (cycles < 10000000 && output_produced < 1792) begin
      @(negedge clock);
      input_0_valid = input_0_accepted < 1792;
      if (input_0_accepted < 1792) input_0_data = input_mem_0[input_0_accepted];
      @(posedge clock);
      if (input_0_valid && input_0_ready) input_0_accepted = input_0_accepted + 1;
      if (output_valid && output_ready) begin
        $fdisplay(output_fd, "%0h", output_data);
        output_produced = output_produced + 1;
      end
      cycles = cycles + 1;
    end
    if (!(input_0_accepted == 1792) || output_produced != 1792)
      $fatal(1, "semantic harness timeout or output-shape mismatch");
    @(negedge clock);
    $fclose(output_fd);
    $display("PASS semantic harness real-weight execution beats=%0d cycles=%0d", output_produced, cycles);
    $finish;
  end


  // Verification-only direct lifecycle probes. These counters and displays do
  // not drive DUT ports or alter the canonical semantic testbench.
  integer connected_kernel_direct_cycle = 0;
  integer connected_kernel_ingress_accepted = 0;
  integer connected_kernel_egress_accepted = 0;
  integer connected_kernel_mlp_mul_accepted = 0;
  integer connected_kernel_mlp_down_accepted = 0;
  reg connected_kernel_direct_started = 0;
  reg connected_kernel_egress_valid_seen = 0;
  reg connected_kernel_egress_ready_seen = 0;
  reg connected_kernel_residual_valid_seen = 0;
  reg connected_kernel_residual_ready_seen = 0;
  always @(posedge clock) begin
    if (reset) begin
      connected_kernel_direct_cycle = 0;
      connected_kernel_ingress_accepted = 0;
      connected_kernel_egress_accepted = 0;
      connected_kernel_mlp_mul_accepted = 0;
      connected_kernel_mlp_down_accepted = 0;
      connected_kernel_direct_started = 0;
      connected_kernel_egress_valid_seen = 0;
      connected_kernel_egress_ready_seen = 0;
      connected_kernel_residual_valid_seen = 0;
      connected_kernel_residual_ready_seen = 0;
    end else begin
      connected_kernel_direct_cycle = connected_kernel_direct_cycle + 1;
      if (start && !connected_kernel_direct_started) begin
        connected_kernel_direct_started = 1;
        $display("SPATIALACC_CONNECTED_KERNEL_DIRECT kind=start cycle=%0d valid=0 ready=0 fire=0 accepted=0 token=-1 beat=-1 st=0 last=0", connected_kernel_direct_cycle);
      end
      if (dut.core.io_in_valid && dut.core.io_in_ready) begin
        connected_kernel_ingress_accepted = connected_kernel_ingress_accepted + 1;
        if (dut.core.io_in_bits_st || dut.core.io_in_bits_last)
          $display("SPATIALACC_CONNECTED_KERNEL_DIRECT kind=core_ingress cycle=%0d valid=1 ready=1 fire=1 accepted=%0d token=%0d beat=%0d st=%0d last=%0d", connected_kernel_direct_cycle, connected_kernel_ingress_accepted, dut.core.io_in_bits_addr / 112, dut.core.io_in_bits_addr % 112, dut.core.io_in_bits_st, dut.core.io_in_bits_last);
      end
      if (dut.core.mlp_mul_io_out_valid__bore && dut.core.mlp_mul_io_out_ready__bore) begin
        connected_kernel_mlp_mul_accepted = connected_kernel_mlp_mul_accepted + 1;
        if (dut.core.mlp_mul_io_out_bits_st__bore || dut.core.mlp_mul_io_out_bits_last__bore)
          $display("SPATIALACC_CONNECTED_KERNEL_DIRECT kind=mlp_mul_tail cycle=%0d valid=1 ready=1 fire=1 accepted=%0d token=-1 beat=-1 st=%0d last=%0d", connected_kernel_direct_cycle, connected_kernel_mlp_mul_accepted, dut.core.mlp_mul_io_out_bits_st__bore, dut.core.mlp_mul_io_out_bits_last__bore);
      end
      if (dut.core.mlp_down_io_out_valid__bore && dut.core.mlp_down_io_out_ready__bore) begin
        connected_kernel_mlp_down_accepted = connected_kernel_mlp_down_accepted + 1;
        if (dut.core.mlp_down_io_out_bits_st__bore || dut.core.mlp_down_io_out_bits_last__bore)
          $display("SPATIALACC_CONNECTED_KERNEL_DIRECT kind=mlp_down_tail cycle=%0d valid=1 ready=1 fire=1 accepted=%0d token=-1 beat=-1 st=%0d last=%0d", connected_kernel_direct_cycle, connected_kernel_mlp_down_accepted, dut.core.mlp_down_io_out_bits_st__bore, dut.core.mlp_down_io_out_bits_last__bore);
      end
      if (dut.core._add2_io_out_valid != connected_kernel_residual_valid_seen || dut.core._add2_io_computed_ready != connected_kernel_residual_ready_seen) begin
        connected_kernel_residual_valid_seen = dut.core._add2_io_out_valid;
        connected_kernel_residual_ready_seen = dut.core._add2_io_computed_ready;
        $display("SPATIALACC_CONNECTED_KERNEL_DIRECT kind=residual2_frontier cycle=%0d valid=%0d ready=%0d fire=%0d accepted=%0d token=-1 beat=-1 st=0 last=0", connected_kernel_direct_cycle, dut.core._add2_io_out_valid, dut.core._add2_io_computed_ready, dut.core._add2_io_out_valid && dut.core._add2_io_computed_ready, connected_kernel_egress_accepted);
      end
      if (dut.core.io_out_valid != connected_kernel_egress_valid_seen || dut.core.io_out_ready != connected_kernel_egress_ready_seen || (dut.core.io_out_valid && dut.core.io_out_ready && ((connected_kernel_egress_accepted % 112) == 111))) begin
        connected_kernel_egress_valid_seen = dut.core.io_out_valid;
        connected_kernel_egress_ready_seen = dut.core.io_out_ready;
        $display("SPATIALACC_CONNECTED_KERNEL_DIRECT kind=core_egress cycle=%0d valid=%0d ready=%0d fire=%0d accepted=%0d token=%0d beat=%0d st=0 last=%0d", connected_kernel_direct_cycle, dut.core.io_out_valid, dut.core.io_out_ready, dut.core.io_out_valid && dut.core.io_out_ready, connected_kernel_egress_accepted + (dut.core.io_out_valid && dut.core.io_out_ready), connected_kernel_egress_accepted / 112, connected_kernel_egress_accepted % 112, ((connected_kernel_egress_accepted % 112) == 111));
      end
      if (dut.core.io_out_valid && dut.core.io_out_ready)
        connected_kernel_egress_accepted = connected_kernel_egress_accepted + 1;
    end
  end
endmodule
