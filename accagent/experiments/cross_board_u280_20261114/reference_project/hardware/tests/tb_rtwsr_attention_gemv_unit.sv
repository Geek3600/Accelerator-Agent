`timescale 1ns / 1ps

module tb_rtwsr_attention_gemv_unit #(
    parameter int HEAD_DIM = 128,
    parameter int LANES = 128,
    parameter int MAX_CONTEXT = 2048,
    parameter int DATA_W = 16,
    parameter int ATTN_SCALE_Q15 = 2896,
    parameter bit FAST_RECIPROCAL = 1'b0,
    parameter bit USE_TIMING_CANDIDATE = 1'b0,
    parameter int CONTEXT_COUNT_W = $clog2(MAX_CONTEXT + 1),
    parameter int QUERY_WIDTH = HEAD_DIM * DATA_W,
    parameter int CHUNK_WIDTH = LANES * DATA_W,
    parameter int OUTPUT_CHUNKS = (HEAD_DIM + LANES - 1) / LANES
);
    logic clk = 1'b0;
    logic rst_n = 1'b0;
    logic start = 1'b0;
    logic [CONTEXT_COUNT_W-1:0] active_context_tokens = '0;
    logic [QUERY_WIDTH-1:0] query_vector_q4_12 = '0;
    logic ready;
    logic kv_valid = 1'b0;
    logic kv_ready;
    logic [CHUNK_WIDTH-1:0] kv_key_chunk_q4_12 = '0;
    logic [CHUNK_WIDTH-1:0] kv_value_chunk_q4_12 = '0;
    logic out_valid;
    logic out_ready = 1'b1;
    logic [CHUNK_WIDTH-1:0] out_chunk_q4_12;
    logic out_last;
    logic busy;
    logic done;
    logic protocol_error;
    logic signed [15:0] expected_512 [0:HEAD_DIM-1];
    logic signed [15:0] expected_2048 [0:HEAD_DIM-1];
    integer output_chunk_count;
    integer output_dimension;
    integer wait_cycles;
    integer cycle_count = 0;
    integer start_cycle;

    always #5 clk = ~clk;

    always @(posedge clk)
        cycle_count++;

`ifdef RTWSR_USE_TIMING_CANDIDATE
    rtwsr_attention_gemv_unit #(
        .HEAD_DIM(HEAD_DIM), .LANES(LANES), .MAX_CONTEXT(MAX_CONTEXT),
        .DATA_W(DATA_W), .ATTN_SCALE_Q15(ATTN_SCALE_Q15)
    ) dut (
        .clk(clk), .rst_n(rst_n), .start(start),
        .active_context_tokens(active_context_tokens), .query_vector_q4_12(query_vector_q4_12),
        .ready(ready), .kv_valid(kv_valid), .kv_ready(kv_ready),
        .kv_key_chunk_q4_12(kv_key_chunk_q4_12), .kv_value_chunk_q4_12(kv_value_chunk_q4_12),
        .out_valid(out_valid), .out_ready(out_ready), .out_chunk_q4_12(out_chunk_q4_12),
        .out_last(out_last), .busy(busy), .done(done), .protocol_error(protocol_error)
    );
