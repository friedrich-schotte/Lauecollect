#!/usr/bin/env python
"""Spectra Physics 3930 Lok-to-Clock frequency stabilizer for the Tsunami laser
This is to make the device remote controllable accross the network using
EPICS.

Usage: put a link "LokToClock_server.py" in the "Startup" folder of the
Windows Start menu.
C:\>"C:\Python27\python.exe" -i I:\NIH\Software\LokToClock_server.py
Friedrich Schotte, 3 Jun 2013 - 7 Feb 2015
"""
__version__ = "1.0.1"

from LokToClock_driver import LokToClock
from CAServer import register_object
register_object(LokToClock,"14IDL:LokToClock")
