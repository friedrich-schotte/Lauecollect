"""
Author: Friedrich Schotte
Date created: 2021-11-29
Date last modified: 2022-06-28
Revision comment: Cleanup: Using only standard properties
"""
__version__ = "1.2.2"

import logging
from scan_client import Scan_Client
from cached_function import cached_function
from alias_property import alias_property


@cached_function()
def temperature_scan_client(domain_name):
    return Temperature_Scan_Client(domain_name)


class Temperature_Scan_Client(Scan_Client):
    pass


if __name__ == "__main__":  # for debugging
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = "BioCARS"
    self = temperature_scan_client(domain_name)

    print("self.values_string")
