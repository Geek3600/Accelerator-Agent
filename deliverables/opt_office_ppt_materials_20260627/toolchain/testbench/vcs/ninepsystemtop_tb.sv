`timescale 1ns/1ps

module NinePSystemTop_tb;

  localparam int DDR_LATENCY = 4;
  localparam int MAX_CYCLES = 1000000000;
  localparam int MAX_DDR_BEATS = 300000;
  localparam int MAX_DDR_WORDS = MAX_DDR_BEATS * 16;
  localparam int MAX_GOLDEN_BEATS = 65536;
  localparam int MAX_GOLDEN_WORDS = MAX_GOLDEN_BEATS * 12;
  localparam int PROGRESS_CYCLES = 100000;
localparam int DEBUG_TOKEN_START = 31;
localparam int DEBUG_TOKEN_END = 31;
  localparam int DEBUG_ADDR_START = 0;
  localparam int DEBUG_ADDR_END = 63;
  localparam bit ENABLE_DEEP_DEBUG = 1'b1;

  logic clock = 1'b0;
  logic reset = 1'b1;

  logic         io_start;
  logic [15:0]  io_cfg_seqlen;
  logic         io_cfg_prefill;
  logic [15:0]  io_attn_cfg_seqlen;
  logic         io_attn_cfg_prefill;
  logic         io_attn_cfg_valid;
  logic         io_attn_cfg_single_query;
  logic [31:0]  io_ln1_out_inv_scale;
  logic [7:0]   io_ln1_out_zero_point;
  logic [31:0]  io_q_out_inv_scale;
  logic [31:0]  io_k_out_inv_scale;
  logic [31:0]  io_v_out_inv_scale;
  logic [31:0]  io_q_bias_scale;
  logic [31:0]  io_k_bias_scale;
  logic [31:0]  io_v_bias_scale;
  logic [31:0]  io_dm1_out_scale;
  logic [31:0]  io_dm2_ctx_inv_scale;
  logic [7:0]   io_dm2_ctx_zero_point;
  logic [31:0]  io_dm2_out_inv_scale;
  logic [31:0]  io_out_out_scale;
  logic [31:0]  io_ln2_out_inv_scale;
  logic [7:0]   io_ln2_out_zero_point;
  logic [31:0]  io_ffnup_out_inv_scale;
  logic [31:0]  io_ffnup_bias_scale;
  logic [31:0]  io_ffndown_out_scale;
  logic [31:0]  io_input_base_addr;
  logic [31:0]  io_ln1_w_base_addr;
  logic [31:0]  io_qkv_w_base_addr;
  logic [31:0]  io_qkv_b_base_addr;
  logic [31:0]  io_sm_base_addr;
  logic [31:0]  io_out_w_base_addr;
  logic [31:0]  io_out_b_base_addr;
  logic [31:0]  io_ln2_w_base_addr;
  logic [31:0]  io_ffnup_w_base_addr;
  logic [31:0]  io_ffnup_b_base_addr;
  logic [31:0]  io_ffndown_w_base_addr;
  logic [31:0]  io_ffndown_b_base_addr;
  logic [31:0]  io_ddr_addr;
  logic [2:0]   io_ddr_cmd;
  logic         io_ddr_en;
  logic         io_ddr_rdy;
  logic [511:0] io_ddr_rd_data;
  logic         io_ddr_rd_data_valid;
  logic         io_ddr_rd_data_end;
  logic         io_ddr_init_done;
  logic [383:0] io_res;
  logic         io_res_st;
  logic [31:0]  io_res_addr;
  logic         io_res_valid;
  logic         io_res_last;
  logic         io_res_ready;

  logic [31:0] ddr_image_words [0:MAX_DDR_WORDS-1];
  logic [31:0] golden_words [0:MAX_GOLDEN_WORDS-1];
  logic [31:0] observed_words [0:MAX_GOLDEN_WORDS-1];
  bit seen [0:MAX_GOLDEN_BEATS-1];
  bit pending_valid [0:DDR_LATENCY-1];
  logic [31:0] pending_addr [0:DDR_LATENCY-1];
  bit dbg_ln2_x_reported;
  logic [3:0] dbg_prev_ln2_state;
  logic [15:0] dbg_prev_run_token;
  logic dbg_prev_front_adapter_ready;
  logic [0:0] dbg_prev_ln_addr_state;
  logic dbg_prev_ln_data_valid;
  logic [3:0] dbg_prev_ln_state;
  logic dbg_prev_ln_ready;
  logic dbg_prev_resadd_orig_ready;
  logic [1:0] dbg_prev_qkv_state;
  logic dbg_prev_resadd2_s7_ready;
  logic dbg_prev_resadd_reading;
  logic dbg_prev_resadd2_reading;
  logic [4:0] dbg_prev_top_state;
  logic dbg_prev_core_cfg_valid;
  logic dbg_prev_core_layer_st;
  logic dbg_prev_ln_start_pending;

  int ddr_word_count;
  int ddr_beats;
  int golden_word_count;
  int golden_beats;
  int seen_count;
  bit saw_st;
  bit saw_last;

  integer idx;
  integer cycle;
  integer word_idx;
  integer dbg_dm1_res_cnt;
  integer dbg_dm1_ready0_cnt;
  integer dbg_sm_in_cnt;
  integer dbg_sm_in_ready0_cnt;
  integer dbg_sm_res_cnt;
  integer dbg_sm_ready0_cnt;
  integer dbg_vc_res_cnt;
  integer dbg_vc_ready0_cnt;
  integer dbg_dm2_in_cnt;
  integer dbg_dm2_ctx_only_cnt;
  integer dbg_dm2_v_only_cnt;
  integer dbg_dm2_both_cnt;
  integer dbg_dm2_ctxr0_cnt;
  integer dbg_dm2_vr0_cnt;
  integer dbg_dm2_core_cnt;
  integer dbg_dm2_res_cnt;
  integer dbg_outlinear_out_cnt;
  string window_dir;
  string cfg_path;
  string ddr_path;
  string golden_path;

  NinePSystemTop dut (
    .clock(clock),
    .reset(reset),
    .io_start(io_start),
    .io_cfg_seqlen(io_cfg_seqlen),
    .io_cfg_prefill(io_cfg_prefill),
    .io_attn_cfg_seqlen(io_attn_cfg_seqlen),
    .io_attn_cfg_prefill(io_attn_cfg_prefill),
    .io_attn_cfg_valid(io_attn_cfg_valid),
    .io_attn_cfg_single_query(io_attn_cfg_single_query),
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
    .io_input_base_addr(io_input_base_addr),
    .io_ln1_w_base_addr(io_ln1_w_base_addr),
    .io_qkv_w_base_addr(io_qkv_w_base_addr),
    .io_qkv_b_base_addr(io_qkv_b_base_addr),
    .io_sm_base_addr(io_sm_base_addr),
    .io_out_w_base_addr(io_out_w_base_addr),
    .io_out_b_base_addr(io_out_b_base_addr),
    .io_ln2_w_base_addr(io_ln2_w_base_addr),
    .io_ffnup_w_base_addr(io_ffnup_w_base_addr),
    .io_ffnup_b_base_addr(io_ffnup_b_base_addr),
    .io_ffndown_w_base_addr(io_ffndown_w_base_addr),
    .io_ffndown_b_base_addr(io_ffndown_b_base_addr),
    .io_ddr_addr(io_ddr_addr),
    .io_ddr_cmd(io_ddr_cmd),
    .io_ddr_en(io_ddr_en),
    .io_ddr_rdy(io_ddr_rdy),
    .io_ddr_rd_data(io_ddr_rd_data),
    .io_ddr_rd_data_valid(io_ddr_rd_data_valid),
    .io_ddr_rd_data_end(io_ddr_rd_data_end),
    .io_ddr_init_done(io_ddr_init_done),
    .io_res(io_res),
    .io_res_st(io_res_st),
    .io_res_addr(io_res_addr),
    .io_res_valid(io_res_valid),
    .io_res_last(io_res_last),
    .io_res_ready(io_res_ready)
  );

  always #5 clock = ~clock;

  function automatic real abs_real(input real value);
    if (value < 0.0) begin
      return -value;
    end
    return value;
  endfunction

  function automatic bit in_debug_addr_window(input int addr);
    begin
      in_debug_addr_window = (addr >= DEBUG_ADDR_START) && (addr <= DEBUG_ADDR_END);
    end
  endfunction

  function automatic bit in_debug_token_window(input int token);
    begin
      in_debug_token_window = (token >= DEBUG_TOKEN_START) && (token <= DEBUG_TOKEN_END);
    end
  endfunction

  task automatic fatal_msg(input string msg);
    begin
      $display("%s", msg);
      $fatal(1);
    end
  endtask

  function automatic logic [31:0] byteswap32(input logic [31:0] w);
    begin
      byteswap32 = {w[7:0], w[15:8], w[23:16], w[31:24]};
    end
  endfunction

  task automatic load_ddr_image(input string path, output int word_count_out);
    int fd;
    int byte_count;
    int word_idx_local;
    begin
      fd = $fopen(path, "rb");
      if (fd == 0) begin
        fatal_msg($sformatf("failed to open binary: %s", path));
      end
      byte_count = $fread(ddr_image_words, fd);
      $fclose(fd);
      if ((byte_count % 4) != 0) begin
        fatal_msg($sformatf("unexpected binary size: %s bytes=%0d", path, byte_count));
      end
      word_count_out = byte_count / 4;
      for (word_idx_local = 0; word_idx_local < word_count_out; word_idx_local++) begin
        ddr_image_words[word_idx_local] = byteswap32(ddr_image_words[word_idx_local]);
      end
    end
  endtask

  task automatic load_golden(input string path, output int word_count_out);
    int fd;
    int byte_count;
    int word_idx_local;
    begin
      fd = $fopen(path, "rb");
      if (fd == 0) begin
        fatal_msg($sformatf("failed to open binary: %s", path));
      end
      byte_count = $fread(golden_words, fd);
      $fclose(fd);
      if ((byte_count % 4) != 0) begin
        fatal_msg($sformatf("unexpected binary size: %s bytes=%0d", path, byte_count));
      end
      word_count_out = byte_count / 4;
      for (word_idx_local = 0; word_idx_local < word_count_out; word_idx_local++) begin
        golden_words[word_idx_local] = byteswap32(golden_words[word_idx_local]);
      end
    end
  endtask

  task automatic parse_cfg(input string path);
    int fd;
    int parsed_int;
    begin
      fd = $fopen(path, "r");
      if (fd == 0) begin
        fatal_msg($sformatf("failed to open cfg: %s", path));
      end
      if ($fscanf(fd, "cfg_seqlen=%d\n", parsed_int) != 1) fatal_msg("parse_cfg cfg_seqlen failed");
      io_cfg_seqlen = parsed_int[15:0];
      if ($fscanf(fd, "input_beats=%d\n", parsed_int) != 1) fatal_msg("parse_cfg input_beats failed");
      if ($fscanf(fd, "output_beats=%d\n", parsed_int) != 1) fatal_msg("parse_cfg output_beats failed");
      if ($fscanf(fd, "ln1_out_inv_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse_cfg ln1_out_inv_scale failed");
      io_ln1_out_inv_scale = parsed_int[31:0];
      if ($fscanf(fd, "ln1_out_zero_point_s8=%d\n", parsed_int) != 1) fatal_msg("parse_cfg ln1_out_zero_point failed");
      io_ln1_out_zero_point = parsed_int[7:0];
      if ($fscanf(fd, "q_out_inv_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse_cfg q_out_inv_scale failed");
      io_q_out_inv_scale = parsed_int[31:0];
      if ($fscanf(fd, "k_out_inv_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse_cfg k_out_inv_scale failed");
      io_k_out_inv_scale = parsed_int[31:0];
      if ($fscanf(fd, "v_out_inv_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse_cfg v_out_inv_scale failed");
      io_v_out_inv_scale = parsed_int[31:0];
      if ($fscanf(fd, "q_bias_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse_cfg q_bias_scale failed");
      io_q_bias_scale = parsed_int[31:0];
      if ($fscanf(fd, "k_bias_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse_cfg k_bias_scale failed");
      io_k_bias_scale = parsed_int[31:0];
      if ($fscanf(fd, "v_bias_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse_cfg v_bias_scale failed");
      io_v_bias_scale = parsed_int[31:0];
      if ($fscanf(fd, "dm1_out_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse_cfg dm1_out_scale failed");
      io_dm1_out_scale = parsed_int[31:0];
      if ($fscanf(fd, "dm2_ctx_inv_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse_cfg dm2_ctx_inv_scale failed");
      io_dm2_ctx_inv_scale = parsed_int[31:0];
      if ($fscanf(fd, "dm2_ctx_zero_point_u8=%d\n", parsed_int) != 1) fatal_msg("parse_cfg dm2_ctx_zero_point failed");
      io_dm2_ctx_zero_point = parsed_int[7:0];
      if ($fscanf(fd, "dm2_out_inv_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse_cfg dm2_out_inv_scale failed");
      io_dm2_out_inv_scale = parsed_int[31:0];
      if ($fscanf(fd, "out_out_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse_cfg out_out_scale failed");
      io_out_out_scale = parsed_int[31:0];
      if ($fscanf(fd, "ln2_out_inv_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse_cfg ln2_out_inv_scale failed");
      io_ln2_out_inv_scale = parsed_int[31:0];
      if ($fscanf(fd, "ln2_out_zero_point_s8=%d\n", parsed_int) != 1) fatal_msg("parse_cfg ln2_out_zero_point failed");
      io_ln2_out_zero_point = parsed_int[7:0];
      if ($fscanf(fd, "ffnup_out_inv_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse_cfg ffnup_out_inv_scale failed");
      io_ffnup_out_inv_scale = parsed_int[31:0];
      if ($fscanf(fd, "ffnup_bias_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse_cfg ffnup_bias_scale failed");
      io_ffnup_bias_scale = parsed_int[31:0];
      if ($fscanf(fd, "ffndown_out_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse_cfg ffndown_out_scale failed");
      io_ffndown_out_scale = parsed_int[31:0];
      if ($fscanf(fd, "ddr_input_base_addr=%d\n", parsed_int) != 1) fatal_msg("parse_cfg ddr_input_base_addr failed");
      io_input_base_addr = parsed_int[31:0];
      if ($fscanf(fd, "ddr_ln1_w_base_addr=%d\n", parsed_int) != 1) fatal_msg("parse_cfg ddr_ln1_w_base_addr failed");
      io_ln1_w_base_addr = parsed_int[31:0];
      if ($fscanf(fd, "ddr_qkv_w_base_addr=%d\n", parsed_int) != 1) fatal_msg("parse_cfg ddr_qkv_w_base_addr failed");
      io_qkv_w_base_addr = parsed_int[31:0];
      if ($fscanf(fd, "ddr_qkv_b_base_addr=%d\n", parsed_int) != 1) fatal_msg("parse_cfg ddr_qkv_b_base_addr failed");
      io_qkv_b_base_addr = parsed_int[31:0];
      if ($fscanf(fd, "ddr_sm_base_addr=%d\n", parsed_int) != 1) fatal_msg("parse_cfg ddr_sm_base_addr failed");
      io_sm_base_addr = parsed_int[31:0];
      if ($fscanf(fd, "ddr_out_w_base_addr=%d\n", parsed_int) != 1) fatal_msg("parse_cfg ddr_out_w_base_addr failed");
      io_out_w_base_addr = parsed_int[31:0];
      if ($fscanf(fd, "ddr_out_b_base_addr=%d\n", parsed_int) != 1) fatal_msg("parse_cfg ddr_out_b_base_addr failed");
      io_out_b_base_addr = parsed_int[31:0];
      if ($fscanf(fd, "ddr_ln2_w_base_addr=%d\n", parsed_int) != 1) fatal_msg("parse_cfg ddr_ln2_w_base_addr failed");
      io_ln2_w_base_addr = parsed_int[31:0];
      if ($fscanf(fd, "ddr_ffnup_w_base_addr=%d\n", parsed_int) != 1) fatal_msg("parse_cfg ddr_ffnup_w_base_addr failed");
      io_ffnup_w_base_addr = parsed_int[31:0];
      if ($fscanf(fd, "ddr_ffnup_b_base_addr=%d\n", parsed_int) != 1) fatal_msg("parse_cfg ddr_ffnup_b_base_addr failed");
      io_ffnup_b_base_addr = parsed_int[31:0];
      if ($fscanf(fd, "ddr_ffndown_w_base_addr=%d\n", parsed_int) != 1) fatal_msg("parse_cfg ddr_ffndown_w_base_addr failed");
      io_ffndown_w_base_addr = parsed_int[31:0];
      if ($fscanf(fd, "ddr_ffndown_b_base_addr=%d\n", parsed_int) != 1) fatal_msg("parse_cfg ddr_ffndown_b_base_addr failed");
      io_ffndown_b_base_addr = parsed_int[31:0];
      $fclose(fd);
    end
  endtask

  task automatic check_outputs;
    int beat_idx;
    int lane_idx;
    real obs;
    real exp;
    real abs_err;
    begin
      if (!saw_st) begin
        fatal_msg("NinePSystemTop never asserted io_res_st");
      end
      if (!saw_last) begin
        fatal_msg("NinePSystemTop never asserted io_res_last");
      end
      for (beat_idx = 0; beat_idx < golden_beats; beat_idx++) begin
        if (!seen[beat_idx]) begin
          fatal_msg($sformatf("missing NinePSystemTop output beat=%0d", beat_idx));
        end
        for (lane_idx = 0; lane_idx < 12; lane_idx++) begin
          if (observed_words[beat_idx * 12 + lane_idx] != golden_words[beat_idx * 12 + lane_idx]) begin
            obs = $bitstoshortreal(observed_words[beat_idx * 12 + lane_idx]);
            exp = $bitstoshortreal(golden_words[beat_idx * 12 + lane_idx]);
            abs_err = abs_real(obs - exp);
            if (abs_err > 5.0e-4) begin
              fatal_msg(
                  $sformatf(
                      "NinePSystemTop mismatch at beat=%0d lane=%0d observed_bits=0x%08x expected_bits=0x%08x observed=%f expected=%f abs_err=%f",
                      beat_idx,
                      lane_idx,
                      observed_words[beat_idx * 12 + lane_idx],
                      golden_words[beat_idx * 12 + lane_idx],
                      obs,
                      exp,
                      abs_err
                  )
              );
            end
          end
        end
      end
      $display("NinePSystemTop PASS beats=%0d", golden_beats);
    end
  endtask

  initial begin
    if (!$value$plusargs("window_dir=%s", window_dir)) begin
      fatal_msg("usage: simv +window_dir=<window_dir>");
    end

    cfg_path = {window_dir, "/window.cfg"};
    ddr_path = {window_dir, "/artifacts/ddr_image.u32.bin"};
    golden_path = {window_dir, "/artifacts/golden.u32.bin"};

    io_start = 1'b0;
    io_cfg_seqlen = '0;
    io_cfg_prefill = 1'b1;
    io_attn_cfg_seqlen = '0;
    io_attn_cfg_prefill = 1'b1;
    io_attn_cfg_valid = 1'b1;
    io_attn_cfg_single_query = 1'b0;
    io_ln1_out_inv_scale = '0;
    io_ln1_out_zero_point = '0;
    io_q_out_inv_scale = '0;
    io_k_out_inv_scale = '0;
    io_v_out_inv_scale = '0;
    io_q_bias_scale = '0;
    io_k_bias_scale = '0;
    io_v_bias_scale = '0;
    io_dm1_out_scale = '0;
    io_dm2_ctx_inv_scale = '0;
    io_dm2_ctx_zero_point = '0;
    io_dm2_out_inv_scale = '0;
    io_out_out_scale = '0;
    io_ln2_out_inv_scale = '0;
    io_ln2_out_zero_point = '0;
    io_ffnup_out_inv_scale = '0;
    io_ffnup_bias_scale = '0;
    io_ffndown_out_scale = '0;
    io_input_base_addr = '0;
    io_ln1_w_base_addr = '0;
    io_qkv_w_base_addr = '0;
    io_qkv_b_base_addr = '0;
    io_sm_base_addr = '0;
    io_out_w_base_addr = '0;
    io_out_b_base_addr = '0;
    io_ln2_w_base_addr = '0;
    io_ffnup_w_base_addr = '0;
    io_ffnup_b_base_addr = '0;
    io_ffndown_w_base_addr = '0;
    io_ffndown_b_base_addr = '0;
    io_ddr_rdy = 1'b1;
    io_ddr_rd_data = '0;
    io_ddr_rd_data_valid = 1'b0;
    io_ddr_rd_data_end = 1'b0;
    io_ddr_init_done = 1'b1;
    io_res_ready = 1'b1;
    ddr_word_count = 0;
    ddr_beats = 0;
    golden_word_count = 0;
    golden_beats = 0;
    seen_count = 0;
    saw_st = 1'b0;
    saw_last = 1'b0;
    dbg_ln2_x_reported = 1'b0;
    dbg_prev_ln2_state = 4'hf;
    dbg_prev_run_token = 16'hffff;
    dbg_prev_front_adapter_ready = 1'b0;
    dbg_prev_ln_addr_state = 1'b0;
    dbg_prev_ln_data_valid = 1'b0;
    dbg_prev_ln_state = 4'hf;
    dbg_prev_ln_ready = 1'b0;
    dbg_prev_resadd_orig_ready = 1'b0;
    dbg_prev_qkv_state = 2'b11;
    dbg_prev_resadd2_s7_ready = 1'b0;
    dbg_prev_resadd_reading = 1'b0;
    dbg_prev_resadd2_reading = 1'b0;
    dbg_dm1_res_cnt = 0;
    dbg_dm1_ready0_cnt = 0;
    dbg_sm_in_cnt = 0;
    dbg_sm_in_ready0_cnt = 0;
    dbg_sm_res_cnt = 0;
    dbg_sm_ready0_cnt = 0;
    dbg_vc_res_cnt = 0;
    dbg_vc_ready0_cnt = 0;
    dbg_dm2_in_cnt = 0;
    dbg_dm2_ctx_only_cnt = 0;
    dbg_dm2_v_only_cnt = 0;
    dbg_dm2_both_cnt = 0;
    dbg_dm2_ctxr0_cnt = 0;
    dbg_dm2_vr0_cnt = 0;
    dbg_dm2_core_cnt = 0;
    dbg_dm2_res_cnt = 0;
    dbg_outlinear_out_cnt = 0;

    for (idx = 0; idx < MAX_GOLDEN_BEATS; idx++) begin
      seen[idx] = 1'b0;
    end
    for (idx = 0; idx < DDR_LATENCY; idx++) begin
      pending_valid[idx] = 1'b0;
      pending_addr[idx] = '0;
    end

    parse_cfg(cfg_path);
    io_attn_cfg_seqlen = io_cfg_seqlen;
    $display(
        "NinePSystemTop cfg loaded cfg_seqlen=%0d attn_cfg_seqlen=%0d single_query=%0d",
        io_cfg_seqlen,
        io_attn_cfg_seqlen,
        io_attn_cfg_single_query
    );

    load_ddr_image(ddr_path, ddr_word_count);
    if ((ddr_word_count % 16) != 0) begin
      fatal_msg($sformatf("DDR image word count is not a multiple of 16: %0d", ddr_word_count));
    end
    ddr_beats = ddr_word_count / 16;
    if (ddr_beats > MAX_DDR_BEATS) begin
      fatal_msg($sformatf("DDR image beats exceed testbench limit: %0d", ddr_beats));
    end

    load_golden(golden_path, golden_word_count);
    if ((golden_word_count % 12) != 0) begin
      fatal_msg($sformatf("golden word count is not a multiple of 12: %0d", golden_word_count));
    end
    golden_beats = golden_word_count / 12;
    if (golden_beats > MAX_GOLDEN_BEATS) begin
      fatal_msg($sformatf("golden beats exceed testbench limit: %0d", golden_beats));
    end

    repeat (5) @(posedge clock);
    reset <= 1'b0;
    @(posedge clock);
    io_start <= 1'b1;
    @(posedge clock);
    io_start <= 1'b0;

    cycle = 0;
    while (cycle < MAX_CYCLES && seen_count < golden_beats) begin
      @(posedge clock);
      cycle = cycle + 1;
      if ((cycle % PROGRESS_CYCLES) == 0) begin
        $display(
            "SystemTop progress cycle=%0d state=%0d token=%0d ddr_en=%0d ddr_addr=%0d seen=%0d/%0d core_addr=%0d run[cfg_v=%0d layer_st=%0d wait=%0d ln_pending=%0d] top_valids[ln=%0d qkv=%0d attn=%0d out=%0d res1=%0d ln2=%0d up=%0d down=%0d top=%0d] qkv[last=%0d addr=%0d state=%0d] attn_ready[qkv=%0d dm1_wr=%0d dm1_rd=%0d vc_in=%0d sm_in=%0d dm2_ctx_r=%0d dm2_v_r=%0d] attn_valid[dm1=%0d sm=%0d vc=%0d dm2=%0d] dm1_pipe[lu=%0d cu=%0d su=%0d] dm1_load[last=%0d addr=%0d state=%0d] sm_pipe[sq=%0d in=%0d cu=%0d su=%0d st=%0d] vc_pipe[in=%0d out=%0d st=%0d] dm2_pipe[ctx=%0d v=%0d cu=%0d su=%0d addr=%0d] ln2[state=%0d in=%0d w=%0d tok=%0d var=0x%08x sqrt_rdy=%0d sqrt_v=%0d] front[in_rdy=%0d adapter=%0d ln_gen_state=%0d ln_gen_v=%0d ln_gen_last=%0d ln_gen_addr=%0d ln_state=%0d ln_loaded=%0d ln_tok=%0d ln_rdy=%0d res1_orig_rdy=%0d res1_state=%0d res2_s7_rdy=%0d res2_state=%0d ffndown_v=%0d]",
            cycle,
            dut.state,
            dut.run_token_idx,
            io_ddr_en,
            io_ddr_addr,
            seen_count,
            golden_beats,
            dut.core_data_in_addr,
            dut.core_cfg_valid,
            dut.core_layer_st,
            dut.preload_wait_cnt,
            dut.u_core.ln_addr_gen.start_pending,
            dut.u_core._layernorm_io_res_valid,
            dut.u_core._qkvlinear_io_data_out_valid,
            dut.u_core._atten_io_res_valid,
            dut.u_core._outlinear_io_data_out_valid,
            dut.u_core._resadd_io_res_valid,
            dut.u_core._layernorm2_io_res_valid,
            dut.u_core._ffnup_io_data_out_valid,
            dut.u_core._ffndown_io_data_out_valid,
            dut.u_core.io_res_valid,
            dut.u_core._qkvlinear_io_data_out_last,
            dut.u_core._qkvlinear_io_data_out_addr,
            dut.u_core.qkvlinear.state,
            dut.u_core._atten_io_data_ready,
            dut.u_core.atten.dm1.mem_inst.io_w_ready,
            dut.u_core.atten.dm1.mem_inst.io_r_ready,
            dut.u_core.atten._vcache_io_data_in_ready,
            dut.u_core.atten._softmax_io_data_ready,
            dut.u_core.atten._dm2_io_data_in_ctx_ready,
            dut.u_core.atten._dm2_io_data_in_v_ready,
            dut.u_core.atten._dm1_io_res_valid,
            dut.u_core.atten._softmax_io_res_valid,
            dut.u_core.atten._vcache_io_res_valid,
            dut.u_core.atten.io_res_valid,
            dut.u_core.atten.dm1.lu_inst.io_data_out_valid,
            dut.u_core.atten.dm1.cu_inst.io_data_out_valid,
            dut.u_core.atten.dm1.su_inst.io_data_out_valid,
            dut.u_core.atten.dm1.lu_inst.io_data_in_last,
            dut.u_core.atten.dm1.lu_inst.io_data_in_addr,
            dut.u_core.atten.dm1.lu_inst.state,
            1'b0,
            dut.u_core.atten.softmax.io_data_valid,
            dut.u_core.atten.softmax._cuInst_io_data_out_valid,
            dut.u_core.atten.softmax.io_res_valid,
            dut.u_core.atten.softmax.io_data_in_st,
            dut.u_core.atten.vcache.io_data_in_valid,
            dut.u_core.atten.vcache.lsu_inst.io_data_out_valid,
            dut.u_core.atten.vcache.io_res_st,
            dut.u_core.atten.dm2.loaduInst.io_data_out_ctx_valid,
            dut.u_core.atten.dm2.loaduInst.io_data_out_v_valid,
            dut.u_core.atten.dm2.dmInst.io_data_out_valid,
            dut.u_core.atten.dm2.io_res_valid,
            dut.u_core.atten.dm2.io_res_addr,
            dut.u_core.layernorm2.state,
            dut.u_core.layernorm2.inputLoaded,
            dut.u_core.layernorm2.weightsLoaded,
            dut.u_core.layernorm2.tokenCount,
            dut.u_core.layernorm2.varReg,
            dut.u_core.layernorm2.sqrt.io_inReady,
            dut.u_core.layernorm2.sqrt.io_outValidSqrt,
            dut.core_data_in_ready,
            (dut.u_core._layernorm_io_data_ready & dut.u_core._resadd_io_orig_ready),
            dut.u_core.ln_addr_gen.state,
            dut.u_core._ln_addr_gen_io_data_valid,
            dut.u_core._ln_addr_gen_io_data_last,
            dut.u_core._ln_addr_gen_io_data_addr,
            dut.u_core.layernorm.state,
            dut.u_core.layernorm.inputLoaded,
            dut.u_core.layernorm.tokenCount,
            dut.u_core._layernorm_io_data_ready,
            dut.u_core._resadd_io_orig_ready,
            dut.u_core.resadd.state,
            dut.u_core._resadd2_io_s7_ready,
            dut.u_core.resadd2.state,
            dut.u_core._ffndown_io_data_out_valid
        );
        if (ENABLE_DEEP_DEBUG && in_debug_token_window(dut.run_token_idx)) begin
          $display(
              "Debug summary token=%0d dm1=%0d dm1_r0=%0d sm_in=%0d sm_in_r0=%0d sm=%0d sm_r0=%0d vc=%0d vc_r0=%0d dm2in=%0d ctx_only=%0d v_only=%0d both=%0d ctxr0=%0d vr0=%0d dm2core=%0d dm2res=%0d out=%0d",
              dut.run_token_idx,
              dbg_dm1_res_cnt,
              dbg_dm1_ready0_cnt,
              dbg_sm_in_cnt,
              dbg_sm_in_ready0_cnt,
              dbg_sm_res_cnt,
              dbg_sm_ready0_cnt,
              dbg_vc_res_cnt,
              dbg_vc_ready0_cnt,
              dbg_dm2_in_cnt,
              dbg_dm2_ctx_only_cnt,
              dbg_dm2_v_only_cnt,
              dbg_dm2_both_cnt,
              dbg_dm2_ctxr0_cnt,
              dbg_dm2_vr0_cnt,
              dbg_dm2_core_cnt,
              dbg_dm2_res_cnt,
              dbg_outlinear_out_cnt
          );
        end
      end
      if (ENABLE_DEEP_DEBUG &&
          in_debug_token_window(dut.run_token_idx) &&
          dut.u_core.atten._dm1_io_res_valid) begin
        dbg_dm1_res_cnt = dbg_dm1_res_cnt + 1;
        if (!dut.u_core.atten.dm1.io_res_ready) begin
          dbg_dm1_ready0_cnt = dbg_dm1_ready0_cnt + 1;
        end
      end
      if (ENABLE_DEEP_DEBUG &&
          in_debug_token_window(dut.run_token_idx) &&
          dut.u_core.atten.softmax.io_data_valid) begin
        dbg_sm_in_cnt = dbg_sm_in_cnt + 1;
        if (!dut.u_core.atten._softmax_io_data_ready) begin
          dbg_sm_in_ready0_cnt = dbg_sm_in_ready0_cnt + 1;
        end
      end
      if (ENABLE_DEEP_DEBUG &&
          in_debug_token_window(dut.run_token_idx) &&
          dut.u_core.atten._softmax_io_res_valid) begin
        dbg_sm_res_cnt = dbg_sm_res_cnt + 1;
        if (!dut.u_core.atten.ctxToDm2Q.io_enq_ready) begin
          dbg_sm_ready0_cnt = dbg_sm_ready0_cnt + 1;
        end
      end
      if (ENABLE_DEEP_DEBUG &&
          in_debug_token_window(dut.run_token_idx) &&
          dut.u_core.atten._vcache_io_res_valid) begin
        dbg_vc_res_cnt = dbg_vc_res_cnt + 1;
        if (!dut.u_core.atten.vToDm2Q.io_enq_ready) begin
          dbg_vc_ready0_cnt = dbg_vc_ready0_cnt + 1;
        end
      end
      if (ENABLE_DEEP_DEBUG &&
          in_debug_token_window(dut.run_token_idx) &&
          (dut.u_core.atten.dm2.loaduInst.io_data_out_ctx_valid ||
           dut.u_core.atten.dm2.loaduInst.io_data_out_v_valid)) begin
        dbg_dm2_in_cnt = dbg_dm2_in_cnt + 1;
        if (dut.u_core.atten.dm2.loaduInst.io_data_out_ctx_valid &&
            !dut.u_core.atten.dm2.loaduInst.io_data_out_v_valid) begin
          dbg_dm2_ctx_only_cnt = dbg_dm2_ctx_only_cnt + 1;
        end
        if (!dut.u_core.atten.dm2.loaduInst.io_data_out_ctx_valid &&
            dut.u_core.atten.dm2.loaduInst.io_data_out_v_valid) begin
          dbg_dm2_v_only_cnt = dbg_dm2_v_only_cnt + 1;
        end
        if (dut.u_core.atten.dm2.loaduInst.io_data_out_ctx_valid &&
            dut.u_core.atten.dm2.loaduInst.io_data_out_v_valid) begin
          dbg_dm2_both_cnt = dbg_dm2_both_cnt + 1;
        end
        if (!dut.u_core.atten._dm2_io_data_in_ctx_ready) begin
          dbg_dm2_ctxr0_cnt = dbg_dm2_ctxr0_cnt + 1;
        end
        if (!dut.u_core.atten._dm2_io_data_in_v_ready) begin
          dbg_dm2_vr0_cnt = dbg_dm2_vr0_cnt + 1;
        end
      end
      if (ENABLE_DEEP_DEBUG &&
          in_debug_token_window(dut.run_token_idx) &&
          dut.u_core.atten.dm2.dmInst.io_data_out_valid) begin
        dbg_dm2_core_cnt = dbg_dm2_core_cnt + 1;
      end
      if (ENABLE_DEEP_DEBUG &&
          in_debug_token_window(dut.run_token_idx) &&
          dut.u_core.atten.dm2.io_res_valid) begin
        dbg_dm2_res_cnt = dbg_dm2_res_cnt + 1;
      end
      if (ENABLE_DEEP_DEBUG &&
          in_debug_token_window(dut.run_token_idx) &&
          dut.u_core._outlinear_io_data_out_valid) begin
        dbg_outlinear_out_cnt = dbg_outlinear_out_cnt + 1;
      end
      if (ENABLE_DEEP_DEBUG &&
          (dut.run_token_idx >= DEBUG_TOKEN_START) &&
          (dut.run_token_idx <= DEBUG_TOKEN_END) &&
          ((dut.run_token_idx != dbg_prev_run_token) ||
           (dut.state != dbg_prev_top_state) ||
           (dut.core_cfg_valid != dbg_prev_core_cfg_valid) ||
           (dut.core_layer_st != dbg_prev_core_layer_st) ||
           (dut.u_core.ln_addr_gen.start_pending != dbg_prev_ln_start_pending) ||
           ((dut.u_core._layernorm_io_data_ready & dut.u_core._resadd_io_orig_ready) != dbg_prev_front_adapter_ready) ||
           (dut.u_core.ln_addr_gen.state != dbg_prev_ln_addr_state) ||
           (dut.u_core._ln_addr_gen_io_data_valid != dbg_prev_ln_data_valid) ||
           (dut.u_core.layernorm.state != dbg_prev_ln_state) ||
           (dut.u_core._layernorm_io_data_ready != dbg_prev_ln_ready) ||
           (dut.u_core._resadd_io_orig_ready != dbg_prev_resadd_orig_ready) ||
           (dut.u_core.qkvlinear.state != dbg_prev_qkv_state) ||
           (dut.u_core._resadd2_io_s7_ready != dbg_prev_resadd2_s7_ready) ||
           (dut.u_core.resadd.state != dbg_prev_resadd_reading) ||
           (dut.u_core.resadd2.state != dbg_prev_resadd2_reading))) begin
        $display(
            "Front trace cycle=%0d top_state=%0d token=%0d cfg_v=%0d layer_st=%0d wait=%0d core_in_rdy=%0d adapter=%0d ln_gen[pending=%0d state=%0d v=%0d last=%0d addr=%0d] ln[state=%0d loaded=%0d tok=%0d ready=%0d] qkv[state=%0d] res1[orig_rdy=%0d state=%0d] res2[s7_rdy=%0d state=%0d] ffndown_v=%0d top_res_v=%0d top_res_last=%0d",
            cycle,
            dut.state,
            dut.run_token_idx,
            dut.core_cfg_valid,
            dut.core_layer_st,
            dut.preload_wait_cnt,
            dut.core_data_in_ready,
            (dut.u_core._layernorm_io_data_ready & dut.u_core._resadd_io_orig_ready),
            dut.u_core.ln_addr_gen.start_pending,
            dut.u_core.ln_addr_gen.state,
            dut.u_core._ln_addr_gen_io_data_valid,
            dut.u_core._ln_addr_gen_io_data_last,
            dut.u_core._ln_addr_gen_io_data_addr,
            dut.u_core.layernorm.state,
            dut.u_core.layernorm.inputLoaded,
            dut.u_core.layernorm.tokenCount,
            dut.u_core._layernorm_io_data_ready,
            dut.u_core.qkvlinear.state,
            dut.u_core._resadd_io_orig_ready,
            dut.u_core.resadd.state,
            dut.u_core._resadd2_io_s7_ready,
            dut.u_core.resadd2.state,
            dut.u_core._ffndown_io_data_out_valid,
            dut.u_core.io_res_valid,
            dut.u_core.io_res_last
        );
        dbg_prev_run_token = dut.run_token_idx;
        dbg_prev_top_state = dut.state;
        dbg_prev_core_cfg_valid = dut.core_cfg_valid;
        dbg_prev_core_layer_st = dut.core_layer_st;
        dbg_prev_ln_start_pending = dut.u_core.ln_addr_gen.start_pending;
        dbg_prev_front_adapter_ready = (dut.u_core._layernorm_io_data_ready & dut.u_core._resadd_io_orig_ready);
        dbg_prev_ln_addr_state = dut.u_core.ln_addr_gen.state;
        dbg_prev_ln_data_valid = dut.u_core._ln_addr_gen_io_data_valid;
        dbg_prev_ln_state = dut.u_core.layernorm.state;
        dbg_prev_ln_ready = dut.u_core._layernorm_io_data_ready;
        dbg_prev_resadd_orig_ready = dut.u_core._resadd_io_orig_ready;
        dbg_prev_qkv_state = dut.u_core.qkvlinear.state;
        dbg_prev_resadd2_s7_ready = dut.u_core._resadd2_io_s7_ready;
        dbg_prev_resadd_reading = dut.u_core.resadd.state;
        dbg_prev_resadd2_reading = dut.u_core.resadd2.state;
      end
      if (ENABLE_DEEP_DEBUG &&
          (dut.run_token_idx == 16'd0) &&
          dut.u_core._ln_addr_gen_io_data_valid &&
          (dut.u_core._ln_addr_gen_io_data_addr < 11'd4)) begin
        $display(
            "LN1 feed cycle=%0d token=%0d ln_addr=%0d last=%0d adapter=%0d ln_rdy=%0d res1_orig_rdy=%0d",
            cycle,
            dut.run_token_idx,
            dut.u_core._ln_addr_gen_io_data_addr,
            dut.u_core._ln_addr_gen_io_data_last,
            (dut.u_core._layernorm_io_data_ready & dut.u_core._resadd_io_orig_ready),
            dut.u_core._layernorm_io_data_ready,
            dut.u_core._resadd_io_orig_ready
        );
      end
      if (ENABLE_DEEP_DEBUG &&
          (dut.run_token_idx == 16'd0) &&
          dut.u_core.resadd.io_orig_in_valid &&
          (dut.u_core.resadd.io_orig_in_addr < 11'd4)) begin
        $display(
            "ResAdd1 orig early cycle=%0d token=%0d addr=%0d last=%0d ready=%0d data=%h",
            cycle,
            dut.run_token_idx,
            dut.u_core.resadd.io_orig_in_addr,
            dut.u_core.resadd.io_orig_in_last,
            dut.u_core._resadd_io_orig_ready,
            dut.u_core.resadd.io_orig_in
        );
      end
      if (ENABLE_DEEP_DEBUG &&
          in_debug_token_window(dut.run_token_idx) &&
          dut.u_core._qkvlinear_io_data_out_last) begin
        $display(
            "QKV last cycle=%0d addr=%0d ready=%0d qkv_state=%0d",
            cycle,
            dut.u_core._qkvlinear_io_data_out_addr,
            dut.u_core._atten_io_data_ready,
            dut.u_core.qkvlinear.state
        );
      end
      if (ENABLE_DEEP_DEBUG &&
          in_debug_token_window(dut.run_token_idx) &&
          dut.u_core.atten.dm1.lu_inst.io_data_in_last) begin
        $display(
            "DM1 load-last cycle=%0d addr=%0d r_ready=%0d lu_state=%0d",
            cycle,
            dut.u_core.atten.dm1.lu_inst.io_data_in_addr,
            dut.u_core.atten.dm1.mem_inst.io_r_ready,
            dut.u_core.atten.dm1.lu_inst.state
        );
      end
      if (ENABLE_DEEP_DEBUG &&
          in_debug_token_window(dut.run_token_idx) &&
          dut.u_core.atten._dm1_io_res_valid) begin
        $display(
            "DM1 res cycle=%0d token=%0d addr=%0d last=%0d data=%h",
            cycle,
            dut.run_token_idx,
            dut.u_core.atten.dm1.io_res_addr,
            dut.u_core.atten.dm1.io_res_last,
            dut.u_core.atten.dm1.io_res
        );
      end
      if (ENABLE_DEEP_DEBUG &&
          in_debug_token_window(dut.run_token_idx) &&
          dut.u_core.atten._softmax_io_res_valid) begin
        $display(
            "Softmax res cycle=%0d token=%0d addr=%0d last=%0d ready=%0d data=%h",
            cycle,
            dut.run_token_idx,
            dut.u_core.atten.softmax.io_res_addr,
            dut.u_core.atten.softmax.io_res_last,
            dut.u_core.atten.ctxToDm2Q.io_enq_ready,
            dut.u_core.atten.softmax.io_res
        );
      end
      if (ENABLE_DEEP_DEBUG &&
          in_debug_token_window(dut.run_token_idx) &&
          dut.u_core.atten.vcache.io_data_in_valid) begin
        $display(
            "VCache in cycle=%0d token=%0d addr=%0d last=%0d ready=%0d data=%h wptr=%0d",
            cycle,
            dut.run_token_idx,
            dut.u_core.atten.vcache.io_data_in_addr,
            dut.u_core.atten.vcache.io_data_in_last,
            dut.u_core.atten._vcache_io_data_in_ready,
            dut.u_core.atten.vcache.io_data_in,
            dut.u_core.atten.vcache.mem_inst.w_ptr
        );
      end
      if (ENABLE_DEEP_DEBUG &&
          in_debug_token_window(dut.run_token_idx) &&
          dut.u_core.atten._vcache_io_res_valid) begin
        $display(
            "VCache res cycle=%0d token=%0d addr=%0d last=%0d ready=%0d data=%h rptr=%0d wptr=%0d full=%0d busy=%0d req_addr=%0d req_last=%0d req_en=%0d q_enq_v=%0d q_enq_r=%0d q_deq_v=%0d q_deq_r=%0d",
            cycle,
            dut.run_token_idx,
            dut.u_core.atten.vcache.io_res_addr,
            dut.u_core.atten.vcache.io_res_last,
            dut.u_core.atten.vToDm2Q.io_enq_ready,
            dut.u_core.atten.vcache.io_res,
            dut.u_core.atten.vcache.mem_inst.r_ptr,
            dut.u_core.atten.vcache.mem_inst.w_ptr,
            dut.u_core.atten.vcache.mem_inst.full_cnt,
            dut.u_core.atten.vcache.mem_inst.buzy_cnt,
            dut.u_core.atten.vcache.lsu_inst.io_data_in_addr,
            dut.u_core.atten.vcache.lsu_inst.io_data_in_last,
            dut.u_core.atten.vcache.lsu_inst.io_data_in_en,
            dut.u_core.atten.vToDm2Q.io_enq_valid,
            dut.u_core.atten.vToDm2Q.io_enq_ready,
            dut.u_core.atten.vToDm2Q.io_deq_valid,
            dut.u_core.atten.vToDm2Q.io_deq_ready
        );
      end
      if (ENABLE_DEEP_DEBUG &&
          in_debug_token_window(dut.run_token_idx) &&
          (dut.u_core.atten.vToDm2Q.io_enq_valid ||
           dut.u_core.atten.vToDm2Q.io_deq_valid ||
           dut.u_core.atten.dm1.io_res_valid ||
           dut.u_core.atten.softmax.io_res_valid ||
           dut.u_core.atten.input_fire ||
           dut.u_core.atten.softmax.io_layer_st ||
           dut.u_core.atten.softmax.io_data_in_st)) begin
        $display(
            "Attn mid cycle=%0d token=%0d in_v=%0d in_r=%0d fire=%0d sm_st=%0d sm_in_st=%0d dm1_v=%0d sm_v=%0d sm_r=%0d q_enq[v=%0d r=%0d a=%0d l=%0d] q_deq[v=%0d r=%0d a=%0d l=%0d] dm2v_r=%0d dm2c_r=%0d",
            cycle,
            dut.run_token_idx,
            dut.u_core.atten.io_data_valid,
            dut.u_core.atten.io_data_ready,
            dut.u_core.atten.input_fire,
            dut.u_core.atten.softmax.io_layer_st,
            dut.u_core.atten.softmax.io_data_in_st,
            dut.u_core.atten.dm1.io_res_valid,
            dut.u_core.atten.softmax.io_res_valid,
            dut.u_core.atten._dm2_io_data_in_ctx_ready,
            dut.u_core.atten.vToDm2Q.io_enq_valid,
            dut.u_core.atten.vToDm2Q.io_enq_ready,
            dut.u_core.atten.vToDm2Q.io_enq_bits_addr,
            dut.u_core.atten.vToDm2Q.io_enq_bits_last,
            dut.u_core.atten.vToDm2Q.io_deq_valid,
            dut.u_core.atten.vToDm2Q.io_deq_ready,
            dut.u_core.atten.vToDm2Q.io_deq_bits_addr,
            dut.u_core.atten.vToDm2Q.io_deq_bits_last,
            dut.u_core.atten._dm2_io_data_in_v_ready,
            dut.u_core.atten._dm2_io_data_in_ctx_ready
        );
      end
      if (ENABLE_DEEP_DEBUG &&
          in_debug_token_window(dut.run_token_idx) &&
          (dut.u_core.atten.dm2.loaduInst.io_data_out_ctx_valid ||
           dut.u_core.atten.dm2.loaduInst.io_data_out_v_valid)) begin
        $display(
            "DM2 in cycle=%0d token=%0d ctx=%0d v=%0d ctx_r=%0d v_r=%0d lu_state=%0d st=%0d gev=%0d waitctx=%0d mul=%0d batch=%0d vaddr=%0d caddr=%0d vmem[full=%0d busy=%0d wptr=%0d rptr=%0d] ctxmem[full=%0d busy=%0d wptr=%0d rptr=%0d]",
            cycle,
            dut.run_token_idx,
            dut.u_core.atten.dm2.loaduInst.io_data_out_ctx_valid,
            dut.u_core.atten.dm2.loaduInst.io_data_out_v_valid,
            dut.u_core.atten._dm2_io_data_in_ctx_ready,
            dut.u_core.atten._dm2_io_data_in_v_ready,
            dut.u_core.atten.dm2.loaduInst.state,
            dut.u_core.atten.dm2.dmInst.state,
            dut.u_core.atten.dm2.dmInst.gevCnt,
            dut.u_core.atten.dm2.dmInst.waitctxCnt,
            dut.u_core.atten.dm2.dmInst.mulCnt,
            dut.u_core.atten.dm2.dmInst.lbatchCnt,
            dut.u_core.atten.dm2.loaduInst.io_data_in_v_addr,
            dut.u_core.atten.dm2.loaduInst.io_data_in_ctx_addr,
            dut.u_core.atten.dm2.vmemInst.full_cnt,
            dut.u_core.atten.dm2.vmemInst.buzy_cnt,
            dut.u_core.atten.dm2.vmemInst.w_ptr,
            dut.u_core.atten.dm2.vmemInst.r_ptr,
            dut.u_core.atten.dm2.ctxmemInst.full_cnt,
            dut.u_core.atten.dm2.ctxmemInst.buzy_cnt,
            dut.u_core.atten.dm2.ctxmemInst.w_ptr,
            dut.u_core.atten.dm2.ctxmemInst.r_ptr
        );
      end
      if (ENABLE_DEEP_DEBUG &&
          in_debug_token_window(dut.run_token_idx) &&
          (dut.u_core.atten.dm2.loaduInst.io_data_in_v_ready !== dut.u_core.atten.dm2.loaduInst.io_data_in_ctx_ready ||
           dut.u_core.atten.dm2.vmemInst.io_r_ready !== dut.u_core.atten.dm2.ctxmemInst.io_r_ready ||
           dut.u_core.atten.dm2.vmemInst.full_cnt !== dut.u_core.atten.dm2.ctxmemInst.full_cnt ||
           dut.u_core.atten.dm2.vmemInst.buzy_cnt !== dut.u_core.atten.dm2.ctxmemInst.buzy_cnt)) begin
        $display(
            "DM2 mem skew cycle=%0d token=%0d lu_state=%0d v_r=%0d c_r=%0d vmem[wr=%0d rr=%0d full=%0d busy=%0d wptr=%0d rptr=%0d] ctxmem[wr=%0d rr=%0d full=%0d busy=%0d wptr=%0d rptr=%0d]",
            cycle,
            dut.run_token_idx,
            dut.u_core.atten.dm2.loaduInst.state,
            dut.u_core.atten.dm2.loaduInst.io_data_in_v_ready,
            dut.u_core.atten.dm2.loaduInst.io_data_in_ctx_ready,
            dut.u_core.atten.dm2.vmemInst.io_w_ready,
            dut.u_core.atten.dm2.vmemInst.io_r_ready,
            dut.u_core.atten.dm2.vmemInst.full_cnt,
            dut.u_core.atten.dm2.vmemInst.buzy_cnt,
            dut.u_core.atten.dm2.vmemInst.w_ptr,
            dut.u_core.atten.dm2.vmemInst.r_ptr,
            dut.u_core.atten.dm2.ctxmemInst.io_w_ready,
            dut.u_core.atten.dm2.ctxmemInst.io_r_ready,
            dut.u_core.atten.dm2.ctxmemInst.full_cnt,
            dut.u_core.atten.dm2.ctxmemInst.buzy_cnt,
            dut.u_core.atten.dm2.ctxmemInst.w_ptr,
            dut.u_core.atten.dm2.ctxmemInst.r_ptr
        );
      end
      if (ENABLE_DEEP_DEBUG &&
          in_debug_token_window(dut.run_token_idx) &&
          (dut.u_core.atten.dm2.dmInst.io_data_out_valid ||
           $isunknown(dut.u_core.atten.dm2.dmInst.io_data_out))) begin
        $display(
            "DM2 core cycle=%0d token=%0d state=%0d gev=%0d waitctx=%0d mul=%0d lbatch=%0d prefillLoad=%0d ctx_v=%0d v_v=%0d ctx_head=%h out=%h",
            cycle,
            dut.run_token_idx,
            dut.u_core.atten.dm2.dmInst.state,
            dut.u_core.atten.dm2.dmInst.gevCnt,
            dut.u_core.atten.dm2.dmInst.waitctxCnt,
            dut.u_core.atten.dm2.dmInst.mulCnt,
            dut.u_core.atten.dm2.dmInst.lbatchCnt,
            dut.u_core.atten.dm2.dmInst.prefillLoadCnt,
            dut.u_core.atten.dm2.dmInst.io_data_in_ctx_valid,
            dut.u_core.atten.dm2.dmInst.io_data_in_v_valid,
            dut.u_core.atten.dm2.dmInst.ctx[7:0],
            dut.u_core.atten.dm2.dmInst.io_data_out
        );
      end
      if (ENABLE_DEEP_DEBUG &&
          in_debug_token_window(dut.run_token_idx) &&
          (dut.u_core.atten.dm2.dmInst.io_data_out_valid || dut.u_core.atten.dm2.io_res_valid)) begin
        $display(
            "DM2 res cycle=%0d token=%0d cu=%0d su=%0d addr=%0d last=%0d data=%h",
            cycle,
            dut.run_token_idx,
            dut.u_core.atten.dm2.dmInst.io_data_out_valid,
            dut.u_core.atten.dm2.io_res_valid,
            dut.u_core.atten.dm2.io_res_addr,
            dut.u_core.atten.dm2.io_res_last,
            dut.u_core.atten.dm2.io_res
        );
      end
      if (ENABLE_DEEP_DEBUG &&
          in_debug_token_window(dut.run_token_idx) &&
          dut.u_core._atten_io_res_valid &&
          in_debug_addr_window(dut.u_core.atten.io_res_addr)) begin
        $display(
            "Attn out cycle=%0d token=%0d addr=%0d last=%0d ready=%0d data=%h",
            cycle,
            dut.run_token_idx,
            dut.u_core.atten.io_res_addr,
            dut.u_core.atten.io_res_last,
            dut.u_core.outlinear.io_data_ready,
            dut.u_core.atten.io_res
        );
      end
      if (ENABLE_DEEP_DEBUG &&
          dut.u_core.outlinear.io_bias_init_valid &&
          (dut.u_core.outlinear.bias_init_cnt >= 6'd33) &&
          (dut.u_core.outlinear.bias_init_cnt <= 6'd35)) begin
        $display(
            "OutLinear bias init cycle=%0d cnt=%0d data=%h",
            cycle,
            dut.u_core.outlinear.bias_init_cnt,
            dut.u_core.outlinear.io_bias_init_data
        );
      end
      if (ENABLE_DEEP_DEBUG &&
          in_debug_token_window(dut.run_token_idx) &&
          dut.u_core._outlinear_io_data_out_valid &&
          in_debug_addr_window(dut.u_core.outlinear.io_data_out_addr)) begin
        $display(
            "OutLinear out cycle=%0d token=%0d addr=%0d last=%0d data=%h raw=%h bias34=%h",
            cycle,
            dut.run_token_idx,
            dut.u_core.outlinear.io_data_out_addr,
            dut.u_core.outlinear.io_data_out_last,
            dut.u_core.outlinear.io_data_out,
            dut.u_core.outlinear.su_inst.io_data_out,
            dut.u_core.outlinear.bias_mem_34
        );
      end
      if (ENABLE_DEEP_DEBUG &&
          in_debug_token_window(dut.run_token_idx) &&
          dut.u_core.outToResQ.io_enq_valid &&
          in_debug_addr_window(dut.u_core.outToResQ.io_enq_bits_addr)) begin
        $display(
            "ResAdd1 dm2 enq cycle=%0d token=%0d addr=%0d last=%0d ready=%0d enq_ptr=%0d deq_ptr=%0d maybe_full=%0d data=%h",
            cycle,
            dut.run_token_idx,
            dut.u_core.outToResQ.io_enq_bits_addr,
            dut.u_core.outToResQ.io_enq_bits_last,
            dut.u_core.outToResQ.io_enq_ready,
            dut.u_core.outToResQ.enq_ptr_value,
            dut.u_core.outToResQ.deq_ptr_value,
            dut.u_core.outToResQ.maybe_full,
            dut.u_core.outToResQ.io_enq_bits_data
        );
      end
      if (ENABLE_DEEP_DEBUG &&
          in_debug_token_window(dut.run_token_idx) &&
          dut.u_core.resadd.io_orig_in_valid &&
          in_debug_addr_window(dut.u_core.resadd.io_orig_in_addr)) begin
        $display(
            "ResAdd1 orig write cycle=%0d token=%0d addr=%0d last=%0d ready=%0d data=%h",
            cycle,
            dut.run_token_idx,
            dut.u_core.resadd.io_orig_in_addr,
            dut.u_core.resadd.io_orig_in_last,
            dut.u_core.resadd.io_orig_ready,
            dut.u_core.resadd.io_orig_in
        );
      end
      if (ENABLE_DEEP_DEBUG &&
          in_debug_token_window(dut.run_token_idx) &&
          dut.u_core._outToResQ_io_deq_valid && dut.u_core._resadd_io_dm2_ready &&
          in_debug_addr_window(dut.u_core._outToResQ_io_deq_bits_addr)) begin
        $display(
            "ResAdd1 dm2 load cycle=%0d token=%0d addr=%0d last=%0d enq_ptr=%0d deq_ptr=%0d maybe_full=%0d data=%h",
            cycle,
            dut.run_token_idx,
            dut.u_core._outToResQ_io_deq_bits_addr,
            dut.u_core._outToResQ_io_deq_bits_last,
            dut.u_core.outToResQ.enq_ptr_value,
            dut.u_core.outToResQ.deq_ptr_value,
            dut.u_core.outToResQ.maybe_full,
            dut.u_core._outToResQ_io_deq_bits_data
        );
      end
      if (ENABLE_DEEP_DEBUG &&
          in_debug_token_window(dut.run_token_idx) &&
          (dut.u_core.layernorm2.state != dbg_prev_ln2_state)) begin
        $display(
            "LN2 state cycle=%0d token=%0d state=%0d tokenIdx=%0d vecIdx=%0d statValid=%0d sum=%h sq=%h mean=%h var=%h sqrt_rdy=%0d sqrt_v=%0d",
            cycle,
            dut.run_token_idx,
            dut.u_core.layernorm2.state,
            dut.u_core.layernorm2.tokenIdx,
            dut.u_core.layernorm2.vecIdx,
            dut.u_core.layernorm2.statValid,
            dut.u_core.layernorm2.sumAcc,
            dut.u_core.layernorm2.sqSumAcc,
            dut.u_core.layernorm2.meanReg,
            dut.u_core.layernorm2.varReg,
            dut.u_core.layernorm2.sqrt.io_inReady,
            dut.u_core.layernorm2.sqrt.io_outValidSqrt
        );
        dbg_prev_ln2_state = dut.u_core.layernorm2.state;
      end
      if (ENABLE_DEEP_DEBUG &&
          in_debug_token_window(dut.run_token_idx) &&
          dut.u_core._resadd_io_res_valid &&
          in_debug_addr_window(dut.u_core.resadd.io_res_addr)) begin
        $display(
            "ResAdd1 out cycle=%0d token=%0d addr=%0d last=%0d data=%h orig=%h dm2=%h",
            cycle,
            dut.run_token_idx,
            dut.u_core.resadd.io_res_addr,
            dut.u_core.resadd.io_res_last,
            dut.u_core.resadd.io_res,
            dut.u_core.resadd.mem.io_r_data,
            dut.u_core.resadd.dm2_data_r
        );
      end
      if (ENABLE_DEEP_DEBUG &&
          in_debug_token_window(dut.run_token_idx) && dut.u_core.layernorm2.statValid) begin
        $display(
            "LN2 stat cycle=%0d token=%0d tokenIdx=%0d vecIdx=%0d statFirst=%0d statLast=%0d sum=%h sq=%h lane=%h lane_sq=%h",
            cycle,
            dut.run_token_idx,
            dut.u_core.layernorm2.tokenIdx,
            dut.u_core.layernorm2.vecIdx,
            dut.u_core.layernorm2.statFirst,
            dut.u_core.layernorm2.statLast,
            dut.u_core.layernorm2.sumAcc,
            dut.u_core.layernorm2.sqSumAcc,
            dut.u_core.layernorm2._laneSum_io_out,
            dut.u_core.layernorm2._laneSqSum_io_out
        );
      end
      if (ENABLE_DEEP_DEBUG &&
          in_debug_token_window(dut.run_token_idx) && dut.u_core._layernorm2_io_res_valid) begin
        $display(
            "LN2 out cycle=%0d token=%0d addr=%0d last=%0d data=%h",
            cycle,
            dut.run_token_idx,
            dut.u_core.layernorm2.io_res_addr,
            dut.u_core.layernorm2.io_res_last,
            dut.u_core.layernorm2.io_res
        );
      end
      if (ENABLE_DEEP_DEBUG &&
          in_debug_token_window(dut.run_token_idx) &&
          in_debug_addr_window(dut.u_core.ffnup.io_data_out_addr) &&
          dut.u_core._ffnup_io_data_out_valid) begin
        $display(
            "FFNUp out cycle=%0d token=%0d addr=%0d last=%0d data=%h",
            cycle,
            dut.run_token_idx,
            dut.u_core.ffnup.io_data_out_addr,
            dut.u_core.ffnup.io_data_out_last,
            dut.u_core.ffnup.io_data_out
        );
      end
      if (ENABLE_DEEP_DEBUG &&
          in_debug_token_window(dut.run_token_idx) &&
          in_debug_addr_window(dut.u_core.ffndown.io_data_out_addr) &&
          dut.u_core._ffndown_io_data_out_valid) begin
        $display(
            "FFNDown out cycle=%0d token=%0d addr=%0d last=%0d data=%h",
            cycle,
            dut.run_token_idx,
            dut.u_core.ffndown.io_data_out_addr,
            dut.u_core.ffndown.io_data_out_last,
            dut.u_core.ffndown.io_data_out
        );
      end
      if (ENABLE_DEEP_DEBUG &&
          in_debug_token_window(dut.run_token_idx) &&
          in_debug_addr_window(dut.u_core._resadd_io_res_addr) &&
          dut.u_core._resadd_io_res_valid) begin
        $display(
            "ResAdd2 s7 in cycle=%0d token=%0d addr=%0d last=%0d data=%h",
            cycle,
            dut.run_token_idx,
            dut.u_core._resadd_io_res_addr,
            dut.u_core._resadd_io_res_last,
            dut.u_core._resadd_io_res
        );
      end
      if (ENABLE_DEEP_DEBUG &&
          in_debug_token_window(dut.run_token_idx) && dut.u_core.io_res_valid) begin
        $display(
            "Top out cycle=%0d token=%0d addr=%0d last=%0d st=%0d data=%h",
            cycle,
            dut.run_token_idx,
            dut.u_core.io_res_addr,
            dut.u_core.io_res_last,
            dut.u_core.io_res_st,
            dut.u_core.io_res
        );
      end
      if (ENABLE_DEEP_DEBUG &&
          !dbg_ln2_x_reported &&
          (dut.run_token_idx == DEBUG_TOKEN_START) && $isunknown(dut.u_core.layernorm2.varReg)) begin
        $display(
            "LN2 X cycle=%0d token=%0d state=%0d inputLoaded=%0d weightsLoaded=%0d tokenCount=%0d tokenIdx=%0d vecIdx=%0d statValid=%0d sum=%h sq=%h mean=%h var=%h sqrt_rdy=%0d sqrt_v=%0d",
            cycle,
            dut.run_token_idx,
            dut.u_core.layernorm2.state,
            dut.u_core.layernorm2.inputLoaded,
            dut.u_core.layernorm2.weightsLoaded,
            dut.u_core.layernorm2.tokenCount,
            dut.u_core.layernorm2.tokenIdx,
            dut.u_core.layernorm2.vecIdx,
            dut.u_core.layernorm2.statValid,
            dut.u_core.layernorm2.sumAcc,
            dut.u_core.layernorm2.sqSumAcc,
            dut.u_core.layernorm2.meanReg,
            dut.u_core.layernorm2.varReg,
            dut.u_core.layernorm2.sqrt.io_inReady,
            dut.u_core.layernorm2.sqrt.io_outValidSqrt
        );
        dbg_ln2_x_reported = 1'b1;
      end
    end

    if (seen_count != golden_beats) begin
      int miss_printed;
      int beat_idx_dbg;
      miss_printed = 0;
      for (beat_idx_dbg = 0; beat_idx_dbg < golden_beats; beat_idx_dbg++) begin
        if (!seen[beat_idx_dbg] && (miss_printed < 32)) begin
          $display(
              "Missing beat summary beat=%0d token=%0d lane_addr=%0d",
              beat_idx_dbg,
              beat_idx_dbg / 64,
              beat_idx_dbg % 64
          );
          miss_printed = miss_printed + 1;
        end
      end
      fatal_msg($sformatf("missing NinePSystemTop output beats seen=%0d expected=%0d", seen_count, golden_beats));
    end
    check_outputs();
    $finish;
  end

  always @(negedge clock) begin
    if (reset) begin
      io_ddr_rd_data <= '0;
      io_ddr_rd_data_valid <= 1'b0;
      io_ddr_rd_data_end <= 1'b0;
      for (idx = 0; idx < DDR_LATENCY; idx++) begin
        pending_valid[idx] <= 1'b0;
        pending_addr[idx] <= '0;
      end
    end else begin
      io_ddr_rd_data_valid <= pending_valid[DDR_LATENCY-1];
      io_ddr_rd_data_end <= pending_valid[DDR_LATENCY-1];
      io_ddr_rd_data <= '0;
      if (pending_valid[DDR_LATENCY-1]) begin
        if (pending_addr[DDR_LATENCY-1] >= ddr_beats) begin
          fatal_msg($sformatf("DDR read addr out of range: %0d >= %0d", pending_addr[DDR_LATENCY-1], ddr_beats));
        end
        for (word_idx = 0; word_idx < 16; word_idx++) begin
          io_ddr_rd_data[word_idx * 32 +: 32] <= ddr_image_words[pending_addr[DDR_LATENCY-1] * 16 + word_idx];
        end
      end

      for (idx = DDR_LATENCY - 1; idx > 0; idx--) begin
        pending_valid[idx] <= pending_valid[idx - 1];
        pending_addr[idx] <= pending_addr[idx - 1];
      end
      pending_valid[0] <= io_ddr_en && io_ddr_rdy && (io_ddr_cmd == 3'b001);
      pending_addr[0] <= io_ddr_addr;
    end
  end

  always @(posedge clock) begin
    if (!reset && io_res_valid) begin
      if (io_res_addr >= golden_beats) begin
        fatal_msg($sformatf("NinePSystemTop output addr out of range: %0d >= %0d", io_res_addr, golden_beats));
      end
      if (seen[io_res_addr]) begin
        $display(
            "Duplicate top beat cycle=%0d beat=%0d token=%0d lane_addr=%0d last=%0d data=%h",
            cycle,
            io_res_addr,
            io_res_addr / 64,
            io_res_addr % 64,
            io_res_last,
            io_res
        );
      end
      if (!seen[io_res_addr]) begin
        seen[io_res_addr] <= 1'b1;
        seen_count <= seen_count + 1;
      end
      for (idx = 0; idx < 12; idx++) begin
        observed_words[io_res_addr * 12 + idx] <= io_res[idx * 32 +: 32];
      end
      saw_st <= saw_st || io_res_st;
      saw_last <= saw_last || io_res_last;
    end
  end

endmodule
