`timescale 1ns / 1ps

module rtwsr_runtime_weight_subsystem #(
    parameter int CHANNELS = 96,
    parameter int HBM_LOAD_LANES = 24,
    parameter int POOL_DEPTH = 16384,
    parameter int RING_DEPTH = 73728,
    parameter int RING_COUNT_WIDTH = $clog2(RING_DEPTH + 1),
    parameter bit OVERLAP_READ = 1'b0,
    parameter bit HBM_PARALLEL_LOAD = 1'b0,
    parameter bit READ_PARALLEL_SLOTS = 1'b0
)(
    input  logic                       clk,
    input  logic                       rst_n,
    input  logic                       load_start,
    input  logic                       load_abort,
    input  logic [15:0]                load_rows,
    input  logic [15:0]                load_columns,
    input  logic                       weight_stream_valid,
    output logic                       weight_stream_ready,
    input  logic [511:0]               weight_stream_data,
    input  logic                       weight_stream_last,
    input  logic                       pool_drain_enable,
    output logic                       weight_store_busy,
    output logic                       weight_load_done,
    output logic                       weight_protocol_error,
    output logic [RING_COUNT_WIDTH-1:0] shadow_occupancy,
    output logic [6:0]                 pool_window_count,
    output logic [14:0]                pool_words_per_port,
    input  logic                       activate_loaded_weights,
    input  logic                       consumed_tile_valid,
    input  logic [8:0]                 consumed_tile_index,
    input  logic                       pool_read_enable,
    input  logic [8:0]                 pool_read_tile_index,
    input  logic [6:0]                 pool_read_window_index,
    input  logic [1:0]                 pool_read_subword_index,
    output logic                       pool_read_valid,
    output logic [(READ_PARALLEL_SLOTS ? CHANNELS : CHANNELS/4)*512-1:0] pool_read_data,
    output logic                       pool_read_error,
    input  logic                       parallel_load_valid,
    output logic                       parallel_load_ready,
    input  logic [HBM_LOAD_LANES-1:0]         parallel_load_enable,
    input  logic [HBM_LOAD_LANES*14-1:0]      parallel_load_address,
    input  logic [HBM_LOAD_LANES*512-1:0]     parallel_load_data
);
    logic subsystem_rst_n;
    logic pool_busy;
    logic pool_stream_ready;
    logic pool_stream_valid;
    logic [511:0] pool_stream_data;
    logic pool_stream_last;
    logic ring_input_ready;
    logic ring_output_valid;
    logic ring_output_ready;
    logic [511:0] ring_output_data;
    logic [31:0] total_records_q;
    logic [31:0] input_record_index_q;
    logic [31:0] output_record_index_q;
    logic input_error_q;
    logic pool_protocol_error;
    logic input_expected_last;
    logic output_expected_last;
    logic [31:0] requested_windows;
    logic [31:0] requested_records;
    logic input_fire;
    logic output_fire;

    assign subsystem_rst_n = rst_n && !load_abort;
    assign requested_windows = (int'(load_columns) + 255) / 256;
    assign requested_records = int'(load_rows) * requested_windows;
    assign input_expected_last = input_record_index_q == total_records_q - 1'b1;
    assign output_expected_last = output_record_index_q == total_records_q - 1'b1;
    assign weight_stream_ready = !HBM_PARALLEL_LOAD && pool_busy && ring_input_ready &&
                                 (input_record_index_q < total_records_q) && !input_error_q;
    assign input_fire = weight_stream_valid && weight_stream_ready;
    assign pool_stream_valid = !HBM_PARALLEL_LOAD && ring_output_valid && pool_busy && pool_drain_enable;
    assign ring_output_ready = !HBM_PARALLEL_LOAD && pool_stream_ready && pool_busy && pool_drain_enable;
    assign pool_stream_data = HBM_PARALLEL_LOAD ? '0 : ring_output_data;
    assign pool_stream_last = output_expected_last;
    assign output_fire = pool_stream_valid && pool_stream_ready;
    assign weight_store_busy = pool_busy || (!HBM_PARALLEL_LOAD && shadow_occupancy != 0);
    assign weight_protocol_error = input_error_q || pool_read_error || pool_protocol_error;

    generate
        if (HBM_PARALLEL_LOAD) begin : gen_no_serial_shadow_fifo
            assign ring_input_ready = 1'b0;
            assign ring_output_valid = 1'b0;
            assign ring_output_data = '0;
            assign shadow_occupancy = '0;
        end else begin : gen_serial_shadow_fifo
            rtwsr_runtime_weight_ring #(.DEPTH(RING_DEPTH)) u_shadow_fifo (
                .clk(clk),
                .rst_n(subsystem_rst_n),
                .in_valid(input_fire),
                .in_ready(ring_input_ready),
                .in_data(weight_stream_data),
                .out_valid(ring_output_valid),
                .out_ready(ring_output_ready),
                .out_data(ring_output_data),
                .occupancy(shadow_occupancy)
            );
        end
    endgenerate

    rtwsr_runtime_weight_pool #(
        .CHANNELS(CHANNELS), .HBM_LOAD_LANES(HBM_LOAD_LANES),
        .POOL_DEPTH(POOL_DEPTH), .OVERLAP_READ(OVERLAP_READ),
        .HBM_PARALLEL_LOAD(HBM_PARALLEL_LOAD),
        .READ_PARALLEL_SLOTS(READ_PARALLEL_SLOTS)
    ) u_primary_pool (
        .clk(clk),
        .rst_n(subsystem_rst_n),
        .load_start(load_start),
        .load_rows(load_rows),
        .load_columns(load_columns),
        .load_valid(pool_stream_valid),
        .load_ready(pool_stream_ready),
        .load_data(pool_stream_data),
        .load_last(pool_stream_last),
        .load_busy(pool_busy),
        .load_done(weight_load_done),
        .protocol_error(pool_protocol_error),
        .load_window_count(pool_window_count),
        .load_words_per_port(pool_words_per_port),
        .activate_loaded_weights(activate_loaded_weights),
        .consumed_tile_valid(consumed_tile_valid),
        .consumed_tile_index(consumed_tile_index),
        .pool_read_enable(pool_read_enable),
        .pool_read_tile_index(pool_read_tile_index),
        .pool_read_window_index(pool_read_window_index),
        .pool_read_subword_index(pool_read_subword_index),
        .pool_read_valid(pool_read_valid),
        .pool_read_data(pool_read_data),
        .pool_read_error(pool_read_error),
        .parallel_load_valid(parallel_load_valid),
        .parallel_load_ready(parallel_load_ready),
        .parallel_load_enable(parallel_load_enable),
        .parallel_load_address(parallel_load_address),
        .parallel_load_data(parallel_load_data)
    );

    always_ff @(posedge clk) begin
        if (!subsystem_rst_n) begin
            total_records_q <= '0;
            input_record_index_q <= '0;
            output_record_index_q <= '0;
            input_error_q <= 1'b0;
        end else begin
            if (load_start && !pool_busy) begin
                total_records_q <= requested_records;
                input_record_index_q <= '0;
                output_record_index_q <= '0;
                input_error_q <= 1'b0;
            end

            if (input_fire) begin
                if (weight_stream_last != input_expected_last)
                    input_error_q <= 1'b1;
                input_record_index_q <= input_record_index_q + 1'b1;
            end

            if (output_fire && !output_expected_last)
                output_record_index_q <= output_record_index_q + 1'b1;
        end
    end
endmodule
