module AxiBoardSystemTop(
  input         clock,
  input         reset,
  input         io_start,
  input  [15:0] io_cfg_seqlen,
  input         io_cfg_prefill,
  input  [31:0] io_ln1_out_inv_scale,
  input  [7:0]  io_ln1_out_zero_point,
  input  [31:0] io_q_out_inv_scale,
  input  [31:0] io_k_out_inv_scale,
  input  [31:0] io_v_out_inv_scale,
  input  [31:0] io_q_bias_scale,
  input  [31:0] io_k_bias_scale,
  input  [31:0] io_v_bias_scale,
  input  [31:0] io_dm1_out_scale,
  input  [31:0] io_dm2_ctx_inv_scale,
  input  [7:0]  io_dm2_ctx_zero_point,
  input  [31:0] io_dm2_out_inv_scale,
  input  [31:0] io_out_out_scale,
  input  [31:0] io_ln2_out_inv_scale,
  input  [7:0]  io_ln2_out_zero_point,
  input  [31:0] io_ffnup_out_inv_scale,
  input  [31:0] io_ffnup_bias_scale,
  input  [31:0] io_ffndown_out_scale,
  input  [63:0] io_input_base_addr,
  input  [63:0] io_ln1_w_base_addr,
  input  [63:0] io_qkv_w_base_addr,
  input  [63:0] io_qkv_b_base_addr,
  input  [63:0] io_sm_base_addr,
  input  [63:0] io_out_w_base_addr,
  input  [63:0] io_out_b_base_addr,
  input  [63:0] io_ln2_w_base_addr,
  input  [63:0] io_ffnup_w_base_addr,
  input  [63:0] io_ffnup_b_base_addr,
  input  [63:0] io_ffndown_w_base_addr,
  input  [63:0] io_ffndown_b_base_addr,
  input  [63:0] io_output_base_addr,
  input  [31:0] io_output_stride_bytes,
  output reg [4:0]  io_m_axi_awid,
  output reg [63:0] io_m_axi_awaddr,
  output reg [7:0]  io_m_axi_awlen,
  output reg [2:0]  io_m_axi_awsize,
  output reg [1:0]  io_m_axi_awburst,
  output reg [0:0]  io_m_axi_awlock,
  output reg [3:0]  io_m_axi_awcache,
  output reg [2:0]  io_m_axi_awprot,
  output reg [3:0]  io_m_axi_awregion,
  output reg [3:0]  io_m_axi_awqos,
  output reg        io_m_axi_awvalid,
  input             io_m_axi_awready,
  output reg [63:0] io_m_axi_wdata,
  output reg [7:0]  io_m_axi_wstrb,
  output reg        io_m_axi_wlast,
  output reg        io_m_axi_wvalid,
  input             io_m_axi_wready,
  input      [4:0]  io_m_axi_bid,
  input      [1:0]  io_m_axi_bresp,
  input             io_m_axi_bvalid,
  output reg        io_m_axi_bready,
  output reg [4:0]  io_m_axi_arid,
  output reg [63:0] io_m_axi_araddr,
  output reg [7:0]  io_m_axi_arlen,
  output reg [2:0]  io_m_axi_arsize,
  output reg [1:0]  io_m_axi_arburst,
  output reg [0:0]  io_m_axi_arlock,
  output reg [3:0]  io_m_axi_arcache,
  output reg [2:0]  io_m_axi_arprot,
  output reg [3:0]  io_m_axi_arregion,
  output reg [3:0]  io_m_axi_arqos,
  output reg        io_m_axi_arvalid,
  input             io_m_axi_arready,
  input      [4:0]  io_m_axi_rid,
  input      [63:0] io_m_axi_rdata,
  input      [1:0]  io_m_axi_rresp,
  input             io_m_axi_rlast,
  input             io_m_axi_rvalid,
  output reg        io_m_axi_rready,
  output reg [383:0] io_res,
  output reg         io_res_st,
  output reg [31:0]  io_res_addr,
  output reg         io_res_valid,
  output reg         io_res_last,
  output             io_done,
  output reg         io_error
);

  localparam integer INPUT_BEATS_MAX = 65536;
  localparam integer LN_WEIGHT_BEATS = 128;
  localparam integer QKV_WEIGHT_BEATS = 49152;
  localparam integer QKV_BIAS_BEATS = 192;
  localparam integer SM_BEATS = 26;
  localparam integer SOFTMAX_SEQ_LEN = 912;
  localparam integer OUT_WEIGHT_BEATS = 16896;
  localparam integer OUT_BIAS_BEATS = 64;
  localparam integer FFNUP_WEIGHT_BEATS = 66048;
  localparam integer FFNUP_BIAS_BEATS = 256;
  localparam integer FFNDOWN_WEIGHT_BEATS = 67584;
  localparam integer FFNDOWN_BIAS_BEATS = 64;
  localparam integer AXI_BEAT_BYTES = 8;
  localparam integer LINE_BYTES = 64;
  localparam integer LINE_BEATS = LINE_BYTES / AXI_BEAT_BYTES;
  localparam integer NUM_LAYERS = 12;
  localparam [4:0]
    ST_IDLE            = 5'd0,
    ST_LOAD_INPUT      = 5'd1,
    ST_LOAD_LN1        = 5'd2,
    ST_LOAD_QKV_W      = 5'd3,
    ST_LOAD_QKV_B      = 5'd4,
    ST_LOAD_SM         = 5'd5,
    ST_LOAD_OUT_W      = 5'd6,
    ST_LOAD_OUT_B      = 5'd7,
    ST_LOAD_LN2        = 5'd8,
    ST_LOAD_FFNUP_W    = 5'd9,
    ST_LOAD_FFNUP_B    = 5'd10,
    ST_LOAD_FFNDOWN_W  = 5'd11,
    ST_LOAD_FFNDOWN_B  = 5'd12,
    ST_WEIGHT_INIT     = 5'd13,
    ST_CORE_RESET      = 5'd14,
    ST_STREAM_LN1      = 5'd15,
    ST_STREAM_LN2      = 5'd16,
    ST_STREAM_QKV_B    = 5'd17,
    ST_STREAM_OUT_B    = 5'd18,
    ST_STREAM_FFNUP_B  = 5'd19,
    ST_STREAM_FFNDOWN_B= 5'd20,
    ST_PRELOAD_PULSE   = 5'd21,
    ST_PRELOAD_WAIT    = 5'd22,
    ST_RUN_CFG         = 5'd23,
    ST_RUN             = 5'd24,
    ST_DONE            = 5'd25,
    ST_WRITEBACK       = 5'd26;

  reg [4:0] state;
  reg [31:0] issue_count;
  reg [31:0] recv_count;
  reg [31:0] weight_init_tail;
  reg [7:0] core_reset_cnt;
  reg [7:0] preload_wait_cnt;
  reg [31:0] stream_cnt;

  reg [15:0] max_qkv_addr;
  reg [14:0] max_out_addr;
  reg [16:0] max_ffnup_addr;
  reg [16:0] max_ffndown_addr;

  reg [383:0] input_mem [0:INPUT_BEATS_MAX-1];
  reg [383:0] act_mem1 [0:INPUT_BEATS_MAX-1];
  reg [383:0] ln1_w_mem [0:LN_WEIGHT_BEATS-1];
  reg [383:0] ln2_w_mem [0:LN_WEIGHT_BEATS-1];
  reg [287:0] qkv_w_mem [0:QKV_WEIGHT_BEATS-1];
  reg [95:0]  qkv_b_mem [0:QKV_BIAS_BEATS-1];
  reg [25:0]  sm_w_mem [0:SM_BEATS-1];
  reg [287:0] out_w_mem [0:OUT_WEIGHT_BEATS-1];
  reg [383:0] out_b_mem [0:OUT_BIAS_BEATS-1];
  reg [287:0] ffnup_w_mem [0:FFNUP_WEIGHT_BEATS-1];
  reg [95:0]  ffnup_b_mem [0:FFNUP_BIAS_BEATS-1];
  reg [287:0] ffndown_w_mem [0:FFNDOWN_WEIGHT_BEATS-1];
  reg [383:0] ffndown_b_mem [0:FFNDOWN_BIAS_BEATS-1];

  reg [63:0] cur_base_addr;
  reg [31:0] cur_len;
  reg        rd_active;
  reg [2:0]  rd_beat_idx;
  reg [511:0] rd_line_buf;
  reg [63:0] ar_addr_reg;

  reg        wr_busy;
  reg [3:0]  wr_beat_idx;
  reg [511:0] wr_line_buf;
  reg [63:0] aw_addr_reg;
  reg        token_last_pending;
  reg [10:0] token_last_core_addr;
  reg [383:0] final_token_buf [0:63];
  reg [6:0]   writeback_idx;
  reg         writeback_last_token;

  reg [15:0] run_token_idx;
  reg [3:0]  layer_idx;
  reg        active_weight_bank;
  reg        active_act_bank;
  reg        weight_init_bank_sel;
  reg [1:0]  weight_init_region;
  reg [16:0] weight_init_addr;
  wire run_last_token = run_token_idx == io_cfg_seqlen;
  wire run_last_layer = layer_idx == (NUM_LAYERS - 1);
  wire [31:0] input_beats = ({16'd0, io_cfg_seqlen} + 32'd1) << 6;
  wire is_load_state =
      state == ST_LOAD_INPUT || state == ST_LOAD_LN1 || state == ST_LOAD_QKV_W ||
      state == ST_LOAD_QKV_B || state == ST_LOAD_SM || state == ST_LOAD_OUT_W ||
      state == ST_LOAD_OUT_B || state == ST_LOAD_LN2 || state == ST_LOAD_FFNUP_W ||
      state == ST_LOAD_FFNUP_B || state == ST_LOAD_FFNDOWN_W || state == ST_LOAD_FFNDOWN_B;

  wire core_weight_init_mode = 1'b0;
  wire core_layer_st = (state == ST_PRELOAD_PULSE);
  wire core_cfg_valid = (state == ST_RUN_CFG);
  wire [4:0] core_cfg_seqlen = 5'd0;
  wire core_cfg_prefill = 1'b1;
  wire core_data_in_ready = (state == ST_RUN);
  wire [15:0] core_attn_cfg_seqlen = run_token_idx;
  wire core_attn_cfg_prefill = 1'b0;
  wire core_attn_cfg_valid = (state == ST_RUN_CFG);
  wire core_attn_cfg_single_query = 1'b1;
  wire core_ln_w_valid = (state == ST_STREAM_LN1);
  wire core_ln2_w_valid = (state == ST_STREAM_LN2);
  wire core_qkv_b_valid = (state == ST_STREAM_QKV_B);
  wire core_out_b_valid = (state == ST_STREAM_OUT_B);
  wire core_ffnup_b_valid = (state == ST_STREAM_FFNUP_B);
  wire core_ffndown_b_valid = (state == ST_STREAM_FFNDOWN_B);
  wire core_reset = reset || (state == ST_CORE_RESET);
  wire [31:0] core_data_in_addr;
  wire [15:0] core_qkv_w_addr;
  wire [10:0] core_sm_w_addr;
  wire [14:0] core_out_w_addr;
  wire [16:0] core_ffnup_w_addr;
  wire [16:0] core_ffndown_w_addr;
  wire [383:0] core_res;
  wire core_res_st;
  wire [10:0] core_res_addr;
  wire core_res_valid;
  wire core_res_last;
  wire core_res_ready;

  wire [31:0] input_token_base = {10'd0, run_token_idx, 6'd0};
  wire [31:0] core_data_in_addr_abs = input_token_base + core_data_in_addr;
  wire [383:0] core_data_in =
      (core_data_in_addr_abs < INPUT_BEATS_MAX)
          ? (active_act_bank ? act_mem1[core_data_in_addr_abs] : input_mem[core_data_in_addr_abs])
          : 384'd0;
  wire [383:0] core_ln1_w_in = ln1_w_mem[stream_cnt[6:0]];
  wire [383:0] core_ln2_w_in = ln2_w_mem[stream_cnt[6:0]];
  wire [95:0]  core_qkv_b_in = qkv_b_mem[stream_cnt[7:0]];
  wire [SOFTMAX_SEQ_LEN-1:0] core_sm_w_in = make_softmax_prefix_mask(run_token_idx);
  wire [287:0] core_qkv_w_in =
      (core_qkv_w_addr < 16'd49152) ? qkv_w_mem[core_qkv_w_addr] : 288'd0;
  wire [287:0] core_out_w_in =
      (core_out_w_addr < 15'd16896) ? out_w_mem[core_out_w_addr] : 288'd0;
  wire [383:0] core_out_b_in = out_b_mem[stream_cnt[5:0]];
  wire [287:0] core_ffnup_w_in =
      (core_ffnup_w_addr < 17'd66048) ? ffnup_w_mem[core_ffnup_w_addr] : 288'd0;
  wire [95:0] core_ffnup_b_in = ffnup_b_mem[stream_cnt[7:0]];
  wire [287:0] core_ffndown_w_in =
      (core_ffndown_w_addr < 17'd67584) ? ffndown_w_mem[core_ffndown_w_addr] : 288'd0;
  wire [383:0] core_ffndown_b_in = ffndown_b_mem[stream_cnt[5:0]];
  wire core_qkv_w_preload_valid = (state == ST_WEIGHT_INIT) && (weight_init_region == 2'd0);
  wire [15:0] core_qkv_w_preload_addr = weight_init_addr[15:0];
  wire [287:0] core_qkv_w_preload_data =
      (weight_init_addr < QKV_WEIGHT_BEATS) ? qkv_w_mem[weight_init_addr[15:0]] : 288'd0;
  wire core_out_w_preload_valid = (state == ST_WEIGHT_INIT) && (weight_init_region == 2'd1);
  wire [14:0] core_out_w_preload_addr = weight_init_addr[14:0];
  wire [287:0] core_out_w_preload_data =
      (weight_init_addr < OUT_WEIGHT_BEATS) ? out_w_mem[weight_init_addr[14:0]] : 288'd0;
  wire core_ffnup_w_preload_valid = (state == ST_WEIGHT_INIT) && (weight_init_region == 2'd2);
  wire [16:0] core_ffnup_w_preload_addr = weight_init_addr;
  wire [287:0] core_ffnup_w_preload_data =
      (weight_init_addr < FFNUP_WEIGHT_BEATS) ? ffnup_w_mem[weight_init_addr] : 288'd0;
  wire core_ffndown_w_preload_valid = (state == ST_WEIGHT_INIT) && (weight_init_region == 2'd3);
  wire [16:0] core_ffndown_w_preload_addr = weight_init_addr;
  wire [287:0] core_ffndown_w_preload_data =
      (weight_init_addr < FFNDOWN_WEIGHT_BEATS) ? ffndown_w_mem[weight_init_addr] : 288'd0;
  wire [31:0] sys_res_addr = ({16'd0, run_token_idx} << 6) + {{21{1'b0}}, core_res_addr};
  wire [31:0] writeback_sys_res_addr = ({16'd0, run_token_idx} << 6) + {{25{1'b0}}, writeback_idx[5:0]};
  wire [63:0] output_byte_addr = io_output_base_addr + ({32'd0, sys_res_addr} * {32'd0, io_output_stride_bytes});
  wire [63:0] writeback_output_byte_addr = io_output_base_addr + ({32'd0, writeback_sys_res_addr} * {32'd0, io_output_stride_bytes});
  wire [63:0] next_line_addr = cur_base_addr + ({32'd0, issue_count} << 6);

  function automatic [SOFTMAX_SEQ_LEN-1:0] make_softmax_prefix_mask;
    input [15:0] upto_token;
    integer i;
    begin
      make_softmax_prefix_mask = {SOFTMAX_SEQ_LEN{1'b0}};
      for (i = 0; i < SOFTMAX_SEQ_LEN; i = i + 1) begin
        if (i <= upto_token) begin
          make_softmax_prefix_mask[i] = 1'b1;
        end
      end
    end
  endfunction

  Top u_core (
    .clock(clock),
    .reset(core_reset),
    .io_layer_st(core_layer_st),
    .io_cfg_seqlen(core_cfg_seqlen),
    .io_cfg_prefill(core_cfg_prefill),
    .io_cfg_valid(core_cfg_valid),
    .io_attn_cfg_seqlen(core_attn_cfg_seqlen),
    .io_attn_cfg_prefill(core_attn_cfg_prefill),
    .io_attn_cfg_valid(core_attn_cfg_valid),
    .io_attn_cfg_single_query(core_attn_cfg_single_query),
    .io_weight_init_mode(core_weight_init_mode),
    .io_weight_active_bank(active_weight_bank),
    .io_weight_preload_bank(weight_init_bank_sel),
    .io_data_in(core_data_in),
    .io_data_in_ready(core_data_in_ready),
    .io_data_in_addr(core_data_in_addr),
    .io_ln_w_in(core_ln1_w_in),
    .io_ln_w_valid(core_ln_w_valid),
    .io_ln1_out_inv_scale(io_ln1_out_inv_scale),
    .io_ln1_out_zero_point(io_ln1_out_zero_point),
    .io_q_out_inv_scale(io_q_out_inv_scale),
    .io_k_out_inv_scale(io_k_out_inv_scale),
    .io_v_out_inv_scale(io_v_out_inv_scale),
    .io_q_bias_scale(io_q_bias_scale),
    .io_k_bias_scale(io_k_bias_scale),
    .io_v_bias_scale(io_v_bias_scale),
    .io_dm1_out_scale(io_dm1_out_scale),
    .io_dm2_ctx_inv_scale(io_dm2_ctx_inv_scale),
    .io_dm2_ctx_zero_point(io_dm2_ctx_zero_point),
    .io_dm2_out_inv_scale(io_dm2_out_inv_scale),
    .io_out_out_scale(io_out_out_scale),
    .io_ln2_out_inv_scale(io_ln2_out_inv_scale),
    .io_ln2_out_zero_point(io_ln2_out_zero_point),
    .io_ffnup_out_inv_scale(io_ffnup_out_inv_scale),
    .io_ffnup_bias_scale(io_ffnup_bias_scale),
    .io_ffndown_out_scale(io_ffndown_out_scale),
    .io_qkv_w_in(core_qkv_w_in),
    .io_qkv_w_addr(core_qkv_w_addr),
    .io_qkv_w_preload_valid(core_qkv_w_preload_valid),
    .io_qkv_w_preload_addr(core_qkv_w_preload_addr),
    .io_qkv_w_preload_data(core_qkv_w_preload_data),
    .io_qkv_b_in(core_qkv_b_in),
    .io_qkv_b_valid(core_qkv_b_valid),
    .io_sm_w_in(core_sm_w_in),
    .io_sm_w_addr(core_sm_w_addr),
    .io_out_w_in(core_out_w_in),
    .io_out_w_addr(core_out_w_addr),
    .io_out_w_preload_valid(core_out_w_preload_valid),
    .io_out_w_preload_addr(core_out_w_preload_addr),
    .io_out_w_preload_data(core_out_w_preload_data),
    .io_out_b_in(core_out_b_in),
    .io_out_b_valid(core_out_b_valid),
    .io_ln2_w_in(core_ln2_w_in),
    .io_ln2_w_valid(core_ln2_w_valid),
    .io_ffnup_w_in(core_ffnup_w_in),
    .io_ffnup_w_addr(core_ffnup_w_addr),
    .io_ffnup_w_preload_valid(core_ffnup_w_preload_valid),
    .io_ffnup_w_preload_addr(core_ffnup_w_preload_addr),
    .io_ffnup_w_preload_data(core_ffnup_w_preload_data),
    .io_ffnup_b_in(core_ffnup_b_in),
    .io_ffnup_b_valid(core_ffnup_b_valid),
    .io_ffndown_w_in(core_ffndown_w_in),
    .io_ffndown_w_addr(core_ffndown_w_addr),
    .io_ffndown_w_preload_valid(core_ffndown_w_preload_valid),
    .io_ffndown_w_preload_addr(core_ffndown_w_preload_addr),
    .io_ffndown_w_preload_data(core_ffndown_w_preload_data),
    .io_ffndown_b_in(core_ffndown_b_in),
    .io_ffndown_b_valid(core_ffndown_b_valid),
    .io_res(core_res),
    .io_res_st(core_res_st),
    .io_res_addr(core_res_addr),
    .io_res_valid(core_res_valid),
    .io_res_last(core_res_last),
    .io_res_ready(core_res_ready)
  );

  assign io_done = (state == ST_DONE);
  assign core_res_ready = (state == ST_RUN);

  always @(*) begin
    case (state)
      ST_LOAD_INPUT: begin
        cur_base_addr = io_input_base_addr;
        cur_len = input_beats;
      end
      ST_LOAD_LN1: begin
        cur_base_addr = io_ln1_w_base_addr;
        cur_len = LN_WEIGHT_BEATS;
      end
      ST_LOAD_QKV_W: begin
        cur_base_addr = io_qkv_w_base_addr;
        cur_len = QKV_WEIGHT_BEATS;
      end
      ST_LOAD_QKV_B: begin
        cur_base_addr = io_qkv_b_base_addr;
        cur_len = QKV_BIAS_BEATS;
      end
      ST_LOAD_SM: begin
        cur_base_addr = io_sm_base_addr;
        cur_len = SM_BEATS;
      end
      ST_LOAD_OUT_W: begin
        cur_base_addr = io_out_w_base_addr;
        cur_len = OUT_WEIGHT_BEATS;
      end
      ST_LOAD_OUT_B: begin
        cur_base_addr = io_out_b_base_addr;
        cur_len = OUT_BIAS_BEATS;
      end
      ST_LOAD_LN2: begin
        cur_base_addr = io_ln2_w_base_addr;
        cur_len = LN_WEIGHT_BEATS;
      end
      ST_LOAD_FFNUP_W: begin
        cur_base_addr = io_ffnup_w_base_addr;
        cur_len = FFNUP_WEIGHT_BEATS;
      end
      ST_LOAD_FFNUP_B: begin
        cur_base_addr = io_ffnup_b_base_addr;
        cur_len = FFNUP_BIAS_BEATS;
      end
      ST_LOAD_FFNDOWN_W: begin
        cur_base_addr = io_ffndown_w_base_addr;
        cur_len = FFNDOWN_WEIGHT_BEATS;
      end
      ST_LOAD_FFNDOWN_B: begin
        cur_base_addr = io_ffndown_b_base_addr;
        cur_len = FFNDOWN_BIAS_BEATS;
      end
      default: begin
        cur_base_addr = 64'd0;
        cur_len = 32'd0;
      end
    endcase
  end

  always @(posedge clock) begin
    if (reset) begin
      state <= ST_IDLE;
      issue_count <= 32'd0;
      recv_count <= 32'd0;
      weight_init_tail <= 32'd0;
      core_reset_cnt <= 8'd0;
      preload_wait_cnt <= 8'd0;
      stream_cnt <= 32'd0;
      run_token_idx <= 16'd0;
      layer_idx <= 4'd0;
      active_weight_bank <= 1'b0;
      active_act_bank <= 1'b0;
      weight_init_bank_sel <= 1'b0;
      weight_init_region <= 2'd0;
      weight_init_addr <= 17'd0;
      max_qkv_addr <= 16'd0;
      max_out_addr <= 15'd0;
      max_ffnup_addr <= 17'd0;
      max_ffndown_addr <= 17'd0;

      io_m_axi_awid <= 5'd0;
      io_m_axi_awaddr <= 64'd0;
      io_m_axi_awlen <= 8'd7;
      io_m_axi_awsize <= 3'd3;
      io_m_axi_awburst <= 2'b01;
      io_m_axi_awlock <= 1'b0;
      io_m_axi_awcache <= 4'd0;
      io_m_axi_awprot <= 3'd0;
      io_m_axi_awregion <= 4'd0;
      io_m_axi_awqos <= 4'd0;
      io_m_axi_awvalid <= 1'b0;

      io_m_axi_wdata <= 64'd0;
      io_m_axi_wstrb <= 8'd0;
      io_m_axi_wlast <= 1'b0;
      io_m_axi_wvalid <= 1'b0;
      io_m_axi_bready <= 1'b0;

      io_m_axi_arid <= 5'd0;
      io_m_axi_araddr <= 64'd0;
      io_m_axi_arlen <= 8'd7;
      io_m_axi_arsize <= 3'd3;
      io_m_axi_arburst <= 2'b01;
      io_m_axi_arlock <= 1'b0;
      io_m_axi_arcache <= 4'd0;
      io_m_axi_arprot <= 3'd0;
      io_m_axi_arregion <= 4'd0;
      io_m_axi_arqos <= 4'd0;
      io_m_axi_arvalid <= 1'b0;
      io_m_axi_rready <= 1'b0;

      rd_active <= 1'b0;
      rd_beat_idx <= 3'd0;
      rd_line_buf <= 512'd0;
      ar_addr_reg <= 64'd0;

      wr_busy <= 1'b0;
      wr_beat_idx <= 4'd0;
      wr_line_buf <= 512'd0;
      aw_addr_reg <= 64'd0;
      token_last_pending <= 1'b0;
      writeback_idx <= 7'd0;
      writeback_last_token <= 1'b0;
      token_last_core_addr <= 11'd0;

      io_res <= 384'd0;
      io_res_st <= 1'b0;
      io_res_addr <= 32'd0;
      io_res_valid <= 1'b0;
      io_res_last <= 1'b0;
      io_error <= 1'b0;
    end else begin
      io_res_valid <= 1'b0;

      if (io_m_axi_rvalid && io_m_axi_rready && io_m_axi_rresp != 2'b00) begin
        io_error <= 1'b1;
      end
      if (io_m_axi_bvalid && io_m_axi_bready && io_m_axi_bresp != 2'b00) begin
        io_error <= 1'b1;
      end

      if (is_load_state && !io_m_axi_arvalid && !rd_active && (issue_count < cur_len)) begin
        ar_addr_reg <= next_line_addr;
        io_m_axi_arid <= 5'd0;
        io_m_axi_araddr <= next_line_addr;
        io_m_axi_arlen <= LINE_BEATS - 1;
        io_m_axi_arsize <= 3'd3;
        io_m_axi_arburst <= 2'b01;
        io_m_axi_arlock <= 1'b0;
        io_m_axi_arcache <= 4'd0;
        io_m_axi_arprot <= 3'd0;
        io_m_axi_arregion <= 4'd0;
        io_m_axi_arqos <= 4'd0;
        io_m_axi_arvalid <= 1'b1;
      end else if (!is_load_state) begin
        io_m_axi_arvalid <= 1'b0;
      end

      if (io_m_axi_arvalid && io_m_axi_arready) begin
        io_m_axi_arvalid <= 1'b0;
        io_m_axi_rready <= 1'b1;
        rd_active <= 1'b1;
        rd_beat_idx <= 3'd0;
        issue_count <= issue_count + 32'd1;
      end

      if (rd_active && io_m_axi_rvalid && io_m_axi_rready) begin
        rd_line_buf[rd_beat_idx * 64 +: 64] <= io_m_axi_rdata;
        if (io_m_axi_rlast) begin
          rd_active <= 1'b0;
          io_m_axi_rready <= 1'b0;
          case (state)
            ST_LOAD_INPUT: begin
              if (recv_count < INPUT_BEATS_MAX) input_mem[recv_count] <= {io_m_axi_rdata, rd_line_buf[447:0]}[383:0];
            end
            ST_LOAD_LN1: begin
              ln1_w_mem[recv_count[6:0]] <= {io_m_axi_rdata, rd_line_buf[447:0]}[383:0];
            end
            ST_LOAD_QKV_W: begin
              qkv_w_mem[recv_count[15:0]] <= {io_m_axi_rdata, rd_line_buf[447:0]}[287:0];
            end
            ST_LOAD_QKV_B: begin
              qkv_b_mem[recv_count[7:0]] <= {io_m_axi_rdata, rd_line_buf[447:0]}[95:0];
            end
            ST_LOAD_SM: begin
              sm_w_mem[recv_count[4:0]] <= {io_m_axi_rdata, rd_line_buf[447:0]}[25:0];
            end
            ST_LOAD_OUT_W: begin
              out_w_mem[recv_count[14:0]] <= {io_m_axi_rdata, rd_line_buf[447:0]}[287:0];
            end
            ST_LOAD_OUT_B: begin
              out_b_mem[recv_count[5:0]] <= {io_m_axi_rdata, rd_line_buf[447:0]}[383:0];
            end
            ST_LOAD_LN2: begin
              ln2_w_mem[recv_count[6:0]] <= {io_m_axi_rdata, rd_line_buf[447:0]}[383:0];
            end
            ST_LOAD_FFNUP_W: begin
              ffnup_w_mem[recv_count[16:0]] <= {io_m_axi_rdata, rd_line_buf[447:0]}[287:0];
            end
            ST_LOAD_FFNUP_B: begin
              ffnup_b_mem[recv_count[7:0]] <= {io_m_axi_rdata, rd_line_buf[447:0]}[95:0];
            end
            ST_LOAD_FFNDOWN_W: begin
              ffndown_w_mem[recv_count[16:0]] <= {io_m_axi_rdata, rd_line_buf[447:0]}[287:0];
            end
            ST_LOAD_FFNDOWN_B: begin
              ffndown_b_mem[recv_count[5:0]] <= {io_m_axi_rdata, rd_line_buf[447:0]}[383:0];
            end
            default: begin
            end
          endcase

          if (recv_count + 32'd1 == cur_len) begin
            issue_count <= 32'd0;
            recv_count <= 32'd0;
            case (state)
              ST_LOAD_INPUT: state <= ST_LOAD_LN1;
              ST_LOAD_LN1: state <= ST_LOAD_QKV_W;
              ST_LOAD_QKV_W: state <= ST_LOAD_QKV_B;
              ST_LOAD_QKV_B: state <= ST_LOAD_SM;
              ST_LOAD_SM: state <= ST_LOAD_OUT_W;
              ST_LOAD_OUT_W: state <= ST_LOAD_OUT_B;
              ST_LOAD_OUT_B: state <= ST_LOAD_LN2;
              ST_LOAD_LN2: state <= ST_LOAD_FFNUP_W;
              ST_LOAD_FFNUP_W: state <= ST_LOAD_FFNUP_B;
              ST_LOAD_FFNUP_B: state <= ST_LOAD_FFNDOWN_W;
              ST_LOAD_FFNDOWN_W: state <= ST_LOAD_FFNDOWN_B;
              default: begin
                state <= ST_WEIGHT_INIT;
                weight_init_bank_sel <= 1'b0;
                weight_init_region <= 2'd0;
                weight_init_addr <= 17'd0;
              end
            endcase
          end else begin
            recv_count <= recv_count + 32'd1;
          end
        end else begin
          rd_beat_idx <= rd_beat_idx + 3'd1;
        end
      end

      if (state == ST_RUN && core_res_valid && core_res_ready) begin
        if (run_last_layer) begin
          final_token_buf[core_res_addr[5:0]] <= core_res;
          io_res <= core_res;
          io_res_st <= core_res_st;
          io_res_addr <= sys_res_addr;
          io_res_last <= core_res_last;
          io_res_valid <= 1'b1;
        end else begin
          if (active_act_bank) begin
            input_mem[sys_res_addr] <= core_res;
          end else begin
            act_mem1[sys_res_addr] <= core_res;
          end
        end

        if (core_res_last) begin
          token_last_pending <= 1'b1;
          token_last_core_addr <= core_res_addr;
        end
      end

      if (!wr_busy && state == ST_WRITEBACK && writeback_idx < 7'd64) begin
        wr_busy <= 1'b1;
        wr_beat_idx <= 4'd0;
        wr_line_buf <= {128'd0, final_token_buf[writeback_idx[5:0]]};
        aw_addr_reg <= writeback_output_byte_addr;
        io_m_axi_awid <= 5'd0;
        io_m_axi_awaddr <= writeback_output_byte_addr;
        io_m_axi_awlen <= LINE_BEATS - 1;
        io_m_axi_awsize <= 3'd3;
        io_m_axi_awburst <= 2'b01;
        io_m_axi_awlock <= 1'b0;
        io_m_axi_awcache <= 4'd0;
        io_m_axi_awprot <= 3'd0;
        io_m_axi_awregion <= 4'd0;
        io_m_axi_awqos <= 4'd0;
        io_m_axi_awvalid <= 1'b1;
      end

      if (io_m_axi_awvalid && io_m_axi_awready) begin
        io_m_axi_awvalid <= 1'b0;
        io_m_axi_wdata <= wr_line_buf[63:0];
        io_m_axi_wstrb <= 8'hff;
        io_m_axi_wlast <= 1'b0;
        io_m_axi_wvalid <= 1'b1;
        wr_beat_idx <= 4'd1;
      end else if (io_m_axi_wvalid && io_m_axi_wready) begin
        if (wr_beat_idx == 4'd6) begin
          io_m_axi_wdata <= wr_line_buf[447:384];
          io_m_axi_wstrb <= 8'h00;
          io_m_axi_wlast <= 1'b0;
          io_m_axi_wvalid <= 1'b1;
          wr_beat_idx <= 4'd7;
        end else if (wr_beat_idx == 4'd7) begin
          io_m_axi_wdata <= wr_line_buf[511:448];
          io_m_axi_wstrb <= 8'h00;
          io_m_axi_wlast <= 1'b1;
          io_m_axi_wvalid <= 1'b1;
          wr_beat_idx <= 4'd8;
        end else if (wr_beat_idx == 4'd8) begin
          io_m_axi_wvalid <= 1'b0;
          io_m_axi_wlast <= 1'b0;
          io_m_axi_bready <= 1'b1;
        end else begin
          io_m_axi_wdata <= wr_line_buf[wr_beat_idx * 64 +: 64];
          io_m_axi_wstrb <= 8'hff;
          io_m_axi_wlast <= 1'b0;
          io_m_axi_wvalid <= 1'b1;
          wr_beat_idx <= wr_beat_idx + 4'd1;
        end
      end

      if (io_m_axi_bvalid && io_m_axi_bready) begin
        io_m_axi_bready <= 1'b0;
        wr_busy <= 1'b0;
        if (state == ST_WRITEBACK) begin
          if (writeback_idx == 7'd63) begin
            if (writeback_last_token) begin
              state <= ST_DONE;
            end else begin
              run_token_idx <= run_token_idx + 16'd1;
              state <= ST_RUN_CFG;
            end
          end else begin
            writeback_idx <= writeback_idx + 7'd1;
          end
        end
      end

      case (state)
        ST_IDLE: begin
          issue_count <= 32'd0;
          recv_count <= 32'd0;
          run_token_idx <= 16'd0;
          layer_idx <= 4'd0;
          active_weight_bank <= 1'b0;
          active_act_bank <= 1'b0;
          weight_init_bank_sel <= 1'b0;
          weight_init_region <= 2'd0;
          weight_init_addr <= 17'd0;
          token_last_pending <= 1'b0;
          if (io_start) begin
            state <= ST_LOAD_INPUT;
          end
        end
        ST_WEIGHT_INIT: begin
          case (weight_init_region)
            2'd0: begin
              if (weight_init_addr == QKV_WEIGHT_BEATS - 1) begin
                weight_init_region <= 2'd1;
                weight_init_addr <= 17'd0;
              end else begin
                weight_init_addr <= weight_init_addr + 17'd1;
              end
            end
            2'd1: begin
              if (weight_init_addr == OUT_WEIGHT_BEATS - 1) begin
                weight_init_region <= 2'd2;
                weight_init_addr <= 17'd0;
              end else begin
                weight_init_addr <= weight_init_addr + 17'd1;
              end
            end
            2'd2: begin
              if (weight_init_addr == FFNUP_WEIGHT_BEATS - 1) begin
                weight_init_region <= 2'd3;
                weight_init_addr <= 17'd0;
              end else begin
                weight_init_addr <= weight_init_addr + 17'd1;
              end
            end
            default: begin
              if (weight_init_addr == FFNDOWN_WEIGHT_BEATS - 1) begin
                if (!weight_init_bank_sel) begin
                  weight_init_bank_sel <= 1'b1;
                  weight_init_region <= 2'd0;
                  weight_init_addr <= 17'd0;
                end else begin
                  state <= ST_CORE_RESET;
                  core_reset_cnt <= 8'd0;
                end
              end else begin
                weight_init_addr <= weight_init_addr + 17'd1;
              end
            end
          endcase
        end
        ST_CORE_RESET: begin
          core_reset_cnt <= core_reset_cnt + 8'd1;
          if (core_reset_cnt == 8'd5) begin
            state <= ST_STREAM_LN1;
            stream_cnt <= 32'd0;
          end
        end
        ST_STREAM_LN1: begin
          stream_cnt <= stream_cnt + 32'd1;
          if (stream_cnt + 32'd1 == LN_WEIGHT_BEATS) begin
            state <= ST_STREAM_LN2;
            stream_cnt <= 32'd0;
          end
        end
        ST_STREAM_LN2: begin
          stream_cnt <= stream_cnt + 32'd1;
          if (stream_cnt + 32'd1 == LN_WEIGHT_BEATS) begin
            state <= ST_STREAM_QKV_B;
            stream_cnt <= 32'd0;
          end
        end
        ST_STREAM_QKV_B: begin
          stream_cnt <= stream_cnt + 32'd1;
          if (stream_cnt + 32'd1 == QKV_BIAS_BEATS) begin
            state <= ST_STREAM_OUT_B;
            stream_cnt <= 32'd0;
          end
        end
        ST_STREAM_OUT_B: begin
          stream_cnt <= stream_cnt + 32'd1;
          if (stream_cnt + 32'd1 == OUT_BIAS_BEATS) begin
            state <= ST_STREAM_FFNUP_B;
            stream_cnt <= 32'd0;
          end
        end
        ST_STREAM_FFNUP_B: begin
          stream_cnt <= stream_cnt + 32'd1;
          if (stream_cnt + 32'd1 == FFNUP_BIAS_BEATS) begin
            state <= ST_STREAM_FFNDOWN_B;
            stream_cnt <= 32'd0;
          end
        end
        ST_STREAM_FFNDOWN_B: begin
          stream_cnt <= stream_cnt + 32'd1;
          if (stream_cnt + 32'd1 == FFNDOWN_BIAS_BEATS) begin
            run_token_idx <= 16'd0;
            token_last_pending <= 1'b0;
            state <= ST_RUN_CFG;
          end
        end
        ST_RUN_CFG: begin
          state <= ST_PRELOAD_PULSE;
        end
        ST_PRELOAD_PULSE: begin
          state <= ST_PRELOAD_WAIT;
          preload_wait_cnt <= 8'd0;
        end
        ST_PRELOAD_WAIT: begin
          preload_wait_cnt <= preload_wait_cnt + 8'd1;
          if (preload_wait_cnt == 8'd63) begin
            state <= ST_RUN;
          end
        end
        ST_RUN: begin
          if (token_last_pending) begin
            $display(
              "AxiBoardSystemTop token-done layer=%0d token=%0d cfg_seqlen=%0d run_last_token=%0d run_last_layer=%0d core_res_addr=%0d sys_res_addr=%0d",
              layer_idx,
              run_token_idx,
              io_cfg_seqlen,
              run_last_token,
              run_last_layer,
              token_last_core_addr,
              (({16'd0, run_token_idx} << 6) + {{21{1'b0}}, token_last_core_addr})
            );
            token_last_pending <= 1'b0;
            if (run_last_layer) begin
              writeback_idx <= 7'd0;
              writeback_last_token <= run_last_token;
              state <= ST_WRITEBACK;
            end else if (run_last_token) begin
              layer_idx <= layer_idx + 4'd1;
              active_weight_bank <= ~active_weight_bank;
              active_act_bank <= ~active_act_bank;
              run_token_idx <= 16'd0;
              state <= ST_CORE_RESET;
              core_reset_cnt <= 8'd0;
            end else begin
              run_token_idx <= run_token_idx + 16'd1;
              state <= ST_RUN_CFG;
            end
          end
        end
        ST_WRITEBACK: begin
        end
        ST_DONE: begin
        end
        default: begin
        end
      endcase
    end
  end

endmodule
