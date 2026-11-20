`timescale 1ns / 1ps

module tb_rtwsr_runtime_weight_pool;
    localparam int ROWS = 17920;
    localparam int COLUMNS = 5280;
    localparam int WINDOWS = 21;
    localparam int TILES = 187;
    localparam int RECORDS = ROWS * WINDOWS;
    localparam int WORDS_PER_PORT = TILES * WINDOWS * 4;

    logic clk = 1'b0;
    logic rst_n = 1'b0;
    logic load_start = 1'b0;
    logic [15:0] load_rows = '0;
    logic [15:0] load_columns = '0;
    logic load_valid = 1'b0;
    logic load_ready;
    logic [511:0] load_data = '0;
    logic load_last = 1'b0;
    logic load_busy;
    logic load_done;
    logic protocol_error;
    logic [6:0] load_window_count;
    logic [14:0] load_words_per_port;
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

    rtwsr_runtime_weight_pool dut (
        .activate_loaded_weights(1'b0), .consumed_tile_valid(1'b0),
        .consumed_tile_index(9'd0), .*
    );

    function automatic logic [511:0] marker(input integer record_index);
        marker = 512'(record_index) ^ 512'h6a09e667f3bcc908bb67ae8584caa73b;
    endfunction

    task automatic push_record(input integer index);
        begin
            @(negedge clk);
            load_valid = 1'b1;
            load_data = marker(index);
            load_last = (index == RECORDS - 1);
            if (!load_ready)
                $fatal(1, "runtime pool stopped accepting weight record %0d", index);
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

    integer row;
    integer window;
    integer tile;
    integer slot;
    initial begin
        repeat (3) @(posedge clk);
        @(negedge clk);
        rst_n = 1'b1;
        load_rows = 16'(ROWS);
        load_columns = 16'(COLUMNS);
        load_start = 1'b1;
        @(posedge clk);
        #1 load_start = 1'b0;
        if (!load_busy || load_window_count != WINDOWS || load_words_per_port != WORDS_PER_PORT)
            $fatal(1, "runtime descriptor mismatch windows=%0d words=%0d", load_window_count,
                   load_words_per_port);

        for (row = 0; row < ROWS; row = row + 1)
            for (window = 0; window < WINDOWS; window = window + 1)
                push_record(row * WINDOWS + window);

        @(negedge clk);
        load_valid = 1'b0;
        if (load_busy || !load_done || protocol_error)
            $fatal(1, "full runtime weight load failed busy=%0d done=%0d error=%0d",
                   load_busy, load_done, protocol_error);

        for (tile = 0; tile < TILES; tile = tile + 1)
            for (window = 0; window < WINDOWS; window = window + 1)
                for (slot = 0; slot < 4; slot = slot + 1)
                    check_pool_address(tile, window, slot);
        if (checked_records != RECORDS)
            $fatal(1, "test did not cover every runtime weight record: %0d/%0d",
                   checked_records, RECORDS);

        @(negedge clk);
        pool_read_enable = 1'b0;
        load_rows = 16'(17920);
        load_columns = 16'(17920);
        load_start = 1'b1;
        @(posedge clk);
        #1 load_start = 1'b0;
        if (load_busy || !load_done || !protocol_error)
            $fatal(1, "over-capacity runtime descriptor was not rejected");

        $display("PASS: runtime USW pool loaded and read back %0d records; words_per_port=%0d",
                 RECORDS, WORDS_PER_PORT);
        $finish;
    end
endmodule
