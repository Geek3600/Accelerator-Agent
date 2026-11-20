`timescale 1ns / 1ps

module tb_rtwsr_dual_track_gemv_array #(
    parameter int SLR_COUNT = 3,
    parameter int CHANNELS_PER_SLR = 32,
    parameter int TRITS_PER_CYCLE = 64,
    parameter int K = 17920,
    parameter int WINDOW_COUNT = K / 256,
    parameter int CHANNEL_COUNT = SLR_COUNT * CHANNELS_PER_SLR
)(
);
    logic clk = 1'b0;
    logic rst_n = 1'b0;
    logic valid_in = 1'b0;
    logic first_subchunk = 1'b0;
    logic last_subchunk = 1'b0;
    logic [1:0] subchunk_index = '0;
    logic [CHANNEL_COUNT*512-1:0] usw_words = '0;
    logic [256*8-1:0] activation_window = '0;
    logic [CHANNEL_COUNT*16-1:0] fused_gamma_fp16 = '0;
    logic [15:0] activation_scale_fp16 = 16'h3c00;
    logic [CHANNEL_COUNT-1:0] row_done_valid;
    logic [CHANNEL_COUNT*32-1:0] final_channels_q12;
    longint signed expected_q12 [0:CHANNEL_COUNT-1];
    longint signed expected_dense_total [0:CHANNEL_COUNT-1];
    longint signed expected_sparse_total [0:CHANNEL_COUNT-1];
    integer activation_value;
    integer trit_value;
    integer expected_dense;
    integer expected_sparse;
    integer sparse_index;
    integer total_comparisons = 0;
    integer channel;
    integer window_id;
    integer element;
    integer slot;
    integer cycle_id;
    integer result_seen = 0;

    always #5 clk = ~clk;

    function automatic integer trit_for(
        input integer channel_id,
        input integer window,
        input integer element_id
    );
        integer residue;
        begin
            residue = (channel_id*17 + window*19 + element_id*7) % 5;
            if (residue == 0)
                trit_for = 1;
            else if (residue == 1)
                trit_for = -1;
            else
                trit_for = 0;
        end
    endfunction

    function automatic integer activation_for(input integer window, input integer index);
        activation_for = ((window*37 + index*29) % 256) - 128;
    endfunction

    function automatic logic [511:0] make_weight_word(
        input integer channel_id,
        input integer window
    );
        logic [511:0] word_value;
        integer trit_index;
        integer byte_index;
        integer digit_index;
        integer radix_code;
        integer radix_place;
        integer trit;
        integer index_value;
        begin
            word_value = '0;
            for (integer sparse_slot = 0; sparse_slot < 4; sparse_slot = sparse_slot + 1) begin
                index_value = (channel_id*11 + window*13 + sparse_slot*47) % 256;
                word_value[sparse_slot*24 +: 16] = 16'h1000;
                word_value[sparse_slot*24+16 +: 8] = 8'(index_value);
            end
            for (byte_index = 0; byte_index < 51; byte_index = byte_index + 1) begin
                radix_code = 0;
                radix_place = 1;
                for (digit_index = 0; digit_index < 5; digit_index = digit_index + 1) begin
                    trit_index = byte_index*5 + digit_index;
                    trit = trit_for(channel_id, window, trit_index);
                    radix_code = radix_code + (trit + 1)*radix_place;
                    radix_place = radix_place * 3;
                end
                word_value[96 + byte_index*8 +: 8] = 8'(radix_code);
            end
            trit = trit_for(channel_id, window, 255);
            word_value[63*8 +: 8] = 8'(trit + 1);
            make_weight_word = word_value;
        end
    endfunction

    rtwsr_dual_track_gemv_array #(
        .SLR_COUNT(SLR_COUNT),
        .CHANNELS_PER_SLR(CHANNELS_PER_SLR),
        .TRITS_PER_CYCLE(TRITS_PER_CYCLE)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .valid_in(valid_in),
        .first_subchunk(first_subchunk),
        .last_subchunk(last_subchunk),
        .subchunk_index(subchunk_index),
        .usw_words(usw_words),
        .activation_window(activation_window),
        .fused_gamma_fp16(fused_gamma_fp16),
        .activation_scale_fp16(activation_scale_fp16),
        .row_done_valid(row_done_valid),
        .final_channels_q12(final_channels_q12)
    );

    always @(posedge clk) begin
        if (rst_n && |row_done_valid) begin
            if (row_done_valid != {CHANNEL_COUNT{1'b1}})
                $fatal(1, "%0d output channels did not complete in lockstep", CHANNEL_COUNT);
            for (integer output_channel = 0; output_channel < CHANNEL_COUNT; output_channel = output_channel + 1) begin
                if ($signed(final_channels_q12[output_channel*32 +: 32]) !== expected_q12[output_channel][31:0])
                    $fatal(1, "channel %0d mismatch: got %0d expected %0d; dense_hw=%0d sparse_hw=%0d dense_ref=%0d sparse_ref=%0d",
                        output_channel,
                        $signed(final_channels_q12[output_channel*32 +: 32]),
                        expected_q12[output_channel],
                        dut.gen_slr_array[0].u_channel_array.gen_channel[0].u_channel.dense_acc,
                        dut.gen_slr_array[0].u_channel_array.gen_channel[0].u_channel.sparse_acc,
                        expected_dense_total[output_channel], expected_sparse_total[output_channel]);
                total_comparisons = total_comparisons + 1;
            end
            result_seen = result_seen + 1;
        end
    end

    initial begin
        for (channel = 0; channel < CHANNEL_COUNT; channel = channel + 1) begin
            expected_q12[channel] = 0;
            expected_dense_total[channel] = 0;
            expected_sparse_total[channel] = 0;
            fused_gamma_fp16[channel*16 +: 16] = 16'h3c00;
        end
        repeat (5) @(negedge clk);
        rst_n = 1'b1;

        for (window_id = 0; window_id < WINDOW_COUNT; window_id = window_id + 1) begin
            for (channel = 0; channel < CHANNEL_COUNT; channel = channel + 1) begin
                expected_dense = 0;
                expected_sparse = 0;
                for (element = 0; element < 256; element = element + 1) begin
                    trit_value = trit_for(channel, window_id, element);
                    activation_value = activation_for(window_id, element);
                    expected_dense = expected_dense + trit_value*activation_value;
                end
                for (slot = 0; slot < 4; slot = slot + 1) begin
                    sparse_index = (channel*11 + window_id*13 + slot*47) % 256;
                    expected_sparse = expected_sparse + activation_for(window_id, sparse_index)*4096;
                end
                expected_q12[channel] = expected_q12[channel] + expected_dense*4096 + expected_sparse;
                expected_dense_total[channel] = expected_dense_total[channel] + expected_dense;
                expected_sparse_total[channel] = expected_sparse_total[channel] + expected_sparse;
            end

            for (slot = 0; slot < 4; slot = slot + TRITS_PER_CYCLE / 64) begin
                @(negedge clk);
                if (slot == 0) begin
                    for (channel = 0; channel < CHANNEL_COUNT; channel = channel + 1)
                        usw_words[channel*512 +: 512] = make_weight_word(channel, window_id);
                    for (element = 0; element < 256; element = element + 1)
                        activation_window[element*8 +: 8] = 8'(activation_for(window_id, element));
                end
                valid_in = 1'b1;
                first_subchunk = (window_id == 0 && slot == 0);
                last_subchunk = (window_id == WINDOW_COUNT-1 &&
                    slot + TRITS_PER_CYCLE / 64 == 4);
                subchunk_index = 2'(slot);
                #1;
                for (element = 0; element < TRITS_PER_CYCLE; element = element + 1) begin
                    trit_value = trit_for(0, window_id, slot*64 + element);
                    if (dut.gen_slr_array[0].u_channel_array.gen_channel[0].subchunk_nz[element] !==
                            (trit_value != 0) ||
                        dut.gen_slr_array[0].u_channel_array.gen_channel[0].subchunk_sgn[element] !==
                            (trit_value < 0))
                        $fatal(1, "lane decoder mismatch at window %0d subchunk %0d element %0d",
                            window_id, slot, element);
                    if ($signed(dut.gen_slr_array[0].u_channel_array.activation_subvector[element*8 +: 8]) !==
                            activation_for(window_id, slot*64 + element) ||
                        $signed(dut.gen_slr_array[0].u_channel_array.gen_channel[0].u_channel.u_dense_track.term_comb[element]) !==
                            trit_value*activation_for(window_id, slot*64 + element))
                        $fatal(1, "lane term mismatch at window %0d subchunk %0d element %0d",
                            window_id, slot, element);
                end
                sparse_index = (window_id*13 + slot*47) % 256;
                if (dut.gen_slr_array[0].u_channel_array.gen_channel[0].outlier_idx0 !== 8'(sparse_index) ||
                    dut.gen_slr_array[0].u_channel_array.gen_channel[0].outlier_val0_q4_12 !== 16'sh1000 ||
                    dut.gen_slr_array[0].u_channel_array.gen_channel[0].act_window_lookup0 !==
                        8'(activation_for(window_id, sparse_index)))
                    $fatal(1, "lane sparse decoder mismatch at window %0d subchunk %0d", window_id, slot);
                if (TRITS_PER_CYCLE == 128) begin
                    sparse_index = (window_id*13 + (slot+1)*47) % 256;
                    if (dut.gen_slr_array[0].u_channel_array.gen_channel[0].outlier_idx1 !== 8'(sparse_index) ||
                        dut.gen_slr_array[0].u_channel_array.gen_channel[0].outlier_val1_q4_12 !== 16'sh1000 ||
                        dut.gen_slr_array[0].u_channel_array.gen_channel[0].act_window_lookup1 !==
                            8'(activation_for(window_id, sparse_index)))
                        $fatal(1, "second sparse decoder mismatch at window %0d subchunk %0d", window_id, slot);
                end
                @(posedge clk);
            end
        end

        @(negedge clk);
        valid_in = 1'b0;
        first_subchunk = 1'b0;
        last_subchunk = 1'b0;
        repeat (12) @(negedge clk);
        if (result_seen != 1 || total_comparisons != CHANNEL_COUNT)
            $fatal(1, "expected one aligned result for %0d channels; saw %0d results and %0d comparisons",
                CHANNEL_COUNT, result_seen, total_comparisons);

        $display("PASS: full K=%0d, %0d SLR x %0d channels, %0d trits/cycle, %0d USW-512 windows, %0d Q12 outputs",
            K, SLR_COUNT, CHANNELS_PER_SLR, TRITS_PER_CYCLE, WINDOW_COUNT, total_comparisons);
        $finish;
    end
endmodule
