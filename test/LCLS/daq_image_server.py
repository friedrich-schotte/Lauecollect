"""
Run on "mond" node "daq-xpp-mon05.pcdsn" or "daq-xpp-mon06.pcdsn".
Only one instance can run per node.
Setup:
source /reg/g/psdm/etc/ana_env.sh
DAQ Control - (uncheck) Record Run - Begin Running

Chris O'Grady, Jan 22, 2016
"""
import time
import zmq
from psana import *
from logging import info,warn,debug

ds = DataSource('shmem=XPP.0:stop=no')
src = Source('rayonix')

context = zmq.Context()
sender = context.socket(zmq.PUSH)
sender.connect("tcp://172.21.22.71:12323")

for evt in ds.events():
    debug("Waiting for event...")
    raw = evt.get(Camera.FrameV1,src)
    debug("Got event")
    if raw is None: continue
    data = raw.data16()
    t = evt.get(EventId).fiducials()
    print('Sending array data: %r,%r' % (t,data.shape))
    sender.send_pyobj(data)
