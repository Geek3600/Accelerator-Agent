module app_shell_9p_cnn_core_0_1(
  input clk_300M,
  input clk_600M,
  input [703:0] cfg_data,
  input cfg_data_valid,
  input cfg_done,
  input cnn0_input_batch_set,
  output [2:0] cnn0_batch_count,
  input cnn0_result_batch_clear,
  output [2:0] cnn0_result_count,
  input user_rst,
  output [3:0] c0_ddr4_s_axi_awid,
  output [36:0] c0_ddr4_s_axi_awaddr,
  output [7:0] c0_ddr4_s_axi_awlen,
  output [2:0] c0_ddr4_s_axi_awsize,
  output [1:0] c0_ddr4_s_axi_awburst,
  output c0_ddr4_s_axi_awlock,
  output [3:0] c0_ddr4_s_axi_awcache,
  output [2:0] c0_ddr4_s_axi_awprot,
  output c0_ddr4_s_axi_awvalid,
  input c0_ddr4_s_axi_awready,
  output [511:0] c0_ddr4_s_axi_wdata,
  output [63:0] c0_ddr4_s_axi_wstrb,
  output c0_ddr4_s_axi_wlast,
  output c0_ddr4_s_axi_wvalid,
  input c0_ddr4_s_axi_wready,
  output c0_ddr4_s_axi_bready,
  input [3:0] c0_ddr4_s_axi_bid,
  input [1:0] c0_ddr4_s_axi_bresp,
  input c0_ddr4_s_axi_bvalid,
  output [3:0] c0_ddr4_s_axi_arid,
  output [36:0] c0_ddr4_s_axi_araddr,
  output [7:0] c0_ddr4_s_axi_arlen,
  output [2:0] c0_ddr4_s_axi_arsize,
  output [1:0] c0_ddr4_s_axi_arburst,
  output c0_ddr4_s_axi_arlock,
  output [3:0] c0_ddr4_s_axi_arcache,
  output [2:0] c0_ddr4_s_axi_arprot,
  output c0_ddr4_s_axi_arvalid,
  input c0_ddr4_s_axi_arready,
  output c0_ddr4_s_axi_rready,
  input c0_ddr4_s_axi_rlast,
  input c0_ddr4_s_axi_rvalid,
  input [1:0] c0_ddr4_s_axi_rresp,
  input [3:0] c0_ddr4_s_axi_rid,
  input [511:0] c0_ddr4_s_axi_rdata,
  input c0_ddr4_s_axi_clk,
  input c0_ddr4_s_axi_rst_n,
  input c0_init_calib_complete,
  input sys_rst_n
);

