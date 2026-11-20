`timescale 1ps / 1ps

module rtwsr_u280_hbm_axi_cycle_model #(
    parameter int HBM_PCS = 32,
    parameter int MAX_OUTSTANDING = 16,
    parameter int READ_LATENCY = 77,
    parameter int PTR_WIDTH = $clog2(MAX_OUTSTANDING),
    parameter int COUNT_WIDTH = $clog2(MAX_OUTSTANDING + 1)
)(
    input  logic                         hbm_clk,
    input  logic                         hbm_rst_n,
    input  logic [HBM_PCS*33-1:0]        araddr,
    input  logic [HBM_PCS*6-1:0]         arid,
    input  logic [HBM_PCS*4-1:0]         arlen,
    input  logic [HBM_PCS*3-1:0]         arsize,
    input  logic [HBM_PCS*2-1:0]         arburst,
    input  logic [HBM_PCS-1:0]           arvalid,
    output logic [HBM_PCS-1:0]           arready,
    output logic [HBM_PCS*6-1:0]         rid,
    output logic [HBM_PCS*256-1:0]       rdata,
    output logic [HBM_PCS*2-1:0]         rresp,
    output logic [HBM_PCS-1:0]           rlast,
    output logic [HBM_PCS-1:0]           rvalid,
    input  logic [HBM_PCS-1:0]           rready,
    output logic [HBM_PCS-1:0]           protocol_error
);
    genvar pc;
    generate
        for (pc = 0; pc < HBM_PCS; pc = pc + 1) begin : gen_pc
            logic [63:0] cycle_q;
            logic [63:0] ready_cycle_q [0:MAX_OUTSTANDING-1];
            logic [4:0] queued_beats_q [0:MAX_OUTSTANDING-1];
            logic [5:0] queued_id_q [0:MAX_OUTSTANDING-1];
            logic [PTR_WIDTH-1:0] write_ptr_q;
            logic [PTR_WIDTH-1:0] read_ptr_q;
            logic [COUNT_WIDTH-1:0] queue_count_q;
            logic [4:0] response_beats_q;
            logic [5:0] response_id_q;
            logic response_active_q;
            logic address_fire;
            logic response_fire;
            logic response_last_fire;
            logic [PTR_WIDTH-1:0] next_read_ptr;

            assign address_fire = arvalid[pc] && arready[pc];
            assign response_fire = rvalid[pc] && rready[pc];
            assign response_last_fire = response_fire && rlast[pc];
            assign next_read_ptr = read_ptr_q == PTR_WIDTH'(MAX_OUTSTANDING - 1) ?
                '0 : read_ptr_q + 1'b1;

            assign arready[pc] = hbm_rst_n &&
                (queue_count_q < COUNT_WIDTH'(MAX_OUTSTANDING));
            assign rid[pc*6 +: 6] = response_id_q;
            assign rdata[pc*256 +: 256] = '0;
            assign rresp[pc*2 +: 2] = 2'b00;
            assign rlast[pc] = response_active_q && (response_beats_q == 1);
            assign rvalid[pc] = response_active_q;

            always_ff @(posedge hbm_clk) begin
                if (!hbm_rst_n) begin
                    cycle_q <= '0;
                    write_ptr_q <= '0;
                    read_ptr_q <= '0;
                    queue_count_q <= '0;
                    response_beats_q <= '0;
                    response_id_q <= '0;
                    response_active_q <= 1'b0;
                    protocol_error[pc] <= 1'b0;
                    for (integer slot = 0; slot < MAX_OUTSTANDING; slot = slot + 1) begin
                        ready_cycle_q[slot] <= '0;
                        queued_beats_q[slot] <= '0;
                        queued_id_q[slot] <= '0;
                    end
                end else begin
                    cycle_q <= cycle_q + 1'b1;

                    if (address_fire) begin
                        if (arsize[pc*3 +: 3] != 3'd5 ||
                            arburst[pc*2 +: 2] != 2'b01 ||
                            araddr[pc*33 +: 5] != 0)
                            protocol_error[pc] <= 1'b1;
                        ready_cycle_q[write_ptr_q] <= cycle_q + 64'(READ_LATENCY);
                        queued_beats_q[write_ptr_q] <=
                            {1'b0, arlen[pc*4 +: 4]} + 1'b1;
                        queued_id_q[write_ptr_q] <= arid[pc*6 +: 6];
                        if (write_ptr_q == PTR_WIDTH'(MAX_OUTSTANDING - 1))
                            write_ptr_q <= '0;
                        else
                            write_ptr_q <= write_ptr_q + 1'b1;
                    end

                    if (!response_active_q && queue_count_q != 0 &&
                        cycle_q >= ready_cycle_q[read_ptr_q]) begin
                        response_active_q <= 1'b1;
                        response_beats_q <= queued_beats_q[read_ptr_q];
                        response_id_q <= queued_id_q[read_ptr_q];
                    end

                    if (response_fire) begin
                        if (response_beats_q == 1) begin
                            if (queue_count_q > 1 &&
                                cycle_q >= ready_cycle_q[next_read_ptr]) begin
                                read_ptr_q <= next_read_ptr;
                                response_beats_q <= queued_beats_q[next_read_ptr];
                                response_id_q <= queued_id_q[next_read_ptr];
                                response_active_q <= 1'b1;
                            end else begin
                                response_active_q <= 1'b0;
                                response_beats_q <= '0;
                                read_ptr_q <= next_read_ptr;
                            end
                        end else begin
                            response_beats_q <= response_beats_q - 1'b1;
                        end
                    end

                    case ({address_fire, response_last_fire})
                        2'b10: queue_count_q <= queue_count_q + 1'b1;
                        2'b01: queue_count_q <= queue_count_q - 1'b1;
                        default: queue_count_q <= queue_count_q;
                    endcase
                end
            end
        end
    endgenerate

    initial begin
        if (HBM_PCS < 1 || MAX_OUTSTANDING < 2 ||
            (2 ** PTR_WIDTH) != MAX_OUTSTANDING || READ_LATENCY < 1)
            $error("Invalid U280 HBM AXI cycle-model configuration");
    end
endmodule
