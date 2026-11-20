`timescale 1ns / 1ps

module usw512_dual_track_channel #(
    parameter int TRITS_PER_CYCLE = 64,
    parameter int ACT_W = 8,
    parameter int ACC_W = 24,
    parameter bit STATIC_REUSE = 1'b0
)(
    input  logic                         clk,
    input  logic                         rst_n,
    input  logic                         valid_in,
    input  logic                         first_subchunk,
    input  logic                         last_subchunk,
    input  logic [TRITS_PER_CYCLE-1:0]   subchunk_nz,
    input  logic [TRITS_PER_CYCLE-1:0]   subchunk_sgn,
    input  logic signed [15:0]           outlier_val0_q4_12,
    input  logic signed [15:0]           outlier_val1_q4_12,
    input  logic [TRITS_PER_CYCLE*ACT_W-1:0] act_subvec,
    input  logic signed [ACT_W-1:0]      act_window_lookup0,
    input  logic signed [ACT_W-1:0]      act_window_lookup1,
    input  logic [15:0]                  fused_gamma_fp16,
    input  logic signed [31:0]           activation_scale_q8_24,
    input  logic                         static_sum_enable,
    input  logic signed [36:0]           static_sum_q12,
    output logic                         row_done_valid,
    output logic signed [31:0]           final_channel_out_q12,
    output logic signed [36:0]           unscaled_sum_q12
);
    localparam int SPARSE_ACC_W = 32;
    localparam int MERGE_W = 37;

    logic dense_valid;
    logic signed [ACC_W-1:0] dense_acc;
    localparam int SPARSE_PRODUCT_W = ACT_W + 16 + (TRITS_PER_CYCLE == 128 ? 1 : 0);

    logic signed [ACT_W+15:0] sparse_product0_comb;
    logic signed [ACT_W+15:0] sparse_product1_comb;
    logic signed [SPARSE_PRODUCT_W-1:0] sparse_product_sum_comb;
    logic signed [SPARSE_PRODUCT_W-1:0] sparse_product_stage1;
    logic signed [SPARSE_PRODUCT_W-1:0] sparse_product_stage2;
    logic signed [SPARSE_ACC_W-1:0] sparse_acc;
    logic valid_stage1;
    logic valid_stage2;
    logic first_stage1;
    logic first_stage2;
    logic last_stage1;
    logic last_stage2;
    (* DONT_TOUCH = "TRUE" *) logic last_stage3;
    logic signed [31:0] gamma_stage1;
    logic signed [31:0] gamma_stage2;
    logic signed [31:0] gamma_stage3;
    logic signed [31:0] activation_scale_stage1;
    logic signed [31:0] activation_scale_stage2;
    logic signed [31:0] activation_scale_stage3;
    logic signed [MERGE_W-1:0] dense_q12;
    logic signed [MERGE_W-1:0] merged_sum_q12;
    logic signed [63:0] scale_product_q48;
    logic signed [MERGE_W-1:0] merged_sum_stage1;
    logic signed [63:0] scale_product_stage1;
    logic signed [100:0] scaled_product_comb;
    logic signed [100:0] scaled_product_stage2;
    logic signed [53:0] truncated_q12;
    logic signed [53:0] rounded_q12_comb;
    logic signed [53:0] rounded_q12_stage3;
    logic round_up_q12;
    logic scale_valid_stage1;
    logic scale_valid_stage2;
    logic scale_valid_stage3;

    function automatic logic signed [31:0] fp16_to_q8_24(input logic [15:0] value);
        logic [4:0] exponent;
        logic [10:0] significand;
        logic [31:0] magnitude;
        logic signed [32:0] signed_value;
        integer shift_amount;
        begin
            exponent = value[14:10];
            significand = {1'b1, value[9:0]};
            if (exponent == 5'd0) begin
                magnitude = {22'b0, value[9:0]};
            end else if (exponent == 5'd31) begin
                magnitude = 32'd0;
            end else if (exponent >= 5'd22) begin
                magnitude = 32'd0;
            end else begin
                shift_amount = int'(exponent) - 1;
                magnitude = {21'b0, significand} << shift_amount;
            end

            if (exponent == 5'd31)
                fp16_to_q8_24 = 32'sd0;
            else if (exponent >= 5'd22)
                fp16_to_q8_24 = value[15] ? 32'sh80000000 : 32'sh7fffffff;
            else begin
                signed_value = value[15] ? -$signed({1'b0, magnitude}) :
                                           $signed({1'b0, magnitude});
                fp16_to_q8_24 = signed_value[31:0];
            end
        end
    endfunction

    scale_hoisted_ternary_lane #(
        .VEC_LEN(TRITS_PER_CYCLE), .ACT_W(ACT_W), .ACC_W(ACC_W)
    ) u_dense_track (
        .clk(clk),
        .rst_n(rst_n),
        .valid_in(valid_in),
        .first_chunk(first_subchunk),
        .act_vec(act_subvec),
        .trit_nz(subchunk_nz),
        .trit_sgn(subchunk_sgn),
        .valid_out(dense_valid),
        .dense_acc_out(dense_acc)
    );

    always_comb begin
        dense_q12 = {{(MERGE_W-ACC_W){dense_acc[ACC_W-1]}}, dense_acc};
        dense_q12 = dense_q12 <<< 12;
        merged_sum_q12 = dense_q12 +
            {{(MERGE_W-SPARSE_ACC_W){sparse_acc[SPARSE_ACC_W-1]}}, sparse_acc};

        scale_product_q48 =
            $signed({{32{activation_scale_stage3[31]}}, activation_scale_stage3}) *
            $signed({{32{gamma_stage3[31]}}, gamma_stage3});
        scaled_product_comb = $signed(merged_sum_stage1) * $signed(scale_product_stage1);
        truncated_q12 = {{1{scaled_product_stage2[100]}}, scaled_product_stage2[100:48]};
        round_up_q12 = scaled_product_stage2[47] &&
            ((|scaled_product_stage2[46:0]) || truncated_q12[0]);
        rounded_q12_comb = truncated_q12 + {{53{1'b0}}, round_up_q12};
        sparse_product_sum_comb =
            {{(SPARSE_PRODUCT_W-(ACT_W+16)){sparse_product0_comb[ACT_W+15]}}, sparse_product0_comb} +
            {{(SPARSE_PRODUCT_W-(ACT_W+16)){sparse_product1_comb[ACT_W+15]}}, sparse_product1_comb};
    end

    always_comb begin
        sparse_product0_comb = act_window_lookup0 * outlier_val0_q4_12;
        sparse_product1_comb = act_window_lookup1 * outlier_val1_q4_12;
    end

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            sparse_product_stage1 <= '0;
            sparse_product_stage2 <= '0;
            sparse_acc <= '0;
            valid_stage1 <= 1'b0;
            valid_stage2 <= 1'b0;
            first_stage1 <= 1'b0;
            first_stage2 <= 1'b0;
            last_stage1 <= 1'b0;
            last_stage2 <= 1'b0;
            last_stage3 <= 1'b0;
            gamma_stage1 <= '0;
            gamma_stage2 <= '0;
            gamma_stage3 <= '0;
            activation_scale_stage1 <= '0;
            activation_scale_stage2 <= '0;
            activation_scale_stage3 <= '0;
            merged_sum_stage1 <= '0;
            scale_product_stage1 <= '0;
            scaled_product_stage2 <= '0;
            rounded_q12_stage3 <= '0;
            scale_valid_stage1 <= 1'b0;
            scale_valid_stage2 <= 1'b0;
            scale_valid_stage3 <= 1'b0;
            row_done_valid <= 1'b0;
            final_channel_out_q12 <= '0;
            unscaled_sum_q12 <= '0;
        end else begin
            sparse_product_stage1 <= sparse_product_sum_comb;
            sparse_product_stage2 <= sparse_product_stage1;

            valid_stage1 <= valid_in;
            valid_stage2 <= valid_stage1;
            first_stage1 <= valid_in & first_subchunk;
            first_stage2 <= first_stage1;
            last_stage1 <= valid_in & last_subchunk;
            last_stage2 <= last_stage1;
            last_stage3 <= last_stage2;
            gamma_stage1 <= fp16_to_q8_24(fused_gamma_fp16);
            gamma_stage2 <= gamma_stage1;
            gamma_stage3 <= gamma_stage2;
            activation_scale_stage1 <= activation_scale_q8_24;
            activation_scale_stage2 <= activation_scale_stage1;
            activation_scale_stage3 <= activation_scale_stage2;

            scale_valid_stage1 <= dense_valid & last_stage3;
            scale_valid_stage2 <= scale_valid_stage1;
            scale_valid_stage3 <= scale_valid_stage2;
            row_done_valid <= scale_valid_stage3;
            if (dense_valid & last_stage3) begin
                unscaled_sum_q12 <= merged_sum_q12;
                if (STATIC_REUSE && static_sum_enable)
                    merged_sum_stage1 <= merged_sum_q12 + static_sum_q12;
                else
                    merged_sum_stage1 <= merged_sum_q12;
                scale_product_stage1 <= scale_product_q48;
            end
            scaled_product_stage2 <= scaled_product_comb;
            if (scale_valid_stage2)
                rounded_q12_stage3 <= rounded_q12_comb;

            if (valid_stage2) begin
                if (first_stage2)
                    sparse_acc <= {{(SPARSE_ACC_W-SPARSE_PRODUCT_W){sparse_product_stage2[SPARSE_PRODUCT_W-1]}}, sparse_product_stage2};
                else
                    sparse_acc <= sparse_acc +
                        {{(SPARSE_ACC_W-SPARSE_PRODUCT_W){sparse_product_stage2[SPARSE_PRODUCT_W-1]}}, sparse_product_stage2};
            end
            if (scale_valid_stage3) begin
                if (rounded_q12_stage3 > 54'sd2147483647)
                    final_channel_out_q12 <= 32'sh7fffffff;
                else if (rounded_q12_stage3 < -54'sd2147483648)
                    final_channel_out_q12 <= 32'sh80000000;
                else
                    final_channel_out_q12 <= rounded_q12_stage3[31:0];
            end
        end
    end
endmodule
