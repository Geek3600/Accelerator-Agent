`timescale 1ns / 1ps

module tb_rtwsr_adapter_reuse_tile;
    logic clk = 0, rst_n = 0, invalidate = 0;
    logic tile_valid = 0, tile_ready;
    logic [8:0] tile_index = 0;
    integer block_index = 0;
    logic [5:0] adapter_block_index = 0;
    logic [6:0] activation_index;
    logic [2047:0] activation_window;
    logic pool_read_enable, pool_read_valid;
    logic [8:0] pool_tile;
    logic [6:0] pool_window;
    logic [1:0] pool_subword;
    logic [12287:0] pool_data;
    logic [2:0] pool_delay = '0;
    logic result_valid, tile_done, protocol_error;
    logic [3071:0] result_q12;
    logic [6:0] result_rows;
    integer round_index = 0;
    integer pool_reads = 0;
    integer expected_value;
    integer read_before;
    logic [511:0] word_value;

    always #5 clk = ~clk;
    always @(posedge clk) begin
        pool_delay <= {pool_delay[1:0], pool_read_enable};
        if (pool_read_enable)
            pool_reads <= pool_reads + 1;
        if (protocol_error)
            $fatal(1, "Adapter tile protocol error");
    end
    assign pool_read_valid = pool_delay[2];
    always_comb begin
        for (integer element = 0; element < 256; element++) begin
            integer column;
            column = int'(activation_index)*256 + element;
            activation_window[element*8 +: 8] = 8'((column*17 +
                (column < 5280 ? round_index*13 + block_index*11 : 5)) % 127 - 63);
        end
        for (integer lane = 0; lane < 24; lane++)
            pool_data[lane*512 +: 512] = word_value;
    end

    rtwsr_runtime_tile_gemv #(.ADAPTER_STATIC_REUSE(1'b1)) dut (
        .clk(clk), .rst_n(rst_n), .tile_valid(tile_valid), .tile_ready(tile_ready),
        .tile_index(tile_index), .tile_rows(7'd96), .matrix_columns(16'd10560),
        .tile_gamma_fp16({96{16'h3c00}}), .activation_scale_fp16(16'h3c00),
        .adapter_reuse(1'b1), .adapter_cache_invalidate(invalidate),
        .activation_ready(), .activation_valid(1'b1), .activation_window(activation_window),
        .activation_window_index(activation_index),
        .pool_read_enable(pool_read_enable), .pool_read_tile_index(pool_tile),
        .pool_read_window_index(pool_window), .pool_read_subword_index(pool_subword),
        .pool_read_valid(pool_read_valid), .pool_read_data(pool_data),
        .result_valid(result_valid), .result_ready(1'b1), .result_q12(result_q12),
        .result_rows(result_rows), .tile_done(tile_done), .protocol_error(protocol_error)
    );

    function automatic integer activation(input integer column, input integer round, input integer block);
        activation = (column*17 + (column < 5280 ? round*13 + block*11 : 5)) % 127 - 63;
    endfunction

    task automatic run_tile(input integer block, input integer tile, input integer expected_reads);
        @(negedge clk);
        while (!tile_ready) @(negedge clk);
        read_before = pool_reads;
        block_index = block;
        tile_index = 9'(tile);
        tile_valid = 1;
        @(negedge clk);
        tile_valid = 0;
        while (!result_valid) @(negedge clk);
        for (integer row = 0; row < 96; row++)
            if ($signed(result_q12[row*32 +: 32]) !== expected_value)
                $fatal(1, "tile=%0d round=%0d row=%0d result=%0d expected=%0d",
                    tile, round_index, row, $signed(result_q12[row*32 +: 32]), expected_value);
        if (pool_reads - read_before != expected_reads)
            $fatal(1, "tile=%0d round=%0d reads=%0d expected=%0d",
                tile, round_index, pool_reads - read_before, expected_reads);
        @(negedge clk);
    endtask

    initial begin
        word_value = '0;
        for (integer slot = 0; slot < 4; slot++) begin
            word_value[slot*24 +: 16] = slot[0] ? 16'hf000 : 16'h1000;
            word_value[slot*24+16 +: 8] = 8'(slot*70);
        end
        for (integer byte_index = 0; byte_index < 51; byte_index++)
            word_value[96+byte_index*8 +: 8] = 8'd242;
        word_value[504 +: 8] = 8'd2;
        repeat (3) @(negedge clk);
        rst_n = 1;
        for (round_index = 0; round_index < 32; round_index++) begin
            for (integer block = 0; block < 4; block++) begin
                expected_value = 0;
                for (integer column = 0; column < 10560; column++)
                    expected_value += activation(column, round_index, block) * 4096;
                for (integer window = 0; window < 42; window++)
                    for (integer slot = 0; slot < 4; slot++)
                        if (window*256 + slot*70 < 10560)
                            expected_value += activation(window*256 + slot*70, round_index, block) *
                                (slot[0] ? -4096 : 4096);
                for (integer tile = 0; tile < 55; tile++)
                    run_tile(block, tile, round_index == 0 && block == 0 ? 172 : 84);
            end
        end
        @(negedge clk);
        invalidate = 1;
        @(negedge clk);
        invalidate = 0;
        round_index = 0;
        block_index = 0;
        expected_value = 0;
        for (integer column = 0; column < 10560; column++)
            expected_value += activation(column, round_index, 0) * 4096;
        for (integer window = 0; window < 42; window++)
            for (integer slot = 0; slot < 4; slot++)
                if (window*256 + slot*70 < 10560)
                    expected_value += activation(window*256 + slot*70, round_index, 0) *
                        (slot[0] ? -4096 : 4096);
        run_tile(0, 0, 172);
        $display("PASS Adapter tile reuse 4 blocks 5280x10560 55 tiles 32 rounds pool_reads=%0d", pool_reads);
        $finish;
    end

    initial begin
        #100000000;
        $fatal(1, "Adapter tile reuse timeout");
    end
endmodule
