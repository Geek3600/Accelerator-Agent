`timescale 1ns / 1ps

module tb_rtwsr_adapter_hbm_skip #(parameter int POOL_LANES = 24);
    localparam int PCS = 32;
    localparam int ADAPTER_START_RECORD = 6268416;
    localparam int ADAPTER_RECORDS = 221760;
    logic clk = 0, rst_n = 0, start = 0;
    logic [PCS*33-1:0] base, araddr;
    logic [PCS*32-1:0] full_counts, counts;
    logic [PCS*6-1:0] arid, rid;
    logic [PCS*4-1:0] arlen;
    logic [PCS*3-1:0] arsize;
    logic [PCS*2-1:0] arburst, rresp;
    logic [PCS-1:0] arvalid, arready, rlast, rvalid, rready, stream_valid, model_error;
    logic [PCS*256-1:0] rdata, stream_data;
    logic [4:0] first_pc;
    logic busy, done, error, valid;
    logic [15:0] rows, columns;
    bit [1:0] seen [0:ADAPTER_RECORDS-1];
    integer issued_beats = 0;

    always #5 clk = ~clk;

    rtwsr_huginn_u280_hbm_descriptor #(.POOL_LANES(POOL_LANES)) u_descriptor (
        .command_id(5'd0), .block_index(6'd0), .valid(valid), .matrix_rows(rows),
        .matrix_columns(columns), .first_pc(first_pc), .pc_base_address(base),
        .pc_record_count(full_counts)
    );
    always_comb begin
        for (integer pc = 0; pc < PCS; pc++)
            counts[pc*32 +: 32] = POOL_LANES == 32 ? 32'd3465 :
                ((pc % 16 < 8) ? 32'd3520 : 32'd3410);
    end
    rtwsr_hbm_read_dma_27pc #(.HBM_PCS(PCS), .POOL_LANES(POOL_LANES), .ADAPTER_STATIC_REUSE(1'b1)) u_dma (
        .clk(clk), .rst_n(rst_n), .load_start(start), .load_skip_adapter_static(1'b1),
        .load_first_pc(first_pc), .load_base_address(base), .load_record_count(counts),
        .busy(busy), .load_done(done), .protocol_error(error), .m_axi_araddr(araddr),
        .m_axi_arid(arid), .m_axi_arlen(arlen), .m_axi_arsize(arsize), .m_axi_arburst(arburst),
        .m_axi_arvalid(arvalid), .m_axi_arready(arready), .m_axi_rid(rid), .m_axi_rdata(rdata),
        .m_axi_rresp(rresp), .m_axi_rlast(rlast), .m_axi_rvalid(rvalid), .m_axi_rready(rready),
        .stream_valid(stream_valid), .stream_ready({PCS{1'b1}}), .stream_data(stream_data)
    );
    rtwsr_u280_hbm_axi_cycle_model #(.HBM_PCS(PCS)) u_memory (
        .hbm_clk(clk), .hbm_rst_n(rst_n), .araddr(araddr), .arid(arid), .arlen(arlen),
        .arsize(arsize), .arburst(arburst), .arvalid(arvalid), .arready(arready), .rid(rid),
        .rdata(rdata), .rresp(rresp), .rlast(rlast), .rvalid(rvalid), .rready(rready),
        .protocol_error(model_error)
    );

    always @(posedge clk) begin
        if (rst_n) begin
            for (integer pc = 0; pc < PCS; pc++) begin
                if (arvalid[pc] && arready[pc]) begin
                    for (integer beat = 0; beat <= int'(arlen[pc*4 +: 4]); beat++) begin
                        integer byte_address, record, half;
                        byte_address = int'(araddr[pc*33 +: 33]) + beat*32;
                        record = (byte_address / 64)*PCS + pc - ADAPTER_START_RECORD;
                        half = (byte_address / 32) % 2;
                        if (record < 0 || record >= ADAPTER_RECORDS ||
                            (record / POOL_LANES) % 42 >= 21 || seen[record][half])
                            $fatal(1, "invalid adapter read pc=%0d address=%0d record=%0d half=%0d",
                                pc, byte_address, record, half);
                        seen[record][half] = 1'b1;
                        issued_beats++;
                    end
                end
            end
            if (error || (|model_error))
                $fatal(1, "HBM skip protocol error");
        end
    end

    initial begin
        repeat (3) @(negedge clk);
        rst_n = 1;
        if (!valid || rows != 5280 || columns != 10560 || first_pc != 0)
            $fatal(1, "Adapter descriptor mismatch");
        start = 1;
        @(negedge clk);
        start = 0;
        wait (done);
        @(negedge clk);
        for (integer record = 0; record < ADAPTER_RECORDS; record++) begin
            if ((record / POOL_LANES) % 42 < 21) begin
                if (seen[record] !== 2'b11)
                    $fatal(1, "missing required Adapter record %0d", record);
            end else if (seen[record] !== 2'b00) begin
                $fatal(1, "read skipped Adapter record %0d", record);
            end
        end
        if (issued_beats != 221760)
            $fatal(1, "incorrect beat total %0d", issued_beats);
        $display("PASS Adapter HBM skip lanes=%0d PCs=32 records=110880 beats=221760", POOL_LANES);
        $finish;
    end

    initial begin
        #2000000;
        $fatal(1, "Adapter HBM skip timeout");
    end
endmodule
