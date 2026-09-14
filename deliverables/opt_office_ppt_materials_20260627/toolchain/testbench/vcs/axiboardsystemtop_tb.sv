`timescale 1ns/1ps

module AxiBoardSystemTop_tb;

  localparam int READ_ADDR_LATENCY = 10;
  localparam int WRITE_RESP_LATENCY = 8;
  localparam longint unsigned MAX_CYCLES = 64'd3000000000;
  localparam int MAX_DDR_BEATS = 300000;
  localparam int MAX_DDR_WORDS = MAX_DDR_BEATS * 16;
  localparam int MAX_GOLDEN_BEATS = 65536;
  localparam int MAX_GOLDEN_WORDS = MAX_GOLDEN_BEATS * 12;
  localparam int MAX_MEM_WORDS = MAX_DDR_WORDS + MAX_GOLDEN_BEATS * 16 + 4096;
  localparam int PROGRESS_CYCLES = 100000;
  localparam int XBAR_SI_SLOT = 2;
  localparam int XBAR_MI_C0 = 0;
  localparam int XBAR_MI_C1 = 1;
  localparam bit USE_CUSTOM_DDR_MODEL = 1;

  logic clock = 1'b0;
  logic c0_ui_clock = 1'b0;
  logic c1_ui_clock = 1'b0;
  logic c0_ui_clk_sync_rst;
  logic c1_ui_clk_sync_rst;
  logic c0_init_calib_complete;
  logic c1_init_calib_complete;
  logic c0_dbg_clk;
  logic c1_dbg_clk;
  logic [511:0] c0_dbg_bus;
  logic [511:0] c1_dbg_bus;
  logic c0_ddr4_interrupt;
  logic c1_ddr4_interrupt;
  logic c0_sys_clk_p = 1'b0;
  logic c0_sys_clk_n = 1'b1;
  logic c1_sys_clk_p = 1'b0;
  logic c1_sys_clk_n = 1'b1;
  logic reset = 1'b1;

  logic [0:0] c0_interconnect_aresetn;
  logic [0:0] c1_interconnect_aresetn;
  logic [0:0] c0_bus_struct_reset;
  logic [0:0] c1_bus_struct_reset;
  logic [0:0] c0_peripheral_reset;
  logic [0:0] c1_peripheral_reset;
  logic [0:0] c0_peripheral_aresetn;
  logic [0:0] c1_peripheral_aresetn;
  logic c0_mb_reset;
  logic c1_mb_reset;
  wire c0_axi_aresetn = USE_CUSTOM_DDR_MODEL ? ~reset : c0_interconnect_aresetn[0];
  wire c1_axi_aresetn = USE_CUSTOM_DDR_MODEL ? ~reset : c1_interconnect_aresetn[0];

  wire              c0_ddr4_act_n;
  wire [16:0]       c0_ddr4_adr;
  wire [1:0]        c0_ddr4_ba;
  wire [1:0]        c0_ddr4_bg;
  wire [1:0]        c0_ddr4_cke;
  wire [1:0]        c0_ddr4_odt;
  wire [1:0]        c0_ddr4_cs_n;
  wire [0:0]        c0_ddr4_ck_t;
  wire [0:0]        c0_ddr4_ck_c;
  wire              c0_ddr4_reset_n;
  wire              c0_ddr4_parity;
  tri1 [8:0]        c0_ddr4_dm_dbi_n;
  tri [71:0]        c0_ddr4_dq;
  tri [17:0]        c0_ddr4_dqs_c;
  tri [17:0]        c0_ddr4_dqs_t;
  tri1              c0_ddr4_alert_n;

  wire              c1_ddr4_act_n;
  wire [16:0]       c1_ddr4_adr;
  wire [1:0]        c1_ddr4_ba;
  wire [1:0]        c1_ddr4_bg;
  wire [1:0]        c1_ddr4_cke;
  wire [1:0]        c1_ddr4_odt;
  wire [1:0]        c1_ddr4_cs_n;
  wire [0:0]        c1_ddr4_ck_t;
  wire [0:0]        c1_ddr4_ck_c;
  wire              c1_ddr4_reset_n;
  wire              c1_ddr4_parity;
  tri1 [8:0]        c1_ddr4_dm_dbi_n;
  tri [71:0]        c1_ddr4_dq;
  tri [17:0]        c1_ddr4_dqs_c;
  tri [17:0]        c1_ddr4_dqs_t;
  tri1              c1_ddr4_alert_n;

  logic         io_start;
  logic [15:0]  io_cfg_seqlen;
  logic         io_cfg_prefill;
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
  logic [63:0]  io_input_base_addr;
  logic [63:0]  io_ln1_w_base_addr;
  logic [63:0]  io_qkv_w_base_addr;
  logic [63:0]  io_qkv_b_base_addr;
  logic [63:0]  io_sm_base_addr;
  logic [63:0]  io_out_w_base_addr;
  logic [63:0]  io_out_b_base_addr;
  logic [63:0]  io_ln2_w_base_addr;
  logic [63:0]  io_ffnup_w_base_addr;
  logic [63:0]  io_ffnup_b_base_addr;
  logic [63:0]  io_ffndown_w_base_addr;
  logic [63:0]  io_ffndown_b_base_addr;
  logic [63:0]  io_output_base_addr;
  logic [31:0]  io_output_stride_bytes;

  logic [4:0]   io_m_axi_awid;
  logic [63:0]  io_m_axi_awaddr;
  logic [7:0]   io_m_axi_awlen;
  logic [2:0]   io_m_axi_awsize;
  logic [1:0]   io_m_axi_awburst;
  logic [0:0]   io_m_axi_awlock;
  logic [3:0]   io_m_axi_awcache;
  logic [2:0]   io_m_axi_awprot;
  logic [3:0]   io_m_axi_awregion;
  logic [3:0]   io_m_axi_awqos;
  logic         io_m_axi_awvalid;
  logic         io_m_axi_awready;
  logic [63:0]  io_m_axi_wdata;
  logic [7:0]   io_m_axi_wstrb;
  logic         io_m_axi_wlast;
  logic         io_m_axi_wvalid;
  logic         io_m_axi_wready;
  logic [4:0]   io_m_axi_bid;
  logic [1:0]   io_m_axi_bresp;
  logic         io_m_axi_bvalid;
  logic         io_m_axi_bready;
  logic [4:0]   io_m_axi_arid;
  logic [63:0]  io_m_axi_araddr;
  logic [7:0]   io_m_axi_arlen;
  logic [2:0]   io_m_axi_arsize;
  logic [1:0]   io_m_axi_arburst;
  logic [0:0]   io_m_axi_arlock;
  logic [3:0]   io_m_axi_arcache;
  logic [2:0]   io_m_axi_arprot;
  logic [3:0]   io_m_axi_arregion;
  logic [3:0]   io_m_axi_arqos;
  logic         io_m_axi_arvalid;
  logic         io_m_axi_arready;
  logic [4:0]   io_m_axi_rid;
  logic [63:0]  io_m_axi_rdata;
  logic [1:0]   io_m_axi_rresp;
  logic         io_m_axi_rlast;
  logic         io_m_axi_rvalid;
  logic         io_m_axi_rready;

  logic [4:0]   up_awid;
  logic [63:0]  up_awaddr;
  logic [7:0]   up_awlen;
  logic [2:0]   up_awsize;
  logic [1:0]   up_awburst;
  logic [0:0]   up_awlock;
  logic [3:0]   up_awcache;
  logic [2:0]   up_awprot;
  logic [3:0]   up_awregion;
  logic [3:0]   up_awqos;
  logic         up_awvalid;
  logic         up_awready;
  logic [63:0]  up_wdata;
  logic [7:0]   up_wstrb;
  logic         up_wlast;
  logic         up_wvalid;
  logic         up_wready;
  logic [4:0]   up_bid;
  logic [1:0]   up_bresp;
  logic         up_bvalid;
  logic         up_bready;
  logic [4:0]   up_arid;
  logic [63:0]  up_araddr;
  logic [7:0]   up_arlen;
  logic [2:0]   up_arsize;
  logic [1:0]   up_arburst;
  logic [0:0]   up_arlock;
  logic [3:0]   up_arcache;
  logic [2:0]   up_arprot;
  logic [3:0]   up_arregion;
  logic [3:0]   up_arqos;
  logic         up_arvalid;
  logic         up_arready;
  logic [4:0]   up_rid;
  logic [63:0]  up_rdata;
  logic [1:0]   up_rresp;
  logic         up_rlast;
  logic         up_rvalid;
  logic         up_rready;

  logic [63:0]  mid_awaddr;
  logic [7:0]   mid_awlen;
  logic [2:0]   mid_awsize;
  logic [1:0]   mid_awburst;
  logic [0:0]   mid_awlock;
  logic [3:0]   mid_awcache;
  logic [2:0]   mid_awprot;
  logic [3:0]   mid_awregion;
  logic [3:0]   mid_awqos;
  logic         mid_awvalid;
  logic         mid_awready;
  logic [255:0] mid_wdata;
  logic [31:0]  mid_wstrb;
  logic         mid_wlast;
  logic         mid_wvalid;
  logic         mid_wready;
  logic [1:0]   mid_bresp;
  logic         mid_bvalid;
  logic         mid_bready;
  logic [63:0]  mid_araddr;
  logic [7:0]   mid_arlen;
  logic [2:0]   mid_arsize;
  logic [1:0]   mid_arburst;
  logic [0:0]   mid_arlock;
  logic [3:0]   mid_arcache;
  logic [2:0]   mid_arprot;
  logic [3:0]   mid_arregion;
  logic [3:0]   mid_arqos;
  logic         mid_arvalid;
  logic         mid_arready;
  logic [255:0] mid_rdata;
  logic [1:0]   mid_rresp;
  logic         mid_rlast;
  logic         mid_rvalid;
  logic         mid_rready;

  logic [63:0]  fifo_awaddr;
  logic [7:0]   fifo_awlen;
  logic [2:0]   fifo_awsize;
  logic [1:0]   fifo_awburst;
  logic [0:0]   fifo_awlock;
  logic [3:0]   fifo_awcache;
  logic [2:0]   fifo_awprot;
  logic [3:0]   fifo_awregion;
  logic [3:0]   fifo_awqos;
  logic         fifo_awvalid;
  logic         fifo_awready;
  logic [255:0] fifo_wdata;
  logic [31:0]  fifo_wstrb;
  logic         fifo_wlast;
  logic         fifo_wvalid;
  logic         fifo_wready;
  logic [1:0]   fifo_bresp;
  logic         fifo_bvalid;
  logic         fifo_bready;
  logic [63:0]  fifo_araddr;
  logic [7:0]   fifo_arlen;
  logic [2:0]   fifo_arsize;
  logic [1:0]   fifo_arburst;
  logic [0:0]   fifo_arlock;
  logic [3:0]   fifo_arcache;
  logic [2:0]   fifo_arprot;
  logic [3:0]   fifo_arregion;
  logic [3:0]   fifo_arqos;
  logic         fifo_arvalid;
  logic         fifo_arready;
  logic [255:0] fifo_rdata;
  logic [1:0]   fifo_rresp;
  logic         fifo_rlast;
  logic         fifo_rvalid;
  logic         fifo_rready;

  logic [23:0]   xbar_s_awid;
  logic [255:0]  xbar_s_awaddr;
  logic [31:0]   xbar_s_awlen;
  logic [11:0]   xbar_s_awsize;
  logic [7:0]    xbar_s_awburst;
  logic [3:0]    xbar_s_awlock;
  logic [15:0]   xbar_s_awcache;
  logic [11:0]   xbar_s_awprot;
  logic [15:0]   xbar_s_awqos;
  logic [3:0]    xbar_s_awvalid;
  logic [3:0]    xbar_s_awready;
  logic [1023:0] xbar_s_wdata;
  logic [127:0]  xbar_s_wstrb;
  logic [3:0]    xbar_s_wlast;
  logic [3:0]    xbar_s_wvalid;
  logic [3:0]    xbar_s_wready;
  logic [23:0]   xbar_s_bid;
  logic [7:0]    xbar_s_bresp;
  logic [3:0]    xbar_s_bvalid;
  logic [3:0]    xbar_s_bready;
  logic [23:0]   xbar_s_arid;
  logic [255:0]  xbar_s_araddr;
  logic [31:0]   xbar_s_arlen;
  logic [11:0]   xbar_s_arsize;
  logic [7:0]    xbar_s_arburst;
  logic [3:0]    xbar_s_arlock;
  logic [15:0]   xbar_s_arcache;
  logic [11:0]   xbar_s_arprot;
  logic [15:0]   xbar_s_arqos;
  logic [3:0]    xbar_s_arvalid;
  logic [3:0]    xbar_s_arready;
  logic [23:0]   xbar_s_rid;
  logic [1023:0] xbar_s_rdata;
  logic [7:0]    xbar_s_rresp;
  logic [3:0]    xbar_s_rlast;
  logic [3:0]    xbar_s_rvalid;
  logic [3:0]    xbar_s_rready;

  logic [35:0]   xbar_m_awid;
  logic [383:0]  xbar_m_awaddr;
  logic [47:0]   xbar_m_awlen;
  logic [17:0]   xbar_m_awsize;
  logic [11:0]   xbar_m_awburst;
  logic [5:0]    xbar_m_awlock;
  logic [23:0]   xbar_m_awcache;
  logic [17:0]   xbar_m_awprot;
  logic [23:0]   xbar_m_awregion;
  logic [23:0]   xbar_m_awqos;
  logic [5:0]    xbar_m_awvalid;
  logic [5:0]    xbar_m_awready;
  logic [1535:0] xbar_m_wdata;
  logic [191:0]  xbar_m_wstrb;
  logic [5:0]    xbar_m_wlast;
  logic [5:0]    xbar_m_wvalid;
  logic [5:0]    xbar_m_wready;
  logic [35:0]   xbar_m_bid;
  logic [11:0]   xbar_m_bresp;
  logic [5:0]    xbar_m_bvalid;
  logic [5:0]    xbar_m_bready;
  logic [35:0]   xbar_m_arid;
  logic [383:0]  xbar_m_araddr;
  logic [47:0]   xbar_m_arlen;
  logic [17:0]   xbar_m_arsize;
  logic [11:0]   xbar_m_arburst;
  logic [5:0]    xbar_m_arlock;
  logic [23:0]   xbar_m_arcache;
  logic [17:0]   xbar_m_arprot;
  logic [23:0]   xbar_m_arregion;
  logic [23:0]   xbar_m_arqos;
  logic [5:0]    xbar_m_arvalid;
  logic [5:0]    xbar_m_arready;
  logic [35:0]   xbar_m_rid;
  logic [1535:0] xbar_m_rdata;
  logic [11:0]   xbar_m_rresp;
  logic [5:0]    xbar_m_rlast;
  logic [5:0]    xbar_m_rvalid;
  logic [5:0]    xbar_m_rready;

  logic [5:0]    c0_awid;
  logic [34:0]   c0_awaddr;
  logic [7:0]    c0_awlen;
  logic [2:0]    c0_awsize;
  logic [1:0]    c0_awburst;
  logic [0:0]    c0_awlock;
  logic [3:0]    c0_awcache;
  logic [2:0]    c0_awprot;
  logic [3:0]    c0_awregion;
  logic [3:0]    c0_awqos;
  logic          c0_awvalid;
  logic          c0_awready;
  logic [255:0]  c0_wdata;
  logic [31:0]   c0_wstrb;
  logic          c0_wlast;
  logic          c0_wvalid;
  logic          c0_wready;
  logic [5:0]    c0_bid;
  logic [1:0]    c0_bresp;
  logic          c0_bvalid;
  logic          c0_bready;
  logic [5:0]    c0_arid;
  logic [34:0]   c0_araddr;
  logic [7:0]    c0_arlen;
  logic [2:0]    c0_arsize;
  logic [1:0]    c0_arburst;
  logic [0:0]    c0_arlock;
  logic [3:0]    c0_arcache;
  logic [2:0]    c0_arprot;
  logic [3:0]    c0_arregion;
  logic [3:0]    c0_arqos;
  logic          c0_arvalid;
  logic          c0_arready;
  logic [5:0]    c0_rid;
  logic [255:0]  c0_rdata;
  logic [1:0]    c0_rresp;
  logic          c0_rlast;
  logic          c0_rvalid;
  logic          c0_rready;

  logic [5:0]    c1_awid;
  logic [34:0]   c1_awaddr;
  logic [7:0]    c1_awlen;
  logic [2:0]    c1_awsize;
  logic [1:0]    c1_awburst;
  logic [0:0]    c1_awlock;
  logic [3:0]    c1_awcache;
  logic [2:0]    c1_awprot;
  logic [3:0]    c1_awregion;
  logic [3:0]    c1_awqos;
  logic          c1_awvalid;
  logic          c1_awready;
  logic [255:0]  c1_wdata;
  logic [31:0]   c1_wstrb;
  logic          c1_wlast;
  logic          c1_wvalid;
  logic          c1_wready;
  logic [5:0]    c1_bid;
  logic [1:0]    c1_bresp;
  logic          c1_bvalid;
  logic          c1_bready;
  logic [5:0]    c1_arid;
  logic [34:0]   c1_araddr;
  logic [7:0]    c1_arlen;
  logic [2:0]    c1_arsize;
  logic [1:0]    c1_arburst;
  logic [0:0]    c1_arlock;
  logic [3:0]    c1_arcache;
  logic [2:0]    c1_arprot;
  logic [3:0]    c1_arregion;
  logic [3:0]    c1_arqos;
  logic          c1_arvalid;
  logic          c1_arready;
  logic [5:0]    c1_rid;
  logic [255:0]  c1_rdata;
  logic [1:0]    c1_rresp;
  logic          c1_rlast;
  logic          c1_rvalid;
  logic          c1_rready;

  logic [5:0]    cc0_bid;
  logic [1:0]    cc0_bresp;
  logic          cc0_bvalid;
  logic          cc0_bready;
  logic          cc0_awready;
  logic          cc0_wready;
  logic          cc0_arready;
  logic [5:0]    cc0_rid;
  logic [255:0]  cc0_rdata;
  logic [1:0]    cc0_rresp;
  logic          cc0_rlast;
  logic          cc0_rvalid;
  logic          cc0_rready;

  logic [5:0]    cc1_bid;
  logic [1:0]    cc1_bresp;
  logic          cc1_bvalid;
  logic          cc1_bready;
  logic          cc1_awready;
  logic          cc1_wready;
  logic          cc1_arready;
  logic [5:0]    cc1_rid;
  logic [255:0]  cc1_rdata;
  logic [1:0]    cc1_rresp;
  logic          cc1_rlast;
  logic          cc1_rvalid;
  logic          cc1_rready;

  logic [383:0] io_res;
  logic         io_res_st;
  logic [31:0]  io_res_addr;
  logic         io_res_valid;
  logic         io_res_last;
  logic         io_done;
  logic         io_error;

  logic [31:0] ddr_image_words [0:MAX_DDR_WORDS-1];
  logic [31:0] golden_words [0:MAX_GOLDEN_WORDS-1];
  logic [31:0] mem_words [0:MAX_MEM_WORDS-1];
  logic [31:0] mem_words_c1 [0:MAX_MEM_WORDS-1];
  logic [31:0] observed_words [0:MAX_GOLDEN_WORDS-1];
  bit seen [0:MAX_GOLDEN_BEATS-1];

  string window_dir;
  string cfg_path;
  string ddr_path;
  string golden_path;

  integer ddr_word_count;
  integer golden_word_count;
  integer golden_beats;
  integer expected_output_beats;
  integer seen_count;
  longint unsigned cycle;
  integer idx;
  integer word_idx;
  integer up_ar_hs_count;
  integer mid_ar_hs_count;
  integer fifo_ar_hs_count;
  integer c0_ar_hs_count;
  integer c0_r_hs_count;
  integer c0_cycle;
  integer c1_cycle;
  bit saw_st;
  bit saw_last;
  bit debug_final_beats;

  longint unsigned c0_base_addr;
  longint unsigned c1_base_addr;
  longint unsigned output_base_addr_u64;
  longint unsigned output_stride_bytes_u64;

  bit rd_active;
  integer rd_latency;
  longint unsigned rd_addr;
  integer rd_beats_total;
  integer rd_beat_idx;
  integer rd_beat_bytes;
  logic [5:0] rd_id;

  bit wr_active;
  longint unsigned wr_addr;
  integer wr_beats_total;
  integer wr_beat_idx;
  integer wr_beat_bytes;
  logic [5:0] wr_id;
  bit b_pending;
  integer b_latency;

  bit c1_rd_active;
  integer c1_rd_latency;
  longint unsigned c1_rd_addr;
  integer c1_rd_beats_total;
  integer c1_rd_beat_idx;
  integer c1_rd_beat_bytes;
  logic [5:0] c1_rd_id;

  bit c1_wr_active;
  longint unsigned c1_wr_addr;
  integer c1_wr_beats_total;
  integer c1_wr_beat_idx;
  integer c1_wr_beat_bytes;
  logic [5:0] c1_wr_id;
  bit c1_b_pending;
  integer c1_b_latency;

  AxiBoardSystemTop dut (
    .clock(clock),
    .reset(reset),
    .io_start(io_start),
    .io_cfg_seqlen(io_cfg_seqlen),
    .io_cfg_prefill(io_cfg_prefill),
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
    .io_output_base_addr(io_output_base_addr),
    .io_output_stride_bytes(io_output_stride_bytes),
    .io_m_axi_awid(up_awid),
    .io_m_axi_awaddr(up_awaddr),
    .io_m_axi_awlen(up_awlen),
    .io_m_axi_awsize(up_awsize),
    .io_m_axi_awburst(up_awburst),
    .io_m_axi_awlock(up_awlock),
    .io_m_axi_awcache(up_awcache),
    .io_m_axi_awprot(up_awprot),
    .io_m_axi_awregion(up_awregion),
    .io_m_axi_awqos(up_awqos),
    .io_m_axi_awvalid(up_awvalid),
    .io_m_axi_awready(up_awready),
    .io_m_axi_wdata(up_wdata),
    .io_m_axi_wstrb(up_wstrb),
    .io_m_axi_wlast(up_wlast),
    .io_m_axi_wvalid(up_wvalid),
    .io_m_axi_wready(up_wready),
    .io_m_axi_bid(up_bid),
    .io_m_axi_bresp(up_bresp),
    .io_m_axi_bvalid(up_bvalid),
    .io_m_axi_bready(up_bready),
    .io_m_axi_arid(up_arid),
    .io_m_axi_araddr(up_araddr),
    .io_m_axi_arlen(up_arlen),
    .io_m_axi_arsize(up_arsize),
    .io_m_axi_arburst(up_arburst),
    .io_m_axi_arlock(up_arlock),
    .io_m_axi_arcache(up_arcache),
    .io_m_axi_arprot(up_arprot),
    .io_m_axi_arregion(up_arregion),
    .io_m_axi_arqos(up_arqos),
    .io_m_axi_arvalid(up_arvalid),
    .io_m_axi_arready(up_arready),
    .io_m_axi_rid(up_rid),
    .io_m_axi_rdata(up_rdata),
    .io_m_axi_rresp(up_rresp),
    .io_m_axi_rlast(up_rlast),
    .io_m_axi_rvalid(up_rvalid),
    .io_m_axi_rready(up_rready),
    .io_res(io_res),
    .io_res_st(io_res_st),
    .io_res_addr(io_res_addr),
    .io_res_valid(io_res_valid),
    .io_res_last(io_res_last),
    .io_done(io_done),
    .io_error(io_error)
  );

  app_shell_9p_auto_us_0 auto_us (
    .s_axi_aclk(clock),
    .s_axi_aresetn(~reset),
    .s_axi_awid(up_awid),
    .s_axi_awaddr(up_awaddr),
    .s_axi_awlen(up_awlen),
    .s_axi_awsize(up_awsize),
    .s_axi_awburst(up_awburst),
    .s_axi_awlock(up_awlock),
    .s_axi_awcache(up_awcache),
    .s_axi_awprot(up_awprot),
    .s_axi_awregion(up_awregion),
    .s_axi_awqos(up_awqos),
    .s_axi_awvalid(up_awvalid),
    .s_axi_awready(up_awready),
    .s_axi_wdata(up_wdata),
    .s_axi_wstrb(up_wstrb),
    .s_axi_wlast(up_wlast),
    .s_axi_wvalid(up_wvalid),
    .s_axi_wready(up_wready),
    .s_axi_bid(up_bid),
    .s_axi_bresp(up_bresp),
    .s_axi_bvalid(up_bvalid),
    .s_axi_bready(up_bready),
    .s_axi_arid(up_arid),
    .s_axi_araddr(up_araddr),
    .s_axi_arlen(up_arlen),
    .s_axi_arsize(up_arsize),
    .s_axi_arburst(up_arburst),
    .s_axi_arlock(up_arlock),
    .s_axi_arcache(up_arcache),
    .s_axi_arprot(up_arprot),
    .s_axi_arregion(up_arregion),
    .s_axi_arqos(up_arqos),
    .s_axi_arvalid(up_arvalid),
    .s_axi_arready(up_arready),
    .s_axi_rid(up_rid),
    .s_axi_rdata(up_rdata),
    .s_axi_rresp(up_rresp),
    .s_axi_rlast(up_rlast),
    .s_axi_rvalid(up_rvalid),
    .s_axi_rready(up_rready),
    .m_axi_awaddr(mid_awaddr),
    .m_axi_awlen(mid_awlen),
    .m_axi_awsize(mid_awsize),
    .m_axi_awburst(mid_awburst),
    .m_axi_awlock(mid_awlock),
    .m_axi_awcache(mid_awcache),
    .m_axi_awprot(mid_awprot),
    .m_axi_awregion(mid_awregion),
    .m_axi_awqos(mid_awqos),
    .m_axi_awvalid(mid_awvalid),
    .m_axi_awready(mid_awready),
    .m_axi_wdata(mid_wdata),
    .m_axi_wstrb(mid_wstrb),
    .m_axi_wlast(mid_wlast),
    .m_axi_wvalid(mid_wvalid),
    .m_axi_wready(mid_wready),
    .m_axi_bresp(mid_bresp),
    .m_axi_bvalid(mid_bvalid),
    .m_axi_bready(mid_bready),
    .m_axi_araddr(mid_araddr),
    .m_axi_arlen(mid_arlen),
    .m_axi_arsize(mid_arsize),
    .m_axi_arburst(mid_arburst),
    .m_axi_arlock(mid_arlock),
    .m_axi_arcache(mid_arcache),
    .m_axi_arprot(mid_arprot),
    .m_axi_arregion(mid_arregion),
    .m_axi_arqos(mid_arqos),
    .m_axi_arvalid(mid_arvalid),
    .m_axi_arready(mid_arready),
    .m_axi_rdata(mid_rdata),
    .m_axi_rresp(mid_rresp),
    .m_axi_rlast(mid_rlast),
    .m_axi_rvalid(mid_rvalid),
    .m_axi_rready(mid_rready)
  );

  app_shell_9p_s02_data_fifo_0 data_fifo (
    .aclk(clock),
    .aresetn(~reset),
    .s_axi_awaddr(mid_awaddr),
    .s_axi_awlen(mid_awlen),
    .s_axi_awsize(mid_awsize),
    .s_axi_awburst(mid_awburst),
    .s_axi_awlock(mid_awlock),
    .s_axi_awcache(mid_awcache),
    .s_axi_awprot(mid_awprot),
    .s_axi_awregion(mid_awregion),
    .s_axi_awqos(mid_awqos),
    .s_axi_awvalid(mid_awvalid),
    .s_axi_awready(mid_awready),
    .s_axi_wdata(mid_wdata),
    .s_axi_wstrb(mid_wstrb),
    .s_axi_wlast(mid_wlast),
    .s_axi_wvalid(mid_wvalid),
    .s_axi_wready(mid_wready),
    .s_axi_bresp(mid_bresp),
    .s_axi_bvalid(mid_bvalid),
    .s_axi_bready(mid_bready),
    .s_axi_araddr(mid_araddr),
    .s_axi_arlen(mid_arlen),
    .s_axi_arsize(mid_arsize),
    .s_axi_arburst(mid_arburst),
    .s_axi_arlock(mid_arlock),
    .s_axi_arcache(mid_arcache),
    .s_axi_arprot(mid_arprot),
    .s_axi_arregion(mid_arregion),
    .s_axi_arqos(mid_arqos),
    .s_axi_arvalid(mid_arvalid),
    .s_axi_arready(mid_arready),
    .s_axi_rdata(mid_rdata),
    .s_axi_rresp(mid_rresp),
    .s_axi_rlast(mid_rlast),
    .s_axi_rvalid(mid_rvalid),
    .s_axi_rready(mid_rready),
    .m_axi_awaddr(fifo_awaddr),
    .m_axi_awlen(fifo_awlen),
    .m_axi_awsize(fifo_awsize),
    .m_axi_awburst(fifo_awburst),
    .m_axi_awlock(fifo_awlock),
    .m_axi_awcache(fifo_awcache),
    .m_axi_awprot(fifo_awprot),
    .m_axi_awregion(fifo_awregion),
    .m_axi_awqos(fifo_awqos),
    .m_axi_awvalid(fifo_awvalid),
    .m_axi_awready(fifo_awready),
    .m_axi_wdata(fifo_wdata),
    .m_axi_wstrb(fifo_wstrb),
    .m_axi_wlast(fifo_wlast),
    .m_axi_wvalid(fifo_wvalid),
    .m_axi_wready(fifo_wready),
    .m_axi_bresp(fifo_bresp),
    .m_axi_bvalid(fifo_bvalid),
    .m_axi_bready(fifo_bready),
    .m_axi_araddr(fifo_araddr),
    .m_axi_arlen(fifo_arlen),
    .m_axi_arsize(fifo_arsize),
    .m_axi_arburst(fifo_arburst),
    .m_axi_arlock(fifo_arlock),
    .m_axi_arcache(fifo_arcache),
    .m_axi_arprot(fifo_arprot),
    .m_axi_arregion(fifo_arregion),
    .m_axi_arqos(fifo_arqos),
    .m_axi_arvalid(fifo_arvalid),
    .m_axi_arready(fifo_arready),
    .m_axi_rdata(fifo_rdata),
    .m_axi_rresp(fifo_rresp),
    .m_axi_rlast(fifo_rlast),
    .m_axi_rvalid(fifo_rvalid),
    .m_axi_rready(fifo_rready)
  );

  always_comb begin
    xbar_s_awid = '0;
    xbar_s_awaddr = '0;
    xbar_s_awlen = '0;
    xbar_s_awsize = '0;
    xbar_s_awburst = '0;
    xbar_s_awlock = '0;
    xbar_s_awcache = '0;
    xbar_s_awprot = '0;
    xbar_s_awqos = '0;
    xbar_s_awvalid = '0;
    xbar_s_wdata = '0;
    xbar_s_wstrb = '0;
    xbar_s_wlast = '0;
    xbar_s_wvalid = '0;
    xbar_s_bready = '0;
    xbar_s_arid = '0;
    xbar_s_araddr = '0;
    xbar_s_arlen = '0;
    xbar_s_arsize = '0;
    xbar_s_arburst = '0;
    xbar_s_arlock = '0;
    xbar_s_arcache = '0;
    xbar_s_arprot = '0;
    xbar_s_arqos = '0;
    xbar_s_arvalid = '0;
    xbar_s_rready = '0;

    xbar_s_awaddr[64 * XBAR_SI_SLOT +: 64] = fifo_awaddr;
    xbar_s_awlen[8 * XBAR_SI_SLOT +: 8] = fifo_awlen;
    xbar_s_awsize[3 * XBAR_SI_SLOT +: 3] = fifo_awsize;
    xbar_s_awburst[2 * XBAR_SI_SLOT +: 2] = fifo_awburst;
    xbar_s_awlock[XBAR_SI_SLOT +: 1] = fifo_awlock;
    xbar_s_awcache[4 * XBAR_SI_SLOT +: 4] = fifo_awcache;
    xbar_s_awprot[3 * XBAR_SI_SLOT +: 3] = fifo_awprot;
    xbar_s_awqos[4 * XBAR_SI_SLOT +: 4] = fifo_awqos;
    xbar_s_awvalid[XBAR_SI_SLOT] = fifo_awvalid;
    xbar_s_wdata[256 * XBAR_SI_SLOT +: 256] = fifo_wdata;
    xbar_s_wstrb[32 * XBAR_SI_SLOT +: 32] = fifo_wstrb;
    xbar_s_wlast[XBAR_SI_SLOT] = fifo_wlast;
    xbar_s_wvalid[XBAR_SI_SLOT] = fifo_wvalid;
    xbar_s_bready[XBAR_SI_SLOT] = fifo_bready;
    xbar_s_araddr[64 * XBAR_SI_SLOT +: 64] = fifo_araddr;
    xbar_s_arlen[8 * XBAR_SI_SLOT +: 8] = fifo_arlen;
    xbar_s_arsize[3 * XBAR_SI_SLOT +: 3] = fifo_arsize;
    xbar_s_arburst[2 * XBAR_SI_SLOT +: 2] = fifo_arburst;
    xbar_s_arlock[XBAR_SI_SLOT +: 1] = fifo_arlock;
    xbar_s_arcache[4 * XBAR_SI_SLOT +: 4] = fifo_arcache;
    xbar_s_arprot[3 * XBAR_SI_SLOT +: 3] = fifo_arprot;
    xbar_s_arqos[4 * XBAR_SI_SLOT +: 4] = fifo_arqos;
    xbar_s_arvalid[XBAR_SI_SLOT] = fifo_arvalid;
    xbar_s_rready[XBAR_SI_SLOT] = fifo_rready;

    xbar_m_awready = 6'b111100;
    xbar_m_wready = 6'b111100;
    xbar_m_bid = '0;
    xbar_m_bresp = '0;
    xbar_m_bvalid = '0;
    xbar_m_arready = 6'b111100;
    xbar_m_rid = '0;
    xbar_m_rdata = '0;
    xbar_m_rresp = '0;
    xbar_m_rlast = '0;
    xbar_m_rvalid = '0;

    xbar_m_awready[XBAR_MI_C0] = cc0_awready;
    xbar_m_wready[XBAR_MI_C0] = cc0_wready;
    xbar_m_bid[6 * XBAR_MI_C0 +: 6] = cc0_bid;
    xbar_m_bresp[2 * XBAR_MI_C0 +: 2] = cc0_bresp;
    xbar_m_bvalid[XBAR_MI_C0] = cc0_bvalid;
    xbar_m_arready[XBAR_MI_C0] = cc0_arready;
    xbar_m_rid[6 * XBAR_MI_C0 +: 6] = cc0_rid;
    xbar_m_rdata[256 * XBAR_MI_C0 +: 256] = cc0_rdata;
    xbar_m_rresp[2 * XBAR_MI_C0 +: 2] = cc0_rresp;
    xbar_m_rlast[XBAR_MI_C0] = cc0_rlast;
    xbar_m_rvalid[XBAR_MI_C0] = cc0_rvalid;

    xbar_m_awready[XBAR_MI_C1] = cc1_awready;
    xbar_m_wready[XBAR_MI_C1] = cc1_wready;
    xbar_m_bid[6 * XBAR_MI_C1 +: 6] = cc1_bid;
    xbar_m_bresp[2 * XBAR_MI_C1 +: 2] = cc1_bresp;
    xbar_m_bvalid[XBAR_MI_C1] = cc1_bvalid;
    xbar_m_arready[XBAR_MI_C1] = cc1_arready;
    xbar_m_rid[6 * XBAR_MI_C1 +: 6] = cc1_rid;
    xbar_m_rdata[256 * XBAR_MI_C1 +: 256] = cc1_rdata;
    xbar_m_rresp[2 * XBAR_MI_C1 +: 2] = cc1_rresp;
    xbar_m_rlast[XBAR_MI_C1] = cc1_rlast;
    xbar_m_rvalid[XBAR_MI_C1] = cc1_rvalid;
  end

  assign fifo_awready = xbar_s_awready[XBAR_SI_SLOT];
  assign fifo_wready = xbar_s_wready[XBAR_SI_SLOT];
  assign fifo_bresp = xbar_s_bresp[2 * XBAR_SI_SLOT +: 2];
  assign fifo_bvalid = xbar_s_bvalid[XBAR_SI_SLOT];
  assign fifo_arready = xbar_s_arready[XBAR_SI_SLOT];
  assign fifo_rdata = xbar_s_rdata[256 * XBAR_SI_SLOT +: 256];
  assign fifo_rresp = xbar_s_rresp[2 * XBAR_SI_SLOT +: 2];
  assign fifo_rlast = xbar_s_rlast[XBAR_SI_SLOT];
  assign fifo_rvalid = xbar_s_rvalid[XBAR_SI_SLOT];

  assign cc0_bready = xbar_m_bready[XBAR_MI_C0];
  assign cc0_rready = xbar_m_rready[XBAR_MI_C0];
  assign cc1_bready = xbar_m_bready[XBAR_MI_C1];
  assign cc1_rready = xbar_m_rready[XBAR_MI_C1];

  app_shell_9p_xbar_0 xbar (
    .aclk(clock),
    .aresetn(~reset),
    .s_axi_awid(xbar_s_awid),
    .s_axi_awaddr(xbar_s_awaddr),
    .s_axi_awlen(xbar_s_awlen),
    .s_axi_awsize(xbar_s_awsize),
    .s_axi_awburst(xbar_s_awburst),
    .s_axi_awlock(xbar_s_awlock),
    .s_axi_awcache(xbar_s_awcache),
    .s_axi_awprot(xbar_s_awprot),
    .s_axi_awqos(xbar_s_awqos),
    .s_axi_awvalid(xbar_s_awvalid),
    .s_axi_awready(xbar_s_awready),
    .s_axi_wdata(xbar_s_wdata),
    .s_axi_wstrb(xbar_s_wstrb),
    .s_axi_wlast(xbar_s_wlast),
    .s_axi_wvalid(xbar_s_wvalid),
    .s_axi_wready(xbar_s_wready),
    .s_axi_bid(xbar_s_bid),
    .s_axi_bresp(xbar_s_bresp),
    .s_axi_bvalid(xbar_s_bvalid),
    .s_axi_bready(xbar_s_bready),
    .s_axi_arid(xbar_s_arid),
    .s_axi_araddr(xbar_s_araddr),
    .s_axi_arlen(xbar_s_arlen),
    .s_axi_arsize(xbar_s_arsize),
    .s_axi_arburst(xbar_s_arburst),
    .s_axi_arlock(xbar_s_arlock),
    .s_axi_arcache(xbar_s_arcache),
    .s_axi_arprot(xbar_s_arprot),
    .s_axi_arqos(xbar_s_arqos),
    .s_axi_arvalid(xbar_s_arvalid),
    .s_axi_arready(xbar_s_arready),
    .s_axi_rid(xbar_s_rid),
    .s_axi_rdata(xbar_s_rdata),
    .s_axi_rresp(xbar_s_rresp),
    .s_axi_rlast(xbar_s_rlast),
    .s_axi_rvalid(xbar_s_rvalid),
    .s_axi_rready(xbar_s_rready),
    .m_axi_awid(xbar_m_awid),
    .m_axi_awaddr(xbar_m_awaddr),
    .m_axi_awlen(xbar_m_awlen),
    .m_axi_awsize(xbar_m_awsize),
    .m_axi_awburst(xbar_m_awburst),
    .m_axi_awlock(xbar_m_awlock),
    .m_axi_awcache(xbar_m_awcache),
    .m_axi_awprot(xbar_m_awprot),
    .m_axi_awregion(xbar_m_awregion),
    .m_axi_awqos(xbar_m_awqos),
    .m_axi_awvalid(xbar_m_awvalid),
    .m_axi_awready(xbar_m_awready),
    .m_axi_wdata(xbar_m_wdata),
    .m_axi_wstrb(xbar_m_wstrb),
    .m_axi_wlast(xbar_m_wlast),
    .m_axi_wvalid(xbar_m_wvalid),
    .m_axi_wready(xbar_m_wready),
    .m_axi_bid(xbar_m_bid),
    .m_axi_bresp(xbar_m_bresp),
    .m_axi_bvalid(xbar_m_bvalid),
    .m_axi_bready(xbar_m_bready),
    .m_axi_arid(xbar_m_arid),
    .m_axi_araddr(xbar_m_araddr),
    .m_axi_arlen(xbar_m_arlen),
    .m_axi_arsize(xbar_m_arsize),
    .m_axi_arburst(xbar_m_arburst),
    .m_axi_arlock(xbar_m_arlock),
    .m_axi_arcache(xbar_m_arcache),
    .m_axi_arprot(xbar_m_arprot),
    .m_axi_arregion(xbar_m_arregion),
    .m_axi_arqos(xbar_m_arqos),
    .m_axi_arvalid(xbar_m_arvalid),
    .m_axi_arready(xbar_m_arready),
    .m_axi_rid(xbar_m_rid),
    .m_axi_rdata(xbar_m_rdata),
    .m_axi_rresp(xbar_m_rresp),
    .m_axi_rlast(xbar_m_rlast),
    .m_axi_rvalid(xbar_m_rvalid),
    .m_axi_rready(xbar_m_rready)
  );

  app_shell_9p_auto_cc_0 auto_cc0 (
    .s_axi_aclk(clock),
    .s_axi_aresetn(~reset),
    .s_axi_awid(xbar_m_awid[6 * XBAR_MI_C0 +: 6]),
    .s_axi_awaddr(xbar_m_awaddr[64 * XBAR_MI_C0 +: 35]),
    .s_axi_awlen(xbar_m_awlen[8 * XBAR_MI_C0 +: 8]),
    .s_axi_awsize(xbar_m_awsize[3 * XBAR_MI_C0 +: 3]),
    .s_axi_awburst(xbar_m_awburst[2 * XBAR_MI_C0 +: 2]),
    .s_axi_awlock(xbar_m_awlock[XBAR_MI_C0 +: 1]),
    .s_axi_awcache(xbar_m_awcache[4 * XBAR_MI_C0 +: 4]),
    .s_axi_awprot(xbar_m_awprot[3 * XBAR_MI_C0 +: 3]),
    .s_axi_awregion(xbar_m_awregion[4 * XBAR_MI_C0 +: 4]),
    .s_axi_awqos(xbar_m_awqos[4 * XBAR_MI_C0 +: 4]),
    .s_axi_awvalid(xbar_m_awvalid[XBAR_MI_C0]),
    .s_axi_awready(cc0_awready),
    .s_axi_wdata(xbar_m_wdata[256 * XBAR_MI_C0 +: 256]),
    .s_axi_wstrb(xbar_m_wstrb[32 * XBAR_MI_C0 +: 32]),
    .s_axi_wlast(xbar_m_wlast[XBAR_MI_C0]),
    .s_axi_wvalid(xbar_m_wvalid[XBAR_MI_C0]),
    .s_axi_wready(cc0_wready),
    .s_axi_bid(cc0_bid),
    .s_axi_bresp(cc0_bresp),
    .s_axi_bvalid(cc0_bvalid),
    .s_axi_bready(cc0_bready),
    .s_axi_arid(xbar_m_arid[6 * XBAR_MI_C0 +: 6]),
    .s_axi_araddr(xbar_m_araddr[64 * XBAR_MI_C0 +: 35]),
    .s_axi_arlen(xbar_m_arlen[8 * XBAR_MI_C0 +: 8]),
    .s_axi_arsize(xbar_m_arsize[3 * XBAR_MI_C0 +: 3]),
    .s_axi_arburst(xbar_m_arburst[2 * XBAR_MI_C0 +: 2]),
    .s_axi_arlock(xbar_m_arlock[XBAR_MI_C0 +: 1]),
    .s_axi_arcache(xbar_m_arcache[4 * XBAR_MI_C0 +: 4]),
    .s_axi_arprot(xbar_m_arprot[3 * XBAR_MI_C0 +: 3]),
    .s_axi_arregion(xbar_m_arregion[4 * XBAR_MI_C0 +: 4]),
    .s_axi_arqos(xbar_m_arqos[4 * XBAR_MI_C0 +: 4]),
    .s_axi_arvalid(xbar_m_arvalid[XBAR_MI_C0]),
    .s_axi_arready(cc0_arready),
    .s_axi_rid(cc0_rid),
    .s_axi_rdata(cc0_rdata),
    .s_axi_rresp(cc0_rresp),
    .s_axi_rlast(cc0_rlast),
    .s_axi_rvalid(cc0_rvalid),
    .s_axi_rready(cc0_rready),
    .m_axi_aclk(c0_ui_clock),
    .m_axi_aresetn(c0_axi_aresetn),
    .m_axi_awid(c0_awid),
    .m_axi_awaddr(c0_awaddr),
    .m_axi_awlen(c0_awlen),
    .m_axi_awsize(c0_awsize),
    .m_axi_awburst(c0_awburst),
    .m_axi_awlock(c0_awlock),
    .m_axi_awcache(c0_awcache),
    .m_axi_awprot(c0_awprot),
    .m_axi_awregion(c0_awregion),
    .m_axi_awqos(c0_awqos),
    .m_axi_awvalid(c0_awvalid),
    .m_axi_awready(c0_awready),
    .m_axi_wdata(c0_wdata),
    .m_axi_wstrb(c0_wstrb),
    .m_axi_wlast(c0_wlast),
    .m_axi_wvalid(c0_wvalid),
    .m_axi_wready(c0_wready),
    .m_axi_bid(c0_bid),
    .m_axi_bresp(c0_bresp),
    .m_axi_bvalid(c0_bvalid),
    .m_axi_bready(c0_bready),
    .m_axi_arid(c0_arid),
    .m_axi_araddr(c0_araddr),
    .m_axi_arlen(c0_arlen),
    .m_axi_arsize(c0_arsize),
    .m_axi_arburst(c0_arburst),
    .m_axi_arlock(c0_arlock),
    .m_axi_arcache(c0_arcache),
    .m_axi_arprot(c0_arprot),
    .m_axi_arregion(c0_arregion),
    .m_axi_arqos(c0_arqos),
    .m_axi_arvalid(c0_arvalid),
    .m_axi_arready(c0_arready),
    .m_axi_rid(c0_rid),
    .m_axi_rdata(c0_rdata),
    .m_axi_rresp(c0_rresp),
    .m_axi_rlast(c0_rlast),
    .m_axi_rvalid(c0_rvalid),
    .m_axi_rready(c0_rready)
  );

  app_shell_9p_auto_cc_1 auto_cc1 (
    .s_axi_aclk(clock),
    .s_axi_aresetn(~reset),
    .s_axi_awid(xbar_m_awid[6 * XBAR_MI_C1 +: 6]),
    .s_axi_awaddr(xbar_m_awaddr[64 * XBAR_MI_C1 +: 35]),
    .s_axi_awlen(xbar_m_awlen[8 * XBAR_MI_C1 +: 8]),
    .s_axi_awsize(xbar_m_awsize[3 * XBAR_MI_C1 +: 3]),
    .s_axi_awburst(xbar_m_awburst[2 * XBAR_MI_C1 +: 2]),
    .s_axi_awlock(xbar_m_awlock[XBAR_MI_C1 +: 1]),
    .s_axi_awcache(xbar_m_awcache[4 * XBAR_MI_C1 +: 4]),
    .s_axi_awprot(xbar_m_awprot[3 * XBAR_MI_C1 +: 3]),
    .s_axi_awregion(xbar_m_awregion[4 * XBAR_MI_C1 +: 4]),
    .s_axi_awqos(xbar_m_awqos[4 * XBAR_MI_C1 +: 4]),
    .s_axi_awvalid(xbar_m_awvalid[XBAR_MI_C1]),
    .s_axi_awready(cc1_awready),
    .s_axi_wdata(xbar_m_wdata[256 * XBAR_MI_C1 +: 256]),
    .s_axi_wstrb(xbar_m_wstrb[32 * XBAR_MI_C1 +: 32]),
    .s_axi_wlast(xbar_m_wlast[XBAR_MI_C1]),
    .s_axi_wvalid(xbar_m_wvalid[XBAR_MI_C1]),
    .s_axi_wready(cc1_wready),
    .s_axi_bid(cc1_bid),
    .s_axi_bresp(cc1_bresp),
    .s_axi_bvalid(cc1_bvalid),
    .s_axi_bready(cc1_bready),
    .s_axi_arid(xbar_m_arid[6 * XBAR_MI_C1 +: 6]),
    .s_axi_araddr(xbar_m_araddr[64 * XBAR_MI_C1 +: 35]),
    .s_axi_arlen(xbar_m_arlen[8 * XBAR_MI_C1 +: 8]),
    .s_axi_arsize(xbar_m_arsize[3 * XBAR_MI_C1 +: 3]),
    .s_axi_arburst(xbar_m_arburst[2 * XBAR_MI_C1 +: 2]),
    .s_axi_arlock(xbar_m_arlock[XBAR_MI_C1 +: 1]),
    .s_axi_arcache(xbar_m_arcache[4 * XBAR_MI_C1 +: 4]),
    .s_axi_arprot(xbar_m_arprot[3 * XBAR_MI_C1 +: 3]),
    .s_axi_arregion(xbar_m_arregion[4 * XBAR_MI_C1 +: 4]),
    .s_axi_arqos(xbar_m_arqos[4 * XBAR_MI_C1 +: 4]),
    .s_axi_arvalid(xbar_m_arvalid[XBAR_MI_C1]),
    .s_axi_arready(cc1_arready),
    .s_axi_rid(cc1_rid),
    .s_axi_rdata(cc1_rdata),
    .s_axi_rresp(cc1_rresp),
    .s_axi_rlast(cc1_rlast),
    .s_axi_rvalid(cc1_rvalid),
    .s_axi_rready(cc1_rready),
    .m_axi_aclk(c1_ui_clock),
    .m_axi_aresetn(c1_axi_aresetn),
    .m_axi_awid(c1_awid),
    .m_axi_awaddr(c1_awaddr),
    .m_axi_awlen(c1_awlen),
    .m_axi_awsize(c1_awsize),
    .m_axi_awburst(c1_awburst),
    .m_axi_awlock(c1_awlock),
    .m_axi_awcache(c1_awcache),
    .m_axi_awprot(c1_awprot),
    .m_axi_awregion(c1_awregion),
    .m_axi_awqos(c1_awqos),
    .m_axi_awvalid(c1_awvalid),
    .m_axi_awready(c1_awready),
    .m_axi_wdata(c1_wdata),
    .m_axi_wstrb(c1_wstrb),
    .m_axi_wlast(c1_wlast),
    .m_axi_wvalid(c1_wvalid),
    .m_axi_wready(c1_wready),
    .m_axi_bid(c1_bid),
    .m_axi_bresp(c1_bresp),
    .m_axi_bvalid(c1_bvalid),
    .m_axi_bready(c1_bready),
    .m_axi_arid(c1_arid),
    .m_axi_araddr(c1_araddr),
    .m_axi_arlen(c1_arlen),
    .m_axi_arsize(c1_arsize),
    .m_axi_arburst(c1_arburst),
    .m_axi_arlock(c1_arlock),
    .m_axi_arcache(c1_arcache),
    .m_axi_arprot(c1_arprot),
    .m_axi_arregion(c1_arregion),
    .m_axi_arqos(c1_arqos),
    .m_axi_arvalid(c1_arvalid),
    .m_axi_arready(c1_arready),
    .m_axi_rid(c1_rid),
    .m_axi_rdata(c1_rdata),
    .m_axi_rresp(c1_rresp),
    .m_axi_rlast(c1_rlast),
    .m_axi_rvalid(c1_rvalid),
    .m_axi_rready(c1_rready)
  );

`ifdef ENABLE_REAL_MIG
  app_shell_9p_proc_sys_reset_2_0 proc_sys_reset_c0 (
    .slowest_sync_clk(c0_ui_clock),
    .ext_reset_in(c0_ui_clk_sync_rst),
    .aux_reset_in(1'b0),
    .mb_debug_sys_rst(1'b0),
    .dcm_locked(1'b1),
    .mb_reset(c0_mb_reset),
    .bus_struct_reset(c0_bus_struct_reset),
    .peripheral_reset(c0_peripheral_reset),
    .interconnect_aresetn(c0_interconnect_aresetn),
    .peripheral_aresetn(c0_peripheral_aresetn)
  );

  app_shell_9p_proc_sys_reset_1_0 proc_sys_reset_c1 (
    .slowest_sync_clk(c1_ui_clock),
    .ext_reset_in(c1_ui_clk_sync_rst),
    .aux_reset_in(1'b0),
    .mb_debug_sys_rst(1'b0),
    .dcm_locked(1'b1),
    .mb_reset(c1_mb_reset),
    .bus_struct_reset(c1_bus_struct_reset),
    .peripheral_reset(c1_peripheral_reset),
    .interconnect_aresetn(c1_interconnect_aresetn),
    .peripheral_aresetn(c1_peripheral_aresetn)
  );

  app_shell_9p_ddr4_0_0 ddr4_0 (
    .sys_rst(reset),
    .c0_sys_clk_p(c0_sys_clk_p),
    .c0_sys_clk_n(c0_sys_clk_n),
    .c0_ddr4_act_n(c0_ddr4_act_n),
    .c0_ddr4_adr(c0_ddr4_adr),
    .c0_ddr4_ba(c0_ddr4_ba),
    .c0_ddr4_bg(c0_ddr4_bg),
    .c0_ddr4_cke(c0_ddr4_cke),
    .c0_ddr4_odt(c0_ddr4_odt),
    .c0_ddr4_cs_n(c0_ddr4_cs_n),
    .c0_ddr4_ck_t(c0_ddr4_ck_t),
    .c0_ddr4_ck_c(c0_ddr4_ck_c),
    .c0_ddr4_reset_n(c0_ddr4_reset_n),
    .c0_ddr4_parity(c0_ddr4_parity),
    .c0_ddr4_dq(c0_ddr4_dq),
    .c0_ddr4_dqs_c(c0_ddr4_dqs_c),
    .c0_ddr4_dqs_t(c0_ddr4_dqs_t),
    .c0_init_calib_complete(c0_init_calib_complete),
    .c0_ddr4_ui_clk(c0_ui_clock),
    .c0_ddr4_ui_clk_sync_rst(c0_ui_clk_sync_rst),
    .dbg_clk(c0_dbg_clk),
    .c0_ddr4_s_axi_ctrl_awvalid(1'b0),
    .c0_ddr4_s_axi_ctrl_awready(),
    .c0_ddr4_s_axi_ctrl_awaddr(32'd0),
    .c0_ddr4_s_axi_ctrl_wvalid(1'b0),
    .c0_ddr4_s_axi_ctrl_wready(),
    .c0_ddr4_s_axi_ctrl_wdata(32'd0),
    .c0_ddr4_s_axi_ctrl_bvalid(),
    .c0_ddr4_s_axi_ctrl_bready(1'b1),
    .c0_ddr4_s_axi_ctrl_bresp(),
    .c0_ddr4_s_axi_ctrl_arvalid(1'b0),
    .c0_ddr4_s_axi_ctrl_arready(),
    .c0_ddr4_s_axi_ctrl_araddr(32'd0),
    .c0_ddr4_s_axi_ctrl_rvalid(),
    .c0_ddr4_s_axi_ctrl_rready(1'b1),
    .c0_ddr4_s_axi_ctrl_rdata(),
    .c0_ddr4_s_axi_ctrl_rresp(),
    .c0_ddr4_interrupt(c0_ddr4_interrupt),
    .c0_ddr4_aresetn(c0_interconnect_aresetn[0]),
    .c0_ddr4_s_axi_awid(c0_awid),
    .c0_ddr4_s_axi_awaddr(c0_awaddr),
    .c0_ddr4_s_axi_awlen(c0_awlen),
    .c0_ddr4_s_axi_awsize(c0_awsize),
    .c0_ddr4_s_axi_awburst(c0_awburst),
    .c0_ddr4_s_axi_awlock(c0_awlock),
    .c0_ddr4_s_axi_awcache(c0_awcache),
    .c0_ddr4_s_axi_awprot(c0_awprot),
    .c0_ddr4_s_axi_awqos(c0_awqos),
    .c0_ddr4_s_axi_awvalid(c0_awvalid),
    .c0_ddr4_s_axi_awready(c0_awready),
    .c0_ddr4_s_axi_wdata(c0_wdata),
    .c0_ddr4_s_axi_wstrb(c0_wstrb),
    .c0_ddr4_s_axi_wlast(c0_wlast),
    .c0_ddr4_s_axi_wvalid(c0_wvalid),
    .c0_ddr4_s_axi_wready(c0_wready),
    .c0_ddr4_s_axi_bready(c0_bready),
    .c0_ddr4_s_axi_bid(c0_bid),
    .c0_ddr4_s_axi_bresp(c0_bresp),
    .c0_ddr4_s_axi_bvalid(c0_bvalid),
    .c0_ddr4_s_axi_arid(c0_arid),
    .c0_ddr4_s_axi_araddr(c0_araddr),
    .c0_ddr4_s_axi_arlen(c0_arlen),
    .c0_ddr4_s_axi_arsize(c0_arsize),
    .c0_ddr4_s_axi_arburst(c0_arburst),
    .c0_ddr4_s_axi_arlock(c0_arlock),
    .c0_ddr4_s_axi_arcache(c0_arcache),
    .c0_ddr4_s_axi_arprot(c0_arprot),
    .c0_ddr4_s_axi_arqos(c0_arqos),
    .c0_ddr4_s_axi_arvalid(c0_arvalid),
    .c0_ddr4_s_axi_arready(c0_arready),
    .c0_ddr4_s_axi_rready(c0_rready),
    .c0_ddr4_s_axi_rid(c0_rid),
    .c0_ddr4_s_axi_rdata(c0_rdata),
    .c0_ddr4_s_axi_rresp(c0_rresp),
    .c0_ddr4_s_axi_rlast(c0_rlast),
    .c0_ddr4_s_axi_rvalid(c0_rvalid),
    .dbg_bus(c0_dbg_bus)
  );

  app_shell_9p_ddr4_0_1 ddr4_1 (
    .sys_rst(reset),
    .c0_sys_clk_p(c1_sys_clk_p),
    .c0_sys_clk_n(c1_sys_clk_n),
    .c0_ddr4_act_n(c1_ddr4_act_n),
    .c0_ddr4_adr(c1_ddr4_adr),
    .c0_ddr4_ba(c1_ddr4_ba),
    .c0_ddr4_bg(c1_ddr4_bg),
    .c0_ddr4_cke(c1_ddr4_cke),
    .c0_ddr4_odt(c1_ddr4_odt),
    .c0_ddr4_cs_n(c1_ddr4_cs_n),
    .c0_ddr4_ck_t(c1_ddr4_ck_t),
    .c0_ddr4_ck_c(c1_ddr4_ck_c),
    .c0_ddr4_reset_n(c1_ddr4_reset_n),
    .c0_ddr4_parity(c1_ddr4_parity),
    .c0_ddr4_dq(c1_ddr4_dq),
    .c0_ddr4_dqs_c(c1_ddr4_dqs_c),
    .c0_ddr4_dqs_t(c1_ddr4_dqs_t),
    .c0_init_calib_complete(c1_init_calib_complete),
    .c0_ddr4_ui_clk(c1_ui_clock),
    .c0_ddr4_ui_clk_sync_rst(c1_ui_clk_sync_rst),
    .dbg_clk(c1_dbg_clk),
    .c0_ddr4_s_axi_ctrl_awvalid(1'b0),
    .c0_ddr4_s_axi_ctrl_awready(),
    .c0_ddr4_s_axi_ctrl_awaddr(32'd0),
    .c0_ddr4_s_axi_ctrl_wvalid(1'b0),
    .c0_ddr4_s_axi_ctrl_wready(),
    .c0_ddr4_s_axi_ctrl_wdata(32'd0),
    .c0_ddr4_s_axi_ctrl_bvalid(),
    .c0_ddr4_s_axi_ctrl_bready(1'b1),
    .c0_ddr4_s_axi_ctrl_bresp(),
    .c0_ddr4_s_axi_ctrl_arvalid(1'b0),
    .c0_ddr4_s_axi_ctrl_arready(),
    .c0_ddr4_s_axi_ctrl_araddr(32'd0),
    .c0_ddr4_s_axi_ctrl_rvalid(),
    .c0_ddr4_s_axi_ctrl_rready(1'b1),
    .c0_ddr4_s_axi_ctrl_rdata(),
    .c0_ddr4_s_axi_ctrl_rresp(),
    .c0_ddr4_interrupt(c1_ddr4_interrupt),
    .c0_ddr4_aresetn(c1_interconnect_aresetn[0]),
    .c0_ddr4_s_axi_awid(c1_awid),
    .c0_ddr4_s_axi_awaddr(c1_awaddr),
    .c0_ddr4_s_axi_awlen(c1_awlen),
    .c0_ddr4_s_axi_awsize(c1_awsize),
    .c0_ddr4_s_axi_awburst(c1_awburst),
    .c0_ddr4_s_axi_awlock(c1_awlock),
    .c0_ddr4_s_axi_awcache(c1_awcache),
    .c0_ddr4_s_axi_awprot(c1_awprot),
    .c0_ddr4_s_axi_awqos(c1_awqos),
    .c0_ddr4_s_axi_awvalid(c1_awvalid),
    .c0_ddr4_s_axi_awready(c1_awready),
    .c0_ddr4_s_axi_wdata(c1_wdata),
    .c0_ddr4_s_axi_wstrb(c1_wstrb),
    .c0_ddr4_s_axi_wlast(c1_wlast),
    .c0_ddr4_s_axi_wvalid(c1_wvalid),
    .c0_ddr4_s_axi_wready(c1_wready),
    .c0_ddr4_s_axi_bready(c1_bready),
    .c0_ddr4_s_axi_bid(c1_bid),
    .c0_ddr4_s_axi_bresp(c1_bresp),
    .c0_ddr4_s_axi_bvalid(c1_bvalid),
    .c0_ddr4_s_axi_arid(c1_arid),
    .c0_ddr4_s_axi_araddr(c1_araddr),
    .c0_ddr4_s_axi_arlen(c1_arlen),
    .c0_ddr4_s_axi_arsize(c1_arsize),
    .c0_ddr4_s_axi_arburst(c1_arburst),
    .c0_ddr4_s_axi_arlock(c1_arlock),
    .c0_ddr4_s_axi_arcache(c1_arcache),
    .c0_ddr4_s_axi_arprot(c1_arprot),
    .c0_ddr4_s_axi_arqos(c1_arqos),
    .c0_ddr4_s_axi_arvalid(c1_arvalid),
    .c0_ddr4_s_axi_arready(c1_arready),
    .c0_ddr4_s_axi_rready(c1_rready),
    .c0_ddr4_s_axi_rid(c1_rid),
    .c0_ddr4_s_axi_rdata(c1_rdata),
    .c0_ddr4_s_axi_rresp(c1_rresp),
    .c0_ddr4_s_axi_rlast(c1_rlast),
    .c0_ddr4_s_axi_rvalid(c1_rvalid),
    .dbg_bus(c1_dbg_bus)
  );

  ddr4_rdimm_wrapper #(
    .MC_DQ_WIDTH(72),
    .MC_DQS_BITS(18),
    .MC_DM_WIDTH(9),
    .MC_CKE_NUM(2),
    .MC_ODT_WIDTH(2),
    .MC_ABITS(17),
    .MC_BANK_WIDTH(2),
    .MC_BANK_GROUP(2),
    .MC_CS_NUM(2),
    .MC_RANKS_NUM(2),
    .NUM_PHYSICAL_PARTS(18),
    .CALIB_EN("NO"),
    .MEM_PART_WIDTH("x4"),
    .DDR_SIM_MODEL("MICRON"),
    .DM_DBI("NONE"),
    .MC_REG_CTRL("ON"),
    .DIMM_MODEL("RDIMM"),
    .RDIMM_SLOTS(1),
    .CONFIGURED_DENSITY(_8G)
  ) c0_rdimm (
    .ddr4_act_n(c0_ddr4_act_n),
    .ddr4_addr(c0_ddr4_adr),
    .ddr4_ba(c0_ddr4_ba),
    .ddr4_bg(c0_ddr4_bg),
    .ddr4_par(c0_ddr4_parity),
    .ddr4_cke(c0_ddr4_cke),
    .ddr4_odt(c0_ddr4_odt),
    .ddr4_cs_n(c0_ddr4_cs_n),
    .ddr4_ck_t(c0_ddr4_ck_t[0]),
    .ddr4_ck_c(c0_ddr4_ck_c[0]),
    .ddr4_reset_n(c0_ddr4_reset_n),
    .ddr4_dm_dbi_n(c0_ddr4_dm_dbi_n),
    .ddr4_dq(c0_ddr4_dq),
    .ddr4_dqs_t(c0_ddr4_dqs_t),
    .ddr4_dqs_c(c0_ddr4_dqs_c),
    .ddr4_alert_n(c0_ddr4_alert_n),
    .initDone(c0_init_calib_complete),
    .scl(1'b0),
    .sa0(1'b0),
    .sa1(1'b0),
    .sa2(1'b0),
    .sda(),
    .bfunc(1'b0),
    .vddspd(1'b1)
  );

  ddr4_rdimm_wrapper #(
    .MC_DQ_WIDTH(72),
    .MC_DQS_BITS(18),
    .MC_DM_WIDTH(9),
    .MC_CKE_NUM(2),
    .MC_ODT_WIDTH(2),
    .MC_ABITS(17),
    .MC_BANK_WIDTH(2),
    .MC_BANK_GROUP(2),
    .MC_CS_NUM(2),
    .MC_RANKS_NUM(2),
    .NUM_PHYSICAL_PARTS(18),
    .CALIB_EN("NO"),
    .MEM_PART_WIDTH("x4"),
    .DDR_SIM_MODEL("MICRON"),
    .DM_DBI("NONE"),
    .MC_REG_CTRL("ON"),
    .DIMM_MODEL("RDIMM"),
    .RDIMM_SLOTS(1),
    .CONFIGURED_DENSITY(_8G)
  ) c1_rdimm (
    .ddr4_act_n(c1_ddr4_act_n),
    .ddr4_addr(c1_ddr4_adr),
    .ddr4_ba(c1_ddr4_ba),
    .ddr4_bg(c1_ddr4_bg),
    .ddr4_par(c1_ddr4_parity),
    .ddr4_cke(c1_ddr4_cke),
    .ddr4_odt(c1_ddr4_odt),
    .ddr4_cs_n(c1_ddr4_cs_n),
    .ddr4_ck_t(c1_ddr4_ck_t[0]),
    .ddr4_ck_c(c1_ddr4_ck_c[0]),
    .ddr4_reset_n(c1_ddr4_reset_n),
    .ddr4_dm_dbi_n(c1_ddr4_dm_dbi_n),
    .ddr4_dq(c1_ddr4_dq),
    .ddr4_dqs_t(c1_ddr4_dqs_t),
    .ddr4_dqs_c(c1_ddr4_dqs_c),
    .ddr4_alert_n(c1_ddr4_alert_n),
    .initDone(c1_init_calib_complete),
    .scl(1'b0),
    .sa0(1'b0),
    .sa1(1'b0),
    .sa2(1'b0),
    .sda(),
    .bfunc(1'b0),
    .vddspd(1'b1)
  );

  always #5 c0_sys_clk_p = ~c0_sys_clk_p;
  always #5 c1_sys_clk_p = ~c1_sys_clk_p;
  always @(*) c0_sys_clk_n = ~c0_sys_clk_p;
  always @(*) c1_sys_clk_n = ~c1_sys_clk_p;
`else
  always #2.0 c0_ui_clock = ~c0_ui_clock;
  always #2.0 c1_ui_clock = ~c1_ui_clock;
  always @(*) begin
    c0_ui_clk_sync_rst = reset;
    c1_ui_clk_sync_rst = reset;
    c0_init_calib_complete = ~reset;
    c1_init_calib_complete = ~reset;
    c0_dbg_clk = 1'b0;
    c1_dbg_clk = 1'b0;
    c0_dbg_bus = '0;
    c1_dbg_bus = '0;
    c0_ddr4_interrupt = 1'b0;
    c1_ddr4_interrupt = 1'b0;
    c0_interconnect_aresetn = {~reset};
    c1_interconnect_aresetn = {~reset};
    c0_bus_struct_reset = {reset};
    c1_bus_struct_reset = {reset};
    c0_peripheral_reset = {reset};
    c1_peripheral_reset = {reset};
    c0_peripheral_aresetn = {~reset};
    c1_peripheral_aresetn = {~reset};
    c0_mb_reset = reset;
    c1_mb_reset = reset;
  end
`endif

  always #2.5 clock = ~clock;

  function automatic logic [31:0] byteswap32(input logic [31:0] w);
    begin
      byteswap32 = {w[7:0], w[15:8], w[23:16], w[31:24]};
    end
  endfunction

  function automatic real abs_real(input real value);
    begin
      if (value < 0.0) abs_real = -value;
      else abs_real = value;
    end
  endfunction

  task automatic fatal_msg(input string msg);
    begin
      $display("%s", msg);
      $fatal(1);
    end
  endtask

  function automatic integer mem_word_index(input longint unsigned addr);
    longint unsigned off_bytes;
    begin
      off_bytes = addr - c0_base_addr;
      mem_word_index = off_bytes >> 2;
    end
  endfunction

  function automatic integer mem_word_index_c1(input longint unsigned addr);
    longint unsigned off_bytes;
    begin
      off_bytes = addr - c1_base_addr;
      mem_word_index_c1 = off_bytes >> 2;
    end
  endfunction

  function automatic logic [31:0] read_mem_word_abs(input longint unsigned addr);
    begin
      if (addr >= c1_base_addr) read_mem_word_abs = mem_words_c1[mem_word_index_c1(addr)];
      else read_mem_word_abs = mem_words[mem_word_index(addr)];
    end
  endfunction

  task automatic load_ddr_image(input string path, output int word_count_out);
    int fd;
    int byte_count;
    int i;
    begin
      fd = $fopen(path, "rb");
      if (fd == 0) fatal_msg($sformatf("failed to open binary: %s", path));
      byte_count = $fread(ddr_image_words, fd);
      $fclose(fd);
      if ((byte_count % 4) != 0) fatal_msg($sformatf("unexpected binary size: %s bytes=%0d", path, byte_count));
      word_count_out = byte_count / 4;
      for (i = 0; i < word_count_out; i++) begin
        ddr_image_words[i] = byteswap32(ddr_image_words[i]);
      end
    end
  endtask

  task automatic load_golden(input string path, output int word_count_out);
    int fd;
    int byte_count;
    int i;
    begin
      fd = $fopen(path, "rb");
      if (fd == 0) fatal_msg($sformatf("failed to open binary: %s", path));
      byte_count = $fread(golden_words, fd);
      $fclose(fd);
      if ((byte_count % 4) != 0) fatal_msg($sformatf("unexpected binary size: %s bytes=%0d", path, byte_count));
      word_count_out = byte_count / 4;
      for (i = 0; i < word_count_out; i++) begin
        golden_words[i] = byteswap32(golden_words[i]);
      end
    end
  endtask

  task automatic parse_cfg(input string path);
    int fd;
    int parsed_int;
    longint unsigned parsed_u64;
    begin
      fd = $fopen(path, "r");
      if (fd == 0) fatal_msg($sformatf("failed to open cfg: %s", path));
      if ($fscanf(fd, "cfg_seqlen=%d\n", parsed_int) != 1) fatal_msg("parse cfg_seqlen failed");
      io_cfg_seqlen = parsed_int[15:0];
      if ($fscanf(fd, "input_beats=%d\n", parsed_int) != 1) fatal_msg("parse input_beats failed");
      if ($fscanf(fd, "output_beats=%d\n", parsed_int) != 1) fatal_msg("parse output_beats failed");
      expected_output_beats = parsed_int;
      if ($fscanf(fd, "ln1_out_inv_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse ln1_out_inv_scale failed");
      io_ln1_out_inv_scale = parsed_int[31:0];
      if ($fscanf(fd, "ln1_out_zero_point_s8=%d\n", parsed_int) != 1) fatal_msg("parse ln1_out_zero_point failed");
      io_ln1_out_zero_point = parsed_int[7:0];
      if ($fscanf(fd, "q_out_inv_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse q_out_inv_scale failed");
      io_q_out_inv_scale = parsed_int[31:0];
      if ($fscanf(fd, "k_out_inv_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse k_out_inv_scale failed");
      io_k_out_inv_scale = parsed_int[31:0];
      if ($fscanf(fd, "v_out_inv_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse v_out_inv_scale failed");
      io_v_out_inv_scale = parsed_int[31:0];
      if ($fscanf(fd, "q_bias_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse q_bias_scale failed");
      io_q_bias_scale = parsed_int[31:0];
      if ($fscanf(fd, "k_bias_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse k_bias_scale failed");
      io_k_bias_scale = parsed_int[31:0];
      if ($fscanf(fd, "v_bias_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse v_bias_scale failed");
      io_v_bias_scale = parsed_int[31:0];
      if ($fscanf(fd, "dm1_out_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse dm1_out_scale failed");
      io_dm1_out_scale = parsed_int[31:0];
      if ($fscanf(fd, "dm2_ctx_inv_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse dm2_ctx_inv_scale failed");
      io_dm2_ctx_inv_scale = parsed_int[31:0];
      if ($fscanf(fd, "dm2_ctx_zero_point_u8=%d\n", parsed_int) != 1) fatal_msg("parse dm2_ctx_zero_point failed");
      io_dm2_ctx_zero_point = parsed_int[7:0];
      if ($fscanf(fd, "dm2_out_inv_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse dm2_out_inv_scale failed");
      io_dm2_out_inv_scale = parsed_int[31:0];
      if ($fscanf(fd, "out_out_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse out_out_scale failed");
      io_out_out_scale = parsed_int[31:0];
      if ($fscanf(fd, "ln2_out_inv_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse ln2_out_inv_scale failed");
      io_ln2_out_inv_scale = parsed_int[31:0];
      if ($fscanf(fd, "ln2_out_zero_point_s8=%d\n", parsed_int) != 1) fatal_msg("parse ln2_out_zero_point failed");
      io_ln2_out_zero_point = parsed_int[7:0];
      if ($fscanf(fd, "ffnup_out_inv_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse ffnup_out_inv_scale failed");
      io_ffnup_out_inv_scale = parsed_int[31:0];
      if ($fscanf(fd, "ffnup_bias_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse ffnup_bias_scale failed");
      io_ffnup_bias_scale = parsed_int[31:0];
      if ($fscanf(fd, "ffndown_out_scale_u32=%d\n", parsed_int) != 1) fatal_msg("parse ffndown_out_scale failed");
      io_ffndown_out_scale = parsed_int[31:0];

      if ($fscanf(fd, "ddr_input_base_addr=%d\n", parsed_int) != 1) fatal_msg("parse ddr_input_base_addr failed");
      if ($fscanf(fd, "ddr_ln1_w_base_addr=%d\n", parsed_int) != 1) fatal_msg("parse ddr_ln1_w_base_addr failed");
      if ($fscanf(fd, "ddr_qkv_w_base_addr=%d\n", parsed_int) != 1) fatal_msg("parse ddr_qkv_w_base_addr failed");
      if ($fscanf(fd, "ddr_qkv_b_base_addr=%d\n", parsed_int) != 1) fatal_msg("parse ddr_qkv_b_base_addr failed");
      if ($fscanf(fd, "ddr_sm_base_addr=%d\n", parsed_int) != 1) fatal_msg("parse ddr_sm_base_addr failed");
      if ($fscanf(fd, "ddr_out_w_base_addr=%d\n", parsed_int) != 1) fatal_msg("parse ddr_out_w_base_addr failed");
      if ($fscanf(fd, "ddr_out_b_base_addr=%d\n", parsed_int) != 1) fatal_msg("parse ddr_out_b_base_addr failed");
      if ($fscanf(fd, "ddr_ln2_w_base_addr=%d\n", parsed_int) != 1) fatal_msg("parse ddr_ln2_w_base_addr failed");
      if ($fscanf(fd, "ddr_ffnup_w_base_addr=%d\n", parsed_int) != 1) fatal_msg("parse ddr_ffnup_w_base_addr failed");
      if ($fscanf(fd, "ddr_ffnup_b_base_addr=%d\n", parsed_int) != 1) fatal_msg("parse ddr_ffnup_b_base_addr failed");
      if ($fscanf(fd, "ddr_ffndown_w_base_addr=%d\n", parsed_int) != 1) fatal_msg("parse ddr_ffndown_w_base_addr failed");
      if ($fscanf(fd, "ddr_ffndown_b_base_addr=%d\n", parsed_int) != 1) fatal_msg("parse ddr_ffndown_b_base_addr failed");

      if ($fscanf(fd, "axi_c0_window_base_addr=%d\n", parsed_u64) != 1) fatal_msg("parse axi_c0_window_base_addr failed");
      c0_base_addr = parsed_u64;
      if ($fscanf(fd, "axi_c1_window_base_addr=%d\n", parsed_u64) != 1) fatal_msg("parse axi_c1_window_base_addr failed");
      c1_base_addr = parsed_u64;
      if ($fscanf(fd, "axi_data_bytes=%d\n", parsed_int) != 1) fatal_msg("parse axi_data_bytes failed");
      if ($fscanf(fd, "axi_line_bytes=%d\n", parsed_int) != 1) fatal_msg("parse axi_line_bytes failed");
      if ($fscanf(fd, "axi_input_base_addr=%d\n", parsed_u64) != 1) fatal_msg("parse axi_input_base_addr failed");
      io_input_base_addr = parsed_u64;
      if ($fscanf(fd, "axi_ln1_w_base_addr=%d\n", parsed_u64) != 1) fatal_msg("parse axi_ln1_w_base_addr failed");
      io_ln1_w_base_addr = parsed_u64;
      if ($fscanf(fd, "axi_qkv_w_base_addr=%d\n", parsed_u64) != 1) fatal_msg("parse axi_qkv_w_base_addr failed");
      io_qkv_w_base_addr = parsed_u64;
      if ($fscanf(fd, "axi_qkv_b_base_addr=%d\n", parsed_u64) != 1) fatal_msg("parse axi_qkv_b_base_addr failed");
      io_qkv_b_base_addr = parsed_u64;
      if ($fscanf(fd, "axi_sm_base_addr=%d\n", parsed_u64) != 1) fatal_msg("parse axi_sm_base_addr failed");
      io_sm_base_addr = parsed_u64;
      if ($fscanf(fd, "axi_out_w_base_addr=%d\n", parsed_u64) != 1) fatal_msg("parse axi_out_w_base_addr failed");
      io_out_w_base_addr = parsed_u64;
      if ($fscanf(fd, "axi_out_b_base_addr=%d\n", parsed_u64) != 1) fatal_msg("parse axi_out_b_base_addr failed");
      io_out_b_base_addr = parsed_u64;
      if ($fscanf(fd, "axi_ln2_w_base_addr=%d\n", parsed_u64) != 1) fatal_msg("parse axi_ln2_w_base_addr failed");
      io_ln2_w_base_addr = parsed_u64;
      if ($fscanf(fd, "axi_ffnup_w_base_addr=%d\n", parsed_u64) != 1) fatal_msg("parse axi_ffnup_w_base_addr failed");
      io_ffnup_w_base_addr = parsed_u64;
      if ($fscanf(fd, "axi_ffnup_b_base_addr=%d\n", parsed_u64) != 1) fatal_msg("parse axi_ffnup_b_base_addr failed");
      io_ffnup_b_base_addr = parsed_u64;
      if ($fscanf(fd, "axi_ffndown_w_base_addr=%d\n", parsed_u64) != 1) fatal_msg("parse axi_ffndown_w_base_addr failed");
      io_ffndown_w_base_addr = parsed_u64;
      if ($fscanf(fd, "axi_ffndown_b_base_addr=%d\n", parsed_u64) != 1) fatal_msg("parse axi_ffndown_b_base_addr failed");
      io_ffndown_b_base_addr = parsed_u64;
      if ($fscanf(fd, "axi_output_base_addr=%d\n", parsed_u64) != 1) fatal_msg("parse axi_output_base_addr failed");
      io_output_base_addr = parsed_u64;
      output_base_addr_u64 = parsed_u64;
      if ($fscanf(fd, "axi_output_stride_bytes=%d\n", parsed_u64) != 1) fatal_msg("parse axi_output_stride_bytes failed");
      io_output_stride_bytes = parsed_u64[31:0];
      output_stride_bytes_u64 = parsed_u64;
      $fclose(fd);
    end
  endtask

  task automatic load_mem_image;
    integer i;
    begin
      for (i = 0; i < MAX_MEM_WORDS; i++) begin
        mem_words[i] = 32'd0;
        mem_words_c1[i] = 32'd0;
      end
      for (i = 0; i < ddr_word_count; i++) begin
        mem_words[i] = ddr_image_words[i];
      end
    end
  endtask

  task automatic fill_axi_rdata(input longint unsigned addr);
    longint unsigned aligned_addr;
    integer base_idx;
    integer i;
    begin
      aligned_addr = addr & ~64'h1f;
      base_idx = mem_word_index(aligned_addr);
      c0_rdata = '0;
      for (i = 0; i < 8; i++) begin
        c0_rdata[i * 32 +: 32] = mem_words[base_idx + i];
      end
    end
  endtask

  task automatic fill_axi_rdata_c1(input longint unsigned addr);
    longint unsigned aligned_addr;
    integer base_idx;
    integer i;
    begin
      aligned_addr = addr & ~64'h1f;
      base_idx = mem_word_index_c1(aligned_addr);
      c1_rdata = '0;
      for (i = 0; i < 8; i++) begin
        c1_rdata[i * 32 +: 32] = mem_words_c1[base_idx + i];
      end
    end
  endtask

  task automatic store_axi_wdata(
      input longint unsigned addr,
      input logic [255:0] data,
      input logic [31:0] strb
  );
    longint unsigned aligned_addr;
    integer base_idx;
    integer byte_idx;
    integer word_sel;
    integer byte_sel;
    logic [31:0] cur_word;
    begin
      aligned_addr = addr & ~64'h1f;
      base_idx = mem_word_index(aligned_addr);
      for (byte_idx = 0; byte_idx < 32; byte_idx++) begin
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

  task automatic store_axi_wdata_c1(
      input longint unsigned addr,
      input logic [255:0] data,
      input logic [31:0] strb
  );
    longint unsigned aligned_addr;
    integer base_idx;
    integer byte_idx;
    integer word_sel;
    integer byte_sel;
    logic [31:0] cur_word;
    begin
      aligned_addr = addr & ~64'h1f;
      base_idx = mem_word_index_c1(aligned_addr);
      for (byte_idx = 0; byte_idx < 32; byte_idx++) begin
        if (strb[byte_idx]) begin
          word_sel = byte_idx / 4;
          byte_sel = byte_idx % 4;
          cur_word = mem_words_c1[base_idx + word_sel];
          cur_word[byte_sel * 8 +: 8] = data[byte_idx * 8 +: 8];
          mem_words_c1[base_idx + word_sel] = cur_word;
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
      if (io_error) fatal_msg("AxiBoardSystemTop raised io_error");
      if (!saw_st) fatal_msg("AxiBoardSystemTop never asserted io_res_st");
      if (!saw_last) fatal_msg("AxiBoardSystemTop never asserted io_res_last");
      for (beat_idx = 0; beat_idx < golden_beats; beat_idx++) begin
        if (!seen[beat_idx]) fatal_msg($sformatf("missing debug output beat=%0d", beat_idx));
      end
      if (dut.NUM_LAYERS == 1) begin
        for (beat_idx = 0; beat_idx < golden_beats; beat_idx++) begin
          for (lane_idx = 0; lane_idx < 12; lane_idx++) begin
            written_word = read_mem_word_abs(output_base_addr_u64 + beat_idx * output_stride_bytes_u64 + lane_idx * 4);
            if (written_word != golden_words[beat_idx * 12 + lane_idx]) begin
              obs = $bitstoshortreal(written_word);
              exp = $bitstoshortreal(golden_words[beat_idx * 12 + lane_idx]);
              abs_err = abs_real(obs - exp);
              if (abs_err > 5.0e-4) begin
                fatal_msg(
                    $sformatf(
                        "AxiBoardSystemTop writeback mismatch at beat=%0d lane=%0d observed_bits=0x%08x expected_bits=0x%08x observed=%f expected=%f abs_err=%f",
                        beat_idx,
                        lane_idx,
                        written_word,
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
        $display("AxiBoardSystemTop PASS beats=%0d", golden_beats);
      end else begin
        $display("AxiBoardSystemTop PASS runtime-only layers=%0d beats=%0d", dut.NUM_LAYERS, golden_beats);
      end
    end
  endtask

  always @(posedge c0_ui_clock) begin
    if (USE_CUSTOM_DDR_MODEL) begin
    if (reset) begin
      c0_cycle <= 0;
      rd_active <= 1'b0;
      rd_latency <= 0;
      rd_addr <= 0;
      rd_beats_total <= 0;
      rd_beat_idx <= 0;
      rd_beat_bytes <= 0;
      rd_id <= '0;
      wr_active <= 1'b0;
      wr_addr <= 0;
      wr_beats_total <= 0;
      wr_beat_idx <= 0;
      wr_beat_bytes <= 0;
      wr_id <= '0;
      b_pending <= 1'b0;
      b_latency <= 0;
      c0_awready <= 1'b0;
      c0_wready <= 1'b0;
      c0_bresp <= 2'b00;
      c0_bvalid <= 1'b0;
      c0_arready <= 1'b0;
      c0_rdata <= '0;
      c0_rresp <= 2'b00;
      c0_rlast <= 1'b0;
      c0_rvalid <= 1'b0;
      c0_bid <= '0;
      c0_rid <= '0;
    end else begin
      c0_cycle = c0_cycle + 1;
      if (c0_arvalid && c0_arready) begin
        if (rd_active) fatal_msg("multiple outstanding AXI reads are not supported");
        if (c0_arburst != 2'b01) fatal_msg($sformatf("unexpected c0 read burst type: araddr=0x%0h arlen=%0d arsize=%0d arburst=%0d", c0_araddr, c0_arlen, c0_arsize, c0_arburst));
        if (c0_arsize > 3'd5) fatal_msg($sformatf("unsupported c0 read size: araddr=0x%0h arlen=%0d arsize=%0d", c0_araddr, c0_arlen, c0_arsize));
        rd_active = 1'b1;
        rd_latency = READ_ADDR_LATENCY;
        rd_addr = c0_araddr;
        rd_beats_total = c0_arlen + 1;
        rd_beat_idx = 0;
        rd_beat_bytes = (1 << c0_arsize);
        rd_id = c0_arid;
      end

      if (c0_awvalid && c0_awready) begin
        if (wr_active) fatal_msg("multiple outstanding AXI writes are not supported");
        if (c0_awburst != 2'b01) fatal_msg($sformatf("unexpected c0 write burst type: awaddr=0x%0h awlen=%0d awsize=%0d awburst=%0d", c0_awaddr, c0_awlen, c0_awsize, c0_awburst));
        if (c0_awsize > 3'd5) fatal_msg($sformatf("unsupported c0 write size: awaddr=0x%0h awlen=%0d awsize=%0d", c0_awaddr, c0_awlen, c0_awsize));
        wr_active = 1'b1;
        wr_addr = c0_awaddr;
        wr_beats_total = c0_awlen + 1;
        wr_beat_idx = 0;
        wr_beat_bytes = (1 << c0_awsize);
        wr_id = c0_awid;
      end

      if (c0_wvalid && c0_wready) begin
        if (!wr_active) fatal_msg("c0 AXI write data arrived without AW");
        store_axi_wdata(wr_addr + wr_beat_idx * wr_beat_bytes, c0_wdata, c0_wstrb);
        wr_beat_idx = wr_beat_idx + 1;
        if (c0_wlast) begin
          if (wr_beat_idx != wr_beats_total) fatal_msg("c0 AXI WLAST arrived early");
          wr_active = 1'b0;
          b_pending = 1'b1;
          b_latency = WRITE_RESP_LATENCY;
        end
      end

      if (c0_rvalid && c0_rready) begin
        if (!rd_active) fatal_msg("c0 AXI read data arrived without AR");
        rd_beat_idx = rd_beat_idx + 1;
        if (c0_rlast) begin
          if (rd_beat_idx != rd_beats_total) fatal_msg("c0 AXI RLAST arrived early");
          rd_active = 1'b0;
          rd_beat_idx = 0;
        end
      end

      if (c0_bvalid && c0_bready) begin
        b_pending = 1'b0;
      end

      c0_arready <= ((c0_cycle % 9) != 0);
      c0_awready <= ((c0_cycle % 11) != 0);
      c0_wready <= ((c0_cycle % 13) != 0);

      c0_rvalid <= 1'b0;
      c0_rlast <= 1'b0;
      c0_rresp <= 2'b00;
      c0_rdata <= '0;
      c0_rid <= rd_id;
      if (rd_active) begin
        if (rd_latency > 0) begin
          rd_latency = rd_latency - 1;
        end else begin
          fill_axi_rdata(rd_addr + rd_beat_idx * rd_beat_bytes);
          c0_rvalid <= 1'b1;
          c0_rlast <= ((rd_beat_idx + 1) == rd_beats_total);
        end
      end

      c0_bvalid <= 1'b0;
      c0_bresp <= 2'b00;
      c0_bid <= wr_id;
      if (b_pending) begin
        if (b_latency > 0) begin
          b_latency = b_latency - 1;
        end else begin
          c0_bvalid <= 1'b1;
        end
      end
    end
    end
  end

  always @(posedge c1_ui_clock) begin
    if (USE_CUSTOM_DDR_MODEL) begin
    if (reset) begin
      c1_cycle <= 0;
      c1_rd_active <= 1'b0;
      c1_rd_latency <= 0;
      c1_rd_addr <= 0;
      c1_rd_beats_total <= 0;
      c1_rd_beat_idx <= 0;
      c1_rd_beat_bytes <= 0;
      c1_rd_id <= '0;
      c1_wr_active <= 1'b0;
      c1_wr_addr <= 0;
      c1_wr_beats_total <= 0;
      c1_wr_beat_idx <= 0;
      c1_wr_beat_bytes <= 0;
      c1_wr_id <= '0;
      c1_b_pending <= 1'b0;
      c1_b_latency <= 0;
      c1_awready <= 1'b0;
      c1_wready <= 1'b0;
      c1_bresp <= 2'b00;
      c1_bvalid <= 1'b0;
      c1_arready <= 1'b0;
      c1_rdata <= '0;
      c1_rresp <= 2'b00;
      c1_rlast <= 1'b0;
      c1_rvalid <= 1'b0;
      c1_bid <= '0;
      c1_rid <= '0;
    end else begin
      c1_cycle = c1_cycle + 1;
      if (c1_arvalid && c1_arready) begin
        if (c1_rd_active) fatal_msg("multiple outstanding c1 AXI reads are not supported");
        if (c1_arburst != 2'b01) fatal_msg($sformatf("unexpected c1 read burst type: araddr=0x%0h arlen=%0d arsize=%0d arburst=%0d", c1_araddr, c1_arlen, c1_arsize, c1_arburst));
        if (c1_arsize > 3'd5) fatal_msg($sformatf("unsupported c1 read size: araddr=0x%0h arlen=%0d arsize=%0d", c1_araddr, c1_arlen, c1_arsize));
        c1_rd_active = 1'b1;
        c1_rd_latency = READ_ADDR_LATENCY;
        c1_rd_addr = c1_araddr;
        c1_rd_beats_total = c1_arlen + 1;
        c1_rd_beat_idx = 0;
        c1_rd_beat_bytes = (1 << c1_arsize);
        c1_rd_id = c1_arid;
      end

      if (c1_awvalid && c1_awready) begin
        if (c1_wr_active) fatal_msg("multiple outstanding c1 AXI writes are not supported");
        if (c1_awburst != 2'b01) fatal_msg($sformatf("unexpected c1 write burst type: awaddr=0x%0h awlen=%0d awsize=%0d awburst=%0d", c1_awaddr, c1_awlen, c1_awsize, c1_awburst));
        if (c1_awsize > 3'd5) fatal_msg($sformatf("unsupported c1 write size: awaddr=0x%0h awlen=%0d awsize=%0d", c1_awaddr, c1_awlen, c1_awsize));
        c1_wr_active = 1'b1;
        c1_wr_addr = c1_awaddr;
        c1_wr_beats_total = c1_awlen + 1;
        c1_wr_beat_idx = 0;
        c1_wr_beat_bytes = (1 << c1_awsize);
        c1_wr_id = c1_awid;
      end

      if (c1_wvalid && c1_wready) begin
        if (!c1_wr_active) fatal_msg("c1 AXI write data arrived without AW");
        store_axi_wdata_c1(c1_wr_addr + c1_wr_beat_idx * c1_wr_beat_bytes, c1_wdata, c1_wstrb);
        c1_wr_beat_idx = c1_wr_beat_idx + 1;
        if (c1_wlast) begin
          if (c1_wr_beat_idx != c1_wr_beats_total) fatal_msg("c1 AXI WLAST arrived early");
          c1_wr_active = 1'b0;
          c1_b_pending = 1'b1;
          c1_b_latency = WRITE_RESP_LATENCY;
        end
      end

      if (c1_rvalid && c1_rready) begin
        if (!c1_rd_active) fatal_msg("c1 AXI read data arrived without AR");
        c1_rd_beat_idx = c1_rd_beat_idx + 1;
        if (c1_rlast) begin
          if (c1_rd_beat_idx != c1_rd_beats_total) fatal_msg("c1 AXI RLAST arrived early");
          c1_rd_active = 1'b0;
          c1_rd_beat_idx = 0;
        end
      end

      if (c1_bvalid && c1_bready) begin
        c1_b_pending = 1'b0;
      end

      c1_arready <= ((c1_cycle % 7) != 0);
      c1_awready <= ((c1_cycle % 5) != 0);
      c1_wready <= ((c1_cycle % 11) != 0);

      c1_rvalid <= 1'b0;
      c1_rlast <= 1'b0;
      c1_rresp <= 2'b00;
      c1_rdata <= '0;
      c1_rid <= c1_rd_id;
      if (c1_rd_active) begin
        if (c1_rd_latency > 0) begin
          c1_rd_latency = c1_rd_latency - 1;
        end else begin
          fill_axi_rdata_c1(c1_rd_addr + c1_rd_beat_idx * c1_rd_beat_bytes);
          c1_rvalid <= 1'b1;
          c1_rlast <= ((c1_rd_beat_idx + 1) == c1_rd_beats_total);
        end
      end

      c1_bvalid <= 1'b0;
      c1_bresp <= 2'b00;
      c1_bid <= c1_wr_id;
      if (c1_b_pending) begin
        if (c1_b_latency > 0) begin
          c1_b_latency = c1_b_latency - 1;
        end else begin
          c1_bvalid <= 1'b1;
        end
      end
    end
    end
  end

  initial begin
    if ($test$plusargs("debug_final_beats")) debug_final_beats = 1'b1;
    if (!$value$plusargs("window_dir=%s", window_dir)) begin
      fatal_msg("usage: simv +window_dir=<window_dir>");
    end

    cfg_path = {window_dir, "/window.cfg"};
    ddr_path = {window_dir, "/artifacts/ddr_image.u32.bin"};
    golden_path = {window_dir, "/artifacts/golden.u32.bin"};

    io_start = 1'b0;
    io_cfg_seqlen = '0;
    io_cfg_prefill = 1'b1;
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
    io_output_base_addr = '0;
    io_output_stride_bytes = '0;

    if (USE_CUSTOM_DDR_MODEL) begin
      c0_awready = 1'b0;
      c0_wready = 1'b0;
      c0_bresp = 2'b00;
      c0_bvalid = 1'b0;
      c0_arready = 1'b0;
      c0_rdata = '0;
      c0_rresp = 2'b00;
      c0_rlast = 1'b0;
      c0_rvalid = 1'b0;
      c0_bid = '0;
      c0_rid = '0;

      c1_awready = 1'b1;
      c1_wready = 1'b1;
      c1_bresp = 2'b00;
      c1_bvalid = 1'b0;
      c1_arready = 1'b1;
      c1_rdata = '0;
      c1_rresp = 2'b00;
      c1_rlast = 1'b0;
      c1_rvalid = 1'b0;
      c1_bid = '0;
      c1_rid = '0;
    end

    ddr_word_count = 0;
    golden_word_count = 0;
    golden_beats = 0;
    expected_output_beats = 0;
    seen_count = 0;
    up_ar_hs_count = 0;
    mid_ar_hs_count = 0;
    fifo_ar_hs_count = 0;
    c0_ar_hs_count = 0;
    c0_r_hs_count = 0;
    c0_cycle = 0;
    c1_cycle = 0;
    saw_st = 1'b0;
    saw_last = 1'b0;
    debug_final_beats = 1'b0;
    rd_active = 1'b0;
    rd_latency = 0;
    rd_addr = 0;
    rd_beats_total = 0;
    rd_beat_idx = 0;
    rd_beat_bytes = 0;
    rd_id = '0;
    wr_active = 1'b0;
    wr_addr = 0;
    wr_beats_total = 0;
    wr_beat_idx = 0;
    wr_beat_bytes = 0;
    wr_id = '0;
    b_pending = 1'b0;
    b_latency = 0;
    c1_rd_active = 1'b0;
    c1_rd_latency = 0;
    c1_rd_addr = 0;
    c1_rd_beats_total = 0;
    c1_rd_beat_idx = 0;
    c1_rd_beat_bytes = 0;
    c1_rd_id = '0;
    c1_wr_active = 1'b0;
    c1_wr_addr = 0;
    c1_wr_beats_total = 0;
    c1_wr_beat_idx = 0;
    c1_wr_beat_bytes = 0;
    c1_wr_id = '0;
    c1_b_pending = 1'b0;
    c1_b_latency = 0;

    for (idx = 0; idx < MAX_GOLDEN_BEATS; idx++) begin
      seen[idx] = 1'b0;
    end

    parse_cfg(cfg_path);
    load_ddr_image(ddr_path, ddr_word_count);
    load_golden(golden_path, golden_word_count);
    if ((golden_word_count % 12) != 0) fatal_msg($sformatf("golden word count is not a multiple of 12: %0d", golden_word_count));
    golden_beats = expected_output_beats;
    if (golden_beats == 0) golden_beats = golden_word_count / 12;
    load_mem_image();

    repeat (5) @(posedge clock);
    reset <= 1'b0;
    @(posedge clock);
    io_start <= 1'b1;
    @(posedge clock);
    io_start <= 1'b0;

    cycle = 0;
    while (cycle < MAX_CYCLES && !io_done) begin
      @(posedge clock);
      cycle = cycle + 1;

      if (up_arvalid && up_arready) up_ar_hs_count = up_ar_hs_count + 1;
      if (mid_arvalid && mid_arready) mid_ar_hs_count = mid_ar_hs_count + 1;
      if (fifo_arvalid && fifo_arready) fifo_ar_hs_count = fifo_ar_hs_count + 1;
      if (c0_arvalid && c0_arready) c0_ar_hs_count = c0_ar_hs_count + 1;
      if (c0_rvalid && c0_rready) c0_r_hs_count = c0_r_hs_count + 1;
      if (dut.NUM_LAYERS != 1 && debug_final_beats && c0_awvalid && c0_awready) begin
        $display("AxiBoardSystemTop write-req layer=%0d token=%0d awaddr=0x%0h awlen=%0d",
                 dut.layer_idx, dut.run_token_idx, c0_awaddr, c0_awlen);
      end

      if (io_res_valid) begin
        if (dut.NUM_LAYERS != 1 && debug_final_beats) begin
          $display("AxiBoardSystemTop debug-beat layer=%0d token=%0d addr=%0d st=%0d last=%0d",
                   dut.layer_idx, dut.run_token_idx, io_res_addr, io_res_st, io_res_last);
        end
        if (io_res_addr >= golden_beats) fatal_msg($sformatf("debug output addr out of range: %0d", io_res_addr));
        for (word_idx = 0; word_idx < 12; word_idx++) begin
          observed_words[io_res_addr * 12 + word_idx] = io_res[word_idx * 32 +: 32];
        end
        if (!seen[io_res_addr]) begin
          seen[io_res_addr] = 1'b1;
          seen_count = seen_count + 1;
        end
        saw_st = saw_st || io_res_st;
        saw_last = saw_last || io_res_last;
      end

      if ((cycle % PROGRESS_CYCLES) == 0) begin
        $display(
            "AxiBoardSystemTop progress cycle=%0d state=%0d layer=%0d token=%0d issue=%0d recv=%0d dut_rd_active=%0d up_ar[v=%0d r=%0d hs=%0d] mid_ar[v=%0d r=%0d hs=%0d] fifo_ar[v=%0d r=%0d hs=%0d] c0_ar[v=%0d r=%0d hs=%0d len=%0d] c0_r[v=%0d r=%0d hs=%0d l=%0d] c0_aw[v=%0d r=%0d len=%0d] c0_w[v=%0d r=%0d l=%0d] c0_b[v=%0d r=%0d] done=%0d seen=%0d/%0d err=%0d",
            cycle,
            dut.state,
            dut.layer_idx,
            dut.run_token_idx,
            dut.issue_count,
            dut.recv_count,
            dut.rd_active,
            up_arvalid,
            up_arready,
            up_ar_hs_count,
            mid_arvalid,
            mid_arready,
            mid_ar_hs_count,
            fifo_arvalid,
            fifo_arready,
            fifo_ar_hs_count,
            c0_arvalid,
            c0_arready,
            c0_ar_hs_count,
            c0_arlen,
            c0_rvalid,
            c0_rready,
            c0_r_hs_count,
            c0_rlast,
            c0_awvalid,
            c0_awready,
            c0_awlen,
            c0_wvalid,
            c0_wready,
            c0_wlast,
            c0_bvalid,
            c0_bready,
            io_done,
            seen_count,
            golden_beats,
            io_error
        );
      end
    end

    if (!io_done) fatal_msg($sformatf("AxiBoardSystemTop did not finish before cycle limit=%0d", MAX_CYCLES));
    check_outputs();
    $finish;
  end

endmodule
