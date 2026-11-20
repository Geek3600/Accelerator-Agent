`timescale 1ps / 1ps

module rtwsr_u280_axil_bfm (
    input logic clk,
    input logic rst_n,
    output logic [11:0] awaddr,
    output logic [2:0] awprot,
    output logic awvalid,
    input logic awready,
    output logic [31:0] wdata,
    output logic [3:0] wstrb,
    output logic wvalid,
    input logic wready,
    input logic [1:0] bresp,
    input logic bvalid,
    output logic bready,
    output logic [11:0] araddr,
    output logic [2:0] arprot,
    output logic arvalid,
    input logic arready,
    input logic [31:0] rdata,
    input logic [1:0] rresp,
    input logic rvalid,
    output logic rready
);
    assign awprot = 3'b000;
    assign wstrb = 4'hf;
    assign bready = 1'b1;
    assign arprot = 3'b000;
    assign rready = 1'b1;

    initial begin
        awaddr = '0;
        awvalid = 1'b0;
        wdata = '0;
        wvalid = 1'b0;
        araddr = '0;
        arvalid = 1'b0;
    end

    task automatic write_reg(input logic [11:0] address, input logic [31:0] value);
        logic address_sent;
        logic data_sent;
        begin
            address_sent = 1'b0;
            data_sent = 1'b0;
            @(negedge clk);
            awaddr = address;
            awvalid = 1'b1;
            wdata = value;
            wvalid = 1'b1;
            while (!address_sent || !data_sent) begin
                @(posedge clk);
                if (awvalid && awready)
                    address_sent = 1'b1;
                if (wvalid && wready)
                    data_sent = 1'b1;
            end
            @(negedge clk);
            awvalid = 1'b0;
            wvalid = 1'b0;
            do @(posedge clk); while (!bvalid);
            if (bresp != 2'b00)
                $fatal(1, "AXI-Lite write response error at 0x%03x: %b", address, bresp);
        end
    endtask

    task automatic read_reg(input logic [11:0] address, output logic [31:0] value);
        begin
            @(negedge clk);
            araddr = address;
            arvalid = 1'b1;
            do @(posedge clk); while (!arready);
            @(negedge clk);
            arvalid = 1'b0;
            do @(posedge clk); while (!rvalid);
            value = rdata;
            if (rresp != 2'b00)
                $fatal(1, "AXI-Lite read response error at 0x%03x: %b", address, rresp);
        end
    endtask
endmodule

module rtwsr_u280_gamma_axi_bfm (
    input logic clk,
    input logic rst_n,
    input logic [36:0] araddr,
    input logic [4:0] arid,
    input logic [7:0] arlen,
    input logic [2:0] arsize,
    input logic [1:0] arburst,
    input logic arvalid,
    output logic arready,
    output logic [4:0] rid,
    output logic [511:0] rdata,
    output logic [1:0] rresp,
    output logic rlast,
    output logic rvalid,
    input logic rready,
    output logic [63:0] read_beats
);
    logic active_q;
    logic [8:0] beats_left_q;
    logic [4:0] response_id_q;

    assign arready = rst_n && !active_q;
    assign rid = response_id_q;
    assign rdata = 512'd0;
    assign rresp = 2'b00;
    assign rlast = beats_left_q == 1;
    assign rvalid = active_q;

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            active_q <= 1'b0;
            beats_left_q <= '0;
            response_id_q <= '0;
            read_beats <= 64'd0;
        end else if (arvalid && arready) begin
            active_q <= 1'b1;
            beats_left_q <= {1'b0, arlen} + 1'b1;
            response_id_q <= arid;
        end else if (rvalid && rready) begin
            read_beats <= read_beats + 1'b1;
            if (beats_left_q == 1) begin
                active_q <= 1'b0;
                beats_left_q <= '0;
            end else begin
                beats_left_q <= beats_left_q - 1'b1;
            end
        end
    end
endmodule
