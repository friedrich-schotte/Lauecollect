#!/usr/bin/env python
"""Upload and download files across the network,
from and to the FPGA timing system.

Setup:
A server program, named "file-server" to be
running on the timing system (in "/home/timing_system").

Usage examples:
wput("test\n","//id14timing3.cars.aps.anl.gov:2001/tmp/test.txt")
wput("."*1000000,"//id14timing3.cars.aps.anl.gov:2001/tmp/test.dat")
data = wget("//id14timing3.cars.aps.anl.gov:2001/tmp/test.dat")
wdel("//id14timing3.cars.aps.anl.gov:2001/tmp/test.txt")

Transfer speed: 8.2 MB/s upload, 8.1 MB/s download
: 15 us per file upload, 8 ms per file download
Friedrich Schotte, Nov 21, 2015 - Aug 28, 2017
"""
__version__ = "1.4" # (ip_address,port) -> ip_address_and_port
from logging import debug,info,warn,error
from tcp_client import connection

default_port_number = 2001

from thread import allocate_lock
lock = allocate_lock()

def wput(data,URL):
    """Upload a file across the network
    data: content of the file to upload.
    URL: e.g. "//id14timing3.cars.aps.anl.gov:2001/tmp/test.txt"
    """
    ##debug("%s, %d bytes %r " % (URL,len(data),data[0:21]))
    with lock: # Allow only one thread at a time inside this function.
        import socket
        url = URL
        default_port = 80 if url.startswith("http:") else default_port_number
        url = url.replace("http:","")
        if url.startswith("//"): url = url[2:]
        ip_address_and_port = url.split("/")[0].split("@")[-1]
        if not ":" in ip_address_and_port: ip_address_and_port += ":"+str(default_port)
        pathname = "/"+"/".join(url.split("/")[1:])
        s =  "PUT %s\n" % pathname
        s += "Content-Length: %d\n" % len(data)
        s += "\n"
        s += data
        for attempt in range(0,2):
            try:
                c = connection(ip_address_and_port)
                if c is None: break
                c.sendall(s)
            except socket.error: continue
            break    

def wget(URL):
    """Download a file from the network
    URL: e.g. "//id14timing3.cars.aps.anl.gov:2001/tmp/test.txt"
    """
    ##debug("wget %r queued" % URL)
    with lock: # Allow only one thread at a time inside this function.
        ##debug("wget %r..." % URL)
        import socket
        url = URL
        default_port = 80 if url.startswith("http:") else default_port_number
        url = url.replace("http:","")
        if url.startswith("//"): url = url[2:]
        ip_address_and_port = url.split("/")[0]
        if not ":" in ip_address_and_port: ip_address_and_port += ":"+str(default_port)
        pathname = "/"+"/".join(url.split("/")[1:])
        s =  "GET %s\n" % pathname
        s += "\n"
        data = ""
        for attempt in range(0,2):
            try: 
                c = connection(ip_address_and_port)
                if c is None: break
                c.sendall(s)
                reply = ""
                while not "\n\n" in reply:
                    r = c.recv(65536)
                    if len(r) == 0: break
                    reply += r
                if len(r) == 0: continue
                header_size = reply.find("\n\n")+2
                keyword = "Content-Length: "
                if not keyword in reply: return ""
                start = reply.find(keyword)+len(keyword)
                end = start+reply[start:].find("\n")
                file_size = int(reply[start:end])
                while len(reply) < header_size+file_size:
                    r = c.recv(65536)
                    if len(r) == 0: break
                    reply += r
                if len(r) == 0: continue
                data = reply[header_size:]
                if len(data) != file_size:
                    warn("file server %s: expecting %d,got %d bytes" %
                         (ip_address_and_port,file_size,len(data)))
            except socket.error: continue
            break    
        ##debug("wget %r: %-.20r" % (URL,data))
        return data

def wdel(URL):
    """Download a file from the network
    URL: e.g. "//id14timing3.cars.aps.anl.gov:2001/tmp/test.txt"
    """
    with lock: # Allow only one thread at a time inside this function.
        import socket
        url = URL
        default_port = 80 if url.startswith("http:") else default_port_number
        url = url.replace("http:","")
        if url.startswith("//"): url = url[2:]
        ip_address_and_port = url.split("/")[0]
        if not ":" in ip_address_and_port: ip_address_and_port += ":"+str(default_port)
        pathname = "/"+"/".join(url.split("/")[1:])
        s =  "DEL %s\n" % pathname
        s += "\n"
        for attempt in range(0,2):
            try:
                c = connection(ip_address_and_port)
                if c is None: break
                c.sendall(s)
            except socket.error: continue
            break    

