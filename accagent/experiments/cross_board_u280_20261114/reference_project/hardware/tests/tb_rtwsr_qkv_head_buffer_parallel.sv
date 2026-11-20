`timescale 1ns / 1ps

module tb_rtwsr_qkv_head_buffer_parallel #(
    parameter int PARALLEL_READ_PORTS = 4
);
    localparam int QUERY_SIZE = 5280;
    localparam int KV_SIZE = 5280;
    localparam int HEAD_DIM = 96;
    localparam int QUERY_HEADS = QUERY_SIZE / HEAD_DIM;
    localparam int HEAD_INDEX_W = $clog2(QUERY_HEADS);
    localparam logic [4:0] CMD_QKV = 5'd3;

    logic clk = 0, rst_n = 0;
    logic write_valid = 0, write_ready;
    logic [4:0] write_command_id = CMD_QKV;
    logic [15:0] write_row_start = 0;
    logic [6:0] write_rows = 0;
    logic [3071:0] write_result_q12 = '0;
    logic qkv_valid;
    logic read_start = 0, read_ready, read_valid, read_done = 0;
    logic [HEAD_INDEX_W-1:0] read_head_index = '0;
    logic read_chunk_index = 0;
    logic [1535:0] query_chunk_q4_12, key_chunk_q4_12, value_chunk_q4_12;
    logic parallel_read_start = 0, parallel_read_ready, parallel_read_valid;
    logic [PARALLEL_READ_PORTS*HEAD_INDEX_W-1:0] parallel_read_heads = '0;
    logic [PARALLEL_READ_PORTS-1:0] parallel_read_chunks = '0;
    logic parallel_read_done = 0;
    logic [PARALLEL_READ_PORTS*1536-1:0] parallel_query_chunks_q4_12;
    logic [PARALLEL_READ_PORTS*1536-1:0] parallel_key_chunks_q4_12;
    logic [PARALLEL_READ_PORTS*1536-1:0] parallel_value_chunks_q4_12;
    integer cycle_count = 0;
    integer serial_cycles = 0;
    integer parallel_cycles = 0;

    always #5 clk = ~clk;
    always @(posedge clk)
        cycle_count++;

    rtwsr_qkv_head_buffer_banked #(
        .QUERY_SIZE(QUERY_SIZE), .KV_SIZE(KV_SIZE), .HEAD_DIM(HEAD_DIM),
        .PARALLEL_READ_PORTS(PARALLEL_READ_PORTS)
    ) dut (.*);

    function automatic integer q_value(input integer row);
        q_value = 1000 + row;
    endfunction

    function automatic integer k_value(input integer row);
        k_value = 5000 + row;
    endfunction

    function automatic integer v_value(input integer row);
        v_value = -5000 - row;
    endfunction

    task automatic write_tile(input integer row_start);
        integer row;
        begin
            @(negedge clk);
            write_row_start = 16'(row_start);
            write_rows = 7'd96;
            for (integer lane = 0; lane < 96; lane++) begin
                row = row_start + lane;
                if (row < QUERY_SIZE)
                    write_result_q12[lane*32 +: 32] = 32'(q_value(row));
                else if (row < QUERY_SIZE + KV_SIZE)
                    write_result_q12[lane*32 +: 32] = 32'(k_value(row - QUERY_SIZE));
                else
                    write_result_q12[lane*32 +: 32] = 32'(v_value(row - QUERY_SIZE - KV_SIZE));
            end
            write_valid = 1;
            @(negedge clk);
            write_valid = 0;
        end
    endtask

    task automatic check_parallel_batch(input integer head_base);
        integer head;
        integer wait_count;
        integer cycle_start;
        begin
            for (integer port = 0; port < PARALLEL_READ_PORTS; port++) begin
                head = head_base + port;
                if (head >= QUERY_HEADS)
                    head = QUERY_HEADS - 1;
                parallel_read_heads[port*HEAD_INDEX_W +: HEAD_INDEX_W] = HEAD_INDEX_W'(head);
                parallel_read_chunks[port] = 1'b0;
            end
            wait_count = 0;
            while (!parallel_read_ready && wait_count < 20) begin
                @(negedge clk);
                wait_count++;
            end
            if (!parallel_read_ready)
                $fatal(1, "parallel QKV read did not become ready");
            cycle_start = cycle_count;
            parallel_read_start = 1;
            @(negedge clk);
            parallel_read_start = 0;
            wait_count = 0;
            while (!parallel_read_valid && wait_count < 20) begin
                @(negedge clk);
                wait_count++;
            end
            if (!parallel_read_valid)
                $fatal(1, "parallel QKV read did not return data");
            for (integer port = 0; port < PARALLEL_READ_PORTS; port++) begin
                head = int'(parallel_read_heads[port*HEAD_INDEX_W +: HEAD_INDEX_W]);
                if (head_base + port < QUERY_HEADS) begin
                for (integer dim = 0; dim < HEAD_DIM; dim++) begin
                    if ($signed(parallel_query_chunks_q4_12[port*1536 + dim*16 +: 16]) !==
                            q_value(head*HEAD_DIM + dim) ||
                        $signed(parallel_key_chunks_q4_12[port*1536 + dim*16 +: 16]) !==
                            k_value(head*HEAD_DIM + dim) ||
                        $signed(parallel_value_chunks_q4_12[port*1536 + dim*16 +: 16]) !==
                            v_value(head*HEAD_DIM + dim))
                        $fatal(1, "parallel QKV mismatch head=%0d dim=%0d q=%0d/%0d k=%0d/%0d v=%0d/%0d",
                               head, dim,
                               $signed(parallel_query_chunks_q4_12[port*1536 + dim*16 +: 16]),
                               q_value(head*HEAD_DIM + dim),
                               $signed(parallel_key_chunks_q4_12[port*1536 + dim*16 +: 16]),
                               k_value(head*HEAD_DIM + dim),
                               $signed(parallel_value_chunks_q4_12[port*1536 + dim*16 +: 16]),
                               v_value(head*HEAD_DIM + dim));
                end
                end
            end
            parallel_read_done = 1;
            @(negedge clk);
            parallel_read_done = 0;
            parallel_cycles += cycle_count - cycle_start;
        end
    endtask

    initial begin
        integer rows;
        integer head;
        integer wait_count;
        integer cycle_start;
        repeat (4) @(negedge clk);
        rst_n = 1;

        rows = QUERY_SIZE + 2*KV_SIZE;
        for (integer row = 0; row < rows; row += 96)
            write_tile(row);
        if (!qkv_valid)
            $fatal(1, "QKV buffer did not become valid");
        for (integer head_base = 0; head_base < QUERY_HEADS; head_base += PARALLEL_READ_PORTS)
            check_parallel_batch(head_base);

        for (integer index = 0; index < QUERY_HEADS; index++) begin
            head = index;
            wait_count = 0;
            while (!read_ready && wait_count < 20) begin
                @(negedge clk);
                wait_count++;
            end
            if (!read_ready)
                $fatal(1, "serial QKV read did not become ready");
            cycle_start = cycle_count;
            read_head_index = HEAD_INDEX_W'(head);
            read_chunk_index = 1'b0;
            read_start = 1;
            @(negedge clk);
            read_start = 0;
            wait_count = 0;
            while (!read_valid && wait_count < 20) begin
                @(negedge clk);
                wait_count++;
            end
            if (!read_valid)
                $fatal(1, "serial QKV read did not return data");
            for (integer dim = 0; dim < HEAD_DIM; dim++) begin
                if ($signed(query_chunk_q4_12[dim*16 +: 16]) !== q_value(head*HEAD_DIM + dim) ||
                    $signed(key_chunk_q4_12[dim*16 +: 16]) !== k_value(head*HEAD_DIM + dim) ||
                    $signed(value_chunk_q4_12[dim*16 +: 16]) !== v_value(head*HEAD_DIM + dim))
                    $fatal(1, "serial QKV mismatch head=%0d dim=%0d", head, dim);
            end
            read_done = 1;
            @(negedge clk);
            read_done = 0;
            serial_cycles += cycle_count - cycle_start;
        end

        if (parallel_cycles != 2*((QUERY_HEADS + PARALLEL_READ_PORTS - 1)/PARALLEL_READ_PORTS) ||
            serial_cycles != 2*QUERY_HEADS)
            $fatal(1, "QKV head count mismatch serial=%0d parallel=%0d",
                   serial_cycles, parallel_cycles);
        $display("PASS Huginn QKV per-value regression heads=%0d parallel_ports=%0d serial_read_cycles=%0d parallel_read_cycles=%0d",
                 QUERY_HEADS, PARALLEL_READ_PORTS, serial_cycles, parallel_cycles);
        $finish;
    end
endmodule
