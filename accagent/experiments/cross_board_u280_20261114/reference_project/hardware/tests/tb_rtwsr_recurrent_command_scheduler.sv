`timescale 1ns / 1ps

module tb_rtwsr_recurrent_command_scheduler #(
    parameter int MODEL_ID = 0
);
    logic clk = 1'b0;
    logic rst_n = 1'b0;
    logic start = 1'b0;
    logic [15:0] context_tokens = '0;
    logic command_valid;
    logic command_ready;
    logic command_done;
    logic [4:0] command_id;
    logic [3:0] command_stage;
    logic [5:0] block_index;
    logic [4:0] recurrence_index;
    logic [1:0] command_index;
    logic [15:0] matrix_rows;
    logic [15:0] matrix_columns;
    logic [15:0] vector_length;
    logic [15:0] active_context_tokens;
    logic attention_is_full;
    logic done;
    logic error;
    logic linear_engine_ready = 1'b0;
    logic linear_engine_done = 1'b0;
    logic operator_ready = 1'b0;
    logic operator_done = 1'b0;
    logic linear_engine_valid;
    logic [4:0] linear_engine_command_id;
    logic [5:0] linear_engine_block_index;
    logic [4:0] linear_engine_recurrence_index;
    logic [15:0] linear_engine_rows;
    logic [15:0] linear_engine_columns;
    integer command_total;
    integer stage_total;
    integer expected_command_total;
    integer expected_stage_total;

    localparam int HIDDEN_SIZE = MODEL_ID == 0 ? 5280 : MODEL_ID == 1 ? 2048 : 2560;
    localparam int INTERMEDIATE_SIZE = MODEL_ID == 0 ? 17920 : MODEL_ID == 1 ? 5632 : 7168;
    localparam int QUERY_SIZE = MODEL_ID == 0 ? 5280 : MODEL_ID == 1 ? 2048 : 4096;
    localparam int KV_SIZE = MODEL_ID == 2 ? 1024 : QUERY_SIZE;
    localparam int HEAD_DIM = MODEL_ID == 0 ? 96 : MODEL_ID == 1 ? 128 : 256;
    localparam int BLOCKS = MODEL_ID == 0 ? 4 : MODEL_ID == 1 ? 24 : 20;
    localparam int RECURRENCES = MODEL_ID == 0 ? 32 : 4;
    localparam int FULL_ATTENTION_MASK = MODEL_ID == 2 ? 20'h88888 : 20'hfffff;

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

    always #5 clk = ~clk;

    rtwsr_recurrent_command_scheduler #(.MODEL_ID(MODEL_ID)) dut (.*);
    rtwsr_linear_command_dispatch u_dispatch (
        .command_valid(command_valid),
        .command_id(command_id),
        .block_index(block_index),
        .recurrence_index(recurrence_index),
        .matrix_rows(matrix_rows),
        .matrix_columns(matrix_columns),
        .linear_engine_ready(linear_engine_ready),
        .linear_engine_done(linear_engine_done),
        .operator_ready(operator_ready),
        .operator_done(operator_done),
        .linear_engine_valid(linear_engine_valid),
        .linear_engine_command_id(linear_engine_command_id),
        .linear_engine_block_index(linear_engine_block_index),
        .linear_engine_recurrence_index(linear_engine_recurrence_index),
        .linear_engine_rows(linear_engine_rows),
        .linear_engine_columns(linear_engine_columns),
        .scheduler_command_ready(command_ready),
        .scheduler_command_done(command_done)
    );

    function automatic integer command_count(input integer stage);
        begin
            if (stage == 2 && MODEL_ID != 0)
                command_count = 3;
            else if (stage == 8)
                command_count = 2;
            else if ((stage == 3 || stage == 9) && MODEL_ID == 2)
                command_count = 2;
            else if (stage == 6 || stage == 10)
                command_count = 2;
            else
                command_count = 1;
        end
    endfunction

    task automatic check_command(
        input integer stage,
        input integer command_number,
        input integer expected_block,
        input integer expected_recurrence,
        input integer context_length
    );
        integer expected_id;
        integer expected_rows;
        integer expected_columns;
        integer expected_vector;
        integer expected_context;
        logic expected_full;
        logic expected_linear;
        begin
            expected_id = CMD_PRE_ATTN_NORM;
            expected_rows = 0;
            expected_columns = 0;
            expected_vector = 0;
            expected_context = context_length;
            expected_full = FULL_ATTENTION_MASK[expected_block];

            case (stage)
                0: if (MODEL_ID == 0) begin
                    expected_id = CMD_ADAPTER;
                    expected_rows = HIDDEN_SIZE;
                    expected_columns = 2 * HIDDEN_SIZE;
                    expected_vector = 2 * HIDDEN_SIZE;
                end else begin
                    expected_id = CMD_DORY_INPUT;
                    expected_vector = HIDDEN_SIZE;
                end
                1: begin expected_id = CMD_PRE_ATTN_NORM; expected_vector = HIDDEN_SIZE; end
                2: begin
                    if (MODEL_ID == 0) begin
                        expected_id = CMD_QKV;
                        expected_rows = QUERY_SIZE + 2 * KV_SIZE;
                    end else if (command_number == 0) begin
                        expected_id = CMD_Q_PROJ;
                        expected_rows = QUERY_SIZE;
                    end else if (command_number == 1) begin
                        expected_id = CMD_K_PROJ;
                        expected_rows = KV_SIZE;
                    end else begin
                        expected_id = CMD_V_PROJ;
                        expected_rows = KV_SIZE;
                    end
                    expected_columns = HIDDEN_SIZE;
                end
                3: if (MODEL_ID == 2 && command_number == 0) begin
                    expected_id = CMD_G_PROJ;
                    expected_rows = 4096;
                    expected_columns = HIDDEN_SIZE;
                end else begin
                    expected_id = CMD_ROPE_KV;
                    expected_vector = QUERY_SIZE + KV_SIZE;
                end
                4: begin
                    expected_id = CMD_SCORE_SOFTMAX;
                    expected_vector = HEAD_DIM;
                    if (MODEL_ID == 2 && !expected_full && expected_context > 1024)
                        expected_context = 1024;
                end
                5: begin
                    expected_id = MODEL_ID == 2 ? CMD_CONTEXT_GATE_NORM : CMD_CONTEXT;
                    expected_vector = QUERY_SIZE;
                    if (MODEL_ID == 2 && !expected_full && expected_context > 1024)
                        expected_context = 1024;
                end
                6: if (command_number == 0) begin
                    expected_id = CMD_O_PROJ;
                    expected_rows = HIDDEN_SIZE;
                    expected_columns = QUERY_SIZE;
                end else begin
                    expected_id = CMD_ATTN_POST;
                    expected_vector = HIDDEN_SIZE;
                end
                7: begin expected_id = CMD_PRE_FFN_NORM; expected_vector = HIDDEN_SIZE; end
                8: begin
                    if (command_number == 0) begin
                        expected_id = CMD_GATE_PROJ;
                        expected_rows = INTERMEDIATE_SIZE;
                    end else begin
                        expected_id = CMD_UP_PROJ;
                        expected_rows = INTERMEDIATE_SIZE;
                    end
                    expected_columns = HIDDEN_SIZE;
                end
                9: begin
                    if (MODEL_ID == 2 && command_number == 1)
                        expected_id = CMD_PRE_DOWN_JUSTNORM;
                    else
                        expected_id = CMD_SWIGLU;
                    expected_vector = INTERMEDIATE_SIZE;
                end
                10: if (command_number == 0) begin
                    expected_id = CMD_DOWN;
                    expected_rows = HIDDEN_SIZE;
                    expected_columns = INTERMEDIATE_SIZE;
                end else begin
                    expected_id = CMD_MLP_POST;
                    expected_vector = HIDDEN_SIZE;
                end
                11: begin expected_id = CMD_RECURRENCE_POST; expected_vector = HIDDEN_SIZE; end
                default: $fatal(1, "unexpected stage %0d", stage);
            endcase

            expected_linear = expected_id == CMD_ADAPTER || expected_id == CMD_QKV ||
                              expected_id == CMD_G_PROJ || expected_id == CMD_O_PROJ ||
                              expected_id == CMD_DOWN || expected_id == CMD_Q_PROJ ||
                              expected_id == CMD_K_PROJ || expected_id == CMD_V_PROJ ||
                              expected_id == CMD_GATE_PROJ || expected_id == CMD_UP_PROJ;

            @(negedge clk);
            if (!command_valid || command_id != expected_id || command_stage != stage ||
                command_index != command_number || block_index != expected_block ||
                recurrence_index != expected_recurrence || matrix_rows != expected_rows ||
                matrix_columns != expected_columns || vector_length != expected_vector ||
                active_context_tokens != expected_context || attention_is_full != expected_full || error)
                $fatal(1, "command mismatch m=%0d r=%0d b=%0d s=%0d i=%0d id=%0d dims=%0dx%0d v=%0d ctx=%0d full=%0d",
                       MODEL_ID, recurrence_index, block_index, command_stage, command_index,
                       command_id, matrix_rows, matrix_columns, vector_length,
                       active_context_tokens, attention_is_full);

            linear_engine_ready = expected_linear;
            operator_ready = !expected_linear;
            #1;
            if (linear_engine_valid != expected_linear ||
                command_ready != (expected_linear ? linear_engine_ready : operator_ready) ||
                linear_engine_command_id != (expected_linear ? command_id : 5'd0) ||
                linear_engine_block_index != (expected_linear ? block_index : 6'd0) ||
                linear_engine_recurrence_index != (expected_linear ? recurrence_index : 5'd0) ||
                linear_engine_rows != (expected_linear ? expected_rows : 16'd0) ||
                linear_engine_columns != (expected_linear ? expected_columns : 16'd0))
                $fatal(1, "shared engine descriptor mismatch m=%0d id=%0d rows=%0d cols=%0d",
                       MODEL_ID, command_id, linear_engine_rows, linear_engine_columns);

            @(posedge clk);
            #1 begin
                linear_engine_ready = 1'b0;
                operator_ready = 1'b0;
            end
            repeat (2) @(posedge clk);
            #1 begin
                linear_engine_done = expected_linear;
                operator_done = !expected_linear;
            end
            @(posedge clk);
            #1 begin
                linear_engine_done = 1'b0;
                operator_done = 1'b0;
            end
            command_total = command_total + 1;
        end
    endtask

    task automatic consume_stage(
        input integer stage,
        input integer expected_block,
        input integer expected_recurrence,
        input integer context_length
    );
        integer command_number;
        begin
            wait (command_valid);
            @(negedge clk);
            if (!command_valid || command_stage != stage || block_index != expected_block ||
                recurrence_index != expected_recurrence)
                $fatal(1, "stage mismatch m=%0d r=%0d b=%0d expected_s=%0d got_s=%0d",
                       MODEL_ID, recurrence_index, block_index, stage, command_stage);

            for (command_number = 0; command_number < command_count(stage); command_number = command_number + 1)
                check_command(stage, command_number, expected_block,
                              expected_recurrence, context_length);

            stage_total = stage_total + 1;
        end
    endtask

    task automatic reset_core;
        begin
            rst_n = 1'b0;
            repeat (2) @(posedge clk);
            @(negedge clk);
            rst_n = 1'b1;
        end
    endtask

    task automatic run_context(input integer context_length);
        integer recurrence;
        integer block;
        integer stage;
        integer commands_before;
        integer stages_before;
        begin
            reset_core();
            commands_before = command_total;
            stages_before = stage_total;
            @(negedge clk);
            context_tokens = context_length;
            start = 1'b1;
            @(posedge clk);
            #1 start = 1'b0;

            for (recurrence = 0; recurrence < RECURRENCES; recurrence = recurrence + 1) begin
                if (MODEL_ID != 1)
                    consume_stage(0, 0, recurrence, context_length);
                for (block = 0; block < BLOCKS; block = block + 1) begin
                    for (stage = 1; stage <= 10; stage = stage + 1) begin
                        if (!((MODEL_ID == 2) && (stage == 1 || stage == 7)))
                            consume_stage(stage, block, recurrence, context_length);
                    end
                end
                if (MODEL_ID != 0)
                    consume_stage(11, BLOCKS - 1, recurrence, context_length);
            end

            expected_command_total = MODEL_ID == 0 ? 1696 : MODEL_ID == 1 ? 1444 : 1208;
            expected_stage_total = MODEL_ID == 0 ? 1312 : MODEL_ID == 1 ? 964 : 648;
            wait (done);
            @(negedge clk);
            if (!done || error || command_total - commands_before != expected_command_total ||
                stage_total - stages_before != expected_stage_total)
                $fatal(1, "core completion mismatch m=%0d ctx=%0d done=%0d error=%0d commands=%0d stages=%0d",
                       MODEL_ID, context_length, done, error,
                       command_total - commands_before, stage_total - stages_before);
        end
    endtask

    initial begin
        command_total = 0;
        stage_total = 0;
        linear_engine_ready = 1'b0;
        linear_engine_done = 1'b0;
        operator_ready = 1'b0;
        operator_done = 1'b0;
        run_context(512);
        run_context(2048);

        reset_core();
        @(negedge clk);
        context_tokens = 1024;
        start = 1'b1;
        @(posedge clk);
        #1 start = 1'b0;
        @(negedge clk);
        if (!done || !error)
            $fatal(1, "unsupported context must finish with error");

        $display("PASS: full command schedule model=%0d stages=%0d commands=%0d at contexts 512 and 2048",
                 MODEL_ID, expected_stage_total, expected_command_total);
        $finish;
    end
endmodule
