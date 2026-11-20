`timescale 1ns / 1ps

module rtwsr_weight_dma #(
    parameter int ADDR_WIDTH = 37
)(
    input  logic                    clk,
    input  logic                    rst_n,
    input  logic                    command_valid,
    output logic                    command_ready,
    input  logic [ADDR_WIDTH-1:0]   command_address,
    input  logic [31:0]             command_words,
    output logic                    m_axi_arvalid,
    input  logic                    m_axi_arready,
    output logic [4:0]              m_axi_arid,
    output logic [ADDR_WIDTH-1:0]   m_axi_araddr,
    output logic [7:0]              m_axi_arlen,
    output logic [2:0]              m_axi_arsize,
    output logic [1:0]              m_axi_arburst,
    input  logic                    m_axi_rvalid,
    output logic                    m_axi_rready,
    input  logic [4:0]              m_axi_rid,
    input  logic [511:0]            m_axi_rdata,
    input  logic [1:0]              m_axi_rresp,
    input  logic                    m_axi_rlast,
    output logic                    data_valid,
    input  logic                    data_ready,
    output logic [511:0]            data_word,
    output logic                    data_last,
    output logic                    busy,
    output logic                    done,
    output logic                    error
);
    logic busy_q;
    logic arvalid_q;
    logic [ADDR_WIDTH-1:0] next_address_q;
    logic [31:0] words_to_issue_q;
    logic [31:0] words_to_receive_q;
    logic [8:0] burst_words_q;
    logic [8:0] burst_beats_left_q;
    logic response_pending_q;
    logic [511:0] data_word_q;
    logic data_valid_q;
    logic data_last_q;
    logic error_q;
    logic [63:0] command_end_address;
    logic command_address_overflow;

    function automatic logic [8:0] burst_words(
        input logic [ADDR_WIDTH-1:0] address,
        input logic [31:0] words_left
    );
        integer page_words;
        logic [8:0] result;
        begin
            page_words = 64 - int'(address[11:6]);
            if (words_left < 32'd64)
                result = 9'(words_left);
            else
                result = 9'd64;
            if (result > 9'(page_words))
                result = 9'(page_words);
            return result;
        end
    endfunction

    assign command_ready = !busy_q;
    assign m_axi_arvalid = arvalid_q;
    assign m_axi_arid = '0;
    assign m_axi_arburst = 2'b01;
    assign m_axi_arsize = 3'd6;
    assign m_axi_rready = busy_q && response_pending_q &&
                          (!data_valid_q || data_ready);
    assign data_valid = data_valid_q;
    assign data_word = data_word_q;
    assign data_last = data_last_q;
    assign busy = busy_q;
    assign error = error_q;

    always_comb begin
        command_end_address = 64'(command_address) + (64'(command_words) << 6);
        command_address_overflow = command_end_address > (64'd1 << ADDR_WIDTH);
    end

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            busy_q <= 1'b0;
            arvalid_q <= 1'b0;
            m_axi_araddr <= '0;
            m_axi_arlen <= '0;
            next_address_q <= '0;
            words_to_issue_q <= '0;
            words_to_receive_q <= '0;
            burst_words_q <= '0;
            burst_beats_left_q <= '0;
            response_pending_q <= 1'b0;
            data_word_q <= '0;
            data_valid_q <= 1'b0;
            data_last_q <= 1'b0;
            done <= 1'b0;
            error_q <= 1'b0;
        end else begin
            done <= 1'b0;

            if (data_valid_q && data_ready) begin
                data_valid_q <= 1'b0;
                if (data_last_q) begin
                    busy_q <= 1'b0;
                    done <= 1'b1;
                end
            end

            if (command_valid && command_ready) begin
                error_q <= 1'b0;
                if (command_address[5:0] != '0 || command_words == 0 ||
                    command_address_overflow) begin
                    error_q <= 1'b1;
                    done <= 1'b1;
                end else begin
                    busy_q <= 1'b1;
                    next_address_q <= command_address;
                    words_to_issue_q <= command_words;
                    words_to_receive_q <= command_words;
                    burst_words_q <= burst_words(command_address, command_words);
                    m_axi_araddr <= command_address;
                    m_axi_arlen <= 8'(burst_words(command_address, command_words) - 1'b1);
                    arvalid_q <= 1'b1;
                end
            end

            if (arvalid_q && m_axi_arready) begin
                arvalid_q <= 1'b0;
                words_to_issue_q <= words_to_issue_q - {23'd0, burst_words_q};
                next_address_q <= next_address_q + (ADDR_WIDTH'(burst_words_q) << 6);
                burst_beats_left_q <= burst_words_q;
                response_pending_q <= 1'b1;
            end

            if (m_axi_rvalid && m_axi_rready) begin
                if (m_axi_rresp != 2'b00 || m_axi_rid != 5'd0 ||
                    m_axi_rlast != (burst_beats_left_q == 1)) begin
                    error_q <= 1'b1;
                    busy_q <= 1'b0;
                    arvalid_q <= 1'b0;
                    response_pending_q <= 1'b0;
                    data_valid_q <= 1'b0;
                    data_last_q <= 1'b0;
                    done <= 1'b1;
                end else begin
                    data_word_q <= m_axi_rdata;
                    data_valid_q <= 1'b1;
                    data_last_q <= (words_to_receive_q == 1);
                    words_to_receive_q <= words_to_receive_q - 1'b1;

                    if (burst_beats_left_q == 1) begin
                        response_pending_q <= 1'b0;
                        burst_beats_left_q <= '0;
                        if (words_to_issue_q != 0) begin
                            burst_words_q <= burst_words(next_address_q, words_to_issue_q);
                            m_axi_araddr <= next_address_q;
                            m_axi_arlen <= 8'(burst_words(next_address_q, words_to_issue_q) - 1'b1);
                            arvalid_q <= 1'b1;
                        end
                    end else begin
                        burst_beats_left_q <= burst_beats_left_q - 1'b1;
                    end
                end
            end
        end
    end
endmodule
