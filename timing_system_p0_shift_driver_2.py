"""
Author: Friedrich Schotte
Date created: 2022-03-30
Date last modified: 2022-08-01
Revision comment:
"""
__version__ = "2.0"

from timing_system_register_driver_2 import Timing_System_Register_Driver
from monitored_property import monitored_property
from alias_property import alias_property
from cached_function import cached_function


@cached_function()
def timing_system_p0_shift_driver(registers):
    return Timing_System_P0_Shift_Driver(registers)


class Timing_System_P0_Shift_Driver(Timing_System_Register_Driver):
    def __init__(self, registers):
        super().__init__(registers=registers, name="p0_shift")

    def __repr__(self):
        return f"{self.registers}.p0_shift"

    stepsize = alias_property("timing_system.clock.bct")

    @monitored_property
    def count(self, p0d2_count, p0fd2_count):
        count = p0d2_count * 4 + (p0fd2_count + 2) % 4
        return count

    @count.setter
    def count(self, count):
        from numpy import isnan, rint
        if not isnan(count):
            count = int(rint(count))
            self.p0d2_count = count / 4
            self.p0fd2_count = (count - 2) % 4

    p0d2_count = alias_property("registers.p0d2.count")
    p0fd2_count = alias_property("registers.p0fd2.count")

    max_count = 1296 - 1


if __name__ == "__main__":
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = "BioCARS"

    from timing_system_driver_9 import timing_system_driver
    timing_system = timing_system_driver(domain_name)
    registers = timing_system.registers
    self = timing_system_p0_shift_driver(registers)
    print("self.count")
    print("self.value")
