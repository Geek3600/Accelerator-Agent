`timescale 1ns / 1ps

module rtwsr_qkv_head_buffer_banked #(
    parameter int QUERY_SIZE = 5280,
    parameter int KV_SIZE = 5280,
    parameter int HEAD_DIM = 96,
    parameter int WRITE_LANES = 96,
    parameter int DATA_W = 16,
    parameter int RESULT_W = 32,
    parameter int COMMAND_W = 5,
    parameter logic [COMMAND_W-1:0] CMD_QKV = 5'd3,
    parameter logic [COMMAND_W-1:0] CMD_Q_PROJ = 5'd18,
    parameter logic [COMMAND_W-1:0] CMD_K_PROJ = 5'd19,
    parameter logic [COMMAND_W-1:0] CMD_V_PROJ = 5'd20,
    parameter int QUERY_HEADS = QUERY_SIZE / HEAD_DIM,
    parameter int KV_HEADS = KV_SIZE / HEAD_DIM,
    parameter int QUERY_DEPTH = (QUERY_SIZE + WRITE_LANES - 1) / WRITE_LANES,
    parameter int KV_DEPTH = (KV_SIZE + WRITE_LANES - 1) / WRITE_LANES,
    parameter int HEAD_INDEX_W = (QUERY_HEADS <= 1) ? 1 : $clog2(QUERY_HEADS),
    parameter int CHUNKS_PER_HEAD = (HEAD_DIM + WRITE_LANES - 1) / WRITE_LANES,
    parameter int CHUNK_INDEX_W = (CHUNKS_PER_HEAD <= 1) ? 1 : $clog2(CHUNKS_PER_HEAD),
    parameter int PARALLEL_READ_PORTS = 4,
    parameter int READ_CHUNK_WIDTH = WRITE_LANES * DATA_W
)(
    input  logic                                  clk,
    input  logic                                  rst_n,
    input  logic                                  write_valid,
    output logic                                  write_ready,
    input  logic [COMMAND_W-1:0]                  write_command_id,
    input  logic [15:0]                           write_row_start,
    input  logic [6:0]                            write_rows,
    input  logic [WRITE_LANES*RESULT_W-1:0]       write_result_q12,
    output logic                                  qkv_valid,
    input  logic                                  read_start,
    input  logic [HEAD_INDEX_W-1:0]               read_head_index,
    input  logic [CHUNK_INDEX_W-1:0]              read_chunk_index,
    output logic                                  read_ready,
    output logic                                  read_valid,
    input  logic                                  read_done,
    output logic [READ_CHUNK_WIDTH-1:0]           query_chunk_q4_12,
    output logic [READ_CHUNK_WIDTH-1:0]           key_chunk_q4_12,
    output logic [READ_CHUNK_WIDTH-1:0]           value_chunk_q4_12,
    input  logic                                  parallel_read_start,
    input  logic [PARALLEL_READ_PORTS*HEAD_INDEX_W-1:0] parallel_read_heads,
    input  logic [PARALLEL_READ_PORTS*CHUNK_INDEX_W-1:0] parallel_read_chunks,
    output logic                                  parallel_read_ready,
    output logic                                  parallel_read_valid,
    input  logic                                  parallel_read_done,
    output logic [PARALLEL_READ_PORTS*READ_CHUNK_WIDTH-1:0] parallel_query_chunks_q4_12,
    output logic [PARALLEL_READ_PORTS*READ_CHUNK_WIDTH-1:0] parallel_key_chunks_q4_12,
    output logic [PARALLEL_READ_PORTS*READ_CHUNK_WIDTH-1:0] parallel_value_chunks_q4_12
);
    localparam bit USE_BANKED_HEADS =
        HEAD_DIM == WRITE_LANES && QUERY_HEADS == KV_HEADS && PARALLEL_READ_PORTS > 1 &&
        DATA_W == 16 && RESULT_W == 32 && (HEAD_DIM * DATA_W) % 64 == 0;

    generate
        if (USE_BANKED_HEADS) begin : g_banked
            localparam int HEAD_DATA_W = HEAD_DIM * DATA_W;
            localparam int QUERY_BANK_DEPTH_RAW =
                (QUERY_HEADS + PARALLEL_READ_PORTS - 1) / PARALLEL_READ_PORTS;
            localparam int KV_BANK_DEPTH_RAW =
                (KV_HEADS + PARALLEL_READ_PORTS - 1) / PARALLEL_READ_PORTS;
            localparam int QUERY_BANK_DEPTH = (QUERY_BANK_DEPTH_RAW < 16) ? 16 : QUERY_BANK_DEPTH_RAW;
            localparam int KV_BANK_DEPTH = (KV_BANK_DEPTH_RAW < 16) ? 16 : KV_BANK_DEPTH_RAW;
            localparam int MEMORY_CHUNK_W = 64;
            localparam int MEMORY_CHUNKS = (HEAD_DATA_W + MEMORY_CHUNK_W - 1) / MEMORY_CHUNK_W;
            localparam int BANK_ADDR_W = $clog2((QUERY_BANK_DEPTH > KV_BANK_DEPTH) ?
                QUERY_BANK_DEPTH : KV_BANK_DEPTH);

            logic qkv_valid_q;
            logic read_valid_q;
            logic parallel_read_valid_q;
            logic [HEAD_INDEX_W-1:0] serial_bank_q;
            logic [PARALLEL_READ_PORTS-1:0] parallel_duplicate_q;
            logic [HEAD_DATA_W-1:0] query_read_bank_q [0:PARALLEL_READ_PORTS-1];
            logic [HEAD_DATA_W-1:0] key_read_bank_q [0:PARALLEL_READ_PORTS-1];
            logic [HEAD_DATA_W-1:0] value_read_bank_q [0:PARALLEL_READ_PORTS-1];
            logic [MEMORY_CHUNK_W-1:0] query_read_chunk_q
                [0:PARALLEL_READ_PORTS-1][0:MEMORY_CHUNKS-1];
            logic [MEMORY_CHUNK_W-1:0] key_read_chunk_q
                [0:PARALLEL_READ_PORTS-1][0:MEMORY_CHUNKS-1];
            logic [MEMORY_CHUNK_W-1:0] value_read_chunk_q
                [0:PARALLEL_READ_PORTS-1][0:MEMORY_CHUNKS-1];
            logic [PARALLEL_READ_PORTS-1:0] parallel_request_legal;
            logic [PARALLEL_READ_PORTS-1:0] bank_write_valid;
            logic [PARALLEL_READ_PORTS-1:0] bank_write_query;
            logic [PARALLEL_READ_PORTS-1:0] bank_write_key;
            logic [PARALLEL_READ_PORTS-1:0] bank_write_value;
            logic [PARALLEL_READ_PORTS-1:0] bank_read_valid;
            logic [BANK_ADDR_W-1:0] bank_write_address [0:PARALLEL_READ_PORTS-1];
            logic [BANK_ADDR_W-1:0] bank_read_address [0:PARALLEL_READ_PORTS-1];
            integer write_head_calc;
            integer write_row_calc;
            logic write_request;
            logic write_query;
            logic write_key;
            logic write_value;

            function automatic logic [MEMORY_CHUNK_W-1:0] pack_memory_chunk(
                input logic [WRITE_LANES*RESULT_W-1:0] values,
                input integer chunk_index
            );
                begin
                    for (integer lane = 0; lane < MEMORY_CHUNK_W / DATA_W; lane = lane + 1) begin
                        if ($signed(values[(chunk_index*(MEMORY_CHUNK_W/DATA_W)+lane)*RESULT_W +: RESULT_W]) > 32'sd32767)
                            pack_memory_chunk[lane*DATA_W +: DATA_W] = 16'h7fff;
                        else if ($signed(values[(chunk_index*(MEMORY_CHUNK_W/DATA_W)+lane)*RESULT_W +: RESULT_W]) < -32'sd32768)
                            pack_memory_chunk[lane*DATA_W +: DATA_W] = 16'h8000;
                        else
                            pack_memory_chunk[lane*DATA_W +: DATA_W] =
                                values[(chunk_index*(MEMORY_CHUNK_W/DATA_W)+lane)*RESULT_W +: DATA_W];
                    end
                end
            endfunction

            always_comb begin
                integer request_head;
                parallel_request_legal = '1;
                for (integer port_id = 0; port_id < PARALLEL_READ_PORTS; port_id = port_id + 1) begin
                    request_head = int'(parallel_read_heads[port_id*HEAD_INDEX_W +: HEAD_INDEX_W]);
                    if (int'(parallel_read_chunks[port_id*CHUNK_INDEX_W +: CHUNK_INDEX_W]) != 0)
                        parallel_request_legal[port_id] = 1'b0;
                    if (request_head >= QUERY_HEADS)
                        parallel_request_legal[port_id] = 1'b0;
                    else if (request_head % PARALLEL_READ_PORTS != port_id) begin
                        if (port_id == 0 ||
                            parallel_read_heads[port_id*HEAD_INDEX_W +: HEAD_INDEX_W] !=
                                parallel_read_heads[(port_id-1)*HEAD_INDEX_W +: HEAD_INDEX_W])
                            parallel_request_legal[port_id] = 1'b0;
                    end
                end
            end

            always_comb begin
                write_row_calc = int'(write_row_start);
                write_head_calc = 0;
                write_request = 1'b0;
                write_query = 1'b0;
                write_key = 1'b0;
                write_value = 1'b0;

                if (write_valid && write_rows == HEAD_DIM &&
                    write_row_calc % HEAD_DIM == 0) begin
                    if (write_command_id == CMD_QKV) begin
                        if (write_row_calc < QUERY_SIZE) begin
                            write_head_calc = write_row_calc / HEAD_DIM;
                            write_request = 1'b1;
                            write_query = 1'b1;
                        end else if (write_row_calc < QUERY_SIZE + KV_SIZE) begin
                            write_head_calc = (write_row_calc - QUERY_SIZE) / HEAD_DIM;
                            write_request = 1'b1;
                            write_key = 1'b1;
                        end else if (write_row_calc < QUERY_SIZE + 2*KV_SIZE) begin
                            write_head_calc = (write_row_calc - QUERY_SIZE - KV_SIZE) / HEAD_DIM;
                            write_request = 1'b1;
                            write_value = 1'b1;
                        end
                    end else if (write_command_id == CMD_Q_PROJ && write_row_calc < QUERY_SIZE) begin
                        write_head_calc = write_row_calc / HEAD_DIM;
                        write_request = 1'b1;
                        write_query = 1'b1;
                    end else if (write_command_id == CMD_K_PROJ && write_row_calc < KV_SIZE) begin
                        write_head_calc = write_row_calc / HEAD_DIM;
                        write_request = 1'b1;
                        write_key = 1'b1;
                    end else if (write_command_id == CMD_V_PROJ && write_row_calc < KV_SIZE) begin
                        write_head_calc = write_row_calc / HEAD_DIM;
                        write_request = 1'b1;
                        write_value = 1'b1;
                    end
                end
            end

            always_comb begin
                integer request_head;
                for (integer bank_id = 0; bank_id < PARALLEL_READ_PORTS; bank_id = bank_id + 1) begin
                    bank_write_valid[bank_id] = write_request &&
                        write_head_calc % PARALLEL_READ_PORTS == bank_id;
                    bank_write_query[bank_id] = write_query;
                    bank_write_key[bank_id] = write_key;
                    bank_write_value[bank_id] = write_value;
                    bank_write_address[bank_id] = BANK_ADDR_W'(write_head_calc / PARALLEL_READ_PORTS);
                    bank_read_valid[bank_id] = 1'b0;
                    bank_read_address[bank_id] = '0;

                    request_head = int'(parallel_read_heads[bank_id*HEAD_INDEX_W +: HEAD_INDEX_W]);
                    if (parallel_read_start && parallel_read_ready && request_head < QUERY_HEADS &&
                        request_head % PARALLEL_READ_PORTS == bank_id) begin
                        bank_read_valid[bank_id] = 1'b1;
                        bank_read_address[bank_id] = BANK_ADDR_W'(request_head / PARALLEL_READ_PORTS);
                    end else if (read_start && read_ready && int'(read_head_index) < QUERY_HEADS &&
                                 int'(read_chunk_index) == 0 &&
                                 int'(read_head_index) % PARALLEL_READ_PORTS == bank_id) begin
                        bank_read_valid[bank_id] = 1'b1;
                        bank_read_address[bank_id] = BANK_ADDR_W'(
                            int'(read_head_index) / PARALLEL_READ_PORTS);
                    end
                end
            end

            assign write_ready = 1'b1;
            assign qkv_valid = qkv_valid_q;
            assign read_valid = read_valid_q;
            assign parallel_read_valid = parallel_read_valid_q;
            assign read_ready = qkv_valid_q && !read_valid_q && !parallel_read_valid_q &&
                !parallel_read_start;
            assign parallel_read_ready = qkv_valid_q && !read_valid_q && !parallel_read_valid_q &&
                (&parallel_request_legal);

            always_comb begin
                query_chunk_q4_12 = query_read_bank_q[serial_bank_q];
                key_chunk_q4_12 = key_read_bank_q[serial_bank_q];
                value_chunk_q4_12 = value_read_bank_q[serial_bank_q];
                parallel_query_chunks_q4_12 = '0;
                parallel_key_chunks_q4_12 = '0;
                parallel_value_chunks_q4_12 = '0;
                for (integer port_id = 0; port_id < PARALLEL_READ_PORTS; port_id = port_id + 1) begin
                    if (!parallel_duplicate_q[port_id]) begin
                        parallel_query_chunks_q4_12[port_id*READ_CHUNK_WIDTH +: HEAD_DATA_W] =
                            query_read_bank_q[port_id];
                        parallel_key_chunks_q4_12[port_id*READ_CHUNK_WIDTH +: HEAD_DATA_W] =
                            key_read_bank_q[port_id];
                        parallel_value_chunks_q4_12[port_id*READ_CHUNK_WIDTH +: HEAD_DATA_W] =
                            value_read_bank_q[port_id];
                    end
                end
            end

            always_comb begin
                for (integer bank_id = 0; bank_id < PARALLEL_READ_PORTS; bank_id = bank_id + 1) begin
                    for (integer chunk = 0; chunk < MEMORY_CHUNKS; chunk = chunk + 1) begin
                        query_read_bank_q[bank_id][chunk*MEMORY_CHUNK_W +: MEMORY_CHUNK_W] =
                            query_read_chunk_q[bank_id][chunk];
                        key_read_bank_q[bank_id][chunk*MEMORY_CHUNK_W +: MEMORY_CHUNK_W] =
                            key_read_chunk_q[bank_id][chunk];
                        value_read_bank_q[bank_id][chunk*MEMORY_CHUNK_W +: MEMORY_CHUNK_W] =
                            value_read_chunk_q[bank_id][chunk];
                    end
                end
            end

            for (genvar bank = 0; bank < PARALLEL_READ_PORTS; bank = bank + 1) begin : g_bank
                for (genvar chunk = 0; chunk < MEMORY_CHUNKS; chunk = chunk + 1) begin : g_word
                    (* ram_style = "block" *) logic [MEMORY_CHUNK_W-1:0]
                        query_memory [0:QUERY_BANK_DEPTH-1];
                    (* ram_style = "block" *) logic [MEMORY_CHUNK_W-1:0]
                        key_memory [0:KV_BANK_DEPTH-1];
                    (* ram_style = "block" *) logic [MEMORY_CHUNK_W-1:0]
                        value_memory [0:KV_BANK_DEPTH-1];

                    always_ff @(posedge clk) begin
                        if (rst_n) begin
                            if (bank_write_valid[bank]) begin
                                if (bank_write_query[bank])
                                    query_memory[bank_write_address[bank]] <=
                                        pack_memory_chunk(write_result_q12, chunk);
                                if (bank_write_key[bank])
                                    key_memory[bank_write_address[bank]] <=
                                        pack_memory_chunk(write_result_q12, chunk);
                                if (bank_write_value[bank])
                                    value_memory[bank_write_address[bank]] <=
                                        pack_memory_chunk(write_result_q12, chunk);
                            end
                            if (bank_read_valid[bank]) begin
                                query_read_chunk_q[bank][chunk] <= query_memory[bank_read_address[bank]];
                                key_read_chunk_q[bank][chunk] <= key_memory[bank_read_address[bank]];
                                value_read_chunk_q[bank][chunk] <= value_memory[bank_read_address[bank]];
                            end
                        end
                    end
                end
            end

            always_ff @(posedge clk) begin
                if (!rst_n) begin
                    qkv_valid_q <= 1'b0;
                    read_valid_q <= 1'b0;
                    parallel_read_valid_q <= 1'b0;
                    serial_bank_q <= '0;
                    parallel_duplicate_q <= '0;
                end else begin
                    if (write_valid) begin
                        if (write_command_id == CMD_QKV || write_command_id == CMD_Q_PROJ)
                            qkv_valid_q <= 1'b0;
                        if (write_command_id == CMD_QKV &&
                            int'(write_row_start) + int'(write_rows) >= QUERY_SIZE + 2*KV_SIZE)
                            qkv_valid_q <= 1'b1;
                        if (write_command_id == CMD_V_PROJ &&
                            int'(write_row_start) + int'(write_rows) >= KV_SIZE)
                            qkv_valid_q <= 1'b1;
                    end

                    if (read_start && read_ready && int'(read_head_index) < QUERY_HEADS &&
                        int'(read_chunk_index) == 0) begin
                        read_valid_q <= 1'b1;
                        serial_bank_q <= HEAD_INDEX_W'(int'(read_head_index) % PARALLEL_READ_PORTS);
                    end else if (read_valid_q && read_done) begin
                        read_valid_q <= 1'b0;
                    end

                    if (parallel_read_start && parallel_read_ready) begin
                        parallel_read_valid_q <= 1'b1;
                        for (integer port_id = 0; port_id < PARALLEL_READ_PORTS; port_id = port_id + 1)
                            parallel_duplicate_q[port_id] <= port_id > 0 &&
                                parallel_read_heads[port_id*HEAD_INDEX_W +: HEAD_INDEX_W] ==
                                parallel_read_heads[(port_id-1)*HEAD_INDEX_W +: HEAD_INDEX_W] &&
                                int'(parallel_read_heads[port_id*HEAD_INDEX_W +: HEAD_INDEX_W]) %
                                    PARALLEL_READ_PORTS != port_id;
                    end else if (parallel_read_valid_q && parallel_read_done) begin
                        parallel_read_valid_q <= 1'b0;
                        parallel_duplicate_q <= '0;
                    end
                end
            end

        end else begin : g_legacy
            rtwsr_qkv_head_buffer #(
                .QUERY_SIZE(QUERY_SIZE), .KV_SIZE(KV_SIZE), .HEAD_DIM(HEAD_DIM),
                .WRITE_LANES(WRITE_LANES), .DATA_W(DATA_W), .RESULT_W(RESULT_W),
                .COMMAND_W(COMMAND_W), .CMD_QKV(CMD_QKV), .CMD_Q_PROJ(CMD_Q_PROJ),
                .CMD_K_PROJ(CMD_K_PROJ), .CMD_V_PROJ(CMD_V_PROJ),
                .QUERY_HEADS(QUERY_HEADS), .KV_HEADS(KV_HEADS), .QUERY_DEPTH(QUERY_DEPTH),
                .KV_DEPTH(KV_DEPTH), .HEAD_INDEX_W(HEAD_INDEX_W),
                .CHUNKS_PER_HEAD(CHUNKS_PER_HEAD), .CHUNK_INDEX_W(CHUNK_INDEX_W),
                .PARALLEL_READ_PORTS(PARALLEL_READ_PORTS), .READ_CHUNK_WIDTH(READ_CHUNK_WIDTH)
            ) u_legacy (.*);
        end
    endgenerate
endmodule
