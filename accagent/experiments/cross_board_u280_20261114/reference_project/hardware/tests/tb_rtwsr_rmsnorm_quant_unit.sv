`timescale 1ns / 1ps

module tb_rtwsr_rmsnorm_quant_unit #(
    parameter int VECTOR_LEN = 5280,
    parameter int MAX_VECTOR_LEN = 7168,
    parameter int LANES = 16,
    parameter int DATA_W = 16,
    parameter bit PARALLEL_QUANTIZE = 1'b0,
    parameter bit PRECOMPUTED_SUM = 1'b0,
    parameter int VECTOR_COUNT = (VECTOR_LEN + LANES - 1) / LANES,
    parameter int MAX_VECTOR_COUNT = (MAX_VECTOR_LEN + LANES - 1) / LANES,
    parameter int COUNT_WIDTH = (MAX_VECTOR_COUNT <= 1) ? 1 : $clog2(MAX_VECTOR_COUNT + 1),
    parameter int VECTOR_WIDTH = LANES * DATA_W,
    parameter int QUANT_WIDTH = LANES * 8
);
    logic clk = 1'b0;
    logic rst_n = 1'b0;
    logic start = 1'b0;
    logic ready;
    logic in_valid = 1'b0;
    logic in_ready;
    logic [VECTOR_WIDTH-1:0] in_activation_q4_12 = '0;
    logic [VECTOR_WIDTH-1:0] in_gamma_q4_12 = '0;
    logic [15:0] vector_length = 16'(VECTOR_LEN);
    logic in_last = 1'b0;
    logic out_valid;
    logic out_ready = 1'b1;
    logic [VECTOR_WIDTH-1:0] out_normalized_q4_12;
    logic [QUANT_WIDTH-1:0] out_quantized_int8;
    logic out_last;
    logic [15:0] inv_rms_q15;
    logic [15:0] activation_scale_q4_12;
    logic busy;
    logic done;
    logic protocol_error;
    integer chunk;
    integer lane;
    integer dimension;
    integer output_count;
    integer wait_cycles;
    integer cycle_count = 0;
    integer start_cycle;
    longint unsigned sum_square;
    longint unsigned mean_square;
    longint unsigned low;
    longint unsigned high;
    longint unsigned middle;
    longint unsigned rms_q12;
    longint unsigned reciprocal;
    longint signed max_normalized;
    longint signed normalized_value;
    longint signed quantized_value;
    longint signed scale_signed;
    longint signed expected;
    integer input_value;
    longint signed input_signed;

    always #5 clk = ~clk;

    always @(posedge clk)
        cycle_count++;

    rtwsr_rmsnorm_quant_unit #(
        .VECTOR_LEN(VECTOR_LEN),
        .MAX_VECTOR_LEN(MAX_VECTOR_LEN),
        .LANES(LANES),
        .PARALLEL_QUANTIZE(PARALLEL_QUANTIZE)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .start(start),
        .precomputed_sum_valid(PRECOMPUTED_SUM),
        .precomputed_sum_square(sum_square),
        .preloaded_input_valid(1'b0), .preload_write(1'b0), .preload_tile_index(9'd0),
        .preload_activation_q4_12('0), .preload_gamma_q4_12('0),
        .vector_length(vector_length),
        .ready(ready),
        .in_valid(in_valid),
        .in_ready(in_ready),
        .in_activation_q4_12(in_activation_q4_12),
        .in_gamma_q4_12(in_gamma_q4_12),
        .in_last(in_last),
        .out_valid(out_valid),
        .out_ready(out_ready),
        .out_normalized_q4_12(out_normalized_q4_12),
        .out_quantized_int8(out_quantized_int8),
        .out_last(out_last),
        .inv_rms_q15(inv_rms_q15),
        .activation_scale_q4_12(activation_scale_q4_12),
        .busy(busy),
        .done(done),
        .protocol_error(protocol_error)
    );

    function automatic integer activation_pattern(input integer value_index);
        activation_pattern = (((value_index * 43 + 7) % 2049) - 1024);
    endfunction

    function automatic integer gamma_pattern(input integer value_index);
        gamma_pattern = 3072 + ((value_index * 29 + 11) % 2049);
    endfunction

    function automatic longint signed normalized_pattern(
        input integer value,
        input integer gamma,
        input longint unsigned inverse
    );
        longint signed first;
        longint signed second;
        longint signed inverse_signed;
        begin
            inverse_signed = inverse;
            first = (value * inverse_signed) >>> 15;
            second = (first * gamma) >>> 12;
            if (second > 32767)
                normalized_pattern = 32767;
            else if (second < -32768)
                normalized_pattern = -32768;
            else
                normalized_pattern = second;
        end
    endfunction

    initial begin
        sum_square = 0;
        for (dimension = 0; dimension < VECTOR_LEN; dimension = dimension + 1) begin
            input_value = activation_pattern(dimension);
            input_signed = input_value;
            sum_square = sum_square + input_signed * input_signed;
        end
        mean_square = sum_square / VECTOR_LEN;
        low = 0;
        high = 32'hffff_ffff;
        for (integer iteration = 0; iteration < 32; iteration = iteration + 1) begin
            middle = (low + high + 1) >> 1;
            if (middle * middle <= mean_square)
                low = middle;
            else
                high = middle - 1;
        end
        rms_q12 = low;
        reciprocal = rms_q12 == 0 ? 32767 : (64'd1 << 27) / rms_q12;
        if (reciprocal > 32767)
            reciprocal = 32767;
        max_normalized = 0;
        for (dimension = 0; dimension < VECTOR_LEN; dimension = dimension + 1) begin
            normalized_value = normalized_pattern(activation_pattern(dimension), gamma_pattern(dimension), reciprocal);
            if ((normalized_value < 0 ? -normalized_value : normalized_value) > max_normalized)
                max_normalized = normalized_value < 0 ? -normalized_value : normalized_value;
        end
        expected = max_normalized / 127;
        if (expected < 1)
            expected = 1;

        repeat (3) @(posedge clk);
        @(negedge clk);
        rst_n = 1'b1;
        wait (ready);
        start_cycle = cycle_count;
        start = 1'b1;
        @(posedge clk);
        @(negedge clk);
        start = 1'b0;
        for (chunk = 0; chunk < VECTOR_COUNT; chunk = chunk + 1) begin
            in_activation_q4_12 = '0;
            in_gamma_q4_12 = '0;
            for (lane = 0; lane < LANES; lane = lane + 1) begin
                dimension = chunk * LANES + lane;
                if (dimension < VECTOR_LEN) begin
                    in_activation_q4_12[lane*DATA_W +: DATA_W] = activation_pattern(dimension);
                    in_gamma_q4_12[lane*DATA_W +: DATA_W] = gamma_pattern(dimension);
                end
            end
            in_last = (chunk == VECTOR_COUNT - 1);
            in_valid = 1'b1;
            if (!in_ready)
                $fatal(1, "RMSNorm input not ready at chunk %0d", chunk);
            @(posedge clk);
            @(negedge clk);
        end
        in_valid = 1'b0;
        in_last = 1'b0;
        wait_cycles = 0;
        output_count = 0;
        while (!done && wait_cycles < 40 * VECTOR_COUNT + 256) begin
            @(negedge clk);
            if (out_valid) begin
                for (lane = 0; lane < LANES; lane = lane + 1) begin
                    dimension = output_count * LANES + lane;
                    if (dimension < VECTOR_LEN) begin
                        normalized_value = normalized_pattern(activation_pattern(dimension), gamma_pattern(dimension), inv_rms_q15);
                        scale_signed = activation_scale_q4_12;
                        quantized_value = normalized_value / scale_signed;
                        if (quantized_value > 127)
                            quantized_value = 127;
                        else if (quantized_value < -128)
                            quantized_value = -128;
                        if ($signed(out_normalized_q4_12[lane*DATA_W +: DATA_W]) !== normalized_value)
                            $fatal(1, "RMSNorm normalized mismatch at %0d: got %0d expected %0d inv=%0d scale=%0d",
                                dimension, $signed(out_normalized_q4_12[lane*DATA_W +: DATA_W]), normalized_value,
                                inv_rms_q15, activation_scale_q4_12);
                        if ($signed(out_quantized_int8[lane*8 +: 8]) !== quantized_value)
                            $fatal(1, "RMSNorm quantized mismatch at %0d: got %0d expected %0d norm=%0d scale=%0d",
                                dimension, $signed(out_quantized_int8[lane*8 +: 8]), quantized_value,
                                normalized_value, activation_scale_q4_12);
                    end
                end
                if (out_last !== (output_count == VECTOR_COUNT - 1))
                    $fatal(1, "RMSNorm last mismatch at chunk %0d", output_count);
                output_count = output_count + 1;
            end
            @(posedge clk);
            #1;
            wait_cycles = wait_cycles + 1;
        end
        if (!done || output_count != VECTOR_COUNT)
            $fatal(1, "RMSNorm output incomplete: done=%b chunks=%0d expected=%0d cycles=%0d state=%0d emit=%0d",
                done, output_count, VECTOR_COUNT, wait_cycles, dut.state_q, dut.emit_count_q);
        if (!PARALLEL_QUANTIZE && wait_cycles < 22 * VECTOR_COUNT)
            $fatal(1, "RMSNorm quantizer did not use the expected iterative latency: %0d", wait_cycles);
        if (inv_rms_q15 !== reciprocal[15:0] || activation_scale_q4_12 !== expected[15:0])
            $fatal(1, "RMSNorm scale mismatch: inv=%0d/%0d scale=%0d/%0d", inv_rms_q15, reciprocal,
                activation_scale_q4_12, expected);
        if (protocol_error)
            $fatal(1, "RMSNorm reported protocol error");
        $display("PASS: RMSNorm/dynamic INT8 VECTOR_LEN=%0d, %0d chunks, parallel=%0d cycles=%0d output_wait=%0d",
                 VECTOR_LEN, VECTOR_COUNT, PARALLEL_QUANTIZE, cycle_count - start_cycle, wait_cycles);
        $finish;
    end
endmodule
