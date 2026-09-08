/**
 * File              : processing_associated_data_phase.sv
 * Author            : German C.Quiveu <germancq@dte.us.es>
 * Date              : 26.08.2026
 * Last Modified Date: 26.08.2026
 * Last Modified By  : German C.Quiveu <germancq@dte.us.es>
 */

module processing_associated_data_phase #(
    parameter a = 12,
    parameter b = 8,
    parameter rate = 16
) (
    input clk,
    input rst,
    input [(rate<<3)-1:0] block_i,
    input start,
    input feed_block,
    input last_block,
    output logic [63:0] state_din[4:0],
    input [63:0] state_dout[4:0],
    output logic [0:0] state_w[4:0],
    output logic [7:0] p_impl_rounds,
    output logic p_impl_start,
    output logic p_impl_rst,
    input p_impl_end,
    output logic error,
    output logic end_signal
);

  logic [3:0] current_state, next_state, jmp_state;
  logic r_jmp_state_cl;
  logic r_jmp_state_w;
  logic [3:0] r_jmp_state_din;

  register #(
      .DATA_WIDTH(4)
  ) r_jmp_state (
      .clk(clk),
      .cl(r_jmp_state_cl),
      .w(r_jmp_state_w),
      .din(r_jmp_state_din),
      .dout(jmp_state)
  );

  localparam IDLE = 0;
  localparam XOR_DATA = 1;
  localparam ASCON_PERMUTATION_B_0 = 2;
  localparam ASCON_PERMUTATION_B_1 = 3;
  localparam END_FEED = 4;
  localparam END_FEED_0 = 5;
  localparam FINAL_STEP_0 = 6;
  localparam FINAL_STEP_1 = 7;
  localparam END_STATE = 8;
  localparam ERROR = 9;

  logic [31:0] j;

  always_comb begin
    next_state = current_state;
    for (j = 0; j < 5; j++) begin
      state_w[j]   = 0;
      state_din[j] = 0;
    end
    p_impl_rounds = b;
    p_impl_rst = 0;
    p_impl_start = 0;
    end_signal = 0;
    error = 0;
    r_jmp_state_cl = 0;
    r_jmp_state_w = 0;
    r_jmp_state_din = current_state;
    case (current_state)
      IDLE: begin
        r_jmp_state_cl = 1;
        if (start) begin
          next_state = XOR_DATA;
        end
      end
      XOR_DATA: begin
        if (rate == 8) begin
          state_din[0] = state_dout[0] ^ block_i[63:0];
          state_w[0]   = 1;
        end else if (rate == 16) begin
          state_din[0] = state_dout[0] ^ block_i[63:0];
          state_din[1] = state_dout[1] ^ block_i[127:64];
          state_w[0]   = 1;
          state_w[1]   = 1;
        end else begin
          next_state = ERROR;
        end
        next_state = ASCON_PERMUTATION_B_0;
        r_jmp_state_w = 1;
        r_jmp_state_din = END_FEED;
      end
      ASCON_PERMUTATION_B_0: begin
        p_impl_rounds = b;
        for (j = 0; j < 5; j++) begin
          state_din[j] = state_dout[j];
        end
        p_impl_start = 1;
        next_state   = ASCON_PERMUTATION_B_1;
      end
      ASCON_PERMUTATION_B_1: begin
        p_impl_rounds = b;
        for (j = 0; j < 5; j++) begin
          state_din[j] = state_dout[j];
        end
        if (p_impl_end == 1) begin
          next_state = jmp_state;
          for (j = 0; j < 5; j++) begin
            state_w[j] = 1;
          end
        end
      end
      END_FEED: begin
        p_impl_rst = 1;
        next_state = END_FEED_0;
        if (last_block == 1) begin
          next_state = FINAL_STEP_0;
        end
      end
      END_FEED_0: begin
        end_signal = 1;
        if (feed_block == 1) begin
          next_state = XOR_DATA;
        end
      end
      FINAL_STEP_0: begin

        if (rate == 8) begin
          state_din[0] = state_dout[0] ^ (1 << 63);
          state_w[0]   = 1;
        end else if (rate == 16) begin
          state_din[1] = state_dout[1] ^ (1 << 63);
          state_w[1]   = 1;
        end

        next_state = ASCON_PERMUTATION_B_0;
        r_jmp_state_w = 1;
        r_jmp_state_din = FINAL_STEP_1;

      end
      FINAL_STEP_1: begin
        state_din[4] = state_dout[4] ^ (1 << 63);
        state_w[4]   = 1;
        next_state   = END_STATE;
      end
      END_STATE: begin
        end_signal = 1;
      end
      ERROR: begin
        error = 1;
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
