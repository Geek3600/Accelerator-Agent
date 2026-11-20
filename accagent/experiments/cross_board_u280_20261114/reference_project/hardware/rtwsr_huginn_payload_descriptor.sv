`timescale 1ns / 1ps

module rtwsr_huginn_payload_descriptor(
    input  logic [4:0]  command_id,
    input  logic [5:0]  block_index,
    input  logic [4:0]  recurrence_index,
    output logic        valid,
    output logic        adapter_file,
    output logic [31:0] weight_offset_bytes,
    output logic [31:0] weight_bytes,
    output logic [31:0] weight_words,
    output logic [31:0] gamma_offset_bytes,
    output logic [31:0] gamma_bytes,
    output logic [31:0] gamma_words,
    output logic [15:0] matrix_rows,
    output logic [15:0] matrix_columns
);
    localparam logic [4:0] CMD_ADAPTER = 5'd0;
    localparam logic [4:0] CMD_QKV = 5'd3;
    localparam logic [4:0] CMD_O_PROJ = 5'd9;
    localparam logic [4:0] CMD_DOWN = 5'd15;
    localparam logic [4:0] CMD_GATE_PROJ = 5'd21;
    localparam logic [4:0] CMD_UP_PROJ = 5'd22;

    localparam int CORE_WEIGHT_BLOCK_BYTES = 100208640;
    localparam int CORE_GAMMA_BLOCK_BYTES = 3983360;

    always_comb begin
        integer block_weight_base;
        integer block_gamma_base;
        integer weight_offset_in_block;
        integer gamma_offset_in_block;
        integer gamma_recurrence_stride;
        integer gamma_row_offset;

        valid = 1'b0;
        adapter_file = 1'b0;
        weight_offset_bytes = '0;
        weight_bytes = '0;
        weight_words = '0;
        gamma_offset_bytes = '0;
        gamma_bytes = '0;
        gamma_words = '0;
        matrix_rows = '0;
        matrix_columns = '0;
        block_weight_base = int'(block_index) * CORE_WEIGHT_BLOCK_BYTES;
        block_gamma_base = int'(block_index) * CORE_GAMMA_BLOCK_BYTES;
        weight_offset_in_block = 0;
        gamma_offset_in_block = 0;
        gamma_recurrence_stride = 0;
        gamma_row_offset = 0;

        if (command_id == CMD_ADAPTER) begin
            valid = 1'b1;
            adapter_file = 1'b1;
            weight_bytes = 32'd14192640;
            gamma_bytes = 32'd10560;
            gamma_offset_bytes = 32'(int'(recurrence_index) * 10560);
            matrix_rows = 16'd5280;
            matrix_columns = 16'd10560;
        end else if (block_index < 4) begin
            case (command_id)
                CMD_QKV: begin
                    valid = 1'b1;
                    weight_offset_in_block = 0;
                    weight_bytes = 32'd21288960;
                    gamma_offset_in_block = 0;
                    gamma_recurrence_stride = 31680;
                    gamma_bytes = 32'd31680;
                    matrix_rows = 16'd15840;
                    matrix_columns = 16'd5280;
                end
                CMD_O_PROJ: begin
                    valid = 1'b1;
                    weight_offset_in_block = 21288960;
                    weight_bytes = 32'd7096320;
                    gamma_offset_in_block = 1013760;
                    gamma_recurrence_stride = 10560;
                    gamma_bytes = 32'd10560;
                    matrix_rows = 16'd5280;
                    matrix_columns = 16'd5280;
                end
                CMD_GATE_PROJ: begin
                    valid = 1'b1;
                    weight_offset_in_block = 28385280;
                    weight_bytes = 32'd24084480;
                    gamma_offset_in_block = 1351680;
                    gamma_recurrence_stride = 71680;
                    gamma_bytes = 32'd35840;
                    matrix_rows = 16'd17920;
                    matrix_columns = 16'd5280;
                end
                CMD_UP_PROJ: begin
                    valid = 1'b1;
                    weight_offset_in_block = 52469760;
                    weight_bytes = 32'd24084480;
                    gamma_offset_in_block = 1351680;
                    gamma_recurrence_stride = 71680;
                    gamma_row_offset = 17920;
                    gamma_bytes = 32'd35840;
                    matrix_rows = 16'd17920;
                    matrix_columns = 16'd5280;
                end
                CMD_DOWN: begin
                    valid = 1'b1;
                    weight_offset_in_block = 76554240;
                    weight_bytes = 32'd23654400;
                    gamma_offset_in_block = 3645440;
                    gamma_recurrence_stride = 10560;
                    gamma_bytes = 32'd10560;
                    matrix_rows = 16'd5280;
                    matrix_columns = 16'd17920;
                end
                default: begin end
            endcase

            if (valid) begin
                weight_offset_bytes = 32'(block_weight_base + weight_offset_in_block);
                gamma_offset_bytes = 32'(block_gamma_base + gamma_offset_in_block +
                    int'(recurrence_index) * gamma_recurrence_stride + gamma_row_offset * 2);
            end
        end

        if (valid) begin
            weight_words = weight_bytes >> 6;
            gamma_words = gamma_bytes >> 6;
        end
    end
endmodule
