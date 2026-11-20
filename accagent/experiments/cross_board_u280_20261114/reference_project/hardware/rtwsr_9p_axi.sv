`timescale 1ns / 1ps

module rtwsr_9p_axi #(
    parameter int S_AXI_DATA_WIDTH = 32,
    parameter int S_AXI_ADDR_WIDTH = 12,
    parameter int P_CH = 32,
    parameter int C_OUT_PER_SLR = 1760,
    parameter int K = 17920,
    parameter int ROUNDS = 32,
    parameter int SLR_COUNT = 3,
    parameter int CHANNEL_WIDTH = $clog2(C_OUT_PER_SLR),
    parameter int WINDOW_COUNT = (K + 255) / 256,
    parameter int TILE_COUNT = (C_OUT_PER_SLR + P_CH - 1) / P_CH,
    parameter int WINDOW_WIDTH = $clog2(WINDOW_COUNT),
    parameter int TILE_WIDTH = $clog2(TILE_COUNT),
    parameter int ROUND_WIDTH = $clog2(ROUNDS)
)(
    input  logic                              s_axi_aclk,
    input  logic                              s_axi_aresetn,
    input  logic [S_AXI_ADDR_WIDTH-1:0]       s_axi_awaddr,
    input  logic [2:0]                        s_axi_awprot,
    input  logic                              s_axi_awvalid,
    output logic                              s_axi_awready,
    input  logic [S_AXI_DATA_WIDTH-1:0]       s_axi_wdata,
    input  logic [S_AXI_DATA_WIDTH/8-1:0]      s_axi_wstrb,
    input  logic                              s_axi_wvalid,
    output logic                              s_axi_wready,
    output logic [1:0]                        s_axi_bresp,
    output logic                              s_axi_bvalid,
    input  logic                              s_axi_bready,
    input  logic [S_AXI_ADDR_WIDTH-1:0]       s_axi_araddr,
    input  logic [2:0]                        s_axi_arprot,
    input  logic                              s_axi_arvalid,
    output logic                              s_axi_arready,
    output logic [S_AXI_DATA_WIDTH-1:0]       s_axi_rdata,
    output logic [1:0]                        s_axi_rresp,
    output logic                              s_axi_rvalid,
    input  logic                              s_axi_rready,
    output logic [36:0]                       m_axi_araddr,
    output logic [4:0]                        m_axi_arid,
    output logic [7:0]                        m_axi_arlen,
    output logic [2:0]                        m_axi_arsize,
    output logic [1:0]                        m_axi_arburst,
    output logic                              m_axi_arvalid,
    input  logic                              m_axi_arready,
    input  logic [4:0]                        m_axi_rid,
    input  logic [511:0]                      m_axi_rdata,
    input  logic [1:0]                        m_axi_rresp,
    input  logic                              m_axi_rlast,
    input  logic                              m_axi_rvalid,
    output logic                              m_axi_rready
);
    localparam logic [9:0] WEIGHT_DATA_BASE = 10'h010;
    localparam logic [9:0] ACTIVATION_BASE = 10'h040;
    localparam logic [9:0] GAMMA_BASE = 10'h080;
    localparam logic [9:0] RESULT_BASE = 10'h100;
    localparam logic [9:0] DMA_STATUS = 10'h00a;
    localparam int OPERATOR_WORDS = SLR_COUNT * C_OUT_PER_SLR * WINDOW_COUNT;
    localparam int RESULT_WORDS = SLR_COUNT * P_CH;
    localparam int RESULT_INDEX_WIDTH = (RESULT_WORDS <= 1) ? 1 : $clog2(RESULT_WORDS);
    localparam logic [9:0] RESULT_LIMIT = 10'(RESULT_BASE + RESULT_WORDS);

    logic [S_AXI_ADDR_WIDTH-1:0] awaddr_q;
    logic [S_AXI_DATA_WIDTH-1:0] wdata_q;
    logic [S_AXI_DATA_WIDTH/8-1:0] wstrb_q;
    logic aw_pending;
    logic w_pending;
    logic [S_AXI_ADDR_WIDTH-1:0] araddr_q;

    logic [12:0] weight_route_q;
    logic [WINDOW_WIDTH-1:0] weight_window_q;
    logic [15:0] activation_scale_q;
    logic [511:0] weight_data_q;
    logic [256*8-1:0] activation_window_q;
    logic [SLR_COUNT*P_CH*16-1:0] round_gamma_q;
    logic [36:0] dma_address_q;
    logic [31:0] dma_words_q;
    logic operator_valid;
    logic dma_command_valid;
    logic dma_command_ready;
    logic dma_stream_valid;
    logic dma_stream_ready;
    logic [511:0] dma_stream_data;
    logic dma_stream_last;
    logic dma_busy;
    logic dma_done;
    logic dma_done_latched;
    logic dma_error;
    logic stream_store_start;
    logic stream_store_abort;
    logic stream_store_busy;
    logic stream_store_done;
    logic stream_store_error;
    logic [16:0] stream_store_occupancy;
    logic [SLR_COUNT-1:0] stream_pool_valid;
    logic [SLR_COUNT-1:0] stream_pool_ready;
    logic [SLR_COUNT*CHANNEL_WIDTH-1:0] stream_pool_channel;
    logic [SLR_COUNT*WINDOW_WIDTH-1:0] stream_pool_window;
    logic [SLR_COUNT*512-1:0] stream_pool_data;
    logic [SLR_COUNT*CHANNEL_WIDTH-1:0] weight_load_channel;
    logic [SLR_COUNT*WINDOW_WIDTH-1:0] weight_load_window;
    logic [SLR_COUNT*512-1:0] weight_load_data;
    logic weight_pending;
    logic round_pending;
    logic activation_pending;
    logic [2:0] error_q;

    logic [SLR_COUNT-1:0] weight_load_valid;
    logic [SLR_COUNT-1:0] weight_load_ready;
    logic [SLR_COUNT-1:0] round_config_valid;
    logic [SLR_COUNT-1:0] round_config_ready;
    logic [SLR_COUNT-1:0] activation_valid;
    logic [SLR_COUNT-1:0] activation_ready;
    logic [SLR_COUNT-1:0] tile_result_valid;
    logic [SLR_COUNT*TILE_WIDTH-1:0] output_tile_index;
    logic [SLR_COUNT*P_CH*32-1:0] tile_result_q12;
    logic [SLR_COUNT-1:0] round_result_valid;
    logic [SLR_COUNT*ROUND_WIDTH-1:0] round_index;
    logic [SLR_COUNT-1:0] core_done;
    logic [SLR_COUNT-1:0] tile_result_seen;
    logic [TILE_WIDTH-1:0] result_tile_q;
    logic [ROUND_WIDTH-1:0] result_round_q;
    logic [31:0] result_words [0:RESULT_WORDS-1];
    logic run_active;
    logic [63:0] run_cycles;
    logic [63:0] run_cycles_latched;

    logic [S_AXI_ADDR_WIDTH-1:0] write_addr;
    logic [S_AXI_DATA_WIDTH-1:0] write_data;
    logic [S_AXI_DATA_WIDTH/8-1:0] write_strb;
    logic have_aw;
    logic have_w;
    logic write_commit;
    logic [9:0] write_index;
    logic [9:0] read_index;
    logic [S_AXI_DATA_WIDTH-1:0] read_value;
    logic [S_AXI_DATA_WIDTH-1:0] merged_value;
    logic all_round_ready;
    logic all_activation_ready;
    logic all_done;
    logic [31:0] status_word;

    function automatic logic [S_AXI_DATA_WIDTH-1:0] merge_wstrb(
        input logic [S_AXI_DATA_WIDTH-1:0] previous,
        input logic [S_AXI_DATA_WIDTH-1:0] incoming,
        input logic [S_AXI_DATA_WIDTH/8-1:0] strobes
    );
        logic [S_AXI_DATA_WIDTH-1:0] result;
        begin
            result = previous;
            for (integer byte_index = 0; byte_index < S_AXI_DATA_WIDTH/8; byte_index++)
                if (strobes[byte_index])
                    result[byte_index*8 +: 8] = incoming[byte_index*8 +: 8];
            return result;
        end
    endfunction

    always_comb begin
        s_axi_awready = !aw_pending && !s_axi_bvalid;
        s_axi_wready = !w_pending && !s_axi_bvalid;
        s_axi_arready = !s_axi_rvalid;
        write_addr = aw_pending ? awaddr_q : s_axi_awaddr;
        write_data = w_pending ? wdata_q : s_axi_wdata;
        write_strb = w_pending ? wstrb_q : s_axi_wstrb;
        have_aw = aw_pending || (s_axi_awvalid && s_axi_awready);
        have_w = w_pending || (s_axi_wvalid && s_axi_wready);
        write_commit = !s_axi_bvalid && have_aw && have_w;
        write_index = write_addr[11:2];
        read_index = s_axi_rvalid ? araddr_q[11:2] : s_axi_araddr[11:2];

        all_round_ready = &round_config_ready;
        all_activation_ready = &activation_ready;
        all_done = &core_done;
        dma_command_valid = write_commit && write_index == DMA_STATUS &&
                            write_strb[0] && write_data[0] &&
                            dma_words_q == OPERATOR_WORDS && dma_command_ready &&
                            !dma_busy && !stream_store_busy && !weight_pending &&
                            !dma_done && (dma_address_q[5:0] == '0);
        stream_store_start = dma_command_valid && dma_command_ready;
        stream_store_abort = (dma_done && dma_error) || stream_store_error;
        weight_load_valid = stream_pool_valid;
        stream_pool_ready = weight_load_ready & {SLR_COUNT{!weight_pending}};
        weight_load_channel = stream_pool_channel;
        weight_load_window = stream_pool_window;
        weight_load_data = stream_pool_data;
        if (weight_pending && int'(weight_route_q[12:11]) < SLR_COUNT) begin
            weight_load_valid = '0;
            weight_load_valid[weight_route_q[12:11]] = 1'b1;
            weight_load_channel[weight_route_q[12:11]*CHANNEL_WIDTH +: CHANNEL_WIDTH] =
                weight_route_q[CHANNEL_WIDTH-1:0];
            weight_load_window[weight_route_q[12:11]*WINDOW_WIDTH +: WINDOW_WIDTH] =
                weight_window_q;
            weight_load_data[weight_route_q[12:11]*512 +: 512] = weight_data_q;
        end
        round_config_valid = {SLR_COUNT{round_pending && all_round_ready &&
            (run_active || (operator_valid && !stream_store_busy && !dma_busy))}};
        activation_valid = {SLR_COUNT{activation_pending}};

        status_word = '0;
        status_word[2:0] = tile_result_seen;
        status_word[5:3] = core_done;
        status_word[8] = run_active;
        status_word[9] = weight_pending;
        status_word[10] = round_pending;
        status_word[11] = activation_pending;
        status_word[14:12] = error_q;
        status_word[15] = dma_busy;
        status_word[16] = dma_done_latched;
        status_word[17] = dma_error || stream_store_error;
        status_word[18] = operator_valid;
        status_word[19] = stream_store_busy;

        read_value = '0;
        if (read_index == 10'h001)
            read_value = status_word;
        else if (read_index == 10'h002) begin
            read_value = '0;
            read_value[TILE_WIDTH-1:0] = result_tile_q;
        end else if (read_index == 10'h003) begin
            read_value = '0;
            read_value[ROUND_WIDTH-1:0] = result_round_q;
        end
        else if (read_index == 10'h004)
            read_value = run_cycles_latched[31:0];
        else if (read_index == 10'h005)
            read_value = run_cycles_latched[63:32];
        else if (read_index >= RESULT_BASE && read_index < RESULT_LIMIT)
            read_value = result_words[RESULT_INDEX_WIDTH'(read_index - RESULT_BASE)];
        else if (read_index == 10'h006)
            read_value = {29'd0, error_q};
        else if (read_index == 10'h007)
            read_value = dma_address_q[31:0];
        else if (read_index == 10'h008)
            read_value = {27'd0, dma_address_q[36:32]};
        else if (read_index == 10'h009)
            read_value = dma_words_q;
        else if (read_index == DMA_STATUS)
            read_value = {29'd0, dma_error, dma_done_latched, dma_busy};

        merged_value = '0;
        if (write_index == 10'h002)
            merged_value = merge_wstrb({19'd0, weight_route_q}, write_data, write_strb);
        else if (write_index == 10'h003)
            merged_value = merge_wstrb(
                {{(S_AXI_DATA_WIDTH-WINDOW_WIDTH){1'b0}}, weight_window_q}, write_data, write_strb
            );
        else if (write_index == 10'h004)
            merged_value = merge_wstrb('0, write_data, write_strb);
        else if (write_index == 10'h005)
            merged_value = merge_wstrb({16'd0, activation_scale_q}, write_data, write_strb);
        else if (write_index == 10'h007)
            merged_value = merge_wstrb(dma_address_q[31:0], write_data, write_strb);
        else if (write_index == 10'h008)
            merged_value = merge_wstrb({27'd0, dma_address_q[36:32]}, write_data, write_strb);
        else if (write_index == 10'h009)
            merged_value = merge_wstrb(dma_words_q, write_data, write_strb);
        else if (write_index >= WEIGHT_DATA_BASE &&
                 write_index < WEIGHT_DATA_BASE + 16)
            merged_value = merge_wstrb(
                weight_data_q[(write_index-WEIGHT_DATA_BASE)*32 +: 32], write_data, write_strb
            );
        else if (write_index >= ACTIVATION_BASE &&
                 write_index < ACTIVATION_BASE + 64)
            merged_value = merge_wstrb(
                activation_window_q[(write_index-ACTIVATION_BASE)*32 +: 32], write_data, write_strb
            );
        else if (write_index >= GAMMA_BASE && write_index < GAMMA_BASE + 48)
            merged_value = merge_wstrb(
                round_gamma_q[(write_index-GAMMA_BASE)*32 +: 32], write_data, write_strb
            );
    end

    rtwsr_streaming_weight_store #(
        .P_CH(P_CH),
        .C_OUT_PER_SLR(C_OUT_PER_SLR),
        .SLR_COUNT(SLR_COUNT),
        .WINDOW_COUNT(WINDOW_COUNT),
        .RING_DEPTH(73728)
    ) u_streaming_weight_store (
        .clk(s_axi_aclk),
        .rst_n(s_axi_aresetn),
        .start(stream_store_start),
        .abort(stream_store_abort),
        .stream_valid(dma_stream_valid),
        .stream_ready(dma_stream_ready),
        .stream_data(dma_stream_data),
        .stream_last(dma_stream_last),
        .pool_valid(stream_pool_valid),
        .pool_ready(stream_pool_ready),
        .pool_channel(stream_pool_channel),
        .pool_window(stream_pool_window),
        .pool_data(stream_pool_data),
        .busy(stream_store_busy),
        .load_done(stream_store_done),
        .protocol_error(stream_store_error),
        .occupancy(stream_store_occupancy)
    );

    rtwsr_weight_dma #(.ADDR_WIDTH(37)) u_weight_dma (
        .clk(s_axi_aclk),
        .rst_n(s_axi_aresetn),
        .command_valid(dma_command_valid),
        .command_ready(dma_command_ready),
        .command_address(dma_address_q),
        .command_words(dma_words_q),
        .m_axi_arvalid(m_axi_arvalid),
        .m_axi_arready(m_axi_arready),
        .m_axi_araddr(m_axi_araddr),
        .m_axi_arid(m_axi_arid),
        .m_axi_arlen(m_axi_arlen),
        .m_axi_arsize(m_axi_arsize),
        .m_axi_arburst(m_axi_arburst),
        .m_axi_rvalid(m_axi_rvalid),
        .m_axi_rready(m_axi_rready),
        .m_axi_rid(m_axi_rid),
        .m_axi_rdata(m_axi_rdata),
        .m_axi_rresp(m_axi_rresp),
        .m_axi_rlast(m_axi_rlast),
        .data_valid(dma_stream_valid),
        .data_ready(dma_stream_ready),
        .data_word(dma_stream_data),
        .data_last(dma_stream_last),
        .busy(dma_busy),
        .done(dma_done),
        .error(dma_error)
    );

    genvar slr_index;
    generate
        for (slr_index = 0; slr_index < SLR_COUNT; slr_index = slr_index + 1) begin : gen_slr
            rtwsr_top #(
                .P_CH(P_CH),
                .C_OUT(C_OUT_PER_SLR),
                .K(K),
                .ROUNDS(ROUNDS)
            ) u_rtwsr_top (
                .clk(s_axi_aclk),
                .rst_n(s_axi_aresetn),
                .weight_load_valid(weight_load_valid[slr_index]),
                .weight_load_ready(weight_load_ready[slr_index]),
                .weight_load_channel(weight_load_channel[slr_index*CHANNEL_WIDTH +: CHANNEL_WIDTH]),
                .weight_load_window(weight_load_window[slr_index*WINDOW_WIDTH +: WINDOW_WIDTH]),
                .weight_load_data(weight_load_data[slr_index*512 +: 512]),
                .round_config_valid(round_config_valid[slr_index]),
                .round_config_ready(round_config_ready[slr_index]),
                .round_gamma_fp16(round_gamma_q[slr_index*P_CH*16 +: P_CH*16]),
                .round_activation_scale_fp16(activation_scale_q),
                .activation_valid(activation_valid[slr_index]),
                .activation_ready(activation_ready[slr_index]),
                .activation_window(activation_window_q),
                .tile_result_valid(tile_result_valid[slr_index]),
                .output_tile_index(output_tile_index[slr_index*TILE_WIDTH +: TILE_WIDTH]),
                .tile_result_q12(tile_result_q12[slr_index*P_CH*32 +: P_CH*32]),
                .round_result_valid(round_result_valid[slr_index]),
                .round_index(round_index[slr_index*ROUND_WIDTH +: ROUND_WIDTH]),
                .done(core_done[slr_index])
            );
        end
    endgenerate

    always_ff @(posedge s_axi_aclk) begin
        if (!s_axi_aresetn) begin
            awaddr_q <= '0;
            wdata_q <= '0;
            wstrb_q <= '0;
            aw_pending <= 1'b0;
            w_pending <= 1'b0;
            araddr_q <= '0;
            s_axi_bresp <= 2'b00;
            s_axi_bvalid <= 1'b0;
            s_axi_rdata <= '0;
            s_axi_rresp <= 2'b00;
            s_axi_rvalid <= 1'b0;
            weight_route_q <= '0;
            weight_window_q <= '0;
            activation_scale_q <= 16'h3c00;
            weight_data_q <= '0;
            activation_window_q <= '0;
            round_gamma_q <= '0;
            dma_address_q <= '0;
            dma_words_q <= '0;
            operator_valid <= 1'b0;
            dma_done_latched <= 1'b0;
            weight_pending <= 1'b0;
            round_pending <= 1'b0;
            activation_pending <= 1'b0;
            error_q <= '0;
            tile_result_seen <= '0;
            result_tile_q <= '0;
            result_round_q <= '0;
            run_active <= 1'b0;
            run_cycles <= '0;
            run_cycles_latched <= '0;
        end else begin
            if (s_axi_awvalid && s_axi_awready) begin
                awaddr_q <= s_axi_awaddr;
                aw_pending <= 1'b1;
            end
            if (s_axi_wvalid && s_axi_wready) begin
                wdata_q <= s_axi_wdata;
                wstrb_q <= s_axi_wstrb;
                w_pending <= 1'b1;
            end
            if (write_commit) begin
                aw_pending <= 1'b0;
                w_pending <= 1'b0;
                s_axi_bvalid <= 1'b1;
                s_axi_bresp <= 2'b00;

                if (|write_addr[1:0]) begin
                    error_q[0] <= 1'b1;
                end else if (write_index == 10'h000) begin
                    if (write_strb[0] && write_data[0]) begin
                        if (weight_pending || dma_busy || stream_store_busy || run_active)
                            error_q[0] <= 1'b1;
                        else begin
                            weight_pending <= 1'b1;
                            operator_valid <= 1'b0;
                        end
                    end
                    if (write_strb[0] && write_data[1]) begin
                        if (round_pending || (!run_active &&
                            (!operator_valid || dma_busy || stream_store_busy)))
                            error_q[1] <= 1'b1;
                        else
                            round_pending <= 1'b1;
                    end
                    if (write_strb[0] && write_data[2]) begin
                        if (activation_pending)
                            error_q[2] <= 1'b1;
                        else
                            activation_pending <= 1'b1;
                    end
                    if (write_strb[0] && write_data[3])
                        tile_result_seen <= '0;
                    if (write_strb[0] && write_data[4]) begin
                        if (weight_pending || dma_busy || stream_store_busy || run_active)
                            error_q[0] <= 1'b1;
                        else
                            operator_valid <= 1'b1;
                    end
                end else if (write_index == 10'h001) begin
                    if (write_strb[0] && write_data[0])
                        tile_result_seen <= '0;
                    if (write_strb[0] && write_data[1])
                        error_q <= '0;
                end else if (write_index == 10'h002) begin
                    weight_route_q <= merged_value[12:0];
                    if (int'(merged_value[12:11]) >= SLR_COUNT)
                        error_q[0] <= 1'b1;
                end else if (write_index == 10'h003) begin
                    weight_window_q <= merged_value[WINDOW_WIDTH-1:0];
                    if (merged_value >= WINDOW_COUNT)
                        error_q[0] <= 1'b1;
                end else if (write_index == 10'h004) begin
                    if (|merged_value[1:0]) begin
                        error_q[0] <= 1'b1;
                    end
                end else if (write_index == 10'h005) begin
                    activation_scale_q <= merged_value[15:0];
                end else if (write_index == 10'h007) begin
                    dma_address_q[31:0] <= merged_value;
                end else if (write_index == 10'h008) begin
                    dma_address_q[36:32] <= merged_value[4:0];
                end else if (write_index == 10'h009) begin
                    dma_words_q <= merged_value;
                end else if (write_index == DMA_STATUS) begin
                    if (write_strb[0] && write_data[1])
                        dma_done_latched <= 1'b0;
                    if (write_strb[0] && write_data[0]) begin
                        if (!dma_command_ready || dma_busy || stream_store_busy || dma_done ||
                            weight_pending || dma_words_q != OPERATOR_WORDS ||
                            dma_address_q[5:0] != '0) begin
                            error_q[0] <= 1'b1;
                        end else begin
                            dma_done_latched <= 1'b0;
                            if (!run_active)
                                operator_valid <= 1'b0;
                        end
                    end
                end else if (write_index >= WEIGHT_DATA_BASE &&
                             write_index < WEIGHT_DATA_BASE + 16) begin
                    weight_data_q[(write_index-WEIGHT_DATA_BASE)*32 +: 32] <= merged_value;
                end else if (write_index >= ACTIVATION_BASE &&
                             write_index < ACTIVATION_BASE + 64) begin
                    activation_window_q[(write_index-ACTIVATION_BASE)*32 +: 32] <= merged_value;
                end else if (write_index >= GAMMA_BASE && write_index < GAMMA_BASE + 48) begin
                    round_gamma_q[(write_index-GAMMA_BASE)*32 +: 32] <= merged_value;
                end else begin
                    error_q[0] <= 1'b1;
                end
            end

            if (s_axi_bvalid && s_axi_bready)
                s_axi_bvalid <= 1'b0;

            if (weight_pending && int'(weight_route_q[12:11]) < SLR_COUNT &&
                weight_load_ready[weight_route_q[12:11]]) begin
                weight_pending <= 1'b0;
                operator_valid <= 1'b0;
            end
            if (dma_done) begin
                dma_done_latched <= 1'b1;
            end
            if (stream_store_done)
                operator_valid <= 1'b1;
            if (stream_store_error) begin
                error_q[0] <= 1'b1;
                operator_valid <= 1'b0;
            end
            if (round_pending && all_round_ready &&
                (run_active || (operator_valid && !stream_store_busy && !dma_busy))) begin
                round_pending <= 1'b0;
                if (!run_active) begin
                    run_cycles <= '0;
                    run_active <= 1'b1;
                end
            end
            if (activation_pending && all_activation_ready)
                activation_pending <= 1'b0;

            if (run_active)
                run_cycles <= run_cycles + 1'b1;
            if (run_active && all_done) begin
                run_active <= 1'b0;
                run_cycles_latched <= run_cycles;
                if (stream_store_busy && !stream_store_done)
                    operator_valid <= 1'b0;
            end

            for (integer slr = 0; slr < SLR_COUNT; slr++) begin
                if (tile_result_valid[slr]) begin
                    tile_result_seen[slr] <= 1'b1;
                end
            end
            if (tile_result_valid[0]) begin
                result_tile_q <= output_tile_index[TILE_WIDTH-1:0];
                result_round_q <= round_index[ROUND_WIDTH-1:0];
            end

            if (s_axi_arvalid && s_axi_arready) begin
                araddr_q <= s_axi_araddr;
                s_axi_rdata <= read_value;
                s_axi_rresp <= 2'b00;
                s_axi_rvalid <= 1'b1;
            end else if (s_axi_rvalid && s_axi_rready) begin
                s_axi_rvalid <= 1'b0;
            end
        end
    end

    genvar result_slr;
    genvar result_channel;
    generate
        for (result_slr = 0; result_slr < SLR_COUNT; result_slr++) begin : gen_result_slr
            for (result_channel = 0; result_channel < P_CH; result_channel++) begin : gen_result_channel
                localparam int RESULT_INDEX = result_slr * P_CH + result_channel;
                always_ff @(posedge s_axi_aclk) begin
                    if (!s_axi_aresetn)
                        result_words[RESULT_INDEX] <= '0;
                    else if (tile_result_valid[result_slr])
                        result_words[RESULT_INDEX] <=
                            tile_result_q12[RESULT_INDEX*32 +: 32];
                end
            end
        end
    endgenerate

    initial begin
        if (SLR_COUNT != 3 || P_CH != 32 || C_OUT_PER_SLR != 1760 || K != 17920 || ROUNDS != 32)
            $error("Plan 5 shell wrapper requires the full 3-SLR configuration");
        if (S_AXI_DATA_WIDTH != 32 || S_AXI_ADDR_WIDTH < 12)
            $error("AXI4-Lite data width must be 32 bits and address width at least 12 bits");
    end
endmodule
