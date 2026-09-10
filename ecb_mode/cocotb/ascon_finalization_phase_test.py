#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : ascon_finalization_phase_test.py
# Author            : German C.Quiveu <germancq@dte.us.es>
# Date              : 10.09.2026
# Last Modified Date: 10.09.2026
# Last Modified By  : German C.Quiveu <germancq@dte.us.es>

import os
import random
import sys

import cocotb
import numpy as np
from ascon import *
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer

CLK_PERIOD = 20


def setup_dut(dut, key, initialState):
    cocotb.start_soon(Clock(dut.clk, CLK_PERIOD, unit="ns").start())
    dut.rst.value = 0
    dut.start.value = 0
    dut.key.value = key
    dut.p_impl_end.value = 0
    for i in range(0, 5):
        dut.state_dout[i].value = initialState[i]


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


async def test_finalization(dut, expected_State):
    dut._log.info("START FINALIZATION PHASE")
    dut.rst.value = 0
    S_dut = [0, 0, 0, 0, 0]

    for i in range(0, 5):
        S_dut[i] = int(dut.state_dout[i].value)

    await n_cycles_clock(dut, 2)

    dut.start.value = 1

    await RisingEdge(dut.clk)
    if int(dut.rate.value) == 8:
        S_dut[1] = int(dut.state_din[1].value)
        S_dut[2] = int(dut.state_din[2].value)
    elif int(dut.rate.value) == 16:
        S_dut[2] = int(dut.state_din[2].value)
        S_dut[3] = int(dut.state_din[3].value)
    await FallingEdge(dut.clk)
    assert int(dut.current_state.value) == int(
        dut.ASCON_PERMUTATION_A_0.value
    ), f"ERROR STATE IN TEST, STATE={int(dut.current_state.value)}"
    ascon_permutation(S_dut, int(dut.a.value))
    await n_cycles_clock(dut, 1)
    assert int(dut.current_state.value) == int(
        dut.ASCON_PERMUTATION_A_1.value
    ), f"ERROR STATE IN TEST, STATE={int(dut.current_state.value)}"
    dut.p_impl_end.value = 1

    for i in range(0, 5):
        dut.state_dout[i].value = S_dut[i]

    await n_cycles_clock(dut, 1)
    assert int(dut.current_state.value) == int(
        dut.XOR_KEY.value
    ), f"ERROR STATE IN TEST, STATE={int(dut.current_state.value)}"

    for i in range(3, 5):
        S_dut[i] = int(dut.state_din[i].value)

    await n_cycles_clock(dut, 1)

    assert int(dut.current_state.value) == int(
        dut.END_STATE.value
    ), f"ERROR STATE IN TEST, STATE={int(dut.current_state.value)}"

    assert dut.end_signal.value == 1, f"ERROR in End_signal"

    dut._log.info("tag is {0}".format(hex(dut.tag.value)))
    for i in range(0, 5):
        assert (
            S_dut[i] == expected_State[i]
        ), f"Error in state {i} expected {hex(expected_State[i])}, calculated={hex(S_dut[i])}"


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
    S = [0, 0, 0, 0, 0]
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

    dut._log.info(hex(P_value))
    dut._log.info(n)

    ascon_process_associated_data(
        S_init,
        int(dut.b.value),
        int(dut.rate.value),
        A_value.to_bytes((m * int(dut.rate.value)), "little"),
    )

    ascon_process_plaintext(
        S_init,
        int(dut.b.value),
        int(dut.rate.value),
        P_value.to_bytes((n * int(dut.rate.value)), "little"),
    )

    for k in range(0, 5):
        S[k] = S_init[k]

    tag_value = ascon_finalize(
        S, int(dut.rate.value), int(dut.a.value), key.to_bytes(16, "little")
    )

    setup_dut(dut, key, S_init)
    await rst_function_test(dut)
    await test_finalization(dut, S)
    dut._log.info(bytes_to_hex(tag_value))
