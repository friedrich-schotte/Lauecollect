#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2014-03-14
Date last modified: 2022-08-17
Revision comment: Added phi_scan
"""
__version__ = "2.16"

from instrumentation_id14 import *

from acquisition import acquisition
from acquisition_driver import acquisition_driver
from acquisition_client import acquisition_client
from diagnostics import diagnostics
from configuration_tables import configuration_tables
from configuration_tables_client import configuration_tables_client
from configuration_tables_driver import configuration_tables_driver
from timing_system import timing_system
from timing_system_driver import timing_system_driver
from timing_system_client import timing_system_client
from channel_archiver_driver import channel_archiver_driver
from channel_archiver import channel_archiver
from sequence_expander import sequence_expander
from camera_controls import camera_controls
from temperature_scan import temperature_scan
from temperature_scan_driver import temperature_scan_driver
from temperature_scan_client import temperature_scan_client
from motor_scan import motor_scan
from motor_scan_driver import motor_scan_driver
from motor_scan_client import motor_scan_client
from temperature_system import temperature_system
from temperature_system_driver import temperature_system_driver
from temperature_system_client import temperature_system_client
from temperature import temperature  # Needed by diagnostics
from power_scan import power_scan
from power_scan_client import power_scan_client
from power_scan_driver import power_scan_driver
from alio_scan import alio_scan
from alio_scan_client import alio_scan_client
from phi_scan import phi_scan
from phi_scan_client import phi_scan_client


# Still needed?
from configuration_tables import configuration_tables as configurations

from domain import domain

BioCARS = domain("BioCARS")
LaserLab = domain("LaserLab")
TestBench = domain("TestBench")
WetLab = domain("WetLab")

if __name__ == "__main__":
    self = domain("BioCARS")
    print('self.timing_system')
    print('self.acquisition')
    print('self.configuration_tables')
    print('self.configuration_tables.method')
