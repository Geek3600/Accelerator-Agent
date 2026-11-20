`timescale 1ns / 1ps

module tb_rtwsr_huginn_recurrent_sequencer;
    logic clk = 1'b0;
    logic rst_n = 1'b0;
    logic start = 1'b0;
    logic [15:0] context_tokens = '0;
    logic stage_valid;
    logic stage_ready = 1'b0;
    logic stage_done = 1'b0;
    logic [3:0] stage_id;
    logic [1:0] block_index;
    logic [4:0] recurrence_index;
    logic [15:0] matrix_rows;
    logic [15:0] matrix_columns;
    logic [15:0] vector_length;
    logic [15:0] active_context_tokens;
    logic done;
    logic error;
    integer event_count;

    always #5 clk = ~clk;

    rtwsr_huginn_recurrent_sequencer dut (.*);

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
        input integer expected_context
    );
        begin
            @(negedge clk);
            if (!stage_valid)
                $fatal(1, "stage_valid low at event %0d", event_count);
            if (recurrence_index != expected_recurrence || block_index != expected_block ||
                stage_id != expected_stage || matrix_rows != expected_rows ||
                matrix_columns != expected_columns || vector_length != expected_vector_length ||
                active_context_tokens != expected_context || error)
                $fatal(1, "schedule mismatch at event %0d r%0d b%0d s%0d dims %0dx%0d v%0d ctx%0d",
                       event_count, recurrence_index, block_index, stage_id,
                       matrix_rows, matrix_columns, vector_length, active_context_tokens);

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

            for (recurrence = 0; recurrence < 32; recurrence = recurrence + 1) begin
                consume_stage(recurrence, 0, 0, 5280, 10560, 5280, context_length);
                for (block = 0; block < 4; block = block + 1) begin
                    for (stage = 1; stage <= 10; stage = stage + 1) begin
                        rows = 0;
                        columns = 0;
                        vector_size = 5280;
                        case (stage)
                            1, 7: vector_size = 5280;
                            2: begin rows = 15840; columns = 5280; end
                            3: vector_size = 5280;
                            4: vector_size = 96;
                            5: vector_size = 5280;
                            6: begin rows = 5280; columns = 5280; end
                            8: begin rows = 35840; columns = 5280; end
                            9: vector_size = 17920;
                            10: begin rows = 5280; columns = 17920; end
                            default: $fatal(1, "unexpected stage %0d", stage);
                        endcase
                        consume_stage(recurrence, block, stage, rows, columns,
                                      vector_size, context_length);
                    end
                end
            end

            @(negedge clk);
            if (!done || error || event_count - count_before != 1312)
                $fatal(1, "completion mismatch for context %0d: done=%0d error=%0d events=%0d",
                       context_length, done, error, event_count - count_before);
        end
    endtask

    initial begin
        event_count = 0;
        run_context(512);
        run_context(2048);
        if (event_count != 2624)
            $fatal(1, "expected 2624 total stage handshakes, saw %0d", event_count);
        $display("PASS: Huginn recurrent schedule, 1312 stages at context 512 and 2048");
        $finish;
    end
endmodule
