"""
Author: Friedrich Schotte
Date created: 2018-10-22
Date last modified: 2022-07-01
Revision comment: Overriding motor_name of super class rather than motor
"""
__version__ = "3.2.3"

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

    def format(self, value):
        return f"{value:.3f}C"


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = "BioCARS"

    self = Temperature_Scan_Driver(domain_name)
