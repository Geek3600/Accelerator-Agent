`timescale 1ns / 1ps

module rtwsr_swiglu_residual_unit #(
    parameter int VECTOR_LEN = 17920,
    parameter int LANES = 16,
    parameter int DATA_W = 16,
    parameter int SCALE_W = 16,
    parameter int COUNT_WIDTH = $clog2((VECTOR_LEN + LANES - 1) / LANES + 1),
    parameter int VECTOR_WIDTH = LANES * DATA_W,
    parameter int PRODUCT_WIDTH = LANES * 2 * DATA_W,
    // Three registered stages share the same valid/ready stream.
    parameter bit STREAM_FUSED = 1'b0
)(
    input  logic                         clk,
    input  logic                         rst_n,
    input  logic                         start,
    input  logic                         in_valid,
    output logic                         in_ready,
    input  logic [VECTOR_WIDTH-1:0]      gate_q4_12,
    input  logic [VECTOR_WIDTH-1:0]      up_q4_12,
    input  logic [VECTOR_WIDTH-1:0]      residual_q4_12,
    input  logic                         in_last,
    input  logic [SCALE_W-1:0]           residual_rate_q15,
    output logic                         ready,
    output logic                         out_valid,
    input  logic                         out_ready,
    output logic [VECTOR_WIDTH-1:0]      output_q4_12,
    output logic                         out_last,
    output logic                         busy,
    output logic                         done,
    output logic                         protocol_error
);
    localparam int VECTOR_COUNT = (VECTOR_LEN + LANES - 1) / LANES;
    localparam logic [0:32][15:0] SIGMOID_LUT = {
        16'd11, 16'd18, 16'd30, 16'd49, 16'd81, 16'd133, 16'd219, 16'd360,
        16'd589, 16'd961, 16'd1554, 16'd2486, 16'd3906, 16'd5978, 16'd8813,
        16'd12371, 16'd16384, 16'd20397, 16'd23955, 16'd26790, 16'd28862,
        16'd30282, 16'd31214, 16'd31807, 16'd32179, 16'd32408, 16'd32549,
        16'd32635, 16'd32687, 16'd32719, 16'd32738, 16'd32750, 16'd32757
    };

    typedef enum logic [2:0] {IDLE, COLLECT, ACTIVATE, MULTIPLY, UPDATE, OUTPUT} state_t;
    state_t state_q;
    logic [COUNT_WIDTH-1:0] chunk_count_q;
    logic [SCALE_W-1:0] residual_rate_q;
    logic [VECTOR_WIDTH-1:0] gate_q;
    logic [VECTOR_WIDTH-1:0] up_q;
    logic [VECTOR_WIDTH-1:0] residual_q;
    logic [VECTOR_WIDTH-1:0] activated_q;
    logic [PRODUCT_WIDTH-1:0] product_q;
    logic [VECTOR_WIDTH-1:0] output_q;
    logic [VECTOR_WIDTH-1:0] activated_next;
    logic [PRODUCT_WIDTH-1:0] product_next;
    logic [VECTOR_WIDTH-1:0] output_next;
    logic input_last_q;
    logic output_last_q;
    logic protocol_error_q;

    function automatic logic [15:0] sigmoid_q15(input logic signed [DATA_W-1:0] value_q4_12);
        logic [16:0] shifted;
        logic [5:0] index;
        logic [10:0] fraction;
        logic [15:0] delta;
        logic [26:0] fraction_extended;
        logic [26:0] slope_product;
        logic [15:0] interpolated;
        begin
            shifted = {value_q4_12[DATA_W-1], value_q4_12} + 17'd32768;
            if (shifted == 17'd0)
                sigmoid_q15 = SIGMOID_LUT[0];
            else if (shifted >= 17'd65536)
                sigmoid_q15 = SIGMOID_LUT[32];
            else begin
                index = shifted[15:11];
                fraction = shifted[10:0];
                delta = SIGMOID_LUT[index + 6'd1] - SIGMOID_LUT[index];
                fraction_extended = {16'd0, fraction};
                slope_product = delta * fraction_extended;
                interpolated = SIGMOID_LUT[index] + slope_product[26:11];
                sigmoid_q15 = interpolated;
            end
        end
    endfunction

    function automatic logic signed [DATA_W-1:0] silu_q4_12(
        input logic signed [DATA_W-1:0] value_q4_12
    );
        logic [15:0] sigmoid;
        logic signed [DATA_W+15:0] product;
        logic signed [DATA_W+15:0] scaled;
        begin
            sigmoid = sigmoid_q15(value_q4_12);
            product = value_q4_12 * $signed({1'b0, sigmoid});
            scaled = product >>> 15;
            if (scaled > 32767)
                silu_q4_12 = 16'sd32767;
            else if (scaled < -32768)
                silu_q4_12 = -16'sd32768;
            else
                silu_q4_12 = scaled[DATA_W-1:0];
        end
    endfunction

    always_comb begin
        integer lane;
        integer dimension;
        logic signed [DATA_W-1:0] gate_value;
        logic signed [DATA_W-1:0] up_value;
        logic signed [DATA_W-1:0] activated_value;
        logic signed [2*DATA_W-1:0] product_value;
        logic signed [2*DATA_W+SCALE_W:0] update_product;
        logic signed [2*DATA_W+SCALE_W:0] scaled_update;
        logic signed [2*DATA_W+SCALE_W:0] sum_value;

        activated_next = activated_q;
        product_next = product_q;
        output_next = output_q;
        gate_value = '0;
        up_value = '0;
        activated_value = '0;
        product_value = '0;
        update_product = '0;
        scaled_update = '0;
        sum_value = '0;
        for (lane = 0; lane < LANES; lane = lane + 1) begin
            dimension = int'(chunk_count_q) * LANES + lane;
            if (dimension < VECTOR_LEN) begin
                case (state_q)
                    ACTIVATE: begin
                        gate_value = $signed(gate_q[lane*DATA_W +: DATA_W]);
                        activated_next[lane*DATA_W +: DATA_W] = silu_q4_12(gate_value);
                    end
                    MULTIPLY: begin
                        activated_value = $signed(activated_q[lane*DATA_W +: DATA_W]);
                        up_value = $signed(up_q[lane*DATA_W +: DATA_W]);
                        product_value = activated_value * up_value;
                        product_next[lane*2*DATA_W +: 2*DATA_W] = product_value;
                    end
                    UPDATE: begin
                        product_value = $signed(product_q[lane*2*DATA_W +: 2*DATA_W]);
                        update_product = product_value * $signed({1'b0, residual_rate_q});
                        scaled_update = update_product >>> ((DATA_W - 4) + (SCALE_W - 1));
                        sum_value = $signed(residual_q[lane*DATA_W +: DATA_W]) + scaled_update;
                        if (sum_value > 32767)
                            output_next[lane*DATA_W +: DATA_W] = 16'sd32767;
                        else if (sum_value < -32768)
                            output_next[lane*DATA_W +: DATA_W] = -16'sd32768;
                        else
                            output_next[lane*DATA_W +: DATA_W] = sum_value[DATA_W-1:0];
                    end
                    default: begin end
                endcase

            end
        end
    end

    generate if (STREAM_FUSED) begin : g_stream_fused
        logic active_q, input_complete_q;
        logic [2:0] valid_q, last_q;
        logic [COUNT_WIDTH-1:0] input_count_q;
        logic [15:0] rate_q;
        logic error_q;
        logic advance;
        logic [VECTOR_WIDTH-1:0] activated_input;
        logic [VECTOR_WIDTH-1:0] activated_pipe_q, up_pipe_q;
        logic [VECTOR_WIDTH-1:0] residual_first_q, residual_second_q;
        logic [PRODUCT_WIDTH-1:0] product_pipe_q;
        logic [VECTOR_WIDTH-1:0] result_pipe_q;

        assign advance = !valid_q[2] || out_ready;
        assign ready = !active_q;
        assign in_ready = active_q && !input_complete_q && advance;
        assign out_valid = valid_q[2];
        assign output_q4_12 = result_pipe_q;
        assign out_last = valid_q[2] && last_q[2];
        assign busy = active_q;
        assign protocol_error = error_q;

        always_comb begin
            integer lane;
            integer dimension;
            activated_input = '0;
            for (lane = 0; lane < LANES; lane = lane + 1) begin
                dimension = int'(input_count_q) * LANES + lane;
                if (dimension < VECTOR_LEN)
                    activated_input[lane*DATA_W +: DATA_W] =
                        silu_q4_12($signed(gate_q4_12[lane*DATA_W +: DATA_W]));
            end
        end

        always_ff @(posedge clk) begin
            integer lane;
            integer dimension;
            logic signed [2*DATA_W-1:0] product;
            logic signed [2*DATA_W+SCALE_W:0] update;
            logic signed [2*DATA_W+SCALE_W:0] sum;
            if (!rst_n) begin
                active_q <= 1'b0;
                input_complete_q <= 1'b0;
                valid_q <= '0;
                last_q <= '0;
                input_count_q <= '0;
                rate_q <= '0;
                error_q <= 1'b0;
                done <= 1'b0;
            end else begin
                done <= 1'b0;
                if (start && ready) begin
                    active_q <= 1'b1;
                    input_complete_q <= 1'b0;
                    input_count_q <= '0;
                    rate_q <= residual_rate_q15;
                    error_q <= 1'b0;
                end
                if (advance) begin
                    valid_q <= {valid_q[1:0], in_valid && in_ready};
                    last_q <= {last_q[1:0], in_last};
                    if (in_valid && in_ready) begin
                        activated_pipe_q <= activated_input;
                        up_pipe_q <= up_q4_12;
                        residual_first_q <= residual_q4_12;
                        if (in_last != (input_count_q == COUNT_WIDTH'(VECTOR_COUNT - 1)))
                            error_q <= 1'b1;
                        input_complete_q <= in_last;
                        input_count_q <= input_count_q + 1'b1;
                    end
                    if (valid_q[0]) begin
                        for (lane = 0; lane < LANES; lane = lane + 1)
                            product_pipe_q[lane*2*DATA_W +: 2*DATA_W] <=
                                $signed(activated_pipe_q[lane*DATA_W +: DATA_W]) *
                                $signed(up_pipe_q[lane*DATA_W +: DATA_W]);
                        residual_second_q <= residual_first_q;
                    end
                    if (valid_q[1]) begin
                        for (lane = 0; lane < LANES; lane = lane + 1) begin
                            product = $signed(product_pipe_q[lane*2*DATA_W +: 2*DATA_W]);
                            update = product * $signed({1'b0, rate_q});
                            sum = $signed(residual_second_q[lane*DATA_W +: DATA_W]) +
                                (update >>> ((DATA_W - 4) + (SCALE_W - 1)));
                            if (sum > 32767)
                                result_pipe_q[lane*DATA_W +: DATA_W] <= 16'sd32767;
                            else if (sum < -32768)
                                result_pipe_q[lane*DATA_W +: DATA_W] <= -16'sd32768;
                            else
                                result_pipe_q[lane*DATA_W +: DATA_W] <= sum[DATA_W-1:0];
                        end
                    end
                end
                if (out_valid && out_ready && out_last) begin
                    active_q <= 1'b0;
                    done <= 1'b1;
                end
            end
        end
    end else begin : g_serial
    assign ready = (state_q == IDLE);
    assign in_ready = (state_q == COLLECT);
    assign out_valid = (state_q == OUTPUT);
    assign output_q4_12 = output_q;
    assign out_last = out_valid && output_last_q;
    assign busy = (state_q != IDLE);
    assign protocol_error = protocol_error_q;

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            state_q <= IDLE;
            chunk_count_q <= '0;
            residual_rate_q <= '0;
            input_last_q <= 1'b0;
            output_last_q <= 1'b0;
            protocol_error_q <= 1'b0;
            done <= 1'b0;
        end else begin
            done <= 1'b0;
            case (state_q)
                IDLE: begin
                    if (start) begin
                        chunk_count_q <= '0;
                        residual_rate_q <= residual_rate_q15;
                        protocol_error_q <= 1'b0;
                        state_q <= COLLECT;
                    end
                end
                COLLECT: begin
                    if (in_valid && in_ready) begin
                        gate_q <= gate_q4_12;
                        up_q <= up_q4_12;
                        residual_q <= residual_q4_12;
                        input_last_q <= in_last;
                        if (in_last != (chunk_count_q == COUNT_WIDTH'(VECTOR_COUNT - 1)))
                            protocol_error_q <= 1'b1;
                        state_q <= ACTIVATE;
                    end
                end
                ACTIVATE: begin
                    activated_q <= activated_next;
                    state_q <= MULTIPLY;
                end
                MULTIPLY: begin
                    product_q <= product_next;
                    state_q <= UPDATE;
                end
                UPDATE: begin
                    output_q <= output_next;
                    output_last_q <= input_last_q;
                    state_q <= OUTPUT;
                end
                OUTPUT: begin
                    if (out_ready) begin
                        if (input_last_q) begin
                            state_q <= IDLE;
                            done <= 1'b1;
                        end else begin
                            chunk_count_q <= chunk_count_q + 1'b1;
                            state_q <= COLLECT;
                        end
                    end
                end
                default: state_q <= IDLE;
            endcase
        end
    end

    end endgenerate

    initial begin
        if (VECTOR_LEN < 1 || LANES != 16 || DATA_W != 16 || SCALE_W != 16)
            $error("Plan 6 SwiGLU unit requires non-empty 16-lane Q4.12 vectors");
    end
endmodule
