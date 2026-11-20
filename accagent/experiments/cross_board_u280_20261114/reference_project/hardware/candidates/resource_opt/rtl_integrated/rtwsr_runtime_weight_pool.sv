`timescale 1ns / 1ps

module rtwsr_runtime_weight_pool #(
    parameter int CHANNELS = 96,
    parameter int POOL_DEPTH = 16384,
    parameter int ADDR_WIDTH = $clog2(POOL_DEPTH),
    parameter int BANK_COUNT = CHANNELS / 4,
    parameter int BANK_INDEX_WIDTH = $clog2(BANK_COUNT),
    parameter int TILE_INDEX_WIDTH = 9,
    parameter int HBM_LOAD_LANES = 24,
    parameter bit OVERLAP_READ = 1'b0,
    parameter bit HBM_PARALLEL_LOAD = 1'b0,
    parameter bit READ_PARALLEL_SLOTS = 1'b0
)(
    input  logic                                      clk,
    input  logic                                      rst_n,
    input  logic                                      load_start,
    input  logic [15:0]                               load_rows,
    input  logic [15:0]                               load_columns,
    input  logic                                      load_valid,
    output logic                                      load_ready,
    input  logic [511:0]                              load_data,
    input  logic                                      load_last,
    output logic                                      load_busy,
    output logic                                      load_done,
    output logic                                      protocol_error,
    output logic [6:0]                                load_window_count,
    output logic [14:0]                               load_words_per_port,
    input  logic                                      activate_loaded_weights,
    input  logic                                      consumed_tile_valid,
    input  logic [TILE_INDEX_WIDTH-1:0]               consumed_tile_index,
    input  logic                                      pool_read_enable,
    input  logic [TILE_INDEX_WIDTH-1:0]               pool_read_tile_index,
    input  logic [6:0]                                pool_read_window_index,
    input  logic [1:0]                                pool_read_subword_index,
    output logic                                      pool_read_valid,
    output logic [(READ_PARALLEL_SLOTS ? CHANNELS : BANK_COUNT)*512-1:0] pool_read_data,
    output logic                                      pool_read_error,
    input  logic                                      parallel_load_valid,
    output logic                                      parallel_load_ready,
    input  logic [HBM_LOAD_LANES-1:0]                 parallel_load_enable,
    input  logic [HBM_LOAD_LANES*ADDR_WIDTH-1:0]       parallel_load_address,
    input  logic [HBM_LOAD_LANES*512-1:0]              parallel_load_data
);
    logic [15:0] rows_q;
    logic [6:0] windows_q;
    logic [8:0] tiles_q;
    logic [31:0] total_records_q;
    logic [31:0] record_index_q;
    logic [8:0] tile_index_q;
    logic [$clog2(CHANNELS)-1:0] row_in_tile_q;
    logic [6:0] window_index_q;
    localparam int READ_BANK_COUNT = READ_PARALLEL_SLOTS ? CHANNELS : BANK_COUNT;
    localparam int READ_DEPTH = READ_PARALLEL_SLOTS ?
        POOL_DEPTH / (CHANNELS == 192 ? 8 : 4) : POOL_DEPTH;
    localparam int READ_ADDR_WIDTH = $clog2(READ_DEPTH);
    localparam int READ_BANKS_PER_SLR = READ_BANK_COUNT / 3;
    localparam int READ_ADDRESS_FACTOR = READ_PARALLEL_SLOTS ? 1 : 4;
    logic [READ_BANK_COUNT-1:0] bank_wr_enable;
    logic [READ_ADDR_WIDTH-1:0] bank_wr_address;
    logic [READ_BANK_COUNT*READ_ADDR_WIDTH-1:0] bank_wr_address_bus;
    logic [READ_BANK_COUNT*512-1:0] bank_wr_data_bus;
    logic [READ_ADDR_WIDTH-1:0] read_address_global_q;
    logic read_request_valid_global_q;
    (* keep = "true" *) logic [READ_ADDR_WIDTH-1:0] slr_read_address_q [0:2];
    (* keep = "true" *) logic [2:0] slr_read_valid_q;
    logic [READ_BANK_COUNT-1:0] bank_rd_valid;
    logic [READ_BANK_COUNT*512-1:0] bank_rd_data;
    logic [31:0] requested_tiles;
    logic [31:0] requested_windows;
    logic [31:0] requested_words_per_port;
    logic [31:0] requested_records;
    logic [31:0] requested_groups;
    localparam int HBM_GROUPS_PER_TILE = 96 / HBM_LOAD_LANES;
    logic [31:0] total_groups_q;
    logic [31:0] group_count_q;
    logic [6:0] local_channel;
    logic [1:0] slr_index;
    logic [$clog2(READ_BANK_COUNT)-1:0] bank_index;
    logic [1:0] row_slot;
    logic [31:0] write_address_wide;
    logic [31:0] read_address_wide;
    logic write_address_valid;
    logic read_address_valid;
    logic expected_last;
    logic last_error_q;
    logic read_error_q;
    logic [6:0] read_windows_q;
    logic [8:0] read_tiles_q;
    logic [8:0] released_tiles_q;
    logic read_descriptor_valid_q;
    logic loaded_matrix_valid_q;
    logic overlap_error_q;
    logic [31:0] writable_words;
    logic [31:0] expected_group_tile;
    logic [31:0] expected_group_slot;
    logic [31:0] expected_group_window;
    logic [31:0] expected_group_address;
    logic [31:0] expected_group_storage_address;
    logic [HBM_LOAD_LANES-1:0] expected_group_mask;
    logic parallel_group_valid;
    logic parallel_load_fire;
    logic [6:0] read_windows;
    logic [8:0] read_tiles;

    assign read_windows = OVERLAP_READ ? read_windows_q : windows_q;
    assign read_tiles = OVERLAP_READ ? read_tiles_q : tiles_q;
    // Only a contiguous consumed prefix may be reused by the next operator.
    assign writable_words = !OVERLAP_READ || !read_descriptor_valid_q ||
        released_tiles_q == read_tiles_q ? READ_DEPTH :
        int'(released_tiles_q) * int'(read_windows_q) * READ_ADDRESS_FACTOR;

    always_comb begin
        requested_tiles = (int'(load_rows) + CHANNELS - 1) / CHANNELS;
        requested_windows = (int'(load_columns) + 255) / 256;
        requested_words_per_port = requested_tiles * requested_windows * READ_ADDRESS_FACTOR;
        requested_records = int'(load_rows) * requested_windows;
        requested_groups = (HBM_PARALLEL_LOAD ?
            (int'(load_rows) + 95) / 96 : requested_tiles) * requested_windows *
            (HBM_PARALLEL_LOAD ? HBM_GROUPS_PER_TILE : 4);

        local_channel = row_in_tile_q % 32;
        if (row_in_tile_q < CHANNELS / 3)
            slr_index = 2'd0;
        else if (row_in_tile_q < (2 * CHANNELS) / 3)
            slr_index = 2'd1;
        else
            slr_index = 2'd2;
        bank_index = READ_PARALLEL_SLOTS ?
            $clog2(READ_BANK_COUNT)'(row_in_tile_q) :
            $clog2(READ_BANK_COUNT)'(int'(slr_index) * (BANK_COUNT / 3) +
                (int'(local_channel) % (CHANNELS / 3)) / 4);
        row_slot = 2'(int'(local_channel) % 4);
        write_address_wide =
            ((int'(tile_index_q) * int'(windows_q) + int'(window_index_q)) * READ_ADDRESS_FACTOR) +
            (READ_PARALLEL_SLOTS ? 0 : int'(row_slot));
        write_address_valid = write_address_wide < READ_DEPTH;
        bank_wr_address = READ_ADDR_WIDTH'(write_address_wide);
        bank_wr_enable = '0;
        if (load_valid && load_ready && write_address_valid)
            bank_wr_enable[bank_index] = 1'b1;

        expected_group_tile = '0;
        expected_group_slot = '0;
        expected_group_window = '0;
        if (windows_q != 0) begin
            expected_group_tile = group_count_q /
                (HBM_GROUPS_PER_TILE * int'(windows_q));
            expected_group_slot = (group_count_q / int'(windows_q)) %
                (HBM_PARALLEL_LOAD ? HBM_GROUPS_PER_TILE : 4);
            expected_group_window = group_count_q % int'(windows_q);
        end
        expected_group_address =
            ((expected_group_tile * int'(windows_q) + expected_group_window) *
             (HBM_PARALLEL_LOAD ? HBM_GROUPS_PER_TILE : 4)) +
            expected_group_slot;
        expected_group_storage_address =
            ((CHANNELS == 192 ? expected_group_tile / 2 : expected_group_tile) *
             int'(windows_q) + expected_group_window) * READ_ADDRESS_FACTOR;
        expected_group_mask = '0;
        for (integer lane = 0; lane < HBM_LOAD_LANES; lane = lane + 1) begin
            if ((expected_group_tile * 96 +
                 (HBM_LOAD_LANES == 32 ? expected_group_slot * HBM_LOAD_LANES + lane :
                  (lane / 8) * 32 + (lane % 8) * 4 + expected_group_slot)) < int'(rows_q))
                expected_group_mask[lane] = 1'b1;
        end
        parallel_group_valid = HBM_PARALLEL_LOAD &&
            group_count_q < total_groups_q &&
            parallel_load_enable == expected_group_mask;
        for (integer lane = 0; lane < HBM_LOAD_LANES; lane = lane + 1)
            if (parallel_load_address[lane*ADDR_WIDTH +: ADDR_WIDTH] !=
                ADDR_WIDTH'(expected_group_address))
                parallel_group_valid = 1'b0;

        for (integer lane = 0; lane < READ_BANK_COUNT; lane = lane + 1) begin
            if (HBM_PARALLEL_LOAD) begin
                if (READ_PARALLEL_SLOTS) begin
                    integer source_lane;
                    integer source_slot;
                    integer local_row;
                    integer group_half;
                    local_row = (CHANNELS == 192) ? lane % 96 : lane;
                    group_half = (CHANNELS == 192) ? expected_group_tile % 2 : 0;
                    if (HBM_LOAD_LANES == 32) begin
                        source_lane = local_row - int'(expected_group_slot) * HBM_LOAD_LANES;
                        source_slot = source_lane >= 0 && source_lane < HBM_LOAD_LANES;
                        bank_wr_enable[lane] = parallel_load_fire &&
                            (CHANNELS != 192 || lane / 96 == group_half) &&
                            source_slot && parallel_load_enable[source_lane];
                    end else begin
                        source_lane = (local_row / 32) * 8 + ((local_row % 32) / 4);
                        source_slot = local_row % 4;
                        bank_wr_enable[lane] = parallel_load_fire &&
                            (CHANNELS != 192 || lane / 96 == group_half) &&
                            expected_group_slot == source_slot && parallel_load_enable[source_lane];
                    end
                    bank_wr_address_bus[lane*READ_ADDR_WIDTH +: READ_ADDR_WIDTH] =
                        READ_ADDR_WIDTH'(expected_group_storage_address);
                    bank_wr_data_bus[lane*512 +: 512] =
                        parallel_load_data[source_lane*512 +: 512];
                end else begin
                    bank_wr_enable[lane] = parallel_load_fire && parallel_load_enable[lane];
                    bank_wr_address_bus[lane*READ_ADDR_WIDTH +: READ_ADDR_WIDTH] =
                        READ_ADDR_WIDTH'(parallel_load_address[lane*ADDR_WIDTH +: ADDR_WIDTH]);
                    bank_wr_data_bus[lane*512 +: 512] = parallel_load_data[lane*512 +: 512];
                end
            end else begin
                bank_wr_address_bus[lane*READ_ADDR_WIDTH +: READ_ADDR_WIDTH] = bank_wr_address;
                bank_wr_data_bus[lane*512 +: 512] = load_data;
            end
        end

        read_address_wide =
            ((int'(pool_read_tile_index) * int'(read_windows) + int'(pool_read_window_index)) *
             READ_ADDRESS_FACTOR) +
            (READ_PARALLEL_SLOTS ? 0 : int'(pool_read_subword_index));
        read_address_valid = pool_read_enable &&
            int'(pool_read_tile_index) < int'(read_tiles) &&
            int'(pool_read_window_index) < int'(read_windows) &&
            (!OVERLAP_READ || (read_descriptor_valid_q &&
                pool_read_tile_index >= released_tiles_q)) &&
            read_address_wide < READ_DEPTH;
        expected_last = record_index_q == total_records_q - 1'b1;
    end

    assign load_ready = !HBM_PARALLEL_LOAD && load_busy &&
                        write_address_wide < writable_words;
    assign parallel_load_ready = HBM_PARALLEL_LOAD && load_busy &&
                                 parallel_group_valid &&
                                 READ_ADDR_WIDTH'(expected_group_storage_address) < writable_words;
    assign parallel_load_fire = parallel_load_valid && parallel_load_ready;
    assign load_window_count = windows_q;
    assign load_words_per_port = 15'(int'(tiles_q) * int'(windows_q) * READ_ADDRESS_FACTOR);
    assign pool_read_valid = bank_rd_valid[0];
    assign pool_read_data = bank_rd_data;
    assign pool_read_error = read_error_q;
    assign protocol_error = last_error_q || read_error_q || overlap_error_q;

    genvar bank;
    generate
        for (bank = 0; bank < READ_BANK_COUNT; bank = bank + 1) begin : gen_pool_bank
            uram_active_pool_bank #(
                .DEPTH(READ_DEPTH),
                .ADDR_WIDTH(READ_ADDR_WIDTH),
                .WR_ADDR_MODE(0),
                .CHANNELS_PER_TILE(4),
                .WINDOW_COUNT(1),
                .CHANNEL_WIDTH(1),
                .WINDOW_WIDTH(1)
            ) u_pool_bank (
                .clk(clk),
                .wr_en(bank_wr_enable[bank]),
                .wr_addr(bank_wr_address_bus[bank*READ_ADDR_WIDTH +: READ_ADDR_WIDTH]),
                .wr_channel('0),
                .wr_window('0),
                .wr_data(bank_wr_data_bus[bank*512 +: 512]),
                .rd_en(slr_read_valid_q[bank / READ_BANKS_PER_SLR]),
                .rd_addr(slr_read_address_q[bank / READ_BANKS_PER_SLR]),
                .rd_valid(bank_rd_valid[bank]),
                .rd_data(bank_rd_data[bank*512 +: 512])
            );
        end
    endgenerate

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            rows_q <= '0;
            windows_q <= '0;
            tiles_q <= '0;
            total_records_q <= '0;
            record_index_q <= '0;
            tile_index_q <= '0;
            row_in_tile_q <= '0;
            window_index_q <= '0;
            load_busy <= 1'b0;
            load_done <= 1'b0;
            last_error_q <= 1'b0;
            read_error_q <= 1'b0;
            read_windows_q <= '0;
            read_tiles_q <= '0;
            released_tiles_q <= '0;
            read_descriptor_valid_q <= 1'b0;
            loaded_matrix_valid_q <= 1'b0;
            overlap_error_q <= 1'b0;
            group_count_q <= '0;
            total_groups_q <= '0;
            read_address_global_q <= '0;
            read_request_valid_global_q <= 1'b0;
            slr_read_valid_q <= '0;
            for (integer slr = 0; slr < 3; slr++)
                slr_read_address_q[slr] <= '0;
        end else begin
            load_done <= 1'b0;
            read_address_global_q <= READ_ADDR_WIDTH'(read_address_wide);
            read_request_valid_global_q <= read_address_valid;
            for (integer slr = 0; slr < 3; slr++) begin
                slr_read_address_q[slr] <= read_address_global_q;
                slr_read_valid_q[slr] <= read_request_valid_global_q;
            end
            if (load_start && !load_busy) begin
                loaded_matrix_valid_q <= 1'b0;
                if (load_rows == 0 || load_columns == 0 || requested_windows == 0 ||
                    requested_windows >= 128 || requested_tiles >= 512 ||
                    requested_words_per_port > READ_DEPTH || requested_records == 0) begin
                    last_error_q <= 1'b1;
                    load_done <= 1'b1;
                end else begin
                    rows_q <= load_rows;
                    windows_q <= 7'(requested_windows);
                    tiles_q <= 9'(requested_tiles);
                    total_records_q <= requested_records;
                    total_groups_q <= requested_groups;
                    group_count_q <= '0;
                    record_index_q <= '0;
                    tile_index_q <= '0;
                    row_in_tile_q <= '0;
                    window_index_q <= '0;
                    load_busy <= 1'b1;
                    last_error_q <= 1'b0;
                    read_error_q <= 1'b0;
                end
            end

            if (load_valid && load_ready) begin
                if (!write_address_valid || (load_last != expected_last)) begin
                    load_busy <= 1'b0;
                    last_error_q <= 1'b1;
                    load_done <= 1'b1;
                end else if (expected_last) begin
                    load_busy <= 1'b0;
                    load_done <= 1'b1;
                    loaded_matrix_valid_q <= 1'b1;
                end else begin
                    record_index_q <= record_index_q + 1'b1;
                    if (window_index_q == windows_q - 1'b1) begin
                        window_index_q <= '0;
                        if (row_in_tile_q == CHANNELS - 1) begin
                            row_in_tile_q <= '0;
                            tile_index_q <= tile_index_q + 1'b1;
                        end else begin
                            row_in_tile_q <= row_in_tile_q + 1'b1;
                        end
                    end else begin
                        window_index_q <= window_index_q + 1'b1;
                    end
                end
            end

            if (HBM_PARALLEL_LOAD && parallel_load_valid && load_busy &&
                !parallel_group_valid) begin
                load_busy <= 1'b0;
                load_done <= 1'b1;
                last_error_q <= 1'b1;
            end else if (parallel_load_fire) begin
                if (group_count_q + 1'b1 == total_groups_q) begin
                    load_busy <= 1'b0;
                    load_done <= 1'b1;
                    loaded_matrix_valid_q <= 1'b1;
                end else begin
                    group_count_q <= group_count_q + 1'b1;
                end
            end

            if (pool_read_enable && !read_address_valid)
                read_error_q <= 1'b1;

            if (OVERLAP_READ && consumed_tile_valid) begin
                if (!read_descriptor_valid_q || consumed_tile_index != released_tiles_q ||
                    released_tiles_q >= read_tiles_q)
                    overlap_error_q <= 1'b1;
                else
                    released_tiles_q <= released_tiles_q + 1'b1;
            end
            if (OVERLAP_READ && activate_loaded_weights) begin
                if (load_busy || !loaded_matrix_valid_q ||
                    (read_descriptor_valid_q && released_tiles_q != read_tiles_q))
                    overlap_error_q <= 1'b1;
                else begin
                    read_windows_q <= windows_q;
                    read_tiles_q <= tiles_q;
                    released_tiles_q <= '0;
                    read_descriptor_valid_q <= 1'b1;
                    loaded_matrix_valid_q <= 1'b0;
                end
            end
        end
    end

    initial begin
        if ((CHANNELS != 96 && !(CHANNELS == 192 && READ_PARALLEL_SLOTS)) ||
            (CHANNELS % 12) != 0 || BANK_COUNT != CHANNELS / 4 ||
            (HBM_PARALLEL_LOAD && HBM_LOAD_LANES != 24 && HBM_LOAD_LANES != 32) ||
            (HBM_PARALLEL_LOAD && HBM_LOAD_LANES == 32 && !READ_PARALLEL_SLOTS) ||
            (96 % HBM_LOAD_LANES) != 0 ||
            POOL_DEPTH < 2 || (2 ** ADDR_WIDTH) != POOL_DEPTH)
            $error("Plan 6 runtime pool supports 96 channels or 192 parallel-read channels");
    end
endmodule
