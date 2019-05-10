#!/bin/env python
"""Setup: source /reg/g/psdm/etc/ana_env.sh
Open a port to psana via SSh Tunneling.
ssh -Nx -L localhost:12322:psana1508:12322 psdev &
"""
import zmq
from logging import info,warn,debug

class DataStream:
    def __init__(self,address):
        context = zmq.Context()
        self.client = context.socket(zmq.PAIR)
        self.client.connect(address)

    def image(self,image_id):
        """image_id: string"""
        print("DataStream: requesting %r" % image_id)
        self.client.send_pyobj(image_id) 
        return self.client.recv_pyobj()

##address = "tcp://127.0.01:12322" # requires SSH Tunnel
address = "tcp://psana1508.pcdsn:12322"
datastream = DataStream(address)  

if __name__ == "__main__": # for testing
    from time import time
    run = "exp=xppj1216:run=17:smd:dir=/reg/d/ffb/xpp/xppj1216/xtc:live"

    def test():
        start = time()
        n = 0
        for i in range(0,20):
            image_id = "%s:%d" % (run,i)
            info("getting image %r" % image_id)
            img = datastream.image(image_id)
            if img is not None:
                n += 1
                info("%s\n%s"%(img.shape,img[0:2,0:2]))
            else: info("None")
        print "%d images, %.1f images/s" % (n,n/(time()-start))
    print("test()")

