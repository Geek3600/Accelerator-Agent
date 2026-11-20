`timescale 1ns / 1ps

module tb_rtwsr_huginn_payload_descriptor;
    logic [4:0] command_id;
    logic [5:0] block_index;
    logic [4:0] recurrence_index;
    logic valid;
    logic adapter_file;
    logic [31:0] weight_offset_bytes;
    logic [31:0] weight_bytes;
    logic [31:0] weight_words;
    logic [31:0] gamma_offset_bytes;
    logic [31:0] gamma_bytes;
    logic [31:0] gamma_words;
    logic [15:0] matrix_rows;
    logic [15:0] matrix_columns;
    integer block;
    integer op;
    integer round_id;
    logic [4:0] commands [0:4];

    rtwsr_huginn_payload_descriptor dut (.*);

    initial begin
        commands[0] = 5'd3;
        commands[1] = 5'd9;
        commands[2] = 5'd21;
        commands[3] = 5'd22;
        commands[4] = 5'd15;
        for (block = 0; block < 4; block = block + 1) begin
            for (op = 0; op < 5; op = op + 1) begin
                for (round_id = 0; round_id < 3; round_id = round_id + 1) begin
                    case (round_id)
                        0: recurrence_index = 5'd0;
                        1: recurrence_index = 5'd7;
                        default: recurrence_index = 5'd31;
                    endcase
                    block_index = 6'(block);
                    command_id = commands[op];
                    #1;
                    if (!valid || adapter_file || weight_words * 64 != weight_bytes ||
                        gamma_words * 64 != gamma_bytes)
                        $fatal(1, "invalid descriptor command=%0d block=%0d recurrence=%0d",
                            command_id, block_index, recurrence_index);
                    $display("DESC %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d",
                        command_id, block_index, recurrence_index, weight_offset_bytes,
                        weight_bytes, gamma_offset_bytes, gamma_bytes, weight_words,
                        gamma_words, {matrix_rows, matrix_columns});
                end
            end
        end
        for (round_id = 0; round_id < 3; round_id = round_id + 1) begin
            case (round_id)
                0: recurrence_index = 5'd0;
                1: recurrence_index = 5'd7;
                default: recurrence_index = 5'd31;
            endcase
            command_id = 5'd0;
            block_index = 6'd0;
            #1;
            if (!valid || !adapter_file || weight_bytes != 32'd14192640 ||
                matrix_rows != 16'd5280 || matrix_columns != 16'd10560)
                $fatal(1, "invalid adapter descriptor recurrence=%0d", recurrence_index);
            $display("DESC %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d",
                command_id, block_index, recurrence_index, weight_offset_bytes,
                weight_bytes, gamma_offset_bytes, gamma_bytes, weight_words,
                gamma_words, {matrix_rows, matrix_columns});
        end
        command_id = 5'd6;
        block_index = 6'd0;
        recurrence_index = 5'd0;
        #1;
        if (valid)
            $fatal(1, "unsupported command produced a descriptor");
        $display("PASS descriptors=63");
        $finish;
    end
endmodule
