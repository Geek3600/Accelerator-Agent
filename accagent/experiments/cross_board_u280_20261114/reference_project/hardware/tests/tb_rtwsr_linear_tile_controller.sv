`timescale 1ns / 1ps

module tb_rtwsr_linear_tile_controller #(
    parameter int CHANNELS = 96,
    parameter int ROW_COUNT_WIDTH = (CHANNELS <= 127) ? 7 : 8
);
    logic clk = 1'b0;
    logic rst_n = 1'b0;
    logic command_valid = 1'b0;
    logic command_ready;
    logic [4:0] command_id = '0;
    logic [5:0] block_index = '0;
    logic [4:0] recurrence_index = '0;
    logic [15:0] matrix_rows = '0;
    logic [15:0] matrix_columns = '0;
    logic tile_valid;
    logic tile_ready = 1'b0;
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
    logic [ROW_COUNT_WIDTH-1:0] tile_active_rows;
    logic command_done;
    logic protocol_error;

    always #5 clk = ~clk;

    rtwsr_linear_tile_controller #(
        .CHANNELS(CHANNELS), .ROW_COUNT_WIDTH(ROW_COUNT_WIDTH), .TILE_INDEX_WIDTH(9)
    ) dut (.*);

    task automatic run_matrix(
        input logic [4:0] id,
        input integer rows,
        input integer columns,
        input integer expected_block,
        input integer expected_recurrence
    );
        integer tiles;
        integer index;
        integer row_start;
        integer active_rows;
        integer expected_windows;
        integer expected_pool_words;
        begin
            tiles = (rows + CHANNELS - 1) / CHANNELS;
            expected_windows = (columns + 255) / 256;
            expected_pool_words = tiles * expected_windows * 4;
            if (expected_pool_words > 16384)
                $fatal(1, "test matrix exceeds the configured per-port pool depth");
            @(negedge clk);
            command_id = id;
            block_index = 6'(expected_block);
            recurrence_index = 5'(expected_recurrence);
            matrix_rows = 16'(rows);
            matrix_columns = 16'(columns);
            command_valid = 1'b1;
            if (!command_ready)
                $fatal(1, "linear engine accepted a new matrix while busy");
            @(posedge clk);
            #1 command_valid = 1'b0;

            for (index = 0; index < tiles; index = index + 1) begin
                row_start = index * CHANNELS;
                active_rows = rows - row_start;
                if (active_rows > CHANNELS)
                    active_rows = CHANNELS;
                wait (tile_valid);
                @(negedge clk);
                if (tile_command_id != id || tile_block_index != expected_block ||
                    tile_recurrence_index != expected_recurrence ||
                    tile_matrix_rows != rows || tile_matrix_columns != columns ||
                    matrix_window_count != expected_windows ||
                    matrix_pool_words_per_port != expected_pool_words ||
                    tile_pool_base_per_port != index * expected_windows * 4 ||
                    tile_index != index || tile_row_start != row_start ||
                    tile_active_rows != active_rows || command_ready)
                    $fatal(1, "tile descriptor mismatch id=%0d tile=%0d start=%0d active=%0d",
                           id, tile_index, tile_row_start, tile_active_rows);
                tile_ready = 1'b1;
                @(posedge clk);
                #1 tile_ready = 1'b0;
                repeat (2) @(posedge clk);
                #1 tile_done = 1'b1;
                @(posedge clk);
                #1 begin
                    tile_done = 1'b0;
                    if (command_done != (index == tiles - 1))
                        $fatal(1, "matrix completion mismatch id=%0d tile=%0d", id, index);
                end
            end
            if (protocol_error)
                $fatal(1, "valid matrix descriptor raised protocol_error");
        end
    endtask

    initial begin
        repeat (2) @(posedge clk);
        @(negedge clk);
        rst_n = 1'b1;
        run_matrix(5'd0, 5280, 10560, 0, 0);
        run_matrix(5'd3, 15840, 5280, 0, 1);
        run_matrix(5'd9, 5280, 5280, 0, 0);
        run_matrix(5'd21, 17920, 5280, 0, 0);
        run_matrix(5'd22, 17920, 5280, 0, 0);
        run_matrix(5'd15, 5280, 17920, 0, 0);
        run_matrix(5'd18, 2048, 2048, 0, 0);
        run_matrix(5'd19, 2048, 2048, 0, 0);
        run_matrix(5'd20, 2048, 2048, 0, 0);
        run_matrix(5'd9, 2048, 2048, 0, 0);
        run_matrix(5'd21, 5632, 2048, 0, 0);
        run_matrix(5'd22, 5632, 2048, 0, 0);
        run_matrix(5'd15, 2048, 5632, 0, 0);
        run_matrix(5'd18, 4096, 2560, 0, 0);
        run_matrix(5'd19, 1024, 2560, 0, 0);
        run_matrix(5'd20, 1024, 2560, 0, 0);
        run_matrix(5'd4, 4096, 2560, 0, 0);
        run_matrix(5'd9, 2560, 4096, 0, 0);
        run_matrix(5'd21, 7168, 2560, 0, 0);
        run_matrix(5'd22, 7168, 2560, 0, 0);
        run_matrix(5'd15, 2560, 7168, 0, 0);

        @(negedge clk);
        matrix_rows = 0;
        matrix_columns = 16'd2048;
        command_valid = 1'b1;
        @(posedge clk);
        #1 command_valid = 1'b0;
        if (!command_done || !protocol_error)
            $fatal(1, "empty matrix descriptor must terminate with a protocol error");

        @(negedge clk);
        matrix_rows = 16'd17920;
        matrix_columns = 16'd17920;
        command_valid = 1'b1;
        @(posedge clk);
        #1 command_valid = 1'b0;
        if (!command_done || !protocol_error)
            $fatal(1, "matrix exceeding the primary pool must be rejected");

        $display("PASS: shared %0d-channel matrix tiling covers all Plan 6 model dimensions", CHANNELS);
        $finish;
    end
endmodule
