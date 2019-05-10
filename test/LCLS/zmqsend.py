import time
import zmq
import numpy as np

context = zmq.Context()
sender = context.socket(zmq.PUSH)
sender.connect("tcp://127.0.0.1:12321")
arr = np.zeros([512,512])
for num in range(1000):
    sender.send_pyobj(arr)
    arr+=1
    time.sleep(1)
