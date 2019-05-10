#!/bin/env python
"""Setup: source /reg/g/psdm/etc/ana_env.sh
"""
from time import time
import zmq
from logging import error,warn,info,debug

context = zmq.Context()
socket = context.socket(zmq.SUB)
servers = ["daq-xpp-mon05","daq-xpp-mon06"]
##servers = ['172.21.38.163','172.21.38.173']
##servers = ["localhost"]
ports = range(12300,12300+12)
for server in servers:
    for port in ports: socket.connect("tcp://%s:%d" % (server,port)) 
socket.setsockopt(zmq.SUBSCRIBE, 'rayonix')

last_fid = 0
while True:
    topic = socket.recv()
    fid = socket.recv_pyobj()
    arr = socket.recv_pyobj()
    print("%d (%+d): %r" % (fid,fid-last_fid,arr.shape))
    last_fid = fid
