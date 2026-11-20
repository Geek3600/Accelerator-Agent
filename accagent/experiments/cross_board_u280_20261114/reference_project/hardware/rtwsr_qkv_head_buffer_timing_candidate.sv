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
    output logic [READ_CHUNK_WIDTH-1:0]  value_chunk_q4_12
);
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


    localparam int QUERY_ADDR_W = QUERY_DEPTH <= 1 ? 1 : $clog2(QUERY_DEPTH);
    localparam int KV_ADDR_W = KV_DEPTH <= 1 ? 1 : $clog2(KV_DEPTH);
    localparam int BANK_INDEX_W = $clog2(WRITE_LANES);
    localparam int HEAD_LAYOUT_W = QUERY_ADDR_W + KV_ADDR_W + 2*BANK_INDEX_W;
    typedef enum logic [2:0] {IDLE, READ_ADDRESS, READ_MEMORY, ROTATE_OUTPUT, OUTPUT_VALID} read_state_t;
    read_state_t read_state_q;
    (* rom_style = "distributed" *) logic [HEAD_LAYOUT_W-1:0] head_layout [0:QUERY_HEADS-1];
    logic [QUERY_ADDR_W-1:0] query_base_q;
    logic [KV_ADDR_W-1:0] key_base_q;
    logic [BANK_INDEX_W-1:0] query_offset_q, key_offset_q;
    logic [CHUNK_INDEX_W-1:0] chunk_q;
    logic [WRITE_LANES-1:0] lane_mask_q;
    logic [QUERY_ADDR_W-1:0] query_address_q [0:WRITE_LANES-1];
    logic [KV_ADDR_W-1:0] key_address_q [0:WRITE_LANES-1];
    logic [READ_CHUNK_WIDTH-1:0] query_banks_q, key_banks_q, value_banks_q;
    logic [READ_CHUNK_WIDTH-1:0] query_rotated, key_rotated, value_rotated;
    logic [16:0] write_tile_index;
    logic qkv_valid_q;

    // Constant head geometry is decoded before the registered RAM addresses.
    initial begin
        for (integer head = 0; head < QUERY_HEADS; head++)
            head_layout[head] = {
                QUERY_ADDR_W'((head * HEAD_DIM) / WRITE_LANES),
                KV_ADDR_W'(((head / (QUERY_HEADS / KV_HEADS)) * HEAD_DIM) / WRITE_LANES),
                BANK_INDEX_W'((head * HEAD_DIM) % WRITE_LANES),
                BANK_INDEX_W'(((head / (QUERY_HEADS / KV_HEADS)) * HEAD_DIM) % WRITE_LANES)
            };
    end

    assign write_ready = 1'b1;
    assign qkv_valid = qkv_valid_q;
    assign read_ready = qkv_valid_q && read_state_q == IDLE;
    assign read_valid = read_state_q == OUTPUT_VALID;
    assign write_tile_index = {1'b0, write_row_start} / 17'(WRITE_LANES);
    assign query_rotated = {query_banks_q, query_banks_q} >> (query_offset_q * DATA_W);
    assign key_rotated = {key_banks_q, key_banks_q} >> (key_offset_q * DATA_W);
    assign value_rotated = {value_banks_q, value_banks_q} >> (key_offset_q * DATA_W);

    for (genvar bank = 0; bank < WRITE_LANES; bank++) begin : g_channel_bank
        localparam int KEY_SOURCE_LANE = (QUERY_SIZE + bank) % WRITE_LANES;
        localparam int VALUE_SOURCE_LANE = (QUERY_SIZE + KV_SIZE + bank) % WRITE_LANES;
        localparam int KEY_TILE_OFFSET = QUERY_SIZE / WRITE_LANES +
            ((bank + QUERY_SIZE % WRITE_LANES) >= WRITE_LANES);
        localparam int VALUE_TILE_OFFSET = (QUERY_SIZE + KV_SIZE) / WRITE_LANES +
            ((bank + (QUERY_SIZE + KV_SIZE) % WRITE_LANES) >= WRITE_LANES);
        (* ram_style = "block" *) logic [DATA_W-1:0] query_memory [0:QUERY_DEPTH-1];
        (* ram_style = "block" *) logic [DATA_W-1:0] key_memory [0:KV_DEPTH-1];
        (* ram_style = "block" *) logic [DATA_W-1:0] value_memory [0:KV_DEPTH-1];
        logic [16:0] query_row, key_row, value_row;
        logic query_write, key_write, value_write;
        logic [KV_ADDR_W-1:0] key_write_address, value_write_address;

        assign query_row = {1'b0, write_row_start} + 17'(bank);
        assign key_row = write_command_id == CMD_QKV ?
            {1'b0, write_row_start} + 17'(KEY_SOURCE_LANE) - 17'(QUERY_SIZE) : query_row;
        assign value_row = write_command_id == CMD_QKV ?
            {1'b0, write_row_start} + 17'(VALUE_SOURCE_LANE) - 17'(QUERY_SIZE + KV_SIZE) : query_row;
        assign query_write = rst_n && write_valid && write_rows > bank && query_row < QUERY_SIZE &&
            (write_command_id == CMD_QKV || write_command_id == CMD_Q_PROJ);
        assign key_write = rst_n && write_valid && key_row < KV_SIZE &&
            ((write_command_id == CMD_QKV && write_rows > KEY_SOURCE_LANE) ||
             (write_command_id == CMD_K_PROJ && write_rows > bank));
        assign value_write = rst_n && write_valid && value_row < KV_SIZE &&
            ((write_command_id == CMD_QKV && write_rows > VALUE_SOURCE_LANE) ||
             (write_command_id == CMD_V_PROJ && write_rows > bank));
        assign key_write_address = write_command_id == CMD_QKV ?
            KV_ADDR_W'(write_tile_index - KEY_TILE_OFFSET) : KV_ADDR_W'(write_tile_index);
        assign value_write_address = write_command_id == CMD_QKV ?
            KV_ADDR_W'(write_tile_index - VALUE_TILE_OFFSET) : KV_ADDR_W'(write_tile_index);
        // Each bank has one write port and one synchronous read port, without array resets.
        always_ff @(posedge clk) begin
            if (query_write)
                query_memory[QUERY_ADDR_W'(write_tile_index)] <=
                    saturate_q4_12($signed(write_result_q12[bank*RESULT_W +: RESULT_W]));
            if (key_write)
                key_memory[key_write_address] <= saturate_q4_12(write_command_id == CMD_QKV ?
                    $signed(write_result_q12[KEY_SOURCE_LANE*RESULT_W +: RESULT_W]) :
                    $signed(write_result_q12[bank*RESULT_W +: RESULT_W]));
            if (value_write)
                value_memory[value_write_address] <= saturate_q4_12(write_command_id == CMD_QKV ?
                    $signed(write_result_q12[VALUE_SOURCE_LANE*RESULT_W +: RESULT_W]) :
                    $signed(write_result_q12[bank*RESULT_W +: RESULT_W]));
            if (read_state_q == READ_MEMORY) begin
                query_banks_q[bank*DATA_W +: DATA_W] <= query_memory[query_address_q[bank]];
                key_banks_q[bank*DATA_W +: DATA_W] <= key_memory[key_address_q[bank]];
                value_banks_q[bank*DATA_W +: DATA_W] <= value_memory[key_address_q[bank]];
            end
        end

        always_ff @(posedge clk) begin
            if (read_state_q == READ_ADDRESS) begin
                query_address_q[bank] <= query_base_q + QUERY_ADDR_W'(chunk_q) +
                                         QUERY_ADDR_W'(bank < query_offset_q);
                key_address_q[bank] <= key_base_q + KV_ADDR_W'(chunk_q) +
                                       KV_ADDR_W'(bank < key_offset_q);
            end
            if (read_state_q == ROTATE_OUTPUT) begin
                query_chunk_q4_12[bank*DATA_W +: DATA_W] <= lane_mask_q[bank] ?
                    query_rotated[bank*DATA_W +: DATA_W] : '0;
                key_chunk_q4_12[bank*DATA_W +: DATA_W] <= lane_mask_q[bank] ?
                    key_rotated[bank*DATA_W +: DATA_W] : '0;
                value_chunk_q4_12[bank*DATA_W +: DATA_W] <= lane_mask_q[bank] ?
                    value_rotated[bank*DATA_W +: DATA_W] : '0;
            end
        end
    end

    always_ff @(posedge clk) begin
        if (read_start && read_ready && int'(read_head_index) < QUERY_HEADS &&
            int'(read_chunk_index) < CHUNKS_PER_HEAD) begin
            {query_base_q, key_base_q, query_offset_q, key_offset_q} <= head_layout[read_head_index];
            chunk_q <= read_chunk_index;
            for (integer lane = 0; lane < WRITE_LANES; lane++)
                lane_mask_q[lane] <= int'(read_chunk_index) * WRITE_LANES + lane < HEAD_DIM;
        end
    end

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            qkv_valid_q <= 1'b0;
            read_state_q <= IDLE;
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
            case (read_state_q)
                IDLE: if (read_start && read_ready && int'(read_head_index) < QUERY_HEADS &&
                          int'(read_chunk_index) < CHUNKS_PER_HEAD)
                    read_state_q <= READ_ADDRESS;
                READ_ADDRESS: read_state_q <= READ_MEMORY;
                READ_MEMORY: read_state_q <= ROTATE_OUTPUT;
                ROTATE_OUTPUT: read_state_q <= OUTPUT_VALID;
                OUTPUT_VALID: if (read_done) read_state_q <= IDLE;
                default: read_state_q <= IDLE;
            endcase
        end
    end
    initial begin
        if (QUERY_SIZE < 1 || KV_SIZE < 1 || HEAD_DIM < 1 ||
            QUERY_SIZE % HEAD_DIM != 0 || KV_SIZE % HEAD_DIM != 0 ||
            QUERY_HEADS % KV_HEADS != 0 || WRITE_LANES != 96 ||
            DATA_W != 16 || RESULT_W != 32)
            $error("Plan 6 QKV buffer requires divisible heads and 96x32-bit result tiles");
    end
endmodule
