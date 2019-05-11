"""
Simple SOCKET server for testing\learning purposes
"""

import socket
from time import time,clock
from numpy import zeros


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
port = 2207
sock.bind(('',port))
sock.listen(5)

def run():
    from thread import start_new_thread
    start_new_thread(run_once,())
def run_once():
    while True:
        global client_lst
        client_lst= []
        client, addr = sock.accept()
        print addr
        try:
            print(client_lst.index(addr))
        except: pass
        client_lst.append((time(),addr))
        t1 = clock()
        #print('Got connection from ' , adrr)
        #x = raw_input('type response:')
        data = client.recv(3044)
    
        client.send(data)