`else
    rtwsr_attention_gemv_unit #(
        .HEAD_DIM(HEAD_DIM), .LANES(LANES), .MAX_CONTEXT(MAX_CONTEXT),
        .DATA_W(DATA_W), .ATTN_SCALE_Q15(ATTN_SCALE_Q15), .FAST_RECIPROCAL(FAST_RECIPROCAL)
    ) dut (
        .clk(clk), .rst_n(rst_n), .start(start),
        .active_context_tokens(active_context_tokens), .query_vector_q4_12(query_vector_q4_12),
        .ready(ready), .kv_valid(kv_valid), .kv_ready(kv_ready),
        .kv_key_chunk_q4_12(kv_key_chunk_q4_12), .kv_value_chunk_q4_12(kv_value_chunk_q4_12),
        .out_valid(out_valid), .out_ready(out_ready), .out_chunk_q4_12(out_chunk_q4_12),
        .out_last(out_last), .busy(busy), .done(done), .protocol_error(protocol_error)
    );
`endif

    function automatic logic signed [15:0] query_value(input integer dimension);
        query_value = 16'((((dimension * 37 + 11) % 101) - 50) * 20);
    endfunction

    function automatic logic signed [15:0] key_value(input integer token, input integer dimension);
        key_value = 16'((((token * 29 + dimension * 13 + 7) % 67) - 33) * 12);
    endfunction

    function automatic logic signed [15:0] value_value(input integer token, input integer dimension);
        value_value = 16'((((token * 17 + dimension * 23 + 5) % 401) - 200) * 16);
    endfunction

    task automatic run_context(input integer context_length, input integer expected_bank);
        integer token;
        integer chunk;
        integer lane;
        integer dimension;
        integer total_cycles;
        begin
            start_cycle = cycle_count;
            @(negedge clk);
            active_context_tokens = CONTEXT_COUNT_W'(context_length);
            start = 1'b1;
            @(posedge clk);
            @(negedge clk);
            start = 1'b0;

            for (token = 0; token < context_length; token = token + 1) begin
                for (chunk = 0; chunk < (HEAD_DIM + LANES - 1) / LANES; chunk = chunk + 1) begin
                    kv_key_chunk_q4_12 = '0;
                    kv_value_chunk_q4_12 = '0;
                    for (lane = 0; lane < LANES; lane = lane + 1) begin
                        dimension = chunk * LANES + lane;
                        if (dimension < HEAD_DIM) begin
                            kv_key_chunk_q4_12[lane*DATA_W +: DATA_W] = key_value(token, dimension);
                            kv_value_chunk_q4_12[lane*DATA_W +: DATA_W] = value_value(token, dimension);
                        end
                    end
                    kv_valid = 1'b1;
                    wait_cycles = 0;
                    while (!kv_ready && wait_cycles < 100) begin
                        @(negedge clk);
                        wait_cycles = wait_cycles + 1;
                    end
                    if (!kv_ready)
                        $fatal(1, "KV stream timed out at token %0d chunk %0d", token, chunk);
                    @(posedge clk);
                    @(negedge clk);
                end
            end
            kv_valid = 1'b0;

            output_chunk_count = 0;
            wait_cycles = 0;
            while (!done && wait_cycles < 100) begin
                if (out_valid) begin
                    for (lane = 0; lane < LANES; lane = lane + 1) begin
                        output_dimension = output_chunk_count * LANES + lane;
                        if (output_dimension < HEAD_DIM) begin
                            if (expected_bank == 0) begin
                                if ($signed(out_chunk_q4_12[lane*DATA_W +: DATA_W]) !== expected_512[output_dimension])
                                    $fatal(1, "512-token output[%0d] mismatch: got %0d expected %0d",
                                        output_dimension,
                                        $signed(out_chunk_q4_12[lane*DATA_W +: DATA_W]),
                                        expected_512[output_dimension]);
                            end else begin
                                if ($signed(out_chunk_q4_12[lane*DATA_W +: DATA_W]) !== expected_2048[output_dimension])
                                    $fatal(1, "2048-token output[%0d] mismatch: got %0d expected %0d",
                                        output_dimension,
                                        $signed(out_chunk_q4_12[lane*DATA_W +: DATA_W]),
                                        expected_2048[output_dimension]);
                            end
                        end else if (out_chunk_q4_12[lane*DATA_W +: DATA_W] !== '0) begin
                            $fatal(1, "padding lane %0d was not zero", lane);
                        end
                    end
                    if (out_last !== (output_chunk_count == OUTPUT_CHUNKS-1))
                        $fatal(1, "out_last mismatch at output chunk %0d", output_chunk_count);
                    output_chunk_count = output_chunk_count + 1;
                end
                @(posedge clk);
                #1;
                wait_cycles = wait_cycles + 1;
                @(negedge clk);
            end
            if (!done || output_chunk_count != OUTPUT_CHUNKS)
                $fatal(1, "attention did not complete context %0d, chunks=%0d", context_length, output_chunk_count);
            if (protocol_error || busy)
                $fatal(1, "attention reported error or remained busy after context %0d", context_length);
            total_cycles = cycle_count - start_cycle;
            $display("PASS: Attention head_dim=%0d context=%0d fast_reciprocal=%0d candidate_module=%0d cycles=%0d",
                     HEAD_DIM, context_length, FAST_RECIPROCAL, USE_TIMING_CANDIDATE, total_cycles);
        end
    endtask

    initial begin
        for (integer dimension = 0; dimension < HEAD_DIM; dimension = dimension + 1)
            query_vector_q4_12[dimension*DATA_W +: DATA_W] = query_value(dimension);
        $readmemh("expected_512.mem", expected_512);
        $readmemh("expected_2048.mem", expected_2048);

        repeat (3) @(posedge clk);
        @(negedge clk);
        rst_n = 1'b1;
        wait (ready);
        run_context(512, 0);
        run_context(2048, 1);
        $display("PASS: online QK-softmax-PV HEAD_DIM=%0d, contexts=512/2048, 128 lanes", HEAD_DIM);
        $finish;
    end
endmodule
