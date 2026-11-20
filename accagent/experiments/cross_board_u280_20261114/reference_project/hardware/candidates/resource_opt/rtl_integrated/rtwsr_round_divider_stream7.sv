`timescale 1ns / 1ps

module rtwsr_round_divider_stream7 (
    input  logic        clk,
    input  logic        rst_n,
    input  logic        input_valid,
    input  logic [15:0] dividend,
    input  logic [15:0] divisor,
    input  logic        input_negative,
    input  logic [15:0] input_index,
    output logic        output_valid,
    output logic [7:0]  quotient,
    output logic        output_negative,
    output logic [15:0] output_index
);
    logic [6:0] valid_q;
    logic [15:0] dividend_q [0:6];
    logic [15:0] divisor_q [0:6];
    logic [15:0] remainder_q [0:6];
    logic [7:0] quotient_q [0:6];
    logic negative_q [0:6];
    logic [15:0] index_q [0:6];

    function automatic logic [23:0] divide_step(
        input logic [15:0] remainder_in,
        input logic [7:0] quotient_in,
        input logic [15:0] input_dividend,
        input logic [15:0] input_divisor,
        input integer bit_index
    );
        logic [15:0] remainder_value;
        logic [7:0] quotient_value;
        remainder_value = {remainder_in[14:0], input_dividend[bit_index]};
        quotient_value = {quotient_in[6:0], 1'b0};
        if (remainder_value >= input_divisor) begin
            remainder_value = remainder_value - input_divisor;
            quotient_value[0] = 1'b1;
        end
        return {remainder_value, quotient_value};
    endfunction

    assign output_valid = valid_q[6];
    assign quotient = quotient_q[6];
    assign output_negative = negative_q[6];
    assign output_index = index_q[6];

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            valid_q <= '0;
            for (integer stage = 0; stage < 7; stage = stage + 1) begin
                dividend_q[stage] <= '0;
                divisor_q[stage] <= 16'd1;
                remainder_q[stage] <= '0;
                quotient_q[stage] <= '0;
                negative_q[stage] <= 1'b0;
                index_q[stage] <= '0;
            end
        end else begin
            valid_q[0] <= input_valid && (divisor != 0);
            if (input_valid && divisor != 0) begin
                dividend_q[0] <= dividend;
                divisor_q[0] <= divisor;
                {remainder_q[0], quotient_q[0]} <= divide_step(
                    {7'd0, dividend[15:7]}, 8'd0, dividend, divisor, 6);
                negative_q[0] <= input_negative;
                index_q[0] <= input_index;
            end
            for (integer stage = 1; stage < 7; stage = stage + 1) begin
                valid_q[stage] <= valid_q[stage-1];
                if (valid_q[stage-1]) begin
                    dividend_q[stage] <= dividend_q[stage-1];
                    divisor_q[stage] <= divisor_q[stage-1];
                    {remainder_q[stage], quotient_q[stage]} <= divide_step(
                        remainder_q[stage-1], quotient_q[stage-1],
                        dividend_q[stage-1], divisor_q[stage-1], 6-stage);
                    negative_q[stage] <= negative_q[stage-1];
                    index_q[stage] <= index_q[stage-1];
                end
            end
        end
    end
endmodule
