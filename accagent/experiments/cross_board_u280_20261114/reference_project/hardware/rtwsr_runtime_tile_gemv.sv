`timescale 1ns / 1ps

// A shared three-SLR array. Parallel slot reads supply one weight record per output row.
module rtwsr_runtime_tile_gemv #(
    parameter int CHANNELS = 96,
    parameter int ROW_COUNT_WIDTH = (CHANNELS <= 127) ? 7 : 8,
    parameter bit ADAPTER_STATIC_REUSE = 1'b0,
    parameter int TRITS_PER_CYCLE = 64,
    parameter bit READ_PARALLEL_SLOTS = 1'b0
) (
    input logic clk,
    input logic rst_n,
    input logic tile_valid,
    output logic tile_ready,
    input logic [8:0] tile_index,
    input logic [ROW_COUNT_WIDTH-1:0] tile_rows,
    input logic [15:0] matrix_columns,
    input logic [CHANNELS*16-1:0] tile_gamma_fp16,
    input logic [15:0] activation_scale_fp16,
    input logic adapter_reuse,
    input logic adapter_cache_invalidate,
    output logic activation_ready,
    input logic activation_valid,
    input logic [2047:0] activation_window,
    output logic [6:0] activation_window_index,
    output logic pool_read_enable,
    output logic [8:0] pool_read_tile_index,
    output logic [6:0] pool_read_window_index,
    output logic [1:0] pool_read_subword_index,
    input logic pool_read_valid,
    input logic [(READ_PARALLEL_SLOTS ? CHANNELS : CHANNELS/4)*512-1:0] pool_read_data,
    output logic result_valid,
    input logic result_ready,
    output logic [CHANNELS*32-1:0] result_q12,
    output logic [ROW_COUNT_WIDTH-1:0] result_rows,
    output logic tile_done,
    output logic protocol_error
);
    typedef enum logic [2:0] {IDLE, ACTIVE, WAIT_RESULT, CACHE_REQUEST, CACHE_WAIT, RESULT} state_t;
    state_t state_q;
    logic [8:0] tile_q;
    logic [ROW_COUNT_WIDTH-1:0] rows_q;
    logic [6:0] windows_q, load_window_q, execute_window_q;
    logic [15:0] columns_q;
    logic read_burst_q;
    logic [1:0] read_subword_q, subchunk_q;
    logic read_pending_q, read_pending_q1, read_pending_q2;
    logic read_slot_q, read_slot_q1, read_slot_q2;
    logic [1:0] return_subword_q, return_subword_q1, return_subword_q2;
    logic [1:0] buffer_ready_q, buffer_loading_q;
    (* ram_style = "registers" *) logic [511:0] words_0_q [0:CHANNELS-1];
    (* ram_style = "registers" *) logic [511:0] words_1_q [0:CHANNELS-1];
    logic [CHANNELS*512-1:0] active_words;
    logic [2047:0] activation_q [0:1];
    logic [CHANNELS*16-1:0] gamma_q;
    logic [15:0] scale_q;
    logic [CHANNELS-1:0] array_done;
    logic [CHANNELS*32-1:0] array_result;
    logic [CHANNELS*37-1:0] array_unscaled_sum, static_sum;
    logic [2047:0] activation_mask;
    logic execute_valid;
    logic release_buffer;
    logic load_slot_available;
    logic adapter_reuse_q, static_pass_q;
    logic [6:0] first_window_q, final_window_q;
    logic cache_tile_valid, cache_read_valid, cache_error;
    logic cache_write_enable, cache_read_enable;

    localparam int ADAPTER_TILE_COUNT = (5280 + CHANNELS - 1) / CHANNELS;

    assign cache_write_enable = ADAPTER_STATIC_REUSE && state_q == WAIT_RESULT &&
        (|array_done) && static_pass_q;
    assign cache_read_enable = ADAPTER_STATIC_REUSE &&
        ((state_q == IDLE && tile_valid && adapter_reuse && cache_tile_valid) ||
         state_q == CACHE_REQUEST);

    generate
        if (ADAPTER_STATIC_REUSE) begin : g_adapter_cache
            rtwsr_adapter_static_cache #(
                .CHANNELS(CHANNELS)
            ) u_cache (
                .clk(clk), .rst_n(rst_n), .invalidate(adapter_cache_invalidate),
                .window_index(load_window_q), .activation_window('0),
                .state_window(), .embedding_window(),
                .write_enable(cache_write_enable), .write_tile(tile_q[5:0]),
                .write_sum(array_unscaled_sum), .read_enable(cache_read_enable),
                .read_tile(state_q == IDLE ? tile_index[5:0] : tile_q[5:0]),
                .tile_valid(cache_tile_valid), .read_valid(cache_read_valid),
                .read_sum(static_sum), .protocol_error(cache_error)
            );
        end else begin : g_no_adapter_cache
            assign static_sum = '0;
            assign cache_tile_valid = 1'b0;
            assign cache_read_valid = 1'b0;
            assign cache_error = 1'b0;
        end
    endgenerate

    assign tile_ready = state_q == IDLE;
    assign execute_valid = state_q == ACTIVE && buffer_ready_q[execute_window_q[0]];
    localparam int SUBCHUNKS_PER_CYCLE = TRITS_PER_CYCLE / 64;
    assign release_buffer = execute_valid &&
        int'(subchunk_q) + SUBCHUNKS_PER_CYCLE >= 4;
    assign load_slot_available =
        (!buffer_ready_q[load_window_q[0]] &&
         (!READ_PARALLEL_SLOTS || !buffer_loading_q[load_window_q[0]])) ||
        (release_buffer && execute_window_q[0] == load_window_q[0]);
    assign activation_ready = state_q == ACTIVE && !read_burst_q &&
        load_window_q < windows_q && load_slot_available;
    assign activation_window_index = load_window_q;
    assign pool_read_enable = state_q == ACTIVE &&
        (read_burst_q || (activation_ready && activation_valid));
    assign pool_read_tile_index = tile_q;
    assign pool_read_window_index = load_window_q;
    assign pool_read_subword_index = READ_PARALLEL_SLOTS ? 2'd0 :
        (read_burst_q ? read_subword_q : 2'd0);
    assign result_valid = state_q == RESULT;
    assign result_rows = rows_q;

    always_comb begin
        for (integer element_id = 0; element_id < 256; element_id = element_id + 1)
            activation_mask[element_id*8 +: 8] =
                int'(load_window_q)*256 + element_id < int'(columns_q) &&
                (!adapter_reuse_q ||
                 (static_pass_q ? int'(load_window_q)*256 + element_id >= 5280 :
                                  int'(load_window_q)*256 + element_id < 5280)) ?
                8'hff : 8'h00;
    end

    rtwsr_dual_track_gemv_array #(
        .CHANNELS_PER_SLR(CHANNELS / 3),
        .STATIC_REUSE(ADAPTER_STATIC_REUSE),
        .TRITS_PER_CYCLE(TRITS_PER_CYCLE)
    ) u_array (
        .clk(clk), .rst_n(rst_n), .valid_in(execute_valid),
        .first_subchunk(execute_window_q == first_window_q && subchunk_q == 0),
        .last_subchunk(execute_window_q == final_window_q &&
            int'(subchunk_q) + SUBCHUNKS_PER_CYCLE >= 4),
        .subchunk_index(subchunk_q), .usw_words(active_words),
        .activation_window(activation_q[execute_window_q[0]]), .fused_gamma_fp16(gamma_q),
        .activation_scale_fp16(scale_q),
        .static_sum_enable(adapter_reuse_q && !static_pass_q), .static_sums_q12(static_sum),
        .row_done_valid(array_done), .final_channels_q12(array_result),
        .unscaled_sums_q12(array_unscaled_sum)
    );

    genvar row;
    generate
        for (row = 0; row < CHANNELS; row = row + 1) begin : gen_weight_row
            assign active_words[row*512 +: 512] =
                execute_window_q[0] ? words_1_q[row] : words_0_q[row];

            always_ff @(posedge clk) begin
                if (rst_n && pool_read_valid &&
                    (READ_PARALLEL_SLOTS || return_subword_q2 == 2'(row % 4))) begin
                    if (read_slot_q2) begin
                        words_1_q[row] <= row < int'(rows_q) ?
                        pool_read_data[(READ_PARALLEL_SLOTS ? row : row/4)*512 +: 512] : 512'd0;
                    end else begin
                        words_0_q[row] <= row < int'(rows_q) ?
                        pool_read_data[(READ_PARALLEL_SLOTS ? row : row/4)*512 +: 512] : 512'd0;
                    end
                end
            end
        end
    endgenerate

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            state_q <= IDLE;
            tile_q <= '0;
            rows_q <= '0;
            columns_q <= '0;
            windows_q <= '0;
            load_window_q <= '0;
            execute_window_q <= '0;
            read_burst_q <= 1'b0;
            read_subword_q <= '0;
            read_pending_q <= 1'b0;
            read_pending_q1 <= 1'b0;
            read_pending_q2 <= 1'b0;
            read_slot_q <= 1'b0;
            read_slot_q1 <= 1'b0;
            read_slot_q2 <= 1'b0;
            return_subword_q <= '0;
            return_subword_q1 <= '0;
            return_subword_q2 <= '0;
            buffer_ready_q <= '0;
            buffer_loading_q <= '0;
            subchunk_q <= '0;
            gamma_q <= '0;
            scale_q <= '0;
            result_q12 <= '0;
            tile_done <= 1'b0;
            protocol_error <= 1'b0;
            adapter_reuse_q <= 1'b0;
            static_pass_q <= 1'b0;
            first_window_q <= '0;
            final_window_q <= '0;
        end else begin
            if (cache_error)
                protocol_error <= 1'b1;
            tile_done <= 1'b0;
            read_pending_q <= pool_read_enable;
            read_pending_q1 <= read_pending_q;
            read_pending_q2 <= read_pending_q1;
            read_slot_q1 <= read_slot_q;
            read_slot_q2 <= read_slot_q1;
            return_subword_q1 <= return_subword_q;
            return_subword_q2 <= return_subword_q1;
            if (pool_read_enable) begin
                read_slot_q <= load_window_q[0];
                return_subword_q <= READ_PARALLEL_SLOTS ? 2'd3 : pool_read_subword_index;
                if (READ_PARALLEL_SLOTS)
                    buffer_loading_q[load_window_q[0]] <= 1'b1;
            end
            if (pool_read_valid) begin
                if (!read_pending_q2)
                    protocol_error <= 1'b1;
                if (READ_PARALLEL_SLOTS) begin
                    buffer_loading_q[read_slot_q2] <= 1'b0;
                    buffer_ready_q[read_slot_q2] <= 1'b1;
                end else if (return_subword_q2 == 3) begin
                    buffer_ready_q[read_slot_q2] <= 1'b1;
                end
            end
            case (state_q)
                IDLE: if (tile_valid) begin
                    if (tile_rows == 0 || tile_rows > CHANNELS || matrix_columns == 0 ||
                        matrix_columns > 32512 ||
                        (ADAPTER_STATIC_REUSE && adapter_reuse &&
                         (matrix_columns != 10560 ||
                          int'(tile_index) >= ADAPTER_TILE_COUNT))) begin
                        protocol_error <= 1'b1;
                        tile_done <= 1'b1;
                    end else begin
                        protocol_error <= 1'b0;
                        tile_q <= tile_index;
                        rows_q <= tile_rows;
                        columns_q <= matrix_columns;
                        adapter_reuse_q <= ADAPTER_STATIC_REUSE && adapter_reuse;
                        static_pass_q <= ADAPTER_STATIC_REUSE && adapter_reuse && !cache_tile_valid;
                        first_window_q <= ADAPTER_STATIC_REUSE && adapter_reuse && !cache_tile_valid ? 7'd20 : 7'd0;
                        final_window_q <= ADAPTER_STATIC_REUSE && adapter_reuse && cache_tile_valid ?
                            7'd20 : 7'((int'(matrix_columns) + 255) / 256 - 1);
                        windows_q <= ADAPTER_STATIC_REUSE && adapter_reuse && cache_tile_valid ?
                            7'd21 : 7'((int'(matrix_columns) + 255) / 256);
                        load_window_q <= ADAPTER_STATIC_REUSE && adapter_reuse && !cache_tile_valid ? 7'd20 : 7'd0;
                        execute_window_q <= ADAPTER_STATIC_REUSE && adapter_reuse && !cache_tile_valid ? 7'd20 : 7'd0;
                        buffer_ready_q <= '0;
                        buffer_loading_q <= '0;
                        read_burst_q <= 1'b0;
                        subchunk_q <= '0;
                        gamma_q <= tile_gamma_fp16;
                        scale_q <= activation_scale_fp16;
                        state_q <= ACTIVE;
                    end
                end
                ACTIVE: begin
                    if (activation_ready && activation_valid) begin
                        // Two window registers overlap pool reads with array execution.
                        // Padding is masked for both the dense and sparse tracks.
                        activation_q[load_window_q[0]] <= activation_window & activation_mask;
                        if (READ_PARALLEL_SLOTS) begin
                            read_burst_q <= 1'b0;
                            load_window_q <= load_window_q + 1'b1;
                        end else begin
                            read_burst_q <= 1'b1;
                            read_subword_q <= 2'd1;
                        end
                    end else if (read_burst_q) begin
                        if (read_subword_q == 3) begin
                            read_burst_q <= 1'b0;
                            load_window_q <= load_window_q + 1'b1;
                        end else
                            read_subword_q <= read_subword_q + 1'b1;
                    end
                    if (execute_valid) begin
                        if (int'(subchunk_q) + SUBCHUNKS_PER_CYCLE >= 4) begin
                            buffer_ready_q[execute_window_q[0]] <= 1'b0;
                            subchunk_q <= '0;
                            if (execute_window_q == final_window_q)
                                state_q <= WAIT_RESULT;
                            else
                                execute_window_q <= execute_window_q + 1'b1;
                        end else
                            subchunk_q <= subchunk_q + 2'(SUBCHUNKS_PER_CYCLE);
                    end
                end
                WAIT_RESULT: if (|array_done) begin
                    if (!(&array_done))
                        protocol_error <= 1'b1;
                    if (static_pass_q) begin
                        state_q <= CACHE_REQUEST;
                    end else begin
                        for (integer row_id = 0; row_id < CHANNELS; row_id = row_id + 1)
                            result_q12[row_id*32 +: 32] <= row_id < int'(rows_q) ?
                                array_result[row_id*32 +: 32] : 32'd0;
                        state_q <= RESULT;
                    end
                end
                CACHE_REQUEST: state_q <= CACHE_WAIT;
                CACHE_WAIT: if (cache_read_valid) begin
                    static_pass_q <= 1'b0;
                    first_window_q <= '0;
                    final_window_q <= 7'd20;
                    windows_q <= 7'd21;
                    load_window_q <= '0;
                    execute_window_q <= '0;
                    buffer_ready_q <= '0;
                    buffer_loading_q <= '0;
                    read_burst_q <= 1'b0;
                    subchunk_q <= '0;
                    state_q <= ACTIVE;
                end
                RESULT: if (result_ready) begin
                    state_q <= IDLE;
                    tile_done <= 1'b1;
                end
                default: state_q <= IDLE;
            endcase
        end
    end

    initial begin
        if (TRITS_PER_CYCLE != 64 && TRITS_PER_CYCLE != 128)
            $error("runtime GEMV supports 64 or 128 trits per cycle");
        if (CHANNELS != 96 && !(CHANNELS == 192 && READ_PARALLEL_SLOTS))
            $error("runtime GEMV supports 96 channels or 192 channels with parallel slot reads");
    end
endmodule
