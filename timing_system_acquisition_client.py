"""
Author: Friedrich Schotte
Date created: 2022-05-01
Date last modified: 2022-06-20
Revision comment: Renamed: sequences_per_scan_point
"""
__version__ = "1.0.1"

from cached_function import cached_function
from PV_record import PV_record
from PV_property import PV_property


@cached_function()
def timing_system_acquisition_client(timing_system, base_name="acquisition"):
    return Timing_System_Acquisition_Client(timing_system, base_name)


class Timing_System_Acquisition_Client(PV_record):
    base_name = "acquisition"

    def __init__(self, timing_system, base_name):
        super().__init__(domain_name=timing_system.name)
        self.timing_system = timing_system
        self.base_name = base_name

    def __repr__(self):
        return f"{self.timing_system}.{self.base_name}"

    @property
    def prefix(self):
        return f'{self.timing_system.prefix}.{self.base_name}'.upper()

    sequences_loading = PV_property(dtype=bool)
    first_scan_point = PV_property(dtype=int)
    last_scan_point = PV_property(dtype=int)
    generating_packets = PV_property(dtype=int)
    xray_images_per_sequence_queue = PV_property(dtype=int)
    sequences_per_scan_point = PV_property(dtype=int)


if __name__ == '__main__':
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = "BioCARS"
    from timing_system_client import timing_system_client

    timing_system = timing_system_client(domain_name)
    self = timing_system_acquisition_client(timing_system, "acquisition")

    print("self.xray_images_per_sequence_queue")
