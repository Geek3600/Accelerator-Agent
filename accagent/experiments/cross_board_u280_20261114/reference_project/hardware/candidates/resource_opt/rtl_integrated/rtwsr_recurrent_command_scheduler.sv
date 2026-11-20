`timescale 1ns / 1ps

module rtwsr_recurrent_command_scheduler #(
    parameter int MODEL_ID = 0,
    parameter int RECURRENCES_OVERRIDE = 0
)(
    input  logic        clk,
    input  logic        rst_n,
    input  logic        start,
    input  logic [15:0] context_tokens,
    output logic        command_valid,
    input  logic        command_ready,
    input  logic        command_done,
    output logic [4:0]  command_id,
    output logic [3:0]  command_stage,
    output logic [5:0]  block_index,
    output logic [4:0]  recurrence_index,
    output logic [1:0]  command_index,
    output logic [15:0] matrix_rows,
    output logic [15:0] matrix_columns,
    output logic [15:0] vector_length,
    output logic [15:0] active_context_tokens,
    output logic        attention_is_full,
    output logic        done,
    output logic        error
);
    localparam int MODEL_HUGINN = 0;
    localparam int MODEL_OURO = 1;
    localparam int MODEL_DORY = 2;

    localparam logic [4:0] CMD_ADAPTER = 5'd0;
    localparam logic [4:0] CMD_DORY_INPUT = 5'd1;
    localparam logic [4:0] CMD_PRE_ATTN_NORM = 5'd2;
    localparam logic [4:0] CMD_QKV = 5'd3;
    localparam logic [4:0] CMD_G_PROJ = 5'd4;
    localparam logic [4:0] CMD_ROPE_KV = 5'd5;
    localparam logic [4:0] CMD_SCORE_SOFTMAX = 5'd6;
    localparam logic [4:0] CMD_CONTEXT = 5'd7;
    localparam logic [4:0] CMD_CONTEXT_GATE_NORM = 5'd8;
    localparam logic [4:0] CMD_O_PROJ = 5'd9;
    localparam logic [4:0] CMD_ATTN_POST = 5'd10;
    localparam logic [4:0] CMD_PRE_FFN_NORM = 5'd11;
    localparam logic [4:0] CMD_SWIGLU = 5'd13;
    localparam logic [4:0] CMD_PRE_DOWN_JUSTNORM = 5'd14;
    localparam logic [4:0] CMD_DOWN = 5'd15;
    localparam logic [4:0] CMD_MLP_POST = 5'd16;
    localparam logic [4:0] CMD_RECURRENCE_POST = 5'd17;
    localparam logic [4:0] CMD_Q_PROJ = 5'd18;
    localparam logic [4:0] CMD_K_PROJ = 5'd19;
    localparam logic [4:0] CMD_V_PROJ = 5'd20;
    localparam logic [4:0] CMD_GATE_PROJ = 5'd21;
    localparam logic [4:0] CMD_UP_PROJ = 5'd22;

    localparam logic [15:0] HIDDEN_SIZE = MODEL_ID == MODEL_HUGINN ? 16'd5280 :
                                           MODEL_ID == MODEL_OURO ? 16'd2048 : 16'd2560;
    localparam logic [15:0] INTERMEDIATE_SIZE = MODEL_ID == MODEL_HUGINN ? 16'd17920 :
                                                MODEL_ID == MODEL_OURO ? 16'd5632 : 16'd7168;
    localparam logic [15:0] QUERY_SIZE = MODEL_ID == MODEL_HUGINN ? 16'd5280 :
                                         MODEL_ID == MODEL_OURO ? 16'd2048 : 16'd4096;
    localparam logic [15:0] KV_SIZE = MODEL_ID == MODEL_DORY ? 16'd1024 : QUERY_SIZE;
    localparam logic [15:0] HEAD_DIM = MODEL_ID == MODEL_HUGINN ? 16'd96 :
                                       MODEL_ID == MODEL_OURO ? 16'd128 : 16'd256;
    localparam logic [15:0] ATTENTION_GATE_ROWS = MODEL_ID == MODEL_DORY ? 16'd4096 : 16'd0;
    localparam int CORE_BLOCKS = MODEL_ID == MODEL_HUGINN ? 4 :
                                 MODEL_ID == MODEL_OURO ? 24 : 20;
    localparam int RECURRENCES = RECURRENCES_OVERRIDE > 0 ? RECURRENCES_OVERRIDE :
                                 MODEL_ID == MODEL_HUGINN ? 32 : 4;
    localparam int PRE_STAGE = MODEL_ID == MODEL_OURO ? -1 : 0;
    localparam int POST_STAGE = MODEL_ID == MODEL_HUGINN ? -1 : 11;
    localparam logic [19:0] FULL_MASK = MODEL_ID == MODEL_DORY ? 20'h88888 : 20'hfffff;

    typedef enum logic [1:0] {IDLE, ISSUE_COMMAND, WAIT_COMMAND} state_t;

    state_t state;
    logic stage_valid;
    logic stage_ready;
    logic stage_done;
    logic [3:0] stage_id;
    logic [5:0] stage_block;
    logic [4:0] stage_recurrence;
    logic [15:0] stage_rows;
    logic [15:0] stage_columns;
    logic [15:0] stage_vector_length;
    logic [15:0] stage_context_tokens;
    logic stage_attention_is_full;
    logic [3:0] active_stage_q;
    logic [5:0] active_block_q;
    logic [4:0] active_recurrence_q;
    logic [1:0] active_command_index_q;
    logic [1:0] active_command_count_q;
    logic stage_done_q;

    function automatic logic [1:0] command_count(input logic [3:0] stage);
        begin
            case (stage)
                4'd2: command_count = (MODEL_ID == MODEL_HUGINN) ? 2'd1 : 2'd3;
                4'd3: command_count = (MODEL_ID == MODEL_DORY) ? 2'd2 : 2'd1;
                4'd6, 4'd10: command_count = 2'd2;
                4'd8: command_count = 2'd2;
                4'd9: command_count = (MODEL_ID == MODEL_DORY) ? 2'd2 : 2'd1;
                default: command_count = 2'd1;
            endcase
        end
    endfunction

    assign command_valid = (state == ISSUE_COMMAND);
    assign command_stage = active_stage_q;
    assign block_index = active_block_q;
    assign recurrence_index = active_recurrence_q;
    assign command_index = active_command_index_q;
    assign active_context_tokens = stage_context_tokens;
    assign attention_is_full = stage_attention_is_full;
    assign stage_ready = (state == IDLE);
    assign stage_done = stage_done_q;

    rtwsr_recurrent_sequencer #(
        .HIDDEN_SIZE(HIDDEN_SIZE),
        .INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),
        .QUERY_SIZE(QUERY_SIZE),
        .KV_SIZE(KV_SIZE),
        .HEAD_DIM(HEAD_DIM),
        .ATTENTION_GATE_ROWS(ATTENTION_GATE_ROWS),
        .HAS_PRE_ATTENTION_NORM(MODEL_ID != MODEL_DORY),
        .HAS_PRE_FFN_NORM(MODEL_ID != MODEL_DORY),
        .CORE_BLOCKS(CORE_BLOCKS),
        .RECURRENCES(RECURRENCES),
        .PRE_RECURRENCE_STAGE(PRE_STAGE),
        .PRE_STAGE_ROWS(MODEL_ID == MODEL_HUGINN ? 16'd5280 : 16'd0),
        .PRE_STAGE_COLUMNS(MODEL_ID == MODEL_HUGINN ? 16'd10560 : 16'd0),
        .PRE_STAGE_VECTOR_LENGTH(MODEL_ID == MODEL_DORY ? HIDDEN_SIZE : 16'd5280),
        .POST_RECURRENCE_STAGE(POST_STAGE),
        .FULL_ATTENTION_MASK(CORE_BLOCKS'(FULL_MASK)),
        .SLIDING_WINDOW(MODEL_ID == MODEL_DORY ? 1024 : 0)
    ) u_recurrent_sequencer (
        .clk(clk),
        .rst_n(rst_n),
        .start(start),
        .context_tokens(context_tokens),
        .stage_valid(stage_valid),
        .stage_ready(stage_ready),
        .stage_done(stage_done),
        .stage_id(stage_id),
        .block_index(stage_block),
        .recurrence_index(stage_recurrence),
        .matrix_rows(stage_rows),
        .matrix_columns(stage_columns),
        .vector_length(stage_vector_length),
        .active_context_tokens(stage_context_tokens),
        .attention_is_full(stage_attention_is_full),
        .done(done),
        .error(error)
    );

    always_comb begin
        command_id = CMD_PRE_ATTN_NORM;
        matrix_rows = 16'd0;
        matrix_columns = 16'd0;
        vector_length = 16'd0;

        case (active_stage_q)
            4'd0: begin
                if (MODEL_ID == MODEL_HUGINN) begin
                    command_id = CMD_ADAPTER;
                    matrix_rows = HIDDEN_SIZE;
                    matrix_columns = HIDDEN_SIZE << 1;
                    vector_length = HIDDEN_SIZE << 1;
                end else begin
                    command_id = CMD_DORY_INPUT;
                    vector_length = HIDDEN_SIZE;
                end
            end
            4'd1: begin
                command_id = CMD_PRE_ATTN_NORM;
                vector_length = HIDDEN_SIZE;
            end
            4'd2: begin
                if (MODEL_ID == MODEL_HUGINN) begin
                    command_id = CMD_QKV;
                    matrix_rows = QUERY_SIZE + (KV_SIZE << 1);
                end else begin
                    case (active_command_index_q)
                        2'd0: begin command_id = CMD_Q_PROJ; matrix_rows = QUERY_SIZE; end
                        2'd1: begin command_id = CMD_K_PROJ; matrix_rows = KV_SIZE; end
                        default: begin command_id = CMD_V_PROJ; matrix_rows = KV_SIZE; end
                    endcase
                end
                matrix_columns = HIDDEN_SIZE;
            end
            4'd3: begin
                if (MODEL_ID == MODEL_DORY && active_command_index_q == 0) begin
                    command_id = CMD_G_PROJ;
                    matrix_rows = ATTENTION_GATE_ROWS;
                    matrix_columns = HIDDEN_SIZE;
                end else begin
                    command_id = CMD_ROPE_KV;
                    vector_length = QUERY_SIZE + KV_SIZE;
                end
            end
            4'd4: begin
                command_id = CMD_SCORE_SOFTMAX;
                vector_length = HEAD_DIM;
            end
            4'd5: begin
                command_id = MODEL_ID == MODEL_DORY ? CMD_CONTEXT_GATE_NORM : CMD_CONTEXT;
                vector_length = QUERY_SIZE;
            end
            4'd6: begin
                if (active_command_index_q == 0) begin
                    command_id = CMD_O_PROJ;
                    matrix_rows = HIDDEN_SIZE;
                    matrix_columns = QUERY_SIZE;
                end else begin
                    command_id = CMD_ATTN_POST;
                    vector_length = HIDDEN_SIZE;
                end
            end
            4'd7: begin
                command_id = CMD_PRE_FFN_NORM;
                vector_length = HIDDEN_SIZE;
            end
            4'd8: begin
                if (active_command_index_q == 0) begin
                    command_id = CMD_GATE_PROJ;
                    matrix_rows = INTERMEDIATE_SIZE;
                end else begin
                    command_id = CMD_UP_PROJ;
                    matrix_rows = INTERMEDIATE_SIZE;
                end
                matrix_columns = HIDDEN_SIZE;
            end
            4'd9: begin
                if (MODEL_ID == MODEL_DORY && active_command_index_q == 1)
                    command_id = CMD_PRE_DOWN_JUSTNORM;
                else
                    command_id = CMD_SWIGLU;
                vector_length = INTERMEDIATE_SIZE;
            end
            4'd10: begin
                if (active_command_index_q == 0) begin
                    command_id = CMD_DOWN;
                    matrix_rows = HIDDEN_SIZE;
                    matrix_columns = INTERMEDIATE_SIZE;
                end else begin
                    command_id = CMD_MLP_POST;
                    vector_length = HIDDEN_SIZE;
                end
            end
            4'd11: begin
                command_id = CMD_RECURRENCE_POST;
                vector_length = HIDDEN_SIZE;
            end
            default: begin end
        endcase
    end

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            state <= IDLE;
            active_stage_q <= '0;
            active_block_q <= '0;
            active_recurrence_q <= '0;
            active_command_index_q <= '0;
            active_command_count_q <= '0;
            stage_done_q <= 1'b0;
        end else begin
            stage_done_q <= 1'b0;
            if (stage_valid && stage_ready) begin
                active_stage_q <= stage_id;
                active_block_q <= stage_block;
                active_recurrence_q <= stage_recurrence;
                active_command_index_q <= '0;
                active_command_count_q <= command_count(stage_id);
                state <= ISSUE_COMMAND;
            end else begin
                case (state)
                    ISSUE_COMMAND: begin
                        if (command_ready)
                            state <= WAIT_COMMAND;
                    end
                    WAIT_COMMAND: begin
                        if (command_done) begin
                            if (active_command_index_q + 1'b1 < active_command_count_q) begin
                                active_command_index_q <= active_command_index_q + 1'b1;
                                state <= ISSUE_COMMAND;
                            end else begin
                                state <= IDLE;
                                stage_done_q <= 1'b1;
                            end
                        end
                    end
                    default: state <= IDLE;
                endcase
            end
        end
    end

    initial begin
        if (MODEL_ID < MODEL_HUGINN || MODEL_ID > MODEL_DORY)
            $error("MODEL_ID must select Huginn, Ouro, or Dory");
    end
endmodule
