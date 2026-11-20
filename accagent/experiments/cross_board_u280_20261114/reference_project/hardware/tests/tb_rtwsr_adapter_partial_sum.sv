`timescale 1ns / 1ps

module tb_rtwsr_adapter_partial_sum;
    localparam int HIDDEN_SIZE = 5280;
    localparam int CHUNKS = 165;
    logic clk = 0, rst_n = 0;
    logic valid_in = 0, first_subchunk = 0, last_subchunk = 0;
    logic [63:0] subchunk_nz, subchunk_sgn;
    logic signed [15:0] outlier_val_q4_12;
    logic [511:0] full_vector, state_vector, embedding_vector;
    logic signed [7:0] full_sparse, state_sparse, embedding_sparse;
    logic [15:0] gamma = 16'h3c00;
    logic signed [31:0] scale = 32'sh01000000;
    logic signed [36:0] saved_embedding_sum;
    logic full_done, state_done, embedding_done;
    logic signed [31:0] full_result, state_result, embedding_result;
    logic signed [36:0] full_sum, state_sum, embedding_sum;

    always #5 clk = ~clk;

    usw512_dual_track_channel u_full (
        .clk(clk), .rst_n(rst_n), .valid_in(valid_in), .first_subchunk(first_subchunk),
        .last_subchunk(last_subchunk), .subchunk_nz(subchunk_nz), .subchunk_sgn(subchunk_sgn),
        .outlier_val0_q4_12(outlier_val_q4_12), .outlier_val1_q4_12(16'sd0),
        .act_subvec(full_vector), .act_window_lookup0(full_sparse), .act_window_lookup1(8'sd0),
        .fused_gamma_fp16(gamma), .activation_scale_q8_24(scale),
        .static_sum_enable(1'b0), .static_sum_q12(37'sd0), .row_done_valid(full_done),
        .final_channel_out_q12(full_result), .unscaled_sum_q12(full_sum)
    );
    usw512_dual_track_channel #(.STATIC_REUSE(1'b1)) u_state (
        .clk(clk), .rst_n(rst_n), .valid_in(valid_in), .first_subchunk(first_subchunk),
        .last_subchunk(last_subchunk), .subchunk_nz(subchunk_nz), .subchunk_sgn(subchunk_sgn),
        .outlier_val0_q4_12(outlier_val_q4_12), .outlier_val1_q4_12(16'sd0),
        .act_subvec(state_vector), .act_window_lookup0(state_sparse), .act_window_lookup1(8'sd0),
        .fused_gamma_fp16(gamma), .activation_scale_q8_24(scale),
        .static_sum_enable(1'b1), .static_sum_q12(saved_embedding_sum), .row_done_valid(state_done),
        .final_channel_out_q12(state_result), .unscaled_sum_q12(state_sum)
    );
    usw512_dual_track_channel u_embedding (
        .clk(clk), .rst_n(rst_n), .valid_in(valid_in), .first_subchunk(first_subchunk),
        .last_subchunk(last_subchunk), .subchunk_nz(subchunk_nz), .subchunk_sgn(subchunk_sgn),
        .outlier_val0_q4_12(outlier_val_q4_12), .outlier_val1_q4_12(16'sd0),
        .act_subvec(embedding_vector), .act_window_lookup0(embedding_sparse), .act_window_lookup1(8'sd0),
        .fused_gamma_fp16(gamma), .activation_scale_q8_24(scale),
        .static_sum_enable(1'b0), .static_sum_q12(37'sd0), .row_done_valid(embedding_done),
        .final_channel_out_q12(embedding_result), .unscaled_sum_q12(embedding_sum)
    );

    task automatic send_vector(input integer round);
        integer column;
        integer value;
        for (integer chunk = 0; chunk < CHUNKS; chunk++) begin
            @(negedge clk);
            valid_in = 1;
            first_subchunk = chunk == 0;
            last_subchunk = chunk == CHUNKS - 1;
            outlier_val_q4_12 = 16'((chunk % 7 - 3) * 913);
            for (integer lane = 0; lane < 64; lane++) begin
                column = chunk*64 + lane;
                value = ((column*17 + (column < HIDDEN_SIZE ? round*13 : 5)) % 127) - 63;
                full_vector[lane*8 +: 8] = 8'(value);
                state_vector[lane*8 +: 8] = column < HIDDEN_SIZE ? 8'(value) : 8'd0;
                embedding_vector[lane*8 +: 8] = column >= HIDDEN_SIZE ? 8'(value) : 8'd0;
                subchunk_nz[lane] = (column % 5 != 0);
                subchunk_sgn[lane] = (column % 3 == 0);
            end
            full_sparse = $signed(full_vector[7:0]);
            state_sparse = $signed(state_vector[7:0]);
            embedding_sparse = $signed(embedding_vector[7:0]);
        end
        @(negedge clk);
        valid_in = 0;
        first_subchunk = 0;
        last_subchunk = 0;
        wait (full_done && state_done && embedding_done);
        @(negedge clk);
    endtask

    initial begin
        saved_embedding_sum = '0;
        repeat (3) @(negedge clk);
        rst_n = 1;
        send_vector(0);
        saved_embedding_sum = embedding_sum;
        for (integer round = 0; round < 32; round++) begin
            scale = round[0] ? 32'sh00800000 : 32'sh01000000;
            gamma = round[1] ? 16'h3800 : 16'h3c00;
            send_vector(round);
            if (full_result !== state_result || full_sum !== state_sum + saved_embedding_sum ||
                embedding_sum !== saved_embedding_sum)
                $fatal(1, "Adapter partial mismatch round=%0d full=%0d cached=%0d sums=%0d/%0d/%0d",
                       round, full_result, state_result, full_sum, state_sum, saved_embedding_sum);
        end
        $display("PASS Adapter dense+sparse unscaled split columns=10560 boundary=5280 rounds=32");
        $finish;
    end
endmodule
