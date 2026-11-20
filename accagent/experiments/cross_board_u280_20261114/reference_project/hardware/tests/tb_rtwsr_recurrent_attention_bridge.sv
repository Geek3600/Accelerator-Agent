`timescale 1ns / 1ps

module tb_rtwsr_recurrent_attention_bridge;
    localparam int QUERY_SIZE = 1024;
    localparam int KV_SIZE = 256;
    localparam int HEAD_DIM = 256;
    localparam int QUERY_HEADS = QUERY_SIZE / HEAD_DIM;

    logic clk = 0;
    logic rst_n = 0;
    logic start = 0;
    logic ready, done, protocol_error;
    logic qkv_valid = 1;
    logic qkv_read_start, qkv_read_ready, qkv_read_valid = 0, qkv_read_done;
    logic [1:0] qkv_read_head;
    logic [1:0] qkv_read_chunk;
    logic [1535:0] qkv_query_chunk, qkv_key_chunk, qkv_value_chunk;
    logic rope_start, rope_ready, rope_query_valid = 0, rope_done = 0, rope_error = 0;
    logic [4095:0] rope_query, rope_key, rope_value, rope_query_rotated;
    logic rope_kv_valid = 0, rope_kv_ready;
    logic [2047:0] rope_kv_key = '0, rope_kv_value = '0;
    logic attention_start, attention_ready, attention_kv_ready;
    logic [4095:0] attention_query;
    logic attention_kv_valid, attention_done = 0, attention_error = 0;
    logic [2047:0] attention_kv_key, attention_kv_value;
    logic attention_out_valid = 0, attention_out_ready;
    logic [2047:0] attention_out;
    logic context_valid, context_last;
    logic [1:0] context_head;
    logic context_chunk;
    logic [2047:0] context_data;
    logic rope_active_q = 0;
    logic attention_active_q = 0;
    logic attention_output_active_q = 0;
    logic attention_output_chunk_q = 0;
    logic [1:0] rope_kv_chunk_q = 0;
    integer read_count = 0;
    integer rope_count = 0;
    integer attention_count = 0;
    integer context_count = 0;
    integer last_count = 0;
    integer cycles = 0;

    always #5 clk = ~clk;

    assign qkv_read_ready = !qkv_read_valid;
    assign rope_ready = !rope_active_q;
    assign rope_query_rotated = rope_query;
    assign attention_ready = !attention_active_q && !attention_done;
    assign attention_kv_ready = attention_active_q && !attention_output_active_q;
    assign attention_out_ready = 1'b1;
    assign attention_out = {128{16'(context_head * 100 + attention_output_chunk_q * 128)}};

    always_comb begin
        integer lane;
        integer dimension;
        integer head_base;
        qkv_query_chunk = '0;
        qkv_key_chunk = '0;
        qkv_value_chunk = '0;
        head_base = int'(qkv_read_head) * 1000;
        for (lane = 0; lane < 96; lane = lane + 1) begin
            dimension = int'(qkv_read_chunk) * 96 + lane;
            if (dimension < HEAD_DIM) begin
                qkv_query_chunk[lane*16 +: 16] = 16'(head_base + dimension);
                qkv_key_chunk[lane*16 +: 16] = 16'(2*head_base + dimension);
                qkv_value_chunk[lane*16 +: 16] = 16'(3*head_base + dimension);
            end
        end
    end

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            qkv_read_valid <= 1'b0;
            rope_query_valid <= 1'b0;
            rope_done <= 1'b0;
            rope_kv_valid <= 1'b0;
            attention_done <= 1'b0;
            attention_out_valid <= 1'b0;
            rope_active_q <= 1'b0;
            attention_active_q <= 1'b0;
            attention_output_active_q <= 1'b0;
            attention_output_chunk_q <= 1'b0;
            rope_kv_chunk_q <= '0;
            read_count <= 0;
            rope_count <= 0;
            attention_count <= 0;
            context_count <= 0;
            last_count <= 0;
            cycles <= 0;
        end else begin
            cycles <= cycles + 1;
            if (cycles > 3000)
                $fatal(1, "bridge timed out");
            qkv_read_valid <= qkv_read_start;
            rope_query_valid <= rope_start;
            rope_done <= 1'b0;
            attention_done <= 1'b0;
            if (qkv_read_start)
                read_count <= read_count + 1;
            if (rope_start) begin
                rope_count <= rope_count + 1;
                if (!rope_ready)
                    $fatal(1, "RoPE started while busy");
                for (integer dimension_id = 0; dimension_id < HEAD_DIM; dimension_id++) begin
                    if ($signed(rope_query[dimension_id*16 +: 16]) !=
                        int'(qkv_read_head) * 1000 + dimension_id ||
                        $signed(rope_key[dimension_id*16 +: 16]) !=
                        int'(qkv_read_head) * 2000 + dimension_id ||
                        $signed(rope_value[dimension_id*16 +: 16]) !=
                        int'(qkv_read_head) * 3000 + dimension_id)
                        $fatal(1, "assembled QKV mismatch head=%0d dim=%0d",
                               qkv_read_head, dimension_id);
                end
                rope_active_q <= 1'b1;
                rope_kv_chunk_q <= '0;
            end
            if (attention_start) begin
                attention_count <= attention_count + 1;
                if (!attention_ready || attention_query !== rope_query_rotated)
                    $fatal(1, "Attention query handshake mismatch");
                attention_active_q <= 1'b1;
            end
            if (rope_kv_valid && attention_kv_ready) begin
                rope_kv_valid <= 1'b0;
                if (rope_kv_chunk_q == 1) begin
                    rope_active_q <= 1'b0;
                    rope_done <= 1'b1;
                end else begin
                    rope_kv_chunk_q <= rope_kv_chunk_q + 1'b1;
                end
            end else if (rope_active_q && attention_active_q) begin
                rope_kv_valid <= 1'b1;
            end
            if (attention_kv_valid && attention_kv_ready) begin
                attention_output_active_q <= 1'b1;
                attention_out_valid <= 1'b1;
            end
            if (attention_out_valid && attention_out_ready) begin
                context_count <= context_count + 1;
                if (context_head != context_count / 2 || context_chunk != context_count % 2)
                    $fatal(1, "context index mismatch head=%0d chunk=%0d count=%0d",
                           context_head, context_chunk, context_count);
                if (context_last)
                    last_count <= last_count + 1;
                attention_output_active_q <= 1'b0;
                if (!attention_output_chunk_q) begin
                    attention_output_chunk_q <= 1'b1;
                end else begin
                    attention_output_chunk_q <= 1'b0;
                    attention_active_q <= 1'b0;
                    attention_done <= 1'b1;
                end
                attention_out_valid <= 1'b0;
            end
        end
    end

    rtwsr_recurrent_attention_bridge #(
        .QUERY_SIZE(QUERY_SIZE), .KV_SIZE(KV_SIZE), .HEAD_DIM(HEAD_DIM)
    ) dut (
        .clk(clk), .rst_n(rst_n), .start(start), .ready(ready), .done(done),
        .protocol_error(protocol_error), .qkv_valid(qkv_valid),
        .qkv_read_start(qkv_read_start), .qkv_read_head(qkv_read_head),
        .qkv_read_chunk(qkv_read_chunk), .qkv_read_ready(qkv_read_ready),
        .qkv_read_valid(qkv_read_valid), .qkv_read_done(qkv_read_done),
        .qkv_query_chunk(qkv_query_chunk), .qkv_key_chunk(qkv_key_chunk),
        .qkv_value_chunk(qkv_value_chunk), .rope_start(rope_start), .rope_ready(rope_ready),
        .rope_query(rope_query), .rope_key(rope_key), .rope_value(rope_value),
        .rope_query_valid(rope_query_valid), .rope_query_rotated(rope_query_rotated),
        .rope_done(rope_done), .rope_error(rope_error), .rope_kv_valid(rope_kv_valid),
        .rope_kv_ready(rope_kv_ready), .rope_kv_key(rope_kv_key),
        .rope_kv_value(rope_kv_value), .attention_start(attention_start),
        .attention_ready(attention_ready), .attention_query(attention_query),
        .attention_kv_ready(attention_kv_ready), .attention_kv_valid(attention_kv_valid),
        .attention_kv_key(attention_kv_key), .attention_kv_value(attention_kv_value),
        .attention_done(attention_done), .attention_error(attention_error),
        .attention_out_valid(attention_out_valid), .attention_out_ready(attention_out_ready),
        .attention_out(attention_out), .context_valid(context_valid),
        .context_head(context_head), .context_chunk(context_chunk),
        .context_last(context_last), .context_data(context_data)
    );

    initial begin
        repeat (4) @(negedge clk);
        rst_n = 1'b1;
        @(negedge clk);
        start = 1'b1;
        @(negedge clk);
        start = 1'b0;
        wait (done);
        if (protocol_error || read_count != QUERY_HEADS*3 || rope_count != QUERY_HEADS ||
            attention_count != QUERY_HEADS || context_count != QUERY_HEADS*2 || last_count != 1)
            $fatal(1, "bridge count mismatch read=%0d rope=%0d attention=%0d context=%0d last=%0d",
                   read_count, rope_count, attention_count, context_count, last_count);
        $display("PASS QKV-to-attention bridge heads=%0d reads=%0d context_chunks=%0d cycles=%0d",
                 QUERY_HEADS, read_count, context_count, cycles);
        $finish;
    end
endmodule
