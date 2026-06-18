/**
 * File              : substitution_layer.sv
 * Author            : German C.Quiveu <germancq@dte.us.es>
 * Date              : 07.10.2025
 * Last Modified Date: 07.10.2025
 * Last Modified By  : German C.Quiveu <germancq@dte.us.es>
 */

module substitution_layer (
    input  [63:0] state_ascon_dout[4:0],
    output [63:0] state_ascon_din [4:0]
);

  logic [7:0] sbox[31:0];
  assign sbox[0]  = 8'h4;
  assign sbox[1]  = 8'hb;
  assign sbox[2]  = 8'h1f;
  assign sbox[3]  = 8'h14;
  assign sbox[4]  = 8'h1a;
  assign sbox[5]  = 8'h15;
  assign sbox[6]  = 8'h9;
  assign sbox[7]  = 8'h2;
  assign sbox[8]  = 8'h1b;
  assign sbox[9]  = 8'h5;
  assign sbox[10] = 8'h8;
  assign sbox[11] = 8'h12;
  assign sbox[12] = 8'h1d;
  assign sbox[13] = 8'h3;
  assign sbox[14] = 8'h6;
  assign sbox[15] = 8'h1c;
  assign sbox[16] = 8'h1e;
  assign sbox[17] = 8'h13;
  assign sbox[18] = 8'h7;
  assign sbox[19] = 8'he;
  assign sbox[20] = 8'h0;
  assign sbox[21] = 8'hd;
  assign sbox[22] = 8'h11;
  assign sbox[23] = 8'h18;
  assign sbox[24] = 8'h10;
  assign sbox[25] = 8'hc;
  assign sbox[26] = 8'h1;
  assign sbox[27] = 8'h19;
  assign sbox[28] = 8'h16;
  assign sbox[29] = 8'ha;
  assign sbox[30] = 8'hf;
  assign sbox[31] = 8'h17;



  genvar i;
  generate
    for (i = 0; i < 64; i++) begin
      assign state_ascon_din[0][i] = sbox[{
        state_ascon_dout[0][i],
        state_ascon_dout[1][i],
        state_ascon_dout[2][i],
        state_ascon_dout[3][i],
        state_ascon_dout[4][i]
      }][4];
      assign state_ascon_din[1][i] = sbox[{
        state_ascon_dout[0][i],
        state_ascon_dout[1][i],
        state_ascon_dout[2][i],
        state_ascon_dout[3][i],
        state_ascon_dout[4][i]
      }][3];
      assign state_ascon_din[2][i] = sbox[{
        state_ascon_dout[0][i],
        state_ascon_dout[1][i],
        state_ascon_dout[2][i],
        state_ascon_dout[3][i],
        state_ascon_dout[4][i]
      }][2];
      assign state_ascon_din[3][i] = sbox[{
        state_ascon_dout[0][i],
        state_ascon_dout[1][i],
        state_ascon_dout[2][i],
        state_ascon_dout[3][i],
        state_ascon_dout[4][i]
      }][1];
      assign state_ascon_din[4][i] = sbox[{
        state_ascon_dout[0][i],
        state_ascon_dout[1][i],
        state_ascon_dout[2][i],
        state_ascon_dout[3][i],
        state_ascon_dout[4][i]
      }][0];

    end
  endgenerate

endmodule
