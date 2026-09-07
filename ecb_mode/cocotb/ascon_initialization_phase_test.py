#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : ascon_initialization_phase.py
# Author            : German C.Quiveu <germancq@dte.us.es>
# Date              : 07.09.2026
# Last Modified Date: 07.09.2026
# Last Modified By  : German C.Quiveu <germancq@dte.us.es>

import os
import random
import sys

import cocotb
import numpy as np
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer

from ascon import *

CLK_PERIOD = 20


def setup_dut(dut, key, nonce):
    cocotb.start_soon(Clock(dut.clk, CLK_PERIOD, unit="ns").start())
    dut.rst.value = 0
    dut.start.value = 0
    dut.key.value = key
    dut.nonce.value = nonce
    dut.p_impl_end.value = 0
    for i in range(0, 6):
        dut.state_dout[i].value = 0


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


async def test_initialization(dut, expected_State):
    dut.rst.value = 0
    dut.start.value = 1
    S_dut = [0, 0, 0, 0, 0]
    await RisingEdge(dut.clk)
    for i in range(0, 6):
        assert dut.state_w[i].value == 1, f"ERROR Write signal in IDLE"
        S_dut[i] = dut.state_din[i].value
    await FallingEdge(dut.clk)
    assert int(dut.current_state.value) == int(
        dut.ASCON_PERMUTATION_A_0.value
    ), f"ERROR STATE IN TEST, STATE={int(dut.current_state.value)}"
    ascon_permutation(S_dut, dut.a.value)
    await n_cycles_clock(dut, 1)
    assert int(dut.current_state.value) == int(
        dut.ASCON_PERMUTATION_A_1.value
    ), f"ERROR STATE IN TEST, STATE={int(dut.current_state.value)}"
    dut.p_impl_end.value = 1

    for i in range(0, 6):
        dut.state_dout[i].value = S_dut[i]

    await n_cycles_clock(dut, 1)
    assert int(dut.current_state.value) == int(
        dut.XOR_KEY.value
    ), f"ERROR STATE IN TEST, STATE={int(dut.current_state.value)}"

    S_dut[3] = dut.state_din[3].value
    S_dut[4] = dut.state_din[4].value

    await n_cycles_clock(dut, 1)

    assert int(dut.current_state.value) == int(
        dut.END_STATE.value
    ), f"ERROR STATE IN TEST, STATE={int(dut.current_state.value)}"

    assert dut.end_signal.value == 1, f"ERROR in End_signal"

    for i in range(0, 6):
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
    nonce = random.getrandbits(128)

    S = [0, 0, 0, 0, 0]
    expected_result = ascon_initialize(
        S,
        dut.k.value,
        dut.rate.value,
        dut.a.value,
        dut.b.value,
        dut.version.value,
        key,
        nonce,
    )

    setup_dut(dut, key, nonce)
    await rst_function_test(dut)
    await test_initialization(dut, S)
