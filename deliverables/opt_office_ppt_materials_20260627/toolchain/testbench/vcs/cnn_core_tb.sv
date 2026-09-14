`timescale 1ns/1ps

`ifdef USE_OPT_ACC_CORE
  `define DUT_MODULE opt_acc_core
  `define DUT_LABEL  "opt_acc_core"
`else
  `define DUT_MODULE cnn_core
  `define DUT_LABEL  "cnn_core"
`endif

module cnn_core_tb;

  localparam int NUM_LAYERS = 12;
  localparam longint unsigned C0_BASE_ADDR = 64'h0000_0008_0000_0000;
  localparam int READ_ADDR_LATENCY = 12;
  localparam int WRITE_RESP_LATENCY = 8;
  localparam longint unsigned MAX_CYCLES = 64'd12000000000;
  localparam int MAX_DDR_BEATS = 300000;
  localparam int MAX_OUTPUT_BEATS = 65536;
  localparam int MAX_DDR_WORDS = MAX_DDR_BEATS * 16;
  localparam int MAX_GOLDEN_WORDS = MAX_OUTPUT_BEATS * 12;
  localparam int MAX_MEM_WORDS = (MAX_DDR_BEATS + MAX_OUTPUT_BEATS + 4096) * 16;
  localparam longint unsigned PROGRESS_CYCLES = 64'd10000000;

  logic c0_ddr4_s_axi_clk = 1'b0;
  logic clk_300M = 1'b0;
  logic clk_600M = 1'b0;
  logic c0_ddr4_s_axi_rst_n = 1'b0;
  logic c0_init_calib_complete = 1'b0;
  logic sys_rst_n = 1'b0;
  logic user_rst = 1'b1;

  logic [703:0] cfg_data = '0;
  logic cfg_data_valid = 1'b0;
  logic cfg_done = 1'b0;
  logic cnn0_input_batch_set = 1'b0;
  wire [2:0] cnn0_batch_count;
  logic cnn0_result_batch_clear = 1'b0;
  wire [2:0] cnn0_result_count;

  wire [3:0]    c0_ddr4_s_axi_awid;
  wire [36:0]   c0_ddr4_s_axi_awaddr;
  wire [7:0]    c0_ddr4_s_axi_awlen;
  wire [2:0]    c0_ddr4_s_axi_awsize;
  wire [1:0]    c0_ddr4_s_axi_awburst;
  wire          c0_ddr4_s_axi_awlock;
  wire [3:0]    c0_ddr4_s_axi_awcache;
  wire [2:0]    c0_ddr4_s_axi_awprot;
  wire          c0_ddr4_s_axi_awvalid;
  logic         c0_ddr4_s_axi_awready = 1'b0;
  wire [511:0]  c0_ddr4_s_axi_wdata;
  wire [63:0]   c0_ddr4_s_axi_wstrb;
  wire          c0_ddr4_s_axi_wlast;
  wire          c0_ddr4_s_axi_wvalid;
  logic         c0_ddr4_s_axi_wready = 1'b0;
  wire          c0_ddr4_s_axi_bready;
  logic [3:0]   c0_ddr4_s_axi_bid = 4'd0;
  logic [1:0]   c0_ddr4_s_axi_bresp = 2'b00;
  logic         c0_ddr4_s_axi_bvalid = 1'b0;
  wire [3:0]    c0_ddr4_s_axi_arid;
  wire [36:0]   c0_ddr4_s_axi_araddr;
  wire [7:0]    c0_ddr4_s_axi_arlen;
  wire [2:0]    c0_ddr4_s_axi_arsize;
  wire [1:0]    c0_ddr4_s_axi_arburst;
  wire          c0_ddr4_s_axi_arlock;
  wire [3:0]    c0_ddr4_s_axi_arcache;
  wire [2:0]    c0_ddr4_s_axi_arprot;
  wire          c0_ddr4_s_axi_arvalid;
  logic         c0_ddr4_s_axi_arready = 1'b0;
  wire          c0_ddr4_s_axi_rready;
  logic         c0_ddr4_s_axi_rlast = 1'b0;
  logic         c0_ddr4_s_axi_rvalid = 1'b0;
  logic [1:0]   c0_ddr4_s_axi_rresp = 2'b00;
  logic [3:0]   c0_ddr4_s_axi_rid = 4'd0;
  logic [511:0] c0_ddr4_s_axi_rdata = '0;

  logic [31:0] ddr_image_words [0:MAX_DDR_WORDS-1];
  logic [31:0] golden_words [0:MAX_GOLDEN_WORDS-1];
  logic [31:0] mem_words [0:MAX_MEM_WORDS-1];
  bit seen [0:MAX_OUTPUT_BEATS-1];

  string window_dir;
  string cfg_path;
  string ddr_path;
  string golden_path;
  integer trace_fd;

  integer ddr_word_count;
  integer golden_word_count;
  integer golden_beats;
  integer input_beats_cfg;
  integer output_beats_cfg;
  longint unsigned output_base_addr_u64;
  longint unsigned output_stride_bytes_u64;
  longint unsigned input_base_addr_u64;
  longint unsigned cycle;
  integer cycle_mod;
  integer idx;
  integer progress_count;
  bit tb_debug_enable;
  integer debug_event_count;
  integer stage_event_count;
  integer qkv_stage_event_count;
  integer token3_qkv_event_count;
  integer token3_attn_in_event_count;
  integer token1_focus_event_count;
  integer token1_qkv_collect_event_count;
  integer token2_front_event_count;
  integer out_token1_event_count;
  integer out_cu_event_count;
  integer out_lu_trace_count;
  integer out_lu_vec22_trace_count;
  integer token1_resadd_event_count;
  integer outlinear_live_event_count;
  integer out_psum_event_count;
  integer out_headbuf_event_count;
  integer out_capture_event_count;
  integer out_queue_event_count;
  integer dm2_event_count;
  integer dm1_event_count;
  integer dm1_override_event_count;
  integer tap_trace_count;
  integer hist_write_trace_count;
  integer hist_read_trace_count;
  integer token3_out_event_count;
  integer outlinear_feed_count;
  integer outlinear_collect_count;
  integer lnq_stat_event_count;
  longint unsigned run_entry_cycle;
  logic [4:0] prev_dut_state;
  logic [1:0] prev_outlinear_state;
  logic [3:0] prev_lnq_state;
  logic prev_lnq_stat_read_en;
  logic prev_lnq_stat_valid;
  logic prev_lnq_stat_first;
  logic prev_lnq_stat_last;
  logic out_lu_vec22_trace_active;

  function automatic bit runtime_debug_window;
    input [4:0] state_value;
    begin
      runtime_debug_window = tb_debug_enable && (state_value == 5'd23);
    end
  endfunction

  integer cfg_seqlen_i;
  integer parsed_int;
  longint unsigned parsed_u64;
  integer dummy_int;
  logic [31:0] ln1_out_inv_scale_u32;
  logic signed [7:0] ln1_out_zero_point_s8;
  logic [31:0] q_out_inv_scale_u32;
  logic [31:0] k_out_inv_scale_u32;
  logic [31:0] v_out_inv_scale_u32;
  logic [31:0] q_bias_scale_u32;
  logic [31:0] k_bias_scale_u32;
  logic [31:0] v_bias_scale_u32;
  logic [31:0] dm1_out_scale_u32;
  logic [31:0] dm2_ctx_inv_scale_u32;
  logic [7:0]  dm2_ctx_zero_point_u8;
  logic [31:0] dm2_out_inv_scale_u32;
  logic [31:0] out_out_scale_u32;
  logic [31:0] ln2_out_inv_scale_u32;
  logic signed [7:0] ln2_out_zero_point_s8;
  logic [31:0] ffnup_out_inv_scale_u32;
  logic [31:0] ffnup_bias_scale_u32;
  logic [31:0] ffndown_out_scale_u32;

  bit rd_active;
  integer rd_latency;
  longint unsigned rd_addr;
  logic [3:0] rd_id;
  integer ar_hs_count;
  integer r_hs_count;

  bit wr_active;
  longint unsigned wr_addr;
  logic [3:0] wr_id;
  bit b_pending;
  integer b_latency;
  integer aw_hs_count;
  integer w_hs_count;
  integer b_emit_count;
  integer b_hs_count;

  `DUT_MODULE #(
    .ADDR_OFFSET_H(32'h00000008),
    .ADDR_OFFSET_L(32'h00000000),
    .NUM_LAYERS(NUM_LAYERS)
  ) dut (
    .clk_300M(clk_300M),
    .clk_600M(clk_600M),
    .cfg_data(cfg_data),
    .cfg_data_valid(cfg_data_valid),
    .cfg_done(cfg_done),
    .cnn0_input_batch_set(cnn0_input_batch_set),
    .cnn0_batch_count(cnn0_batch_count),
    .cnn0_result_batch_clear(cnn0_result_batch_clear),
    .cnn0_result_count(cnn0_result_count),
    .user_rst(user_rst),
    .c0_ddr4_s_axi_awid(c0_ddr4_s_axi_awid),
    .c0_ddr4_s_axi_awaddr(c0_ddr4_s_axi_awaddr),
    .c0_ddr4_s_axi_awlen(c0_ddr4_s_axi_awlen),
    .c0_ddr4_s_axi_awsize(c0_ddr4_s_axi_awsize),
    .c0_ddr4_s_axi_awburst(c0_ddr4_s_axi_awburst),
    .c0_ddr4_s_axi_awlock(c0_ddr4_s_axi_awlock),
    .c0_ddr4_s_axi_awcache(c0_ddr4_s_axi_awcache),
    .c0_ddr4_s_axi_awprot(c0_ddr4_s_axi_awprot),
    .c0_ddr4_s_axi_awvalid(c0_ddr4_s_axi_awvalid),
    .c0_ddr4_s_axi_awready(c0_ddr4_s_axi_awready),
    .c0_ddr4_s_axi_wdata(c0_ddr4_s_axi_wdata),
    .c0_ddr4_s_axi_wstrb(c0_ddr4_s_axi_wstrb),
    .c0_ddr4_s_axi_wlast(c0_ddr4_s_axi_wlast),
    .c0_ddr4_s_axi_wvalid(c0_ddr4_s_axi_wvalid),
    .c0_ddr4_s_axi_wready(c0_ddr4_s_axi_wready),
    .c0_ddr4_s_axi_bready(c0_ddr4_s_axi_bready),
    .c0_ddr4_s_axi_bid(c0_ddr4_s_axi_bid),
    .c0_ddr4_s_axi_bresp(c0_ddr4_s_axi_bresp),
    .c0_ddr4_s_axi_bvalid(c0_ddr4_s_axi_bvalid),
    .c0_ddr4_s_axi_arid(c0_ddr4_s_axi_arid),
    .c0_ddr4_s_axi_araddr(c0_ddr4_s_axi_araddr),
    .c0_ddr4_s_axi_arlen(c0_ddr4_s_axi_arlen),
    .c0_ddr4_s_axi_arsize(c0_ddr4_s_axi_arsize),
    .c0_ddr4_s_axi_arburst(c0_ddr4_s_axi_arburst),
    .c0_ddr4_s_axi_arlock(c0_ddr4_s_axi_arlock),
    .c0_ddr4_s_axi_arcache(c0_ddr4_s_axi_arcache),
    .c0_ddr4_s_axi_arprot(c0_ddr4_s_axi_arprot),
    .c0_ddr4_s_axi_arvalid(c0_ddr4_s_axi_arvalid),
    .c0_ddr4_s_axi_arready(c0_ddr4_s_axi_arready),
    .c0_ddr4_s_axi_rready(c0_ddr4_s_axi_rready),
    .c0_ddr4_s_axi_rlast(c0_ddr4_s_axi_rlast),
    .c0_ddr4_s_axi_rvalid(c0_ddr4_s_axi_rvalid),
    .c0_ddr4_s_axi_rresp(c0_ddr4_s_axi_rresp),
    .c0_ddr4_s_axi_rid(c0_ddr4_s_axi_rid),
    .c0_ddr4_s_axi_rdata(c0_ddr4_s_axi_rdata),
    .c0_ddr4_s_axi_clk(c0_ddr4_s_axi_clk),
    .c0_ddr4_s_axi_rst_n(c0_ddr4_s_axi_rst_n),
    .c0_init_calib_complete(c0_init_calib_complete),
    .sys_rst_n(sys_rst_n)
  );

  always #2.0 c0_ddr4_s_axi_clk = ~c0_ddr4_s_axi_clk;
  always #1.666 clk_300M = ~clk_300M;
  always #0.833 clk_600M = ~clk_600M;

  task automatic fatal_msg(input string msg);
    begin
      if (trace_fd != 0) begin
        $fdisplay(trace_fd, "FATAL_TRACE t=%0t msg=%s state=%h result_done=%b cfg_loaded=%b layer=%0d token=%0d",
                  $time, msg, dut.state, dut.result_done, dut.cfg_loaded, dut.layer_idx, dut.run_token_idx);
        $fflush(trace_fd);
      end
      $display("FATAL: %s", msg);
      $finish(1);
    end
  endtask

  task automatic wait_clk_edges(input integer edge_count);
    integer edge_idx;
    begin
      for (edge_idx = 0; edge_idx < edge_count; edge_idx = edge_idx + 1) begin
        @(posedge c0_ddr4_s_axi_clk);
        #0.001;
      end
    end
  endtask

  function automatic real abs_real(input real value);
    begin
      abs_real = (value < 0.0) ? -value : value;
    end
  endfunction

  function automatic integer mem_word_index(input longint unsigned addr);
    begin
      if (addr < C0_BASE_ADDR) fatal_msg($sformatf("address below C0 base: 0x%0h", addr));
      mem_word_index = (addr - C0_BASE_ADDR) >> 2;
      if (mem_word_index < 0 || mem_word_index >= MAX_MEM_WORDS)
        fatal_msg($sformatf("memory index out of range: addr=0x%0h idx=%0d", addr, mem_word_index));
    end
  endfunction

  function automatic logic [31:0] read_mem_word_abs(input longint unsigned addr);
    begin
      read_mem_word_abs = mem_words[mem_word_index(addr)];
    end
  endfunction

  task automatic load_words_from_bin(
      input string path,
      output logic [31:0] dest [0:MAX_DDR_WORDS-1],
      output integer word_count
  );
    integer fd;
    integer byte_count;
    integer read_count;
    begin
      fd = $fopen(path, "rb");
      if (fd == 0) fatal_msg($sformatf("failed to open binary: %s", path));
      byte_count = $fseek(fd, 0, 2);
      byte_count = $ftell(fd);
      if ($fseek(fd, 0, 0) != 0) fatal_msg($sformatf("failed to rewind binary: %s", path));
      if ((byte_count % 4) != 0) fatal_msg($sformatf("unexpected binary size: %s bytes=%0d", path, byte_count));
      word_count = byte_count / 4;
      if (word_count > MAX_DDR_WORDS) fatal_msg($sformatf("binary too large for buffer: %s words=%0d", path, word_count));
      for (idx = 0; idx < MAX_DDR_WORDS; idx++) dest[idx] = 32'd0;
      read_count = $fread(dest, fd);
      if (read_count != byte_count) fatal_msg($sformatf("short read on binary: %s got=%0d expect=%0d", path, read_count, byte_count));
      $fclose(fd);
    end
  endtask

  task automatic load_golden_from_bin(
      input string path,
      output logic [31:0] dest [0:MAX_GOLDEN_WORDS-1],
      output integer word_count
  );
    integer fd;
    integer byte_count;
    integer read_count;
    begin
      fd = $fopen(path, "rb");
      if (fd == 0) fatal_msg($sformatf("failed to open binary: %s", path));
      byte_count = $fseek(fd, 0, 2);
      byte_count = $ftell(fd);
      if ($fseek(fd, 0, 0) != 0) fatal_msg($sformatf("failed to rewind binary: %s", path));
      if ((byte_count % 4) != 0) fatal_msg($sformatf("unexpected binary size: %s bytes=%0d", path, byte_count));
      word_count = byte_count / 4;
      if (word_count > MAX_GOLDEN_WORDS) fatal_msg($sformatf("golden too large for buffer: %s words=%0d", path, word_count));
      for (idx = 0; idx < MAX_GOLDEN_WORDS; idx++) dest[idx] = 32'd0;
      read_count = $fread(dest, fd);
      if (read_count != byte_count) fatal_msg($sformatf("short read on binary: %s got=%0d expect=%0d", path, read_count, byte_count));
      $fclose(fd);
    end
  endtask

  task automatic load_window_cfg(input string path);
    integer fd;
    longint unsigned rel_window_base;
    longint unsigned rel_output_base;
    begin
      fd = $fopen(path, "r");
      if (fd == 0) fatal_msg($sformatf("failed to open cfg: %s", path));
      if ($fscanf(fd, "cfg_seqlen=%d\n", cfg_seqlen_i) != 1) fatal_msg("parse cfg_seqlen failed");
      if ($fscanf(fd, "input_beats=%d\n", input_beats_cfg) != 1) fatal_msg("parse input_beats failed");
      if ($fscanf(fd, "output_beats=%d\n", output_beats_cfg) != 1) fatal_msg("parse output_beats failed");
      if ($fscanf(fd, "ln1_out_inv_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse ln1_out_inv_scale failed"); ln1_out_inv_scale_u32 = parsed_int[31:0];
      if ($fscanf(fd, "ln1_out_zero_point_s8=%d\n", parsed_int) != 1) fatal_msg("parse ln1_out_zero_point failed"); ln1_out_zero_point_s8 = parsed_int[7:0];
      if ($fscanf(fd, "q_out_inv_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse q_out_inv_scale failed"); q_out_inv_scale_u32 = parsed_int[31:0];
      if ($fscanf(fd, "k_out_inv_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse k_out_inv_scale failed"); k_out_inv_scale_u32 = parsed_int[31:0];
      if ($fscanf(fd, "v_out_inv_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse v_out_inv_scale failed"); v_out_inv_scale_u32 = parsed_int[31:0];
      if ($fscanf(fd, "q_bias_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse q_bias_scale failed"); q_bias_scale_u32 = parsed_int[31:0];
      if ($fscanf(fd, "k_bias_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse k_bias_scale failed"); k_bias_scale_u32 = parsed_int[31:0];
      if ($fscanf(fd, "v_bias_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse v_bias_scale failed"); v_bias_scale_u32 = parsed_int[31:0];
      if ($fscanf(fd, "dm1_out_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse dm1_out_scale failed"); dm1_out_scale_u32 = parsed_int[31:0];
      if ($fscanf(fd, "dm2_ctx_inv_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse dm2_ctx_inv_scale failed"); dm2_ctx_inv_scale_u32 = parsed_int[31:0];
      if ($fscanf(fd, "dm2_ctx_zero_point_u8=%d\n", parsed_int) != 1) fatal_msg("parse dm2_ctx_zero_point failed"); dm2_ctx_zero_point_u8 = parsed_int[7:0];
      if ($fscanf(fd, "dm2_out_inv_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse dm2_out_inv_scale failed"); dm2_out_inv_scale_u32 = parsed_int[31:0];
      if ($fscanf(fd, "out_out_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse out_out_scale failed"); out_out_scale_u32 = parsed_int[31:0];
      if ($fscanf(fd, "ln2_out_inv_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse ln2_out_inv_scale failed"); ln2_out_inv_scale_u32 = parsed_int[31:0];
      if ($fscanf(fd, "ln2_out_zero_point_s8=%d\n", parsed_int) != 1) fatal_msg("parse ln2_out_zero_point failed"); ln2_out_zero_point_s8 = parsed_int[7:0];
      if ($fscanf(fd, "ffnup_out_inv_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse ffnup_out_inv_scale failed"); ffnup_out_inv_scale_u32 = parsed_int[31:0];
      if ($fscanf(fd, "ffnup_bias_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse ffnup_bias_scale failed"); ffnup_bias_scale_u32 = parsed_int[31:0];
      if ($fscanf(fd, "ffndown_out_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse ffndown_out_scale failed"); ffndown_out_scale_u32 = parsed_int[31:0];

      if ($fscanf(fd, "ddr_input_base_addr=%d\n", dummy_int) != 1) fatal_msg("parse ddr_input_base_addr failed");
      if ($fscanf(fd, "ddr_ln1_w_base_addr=%d\n", dummy_int) != 1) fatal_msg("parse ddr_ln1_w_base_addr failed");
      if ($fscanf(fd, "ddr_qkv_w_base_addr=%d\n", dummy_int) != 1) fatal_msg("parse ddr_qkv_w_base_addr failed");
      if ($fscanf(fd, "ddr_qkv_b_base_addr=%d\n", dummy_int) != 1) fatal_msg("parse ddr_qkv_b_base_addr failed");
      if ($fscanf(fd, "ddr_sm_base_addr=%d\n", dummy_int) != 1) fatal_msg("parse ddr_sm_base_addr failed");
      if ($fscanf(fd, "ddr_out_w_base_addr=%d\n", dummy_int) != 1) fatal_msg("parse ddr_out_w_base_addr failed");
      if ($fscanf(fd, "ddr_out_b_base_addr=%d\n", dummy_int) != 1) fatal_msg("parse ddr_out_b_base_addr failed");
      if ($fscanf(fd, "ddr_ln2_w_base_addr=%d\n", dummy_int) != 1) fatal_msg("parse ddr_ln2_w_base_addr failed");
      if ($fscanf(fd, "ddr_ffnup_w_base_addr=%d\n", dummy_int) != 1) fatal_msg("parse ddr_ffnup_w_base_addr failed");
      if ($fscanf(fd, "ddr_ffnup_b_base_addr=%d\n", dummy_int) != 1) fatal_msg("parse ddr_ffnup_b_base_addr failed");
      if ($fscanf(fd, "ddr_ffndown_w_base_addr=%d\n", dummy_int) != 1) fatal_msg("parse ddr_ffndown_w_base_addr failed");
      if ($fscanf(fd, "ddr_ffndown_b_base_addr=%d\n", dummy_int) != 1) fatal_msg("parse ddr_ffndown_b_base_addr failed");
      if ($fscanf(fd, "axi_c0_window_base_addr=%d\n", parsed_u64) != 1) fatal_msg("parse axi_c0_window_base_addr failed");
      if ($fscanf(fd, "axi_c1_window_base_addr=%d\n", parsed_u64) != 1) fatal_msg("parse axi_c1_window_base_addr failed");
      if ($fscanf(fd, "axi_data_bytes=%d\n", dummy_int) != 1) fatal_msg("parse axi_data_bytes failed");
      if ($fscanf(fd, "axi_line_bytes=%d\n", dummy_int) != 1) fatal_msg("parse axi_line_bytes failed");
      if ($fscanf(fd, "axi_input_base_addr=%d\n", parsed_u64) != 1) fatal_msg("parse axi_input_base_addr failed");
      if ($fscanf(fd, "axi_ln1_w_base_addr=%d\n", parsed_u64) != 1) fatal_msg("parse axi_ln1_w_base_addr failed");
      if ($fscanf(fd, "axi_qkv_w_base_addr=%d\n", parsed_u64) != 1) fatal_msg("parse axi_qkv_w_base_addr failed");
      if ($fscanf(fd, "axi_qkv_b_base_addr=%d\n", parsed_u64) != 1) fatal_msg("parse axi_qkv_b_base_addr failed");
      if ($fscanf(fd, "axi_sm_base_addr=%d\n", parsed_u64) != 1) fatal_msg("parse axi_sm_base_addr failed");
      if ($fscanf(fd, "axi_out_w_base_addr=%d\n", parsed_u64) != 1) fatal_msg("parse axi_out_w_base_addr failed");
      if ($fscanf(fd, "axi_out_b_base_addr=%d\n", parsed_u64) != 1) fatal_msg("parse axi_out_b_base_addr failed");
      if ($fscanf(fd, "axi_ln2_w_base_addr=%d\n", parsed_u64) != 1) fatal_msg("parse axi_ln2_w_base_addr failed");
      if ($fscanf(fd, "axi_ffnup_w_base_addr=%d\n", parsed_u64) != 1) fatal_msg("parse axi_ffnup_w_base_addr failed");
      if ($fscanf(fd, "axi_ffnup_b_base_addr=%d\n", parsed_u64) != 1) fatal_msg("parse axi_ffnup_b_base_addr failed");
      if ($fscanf(fd, "axi_ffndown_w_base_addr=%d\n", parsed_u64) != 1) fatal_msg("parse axi_ffndown_w_base_addr failed");
      if ($fscanf(fd, "axi_ffndown_b_base_addr=%d\n", parsed_u64) != 1) fatal_msg("parse axi_ffndown_b_base_addr failed");
      if ($fscanf(fd, "axi_output_base_addr=%d\n", parsed_u64) != 1) fatal_msg("parse axi_output_base_addr failed");
      if ($fscanf(fd, "axi_output_stride_bytes=%d\n", parsed_u64) != 1) fatal_msg("parse axi_output_stride_bytes failed"); output_stride_bytes_u64 = parsed_u64;
      $fclose(fd);
    end
  endtask

  task automatic pack_cfg_data;
    longint unsigned rel_window_base;
    longint unsigned rel_output_base;
    begin
      rel_window_base = input_base_addr_u64 - C0_BASE_ADDR;
      rel_output_base = output_base_addr_u64 - C0_BASE_ADDR;
      cfg_data = '0;
      cfg_data[0*32 +: 32] = cfg_seqlen_i[31:0];
      cfg_data[1*32 +: 32] = output_stride_bytes_u64[31:0];
      cfg_data[2*32 +: 32] = rel_window_base[31:0];
      cfg_data[3*32 +: 32] = rel_window_base[63:32];
      cfg_data[4*32 +: 32] = rel_output_base[31:0];
      cfg_data[5*32 +: 32] = rel_output_base[63:32];
      cfg_data[6*32 +: 8] = ln1_out_zero_point_s8[7:0];
      cfg_data[6*32 + 8 +: 8] = dm2_ctx_zero_point_u8;
      cfg_data[6*32 + 16 +: 8] = ln2_out_zero_point_s8[7:0];
      cfg_data[7*32 +: 32] = ln1_out_inv_scale_u32;
      cfg_data[8*32 +: 32] = q_out_inv_scale_u32;
      cfg_data[9*32 +: 32] = k_out_inv_scale_u32;
      cfg_data[10*32 +: 32] = v_out_inv_scale_u32;
      cfg_data[11*32 +: 32] = q_bias_scale_u32;
      cfg_data[12*32 +: 32] = k_bias_scale_u32;
      cfg_data[13*32 +: 32] = v_bias_scale_u32;
      cfg_data[14*32 +: 32] = dm1_out_scale_u32;
      cfg_data[15*32 +: 32] = dm2_ctx_inv_scale_u32;
      cfg_data[16*32 +: 32] = dm2_out_inv_scale_u32;
      cfg_data[17*32 +: 32] = out_out_scale_u32;
      cfg_data[18*32 +: 32] = ln2_out_inv_scale_u32;
      cfg_data[19*32 +: 32] = ffnup_out_inv_scale_u32;
      cfg_data[20*32 +: 32] = ffnup_bias_scale_u32;
      cfg_data[21*32 +: 32] = ffndown_out_scale_u32;
    end
  endtask

  task automatic load_mem_image;
    begin
      for (idx = 0; idx < MAX_MEM_WORDS; idx++) mem_words[idx] = 32'd0;
      for (idx = 0; idx < ddr_word_count; idx++) mem_words[idx] = ddr_image_words[idx];
      for (idx = 0; idx < MAX_OUTPUT_BEATS; idx++) seen[idx] = 1'b0;
    end
  endtask

  task automatic fill_axi_rdata(input longint unsigned addr);
    longint unsigned aligned_addr;
    integer base_idx;
    begin
      aligned_addr = addr & ~64'h3f;
      base_idx = mem_word_index(aligned_addr);
      c0_ddr4_s_axi_rdata = '0;
      for (idx = 0; idx < 16; idx++) begin
        c0_ddr4_s_axi_rdata[idx * 32 +: 32] = mem_words[base_idx + idx];
      end
    end
  endtask

  task automatic store_axi_wdata(
      input longint unsigned addr,
      input logic [511:0] data,
      input logic [63:0] strb
  );
    longint unsigned aligned_addr;
    integer base_idx;
    integer byte_idx;
    integer word_sel;
    integer byte_sel;
    logic [31:0] cur_word;
    begin
      aligned_addr = addr & ~64'h3f;
      base_idx = mem_word_index(aligned_addr);
      for (byte_idx = 0; byte_idx < 64; byte_idx++) begin
        if (strb[byte_idx]) begin
          word_sel = byte_idx / 4;
          byte_sel = byte_idx % 4;
          cur_word = mem_words[base_idx + word_sel];
          cur_word[byte_sel * 8 +: 8] = data[byte_idx * 8 +: 8];
          mem_words[base_idx + word_sel] = cur_word;
        end
      end
    end
  endtask

  task automatic check_outputs;
    integer beat_idx;
    integer lane_idx;
    logic [31:0] written_word;
    real obs;
    real exp;
    real abs_err;
    begin
      if ($isunknown(output_beats_cfg)) fatal_msg("output_beats_cfg is unknown at check_outputs");
      if (output_beats_cfg <= 0 || output_beats_cfg > MAX_OUTPUT_BEATS) begin
        fatal_msg($sformatf("unexpected output_beats_cfg=%0d", output_beats_cfg));
      end
      for (beat_idx = 0; beat_idx < output_beats_cfg; beat_idx++) begin
        if (!seen[beat_idx]) fatal_msg($sformatf("missing output beat=%0d", beat_idx));
      end
      if (NUM_LAYERS == 1) begin
        if ((golden_word_count % 12) != 0) fatal_msg($sformatf("golden word count is not a multiple of 12: %0d", golden_word_count));
        golden_beats = golden_word_count / 12;
        for (beat_idx = 0; beat_idx < golden_beats; beat_idx++) begin
          for (lane_idx = 0; lane_idx < 12; lane_idx++) begin
            written_word = read_mem_word_abs(output_base_addr_u64 + beat_idx * output_stride_bytes_u64 + lane_idx * 4);
            if (written_word != golden_words[beat_idx * 12 + lane_idx]) begin
              obs = $bitstoshortreal(written_word);
              exp = $bitstoshortreal(golden_words[beat_idx * 12 + lane_idx]);
              abs_err = abs_real(obs - exp);
              if (abs_err > 5.0e-4) begin
                fatal_msg($sformatf("%s writeback mismatch beat=%0d lane=%0d observed_bits=0x%08x expected_bits=0x%08x observed=%f expected=%f abs_err=%f",
                                    `DUT_LABEL,
                                    beat_idx, lane_idx, written_word, golden_words[beat_idx * 12 + lane_idx], obs, exp, abs_err));
              end
            end
          end
        end
        $display("%s PASS beats=%0d", `DUT_LABEL, golden_beats);
      end else begin
        $display("%s PASS runtime-only layers=%0d beats=%0d", `DUT_LABEL, NUM_LAYERS, output_beats_cfg);
      end
    end
  endtask

  initial begin
    forever begin
      @(posedge c0_ddr4_s_axi_arvalid);
      if (c0_ddr4_s_axi_rst_n) begin
        if (rd_active) fatal_msg("multiple outstanding AXI reads are not supported");
        rd_active = 1'b1;
        rd_latency = READ_ADDR_LATENCY;
        rd_addr = {27'd0, c0_ddr4_s_axi_araddr};
        rd_id = c0_ddr4_s_axi_arid;
        ar_hs_count = ar_hs_count + 1;
        if (trace_fd != 0) begin
          $fdisplay(trace_fd, "TRACE ar_accept t=%0t addr=0x%0h id=%0d lat=%0d",
                    $time, rd_addr, rd_id, rd_latency);
          $fflush(trace_fd);
        end
        repeat (READ_ADDR_LATENCY) begin
          @(posedge c0_ddr4_s_axi_clk);
          rd_latency = rd_latency - 1;
        end
        fill_axi_rdata(rd_addr);
        c0_ddr4_s_axi_rid = rd_id;
        c0_ddr4_s_axi_rresp = 2'b00;
        c0_ddr4_s_axi_rvalid = 1'b1;
        c0_ddr4_s_axi_rlast = 1'b1;
        while (!c0_ddr4_s_axi_rready) begin
          @(posedge c0_ddr4_s_axi_clk);
        end
        @(posedge c0_ddr4_s_axi_clk);
        c0_ddr4_s_axi_rvalid = 1'b0;
        c0_ddr4_s_axi_rlast = 1'b0;
        r_hs_count = r_hs_count + 1;
        rd_active = 1'b0;
      end
    end
  end

  initial begin
    forever begin
      @(posedge c0_ddr4_s_axi_awvalid);
      if (c0_ddr4_s_axi_rst_n) begin
        while (c0_ddr4_s_axi_rst_n && !c0_ddr4_s_axi_awready) begin
          @(posedge c0_ddr4_s_axi_clk);
        end
        if (c0_ddr4_s_axi_rst_n) begin
          if (wr_active) fatal_msg("multiple outstanding AXI writes are not supported");
          if (c0_ddr4_s_axi_awburst != 2'b01) fatal_msg("unexpected write burst type");
          if (c0_ddr4_s_axi_awsize != 3'd6) fatal_msg($sformatf("unexpected write size=%0d", c0_ddr4_s_axi_awsize));
          if (c0_ddr4_s_axi_awlen != 8'd0) fatal_msg($sformatf("unexpected write len=%0d", c0_ddr4_s_axi_awlen));
          if (runtime_debug_window(dut.state) && debug_event_count < 64) begin
            $display("cnn_core_tb event AW cycle=%0d addr=0x%0h id=%0d state=%0d layer=%0d token=%0d",
                     cycle, {27'd0, c0_ddr4_s_axi_awaddr}, c0_ddr4_s_axi_awid, dut.state, dut.layer_idx, dut.run_token_idx);
            debug_event_count = debug_event_count + 1;
          end
          wr_active = 1'b1;
          wr_addr = {27'd0, c0_ddr4_s_axi_awaddr};
          wr_id = c0_ddr4_s_axi_awid;
          aw_hs_count = aw_hs_count + 1;

          while (c0_ddr4_s_axi_rst_n && !(c0_ddr4_s_axi_wvalid && c0_ddr4_s_axi_wready)) begin
            @(posedge c0_ddr4_s_axi_clk);
          end
          if (c0_ddr4_s_axi_rst_n) begin
            if (!wr_active) fatal_msg("write data arrived without AW");
            if (!c0_ddr4_s_axi_wlast) fatal_msg("expected single-beat write with WLAST=1");
            if (runtime_debug_window(dut.state) && debug_event_count < 64) begin
              $display("cnn_core_tb event W cycle=%0d addr=0x%0h strb=0x%0h state=%0d layer=%0d token=%0d",
                       cycle, wr_addr, c0_ddr4_s_axi_wstrb, dut.state, dut.layer_idx, dut.run_token_idx);
              debug_event_count = debug_event_count + 1;
            end
            store_axi_wdata(wr_addr, c0_ddr4_s_axi_wdata, c0_ddr4_s_axi_wstrb);
            if (wr_addr >= output_base_addr_u64 && wr_addr < (output_base_addr_u64 + output_beats_cfg * output_stride_bytes_u64)) begin
              idx = (wr_addr - output_base_addr_u64) / output_stride_bytes_u64;
              if (idx >= 0 && idx < MAX_OUTPUT_BEATS) seen[idx] = 1'b1;
            end
            wr_active = 1'b0;
            b_pending = 1'b1;
            b_latency = WRITE_RESP_LATENCY;
            w_hs_count = w_hs_count + 1;

            repeat (WRITE_RESP_LATENCY) begin
              @(posedge c0_ddr4_s_axi_clk);
            end
            if (c0_ddr4_s_axi_rst_n) begin
              c0_ddr4_s_axi_bvalid = 1'b1;
              b_emit_count = b_emit_count + 1;
              if (runtime_debug_window(dut.state) && debug_event_count < 64) begin
                $display("cnn_core_tb event B cycle=%0d addr=0x%0h id=%0d state=%0d layer=%0d token=%0d",
                         cycle, wr_addr, wr_id, dut.state, dut.layer_idx, dut.run_token_idx);
                debug_event_count = debug_event_count + 1;
              end
              while (c0_ddr4_s_axi_rst_n && !c0_ddr4_s_axi_bready) begin
                @(posedge c0_ddr4_s_axi_clk);
              end
              if (c0_ddr4_s_axi_rst_n) begin
                @(posedge c0_ddr4_s_axi_clk);
                c0_ddr4_s_axi_bvalid = 1'b0;
                b_pending = 1'b0;
                b_hs_count = b_hs_count + 1;
              end
            end
          end
        end
      end
    end
  end

  always @(posedge c0_ddr4_s_axi_clk) begin
    if (!c0_ddr4_s_axi_rst_n) begin
      rd_active = 1'b0;
      rd_latency = 0;
      rd_addr = 64'd0;
      rd_id = 4'd0;
      ar_hs_count <= 0;
      r_hs_count <= 0;
      wr_active <= 1'b0;
      wr_addr <= 64'd0;
      wr_id <= 4'd0;
      b_pending <= 1'b0;
      b_latency <= 0;
      aw_hs_count <= 0;
      w_hs_count <= 0;
      b_emit_count <= 0;
      b_hs_count <= 0;
      c0_ddr4_s_axi_arready <= 1'b0;
      c0_ddr4_s_axi_rvalid <= 1'b0;
      c0_ddr4_s_axi_rlast <= 1'b0;
      c0_ddr4_s_axi_rresp <= 2'b00;
      c0_ddr4_s_axi_rid <= 4'd0;
      c0_ddr4_s_axi_rdata <= '0;
      c0_ddr4_s_axi_awready <= 1'b0;
      c0_ddr4_s_axi_wready <= 1'b0;
      c0_ddr4_s_axi_bvalid <= 1'b0;
      c0_ddr4_s_axi_bresp <= 2'b00;
      c0_ddr4_s_axi_bid <= 4'd0;
      prev_dut_state <= 5'd0;
      run_entry_cycle <= 64'd0;
      stage_event_count <= 0;
      token3_qkv_event_count <= 0;
      token3_attn_in_event_count <= 0;
      token1_qkv_collect_event_count <= 0;
      lnq_stat_event_count <= 0;
      prev_lnq_state <= 4'd0;
      prev_lnq_stat_read_en <= 1'b0;
      prev_lnq_stat_valid <= 1'b0;
      prev_lnq_stat_first <= 1'b0;
      prev_lnq_stat_last <= 1'b0;
    end else begin
      cycle_mod = cycle % 17;
      c0_ddr4_s_axi_arready <= !rd_active;
      c0_ddr4_s_axi_awready <= ((cycle % 13) != 0);
      c0_ddr4_s_axi_wready <= ((cycle % 11) != 0);

      c0_ddr4_s_axi_rresp <= 2'b00;
      c0_ddr4_s_axi_bresp <= 2'b00;
      c0_ddr4_s_axi_bid <= wr_id;
      c0_ddr4_s_axi_rid <= rd_id;

      if (dut.state != prev_dut_state) begin
        $display("cnn_core_tb state-change cycle=%0d prev=%0d curr=%0d layer=%0d token=%0d run_slot=%0d load_tok=%0d exec_tok=%0d store_tok=%0d",
                 cycle, prev_dut_state, dut.state, dut.layer_idx, dut.run_token_idx, dut.run_slot_idx,
                 dut.load_token_idx, dut.exec_token_idx, dut.store_token_idx);
        if (dut.state == 5'd23) begin
          run_entry_cycle <= cycle;
          stage_event_count <= 0;
          qkv_stage_event_count <= 0;
          token3_qkv_event_count <= 0;
          token3_attn_in_event_count <= 0;
          token1_focus_event_count <= 0;
          token1_qkv_collect_event_count <= 0;
          token2_front_event_count <= 0;
          out_token1_event_count <= 0;
          out_cu_event_count <= 0;
          out_lu_trace_count <= 0;
          out_lu_vec22_trace_count <= 0;
          token1_resadd_event_count <= 0;
          outlinear_live_event_count <= 0;
          out_psum_event_count <= 0;
          out_headbuf_event_count <= 0;
          out_capture_event_count <= 0;
          out_queue_event_count <= 0;
          dm2_event_count <= 0;
          dm1_event_count <= 0;
          dm1_override_event_count <= 0;
          tap_trace_count <= 0;
          hist_write_trace_count <= 0;
          hist_read_trace_count <= 0;
          token3_out_event_count <= 0;
          lnq_stat_event_count <= 0;
          outlinear_feed_count <= 0;
          outlinear_collect_count <= 0;
          out_lu_vec22_trace_active <= 1'b0;
        end
        prev_dut_state <= dut.state;
      end

      if (runtime_debug_window(dut.state) &&
          (dut.run_token_idx == 11'd0) &&
          (lnq_stat_event_count < 160) &&
          ((dut.u_core.layernorm.state >= 4'd1) &&
           (dut.u_core.layernorm.state <= 4'd9) ||
           dut.u_core.layernorm.io_res_valid)) begin
        $display("cnn_core_tb lnq-event cycle=%0d state=%0d vec=%0d statRe=%0d statV=%0d statF=%0d statL=%0d sqrtInV=%0d sqrtIR=%0d sqrtOV=%0d divInV=%0d divIR=%0d divOV=%0d outReadEn=%0d outValidRaw=%0d outFirstRaw=%0d outLastRaw=%0d outValidPipe=%0d resV=%0d resLast=%0d outAddrRaw=%0d outAddrPipe=%0d r0_x=%0d r0_w0=%h r0_w1=%h r0_w2=%h r0_w3=%h r0_w4=%h r0_w5=%h r0_w6=%h r0_w7=%h r0_w8=%h r0_w9=%h r0_w10=%h r0_w11=%h add01=%h add23=%h add45=%h add67=%h add89=%h add1011=%h add0123=%h add4567=%h add891011=%h laneSum=%h mul0=%h mul1=%h laneSq=%h sumAcc=%h sqSumAcc=%h sumAdd=%h sqAdd=%h meanMul=%h varAddEps=%h mean=%h var=%h",
                 cycle,
                 dut.u_core.layernorm.state,
                 dut.u_core.layernorm.vecIdx,
                 dut.u_core.layernorm.statReadEn,
                 dut.u_core.layernorm.statValid,
                 dut.u_core.layernorm.statFirst,
                 dut.u_core.layernorm.statLast,
                 dut.u_core.layernorm.sqrt_io_inValid,
                 dut.u_core.layernorm._sqrt_io_inReady,
                 dut.u_core.layernorm._sqrt_io_outValidSqrt,
                 dut.u_core.layernorm.div_io_inValid,
                 dut.u_core.layernorm._div_io_inReady,
                 dut.u_core.layernorm._div_io_outValidDiv,
                 dut.u_core.layernorm.outReadEn,
                 dut.u_core.layernorm.outValidRaw,
                 dut.u_core.layernorm.outFirstRaw,
                 dut.u_core.layernorm.outLastRaw,
                 dut.u_core.layernorm.outValidPipe_69,
                 dut.u_core.layernorm.io_res_valid,
                 dut.u_core.layernorm.io_res_last,
                 dut.u_core.layernorm.outAddrRegRaw,
                 dut.u_core.layernorm.outAddrPipe_69,
                 $isunknown(dut.u_core.layernorm._inputMem_ext_R0_data),
                 dut.u_core.layernorm._inputMem_ext_R0_data[31:0],
                 dut.u_core.layernorm._inputMem_ext_R0_data[63:32],
                 dut.u_core.layernorm._inputMem_ext_R0_data[95:64],
                 dut.u_core.layernorm._inputMem_ext_R0_data[127:96],
                 dut.u_core.layernorm._inputMem_ext_R0_data[159:128],
                 dut.u_core.layernorm._inputMem_ext_R0_data[191:160],
                 dut.u_core.layernorm._inputMem_ext_R0_data[223:192],
                 dut.u_core.layernorm._inputMem_ext_R0_data[255:224],
                 dut.u_core.layernorm._inputMem_ext_R0_data[287:256],
                 dut.u_core.layernorm._inputMem_ext_R0_data[319:288],
                 dut.u_core.layernorm._inputMem_ext_R0_data[351:320],
                 dut.u_core.layernorm._inputMem_ext_R0_data[383:352],
                 dut.u_core.layernorm.laneSum._add01_io_out,
                 dut.u_core.layernorm.laneSum._add23_io_out,
                 dut.u_core.layernorm.laneSum._add45_io_out,
                 dut.u_core.layernorm.laneSum._add67_io_out,
                 dut.u_core.layernorm.laneSum._add89_io_out,
                 dut.u_core.layernorm.laneSum._add1011_io_out,
                 dut.u_core.layernorm.laneSum._add0123_io_out,
                 dut.u_core.layernorm.laneSum._add4567_io_out,
                 dut.u_core.layernorm.laneSum._add891011_io_out,
                 dut.u_core.layernorm._laneSum_io_out,
                 dut.u_core.layernorm.laneSqSum._mul_io_out,
                 dut.u_core.layernorm.laneSqSum._mul_1_io_out,
                 dut.u_core.layernorm._laneSqSum_io_out,
                 dut.u_core.layernorm.sumAcc,
                 dut.u_core.layernorm.sqSumAcc,
                 dut.u_core.layernorm._sumAdd_io_out,
                 dut.u_core.layernorm._sqAdd_io_out,
                 dut.u_core.layernorm._meanMul_io_out,
                 dut.u_core.layernorm._varAddEps_io_out,
                 dut.u_core.layernorm.meanReg,
                 dut.u_core.layernorm.varReg);
        lnq_stat_event_count <= lnq_stat_event_count + 1;
      end
      prev_lnq_state <= dut.u_core.layernorm.state;
      prev_lnq_stat_read_en <= dut.u_core.layernorm.statReadEn;
      prev_lnq_stat_valid <= dut.u_core.layernorm.statValid;
      prev_lnq_stat_first <= dut.u_core.layernorm.statFirst;
      prev_lnq_stat_last <= dut.u_core.layernorm.statLast;

      if ((prev_outlinear_state != dut.u_core.outlinear.state) &&
          (dut.u_core.outlinear.state == 2'd1)) begin
        outlinear_collect_count <= outlinear_collect_count + 1;
      end

      if ((prev_outlinear_state != dut.u_core.outlinear.state) &&
          (dut.u_core.outlinear.state == 2'd2)) begin
        outlinear_feed_count <= outlinear_feed_count + 1;
      end
      if (runtime_debug_window(dut.state) &&
          ((dut.run_token_idx == 11'd3) || (dut.run_token_idx == 11'd18)) &&
          (token3_attn_in_event_count < 256) &&
          (dut.u_core._qkvlinear_io_data_out_st ||
           dut.u_core._qkvlinear_io_data_out_last ||
           (dut.u_core._qkvlinear_io_data_out_valid && !dut.u_core.atten.input_ready) ||
           dut.u_core.atten.vcache_io_data_in_st ||
           dut.u_core.atten.inputHeadDone)) begin
        $display("cnn_core_tb attn-in cycle=%0d run_token=%0d qkv_head=%0d qkv_v=%0d qkv_st=%0d qkv_last=%0d qkv_addr=%0d attn_rdy=%0d input_rdy=%0d input_fire=%0d dm1_rdy=%0d vcache_rdy=%0d vcache_st=%0d vcache_last=%0d",
                 cycle,
                 dut.run_token_idx,
                 dut.core_attn_tap_head,
                 dut.u_core._qkvlinear_io_data_out_valid,
                 dut.u_core._qkvlinear_io_data_out_st,
                 dut.u_core._qkvlinear_io_data_out_last,
                 dut.u_core._qkvlinear_io_data_out_addr,
                 dut.u_core._atten_io_data_ready,
                 dut.u_core.atten.input_ready,
                 dut.u_core.atten.input_fire,
                 dut.u_core.atten._dm1_io_data_ready,
                 dut.u_core.atten._vcache_io_data_in_ready,
                 dut.u_core.atten.vcache_io_data_in_st,
                 dut.u_core.atten.inputHeadDone);
        token3_attn_in_event_count <= token3_attn_in_event_count + 1;
      end
      if (runtime_debug_window(dut.state) &&
          ((dut.run_token_idx == 11'd3) || (dut.run_token_idx == 11'd18)) &&
          (token3_out_event_count < 256) &&
          (dut.u_core._atten_io_res_valid ||
           dut.u_core._attnToOutQ_io_deq_valid ||
           dut.u_core.outlinear.io_data_in_valid ||
           dut.u_core.outlinear._lu_inst_io_read_en ||
           dut.u_core.outlinear._mem_inst_io_r_ready ||
           dut.u_core.outlinear._lu_inst_io_data_out_valid ||
           dut.u_core.outlinear._cu_inst_io_data_out_valid ||
           dut.u_core._outlinear_io_data_out_valid)) begin
        $display("cnn_core_tb token3-out cycle=%0d run_token=%0d attn_v=%0d attn_st=%0d attn_last=%0d attn_x=%0d aq_enq_rdy=%0d aq_v=%0d aq_st=%0d aq_last=%0d aq_full=%0d aq_enq=%0d aq_deq=%0d out_state=%0d out_head=%0d out_rdy=%0d out_gap=%0d out_seen=%0d out_in_v=%0d out_in_st=%0d out_in_last=%0d out_lu_re=%0d out_mem_rrdy=%0d lu_v=%0d cu_v=%0d out_v=%0d",
                 cycle,
                 dut.run_token_idx,
                 dut.u_core._atten_io_res_valid,
                 dut.u_core._atten_io_res_st,
                 dut.u_core._atten_io_res_last,
                 $isunknown(dut.u_core._atten_io_res),
                 dut.u_core._attnToOutQ_io_enq_ready,
                 dut.u_core._attnToOutQ_io_deq_valid,
                 dut.u_core._attnToOutQ_io_deq_bits_st,
                 dut.u_core._attnToOutQ_io_deq_bits_last,
                 dut.u_core.attnToOutQ.maybe_full,
                 dut.u_core.attnToOutQ.enq_ptr_value,
                 dut.u_core.attnToOutQ.deq_ptr_value,
                 dut.u_core.outlinear.state,
                 dut.u_core.outlinear.head_cnt,
                 dut.u_core._outlinear_io_data_ready,
                 dut.u_core.outlinear.awaitInputGap,
                 dut.u_core.outlinear.decodeBurstSeen,
                 dut.u_core.outlinear.io_data_in_valid,
                 dut.u_core.outlinear.io_data_in_st,
                 dut.u_core.outlinear.io_data_in_last,
                 dut.u_core.outlinear._lu_inst_io_read_en,
                 dut.u_core.outlinear._mem_inst_io_r_ready,
                 dut.u_core.outlinear._lu_inst_io_data_out_valid,
                 dut.u_core.outlinear._cu_inst_io_data_out_valid,
                 dut.u_core._outlinear_io_data_out_valid);
        token3_out_event_count <= token3_out_event_count + 1;
      end
      if (runtime_debug_window(dut.state) &&
          (dut.run_token_idx == 11'd1) &&
          (dm1_override_event_count < 128) &&
          dut.core_attn_dm1_override_valid &&
          dut.core_attn_dm1_override_ready) begin
        $display("cnn_core_tb dm1ov-fire cycle=%0d run_token=%0d replay_tok=%0d replay_head=%0d replay_beat=%0d ov_x=%0d ov=0x%08h q=0x%04h k=0x%04h",
                 cycle,
                 dut.run_token_idx,
                 dut.replay_token_idx,
                 dut.replay_head_idx,
                 dut.replay_beat_idx,
                 $isunknown(dut.core_attn_dm1_override_data),
                 dut.core_attn_dm1_override_data,
                 dut.replay_q_beat,
                 dut.replay_k_beat);
        dm1_override_event_count <= dm1_override_event_count + 1;
      end

      if (tb_debug_enable &&
          runtime_debug_window(dut.state) &&
          (dut.run_token_idx == 11'd0) &&
          (tap_trace_count < 96) &&
          dut.core_attn_tap_valid &&
          (dut.core_attn_tap_head < 4'd2)) begin
        $display("cnn_core_tb tap-fire cycle=%0d run_token=%0d head=%0d addr=%0d last=%0d tap_x=%0d tap=0x%012h q=0x%04h k=0x%04h v=0x%04h kv_done=0x%03x",
                 cycle,
                 dut.run_token_idx,
                 dut.core_attn_tap_head,
                 dut.core_attn_tap_addr,
                 dut.core_attn_tap_last,
                 $isunknown(dut.core_attn_tap_data),
                 dut.core_attn_tap_data,
                 dut.core_attn_tap_data[15:0],
                 dut.core_attn_tap_data[31:16],
                 dut.core_attn_tap_data[47:32],
                 dut.kv_tap_head_done);
        tap_trace_count <= tap_trace_count + 1;
      end

      if (tb_debug_enable &&
          runtime_debug_window(dut.state) &&
          (hist_write_trace_count < 48) &&
          c0_ddr4_s_axi_wvalid &&
          c0_ddr4_s_axi_wready &&
          dut.wr_hist_active &&
          (dut.kv_hist_write_head_idx < 4'd2)) begin
        $display("cnn_core_tb hist-write cycle=%0d run_token=%0d head=%0d phase=%0d wr_addr=0x%0h wdata_x=%0d w0=0x%04h w1=0x%04h w2=0x%04h w3=0x%04h k00=0x%04h k01=0x%04h k02=0x%04h k03=0x%04h k10=0x%04h k11=0x%04h k12=0x%04h k13=0x%04h",
                 cycle,
                 dut.run_token_idx,
                 dut.kv_hist_write_head_idx,
                 dut.kv_hist_write_phase,
                 wr_addr,
                 $isunknown(dut.kv_hist_write_data),
                 dut.kv_hist_write_data[15:0],
                 dut.kv_hist_write_data[31:16],
                 dut.kv_hist_write_data[47:32],
                 dut.kv_hist_write_data[63:48],
                 dut.k_tap_buf[0][0],
                 dut.k_tap_buf[0][1],
                 dut.k_tap_buf[0][2],
                 dut.k_tap_buf[0][3],
                 dut.k_tap_buf[1][0],
                 dut.k_tap_buf[1][1],
                 dut.k_tap_buf[1][2],
                 dut.k_tap_buf[1][3]);
        hist_write_trace_count <= hist_write_trace_count + 1;
      end

      if (tb_debug_enable &&
          runtime_debug_window(dut.state) &&
          (hist_read_trace_count < 48) &&
          dut.rd_fire &&
          dut.rd_hist_active &&
          (dut.replay_token_idx == 16'd0) &&
          (dut.replay_head_idx < 4'd2)) begin
        $display("cnn_core_tb hist-read cycle=%0d run_token=%0d replay_tok=%0d head=%0d phase=%0d rd_addr=0x%0h rdata_x=%0d r0=0x%04h r1=0x%04h r2=0x%04h r3=0x%04h",
                 cycle,
                 dut.run_token_idx,
                 dut.replay_token_idx,
                 dut.replay_head_idx,
                 dut.replay_read_phase,
                 rd_addr,
                 $isunknown(c0_ddr4_s_axi_rdata),
                 c0_ddr4_s_axi_rdata[15:0],
                 c0_ddr4_s_axi_rdata[31:16],
                 c0_ddr4_s_axi_rdata[47:32],
                 c0_ddr4_s_axi_rdata[63:48]);
        hist_read_trace_count <= hist_read_trace_count + 1;
      end

      if (runtime_debug_window(dut.state) &&
          ((dut.run_token_idx == 11'd0) ||
           (dut.run_token_idx == 11'd1) ||
           (dut.run_token_idx == 11'd3) ||
           (dut.run_token_idx == 11'd18) ||
           (dut.run_token_idx == 11'd25) ||
           (dut.run_token_idx == 11'd26) ||
           (dut.run_token_idx >= 11'd52)) &&
          (dm1_event_count < 512) &&
          (dut.u_core.atten._dm1_io_res_valid ||
           dut.u_core.atten.dm1.cu_inst.qkVecValid ||
           dut.u_core.atten.dm1.cu_inst.rowDone ||
           dut.u_core.atten._softmax_io_res_valid)) begin
        $display("cnn_core_tb dm1-event cycle=%0d run_token=%0d dm1_res_v=%0d dm1_res_st=%0d dm1_res_last=%0d dm1_res_addr=%0d dm1_res_rdy=%0d dm1_res_x=%0d dm1_b0=0x%08h dm1_b1=0x%08h dm1_b2=0x%08h dm1_lu_v=%0d qk_valid=%0d cu_state=%0d compute_done=%0d row_done=%0d key_cnt=%0d prefill_q=%0d lbatch=%0d smx_head_st=%0d smx_started=%0d soft_state=%0d soft_res_v=%0d soft_w_x=%0d soft_w_lo=0x%08h soft_w_b0=%0d soft_tile_x=%0d soft_gmax_x=%0d soft_sum_x=%0d soft_sum=0x%09h soft_div_v=%0d soft_mask_addr=%0d soft_tiles=%0d",
                 cycle,
                 dut.run_token_idx,
                 dut.u_core.atten._dm1_io_res_valid,
                 dut.u_core.atten._dm1_io_res_st,
                 dut.u_core.atten._dm1_io_res_last,
                 dut.u_core.atten._dm1_io_res_addr,
                 dut.u_core.atten._softmax_io_data_ready,
                 $isunknown(dut.u_core.atten.dm1.io_res),
                 dut.u_core.atten.dm1.io_res[31:0],
                 dut.u_core.atten.dm1.io_res[63:32],
                 dut.u_core.atten.dm1.io_res[95:64],
                 dut.u_core.atten.dm1._lu_inst_io_data_out_valid,
                 dut.u_core.atten.dm1.cu_inst.qkVecValid,
                 dut.u_core.atten.dm1.cu_inst.state,
                 dut.u_core.atten.dm1.cu_inst.computeDone,
                 dut.u_core.atten.dm1.cu_inst.rowDone,
                 dut.u_core.atten.dm1.cu_inst.comp_key_cnt,
                 dut.u_core.atten.dm1.cu_inst.comp_prefill_q_cnt,
                 dut.u_core.atten.dm1.cu_inst.lbatch_cnt,
                 dut.u_core.atten.softmaxHeadStart,
                 1'b0,
                 dut.u_core.atten.softmax.state,
                 dut.u_core.atten._softmax_io_res_valid,
                 $isunknown(dut.u_core.atten.softmax.io_w_in),
                 dut.u_core.atten.softmax.io_w_in[31:0],
                 dut.u_core.atten.softmax.io_w_in[0],
                 $isunknown(dut.u_core.atten.softmax.passTileReg),
                 $isunknown(dut.u_core.atten.softmax.globalMaxReg),
                 $isunknown(dut.u_core.atten.softmax.sumExpReg),
                 dut.u_core.atten.softmax.sumExpReg,
                 dut.u_core.atten.softmax._recipDiv_io_outValidDiv,
                 dut.u_core.atten.softmax.maskAddrReg,
                 dut.u_core.atten.softmax.rowTileCountReg);
        dm1_event_count <= dm1_event_count + 1;
      end
      if (runtime_debug_window(dut.state) &&
          ((dut.run_token_idx == 11'd0) ||
           (dut.run_token_idx == 11'd3) ||
           (dut.run_token_idx == 11'd18) ||
           (dut.run_token_idx == 11'd25) ||
           (dut.run_token_idx == 11'd26) ||
           (dut.run_token_idx >= 11'd52)) &&
          (dm2_event_count < 256) &&
          (dut.u_core.atten._softmax_io_res_valid ||
           dut.u_core.atten._vcache_io_res_valid ||
           (dut.u_core.atten._ctxToDm2Q_io_deq_valid && dut.u_core.atten._dm2_io_data_in_ctx_ready) ||
           (dut.u_core.atten._vToDm2Q_io_deq_valid && dut.u_core.atten._dm2_io_data_in_v_ready) ||
           dut.u_core.atten.dm2._dmInst_io_data_out_valid ||
           dut.u_core.atten.dm2._suInst_io_data_out_valid ||
           dut.u_core.atten.io_res_valid)) begin
        $display("cnn_core_tb dm2-event cycle=%0d run_token=%0d soft_v=%0d soft_st=%0d soft_last=%0d soft_addr=%0d ctx_fire=%0d ctx_st=%0d ctx_x=%0d ctx_b0=0x%02h vc_v=%0d vc_st=%0d vc_last=%0d vc_addr=%0d v_fire=%0d v_x=%0d v_b0=0x%02h dm2_state=%0d lbatch=%0d tile_base=%0d tile_cnt=%0d waitctx=%0d mul=%0d dm2_out_v=%0d su_v=%0d su_addr=%0d su_last=%0d attn_v=%0d attn_addr=%0d attn_last=%0d attn_x=%0d attn_b0=0x%02h attn_b63=0x%02h ctxq_full=%0d ctxq_enq=%0d ctxq_deq=%0d vq_full=%0d vq_enq=%0d vq_deq=%0d",
                 cycle,
                 dut.run_token_idx,
                 dut.u_core.atten._softmax_io_res_valid,
                 dut.u_core.atten._softmax_io_res_st,
                 dut.u_core.atten._softmax_io_res_last,
                 dut.u_core.atten._softmax_io_res_addr,
                 dut.u_core.atten._ctxToDm2Q_io_deq_valid && dut.u_core.atten._dm2_io_data_in_ctx_ready,
                 dut.u_core.atten._ctxToDm2Q_io_deq_bits_st,
                 $isunknown(dut.u_core.atten._ctxToDm2Q_io_deq_bits_data),
                 dut.u_core.atten._ctxToDm2Q_io_deq_bits_data[7:0],
                 dut.u_core.atten._vcache_io_res_valid,
                 dut.u_core.atten._vcache_io_res_st,
                 dut.u_core.atten._vcache_io_res_last,
                 dut.u_core.atten._vcache_io_res_addr,
                 dut.u_core.atten._vToDm2Q_io_deq_valid && dut.u_core.atten._dm2_io_data_in_v_ready,
                 $isunknown(dut.u_core.atten._vToDm2Q_io_deq_bits_data),
                 dut.u_core.atten._vToDm2Q_io_deq_bits_data[7:0],
                 dut.u_core.atten.dm2.dmInst.state,
                 dut.u_core.atten.dm2.dmInst.lbatchCnt,
                 dut.u_core.atten.dm2.dmInst.tileBase,
                 dut.u_core.atten.dm2.dmInst.tileLoadCnt,
                 dut.u_core.atten.dm2.dmInst.waitctxCnt,
                 dut.u_core.atten.dm2.dmInst.mulCnt,
                 dut.u_core.atten.dm2._dmInst_io_data_out_valid,
                 dut.u_core.atten.dm2._suInst_io_data_out_valid,
                 dut.u_core.atten.dm2._suInst_io_data_out_addr,
                 dut.u_core.atten.dm2._suInst_io_data_out_last,
                 dut.u_core.atten.io_res_valid,
                 dut.u_core.atten._dm2_io_res_addr,
                 dut.u_core.atten.io_res_last,
                 $isunknown(dut.u_core._atten_io_res),
                 dut.u_core._atten_io_res[7:0],
                 dut.u_core._atten_io_res[511:504],
                 dut.u_core.atten.ctxToDm2Q.maybe_full,
                 dut.u_core.atten.ctxToDm2Q.enq_ptr_value,
                 dut.u_core.atten.ctxToDm2Q.deq_ptr_value,
                 dut.u_core.atten.vToDm2Q.maybe_full,
                 dut.u_core.atten.vToDm2Q.enq_ptr_value,
                 dut.u_core.atten.vToDm2Q.deq_ptr_value);
        dm2_event_count <= dm2_event_count + 1;
      end
      if (runtime_debug_window(dut.state) &&
          ((dut.run_token_idx == 11'd0) ||
           (dut.run_token_idx == 11'd3) ||
           (dut.run_token_idx == 11'd18) ||
           (dut.run_token_idx == 11'd25) ||
           (dut.run_token_idx == 11'd26) ||
           (dut.run_token_idx >= 11'd52)) &&
          (out_queue_event_count < 96) &&
          (dut.u_core._attnToOutQ_io_deq_valid ||
           dut.u_core.outlinear.io_data_in_valid ||
           (dut.u_core.outlinear.state != prev_outlinear_state))) begin
        $display("cnn_core_tb outlinear-queue cycle=%0d run_token=%0d q_v=%0d q_rdy=%0d q_st=%0d q_last=%0d q_addr=%0d q_x=%0d q_b0=0x%02h q_b31=0x%02h q_b63=0x%02h ol_v=%0d ol_rdy=%0d ol_st=%0d ol_last=%0d ol_addr=%0d ol_x=%0d ol_b0=0x%02h ol_b31=0x%02h ol_b63=0x%02h out_state=%0d head=%0d head_idx=%0d await_gap=%0d burst_seen=%0d actual_bs=%0d pipe_busy=%0d cap_open=%0d fresh=%0d aligned=%0d cap_fire=%0d feed_tok=%0d feed_chunk=%0d hb21_0_x=%0d hb21_0_b0=0x%02h hb21_0_b63=0x%02h aq_full=%0d aq_enq=%0d aq_deq=%0d",
                 cycle,
                 dut.run_token_idx,
                 dut.u_core._attnToOutQ_io_deq_valid,
                 dut.u_core.outlinear.io_data_ready,
                 dut.u_core._attnToOutQ_io_deq_bits_st,
                 dut.u_core._attnToOutQ_io_deq_bits_last,
                 dut.u_core._attnToOutQ_io_deq_bits_addr,
                 $isunknown(dut.u_core._attnToOutQ_io_deq_bits_data),
                 dut.u_core._attnToOutQ_io_deq_bits_data[7:0],
                 dut.u_core._attnToOutQ_io_deq_bits_data[255:248],
                 dut.u_core._attnToOutQ_io_deq_bits_data[511:504],
                 dut.u_core.outlinear.io_data_in_valid,
                 dut.u_core.outlinear.io_data_ready,
                 dut.u_core.outlinear.io_data_in_st,
                 dut.u_core.outlinear.io_data_in_last,
                 dut.u_core.outlinear.io_data_in_addr,
                 $isunknown(dut.u_core.outlinear.io_data_in),
                 dut.u_core.outlinear.io_data_in[7:0],
                 dut.u_core.outlinear.io_data_in[255:248],
                 dut.u_core.outlinear.io_data_in[511:504],
                 dut.u_core.outlinear.state,
                 dut.u_core.outlinear.head_cnt,
                 dut.u_core.outlinear.io_data_in_st ? 4'd0 : dut.u_core.outlinear.head_cnt,
                 dut.u_core.outlinear.awaitInputGap,
                 dut.u_core.outlinear.decodeBurstSeen,
                 dut.u_core.outlinear.actual_batchsize,
                 1'b0,
                 !dut.u_core.outlinear.awaitInputGap ||
                   dut.u_core.outlinear.io_cfg_valid ||
                   dut.u_core.outlinear.io_data_in_st,
                 (dut.u_core.outlinear.actual_batchsize != 0) ||
                   !dut.u_core.outlinear.decodeBurstSeen ||
                   dut.u_core.outlinear.io_cfg_valid,
                 (dut.u_core.outlinear.actual_batchsize != 0) ||
                   (dut.u_core.outlinear.state != 2'd0) ||
                   dut.u_core.outlinear.io_data_in_st,
                 dut.u_core.outlinear.io_data_in_valid &&
                   dut.u_core.outlinear.io_data_ready &&
                   (!dut.u_core.outlinear.awaitInputGap ||
                    dut.u_core.outlinear.io_cfg_valid ||
                    dut.u_core.outlinear.io_data_in_st) &&
                   ((dut.u_core.outlinear.actual_batchsize != 0) ||
                    !dut.u_core.outlinear.decodeBurstSeen ||
                    dut.u_core.outlinear.io_cfg_valid) &&
                   ((dut.u_core.outlinear.actual_batchsize != 0) ||
                    (dut.u_core.outlinear.state != 2'd0) ||
                    dut.u_core.outlinear.io_data_in_st),
                 dut.u_core.outlinear.feed_token_cnt,
                 dut.u_core.outlinear.feed_chunk_cnt,
                 $isunknown(dut.u_core.outlinear.head_buffer_21_0),
                 dut.u_core.outlinear.head_buffer_21_0[7:0],
                 dut.u_core.outlinear.head_buffer_21_0[511:504],
                 dut.u_core.attnToOutQ.maybe_full,
                 dut.u_core.attnToOutQ.enq_ptr_value,
                 dut.u_core.attnToOutQ.deq_ptr_value);
        out_queue_event_count <= out_queue_event_count + 1;
      end

      if (runtime_debug_window(dut.state) &&
          ((dut.run_token_idx == 11'd0) ||
           (dut.run_token_idx == 11'd3) ||
           (dut.run_token_idx == 11'd18) ||
           (dut.run_token_idx == 11'd25) ||
           (dut.run_token_idx == 11'd26) ||
           (dut.run_token_idx >= 11'd52)) &&
          (out_capture_event_count < 64) &&
          dut.u_core.outlinear.io_data_in_valid &&
          dut.u_core.outlinear.io_data_in_last &&
          dut.u_core.outlinear.io_data_ready) begin
        $display("cnn_core_tb outlinear-capture cycle=%0d run_token=%0d head=%0d head_idx=%0d attn_v=%0d attn_addr=%0d attn_st=%0d attn_last=%0d attn_x=%0d attn_b0=0x%02h attn_b31=0x%02h attn_b63=0x%02h q_v=%0d q_st=%0d q_last=%0d q_addr=%0d q_x=%0d q_b0=0x%02h q_b31=0x%02h q_b63=0x%02h ol_v=%0d ol_addr=%0d ol_st=%0d ol_last=%0d ol_x=%0d ol_b0=0x%02h ol_b31=0x%02h ol_b63=0x%02h out_state=%0d await_gap=%0d burst_seen=%0d actual_bs=%0d pipe_busy=%0d cap_open=%0d fresh=%0d aligned=%0d cap_fire=%0d feed_tok=%0d feed_chunk=%0d hb21_0_x=%0d hb21_0_b0=0x%02h hb21_0_b63=0x%02h aq_full=%0d aq_enq=%0d aq_deq=%0d dm2_state=%0d lbatch=%0d tile_base=%0d tile_cnt=%0d waitctx=%0d mul=%0d ctx_fire=%0d v_fire=%0d",
                 cycle,
                 dut.run_token_idx,
                 dut.u_core.outlinear.head_cnt,
                 dut.u_core.outlinear.io_data_in_st ? 4'd0 : dut.u_core.outlinear.head_cnt,
                 dut.u_core.atten.io_res_valid,
                 dut.u_core.atten._dm2_io_res_addr,
                 dut.u_core.atten.dm2._suInst_io_data_out_valid &&
                   (dut.u_core.atten.dm2._suInst_io_data_out_addr == 0),
                 dut.u_core._atten_io_res_last,
                 $isunknown(dut.u_core._atten_io_res),
                 dut.u_core._atten_io_res[7:0],
                 dut.u_core._atten_io_res[255:248],
                 dut.u_core._atten_io_res[511:504],
                 dut.u_core._attnToOutQ_io_deq_valid,
                 dut.u_core._attnToOutQ_io_deq_bits_st,
                 dut.u_core._attnToOutQ_io_deq_bits_last,
                 dut.u_core._attnToOutQ_io_deq_bits_addr,
                 $isunknown(dut.u_core._attnToOutQ_io_deq_bits_data),
                 dut.u_core._attnToOutQ_io_deq_bits_data[7:0],
                 dut.u_core._attnToOutQ_io_deq_bits_data[255:248],
                 dut.u_core._attnToOutQ_io_deq_bits_data[511:504],
                 dut.u_core.outlinear.io_data_in_valid,
                 dut.u_core.outlinear.io_data_in_addr,
                 dut.u_core.outlinear.io_data_in_st,
                 dut.u_core.outlinear.io_data_in_last,
                 $isunknown(dut.u_core.outlinear.io_data_in),
                 dut.u_core.outlinear.io_data_in[7:0],
                 dut.u_core.outlinear.io_data_in[255:248],
                 dut.u_core.outlinear.io_data_in[511:504],
                 dut.u_core.outlinear.state,
                 dut.u_core.outlinear.awaitInputGap,
                 dut.u_core.outlinear.decodeBurstSeen,
                 dut.u_core.outlinear.actual_batchsize,
                 1'b0,
                 !dut.u_core.outlinear.awaitInputGap ||
                   dut.u_core.outlinear.io_cfg_valid ||
                   dut.u_core.outlinear.io_data_in_st,
                 (dut.u_core.outlinear.actual_batchsize != 0) ||
                   !dut.u_core.outlinear.decodeBurstSeen ||
                   dut.u_core.outlinear.io_cfg_valid,
                 (dut.u_core.outlinear.actual_batchsize != 0) ||
                   (dut.u_core.outlinear.state != 2'd0) ||
                   dut.u_core.outlinear.io_data_in_st,
                 dut.u_core.outlinear.io_data_in_valid &&
                   dut.u_core.outlinear.io_data_ready &&
                   (!dut.u_core.outlinear.awaitInputGap ||
                    dut.u_core.outlinear.io_cfg_valid ||
                    dut.u_core.outlinear.io_data_in_st) &&
                   ((dut.u_core.outlinear.actual_batchsize != 0) ||
                    !dut.u_core.outlinear.decodeBurstSeen ||
                    dut.u_core.outlinear.io_cfg_valid) &&
                   ((dut.u_core.outlinear.actual_batchsize != 0) ||
                    (dut.u_core.outlinear.state != 2'd0) ||
                    dut.u_core.outlinear.io_data_in_st),
                 dut.u_core.outlinear.feed_token_cnt,
                 dut.u_core.outlinear.feed_chunk_cnt,
                 $isunknown(dut.u_core.outlinear.head_buffer_21_0),
                 dut.u_core.outlinear.head_buffer_21_0[7:0],
                 dut.u_core.outlinear.head_buffer_21_0[511:504],
                 dut.u_core.attnToOutQ.maybe_full,
                 dut.u_core.attnToOutQ.enq_ptr_value,
                 dut.u_core.attnToOutQ.deq_ptr_value,
                 dut.u_core.atten.dm2.dmInst.state,
                 dut.u_core.atten.dm2.dmInst.lbatchCnt,
                 dut.u_core.atten.dm2.dmInst.tileBase,
                 dut.u_core.atten.dm2.dmInst.tileLoadCnt,
                 dut.u_core.atten.dm2.dmInst.waitctxCnt,
                 dut.u_core.atten.dm2.dmInst.mulCnt,
                 dut.u_core.atten._ctxToDm2Q_io_deq_valid && dut.u_core.atten._dm2_io_data_in_ctx_ready,
                 dut.u_core.atten._vToDm2Q_io_deq_valid && dut.u_core.atten._dm2_io_data_in_v_ready);
        out_capture_event_count <= out_capture_event_count + 1;
      end
      if ((prev_outlinear_state != dut.u_core.outlinear.state) &&
          (dut.u_core.outlinear.state == 2'd2) &&
          ((dut.run_token_idx == 11'd0) ||
           (dut.run_token_idx == 11'd3) ||
           (dut.run_token_idx == 11'd18) ||
           (dut.run_token_idx >= 11'd52)) &&
          (out_headbuf_event_count < 8)) begin
        $display("cnn_core_tb outlinear-headbuf cycle=%0d run_token=%0d head=%0d collect=%0d feed=%0d hb_xmask=0x%03h hb0_b0=0x%02h hb1_b0=0x%02h hb2_b0=0x%02h hb3_b0=0x%02h hb4_b0=0x%02h hb5_b0=0x%02h hb11_b0=0x%02h hb0_b63=0x%02h hb1_b63=0x%02h hb2_b63=0x%02h hb3_b63=0x%02h hb4_b63=0x%02h hb5_b63=0x%02h hb11_b63=0x%02h",
                 cycle,
                 dut.run_token_idx,
                 dut.u_core.outlinear.head_cnt,
                 outlinear_collect_count,
                 outlinear_feed_count,
                 {
                   $isunknown(dut.u_core.outlinear.head_buffer_0_11),
                   $isunknown(dut.u_core.outlinear.head_buffer_0_10),
                   $isunknown(dut.u_core.outlinear.head_buffer_0_9),
                   $isunknown(dut.u_core.outlinear.head_buffer_0_8),
                   $isunknown(dut.u_core.outlinear.head_buffer_0_7),
                   $isunknown(dut.u_core.outlinear.head_buffer_0_6),
                   $isunknown(dut.u_core.outlinear.head_buffer_0_5),
                   $isunknown(dut.u_core.outlinear.head_buffer_0_4),
                   $isunknown(dut.u_core.outlinear.head_buffer_0_3),
                   $isunknown(dut.u_core.outlinear.head_buffer_0_2),
                   $isunknown(dut.u_core.outlinear.head_buffer_0_1),
                   $isunknown(dut.u_core.outlinear.head_buffer_0_0)
                 },
                 dut.u_core.outlinear.head_buffer_0_0[7:0],
                 dut.u_core.outlinear.head_buffer_0_1[7:0],
                 dut.u_core.outlinear.head_buffer_0_2[7:0],
                 dut.u_core.outlinear.head_buffer_0_3[7:0],
                 dut.u_core.outlinear.head_buffer_0_4[7:0],
                 dut.u_core.outlinear.head_buffer_0_5[7:0],
                 dut.u_core.outlinear.head_buffer_0_11[7:0],
                 dut.u_core.outlinear.head_buffer_0_0[511:504],
                 dut.u_core.outlinear.head_buffer_0_1[511:504],
                 dut.u_core.outlinear.head_buffer_0_2[511:504],
                 dut.u_core.outlinear.head_buffer_0_3[511:504],
                 dut.u_core.outlinear.head_buffer_0_4[511:504],
                 dut.u_core.outlinear.head_buffer_0_5[511:504],
                 dut.u_core.outlinear.head_buffer_0_11[511:504]);
        out_headbuf_event_count <= out_headbuf_event_count + 1;
      end
      prev_outlinear_state <= dut.u_core.outlinear.state;

`ifdef ENABLE_CNN_CORE_TB_DEEP_DEBUG
      if ((dut.state == 5'd23) && (dut.run_token_idx >= 11'd52) &&
          ((cycle - run_entry_cycle) < 64'd256)) begin
        $display("cnn_core_tb run-trace cycle=%0d dt=%0d cfg_v=%0d cfg_prefill=%0d attn_cfg_v=%0d attn_prefill=%0d attn_sq=%0d ln_state=%0d ln_start=%0d ln_v=%0d ln_addr=%0d ln_last=%0d lnq_state=%0d lnq_w=%0d lnq_i=%0d lnq_tok=%0d ln_res_v=%0d ln_res_st=%0d qkv_v=%0d qkv_last=%0d q_lu_state=%0d q_lu_phase=%0d q_mem_full=%0d q_mem_rdy=%0d q_lu_v=%0d q_cu_v=%0d q_su_v=%0d attn_res_v=%0d attn_last=%0d out_v=%0d resadd_v=%0d ln2_v=%0d ffnup_v=%0d ffndown_v=%0d top_res_v=%0d top_res_last=%0d top_res_addr=%0d",
                 cycle,
                 cycle - run_entry_cycle,
                 dut.core_cfg_valid,
                 dut.core_cfg_prefill,
                 dut.core_attn_cfg_valid,
                 dut.core_attn_cfg_prefill,
                 dut.core_attn_cfg_single_query,
                 dut.u_core.ln_addr_gen.state,
                 dut.u_core.ln_addr_gen.start_pending,
                 dut.u_core._ln_addr_gen_io_data_valid,
                 dut.u_core._ln_addr_gen_io_data_addr,
                 dut.u_core._ln_addr_gen_io_data_last,
                 dut.u_core.layernorm.state,
                 dut.u_core.layernorm.weightsLoaded,
                 dut.u_core.layernorm.inputLoaded,
                 dut.u_core.layernorm.tokenCount,
                 dut.u_core._layernorm_io_res_valid,
                 dut.u_core._layernorm_io_res_st,
                 dut.u_core._qkvlinear_io_data_out_valid,
                 dut.u_core._qkvlinear_io_data_out_last,
                 dut.u_core.qkvlinear.lu_inst.state,
                 dut.u_core.qkvlinear.lu_inst.phaseCnt,
                 dut.u_core.qkvlinear.mem_inst.full_cnt_r,
                 dut.u_core.qkvlinear._mem_inst_io_r_ready,
                 dut.u_core.qkvlinear._lu_inst_io_data_out_valid,
                 dut.u_core.qkvlinear._cu_inst_io_data_out_valid,
                 dut.u_core._qkvlinear_io_data_out_valid,
                 dut.u_core._atten_io_res_valid,
                 dut.u_core._atten_io_res_last,
                 dut.u_core._outlinear_io_data_out_valid,
                 dut.u_core._resadd_io_res_valid,
                 dut.u_core._layernorm2_io_res_valid,
                 dut.u_core._ffnup_io_data_out_valid,
                 dut.u_core._ffndown_io_data_out_valid,
                 dut.u_core.io_res_valid,
                 dut.u_core.io_res_last,
                 dut.u_core.io_res_addr);
      end

      if (runtime_debug_window(dut.state) &&
          (dut.run_token_idx == 11'd3) &&
          (token3_qkv_event_count < 96) &&
          dut.u_core._qkvlinear_io_data_out_valid) begin
        $display("cnn_core_tb stage QKV cycle=%0d addr=%0d last=%0d token=%0d q_state=%0d q_prefill=%0d q_seqlen=%0d q_sq=%0d out_cnt=%0d prefill_cnt=%0d batch_cnt=%0d head_cnt=%0d su_v=%0d su_addr=%0d su_last=%0d cu_v=%0d lu_v=%0d attn_rdy=%0d attn_input_rdy=%0d dm1_rdy=%0d vcache_rdy=%0d attn_cfg_sq=%0d replay_active=%0d replay_v=%0d",
                 cycle,
                 dut.u_core._qkvlinear_io_data_out_addr,
                 dut.u_core._qkvlinear_io_data_out_last,
                 dut.run_token_idx,
                 dut.u_core.qkvlinear.state,
                 dut.u_core.qkvlinear.is_prefill,
                 dut.u_core.qkvlinear.seqlen,
                 dut.u_core.qkvlinear.is_single_query,
                 dut.u_core.qkvlinear.output_cnt_r,
                 dut.u_core.qkvlinear.prefill_cnt_r,
                 dut.u_core.qkvlinear.batch_cnt_r,
                 dut.u_core.qkvlinear.head_cnt_r,
                 dut.u_core._qkvlinear_io_data_out_valid,
                 dut.u_core._qkvlinear_io_data_out_addr,
                 dut.u_core._qkvlinear_io_data_out_last,
                 dut.u_core.qkvlinear._cu_inst_io_data_out_valid,
                 dut.u_core.qkvlinear._lu_inst_io_data_out_valid,
                 dut.u_core._atten_io_data_ready,
                 dut.u_core.atten.input_ready,
                 dut.u_core.atten._dm1_io_data_ready,
                 dut.u_core.atten._vcache_io_data_in_ready,
                 dut.u_core.atten.cfgSingleQuery,
                 dut.replay_active,
                 dut.replay_v_send_pending);
        token3_qkv_event_count = token3_qkv_event_count + 1;
      end

      if (runtime_debug_window(dut.state) &&
          (dut.run_token_idx >= 11'd52) &&
          stage_event_count < 128) begin
        if (dut.u_core._layernorm_io_res_valid) begin
          $display("cnn_core_tb stage LNRES cycle=%0d addr=%0d last=%0d token=%0d",
                   cycle, dut.u_core._layernorm_io_res_addr, dut.u_core._layernorm_io_res_last, dut.run_token_idx);
          stage_event_count = stage_event_count + 1;
        end
        if (dut.u_core._qkvlinear_io_data_out_valid) begin
          if (qkv_stage_event_count < 96) begin
          $display("cnn_core_tb stage QKV cycle=%0d addr=%0d last=%0d token=%0d q_state=%0d q_prefill=%0d q_seqlen=%0d q_sq=%0d out_cnt=%0d prefill_cnt=%0d batch_cnt=%0d head_cnt=%0d su_v=%0d su_addr=%0d su_last=%0d cu_v=%0d lu_v=%0d attn_rdy=%0d attn_input_rdy=%0d dm1_rdy=%0d vcache_rdy=%0d attn_cfg_sq=%0d replay_active=%0d replay_v=%0d",
                   cycle,
                   dut.u_core._qkvlinear_io_data_out_addr,
                   dut.u_core._qkvlinear_io_data_out_last,
                   dut.run_token_idx,
                   dut.u_core.qkvlinear.state,
                   dut.u_core.qkvlinear.is_prefill,
                   dut.u_core.qkvlinear.seqlen,
                   dut.u_core.qkvlinear.is_single_query,
                   dut.u_core.qkvlinear.output_cnt_r,
                   dut.u_core.qkvlinear.prefill_cnt_r,
                   dut.u_core.qkvlinear.batch_cnt_r,
                   dut.u_core.qkvlinear.head_cnt_r,
                   dut.u_core._qkvlinear_io_data_out_valid,
                   dut.u_core._qkvlinear_io_data_out_addr,
                   dut.u_core._qkvlinear_io_data_out_last,
                   dut.u_core.qkvlinear._cu_inst_io_data_out_valid,
                   dut.u_core.qkvlinear._lu_inst_io_data_out_valid,
                   dut.u_core._atten_io_data_ready,
                   dut.u_core.atten.input_ready,
                   dut.u_core.atten._dm1_io_data_ready,
                   dut.u_core.atten._vcache_io_data_in_ready,
                   dut.u_core.atten.cfgSingleQuery,
                   dut.replay_active,
                   dut.replay_v_send_pending);
            qkv_stage_event_count = qkv_stage_event_count + 1;
            stage_event_count = stage_event_count + 1;
          end
        end
        if (((dut.run_token_idx == 11'd1) || (dut.run_token_idx == 11'd2)) && (token1_focus_event_count < 96) &&
            (dut.u_core._layernorm_io_res_valid ||
             dut.u_core._qkvlinear_io_data_out_valid ||
             dut.u_core._atten_io_res_valid ||
             dut.u_core.outlinear._lu_inst_io_data_out_valid ||
             dut.u_core.outlinear._cu_inst_io_data_out_valid ||
             dut.u_core.outlinear._lw_inst_io_data_out_valid ||
             dut.u_core._outlinear_io_data_out_valid ||
             dut.u_core._resadd_io_res_valid ||
             dut.u_core._layernorm2_io_res_valid ||
             dut.u_core._ffnup_io_data_out_valid ||
             dut.u_core._ffndown_io_data_out_valid ||
             dut.u_core.io_res_valid)) begin
          $display("cnn_core_tb token-focus cycle=%0d run_token=%0d ln_v=%0d ln_st=%0d ln_addr=%0d ln_last=%0d qkv_v=%0d qkv_addr=%0d qkv_last=%0d q_state=%0d q_prefill=%0d q_seqlen=%0d q_sq=%0d q_head=%0d q_mem_full=%0d q_mem_rdy=%0d q_lu_state=%0d q_lu_phase=%0d q_lu_v=%0d q_cu_v=%0d q_su_v=%0d attn_in_rdy=%0d dm1_rdy=%0d attn_v=%0d attn_last=%0d out_state=%0d out_head=%0d out_feed_tok=%0d out_feed_chunk=%0d out_mem_full=%0d out_mem_busy=%0d out_mem_w_rdy=%0d out_mem_r_rdy=%0d out_lu_state=%0d out_lu_v=%0d out_cu_v=%0d out_w_v=%0d out_w_update=%0d out_v=%0d out_addr=%0d out_last=%0d resadd_v=%0d resadd_addr=%0d resadd_last=%0d ln2_v=%0d ln2_addr=%0d ln2_last=%0d ffnup_v=%0d ffnup_addr=%0d ffnup_last=%0d ffndown_v=%0d ffndown_addr=%0d ffndown_last=%0d top_v=%0d top_addr=%0d top_last=%0d",
                   cycle,
                   dut.run_token_idx,
                   dut.u_core._layernorm_io_res_valid,
                   dut.u_core._layernorm_io_res_st,
                   dut.u_core._layernorm_io_res_addr,
                   dut.u_core._layernorm_io_res_last,
                   dut.u_core._qkvlinear_io_data_out_valid,
                   dut.u_core._qkvlinear_io_data_out_addr,
                   dut.u_core._qkvlinear_io_data_out_last,
                   dut.u_core.qkvlinear.state,
                   dut.u_core.qkvlinear.is_prefill,
                   dut.u_core.qkvlinear.seqlen,
                   dut.u_core.qkvlinear.is_single_query,
                   dut.u_core.qkvlinear.head_cnt_r,
                   dut.u_core.qkvlinear.mem_inst.full_cnt_r,
                   dut.u_core.qkvlinear._mem_inst_io_r_ready,
                   dut.u_core.qkvlinear.lu_inst.state,
                   dut.u_core.qkvlinear.lu_inst.phaseCnt,
                   dut.u_core.qkvlinear._lu_inst_io_data_out_valid,
                   dut.u_core.qkvlinear._cu_inst_io_data_out_valid,
                   dut.u_core._qkvlinear_io_data_out_valid,
                   dut.u_core.atten.input_ready,
                   dut.u_core.atten._dm1_io_data_ready,
                   dut.u_core._atten_io_res_valid,
                   dut.u_core._atten_io_res_last,
                   dut.u_core.outlinear.state,
                   dut.u_core.outlinear.head_cnt,
                   dut.u_core.outlinear.feed_token_cnt,
                   dut.u_core.outlinear.feed_chunk_cnt,
                   dut.u_core.outlinear.mem_inst.full_cnt,
                   dut.u_core.outlinear.mem_inst.buzy_cnt,
                   dut.u_core.outlinear._mem_inst_io_w_ready,
                   dut.u_core.outlinear._mem_inst_io_r_ready,
                   dut.u_core.outlinear.lu_inst.state,
                   dut.u_core.outlinear._lu_inst_io_data_out_valid,
                   dut.u_core.outlinear._cu_inst_io_data_out_valid,
                   dut.u_core.outlinear._lw_inst_io_data_out_valid,
                   dut.u_core.outlinear._cu_inst_io_w_update,
                   dut.u_core._outlinear_io_data_out_valid,
                   dut.u_core._outlinear_io_data_out_addr,
                   dut.u_core._outlinear_io_data_out_last,
                   dut.u_core._resadd_io_res_valid,
                   dut.u_core._resadd_io_res_addr,
                   dut.u_core._resadd_io_res_last,
                   dut.u_core._layernorm2_io_res_valid,
                   dut.u_core._layernorm2_io_res_addr,
                   dut.u_core._layernorm2_io_res_last,
                   dut.u_core._ffnup_io_data_out_valid,
                   dut.u_core._ffnup_io_data_out_addr,
                   dut.u_core._ffnup_io_data_out_last,
                   dut.u_core._ffndown_io_data_out_valid,
                   dut.u_core._ffndown_io_data_out_addr,
                   dut.u_core._ffndown_io_data_out_last,
                   dut.u_core.io_res_valid,
                   dut.u_core.io_res_addr,
                   dut.u_core.io_res_last);
          token1_focus_event_count = token1_focus_event_count + 1;
        end
        if (((dut.run_token_idx == 11'd1) || (dut.run_token_idx == 11'd2)) &&
            (token1_qkv_collect_event_count < 160) &&
            (dut.u_core.qkvlinear.collectWriteEnableReg ||
             dut.u_core._qkvlinear_io_data_out_valid ||
             dut.u_core._qkvlinear_io_data_out_valid ||
             dut.core_attn_tap_valid)) begin
          $display("cnn_core_tb token-qkv cycle=%0d run_token=%0d q_state=%0d q_head=%0d q_out_cnt=%0d q_prefill_cnt=%0d q_batch_cnt=%0d su_v=%0d su_addr=%0d su_last=%0d collect_w=%0d collect_tok=%0d collect_vec=%0d collect_b0=0x%02h collect_b11=0x%02h vb0_b0=0x%02h vb1_b0=0x%02h vb2_b0=0x%02h vb64_b0=0x%02h vb65_b0=0x%02h vb66_b0=0x%02h vb128_b0=0x%02h vb129_b0=0x%02h vb130_b0=0x%02h vb189_b0=0x%02h vb190_b0=0x%02h vb191_b0=0x%02h qout_v=%0d qout_addr=%0d qout_last=%0d tap_v=%0d tap_head=%0d tap_addr=%0d tap_last=%0d tap_b0=0x%02h tap_b5=0x%02h attn_in_rdy=%0d dm1_rdy=%0d replay_active=%0d replay_v=%0d",
                   cycle,
                   dut.run_token_idx,
                   dut.u_core.qkvlinear.state,
                   dut.u_core.qkvlinear.head_cnt_r,
                   dut.u_core.qkvlinear.output_cnt_r,
                   dut.u_core.qkvlinear.prefill_cnt_r,
                   dut.u_core.qkvlinear.batch_cnt_r,
                   dut.u_core._qkvlinear_io_data_out_valid,
                   dut.u_core._qkvlinear_io_data_out_addr,
                   dut.u_core._qkvlinear_io_data_out_last,
                   dut.u_core.qkvlinear.collectWriteEnableReg,
                   dut.u_core.qkvlinear.collectTokenReg,
                   dut.u_core.qkvlinear.collectVecReg,
                   dut.u_core.qkvlinear.collectDataReg[7:0],
                   dut.u_core.qkvlinear.collectDataReg[95:88],
                   dut.u_core.qkvlinear.vec_buffer_0_0[7:0],
                   dut.u_core.qkvlinear.vec_buffer_0_1[7:0],
                   dut.u_core.qkvlinear.vec_buffer_0_2[7:0],
                   dut.u_core.qkvlinear.vec_buffer_0_64[7:0],
                   dut.u_core.qkvlinear.vec_buffer_0_65[7:0],
                   dut.u_core.qkvlinear.vec_buffer_0_66[7:0],
                   dut.u_core.qkvlinear.vec_buffer_0_128[7:0],
                   dut.u_core.qkvlinear.vec_buffer_0_129[7:0],
                   dut.u_core.qkvlinear.vec_buffer_0_130[7:0],
                   dut.u_core.qkvlinear.vec_buffer_0_189[7:0],
                   dut.u_core.qkvlinear.vec_buffer_0_190[7:0],
                   dut.u_core.qkvlinear.vec_buffer_0_191[7:0],
                   dut.u_core._qkvlinear_io_data_out_valid,
                   dut.u_core._qkvlinear_io_data_out_addr,
                   dut.u_core._qkvlinear_io_data_out_last,
                   dut.core_attn_tap_valid,
                   dut.core_attn_tap_head,
                   dut.core_attn_tap_addr,
                   dut.core_attn_tap_last,
                   dut.core_attn_tap_data[7:0],
                   dut.core_attn_tap_data[47:40],
                   dut.u_core.atten.input_ready,
                   dut.u_core.atten._dm1_io_data_ready,
                   dut.replay_active,
                   dut.replay_v_send_pending);
          token1_qkv_collect_event_count = token1_qkv_collect_event_count + 1;
        end
        if ((dut.run_token_idx == 11'd2) &&
            (token2_front_event_count < 160) &&
            ((cycle - run_entry_cycle) < 12'd512) &&
            (((cycle - run_entry_cycle) % 8) == 0)) begin
          $display("cnn_core_tb token2-front cycle=%0d run_token=%0d dt=%0d ln_state=%0d ln_start_pending=%0d ln_data_v=%0d ln_data_addr=%0d ln_data_last=%0d ln_mem_addr=%0d ln_fire_ready=%0d ln_adapter_ready=%0d ln_res_v=%0d ln_res_addr=%0d q_state=%0d q_v=%0d q_addr=%0d q_last=%0d q_head=%0d attn_in_rdy=%0d dm1_rdy=%0d core_cfg_v=%0d core_attn_cfg_v=%0d cfg_sq=%0d q_prefill=%0d q_seqlen=%0d",
                   cycle,
                   dut.run_token_idx,
                   cycle - run_entry_cycle,
                   dut.u_core.ln_addr_gen.state,
                   dut.u_core.ln_addr_gen.start_pending,
                   dut.u_core._ln_addr_gen_io_data_valid,
                   dut.u_core._ln_addr_gen_io_data_addr,
                   dut.u_core._ln_addr_gen_io_data_last,
                   dut.u_core._ln_addr_gen_io_mem_addr,
                   dut.u_core._layernorm_io_data_ready,
                   dut.u_core._layernorm_io_data_ready & dut.u_core._resadd_io_orig_ready,
                   dut.u_core._layernorm_io_res_valid,
                   dut.u_core._layernorm_io_res_addr,
                   dut.u_core.qkvlinear.state,
                   dut.u_core._qkvlinear_io_data_out_valid,
                   dut.u_core._qkvlinear_io_data_out_addr,
                   dut.u_core._qkvlinear_io_data_out_last,
                   dut.u_core.qkvlinear.head_cnt_r,
                   dut.u_core.atten.input_ready,
                   dut.u_core.atten._dm1_io_data_ready,
                   dut.core_cfg_valid,
                   dut.core_attn_cfg_valid,
                   dut.u_core.atten.cfgSingleQuery,
                   dut.u_core.qkvlinear.is_prefill,
                   dut.u_core.qkvlinear.seqlen);
          token2_front_event_count = token2_front_event_count + 1;
        end
        if (1'b0 && (token1_resadd_event_count < 256) && dut.u_core._resadd_io_res_valid) begin
          $display("cnn_core_tb resadd-trace cycle=%0d run_token=%0d addr=%0d last=%0d res_x=%0d orig_x=%0d dm2_x=%0d orig_rdy=%0d dm2_rdy=%0d mem_full=%0d mem_busy=%0d mem_rrdy=%0d ln2_rdy=%0d ln2_state=%0d",
                   cycle,
                   dut.run_token_idx,
                   dut.u_core._resadd_io_res_addr,
                   dut.u_core._resadd_io_res_last,
                   $isunknown(dut.u_core._resadd_io_res),
                   $isunknown(dut.u_core.resadd._mem_io_r_data),
                   $isunknown(dut.u_core.resadd.dm2_data_r),
                   dut.u_core._resadd_io_orig_ready,
                   dut.u_core._resadd_io_dm2_ready,
                   dut.u_core.resadd.mem.full_cnt,
                   dut.u_core.resadd.mem.buzy_cnt,
                   dut.u_core.resadd._mem_io_r_ready,
                   dut.u_core._layernorm2_io_data_ready,
                   dut.u_core.layernorm2.state);
          token1_resadd_event_count = token1_resadd_event_count + 1;
        end
        if (dut.u_core._atten_io_res_valid) begin
          $display("cnn_core_tb stage ATTN cycle=%0d addr=%0d last=%0d token=%0d out_state=%0d out_head=%0d out_feed_tok=%0d out_feed_chunk=%0d out_mem_full=%0d out_mem_busy=%0d out_mem_w_rdy=%0d out_mem_r_rdy=%0d out_lu_state=%0d out_lu_v=%0d out_cu_v=%0d out_v=%0d",
                   cycle,
                   dut.u_core._atten_io_res_addr,
                   dut.u_core._atten_io_res_last,
                   dut.run_token_idx,
                   dut.u_core.outlinear.state,
                   dut.u_core.outlinear.head_cnt,
                   dut.u_core.outlinear.feed_token_cnt,
                   dut.u_core.outlinear.feed_chunk_cnt,
                   dut.u_core.outlinear.mem_inst.full_cnt,
                   dut.u_core.outlinear.mem_inst.buzy_cnt,
                   dut.u_core.outlinear._mem_inst_io_w_ready,
                   dut.u_core.outlinear._mem_inst_io_r_ready,
                   dut.u_core.outlinear.lu_inst.state,
                   dut.u_core.outlinear._lu_inst_io_data_out_valid,
                   dut.u_core.outlinear._cu_inst_io_data_out_valid,
                   dut.u_core._outlinear_io_data_out_valid);
          stage_event_count = stage_event_count + 1;
        end
        if (dut.u_core._outlinear_io_data_out_valid) begin
          $display("cnn_core_tb stage OUT cycle=%0d addr=%0d last=%0d token=%0d",
                   cycle, dut.u_core._outlinear_io_data_out_addr, dut.u_core._outlinear_io_data_out_last, dut.run_token_idx);
          stage_event_count = stage_event_count + 1;
        end
        if (dut.u_core._resadd_io_res_valid) begin
          $display("cnn_core_tb stage RESADD cycle=%0d addr=%0d last=%0d token=%0d",
                   cycle, dut.u_core._resadd_io_res_addr, dut.u_core._resadd_io_res_last, dut.run_token_idx);
          stage_event_count = stage_event_count + 1;
        end
        if (dut.u_core._layernorm2_io_res_valid) begin
          $display("cnn_core_tb stage LN2 cycle=%0d addr=%0d last=%0d token=%0d",
                   cycle, dut.u_core._layernorm2_io_res_addr, dut.u_core._layernorm2_io_res_last, dut.run_token_idx);
          stage_event_count = stage_event_count + 1;
        end
        if (dut.u_core._ffnup_io_data_out_valid) begin
          $display("cnn_core_tb stage FFNUP cycle=%0d addr=%0d last=%0d token=%0d",
                   cycle, dut.u_core._ffnup_io_data_out_addr, dut.u_core._ffnup_io_data_out_last, dut.run_token_idx);
          stage_event_count = stage_event_count + 1;
        end
        if (dut.u_core._ffndown_io_data_out_valid) begin
          $display("cnn_core_tb stage FFNDOWN cycle=%0d addr=%0d last=%0d token=%0d",
                   cycle, dut.u_core._ffndown_io_data_out_addr, dut.u_core._ffndown_io_data_out_last, dut.run_token_idx);
          stage_event_count = stage_event_count + 1;
        end
        if (dut.u_core.io_res_valid) begin
          $display("cnn_core_tb stage TOPRES cycle=%0d addr=%0d last=%0d token=%0d",
                   cycle, dut.u_core.io_res_addr, dut.u_core.io_res_last, dut.run_token_idx);
          stage_event_count = stage_event_count + 1;
        end
      end

      if (runtime_debug_window(dut.state) && (token1_resadd_event_count < 256) &&
          dut.u_core._resadd_io_res_valid &&
          ((dut.run_token_idx >= 11'd52) || $isunknown(dut.u_core._resadd_io_res))) begin
        $display("cnn_core_tb resadd-trace cycle=%0d run_token=%0d addr=%0d last=%0d res_x=%0d orig_x=%0d dm2_x=%0d orig_rdy=%0d dm2_rdy=%0d mem_full=%0d mem_busy=%0d mem_rrdy=%0d ln2_rdy=%0d ln2_state=%0d",
                 cycle,
                 dut.run_token_idx,
                 dut.u_core._resadd_io_res_addr,
                 dut.u_core._resadd_io_res_last,
                 $isunknown(dut.u_core._resadd_io_res),
                 $isunknown(dut.u_core.resadd._mem_io_r_data),
                 $isunknown(dut.u_core.resadd.dm2_data_r),
                 dut.u_core._resadd_io_orig_ready,
                 dut.u_core._resadd_io_dm2_ready,
                 dut.u_core.resadd.mem.full_cnt,
                 dut.u_core.resadd.mem.buzy_cnt,
                 dut.u_core.resadd._mem_io_r_ready,
                 dut.u_core._layernorm2_io_data_ready,
                 dut.u_core.layernorm2.state);
        token1_resadd_event_count = token1_resadd_event_count + 1;
      end

      if (runtime_debug_window(dut.state) && dut.core_attn_tap_valid && debug_event_count < 64) begin
        $display("cnn_core_tb event TAP cycle=%0d head=%0d addr=%0d last=%0d state=%0d token=%0d",
                 cycle, dut.core_attn_tap_head, dut.core_attn_tap_addr, dut.core_attn_tap_last, dut.state, dut.run_token_idx);
        debug_event_count = debug_event_count + 1;
      end
      if (runtime_debug_window(dut.state) && dut.core_res_valid && debug_event_count < 64) begin
        $display("cnn_core_tb event RES cycle=%0d addr=%0d last=%0d state=%0d token=%0d",
                 cycle, dut.core_res_addr, dut.core_res_last, dut.state, dut.run_token_idx);
        debug_event_count = debug_event_count + 1;
      end
`endif
    end
  end

  initial begin
    $dumpfile("tb_startup.vcd");
    $dumpvars(0, c0_ddr4_s_axi_clk);
    $dumpvars(0, user_rst);
    $dumpvars(0, sys_rst_n);
    $dumpvars(0, c0_ddr4_s_axi_rst_n);
    $dumpvars(0, c0_init_calib_complete);
    $dumpvars(0, cfg_data_valid);
    $dumpvars(0, cfg_done);
    $dumpvars(0, cnn0_input_batch_set);
    $dumpvars(0, cnn0_result_count);
    $dumpvars(0, c0_ddr4_s_axi_arvalid);
    $dumpvars(0, c0_ddr4_s_axi_arready);
    $dumpvars(0, c0_ddr4_s_axi_rvalid);
    $dumpvars(0, c0_ddr4_s_axi_rready);
    $dumpvars(0, rd_active);
    $dumpvars(0, rd_latency);
    $dumpvars(0, dut.state);
    $dumpvars(0, dut.result_done);
    $dumpvars(0, dut.cfg_loaded);
    $dumpvars(0, dut.issue_count);
    $dumpvars(0, dut.recv_count);
    if (!$value$plusargs("window_dir=%s", window_dir)) begin
      fatal_msg("usage: simv +window_dir=<window_dir>");
    end

    cfg_path = {window_dir, "/window.cfg"};
    ddr_path = {window_dir, "/artifacts/ddr_image.u32.bin"};
    golden_path = {window_dir, "/artifacts/golden.u32.bin"};

    cfg_data = '0;
    cfg_data_valid = 1'b0;
    cfg_done = 1'b0;
    cnn0_input_batch_set = 1'b0;
    cnn0_result_batch_clear = 1'b0;
    cycle = 64'd0;
    progress_count = 0;
    tb_debug_enable = $test$plusargs("TB_DEBUG");
    debug_event_count = 0;
    qkv_stage_event_count = 0;
    token1_focus_event_count = 0;
    token1_qkv_collect_event_count = 0;
    token2_front_event_count = 0;
    out_token1_event_count = 0;
    out_cu_event_count = 0;
    out_lu_trace_count = 0;
    tap_trace_count = 0;
    hist_write_trace_count = 0;
    hist_read_trace_count = 0;
    trace_fd = $fopen("tb_trace.log", "w");
    if (trace_fd == 0) begin
      $display("cnn_core_tb WARN failed to open tb_trace.log");
    end
    if (trace_fd != 0) begin
      $fdisplay(trace_fd, "TRACE start t=%0t", $time);
      $fflush(trace_fd);
    end

    load_window_cfg(cfg_path);
    load_words_from_bin(ddr_path, ddr_image_words, ddr_word_count);
    load_golden_from_bin(golden_path, golden_words, golden_word_count);
    input_base_addr_u64 = C0_BASE_ADDR;
    output_base_addr_u64 = C0_BASE_ADDR + (((ddr_word_count + 15) / 16) * 64);
    load_mem_image();
    pack_cfg_data();

    #80.001;
    if (trace_fd != 0) begin
      $fdisplay(trace_fd, "TRACE checkpoint reset_hold t=%0t result_count=%b state=%h result_done=%b",
                $time, cnn0_result_count, dut.state, dut.result_done);
      $fflush(trace_fd);
    end
    $display("cnn_core_tb checkpoint reset_hold t=%0t result_count=%b state=%h result_done=%b",
             $time, cnn0_result_count, dut.state, dut.result_done);
    if ($isunknown(cnn0_result_count)) begin
      fatal_msg($sformatf("cnn0_result_count unknown while reset asserted t=%0t state=0x%0h result_done=%0b",
                          $time, dut.state, dut.result_done));
    end
    user_rst = 1'b0;
    sys_rst_n = 1'b1;
    c0_ddr4_s_axi_rst_n = 1'b1;
    #80.001;
    if (trace_fd != 0) begin
      $fdisplay(trace_fd, "TRACE checkpoint reset_release t=%0t result_count=%b state=%h result_done=%b",
                $time, cnn0_result_count, dut.state, dut.result_done);
      $fflush(trace_fd);
    end
    $display("cnn_core_tb checkpoint reset_release t=%0t result_count=%b state=%h result_done=%b",
             $time, cnn0_result_count, dut.state, dut.result_done);
    if ($isunknown(cnn0_result_count)) begin
      fatal_msg($sformatf("cnn0_result_count unknown after reset release t=%0t state=0x%0h result_done=%0b",
                          $time, dut.state, dut.result_done));
    end
    c0_init_calib_complete = 1'b1;
    #4.001;
    if (trace_fd != 0) begin
      $fdisplay(trace_fd, "TRACE checkpoint calib t=%0t result_count=%b state=%h result_done=%b cfg_loaded=%b",
                $time, cnn0_result_count, dut.state, dut.result_done, dut.cfg_loaded);
      $fflush(trace_fd);
    end
    $display("cnn_core_tb checkpoint calib t=%0t result_count=%b state=%h result_done=%b cfg_loaded=%b",
             $time, cnn0_result_count, dut.state, dut.result_done, dut.cfg_loaded);
    if ($isunknown(cnn0_result_count)) begin
      fatal_msg($sformatf("cnn0_result_count unknown after calib t=%0t state=0x%0h result_done=%0b",
                          $time, dut.state, dut.result_done));
    end

    cfg_data_valid <= 1'b1;
    cfg_done <= 1'b1;
    #4.001;
    cfg_data_valid <= 1'b0;
    cfg_done <= 1'b0;

    #16.001;
    cnn0_input_batch_set <= 1'b1;
    #4.001;
    cnn0_input_batch_set <= 1'b0;
    if (trace_fd != 0) begin
      $fdisplay(trace_fd, "TRACE checkpoint before_wait t=%0t result_count=%b state=%h result_done=%b cfg_loaded=%b",
                $time, cnn0_result_count, dut.state, dut.result_done, dut.cfg_loaded);
      $fflush(trace_fd);
    end
    $display("cnn_core_tb checkpoint before_wait t=%0t result_count=%b state=%h result_done=%b cfg_loaded=%b",
             $time, cnn0_result_count, dut.state, dut.result_done, dut.cfg_loaded);
    while ((cnn0_result_count !== 3'd1) && (cycle < MAX_CYCLES)) begin
      #4.001;
      cycle <= cycle + 64'd1;
      if ((cycle != 0) && ((cycle % 64'd256) == 0) && (cycle <= 64'd4096)) begin
        $display("cnn_core_tb startup-step cycle=%0d state=%0d issue=%0d recv=%0d rd_active=%0d rd_latency=%0d ar[v=%0d r=%0d] r[v=%0d r=%0d]",
                 cycle, dut.state, dut.issue_count, dut.recv_count, rd_active, rd_latency,
                 c0_ddr4_s_axi_arvalid, c0_ddr4_s_axi_arready,
                 c0_ddr4_s_axi_rvalid, c0_ddr4_s_axi_rready);
      end
      if ((cycle % PROGRESS_CYCLES) == 0) begin
        progress_count = progress_count + 1;
        $display("cnn_core_tb progress cycle=%0d state=%0d layer=%0d token=%0d run_slot=%0d load_tok=%0d exec_tok=%0d store_tok=%0d busy=%0d done=%0d ar[v=%0d r=%0d a=0x%0h] r[v=%0d r=%0d id=%0d] aw[v=%0d r=%0d a=0x%0h] w[v=%0d r=%0d] b[v=%0d r=%0d]",
                 cycle,
                 dut.state,
                 dut.layer_idx,
                 dut.run_token_idx,
                 dut.run_slot_idx,
                 dut.load_token_idx,
                 dut.exec_token_idx,
                 dut.store_token_idx,
                 cnn0_batch_count[0],
                 cnn0_result_count[0],
                 c0_ddr4_s_axi_arvalid,
                 c0_ddr4_s_axi_arready,
                 c0_ddr4_s_axi_araddr,
                 c0_ddr4_s_axi_rvalid,
                 c0_ddr4_s_axi_rready,
                 c0_ddr4_s_axi_rid,
                 c0_ddr4_s_axi_awvalid,
                 c0_ddr4_s_axi_awready,
                 c0_ddr4_s_axi_awaddr,
                 c0_ddr4_s_axi_wvalid,
                 c0_ddr4_s_axi_wready,
                 c0_ddr4_s_axi_bvalid,
                 c0_ddr4_s_axi_bready);
        $display("cnn_core_tb runtime load_active=%0d load_slot=%0d load_issue=%0d load_recv=%0d store_active=%0d store_slot=%0d store_idx=%0d token_last_pending=%0d token_last_core_addr=%0d preload_wait=%0d full_wait=%0d",
                 dut.load_active,
                 dut.load_slot_idx,
                 dut.load_issue_count,
                 dut.load_recv_count,
                 dut.store_active,
                 dut.store_slot_idx,
                 dut.store_write_idx,
                 dut.token_last_pending,
                 dut.token_last_core_addr,
                 dut.preload_wait_cnt,
                 dut.preload_full_wait);
        $display("cnn_core_tb axird ar_hs=%0d r_hs=%0d rd_active=%0d rd_addr=0x%0h rd_id=%0d",
                 ar_hs_count,
                 r_hs_count,
                 rd_active,
                 rd_addr,
                 rd_id);
        $display("cnn_core_tb axiwr aw_hs=%0d w_hs=%0d b_emit=%0d b_hs=%0d wr_active=%0d wr_addr=0x%0h wr_id=%0d b_pending=%0d b_latency=%0d",
                 aw_hs_count,
                 w_hs_count,
                 b_emit_count,
                 b_hs_count,
                 wr_active,
                 wr_addr,
                 wr_id,
                 b_pending,
                 b_latency);
        $display("cnn_core_tb hist hist_state=%0d hist_busy=%0d kvh_head=%0d kvh_phase=%0d replay_rd_phase=%0d replay_active=%0d replay_done=%0d replay_v_pending=%0d replay_tok=%0d replay_head=%0d replay_beat=%0d rd_active=%0d rd_hist=%0d wr_hist=%0d wr_short=%0d kv_done=0x%03x",
                 dut.hist_state,
                 dut.hist_busy,
                 dut.kv_hist_write_head_idx,
                 dut.kv_hist_write_phase,
                 dut.replay_read_phase,
                 dut.replay_active,
                 dut.replay_done,
                 dut.replay_v_send_pending,
                 dut.replay_token_idx,
                 dut.replay_head_idx,
                 dut.replay_beat_idx,
                 dut.rd_active,
                 dut.rd_hist_active,
                 dut.wr_hist_active,
                 1'b0,
                 dut.kv_tap_head_done);
        $display("cnn_core_tb slots valid=%b loaded=%b exec_done=%b store_done=%b id0=%0d id1=%0d id2=%0d id3=%0d free_found=%0d exec_ready=%0d store_ready=%0d",
                 dut.token_slot_valid,
                 dut.token_slot_loaded,
                 dut.token_slot_exec_done,
                 1'b0,
                 dut.token_slot_id[0],
                 dut.token_slot_id[1],
                 dut.token_slot_id[2],
                 dut.token_slot_id[3],
                 dut.free_slot_found,
                 dut.exec_slot_ready,
                 dut.store_slot_ready);
        $display("cnn_core_tb core core_res_v=%0d core_res_last=%0d core_res_ready=%0d core_res_addr=%0d core_attn_tap_v=%0d core_attn_tap_last=%0d dm1_ov_v=%0d dm1_ov_rdy=%0d dm1_ov_x=%0d dm1_ov=0x%08h replay_q=0x%04h replay_k=0x%04h dm2v_ov_v=%0d dm2v_ov_rdy=%0d",
                 dut.core_res_valid,
                 dut.core_res_last,
                 dut.core_res_ready,
                 dut.core_res_addr,
                 dut.core_attn_tap_valid,
                 dut.core_attn_tap_last,
                 dut.core_attn_dm1_override_valid,
                 dut.core_attn_dm1_override_ready,
                 $isunknown(dut.core_attn_dm1_override_data),
                 dut.core_attn_dm1_override_data,
                 dut.replay_q_beat,
                 dut.replay_k_beat,
                 dut.core_attn_dm2_v_override_valid,
                 dut.core_attn_dm2_v_override_ready);
        $display("cnn_core_tb top ln_addr_v=%0d ln_addr=%0d ln_last=%0d ln_rdy=%0d ln_res_v=%0d ln_res_last=%0d qkv_v=%0d qkv_last=%0d attn_rdy=%0d attn_res_v=%0d attn_res_last=%0d",
                 dut.u_core._ln_addr_gen_io_data_valid,
                 dut.u_core._ln_addr_gen_io_data_addr,
                 dut.u_core._ln_addr_gen_io_data_last,
                 dut.u_core._layernorm_io_data_ready,
                 dut.u_core._layernorm_io_res_valid,
                 dut.u_core._layernorm_io_res_last,
                 dut.u_core._qkvlinear_io_data_out_valid,
                 dut.u_core._qkvlinear_io_data_out_last,
                 dut.u_core._atten_io_data_ready,
                 dut.u_core._atten_io_res_valid,
                 dut.u_core._atten_io_res_last);
        $display("cnn_core_tb attn cfg_seqlen=%0d cfg_prefill=%0d cfg_sq=%0d dm1_rdy=%0d dm1_res_v=%0d dm1_res_last=%0d dm1_res_x=%0d dm1_b0=0x%08h dm1_b1=0x%08h dm1_b2=0x%08h dm1_cu_state=%0d dm1_compute_done=%0d dm1_row_done=%0d dm1_key_cnt=%0d dm1_prefill_q_cnt=%0d smx_head_st=%0d smx_started=%0d softmax_state=%0d softmax_res_v=%0d soft_w_x=%0d soft_w_lo=0x%08h soft_w_b0=%0d soft_tile_x=%0d soft_gmax_x=%0d soft_sum_x=%0d soft_sum=0x%09h soft_div_v=%0d soft_mask_addr=%0d soft_tiles=%0d dm2_ctx_rdy=%0d dm2_v_rdy=%0d dm2_res_v=%0d dm2_res_last=%0d dm2_state=%0d dm2_prefill=%0d dm2_sq=%0d dm2_seqlen=%0d dm2_tile_base=%0d dm2_tile_cnt=%0d dm2_waitctx_cnt=%0d dm2_mul_cnt=%0d ctxq_full=%0d ctxq_enq=%0d ctxq_deq=%0d vq_full=%0d vq_enq=%0d vq_deq=%0d vcache_res_v=%0d",
                 dut.u_core.atten.io_cfg_seqlen,
                 dut.u_core.atten.io_cfg_prefill,
                 dut.u_core.atten.cfgSingleQuery,
                 dut.u_core.atten._dm1_io_data_ready,
                 dut.u_core.atten._dm1_io_res_valid,
                 dut.u_core.atten._dm1_io_res_last,
                 $isunknown(dut.u_core.atten.dm1.io_res),
                 dut.u_core.atten.dm1.io_res[31:0],
                 dut.u_core.atten.dm1.io_res[63:32],
                 dut.u_core.atten.dm1.io_res[95:64],
                 dut.u_core.atten.dm1.cu_inst.state,
                 dut.u_core.atten.dm1.cu_inst.computeDone,
                 dut.u_core.atten.dm1.cu_inst.rowDone,
                 dut.u_core.atten.dm1.cu_inst.comp_key_cnt,
                 dut.u_core.atten.dm1.cu_inst.comp_prefill_q_cnt,
                 dut.u_core.atten.softmaxHeadStart,
                 1'b0,
                 dut.u_core.atten.softmax.state,
                 dut.u_core.atten._softmax_io_res_valid,
                 $isunknown(dut.u_core.atten.softmax.io_w_in),
                 dut.u_core.atten.softmax.io_w_in[31:0],
                 dut.u_core.atten.softmax.io_w_in[0],
                 $isunknown(dut.u_core.atten.softmax.passTileReg),
                 $isunknown(dut.u_core.atten.softmax.globalMaxReg),
                 $isunknown(dut.u_core.atten.softmax.sumExpReg),
                 dut.u_core.atten.softmax.sumExpReg,
                 dut.u_core.atten.softmax._recipDiv_io_outValidDiv,
                 dut.u_core.atten.softmax.maskAddrReg,
                 dut.u_core.atten.softmax.rowTileCountReg,
                 dut.u_core.atten._dm2_io_data_in_ctx_ready,
                 dut.u_core.atten._dm2_io_data_in_v_ready,
                 dut.u_core.atten.io_res_valid,
                 dut.u_core.atten.io_res_last,
                 dut.u_core.atten.dm2.dmInst.state,
                 dut.u_core.atten.dm2.dmInst.prefill,
                 dut.u_core.atten.dm2.dmInst.singleQuery,
                 dut.u_core.atten.dm2.dmInst.seqlen,
                 dut.u_core.atten.dm2.dmInst.tileBase,
                 dut.u_core.atten.dm2.dmInst.tileLoadCnt,
                 dut.u_core.atten.dm2.dmInst.waitctxCnt,
                 dut.u_core.atten.dm2.dmInst.mulCnt,
                 dut.u_core.atten.ctxToDm2Q.maybe_full,
                 dut.u_core.atten.ctxToDm2Q.enq_ptr_value,
                 dut.u_core.atten.ctxToDm2Q.deq_ptr_value,
                 dut.u_core.atten.vToDm2Q.maybe_full,
                 dut.u_core.atten.vToDm2Q.enq_ptr_value,
                 dut.u_core.atten.vToDm2Q.deq_ptr_value,
                 dut.u_core.atten._vcache_io_res_valid);
        $display("cnn_core_tb qkv q_state=%0d q_prefill=%0d q_seqlen=%0d q_sq=%0d q_out_cnt=%0d q_prefill_cnt=%0d q_batch_cnt=%0d q_head_cnt=%0d q_su_v=%0d q_su_addr=%0d q_su_last=%0d q_cu_v=%0d q_lu_v=%0d attn_rdy=%0d attn_input_rdy=%0d dm1_rdy=%0d vcache_rdy=%0d attn_cfg_sq=%0d replay_active=%0d replay_v=%0d",
                 dut.u_core.qkvlinear.state,
                 dut.u_core.qkvlinear.is_prefill,
                 dut.u_core.qkvlinear.seqlen,
                 dut.u_core.qkvlinear.is_single_query,
                 dut.u_core.qkvlinear.output_cnt_r,
                 dut.u_core.qkvlinear.prefill_cnt_r,
                 dut.u_core.qkvlinear.batch_cnt_r,
                 dut.u_core.qkvlinear.head_cnt_r,
                 dut.u_core._qkvlinear_io_data_out_valid,
                 dut.u_core._qkvlinear_io_data_out_addr,
                 dut.u_core._qkvlinear_io_data_out_last,
                 dut.u_core.qkvlinear._cu_inst_io_data_out_valid,
                 dut.u_core.qkvlinear._lu_inst_io_data_out_valid,
                 dut.u_core._atten_io_data_ready,
                 dut.u_core.atten.input_ready,
                 dut.u_core.atten._dm1_io_data_ready,
                 dut.u_core.atten._vcache_io_data_in_ready,
                 dut.u_core.atten.cfgSingleQuery,
                 dut.replay_active,
                 dut.replay_v_send_pending);
        $display("cnn_core_tb vcache vc_in_v=%0d vc_in_addr=%0d vc_in_last=%0d vc_rdy=%0d vc_res_v=%0d vc_res_st=%0d vc_res_last=%0d vc_res_addr=%0d vc_mem_full=%0d vc_mem_busy=%0d vc_wptr=%0d vc_rptr=%0d vc_lsu_state=%0d vc_vcnt=%0d vc_batch_cnt=%0d vc_prefill_cnt=%0d vq_enq_rdy=%0d vq_deq_v=%0d dm2_v_rdy=%0d vq_full=%0d vq_enq=%0d vq_deq=%0d",
                 dut.u_core.atten.vcache.io_data_in_valid,
                 dut.u_core.atten.vcache.io_data_in_addr,
                 dut.u_core.atten.vcache.io_data_in_last,
                 dut.u_core.atten._vcache_io_data_in_ready,
                 dut.u_core.atten._vcache_io_res_valid,
                 dut.u_core.atten._vcache_io_res_st,
                 dut.u_core.atten._vcache_io_res_last,
                 dut.u_core.atten._vcache_io_res_addr,
                 dut.u_core.atten.vcache.mem_inst.full_cnt,
                 dut.u_core.atten.vcache.mem_inst.buzy_cnt,
                 dut.u_core.atten.vcache.mem_inst.w_ptr,
                 dut.u_core.atten.vcache.mem_inst.r_ptr,
                 dut.u_core.atten.vcache.lsu_inst.state,
                 dut.u_core.atten.vcache.lsu_inst.v_cnt,
                 dut.u_core.atten.vcache.lsu_inst.batch_cnt,
                 dut.u_core.atten.vcache.lsu_inst.prefill_cnt,
                 dut.u_core.atten._vToDm2Q_io_enq_ready,
                 dut.u_core.atten._vToDm2Q_io_deq_valid,
                 dut.u_core.atten._dm2_io_data_in_v_ready,
                 dut.u_core.atten.vToDm2Q.maybe_full,
                 dut.u_core.atten.vToDm2Q.enq_ptr_value,
                 dut.u_core.atten.vToDm2Q.deq_ptr_value);
        $display("cnn_core_tb top0 ln_state=%0d ln_start_pending=%0d ln_prefill=%0d ln_seqlen=%0d adapter_rdy=%0d resadd_orig_rdy=%0d resadd_dm2_rdy=%0d lnq_state=%0d lnq_w_loaded=%0d lnq_i_loaded=%0d lnq_weight_cnt=%0d lnq_token_cnt=%0d lnq_sum=%h lnq_sqsum=%h lnq_meanMul=%h lnq_varAddEps=%h lnq_mean=%h lnq_var=%h lnq_sqrt_inV=%0d lnq_sqrt_ir=%0d lnq_sqrt_core_ov=%0d lnq_sqrt_ov=%0d lnq_sqrt_out=%h lnq_div_inV=%0d lnq_div_ir=%0d lnq_div_core_ov=%0d lnq_div_ov=%0d lnq_div_out=%h",
                 dut.u_core.ln_addr_gen.state,
                 dut.u_core.ln_addr_gen.start_pending,
                 dut.u_core.ln_addr_gen.is_prefill,
                 dut.u_core.ln_addr_gen.seqlen,
                 dut.u_core._layernorm_io_data_ready & dut.u_core._resadd_io_orig_ready,
                 dut.u_core._resadd_io_orig_ready,
                 dut.u_core._resadd_io_dm2_ready,
                 dut.u_core.layernorm.state,
                 dut.u_core.layernorm.weightsLoaded,
                 dut.u_core.layernorm.inputLoaded,
                 dut.u_core.layernorm.weightCnt,
                 dut.u_core.layernorm.tokenCount,
                 dut.u_core.layernorm.sumAcc,
                 dut.u_core.layernorm.sqSumAcc,
                 dut.u_core.layernorm._meanMul_io_out,
                 dut.u_core.layernorm._varAddEps_io_out,
                 dut.u_core.layernorm.meanReg,
                 dut.u_core.layernorm.varReg,
                 dut.u_core.layernorm.sqrt_io_inValid,
                 dut.u_core.layernorm._sqrt_io_inReady,
                 dut.u_core.layernorm.sqrt.sqrt._core_io_outValid,
                 dut.u_core.layernorm._sqrt_io_outValidSqrt,
                 dut.u_core.layernorm._sqrt_io_out,
                 dut.u_core.layernorm.div_io_inValid,
                 dut.u_core.layernorm._div_io_inReady,
                 dut.u_core.layernorm.div.div._core_io_outValid,
                 dut.u_core.layernorm._div_io_outValidDiv,
                 dut.u_core.layernorm._div_io_out);
        $display("cnn_core_tb top0stat vec=%0d statRe=%0d statV=%0d statF=%0d statL=%0d r0_x=%0d r0_lo=%h r0_hi=%h r1_x=%0d r1_lo=%h r1_hi=%h laneSum=%h laneSq=%h sumAdd=%h sqAdd=%h",
                 dut.u_core.layernorm.vecIdx,
                 dut.u_core.layernorm.statReadEn,
                 dut.u_core.layernorm.statValid,
                 dut.u_core.layernorm.statFirst,
                 dut.u_core.layernorm.statLast,
                 $isunknown(dut.u_core.layernorm._inputMem_ext_R0_data),
                 dut.u_core.layernorm._inputMem_ext_R0_data[31:0],
                 dut.u_core.layernorm._inputMem_ext_R0_data[383:352],
                 $isunknown(dut.u_core.layernorm._inputMem_ext_R1_data),
                 dut.u_core.layernorm._inputMem_ext_R1_data[31:0],
                 dut.u_core.layernorm._inputMem_ext_R1_data[383:352],
                 dut.u_core.layernorm._laneSum_io_out,
                 dut.u_core.layernorm._laneSqSum_io_out,
                 dut.u_core.layernorm._sumAdd_io_out,
                 dut.u_core.layernorm._sqAdd_io_out);
        $display("cnn_core_tb top2 out_state=%0d out_head=%0d out_feed_tok=%0d out_feed_chunk=%0d out_bypass=%0d out_pending=%0d out_pending_wait=%0d out_cfg_restart=%0d out_accept=%0d out_accept_x=%0d out_mem_w_rdy=%0d out_mem_r_rdy=%0d out_v=%0d out_last=%0d resadd_v=%0d resadd_last=%0d ln2_rdy=%0d ln2_state=%0d ln2_i_loaded=%0d ln2_tok_cnt=%0d ln2_tok_idx=%0d ln2_vec_idx=%0d ln2_var=0x%08h sqrt_ir=%0d sqrt_ov=%0d sqrt_out=0x%08h div_ir=%0d div_ov=%0d res2_s7_rdy=%0d ffnup_rdy=%0d ln2_v=%0d ln2_last=%0d ffnup_v=%0d ffnup_last=%0d ffndown_rdy=%0d ffndown_v=%0d ffndown_last=%0d",
                 dut.u_core.outlinear.state,
                 dut.u_core.outlinear.head_cnt,
                 dut.u_core.outlinear.feed_token_cnt,
                 dut.u_core.outlinear.feed_chunk_cnt,
                 dut.u_core.outlinear.bypassActive,
                 dut.u_core.outlinear.pendingFeed,
                 dut.u_core.outlinear.pendingFeedWait,
                 dut.u_core.outlinear.cfgRestartPending,
                 dut.u_core.outlinear.acceptReady,
                 $isunknown(dut.u_core.outlinear.acceptReady),
                 dut.u_core.outlinear._mem_inst_io_w_ready,
                 dut.u_core.outlinear._mem_inst_io_r_ready,
                 dut.u_core._outlinear_io_data_out_valid,
                 dut.u_core._outlinear_io_data_out_last,
                 dut.u_core._resadd_io_res_valid,
                 dut.u_core._resadd_io_res_last,
                 dut.u_core._layernorm2_io_data_ready,
                 dut.u_core.layernorm2.state,
                 dut.u_core.layernorm2.inputLoaded,
                 dut.u_core.layernorm2.tokenCount,
                 dut.u_core.layernorm2.tokenIdx,
                 dut.u_core.layernorm2.vecIdx,
                 dut.u_core.layernorm2.varReg,
                 dut.u_core.layernorm2.sqrt.io_inReady,
                 dut.u_core.layernorm2.sqrt.io_outValidSqrt,
                 dut.u_core.layernorm2.sqrt.io_out,
                 dut.u_core.layernorm2.div.io_inReady,
                 dut.u_core.layernorm2.div.io_outValidDiv,
                 dut.u_core._resadd2_io_s7_ready,
                 dut.u_core.ffnup.mem_inst.io_w_ready,
                 dut.u_core._layernorm2_io_res_valid,
                 dut.u_core._layernorm2_io_res_last,
                 dut.u_core._ffnup_io_data_out_valid,
                 dut.u_core._ffnup_io_data_out_last,
                 dut.u_core._ffndown_io_data_ready,
                 dut.u_core._ffndown_io_data_out_valid,
                 dut.u_core._ffndown_io_data_out_last);
        $display("cnn_core_tb outin aq_v=%0d aq_st=%0d aq_last=%0d aq_full=%0d aq_enq=%0d aq_deq=%0d out_in_v=%0d out_in_st=%0d out_in_last=%0d out_rdy=%0d out_rdy_x=%0d out_gap=%0d out_seen=%0d out_bypass=%0d out_pending=%0d out_pending_wait=%0d out_cfg_restart=%0d out_accept=%0d out_lu_re=%0d out_mem_rrdy=%0d dm2_dec_head=%0d",
                 dut.u_core._attnToOutQ_io_deq_valid,
                 dut.u_core._attnToOutQ_io_deq_bits_st,
                 dut.u_core._attnToOutQ_io_deq_bits_last,
                 dut.u_core.attnToOutQ.maybe_full,
                 dut.u_core.attnToOutQ.enq_ptr_value,
                 dut.u_core.attnToOutQ.deq_ptr_value,
                 dut.u_core.outlinear.io_data_in_valid,
                 dut.u_core.outlinear.io_data_in_st,
                 dut.u_core.outlinear.io_data_in_last,
                 dut.u_core._outlinear_io_data_ready,
                 $isunknown(dut.u_core._outlinear_io_data_ready),
                 dut.u_core.outlinear.awaitInputGap,
                 dut.u_core.outlinear.decodeBurstSeen,
                 dut.u_core.outlinear.bypassActive,
                 dut.u_core.outlinear.pendingFeed,
                 dut.u_core.outlinear.pendingFeedWait,
                 dut.u_core.outlinear.cfgRestartPending,
                 dut.u_core.outlinear.acceptReady,
                 dut.u_core.outlinear._lu_inst_io_read_en,
                 dut.u_core.outlinear._mem_inst_io_r_ready,
                 dut.u_core.atten.dm2.decodeHeadCnt);
        $display("cnn_core_tb top3 in_addr=%0d qkv_addr=%0d out_addr=%0d ffnup_addr=%0d ffndown_addr=%0d top_res_v=%0d top_res_last=%0d top_res_addr=%0d",
                 dut.core_data_in_addr,
                 0,
                 0,
                 0,
                 0,
                 dut.u_core.io_res_valid,
                 dut.u_core.io_res_last,
                 dut.u_core.io_res_addr);
        $display("cnn_core_tb cfg core_cfg_v=%0d core_prefill=%0d core_seqlen=%0d core_attn_cfg_v=%0d core_attn_prefill=%0d core_attn_seqlen=%0d core_attn_sq=%0d layer_st=%0d",
                 dut.core_cfg_valid,
                 dut.core_cfg_prefill,
                 dut.core_cfg_seqlen,
                 dut.core_attn_cfg_valid,
                 dut.core_attn_cfg_prefill,
                 dut.core_attn_cfg_seqlen,
                 dut.core_attn_cfg_single_query,
                 dut.core_layer_st);
        if (progress_count >= 4 && dut.state == 5'd23 && dut.run_token_idx == 16'd0) begin
          $display("cnn_core_tb stall-focus rd_addr=0x%0h wr_addr=0x%0h rd_id=%0d wr_id=%0d rd_latency=%0d b_pending=%0d b_latency=%0d",
                   rd_addr,
                   wr_addr,
                   rd_id,
                   wr_id,
                   rd_latency,
                   b_pending,
                   b_latency);
        end
      end
    end

    #100.001;
    if ($isunknown(cnn0_result_count)) begin
      fatal_msg($sformatf("cnn0_result_count unknown at end of run t=%0t state=0x%0h result_done=%0b cfg_loaded=%0b layer=%0d token=%0d",
                          $time, dut.state, dut.result_done, dut.cfg_loaded, dut.layer_idx, dut.run_token_idx));
    end
    if (cnn0_result_count == 3'd0) fatal_msg($sformatf("%s did not finish before cycle limit=%0d", `DUT_LABEL, MAX_CYCLES));
    check_outputs();
    $finish;
  end
endmodule
