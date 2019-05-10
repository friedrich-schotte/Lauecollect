#!/bin/env python
"""Setup: source /reg/g/psdm/etc/ana_env.sh"""
import zmq
import numpy as np
from time import sleep

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:12300")

arr = np.zeros([512,512])
i = 0
while True:
    print i
    socket.send('rayonix',zmq.SNDMORE)
    socket.send_pyobj(i,zmq.SNDMORE)
    socket.send_pyobj(arr)
    i += 1
    arr += 1
    sleep(1)
