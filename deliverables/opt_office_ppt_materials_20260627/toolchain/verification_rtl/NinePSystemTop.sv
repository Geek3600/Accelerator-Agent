// 9P-side DDR-only system wrapper.
// 当前保留最小 DDR 取数 + core 驱动骨架，并以 token-by-token 调度跑 full-seq。
// 非 attention 主链保持单 token；attention 单独看到完整历史长度。
module NinePSystemTop(
  input         clock,
  input         reset,
  input         io_start,
  input  [15:0] io_cfg_seqlen,
  input         io_cfg_prefill,
  input  [15:0] io_attn_cfg_seqlen,
  input         io_attn_cfg_prefill,
  input         io_attn_cfg_valid,
  input         io_attn_cfg_single_query,
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
  input  [31:0] io_input_base_addr,
  input  [31:0] io_ln1_w_base_addr,
  input  [31:0] io_qkv_w_base_addr,
  input  [31:0] io_qkv_b_base_addr,
  input  [31:0] io_sm_base_addr,
  input  [31:0] io_out_w_base_addr,
  input  [31:0] io_out_b_base_addr,
  input  [31:0] io_ln2_w_base_addr,
  input  [31:0] io_ffnup_w_base_addr,
  input  [31:0] io_ffnup_b_base_addr,
  input  [31:0] io_ffndown_w_base_addr,
  input  [31:0] io_ffndown_b_base_addr,
  output reg [31:0]  io_ddr_addr,
  output reg [2:0]   io_ddr_cmd,
  output reg         io_ddr_en,
  input              io_ddr_rdy,
  input      [511:0] io_ddr_rd_data,
  input              io_ddr_rd_data_valid,
  input              io_ddr_rd_data_end,
  input              io_ddr_init_done,
  output     [383:0] io_res,
  output             io_res_st,
  output     [31:0]  io_res_addr,
  output             io_res_valid,
  output             io_res_last,
  input              io_res_ready
);

  localparam integer DDR_WORD_W = 512;
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
    ST_DONE            = 5'd25;

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

  wire [31:0] input_beats = ({16'd0, io_cfg_seqlen} + 32'd1) << 6;

  reg [31:0] cur_base_addr;
  reg [31:0] cur_len;

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
        cur_base_addr = 32'd0;
        cur_len = 32'd0;
      end
    endcase
  end

  wire is_load_state =
      state == ST_LOAD_INPUT || state == ST_LOAD_LN1 || state == ST_LOAD_QKV_W ||
      state == ST_LOAD_QKV_B || state == ST_LOAD_SM || state == ST_LOAD_OUT_W ||
      state == ST_LOAD_OUT_B || state == ST_LOAD_LN2 || state == ST_LOAD_FFNUP_W ||
      state == ST_LOAD_FFNUP_B || state == ST_LOAD_FFNDOWN_W || state == ST_LOAD_FFNDOWN_B;

  reg [15:0] run_token_idx;
  wire run_last_token = run_token_idx == io_cfg_seqlen;
  wire [31:0] input_token_base = {10'd0, run_token_idx, 6'd0};

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

  wire core_weight_init_mode = (state == ST_WEIGHT_INIT);
  wire core_layer_st = (state == ST_WEIGHT_INIT && weight_init_tail == 0) || (state == ST_PRELOAD_PULSE);
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
  wire [47:0] core_attn_tap_data_unused;
  wire [3:0] core_attn_tap_head_unused;
  wire [31:0] core_attn_tap_addr_unused;
  wire core_attn_tap_valid_unused;
  wire core_attn_tap_last_unused;
  wire core_attn_dm1_override_ready_unused;
  wire core_attn_dm2_v_override_ready_unused;

  wire [31:0] core_data_in_addr_abs = input_token_base + core_data_in_addr;
  wire [383:0] core_data_in =
      (core_data_in_addr_abs < INPUT_BEATS_MAX) ? input_mem[core_data_in_addr_abs] : 384'd0;
  wire [383:0] core_ln1_w_in = ln1_w_mem[stream_cnt[6:0]];
  wire [383:0] core_ln2_w_in = ln2_w_mem[stream_cnt[6:0]];
  wire [95:0]  core_qkv_b_in = qkv_b_mem[stream_cnt[7:0]];
  // Full-seq token-by-token verification uses a causal prefix mask for attention.
  // The old all-zero tie-off forced Softmax in_mask false on every lane, collapsing
  // attention probabilities to zero and poisoning the whole integrated path.
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
    .io_weight_active_bank(1'b0),
    .io_weight_preload_bank(1'b0),
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
    .io_qkv_w_preload_valid(1'b0),
    .io_qkv_w_preload_addr(16'd0),
    .io_qkv_w_preload_data(288'd0),
    .io_qkv_b_in(core_qkv_b_in),
    .io_qkv_b_valid(core_qkv_b_valid),
    .io_sm_w_in(core_sm_w_in),
    .io_sm_w_addr(core_sm_w_addr),
    .io_out_w_in(core_out_w_in),
    .io_out_w_addr(core_out_w_addr),
    .io_out_w_preload_valid(1'b0),
    .io_out_w_preload_addr(15'd0),
    .io_out_w_preload_data(288'd0),
    .io_out_b_in(core_out_b_in),
    .io_out_b_valid(core_out_b_valid),
    .io_ln2_w_in(core_ln2_w_in),
    .io_ln2_w_valid(core_ln2_w_valid),
    .io_ffnup_w_in(core_ffnup_w_in),
    .io_ffnup_w_addr(core_ffnup_w_addr),
    .io_ffnup_w_preload_valid(1'b0),
    .io_ffnup_w_preload_addr(17'd0),
    .io_ffnup_w_preload_data(288'd0),
    .io_ffnup_b_in(core_ffnup_b_in),
    .io_ffnup_b_valid(core_ffnup_b_valid),
    .io_ffndown_w_in(core_ffndown_w_in),
    .io_ffndown_w_addr(core_ffndown_w_addr),
    .io_ffndown_w_preload_valid(1'b0),
    .io_ffndown_w_preload_addr(17'd0),
    .io_ffndown_w_preload_data(288'd0),
    .io_ffndown_b_in(core_ffndown_b_in),
    .io_ffndown_b_valid(core_ffndown_b_valid),
    .io_attn_tap_data(core_attn_tap_data_unused),
    .io_attn_tap_head(core_attn_tap_head_unused),
    .io_attn_tap_addr(core_attn_tap_addr_unused),
    .io_attn_tap_valid(core_attn_tap_valid_unused),
    .io_attn_tap_last(core_attn_tap_last_unused),
    .io_attn_dm1_override_enable(1'b0),
    .io_attn_dm1_override_data('0),
    .io_attn_dm1_override_st(1'b0),
    .io_attn_dm1_override_addr('0),
    .io_attn_dm1_override_valid(1'b0),
    .io_attn_dm1_override_last(1'b0),
    .io_attn_dm1_override_ready(core_attn_dm1_override_ready_unused),
    .io_attn_dm2_v_override_enable(1'b0),
    .io_attn_dm2_v_override_data('0),
    .io_attn_dm2_v_override_valid(1'b0),
    .io_attn_dm2_v_override_ready(core_attn_dm2_v_override_ready_unused),
    .io_res(core_res),
    .io_res_st(core_res_st),
    .io_res_addr(core_res_addr),
    .io_res_valid(core_res_valid),
    .io_res_last(core_res_last),
    .io_res_ready(io_res_ready)
  );

  assign io_res = core_res;
  assign io_res_st = core_res_st;
  assign io_res_valid = core_res_valid;
  assign io_res_last = core_res_last;
  assign io_res_addr = ({16'd0, run_token_idx} << 6) + {{21{1'b0}}, core_res_addr};

  always @(*) begin
    io_ddr_en = 1'b0;
    io_ddr_cmd = 3'b001;
    io_ddr_addr = 32'd0;
    if (is_load_state && io_ddr_init_done && issue_count < cur_len) begin
      io_ddr_en = 1'b1;
      io_ddr_addr = cur_base_addr + issue_count;
    end
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
      max_qkv_addr <= 16'd0;
      max_out_addr <= 15'd0;
      max_ffnup_addr <= 17'd0;
      max_ffndown_addr <= 17'd0;
    end else begin
      if (io_ddr_en && io_ddr_rdy) begin
        issue_count <= issue_count + 32'd1;
      end

      if (io_ddr_rd_data_valid) begin
        case (state)
          ST_LOAD_INPUT: begin
            if (recv_count < INPUT_BEATS_MAX) input_mem[recv_count] <= io_ddr_rd_data[383:0];
          end
          ST_LOAD_LN1: begin
            ln1_w_mem[recv_count[6:0]] <= io_ddr_rd_data[383:0];
          end
          ST_LOAD_QKV_W: begin
            qkv_w_mem[recv_count[15:0]] <= io_ddr_rd_data[287:0];
          end
          ST_LOAD_QKV_B: begin
            qkv_b_mem[recv_count[7:0]] <= io_ddr_rd_data[95:0];
          end
          ST_LOAD_SM: begin
            sm_w_mem[recv_count[4:0]] <= io_ddr_rd_data[25:0];
          end
          ST_LOAD_OUT_W: begin
            out_w_mem[recv_count[14:0]] <= io_ddr_rd_data[287:0];
          end
          ST_LOAD_OUT_B: begin
            out_b_mem[recv_count[5:0]] <= io_ddr_rd_data[383:0];
          end
          ST_LOAD_LN2: begin
            ln2_w_mem[recv_count[6:0]] <= io_ddr_rd_data[383:0];
          end
          ST_LOAD_FFNUP_W: begin
            ffnup_w_mem[recv_count[16:0]] <= io_ddr_rd_data[287:0];
          end
          ST_LOAD_FFNUP_B: begin
            ffnup_b_mem[recv_count[7:0]] <= io_ddr_rd_data[95:0];
          end
          ST_LOAD_FFNDOWN_W: begin
            ffndown_w_mem[recv_count[16:0]] <= io_ddr_rd_data[287:0];
          end
          ST_LOAD_FFNDOWN_B: begin
            ffndown_b_mem[recv_count[5:0]] <= io_ddr_rd_data[383:0];
          end
          default: begin
          end
        endcase
        recv_count <= recv_count + 32'd1;
      end

      case (state)
        ST_IDLE: begin
          issue_count <= 32'd0;
          recv_count <= 32'd0;
          run_token_idx <= 16'd0;
          if (io_start && io_ddr_init_done) begin
            state <= ST_LOAD_INPUT;
          end
        end
        ST_LOAD_INPUT,
        ST_LOAD_LN1,
        ST_LOAD_QKV_W,
        ST_LOAD_QKV_B,
        ST_LOAD_SM,
        ST_LOAD_OUT_W,
        ST_LOAD_OUT_B,
        ST_LOAD_LN2,
        ST_LOAD_FFNUP_W,
        ST_LOAD_FFNUP_B,
        ST_LOAD_FFNDOWN_W,
        ST_LOAD_FFNDOWN_B: begin
          if (io_ddr_rd_data_valid && (recv_count + 32'd1 == cur_len)) begin
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
              default: state <= ST_WEIGHT_INIT;
            endcase
            if (state == ST_LOAD_FFNDOWN_B) begin
              state <= ST_WEIGHT_INIT;
              max_qkv_addr <= 16'd0;
              max_out_addr <= 15'd0;
              max_ffnup_addr <= 17'd0;
              max_ffndown_addr <= 17'd0;
              weight_init_tail <= 32'd0;
            end
          end
        end
        ST_WEIGHT_INIT: begin
          if (core_qkv_w_addr > max_qkv_addr) max_qkv_addr <= core_qkv_w_addr;
          if (core_out_w_addr > max_out_addr) max_out_addr <= core_out_w_addr;
          if (core_ffnup_w_addr > max_ffnup_addr) max_ffnup_addr <= core_ffnup_w_addr;
          if (core_ffndown_w_addr > max_ffndown_addr) max_ffndown_addr <= core_ffndown_w_addr;
          if (max_qkv_addr == 16'd49151 &&
              max_out_addr == 15'd16895 &&
              max_ffnup_addr == 17'd66047 &&
              max_ffndown_addr == 17'd67583) begin
            weight_init_tail <= weight_init_tail + 32'd1;
            if (weight_init_tail == 32'd127) begin
              state <= ST_CORE_RESET;
              core_reset_cnt <= 8'd0;
            end
          end
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
          if (core_res_valid && core_res_last) begin
            $display(
              "NinePSystemTop token-done token=%0d cfg_seqlen=%0d run_last_token=%0d core_res_addr=%0d sys_res_addr=%0d",
              run_token_idx,
              io_cfg_seqlen,
              run_last_token,
              core_res_addr,
              (({16'd0, run_token_idx} << 6) + {{21{1'b0}}, core_res_addr})
            );
            if (run_last_token) begin
              state <= ST_DONE;
            end else begin
              run_token_idx <= run_token_idx + 16'd1;
              state <= ST_RUN_CFG;
            end
          end
        end
        ST_DONE: begin
        end
        default: begin
          state <= ST_IDLE;
        end
      endcase
    end
  end

endmodule
