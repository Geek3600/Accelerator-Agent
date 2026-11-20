`timescale 1ns / 1ps

module rtwsr_huginn_recurrent_sequencer #(
    parameter int RECURRENCES = 32,
    parameter int CORE_BLOCKS = 4
)(
    input  logic        clk,
    input  logic        rst_n,
    input  logic        start,
    input  logic [15:0] context_tokens,
    output logic        stage_valid,
    input  logic        stage_ready,
    input  logic        stage_done,
    output logic [3:0]  stage_id,
    output logic [1:0]  block_index,
    output logic [4:0]  recurrence_index,
    output logic [15:0] matrix_rows,
    output logic [15:0] matrix_columns,
    output logic [15:0] vector_length,
    output logic [15:0] active_context_tokens,
    output logic        done,
    output logic        error
);
    localparam logic [3:0] STAGE_ADAPTER = 4'd0;
    localparam logic [3:0] STAGE_NORM1 = 4'd1;
    localparam logic [3:0] STAGE_QKV = 4'd2;
    localparam logic [3:0] STAGE_ROPE_KV = 4'd3;
    localparam logic [3:0] STAGE_SCORE_SOFTMAX = 4'd4;
    localparam logic [3:0] STAGE_CONTEXT = 4'd5;
    localparam logic [3:0] STAGE_PROJ_RESIDUAL_NORM2 = 4'd6;
    localparam logic [3:0] STAGE_NORM3 = 4'd7;
    localparam logic [3:0] STAGE_GATE_UP = 4'd8;
    localparam logic [3:0] STAGE_SWIGLU = 4'd9;
    localparam logic [3:0] STAGE_DOWN_RESIDUAL_NORM4 = 4'd10;

    typedef enum logic [1:0] {IDLE, ISSUE, WAIT_DONE, COMPLETE} state_t;

    state_t state;
    logic [3:0] stage_q;
    logic [1:0] block_q;
    logic [4:0] recurrence_q;
    logic [15:0] context_q;

    assign stage_valid = (state == ISSUE);
    assign stage_id = stage_q;
    assign block_index = block_q;
    assign recurrence_index = recurrence_q;
    assign active_context_tokens = context_q;
    assign done = (state == COMPLETE);

    always_comb begin
        matrix_rows = 16'd0;
        matrix_columns = 16'd0;
        vector_length = 16'd5280;
        case (stage_q)
            STAGE_ADAPTER: begin
                matrix_rows = 16'd5280;
                matrix_columns = 16'd10560;
            end
            STAGE_NORM1, STAGE_NORM3: vector_length = 16'd5280;
            STAGE_QKV: begin
                matrix_rows = 16'd15840;
                matrix_columns = 16'd5280;
            end
            STAGE_ROPE_KV: vector_length = 16'd5280;
            STAGE_SCORE_SOFTMAX: vector_length = 16'd96;
            STAGE_CONTEXT: vector_length = 16'd5280;
            STAGE_PROJ_RESIDUAL_NORM2: begin
                matrix_rows = 16'd5280;
                matrix_columns = 16'd5280;
            end
            STAGE_GATE_UP: begin
                matrix_rows = 16'd35840;
                matrix_columns = 16'd5280;
            end
            STAGE_SWIGLU: vector_length = 16'd17920;
            STAGE_DOWN_RESIDUAL_NORM4: begin
                matrix_rows = 16'd5280;
                matrix_columns = 16'd17920;
            end
            default: begin
                matrix_rows = 16'd0;
                matrix_columns = 16'd0;
                vector_length = 16'd0;
            end
        endcase
    end

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            state <= IDLE;
            stage_q <= STAGE_ADAPTER;
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
                            stage_q <= STAGE_ADAPTER;
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
                        if (stage_q == STAGE_ADAPTER) begin
                            stage_q <= STAGE_NORM1;
                        end else if (stage_q != STAGE_DOWN_RESIDUAL_NORM4) begin
                            stage_q <= stage_q + 1'b1;
                        end else if (block_q != CORE_BLOCKS - 1) begin
                            block_q <= block_q + 1'b1;
                            stage_q <= STAGE_NORM1;
                        end else if (recurrence_q != RECURRENCES - 1) begin
                            recurrence_q <= recurrence_q + 1'b1;
                            block_q <= '0;
                            stage_q <= STAGE_ADAPTER;
                        end else begin
                            state <= COMPLETE;
                        end
                        if (!(stage_q == STAGE_DOWN_RESIDUAL_NORM4 &&
                              block_q == CORE_BLOCKS - 1 &&
                              recurrence_q == RECURRENCES - 1))
                            state <= ISSUE;
                    end
                end
                COMPLETE: begin
                    if (start) begin
                        if ((context_tokens != 16'd512) && (context_tokens != 16'd2048)) begin
                            error <= 1'b1;
                        end else begin
                            stage_q <= STAGE_ADAPTER;
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
