/**
 * File              : ascon.sv
 * Author            : German C.Quiveu <germancq@dte.us.es>
 * Date              : 15.04.2026
 * Last Modified Date: 15.04.2026
 * Last Modified By  : German C.Quiveu <germancq@dte.us.es>
 */

module ascon #(
    parameter BLK_LEN = 256,
    parameter KEY_LEN = 256,
    parameter a = 12,
    parameter b = 8,
    parameter rate = 16,
    parameter version = 1,
    parameter a_len = 32,
    parameter plaintext_len = 96
) (
    input clk,
    input rst,
    input [KEY_LEN-1:0] key,
    input [BLK_LEN-1:0] block_i,  //includes a_data and nonce
    output [BLK_LEN-1:0] block_o,  //includes tag
    input rq_data,
    output end_key_generation,
    output end_signal
);

  assign end_key_generation = 1;

  logic [a_len-1:0] a_data_encrypt;
  logic [plaintext_len-1:0] plaintext_encrypt;
  logic [127:0] nonce_encrypt;
  logic [127:0] tag_encrypt;
  logic [plaintext_len-1:0] ciphertext_encrypt;

  assign block_o[127:0] = tag_encrypt;
  assign block_o[(128+plaintext_len)-1:128] = ciphertext_encrypt;

  assign nonce_encrypt = block_i[127:0];
  assign a_data_encrypt = block_i[(128+a_len)-1:128];
  assign plaintext_encrypt = block_i[BLK_LEN-1:(128+a_len)];

  encrypt #(
      .k(KEY_LEN),
      .a(a),
      .b(b),
      .rate(rate),
      .version(version),
      .a_len(a_len),
      .plaintext_len(plaintext_len)
  ) ascon_encrypt (
      .clk(clk),
      .rst(rst),
      .start(rq_data),
      .key(key),
      .nonce(nonce_encrypt),
      .plaintext(plaintext_encrypt),
      .a_data(a_data_encrypt),
      .ciphertext(ciphertext_encrypt),
      .tag(tag_encrypt),
      .end_signal(end_signal)
  );

endmodule
