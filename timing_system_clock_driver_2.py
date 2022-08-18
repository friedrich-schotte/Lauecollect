"""
Author: Friedrich Schotte
Date created: 2022-07-29
Date last modified: 2022-07-29
Revision comment:
"""
__version__ = "2.0"

import logging

from alias_property import alias_property
from cached_function import cached_function
from db_property import db_property
from monitored_property import monitored_property


@cached_function()
def timing_system_clock_driver(timing_system):
    return Timing_System_Clock_Driver(timing_system)


class Timing_System_Clock_Driver:
    def __init__(self, timing_system):
        self.timing_system = timing_system

    def __repr__(self):
        return f"{self.timing_system}.clock"

    @property
    def class_name(self):
        return type(self).__name__.lower()

    @property
    def db_name(self):
        return f"{self.timing_system.db_name}"

    @monitored_property
    def clock_period(self, clk_src_count, clock_period_internal, clock_period_external):
        """Clock period in s (ca. 2.8 ns)"""
        if clk_src_count == 29:
            return clock_period_internal
        else:
            return clock_period_external

    @clock_period.setter
    def clock_period(self, value):
        if self.clk_src_count == 29:
            self.clock_period_internal = value
        else:
            self.clock_period_external = value

    clk_src_count = alias_property("registers.clk_src.count")

    clock_period_external = db_property("clock_period_external", 1 / 351933984.0)
    clock_period_internal = db_property("clock_period_internal", 1 / 350000000.0)

    @monitored_property
    def bct(self, clk_on_count, clock_period, clock_multiplier, clock_divider):
        """Bunch clock period in s (ca. 2.8 ns)"""
        if clk_on_count == 1:
            T = clock_period / clock_multiplier * clock_divider
        else:
            T = clock_period
        return T

    @bct.setter
    def bct(self, value):
        if self.clk_on_count == 0:
            self.clock_period = value
        else:
            self.clock_period = value * self.clock_multiplier / self.clock_divider

    registers = alias_property("timing_system.registers")

    clk_on_count = alias_property("registers.clk_on.count")

    @monitored_property
    def clock_divider(self, clk_div_count):
        """Clock scale factor"""
        value = clk_div_count + 1
        return value

    @clock_divider.setter
    def clock_divider(self, value):
        from numpy import rint

        value = int(rint(value))
        if 1 <= value <= 32:
            self.clk_div_count = value - 1
        else:
            logging.warning("%r must be in range 1 to 32.")

    clk_div_count = alias_property("registers.clk_div.count")

    @monitored_property
    def clock_multiplier(self, clk_mul_count):
        value = (clk_mul_count + 1) / 2
        return value

    @clock_multiplier.setter
    def clock_multiplier(self, value):
        from numpy import rint

        value = int(rint(value))
        if 1 <= value <= 32:
            self.clk_mul_count = 2 * value - 1
        else:
            logging.warning("%r must be in range 1 to 32.")

    clk_mul_count = alias_property("registers.clk_mul.count")

    @monitored_property
    def P0t(self, hsct, p0_div_1kHz_count):
        """Single-bunch clock period (ca. 3.6us)"""
        from numpy import nan

        try:
            value = hsct / p0_div_1kHz_count
        except ZeroDivisionError:
            value = nan
        return value

    @P0t.setter
    def P0t(self, value):
        from numpy import rint

        try:
            self.p0_div_1kHz_count = rint(self.hsct / value)
        except ZeroDivisionError:
            pass

    @monitored_property
    def p0_div_1kHz_count(self, registers_p0_div_1kHz_count):
        from numpy import isnan
        if not isnan(registers_p0_div_1kHz_count):
            count = registers_p0_div_1kHz_count
        else:
            count = self.default_p0_div_1kHz_count
            logging.info(f"p0_div_1kHz_count: Defaulting to {count}")
        return count

    @p0_div_1kHz_count.setter
    def p0_div_1kHz_count(self, count):
        self.registers_p0_div_1kHz_count = count

    default_p0_div_1kHz_count = 275

    registers_p0_div_1kHz_count = alias_property("registers.p0_div_1kHz.count")

    @monitored_property
    def hsct(self, bct, clk_88Hz_div_1kHz_count):
        """High-speed chopper rotation period (ca. 1 ms)"""
        return bct * 4 * clk_88Hz_div_1kHz_count

    @hsct.setter
    def hsct(self, value):
        from numpy import rint

        try:
            self.clk_88Hz_div_1kHz_count = rint(value / (self.bct * 4))
        except ZeroDivisionError:
            pass

    @monitored_property
    def clk_88Hz_div_1kHz_count(self, registers_clk_88Hz_div_1kHz_count):
        from numpy import isnan
        if not isnan(registers_clk_88Hz_div_1kHz_count):
            count = registers_clk_88Hz_div_1kHz_count
        else:
            count = self.default_clk_88Hz_div_1kHz_count
            logging.info(f"clk_88Hz_div_1kHz_count: Defaulting to {count}")
        return count

    @clk_88Hz_div_1kHz_count.setter
    def clk_88Hz_div_1kHz_count(self, count):
        self.registers_clk_88Hz_div_1kHz_count = count

    default_clk_88Hz_div_1kHz_count = 89100

    registers_clk_88Hz_div_1kHz_count = alias_property("registers.clk_88Hz_div_1kHz.count")

    @monitored_property
    def hlct(self, hsct, hlc_div):
        """X-ray pulse repetition period.
        Selected by the heatload chopper.
        Depends on the number of slots in the X-ray beam path:
        period = hlct / 12 * number of slots
        (ca 12 ms with one slot) Number of slots: 1,4,12"""
        return hsct * hlc_div

    @hlct.setter
    def hlct(self, value):
        from numpy import rint

        try:
            self.hlc_div = rint(value / self.hsct)
        except ZeroDivisionError:
            pass

    hlc_div = db_property("hlc_div", 12)

    @monitored_property
    def hlc_nslots(self, hlc_div):
        """Number of slots of the heatload chopper in the X-ray beam"""
        from numpy import rint, nan

        try:
            nslots = rint(12.0 / hlc_div)
        except ZeroDivisionError:
            nslots = nan
        return nslots

    @hlc_nslots.setter
    def hlc_nslots(self, nslots):
        from numpy import rint

        try:
            self.hlc_div = rint(12.0 / nslots)
        except ZeroDivisionError:
            pass

    @monitored_property
    def nslt(self, hsct, nsl_div):
        """ns laser flash lamp period (ca. 100 ms)"""
        return hsct * nsl_div

    @nslt.setter
    def nslt(self, value):
        from numpy import rint
        self.nsl_div = rint(value / self.hsct)

    nsl_div = db_property("nsl_div", 48)

    clk_shift_stepsize = db_property("clk_shift_stepsize", 8.594e-12)

    phase_matching_period = db_property("phase_matching_period", 1)


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    name = "BioCARS"
    # name = "LaserLab"

    from timing_system_driver_9 import timing_system_driver

    timing_system = timing_system_driver(name)
    self = timing_system_clock_driver(timing_system)
