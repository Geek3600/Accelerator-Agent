`timescale 1ns / 1ps

module usw512_word_decoder (
    input  logic [511:0] usw_word,
    input  logic [1:0]   subchunk_index,
    output logic [63:0]  subchunk_nz,
    output logic [63:0]  subchunk_sgn,
    output logic [7:0]   outlier_idx,
    output logic signed [15:0] outlier_val
);
    wire [69:0] decoded_nz;
    wire [69:0] decoded_sgn;

    always_comb begin
        case (subchunk_index)
            2'd0: begin
                subchunk_nz = decoded_nz[0 +: 64];
                subchunk_sgn = decoded_sgn[0 +: 64];
                outlier_val = $signed(usw_word[0 +: 16]);
                outlier_idx = usw_word[16 +: 8];
            end
            2'd1: begin
                subchunk_nz = decoded_nz[4 +: 64];
                subchunk_sgn = decoded_sgn[4 +: 64];
                outlier_val = $signed(usw_word[24 +: 16]);
                outlier_idx = usw_word[40 +: 8];
            end
            2'd2: begin
                subchunk_nz = decoded_nz[3 +: 64];
                subchunk_sgn = decoded_sgn[3 +: 64];
                outlier_val = $signed(usw_word[48 +: 16]);
                outlier_idx = usw_word[64 +: 8];
            end
            default: begin
                subchunk_nz = decoded_nz[2 +: 64];
                subchunk_sgn = decoded_sgn[2 +: 64];
                outlier_val = $signed(usw_word[72 +: 16]);
                outlier_idx = usw_word[88 +: 8];
            end
        endcase
    end

    genvar byte_index;
    generate
        for (byte_index = 0; byte_index < 14; byte_index = byte_index + 1) begin : gen_decoder
            logic [7:0] packed_byte;
            wire [4:0] decoded_byte_nz;
            wire [4:0] decoded_byte_sgn;

            always_comb begin
                case (subchunk_index)
                    2'd0: packed_byte = usw_word[96 + byte_index*8 +: 8];
                    2'd1: packed_byte = usw_word[192 + byte_index*8 +: 8];
                    2'd2: packed_byte = usw_word[296 + byte_index*8 +: 8];
                    default: packed_byte = usw_word[400 + byte_index*8 +: 8];
                endcase
            end

            radix3_5trit_decoder u_decoder (
                .packed_byte(packed_byte),
                .trit_nz(decoded_byte_nz),
                .trit_sgn(decoded_byte_sgn)
            );

            assign decoded_nz[byte_index*5 +: 5] = decoded_byte_nz;
            assign decoded_sgn[byte_index*5 +: 5] = decoded_byte_sgn;
        end
    endgenerate
endmodule
