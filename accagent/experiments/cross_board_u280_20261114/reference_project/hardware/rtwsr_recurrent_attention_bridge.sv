`timescale 1ns / 1ps

module rtwsr_recurrent_attention_bridge #(
    parameter int QUERY_SIZE = 5280,
    parameter int KV_SIZE = 5280,
    parameter int HEAD_DIM = 96,
    parameter int QUERY_HEADS = QUERY_SIZE / HEAD_DIM,
    parameter int KV_HEADS = KV_SIZE / HEAD_DIM,
    parameter int WRITE_LANES = 96,
    parameter int LANES = 128,
    parameter int DATA_W = 16,
    parameter int HEAD_INDEX_W = (QUERY_HEADS <= 1) ? 1 : $clog2(QUERY_HEADS),
    parameter int READ_CHUNKS = (HEAD_DIM + WRITE_LANES - 1) / WRITE_LANES,
    parameter int READ_CHUNK_INDEX_W = (READ_CHUNKS <= 1) ? 1 : $clog2(READ_CHUNKS),
    parameter int ATTENTION_CHUNKS = (HEAD_DIM + LANES - 1) / LANES,
    parameter int ATTENTION_CHUNK_INDEX_W = (ATTENTION_CHUNKS <= 1) ? 1 : $clog2(ATTENTION_CHUNKS),
    parameter int QUERY_VECTOR_W = HEAD_DIM * DATA_W,
    parameter int CHUNK_W = LANES * DATA_W
)(
    input  logic                          clk,
    input  logic                          rst_n,
    input  logic                          start,
    output logic                          ready,
    output logic                          done,
    output logic                          protocol_error,

    input  logic                          qkv_valid,
    output logic                          qkv_read_start,
    output logic [HEAD_INDEX_W-1:0]       qkv_read_head,
    output logic [READ_CHUNK_INDEX_W-1:0] qkv_read_chunk,
    input  logic                          qkv_read_ready,
    input  logic                          qkv_read_valid,
    output logic                          qkv_read_done,
    input  logic [WRITE_LANES*DATA_W-1:0] qkv_query_chunk,
    input  logic [WRITE_LANES*DATA_W-1:0] qkv_key_chunk,
    input  logic [WRITE_LANES*DATA_W-1:0] qkv_value_chunk,

    output logic                          rope_start,
    input  logic                          rope_ready,
    output logic [QUERY_VECTOR_W-1:0]     rope_query,
    output logic [QUERY_VECTOR_W-1:0]     rope_key,
    output logic [QUERY_VECTOR_W-1:0]     rope_value,
    input  logic                          rope_query_valid,
    input  logic [QUERY_VECTOR_W-1:0]     rope_query_rotated,
    input  logic                          rope_done,
    input  logic                          rope_error,
    input  logic                          rope_kv_valid,
    output logic                          rope_kv_ready,
    input  logic [CHUNK_W-1:0]           rope_kv_key,
    input  logic [CHUNK_W-1:0]           rope_kv_value,

    output logic                          attention_start,
    input  logic                          attention_ready,
    output logic [QUERY_VECTOR_W-1:0]     attention_query,
    input  logic                          attention_kv_ready,
    output logic                          attention_kv_valid,
    output logic [CHUNK_W-1:0]           attention_kv_key,
    output logic [CHUNK_W-1:0]           attention_kv_value,
    input  logic                          attention_done,
    input  logic                          attention_error,
    input  logic                          attention_out_valid,
    output logic                          attention_out_ready,
    input  logic [CHUNK_W-1:0]           attention_out,
    output logic                          context_valid,
    output logic [HEAD_INDEX_W-1:0]      context_head,
    output logic [ATTENTION_CHUNK_INDEX_W-1:0] context_chunk,
    output logic                          context_last,
    output logic [CHUNK_W-1:0]           context_data
);
    typedef enum logic [3:0] {
        IDLE,
        READ_ISSUE,
        READ_CAPTURE,
        ROPE_LAUNCH,
        RUN_HEAD,
        COMPLETE,
        FAILED
    } state_t;

    state_t state_q;
    logic [HEAD_INDEX_W-1:0] head_q;
    logic [READ_CHUNK_INDEX_W-1:0] read_chunk_q;
    logic [ATTENTION_CHUNK_INDEX_W-1:0] attention_chunk_q;
    logic [QUERY_VECTOR_W-1:0] query_q;
    logic [QUERY_VECTOR_W-1:0] key_q;
    logic [QUERY_VECTOR_W-1:0] value_q;
    logic rope_done_q;
    logic attention_done_q;
    logic protocol_error_q;

    assign ready = (state_q == IDLE) && qkv_valid;
    assign done = state_q == COMPLETE || state_q == FAILED;
    assign protocol_error = protocol_error_q;
    assign qkv_read_head = head_q;
    assign qkv_read_chunk = read_chunk_q;
    assign qkv_read_start = state_q == READ_ISSUE && qkv_read_ready;
    assign qkv_read_done = state_q == READ_CAPTURE && qkv_read_valid;
    assign rope_start = state_q == ROPE_LAUNCH && rope_ready;
    assign rope_query = query_q;
    assign rope_key = key_q;
    assign rope_value = value_q;
    assign attention_start = state_q == RUN_HEAD && rope_query_valid && attention_ready;
    assign attention_query = rope_query_rotated;
    assign attention_kv_valid = rope_kv_valid;
    assign attention_kv_key = rope_kv_key;
    assign attention_kv_value = rope_kv_value;
    assign rope_kv_ready = attention_kv_ready;
    assign attention_out_ready = 1'b1;
    assign context_valid = attention_out_valid;
    assign context_head = head_q;
    assign context_chunk = attention_chunk_q;
    assign context_last = context_valid &&
        (head_q == HEAD_INDEX_W'(QUERY_HEADS - 1)) &&
        (attention_chunk_q == ATTENTION_CHUNK_INDEX_W'(ATTENTION_CHUNKS - 1));
    assign context_data = attention_out;

    always_ff @(posedge clk) begin
        integer lane;
        integer dimension;
        logic rope_finished;
        logic attention_finished;
        if (!rst_n) begin
            state_q <= IDLE;
            head_q <= '0;
            read_chunk_q <= '0;
            attention_chunk_q <= '0;
            query_q <= '0;
            key_q <= '0;
            value_q <= '0;
            rope_done_q <= 1'b0;
            attention_done_q <= 1'b0;
            protocol_error_q <= 1'b0;
        end else begin
            if (rope_error || attention_error) begin
                protocol_error_q <= 1'b1;
                state_q <= FAILED;
            end else begin
                case (state_q)
                    IDLE: begin
                        if (start && qkv_valid) begin
                            head_q <= '0;
                            read_chunk_q <= '0;
                            attention_chunk_q <= '0;
                            query_q <= '0;
                            key_q <= '0;
                            value_q <= '0;
                            rope_done_q <= 1'b0;
                            attention_done_q <= 1'b0;
                            protocol_error_q <= 1'b0;
                            state_q <= READ_ISSUE;
                        end
                    end
                    READ_ISSUE: begin
                        if (qkv_read_start)
                            state_q <= READ_CAPTURE;
                    end
                    READ_CAPTURE: begin
                        if (qkv_read_valid) begin
                            for (lane = 0; lane < WRITE_LANES; lane = lane + 1) begin
                                dimension = int'(read_chunk_q) * WRITE_LANES + lane;
                                if (dimension < HEAD_DIM) begin
                                    query_q[dimension*DATA_W +: DATA_W] <=
                                        qkv_query_chunk[lane*DATA_W +: DATA_W];
                                    key_q[dimension*DATA_W +: DATA_W] <=
                                        qkv_key_chunk[lane*DATA_W +: DATA_W];
                                    value_q[dimension*DATA_W +: DATA_W] <=
                                        qkv_value_chunk[lane*DATA_W +: DATA_W];
                                end
                            end
                            if (read_chunk_q == READ_CHUNK_INDEX_W'(READ_CHUNKS - 1)) begin
                                state_q <= ROPE_LAUNCH;
                            end else begin
                                read_chunk_q <= read_chunk_q + 1'b1;
                                state_q <= READ_ISSUE;
                            end
                        end
                    end
                    ROPE_LAUNCH: begin
                        if (rope_start) begin
                            attention_chunk_q <= '0;
                            rope_done_q <= 1'b0;
                            attention_done_q <= 1'b0;
                            state_q <= RUN_HEAD;
                        end
                    end
                    RUN_HEAD: begin
                        if (context_valid && attention_out_ready &&
                            attention_chunk_q != ATTENTION_CHUNK_INDEX_W'(ATTENTION_CHUNKS - 1))
                            attention_chunk_q <= attention_chunk_q + 1'b1;

                        rope_finished = rope_done_q || rope_done;
                        attention_finished = attention_done_q || attention_done;
                        if (rope_done)
                            rope_done_q <= 1'b1;
                        if (attention_done)
                            attention_done_q <= 1'b1;
                        if (rope_finished && attention_finished) begin
                            rope_done_q <= 1'b0;
                            attention_done_q <= 1'b0;
                            if (head_q == HEAD_INDEX_W'(QUERY_HEADS - 1)) begin
                                state_q <= COMPLETE;
                            end else begin
                                head_q <= head_q + 1'b1;
                                read_chunk_q <= '0;
                                query_q <= '0;
                                key_q <= '0;
                                value_q <= '0;
                                state_q <= READ_ISSUE;
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
    end

    initial begin
        if (QUERY_SIZE < 1 || KV_SIZE < 1 || HEAD_DIM < 1 ||
            QUERY_SIZE % HEAD_DIM != 0 || KV_SIZE % HEAD_DIM != 0 ||
            QUERY_HEADS % KV_HEADS != 0 || WRITE_LANES != 96 || LANES != 128 || DATA_W != 16)
            $error("Plan 6 attention bridge requires divisible query/KV heads and 96/128 lane widths");
    end
endmodule
