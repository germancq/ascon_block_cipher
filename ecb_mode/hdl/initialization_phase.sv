/**
 * File              : initialization_phase.sv
 * Author            : German C.Quiveu <germancq@dte.us.es>
 * Date              : 26.08.2026
 * Last Modified Date: 26.08.2026
 * Last Modified By  : German C.Quiveu <germancq@dte.us.es>
 */
module initialization_phase #(
    parameter a = 12,
    parameter b = 8,
    parameter rate = 16,
    parameter version = 1
) (
    input clk,
    input rst,
    input start,
    output [63:0] state[4:0],
    input [127:0] key,
    input [127:0] nonce,
    output end_signal
);

  initial_state #(
      .a(a),
      .b(b),
      .k(128),
      .version(version),
      .rate(rate)
  ) i_state_impl (
      .key(key),
      .nonce(nonce),
      .state_ascon_din(state)
  );

  always_comb begin

  end


endmodule
