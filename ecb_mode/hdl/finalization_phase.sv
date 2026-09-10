/**
 * File              : finalization_phase.sv
 * Author            : German C.Quiveu <germancq@dte.us.es>
 * Date              : 26.08.2026
 * Last Modified Date: 08.09.2026
 * Last Modified By  : German C.Quiveu <germancq@dte.us.es>
 */

module finalization_phase #(
    parameter a = 12,
    parameter b = 8,
    parameter k = 128,
    parameter rate = 16
) (
    input clk,
    input rst,
    input start,
    output logic [63:0] state_din[4:0],
    input [63:0] state_dout[4:0],
    output logic [0:0] state_w[4:0],
    input [127:0] key,
    output [127:0] tag,
    output logic [7:0] p_impl_rounds,
    output logic p_impl_start,
    output logic p_impl_rst,
    input p_impl_end,
    output logic end_signal
);

  logic tag_cl;
  logic tag_w;
  logic [127:0] tag_din;
  register #(
      .DATA_WIDTH(128)
  ) r_tag (
      .clk(clk),
      .cl(tag_cl),
      .w(tag_w),
      .din(tag_din),
      .dout(tag)
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
    tag_w = 0;
    tag_din = 0;
    tag_cl = 0;
    case (current_state)
      IDLE: begin
        tag_cl = 1;
        if (start) begin
          next_state = ASCON_PERMUTATION_A_0;

          if (rate == 16) begin
            state_din[3] = state_dout[3] ^ key[127:64];
            state_din[2] = state_dout[2] ^ key[63:0];

            state_w[2]   = 1;
            state_w[3]   = 1;

          end else if (rate == 8) begin
            state_din[2] = state_dout[2] ^ key[127:64];
            state_din[1] = state_dout[1] ^ key[63:0];

            state_w[1]   = 1;
            state_w[2]   = 1;
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
        p_impl_rst = 1;
        next_state = END_STATE;

        tag_din = {state_dout[3] ^ key[63:0], state_dout[4] ^ key[127:64]};

        tag_w = 1;

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
