`timescale 1ns / 1ps

module tb_rtwsr_adapter_hbm_path;
    localparam int PCS = 32;
    logic core_clk = 0, axi_clk = 0, rst_n = 0, start = 0;
    logic busy, done, error;
    logic [PCS*33-1:0] araddr;
    logic [PCS*6-1:0] arid, rid;
    logic [PCS*4-1:0] arlen;
    logic [PCS*3-1:0] arsize;
    logic [PCS*2-1:0] arburst, rresp;
    logic [PCS-1:0] arvalid, arready, rlast, rvalid, rready, model_error;
    logic [PCS*256-1:0] rdata;
    logic pool_valid, pool_ready;
    logic pool_input_ready, pool_busy, pool_done, pool_error, pool_read_valid, pool_read_error;
    logic pool_read_enable = 0;
    logic [8:0] pool_read_tile = 0;
    logic [6:0] pool_read_window = 0;
    logic [1:0] pool_read_slot = 0;
    logic [24*512-1:0] pool_read_data;
    logic [6:0] pool_windows;
    logic [14:0] pool_words;
    logic pool_done_seen = 0;
    logic [23:0] pool_enable;
    logic [24*14-1:0] pool_address;
    logic [24*512-1:0] pool_data;
    logic [$clog2(PCS*2304+1)-1:0] ring_occupancy;
    integer groups = 0, beats = 0, cycles = 0, reads = 0;
    integer block_index = 0, recurrence_index = 0;
    integer group_start, beat_start, read_start, expected_windows;

    always #5 core_clk = ~core_clk;
    always #2.5 axi_clk = ~axi_clk;
    assign pool_ready = pool_input_ready && cycles % 9 != 0;

    rtwsr_plan6_huginn_u280_hbm_weight_path #(
        .HBM_PCS(PCS), .ADAPTER_STATIC_REUSE(1'b1)
    ) dut (
        .core_clk(core_clk), .core_rst_n(rst_n), .axi_clk(axi_clk), .axi_rst_n(rst_n),
        .load_start(start), .load_command_id(5'd0), .load_block_index(6'(block_index)),
        .load_rows(16'd5280), .load_columns(16'd10560),
        .load_skip_adapter_static(recurrence_index != 0 || block_index != 0),
        .load_busy(busy), .load_done(done), .protocol_error(error),
        .m_axi_araddr(araddr), .m_axi_arid(arid), .m_axi_arlen(arlen), .m_axi_arsize(arsize),
        .m_axi_arburst(arburst), .m_axi_arvalid(arvalid), .m_axi_arready(arready),
        .m_axi_rid(rid), .m_axi_rdata(rdata), .m_axi_rresp(rresp), .m_axi_rlast(rlast),
        .m_axi_rvalid(rvalid), .m_axi_rready(rready), .pool_wr_valid(pool_valid),
        .pool_wr_ready(pool_ready), .pool_wr_enable(pool_enable), .pool_wr_address(pool_address),
        .pool_wr_data(pool_data), .ring_occupancy(ring_occupancy)
    );
    rtwsr_u280_hbm_axi_cycle_model #(.HBM_PCS(PCS)) memory (
        .hbm_clk(axi_clk), .hbm_rst_n(rst_n), .araddr(araddr), .arid(arid), .arlen(arlen),
        .arsize(arsize), .arburst(arburst), .arvalid(arvalid), .arready(arready), .rid(rid),
        .rdata(rdata), .rresp(rresp), .rlast(rlast), .rvalid(rvalid), .rready(rready),
        .protocol_error(model_error)
    );
    rtwsr_runtime_weight_pool #(.HBM_PARALLEL_LOAD(1'b1)) pool (
        .clk(core_clk), .rst_n(rst_n), .load_start(start),
        .load_rows(16'd5280),
        .load_columns(recurrence_index == 0 && block_index == 0 ? 16'd10560 : 16'd5280),
        .load_valid(1'b0), .load_ready(), .load_data('0), .load_last(1'b0),
        .load_busy(pool_busy), .load_done(pool_done), .protocol_error(pool_error),
        .load_window_count(pool_windows), .load_words_per_port(pool_words),
        .activate_loaded_weights(1'b0), .consumed_tile_valid(1'b0), .consumed_tile_index('0),
        .pool_read_enable(pool_read_enable), .pool_read_tile_index(pool_read_tile),
        .pool_read_window_index(pool_read_window), .pool_read_subword_index(pool_read_slot),
        .pool_read_valid(pool_read_valid), .pool_read_data(pool_read_data),
        .pool_read_error(pool_read_error),
        .parallel_load_valid(pool_valid && cycles % 9 != 0),
        .parallel_load_ready(pool_input_ready), .parallel_load_enable(pool_enable),
        .parallel_load_address(pool_address), .parallel_load_data(pool_data)
    );
    always @(posedge axi_clk) begin
        if (rst_n)
            beats += $countones(rvalid & rready);
    end
    always @(posedge core_clk) begin
        integer local_group, tile, slot, window, expected_address;
        if (rst_n) begin
            cycles++;
            if (pool_done) pool_done_seen = 1;
            if (pool_read_valid) begin
                if (pool_read_data != '0) $fatal(1, "pool read data %0d", reads);
                reads++;
            end
            if (pool_valid && pool_ready) begin
                local_group = groups - group_start;
                tile = local_group / (expected_windows * 4);
                slot = (local_group / expected_windows) % 4;
                window = local_group % expected_windows;
                expected_address = (tile*expected_windows + window)*4 + slot;
                if (pool_enable != 24'hffffff)
                    $fatal(1, "integrated HBM path lane mask group=%0d", groups);
                for (integer lane = 0; lane < 24; lane++)
                    if (pool_address[lane*14 +: 14] != 14'(expected_address) ||
                        pool_data[lane*512 +: 512] != 0)
                        $fatal(1, "integrated HBM path data/address group=%0d lane=%0d", groups, lane);
                groups++;
            end
            if (error || pool_error || pool_read_error || (|model_error))
                $fatal(1, "integrated HBM path protocol error");
        end
    end
    initial begin
        repeat (4) @(negedge core_clk);
        rst_n = 1;
        for (recurrence_index = 0; recurrence_index < 32; recurrence_index++) begin
            for (block_index = 0; block_index < 4; block_index++) begin
                expected_windows = recurrence_index == 0 && block_index == 0 ? 42 : 21;
                group_start = groups;
                beat_start = beats;
                read_start = reads;
                pool_done_seen = 0;
                start = 1;
                @(negedge core_clk);
                start = 0;
                wait (done);
                @(negedge core_clk);
                if (groups - group_start != 55*expected_windows*4 || !pool_done_seen ||
                    pool_windows != expected_windows || pool_words != 55*expected_windows*4)
                    $fatal(1, "pool block=%0d recurrence=%0d groups=%0d pool_done=%0d",
                           block_index, recurrence_index, groups-group_start, pool_done_seen);
                for (integer tile = 0; tile < 55; tile++)
                    for (integer window = 0; window < expected_windows; window++)
                        for (integer slot = 0; slot < 4; slot++) begin
                            pool_read_enable = 1;
                            pool_read_tile = 9'(tile);
                            pool_read_window = 7'(window);
                            pool_read_slot = 2'(slot);
                            @(negedge core_clk);
                        end
                pool_read_enable = 0;
                repeat (8) @(negedge core_clk);
                if (reads - read_start != 55*expected_windows*4)
                    $fatal(1, "pool reads block=%0d recurrence=%0d got=%0d",
                           block_index, recurrence_index, reads-read_start);
                $display("PASS Adapter HBM primary pool block=%0d recurrence=%0d windows=%0d groups=%0d beats=%0d reads=%0d",
                         block_index, recurrence_index, expected_windows,
                         groups-group_start, beats-beat_start, reads-read_start);
            end
        end
        $display("PASS Adapter HBM primary pool blocks=4 recurrences=32 groups=%0d beats=%0d reads=%0d core_cycles=%0d",
                 groups, beats, reads, cycles);
        $finish;
    end
    initial begin
        #50000000;
        $fatal(1, "integrated HBM path timeout groups=%0d beats=%0d", groups, beats);
    end
endmodule
