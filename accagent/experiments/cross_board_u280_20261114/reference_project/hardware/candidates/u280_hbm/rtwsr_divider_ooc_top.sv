`timescale 1ns / 1ps

module rtwsr_divider_ooc_top (
    input logic clk,
    input logic rst_n,
    input logic start,
    input logic [15:0] dividend,
    input logic [15:0] divisor,
    output logic ready,
    output logic done,
    output logic [7:0] quotient
);
    logic rst_n_q, start_q;
    logic [15:0] dividend_q, divisor_q;
    logic divider_ready, divider_done;
    logic [7:0] divider_quotient;

    always_ff @(posedge clk) begin
        rst_n_q <= rst_n;
        start_q <= start;
        dividend_q <= dividend;
        divisor_q <= divisor;
        ready <= divider_ready;
        done <= divider_done;
        quotient <= divider_quotient;
    end

    rtwsr_round_divider_7bit #(.FAST(1'b1)) u_divider (
        .clk(clk), .rst_n(rst_n_q), .start(start_q), .dividend(dividend_q),
        .divisor(divisor_q), .ready(divider_ready), .done(divider_done),
        .quotient(divider_quotient)
    );
endmodule
