"""
Author: Friedrich Schotte
Date created: 2022-07-14
Date last modified: 2022-07-14
Revision comment:
"""
__version__ = "1.0"

import logging
from scan_client import Scan_Client
from cached_function import cached_function
from alias_property import alias_property


@cached_function()
def power_scan_client(domain_name):
    return Power_Scan_Client(domain_name)


class Power_Scan_Client(Scan_Client):
    pass


if __name__ == "__main__":  # for debugging
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = "BioCARS"
    self = power_scan_client(domain_name)

    print("self.values_string")
