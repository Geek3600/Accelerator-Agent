`timescale 1ns / 1ps

module rtwsr_rmsnorm_quant_unit #(
    parameter int VECTOR_LEN = 5280,
    parameter int LANES = 16,
    parameter int DATA_W = 16,
    parameter int QUANT_W = 8,
    parameter int FRAC_W = 12,
    parameter int MAX_VECTOR_LEN = VECTOR_LEN,
    parameter int MAX_VECTOR_COUNT = (MAX_VECTOR_LEN + LANES - 1) / LANES,
    parameter int COUNT_WIDTH = (MAX_VECTOR_COUNT <= 1) ? 1 : $clog2(MAX_VECTOR_COUNT + 1),
    parameter int VECTOR_WIDTH = LANES * DATA_W,
    parameter int QUANT_WIDTH = LANES * QUANT_W,
    parameter bit PRELOAD_TILED_INPUT = 1'b0,
    // Uses one combinational integer divide per lane for the final INT8
    // quantization.  The RMSNorm reduction, square-root, reciprocal and
    // output scaling dependencies remain unchanged.
    parameter bit PARALLEL_QUANTIZE = 1'b0
)(
    input  logic                         clk,
    input  logic                         rst_n,
    input  logic                         start,
    input  logic [15:0]                  vector_length,
    input  logic                         precomputed_sum_valid,
    input  logic [63:0]                  precomputed_sum_square,
    input  logic                         preloaded_input_valid,
    input  logic                         preload_write,
    input  logic [8:0]                   preload_tile_index,
    input  logic [1535:0]                preload_activation_q4_12,
    input  logic [1535:0]                preload_gamma_q4_12,
    output logic                         ready,
    input  logic                         in_valid,
    output logic                         in_ready,
    input  logic [VECTOR_WIDTH-1:0]       in_activation_q4_12,
    input  logic [VECTOR_WIDTH-1:0]       in_gamma_q4_12,
    input  logic                         in_last,
    output logic                         out_valid,
    input  logic                         out_ready,
    output logic [VECTOR_WIDTH-1:0]       out_normalized_q4_12,
    output logic [QUANT_WIDTH-1:0]        out_quantized_int8,
    output logic                         out_last,
    output logic [15:0]                   inv_rms_q15,
    output logic [15:0]                   activation_scale_q4_12,
    output logic                         busy,
    output logic                         done,
    output logic                         protocol_error
);
    typedef enum logic [3:0] {
        IDLE, COLLECT, COMPUTE, MEAN_DIVIDE, SQRT, DIVIDE, SCAN_READ, SCAN,
        PREPARE_READ, PREPARE, QUANTIZE, EMIT,
        NORMALIZE_FIRST, NORMALIZE_SECOND, NORMALIZE_CLAMP, SCALE
    } state_t;
    state_t state_q;
    logic [COUNT_WIDTH-1:0] collect_count_q;
    logic [COUNT_WIDTH-1:0] scan_count_q;
    logic [COUNT_WIDTH-1:0] emit_count_q;
    logic [15:0] active_vector_length_q;
    logic [COUNT_WIDTH-1:0] active_vector_count_q;
    logic [4:0] sqrt_count_q;
    logic [4:0] divide_count_q;
    logic [4:0] quant_count_q;
    logic [63:0] sum_square_q;
    logic use_precomputed_sum_q;
    logic use_preloaded_input_q;
    logic [63:0] mean_square_q;
    logic [63:0] mean_dividend_q;
    logic [16:0] mean_remainder_q;
    logic [5:0] mean_count_q;
    logic [16:0] mean_remainder_shifted;
    logic [16:0] mean_remainder_next;
    logic [63:0] mean_quotient_next;
    logic [15:0] inv_rms_q;
    logic [15:0] activation_scale_q;
    logic [15:0] scan_max_q;
    logic normalization_scan_q;
    logic signed [DATA_W+15:0] first_product_q [0:LANES-1];
    logic signed [DATA_W+15:0] second_product_q [0:LANES-1];
    logic signed [DATA_W-1:0] normalized_q [0:LANES-1];
    logic [15:0] scan_max_tree [1:2*LANES-1];
    logic [31:0] sqrt_root_q;
    logic [33:0] sqrt_remainder_q;
    logic [31:0] divide_q;
    logic [32:0] divide_remainder_q;
    logic [LANES*DATA_W-1:0] output_normalized_q;
    logic [LANES*QUANT_W-1:0] output_quantized_q;
    logic [21:0] quant_numerator_q [0:LANES-1];
    logic [16:0] quant_remainder_q [0:LANES-1];
    logic [21:0] quant_quotient_q [0:LANES-1];
    logic quant_negative_q [0:LANES-1];
    logic protocol_error_q;

    (* ram_style = "block" *) logic [VECTOR_WIDTH-1:0] activation_memory [0:MAX_VECTOR_COUNT-1];
    (* ram_style = "block" *) logic [VECTOR_WIDTH-1:0] gamma_memory [0:MAX_VECTOR_COUNT-1];
    (* ram_style = "block" *) logic [1535:0] preloaded_activation_memory [0:(MAX_VECTOR_COUNT+5)/6-1];
    (* ram_style = "block" *) logic [1535:0] preloaded_gamma_memory [0:(MAX_VECTOR_COUNT+5)/6-1];
    logic [VECTOR_WIDTH-1:0] activation_read_q;
    logic [VECTOR_WIDTH-1:0] gamma_read_q;

    logic [63:0] chunk_sum_square;
    logic [63:0] next_sum_square;
    logic [1:0] sqrt_pair;
    logic [33:0] sqrt_remainder_shifted;
    logic [33:0] sqrt_trial;
    logic [33:0] sqrt_remainder_next;
    logic [31:0] sqrt_root_next;
    logic [32:0] divide_remainder_shifted;
    logic [32:0] divide_remainder_next;
    logic [31:0] divide_q_next;
    logic [15:0] scan_chunk_max;
    logic [15:0] scan_next_max;
    logic [15:0] scan_scale_next;
    logic signed [DATA_W-1:0] prepare_normalized [0:LANES-1];
    logic [21:0] quant_numerator_next [0:LANES-1];
    logic [16:0] quant_remainder_shifted [0:LANES-1];
    logic [16:0] quant_remainder_next [0:LANES-1];
    logic [21:0] quant_quotient_next [0:LANES-1];
    logic signed [DATA_W-1:0] normalized_for_scale;
    logic [LANES*QUANT_W-1:0] parallel_quantized_next;

    always_comb begin
        integer lane;
        integer dimension;
        logic signed [DATA_W-1:0] value;
        logic signed [2*DATA_W-1:0] square_product;
        logic [15:0] absolute_value;
        logic [16:0] quant_divisor;
        chunk_sum_square = '0;
        value = '0;
        square_product = '0;
        absolute_value = '0;
        quant_divisor = {1'b0, activation_scale_q};
        if (quant_divisor == 0)
            quant_divisor = 17'd1;
        sqrt_pair = (mean_square_q >> ((31 - int'(sqrt_count_q)) * 2));
        sqrt_remainder_shifted = (sqrt_remainder_q << 2) | sqrt_pair;
        sqrt_trial = {sqrt_root_q, 2'b01};
        if (sqrt_remainder_shifted >= sqrt_trial) begin
            sqrt_remainder_next = sqrt_remainder_shifted - sqrt_trial;
            sqrt_root_next = {sqrt_root_q[30:0], 1'b1};
        end else begin
            sqrt_remainder_next = sqrt_remainder_shifted;
            sqrt_root_next = {sqrt_root_q[30:0], 1'b0};
        end
        divide_remainder_shifted = (divide_remainder_q << 1) | (divide_count_q == 0);
        if (divide_remainder_shifted >= {1'b0, sqrt_root_q}) begin
            divide_remainder_next = divide_remainder_shifted - {1'b0, sqrt_root_q};
            divide_q_next = (divide_q << 1) | 1'b1;
        end else begin
            divide_remainder_next = divide_remainder_shifted;
            divide_q_next = (divide_q << 1);
        end
        for (lane = 0; lane < LANES; lane = lane + 1) begin
            dimension = int'(collect_count_q) * LANES + lane;
            if (dimension < int'(active_vector_length_q)) begin
                value = $signed(in_activation_q4_12[lane*DATA_W +: DATA_W]);
                square_product = $signed(value) * $signed(value);
                chunk_sum_square = chunk_sum_square + square_product;
            end
        end
        next_sum_square = sum_square_q + chunk_sum_square;
        mean_remainder_shifted = {mean_remainder_q[15:0], mean_dividend_q[63]};
        mean_remainder_next = mean_remainder_shifted;
        mean_quotient_next = {mean_dividend_q[62:0], 1'b0};
        if (mean_remainder_shifted >= {1'b0, active_vector_length_q}) begin
            mean_remainder_next = mean_remainder_shifted - {1'b0, active_vector_length_q};
            mean_quotient_next[0] = 1'b1;
        end
        normalized_for_scale = '0;
        for (lane = 0; lane < LANES; lane = lane + 1) begin
            dimension = int'(scan_count_q) * LANES + lane;
            normalized_for_scale = normalized_q[lane];
            absolute_value = normalized_for_scale < 0 ? -normalized_for_scale : normalized_for_scale;
            scan_max_tree[LANES + lane] = dimension < int'(active_vector_length_q) ? absolute_value : 16'd0;
        end
        for (lane = LANES - 1; lane > 0; lane = lane - 1)
            scan_max_tree[lane] = scan_max_tree[2*lane] > scan_max_tree[2*lane+1] ?
                                  scan_max_tree[2*lane] : scan_max_tree[2*lane+1];
        scan_chunk_max = scan_max_tree[1];
        scan_next_max = (scan_chunk_max > scan_max_q) ? scan_chunk_max : scan_max_q;
        for (lane = 0; lane < LANES; lane = lane + 1) begin
            dimension = int'(emit_count_q) * LANES + lane;
            prepare_normalized[lane] = '0;
            if (dimension < int'(active_vector_length_q)) begin
                prepare_normalized[lane] = normalized_q[lane];
            end

            quant_numerator_next[lane] = {quant_numerator_q[lane][20:0], 1'b0};
            quant_remainder_shifted[lane] = {quant_remainder_q[lane][15:0], quant_numerator_q[lane][21]};
            if (quant_remainder_shifted[lane] >= quant_divisor) begin
                quant_remainder_next[lane] = quant_remainder_shifted[lane] - quant_divisor;
                quant_quotient_next[lane] = {quant_quotient_q[lane][20:0], 1'b1};
            end else begin
                quant_remainder_next[lane] = quant_remainder_shifted[lane];
                quant_quotient_next[lane] = {quant_quotient_q[lane][20:0], 1'b0};
            end
        end
        scan_scale_next = (scan_max_q < 16'd127) ? 16'd1 : scan_max_q / 16'd127;
        parallel_quantized_next = '0;
        for (lane = 0; lane < LANES; lane = lane + 1) begin
            integer parallel_input;
            integer parallel_output;
            parallel_input = int'($signed(prepare_normalized[lane]));
            if (activation_scale_q == 0)
                parallel_output = 0;
            else
                parallel_output = parallel_input / int'(activation_scale_q);
            if (parallel_output > 127)
                parallel_output = 127;
            else if (parallel_output < -128)
                parallel_output = -128;
            parallel_quantized_next[lane*QUANT_W +: QUANT_W] = QUANT_W'(parallel_output);
        end
    end

    assign ready = (state_q == IDLE);
    assign in_ready = (state_q == COLLECT);
    assign out_valid = (state_q == EMIT);
    assign out_last = out_valid && (emit_count_q == active_vector_count_q - 1'b1);
    assign out_normalized_q4_12 = output_normalized_q;
    assign out_quantized_int8 = output_quantized_q;
    assign inv_rms_q15 = inv_rms_q;
    assign activation_scale_q4_12 = activation_scale_q;
    assign busy = (state_q != IDLE);
    assign protocol_error = protocol_error_q;

    always_ff @(posedge clk) begin
        integer lane;
        integer dimension;
        integer quant_input;
        integer quant_output;
        if (!rst_n) begin
            state_q <= IDLE;
            collect_count_q <= '0;
            scan_count_q <= '0;
            emit_count_q <= '0;
            active_vector_length_q <= 16'(VECTOR_LEN);
            active_vector_count_q <= COUNT_WIDTH'((VECTOR_LEN + LANES - 1) / LANES);
            sum_square_q <= '0;
            use_precomputed_sum_q <= 1'b0;
            use_preloaded_input_q <= 1'b0;
            mean_square_q <= '0;
            mean_dividend_q <= '0;
            mean_remainder_q <= '0;
            mean_count_q <= '0;
            inv_rms_q <= '0;
            activation_scale_q <= '0;
            scan_max_q <= '0;
            normalization_scan_q <= 1'b0;
            sqrt_count_q <= '0;
            divide_count_q <= '0;
            quant_count_q <= '0;
            sqrt_root_q <= '0;
            sqrt_remainder_q <= '0;
            divide_q <= '0;
            divide_remainder_q <= '0;
            output_normalized_q <= '0;
            output_quantized_q <= '0;
            activation_read_q <= '0;
            gamma_read_q <= '0;
            for (lane = 0; lane < LANES; lane = lane + 1) begin
                first_product_q[lane] <= '0;
                second_product_q[lane] <= '0;
                normalized_q[lane] <= '0;
                quant_numerator_q[lane] <= '0;
                quant_remainder_q[lane] <= '0;
                quant_quotient_q[lane] <= '0;
                quant_negative_q[lane] <= 1'b0;
            end
            protocol_error_q <= 1'b0;
            done <= 1'b0;
        end else begin
            done <= 1'b0;
            if (PRELOAD_TILED_INPUT && preload_write) begin
                preloaded_activation_memory[preload_tile_index] <= preload_activation_q4_12;
                preloaded_gamma_memory[preload_tile_index] <= preload_gamma_q4_12;
            end
            case (state_q)
                IDLE: begin
                    if (start) begin
                        collect_count_q <= '0;
                        scan_count_q <= '0;
                        protocol_error_q <= 1'b0;
                        if (vector_length == 0 || vector_length > MAX_VECTOR_LEN) begin
                            active_vector_length_q <= 16'(VECTOR_LEN);
                            active_vector_count_q <= COUNT_WIDTH'((VECTOR_LEN + LANES - 1) / LANES);
                            protocol_error_q <= 1'b1;
                        end else begin
                            active_vector_length_q <= vector_length;
                            active_vector_count_q <= COUNT_WIDTH'((int'(vector_length) + LANES - 1) / LANES);
                        end
                        sum_square_q <= precomputed_sum_valid ? precomputed_sum_square : 64'd0;
                        use_precomputed_sum_q <= precomputed_sum_valid;
                        use_preloaded_input_q <= PRELOAD_TILED_INPUT && preloaded_input_valid;
                        scan_max_q <= '0;
                        mean_square_q <= '0;
                        output_normalized_q <= '0;
                        output_quantized_q <= '0;
                        if (PRELOAD_TILED_INPUT && preloaded_input_valid) begin
                            if (!precomputed_sum_valid)
                                protocol_error_q <= 1'b1;
                            state_q <= COMPUTE;
                        end else begin
                            state_q <= COLLECT;
                        end
                    end
                end
                COLLECT: begin
                    if (in_valid && in_ready) begin
                        activation_memory[collect_count_q] <= in_activation_q4_12;
                        gamma_memory[collect_count_q] <= in_gamma_q4_12;
                        if (!use_precomputed_sum_q)
                            sum_square_q <= next_sum_square;
                        if (collect_count_q == active_vector_count_q - 1'b1) begin
                            if (!in_last)
                                protocol_error_q <= 1'b1;
                            collect_count_q <= '0;
                            state_q <= COMPUTE;
                        end else begin
                            if (in_last)
                                protocol_error_q <= 1'b1;
                            collect_count_q <= collect_count_q + 1'b1;
                        end
                    end
                end
                COMPUTE: begin
                    mean_dividend_q <= sum_square_q;
                    mean_remainder_q <= '0;
                    mean_count_q <= '0;
                    state_q <= MEAN_DIVIDE;
                end
                MEAN_DIVIDE: begin
                    mean_dividend_q <= mean_quotient_next;
                    mean_remainder_q <= mean_remainder_next;
                    if (mean_count_q == 6'd63) begin
                        mean_square_q <= mean_quotient_next;
                        sqrt_count_q <= '0;
                        sqrt_root_q <= '0;
                        sqrt_remainder_q <= '0;
                        state_q <= SQRT;
                    end else begin
                        mean_count_q <= mean_count_q + 1'b1;
                    end
                end
                SQRT: begin
                    sqrt_root_q <= sqrt_root_next;
                    sqrt_remainder_q <= sqrt_remainder_next;
                    if (sqrt_count_q == 5'd31) begin
                        if (sqrt_root_next <= 32'd4096) begin
                            inv_rms_q <= 16'h7fff;
                            scan_count_q <= '0;
                            scan_max_q <= '0;
                            quant_count_q <= '0;
                            state_q <= SCAN_READ;
                        end else begin
                            divide_count_q <= '0;
                            divide_q <= '0;
                            divide_remainder_q <= '0;
                            state_q <= DIVIDE;
                        end
                    end else begin
                        sqrt_count_q <= sqrt_count_q + 1'b1;
                    end
                end
                DIVIDE: begin
                    divide_remainder_q <= divide_remainder_next;
                    divide_q <= divide_q_next;
                    if (divide_count_q == 5'd27) begin
                        inv_rms_q <= divide_q_next[15:0];
                        scan_count_q <= '0;
                        scan_max_q <= '0;
                        quant_count_q <= '0;
                        state_q <= SCAN_READ;
                    end else begin
                        divide_count_q <= divide_count_q + 1'b1;
                    end
                end
                SCAN_READ: begin
                    if (use_preloaded_input_q) begin
                        activation_read_q <= preloaded_activation_memory[int'(scan_count_q) / 6] >>
                            ((int'(scan_count_q) % 6) * VECTOR_WIDTH);
                        gamma_read_q <= preloaded_gamma_memory[int'(scan_count_q) / 6] >>
                            ((int'(scan_count_q) % 6) * VECTOR_WIDTH);
                    end else begin
                        activation_read_q <= activation_memory[scan_count_q];
                        gamma_read_q <= gamma_memory[scan_count_q];
                    end
                    normalization_scan_q <= 1'b1;
                    state_q <= NORMALIZE_FIRST;
                end
                SCAN: begin
                    scan_max_q <= scan_next_max;
                    if (scan_count_q == active_vector_count_q - 1'b1) begin
                        state_q <= SCALE;
                    end else begin
                        scan_count_q <= scan_count_q + 1'b1;
                        state_q <= SCAN_READ;
                    end
                end
                PREPARE_READ: begin
                    if (use_preloaded_input_q) begin
                        activation_read_q <= preloaded_activation_memory[int'(emit_count_q) / 6] >>
                            ((int'(emit_count_q) % 6) * VECTOR_WIDTH);
                        gamma_read_q <= preloaded_gamma_memory[int'(emit_count_q) / 6] >>
                            ((int'(emit_count_q) % 6) * VECTOR_WIDTH);
                    end else begin
                        activation_read_q <= activation_memory[emit_count_q];
                        gamma_read_q <= gamma_memory[emit_count_q];
                    end
                    normalization_scan_q <= 1'b0;
                    state_q <= NORMALIZE_FIRST;
                end
                NORMALIZE_FIRST: begin
                    for (lane = 0; lane < LANES; lane = lane + 1)
                        first_product_q[lane] <= $signed(activation_read_q[lane*DATA_W +: DATA_W]) *
                                                 $signed({1'b0, inv_rms_q});
                    state_q <= NORMALIZE_SECOND;
                end
                NORMALIZE_SECOND: begin
                    for (lane = 0; lane < LANES; lane = lane + 1)
                        second_product_q[lane] <= (first_product_q[lane] >>> 15) *
                                                  $signed(gamma_read_q[lane*DATA_W +: DATA_W]);
                    state_q <= NORMALIZE_CLAMP;
                end
                NORMALIZE_CLAMP: begin
                    for (lane = 0; lane < LANES; lane = lane + 1) begin
                        if ((second_product_q[lane] >>> FRAC_W) > 32767)
                            normalized_q[lane] <= 16'sd32767;
                        else if ((second_product_q[lane] >>> FRAC_W) < -32768)
                            normalized_q[lane] <= -16'sd32768;
                        else
                            normalized_q[lane] <= DATA_W'(second_product_q[lane] >>> FRAC_W);
                    end
                    state_q <= normalization_scan_q ? SCAN : PREPARE;
                end
                SCALE: begin
                    activation_scale_q <= scan_scale_next;
                    emit_count_q <= '0;
                    state_q <= PREPARE_READ;
                end
                PREPARE: begin
                    quant_count_q <= '0;
                    for (lane = 0; lane < LANES; lane = lane + 1) begin
                        quant_input = int'($signed(prepare_normalized[lane]));
                        output_normalized_q[lane*DATA_W +: DATA_W] <= prepare_normalized[lane];
                        quant_negative_q[lane] <= (quant_input < 0);
                        if (quant_input < 0)
                            quant_numerator_q[lane] <= 22'(-quant_input);
                        else
                            quant_numerator_q[lane] <= 22'(quant_input);
                        quant_remainder_q[lane] <= '0;
                        quant_quotient_q[lane] <= '0;
                    end
                    if (PARALLEL_QUANTIZE) begin
                        output_quantized_q <= parallel_quantized_next;
                        state_q <= EMIT;
                    end else begin
                        state_q <= QUANTIZE;
                    end
                end
                QUANTIZE: begin
                    for (lane = 0; lane < LANES; lane = lane + 1) begin
                        quant_numerator_q[lane] <= quant_numerator_next[lane];
                        quant_remainder_q[lane] <= quant_remainder_next[lane];
                        quant_quotient_q[lane] <= quant_quotient_next[lane];
                    end
                    if (quant_count_q == 5'd21) begin
                        for (lane = 0; lane < LANES; lane = lane + 1) begin
                            quant_output = int'(quant_quotient_next[lane]);
                            if (activation_scale_q == 0)
                                output_quantized_q[lane*QUANT_W +: QUANT_W] <= '0;
                            else if (quant_negative_q[lane]) begin
                                if (quant_output > 128)
                                    output_quantized_q[lane*QUANT_W +: QUANT_W] <= -8'sd128;
                                else
                                    output_quantized_q[lane*QUANT_W +: QUANT_W] <= 8'(-quant_output);
                            end else if (quant_output > 127)
                                output_quantized_q[lane*QUANT_W +: QUANT_W] <= 8'sd127;
                            else
                                output_quantized_q[lane*QUANT_W +: QUANT_W] <= 8'(quant_output);
                        end
                        state_q <= EMIT;
                    end else begin
                        quant_count_q <= quant_count_q + 1'b1;
                    end
                end
                EMIT: begin
                    if (out_ready) begin
                        if (emit_count_q == active_vector_count_q - 1'b1) begin
                            state_q <= IDLE;
                            use_preloaded_input_q <= 1'b0;
                            done <= 1'b1;
                        end else begin
                            emit_count_q <= emit_count_q + 1'b1;
                            state_q <= PREPARE_READ;
                        end
                    end
                end
                default: state_q <= IDLE;
            endcase
        end
    end

    initial begin
        if (VECTOR_LEN < 1 || MAX_VECTOR_LEN < VECTOR_LEN || LANES != 16 || DATA_W != 16 ||
            QUANT_W != 8 || FRAC_W != 12)
            $error("Plan 6 RMSNorm unit requires 16 lanes, Q4.12 data, and INT8 output");
    end
endmodule
