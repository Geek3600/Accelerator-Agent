`timescale 1ns/1ps

module portable_memory_state_dut (
    input  logic        clock,
    input  logic        reset,
    input  logic        enable,
    output logic [7:0]  counter,
    output logic [31:0] checksum,
    output logic [3:0]  write_index,
    output logic [3:0]  read_index,
    output logic [31:0] memory_probe
);
    logic [31:0] memory [0:15];

    assign memory_probe = memory[read_index];

    always_ff @(posedge clock) begin : state_update
        integer index;
        if (reset) begin
            counter     <= 8'd0;
            checksum    <= 32'd0;
            write_index <= 4'd0;
            read_index  <= 4'd7;
            for (index = 0; index < 16; index = index + 1)
                memory[index] <= 32'h1000_0000 + index;
        end else if (enable) begin
            counter <= counter + 8'd1;
            checksum <= {checksum[30:0], checksum[31]}
                ^ memory[read_index]
                ^ {24'd0, counter};
            memory[write_index] <= memory[write_index]
                ^ 32'ha500_0000
                ^ {24'd0, counter};
            write_index <= write_index + 4'd3;
            read_index  <= read_index + 4'd5;
        end
    end
endmodule

module portable_memory_state_tb;
    logic clock = 1'b0;
    logic reset = 1'b1;
    logic enable = 1'b0;
    logic [7:0] counter;
    logic [31:0] checksum;
    logic [3:0] write_index;
    logic [3:0] read_index;
    logic [31:0] memory_probe;
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

    portable_memory_state_dut dut (
        .clock        (clock),
        .reset        (reset),
        .enable       (enable),
        .counter      (counter),
        .checksum     (checksum),
        .write_index  (write_index),
        .read_index   (read_index),
        .memory_probe (memory_probe)
    );

    always #5 clock = ~clock;

    task automatic write_suffix_evidence;
        begin
            $fdisplay(
                progress_fd,
                "{\"schema_version\":\"spatialaccagent.board_progress_event.v1\",\"sequence\":%0d,\"cycle\":%0d,\"event_kind\":\"semantic_progress\",\"phase\":\"portable_memory_suffix_step\",\"semantic_progress\":true,\"progress_epoch\":%0d,\"layer\":0,\"token\":0,\"beat\":%0d,\"stage_or_boundary\":\"fixture.dut_memory_output\",\"counter\":%0d,\"checksum\":%0d,\"write_index\":%0d,\"read_index\":%0d,\"memory_probe\":%0d}",
                counter,
                counter,
                counter,
                suffix_index,
                counter,
                checksum,
                write_index,
                read_index,
                memory_probe
            );
            $fflush(progress_fd);
        end
    endtask

    initial begin
        if (!$value$plusargs("CHECKPOINT_MODE=%s", checkpoint_mode))
            checkpoint_mode = "capture";
        if (!$value$plusargs("STATE_PATH=%s", state_path))
            state_path = "portable_memory_state.bin";
        if (!$value$plusargs("SCHEMA_PATH=%s", schema_path))
            schema_path = "portable_memory_state.schema";
        if (!$value$plusargs("PROGRESS_PATH=%s", progress_path))
            progress_path = "memory_progress.jsonl";
        if (!$value$plusargs("RTL_OUTPUT_PATH=%s", rtl_output_path))
            rtl_output_path = "memory_rtl_output.txt";
        if (!$value$plusargs("BOUNDARY_PATH=%s", boundary_path))
            boundary_path = "memory_boundary.json";
        if (!$value$plusargs("EXTERNAL_STATE_PATH=%s", external_state_path))
            external_state_path = "memory_testbench_external_state.txt";
        progress_fd = $fopen(progress_path, "w");
        rtl_output_fd = $fopen(rtl_output_path, "w");
        boundary_fd = $fopen(boundary_path, "w");
        if (progress_fd == 0 || rtl_output_fd == 0 || boundary_fd == 0)
            $fatal(1, "portable memory evidence file open failed");

        repeat (2) @(posedge clock);
        @(negedge clock);
        reset = 1'b0;

        if (checkpoint_mode == "restore") begin
            external_state_fd = $fopen(external_state_path, "r");
            if (external_state_fd == 0)
                $fatal(1, "portable memory external state open failed");
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
                $fatal(1, "portable memory external state parse failed");
            $fclose(external_state_fd);
            checkpoint_rc = $spatialacc_state_restore(
                state_path,
                "portable_memory_state_tb.dut",
                schema_path
            );
            if (checkpoint_rc != 0)
                $fatal(1, "portable memory state restore failed rc=%0d", checkpoint_rc);
            if (
                counter != restored_sequence[7:0]
                || counter != restored_cycle[7:0]
            )
                $fatal(1, "portable memory external state anchor mismatch");
            if (
                restored_progress_offset != 0
                || restored_rtl_offset != 0
                || restored_boundary_offset != 0
            )
                $fatal(1, "portable memory external file offset mismatch");
            enable = restored_enable[0];
            for (suffix_index = 0; suffix_index < 4; suffix_index = suffix_index + 1) begin
                @(posedge clock);
                @(negedge clock);
                write_suffix_evidence();
            end
            $display(
                "SPATIALACC_PORTABLE_MEMORY_RESTORE_PASS counter=%0d checksum=%0d probe=%0d",
                counter,
                checksum,
                memory_probe
            );
        end else begin
            enable = 1'b1;
            repeat (7) @(posedge clock);
            @(negedge clock);
            checkpoint_rc = $spatialacc_state_capture(
                state_path,
                "portable_memory_state_tb.dut",
                schema_path
            );
            if (checkpoint_rc != 0)
                $fatal(1, "portable memory state capture failed rc=%0d", checkpoint_rc);
            external_state_fd = $fopen(external_state_path, "w");
            if (external_state_fd == 0)
                $fatal(1, "portable memory external state create failed");
            $fdisplay(
                external_state_fd,
                "%0d %0d %0d 0 0 0",
                enable,
                counter,
                counter
            );
            $fclose(external_state_fd);
            for (suffix_index = 0; suffix_index < 4; suffix_index = suffix_index + 1) begin
                @(posedge clock);
                @(negedge clock);
                write_suffix_evidence();
            end
            $display(
                "SPATIALACC_PORTABLE_MEMORY_CAPTURE_PASS counter=%0d checksum=%0d probe=%0d",
                counter,
                checksum,
                memory_probe
            );
        end
        $fdisplay(
            rtl_output_fd,
            "counter=%0d checksum=%0d write_index=%0d read_index=%0d probe=%0d",
            counter,
            checksum,
            write_index,
            read_index,
            memory_probe
        );
        $fdisplay(
            boundary_fd,
            "{\"counter\":%0d,\"checksum\":%0d,\"write_index\":%0d,\"read_index\":%0d,\"memory_probe\":%0d,\"suffix_cycles\":4}",
            counter,
            checksum,
            write_index,
            read_index,
            memory_probe
        );
        $fclose(progress_fd);
        $fclose(rtl_output_fd);
        $fclose(boundary_fd);
        $finish;
    end
endmodule