def wexists(URL):
    """Download a file from the network
    url: e.g. "//id14timing3.cars.aps.anl.gov:2001/tmp/test.txt"
    """
    with lock: # Allow only one thread at a time inside this function.
        import socket
        url = URL
        default_port = 80 if url.startswith("http:") else default_port_number
        url = url.replace("http:","")
        if url.startswith("//"): url = url[2:]
        ip_address_and_port = url.split("/")[0]
        if not ":" in ip_address_and_port: ip_address_and_port += ":"+str(default_port)
        pathname = "/"+"/".join(url.split("/")[1:])
        s =  "EXISTS %s\n" % pathname
        s += "\n"
        data = ""
        for attempt in range(0,2):
            try: 
                c = connection(ip_address_and_port)
                if c is None: break
                c.sendall(s)
                reply = ""
                while not "\n\n" in reply:
                    r = c.recv(65536)
                    if len(r) == 0: break
                    reply += r
                if len(r) == 0: continue
                header_size = reply.find("\n\n")+2
                keyword = "Content-Length: "
                if not keyword in reply: return ""
                start = reply.find(keyword)+len(keyword)
                end = start+reply[start:].find("\n")
                file_size = int(reply[start:end])
                while len(reply) < header_size+file_size:
                    r = c.recv(65536)
                    if len(r) == 0: break
                    reply += r
                if len(r) == 0: continue
                data = reply[header_size:]
                if len(data) != file_size:
                    warn("file server %s: expecting %d,got %d bytes" %
                         (ip_address_and_port,file_size,len(data)))
            except socket.error: continue
            break    
        return data == "True\n"

def wdir(URL):
    """Download a file from the network
    URL: e.g. "//id14timing3.cars.aps.anl.gov:2001/tmp/*"
    """
    with lock: # Allow only one thread at a time inside this function.
        import socket
        url = URL
        default_port = 80 if url.startswith("http:") else default_port_number
        url = url.replace("http:","")
        if url.startswith("//"): url = url[2:]
        ip_address_and_port = url.split("/")[0]
        if not ":" in ip_address_and_port: ip_address_and_port += ":"+str(default_port)
        pathname = "/"+"/".join(url.split("/")[1:])
        s =  "DIR %s\n" % pathname
        s += "\n"
        data = ""
        for attempt in range(0,2):
            try: 
                c = connection(ip_address_and_port)
                if c is None: break
                c.sendall(s)
                reply = ""
                while not "\n\n" in reply:
                    r = c.recv(65536)
                    if len(r) == 0: break
                    reply += r
                if len(r) == 0: continue
                header_size = reply.find("\n\n")+2
                keyword = "Content-Length: "
                if not keyword in reply: return ""
                start = reply.find(keyword)+len(keyword)
                end = start+reply[start:].find("\n")
                file_size = int(reply[start:end])
                while len(reply) < header_size+file_size:
                    r = c.recv(65536)
                    if len(r) == 0: break
                    reply += r
                if len(r) == 0: continue
                data = reply[header_size:]
                if len(data) != file_size:
                    warn("file server %s: expecting %d,got %d bytes" %
                         (ip_address_and_port,file_size,len(data)))
            except socket.error: continue
            break    
        return data

def wsize(URL):
    """Download a file from the network
    URL: e.g. "//id14timing3.cars.aps.anl.gov:2001/tmp/test.txt"
    """
    with lock: # Allow only one thread at a time inside this function.
        import socket
        url = URL
        default_port = 80 if url.startswith("http:") else default_port_number
        url = url.replace("http:","")
        if url.startswith("//"): url = url[2:]
        ip_address_and_port = url.split("/")[0]
        if not ":" in ip_address_and_port: ip_address_and_port += ":"+str(default_port)
        pathname = "/"+"/".join(url.split("/")[1:])
        s =  "SIZE %s\n" % pathname
        s += "\n"
        data = ""
        for attempt in range(0,2):
            try: 
                c = connection(ip_address_and_port)
                if c is None: break
                c.sendall(s)
                reply = ""
                while not "\n\n" in reply:
                    r = c.recv(65536)
                    if len(r) == 0: break
                    reply += r
                if len(r) == 0: continue
                header_size = reply.find("\n\n")+2
                keyword = "Content-Length: "
                if not keyword in reply: return ""
                start = reply.find(keyword)+len(keyword)
                end = start+reply[start:].find("\n")
                file_size = int(reply[start:end])
                while len(reply) < header_size+file_size:
                    r = c.recv(65536)
                    if len(r) == 0: break
                    reply += r
                if len(r) == 0: continue
                data = reply[header_size:]
                if len(data) != file_size:
                    warn("file server %s: expecting %d,got %d bytes" %
                        (ip_address_and_port,file_size,len(data)))
            except socket.error: continue
            break
        data = data.strip()
        try: size = int(data)
        except:
            warn("file server %s: expecting integer, got %r" %
                (ip_address_and_port,data))
            size = 0
        return size


if __name__ == "__main__":
    from pdb import pm
    from sys import argv,stderr
    if len(argv) != 3:
        stderr.write("Usage: %s test.txt http://id14timing3.cars.aps.anl.gov:2001/tmp/test.txt\n" % argv[0])
    else:
        filename,URL = argv[1],argv[2]
        wput(file(filename).read(),URL)

    ##wput('22'.ljust(22)+'\n','id14timing3.cars.aps.anl.gov:2001/tmp/sequencer_fs/queue_max_repeat_count')
