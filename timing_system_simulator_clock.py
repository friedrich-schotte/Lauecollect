#!/usr/bin/env python
"""
FPGA Timing System Simulator

Author: Friedrich Schotte
Date created: 2021-08-30
Date last modified: 2021-08-30
Revision comment:
"""
__version__ = "1.0"

from logging import warning

from cached_function import cached_function


@cached_function()
def timing_system_simulator_clock(name):
    return Timing_System_Simulator_Clock(name)


class Timing_System_Simulator_Clock:
    from monitored_property import monitored_property
    from monitored_value_property import monitored_value_property
    from timing_system_simulator_register_count_property import register_count_property

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__.lower(), self.name)

    @property
    def timing_system(self):
        from timing_system_simulator import timing_system_simulator
        return timing_system_simulator(self.name)

    @property
    def registers(self):
        return self.timing_system.registers

    clk_88Hz_div_1kHz = register_count_property("clk_88Hz_div_1kHz")
    clk_src = register_count_property("clk_src")
    clk_on = register_count_property("clk_on")
    clk_mul = register_count_property("clk_mul")
    clk_div = register_count_property("clk_div")

    clock_period_external = monitored_value_property(1 / 351933984.0)
    clock_period_internal = monitored_value_property(1 / 350000000.0)

    @monitored_property
    def hsct(self, bct, clk_88Hz_div_1kHz):
        """High-speed chopper rotation period (ca. 1 ms)"""
        return bct * 4 * clk_88Hz_div_1kHz

    @hsct.setter
    def hsct(self, value):
        from numpy import rint

        try:
            self.clk_88Hz_div_1kHz = rint(value / (self.bct * 4))
        except ZeroDivisionError:
            pass

    @monitored_property
    def bct(self, clk_on, clock_period, clock_multiplier, clock_divider):
        """Bunch clock period in s (ca. 2.8 ns)"""
        if clk_on == 0:
            T = clock_period
        else:
            T = clock_period / clock_multiplier * clock_divider
        return T

    @bct.setter
    def bct(self, value):
        if self.clk_on == 0:
            self.clock_period = value
        else:
            self.clock_period = value * self.clock_multiplier / self.clock_divider

    @monitored_property
    def clock_period(self, clk_src, clock_period_internal, clock_period_external):
        """Clock period in s (ca. 2.8 ns)"""
        if clk_src == 29:
            return clock_period_internal
        else:
            return clock_period_external

    @clock_period.setter
    def clock_period(self, value):
        if self.clk_src == 29:
            self.clock_period_internal = value
        else:
            self.clock_period_external = value

    @monitored_property
    def clock_multiplier(self, clk_mul):
        value = (clk_mul + 1) / 2
        return value

    @clock_multiplier.setter
    def clock_multiplier(self, value):
        from numpy import rint

        value = int(rint(value))
        if 1 <= value <= 32:
            self.clk_mul = 2 * value - 1
        else:
            warning("%r must be in range 1 to 32.")

    @monitored_property
    def clock_divider(self, clk_div):
        """Clock scale factor"""
        value = clk_div + 1
        return value

    @clock_divider.setter
    def clock_divider(self, value):
        from numpy import rint

        value = int(rint(value))
        if 1 <= value <= 32:
            self.clk_div = value - 1
        else:
            warning("%r must be in range 1 to 32.")


if __name__ == "__main__":  # for testing
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    name = "BioCARS"
    # name = "LaserLab"

    self = timing_system_simulator_clock(name)
    print(f"self = {self}")

    # print(f"self.bct = {self.bct}")
