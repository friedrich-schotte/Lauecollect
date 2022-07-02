"""
Author: Friedrich Schotte
Date created: 2022-03-30
Date last modified: 2022-04-01
Revision comment: Cleanup: count
"""
__version__ = "1.1"

from cached_function import cached_function
from timing_system_timing_register import Timing_Register


@cached_function()
def timing_system_p0_shift(timing_system):
    return Timing_System_P0_shift(timing_system)


class Timing_System_P0_shift(Timing_Register):
    from monitored_property import monitored_property
    from alias_property import alias_property

    def __init__(self, timing_system):
        Timing_Register.__init__(self, timing_system, "p0_shift", stepsize="bct")

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

    p0d2_count = alias_property("timing_system.p0d2.count")
    p0fd2_count = alias_property("timing_system.p0fd2.count")

    max_count = 1296 - 1


if __name__ == "__main__":
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    from timing_system import timing_system
    domain_name = "BioCARS"
    self = timing_system_p0_shift(timing_system(domain_name))
    print("self.count")
    print("self.value")
