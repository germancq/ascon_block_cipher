#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : ascon_encrypt_test.py
# Author            : German C.Quiveu <germancq@dte.us.es>
# Date      ,       : 21.10.2025
# Last Modified Date: 21.10.2025
# Last Modified By  : German C.Quiveu <germancq@dte.us.es>

import os
import random
import sys

import ascon_aead
import cocotb
import numpy as np
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer

CLK_PERIOD = 20


def setup_dut(dut, key, nonce, plaintext, a_data):
    cocotb.start_soon(Clock(dut.clk, CLK_PERIOD, unit="ns").start())
    dut.rst.value = 0
    dut.start.value = 0
    dut.key.value = key
    dut.nonce.value = nonce
    dut.plaintext.value = plaintext
    dut.a_data.value = a_data


async def rst_function_test(dut):
    dut.rst.value = 1
    await n_cycles_clock(dut, 1)
    assert int(dut.current_state.value) == int(
        dut.IDLE.value
    ), f"ERROR STATE IN RST, STATE={int(dut.current_state.value)}"
    await n_cycles_clock(dut, 10)
    assert int(dut.current_state.value) == int(
        dut.IDLE.value
    ), f"ERROR STATE IN RST, STATE={int(dut.current_state.value)}"


async def initial_state_test(dut, ascon_sw):
    dut._log.info("initial_state_test")
    dut.rst.value = 0
    await n_cycles_clock(dut, 5)
    assert int(dut.current_state.value) == int(
        dut.IDLE.value
    ), f"ERROR STATE IN RST, STATE={int(dut.current_state.value)}"
    dut.start.value = 1
    await n_cycles_clock(dut, 1)
    assert int(dut.current_state.value) == int(
        dut.INITIAL_STATE.value
    ), f"ERROR STATE IN INITIAL_STATE, STATE={int(dut.current_state.value)}"

    await permutation_a_test(dut)

    ascon_sw.get_initial_state()
    ascon_sw.ascon_permutation(dut.a.value)

    check_state(dut, ascon_sw)


async def xor_key_state_test(dut, ascon_sw):
    dut._log.info("xor_key_state_test")
    await n_cycles_clock(dut, 1)
    assert int(dut.current_state.value) == int(
        dut.XOR_KEY.value
    ), f"ERROR STATE IN XOR_KEY, STATE={int(dut.current_state.value)}"

    dut._log.info(hex(ascon_sw.key_0))
    dut._log.info(hex(dut.key_0.value))
    dut._log.info(hex(ascon_sw.key_1))
    dut._log.info(hex(dut.key_1.value))
    ascon_sw.state_array[4] = ascon_sw.state_array[4] ^ ascon_sw.key_0
    ascon_sw.state_array[3] = ascon_sw.state_array[3] ^ ascon_sw.key_1

    await n_cycles_clock(dut, 1)

    check_state(dut, ascon_sw)


