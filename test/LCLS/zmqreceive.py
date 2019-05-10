import zmq

context = zmq.Context()
receiver = context.socket(zmq.PULL)
receiver.bind("tcp://*:12321")

while True:
    arr = receiver.recv_pyobj()
    print arr.shape,'\n',arr[0:2,0:2]
