`timescale 1ns / 1ps

// Full Huginn operator payload and a second streamed operator pass.
module tb_uram_shadow_ring #(
    parameter int DEPTH = 73728,
    parameter int TILE_SLOTS = 165,
    parameter int WINDOW_COUNT = 70,
    parameter int WORDS_PER_WINDOW = 4
);
    localparam int TILE_RECORDS = WINDOW_COUNT * WORDS_PER_WINDOW;
    localparam int TILE_WIDTH = (TILE_SLOTS <= 1) ? 1 : $clog2(TILE_SLOTS);
    localparam int WINDOW_WIDTH = (WINDOW_COUNT <= 1) ? 1 : $clog2(WINDOW_COUNT);
    localparam int WORD_WIDTH = (WORDS_PER_WINDOW <= 1) ? 1 : $clog2(WORDS_PER_WINDOW);

    logic clk = 1'b0;
    logic rst_n = 1'b0;
    logic push_valid = 1'b0;
    logic push_ready;
    logic [TILE_WIDTH-1:0] push_tile = '0;
    logic [WINDOW_WIDTH-1:0] push_window = '0;
    logic [WORD_WIDTH-1:0] push_word = '0;
    logic push_tile_last = 1'b0;
    logic [511:0] push_data = '0;
    logic out_valid;
    logic out_ready = 1'b0;
    logic [TILE_WIDTH-1:0] out_tile;
    logic [WINDOW_WIDTH-1:0] out_window;
    logic [WORD_WIDTH-1:0] out_word;
    logic out_tile_last;
    logic [511:0] out_data;
    logic [TILE_SLOTS-1:0] tile_complete;
    logic protocol_error;
    logic [$clog2(DEPTH+1)-1:0] occupancy;
    integer received = 0;
    integer cycle = 0;
    integer backpressure_cycles = 0;
    logic consume_enabled = 1'b0;

    always #1 clk = ~clk;
    always @(negedge clk) begin
        if (consume_enabled)
            out_ready = ((cycle % 11) != 0) && ((cycle % 17) != 0);
        else
            out_ready = 1'b0;
    end

    always @(posedge clk) begin
        cycle <= cycle + 1;
        if (out_valid && out_ready) begin
            if (out_data !== 512'(out_tile * TILE_RECORDS +
                                  out_window * WORDS_PER_WINDOW + out_word))
                $fatal(1, "data order mismatch tile=%0d window=%0d word=%0d",
                       out_tile, out_window, out_word);
            if (out_tile_last !== (out_window == WINDOW_COUNT - 1 &&
                                   out_word == WORDS_PER_WINDOW - 1))
                $fatal(1, "tile last marker mismatch");
            received <= received + 1;
        end
        if (consume_enabled && out_valid && !out_ready)
            backpressure_cycles <= backpressure_cycles + 1;
    end

    uram_shadow_ring #(
        .DEPTH(DEPTH),
        .TILE_SLOTS(TILE_SLOTS),
        .WINDOW_COUNT(WINDOW_COUNT),
        .WORDS_PER_WINDOW(WORDS_PER_WINDOW)
    ) dut (
        .clk(clk), .rst_n(rst_n),
        .push_valid(push_valid), .push_ready(push_ready),
        .push_tile(push_tile), .push_window(push_window), .push_word(push_word),
        .push_tile_last(push_tile_last), .push_data(push_data),
        .out_valid(out_valid), .out_ready(out_ready),
        .out_tile(out_tile), .out_window(out_window), .out_word(out_word),
        .out_tile_last(out_tile_last), .out_data(out_data),
        .tile_complete(tile_complete), .protocol_error(protocol_error),
        .occupancy(occupancy)
    );

    task automatic push_record(input integer tile, input integer window,
                               input integer word, input logic last);
        begin
            @(negedge clk);
            push_valid = 1'b1;
            push_tile = TILE_WIDTH'(tile);
            push_window = WINDOW_WIDTH'(window);
            push_word = WORD_WIDTH'(word);
            push_tile_last = last;
            push_data = 512'(tile * TILE_RECORDS + window * WORDS_PER_WINDOW + word);
            do @(posedge clk); while (!push_ready);
        end
    endtask

    initial begin
        repeat (4) @(posedge clk);
        @(negedge clk);
        rst_n = 1'b1;
        // Fill one complete Huginn operator payload without a consumer.
        for (integer tile = 0; tile < TILE_SLOTS; tile = tile + 1) begin
            for (integer window = 0; window < WINDOW_COUNT; window = window + 1) begin
                for (integer word = 0; word < WORDS_PER_WINDOW; word = word + 1) begin
                    push_record(tile, window, word,
                                window == WINDOW_COUNT - 1 &&
                                word == WORDS_PER_WINDOW - 1);
                    if (tile == 0 && window == 0 && word == 0) begin
                        @(negedge clk);
                        push_valid = 1'b0;
                        if (out_valid)
                            $fatal(1, "incomplete tile became visible");
                    end
                end
            end
            @(negedge clk);
            push_valid = 1'b0;
            if (!tile_complete[tile])
                $fatal(1, "tile %0d did not become complete", tile);
        end
        if (occupancy != TILE_SLOTS * TILE_RECORDS)
            $fatal(1, "operator payload occupancy mismatch: %0d", occupancy);
        if (push_ready)
            $fatal(1, "producer advanced while all destination tiles were complete");
        if (!out_valid || out_data !== 512'(0))
            $fatal(1, "complete head tile was not presented in order");
        repeat (5) begin
            @(posedge clk);
            if (!out_valid || out_data !== 512'(0) || out_tile != 0 ||
                out_window != 0 || out_word != 0 || out_tile_last)
                $fatal(1, "output changed while consumer backpressure was asserted");
        end

        // Refill released tile IDs while draining, then cross the physical
        // ring boundary with more than one DEPTH of total streamed records.
        consume_enabled = 1'b1;
        for (integer tile = 0; tile < TILE_SLOTS; tile = tile + 1) begin
            for (integer window = 0; window < WINDOW_COUNT; window = window + 1) begin
                for (integer word = 0; word < WORDS_PER_WINDOW; word = word + 1)
                    push_record(tile, window, word,
                                window == WINDOW_COUNT - 1 &&
                                word == WORDS_PER_WINDOW - 1);
            end
        end
        @(negedge clk);
        push_valid = 1'b0;
        while (received < 2 * TILE_SLOTS * TILE_RECORDS) @(negedge clk);
        repeat (3) @(posedge clk);
        consume_enabled = 1'b0;
        if (protocol_error || occupancy != 0 ||
            received != 2 * TILE_SLOTS * TILE_RECORDS)
            $fatal(1, "streamed operator drain state mismatch");
        $display("PASS: complete configured tile set staged (%0d records, %0d bytes)",
                 TILE_SLOTS * TILE_RECORDS, TILE_SLOTS * TILE_RECORDS * 64);
        $display("PASS: completion gating, output backpressure, and tile refill held in order");
        $display("PASS: %0d streamed records crossed the %0d-entry ring boundary", received, DEPTH);
        $display("PASS: %0d consumer backpressure cycles", backpressure_cycles);
        $finish;
    end
endmodule
