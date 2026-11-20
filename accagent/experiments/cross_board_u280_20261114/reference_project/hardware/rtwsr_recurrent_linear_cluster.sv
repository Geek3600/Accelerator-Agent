`timescale 1ns / 1ps

module rtwsr_recurrent_linear_cluster #(
    parameter int SLR_COUNT = 3,
    parameter int CHANNELS_PER_SLR = 32,
    parameter int C_OUT_PER_SLR = 1760,
    parameter int K = 17920,
    parameter int ROUNDS = 32,
    parameter int ACT_W = 8,
    parameter int ACC_W = 24,
    parameter int WINDOW_COUNT = (K + 255) / 256,
    parameter int CHANNEL_WIDTH = (C_OUT_PER_SLR <= 1) ? 1 : $clog2(C_OUT_PER_SLR),
    parameter int WINDOW_WIDTH = (WINDOW_COUNT <= 1) ? 1 : $clog2(WINDOW_COUNT),
    parameter int TILE_COUNT = (C_OUT_PER_SLR + CHANNELS_PER_SLR - 1) / CHANNELS_PER_SLR,
    parameter int TILE_WIDTH = (TILE_COUNT <= 1) ? 1 : $clog2(TILE_COUNT),
    parameter int ROUND_WIDTH = (ROUNDS <= 1) ? 1 : $clog2(ROUNDS),
    parameter int RING_DEPTH = 73728,
    parameter int OCCUPANCY_WIDTH = $clog2(RING_DEPTH + 1)
)(
    input  logic                                             clk,
    input  logic                                             rst_n,
    input  logic                                             weight_start,
    input  logic                                             weight_abort,
    input  logic                                             weight_stream_valid,
    output logic                                             weight_stream_ready,
    input  logic [511:0]                                     weight_stream_data,
    input  logic                                             weight_stream_last,
    output logic                                             weight_store_busy,
    output logic                                             weight_load_done,
    output logic                                             weight_protocol_error,
    output logic [OCCUPANCY_WIDTH-1:0]                       shadow_occupancy,
    input  logic [SLR_COUNT-1:0]                             round_config_valid,
    output logic [SLR_COUNT-1:0]                             round_config_ready,
    input  logic [SLR_COUNT*CHANNELS_PER_SLR*16-1:0]         round_gamma_fp16,
    input  logic [15:0]                                      round_activation_scale_fp16,
    input  logic [SLR_COUNT-1:0]                             activation_valid,
    output logic [SLR_COUNT-1:0]                             activation_ready,
    input  logic [256*ACT_W-1:0]                             activation_window,
    output logic [SLR_COUNT-1:0]                             tile_result_valid,
    output logic [SLR_COUNT*TILE_WIDTH-1:0]                  output_tile_index,
    output logic [SLR_COUNT*CHANNELS_PER_SLR*32-1:0]         tile_result_q12,
    output logic [SLR_COUNT-1:0]                             round_result_valid,
    output logic [SLR_COUNT*ROUND_WIDTH-1:0]                 round_index,
    output logic [SLR_COUNT-1:0]                             done
);
    localparam int GLOBAL_TILE_COUNT = SLR_COUNT * TILE_COUNT;

    logic [SLR_COUNT-1:0] pool_valid;
    logic [SLR_COUNT-1:0] pool_ready;
    logic [SLR_COUNT*CHANNEL_WIDTH-1:0] pool_channel;
    logic [SLR_COUNT*WINDOW_WIDTH-1:0] pool_window;
    logic [SLR_COUNT*512-1:0] pool_data;

    rtwsr_streaming_weight_store #(
        .P_CH(CHANNELS_PER_SLR),
        .C_OUT_PER_SLR(C_OUT_PER_SLR),
        .SLR_COUNT(SLR_COUNT),
        .WINDOW_COUNT(WINDOW_COUNT),
        .RING_DEPTH(RING_DEPTH),
        .TILE_COUNT(TILE_COUNT),
        .GLOBAL_TILE_COUNT(GLOBAL_TILE_COUNT),
        .CHANNEL_WIDTH(CHANNEL_WIDTH),
        .WINDOW_WIDTH(WINDOW_WIDTH),
        .OPERATOR_WORDS(SLR_COUNT*C_OUT_PER_SLR*WINDOW_COUNT),
        .OCCUPANCY_WIDTH(OCCUPANCY_WIDTH)
    ) u_weight_stream_ring (
        .clk(clk),
        .rst_n(rst_n),
        .start(weight_start),
        .abort(weight_abort),
        .stream_valid(weight_stream_valid),
        .stream_ready(weight_stream_ready),
        .stream_data(weight_stream_data),
        .stream_last(weight_stream_last),
        .pool_valid(pool_valid),
        .pool_ready(pool_ready),
        .pool_channel(pool_channel),
        .pool_window(pool_window),
        .pool_data(pool_data),
        .busy(weight_store_busy),
        .load_done(weight_load_done),
        .protocol_error(weight_protocol_error),
        .occupancy(shadow_occupancy)
    );

    genvar slr;
    generate
        for (slr = 0; slr < SLR_COUNT; slr = slr + 1) begin : gen_slr_engine
            rtwsr_top #(
                .P_CH(CHANNELS_PER_SLR),
                .C_OUT(C_OUT_PER_SLR),
                .K(K),
                .ROUNDS(ROUNDS),
                .ACT_W(ACT_W),
                .ACC_W(ACC_W),
                .WINDOW_COUNT(WINDOW_COUNT),
                .TILE_COUNT(TILE_COUNT),
                .WINDOW_WIDTH(WINDOW_WIDTH),
                .TILE_WIDTH(TILE_WIDTH),
                .ROUND_WIDTH(ROUND_WIDTH),
                .CHANNEL_WIDTH(CHANNEL_WIDTH)
            ) u_rtwsr_top (
                .clk(clk),
                .rst_n(rst_n),
                .weight_load_valid(pool_valid[slr]),
                .weight_load_ready(pool_ready[slr]),
                .weight_load_channel(pool_channel[slr*CHANNEL_WIDTH +: CHANNEL_WIDTH]),
                .weight_load_window(pool_window[slr*WINDOW_WIDTH +: WINDOW_WIDTH]),
                .weight_load_data(pool_data[slr*512 +: 512]),
                .round_config_valid(round_config_valid[slr]),
                .round_config_ready(round_config_ready[slr]),
                .round_gamma_fp16(round_gamma_fp16[slr*CHANNELS_PER_SLR*16 +: CHANNELS_PER_SLR*16]),
                .round_activation_scale_fp16(round_activation_scale_fp16),
                .activation_valid(activation_valid[slr]),
                .activation_ready(activation_ready[slr]),
                .activation_window(activation_window),
                .tile_result_valid(tile_result_valid[slr]),
                .output_tile_index(output_tile_index[slr*TILE_WIDTH +: TILE_WIDTH]),
                .tile_result_q12(tile_result_q12[slr*CHANNELS_PER_SLR*32 +: CHANNELS_PER_SLR*32]),
                .round_result_valid(round_result_valid[slr]),
                .round_index(round_index[slr*ROUND_WIDTH +: ROUND_WIDTH]),
                .done(done[slr])
            );
        end
    endgenerate

    initial begin
        if (SLR_COUNT != 3 || CHANNELS_PER_SLR != 32 || ACT_W != 8)
            $error("Plan 6 linear cluster requires 3 SLRs x 32 INT8 channels");
        if (C_OUT_PER_SLR < 1 || K < 1 || ROUNDS < 1 || RING_DEPTH < CHANNELS_PER_SLR*WINDOW_COUNT)
            $error("invalid recurrent linear cluster dimensions");
    end
endmodule
