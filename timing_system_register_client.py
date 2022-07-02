"""
Author: Friedrich Schotte
Date created: 2022-03-30
Date last modified: 2022-04-11
Revision comment:
"""
__version__ = "1.0"

from PV_record import PV_record
from cached_function import cached_function


@cached_function()
def timing_system_register_client(registers, base_name):
    return Timing_System_Register_Client(registers, base_name)


class Timing_System_Register_Client(PV_record):
    from PV_property import PV_property
    from numpy import uint32

    base_name = "register"

    def __init__(self, registers, base_name):
        super().__init__(domain_name=registers.name)
        self.registers = registers
        self.base_name = base_name

    def __repr__(self):
        return f"{self.registers}.{self.base_name}"

    @property
    def prefix(self):
        return f'{self.registers.prefix}.{self.base_name}'.upper()

    count = PV_property(dtype=int)
    value = PV_property(dtype=float)
    dial = PV_property(dtype=float)

    min_count = PV_property(dtype=int)
    max_count = PV_property(dtype=int)
    min_value = PV_property(dtype=float)
    max_value = PV_property(dtype=float)
    min_dial = PV_property(dtype=float)
    max_dial = PV_property(dtype=float)

    offset = PV_property(dtype=float)
    stepsize = PV_property(dtype=float)

    description = PV_property(dtype=str)
    address = PV_property(dtype=uint32)
    bit_offset = PV_property(dtype=int)
    bits = PV_property(dtype=int)


if __name__ == '__main__':
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = "BioCARS"
    from timing_system_client import timing_system_client

    timing_system = timing_system_client(domain_name)
    self = timing_system_register_client(timing_system.registers, "image_number")

    print("self.count")
