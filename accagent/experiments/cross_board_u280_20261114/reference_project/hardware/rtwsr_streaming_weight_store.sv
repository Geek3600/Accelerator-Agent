`timescale 1ns / 1ps

module rtwsr_streaming_weight_store #(
    parameter int P_CH = 32,
    parameter int C_OUT_PER_SLR = 1760,
    parameter int SLR_COUNT = 3,
    parameter int WINDOW_COUNT = 70,
    parameter int RING_DEPTH = 73728,
    parameter int TILE_COUNT = (C_OUT_PER_SLR + P_CH - 1) / P_CH,
    parameter int GLOBAL_TILE_COUNT = SLR_COUNT * TILE_COUNT,
    parameter int CHANNEL_WIDTH = (C_OUT_PER_SLR <= 1) ? 1 : $clog2(C_OUT_PER_SLR),
    parameter int WINDOW_WIDTH = (WINDOW_COUNT <= 1) ? 1 : $clog2(WINDOW_COUNT),
    parameter int TILE_WIDTH = (GLOBAL_TILE_COUNT <= 1) ? 1 : $clog2(GLOBAL_TILE_COUNT),
    parameter int RING_SEQUENCE_WIDTH = (P_CH * WINDOW_COUNT <= 1) ? 1 : $clog2(P_CH * WINDOW_COUNT),
    parameter int OPERATOR_WORDS = SLR_COUNT * C_OUT_PER_SLR * WINDOW_COUNT,
    parameter int OCCUPANCY_WIDTH = $clog2(RING_DEPTH + 1)
)(
    input  logic                                  clk,
    input  logic                                  rst_n,
    input  logic                                  start,
    input  logic                                  abort,
    input  logic                                  stream_valid,
    output logic                                  stream_ready,
    input  logic [511:0]                          stream_data,
    input  logic                                  stream_last,
    output logic [SLR_COUNT-1:0]                  pool_valid,
    input  logic [SLR_COUNT-1:0]                  pool_ready,
    output logic [SLR_COUNT*CHANNEL_WIDTH-1:0]    pool_channel,
    output logic [SLR_COUNT*WINDOW_WIDTH-1:0]     pool_window,
    output logic [SLR_COUNT*512-1:0]              pool_data,
    output logic                                  busy,
    output logic                                  load_done,
    output logic                                  protocol_error,
    output logic [OCCUPANCY_WIDTH-1:0]            occupancy
);
    localparam int TILE_RECORDS = P_CH * WINDOW_COUNT;
    localparam int OUTPUT_CHANNEL_WIDTH = $clog2(SLR_COUNT * C_OUT_PER_SLR);
    localparam int RING_WINDOW_COUNT = TILE_RECORDS;

    logic busy_q;
    logic [31:0] input_word_index_q;
    logic [31:0] output_word_index_q;
    logic [TILE_WIDTH-1:0] push_tile;
    logic [RING_SEQUENCE_WIDTH-1:0] push_sequence;
    logic push_tile_last;
    logic push_valid;
    logic push_ready;
    logic [511:0] push_data;
    logic out_valid;
    logic out_ready;
    logic [TILE_WIDTH-1:0] out_tile;
    logic [RING_SEQUENCE_WIDTH-1:0] out_sequence;
    logic out_tile_last;
    logic [511:0] out_data;
    logic [GLOBAL_TILE_COUNT-1:0] tile_complete;
    logic ring_protocol_error;
    logic [OCCUPANCY_WIDTH-1:0] ring_occupancy;
    logic last_error_q;
    logic [OUTPUT_CHANNEL_WIDTH-1:0] output_global_channel;
    logic [1:0] output_slr;
    logic [CHANNEL_WIDTH-1:0] output_local_channel;
    logic [WINDOW_WIDTH-1:0] output_window;
    logic output_route_valid;
    logic output_fire;

    always_comb begin
        push_tile = TILE_WIDTH'((input_word_index_q / WINDOW_COUNT) / P_CH);
        push_sequence = RING_SEQUENCE_WIDTH'(
            ((input_word_index_q / WINDOW_COUNT) % P_CH) * WINDOW_COUNT +
            (input_word_index_q % WINDOW_COUNT)
        );
        push_tile_last = push_sequence == RING_SEQUENCE_WIDTH'(TILE_RECORDS - 1);
        push_valid = busy_q && stream_valid && input_word_index_q < OPERATOR_WORDS;
        push_data = stream_data;
        stream_ready = busy_q && push_ready && input_word_index_q < OPERATOR_WORDS;
    end

    always_comb begin
        output_global_channel = OUTPUT_CHANNEL_WIDTH'(
            int'(out_tile) * P_CH + int'(out_sequence) / WINDOW_COUNT
        );
        output_slr = 2'(int'(output_global_channel) / C_OUT_PER_SLR);
        output_local_channel = CHANNEL_WIDTH'(int'(output_global_channel) % C_OUT_PER_SLR);
        output_window = WINDOW_WIDTH'(int'(out_sequence) % WINDOW_COUNT);
        output_route_valid = int'(output_global_channel) < SLR_COUNT * C_OUT_PER_SLR &&
                             int'(output_slr) < SLR_COUNT;
        pool_channel = '0;
        pool_window = '0;
        pool_data = '0;
        if (output_route_valid) begin
            pool_channel[output_slr*CHANNEL_WIDTH +: CHANNEL_WIDTH] = output_local_channel;
            pool_window[output_slr*WINDOW_WIDTH +: WINDOW_WIDTH] = output_window;
            pool_data[output_slr*512 +: 512] = out_data;
        end
    end

    always_comb begin
        pool_valid = '0;
        out_ready = 1'b0;
        if (output_route_valid) begin
            pool_valid[output_slr] = out_valid;
            out_ready = pool_ready[output_slr];
        end
        output_fire = out_valid && out_ready;
    end

    assign busy = busy_q;
    assign occupancy = ring_occupancy;
    assign protocol_error = ring_protocol_error || last_error_q;

    uram_shadow_ring #(
        .DEPTH(RING_DEPTH),
        .TILE_SLOTS(GLOBAL_TILE_COUNT),
        .WINDOW_COUNT(RING_WINDOW_COUNT),
        .WORDS_PER_WINDOW(1),
        .TILE_WIDTH(TILE_WIDTH),
        .WINDOW_WIDTH(RING_SEQUENCE_WIDTH),
        .WORD_WIDTH(1),
        .ADDR_WIDTH($clog2(RING_DEPTH))
    ) u_shadow_ring (
        .clk(clk),
        .rst_n(rst_n && !abort),
        .push_valid(push_valid),
        .push_ready(push_ready),
        .push_tile(push_tile),
        .push_window(push_sequence),
        .push_word(1'b0),
        .push_tile_last(push_tile_last),
        .push_data(push_data),
        .out_valid(out_valid),
        .out_ready(out_ready),
        .out_tile(out_tile),
        .out_window(out_sequence),
        .out_word(),
        .out_tile_last(out_tile_last),
        .out_data(out_data),
        .tile_complete(tile_complete),
        .protocol_error(ring_protocol_error),
        .occupancy(ring_occupancy)
    );

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            busy_q <= 1'b0;
            input_word_index_q <= '0;
            output_word_index_q <= '0;
            load_done <= 1'b0;
            last_error_q <= 1'b0;
        end else begin
            load_done <= 1'b0;
            if (start && !busy_q) begin
                busy_q <= 1'b1;
                input_word_index_q <= '0;
                output_word_index_q <= '0;
            end
            if (abort) begin
                busy_q <= 1'b0;
                input_word_index_q <= '0;
                output_word_index_q <= '0;
                last_error_q <= 1'b0;
            end else begin
                if (stream_valid && stream_ready) begin
                    if (stream_last != (input_word_index_q == OPERATOR_WORDS - 1))
                        last_error_q <= 1'b1;
                    input_word_index_q <= input_word_index_q + 1'b1;
                end
                if (output_fire) begin
                    output_word_index_q <= output_word_index_q + 1'b1;
                    if (output_word_index_q == OPERATOR_WORDS - 1) begin
                        busy_q <= 1'b0;
                        load_done <= 1'b1;
                    end
                end
            end
            if (abort)
                last_error_q <= 1'b0;
        end
    end

    initial begin
        if (P_CH < 1 || C_OUT_PER_SLR < 1 || SLR_COUNT < 1 || WINDOW_COUNT < 1 ||
            RING_DEPTH < TILE_RECORDS || OPERATOR_WORDS != SLR_COUNT*C_OUT_PER_SLR*WINDOW_COUNT)
            $error("invalid streaming weight-store dimensions");
    end
endmodule
