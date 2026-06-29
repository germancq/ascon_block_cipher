/**
 * File              : encrypt.sv
 * Author            : German C.Quiveu <germancq@dte.us.es>
 * Date              : 09.10.2025
 * Last Modified Date: 09.10.2025
 * Last Modified By  : German C.Quiveu <germancq@dte.us.es>
 */

module encrypt #(
    parameter a = 12,
    parameter b = 8,
    parameter rate = 16,
    parameter k = 128,
    parameter version = 1,
    parameter a_len = 40,
    parameter plaintext_len = 40
) (
    input clk,
    input rst,
    input start,
    input [k-1:0] key,
    input [127:0] nonce,
    input [plaintext_len-1:0] plaintext,
    input [a_len-1:0] a_data,
    output [plaintext_len-1:0] ciphertext,
    output [127:0] tag,
    output logic end_signal
);

  logic [1:0] sel_i_state;

  logic [63:0] key_0, key_1;

  logic [a_len:0] a_data_reord;
  logic [plaintext_len:0] plaintext_reord;

  logic [63:0] tag_0, tag_1;

  assign tag = {tag_0, tag_1};

  // assign key_0 = {
  //   key[7:0], key[15:8], key[23:16], key[31:24], key[39:32], key[47:40], key[55:48], key[63:56]
  // };
  //assign key_0 = ascon_utils#(.LEN(64))::order(key[63:0]);

  reorder #(
      .LEN(64)
  ) reorder_k0 (
      .i_data(key[63:0]),
      .o_data(key_0)
  );

  reorder #(
      .LEN(64)
  ) reorder_t0 (
      .i_data(state_ascon_dout[3]),
      .o_data(tag_0)
  );
  reorder #(
      .LEN(64)
  ) reorder_t1 (
      .i_data(state_ascon_dout[4]),
      .o_data(tag_1)
  );
  // assign key_1 = {
  //   key[71:64],
  //   key[79:72],
  //   key[87:80],
  //   key[95:88],
  //   key[103:96],
  //   key[111:104],
  //   key[119:112],
  //   key[127:120]
  // };
  //assign key_1 = ascon_utils#(.LEN(64))::order(key[127:64]);

  reorder #(
      .LEN(64)
  ) reorder_k1 (
      .i_data(key[127:64]),
      .o_data(key_1)
  );

  order_and_pad #(
      .LEN(a_len)
  ) ord_pad_impl (
      .i_data(a_data),
      .o_data(a_data_reord)
  );
  //assign a_data_reord = ascon_utils#(.LEN(a_len))::order_and_pad(a_data);
  order_and_pad #(
      .LEN(plaintext_len)
  ) ord_pad_impl_plaintext (
      .i_data(plaintext),
      .o_data(plaintext_reord)
  );


  localparam SEL_CUSTOM = 0;
  localparam SEL_INIT_STATE = 2;
  localparam SEL_PERMUTATION_STATE = 3;



  localparam N_BLOCKS = (plaintext_len / (rate << 3)) + 1;
  genvar i;


  logic [(N_BLOCKS*(rate<<3))-1:0] ciphertext_ord;
  logic [0:0] reg_ciphertext_cl[N_BLOCKS-1:0];
  logic [0:0] reg_ciphertext_w[N_BLOCKS-1:0];
  logic [(rate<<3)-1:0] reg_ciphertext_din[N_BLOCKS-1:0];
  logic [(rate<<3)-1:0] ciphertext_non_ord[N_BLOCKS-1:0];

  generate
    for (i = 0; i < N_BLOCKS; i++) begin
      register #(
          .DATA_WIDTH(rate << 3)
      ) reg_ciphertext_i (
          .clk(clk),
          .cl(reg_ciphertext_cl[i]),
          .w(reg_ciphertext_w[i]),
          .din(reg_ciphertext_din[i]),  //& ((2 << plaintext_len) - 1)),
          .dout(ciphertext_non_ord[i])
      );

      reorder #(
          .LEN(rate << 3)
      ) ord_pad_impl_ciphertext (
          .i_data(ciphertext_non_ord[N_BLOCKS-i-1]),
          .o_data(ciphertext_ord[(i*(rate<<3))+:(rate<<3)])
      );
    end
  endgenerate

  trail_0s_bytes #(
      .LEN(plaintext_len)
  ) ciphertext_without_0s (
      .i_data(ciphertext_ord >> ((N_BLOCKS * (rate << 3)) - plaintext_len)),
      .o_data(ciphertext)
  );
  //assign ciphertext = ciphertext_ord >> ((N_BLOCKS*(rate<<3))-plaintext_len);  //& ((2 << plaintext_len) - 1);



  logic [0:0] state_ascon_cl[4:0];
  logic [0:0] state_ascon_w[4:0];
  logic [63:0] state_ascon_din[4:0];
  logic [63:0] state_ascon_dout[4:0];

  logic [63:0] custom_state_ascon_din[4:0];
  logic [0:0] custom_state_ascon_w[4:0];
  generate
    for (i = 0; i < 5; i++) begin
      register #(
          .DATA_WIDTH(64)
      ) state_ascon_i (
          .clk(clk),
          .cl(state_ascon_cl[i]),
          .w(state_ascon_w[i]),
          .din(state_ascon_din[i]),
          .dout(state_ascon_dout[i])
      );

      mux_4 #(
          .N(64)
      ) mux_state_din (
          .a(custom_state_ascon_din[i]),
          .b(custom_state_ascon_din[i]),
          .c(i_state_impl_state_ascon_din[i]),
          .d(p_impl_state_ascon_din[i]),
          .dout(state_ascon_din[i]),
          .sel(sel_i_state)
      );

      mux_4 #(
          .N(1)
      ) mux_state_w (
          .a(custom_state_ascon_w[i]),
          .b(custom_state_ascon_w[i]),
          .c(1),
          .d(p_impl_state_ascon_w[i]),
          .dout(state_ascon_w[i]),
          .sel(sel_i_state)
      );

    end
  endgenerate


  logic [63:0] i_state_impl_state_ascon_din[4:0];
  initial_state #(
      .a(a),
      .b(b),
      .k(k),
      .version(version),
      .rate(rate)
  ) i_state_impl (
      .key(key),
      .nonce(nonce),
      .state_ascon_din(i_state_impl_state_ascon_din)
  );

  logic p_impl_rst;
  logic p_impl_start;
  logic [7:0] p_impl_total_rounds;
  logic [63:0] p_impl_state_ascon_din[4:0];
  logic [0:0] p_impl_state_ascon_w[4:0];
  logic p_impl_end_signal;
  permutation p_impl (
      .clk(clk),
      .rst(p_impl_rst),
      .start(p_impl_start),
      .total_rounds(p_impl_total_rounds),
      .state_ascon_dout(state_ascon_dout),
      .state_ascon_din(p_impl_state_ascon_din),
      .state_ascon_w(p_impl_state_ascon_w),
      .end_signal(p_impl_end_signal)
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

  //
  logic [15:0] generic_counter_o;
  logic generic_counter_up, generic_counter_rst;
  counter #(
      .DATA_WIDTH(16)
  ) generic_counter (
      .clk (clk),
      .rst (generic_counter_rst),
      .up  (generic_counter_up),
      .down(1'b0),
      .din (0),
      .dout(generic_counter_o)
  );

  localparam IDLE = 0;
  localparam INITIAL_STATE = 1;
  localparam XOR_KEY = 2;
  localparam ASCON_PERMUTATION_A_0 = 3;
  localparam ASCON_PERMUTATION_A_1 = 4;
  localparam ASCON_PERMUTATION_A_2 = 5;
  localparam ASCON_PERMUTATION_B_0 = 6;
  localparam ASCON_PERMUTATION_B_1 = 7;
  localparam ASCON_PERMUTATION_B_2 = 8;
  localparam ASSOCIATED_DATA = 9;
  localparam UPDATE_STATE = 10;
  localparam PLAINTEXT_LAST_BLOCK = 11;
  localparam PLAINTEXT_BLOCK = 12;
  localparam TAG_DATA_0 = 13;
  localparam TAG_DATA_1 = 14;
  localparam END_STATE = 15;


  logic [(rate<<3)-1:0] aux_var;
  logic [31:0] j;
  always_comb begin
    next_state = current_state;

    r_jmp_state_cl = 0;
    r_jmp_state_w = 0;
    r_jmp_state_din = current_state;

    p_impl_rst = 0;
    p_impl_start = 0;
    p_impl_total_rounds = a;

    sel_i_state = SEL_CUSTOM;

    generic_counter_rst = 0;
    generic_counter_up = 0;



    for (j = 0; j < 5; j++) begin
      state_ascon_cl[j] = 0;
      custom_state_ascon_w[j] = 0;
      custom_state_ascon_din[j] = 0;
    end

    for (j = 0; j < N_BLOCKS; j++) begin
      reg_ciphertext_cl[j]  = 0;
      reg_ciphertext_w[j]   = 0;
      reg_ciphertext_din[j] = 0;
    end


    end_signal = 0;

    case (current_state)
      IDLE: begin
        r_jmp_state_cl = 1;
        for (j = 0; j < N_BLOCKS; j++) begin
          reg_ciphertext_cl[j] = 1;
        end
        for (j = 0; j < 5; j++) begin
          state_ascon_cl[j] = 1;
        end
        p_impl_rst = 1;
        generic_counter_rst = 1;

        if (start) begin
          next_state = INITIAL_STATE;
        end
      end
      INITIAL_STATE: begin
        sel_i_state = SEL_INIT_STATE;
        next_state = ASCON_PERMUTATION_A_0;
        r_jmp_state_din = XOR_KEY;
        r_jmp_state_w = 1;
      end
      XOR_KEY: begin

        custom_state_ascon_din[4] = state_ascon_dout[4] ^ key_0;

        custom_state_ascon_din[3] = state_ascon_dout[3] ^ key_1;

        custom_state_ascon_w[4] = 1;
        custom_state_ascon_w[3] = 1;

        next_state = ASSOCIATED_DATA;
      end
      ASSOCIATED_DATA: begin
        custom_state_ascon_din[0] = state_ascon_dout[0] ^ a_data_reord[(generic_counter_o<<6)+:64];

        if (rate == 16) begin
          aux_var = a_data_reord >> ((generic_counter_o) << 7);

          //custom_state_ascon_din[0] = state_ascon_dout[0] ^ a_data_reord[(generic_counter_o<<7) +: 64];
          //custom_state_ascon_din[1] = state_ascon_dout[1] ^ a_data_reord[(generic_counter_o<<7)+64 +: 64];
          custom_state_ascon_din[0] = state_ascon_dout[0] ^ aux_var[63:0];
          custom_state_ascon_din[1] = state_ascon_dout[1] ^ aux_var[127:64];

          custom_state_ascon_w[1] = 1;

        end

        custom_state_ascon_w[0] = 1;

        generic_counter_up = 1;

        next_state = ASCON_PERMUTATION_B_0;
        r_jmp_state_w = 1;
        r_jmp_state_din = UPDATE_STATE;

        if (((generic_counter_o + 1) * (rate << 3)) < (a_len + 1)) begin
          r_jmp_state_din = ASSOCIATED_DATA;
        end



      end
      UPDATE_STATE: begin
        generic_counter_rst = 1;
        custom_state_ascon_din[4] = state_ascon_dout[4] ^ (1 << 63);
        custom_state_ascon_w[4] = 1;
        next_state = PLAINTEXT_BLOCK;
      end
      PLAINTEXT_BLOCK: begin
        custom_state_ascon_din[0] = state_ascon_dout[0] ^ plaintext_reord[(generic_counter_o<<6)+:64];
        reg_ciphertext_din[generic_counter_o][63:0] = state_ascon_dout[0] ^ plaintext_reord[(generic_counter_o<<6)+:64];

        if (rate == 16) begin
          aux_var = plaintext_reord >> ((generic_counter_o) << 7);

          custom_state_ascon_din[0] = state_ascon_dout[0] ^ aux_var[63:0];
          reg_ciphertext_din[generic_counter_o][63:0] = state_ascon_dout[0] ^ aux_var[63:0];
          custom_state_ascon_din[1] = state_ascon_dout[1] ^ aux_var[127:64];
          reg_ciphertext_din[generic_counter_o][127:64] = state_ascon_dout[1] ^ aux_var[127:64];

          custom_state_ascon_w[1] = 1;

        end

        custom_state_ascon_w[0] = 1;
        reg_ciphertext_w[generic_counter_o] = 1;

        generic_counter_up = 1;

        next_state = TAG_DATA_0;


        if (((generic_counter_o + 1) * (rate << 3)) < (plaintext_len + 1)) begin
          next_state = ASCON_PERMUTATION_B_0;
          r_jmp_state_w = 1;
          r_jmp_state_din = PLAINTEXT_BLOCK;
        end

      end
      /*
      PLAINTEXT_LAST_BLOCK: begin
        //by specification there is two rates 64 or 128 bits
        if (plaintext_len < 64) begin
          custom_state_ascon_din[0] = state_ascon_dout[0] ^ plaintext_reord[63:0] ^ (1<<(plaintext_len - ((plaintext_len/64)*64)));
          reg_ciphertext_din[63:0] = state_ascon_dout[0] ^ plaintext_reord[63:0] ^ (1<<(plaintext_len - ((plaintext_len/64)*64)));
        end else begin
          custom_state_ascon_din[0] = state_ascon_dout[0] ^ plaintext_reord[63:0];
          reg_ciphertext_din[63:0]  = state_ascon_dout[0] ^ plaintext_reord[63:0];
        end

        custom_state_ascon_w[0] = 1;
        reg_ciphertext_w = 1;
        next_state = TAG_DATA_0;
      end
      PLAINTEXT_BLOCK: begin
        custom_state_ascon_din[1] = state_ascon_dout[1] ^ plaintext_reord[127:64] ^ (1<<(plaintext_len - ((plaintext_len/64)*64)));
        custom_state_ascon_w[1] = 1;
        reg_ciphertext_w = 1;
        reg_ciphertext_din[127:64] = state_ascon_dout[1] ^ plaintext_reord[127:64] ^ (1<<(plaintext_len - ((plaintext_len/64)*64)));
        next_state = PLAINTEXT_LAST_BLOCK;
        //next_state = ASCON_PERMUTATION_B_0;
        //r_jmp_state_din = PLAINTEXT_LAST_BLOCK;
        //r_jmp_state_w = 1;
      end
      */
      TAG_DATA_0: begin
        custom_state_ascon_din[2] = state_ascon_dout[2] ^ key_1;
        custom_state_ascon_din[3] = state_ascon_dout[3] ^ key_0;
        custom_state_ascon_w[2] = 1;
        custom_state_ascon_w[3] = 1;
        next_state = ASCON_PERMUTATION_A_0;
        r_jmp_state_din = TAG_DATA_1;
        r_jmp_state_w = 1;
      end
      TAG_DATA_1: begin
        custom_state_ascon_din[3] = state_ascon_dout[3] ^ key_1;
        custom_state_ascon_din[4] = state_ascon_dout[4] ^ key_0;
        custom_state_ascon_w[3] = 1;
        custom_state_ascon_w[4] = 1;
        next_state = END_STATE;
      end
      END_STATE: begin
        end_signal = 1;
      end
      ASCON_PERMUTATION_A_0: begin
        sel_i_state = SEL_PERMUTATION_STATE;
        p_impl_total_rounds = a;
        p_impl_start = 1;
        next_state = ASCON_PERMUTATION_A_1;
      end
      ASCON_PERMUTATION_A_1: begin
        sel_i_state = SEL_PERMUTATION_STATE;
        p_impl_total_rounds = a;
        if (p_impl_end_signal == 1) begin
          next_state = ASCON_PERMUTATION_A_2;
        end
      end
      ASCON_PERMUTATION_A_2: begin
        sel_i_state = SEL_PERMUTATION_STATE;
        p_impl_total_rounds = a;
        p_impl_rst = 1;
        next_state = jmp_state;
      end
      ASCON_PERMUTATION_B_0: begin
        sel_i_state = SEL_PERMUTATION_STATE;
        p_impl_total_rounds = b;
        p_impl_start = 1;
        next_state = ASCON_PERMUTATION_B_1;
      end
      ASCON_PERMUTATION_B_1: begin
        sel_i_state = SEL_PERMUTATION_STATE;
        p_impl_total_rounds = b;
        if (p_impl_end_signal == 1) begin
          next_state = ASCON_PERMUTATION_B_2;
        end
      end
      ASCON_PERMUTATION_B_2: begin
        sel_i_state = SEL_PERMUTATION_STATE;
        p_impl_total_rounds = b;
        p_impl_rst = 1;
        next_state = jmp_state;
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
