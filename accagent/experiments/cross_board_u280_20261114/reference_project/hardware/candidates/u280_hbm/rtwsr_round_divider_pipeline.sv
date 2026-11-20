`timescale 1ns / 1ps

module rtwsr_round_divider_pipeline (
    input logic clk,
    input logic rst_n,
    input logic start,
    input logic [15:0] dividend,
    input logic [15:0] divisor,
    output logic ready,
    output logic done,
    output logic [7:0] quotient
);
    typedef enum logic [1:0] {IDLE, MIDDLE, FINISH} state_t;
    state_t state_q;
    logic [15:0] dividend_q, divisor_q, remainder_q;
    logic [7:0] quotient_q;

    function automatic logic [23:0] divide_bits(
        input logic [15:0] remainder_in,
        input logic [7:0] quotient_in,
        input logic [15:0] input_dividend,
        input logic [15:0] input_divisor,
        input integer high_bit,
        input integer low_bit
    );
        logic [15:0] remainder_value;
        logic [7:0] quotient_value;
        remainder_value = remainder_in;
        quotient_value = quotient_in;
        for (integer bit_index = high_bit; bit_index >= low_bit; bit_index = bit_index - 1) begin
            remainder_value = {remainder_value[14:0], input_dividend[bit_index]};
            quotient_value = {quotient_value[6:0], 1'b0};
            if (remainder_value >= input_divisor) begin
                remainder_value = remainder_value - input_divisor;
                quotient_value[0] = 1'b1;
            end
        end
        return {remainder_value, quotient_value};
    endfunction

    assign ready = state_q == IDLE;

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            state_q <= IDLE;
            dividend_q <= '0;
            divisor_q <= '0;
            remainder_q <= '0;
            quotient_q <= '0;
            quotient <= '0;
            done <= 1'b0;
        end else begin
            done <= 1'b0;
            case (state_q)
                IDLE: if (start && divisor != 0) begin
                    dividend_q <= dividend;
                    divisor_q <= divisor;
                    {remainder_q, quotient_q} <= divide_bits(
                        {7'd0, dividend[15:7]}, 8'd0, dividend, divisor, 6, 4);
                    state_q <= MIDDLE;
                end
                MIDDLE: begin
                    {remainder_q, quotient_q} <= divide_bits(
                        remainder_q, quotient_q, dividend_q, divisor_q, 3, 2);
                    state_q <= FINISH;
                end
                FINISH: begin
                    quotient <= 8'(divide_bits(
                        remainder_q, quotient_q, dividend_q, divisor_q, 1, 0));
                    done <= 1'b1;
                    state_q <= IDLE;
                end
                default: state_q <= IDLE;
            endcase
        end
    end
endmodule
