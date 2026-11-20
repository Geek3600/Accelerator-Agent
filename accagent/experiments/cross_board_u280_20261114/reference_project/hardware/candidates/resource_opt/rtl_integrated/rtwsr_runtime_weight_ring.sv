`timescale 1ns / 1ps

module rtwsr_runtime_weight_ring #(
    parameter int DEPTH = 73728,
    parameter int ADDR_WIDTH = $clog2(DEPTH),
    parameter int COUNT_WIDTH = $clog2(DEPTH + 1)
)(
    input  logic                  clk,
    input  logic                  rst_n,
    input  logic                  in_valid,
    output logic                  in_ready,
    input  logic [511:0]          in_data,
    output logic                  out_valid,
    input  logic                  out_ready,
    output logic [511:0]          out_data,
    output logic [COUNT_WIDTH-1:0] occupancy
);
    logic [ADDR_WIDTH-1:0] write_pointer_q;
    logic [ADDR_WIDTH-1:0] read_pointer_q;
    logic [COUNT_WIDTH-1:0] occupancy_q;
    logic output_pending_q;
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
    assign input_fire = in_valid && in_ready;
    assign output_fire = out_valid && out_ready;
    assign output_slot_available = !output_pending_q || output_fire;
    assign unread_entry_available = occupancy_q > (output_pending_q ? 1 : 0);
    assign read_issue = output_slot_available && unread_entry_available;
    assign in_ready = (int'(occupancy_q) < DEPTH) || output_fire;

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            write_pointer_q <= '0;
            read_pointer_q <= '0;
            occupancy_q <= '0;
            output_pending_q <= 1'b0;
        end else begin
            if (input_fire)
                write_pointer_q <= increment_pointer(write_pointer_q);
            if (read_issue)
                read_pointer_q <= increment_pointer(read_pointer_q);

            if (read_issue)
                output_pending_q <= 1'b1;
            else if (output_fire)
                output_pending_q <= 1'b0;

            case ({input_fire, output_fire})
                2'b10: occupancy_q <= occupancy_q + 1'b1;
                2'b01: occupancy_q <= occupancy_q - 1'b1;
                default: occupancy_q <= occupancy_q;
            endcase
        end
    end

`ifdef XILINX_XPM
    wire [71:0] data_lane [0:6];
    wire [7:0] data_tail;
    genvar lane;
    generate
        for (lane = 0; lane < 7; lane = lane + 1) begin : gen_uram_data
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
                .clka(clk),
                .ena(input_fire),
                .wea(input_fire),
                .addra(write_pointer_q),
                .dina(in_data[lane*72 +: 72]),
                .injectdbiterra(1'b0),
                .injectsbiterra(1'b0),
                .clkb(clk),
                .enb(read_issue),
                .addrb(read_pointer_q),
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
    ) u_data_tail (
        .clka(clk),
        .ena(input_fire),
        .wea(input_fire),
        .addra(write_pointer_q),
        .dina(in_data[511:504]),
        .injectdbiterra(1'b0),
        .injectsbiterra(1'b0),
        .clkb(clk),
        .enb(read_issue),
        .addrb(read_pointer_q),
        .rstb(1'b0),
        .regceb(1'b1),
        .doutb(data_tail),
        .sbiterrb(),
        .dbiterrb(),
        .sleep(1'b0)
    );

    always_comb begin
        for (integer lane_index = 0; lane_index < 7; lane_index = lane_index + 1)
            out_data[lane_index*72 +: 72] = data_lane[lane_index];
        out_data[511:504] = data_tail;
    end
`else
    (* ram_style = "ultra" *) logic [511:0] data_memory [0:DEPTH-1];
    logic [511:0] output_data_q;

    always_ff @(posedge clk) begin
        if (input_fire)
            data_memory[write_pointer_q] <= in_data;
        if (read_issue)
            output_data_q <= data_memory[read_pointer_q];
    end

    assign out_data = output_data_q;
`endif

    initial begin
        if (DEPTH < 2 || (2 ** ADDR_WIDTH) < DEPTH)
            $error("runtime weight-ring address width cannot cover DEPTH");
    end
endmodule
