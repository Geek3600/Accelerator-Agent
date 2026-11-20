`timescale 1ns / 1ps

module tb_rtwsr_runtime_tile_gemv #(
    parameter int CHANNELS = 96,
    parameter int ROW_COUNT_WIDTH = (CHANNELS <= 127) ? 7 : 8,
    parameter int TRITS_PER_CYCLE = 64,
    parameter bit READ_PARALLEL_SLOTS = 1'b0,
    parameter bit ADAPTER_STATIC_REUSE = 1'b0,
    parameter bit ADAPTER_CACHE_TEST = 1'b0
);
    logic clk = 0;
    logic rst_n = 0;
    logic load_start = 0;
    logic [15:0] load_rows = 0, load_columns = 0;
    logic weight_stream_valid = 0, weight_stream_ready;
    logic [511:0] weight_stream_data = 0;
    logic weight_stream_last = 0;
    logic weight_store_busy, weight_load_done, weight_protocol_error;
    logic [16:0] shadow_occupancy;
    logic pool_read_enable, pool_read_valid, pool_read_error;
    logic [8:0] pool_read_tile_index;
    logic [6:0] pool_read_window_index;
    logic [1:0] pool_read_subword_index;
    logic [(READ_PARALLEL_SLOTS ? CHANNELS : CHANNELS/4)*512-1:0] pool_read_data;
    logic tile_valid = 0, tile_ready;
    logic adapter_cache_invalidate = 0;
    logic [8:0] tile_index = 0;
    logic [ROW_COUNT_WIDTH-1:0] tile_rows = 0;
    logic [CHANNELS*16-1:0] tile_gamma_fp16 = 0;
    logic [15:0] activation_scale_fp16 = 16'h3800;
    logic activation_ready, activation_valid = 0;
    logic [2047:0] activation_window = 0;
    logic [6:0] activation_window_index;
    logic result_valid, result_ready = 0;
    logic [CHANNELS*32-1:0] result_q12;
    logic [ROW_COUNT_WIDTH-1:0] result_rows;
    logic tile_done, protocol_error;
    integer cycles = 0;
    integer last_execute_cycle = 0;
    integer executed_subchunks = 0;
    integer pool_read_count = 0;
    logic continuous_expected = 0;
    integer checked_rows = 0;
    integer checked_tiles = 0;
    integer expected_tiles = 0;
    integer adapter_cache_runs = 0;
    longint signed reference_q12 [0:CHANNELS-1];
    logic [CHANNELS*32-1:0] held_result;

    always #5 clk = ~clk;
    always @(posedge clk) begin
        cycles <= cycles + 1;
        if (rst_n && pool_read_valid)
            pool_read_count++;
        if (cycles > 5000000)
            $fatal(1, "full-matrix runtime GEMV timeout");
        if (rst_n && dut.execute_valid) begin
            if (continuous_expected && dut.subchunk_q != 0 &&
                cycles != last_execute_cycle + 1)
                $fatal(1, "shared array bubble within a four-subchunk window");
            if (tile_index == 0) begin
                for (integer channel_id = 0; channel_id < CHANNELS; channel_id++)
                    if (dut.active_words[channel_id*512 +: 512] !==
                        make_word(channel_id,int'(dut.execute_window_q)))
                        $fatal(1, "word mismatch window=%0d subchunk=%0d row=%0d",
                            dut.execute_window_q,dut.subchunk_q,channel_id);
                for (integer element_id = 0; element_id < 256; element_id++) begin
                    integer column_id;
                    logic expected_activation_valid;
                    column_id = int'(dut.execute_window_q)*256 + element_id;
                    expected_activation_valid = column_id < int'(load_columns);
                    if (ADAPTER_CACHE_TEST) begin
                        if (dut.static_pass_q)
                            expected_activation_valid = expected_activation_valid && column_id >= 5280;
                        else
                            expected_activation_valid = expected_activation_valid && column_id < 5280;
                    end
                    if ($signed(dut.activation_q[dut.execute_window_q[0]][element_id*8 +: 8]) !==
                        8'(expected_activation_valid ?
                            activation_for(int'(dut.execute_window_q),element_id) : 0))
                        $fatal(1, "activation mismatch window=%0d subchunk=%0d element=%0d actual=%0d expected=%0d load_window=%0d columns=%0d",
                            dut.execute_window_q,dut.subchunk_q,element_id,
                            $signed(dut.activation_q[dut.execute_window_q[0]][element_id*8 +: 8]),
                            activation_for(int'(dut.execute_window_q),element_id),
                            dut.load_window_q,dut.columns_q);
                end
            end
            last_execute_cycle = cycles;
            executed_subchunks++;
        end
        if (rst_n && (protocol_error || weight_protocol_error || pool_read_error))
            $fatal(1, "runtime GEMV protocol error");
    end

    rtwsr_runtime_weight_subsystem #(
        .CHANNELS(CHANNELS),
        .READ_PARALLEL_SLOTS(READ_PARALLEL_SLOTS)
    ) u_storage (
        .activate_loaded_weights(1'b0), .consumed_tile_valid(1'b0),
        .consumed_tile_index(9'd0),
        .clk(clk), .rst_n(rst_n), .load_start(load_start), .load_abort(1'b0),
        .load_rows(load_rows), .load_columns(load_columns),
        .weight_stream_valid(weight_stream_valid), .weight_stream_ready(weight_stream_ready),
        .weight_stream_data(weight_stream_data), .weight_stream_last(weight_stream_last),
        .pool_drain_enable(1'b1), .weight_store_busy(weight_store_busy),
        .weight_load_done(weight_load_done), .weight_protocol_error(weight_protocol_error),
        .shadow_occupancy(shadow_occupancy), .pool_window_count(), .pool_words_per_port(),
        .pool_read_enable(pool_read_enable), .pool_read_tile_index(pool_read_tile_index),
        .pool_read_window_index(pool_read_window_index),
        .pool_read_subword_index(pool_read_subword_index),
        .pool_read_valid(pool_read_valid), .pool_read_data(pool_read_data),
        .pool_read_error(pool_read_error)
    );
    rtwsr_runtime_tile_gemv #(
        .CHANNELS(CHANNELS),
        .ROW_COUNT_WIDTH(ROW_COUNT_WIDTH),
        .ADAPTER_STATIC_REUSE(ADAPTER_STATIC_REUSE),
        .TRITS_PER_CYCLE(TRITS_PER_CYCLE),
        .READ_PARALLEL_SLOTS(READ_PARALLEL_SLOTS)
    ) dut (
        .clk(clk), .rst_n(rst_n), .tile_valid(tile_valid), .tile_ready(tile_ready),
        .tile_index(tile_index), .tile_rows(tile_rows), .matrix_columns(load_columns),
        .tile_gamma_fp16(tile_gamma_fp16), .activation_scale_fp16(activation_scale_fp16),
        .adapter_reuse(ADAPTER_CACHE_TEST),
        .adapter_cache_invalidate(adapter_cache_invalidate),
        .activation_ready(activation_ready), .activation_valid(activation_valid),
        .activation_window(activation_window), .activation_window_index(activation_window_index),
        .pool_read_enable(pool_read_enable), .pool_read_tile_index(pool_read_tile_index),
        .pool_read_window_index(pool_read_window_index),
        .pool_read_subword_index(pool_read_subword_index),
        .pool_read_valid(pool_read_valid), .pool_read_data(pool_read_data),
        .result_valid(result_valid), .result_ready(result_ready), .result_q12(result_q12),
        .result_rows(result_rows), .tile_done(tile_done), .protocol_error(protocol_error)
    );

    function automatic integer trit_for(input integer row_id, window_id, element_id);
        integer residue;
        residue = (row_id*17 + window_id*19 + element_id*7) % 5;
        trit_for = residue == 0 ? 1 : residue == 1 ? -1 : 0;
    endfunction
    function automatic integer activation_for(input integer window_id, element_id);
        activation_for = ((window_id*37 + element_id*29) % 256) - 128;
    endfunction
    function automatic logic [511:0] make_word(input integer row_id, window_id);
        logic [511:0] word_value;
        integer code, place_value;
        word_value = 0;
        for (integer slot_id = 0; slot_id < 4; slot_id++) begin
            word_value[slot_id*24 +: 16] = 16'h1000;
            word_value[slot_id*24+16 +: 8] = 8'((row_id*11+window_id*13+slot_id*47)%256);
        end
        for (integer byte_id = 0; byte_id < 51; byte_id++) begin
            code = 0;
            place_value = 1;
            for (integer digit_id = 0; digit_id < 5; digit_id++) begin
                code += (trit_for(row_id, window_id, byte_id*5+digit_id)+1)*place_value;
                place_value *= 3;
            end
            word_value[96+byte_id*8 +: 8] = 8'(code);
        end
        word_value[504 +: 8] = 8'(trit_for(row_id,window_id,255)+1);
        return word_value;
    endfunction

    function automatic longint signed round_divide_even(input longint signed value, input integer divisor);
        longint unsigned magnitude, quotient, remainder;
        magnitude = value < 0 ? -value : value;
        quotient = magnitude / divisor;
        remainder = magnitude % divisor;
        if (2*remainder > divisor || (2*remainder == divisor && quotient[0]))
            quotient++;
        return value < 0 ? -longint'(quotient) : longint'(quotient);
    endfunction

    task automatic run_matrix(input integer rows, columns);
        integer windows, tiles, global_row, active_rows, sparse_index;
        integer begin_cycle, compute_begin, reads_before, reads_expected;
        integer activation_count, active_window_id;
        longint signed total;
        windows = (columns+255)/256;
        tiles = (rows+CHANNELS-1)/CHANNELS;
        expected_tiles += tiles;
        begin_cycle = cycles;
        reads_before = pool_read_count;
        @(negedge clk);
        load_rows = 16'(rows);
        load_columns = 16'(columns);
        load_start = 1;
        @(negedge clk);
        load_start = 0;
        for (integer row_id = 0; row_id < rows; row_id++) begin
            for (integer window_id = 0; window_id < windows; window_id++) begin
                weight_stream_valid = 1;
                weight_stream_data = make_word(row_id, window_id);
                weight_stream_last = row_id == rows-1 && window_id == windows-1;
                do @(posedge clk); while (!weight_stream_ready);
                @(negedge clk);
            end
        end
        weight_stream_valid = 0;
        weight_stream_last = 0;
        while (!weight_load_done) @(negedge clk);
        compute_begin = cycles;
        for (integer tile_id = 0; tile_id < tiles; tile_id++) begin
            active_rows = rows-tile_id*CHANNELS < CHANNELS ? rows-tile_id*CHANNELS : CHANNELS;
            // Independent integer dense+sparse reference with per-row Gamma.
            for (integer channel_id = 0; channel_id < CHANNELS; channel_id++) begin
                global_row = tile_id*CHANNELS+channel_id;
                total = 0;
                if (channel_id < active_rows) begin
                    for (integer window_id = 0; window_id < windows; window_id++) begin
                        for (integer element_id = 0; element_id < 256; element_id++)
                            if (window_id*256+element_id < columns)
                                total += trit_for(global_row,window_id,element_id)*
                                    activation_for(window_id,element_id)*4096;
                        for (integer slot_id = 0; slot_id < 4; slot_id++) begin
                            sparse_index = (global_row*11+window_id*13+slot_id*47)%256;
                            if (window_id*256+sparse_index < columns)
                                total += activation_for(window_id,sparse_index)*4096;
                        end
                    end
                end
                case (global_row%3)
                    0: begin tile_gamma_fp16[channel_id*16 +: 16] = 16'h3800; total = round_divide_even(total, 4); end
                    1: begin tile_gamma_fp16[channel_id*16 +: 16] = 16'h3c00; total = round_divide_even(total, 2); end
                    2: tile_gamma_fp16[channel_id*16 +: 16] = 16'h4000;
                endcase
                reference_q12[channel_id] = total;
            end
            continuous_expected = tile_id%11 != 0;
            tile_valid = 1;
            tile_index = 9'(tile_id);
            tile_rows = ROW_COUNT_WIDTH'(active_rows);
            do @(posedge clk); while (!tile_ready);
            @(negedge clk);
            tile_valid = 0;
            activation_count = ADAPTER_CACHE_TEST ?
                (adapter_cache_runs == 0 ? windows + 1 : windows / 2) : windows;
            for (integer activation_step = 0; activation_step < activation_count; activation_step++) begin
                // Input gaps exercise activation backpressure at each window boundary.
                repeat ((tile_id%11 == 0 && activation_step%5 == 0) ? 7 :
                        (tile_id+activation_step)%3) @(negedge clk);
                while (!activation_ready) @(negedge clk);
                active_window_id = ADAPTER_CACHE_TEST ? int'(activation_window_index) : activation_step;
                if (!ADAPTER_CACHE_TEST && activation_window_index != active_window_id)
                    $fatal(1, "activation window index mismatch");
                for (integer element_id = 0; element_id < 256; element_id++)
                    activation_window[element_id*8 +: 8] = 8'(activation_for(active_window_id,element_id));
                activation_valid = 1;
                @(negedge clk);
                activation_valid = 0;
            end
            while (!result_valid) @(negedge clk);
            held_result = result_q12;
            repeat (3) begin
                @(negedge clk);
                if (!result_valid || result_q12 !== held_result || tile_done || tile_ready)
                    $fatal(1, "result changed under backpressure");
            end
            if (result_rows != active_rows)
                $fatal(1, "result row mask mismatch");
            for (integer channel_id = 0; channel_id < CHANNELS; channel_id++) begin
                if ($signed(result_q12[channel_id*32 +: 32]) !== reference_q12[channel_id][31:0])
                    $fatal(1, "rows=%0d columns=%0d tile=%0d row=%0d got=%0d reference=%0d",
                        rows,columns,tile_id,channel_id,
                        $signed(result_q12[channel_id*32 +: 32]),reference_q12[channel_id]);
            end
            checked_rows += active_rows;
            checked_tiles++;
            result_ready = 1;
            @(negedge clk);
            if (!tile_done) $fatal(1, "tile completion handshake missing");
            result_ready = 0;
        end
        reads_expected = ADAPTER_CACHE_TEST ?
            tiles * (adapter_cache_runs == 0 ? windows + 1 : (windows / 2)) :
            tiles * windows * (READ_PARALLEL_SLOTS ? 1 : 4);
        if (pool_read_count - reads_before != reads_expected)
            $fatal(1, "pool read count mismatch rows=%0d columns=%0d got=%0d expected=%0d",
                rows, columns, pool_read_count-reads_before, reads_expected);
        $display("PASS full matrix %0dx%0d: tiles=%0d records=%0d pool_reads=%0d compute_cycles=%0d total_cycles=%0d adapter_cache_run=%0d",
            rows,columns,tiles,rows*windows,pool_read_count-reads_before,
            cycles-compute_begin,cycles-begin_cycle,adapter_cache_runs);
        if (ADAPTER_CACHE_TEST)
            adapter_cache_runs++;
    endtask

    initial begin
        expected_tiles = 0;
        repeat (5) @(negedge clk);
        rst_n = 1;
        if (ADAPTER_CACHE_TEST) begin
            run_matrix(5280,10560);
            run_matrix(5280,10560);
            run_matrix(5280,10560);
        end else begin
            run_matrix(17920,5280);
            run_matrix(5280,17920);
            run_matrix(5280,10560);
            run_matrix(15840,5280);
            run_matrix(5280,5280);
            run_matrix(2048,2048);
            run_matrix(5632,2048);
            run_matrix(2048,5632);
            run_matrix(4096,2560);
            run_matrix(1024,2560);
            run_matrix(2560,4096);
            run_matrix(7168,2560);
            run_matrix(2560,7168);
            if (checked_rows != 76736 || checked_tiles != expected_tiles)
                $fatal(1, "incomplete full-matrix coverage");
        end
        $display("PASS sustained array throughput: trits_per_cycle=%0d; executed_cycles=%0d",
            TRITS_PER_CYCLE,executed_subchunks);
        $display("PASS runtime storage-to-array: channels=%0d valid rows=%0d tiles=%0d",
            CHANNELS, checked_rows, checked_tiles);
        $finish;
    end
endmodule
