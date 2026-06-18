/**
 * File              : ascon_utils.sv
 * Author            : German C.Quiveu <germancq@dte.us.es>
 * Date              : 14.10.2025
 * Last Modified Date: 14.10.2025
 * Last Modified By  : German C.Quiveu <germancq@dte.us.es>
 */

virtual class ascon_utils #(
    parameter LEN  = 64,
    parameter RATE = 64
);

  static function logic [LEN-1:0] order(input logic [LEN-1:0] i_data);
    logic [LEN-1:0] result;

    for (int i = 0; i < (LEN >> 3); i++) begin
      //result[7+(i*8):(i*8)] = i_data[(LEN-1)-(i*8):(LEN)-((i+1)*8)];
      result[(i*8)+:8] = i_data[(LEN-1)-(i*8)-:8];
    end
    return result;

  endfunction

  static function logic [LEN-1:0] pad(input logic [LEN-1:0] i_data);
    logic [LEN-1:0] result;
    result = i_data ^ (1 << ($clog2(i_data) + 1));
    return result;

  endfunction

  static function logic [LEN-1:0] order_and_pad(input logic [LEN-1:0] i_data);
    logic [LEN-1:0] result;
    result = order(i_data);
    result = pad(result);
    return result;
  endfunction

  static function logic [RATE-1:0] xor_data(input logic [LEN-1:0] i_data);
    logic [RATE-1:0] result;
    result = 0;
    for (int i = 0; i < $floor(LEN / RATE); i++) begin
      result = result ^ i_data[(i*(RATE))+:RATE];
    end
    return result;

  endfunction


endclass
