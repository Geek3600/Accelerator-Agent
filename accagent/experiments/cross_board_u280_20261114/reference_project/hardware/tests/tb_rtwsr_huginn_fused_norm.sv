`timescale 1ns / 1ps

module tb_rtwsr_huginn_fused_norm;
    logic clk = 0, rst_n = 0;
    logic [8:0] tile_index = 0;
    logic [15:0] tile_row_start = 0;
    logic [4:0] linear_command = 0, norm_command = 0;
    logic [3071:0] result_q12 = 0;
    logic launch = 0, result_valid = 0, norm_start = 0;
    logic gamma_valid = 0;
    logic [1535:0] gamma_tile = 0;
    logic [255:0] bank_values [0:5];
    logic [63:0] expected_sum;
    logic ref_ready, ref_in_ready, ref_out_valid, ref_out_last, ref_done, ref_error;
    logic [255:0] ref_normalized;
    logic [127:0] ref_quantized;
    logic [15:0] ref_inv, ref_scale;
    logic ref_input_valid = 0, ref_input_last = 0;
    logic [255:0] ref_activation = 0, ref_gamma = 0;
    logic [255:0] candidate_normalized [0:329];
    logic [127:0] candidate_quantized [0:329];
    logic [15:0] candidate_inv, candidate_scale;
    integer outputs, ref_outputs, inputs, cycle_count = 0, start_cycle;
    integer candidate_done_cycle, reference_done_cycle;

    always #5 clk = ~clk;
    always @(posedge clk) cycle_count++;

    rtwsr_transformer_top #(.MODEL_ID(0), .CORE_TIMING_CANDIDATE(1),
                            .RESIDUAL_NORM_FUSION(1), .RESIDUAL_NORM_TILE_PRELOAD(1)) dut (
        .clk(clk), .rst_n(rst_n), .start(1'b0), .weight_abort(1'b0),
        .gamma_load_vector_data(512'd0),
        .norm_in_gamma_q4_12('0), .norm_out_ready(1'b1),
        .norm_preload_gamma_valid(gamma_valid), .norm_preload_gamma_q4_12(gamma_tile)
    );

    rtwsr_rmsnorm_quant_unit #(.VECTOR_LEN(5280), .PARALLEL_QUANTIZE(1)) reference_norm (
        .clk(clk), .rst_n(rst_n), .start(norm_start), .vector_length(16'd5280),
        .precomputed_sum_valid(1'b0), .precomputed_sum_square(64'd0),
        .preloaded_input_valid(1'b0), .preload_write(1'b0), .preload_tile_index(9'd0),
        .preload_activation_q4_12('0), .preload_gamma_q4_12('0),
        .ready(ref_ready), .in_valid(ref_input_valid), .in_ready(ref_in_ready),
        .in_activation_q4_12(ref_activation),
        .in_gamma_q4_12(ref_gamma), .in_last(ref_input_last),
        .out_valid(ref_out_valid), .out_ready(1'b1), .out_normalized_q4_12(ref_normalized),
        .out_quantized_int8(ref_quantized), .out_last(ref_out_last),
        .inv_rms_q15(ref_inv), .activation_scale_q4_12(ref_scale),
        .busy(), .done(ref_done), .protocol_error(ref_error)
    );

    always @(posedge clk) begin
        if (rst_n && ref_input_valid && ref_in_ready)
            inputs++;
        if (rst_n && dut.norm_out_valid) begin
            candidate_normalized[outputs] = dut.norm_out_normalized_q4_12;
            candidate_quantized[outputs] = dut.norm_out_quantized_int8;
            candidate_inv = dut.norm_inv_rms_q15;
            candidate_scale = dut.norm_activation_scale_q4_12;
            outputs++;
        end
        if (rst_n && ref_out_valid) begin
            if (outputs <= ref_outputs || candidate_normalized[ref_outputs] !== ref_normalized ||
                candidate_quantized[ref_outputs] !== ref_quantized ||
                ref_out_last !== (ref_outputs == 329) || candidate_inv !== ref_inv ||
                candidate_scale !== ref_scale)
                $fatal(1, "fused/reference Norm output mismatch chunk=%0d", ref_outputs);
            ref_outputs++;
        end
        if (dut.norm_done) candidate_done_cycle = cycle_count;
        if (ref_done) reference_done_cycle = cycle_count;
    end

    initial begin
        integer value, delta, raw_delta, residual, lane, bank, tile, dimension;
        longint signed signed_residual;
        force dut.recurrent_state_valid_q = 1'b1;
        force dut.linear_engine_command_id = linear_command;
        force dut.linear_engine_tile_index = tile_index;
        force dut.linear_engine_tile_row_start = tile_row_start;
        force dut.linear_result_rows = 7'd96;
        force dut.linear_result_q12 = result_q12;
        force dut.linear_result_valid = result_valid;
        force dut.tile_launch = launch;
        force dut.ffn_pipeline_write_ready = 1'b1;
        force dut.scheduler_command_id = norm_command;
        force dut.scheduler_vector_length = 16'd5280;
        force dut.norm_start = norm_start;
        repeat (5) @(negedge clk);
        rst_n = 1;
        for (integer pass = 0; pass < 2; pass++) begin
            linear_command = pass == 0 ? 5'd9 : 5'd15;
            norm_command = pass == 0 ? 5'd10 : 5'd16;
            force dut.linear_engine_command_id = linear_command;
            force dut.scheduler_command_id = norm_command;
            expected_sum = 0;
            outputs = 0;
            ref_outputs = 0;
            inputs = 0;
            for (tile = 0; tile < 55; tile++) begin
                for (bank = 0; bank < 6; bank++) bank_values[bank] = '0;
                result_q12 = '0;
                gamma_tile = '0;
                for (lane = 0; lane < 96; lane++) begin
                    value = ((tile * 96 + lane) * 71 % 60001) - 30000;
                    raw_delta = ((tile * 96 + lane) * 97 % 70001) - 35000;
                    delta = raw_delta;
                    if (delta > 32767) delta = 32767;
                    if (delta < -32768) delta = -32768;
                    residual = value + delta;
                    if (residual > 32767) residual = 32767;
                    if (residual < -32768) residual = -32768;
                    signed_residual = residual;
                    expected_sum += signed_residual * signed_residual;
                    bank_values[lane / 16][(lane % 16)*16 +: 16] = 16'(value);
                    result_q12[lane*32 +: 32] = 32'(raw_delta);
                    gamma_tile[lane*16 +: 16] = 16'(2500 + ((tile*96+lane)*29 % 3000));
                end
                dut.g_huginn_recurrent_state.g_bank[0].state_memory[tile] = bank_values[0];
                dut.g_huginn_recurrent_state.g_bank[1].state_memory[tile] = bank_values[1];
                dut.g_huginn_recurrent_state.g_bank[2].state_memory[tile] = bank_values[2];
                dut.g_huginn_recurrent_state.g_bank[3].state_memory[tile] = bank_values[3];
                dut.g_huginn_recurrent_state.g_bank[4].state_memory[tile] = bank_values[4];
                dut.g_huginn_recurrent_state.g_bank[5].state_memory[tile] = bank_values[5];
                tile_index = 9'(tile);
                tile_row_start = 16'(tile * 96);
                force dut.linear_engine_tile_index = tile_index;
                force dut.linear_engine_tile_row_start = tile_row_start;
                force dut.linear_result_q12 = result_q12;
                launch = 1;
                force dut.tile_launch = 1'b1;
                @(negedge clk);
                launch = 0;
                force dut.tile_launch = 1'b0;
                result_valid = 1;
                force dut.linear_result_valid = 1'b1;
                #1;
                if (!dut.fused_residual_write || !dut.linear_result_valid ||
                    !dut.linear_result_internal_sink || dut.linear_result_ready_to_engine ||
                    !dut.norm_preload_gamma_request ||
                    dut.norm_preload_gamma_command_id != norm_command ||
                    dut.norm_preload_gamma_tile_index != tile_index)
                    $fatal(1, "fusion handshake not active pass=%0d tile=%0d command=%0d write=%0d valid=%0d sink=%0d ready=%0d",
                           pass, tile, dut.linear_engine_command_id, dut.fused_residual_write,
                           dut.linear_result_valid, dut.linear_result_internal_sink,
                           dut.linear_result_ready_to_engine);
                @(negedge clk);
                gamma_valid = 1;
                @(negedge clk);
                result_valid = 0;
                gamma_valid = 0;
                force dut.linear_result_valid = 1'b0;
            end
            if (!dut.fused_sum_valid_q || dut.fused_sum_square_q !== expected_sum)
                $fatal(1, "fused sum mismatch pass=%0d got=%0d expected=%0d",
                       pass, dut.fused_sum_square_q, expected_sum);
            norm_start = 1;
            force dut.norm_start = 1'b1;
            start_cycle = cycle_count;
            @(negedge clk);
            norm_start = 0;
            force dut.norm_start = 1'b0;
            for (integer chunk = 0; chunk < 330; chunk++) begin
                ref_activation = '0;
                ref_gamma = '0;
                for (lane = 0; lane < 16; lane++) begin
                    dimension = chunk * 16 + lane;
                    value = (dimension * 71 % 60001) - 30000;
                    delta = (dimension * 97 % 70001) - 35000;
                    if (delta > 32767) delta = 32767;
                    if (delta < -32768) delta = -32768;
                    residual = value + delta;
                    if (residual > 32767) residual = 32767;
                    if (residual < -32768) residual = -32768;
                    ref_activation[lane*16 +: 16] = 16'(residual);
                    ref_gamma[lane*16 +: 16] = 16'(2500 + (dimension*29 % 3000));
                end
                ref_input_valid = 1;
                ref_input_last = chunk == 329;
                do @(posedge clk); while (!ref_in_ready);
                @(negedge clk);
            end
            ref_input_valid = 0;
            ref_input_last = 0;
            wait (ref_done);
            @(posedge clk);
            @(negedge clk);
            if (inputs != 330 || outputs != 330 || ref_outputs != 330 || ref_error || dut.norm_protocol_error ||
                reference_done_cycle - candidate_done_cycle != 330)
                $fatal(1, "Norm count/error pass=%0d inputs=%0d outputs=%0d ref=%0d candidate=%0d reference=%0d",
                       pass, inputs, outputs, ref_outputs, candidate_done_cycle, reference_done_cycle);
            $display("PASS full Huginn fused Norm command=%0d sum=%0d chunks=%0d candidate_cycles=%0d reference_cycles=%0d",
                     norm_command, expected_sum, outputs, candidate_done_cycle-start_cycle,
                     reference_done_cycle-start_cycle);
        end
        $finish;
    end

    initial begin
        repeat (100000) @(posedge clk);
        $fatal(1, "full Huginn fused Norm timeout");
    end
endmodule
