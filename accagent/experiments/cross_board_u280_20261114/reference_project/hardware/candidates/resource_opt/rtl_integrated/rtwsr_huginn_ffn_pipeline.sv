`timescale 1ns / 1ps

module rtwsr_huginn_ffn_pipeline #(
    parameter int VECTOR_LEN = 17920,
    parameter int WRITE_LANES = 96,
    parameter int DATA_W = 16,
    parameter int VECTOR_LANES = 16,
    parameter int CHUNK_COUNT = (VECTOR_LEN + VECTOR_LANES - 1) / VECTOR_LANES,
    parameter int COUNT_WIDTH = $clog2(CHUNK_COUNT + 1),
    parameter int TILE_COUNT = (VECTOR_LEN + WRITE_LANES - 1) / WRITE_LANES,
    parameter int TILE_GROUPS = WRITE_LANES / VECTOR_LANES,
    parameter int WINDOW_COUNT = (VECTOR_LEN + 255) / 256,
    parameter bit STREAM_FUSED = 1'b0,
    parameter bit GEMV_STREAM_FUSED = 1'b0
)(
    input  logic                         clk,
    input  logic                         rst_n,
    input  logic                         start,
    output logic                         ready,
    output logic                         done,
    output logic                         busy,
    input  logic                         write_valid,
    input  logic [4:0]                   write_command_id,
    input  logic [15:0]                  write_row_start,
    input  logic [6:0]                   write_rows,
    input  logic [WRITE_LANES*32-1:0]    write_result_q12,
    output logic                         write_ready,
    output logic                         in_ready,
    output logic                         out_valid,
    output logic                         out_last,
    output logic [VECTOR_LANES*DATA_W-1:0] output_q4_12,
    output logic                         protocol_error,
    output logic                         activation_valid,
    input  logic [6:0]                   activation_window_index,
    output logic [2047:0]                activation_window,
    output logic [15:0]                  activation_scale_fp16
);
    localparam logic [4:0] CMD_GATE_PROJ = 5'd21;
    localparam logic [4:0] CMD_UP_PROJ = 5'd22;
    localparam int VECTOR_WIDTH = VECTOR_LANES * DATA_W;
    localparam int PRODUCT_WIDTH = VECTOR_LANES * 2 * DATA_W;
    localparam int MEMORY_BANK_WIDTH = 64;
    localparam int MEMORY_BANK_COUNT = (WRITE_LANES * DATA_W) / MEMORY_BANK_WIDTH;
    localparam int TILE_INDEX_W = (TILE_COUNT <= 1) ? 1 : $clog2(TILE_COUNT);
    localparam int WRITE_TILE_INDEX_W = $clog2(65536 / WRITE_LANES + 1);

    typedef enum logic [3:0] {
        IDLE, STREAM, DRAIN, GEMV_WAIT, GEMV_STREAM, GEMV_DRAIN,
        SCAN_PRIME, SCAN, SCALE_DIVIDE, RECIPROCAL, QUANTIZE_PRIME, QUANTIZE, COMPLETE
    } state_t;
    state_t state_q;
    logic [COUNT_WIDTH-1:0] input_chunk_q;
    logic [COUNT_WIDTH-1:0] output_chunk_q;
    logic [COUNT_WIDTH-1:0] scan_chunk_q;
    logic [COUNT_WIDTH-1:0] quantize_chunk_q;
    logic [16:0] maximum_q4_12_q;
    logic [16:0] scan_chunk_maximum;
    logic [16:0] next_maximum;
    logic [16:0] stream_chunk_maximum;
    logic [16:0] stream_next_maximum;
    logic [16:0] scale_dividend_q;
    logic [6:0] scale_remainder_q;
    logic [16:0] scale_quotient_q;
    logic [4:0] scale_iteration_q;
    logic [7:0] scale_remainder_shift;
    logic [7:0] scale_remainder_next;
    logic [16:0] scale_quotient_next;
    logic [15:0] activation_scale_q4_12_q;
    logic [2047:0] activation_window_q;
    logic [8:0] reciprocal_divisor_q;
    logic [8:0] reciprocal_remainder_q;
    logic [25:0] reciprocal_quotient_q;
    logic [25:0] reciprocal_q25_q;
    logic [4:0] reciprocal_iteration_q;
    logic [9:0] reciprocal_remainder_shift;
    logic [9:0] reciprocal_remainder_next;
    logic [25:0] reciprocal_quotient_next;
    logic [15:0] magnitude;
    logic [15:0] adjusted_magnitude;
    logic [41:0] reciprocal_product;
    logic [41:0] reciprocal_product_rounded;
    logic [WRITE_LANES*DATA_W-1:0] projection_write_data;
    logic [WRITE_LANES*DATA_W-1:0] gate_read_data_q;
    logic [WRITE_LANES*DATA_W-1:0] up_read_data_q;
    logic projection_read_enable;
    logic [TILE_INDEX_W-1:0] projection_read_address;
    logic [WRITE_TILE_INDEX_W-1:0] write_tile;
    logic [WRITE_LANES*DATA_W-1:0] gemv_up_tile_q;
    logic [2:0] gemv_group_q;
    logic [2:0] gemv_group_count_q;
    logic gemv_final_tile_q;
    logic gemv_input_last;
    logic gemv_error_q;
    logic unit_start;
    logic unit_ready;
    logic unit_in_ready;
    logic unit_out_valid;
    logic unit_out_last;
    logic [VECTOR_WIDTH-1:0] unit_output;
    logic unit_done;
    logic unit_protocol_error;
    logic [VECTOR_WIDTH-1:0] unit_gate;
    logic [VECTOR_WIDTH-1:0] unit_up;
    logic unit_in_valid;
    logic swiglu_read_enable;
    logic [COUNT_WIDTH-1:0] swiglu_read_address;
    logic [VECTOR_WIDTH-1:0] swiglu_read_data_q;
    logic [VECTOR_LANES*8-1:0] quantized_activation_chunk;
    logic [2047:0] quantized_window_next;
    (* ram_style = "block" *) logic [VECTOR_WIDTH-1:0] swiglu_memory [0:CHUNK_COUNT-1];
    (* ram_style = "distributed" *) logic [2047:0]
        activation_memory [0:WINDOW_COUNT-1];

    function automatic logic [16:0] max_abs_chunk(
        input logic [VECTOR_WIDTH-1:0] chunk
    );
        logic [16:0] lane_values [0:VECTOR_LANES-1];
        logic signed [DATA_W:0] sample;
        integer lane;
        integer stride;
        begin
            for (lane = 0; lane < VECTOR_LANES; lane = lane + 1) begin
                sample = $signed(chunk[lane*DATA_W +: DATA_W]);
                lane_values[lane] = sample < 0 ? 17'(-sample) : 17'(sample);
            end
            for (stride = 1; stride < VECTOR_LANES; stride = stride * 2) begin
                for (lane = 0; lane < VECTOR_LANES / (stride * 2); lane = lane + 1) begin
                    if (lane_values[lane + stride] > lane_values[lane])
                        lane_values[lane] = lane_values[lane + stride];
                end
            end
            max_abs_chunk = lane_values[0];
        end
    endfunction

    function automatic logic signed [DATA_W-1:0] saturate_q4_12(
        input logic signed [31:0] value
    );
        begin
            if (value > 32'sd32767)
                saturate_q4_12 = 16'sd32767;
            else if (value < -32'sd32768)
                saturate_q4_12 = -16'sd32768;
            else
                saturate_q4_12 = value[DATA_W-1:0];
        end
    endfunction

    function automatic logic [15:0] q4_12_to_fp16(input logic [15:0] value);
        integer leading_bit;
        integer bit_index;
        logic [15:0] significand;
        begin
            leading_bit = -1;
            significand = '0;
            for (bit_index = 15; bit_index >= 0; bit_index = bit_index - 1)
                if (value[bit_index] && leading_bit < 0)
                    leading_bit = bit_index;
            if (leading_bit < 0)
                q4_12_to_fp16 = 16'h0000;
            else begin
                if (leading_bit > 10)
                    significand = value >> (leading_bit - 10);
                else
                    significand = value << (10 - leading_bit);
                q4_12_to_fp16 = {1'b0, 5'(leading_bit + 3), significand[9:0]};
            end
        end
    endfunction

    always_comb begin
        unit_gate = '0;
        unit_up = '0;
        if (GEMV_STREAM_FUSED && state_q == GEMV_STREAM) begin
            unit_gate = gate_read_data_q[int'(gemv_group_q) * VECTOR_WIDTH +: VECTOR_WIDTH];
            unit_up = gemv_up_tile_q[int'(gemv_group_q) * VECTOR_WIDTH +: VECTOR_WIDTH];
        end else begin
            unit_gate = gate_read_data_q[(int'(input_chunk_q) % TILE_GROUPS) * VECTOR_WIDTH +: VECTOR_WIDTH];
            unit_up = up_read_data_q[(int'(input_chunk_q) % TILE_GROUPS) * VECTOR_WIDTH +: VECTOR_WIDTH];
        end
        ready = state_q == IDLE || state_q == COMPLETE;
        done = state_q == COMPLETE;
        busy = state_q != IDLE && state_q != COMPLETE;
        write_ready = 1'b1;
        if (GEMV_STREAM_FUSED && write_command_id == CMD_UP_PROJ)
            write_ready = state_q == GEMV_WAIT;
        in_ready = unit_in_ready;
        out_valid = unit_out_valid;
        out_last = unit_out_last;
        output_q4_12 = unit_output;
        protocol_error = unit_protocol_error || gemv_error_q;
        activation_window = '0;
        if (int'(activation_window_index) < WINDOW_COUNT)
            activation_window = activation_memory[activation_window_index];
        activation_valid = state_q == COMPLETE;
    end

    always_comb begin
        projection_write_data = '0;
        write_tile = write_row_start / 16'(WRITE_LANES);
        for (integer lane = 0; lane < WRITE_LANES; lane = lane + 1) begin
            if (int'(write_rows) > lane)
                projection_write_data[lane*DATA_W +: DATA_W] =
                    saturate_q4_12($signed(write_result_q12[lane*32 +: 32]));
        end
    end

    always_comb begin
        projection_read_enable = 1'b0;
        projection_read_address = '0;
        if ((state_q == IDLE || state_q == COMPLETE) && start) begin
            projection_read_enable = 1'b1;
        end else if (GEMV_STREAM_FUSED && state_q == GEMV_WAIT && write_valid && write_ready &&
                     write_command_id == CMD_UP_PROJ) begin
            projection_read_enable = 1'b1;
            projection_read_address = TILE_INDEX_W'(write_tile);
        end else if (state_q == STREAM && unit_in_ready && unit_in_valid &&
                     (int'(input_chunk_q) % TILE_GROUPS == TILE_GROUPS - 1) &&
                     input_chunk_q < COUNT_WIDTH'(CHUNK_COUNT - 1)) begin
            projection_read_enable = 1'b1;
            projection_read_address = TILE_INDEX_W'((input_chunk_q + 1'b1) / TILE_GROUPS);
        end
    end

    generate
        for (genvar bank = 0; bank < MEMORY_BANK_COUNT; bank = bank + 1) begin : g_projection_memory_bank
            (* ram_style = "block" *) logic [MEMORY_BANK_WIDTH-1:0]
                gate_memory [0:TILE_COUNT-1];
            (* ram_style = "block" *) logic [MEMORY_BANK_WIDTH-1:0]
                up_memory [0:TILE_COUNT-1];
            logic [MEMORY_BANK_WIDTH-1:0] gate_read_q;
            logic [MEMORY_BANK_WIDTH-1:0] up_read_q;

            assign gate_read_data_q[bank*MEMORY_BANK_WIDTH +: MEMORY_BANK_WIDTH] = gate_read_q;
            assign up_read_data_q[bank*MEMORY_BANK_WIDTH +: MEMORY_BANK_WIDTH] = up_read_q;

            always_ff @(posedge clk) begin
                if (projection_read_enable) begin
                    gate_read_q <= gate_memory[projection_read_address];
                    up_read_q <= up_memory[projection_read_address];
                end
            end

            always_ff @(posedge clk) begin
                if (rst_n && write_valid && write_ready && write_tile < TILE_COUNT) begin
                    if (write_command_id == CMD_GATE_PROJ)
                        gate_memory[write_tile[TILE_INDEX_W-1:0]] <=
                            projection_write_data[bank*MEMORY_BANK_WIDTH +: MEMORY_BANK_WIDTH];
                    else if (write_command_id == CMD_UP_PROJ)
                        up_memory[write_tile[TILE_INDEX_W-1:0]] <=
                            projection_write_data[bank*MEMORY_BANK_WIDTH +: MEMORY_BANK_WIDTH];
                end
            end
        end
    endgenerate

    always_comb begin
        swiglu_read_enable = 1'b0;
        swiglu_read_address = '0;
        case (state_q)
            SCAN_PRIME: begin
                swiglu_read_enable = 1'b1;
                swiglu_read_address = scan_chunk_q;
            end
            SCAN: begin
                if (int'(scan_chunk_q) + 1 < CHUNK_COUNT) begin
                    swiglu_read_enable = 1'b1;
                    swiglu_read_address = scan_chunk_q + 1'b1;
                end
            end
            QUANTIZE_PRIME: begin
                swiglu_read_enable = 1'b1;
                swiglu_read_address = quantize_chunk_q;
            end
            QUANTIZE: begin
                if (int'(quantize_chunk_q) + 1 < CHUNK_COUNT) begin
                    swiglu_read_enable = 1'b1;
                    swiglu_read_address = quantize_chunk_q + 1'b1;
                end
            end
            default: begin end
        endcase
    end

    always_comb begin
        reciprocal_remainder_shift = {reciprocal_remainder_q, reciprocal_iteration_q == 0};
        reciprocal_remainder_next = reciprocal_remainder_shift;
        reciprocal_quotient_next = {reciprocal_quotient_q[24:0], 1'b0};
        if (reciprocal_remainder_shift >= {1'b0, reciprocal_divisor_q}) begin
            reciprocal_remainder_next = reciprocal_remainder_shift - {1'b0, reciprocal_divisor_q};
            reciprocal_quotient_next[0] = 1'b1;
        end
    end

    always_comb begin
        scale_remainder_shift = {scale_remainder_q, scale_dividend_q[16]};
        scale_remainder_next = scale_remainder_shift;
        scale_quotient_next = {scale_quotient_q[15:0], 1'b0};
        if (scale_remainder_shift >= 8'd127) begin
            scale_remainder_next = scale_remainder_shift - 8'd127;
            scale_quotient_next[0] = 1'b1;
        end
        scan_chunk_maximum = max_abs_chunk(swiglu_read_data_q);
        next_maximum = maximum_q4_12_q;
        if (scan_chunk_maximum > next_maximum)
            next_maximum = scan_chunk_maximum;
        stream_chunk_maximum = max_abs_chunk(unit_output);
        stream_next_maximum = maximum_q4_12_q;
        if (stream_chunk_maximum > stream_next_maximum)
            stream_next_maximum = stream_chunk_maximum;
    end

    always_comb begin
        logic [15:0] current_word;
        integer quantized_value;
        quantized_activation_chunk = '0;
        magnitude = '0;
        adjusted_magnitude = '0;
        reciprocal_product = '0;
        reciprocal_product_rounded = '0;
        current_word = '0;
        quantized_value = 0;
        for (integer lane = 0; lane < VECTOR_LANES; lane = lane + 1) begin
            current_word = swiglu_read_data_q[lane*DATA_W +: DATA_W];
            magnitude = current_word[DATA_W-1] ? -$signed(current_word) : current_word;
            adjusted_magnitude = magnitude + (reciprocal_divisor_q >> 1);
            reciprocal_product = {26'd0, adjusted_magnitude} * {16'd0, reciprocal_q25_q};
            reciprocal_product_rounded = reciprocal_product;
            quantized_value = int'(reciprocal_product_rounded >> 25);
            if (quantized_value > 127)
                quantized_value = 127;
            if (current_word[DATA_W-1])
                quantized_value = -quantized_value;
            quantized_activation_chunk[lane*8 +: 8] = 8'(quantized_value);
        end

        quantized_window_next = activation_window_q;
        quantized_window_next[(int'(quantize_chunk_q) % 16) * 128 +: 128] =
            quantized_activation_chunk;
    end

    always_ff @(posedge clk) begin
        if (swiglu_read_enable)
            swiglu_read_data_q <= swiglu_memory[swiglu_read_address];
    end

    always_ff @(posedge clk) begin
        if (rst_n &&
            ((state_q == STREAM || state_q == DRAIN) ||
             (GEMV_STREAM_FUSED &&
              (state_q == GEMV_WAIT || state_q == GEMV_STREAM || state_q == GEMV_DRAIN))) &&
            unit_out_valid)
            swiglu_memory[output_chunk_q] <= unit_output;
    end

    assign unit_start = start && ready;
    assign unit_in_valid = GEMV_STREAM_FUSED ? (state_q == GEMV_STREAM) : (state_q == STREAM);
    assign gemv_input_last = GEMV_STREAM_FUSED && state_q == GEMV_STREAM && gemv_final_tile_q &&
                             (gemv_group_q + 1'b1 == gemv_group_count_q);

    rtwsr_swiglu_residual_unit #(
        .VECTOR_LEN(VECTOR_LEN),
        .LANES(VECTOR_LANES),
        .DATA_W(DATA_W),
        .SCALE_W(16),
        .STREAM_FUSED(STREAM_FUSED)
    ) u_swiglu (
        .clk(clk),
        .rst_n(rst_n),
        .start(unit_start),
        .in_valid(unit_in_valid),
        .in_ready(unit_in_ready),
        .gate_q4_12(unit_gate),
        .up_q4_12(unit_up),
        .residual_q4_12('0),
        .in_last(GEMV_STREAM_FUSED ? gemv_input_last :
                 (input_chunk_q == COUNT_WIDTH'(CHUNK_COUNT - 1))),
        .residual_rate_q15(16'h8000),
        .ready(unit_ready),
        .out_valid(unit_out_valid),
        .out_ready(1'b1),
        .output_q4_12(unit_output),
        .out_last(unit_out_last),
        .busy(),
        .done(unit_done),
        .protocol_error(unit_protocol_error)
    );

    always_ff @(posedge clk) begin
        integer scale_value;
        integer active_groups;
        if (!rst_n) begin
            state_q <= IDLE;
            input_chunk_q <= '0;
            output_chunk_q <= '0;
            gemv_up_tile_q <= '0;
            gemv_group_q <= '0;
            gemv_group_count_q <= '0;
            gemv_final_tile_q <= 1'b0;
            gemv_error_q <= 1'b0;
            scan_chunk_q <= '0;
            quantize_chunk_q <= '0;
            maximum_q4_12_q <= '0;
            scale_dividend_q <= '0;
            scale_remainder_q <= '0;
            scale_quotient_q <= '0;
            scale_iteration_q <= '0;
            activation_scale_q4_12_q <= '0;
            activation_scale_fp16 <= '0;
            reciprocal_divisor_q <= '0;
            reciprocal_remainder_q <= '0;
            reciprocal_quotient_q <= '0;
            reciprocal_q25_q <= '0;
            reciprocal_iteration_q <= '0;
        end else begin
            case (state_q)
                IDLE, COMPLETE: begin
                    if (start) begin
                        input_chunk_q <= '0;
                        output_chunk_q <= '0;
                        scan_chunk_q <= '0;
                        quantize_chunk_q <= '0;
                        maximum_q4_12_q <= '0;
                        scale_dividend_q <= '0;
                        scale_remainder_q <= '0;
                        scale_quotient_q <= '0;
                        scale_iteration_q <= '0;
                        activation_scale_q4_12_q <= '0;
                        activation_scale_fp16 <= '0;
                        activation_window_q <= '0;
                        reciprocal_divisor_q <= '0;
                        reciprocal_remainder_q <= '0;
                        reciprocal_quotient_q <= '0;
                        reciprocal_q25_q <= '0;
                        reciprocal_iteration_q <= '0;
                        if (GEMV_STREAM_FUSED) begin
                            gemv_group_q <= '0;
                            gemv_group_count_q <= '0;
                            gemv_final_tile_q <= 1'b0;
                            gemv_error_q <= 1'b0;
                            state_q <= GEMV_WAIT;
                        end else begin
                            state_q <= STREAM;
                        end
                    end
                end
                STREAM: begin
                    if (unit_in_valid && unit_in_ready) begin
                        if (input_chunk_q == COUNT_WIDTH'(CHUNK_COUNT - 1)) begin
                            state_q <= DRAIN;
                        end else begin
                            input_chunk_q <= input_chunk_q + 1'b1;
                        end
                    end
                end
                DRAIN: begin end
                GEMV_WAIT: begin
                    if (write_valid && write_ready && write_command_id == CMD_UP_PROJ) begin
                        active_groups = (int'(write_rows) + VECTOR_LANES - 1) / VECTOR_LANES;
                        if (active_groups == 0 || int'(write_tile) >= TILE_COUNT) begin
                            gemv_error_q <= 1'b1;
                            state_q <= COMPLETE;
                        end else begin
                            gemv_up_tile_q <= projection_write_data;
                            gemv_group_q <= '0;
                            gemv_group_count_q <= 3'(active_groups);
                            gemv_final_tile_q <= int'(write_row_start) + int'(write_rows) >= VECTOR_LEN;
                            state_q <= GEMV_STREAM;
                        end
                    end
                end
                GEMV_STREAM: begin
                    if (unit_in_valid && unit_in_ready) begin
                        if (gemv_group_q + 1'b1 >= gemv_group_count_q) begin
                            if (gemv_final_tile_q)
                                state_q <= GEMV_DRAIN;
                            else
                                state_q <= GEMV_WAIT;
                        end else begin
                            gemv_group_q <= gemv_group_q + 1'b1;
                        end
                    end
                end
                GEMV_DRAIN: begin end
                SCAN_PRIME: state_q <= SCAN;
                SCAN: begin
                    maximum_q4_12_q <= next_maximum;
                    if (scan_chunk_q == COUNT_WIDTH'(CHUNK_COUNT - 1)) begin
                        scale_dividend_q <= next_maximum;
                        scale_remainder_q <= '0;
                        scale_quotient_q <= '0;
                        scale_iteration_q <= '0;
                        state_q <= SCALE_DIVIDE;
                    end else begin
                        scan_chunk_q <= scan_chunk_q + 1'b1;
                    end
                end
                SCALE_DIVIDE: begin
                    scale_dividend_q <= {scale_dividend_q[15:0], 1'b0};
                    scale_remainder_q <= scale_remainder_next[6:0];
                    scale_quotient_q <= scale_quotient_next;
                    if (scale_iteration_q == 5'd16) begin
                        scale_value = int'(scale_quotient_next) +
                                      int'(scale_remainder_next != 0);
                        if (scale_value < 1)
                            scale_value = 1;
                        activation_scale_q4_12_q <= 16'(scale_value);
                        reciprocal_divisor_q <= 9'(scale_value);
                        reciprocal_remainder_q <= '0;
                        reciprocal_quotient_q <= '0;
                        reciprocal_iteration_q <= '0;
                        quantize_chunk_q <= '0;
                        state_q <= RECIPROCAL;
                    end else begin
                        scale_iteration_q <= scale_iteration_q + 1'b1;
                    end
                end
                RECIPROCAL: begin
                    reciprocal_remainder_q <= reciprocal_remainder_next[8:0];
                    reciprocal_quotient_q <= reciprocal_quotient_next;
                    if (reciprocal_iteration_q == 5'd25) begin
                        reciprocal_q25_q <= reciprocal_quotient_next +
                            (reciprocal_remainder_next != 0);
                        state_q <= QUANTIZE_PRIME;
                    end else begin
                        reciprocal_iteration_q <= reciprocal_iteration_q + 1'b1;
                    end
                end
                QUANTIZE_PRIME: state_q <= QUANTIZE;
                QUANTIZE: begin
                    activation_window_q <= quantized_window_next;
                    if ((int'(quantize_chunk_q) % 16) == 15 ||
                        quantize_chunk_q == COUNT_WIDTH'(CHUNK_COUNT - 1)) begin
                        activation_memory[int'(quantize_chunk_q) / 16] <= quantized_window_next;
                        activation_window_q <= '0;
                    end
                    if (quantize_chunk_q == COUNT_WIDTH'(CHUNK_COUNT - 1)) begin
                        activation_scale_fp16 <= q4_12_to_fp16(activation_scale_q4_12_q);
                        state_q <= COMPLETE;
                    end else begin
                        quantize_chunk_q <= quantize_chunk_q + 1'b1;
                    end
                end
                default: state_q <= IDLE;
            endcase

            if (((state_q == STREAM || state_q == DRAIN) ||
                 (GEMV_STREAM_FUSED &&
                  (state_q == GEMV_WAIT || state_q == GEMV_STREAM || state_q == GEMV_DRAIN))) &&
                unit_out_valid) begin
                if (STREAM_FUSED)
                    maximum_q4_12_q <= stream_next_maximum;
                if (unit_out_last) begin
                    if (STREAM_FUSED) begin
                        scale_dividend_q <= stream_next_maximum;
                        scale_remainder_q <= '0;
                        scale_quotient_q <= '0;
                        scale_iteration_q <= '0;
                        state_q <= SCALE_DIVIDE;
                    end else begin
                        scan_chunk_q <= '0;
                        maximum_q4_12_q <= '0;
                        state_q <= SCAN_PRIME;
                    end
                end else begin
                    output_chunk_q <= output_chunk_q + 1'b1;
                end
            end
        end
    end

    initial begin
        if (VECTOR_LEN != 17920 || WRITE_LANES != 96 || DATA_W != 16 || VECTOR_LANES != 16 ||
            (WRITE_LANES * DATA_W) % MEMORY_BANK_WIDTH != 0)
            $error("Huginn FFN pipeline requires Plan 6 production dimensions");
    end
endmodule
