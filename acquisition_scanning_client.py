"""
Author: Friedrich Schotte
Date created: 2022-05-07
Date last modified: 2022-06-27
Revision comment: Updated example
"""
__version__ = "1.0.1"

from PV_record import PV_record
from cached_function import cached_function


@cached_function()
def acquisition_scanning_client(timing_system, base_name):
    return Acquisition_Scanning_Client(timing_system, base_name)


class Acquisition_Scanning_Client(PV_record):
    from PV_property import PV_property

    base_name = "scan_point_dividers"

    def __init__(self, parent, base_name):
        super().__init__(domain_name=parent.name)
        self.parent = parent
        self.base_name = base_name

    def __repr__(self):
        return f"{self.parent}.{self.base_name}"

    @property
    def prefix(self):
        return f'{self.parent.prefix}.{self.base_name}'.upper()

    delay = PV_property(default_value=False)
    laser_on = PV_property(default_value=False)
    temperature = PV_property(default_value=False)
    power = PV_property(default_value=False)
    scan_motor = PV_property(default_value=False)
    alio = PV_property(default_value=False)


if __name__ == '__main__':
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = "BioCARS"
    from acquisition_client import acquisition_client

    acquisition = acquisition_client(domain_name)
    self = acquisition_scanning_client(acquisition, "scanning")

    print("self.delay")
