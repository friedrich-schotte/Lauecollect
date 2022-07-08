"""
Author: Friedrich Schotte
Date created: 2022-06-27
Date last modified: 2022-07-08
Revision comment: Added: scan_speed, normal_speed
"""
__version__ = "1.1"

import logging

from PV_property import PV_property
from scan_client import Scan_Client
from cached_function import cached_function


@cached_function()
def motor_scan_client(domain_name):
    return Motor_Scan_Client(domain_name)


class Motor_Scan_Client(Scan_Client):
    scan_relative = PV_property(dtype=bool)
    scan_return = PV_property(dtype=bool)
    scan_speed = PV_property(dtype=float)
    normal_speed = PV_property(dtype=float)


if __name__ == "__main__":  # for debugging
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = "BioCARS"
    self = motor_scan_client(domain_name)

    print("self.values_string")
