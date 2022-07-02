"""
Author: Friedrich Schotte
Date created: 2022-05-01
Date last modified: 2022-05-01
Revision comment:
"""
__version__ = "1.0"

import logging

from scan_client import Scan_Client
from cached_function import cached_function


@cached_function()
def timing_system_delay_scan_client(domain_name):
    return Timing_System_Delay_Scan_Client(domain_name)


class Timing_System_Delay_Scan_Client(Scan_Client):
    @property
    def base_name(self):
        return "timing_system.delay_scan"


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = "BioCARS"
    self = timing_system_delay_scan_client(domain_name)

    print("self.values_string")
