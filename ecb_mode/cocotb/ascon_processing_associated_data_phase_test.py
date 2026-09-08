#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : ascon_processing_associated_data_phase_test.py
# Author            : German C.Quiveu <germancq@dte.us.es>
# Date              : 07.09.2026
# Last Modified Date: 07.09.2026
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


def setup_dut(dut, initial_state):
    cocotb.start_soon(Clock(dut.clk, CLK_PERIOD, unit="ns").start())
    dut.rst.value = 0
    dut.start.value = 0
    dut.p_impl_end.value = 0
    dut.feed_block.value = 0
    dut.last_block.value = 0
    dut.block_i.value = 0
    for i in range(0, 5):
        dut.state_dout[i].value = initial_state[i]


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


async def test_associated_data(dut, expected_State, A_array, num_blocks):
    dut.rst.value = 0
    dut.start.value = 1
    S_dut = [0, 0, 0, 0, 0]
    await n_cycles_clock(dut, 1)
    for n in range(0, num_blocks):

        if n == num_blocks - 1:
            dut.last_block.value = 1
        else:
            dut.last_block.value = 0

        assert int(dut.current_state.value) == int(
            dut.XOR_DATA.value
        ), f"ERROR STATE IN TEST, STATE={int(dut.current_state.value)}"

        assert dut.state_w[0].value == 1, f"ERROR Write signal"
        S_dut[0] = int(dut.state_din[0].value)

        if int(dut.rate.value) == 16:
            assert dut.state_w[1].value == 1, f"ERROR Write signal"
            S_dut[1] = int(dut.state_din[1].value)

        await n_cycles_clock(dut, 1)

        assert int(dut.current_state.value) == int(
            dut.ASCON_PERMUTATION_B_0.value
        ), f"ERROR STATE IN TEST, STATE={int(dut.current_state.value)}"

        ascon_permutation(S_dut, int(dut.b.value))

        await n_cycles_clock(dut, 1)

        assert int(dut.current_state.value) == int(
            dut.ASCON_PERMUTATION_B_1.value
        ), f"ERROR STATE IN TEST, STATE={int(dut.current_state.value)}"
        dut.p_impl_end.value = 1

        for i in range(0, 5):
            dut.state_dout[i].value = S_dut[i]

        assert int(dut.current_state.value) == int(
            dut.END_FEED.value
        ), f"ERROR STATE IN TEST, STATE={int(dut.current_state.value)}"

        await n_cycles_clock(dut, 1)

        if dut.last_block.value == 1:
            break
        else:
            assert int(dut.current_state.value) == int(
                dut.END_FEED_0.value
            ), f"ERROR STATE IN TEST, STATE={int(dut.current_state.value)}"

            dut.feed_block.value = 1

            await n_cycles_clock(dut, 1)

            dut.feed_block.value = 0

    assert int(dut.current_state.value) == int(
        dut.FINAL_STEP_0.value
    ), f"ERROR STATE IN TEST, STATE={int(dut.current_state.value)}"

    if int(dut.rate.value == 8):
        assert dut.state_w[0].value == 1, f"ERROR Write signal"
        S_dut[0] = int(dut.state_din[0].value)

    if int(dut.rate.value) == 16:
        assert dut.state_w[1].value == 1, f"ERROR Write signal"
        S_dut[1] = int(dut.state_din[1].value)

    await n_cycles_clock(dut, 1)

    assert int(dut.current_state.value) == int(
        dut.ASCON_PERMUTATION_B_0.value
    ), f"ERROR STATE IN TEST, STATE={int(dut.current_state.value)}"

    ascon_permutation(S_dut, int(dut.b.value))

    await n_cycles_clock(dut, 1)

    assert int(dut.current_state.value) == int(
        dut.ASCON_PERMUTATION_B_1.value
    ), f"ERROR STATE IN TEST, STATE={int(dut.current_state.value)}"
    dut.p_impl_end.value = 1

    for i in range(0, 5):
        dut.state_dout[i].value = S_dut[i]

    await n_cycles_clock(dut, 1)

    assert int(dut.current_state.value) == int(
        dut.FINAL_STEP_1.value
    ), f"ERROR STATE IN TEST, STATE={int(dut.current_state.value)}"

    assert dut.state_w[4].value == 1, f"ERROR Write signal"
    S_dut[4] = int(dut.state_din[4].value)

    await n_cycles_clock(dut, 1)

    assert int(dut.current_state.value) == int(
        dut.END_STATE.value
    ), f"ERROR STATE IN TEST, STATE={int(dut.current_state.value)}"

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

    key = random.getrandbits(128)
    nonce = random.getrandbits(128)

    n = random.randint(1, 3)
    A_array = [0] * n
    A_value = 0
    for i in range(0, n):
        A_data = random.getrandbits(int(dut.rate.value) * 8)
        A_array[i] = A_data
        A_value = A_value + (A_data << (int(dut.rate.value)) * 8)

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

    for k in range(0, 5):
        S[k] = S_init[k]

    expected_result = ascon_process_associated_data(
        S,
        int(dut.b.value),
        int(dut.rate.value),
        A_value.to_bytes((n * int(dut.rate.value)), "little"),
    )

    setup_dut(dut, S_init)
    await rst_function_test(dut)
    await test_associated_data(dut, S, A_array, n)
