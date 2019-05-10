"""Spectra Physics 3930 Lok-to-Clock frequency stabilizer for the Tsunami laser
This is to make the device remote controllable accross the network using
EPICS.
Friedrich Schotte, 3 Jun 2013 - 27 Apr 2016
"""
__version__ = "1.1.1" # EPICS_CA_ADDR_LIST

from CA import Record
from os import environ

environ["EPICS_CA_ADDR_LIST"] = "id14l-spitfire2.cars.aps.anl.gov"
LokToClock = Record("14IDL:LokToClock")

if __name__ == "__main__":
    from CA import caget
    print 'caget("14IDL:LokToClock.locked")'
    print "LokToClock.locked"
    print "LokToClock.locked = 1"
