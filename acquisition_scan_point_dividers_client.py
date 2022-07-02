"""
Author: Friedrich Schotte
Date created: 2022-04-11
Date last modified: 2022-06-27
Revision comment: Updated example
"""
__version__ = "1.0.1"

from PV_record import PV_record
from cached_function import cached_function


@cached_function()
def acquisition_scan_point_dividers_client(timing_system, base_name):
    return Acquisition_Scan_Point_Dividers_Client(timing_system, base_name)


class Acquisition_Scan_Point_Dividers_Client(PV_record):
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

    delay = PV_property(default_value=1)
    laser_on = PV_property(default_value=1)
    temperature = PV_property(default_value=1)
    power = PV_property(default_value=1)
    scan_motor = PV_property(default_value=1)
    alio = PV_property(default_value=1)


if __name__ == '__main__':
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = "BioCARS"
    from acquisition_client import acquisition_client

    acquisition = acquisition_client(domain_name)
    self = acquisition_scan_point_dividers_client(acquisition, "scan_point_dividers")

    print("self.delay")
