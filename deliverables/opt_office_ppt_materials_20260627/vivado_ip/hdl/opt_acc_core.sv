module OptAccClockDiv3(
  input  clk_in,
  input  rst,
  output clk_out
);
`ifdef SYNTHESIS
  BUFGCE_DIV #(
    .BUFGCE_DIVIDE(3),
    .SIM_DEVICE("ULTRASCALE")
  ) u_core_clk_div (
    .I(clk_in),
    .CE(1'b1),
    .CLR(rst),
    .O(clk_out)
  );
`else
  reg [1:0] div_cnt;
  reg       clk_out_r;
  always @(posedge clk_in or posedge rst) begin
    if (rst) begin
      div_cnt <= 2'd0;
      clk_out_r <= 1'b0;
    end else begin
      div_cnt <= (div_cnt == 2'd2) ? 2'd0 : (div_cnt + 2'd1);
      clk_out_r <= (div_cnt == 2'd0);
    end
  end
  assign clk_out = clk_out_r;
`endif
endmodule

module OptAccDualClockMem #(
  parameter integer WIDTH = 384,
  parameter integer DEPTH = 1024,
  parameter integer ADDR_W = 10
)(
  input                  a_clk,
  input                  a_write_en,
  input  [ADDR_W-1:0]    a_write_addr,
  input  [WIDTH-1:0]     a_write_data,
  input                  a_read_en,
  input  [ADDR_W-1:0]    a_read_addr,
  output [WIDTH-1:0]     a_read_data,
  input                  b_clk,
  input                  b_write_en,
  input  [ADDR_W-1:0]    b_write_addr,
  input  [WIDTH-1:0]     b_write_data,
  input                  b_read_en,
  input  [ADDR_W-1:0]    b_read_addr,
  output [WIDTH-1:0]     b_read_data
);
`ifdef SYNTHESIS
  wire [WIDTH-1:0] mem_read_data_a;
  wire [WIDTH-1:0] mem_read_data_b;
  reg              a_read_en_d;
  reg              b_read_en_d;

  xpm_memory_tdpram #(
    .ADDR_WIDTH_A(ADDR_W),
    .ADDR_WIDTH_B(ADDR_W),
    .AUTO_SLEEP_TIME(0),
    .BYTE_WRITE_WIDTH_A(WIDTH),
    .BYTE_WRITE_WIDTH_B(WIDTH),
    .CLOCKING_MODE("independent_clock"),
    .ECC_MODE("no_ecc"),
    .MEMORY_INIT_FILE("none"),
    .MEMORY_INIT_PARAM("0"),
    .MEMORY_OPTIMIZATION("true"),
    .MEMORY_PRIMITIVE("block"),
    .MEMORY_SIZE(DEPTH * WIDTH),
    .MESSAGE_CONTROL(0),
    .READ_DATA_WIDTH_A(WIDTH),
    .READ_DATA_WIDTH_B(WIDTH),
    .READ_LATENCY_A(1),
    .READ_LATENCY_B(1),
    .READ_RESET_VALUE_A("0"),
    .READ_RESET_VALUE_B("0"),
    .RST_MODE_A("SYNC"),
    .RST_MODE_B("SYNC"),
    .USE_EMBEDDED_CONSTRAINT(0),
    .USE_MEM_INIT(0),
    .WAKEUP_TIME("disable_sleep"),
    .WRITE_DATA_WIDTH_A(WIDTH),
    .WRITE_DATA_WIDTH_B(WIDTH),
    .WRITE_MODE_A("read_first"),
    .WRITE_MODE_B("read_first")
  ) mem (
    .sleep(1'b0),
    .clka(a_clk),
    .rsta(1'b0),
    .ena(a_write_en || a_read_en),
    .regcea(1'b1),
    .wea(a_write_en),
    .addra(a_write_en ? a_write_addr : a_read_addr),
    .dina(a_write_data),
    .injectsbiterra(1'b0),
    .injectdbiterra(1'b0),
    .douta(mem_read_data_a),
    .sbiterra(),
    .dbiterra(),
    .clkb(b_clk),
    .rstb(1'b0),
    .enb(b_write_en || b_read_en),
    .regceb(1'b1),
    .web(b_write_en),
    .addrb(b_write_en ? b_write_addr : b_read_addr),
    .dinb(b_write_data),
    .injectsbiterrb(1'b0),
    .injectdbiterrb(1'b0),
    .doutb(mem_read_data_b),
    .sbiterrb(),
    .dbiterrb()
  );

  always @(posedge a_clk) begin
    a_read_en_d <= a_read_en;
  end
  always @(posedge b_clk) begin
    b_read_en_d <= b_read_en;
  end

  assign a_read_data = a_read_en_d ? mem_read_data_a : {WIDTH{1'b0}};
  assign b_read_data = b_read_en_d ? mem_read_data_b : {WIDTH{1'b0}};
`else
  (* ram_style = "block" *) reg [WIDTH-1:0] mem [0:DEPTH-1];
  reg [WIDTH-1:0] a_read_data_r;
  reg [WIDTH-1:0] b_read_data_r;

  always @(posedge a_clk) begin
    if (a_write_en)
      mem[a_write_addr] <= a_write_data;
    if (a_read_en)
      a_read_data_r <= mem[a_read_addr];
    else
      a_read_data_r <= {WIDTH{1'b0}};
  end

  always @(posedge b_clk) begin
    if (b_write_en)
      mem[b_write_addr] <= b_write_data;
    if (b_read_en)
      b_read_data_r <= mem[b_read_addr];
    else
      b_read_data_r <= {WIDTH{1'b0}};
  end

  assign a_read_data = a_read_data_r;
  assign b_read_data = b_read_data_r;
`endif
endmodule

module OptAccAsyncFifo #(
  parameter integer WIDTH = 288,
  parameter integer ADDR_W = 4
)(
  input                  wr_clk,
  input                  wr_rst,
  input                  wr_en,
  input  [WIDTH-1:0]     wr_data,
  output                 wr_full,
  output                 wr_empty,
  input                  rd_clk,
  input                  rd_rst,
  input                  rd_en,
  output reg [WIDTH-1:0] rd_data,
  output                 rd_empty,
  output reg             rd_valid
);
  localparam integer DEPTH = (1 << ADDR_W);
  localparam integer PTR_W = ADDR_W + 1;

  function [PTR_W-1:0] bin2gray;
    input [PTR_W-1:0] bin;
    begin
      bin2gray = (bin >> 1) ^ bin;
    end
  endfunction

  (* ram_style = "block" *) reg [WIDTH-1:0] mem [0:DEPTH-1];
  reg [PTR_W-1:0] wr_ptr_bin;
  reg [PTR_W-1:0] wr_ptr_gray;
  reg [PTR_W-1:0] rd_ptr_bin;
  reg [PTR_W-1:0] rd_ptr_gray;
  reg [PTR_W-1:0] rd_ptr_gray_sync1;
  reg [PTR_W-1:0] rd_ptr_gray_sync2;
  reg [PTR_W-1:0] wr_ptr_gray_sync1;
  reg [PTR_W-1:0] wr_ptr_gray_sync2;
  reg             wr_full_r;
  reg             rd_empty_r;

  wire wr_fire = wr_en && !wr_full_r;
  wire rd_fire = rd_en && !rd_empty_r;

  wire [PTR_W-1:0] wr_ptr_bin_next = wr_ptr_bin + {{PTR_W-1{1'b0}}, wr_fire};
  wire [PTR_W-1:0] rd_ptr_bin_next = rd_ptr_bin + {{PTR_W-1{1'b0}}, rd_fire};
  wire [PTR_W-1:0] wr_ptr_gray_next = bin2gray(wr_ptr_bin_next);
  wire [PTR_W-1:0] rd_ptr_gray_next = bin2gray(rd_ptr_bin_next);

  assign wr_full = wr_full_r;
  assign wr_empty = (wr_ptr_gray == rd_ptr_gray_sync2);
  assign rd_empty = rd_empty_r;

  function [PTR_W-1:0] fifo_full_compare;
    input [PTR_W-1:0] gray_ptr;
    input [PTR_W-1:0] gray_sync;
    begin
      fifo_full_compare = {~gray_sync[PTR_W-1:PTR_W-2], gray_sync[PTR_W-3:0]};
    end
  endfunction

  always @(posedge wr_clk) begin
    if (wr_fire)
      mem[wr_ptr_bin[ADDR_W-1:0]] <= wr_data;
  end

  always @(posedge rd_clk) begin
    if (rd_fire)
      rd_data <= mem[rd_ptr_bin[ADDR_W-1:0]];
  end

  always @(posedge wr_clk or posedge wr_rst) begin
    if (wr_rst) begin
      wr_ptr_bin <= {PTR_W{1'b0}};
      wr_ptr_gray <= {PTR_W{1'b0}};
      rd_ptr_gray_sync1 <= {PTR_W{1'b0}};
      rd_ptr_gray_sync2 <= {PTR_W{1'b0}};
      wr_full_r <= 1'b0;
    end else begin
      rd_ptr_gray_sync1 <= rd_ptr_gray;
      rd_ptr_gray_sync2 <= rd_ptr_gray_sync1;
      if (wr_fire) begin
        wr_ptr_bin <= wr_ptr_bin_next;
        wr_ptr_gray <= wr_ptr_gray_next;
      end
      wr_full_r <= (wr_ptr_gray_next == fifo_full_compare(wr_ptr_gray_next, rd_ptr_gray_sync2));
    end
  end

  always @(posedge rd_clk or posedge rd_rst) begin
    if (rd_rst) begin
      rd_ptr_bin <= {PTR_W{1'b0}};
      rd_ptr_gray <= {PTR_W{1'b0}};
      wr_ptr_gray_sync1 <= {PTR_W{1'b0}};
      wr_ptr_gray_sync2 <= {PTR_W{1'b0}};
      rd_valid <= 1'b0;
      rd_empty_r <= 1'b1;
    end else begin
      wr_ptr_gray_sync1 <= wr_ptr_gray;
      wr_ptr_gray_sync2 <= wr_ptr_gray_sync1;
      rd_valid <= rd_fire;
      if (rd_fire) begin
        rd_ptr_bin <= rd_ptr_bin_next;
        rd_ptr_gray <= rd_ptr_gray_next;
      end
      rd_empty_r <= (rd_ptr_gray_next == wr_ptr_gray_sync2);
    end
  end
endmodule

module opt_acc_core #(
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
  (* max_fanout = 16 *) output reg         c0_ddr4_s_axi_rready,
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

  localparam integer LN_WEIGHT_BEATS = 128;
  localparam integer QKV_WEIGHT_BEATS = 49152;
  localparam integer QKV_BIAS_BEATS = 192;
  localparam integer SM_BEATS = 26;
  localparam integer SOFTMAX_SEQ_LEN = 16;
  localparam integer OUT_WEIGHT_BEATS = 16896;
  localparam integer OUT_BIAS_BEATS = 64;
  localparam integer FFNUP_WEIGHT_BEATS = 66048;
  localparam integer FFNUP_BIAS_BEATS = 256;
  localparam integer FFNDOWN_WEIGHT_BEATS = 67584;
  localparam integer FFNDOWN_BIAS_BEATS = 64;
  localparam integer LAYER_SCALAR_BEATS = 2;
  localparam integer LAYER_REGION_BEATS =
      LAYER_SCALAR_BEATS + LN_WEIGHT_BEATS + QKV_WEIGHT_BEATS + QKV_BIAS_BEATS + SM_BEATS +
      OUT_WEIGHT_BEATS + OUT_BIAS_BEATS + LN_WEIGHT_BEATS + FFNUP_WEIGHT_BEATS +
      FFNUP_BIAS_BEATS + FFNDOWN_WEIGHT_BEATS + FFNDOWN_BIAS_BEATS;
  localparam integer LAYER_LN1_W_OFF_BEATS = LAYER_SCALAR_BEATS;
  localparam integer LAYER_QKV_W_OFF_BEATS = LAYER_LN1_W_OFF_BEATS + LN_WEIGHT_BEATS;
  localparam integer LAYER_QKV_B_OFF_BEATS = LAYER_QKV_W_OFF_BEATS + QKV_WEIGHT_BEATS;
  localparam integer LAYER_SM_OFF_BEATS = LAYER_QKV_B_OFF_BEATS + QKV_BIAS_BEATS;
  localparam integer LAYER_OUT_W_OFF_BEATS = LAYER_SM_OFF_BEATS + SM_BEATS;
  localparam integer LAYER_OUT_B_OFF_BEATS = LAYER_OUT_W_OFF_BEATS + OUT_WEIGHT_BEATS;
  localparam integer LAYER_LN2_W_OFF_BEATS = LAYER_OUT_B_OFF_BEATS + OUT_BIAS_BEATS;
  localparam integer LAYER_FFNUP_W_OFF_BEATS = LAYER_LN2_W_OFF_BEATS + LN_WEIGHT_BEATS;
  localparam integer LAYER_FFNUP_B_OFF_BEATS = LAYER_FFNUP_W_OFF_BEATS + FFNUP_WEIGHT_BEATS;
  localparam integer LAYER_FFNDOWN_W_OFF_BEATS = LAYER_FFNUP_B_OFF_BEATS + FFNUP_BIAS_BEATS;
  localparam integer LAYER_FFNDOWN_B_OFF_BEATS = LAYER_FFNDOWN_W_OFF_BEATS + FFNDOWN_WEIGHT_BEATS;
  localparam integer TOKEN_BEATS = 64;
  localparam integer AXI_BEAT_BYTES = 64;
  localparam integer SHORT_SEQ_MAX_TOKENS = 16;
  localparam integer SHORT_SEQ_TOTAL_BEATS = SHORT_SEQ_MAX_TOKENS * TOKEN_BEATS;
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

  localparam [2:0]
    PHASE_LN1         = 3'd0,
    PHASE_LN2         = 3'd1,
    PHASE_QKV_B       = 3'd2,
    PHASE_OUT_B       = 3'd3,
    PHASE_FFNUP_B     = 3'd4,
    PHASE_FFNDOWN_B   = 3'd5;
  localparam integer PHASE_CMD_W = 4;
  localparam integer PHASE_DONE_W = 3;
  localparam integer CFG_SM_BITS = SM_BEATS * SOFTMAX_SEQ_LEN;
  localparam integer CFG_CMD_W = 942;
  localparam integer TOKEN_DONE_W = 10;
  localparam integer QKV_W_FIFO_W = 304;
  localparam integer OUT_W_FIFO_W = 303;
  localparam integer FFNUP_W_FIFO_W = 305;
  localparam integer FFNDOWN_W_FIFO_W = 305;

  wire clock = c0_ddr4_s_axi_clk;
  wire reset = user_rst | ~sys_rst_n | ~c0_ddr4_s_axi_rst_n;
  wire core_clock;
  OptAccClockDiv3 u_core_clk_div (
    .clk_in(clk_300M),
    .rst(reset),
    .clk_out(core_clock)
  );
  reg [3:0] core_startup_reset_cnt;
  always @(posedge core_clock or posedge reset) begin
    if (reset)
      core_startup_reset_cnt <= 4'hF;
    else if (core_startup_reset_cnt != 4'd0)
      core_startup_reset_cnt <= core_startup_reset_cnt - 4'd1;
  end
  wire core_startup_reset = |core_startup_reset_cnt;

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
  wire        all_layers_mode = cfg_words[6][24];

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

  (* max_fanout = 16 *) reg [4:0] state;
  reg [31:0] issue_count;
  reg [31:0] recv_count;
  reg [7:0]  core_reset_cnt;
  reg [7:0]  preload_wait_cnt;
  reg        preload_full_wait;
  reg [31:0] stream_cnt;
  reg [15:0] run_token_idx;
  reg [3:0]  layer_idx;
  reg        active_weight_bank;
  reg        active_act_bank;
  reg        weight_init_bank_sel;
  reg        token_last_pending;
  reg        token_res_started;
  reg [9:0] token_last_core_addr;
  reg [10:0] writeback_idx;
  reg        result_done;
  reg        main_weight_drain_pending;
  reg        bg_weight_drain_pending;
  reg        preload_bank_session_reg;
  reg        phase_cmd_sent;
  (* max_fanout = 16 *) reg        rd_active;
  reg [3:0]  preload_layer_idx;
  reg [3:0]  pending_layer_idx;
  reg        pending_layer_switch;
  reg [3:0]  weight_bank_layer_idx [0:1];
  reg [1:0]  weight_bank_valid;
  reg        bg_preload_active;
  reg        bg_preload_bank_sel;
  reg [3:0]  bg_preload_layer_idx;
  reg [4:0]  bg_preload_state;
  reg [31:0] bg_issue_count;
  reg [31:0] bg_recv_count;
  reg        rd_bg_preload_active;
  (* max_fanout = 16 *) reg        rd_pipe_valid;
  reg        rd_pipe_bg_preload;
  reg [511:0] rd_pipe_data;

  reg        short_inputs_loaded;
  reg [SOFTMAX_SEQ_LEN-1:0]  sm_w_mem [0:SM_BEATS-1];
  reg [CFG_SM_BITS-1:0] sm_cfg_pack;
  integer sm_pack_i;
  wire [383:0] act_buf_rd_data [0:1];
  wire [383:0] act_buf_core_rd_data [0:1];
  wire [383:0] ln1_w_rd_data [0:1];
  wire [383:0] ln2_w_rd_data [0:1];
  wire [95:0]  qkv_b_rd_data [0:1];
  wire [383:0] out_b_rd_data [0:1];
  wire [95:0]  ffnup_b_rd_data [0:1];
  wire [383:0] ffndown_b_rd_data [0:1];
  reg  [SOFTMAX_SEQ_LEN-1:0] core_sm_w_mem [0:SM_BEATS-1];

  wire         act_buf_wen [0:1];
  wire [9:0]   act_buf_waddr [0:1];
  wire [383:0] act_buf_wdata [0:1];
  wire         act_buf_ren [0:1];
  wire [9:0]   act_buf_raddr [0:1];
  wire         act_buf_core_wen [0:1];
  wire [9:0]   act_buf_core_waddr [0:1];
  wire [383:0] act_buf_core_wdata [0:1];
  wire         act_buf_core_ren [0:1];
  wire [9:0]   act_buf_core_raddr [0:1];

  wire         ln1_w_wen [0:1];
  wire [6:0]   ln1_w_waddr [0:1];
  wire [383:0] ln1_w_wdata [0:1];
  wire         ln1_w_core_ren [0:1];
  wire [6:0]   ln1_w_core_raddr [0:1];

  wire         ln2_w_wen [0:1];
  wire [6:0]   ln2_w_waddr [0:1];
  wire [383:0] ln2_w_wdata [0:1];
  wire         ln2_w_core_ren [0:1];
  wire [6:0]   ln2_w_core_raddr [0:1];

  wire         qkv_b_wen [0:1];
  wire [7:0]   qkv_b_waddr [0:1];
  wire [95:0]  qkv_b_wdata [0:1];
  wire         qkv_b_core_ren [0:1];
  wire [7:0]   qkv_b_core_raddr [0:1];

  wire         out_b_wen [0:1];
  wire [5:0]   out_b_waddr [0:1];
  wire [383:0] out_b_wdata [0:1];
  wire         out_b_core_ren [0:1];
  wire [5:0]   out_b_core_raddr [0:1];

  wire         ffnup_b_wen [0:1];
  wire [7:0]   ffnup_b_waddr [0:1];
  wire [95:0]  ffnup_b_wdata [0:1];
  wire         ffnup_b_core_ren [0:1];
  wire [7:0]   ffnup_b_core_raddr [0:1];

  wire         ffndown_b_wen [0:1];
  wire [5:0]   ffndown_b_waddr [0:1];
  wire [383:0] ffndown_b_wdata [0:1];
  wire         ffndown_b_core_ren [0:1];
  wire [5:0]   ffndown_b_core_raddr [0:1];

  reg  [PHASE_CMD_W-1:0]   phase_cmd_wr_data;
  reg                      phase_cmd_wr_en;
  wire                     phase_cmd_wr_full;
  wire                     phase_cmd_wr_empty;
  wire [PHASE_CMD_W-1:0]   phase_cmd_rd_data;
  wire                     phase_cmd_rd_empty;
  wire                     phase_cmd_rd_valid;
  wire                     phase_cmd_rd_en;

  reg                      cfg_cmd_wr_en;
  reg  [CFG_CMD_W-1:0]     cfg_cmd_wr_data;
  wire                     cfg_cmd_wr_full;
  wire                     cfg_cmd_wr_empty;
  wire [CFG_CMD_W-1:0]     cfg_cmd_rd_data;
  wire                     cfg_cmd_rd_empty;
  wire                     cfg_cmd_rd_valid;
  wire                     cfg_cmd_rd_en;

  reg                      layer_cmd_wr_en;
  wire                     layer_cmd_wr_full;
  wire                     layer_cmd_wr_empty;
  wire                     layer_cmd_rd_empty;
  wire                     layer_cmd_rd_valid;
  wire                     layer_cmd_rd_en;
  wire [0:0]               layer_cmd_rd_data;

  wire [PHASE_DONE_W-1:0]  phase_done_rd_data;
  wire                     phase_done_rd_empty;
  wire                     phase_done_rd_valid;
  reg                      phase_done_rd_en;
  reg                      phase_done_wr_en;
  reg  [PHASE_DONE_W-1:0]  phase_done_wr_data;

  wire [TOKEN_DONE_W-1:0]  token_done_rd_data;
  wire                     token_done_rd_empty;
  wire                     token_done_rd_valid;
  reg                      token_done_rd_en;
  reg                      token_done_wr_en;
  reg  [TOKEN_DONE_W-1:0]  token_done_wr_data;

  reg                      qkv_w_fifo_wr_en;
  reg  [QKV_W_FIFO_W-1:0]  qkv_w_fifo_wr_data;
  wire                     qkv_w_fifo_wr_full;
  wire                     qkv_w_fifo_wr_empty;
  wire [QKV_W_FIFO_W-1:0]  qkv_w_fifo_rd_data;
  wire                     qkv_w_fifo_rd_empty;
  wire                     qkv_w_fifo_rd_valid;
  wire                     qkv_w_fifo_rd_en;

  reg                      out_w_fifo_wr_en;
  reg  [OUT_W_FIFO_W-1:0]  out_w_fifo_wr_data;
  wire                     out_w_fifo_wr_full;
  wire                     out_w_fifo_wr_empty;
  wire [OUT_W_FIFO_W-1:0]  out_w_fifo_rd_data;
  wire                     out_w_fifo_rd_empty;
  wire                     out_w_fifo_rd_valid;
  wire                     out_w_fifo_rd_en;

  reg                        ffnup_w_fifo_wr_en;
  reg  [FFNUP_W_FIFO_W-1:0]  ffnup_w_fifo_wr_data;
  wire                       ffnup_w_fifo_wr_full;
  wire                       ffnup_w_fifo_wr_empty;
  wire [FFNUP_W_FIFO_W-1:0]  ffnup_w_fifo_rd_data;
  wire                       ffnup_w_fifo_rd_empty;
  wire                       ffnup_w_fifo_rd_valid;
  wire                       ffnup_w_fifo_rd_en;

  reg                          ffndown_w_fifo_wr_en;
  reg  [FFNDOWN_W_FIFO_W-1:0]  ffndown_w_fifo_wr_data;
  wire                         ffndown_w_fifo_wr_full;
  wire                         ffndown_w_fifo_wr_empty;
  wire [FFNDOWN_W_FIFO_W-1:0]  ffndown_w_fifo_rd_data;
  wire                         ffndown_w_fifo_rd_empty;
  wire                         ffndown_w_fifo_rd_valid;
  wire                         ffndown_w_fifo_rd_en;

  reg        core_run_sync1;
  reg        core_run_sync2;
  reg        core_preload_bank_sync1;
  reg        core_preload_bank_sync2;
  reg        core_cfg_pending;
  reg        phase_active;
  reg [2:0]  phase_id_reg;
  reg        phase_bank_reg;
  reg [7:0]  phase_issue_idx;
  reg        phase_read_issue;
  reg [2:0]  phase_id_d;
  reg        phase_bank_d;
  reg        phase_valid_d;
  reg        phase_last_d;
  integer    core_sm_i;

  reg        core_active_weight_bank_r;
  reg        core_active_act_bank_r;
  reg [3:0]  core_cfg_seqlen_r;
  reg [15:0] core_attn_cfg_seqlen_r;
  reg [31:0] core_ln1_out_inv_scale_r;
  reg [7:0]  core_ln1_out_zero_point_r;
  reg [31:0] core_q_out_inv_scale_r;
  reg [31:0] core_k_out_inv_scale_r;
  reg [31:0] core_v_out_inv_scale_r;
  reg [31:0] core_q_bias_scale_r;
  reg [31:0] core_k_bias_scale_r;
  reg [31:0] core_v_bias_scale_r;
  reg [31:0] core_dm1_out_scale_r;
  reg [31:0] core_dm2_ctx_inv_scale_r;
  reg [7:0]  core_dm2_ctx_zero_point_r;
  reg [31:0] core_dm2_out_inv_scale_r;
  reg [31:0] core_out_out_scale_r;
  reg [31:0] core_ln2_out_inv_scale_r;
  reg [7:0]  core_ln2_out_zero_point_r;
  reg [31:0] core_ffnup_out_inv_scale_r;
  reg [31:0] core_ffnup_bias_scale_r;
  reg [31:0] core_ffndown_out_scale_r;
  reg        core_cfg_valid_pulse_r;
  reg        core_attn_cfg_valid_pulse_r;
  reg        core_layer_st_pulse_r;
  reg [383:0] core_ln1_w_in_r;
  reg [383:0] core_ln2_w_in_r;
  reg [95:0]  core_qkv_b_in_r;
  reg [383:0] core_out_b_in_r;
  reg [95:0]  core_ffnup_b_in_r;
  reg [383:0] core_ffndown_b_in_r;
  reg        core_ln_w_valid_r;
  reg        core_ln2_w_valid_r;
  reg        core_qkv_b_valid_r;
  reg        core_out_b_valid_r;
  reg        core_ffnup_b_valid_r;
  reg        core_ffndown_b_valid_r;

  reg [511:0] writeback_buf;
  reg [63:0]  cur_base_addr;
  reg [31:0]  cur_len;

  wire axi_rd_fire = rd_active && c0_ddr4_s_axi_rvalid && c0_ddr4_s_axi_rready;
  wire rd_fire = rd_pipe_valid;
  wire [511:0] rd_data = rd_pipe_data;

  wire [63:0] total_tokens_u64 = {48'd0, cfg_seqlen_word} + 64'd1;
  wire [63:0] total_output_beats_u64 = total_tokens_u64 << 6;
  wire [63:0] layers_base_addr = input_base_addr + (total_output_beats_u64 << 6);
  wire short_seq_all_layers_mode = all_layers_mode;
  wire [10:0] short_total_beats = ({6'd0, cfg_seqlen_word[4:0]} + 11'd1) << 6;
  wire [63:0] preload_layer_base_addr =
      layers_base_addr + ({60'd0, preload_layer_idx} * (64'd200540 << 6));
  wire [63:0] bg_preload_layer_base_addr =
      layers_base_addr + ({60'd0, bg_preload_layer_idx} * (64'd200540 << 6));
  wire [63:0] ln1_w_load_base_addr =
      short_seq_all_layers_mode ? (preload_layer_base_addr + (64'd2 << 6)) : ln1_w_base_addr;
  wire [63:0] qkv_w_load_base_addr =
      short_seq_all_layers_mode ? (preload_layer_base_addr + (64'd130 << 6)) : qkv_w_base_addr;
  wire [63:0] qkv_b_load_base_addr =
      short_seq_all_layers_mode ? (preload_layer_base_addr + (64'd49282 << 6)) : qkv_b_base_addr;
  wire [63:0] sm_load_base_addr =
      short_seq_all_layers_mode ? (preload_layer_base_addr + (64'd49474 << 6)) : sm_base_addr;
  wire [63:0] out_w_load_base_addr =
      short_seq_all_layers_mode ? (preload_layer_base_addr + (64'd49500 << 6)) : out_w_base_addr;
  wire [63:0] out_b_load_base_addr =
      short_seq_all_layers_mode ? (preload_layer_base_addr + (64'd66396 << 6)) : out_b_base_addr;
  wire [63:0] ln2_w_load_base_addr =
      short_seq_all_layers_mode ? (preload_layer_base_addr + (64'd66460 << 6)) : ln2_w_base_addr;
  wire [63:0] ffnup_w_load_base_addr =
      short_seq_all_layers_mode ? (preload_layer_base_addr + (64'd66588 << 6)) : ffnup_w_base_addr;
  wire [63:0] ffnup_b_load_base_addr =
      short_seq_all_layers_mode ? (preload_layer_base_addr + (64'd132636 << 6)) : ffnup_b_base_addr;
  wire [63:0] ffndown_w_load_base_addr =
      short_seq_all_layers_mode ? (preload_layer_base_addr + (64'd132892 << 6)) : ffndown_w_base_addr;
  wire [63:0] ffndown_b_load_base_addr =
      short_seq_all_layers_mode ? (preload_layer_base_addr + (64'd200476 << 6)) : ffndown_b_base_addr;
  wire [63:0] bg_ln1_w_load_base_addr = bg_preload_layer_base_addr + (64'd2 << 6);
  wire [63:0] bg_qkv_w_load_base_addr = bg_preload_layer_base_addr + (64'd130 << 6);
  wire [63:0] bg_qkv_b_load_base_addr = bg_preload_layer_base_addr + (64'd49282 << 6);
  wire [63:0] bg_sm_load_base_addr = bg_preload_layer_base_addr + (64'd49474 << 6);
  wire [63:0] bg_out_w_load_base_addr = bg_preload_layer_base_addr + (64'd49500 << 6);
  wire [63:0] bg_out_b_load_base_addr = bg_preload_layer_base_addr + (64'd66396 << 6);
  wire [63:0] bg_ln2_w_load_base_addr = bg_preload_layer_base_addr + (64'd66460 << 6);
  wire [63:0] bg_ffnup_w_load_base_addr = bg_preload_layer_base_addr + (64'd66588 << 6);
  wire [63:0] bg_ffnup_b_load_base_addr = bg_preload_layer_base_addr + (64'd132636 << 6);
  wire [63:0] bg_ffndown_w_load_base_addr = bg_preload_layer_base_addr + (64'd132892 << 6);
  wire [63:0] bg_ffndown_b_load_base_addr = bg_preload_layer_base_addr + (64'd200476 << 6);
  assign act_buf_ren[0] = (state == ST_WRITEBACK) && active_act_bank;
  assign act_buf_ren[1] = (state == ST_WRITEBACK) && !active_act_bank;
  assign act_buf_raddr[0] = writeback_idx[9:0];
  assign act_buf_raddr[1] = writeback_idx[9:0];
  assign act_buf_wen[0] = main_load_rd_fire && (state == ST_LOAD_TOKEN) && !active_act_bank;
  assign act_buf_wen[1] = main_load_rd_fire && (state == ST_LOAD_TOKEN) && active_act_bank;
  assign act_buf_waddr[0] = recv_count[9:0];
  assign act_buf_waddr[1] = recv_count[9:0];
  assign act_buf_wdata[0] = rd_data[383:0];
  assign act_buf_wdata[1] = rd_data[383:0];

  assign act_buf_core_ren[0] = core_run_sync2 && !core_active_act_bank_r;
  assign act_buf_core_ren[1] = core_run_sync2 && core_active_act_bank_r;
  assign act_buf_core_raddr[0] = core_data_in_addr[9:0];
  assign act_buf_core_raddr[1] = core_data_in_addr[9:0];
  assign act_buf_core_wen[0] = core_res_valid && core_active_act_bank_r;
  assign act_buf_core_wen[1] = core_res_valid && !core_active_act_bank_r;
  assign act_buf_core_waddr[0] = core_res_addr[9:0];
  assign act_buf_core_waddr[1] = core_res_addr[9:0];
  assign act_buf_core_wdata[0] = core_res;
  assign act_buf_core_wdata[1] = core_res;

  assign ln1_w_core_ren[0] = phase_read_issue && (phase_id_reg == PHASE_LN1) && !phase_bank_reg;
  assign ln1_w_core_ren[1] = phase_read_issue && (phase_id_reg == PHASE_LN1) && phase_bank_reg;
  assign ln1_w_core_raddr[0] = phase_issue_idx[6:0];
  assign ln1_w_core_raddr[1] = phase_issue_idx[6:0];
  assign ln1_w_wen[0] =
      (bg_load_rd_fire && (bg_preload_state == ST_LOAD_LN1) && !bg_preload_bank_sel) ||
      (main_load_rd_fire && (state == ST_LOAD_LN1) && !weight_init_bank_sel);
  assign ln1_w_wen[1] =
      (bg_load_rd_fire && (bg_preload_state == ST_LOAD_LN1) && bg_preload_bank_sel) ||
      (main_load_rd_fire && (state == ST_LOAD_LN1) && weight_init_bank_sel);
  assign ln1_w_waddr[0] = (bg_load_rd_fire && (bg_preload_state == ST_LOAD_LN1))
                              ? bg_recv_count[6:0] : recv_count[6:0];
  assign ln1_w_waddr[1] = (bg_load_rd_fire && (bg_preload_state == ST_LOAD_LN1))
                              ? bg_recv_count[6:0] : recv_count[6:0];
  assign ln1_w_wdata[0] = rd_data[383:0];
  assign ln1_w_wdata[1] = rd_data[383:0];

  assign ln2_w_core_ren[0] = phase_read_issue && (phase_id_reg == PHASE_LN2) && !phase_bank_reg;
  assign ln2_w_core_ren[1] = phase_read_issue && (phase_id_reg == PHASE_LN2) && phase_bank_reg;
  assign ln2_w_core_raddr[0] = phase_issue_idx[6:0];
  assign ln2_w_core_raddr[1] = phase_issue_idx[6:0];
  assign ln2_w_wen[0] =
      (bg_load_rd_fire && (bg_preload_state == ST_LOAD_LN2) && !bg_preload_bank_sel) ||
      (main_load_rd_fire && (state == ST_LOAD_LN2) && !weight_init_bank_sel);
  assign ln2_w_wen[1] =
      (bg_load_rd_fire && (bg_preload_state == ST_LOAD_LN2) && bg_preload_bank_sel) ||
      (main_load_rd_fire && (state == ST_LOAD_LN2) && weight_init_bank_sel);
  assign ln2_w_waddr[0] = (bg_load_rd_fire && (bg_preload_state == ST_LOAD_LN2))
                              ? bg_recv_count[6:0] : recv_count[6:0];
  assign ln2_w_waddr[1] = (bg_load_rd_fire && (bg_preload_state == ST_LOAD_LN2))
                              ? bg_recv_count[6:0] : recv_count[6:0];
  assign ln2_w_wdata[0] = rd_data[383:0];
  assign ln2_w_wdata[1] = rd_data[383:0];

  assign qkv_b_core_ren[0] = phase_read_issue && (phase_id_reg == PHASE_QKV_B) && !phase_bank_reg;
  assign qkv_b_core_ren[1] = phase_read_issue && (phase_id_reg == PHASE_QKV_B) && phase_bank_reg;
  assign qkv_b_core_raddr[0] = phase_issue_idx[7:0];
  assign qkv_b_core_raddr[1] = phase_issue_idx[7:0];
  assign qkv_b_wen[0] =
      (bg_load_rd_fire && (bg_preload_state == ST_LOAD_QKV_B) && !bg_preload_bank_sel) ||
      (main_load_rd_fire && (state == ST_LOAD_QKV_B) && !weight_init_bank_sel);
  assign qkv_b_wen[1] =
      (bg_load_rd_fire && (bg_preload_state == ST_LOAD_QKV_B) && bg_preload_bank_sel) ||
      (main_load_rd_fire && (state == ST_LOAD_QKV_B) && weight_init_bank_sel);
  assign qkv_b_waddr[0] = (bg_load_rd_fire && (bg_preload_state == ST_LOAD_QKV_B))
                              ? bg_recv_count[7:0] : recv_count[7:0];
  assign qkv_b_waddr[1] = (bg_load_rd_fire && (bg_preload_state == ST_LOAD_QKV_B))
                              ? bg_recv_count[7:0] : recv_count[7:0];
  assign qkv_b_wdata[0] = rd_data[95:0];
  assign qkv_b_wdata[1] = rd_data[95:0];

  assign out_b_core_ren[0] = phase_read_issue && (phase_id_reg == PHASE_OUT_B) && !phase_bank_reg;
  assign out_b_core_ren[1] = phase_read_issue && (phase_id_reg == PHASE_OUT_B) && phase_bank_reg;
  assign out_b_core_raddr[0] = phase_issue_idx[5:0];
  assign out_b_core_raddr[1] = phase_issue_idx[5:0];
  assign out_b_wen[0] =
      (bg_load_rd_fire && (bg_preload_state == ST_LOAD_OUT_B) && !bg_preload_bank_sel) ||
      (main_load_rd_fire && (state == ST_LOAD_OUT_B) && !weight_init_bank_sel);
  assign out_b_wen[1] =
      (bg_load_rd_fire && (bg_preload_state == ST_LOAD_OUT_B) && bg_preload_bank_sel) ||
      (main_load_rd_fire && (state == ST_LOAD_OUT_B) && weight_init_bank_sel);
  assign out_b_waddr[0] = (bg_load_rd_fire && (bg_preload_state == ST_LOAD_OUT_B))
                              ? bg_recv_count[5:0] : recv_count[5:0];
  assign out_b_waddr[1] = (bg_load_rd_fire && (bg_preload_state == ST_LOAD_OUT_B))
                              ? bg_recv_count[5:0] : recv_count[5:0];
  assign out_b_wdata[0] = rd_data[383:0];
  assign out_b_wdata[1] = rd_data[383:0];

  assign ffnup_b_core_ren[0] = phase_read_issue && (phase_id_reg == PHASE_FFNUP_B) && !phase_bank_reg;
  assign ffnup_b_core_ren[1] = phase_read_issue && (phase_id_reg == PHASE_FFNUP_B) && phase_bank_reg;
  assign ffnup_b_core_raddr[0] = phase_issue_idx[7:0];
  assign ffnup_b_core_raddr[1] = phase_issue_idx[7:0];
  assign ffnup_b_wen[0] =
      (bg_load_rd_fire && (bg_preload_state == ST_LOAD_FFNUP_B) && !bg_preload_bank_sel) ||
      (main_load_rd_fire && (state == ST_LOAD_FFNUP_B) && !weight_init_bank_sel);
  assign ffnup_b_wen[1] =
      (bg_load_rd_fire && (bg_preload_state == ST_LOAD_FFNUP_B) && bg_preload_bank_sel) ||
      (main_load_rd_fire && (state == ST_LOAD_FFNUP_B) && weight_init_bank_sel);
  assign ffnup_b_waddr[0] = (bg_load_rd_fire && (bg_preload_state == ST_LOAD_FFNUP_B))
                                ? bg_recv_count[7:0] : recv_count[7:0];
  assign ffnup_b_waddr[1] = (bg_load_rd_fire && (bg_preload_state == ST_LOAD_FFNUP_B))
                                ? bg_recv_count[7:0] : recv_count[7:0];
  assign ffnup_b_wdata[0] = rd_data[95:0];
  assign ffnup_b_wdata[1] = rd_data[95:0];

  assign ffndown_b_core_ren[0] = phase_read_issue && (phase_id_reg == PHASE_FFNDOWN_B) && !phase_bank_reg;
  assign ffndown_b_core_ren[1] = phase_read_issue && (phase_id_reg == PHASE_FFNDOWN_B) && phase_bank_reg;
  assign ffndown_b_core_raddr[0] = phase_issue_idx[5:0];
  assign ffndown_b_core_raddr[1] = phase_issue_idx[5:0];
  assign ffndown_b_wen[0] =
      (bg_load_rd_fire && (bg_preload_state == ST_LOAD_FFNDOWN_B) && !bg_preload_bank_sel) ||
      (main_load_rd_fire && (state == ST_LOAD_FFNDOWN_B) && !weight_init_bank_sel);
  assign ffndown_b_wen[1] =
      (bg_load_rd_fire && (bg_preload_state == ST_LOAD_FFNDOWN_B) && bg_preload_bank_sel) ||
      (main_load_rd_fire && (state == ST_LOAD_FFNDOWN_B) && weight_init_bank_sel);
  assign ffndown_b_waddr[0] = (bg_load_rd_fire && (bg_preload_state == ST_LOAD_FFNDOWN_B))
                                  ? bg_recv_count[5:0] : recv_count[5:0];
  assign ffndown_b_waddr[1] = (bg_load_rd_fire && (bg_preload_state == ST_LOAD_FFNDOWN_B))
                                  ? bg_recv_count[5:0] : recv_count[5:0];
  assign ffndown_b_wdata[0] = rd_data[383:0];
  assign ffndown_b_wdata[1] = rd_data[383:0];

  genvar bank_i;
  generate
    for (bank_i = 0; bank_i < 2; bank_i = bank_i + 1) begin : gen_wrapper_bank_mem
      OptAccDualClockMem #(.WIDTH(384), .DEPTH(SHORT_SEQ_TOTAL_BEATS), .ADDR_W(10)) act_buf_mem (
        .a_clk(clock), .a_write_en(act_buf_wen[bank_i]), .a_write_addr(act_buf_waddr[bank_i]),
        .a_write_data(act_buf_wdata[bank_i]), .a_read_en(act_buf_ren[bank_i]),
        .a_read_addr(act_buf_raddr[bank_i]), .a_read_data(act_buf_rd_data[bank_i]),
        .b_clk(core_clock), .b_write_en(act_buf_core_wen[bank_i]), .b_write_addr(act_buf_core_waddr[bank_i]),
        .b_write_data(act_buf_core_wdata[bank_i]), .b_read_en(act_buf_core_ren[bank_i]),
        .b_read_addr(act_buf_core_raddr[bank_i]), .b_read_data(act_buf_core_rd_data[bank_i])
      );
      OptAccDualClockMem #(.WIDTH(384), .DEPTH(LN_WEIGHT_BEATS), .ADDR_W(7)) ln1_w_mem (
        .a_clk(clock), .a_write_en(ln1_w_wen[bank_i]), .a_write_addr(ln1_w_waddr[bank_i]),
        .a_write_data(ln1_w_wdata[bank_i]), .a_read_en(1'b0), .a_read_addr({7{1'b0}}),
        .a_read_data(), .b_clk(core_clock), .b_write_en(1'b0), .b_write_addr({7{1'b0}}),
        .b_write_data({384{1'b0}}), .b_read_en(ln1_w_core_ren[bank_i]),
        .b_read_addr(ln1_w_core_raddr[bank_i]), .b_read_data(ln1_w_rd_data[bank_i])
      );
      OptAccDualClockMem #(.WIDTH(384), .DEPTH(LN_WEIGHT_BEATS), .ADDR_W(7)) ln2_w_mem (
        .a_clk(clock), .a_write_en(ln2_w_wen[bank_i]), .a_write_addr(ln2_w_waddr[bank_i]),
        .a_write_data(ln2_w_wdata[bank_i]), .a_read_en(1'b0), .a_read_addr({7{1'b0}}),
        .a_read_data(), .b_clk(core_clock), .b_write_en(1'b0), .b_write_addr({7{1'b0}}),
        .b_write_data({384{1'b0}}), .b_read_en(ln2_w_core_ren[bank_i]),
        .b_read_addr(ln2_w_core_raddr[bank_i]), .b_read_data(ln2_w_rd_data[bank_i])
      );
      OptAccDualClockMem #(.WIDTH(96), .DEPTH(QKV_BIAS_BEATS), .ADDR_W(8)) qkv_b_mem (
        .a_clk(clock), .a_write_en(qkv_b_wen[bank_i]), .a_write_addr(qkv_b_waddr[bank_i]),
        .a_write_data(qkv_b_wdata[bank_i]), .a_read_en(1'b0), .a_read_addr({8{1'b0}}),
        .a_read_data(), .b_clk(core_clock), .b_write_en(1'b0), .b_write_addr({8{1'b0}}),
        .b_write_data({96{1'b0}}), .b_read_en(qkv_b_core_ren[bank_i]),
        .b_read_addr(qkv_b_core_raddr[bank_i]), .b_read_data(qkv_b_rd_data[bank_i])
      );
      OptAccDualClockMem #(.WIDTH(384), .DEPTH(OUT_BIAS_BEATS), .ADDR_W(6)) out_b_mem (
        .a_clk(clock), .a_write_en(out_b_wen[bank_i]), .a_write_addr(out_b_waddr[bank_i]),
        .a_write_data(out_b_wdata[bank_i]), .a_read_en(1'b0), .a_read_addr({6{1'b0}}),
        .a_read_data(), .b_clk(core_clock), .b_write_en(1'b0), .b_write_addr({6{1'b0}}),
        .b_write_data({384{1'b0}}), .b_read_en(out_b_core_ren[bank_i]),
        .b_read_addr(out_b_core_raddr[bank_i]), .b_read_data(out_b_rd_data[bank_i])
      );
      OptAccDualClockMem #(.WIDTH(96), .DEPTH(FFNUP_BIAS_BEATS), .ADDR_W(8)) ffnup_b_mem (
        .a_clk(clock), .a_write_en(ffnup_b_wen[bank_i]), .a_write_addr(ffnup_b_waddr[bank_i]),
        .a_write_data(ffnup_b_wdata[bank_i]), .a_read_en(1'b0), .a_read_addr({8{1'b0}}),
        .a_read_data(), .b_clk(core_clock), .b_write_en(1'b0), .b_write_addr({8{1'b0}}),
        .b_write_data({96{1'b0}}), .b_read_en(ffnup_b_core_ren[bank_i]),
        .b_read_addr(ffnup_b_core_raddr[bank_i]), .b_read_data(ffnup_b_rd_data[bank_i])
      );
      OptAccDualClockMem #(.WIDTH(384), .DEPTH(FFNDOWN_BIAS_BEATS), .ADDR_W(6)) ffndown_b_mem (
        .a_clk(clock), .a_write_en(ffndown_b_wen[bank_i]), .a_write_addr(ffndown_b_waddr[bank_i]),
        .a_write_data(ffndown_b_wdata[bank_i]), .a_read_en(1'b0), .a_read_addr({6{1'b0}}),
        .a_read_data(), .b_clk(core_clock), .b_write_en(1'b0), .b_write_addr({6{1'b0}}),
        .b_write_data({384{1'b0}}), .b_read_en(ffndown_b_core_ren[bank_i]),
        .b_read_addr(ffndown_b_core_raddr[bank_i]), .b_read_data(ffndown_b_rd_data[bank_i])
      );
    end
  endgenerate
  wire run_last_token = (run_token_idx == cfg_seqlen_word);
  wire run_last_layer = (layer_idx == (NUM_LAYERS[3:0] - 4'd1));
  wire [3:0] next_layer_idx_w = layer_idx + 4'd1;
  wire next_weight_bank = ~active_weight_bank;
  wire next_layer_bank_ready =
      weight_bank_valid[next_weight_bank] &&
      (weight_bank_layer_idx[next_weight_bank] == next_layer_idx_w);
  wire is_load_state =
      state == ST_LOAD_LN1 || state == ST_LOAD_QKV_W || state == ST_LOAD_QKV_B ||
      state == ST_LOAD_SM || state == ST_LOAD_OUT_W || state == ST_LOAD_OUT_B ||
      state == ST_LOAD_LN2 || state == ST_LOAD_FFNUP_W || state == ST_LOAD_FFNUP_B ||
      state == ST_LOAD_FFNDOWN_W || state == ST_LOAD_FFNDOWN_B || state == ST_LOAD_TOKEN;
  wire [63:0] issue_addr64 = cur_base_addr + ({32'd0, issue_count} << 6);
  reg [63:0] bg_cur_base_addr;
  reg [31:0] bg_cur_len;
  wire [63:0] bg_issue_addr64 = bg_cur_base_addr + ({32'd0, bg_issue_count} << 6);
  wire bg_preload_issue = bg_preload_active && (bg_issue_count < bg_cur_len);
  wire [7:0] preload_wait_target = preload_full_wait ? 8'd191 : 8'd15;
  wire short_writeback_state = (state == ST_WRITEBACK);
  wire write_state = short_writeback_state;
  wire [63:0] write_issue_addr64 =
      output_base_addr + ({53'd0, writeback_idx} * output_stride_bytes);
  wire all_weight_fifos_empty =
      qkv_w_fifo_wr_empty && out_w_fifo_wr_empty && ffnup_w_fifo_wr_empty && ffndown_w_fifo_wr_empty;
  wire qkv_w_load_ready =
      (state == ST_LOAD_QKV_W || bg_preload_state == ST_LOAD_QKV_W) ? !qkv_w_fifo_wr_full : 1'b1;
  wire out_w_load_ready =
      (state == ST_LOAD_OUT_W || bg_preload_state == ST_LOAD_OUT_W) ? !out_w_fifo_wr_full : 1'b1;
  wire ffnup_w_load_ready =
      (state == ST_LOAD_FFNUP_W || bg_preload_state == ST_LOAD_FFNUP_W) ? !ffnup_w_fifo_wr_full : 1'b1;
  wire ffndown_w_load_ready =
      (state == ST_LOAD_FFNDOWN_W || bg_preload_state == ST_LOAD_FFNDOWN_W) ? !ffndown_w_fifo_wr_full : 1'b1;
  wire load_target_ready = qkv_w_load_ready && out_w_load_ready && ffnup_w_load_ready && ffndown_w_load_ready;
  wire [47:0] core_attn_tap_data;
  wire [3:0] core_attn_tap_head;
  wire [31:0] core_attn_tap_addr;
  wire core_attn_tap_valid;
  wire core_attn_tap_last;
  wire core_attn_dm1_override_ready;
  wire core_attn_dm2_v_override_ready;
  wire core_attn_dm1_override_enable = 1'b0;
  wire [31:0] core_attn_dm1_override_data = 32'd0;
  wire core_attn_dm1_override_st = 1'b0;
  wire [8:0] core_attn_dm1_override_addr = 9'd0;
  wire core_attn_dm1_override_valid = 1'b0;
  wire core_attn_dm1_override_last = 1'b0;
  wire core_attn_dm2_v_override_enable = 1'b0;
  wire [511:0] core_attn_dm2_v_override_data = 512'd0;
  wire core_attn_dm2_v_override_valid = 1'b0;
  wire [10:0] core_sm_w_addr;
  wire [31:0] core_data_in_addr;
  wire [383:0] core_res;
  wire core_res_st;
  wire [9:0] core_res_addr;
  wire core_res_valid;
  wire core_res_last;
  wire core_res_ready = 1'b1;
  (* max_fanout = 16 *) wire main_load_rd_fire = rd_fire && !rd_pipe_bg_preload;
  (* max_fanout = 16 *) wire bg_load_rd_fire = rd_fire && rd_pipe_bg_preload;
  wire [383:0] act_buf_writeback_data = active_act_bank ? act_buf_rd_data[0] : act_buf_rd_data[1];
  wire [383:0] core_data_in = core_active_act_bank_r ? act_buf_core_rd_data[1] : act_buf_core_rd_data[0];
  wire [3:0] core_cfg_seqlen = core_cfg_seqlen_r;
  wire core_cfg_prefill = 1'b1;
  wire [15:0] core_attn_cfg_seqlen = core_attn_cfg_seqlen_r;
  wire core_attn_cfg_prefill = 1'b0;
  wire core_attn_cfg_single_query = 1'b1;
  wire core_layer_st = core_layer_st_pulse_r;
  wire core_cfg_valid = core_cfg_valid_pulse_r;
  wire core_attn_cfg_valid = core_attn_cfg_valid_pulse_r;
  wire core_ln_w_valid = core_ln_w_valid_r;
  wire core_ln2_w_valid = core_ln2_w_valid_r;
  wire core_qkv_b_valid = core_qkv_b_valid_r;
  wire core_out_b_valid = core_out_b_valid_r;
  wire core_ffnup_b_valid = core_ffnup_b_valid_r;
  wire core_ffndown_b_valid = core_ffndown_b_valid_r;
  wire core_reset = reset | core_startup_reset;
  wire [383:0] core_ln1_w_in = core_ln1_w_in_r;
  wire [383:0] core_ln2_w_in = core_ln2_w_in_r;
  wire [95:0]  core_qkv_b_in = core_qkv_b_in_r;
  wire [383:0] core_out_b_in = core_out_b_in_r;
  wire [95:0]  core_ffnup_b_in = core_ffnup_b_in_r;
  wire [383:0] core_ffndown_b_in = core_ffndown_b_in_r;
  wire [SOFTMAX_SEQ_LEN-1:0] core_sm_w_in =
      (core_sm_w_addr < SM_BEATS[10:0]) ? core_sm_w_mem[core_sm_w_addr[4:0]]
                                        : {SOFTMAX_SEQ_LEN{1'b0}};
  wire [287:0] core_qkv_w_in = 288'd0;
  wire [287:0] core_out_w_in = 288'd0;
  wire [287:0] core_ffnup_w_in = 288'd0;
  wire [287:0] core_ffndown_w_in = 288'd0;
  wire core_qkv_w_preload_valid = qkv_w_fifo_rd_valid;
  wire [15:0] core_qkv_w_preload_addr = qkv_w_fifo_rd_data[QKV_W_FIFO_W-1:288];
  wire [287:0] core_qkv_w_preload_data = qkv_w_fifo_rd_data[287:0];
  wire core_out_w_preload_valid = out_w_fifo_rd_valid;
  wire [14:0] core_out_w_preload_addr = out_w_fifo_rd_data[OUT_W_FIFO_W-1:288];
  wire [287:0] core_out_w_preload_data = out_w_fifo_rd_data[287:0];
  wire core_ffnup_w_preload_valid = ffnup_w_fifo_rd_valid;
  wire [16:0] core_ffnup_w_preload_addr = ffnup_w_fifo_rd_data[FFNUP_W_FIFO_W-1:288];
  wire [287:0] core_ffnup_w_preload_data = ffnup_w_fifo_rd_data[287:0];
  wire core_ffndown_w_preload_valid = ffndown_w_fifo_rd_valid;
  wire [16:0] core_ffndown_w_preload_addr = ffndown_w_fifo_rd_data[FFNDOWN_W_FIFO_W-1:288];
  wire [287:0] core_ffndown_w_preload_data = ffndown_w_fifo_rd_data[287:0];
  assign qkv_w_fifo_rd_en = !qkv_w_fifo_rd_empty;
  assign out_w_fifo_rd_en = !out_w_fifo_rd_empty;
  assign ffnup_w_fifo_rd_en = !ffnup_w_fifo_rd_empty;
  assign ffndown_w_fifo_rd_en = !ffndown_w_fifo_rd_empty;
  assign phase_cmd_rd_en = !phase_active && !phase_cmd_rd_empty;
  assign cfg_cmd_rd_en = !cfg_cmd_rd_empty;
  assign layer_cmd_rd_en = !layer_cmd_rd_empty;
  assign cnn0_batch_count = {2'd0, (state != ST_IDLE)};
  assign cnn0_result_count = {2'd0, result_done};

  always @(*) begin
    for (sm_pack_i = 0; sm_pack_i < SM_BEATS; sm_pack_i = sm_pack_i + 1)
      sm_cfg_pack[sm_pack_i * SOFTMAX_SEQ_LEN +: SOFTMAX_SEQ_LEN] = sm_w_mem[sm_pack_i];
  end

  OptAccAsyncFifo #(.WIDTH(PHASE_CMD_W), .ADDR_W(2)) u_phase_cmd_fifo (
    .wr_clk(clock), .wr_rst(reset), .wr_en(phase_cmd_wr_en), .wr_data(phase_cmd_wr_data),
    .wr_full(phase_cmd_wr_full), .wr_empty(phase_cmd_wr_empty),
    .rd_clk(core_clock), .rd_rst(reset), .rd_en(phase_cmd_rd_en), .rd_data(phase_cmd_rd_data),
    .rd_empty(phase_cmd_rd_empty), .rd_valid(phase_cmd_rd_valid)
  );
  OptAccAsyncFifo #(.WIDTH(CFG_CMD_W), .ADDR_W(2)) u_cfg_cmd_fifo (
    .wr_clk(clock), .wr_rst(reset), .wr_en(cfg_cmd_wr_en), .wr_data(cfg_cmd_wr_data),
    .wr_full(cfg_cmd_wr_full), .wr_empty(cfg_cmd_wr_empty),
    .rd_clk(core_clock), .rd_rst(reset), .rd_en(cfg_cmd_rd_en), .rd_data(cfg_cmd_rd_data),
    .rd_empty(cfg_cmd_rd_empty), .rd_valid(cfg_cmd_rd_valid)
  );
  OptAccAsyncFifo #(.WIDTH(1), .ADDR_W(2)) u_layer_cmd_fifo (
    .wr_clk(clock), .wr_rst(reset), .wr_en(layer_cmd_wr_en), .wr_data(1'b1),
    .wr_full(layer_cmd_wr_full), .wr_empty(layer_cmd_wr_empty),
    .rd_clk(core_clock), .rd_rst(reset), .rd_en(layer_cmd_rd_en), .rd_data(layer_cmd_rd_data),
    .rd_empty(layer_cmd_rd_empty), .rd_valid(layer_cmd_rd_valid)
  );
  OptAccAsyncFifo #(.WIDTH(PHASE_DONE_W), .ADDR_W(2)) u_phase_done_fifo (
    .wr_clk(core_clock), .wr_rst(reset), .wr_en(phase_done_wr_en), .wr_data(phase_done_wr_data),
    .wr_full(), .wr_empty(),
    .rd_clk(clock), .rd_rst(reset), .rd_en(phase_done_rd_en), .rd_data(phase_done_rd_data),
    .rd_empty(phase_done_rd_empty), .rd_valid(phase_done_rd_valid)
  );
  OptAccAsyncFifo #(.WIDTH(TOKEN_DONE_W), .ADDR_W(2)) u_token_done_fifo (
    .wr_clk(core_clock), .wr_rst(reset), .wr_en(token_done_wr_en), .wr_data(token_done_wr_data),
    .wr_full(), .wr_empty(),
    .rd_clk(clock), .rd_rst(reset), .rd_en(token_done_rd_en), .rd_data(token_done_rd_data),
    .rd_empty(token_done_rd_empty), .rd_valid(token_done_rd_valid)
  );
  OptAccAsyncFifo #(.WIDTH(QKV_W_FIFO_W), .ADDR_W(9)) u_qkv_w_fifo (
    .wr_clk(clock), .wr_rst(reset), .wr_en(qkv_w_fifo_wr_en), .wr_data(qkv_w_fifo_wr_data),
    .wr_full(qkv_w_fifo_wr_full), .wr_empty(qkv_w_fifo_wr_empty),
    .rd_clk(core_clock), .rd_rst(reset), .rd_en(qkv_w_fifo_rd_en), .rd_data(qkv_w_fifo_rd_data),
    .rd_empty(qkv_w_fifo_rd_empty), .rd_valid(qkv_w_fifo_rd_valid)
  );
  OptAccAsyncFifo #(.WIDTH(OUT_W_FIFO_W), .ADDR_W(8)) u_out_w_fifo (
    .wr_clk(clock), .wr_rst(reset), .wr_en(out_w_fifo_wr_en), .wr_data(out_w_fifo_wr_data),
    .wr_full(out_w_fifo_wr_full), .wr_empty(out_w_fifo_wr_empty),
    .rd_clk(core_clock), .rd_rst(reset), .rd_en(out_w_fifo_rd_en), .rd_data(out_w_fifo_rd_data),
    .rd_empty(out_w_fifo_rd_empty), .rd_valid(out_w_fifo_rd_valid)
  );
  OptAccAsyncFifo #(.WIDTH(FFNUP_W_FIFO_W), .ADDR_W(9)) u_ffnup_w_fifo (
    .wr_clk(clock), .wr_rst(reset), .wr_en(ffnup_w_fifo_wr_en), .wr_data(ffnup_w_fifo_wr_data),
    .wr_full(ffnup_w_fifo_wr_full), .wr_empty(ffnup_w_fifo_wr_empty),
    .rd_clk(core_clock), .rd_rst(reset), .rd_en(ffnup_w_fifo_rd_en), .rd_data(ffnup_w_fifo_rd_data),
    .rd_empty(ffnup_w_fifo_rd_empty), .rd_valid(ffnup_w_fifo_rd_valid)
  );
  OptAccAsyncFifo #(.WIDTH(FFNDOWN_W_FIFO_W), .ADDR_W(9)) u_ffndown_w_fifo (
    .wr_clk(clock), .wr_rst(reset), .wr_en(ffndown_w_fifo_wr_en), .wr_data(ffndown_w_fifo_wr_data),
    .wr_full(ffndown_w_fifo_wr_full), .wr_empty(ffndown_w_fifo_wr_empty),
    .rd_clk(core_clock), .rd_rst(reset), .rd_en(ffndown_w_fifo_rd_en), .rd_data(ffndown_w_fifo_rd_data),
    .rd_empty(ffndown_w_fifo_rd_empty), .rd_valid(ffndown_w_fifo_rd_valid)
  );

  always @(posedge core_clock or posedge reset) begin
    if (reset) begin
      core_run_sync1 <= 1'b0;
      core_run_sync2 <= 1'b0;
      core_preload_bank_sync1 <= 1'b0;
      core_preload_bank_sync2 <= 1'b0;
      core_active_weight_bank_r <= 1'b0;
      core_active_act_bank_r <= 1'b0;
      core_cfg_seqlen_r <= 4'd0;
      core_attn_cfg_seqlen_r <= 16'd0;
      core_ln1_out_inv_scale_r <= 32'd0;
      core_ln1_out_zero_point_r <= 8'd0;
      core_q_out_inv_scale_r <= 32'd0;
      core_k_out_inv_scale_r <= 32'd0;
      core_v_out_inv_scale_r <= 32'd0;
      core_q_bias_scale_r <= 32'd0;
      core_k_bias_scale_r <= 32'd0;
      core_v_bias_scale_r <= 32'd0;
      core_dm1_out_scale_r <= 32'd0;
      core_dm2_ctx_inv_scale_r <= 32'd0;
      core_dm2_ctx_zero_point_r <= 8'd0;
      core_dm2_out_inv_scale_r <= 32'd0;
      core_out_out_scale_r <= 32'd0;
      core_ln2_out_inv_scale_r <= 32'd0;
      core_ln2_out_zero_point_r <= 8'd0;
      core_ffnup_out_inv_scale_r <= 32'd0;
      core_ffnup_bias_scale_r <= 32'd0;
      core_ffndown_out_scale_r <= 32'd0;
      core_cfg_valid_pulse_r <= 1'b0;
      core_attn_cfg_valid_pulse_r <= 1'b0;
      core_layer_st_pulse_r <= 1'b0;
      core_ln_w_valid_r <= 1'b0;
      core_ln2_w_valid_r <= 1'b0;
      core_qkv_b_valid_r <= 1'b0;
      core_out_b_valid_r <= 1'b0;
      core_ffnup_b_valid_r <= 1'b0;
      core_ffndown_b_valid_r <= 1'b0;
      phase_active <= 1'b0;
      phase_id_reg <= 3'd0;
      phase_bank_reg <= 1'b0;
      phase_issue_idx <= 8'd0;
      phase_read_issue <= 1'b0;
      phase_id_d <= 3'd0;
      phase_bank_d <= 1'b0;
      phase_valid_d <= 1'b0;
      phase_last_d <= 1'b0;
      phase_done_wr_en <= 1'b0;
      phase_done_wr_data <= {PHASE_DONE_W{1'b0}};
      token_done_wr_en <= 1'b0;
      token_done_wr_data <= {TOKEN_DONE_W{1'b0}};
      for (core_sm_i = 0; core_sm_i < SM_BEATS; core_sm_i = core_sm_i + 1)
        core_sm_w_mem[core_sm_i] <= {SOFTMAX_SEQ_LEN{1'b0}};
    end else begin
      core_run_sync1 <= (state == ST_RUN);
      core_run_sync2 <= core_run_sync1;
      core_preload_bank_sync1 <= preload_bank_session_reg;
      core_preload_bank_sync2 <= core_preload_bank_sync1;
      core_cfg_valid_pulse_r <= 1'b0;
      core_attn_cfg_valid_pulse_r <= 1'b0;
      core_layer_st_pulse_r <= 1'b0;
      core_ln_w_valid_r <= 1'b0;
      core_ln2_w_valid_r <= 1'b0;
      core_qkv_b_valid_r <= 1'b0;
      core_out_b_valid_r <= 1'b0;
      core_ffnup_b_valid_r <= 1'b0;
      core_ffndown_b_valid_r <= 1'b0;
      phase_read_issue <= 1'b0;
      phase_valid_d <= 1'b0;
      phase_last_d <= 1'b0;
      phase_done_wr_en <= 1'b0;
      token_done_wr_en <= 1'b0;

      if (cfg_cmd_rd_valid) begin
        {core_active_weight_bank_r, core_active_act_bank_r, core_cfg_seqlen_r,
         core_attn_cfg_seqlen_r, core_ln1_out_inv_scale_r, core_q_out_inv_scale_r,
         core_k_out_inv_scale_r, core_v_out_inv_scale_r, core_q_bias_scale_r,
         core_k_bias_scale_r, core_v_bias_scale_r, core_dm1_out_scale_r,
         core_dm2_ctx_inv_scale_r, core_dm2_out_inv_scale_r, core_out_out_scale_r,
         core_ln2_out_inv_scale_r, core_ffnup_out_inv_scale_r, core_ffnup_bias_scale_r,
         core_ffndown_out_scale_r, core_ln1_out_zero_point_r, core_dm2_ctx_zero_point_r,
         core_ln2_out_zero_point_r} <= cfg_cmd_rd_data[CFG_CMD_W-1:CFG_SM_BITS];
        for (core_sm_i = 0; core_sm_i < SM_BEATS; core_sm_i = core_sm_i + 1)
          core_sm_w_mem[core_sm_i] <= cfg_cmd_rd_data[core_sm_i * SOFTMAX_SEQ_LEN +: SOFTMAX_SEQ_LEN];
        core_cfg_valid_pulse_r <= 1'b1;
        core_attn_cfg_valid_pulse_r <= 1'b1;
      end

      if (layer_cmd_rd_valid)
        core_layer_st_pulse_r <= 1'b1;

      if (!phase_active && phase_cmd_rd_valid) begin
        phase_active <= 1'b1;
        phase_id_reg <= phase_cmd_rd_data[2:0];
        phase_bank_reg <= phase_cmd_rd_data[3];
        phase_issue_idx <= 8'd0;
      end else if (phase_active) begin
        phase_read_issue <= 1'b1;
        phase_id_d <= phase_id_reg;
        phase_bank_d <= phase_bank_reg;
        phase_valid_d <= 1'b1;
        case (phase_id_reg)
          PHASE_LN1,
          PHASE_LN2: begin
            phase_last_d <= (phase_issue_idx == 8'd127);
            if (phase_issue_idx == 8'd127)
              phase_active <= 1'b0;
            else
              phase_issue_idx <= phase_issue_idx + 8'd1;
          end
          PHASE_QKV_B: begin
            phase_last_d <= (phase_issue_idx == 8'd191);
            if (phase_issue_idx == 8'd191)
              phase_active <= 1'b0;
            else
              phase_issue_idx <= phase_issue_idx + 8'd1;
          end
          PHASE_OUT_B: begin
            phase_last_d <= (phase_issue_idx == 8'd63);
            if (phase_issue_idx == 8'd63)
              phase_active <= 1'b0;
            else
              phase_issue_idx <= phase_issue_idx + 8'd1;
          end
          PHASE_FFNUP_B: begin
            phase_last_d <= (phase_issue_idx == 8'd255);
            if (phase_issue_idx == 8'd255)
              phase_active <= 1'b0;
            else
              phase_issue_idx <= phase_issue_idx + 8'd1;
          end
          default: begin
            phase_last_d <= (phase_issue_idx == 8'd63);
            if (phase_issue_idx == 8'd63)
              phase_active <= 1'b0;
            else
              phase_issue_idx <= phase_issue_idx + 8'd1;
          end
        endcase
      end

      if (phase_valid_d) begin
        case (phase_id_d)
          PHASE_LN1: begin
            core_ln_w_valid_r <= 1'b1;
            core_ln1_w_in_r <= phase_bank_d ? ln1_w_rd_data[1] : ln1_w_rd_data[0];
          end
          PHASE_LN2: begin
            core_ln2_w_valid_r <= 1'b1;
            core_ln2_w_in_r <= phase_bank_d ? ln2_w_rd_data[1] : ln2_w_rd_data[0];
          end
          PHASE_QKV_B: begin
            core_qkv_b_valid_r <= 1'b1;
            core_qkv_b_in_r <= phase_bank_d ? qkv_b_rd_data[1] : qkv_b_rd_data[0];
          end
          PHASE_OUT_B: begin
            core_out_b_valid_r <= 1'b1;
            core_out_b_in_r <= phase_bank_d ? out_b_rd_data[1] : out_b_rd_data[0];
          end
          PHASE_FFNUP_B: begin
            core_ffnup_b_valid_r <= 1'b1;
            core_ffnup_b_in_r <= phase_bank_d ? ffnup_b_rd_data[1] : ffnup_b_rd_data[0];
          end
          default: begin
            core_ffndown_b_valid_r <= 1'b1;
            core_ffndown_b_in_r <= phase_bank_d ? ffndown_b_rd_data[1] : ffndown_b_rd_data[0];
          end
        endcase
        if (phase_last_d) begin
          phase_done_wr_en <= 1'b1;
          phase_done_wr_data <= phase_id_d;
        end
      end

      if (core_res_valid && core_res_last) begin
        token_done_wr_en <= 1'b1;
        token_done_wr_data <= core_res_addr;
      end
    end
  end

  Top u_core (
    .clock(core_clock),
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
    .io_weight_active_bank(core_active_weight_bank_r),
    .io_weight_preload_bank(core_preload_bank_sync2),
    .io_data_in(core_data_in),
    .io_data_in_ready(core_run_sync2),
    .io_data_in_addr(core_data_in_addr),
    .io_attn_tap_data(core_attn_tap_data),
    .io_attn_tap_head(core_attn_tap_head),
    .io_attn_tap_addr(core_attn_tap_addr),
    .io_attn_tap_valid(core_attn_tap_valid),
    .io_attn_tap_last(core_attn_tap_last),
    .io_attn_dm1_override_enable(core_attn_dm1_override_enable),
    .io_attn_dm1_override_data(core_attn_dm1_override_data),
    .io_attn_dm1_override_st(core_attn_dm1_override_st),
    .io_attn_dm1_override_addr(core_attn_dm1_override_addr[8:0]),
    .io_attn_dm1_override_valid(core_attn_dm1_override_valid),
    .io_attn_dm1_override_last(core_attn_dm1_override_last),
    .io_attn_dm1_override_ready(core_attn_dm1_override_ready),
    .io_attn_dm2_v_override_enable(core_attn_dm2_v_override_enable),
    .io_attn_dm2_v_override_data(core_attn_dm2_v_override_data),
    .io_attn_dm2_v_override_valid(core_attn_dm2_v_override_valid),
    .io_attn_dm2_v_override_ready(core_attn_dm2_v_override_ready),
    .io_ln_w_in(core_ln1_w_in),
    .io_ln_w_valid(core_ln_w_valid),
    .io_ln1_out_inv_scale(core_ln1_out_inv_scale_r),
    .io_ln1_out_zero_point(core_ln1_out_zero_point_r),
    .io_q_out_inv_scale(core_q_out_inv_scale_r),
    .io_k_out_inv_scale(core_k_out_inv_scale_r),
    .io_v_out_inv_scale(core_v_out_inv_scale_r),
    .io_q_bias_scale(core_q_bias_scale_r),
    .io_k_bias_scale(core_k_bias_scale_r),
    .io_v_bias_scale(core_v_bias_scale_r),
    .io_dm1_out_scale(core_dm1_out_scale_r),
    .io_dm2_ctx_inv_scale(core_dm2_ctx_inv_scale_r),
    .io_dm2_ctx_zero_point(core_dm2_ctx_zero_point_r),
    .io_dm2_out_inv_scale(core_dm2_out_inv_scale_r),
    .io_out_out_scale(core_out_out_scale_r),
    .io_ln2_out_inv_scale(core_ln2_out_inv_scale_r),
    .io_ln2_out_zero_point(core_ln2_out_zero_point_r),
    .io_ffnup_out_inv_scale(core_ffnup_out_inv_scale_r),
    .io_ffnup_bias_scale(core_ffnup_bias_scale_r),
    .io_ffndown_out_scale(core_ffndown_out_scale_r),
    .io_qkv_w_in(core_qkv_w_in),
    .io_qkv_w_addr(),
    .io_qkv_w_preload_valid(core_qkv_w_preload_valid),
    .io_qkv_w_preload_addr(core_qkv_w_preload_addr),
    .io_qkv_w_preload_data(core_qkv_w_preload_data),
    .io_qkv_b_in(core_qkv_b_in),
    .io_qkv_b_valid(core_qkv_b_valid),
    .io_sm_w_in(core_sm_w_in),
    .io_sm_w_addr(core_sm_w_addr),
    .io_out_w_in(core_out_w_in),
    .io_out_w_addr(),
    .io_out_w_preload_valid(core_out_w_preload_valid),
    .io_out_w_preload_addr(core_out_w_preload_addr),
    .io_out_w_preload_data(core_out_w_preload_data),
    .io_out_b_in(core_out_b_in),
    .io_out_b_valid(core_out_b_valid),
    .io_ln2_w_in(core_ln2_w_in),
    .io_ln2_w_valid(core_ln2_w_valid),
    .io_ffnup_w_in(core_ffnup_w_in),
    .io_ffnup_w_addr(),
    .io_ffnup_w_preload_valid(core_ffnup_w_preload_valid),
    .io_ffnup_w_preload_addr(core_ffnup_w_preload_addr),
    .io_ffnup_w_preload_data(core_ffnup_w_preload_data),
    .io_ffnup_b_in(core_ffnup_b_in),
    .io_ffnup_b_valid(core_ffnup_b_valid),
    .io_ffndown_w_in(core_ffndown_w_in),
    .io_ffndown_w_addr(),
    .io_ffndown_w_preload_valid(core_ffndown_w_preload_valid),
    .io_ffndown_w_preload_addr(core_ffndown_w_preload_addr),
    .io_ffndown_w_preload_data(core_ffndown_w_preload_data),
    .io_ffndown_b_in(core_ffndown_b_in),
    .io_ffndown_b_valid(core_ffndown_b_valid),
    .io_res(core_res),
    .io_res_st(core_res_st),
    .io_res_addr(core_res_addr[9:0]),
    .io_res_valid(core_res_valid),
    .io_res_last(core_res_last),
    .io_res_ready(core_res_ready)
  );

  always @(*) begin
    qkv_w_fifo_wr_en = 1'b0;
    qkv_w_fifo_wr_data = {QKV_W_FIFO_W{1'b0}};
    out_w_fifo_wr_en = 1'b0;
    out_w_fifo_wr_data = {OUT_W_FIFO_W{1'b0}};
    ffnup_w_fifo_wr_en = 1'b0;
    ffnup_w_fifo_wr_data = {FFNUP_W_FIFO_W{1'b0}};
    ffndown_w_fifo_wr_en = 1'b0;
    ffndown_w_fifo_wr_data = {FFNDOWN_W_FIFO_W{1'b0}};
    phase_cmd_wr_en = 1'b0;
    phase_cmd_wr_data = {PHASE_CMD_W{1'b0}};
    cfg_cmd_wr_en = 1'b0;
    cfg_cmd_wr_data = {
      active_weight_bank,
      active_act_bank,
      cfg_seqlen_word[3:0],
      run_token_idx,
      ln1_out_inv_scale,
      q_out_inv_scale,
      k_out_inv_scale,
      v_out_inv_scale,
      q_bias_scale,
      k_bias_scale,
      v_bias_scale,
      dm1_out_scale,
      dm2_ctx_inv_scale,
      dm2_out_inv_scale,
      out_out_scale,
      ln2_out_inv_scale,
      ffnup_out_inv_scale,
      ffnup_bias_scale,
      ffndown_out_scale,
      ln1_zero_point,
      dm2_ctx_zero_point,
      ln2_zero_point,
      sm_cfg_pack
    };
    layer_cmd_wr_en = 1'b0;
    phase_done_rd_en = 1'b0;
    token_done_rd_en = 1'b0;

    if (main_load_rd_fire) begin
      case (state)
        ST_LOAD_QKV_W: begin
          qkv_w_fifo_wr_en = 1'b1;
          qkv_w_fifo_wr_data = {recv_count[15:0], rd_data[287:0]};
        end
        ST_LOAD_OUT_W: begin
          out_w_fifo_wr_en = 1'b1;
          out_w_fifo_wr_data = {recv_count[14:0], rd_data[287:0]};
        end
        ST_LOAD_FFNUP_W: begin
          ffnup_w_fifo_wr_en = 1'b1;
          ffnup_w_fifo_wr_data = {recv_count[16:0], rd_data[287:0]};
        end
        ST_LOAD_FFNDOWN_W: begin
          ffndown_w_fifo_wr_en = 1'b1;
          ffndown_w_fifo_wr_data = {recv_count[16:0], rd_data[287:0]};
        end
        default: begin end
      endcase
    end
    if (bg_load_rd_fire) begin
      case (bg_preload_state)
        ST_LOAD_QKV_W: begin
          qkv_w_fifo_wr_en = 1'b1;
          qkv_w_fifo_wr_data = {bg_recv_count[15:0], rd_data[287:0]};
        end
        ST_LOAD_OUT_W: begin
          out_w_fifo_wr_en = 1'b1;
          out_w_fifo_wr_data = {bg_recv_count[14:0], rd_data[287:0]};
        end
        ST_LOAD_FFNUP_W: begin
          ffnup_w_fifo_wr_en = 1'b1;
          ffnup_w_fifo_wr_data = {bg_recv_count[16:0], rd_data[287:0]};
        end
        ST_LOAD_FFNDOWN_W: begin
          ffndown_w_fifo_wr_en = 1'b1;
          ffndown_w_fifo_wr_data = {bg_recv_count[16:0], rd_data[287:0]};
        end
        default: begin end
      endcase
    end

    if (!phase_cmd_sent && !phase_cmd_wr_full) begin
      case (state)
        ST_STREAM_LN1:       begin phase_cmd_wr_en = 1'b1; phase_cmd_wr_data = {active_weight_bank, PHASE_LN1}; end
        ST_STREAM_LN2:       begin phase_cmd_wr_en = 1'b1; phase_cmd_wr_data = {active_weight_bank, PHASE_LN2}; end
        ST_STREAM_QKV_B:     begin phase_cmd_wr_en = 1'b1; phase_cmd_wr_data = {active_weight_bank, PHASE_QKV_B}; end
        ST_STREAM_OUT_B:     begin phase_cmd_wr_en = 1'b1; phase_cmd_wr_data = {active_weight_bank, PHASE_OUT_B}; end
        ST_STREAM_FFNUP_B:   begin phase_cmd_wr_en = 1'b1; phase_cmd_wr_data = {active_weight_bank, PHASE_FFNUP_B}; end
        ST_STREAM_FFNDOWN_B: begin phase_cmd_wr_en = 1'b1; phase_cmd_wr_data = {active_weight_bank, PHASE_FFNDOWN_B}; end
        default: begin end
      endcase
    end

    if (phase_cmd_sent && !phase_done_rd_empty)
      phase_done_rd_en = 1'b1;

    if ((state == ST_RUN) && !token_done_rd_empty)
      token_done_rd_en = 1'b1;

    if ((state == ST_RUN_CFG) && all_weight_fifos_empty && !cfg_cmd_wr_full)
      cfg_cmd_wr_en = 1'b1;

    if ((state == ST_PRELOAD_PULSE) && !layer_cmd_wr_full)
      layer_cmd_wr_en = 1'b1;
  end

  always @(*) begin
    case (state)
      ST_LOAD_TOKEN:      begin
                            cur_base_addr = input_base_addr;
                            cur_len = {21'd0, short_total_beats};
                          end
      ST_LOAD_LN1:        begin cur_base_addr = ln1_w_load_base_addr;     cur_len = LN_WEIGHT_BEATS; end
      ST_LOAD_QKV_W:      begin cur_base_addr = qkv_w_load_base_addr;     cur_len = QKV_WEIGHT_BEATS; end
      ST_LOAD_QKV_B:      begin cur_base_addr = qkv_b_load_base_addr;     cur_len = QKV_BIAS_BEATS; end
      ST_LOAD_SM:         begin cur_base_addr = sm_load_base_addr;        cur_len = SM_BEATS; end
      ST_LOAD_OUT_W:      begin cur_base_addr = out_w_load_base_addr;     cur_len = OUT_WEIGHT_BEATS; end
      ST_LOAD_OUT_B:      begin cur_base_addr = out_b_load_base_addr;     cur_len = OUT_BIAS_BEATS; end
      ST_LOAD_LN2:        begin cur_base_addr = ln2_w_load_base_addr;     cur_len = LN_WEIGHT_BEATS; end
      ST_LOAD_FFNUP_W:    begin cur_base_addr = ffnup_w_load_base_addr;   cur_len = FFNUP_WEIGHT_BEATS; end
      ST_LOAD_FFNUP_B:    begin cur_base_addr = ffnup_b_load_base_addr;   cur_len = FFNUP_BIAS_BEATS; end
      ST_LOAD_FFNDOWN_W:  begin cur_base_addr = ffndown_w_load_base_addr; cur_len = FFNDOWN_WEIGHT_BEATS; end
      ST_LOAD_FFNDOWN_B:  begin cur_base_addr = ffndown_b_load_base_addr; cur_len = FFNDOWN_BIAS_BEATS; end
      default:            begin cur_base_addr = 64'd0;               cur_len = 32'd0; end
    endcase
  end

  always @(*) begin
    case (bg_preload_state)
      ST_LOAD_LN1:        begin bg_cur_base_addr = bg_ln1_w_load_base_addr;     bg_cur_len = LN_WEIGHT_BEATS; end
      ST_LOAD_QKV_W:      begin bg_cur_base_addr = bg_qkv_w_load_base_addr;     bg_cur_len = QKV_WEIGHT_BEATS; end
      ST_LOAD_QKV_B:      begin bg_cur_base_addr = bg_qkv_b_load_base_addr;     bg_cur_len = QKV_BIAS_BEATS; end
      ST_LOAD_SM:         begin bg_cur_base_addr = bg_sm_load_base_addr;        bg_cur_len = SM_BEATS; end
      ST_LOAD_OUT_W:      begin bg_cur_base_addr = bg_out_w_load_base_addr;     bg_cur_len = OUT_WEIGHT_BEATS; end
      ST_LOAD_OUT_B:      begin bg_cur_base_addr = bg_out_b_load_base_addr;     bg_cur_len = OUT_BIAS_BEATS; end
      ST_LOAD_LN2:        begin bg_cur_base_addr = bg_ln2_w_load_base_addr;     bg_cur_len = LN_WEIGHT_BEATS; end
      ST_LOAD_FFNUP_W:    begin bg_cur_base_addr = bg_ffnup_w_load_base_addr;   bg_cur_len = FFNUP_WEIGHT_BEATS; end
      ST_LOAD_FFNUP_B:    begin bg_cur_base_addr = bg_ffnup_b_load_base_addr;   bg_cur_len = FFNUP_BIAS_BEATS; end
      ST_LOAD_FFNDOWN_W:  begin bg_cur_base_addr = bg_ffndown_w_load_base_addr; bg_cur_len = FFNDOWN_WEIGHT_BEATS; end
      ST_LOAD_FFNDOWN_B:  begin bg_cur_base_addr = bg_ffndown_b_load_base_addr; bg_cur_len = FFNDOWN_BIAS_BEATS; end
      default:            begin bg_cur_base_addr = 64'd0;                        bg_cur_len = 32'd0; end
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
      layer_idx <= 4'd0;
      preload_full_wait <= 1'b1;
      active_weight_bank <= 1'b0;
      active_act_bank <= 1'b0;
      weight_init_bank_sel <= 1'b0;
      token_last_pending <= 1'b0;
      token_res_started <= 1'b0;
      token_last_core_addr <= 10'd0;
      writeback_idx <= 11'd0;
      main_weight_drain_pending <= 1'b0;
      bg_weight_drain_pending <= 1'b0;
      preload_bank_session_reg <= 1'b0;
      phase_cmd_sent <= 1'b0;
      cfg_shadow <= 704'd0;
      cfg_active <= 704'd0;
      cfg_loaded <= 1'b0;
      result_done <= 1'b0;
      rd_active <= 1'b0;
      preload_layer_idx <= 4'd0;
      pending_layer_idx <= 4'd0;
      pending_layer_switch <= 1'b0;
      weight_bank_layer_idx[0] <= 4'd0;
      weight_bank_layer_idx[1] <= 4'd0;
      weight_bank_valid <= 2'b00;
      bg_preload_active <= 1'b0;
      bg_preload_bank_sel <= 1'b0;
      bg_preload_layer_idx <= 4'd0;
      bg_preload_state <= ST_IDLE;
      bg_issue_count <= 32'd0;
      bg_recv_count <= 32'd0;
      rd_bg_preload_active <= 1'b0;
      rd_pipe_valid <= 1'b0;
      rd_pipe_bg_preload <= 1'b0;
      rd_pipe_data <= 512'd0;
      short_inputs_loaded <= 1'b0;

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
      if (phase_cmd_wr_en)
        phase_cmd_sent <= 1'b1;
      if (phase_done_rd_valid)
        phase_cmd_sent <= 1'b0;
      if (main_weight_drain_pending && all_weight_fifos_empty) begin
        main_weight_drain_pending <= 1'b0;
        weight_bank_valid[weight_init_bank_sel] <= 1'b1;
        weight_bank_layer_idx[weight_init_bank_sel] <= preload_layer_idx;
      end
      if (bg_weight_drain_pending && all_weight_fifos_empty) begin
        bg_weight_drain_pending <= 1'b0;
        bg_preload_active <= 1'b0;
        weight_bank_valid[bg_preload_bank_sel] <= 1'b1;
        weight_bank_layer_idx[bg_preload_bank_sel] <= bg_preload_layer_idx;
      end
      if (cfg_data_valid)
        cfg_shadow <= cfg_data;
      if (cfg_done) begin
        cfg_active <= cfg_data_valid ? cfg_data : cfg_shadow;
        cfg_loaded <= 1'b1;
      end

      if (state == ST_DONE && cnn0_result_batch_clear) begin
        result_done <= 1'b0;
        state <= ST_IDLE;
      end

      if (!c0_ddr4_s_axi_arvalid && !rd_active && c0_init_calib_complete &&
          load_target_ready &&
          ((is_load_state && (issue_count < cur_len)) || bg_preload_issue)) begin
        c0_ddr4_s_axi_arid <= 4'd0;
        if (is_load_state)
          c0_ddr4_s_axi_araddr <= issue_addr64[36:0];
        else
          c0_ddr4_s_axi_araddr <= bg_issue_addr64[36:0];
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
        rd_bg_preload_active <= !is_load_state && bg_preload_issue;
        if (is_load_state)
          issue_count <= issue_count + 32'd1;
        else
          bg_issue_count <= bg_issue_count + 32'd1;
      end

      if (axi_rd_fire) begin
        rd_active <= 1'b0;
        c0_ddr4_s_axi_rready <= 1'b0;
        rd_bg_preload_active <= 1'b0;
        rd_pipe_valid <= 1'b1;
        rd_pipe_bg_preload <= rd_bg_preload_active;
        rd_pipe_data <= c0_ddr4_s_axi_rdata;
      end else if (rd_fire) begin
        rd_pipe_valid <= 1'b0;
      end

      if (rd_fire) begin
        if (rd_pipe_bg_preload) begin
          case (bg_preload_state)
            ST_LOAD_SM:         sm_w_mem[bg_recv_count[4:0]] <= rd_data[SOFTMAX_SEQ_LEN-1:0];
            default: begin end
          endcase
        end else begin
          case (state)
            ST_LOAD_SM:         sm_w_mem[recv_count[4:0]] <= rd_data[SOFTMAX_SEQ_LEN-1:0];
            default: begin end
          endcase
        end

        if (rd_pipe_bg_preload) begin
          if (bg_recv_count + 32'd1 == bg_cur_len) begin
            bg_issue_count <= 32'd0;
            bg_recv_count <= 32'd0;
            case (bg_preload_state)
              ST_LOAD_LN1:        bg_preload_state <= ST_LOAD_QKV_W;
              ST_LOAD_QKV_W:      bg_preload_state <= ST_LOAD_QKV_B;
              ST_LOAD_QKV_B:      bg_preload_state <= ST_LOAD_SM;
              ST_LOAD_SM:         bg_preload_state <= ST_LOAD_OUT_W;
              ST_LOAD_OUT_W:      bg_preload_state <= ST_LOAD_OUT_B;
              ST_LOAD_OUT_B:      bg_preload_state <= ST_LOAD_LN2;
              ST_LOAD_LN2:        bg_preload_state <= ST_LOAD_FFNUP_W;
              ST_LOAD_FFNUP_W:    bg_preload_state <= ST_LOAD_FFNUP_B;
              ST_LOAD_FFNUP_B:    bg_preload_state <= ST_LOAD_FFNDOWN_W;
              ST_LOAD_FFNDOWN_W:  bg_preload_state <= ST_LOAD_FFNDOWN_B;
              ST_LOAD_FFNDOWN_B:  begin
                                    bg_weight_drain_pending <= 1'b1;
                                    bg_preload_state <= ST_IDLE;
                                  end
              default: begin end
            endcase
          end else begin
            bg_recv_count <= bg_recv_count + 32'd1;
          end
        end else if (recv_count + 32'd1 == cur_len) begin
          issue_count <= 32'd0;
          recv_count <= 32'd0;
          case (state)
            ST_LOAD_TOKEN:      begin
                                  short_inputs_loaded <= 1'b1;
                                  stream_cnt <= 32'd0;
                                  state <= ST_STREAM_LN1;
                                end
            ST_LOAD_LN1:        begin state <= ST_LOAD_QKV_W; end
            ST_LOAD_QKV_W:      begin state <= ST_LOAD_QKV_B; end
            ST_LOAD_QKV_B:      state <= ST_LOAD_SM;
            ST_LOAD_SM:         state <= ST_LOAD_OUT_W;
            ST_LOAD_OUT_W:      begin state <= ST_LOAD_OUT_B; end
            ST_LOAD_OUT_B:      state <= ST_LOAD_LN2;
            ST_LOAD_LN2:        state <= ST_LOAD_FFNUP_W;
            ST_LOAD_FFNUP_W:    begin state <= ST_LOAD_FFNUP_B; end
            ST_LOAD_FFNUP_B:    state <= ST_LOAD_FFNDOWN_W;
            ST_LOAD_FFNDOWN_W:  begin state <= ST_LOAD_FFNDOWN_B; end
            ST_LOAD_FFNDOWN_B:  begin
                                  main_weight_drain_pending <= 1'b1;
                                  phase_cmd_sent <= 1'b0;
                                  if (!short_inputs_loaded)
                                    state <= ST_LOAD_TOKEN;
                                  else
                                    state <= ST_STREAM_LN1;
                                end
            default: begin end
          endcase
        end else begin
          recv_count <= recv_count + 32'd1;
        end
      end

      if (!c0_ddr4_s_axi_awvalid && !c0_ddr4_s_axi_wvalid && !c0_ddr4_s_axi_bready &&
          write_state &&
          (writeback_idx < short_total_beats) &&
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
        writeback_buf <= {128'd0, act_buf_writeback_data};
      end

      if (c0_ddr4_s_axi_awvalid && c0_ddr4_s_axi_awready) begin
        c0_ddr4_s_axi_awvalid <= 1'b0;
        c0_ddr4_s_axi_wdata <= writeback_buf;
        c0_ddr4_s_axi_wstrb <= 64'h0000FFFFFFFFFFFF;
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
        if (short_writeback_state) begin
          if (writeback_idx + 11'd1 == short_total_beats) begin
            writeback_idx <= 11'd0;
            state <= ST_DONE;
            result_done <= 1'b1;
`ifndef SYNTHESIS
            $display("opt_acc_core shortseq-done layers=%0d beats=%0d",
                     NUM_LAYERS, short_total_beats);
`endif
          end else begin
            writeback_idx <= writeback_idx + 11'd1;
          end
        end
      end

      case (state)
        ST_IDLE: begin
          issue_count <= 32'd0;
          recv_count <= 32'd0;
          run_token_idx <= 16'd0;
          layer_idx <= 4'd0;
          preload_full_wait <= 1'b1;
          active_weight_bank <= 1'b0;
          active_act_bank <= 1'b0;
          weight_init_bank_sel <= 1'b0;
          preload_layer_idx <= 4'd0;
          pending_layer_idx <= 4'd0;
          pending_layer_switch <= 1'b0;
          weight_bank_layer_idx[0] <= 4'd0;
          weight_bank_layer_idx[1] <= 4'd0;
          weight_bank_valid <= 2'b00;
          bg_preload_active <= 1'b0;
          bg_preload_bank_sel <= 1'b0;
          bg_preload_layer_idx <= 4'd0;
          bg_preload_state <= ST_IDLE;
          bg_issue_count <= 32'd0;
          bg_recv_count <= 32'd0;
          rd_bg_preload_active <= 1'b0;
          rd_pipe_valid <= 1'b0;
          short_inputs_loaded <= 1'b0;
          main_weight_drain_pending <= 1'b0;
          bg_weight_drain_pending <= 1'b0;
          phase_cmd_sent <= 1'b0;
          preload_bank_session_reg <= 1'b0;
          token_last_pending <= 1'b0;
          token_res_started <= 1'b0;
          writeback_idx <= 11'd0;
          if (cfg_loaded && c0_init_calib_complete && cnn0_input_batch_set) begin
            result_done <= 1'b0;
            preload_bank_session_reg <= 1'b0;
            state <= ST_LOAD_LN1;
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
          if (phase_done_rd_valid) begin
            phase_cmd_sent <= 1'b0;
            state <= ST_STREAM_LN2;
          end
        end
        ST_STREAM_LN2: begin
          if (phase_done_rd_valid) begin
            phase_cmd_sent <= 1'b0;
            state <= ST_STREAM_QKV_B;
          end
        end
        ST_STREAM_QKV_B: begin
          if (phase_done_rd_valid) begin
            phase_cmd_sent <= 1'b0;
            state <= ST_STREAM_OUT_B;
          end
        end
        ST_STREAM_OUT_B: begin
          if (phase_done_rd_valid) begin
            phase_cmd_sent <= 1'b0;
            state <= ST_STREAM_FFNUP_B;
          end
        end
        ST_STREAM_FFNUP_B: begin
          if (phase_done_rd_valid) begin
            phase_cmd_sent <= 1'b0;
            state <= ST_STREAM_FFNDOWN_B;
          end
        end
        ST_STREAM_FFNDOWN_B: begin
          if (phase_done_rd_valid) begin
            phase_cmd_sent <= 1'b0;
            token_last_pending <= 1'b0;
            token_res_started <= 1'b0;
            preload_full_wait <= 1'b1;
            state <= ST_RUN_CFG;
          end
        end
        ST_PIPE_SCHED: begin
          // Long-sequence token scheduling has been removed.
          state <= ST_IDLE;
        end
        ST_RUN_CFG: begin
          token_res_started <= 1'b0;
          if (cfg_cmd_wr_en)
            state <= ST_PRELOAD_PULSE;
        end
        ST_PRELOAD_PULSE: begin
          if (layer_cmd_wr_en) begin
            state <= ST_PRELOAD_WAIT;
            preload_wait_cnt <= 8'd0;
          end
        end
        ST_PRELOAD_WAIT: begin
          preload_wait_cnt <= preload_wait_cnt + 8'd1;
          if (preload_wait_cnt == preload_wait_target) begin
            preload_full_wait <= 1'b0;
            if (short_seq_all_layers_mode && !run_last_layer &&
                !next_layer_bank_ready && !bg_preload_active) begin
              bg_preload_active <= 1'b1;
              bg_preload_bank_sel <= next_weight_bank;
              bg_preload_layer_idx <= next_layer_idx_w;
              bg_preload_state <= ST_LOAD_LN1;
              bg_issue_count <= 32'd0;
              bg_recv_count <= 32'd0;
              bg_weight_drain_pending <= 1'b0;
              preload_bank_session_reg <= next_weight_bank;
              weight_bank_valid[next_weight_bank] <= 1'b0;
            end
            state <= ST_RUN;
          end
        end
        ST_RUN: begin
          if (token_done_rd_valid) begin
            token_last_pending <= 1'b0;
            token_res_started <= 1'b0;
            token_last_core_addr <= token_done_rd_data[9:0];
`ifndef SYNTHESIS
            $display("opt_acc_core token-done layer=%0d token=%0d cfg_seqlen=%0d run_last_token=%0d run_last_layer=%0d core_res_addr=%0d",
                     layer_idx, run_token_idx, cfg_seqlen_word, run_last_token, run_last_layer, token_done_rd_data[9:0]);
`endif
            if (run_last_layer) begin
              writeback_idx <= 11'd0;
              state <= ST_WRITEBACK;
`ifndef SYNTHESIS
              $display("opt_acc_core shortseq-layer-done layer=%0d final=1 beats=%0d",
                       layer_idx, short_total_beats);
`endif
            end else if (short_seq_all_layers_mode) begin
              if (next_layer_bank_ready) begin
                layer_idx <= next_layer_idx_w;
                active_weight_bank <= next_weight_bank;
                active_act_bank <= ~active_act_bank;
                preload_full_wait <= 1'b1;
                phase_cmd_sent <= 1'b0;
                state <= ST_STREAM_LN1;
`ifndef SYNTHESIS
                $display("opt_acc_core shortseq-layer-switch next_layer=%0d active_weight_bank=%0d active_act_bank=%0d",
                         next_layer_idx_w, next_weight_bank, ~active_act_bank);
`endif
              end else begin
                pending_layer_idx <= next_layer_idx_w;
                pending_layer_switch <= 1'b1;
                if (!bg_preload_active) begin
                  bg_preload_active <= 1'b1;
                  bg_preload_bank_sel <= next_weight_bank;
                  bg_preload_layer_idx <= next_layer_idx_w;
                  bg_preload_state <= ST_LOAD_LN1;
                  bg_issue_count <= 32'd0;
                  bg_recv_count <= 32'd0;
                  bg_weight_drain_pending <= 1'b0;
                  preload_bank_session_reg <= next_weight_bank;
                  weight_bank_valid[next_weight_bank] <= 1'b0;
                end
                state <= ST_KVHIST_PREP;
`ifndef SYNTHESIS
                $display("opt_acc_core shortseq-layer-preload target_layer=%0d target_bank=%0d",
                         next_layer_idx_w, next_weight_bank);
`endif
              end
            end else begin
              layer_idx <= layer_idx + 4'd1;
              active_weight_bank <= ~active_weight_bank;
              active_act_bank <= ~active_act_bank;
              preload_full_wait <= 1'b1;
              phase_cmd_sent <= 1'b0;
              state <= ST_STREAM_LN1;
`ifndef SYNTHESIS
              $display("opt_acc_core shortseq-layer-switch next_layer=%0d active_weight_bank=%0d active_act_bank=%0d",
                       layer_idx + 4'd1, ~active_weight_bank, ~active_act_bank);
`endif
            end
          end
        end
        ST_KVHIST_PREP: begin
          if (pending_layer_switch && next_layer_bank_ready) begin
            pending_layer_switch <= 1'b0;
            layer_idx <= pending_layer_idx;
            active_weight_bank <= next_weight_bank;
            active_act_bank <= ~active_act_bank;
            preload_full_wait <= 1'b1;
            phase_cmd_sent <= 1'b0;
            state <= ST_STREAM_LN1;
`ifndef SYNTHESIS
            $display("opt_acc_core shortseq-layer-switch next_layer=%0d active_weight_bank=%0d active_act_bank=%0d",
                     pending_layer_idx, next_weight_bank, ~active_act_bank);
`endif
          end
        end
        ST_KVHIST_WRITE: begin state <= ST_IDLE; end
        ST_REPLAY_PREP: begin state <= ST_IDLE; end
        ST_REPLAY_READ: begin state <= ST_IDLE; end
        ST_REPLAY_STREAM: begin state <= ST_IDLE; end
        ST_WRITEBACK: begin end
        ST_DONE: begin end
        default: begin end
      endcase
    end
  end
endmodule
