/**
 * File              : permutation.sv
 * Author            : German C.Quiveu <germancq@dte.us.es>
 * Date              : 08.10.2025
 * Last Modified Date: 08.10.2025
 * Last Modified By  : German C.Quiveu <germancq@dte.us.es>
 */

module permutation (
    input clk,
    input rst,
    input start,
    input [7:0] total_rounds,
    input [63:0] state_ascon_dout[4:0],
    output logic [63:0] state_ascon_din[4:0],
    output logic [0:0] state_ascon_w[4:0],
    output logic end_signal
);

  logic [63:0] cte_layer_state_2_din;
  constant_addition_layer cte_layer_impl (
      .total_rounds (total_rounds),
      .current_round(counter_rounds_dout),
      .state_2_din  (cte_layer_state_2_din),
      .state_2_dout (state_ascon_dout[2])
  );

  logic [63:0] subs_layer_state_ascon_din[4:0];
  substitution_layer subs_layer_impl (
      .state_ascon_dout(state_ascon_dout),
      .state_ascon_din (subs_layer_state_ascon_din)
  );

  logic [63:0] linear_diff_layer_state_ascon_din[4:0];
  linear_diffusion_layer linear_diff_layer_impl (
      .state_ascon_dout(state_ascon_dout),
      .state_ascon_din (linear_diff_layer_state_ascon_din)
  );

  logic counter_rounds_rst;
  logic counter_rounds_up;
  logic [7:0] counter_rounds_dout;
  counter #(
      .DATA_WIDTH(8)
  ) counter_rounds (
      .clk (clk),
      .rst (counter_rounds_rst),
      .up  (counter_rounds_up),
      .down(0),
      .din (0),
      .dout(counter_rounds_dout)
  );

  logic [2:0] current_state, next_state;

  localparam IDLE = 0;
  localparam CTE_LAYER = 1;
  localparam SUBS_LAYER = 2;
  localparam DIFF_LAYER = 3;
  localparam END_STATE = 4;

  logic [31:0] j;

  always_comb begin
    next_state = current_state;

    counter_rounds_rst = 0;
    counter_rounds_up = 0;

    end_signal = 0;

    for (j = 0; j < 5; j++) begin
      state_ascon_din[j] = 0;
      state_ascon_w[j]   = 0;
    end

    case (current_state)
      IDLE: begin
        counter_rounds_rst = 1;
        if (start) begin
          next_state = CTE_LAYER;
        end
      end
      CTE_LAYER: begin
        state_ascon_din[2] = cte_layer_state_2_din;
        state_ascon_w[2] = 1;
        next_state = SUBS_LAYER;
      end
      SUBS_LAYER: begin
        for (j = 0; j < 5; j++) begin
          state_ascon_din[j] = subs_layer_state_ascon_din[j];
          state_ascon_w[j]   = 1;
        end
        counter_rounds_up = 1;
        next_state = DIFF_LAYER;
      end
      DIFF_LAYER: begin
        for (j = 0; j < 5; j++) begin
          state_ascon_din[j] = linear_diff_layer_state_ascon_din[j];
          state_ascon_w[j]   = 1;
        end
        next_state = CTE_LAYER;
        if (counter_rounds_dout == total_rounds) begin
          next_state = END_STATE;
        end
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
