`timescale 1ns / 1ps

module tb_rtwsr_runtime_weight_overlap;
    logic clk = 0, rst_n = 0, load_start = 0, load_abort = 0;
    logic [15:0] load_rows = 0, load_columns = 0;
    logic weight_stream_valid = 0, weight_stream_ready, weight_stream_last = 0;
    logic [511:0] weight_stream_data = 0;
    logic pool_drain_enable = 1;
    logic weight_store_busy, weight_load_done, weight_protocol_error;
    logic [16:0] shadow_occupancy;
    logic [6:0] pool_window_count;
    logic [14:0] pool_words_per_port;
    logic activate_loaded_weights = 0, consumed_tile_valid = 0;
    logic [8:0] consumed_tile_index = 0;
    logic pool_read_enable = 0, pool_read_valid, pool_read_error;
    logic [8:0] pool_read_tile_index = 0;
    logic [6:0] pool_read_window_index = 0;
    logic [1:0] pool_read_subword_index = 0;
    logic [12287:0] pool_read_data;
    integer checked_records = 0, simultaneous_cycles = 0, blocked_cycles = 0;
    integer cycles = 0;
    integer waited_cycles;
    bit producer_done = 0;

    always #5 clk = ~clk;
    always @(posedge clk) begin
        cycles++;
        if (rst_n && dut.pool_stream_valid && !dut.pool_stream_ready)
            blocked_cycles++;
        if (rst_n && pool_read_enable && dut.output_fire)
            simultaneous_cycles++;
        if (cycles > 8000000) $fatal(1, "overlap regression timeout");
    end

    rtwsr_runtime_weight_subsystem #(.OVERLAP_READ(1'b1)) dut (.*);

    function automatic logic [511:0] marker(input integer matrix_id, row_id, window_id);
        logic [511:0] value;
        for (integer lane = 0; lane < 16; lane++)
            value[lane*32 +: 32] = 32'(matrix_id*1000003 + row_id*131 + window_id*17 + lane);
        return value;
    endfunction

    task automatic begin_load(input integer rows, columns);
        @(negedge clk);
        load_rows = 16'(rows);
        load_columns = 16'(columns);
        load_start = 1;
        @(negedge clk);
        load_start = 0;
        if (!weight_store_busy || weight_protocol_error)
            $fatal(1, "load descriptor rejected %0dx%0d", rows, columns);
    endtask

    task automatic stream_matrix(input integer matrix_id, rows, columns);
        integer windows;
        windows = (columns+255)/256;
        for (integer row_id = 0; row_id < rows; row_id++) begin
            for (integer window_id = 0; window_id < windows; window_id++) begin
                weight_stream_valid = 1;
                weight_stream_data = marker(matrix_id, row_id, window_id);
                weight_stream_last = row_id == rows-1 && window_id == windows-1;
                do @(posedge clk); while (!weight_stream_ready);
                @(negedge clk);
            end
        end
        weight_stream_valid = 0;
        weight_stream_last = 0;
        while (!weight_load_done) @(negedge clk);
        if (weight_store_busy || shadow_occupancy != 0 || weight_protocol_error)
            $fatal(1, "matrix load did not finish cleanly");
        producer_done = 1;
    endtask

    task automatic activate;
        @(negedge clk);
        activate_loaded_weights = 1;
        @(negedge clk);
        activate_loaded_weights = 0;
        if (weight_protocol_error) $fatal(1, "matrix activation rejected");
    endtask

    task automatic consume_matrix(input integer matrix_id, rows, columns);
        integer windows, tiles, row_id;
        windows = (columns+255)/256;
        tiles = (rows+95)/96;
        for (integer tile_id = 0; tile_id < tiles; tile_id++) begin
            for (integer window_id = 0; window_id < windows; window_id++) begin
                for (integer slot_id = 0; slot_id < 4; slot_id++) begin
                    @(negedge clk);
                    pool_read_enable = 1;
                    pool_read_tile_index = 9'(tile_id);
                    pool_read_window_index = 7'(window_id);
                    pool_read_subword_index = 2'(slot_id);
                    @(posedge clk);
                    #1;
                    if (pool_read_valid)
                        $fatal(1, "runtime read returned before the two address slices");
                    @(negedge clk);
                    pool_read_enable = 0;
                    waited_cycles = 0;
                    while (!pool_read_valid && waited_cycles < 4) begin
                        @(posedge clk);
                        #1;
                        waited_cycles++;
                    end
                    if (waited_cycles != 2)
                        $fatal(1, "runtime read latency mismatch: %0d cycles", waited_cycles);
                    if (!pool_read_valid || pool_read_error || weight_protocol_error)
                        $fatal(1, "active descriptor changed during overwrite");
                    for (integer bank_id = 0; bank_id < 24; bank_id++) begin
                        row_id = tile_id*96 + bank_id*4 + slot_id;
                        if (row_id < rows) begin
                            if (pool_read_data[bank_id*512 +: 512] !==
                                marker(matrix_id, row_id, window_id))
                                $fatal(1, "unconsumed data overwritten matrix=%0d row=%0d window=%0d",
                                       matrix_id, row_id, window_id);
                            checked_records++;
                        end
                    end
                end
            end
            @(negedge clk);
            pool_read_enable = 0;
            consumed_tile_valid = 1;
            consumed_tile_index = 9'(tile_id);
            @(negedge clk);
            consumed_tile_valid = 0;
            // Allow DMA to reach the released frontier before the next tile.
            // Backpressure remains active if the next matrix has a wider stride.
            repeat ((tile_id%7 == 0) ? 2600 : 2) @(negedge clk);
        end
        if (weight_protocol_error) $fatal(1, "tile release rejected");
    endtask

    task automatic run_pair(input integer matrix_id, rows, columns, next_rows, next_columns);
        integer initial_checked, initial_overlap, initial_blocked;
        initial_checked = checked_records;
        initial_overlap = simultaneous_cycles;
        initial_blocked = blocked_cycles;
        producer_done = 0;
        begin_load(rows, columns);
        stream_matrix(matrix_id, rows, columns);
        activate();
        producer_done = 0;
        begin_load(next_rows, next_columns);
        fork
            stream_matrix(matrix_id+1, next_rows, next_columns);
            begin
                // Before any tile is consumed, the ring must fill without a pool write.
                while (int'(shadow_occupancy) !=
                    ((next_rows*((next_columns+255)/256) < 73728) ?
                     next_rows*((next_columns+255)/256) : 73728)) @(negedge clk);
                repeat (12) begin
                    @(negedge clk);
                    if (weight_stream_ready || dut.output_record_index_q != 0)
                        $fatal(1, "prefetch overwrote a live tile before release");
                end
                consume_matrix(matrix_id, rows, columns);
            end
        join
        if (!producer_done || simultaneous_cycles == initial_overlap ||
            blocked_cycles == initial_blocked)
            $fatal(1, "regression missed read/write overlap or protected-write stalls");
        activate();
        consume_matrix(matrix_id+1, next_rows, next_columns);
        if (checked_records-initial_checked !=
            rows*((columns+255)/256) + next_rows*((next_columns+255)/256))
            $fatal(1, "incomplete full-matrix coverage");
        $display("PASS overwrite %0dx%0d -> %0dx%0d records=%0d simultaneous_cycles=%0d protected_stalls=%0d",
            rows, columns, next_rows, next_columns, checked_records-initial_checked,
            simultaneous_cycles-initial_overlap, blocked_cycles-initial_blocked);
        @(negedge clk);
        consumed_tile_valid = 1;
        consumed_tile_index = 0;
        @(negedge clk);
        consumed_tile_valid = 0;
        if (!weight_protocol_error) $fatal(1, "duplicate tile release was accepted");
        // Reset between model workloads; the same fixed-capacity memories are reused.
        @(negedge clk); load_abort = 1;
        @(negedge clk); load_abort = 0;
        if (weight_protocol_error || shadow_occupancy != 0 || weight_store_busy)
            $fatal(1, "abort did not clear overlap control and FIFO state");
    endtask

    initial begin
        repeat (4) @(negedge clk);
        rst_n = 1;
        run_pair(1, 17920, 5280, 5280, 17920);
        run_pair(3, 5280, 17920, 17920, 5280);
        // Smaller full operators fit in the ring; all model dimensions remain exact.
        run_pair(5, 7168, 2560, 2560, 7168);
        run_pair(7, 5632, 2048, 2048, 5632);
        @(negedge clk); activate_loaded_weights = 1;
        @(negedge clk); activate_loaded_weights = 0;
        if (!weight_protocol_error) $fatal(1, "an unloaded matrix was activated");
        $display("PASS full-shape overlap checked_records=%0d", checked_records);
        $finish;
    end
endmodule
