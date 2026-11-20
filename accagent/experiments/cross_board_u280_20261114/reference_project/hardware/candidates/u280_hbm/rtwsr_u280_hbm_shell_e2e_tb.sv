`timescale 1ps / 1ps

module rtwsr_u280_hbm_shell_e2e_tb;
    localparam int HBM_PCS = 27;
    localparam int CORE_HZ = 225_000_000;
    localparam int CONTEXT_TOKENS = 512;
    localparam int POLL_INTERVAL_PS = 1_000_000_000;
    localparam time TIMEOUT_PS = 3_000_000_000_000;

    logic hbm_ref_clk_0 = 1'b0;
    logic hbm_ref_clk_1 = 1'b0;
    logic apb_clk = 1'b0;
    logic apb_reset_n = 1'b0;
    logic core_clk = 1'b0;
    logic core_reset_n = 1'b0;
    logic hbm_axi_clk = 1'b0;
    logic hbm_axi_reset_n = 1'b0;

    logic [11:0] s_axi_awaddr;
    logic [2:0] s_axi_awprot;
    logic s_axi_awvalid, s_axi_awready;
    logic [31:0] s_axi_wdata;
    logic [3:0] s_axi_wstrb;
    logic s_axi_wvalid, s_axi_wready;
    logic [1:0] s_axi_bresp;
    logic s_axi_bvalid, s_axi_bready;
    logic [11:0] s_axi_araddr;
    logic [2:0] s_axi_arprot;
    logic s_axi_arvalid, s_axi_arready;
    logic [31:0] s_axi_rdata;
    logic [1:0] s_axi_rresp;
    logic s_axi_rvalid, s_axi_rready;

    logic [36:0] gamma_araddr;
    logic [4:0] gamma_arid;
    logic [7:0] gamma_arlen;
    logic [2:0] gamma_arsize;
    logic [1:0] gamma_arburst;
    logic gamma_arvalid, gamma_arready;
    logic [4:0] gamma_rid;
    logic [511:0] gamma_rdata;
    logic [1:0] gamma_rresp;
    logic gamma_rlast, gamma_rvalid, gamma_rready;
    logic [63:0] gamma_read_beats;

    logic [HBM_PCS*33-1:0] hbm_araddr;
    logic [HBM_PCS*6-1:0] hbm_arid;
    logic [HBM_PCS*4-1:0] hbm_arlen;
    logic [HBM_PCS*3-1:0] hbm_arsize;
    logic [HBM_PCS*2-1:0] hbm_arburst;
    logic [HBM_PCS-1:0] hbm_arvalid, hbm_arready;
    logic [HBM_PCS*6-1:0] hbm_rid;
    logic [HBM_PCS*256-1:0] hbm_rdata;
    logic [HBM_PCS*2-1:0] hbm_rresp;
    logic [HBM_PCS-1:0] hbm_rlast, hbm_rvalid, hbm_rready;

    logic [31:0] apb0_wdata, apb0_addr, apb0_rdata;
    logic apb0_enable, apb0_select, apb0_write, apb0_ready, apb0_error;
    logic [31:0] apb1_wdata, apb1_addr, apb1_rdata;
    logic apb1_enable, apb1_select, apb1_write, apb1_ready, apb1_error;
    logic apb0_done, apb1_done;

    longint unsigned hbm_ar_count;
    longint unsigned hbm_r_beats;
    integer unsigned hbm_pc_beats [0:HBM_PCS-1];
    integer unsigned read_status;
    integer unsigned cycles_low, cycles_high;
    integer unsigned output_chunks, output_digest, final_context;
    integer unsigned poll_count;
    real elapsed_ms;
    longint unsigned hbm_read_bytes;
    logic [31:0] status_word;
    logic [63:0] shell_cycles;
    logic run_started;

    always #5000 hbm_ref_clk_0 = ~hbm_ref_clk_0;
    always #5000 hbm_ref_clk_1 = ~hbm_ref_clk_1;
    always #5000 apb_clk = ~apb_clk;
    always #2222 core_clk = ~core_clk;
    always #1111 hbm_axi_clk = ~hbm_axi_clk;

    rtwsr_plan6_huginn_u280_hbm_shell u_shell (
        .core_clk(core_clk), .core_rst_n(core_reset_n),
        .hbm_axi_clk(hbm_axi_clk), .hbm_axi_rst_n(hbm_axi_reset_n),
        .s_axi_awaddr(s_axi_awaddr), .s_axi_awprot(s_axi_awprot),
        .s_axi_awvalid(s_axi_awvalid), .s_axi_awready(s_axi_awready),
        .s_axi_wdata(s_axi_wdata), .s_axi_wstrb(s_axi_wstrb),
        .s_axi_wvalid(s_axi_wvalid), .s_axi_wready(s_axi_wready),
        .s_axi_bresp(s_axi_bresp), .s_axi_bvalid(s_axi_bvalid),
        .s_axi_bready(s_axi_bready), .s_axi_araddr(s_axi_araddr),
        .s_axi_arprot(s_axi_arprot), .s_axi_arvalid(s_axi_arvalid),
        .s_axi_arready(s_axi_arready), .s_axi_rdata(s_axi_rdata),
        .s_axi_rresp(s_axi_rresp), .s_axi_rvalid(s_axi_rvalid),
        .s_axi_rready(s_axi_rready),
        .gamma_m_axi_araddr(gamma_araddr), .gamma_m_axi_arid(gamma_arid),
        .gamma_m_axi_arlen(gamma_arlen), .gamma_m_axi_arsize(gamma_arsize),
        .gamma_m_axi_arburst(gamma_arburst), .gamma_m_axi_arvalid(gamma_arvalid),
        .gamma_m_axi_arready(gamma_arready), .gamma_m_axi_rid(gamma_rid),
        .gamma_m_axi_rdata(gamma_rdata), .gamma_m_axi_rresp(gamma_rresp),
        .gamma_m_axi_rlast(gamma_rlast), .gamma_m_axi_rvalid(gamma_rvalid),
        .gamma_m_axi_rready(gamma_rready),
        .hbm_m_axi_araddr(hbm_araddr), .hbm_m_axi_arid(hbm_arid),
        .hbm_m_axi_arlen(hbm_arlen), .hbm_m_axi_arsize(hbm_arsize),
        .hbm_m_axi_arburst(hbm_arburst), .hbm_m_axi_arvalid(hbm_arvalid),
        .hbm_m_axi_arready(hbm_arready), .hbm_m_axi_rid(hbm_rid),
        .hbm_m_axi_rdata(hbm_rdata), .hbm_m_axi_rresp(hbm_rresp),
        .hbm_m_axi_rlast(hbm_rlast), .hbm_m_axi_rvalid(hbm_rvalid),
        .hbm_m_axi_rready(hbm_rready)
    );

    rtwsr_u280_axil_bfm u_axil (
        .clk(core_clk), .rst_n(core_reset_n),
        .awaddr(s_axi_awaddr), .awprot(s_axi_awprot),
        .awvalid(s_axi_awvalid), .awready(s_axi_awready),
        .wdata(s_axi_wdata), .wstrb(s_axi_wstrb),
        .wvalid(s_axi_wvalid), .wready(s_axi_wready),
        .bresp(s_axi_bresp), .bvalid(s_axi_bvalid), .bready(s_axi_bready),
        .araddr(s_axi_araddr), .arprot(s_axi_arprot),
        .arvalid(s_axi_arvalid), .arready(s_axi_arready),
        .rdata(s_axi_rdata), .rresp(s_axi_rresp),
        .rvalid(s_axi_rvalid), .rready(s_axi_rready)
    );

    rtwsr_u280_gamma_axi_bfm u_gamma_bfm (
        .clk(core_clk), .rst_n(core_reset_n),
        .araddr(gamma_araddr), .arid(gamma_arid), .arlen(gamma_arlen),
        .arsize(gamma_arsize), .arburst(gamma_arburst),
        .arvalid(gamma_arvalid), .arready(gamma_arready),
        .rid(gamma_rid), .rdata(gamma_rdata), .rresp(gamma_rresp),
        .rlast(gamma_rlast), .rvalid(gamma_rvalid), .rready(gamma_rready),
        .read_beats(gamma_read_beats)
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

    always_ff @(posedge hbm_axi_clk) begin
        if (!hbm_axi_reset_n) begin
            hbm_ar_count <= 64'd0;
            hbm_r_beats <= 64'd0;
            for (integer lane = 0; lane < HBM_PCS; lane = lane + 1)
                hbm_pc_beats[lane] <= 0;
        end else begin
            hbm_ar_count <= hbm_ar_count + $countones(hbm_arvalid & hbm_arready);
            hbm_r_beats <= hbm_r_beats + $countones(hbm_rvalid & hbm_rready);
            for (integer lane = 0; lane < HBM_PCS; lane = lane + 1) begin
                if (hbm_rvalid[lane] && hbm_rready[lane]) begin
                    hbm_pc_beats[lane] <= hbm_pc_beats[lane] + 1;
                end
            end
        end
    end

    `define HBM_PC(N, I) \
        .AXI_``N``_ACLK(hbm_axi_clk), .AXI_``N``_ARESET_N(hbm_axi_reset_n), \
        .AXI_``N``_ARADDR(hbm_araddr[I*33 +: 33]), \
        .AXI_``N``_ARBURST(hbm_arburst[I*2 +: 2]), \
        .AXI_``N``_ARID(hbm_arid[I*6 +: 6]), \
        .AXI_``N``_ARLEN(hbm_arlen[I*4 +: 4]), \
        .AXI_``N``_ARSIZE(hbm_arsize[I*3 +: 3]), .AXI_``N``_ARVALID(hbm_arvalid[I]), \
        .AXI_``N``_RREADY(hbm_rready[I]), .AXI_``N``_ARREADY(hbm_arready[I]), \
        .AXI_``N``_RDATA(hbm_rdata[I*256 +: 256]), \
        .AXI_``N``_RID(hbm_rid[I*6 +: 6]), .AXI_``N``_RLAST(hbm_rlast[I]), \
        .AXI_``N``_RRESP(hbm_rresp[I*2 +: 2]), .AXI_``N``_RVALID(hbm_rvalid[I]), \
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
        `HBM_PC(24, 24), `HBM_PC(25, 25), `HBM_PC(26, 26),
        .AXI_27_ACLK(hbm_axi_clk), .AXI_27_ARESET_N(hbm_axi_reset_n),
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
        run_started = 1'b0;
        #5000 apb_reset_n = 1'b1;
        wait (apb0_done && apb1_done);
        $display("U280_HBM_E2E_STAGE APB_DONE sim_ns=%0.3f", $realtime / 1000.0);
        core_reset_n = 1'b1;
        hbm_axi_reset_n = 1'b1;
        repeat (16) @(posedge core_clk);

        u_axil.write_reg(12'h018, CONTEXT_TOKENS);
        u_axil.read_reg(12'h018, final_context);
        if (final_context != CONTEXT_TOKENS)
            $fatal(1, "AXI-Lite context readback mismatch: %0d", final_context);
        $display("U280_HBM_E2E_STAGE CONFIGURED context=%0d sim_ns=%0.3f",
            final_context, $realtime / 1000.0);

        run_started = 1'b1;
        u_axil.write_reg(12'h000, 32'd1);
        $display("U280_HBM_E2E_STAGE START sim_ns=%0.3f blocks=4 recurrences=32 context=%0d",
            $realtime / 1000.0, CONTEXT_TOKENS);
        poll_count = 0;
        status_word = '0;
        while (!status_word[0] && !status_word[2] && poll_count < TIMEOUT_PS / POLL_INTERVAL_PS) begin
            #(POLL_INTERVAL_PS);
            u_axil.read_reg(12'h004, read_status);
            status_word = read_status;
            poll_count = poll_count + 1;
            $display("U280_HBM_E2E_PROGRESS poll=%0d sim_ns=%0.3f status=0x%08x hbm_ar=%0d hbm_r_beats=%0d gamma_r_beats=%0d",
                poll_count, $realtime / 1000.0, status_word,
                hbm_ar_count, hbm_r_beats, gamma_read_beats);
        end

        if (!status_word[0])
            $fatal(1, "FlightCore run failed or timed out: status=0x%08x", status_word);
        u_axil.read_reg(12'h008, cycles_low);
        u_axil.read_reg(12'h00c, cycles_high);
        u_axil.read_reg(12'h010, output_chunks);
        u_axil.read_reg(12'h014, output_digest);
        u_axil.read_reg(12'h018, final_context);
        shell_cycles = {cycles_high, cycles_low};
        hbm_read_bytes = hbm_r_beats * 64'd32;
        elapsed_ms = real'(shell_cycles) * 1000.0 / real'(CORE_HZ);
        $display("U280_HBM_E2E_RESULT model=Huginn-3.5B scope=recurrent_core blocks=4 recurrences=32 context=%0d status=0x%08x shell_cycles=%0d core_clock_hz=%0d latency_ms=%0.6f output_chunks=%0d output_digest=0x%08x hbm_ar_bursts=%0d hbm_r_beats=%0d hbm_bytes=%0d gamma_r_beats=%0d",
            final_context, status_word, shell_cycles, CORE_HZ, elapsed_ms,
            output_chunks, output_digest, hbm_ar_count, hbm_r_beats,
            hbm_read_bytes, gamma_read_beats);
        for (integer lane = 0; lane < HBM_PCS; lane = lane + 1)
            $display("U280_HBM_E2E_PC pc=%0d r_beats=%0d", lane, hbm_pc_beats[lane]);
        if (status_word[2] || !status_word[0])
            $fatal(1, "FlightCore reported error or failed to complete");
        $display("U280_HBM_E2E_TEST_PASS");
        $finish;
    end

    initial begin
        wait (run_started);
        forever begin
            #POLL_INTERVAL_PS;
            $display("U280_HBM_E2E_HEARTBEAT sim_ns=%0.3f status=0x%08x hbm_ar=%0d hbm_r_beats=%0d gamma_r_beats=%0d",
                $realtime / 1000.0, u_shell.u_plan6_huginn_hbm_shell.status_word,
                hbm_ar_count, hbm_r_beats, gamma_read_beats);
        end
    end

    initial begin
        #TIMEOUT_PS;
        if (!status_word[0])
            $fatal(1, "U280 FlightCore E2E timeout");
    end
endmodule
