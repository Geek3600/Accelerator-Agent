`timescale 1ns / 1ps

module scale_hoisted_ternary_lane #(
    parameter int VEC_LEN = 64,
    parameter int ACT_W = 8,
    parameter int ACC_W = 24
)(
    input  logic                          clk,
    input  logic                          rst_n,
    input  logic                          valid_in,
    input  logic                          first_chunk,
    input  logic [VEC_LEN*ACT_W-1:0]      act_vec,
    input  logic [VEC_LEN-1:0]            trit_nz,
    input  logic [VEC_LEN-1:0]            trit_sgn,
    output logic                          valid_out,
    output logic signed [ACC_W-1:0]       dense_acc_out
);
    localparam int TERM_W = ACT_W + 1;
    localparam int GROUPS = VEC_LEN / 8;
    localparam int GROUP_W = ACT_W + 4;
    localparam int SUM_W = ACT_W + 1 + $clog2(VEC_LEN);

    logic signed [TERM_W-1:0] term_comb [VEC_LEN];
    logic signed [TERM_W-1:0] term_stage1 [0:VEC_LEN-1];
    logic signed [TERM_W:0] pair_sum [0:VEC_LEN/2-1];
    logic signed [TERM_W+1:0] quad_sum [0:VEC_LEN/4-1];
    logic signed [GROUP_W-1:0] group_sum_comb [0:GROUPS-1];
    logic signed [GROUP_W-1:0] group_stage2 [0:GROUPS-1];
    logic signed [SUM_W-1:0] total_pair [0:GROUPS/2-1];
    logic signed [SUM_W-1:0] total_quad [0:GROUPS/4-1];
    logic valid_stage1;
    logic valid_stage2;
    logic first_stage1;
    logic first_stage2;
    logic signed [SUM_W-1:0] total_sum;

    initial begin
        if ((VEC_LEN != 64 && VEC_LEN != 128) || ACT_W != 8 || VEC_LEN % 8 != 0)
            $error("scale_hoisted_ternary_lane supports VEC_LEN=64 or 128 and ACT_W=8");
    end

    genvar lane;
    generate
        for (lane = 0; lane < VEC_LEN; lane = lane + 1) begin : gen_term
`ifdef SIM_SCHEDULING_FAST_DATAPATH
            always_comb term_comb[lane] = '0;
`else
            wire activation_sign = act_vec[lane*ACT_W + ACT_W-1];
            wire negate = trit_nz[lane] & trit_sgn[lane];
            wire [7:0] operand = trit_nz[lane]
                ? (act_vec[lane*ACT_W +: ACT_W] ^ {ACT_W{negate}}) : 8'b0;
            wire [7:0] carry_sum;
            wire carry_to_sign;
            wire signed [8:0] term_value;

`ifdef SYNTH_CARRY8
            wire [7:0] carry_out;
            CARRY8 #(.CARRY_TYPE("SINGLE_CY8")) u_carry8 (
                .CI(negate),
                .CI_TOP(1'b0),
                .DI(8'b0),
                .S(operand),
                .CO(carry_out),
                .O(carry_sum)
            );
            assign carry_to_sign = carry_out[7];
`else
            wire [8:0] carry_result = {1'b0, operand} + {{8{1'b0}}, negate};
            assign carry_sum = carry_result[7:0];
            assign carry_to_sign = carry_result[8];
`endif

            assign term_value = {
                trit_nz[lane] & (activation_sign ^ negate ^ carry_to_sign),
                carry_sum
            };
            always_comb term_comb[lane] = term_value;
`endif
        end
    endgenerate

    always_comb begin
        for (integer pair_index = 0; pair_index < VEC_LEN/2; pair_index = pair_index + 1)
            pair_sum[pair_index] =
                {term_stage1[pair_index*2][TERM_W-1], term_stage1[pair_index*2]} +
                {term_stage1[pair_index*2+1][TERM_W-1], term_stage1[pair_index*2+1]};

        for (integer quad_index = 0; quad_index < VEC_LEN/4; quad_index = quad_index + 1)
            quad_sum[quad_index] =
                {pair_sum[quad_index*2][TERM_W], pair_sum[quad_index*2]} +
                {pair_sum[quad_index*2+1][TERM_W], pair_sum[quad_index*2+1]};

        for (integer group_index = 0; group_index < GROUPS; group_index = group_index + 1)
            group_sum_comb[group_index] =
                {{(GROUP_W-(TERM_W+2)){quad_sum[group_index*2][TERM_W+1]}}, quad_sum[group_index*2]} +
                {{(GROUP_W-(TERM_W+2)){quad_sum[group_index*2+1][TERM_W+1]}}, quad_sum[group_index*2+1]};
    end

    genvar term_index;
    generate
        for (term_index = 0; term_index < VEC_LEN; term_index = term_index + 1) begin : gen_term_register
            always_ff @(posedge clk) begin
                if (!rst_n)
                    term_stage1[term_index] <= '0;
                else if (valid_in)
                    term_stage1[term_index] <= term_comb[term_index];
            end
        end
    endgenerate

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            valid_stage1 <= 1'b0;
            first_stage1 <= 1'b0;
        end else begin
            valid_stage1 <= valid_in;
            first_stage1 <= first_chunk;
        end
    end

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            valid_stage2 <= 1'b0;
            first_stage2 <= 1'b0;
            for (integer group_index = 0; group_index < GROUPS; group_index = group_index + 1)
                group_stage2[group_index] <= '0;
        end else begin
            valid_stage2 <= valid_stage1;
            first_stage2 <= first_stage1;
            if (valid_stage1) begin
                for (integer group_index = 0; group_index < GROUPS; group_index = group_index + 1)
                    group_stage2[group_index] <= group_sum_comb[group_index];
            end
        end
    end

    logic signed [ACC_W-1:0] total_sum_extended;

    always_comb begin
        for (integer pair_index = 0; pair_index < GROUPS/2; pair_index = pair_index + 1)
            total_pair[pair_index] =
                {{(SUM_W-GROUP_W){group_stage2[pair_index*2][GROUP_W-1]}}, group_stage2[pair_index*2]} +
                {{(SUM_W-GROUP_W){group_stage2[pair_index*2+1][GROUP_W-1]}}, group_stage2[pair_index*2+1]};
        for (integer quad_index = 0; quad_index < GROUPS/4; quad_index = quad_index + 1)
            total_quad[quad_index] = total_pair[quad_index*2] + total_pair[quad_index*2+1];
        total_sum_extended =
            {{(ACC_W-SUM_W){total_sum[SUM_W-1]}}, total_sum};
    end

    generate
        if (VEC_LEN == 64) begin : gen_reduce_64
            always_comb total_sum = total_quad[0] + total_quad[1];
        end else begin : gen_reduce_128
            logic signed [SUM_W-1:0] total_octa [0:1];
            always_comb begin
                total_octa[0] = total_quad[0] + total_quad[1];
                total_octa[1] = total_quad[2] + total_quad[3];
                total_sum = total_octa[0] + total_octa[1];
            end
        end
    endgenerate

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            valid_out <= 1'b0;
            dense_acc_out <= '0;
        end else begin
            valid_out <= valid_stage2;
            if (valid_stage2) begin
                if (first_stage2)
                    dense_acc_out <= total_sum_extended;
                else
                    dense_acc_out <= dense_acc_out + total_sum_extended;
            end
        end
    end
endmodule
