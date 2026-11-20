`timescale 1ns / 1ps

module tb_rtwsr_external_kv_stream;
    localparam int HEAD_DIM = 128;
    localparam int VECTOR_WIDTH = HEAD_DIM * 16;

    logic clk = 0, rst_n = 0, start = 0;
    logic [10:0] write_position = 1, window_start = 0;
    logic [11:0] active_context_tokens = 2;
    logic [VECTOR_WIDTH-1:0] query_q4_12, key_q4_12, value_q4_12;
    logic [VECTOR_WIDTH-1:0] rope_sin_q1_15, rope_cos_q1_15;
    logic ready, query_valid, kv_valid, kv_ready = 1, kv_last;
    logic [VECTOR_WIDTH-1:0] query_rotated;
    logic [10:0] kv_token_index;
    logic [0:0] kv_chunk_index;
    logic [2047:0] kv_key_chunk, kv_value_chunk;
    logic cache_load_ready, cache_load_valid = 0;
    logic [10:0] cache_load_index = 0;
    logic [VECTOR_WIDTH-1:0] cache_load_key, cache_load_value;
    logic cache_read_request, cache_read_request_ready = 1;
    logic [10:0] cache_read_index;
    logic busy, done, protocol_error;
    integer requests = 0, chunks = 0, cycles = 0;

    always #5 clk = ~clk;

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            cache_load_valid <= 1'b0;
            requests <= 0;
            chunks <= 0;
            cycles <= 0;
        end else begin
            cycles <= cycles + 1;
            if (cycles > 100)
                $fatal(1, "external KV stream timed out");
            cache_load_valid <= cache_read_request && cache_read_request_ready;
            if (cache_read_request && cache_read_request_ready) begin
                cache_load_index <= cache_read_index;
                requests <= requests + 1;
            end
            if (kv_valid && kv_ready) begin
                if (chunks == 0) begin
                    if (kv_token_index != 0 || kv_last || $signed(kv_key_chunk[15:0]) != 77 ||
                        $signed(kv_value_chunk[15:0]) != 88)
                        $fatal(1, "external KV response mismatch token=%0d key=%0d value=%0d",
                               kv_token_index, $signed(kv_key_chunk[15:0]),
                               $signed(kv_value_chunk[15:0]));
                end else if (kv_token_index != 1 || !kv_last ||
                             $signed(kv_key_chunk[15:0]) != 199 ||
                             $signed(kv_value_chunk[15:0]) != 300) begin
                    $fatal(1, "current KV mismatch token=%0d key=%0d value=%0d",
                           kv_token_index, $signed(kv_key_chunk[15:0]),
                           $signed(kv_value_chunk[15:0]));
                end
                chunks <= chunks + 1;
            end
        end
    end

    rtwsr_rope_kv_cache #(
        .HEAD_DIM(HEAD_DIM), .MAX_CONTEXT(2048), .EXTERNAL_CACHE(1'b1)
    ) dut (
        .clk(clk), .rst_n(rst_n), .start(start), .write_position(write_position),
        .active_context_tokens(active_context_tokens), .window_start(window_start),
        .query_q4_12(query_q4_12), .key_q4_12(key_q4_12), .value_q4_12(value_q4_12),
        .rope_sin_q1_15(rope_sin_q1_15), .rope_cos_q1_15(rope_cos_q1_15),
        .ready(ready), .query_valid(query_valid), .query_rotated_q4_12(query_rotated),
        .kv_ready(kv_ready), .kv_valid(kv_valid), .kv_token_index(kv_token_index),
        .kv_chunk_index(kv_chunk_index), .kv_key_chunk_q4_12(kv_key_chunk),
        .kv_value_chunk_q4_12(kv_value_chunk), .kv_last(kv_last),
        .cache_load_ready(cache_load_ready), .cache_load_valid(cache_load_valid),
        .cache_load_index(cache_load_index), .cache_load_key_q4_12(cache_load_key),
        .cache_load_value_q4_12(cache_load_value), .cache_read_request(cache_read_request),
        .cache_read_request_ready(cache_read_request_ready), .cache_read_index(cache_read_index),
        .busy(busy), .done(done), .protocol_error(protocol_error)
    );

    initial begin
        query_q4_12 = {HEAD_DIM{16'd50}};
        key_q4_12 = {HEAD_DIM{16'd200}};
        value_q4_12 = {HEAD_DIM{16'd300}};
        rope_sin_q1_15 = '0;
        rope_cos_q1_15 = {HEAD_DIM{16'd32767}};
        cache_load_key = {HEAD_DIM{16'd77}};
        cache_load_value = {HEAD_DIM{16'd88}};
        repeat (4) @(negedge clk);
        rst_n = 1;
        @(negedge clk);
        start = 1;
        @(negedge clk);
        start = 0;
        wait (done);
        if (protocol_error || requests != 1 || chunks != 2)
            $fatal(1, "external KV counts request=%0d chunks=%0d error=%0d",
                   requests, chunks, protocol_error);
        $display("PASS external KV stream requests=%0d chunks=%0d", requests, chunks);
        $finish;
    end
endmodule
