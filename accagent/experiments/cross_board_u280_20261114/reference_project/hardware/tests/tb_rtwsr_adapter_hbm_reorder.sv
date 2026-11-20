`timescale 1ns / 1ps

module tb_rtwsr_adapter_hbm_reorder #(parameter int POOL_LANES = 24);
    localparam int PCS = 32;
    localparam int GROUPS_PER_TILE = 96 / POOL_LANES;
    localparam int SEGMENTS = 55 * GROUPS_PER_TILE;
    localparam int ADAPTER_START_RECORD = 6268416;
    logic clk = 0, rst_n = 0, start = 0;
    logic [PCS-1:0] hbm_valid, hbm_ready;
    logic [PCS*512-1:0] hbm_data;
    logic pool_valid, pool_ready = 1, done, error;
    logic [POOL_LANES-1:0] pool_enable;
    logic [POOL_LANES*14-1:0] pool_address;
    logic [POOL_LANES*512-1:0] pool_data;
    logic [$clog2(PCS*64+1)-1:0] occupancy;
    integer segment [0:PCS-1];
    integer position [0:PCS-1];
    integer output_group = 0;
    integer cycle = 0;

    always #5 clk = ~clk;
    rtwsr_hbm_weight_pool_adapter_27to24 #(
        .HBM_PCS(PCS), .POOL_LANES(POOL_LANES), .FIFO_DEPTH(64), .ADAPTER_STATIC_REUSE(1'b1)
    ) dut (
        .clk(clk), .rst_n(rst_n), .load_start(start), .load_rows(16'd5280),
        .load_columns(16'd5280), .load_first_pc(5'd0), .load_skip_adapter_static(1'b1),
        .hbm_valid(hbm_valid), .hbm_ready(hbm_ready), .hbm_data(hbm_data),
        .pool_wr_valid(pool_valid), .pool_wr_ready(pool_ready), .pool_wr_enable(pool_enable),
        .pool_wr_address(pool_address), .pool_wr_data(pool_data), .ring_occupancy(occupancy),
        .load_done(done), .protocol_error(error)
    );

    function automatic integer offset(input integer pc, input integer segment_index);
        offset = (pc - (segment_index*42*POOL_LANES) % 32 + 32) % 32;
    endfunction
    function automatic integer segment_records(input integer pc, input integer segment_index);
        segment_records = (21*POOL_LANES - 1 - offset(pc, segment_index)) / 32 + 1;
    endfunction
    always_comb begin
        hbm_valid = '0;
        hbm_data = '0;
        for (integer pc = 0; pc < PCS; pc++) begin
            if (segment[pc] < SEGMENTS) begin
                hbm_valid[pc] = 1'b1;
                hbm_data[pc*512 +: 32] = 32'(ADAPTER_START_RECORD + segment[pc]*42*POOL_LANES +
                    offset(pc, segment[pc]) + position[pc]*32);
            end
        end
    end
    always @(posedge clk) begin
        integer tile, slot, window, expected_record, expected_address;
        if (rst_n) begin
            cycle++;
            for (integer pc = 0; pc < PCS; pc++) begin
                if (hbm_valid[pc] && hbm_ready[pc]) begin
                    if (position[pc] + 1 == segment_records(pc, segment[pc])) begin
                        position[pc] = 0;
                        segment[pc]++;
                    end else begin
                        position[pc]++;
                    end
                end
            end
            if (pool_valid && pool_ready) begin
                tile = output_group / (21*GROUPS_PER_TILE);
                slot = (output_group % (21*GROUPS_PER_TILE)) / 21;
                window = output_group % 21;
                expected_address = (tile*21 + window)*GROUPS_PER_TILE + slot;
                if (pool_enable != {POOL_LANES{1'b1}})
                    $fatal(1, "Adapter pool mask mismatch group=%0d", output_group);
                for (integer lane = 0; lane < POOL_LANES; lane++) begin
                    expected_record = ADAPTER_START_RECORD + (tile*GROUPS_PER_TILE*42 + slot*42 + window)*POOL_LANES + lane;
                    if (pool_address[lane*14 +: 14] != 14'(expected_address) ||
                        pool_data[lane*512 +: 32] != 32'(expected_record))
                        $fatal(1, "Adapter pool reorder group=%0d lane=%0d expected=%0d got=%0d addr=%0d expected_addr=%0d",
                            output_group, lane, expected_record, pool_data[lane*512 +: 32],
                            pool_address[lane*14 +: 14], expected_address);
                end
                output_group++;
            end
            if (error)
                $fatal(1, "Adapter reorder protocol error");
        end
    end

    initial begin
        for (integer pc = 0; pc < PCS; pc++) begin
            segment[pc] = 0;
            position[pc] = 0;
        end
        repeat (3) @(negedge clk);
        rst_n = 1;
        start = 1;
        @(negedge clk);
        start = 0;
        wait (done);
        @(negedge clk);
        if (output_group != 55*GROUPS_PER_TILE*21)
            $fatal(1, "Adapter reorder group count %0d", output_group);
        $display("PASS Adapter HBM reorder lanes=%0d groups=%0d records=110880", POOL_LANES, output_group);
        $finish;
    end
    initial begin
        #2000000;
        $fatal(1, "Adapter HBM reorder timeout group=%0d", output_group);
    end
endmodule
