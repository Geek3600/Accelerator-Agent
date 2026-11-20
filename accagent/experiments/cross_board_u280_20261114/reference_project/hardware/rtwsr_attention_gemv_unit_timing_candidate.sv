`timescale 1ns / 1ps

module rtwsr_attention_gemv_unit #(
    parameter int HEAD_DIM = 128,
    parameter int LANES = 128,
    parameter int MAX_CONTEXT = 2048,
    parameter int DATA_W = 16,
    parameter int ATTN_SCALE_Q15 = 2896,
    parameter int ACC_W = DATA_W + 16 + $clog2(MAX_CONTEXT),
    parameter int DEN_W = 48,
    parameter int QUERY_WIDTH = HEAD_DIM * DATA_W,
    parameter int CHUNK_WIDTH = LANES * DATA_W,
    parameter int CHUNK_COUNT = (HEAD_DIM + LANES - 1) / LANES,
    parameter int CHUNK_INDEX_W = (CHUNK_COUNT <= 1) ? 1 : $clog2(CHUNK_COUNT),
    parameter int CONTEXT_COUNT_W = $clog2(MAX_CONTEXT + 1),
    parameter int TOKEN_INDEX_W = (MAX_CONTEXT <= 1) ? 1 : $clog2(MAX_CONTEXT),
    parameter int OUTPUT_CHUNKS = (HEAD_DIM + LANES - 1) / LANES,
    parameter int OUTPUT_INDEX_W = (OUTPUT_CHUNKS <= 1) ? 1 : $clog2(OUTPUT_CHUNKS),
    parameter int DIVIDE_COUNT_W = 6
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
    localparam int FIRST_GROUPS = LANES / 8;
    localparam int SECOND_GROUPS = FIRST_GROUPS / 8;
    // The first softmax term makes denominator >= 2^15, so 2^40/denominator <= 2^25.
    localparam int RECIPROCAL_W = 26;
    localparam int OUTPUT_PRODUCT_W = ACC_W + RECIPROCAL_W + 1;

    typedef enum logic [4:0] {
        IDLE, STREAM_KV, DOT_PRODUCT, DOT_REDUCE_FIRST, DOT_REDUCE_SECOND,
        DOT_SUM, SCALE_SCORE, COMPARE_SCORE, EXP_LOOKUP, EXP_MULTIPLY,
        EXP_WEIGHT, PREPARE_CONTEXT, SCALE_CONTEXT, UPDATE_CONTEXT,
        DIVIDE_RECIPROCAL, OUTPUT_PRODUCT, OUTPUT_PACK, EMIT_OUTPUT
    } state_t;

    state_t state_q;
    logic [QUERY_WIDTH-1:0] query_q, value_q;
    logic [CHUNK_WIDTH-1:0] query_chunk_q, key_chunk_q;
    logic [LANES-1:0][2*DATA_W-1:0] dot_product_q;
    (* use_dsp = "no" *) logic signed [DOT_W-1:0] first_tree [0:3][0:LANES-1];
    (* use_dsp = "no" *) logic signed [DOT_W-1:0] second_tree [0:3][0:FIRST_GROUPS-1];
    (* use_dsp = "no" *) logic [FIRST_GROUPS-1:0][DOT_W-1:0] first_sum_q;
    (* use_dsp = "no" *) logic [SECOND_GROUPS-1:0][DOT_W-1:0] second_sum_q;
    logic signed [DOT_W-1:0] dot_sum_q;
    logic signed [63:0] scaled_score_product_q;
    logic signed [31:0] score_q12, max_score_q12, score_delta_q12;
    logic score_is_higher_q, have_score_q;
    logic [16:0] exp_base_q, decay_weight_q15;
    logic signed [15:0] exp_slope_q;
    logic [10:0] exp_fraction_q;
    logic signed [27:0] exp_product_q;
    logic exp_one_q, exp_zero_q;
    logic [32:0] exp_coefficients;

    logic [HEAD_DIM-1:0][ACC_W-1:0] context_accumulator_q;
    logic [HEAD_DIM-1:0][ACC_W-1:0] context_scale_input_q;
    logic [HEAD_DIM-1:0][ACC_W-1:0] context_bypass_q;
    logic [HEAD_DIM-1:0][ACC_W+17:0] context_product_q;
    logic [DEN_W-1:0] denominator_q15, denominator_input_q;
    logic [16:0] denominator_increment_q;
    logic [DEN_W+17:0] denominator_product_q;
    logic [DEN_W-1:0] denominator_base_q;

    logic [DEN_W-1:0] divide_remainder_q;
    logic [RECIPROCAL_W-1:0] reciprocal_q40, next_reciprocal;
    logic [40:0] divide_numerator_q;
    logic [DIVIDE_COUNT_W-1:0] divide_count_q;
    logic [DEN_W-1:0] shifted_remainder, next_remainder;
    logic [HEAD_DIM-1:0][OUTPUT_PRODUCT_W-1:0] output_product_q;
    logic [QUERY_WIDTH-1:0] normalized_output_q;
    logic [CONTEXT_COUNT_W-1:0] context_length_q;
    logic [TOKEN_INDEX_W-1:0] token_index_q;
    logic [CHUNK_INDEX_W-1:0] chunk_index_q;
    logic [OUTPUT_INDEX_W-1:0] output_chunk_q;
    logic protocol_error_q;

    function automatic logic [32:0] exp_lookup(input logic [3:0] segment);
        logic [16:0] base;
        logic signed [15:0] slope;
        begin
            case (segment)
                4'd0: begin base = 17'd32768; slope = -16'sd12893; end
                4'd1: begin base = 17'd19875; slope = -16'sd7820; end
                4'd2: begin base = 17'd12055; slope = -16'sd4743; end
                4'd3: begin base = 17'd7312;  slope = -16'sd2877; end
                4'd4: begin base = 17'd4435;  slope = -16'sd1745; end
                4'd5: begin base = 17'd2690;  slope = -16'sd1059; end
                4'd6: begin base = 17'd1631;  slope = -16'sd641; end
                4'd7: begin base = 17'd990;   slope = -16'sd390; end
                4'd8: begin base = 17'd600;   slope = -16'sd236; end
                4'd9: begin base = 17'd364;   slope = -16'sd143; end
                4'd10: begin base = 17'd221; slope = -16'sd87; end
                4'd11: begin base = 17'd134; slope = -16'sd53; end
                4'd12: begin base = 17'd81;  slope = -16'sd32; end
                4'd13: begin base = 17'd49;  slope = -16'sd19; end
                4'd14: begin base = 17'd30;  slope = -16'sd12; end
                default: begin base = 17'd18; slope = -16'sd7; end
            endcase
            exp_lookup = {base, slope};
        end
    endfunction

    function automatic logic signed [DATA_W-1:0] saturate_output(
        input logic signed [OUTPUT_PRODUCT_W-1:0] product
    );
        logic signed [OUTPUT_PRODUCT_W-1:0] value;
        begin
            value = product >>> 40;
            if (value > 32767)
                saturate_output = 16'sd32767;
            else if (value < -32768)
                saturate_output = -16'sd32768;
            else
                saturate_output = value[DATA_W-1:0];
        end
    endfunction

    always_comb begin
        for (integer level = 0; level <= 3; level++) begin
            for (integer lane = 0; lane < LANES; lane++)
                first_tree[level][lane] = '0;
            for (integer lane = 0; lane < FIRST_GROUPS; lane++)
                second_tree[level][lane] = '0;
        end
        for (integer lane = 0; lane < LANES; lane++)
            first_tree[0][lane] = DOT_W'($signed(dot_product_q[lane]));
        for (integer lane = 0; lane < FIRST_GROUPS; lane++)
            second_tree[0][lane] = first_sum_q[lane];
        for (integer level = 1; level <= 3; level++) begin
            for (integer lane = 0; lane < (LANES >> level); lane++)
                first_tree[level][lane] = first_tree[level-1][2*lane] +
                                          first_tree[level-1][2*lane+1];
            for (integer lane = 0; lane < (FIRST_GROUPS >> level); lane++)
                second_tree[level][lane] = second_tree[level-1][2*lane] +
                                           second_tree[level-1][2*lane+1];
        end

        score_q12 = scaled_score_product_q[58:27];
        exp_coefficients = exp_lookup(score_delta_q12[14:11]);
        shifted_remainder = (divide_remainder_q << 1) |
                            {{(DEN_W-1){1'b0}}, divide_numerator_q[40]};
        if (shifted_remainder >= denominator_q15) begin
            next_remainder = shifted_remainder - denominator_q15;
            next_reciprocal = (reciprocal_q40 << 1) | {{(RECIPROCAL_W-1){1'b0}}, 1'b1};
        end else begin
            next_remainder = shifted_remainder;
            next_reciprocal = reciprocal_q40 << 1;
        end

        out_chunk_q4_12 = '0;
        for (integer lane = 0; lane < LANES; lane++) begin
            if (int'(output_chunk_q) * LANES + lane < HEAD_DIM)
                out_chunk_q4_12[lane*DATA_W +: DATA_W] =
                    normalized_output_q[(int'(output_chunk_q)*LANES+lane)*DATA_W +: DATA_W];
        end
    end

    assign ready = (state_q == IDLE);
    assign kv_ready = (state_q == STREAM_KV);
    assign out_valid = (state_q == EMIT_OUTPUT);
    assign out_last = out_valid && (output_chunk_q == OUTPUT_INDEX_W'(OUTPUT_CHUNKS - 1));
    assign busy = (state_q != IDLE);
    assign protocol_error = protocol_error_q;

    // Data registers have no reset; state_q controls when each stage is consumed.
    always_ff @(posedge clk) begin
        integer dimension;
        logic signed [DATA_W-1:0] current_value;
        logic signed [ACC_W-1:0] extended_value;
        if (start && ready && active_context_tokens != 0 &&
            int'(active_context_tokens) <= MAX_CONTEXT)
            query_q <= query_vector_q4_12;
        case (state_q)
            STREAM_KV: begin
                if (kv_valid) begin
                    query_chunk_q <= '0;
                    key_chunk_q <= kv_key_chunk_q4_12;
                    for (integer lane = 0; lane < LANES; lane++) begin
                        dimension = int'(chunk_index_q) * LANES + lane;
                        if (dimension < HEAD_DIM) begin
                            query_chunk_q[lane*DATA_W +: DATA_W] <= query_q[dimension*DATA_W +: DATA_W];
                            value_q[dimension*DATA_W +: DATA_W] <= kv_value_chunk_q4_12[lane*DATA_W +: DATA_W];
                        end
                    end
                end
            end
            DOT_PRODUCT: begin
                for (integer lane = 0; lane < LANES; lane++)
                    dot_product_q[lane] <= $signed(query_chunk_q[lane*DATA_W +: DATA_W]) *
                                           $signed(key_chunk_q[lane*DATA_W +: DATA_W]);
            end
            DOT_REDUCE_FIRST: begin
                for (integer lane = 0; lane < FIRST_GROUPS; lane++)
                    first_sum_q[lane] <= first_tree[3][lane];
            end
            DOT_REDUCE_SECOND: begin
                for (integer lane = 0; lane < SECOND_GROUPS; lane++)
                    second_sum_q[lane] <= second_tree[3][lane];
            end
            SCALE_SCORE: begin
                scaled_score_product_q <=
                    $signed({{(64-DOT_W){dot_sum_q[DOT_W-1]}}, dot_sum_q}) * ATTN_SCALE_Q15;
            end
            EXP_LOOKUP: begin
                exp_base_q <= exp_coefficients[32:16];
                exp_slope_q <= $signed(exp_coefficients[15:0]);
                exp_fraction_q <= score_delta_q12[10:0];
                exp_one_q <= !have_score_q || score_delta_q12 <= 0;
                exp_zero_q <= have_score_q && score_delta_q12 >= 32768;
            end
            EXP_MULTIPLY: exp_product_q <= exp_slope_q * $signed({1'b0, exp_fraction_q});
            EXP_WEIGHT: begin
                if (exp_one_q)
                    decay_weight_q15 <= EXP_ONE_Q15;
                else if (exp_zero_q)
                    decay_weight_q15 <= '0;
                else
                    decay_weight_q15 <= exp_base_q + exp_product_q[27:11];
            end
            PREPARE_CONTEXT: begin
                for (integer channel = 0; channel < HEAD_DIM; channel++) begin
                    current_value = $signed(value_q[channel*DATA_W +: DATA_W]);
                    extended_value = ACC_W'(current_value);
                    if (!have_score_q) begin
                        context_scale_input_q[channel] <= '0;
                        context_bypass_q[channel] <= extended_value <<< 15;
                    end else if (score_is_higher_q) begin
                        context_scale_input_q[channel] <= context_accumulator_q[channel];
                        context_bypass_q[channel] <= extended_value <<< 15;
                    end else begin
                        context_scale_input_q[channel] <= extended_value <<< 15;
                        context_bypass_q[channel] <= context_accumulator_q[channel];
                    end
                end
                denominator_input_q <= score_is_higher_q ? denominator_q15 : '0;
                denominator_base_q <= have_score_q && !score_is_higher_q ? denominator_q15 : '0;
                denominator_increment_q <= !have_score_q || score_is_higher_q ?
                                           EXP_ONE_Q15 : decay_weight_q15;
            end
            SCALE_CONTEXT: begin
                for (integer channel = 0; channel < HEAD_DIM; channel++)
                    context_product_q[channel] <= $signed(context_scale_input_q[channel]) *
                                                  $signed({1'b0, decay_weight_q15});
                denominator_product_q <= denominator_input_q * {1'b0, decay_weight_q15};
            end
            UPDATE_CONTEXT: begin
                for (integer channel = 0; channel < HEAD_DIM; channel++)
                    context_accumulator_q[channel] <=
                        $signed(context_product_q[channel][ACC_W+14:15]) + context_bypass_q[channel];
            end
            OUTPUT_PRODUCT: begin
                for (integer channel = 0; channel < HEAD_DIM; channel++)
                    output_product_q[channel] <= $signed(context_accumulator_q[channel]) *
                                                 $signed({1'b0, reciprocal_q40});
            end
            OUTPUT_PACK: begin
                for (integer channel = 0; channel < HEAD_DIM; channel++)
                    normalized_output_q[channel*DATA_W +: DATA_W] <= saturate_output(output_product_q[channel]);
            end
            default: begin end
        endcase
    end

    always_ff @(posedge clk) begin
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
            have_score_q <= 1'b0;
            score_is_higher_q <= 1'b0;
            score_delta_q12 <= '0;
            protocol_error_q <= 1'b0;
            done <= 1'b0;
        end else begin
            done <= 1'b0;
            if (start && ready) begin
                if (active_context_tokens == 0 || int'(active_context_tokens) > MAX_CONTEXT) begin
                    protocol_error_q <= 1'b1;
                end else begin
                    context_length_q <= active_context_tokens;
                    token_index_q <= '0;
                    chunk_index_q <= '0;
                    output_chunk_q <= '0;
                    dot_sum_q <= '0;
                    max_score_q12 <= '0;
                    denominator_q15 <= '0;
                    have_score_q <= 1'b0;
                    state_q <= STREAM_KV;
                    protocol_error_q <= 1'b0;
                end
            end else begin
                case (state_q)
                    STREAM_KV: if (kv_valid) state_q <= DOT_PRODUCT;
                    DOT_PRODUCT: state_q <= DOT_REDUCE_FIRST;
                    DOT_REDUCE_FIRST: state_q <= DOT_REDUCE_SECOND;
                    DOT_REDUCE_SECOND: state_q <= DOT_SUM;
                    DOT_SUM: begin
                        dot_sum_q <= dot_sum_q + second_sum_q[0] + second_sum_q[1];
                        if (chunk_index_q == CHUNK_INDEX_W'(CHUNK_COUNT - 1)) begin
                            chunk_index_q <= '0;
                            state_q <= SCALE_SCORE;
                        end else begin
                            chunk_index_q <= chunk_index_q + 1'b1;
                            state_q <= STREAM_KV;
                        end
                    end
                    SCALE_SCORE: state_q <= COMPARE_SCORE;
                    COMPARE_SCORE: begin
                        score_is_higher_q <= have_score_q && score_q12 > max_score_q12;
                        if (!have_score_q || score_q12 > max_score_q12) begin
                            max_score_q12 <= score_q12;
                            score_delta_q12 <= have_score_q ? score_q12 - max_score_q12 : '0;
                        end else begin
                            score_delta_q12 <= max_score_q12 - score_q12;
                        end
                        state_q <= EXP_LOOKUP;
                    end
                    EXP_LOOKUP: state_q <= EXP_MULTIPLY;
                    EXP_MULTIPLY: state_q <= EXP_WEIGHT;
                    EXP_WEIGHT: state_q <= PREPARE_CONTEXT;
                    PREPARE_CONTEXT: state_q <= SCALE_CONTEXT;
                    SCALE_CONTEXT: state_q <= UPDATE_CONTEXT;
                    UPDATE_CONTEXT: begin
                        denominator_q15 <= denominator_product_q[DEN_W+14:15] +
                                           denominator_base_q + DEN_W'(denominator_increment_q);
                        have_score_q <= 1'b1;
                        dot_sum_q <= '0;
                        if (token_index_q + 1'b1 == context_length_q) begin
                            divide_remainder_q <= '0;
                            divide_numerator_q <= RECIPROCAL_NUMERATOR;
                            reciprocal_q40 <= '0;
                            divide_count_q <= '0;
                            state_q <= DIVIDE_RECIPROCAL;
                        end else begin
                            token_index_q <= token_index_q + 1'b1;
                            state_q <= STREAM_KV;
                        end
                    end
                    DIVIDE_RECIPROCAL: begin
                        divide_remainder_q <= next_remainder;
                        reciprocal_q40 <= next_reciprocal;
                        divide_numerator_q <= divide_numerator_q << 1;
                        if (divide_count_q == DIVIDE_COUNT_W'(40)) begin
                            output_chunk_q <= '0;
                            state_q <= OUTPUT_PRODUCT;
                        end else begin
                            divide_count_q <= divide_count_q + 1'b1;
                        end
                    end
                    OUTPUT_PRODUCT: state_q <= OUTPUT_PACK;
                    OUTPUT_PACK: state_q <= EMIT_OUTPUT;
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
                    default: state_q <= IDLE;
                endcase
            end
        end
    end

    initial begin
        if (HEAD_DIM < 1 || LANES != 128 || MAX_CONTEXT < 2048 || DATA_W != 16)
            $error("Plan 6 attention engine requires 128 lanes, 16-bit Q4.12 values, and context >= 2048");
        if (ATTN_SCALE_Q15 <= 0 || ACC_W < DATA_W + 16 + $clog2(MAX_CONTEXT) || DEN_W < 32)
            $error("invalid attention fixed-point configuration");
    end
endmodule
