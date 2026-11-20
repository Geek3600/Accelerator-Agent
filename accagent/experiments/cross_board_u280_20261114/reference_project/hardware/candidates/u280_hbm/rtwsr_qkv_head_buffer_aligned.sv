`timescale 1ns / 1ps

module rtwsr_qkv_head_buffer #(
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
    input  logic                         clk,
    input  logic                         rst_n,
    input  logic                         write_valid,
    output logic                         write_ready,
    input  logic [COMMAND_W-1:0]         write_command_id,
    input  logic [15:0]                  write_row_start,
    input  logic [6:0]                   write_rows,
    input  logic [WRITE_LANES*RESULT_W-1:0] write_result_q12,
    output logic                         qkv_valid,
    input  logic                         read_start,
    input  logic [HEAD_INDEX_W-1:0]      read_head_index,
    input  logic [CHUNK_INDEX_W-1:0]     read_chunk_index,
    output logic                         read_ready,
    output logic                         read_valid,
    input  logic                         read_done,
    output logic [READ_CHUNK_WIDTH-1:0]  query_chunk_q4_12,
    output logic [READ_CHUNK_WIDTH-1:0]  key_chunk_q4_12,
    output logic [READ_CHUNK_WIDTH-1:0]  value_chunk_q4_12,
    input  logic                         parallel_read_start,
    input  logic [PARALLEL_READ_PORTS*HEAD_INDEX_W-1:0] parallel_read_heads,
    input  logic [PARALLEL_READ_PORTS*CHUNK_INDEX_W-1:0] parallel_read_chunks,
    output logic                         parallel_read_ready,
    output logic                         parallel_read_valid,
    input  logic                         parallel_read_done,
    output logic [PARALLEL_READ_PORTS*READ_CHUNK_WIDTH-1:0] parallel_query_chunks_q4_12,
    output logic [PARALLEL_READ_PORTS*READ_CHUNK_WIDTH-1:0] parallel_key_chunks_q4_12,
    output logic [PARALLEL_READ_PORTS*READ_CHUNK_WIDTH-1:0] parallel_value_chunks_q4_12
);
    (* ram_style = "block" *) logic [DATA_W-1:0] query_memory [0:WRITE_LANES-1][0:QUERY_DEPTH-1];
    (* ram_style = "block" *) logic [DATA_W-1:0] key_memory [0:WRITE_LANES-1][0:KV_DEPTH-1];
    (* ram_style = "block" *) logic [DATA_W-1:0] value_memory [0:WRITE_LANES-1][0:KV_DEPTH-1];
    (* ram_style = "block" *) logic [DATA_W-1:0]
        parallel_query_memory [0:PARALLEL_READ_PORTS-1][0:WRITE_LANES-1][0:QUERY_DEPTH-1];
    (* ram_style = "block" *) logic [DATA_W-1:0]
        parallel_key_memory [0:PARALLEL_READ_PORTS-1][0:WRITE_LANES-1][0:KV_DEPTH-1];
    (* ram_style = "block" *) logic [DATA_W-1:0]
        parallel_value_memory [0:PARALLEL_READ_PORTS-1][0:WRITE_LANES-1][0:KV_DEPTH-1];
    logic [DATA_W-1:0] query_read_q [0:WRITE_LANES-1];
    logic [DATA_W-1:0] key_read_q [0:WRITE_LANES-1];
    logic [DATA_W-1:0] value_read_q [0:WRITE_LANES-1];
    logic [DATA_W-1:0] parallel_query_read_q [0:PARALLEL_READ_PORTS-1][0:WRITE_LANES-1];
    logic [DATA_W-1:0] parallel_key_read_q [0:PARALLEL_READ_PORTS-1][0:WRITE_LANES-1];
    logic [DATA_W-1:0] parallel_value_read_q [0:PARALLEL_READ_PORTS-1][0:WRITE_LANES-1];
    logic qkv_valid_q;
    logic read_valid_q;
    logic parallel_read_valid_q;

    function automatic logic signed [DATA_W-1:0] saturate_q4_12(
        input logic signed [RESULT_W-1:0] value
    );
        begin
            if (value > 32'sd32767)
                saturate_q4_12 = 16'sd32767;
            else if (value < -32'sd32768)
                saturate_q4_12 = -16'sd32768;
            else
                saturate_q4_12 = value[DATA_W-1:0];
        end
    endfunction

    assign write_ready = 1'b1;
    assign qkv_valid = qkv_valid_q;
    assign read_ready = qkv_valid_q && !read_valid_q;
    assign read_valid = read_valid_q;
    assign parallel_read_ready = qkv_valid_q && !parallel_read_valid_q;
    assign parallel_read_valid = parallel_read_valid_q;

    for (genvar lane = 0; lane < WRITE_LANES; lane = lane + 1) begin : g_channel_bank
        integer row;
        integer bank_depth;
        integer key_row;
        integer value_row;

        always_ff @(posedge clk) begin
            if (rst_n && write_valid && write_ready && int'(write_rows) > lane) begin
                row = int'(write_row_start) + lane;
                bank_depth = int'(write_row_start) / WRITE_LANES;
                if (write_command_id == CMD_QKV) begin
                    if (row < QUERY_SIZE) begin
                        query_memory[lane][bank_depth] <= saturate_q4_12(
                            $signed(write_result_q12[lane*RESULT_W +: RESULT_W]));
                        for (integer read_port = 0; read_port < PARALLEL_READ_PORTS; read_port = read_port + 1)
                            parallel_query_memory[read_port][lane][bank_depth] <= saturate_q4_12(
                                $signed(write_result_q12[lane*RESULT_W +: RESULT_W]));
                    end
                    else if (row < QUERY_SIZE + KV_SIZE) begin
                        key_row = row - QUERY_SIZE;
                        key_memory[lane][key_row / WRITE_LANES] <= saturate_q4_12(
                            $signed(write_result_q12[lane*RESULT_W +: RESULT_W]));
                        for (integer read_port = 0; read_port < PARALLEL_READ_PORTS; read_port = read_port + 1)
                            parallel_key_memory[read_port][lane][key_row / WRITE_LANES] <= saturate_q4_12(
                                $signed(write_result_q12[lane*RESULT_W +: RESULT_W]));
                    end else if (row < QUERY_SIZE + 2*KV_SIZE) begin
                        value_row = row - QUERY_SIZE - KV_SIZE;
                        value_memory[lane][value_row / WRITE_LANES] <= saturate_q4_12(
                            $signed(write_result_q12[lane*RESULT_W +: RESULT_W]));
                        for (integer read_port = 0; read_port < PARALLEL_READ_PORTS; read_port = read_port + 1)
                            parallel_value_memory[read_port][lane][value_row / WRITE_LANES] <= saturate_q4_12(
                                $signed(write_result_q12[lane*RESULT_W +: RESULT_W]));
                    end
                end else if (write_command_id == CMD_Q_PROJ && row < QUERY_SIZE) begin
                    query_memory[lane][bank_depth] <= saturate_q4_12(
                        $signed(write_result_q12[lane*RESULT_W +: RESULT_W]));
                    for (integer read_port = 0; read_port < PARALLEL_READ_PORTS; read_port = read_port + 1)
                        parallel_query_memory[read_port][lane][bank_depth] <= saturate_q4_12(
                            $signed(write_result_q12[lane*RESULT_W +: RESULT_W]));
                end else if (write_command_id == CMD_K_PROJ && row < KV_SIZE) begin
                    key_memory[lane][bank_depth] <= saturate_q4_12(
                        $signed(write_result_q12[lane*RESULT_W +: RESULT_W]));
                    for (integer read_port = 0; read_port < PARALLEL_READ_PORTS; read_port = read_port + 1)
                        parallel_key_memory[read_port][lane][bank_depth] <= saturate_q4_12(
                            $signed(write_result_q12[lane*RESULT_W +: RESULT_W]));
                end else if (write_command_id == CMD_V_PROJ && row < KV_SIZE) begin
                    value_memory[lane][bank_depth] <= saturate_q4_12(
                        $signed(write_result_q12[lane*RESULT_W +: RESULT_W]));
                    for (integer read_port = 0; read_port < PARALLEL_READ_PORTS; read_port = read_port + 1)
                        parallel_value_memory[read_port][lane][bank_depth] <= saturate_q4_12(
                            $signed(write_result_q12[lane*RESULT_W +: RESULT_W]));
                end
            end
        end

        always_ff @(posedge clk) begin
            integer query_row;
        integer query_base;
        integer query_lane;
            integer key_head;
            integer key_row;
        integer key_base;
        integer key_lane;
            if (!rst_n) begin
                query_read_q[lane] <= '0;
                key_read_q[lane] <= '0;
                value_read_q[lane] <= '0;
            end else if (read_start && read_ready) begin
                query_base = int'(read_head_index) * HEAD_DIM +
                             int'(read_chunk_index) * WRITE_LANES;
                query_lane = HEAD_DIM % WRITE_LANES == 0 ? lane :
                             (lane - (query_base % WRITE_LANES) + WRITE_LANES) % WRITE_LANES;
                query_row = query_base + query_lane;
                key_head = int'(read_head_index) / (QUERY_HEADS / KV_HEADS);
                key_base = key_head * HEAD_DIM + int'(read_chunk_index) * WRITE_LANES;
                key_lane = HEAD_DIM % WRITE_LANES == 0 ? lane :
                           (lane - (key_base % WRITE_LANES) + WRITE_LANES) % WRITE_LANES;
                key_row = key_base + key_lane;
                if (query_row < (int'(read_head_index) + 1) * HEAD_DIM && query_row < QUERY_SIZE)
                    query_read_q[lane] <= query_memory[lane][query_row / WRITE_LANES];
                else
                    query_read_q[lane] <= '0;
                if (key_row < (key_head + 1) * HEAD_DIM && key_row < KV_SIZE) begin
                    key_read_q[lane] <= key_memory[lane][key_row / WRITE_LANES];
                    value_read_q[lane] <= value_memory[lane][key_row / WRITE_LANES];
                end else begin
                    key_read_q[lane] <= '0;
                    value_read_q[lane] <= '0;
                end
            end
        end

        for (genvar read_port = 0; read_port < PARALLEL_READ_PORTS; read_port = read_port + 1) begin : g_parallel_read
            integer query_head;
            integer query_chunk;
            integer query_base;
            integer query_lane;
            integer query_row;
            integer key_head;
            integer key_chunk;
            integer key_base;
            integer key_lane;
            integer key_row;

            always_ff @(posedge clk) begin
                if (!rst_n) begin
                    parallel_query_read_q[read_port][lane] <= '0;
                    parallel_key_read_q[read_port][lane] <= '0;
                    parallel_value_read_q[read_port][lane] <= '0;
                end else if (parallel_read_start && parallel_read_ready) begin
                    query_head = int'(parallel_read_heads[read_port*HEAD_INDEX_W +: HEAD_INDEX_W]);
                    query_chunk = int'(parallel_read_chunks[read_port*CHUNK_INDEX_W +: CHUNK_INDEX_W]);
                    query_base = query_head * HEAD_DIM + query_chunk * WRITE_LANES;
                    query_lane = HEAD_DIM % WRITE_LANES == 0 ? lane :
                                 (lane - (query_base % WRITE_LANES) + WRITE_LANES) % WRITE_LANES;
                    query_row = query_base + query_lane;
                    key_head = query_head / (QUERY_HEADS / KV_HEADS);
                    key_chunk = query_chunk;
                    key_base = key_head * HEAD_DIM + key_chunk * WRITE_LANES;
                    key_lane = HEAD_DIM % WRITE_LANES == 0 ? lane :
                               (lane - (key_base % WRITE_LANES) + WRITE_LANES) % WRITE_LANES;
                    key_row = key_base + key_lane;
                    if (query_head < QUERY_HEADS && query_row < (query_head + 1) * HEAD_DIM &&
                        query_row < QUERY_SIZE)
                        parallel_query_read_q[read_port][lane] <=
                            parallel_query_memory[read_port][lane][query_row / WRITE_LANES];
                    else
                        parallel_query_read_q[read_port][lane] <= '0;
                    if (key_row < (key_head + 1) * HEAD_DIM && key_row < KV_SIZE) begin
                        parallel_key_read_q[read_port][lane] <= parallel_key_memory[read_port][lane][key_row / WRITE_LANES];
                        parallel_value_read_q[read_port][lane] <= parallel_value_memory[read_port][lane][key_row / WRITE_LANES];
                    end else begin
                        parallel_key_read_q[read_port][lane] <= '0;
                        parallel_value_read_q[read_port][lane] <= '0;
                    end
                end
            end
        end

    end

    always_comb begin
        integer lane;
        integer query_row;
        integer query_head_base;
        integer query_bank;
        integer key_head;
        integer key_row;
        integer key_head_base;
        integer key_bank;

        query_chunk_q4_12 = '0;
        key_chunk_q4_12 = '0;
        value_chunk_q4_12 = '0;
        query_head_base = int'(read_head_index) * HEAD_DIM;
        key_head = int'(read_head_index) / (QUERY_HEADS / KV_HEADS);
        key_head_base = key_head * HEAD_DIM;
        for (lane = 0; lane < WRITE_LANES; lane = lane + 1) begin
            query_row = query_head_base + int'(read_chunk_index) * WRITE_LANES + lane;
            query_bank = HEAD_DIM % WRITE_LANES == 0 ? lane : query_row % WRITE_LANES;
            key_row = key_head_base + int'(read_chunk_index) * WRITE_LANES + lane;
            key_bank = HEAD_DIM % WRITE_LANES == 0 ? lane : key_row % WRITE_LANES;
            if (query_row < (int'(read_head_index) + 1) * HEAD_DIM)
                query_chunk_q4_12[lane*DATA_W +: DATA_W] = query_read_q[query_bank];
            if (key_row < (key_head + 1) * HEAD_DIM) begin
                key_chunk_q4_12[lane*DATA_W +: DATA_W] = key_read_q[key_bank];
                value_chunk_q4_12[lane*DATA_W +: DATA_W] = value_read_q[key_bank];
            end
        end
    end

    always_comb begin
        integer read_port;
        integer lane;
        integer query_head;
        integer query_chunk;
        integer query_row;
        integer query_bank;
        integer key_head;
        integer key_row;
        integer key_bank;

        parallel_query_chunks_q4_12 = '0;
        parallel_key_chunks_q4_12 = '0;
        parallel_value_chunks_q4_12 = '0;
        for (read_port = 0; read_port < PARALLEL_READ_PORTS; read_port = read_port + 1) begin
            query_head = int'(parallel_read_heads[read_port*HEAD_INDEX_W +: HEAD_INDEX_W]);
            query_chunk = int'(parallel_read_chunks[read_port*CHUNK_INDEX_W +: CHUNK_INDEX_W]);
            key_head = query_head / (QUERY_HEADS / KV_HEADS);
            for (lane = 0; lane < WRITE_LANES; lane = lane + 1) begin
                query_row = query_head * HEAD_DIM + query_chunk * WRITE_LANES + lane;
                query_bank = HEAD_DIM % WRITE_LANES == 0 ? lane : query_row % WRITE_LANES;
                key_row = key_head * HEAD_DIM + query_chunk * WRITE_LANES + lane;
                key_bank = HEAD_DIM % WRITE_LANES == 0 ? lane : key_row % WRITE_LANES;
                if (query_row < (query_head + 1) * HEAD_DIM && query_row < QUERY_SIZE)
                    parallel_query_chunks_q4_12[read_port*READ_CHUNK_WIDTH + lane*DATA_W +: DATA_W] =
                        parallel_query_read_q[read_port][query_bank];
                if (key_row < (key_head + 1) * HEAD_DIM && key_row < KV_SIZE) begin
                    parallel_key_chunks_q4_12[read_port*READ_CHUNK_WIDTH + lane*DATA_W +: DATA_W] =
                        parallel_key_read_q[read_port][key_bank];
                    parallel_value_chunks_q4_12[read_port*READ_CHUNK_WIDTH + lane*DATA_W +: DATA_W] =
                        parallel_value_read_q[read_port][key_bank];
                end
            end
        end
    end

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            qkv_valid_q <= 1'b0;
            read_valid_q <= 1'b0;
            parallel_read_valid_q <= 1'b0;
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
                int'(read_chunk_index) < CHUNKS_PER_HEAD)
                read_valid_q <= 1'b1;
            else if (read_valid_q && read_done)
                read_valid_q <= 1'b0;

            if (parallel_read_start && parallel_read_ready)
                parallel_read_valid_q <= 1'b1;
            else if (parallel_read_valid_q && parallel_read_done)
                parallel_read_valid_q <= 1'b0;
        end
    end

    initial begin
        if (QUERY_SIZE < 1 || KV_SIZE < 1 || HEAD_DIM < 1 ||
            QUERY_SIZE % HEAD_DIM != 0 || KV_SIZE % HEAD_DIM != 0 ||
            QUERY_HEADS % KV_HEADS != 0 || WRITE_LANES != 96 || PARALLEL_READ_PORTS < 1 ||
            DATA_W != 16 || RESULT_W != 32)
            $error("Plan 6 QKV buffer requires divisible heads and 96x32-bit result tiles");
    end
endmodule
