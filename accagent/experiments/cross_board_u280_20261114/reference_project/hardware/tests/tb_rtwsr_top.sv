`timescale 1ns / 1ps

module rtwsr_top_full_testbench #(
    parameter bit USE_PLAN5_PAYLOAD = 1'b0,
    parameter bit USE_STREAMING_CLUSTER = 1'b0
);
    localparam int SLR_COUNT = 3;
    localparam int P_CH = 32;
    localparam int C_OUT_PER_SLR = 1760;
    localparam int C_OUT = SLR_COUNT * C_OUT_PER_SLR;
    localparam int K = 17920;
    localparam int WINDOW_COUNT = K / 256;
    localparam int TILE_COUNT = C_OUT_PER_SLR / P_CH;
    localparam int ROUNDS = 32;
    localparam int CHANNEL_WIDTH = $clog2(C_OUT_PER_SLR);
    localparam int WINDOW_WIDTH = $clog2(WINDOW_COUNT);
    localparam int TILE_WIDTH = $clog2(TILE_COUNT);
    localparam int ROUND_WIDTH = $clog2(ROUNDS);

    logic clk = 1'b0;
    logic rst_n = 1'b0;
    logic [SLR_COUNT-1:0] weight_load_valid = '0;
    logic [SLR_COUNT-1:0] weight_load_ready;
    logic [CHANNEL_WIDTH-1:0] weight_load_channel;
    logic [WINDOW_WIDTH-1:0] weight_load_window;
    logic [SLR_COUNT-1:0][511:0] weight_load_data;
    logic weight_stream_start = 1'b0;
    logic weight_stream_valid = 1'b0;
    logic weight_stream_ready;
    logic [511:0] weight_stream_data = '0;
    logic weight_stream_last = 1'b0;
    logic weight_store_busy;
    logic weight_store_load_done;
    logic weight_store_protocol_error;
    logic [16:0] shadow_occupancy;
    logic [SLR_COUNT-1:0] round_config_valid = '0;
    logic [SLR_COUNT-1:0] round_config_ready;
    logic [SLR_COUNT-1:0][P_CH*16-1:0] round_gamma_fp16;
    logic [SLR_COUNT-1:0][15:0] round_activation_scale_fp16;
    logic [SLR_COUNT-1:0] activation_valid = '0;
    logic [SLR_COUNT-1:0] activation_ready;
    logic [SLR_COUNT-1:0][256*8-1:0] activation_window;
    logic [SLR_COUNT-1:0] tile_result_valid;
    logic [SLR_COUNT-1:0][TILE_WIDTH-1:0] output_tile_index;
    logic [SLR_COUNT-1:0][P_CH*32-1:0] tile_result_q12;
    logic [SLR_COUNT-1:0] round_result_valid;
    logic [SLR_COUNT-1:0][ROUND_WIDTH-1:0] round_index;
    logic [SLR_COUNT-1:0] done;

    longint signed expected_dense [0:C_OUT-1];
    longint signed expected_sparse_q12 [0:C_OUT-1];
    logic [511:0] payload_records [0:C_OUT*WINDOW_COUNT-1];
    logic [15:0] payload_gamma [0:C_OUT*ROUNDS-1];
    logic signed [31:0] payload_expected [0:C_OUT*ROUNDS-1];
    integer cycle_count = 0;
    integer comparisons = 0;
    integer activation_accepts = 0;
    integer first_window_cycle = -1;
    integer first_steady_window_interval = -1;
    integer second_steady_window_interval = -1;
    integer previous_window_cycle = -1;
    integer load_start_cycle;
    integer load_done_cycle;
    integer run_start_cycle;
    integer run_done_cycle;
    integer last_tile_cycle;
    integer round_start_cycle;
    integer first_tile_round_cycles = 0;
    integer steady_tile_round_cycles = 0;
    integer channel;
    integer window;
    integer round_num;
    integer tile;
    integer slr;
    integer offset;
    integer trit_offset;
    integer trit;
    integer idx_a;
    integer idx_b;
    integer idx_c;
    integer idx_d;
    integer record_byte;
    integer digit;
    integer code;
    integer place;
    integer global_channel;
    integer expected_value;
    integer received_value;
    integer lane;
    logic [511:0] record_word;

    always #5 clk = ~clk;
    always @(posedge clk) cycle_count <= cycle_count + 1;

    genvar slr_index;
    generate
        if (USE_STREAMING_CLUSTER) begin : gen_streaming_cluster
            rtwsr_recurrent_linear_cluster #(
                .SLR_COUNT(SLR_COUNT),
                .CHANNELS_PER_SLR(P_CH),
                .C_OUT_PER_SLR(C_OUT_PER_SLR),
                .K(K),
                .ROUNDS(ROUNDS),
                .RING_DEPTH(73728)
            ) dut (
                .clk(clk),
                .rst_n(rst_n),
                .weight_start(weight_stream_start),
                .weight_abort(1'b0),
                .weight_stream_valid(weight_stream_valid),
                .weight_stream_ready(weight_stream_ready),
                .weight_stream_data(weight_stream_data),
                .weight_stream_last(weight_stream_last),
                .weight_store_busy(weight_store_busy),
                .weight_load_done(weight_store_load_done),
                .weight_protocol_error(weight_store_protocol_error),
                .shadow_occupancy(shadow_occupancy),
                .round_config_valid(round_config_valid),
                .round_config_ready(round_config_ready),
                .round_gamma_fp16(round_gamma_fp16),
                .round_activation_scale_fp16(round_activation_scale_fp16[0]),
                .activation_valid(activation_valid),
                .activation_ready(activation_ready),
                .activation_window(activation_window[0]),
                .tile_result_valid(tile_result_valid),
                .output_tile_index(output_tile_index),
                .tile_result_q12(tile_result_q12),
                .round_result_valid(round_result_valid),
                .round_index(round_index),
                .done(done)
            );
        end else begin : gen_independent_slrs
            for (slr_index = 0; slr_index < SLR_COUNT; slr_index = slr_index + 1) begin : gen_slr
                rtwsr_top #(
                    .P_CH(P_CH),
                    .C_OUT(C_OUT_PER_SLR),
                    .K(K),
                    .ROUNDS(ROUNDS)
                ) dut (
                    .clk(clk),
                    .rst_n(rst_n),
                    .weight_load_valid(weight_load_valid[slr_index]),
                    .weight_load_ready(weight_load_ready[slr_index]),
                    .weight_load_channel(weight_load_channel),
                    .weight_load_window(weight_load_window),
                    .weight_load_data(weight_load_data[slr_index]),
                    .round_config_valid(round_config_valid[slr_index]),
                    .round_config_ready(round_config_ready[slr_index]),
                    .round_gamma_fp16(round_gamma_fp16[slr_index]),
                    .round_activation_scale_fp16(round_activation_scale_fp16[slr_index]),
                    .activation_valid(activation_valid[slr_index]),
                    .activation_ready(activation_ready[slr_index]),
                    .activation_window(activation_window[slr_index]),
                    .tile_result_valid(tile_result_valid[slr_index]),
                    .output_tile_index(output_tile_index[slr_index]),
                    .tile_result_q12(tile_result_q12[slr_index]),
                    .round_result_valid(round_result_valid[slr_index]),
                    .round_index(round_index[slr_index]),
                    .done(done[slr_index])
                );
            end
        end
    endgenerate

    function automatic integer activation_value(input integer window_id, input integer index);
        activation_value = ((window_id * 37 + index * 29) % 256) - 128;
    endfunction

    function automatic integer ternary_value(
        input integer output_channel,
        input integer window_id,
        input integer index
    );
        integer base;
        begin
            base = (output_channel * 7 + window_id * 13) % 256;
            if (index == (base + 31) % 256)
                ternary_value = ((output_channel + window_id) % 2) ? 1 : -1;
            else if (index == (base + 97) % 256)
                ternary_value = ((output_channel + window_id) % 3) ? -1 : 1;
            else if (index == (base + 173) % 256)
                ternary_value = ((output_channel + window_id) % 2) ? -1 : 1;
            else
                ternary_value = 0;
        end
    endfunction

    function automatic logic [511:0] make_record(
        input integer output_channel,
        input integer window_id
    );
        logic [511:0] packed_record;
        integer trit_index;
        integer digit_value;
        integer radix_place;
        integer radix_code;
        integer sparse_a;
        integer sparse_b;
        integer base;
        begin
            packed_record = '0;
            for (integer byte_id = 0; byte_id < 51; byte_id = byte_id + 1) begin
                radix_code = 0;
                radix_place = 1;
                for (integer digit_id = 0; digit_id < 5; digit_id = digit_id + 1) begin
                    trit_index = byte_id * 5 + digit_id;
                    digit_value = ternary_value(output_channel, window_id, trit_index) + 1;
                    radix_code = radix_code + digit_value * radix_place;
                    radix_place = radix_place * 3;
                end
                packed_record[96 + byte_id*8 +: 8] = 8'(radix_code);
            end

            digit_value = ternary_value(output_channel, window_id, 255) + 1;
            packed_record[96 + 51*8 +: 8] = 8'(digit_value);

            base = (output_channel * 7 + window_id * 13) % 256;
            sparse_a = (base + 11) % 256;
            sparse_b = (base + 143) % 256;
            packed_record[15:0] = 16'h1000;
            packed_record[23:16] = 8'(sparse_a);
            packed_record[39:24] = 16'hf800;
            packed_record[47:40] = 8'(sparse_b);
            return packed_record;
        end
    endfunction

    function automatic logic [256*8-1:0] make_activation_window(input integer window_id);
        logic [256*8-1:0] result;
        begin
            for (integer element = 0; element < 256; element = element + 1)
                result[element*8 +: 8] = 8'(activation_value(window_id, element));
            return result;
        end
    endfunction

    task automatic check_tile(input integer expected_tile, input integer expected_round);
        integer local_channel;
        integer slr_id;
        integer global_id;
        logic [SLR_COUNT-1:0] seen;
        begin
            seen = '0;
            while (seen != {SLR_COUNT{1'b1}}) begin
                @(posedge clk);
                #1;
                for (slr_id = 0; slr_id < SLR_COUNT; slr_id = slr_id + 1) begin
                    if (tile_result_valid[slr_id]) begin
                        if (seen[slr_id])
                            $fatal(1, "duplicate tile result from SLR %0d", slr_id);
                        if (output_tile_index[slr_id] !== TILE_WIDTH'(expected_tile))
                            $fatal(1, "SLR %0d tile index mismatch", slr_id);
                        seen[slr_id] = 1'b1;
                        for (local_channel = 0; local_channel < P_CH; local_channel = local_channel + 1) begin
                            global_id = slr_id*C_OUT_PER_SLR + expected_tile*P_CH + local_channel;
                            if (USE_PLAN5_PAYLOAD)
                                expected_value = payload_expected[expected_round*C_OUT + global_id];
                            else
                                expected_value = expected_dense[global_id]*4096 + expected_sparse_q12[global_id];
                            received_value = $signed(tile_result_q12[slr_id][local_channel*32 +: 32]);
                            if (received_value != expected_value) begin
                                $fatal(
                                    1,
                                    "round=%0d tile=%0d SLR=%0d channel=%0d got=%0d expected=%0d dense=%0d sparse_q12=%0d",
                                    expected_round,
                                    expected_tile,
                                    slr_id,
                                    local_channel,
                                    received_value,
                                    expected_value,
                                    expected_dense[global_id],
                                    expected_sparse_q12[global_id]
                                );
                            end
                            comparisons = comparisons + 1;
                        end
                        if ((expected_tile == TILE_COUNT-1) != round_result_valid[slr_id])
                            $fatal(1, "SLR %0d round-result pulse mismatch at tile %0d", slr_id, expected_tile);
                        if (round_result_valid[slr_id] && round_index[slr_id] != ROUND_WIDTH'(expected_round))
                            $fatal(1, "SLR %0d round index mismatch", slr_id);
                    end
                end
            end
        end
    endtask

    task automatic preload_streaming_cluster;
        begin
            @(negedge clk);
            weight_stream_start = 1'b1;
            @(posedge clk);
            @(negedge clk);
            weight_stream_start = 1'b0;

            for (channel = 0; channel < C_OUT; channel = channel + 1) begin
                for (window = 0; window < WINDOW_COUNT; window = window + 1) begin
                    @(negedge clk);
                    weight_stream_valid = 1'b1;
                    weight_stream_data = USE_PLAN5_PAYLOAD
                        ? payload_records[channel*WINDOW_COUNT + window]
                        : make_record(channel, window);
                    weight_stream_last = (channel == C_OUT-1 && window == WINDOW_COUNT-1);
                    while (!weight_stream_ready)
                        @(negedge clk);
                    @(posedge clk);
                    #1;

                    if (!USE_PLAN5_PAYLOAD) begin
                        idx_a = (channel*7 + window*13 + 11) % 256;
                        idx_b = (channel*7 + window*13 + 143) % 256;
                        expected_sparse_q12[channel] = expected_sparse_q12[channel] +
                            activation_value(window, idx_a)*4096 + activation_value(window, idx_b)*(-2048);
                        for (integer dense_lane = 0; dense_lane < 3; dense_lane = dense_lane + 1) begin
                            case (dense_lane)
                                0: trit_offset = (channel*7 + window*13 + 31) % 256;
                                1: trit_offset = (channel*7 + window*13 + 97) % 256;
                                default: trit_offset = (channel*7 + window*13 + 173) % 256;
                            endcase
                            trit = ternary_value(channel, window, trit_offset);
                            expected_dense[channel] = expected_dense[channel] +
                                trit*activation_value(window, trit_offset);
                        end
                    end
                end
            end

            @(negedge clk);
            weight_stream_valid = 1'b0;
            weight_stream_last = 1'b0;
            while (!weight_store_load_done) begin
                @(posedge clk);
                #1;
            end
            if (weight_store_protocol_error || weight_store_busy)
                $fatal(1, "streaming weight load ended with busy or protocol error");
            load_done_cycle = cycle_count;
        end
    endtask

    initial begin
        if (USE_PLAN5_PAYLOAD) begin
            $readmemh("payload_words.mem", payload_records);
            $readmemh("payload_gamma.mem", payload_gamma);
            $readmemh("payload_expected.mem", payload_expected);
        end

        for (slr = 0; slr < SLR_COUNT; slr = slr + 1) begin
            round_gamma_fp16[slr] = {P_CH{16'h3c00}};
            round_activation_scale_fp16[slr] = 16'h3c00;
            activation_window[slr] = '0;
            weight_load_data[slr] = '0;
        end
        weight_load_channel = '0;
        weight_load_window = '0;
        for (channel = 0; channel < C_OUT; channel = channel + 1) begin
            expected_dense[channel] = 0;
            expected_sparse_q12[channel] = 0;
        end

        repeat (4) @(posedge clk);
        @(negedge clk);
        rst_n = 1'b1;
        load_start_cycle = cycle_count;

        if (USE_STREAMING_CLUSTER) begin
            preload_streaming_cluster();
        end else begin
        for (channel = 0; channel < C_OUT_PER_SLR; channel = channel + 1) begin
            for (window = 0; window < WINDOW_COUNT; window = window + 1) begin
                @(negedge clk);
                weight_load_valid = {SLR_COUNT{1'b1}};
                weight_load_channel = CHANNEL_WIDTH'(channel);
                weight_load_window = WINDOW_WIDTH'(window);
                for (slr = 0; slr < SLR_COUNT; slr = slr + 1) begin
                    global_channel = slr*C_OUT_PER_SLR + channel;
                    if (USE_PLAN5_PAYLOAD)
                        weight_load_data[slr] = payload_records[global_channel*WINDOW_COUNT + window];
                    else
                        weight_load_data[slr] = make_record(global_channel, window);

`ifndef PLAN6_CLUSTER_TEST
                    if (USE_PLAN5_PAYLOAD && slr == 0 &&
                        ((channel == 0 && window == 0) || (channel == 1731 && window == WINDOW_COUNT-1))) begin
                        if (weight_load_channel !== CHANNEL_WIDTH'(channel) ||
                            weight_load_window !== WINDOW_WIDTH'(window))
                            $fatal(1, "testbench address drive mismatch: channel=%0d window=%0d signal=%0d/%0d",
                                channel, window,
                                weight_load_channel,
                                weight_load_window);
                        #1;
                        if (channel == 0) begin
                            if (gen_independent_slrs.gen_slr[0].dut.gen_weight_bank[0].u_active_pool_bank.mapped_addr !==
                                    14'(((channel/32*WINDOW_COUNT + window)*4) + channel%4) ||
                                gen_independent_slrs.gen_slr[0].dut.gen_weight_bank[0].group_wr_en !== 1'b1)
                                $fatal(1, "channel/window did not reach active bank 0: channel=%0d window=%0d address=%0d write=%b",
                                    channel, window,
                                    gen_independent_slrs.gen_slr[0].dut.gen_weight_bank[0].u_active_pool_bank.mapped_addr,
                                    gen_independent_slrs.gen_slr[0].dut.gen_weight_bank[0].group_wr_en);
                        end else begin
                            if (gen_independent_slrs.gen_slr[0].dut.gen_weight_bank[0].u_active_pool_bank.mapped_addr !==
                                    14'(((channel/32*WINDOW_COUNT + window)*4) + channel%4) ||
                                gen_independent_slrs.gen_slr[0].dut.gen_weight_bank[0].group_wr_en !== 1'b1)
                                $fatal(1, "channel/window did not reach active bank 0: channel=%0d window=%0d address=%0d write=%b",
                                    channel, window,
                                    gen_independent_slrs.gen_slr[0].dut.gen_weight_bank[0].u_active_pool_bank.mapped_addr,
                                    gen_independent_slrs.gen_slr[0].dut.gen_weight_bank[0].group_wr_en);
                        end
                    end
`endif

                    if (!USE_PLAN5_PAYLOAD) begin
                        idx_a = (global_channel*7 + window*13 + 11) % 256;
                        idx_b = (global_channel*7 + window*13 + 143) % 256;
                        expected_sparse_q12[global_channel] = expected_sparse_q12[global_channel] +
                            activation_value(window, idx_a)*4096 + activation_value(window, idx_b)*(-2048);
                        for (integer dense_lane = 0; dense_lane < 3; dense_lane = dense_lane + 1) begin
                            case (dense_lane)
                                0: trit_offset = (global_channel*7 + window*13 + 31) % 256;
                                1: trit_offset = (global_channel*7 + window*13 + 97) % 256;
                                default: trit_offset = (global_channel*7 + window*13 + 173) % 256;
                            endcase
                            trit = ternary_value(global_channel, window, trit_offset);
                            expected_dense[global_channel] = expected_dense[global_channel] +
                                trit*activation_value(window, trit_offset);
                        end
                    end
                end
                @(posedge clk);
                #1;
                if (weight_load_ready !== {SLR_COUNT{1'b1}})
                    $fatal(1, "weight loader was not ready during full active-buffer preload");
            end
        end
        @(negedge clk);
        weight_load_valid = '0;
        load_done_cycle = cycle_count;
`ifndef PLAN6_CLUSTER_TEST
        if (USE_PLAN5_PAYLOAD && !USE_STREAMING_CLUSTER) begin
            if (gen_independent_slrs.gen_slr[0].dut.gen_weight_bank[0].u_active_pool_bank.memory[0] !== payload_records[0])
                $fatal(1, "channel 0 preload mismatch: got=%h expected=%h",
                    gen_independent_slrs.gen_slr[0].dut.gen_weight_bank[0].u_active_pool_bank.memory[0], payload_records[0]);
            if (gen_independent_slrs.gen_slr[0].dut.gen_weight_bank[0].u_active_pool_bank.memory[15399] !==
                payload_records[1731*WINDOW_COUNT + WINDOW_COUNT-1])
                $fatal(1, "channel 1731 preload mismatch: got=%h expected=%h",
                    gen_independent_slrs.gen_slr[0].dut.gen_weight_bank[0].u_active_pool_bank.memory[15399],
                    payload_records[1731*WINDOW_COUNT + WINDOW_COUNT-1]);
            if (gen_independent_slrs.gen_slr[0].dut.gen_weight_bank[1].u_active_pool_bank.memory[0] !== payload_records[4*WINDOW_COUNT])
                $fatal(1, "channel 4 preload mismatch: got=%h expected=%h",
                    gen_independent_slrs.gen_slr[0].dut.gen_weight_bank[1].u_active_pool_bank.memory[0], payload_records[4*WINDOW_COUNT]);
        end
`endif
        end

        run_start_cycle = cycle_count;
        for (round_num = 0; round_num < ROUNDS; round_num = round_num + 1) begin
            round_start_cycle = cycle_count;
            for (tile = 0; tile < TILE_COUNT; tile = tile + 1) begin
                @(negedge clk);
                if (USE_PLAN5_PAYLOAD) begin
                    for (slr = 0; slr < SLR_COUNT; slr = slr + 1) begin
                        for (lane = 0; lane < P_CH; lane = lane + 1) begin
                            global_channel = slr*C_OUT_PER_SLR + tile*P_CH + lane;
                            round_gamma_fp16[slr][lane*16 +: 16] =
                                payload_gamma[round_num*C_OUT + global_channel];
                        end
                    end
                end
                round_config_valid = {SLR_COUNT{1'b1}};
                while (round_config_ready != {SLR_COUNT{1'b1}})
                    @(negedge clk);
                round_config_valid = '0;
                if (!USE_STREAMING_CLUSTER && (round_num > 0 || tile > 0)) begin
                    weight_load_channel = CHANNEL_WIDTH'(tile*P_CH);
                    for (slr = 0; slr < SLR_COUNT; slr = slr + 1) begin
                        weight_load_data[slr] = '0;
                    end
                    weight_load_window = '0;
                    weight_load_valid = {SLR_COUNT{1'b1}};
                    #1;
                    if (weight_load_ready !== '0)
                        $fatal(1, "active weight buffer was writable between tiles or rounds");
                    @(posedge clk);
                    #1;
                    @(negedge clk);
                    weight_load_valid = '0;

                end
                round_config_valid = {SLR_COUNT{1'b1}};
                @(posedge clk);
                #1;
                @(negedge clk);
                round_config_valid = '0;

                for (window = 0; window < WINDOW_COUNT; window = window + 1) begin
                    @(negedge clk);
                    activation_valid = {SLR_COUNT{1'b1}};
                    for (slr = 0; slr < SLR_COUNT; slr = slr + 1)
                        activation_window[slr] = make_activation_window(window);
                    while (activation_ready != {SLR_COUNT{1'b1}})
                        @(negedge clk);
                    @(posedge clk);
                    #1;
                    activation_accepts = activation_accepts + 1;
`ifndef PLAN6_CLUSTER_TEST
                    if (USE_PLAN5_PAYLOAD && !USE_STREAMING_CLUSTER &&
                        round_num == 0 && tile == 0 && window == 0) begin
                        while (gen_independent_slrs.gen_slr[0].dut.state != 3'd3)
                            @(negedge clk);
                        #1;
                        if (gen_independent_slrs.gen_slr[0].dut.weight_words_q[0 +: 512] !== payload_records[0])
                            $fatal(1, "channel 0 pool word mismatch: got=%h expected=%h",
                                gen_independent_slrs.gen_slr[0].dut.weight_words_q[0 +: 512], payload_records[0]);
                        if (gen_independent_slrs.gen_slr[0].dut.weight_words_q[4*512 +: 512] !== payload_records[4*WINDOW_COUNT])
                            $fatal(1, "channel 4 pool word mismatch: got=%h expected=%h",
                                gen_independent_slrs.gen_slr[0].dut.weight_words_q[4*512 +: 512], payload_records[4*WINDOW_COUNT]);
                        if (gen_independent_slrs.gen_slr[0].dut.gamma_q[0 +: 16] !== payload_gamma[0])
                            $fatal(1, "channel 0 Gamma mismatch: got=%h expected=%h",
                                gen_independent_slrs.gen_slr[0].dut.gamma_q[0 +: 16], payload_gamma[0]);
                    end
`endif
                    if (round_num == 0 && tile == 0) begin
                        if (window == 0)
                            first_window_cycle = cycle_count;
                        else if (window == 1)
                            first_steady_window_interval = cycle_count - previous_window_cycle;
                        else if (window == 2)
                            second_steady_window_interval = cycle_count - previous_window_cycle;
                        previous_window_cycle = cycle_count;
                    end
                end
                @(negedge clk);
                activation_valid = '0;
                check_tile(tile, round_num);
                if (!USE_STREAMING_CLUSTER && round_num == ROUNDS-1 && tile == 0) begin
                    @(negedge clk);
                    weight_load_valid = {SLR_COUNT{1'b1}};
                    weight_load_channel = '0;
                    weight_load_window = '0;
                    for (slr = 0; slr < SLR_COUNT; slr = slr + 1) begin
                        global_channel = slr*C_OUT_PER_SLR;
                        if (USE_PLAN5_PAYLOAD)
                            weight_load_data[slr] = payload_records[global_channel*WINDOW_COUNT];
                        else
                            weight_load_data[slr] = make_record(global_channel, 0);
                    end
                    #1;
                    if (weight_load_ready !== {SLR_COUNT{1'b1}})
                        $fatal(1, "a tile was not writable after its final-round result");
                    @(posedge clk);
                    #1;
                    @(negedge clk);
                    weight_load_valid = '0;
                    weight_load_channel = CHANNEL_WIDTH'(P_CH);
                    weight_load_valid = {SLR_COUNT{1'b1}};
                    #1;
                    if (weight_load_ready !== '0)
                        $fatal(1, "an unconsumed tile was writable during the final round");
                    @(posedge clk);
                    #1;
                    @(negedge clk);
                    weight_load_valid = '0;
                end
            end
            if (round_num == 0)
                first_tile_round_cycles = cycle_count - round_start_cycle;
            else if (round_num == 1)
                steady_tile_round_cycles = cycle_count - round_start_cycle;
        end
        run_done_cycle = cycle_count;

        if (comparisons != C_OUT*ROUNDS)
            $fatal(1, "expected %0d channel-round comparisons, got %0d", C_OUT*ROUNDS, comparisons);
        if (activation_accepts != ROUNDS*TILE_COUNT*WINDOW_COUNT)
            $fatal(1, "activation-window handshake count mismatch");
        if (round_result_valid !== {SLR_COUNT{1'b1}} || done !== {SLR_COUNT{1'b1}})
            $fatal(1, "final round did not assert round_result_valid and done on all SLRs");
        if (first_steady_window_interval < 1 || second_steady_window_interval != 4)
            $fatal(
                1,
                "unexpected window schedule: initial=%0d steady=%0d",
                first_steady_window_interval,
                second_steady_window_interval
            );

        $display("PASS: SLR=%0d, C_OUT=%0d, K=%0d, ROUNDS=%0d", SLR_COUNT, C_OUT, K, ROUNDS);
        $display("PASS: %0d channel-round outputs matched software reference", comparisons);
        $display("MEASURE: active preload cycles=%0d", load_done_cycle-load_start_cycle);
        $display("MEASURE: cold first-window accept cycle=%0d", first_window_cycle-run_start_cycle);
        $display(
            "MEASURE: window accept intervals initial=%0d steady=%0d",
            first_steady_window_interval,
            second_steady_window_interval
        );
        $display("MEASURE: round 0 cycles=%0d steady round cycles=%0d", first_tile_round_cycles, steady_tile_round_cycles);
        $display("MEASURE: full 32-round cycles=%0d", run_done_cycle-run_start_cycle);
        if (USE_STREAMING_CLUSTER)
            $display("PASS: full operator stream drained through the shared shadow ring into three SLR active pools");
        else
            $display("PASS: single active pool stayed locked through each tile's last round and released after consumption");
        $finish;
    end
endmodule

module tb_rtwsr_top;
    rtwsr_top_full_testbench #(.USE_PLAN5_PAYLOAD(1'b0)) testbench();
endmodule

module tb_rtwsr_top_payload;
    rtwsr_top_full_testbench #(.USE_PLAN5_PAYLOAD(1'b1)) testbench();
endmodule

module tb_rtwsr_recurrent_linear_cluster;
    rtwsr_top_full_testbench #(.USE_STREAMING_CLUSTER(1'b1)) testbench();
endmodule
