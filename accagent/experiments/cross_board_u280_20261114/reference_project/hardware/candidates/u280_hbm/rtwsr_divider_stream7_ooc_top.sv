`timescale 1ns / 1ps

module rtwsr_divider_stream7_ooc_top (
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
    rtwsr_round_divider_stream7 u_divider (.*);
endmodule
