#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : ascon_aead.py
# Author            : German C.Quiveu <germancq@dte.us.es>
# Date              : 03.07.2025
# Last Modified Date: 03.07.2025
# Last Modified By  : German C.Quiveu <germancq@dte.us.es>

import math
import sys

IV = 0x00001000808C0001

Const = [
    0xF0,
    0xE1,
    0xD2,
    0xC3,
    0xB4,
    0xA5,
    0x96,
    0x87,
    0x78,
    0x69,
    0x5A,
    0x4B,
]

Sbox = [
    0x4,
    0xB,
    0x1F,
    0x14,
    0x1A,
    0x15,
    0x9,
    0x2,
    0x1B,
    0x5,
    0x8,
    0x12,
    0x1D,
    0x3,
    0x6,
    0x1C,
    0x1E,
    0x13,
    0x7,
    0xE,
    0x0,
    0xD,
    0x11,
    0x18,
    0x10,
    0xC,
    0x1,
    0x19,
    0x16,
    0xA,
    0xF,
    0x17,
]


class ASCON_AEAD:

    def __init__(self, key, nonce):
        self.input_array = []
        self.state_array = []
        self.key = key
        self.key_0 = 0
        self.key_1 = 0
        self.nonce = nonce
        self.tag = []
        self.rate = 128
        self.a = 12
        self.b = 8

    def ror(self, size, x, i):
        if i == 0:
            return x
        else:
            lsb = x & 0x1
            out = (x >> 1) + (lsb << (size - 1))
            return self.ror(size, out, i - 1)

    def parse(self, x, r):
        print("parse x = {} with r = {}".format(hex(x), r))
        arr = []
        i = 1
        x_aux = x  # & ((2**r) - 1)
        while x_aux != 0:
            #print(hex(x_aux))
            arr.insert(i - 1, x_aux & ((2**r) - 1))
            x_aux = x >> (r * i)
            i = i + 1

        arr_result = []
        for j in range(0, arr.__len__()):
            arr_result.insert(i, arr[arr.__len__() - j - 1])

        return arr_result

    def pad(self, x, r, len_bits):
        #bits_used = int(math.ceil((math.log2(x))))
        #print(bits_used)
        #print(r)
        #bytes_used = int(math.ceil(bits_used / 8))

        # if bytes_used < r / 8:
        #    return (1 << (bytes_used * 8)) + x
        # else:
        #    return x
        return (1 << (len_bits)) + x

    def print_state(self):
        print("/////////////")
        print("S0 = {}".format(hex(self.state_array[0])))
        print("S1 = {}".format(hex(self.state_array[1])))
        print("S2 = {}".format(hex(self.state_array[2])))
        print("S3 = {}".format(hex(self.state_array[3])))
        print("S4 = {}".format(hex(self.state_array[4])))
        print("/////////////")

    def encrypt(self, plaintext, a_data, len_plaintext_bits):
        self.get_initial_state()
        self.ascon_permutation(self.a)
        print("xor key with state")
        self.state_array[4] = (self.state_array[4] ^ self.key_0) & ((2**64)-1)
        self.state_array[3] = (self.state_array[3] ^ self.key_1) & ((2**64)-1) 
        self.print_state()
        print("associated data")
        a_data_endian = self.parse(a_data, 8)
        a_data_reord = 0
        i = 0
        for a_d in a_data_endian:
            a_data_reord = (a_d << (8 * i)) + a_data_reord
            i = i + 1
        if(i<(len_plaintext_bits/8)):
            shift = int(len_plaintext_bits/8)
            a_data_reord = a_data_reord << ((shift - i)*8)

        print("non-padded a_data = {0}".format(hex(a_data_reord)))


        associated_data = self.pad(a_data_reord, self.rate,len_plaintext_bits)
        print("padded a_data = {0}".format(hex(associated_data)))
        associated_data = self.parse(associated_data, self.rate)
        len_a_data = len(associated_data)

        print(len_a_data)

        # associated_data[len_a_data - 1] = self.pad(
        #    associated_data[len_a_data - 1], self.rate
        # )

        for i in range(0, len_a_data):
            a = associated_data[len_a_data - i - 1]
            print("a_data = {0}".format(hex(a)))
            self.state_array[0] = self.state_array[0] ^ (a & ((2**64) - 1))
            self.state_array[0] = self.state_array[0] & ((2**64)-1)
            if self.rate == 128:
                self.state_array[1] = self.state_array[1] ^ (a >> 64)
                self.state_array[1] = self.state_array[1] & ((2**64)-1)
            self.print_state()
            self.ascon_permutation(self.b)

        print("update state")
        self.state_array[4] = self.state_array[4] ^ (1 << 63)
        self.state_array[4] = self.state_array[4] & ((2**64)-1)
        self.print_state()

        print("plaintext")
        plaintext_endian = self.parse(plaintext, 8)
        plaintext_reord = 0
        i = 0
        for p_d in plaintext_endian:
            print(hex(p_d))
            plaintext_reord = (p_d << (8 * i)) + plaintext_reord
            i = i + 1

        if(i<(len_plaintext_bits/8)):
            shift = int(len_plaintext_bits/8)
            plaintext_reord = plaintext_reord << ((shift - i)*8)

        plaintext_reord = self.pad(
            plaintext_reord, self.rate, len_plaintext_bits
        )
        print("plaintext padded and reord data = {}".format(hex(plaintext_reord)))

        plaintext_data = self.parse(plaintext_reord, self.rate)
        plaintext_data_parse=[]
        len_plaintext_data = len(plaintext_data)

        for i in range(0,len_plaintext_data):
            plaintext_data_parse.append(0)

        for i in range(0,len_plaintext_data):
            plaintext_data_parse[i] = plaintext_data[len_plaintext_data - i-1]

        len_plaintext_data_parse = len(plaintext_data_parse)
        print("len plaintext data = {}".format(len_plaintext_data))
        bits_for_last_block = int(
            len_plaintext_bits - (self.rate * (len_plaintext_data - 1))
        )
        # bits_for_last_block = int(
        #    math.ceil(math.log2(plaintext_data[len_plaintext_data - 1]))
        # )
        for i in range(0, len(plaintext_data_parse)):
            print("plaintext_data_parse_{0} = {1}".format(i, hex(plaintext_data_parse[i])))


        for i in range(0, len(plaintext_data_parse)):
            print("plaintext_data_parse_{0} = {1}".format(i, hex(plaintext_data_parse[i])))

        print(bits_for_last_block)
        ciphertext_arr = []
        for i in range(0, len_plaintext_data_parse):
            if i < len_plaintext_data_parse - 1:
                print("final block plaintext{} is = {}".format(i, hex(plaintext_data_parse[i])))
                print("state_0 is = {}".format(hex(self.state_array[0])))
                self.state_array[0] = self.state_array[0] ^ (
                    plaintext_data_parse[i] & ((2**64) - 1)
                )
                self.state_array[0] = self.state_array[0] & ((2**64)-1)
                if self.rate == 128:
                    self.state_array[1] = self.state_array[1] ^ (
                        plaintext_data_parse[i] >> 64
                    )
                    self.state_array[1] = self.state_array[1] & ((2**64)-1)
                    ciphertext_arr.insert(
                        i, ((self.state_array[1] << 64) + self.state_array[0])
                    )
                else:
                    ciphertext_arr.insert(i, self.state_array[0])

                self.ascon_permutation(self.b)
                self.print_state()
            else:
                print("plaintext{} is = {}".format(i, hex(plaintext_data_parse[i])))
                print("state_0 is = {}".format(hex(self.state_array[0])))
                self.state_array[0] = self.state_array[0] ^ (
                    plaintext_data_parse[i] & ((2**64) - 1)
                )
                self.state_array[0] = self.state_array[0] & ((2**64)-1)

                if self.rate == 128:
                    self.state_array[1] = self.state_array[1] ^ (
                        plaintext_data_parse[i] >> 64
                    )
                    self.state_array[1] = self.state_array[1] & ((2**64)-1)
                    print("xor is {}".format(hex(self.state_array[0])))
                    print("bits_for_last_block is {}".format(bits_for_last_block))
                    
                    c_aux = ((self.state_array[1] << 64) + (self.state_array[0])) & (
                        (2**bits_for_last_block) - 1
                    )
                    print("c_aux is {}".format(hex(c_aux)))
                    ciphertext_arr.insert(i, c_aux)
                else:
                    print("xor is {}".format(hex(self.state_array[0])))
                    c_aux = self.state_array[0] & (
                        (2**bits_for_last_block) - 1)
                    print("c_aux is {}".format(hex(c_aux)))
                    ciphertext_arr.insert(i, c_aux)

        self.print_state()
        i = 0
        for c_i in ciphertext_arr:
            print("ciphertext_arr c_{} = {}".format(i, hex(c_i)))
            i = i + 1

        print("tag")
        self.state_array[2] = self.state_array[2] ^ self.key_1
        self.state_array[2] = self.state_array[2] & ((2**64)-1)
        self.state_array[3] = self.state_array[3] ^ self.key_0
        self.state_array[3] = self.state_array[3] & ((2**64)-1)

        self.print_state()

        self.ascon_permutation(12)

        self.print_state()

        self.state_array[3] = self.state_array[3] ^ self.key_1
        self.state_array[3] = self.state_array[3] & ((2**64)-1)
        self.state_array[4] = self.state_array[4] ^ self.key_0
        self.state_array[4] = self.state_array[4] & ((2**64)-1)

        self.print_state()

        self.tag.insert(0, self.state_array[3])
        self.tag.insert(1, self.state_array[4])

        ciphertext_res = 0
        for i in range(0, len(ciphertext_arr)):
            print("ciphertext_arr c_{} = {}".format(i, hex(ciphertext_arr[i])))
            ciphertext_res = ciphertext_res + (ciphertext_arr[i] << (128 * i))
            print("ciphertext_res = {}".format(hex(ciphertext_res)))

        ciphertext_reord = 0
        ciphertext_endian = self.parse(ciphertext_res, 8)
        i = 0
        for c_d in ciphertext_endian:
            ciphertext_reord = (c_d << (8 * i)) + ciphertext_reord
            i = i + 1
        if i<(len_plaintext_bits/8):
            ciphertext_reord=ciphertext_reord << ((int(len_plaintext_bits/8)-i)*8)

        tag0_reord = 0
        tag0_endian = self.parse(self.tag[0], 8)
        i = 0
        for c_d in tag0_endian:
            #print(hex(c_d))
            tag0_reord = (c_d << (8 * i)) + tag0_reord
            i = i + 1
        if i<8:
            tag0_reord=tag0_reord << ((8-i)*8)

        tag1_reord = 0
        tag1_endian = self.parse(self.tag[1], 8)
        i = 0
        for c_d in tag1_endian:
            #print(hex(c_d))
            tag1_reord = (c_d << (8 * i)) + tag1_reord
            i = i + 1
        if i<8:
            tag1_reord=tag1_reord << ((8-i)*8)

        return ciphertext_reord, ((tag0_reord << 64) + tag1_reord)

    def get_initial_state(self):
        print(
            "initial_state with key = {} and nonce = {}".format(
                hex(self.key), hex(self.nonce)
            )
        )
        self.key_0 = (self.key) & ((2**64) - 1)
        self.key_1 = self.key >> 64
        print("key_0 = {}, key_1 = {}".format(
            hex(self.key_0), hex(self.key_1)))
        bytes_key_0 = self.parse(self.key_0, 8)
        bytes_key_1 = self.parse(self.key_1, 8)
        self.key_0 = 0
        self.key_1 = 0

        # for i in range(0, len(bytes_key_0)):
        i=0
        for i in range(0, 8):
            if i < len(bytes_key_0):
                self.key_0 = (bytes_key_0[i] << (8 * i)) + self.key_0
                i = i + 1

        if i<8:
            self.key_0=self.key_0 << ((8-i)*8)

        i=0

        for i in range(0, 8):
            if i < len(bytes_key_1):
                self.key_1 = (bytes_key_1[i] << (8 * i)) + self.key_1
                i = i + 1

        if i<8:
            self.key_1=self.key_1 << ((8-i)*8)
        # for i in range(0, len(bytes_key_1)):
        #    self.key_1 = (bytes_key_1[i] << (8 * i)) + self.key_1

        nonce_0 = (self.nonce) & ((2**64) - 1)
        nonce_1 = self.nonce >> 64
        bytes_nonce_0 = self.parse(nonce_0, 8)
        bytes_nonce_1 = self.parse(nonce_1, 8)
        nonce_0 = 0
        nonce_1 = 0

        # for i in range(0, len(bytes_nonce_0)):
        #    nonce_0 = (bytes_nonce_0[i] << (8 * i)) + nonce_0
        i=0
        for i in range(0, 8):
            if i < len(bytes_nonce_0):
                nonce_0 = (bytes_nonce_0[i] << (8 * i)) + nonce_0
                i = i + 1

        if i<8:
            nonce_0=nonce_0 << ((8-i)*8)
        # for i in range(0, len(bytes_nonce_1)):
        #     nonce_1 = (bytes_nonce_1[i] << (8 * i)) + nonce_1
        i=0
        for i in range(0, 8):
            if i < len(bytes_nonce_1):
                nonce_1 = (bytes_nonce_1[i] << (8 * i)) + nonce_1
                i = i + 1

        if i<8:
            nonce_1=nonce_1 << ((8-i)*8)

        initial_state = (
            (IV << 256)
            + (self.key_1 << 192)
            + (self.key_0 << 128)
            + (nonce_1 << 64)
            + (nonce_0)
        )
        self.state_array = self.parse(initial_state, 64)
        self.print_state()

    def ascon_permutation(self, rnd):
        for i in range(0, rnd):
            self.constant_addition_layer(rnd, i)
            self.substitution_layer()
            self.linear_diffusion_layer()

    def constant_addition_layer(self, rnd, i):
        print("constant_addition_layer")
        c = Const[12 - rnd + i]
        S2 = self.state_array[2]
        S2 = S2 ^ c
        self.state_array[2] = S2
        self.print_state()

    def substitution_layer(self):
        print("substitution_layer")
        S0 = self.state_array[0]
        S1 = self.state_array[1]
        S2 = self.state_array[2]
        S3 = self.state_array[3]
        S4 = self.state_array[4]
        new_S0 = 0
        new_S1 = 0
        new_S2 = 0
        new_S3 = 0
        new_S4 = 0

        for j in range(0, 64):
            s_0 = ((S0 >> j) & 0x1) << 4
            s_1 = ((S1 >> j) & 0x1) << 3
            s_2 = ((S2 >> j) & 0x1) << 2
            s_3 = ((S3 >> j) & 0x1) << 1
            s_4 = (S4 >> j) & 0x1
            s_i = s_0 + s_1 + s_2 + s_3 + s_4
            sbox_s_i = Sbox[s_i]
            sbox_s_0 = ((sbox_s_i >> 4) & 0x1) << j
            sbox_s_1 = ((sbox_s_i >> 3) & 0x1) << j
            sbox_s_2 = ((sbox_s_i >> 2) & 0x1) << j
            sbox_s_3 = ((sbox_s_i >> 1) & 0x1) << j
            sbox_s_4 = ((sbox_s_i >> 0) & 0x1) << j
            new_S0 = new_S0 + sbox_s_0
            new_S1 = new_S1 + sbox_s_1
            new_S2 = new_S2 + sbox_s_2
            new_S3 = new_S3 + sbox_s_3
            new_S4 = new_S4 + sbox_s_4

        self.state_array[0] = new_S0
        self.state_array[1] = new_S1
        self.state_array[2] = new_S2
        self.state_array[3] = new_S3
        self.state_array[4] = new_S4

        self.print_state()

    def linear_diffusion_layer(self):
        print("linear_diffusion_layer")
        self.state_array[0] = (
            self.state_array[0]
            ^ self.ror(64, self.state_array[0], 19)
            ^ self.ror(64, self.state_array[0], 28)
        )
        self.state_array[1] = (
            self.state_array[1]
            ^ self.ror(64, self.state_array[1], 61)
            ^ self.ror(64, self.state_array[1], 39)
        )
        self.state_array[2] = (
            self.state_array[2]
            ^ self.ror(64, self.state_array[2], 1)
            ^ self.ror(64, self.state_array[2], 6)
        )
        self.state_array[3] = (
            self.state_array[3]
            ^ self.ror(64, self.state_array[3], 10)
            ^ self.ror(64, self.state_array[3], 17)
        )
        self.state_array[4] = (
            self.state_array[4]
            ^ self.ror(64, self.state_array[4], 7)
            ^ self.ror(64, self.state_array[4], 41)
        )

        self.print_state()

    def print_constants(self):
        for i in range(0, 12):
            print(f"assign constanst[{i}] = 8'h{hex(Const[i])};")

    def print_sbox(self):
        for i in range(0, 32):
            print(f"assign sbox[{i}] = 8'h{hex(Sbox[i])};")


