"""
Author: Friedrich Schotte
Date created: 2022-06-27
Date last modified: 2022-06-27
Revision comment: Added: scan_speed, normal_speed
"""
__version__ = "1.1"

import logging

from cached_function import cached_function
from scan_driver import Scan_Driver
from alias_property import alias_property
from db_property import db_property
from numpy import nan


@cached_function()
def motor_scan_driver(domain_name): return Motor_Scan_Driver(domain_name)


class Motor_Scan_Driver(Scan_Driver):
    enabled = alias_property("acquisition.scanning.scan_motor")
    scan_point_divider = alias_property("acquisition.scan_point_dividers.scan_motor")

    scan_relative = db_property("scan_relative", False)
    scan_return = db_property("scan_return", False)

    scan_speed = db_property("scan_speed", nan)
    normal_speed = db_property("scan_speed", nan)


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = "BioCARS"

    self = motor_scan_driver(domain_name)
