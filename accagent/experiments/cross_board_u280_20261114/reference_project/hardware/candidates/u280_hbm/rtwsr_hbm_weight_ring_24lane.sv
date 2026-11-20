`timescale 1ns / 1ps

// Isolated U280 HBM candidate: 24 bank-group lanes, preserving 4.5 MiB data capacity.
module rtwsr_hbm_weight_ring_24lane #(
    parameter int LANES = 24,
    parameter int DEPTH = 3072,
    parameter int ADDR_WIDTH = $clog2(DEPTH),
    parameter int COUNT_WIDTH = $clog2(DEPTH + 1)
)(
    input  logic                    clk,
    input  logic                    rst_n,
    input  logic                    in_valid,
    output logic                    in_ready,
    input  logic [LANES*512-1:0]    in_data,
    input  logic [LANES-1:0]        in_mask,
    output logic                    out_valid,
    input  logic                    out_ready,
    output logic [LANES*512-1:0]    out_data,
    output logic [LANES-1:0]        out_mask,
    output logic [COUNT_WIDTH-1:0]  occupancy
);
    logic [ADDR_WIDTH-1:0] write_pointer_q;
    logic [ADDR_WIDTH-1:0] read_pointer_q;
    logic [COUNT_WIDTH-1:0] occupancy_q;
    logic output_pending_q;
    (* ram_style = "block" *) logic [LANES-1:0] mask_memory [0:DEPTH-1];
    logic [LANES-1:0] output_mask_q;
    logic input_fire;
    logic output_fire;
    logic read_issue;
    logic output_slot_available;
    logic unread_entry_available;

    function automatic logic [ADDR_WIDTH-1:0] increment_pointer(
        input logic [ADDR_WIDTH-1:0] pointer
    );
        if (int'(pointer) == DEPTH - 1)
            return '0;
        return pointer + 1'b1;
    endfunction

    assign occupancy = occupancy_q;
    assign out_valid = output_pending_q;
    assign out_mask = output_mask_q;
    assign input_fire = in_valid && in_ready;
    assign output_fire = out_valid && out_ready;
    assign output_slot_available = !output_pending_q || output_fire;
    assign unread_entry_available = occupancy_q > (output_pending_q ? 1 : 0);
    assign read_issue = output_slot_available && unread_entry_available;
    assign in_ready = int'(occupancy_q) < DEPTH || output_fire;

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            write_pointer_q <= '0;
            read_pointer_q <= '0;
            occupancy_q <= '0;
            output_pending_q <= 1'b0;
            output_mask_q <= '0;
        end else begin
            if (input_fire) begin
                write_pointer_q <= increment_pointer(write_pointer_q);
                mask_memory[write_pointer_q] <= in_mask;
            end
            if (read_issue) begin
                read_pointer_q <= increment_pointer(read_pointer_q);
                output_pending_q <= 1'b1;
                output_mask_q <= mask_memory[read_pointer_q];
            end else if (output_fire) begin
                output_pending_q <= 1'b0;
            end

            case ({input_fire, output_fire})
                2'b10: occupancy_q <= occupancy_q + 1'b1;
                2'b01: occupancy_q <= occupancy_q - 1'b1;
                default: occupancy_q <= occupancy_q;
            endcase
        end
    end

`ifdef XILINX_XPM
    genvar lane;
    generate
        for (lane = 0; lane < LANES; lane = lane + 1) begin : gen_lane
            wire [71:0] uram_data [0:4];
            wire [71:0] bram_data [0:1];
            wire [7:0] tail_data;

            for (genvar slice = 0; slice < 5; slice = slice + 1) begin : gen_uram
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
                ) u_data (
                    .clka(clk), .ena(input_fire), .wea(input_fire),
                    .addra(write_pointer_q),
                    .dina(in_data[lane*512 + slice*72 +: 72]),
                    .injectdbiterra(1'b0), .injectsbiterra(1'b0),
                    .clkb(clk), .enb(read_issue), .addrb(read_pointer_q),
                    .rstb(1'b0), .regceb(1'b1), .doutb(uram_data[slice]),
                    .sbiterrb(), .dbiterrb(), .sleep(1'b0)
                );
            end

            for (genvar slice = 0; slice < 2; slice = slice + 1) begin : gen_bram
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
                    .MEMORY_PRIMITIVE("block"),
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
                ) u_data (
                    .clka(clk), .ena(input_fire), .wea(input_fire),
                    .addra(write_pointer_q),
                    .dina(in_data[lane*512 + 360 + slice*72 +: 72]),
                    .injectdbiterra(1'b0), .injectsbiterra(1'b0),
                    .clkb(clk), .enb(read_issue), .addrb(read_pointer_q),
                    .rstb(1'b0), .regceb(1'b1), .doutb(bram_data[slice]),
                    .sbiterrb(), .dbiterrb(), .sleep(1'b0)
                );
            end

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
            ) u_tail (
                .clka(clk), .ena(input_fire), .wea(input_fire),
                .addra(write_pointer_q),
                .dina(in_data[lane*512 + 504 +: 8]),
                .injectdbiterra(1'b0), .injectsbiterra(1'b0),
                .clkb(clk), .enb(read_issue), .addrb(read_pointer_q),
                .rstb(1'b0), .regceb(1'b1), .doutb(tail_data),
                .sbiterrb(), .dbiterrb(), .sleep(1'b0)
            );

            always_comb begin
                for (integer slice = 0; slice < 5; slice = slice + 1)
                    out_data[lane*512 + slice*72 +: 72] = uram_data[slice];
                for (integer slice = 0; slice < 2; slice = slice + 1)
                    out_data[lane*512 + 360 + slice*72 +: 72] = bram_data[slice];
                out_data[lane*512 + 504 +: 8] = tail_data;
            end
        end
    endgenerate
`else
    (* ram_style = "block" *) logic [LANES*512-1:0] data_memory [0:DEPTH-1];
    logic [LANES*512-1:0] output_data_q;

    always_ff @(posedge clk) begin
        if (input_fire)
            data_memory[write_pointer_q] <= in_data;
        if (read_issue)
            output_data_q <= data_memory[read_pointer_q];
    end

    assign out_data = output_data_q;
`endif

    initial begin
        if (LANES != 24 || DEPTH != 3072 || (2 ** ADDR_WIDTH) < DEPTH)
            $error("U280 ring prototype expects 24 lanes and depth 3072");
    end
endmodule
