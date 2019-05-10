"""
Run on "mond" node "daq-xpp-mon05.pcdsn" or "daq-xpp-mon06.pcdsn".
Only one instance can run per node.

Setup:
ssh daq-xpp-mon06.pcdsn
source /reg/g/psdm/etc/ana_env.sh

DAQ Control - (uncheck) Record Run - Begin Running

Chris O'Grady, Jan 22, 2016
"""
from psana import *
from logging import info,warn,debug

ds = DataSource('shmem=XPP.0:stop=no')
src = Source('rayonix')
t0 = 0

print("Setup complete")
for evt in ds.events():
    debug("Waiting for event...")
    raw = evt.get(Camera.FrameV1,src)
    debug("Got event")
    if raw is None: continue
    t = evt.get(EventId).fiducials()
    print('Fiducial %d (+%d)' % (t,t-t0))
    t0 = t
