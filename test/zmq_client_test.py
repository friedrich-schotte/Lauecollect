import time
import zmq

context = zmq.Context()
client = context.socket(zmq.PAIR)
client.connect("tcp://127.0.0.1:12322")

for i in range(0,100):
    client.send_pyobj(i)
    arr = client.recv_pyobj()
    print arr.shape,'\n',arr[0:2,0:2]
    time.sleep(1)
