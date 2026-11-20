`timescale 1ns / 1ps

module rtwsr_runtime_gamma_pool #(
    parameter int MAX_ROWS = 17920,
    parameter int CHANNELS = 96,
    parameter int MAX_PAIRS = (MAX_ROWS + 1) / 2,
    parameter bit PARALLEL_LOAD = 1'b0,
    parameter int TILE_INDEX_WIDTH = 9,
    parameter int PAIR_ADDR_WIDTH = $clog2(MAX_PAIRS),
    parameter int COUNT_WIDTH = $clog2(MAX_PAIRS + 1)
)(
    input  logic                       clk,
    input  logic                       rst_n,
    input  logic                       load_abort,
    input  logic                       load_start,
    output logic                       load_start_ready,
    input  logic [4:0]                 load_command_id,
    input  logic [5:0]                 load_block_index,
    input  logic [4:0]                 load_recurrence_index,
    input  logic [15:0]                load_matrix_rows,
    input  logic [15:0]                load_matrix_columns,
    input  logic                       load_valid,
    output logic                       load_ready,
    input  logic [31:0]                load_pair_data,
    input  logic [511:0]               load_vector_data,
    input  logic                       load_last,
    output logic                       load_done,
    output logic                       protocol_error,
    input  logic                       read_enable,
    input  logic [4:0]                 read_command_id,
    input  logic [5:0]                 read_block_index,
    input  logic [4:0]                 read_recurrence_index,
    input  logic [15:0]                read_matrix_rows,
    input  logic [15:0]                read_matrix_columns,
    input  logic [TILE_INDEX_WIDTH-1:0] read_tile_index,
    input  logic                       release_enable,
    input  logic [TILE_INDEX_WIDTH-1:0] release_tile_index,
    output logic                       read_match,
    output logic                       read_valid,
    output logic [CHANNELS*16-1:0]     read_tile_data
);
    localparam int BANK_DEPTH = (MAX_PAIRS + 15) / 16;
    localparam int WRITE_LANES = PARALLEL_LOAD ? 16 : 1;
    localparam int TILE_PAIR_COUNT = CHANNELS / 2;
    localparam int TILE_PAIR_WIDTH = (TILE_PAIR_COUNT < 2) ? 1 : $clog2(TILE_PAIR_COUNT + 1);
    (* ram_style = "block" *) logic [511:0] gamma_bank_0 [0:BANK_DEPTH-1];
    (* ram_style = "block" *) logic [511:0] gamma_bank_1 [0:BANK_DEPTH-1];
    logic bank_0_valid_q, bank_1_valid_q;
    logic [4:0] bank_0_command_q, bank_1_command_q;
    logic [5:0] bank_0_block_q, bank_1_block_q;
    logic [4:0] bank_0_recurrence_q, bank_1_recurrence_q;
    logic [15:0] bank_0_rows_q, bank_1_rows_q;
    logic [15:0] bank_0_columns_q, bank_1_columns_q;
    logic [CHANNELS*16-1:0] gamma_tile_data_q [0:1];
    logic [4:0] cache_command_q [0:1];
    logic [5:0] cache_block_q [0:1];
    logic [4:0] cache_recurrence_q [0:1];
    logic [15:0] cache_rows_q [0:1];
    logic [15:0] cache_columns_q [0:1];
    logic [TILE_INDEX_WIDTH-1:0] cache_tile_q [0:1];
    logic cache_valid_q [0:1];
    logic cache_bank_q [0:1];
    logic load_busy_q, load_bank_q;
    logic [COUNT_WIDTH-1:0] load_count_q, load_pairs_q;
    logic [4:0] load_command_q;
    logic [5:0] load_block_q;
    logic [4:0] load_recurrence_q;
    logic [15:0] load_rows_q, load_columns_q;
    logic read_bank_0, read_bank_1;
    logic cache_match_0, cache_match_1;
    logic release_cache_0, release_cache_1;
    logic stale_cache_0, stale_cache_1;
    logic slot_available_0, slot_available_1;
    logic candidate_valid, candidate_cached, prefetch_start, prefetch_slot;
    logic [TILE_INDEX_WIDTH-1:0] candidate_tile;
    logic prefetch_busy_q, prefetch_bank_q, prefetch_slot_q;
    logic [TILE_INDEX_WIDTH-1:0] prefetch_tile_q;
    logic [TILE_PAIR_WIDTH-1:0] prefetch_pair_q;
    logic [4:0] prefetch_command_q;
    logic [5:0] prefetch_block_q;
    logic [4:0] prefetch_recurrence_q;
    logic [15:0] prefetch_rows_q, prefetch_columns_q;
    logic [PAIR_ADDR_WIDTH-1:0] prefetch_address;
    logic descriptor_valid;
    logic load_fire;

    assign read_bank_0 = bank_0_valid_q &&
        bank_0_command_q == read_command_id &&
        bank_0_block_q == read_block_index &&
        bank_0_recurrence_q == read_recurrence_index &&
        bank_0_rows_q == read_matrix_rows &&
        bank_0_columns_q == read_matrix_columns;
    assign read_bank_1 = bank_1_valid_q &&
        bank_1_command_q == read_command_id &&
        bank_1_block_q == read_block_index &&
        bank_1_recurrence_q == read_recurrence_index &&
        bank_1_rows_q == read_matrix_rows &&
        bank_1_columns_q == read_matrix_columns;
    assign cache_match_0 = cache_valid_q[0] &&
        cache_command_q[0] == read_command_id &&
        cache_block_q[0] == read_block_index &&
        cache_recurrence_q[0] == read_recurrence_index &&
        cache_rows_q[0] == read_matrix_rows &&
        cache_columns_q[0] == read_matrix_columns &&
        cache_tile_q[0] == read_tile_index;
    assign cache_match_1 = cache_valid_q[1] &&
        cache_command_q[1] == read_command_id &&
        cache_block_q[1] == read_block_index &&
        cache_recurrence_q[1] == read_recurrence_index &&
        cache_rows_q[1] == read_matrix_rows &&
        cache_columns_q[1] == read_matrix_columns &&
        cache_tile_q[1] == read_tile_index;
    assign read_match = cache_match_0 || cache_match_1;
    assign read_valid = read_match;
    assign read_tile_data = cache_match_0 ? gamma_tile_data_q[0] :
                            cache_match_1 ? gamma_tile_data_q[1] : '0;
    assign load_start_ready = !load_busy_q && !(read_bank_0 && read_bank_1);
    assign load_ready = load_busy_q;
    assign load_fire = load_busy_q && load_valid;
    assign descriptor_valid = load_matrix_rows != 0 && load_matrix_columns != 0 &&
        int'((int'(load_matrix_rows) + 1) / 2) <= MAX_PAIRS;

    assign release_cache_0 = release_enable && cache_valid_q[0] &&
        cache_command_q[0] == read_command_id &&
        cache_block_q[0] == read_block_index &&
        cache_recurrence_q[0] == read_recurrence_index &&
        cache_rows_q[0] == read_matrix_rows &&
        cache_columns_q[0] == read_matrix_columns &&
        cache_tile_q[0] == release_tile_index;
    assign release_cache_1 = release_enable && cache_valid_q[1] &&
        cache_command_q[1] == read_command_id &&
        cache_block_q[1] == read_block_index &&
        cache_recurrence_q[1] == read_recurrence_index &&
        cache_rows_q[1] == read_matrix_rows &&
        cache_columns_q[1] == read_matrix_columns &&
        cache_tile_q[1] == release_tile_index;
    assign stale_cache_0 = read_enable && cache_valid_q[0] && !(
        cache_command_q[0] == read_command_id &&
        cache_block_q[0] == read_block_index &&
        cache_recurrence_q[0] == read_recurrence_index &&
        cache_rows_q[0] == read_matrix_rows &&
        cache_columns_q[0] == read_matrix_columns
    );
    assign stale_cache_1 = read_enable && cache_valid_q[1] && !(
        cache_command_q[1] == read_command_id &&
        cache_block_q[1] == read_block_index &&
        cache_recurrence_q[1] == read_recurrence_index &&
        cache_rows_q[1] == read_matrix_rows &&
        cache_columns_q[1] == read_matrix_columns
    );
    assign slot_available_0 = !cache_valid_q[0] || release_cache_0 || stale_cache_0;
    assign slot_available_1 = !cache_valid_q[1] || release_cache_1 || stale_cache_1;
    assign candidate_tile = read_enable && !read_match ? read_tile_index :
                            TILE_INDEX_WIDTH'(int'(read_tile_index) + 1);
    assign candidate_valid = read_enable && (read_bank_0 || read_bank_1) &&
        int'(candidate_tile) < ((int'(read_matrix_rows) + CHANNELS - 1) / CHANNELS);
    assign candidate_cached = (cache_valid_q[0] &&
        cache_command_q[0] == read_command_id &&
        cache_block_q[0] == read_block_index &&
        cache_recurrence_q[0] == read_recurrence_index &&
        cache_rows_q[0] == read_matrix_rows &&
        cache_columns_q[0] == read_matrix_columns &&
        cache_tile_q[0] == candidate_tile) ||
        (cache_valid_q[1] &&
        cache_command_q[1] == read_command_id &&
        cache_block_q[1] == read_block_index &&
        cache_recurrence_q[1] == read_recurrence_index &&
        cache_rows_q[1] == read_matrix_rows &&
        cache_columns_q[1] == read_matrix_columns &&
        cache_tile_q[1] == candidate_tile);
    assign prefetch_start = !prefetch_busy_q && candidate_valid && !candidate_cached &&
        (slot_available_0 || slot_available_1);
    assign prefetch_slot = slot_available_0 ? 1'b0 : 1'b1;
    assign prefetch_address = PAIR_ADDR_WIDTH'(
        int'(prefetch_tile_q) * TILE_PAIR_COUNT + int'(prefetch_pair_q));

    always_ff @(posedge clk) begin
        integer pair_index;
        logic [31:0] pair_data;
        if (!rst_n || load_abort) begin
            bank_0_valid_q <= 1'b0;
            bank_1_valid_q <= 1'b0;
            cache_valid_q[0] <= 1'b0;
            cache_valid_q[1] <= 1'b0;
            load_busy_q <= 1'b0;
            load_bank_q <= 1'b0;
            load_count_q <= '0;
            load_pairs_q <= '0;
            load_command_q <= '0;
            load_block_q <= '0;
            load_recurrence_q <= '0;
            load_rows_q <= '0;
            load_columns_q <= '0;
            prefetch_busy_q <= 1'b0;
            prefetch_bank_q <= 1'b0;
            prefetch_slot_q <= 1'b0;
            prefetch_tile_q <= '0;
            prefetch_pair_q <= '0;
            prefetch_command_q <= '0;
            prefetch_block_q <= '0;
            prefetch_recurrence_q <= '0;
            prefetch_rows_q <= '0;
            prefetch_columns_q <= '0;
            load_done <= 1'b0;
            protocol_error <= 1'b0;
        end else begin
            load_done <= 1'b0;

            if (release_cache_0)
                cache_valid_q[0] <= 1'b0;
            if (release_cache_1)
                cache_valid_q[1] <= 1'b0;

            if (prefetch_start) begin
                prefetch_busy_q <= 1'b1;
                prefetch_bank_q <= !read_bank_0;
                prefetch_slot_q <= prefetch_slot;
                prefetch_tile_q <= candidate_tile;
                prefetch_pair_q <= '0;
                prefetch_command_q <= read_command_id;
                prefetch_block_q <= read_block_index;
                prefetch_recurrence_q <= read_recurrence_index;
                prefetch_rows_q <= read_matrix_rows;
                prefetch_columns_q <= read_matrix_columns;
                if (prefetch_slot)
                    cache_valid_q[1] <= 1'b0;
                else
                    cache_valid_q[0] <= 1'b0;
            end else if (prefetch_busy_q) begin
                if (prefetch_tile_q * CHANNELS + prefetch_pair_q * 2 < prefetch_rows_q) begin
                    if (prefetch_bank_q)
                        pair_data = gamma_bank_1[int'(prefetch_address) / 16]
                            [(int'(prefetch_address) % 16) * 32 +: 32];
                    else
                        pair_data = gamma_bank_0[int'(prefetch_address) / 16]
                            [(int'(prefetch_address) % 16) * 32 +: 32];
                    gamma_tile_data_q[prefetch_slot_q][prefetch_pair_q*32 +: 16] <= pair_data[15:0];
                    gamma_tile_data_q[prefetch_slot_q][prefetch_pair_q*32+16 +: 16] <=
                        prefetch_tile_q * CHANNELS + prefetch_pair_q * 2 + 1 < prefetch_rows_q ?
                        pair_data[31:16] : 16'd0;
                end else begin
                    gamma_tile_data_q[prefetch_slot_q][prefetch_pair_q*32 +: 32] <= '0;
                end

                if (prefetch_pair_q == TILE_PAIR_COUNT - 1) begin
                    prefetch_busy_q <= 1'b0;
                    cache_valid_q[prefetch_slot_q] <= 1'b1;
                    cache_bank_q[prefetch_slot_q] <= prefetch_bank_q;
                    cache_command_q[prefetch_slot_q] <= prefetch_command_q;
                    cache_block_q[prefetch_slot_q] <= prefetch_block_q;
                    cache_recurrence_q[prefetch_slot_q] <= prefetch_recurrence_q;
                    cache_rows_q[prefetch_slot_q] <= prefetch_rows_q;
                    cache_columns_q[prefetch_slot_q] <= prefetch_columns_q;
                    cache_tile_q[prefetch_slot_q] <= prefetch_tile_q;
                end else begin
                    prefetch_pair_q <= prefetch_pair_q + 1'b1;
                end
            end

            if (load_start) begin
                if (!load_start_ready || !descriptor_valid) begin
                    protocol_error <= 1'b1;
                end else begin
                    load_bank_q <= bank_0_valid_q && read_bank_0;
                    load_count_q <= '0;
                    load_pairs_q <= COUNT_WIDTH'((int'(load_matrix_rows) + 1) / 2);
                    load_command_q <= load_command_id;
                    load_block_q <= load_block_index;
                    load_recurrence_q <= load_recurrence_index;
                    load_rows_q <= load_matrix_rows;
                    load_columns_q <= load_matrix_columns;
                    load_busy_q <= 1'b1;
                    protocol_error <= 1'b0;
                    if (bank_0_valid_q && read_bank_0) begin
                        bank_1_valid_q <= 1'b0;
                        if (cache_valid_q[0] && cache_bank_q[0]) cache_valid_q[0] <= 1'b0;
                        if (cache_valid_q[1] && cache_bank_q[1]) cache_valid_q[1] <= 1'b0;
                    end else begin
                        bank_0_valid_q <= 1'b0;
                        if (cache_valid_q[0] && !cache_bank_q[0]) cache_valid_q[0] <= 1'b0;
                        if (cache_valid_q[1] && !cache_bank_q[1]) cache_valid_q[1] <= 1'b0;
                    end
                end
            end

            if (load_fire) begin
                if (PARALLEL_LOAD) begin
                    if (load_bank_q)
                        gamma_bank_1[int'(load_count_q) / 16] <= load_vector_data;
                    else
                        gamma_bank_0[int'(load_count_q) / 16] <= load_vector_data;
                end else begin
                    pair_index = int'(load_count_q);
                    if (pair_index < int'(load_pairs_q)) begin
                        pair_data = load_pair_data;
                        if (load_rows_q[0] && pair_index == int'(load_pairs_q) - 1)
                            pair_data = {16'd0, pair_data[15:0]};
                        if (load_bank_q)
                            gamma_bank_1[pair_index / 16][(pair_index % 16) * 32 +: 32] <= pair_data;
                        else
                            gamma_bank_0[pair_index / 16][(pair_index % 16) * 32 +: 32] <= pair_data;
                    end
                end

                if (load_last != (int'(load_count_q) + WRITE_LANES >= int'(load_pairs_q))) begin
                    protocol_error <= 1'b1;
                    load_busy_q <= 1'b0;
                end else if (int'(load_count_q) + WRITE_LANES >= int'(load_pairs_q)) begin
                    load_busy_q <= 1'b0;
                    if (load_last) begin
                        if (load_bank_q) begin
                            bank_1_command_q <= load_command_q;
                            bank_1_block_q <= load_block_q;
                            bank_1_recurrence_q <= load_recurrence_q;
                            bank_1_rows_q <= load_rows_q;
                            bank_1_columns_q <= load_columns_q;
                            bank_1_valid_q <= 1'b1;
                        end else begin
                            bank_0_command_q <= load_command_q;
                            bank_0_block_q <= load_block_q;
                            bank_0_recurrence_q <= load_recurrence_q;
                            bank_0_rows_q <= load_rows_q;
                            bank_0_columns_q <= load_columns_q;
                            bank_0_valid_q <= 1'b1;
                        end
                        load_done <= 1'b1;
                    end else begin
                        protocol_error <= 1'b1;
                    end
                end else begin
                    load_count_q <= load_count_q + WRITE_LANES;
                end
            end
        end
    end

    initial begin
        if (MAX_ROWS < 1 || CHANNELS < 2 || (CHANNELS % 2) != 0 || TILE_INDEX_WIDTH < 1 ||
            (2 ** PAIR_ADDR_WIDTH) < MAX_PAIRS)
            $error("Gamma memory dimensions are invalid");
    end
endmodule
