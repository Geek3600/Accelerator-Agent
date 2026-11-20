`timescale 1ns / 1ps

module rtwsr_linear_tile_controller #(
    parameter int CHANNELS = 96,
    parameter int ROW_COUNT_WIDTH = (CHANNELS <= 127) ? 7 : 8,
    parameter int TILE_INDEX_WIDTH = 9,
    parameter int USW_WINDOW_SIZE = 256,
    parameter int WORDS_PER_USW = 4,
    parameter int POOL_DEPTH = 16384,
    parameter int WINDOW_COUNT_WIDTH = 7,
    parameter int POOL_COUNT_WIDTH = 15
)(
    input  logic        clk,
    input  logic        rst_n,
    input  logic        command_valid,
    output logic        command_ready,
    input  logic [4:0]  command_id,
    input  logic [5:0]  block_index,
    input  logic [4:0]  recurrence_index,
    input  logic [15:0] matrix_rows,
    input  logic [15:0] matrix_columns,
    output logic        tile_valid,
    input  logic        tile_ready,
    input  logic        tile_done,
    output logic [4:0]  tile_command_id,
    output logic [5:0]  tile_block_index,
    output logic [4:0]  tile_recurrence_index,
    output logic [15:0] tile_matrix_rows,
    output logic [15:0] tile_matrix_columns,
    output logic [WINDOW_COUNT_WIDTH-1:0] matrix_window_count,
    output logic [POOL_COUNT_WIDTH-1:0] matrix_pool_words_per_port,
    output logic [POOL_COUNT_WIDTH-1:0] tile_pool_base_per_port,
    output logic [TILE_INDEX_WIDTH-1:0] tile_index,
    output logic [15:0] tile_row_start,
    output logic [ROW_COUNT_WIDTH-1:0] tile_active_rows,
    output logic        command_done,
    output logic        protocol_error
);
    logic active_q;
    logic tile_inflight_q;
    logic [4:0] command_id_q;
    logic [5:0] block_index_q;
    logic [4:0] recurrence_index_q;
    logic [15:0] rows_q;
    logic [15:0] columns_q;
    logic [WINDOW_COUNT_WIDTH-1:0] window_count_q;
    logic [POOL_COUNT_WIDTH-1:0] pool_words_per_port_q;
    logic [TILE_INDEX_WIDTH-1:0] tile_index_q;
    logic [31:0] row_start_wide;
    logic [31:0] rows_remaining;
    logic [31:0] requested_tiles;
    logic [31:0] requested_windows;
    logic [31:0] requested_pool_words;

    assign command_ready = !active_q;
    assign tile_valid = active_q && !tile_inflight_q;
    assign tile_command_id = active_q ? command_id_q : '0;
    assign tile_block_index = active_q ? block_index_q : '0;
    assign tile_recurrence_index = active_q ? recurrence_index_q : '0;
    assign tile_matrix_rows = active_q ? rows_q : '0;
    assign tile_matrix_columns = active_q ? columns_q : '0;
    assign matrix_window_count = active_q ? window_count_q : '0;
    assign matrix_pool_words_per_port = active_q ? pool_words_per_port_q : '0;
    assign tile_pool_base_per_port = active_q ?
        POOL_COUNT_WIDTH'(int'(tile_index_q) * int'(window_count_q) * WORDS_PER_USW) : '0;
    assign tile_index = active_q ? tile_index_q : '0;
    assign row_start_wide = int'(tile_index_q) * CHANNELS;
    assign rows_remaining = int'(rows_q) - row_start_wide;
    assign tile_row_start = active_q ? 16'(row_start_wide) : '0;
    assign tile_active_rows = !active_q ? '0 :
                              (rows_remaining >= CHANNELS ? ROW_COUNT_WIDTH'(CHANNELS) :
                               ROW_COUNT_WIDTH'(rows_remaining));
    assign requested_tiles = (int'(matrix_rows) + CHANNELS - 1) / CHANNELS;
    assign requested_windows = (int'(matrix_columns) + USW_WINDOW_SIZE - 1) / USW_WINDOW_SIZE;
    assign requested_pool_words = requested_tiles * requested_windows * WORDS_PER_USW;

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            active_q <= 1'b0;
            tile_inflight_q <= 1'b0;
            command_id_q <= '0;
            block_index_q <= '0;
            recurrence_index_q <= '0;
            rows_q <= '0;
            columns_q <= '0;
            window_count_q <= '0;
            pool_words_per_port_q <= '0;
            tile_index_q <= '0;
            command_done <= 1'b0;
            protocol_error <= 1'b0;
        end else begin
            command_done <= 1'b0;
            if (command_valid && command_ready) begin
                if (matrix_rows == 0 || matrix_columns == 0) begin
                    protocol_error <= 1'b1;
                    command_done <= 1'b1;
                end else if (requested_windows >= (2 ** WINDOW_COUNT_WIDTH) ||
                             requested_pool_words > POOL_DEPTH) begin
                    protocol_error <= 1'b1;
                    command_done <= 1'b1;
                end else begin
                    active_q <= 1'b1;
                    tile_inflight_q <= 1'b0;
                    command_id_q <= command_id;
                    block_index_q <= block_index;
                    recurrence_index_q <= recurrence_index;
                    rows_q <= matrix_rows;
                    columns_q <= matrix_columns;
                    window_count_q <= WINDOW_COUNT_WIDTH'(requested_windows);
                    pool_words_per_port_q <= POOL_COUNT_WIDTH'(requested_pool_words);
                    tile_index_q <= '0;
                    protocol_error <= 1'b0;
                end
            end

            if (tile_valid && tile_ready)
                tile_inflight_q <= 1'b1;

            if (active_q && tile_inflight_q && tile_done) begin
                tile_inflight_q <= 1'b0;
                if (rows_remaining <= CHANNELS) begin
                    active_q <= 1'b0;
                    command_done <= 1'b1;
                end else begin
                    tile_index_q <= tile_index_q + 1'b1;
                end
            end
        end
    end

    initial begin
        if (CHANNELS < 1 || CHANNELS > 255 || ROW_COUNT_WIDTH < $clog2(CHANNELS + 1) ||
            TILE_INDEX_WIDTH < 1 ||
            USW_WINDOW_SIZE < 1 || WORDS_PER_USW < 1 || POOL_DEPTH < 1)
            $error("invalid shared linear tile dimensions");
    end
endmodule
