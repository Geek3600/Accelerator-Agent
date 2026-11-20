`timescale 1ns / 1ps

module tb_rtwsr_huginn_ffn_pipeline #(
    parameter bit STREAM_FUSED = 1'b0,
    parameter bit GEMV_STREAM_FUSED = 1'b0
);
    localparam int VECTOR_LEN = 17920;
    logic clk = 1'b0;
    logic rst_n = 1'b0;
    logic start = 1'b0;
    logic ready, done, busy;
    logic write_valid = 1'b0;
    logic [4:0] write_command_id = '0;
    logic [15:0] write_row_start = '0;
    logic [6:0] write_rows = '0;
    logic [3071:0] write_result_q12 = '0;
    logic write_ready, in_ready, out_valid, out_last;
    logic [255:0] output_q4_12;
    logic protocol_error, activation_valid;
    logic [6:0] activation_window_index = '0;
    logic [2047:0] activation_window;
    logic [15:0] activation_scale_fp16;
    integer output_chunks = 0;
    integer cycles = 0;
    integer nonzero_outputs = 0;
    logic [31:0] activation_digest = '0;
    logic [31:0] window_digest;

    always #5 clk = ~clk;

    always @(posedge clk) begin
        cycles++;
        if (cycles > 50000)
            $fatal(1, "Huginn full-width FFN pipeline timeout");
        if (rst_n && protocol_error)
            $fatal(1, "Huginn FFN pipeline protocol error");
        if (out_valid) begin
            output_chunks++;
            for (integer lane = 0; lane < 16; lane++)
                if ($signed(output_q4_12[lane*16 +: 16]) != 0)
                    nonzero_outputs++;
        end
    end

    rtwsr_huginn_ffn_pipeline #(
        .STREAM_FUSED(STREAM_FUSED),
        .GEMV_STREAM_FUSED(GEMV_STREAM_FUSED)
    ) dut (
        .clk(clk), .rst_n(rst_n), .start(start), .ready(ready), .done(done), .busy(busy),
        .write_valid(write_valid), .write_command_id(write_command_id),
        .write_row_start(write_row_start), .write_rows(write_rows),
        .write_result_q12(write_result_q12), .write_ready(write_ready),
        .in_ready(in_ready), .out_valid(out_valid), .out_last(out_last),
        .output_q4_12(output_q4_12), .protocol_error(protocol_error),
        .activation_valid(activation_valid),
        .activation_window_index(activation_window_index),
        .activation_window(activation_window), .activation_scale_fp16(activation_scale_fp16)
    );

    task automatic write_projection(input logic [4:0] command_id);
        integer row_start;
        integer rows;
        integer row_value;
        begin
            for (row_start = 0; row_start < VECTOR_LEN; row_start = row_start + 96) begin
                rows = (VECTOR_LEN - row_start < 96) ? VECTOR_LEN - row_start : 96;
                @(negedge clk);
                write_valid = 1'b1;
                write_command_id = command_id;
                write_row_start = 16'(row_start);
                write_rows = 7'(rows);
                write_result_q12 = '0;
                for (integer lane = 0; lane < rows; lane++) begin
                    row_value = row_start + lane;
                    if (command_id == 5'd21)
                        write_result_q12[lane*32 +: 32] = 32'(2048 + ((row_value * 17) % 2048));
                    else
                        write_result_q12[lane*32 +: 32] = 32'(2560 + ((row_value * 11) % 1536));
                end
                do @(posedge clk); while (!write_ready);
            end
            @(negedge clk);
            write_valid = 1'b0;
        end
    endtask

    initial begin
        repeat (4) @(negedge clk);
        rst_n = 1'b1;
        write_projection(5'd21);
        if (GEMV_STREAM_FUSED) begin
            @(negedge clk);
            start = 1'b1;
            @(negedge clk);
            start = 1'b0;
            write_projection(5'd22);
        end else begin
            write_projection(5'd22);
            @(negedge clk);
            start = 1'b1;
            @(negedge clk);
            start = 1'b0;
        end
        while (!done) @(negedge clk);

        if (output_chunks != 1120 || nonzero_outputs != VECTOR_LEN || !activation_valid ||
            activation_scale_fp16 == 16'h0000)
            $fatal(1, "full-width FFN output mismatch chunks=%0d nonzero=%0d valid=%0d scale=%h",
                output_chunks, nonzero_outputs, activation_valid, activation_scale_fp16);

        activation_digest = '0;
        for (integer window_id = 0; window_id < 70; window_id++) begin
            activation_window_index = 7'(window_id);
            #1;
            window_digest = '0;
            for (integer byte_id = 0; byte_id < 256; byte_id++) begin
                window_digest = (window_digest << 5) - window_digest +
                                activation_window[byte_id*8 +: 8] + 32'(window_id);
                activation_digest = (activation_digest << 5) - activation_digest +
                                    activation_window[byte_id*8 +: 8] + 32'(window_id);
            end
            $display("FFN window=%0d digest=%08x", window_id, window_digest);
        end

        activation_window_index = 7'd0;
        #1;
        if (activation_window[7:0] == 8'd0 || activation_window[2047:2040] == 8'd0)
            $fatal(1, "first quantized activation window is zero");
        activation_window_index = 7'd69;
        #1;
        if (activation_window[7:0] == 8'd0 || activation_window[2047:2040] == 8'd0)
            $fatal(1, "last quantized activation window is zero");

        $display("PASS Huginn FFN rows=%0d chunks=%0d nonzero=%0d cycles=%0d scale=%h",
                 VECTOR_LEN, output_chunks, nonzero_outputs, cycles, activation_scale_fp16);
        $display("FFN activation digest=%08x", activation_digest);
        $finish;
    end
endmodule
