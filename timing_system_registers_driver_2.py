#!/usr/bin/env python
"""
FPGA Timing System Simulator

Author: Friedrich Schotte
Date created: 2022-03-30
Date last modified: 2022-07-29
Revision comment:
"""
__version__ = "2.0"

from logging import warning

from alias_property import alias_property
from cached_function import cached_function
from monitored_property import monitored_property
from monitored_value_property import monitored_value_property


@cached_function()
def timing_system_registers_driver(timing_system):
    return Timing_System_Registers_Driver(timing_system)


class Timing_System_Registers_Driver:
    def __init__(self, timing_system):
        self.timing_system = timing_system
        self.read_configuration()

    def __repr__(self):
        return f"{self.timing_system}.registers"

    @property
    def p0_shift(self):
        from timing_system_p0_shift_driver_2 import timing_system_p0_shift_driver
        return timing_system_p0_shift_driver(self)

    @property
    def class_name(self):
        return type(self).__name__.lower()

    @property
    def db_name(self):
        return f"{self.timing_system.db_name}"

    def __len__(self):
        return len(self.names)

    def __iter__(self):
        for name in self.names:
            yield self.register(name)

    @property
    def prefix(self):
        return f"{self.timing_system.prefix.strip('.')}.registers"

    def load_values(self, filename):
        self.values = open(filename).read()

    def save_values(self, filename):
        open(filename, "w").write(self.values)

    names = []

    def read_configuration(self):
        self.names = []
        # debug("Reading %r" % self.configuration_filename)
        text = open(self.configuration_filename).read()
        for line in text.splitlines():
            fields = line.split("\t")
            try:
                description = fields[0]
            except IndexError:
                description = ""
            try:
                name = fields[1]
            except IndexError:
                name = ""
            try:
                address = int(fields[2], base=16)
            except (IndexError, ValueError):
                address = 0
            try:
                bit_offset = int(fields[3])
            except (IndexError, ValueError):
                bit_offset = 0
            try:
                bits = int(fields[4])
            except (IndexError, ValueError):
                bits = 32
            from timing_system_register_driver_2 import Timing_System_Register_Driver
            register = Timing_System_Register_Driver(self, description, name, address, bit_offset, bits)
            setattr(self, name, register)
            self.names.append(name)

    @property
    def values(self):
        lines = ["#mnemonic\tcount\n"]
        for register in self:
            lines.append("%s\t%r" % (register.name, register.count))
        text = "\n".join(lines)
        return text

    @values.setter
    def values(self, text):
        for line in text.splitlines():
            if not line.startswith("#"):
                fields = line.split()
                try:
                    name = fields[0]
                except IndexError:
                    warning("ignoring line %r" % line)
                    continue
                try:
                    count = int(fields[1])
                except (IndexError, ValueError):
                    warning("ignoring line %r" % line)
                    continue
                self.register(name).count = count

    def register(self, name):
        if name not in self.names:
            from timing_system_register_driver_2 import Timing_System_Register_Driver
            register = Timing_System_Register_Driver(self, name=name)
            setattr(self, name, register)
            self.names.append(name)
        register = getattr(self, name)
        return register

    @property
    def configuration_filename(self):
        return self.timing_system.directory + "/registers.txt"

    psod1_stepsize = alias_property("bct")
    psod1_max_count = monitored_value_property(4)
    psod2_stepsize = alias_property("clk_shift_stepsize")
    psod3_stepsize = alias_property("bct_div2_x5")
    psod3_max_count = monitored_value_property(1)

    p0fd_stepsize = alias_property("bct")
    p0d_stepsize = alias_property("bct_x4")

    p0afd_stepsize = alias_property("bct")
    p0ad_stepsize = alias_property("bct_x4")

    p0fd2_stepsize = alias_property("bct")
    p0d2_stepsize = alias_property("bct_x4")

    hlcnd_stepsize = alias_property("bct_x4")
    hlctd_stepsize = alias_property("bct_x4")
    hlcad_stepsize = alias_property("bct_x4")

    for i in range(0, 24):
        exec(f'ch{i+1}_delay_stepsize = alias_property("bct_div2")')
        exec(f'ch{i+1}_delay_max_count = monitored_value_property(712799)')
        exec(f'ch{i+1}_pulse_stepsize = alias_property("bct_x4")')

    @monitored_property
    def bct_x4(self, bct): return bct*4

    @monitored_property
    def bct_div2(self, bct): return bct/2

    @monitored_property
    def bct_div2_x5(self, bct): return bct*2.5

    bct = alias_property("clock.bct")
    clk_shift_stepsize = alias_property("clock.clk_shift_stepsize")

    clock = alias_property("timing_system.clock")


if __name__ == "__main__":  # for testing
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    name = "BioCARS"
    # name = "LaserLab"

    from timing_system_driver_9 import timing_system_driver

    timing_system = timing_system_driver(name)
    self = timing_system_registers_driver(timing_system)
    print(f"self = {self}")

    filename = self.timing_system.directory + "/register-values.txt"
    print("print(self.values)")
    print(f"self.load_values({filename!r})")
    print(f"self.save_values({filename!r})")
