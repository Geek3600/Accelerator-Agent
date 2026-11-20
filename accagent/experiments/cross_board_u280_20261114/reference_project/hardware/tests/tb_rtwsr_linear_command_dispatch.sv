`timescale 1ns / 1ps

module tb_rtwsr_linear_command_dispatch;
    logic command_valid = 1'b0;
    logic [4:0] command_id = '0;
    logic [5:0] block_index = '0;
    logic [4:0] recurrence_index = '0;
    logic [15:0] matrix_rows = '0;
    logic [15:0] matrix_columns = '0;
    logic linear_engine_ready = 1'b0;
    logic linear_engine_done = 1'b0;
    logic operator_ready = 1'b0;
    logic operator_done = 1'b0;
    logic linear_engine_valid;
    logic [4:0] linear_engine_command_id;
    logic [5:0] linear_engine_block_index;
    logic [4:0] linear_engine_recurrence_index;
    logic [15:0] linear_engine_rows;
    logic [15:0] linear_engine_columns;
    logic scheduler_command_ready;
    logic scheduler_command_done;

    rtwsr_linear_command_dispatch dut (.*);

    task automatic check_linear(input logic [4:0] id);
        begin
            command_valid = 1'b1;
            command_id = id;
            block_index = 6'd17;
            recurrence_index = 5'd9;
            matrix_rows = 16'd1234;
            matrix_columns = 16'd5678;
            linear_engine_ready = 1'b1;
            linear_engine_done = 1'b0;
            operator_ready = 1'b0;
            operator_done = 1'b1;
            #1;
            if (!linear_engine_valid || scheduler_command_ready != linear_engine_ready ||
                scheduler_command_done != linear_engine_done || linear_engine_command_id != id ||
                linear_engine_block_index != block_index ||
                linear_engine_recurrence_index != recurrence_index ||
                linear_engine_rows != matrix_rows || linear_engine_columns != matrix_columns)
                $fatal(1, "linear descriptor/handshake mismatch for command %0d", id);
            linear_engine_ready = 1'b0;
            linear_engine_done = 1'b1;
            #1;
            if (scheduler_command_ready || !scheduler_command_done)
                $fatal(1, "linear completion did not use the shared engine handshake");
        end
    endtask

    task automatic check_operator(input logic [4:0] id);
        begin
            command_valid = 1'b1;
            command_id = id;
            linear_engine_ready = 1'b0;
            linear_engine_done = 1'b0;
            operator_ready = 1'b1;
            operator_done = 1'b0;
            #1;
            if (linear_engine_valid || scheduler_command_ready != operator_ready ||
                scheduler_command_done != operator_done || linear_engine_rows != 16'd0 ||
                linear_engine_columns != 16'd0)
                $fatal(1, "non-linear command %0d escaped to the shared engine", id);
        end
    endtask

    initial begin
        check_linear(5'd0);
        check_linear(5'd3);
        check_linear(5'd4);
        check_linear(5'd9);
        check_linear(5'd15);
        check_linear(5'd18);
        check_linear(5'd19);
        check_linear(5'd20);
        check_linear(5'd21);
        check_linear(5'd22);
        check_operator(5'd1);
        check_operator(5'd2);
        check_operator(5'd5);
        check_operator(5'd6);
        check_operator(5'd7);
        check_operator(5'd10);
        check_operator(5'd13);

        command_valid = 1'b0;
        command_id = 5'd3;
        #1;
        if (linear_engine_valid)
            $fatal(1, "shared engine valid asserted while scheduler command was invalid");
        $display("PASS: shared linear engine routes all model matrix command types");
        $finish;
    end
endmodule
