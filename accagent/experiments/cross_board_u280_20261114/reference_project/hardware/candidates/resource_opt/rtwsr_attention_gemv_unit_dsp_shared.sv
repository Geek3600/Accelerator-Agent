`timescale 1ns / 1ps

module rtwsr_attention_gemv_unit #(
    parameter int HEAD_DIM = 128,
    parameter int LANES = 128,
    parameter int MAX_CONTEXT = 2048,
    parameter int DATA_W = 16,
    parameter int ATTN_SCALE_Q15 = 2896,
    parameter int ACC_W = 56,
    parameter int DEN_W = 48,
    parameter int QUERY_WIDTH = HEAD_DIM * DATA_W,
    parameter int CHUNK_WIDTH = LANES * DATA_W,
    parameter int CHUNK_COUNT = (HEAD_DIM + LANES - 1) / LANES,
    parameter int CHUNK_INDEX_W = (CHUNK_COUNT <= 1) ? 1 : $clog2(CHUNK_COUNT),
    parameter int CONTEXT_COUNT_W = $clog2(MAX_CONTEXT + 1),
    parameter int TOKEN_INDEX_W = (MAX_CONTEXT <= 1) ? 1 : $clog2(MAX_CONTEXT),
    parameter int OUTPUT_CHUNKS = (HEAD_DIM + LANES - 1) / LANES,
    parameter int OUTPUT_INDEX_W = (OUTPUT_CHUNKS <= 1) ? 1 : $clog2(OUTPUT_CHUNKS),
    parameter int DIVIDE_COUNT_W = 6,
    // The denominator is already the fully reduced online-softmax value at
    // the end of the final KV token.  A hardware divider can therefore
    // replace the bit-serial reciprocal iteration without changing the
    // online max/denominator or context accumulator dependencies.
    parameter bit FAST_RECIPROCAL = 1'b0,
    parameter int OUTPUT_MULTIPLIER_LANES = 16,
    parameter int OUTPUT_GROUPS = (HEAD_DIM + OUTPUT_MULTIPLIER_LANES - 1) / OUTPUT_MULTIPLIER_LANES,
    parameter int OUTPUT_GROUP_INDEX_W = (OUTPUT_GROUPS <= 1) ? 1 : $clog2(OUTPUT_GROUPS)
)(
    input  logic                         clk,
    input  logic                         rst_n,
    input  logic                         start,
    input  logic [CONTEXT_COUNT_W-1:0]   active_context_tokens,
    input  logic [QUERY_WIDTH-1:0]       query_vector_q4_12,
    output logic                         ready,
    input  logic                         kv_valid,
    output logic                         kv_ready,
    input  logic [CHUNK_WIDTH-1:0]       kv_key_chunk_q4_12,
    input  logic [CHUNK_WIDTH-1:0]       kv_value_chunk_q4_12,
    output logic                         out_valid,
    input  logic                         out_ready,
    output logic [CHUNK_WIDTH-1:0]       out_chunk_q4_12,
    output logic                         out_last,
    output logic                         busy,
    output logic                         done,
    output logic                         protocol_error
);
    localparam logic [16:0] EXP_ONE_Q15 = 17'd32768;
    localparam logic [40:0] RECIPROCAL_NUMERATOR = 41'b1 << 40;
    localparam int DOT_W = 2 * DATA_W + $clog2(HEAD_DIM) + 1;
    localparam int REDUCTION_LEVELS = $clog2(LANES);

    typedef enum logic [2:0] {IDLE, STREAM_KV, DIVIDE_RECIPROCAL, PREP_OUTPUT, EMIT_OUTPUT} state_t;

    state_t state_q;
    logic [HEAD_DIM*DATA_W-1:0] query_q;
    logic [HEAD_DIM*DATA_W-1:0] value_q;
    logic signed [HEAD_DIM*ACC_W-1:0] context_accumulator_q;
    logic signed [DOT_W-1:0] dot_sum_q;
    logic signed [31:0] max_score_q12;
    logic [DEN_W-1:0] denominator_q15;
    logic [DEN_W-1:0] divide_remainder_q;
    logic [40:0] divide_numerator_q;
    logic [DEN_W-1:0] reciprocal_q40;
    logic [DIVIDE_COUNT_W-1:0] divide_count_q;
    logic [CONTEXT_COUNT_W-1:0] context_length_q;
    logic [TOKEN_INDEX_W-1:0] token_index_q;
    logic [CHUNK_INDEX_W-1:0] chunk_index_q;
    logic [OUTPUT_INDEX_W-1:0] output_chunk_q;
    logic [OUTPUT_GROUP_INDEX_W-1:0] output_group_q;
    logic have_score_q;
    logic protocol_error_q;
    logic [HEAD_DIM*DATA_W-1:0] output_vector_q;

    logic signed [DOT_W-1:0] chunk_dot;
    logic signed [DOT_W-1:0] reduction_tree [0:REDUCTION_LEVELS][0:LANES-1];
    logic signed [63:0] scaled_score_product;
    logic signed [31:0] score_q12;
    logic signed [31:0] next_max_score_q12;
    logic signed [31:0] old_score_delta_q12;
    logic signed [31:0] current_score_delta_q12;
    logic [16:0] old_weight_q15;
    logic [16:0] current_weight_q15;
    logic [DEN_W-1:0] next_denominator_q15;
    logic [DEN_W-1:0] shifted_remainder;
    logic [DEN_W-1:0] next_remainder;
    logic [DEN_W-1:0] next_reciprocal;
    logic signed [ACC_W+DEN_W:0] output_product [0:OUTPUT_MULTIPLIER_LANES-1];
    logic signed [ACC_W+DEN_W:0] output_value_q12 [0:OUTPUT_MULTIPLIER_LANES-1];
    logic signed [DATA_W-1:0] output_value_saturated [0:OUTPUT_MULTIPLIER_LANES-1];
    logic final_chunk;
    logic final_token;

    function automatic logic [16:0] exp_neg_q15(input logic signed [31:0] delta_q12);
        logic [3:0] segment;
        logic [10:0] fraction;
        logic signed [15:0] slope_q15;
        logic signed [27:0] slope_product;
        logic signed [16:0] interpolation;
        logic [16:0] base_q15;
        begin
            if (delta_q12 <= 0) begin
                exp_neg_q15 = EXP_ONE_Q15;
            end else if (delta_q12 >= 32'sd32768) begin
                exp_neg_q15 = 17'd0;
            end else begin
                segment = delta_q12[14:11];
                fraction = delta_q12[10:0];
                case (segment)
                    4'd0: begin base_q15 = 17'd32768; slope_q15 = -16'sd12893; end
                    4'd1: begin base_q15 = 17'd19875; slope_q15 = -16'sd7820; end
                    4'd2: begin base_q15 = 17'd12055; slope_q15 = -16'sd4743; end
                    4'd3: begin base_q15 = 17'd7312;  slope_q15 = -16'sd2877; end
                    4'd4: begin base_q15 = 17'd4435;  slope_q15 = -16'sd1745; end
                    4'd5: begin base_q15 = 17'd2690;  slope_q15 = -16'sd1059; end
                    4'd6: begin base_q15 = 17'd1631;  slope_q15 = -16'sd641; end
                    4'd7: begin base_q15 = 17'd990;   slope_q15 = -16'sd390; end
                    4'd8: begin base_q15 = 17'd600;   slope_q15 = -16'sd236; end
                    4'd9: begin base_q15 = 17'd364;   slope_q15 = -16'sd143; end
                    4'd10: begin base_q15 = 17'd221;  slope_q15 = -16'sd87; end
                    4'd11: begin base_q15 = 17'd134;  slope_q15 = -16'sd53; end
                    4'd12: begin base_q15 = 17'd81;   slope_q15 = -16'sd32; end
                    4'd13: begin base_q15 = 17'd49;   slope_q15 = -16'sd19; end
                    4'd14: begin base_q15 = 17'd30;   slope_q15 = -16'sd12; end
                    default: begin base_q15 = 17'd18; slope_q15 = -16'sd7; end
                endcase
                slope_product = slope_q15 * $signed({1'b0, fraction});
                interpolation = slope_product[27:11];
                exp_neg_q15 = base_q15 + interpolation;
            end
        end
    endfunction

    function automatic [DEN_W-1:0] scale_denominator(
        input logic [DEN_W-1:0] value,
        input logic [16:0] weight
    );
        logic [DEN_W+17:0] product;
        begin
            product = value * {1'b0, weight};
            scale_denominator = product[DEN_W+14:15];
        end
    endfunction

    function automatic logic signed [ACC_W-1:0] scale_accumulator(
        input logic signed [ACC_W-1:0] value,
        input logic [16:0] weight
    );
        logic signed [ACC_W+17:0] product;
        begin
            product = value * $signed({1'b0, weight});
            scale_accumulator = product[ACC_W+14:15];
        end
    endfunction

    function automatic logic signed [ACC_W-1:0] weighted_value(
        input logic signed [DATA_W-1:0] value,
        input logic [16:0] weight
    );
        logic signed [DATA_W+17:0] product;
        begin
            product = value * $signed({1'b0, weight});
            weighted_value = {{(ACC_W-DATA_W-18){product[DATA_W+17]}}, product};
        end
    endfunction

    always_comb begin
        integer lane;
        integer dimension;
        integer level;
        integer output_dimension;
        logic signed [DATA_W-1:0] query_value;
        logic signed [DATA_W-1:0] key_value;
        logic signed [2*DATA_W-1:0] product;
        logic signed [DOT_W-1:0] full_dot;

        chunk_dot = '0;
        query_value = '0;
        key_value = '0;
        product = '0;
        for (level = 0; level <= REDUCTION_LEVELS; level = level + 1) begin
            for (lane = 0; lane < LANES; lane = lane + 1)
                reduction_tree[level][lane] = '0;
        end
        for (lane = 0; lane < LANES; lane = lane + 1) begin
            dimension = int'(chunk_index_q) * LANES + lane;
            if (dimension < HEAD_DIM) begin
                query_value = $signed(query_q[dimension*DATA_W +: DATA_W]);
                key_value = $signed(kv_key_chunk_q4_12[lane*DATA_W +: DATA_W]);
                product = query_value * key_value;
                reduction_tree[0][lane] = {{(DOT_W-2*DATA_W){product[2*DATA_W-1]}}, product};
            end
        end

        for (level = 1; level <= REDUCTION_LEVELS; level = level + 1) begin
            for (lane = 0; lane < (LANES >> level); lane = lane + 1)
                reduction_tree[level][lane] = reduction_tree[level-1][2*lane] +
                                              reduction_tree[level-1][2*lane+1];
        end
        chunk_dot = reduction_tree[REDUCTION_LEVELS][0];

        full_dot = dot_sum_q + chunk_dot;
        scaled_score_product = $signed({{(64-DOT_W){full_dot[DOT_W-1]}}, full_dot}) * ATTN_SCALE_Q15;
        score_q12 = scaled_score_product[58:27];
        if (!have_score_q) begin
            next_max_score_q12 = score_q12;
            old_score_delta_q12 = 32'sd32768;
            current_score_delta_q12 = 32'sd0;
            old_weight_q15 = 17'd0;
            current_weight_q15 = EXP_ONE_Q15;
        end else begin
            next_max_score_q12 = (score_q12 > max_score_q12) ? score_q12 : max_score_q12;
            old_score_delta_q12 = next_max_score_q12 - max_score_q12;
            current_score_delta_q12 = next_max_score_q12 - score_q12;
            old_weight_q15 = exp_neg_q15(old_score_delta_q12);
            current_weight_q15 = exp_neg_q15(current_score_delta_q12);
        end
        next_denominator_q15 = scale_denominator(denominator_q15, old_weight_q15) +
                               {{(DEN_W-17){1'b0}}, current_weight_q15};

        final_chunk = (chunk_index_q == CHUNK_INDEX_W'(CHUNK_COUNT - 1));
        final_token = (token_index_q + 1'b1 == context_length_q);

        shifted_remainder = (divide_remainder_q << 1) |
                            {{(DEN_W-1){1'b0}}, divide_numerator_q[40]};
        if (shifted_remainder >= denominator_q15) begin
            next_remainder = shifted_remainder - denominator_q15;
            next_reciprocal = (reciprocal_q40 << 1) | {{(DEN_W-1){1'b0}}, 1'b1};
        end else begin
            next_remainder = shifted_remainder;
            next_reciprocal = reciprocal_q40 << 1;
        end

        out_chunk_q4_12 = '0;
        for (lane = 0; lane < LANES; lane = lane + 1) begin
            dimension = int'(output_chunk_q) * LANES + lane;
            if (dimension < HEAD_DIM)
                out_chunk_q4_12[lane*DATA_W +: DATA_W] = output_vector_q[dimension*DATA_W +: DATA_W];
        end

        for (lane = 0; lane < OUTPUT_MULTIPLIER_LANES; lane = lane + 1) begin
            output_dimension = int'(output_group_q) * OUTPUT_MULTIPLIER_LANES + lane;
            output_product[lane] = '0;
            output_value_q12[lane] = '0;
            output_value_saturated[lane] = '0;
            if (output_dimension < HEAD_DIM) begin
                output_product[lane] =
                    $signed(context_accumulator_q[output_dimension*ACC_W +: ACC_W]) *
                    $signed({1'b0, reciprocal_q40});
                output_value_q12[lane] = output_product[lane] >>> 40;
                if (output_value_q12[lane] > 105'sd32767)
                    output_value_saturated[lane] = 16'sd32767;
                else if (output_value_q12[lane] < -105'sd32768)
                    output_value_saturated[lane] = -16'sd32768;
                else
                    output_value_saturated[lane] = output_value_q12[lane][DATA_W-1:0];
            end
        end
    end

    assign ready = (state_q == IDLE);
    assign kv_ready = (state_q == STREAM_KV);
    assign out_valid = (state_q == EMIT_OUTPUT);
    assign out_last = out_valid && (output_chunk_q == OUTPUT_INDEX_W'(OUTPUT_CHUNKS - 1));
    assign busy = (state_q != IDLE);
    assign protocol_error = protocol_error_q;

    always_ff @(posedge clk) begin
        integer dimension;
        integer lane;
        integer chunk_base;
        integer output_dimension;
        logic signed [DATA_W-1:0] current_value_tmp;
        logic signed [ACC_W-1:0] next_context_value_tmp;
        if (!rst_n) begin
            state_q <= IDLE;
            dot_sum_q <= '0;
            max_score_q12 <= '0;
            denominator_q15 <= '0;
            divide_remainder_q <= '0;
            divide_numerator_q <= '0;
            reciprocal_q40 <= '0;
            divide_count_q <= '0;
            context_length_q <= '0;
            token_index_q <= '0;
            chunk_index_q <= '0;
            output_chunk_q <= '0;
            output_group_q <= '0;
            have_score_q <= 1'b0;
            protocol_error_q <= 1'b0;
            done <= 1'b0;
            query_q <= '0;
            value_q <= '0;
            context_accumulator_q <= '0;
            output_vector_q <= '0;
        end else begin
            done <= 1'b0;
            if (start && ready) begin
                if (active_context_tokens == 0 || int'(active_context_tokens) > MAX_CONTEXT) begin
                    protocol_error_q <= 1'b1;
                end else begin
                    query_q <= query_vector_q4_12;
                    value_q <= '0;
                    context_accumulator_q <= '0;
                    context_length_q <= active_context_tokens;
                    token_index_q <= '0;
                    chunk_index_q <= '0;
                    output_chunk_q <= '0;
                    output_group_q <= '0;
                    output_vector_q <= '0;
                    dot_sum_q <= '0;
                    max_score_q12 <= '0;
                    denominator_q15 <= '0;
                    have_score_q <= 1'b0;
                    state_q <= STREAM_KV;
                    protocol_error_q <= 1'b0;
                end
            end else begin
                case (state_q)
                    STREAM_KV: begin
                        if (kv_valid && kv_ready) begin
                            chunk_base = int'(chunk_index_q) * LANES;
                            for (lane = 0; lane < LANES; lane = lane + 1) begin
                                dimension = chunk_base + lane;
                                if (dimension < HEAD_DIM)
                                    value_q[dimension*DATA_W +: DATA_W] <= kv_value_chunk_q4_12[lane*DATA_W +: DATA_W];
                            end

                            if (final_chunk) begin
                                max_score_q12 <= next_max_score_q12;
                                denominator_q15 <= next_denominator_q15;
                                have_score_q <= 1'b1;
                                for (dimension = 0; dimension < HEAD_DIM; dimension = dimension + 1) begin
                                    current_value_tmp = $signed(value_q[dimension*DATA_W +: DATA_W]);
                                    if ((dimension / LANES) == int'(chunk_index_q))
                                        current_value_tmp = $signed(kv_value_chunk_q4_12[(dimension % LANES)*DATA_W +: DATA_W]);
                                    next_context_value_tmp = scale_accumulator(
                                        $signed(context_accumulator_q[dimension*ACC_W +: ACC_W]), old_weight_q15
                                    ) + weighted_value(current_value_tmp, current_weight_q15);
                                    context_accumulator_q[dimension*ACC_W +: ACC_W] <= next_context_value_tmp;
                                end
                                dot_sum_q <= '0;
                                chunk_index_q <= '0;
                                if (final_token) begin
                                    if (FAST_RECIPROCAL) begin
                                        reciprocal_q40 <= (next_denominator_q15 == 0) ? '0 :
                                            RECIPROCAL_NUMERATOR / next_denominator_q15;
                                        output_group_q <= '0;
                                        state_q <= PREP_OUTPUT;
                                    end else begin
                                        divide_remainder_q <= '0;
                                        divide_numerator_q <= RECIPROCAL_NUMERATOR;
                                        reciprocal_q40 <= '0;
                                        divide_count_q <= '0;
                                        state_q <= DIVIDE_RECIPROCAL;
                                    end
                                end else begin
                                    token_index_q <= token_index_q + 1'b1;
                                end
                            end else begin
                                dot_sum_q <= dot_sum_q + chunk_dot;
                                chunk_index_q <= chunk_index_q + 1'b1;
                            end
                        end
                    end
                    DIVIDE_RECIPROCAL: begin
                        divide_remainder_q <= next_remainder;
                        reciprocal_q40 <= next_reciprocal;
                        divide_numerator_q <= divide_numerator_q << 1;
                        if (divide_count_q == DIVIDE_COUNT_W'(40)) begin
                            output_chunk_q <= '0;
                            output_group_q <= '0;
                            state_q <= PREP_OUTPUT;
                        end else begin
                            divide_count_q <= divide_count_q + 1'b1;
                        end
                    end
                    PREP_OUTPUT: begin
                        for (lane = 0; lane < OUTPUT_MULTIPLIER_LANES; lane = lane + 1) begin
                            output_dimension = int'(output_group_q) * OUTPUT_MULTIPLIER_LANES + lane;
                            if (output_dimension < HEAD_DIM)
                                output_vector_q[output_dimension*DATA_W +: DATA_W] <= output_value_saturated[lane];
                        end
                        if (output_group_q == OUTPUT_GROUP_INDEX_W'(OUTPUT_GROUPS - 1)) begin
                            output_chunk_q <= '0;
                            state_q <= EMIT_OUTPUT;
                        end else begin
                            output_group_q <= output_group_q + 1'b1;
                        end
                    end
                    EMIT_OUTPUT: begin
                        if (out_ready) begin
                            if (output_chunk_q == OUTPUT_INDEX_W'(OUTPUT_CHUNKS - 1)) begin
                                state_q <= IDLE;
                                done <= 1'b1;
                            end else begin
                                output_chunk_q <= output_chunk_q + 1'b1;
                            end
                        end
                    end
                    default: begin
                        state_q <= IDLE;
                    end
                endcase
            end
        end
    end

    initial begin
        if (HEAD_DIM < 1 || LANES != 128 || MAX_CONTEXT < 2048 || DATA_W != 16)
            $error("Plan 6 attention engine requires 128 lanes, 16-bit Q4.12 values, and context >= 2048");
        if (ATTN_SCALE_Q15 <= 0 || ACC_W < 48 || DEN_W < 32 ||
            OUTPUT_MULTIPLIER_LANES < 1 || OUTPUT_MULTIPLIER_LANES > HEAD_DIM)
            $error("invalid attention fixed-point configuration");
    end
endmodule