localparam [4:0] TARGET_LAYERS = 5'd1;
localparam [4:0] LAST_LAYER = 5'd0;
localparam [4:0] TARGET_TOKENS = 5'd16;
localparam [10:0] KERNEL_TRANSFER_BEATS = 11'd1792;
localparam [9:0] ACTIVATION_AXI_BEATS = 10'd896;
localparam [9:0] ACTIVATION_AXI_BEATS_PER_TOKEN = ACTIVATION_AXI_BEATS / TARGET_TOKENS;
localparam [10:0] KERNEL_TRANSFER_BEATS_PER_TOKEN = KERNEL_TRANSFER_BEATS / TARGET_TOKENS;
localparam [22:0] WEIGHT_WORDS = 23'd7457664;
localparam [19:0] WEIGHT_AXI_BEATS = 20'd466104;
localparam [10:0] RUNTIME_WORDS = 11'd1056;
localparam [6:0] RUNTIME_AXI_BEATS = 7'd66;
localparam [36:0] INPUT_TOKENS_BASE = 37'd0;
localparam [36:0] OUTPUT_TOKENS_BASE = 37'd57344;
localparam [36:0] ACTIVATION_PING_BASE = 37'd114688;
localparam [36:0] ACTIVATION_PONG_BASE = 37'd270336;
localparam [36:0] WEIGHT_BANK_A_BASE = 37'd425984;
localparam [36:0] WEIGHT_BANK_B_BASE = 37'd30256640;
localparam [36:0] RUNTIME_CONSTANTS_BASE = 37'd60087296;
localparam [36:0] FULL_WEIGHT_IMAGE_BASE = RUNTIME_CONSTANTS_BASE + (RUNTIME_AXI_BEATS * 37'd64);
localparam [36:0] WEIGHT_LAYER_BYTES = 37'd29830656;

localparam [7:0] S_IDLE = 8'd0;
localparam [7:0] S_COPY_AR = 8'd1;
localparam [7:0] S_COPY_R = 8'd2;
localparam [7:0] S_COPY_AW = 8'd3;
localparam [7:0] S_COPY_B = 8'd4;
localparam [7:0] S_INITIAL_PREFETCH_SETUP = 8'd5;
localparam [7:0] S_KERNEL_RESET = 8'd6;
localparam [7:0] S_WEIGHT_SETUP = 8'd7;
localparam [7:0] S_WEIGHT_AR = 8'd8;
localparam [7:0] S_WEIGHT_R = 8'd9;
localparam [7:0] S_WEIGHT_WORD = 8'd10;
localparam [7:0] S_RUNTIME_SETUP = 8'd11;
localparam [7:0] S_RUNTIME_AR = 8'd12;
localparam [7:0] S_RUNTIME_R = 8'd13;
localparam [7:0] S_RUNTIME_WORD = 8'd14;
localparam [7:0] S_KERNEL_START = 8'd15;
localparam [7:0] S_COMPUTE_ARM = 8'd29;
localparam [7:0] S_COMPUTE_RUN = 8'd30;
localparam [7:0] S_COMPUTE_INPUT_AR = 8'd31;
localparam [7:0] S_COMPUTE_INPUT_R = 8'd32;
localparam [7:0] S_COMPUTE_INPUT_LO = 8'd33;
localparam [7:0] S_COMPUTE_INPUT_HI = 8'd34;
localparam [7:0] S_COMPUTE_PREF_AR = 8'd35;
localparam [7:0] S_COMPUTE_PREF_R = 8'd36;
localparam [7:0] S_COMPUTE_PREF_AW = 8'd37;
localparam [7:0] S_COMPUTE_PREF_B = 8'd38;
localparam [7:0] S_COMPUTE_OUT_AW = 8'd39;
localparam [7:0] S_COMPUTE_OUT_B = 8'd40;
localparam [7:0] S_LAYER_DONE = 8'd41;
localparam [7:0] S_FINAL_RESET = 8'd50;
localparam [7:0] S_FINAL_COPY_SETUP = 8'd51;
localparam [7:0] S_COMPLETE = 8'd52;

function [36:0] beat_offset;
  input [31:0] beat;
  begin
    beat_offset = beat * 37'd64;
  end
endfunction

function [36:0] weight_image_layer_base;
  input [4:0] layer;
  begin
    weight_image_layer_base = FULL_WEIGHT_IMAGE_BASE + (layer * WEIGHT_LAYER_BYTES);
  end
endfunction

function [36:0] activation_read_base;
  input [4:0] layer;
  begin
    activation_read_base = layer[0] ? ACTIVATION_PONG_BASE : ACTIVATION_PING_BASE;
  end
endfunction

function [36:0] activation_write_base;
  input [4:0] layer;
  begin
    activation_write_base = layer[0] ? ACTIVATION_PING_BASE : ACTIVATION_PONG_BASE;
  end
endfunction

function [36:0] weight_bank_base;
  input [4:0] layer;
  begin
    weight_bank_base = layer[0] ? WEIGHT_BANK_B_BASE : WEIGHT_BANK_A_BASE;
  end
endfunction

function [36:0] inactive_weight_bank_base;
  input [4:0] layer;
  begin
    inactive_weight_bank_base = layer[0] ? WEIGHT_BANK_A_BASE : WEIGHT_BANK_B_BASE;
  end
endfunction

function [31:0] select_word;
  input [511:0] data;
  input [3:0] lane;
  begin
    case (lane)
      4'd0: select_word = data[31:0];
      4'd1: select_word = data[63:32];
      4'd2: select_word = data[95:64];
      4'd3: select_word = data[127:96];
      4'd4: select_word = data[159:128];
      4'd5: select_word = data[191:160];
      4'd6: select_word = data[223:192];
      4'd7: select_word = data[255:224];
      4'd8: select_word = data[287:256];
      4'd9: select_word = data[319:288];
      4'd10: select_word = data[351:320];
      4'd11: select_word = data[383:352];
      4'd12: select_word = data[415:384];
      4'd13: select_word = data[447:416];
      4'd14: select_word = data[479:448];
      default: select_word = data[511:480];
    endcase
  end
endfunction

reg [7:0] state;
reg [703:0] cfg_shadow;
reg cfg_seen;
reg [2:0] batch_count_q;
reg [2:0] result_count_q;
reg busy_q;
reg [4:0] layer_index;
reg [10:0] reset_count;
reg kernel_reset_q;
reg kernel_start_q;
reg kernel_input_valid_q;
reg [255:0] kernel_input_data_q;
wire kernel_input_ready;
wire kernel_output_valid;
wire kernel_output_ready;
wire [255:0] kernel_output_data;
reg weight_valid_q;
wire weight_ready;
reg [31:0] weight_data_q;
reg [22:0] weight_addr_q;
reg weight_last_q;
reg runtime_valid_q;
wire runtime_ready;
reg [31:0] runtime_data_q;
reg [10:0] runtime_addr_q;
reg runtime_last_q;
reg [36:0] axi_awaddr_q;
reg [7:0] axi_awlen_q;
reg axi_awvalid_q;
reg [511:0] axi_wdata_q;
reg [63:0] axi_wstrb_q;
reg axi_wlast_q;
reg axi_wvalid_q;
reg axi_bready_q;
reg [36:0] axi_araddr_q;
reg [7:0] axi_arlen_q;
reg axi_arvalid_q;
reg axi_rready_q;
reg write_aw_done;
reg write_w_done;
reg [511:0] read_data_q;
reg axi_error_q;
reg [36:0] copy_src_base;
reg [36:0] copy_dst_base;
reg [19:0] copy_beats;
reg [19:0] copy_index;
reg [7:0] copy_return_state;
reg copy_updates_prefetch;
reg copy_trace_prefetch;
reg copy_trace_final;
reg [19:0] weight_beat_index;
reg [22:0] weight_word_index;
reg [6:0] runtime_beat_index;
reg [10:0] runtime_word_index;
reg [3:0] word_lane;
reg [19:0] input_axi_index;
reg [19:0] prefetch_index;
reg [19:0] output_write_index;
reg [11:0] output_accept_count;
reg [6:0] output_token_beat_count;
reg kernel_token_rearm_pending;
reg kernel_invocation_launched;
reg [9:0] output_fifo_write_index;
reg [9:0] output_fifo_read_index;
reg [9:0] output_fifo_count;
reg [511:0] output_fifo [0:ACTIVATION_AXI_BEATS-1];
reg output_ingress_half;
reg [255:0] output_ingress_low;
reg [19:0] input_launch_limit;
reg output_pair_valid;
reg [511:0] output_pair_data;
reg [63:0] trace_cycle;
reg trace_weight_prefetch_start;
reg trace_weight_prefetch_complete;
reg trace_weight_bank_switch;
reg trace_activation_bank_switch;
reg trace_runtime_load_start;
reg trace_runtime_load_complete;
reg trace_final_writeback_start;
reg trace_final_writeback_complete;
reg [4:0] trace_current_layer_index;
reg [4:0] trace_prefetch_layer_index;
reg trace_private_kernel_reset;
reg trace_kernel_start;
reg trace_layer_output_complete;

assign cnn0_batch_count = batch_count_q;
assign cnn0_result_count = result_count_q;
assign c0_ddr4_s_axi_awid = 4'h1;
assign c0_ddr4_s_axi_awaddr = axi_awaddr_q;
assign c0_ddr4_s_axi_awlen = axi_awlen_q;
assign c0_ddr4_s_axi_awsize = 3'b110;
assign c0_ddr4_s_axi_awburst = 2'b01;
assign c0_ddr4_s_axi_awlock = 1'b0;
assign c0_ddr4_s_axi_awcache = 4'b0011;
assign c0_ddr4_s_axi_awprot = 3'b000;
assign c0_ddr4_s_axi_awvalid = axi_awvalid_q;
assign c0_ddr4_s_axi_wdata = axi_wdata_q;
assign c0_ddr4_s_axi_wstrb = axi_wstrb_q;
assign c0_ddr4_s_axi_wlast = axi_wlast_q;
assign c0_ddr4_s_axi_wvalid = axi_wvalid_q;
assign c0_ddr4_s_axi_bready = axi_bready_q;
assign c0_ddr4_s_axi_arid = 4'h0;
assign c0_ddr4_s_axi_araddr = axi_araddr_q;
assign c0_ddr4_s_axi_arlen = axi_arlen_q;
assign c0_ddr4_s_axi_arsize = 3'b110;
assign c0_ddr4_s_axi_arburst = 2'b01;
assign c0_ddr4_s_axi_arlock = 1'b0;
assign c0_ddr4_s_axi_arcache = 4'b0011;
assign c0_ddr4_s_axi_arprot = 3'b000;
assign c0_ddr4_s_axi_arvalid = axi_arvalid_q;
assign c0_ddr4_s_axi_rready = axi_rready_q;

wire global_reset = (~c0_ddr4_s_axi_rst_n) | (~sys_rst_n) | user_rst;
wire start_condition = c0_init_calib_complete & cfg_seen & cfg_done & cnn0_input_batch_set & (state == S_IDLE);
wire in_compute = (state >= S_COMPUTE_RUN) & (state <= S_LAYER_DONE);
assign kernel_output_ready = in_compute &
                             (output_accept_count < {1'b0,KERNEL_TRANSFER_BEATS}) &
                             (output_fifo_count < ACTIVATION_AXI_BEATS);
wire kernel_output_fire = kernel_output_valid & kernel_output_ready;
wire kernel_output_token_terminal_fire =
    kernel_output_fire &&
    (output_token_beat_count == (KERNEL_TRANSFER_BEATS_PER_TOKEN - 11'd1)) &&
    (output_accept_count != ({1'b0, KERNEL_TRANSFER_BEATS} - 12'd1));
wire kernel_start_to_core = kernel_start_q;

SingleLayerSemanticHarness spatialacc_single_kernel(
  .clock(c0_ddr4_s_axi_clk),
  .reset(kernel_reset_q),
  .start(kernel_start_to_core),
  .input_0_valid(kernel_input_valid_q),
  .input_0_ready(kernel_input_ready),
  .input_0_data(kernel_input_data_q),
  .output_valid(kernel_output_valid),
  .output_ready(kernel_output_ready),
  .output_data(kernel_output_data),
  .weight_valid(weight_valid_q),
  .weight_ready(weight_ready),
  .weight_data(weight_data_q),
  .weight_addr(weight_addr_q),
  .weight_last(weight_last_q),
  .runtime_valid(runtime_valid_q),
  .runtime_ready(runtime_ready),
  .runtime_data(runtime_data_q),
  .runtime_addr(runtime_addr_q),
  .runtime_last(runtime_last_q)
);

always @(posedge c0_ddr4_s_axi_clk) begin
  if (global_reset) begin
    state <= S_IDLE;
    cfg_shadow <= 704'd0;
    cfg_seen <= 1'b0;
    batch_count_q <= 3'd0;
    result_count_q <= 3'd0;
    busy_q <= 1'b0;
    layer_index <= 5'd0;
    reset_count <= 11'd0;
    kernel_reset_q <= 1'b1;
    kernel_start_q <= 1'b0;
    kernel_invocation_launched <= 1'b0;
    kernel_input_valid_q <= 1'b0;
    kernel_input_data_q <= 256'd0;
    weight_valid_q <= 1'b0;
    weight_data_q <= 32'd0;
    weight_addr_q <= 23'd0;
    weight_last_q <= 1'b0;
    runtime_valid_q <= 1'b0;
    runtime_data_q <= 32'd0;
    runtime_addr_q <= 11'd0;
    runtime_last_q <= 1'b0;
    axi_awaddr_q <= 37'd0;
    axi_awlen_q <= 8'd0;
    axi_awvalid_q <= 1'b0;
    axi_wdata_q <= 512'd0;
    axi_wstrb_q <= 64'd0;
    axi_wlast_q <= 1'b0;
    axi_wvalid_q <= 1'b0;
    axi_bready_q <= 1'b0;
    axi_araddr_q <= 37'd0;
    axi_arlen_q <= 8'd0;
    axi_arvalid_q <= 1'b0;
    axi_rready_q <= 1'b0;
    write_aw_done <= 1'b0;
    write_w_done <= 1'b0;
    read_data_q <= 512'd0;
    axi_error_q <= 1'b0;
    copy_src_base <= 37'd0;
    copy_dst_base <= 37'd0;
    copy_beats <= 20'd0;
    copy_index <= 20'd0;
    copy_return_state <= S_IDLE;
    copy_updates_prefetch <= 1'b0;
    copy_trace_prefetch <= 1'b0;
    copy_trace_final <= 1'b0;
    weight_beat_index <= 20'd0;
    weight_word_index <= 23'd0;
    runtime_beat_index <= 7'd0;
    runtime_word_index <= 11'd0;
    word_lane <= 4'd0;
    input_axi_index <= 20'd0;
    prefetch_index <= 20'd0;
    output_write_index <= 20'd0;
    output_accept_count <= 12'd0;
    output_token_beat_count <= 7'd0;
    kernel_token_rearm_pending <= 1'b0;
    output_fifo_write_index <= 10'd0;
    output_fifo_read_index <= 10'd0;
    output_fifo_count <= 10'd0;
    output_ingress_half <= 1'b0;
    output_ingress_low <= 256'd0;
    input_launch_limit <= 20'd0;
    output_pair_valid <= 1'b0;
    output_pair_data <= 512'd0;
    trace_cycle <= 64'd0;
    trace_weight_prefetch_start <= 1'b0;
    trace_weight_prefetch_complete <= 1'b0;
    trace_weight_bank_switch <= 1'b0;
    trace_activation_bank_switch <= 1'b0;
    trace_runtime_load_start <= 1'b0;
    trace_runtime_load_complete <= 1'b0;
    trace_final_writeback_start <= 1'b0;
    trace_final_writeback_complete <= 1'b0;
    trace_current_layer_index <= 5'd0;
    trace_prefetch_layer_index <= 5'd0;
    trace_private_kernel_reset <= 1'b1;
    trace_kernel_start <= 1'b0;
    trace_layer_output_complete <= 1'b0;
  end else begin
    trace_cycle <= trace_cycle + 64'd1;
    trace_weight_prefetch_start <= 1'b0;
    trace_weight_prefetch_complete <= 1'b0;
    trace_weight_bank_switch <= 1'b0;
    trace_activation_bank_switch <= 1'b0;
    trace_runtime_load_start <= 1'b0;
    trace_runtime_load_complete <= 1'b0;
    trace_final_writeback_start <= 1'b0;
    trace_final_writeback_complete <= 1'b0;
    trace_private_kernel_reset <= 1'b0;
    trace_kernel_start <= 1'b0;
    trace_layer_output_complete <= 1'b0;
    kernel_start_q <= 1'b0;
    if (cfg_data_valid) begin
      cfg_shadow <= cfg_data;
      cfg_seen <= 1'b1;
    end
    if (cnn0_result_batch_clear && (result_count_q != 3'd0)) begin
      result_count_q <= result_count_q - 3'd1;
    end
    kernel_token_rearm_pending <= 1'b0;
    if (kernel_output_token_terminal_fire) begin
      kernel_token_rearm_pending <= 1'b1;
      if (input_launch_limit < {10'd0, ACTIVATION_AXI_BEATS}) begin
        input_launch_limit <= input_launch_limit +
                              {10'd0, ACTIVATION_AXI_BEATS_PER_TOKEN};
      end
    end
    if (kernel_output_fire) begin
      output_accept_count <= output_accept_count + 12'd1;
      if (output_token_beat_count == (KERNEL_TRANSFER_BEATS_PER_TOKEN - 11'd1)) begin
        output_token_beat_count <= 7'd0;
      end else begin
        output_token_beat_count <= output_token_beat_count + 7'd1;
      end
      if (!output_ingress_half) begin
        output_ingress_low <= kernel_output_data;
        output_ingress_half <= 1'b1;
      end else begin
        output_fifo[output_fifo_write_index] <= {kernel_output_data, output_ingress_low};
        output_fifo_write_index <= output_fifo_write_index + 10'd1;
        output_fifo_count <= output_fifo_count + 10'd1;
        output_ingress_half <= 1'b0;
      end
    end
    case (state)
      S_IDLE: begin
        kernel_reset_q <= 1'b1;
        kernel_input_valid_q <= 1'b0;
        weight_valid_q <= 1'b0;
        runtime_valid_q <= 1'b0;
        axi_awvalid_q <= 1'b0;
        axi_wvalid_q <= 1'b0;
        axi_bready_q <= 1'b0;
        axi_arvalid_q <= 1'b0;
        axi_rready_q <= 1'b0;
        if (start_condition) begin
          busy_q <= 1'b1;
          if (batch_count_q != 3'd7) begin
            batch_count_q <= batch_count_q + 3'd1;
          end
          layer_index <= 5'd0;
          copy_src_base <= INPUT_TOKENS_BASE;
          copy_dst_base <= ACTIVATION_PING_BASE;
          copy_beats <= {10'd0, ACTIVATION_AXI_BEATS};
          copy_index <= 20'd0;
          copy_return_state <= S_INITIAL_PREFETCH_SETUP;
          copy_updates_prefetch <= 1'b0;
          copy_trace_prefetch <= 1'b0;
          copy_trace_final <= 1'b0;
          state <= S_COPY_AR;
        end
      end
      S_COPY_AR: begin
        if (!axi_arvalid_q && !axi_rready_q) begin
          axi_araddr_q <= copy_src_base + beat_offset(copy_index);
          axi_arlen_q <= 8'd0;
          axi_arvalid_q <= 1'b1;
        end else if (axi_arvalid_q && c0_ddr4_s_axi_arready) begin
          axi_arvalid_q <= 1'b0;
          axi_rready_q <= 1'b1;
          state <= S_COPY_R;
        end
      end
      S_COPY_R: begin
        if (axi_rready_q && c0_ddr4_s_axi_rvalid) begin
          read_data_q <= c0_ddr4_s_axi_rdata;
          axi_error_q <= axi_error_q | (c0_ddr4_s_axi_rresp != 2'b00) | (~c0_ddr4_s_axi_rlast);
          axi_rready_q <= 1'b0;
          axi_awaddr_q <= copy_dst_base + beat_offset(copy_index);
          axi_awlen_q <= 8'd0;
          axi_awvalid_q <= 1'b1;
          axi_wdata_q <= c0_ddr4_s_axi_rdata;
          axi_wstrb_q <= 64'hffffffffffffffff;
          axi_wlast_q <= 1'b1;
          axi_wvalid_q <= 1'b1;
          write_aw_done <= 1'b0;
          write_w_done <= 1'b0;
          state <= S_COPY_AW;
        end
      end
      S_COPY_AW: begin
        if (axi_awvalid_q && c0_ddr4_s_axi_awready) begin
          axi_awvalid_q <= 1'b0;
          write_aw_done <= 1'b1;
        end
        if (axi_wvalid_q && c0_ddr4_s_axi_wready) begin
          axi_wvalid_q <= 1'b0;
          write_w_done <= 1'b1;
        end
        if ((write_aw_done || (axi_awvalid_q && c0_ddr4_s_axi_awready)) && (write_w_done || (axi_wvalid_q && c0_ddr4_s_axi_wready))) begin
          axi_bready_q <= 1'b1;
          state <= S_COPY_B;
        end
      end
      S_COPY_B: begin
        if (axi_bready_q && c0_ddr4_s_axi_bvalid) begin
          axi_bready_q <= 1'b0;
          axi_error_q <= axi_error_q | (c0_ddr4_s_axi_bresp != 2'b00);
          if (copy_updates_prefetch) begin
            prefetch_index <= copy_index + 20'd1;
          end
          if ((copy_index + 20'd1) >= copy_beats) begin
            if (copy_trace_prefetch) begin
              trace_weight_prefetch_complete <= 1'b1;
            end
            if (copy_trace_final) begin
              trace_final_writeback_complete <= 1'b1;
            end
            state <= copy_return_state;
          end else begin
            copy_index <= copy_index + 20'd1;
            state <= S_COPY_AR;
          end
        end
      end
      S_INITIAL_PREFETCH_SETUP: begin
        trace_weight_prefetch_start <= 1'b0;
        trace_current_layer_index <= 5'd0;
        trace_prefetch_layer_index <= 5'd0;
        copy_src_base <= weight_image_layer_base(5'd0);
        copy_dst_base <= WEIGHT_BANK_A_BASE;
        copy_beats <= WEIGHT_AXI_BEATS;
        copy_index <= 20'd0;
        copy_return_state <= S_KERNEL_RESET;
        copy_updates_prefetch <= 1'b0;
        copy_trace_prefetch <= 1'b0;
        copy_trace_final <= 1'b0;
        state <= S_COPY_AR;
      end
      S_KERNEL_RESET: begin
        kernel_reset_q <= 1'b1;
        kernel_start_q <= 1'b0;
        output_token_beat_count <= 7'd0;
        kernel_token_rearm_pending <= 1'b0;
        kernel_invocation_launched <= 1'b0;
        trace_private_kernel_reset <= 1'b1;
        kernel_input_valid_q <= 1'b0;
        weight_valid_q <= 1'b0;
        runtime_valid_q <= 1'b0;
        if (reset_count == 11'd7) begin
          reset_count <= 11'd0;
          kernel_reset_q <= 1'b0;
          state <= S_WEIGHT_SETUP;
        end else begin
          reset_count <= reset_count + 11'd1;
        end
      end
      S_WEIGHT_SETUP: begin
        weight_beat_index <= 20'd0;
        weight_word_index <= 23'd0;
        word_lane <= 4'd0;
        weight_valid_q <= 1'b0;
        state <= S_WEIGHT_AR;
      end
      S_WEIGHT_AR: begin
        if (!axi_arvalid_q && !axi_rready_q) begin
          axi_araddr_q <= weight_bank_base(layer_index) + beat_offset(weight_beat_index);
          axi_arlen_q <= 8'd0;
          axi_arvalid_q <= 1'b1;
        end else if (axi_arvalid_q && c0_ddr4_s_axi_arready) begin
          axi_arvalid_q <= 1'b0;
          axi_rready_q <= 1'b1;
          state <= S_WEIGHT_R;
        end
      end
      S_WEIGHT_R: begin
        if (axi_rready_q && c0_ddr4_s_axi_rvalid) begin
          read_data_q <= c0_ddr4_s_axi_rdata;
          axi_error_q <= axi_error_q | (c0_ddr4_s_axi_rresp != 2'b00) | (~c0_ddr4_s_axi_rlast);
          axi_rready_q <= 1'b0;
          word_lane <= 4'd0;
          weight_valid_q <= 1'b0;
          state <= S_WEIGHT_WORD;
        end
      end
      S_WEIGHT_WORD: begin
        if (!weight_valid_q) begin
          weight_valid_q <= 1'b1;
          weight_data_q <= select_word(read_data_q, word_lane);
          weight_addr_q <= weight_word_index;
          weight_last_q <= (weight_word_index == (WEIGHT_WORDS - 23'd1));
        end else if (weight_valid_q && weight_ready) begin
          if (weight_word_index == (WEIGHT_WORDS - 23'd1)) begin
            weight_valid_q <= 1'b0;
            weight_last_q <= 1'b0;
            state <= S_RUNTIME_SETUP;
          end else if (word_lane == 4'd15) begin
            weight_valid_q <= 1'b0;
            weight_word_index <= weight_word_index + 23'd1;
            weight_beat_index <= weight_beat_index + 20'd1;
            word_lane <= 4'd0;
            state <= S_WEIGHT_AR;
          end else begin
            word_lane <= word_lane + 4'd1;
            weight_word_index <= weight_word_index + 23'd1;
            weight_data_q <= select_word(read_data_q, word_lane + 4'd1);
            weight_addr_q <= weight_word_index + 23'd1;
            weight_last_q <= ((weight_word_index + 23'd1) == (WEIGHT_WORDS - 23'd1));
          end
        end
      end
      S_RUNTIME_SETUP: begin
        runtime_beat_index <= 7'd0;
        runtime_word_index <= 11'd0;
        word_lane <= 4'd0;
        runtime_valid_q <= 1'b0;
        trace_runtime_load_start <= 1'b1;
        trace_current_layer_index <= layer_index;
        state <= S_RUNTIME_AR;
      end
      S_RUNTIME_AR: begin
        if (!axi_arvalid_q && !axi_rready_q) begin
          axi_araddr_q <= RUNTIME_CONSTANTS_BASE + beat_offset({25'd0, runtime_beat_index});
          axi_arlen_q <= 8'd0;
          axi_arvalid_q <= 1'b1;
        end else if (axi_arvalid_q && c0_ddr4_s_axi_arready) begin
          axi_arvalid_q <= 1'b0;
          axi_rready_q <= 1'b1;
          state <= S_RUNTIME_R;
        end
      end
      S_RUNTIME_R: begin
        if (axi_rready_q && c0_ddr4_s_axi_rvalid) begin
          read_data_q <= c0_ddr4_s_axi_rdata;
          axi_error_q <= axi_error_q | (c0_ddr4_s_axi_rresp != 2'b00) | (~c0_ddr4_s_axi_rlast);
          axi_rready_q <= 1'b0;
          word_lane <= 4'd0;
          runtime_valid_q <= 1'b0;
          state <= S_RUNTIME_WORD;
        end
      end
      S_RUNTIME_WORD: begin
        if (!runtime_valid_q) begin
          runtime_valid_q <= 1'b1;
          runtime_data_q <= select_word(read_data_q, word_lane);
          runtime_addr_q <= runtime_word_index;
          runtime_last_q <= (runtime_word_index == (RUNTIME_WORDS - 11'd1));
        end else if (runtime_valid_q && runtime_ready) begin
          if (runtime_word_index == (RUNTIME_WORDS - 11'd1)) begin
            runtime_valid_q <= 1'b0;
            runtime_last_q <= 1'b0;
            trace_runtime_load_complete <= 1'b1;
            trace_current_layer_index <= layer_index;
            state <= S_KERNEL_START;
          end else if (word_lane == 4'd15) begin
            runtime_valid_q <= 1'b0;
            runtime_word_index <= runtime_word_index + 11'd1;
            runtime_beat_index <= runtime_beat_index + 7'd1;
            word_lane <= 4'd0;
            state <= S_RUNTIME_AR;
          end else begin
            word_lane <= word_lane + 4'd1;
            runtime_word_index <= runtime_word_index + 11'd1;
            runtime_data_q <= select_word(read_data_q, word_lane + 4'd1);
            runtime_addr_q <= runtime_word_index + 11'd1;
            runtime_last_q <= ((runtime_word_index + 11'd1) == (RUNTIME_WORDS - 11'd1));
          end
        end
      end
      S_KERNEL_START: begin
        kernel_start_q <= 1'b0;
        kernel_invocation_launched <= 1'b0;
        trace_current_layer_index <= layer_index;
        input_axi_index <= 20'd0;
        prefetch_index <= 20'd0;
        output_write_index <= 20'd0;
        output_accept_count <= 12'd0;
        output_token_beat_count <= 7'd0;
        kernel_token_rearm_pending <= 1'b0;
        output_fifo_write_index <= 10'd0;
        output_fifo_read_index <= 10'd0;
        output_fifo_count <= 10'd0;
        output_ingress_half <= 1'b0;
        output_ingress_low <= 256'd0;
        input_launch_limit <= (layer_index == LAST_LAYER) ?
                              {10'd0, ACTIVATION_AXI_BEATS} :
                              {10'd0, ACTIVATION_AXI_BEATS_PER_TOKEN};
        output_pair_valid <= 1'b0;
        kernel_input_valid_q <= 1'b0;
        state <= S_COMPUTE_RUN;
      end
      S_COMPUTE_RUN: begin
        if (output_pair_valid) begin
          axi_awaddr_q <= activation_write_base(layer_index) + beat_offset(output_write_index);
          axi_awlen_q <= 8'd0;
          axi_awvalid_q <= 1'b1;
          axi_wdata_q <= output_pair_data;
          axi_wstrb_q <= 64'hffffffffffffffff;
          axi_wlast_q <= 1'b1;
          axi_wvalid_q <= 1'b1;
          write_aw_done <= 1'b0;
          write_w_done <= 1'b0;
          output_pair_valid <= 1'b0;
          state <= S_COMPUTE_OUT_AW;
        end else if ((output_fifo_count != 10'd0) &&
                     !(kernel_output_fire && output_ingress_half)) begin
          output_pair_data <= output_fifo[output_fifo_read_index];
          output_pair_valid <= 1'b1;
          output_fifo_read_index <= output_fifo_read_index + 10'd1;
          output_fifo_count <= output_fifo_count - 10'd1;
        end else if ((input_axi_index < {10'd0, ACTIVATION_AXI_BEATS}) &&
                     (input_axi_index < input_launch_limit)) begin
          axi_araddr_q <= activation_read_base(layer_index) + beat_offset(input_axi_index);
          axi_arlen_q <= 8'd0;
          axi_arvalid_q <= 1'b1;
          state <= S_COMPUTE_INPUT_AR;
        end else if ((layer_index != LAST_LAYER) && (prefetch_index < WEIGHT_AXI_BEATS)) begin
          if (prefetch_index == 20'd0) begin
            trace_weight_prefetch_start <= 1'b1;
            trace_current_layer_index <= layer_index;
            trace_prefetch_layer_index <= layer_index + 5'd1;
          end
          axi_araddr_q <= weight_image_layer_base(layer_index + 5'd1) + beat_offset(prefetch_index);
          axi_arlen_q <= 8'd0;
          axi_arvalid_q <= 1'b1;
          state <= S_COMPUTE_PREF_AR;
        end else if ((output_accept_count == {1'b0, KERNEL_TRANSFER_BEATS}) &&
                     (output_write_index == {10'd0, ACTIVATION_AXI_BEATS}) &&
                     (output_fifo_count == 10'd0) &&
                     !output_ingress_half && !output_pair_valid) begin
          trace_layer_output_complete <= 1'b1;
          trace_current_layer_index <= layer_index;
          state <= S_LAYER_DONE;
        end
      end
      S_COMPUTE_INPUT_AR: begin
        if (axi_arvalid_q && c0_ddr4_s_axi_arready) begin
          axi_arvalid_q <= 1'b0;
          axi_rready_q <= 1'b1;
          state <= S_COMPUTE_INPUT_R;
        end
      end
      S_COMPUTE_INPUT_R: begin
        if (axi_rready_q && c0_ddr4_s_axi_rvalid) begin
          read_data_q <= c0_ddr4_s_axi_rdata;
          axi_error_q <= axi_error_q | (c0_ddr4_s_axi_rresp != 2'b00) | (~c0_ddr4_s_axi_rlast);
          axi_rready_q <= 1'b0;
          kernel_input_valid_q <= 1'b1;
          kernel_input_data_q <= c0_ddr4_s_axi_rdata[255:0];
          state <= S_COMPUTE_INPUT_LO;
        end
      end
      S_COMPUTE_INPUT_LO: begin
        if (kernel_input_valid_q && kernel_input_ready) begin
          if ((input_axi_index == 20'd0) && !kernel_invocation_launched) begin
            kernel_input_valid_q <= 1'b0;
            state <= S_COMPUTE_ARM;
          end else begin
            kernel_input_data_q <= read_data_q[511:256];
            state <= S_COMPUTE_INPUT_HI;
          end
        end
      end
      S_COMPUTE_ARM: begin
        kernel_start_q <= 1'b1;
        kernel_invocation_launched <= 1'b1;
        trace_kernel_start <= 1'b1;
        trace_current_layer_index <= layer_index;
        kernel_input_valid_q <= 1'b0;
        kernel_input_data_q <= read_data_q[511:256];
        state <= S_COMPUTE_INPUT_HI;
      end
      S_COMPUTE_INPUT_HI: begin
        if (!kernel_input_valid_q) begin
          kernel_input_valid_q <= 1'b1;
          kernel_input_data_q <= read_data_q[511:256];
        end else if (kernel_input_valid_q && kernel_input_ready) begin
          kernel_input_valid_q <= 1'b0;
          input_axi_index <= input_axi_index + 20'd1;
          state <= S_COMPUTE_RUN;
        end
      end
      S_COMPUTE_PREF_AR: begin
        if (axi_arvalid_q && c0_ddr4_s_axi_arready) begin
          axi_arvalid_q <= 1'b0;
          axi_rready_q <= 1'b1;
          state <= S_COMPUTE_PREF_R;
        end
      end
      S_COMPUTE_PREF_R: begin
        if (axi_rready_q && c0_ddr4_s_axi_rvalid) begin
          read_data_q <= c0_ddr4_s_axi_rdata;
          axi_error_q <= axi_error_q | (c0_ddr4_s_axi_rresp != 2'b00) | (~c0_ddr4_s_axi_rlast);
          axi_rready_q <= 1'b0;
          axi_awaddr_q <= inactive_weight_bank_base(layer_index) + beat_offset(prefetch_index);
          axi_awlen_q <= 8'd0;
          axi_awvalid_q <= 1'b1;
          axi_wdata_q <= c0_ddr4_s_axi_rdata;
          axi_wstrb_q <= 64'hffffffffffffffff;
          axi_wlast_q <= 1'b1;
          axi_wvalid_q <= 1'b1;
          write_aw_done <= 1'b0;
          write_w_done <= 1'b0;
          state <= S_COMPUTE_PREF_AW;
        end
      end
      S_COMPUTE_PREF_AW: begin
        if (axi_awvalid_q && c0_ddr4_s_axi_awready) begin
          axi_awvalid_q <= 1'b0;
          write_aw_done <= 1'b1;
        end
        if (axi_wvalid_q && c0_ddr4_s_axi_wready) begin
          axi_wvalid_q <= 1'b0;
          write_w_done <= 1'b1;
        end
        if ((write_aw_done || (axi_awvalid_q && c0_ddr4_s_axi_awready)) && (write_w_done || (axi_wvalid_q && c0_ddr4_s_axi_wready))) begin
          axi_bready_q <= 1'b1;
          state <= S_COMPUTE_PREF_B;
        end
      end
      S_COMPUTE_PREF_B: begin
        if (axi_bready_q && c0_ddr4_s_axi_bvalid) begin
          axi_bready_q <= 1'b0;
          axi_error_q <= axi_error_q | (c0_ddr4_s_axi_bresp != 2'b00);
          prefetch_index <= prefetch_index + 20'd1;
          if ((prefetch_index + 20'd1) == WEIGHT_AXI_BEATS) begin
            trace_weight_prefetch_complete <= 1'b1;
            trace_current_layer_index <= layer_index;
            trace_prefetch_layer_index <= layer_index + 5'd1;
            input_launch_limit <= {10'd0, ACTIVATION_AXI_BEATS};
          end
          state <= S_COMPUTE_RUN;
        end
      end
      S_COMPUTE_OUT_AW: begin
        if (axi_awvalid_q && c0_ddr4_s_axi_awready) begin
          axi_awvalid_q <= 1'b0;
          write_aw_done <= 1'b1;
        end
        if (axi_wvalid_q && c0_ddr4_s_axi_wready) begin
          axi_wvalid_q <= 1'b0;
          write_w_done <= 1'b1;
        end
        if ((write_aw_done || (axi_awvalid_q && c0_ddr4_s_axi_awready)) && (write_w_done || (axi_wvalid_q && c0_ddr4_s_axi_wready))) begin
          axi_bready_q <= 1'b1;
          state <= S_COMPUTE_OUT_B;
        end
      end
      S_COMPUTE_OUT_B: begin
        if (axi_bready_q && c0_ddr4_s_axi_bvalid) begin
          axi_bready_q <= 1'b0;
          axi_error_q <= axi_error_q | (c0_ddr4_s_axi_bresp != 2'b00);
          output_write_index <= output_write_index + 20'd1;
          state <= S_COMPUTE_RUN;
        end
      end
      S_LAYER_DONE: begin
        if (layer_index == LAST_LAYER) begin
          kernel_reset_q <= 1'b1;
          reset_count <= 11'd0;
          state <= S_FINAL_RESET;
        end else if (prefetch_index == WEIGHT_AXI_BEATS) begin
          trace_weight_bank_switch <= 1'b1;
          trace_activation_bank_switch <= 1'b1;
          trace_current_layer_index <= layer_index;
          layer_index <= layer_index + 5'd1;
          kernel_reset_q <= 1'b1;
          reset_count <= 11'd0;
          state <= S_KERNEL_RESET;
        end
      end
      S_FINAL_RESET: begin
        kernel_reset_q <= 1'b1;
        trace_private_kernel_reset <= 1'b1;
        if (reset_count == 11'd7) begin
          reset_count <= 11'd0;
          state <= S_FINAL_COPY_SETUP;
        end else begin
          reset_count <= reset_count + 11'd1;
        end
      end
      S_FINAL_COPY_SETUP: begin
        trace_final_writeback_start <= 1'b1;
        trace_current_layer_index <= LAST_LAYER;
        copy_src_base <= activation_write_base(LAST_LAYER);
        copy_dst_base <= OUTPUT_TOKENS_BASE;
        copy_beats <= {10'd0, ACTIVATION_AXI_BEATS};
        copy_index <= 20'd0;
        copy_return_state <= S_COMPLETE;
        copy_updates_prefetch <= 1'b0;
        copy_trace_prefetch <= 1'b0;
        copy_trace_final <= 1'b1;
        state <= S_COPY_AR;
      end
      S_COMPLETE: begin
        busy_q <= 1'b0;
        kernel_reset_q <= 1'b1;
        if (batch_count_q != 3'd0) begin
          batch_count_q <= batch_count_q - 3'd1;
        end
        if (result_count_q != 3'd7) begin
          result_count_q <= result_count_q + 3'd1;
        end
        state <= S_IDLE;
      end
      default: begin
        state <= S_IDLE;
        kernel_reset_q <= 1'b1;
      end
    endcase
  end
end

endmodule
