#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : ascon_permutation_test.py
# Author            : German C.Quiveu <germancq@dte.us.es>
# Date              : 08.10.2025
# Last Modified Date: 08.10.2025
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


def setup_dut(dut, total_rounds, state_ascon):
    cocotb.start_soon(Clock(dut.clk, CLK_PERIOD, unit="ns").start())
    dut.rst.value = 0
    dut.start.value = 0
    dut.total_rounds.value = total_rounds
    for i in range(0, 5):
        dut.state_ascon_dout[i].value = state_ascon[i]


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

    assert dut.counter_rounds_dout.value == 0, f"ERROR IDLE in counter"


async def permutation_loop_test(dut, ascon_sw):
    calculated_state = [0, 0, 0, 0, 0]

    dut.rst.value = 0
    await n_cycles_clock(dut, 1)
    assert int(dut.current_state.value) == int(
        dut.IDLE.value
    ), f"ERROR STATE IN RST, STATE={int(dut.current_state.value)}"

    dut.start.value = 1

    i = 0
    while True:

        await n_cycles_clock(dut, 1)

        ascon_sw.constant_addition_layer(int(dut.total_rounds.value), i)

        assert int(dut.current_state.value) == int(
            dut.CTE_LAYER.value
        ), f"ERROR STATE IN CTE_LAYER, STATE={int(dut.current_state.value)}"

        assert dut.state_ascon_w[2].value == 1, f"ERROR in CTE_LAYER Write signal"

        assert dut.state_ascon_w[0].value == 0, f"ERROR in CTE_LAYER Write signal"
        assert dut.state_ascon_w[1].value == 0, f"ERROR in CTE_LAYER Write signal"
        assert dut.state_ascon_w[3].value == 0, f"ERROR in CTE_LAYER Write signal"
        assert dut.state_ascon_w[4].value == 0, f"ERROR in CTE_LAYER Write signal"

        calculated_state[2] = dut.state_ascon_din[2].value

        assert (
            dut.state_ascon_din[2].value == ascon_sw.state_array[2]
        ), f"ERROR in CTE_LAYER, expected {hex(ascon_sw.state_array[2])}, calculated = {hex(dut.state_ascon_din[2].value)}"

        for j in range(0, 5):
            dut.state_ascon_dout[j].value = ascon_sw.state_array[j]

        await n_cycles_clock(dut, 1)

        ascon_sw.substitution_layer()

        assert int(dut.current_state.value) == int(
            dut.SUBS_LAYER.value
        ), f"ERROR STATE IN SUBS_LAYER, STATE={int(dut.current_state.value)}"

        for j in range(0, 5):
            assert (
                dut.state_ascon_w[j].value == 1
            ), f"ERROR in SUBS_LAYER Write signal {j}"

        for j in range(0, 5):
            assert (
                dut.state_ascon_din[j].value == ascon_sw.state_array[j]
            ), f"ERROR in SUBS_LAYER, expected {hex(ascon_sw.state_array[j])}, calculated = {hex(dut.state_ascon_din[j].value)}"

        for j in range(0, 5):
            calculated_state[j] = dut.state_ascon_din[j].value

        for j in range(0, 5):
            dut.state_ascon_dout[j].value = ascon_sw.state_array[j]

        await n_cycles_clock(dut, 1)

        ascon_sw.linear_diffusion_layer()

        assert int(dut.current_state.value) == int(
            dut.DIFF_LAYER.value
        ), f"ERROR STATE IN DIFF_LAYER, STATE={int(dut.current_state.value)}"

        for j in range(0, 5):
            assert (
                dut.state_ascon_w[j].value == 1
            ), f"ERROR in DIFF_LAYER Write signal {j}"

        for j in range(0, 5):
            assert (
                dut.state_ascon_din[j].value == ascon_sw.state_array[j]
            ), f"ERROR in DIFF_LAYER, expected {hex(ascon_sw.state_array[j])}, calculated = {hex(dut.state_ascon_din[j].value)}"

        for j in range(0, 5):
            calculated_state[j] = dut.state_ascon_din[j].value

        for j in range(0, 5):
            dut.state_ascon_dout[j].value = ascon_sw.state_array[j]

        i = i + 1

        if dut.counter_rounds_dout.value == dut.total_rounds.value:
            return calculated_state


async def end_state_test(dut, calculated_state, expected_state):
    await n_cycles_clock(dut, 1)
    assert int(dut.current_state.value) == int(
        dut.END_STATE.value
    ), f"ERROR STATE IN END_STATE, STATE={int(dut.current_state.value)}"

    assert dut.end_signal.value == 1, f"ERROR end_signal"

    for i in range(0, 5):
        assert (
            calculated_state[i] == expected_state[i]
        ), f"ERROR in state {i}, expected={hex(expected_state[i])}, calculated = {hex(calculated_state[i])}"

    await n_cycles_clock(dut, 10)
    assert int(dut.current_state.value) == int(
        dut.END_STATE.value
    ), f"ERROR STATE IN END_STATE, STATE={int(dut.current_state.value)}"


async def n_cycles_clock(dut, n):
    for i in range(0, n):
        await RisingEdge(dut.clk)
        await FallingEdge(dut.clk)


@cocotb.test()
@cocotb.parametrize(index=range(0, 10))
async def test(dut, index=0):

    random.seed(index)

    key = random.getrandbits(128)
    nonce = random.getrandbits(128)
    total_rounds = [6, 8, 12]
    random_number = random.randint(0, 2)
    t_rnds = total_rounds[random_number]
    print(t_rnds)
    print(hex(key))
    print(hex(nonce))

    ascon_sw = ascon_aead.ASCON_AEAD(key, nonce)
    ascon_sw.get_initial_state()

    setup_dut(dut, t_rnds, ascon_sw.state_array)
    await rst_function_test(dut)
    calculated_state = await permutation_loop_test(dut, ascon_sw)

    ascon_sw_2 = ascon_aead.ASCON_AEAD(key, nonce)
    ascon_sw_2.get_initial_state()
    ascon_sw_2.ascon_permutation(t_rnds)

    await end_state_test(dut, calculated_state, ascon_sw_2.state_array)
