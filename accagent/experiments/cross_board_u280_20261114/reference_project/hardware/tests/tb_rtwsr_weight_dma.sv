`timescale 1ns / 1ps

module tb_rtwsr_weight_dma;
    localparam int ADDR_WIDTH = 37;
    localparam int WORD_COUNT = 130;

    logic clk = 1'b0;
    logic rst_n = 1'b0;
    logic command_valid = 1'b0;
    logic command_ready;
    logic [ADDR_WIDTH-1:0] command_address = '0;
    logic [31:0] command_words = '0;
    logic m_axi_arvalid;
    logic m_axi_arready = 1'b0;
    logic [4:0] m_axi_arid;
    logic [ADDR_WIDTH-1:0] m_axi_araddr;
    logic [7:0] m_axi_arlen;
    logic [2:0] m_axi_arsize;
    logic [1:0] m_axi_arburst;
    logic m_axi_rvalid = 1'b0;
    logic m_axi_rready;
    logic [4:0] m_axi_rid = '0;
    logic [511:0] m_axi_rdata = '0;
    logic [1:0] m_axi_rresp = '0;
    logic m_axi_rlast = 1'b0;
    logic data_valid;
    logic data_ready = 1'b0;
    logic [511:0] data_word;
    logic data_last;
    logic busy;
    logic done;
    logic error;
    integer cycles = 0;
    integer output_words = 0;
    integer burst_count = 0;
    integer expected_burst_words [0:3];
    logic [ADDR_WIDTH-1:0] expected_burst_address [0:3];
    integer burst_words_now;
    integer source_word = 0;

    always #5 clk = ~clk;

    always @(posedge clk) begin
        cycles <= cycles + 1;
        if (data_valid && data_ready) begin
            if (data_word !== 512'(output_words))
                $fatal(1, "DMA data order mismatch at word %0d", output_words);
            if (data_last !== (output_words == WORD_COUNT-1))
                $fatal(1, "DMA last marker mismatch at word %0d", output_words);
            output_words <= output_words + 1;
        end
    end

    always @(negedge clk)
        data_ready = (cycles % 9 != 0) && (cycles % 13 != 0);

    rtwsr_weight_dma #(.ADDR_WIDTH(ADDR_WIDTH)) dut (
        .clk(clk),
        .rst_n(rst_n),
        .command_valid(command_valid),
        .command_ready(command_ready),
        .command_address(command_address),
        .command_words(command_words),
        .m_axi_arvalid(m_axi_arvalid),
        .m_axi_arready(m_axi_arready),
        .m_axi_arid(m_axi_arid),
        .m_axi_araddr(m_axi_araddr),
        .m_axi_arlen(m_axi_arlen),
        .m_axi_arsize(m_axi_arsize),
        .m_axi_arburst(m_axi_arburst),
        .m_axi_rvalid(m_axi_rvalid),
        .m_axi_rready(m_axi_rready),
        .m_axi_rid(m_axi_rid),
        .m_axi_rdata(m_axi_rdata),
        .m_axi_rresp(m_axi_rresp),
        .m_axi_rlast(m_axi_rlast),
        .data_valid(data_valid),
        .data_ready(data_ready),
        .data_word(data_word),
        .data_last(data_last),
        .busy(busy),
        .done(done),
        .error(error)
    );

    task automatic send_read_beat(input integer word_number, input logic last_beat);
        begin
            @(negedge clk);
            m_axi_rvalid = 1'b1;
            m_axi_rdata = 512'(word_number);
            m_axi_rlast = last_beat;
            do @(posedge clk); while (!m_axi_rready);
            @(negedge clk);
            m_axi_rvalid = 1'b0;
            m_axi_rlast = 1'b0;
        end
    endtask

    initial begin
        expected_burst_words[0] = 1;
        expected_burst_words[1] = 64;
        expected_burst_words[2] = 64;
        expected_burst_words[3] = 1;
        expected_burst_address[0] = 37'h0800000fc0;
        expected_burst_address[1] = 37'h0800001000;
        expected_burst_address[2] = 37'h0800002000;
        expected_burst_address[3] = 37'h0800003000;

        repeat (4) @(posedge clk);
        @(negedge clk);
        rst_n = 1'b1;
        command_address = 37'h0800000fc0;
        command_words = WORD_COUNT;
        command_valid = 1'b1;
        do @(posedge clk); while (!command_ready);
        @(negedge clk);
        command_valid = 1'b0;

        while (burst_count < 4) begin
            @(negedge clk);
            while (!m_axi_arvalid) @(negedge clk);
            if (m_axi_araddr !== expected_burst_address[burst_count])
                $fatal(1, "unexpected AR address in burst %0d", burst_count);
            if ((int'(m_axi_arlen) + 1) != expected_burst_words[burst_count])
                $fatal(1, "unexpected AR length in burst %0d", burst_count);
            if (m_axi_arsize != 3'd6 || m_axi_arburst != 2'b01)
                $fatal(1, "unexpected AXI beat size or burst type");
            burst_words_now = int'(m_axi_arlen) + 1;
            m_axi_arready = 1'b1;
            @(posedge clk);
            @(negedge clk);
            m_axi_arready = 1'b0;
            for (integer beat = 0; beat < burst_words_now; beat = beat + 1) begin
                send_read_beat(source_word, beat == burst_words_now-1);
                source_word = source_word + 1;
            end
            burst_count = burst_count + 1;
        end

        wait (done);
        @(posedge clk);
        #1;
        if (busy || error || output_words != WORD_COUNT)
            $fatal(1, "DMA completion state mismatch");
        $display("PASS: %0d AXI beats crossed 4KB boundaries in %0d bursts", output_words, burst_count);
        $display("PASS: stream backpressure and final-beat marker held correctly");

        @(negedge clk);
        rst_n = 1'b0;
        m_axi_arready = 1'b0;
        output_words = 0;
        repeat (3) @(posedge clk);
        @(negedge clk);
        rst_n = 1'b1;
        command_address = 37'h0800000000;
        command_words = 2;
        command_valid = 1'b1;
        do @(posedge clk); while (!command_ready);
        @(negedge clk);
        command_valid = 1'b0;
        while (!m_axi_arvalid) @(negedge clk);
        m_axi_arready = 1'b1;
        @(posedge clk);
        @(negedge clk);
        m_axi_arready = 1'b0;
        send_read_beat(0, 1'b1);
        wait (done);
        #1;
        if (busy || !error || data_valid)
            $fatal(1, "early RLAST did not abort the DMA with error");
        $display("PASS: early RLAST aborts without leaving the DMA busy");

        @(negedge clk);
        rst_n = 1'b0;
        m_axi_rvalid = 1'b0;
        output_words = 0;
        repeat (3) @(posedge clk);
        @(negedge clk);
        rst_n = 1'b1;
        command_address = 37'h1fffffffc0;
        command_words = 2;
        command_valid = 1'b1;
        do @(posedge clk); while (!command_ready);
        @(negedge clk);
        command_valid = 1'b0;
        wait (done);
        #1;
        if (busy || !error || m_axi_arvalid)
            $fatal(1, "address overflow was not rejected before issuing AXI reads");
        $display("PASS: address overflow is rejected before AXI traffic");

        @(negedge clk);
        rst_n = 1'b0;
        repeat (3) @(posedge clk);
        @(negedge clk);
        rst_n = 1'b1;
        command_address = 37'h0800000000;
        command_words = 2;
        command_valid = 1'b1;
        do @(posedge clk); while (!command_ready);
        @(negedge clk);
        command_valid = 1'b0;
        while (!m_axi_arvalid) @(negedge clk);
        m_axi_arready = 1'b1;
        @(posedge clk);
        @(negedge clk);
        m_axi_arready = 1'b0;
        send_read_beat(0, 1'b0);
        send_read_beat(1, 1'b0);
        wait (done);
        #1;
        if (busy || !error || data_valid)
            $fatal(1, "missing RLAST did not abort the DMA with error");
        $display("PASS: missing RLAST aborts without advancing to another burst");
        $finish;
    end
endmodule
