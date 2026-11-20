`timescale 1ns / 1ps

module tb_rtwsr_attention_parallel4_e2e #(
    parameter int PARALLEL_HEADS = 4
);
    localparam int QUERY_SIZE = 5280;
    localparam int KV_SIZE = 5280;
    localparam int HEAD_DIM = 96;
    localparam int QUERY_HEADS = 55;
    localparam int MAX_CONTEXT = 2048;
    localparam int CONTEXT_TOKENS = 512;
    localparam int VECTOR_WIDTH = HEAD_DIM * 16;
    localparam int CHUNK_WIDTH = 128 * 16;
    localparam int HEAD_INDEX_W = 6;
    localparam logic [4:0] CMD_QKV = 5'd3;

    logic clk = 0, rst_n = 0;
    logic write_valid = 0, write_ready;
    logic [4:0] write_command_id = CMD_QKV;
    logic [15:0] write_row_start = 0;
    logic [6:0] write_rows = 0;
    logic [3071:0] write_result_q12 = '0;
    logic qkv_valid;

    logic s_start = 0, s_ready, s_done, s_error;
    logic s_read_start, s_read_ready, s_read_valid, s_read_done;
    logic [5:0] s_read_head;
    logic s_read_chunk;
    logic [1535:0] s_query_chunk, s_key_chunk, s_value_chunk;
    logic s_rope_start, s_rope_ready, s_rope_query_valid, s_rope_done, s_rope_error;
    logic [1535:0] s_rope_query, s_rope_key, s_rope_value, s_rope_query_rotated;
    logic s_rope_kv_valid, s_rope_kv_ready;
    logic [2047:0] s_rope_kv_key, s_rope_kv_value;
    logic s_attention_start, s_attention_ready, s_attention_kv_ready;
    logic [1535:0] s_attention_query;
    logic s_attention_kv_valid, s_attention_done, s_attention_error;
    logic [2047:0] s_attention_kv_key, s_attention_kv_value, s_attention_out;
    logic s_attention_out_valid, s_attention_out_ready;
    logic s_context_valid, s_context_last;
    logic [5:0] s_context_head;
    logic s_context_chunk;
    logic [2047:0] s_context_data;
    logic s_cache_read_request, s_cache_read_ready, s_cache_load_valid;
    logic [10:0] s_cache_read_index, s_cache_load_index;
    logic [1535:0] s_cache_load_key, s_cache_load_value;

    logic p_start = 0, p_ready, p_done, p_error;
    logic p_read_start, p_read_ready, p_read_valid, p_read_done;
    logic [PARALLEL_HEADS*6-1:0] p_read_heads;
    logic [PARALLEL_HEADS-1:0] p_read_chunks;
    logic [PARALLEL_HEADS*1536-1:0] p_query_chunks, p_key_chunks, p_value_chunks;
    logic [PARALLEL_HEADS-1:0] p_rope_start, p_rope_ready, p_rope_query_valid, p_rope_done, p_rope_error;
    logic [PARALLEL_HEADS*1536-1:0] p_rope_queries, p_rope_keys, p_rope_values, p_rope_queries_rotated;
    logic [PARALLEL_HEADS-1:0] p_rope_kv_valid, p_rope_kv_ready;
    logic [PARALLEL_HEADS*2048-1:0] p_rope_kv_keys, p_rope_kv_values;
    logic [PARALLEL_HEADS-1:0] p_attention_start;
    logic [PARALLEL_HEADS-1:0] p_attention_ready;
    logic [PARALLEL_HEADS*1536-1:0] p_attention_queries;
    logic [PARALLEL_HEADS-1:0] p_attention_kv_ready, p_attention_kv_valid;
    logic [PARALLEL_HEADS*2048-1:0] p_attention_kv_keys, p_attention_kv_values;
    logic [PARALLEL_HEADS-1:0] p_attention_done, p_attention_error, p_attention_out_valid, p_attention_out_ready;
    logic [PARALLEL_HEADS*2048-1:0] p_attention_out;
    logic [PARALLEL_HEADS-1:0] p_context_valid;
    logic [PARALLEL_HEADS*6-1:0] p_context_heads;
    logic [PARALLEL_HEADS-1:0] p_context_chunks;
    logic [PARALLEL_HEADS*2048-1:0] p_context_data;
    logic [PARALLEL_HEADS-1:0] p_cache_read_request, p_cache_read_ready, p_cache_load_valid;
    logic [PARALLEL_HEADS*6-1:0] p_cache_read_heads;
    logic [PARALLEL_HEADS*11-1:0] p_cache_read_indices, p_cache_load_indices;
    logic [PARALLEL_HEADS*1536-1:0] p_cache_load_keys, p_cache_load_values;

    logic [2047:0] serial_result [0:QUERY_HEADS-1];
    logic [2047:0] parallel_result [0:QUERY_HEADS-1];
    logic serial_seen [0:QUERY_HEADS-1];
    logic parallel_seen [0:QUERY_HEADS-1];
    integer cycle_count = 0;
    integer serial_start_cycle = 0;
    integer parallel_start_cycle = 0;
    integer serial_qkv_reads = 0;
    integer parallel_qkv_reads = 0;
    integer serial_kv_reads = 0;
    integer parallel_kv_reads = 0;
    integer serial_outputs = 0;
    integer parallel_outputs = 0;
    integer serial_cycles = 0;
    integer parallel_cycles = 0;
    logic serial_done_seen = 0;
    logic parallel_done_seen = 0;

    always #5 clk = ~clk;

    rtwsr_qkv_head_buffer_banked #(
        .QUERY_SIZE(QUERY_SIZE), .KV_SIZE(KV_SIZE), .HEAD_DIM(HEAD_DIM),
        .PARALLEL_READ_PORTS(PARALLEL_HEADS)
    ) u_qkv (
        .clk(clk), .rst_n(rst_n), .write_valid(write_valid), .write_ready(write_ready),
        .write_command_id(write_command_id), .write_row_start(write_row_start),
        .write_rows(write_rows), .write_result_q12(write_result_q12), .qkv_valid(qkv_valid),
        .read_start(s_read_start), .read_head_index(s_read_head), .read_chunk_index(s_read_chunk),
        .read_ready(s_read_ready), .read_valid(s_read_valid), .read_done(s_read_done),
        .query_chunk_q4_12(s_query_chunk), .key_chunk_q4_12(s_key_chunk),
        .value_chunk_q4_12(s_value_chunk), .parallel_read_start(p_read_start),
        .parallel_read_heads(p_read_heads), .parallel_read_chunks(p_read_chunks),
        .parallel_read_ready(p_read_ready), .parallel_read_valid(p_read_valid),
        .parallel_read_done(p_read_done), .parallel_query_chunks_q4_12(p_query_chunks),
        .parallel_key_chunks_q4_12(p_key_chunks), .parallel_value_chunks_q4_12(p_value_chunks)
    );

    rtwsr_recurrent_attention_bridge #(
        .QUERY_SIZE(QUERY_SIZE), .KV_SIZE(KV_SIZE), .HEAD_DIM(HEAD_DIM), .LANES(128)
    ) u_serial_bridge (
        .clk(clk), .rst_n(rst_n), .start(s_start), .ready(s_ready), .done(s_done),
        .protocol_error(s_error), .qkv_valid(qkv_valid), .qkv_read_start(s_read_start),
        .qkv_read_head(s_read_head), .qkv_read_chunk(s_read_chunk),
        .qkv_read_ready(s_read_ready), .qkv_read_valid(s_read_valid), .qkv_read_done(s_read_done),
        .qkv_query_chunk(s_query_chunk), .qkv_key_chunk(s_key_chunk), .qkv_value_chunk(s_value_chunk),
        .rope_start(s_rope_start), .rope_ready(s_rope_ready), .rope_query(s_rope_query),
        .rope_key(s_rope_key), .rope_value(s_rope_value), .rope_query_valid(s_rope_query_valid),
        .rope_query_rotated(s_rope_query_rotated), .rope_done(s_rope_done),
        .rope_error(s_rope_error), .rope_kv_valid(s_rope_kv_valid), .rope_kv_ready(s_rope_kv_ready),
        .rope_kv_key(s_rope_kv_key), .rope_kv_value(s_rope_kv_value),
        .attention_start(s_attention_start), .attention_ready(s_attention_ready),
        .attention_query(s_attention_query), .attention_kv_ready(s_attention_kv_ready),
        .attention_kv_valid(s_attention_kv_valid), .attention_kv_key(s_attention_kv_key),
        .attention_kv_value(s_attention_kv_value), .attention_done(s_attention_done),
        .attention_error(s_attention_error), .attention_out_valid(s_attention_out_valid),
        .attention_out_ready(s_attention_out_ready), .attention_out(s_attention_out),
        .context_valid(s_context_valid), .context_head(s_context_head),
        .context_chunk(s_context_chunk), .context_last(s_context_last), .context_data(s_context_data)
    );

    rtwsr_rope_kv_cache #(
        .HEAD_DIM(HEAD_DIM), .MAX_CONTEXT(MAX_CONTEXT), .LANES(128), .EXTERNAL_CACHE(1'b1)
    ) u_serial_rope (
        .clk(clk), .rst_n(rst_n), .start(s_rope_start), .write_position(11'(CONTEXT_TOKENS-1)),
        .active_context_tokens(12'(CONTEXT_TOKENS)), .window_start(11'd0),
        .query_q4_12(s_rope_query), .key_q4_12(s_rope_key), .value_q4_12(s_rope_value),
        .rope_sin_q1_15({HEAD_DIM{16'd0}}), .rope_cos_q1_15({HEAD_DIM{16'h7fff}}),
        .ready(s_rope_ready), .query_valid(s_rope_query_valid),
        .query_rotated_q4_12(s_rope_query_rotated), .kv_ready(s_rope_kv_ready),
        .kv_valid(s_rope_kv_valid), .kv_token_index(), .kv_chunk_index(),
        .kv_key_chunk_q4_12(s_rope_kv_key), .kv_value_chunk_q4_12(s_rope_kv_value), .kv_last(),
        .cache_load_ready(), .cache_load_valid(s_cache_load_valid),
        .cache_load_index(s_cache_load_index), .cache_load_key_q4_12(s_cache_load_key),
        .cache_load_value_q4_12(s_cache_load_value), .cache_read_request(s_cache_read_request),
        .cache_read_request_ready(s_cache_read_ready), .cache_read_index(s_cache_read_index),
        .busy(), .done(s_rope_done), .protocol_error(s_rope_error)
    );

    rtwsr_attention_gemv_unit #(
        .HEAD_DIM(HEAD_DIM), .LANES(128), .MAX_CONTEXT(MAX_CONTEXT), .QUERY_WIDTH(VECTOR_WIDTH),
        .CHUNK_WIDTH(CHUNK_WIDTH)
    ) u_serial_attention (
        .clk(clk), .rst_n(rst_n), .start(s_attention_start),
        .active_context_tokens(12'(CONTEXT_TOKENS)), .query_vector_q4_12(s_attention_query),
        .ready(s_attention_ready), .kv_valid(s_attention_kv_valid),
        .kv_ready(s_attention_kv_ready), .kv_key_chunk_q4_12(s_attention_kv_key),
        .kv_value_chunk_q4_12(s_attention_kv_value), .out_valid(s_attention_out_valid),
        .out_ready(s_attention_out_ready), .out_chunk_q4_12(s_attention_out), .out_last(),
        .busy(), .done(s_attention_done), .protocol_error(s_attention_error)
    );

    rtwsr_recurrent_attention_bridge4 #(
        .PARALLEL_HEADS(PARALLEL_HEADS), .QUERY_HEADS(QUERY_HEADS),
        .HEAD_DIM(HEAD_DIM), .LANES(128), .READ_WIDTH(VECTOR_WIDTH),
        .CHUNK_WIDTH(CHUNK_WIDTH), .HEAD_INDEX_W(HEAD_INDEX_W), .READ_CHUNK_INDEX_W(1),
        .ATTENTION_CHUNK_INDEX_W(1)
    ) u_parallel_bridge (
        .clk(clk), .rst_n(rst_n), .start(p_start), .ready(p_ready), .done(p_done),
        .protocol_error(p_error), .qkv_valid(qkv_valid), .qkv_read_start(p_read_start),
        .qkv_read_heads(p_read_heads), .qkv_read_chunks(p_read_chunks), .qkv_read_ready(p_read_ready),
        .qkv_read_valid(p_read_valid), .qkv_read_done(p_read_done), .qkv_read_mask(),
        .qkv_query_chunks(p_query_chunks), .qkv_key_chunks(p_key_chunks),
        .qkv_value_chunks(p_value_chunks), .rope_start(p_rope_start), .rope_ready(p_rope_ready),
        .rope_queries(p_rope_queries), .rope_keys(p_rope_keys), .rope_values(p_rope_values),
        .rope_query_valid(p_rope_query_valid), .rope_queries_rotated(p_rope_queries_rotated),
        .rope_done(p_rope_done), .rope_error(p_rope_error), .rope_kv_valid(p_rope_kv_valid),
        .rope_kv_ready(p_rope_kv_ready), .rope_kv_keys(p_rope_kv_keys),
        .rope_kv_values(p_rope_kv_values), .attention_start(p_attention_start),
        .attention_ready(p_attention_ready), .attention_queries(p_attention_queries),
        .attention_kv_ready(p_attention_kv_ready), .attention_kv_valid(p_attention_kv_valid),
        .attention_kv_keys(p_attention_kv_keys), .attention_kv_values(p_attention_kv_values),
        .attention_done(p_attention_done), .attention_error(p_attention_error),
        .attention_out_valid(p_attention_out_valid), .attention_out_ready(p_attention_out_ready),
        .attention_out(p_attention_out), .context_valid(p_context_valid),
        .context_heads(p_context_heads), .context_chunks(p_context_chunks), .context_data(p_context_data)
    );

    logic [PARALLEL_HEADS-1:0] p_attention_ready_by_head;

    assign p_cache_read_ready = '1;
    assign s_cache_read_ready = 1'b1;
    assign p_attention_ready = p_attention_ready_by_head;

    for (genvar lane = 0; lane < PARALLEL_HEADS; lane++) begin : g_parallel_head
        assign p_cache_read_heads[lane*HEAD_INDEX_W +: HEAD_INDEX_W] =
            p_context_heads[lane*HEAD_INDEX_W +: HEAD_INDEX_W];

        rtwsr_rope_kv_cache #(
            .HEAD_DIM(HEAD_DIM), .MAX_CONTEXT(MAX_CONTEXT), .LANES(128), .EXTERNAL_CACHE(1'b1)
        ) u_rope (
            .clk(clk), .rst_n(rst_n), .start(p_rope_start[lane]),
            .write_position(11'(CONTEXT_TOKENS-1)), .active_context_tokens(12'(CONTEXT_TOKENS)),
            .window_start(11'd0), .query_q4_12(p_rope_queries[lane*VECTOR_WIDTH +: VECTOR_WIDTH]),
            .key_q4_12(p_rope_keys[lane*VECTOR_WIDTH +: VECTOR_WIDTH]),
            .value_q4_12(p_rope_values[lane*VECTOR_WIDTH +: VECTOR_WIDTH]),
            .rope_sin_q1_15({HEAD_DIM{16'd0}}), .rope_cos_q1_15({HEAD_DIM{16'h7fff}}),
            .ready(p_rope_ready[lane]), .query_valid(p_rope_query_valid[lane]),
            .query_rotated_q4_12(p_rope_queries_rotated[lane*VECTOR_WIDTH +: VECTOR_WIDTH]),
            .kv_ready(p_rope_kv_ready[lane]), .kv_valid(p_rope_kv_valid[lane]),
            .kv_token_index(), .kv_chunk_index(),
            .kv_key_chunk_q4_12(p_rope_kv_keys[lane*CHUNK_WIDTH +: CHUNK_WIDTH]),
            .kv_value_chunk_q4_12(p_rope_kv_values[lane*CHUNK_WIDTH +: CHUNK_WIDTH]),
            .kv_last(), .cache_load_ready(), .cache_load_valid(p_cache_load_valid[lane]),
            .cache_load_index(p_cache_load_indices[lane*11 +: 11]),
            .cache_load_key_q4_12(p_cache_load_keys[lane*VECTOR_WIDTH +: VECTOR_WIDTH]),
            .cache_load_value_q4_12(p_cache_load_values[lane*VECTOR_WIDTH +: VECTOR_WIDTH]),
            .cache_read_request(p_cache_read_request[lane]),
            .cache_read_request_ready(p_cache_read_ready[lane]),
            .cache_read_index(p_cache_read_indices[lane*11 +: 11]),
            .busy(), .done(p_rope_done[lane]), .protocol_error(p_rope_error[lane])
        );

        rtwsr_attention_gemv_unit #(
            .HEAD_DIM(HEAD_DIM), .LANES(128), .MAX_CONTEXT(MAX_CONTEXT),
            .QUERY_WIDTH(VECTOR_WIDTH), .CHUNK_WIDTH(CHUNK_WIDTH)
        ) u_attention (
            .clk(clk), .rst_n(rst_n), .start(p_attention_start[lane]),
            .active_context_tokens(12'(CONTEXT_TOKENS)),
            .query_vector_q4_12(p_attention_queries[lane*VECTOR_WIDTH +: VECTOR_WIDTH]),
            .ready(p_attention_ready_by_head[lane]), .kv_valid(p_attention_kv_valid[lane]),
            .kv_ready(p_attention_kv_ready[lane]),
            .kv_key_chunk_q4_12(p_attention_kv_keys[lane*CHUNK_WIDTH +: CHUNK_WIDTH]),
            .kv_value_chunk_q4_12(p_attention_kv_values[lane*CHUNK_WIDTH +: CHUNK_WIDTH]),
            .out_valid(p_attention_out_valid[lane]), .out_ready(p_attention_out_ready[lane]),
            .out_chunk_q4_12(p_attention_out[lane*CHUNK_WIDTH +: CHUNK_WIDTH]),
            .out_last(), .busy(), .done(p_attention_done[lane]),
            .protocol_error(p_attention_error[lane])
        );
    end

    function automatic integer q_value(input integer row);
        q_value = ((((row * 17 + 13) % 51) - 25) * 24);
    endfunction

    function automatic integer k_value(input integer row);
        k_value = ((((row * 23 + 7) % 49) - 24) * 20);
    endfunction

    function automatic integer v_value(input integer row);
        v_value = ((((row * 29 + 3) % 55) - 27) * 18);
    endfunction

    function automatic integer history_key(input integer head, input integer token, input integer dim);
        history_key = (((head*23 + token*7 + dim*3) % 61) - 30) * 16;
    endfunction

    function automatic integer history_value(input integer head, input integer token, input integer dim);
        history_value = (((head*11 + token*13 + dim*5) % 73) - 36) * 16;
    endfunction

    task automatic write_qkv_tile(input integer row_start);
        integer row;
        begin
            @(negedge clk);
            write_row_start = 16'(row_start);
            write_rows = 7'd96;
            for (integer lane = 0; lane < 96; lane++) begin
                row = row_start + lane;
                if (row < QUERY_SIZE)
                    write_result_q12[lane*32 +: 32] = 32'(q_value(row));
                else if (row < QUERY_SIZE + KV_SIZE)
                    write_result_q12[lane*32 +: 32] = 32'(k_value(row - QUERY_SIZE));
                else
                    write_result_q12[lane*32 +: 32] = 32'(v_value(row - QUERY_SIZE - KV_SIZE));
            end
            write_valid = 1;
            @(negedge clk);
            write_valid = 0;
        end
    endtask

    always @(posedge clk) begin
        integer head;
        integer token;
        if (!rst_n) begin
            cycle_count <= 0;
            serial_qkv_reads <= 0;
            parallel_qkv_reads <= 0;
            serial_kv_reads <= 0;
            parallel_kv_reads <= 0;
            serial_outputs <= 0;
            parallel_outputs <= 0;
            serial_cycles <= 0;
            parallel_cycles <= 0;
            serial_done_seen <= 1'b0;
            parallel_done_seen <= 1'b0;
            s_cache_load_valid <= 0;
            s_cache_load_index <= '0;
            s_cache_load_key <= '0;
            s_cache_load_value <= '0;
            p_cache_load_valid <= '0;
            p_cache_load_indices <= '0;
            p_cache_load_keys <= '0;
            p_cache_load_values <= '0;
            for (integer index = 0; index < QUERY_HEADS; index++) begin
                serial_result[index] <= '0;
                parallel_result[index] <= '0;
                serial_seen[index] <= 1'b0;
                parallel_seen[index] <= 1'b0;
            end
        end else begin
            cycle_count <= cycle_count + 1;
            if ((cycle_count % 1000000) == 0) begin
                $display("ATTN_PARALLEL_PROGRESS heads=%0d cycle=%0d serial_state=%0d serial_head=%0d serial_kv_state=%0d serial_attn_state=%0d parallel_state=%0d parallel_head_base=%0d parallel_mask=0x%x parallel_kv_reads=%0d/%0d outputs=%0d/%0d ready=0x%x/0x%x",
                    PARALLEL_HEADS,
                    cycle_count, u_serial_bridge.state_q, u_serial_bridge.head_q,
                    u_serial_rope.state_q, u_serial_attention.state_q,
                    u_parallel_bridge.state_q, u_parallel_bridge.head_base_q,
                    u_parallel_bridge.head_mask_q, serial_kv_reads, parallel_kv_reads,
                    serial_outputs, parallel_outputs, p_attention_ready_by_head,
                    p_attention_kv_ready);
            end
            if (s_done && serial_cycles == 0)
                serial_cycles <= cycle_count - serial_start_cycle;
            if (p_done && parallel_cycles == 0)
                parallel_cycles <= cycle_count - parallel_start_cycle;
            if (s_done)
                serial_done_seen <= 1'b1;
            if (p_done)
                parallel_done_seen <= 1'b1;
            s_cache_load_valid <= 1'b0;
            p_cache_load_valid <= '0;
            if (s_read_start)
                serial_qkv_reads <= serial_qkv_reads + 1;
            if (p_read_start)
                parallel_qkv_reads <= parallel_qkv_reads + 1;
            parallel_kv_reads <= parallel_kv_reads + $countones(p_cache_read_request & p_cache_read_ready);
            parallel_outputs <= parallel_outputs + $countones(p_context_valid);
            if (s_cache_read_request && s_cache_read_ready) begin
                serial_kv_reads <= serial_kv_reads + 1;
                s_cache_load_valid <= 1'b1;
                s_cache_load_index <= s_cache_read_index;
                token = int'(s_cache_read_index);
                for (integer dim = 0; dim < HEAD_DIM; dim++) begin
                    s_cache_load_key[dim*16 +: 16] <= 16'(history_key(int'(s_read_head), token, dim));
                    s_cache_load_value[dim*16 +: 16] <= 16'(history_value(int'(s_read_head), token, dim));
                end
            end
            for (integer lane = 0; lane < PARALLEL_HEADS; lane++) begin
                if (p_cache_read_request[lane] && p_cache_read_ready[lane]) begin
                    p_cache_load_valid[lane] <= 1'b1;
                    p_cache_load_indices[lane*11 +: 11] <= p_cache_read_indices[lane*11 +: 11];
                    head = int'(p_cache_read_heads[lane*6 +: 6]);
                    token = int'(p_cache_read_indices[lane*11 +: 11]);
                    for (integer dim = 0; dim < HEAD_DIM; dim++) begin
                        p_cache_load_keys[lane*VECTOR_WIDTH + dim*16 +: 16] <=
                            16'(history_key(head, token, dim));
                        p_cache_load_values[lane*VECTOR_WIDTH + dim*16 +: 16] <=
                            16'(history_value(head, token, dim));
                    end
                end
            end
            if (s_context_valid) begin
                head = int'(s_context_head);
                serial_result[head] <= s_context_data;
                serial_seen[head] <= 1'b1;
                serial_outputs <= serial_outputs + 1;
            end
            for (integer lane = 0; lane < PARALLEL_HEADS; lane++) begin
                if (p_context_valid[lane]) begin
                    head = int'(p_context_heads[lane*6 +: 6]);
                    parallel_result[head] <= p_context_data[lane*CHUNK_WIDTH +: CHUNK_WIDTH];
                    parallel_seen[head] <= 1'b1;
                end
            end
        end
    end

    initial begin
        integer row_count;
        integer head;
        integer dim;
        repeat (4) @(negedge clk);
        rst_n = 1;
        row_count = QUERY_SIZE + 2*KV_SIZE;
        for (integer row = 0; row < row_count; row += 96)
            write_qkv_tile(row);
        if (!qkv_valid)
            $fatal(1, "QKV write did not complete");

        @(negedge clk);
        serial_start_cycle = cycle_count;
        parallel_start_cycle = cycle_count;
        s_start = 1;
        p_start = 1;
        @(negedge clk);
        s_start = 0;
        p_start = 0;
        wait (serial_done_seen && parallel_done_seen);
        @(negedge clk);
        if (s_error || p_error)
            $fatal(1, "attention bridge protocol error serial=%0d parallel=%0d", s_error, p_error);
        if (serial_outputs != QUERY_HEADS || parallel_outputs != QUERY_HEADS)
            $fatal(1, "attention output count mismatch serial=%0d parallel=%0d",
                   serial_outputs, parallel_outputs);
        for (head = 0; head < QUERY_HEADS; head++) begin
            if (!serial_seen[head] || !parallel_seen[head])
                $fatal(1, "attention output missing head=%0d serial_seen=%0d parallel_seen=%0d",
                       head, serial_seen[head], parallel_seen[head]);
            if (serial_result[head] !== parallel_result[head]) begin
                dim = 0;
                while (dim < 128 &&
                       serial_result[head][dim*16 +: 16] === parallel_result[head][dim*16 +: 16])
                    dim++;
                $fatal(1, "attention output mismatch head=%0d lane=%0d dim=%0d serial=0x%04x parallel=0x%04x",
                       head, head % 4, dim, serial_result[head][dim*16 +: 16],
                       parallel_result[head][dim*16 +: 16]);
            end
            for (dim = HEAD_DIM; dim < 128; dim++) begin
                if (serial_result[head][dim*16 +: 16] !== 16'd0 ||
                    parallel_result[head][dim*16 +: 16] !== 16'd0)
                    $fatal(1, "nonzero output padding head=%0d dim=%0d", head, dim);
            end
        end
        if (serial_qkv_reads != QUERY_HEADS ||
            parallel_qkv_reads != (QUERY_HEADS+PARALLEL_HEADS-1)/PARALLEL_HEADS ||
            serial_kv_reads != (CONTEXT_TOKENS-1)*QUERY_HEADS ||
            parallel_kv_reads != (CONTEXT_TOKENS-1)*QUERY_HEADS ||
            parallel_cycles >= serial_cycles)
                $fatal(1, "attention cycle/count mismatch serial=%0d parallel%0d=%0d qkv=%0d/%0d kv=%0d/%0d",
                   serial_cycles, PARALLEL_HEADS, parallel_cycles, serial_qkv_reads, parallel_qkv_reads,
                   serial_kv_reads, parallel_kv_reads);
        $display("PASS Huginn attention full-head regression context=%0d heads=%0d parallel_heads=%0d serial_cycles=%0d parallel_cycles=%0d qkv_reads=%0d/%0d kv_reads=%0d/%0d outputs=%0d/%0d",
                 CONTEXT_TOKENS, QUERY_HEADS, PARALLEL_HEADS, serial_cycles, parallel_cycles,
                 serial_qkv_reads, parallel_qkv_reads, serial_kv_reads, parallel_kv_reads,
                 serial_outputs, parallel_outputs);
        $display("R32 single-physical-block extrapolation serial=%0d parallel%0d=%0d; full 4-block core must also include all non-attention stages",
                 serial_cycles*32, PARALLEL_HEADS, parallel_cycles*32);
        $finish;
    end

    initial begin
        #200000000;
            $display("ATTN_PARALLEL_TIMEOUT heads=%0d cycle=%0d serial_state=%0d serial_head=%0d serial_kv_state=%0d serial_attn_state=%0d parallel_state=%0d parallel_head_base=%0d parallel_mask=0x%x parallel_kv_reads=%0d/%0d qkv_reads=%0d/%0d outputs=%0d/%0d ready=0x%x/0x%x rope_ready=0x%x rope_query_valid=0x%x rope_done=0x%x attention_done=0x%x",
            PARALLEL_HEADS,
            cycle_count, u_serial_bridge.state_q, u_serial_bridge.head_q,
            u_serial_rope.state_q, u_serial_attention.state_q,
            u_parallel_bridge.state_q, u_parallel_bridge.head_base_q,
            u_parallel_bridge.head_mask_q, serial_kv_reads, parallel_kv_reads,
            serial_qkv_reads, parallel_qkv_reads, serial_outputs, parallel_outputs,
            p_attention_ready_by_head, p_attention_kv_ready,
            p_rope_ready, p_rope_query_valid, p_rope_done, p_attention_done);
        $fatal(1, "full-head attention regression timeout cycle=%0d", cycle_count);
    end
endmodule
