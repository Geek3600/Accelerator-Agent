`timescale 1ns / 1ps

// Streaming USW-512 ring. Input must follow contiguous tile/window/word order,
// starting at zero; output metadata is reconstructed from the FIFO sequence.
// A tile becomes visible only after its final record has been accepted.
module uram_shadow_ring #(
    parameter int DEPTH = 73728,
    parameter int TILE_SLOTS = 165,
    parameter int WINDOW_COUNT = 70,
    parameter int WORDS_PER_WINDOW = 4,
    parameter int TILE_WIDTH = (TILE_SLOTS <= 1) ? 1 : $clog2(TILE_SLOTS),
    parameter int WINDOW_WIDTH = (WINDOW_COUNT <= 1) ? 1 : $clog2(WINDOW_COUNT),
    parameter int WORD_WIDTH = (WORDS_PER_WINDOW <= 1) ? 1 : $clog2(WORDS_PER_WINDOW),
    parameter int ADDR_WIDTH = (DEPTH <= 1) ? 1 : $clog2(DEPTH)
)(
    input  logic                       clk,
    input  logic                       rst_n,

    input  logic                       push_valid,
    output logic                       push_ready,
    input  logic [TILE_WIDTH-1:0]      push_tile,
    input  logic [WINDOW_WIDTH-1:0]    push_window,
    input  logic [WORD_WIDTH-1:0]      push_word,
    input  logic                       push_tile_last,
    input  logic [511:0]               push_data,

    output logic                       out_valid,
    input  logic                       out_ready,
    output logic [TILE_WIDTH-1:0]      out_tile,
    output logic [WINDOW_WIDTH-1:0]    out_window,
    output logic [WORD_WIDTH-1:0]      out_word,
    output logic                       out_tile_last,
    output logic [511:0]               out_data,

    output logic [TILE_SLOTS-1:0]      tile_complete,
    output logic                       protocol_error,
    output logic [$clog2(DEPTH+1)-1:0] occupancy
);
    logic [ADDR_WIDTH-1:0] write_pointer_q;
    logic [ADDR_WIDTH-1:0] read_pointer_q;
    logic [$clog2(DEPTH+1)-1:0] occupancy_q;
    logic output_pending_q;
    logic [TILE_SLOTS-1:0] tile_complete_q;
    logic [TILE_WIDTH-1:0] push_tile_q;
    logic [WINDOW_WIDTH-1:0] push_window_q;
    logic [WORD_WIDTH-1:0] push_word_q;
    logic [TILE_WIDTH-1:0] pop_tile_q;
    logic [WINDOW_WIDTH-1:0] pop_window_q;
    logic [WORD_WIDTH-1:0] pop_word_q;
    logic push_metadata_valid;
    logic push_sequence_match;
    logic push_tile_last_expected;
    logic push_fire;
    logic pop_fire;
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

    always_comb begin
        push_metadata_valid = (int'(push_tile) < TILE_SLOTS) &&
                              (int'(push_window) < WINDOW_COUNT) &&
                              (int'(push_word) < WORDS_PER_WINDOW);
        push_tile_last_expected =
            (push_window_q == WINDOW_WIDTH'(WINDOW_COUNT - 1)) &&
            (push_word_q == WORD_WIDTH'(WORDS_PER_WINDOW - 1));
        push_sequence_match = push_metadata_valid && (push_tile == push_tile_q) &&
                              (push_window == push_window_q) &&
                              (push_word == push_word_q) &&
                              (push_tile_last == push_tile_last_expected);

        out_valid = output_pending_q && tile_complete_q[pop_tile_q];
        out_tile = pop_tile_q;
        out_window = pop_window_q;
        out_word = pop_word_q;
        out_tile_last = (pop_window_q == WINDOW_WIDTH'(WINDOW_COUNT - 1)) &&
                        (pop_word_q == WORD_WIDTH'(WORDS_PER_WINDOW - 1));
        occupancy = occupancy_q;
        tile_complete = tile_complete_q;
    end

    always_comb begin
        pop_fire = out_valid && out_ready;
        push_ready = push_sequence_match && !tile_complete_q[push_tile_q] &&
                     ((int'(occupancy_q) < DEPTH) || pop_fire);
        push_fire = push_valid && push_ready;
        output_slot_available = !output_pending_q || pop_fire;
        unread_entry_available = (occupancy_q > (output_pending_q ? 1 : 0));
        read_issue = output_slot_available && unread_entry_available;
    end

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            write_pointer_q <= '0;
            read_pointer_q <= '0;
            occupancy_q <= '0;
            output_pending_q <= 1'b0;
            tile_complete_q <= '0;
            push_tile_q <= '0;
            push_window_q <= '0;
            push_word_q <= '0;
            pop_tile_q <= '0;
            pop_window_q <= '0;
            pop_word_q <= '0;
            protocol_error <= 1'b0;
        end else begin
            if (push_valid && !push_sequence_match)
                protocol_error <= 1'b1;

            if (push_fire) begin
                write_pointer_q <= increment_pointer(write_pointer_q);
                if (push_tile_last) begin
                    tile_complete_q[push_tile_q] <= 1'b1;
                    push_window_q <= '0;
                    push_word_q <= '0;
                    if (push_tile_q == TILE_WIDTH'(TILE_SLOTS - 1))
                        push_tile_q <= '0;
                    else
                        push_tile_q <= push_tile_q + 1'b1;
                end else begin
                    if (push_word_q == WORD_WIDTH'(WORDS_PER_WINDOW - 1)) begin
                        push_word_q <= '0;
                        push_window_q <= push_window_q + 1'b1;
                    end else begin
                        push_word_q <= push_word_q + 1'b1;
                    end
                end
            end

            if (read_issue) begin
                read_pointer_q <= increment_pointer(read_pointer_q);
                output_pending_q <= 1'b1;
            end else if (pop_fire) begin
                output_pending_q <= 1'b0;
            end

            if (pop_fire) begin
                if (out_tile_last) begin
                    tile_complete_q[pop_tile_q] <= 1'b0;
                    pop_window_q <= '0;
                    pop_word_q <= '0;
                    if (pop_tile_q == TILE_WIDTH'(TILE_SLOTS - 1))
                        pop_tile_q <= '0;
                    else
                        pop_tile_q <= pop_tile_q + 1'b1;
                end else if (pop_word_q == WORD_WIDTH'(WORDS_PER_WINDOW - 1)) begin
                    pop_word_q <= '0;
                    pop_window_q <= pop_window_q + 1'b1;
                end else begin
                    pop_word_q <= pop_word_q + 1'b1;
                end
            end

            case ({push_fire, pop_fire})
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
                .ena(push_fire),
                .wea(push_fire),
                .addra(write_pointer_q),
                .dina(push_data[lane*72 +: 72]),
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
        .ena(push_fire),
        .wea(push_fire),
        .addra(write_pointer_q),
        .dina(push_data[511:504]),
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
        if (push_fire)
            data_memory[write_pointer_q] <= push_data;
        if (read_issue)
            output_data_q <= data_memory[read_pointer_q];
    end

    assign out_data = output_data_q;
`endif

    initial begin
        if (DEPTH < 2 || TILE_SLOTS < 1 || WINDOW_COUNT < 1 || WORDS_PER_WINDOW < 1)
            $error("ring depth and tile dimensions must be positive; DEPTH must be at least 2");
        if ((2 ** ADDR_WIDTH) < DEPTH)
            $error("ADDR_WIDTH cannot address DEPTH entries");
    end
endmodule
