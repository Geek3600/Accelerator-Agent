`timescale 1ns / 1ps

module tb_rtwsr_swiglu_residual_unit #(
    parameter int VECTOR_LEN = 17920,
    parameter int LANES = 16,
    parameter int DATA_W = 16,
    parameter bit STREAM_FUSED = 1'b0,
    parameter int VECTOR_COUNT = (VECTOR_LEN + LANES - 1) / LANES,
    parameter int COUNT_WIDTH = $clog2(VECTOR_COUNT + 1),
    parameter int VECTOR_WIDTH = LANES * DATA_W
);
    logic clk = 1'b0;
    logic rst_n = 1'b0;
    logic start = 1'b0;
    logic in_valid = 1'b0;
    logic in_ready;
    logic [VECTOR_WIDTH-1:0] gate_chunk = '0;
    logic [VECTOR_WIDTH-1:0] up_chunk = '0;
    logic [VECTOR_WIDTH-1:0] residual_chunk = '0;
    logic in_last = 1'b0;
    logic [15:0] residual_rate_q15 = 16'd24576;
    logic ready;
    logic out_valid;
    logic out_ready = 1'b0;
    logic [VECTOR_WIDTH-1:0] output_chunk;
    logic out_last;
    logic busy;
    logic done;
    logic protocol_error;
    integer dimension;
    integer lane;
    integer chunk;
    integer wait_cycles;
    integer expected;
    integer gate_value;
    integer up_value;
    integer residual_value;
    integer sigmoid_value;
    longint signed product;
    longint signed scaled_update;
    integer output_count;

    always #5 clk = ~clk;

    rtwsr_swiglu_residual_unit #(
        .VECTOR_LEN(VECTOR_LEN), .LANES(LANES), .STREAM_FUSED(STREAM_FUSED)
    ) dut (
        .clk(clk), .rst_n(rst_n), .start(start),
        .in_valid(in_valid), .in_ready(in_ready),
        .gate_q4_12(gate_chunk), .up_q4_12(up_chunk),
        .residual_q4_12(residual_chunk), .in_last(in_last),
        .residual_rate_q15(residual_rate_q15), .ready(ready),
        .out_valid(out_valid), .out_ready(out_ready),
        .output_q4_12(output_chunk), .out_last(out_last),
        .busy(busy), .done(done), .protocol_error(protocol_error)
    );

    function automatic integer gate_pattern(input integer value_index);
        gate_pattern = (((value_index * 17 + 3) % 4097) - 2048);
    endfunction

    function automatic integer up_pattern(input integer value_index);
        up_pattern = (((value_index * 23 + 11) % 3073) - 1536);
    endfunction

    function automatic integer residual_pattern(input integer value_index);
        residual_pattern = (((value_index * 31 + 19) % 2049) - 1024);
    endfunction

    function automatic integer sigmoid_pattern(input integer value_q4_12);
        integer lut [0:32];
        integer shifted;
        integer index;
        integer fraction;
        begin
            lut[0] = 11; lut[1] = 18; lut[2] = 30; lut[3] = 49;
            lut[4] = 81; lut[5] = 133; lut[6] = 219; lut[7] = 360;
            lut[8] = 589; lut[9] = 961; lut[10] = 1554; lut[11] = 2486;
            lut[12] = 3906; lut[13] = 5978; lut[14] = 8813; lut[15] = 12371;
            lut[16] = 16384; lut[17] = 20397; lut[18] = 23955; lut[19] = 26790;
            lut[20] = 28862; lut[21] = 30282; lut[22] = 31214; lut[23] = 31807;
            lut[24] = 32179; lut[25] = 32408; lut[26] = 32549; lut[27] = 32635;
            lut[28] = 32687; lut[29] = 32719; lut[30] = 32738; lut[31] = 32750;
            lut[32] = 32757;
            shifted = value_q4_12 + 32768;
            if (shifted <= 0)
                sigmoid_pattern = lut[0];
            else if (shifted >= 65536)
                sigmoid_pattern = lut[32];
            else begin
                index = shifted >> 11;
                fraction = shifted & 2047;
                sigmoid_pattern = lut[index] + ((lut[index+1] - lut[index]) * fraction >> 11);
            end
        end
    endfunction

    initial begin
        repeat (3) @(posedge clk);
        @(negedge clk);
        rst_n = 1'b1;
        wait (ready);
        start = 1'b1;
        @(posedge clk);
        @(negedge clk);
        start = 1'b0;
        output_count = 0;
        wait_cycles = 0;
        chunk = 0;
        while ((!done || output_count < VECTOR_COUNT) && wait_cycles < 8 * VECTOR_COUNT + 64) begin
            @(negedge clk);
            out_ready = (wait_cycles % 5 != 2);
            if (in_ready && chunk < VECTOR_COUNT) begin
                gate_chunk = '0;
                up_chunk = '0;
                residual_chunk = '0;
                for (lane = 0; lane < LANES; lane = lane + 1) begin
                    dimension = chunk * LANES + lane;
                    if (dimension < VECTOR_LEN) begin
                        gate_chunk[lane*DATA_W +: DATA_W] = gate_pattern(dimension);
                        up_chunk[lane*DATA_W +: DATA_W] = up_pattern(dimension);
                        residual_chunk[lane*DATA_W +: DATA_W] = residual_pattern(dimension);
                    end
                end
                in_last = (chunk == VECTOR_COUNT - 1);
                in_valid = 1'b1;
                @(posedge clk);
                @(negedge clk);
                in_valid = 1'b0;
                in_last = 1'b0;
                chunk = chunk + 1;
            end
            if (out_valid && out_ready) begin
                for (lane = 0; lane < LANES; lane = lane + 1) begin
                    dimension = output_count * LANES + lane;
                    if (dimension < VECTOR_LEN) begin
                        gate_value = gate_pattern(dimension);
                        up_value = up_pattern(dimension);
                        residual_value = residual_pattern(dimension);
                        sigmoid_value = sigmoid_pattern(gate_value);
                        product = gate_value * sigmoid_value;
                        product = (product >>> 15) * up_value;
                        scaled_update = (product * 24576) >>> 27;
                        expected = residual_value + scaled_update;
                        if (expected > 32767) expected = 32767;
                        else if (expected < -32768) expected = -32768;
                        if ($signed(output_chunk[lane*DATA_W +: DATA_W]) !== expected)
                            $fatal(1, "SwiGLU output mismatch at %0d: got %0d expected %0d", dimension,
                                $signed(output_chunk[lane*DATA_W +: DATA_W]), expected);
                    end
                end
                if (out_last !== (output_count == VECTOR_COUNT - 1))
                    $fatal(1, "SwiGLU last mismatch at chunk %0d", output_count);
                output_count = output_count + 1;
            end
            @(posedge clk);
            #1;
            wait_cycles = wait_cycles + 1;
        end
        if (!done || output_count != VECTOR_COUNT || chunk != VECTOR_COUNT)
            $fatal(1, "SwiGLU incomplete: done=%b input=%0d output=%0d expected=%0d", done,
                chunk, output_count, VECTOR_COUNT);
        if (protocol_error)
            $fatal(1, "SwiGLU unit reported protocol error");
        $display("PASS: streamed SwiGLU/residual VECTOR_LEN=%0d chunks=%0d", VECTOR_LEN, VECTOR_COUNT);
        $finish;
    end
endmodule
