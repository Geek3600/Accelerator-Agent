module cnn_core #(
  parameter integer CORE_EACH_SLR = 2,
  parameter [31:0] ADDR_OFFSET_H = 32'h00000008,
  parameter [31:0] ADDR_OFFSET_L = 32'h00000000,
  parameter integer C_DATA_WIDTH = 512,
  parameter integer CORE_NUM_SHARE_AXI = 2,
  parameter integer NUM_LAYERS = 12
)(
  input         clk_300M,
  input         clk_600M,
  input  [703:0] cfg_data,
  input         cfg_data_valid,
  input         cfg_done,
  input         cnn0_input_batch_set,
  output [2:0]  cnn0_batch_count,
  input         cnn0_result_batch_clear,
  output [2:0]  cnn0_result_count,
  input         user_rst,
  output reg [3:0]   c0_ddr4_s_axi_awid,
  output reg [36:0]  c0_ddr4_s_axi_awaddr,
  output reg [7:0]   c0_ddr4_s_axi_awlen,
  output reg [2:0]   c0_ddr4_s_axi_awsize,
  output reg [1:0]   c0_ddr4_s_axi_awburst,
  output reg         c0_ddr4_s_axi_awlock,
  output reg [3:0]   c0_ddr4_s_axi_awcache,
  output reg [2:0]   c0_ddr4_s_axi_awprot,
  output reg         c0_ddr4_s_axi_awvalid,
  input              c0_ddr4_s_axi_awready,
  output reg [511:0] c0_ddr4_s_axi_wdata,
  output reg [63:0]  c0_ddr4_s_axi_wstrb,
  output reg         c0_ddr4_s_axi_wlast,
  output reg         c0_ddr4_s_axi_wvalid,
  input              c0_ddr4_s_axi_wready,
  output reg         c0_ddr4_s_axi_bready,
  input      [3:0]   c0_ddr4_s_axi_bid,
  input      [1:0]   c0_ddr4_s_axi_bresp,
  input              c0_ddr4_s_axi_bvalid,
  output reg [3:0]   c0_ddr4_s_axi_arid,
  output reg [36:0]  c0_ddr4_s_axi_araddr,
  output reg [7:0]   c0_ddr4_s_axi_arlen,
  output reg [2:0]   c0_ddr4_s_axi_arsize,
  output reg [1:0]   c0_ddr4_s_axi_arburst,
  output reg         c0_ddr4_s_axi_arlock,
  output reg [3:0]   c0_ddr4_s_axi_arcache,
  output reg [2:0]   c0_ddr4_s_axi_arprot,
  output reg         c0_ddr4_s_axi_arvalid,
  input              c0_ddr4_s_axi_arready,
  output reg         c0_ddr4_s_axi_rready,
  input              c0_ddr4_s_axi_rlast,
  input              c0_ddr4_s_axi_rvalid,
  input      [1:0]   c0_ddr4_s_axi_rresp,
  input      [3:0]   c0_ddr4_s_axi_rid,
  input      [511:0] c0_ddr4_s_axi_rdata,
  input              c0_ddr4_s_axi_clk,
  input              c0_ddr4_s_axi_rst_n,
  input              c0_init_calib_complete,
  input              sys_rst_n
);

  localparam integer INPUT_BEATS_MAX = 1664;
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
  localparam integer TOKEN_BEATS = 64;
  localparam integer AXI_BEAT_BYTES = 64;
  localparam integer TOKEN_SLOT_COUNT = 4;
  localparam integer TOKEN_SLOT_BITS = 2;

  localparam [31:0] OFF_INPUT_BEATS     = 32'd0;
  localparam [31:0] OFF_LN1_W_BEATS     = 32'd58368;
  localparam [31:0] OFF_QKV_W_BEATS     = 32'd58496;
  localparam [31:0] OFF_QKV_B_BEATS     = 32'd107648;
  localparam [31:0] OFF_SM_BEATS        = 32'd107840;
  localparam [31:0] OFF_OUT_W_BEATS     = 32'd107866;
  localparam [31:0] OFF_OUT_B_BEATS     = 32'd124762;
  localparam [31:0] OFF_LN2_W_BEATS     = 32'd124826;
  localparam [31:0] OFF_FFNUP_W_BEATS   = 32'd124954;
  localparam [31:0] OFF_FFNUP_B_BEATS   = 32'd191002;
  localparam [31:0] OFF_FFNDOWN_W_BEATS = 32'd191258;
  localparam [31:0] OFF_FFNDOWN_B_BEATS = 32'd258842;

  localparam [4:0]
    ST_IDLE             = 5'd0,
    ST_LOAD_LN1         = 5'd1,
    ST_LOAD_QKV_W       = 5'd2,
    ST_LOAD_QKV_B       = 5'd3,
    ST_LOAD_SM          = 5'd4,
    ST_LOAD_OUT_W       = 5'd5,
    ST_LOAD_OUT_B       = 5'd6,
    ST_LOAD_LN2         = 5'd7,
    ST_LOAD_FFNUP_W     = 5'd8,
    ST_LOAD_FFNUP_B     = 5'd9,
    ST_LOAD_FFNDOWN_W   = 5'd10,
    ST_LOAD_FFNDOWN_B   = 5'd11,
    ST_CORE_RESET       = 5'd12,
    ST_STREAM_LN1       = 5'd13,
    ST_STREAM_LN2       = 5'd14,
    ST_STREAM_QKV_B     = 5'd15,
    ST_STREAM_OUT_B     = 5'd16,
    ST_STREAM_FFNUP_B   = 5'd17,
    ST_STREAM_FFNDOWN_B = 5'd18,
    ST_LOAD_TOKEN       = 5'd19,
    ST_RUN_CFG          = 5'd20,
    ST_PRELOAD_PULSE    = 5'd21,
    ST_PRELOAD_WAIT     = 5'd22,
    ST_RUN              = 5'd23,
    ST_WRITEBACK        = 5'd24,
    ST_DONE             = 5'd25,
    ST_KVHIST_PREP      = 5'd26,
    ST_KVHIST_WRITE     = 5'd27,
    ST_REPLAY_PREP      = 5'd28,
    ST_REPLAY_READ      = 5'd29,
    ST_REPLAY_STREAM    = 5'd30,
    ST_PIPE_SCHED       = 5'd31;

  localparam [1:0]
    HIST_IDLE          = 2'd0,
    HIST_WRITE         = 2'd1,
    HIST_REPLAY_READ   = 2'd2,
    HIST_REPLAY_STREAM = 2'd3;

  wire clock = c0_ddr4_s_axi_clk;
  wire reset = user_rst | ~sys_rst_n | ~c0_ddr4_s_axi_rst_n;

  reg [703:0] cfg_shadow;
  reg [703:0] cfg_active;
  reg         cfg_loaded;
  wire [31:0] cfg_words [0:21];
  genvar cfg_i;
  generate
    for (cfg_i = 0; cfg_i < 22; cfg_i = cfg_i + 1) begin : cfg_unpack
      assign cfg_words[cfg_i] = cfg_active[cfg_i * 32 +: 32];
    end
  endgenerate

  wire [63:0] axi_window_offset = {ADDR_OFFSET_H, ADDR_OFFSET_L};
  wire [15:0] cfg_seqlen_word = cfg_words[0][15:0];
  wire [31:0] output_stride_bytes = cfg_words[1];
  wire [63:0] window_rel_addr = {cfg_words[3], cfg_words[2]};
  wire [63:0] output_rel_addr = {cfg_words[5], cfg_words[4]};
  wire [63:0] window_base_addr = axi_window_offset + window_rel_addr;
  wire [63:0] output_base_addr = axi_window_offset + output_rel_addr;
  wire [7:0]  ln1_zero_point = cfg_words[6][7:0];
  wire [7:0]  dm2_ctx_zero_point = cfg_words[6][15:8];
  wire [7:0]  ln2_zero_point = cfg_words[6][23:16];

  wire [31:0] ln1_out_inv_scale = cfg_words[7];
  wire [31:0] q_out_inv_scale = cfg_words[8];
  wire [31:0] k_out_inv_scale = cfg_words[9];
  wire [31:0] v_out_inv_scale = cfg_words[10];
  wire [31:0] q_bias_scale = cfg_words[11];
  wire [31:0] k_bias_scale = cfg_words[12];
  wire [31:0] v_bias_scale = cfg_words[13];
  wire [31:0] dm1_out_scale = cfg_words[14];
  wire [31:0] dm2_ctx_inv_scale = cfg_words[15];
  wire [31:0] dm2_out_inv_scale = cfg_words[16];
  wire [31:0] out_out_scale = cfg_words[17];
  wire [31:0] ln2_out_inv_scale = cfg_words[18];
  wire [31:0] ffnup_out_inv_scale = cfg_words[19];
  wire [31:0] ffnup_bias_scale = cfg_words[20];
  wire [31:0] ffndown_out_scale = cfg_words[21];

  wire [63:0] input_base_addr     = window_base_addr + ({32'd0, OFF_INPUT_BEATS}     << 6);
  wire [63:0] ln1_w_base_addr     = window_base_addr + ({32'd0, OFF_LN1_W_BEATS}     << 6);
  wire [63:0] qkv_w_base_addr     = window_base_addr + ({32'd0, OFF_QKV_W_BEATS}     << 6);
  wire [63:0] qkv_b_base_addr     = window_base_addr + ({32'd0, OFF_QKV_B_BEATS}     << 6);
  wire [63:0] sm_base_addr        = window_base_addr + ({32'd0, OFF_SM_BEATS}        << 6);
  wire [63:0] out_w_base_addr     = window_base_addr + ({32'd0, OFF_OUT_W_BEATS}     << 6);
  wire [63:0] out_b_base_addr     = window_base_addr + ({32'd0, OFF_OUT_B_BEATS}     << 6);
  wire [63:0] ln2_w_base_addr     = window_base_addr + ({32'd0, OFF_LN2_W_BEATS}     << 6);
  wire [63:0] ffnup_w_base_addr   = window_base_addr + ({32'd0, OFF_FFNUP_W_BEATS}   << 6);
  wire [63:0] ffnup_b_base_addr   = window_base_addr + ({32'd0, OFF_FFNUP_B_BEATS}   << 6);
  wire [63:0] ffndown_w_base_addr = window_base_addr + ({32'd0, OFF_FFNDOWN_W_BEATS} << 6);
  wire [63:0] ffndown_b_base_addr = window_base_addr + ({32'd0, OFF_FFNDOWN_B_BEATS} << 6);

  reg [4:0] state;
  reg [31:0] issue_count;
  reg [31:0] recv_count;
  reg [7:0]  core_reset_cnt;
  reg [7:0]  preload_wait_cnt;
  reg        preload_full_wait;
  reg [31:0] stream_cnt;
  reg [15:0] run_token_idx;
  reg [TOKEN_SLOT_BITS-1:0] run_slot_idx;
  reg [15:0] load_token_idx;
  reg [15:0] exec_token_idx;
  reg [15:0] store_token_idx;
  reg [3:0]  layer_idx;
  reg        active_weight_bank;
  reg        active_act_bank;
  reg        weight_init_bank_sel;
  reg        token_last_pending;
  reg        token_res_started;
  reg [10:0] token_last_core_addr;
  reg [10:0] writeback_idx;
  reg        result_done;
  reg        rd_active;
  reg        rd_token_load_active;
  reg        rd_hist_active;
  reg        wr_hist_active;
  reg        wr_short_active;
  reg        load_active;
  reg        store_active;
  reg [31:0] load_issue_count;
  reg [31:0] load_recv_count;
  reg [6:0]  store_write_idx;
  reg [TOKEN_SLOT_BITS-1:0] load_slot_idx;
  reg [TOKEN_SLOT_BITS-1:0] store_slot_idx;

  reg [383:0] token_buf [0:TOKEN_SLOT_COUNT-1][0:TOKEN_BEATS-1];
  reg [383:0] token_out_buf [0:TOKEN_SLOT_COUNT-1][0:TOKEN_BEATS-1];
  reg [15:0] token_slot_id [0:TOKEN_SLOT_COUNT-1];
  reg [TOKEN_SLOT_COUNT-1:0] token_slot_valid;
  reg [TOKEN_SLOT_COUNT-1:0] token_slot_loaded;
  reg [TOKEN_SLOT_COUNT-1:0] token_slot_exec_done;
  reg [TOKEN_SLOT_COUNT-1:0] token_slot_store_done;
  reg [383:0] input_mem [0:INPUT_BEATS_MAX-1];
  reg [383:0] act_mem1 [0:INPUT_BEATS_MAX-1];

  reg [383:0] ln1_w_mem [0:LN_WEIGHT_BEATS-1];
  reg [383:0] ln2_w_mem [0:LN_WEIGHT_BEATS-1];
  reg [95:0]  qkv_b_mem [0:QKV_BIAS_BEATS-1];
  reg [25:0]  sm_w_mem [0:SM_BEATS-1];
  reg [383:0] out_b_mem [0:OUT_BIAS_BEATS-1];
  reg [95:0]  ffnup_b_mem [0:FFNUP_BIAS_BEATS-1];
  reg [383:0] ffndown_b_mem [0:FFNDOWN_BIAS_BEATS-1];

  reg [511:0] writeback_buf;
  reg [63:0]  cur_base_addr;
  reg [31:0]  cur_len;
  reg [15:0] q_tap_buf [0:11][0:31];
  reg [15:0] k_tap_buf [0:11][0:31];
  reg [15:0] v_tap_buf [0:11][0:31];
  reg [11:0] kv_tap_head_done;
  reg        replay_active;
  reg [3:0]  replay_head_idx;
  reg [15:0] replay_token_idx;
  reg [4:0]  replay_beat_idx;
  reg        replay_read_phase;
  reg        replay_done;
  reg        replay_v_send_pending;
  reg [511:0] replay_k_hist_line_buf;
  reg [511:0] replay_v_hist_line_buf;
  reg [3:0]  kv_hist_write_head_idx;
  reg        kv_hist_write_phase;
  reg [1:0]  hist_state;

  wire [63:0] src_act_base = active_act_bank ? output_base_addr : input_base_addr;
  wire [63:0] dst_act_base = active_act_bank ? input_base_addr : output_base_addr;

  wire rd_fire = rd_active && c0_ddr4_s_axi_rvalid && c0_ddr4_s_axi_rready;

  wire [31:0] input_beats = ({16'd0, cfg_seqlen_word} + 32'd1) << 6;
  wire [63:0] total_tokens_u64 = {48'd0, cfg_seqlen_word} + 64'd1;
  wire [63:0] total_output_beats_u64 = total_tokens_u64 << 6;
  wire [63:0] total_output_bytes_u64 = total_output_beats_u64 * {32'd0, output_stride_bytes};
  wire [63:0] kv_hist_token_bytes_u64 = 64'd768;
  wire [63:0] total_k_hist_bytes_u64 = total_tokens_u64 * kv_hist_token_bytes_u64;
  wire [63:0] k_hist_base_addr = output_base_addr + total_output_bytes_u64;
  wire [63:0] v_hist_base_addr = k_hist_base_addr + total_k_hist_bytes_u64;
  // 显式区分两种 runtime mode：
  // 1. short_seq_mode: 针对 <=26 的短序列场景
  // 2. long_seq_mode : 针对 912 场景的 token-history 路径
  // 当前已稳定验证的主路径仍是 long_seq_mode；保持 sample 工程接口不变。
  wire short_seq_mode = (cfg_seqlen_word <= 16'd25);
  wire long_seq_mode = ~short_seq_mode;
  wire [31:0] core_data_in_addr;
  wire run_last_token = (run_token_idx == cfg_seqlen_word);
  wire run_last_layer = (layer_idx == (NUM_LAYERS - 1));
  wire [31:0] core_data_in_addr_abs =
      short_seq_mode ? core_data_in_addr : (({16'd0, run_token_idx} << 6) + core_data_in_addr);
  wire [31:0] token_linear_idx = ({16'd0, run_token_idx} << 6);
  wire [63:0] token_src_base_addr = src_act_base + ({32'd0, token_linear_idx} * AXI_BEAT_BYTES);
  wire [TOKEN_SLOT_BITS-1:0] active_token_slot = run_slot_idx;
  wire [31:0] load_token_linear_idx = ({16'd0, load_token_idx} << 6);
  wire [63:0] load_token_src_base_addr = src_act_base + ({32'd0, load_token_linear_idx} * AXI_BEAT_BYTES);
  wire [63:0] load_issue_addr64 = load_token_src_base_addr + ({32'd0, load_issue_count} << 6);
  wire [63:0] store_write_base = (layer_idx == (NUM_LAYERS - 1)) ? output_base_addr : dst_act_base;
  wire [31:0] store_linear_idx = ({16'd0, store_token_idx} << 6) + {25'd0, store_write_idx[5:0]};
  wire [63:0] store_write_addr64 = store_write_base + ({32'd0, store_linear_idx} * output_stride_bytes);
  wire free_slot_found =
      !token_slot_valid[0] || !token_slot_valid[1] || !token_slot_valid[2] || !token_slot_valid[3];
  wire [TOKEN_SLOT_BITS-1:0] free_slot_idx =
      !token_slot_valid[0] ? 2'd0 :
      (!token_slot_valid[1] ? 2'd1 :
      (!token_slot_valid[2] ? 2'd2 : 2'd3));
  wire exec_slot_found =
      (token_slot_valid[0] && token_slot_loaded[0] && (token_slot_id[0] == exec_token_idx)) ||
      (token_slot_valid[1] && token_slot_loaded[1] && (token_slot_id[1] == exec_token_idx)) ||
      (token_slot_valid[2] && token_slot_loaded[2] && (token_slot_id[2] == exec_token_idx)) ||
      (token_slot_valid[3] && token_slot_loaded[3] && (token_slot_id[3] == exec_token_idx));
  wire [TOKEN_SLOT_BITS-1:0] exec_slot_idx =
      (token_slot_valid[0] && token_slot_loaded[0] && (token_slot_id[0] == exec_token_idx)) ? 2'd0 :
      ((token_slot_valid[1] && token_slot_loaded[1] && (token_slot_id[1] == exec_token_idx)) ? 2'd1 :
      ((token_slot_valid[2] && token_slot_loaded[2] && (token_slot_id[2] == exec_token_idx)) ? 2'd2 : 2'd3));
  wire store_slot_found =
      (token_slot_valid[0] && token_slot_exec_done[0] && (token_slot_id[0] == store_token_idx)) ||
      (token_slot_valid[1] && token_slot_exec_done[1] && (token_slot_id[1] == store_token_idx)) ||
      (token_slot_valid[2] && token_slot_exec_done[2] && (token_slot_id[2] == store_token_idx)) ||
      (token_slot_valid[3] && token_slot_exec_done[3] && (token_slot_id[3] == store_token_idx));
  wire [TOKEN_SLOT_BITS-1:0] store_slot_candidate =
      (token_slot_valid[0] && token_slot_exec_done[0] && (token_slot_id[0] == store_token_idx)) ? 2'd0 :
      ((token_slot_valid[1] && token_slot_exec_done[1] && (token_slot_id[1] == store_token_idx)) ? 2'd1 :
      ((token_slot_valid[2] && token_slot_exec_done[2] && (token_slot_id[2] == store_token_idx)) ? 2'd2 : 2'd3));
  wire exec_slot_ready = exec_slot_found;
  wire store_slot_ready = store_slot_found;
  wire runtime_state =
      state == ST_PIPE_SCHED || state == ST_RUN_CFG || state == ST_PRELOAD_PULSE ||
      state == ST_PRELOAD_WAIT || state == ST_RUN;

  wire is_load_state =
      state == ST_LOAD_LN1 || state == ST_LOAD_QKV_W || state == ST_LOAD_QKV_B ||
      state == ST_LOAD_SM || state == ST_LOAD_OUT_W || state == ST_LOAD_OUT_B ||
      state == ST_LOAD_LN2 || state == ST_LOAD_FFNUP_W || state == ST_LOAD_FFNUP_B ||
      state == ST_LOAD_FFNDOWN_W || state == ST_LOAD_FFNDOWN_B || state == ST_LOAD_TOKEN;

  wire core_layer_st = (state == ST_PRELOAD_PULSE);
  wire core_cfg_valid = (state == ST_RUN_CFG);
  wire [4:0] core_cfg_seqlen = short_seq_mode ? cfg_seqlen_word[4:0] : 5'd0;
  wire core_cfg_prefill = short_seq_mode ? 1'b1 : 1'b1;
  // Attention requests are token-scoped even in short-seq runtime, so keep
  // the attention-side cfg on the same per-token single-query contract used by
  // the board-validation tops.
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
  wire [47:0] core_attn_tap_data;
  wire core_attn_tap_st;
  wire [3:0] core_attn_tap_head;
  wire [31:0] core_attn_tap_addr;
  wire core_attn_tap_valid;
  wire core_attn_tap_last;
  wire core_attn_override_ready;
  wire core_attn_dm1_override_ready;
  wire core_attn_dm2_v_override_ready;
  wire replay_path_enable = long_seq_mode;
  wire replay_all_heads_done = &kv_tap_head_done;
  wire replay_use_local = (replay_token_idx == run_token_idx);
  wire [15:0] replay_q_beat = q_tap_buf[replay_head_idx][replay_beat_idx];
  wire [15:0] replay_k_beat = replay_use_local ? k_tap_buf[replay_head_idx][replay_beat_idx]
                                               : replay_k_hist_line_buf[replay_beat_idx * 16 +: 16];
  wire [15:0] replay_v_beat = replay_use_local ? v_tap_buf[replay_head_idx][replay_beat_idx]
                                               : replay_v_hist_line_buf[replay_beat_idx * 16 +: 16];
  wire [511:0] replay_v_line = replay_use_local ? pack_v_tap_line(replay_head_idx)
                                                 : replay_v_hist_line_buf;
  wire hist_busy = (hist_state != HIST_IDLE);
  wire replay_read_state = (hist_state == HIST_REPLAY_READ);
  wire axi_read_busy = c0_ddr4_s_axi_arvalid || rd_active || c0_ddr4_s_axi_rready;
  wire axi_write_busy = c0_ddr4_s_axi_awvalid || c0_ddr4_s_axi_wvalid || c0_ddr4_s_axi_bready;
  wire [63:0] replay_k_line_addr = k_hist_base_addr + ((({48'd0, replay_token_idx} * 64'd12) + {60'd0, replay_head_idx}) << 6);
  wire [63:0] replay_v_line_addr = v_hist_base_addr + ((({48'd0, replay_token_idx} * 64'd12) + {60'd0, replay_head_idx}) << 6);
  // Stop using the coarse whole-Attention override path. Long-sequence history
  // now moves toward the finer DM1 / DM2.v history-source interfaces.
  wire core_attn_override_enable = 1'b0;
  wire [47:0] core_attn_override_data = 48'd0;
  wire core_attn_override_st = 1'b0;
  wire [31:0] core_attn_override_addr = 32'd0;
  wire core_attn_override_valid = 1'b0;
  wire core_attn_override_last = 1'b0;
  wire core_attn_dm1_override_enable = long_seq_mode && replay_active;
  wire [31:0] core_attn_dm1_override_data = {replay_k_beat, replay_q_beat};
  wire core_attn_dm1_override_st = long_seq_mode && replay_active && (replay_beat_idx == 5'd0);
  wire [9:0] core_attn_dm1_override_addr = {5'd0, replay_beat_idx};
  wire core_attn_dm1_override_valid = long_seq_mode && replay_active;
  wire core_attn_dm1_override_last = long_seq_mode && replay_active && (replay_beat_idx == 5'd31);
  wire core_attn_dm2_v_override_enable = long_seq_mode && replay_v_send_pending;
  wire [511:0] core_attn_dm2_v_override_data = replay_v_line;
  wire core_attn_dm2_v_override_st = long_seq_mode && replay_v_send_pending;
  wire [4:0] core_attn_dm2_v_override_addr = 5'd0;
  wire core_attn_dm2_v_override_valid = long_seq_mode && replay_v_send_pending;
  wire core_attn_dm2_v_override_last = long_seq_mode && replay_v_send_pending;
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

  wire [383:0] core_data_in =
      short_seq_mode
          ? ((core_data_in_addr_abs < INPUT_BEATS_MAX)
                 ? (active_act_bank ? act_mem1[core_data_in_addr_abs] : input_mem[core_data_in_addr_abs])
                 : 384'd0)
          : token_buf[active_token_slot][core_data_in_addr[5:0]];
  wire [383:0] core_ln1_w_in = ln1_w_mem[stream_cnt[6:0]];
  wire [383:0] core_ln2_w_in = ln2_w_mem[stream_cnt[6:0]];
  wire [95:0]  core_qkv_b_in = qkv_b_mem[stream_cnt[7:0]];
  wire [SOFTMAX_SEQ_LEN-1:0] core_sm_w_in =
      long_seq_mode
          ? make_softmax_prefix_mask(run_token_idx)
          : ((core_sm_w_addr < SM_BEATS)
                 ? {{(SOFTMAX_SEQ_LEN-26){1'b0}}, sm_w_mem[core_sm_w_addr[4:0]]}
                 : {SOFTMAX_SEQ_LEN{1'b0}});
  wire [287:0] core_qkv_w_in = 288'd0;
  wire [287:0] core_out_w_in = 288'd0;
  wire [383:0] core_out_b_in = out_b_mem[stream_cnt[5:0]];
  wire [287:0] core_ffnup_w_in = 288'd0;
  wire [95:0]  core_ffnup_b_in = ffnup_b_mem[stream_cnt[7:0]];
  wire [287:0] core_ffndown_w_in = 288'd0;
  wire [383:0] core_ffndown_b_in = ffndown_b_mem[stream_cnt[5:0]];

  wire core_qkv_w_preload_valid = (state == ST_LOAD_QKV_W) && rd_fire;
  wire [15:0] core_qkv_w_preload_addr = recv_count[15:0];
  wire [287:0] core_qkv_w_preload_data = c0_ddr4_s_axi_rdata[287:0];
  wire core_out_w_preload_valid = (state == ST_LOAD_OUT_W) && rd_fire;
  wire [14:0] core_out_w_preload_addr = recv_count[14:0];
  wire [287:0] core_out_w_preload_data = c0_ddr4_s_axi_rdata[287:0];
  wire core_ffnup_w_preload_valid = (state == ST_LOAD_FFNUP_W) && rd_fire;
  wire [16:0] core_ffnup_w_preload_addr = recv_count[16:0];
  wire [287:0] core_ffnup_w_preload_data = c0_ddr4_s_axi_rdata[287:0];
  wire core_ffndown_w_preload_valid = (state == ST_LOAD_FFNDOWN_W) && rd_fire;
  wire [16:0] core_ffndown_w_preload_addr = recv_count[16:0];
  wire [287:0] core_ffndown_w_preload_data = c0_ddr4_s_axi_rdata[287:0];

  wire [63:0] issue_addr64 = cur_base_addr + ({32'd0, issue_count} << 6);
  wire [31:0] writeback_linear_idx = ({16'd0, run_token_idx} << 6) + {25'd0, writeback_idx[5:0]};
  wire [63:0] writeback_addr64 = store_write_addr64;
  wire short_write_state = short_seq_mode && (state == ST_WRITEBACK);
  wire [63:0] short_writeback_addr64 = output_base_addr + ({32'd0, writeback_idx} * output_stride_bytes);
  wire [383:0] short_writeback_data =
      active_act_bank ? input_mem[writeback_idx] : act_mem1[writeback_idx];
  wire [7:0] preload_wait_target = preload_full_wait ? 8'd63 : 8'd3;

  function automatic [511:0] pack_q_tap_line;
    input [3:0] head_sel;
    integer i;
    begin
      pack_q_tap_line = 512'd0;
      for (i = 0; i < 32; i = i + 1)
        pack_q_tap_line[i*16 +: 16] = q_tap_buf[head_sel][i];
    end
  endfunction

  function automatic [511:0] pack_k_tap_line;
    input [3:0] head_sel;
    integer i;
    begin
      pack_k_tap_line = 512'd0;
      for (i = 0; i < 32; i = i + 1)
        pack_k_tap_line[i*16 +: 16] = k_tap_buf[head_sel][i];
    end
  endfunction

  function automatic [511:0] pack_v_tap_line;
    input [3:0] head_sel;
    integer i;
    begin
      pack_v_tap_line = 512'd0;
      for (i = 0; i < 32; i = i + 1)
        pack_v_tap_line[i*16 +: 16] = v_tap_buf[head_sel][i];
    end
  endfunction

  wire [63:0] kv_hist_write_addr =
      kv_hist_write_phase
          ? (v_hist_base_addr + ((({48'd0, run_token_idx} * 64'd12) + {60'd0, kv_hist_write_head_idx}) << 6))
          : (k_hist_base_addr + ((({48'd0, run_token_idx} * 64'd12) + {60'd0, kv_hist_write_head_idx}) << 6));
  wire [511:0] kv_hist_write_data =
      kv_hist_write_phase ? pack_v_tap_line(kv_hist_write_head_idx) : pack_k_tap_line(kv_hist_write_head_idx);
  wire hist_write_state = (hist_state == HIST_WRITE);
  wire write_state = store_active || hist_write_state || short_write_state;
  wire [63:0] write_issue_addr64 =
      hist_write_state ? kv_hist_write_addr : (short_write_state ? short_writeback_addr64 : writeback_addr64);
  wire [63:0] replay_read_addr64 = replay_read_phase ? replay_v_line_addr : replay_k_line_addr;

  assign core_res_ready = (state == ST_RUN);
  assign cnn0_batch_count = {2'd0, (state != ST_IDLE)};
  assign cnn0_result_count = {2'd0, result_done};

  function automatic [SOFTMAX_SEQ_LEN-1:0] make_softmax_prefix_mask;
    input [15:0] upto_token;
    integer i;
    begin
      make_softmax_prefix_mask = {SOFTMAX_SEQ_LEN{1'b0}};
      for (i = 0; i < SOFTMAX_SEQ_LEN; i = i + 1) begin
        if (i <= upto_token)
          make_softmax_prefix_mask[i] = 1'b1;
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
    .io_weight_init_mode(1'b0),
    .io_weight_active_bank(active_weight_bank),
    .io_weight_preload_bank(weight_init_bank_sel),
    .io_data_in(core_data_in),
    .io_data_in_ready((state == ST_RUN)),
    .io_data_in_addr(core_data_in_addr),
    .io_attn_tap_data(core_attn_tap_data),
    .io_attn_tap_st(core_attn_tap_st),
    .io_attn_tap_head(core_attn_tap_head),
    .io_attn_tap_addr(core_attn_tap_addr),
    .io_attn_tap_valid(core_attn_tap_valid),
    .io_attn_tap_last(core_attn_tap_last),
    .io_attn_override_enable(core_attn_override_enable),
    .io_attn_override_data(core_attn_override_data),
    .io_attn_override_st(core_attn_override_st),
    .io_attn_override_addr(core_attn_override_addr),
    .io_attn_override_valid(core_attn_override_valid),
    .io_attn_override_last(core_attn_override_last),
    .io_attn_override_ready(core_attn_override_ready),
    .io_attn_dm1_override_enable(core_attn_dm1_override_enable),
    .io_attn_dm1_override_data(core_attn_dm1_override_data),
    .io_attn_dm1_override_st(core_attn_dm1_override_st),
    .io_attn_dm1_override_addr(core_attn_dm1_override_addr),
    .io_attn_dm1_override_valid(core_attn_dm1_override_valid),
    .io_attn_dm1_override_last(core_attn_dm1_override_last),
    .io_attn_dm1_override_ready(core_attn_dm1_override_ready),
    .io_attn_dm2_v_override_enable(core_attn_dm2_v_override_enable),
    .io_attn_dm2_v_override_data(core_attn_dm2_v_override_data),
    .io_attn_dm2_v_override_st(core_attn_dm2_v_override_st),
    .io_attn_dm2_v_override_addr(core_attn_dm2_v_override_addr),
    .io_attn_dm2_v_override_valid(core_attn_dm2_v_override_valid),
    .io_attn_dm2_v_override_last(core_attn_dm2_v_override_last),
    .io_attn_dm2_v_override_ready(core_attn_dm2_v_override_ready),
    .io_ln_w_in(core_ln1_w_in),
    .io_ln_w_valid(core_ln_w_valid),
    .io_ln1_out_inv_scale(ln1_out_inv_scale),
    .io_ln1_out_zero_point(ln1_zero_point),
    .io_q_out_inv_scale(q_out_inv_scale),
    .io_k_out_inv_scale(k_out_inv_scale),
    .io_v_out_inv_scale(v_out_inv_scale),
    .io_q_bias_scale(q_bias_scale),
    .io_k_bias_scale(k_bias_scale),
    .io_v_bias_scale(v_bias_scale),
    .io_dm1_out_scale(dm1_out_scale),
    .io_dm2_ctx_inv_scale(dm2_ctx_inv_scale),
    .io_dm2_ctx_zero_point(dm2_ctx_zero_point),
    .io_dm2_out_inv_scale(dm2_out_inv_scale),
    .io_out_out_scale(out_out_scale),
    .io_ln2_out_inv_scale(ln2_out_inv_scale),
    .io_ln2_out_zero_point(ln2_zero_point),
    .io_ffnup_out_inv_scale(ffnup_out_inv_scale),
    .io_ffnup_bias_scale(ffnup_bias_scale),
    .io_ffndown_out_scale(ffndown_out_scale),
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

  always @(*) begin
    case (state)
      ST_LOAD_TOKEN:      begin
                            cur_base_addr = short_seq_mode ? input_base_addr : token_src_base_addr;
                            cur_len = short_seq_mode ? input_beats : TOKEN_BEATS;
                          end
      ST_LOAD_LN1:        begin cur_base_addr = ln1_w_base_addr;     cur_len = LN_WEIGHT_BEATS; end
      ST_LOAD_QKV_W:      begin cur_base_addr = qkv_w_base_addr;     cur_len = QKV_WEIGHT_BEATS; end
      ST_LOAD_QKV_B:      begin cur_base_addr = qkv_b_base_addr;     cur_len = QKV_BIAS_BEATS; end
      ST_LOAD_SM:         begin cur_base_addr = sm_base_addr;        cur_len = SM_BEATS; end
      ST_LOAD_OUT_W:      begin cur_base_addr = out_w_base_addr;     cur_len = OUT_WEIGHT_BEATS; end
      ST_LOAD_OUT_B:      begin cur_base_addr = out_b_base_addr;     cur_len = OUT_BIAS_BEATS; end
      ST_LOAD_LN2:        begin cur_base_addr = ln2_w_base_addr;     cur_len = LN_WEIGHT_BEATS; end
      ST_LOAD_FFNUP_W:    begin cur_base_addr = ffnup_w_base_addr;   cur_len = FFNUP_WEIGHT_BEATS; end
      ST_LOAD_FFNUP_B:    begin cur_base_addr = ffnup_b_base_addr;   cur_len = FFNUP_BIAS_BEATS; end
      ST_LOAD_FFNDOWN_W:  begin cur_base_addr = ffndown_w_base_addr; cur_len = FFNDOWN_WEIGHT_BEATS; end
      ST_LOAD_FFNDOWN_B:  begin cur_base_addr = ffndown_b_base_addr; cur_len = FFNDOWN_BIAS_BEATS; end
      default:            begin cur_base_addr = 64'd0;               cur_len = 32'd0; end
    endcase
  end

  always @(posedge clock) begin
    if (reset) begin
      state <= ST_IDLE;
      issue_count <= 32'd0;
      recv_count <= 32'd0;
      core_reset_cnt <= 8'd0;
      preload_wait_cnt <= 8'd0;
      stream_cnt <= 32'd0;
      run_token_idx <= 16'd0;
      run_slot_idx <= {TOKEN_SLOT_BITS{1'b0}};
      load_token_idx <= 16'd0;
      exec_token_idx <= 16'd0;
      store_token_idx <= 16'd0;
      layer_idx <= 4'd0;
      preload_full_wait <= 1'b1;
      active_weight_bank <= 1'b0;
      active_act_bank <= 1'b0;
      weight_init_bank_sel <= 1'b0;
      token_last_pending <= 1'b0;
      token_res_started <= 1'b0;
      token_last_core_addr <= 11'd0;
      writeback_idx <= 11'd0;
      cfg_shadow <= 704'd0;
      cfg_active <= 704'd0;
      cfg_loaded <= 1'b0;
      result_done <= 1'b0;
      rd_active <= 1'b0;
      rd_token_load_active <= 1'b0;
      rd_hist_active <= 1'b0;
      wr_hist_active <= 1'b0;
      wr_short_active <= 1'b0;
      load_active <= 1'b0;
      store_active <= 1'b0;
      load_issue_count <= 32'd0;
      load_recv_count <= 32'd0;
      store_write_idx <= 7'd0;
      load_slot_idx <= {TOKEN_SLOT_BITS{1'b0}};
      store_slot_idx <= {TOKEN_SLOT_BITS{1'b0}};
      token_slot_valid <= {TOKEN_SLOT_COUNT{1'b0}};
      token_slot_loaded <= {TOKEN_SLOT_COUNT{1'b0}};
      token_slot_exec_done <= {TOKEN_SLOT_COUNT{1'b0}};
      token_slot_store_done <= {TOKEN_SLOT_COUNT{1'b0}};
      kv_tap_head_done <= 12'd0;
      replay_active <= 1'b0;
      replay_head_idx <= 4'd0;
      replay_token_idx <= 16'd0;
      replay_beat_idx <= 5'd0;
      replay_read_phase <= 1'b0;
      replay_done <= 1'b0;
      replay_v_send_pending <= 1'b0;
      replay_k_hist_line_buf <= 512'd0;
      replay_v_hist_line_buf <= 512'd0;
      kv_hist_write_head_idx <= 4'd0;
      kv_hist_write_phase <= 1'b0;
      hist_state <= HIST_IDLE;

      c0_ddr4_s_axi_awid <= 4'd0;
      c0_ddr4_s_axi_awaddr <= 37'd0;
      c0_ddr4_s_axi_awlen <= 8'd0;
      c0_ddr4_s_axi_awsize <= 3'd6;
      c0_ddr4_s_axi_awburst <= 2'b01;
      c0_ddr4_s_axi_awlock <= 1'b0;
      c0_ddr4_s_axi_awcache <= 4'd0;
      c0_ddr4_s_axi_awprot <= 3'd0;
      c0_ddr4_s_axi_awvalid <= 1'b0;

      c0_ddr4_s_axi_wdata <= 512'd0;
      c0_ddr4_s_axi_wstrb <= 64'd0;
      c0_ddr4_s_axi_wlast <= 1'b0;
      c0_ddr4_s_axi_wvalid <= 1'b0;
      c0_ddr4_s_axi_bready <= 1'b0;

      c0_ddr4_s_axi_arid <= 4'd0;
      c0_ddr4_s_axi_araddr <= 37'd0;
      c0_ddr4_s_axi_arlen <= 8'd0;
      c0_ddr4_s_axi_arsize <= 3'd6;
      c0_ddr4_s_axi_arburst <= 2'b01;
      c0_ddr4_s_axi_arlock <= 1'b0;
      c0_ddr4_s_axi_arcache <= 4'd0;
      c0_ddr4_s_axi_arprot <= 3'd0;
      c0_ddr4_s_axi_arvalid <= 1'b0;
      c0_ddr4_s_axi_rready <= 1'b0;
    end else begin
      if (cfg_data_valid)
        cfg_shadow <= cfg_data;
      if (cfg_done) begin
        cfg_active <= cfg_data_valid ? cfg_data : cfg_shadow;
        cfg_loaded <= 1'b1;
      end

      if (state == ST_RUN && core_attn_tap_valid) begin
        q_tap_buf[core_attn_tap_head][core_attn_tap_addr[4:0]] <= core_attn_tap_data[15:0];
        k_tap_buf[core_attn_tap_head][core_attn_tap_addr[4:0]] <= core_attn_tap_data[31:16];
        v_tap_buf[core_attn_tap_head][core_attn_tap_addr[4:0]] <= core_attn_tap_data[47:32];
        if (core_attn_tap_last)
          kv_tap_head_done[core_attn_tap_head] <= 1'b1;
      end

      if (replay_active && core_attn_dm1_override_ready) begin
        if (replay_beat_idx == 5'd31) begin
          replay_beat_idx <= 5'd0;
          replay_active <= 1'b0;
        end else begin
          replay_beat_idx <= replay_beat_idx + 5'd1;
        end
      end

      if (replay_v_send_pending && core_attn_dm2_v_override_ready) begin
        replay_v_send_pending <= 1'b0;
      end

      if (state == ST_DONE && cnn0_result_batch_clear) begin
        result_done <= 1'b0;
        state <= ST_IDLE;
      end

      if (long_seq_mode && runtime_state && !load_active && (load_token_idx <= cfg_seqlen_word) &&
          free_slot_found) begin
        load_active <= 1'b1;
        load_issue_count <= 32'd0;
        load_recv_count <= 32'd0;
        load_slot_idx <= free_slot_idx;
      end

      if (long_seq_mode && runtime_state && !store_active && (store_token_idx <= cfg_seqlen_word) && store_slot_ready) begin
        store_active <= 1'b1;
        store_write_idx <= 7'd0;
        store_slot_idx <= store_token_idx[TOKEN_SLOT_BITS-1:0];
      end

      if (!c0_ddr4_s_axi_arvalid && !rd_active && c0_init_calib_complete &&
          ((is_load_state && (issue_count < cur_len)) || replay_read_state ||
           (load_active && (load_issue_count < TOKEN_BEATS)))) begin
        c0_ddr4_s_axi_arid <= 4'd0;
        if (replay_read_state)
          c0_ddr4_s_axi_araddr <= replay_read_addr64[36:0];
        else if (is_load_state)
          c0_ddr4_s_axi_araddr <= issue_addr64[36:0];
        else
          c0_ddr4_s_axi_araddr <= load_issue_addr64[36:0];
        c0_ddr4_s_axi_arlen <= 8'd0;
        c0_ddr4_s_axi_arsize <= 3'd6;
        c0_ddr4_s_axi_arburst <= 2'b01;
        c0_ddr4_s_axi_arlock <= 1'b0;
        c0_ddr4_s_axi_arcache <= 4'd0;
        c0_ddr4_s_axi_arprot <= 3'd0;
        c0_ddr4_s_axi_arvalid <= 1'b1;
      end

      if (c0_ddr4_s_axi_arvalid && c0_ddr4_s_axi_arready) begin
        c0_ddr4_s_axi_arvalid <= 1'b0;
        c0_ddr4_s_axi_rready <= 1'b1;
        rd_active <= 1'b1;
        rd_token_load_active <= !is_load_state && !replay_read_state;
        rd_hist_active <= replay_read_state;
        if (is_load_state)
          issue_count <= issue_count + 32'd1;
        else if (!replay_read_state)
          load_issue_count <= load_issue_count + 32'd1;
      end

      if (rd_fire) begin
        rd_active <= 1'b0;
        c0_ddr4_s_axi_rready <= 1'b0;
        rd_token_load_active <= 1'b0;
        rd_hist_active <= 1'b0;
        if (rd_token_load_active) begin
          token_buf[load_slot_idx][load_recv_count[5:0]] <= c0_ddr4_s_axi_rdata[383:0];
          token_slot_id[load_slot_idx] <= load_token_idx;
          token_slot_valid[load_slot_idx] <= 1'b1;
          token_slot_exec_done[load_slot_idx] <= 1'b0;
          token_slot_store_done[load_slot_idx] <= 1'b0;
          if (load_recv_count == (TOKEN_BEATS - 1)) begin
            token_slot_loaded[load_slot_idx] <= 1'b1;
            load_active <= 1'b0;
            load_recv_count <= 32'd0;
            load_issue_count <= 32'd0;
            load_token_idx <= load_token_idx + 16'd1;
          end else begin
            load_recv_count <= load_recv_count + 32'd1;
          end
        end else if (rd_hist_active) begin
          if (replay_read_phase)
            replay_v_hist_line_buf <= c0_ddr4_s_axi_rdata;
          else
            replay_k_hist_line_buf <= c0_ddr4_s_axi_rdata;
        end else begin
          case (state)
            ST_LOAD_TOKEN:      if (short_seq_mode && recv_count < INPUT_BEATS_MAX) input_mem[recv_count] <= c0_ddr4_s_axi_rdata[383:0];
            ST_LOAD_LN1:        ln1_w_mem[recv_count[6:0]] <= c0_ddr4_s_axi_rdata[383:0];
            ST_LOAD_QKV_B:      qkv_b_mem[recv_count[7:0]] <= c0_ddr4_s_axi_rdata[95:0];
            ST_LOAD_SM:         sm_w_mem[recv_count[4:0]] <= c0_ddr4_s_axi_rdata[25:0];
            ST_LOAD_OUT_B:      out_b_mem[recv_count[5:0]] <= c0_ddr4_s_axi_rdata[383:0];
            ST_LOAD_LN2:        ln2_w_mem[recv_count[6:0]] <= c0_ddr4_s_axi_rdata[383:0];
            ST_LOAD_FFNUP_B:    ffnup_b_mem[recv_count[7:0]] <= c0_ddr4_s_axi_rdata[95:0];
            ST_LOAD_FFNDOWN_B:  ffndown_b_mem[recv_count[5:0]] <= c0_ddr4_s_axi_rdata[383:0];
            default: begin end
          endcase
        end

        if (!rd_token_load_active && rd_hist_active) begin
          if (replay_read_phase) begin
            replay_read_phase <= 1'b0;
            replay_v_send_pending <= 1'b1;
            replay_active <= 1'b1;
            replay_beat_idx <= 5'd0;
            hist_state <= HIST_REPLAY_STREAM;
          end else begin
            replay_read_phase <= 1'b1;
          end
        end else if (!rd_token_load_active && (recv_count + 32'd1 == cur_len)) begin
          issue_count <= 32'd0;
          recv_count <= 32'd0;
          case (state)
            ST_LOAD_TOKEN:      begin if (short_seq_mode) state <= ST_LOAD_LN1; end
            ST_LOAD_LN1:        begin state <= ST_LOAD_QKV_W;     weight_init_bank_sel <= 1'b0; end
            ST_LOAD_QKV_W:      begin
                                 if (!weight_init_bank_sel) begin
                                   weight_init_bank_sel <= 1'b1;
                                   state <= ST_LOAD_QKV_W;
                                 end else begin
                                   weight_init_bank_sel <= 1'b0;
                                   state <= ST_LOAD_QKV_B;
                                 end
                               end
            ST_LOAD_QKV_B:      state <= ST_LOAD_SM;
            ST_LOAD_SM:         state <= ST_LOAD_OUT_W;
            ST_LOAD_OUT_W:      begin
                                 if (!weight_init_bank_sel) begin
                                   weight_init_bank_sel <= 1'b1;
                                   state <= ST_LOAD_OUT_W;
                                 end else begin
                                   weight_init_bank_sel <= 1'b0;
                                   state <= ST_LOAD_OUT_B;
                                 end
                               end
            ST_LOAD_OUT_B:      state <= ST_LOAD_LN2;
            ST_LOAD_LN2:        state <= ST_LOAD_FFNUP_W;
            ST_LOAD_FFNUP_W:    begin
                                 if (!weight_init_bank_sel) begin
                                   weight_init_bank_sel <= 1'b1;
                                   state <= ST_LOAD_FFNUP_W;
                                 end else begin
                                   weight_init_bank_sel <= 1'b0;
                                   state <= ST_LOAD_FFNUP_B;
                                 end
                               end
            ST_LOAD_FFNUP_B:    state <= ST_LOAD_FFNDOWN_W;
            ST_LOAD_FFNDOWN_W:  begin
                                 if (!weight_init_bank_sel) begin
                                   weight_init_bank_sel <= 1'b1;
                                   state <= ST_LOAD_FFNDOWN_W;
                                 end else begin
                                   weight_init_bank_sel <= 1'b0;
                                   state <= ST_LOAD_FFNDOWN_B;
                                 end
                               end
            ST_LOAD_FFNDOWN_B:  begin state <= ST_STREAM_LN1; stream_cnt <= 32'd0; end
            default: begin end
          endcase
        end else if (!rd_token_load_active) begin
          recv_count <= recv_count + 32'd1;
        end
      end

      if (!c0_ddr4_s_axi_awvalid && !c0_ddr4_s_axi_wvalid && !c0_ddr4_s_axi_bready &&
          write_state &&
          ((store_active && store_write_idx < 7'd64) || hist_write_state || short_write_state) &&
          c0_init_calib_complete) begin
        c0_ddr4_s_axi_awid <= 4'd0;
        c0_ddr4_s_axi_awaddr <= write_issue_addr64[36:0];
        c0_ddr4_s_axi_awlen <= 8'd0;
        c0_ddr4_s_axi_awsize <= 3'd6;
        c0_ddr4_s_axi_awburst <= 2'b01;
        c0_ddr4_s_axi_awlock <= 1'b0;
        c0_ddr4_s_axi_awcache <= 4'd0;
        c0_ddr4_s_axi_awprot <= 3'd0;
        c0_ddr4_s_axi_awvalid <= 1'b1;
        wr_hist_active <= hist_write_state;
        wr_short_active <= short_write_state;
        if (hist_write_state)
          writeback_buf <= kv_hist_write_data;
        else if (short_write_state)
          writeback_buf <= {128'd0, short_writeback_data};
        else if (store_active)
          writeback_buf <= {128'd0, token_out_buf[store_slot_idx][store_write_idx[5:0]]};
      end

      if (c0_ddr4_s_axi_awvalid && c0_ddr4_s_axi_awready) begin
        c0_ddr4_s_axi_awvalid <= 1'b0;
        c0_ddr4_s_axi_wdata <= writeback_buf;
        // Use the latched write kind from the AW issue point so W does not
        // depend on a later combinational history-state transition.
        c0_ddr4_s_axi_wstrb <= wr_hist_active ? 64'hFFFFFFFFFFFFFFFF : 64'h0000FFFFFFFFFFFF;
        c0_ddr4_s_axi_wlast <= 1'b1;
        c0_ddr4_s_axi_wvalid <= 1'b1;
      end

      if (c0_ddr4_s_axi_wvalid && c0_ddr4_s_axi_wready) begin
        c0_ddr4_s_axi_wvalid <= 1'b0;
        c0_ddr4_s_axi_wlast <= 1'b0;
        c0_ddr4_s_axi_bready <= 1'b1;
      end

      if (c0_ddr4_s_axi_bvalid && c0_ddr4_s_axi_bready) begin
        c0_ddr4_s_axi_bready <= 1'b0;
        if (wr_hist_active) begin
            if (kv_hist_write_phase) begin
              kv_hist_write_phase <= 1'b0;
              if (kv_hist_write_head_idx == 4'd11) begin
                replay_token_idx <= 16'd0;
                replay_head_idx <= 4'd0;
                replay_beat_idx <= 5'd0;
                replay_v_send_pending <= 1'b0;
                if (run_token_idx == 16'd0) begin
                  replay_v_send_pending <= 1'b1;
                  replay_active <= 1'b1;
                  hist_state <= HIST_REPLAY_STREAM;
                end else begin
                  replay_read_phase <= 1'b0;
                  hist_state <= HIST_REPLAY_READ;
                end
              end else begin
                kv_hist_write_head_idx <= kv_hist_write_head_idx + 4'd1;
              end
            end else begin
              kv_hist_write_phase <= 1'b1;
          end
        end else if (wr_short_active) begin
          if ({21'd0, writeback_idx} + 32'd1 == input_beats) begin
            writeback_idx <= 11'd0;
            state <= ST_DONE;
            result_done <= 1'b1;
          end else begin
            writeback_idx <= writeback_idx + 11'd1;
          end
        end else begin
          if (store_write_idx == 7'd63) begin
            token_slot_store_done[store_slot_idx] <= 1'b1;
            token_slot_valid[store_slot_idx] <= 1'b0;
            token_slot_loaded[store_slot_idx] <= 1'b0;
            token_slot_exec_done[store_slot_idx] <= 1'b0;
            store_active <= 1'b0;
            store_write_idx <= 7'd0;
            store_token_idx <= store_token_idx + 16'd1;
          end else begin
            store_write_idx <= store_write_idx + 7'd1;
          end
        end
        wr_hist_active <= 1'b0;
        wr_short_active <= 1'b0;
      end

      if (state == ST_RUN && core_res_valid && core_res_ready) begin
        if (core_res_st)
          token_res_started <= 1'b1;
        if (short_seq_mode) begin
          if (active_act_bank)
            input_mem[core_res_addr] <= core_res;
          else
            act_mem1[core_res_addr] <= core_res;
        end else begin
          token_out_buf[active_token_slot][core_res_addr[5:0]] <= core_res;
        end
        if (core_res_last && (token_res_started || core_res_st)) begin
          token_last_pending <= 1'b1;
          token_last_core_addr <= core_res_addr;
          if (!short_seq_mode)
            token_slot_exec_done[active_token_slot] <= 1'b1;
        end
      end

      case (state)
        ST_IDLE: begin
          issue_count <= 32'd0;
          recv_count <= 32'd0;
          run_token_idx <= 16'd0;
          run_slot_idx <= {TOKEN_SLOT_BITS{1'b0}};
          load_token_idx <= 16'd0;
          exec_token_idx <= 16'd0;
          store_token_idx <= 16'd0;
          layer_idx <= 4'd0;
          preload_full_wait <= 1'b1;
          active_weight_bank <= 1'b0;
          active_act_bank <= 1'b0;
          weight_init_bank_sel <= 1'b0;
          token_slot_valid <= {TOKEN_SLOT_COUNT{1'b0}};
          token_slot_loaded <= {TOKEN_SLOT_COUNT{1'b0}};
          token_slot_exec_done <= {TOKEN_SLOT_COUNT{1'b0}};
          token_slot_store_done <= {TOKEN_SLOT_COUNT{1'b0}};
          token_last_pending <= 1'b0;
          token_res_started <= 1'b0;
          writeback_idx <= 11'd0;
          rd_token_load_active <= 1'b0;
          rd_hist_active <= 1'b0;
          wr_hist_active <= 1'b0;
          wr_short_active <= 1'b0;
          load_active <= 1'b0;
          store_active <= 1'b0;
          load_issue_count <= 32'd0;
          load_recv_count <= 32'd0;
          store_write_idx <= 7'd0;
          load_slot_idx <= {TOKEN_SLOT_BITS{1'b0}};
          store_slot_idx <= {TOKEN_SLOT_BITS{1'b0}};
          kv_tap_head_done <= 12'd0;
          replay_active <= 1'b0;
          replay_head_idx <= 4'd0;
          replay_token_idx <= 16'd0;
          replay_beat_idx <= 5'd0;
          replay_read_phase <= 1'b0;
          replay_done <= 1'b0;
          replay_v_send_pending <= 1'b0;
          replay_k_hist_line_buf <= 512'd0;
          replay_v_hist_line_buf <= 512'd0;
          kv_hist_write_head_idx <= 4'd0;
          kv_hist_write_phase <= 1'b0;
          hist_state <= HIST_IDLE;
          if (cfg_loaded && c0_init_calib_complete && cnn0_input_batch_set) begin
            result_done <= 1'b0;
            state <= short_seq_mode ? ST_LOAD_TOKEN : ST_LOAD_LN1;
          end
        end
        ST_CORE_RESET: begin
          core_reset_cnt <= core_reset_cnt + 8'd1;
          if (core_reset_cnt == 8'd5) begin
            state <= ST_STREAM_LN1;
            stream_cnt <= 32'd0;
          end
        end
        ST_STREAM_LN1: begin stream_cnt <= stream_cnt + 32'd1; if (stream_cnt + 32'd1 == LN_WEIGHT_BEATS) begin state <= ST_STREAM_LN2; stream_cnt <= 32'd0; end end
        ST_STREAM_LN2: begin stream_cnt <= stream_cnt + 32'd1; if (stream_cnt + 32'd1 == LN_WEIGHT_BEATS) begin state <= ST_STREAM_QKV_B; stream_cnt <= 32'd0; end end
        ST_STREAM_QKV_B: begin stream_cnt <= stream_cnt + 32'd1; if (stream_cnt + 32'd1 == QKV_BIAS_BEATS) begin state <= ST_STREAM_OUT_B; stream_cnt <= 32'd0; end end
        ST_STREAM_OUT_B: begin stream_cnt <= stream_cnt + 32'd1; if (stream_cnt + 32'd1 == OUT_BIAS_BEATS) begin state <= ST_STREAM_FFNUP_B; stream_cnt <= 32'd0; end end
        ST_STREAM_FFNUP_B: begin stream_cnt <= stream_cnt + 32'd1; if (stream_cnt + 32'd1 == FFNUP_BIAS_BEATS) begin state <= ST_STREAM_FFNDOWN_B; stream_cnt <= 32'd0; end end
        ST_STREAM_FFNDOWN_B: begin
          stream_cnt <= stream_cnt + 32'd1;
          if (stream_cnt + 32'd1 == FFNDOWN_BIAS_BEATS) begin
            token_last_pending <= 1'b0;
            preload_full_wait <= 1'b1;
            if (short_seq_mode) begin
              run_token_idx <= 16'd0;
              state <= ST_RUN_CFG;
            end else begin
              token_slot_valid <= {TOKEN_SLOT_COUNT{1'b0}};
              token_slot_loaded <= {TOKEN_SLOT_COUNT{1'b0}};
              token_slot_exec_done <= {TOKEN_SLOT_COUNT{1'b0}};
              token_slot_store_done <= {TOKEN_SLOT_COUNT{1'b0}};
              run_token_idx <= 16'd0;
              run_slot_idx <= {TOKEN_SLOT_BITS{1'b0}};
              load_token_idx <= 16'd0;
              exec_token_idx <= 16'd0;
              store_token_idx <= 16'd0;
              state <= ST_PIPE_SCHED;
            end
          end
        end
        ST_PIPE_SCHED: begin
          if ((exec_token_idx > cfg_seqlen_word) && (store_token_idx > cfg_seqlen_word) &&
              !load_active && !store_active && !hist_busy &&
              !replay_active && !replay_v_send_pending &&
              !axi_read_busy && !axi_write_busy) begin
            if (layer_idx == (NUM_LAYERS - 1)) begin
              state <= ST_DONE;
              result_done <= 1'b1;
              $display("cnn_core done layers=%0d tokens=%0d", NUM_LAYERS, cfg_seqlen_word + 16'd1);
            end else begin
              layer_idx <= layer_idx + 4'd1;
              active_weight_bank <= ~active_weight_bank;
              active_act_bank <= ~active_act_bank;
              preload_full_wait <= 1'b1;
              stream_cnt <= 32'd0;
              state <= ST_STREAM_LN1;
              $display("cnn_core layer-switch next_layer=%0d active_weight_bank=%0d active_act_bank=%0d",
                       layer_idx + 4'd1, ~active_weight_bank, ~active_act_bank);
            end
          end else if (exec_slot_ready) begin
            run_token_idx <= exec_token_idx;
            run_slot_idx <= exec_slot_idx;
            kv_tap_head_done <= 12'd0;
            replay_active <= 1'b0;
            replay_beat_idx <= 5'd0;
            replay_head_idx <= 4'd0;
            replay_token_idx <= 16'd0;
            replay_read_phase <= 1'b0;
            replay_done <= 1'b0;
            replay_v_send_pending <= 1'b0;
            kv_hist_write_head_idx <= 4'd0;
            kv_hist_write_phase <= 1'b0;
            hist_state <= HIST_IDLE;
            token_last_pending <= 1'b0;
            token_res_started <= 1'b0;
            state <= ST_RUN_CFG;
          end
        end
        ST_RUN_CFG: begin
          kv_tap_head_done <= 12'd0;
          replay_active <= 1'b0;
          replay_beat_idx <= 5'd0;
          replay_head_idx <= 4'd0;
          replay_token_idx <= 16'd0;
          replay_read_phase <= 1'b0;
          replay_done <= 1'b0;
          replay_v_send_pending <= 1'b0;
          kv_hist_write_head_idx <= 4'd0;
          kv_hist_write_phase <= 1'b0;
          hist_state <= HIST_IDLE;
          token_res_started <= 1'b0;
          state <= ST_PRELOAD_PULSE;
        end
        ST_PRELOAD_PULSE: begin state <= ST_PRELOAD_WAIT; preload_wait_cnt <= 8'd0; end
        ST_PRELOAD_WAIT: begin
          preload_wait_cnt <= preload_wait_cnt + 8'd1;
          if (preload_wait_cnt == preload_wait_target) begin
            preload_full_wait <= 1'b0;
            state <= ST_RUN;
          end
        end
        ST_RUN: begin
          if (replay_path_enable && long_seq_mode && !replay_done && replay_all_heads_done && !hist_busy) begin
            kv_hist_write_head_idx <= 4'd0;
            kv_hist_write_phase <= 1'b0;
            hist_state <= HIST_WRITE;
          end else if (token_last_pending && (!replay_path_enable || replay_done)) begin
            token_last_pending <= 1'b0;
            token_res_started <= 1'b0;
            $display("cnn_core token-done layer=%0d token=%0d cfg_seqlen=%0d run_last_token=%0d run_last_layer=%0d core_res_addr=%0d",
                     layer_idx, run_token_idx, cfg_seqlen_word, run_last_token, run_last_layer, token_last_core_addr);
            if (short_seq_mode) begin
              if (run_last_layer) begin
                writeback_idx <= 11'd0;
                state <= ST_WRITEBACK;
              end else begin
                layer_idx <= layer_idx + 4'd1;
                active_weight_bank <= ~active_weight_bank;
                active_act_bank <= ~active_act_bank;
                preload_full_wait <= 1'b1;
                stream_cnt <= 32'd0;
                state <= ST_STREAM_LN1;
                $display("cnn_core layer-switch next_layer=%0d active_weight_bank=%0d active_act_bank=%0d",
                         layer_idx + 4'd1, ~active_weight_bank, ~active_act_bank);
              end
            end else begin
              exec_token_idx <= exec_token_idx + 16'd1;
              state <= ST_PIPE_SCHED;
            end
          end
        end
        ST_KVHIST_PREP: begin end
        ST_KVHIST_WRITE: begin end
        ST_REPLAY_PREP: begin end
        ST_REPLAY_READ: begin end
        ST_REPLAY_STREAM: begin end
        ST_WRITEBACK: begin end
        ST_DONE: begin end
        default: begin end
      endcase

      // Keep replay progress owned by the history sidecar state so the
      // control does not drift back toward a foreground sub-FSM.
      if (hist_state == HIST_REPLAY_STREAM &&
          !replay_active && !replay_v_send_pending) begin
        if (replay_head_idx == 4'd11) begin
          if (replay_token_idx == run_token_idx) begin
            replay_done <= 1'b1;
            hist_state <= HIST_IDLE;
          end else begin
            replay_token_idx <= replay_token_idx + 16'd1;
            replay_head_idx <= 4'd0;
            replay_beat_idx <= 5'd0;
            if (replay_token_idx + 16'd1 == run_token_idx) begin
              replay_v_send_pending <= 1'b1;
              replay_active <= 1'b1;
              hist_state <= HIST_REPLAY_STREAM;
            end else begin
              replay_read_phase <= 1'b0;
              hist_state <= HIST_REPLAY_READ;
            end
          end
        end else begin
          replay_head_idx <= replay_head_idx + 4'd1;
          replay_beat_idx <= 5'd0;
          if (replay_token_idx == run_token_idx) begin
            replay_v_send_pending <= 1'b1;
            replay_active <= 1'b1;
            hist_state <= HIST_REPLAY_STREAM;
          end else begin
            replay_read_phase <= 1'b0;
            hist_state <= HIST_REPLAY_READ;
          end
        end
      end
    end
  end
endmodule
