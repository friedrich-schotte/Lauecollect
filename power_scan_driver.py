"""
Author: Friedrich Schotte
Date created: 2018-10-22
Date last modified: 2022-07-14
Revision comment: Using format_string
"""
__version__ = "3.2.4"

import logging

from alias_property import alias_property
from db_property import db_property
from scan_driver import Scan_Driver
from cached_function import cached_function


@cached_function()
def power_scan_driver(domain_name):
    return Power_Scan_Driver(domain_name)


class Power_Scan_Driver(Scan_Driver):
    enabled = alias_property("acquisition.scanning.power")
    scan_point_divider = alias_property("acquisition.scan_point_dividers.power")

    motor_name = db_property("motor_name", "trans2")

    format_string = db_property("format_string", "%.4f")


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = "BioCARS"

    self = Power_Scan_Driver(domain_name)
