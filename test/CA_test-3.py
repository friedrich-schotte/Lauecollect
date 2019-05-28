"""EPICS Channel Access Protocol"""

from CA import PV,Record,caput,caget
SAMPLET = Record("14IDB-NIH:SAMPLET")

if __name__ == "__main__":
    print "SAMPLET.port_name.value"
    print "SAMPLET.T.unit"
    print "SAMPLET.T.value"
    print "SAMPLET.T.moving"
