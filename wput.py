#!/usr/bin/env python
"""Upload a file across the network using HTTP protocol.
Friedrich Schotte, Jun 25, 2015 - Dec 3, 2015

Setup:
The program "file-upload-receive.cgi" needs to be installed on
the remote host in the "httpd" directory (/home/timing_system).
"""
__version__ = "1.0.2"

def wput(data,URL):
    """Upload a file across the network using HTTP protocol
    data: content of the file to upload.
    URL: e.g. "http://id14timing3.cars.aps.anl.gov/tmp/test.txt"
    """
    URL = URL.replace("http://","")
    ip_address = URL.split("/")[0]
    destination = "/"+"/".join(URL.split("/")[1:])
    boundary = "----WebKitFormBoundaryM5PGi0cwxiuRg1NG"
    s =  "POST /file-upload-receive.cgi HTTP/1.0\n"
    s += "Content-Type: multipart/form-data; boundary="+boundary+"\n"
    s += "\n"
    s += boundary+"\n"
    s += 'Content-Disposition: form-data; name="file"; filename="'+destination+'"\n'
    s += "Content-Type: application/octet-stream\n"
    s += "\n"
    s += data
    s += "\n"
    s += boundary+"--\n"
    import socket
    connection = socket.socket()
    connection.settimeout(3)
    connection.connect((ip_address,80))
    connection.sendall(s)
    connection.shutdown(socket.SHUT_WR)
    connection.settimeout(None)
    reply = ""; r = connection.recv(65536)
    while len(r) > 0: reply += r; r = connection.recv(65536)
    # reply: "HTTP/1.0 200 OK\r\n"

if __name__ == "__main__":
    from sys import argv,stderr
    if len(argv) != 3:
        stderr.write("Usage: wput.py test.txt http://id14timing3.cars.aps.anl.gov/tmp/test.txt\n")
    else:
        filename,URL = argv[1],argv[2]
        wput(file(filename).read(),URL)
