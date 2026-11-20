`timescale 1ns / 1ps

module rtwsr_huginn_u280_hbm_descriptor #(
    parameter int HBM_PCS = 32,
    parameter int POOL_LANES = 24
)(
    input  logic [4:0]                 command_id,
    input  logic [5:0]                 block_index,
    output logic                       valid,
    output logic [15:0]                matrix_rows,
    output logic [15:0]                matrix_columns,
    output logic [4:0]                 first_pc,
    output logic [HBM_PCS*33-1:0]      pc_base_address,
    output logic [HBM_PCS*32-1:0]      pc_record_count
);
    localparam int QKV_GROUPS = 13860;
    localparam int O_PROJ_GROUPS = 4620;
    localparam int GATE_GROUPS = 15708;
    localparam int UP_GROUPS = 15708;
    localparam int DOWN_GROUPS = 15400;
    localparam int GROUPS_PER_BLOCK =
        QKV_GROUPS + O_PROJ_GROUPS + GATE_GROUPS + UP_GROUPS + DOWN_GROUPS;
    localparam int CORE_BLOCKS = 4;

    integer logical_start;
    integer logical_records;
    integer op_groups;
    integer op_rows;
    integer op_columns;
    integer logical_end;
    integer first_record;
    integer local_pc_record;
    integer pc_records;

    always_comb begin
        valid = 1'b0;
        matrix_rows = '0;
        matrix_columns = '0;
        op_groups = 0;
        op_rows = 0;
        op_columns = 0;
        logical_start = 0;
        logical_records = 0;
        logical_end = 0;
        first_record = 0;
        local_pc_record = 0;
        pc_records = 0;
        first_pc = '0;
        pc_base_address = '0;
        pc_record_count = '0;

        if (command_id == 5'd0) begin
            valid = 1'b1;
            op_rows = 5280;
            op_columns = 10560;
            op_groups = 9240;
            logical_start = CORE_BLOCKS * GROUPS_PER_BLOCK * 24;
        end else if (block_index < 6'd4) begin
            logical_start = int'(block_index) * GROUPS_PER_BLOCK * 24;
            case (command_id)
                5'd3: begin
                    valid = 1'b1;
                    op_rows = 15840;
                    op_columns = 5280;
                end
                5'd9: begin
                    valid = 1'b1;
                    op_rows = 5280;
                    op_columns = 5280;
                    logical_start = logical_start + QKV_GROUPS * 24;
                    op_groups = O_PROJ_GROUPS;
                end
                5'd21: begin
                    valid = 1'b1;
                    op_rows = 17920;
                    op_columns = 5280;
                    logical_start = logical_start +
                        (QKV_GROUPS + O_PROJ_GROUPS) * 24;
                    op_groups = GATE_GROUPS;
                end
                5'd22: begin
                    valid = 1'b1;
                    op_rows = 17920;
                    op_columns = 5280;
                    logical_start = logical_start +
                        (QKV_GROUPS + O_PROJ_GROUPS + GATE_GROUPS) * 24;
                    op_groups = UP_GROUPS;
                end
                5'd15: begin
                    valid = 1'b1;
                    op_rows = 5280;
                    op_columns = 17920;
                    logical_start = logical_start +
                        (QKV_GROUPS + O_PROJ_GROUPS + GATE_GROUPS + UP_GROUPS) * 24;
                    op_groups = DOWN_GROUPS;
                end
                default: valid = 1'b0;
            endcase
            if (command_id == 5'd3)
                op_groups = QKV_GROUPS;
        end

        if (valid) begin
            op_groups = op_groups * 24 / POOL_LANES;
            matrix_rows = 16'(op_rows);
            matrix_columns = 16'(op_columns);
            logical_records = op_groups * POOL_LANES;
            logical_end = logical_start + logical_records;
            first_pc = 5'(logical_start % HBM_PCS);
            for (integer pc = 0; pc < HBM_PCS; pc++) begin
                first_record = logical_start + ((pc - logical_start) % HBM_PCS + HBM_PCS) % HBM_PCS;
                if (first_record < logical_end) begin
                    local_pc_record = first_record / HBM_PCS;
                    pc_records = (logical_end - 1 - first_record) / HBM_PCS + 1;
                end else begin
                    local_pc_record = 0;
                    pc_records = 0;
                end
                pc_base_address[pc*33 +: 33] = 33'(local_pc_record * 64);
                pc_record_count[pc*32 +: 32] = 32'(pc_records);
            end
        end else begin
            first_pc = '0;
            pc_base_address = '0;
            pc_record_count = '0;
        end
    end

    initial begin
        if (HBM_PCS < 1 || (POOL_LANES != 24 && POOL_LANES != 32) ||
            (96 % POOL_LANES) != 0)
            $error("Huginn HBM descriptor requires 24 or 32 pool lanes");
    end
endmodule
