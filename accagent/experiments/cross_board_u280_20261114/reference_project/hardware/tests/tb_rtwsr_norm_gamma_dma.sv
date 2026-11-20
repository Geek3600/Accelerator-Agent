`timescale 1ns / 1ps

module tb_rtwsr_norm_gamma_dma;
    localparam int NORM_VALUES = 4 * 4 * 5280;
    localparam int NORM_WORDS = NORM_VALUES / 32;
    localparam int NORM_TILES = NORM_VALUES / 96;
    localparam logic [36:0] NORM_GAMMA_BASE = 37'h0a01032000;

    logic clk = 1'b0;
    logic clock_run = 1'b1;
    logic rst_n = 1'b0;
    integer test_cycle_count = 0;
    always #5 if (clock_run) clk = ~clk;
    always @(posedge clk) begin
        if (!rst_n)
            test_cycle_count <= 0;
        else
            test_cycle_count <= test_cycle_count + 1;
    end

    logic [11:0] s_axi_awaddr = '0;
    logic [2:0] s_axi_awprot = '0;
    logic s_axi_awvalid = 1'b0;
    wire s_axi_awready;
    logic [31:0] s_axi_wdata = '0;
    logic [3:0] s_axi_wstrb = 4'hf;
    logic s_axi_wvalid = 1'b0;
    wire s_axi_wready;
    wire [1:0] s_axi_bresp;
    wire s_axi_bvalid;
    logic s_axi_bready = 1'b0;
    logic [11:0] s_axi_araddr = '0;
    logic [2:0] s_axi_arprot = '0;
    logic s_axi_arvalid = 1'b0;
    wire s_axi_arready;
    wire [31:0] s_axi_rdata;
    wire [1:0] s_axi_rresp;
    wire s_axi_rvalid;
    logic s_axi_rready = 1'b0;

    wire [36:0] m_axi_araddr;
    wire [4:0] m_axi_arid;
    wire [7:0] m_axi_arlen;
    wire [2:0] m_axi_arsize;
    wire [1:0] m_axi_arburst;
    wire m_axi_arvalid;
    wire m_axi_arready = 1'b1;
    logic [4:0] m_axi_rid = '0;
    logic [511:0] m_axi_rdata = '0;
    logic [1:0] m_axi_rresp = '0;
    logic m_axi_rlast = 1'b0;
    logic m_axi_rvalid = 1'b0;
    wire m_axi_rready;
    wire [32*33-1:0] hbm_m_axi_araddr;
    wire [32*6-1:0] hbm_m_axi_arid;
    wire [32*4-1:0] hbm_m_axi_arlen;
    wire [32*3-1:0] hbm_m_axi_arsize;
    wire [32*2-1:0] hbm_m_axi_arburst;
    wire [31:0] hbm_m_axi_arvalid;
    wire [31:0] hbm_m_axi_rready;

    logic read_active_q = 1'b0;
    logic [8:0] burst_left_q = '0;
    integer payload_word_q = 0;
    integer burst_count_q = 0;
    logic [15:0] expected_gamma [0:NORM_VALUES-1];
    logic [10:0] probe_address = '0;
    wire [1535:0] probed_tile;

    logic tile_request;
    logic [4:0] tile_command, stream_command;
    logic [5:0] requested_block;
    logic [8:0] requested_tile, requested_chunk;
    logic [10:0] actual_address;
    logic [10:0] expected_address;
    logic [4:0] norm_commands [0:3];

    generate
        for (genvar bank = 0; bank < 48; bank++) begin : g_probe_bank
            assign probed_tile[bank*32 +: 32] =
                dut.g_norm_gamma_store.g_bank[bank].memory[probe_address];
        end
    endgenerate

    rtwsr_plan6_huginn_9p_axi #(
        .RESIDUAL_NORM_FUSION(1'b1),
        .RESIDUAL_NORM_TILE_PRELOAD(1'b1),
        .NORM_GAMMA_FROM_HOST(1'b1)
    ) dut (
        .s_axi_aclk(clk), .s_axi_aresetn(rst_n),
        .s_axi_awaddr(s_axi_awaddr), .s_axi_awprot(s_axi_awprot),
        .s_axi_awvalid(s_axi_awvalid), .s_axi_awready(s_axi_awready),
        .s_axi_wdata(s_axi_wdata), .s_axi_wstrb(s_axi_wstrb),
        .s_axi_wvalid(s_axi_wvalid), .s_axi_wready(s_axi_wready),
        .s_axi_bresp(s_axi_bresp), .s_axi_bvalid(s_axi_bvalid),
        .s_axi_bready(s_axi_bready),
        .s_axi_araddr(s_axi_araddr), .s_axi_arprot(s_axi_arprot),
        .s_axi_arvalid(s_axi_arvalid), .s_axi_arready(s_axi_arready),
        .s_axi_rdata(s_axi_rdata), .s_axi_rresp(s_axi_rresp),
        .s_axi_rvalid(s_axi_rvalid), .s_axi_rready(s_axi_rready),
        .m_axi_araddr(m_axi_araddr), .m_axi_arid(m_axi_arid),
        .m_axi_arlen(m_axi_arlen), .m_axi_arsize(m_axi_arsize),
        .m_axi_arburst(m_axi_arburst), .m_axi_arvalid(m_axi_arvalid),
        .m_axi_arready(m_axi_arready), .m_axi_rid(m_axi_rid),
        .m_axi_rdata(m_axi_rdata), .m_axi_rresp(m_axi_rresp),
        .m_axi_rlast(m_axi_rlast), .m_axi_rvalid(m_axi_rvalid),
        .m_axi_rready(m_axi_rready),
        .hbm_axi_clk(clk), .hbm_axi_rst_n(rst_n),
        .hbm_m_axi_araddr(hbm_m_axi_araddr), .hbm_m_axi_arid(hbm_m_axi_arid),
        .hbm_m_axi_arlen(hbm_m_axi_arlen), .hbm_m_axi_arsize(hbm_m_axi_arsize),
        .hbm_m_axi_arburst(hbm_m_axi_arburst), .hbm_m_axi_arvalid(hbm_m_axi_arvalid),
        .hbm_m_axi_arready('0), .hbm_m_axi_rid('0), .hbm_m_axi_rdata('0),
        .hbm_m_axi_rresp('0), .hbm_m_axi_rlast('0), .hbm_m_axi_rvalid('0),
        .hbm_m_axi_rready(hbm_m_axi_rready)
    );

    function automatic logic [511:0] payload_word(input integer word_index);
        logic [511:0] word_data;
        begin
            for (integer lane = 0; lane < 32; lane++)
                word_data[lane*16 +: 16] = expected_gamma[word_index*32 + lane];
            return word_data;
        end
    endfunction

    always @(posedge clk) begin
        integer expected_burst;
        integer beats_left;
        if (!rst_n) begin
            read_active_q <= 1'b0;
            burst_left_q <= '0;
            payload_word_q <= 0;
            burst_count_q <= 0;
            m_axi_rvalid <= 1'b0;
            m_axi_rdata <= '0;
            m_axi_rresp <= '0;
            m_axi_rlast <= 1'b0;
        end else begin
            if (m_axi_arvalid && m_axi_arready) begin
                if (read_active_q || m_axi_arid != 0 || m_axi_arsize != 6 ||
                    m_axi_arburst != 1 || m_axi_araddr != NORM_GAMMA_BASE +
                        37'(payload_word_q * 64))
                    $fatal(1, "unexpected gamma DMA address or AR attributes");
                beats_left = NORM_WORDS - payload_word_q;
                expected_burst = 64 - int'(m_axi_araddr[11:6]);
                if (expected_burst > beats_left)
                    expected_burst = beats_left;
                if (int'(m_axi_arlen) + 1 != expected_burst)
                    $fatal(1, "gamma DMA burst length mismatch at word %0d", payload_word_q);
                burst_left_q <= 9'(expected_burst);
                read_active_q <= 1'b1;
                burst_count_q <= burst_count_q + 1;
            end

            if (m_axi_rvalid && m_axi_rready) begin
                if (m_axi_rresp != 0 || m_axi_rid != 0 ||
                    m_axi_rlast != (burst_left_q == 1))
                    $fatal(1, "gamma DMA response attributes mismatch");
                m_axi_rvalid <= 1'b0;
                payload_word_q <= payload_word_q + 1;
                if (burst_left_q == 1) begin
                    burst_left_q <= '0;
                    read_active_q <= 1'b0;
                end else begin
                    burst_left_q <= burst_left_q - 1'b1;
                end
            end else if (read_active_q && !m_axi_rvalid) begin
                if (payload_word_q >= NORM_WORDS)
                    $fatal(1, "gamma DMA read beyond payload");
                m_axi_rdata <= payload_word(payload_word_q);
                m_axi_rresp <= 0;
                m_axi_rid <= 0;
                m_axi_rlast <= burst_left_q == 1;
                m_axi_rvalid <= 1'b1;
            end
        end
    end

    task automatic write_start;
        begin
            @(negedge clk);
            s_axi_awaddr = 12'h000;
            s_axi_wdata = 32'h00000001;
            s_axi_awvalid = 1'b1;
            s_axi_wvalid = 1'b1;
            do @(posedge clk); while (!(s_axi_awready && s_axi_wready));
            @(negedge clk);
            s_axi_awvalid = 1'b0;
            s_axi_wvalid = 1'b0;
            wait (s_axi_bvalid);
            @(negedge clk);
            s_axi_bready = 1'b1;
            @(posedge clk);
            @(negedge clk);
            s_axi_bready = 1'b0;
        end
    endtask

    initial begin
        integer norm_index;
        integer block;
        integer tile;
        integer chunk;
        integer lane;
        integer global_tile;
        integer command_id;
        integer norm_base;

        norm_commands[0] = 5'd2;
        norm_commands[1] = 5'd10;
        norm_commands[2] = 5'd11;
        norm_commands[3] = 5'd16;
        $readmemh("rmsnorm_q412.mem", expected_gamma);
        repeat (5) @(posedge clk);
        @(negedge clk);
        rst_n = 1'b1;
        repeat (3) @(posedge clk);
        if (dut.norm_gamma_loaded_q)
            $fatal(1, "gamma payload must load before the first core start");
        write_start();

        wait (dut.norm_gamma_loaded_q);
        clock_run = 1'b0;
        #1;
        if (payload_word_q != NORM_WORDS || burst_count_q != 42 ||
            read_active_q || dut.norm_gamma_load_tile_index_q != NORM_TILES ||
            dut.norm_gamma_load_beat_q != 0 || dut.state_q != 5'd16 ||
            dut.shell_error_q || dut.dma_error || dut.gamma_protocol_error)
            $fatal(1, "gamma load did not finish cleanly");

        for (global_tile = 0; global_tile < NORM_TILES; global_tile++) begin
            probe_address = 11'(global_tile);
            #1;
            for (lane = 0; lane < 96; lane++) begin
                if (probed_tile[lane*16 +: 16] !==
                    expected_gamma[global_tile*96 + lane])
                    $fatal(1, "gamma tile mismatch tile=%0d lane=%0d", global_tile, lane);
            end
        end

        for (block = 0; block < 4; block++) begin
            for (norm_index = 0; norm_index < 4; norm_index++) begin
                command_id = norm_commands[norm_index];
                for (tile = 0; tile < 55; tile++) begin
                    tile_request = 1'b1;
                    tile_command = 5'(command_id);
                    stream_command = '0;
                    requested_block = 6'(block);
                    requested_tile = 9'(tile);
                    requested_chunk = '0;
                    actual_address = dut.norm_gamma_address(
                        tile_request, tile_command, stream_command, requested_block,
                        requested_tile, requested_chunk);
                    expected_address = 11'(block*220 + norm_index*55 + tile);
                    if (actual_address !== expected_address)
                        $fatal(1, "preload address mismatch command=%0d block=%0d tile=%0d",
                               command_id, block, tile);
                    probe_address = actual_address;
                    #1;
                    norm_base = block*4*5280 + norm_index*5280 + tile*96;
                    for (lane = 0; lane < 96; lane++) begin
                        if (probed_tile[lane*16 +: 16] !== expected_gamma[norm_base + lane])
                            $fatal(1, "command tile mismatch command=%0d block=%0d tile=%0d lane=%0d",
                                   command_id, block, tile, lane);
                    end
                end

                for (chunk = 0; chunk < 330; chunk++) begin
                    tile_request = 1'b0;
                    tile_command = '0;
                    stream_command = 5'(command_id);
                    requested_block = 6'(block);
                    requested_tile = '0;
                    requested_chunk = 9'(chunk);
                    actual_address = dut.norm_gamma_address(
                        tile_request, tile_command, stream_command, requested_block,
                        requested_tile, requested_chunk);
                    expected_address = 11'(block*220 + norm_index*55 + chunk/6);
                    if (actual_address !== expected_address)
                        $fatal(1, "chunk address mismatch command=%0d block=%0d chunk=%0d",
                               command_id, block, chunk);
                end
            end
        end

        $display("NORM_GAMMA_DMA_PASS cycles=%0d bytes=%0d words=%0d tiles=%0d bursts=%0d address_checks=%0d",
                 test_cycle_count, NORM_VALUES*2, payload_word_q, NORM_TILES, burst_count_q,
                 4*4*(55+330));
        $finish;
    end

    initial begin
        #20000000;
        $fatal(1, "Norm gamma DMA test timeout");
    end
endmodule
