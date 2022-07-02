"""
Author: Friedrich Schotte
Date created: 2022-04-11
Date last modified: 2022-04-11
Revision comment:
"""
__version__ = "1.0"

from PV_record import PV_record
from cached_function import cached_function


@cached_function()
def timing_system_variable_client(timing_system, base_name):
    return Timing_System_Variable_Client(timing_system, base_name)


class Timing_System_Variable_Client(PV_record):
    from PV_property import PV_property

    base_name = "variable"

    def __init__(self, timing_system, base_name):
        super().__init__(domain_name=timing_system.name)
        self.timing_system = timing_system
        self.base_name = base_name

    def __repr__(self):
        return f"{self.timing_system}.{self.base_name}"

    @property
    def prefix(self):
        return f'{self.timing_system.prefix}.{self.base_name}'.upper()

    count = PV_property(dtype=int)
    value = PV_property(dtype=float)
    dial = PV_property(dtype=float)

    offset = PV_property(dtype=float)
    stepsize = PV_property(dtype=float)


if __name__ == '__main__':
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = "BioCARS"
    from timing_system_client import timing_system_client

    timing_system = timing_system_client(domain_name)
    self = timing_system_variable_client(timing_system, "delay")

    print("self.value")
