`timescale 1ns / 1ps

module rtwsr_hbm_read_dma_27pc #(
    // U280 exposes 32 pseudo-channels.  The 24-bank pool remains the
    // consumer-side width; unused channels are handled by the adapter.
    parameter int HBM_PCS = 32,
    parameter int POOL_LANES = 24,
    parameter int MAX_OUTSTANDING = 16,
    parameter bit ADAPTER_STATIC_REUSE = 1'b0,
    parameter int OUT_COUNT_WIDTH = $clog2(MAX_OUTSTANDING + 1),
    parameter int PTR_WIDTH = $clog2(MAX_OUTSTANDING)
)(
    input  logic                         clk,
    input  logic                         rst_n,
    input  logic                         load_start,
    input  logic                         load_skip_adapter_static,
    input  logic [4:0]                   load_first_pc,
    input  logic [HBM_PCS*33-1:0]        load_base_address,
    input  logic [HBM_PCS*32-1:0]        load_record_count,
    output logic                         busy,
    output logic                         load_done,
    output logic                         protocol_error,
    output logic [HBM_PCS*33-1:0]        m_axi_araddr,
    output logic [HBM_PCS*6-1:0]         m_axi_arid,
    output logic [HBM_PCS*4-1:0]         m_axi_arlen,
    output logic [HBM_PCS*3-1:0]         m_axi_arsize,
    output logic [HBM_PCS*2-1:0]         m_axi_arburst,
    output logic [HBM_PCS-1:0]           m_axi_arvalid,
    input  logic [HBM_PCS-1:0]           m_axi_arready,
    input  logic [HBM_PCS*6-1:0]         m_axi_rid,
    input  logic [HBM_PCS*256-1:0]       m_axi_rdata,
    input  logic [HBM_PCS*2-1:0]         m_axi_rresp,
    input  logic [HBM_PCS-1:0]           m_axi_rlast,
    input  logic [HBM_PCS-1:0]           m_axi_rvalid,
    output logic [HBM_PCS-1:0]           m_axi_rready,
    output logic [HBM_PCS-1:0]           stream_valid,
    input  logic [HBM_PCS-1:0]           stream_ready,
    output logic [HBM_PCS*256-1:0]       stream_data
);
    logic busy_q;
    logic [HBM_PCS-1:0] arvalid_q;
    logic [HBM_PCS*33-1:0] araddr_q;
    logic [HBM_PCS*4-1:0] arlen_q;
    logic [31:0] total_beats_q [0:HBM_PCS-1];
    logic [31:0] issued_beats_q [0:HBM_PCS-1];
    logic [31:0] received_beats_q [0:HBM_PCS-1];
    logic [OUT_COUNT_WIDTH-1:0] outstanding_q [0:HBM_PCS-1];
    logic [4:0] burst_length_q [0:HBM_PCS-1][0:MAX_OUTSTANDING-1];
    logic [PTR_WIDTH-1:0] burst_write_pointer_q [0:HBM_PCS-1];
    logic [PTR_WIDTH-1:0] burst_read_pointer_q [0:HBM_PCS-1];
    logic [4:0] response_beats_left_q [0:HBM_PCS-1];
    logic [HBM_PCS-1:0] rlast_fire;
    logic [HBM_PCS-1:0] response_error;
    logic [HBM_PCS-1:0] address_error;
    logic [HBM_PCS-1:0] lane_error_q;
    logic [HBM_PCS-1:0] all_channels_done;
    logic [31:0] beats_left [0:HBM_PCS-1];
    logic [12:0] beats_to_page_end [0:HBM_PCS-1];
    logic [4:0] next_burst_beats [0:HBM_PCS-1];
    logic [HBM_PCS-1:0] burst_request_valid;
    logic [HBM_PCS*4-1:0] burst_request_length;
    logic skip_adapter_q;
    logic [4:0] first_pc_q;
    logic [32:0] initial_base_q [0:HBM_PCS-1];
    logic [7:0] segment_q [0:HBM_PCS-1];
    logic [5:0] segment_beats_q [0:HBM_PCS-1];

    function automatic integer segment_offset(input integer channel, input integer first_pc,
                                               input integer segment);
        integer first_logical, original_logical;
        first_logical = first_pc + segment * 42 * POOL_LANES;
        first_logical += (channel - first_logical % 32 + 32) % 32;
        original_logical = first_pc + (channel - first_pc + 32) % 32;
        segment_offset = first_logical / 32 - original_logical / 32;
    endfunction

    function automatic integer segment_beats(input integer channel, input integer first_pc,
                                              input integer segment);
        integer first_logical, offset;
        first_logical = (first_pc + segment * 42 * POOL_LANES) % 32;
        offset = (channel - first_logical + 32) % 32;
        segment_beats = 2 * ((21 * POOL_LANES - 1 - offset) / 32 + 1);
    endfunction

    assign busy = busy_q;
    assign m_axi_arvalid = arvalid_q;
    assign m_axi_araddr = araddr_q;
    assign m_axi_arlen = arlen_q;
    assign m_axi_arid = '0;
    assign m_axi_arsize = {HBM_PCS{3'd5}};
    assign m_axi_arburst = {HBM_PCS{2'b01}};
    assign stream_valid = busy_q ? m_axi_rvalid : '0;
    assign stream_data = m_axi_rdata;
    assign m_axi_rready = {HBM_PCS{busy_q}} & stream_ready;

    always_comb begin
        protocol_error = |lane_error_q;
        for (integer channel = 0; channel < HBM_PCS; channel = channel + 1)
            address_error[channel] = |load_base_address[channel*33 +: 6];
    end

    genvar pc;
    generate
        for (pc = 0; pc < HBM_PCS; pc = pc + 1) begin : gen_pc
            logic [32:0] load_base;
            logic [31:0] load_records;
            logic [5:0] r_id;
            logic [1:0] r_resp;
            logic [4:0] response_length;
            logic expected_last;
            logic local_error;
            logic response_fire;
            logic ar_fire;

            assign load_base = load_base_address[pc*33 +: 33];
            assign load_records = load_record_count[pc*32 +: 32];
            assign r_id = m_axi_rid[pc*6 +: 6];
            assign r_resp = m_axi_rresp[pc*2 +: 2];
            assign response_length = burst_length_q[pc][burst_read_pointer_q[pc]];
            assign response_fire = m_axi_rvalid[pc] && m_axi_rready[pc];
            assign ar_fire = arvalid_q[pc] && m_axi_arready[pc];
            assign rlast_fire[pc] = response_fire && m_axi_rlast[pc];
            assign expected_last = response_beats_left_q[pc] == 0 ?
                response_length == 1 : response_beats_left_q[pc] == 1;
            assign local_error = response_fire &&
                (r_resp != 0 || r_id != 0 || (m_axi_rlast[pc] != expected_last));
            assign response_error[pc] = local_error;
            assign all_channels_done[pc] =
                issued_beats_q[pc] == total_beats_q[pc] &&
                received_beats_q[pc] == total_beats_q[pc] &&
                outstanding_q[pc] == 0 && !arvalid_q[pc];

            always_comb begin
                beats_left[pc] = total_beats_q[pc] - issued_beats_q[pc];
                beats_to_page_end[pc] = (13'd4096 - {1'b0, araddr_q[pc*33 +: 12]}) >> 5;
                next_burst_beats[pc] = 5'd16;
                if (beats_left[pc] < 16)
                    next_burst_beats[pc] = 5'(beats_left[pc]);
                if (beats_to_page_end[pc] < 13'(next_burst_beats[pc]))
                    next_burst_beats[pc] = 5'(beats_to_page_end[pc]);
                if (skip_adapter_q && segment_beats_q[pc] < {1'b0, next_burst_beats[pc]})
                    next_burst_beats[pc] = 5'(segment_beats_q[pc]);
                burst_request_valid[pc] = busy_q && !arvalid_q[pc] &&
                    issued_beats_q[pc] < total_beats_q[pc] &&
                    outstanding_q[pc] < OUT_COUNT_WIDTH'(MAX_OUTSTANDING) &&
                    next_burst_beats[pc] != 0;
                burst_request_length[pc*4 +: 4] = next_burst_beats[pc][3:0] - 1'b1;
            end

            always_ff @(posedge clk) begin
                if (!rst_n) begin
                    arvalid_q[pc] <= 1'b0;
                    araddr_q[pc*33 +: 33] <= '0;
                    arlen_q[pc*4 +: 4] <= '0;
                    total_beats_q[pc] <= '0;
                    issued_beats_q[pc] <= '0;
                    received_beats_q[pc] <= '0;
                    outstanding_q[pc] <= '0;
                    burst_write_pointer_q[pc] <= '0;
                    burst_read_pointer_q[pc] <= '0;
                    response_beats_left_q[pc] <= '0;
                    lane_error_q[pc] <= 1'b0;
                    initial_base_q[pc] <= '0;
                    segment_q[pc] <= '0;
                    segment_beats_q[pc] <= '0;
                end else begin
                    if (load_start && !busy_q) begin
                        total_beats_q[pc] <= load_records << 1;
                        issued_beats_q[pc] <= '0;
                        received_beats_q[pc] <= '0;
                        outstanding_q[pc] <= '0;
                        burst_write_pointer_q[pc] <= '0;
                        burst_read_pointer_q[pc] <= '0;
                        response_beats_left_q[pc] <= '0;
                        araddr_q[pc*33 +: 33] <= load_base;
                        initial_base_q[pc] <= load_base;
                        segment_q[pc] <= '0;
                        segment_beats_q[pc] <= 6'(segment_beats(pc, int'(load_first_pc), 0));
                        arvalid_q[pc] <= 1'b0;
                        lane_error_q[pc] <= address_error[pc];
                    end else if (burst_request_valid[pc] && !arvalid_q[pc]) begin
                        arvalid_q[pc] <= 1'b1;
                        arlen_q[pc*4 +: 4] <= burst_request_length[pc*4 +: 4];
                    end

                    if (arvalid_q[pc] && m_axi_arready[pc]) begin
                        arvalid_q[pc] <= 1'b0;
                        issued_beats_q[pc] <= issued_beats_q[pc] +
                            {28'd0, arlen_q[pc*4 +: 4]} + 1'b1;
                        if (skip_adapter_q && segment_beats_q[pc] ==
                            {2'b0, arlen_q[pc*4 +: 4]} + 1'b1 &&
                            int'(segment_q[pc]) < 55 * (96 / POOL_LANES) - 1) begin
                            segment_q[pc] <= segment_q[pc] + 1'b1;
                            segment_beats_q[pc] <= 6'(segment_beats(pc, int'(first_pc_q),
                                int'(segment_q[pc]) + 1));
                            araddr_q[pc*33 +: 33] <= initial_base_q[pc] +
                                33'(segment_offset(pc, int'(first_pc_q), int'(segment_q[pc]) + 1) * 64);
                        end else begin
                            araddr_q[pc*33 +: 33] <= araddr_q[pc*33 +: 33] +
                                ({29'd0, arlen_q[pc*4 +: 4]} + 1'b1) * 33'd32;
                            if (skip_adapter_q)
                                segment_beats_q[pc] <= segment_beats_q[pc] -
                                    {2'b0, arlen_q[pc*4 +: 4]} - 1'b1;
                        end
                        burst_length_q[pc][burst_write_pointer_q[pc]] <=
                            {1'b0, arlen_q[pc*4 +: 4]} + 5'd1;
                        if (burst_write_pointer_q[pc] == PTR_WIDTH'(MAX_OUTSTANDING - 1))
                            burst_write_pointer_q[pc] <= '0;
                        else
                            burst_write_pointer_q[pc] <= burst_write_pointer_q[pc] + 1'b1;
                    end

                    if (response_fire) begin
                        if (local_error) begin
                            lane_error_q[pc] <= 1'b1;
                        end else begin
                            received_beats_q[pc] <= received_beats_q[pc] + 1'b1;
                            if (m_axi_rlast[pc]) begin
                                response_beats_left_q[pc] <= '0;
                                if (burst_read_pointer_q[pc] == PTR_WIDTH'(MAX_OUTSTANDING - 1))
                                    burst_read_pointer_q[pc] <= '0;
                                else
                                    burst_read_pointer_q[pc] <= burst_read_pointer_q[pc] + 1'b1;
                            end else if (response_beats_left_q[pc] == 0) begin
                                response_beats_left_q[pc] <= response_length - 1'b1;
                            end else begin
                                response_beats_left_q[pc] <= response_beats_left_q[pc] - 1'b1;
                            end
                        end
                    end

                    case ({ar_fire, rlast_fire[pc]})
                        2'b10: outstanding_q[pc] <= outstanding_q[pc] + 1'b1;
                        2'b01: outstanding_q[pc] <= outstanding_q[pc] - 1'b1;
                        default: outstanding_q[pc] <= outstanding_q[pc];
                    endcase
                end
            end
        end
    endgenerate

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            busy_q <= 1'b0;
            load_done <= 1'b0;
            skip_adapter_q <= 1'b0;
            first_pc_q <= '0;
        end else begin
            load_done <= 1'b0;
            if (load_start && !busy_q) begin
                skip_adapter_q <= ADAPTER_STATIC_REUSE && load_skip_adapter_static;
                first_pc_q <= load_first_pc;
                busy_q <= !(|address_error);
                if (|address_error)
                    load_done <= 1'b1;
            end else if (busy_q && (&all_channels_done)) begin
                busy_q <= 1'b0;
                load_done <= 1'b1;
            end
            if (busy_q && (|response_error)) begin
                busy_q <= 1'b0;
                load_done <= 1'b1;
            end
        end
    end

    initial begin
        if (HBM_PCS < 1 || MAX_OUTSTANDING < 2 ||
            (2 ** PTR_WIDTH) != MAX_OUTSTANDING)
            $error("U280 HBM DMA requires a positive PC count and power-of-two outstanding depth");
    end
endmodule
