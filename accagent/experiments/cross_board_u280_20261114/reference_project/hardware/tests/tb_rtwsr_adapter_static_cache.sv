`timescale 1ns / 1ps

module tb_rtwsr_adapter_static_cache;
    parameter int HIDDEN_SIZE = 5280;
    parameter int CHANNELS = 96;
    localparam int SUM_WIDTH = 37;
    localparam int TILES = (HIDDEN_SIZE + CHANNELS - 1) / CHANNELS;
    localparam int TILE_WIDTH = (TILES <= 1) ? 1 : $clog2(TILES);
    logic clk = 0, rst_n = 0, invalidate = 0;
    logic [6:0] window_index;
    logic [2047:0] activation_window, state_window, embedding_window;
    logic write_enable = 0, read_enable = 0;
    logic [TILE_WIDTH-1:0] write_tile, read_tile;
    logic [CHANNELS*SUM_WIDTH-1:0] write_sum, read_sum;
    logic tile_valid, read_valid, protocol_error;

    always #5 clk = ~clk;

    rtwsr_adapter_static_cache u_cache (.*);

    function automatic logic [SUM_WIDTH-1:0] expected_sum(input integer tile, input integer row);
        expected_sum = SUM_WIDTH'((tile*CHANNELS + row)*7919 - 20000000);
    endfunction

    initial begin
        repeat (2) @(negedge clk);
        rst_n = 1;
        for (integer window = 0; window < 42; window++) begin
            window_index = 7'(window);
            for (integer byte_index = 0; byte_index < 256; byte_index++)
                activation_window[byte_index*8 +: 8] = 8'(byte_index + 1);
            #1;
            for (integer byte_index = 0; byte_index < 256; byte_index++) begin
                if (state_window[byte_index*8 +: 8] !==
                    (window*256 + byte_index < HIDDEN_SIZE ? 8'(byte_index + 1) : 8'd0) ||
                    embedding_window[byte_index*8 +: 8] !==
                    (window*256 + byte_index >= HIDDEN_SIZE &&
                     window*256 + byte_index < 2*HIDDEN_SIZE ? 8'(byte_index + 1) : 8'd0))
                    $fatal(1, "window split mismatch window=%0d byte=%0d", window, byte_index);
            end
        end
        for (integer tile = 0; tile < TILES; tile++) begin
            @(negedge clk);
            write_enable = 1;
            write_tile = $bits(write_tile)'(tile);
            for (integer row = 0; row < CHANNELS; row++)
                write_sum[row*SUM_WIDTH +: SUM_WIDTH] = expected_sum(tile, row);
        end
        @(negedge clk);
        write_enable = 0;
        for (integer round = 1; round < 32; round++)
            for (integer block = 0; block < 4; block++)
                for (integer tile = 0; tile < TILES; tile++) begin
                    read_enable = 1;
                    read_tile = $bits(read_tile)'(tile);
                    @(negedge clk);
                    if (!read_valid)
                        $fatal(1, "cache read invalid round=%0d block=%0d tile=%0d", round, block, tile);
                    for (integer row = 0; row < CHANNELS; row++)
                        if (read_sum[row*SUM_WIDTH +: SUM_WIDTH] !== expected_sum(tile, row))
                            $fatal(1, "cache mismatch round=%0d block=%0d tile=%0d row=%0d", round, block, tile, row);
                end
        read_enable = 0;
        invalidate = 1;
        @(negedge clk);
        invalidate = 0;
        read_tile = 0;
        read_enable = 1;
        @(negedge clk);
        if (read_valid || !protocol_error)
            $fatal(1, "invalidated cache returned data");
        $display("PASS Adapter cache hidden=%0d channels=%0d tiles=%0d rounds=32 windows=42 boundary=20:160",
            HIDDEN_SIZE, CHANNELS, TILES);
        $finish;
    end
endmodule
