`timescale 1ns / 1ps

module tb_rtwsr_recurrent_sequencer #(
    parameter int HIDDEN_SIZE = 5280,
    parameter int INTERMEDIATE_SIZE = 17920,
    parameter int QUERY_SIZE = 5280,
    parameter int KV_SIZE = 5280,
    parameter int HEAD_DIM = 96,
    parameter int ATTENTION_GATE_ROWS = 0,
    parameter bit HAS_PRE_ATTENTION_NORM = 1'b1,
    parameter bit HAS_PRE_FFN_NORM = 1'b1,
    parameter int CORE_BLOCKS = 4,
    parameter int RECURRENCES = 32,
    parameter int PRE_RECURRENCE_STAGE = 0,
    parameter int PRE_STAGE_ROWS = 5280,
    parameter int PRE_STAGE_COLUMNS = 10560,
    parameter int PRE_STAGE_VECTOR_LENGTH = 5280,
    parameter int POST_RECURRENCE_STAGE = -1,
    parameter logic [CORE_BLOCKS-1:0] FULL_ATTENTION_MASK = {CORE_BLOCKS{1'b1}},
    parameter int SLIDING_WINDOW = 0
);
    logic clk = 1'b0;
    logic rst_n = 1'b0;
    logic start = 1'b0;
    logic [15:0] context_tokens = '0;
    logic stage_valid;
    logic stage_ready = 1'b0;
    logic stage_done = 1'b0;
    logic [3:0] stage_id;
    logic [5:0] block_index;
    logic [4:0] recurrence_index;
    logic [15:0] matrix_rows;
    logic [15:0] matrix_columns;
    logic [15:0] vector_length;
    logic [15:0] active_context_tokens;
    logic attention_is_full;
    logic done;
    logic error;
    integer event_count;
    integer expected_events;

    always #5 clk = ~clk;

    rtwsr_recurrent_sequencer #(
        .HIDDEN_SIZE(HIDDEN_SIZE),
        .INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),
        .QUERY_SIZE(QUERY_SIZE),
        .KV_SIZE(KV_SIZE),
        .HEAD_DIM(HEAD_DIM),
        .ATTENTION_GATE_ROWS(ATTENTION_GATE_ROWS),
        .HAS_PRE_ATTENTION_NORM(HAS_PRE_ATTENTION_NORM),
        .HAS_PRE_FFN_NORM(HAS_PRE_FFN_NORM),
        .CORE_BLOCKS(CORE_BLOCKS),
        .RECURRENCES(RECURRENCES),
        .PRE_RECURRENCE_STAGE(PRE_RECURRENCE_STAGE),
        .PRE_STAGE_ROWS(PRE_STAGE_ROWS),
        .PRE_STAGE_COLUMNS(PRE_STAGE_COLUMNS),
        .PRE_STAGE_VECTOR_LENGTH(PRE_STAGE_VECTOR_LENGTH),
        .POST_RECURRENCE_STAGE(POST_RECURRENCE_STAGE),
        .FULL_ATTENTION_MASK(FULL_ATTENTION_MASK),
        .SLIDING_WINDOW(SLIDING_WINDOW)
    ) dut (.*);

    task automatic reset_core;
        begin
            rst_n = 1'b0;
            repeat (2) @(posedge clk);
            @(negedge clk);
            rst_n = 1'b1;
        end
    endtask

    task automatic consume_stage(
        input integer expected_recurrence,
        input integer expected_block,
        input integer expected_stage,
        input integer expected_rows,
        input integer expected_columns,
        input integer expected_vector_length,
        input integer context_length
    );
        integer expected_context;
        logic expected_full;
        begin
            expected_context = context_length;
            expected_full = FULL_ATTENTION_MASK[expected_block];
            if (SLIDING_WINDOW > 0 && !expected_full &&
                (expected_stage == 4 || expected_stage == 5) &&
                expected_context > SLIDING_WINDOW)
                expected_context = SLIDING_WINDOW;

            @(negedge clk);
            if (!stage_valid)
                $fatal(1, "stage_valid low at event %0d", event_count);
            if (recurrence_index != expected_recurrence || block_index != expected_block ||
                stage_id != expected_stage || matrix_rows != expected_rows ||
                matrix_columns != expected_columns || vector_length != expected_vector_length ||
                active_context_tokens != expected_context || attention_is_full != expected_full || error)
                $fatal(1, "schedule mismatch event=%0d r=%0d b=%0d s=%0d dims=%0dx%0d v=%0d ctx=%0d full=%0d",
                       event_count, recurrence_index, block_index, stage_id,
                       matrix_rows, matrix_columns, vector_length, active_context_tokens,
                       attention_is_full);

            stage_ready = 1'b1;
            @(posedge clk);
            #1 stage_ready = 1'b0;
            stage_done = 1'b1;
            @(posedge clk);
            #1 stage_done = 1'b0;
            event_count = event_count + 1;
        end
    endtask

    task automatic run_context(input integer context_length);
        integer recurrence;
        integer block;
        integer stage;
        integer rows;
        integer columns;
        integer vector_size;
        integer count_before;
        begin
            reset_core();
            count_before = event_count;
            @(negedge clk);
            context_tokens = context_length;
            start = 1'b1;
            @(posedge clk);
            #1 start = 1'b0;

            for (recurrence = 0; recurrence < RECURRENCES; recurrence = recurrence + 1) begin
                if (PRE_RECURRENCE_STAGE >= 0)
                    consume_stage(recurrence, 0, PRE_RECURRENCE_STAGE,
                                  PRE_STAGE_ROWS, PRE_STAGE_COLUMNS,
                                  PRE_STAGE_VECTOR_LENGTH, context_length);

                for (block = 0; block < CORE_BLOCKS; block = block + 1) begin
                    for (stage = 1; stage <= 10; stage = stage + 1) begin
                        rows = 0;
                        columns = 0;
                        vector_size = 0;
                        case (stage)
                            1: if (HAS_PRE_ATTENTION_NORM) vector_size = HIDDEN_SIZE;
                            7: if (HAS_PRE_FFN_NORM) vector_size = HIDDEN_SIZE;
                            2: begin rows = QUERY_SIZE + 2 * KV_SIZE; columns = HIDDEN_SIZE; end
                            3: begin
                                rows = ATTENTION_GATE_ROWS;
                                if (ATTENTION_GATE_ROWS != 0)
                                    columns = HIDDEN_SIZE;
                                vector_size = HIDDEN_SIZE;
                            end
                            4: vector_size = HEAD_DIM;
                            5: vector_size = QUERY_SIZE;
                            6: begin rows = HIDDEN_SIZE; columns = QUERY_SIZE; end
                            8: begin rows = 2 * INTERMEDIATE_SIZE; columns = HIDDEN_SIZE; end
                            9: vector_size = INTERMEDIATE_SIZE;
                            10: begin rows = HIDDEN_SIZE; columns = INTERMEDIATE_SIZE; end
                            default: $fatal(1, "unexpected stage %0d", stage);
                        endcase
                        if ((stage != 1 || HAS_PRE_ATTENTION_NORM) &&
                            (stage != 7 || HAS_PRE_FFN_NORM))
                            consume_stage(recurrence, block, stage, rows, columns,
                                          vector_size, context_length);
                    end
                end

                if (POST_RECURRENCE_STAGE >= 0)
                    consume_stage(recurrence, CORE_BLOCKS - 1, POST_RECURRENCE_STAGE,
                                  0, 0, HIDDEN_SIZE, context_length);
            end

            expected_events = RECURRENCES * (CORE_BLOCKS *
                (10 - (!HAS_PRE_ATTENTION_NORM) - (!HAS_PRE_FFN_NORM)) +
                ((PRE_RECURRENCE_STAGE >= 0) ? 1 : 0) +
                ((POST_RECURRENCE_STAGE >= 0) ? 1 : 0));
            @(negedge clk);
            if (!done || error || event_count - count_before != expected_events)
                $fatal(1, "completion mismatch context=%0d done=%0d error=%0d events=%0d expected=%0d",
                       context_length, done, error, event_count - count_before, expected_events);
        end
    endtask

    initial begin
        event_count = 0;
        expected_events = 0;
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

        $display("PASS: recurrent schedule (%0d blocks x %0d recurrences, %0d handshakes/context)",
                 CORE_BLOCKS, RECURRENCES, expected_events);
        $finish;
    end
endmodule
