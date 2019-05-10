# Import socket module
import socket               
port = 2060

def connection(N = 1):
    # Create a socket object
    s = socket.socket()         

    # Define the port on which you want to connect
    

    # connect to the server on local computer
    s.connect(('128.231.5.299', port))#128.231.5.59
    
    # receive data from the server
    data = '1'*N
    s.send(data)
    length = len(data)
    while len(data)<length:
        data +=  s.recv(length-len(data))
    # close the connection
    s.close()
    return data
def run():
    from thread import start_new_thread
    start_new_thread(run_once,())
def run_once():
    sock = socket.socket()
    sock.bind(('',port))
    sock.listen(5)
    while True:
        client, adrr = sock.accept()
        t1 = clock()
        #print('Got connection from ' , adrr)
        #x = raw_input('type response:')
        x = '1'*(200000 -20)
        client.send('Connection Received %r' % x)
        t2 = clock()
        print(t2-t1)
        #client.close()
print('data = connection()')
