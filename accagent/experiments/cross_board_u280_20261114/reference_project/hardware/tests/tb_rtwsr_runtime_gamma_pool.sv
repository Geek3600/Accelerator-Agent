`timescale 1ns / 1ps

module tb_rtwsr_runtime_gamma_pool #(
    parameter bit PARALLEL_LOAD = 1'b0,
    parameter int CHANNELS = 96
);
    localparam int MAX_ROWS = 17920;
    logic clk = 1'b0;
    logic rst_n = 1'b0;
    logic load_abort = 1'b0;
    logic load_start = 1'b0;
    logic load_start_ready;
    logic [4:0] load_command_id = '0;
    logic [5:0] load_block_index = '0;
    logic [4:0] load_recurrence_index = '0;
    logic [15:0] load_matrix_rows = '0;
    logic [15:0] load_matrix_columns = '0;
    logic load_valid = 1'b0;
    logic load_ready;
    logic [31:0] load_pair_data = '0;
    logic [511:0] load_vector_data = '0;
    logic load_last = 1'b0;
    logic load_done;
    logic protocol_error;
    logic read_enable = 1'b0;
    logic [4:0] read_command_id = '0;
    logic [5:0] read_block_index = '0;
    logic [4:0] read_recurrence_index = '0;
    logic [15:0] read_matrix_rows = '0;
    logic [15:0] read_matrix_columns = '0;
    logic [8:0] read_tile_index = '0;
    logic release_enable = 1'b0;
    logic [8:0] release_tile_index = '0;
    logic read_match;
    logic read_valid;
    logic [CHANNELS*16-1:0] read_tile_data;
    integer huginn_tiles;
    integer dory_tiles;
    integer ouro_tiles;

    always #5 clk = ~clk;

    rtwsr_runtime_gamma_pool #(
        .MAX_ROWS(MAX_ROWS), .CHANNELS(CHANNELS), .PARALLEL_LOAD(PARALLEL_LOAD)
    ) dut (.*);

    function automatic logic [15:0] gamma_row(input integer seed, input integer row);
        gamma_row = 16'((seed * 7919 + row * 37 + (row >> 4)) & 16'hffff);
    endfunction

    function automatic logic [31:0] gamma_pair(input integer seed, input integer pair_index);
        gamma_pair = {gamma_row(seed, pair_index*2 + 1), gamma_row(seed, pair_index*2)};
    endfunction

    function automatic logic [CHANNELS*16-1:0] gamma_vector(
        input integer seed,
        input integer tile,
        input integer rows
    );
        logic [CHANNELS*16-1:0] value;
        begin
            value = '0;
            for (integer lane = 0; lane < CHANNELS; lane++)
                value[lane*16 +: 16] = tile*CHANNELS + lane < rows ?
                    gamma_row(seed, tile*CHANNELS + lane) : 16'd0;
            return value;
        end
    endfunction

    task automatic set_read_descriptor(
        input logic [4:0] command_id,
        input logic [5:0] block_id,
        input logic [4:0] recurrence_id,
        input logic [15:0] rows,
        input logic [15:0] columns
    );
        begin
            read_command_id = command_id;
            read_block_index = block_id;
            read_recurrence_index = recurrence_id;
            read_matrix_rows = rows;
            read_matrix_columns = columns;
        end
    endtask

    task automatic load_matrix(
        input logic [4:0] command_id,
        input logic [5:0] block_id,
        input logic [4:0] recurrence_id,
        input logic [15:0] rows,
        input logic [15:0] columns,
        input integer seed,
        input logic check_huginn_during_load
    );
        integer pairs, beats;
        begin
            pairs = (int'(rows) + 1) / 2;
            @(negedge clk);
            load_command_id = command_id;
            load_block_index = block_id;
            load_recurrence_index = recurrence_id;
            load_matrix_rows = rows;
            load_matrix_columns = columns;
            load_start = 1'b1;
            #1;
            if (!load_start_ready)
                $fatal(1, "Gamma load was not admitted for command %0d", command_id);
            @(posedge clk);
            @(negedge clk);
            load_start = 1'b0;
            load_valid = 1'b1;
            if (PARALLEL_LOAD) begin
                beats = (pairs + 15) / 16;
                for (integer beat = 0; beat < beats; beat++) begin
                    for (integer lane = 0; lane < 16; lane++) begin
                        if (beat*16 + lane < pairs)
                            load_vector_data[lane*32 +: 32] = gamma_pair(seed, beat*16 + lane);
                        else
                            load_vector_data[lane*32 +: 32] = '0;
                    end
                    load_last = beat == beats - 1;
                    @(posedge clk);
                    #1;
                    if (check_huginn_during_load &&
                        (!read_valid || read_tile_data !== gamma_vector(11, 0, MAX_ROWS)))
                        $fatal(1, "Huginn Gamma changed while command %0d was prefetched", command_id);
                    @(negedge clk);
                end
            end else begin
                for (integer pair_index = 0; pair_index < pairs; pair_index++) begin
                    load_pair_data = gamma_pair(seed, pair_index);
                    load_last = pair_index == pairs - 1;
                    @(posedge clk);
                    #1;
                    if (check_huginn_during_load &&
                        (!read_valid || read_tile_data !== gamma_vector(11, 0, MAX_ROWS)))
                        $fatal(1, "Huginn Gamma changed while command %0d was prefetched", command_id);
                    @(negedge clk);
                end
            end
            load_valid = 1'b0;
            load_last = 1'b0;
            if (!load_done || protocol_error)
                $fatal(1, "Gamma load failed command=%0d done=%b error=%b",
                       command_id, load_done, protocol_error);
        end
    endtask

    task automatic wait_for_tile(
        input integer tile,
        input integer seed,
        input integer rows
    );
        integer waited;
        begin
            read_tile_index = 9'(tile);
            read_enable = 1'b1;
            waited = 0;
            while (!read_valid && waited < CHANNELS/2 + 16) begin
                @(posedge clk);
                #1;
                waited = waited + 1;
            end
            if (!read_valid)
                $fatal(1, "Gamma tile was not ready tile=%0d waited=%0d", tile, waited);
            if (read_tile_data !== gamma_vector(seed, tile, rows)) begin
                for (integer lane = 0; lane < CHANNELS; lane++)
                    if (read_tile_data[lane*16 +: 16] !==
                        (tile*CHANNELS + lane < rows ? gamma_row(seed, tile*CHANNELS + lane) : 16'd0))
                        $fatal(1, "Gamma mismatch tile=%0d lane=%0d got=%h expected=%h waited=%0d",
                            tile, lane, read_tile_data[lane*16 +: 16],
                            tile*CHANNELS + lane < rows ? gamma_row(seed, tile*CHANNELS + lane) : 16'd0,
                            waited);
            end
        end
    endtask

    task automatic release_tile(input integer tile);
        begin
            @(negedge clk);
            release_tile_index = 9'(tile);
            release_enable = 1'b1;
            @(posedge clk);
            @(negedge clk);
            release_enable = 1'b0;
        end
    endtask

    task automatic check_matrix(
        input logic [4:0] command_id,
        input logic [5:0] block_id,
        input logic [4:0] recurrence_id,
        input logic [15:0] rows,
        input logic [15:0] columns,
        input integer seed
    );
        integer tiles;
        begin
            tiles = (int'(rows) + CHANNELS - 1) / CHANNELS;
            set_read_descriptor(command_id, block_id, recurrence_id, rows, columns);
            for (integer tile = 0; tile < tiles; tile++) begin
                wait_for_tile(tile, seed, int'(rows));
                repeat (51) @(posedge clk);
                release_tile(tile);
            end
            read_enable = 1'b0;
        end
    endtask

    initial begin
        huginn_tiles = (17920 + CHANNELS - 1) / CHANNELS;
        dory_tiles = (7168 + CHANNELS - 1) / CHANNELS;
        ouro_tiles = (5632 + CHANNELS - 1) / CHANNELS;
        repeat (3) @(negedge clk);
        rst_n = 1'b1;

        load_matrix(5'd8, 6'd3, 5'd31, 16'd17920, 16'd5280, 11, 1'b0);
        if (dut.gamma_bank_0[0][31:0] !== gamma_pair(11, 0) || !dut.bank_0_valid_q)
            $fatal(1, "Gamma row pairs were not written: got=%h expected=%h valid=%b",
                   dut.gamma_bank_0[0][31:0], gamma_pair(11, 0), dut.bank_0_valid_q);
        check_matrix(5'd8, 6'd3, 5'd31, 16'd17920, 16'd5280, 11);

        set_read_descriptor(5'd8, 6'd3, 5'd31, 16'd17920, 16'd5280);
        wait_for_tile(0, 11, 17920);
        load_matrix(5'd15, 6'd19, 5'd3, 16'd7168, 16'd2560, 23, 1'b1);
        release_tile(0);
        check_matrix(5'd15, 6'd19, 5'd3, 16'd7168, 16'd2560, 23);

        set_read_descriptor(5'd8, 6'd3, 5'd31, 16'd17920, 16'd5280);
        wait_for_tile(0, 11, 17920);
        load_matrix(5'd12, 6'd23, 5'd3, 16'd5632, 16'd2048, 31, 1'b1);
        release_tile(0);
        check_matrix(5'd12, 6'd23, 5'd3, 16'd5632, 16'd2048, 31);
        check_matrix(5'd8, 6'd3, 5'd31, 16'd17920, 16'd5280, 11);

        set_read_descriptor(5'd12, 6'd23, 5'd3, 16'd5632, 16'd2048);
        read_tile_index = 9'(ouro_tiles);
        read_enable = 1'b1;
        repeat (2) @(posedge clk);
        #1;
        if (read_valid)
            $fatal(1, "Gamma accepted an address beyond the descriptor tile count");
        @(negedge clk);
        read_enable = 1'b0;

        @(negedge clk);
        load_matrix_rows = 16'd17921;
        load_matrix_columns = 16'd5280;
        load_start = 1'b1;
        @(posedge clk);
        #1;
        if (!protocol_error || load_done)
            $fatal(1, "Gamma accepted a descriptor beyond its configured row capacity");
        @(negedge clk);
        load_start = 1'b0;

        $display("PASS: Gamma paired rows and prefetched Huginn %0d tiles, Dory %0d tiles, Ouro %0d tiles, parallel_load=%0d",
                 huginn_tiles, dory_tiles, ouro_tiles, PARALLEL_LOAD);
        $finish;
    end
endmodule
