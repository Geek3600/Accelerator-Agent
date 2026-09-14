`timescale 1ns/1ps

module portable_state_dut (
    input  logic       clock,
    input  logic       reset,
    input  logic       enable,
    output logic [7:0] counter,
    output logic [7:0] accumulator
);
    always_ff @(posedge clock) begin
        if (reset) begin
            counter     <= 8'd0;
            accumulator <= 8'd0;
        end else if (enable) begin
            counter <= counter + 8'd1;
`ifdef SPATIALACC_CHECKPOINT_CHANGED_LOGIC
            accumulator <= accumulator + 8'd3;
`else
            accumulator <= accumulator + 8'd1;
`endif
        end
    end
endmodule

module portable_state_tb;
    logic clock = 1'b0;
    logic reset = 1'b1;
    logic enable = 1'b0;
    logic [7:0] counter;
    logic [7:0] accumulator;
    string checkpoint_mode;
    string state_path;
    string schema_path;
    string progress_path;
    string rtl_output_path;
    string boundary_path;
    string external_state_path;
    integer checkpoint_rc;
    integer progress_fd;
    integer rtl_output_fd;
    integer boundary_fd;
    integer external_state_fd;
    integer suffix_index;
    integer restored_enable;
    integer restored_sequence;
    integer restored_cycle;
    integer restored_progress_offset;
    integer restored_rtl_offset;
    integer restored_boundary_offset;

    portable_state_dut dut (
        .clock       (clock),
        .reset       (reset),
        .enable      (enable),
        .counter     (counter),
        .accumulator (accumulator)
    );

    always #5 clock = ~clock;

    task automatic write_suffix_evidence;
        begin
            $fdisplay(
                progress_fd,
                "{\"schema_version\":\"spatialaccagent.board_progress_event.v1\",\"sequence\":%0d,\"cycle\":%0d,\"event_kind\":\"semantic_progress\",\"phase\":\"portable_suffix_step\",\"semantic_progress\":true,\"progress_epoch\":%0d,\"layer\":0,\"token\":0,\"beat\":%0d,\"stage_or_boundary\":\"fixture.dut_output\",\"counter\":%0d,\"accumulator\":%0d}",
                counter,
                counter,
                counter,
                suffix_index,
                counter,
                accumulator
            );
            $fflush(progress_fd);
        end
    endtask

    initial begin
        if (!$value$plusargs("CHECKPOINT_MODE=%s", checkpoint_mode))
            checkpoint_mode = "capture";
        if (!$value$plusargs("STATE_PATH=%s", state_path))
            state_path = "portable_state.bin";
        if (!$value$plusargs("SCHEMA_PATH=%s", schema_path))
            schema_path = "portable_state.schema";
        if (!$value$plusargs("PROGRESS_PATH=%s", progress_path))
            progress_path = "progress.jsonl";
        if (!$value$plusargs("RTL_OUTPUT_PATH=%s", rtl_output_path))
            rtl_output_path = "rtl_output.txt";
        if (!$value$plusargs("BOUNDARY_PATH=%s", boundary_path))
            boundary_path = "boundary.json";
        if (!$value$plusargs("EXTERNAL_STATE_PATH=%s", external_state_path))
            external_state_path = "testbench_external_state.txt";
        progress_fd = $fopen(progress_path, "w");
        rtl_output_fd = $fopen(rtl_output_path, "w");
        boundary_fd = $fopen(boundary_path, "w");
        if (progress_fd == 0 || rtl_output_fd == 0 || boundary_fd == 0)
            $fatal(1, "portable evidence file open failed");

        repeat (2) @(posedge clock);
        @(negedge clock);
        reset = 1'b0;

        if (checkpoint_mode == "restore") begin
            external_state_fd = $fopen(external_state_path, "r");
            if (external_state_fd == 0)
                $fatal(1, "portable external state open failed");
            if ($fscanf(
                external_state_fd,
                "%d %d %d %d %d %d",
                restored_enable,
                restored_sequence,
                restored_cycle,
                restored_progress_offset,
                restored_rtl_offset,
                restored_boundary_offset
            ) != 6)
                $fatal(1, "portable external state parse failed");
            $fclose(external_state_fd);
            checkpoint_rc = $spatialacc_state_restore(
                state_path,
                "portable_state_tb.dut",
                schema_path
            );
            if (checkpoint_rc != 0)
                $fatal(1, "portable state restore failed rc=%0d", checkpoint_rc);
            if (counter != restored_sequence || counter != restored_cycle)
                $fatal(1, "portable external state anchor mismatch");
            if (
                restored_progress_offset != 0
                || restored_rtl_offset != 0
                || restored_boundary_offset != 0
            )
                $fatal(1, "portable external file offset mismatch");
            enable = restored_enable[0];
            for (suffix_index = 0; suffix_index < 3; suffix_index = suffix_index + 1) begin
                @(posedge clock);
                @(negedge clock);
                write_suffix_evidence();
            end
            $display(
                "SPATIALACC_PORTABLE_RESTORE_PASS counter=%0d accumulator=%0d",
                counter,
                accumulator
            );
        end else begin
            enable = 1'b1;
            repeat (5) @(posedge clock);
            @(negedge clock);
            checkpoint_rc = $spatialacc_state_capture(
                state_path,
                "portable_state_tb.dut",
                schema_path
            );
            if (checkpoint_rc != 0)
                $fatal(1, "portable state capture failed rc=%0d", checkpoint_rc);
            external_state_fd = $fopen(external_state_path, "w");
            if (external_state_fd == 0)
                $fatal(1, "portable external state create failed");
            $fdisplay(
                external_state_fd,
                "%0d %0d %0d 0 0 0",
                enable,
                counter,
                counter
            );
            $fclose(external_state_fd);
            for (suffix_index = 0; suffix_index < 3; suffix_index = suffix_index + 1) begin
                @(posedge clock);
                @(negedge clock);
                write_suffix_evidence();
            end
            $display(
                "SPATIALACC_PORTABLE_CAPTURE_PASS counter=%0d accumulator=%0d",
                counter,
                accumulator
            );
        end
        $fdisplay(rtl_output_fd, "counter=%0d accumulator=%0d", counter, accumulator);
        $fdisplay(
            boundary_fd,
            "{\"counter\":%0d,\"accumulator\":%0d,\"suffix_cycles\":3}",
            counter,
            accumulator
        );
        $fclose(progress_fd);
        $fclose(rtl_output_fd);
        $fclose(boundary_fd);
        $finish;
    end
endmodule
