`timescale 1ns / 1ps

module tb_rtwsr_qkv_head_buffer;
    parameter int MODEL_ID = 0;
    localparam int QUERY_SIZE = MODEL_ID == 0 ? 5280 : MODEL_ID == 1 ? 2048 : 4096;
    localparam int KV_SIZE = MODEL_ID == 2 ? 1024 : QUERY_SIZE;
    localparam int HEAD_DIM = MODEL_ID == 0 ? 96 : MODEL_ID == 1 ? 128 : 256;
    localparam int QUERY_HEADS = QUERY_SIZE / HEAD_DIM;
    localparam int KV_HEADS = KV_SIZE / HEAD_DIM;
    localparam int HEAD_INDEX_W = (QUERY_HEADS <= 1) ? 1 : $clog2(QUERY_HEADS);
    localparam int HEAD_CHUNKS = (HEAD_DIM + 95) / 96;
    localparam int CHUNK_INDEX_W = (HEAD_CHUNKS <= 1) ? 1 : $clog2(HEAD_CHUNKS);
    localparam int PARALLEL_READ_PORTS = 4;
    localparam logic [4:0] CMD_QKV = 5'd3;
    localparam logic [4:0] CMD_Q = 5'd18;
    localparam logic [4:0] CMD_K = 5'd19;
    localparam logic [4:0] CMD_V = 5'd20;

    logic clk = 0, rst_n = 0;
    logic write_valid = 0, write_ready;
    logic [4:0] write_command_id = 0;
    logic [15:0] write_row_start = 0;
    logic [6:0] write_rows = 0;
    logic [3071:0] write_result_q12 = '0;
    logic qkv_valid;
    logic read_start = 0, read_ready, read_valid, read_done = 0;
    logic [HEAD_INDEX_W-1:0] read_head_index = '0;
    logic [CHUNK_INDEX_W-1:0] read_chunk_index = '0;
    logic [1535:0] query_chunk_q4_12, key_chunk_q4_12, value_chunk_q4_12;
    logic parallel_read_start = 0;
    logic [PARALLEL_READ_PORTS*HEAD_INDEX_W-1:0] parallel_read_heads = '0;
    logic [PARALLEL_READ_PORTS*CHUNK_INDEX_W-1:0] parallel_read_chunks = '0;
    logic parallel_read_ready, parallel_read_valid, parallel_read_done = 0;
    logic [PARALLEL_READ_PORTS*1536-1:0] parallel_query_chunks_q4_12;
    logic [PARALLEL_READ_PORTS*1536-1:0] parallel_key_chunks_q4_12;
    logic [PARALLEL_READ_PORTS*1536-1:0] parallel_value_chunks_q4_12;
    integer tiles_written = 0;

    always #5 clk = ~clk;

    rtwsr_qkv_head_buffer #(
        .QUERY_SIZE(QUERY_SIZE), .KV_SIZE(KV_SIZE), .HEAD_DIM(HEAD_DIM)
    ) dut (.*);

    function automatic integer value_for_row(input logic [4:0] command_id, input integer row);
        begin
            if (command_id == CMD_QKV) begin
                if (row < QUERY_SIZE)
                    value_for_row = 1000 + row;
                else if (row < QUERY_SIZE + KV_SIZE)
                    value_for_row = 5000 + row - QUERY_SIZE;
                else
                    value_for_row = -5000 - row + QUERY_SIZE + KV_SIZE;
            end else if (command_id == CMD_Q)
                value_for_row = 1000 + row;
            else if (command_id == CMD_K)
                value_for_row = 5000 + row;
            else
                value_for_row = -5000 - row;
        end
    endfunction

    task automatic write_tile(input logic [4:0] command_id, input integer row_start, row_count);
        integer lane;
        integer value;
        begin
            @(negedge clk);
            write_command_id = command_id;
            write_row_start = 16'(row_start);
            write_rows = 7'(row_count);
            for (lane = 0; lane < 96; lane = lane + 1) begin
                value = value_for_row(command_id, row_start + lane);
                write_result_q12[lane*32 +: 32] = 32'(value);
            end
            write_valid = 1;
            @(negedge clk);
            write_valid = 0;
            tiles_written++;
        end
    endtask

    task automatic read_head(input integer head);
        integer dimension;
        integer kv_head;
        integer chunk;
        integer lane;
        begin
            kv_head = head / (QUERY_HEADS / KV_HEADS);
            for (chunk = 0; chunk < HEAD_CHUNKS; chunk = chunk + 1) begin
                while (!read_ready) @(negedge clk);
                read_head_index = HEAD_INDEX_W'(head);
                read_chunk_index = CHUNK_INDEX_W'(chunk);
                read_start = 1;
                @(negedge clk);
                read_start = 0;
                while (!read_valid) @(negedge clk);
                for (lane = 0; lane < 96; lane = lane + 1) begin
                    dimension = chunk*96 + lane;
                    if (dimension < HEAD_DIM &&
                        ($signed(query_chunk_q4_12[lane*16 +: 16]) != 1000 + head*HEAD_DIM + dimension ||
                         $signed(key_chunk_q4_12[lane*16 +: 16]) != 5000 + kv_head*HEAD_DIM + dimension ||
                         $signed(value_chunk_q4_12[lane*16 +: 16]) != -5000 - kv_head*HEAD_DIM - dimension))
                        $fatal(1, "QKV head mismatch model=%0d head=%0d dimension=%0d q=%0d k=%0d v=%0d",
                               MODEL_ID, head, dimension,
                               $signed(query_chunk_q4_12[lane*16 +: 16]),
                               $signed(key_chunk_q4_12[lane*16 +: 16]),
                               $signed(value_chunk_q4_12[lane*16 +: 16]));
                end
                read_done = 1;
                @(negedge clk);
                read_done = 0;
            end
        end
    endtask

    initial begin
        integer row;
        integer rows;
        integer expected_tiles;
        logic [4:0] command_id;
        repeat (4) @(negedge clk);
        rst_n = 1;

        if (MODEL_ID == 0) begin
            rows = QUERY_SIZE + 2*KV_SIZE;
            for (row = 0; row < rows; row = row + 96)
                write_tile(CMD_QKV, row, (rows-row < 96) ? rows-row : 96);
            expected_tiles = (rows + 95) / 96;
        end else begin
            expected_tiles = 0;
            for (integer kind = 0; kind < 3; kind = kind + 1) begin
                command_id = kind == 0 ? CMD_Q : kind == 1 ? CMD_K : CMD_V;
                rows = kind == 0 ? QUERY_SIZE : KV_SIZE;
                for (row = 0; row < rows; row = row + 96)
                    write_tile(command_id, row, (rows-row < 96) ? rows-row : 96);
                expected_tiles += (rows + 95) / 96;
            end
        end

        if (!qkv_valid || tiles_written != expected_tiles)
            $fatal(1, "QKV buffer completion mismatch model=%0d", MODEL_ID);

        for (integer head = 0; head < QUERY_HEADS; head = head + 1)
            read_head(head);

        $display("PASS QKV buffer model=%0d query=%0d kv=%0d head_dim=%0d heads=%0d tiles=%0d",
                 MODEL_ID, QUERY_SIZE, KV_SIZE, HEAD_DIM, QUERY_HEADS, tiles_written);
        $finish;
    end
endmodule
