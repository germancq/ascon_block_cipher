/**
 * File              : permutation_comb.sv
 * Author            : German C.Quiveu <germancq@dte.us.es>
 * Date              : 09.11.2026
 * Last Modified Date: 09.11.2026
 * Last Modified By  : German C.Quiveu <germancq@dte.us.es>
 */

module permutation_comb (
    input clk,
    input rst,
    input start,
    input [3:0] total_rounds,
    input [63:0] state_ascon_dout[4:0],
    output logic [63:0] state_ascon_din[4:0],
    output logic [0:0] state_ascon_w[4:0],
    output logic end_signal
);

  logic counter_rounds_rst;
  logic counter_rounds_up;
  logic [3:0] counter_rounds_dout;
  counter #(
      .DATA_WIDTH(4)
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
  localparam COMB_LAYER = 1;
  localparam END_STATE = 4;

  logic [31:0] j;
  logic [7:0] cte_value;
  logic [63:0] x[4:0];

  always_comb begin
    next_state = current_state;

    counter_rounds_rst = 0;
    counter_rounds_up = 0;

    end_signal = 0;
    cte_value = 0;

    for (j = 0; j < 5; j++) begin
      state_ascon_din[j] = 0;
      state_ascon_w[j]   = 0;
    end

    case (current_state)
      IDLE: begin
        counter_rounds_rst = 1;
        if (start) begin
          next_state = COMB_LAYER;
        end
      end
      COMB_LAYER: begin

        for (j = 0; j < 5; j++) begin
          x[j] = state_ascon_dout[j];
        end
        //cte layer
        if (total_rounds == 8) begin
          cte_value[3:0] = counter_rounds_dout + 4;
          cte_value[7:4] = 11 - counter_rounds_dout;
        end else begin
          cte_value[3:0] = counter_rounds_dout;
          cte_value[7:4] = 15 - counter_rounds_dout;
        end
        x[2] = x[2] ^ cte_value;
        //subs_layer
        for (j = 0; j < 64; j++) begin
          state_ascon_din[0][j] = (x[4][j] & x[1][j]) ^ (x[3][j]) ^ (x[2][j] & x[1][j]) ^ (x[2][j]) ^ (x[1][j] & x[0][j]) ^ (x[1][j]) ^ (x[0][j]);

          state_ascon_din[1][j] = (x[4][j]) ^ (x[3][j] & x[2][j]) ^ (x[3][j] & x[1][j]) ^ (x[3][j]) ^ (x[2][j] & x[1][j]) ^ (x[2][j]) ^ (x[1][j]) ^ (x[0][j]);

          state_ascon_din[2][j] = (x[4][j] & x[3][j]) ^ (x[4][j]) ^ (x[2][j]) ^ (x[1][j]) ^ 1;

          state_ascon_din[3][j] = (x[4][j] & x[0][j]) ^ (x[4][j]) ^ (x[3][j] & x[0][j]) ^ (x[3][j]) ^ (x[2][j]) ^ (x[1][j]) ^ (x[0][j]);

          state_ascon_din[4][j] = (x[4][j] & x[1][j]) ^ (x[4][j]) ^ (x[3][j]) ^ (x[1][j] & x[0][j]) ^ (x[1][j]);

        end


        //diffusion layer
        state_ascon_din[0] = state_ascon_din[0] ^ {state_ascon_din[0][18:0], state_ascon_din[0][63:19]} ^ {state_ascon_din[0][27:0], state_ascon_din[0][63:28]};

        state_ascon_din[1] = state_ascon_din[1] ^ {state_ascon_din[1][60:0],state_ascon_din[1][63:61]} ^ {state_ascon_din[1][38:0],state_ascon_din[1][63:39]};

        state_ascon_din[2] = state_ascon_din[2] ^ {state_ascon_din[2][0:0],state_ascon_din[2][63:1]} ^ {state_ascon_din[2][5:0],state_ascon_din[2][63:6]};

        state_ascon_din[3] = state_ascon_din[3] ^ {state_ascon_din[3][9:0],state_ascon_din[3][63:10]} ^ {state_ascon_din[3][16:0],state_ascon_din[3][63:17]};

        state_ascon_din[4] = state_ascon_din[4] ^ {state_ascon_din[4][6:0],state_ascon_din[4][63:7]} ^ {state_ascon_din[4][40:0],state_ascon_din[4][63:41]};

        for (j = 0; j < 5; j++) begin
          state_ascon_w[j] = 1;
        end

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










