#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : ascon_test.py
# Author            : German C.Quiveu <germancq@dte.us.es>
# Date              : 28.09.2026
# Last Modified Date: 28.09.2026
import os
import random
import sys

import cocotb
import numpy as np
from ascon import *
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer

CLK_PERIOD = 20


def setup_dut(dut, key, nonce):
    cocotb.start_soon(Clock(dut.clk, CLK_PERIOD, unit="ns").start())
    dut.rst.value = 0
    dut.start.value = 0
    dut.key.value = key
    dut.nonce.value = nonce
    dut.enc_dec.value = 0
    dut.block_i.value = 0
    dut.feed_block.value = 0
    dut.last_block.value = 0


async def test_ascon(
    dut,
    a_data_array,
    num_blocks_a_data,
    i_data_array,
    num_blocks_i_data,
    S_init,
    S_a_data,
    S_i_data,
    S_fin_data,
):
    C_array = [0] * (num_blocks_i_data)
    dut._log.info("num_blocks_a_data = {}".format(num_blocks_a_data))
    dut._log.info("num_blocks_i_data = {}".format(num_blocks_i_data))

    dut.rst.value = 1
    dut.enc_dec.value = 0
    await n_cycles_clock(dut, 10)
    dut.rst.value = 0
    dut.start.value = 1
    dut._log.info("START INITIALIZATION")
    while dut.init_end_signal.value == 0:
        await n_cycles_clock(dut, 1)

    for i in range(0, 5):
        assert (
            dut.state_ascon_dout.value[i] == S_init[i]
        ), f"Error in state {i} expected {hex(S_init[i])}, calculated={hex(dut.state_ascon_dout.value[i])}"

    dut._log.info("START A_DATA")
    for i in range(0, num_blocks_a_data):
        dut._log.info("cycle a_data = {}".format(i))
        dut.block_i.value = a_data_array[i]
        dut.feed_block.value = 1
        if i == num_blocks_a_data - 1:
            dut._log.info("LAST BLOCK")
            dut.last_block.value = 1
        else:
            dut.last_block.value = 0
        await n_cycles_clock(dut, 1)
        dut.feed_block.value = 0

        if i == num_blocks_a_data - 1:
            dut._log.info("LAST BLOCK 2")
            dut.last_block.value = 1
            while dut.a_data_end_signal.value == 0:
                await n_cycles_clock(dut, 1)
        else:
            dut.last_block.value = 0
            while dut.feed_complete.value == 0:
                await n_cycles_clock(dut, 1)

    for i in range(0, 5):
        assert (
            dut.state_ascon_dout.value[i] == S_a_data[i]
        ), f"Error in state {i} expected {hex(S_a_data[i])}, calculated={hex(dut.state_ascon_dout.value[i])}"

    dut._log.info("START I_DATA")
    for i in range(0, num_blocks_i_data):
        dut._log.info("cycle i_data = {}".format(i))
        dut.block_i.value = i_data_array[i]
        dut.feed_block.value = 1
        if i == num_blocks_i_data - 1:
            dut._log.info("LAST BLOCK")
            dut.last_block.value = 1
        else:
            dut.last_block.value = 0

        await n_cycles_clock(dut, 1)
        dut.feed_block.value = 0

        if i == num_blocks_i_data - 1:
            dut._log.info("LAST BLOCK 2")
            dut.last_block.value = 1
            while dut.plaintext_end_signal.value == 0:
                await n_cycles_clock(dut, 1)
        else:
            dut.last_block.value = 0
            while dut.feed_complete.value == 0:
                await n_cycles_clock(dut, 1)

        C_array[i] = dut.block_o.value
        dut._log.info("C_array {} = {}".format(i, hex(C_array[i])))

    for i in range(0, 5):
        assert (
            dut.state_ascon_dout.value[i] == S_i_data[i]
        ), f"Error in state {i} expected {hex(S_i_data[i])}, calculated={hex(dut.state_ascon_dout.value[i])}"

    dut._log.info("START FINALIZATION")
    dut._log.info("plaintext_end_signal = {}".format(
        dut.plaintext_end_signal.value))
    dut._log.info(
        "plaintext last_block signal = {}".format(
            dut.impl_plaintext_phase.last_block.value
        )
    )
    dut._log.info(dut.impl_plaintext_phase.current_state.value)
    dut._log.info("ciphertext_end_signal = {}".format(
        dut.ciphertext_end_signal.value))
    dut._log.info(dut.impl_ciphertext_phase.current_state.value)
    while dut.end_signal.value == 0:
        await n_cycles_clock(dut, 1)
        # dut._log.info(dut.impl_fin_phase.current_state.value)

    for i in range(0, 5):
        assert (
            dut.state_ascon_dout.value[i] == S_fin_data[i]
        ), f"Error in state {i} expected {hex(S_fin_data[i])}, calculated={hex(dut.state_ascon_dout.value[i])}"

    dut._log.info("tag = {}".format(hex(dut.tag.value)))


