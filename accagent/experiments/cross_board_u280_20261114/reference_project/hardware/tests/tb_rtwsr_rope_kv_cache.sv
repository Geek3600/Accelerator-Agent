`timescale 1ns / 1ps

module tb_rtwsr_rope_kv_cache #(
    parameter int HEAD_DIM = 128,
    parameter int MAX_CONTEXT = 2048,
    parameter int LANES = 128,
    parameter int DATA_W = 16,
    parameter int TRIG_W = 16,
    parameter int TOKEN_INDEX_W = $clog2(MAX_CONTEXT),
    parameter int CONTEXT_COUNT_W = $clog2(MAX_CONTEXT + 1),
    parameter int CHUNK_COUNT = (HEAD_DIM + LANES - 1) / LANES,
    parameter int CHUNK_INDEX_W = (CHUNK_COUNT <= 1) ? 1 : $clog2(CHUNK_COUNT),
    parameter int VECTOR_WIDTH = HEAD_DIM * DATA_W,
    parameter int TRIG_VECTOR_WIDTH = HEAD_DIM * TRIG_W,
    parameter int CHUNK_WIDTH = LANES * DATA_W
);
    logic clk = 1'b0;
    logic rst_n = 1'b0;
    logic start = 1'b0;
    logic [TOKEN_INDEX_W-1:0] write_position = '0;
    logic [CONTEXT_COUNT_W-1:0] active_context_tokens = '0;
    logic [TOKEN_INDEX_W-1:0] window_start = '0;
    logic [VECTOR_WIDTH-1:0] query_q4_12 = '0;
    logic [VECTOR_WIDTH-1:0] key_q4_12 = '0;
    logic [VECTOR_WIDTH-1:0] value_q4_12 = '0;
    logic [TRIG_VECTOR_WIDTH-1:0] rope_sin_q1_15 = '0;
    logic [TRIG_VECTOR_WIDTH-1:0] rope_cos_q1_15 = '0;
    logic ready;
    logic query_valid;
    logic [VECTOR_WIDTH-1:0] query_rotated_q4_12;
    logic kv_ready = 1'b1;
    logic kv_valid;
    logic [TOKEN_INDEX_W-1:0] kv_token_index;
    logic [CHUNK_INDEX_W-1:0] kv_chunk_index;
    logic [CHUNK_WIDTH-1:0] kv_key_chunk_q4_12;
    logic [CHUNK_WIDTH-1:0] kv_value_chunk_q4_12;
    logic kv_last;
    logic cache_load_ready;
    logic cache_load_valid = 1'b0;
    logic [TOKEN_INDEX_W-1:0] cache_load_index = '0;
    logic [VECTOR_WIDTH-1:0] cache_load_key_q4_12 = '0;
    logic [VECTOR_WIDTH-1:0] cache_load_value_q4_12 = '0;
    logic busy;
    logic done;
    logic protocol_error;
    integer context_length;
    integer dimension;
    integer token;
    integer chunk;
    integer lane;
    integer expected_token;
    integer expected_chunk;
    integer query_seen;
    integer output_count;
    integer wait_cycles;

    always #5 clk = ~clk;

    rtwsr_rope_kv_cache #(
        .HEAD_DIM(HEAD_DIM),
        .MAX_CONTEXT(MAX_CONTEXT),
        .LANES(LANES)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .start(start),
        .write_position(write_position),
        .active_context_tokens(active_context_tokens),
        .window_start(window_start),
        .query_q4_12(query_q4_12),
        .key_q4_12(key_q4_12),
        .value_q4_12(value_q4_12),
        .rope_sin_q1_15(rope_sin_q1_15),
        .rope_cos_q1_15(rope_cos_q1_15),
        .ready(ready),
        .query_valid(query_valid),
        .query_rotated_q4_12(query_rotated_q4_12),
        .kv_ready(kv_ready),
        .kv_valid(kv_valid),
        .kv_token_index(kv_token_index),
        .kv_chunk_index(kv_chunk_index),
        .kv_key_chunk_q4_12(kv_key_chunk_q4_12),
        .kv_value_chunk_q4_12(kv_value_chunk_q4_12),
        .kv_last(kv_last),
        .cache_load_ready(cache_load_ready),
        .cache_load_valid(cache_load_valid),
        .cache_load_index(cache_load_index),
        .cache_load_key_q4_12(cache_load_key_q4_12),
        .cache_load_value_q4_12(cache_load_value_q4_12),
        .busy(busy),
        .done(done),
        .protocol_error(protocol_error)
    );

    function automatic logic signed [15:0] raw_query(input integer value_index);
        raw_query = 16'((((value_index * 41 + 9) % 251) - 125) * 8);
    endfunction

    function automatic logic signed [15:0] raw_key(input integer value_index);
        raw_key = 16'((((value_index * 17 + 21) % 211) - 105) * 9);
    endfunction

    function automatic logic signed [15:0] cache_key(input integer cache_token, input integer value_index);
        cache_key = 16'((((cache_token * 31 + value_index * 19 + 3) % 257) - 128) * 7);
    endfunction

    function automatic logic signed [15:0] cache_value(input integer cache_token, input integer value_index);
        cache_value = 16'((((cache_token * 13 + value_index * 29 + 5) % 401) - 200) * 6);
    endfunction

    function automatic logic signed [15:0] trig_sin(input integer value_index);
        trig_sin = 16'(((value_index * 997 + 123) % 8001) - 4000);
    endfunction

    function automatic logic signed [15:0] trig_cos(input integer value_index);
        trig_cos = 16'(30000 - (value_index % 7) * 257);
    endfunction

    function automatic logic signed [15:0] rotate_expected(
        input logic signed [15:0] value,
        input logic signed [15:0] paired,
        input logic signed [15:0] cosine,
        input logic signed [15:0] sine,
        input logic first_half
    );
        integer product;
        begin
            if (first_half)
                product = value * cosine - paired * sine;
            else
                product = value * cosine + paired * sine;
            if ((product >>> 15) > 32767)
                rotate_expected = 16'sd32767;
            else if ((product >>> 15) < -32768)
                rotate_expected = -16'sd32768;
            else
                rotate_expected = product >>> 15;
        end
    endfunction

    task automatic preload_cache;
        begin
            for (token = 0; token < context_length; token = token + 1) begin
                @(negedge clk);
                cache_load_index = TOKEN_INDEX_W'(token);
                cache_load_key_q4_12 = '0;
                cache_load_value_q4_12 = '0;
                for (dimension = 0; dimension < HEAD_DIM; dimension = dimension + 1) begin
                    cache_load_key_q4_12[dimension*DATA_W +: DATA_W] = cache_key(token, dimension);
                    cache_load_value_q4_12[dimension*DATA_W +: DATA_W] = cache_value(token, dimension);
                end
                cache_load_valid = 1'b1;
                if (!cache_load_ready)
                    $fatal(1, "cache preload was not ready at token %0d", token);
                @(posedge clk);
                @(negedge clk);
            end
            cache_load_valid = 1'b0;
        end
    endtask

    task automatic run_case;
        logic signed [15:0] expected;
        logic signed [15:0] pair;
        integer output_dimension;
        begin
            preload_cache();
            @(negedge clk);
            write_position = TOKEN_INDEX_W'(context_length - 1);
            active_context_tokens = CONTEXT_COUNT_W'(context_length);
            window_start = '0;
            query_q4_12 = '0;
            key_q4_12 = '0;
            value_q4_12 = '0;
            rope_sin_q1_15 = '0;
            rope_cos_q1_15 = '0;
            for (dimension = 0; dimension < HEAD_DIM; dimension = dimension + 1) begin
                query_q4_12[dimension*DATA_W +: DATA_W] = raw_query(dimension);
                key_q4_12[dimension*DATA_W +: DATA_W] = raw_key(dimension);
                value_q4_12[dimension*DATA_W +: DATA_W] = cache_value(context_length - 1, dimension);
                rope_sin_q1_15[dimension*TRIG_W +: TRIG_W] = trig_sin(dimension);
                rope_cos_q1_15[dimension*TRIG_W +: TRIG_W] = trig_cos(dimension);
            end
            start = 1'b1;
            @(posedge clk);
            @(negedge clk);
            start = 1'b0;

            query_seen = 0;
            output_count = 0;
            expected_token = 0;
            expected_chunk = 0;
            wait_cycles = 0;
            if (query_valid) begin
                for (dimension = 0; dimension < HEAD_DIM; dimension = dimension + 1) begin
                    pair = raw_query((dimension < HEAD_DIM/2) ? dimension + HEAD_DIM/2 : dimension - HEAD_DIM/2);
                    expected = rotate_expected(raw_query(dimension), pair, trig_cos(dimension), trig_sin(dimension), dimension < HEAD_DIM/2);
                    if ($signed(query_rotated_q4_12[dimension*DATA_W +: DATA_W]) !== expected)
                        $fatal(1, "RoPE query mismatch dimension %0d: got %0d expected %0d", dimension,
                            $signed(query_rotated_q4_12[dimension*DATA_W +: DATA_W]), expected);
                end
                query_seen = 1;
            end
            while (!done && wait_cycles < context_length * (CHUNK_COUNT + 3) + 32) begin
                @(negedge clk);
                if (query_valid) begin
                    if (query_seen != 0)
                        $fatal(1, "query was emitted more than once");
                    for (dimension = 0; dimension < HEAD_DIM; dimension = dimension + 1) begin
                        pair = raw_query((dimension < HEAD_DIM/2) ? dimension + HEAD_DIM/2 : dimension - HEAD_DIM/2);
                        expected = rotate_expected(raw_query(dimension), pair, trig_cos(dimension), trig_sin(dimension), dimension < HEAD_DIM/2);
                        if ($signed(query_rotated_q4_12[dimension*DATA_W +: DATA_W]) !== expected)
                            $fatal(1, "RoPE query mismatch dimension %0d: got %0d expected %0d", dimension,
                                $signed(query_rotated_q4_12[dimension*DATA_W +: DATA_W]), expected);
                    end
                    query_seen = 1;
                end
                if (kv_valid) begin
                    if (kv_token_index != expected_token || kv_chunk_index != expected_chunk)
                        $fatal(1, "KV index mismatch: got token %0d chunk %0d expected token %0d chunk %0d",
                            kv_token_index, kv_chunk_index, expected_token, expected_chunk);
                    for (lane = 0; lane < LANES; lane = lane + 1) begin
                        output_dimension = expected_chunk * LANES + lane;
                        if (output_dimension < HEAD_DIM) begin
                            if (expected_token == context_length - 1) begin
                                pair = raw_key((output_dimension < HEAD_DIM/2) ?
                                    output_dimension + HEAD_DIM/2 : output_dimension - HEAD_DIM/2);
                                expected = rotate_expected(
                                    raw_key(output_dimension), pair, trig_cos(output_dimension),
                                    trig_sin(output_dimension), output_dimension < HEAD_DIM/2
                                );
                            end else begin
                                expected = cache_key(expected_token, output_dimension);
                            end
                            if ($signed(kv_key_chunk_q4_12[lane*DATA_W +: DATA_W]) !== expected)
                                $fatal(1, "KV key mismatch token %0d dimension %0d", expected_token, output_dimension);
                            expected = cache_value(expected_token, output_dimension);
                            if ($signed(kv_value_chunk_q4_12[lane*DATA_W +: DATA_W]) !== expected)
                                $fatal(1, "KV value mismatch token %0d dimension %0d", expected_token, output_dimension);
                        end
                    end
                    if (kv_last !== (expected_token == context_length-1 && expected_chunk == CHUNK_COUNT-1))
                        $fatal(1, "KV last mismatch at token %0d chunk %0d", expected_token, expected_chunk);
                    output_count = output_count + 1;
                    if (expected_chunk == CHUNK_COUNT-1) begin
                        expected_token = expected_token + 1;
                        expected_chunk = 0;
                    end else begin
                        expected_chunk = expected_chunk + 1;
                    end
                end
                @(posedge clk);
                #1;
                wait_cycles = wait_cycles + 1;
            end
            if (!done || query_seen != 1 || output_count != context_length * CHUNK_COUNT)
                $fatal(1, "RoPE/KV run incomplete: done=%b query=%0d output=%0d expected=%0d",
                    done, query_seen, output_count, context_length * CHUNK_COUNT);
            if (protocol_error)
                $fatal(1, "RoPE/KV run reported protocol error");
        end
    endtask

    initial begin
        context_length = MAX_CONTEXT == 2048 ? 2048 : 512;
        repeat (3) @(posedge clk);
        @(negedge clk);
        rst_n = 1'b1;
        wait (ready);
        run_case();
        $display("PASS: RoPE/KV cache HEAD_DIM=%0d context=%0d, %0d chunks", HEAD_DIM, context_length, CHUNK_COUNT);
        $finish;
    end
endmodule