async def associated_data_test(dut, ascon_sw):
    dut._log.info("associated_data_test")
    assert int(dut.current_state.value) == int(
        dut.ASSOCIATED_DATA.value
    ), f"ERROR STATE IN ASSOCIATED_DATA, STATE={int(dut.current_state.value)}"

    a_data_endian = ascon_sw.parse(dut.a_data.value, 8)
    a_data_reord = 0
    i = 0
    for a_d in a_data_endian:
        a_data_reord = (a_d << (8 * i)) + a_data_reord
        i = i + 1
    if i < (dut.a_len.value / 8):
        shift = int(dut.a_len.value / 8)
        a_data_reord = a_data_reord << ((shift - i) * 8)

    dut._log.info("aux_var in dut = {0}".format(hex(dut.aux_var.value)))

    associated_data = ascon_sw.pad(
        a_data_reord, ascon_sw.rate, dut.a_len.value)
    associated_data = ascon_sw.parse(associated_data, dut.rate.value * 8)
    len_a_data = len(associated_data)

    dut._log.info(len_a_data)

    # associated_data[len_a_data - 1] = ascon_sw.pad(
    #    associated_data[len_a_data - 1], ascon_sw.rate
    # )

    for i in range(0, len_a_data):
        assert int(dut.current_state.value) == int(
            dut.ASSOCIATED_DATA.value
        ), f"ERROR STATE IN ASSOCIATED_DATA, STATE={int(dut.current_state.value)}"
        dut._log.info("aux_var in dut = {0}".format(hex(dut.aux_var.value)))
        dut._log.info("a_data_reord in dut = {0}".format(
            hex(dut.a_data_reord.value)))
        dut._log.info(
            "generic counter in dut = {0}".format(
                hex(dut.generic_counter_o.value))
        )
        a = associated_data[len_a_data - i - 1]
        dut._log.info("a_data = {0}".format(hex(a)))
        ascon_sw.state_array[0] = ascon_sw.state_array[0] ^ (a & ((2**64) - 1))
        ascon_sw.state_array[0] = ascon_sw.state_array[0] & ((2**64) - 1)
        if ascon_sw.rate == 128:
            ascon_sw.state_array[1] = ascon_sw.state_array[1] ^ (a >> 64)
            ascon_sw.state_array[1] = ascon_sw.state_array[1] & ((2**64) - 1)
        await n_cycles_clock(dut, 1)
        check_state(dut, ascon_sw)
        ascon_sw.print_state()
        ascon_sw.ascon_permutation(dut.b.value)
        await permutation_b_test(dut)
        check_state(dut, ascon_sw)
        await n_cycles_clock(dut, 1)


async def update_state_test(dut, ascon_sw):
    dut._log.info("update state")
    # await n_cycles_clock(dut, 1)
    assert int(dut.current_state.value) == int(
        dut.UPDATE_STATE.value
    ), f"ERROR STATE IN UPDATE_STATE, STATE={int(dut.current_state.value)}"

    ascon_sw.state_array[4] = ascon_sw.state_array[4] ^ (1 << 63)
    ascon_sw.state_array[4] = ascon_sw.state_array[4] & ((2**64) - 1)
    ascon_sw.print_state()

    await n_cycles_clock(dut, 1)
    check_state(dut, ascon_sw)


