`timescale 1ns / 1ps

module tb_usw512_array;
    localparam int P_CH = 32;
    localparam int MAX_K = 17920;
    localparam int WINDOW_COUNT = MAX_K / 256;

    logic clk = 1'b0;
    logic rst_n = 1'b0;
    logic valid_in = 1'b0;
    logic first_subchunk = 1'b0;
    logic last_subchunk = 1'b0;
    logic [1:0] subchunk_index = 2'b0;
    logic [P_CH*512-1:0] usw_words;
    logic [2047:0] activation_window;
    logic [P_CH*16-1:0] fused_gamma_fp16 = '0;
    logic [15:0] activation_scale_fp16 = 16'h3c00;
    logic [P_CH-1:0] row_done_valid;
    logic [P_CH*32-1:0] final_channels_q12;
    logic [7:0] packed_byte;
    logic [4:0] decoded_nz;
    logic [4:0] decoded_sgn;
    longint signed expected_dense [0:P_CH-1];
    longint signed expected_sparse_q12 [0:P_CH-1];
    logic signed [127:0] expected_merge;
    logic signed [127:0] expected_product;
    logic signed [127:0] expected_result;
    logic [127:0] expected_magnitude;
    logic [127:0] expected_rounded_magnitude;
    logic [511:0] record;
    integer code;
    integer value;
    integer remainder;
    integer trit_position;
    logic [4:0] expected_nz;
    logic [4:0] expected_sgn;
    integer first_sparse_idx;
    integer second_sparse_idx;
    integer done_seen;
    integer tie_even_seen;
    integer tie_odd_seen;
    integer channel;
    integer window_index;
    integer subchunk;
    integer index;

    always #5 clk <= ~clk;

    radix3_5trit_decoder u_radix3_decoder (
        .packed_byte(packed_byte),
        .trit_nz(decoded_nz),
        .trit_sgn(decoded_sgn)
    );

    usw512_channel_array #(
        .P_CH(P_CH),
        .ACT_W(8),
        .ACC_W(24)
    ) u_array (
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

    function automatic integer activation_value(input integer window, input integer offset);
        activation_value = ((window*37 + offset*29) % 256) - 128;
    endfunction

    function automatic integer ternary_value(
        input integer output_channel,
        input integer window,
        input integer offset
    );
        integer first_idx;
        integer second_idx;
        integer pattern;
        begin
            first_idx = (output_channel*7 + window*13) % 256;
            second_idx = (first_idx + 97) % 256;
            pattern = (output_channel*13 + window*7 + offset*3) % 11;
            if (output_channel < 2)
                ternary_value = 0;
            else if (offset == first_idx || offset == second_idx)
                ternary_value = 0;
            else if (pattern < 2)
                ternary_value = -1;
            else if (pattern < 4)
                ternary_value = 1;
            else
                ternary_value = 0;
        end
    endfunction

    task automatic make_record(
        input integer output_channel,
        input integer window,
        output logic [511:0] packed_record
    );
        integer byte_index;
        integer digit_index;
        integer radix_code;
        integer radix_place;
        integer offset;
        integer trit;
        integer first_idx;
        integer second_idx;
            logic [7:0] first_slot_idx;
            logic [7:0] second_slot_idx;
            logic [15:0] first_slot_value;
            logic [15:0] second_slot_value;
        begin
            packed_record = '0;
            for (byte_index = 0; byte_index < 51; byte_index = byte_index + 1) begin
                radix_code = 0;
                radix_place = 1;
                for (digit_index = 0; digit_index < 5; digit_index = digit_index + 1) begin
                    offset = byte_index*5 + digit_index;
                    trit = ternary_value(output_channel, window, offset);
                    radix_code = radix_code + (trit + 1)*radix_place;
                    radix_place = radix_place*3;
                end
                packed_record[96 + byte_index*8 +: 8] = radix_code[7:0];
            end

            trit = ternary_value(output_channel, window, 255);
            packed_record[96 + 51*8 +: 8] = 8'(trit + 1);

            first_idx = (output_channel*7 + window*13) % 256;
            second_idx = (first_idx + 97) % 256;
            first_slot_idx = first_idx[7:0];
            second_slot_idx = second_idx[7:0];
            first_slot_value = 16'h1000;
            second_slot_value = 16'hf800;
            if (output_channel < 2) begin
                first_slot_value = '0;
                second_slot_value = '0;
                if (output_channel == 0 && window == 0)
                    second_slot_value = 16'h1001;
                else if (output_channel == 1 && window == 0)
                    first_slot_value = 16'h1001;
            end
            if (first_slot_value == 0)
                first_slot_idx = '0;
            if (second_slot_value == 0)
                second_slot_idx = '0;
            packed_record[23:0] = {first_slot_idx, first_slot_value};
            packed_record[47:24] = {second_slot_idx, second_slot_value};
        end
    endtask

    task automatic set_activation_window(input integer window);
        integer offset;
        begin
            for (offset = 0; offset < 256; offset = offset + 1)
                activation_window[offset*8 +: 8] = 8'(activation_value(window, offset));
        end
    endtask

    initial begin
        packed_byte = '0;
        activation_window = '0;
        for (code = 0; code < 256; code = code + 1) begin
            packed_byte = code[7:0];
            #1;
            value = (code <= 242) ? code : 121;
            expected_nz = 0;
            expected_sgn = 0;
            for (trit_position = 0; trit_position < 5; trit_position = trit_position + 1) begin
                remainder = value % 3;
                value = value / 3;
                expected_nz[trit_position] = (remainder != 1);
                expected_sgn[trit_position] = (remainder == 0);
            end
            if (decoded_nz !== expected_nz[4:0] || decoded_sgn !== expected_sgn[4:0])
                $fatal(1, "Radix-3 mismatch for byte %0d", code);
        end

        for (channel = 0; channel < P_CH; channel = channel + 1) begin
            expected_dense[channel] = 0;
            expected_sparse_q12[channel] = 0;
            usw_words[channel*512 +: 512] = '0;
            fused_gamma_fp16[channel*16 +: 16] = 16'h3800;
        end

        repeat (3) @(posedge clk);
        @(negedge clk);
        rst_n = 1'b1;

        for (window_index = 0; window_index < WINDOW_COUNT; window_index = window_index + 1) begin
            set_activation_window(window_index);
            for (channel = 0; channel < P_CH; channel = channel + 1) begin
                make_record(channel, window_index, record);
                usw_words[channel*512 +: 512] = record;

                first_sparse_idx = (channel*7 + window_index*13) % 256;
                second_sparse_idx = (first_sparse_idx + 97) % 256;
                for (index = 0; index < 256; index = index + 1)
                    expected_dense[channel] =
                        expected_dense[channel] +
                        ternary_value(channel, window_index, index) *
                        activation_value(window_index, index);
                if (channel == 0 && window_index == 0)
                    expected_sparse_q12[channel] =
                        expected_sparse_q12[channel] +
                        activation_value(window_index, second_sparse_idx)*4097;
                else if (channel == 1 && window_index == 0)
                    expected_sparse_q12[channel] =
                        expected_sparse_q12[channel] +
                        activation_value(window_index, first_sparse_idx)*4097;
                else if (channel >= 2)
                    expected_sparse_q12[channel] =
                        expected_sparse_q12[channel] +
                        activation_value(window_index, first_sparse_idx)*4096 +
                        activation_value(window_index, second_sparse_idx)*(-2048);
            end

            for (subchunk = 0; subchunk < 4; subchunk = subchunk + 1) begin
                @(negedge clk);
                valid_in = 1'b1;
                first_subchunk = (window_index == 0 && subchunk == 0);
                last_subchunk =
                    (window_index == WINDOW_COUNT-1 && subchunk == 3);
                subchunk_index = subchunk[1:0];
                @(posedge clk);
                #1;
            end
        end

        @(negedge clk);
        valid_in = 1'b0;
        first_subchunk = 1'b0;
        last_subchunk = 1'b0;
        done_seen = 0;
        tie_even_seen = 0;
        tie_odd_seen = 0;
        for (index = 0; index < 8; index = index + 1) begin
            @(posedge clk);
            #1;
            if (|row_done_valid) begin
                if (row_done_valid !== {P_CH{1'b1}})
                    $fatal(1, "channel completion was not cycle-aligned");
                for (channel = 0; channel < P_CH; channel = channel + 1) begin
                    expected_merge =
                        {{64{expected_dense[channel][63]}}, expected_dense[channel]};
                    expected_merge = expected_merge <<< 12;
                    expected_merge = expected_merge +
                        {{64{expected_sparse_q12[channel][63]}}, expected_sparse_q12[channel]};
                    expected_product = expected_merge * 128'sd140737488355328;
                    expected_magnitude = expected_product[127]
                        ? -expected_product
                        : expected_product;
                    expected_rounded_magnitude = expected_magnitude >> 48;
                    if (expected_magnitude[47] && !(|expected_magnitude[46:0])) begin
                        if (expected_rounded_magnitude[0])
                            tie_odd_seen = tie_odd_seen + 1;
                        else
                            tie_even_seen = tie_even_seen + 1;
                    end
                    if (expected_magnitude[47] &&
                        ((|expected_magnitude[46:0]) || expected_rounded_magnitude[0]))
                        expected_rounded_magnitude = expected_rounded_magnitude + 1'b1;
                    expected_result = expected_product[127]
                        ? -$signed(expected_rounded_magnitude)
                        : $signed(expected_rounded_magnitude);
                    if (expected_result[127:32] !== {96{expected_result[31]}})
                        $fatal(1, "channel %0d reference exceeds signed 32-bit Q12", channel);
                    if ($signed(final_channels_q12[channel*32 +: 32]) !== expected_result[31:0])
                        $fatal(
                            1,
                            "channel %0d mismatch: got %0d expected %0d",
                            channel,
                            $signed(final_channels_q12[channel*32 +: 32]),
                            expected_result[31:0]
                        );
                end
                done_seen = done_seen + 1;
            end
        end
        if (done_seen != 1)
            $fatal(1, "expected one row completion pulse, got %0d", done_seen);
        if (tie_even_seen == 0 || tie_odd_seen == 0)
            $fatal(1, "expected both round-to-even tie cases, got even=%0d odd=%0d", tie_even_seen, tie_odd_seen);

        $display(
            "PASS: 256 radix bytes, P_CH=%0d, K=%0d, RNE ties even=%0d odd=%0d",
            P_CH,
            MAX_K,
            tie_even_seen,
            tie_odd_seen
        );
        $finish;
    end
endmodule

`ifdef SYNTH_CARRY8
module CARRY8 #(
    parameter CARRY_TYPE = "SINGLE_CY8"
)(
    input  logic       CI,
    input  logic       CI_TOP,
    input  logic [7:0] DI,
    input  logic [7:0] S,
    output logic [7:0] CO,
    output logic [7:0] O
);
    logic carry;

    always_comb begin
        carry = CI;
        for (integer bit_index = 0; bit_index < 8; bit_index = bit_index + 1) begin
            O[bit_index] = S[bit_index] ^ carry;
            CO[bit_index] = S[bit_index] ? carry : DI[bit_index];
            carry = CO[bit_index];
        end
    end
endmodule
`endif
