`timescale 1ns / 1ps

module rtwsr_plan6_huginn_9p_axi_bd (
    (* keep = "true" *) input wire         Q_replN_alias,
    (* keep = "true" *) input wire         lopt,
    (* keep = "true" *) input wire         \peripheral_aresetn[0]_repN_alias ,
    input  wire         s_axi_aclk,
    input  wire         s_axi_aresetn,
    input  wire [11:0]  s_axi_awaddr,
    input  wire [2:0]   s_axi_awprot,
    input  wire         s_axi_awvalid,
    output wire         s_axi_awready,
    input  wire [31:0]  s_axi_wdata,
    input  wire [3:0]   s_axi_wstrb,
    input  wire         s_axi_wvalid,
    output wire         s_axi_wready,
    output logic [1:0]  s_axi_bresp,
    output logic        s_axi_bvalid,
    input  wire         s_axi_bready,
    input  wire [11:0]  s_axi_araddr,
    input  wire [2:0]   s_axi_arprot,
    input  wire         s_axi_arvalid,
    output wire         s_axi_arready,
    output logic [31:0] s_axi_rdata,
    output logic [1:0]  s_axi_rresp,
    output logic        s_axi_rvalid,
    input  wire         s_axi_rready,
    output wire [36:0]  m_axi_araddr,
    output wire [4:0]   m_axi_arid,
    output wire [7:0]   m_axi_arlen,
    output wire [2:0]   m_axi_arsize,
    output wire [1:0]   m_axi_arburst,
    output wire         m_axi_arlock,
    output wire [3:0]   m_axi_arcache,
    output wire [2:0]   m_axi_arprot,
    output wire [3:0]   m_axi_arqos,
    output wire         m_axi_arvalid,
    input  wire         m_axi_arready,
    input  wire [511:0] m_axi_rdata,
    input  wire [4:0]   m_axi_rid,
    input  wire [1:0]   m_axi_rresp,
    input  wire         m_axi_rlast,
    input  wire         m_axi_rvalid,
    output wire         m_axi_rready
);
    localparam logic [31:0] MAGIC = 32'h4c515052;
    localparam logic [31:0] STATUS = 32'ha11e0001;

    logic aw_pending_q, w_pending_q;
    logic [11:0] awaddr_q;
    logic [31:0] wdata_q;
    logic [3:0] wstrb_q;
    logic [7:0] scratch_q;
    logic [31:0] counter_q;
    logic [31:0] write_data;
    logic [11:0] write_addr;
    logic [3:0] write_strb;
    logic aw_fire, w_fire, write_commit;

    assign s_axi_awready = !aw_pending_q && !s_axi_bvalid;
    assign s_axi_wready = !w_pending_q && !s_axi_bvalid;
    assign s_axi_arready = !s_axi_rvalid;

    assign aw_fire = s_axi_awvalid && s_axi_awready;
    assign w_fire = s_axi_wvalid && s_axi_wready;
    assign write_commit = !s_axi_bvalid &&
        (aw_pending_q || aw_fire) && (w_pending_q || w_fire);
    assign write_addr = aw_pending_q ? awaddr_q : s_axi_awaddr;
    assign write_data = w_pending_q ? wdata_q : s_axi_wdata;
    assign write_strb = w_pending_q ? wstrb_q : s_axi_wstrb;

    assign m_axi_araddr = '0;
    assign m_axi_arid = '0;
    assign m_axi_arlen = '0;
    assign m_axi_arsize = 3'd6;
    assign m_axi_arburst = 2'b01;
    assign m_axi_arlock = 1'b0;
    assign m_axi_arcache = 4'b0011;
    assign m_axi_arprot = '0;
    assign m_axi_arqos = '0;
    assign m_axi_arvalid = 1'b0;
    assign m_axi_rready = 1'b1;

    always_ff @(posedge s_axi_aclk) begin
        if (!s_axi_aresetn) begin
            aw_pending_q <= 1'b0;
            w_pending_q <= 1'b0;
            awaddr_q <= '0;
            wdata_q <= '0;
            wstrb_q <= '0;
            scratch_q <= '0;
            counter_q <= '0;
            s_axi_bresp <= 2'b00;
            s_axi_bvalid <= 1'b0;
            s_axi_rdata <= '0;
            s_axi_rresp <= 2'b00;
            s_axi_rvalid <= 1'b0;
        end else begin
            counter_q <= counter_q + 1'b1;

            if (s_axi_bvalid && s_axi_bready)
                s_axi_bvalid <= 1'b0;
            if (aw_fire) begin
                aw_pending_q <= 1'b1;
                awaddr_q <= s_axi_awaddr;
            end
            if (w_fire) begin
                w_pending_q <= 1'b1;
                wdata_q <= s_axi_wdata;
                wstrb_q <= s_axi_wstrb;
            end
            if (write_commit) begin
                if (write_addr[11:2] == 10'h002) begin
                    if (write_strb[0])
                        scratch_q <= write_data[7:0];
                end
                aw_pending_q <= 1'b0;
                w_pending_q <= 1'b0;
                s_axi_bresp <= 2'b00;
                s_axi_bvalid <= 1'b1;
            end

            if (s_axi_rvalid && s_axi_rready)
                s_axi_rvalid <= 1'b0;
            if (s_axi_arvalid && s_axi_arready) begin
                case (s_axi_araddr[11:2])
                    10'h000: s_axi_rdata <= MAGIC;
                    10'h001: s_axi_rdata <= STATUS;
                    10'h002: s_axi_rdata <= {24'b0, scratch_q};
                    10'h003: s_axi_rdata <= counter_q;
                    default: s_axi_rdata <= 32'hbad0add0;
                endcase
                s_axi_rresp <= 2'b00;
                s_axi_rvalid <= 1'b1;
            end
        end
    end
endmodule