if __name__ == "__main__":
    if sys.argv[1].startswith("0x"):
        plaintext = int(sys.argv[1][2:], 16)  # 0x6173636F6E
    else:
        plaintex = int(sys.argv[1])

    if sys.argv[2].startswith("0x"):
        key = int(sys.argv[2][2:], 16)  # 0x6173636F6E
    else:
        key = int(sys.argv[2])

    if sys.argv[3].startswith("0x"):
        nonce = int(sys.argv[3][2:], 16)  # 0x6173636F6E
    else:
        nonce = int(sys.argv[3])

    if sys.argv[4].startswith("0x"):
        add_data = int(sys.argv[4][2:], 16)  # 0x6173636F6E
    else:
        add_data = int(sys.argv[4])
    # key = int(sys.argv[2])  # 0x54B6A187FB0A1C64925C66F205FBA5BF
    # nonce = int(sys.argv[3])  # 0xC7B7C0CECF7DE4C7A11453474216B1A3
    # add_data = int(sys.argv[4])  # 0x4153434F4E
    ascon = ASCON_AEAD(key, nonce)
    len_plaintext_bits = int(sys.argv[5])  # 40
    ciphertext, tag = ascon.encrypt(plaintext, add_data, len_plaintext_bits)
    print(hex(ciphertext))
    print(hex(tag))
    # print(hex(ciphertext[0]))
    # print(hex(tag[0]))
    # print(hex(tag[1]))
    # ascon.print_constants()
    # ascon.print_sbox()