async def plaintext_state_test(dut, ascon_sw):
    dut._log.info("plaintext state")
    plaintext_endian = ascon_sw.parse(dut.plaintext.value, 8)
    plaintext_reord = 0
    i = 0
    for p_d in plaintext_endian:
        print(hex(p_d))
        plaintext_reord = (p_d << (8 * i)) + plaintext_reord
        i = i + 1

    if i < (dut.plaintext_len.value / 8):
        shift = int(dut.plaintext_len.value / 8)
        plaintext_reord = plaintext_reord << ((shift - i) * 8)

    plaintext_reord = ascon_sw.pad(
        plaintext_reord, ascon_sw.rate, dut.plaintext_len.value
    )
    print("plaintext padded and reord data = {}".format(hex(plaintext_reord)))

    plaintext_data = ascon_sw.parse(plaintext_reord, ascon_sw.rate)
    plaintext_data_parse = []
    len_plaintext_data = len(plaintext_data)

    for i in range(0, len_plaintext_data):
        plaintext_data_parse.append(0)

    for i in range(0, len_plaintext_data):
        plaintext_data_parse[i] = plaintext_data[len_plaintext_data - i - 1]

    len_plaintext_data_parse = len(plaintext_data_parse)
    print("len plaintext data = {}".format(len_plaintext_data))
    bits_for_last_block = int(
        dut.plaintext_len.value - (ascon_sw.rate * (len_plaintext_data - 1))
    )
    # bits_for_last_block = int(
    #    math.ceil(math.log2(plaintext_data[len_plaintext_data - 1]))
    # )
    for i in range(0, len(plaintext_data_parse)):
        print("plaintext_data_parse_{0} = {1}".format(
            i, hex(plaintext_data_parse[i])))

    for i in range(0, len(plaintext_data_parse)):
        print("plaintext_data_parse_{0} = {1}".format(
            i, hex(plaintext_data_parse[i])))

    print(bits_for_last_block)
    ciphertext_arr = []
    for i in range(0, len_plaintext_data_parse):
        dut._log.info("plaintext_reord = {}".format(
            hex(dut.plaintext_reord.value)))
        dut._log.info("aux_var is {}".format(hex(dut.aux_var.value)))
        dut._log.info("state_0 is {}".format(
            hex(dut.state_ascon_dout[0].value)))
        dut._log.info("counter is {}".format(hex(dut.generic_counter_o.value)))
        if i < len_plaintext_data_parse - 1:
            print(
                "final block plaintext{} is = {}".format(
                    i, hex(plaintext_data_parse[i])
                )
            )
            print("state_0 is = {}".format(hex(ascon_sw.state_array[0])))
            ascon_sw.state_array[0] = ascon_sw.state_array[0] ^ (
                plaintext_data_parse[i] & ((2**64) - 1)
            )
            ascon_sw.state_array[0] = ascon_sw.state_array[0] & ((2**64) - 1)
            if ascon_sw.rate == 128:
                ascon_sw.state_array[1] = ascon_sw.state_array[1] ^ (
                    plaintext_data_parse[i] >> 64
                )
                ascon_sw.state_array[1] = ascon_sw.state_array[1] & (
                    (2**64) - 1)
                ciphertext_arr.insert(
                    i, ((ascon_sw.state_array[1] <<
                        64) + ascon_sw.state_array[0])
                )
            else:
                ciphertext_arr.insert(i, ascon_sw.state_array[0])

            ascon_sw.ascon_permutation(ascon_sw.b)
            ascon_sw.print_state()
            await permutation_b_test(dut)
            check_state(dut, ascon_sw)
            await n_cycles_clock(dut, 1)
        else:
            print("plaintext{} is = {}".format(
                i, hex(plaintext_data_parse[i])))
            print("state_0 is = {}".format(hex(ascon_sw.state_array[0])))
            ascon_sw.state_array[0] = ascon_sw.state_array[0] ^ (
                plaintext_data_parse[i] & ((2**64) - 1)
            )
            ascon_sw.state_array[0] = ascon_sw.state_array[0] & ((2**64) - 1)

            if ascon_sw.rate == 128:
                ascon_sw.state_array[1] = ascon_sw.state_array[1] ^ (
                    plaintext_data_parse[i] >> 64
                )
                ascon_sw.state_array[1] = ascon_sw.state_array[1] & (
                    (2**64) - 1)
                print("xor is {}".format(hex(ascon_sw.state_array[0])))
                print("bits_for_last_block is {}".format(bits_for_last_block))

                c_aux = (
                    (ascon_sw.state_array[1] << 64) + (ascon_sw.state_array[0])
                ) & ((2**bits_for_last_block) - 1)
                print("c_aux is {}".format(hex(c_aux)))
                ciphertext_arr.insert(i, c_aux)
            else:
                print("xor is {}".format(hex(ascon_sw.state_array[0])))
                c_aux = ascon_sw.state_array[0] & (
                    (2**bits_for_last_block) - 1)
                print("c_aux is {}".format(hex(c_aux)))
                ciphertext_arr.insert(i, c_aux)

    ascon_sw.print_state()
    i = 0
    for c_i in ciphertext_arr:
        dut._log.info("ciphertext_arr c_{} = {}".format(i, hex(c_i)))
        i = i + 1

    assert int(dut.current_state.value) == int(
        dut.PLAINTEXT_BLOCK.value
    ), f"ERROR STATE IN PLAINTEXT_BLOCK, STATE={int(dut.current_state.value)}"

    await n_cycles_clock(dut, 1)
    check_state(dut, ascon_sw)


