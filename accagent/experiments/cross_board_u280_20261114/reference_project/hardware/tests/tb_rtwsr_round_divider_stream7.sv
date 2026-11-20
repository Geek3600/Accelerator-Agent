`timescale 1ns / 1ps

module tb_rtwsr_round_divider_stream7;
    localparam int VECTOR_LEN = 5280;

    logic clk = 1'b0;
    logic rst_n = 1'b0;
    logic input_valid = 1'b0;
    logic [15:0] dividend = '0;
    logic [15:0] divisor = 16'd1;
    logic input_negative = 1'b0;
    logic [15:0] input_index = '0;
    logic output_valid;
    logic [7:0] quotient;
    logic output_negative;
    logic [15:0] output_index;
    logic [7:0] expected_quotient [0:VECTOR_LEN-1];
    logic expected_negative [0:VECTOR_LEN-1];
    integer maximum;
    integer scale_value;
    integer sample_index;
    integer sample_magnitude;
    integer expected_count;
    integer cycle_index;

    always #5 clk = ~clk;

    rtwsr_round_divider_stream7 dut (.*);

    initial begin
        repeat (4) @(negedge clk);
        rst_n = 1'b1;
        for (maximum = 1; maximum <= 32768; maximum = maximum + 257) begin
            scale_value = (maximum + 126) / 127;
            if (scale_value < 1)
                scale_value = 1;
            for (sample_index = 0; sample_index < VECTOR_LEN; sample_index = sample_index + 1) begin
                sample_magnitude = (maximum * sample_index) / (VECTOR_LEN - 1);
                expected_quotient[sample_index] = 8'((sample_magnitude + scale_value/2) / scale_value);
                expected_negative[sample_index] = sample_index[0];
            end

            expected_count = 0;
            for (cycle_index = 0; cycle_index < VECTOR_LEN + 6; cycle_index = cycle_index + 1) begin
                @(negedge clk);
                input_valid = cycle_index < VECTOR_LEN;
                if (input_valid) begin
                    sample_magnitude = (maximum * cycle_index) / (VECTOR_LEN - 1);
                    dividend = 16'(sample_magnitude + scale_value/2);
                    divisor = 16'(scale_value);
                    input_negative = cycle_index[0];
                    input_index = 16'(cycle_index);
                end
                @(posedge clk);
                #1;
                if (output_valid) begin
                    if (output_index != expected_count ||
                        quotient != expected_quotient[expected_count] ||
                        output_negative != expected_negative[expected_count])
                        $fatal(1, "stream divide mismatch max=%0d index=%0d got=%0d/%0d/%0d expected=%0d/%0d",
                               maximum, output_index, quotient, output_negative, expected_count,
                               expected_quotient[expected_count], expected_negative[expected_count]);
                    expected_count = expected_count + 1;
                end
            end
            if (expected_count != VECTOR_LEN)
                $fatal(1, "stream divide output count mismatch max=%0d got=%0d expected=%0d",
                       maximum, expected_count, VECTOR_LEN);
        end
        $display("ROUND_DIVIDER_STREAM7_VECTOR_PASS vector_length=%0d vectors=128 initiation_interval=1 latency=7",
                 VECTOR_LEN);
        $finish;
    end
endmodule
