`timescale 1ns / 1ps

// Round-robin HBM records feed the existing 24-bank primary-pool interface.
module rtwsr_hbm_weight_pool_adapter_27to24 #(
    parameter int HBM_PCS = 32,
    parameter bit ADAPTER_STATIC_REUSE = 1'b0,
    parameter int POOL_LANES = 24,
    parameter int FIFO_DEPTH = 73728 / HBM_PCS,
    parameter int PTR_WIDTH = $clog2(FIFO_DEPTH),
    parameter int FIFO_COUNT_WIDTH = $clog2(FIFO_DEPTH + 1),
    parameter int OCCUPANCY_WIDTH = $clog2(HBM_PCS * FIFO_DEPTH + 1),
    parameter int ADDR_WIDTH = 14,
    parameter int GROUP_COUNT_WIDTH = 18,
    parameter int INPUT_COUNT_WIDTH = 20
)(
    input  logic                                   clk,
    input  logic                                   rst_n,
    input  logic                                   load_start,
    input  logic [15:0]                            load_rows,
    input  logic [15:0]                            load_columns,
    input  logic [4:0]                             load_first_pc,
    input  logic                                   load_skip_adapter_static,
    input  logic [HBM_PCS-1:0]                     hbm_valid,
    output logic [HBM_PCS-1:0]                     hbm_ready,
    input  logic [HBM_PCS*512-1:0]                 hbm_data,
    output logic                                   pool_wr_valid,
    input  logic                                   pool_wr_ready,
    output logic [POOL_LANES-1:0]                  pool_wr_enable,
    output logic [POOL_LANES*ADDR_WIDTH-1:0]       pool_wr_address,
    output logic [POOL_LANES*512-1:0]              pool_wr_data,
    output logic [OCCUPANCY_WIDTH-1:0]             ring_occupancy,
    output logic                                   load_done,
    output logic                                   protocol_error
);
    logic active_q;
    logic output_pending_q;
    logic [15:0] rows_q;
    logic [6:0] windows_q;
    logic [8:0] output_tile_q;
    logic [1:0] output_slot_q;
    logic [6:0] output_window_q;
    logic [GROUP_COUNT_WIDTH-1:0] total_groups_q;
    logic [GROUP_COUNT_WIDTH-1:0] output_group_q;
    logic [INPUT_COUNT_WIDTH-1:0] input_count_q [0:HBM_PCS-1];
    logic [INPUT_COUNT_WIDTH-1:0] input_limit_q [0:HBM_PCS-1];
    logic [FIFO_COUNT_WIDTH-1:0] fifo_count_q [0:HBM_PCS-1];
    logic [PTR_WIDTH-1:0] write_pointer_q [0:HBM_PCS-1];
    logic [PTR_WIDTH-1:0] read_pointer_q [0:HBM_PCS-1];
    logic [PTR_WIDTH-1:0] fifo_read_address [0:HBM_PCS-1];
    logic [HBM_PCS-1:0] selected_pc;
    logic [HBM_PCS-1:0] input_fire;
    logic [HBM_PCS-1:0] output_pop;
    logic [POOL_LANES-1:0] group_available;
    logic [4:0] lane_pc_q [0:POOL_LANES-1];
    logic [4:0] issue_lane_pc [0:POOL_LANES-1];
    logic [4:0] output_lane_pc_q [0:POOL_LANES-1];
    logic [POOL_LANES-1:0] output_mask_q;
    logic [ADDR_WIDTH-1:0] output_address_q;
    logic [HBM_PCS*512-1:0] lane_memory_output;
    logic [HBM_PCS*512-1:0] lane_memory_rotated;
    logic [15:0] input_tile_row_base;
    logic [31:0] requested_windows;
    logic [31:0] requested_tiles;
    logic [31:0] requested_groups;
    localparam int GROUPS_PER_TILE = 96 / POOL_LANES;
    logic issue_read;
    logic output_fire;
    logic skip_adapter_q;

    assign requested_windows = (int'(load_columns) + 255) / 256;
    assign requested_tiles = (int'(load_rows) + 95) / 96;
    assign requested_groups = requested_tiles * requested_windows * GROUPS_PER_TILE;
    assign input_tile_row_base = ({7'b0, output_tile_q} << 6) +
                                 ({7'b0, output_tile_q} << 5);
    assign input_fire = hbm_valid & hbm_ready;
    assign pool_wr_valid = output_pending_q;

    always_comb begin
        selected_pc = '0;
        for (integer lane = 0; lane < POOL_LANES; lane = lane + 1) begin
            issue_lane_pc[lane] = lane_pc_q[lane];
            selected_pc[issue_lane_pc[lane]] = 1'b1;
        end

        output_fire = output_pending_q && pool_wr_ready;
        output_pop = '0;
        for (integer lane = 0; lane < POOL_LANES; lane = lane + 1)
            if (output_fire)
                output_pop[output_lane_pc_q[lane]] = 1'b1;

        for (integer lane = 0; lane < POOL_LANES; lane = lane + 1)
            group_available[lane] =
                int'(fifo_count_q[issue_lane_pc[lane]]) >
                int'(output_pop[issue_lane_pc[lane]]);

        issue_read = active_q && output_group_q < total_groups_q &&
                     (!output_pending_q || output_fire) && (&group_available);

        hbm_ready = '0;
        for (integer pc = 0; pc < HBM_PCS; pc = pc + 1)
            hbm_ready[pc] = active_q && input_count_q[pc] < input_limit_q[pc] &&
                (int'(fifo_count_q[pc]) < FIFO_DEPTH || output_pop[pc]);

        for (integer pc = 0; pc < HBM_PCS; pc = pc + 1) begin
            if (output_pop[pc] && int'(read_pointer_q[pc]) == FIFO_DEPTH - 1)
                fifo_read_address[pc] = '0;
            else if (output_pop[pc])
                fifo_read_address[pc] = read_pointer_q[pc] + 1'b1;
            else
                fifo_read_address[pc] = read_pointer_q[pc];
        end

        pool_wr_enable = output_pending_q ? output_mask_q : '0;
        for (integer lane = 0; lane < POOL_LANES; lane = lane + 1) begin
            pool_wr_address[lane*ADDR_WIDTH +: ADDR_WIDTH] = output_address_q;
            if (HBM_PCS == 32)
                pool_wr_data[lane*512 +: 512] = lane_memory_rotated[lane*512 +: 512];
            else
                pool_wr_data[lane*512 +: 512] = lane_memory_output[
                    output_lane_pc_q[lane]*512 +: 512];
        end

        ring_occupancy = '0;
        for (integer pc = 0; pc < HBM_PCS; pc = pc + 1)
            ring_occupancy = ring_occupancy + OCCUPANCY_WIDTH'(fifo_count_q[pc]);
    end

    generate
        if (HBM_PCS == 32) begin : gen_shared_pc_rotation
            // Lane PCs stay contiguous, so one shared 32-entry rotation serves every output lane.
            wire [32*512-1:0] rotation_stage0;
            wire [32*512-1:0] rotation_stage1;
            wire [32*512-1:0] rotation_stage2;
            wire [32*512-1:0] rotation_stage3;
            wire [32*512-1:0] rotation_stage4;
            wire [32*512-1:0] rotation_stage5;
            assign rotation_stage0 = lane_memory_output;
            for (genvar lane1 = 0; lane1 < 32; lane1 = lane1 + 1) begin : gen_rotate1
                assign rotation_stage1[lane1*512 +: 512] = output_lane_pc_q[0][0] ?
                    rotation_stage0[((lane1 + 1) % 32)*512 +: 512] : rotation_stage0[lane1*512 +: 512];
            end
            for (genvar lane2 = 0; lane2 < 32; lane2 = lane2 + 1) begin : gen_rotate2
                assign rotation_stage2[lane2*512 +: 512] = output_lane_pc_q[0][1] ?
                    rotation_stage1[((lane2 + 2) % 32)*512 +: 512] : rotation_stage1[lane2*512 +: 512];
            end
            for (genvar lane3 = 0; lane3 < 32; lane3 = lane3 + 1) begin : gen_rotate3
                assign rotation_stage3[lane3*512 +: 512] = output_lane_pc_q[0][2] ?
                    rotation_stage2[((lane3 + 4) % 32)*512 +: 512] : rotation_stage2[lane3*512 +: 512];
            end
            for (genvar lane4 = 0; lane4 < 32; lane4 = lane4 + 1) begin : gen_rotate4
                assign rotation_stage4[lane4*512 +: 512] = output_lane_pc_q[0][3] ?
                    rotation_stage3[((lane4 + 8) % 32)*512 +: 512] : rotation_stage3[lane4*512 +: 512];
            end
            for (genvar lane5 = 0; lane5 < 32; lane5 = lane5 + 1) begin : gen_rotate5
                assign rotation_stage5[lane5*512 +: 512] = output_lane_pc_q[0][4] ?
                    rotation_stage4[((lane5 + 16) % 32)*512 +: 512] : rotation_stage4[lane5*512 +: 512];
            end
            assign lane_memory_rotated = rotation_stage5;
        end else begin : gen_direct_pc_selection
            assign lane_memory_rotated = lane_memory_output;
        end
    endgenerate

    genvar pc;
    generate
        for (pc = 0; pc < HBM_PCS; pc = pc + 1) begin : gen_hbm_fifo
            logic [511:0] memory_output;
            assign lane_memory_output[pc*512 +: 512] = memory_output;

            always_ff @(posedge clk) begin
                if (!rst_n) begin
                    write_pointer_q[pc] <= '0;
                    read_pointer_q[pc] <= '0;
                    fifo_count_q[pc] <= '0;
                end else begin
                    if (input_fire[pc]) begin
                        if (int'(write_pointer_q[pc]) == FIFO_DEPTH - 1)
                            write_pointer_q[pc] <= '0;
                        else
                            write_pointer_q[pc] <= write_pointer_q[pc] + 1'b1;
                    end
                    if (output_pop[pc]) begin
                        if (int'(read_pointer_q[pc]) == FIFO_DEPTH - 1)
                            read_pointer_q[pc] <= '0;
                        else
                            read_pointer_q[pc] <= read_pointer_q[pc] + 1'b1;
                    end
                    case ({input_fire[pc], output_pop[pc]})
                        2'b10: fifo_count_q[pc] <= fifo_count_q[pc] + 1'b1;
                        2'b01: fifo_count_q[pc] <= fifo_count_q[pc] - 1'b1;
                        default: fifo_count_q[pc] <= fifo_count_q[pc];
                    endcase
                end
            end

`ifdef XILINX_XPM
            xpm_memory_sdpram #(
                .ADDR_WIDTH_A(PTR_WIDTH), .ADDR_WIDTH_B(PTR_WIDTH),
                .AUTO_SLEEP_TIME(0), .BYTE_WRITE_WIDTH_A(512), .CASCADE_HEIGHT(0),
                .CLOCKING_MODE("common_clock"), .ECC_MODE("no_ecc"),
                .MEMORY_INIT_FILE("none"), .MEMORY_INIT_PARAM("0"),
                .MEMORY_SIZE(FIFO_DEPTH * 512), .MEMORY_PRIMITIVE("ultra"),
                .MESSAGE_CONTROL(0), .READ_DATA_WIDTH_B(512), .READ_LATENCY_B(1),
                .READ_RESET_VALUE_B("0"), .SIM_ASSERT_CHK(0),
                .USE_EMBEDDED_CONSTRAINT(0), .USE_MEM_INIT(0), .WAKEUP_TIME("disable_sleep"),
                .WRITE_DATA_WIDTH_A(512), .WRITE_MODE_B("read_first")
            ) u_wide_fifo (
                .clka(clk), .ena(input_fire[pc]), .wea(input_fire[pc]),
                .addra(write_pointer_q[pc]), .dina(hbm_data[pc*512 +: 512]),
                .injectdbiterra(1'b0), .injectsbiterra(1'b0),
                .clkb(clk), .enb(issue_read && selected_pc[pc]),
                .addrb(fifo_read_address[pc]), .rstb(1'b0), .regceb(1'b1),
                .doutb(memory_output), .sbiterrb(), .dbiterrb(), .sleep(1'b0)
            );
`else
            (* ram_style = "ultra" *) logic [511:0] memory [0:FIFO_DEPTH-1];
            logic [511:0] output_data_q;
            assign memory_output = output_data_q;
            always_ff @(posedge clk) begin
                if (input_fire[pc])
                    memory[write_pointer_q[pc]] <= hbm_data[pc*512 +: 512];
                if (issue_read && selected_pc[pc])
                    output_data_q <= memory[fifo_read_address[pc]];
            end
`endif
        end
    endgenerate

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            active_q <= 1'b0;
            output_pending_q <= 1'b0;
            rows_q <= '0;
            windows_q <= '0;
            output_tile_q <= '0;
            output_slot_q <= '0;
            output_window_q <= '0;
            total_groups_q <= '0;
            output_group_q <= '0;
            output_mask_q <= '0;
            output_address_q <= '0;
            load_done <= 1'b0;
            protocol_error <= 1'b0;
            skip_adapter_q <= 1'b0;
            for (integer pc_index = 0; pc_index < HBM_PCS; pc_index = pc_index + 1) begin
                input_count_q[pc_index] <= '0;
                input_limit_q[pc_index] <= '0;
            end
            for (integer lane = 0; lane < POOL_LANES; lane = lane + 1) begin
                lane_pc_q[lane] <= 5'(lane);
                output_lane_pc_q[lane] <= 5'(lane);
            end
        end else begin
            load_done <= 1'b0;

            if (load_start && !active_q && ring_occupancy == 0 && !output_pending_q) begin
                if (load_rows == 0 || load_columns == 0 || requested_windows == 0 ||
                    requested_windows >= 128 || requested_tiles >= 512 ||
                    requested_groups == 0) begin
                    protocol_error <= 1'b1;
                    load_done <= 1'b1;
                end else begin
                    active_q <= 1'b1;
                    rows_q <= load_rows;
                    windows_q <= 7'(requested_windows);
                    output_tile_q <= '0;
                    output_slot_q <= '0;
                    output_window_q <= '0;
                    total_groups_q <= GROUP_COUNT_WIDTH'(requested_groups);
                    output_group_q <= '0;
                    protocol_error <= 1'b0;
                    skip_adapter_q <= ADAPTER_STATIC_REUSE && load_skip_adapter_static;
                    for (integer pc_index = 0; pc_index < HBM_PCS; pc_index = pc_index + 1) begin
                        input_count_q[pc_index] <= '0;
                        if (ADAPTER_STATIC_REUSE && load_skip_adapter_static) begin
                            if (POOL_LANES == 32)
                                input_limit_q[pc_index] <= INPUT_COUNT_WIDTH'(3465);
                            else if (((pc_index - int'(load_first_pc) + 32) % 32) < 8 ||
                                (((pc_index - int'(load_first_pc) + 32) % 32) >= 16 &&
                                 ((pc_index - int'(load_first_pc) + 32) % 32) < 24))
                                input_limit_q[pc_index] <= INPUT_COUNT_WIDTH'(3520);
                            else
                                input_limit_q[pc_index] <= INPUT_COUNT_WIDTH'(3410);
                        end else if (((pc_index - int'(load_first_pc) + HBM_PCS) % HBM_PCS) <
                            requested_groups * POOL_LANES)
                            input_limit_q[pc_index] <= INPUT_COUNT_WIDTH'(
                                (requested_groups * POOL_LANES - 1 -
                                 ((pc_index - int'(load_first_pc) + HBM_PCS) % HBM_PCS)) /
                                HBM_PCS + 1
                            );
                        else
                            input_limit_q[pc_index] <= '0;
                    end
                    for (integer lane = 0; lane < POOL_LANES; lane = lane + 1)
                        lane_pc_q[lane] <= 5'((int'(load_first_pc) + lane) % HBM_PCS);
                end
            end

            for (integer pc_index = 0; pc_index < HBM_PCS; pc_index = pc_index + 1) begin
                if (hbm_valid[pc_index] && hbm_ready[pc_index])
                    input_count_q[pc_index] <= input_count_q[pc_index] + 1'b1;
            end

            if (issue_read) begin
                output_pending_q <= 1'b1;
                output_group_q <= output_group_q + 1'b1;
                output_mask_q <= '0;
                output_address_q <= ADDR_WIDTH'(
                    ((int'(output_tile_q) * int'(windows_q) +
                      int'(output_window_q)) * GROUPS_PER_TILE) + int'(output_slot_q)
                );
                for (integer lane = 0; lane < POOL_LANES; lane = lane + 1) begin
                    output_lane_pc_q[lane] <= issue_lane_pc[lane];
                    if (input_tile_row_base +
                        16'(POOL_LANES == 32 ?
                            int'(output_slot_q) * POOL_LANES + lane :
                            (lane / 8) * 32 + (lane % 8) * 4 + int'(output_slot_q)) < rows_q)
                        output_mask_q[lane] <= 1'b1;
                end
            end

            if (output_fire) begin
                if (output_group_q == total_groups_q) begin
                    active_q <= 1'b0;
                    load_done <= 1'b1;
                end
                if (!issue_read)
                    output_pending_q <= 1'b0;
            end

            if (issue_read) begin
                if (output_window_q + 1'b1 == windows_q) begin
                    output_window_q <= '0;
                    if (output_slot_q + 1'b1 == 2'(GROUPS_PER_TILE)) begin
                        output_slot_q <= '0;
                        output_tile_q <= output_tile_q + 1'b1;
                    end else begin
                        output_slot_q <= output_slot_q + 1'b1;
                    end
                end else begin
                    output_window_q <= output_window_q + 1'b1;
                end
                for (integer lane = 0; lane < POOL_LANES; lane = lane + 1) begin
                    if (skip_adapter_q && output_window_q + 1'b1 == windows_q)
                        lane_pc_q[lane] <= 5'((int'(lane_pc_q[lane]) + 22 * POOL_LANES) % 32);
                    else if (int'(lane_pc_q[lane]) >= HBM_PCS - POOL_LANES)
                        lane_pc_q[lane] <= 5'(int'(lane_pc_q[lane]) -
                            (HBM_PCS - POOL_LANES));
                    else
                        lane_pc_q[lane] <= 5'(int'(lane_pc_q[lane]) + POOL_LANES);
                end
            end
        end
    end

    initial begin
        if (HBM_PCS < POOL_LANES || HBM_PCS > 32 ||
            (POOL_LANES != 24 && POOL_LANES != 32) || (96 % POOL_LANES) != 0 || FIFO_DEPTH < 2 ||
            FIFO_DEPTH > (2 ** PTR_WIDTH))
            $error("U280 HBM adapter requires 24 or 32 lanes and a FIFO depth that fits its pointer");
    end
endmodule
