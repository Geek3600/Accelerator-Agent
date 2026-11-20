`timescale 1ns / 1ps

module tb_rtwsr_runtime_weight_subsystem;
    localparam int ROWS = 17920;
    localparam int COLUMNS = 5280;
    localparam int WINDOWS = 21;
    localparam int TILES = 187;
    localparam int RECORDS = ROWS * WINDOWS;
    localparam int WORDS_PER_PORT = TILES * WINDOWS * 4;
    localparam int RING_DEPTH = 73728;

    logic clk = 1'b0;
    logic rst_n = 1'b0;
    logic load_start = 1'b0;
    logic load_abort = 1'b0;
    logic [15:0] load_rows = '0;
    logic [15:0] load_columns = '0;
    logic weight_stream_valid = 1'b0;
    logic weight_stream_ready;
    logic [511:0] weight_stream_data = '0;
    logic weight_stream_last = 1'b0;
    logic pool_drain_enable = 1'b0;
    logic weight_store_busy;
    logic weight_load_done;
    logic weight_protocol_error;
    logic [16:0] shadow_occupancy;
    logic [6:0] pool_window_count;
    logic [14:0] pool_words_per_port;
    logic pool_read_enable = 1'b0;
    logic [8:0] pool_read_tile_index = '0;
    logic [6:0] pool_read_window_index = '0;
    logic [1:0] pool_read_subword_index = '0;
    logic pool_read_valid;
    logic [24*512-1:0] pool_read_data;
    logic pool_read_error;
    logic parallel_load_valid = 1'b0;
    logic parallel_load_ready;
    logic [23:0] parallel_load_enable = '0;
    logic [24*14-1:0] parallel_load_address = '0;
    logic [24*512-1:0] parallel_load_data = '0;
    integer checked_records = 0;
    integer waited_cycles;

    always #5 clk = ~clk;

    rtwsr_runtime_weight_subsystem #(.RING_DEPTH(RING_DEPTH)) dut (
        .activate_loaded_weights(1'b0), .consumed_tile_valid(1'b0),
        .consumed_tile_index(9'd0), .*
    );

    function automatic logic [511:0] marker(input integer record_index);
        marker = 512'(record_index) ^ 512'h6a09e667f3bcc908bb67ae8584caa73b;
    endfunction

    task automatic push_record(input integer index);
        begin
            @(negedge clk);
            weight_stream_valid = 1'b1;
            weight_stream_data = marker(index);
            weight_stream_last = (index == RECORDS - 1);
            if (!weight_stream_ready)
                $fatal(1, "weight stream stalled unexpectedly at record %0d", index);
            @(posedge clk);
            #1;
        end
    endtask

    task automatic check_pool_address(
        input integer tile,
        input integer window,
        input integer slot
    );
        integer bank;
        integer slr;
        integer group_index;
        integer row;
        integer record_index;
        logic [511:0] expected;
        begin
            @(negedge clk);
            pool_read_enable = 1'b1;
            pool_read_tile_index = 9'(tile);
            pool_read_window_index = 7'(window);
            pool_read_subword_index = 2'(slot);
            @(posedge clk);
            #1;
            if (pool_read_valid)
                $fatal(1, "runtime read returned before the two address slices");
            @(negedge clk);
            pool_read_enable = 1'b0;
            waited_cycles = 0;
            while (!pool_read_valid && waited_cycles < 4) begin
                @(posedge clk);
                #1;
                waited_cycles++;
            end
            if (waited_cycles != 2)
                $fatal(1, "runtime read latency mismatch: %0d cycles", waited_cycles);
            if (!pool_read_valid || pool_read_error)
                $fatal(1, "pool read failed tile=%0d window=%0d slot=%0d", tile, window, slot);
            for (bank = 0; bank < 24; bank = bank + 1) begin
                slr = bank / 8;
                group_index = bank % 8;
                row = tile * 96 + slr * 32 + group_index * 4 + slot;
                if (row < ROWS) begin
                    record_index = row * WINDOWS + window;
                    expected = marker(record_index);
                    if (pool_read_data[bank*512 +: 512] !== expected)
                        $fatal(1, "pool data mismatch bank=%0d row=%0d window=%0d", bank, row, window);
                    checked_records = checked_records + 1;
                end
            end
        end
    endtask

    integer index;
    integer tile;
    integer window;
    integer slot;
    integer timeout;
    initial begin
        repeat (3) @(posedge clk);
        @(negedge clk);
        rst_n = 1'b1;
        load_rows = 16'(ROWS);
        load_columns = 16'(COLUMNS);
        load_start = 1'b1;
        @(posedge clk);
        #1 load_start = 1'b0;
        if (!weight_store_busy || pool_window_count != WINDOWS ||
            pool_words_per_port != WORDS_PER_PORT)
            $fatal(1, "runtime subsystem descriptor mismatch");

        for (index = 0; index < RING_DEPTH; index = index + 1)
            push_record(index);
        @(negedge clk);
        weight_stream_valid = 1'b0;
        if (shadow_occupancy != RING_DEPTH || weight_stream_ready)
            $fatal(1, "shadow FIFO did not reach its configured capacity");

        @(negedge clk);
        pool_drain_enable = 1'b1;
        for (index = RING_DEPTH; index < RECORDS; index = index + 1)
            push_record(index);
        @(negedge clk);
        weight_stream_valid = 1'b0;
        timeout = 0;
        while (!weight_load_done && timeout < 100000) begin
            @(posedge clk);
            #1 timeout = timeout + 1;
        end
        if (!weight_load_done || weight_store_busy || shadow_occupancy != 0 ||
            weight_protocol_error)
            $fatal(1, "runtime subsystem load failed busy=%0d occupancy=%0d error=%0d",
                   weight_store_busy, shadow_occupancy, weight_protocol_error);

        for (tile = 0; tile < TILES; tile = tile + 1)
            for (window = 0; window < WINDOWS; window = window + 1)
                for (slot = 0; slot < 4; slot = slot + 1)
                    check_pool_address(tile, window, slot);
        if (checked_records != RECORDS)
            $fatal(1, "test did not cover all records: %0d/%0d", checked_records, RECORDS);

        @(negedge clk);
        pool_read_enable = 1'b0;
        load_rows = 16'(17920);
        load_columns = 16'(17920);
        load_start = 1'b1;
        @(posedge clk);
        #1 load_start = 1'b0;
        if (weight_store_busy || !weight_load_done || !weight_protocol_error)
            $fatal(1, "over-capacity runtime descriptor was not rejected");

        $display("PASS: 128-URAM-equivalent shadow FIFO drained %0d records into 24 pool banks; words_per_port=%0d",
                 RECORDS, WORDS_PER_PORT);
        $finish;
    end
endmodule
