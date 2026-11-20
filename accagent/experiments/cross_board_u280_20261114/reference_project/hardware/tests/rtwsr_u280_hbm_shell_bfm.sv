`timescale 1ns / 1ps

module rtwsr_u280_hbm_shell_bfm #(
    parameter int POLL_INTERVAL = 4096,
    parameter int TIMEOUT_CYCLES = 50_000_000
)(
    input  logic         core_clk,
    input  logic         core_rst_n,
    input  logic         start_test,
    output logic         test_done,
    output logic         test_error,
    output logic [63:0]  measured_cycles,
    output logic [31:0]  final_status,
    output logic [31:0]  nonzero_chunks,
    output logic [31:0]  output_digest,

    output logic [11:0]  s_axi_awaddr,
    output logic [2:0]   s_axi_awprot,
    output logic         s_axi_awvalid,
    input  logic         s_axi_awready,
    output logic [31:0]  s_axi_wdata,
    output logic [3:0]   s_axi_wstrb,
    output logic         s_axi_wvalid,
    input  logic         s_axi_wready,
    input  logic [1:0]   s_axi_bresp,
    input  logic         s_axi_bvalid,
    output logic         s_axi_bready,
    output logic [11:0]  s_axi_araddr,
    output logic [2:0]   s_axi_arprot,
    output logic         s_axi_arvalid,
    input  logic         s_axi_arready,
    input  logic [31:0]  s_axi_rdata,
    input  logic [1:0]   s_axi_rresp,
    input  logic         s_axi_rvalid,
    output logic         s_axi_rready,

    input  logic [36:0]  gamma_m_axi_araddr,
    input  logic [4:0]   gamma_m_axi_arid,
    input  logic [7:0]   gamma_m_axi_arlen,
    input  logic [2:0]   gamma_m_axi_arsize,
    input  logic [1:0]   gamma_m_axi_arburst,
    input  logic         gamma_m_axi_arvalid,
    output logic         gamma_m_axi_arready,
    output logic [4:0]   gamma_m_axi_rid,
    output logic [511:0] gamma_m_axi_rdata,
    output logic [1:0]   gamma_m_axi_rresp,
    output logic         gamma_m_axi_rlast,
    output logic         gamma_m_axi_rvalid,
    input  logic         gamma_m_axi_rready
);
    logic gamma_read_active_q;
    logic [8:0] gamma_beats_left_q;
    logic [4:0] gamma_response_id_q;

    assign s_axi_awprot = '0;
    assign s_axi_wstrb = 4'hf;
    assign s_axi_bready = 1'b1;
    assign s_axi_arprot = '0;
    assign s_axi_rready = 1'b1;

    assign gamma_m_axi_arready = core_rst_n && !gamma_read_active_q;
    assign gamma_m_axi_rid = gamma_response_id_q;
    assign gamma_m_axi_rdata = '0;
    assign gamma_m_axi_rresp = '0;
    assign gamma_m_axi_rlast = gamma_beats_left_q == 1;
    assign gamma_m_axi_rvalid = gamma_read_active_q;

    always_ff @(posedge core_clk) begin
        if (!core_rst_n) begin
            gamma_read_active_q <= 1'b0;
            gamma_beats_left_q <= '0;
            gamma_response_id_q <= '0;
        end else if (gamma_m_axi_arvalid && gamma_m_axi_arready) begin
            gamma_read_active_q <= 1'b1;
            gamma_beats_left_q <= {1'b0, gamma_m_axi_arlen} + 1'b1;
            gamma_response_id_q <= gamma_m_axi_arid;
        end else if (gamma_m_axi_rvalid && gamma_m_axi_rready) begin
            if (gamma_beats_left_q == 1) begin
                gamma_read_active_q <= 1'b0;
                gamma_beats_left_q <= '0;
            end else begin
                gamma_beats_left_q <= gamma_beats_left_q - 1'b1;
            end
        end
    end

    task automatic axi_write(input logic [11:0] address, input logic [31:0] value);
        logic address_sent;
        logic data_sent;
        begin
            address_sent = 1'b0;
            data_sent = 1'b0;
            @(negedge core_clk);
            s_axi_awaddr = address;
            s_axi_awvalid = 1'b1;
            s_axi_wdata = value;
            s_axi_wvalid = 1'b1;
            while (!address_sent || !data_sent) begin
                @(posedge core_clk);
                if (s_axi_awvalid && s_axi_awready)
                    address_sent = 1'b1;
                if (s_axi_wvalid && s_axi_wready)
                    data_sent = 1'b1;
            end
            @(negedge core_clk);
            s_axi_awvalid = 1'b0;
            s_axi_wvalid = 1'b0;
            do @(posedge core_clk); while (!s_axi_bvalid);
            if (s_axi_bresp != 2'b00)
                test_error = 1'b1;
        end
    endtask

    task automatic axi_read(input logic [11:0] address, output logic [31:0] value);
        begin
            @(negedge core_clk);
            s_axi_araddr = address;
            s_axi_arvalid = 1'b1;
            do @(posedge core_clk); while (!s_axi_arready);
            @(negedge core_clk);
            s_axi_arvalid = 1'b0;
            do @(posedge core_clk); while (!s_axi_rvalid);
            value = s_axi_rdata;
            if (s_axi_rresp != 2'b00)
                test_error = 1'b1;
        end
    endtask

    initial begin : run_full_core
        logic [31:0] status_value;
        logic [31:0] cycles_low;
        logic [31:0] cycles_high;
        integer elapsed_cycles;

        s_axi_awaddr = '0;
        s_axi_awvalid = 1'b0;
        s_axi_wdata = '0;
        s_axi_wvalid = 1'b0;
        s_axi_araddr = '0;
        s_axi_arvalid = 1'b0;
        test_done = 1'b0;
        test_error = 1'b0;
        measured_cycles = '0;
        final_status = '0;
        nonzero_chunks = '0;
        output_digest = '0;

        wait (core_rst_n);
        wait (start_test);
        axi_write(12'h018, 32'd512);
        axi_write(12'h000, 32'd1);

        elapsed_cycles = 0;
        status_value = '0;
        while (elapsed_cycles < TIMEOUT_CYCLES && !status_value[0] && !test_error) begin
            repeat (POLL_INTERVAL) @(posedge core_clk);
            elapsed_cycles = elapsed_cycles + POLL_INTERVAL;
            axi_read(12'h004, status_value);
            if (status_value[2])
                test_error = 1'b1;
        end

        final_status = status_value;
        if (!status_value[0])
            test_error = 1'b1;
        axi_read(12'h008, cycles_low);
        axi_read(12'h00c, cycles_high);
        axi_read(12'h010, nonzero_chunks);
        axi_read(12'h014, output_digest);
        measured_cycles = {cycles_high, cycles_low};
        test_done = 1'b1;
    end

    initial begin
        if (POLL_INTERVAL < 1 || TIMEOUT_CYCLES < POLL_INTERVAL)
            $error("Invalid U280 HBM shell BFM timing parameters");
    end
endmodule
