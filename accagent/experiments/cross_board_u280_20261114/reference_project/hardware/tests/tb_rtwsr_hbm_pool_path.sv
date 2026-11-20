`timescale 1ns / 1ps

module tb_rtwsr_hbm_pool_path #(
    parameter int CHANNELS = 96,
    parameter bit READ_PARALLEL_SLOTS = 1'b0,
    parameter int POOL_LANES = 24
);
    localparam int ROWS = 17920;
    localparam int COLUMNS = 5280;
    localparam int WINDOWS = 21;
    localparam int GROUP_TILES = (ROWS + 95) / 96;
    localparam int TILES = (ROWS + CHANNELS - 1) / CHANNELS;
    localparam int GROUPS_PER_TILE = 96 / POOL_LANES;
    localparam int GROUPS = GROUP_TILES * WINDOWS * GROUPS_PER_TILE;
    localparam int PCS = 32;
    localparam int LOGICAL_RECORDS = GROUPS * POOL_LANES;

    logic clk = 1'b0;
    logic rst_n = 1'b0;
    logic load_start = 1'b0;
    logic [PCS-1:0] hbm_valid = '0;
    logic [PCS-1:0] hbm_ready;
    logic [PCS*512-1:0] hbm_data = '0;
    logic pool_wr_valid;
    logic pool_wr_ready;
    logic [POOL_LANES-1:0] pool_wr_enable;
    logic [POOL_LANES*14-1:0] pool_wr_address;
    logic [POOL_LANES*512-1:0] pool_wr_data;
    logic [27*15-1:0] ring_occupancy;
    logic adapter_done;
    logic adapter_error;
    logic pool_load_ready;
    logic pool_load_busy;
    logic pool_load_done;
    logic pool_protocol_error;
    logic [6:0] pool_window_count;
    logic [14:0] pool_words_per_port;
    logic pool_read_enable = 1'b0;
    logic [8:0] pool_read_tile_index = '0;
    logic [6:0] pool_read_window_index = '0;
    logic [1:0] pool_read_subword_index = '0;
    logic pool_read_valid;
    logic [CHANNELS*512-1:0] pool_read_data;
    logic pool_read_error;
    integer sent_count [0:PCS-1];
    integer checked_groups = 0;
    integer timeout;
    integer pc;

    always #5 clk = ~clk;

    function automatic logic [511:0] marker(input integer index);
        marker = 512'(index) ^ 512'h243f6a8885a308d313198a2e03707344;
    endfunction

    rtwsr_hbm_weight_pool_adapter_27to24 #(
        .HBM_PCS(PCS), .POOL_LANES(POOL_LANES), .FIFO_DEPTH(64)
    ) adapter (
        .clk(clk), .rst_n(rst_n), .load_start(load_start),
        .load_rows(16'(ROWS)), .load_columns(16'(COLUMNS)), .load_first_pc(5'd0),
        .hbm_valid(hbm_valid), .hbm_ready(hbm_ready), .hbm_data(hbm_data),
        .pool_wr_valid(pool_wr_valid), .pool_wr_ready(pool_wr_ready),
        .pool_wr_enable(pool_wr_enable), .pool_wr_address(pool_wr_address),
        .pool_wr_data(pool_wr_data), .ring_occupancy(ring_occupancy),
        .load_done(adapter_done), .protocol_error(adapter_error)
    );

    rtwsr_runtime_weight_pool #(
        .CHANNELS(CHANNELS), .HBM_PARALLEL_LOAD(1'b1), .OVERLAP_READ(1'b0),
        .HBM_LOAD_LANES(POOL_LANES),
        .READ_PARALLEL_SLOTS(READ_PARALLEL_SLOTS)
    ) pool (
        .clk(clk), .rst_n(rst_n), .load_start(load_start),
        .load_rows(16'(ROWS)), .load_columns(16'(COLUMNS)),
        .load_valid(1'b0), .load_ready(), .load_data('0), .load_last(1'b0),
        .load_busy(pool_load_busy), .load_done(pool_load_done),
        .protocol_error(pool_protocol_error), .load_window_count(pool_window_count),
        .load_words_per_port(pool_words_per_port), .activate_loaded_weights(1'b0),
        .consumed_tile_valid(1'b0), .consumed_tile_index(9'd0),
        .pool_read_enable(pool_read_enable), .pool_read_tile_index(pool_read_tile_index),
        .pool_read_window_index(pool_read_window_index),
        .pool_read_subword_index(pool_read_subword_index),
        .pool_read_valid(pool_read_valid), .pool_read_data(pool_read_data),
        .pool_read_error(pool_read_error), .parallel_load_valid(pool_wr_valid),
        .parallel_load_ready(pool_wr_ready), .parallel_load_enable(pool_wr_enable),
        .parallel_load_address(pool_wr_address), .parallel_load_data(pool_wr_data)
    );

    initial begin
        for (pc = 0; pc < PCS; pc = pc + 1)
            sent_count[pc] = 0;
        repeat (3) @(posedge clk);
        @(negedge clk);
        rst_n = 1'b1;
        load_start = 1'b1;
        @(posedge clk);
        #1 load_start = 1'b0;
        if (!pool_load_busy || pool_window_count != WINDOWS ||
            pool_words_per_port != TILES * WINDOWS * (READ_PARALLEL_SLOTS ? 1 : 4))
            $fatal(1, "parallel pool descriptor mismatch");

        timeout = 0;
        while (!adapter_done && timeout < GROUPS + 1000) begin
            @(negedge clk);
            for (pc = 0; pc < PCS; pc = pc + 1) begin
                hbm_valid[pc] = sent_count[pc] < ((LOGICAL_RECORDS + PCS - 1 - pc) / PCS);
                hbm_data[pc*512 +: 512] = marker(pc + sent_count[pc] * PCS);
            end

            if (pool_wr_valid && pool_wr_ready) begin
                integer tile;
                integer slot;
                integer window;
                integer row;
                logic [13:0] address;
                tile = checked_groups / (WINDOWS * GROUPS_PER_TILE);
                slot = (checked_groups / WINDOWS) % GROUPS_PER_TILE;
                window = checked_groups % WINDOWS;
                address = 14'(((tile * WINDOWS + window) * GROUPS_PER_TILE) + slot);
                for (integer lane = 0; lane < POOL_LANES; lane = lane + 1) begin
                    row = tile * 96 + (POOL_LANES == 32 ? slot * POOL_LANES + lane :
                        (lane / 8) * 32 + (lane % 8) * 4 + slot);
                    if (pool_wr_address[lane*14 +: 14] !== address ||
                        pool_wr_enable[lane] !== (row < ROWS))
                        $fatal(1, "adapter group format mismatch group=%0d lane=%0d",
                               checked_groups, lane);
                    if (row < ROWS && pool_wr_data[lane*512 +: 512] !==
                        marker(checked_groups * POOL_LANES + lane))
                        $fatal(1, "adapter payload mismatch group=%0d lane=%0d",
                               checked_groups, lane);
                end
                checked_groups = checked_groups + 1;
            end

            @(posedge clk);
            for (pc = 0; pc < PCS; pc = pc + 1)
                if (hbm_valid[pc] && hbm_ready[pc])
                    sent_count[pc] = sent_count[pc] + 1;
            #1;
            timeout = timeout + 1;
        end
        @(negedge clk);
        hbm_valid = '0;
        if (!adapter_done || !pool_load_done || adapter_error || pool_protocol_error ||
            checked_groups != GROUPS)
            $fatal(1, "32-PC pool load failed groups=%0d done=%0d/%0d errors=%0d/%0d",
                   checked_groups, adapter_done, pool_load_done, adapter_error,
                   pool_protocol_error);
        for (pc = 0; pc < PCS; pc = pc + 1)
            if (sent_count[pc] != ((LOGICAL_RECORDS + PCS - 1 - pc) / PCS))
                $fatal(1, "PC %0d count mismatch: %0d", pc, sent_count[pc]);

        if (READ_PARALLEL_SLOTS) begin
            for (integer tile = 0; tile < TILES; tile = tile + 1) begin
                for (integer window = 0; window < WINDOWS; window = window + 1) begin
                    @(negedge clk);
                    pool_read_enable = 1'b1;
                    pool_read_tile_index = 9'(tile);
                    pool_read_window_index = 7'(window);
                    pool_read_subword_index = '0;
                    @(posedge clk);
                    @(negedge clk);
                    pool_read_enable = 1'b0;
                    timeout = 0;
                    while (!pool_read_valid && timeout < 4) begin
                        @(posedge clk);
                        #1;
                        timeout = timeout + 1;
                    end
                    if (!pool_read_valid || pool_read_error)
                        $fatal(1, "parallel pool read failed tile=%0d window=%0d", tile, window);
                    for (integer lane = 0; lane < CHANNELS; lane = lane + 1) begin
                        integer row;
                        integer group_tile;
                        integer local_row;
                        integer source_lane;
                        integer slot;
                        integer group_index;
                        row = tile * CHANNELS + lane;
                        group_tile = (CHANNELS == 192) ? tile * 2 + lane / 96 : tile;
                        local_row = lane % 96;
                        if (POOL_LANES == 32) begin
                            slot = local_row / POOL_LANES;
                            source_lane = local_row % POOL_LANES;
                            group_index = (group_tile * GROUPS_PER_TILE + slot) * WINDOWS + window;
                        end else begin
                            source_lane = (local_row / 32) * 8 + ((local_row % 32) / 4);
                            slot = local_row % 4;
                            group_index = (group_tile * 4 + slot) * WINDOWS + window;
                        end
                        if (row < ROWS && pool_read_data[lane*512 +: 512] !==
                            marker(group_index * POOL_LANES + source_lane))
                            $fatal(1, "parallel pool readback mismatch tile=%0d window=%0d lane=%0d got=%h expected=%h",
                                   tile, window, lane, pool_read_data[lane*512 +: 512],
                                   marker(group_index * POOL_LANES + source_lane));
                    end
                end
            end
        end else begin
            for (integer group_index = 0; group_index < GROUPS; group_index = group_index + 1) begin
                integer tile;
                integer slot;
                integer window;
                tile = group_index / (WINDOWS * GROUPS_PER_TILE);
                slot = (group_index / WINDOWS) % GROUPS_PER_TILE;
                window = group_index % WINDOWS;
                @(negedge clk);
                pool_read_enable = 1'b1;
                pool_read_tile_index = 9'(tile);
                pool_read_window_index = 7'(window);
                pool_read_subword_index = 2'(slot);
                @(posedge clk);
                @(negedge clk);
                pool_read_enable = 1'b0;
                timeout = 0;
                while (!pool_read_valid && timeout < 4) begin
                    @(posedge clk);
                    #1;
                    timeout = timeout + 1;
                end
                if (!pool_read_valid || pool_read_error)
                    $fatal(1, "pool read failed for group %0d", group_index);
                for (integer lane = 0; lane < POOL_LANES; lane = lane + 1) begin
                    integer row;
                    row = tile * 96 + (POOL_LANES == 32 ? slot * POOL_LANES + lane :
                        (lane / 8) * 32 + (lane % 8) * 4 + slot);
                    if (row < ROWS && pool_read_data[lane*512 +: 512] !==
                        marker(group_index * POOL_LANES + lane))
                        $fatal(1, "pool readback mismatch group=%0d lane=%0d", group_index, lane);
                end
            end
        end
        $display("PASS: full Huginn down-proj 32-PC stream loaded and read back %0d groups for %0d channels at %0d pool lanes",
                 GROUPS, CHANNELS, POOL_LANES);
        $finish;
    end
endmodule
