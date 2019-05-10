#!/bin/env python
"""Setup: source /reg/g/psdm/etc/ana_env.sh
Open a port to psana via SSh Tunneling.
ssh -Nx -L localhost:12322:psana1508:12322 psdev &
"""
from time import time
import zmq

##run = "exp=xpptut15:run=240:smd"
run = "exp=xppj1216:run=10:smd:dir=/reg/d/ffb/xpp/xppj1216/xtc:live"

context = zmq.Context()
client = context.socket(zmq.PAIR)
client.connect("tcp://127.0.01:12322") # requires SSH Tunnel

start = time()
for i in range(0,20):
    image_id = "%s:%d" % (run,i)
    print "sending %r" % image_id
    client.send_pyobj(image_id) 
    arr = client.recv_pyobj()
    if arr is not None: print arr.shape,'\n',arr[0:2,0:2]
    else: print "None"

print 20/(time()-start), 'Hz'
