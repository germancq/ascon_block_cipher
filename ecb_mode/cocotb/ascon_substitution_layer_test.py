#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : ascon_substitution_layer_test.py
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

    for i in range(0, 5):
        dut.state_ascon_dout[i].value = ascon_sw.state_array[i]

    await Timer(10, units="ns")

    for i in range(0, 5):
        assert (
            dut.state_ascon_dout[i].value == ascon_sw.state_array[i]
        ), f"ERROR DOUT en state{i}, expected = {hex(ascon_sw.state_array[i])}, calculated = {hex(dut.state_ascon_dout[i].value)}"

    ascon_sw.substitution_layer()

    await Timer(10, units="ns")

    for i in range(0, 5):
        assert (
            dut.state_ascon_din[i].value == ascon_sw.state_array[i]
        ), f"ERROR en state{i}, expected = {hex(ascon_sw.state_array[i])}, calculated = {hex(dut.state_ascon_din[i].value)}"
