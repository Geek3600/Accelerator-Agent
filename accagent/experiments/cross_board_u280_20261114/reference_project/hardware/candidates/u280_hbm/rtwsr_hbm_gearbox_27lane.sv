`timescale 1ns / 1ps

module rtwsr_hbm_gearbox_27lane #(
    parameter int LANES = 27,
    parameter int FIFO_DEPTH = 32,
    parameter int FIFO_COUNT_WIDTH = $clog2(FIFO_DEPTH) + 1
)(
    input  logic                         core_clk,
    input  logic                         core_rst_n,
    input  logic [LANES-1:0]             hbm_clk,
    input  logic [LANES-1:0]             hbm_rst_n,
    input  logic [LANES-1:0]             hbm_rvalid,
    output logic [LANES-1:0]             hbm_rready,
    input  logic [LANES*256-1:0]         hbm_rdata,
    output logic [LANES-1:0]             core_valid,
    input  logic [LANES-1:0]             core_ready,
    output logic [LANES*512-1:0]         core_data,
    output logic [LANES*FIFO_COUNT_WIDTH-1:0] lane_occupancy
);
    logic half_valid_q [0:LANES-1];
    logic [255:0] first_half_q [0:LANES-1];
    logic [LANES-1:0] fifo_full;
    logic [LANES-1:0] fifo_empty;
    logic [LANES-1:0] fifo_wr_busy;
    logic [LANES-1:0] fifo_rd_busy;
    logic [LANES-1:0] fifo_write;
    logic [LANES-1:0] fifo_read;

    genvar lane;
    generate
        for (lane = 0; lane < LANES; lane = lane + 1) begin : gen_lane
            logic [511:0] fifo_data_in;
            logic [511:0] fifo_data_out;
            logic [FIFO_COUNT_WIDTH-1:0] write_count;
            logic [FIFO_COUNT_WIDTH-1:0] read_count;

            assign hbm_rready[lane] = core_rst_n && hbm_rst_n[lane] && !fifo_wr_busy[lane] &&
                (!half_valid_q[lane] || !fifo_full[lane]);
            assign fifo_write[lane] = hbm_rvalid[lane] && hbm_rready[lane] &&
                half_valid_q[lane];
            assign fifo_read[lane] = core_valid[lane] && core_ready[lane];
            assign core_valid[lane] = !fifo_empty[lane] && !fifo_rd_busy[lane] && core_rst_n;
            assign core_data[lane*512 +: 512] = fifo_data_out;
            assign lane_occupancy[lane*FIFO_COUNT_WIDTH +: FIFO_COUNT_WIDTH] = read_count;
            assign fifo_data_in = {hbm_rdata[lane*256 +: 256], first_half_q[lane]};

            always_ff @(posedge hbm_clk[lane]) begin
                if (!hbm_rst_n[lane]) begin
                    half_valid_q[lane] <= 1'b0;
                    first_half_q[lane] <= '0;
                end else if (hbm_rvalid[lane] && hbm_rready[lane]) begin
                    if (half_valid_q[lane])
                        half_valid_q[lane] <= 1'b0;
                    else begin
                        first_half_q[lane] <= hbm_rdata[lane*256 +: 256];
                        half_valid_q[lane] <= 1'b1;
                    end
                end
            end

`ifdef XILINX_XPM
            xpm_fifo_async #(
                .CASCADE_HEIGHT(0),
                .CDC_SYNC_STAGES(2),
                .DOUT_RESET_VALUE("0"),
                .ECC_MODE("no_ecc"),
                .FIFO_MEMORY_TYPE("block"),
                .FIFO_READ_LATENCY(0),
                .FIFO_WRITE_DEPTH(FIFO_DEPTH),
                .FULL_RESET_VALUE(0),
                .PROG_EMPTY_THRESH(10),
                .PROG_FULL_THRESH(FIFO_DEPTH - 5),
                .RD_DATA_COUNT_WIDTH(FIFO_COUNT_WIDTH),
                .READ_DATA_WIDTH(512),
                .READ_MODE("fwft"),
                .RELATED_CLOCKS(0),
                .USE_ADV_FEATURES("0707"),
                .WAKEUP_TIME(0),
                .WRITE_DATA_WIDTH(512),
                .WR_DATA_COUNT_WIDTH(FIFO_COUNT_WIDTH)
            ) u_async_fifo (
                .rst(!core_rst_n || !hbm_rst_n[lane]),
                .wr_clk(hbm_clk[lane]),
                .wr_en(fifo_write[lane]),
                .din(fifo_data_in),
                .full(fifo_full[lane]),
                .overflow(),
                .prog_full(),
                .wr_data_count(write_count),
                .wr_ack(),
                .almost_full(),
                .wr_rst_busy(fifo_wr_busy[lane]),
                .rd_clk(core_clk),
                .rd_en(fifo_read[lane]),
                .dout(fifo_data_out),
                .empty(fifo_empty[lane]),
                .underflow(),
                .rd_data_count(read_count),
                .prog_empty(),
                .data_valid(),
                .almost_empty(),
                .rd_rst_busy(fifo_rd_busy[lane]),
                .sleep(1'b0),
                .injectsbiterr(1'b0),
                .injectdbiterr(1'b0),
                .sbiterr(),
                .dbiterr()
            );
`else
            localparam int PTR_WIDTH = $clog2(FIFO_DEPTH);
            logic [511:0] fallback_memory [0:FIFO_DEPTH-1];
            logic [PTR_WIDTH:0] wr_binary_q, wr_gray_q;
            logic [PTR_WIDTH:0] rd_binary_q, rd_gray_q;
            logic [PTR_WIDTH:0] rd_gray_sync1_q, rd_gray_sync2_q;
            logic [PTR_WIDTH:0] wr_gray_sync1_q, wr_gray_sync2_q;
            logic [PTR_WIDTH:0] wr_binary_next, wr_gray_next;
            logic [PTR_WIDTH:0] rd_binary_next, rd_gray_next;
            logic full_q, empty_q;
            logic [PTR_WIDTH:0] synced_wr_binary;

            function automatic logic [PTR_WIDTH:0] to_gray(
                input logic [PTR_WIDTH:0] binary
            );
                return (binary >> 1) ^ binary;
            endfunction

            function automatic logic [PTR_WIDTH:0] from_gray(
                input logic [PTR_WIDTH:0] gray
            );
                logic [PTR_WIDTH:0] binary;
                binary[PTR_WIDTH] = gray[PTR_WIDTH];
                for (integer bit_index = PTR_WIDTH - 1; bit_index >= 0; bit_index--)
                    binary[bit_index] = binary[bit_index+1] ^ gray[bit_index];
                return binary;
            endfunction

            assign wr_binary_next = wr_binary_q +
                {{PTR_WIDTH{1'b0}}, (fifo_write[lane] && !full_q)};
            assign wr_gray_next = to_gray(wr_binary_next);
            assign rd_binary_next = rd_binary_q +
                {{PTR_WIDTH{1'b0}}, (fifo_read[lane] && !empty_q)};
            assign rd_gray_next = to_gray(rd_binary_next);
            assign fifo_full[lane] = full_q;
            assign fifo_empty[lane] = empty_q;
            assign fifo_wr_busy[lane] = 1'b0;
            assign fifo_rd_busy[lane] = 1'b0;
            assign fifo_data_out = fallback_memory[rd_binary_q[PTR_WIDTH-1:0]];
            assign synced_wr_binary = from_gray(wr_gray_sync2_q);
            assign write_count = FIFO_COUNT_WIDTH'(wr_binary_q - from_gray(rd_gray_sync2_q));
            assign read_count = FIFO_COUNT_WIDTH'(synced_wr_binary - rd_binary_q);

            always_ff @(posedge hbm_clk[lane]) begin
                if (!hbm_rst_n[lane] || !core_rst_n) begin
                    wr_binary_q <= '0;
                    wr_gray_q <= '0;
                    rd_gray_sync1_q <= '0;
                    rd_gray_sync2_q <= '0;
                    full_q <= 1'b0;
                end else begin
                    rd_gray_sync1_q <= rd_gray_q;
                    rd_gray_sync2_q <= rd_gray_sync1_q;
                    if (fifo_write[lane] && !full_q)
                        fallback_memory[wr_binary_q[PTR_WIDTH-1:0]] <= fifo_data_in;
                    wr_binary_q <= wr_binary_next;
                    wr_gray_q <= wr_gray_next;
                    full_q <= wr_gray_next ==
                        {~rd_gray_sync2_q[PTR_WIDTH:PTR_WIDTH-1],
                         rd_gray_sync2_q[PTR_WIDTH-2:0]};
                end
            end

            always_ff @(posedge core_clk) begin
                if (!core_rst_n || !hbm_rst_n[lane]) begin
                    rd_binary_q <= '0;
                    rd_gray_q <= '0;
                    wr_gray_sync1_q <= '0;
                    wr_gray_sync2_q <= '0;
                    empty_q <= 1'b1;
                end else begin
                    wr_gray_sync1_q <= wr_gray_q;
                    wr_gray_sync2_q <= wr_gray_sync1_q;
                    rd_binary_q <= rd_binary_next;
                    rd_gray_q <= rd_gray_next;
                    empty_q <= rd_gray_next == wr_gray_sync2_q;
                end
            end
`endif
        end
    endgenerate

    initial begin
        if (LANES < 1 || FIFO_DEPTH < 16 || (FIFO_DEPTH & (FIFO_DEPTH - 1)) != 0)
            $error("U280 HBM gearbox requires a positive lane count and power-of-two FIFO depth >= 16");
    end
endmodule
