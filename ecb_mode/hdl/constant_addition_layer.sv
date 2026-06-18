/**
 * File              : constant_addition_layer.sv
 * Author            : German C.Quiveu <germancq@dte.us.es>
 * Date              : 07.10.2025
 * Last Modified Date: 07.10.2025
 * Last Modified By  : German C.Quiveu <germancq@dte.us.es>
 */

module constant_addition_layer (
    input  [ 3:0] total_rounds,
    input  [ 3:0] current_round,
    input  [63:0] state_2_dout,
    output [63:0] state_2_din
);

  logic [7:0] constants[11:0];
  assign constants[0]  = 8'hf0;
  assign constants[1]  = 8'he1;
  assign constants[2]  = 8'hd2;
  assign constants[3]  = 8'hc3;
  assign constants[4]  = 8'hb4;
  assign constants[5]  = 8'ha5;
  assign constants[6]  = 8'h96;
  assign constants[7]  = 8'h87;
  assign constants[8]  = 8'h78;
  assign constants[9]  = 8'h69;
  assign constants[10] = 8'h5a;
  assign constants[11] = 8'h4b;

  assign state_2_din   = state_2_dout ^ {56'b0, constants[12-total_rounds+current_round]};

endmodule
