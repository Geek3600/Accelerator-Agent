`timescale 1ns / 1ps

module radix3_5trit_decoder (
    input  logic [7:0] packed_byte,
    output logic [4:0] trit_nz,
    output logic [4:0] trit_sgn
);
    localparam logic [255:0] NZ0 = 256'h0005b6db6db6db6db6db6db6db6db6db6db6db6db6db6db6db6db6db6db6db6d;
    localparam logic [255:0] NZ1 = 256'h00071f8fc7e3f1f8fc7e3f1f8fc7e3f1f8fc7e3f1f8fc7e3f1f8fc7e3f1f8fc7;
    localparam logic [255:0] NZ2 = 256'h0007fc01ffff803ffff007fffe00ffffc01ffff803ffff007fffe00ffffc01ff;
    localparam logic [255:0] NZ3 = 256'h0007ffffff0000001fffffffffffff8000000fffffffffffffc0000007ffffff;
    localparam logic [255:0] NZ4 = 256'h0007fffffffffffffffffffc00000000000000000001ffffffffffffffffffff;
    localparam logic [255:0] SGN0 = 256'h0001249249249249249249249249249249249249249249249249249249249249;
    localparam logic [255:0] SGN1 = 256'h00001c0e070381c0e070381c0e070381c0e070381c0e070381c0e070381c0e07;
    localparam logic [255:0] SGN2 = 256'h00000001ff00003fe00007fc0000ff80001ff00003fe00007fc0000ff80001ff;
    localparam logic [255:0] SGN3 = 256'h00000000000000001ffffffc0000000000000ffffffe00000000000007ffffff;
    localparam logic [255:0] SGN4 = 256'h00000000000000000000000000000000000000000001ffffffffffffffffffff;

    assign trit_nz = {NZ4[packed_byte], NZ3[packed_byte], NZ2[packed_byte], NZ1[packed_byte], NZ0[packed_byte]};
    assign trit_sgn = {SGN4[packed_byte], SGN3[packed_byte], SGN2[packed_byte], SGN1[packed_byte], SGN0[packed_byte]};
endmodule
