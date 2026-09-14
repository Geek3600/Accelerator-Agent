`timescale 1ns/1ps

module qwen_axi_board_tb;
  localparam int AXI_DATA_W = 256;
  localparam int AXI_STRB_W = AXI_DATA_W / 8;
  localparam int INPUT_WORDS = 65536;
  localparam int WEIGHT_WORDS = 16384;
  localparam int OUTPUT_WORDS = 65536;
  localparam int MAX_CYCLES = 12000000;
  localparam int NO_PROGRESS_LIMIT = 300000;
  localparam int NUM_LAYERS = 24;
  localparam int PROBE_LAYER_A = (NUM_LAYERS > 4) ? (NUM_LAYERS / 4) : 1;
  localparam int PROBE_LAYER_B = (NUM_LAYERS > 2) ? (NUM_LAYERS / 2) : 1;
  localparam int PROBE_LAYER_C = (NUM_LAYERS > 4) ? ((NUM_LAYERS * 3) / 4) : NUM_LAYERS;

  logic clock = 1'b0;
  logic reset = 1'b1;
  always #5 clock = ~clock;

  logic io_start;
  logic [15:0] io_cfg_seqlen;
  logic io_cfg_prefill;
  logic io_cfg_single_query;
  logic [63:0] io_input_base_addr;
  logic [63:0] io_weight_base_addr;
  logic [63:0] io_output_base_addr;
  logic [31:0] io_output_stride_bytes;

  logic [5:0] io_m_axi_awid;
  logic [63:0] io_m_axi_awaddr;
  logic [7:0] io_m_axi_awlen;
  logic [2:0] io_m_axi_awsize;
  logic [1:0] io_m_axi_awburst;
  logic [0:0] io_m_axi_awlock;
  logic [3:0] io_m_axi_awcache;
  logic [2:0] io_m_axi_awprot;
  logic [3:0] io_m_axi_awregion;
  logic [3:0] io_m_axi_awqos;
  logic io_m_axi_awvalid;
  logic io_m_axi_awready;
  logic [AXI_DATA_W-1:0] io_m_axi_wdata;
  logic [AXI_STRB_W-1:0] io_m_axi_wstrb;
  logic io_m_axi_wlast;
  logic io_m_axi_wvalid;
  logic io_m_axi_wready;
  logic [5:0] io_m_axi_bid;
  logic [1:0] io_m_axi_bresp;
  logic io_m_axi_bvalid;
  logic io_m_axi_bready;
  logic [5:0] io_m_axi_arid;
  logic [63:0] io_m_axi_araddr;
  logic [7:0] io_m_axi_arlen;
  logic [2:0] io_m_axi_arsize;
  logic [1:0] io_m_axi_arburst;
  logic [0:0] io_m_axi_arlock;
  logic [3:0] io_m_axi_arcache;
  logic [2:0] io_m_axi_arprot;
  logic [3:0] io_m_axi_arregion;
  logic [3:0] io_m_axi_arqos;
  logic io_m_axi_arvalid;
  logic io_m_axi_arready;
  logic [5:0] io_m_axi_rid;
  logic [AXI_DATA_W-1:0] io_m_axi_rdata;
  logic [1:0] io_m_axi_rresp;
  logic io_m_axi_rlast;
  logic io_m_axi_rvalid;
  logic io_m_axi_rready;
  logic [255:0] io_res;
  logic io_res_st;
  logic [31:0] io_res_addr;
  logic io_res_valid;
  logic io_res_last;
  logic io_done;
  logic io_error;

  logic [31:0] input_mem [0:INPUT_WORDS-1];
  logic [31:0] weight_mem [0:WEIGHT_WORDS-1];
  logic [31:0] output_mem [0:OUTPUT_WORDS-1];
  string input_memh;
  string weight_memh;
  string input_manifest;
  string weight_manifest;
  integer i;
  integer j;
  integer cycle;
  integer read_idx;
  integer read_beats;
  integer read_word;
  integer write_word;
  integer input_read_beats;
  integer weight_read_beats;
  integer output_write_beats;
  integer output_valid_beats;
  integer l0_mlp_gate_out_beats;
  integer l0_mlp_up_out_beats;
  integer l0_mlp_act_out_beats;
  integer l0_mlp_actq_deq_beats;
  integer l0_mlp_upq_deq_beats;
  integer l0_mlp_mul_out_beats;
  integer l0_mlp_down_out_beats;
  integer l0_add2_res2q_enq_beats;
  integer l0_add2_res2q_deq_beats;
  integer l0_add2_computed_beats;
  integer l0_add2_out_beats;
  integer pipeline_l0_out_beats;
  integer pipeline_l1_out_beats;
  integer pipeline_last_out_beats;
  integer pipeline_probe_a_beats;
  integer pipeline_probe_b_beats;
  integer pipeline_probe_c_beats;
  integer last_progress_cycle;
  bit read_active;
  bit b_pending;
  longint unsigned rd_base;
  longint unsigned wr_base;

  QwenAxiBoardSystemTop dut (
    .clock(clock),
    .reset(reset),
    .io_start(io_start),
    .io_cfg_seqlen(io_cfg_seqlen),
    .io_cfg_prefill(io_cfg_prefill),
    .io_cfg_single_query(io_cfg_single_query),
    .io_input_base_addr(io_input_base_addr),
    .io_weight_base_addr(io_weight_base_addr),
    .io_output_base_addr(io_output_base_addr),
    .io_output_stride_bytes(io_output_stride_bytes),
    .io_m_axi_awid(io_m_axi_awid),
    .io_m_axi_awaddr(io_m_axi_awaddr),
    .io_m_axi_awlen(io_m_axi_awlen),
    .io_m_axi_awsize(io_m_axi_awsize),
    .io_m_axi_awburst(io_m_axi_awburst),
    .io_m_axi_awlock(io_m_axi_awlock),
    .io_m_axi_awcache(io_m_axi_awcache),
    .io_m_axi_awprot(io_m_axi_awprot),
    .io_m_axi_awregion(io_m_axi_awregion),
    .io_m_axi_awqos(io_m_axi_awqos),
    .io_m_axi_awvalid(io_m_axi_awvalid),
    .io_m_axi_awready(io_m_axi_awready),
    .io_m_axi_wdata(io_m_axi_wdata),
    .io_m_axi_wstrb(io_m_axi_wstrb),
    .io_m_axi_wlast(io_m_axi_wlast),
    .io_m_axi_wvalid(io_m_axi_wvalid),
    .io_m_axi_wready(io_m_axi_wready),
    .io_m_axi_bid(io_m_axi_bid),
    .io_m_axi_bresp(io_m_axi_bresp),
    .io_m_axi_bvalid(io_m_axi_bvalid),
    .io_m_axi_bready(io_m_axi_bready),
    .io_m_axi_arid(io_m_axi_arid),
    .io_m_axi_araddr(io_m_axi_araddr),
    .io_m_axi_arlen(io_m_axi_arlen),
    .io_m_axi_arsize(io_m_axi_arsize),
    .io_m_axi_arburst(io_m_axi_arburst),
    .io_m_axi_arlock(io_m_axi_arlock),
    .io_m_axi_arcache(io_m_axi_arcache),
    .io_m_axi_arprot(io_m_axi_arprot),
    .io_m_axi_arregion(io_m_axi_arregion),
    .io_m_axi_arqos(io_m_axi_arqos),
    .io_m_axi_arvalid(io_m_axi_arvalid),
    .io_m_axi_arready(io_m_axi_arready),
    .io_m_axi_rid(io_m_axi_rid),
    .io_m_axi_rdata(io_m_axi_rdata),
    .io_m_axi_rresp(io_m_axi_rresp),
    .io_m_axi_rlast(io_m_axi_rlast),
    .io_m_axi_rvalid(io_m_axi_rvalid),
    .io_m_axi_rready(io_m_axi_rready),
    .io_res(io_res),
    .io_res_st(io_res_st),
    .io_res_addr(io_res_addr),
    .io_res_valid(io_res_valid),
    .io_res_last(io_res_last),
    .io_done(io_done),
    .io_error(io_error)
  );

  task automatic clear_axi;
    begin
      io_m_axi_awready <= 1'b0;
      io_m_axi_wready <= 1'b0;
      io_m_axi_bid <= 6'd0;
      io_m_axi_bresp <= 2'b00;
      io_m_axi_bvalid <= 1'b0;
      io_m_axi_arready <= 1'b0;
      io_m_axi_rid <= 6'd0;
      io_m_axi_rdata <= '0;
      io_m_axi_rresp <= 2'b00;
      io_m_axi_rlast <= 1'b0;
      io_m_axi_rvalid <= 1'b0;
    end
  endtask

  function automatic [31:0] read_input_word(input integer idx);
    begin
      read_input_word = (idx >= 0 && idx < INPUT_WORDS) ? input_mem[idx] : 32'hBAD0_0001;
    end
  endfunction

  function automatic [31:0] read_weight_word(input integer idx);
    begin
      read_weight_word = (idx >= 0 && idx < WEIGHT_WORDS) ? weight_mem[idx] : 32'hBAD0_0002;
    end
  endfunction

  function automatic [AXI_DATA_W-1:0] pack_read_data(input longint unsigned base, input integer beat);
    integer base_word;
    integer k;
    begin
      pack_read_data = '0;
      if (base >= io_weight_base_addr) begin
        base_word = int'((base - io_weight_base_addr) >> 2) + beat * 8;
        for (k = 0; k < 8; k = k + 1) pack_read_data[32 * k +: 32] = read_weight_word(base_word + k);
      end else begin
        base_word = int'((base - io_input_base_addr) >> 2) + beat * 8;
        for (k = 0; k < 8; k = k + 1) pack_read_data[32 * k +: 32] = read_input_word(base_word + k);
      end
    end
  endfunction

  always @(posedge clock) begin
    clear_axi();
    if (!reset) begin
      io_m_axi_arready <= !read_active;
      if (io_m_axi_arvalid && io_m_axi_arready) begin
        read_active <= 1'b1;
        read_idx <= 0;
        read_beats <= {24'd0, io_m_axi_arlen} + 32'd1;
        rd_base <= io_m_axi_araddr;
        last_progress_cycle <= cycle;
      end
      if (read_active) begin
        io_m_axi_rvalid <= 1'b1;
        io_m_axi_rdata <= pack_read_data(rd_base, read_idx);
        io_m_axi_rlast <= (read_idx == read_beats - 1);
        if (io_m_axi_rvalid && io_m_axi_rready) begin
          if (rd_base >= io_weight_base_addr) weight_read_beats <= weight_read_beats + 1;
          else input_read_beats <= input_read_beats + 1;
          last_progress_cycle <= cycle;
          read_idx <= read_idx + 1;
          if (read_idx == read_beats - 1) read_active <= 1'b0;
        end
      end
      io_m_axi_awready <= !b_pending;
      if (io_m_axi_awvalid && io_m_axi_awready) begin
        wr_base <= io_m_axi_awaddr;
        last_progress_cycle <= cycle;
      end
      io_m_axi_wready <= !b_pending;
      if (io_m_axi_wvalid && io_m_axi_wready) begin
        write_word = int'((wr_base - io_output_base_addr) >> 2);
        for (i = 0; i < 8; i = i + 1) begin
          if (write_word + i >= 0 && write_word + i < OUTPUT_WORDS) output_mem[write_word + i] <= io_m_axi_wdata[32 * i +: 32];
        end
        output_write_beats <= output_write_beats + 1;
        last_progress_cycle <= cycle;
        b_pending <= 1'b1;
      end
      if (b_pending) begin
        io_m_axi_bvalid <= 1'b1;
        if (io_m_axi_bready) begin
          b_pending <= 1'b0;
          last_progress_cycle <= cycle;
        end
      end
      if (io_res_valid) begin
        output_valid_beats <= output_valid_beats + 1;
        last_progress_cycle <= cycle;
      end
      if (dut.core.pipeline.g_layer[0].layer.core.mlp._gate_io_out_valid && dut.core.pipeline.g_layer[0].layer.core.mlp._act_io_in_ready) l0_mlp_gate_out_beats <= l0_mlp_gate_out_beats + 1;
      if (dut.core.pipeline.g_layer[0].layer.core.mlp._up_io_out_valid && dut.core.pipeline.g_layer[0].layer.core.mlp._upQ_io_enq_ready) l0_mlp_up_out_beats <= l0_mlp_up_out_beats + 1;
      if (dut.core.pipeline.g_layer[0].layer.core.mlp._act_io_out_valid && dut.core.pipeline.g_layer[0].layer.core.mlp._actQ_io_enq_ready) l0_mlp_act_out_beats <= l0_mlp_act_out_beats + 1;
      if (dut.core.pipeline.g_layer[0].layer.core.mlp._actQ_io_deq_valid && dut.core.pipeline.g_layer[0].layer.core.mlp._mul_io_lhs_ready) l0_mlp_actq_deq_beats <= l0_mlp_actq_deq_beats + 1;
      if (dut.core.pipeline.g_layer[0].layer.core.mlp._upQ_io_deq_valid && dut.core.pipeline.g_layer[0].layer.core.mlp._mul_io_rhs_ready) l0_mlp_upq_deq_beats <= l0_mlp_upq_deq_beats + 1;
      if (dut.core.pipeline.g_layer[0].layer.core.mlp._mul_io_out_valid && dut.core.pipeline.g_layer[0].layer.core.mlp._down_io_in_ready) l0_mlp_mul_out_beats <= l0_mlp_mul_out_beats + 1;
      if (dut.core.pipeline.g_layer[0].layer.core._mlp_io_out_valid && dut.core.pipeline.g_layer[0].layer.core._add2_io_computed_ready) l0_mlp_down_out_beats <= l0_mlp_down_out_beats + 1;
      if (dut.core.pipeline.g_layer[0].layer.core._add1_io_out_valid && dut.core.pipeline.g_layer[0].layer.core._rms2_io_in_ready && dut.core.pipeline.g_layer[0].layer.core._res2Q_io_enq_ready) l0_add2_res2q_enq_beats <= l0_add2_res2q_enq_beats + 1;
      if (dut.core.pipeline.g_layer[0].layer.core._res2Q_io_deq_valid && dut.core.pipeline.g_layer[0].layer.core._add2_io_residual_ready) l0_add2_res2q_deq_beats <= l0_add2_res2q_deq_beats + 1;
      if (dut.core.pipeline.g_layer[0].layer.core._mlp_io_out_valid && dut.core.pipeline.g_layer[0].layer.core._add2_io_computed_ready) l0_add2_computed_beats <= l0_add2_computed_beats + 1;
      if (dut.core.pipeline.g_layer[0].layer.core.io_out_valid && dut.core.pipeline.g_layer[0].layer.core.io_out_ready) l0_add2_out_beats <= l0_add2_out_beats + 1;
      if (dut.core.pipeline.valid[1] && dut.core.pipeline.ready[1]) begin
        pipeline_l0_out_beats <= pipeline_l0_out_beats + 1;
        last_progress_cycle <= cycle;
      end
      if (dut.core.pipeline.valid[2] && dut.core.pipeline.ready[2]) begin
        pipeline_l1_out_beats <= pipeline_l1_out_beats + 1;
        last_progress_cycle <= cycle;
      end
      if (dut.core.pipeline.valid[NUM_LAYERS] && dut.core.pipeline.ready[NUM_LAYERS]) begin
        pipeline_last_out_beats <= pipeline_last_out_beats + 1;
        last_progress_cycle <= cycle;
      end
      if (dut.core.pipeline.valid[PROBE_LAYER_A] && dut.core.pipeline.ready[PROBE_LAYER_A]) begin
        pipeline_probe_a_beats <= pipeline_probe_a_beats + 1;
        last_progress_cycle <= cycle;
      end
      if (dut.core.pipeline.valid[PROBE_LAYER_B] && dut.core.pipeline.ready[PROBE_LAYER_B]) begin
        pipeline_probe_b_beats <= pipeline_probe_b_beats + 1;
        last_progress_cycle <= cycle;
      end
      if (dut.core.pipeline.valid[PROBE_LAYER_C] && dut.core.pipeline.ready[PROBE_LAYER_C]) begin
        pipeline_probe_c_beats <= pipeline_probe_c_beats + 1;
        last_progress_cycle <= cycle;
      end
    end
  end

  initial begin
    for (i = 0; i < INPUT_WORDS; i = i + 1) input_mem[i] = 32'h0;
    for (i = 0; i < WEIGHT_WORDS; i = i + 1) weight_mem[i] = 32'h0;
    for (i = 0; i < OUTPUT_WORDS; i = i + 1) output_mem[i] = 32'h0;
    if (!$value$plusargs("INPUT_MEMH=%s", input_memh)) input_memh = "input_activation.u32.memh";
    if (!$value$plusargs("WEIGHT_MEMH=%s", weight_memh)) weight_memh = "weight_prefetch.u32.memh";
    if (!$value$plusargs("INPUT_MANIFEST=%s", input_manifest)) input_manifest = "input_manifest.json";
    if (!$value$plusargs("WEIGHT_MANIFEST=%s", weight_manifest)) weight_manifest = "packed_weight_manifest.json";
    $display("qwen_axi_board_tb manifests input=%s weight=%s", input_manifest, weight_manifest);
    $display("qwen_axi_board_tb readmemh input=%s weight=%s", input_memh, weight_memh);
    $readmemh(input_memh, input_mem);
    $readmemh(weight_memh, weight_mem);
    read_active = 1'b0;
    b_pending = 1'b0;
    input_read_beats = 0;
    weight_read_beats = 0;
    output_write_beats = 0;
    output_valid_beats = 0;
    l0_mlp_gate_out_beats = 0;
    l0_mlp_up_out_beats = 0;
    l0_mlp_act_out_beats = 0;
    l0_mlp_actq_deq_beats = 0;
    l0_mlp_upq_deq_beats = 0;
    l0_mlp_mul_out_beats = 0;
    l0_mlp_down_out_beats = 0;
    l0_add2_res2q_enq_beats = 0;
    l0_add2_res2q_deq_beats = 0;
    l0_add2_computed_beats = 0;
    l0_add2_out_beats = 0;
    pipeline_l0_out_beats = 0;
    pipeline_l1_out_beats = 0;
    pipeline_last_out_beats = 0;
    pipeline_probe_a_beats = 0;
    pipeline_probe_b_beats = 0;
    pipeline_probe_c_beats = 0;
    last_progress_cycle = 0;
    io_start = 1'b0;
    io_cfg_seqlen = 16'd16;
    io_cfg_prefill = 1'b1;
    io_cfg_single_query = 1'b0;
    io_input_base_addr = 64'h0;
    io_weight_base_addr = 64'h1000_0000;
    io_output_base_addr = 64'h2000_0000;
    io_output_stride_bytes = 32'd32;
    repeat (12) @(posedge clock);
    reset = 1'b0;
    repeat (4) @(posedge clock);
    io_start = 1'b1;
    @(posedge clock);
    io_start = 1'b0;
    for (cycle = 0; cycle < MAX_CYCLES && !io_done; cycle = cycle + 1) begin
      @(posedge clock);
      if (io_res_valid) $display("qwen_axi_board_tb out addr=%0d st=%0d last=%0d data0=0x%08x", io_res_addr, io_res_st, io_res_last, io_res[31:0]);
      if (cycle % 100000 == 0) begin
        $display("qwen_axi_board_tb progress cycle=%0d input_read_beats=%0d weight_read_beats=%0d output_valid_beats=%0d output_write_beats=%0d rd_state=%0d wr_state=%0d read_idx=%0d write_idx=%0d core_in_ready=%0d core_out_valid=%0d core_out_ready=%0d layer_vr_0=%0d/%0d layer_vr_1=%0d/%0d layer_vr_last=%0d/%0d l0_rms1=%0d l0_qkv=%0d/%0d qkv_state=%0d qkv_lin_state=%0d l0_rope=%0d l0_attn=%0d l0_outproj=%0d l0_add1=%0d l0_rms2=%0d l0_mlp=%0d mlp_gate_out_beats=%0d mlp_up_out_beats=%0d mlp_act_out_beats=%0d mlp_actq_deq_beats=%0d mlp_upq_deq_beats=%0d mlp_mul_out_beats=%0d mlp_down_out_beats=%0d mlp_in=%0d/%0d mlp_gate_out=%0d/%0d mlp_up_out=%0d/%0d mlp_act_out=%0d/%0d mlp_actq=%0d/%0d mlp_upq=%0d/%0d mlp_mul_out=%0d/%0d mlp_down_out=%0d/%0d add2_res2q_enq_beats=%0d add2_res2q_deq_beats=%0d add2_computed_beats=%0d add2_out_beats=%0d add2_residual=%0d/%0d add2_computed=%0d/%0d add2_out=%0d/%0d res2q_enq_ready=%0d pipe_l0_out_beats=%0d pipe_l1_out_beats=%0d pipe_last_out_beats=%0d pipe_link0=%0d/%0d pipe_link1=%0d/%0d pipe_last=%0d/%0d pipe_probe_a_beats=%0d pipe_probe_b_beats=%0d pipe_probe_c_beats=%0d pipe_probe_a=%0d/%0d pipe_probe_b=%0d/%0d pipe_probe_c=%0d/%0d",
                 cycle, input_read_beats, weight_read_beats, output_valid_beats, output_write_beats,
                 dut.rd_state, dut.wr_state, dut.read_idx, dut.write_idx, dut.core_in_ready, dut.core_out_valid, dut.core_out_ready,
                 dut.core.pipeline.valid[0], dut.core.pipeline.ready[0],
                 dut.core.pipeline.valid[1], dut.core.pipeline.ready[1],
                 dut.core.pipeline.valid[NUM_LAYERS], dut.core.pipeline.ready[NUM_LAYERS],
                 dut.core.pipeline.g_layer[0].layer.core._rms1_io_out_valid,
                 dut.core.pipeline.g_layer[0].layer.core._qkv_io_in_ready,
                 dut.core.pipeline.g_layer[0].layer.core._qkv_io_out_valid,
                 dut.core.pipeline.g_layer[0].layer.core.qkv.state,
                 dut.core.pipeline.g_layer[0].layer.core.qkv.linear.state,
                 dut.core.pipeline.g_layer[0].layer.core._rope_io_out_valid,
                 dut.core.pipeline.g_layer[0].layer.core._attn_io_out_valid,
                 dut.core.pipeline.g_layer[0].layer.core._outProj_io_out_valid,
                 dut.core.pipeline.g_layer[0].layer.core._add1_io_out_valid,
                 dut.core.pipeline.g_layer[0].layer.core._rms2_io_out_valid,
                 dut.core.pipeline.g_layer[0].layer.core._mlp_io_out_valid,
                 l0_mlp_gate_out_beats,
                 l0_mlp_up_out_beats,
                 l0_mlp_act_out_beats,
                 l0_mlp_actq_deq_beats,
                 l0_mlp_upq_deq_beats,
                 l0_mlp_mul_out_beats,
                 l0_mlp_down_out_beats,
                 dut.core.pipeline.g_layer[0].layer.core._rms2_io_out_valid,
                 dut.core.pipeline.g_layer[0].layer.core._mlp_io_in_ready,
                 dut.core.pipeline.g_layer[0].layer.core.mlp._gate_io_out_valid,
                 dut.core.pipeline.g_layer[0].layer.core.mlp._act_io_in_ready,
                 dut.core.pipeline.g_layer[0].layer.core.mlp._up_io_out_valid,
                 dut.core.pipeline.g_layer[0].layer.core.mlp._upQ_io_enq_ready,
                 dut.core.pipeline.g_layer[0].layer.core.mlp._act_io_out_valid,
                 dut.core.pipeline.g_layer[0].layer.core.mlp._actQ_io_enq_ready,
                 dut.core.pipeline.g_layer[0].layer.core.mlp._actQ_io_deq_valid,
                 dut.core.pipeline.g_layer[0].layer.core.mlp._mul_io_lhs_ready,
                 dut.core.pipeline.g_layer[0].layer.core.mlp._upQ_io_deq_valid,
                 dut.core.pipeline.g_layer[0].layer.core.mlp._mul_io_rhs_ready,
                 dut.core.pipeline.g_layer[0].layer.core.mlp._mul_io_out_valid,
                 dut.core.pipeline.g_layer[0].layer.core.mlp._down_io_in_ready,
                 dut.core.pipeline.g_layer[0].layer.core._mlp_io_out_valid,
                 dut.core.pipeline.g_layer[0].layer.core._add2_io_computed_ready,
                 l0_add2_res2q_enq_beats,
                 l0_add2_res2q_deq_beats,
                 l0_add2_computed_beats,
                 l0_add2_out_beats,
                 dut.core.pipeline.g_layer[0].layer.core._res2Q_io_deq_valid,
                 dut.core.pipeline.g_layer[0].layer.core._add2_io_residual_ready,
                 dut.core.pipeline.g_layer[0].layer.core._mlp_io_out_valid,
                 dut.core.pipeline.g_layer[0].layer.core._add2_io_computed_ready,
                 dut.core.pipeline.g_layer[0].layer.core.io_out_valid,
                 dut.core.pipeline.g_layer[0].layer.core.io_out_ready,
                 dut.core.pipeline.g_layer[0].layer.core._res2Q_io_enq_ready,
                 pipeline_l0_out_beats,
                 pipeline_l1_out_beats,
                 pipeline_last_out_beats,
                 dut.core.pipeline.valid[1],
                 dut.core.pipeline.ready[1],
                 dut.core.pipeline.valid[2],
                 dut.core.pipeline.ready[2],
                 dut.core.pipeline.valid[NUM_LAYERS],
                 dut.core.pipeline.ready[NUM_LAYERS],
                 pipeline_probe_a_beats,
                 pipeline_probe_b_beats,
                 pipeline_probe_c_beats,
                 dut.core.pipeline.valid[PROBE_LAYER_A],
                 dut.core.pipeline.ready[PROBE_LAYER_A],
                 dut.core.pipeline.valid[PROBE_LAYER_B],
                 dut.core.pipeline.ready[PROBE_LAYER_B],
                 dut.core.pipeline.valid[PROBE_LAYER_C],
                 dut.core.pipeline.ready[PROBE_LAYER_C]);
      end
      if (io_error) begin
        $fatal(1, "qwen_axi_board_tb FAIL io_error");
      end
      if (cycle > NO_PROGRESS_LIMIT && cycle - last_progress_cycle > NO_PROGRESS_LIMIT) begin
        $fatal(1, "qwen_axi_board_tb NO_PROGRESS cycle=%0d input_read_beats=%0d weight_read_beats=%0d output_valid_beats=%0d output_write_beats=%0d arvalid=%0d rready=%0d awvalid=%0d wvalid=%0d bready=%0d rd_state=%0d wr_state=%0d read_idx=%0d core_in_ready=%0d core_out_valid=%0d layer_vr_0=%0d/%0d layer_vr_1=%0d/%0d layer_vr_last=%0d/%0d pipe_l0_out_beats=%0d pipe_l1_out_beats=%0d pipe_last_out_beats=%0d pipe_probe_a_beats=%0d pipe_probe_b_beats=%0d pipe_probe_c_beats=%0d",
               cycle, input_read_beats, weight_read_beats, output_valid_beats, output_write_beats,
               io_m_axi_arvalid, io_m_axi_rready, io_m_axi_awvalid, io_m_axi_wvalid, io_m_axi_bready,
               dut.rd_state, dut.wr_state, dut.read_idx, dut.core_in_ready, dut.core_out_valid,
               dut.core.pipeline.valid[0], dut.core.pipeline.ready[0],
               dut.core.pipeline.valid[1], dut.core.pipeline.ready[1],
               dut.core.pipeline.valid[NUM_LAYERS], dut.core.pipeline.ready[NUM_LAYERS],
               pipeline_l0_out_beats, pipeline_l1_out_beats, pipeline_last_out_beats,
               pipeline_probe_a_beats, pipeline_probe_b_beats, pipeline_probe_c_beats);
      end
    end
    if (!io_done) begin
      $fatal(1, "qwen_axi_board_tb TIMEOUT input_read_beats=%0d weight_read_beats=%0d output_valid_beats=%0d output_write_beats=%0d",
             input_read_beats, weight_read_beats, output_valid_beats, output_write_beats);
    end
    if (input_read_beats == 0 || weight_read_beats == 0 || output_valid_beats == 0 || output_write_beats == 0) begin
      $fatal(1, "qwen_axi_board_tb FAIL incomplete real DDR path input=%0d weight=%0d out_valid=%0d out_write=%0d",
             input_read_beats, weight_read_beats, output_valid_beats, output_write_beats);
    end
    $display("qwen_axi_board_tb PASS real functional ddr path input_beats=%0d weight_beats=%0d out_valid=%0d out_write=%0d",
             input_read_beats, weight_read_beats, output_valid_beats, output_write_beats);
    $finish;
  end
endmodule
