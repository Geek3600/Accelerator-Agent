`timescale 1ns / 1ps

module rtwsr_plan6_huginn_u280_hbm_weight_path #(
    parameter int HBM_PCS = 32,
    parameter int POOL_LANES = 24,
    parameter int RING_RECORDS = 73728,
    parameter int RING_DEPTH = RING_RECORDS / HBM_PCS,
    parameter int MAX_OUTSTANDING = 16,
    parameter bit ADAPTER_STATIC_REUSE = 1'b0
)(
    input  logic                         core_clk,
    input  logic                         core_rst_n,
    input  logic                         axi_clk,
    input  logic                         axi_rst_n,
    input  logic                         load_start,
    input  logic [4:0]                   load_command_id,
    input  logic [5:0]                   load_block_index,
    input  logic [15:0]                  load_rows,
    input  logic [15:0]                  load_columns,
    input  logic                         load_skip_adapter_static,
    output logic                         load_busy,
    output logic                         load_done,
    output logic                         protocol_error,
    output logic [HBM_PCS*33-1:0]        m_axi_araddr,
    output logic [HBM_PCS*6-1:0]         m_axi_arid,
    output logic [HBM_PCS*4-1:0]         m_axi_arlen,
    output logic [HBM_PCS*3-1:0]         m_axi_arsize,
    output logic [HBM_PCS*2-1:0]         m_axi_arburst,
    output logic [HBM_PCS-1:0]           m_axi_arvalid,
    input  logic [HBM_PCS-1:0]           m_axi_arready,
    input  logic [HBM_PCS*6-1:0]         m_axi_rid,
    input  logic [HBM_PCS*256-1:0]       m_axi_rdata,
    input  logic [HBM_PCS*2-1:0]         m_axi_rresp,
    input  logic [HBM_PCS-1:0]           m_axi_rlast,
    input  logic [HBM_PCS-1:0]           m_axi_rvalid,
    output logic [HBM_PCS-1:0]           m_axi_rready,
    output logic                         pool_wr_valid,
    input  logic                         pool_wr_ready,
    output logic [POOL_LANES-1:0]        pool_wr_enable,
    output logic [POOL_LANES*14-1:0]     pool_wr_address,
    output logic [POOL_LANES*512-1:0]    pool_wr_data,
    output logic [$clog2(HBM_PCS*RING_DEPTH+1)-1:0] ring_occupancy
);
    localparam int OCCUPANCY_WIDTH = $clog2(HBM_PCS * RING_DEPTH + 1);

    logic descriptor_valid;
    logic [15:0] descriptor_rows, descriptor_columns;
    logic [4:0] descriptor_first_pc;
    logic [HBM_PCS*33-1:0] descriptor_base_address;
    logic [HBM_PCS*32-1:0] descriptor_record_count;

    logic [15:0] rows_q, columns_q;
    logic [4:0] first_pc_q;
    logic [HBM_PCS*33-1:0] base_address_q;
    logic [HBM_PCS*32-1:0] record_count_q;
    logic request_toggle_q;
    logic [1:0] request_sync_q;
    logic request_seen_q;
    logic [1:0] done_sync_q;
    logic done_seen_q;
    logic [1:0] error_sync_q;
    logic dma_start_q;
    logic dma_busy, dma_done, dma_error;
    logic dma_done_toggle_q;
    logic adapter_done, adapter_error;
    logic [HBM_PCS-1:0] dma_stream_valid, gearbox_hbm_ready;
    logic [HBM_PCS*256-1:0] dma_stream_data;
    logic [HBM_PCS-1:0] gearbox_core_valid;
    logic [HBM_PCS*512-1:0] gearbox_core_data;
    logic [HBM_PCS*6-1:0] gearbox_occupancy;
    logic adapter_start_q;
    logic path_busy_q;
    logic path_error_q;
    logic skip_adapter_q;
    logic [HBM_PCS-1:0] adapter_ready;

    rtwsr_huginn_u280_hbm_descriptor #(
        .HBM_PCS(HBM_PCS), .POOL_LANES(POOL_LANES)
    ) u_descriptor (
        .command_id(load_command_id), .block_index(load_block_index),
        .valid(descriptor_valid), .matrix_rows(descriptor_rows),
        .matrix_columns(descriptor_columns), .first_pc(descriptor_first_pc),
        .pc_base_address(descriptor_base_address),
        .pc_record_count(descriptor_record_count)
    );

    rtwsr_hbm_read_dma_27pc #(
        .HBM_PCS(HBM_PCS), .POOL_LANES(POOL_LANES), .MAX_OUTSTANDING(MAX_OUTSTANDING),
        .ADAPTER_STATIC_REUSE(ADAPTER_STATIC_REUSE)
    ) u_weight_dma (
        .clk(axi_clk), .rst_n(axi_rst_n), .load_start(dma_start_q),
        .load_skip_adapter_static(skip_adapter_q), .load_first_pc(first_pc_q),
        .load_base_address(base_address_q), .load_record_count(record_count_q),
        .busy(dma_busy), .load_done(dma_done), .protocol_error(dma_error),
        .m_axi_araddr(m_axi_araddr), .m_axi_arid(m_axi_arid),
        .m_axi_arlen(m_axi_arlen), .m_axi_arsize(m_axi_arsize),
        .m_axi_arburst(m_axi_arburst), .m_axi_arvalid(m_axi_arvalid),
        .m_axi_arready(m_axi_arready), .m_axi_rid(m_axi_rid),
        .m_axi_rdata(m_axi_rdata), .m_axi_rresp(m_axi_rresp),
        .m_axi_rlast(m_axi_rlast), .m_axi_rvalid(m_axi_rvalid),
        .m_axi_rready(m_axi_rready), .stream_valid(dma_stream_valid),
        .stream_ready(gearbox_hbm_ready), .stream_data(dma_stream_data)
    );

    rtwsr_hbm_gearbox_27lane #(.LANES(HBM_PCS)) u_weight_gearbox (
        .core_clk(core_clk), .core_rst_n(core_rst_n),
        .hbm_clk({HBM_PCS{axi_clk}}), .hbm_rst_n({HBM_PCS{axi_rst_n}}),
        .hbm_rvalid(dma_stream_valid), .hbm_rready(gearbox_hbm_ready),
        .hbm_rdata(dma_stream_data), .core_valid(gearbox_core_valid),
        .core_ready(adapter_ready), .core_data(gearbox_core_data),
        .lane_occupancy(gearbox_occupancy)
    );

    rtwsr_hbm_weight_pool_adapter_27to24 #(
        .HBM_PCS(HBM_PCS), .POOL_LANES(POOL_LANES), .FIFO_DEPTH(RING_DEPTH),
        .ADAPTER_STATIC_REUSE(ADAPTER_STATIC_REUSE),
        .OCCUPANCY_WIDTH(OCCUPANCY_WIDTH)
    ) u_weight_adapter (
        .clk(core_clk), .rst_n(core_rst_n), .load_start(adapter_start_q),
        .load_rows(rows_q), .load_columns(columns_q), .load_first_pc(first_pc_q),
        .load_skip_adapter_static(skip_adapter_q),
        .hbm_valid(gearbox_core_valid), .hbm_ready(adapter_ready),
        .hbm_data(gearbox_core_data), .pool_wr_valid(pool_wr_valid),
        .pool_wr_ready(pool_wr_ready), .pool_wr_enable(pool_wr_enable),
        .pool_wr_address(pool_wr_address), .pool_wr_data(pool_wr_data),
        .ring_occupancy(ring_occupancy), .load_done(adapter_done),
        .protocol_error(adapter_error)
    );

    always_ff @(posedge core_clk) begin
        if (!core_rst_n) begin
            rows_q <= '0;
            columns_q <= '0;
            first_pc_q <= '0;
            base_address_q <= '0;
            record_count_q <= '0;
            request_toggle_q <= 1'b0;
            done_sync_q <= '0;
            done_seen_q <= 1'b0;
            error_sync_q <= '0;
            adapter_start_q <= 1'b0;
            path_busy_q <= 1'b0;
            path_error_q <= 1'b0;
            skip_adapter_q <= 1'b0;
            load_done <= 1'b0;
        end else begin
            done_sync_q <= {done_sync_q[0], dma_done_toggle_q};
            error_sync_q <= {error_sync_q[0], dma_error};
            adapter_start_q <= 1'b0;
            load_done <= 1'b0;

            if (load_start && !path_busy_q) begin
                if (!descriptor_valid || load_rows != descriptor_rows ||
                    load_columns != descriptor_columns ||
                    (ADAPTER_STATIC_REUSE && load_skip_adapter_static &&
                     (load_command_id != 0 || HBM_PCS != 32))) begin
                    path_error_q <= 1'b1;
                    load_done <= 1'b1;
                end else begin
                    rows_q <= descriptor_rows;
                    columns_q <= ADAPTER_STATIC_REUSE && load_skip_adapter_static ?
                        16'd5280 : descriptor_columns;
                    first_pc_q <= descriptor_first_pc;
                    base_address_q <= descriptor_base_address;
                    if (ADAPTER_STATIC_REUSE && load_skip_adapter_static) begin
                        for (integer pc = 0; pc < HBM_PCS; pc++) begin
                            if (POOL_LANES == 32)
                                record_count_q[pc*32 +: 32] <= 32'd3465;
                            else if (((pc - int'(descriptor_first_pc) + 32) % 32) < 8 ||
                                (((pc - int'(descriptor_first_pc) + 32) % 32) >= 16 &&
                                 ((pc - int'(descriptor_first_pc) + 32) % 32) < 24))
                                record_count_q[pc*32 +: 32] <= 32'd3520;
                            else
                                record_count_q[pc*32 +: 32] <= 32'd3410;
                        end
                    end else begin
                        record_count_q <= descriptor_record_count;
                    end
                    skip_adapter_q <= ADAPTER_STATIC_REUSE && load_skip_adapter_static;
                    request_toggle_q <= ~request_toggle_q;
                    adapter_start_q <= 1'b1;
                    path_busy_q <= 1'b1;
                    path_error_q <= 1'b0;
                end
            end

            if (done_sync_q[1] != done_seen_q) begin
                done_seen_q <= done_sync_q[1];
                if (error_sync_q[1]) begin
                    path_error_q <= 1'b1;
                    path_busy_q <= 1'b0;
                    load_done <= 1'b1;
                end
            end

            if (adapter_done) begin
                path_busy_q <= 1'b0;
                load_done <= 1'b1;
            end
            if (adapter_error) begin
                path_error_q <= 1'b1;
                if (path_busy_q) begin
                    path_busy_q <= 1'b0;
                    load_done <= 1'b1;
                end
            end
        end
    end

    always_ff @(posedge axi_clk) begin
        if (!axi_rst_n) begin
            request_sync_q <= '0;
            request_seen_q <= 1'b0;
            dma_start_q <= 1'b0;
            dma_done_toggle_q <= 1'b0;
        end else begin
            request_sync_q <= {request_sync_q[0], request_toggle_q};
            dma_start_q <= 1'b0;

            if (request_sync_q[1] != request_seen_q && !dma_busy) begin
                request_seen_q <= request_sync_q[1];
                dma_start_q <= 1'b1;
            end
            if (dma_done)
                dma_done_toggle_q <= ~dma_done_toggle_q;
        end
    end

    assign load_busy = path_busy_q;
    assign protocol_error = path_error_q || adapter_error || error_sync_q[1];

    initial begin
        if (HBM_PCS < 24 || HBM_PCS > 32 || RING_DEPTH < 2)
            $error("U280 Huginn HBM weight path expects 24 to 32 pseudo-channels");
    end
endmodule
