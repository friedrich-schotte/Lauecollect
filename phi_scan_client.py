"""
Author: Friedrich Schotte
Date created: 2022-08-16
Date last modified: 2022-08-16
Revision comment:
"""
__version__ = "1.1"

import logging

from PV_property import PV_property
from scan_client import Scan_Client
from cached_function import cached_function


@cached_function()
def phi_scan_client(domain_name):
    return Phi_Scan_Client(domain_name)


class Phi_Scan_Client(Scan_Client):
    start = PV_property(dtype=float)
    stop = PV_property(dtype=float)
    step = PV_property(dtype=str)
    offset = PV_property(dtype=str)
    speed = PV_property(dtype=float)


if __name__ == "__main__":  # for debugging
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = "BioCARS"
    self = phi_scan_client(domain_name)

    print("self.start")
    print("self.stop")
    print("self.step")
    print("self.offset")
    print("self.speed")
    print("")
    print("self.ready")
    print("self.formatted_values")
    print("self.formatted_value")
