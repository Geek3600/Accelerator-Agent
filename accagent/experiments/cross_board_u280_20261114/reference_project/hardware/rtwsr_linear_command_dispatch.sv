`timescale 1ns / 1ps

module rtwsr_linear_command_dispatch(
    input  logic        command_valid,
    input  logic [4:0]  command_id,
    input  logic [5:0]  block_index,
    input  logic [4:0]  recurrence_index,
    input  logic [15:0] matrix_rows,
    input  logic [15:0] matrix_columns,
    input  logic        linear_engine_ready,
    input  logic        linear_engine_done,
    input  logic        operator_ready,
    input  logic        operator_done,
    output logic        linear_engine_valid,
    output logic [4:0]  linear_engine_command_id,
    output logic [5:0]  linear_engine_block_index,
    output logic [4:0]  linear_engine_recurrence_index,
    output logic [15:0] linear_engine_rows,
    output logic [15:0] linear_engine_columns,
    output logic        scheduler_command_ready,
    output logic        scheduler_command_done
);
    logic is_linear_command;

    always_comb begin
        case (command_id)
            5'd0,  // Huginn Adapter
            5'd3,  // Huginn fused QKV
            5'd4,  // Dory attention gate projection
            5'd9,  // O projection
            5'd15, // Down projection
            5'd18, // Q projection
            5'd19, // K projection
            5'd20, // V projection
            5'd21, // Gate projection
            5'd22: is_linear_command = 1'b1; // Up projection
            default: is_linear_command = 1'b0;
        endcase

        linear_engine_valid = command_valid && is_linear_command;
        linear_engine_command_id = is_linear_command ? command_id : '0;
        linear_engine_block_index = is_linear_command ? block_index : '0;
        linear_engine_recurrence_index = is_linear_command ? recurrence_index : '0;
        linear_engine_rows = is_linear_command ? matrix_rows : '0;
        linear_engine_columns = is_linear_command ? matrix_columns : '0;

        if (is_linear_command) begin
            scheduler_command_ready = linear_engine_ready;
            scheduler_command_done = linear_engine_done;
        end else begin
            scheduler_command_ready = operator_ready;
            scheduler_command_done = operator_done;
        end
    end
endmodule
