`timescale 1ns / 1ps

module rtwsr_recurrent_sequencer #(
    parameter logic [15:0] HIDDEN_SIZE = 16'd5280,
    parameter logic [15:0] INTERMEDIATE_SIZE = 16'd17920,
    parameter logic [15:0] QUERY_SIZE = 16'd5280,
    parameter logic [15:0] KV_SIZE = 16'd5280,
    parameter logic [15:0] HEAD_DIM = 16'd96,
    parameter logic [15:0] ATTENTION_GATE_ROWS = 16'd0,
    parameter bit HAS_PRE_ATTENTION_NORM = 1'b1,
    parameter bit HAS_PRE_FFN_NORM = 1'b1,
    parameter int CORE_BLOCKS = 4,
    parameter int RECURRENCES = 32,
    parameter int PRE_RECURRENCE_STAGE = 0,
    parameter logic [15:0] PRE_STAGE_ROWS = 16'd5280,
    parameter logic [15:0] PRE_STAGE_COLUMNS = 16'd10560,
    parameter logic [15:0] PRE_STAGE_VECTOR_LENGTH = 16'd5280,
    parameter int POST_RECURRENCE_STAGE = -1,
    parameter logic [CORE_BLOCKS-1:0] FULL_ATTENTION_MASK = {CORE_BLOCKS{1'b1}},
    parameter int SLIDING_WINDOW = 0
)(
    input  logic        clk,
    input  logic        rst_n,
    input  logic        start,
    input  logic [15:0] context_tokens,
    output logic        stage_valid,
    input  logic        stage_ready,
    input  logic        stage_done,
    output logic [3:0]  stage_id,
    output logic [5:0]  block_index,
    output logic [4:0]  recurrence_index,
    output logic [15:0] matrix_rows,
    output logic [15:0] matrix_columns,
    output logic [15:0] vector_length,
    output logic [15:0] active_context_tokens,
    output logic        attention_is_full,
    output logic        done,
    output logic        error
);
    localparam logic [3:0] STAGE_ATTN_NORM = 4'd1;
    localparam logic [3:0] STAGE_QKV = 4'd2;
    localparam logic [3:0] STAGE_ROPE_KV = 4'd3;
    localparam logic [3:0] STAGE_SCORE_SOFTMAX = 4'd4;
    localparam logic [3:0] STAGE_CONTEXT = 4'd5;
    localparam logic [3:0] STAGE_ATTN_PROJ_RESIDUAL = 4'd6;
    localparam logic [3:0] STAGE_FFN_NORM = 4'd7;
    localparam logic [3:0] STAGE_GATE_UP = 4'd8;
    localparam logic [3:0] STAGE_SWIGLU = 4'd9;
    localparam logic [3:0] STAGE_DOWN_RESIDUAL = 4'd10;
    localparam logic [3:0] STAGE_POST_RECURRENCE = 4'd11;
    localparam logic [3:0] FIRST_BLOCK_STAGE = HAS_PRE_ATTENTION_NORM ?
                                                 STAGE_ATTN_NORM : STAGE_QKV;
    localparam int BLOCK_INDEX_BITS = (CORE_BLOCKS > 1) ? $clog2(CORE_BLOCKS) : 1;

    typedef enum logic [1:0] {IDLE, ISSUE, WAIT_DONE, COMPLETE} state_t;

    state_t state;
    logic [3:0] stage_q;
    logic [5:0] block_q;
    logic [4:0] recurrence_q;
    logic [15:0] context_q;
    logic block_attention_full;
    logic [BLOCK_INDEX_BITS-1:0] block_mask_index;

    assign stage_valid = (state == ISSUE);
    assign stage_id = stage_q;
    assign block_index = block_q;
    assign recurrence_index = recurrence_q;
    assign attention_is_full = block_attention_full;
    assign block_mask_index = block_q[BLOCK_INDEX_BITS-1:0];
    assign done = (state == COMPLETE);

    always_comb begin
        matrix_rows = 16'd0;
        matrix_columns = 16'd0;
        vector_length = 16'd0;
        active_context_tokens = context_q;
        block_attention_full = 1'b1;

        if (int'(block_q) < CORE_BLOCKS)
            block_attention_full = FULL_ATTENTION_MASK[block_mask_index];

        if (PRE_RECURRENCE_STAGE >= 0 && stage_q == 4'(PRE_RECURRENCE_STAGE)) begin
            matrix_rows = PRE_STAGE_ROWS;
            matrix_columns = PRE_STAGE_COLUMNS;
            vector_length = PRE_STAGE_VECTOR_LENGTH;
        end else begin
            case (stage_q)
                STAGE_ATTN_NORM:
                    if (HAS_PRE_ATTENTION_NORM) vector_length = HIDDEN_SIZE;
                STAGE_FFN_NORM:
                    if (HAS_PRE_FFN_NORM) vector_length = HIDDEN_SIZE;
                STAGE_QKV: begin
                    matrix_rows = QUERY_SIZE + (KV_SIZE << 1);
                    matrix_columns = HIDDEN_SIZE;
                end
                STAGE_ROPE_KV: begin
                    matrix_rows = ATTENTION_GATE_ROWS;
                    if (ATTENTION_GATE_ROWS != 0)
                        matrix_columns = HIDDEN_SIZE;
                    vector_length = HIDDEN_SIZE;
                end
                STAGE_SCORE_SOFTMAX: vector_length = HEAD_DIM;
                STAGE_CONTEXT: vector_length = QUERY_SIZE;
                STAGE_ATTN_PROJ_RESIDUAL: begin
                    matrix_rows = HIDDEN_SIZE;
                    matrix_columns = QUERY_SIZE;
                end
                STAGE_GATE_UP: begin
                    matrix_rows = INTERMEDIATE_SIZE << 1;
                    matrix_columns = HIDDEN_SIZE;
                end
                STAGE_SWIGLU: vector_length = INTERMEDIATE_SIZE;
                STAGE_DOWN_RESIDUAL: begin
                    matrix_rows = HIDDEN_SIZE;
                    matrix_columns = INTERMEDIATE_SIZE;
                end
                STAGE_POST_RECURRENCE: vector_length = HIDDEN_SIZE;
                default: begin end
            endcase
        end

        if (SLIDING_WINDOW > 0 && !block_attention_full &&
            ((stage_q == STAGE_SCORE_SOFTMAX) || (stage_q == STAGE_CONTEXT)) &&
            int'(context_q) > SLIDING_WINDOW)
            active_context_tokens = 16'(SLIDING_WINDOW);
    end

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            state <= IDLE;
            stage_q <= '0;
            block_q <= '0;
            recurrence_q <= '0;
            context_q <= '0;
            error <= 1'b0;
        end else begin
            case (state)
                IDLE: begin
                    if (start) begin
                        if ((context_tokens != 16'd512) && (context_tokens != 16'd2048)) begin
                            error <= 1'b1;
                            state <= COMPLETE;
                        end else begin
                            if (PRE_RECURRENCE_STAGE >= 0)
                                stage_q <= 4'(PRE_RECURRENCE_STAGE);
                            else
                                stage_q <= FIRST_BLOCK_STAGE;
                            block_q <= '0;
                            recurrence_q <= '0;
                            context_q <= context_tokens;
                            error <= 1'b0;
                            state <= ISSUE;
                        end
                    end
                end
                ISSUE: begin
                    if (stage_ready)
                        state <= WAIT_DONE;
                end
                WAIT_DONE: begin
                    if (stage_done) begin
                        if (PRE_RECURRENCE_STAGE >= 0 && stage_q == 4'(PRE_RECURRENCE_STAGE)) begin
                            stage_q <= FIRST_BLOCK_STAGE;
                        end else if (stage_q == STAGE_ATTN_PROJ_RESIDUAL &&
                                     !HAS_PRE_FFN_NORM) begin
                            stage_q <= STAGE_GATE_UP;
                        end else if (stage_q == STAGE_DOWN_RESIDUAL) begin
                            if (int'(block_q) + 1 < CORE_BLOCKS) begin
                                block_q <= block_q + 1'b1;
                                stage_q <= FIRST_BLOCK_STAGE;
                            end else if (POST_RECURRENCE_STAGE >= 0) begin
                                stage_q <= 4'(POST_RECURRENCE_STAGE);
                            end else if (int'(recurrence_q) + 1 < RECURRENCES) begin
                                recurrence_q <= recurrence_q + 1'b1;
                                block_q <= '0;
                                if (PRE_RECURRENCE_STAGE >= 0)
                                    stage_q <= 4'(PRE_RECURRENCE_STAGE);
                                else
                                    stage_q <= FIRST_BLOCK_STAGE;
                            end else begin
                                state <= COMPLETE;
                            end
                        end else if (POST_RECURRENCE_STAGE >= 0 && stage_q == 4'(POST_RECURRENCE_STAGE)) begin
                            if (int'(recurrence_q) + 1 < RECURRENCES) begin
                                recurrence_q <= recurrence_q + 1'b1;
                                block_q <= '0;
                                if (PRE_RECURRENCE_STAGE >= 0)
                                    stage_q <= 4'(PRE_RECURRENCE_STAGE);
                                else
                                    stage_q <= FIRST_BLOCK_STAGE;
                            end else begin
                                state <= COMPLETE;
                            end
                        end else begin
                            stage_q <= stage_q + 1'b1;
                        end

                        if (!((stage_q == STAGE_DOWN_RESIDUAL &&
                               int'(block_q) + 1 == CORE_BLOCKS && POST_RECURRENCE_STAGE < 0 &&
                               int'(recurrence_q) + 1 == RECURRENCES) ||
                              (POST_RECURRENCE_STAGE >= 0 && stage_q == 4'(POST_RECURRENCE_STAGE) &&
                               int'(recurrence_q) + 1 == RECURRENCES)))
                            state <= ISSUE;
                    end
                end
                COMPLETE: begin
                    if (start) begin
                        if ((context_tokens != 16'd512) && (context_tokens != 16'd2048)) begin
                            error <= 1'b1;
                        end else begin
                            if (PRE_RECURRENCE_STAGE >= 0)
                                stage_q <= 4'(PRE_RECURRENCE_STAGE);
                            else
                                stage_q <= FIRST_BLOCK_STAGE;
                            block_q <= '0;
                            recurrence_q <= '0;
                            context_q <= context_tokens;
                            error <= 1'b0;
                            state <= ISSUE;
                        end
                    end
                end
                default: state <= IDLE;
            endcase
        end
    end
endmodule
