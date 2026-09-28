/**
 * File              : ascon.sv
 * Author            : German C.Quiveu <germancq@dte.us.es>
 * Date              : 15.04.2026
 * Last Modified Date: 15.04.2026
 * Last Modified By  : German C.Quiveu <germancq@dte.us.es>
 */

module ascon #(
    parameter a = 12,
    parameter b = 8,
    parameter k = 128,
    parameter rate = 16,
    parameter version = 1
) (
    input clk,
    input rst,
    input start,
    input enc_dec,
    input [k-1:0] key,
    input [127:0] nonce,
    input [(rate<<3)-1:0] block_i,
    input feed_block,
    output feed_complete,
    input last_block,
    output [(rate<<3)-1:0] block_o,
    output [127:0] tag,
    output logic end_signal
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


  logic [63:0] init_phase_state_din[4:0];
  logic [0:0] init_phase_state_w[4:0];
  logic [7:0] init_p_impl_rounds;
  logic init_p_impl_start;
  logic init_p_impl_rst;
  logic init_p_active;
  logic init_end_signal;
  initialization_phase #(
      .a(a),
      .b(b),
      .k(k),
      .rate(rate),
      .version(version)
  ) impl_init_phase (
      .clk(clk),
      .rst(rst),
      .start(start),
      .state_din(init_phase_state_din),
      .state_dout(state_ascon_dout),
      .state_w(init_phase_state_w),
      .key(key),
      .nonce(nonce),
      .p_impl_rounds(init_p_impl_rounds),
      .p_impl_start(init_p_impl_start),
      .p_impl_rst(init_p_impl_rst),
      .p_impl_end(p_impl_end_signal),
      .p_active(init_p_active),
      .end_signal(init_end_signal)
  );


  logic [63:0] a_data_phase_state_din[4:0];
  logic [0:0] a_data_phase_state_w[4:0];
  logic [7:0] a_data_p_impl_rounds;
  logic a_data_p_impl_start;
  logic a_data_p_impl_rst;
  logic a_data_p_active;
  logic a_data_end_signal;
  logic a_data_end_feed_signal;
  logic a_data_error;
  processing_associated_data_phase #(
      .a(a),
      .b(b),
      .rate(rate)
  ) impl_adata_phase (
      .clk(clk),
      .rst(rst),
      .block_i(block_i),
      .start(init_end_signal),
      .feed_block(feed_block),
      .last_block(last_block),
      .state_din(a_data_phase_state_din),
      .state_dout(state_ascon_dout),
      .state_w(a_data_phase_state_w),
      .p_impl_rounds(a_data_p_impl_rounds),
      .p_impl_start(a_data_p_impl_start),
      .p_impl_rst(a_data_p_impl_rst),
      .p_impl_end(p_impl_end_signal),
      .p_active(a_data_p_active),
      .end_feed_signal(a_data_end_feed_signal),
      .error(a_data_error),
      .end_signal(a_data_end_signal)
  );


  logic [63:0] plaintext_phase_state_din[4:0];
  logic [0:0] plaintext_phase_state_w[4:0];
  logic [7:0] plaintext_p_impl_rounds;
  logic plaintext_p_impl_start;
  logic plaintext_p_impl_rst;
  logic plaintext_p_active;
  logic plaintext_end_signal;
  logic plaintext_end_feed_signal;
  logic plaintext_error;
  logic [(rate<<3)-1:0] plaintext_block_o;
  processing_plaintext_phase #(
      .a(a),
      .b(b),
      .rate(rate)
  ) impl_plaintext_phase (
      .clk(clk),
      .rst(rst),
      .block_i(block_i),
      .block_o(plaintext_block_o),
      .start(a_data_end_signal & !enc_dec),
      .feed_block(feed_block),
      .last_block(last_block),
      .end_feed_signal(plaintext_end_feed_signal),
      .state_din(plaintext_phase_state_din),
      .state_dout(state_ascon_dout),
      .state_w(plaintext_phase_state_w),
      .p_impl_rounds(plaintext_p_impl_rounds),
      .p_impl_start(plaintext_p_impl_start),
      .p_impl_rst(plaintext_p_impl_rst),
      .p_impl_end(p_impl_end_signal),
      .p_active(plaintext_p_active),
      .error(plaintext_error),
      .end_signal(plaintext_end_signal)
  );

  logic [63:0] ciphertext_phase_state_din[4:0];
  logic [0:0] ciphertext_phase_state_w[4:0];
  logic [7:0] ciphertext_p_impl_rounds;
  logic ciphertext_p_impl_start;
  logic ciphertext_p_impl_rst;
  logic ciphertext_p_active;
  logic ciphertext_end_signal;
  logic ciphertext_end_feed_signal;
  logic ciphertext_error;
  logic [(rate<<3)-1:0] ciphertext_block_o;
  processing_ciphertext_phase #(
      .a(a),
      .b(b),
      .rate(rate)
  ) impl_ciphertext_phase (
      .clk(clk),
      .rst(rst),
      .block_i(block_i),
      .block_o(ciphertext_block_o),
      .start(a_data_end_signal & enc_dec),
      .feed_block(feed_block),
      .last_block(last_block),
      .end_feed_signal(ciphertext_end_feed_signal),
      .state_din(ciphertext_phase_state_din),
      .state_dout(state_ascon_dout),
      .state_w(ciphertext_phase_state_w),
      .p_impl_rounds(ciphertext_p_impl_rounds),
      .p_impl_start(ciphertext_p_impl_start),
      .p_impl_rst(ciphertext_p_impl_rst),
      .p_impl_end(p_impl_end_signal),
      .p_active(ciphertext_p_active),
      .error(ciphertext_error),
      .end_signal(ciphertext_end_signal)
  );


  logic [63:0] finalization_phase_state_din[4:0];
  logic [0:0] finalization_phase_state_w[4:0];
  logic [7:0] finalization_p_impl_rounds;
  logic finalization_p_impl_start;
  logic finalization_p_impl_rst;
  logic finalization_p_active;
  finalization_phase #(
      .a(a),
      .b(b),
      .k(k),
      .rate(rate)
  ) impl_fin_phase (
      .clk(clk),
      .rst(rst),
      .start(plaintext_end_signal | ciphertext_end_signal),
      .state_din(finalization_phase_state_din),
      .state_dout(state_ascon_dout),
      .state_w(finalization_phase_state_w),
      .key(key),
      .tag(tag),
      .p_impl_rounds(finalization_p_impl_rounds),
      .p_impl_start(finalization_p_impl_start),
      .p_impl_rst(finalization_p_impl_rst),
      .p_impl_end(p_impl_end_signal),
      .p_active(finalization_p_active),
      .end_signal(end_signal)
  );

  assign feed_complete = ciphertext_end_feed_signal | plaintext_end_feed_signal | a_data_end_feed_signal;

  assign block_o = enc_dec == 0 ? plaintext_block_o : ciphertext_block_o;

  assign p_impl_start = init_p_impl_start | a_data_p_impl_start | plaintext_p_impl_start | ciphertext_p_impl_start | finalization_p_impl_start;

  logic p_active;
  assign p_active = init_p_active | a_data_p_active | plaintext_p_active | ciphertext_p_active | finalization_p_active;

  logic [0:0] phase_state_ascon_w[4:0];
  logic [63:0] phase_state_ascon_din[4:0];

  logic [0:0] state_ascon_w[4:0];
  logic [63:0] state_ascon_din[4:0];
  logic [63:0] state_ascon_dout[4:0];
  genvar i;


  generate
    for (i = 0; i < 5; i++) begin
      register #(
          .DATA_WIDTH(64)
      ) state_ascon_i (
          .clk(clk),
          .cl(rst),
          .w(p_active == 1 ? p_impl_state_ascon_w[i] : phase_state_ascon_w[i]),
          .din(p_active == 1 ? p_impl_state_ascon_din[i] : phase_state_ascon_din[i]),
          .dout(state_ascon_dout[i])
      );

      assign phase_state_ascon_w[i] = init_phase_state_w[i] | a_data_phase_state_w[i] | plaintext_phase_state_w[i] | ciphertext_phase_state_w[i] | finalization_phase_state_w[i];

      assign phase_state_ascon_din[i] = init_phase_state_din[i] | a_data_phase_state_din[i] | plaintext_phase_state_din[i] | ciphertext_phase_state_din[i] | finalization_phase_state_din[i];
    end
  endgenerate


endmodule
