#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : ascon_constant_addition_layer_test.py
# Author            : German C.Quiveu <germancq@dte.us.es>
# Date              : 07.10.2025
# Last Modified Date: 07.10.2025
# Last Modified By  : German C.Quiveu <germancq@dte.us.es>

import os
import random
import sys

import ascon_aead
import cocotb
import numpy as np
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


@cocotb.test()
@cocotb.parametrize(index=range(0, 10))
async def test(dut, index=0):

    random.seed(index)

    key = random.getrandbits(128)
    nonce = random.getrandbits(128)

    ascon_sw = ascon_aead.ASCON_AEAD(key, nonce)
    ascon_sw.get_initial_state()

    total_rounds = 12

    for i in range(0, total_rounds):

        dut.total_rounds.value = total_rounds
        dut.current_round.value = i
        dut.state_2_dout.value = ascon_sw.state_array[2]

        await Timer(10, units="ns")
        ascon_sw.constant_addition_layer(total_rounds, i)

        assert (
            dut.state_2_din.value == ascon_sw.state_array[2]
        ), f"ERROR in output, expected = {hex(ascon_sw.state_array[2])}, calculated = {hex(dut.state_2_din.value)}"
