`timescale 1ns / 1ps

module tb_uram_active_pool_bank;
    localparam int DEPTH = 4096;
    localparam int ADDR_WIDTH = $clog2(DEPTH);
    localparam int MAPPED_DEPTH = 16384;
    localparam int MAPPED_TILES = 55;
    localparam int MAPPED_WINDOWS = 70;
    localparam int MAPPED_RECORDS = MAPPED_TILES*MAPPED_WINDOWS*4;

    logic clk = 1'b0;
    logic wr_en = 1'b0;
    logic [ADDR_WIDTH-1:0] wr_addr = '0;
    logic [10:0] wr_channel = '0;
    logic [6:0] wr_window = '0;
    logic [511:0] wr_data = '0;
    logic rd_en = 1'b0;
    logic [ADDR_WIDTH-1:0] rd_addr = '0;
    logic rd_valid;
    logic [511:0] rd_data;
    logic [511:0] expected [0:DEPTH-1];
    logic mapped_wr_en = 1'b0;
    logic [10:0] mapped_wr_channel = '0;
    logic [6:0] mapped_wr_window = '0;
    logic [511:0] mapped_wr_data = '0;
    logic mapped_rd_en = 1'b0;
    logic [13:0] mapped_rd_addr = '0;
    logic mapped_rd_valid;
    logic [511:0] mapped_rd_data;
    logic [511:0] mapped_expected [0:MAPPED_RECORDS-1];
    int read_addr;

    always #5 clk = ~clk;

    uram_active_pool_bank #(
        .DEPTH(DEPTH),
        .ADDR_WIDTH(ADDR_WIDTH),
        .WR_ADDR_MODE(0)
    ) dut (.*);

    uram_active_pool_bank #(
        .DEPTH(MAPPED_DEPTH),
        .ADDR_WIDTH($clog2(MAPPED_DEPTH)),
        .WR_ADDR_MODE(1),
        .CHANNELS_PER_TILE(32),
        .WINDOW_COUNT(MAPPED_WINDOWS),
        .CHANNEL_WIDTH(11),
        .WINDOW_WIDTH(7)
    ) mapped_dut (
        .clk(clk),
        .wr_en(mapped_wr_en),
        .wr_addr('0),
        .wr_channel(mapped_wr_channel),
        .wr_window(mapped_wr_window),
        .wr_data(mapped_wr_data),
        .rd_en(mapped_rd_en),
        .rd_addr(mapped_rd_addr),
        .rd_valid(mapped_rd_valid),
        .rd_data(mapped_rd_data)
    );

    function automatic logic [511:0] make_word(input int address, input int phase);
        logic [511:0] word_value;
        logic [63:0] lane_value;
        begin
            word_value = '0;
            for (int lane = 0; lane < 8; lane++) begin
                lane_value = 64'h9e3779b97f4a7c15 * (64'(address) + 64'd1)
                           ^ 64'hd1b54a32d192ed03 * (64'(lane) + 64'd1)
                           ^ 64'hbf58476d1ce4e5b9 * (64'(phase) + 64'd1);
                word_value[lane*64 +: 64] = lane_value;
            end
            return word_value;
        end
    endfunction

    initial begin
        @(posedge clk);
        #1;
        if (rd_valid !== 1'b0)
            $fatal(1, "rd_valid must be low without a read");

        for (int address = 0; address < DEPTH; address++) begin
            @(negedge clk);
            wr_en = 1'b1;
            wr_addr = ADDR_WIDTH'(address);
            wr_data = make_word(address, 0);
            rd_en = 1'b0;
            @(posedge clk);
            #1;
            if (rd_valid !== 1'b0)
                $fatal(1, "rd_valid asserted during active-pool initialization");
            expected[address] = make_word(address, 0);
        end

        for (int address = 0; address < DEPTH; address++) begin
            read_addr = (address * 4051 + 17) % DEPTH;
            @(negedge clk);
            wr_en = 1'b1;
            wr_addr = ADDR_WIDTH'(address);
            wr_data = make_word(address, 1);
            rd_en = 1'b1;
            rd_addr = ADDR_WIDTH'(read_addr);
            @(posedge clk);
            #1;
            if (rd_valid !== 1'b1 || rd_data !== expected[read_addr])
                $fatal(1, "data mismatch at address %0d", read_addr);
            expected[address] = make_word(address, 1);
        end

        for (int address = 0; address < DEPTH; address++) begin
            @(negedge clk);
            wr_en = 1'b0;
            rd_en = 1'b1;
            rd_addr = ADDR_WIDTH'(address);
            @(posedge clk);
            #1;
            if (rd_valid !== 1'b1 || rd_data !== expected[address])
                $fatal(1, "final data mismatch at address %0d", address);
        end

        @(negedge clk);
        rd_en = 1'b0;
        @(posedge clk);
        #1;
        if (rd_valid !== 1'b0)
            $fatal(1, "rd_valid did not clear after a read bubble");

        for (int tile = 0; tile < MAPPED_TILES; tile++) begin
            for (int window_id = 0; window_id < MAPPED_WINDOWS; window_id++) begin
                for (int channel_slot = 0; channel_slot < 4; channel_slot++) begin
                    int address;
                    address = (tile*MAPPED_WINDOWS + window_id)*4 + channel_slot;
                    @(negedge clk);
                    mapped_wr_en = 1'b1;
                    mapped_wr_channel = 11'(tile*32 + channel_slot);
                    mapped_wr_window = 7'(window_id);
                    mapped_wr_data = make_word(address, 2);
                    @(posedge clk);
                    #1;
                    mapped_expected[address] = make_word(address, 2);
                end
            end
        end

        for (int address = 0; address < MAPPED_RECORDS; address++) begin
            @(negedge clk);
            mapped_wr_en = 1'b0;
            mapped_rd_en = 1'b1;
            mapped_rd_addr = 14'(address);
            @(posedge clk);
            #1;
            if (mapped_rd_valid !== 1'b1 || mapped_rd_data !== mapped_expected[address])
                $fatal(1, "mapped active-pool mismatch at address %0d", address);
        end

        $display("PASS: one active pool, all %0d linear addresses, 512-bit data, concurrent read/write, and read bubble", DEPTH);
        $display("PASS: channel/window mapping, all %0d active-pool records", MAPPED_RECORDS);
        $finish;
    end
endmodule
