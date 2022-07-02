#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2014-03-14
Date last modified: 2022-06-29
Revision comment: configurations: Updated comment
"""
__version__ = "2.12.1"

from instrumentation_id14 import *

from acquisition import acquisition
from acquisition_driver import acquisition_driver
from acquisition_client import acquisition_client
from diagnostics import diagnostics
from configuration_tables import configuration_tables
from configuration_tables_client import configuration_tables_client
from configuration_tables_driver import configuration_tables_driver
from configuration import configuration
from timing_system import timing_system
from timing_system_driver import timing_system_driver
from timing_system_client import timing_system_client
from timing_system_sequencer import timing_system_sequencer
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

# Still needed?
from configuration_tables import configuration_tables as configurations

from domain import domain

BioCARS = domain("BioCARS")
LaserLab = domain("LaserLab")
TestBench = domain("TestBench")
WetLab = domain("WetLab")

if __name__ == "__main__":
    print('BioCARS.timing_system')
    print('BioCARS.acquisition')
    print('BioCARS.configuration_tables')
    print('BioCARS.configuration_tables.method')