async def n_cycles_clock(dut, n):
    for i in range(0, n):
        await RisingEdge(dut.clk)
        await FallingEdge(dut.clk)


@cocotb.test()
@cocotb.parametrize(index=range(0, 10))
async def test(dut, index=0):

    random.seed(index)

    key = random.getrandbits(dut.k.value)
    dut._log.info(hex(key))
    nonce = random.getrandbits(128)
    dut._log.info(hex(nonce))

    m = random.randint(1, 3)
    A_array = [0] * m
    A_value = 0
    for i in range(0, m):
        A_data = random.getrandbits(int(dut.rate.value) * 8)
        A_array[i] = A_data
        A_value = A_value + (A_data << (int(dut.rate.value)) * (i * 8))

    n = random.randint(1, 3)
    P_array = [0] * n
    P_value = 0
    for i in range(0, n):
        P_data = (random.getrandbits(int(dut.rate.value) * 8)) | (
            (1 << (int(dut.rate.value) * 8) - 1)
        )
        P_array[i] = P_data
        P_value = P_value + (P_data << (int(dut.rate.value)) * (i * 8))

    S_init = [0, 0, 0, 0, 0]
    S_a_data = [0, 0, 0, 0, 0]
    S_i_data = [0, 0, 0, 0, 0]
    S_fin_data = [0, 0, 0, 0, 0]
    initial_ascon = ascon_initialize(
        S_init,
        int(128),
        int(dut.rate.value),
        int(dut.a.value),
        int(dut.b.value),
        int(1),
        key.to_bytes(16, "little"),
        nonce.to_bytes(16, "little"),
    )

    for k in range(0, 5):
        S_a_data[k] = S_init[k]
    dut._log.info(hex(P_value))
    dut._log.info(n)

    ascon_process_associated_data(
        S_a_data,
        int(dut.b.value),
        int(dut.rate.value),
        A_value.to_bytes((m * int(dut.rate.value)), "little"),
    )

    for k in range(0, 5):
        S_i_data[k] = S_a_data[k]

    expected_ciphertext = ascon_process_plaintext(
        S_i_data,
        int(dut.b.value),
        int(dut.rate.value),
        P_value.to_bytes((n * int(dut.rate.value)), "little"),
    )

    for k in range(0, 5):
        S_fin_data[k] = S_i_data[k]

    tag_value = ascon_finalize(
        S_fin_data, int(dut.rate.value), int(
            dut.a.value), key.to_bytes(16, "little")
    )

    setup_dut(dut, key, nonce)
    await test_ascon(
        dut, A_array, m, P_array, n, S_init, S_a_data, S_i_data, S_fin_data
    )
    dut._log.info(bytes_to_hex(expected_ciphertext))
    dut._log.info(bytes_to_hex(tag_value))
