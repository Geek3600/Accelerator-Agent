`timescale 1ns / 1ps

module tb_rtwsr_transformer_prefetch;
    logic clk = 0, rst_n = 0, start = 0;
    logic weight_start = 0, weight_prefetch_start = 0, weight_prefetch_ready;
    logic weight_stream_valid = 0, weight_stream_ready, weight_stream_last = 0;
    logic [511:0] weight_stream_data;
    logic weight_load_done, weight_store_busy, weight_protocol_error, error;
    logic [16:0] shadow_occupancy;
    logic gamma_load_start = 0, gamma_load_start_ready, gamma_load_valid = 0;
    logic gamma_load_ready, gamma_load_last = 0, gamma_load_done, gamma_protocol_error;
    logic [4:0] gamma_load_command_id = 0;
    logic [15:0] gamma_load_matrix_rows = 5280, gamma_load_matrix_columns = 10560;
    logic linear_engine_valid, linear_engine_tile_ready, linear_engine_tile_done;
    logic [4:0] linear_engine_command_id;
    logic [8:0] linear_engine_tile_index;
    logic [6:0] linear_result_rows;
    logic linear_result_valid, linear_result_ready = 1;
    logic [3071:0] linear_result_q12;
    logic [2:0] round_config_ready, activation_ready;
    logic [2:0] activation_valid = 3'b111;
    logic [2047:0] activation_window;
    logic norm_ready, norm_in_ready, norm_out_valid, norm_done;
    logic norm_in_valid = 0, norm_in_last = 0;
    logic [255:0] norm_in_activation_q4_12, norm_in_gamma_q4_12;
    logic [10:0] rope_write_position = 0, rope_window_start = 0;
    logic [11:0] rope_active_context_tokens = 0;
    logic rope_protocol_error;
    logic command_valid;
    logic [4:0] command_id;
    logic payload_descriptor_valid, payload_descriptor_adapter_file;
    logic [31:0] payload_weight_offset_bytes, payload_weight_bytes, payload_weight_words;
    logic [31:0] payload_gamma_offset_bytes, payload_gamma_bytes, payload_gamma_words;
    logic [15:0] payload_matrix_rows, payload_matrix_columns;
    integer checked_rows = 0, checked_tiles = 0, cycles = 0;
    integer internal_norm_chunks = 0, internal_norm_outputs = 0;
    integer expected_columns = 10560;
    bit initial_load_finished = 0, prefetch_finished = 0, expect_rope_error = 0;
    bit qkv_backpressure_tested = 0;
    bit adapter_descriptor_seen = 0, qkv_descriptor_seen = 0;

    always #5 clk = ~clk;
    always_comb begin
        activation_window = {256{8'd1}};
        if (linear_engine_command_id == 5'd0 && dut.linear_activation_window_index == 7'd20)
            activation_window = {{96{8'd2}}, {160{8'd1}}};
        else if (linear_engine_command_id == 5'd0 && dut.linear_activation_window_index > 7'd20)
            activation_window = {256{8'd2}};
    end

    always @(posedge clk) begin
        integer expected_scale_factor;
        cycles++;
        if (cycles > 800000)
            $fatal(1, "transformer prefetch timeout command=%0d rows=%0d busy=%0d pending=%0d loaded=%0d consumed=%0d",
                command_id, checked_rows, weight_store_busy, dut.prefetch_pending_q,
                dut.prefetch_loaded_q, dut.resident_consumed_q);
        if (rst_n && (weight_protocol_error || gamma_protocol_error ||
                      (error && !(expect_rope_error && rope_protocol_error))))
            $fatal(1, "transformer prefetch protocol error");
        if (rst_n && command_valid && payload_descriptor_valid) begin
            if (command_id == 5'd0) begin
                if (!payload_descriptor_adapter_file || payload_weight_offset_bytes != 0 ||
                    payload_weight_bytes != 14192640 || payload_weight_words != 221760 ||
                    payload_gamma_offset_bytes != 0 || payload_gamma_bytes != 10560 ||
                    payload_gamma_words != 165 || payload_matrix_rows != 5280 ||
                    payload_matrix_columns != 10560)
                    $fatal(1, "Adapter payload descriptor mismatch");
                adapter_descriptor_seen = 1;
            end else if (command_id == 5'd3) begin
                if (payload_descriptor_adapter_file || payload_weight_offset_bytes != 0 ||
                    payload_weight_bytes != 21288960 || payload_weight_words != 332640 ||
                    payload_gamma_offset_bytes != 0 || payload_gamma_bytes != 31680 ||
                    payload_gamma_words != 495 || payload_matrix_rows != 15840 ||
                    payload_matrix_columns != 5280)
                    $fatal(1, "QKV payload descriptor mismatch");
                qkv_descriptor_seen = 1;
            end
        end
        if (rst_n && linear_result_valid && dut.linear_result_ready_to_engine) begin
            expected_scale_factor = linear_engine_command_id == 5'd3 ? 4064 : 4096;
            if (linear_engine_command_id == 5'd3 && dut.recurrent_activation_scale_fp16_q != 16'h2000)
                $fatal(1, "Norm activation scale was not forwarded to QKV");
            for (integer row_id = 0; row_id < 96; row_id++)
                if ($signed(linear_result_q12[row_id*32 +: 32]) !=
                    ((row_id < int'(linear_result_rows)) ?
                     (linear_engine_command_id == 5'd0 ? 15840 : expected_columns)*expected_scale_factor : 0))
                    $fatal(1, "top GEMV mismatch command=%0d tile=%0d row=%0d got=%0d",
                        linear_engine_command_id, linear_engine_tile_index, row_id,
                        $signed(linear_result_q12[row_id*32 +: 32]));
            checked_rows += int'(linear_result_rows);
            checked_tiles++;
        end
        if (rst_n && dut.norm_use_recurrent_state && dut.norm_feed_valid && norm_in_ready) begin
            if (norm_in_valid)
                $fatal(1, "pre-attention Norm unexpectedly used external input");
            for (integer lane = 0; lane < 16; lane++)
                if ($signed(dut.norm_feed_activation[lane*16 +: 16]) != 32767)
                    $fatal(1, "adapter recurrent-state read mismatch chunk=%0d lane=%0d value=%0d",
                        internal_norm_chunks, lane,
                        $signed(dut.norm_feed_activation[lane*16 +: 16]));
            internal_norm_chunks++;
        end
        if (rst_n && dut.norm_use_recurrent_state && norm_out_valid && dut.norm_unit_out_ready)
            internal_norm_outputs++;
    end

    rtwsr_transformer_top #(.MODEL_ID(0)) dut (
        .clk(clk), .rst_n(rst_n), .start(start), .context_tokens(16'd512),
        .command_valid(command_valid), .command_id(command_id), .error(error),
        .payload_descriptor_valid(payload_descriptor_valid),
        .payload_descriptor_adapter_file(payload_descriptor_adapter_file),
        .payload_weight_offset_bytes(payload_weight_offset_bytes),
        .payload_weight_bytes(payload_weight_bytes), .payload_weight_words(payload_weight_words),
        .payload_gamma_offset_bytes(payload_gamma_offset_bytes),
        .payload_gamma_bytes(payload_gamma_bytes), .payload_gamma_words(payload_gamma_words),
        .payload_matrix_rows(payload_matrix_rows), .payload_matrix_columns(payload_matrix_columns),
        .operator_ready(1'b1), .operator_done(1'b0),
        .weight_start(weight_start), .weight_abort(1'b0),
        .weight_prefetch_start(weight_prefetch_start),
        .weight_prefetch_ready(weight_prefetch_ready),
        .weight_prefetch_command_id(5'd3), .weight_prefetch_block_index(6'd0),
        .weight_prefetch_rows(16'd15840), .weight_prefetch_columns(16'd5280),
        .weight_stream_valid(weight_stream_valid), .weight_stream_ready(weight_stream_ready),
        .weight_stream_data(weight_stream_data), .weight_stream_last(weight_stream_last),
        .weight_store_busy(weight_store_busy), .weight_load_done(weight_load_done),
        .weight_protocol_error(weight_protocol_error), .shadow_occupancy(shadow_occupancy),
        .gamma_load_start(gamma_load_start), .gamma_load_start_ready(gamma_load_start_ready),
        .gamma_load_command_id(gamma_load_command_id), .gamma_load_block_index(6'd0),
        .gamma_load_recurrence_index(5'd0), .gamma_load_matrix_rows(gamma_load_matrix_rows),
        .gamma_load_matrix_columns(gamma_load_matrix_columns),
        .gamma_load_valid(gamma_load_valid), .gamma_load_ready(gamma_load_ready),
        .gamma_load_pair_data(32'h3c003c00), .gamma_load_vector_data(512'd0),
        .gamma_load_last(gamma_load_last),
        .gamma_load_done(gamma_load_done), .gamma_protocol_error(gamma_protocol_error),
        .rope_write_position(rope_write_position),
        .rope_active_context_tokens(rope_active_context_tokens),
        .rope_window_start(rope_window_start), .rope_protocol_error(rope_protocol_error),
        .round_config_valid(3'b111), .round_config_ready(round_config_ready),
        .round_activation_scale_fp16(16'h3c00),
        .activation_valid(activation_valid), .activation_ready(activation_ready),
        .activation_window(activation_window),
        .linear_engine_valid(linear_engine_valid),
        .linear_engine_command_id(linear_engine_command_id),
        .linear_engine_tile_index(linear_engine_tile_index),
        .linear_engine_tile_ready(linear_engine_tile_ready),
        .linear_engine_tile_done(linear_engine_tile_done),
        .linear_result_valid(linear_result_valid), .linear_result_ready(linear_result_ready),
        .linear_result_q12(linear_result_q12), .linear_result_rows(linear_result_rows),
        .norm_ready(norm_ready), .norm_in_ready(norm_in_ready),
        .norm_in_valid(norm_in_valid), .norm_in_last(norm_in_last),
        .norm_in_activation_q4_12(norm_in_activation_q4_12),
        .norm_in_gamma_q4_12(norm_in_gamma_q4_12),
        .norm_out_valid(norm_out_valid), .norm_out_ready(1'b1), .norm_done(norm_done)
    );

    task automatic stream_weights(input integer rows, columns);
        integer records;
        records = rows*((columns+255)/256);
        for (integer record_id = 0; record_id < records; record_id++) begin
            weight_stream_valid = 1;
            weight_stream_last = record_id == records-1;
            do @(posedge clk); while (!weight_stream_ready);
            @(negedge clk);
        end
        weight_stream_valid = 0;
        weight_stream_last = 0;
        while (!weight_load_done) @(negedge clk);
    endtask

    task automatic load_gamma(input integer id, rows, columns);
        while (!gamma_load_start_ready) @(negedge clk);
        gamma_load_command_id = 5'(id);
        gamma_load_matrix_rows = 16'(rows);
        gamma_load_matrix_columns = 16'(columns);
        gamma_load_start = 1;
        @(negedge clk);
        gamma_load_start = 0;
        for (integer pair_id = 0; pair_id < (rows+1)/2; pair_id++) begin
            gamma_load_valid = 1;
            gamma_load_last = pair_id == (rows+1)/2-1;
            do @(posedge clk); while (!gamma_load_ready);
            @(negedge clk);
        end
        gamma_load_valid = 0;
        gamma_load_last = 0;
    endtask

    initial begin
        // Every dense coefficient is +1; sparse slots are zero.
        weight_stream_data = 0;
        for (integer byte_id = 0; byte_id < 51; byte_id++)
            weight_stream_data[96+byte_id*8 +: 8] = 8'd242;
        weight_stream_data[511:504] = 8'd2;
        norm_in_activation_q4_12 = {16{16'h1000}};
        norm_in_gamma_q4_12 = {16{16'h1000}};
        repeat (5) @(negedge clk);
        rst_n = 1;
        start = 1;
        @(negedge clk); start = 0;
        while (!linear_engine_valid) @(negedge clk);
        weight_start = 1;
        @(negedge clk); weight_start = 0;
        fork
            begin stream_weights(5280,10560); initial_load_finished = 1; end
            load_gamma(0,5280,10560);
        join
        while (!weight_prefetch_ready) @(negedge clk);
        // Hold the first tile while the next matrix fills the complete shadow FIFO.
        activation_valid = 0;
        weight_prefetch_start = 1;
        @(negedge clk); weight_prefetch_start = 0;
        fork
            begin stream_weights(15840,5280); prefetch_finished = 1; end
            begin
                while (shadow_occupancy != 73728) @(negedge clk);
                if (dut.u_weight_memory.output_record_index_q != 0)
                    $fatal(1, "top prefetch wrote before the first tile was consumed");
                activation_valid = 3'b111;
                load_gamma(3,15840,5280);
                while (checked_rows != 5280) @(negedge clk);
                expected_columns = 5280;
                while (checked_rows != 21120) @(negedge clk);
            end
        join
        if (dut.g_huginn_recurrent_state.g_bank[0].state_memory[0][15:0] != 16'sd32767)
            $fatal(1, "Pre-Attention Norm overwrote the raw recurrent residual");
        $display("PASS pre-attention Norm preserves raw recurrent residual");
        force dut.norm_out_valid = 1'b1;
        force dut.norm_unit_out_ready = 1'b1;
        force dut.scheduler_vector_length = 16'd5280;
        force dut.scheduler_command_id = 5'd2;
        #1;
        if (dut.g_huginn_recurrent_state.g_bank[0].state_write_enable)
            $fatal(1, "Pre-Attention Norm enabled a recurrent-state commit");
        force dut.scheduler_command_id = 5'd11;
        #1;
        if (dut.g_huginn_recurrent_state.g_bank[0].state_write_enable)
            $fatal(1, "Pre-FFN Norm enabled a recurrent-state commit");
        force dut.scheduler_command_id = 5'd10;
        #1;
        if (!dut.g_huginn_recurrent_state.g_bank[0].state_write_enable)
            $fatal(1, "Attention post-residual Norm did not commit recurrent state");
        force dut.scheduler_command_id = 5'd16;
        #1;
        if (!dut.g_huginn_recurrent_state.g_bank[0].state_write_enable)
            $fatal(1, "MLP post-residual Norm did not commit recurrent state");
        release dut.norm_out_valid;
        release dut.norm_unit_out_ready;
        release dut.scheduler_vector_length;
        release dut.scheduler_command_id;
        $display("PASS recurrent-state commits are limited to post-residual Norm stages");
        if (!initial_load_finished || !prefetch_finished || checked_tiles != 220 ||
            !qkv_backpressure_tested ||
            dut.prefetch_pending_q || weight_store_busy || internal_norm_chunks != 330 ||
            internal_norm_outputs != 330 || !dut.activation_buffer_valid_q || norm_in_valid ||
            !dut.adapter_embedding_valid_q ||
            !adapter_descriptor_seen || !qkv_descriptor_seen ||
            dut.adapter_embedding_memory[0][1279:0] != {160{8'd1}} ||
            dut.adapter_embedding_memory[0][2047:1280] != {96{8'd2}} ||
            dut.adapter_embedding_memory[1] != {256{8'd2}} ||
            !dut.qkv_buffer_valid || dut.u_qkv_head_buffer.query_memory[0][0] != 16'sd32767 ||
            dut.u_qkv_head_buffer.key_memory[0][0] != 16'sd32767 ||
            dut.u_qkv_head_buffer.value_memory[0][0] != 16'sd32767)
            $fatal(1, "top prefetch/QKV mismatch initial=%0d prefetch=%0d tiles=%0d pending=%0d busy=%0d norm_in=%0d norm_out=%0d act=%0d anchor=%0d anchor0=%h backpressure=%0d qkv=%0d q=%0d k=%0d v=%0d",
                initial_load_finished, prefetch_finished, checked_tiles, dut.prefetch_pending_q,
                weight_store_busy, internal_norm_chunks, internal_norm_outputs,
                dut.activation_buffer_valid_q, dut.adapter_embedding_valid_q,
                dut.adapter_embedding_memory[0], qkv_backpressure_tested,
                dut.qkv_buffer_valid,
                dut.u_qkv_head_buffer.query_memory[0][0],
                dut.u_qkv_head_buffer.key_memory[0][0],
                dut.u_qkv_head_buffer.value_memory[0][0]);

        force dut.linear_engine_command_id = 5'd0;
        force dut.linear_activation_window_index = 9'd0;
        #1;
        if (!dut.adapter_internal_activation || dut.gemv_activation_valid != 3'b111 ||
            dut.gemv_activation_window != dut.normalized_activation_memory[0])
            $fatal(1, "Adapter state input was not selected for the low matrix half");
        force dut.linear_activation_window_index = 9'd20;
        #1;
        if (dut.gemv_activation_window[1279:0] != dut.normalized_activation_memory[20][1279:0] ||
            dut.gemv_activation_window[2047:1280] != dut.adapter_embedding_memory[0][2047:1280])
            $fatal(1, "Adapter state/embedding boundary window was not composed correctly");
        force dut.linear_activation_window_index = 9'd21;
        #1;
        if (dut.gemv_activation_window != dut.adapter_embedding_memory[1])
            $fatal(1, "Adapter embedding input window was not selected after the boundary");
        release dut.linear_activation_window_index;
        release dut.linear_engine_command_id;
        $display("PASS internal adapter-norm-qkv rows=%0d tiles=%0d norm_chunks=%0d cycles=%0d",
                 checked_rows, checked_tiles, internal_norm_chunks, cycles);
        expect_rope_error = 1;
        rope_write_position = 11'd512;
        rope_active_context_tokens = 12'd512;
        while (command_id != 5'd5) @(negedge clk);
        wait (rope_protocol_error);
        if (!error)
            $fatal(1, "top-level error did not include the RoPE/KV protocol error");
        $display("PASS top propagates RoPE/KV protocol error");
        $finish;
    end

    initial begin
        wait (rst_n && linear_engine_command_id == 5'd3 && linear_result_valid);
        force dut.qkv_buffer_ready = 1'b0;
        @(posedge clk);
        #1;
        if (dut.linear_result_ready_to_engine || dut.linear_engine_tile_done)
            $fatal(1, "QKV result advanced while the internal buffer was blocked");
        @(negedge clk);
        release dut.qkv_buffer_ready;
        qkv_backpressure_tested = 1;
    end
endmodule
