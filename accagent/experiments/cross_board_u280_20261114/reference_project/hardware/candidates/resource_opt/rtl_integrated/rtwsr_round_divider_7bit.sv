`timescale 1ns / 1ps

module rtwsr_round_divider_7bit #(
    parameter bit FAST = 1'b0
) (
    input  logic        clk,
    input  logic        rst_n,
    input  logic        start,
    input  logic [15:0] dividend,
    input  logic [15:0] divisor,
    output logic        ready,
    output logic        done,
    output logic [7:0]  quotient
);
    logic busy_q;
    logic [15:0] dividend_q;
    logic [15:0] divisor_q;
    logic [15:0] remainder_q;
    logic [7:0] quotient_q;
    logic [2:0] iteration_q;
    logic [15:0] shifted_remainder;
    logic [15:0] remainder_next;
    logic [7:0] quotient_next;

    function automatic logic [7:0] unrolled_quotient(
        input logic [15:0] input_dividend,
        input logic [15:0] input_divisor
    );
        logic [15:0] remainder_value;
        logic [7:0] quotient_value;
        remainder_value = {7'd0, input_dividend[15:7]};
        quotient_value = '0;
        for (integer bit_index = 6; bit_index >= 0; bit_index = bit_index - 1) begin
            remainder_value = {remainder_value[14:0], input_dividend[bit_index]};
            quotient_value = {quotient_value[6:0], 1'b0};
            if (remainder_value >= input_divisor) begin
                remainder_value = remainder_value - input_divisor;
                quotient_value[0] = 1'b1;
            end
        end
        return quotient_value;
    endfunction

    always_comb begin
        shifted_remainder = {remainder_q[14:0], dividend_q[6 - int'(iteration_q)]};
        if (shifted_remainder >= divisor_q) begin
            remainder_next = shifted_remainder - divisor_q;
            quotient_next = {quotient_q[6:0], 1'b1};
        end else begin
            remainder_next = shifted_remainder;
            quotient_next = {quotient_q[6:0], 1'b0};
        end
    end

    assign ready = !busy_q;

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            busy_q <= 1'b0;
            dividend_q <= '0;
            divisor_q <= 16'd1;
            remainder_q <= '0;
            quotient_q <= '0;
            iteration_q <= '0;
            quotient <= '0;
            done <= 1'b0;
        end else begin
            done <= 1'b0;
            if (start && ready && divisor != 0) begin
                if (FAST) begin
                    quotient <= unrolled_quotient(dividend, divisor);
                    done <= 1'b1;
                end else begin
                    busy_q <= 1'b1;
                    dividend_q <= dividend;
                    divisor_q <= divisor;
                    remainder_q <= {7'd0, dividend[15:7]};
                    quotient_q <= '0;
                    iteration_q <= '0;
                end
            end else if (busy_q) begin
                remainder_q <= remainder_next;
                quotient_q <= quotient_next;
                if (iteration_q == 3'd6) begin
                    quotient <= quotient_next;
                    busy_q <= 1'b0;
                    done <= 1'b1;
                end else begin
                    iteration_q <= iteration_q + 1'b1;
                end
            end
        end
    end
endmodule
