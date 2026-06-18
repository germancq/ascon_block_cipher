/**
 * File              : linear_diffusion_layer.sv
 * Author            : German C.Quiveu <germancq@dte.us.es>
 * Date              : 08.10.2025
 * Last Modified Date: 08.10.2025
 * Last Modified By  : German C.Quiveu <germancq@dte.us.es>
 */

module linear_diffusion_layer (
    input  [63:0] state_ascon_dout[4:0],
    output [63:0] state_ascon_din [4:0]
);

  assign state_ascon_din[0] = state_ascon_dout[0] ^ {state_ascon_dout[0][18:0],state_ascon_dout[0][63:19]} ^ {state_ascon_dout[0][27:0],state_ascon_dout[0][63:28]};

  assign state_ascon_din[1] = state_ascon_dout[1] ^ {state_ascon_dout[1][60:0],state_ascon_dout[1][63:61]} ^ {state_ascon_dout[1][38:0],state_ascon_dout[1][63:39]};

  assign state_ascon_din[2] = state_ascon_dout[2] ^ {state_ascon_dout[2][0:0],state_ascon_dout[2][63:1]} ^ {state_ascon_dout[2][5:0],state_ascon_dout[2][63:6]};

  assign state_ascon_din[3] = state_ascon_dout[3] ^ {state_ascon_dout[3][9:0],state_ascon_dout[3][63:10]} ^ {state_ascon_dout[3][16:0],state_ascon_dout[3][63:17]};

  assign state_ascon_din[4] = state_ascon_dout[4] ^ {state_ascon_dout[4][6:0],state_ascon_dout[4][63:7]} ^ {state_ascon_dout[4][40:0],state_ascon_dout[4][63:41]};

endmodule
