`timescale 1ns / 1ps

// Candidate adapter from 24 independent HBM return lanes to 24 pool-bank writers.
module rtwsr_hbm_weight_pool_adapter_24lane #(
    parameter int LANES = 24,
    parameter int RING_DEPTH = 3072,
    parameter int ADDR_WIDTH = 14,
    parameter int COUNT_WIDTH = $clog2(RING_DEPTH + 1)
)(
    input  logic                        clk,
    input  logic                        rst_n,
    input  logic                        load_start,
    input  logic [15:0]                 load_rows,
    input  logic [15:0]                 load_columns,
    input  logic [LANES-1:0]            hbm_valid,
    output logic [LANES-1:0]            hbm_ready,
    input  logic [LANES*512-1:0]        hbm_data,
    output logic                        pool_wr_valid,
    input  logic                        pool_wr_ready,
    output logic [LANES-1:0]            pool_wr_enable,
    output logic [LANES*ADDR_WIDTH-1:0] pool_wr_address,
    output logic [LANES*512-1:0]        pool_wr_data,
    output logic [ADDR_WIDTH-1:0]       pool_wr_base_address,
    output logic [1:0]                  pool_wr_row_slot,
    output logic [6:0]                  pool_wr_window,
    output logic [8:0]                  pool_wr_tile,
    output logic [COUNT_WIDTH-1:0]      ring_occupancy,
    output logic                        load_done,
    output logic                        protocol_error
);
    logic active_q;
    logic [15:0] rows_q;
    logic [6:0] windows_q;
    logic [17:0] total_groups_q;
    logic [17:0] input_group_count_q;
    logic [17:0] output_group_count_q;
    logic [LANES-1:0] lane_valid_q;
    logic [LANES*512-1:0] lane_data_q;
    logic [LANES-1:0] lane_mask_q;
    logic [8:0] input_tile_q;
    logic [1:0] input_slot_q;
    logic [6:0] input_window_q;
    logic [8:0] output_tile_q;
    logic [1:0] output_slot_q;
    logic [6:0] output_window_q;
    logic [17:0] output_tile_base_q;
    logic [15:0] input_tile_row_base;
    logic [15:0] expected_row;
    logic ring_in_valid;
    logic ring_in_ready;
    logic ring_out_valid;
    logic ring_out_ready;
    logic [LANES*512-1:0] ring_out_data;
    logic [LANES-1:0] ring_out_mask;
    logic [31:0] requested_windows;
    logic [31:0] requested_tiles;
    logic [31:0] requested_groups;
    logic [17:0] input_group_count_after_fire;
    logic [LANES-1:0] expected_mask;
    logic input_group_fire;
    logic output_group_fire;

    assign requested_windows = (int'(load_columns) + 255) / 256;
    assign requested_tiles = (int'(load_rows) + 95) / 96;
    assign requested_groups = requested_tiles * requested_windows * 4;
    assign input_group_count_after_fire = input_group_count_q + {17'b0, input_group_fire};
    assign input_tile_row_base = ({7'b0, input_tile_q} << 6) +
        ({7'b0, input_tile_q} << 5);
    assign ring_in_valid = active_q && (&lane_valid_q);
    assign input_group_fire = ring_in_valid && ring_in_ready;
    assign hbm_ready = {LANES{active_q &&
        input_group_count_after_fire < total_groups_q}} &
        ~(lane_valid_q & {LANES{!input_group_fire}});

    always_comb begin
        for (integer lane = 0; lane < LANES; lane = lane + 1) begin
            pool_wr_address[lane*ADDR_WIDTH +: ADDR_WIDTH] = pool_wr_base_address;
            pool_wr_data[lane*512 +: 512] = ring_out_data[lane*512 +: 512];
        end
    end

    always_comb begin
        pool_wr_base_address = ADDR_WIDTH'(
            output_tile_base_q + {9'b0, output_window_q, 2'b0} +
            {16'b0, output_slot_q}
        );
        pool_wr_row_slot = output_slot_q;
        pool_wr_window = output_window_q;
        pool_wr_tile = output_tile_q;
        pool_wr_valid = active_q && ring_out_valid;
        pool_wr_enable = pool_wr_valid ? ring_out_mask : '0;
        ring_out_ready = active_q && pool_wr_ready;
        output_group_fire = ring_out_valid && ring_out_ready;
    end

    always_comb begin
        expected_mask = '0;
        for (integer lane = 0; lane < LANES; lane = lane + 1) begin
            expected_row = input_tile_row_base +
                16'((lane / 8) * 32 + (lane % 8) * 4) + {14'b0, input_slot_q};
            if (expected_row < rows_q)
                expected_mask[lane] = 1'b1;
        end
    end

    rtwsr_hbm_weight_ring_24lane #(
        .LANES(LANES), .DEPTH(RING_DEPTH), .ADDR_WIDTH($clog2(RING_DEPTH)),
        .COUNT_WIDTH(COUNT_WIDTH)
    ) u_ring (
        .clk(clk), .rst_n(rst_n),
        .in_valid(input_group_fire), .in_ready(ring_in_ready),
        .in_data(lane_data_q), .in_mask(lane_mask_q),
        .out_valid(ring_out_valid), .out_ready(ring_out_ready),
        .out_data(ring_out_data), .out_mask(ring_out_mask),
        .occupancy(ring_occupancy)
    );

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            active_q <= 1'b0;
            rows_q <= '0;
            windows_q <= '0;
            total_groups_q <= '0;
            input_group_count_q <= '0;
            output_group_count_q <= '0;
            input_tile_q <= '0;
            input_slot_q <= '0;
            input_window_q <= '0;
            output_tile_q <= '0;
            output_slot_q <= '0;
            output_window_q <= '0;
            output_tile_base_q <= '0;
            lane_valid_q <= '0;
            lane_mask_q <= '0;
            load_done <= 1'b0;
            protocol_error <= 1'b0;
        end else begin
            load_done <= 1'b0;

            if (load_start && !active_q && ring_occupancy == 0 && lane_valid_q == 0) begin
                if (load_rows == 0 || load_columns == 0 || requested_windows == 0 ||
                    requested_windows >= 128 || requested_tiles >= 512 ||
                    requested_groups == 0) begin
                    protocol_error <= 1'b1;
                    load_done <= 1'b1;
                end else begin
                    active_q <= 1'b1;
                    rows_q <= load_rows;
                    windows_q <= 7'(requested_windows);
                    total_groups_q <= 18'(requested_groups);
                    input_group_count_q <= '0;
                    output_group_count_q <= '0;
                    input_tile_q <= '0;
                    input_slot_q <= '0;
                    input_window_q <= '0;
                    output_tile_q <= '0;
                    output_slot_q <= '0;
                    output_window_q <= '0;
                    output_tile_base_q <= '0;
                    lane_valid_q <= '0;
                    protocol_error <= 1'b0;
                end
            end

            if (input_group_fire) begin
                input_group_count_q <= input_group_count_q + 1'b1;
                if (lane_mask_q != expected_mask)
                    protocol_error <= 1'b1;

                if (input_window_q + 1'b1 == windows_q) begin
                    input_window_q <= '0;
                    if (input_slot_q == 2'd3) begin
                        input_slot_q <= '0;
                        input_tile_q <= input_tile_q + 1'b1;
                    end else begin
                        input_slot_q <= input_slot_q + 1'b1;
                    end
                end else begin
                    input_window_q <= input_window_q + 1'b1;
                end
            end

            for (integer lane = 0; lane < LANES; lane = lane + 1) begin
                if (hbm_valid[lane] && hbm_ready[lane]) begin
                    lane_valid_q[lane] <= 1'b1;
                    lane_data_q[lane*512 +: 512] <= hbm_data[lane*512 +: 512];
                    lane_mask_q[lane] <= expected_mask[lane];
                end else if (input_group_fire) begin
                    lane_valid_q[lane] <= 1'b0;
                end
            end

            if (output_group_fire) begin
                if (output_window_q + 1'b1 == windows_q) begin
                    output_window_q <= '0;
                    if (output_slot_q == 2'd3) begin
                        output_slot_q <= '0;
                        output_tile_q <= output_tile_q + 1'b1;
                        output_tile_base_q <= output_tile_base_q +
                            {9'b0, windows_q, 2'b0};
                    end else begin
                        output_slot_q <= output_slot_q + 1'b1;
                    end
                end else begin
                    output_window_q <= output_window_q + 1'b1;
                end

                if (output_group_count_q + 1'b1 == total_groups_q) begin
                    output_group_count_q <= output_group_count_q + 1'b1;
                    active_q <= 1'b0;
                    load_done <= 1'b1;
                    if (input_group_count_after_fire != total_groups_q ||
                        ((lane_valid_q != 0) && !input_group_fire))
                        protocol_error <= 1'b1;
                end else begin
                    output_group_count_q <= output_group_count_q + 1'b1;
                end
            end
        end
    end

    initial begin
        if (LANES != 24 || ADDR_WIDTH < $clog2(RING_DEPTH))
            $error("U280 pool adapter expects 24 lanes and a sufficient pool address width");
    end
endmodule
