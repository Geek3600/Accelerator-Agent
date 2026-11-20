`timescale 1ns / 1ps

module tb_rtwsr_round_divider_7bit #(
    parameter bit FAST = 1'b0,
    parameter bit PIPELINED = 1'b0
);
    logic clk = 1'b0;
    logic rst_n = 1'b0;
    logic start = 1'b0;
    logic [15:0] dividend = '0;
    logic [15:0] divisor = 16'd1;
    logic ready;
    logic done;
    logic [7:0] quotient;
    integer maximum;
    integer scale_value;
    integer sample_index;
    integer sample_value;
    integer expected;
    integer wait_cycles;

    always #5 clk = ~clk;

    generate
        if (PIPELINED) begin : g_pipelined
            rtwsr_round_divider_pipeline dut (.*);
        end else begin : g_original
            rtwsr_round_divider_7bit #(.FAST(FAST)) dut (.*);
        end
    endgenerate

    initial begin
        repeat (4) @(negedge clk);
        rst_n = 1'b1;
        for (maximum = 1; maximum <= 32768; maximum = maximum + 257) begin
            scale_value = (maximum + 126) / 127;
            if (scale_value < 1)
                scale_value = 1;
            for (sample_index = 0; sample_index < 5280; sample_index = sample_index + 1) begin
                sample_value = (maximum * sample_index) / 5279;
                dividend = 16'(sample_value + (scale_value / 2));
                divisor = 16'(scale_value);
                expected = (sample_value + (scale_value / 2)) / scale_value;
                @(negedge clk);
                start = 1'b1;
                @(negedge clk);
                start = 1'b0;
                wait_cycles = 0;
                while (!done && wait_cycles < 12) begin
                    @(negedge clk);
                    wait_cycles = wait_cycles + 1;
                end
                if (!done || quotient != expected)
                    $fatal(1, "rounded divide mismatch max=%0d value=%0d scale=%0d got=%0d expected=%0d",
                           maximum, sample_value, scale_value, quotient, expected);
            end
        end
        $display("ROUND_DIVIDER_7BIT_VECTOR_PASS fast=%0d vector_length=5280 vectors=128 pipelined=%0d", FAST, PIPELINED);
        $finish;
    end
endmodule
