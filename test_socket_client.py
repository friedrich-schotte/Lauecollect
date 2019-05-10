# Echo client program
import socket

HOST = '164.54.161.158'    # The remote host
PORT = 50000              # The same port as used by the server
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
data  = raw_input('what to send? ')
s.connect((HOST, PORT))
s.send(str(data))
data = s.recv(1024)
s.close()
print 'Received', repr(data)
