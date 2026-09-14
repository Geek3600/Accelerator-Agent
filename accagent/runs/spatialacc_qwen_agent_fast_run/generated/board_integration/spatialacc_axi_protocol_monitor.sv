module spatialacc_axi4_protocol_monitor #(
  parameter ADDR_WIDTH = 37,
  parameter DATA_WIDTH = 512,
  parameter ID_WIDTH = 4,
  parameter READ_OUTSTANDING_LIMIT = 2,
  parameter WRITE_OUTSTANDING_LIMIT = 2
)(
  input aclk,
  input aresetn,
  input calib_complete,
  input [ID_WIDTH-1:0] awid,
  input [ADDR_WIDTH-1:0] awaddr,
  input [7:0] awlen,
  input [2:0] awsize,
  input [1:0] awburst,
  input awlock,
  input [3:0] awcache,
  input [2:0] awprot,
  input awvalid,
  input awready,
  input [DATA_WIDTH-1:0] wdata,
  input [(DATA_WIDTH/8)-1:0] wstrb,
  input wlast,
  input wvalid,
  input wready,
  input [ID_WIDTH-1:0] bid,
  input [1:0] bresp,
  input bvalid,
  input bready,
  input [ID_WIDTH-1:0] arid,
  input [ADDR_WIDTH-1:0] araddr,
  input [7:0] arlen,
  input [2:0] arsize,
  input [1:0] arburst,
  input arlock,
  input [3:0] arcache,
  input [2:0] arprot,
  input arvalid,
  input arready,
  input [DATA_WIDTH-1:0] rdata,
  input [ID_WIDTH-1:0] rid,
  input [1:0] rresp,
  input rlast,
  input rvalid,
  input rready
);
  reg violation;
  reg aw_hold;
  reg [ID_WIDTH-1:0] awid_hold;
  reg [ADDR_WIDTH-1:0] awaddr_hold;
  reg [7:0] awlen_hold;
  reg [2:0] awsize_hold;
  reg [1:0] awburst_hold;
  reg awlock_hold;
  reg [3:0] awcache_hold;
  reg [2:0] awprot_hold;
  reg ar_hold;
  reg [ID_WIDTH-1:0] arid_hold;
  reg [ADDR_WIDTH-1:0] araddr_hold;
  reg [7:0] arlen_hold;
  reg [2:0] arsize_hold;
  reg [1:0] arburst_hold;
  reg arlock_hold;
  reg [3:0] arcache_hold;
  reg [2:0] arprot_hold;
  reg w_hold;
  reg [DATA_WIDTH-1:0] wdata_hold;
  reg [(DATA_WIDTH/8)-1:0] wstrb_hold;
  reg wlast_hold;
  reg [ID_WIDTH-1:0] expected_bid;
  reg expected_bid_valid;
  reg [ID_WIDTH-1:0] expected_rid;
  reg expected_rid_valid;
  integer read_outstanding;
  integer write_outstanding;
  integer expected_w_beats;
  integer seen_w_beats;
  integer expected_r_beats;
  integer seen_r_beats;
  integer aw_bytes;
  integer ar_bytes;

  always @(posedge aclk) begin
    if (!aresetn) begin
      violation <= 1'b0;
      aw_hold <= 1'b0;
      ar_hold <= 1'b0;
      w_hold <= 1'b0;
      expected_bid <= {ID_WIDTH{1'b0}};
      expected_bid_valid <= 1'b0;
      expected_rid <= {ID_WIDTH{1'b0}};
      expected_rid_valid <= 1'b0;
      read_outstanding <= 0;
      write_outstanding <= 0;
      expected_w_beats <= 0;
      seen_w_beats <= 0;
      expected_r_beats <= 0;
      seen_r_beats <= 0;
    end else begin
      if (!calib_complete && (awvalid || arvalid || wvalid)) begin
        violation <= 1'b1;
      end
      if (awvalid && !awready && !aw_hold) begin
        aw_hold <= 1'b1;
        awid_hold <= awid;
        awaddr_hold <= awaddr;
        awlen_hold <= awlen;
        awsize_hold <= awsize;
        awburst_hold <= awburst;
        awlock_hold <= awlock;
        awcache_hold <= awcache;
        awprot_hold <= awprot;
      end else if (awvalid && !awready && aw_hold) begin
        if ((awid_hold != awid) || (awaddr_hold != awaddr) ||
            (awlen_hold != awlen) || (awsize_hold != awsize) ||
            (awburst_hold != awburst) || (awlock_hold != awlock) ||
            (awcache_hold != awcache) || (awprot_hold != awprot)) begin
          violation <= 1'b1;
        end
      end
      if (awvalid && awready) begin
        aw_hold <= 1'b0;
        expected_bid <= awid;
        expected_bid_valid <= 1'b1;
        write_outstanding <= write_outstanding + 1;
        expected_w_beats <= awlen + 1;
        seen_w_beats <= 0;
        aw_bytes = (awlen + 1) << awsize;
        if (awburst != 2'b01) violation <= 1'b1;
        if (awsize > 3'b110) violation <= 1'b1;
        if ((awaddr[11:0] + aw_bytes) > 4096) violation <= 1'b1;
      end
      if (wvalid && !wready && !w_hold) begin
        w_hold <= 1'b1;
        wdata_hold <= wdata;
        wstrb_hold <= wstrb;
        wlast_hold <= wlast;
      end else if (wvalid && !wready && w_hold) begin
        if ((wdata_hold != wdata) || (wstrb_hold != wstrb) || (wlast_hold != wlast)) begin
          violation <= 1'b1;
        end
      end
      if (wvalid && wready) begin
        w_hold <= 1'b0;
        if (wlast != (seen_w_beats == (expected_w_beats - 1))) begin
          violation <= 1'b1;
        end
        seen_w_beats <= seen_w_beats + 1;
      end
      if (bvalid && bready) begin
        if (write_outstanding <= 0) violation <= 1'b1;
        else write_outstanding <= write_outstanding - 1;
        if (!expected_bid_valid || (bid != expected_bid)) violation <= 1'b1;
        expected_bid_valid <= 1'b0;
        if (bresp != 2'b00) violation <= 1'b1;
      end
      if (arvalid && !arready && !ar_hold) begin
        ar_hold <= 1'b1;
        arid_hold <= arid;
        araddr_hold <= araddr;
        arlen_hold <= arlen;
        arsize_hold <= arsize;
        arburst_hold <= arburst;
        arlock_hold <= arlock;
        arcache_hold <= arcache;
        arprot_hold <= arprot;
      end else if (arvalid && !arready && ar_hold) begin
        if ((arid_hold != arid) || (araddr_hold != araddr) ||
            (arlen_hold != arlen) || (arsize_hold != arsize) ||
            (arburst_hold != arburst) || (arlock_hold != arlock) ||
            (arcache_hold != arcache) || (arprot_hold != arprot)) begin
          violation <= 1'b1;
        end
      end
      if (arvalid && arready) begin
        ar_hold <= 1'b0;
        expected_rid <= arid;
        expected_rid_valid <= 1'b1;
        read_outstanding <= read_outstanding + 1;
        expected_r_beats <= arlen + 1;
        seen_r_beats <= 0;
        ar_bytes = (arlen + 1) << arsize;
        if (arburst != 2'b01) violation <= 1'b1;
        if (arsize > 3'b110) violation <= 1'b1;
        if ((araddr[11:0] + ar_bytes) > 4096) violation <= 1'b1;
      end
      if (rvalid && rready) begin
        if (!expected_rid_valid || (rid != expected_rid)) violation <= 1'b1;
        if (rresp != 2'b00) violation <= 1'b1;
        if (rlast != (seen_r_beats == (expected_r_beats - 1))) begin
          violation <= 1'b1;
        end
        if (rlast) begin
          if (read_outstanding <= 0) violation <= 1'b1;
          else read_outstanding <= read_outstanding - 1;
          expected_rid_valid <= 1'b0;
        end
        seen_r_beats <= seen_r_beats + 1;
      end
      if (read_outstanding > READ_OUTSTANDING_LIMIT) violation <= 1'b1;
      if (write_outstanding > WRITE_OUTSTANDING_LIMIT) violation <= 1'b1;
      if ((wvalid && wready) && (wstrb == {(DATA_WIDTH/8){1'b0}})) violation <= 1'b1;
      if ($isunknown({awid, awaddr, awlen, awsize, awburst, awlock, awcache, awprot,
                      awvalid, awready, wdata, wstrb, wlast, wvalid, wready,
                      bid, bresp, bvalid, bready, arid, araddr, arlen, arsize,
                      arburst, arlock, arcache, arprot, arvalid, arready, rdata,
                      rid, rresp, rlast, rvalid, rready})) begin
        violation <= 1'b1;
      end
      if (violation) begin
        $fatal(1, "SPATIALACC_AXI_PROTOCOL_VIOLATION");
      end
    end
  end
endmodule

