`timescale 1ns / 1ps

module rtwsr_dual_track_gemv_array #(
    parameter int SLR_COUNT = 3,
    parameter int CHANNELS_PER_SLR = 32,
    parameter int TRITS_PER_CYCLE = 64,
    parameter int ACT_W = 8,
    parameter int ACC_W = 24,
    parameter bit STATIC_REUSE = 1'b0
)(
    input  logic                                      clk,
    input  logic                                      rst_n,
    input  logic                                      valid_in,
    input  logic                                      first_subchunk,
    input  logic                                      last_subchunk,
    input  logic [1:0]                                subchunk_index,
    input  logic [SLR_COUNT*CHANNELS_PER_SLR*512-1:0] usw_words,
    input  logic [256*ACT_W-1:0]                      activation_window,
    input  logic [SLR_COUNT*CHANNELS_PER_SLR*16-1:0]  fused_gamma_fp16,
    input  logic [15:0]                               activation_scale_fp16,
    input  logic                                      static_sum_enable,
    input  logic [SLR_COUNT*CHANNELS_PER_SLR*37-1:0] static_sums_q12,
    output logic [SLR_COUNT*CHANNELS_PER_SLR-1:0]     row_done_valid,
    output logic [SLR_COUNT*CHANNELS_PER_SLR*32-1:0]  final_channels_q12,
    output logic [SLR_COUNT*CHANNELS_PER_SLR*37-1:0]  unscaled_sums_q12
);
    genvar slr;
    generate
        for (slr = 0; slr < SLR_COUNT; slr = slr + 1) begin : gen_slr_array
            usw512_channel_array #(
                .P_CH(CHANNELS_PER_SLR),
                .TRITS_PER_CYCLE(TRITS_PER_CYCLE),
                .ACT_W(ACT_W),
                .ACC_W(ACC_W),
                .STATIC_REUSE(STATIC_REUSE)
            ) u_channel_array (
                .clk(clk),
                .rst_n(rst_n),
                .valid_in(valid_in),
                .first_subchunk(first_subchunk),
                .last_subchunk(last_subchunk),
                .subchunk_index(subchunk_index),
                .usw_words(usw_words[slr*CHANNELS_PER_SLR*512 +: CHANNELS_PER_SLR*512]),
                .activation_window(activation_window),
                .fused_gamma_fp16(fused_gamma_fp16[slr*CHANNELS_PER_SLR*16 +: CHANNELS_PER_SLR*16]),
                .activation_scale_fp16(activation_scale_fp16),
                .static_sum_enable(static_sum_enable),
                .static_sums_q12(static_sums_q12[slr*CHANNELS_PER_SLR*37 +: CHANNELS_PER_SLR*37]),
                .row_done_valid(row_done_valid[slr*CHANNELS_PER_SLR +: CHANNELS_PER_SLR]),
                .final_channels_q12(final_channels_q12[slr*CHANNELS_PER_SLR*32 +: CHANNELS_PER_SLR*32]),
                .unscaled_sums_q12(unscaled_sums_q12[slr*CHANNELS_PER_SLR*37 +: CHANNELS_PER_SLR*37])
            );
        end
    endgenerate

    initial begin
        if (SLR_COUNT != 3 || (CHANNELS_PER_SLR != 32 && CHANNELS_PER_SLR != 64) ||
            (TRITS_PER_CYCLE != 64 && TRITS_PER_CYCLE != 128) || ACT_W != 8)
            $error("Plan 6 array geometry supports 3 SLRs x 32 or 64 INT8 channels and 64/128 trits per cycle");
    end
endmodule
