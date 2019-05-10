# to do:
# had 1 hang don't understand (maybe hit end of file?)
# test boundary cases

from psana import *
import zmq 
import numpy as np 
import time
 
context = zmq.Context() 
server = context.socket(zmq.PAIR) 
server.bind("tcp://*:12322") 
 

class DataStream:
    def __init__(self):
        self.olddsstring = None
        self.nevent = -1
        self.src = Source('rayonix')

    def image(self,runexp_string):
        fields = runexp_string.split(':')
        dsstring = ":".join(fields[:-1])
        eventreq = int(fields[-1])
        if dsstring != self.olddsstring or eventreq<=self.nevent:
            start = time.time()
            try:
                self.ds = DataSource(dsstring)
            except:
                print '*** Failed to open datasource:',dsstring
                return None
            self.nevent=-1
            self.olddsstring = dsstring
            #det = Detector('rayonix',self.ds.env())
            print 'opened new datasource in',time.time()-start,'seconds'
        for evt in self.ds.events():
            #raw = det.raw(evt)
            raw = evt.get(Camera.FrameV1,self.src)
            if raw is not None: self.nevent+=1
            if eventreq==self.nevent: break
        if eventreq != self.nevent:
            print '*** Event',eventreq,'not found'
            return None
        #server.send_pyobj(raw) 
        print 'sending image',eventreq,self.nevent,evt.get(EventId).fiducials()
        return raw.data16()

stream = DataStream()
while True:
    print 'waiting for request'
    runexp_string = server.recv_pyobj()
    print 'Received request:',runexp_string
    try:
        server.send_pyobj(stream.image(runexp_string),zmq.NOBLOCK)
    except:
        # see http://stackoverflow.com/questions/21826357/zmq-send-with-noblock-raise-resource-temporarily-unavailable
        print '*** zmq send failed.  perhaps the zmq.NOBLOCK has raised eagain' 
