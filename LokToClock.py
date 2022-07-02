"""Spectra Physics 3930 Lok-to-Clock frequency stabilizer for the Tsunami laser
This is to make the device remote controllable accross the network using
EPICS.
Author: Friedrich Schotte
Date created: 2013-06-03
Date last modified: 2019-11-13
"""
__version__ = "1.1.3" # removed address list for EPICS

from CA import Record
LokToClock = Record("14IDL:LokToClock")

if __name__ == "__main__":
    from CA import caget
    print('caget("14IDL:LokToClock.locked")')
    print("LokToClock.locked")
    print("LokToClock.locked = 1")
