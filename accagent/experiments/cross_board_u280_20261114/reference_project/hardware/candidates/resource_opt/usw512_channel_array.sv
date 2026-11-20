`timescale 1ns / 1ps

module usw512_channel_array #(
    parameter int P_CH = 32,
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
    input  logic [1:0]                   subchunk_index,
    input  logic [P_CH*512-1:0]          usw_words,
    input  logic [256*ACT_W-1:0]         activation_window,
    input  logic [P_CH*16-1:0]           fused_gamma_fp16,
    input  logic [15:0]                  activation_scale_fp16,
    input  logic                         static_sum_enable,
    input  logic [P_CH*37-1:0]           static_sums_q12,
    output logic [P_CH-1:0]              row_done_valid,
    output logic [P_CH*32-1:0]           final_channels_q12,
    output logic [P_CH*37-1:0]           unscaled_sums_q12
);
    logic [TRITS_PER_CYCLE*ACT_W-1:0] activation_subvector;
    logic signed [31:0] activation_scale_q8_24;

    function automatic logic signed [31:0] fp16_to_q8_24(input logic [15:0] value);
        logic [4:0] exponent;
        logic [10:0] significand;
        logic signed [63:0] magnitude;
        logic signed [63:0] signed_value;
        integer shift_amount;
        begin
            exponent = value[14:10];
            significand = {1'b1, value[9:0]};
            if (exponent == 5'd0) begin
                magnitude = {54'b0, value[9:0]};
            end else if (exponent == 5'd31) begin
                magnitude = 64'sd0;
            end else begin
                shift_amount = int'(exponent) - 1;
                magnitude = {53'b0, significand} <<< shift_amount;
            end

            signed_value = value[15] ? -magnitude : magnitude;
            if (signed_value > 64'sd2147483647)
                fp16_to_q8_24 = 32'sh7fffffff;
            else if (signed_value < -64'sd2147483648)
                fp16_to_q8_24 = 32'sh80000000;
            else
                fp16_to_q8_24 = signed_value[31:0];
        end
    endfunction

    always_comb
        activation_scale_q8_24 = fp16_to_q8_24(activation_scale_fp16);

    function automatic logic signed [ACT_W-1:0] sparse_activation_lookup(
        input logic [256*ACT_W-1:0] window,
        input logic [7:0] index
    );
        logic [15:0] low_select;
        logic [15:0] high_select;
        logic [ACT_W-1:0] row_value [0:15];
        logic [ACT_W-1:0] selected_value;
        integer low_index;
        integer high_index;
        integer bit_index;
        begin
            low_select = '0;
            high_select = '0;
            for (low_index = 0; low_index < 16; low_index = low_index + 1)
                low_select[low_index] = (index[3:0] == 4'(low_index));
            for (high_index = 0; high_index < 16; high_index = high_index + 1)
                high_select[high_index] = (index[7:4] == 4'(high_index));

            for (high_index = 0; high_index < 16; high_index = high_index + 1) begin
                row_value[high_index] = '0;
                for (low_index = 0; low_index < 16; low_index = low_index + 1)
                    for (bit_index = 0; bit_index < ACT_W; bit_index = bit_index + 1)
                        row_value[high_index][bit_index] = row_value[high_index][bit_index] |
                            (window[(high_index*16+low_index)*ACT_W+bit_index] & low_select[low_index]);
            end

            selected_value = '0;
            for (high_index = 0; high_index < 16; high_index = high_index + 1)
                selected_value = selected_value | (row_value[high_index] & {ACT_W{high_select[high_index]}});
            sparse_activation_lookup = $signed(selected_value);
        end
    endfunction

    always_comb begin
        activation_subvector = '0;
        if (TRITS_PER_CYCLE == 64) begin
            activation_subvector[0 +: 64*ACT_W] =
                activation_window[subchunk_index*64*ACT_W +: 64*ACT_W];
        end else begin
            activation_subvector[0 +: 64*ACT_W] =
                activation_window[subchunk_index*64*ACT_W +: 64*ACT_W];
            activation_subvector[64*ACT_W +: 64*ACT_W] =
                activation_window[2'(subchunk_index + 2'd1)*64*ACT_W +: 64*ACT_W];
        end
    end

    genvar channel;
    generate
        for (channel = 0; channel < P_CH; channel = channel + 1) begin : gen_channel
            wire [TRITS_PER_CYCLE-1:0] subchunk_nz;
            wire [TRITS_PER_CYCLE-1:0] subchunk_sgn;
            wire [63:0] subchunk_nz0, subchunk_sgn0;
            wire [63:0] subchunk_nz1, subchunk_sgn1;
            wire [7:0] outlier_idx0, outlier_idx1;
            wire signed [15:0] outlier_val0_q4_12, outlier_val1_q4_12;
            wire signed [ACT_W-1:0] act_window_lookup0, act_window_lookup1;

            usw512_word_decoder u_word_decoder0 (
                .usw_word(usw_words[channel*512 +: 512]),
                .subchunk_index(subchunk_index),
                .subchunk_nz(subchunk_nz0), .subchunk_sgn(subchunk_sgn0),
                .outlier_idx(outlier_idx0), .outlier_val(outlier_val0_q4_12)
            );

            if (TRITS_PER_CYCLE == 128) begin : gen_second_subchunk
                usw512_word_decoder u_word_decoder1 (
                    .usw_word(usw_words[channel*512 +: 512]),
                    .subchunk_index(2'(subchunk_index + 2'd1)),
                    .subchunk_nz(subchunk_nz1), .subchunk_sgn(subchunk_sgn1),
                    .outlier_idx(outlier_idx1), .outlier_val(outlier_val1_q4_12)
                );
                assign subchunk_nz = {subchunk_nz1, subchunk_nz0};
                assign subchunk_sgn = {subchunk_sgn1, subchunk_sgn0};
                assign act_window_lookup1 =
                    sparse_activation_lookup(activation_window, outlier_idx1);
            end else begin : gen_single_subchunk
                assign subchunk_nz1 = '0;
                assign subchunk_sgn1 = '0;
                assign outlier_idx1 = '0;
                assign outlier_val1_q4_12 = '0;
                assign subchunk_nz = subchunk_nz0;
                assign subchunk_sgn = subchunk_sgn0;
                assign act_window_lookup1 = '0;
            end

            assign act_window_lookup0 =
                sparse_activation_lookup(activation_window, outlier_idx0);

            (* KEEP_HIERARCHY = "TRUE" *) usw512_dual_track_channel #(
                .TRITS_PER_CYCLE(TRITS_PER_CYCLE),
                .ACT_W(ACT_W), .ACC_W(ACC_W), .STATIC_REUSE(STATIC_REUSE)
            ) u_channel (
                .clk(clk),
                .rst_n(rst_n),
                .valid_in(valid_in),
                .first_subchunk(first_subchunk),
                .last_subchunk(last_subchunk),
                .subchunk_nz(subchunk_nz),
                .subchunk_sgn(subchunk_sgn),
                .outlier_val0_q4_12(outlier_val0_q4_12),
                .outlier_val1_q4_12(outlier_val1_q4_12),
                .act_subvec(activation_subvector),
                .act_window_lookup0(act_window_lookup0),
                .act_window_lookup1(act_window_lookup1),
                .fused_gamma_fp16(fused_gamma_fp16[channel*16 +: 16]),
                .activation_scale_q8_24(activation_scale_q8_24),
                .static_sum_enable(static_sum_enable),
                .static_sum_q12(static_sums_q12[channel*37 +: 37]),
                .row_done_valid(row_done_valid[channel]),
                .final_channel_out_q12(final_channels_q12[channel*32 +: 32]),
                .unscaled_sum_q12(unscaled_sums_q12[channel*37 +: 37])
            );
        end
    endgenerate

    initial begin
        if ((TRITS_PER_CYCLE != 64 && TRITS_PER_CYCLE != 128) || ACT_W != 8)
            $error("usw512_channel_array supports 64 or 128 trits per cycle at INT8");
    end
endmodule
