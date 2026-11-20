`timescale 1ns / 1ps

module tb_rtwsr_plan6_core_linear_integration #(
    parameter int MODEL_ID = 0
);
    logic clk = 1'b0;
    logic rst_n = 1'b0;
    logic start = 1'b0;
    logic [15:0] context_tokens = 16'd512;
    logic command_valid;
    logic command_ready;
    logic command_done;
    logic [4:0] command_id;
    logic [3:0] command_stage;
    logic [5:0] block_index;
    logic [4:0] recurrence_index;
    logic [1:0] command_index;
    logic [15:0] matrix_rows;
    logic [15:0] matrix_columns;
    logic [15:0] vector_length;
    logic [15:0] active_context_tokens;
    logic attention_is_full;
    logic core_done;
    logic core_error;
    logic linear_engine_valid;
    logic [4:0] linear_engine_command_id;
    logic [5:0] linear_engine_block_index;
    logic [4:0] linear_engine_recurrence_index;
    logic [15:0] linear_engine_rows;
    logic [15:0] linear_engine_columns;
    logic linear_engine_ready;
    logic linear_engine_done;
    logic operator_ready = 1'b1;
    logic operator_done = 1'b0;
    logic tile_valid;
    logic tile_ready = 1'b1;
    logic tile_done = 1'b0;
    logic [4:0] tile_command_id;
    logic [5:0] tile_block_index;
    logic [4:0] tile_recurrence_index;
    logic [15:0] tile_matrix_rows;
    logic [15:0] tile_matrix_columns;
    logic [6:0] matrix_window_count;
    logic [14:0] matrix_pool_words_per_port;
    logic [14:0] tile_pool_base_per_port;
    logic [8:0] tile_index;
    logic [15:0] tile_row_start;
    logic [6:0] tile_active_rows;
    logic tile_command_done;
    logic tile_protocol_error;
    logic [4:0] expected_command_id_q;
    logic [5:0] expected_block_index_q;
    logic [4:0] expected_recurrence_index_q;
    logic [15:0] expected_rows_q;
    logic [15:0] expected_columns_q;
    logic [8:0] expected_tile_index_q;
    logic tile_pending_q;
    logic operator_pending_q;
    logic [1:0] tile_delay_q;
    integer command_total;
    integer linear_command_total;
    integer tile_total;
    integer max_pool_words;
    integer expected_commands;
    integer timeout_cycles;

    always #5 clk = ~clk;

    rtwsr_recurrent_command_scheduler #(.MODEL_ID(MODEL_ID)) u_scheduler (
        .clk(clk), .rst_n(rst_n), .start(start), .context_tokens(context_tokens),
        .command_valid(command_valid), .command_ready(command_ready),
        .command_done(command_done), .command_id(command_id),
        .command_stage(command_stage), .block_index(block_index),
        .recurrence_index(recurrence_index), .command_index(command_index),
        .matrix_rows(matrix_rows), .matrix_columns(matrix_columns),
        .vector_length(vector_length), .active_context_tokens(active_context_tokens),
        .attention_is_full(attention_is_full), .done(core_done), .error(core_error)
    );

    rtwsr_linear_command_dispatch u_dispatch (
        .command_valid(command_valid), .command_id(command_id),
        .block_index(block_index), .recurrence_index(recurrence_index),
        .matrix_rows(matrix_rows), .matrix_columns(matrix_columns),
        .linear_engine_ready(linear_engine_ready), .linear_engine_done(linear_engine_done),
        .operator_ready(operator_ready), .operator_done(operator_done),
        .linear_engine_valid(linear_engine_valid),
        .linear_engine_command_id(linear_engine_command_id),
        .linear_engine_block_index(linear_engine_block_index),
        .linear_engine_recurrence_index(linear_engine_recurrence_index),
        .linear_engine_rows(linear_engine_rows), .linear_engine_columns(linear_engine_columns),
        .scheduler_command_ready(command_ready), .scheduler_command_done(command_done)
    );

    rtwsr_linear_tile_controller #(
        .CHANNELS(96), .TILE_INDEX_WIDTH(9), .POOL_DEPTH(16384)
    ) u_tiles (
        .clk(clk), .rst_n(rst_n), .command_valid(linear_engine_valid),
        .command_ready(linear_engine_ready), .command_id(linear_engine_command_id),
        .block_index(linear_engine_block_index),
        .recurrence_index(linear_engine_recurrence_index),
        .matrix_rows(linear_engine_rows), .matrix_columns(linear_engine_columns),
        .tile_valid(tile_valid), .tile_ready(tile_ready), .tile_done(tile_done),
        .tile_command_id(tile_command_id), .tile_block_index(tile_block_index),
        .tile_recurrence_index(tile_recurrence_index), .tile_matrix_rows(tile_matrix_rows),
        .tile_matrix_columns(tile_matrix_columns), .matrix_window_count(matrix_window_count),
        .matrix_pool_words_per_port(matrix_pool_words_per_port),
        .tile_pool_base_per_port(tile_pool_base_per_port), .tile_index(tile_index),
        .tile_row_start(tile_row_start), .tile_active_rows(tile_active_rows),
        .command_done(tile_command_done), .protocol_error(tile_protocol_error)
    );

    assign linear_engine_done = tile_command_done;

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            operator_done <= 1'b0;
            operator_pending_q <= 1'b0;
            tile_done <= 1'b0;
            tile_pending_q <= 1'b0;
            tile_delay_q <= '0;
            expected_command_id_q <= '0;
            expected_block_index_q <= '0;
            expected_recurrence_index_q <= '0;
            expected_rows_q <= '0;
            expected_columns_q <= '0;
            expected_tile_index_q <= '0;
            command_total <= 0;
            linear_command_total <= 0;
            tile_total <= 0;
            max_pool_words <= 0;
            timeout_cycles <= 0;
        end else begin
            timeout_cycles <= timeout_cycles + 1;
            if (timeout_cycles > 5000000)
                $fatal(1, "full-core linear integration timeout model=%0d", MODEL_ID);
            operator_done <= 1'b0;
            tile_done <= 1'b0;

            if (command_valid && command_ready) begin
                command_total <= command_total + 1;
                if (linear_engine_valid) begin
                    linear_command_total <= linear_command_total + 1;
                    expected_command_id_q <= linear_engine_command_id;
                    expected_block_index_q <= linear_engine_block_index;
                    expected_recurrence_index_q <= linear_engine_recurrence_index;
                    expected_rows_q <= linear_engine_rows;
                    expected_columns_q <= linear_engine_columns;
                    expected_tile_index_q <= '0;
                end else begin
                    operator_pending_q <= 1'b1;
                end
            end

            if (operator_pending_q) begin
                operator_done <= 1'b1;
                operator_pending_q <= 1'b0;
            end

            if (tile_valid && tile_ready) begin
                tile_total <= tile_total + 1;
                tile_pending_q <= 1'b1;
                tile_delay_q <= 2'd1;
            end
            if (tile_pending_q) begin
                if (tile_delay_q != 0) begin
                    tile_delay_q <= tile_delay_q - 1'b1;
                end else begin
                    tile_done <= 1'b1;
                    tile_pending_q <= 1'b0;
                end
            end

            if (int'(matrix_pool_words_per_port) > max_pool_words)
                max_pool_words <= int'(matrix_pool_words_per_port);
            if (tile_command_done) begin
                if (int'(expected_tile_index_q) !=
                    ((int'(expected_rows_q) + 95) / 96))
                    $fatal(1, "matrix command completed before all tiles model=%0d rows=%0d tiles=%0d",
                           MODEL_ID, expected_rows_q, expected_tile_index_q);
                expected_tile_index_q <= '0;
            end else if (tile_valid && tile_ready) begin
                expected_tile_index_q <= expected_tile_index_q + 1'b1;
            end
        end
    end

    always @(negedge clk) begin
        integer expected_windows;
        integer expected_tiles;
        integer expected_words;
        integer expected_active_rows;
        if (rst_n && tile_valid) begin
            expected_windows = (int'(expected_columns_q) + 255) / 256;
            expected_tiles = (int'(expected_rows_q) + 95) / 96;
            expected_words = expected_tiles * expected_windows * 4;
            expected_active_rows = int'(expected_rows_q) - int'(tile_index) * 96;
            if (expected_active_rows > 96)
                expected_active_rows = 96;
            if (tile_command_id != expected_command_id_q ||
                tile_block_index != expected_block_index_q ||
                tile_recurrence_index != expected_recurrence_index_q ||
                tile_matrix_rows != expected_rows_q || tile_matrix_columns != expected_columns_q ||
                int'(matrix_window_count) != expected_windows ||
                int'(matrix_pool_words_per_port) != expected_words || expected_words > 16384 ||
                int'(tile_index) != int'(expected_tile_index_q) ||
                int'(tile_row_start) != int'(tile_index) * 96 ||
                int'(tile_active_rows) != expected_active_rows ||
                int'(tile_pool_base_per_port) != int'(tile_index) * expected_windows * 4)
                $fatal(1, "tile descriptor mismatch model=%0d command=%0d tile=%0d",
                       MODEL_ID, tile_command_id, tile_index);
        end
    end

    initial begin
        repeat (3) @(posedge clk);
        @(negedge clk);
        rst_n = 1'b1;
        context_tokens = 16'd512;
        start = 1'b1;
        @(posedge clk);
        #1 start = 1'b0;
        expected_commands = MODEL_ID == 0 ? 1696 : MODEL_ID == 1 ? 1444 : 1208;
        wait (core_done);
        @(negedge clk);
        if (core_error || tile_protocol_error || command_total != expected_commands ||
            linear_command_total == 0 || tile_total <= linear_command_total ||
            max_pool_words > 16384)
            $fatal(1, "full-core linear integration failed model=%0d commands=%0d linear=%0d tiles=%0d max_pool=%0d",
                   MODEL_ID, command_total, linear_command_total, tile_total, max_pool_words);
        $display("PASS: model=%0d full-core schedule commands=%0d linear_commands=%0d tiles=%0d max_pool_words=%0d",
                 MODEL_ID, command_total, linear_command_total, tile_total, max_pool_words);
        $finish;
    end
endmodule
