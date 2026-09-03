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
    parameter k = 128,
    parameter rate = 16,
    parameter version = 1
) (
    input clk,
    input rst,
    input start,
    output logic [63:0] state_din[4:0],
    input [63:0] state_dout[4:0],
    output logic [0:0] state_w[4:0],
    input [127:0] key,
    input [127:0] nonce,
    output logic [7:0] p_impl_rounds,
    output logic p_impl_start,
    output logic p_impl_rst,
    input p_impl_end,
    output logic end_signal
);

  logic [2:0] current_state, next_state;
  logic [31:0] j;
  localparam IDLE = 0;
  localparam ASCON_PERMUTATION_A_0 = 1;
  localparam ASCON_PERMUTATION_A_1 = 2;
  localparam XOR_KEY = 3;
  localparam END_STATE = 4;

  always_comb begin
    next_state = current_state;
    for (j = 0; j < 5; j++) begin
      state_w[j]   = 0;
      state_din[j] = 0;
    end
    p_impl_rounds = a;
    p_impl_rst = 0;
    p_impl_start = 0;
    end_signal = 0;
    case (current_state)
      IDLE: begin
        if (start) begin
          next_state = ASCON_PERMUTATION_A_0;

          state_din[0][7:0] = version;  //64'h00001000808C0001;
          state_din[0][15:8] = 0;
          state_din[0][19:16] = a;  //64'h00001000808C0001;
          state_din[0][23:20] = b;  //64'h00001000808C0001;
          state_din[0][31:24] = k;  //64'h00001000808C0001;
          state_din[0][39:32] = 0;  //64'h00001000808C0001;
          state_din[0][47:40] = rate;  //64'h00001000808C0001;
          state_din[0][63:48] = 0;  //64'h00001000808C0001;
          state_din[0][63:48] = 0;  //64'h00001000808C0001;

          state_din[1] = key[127:64];
          state_din[2] = key[63:0];
          state_din[3] = nonce[127:64];
          state_din[4] = nonce[63:0];

          for (j = 0; j < 5; j++) begin
            state_w[j] = 1;
          end
        end
      end
      ASCON_PERMUTATION_A_0: begin
        p_impl_rounds = a;
        for (j = 0; j < 5; j++) begin
          state_din[j] = state_dout[j];
        end
        p_impl_start = 1;
        next_state   = ASCON_PERMUTATION_A_1;
      end
      ASCON_PERMUTATION_A_1: begin
        p_impl_rounds = a;
        for (j = 0; j < 5; j++) begin
          state_din[j] = state_dout[j];
        end
        if (p_impl_end == 1) begin
          next_state = XOR_KEY;
          for (j = 0; j < 5; j++) begin
            state_w[j] = 1;
          end
        end
      end
      XOR_KEY: begin
        p_impl_rst   = 1;
        next_state   = END_STATE;

        state_din[3] = state_dout[3] ^ key[127:64];
        state_din[4] = state_dout[4] ^ key[63:0];

        state_w[3]   = 1;
        state_w[4]   = 1;

      end
      END_STATE: begin
        end_signal = 1;
      end

    endcase

  end

  always_ff @(posedge clk) begin
    if (rst) begin
      current_state <= IDLE;
    end else begin
      current_state <= next_state;
    end

  end

endmodule