async def tag_state_test(dut, ascon_sw):
    assert int(dut.current_state.value) == int(
        dut.TAG_DATA_0.value
    ), f"ERROR STATE IN TAG_DATA_0, STATE={int(dut.current_state.value)}"

    ascon_sw.state_array[2] = ascon_sw.state_array[2] ^ ascon_sw.key_1
    ascon_sw.state_array[3] = ascon_sw.state_array[3] ^ ascon_sw.key_0

    ascon_sw.print_state()

    await n_cycles_clock(dut, 1)
    check_state(dut, ascon_sw)

    ascon_sw.ascon_permutation(dut.a.value)

    ascon_sw.print_state()

    await permutation_a_test(dut)
    check_state(dut, ascon_sw)

    await n_cycles_clock(dut, 1)

    ascon_sw.state_array[3] = ascon_sw.state_array[3] ^ ascon_sw.key_1
    ascon_sw.state_array[4] = ascon_sw.state_array[4] ^ ascon_sw.key_0

    assert int(dut.current_state.value) == int(
        dut.TAG_DATA_1.value
    ), f"ERROR STATE IN TAG_DATA_1, STATE={int(dut.current_state.value)}"

    await n_cycles_clock(dut, 1)

    ascon_sw.print_state()

    check_state(dut, ascon_sw)

    ascon_sw.tag.insert(0, ascon_sw.state_array[3])
    ascon_sw.tag.insert(1, ascon_sw.state_array[4])


async def end_state_test(dut, expected_ciphertext, expected_tag):
    assert int(dut.current_state.value) == int(
        dut.END_STATE.value
    ), f"ERROR STATE IN END_STATE, STATE={int(dut.current_state.value)}"

    assert dut.end_signal.value == 1, f"ERROR end_signal"

    dut._log.info(hex(expected_ciphertext))
    dut._log.info(hex(dut.ciphertext.value))
    dut._log.info(hex(dut.ciphertext_ord.value))
    dut._log.info(hex(expected_tag))
    dut._log.info(hex(dut.tag.value))
    dut._log.info(dut.N_BLOCKS.value)
    for i in range(0, dut.N_BLOCKS.value):
        dut._log.info(hex(dut.ciphertext_non_ord[i].value))

    assert (
        dut.ciphertext.value == expected_ciphertext
    ), f"ERROR in ciphertext, expected = {hex(expected_ciphertext)} calculated = {hex(dut.ciphertext.value)}"

    assert (
        dut.tag.value == expected_tag
    ), f"ERROR in tag, expected = {hex(expected_tag)} calculated = {hex(dut.tag.value)}"


async def permutation_a_test(dut):
    while int(dut.current_state.value) != int(dut.ASCON_PERMUTATION_A_2.value):
        await n_cycles_clock(dut, 1)


async def permutation_b_test(dut):
    while int(dut.current_state.value) != int(dut.ASCON_PERMUTATION_B_2.value):
        await n_cycles_clock(dut, 1)


def check_state(dut, ascon_sw):
    for i in range(0, 5):
        expected_state = ascon_sw.state_array[i] & ((2**64) - 1)
        assert (
            dut.state_ascon_dout[i].value == expected_state
        ), f"ERROR in state {i} on state_test, expected = {hex(expected_state)}, calculated = {hex(dut.state_ascon_dout[i].value)}"


async def n_cycles_clock(dut, n):
    for i in range(0, n):
        await RisingEdge(dut.clk)
        await FallingEdge(dut.clk)


@cocotb.test()
@cocotb.parametrize(index=range(0, 500))
async def test(dut, index=0):

    random.seed(index)

    plaintext = random.getrandbits(dut.plaintext_len.value)
    key = random.getrandbits(dut.k.value)
    nonce = random.getrandbits(128)
    a_data = random.getrandbits(dut.a_len.value)
    # plaintext = 0x6173636F6E
    # key = 0x54B6A187FB0A1C64925C66F205FBA5BF
    # nonce = 0xC7B7C0CECF7DE4C7A11453474216B1A3
    # a_data = 0x4153434F4E

    ascon_sw = ascon_aead.ASCON_AEAD(key, nonce)

    setup_dut(dut, key, nonce, plaintext, a_data)
    await rst_function_test(dut)
    await initial_state_test(dut, ascon_sw)
    await xor_key_state_test(dut, ascon_sw)
    await associated_data_test(dut, ascon_sw)
    await update_state_test(dut, ascon_sw)
    await plaintext_state_test(dut, ascon_sw)
    await tag_state_test(dut, ascon_sw)

    ascon_sw2 = ascon_aead.ASCON_AEAD(key, nonce)
    expected_ciphertext, expected_tag = ascon_sw2.encrypt(
        plaintext, a_data, dut.plaintext_len.value
    )
    await end_state_test(dut, expected_ciphertext, expected_tag)
