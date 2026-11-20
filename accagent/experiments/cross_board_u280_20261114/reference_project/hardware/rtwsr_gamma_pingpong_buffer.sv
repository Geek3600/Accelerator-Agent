`timescale 1ns / 1ps

module rtwsr_gamma_pingpong_buffer #(
    parameter int BANK_DEPTH = 65536,
    parameter int ADDR_WIDTH = $clog2(BANK_DEPTH),
    parameter int COUNT_WIDTH = $clog2(BANK_DEPTH + 1)
)(
    input  logic                    clk,
    input  logic                    rst_n,
    input  logic                    load_start,
    input  logic [COUNT_WIDTH-1:0]  load_length,
    input  logic                    load_valid,
    output logic                    load_ready,
    input  logic [15:0]             load_data,
    input  logic                    load_last,
    output logic                    load_done,
    output logic                    protocol_error,
    input  logic                    read_enable,
    input  logic [ADDR_WIDTH-1:0]   read_address,
    output logic                    read_valid,
    output logic [15:0]             read_data,
    output logic                    active_valid
);
    (* ram_style = "block" *) logic [15:0] gamma_bank_0 [0:BANK_DEPTH-1];
    (* ram_style = "block" *) logic [15:0] gamma_bank_1 [0:BANK_DEPTH-1];

    logic active_bank_q;
    logic load_bank_q;
    logic load_busy_q;
    logic [COUNT_WIDTH-1:0] load_count_q;
    logic [COUNT_WIDTH-1:0] load_length_q;
    logic last_error_q;
    logic load_fire;
    logic read_address_valid;

    assign load_ready = load_busy_q;
    assign load_fire = load_busy_q && load_valid;
    assign read_address_valid = int'(read_address) < BANK_DEPTH;
    assign protocol_error = last_error_q;

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            active_bank_q <= 1'b0;
            load_bank_q <= 1'b1;
            load_busy_q <= 1'b0;
            load_count_q <= '0;
            load_length_q <= '0;
            read_valid <= 1'b0;
            read_data <= '0;
            load_done <= 1'b0;
            active_valid <= 1'b0;
            last_error_q <= 1'b0;
        end else begin
            read_valid <= read_enable && read_address_valid && active_valid;
            load_done <= 1'b0;

            if (read_enable && read_address_valid && active_valid) begin
                if (active_bank_q)
                    read_data <= gamma_bank_1[read_address];
                else
                    read_data <= gamma_bank_0[read_address];
            end

            if (load_start && !load_busy_q) begin
                if (load_length == 0 || int'(load_length) > BANK_DEPTH) begin
                    last_error_q <= 1'b1;
                end else begin
                    load_bank_q <= ~active_bank_q;
                    load_count_q <= '0;
                    load_length_q <= load_length;
                    load_busy_q <= 1'b1;
                    last_error_q <= 1'b0;
                end
            end

            if (load_fire) begin
                if (load_bank_q)
                    gamma_bank_1[load_count_q[ADDR_WIDTH-1:0]] <= load_data;
                else
                    gamma_bank_0[load_count_q[ADDR_WIDTH-1:0]] <= load_data;

                if (load_last && load_count_q != load_length_q - 1'b1) begin
                    last_error_q <= 1'b1;
                    load_busy_q <= 1'b0;
                end else if (load_count_q == load_length_q - 1'b1) begin
                    load_busy_q <= 1'b0;
                    if (load_last) begin
                        active_bank_q <= load_bank_q;
                        active_valid <= 1'b1;
                        load_done <= 1'b1;
                    end else begin
                        last_error_q <= 1'b1;
                    end
                end else begin
                    load_count_q <= load_count_q + 1'b1;
                end
            end
        end
    end

    initial begin
        if (BANK_DEPTH < 2 || (2 ** ADDR_WIDTH) < BANK_DEPTH)
            $error("Gamma bank address width cannot cover BANK_DEPTH");
    end
endmodule
