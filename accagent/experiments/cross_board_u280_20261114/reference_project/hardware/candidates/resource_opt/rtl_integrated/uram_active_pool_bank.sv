`timescale 1ns / 1ps

module uram_active_pool_bank #(
    parameter int DEPTH = 16384,
    parameter int ADDR_WIDTH = $clog2(DEPTH),
    parameter int WR_ADDR_MODE = 0,
    parameter int CHANNELS_PER_TILE = 32,
    parameter int WINDOW_COUNT = 70,
    parameter int CHANNEL_WIDTH = 11,
    parameter int WINDOW_WIDTH = 7
)(
    input  logic                    clk,
    input  logic                    wr_en,
    input  logic [ADDR_WIDTH-1:0]   wr_addr,
    input  logic [CHANNEL_WIDTH-1:0] wr_channel,
    input  logic [WINDOW_WIDTH-1:0] wr_window,
    input  logic [511:0]            wr_data,
    input  logic                    rd_en,
    input  logic [ADDR_WIDTH-1:0]   rd_addr,
    output logic                    rd_valid,
    output logic [511:0]            rd_data
);
    logic [511:0] pool_data;

    function automatic logic [ADDR_WIDTH-1:0] mapped_wr_addr(
        input logic [CHANNEL_WIDTH-1:0] channel,
        input logic [WINDOW_WIDTH-1:0] window_id
    );
        mapped_wr_addr = ADDR_WIDTH'(
            (((int'(channel) / CHANNELS_PER_TILE * WINDOW_COUNT) + int'(window_id)) * 4) +
            (int'(channel) % 4)
        );
    endfunction

    always_ff @(posedge clk)
        rd_valid <= rd_en;

    initial rd_valid = 1'b0;

    assign rd_data = pool_data;

`ifdef XILINX_XPM
    wire [71:0] data_lane [0:6];
    wire [7:0] data_tail;
    genvar lane;
    generate
        for (lane = 0; lane < 7; lane = lane + 1) begin : gen_uram_lane
            xpm_memory_sdpram #(
                .ADDR_WIDTH_A(ADDR_WIDTH),
                .ADDR_WIDTH_B(ADDR_WIDTH),
                .AUTO_SLEEP_TIME(0),
                .BYTE_WRITE_WIDTH_A(72),
                .CASCADE_HEIGHT(0),
                .CLOCKING_MODE("common_clock"),
                .ECC_MODE("no_ecc"),
                .MEMORY_INIT_FILE("none"),
                .MEMORY_INIT_PARAM("0"),
                .MEMORY_SIZE(DEPTH * 72),
                .MEMORY_PRIMITIVE("ultra"),
                .MESSAGE_CONTROL(0),
                .READ_DATA_WIDTH_B(72),
                .READ_LATENCY_B(1),
                .READ_RESET_VALUE_B("0"),
                .SIM_ASSERT_CHK(0),
                .USE_EMBEDDED_CONSTRAINT(0),
                .USE_MEM_INIT(0),
                .WAKEUP_TIME("disable_sleep"),
                .WRITE_DATA_WIDTH_A(72),
                .WRITE_MODE_B("read_first")
            ) u_ram (
                .clka(clk),
                .ena(wr_en),
                .wea(wr_en),
                .addra((WR_ADDR_MODE == 0) ? wr_addr : mapped_wr_addr(wr_channel, wr_window)),
                .dina(wr_data[lane*72 +: 72]),
                .injectdbiterra(1'b0),
                .injectsbiterra(1'b0),
                .clkb(clk),
                .enb(rd_en),
                .addrb(rd_addr),
                .rstb(1'b0),
                .regceb(1'b1),
                .doutb(data_lane[lane]),
                .sbiterrb(),
                .dbiterrb(),
                .sleep(1'b0)
            );
        end
    endgenerate

    xpm_memory_sdpram #(
        .ADDR_WIDTH_A(ADDR_WIDTH),
        .ADDR_WIDTH_B(ADDR_WIDTH),
        .AUTO_SLEEP_TIME(0),
        .BYTE_WRITE_WIDTH_A(8),
        .CASCADE_HEIGHT(0),
        .CLOCKING_MODE("common_clock"),
        .ECC_MODE("no_ecc"),
        .MEMORY_INIT_FILE("none"),
        .MEMORY_INIT_PARAM("0"),
        .MEMORY_SIZE(DEPTH * 8),
        .MEMORY_PRIMITIVE("block"),
        .MESSAGE_CONTROL(0),
        .READ_DATA_WIDTH_B(8),
        .READ_LATENCY_B(1),
        .READ_RESET_VALUE_B("0"),
        .SIM_ASSERT_CHK(0),
        .USE_EMBEDDED_CONSTRAINT(0),
        .USE_MEM_INIT(0),
        .WAKEUP_TIME("disable_sleep"),
        .WRITE_DATA_WIDTH_A(8),
        .WRITE_MODE_B("read_first")
    ) u_tail_ram (
        .clka(clk),
        .ena(wr_en),
        .wea(wr_en),
        .addra((WR_ADDR_MODE == 0) ? wr_addr : mapped_wr_addr(wr_channel, wr_window)),
        .dina(wr_data[511:504]),
        .injectdbiterra(1'b0),
        .injectsbiterra(1'b0),
        .clkb(clk),
        .enb(rd_en),
        .addrb(rd_addr),
        .rstb(1'b0),
        .regceb(1'b1),
        .doutb(data_tail),
        .sbiterrb(),
        .dbiterrb(),
        .sleep(1'b0)
    );

    always_comb begin
        for (integer lane_index = 0; lane_index < 7; lane_index = lane_index + 1)
            pool_data[lane_index*72 +: 72] = data_lane[lane_index];
        pool_data[511:504] = data_tail;
    end
`else
    (* ram_style = "ultra" *) logic [511:0] memory [0:DEPTH-1];
    logic [ADDR_WIDTH-1:0] mapped_addr;

    always_comb begin
        if (WR_ADDR_MODE == 0)
            mapped_addr = wr_addr;
        else
            mapped_addr = mapped_wr_addr(wr_channel, wr_window);
    end

    always_ff @(posedge clk) begin
        if (wr_en)
            memory[mapped_addr] <= wr_data;
        if (rd_en)
            pool_data <= memory[rd_addr];
    end
`endif

    initial begin
        if (DEPTH < 2 || (2 ** ADDR_WIDTH) != DEPTH)
            $error("DEPTH must be a power of two addressed exactly by ADDR_WIDTH");
    end
endmodule
