#!/usr/bin/env python
import logging
logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s")
from Ensemble_registers import ensemble

x = ensemble.integer_registers
x[-1] += -1; ensemble.integer_registers = x

y = ensemble.floating_point_registers
y[-1] += 0.1; ensemble.floating_point_registers = y
