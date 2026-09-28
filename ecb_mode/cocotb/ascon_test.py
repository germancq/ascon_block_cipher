#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : ascon_test.py
# Author            : German C.Quiveu <germancq@dte.us.es>
# Date              : 28.09.2026
# Last Modified Date: 28.09.2026
import os
import random
import sys

import numpy as np
from ascon import *

import cocotb
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
    dut, a_data_array, num_blocks_a_data, i_data_array, num_blocks_i_data
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

    dut._log.info("START A_DATA")
    for i in range(0, num_blocks_a_data):
        dut._log.info("cycle a_data = {}".format(i))
        dut.block_i.value = a_data_array[i]
        dut.feed_block.value = 1
        await n_cycles_clock(dut, 1)
        dut.feed_block.value = 0

        if i == num_blocks_a_data - 1:
            dut.last_block.value = 1
            while dut.a_data_end_signal.value == 0:
                await n_cycles_clock(dut, 1)
        else:
            dut.last_block.value = 0
            while dut.feed_complete.value == 0:
                await n_cycles_clock(dut, 1)

    dut._log.info("START I_DATA")
    for i in range(0, num_blocks_i_data):
        dut._log.info("cycle i_data = {}".format(i))
        dut.block_i.value = i_data_array[i]
        dut.feed_block.value = 1
        await n_cycles_clock(dut, 1)
        dut.feed_block.value = 0

        if i == num_blocks_a_data - 1:
            dut.last_block.value = 1
            while dut.plaintext_end_signal.value == 0:
                await n_cycles_clock(dut, 1)
        else:
            dut.last_block.value = 0
            while dut.feed_complete.value == 0:
                await n_cycles_clock(dut, 1)

        C_array[i] = dut.block_o.value
        dut._log.info("C_array {} = {}".format(i, hex(C_array[i])))

    dut._log.info("START FINALIZATION")
    dut._log.info("plaintext_end_signal = {}".format(
        dut.plaintext_end_signal.value))
    dut._log.info(dut.impl_plaintext_phase.current_state.value)
    dut._log.info("ciphertext_end_signal = {}".format(
        dut.ciphertext_end_signal.value))
    dut._log.info(dut.impl_ciphertext_phase.current_state.value)
    while dut.end_signal.value == 0:
        await n_cycles_clock(dut, 1)
        # dut._log.info(dut.impl_fin_phase.current_state.value)

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

    C = ascon_encrypt(
        key.to_bytes(16, "little"),
        nonce.to_bytes(16, "little"),
        P_value.to_bytes((n * int(dut.rate.value)), "little"),
        A_value.to_bytes((m * int(dut.rate.value)), "little"),
    )

    setup_dut(dut, key, nonce)
    await test_ascon(dut, A_array, m, P_array, n)
    dut._log.info(bytes_to_hex(C))
    # dut._log.info(bytes_to_hex(tag_expected))
