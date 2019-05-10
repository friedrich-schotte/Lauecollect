#!/bin/env python
"""
Acquire a series of images using the XPP Rayonix detector with the
LCLS data acquisition system and a server running on a "mond" node.
This script listens to a shared memory server of the DAQ system and resends
images to a client program (Lauecollect) running on "xpp-daq" or "xpp-control".

Setup:
ssh daq-xpp-mon05
cd ~xppopr/experiments/xppj1216/software
./shmem.py

Author: Chris O'Grady, Jan 22, 2016 - Jan 27, 2016
"""
import time
import zmq
from psana import *
import numpy as np
from thread import start_new_thread

def rebin(a, shape): 
    sh = shape[0],a.shape[0]//shape[0],shape[1],a.shape[1]//shape[1] 
    # can do either two means, or two sums here.  have
    # to watch out for overflows with integers
    return a.reshape(sh).sum(-1).sum(1)

ds = DataSource('shmem=XPP.0:stop=no')
#src = Source('rayonix')
det = Detector('rayonix',ds.env())

from mpi4py import MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

startport = 12300
binning = 1

context = zmq.Context()

socket = context.socket(zmq.PUB)
socket.bind("tcp://*:%d" % (startport+(rank%12)))

def update_binning():
    global binning
    cmd_socket = context.socket(zmq.SUB)
    cmd_socket.connect('tcp://172.21.38.54:12399') # xpp-daq
    cmd_socket.connect('tcp://172.21.38.71:12399') # xpp-control
    cmd_socket.setsockopt(zmq.SUBSCRIBE, 'cmd')
    while True:
        try:
            topic = cmd_socket.recv()
            binning = cmd_socket.recv_pyobj()
            print '*** New binning',binning
        except:
            pass
start_new_thread(update_binning,())

comm.Barrier()
start = time.time()
for nevent,evt in enumerate(ds.events()):
    
    #print rank,evt.get(EventId).fiducials()
    if nevent%100==0:
        neventtot = comm.reduce(nevent)
        if rank==0:
            print '***',nevent,neventtot,neventtot/(time.time()-start),'Hz'
    #raw = evt.get(Camera.FrameV1,src)
    raw = det.raw(evt)
    if raw is None: continue
    #data = raw.data16()
    socket.send('rayonix',zmq.SNDMORE)
    fid = evt.get(EventId).fiducials()
    socket.send_pyobj(fid,zmq.SNDMORE)

    raw_int32 = raw.astype(np.int32) # to avoid overflows
    if binning == 1:
        binned_uint16 = raw
    else:
        binned = rebin(raw_int32,[raw_int32.shape[0]/binning,raw_int32.shape[1]/binning])
        binned -= 10*(binning**2-1) # subtract off all but 1 of the 10ADU pedestals that the rayonix has
        binned[binned>65535]=65535
        binned[binned<0]=0
        binned_uint16 = binned.astype(np.uint16)

    print 'Sending array data:',binned_uint16.shape,fid
    socket.send_pyobj(binned_uint16)
