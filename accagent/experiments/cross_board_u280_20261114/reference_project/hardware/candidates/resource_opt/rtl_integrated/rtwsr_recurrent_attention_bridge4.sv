`timescale 1ns / 1ps

module rtwsr_recurrent_attention_bridge4 #(
    parameter int PARALLEL_HEADS = 4,
    parameter int QUERY_HEADS = 55,
    parameter int HEAD_DIM = 96,
    parameter int LANES = 128,
    parameter int DATA_W = 16,
    parameter int READ_WIDTH = 96 * DATA_W,
    parameter int CHUNK_WIDTH = LANES * DATA_W,
    parameter int HEAD_INDEX_W = (QUERY_HEADS <= 1) ? 1 : $clog2(QUERY_HEADS),
    parameter int READ_CHUNK_INDEX_W = 1,
    parameter int ATTENTION_CHUNKS = (HEAD_DIM + LANES - 1) / LANES,
    parameter int ATTENTION_CHUNK_INDEX_W = (ATTENTION_CHUNKS <= 1) ? 1 : $clog2(ATTENTION_CHUNKS)
)(
    input  logic                                  clk,
    input  logic                                  rst_n,
    input  logic                                  start,
    output logic                                  ready,
    output logic                                  done,
    output logic                                  protocol_error,
    input  logic                                  qkv_valid,
    output logic                                  qkv_read_start,
    output logic [PARALLEL_HEADS*HEAD_INDEX_W-1:0] qkv_read_heads,
    output logic [PARALLEL_HEADS*READ_CHUNK_INDEX_W-1:0] qkv_read_chunks,
    input  logic                                  qkv_read_ready,
    input  logic                                  qkv_read_valid,
    output logic                                  qkv_read_done,
    output logic [PARALLEL_HEADS-1:0]             qkv_read_mask,
    input  logic [PARALLEL_HEADS*READ_WIDTH-1:0] qkv_query_chunks,
    input  logic [PARALLEL_HEADS*READ_WIDTH-1:0] qkv_key_chunks,
    input  logic [PARALLEL_HEADS*READ_WIDTH-1:0] qkv_value_chunks,
    output logic [PARALLEL_HEADS-1:0]            rope_start,
    input  logic [PARALLEL_HEADS-1:0]            rope_ready,
    output logic [PARALLEL_HEADS*HEAD_DIM*DATA_W-1:0] rope_queries,
    output logic [PARALLEL_HEADS*HEAD_DIM*DATA_W-1:0] rope_keys,
    output logic [PARALLEL_HEADS*HEAD_DIM*DATA_W-1:0] rope_values,
    input  logic [PARALLEL_HEADS-1:0]            rope_query_valid,
    input  logic [PARALLEL_HEADS*HEAD_DIM*DATA_W-1:0] rope_queries_rotated,
    input  logic [PARALLEL_HEADS-1:0]            rope_done,
    input  logic [PARALLEL_HEADS-1:0]            rope_error,
    input  logic [PARALLEL_HEADS-1:0]            rope_kv_valid,
    output logic [PARALLEL_HEADS-1:0]            rope_kv_ready,
    input  logic [PARALLEL_HEADS*CHUNK_WIDTH-1:0] rope_kv_keys,
    input  logic [PARALLEL_HEADS*CHUNK_WIDTH-1:0] rope_kv_values,
    output logic [PARALLEL_HEADS-1:0]            attention_start,
    input  logic [PARALLEL_HEADS-1:0]             attention_ready,
    output logic [PARALLEL_HEADS*HEAD_DIM*DATA_W-1:0] attention_queries,
    input  logic [PARALLEL_HEADS-1:0]            attention_kv_ready,
    output logic [PARALLEL_HEADS-1:0]            attention_kv_valid,
    output logic [PARALLEL_HEADS*CHUNK_WIDTH-1:0] attention_kv_keys,
    output logic [PARALLEL_HEADS*CHUNK_WIDTH-1:0] attention_kv_values,
    input  logic [PARALLEL_HEADS-1:0]            attention_done,
    input  logic [PARALLEL_HEADS-1:0]            attention_error,
    input  logic [PARALLEL_HEADS-1:0]            attention_out_valid,
    output logic [PARALLEL_HEADS-1:0]            attention_out_ready,
    input  logic [PARALLEL_HEADS*CHUNK_WIDTH-1:0] attention_out,
    output logic [PARALLEL_HEADS-1:0]            context_valid,
    output logic [PARALLEL_HEADS*HEAD_INDEX_W-1:0] context_heads,
    output logic [PARALLEL_HEADS*ATTENTION_CHUNK_INDEX_W-1:0] context_chunks,
    output logic [PARALLEL_HEADS*CHUNK_WIDTH-1:0] context_data
);
    typedef enum logic [2:0] {IDLE, READ_QKV, LAUNCH_ROPE, RUN_HEADS, COMPLETE, FAILED} state_t;
    state_t state_q;
    logic [HEAD_INDEX_W-1:0] head_base_q;
    logic [ATTENTION_CHUNK_INDEX_W-1:0] output_chunk_q;
    logic [PARALLEL_HEADS-1:0] head_mask_q;
    logic [PARALLEL_HEADS-1:0] rope_started_q;
    logic [PARALLEL_HEADS-1:0] rope_query_done_q;
    logic [PARALLEL_HEADS-1:0] rope_done_q;
    logic [PARALLEL_HEADS-1:0] attention_done_q;
    logic [PARALLEL_HEADS-1:0] attention_started_q;
    logic [PARALLEL_HEADS-1:0] protocol_error_q;
    logic [PARALLEL_HEADS*HEAD_DIM*DATA_W-1:0] query_q;
    logic [PARALLEL_HEADS*HEAD_DIM*DATA_W-1:0] key_q;
    logic [PARALLEL_HEADS*HEAD_DIM*DATA_W-1:0] value_q;
    logic [PARALLEL_HEADS*HEAD_DIM*DATA_W-1:0] rotated_query_q;

    assign ready = (state_q == IDLE) && qkv_valid;
    assign done = (state_q == COMPLETE) || (state_q == FAILED);
    assign protocol_error = |protocol_error_q;
    assign qkv_read_start = (state_q == READ_QKV) && qkv_read_ready;
    assign qkv_read_done = (state_q == READ_QKV) && qkv_read_valid;
    assign qkv_read_mask = head_mask_q;
    always_comb begin
        logic launch_pending;
        rope_start = '0;
        launch_pending = (state_q == LAUNCH_ROPE);
        for (integer port = 0; port < PARALLEL_HEADS; port++) begin
            if (launch_pending && head_mask_q[port] && !rope_started_q[port] && rope_ready[port]) begin
                rope_start[port] = 1'b1;
                launch_pending = 1'b0;
            end
        end
    end
    assign rope_queries = query_q;
    assign rope_keys = key_q;
    assign rope_values = value_q;
    always_comb begin
        attention_start = '0;
        if ((state_q == RUN_HEADS) && (&(rope_query_done_q | ~head_mask_q))) begin
            for (integer port = 0; port < PARALLEL_HEADS; port++) begin
                attention_start[port] = head_mask_q[port] &&
                    !attention_started_q[port] && attention_ready[port];
            end
        end
    end
    assign attention_queries = rotated_query_q;
    assign attention_kv_valid = rope_kv_valid;
    assign attention_kv_keys = rope_kv_keys;
    assign attention_kv_values = rope_kv_values;
    assign rope_kv_ready = attention_kv_ready;
    assign attention_out_ready = {PARALLEL_HEADS{1'b1}};
    assign context_valid = attention_out_valid & head_mask_q;
    assign context_data = attention_out;

    always_comb begin
        integer port;
        integer head_index;
        qkv_read_heads = '0;
        qkv_read_chunks = '0;
        context_heads = '0;
        context_chunks = '0;
        for (port = 0; port < PARALLEL_HEADS; port = port + 1) begin
            head_index = int'(head_base_q) + port;
            if (head_index >= QUERY_HEADS)
                head_index = QUERY_HEADS - 1;
            qkv_read_heads[port*HEAD_INDEX_W +: HEAD_INDEX_W] = HEAD_INDEX_W'(head_index);
            qkv_read_chunks[port*READ_CHUNK_INDEX_W +: READ_CHUNK_INDEX_W] = '0;
            context_heads[port*HEAD_INDEX_W +: HEAD_INDEX_W] = HEAD_INDEX_W'(head_index);
            context_chunks[port*ATTENTION_CHUNK_INDEX_W +: ATTENTION_CHUNK_INDEX_W] = output_chunk_q;
        end
    end

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            state_q <= IDLE;
            head_base_q <= '0;
            output_chunk_q <= '0;
            head_mask_q <= '0;
            rope_started_q <= '0;
            rope_query_done_q <= '0;
            rope_done_q <= '0;
            attention_done_q <= '0;
            attention_started_q <= '0;
            protocol_error_q <= '0;
            query_q <= '0;
            key_q <= '0;
            value_q <= '0;
            rotated_query_q <= '0;
        end else if ((|rope_error) || (|attention_error)) begin
            protocol_error_q <= protocol_error_q | rope_error | attention_error;
            state_q <= FAILED;
        end else begin
            case (state_q)
                IDLE: begin
                    if (start && ready) begin
                        head_base_q <= '0;
                        head_mask_q <= '0;
                        rope_started_q <= '0;
                        rope_query_done_q <= '0;
                        attention_started_q <= '0;
                        output_chunk_q <= '0;
                        protocol_error_q <= '0;
                        state_q <= READ_QKV;
                    end
                end
                READ_QKV: begin
                    if (qkv_read_valid) begin
                        attention_started_q <= '0;
                        for (integer port = 0; port < PARALLEL_HEADS; port = port + 1) begin
                            query_q[port*HEAD_DIM*DATA_W +: HEAD_DIM*DATA_W] <=
                                qkv_query_chunks[port*READ_WIDTH +: HEAD_DIM*DATA_W];
                            key_q[port*HEAD_DIM*DATA_W +: HEAD_DIM*DATA_W] <=
                                qkv_key_chunks[port*READ_WIDTH +: HEAD_DIM*DATA_W];
                            value_q[port*HEAD_DIM*DATA_W +: HEAD_DIM*DATA_W] <=
                                qkv_value_chunks[port*READ_WIDTH +: HEAD_DIM*DATA_W];
                            head_mask_q[port] <= int'(head_base_q) + port < QUERY_HEADS;
                        end
                        state_q <= LAUNCH_ROPE;
                    end
                end
                LAUNCH_ROPE: begin
                    rope_started_q <= rope_started_q | rope_start;
                    rope_query_done_q <= rope_query_done_q | rope_query_valid;
                    for (integer port = 0; port < PARALLEL_HEADS; port++) begin
                        if (rope_query_valid[port])
                            rotated_query_q[port*HEAD_DIM*DATA_W +: HEAD_DIM*DATA_W] <=
                                rope_queries_rotated[port*HEAD_DIM*DATA_W +: HEAD_DIM*DATA_W];
                    end
                    if (&(rope_started_q | rope_start | ~head_mask_q)) begin
                        output_chunk_q <= '0;
                        rope_done_q <= '0;
                        attention_done_q <= '0;
                        state_q <= RUN_HEADS;
                    end
                end
                RUN_HEADS: begin
                    attention_started_q <= attention_started_q | attention_start;
                    rope_query_done_q <= rope_query_done_q | rope_query_valid;
                    for (integer port = 0; port < PARALLEL_HEADS; port++) begin
                        if (rope_query_valid[port])
                            rotated_query_q[port*HEAD_DIM*DATA_W +: HEAD_DIM*DATA_W] <=
                                rope_queries_rotated[port*HEAD_DIM*DATA_W +: HEAD_DIM*DATA_W];
                    end
                    if (context_valid[0] &&
                        output_chunk_q != ATTENTION_CHUNK_INDEX_W'(ATTENTION_CHUNKS - 1))
                        output_chunk_q <= output_chunk_q + 1'b1;
                    rope_done_q <= rope_done_q | rope_done;
                    attention_done_q <= attention_done_q | attention_done;
                    if ((&(rope_done_q | rope_done | ~head_mask_q)) &&
                        (&(attention_done_q | attention_done | ~head_mask_q))) begin
                        rope_done_q <= '0;
                        attention_done_q <= '0;
                        if (int'(head_base_q) + PARALLEL_HEADS >= QUERY_HEADS) begin
                            state_q <= COMPLETE;
                        end else begin
                            head_base_q <= head_base_q + PARALLEL_HEADS;
                            rope_started_q <= '0;
                            rope_query_done_q <= '0;
                            attention_started_q <= '0;
                            state_q <= READ_QKV;
                        end
                    end
                end
                COMPLETE, FAILED: begin
                    if (!start)
                        state_q <= IDLE;
                end
                default: state_q <= IDLE;
            endcase
        end
    end

    initial begin
        if (PARALLEL_HEADS < 1 || QUERY_HEADS < PARALLEL_HEADS ||
            HEAD_DIM != 96 || DATA_W != 16 || LANES != 128)
            $error("Parallel Plan 6 candidate requires Huginn-compatible 96x16 heads and 128 lanes");
    end
endmodule
