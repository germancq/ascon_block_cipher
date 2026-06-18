/**
 * File              : initial_state.sv
 * Author            : German C.Quiveu <germancq@dte.us.es>
 * Date              : 09.10.2025
 * Last Modified Date: 09.10.2025
 * Last Modified By  : German C.Quiveu <germancq@dte.us.es>
 */

module initial_state #(
    parameter rate = 16,  //rate in bytes
    parameter a = 12,
    parameter b = 8,
    parameter k = 128,
    parameter version = 1
) (
    input  [127:0] key,
    input  [127:0] nonce,
    output [ 63:0] state_ascon_din[4:0]
);

  assign state_ascon_din[0][7:0] = version;  //64'h00001000808C0001;
  assign state_ascon_din[0][15:8] = 0;
  assign state_ascon_din[0][19:16] = a;  //64'h00001000808C0001;
  assign state_ascon_din[0][23:20] = b;  //64'h00001000808C0001;
  assign state_ascon_din[0][31:24] = k;  //64'h00001000808C0001;
  assign state_ascon_din[0][39:32] = 0;  //64'h00001000808C0001;
  assign state_ascon_din[0][47:40] = rate;  //64'h00001000808C0001;
  assign state_ascon_din[0][63:48] = 0;  //64'h00001000808C0001;

  assign state_ascon_din[1] = {
    key[71:64],
    key[79:72],
    key[87:80],
    key[95:88],
    key[103:96],
    key[111:104],
    key[119:112],
    key[127:120]
  };
  assign state_ascon_din[2] = {
    key[7:0], key[15:8], key[23:16], key[31:24], key[39:32], key[47:40], key[55:48], key[63:56]
  };
  //assign state_ascon_din[2] = ascon_utils#(.LEN(64))::order(key[63:0]);

  assign state_ascon_din[3] = {
    nonce[71:64],
    nonce[79:72],
    nonce[87:80],
    nonce[95:88],
    nonce[103:96],
    nonce[111:104],
    nonce[119:112],
    nonce[127:120]
  };
  assign state_ascon_din[4] = {
    nonce[7:0],
    nonce[15:8],
    nonce[23:16],
    nonce[31:24],
    nonce[39:32],
    nonce[47:40],
    nonce[55:48],
    nonce[63:56]
  };



endmodule





























