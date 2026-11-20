`timescale 1ns / 1ps

module rtwsr_adapter_static_cache #(
    parameter int HIDDEN_SIZE = 5280,
    parameter int CHANNELS = 96,
    parameter int SUM_WIDTH = 37,
    parameter int TILE_COUNT = (HIDDEN_SIZE + CHANNELS - 1) / CHANNELS,
    parameter int TILE_WIDTH = $clog2(TILE_COUNT)
)(
    input  logic clk,
    input  logic rst_n,
    input  logic invalidate,
    input  logic [6:0] window_index,
    input  logic [2047:0] activation_window,
    output logic [2047:0] state_window,
    output logic [2047:0] embedding_window,
    input  logic write_enable,
    input  logic [TILE_WIDTH-1:0] write_tile,
    input  logic [CHANNELS*SUM_WIDTH-1:0] write_sum,
    input  logic read_enable,
    input  logic [TILE_WIDTH-1:0] read_tile,
    output logic tile_valid,
    output logic read_valid,
    output logic [CHANNELS*SUM_WIDTH-1:0] read_sum,
    output logic protocol_error
);
    (* ram_style = "block" *) logic [CHANNELS*SUM_WIDTH-1:0] sums [0:TILE_COUNT-1];
    logic [TILE_COUNT-1:0] valid_tiles;

    assign tile_valid = int'(read_tile) < TILE_COUNT && valid_tiles[read_tile];

    always_comb begin
        state_window = '0;
        embedding_window = '0;
        for (integer byte_index = 0; byte_index < 256; byte_index++) begin
            if (int'(window_index)*256 + byte_index < HIDDEN_SIZE)
                state_window[byte_index*8 +: 8] = activation_window[byte_index*8 +: 8];
            else if (int'(window_index)*256 + byte_index < 2*HIDDEN_SIZE)
                embedding_window[byte_index*8 +: 8] = activation_window[byte_index*8 +: 8];
        end
    end

    always_ff @(posedge clk) begin
        if (!rst_n || invalidate) begin
            valid_tiles <= '0;
            read_valid <= 1'b0;
            protocol_error <= 1'b0;
        end else begin
            read_valid <= 1'b0;
            if (write_enable) begin
                if (int'(write_tile) < TILE_COUNT) begin
                    sums[write_tile] <= write_sum;
                    valid_tiles[write_tile] <= 1'b1;
                end else begin
                    protocol_error <= 1'b1;
                end
            end
            if (read_enable) begin
                if (int'(read_tile) < TILE_COUNT && valid_tiles[read_tile]) begin
                    read_sum <= sums[read_tile];
                    read_valid <= 1'b1;
                end else begin
                    protocol_error <= 1'b1;
                end
            end
        end
    end
endmodule
