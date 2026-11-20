`timescale 1ns / 1ps

module tb_rtwsr_streaming_weight_store;
    localparam int P_CH = 32;
    localparam int C_OUT_PER_SLR = 1760;
    localparam int SLR_COUNT = 3;
    localparam int WINDOW_COUNT = 70;
    localparam int RING_DEPTH = 73728;
    localparam int OPERATOR_WORDS = SLR_COUNT*C_OUT_PER_SLR*WINDOW_COUNT;
    localparam int CHANNEL_WIDTH = $clog2(C_OUT_PER_SLR);
    localparam int WINDOW_WIDTH = $clog2(WINDOW_COUNT);

    logic clk = 1'b0;
    logic rst_n = 1'b0;
    logic start = 1'b0;
    logic abort = 1'b0;
    logic stream_valid = 1'b0;
    logic stream_ready;
    logic [511:0] stream_data = '0;
    logic stream_last = 1'b0;
    logic [SLR_COUNT-1:0] pool_valid;
    logic [SLR_COUNT-1:0] pool_ready = '0;
    logic [SLR_COUNT*CHANNEL_WIDTH-1:0] pool_channel;
    logic [SLR_COUNT*WINDOW_WIDTH-1:0] pool_window;
    logic [SLR_COUNT*512-1:0] pool_data;
    logic busy;
    logic load_done;
    logic protocol_error;
    logic [16:0] occupancy;
    integer output_count = 0;
    integer load_done_count = 0;
    integer accepted = 0;
    integer expected_channel;
    integer expected_slr;
    integer expected_local_channel;
    integer expected_window;
    integer observed_slr;
    integer observed_channel;
    integer observed_window;
    integer cycle_count = 0;

    always #1 clk = ~clk;

    always @(posedge clk) begin
        cycle_count <= cycle_count + 1;
        if (cycle_count > 2 * OPERATOR_WORDS)
            $fatal(1, "streaming-store timeout: accepted=%0d output=%0d occupancy=%0d error=%0b",
                   accepted, output_count, occupancy, protocol_error);
        if (load_done)
            load_done_count <= load_done_count + 1;
        if (pool_valid != '0) begin
            if ($countones(pool_valid) != 1)
                $fatal(1, "more than one SLR received a pool write");
            for (integer slr = 0; slr < SLR_COUNT; slr++) begin
                if (pool_valid[slr] && pool_ready[slr]) begin
                    expected_channel = output_count / WINDOW_COUNT;
                    expected_slr = expected_channel / C_OUT_PER_SLR;
                    expected_local_channel = expected_channel % C_OUT_PER_SLR;
                    expected_window = output_count % WINDOW_COUNT;
                    observed_channel = pool_channel[slr*CHANNEL_WIDTH +: CHANNEL_WIDTH];
                    observed_window = pool_window[slr*WINDOW_WIDTH +: WINDOW_WIDTH];
                    observed_slr = slr;
                    if (observed_slr != expected_slr ||
                        observed_channel != expected_local_channel ||
                        observed_window != expected_window ||
                        pool_data[slr*512 +: 512] !== 512'(output_count))
                        $fatal(1, "routed output mismatch at record %0d", output_count);
                    output_count <= output_count + 1;
                end
            end
        end
    end

    rtwsr_streaming_weight_store #(
        .P_CH(P_CH),
        .C_OUT_PER_SLR(C_OUT_PER_SLR),
        .SLR_COUNT(SLR_COUNT),
        .WINDOW_COUNT(WINDOW_COUNT),
        .RING_DEPTH(RING_DEPTH)
    ) dut (.*);

    task automatic push_record(input integer index);
        begin
            @(negedge clk);
            stream_valid = 1'b1;
            stream_data = 512'(index);
            stream_last = (index == OPERATOR_WORDS - 1);
            do @(posedge clk); while (!stream_ready);
            accepted = accepted + 1;
        end
    endtask

    initial begin
        repeat (4) @(posedge clk);
        @(negedge clk);
        rst_n = 1'b1;
        start = 1'b1;
        @(posedge clk);
        #1;
        @(negedge clk);
        start = 1'b0;

        for (integer index = 0; index < RING_DEPTH; index++)
            push_record(index);
        @(negedge clk);
        stream_valid = 1'b0;
        if (accepted != RING_DEPTH || stream_ready || occupancy != RING_DEPTH)
            $fatal(1, "shadow ring did not apply full-capacity backpressure");

        pool_ready = '1;
        for (integer index = RING_DEPTH; index < OPERATOR_WORDS; index++)
            push_record(index);
        @(negedge clk);
        stream_valid = 1'b0;
        while (output_count < OPERATOR_WORDS) @(negedge clk);
        repeat (2) @(posedge clk);
        if (accepted != OPERATOR_WORDS || output_count != OPERATOR_WORDS ||
            load_done_count != 1 || busy || occupancy != 0 || protocol_error)
            $fatal(1, "full-operator stream did not complete cleanly");

        $display("PASS: full operator %0d records routed across %0d SLR pools in channel-major order", OPERATOR_WORDS, SLR_COUNT);
        $display("PASS: shared shadow ring capacity %0d records; stream backpressure asserted at full occupancy", RING_DEPTH);
        $display("PASS: ring write/read pointers crossed capacity boundary and drained to zero");
        $finish;
    end
endmodule
