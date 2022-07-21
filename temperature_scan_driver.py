"""
Author: Friedrich Schotte
Date created: 2018-10-22
Date last modified: 2022-07-14
Revision comment: Using format_string and unit
"""
__version__ = "3.2.4"

import logging

from alias_property import alias_property
from db_property import db_property
from scan_driver import Scan_Driver
from cached_function import cached_function


@cached_function()
def temperature_scan_driver(domain_name):
    return Temperature_Scan_Driver(domain_name)


class Temperature_Scan_Driver(Scan_Driver):
    enabled = alias_property("acquisition.scanning.temperature")
    scan_point_divider = alias_property("acquisition.scan_point_dividers.temperature")

    motor_name = db_property("motor_name", "temperature_system")

    format_string = db_property("format_string", "%.3f")
    unit = db_property("unit", "C")


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = "BioCARS"

    self = Temperature_Scan_Driver(domain_name)
