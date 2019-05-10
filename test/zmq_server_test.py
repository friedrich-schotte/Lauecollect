import zmq
import numpy as np

context = zmq.Context()
server = context.socket(zmq.PAIR)
server.bind("tcp://127.0.0.1:12322")

arr = np.zeros([512,512])
while True:
    i = server.recv_pyobj()
    print i
    server.send_pyobj(arr+i)
