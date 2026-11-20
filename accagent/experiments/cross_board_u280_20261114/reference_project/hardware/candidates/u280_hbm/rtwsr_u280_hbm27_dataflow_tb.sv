`timescale 1ps / 1ps

module rtwsr_u280_hbm27_dataflow_tb;
    localparam int HBM_PCS = 27;
    localparam int HBM_HZ = 450_000_000;
    localparam int CORE_HZ = 225_000_000;
    localparam int EXPECTED_ROWS = 15840;
    localparam int EXPECTED_COLUMNS = 5280;
    localparam int EXPECTED_WINDOWS = (EXPECTED_COLUMNS + 255) / 256;
    localparam int EXPECTED_FIRST_PC = 0;
    localparam int EXPECTED_GROUPS = 13860;
    localparam int EXPECTED_RECORDS_PER_PC = 12320;
    localparam int EXPECTED_BEATS_PER_PC = EXPECTED_RECORDS_PER_PC * 2;

    logic hbm_ref_clk_0 = 1'b0;
    logic hbm_ref_clk_1 = 1'b0;
    logic apb_clk = 1'b0;
    logic apb_reset_n = 1'b0;
    logic axi_clk = 1'b0;
    logic core_clk = 1'b0;
    logic axi_reset_n = 1'b0;
    logic core_reset_n = 1'b0;

    logic [15:0] descriptor_rows, descriptor_columns;
    logic [4:0] descriptor_first_pc;
    logic descriptor_valid;
    logic [HBM_PCS*33-1:0] load_base_address;
    logic [HBM_PCS*32-1:0] load_record_count;
    logic load_start = 1'b0;
    logic dma_busy, dma_done, dma_error;
    logic [HBM_PCS*33-1:0] araddr;
    logic [HBM_PCS*6-1:0] arid;
    logic [HBM_PCS*4-1:0] arlen;
    logic [HBM_PCS*3-1:0] arsize;
    logic [HBM_PCS*2-1:0] arburst;
    logic [HBM_PCS-1:0] arvalid, arready;
    logic [HBM_PCS*6-1:0] rid;
    logic [HBM_PCS*256-1:0] rdata;
    logic [HBM_PCS*2-1:0] rresp;
    logic [HBM_PCS-1:0] rlast, rvalid, rready;
    logic [HBM_PCS-1:0] raw_valid, raw_ready;
    logic [HBM_PCS*256-1:0] raw_data;
    logic [HBM_PCS-1:0] core_valid, core_ready;
    logic [HBM_PCS*512-1:0] core_data;
    logic [HBM_PCS*6-1:0] gearbox_occupancy;
    logic adapter_load_done, adapter_error, pool_write_valid;
    logic pool_write_ready = 1'b1;
    logic [23:0] pool_write_enable;
    logic [24*14-1:0] pool_write_address;
    logic [24*512-1:0] pool_write_data;
    localparam int RING_OCCUPANCY_WIDTH = $clog2(HBM_PCS * 2730 + 1);
    logic [RING_OCCUPANCY_WIDTH-1:0] ring_occupancy;

    logic [31:0] apb0_wdata, apb0_addr, apb0_rdata;
    logic apb0_enable, apb0_select, apb0_write, apb0_ready, apb0_error;
    logic [31:0] apb1_wdata, apb1_addr, apb1_rdata;
    logic apb1_enable, apb1_select, apb1_write, apb1_ready, apb1_error;
    logic apb0_done, apb1_done;

    integer core_cycles;
    integer hbm_cycles;
    integer accepted_hbm_beats;
    integer output_groups;
    integer unsigned pool_output_bytes;
    integer pc_beats [0:HBM_PCS-1];
    integer peak_ring_occupancy;
    integer peak_gearbox_occupancy;
    integer observed_gearbox_occupancy;
    logic load_request_toggle = 1'b0;
    logic load_request_sync_1 = 1'b0;
    logic load_request_sync_2 = 1'b0;
    logic load_request_sync_2_q = 1'b0;
    logic measure_core = 1'b0;
    logic measure_hbm = 1'b0;
    logic load_start_axi;

    function automatic integer expected_pool_address(input integer group_index);
        integer tile_index;
        integer groups_per_tile;
        integer group_in_tile;
        integer slot_index;
        integer window_index;
        begin
            groups_per_tile = EXPECTED_WINDOWS * 4;
            tile_index = group_index / groups_per_tile;
            group_in_tile = group_index % groups_per_tile;
            slot_index = group_in_tile / EXPECTED_WINDOWS;
            window_index = group_in_tile % EXPECTED_WINDOWS;
            expected_pool_address =
                ((tile_index * EXPECTED_WINDOWS + window_index) * 4) + slot_index;
        end
    endfunction

    rtwsr_huginn_u280_hbm_descriptor #(.HBM_PCS(HBM_PCS)) u_descriptor (
        .command_id(5'd3), .block_index(6'd0), .valid(descriptor_valid),
        .matrix_rows(descriptor_rows), .matrix_columns(descriptor_columns),
        .first_pc(descriptor_first_pc), .pc_base_address(load_base_address),
        .pc_record_count(load_record_count)
    );

    always #5000 hbm_ref_clk_0 = ~hbm_ref_clk_0;
    always #5000 hbm_ref_clk_1 = ~hbm_ref_clk_1;
    always #5000 apb_clk = ~apb_clk;
    always #1111 axi_clk = ~axi_clk;
    always #2222 core_clk = ~core_clk;

    assign load_start_axi = load_request_sync_2 ^ load_request_sync_2_q;

    always_ff @(posedge axi_clk) begin
        if (!axi_reset_n) begin
            load_request_sync_1 <= 1'b0;
            load_request_sync_2 <= 1'b0;
            load_request_sync_2_q <= 1'b0;
        end else begin
            load_request_sync_1 <= load_request_toggle;
            load_request_sync_2 <= load_request_sync_1;
            load_request_sync_2_q <= load_request_sync_2;
        end
    end

    rtwsr_hbm_read_dma_27pc #(.HBM_PCS(HBM_PCS), .MAX_OUTSTANDING(8)) u_read_dma (
        .clk(axi_clk), .rst_n(axi_reset_n), .load_start(load_start_axi),
        .load_base_address(load_base_address), .load_record_count(load_record_count),
        .busy(dma_busy), .load_done(dma_done), .protocol_error(dma_error),
        .m_axi_araddr(araddr), .m_axi_arid(arid), .m_axi_arlen(arlen),
        .m_axi_arsize(arsize), .m_axi_arburst(arburst), .m_axi_arvalid(arvalid),
        .m_axi_arready(arready), .m_axi_rid(rid), .m_axi_rdata(rdata),
        .m_axi_rresp(rresp), .m_axi_rlast(rlast), .m_axi_rvalid(rvalid),
        .m_axi_rready(rready), .stream_valid(raw_valid), .stream_ready(raw_ready),
        .stream_data(raw_data)
    );

    rtwsr_hbm_gearbox_27lane u_gearbox (
        .core_clk(core_clk), .core_rst_n(core_reset_n),
        .hbm_clk({HBM_PCS{axi_clk}}), .hbm_rst_n({HBM_PCS{axi_reset_n}}),
        .hbm_rvalid(raw_valid), .hbm_rready(raw_ready), .hbm_rdata(raw_data),
        .core_valid(core_valid), .core_ready(core_ready), .core_data(core_data),
        .lane_occupancy(gearbox_occupancy)
    );

    rtwsr_hbm_weight_pool_adapter_27to24 #(.HBM_PCS(HBM_PCS)) u_adapter (
        .clk(core_clk), .rst_n(core_reset_n), .load_start(load_start),
        .load_rows(descriptor_rows), .load_columns(descriptor_columns),
        .load_first_pc(descriptor_first_pc),
        .hbm_valid(core_valid), .hbm_ready(core_ready), .hbm_data(core_data),
        .pool_wr_valid(pool_write_valid), .pool_wr_ready(pool_write_ready),
        .pool_wr_enable(pool_write_enable), .pool_wr_address(pool_write_address),
        .pool_wr_data(pool_write_data), .ring_occupancy(ring_occupancy),
        .load_done(adapter_load_done), .protocol_error(adapter_error)
    );

    ext_apb_mst_top #(.MEM_FILE_SIM("xpm_external_config_file_sim_0.mem")) u_apb_0 (
        .APB_PCLK(apb_clk), .APB_PRESET_N(apb_reset_n),
        .APB_PWDATA(apb0_wdata), .APB_PADDR(apb0_addr),
        .APB_PENABLE(apb0_enable), .APB_PSEL(apb0_select),
        .APB_PWRITE(apb0_write), .APB_PRDATA(apb0_rdata),
        .APB_PREADY(apb0_ready), .APB_PSLVERR(apb0_error), .apb_complete(apb0_done)
    );
    ext_apb_mst_top #(.MEM_FILE_SIM("xpm_external_config_file_sim_1.mem")) u_apb_1 (
        .APB_PCLK(apb_clk), .APB_PRESET_N(apb_reset_n),
        .APB_PWDATA(apb1_wdata), .APB_PADDR(apb1_addr),
        .APB_PENABLE(apb1_enable), .APB_PSEL(apb1_select),
        .APB_PWRITE(apb1_write), .APB_PRDATA(apb1_rdata),
        .APB_PREADY(apb1_ready), .APB_PSLVERR(apb1_error), .apb_complete(apb1_done)
    );

    always_ff @(posedge core_clk) begin
        if (!core_reset_n) begin
            core_cycles <= 0;
            output_groups <= 0;
            pool_output_bytes <= 0;
            peak_ring_occupancy <= 0;
            peak_gearbox_occupancy <= 0;
            measure_core <= 1'b0;
        end else begin
            if (load_start) begin
                core_cycles <= 0;
                output_groups <= 0;
                pool_output_bytes <= 0;
                peak_ring_occupancy <= 0;
                peak_gearbox_occupancy <= 0;
                measure_core <= 1'b1;
            end else if (measure_core) begin
                core_cycles <= core_cycles + 1;
            end
            if (pool_write_valid && pool_write_ready) begin
                if (pool_write_enable != 24'hffffff ||
                    pool_write_address[0 +: 14] != 14'(expected_pool_address(output_groups)))
                    $fatal(1, "HBM pool group address or lane mask mismatch");
                for (integer lane = 1; lane < 24; lane = lane + 1)
                    if (pool_write_address[lane*14 +: 14] !=
                        pool_write_address[0 +: 14])
                        $fatal(1, "HBM pool lane address mismatch");
                output_groups <= output_groups + 1;
                pool_output_bytes <= pool_output_bytes +
                    64 * $countones(pool_write_enable);
                if (output_groups == 0 || (output_groups + 1) % 1024 == 0)
                    $display("U280_HBM27_GROUP_PROGRESS sim_ns=%0.3f groups=%0d expected_groups=%0d address=%0d accepted_beats=%0d ring=%0d gearbox_peak=%0d",
                        $realtime / 1000.0, output_groups + 1, EXPECTED_GROUPS,
                        expected_pool_address(output_groups), accepted_hbm_beats,
                        ring_occupancy, peak_gearbox_occupancy);
            end
            if (int'(ring_occupancy) > peak_ring_occupancy)
                peak_ring_occupancy <= int'(ring_occupancy);
            observed_gearbox_occupancy = peak_gearbox_occupancy;
            for (integer lane = 0; lane < HBM_PCS; lane = lane + 1)
                if (int'(gearbox_occupancy[lane*6 +: 6]) > observed_gearbox_occupancy)
                    observed_gearbox_occupancy = int'(gearbox_occupancy[lane*6 +: 6]);
            if (observed_gearbox_occupancy > peak_gearbox_occupancy)
                peak_gearbox_occupancy <= observed_gearbox_occupancy;
            if (adapter_load_done)
                measure_core <= 1'b0;
        end
    end

    always_ff @(posedge axi_clk) begin
        if (!axi_reset_n) begin
            hbm_cycles <= 0;
            accepted_hbm_beats <= 0;
            measure_hbm <= 1'b0;
            for (integer lane = 0; lane < HBM_PCS; lane = lane + 1)
                pc_beats[lane] <= 0;
        end else begin
            if (load_start_axi) begin
                hbm_cycles <= 0;
                measure_hbm <= 1'b1;
            end else if (measure_hbm) begin
                hbm_cycles <= hbm_cycles + 1;
            end
            if (dma_done)
                measure_hbm <= 1'b0;
            accepted_hbm_beats <= accepted_hbm_beats + $countones(rvalid & rready);
            for (integer lane = 0; lane < HBM_PCS; lane = lane + 1)
                if (rvalid[lane] && rready[lane])
                    pc_beats[lane] <= pc_beats[lane] + 1;
        end
    end

    always @(posedge axi_clk) begin
        if (dma_done)
            $display("U280_HBM27_STAGE DMA_DONE sim_ns=%0.3f accepted_beats=%0d dma_error=%0d",
                $realtime / 1000.0, accepted_hbm_beats, dma_error);
    end

    `define HBM_PC(N, I) \
        .AXI_``N``_ACLK(axi_clk), .AXI_``N``_ARESET_N(axi_reset_n), \
        .AXI_``N``_ARADDR(araddr[I*33 +: 33]), \
        .AXI_``N``_ARBURST(arburst[I*2 +: 2]), \
        .AXI_``N``_ARID(arid[I*6 +: 6]), \
        .AXI_``N``_ARLEN(arlen[I*4 +: 4]), \
        .AXI_``N``_ARSIZE(arsize[I*3 +: 3]), .AXI_``N``_ARVALID(arvalid[I]), \
        .AXI_``N``_RREADY(rready[I]), .AXI_``N``_ARREADY(arready[I]), \
        .AXI_``N``_RDATA(rdata[I*256 +: 256]), \
        .AXI_``N``_RID(rid[I*6 +: 6]), .AXI_``N``_RLAST(rlast[I]), \
        .AXI_``N``_RRESP(rresp[I*2 +: 2]), .AXI_``N``_RVALID(rvalid[I]), \
        .AXI_``N``_AWADDR(33'd0), .AXI_``N``_AWBURST(2'b01), \
        .AXI_``N``_AWID(6'd0), .AXI_``N``_AWLEN(4'd0), \
        .AXI_``N``_AWSIZE(3'd5), .AXI_``N``_AWVALID(1'b0), \
        .AXI_``N``_BREADY(1'b1), .AXI_``N``_WDATA(256'd0), \
        .AXI_``N``_WLAST(1'b0), .AXI_``N``_WSTRB(32'd0), \
        .AXI_``N``_WDATA_PARITY(32'd0), .AXI_``N``_WVALID(1'b0)

    hbm_u280 u_hbm (
        .HBM_REF_CLK_0(hbm_ref_clk_0), .HBM_REF_CLK_1(hbm_ref_clk_1),
        .APB_0_PWDATA(apb0_wdata), .APB_0_PADDR(apb0_addr),
        .APB_0_PCLK(apb_clk), .APB_0_PENABLE(apb0_enable),
        .APB_0_PRESET_N(apb_reset_n), .APB_0_PSEL(apb0_select),
        .APB_0_PWRITE(apb0_write), .APB_0_PRDATA(apb0_rdata),
        .APB_0_PREADY(apb0_ready), .APB_0_PSLVERR(apb0_error),
        .APB_1_PWDATA(apb1_wdata), .APB_1_PADDR(apb1_addr),
        .APB_1_PCLK(apb_clk), .APB_1_PENABLE(apb1_enable),
        .APB_1_PRESET_N(apb_reset_n), .APB_1_PSEL(apb1_select),
        .APB_1_PWRITE(apb1_write), .APB_1_PRDATA(apb1_rdata),
        .APB_1_PREADY(apb1_ready), .APB_1_PSLVERR(apb1_error),
        `HBM_PC(00, 0), `HBM_PC(01, 1), `HBM_PC(02, 2), `HBM_PC(03, 3),
        `HBM_PC(04, 4), `HBM_PC(05, 5), `HBM_PC(06, 6), `HBM_PC(07, 7),
        `HBM_PC(08, 8), `HBM_PC(09, 9), `HBM_PC(10, 10), `HBM_PC(11, 11),
        `HBM_PC(12, 12), `HBM_PC(13, 13), `HBM_PC(14, 14), `HBM_PC(15, 15),
        `HBM_PC(16, 16), `HBM_PC(17, 17), `HBM_PC(18, 18), `HBM_PC(19, 19),
        `HBM_PC(20, 20), `HBM_PC(21, 21), `HBM_PC(22, 22), `HBM_PC(23, 23),
        `HBM_PC(24, 24), `HBM_PC(25, 25), `HBM_PC(26, 26)
        , .AXI_27_ACLK(axi_clk), .AXI_27_ARESET_N(axi_reset_n),
        .AXI_27_ARADDR(33'd0), .AXI_27_ARBURST(2'b01), .AXI_27_ARID(6'd0),
        .AXI_27_ARLEN(4'd0), .AXI_27_ARSIZE(3'd5), .AXI_27_ARVALID(1'b0),
        .AXI_27_AWADDR(33'd0), .AXI_27_AWBURST(2'b01), .AXI_27_AWID(6'd0),
        .AXI_27_AWLEN(4'd0), .AXI_27_AWSIZE(3'd5), .AXI_27_AWVALID(1'b0),
        .AXI_27_RREADY(1'b0), .AXI_27_BREADY(1'b1), .AXI_27_WDATA(256'd0),
        .AXI_27_WLAST(1'b0), .AXI_27_WSTRB(32'd0), .AXI_27_WDATA_PARITY(32'd0),
        .AXI_27_WVALID(1'b0)
    );
    `undef HBM_PC

    initial begin
        #5000 apb_reset_n = 1'b1;
        wait (apb0_done && apb1_done);
        $display("U280_HBM27_STAGE APB_DONE sim_ns=%0.3f", $realtime / 1000.0);
        #10000;
        axi_reset_n = 1'b1;
        core_reset_n = 1'b1;
        repeat (16) @(posedge core_clk);
        if (!descriptor_valid || descriptor_rows != EXPECTED_ROWS ||
            descriptor_columns != EXPECTED_COLUMNS ||
            descriptor_first_pc != EXPECTED_FIRST_PC)
            $fatal(1, "HBM test descriptor mismatch");
        for (integer lane = 0; lane < HBM_PCS; lane = lane + 1)
            if (load_record_count[lane*32 +: 32] != EXPECTED_RECORDS_PER_PC ||
                load_base_address[lane*33 +: 33] != 0)
                $fatal(1, "HBM per-PC descriptor mismatch");
        @(negedge core_clk);
        $display("U280_HBM27_STAGE LOAD_START sim_ns=%0.3f rows=%0d columns=%0d first_pc=%0d records_per_pc=%0d",
            $realtime / 1000.0, descriptor_rows, descriptor_columns,
            descriptor_first_pc, EXPECTED_RECORDS_PER_PC);
        load_start = 1'b1;
        load_request_toggle = ~load_request_toggle;
        @(negedge core_clk);
        load_start = 1'b0;
        wait (adapter_load_done);
        $display("U280_HBM27_STAGE ADAPTER_DONE sim_ns=%0.3f groups=%0d accepted_beats=%0d",
            $realtime / 1000.0, output_groups, accepted_hbm_beats);
        repeat (4) @(posedge core_clk);
        $display("U280_HBM27_DATAFLOW_RESULT groups=%0d expected_groups=%0d pool_bytes=%0d expected_pool_bytes=%0d core_cycles=%0d groups_per_core_cycle=%0f pool_gbps=%0f core_clock_hz=%0d latency_ns=%0f hbm_cycles=%0d hbm_clock_hz=%0d hbm_bytes=%0d effective_hbm_gbps=%0f first_pc=%0d records_per_pc=%0d peak_ring=%0d peak_gearbox=%0d dma_error=%0d adapter_error=%0d",
            output_groups, EXPECTED_GROUPS, pool_output_bytes,
            EXPECTED_GROUPS * 24 * 64, core_cycles,
            real'(output_groups) / real'(core_cycles),
            real'(pool_output_bytes) * CORE_HZ / (real'(core_cycles) * 1.0e9),
            CORE_HZ, real'(core_cycles) * 1.0e9 / CORE_HZ, hbm_cycles, HBM_HZ,
            EXPECTED_RECORDS_PER_PC * HBM_PCS * 64,
            real'(EXPECTED_BEATS_PER_PC * HBM_PCS * 32) * HBM_HZ /
                (real'(hbm_cycles) * 1.0e9),
            descriptor_first_pc, EXPECTED_RECORDS_PER_PC,
            peak_ring_occupancy, peak_gearbox_occupancy, dma_error, adapter_error);
        for (integer lane = 0; lane < HBM_PCS; lane = lane + 1)
            $display("U280_HBM27_PC pc=%0d beats=%0d expected_beats=%0d", lane,
                pc_beats[lane], EXPECTED_BEATS_PER_PC);
        if (output_groups != EXPECTED_GROUPS ||
            pool_output_bytes != EXPECTED_GROUPS * 24 * 64 ||
            dma_error || adapter_error)
            $fatal(1, "U280 HBM dataflow count or protocol error");
        for (integer lane = 0; lane < HBM_PCS; lane = lane + 1)
            if (pc_beats[lane] != EXPECTED_BEATS_PER_PC)
                $fatal(1, "U280 HBM PC beat count mismatch");
        $display("U280_HBM27_DATAFLOW_TEST_PASS");
        $finish;
    end

    initial begin
        forever begin
            #50_000_000;
            $display("U280_HBM27_PROGRESS sim_ns=%0.3f apb_done=%0d%0d load_start=%0d load_start_axi=%0d dma_busy=%0d dma_done=%0d accepted_beats=%0d groups=%0d ring=%0d gearbox_peak=%0d adapter_done=%0d errors=%0d%0d",
                $realtime / 1000.0, apb0_done, apb1_done, load_start,
                load_start_axi, dma_busy, dma_done, accepted_hbm_beats,
                output_groups, ring_occupancy, peak_gearbox_occupancy,
                adapter_load_done, dma_error, adapter_error);
        end
    end

    initial begin
        #10_000_000_000;
        $fatal(1, "U280 HBM dataflow test timeout");
    end
endmodule
