`timescale 1ns / 1ps

module rtwsr_attention_2head_ooc_top #(
    parameter int HEAD_DIM = 96,
    parameter int LANES = 128,
    parameter int MAX_CONTEXT = 2048,
    parameter int PARALLEL_ENGINES = 2,
    parameter int DATA_W = 16,
    parameter int QUERY_WIDTH = HEAD_DIM * DATA_W,
    parameter int CHUNK_WIDTH = LANES * DATA_W,
    parameter int CONTEXT_COUNT_W = $clog2(MAX_CONTEXT + 1)
)(
    input  logic clk,
    input  logic rst_n,
    input  logic [PARALLEL_ENGINES-1:0] start,
    input  logic [PARALLEL_ENGINES*CONTEXT_COUNT_W-1:0] active_context_tokens,
    input  logic [PARALLEL_ENGINES*QUERY_WIDTH-1:0] query_vector_q4_12,
    output logic [PARALLEL_ENGINES-1:0] ready,
    input  logic [PARALLEL_ENGINES-1:0] kv_valid,
    output logic [PARALLEL_ENGINES-1:0] kv_ready,
    input  logic [PARALLEL_ENGINES*CHUNK_WIDTH-1:0] kv_key_chunk_q4_12,
    input  logic [PARALLEL_ENGINES*CHUNK_WIDTH-1:0] kv_value_chunk_q4_12,
    output logic [PARALLEL_ENGINES-1:0] out_valid,
    input  logic [PARALLEL_ENGINES-1:0] out_ready,
    output logic [PARALLEL_ENGINES*CHUNK_WIDTH-1:0] out_chunk_q4_12,
    output logic [PARALLEL_ENGINES-1:0] out_last,
    output logic [PARALLEL_ENGINES-1:0] busy,
    output logic [PARALLEL_ENGINES-1:0] done,
    output logic [PARALLEL_ENGINES-1:0] protocol_error
);
    for (genvar engine = 0; engine < PARALLEL_ENGINES; engine = engine + 1) begin : g_attention
        rtwsr_attention_gemv_unit #(
            .HEAD_DIM(HEAD_DIM),
            .LANES(LANES),
            .MAX_CONTEXT(MAX_CONTEXT),
            .DATA_W(DATA_W),
            .QUERY_WIDTH(QUERY_WIDTH),
            .CHUNK_WIDTH(CHUNK_WIDTH),
            .FAST_RECIPROCAL(1'b1)
        ) u_attention (
            .clk(clk),
            .rst_n(rst_n),
            .start(start[engine]),
            .active_context_tokens(active_context_tokens[engine*CONTEXT_COUNT_W +: CONTEXT_COUNT_W]),
            .query_vector_q4_12(query_vector_q4_12[engine*QUERY_WIDTH +: QUERY_WIDTH]),
            .ready(ready[engine]),
            .kv_valid(kv_valid[engine]),
            .kv_ready(kv_ready[engine]),
            .kv_key_chunk_q4_12(kv_key_chunk_q4_12[engine*CHUNK_WIDTH +: CHUNK_WIDTH]),
            .kv_value_chunk_q4_12(kv_value_chunk_q4_12[engine*CHUNK_WIDTH +: CHUNK_WIDTH]),
            .out_valid(out_valid[engine]),
            .out_ready(out_ready[engine]),
            .out_chunk_q4_12(out_chunk_q4_12[engine*CHUNK_WIDTH +: CHUNK_WIDTH]),
            .out_last(out_last[engine]),
            .busy(busy[engine]),
            .done(done[engine]),
            .protocol_error(protocol_error[engine])
        );
    end
endmodule
