`timescale 1ns / 1ps

module tb_rtwsr_gamma_pingpong_buffer #(
    parameter int BANK_DEPTH = 65536,
    parameter int ADDR_WIDTH = $clog2(BANK_DEPTH),
    parameter int COUNT_WIDTH = $clog2(BANK_DEPTH + 1)
)(
);
    logic clk = 1'b0;
    logic rst_n = 1'b0;
    logic load_start = 1'b0;
    logic [COUNT_WIDTH-1:0] load_length = '0;
    logic load_valid = 1'b0;
    logic load_ready;
    logic [15:0] load_data = '0;
    logic load_last = 1'b0;
    logic load_done;
    logic protocol_error;
    logic read_enable = 1'b0;
    logic [ADDR_WIDTH-1:0] read_address = '0;
    logic read_valid;
    logic [15:0] read_data;
    logic active_valid;
    integer bank_id;
    integer address;
    integer load_count = 0;

    always #5 clk = ~clk;

    rtwsr_gamma_pingpong_buffer #(
        .BANK_DEPTH(BANK_DEPTH),
        .ADDR_WIDTH(ADDR_WIDTH),
        .COUNT_WIDTH(COUNT_WIDTH)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .load_start(load_start),
        .load_length(load_length),
        .load_valid(load_valid),
        .load_ready(load_ready),
        .load_data(load_data),
        .load_last(load_last),
        .load_done(load_done),
        .protocol_error(protocol_error),
        .read_enable(read_enable),
        .read_address(read_address),
        .read_valid(read_valid),
        .read_data(read_data),
        .active_valid(active_valid)
    );

    function automatic logic [15:0] gamma_value(input integer bank, input integer index);
        gamma_value = 16'((bank*7919 + index*37 + (index >> 4)) & 16'hffff);
    endfunction

    task automatic load_full_bank(input integer bank);
        begin
            @(negedge clk);
            load_length = COUNT_WIDTH'(BANK_DEPTH);
            load_start = 1'b1;
            @(posedge clk);
            @(negedge clk);
            load_start = 1'b0;
            load_valid = 1'b1;
            for (integer item = 0; item < BANK_DEPTH; item = item + 1) begin
                load_data = gamma_value(bank, item);
                load_last = (item == BANK_DEPTH-1);
                @(posedge clk);
                @(negedge clk);
            end
            load_valid = 1'b0;
            load_last = 1'b0;
            if (!load_done || !active_valid)
                $fatal(1, "Gamma bank %0d did not complete and become active", bank);
            load_count = load_count + BANK_DEPTH;
            if (protocol_error)
                $fatal(1, "Gamma bank %0d reported a load protocol error", bank);
        end
    endtask

    task automatic check_address(input integer index, input integer bank);
        begin
            @(negedge clk);
            read_address = ADDR_WIDTH'(index);
            read_enable = 1'b1;
            @(posedge clk);
            #1;
            if (!read_valid || read_data !== gamma_value(bank, index))
                $fatal(1, "Gamma bank %0d address %0d mismatch: valid=%b data=%h expected=%h",
                    bank, index, read_valid, read_data, gamma_value(bank, index));
            @(negedge clk);
            read_enable = 1'b0;
        end
    endtask

    initial begin
        repeat (4) @(negedge clk);
        rst_n = 1'b1;
        if (active_valid)
            $fatal(1, "Gamma buffer became valid before a completed load");

        load_full_bank(0);
        check_address(0, 0);
        check_address(BANK_DEPTH/2, 0);
        check_address(BANK_DEPTH-1, 0);

        load_full_bank(1);
        check_address(0, 1);
        check_address(BANK_DEPTH/2, 1);
        check_address(BANK_DEPTH-1, 1);

        if (load_count != 2*BANK_DEPTH)
            $fatal(1, "expected two full Gamma-bank loads");
        $display("PASS: two %0d-entry Gamma banks loaded and read at boundary addresses", BANK_DEPTH);
        $finish;
    end
endmodule
