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
Author: Friedrich Schotte,
Date created: 2015-11-21
Data last modified: 2021-07-16
Revision comment: Refactored
"""
__version__ = "1.4.6"

from logging import error, warning

from tcp_client import connection
from threading import Lock

default_port_number = 2001

lock = Lock()


def wput(data, URL):
    """Upload a file across the network
    data: content of the file to upload.
    URL: e.g. "//id14timing3.cars.aps.anl.gov:2001/tmp/test.txt"
    """
    # debug("%s, %d bytes %r " % (URL,len(data),data[0:21]))
    if has_ip_address(URL):
        with lock:  # Allow only one thread at a time inside this function.
            import socket
            s = b"PUT %s\n" % pathname(URL).encode("utf-8")
            s += b"Content-Length: %d\n" % len(data)
            s += b"\n"
            s += data
            for attempt in range(0, 2):
                try:
                    c = connection(ip_address_and_port(URL))
                    if c is None:
                        break
                    c.sendall(s)
                except socket.error:
                    continue
                break
    else:
        error(f"{URL!r}: IP address unknown")


def wget(URL):
    """Download a file from the network
    URL: e.g. "//id14timing3.cars.aps.anl.gov:2001/tmp/test.txt"
    """
    # debug("wget %r queued" % URL)
    data = b""
    if has_ip_address(URL):
        with lock:  # Allow only one thread at a time inside this function.
            # debug("wget %r..." % URL)
            import socket
            s = b"GET %s\n" % pathname(URL).encode("utf-8")
            s += b"\n"
            for attempt in range(0, 2):
                try:
                    c = connection(ip_address_and_port(URL))
                    if c is None:
                        break
                    c.sendall(s)
                    reply = b""
                    while b"\n\n" not in reply:
                        r = c.recv(65536)
                        if len(r) == 0:
                            break
                        reply += r
                    if len(r) == 0:
                        continue
                    header_size = reply.find(b"\n\n") + 2
                    keyword = b"Content-Length: "
                    if keyword not in reply:
                        return b""
                    start = reply.find(keyword) + len(keyword)
                    end = start + reply[start:].find(b"\n")
                    file_size = int(reply[start:end])
                    while len(reply) < header_size + file_size:
                        r = c.recv(65536)
                        if len(r) == 0:
                            break
                        reply += r
                    if len(r) == 0:
                        continue
                    data = reply[header_size:]
                    if len(data) != file_size:
                        warning("file server %s: expecting %d,got %d bytes" %
                                (ip_address_and_port(URL), file_size, len(data)))
                except socket.error:
                    continue
                break
                # debug("wget %r: %-.20r" % (URL,data))
    else:
        error(f"{URL!r}: IP address unknown")
    return data


def wdel(URL):
    """Download a file from the network
    URL: e.g. "//id14timing3.cars.aps.anl.gov:2001/tmp/test.txt"
    """
    if has_ip_address(URL):
        with lock:  # Allow only one thread at a time inside this function.
            import socket
            s = b"DEL %s\n" % pathname(URL).encode("utf-8")
            s += b"\n"
            for attempt in range(0, 2):
                try:
                    c = connection(ip_address_and_port(URL))
                    if c is None:
                        break
                    c.sendall(s)
                except socket.error:
                    continue
                break
    else:
        error(f"{URL!r}: IP address unknown")


def wexists(URL):
    """Download a file from the network
    url: e.g. "//id14timing3.cars.aps.anl.gov:2001/tmp/test.txt"
    """
    if has_ip_address(URL):
        with lock:  # Allow only one thread at a time inside this function.
            import socket
            s = b"EXISTS %s\n" % pathname(URL).encode("utf-8")
            s += b"\n"
            data = b""
            for attempt in range(0, 2):
                try:
                    c = connection(ip_address_and_port(URL))
                    if c is None:
                        break
                    c.sendall(s)
                    reply = b""
                    while b"\n\n" not in reply:
                        r = c.recv(65536)
                        if len(r) == 0:
                            break
                        reply += r
                    if len(r) == 0:
                        continue
                    header_size = reply.find(b"\n\n") + 2
                    keyword = b"Content-Length: "
                    if keyword not in reply:
                        return False
                    start = reply.find(keyword) + len(keyword)
                    end = start + reply[start:].find(b"\n")
                    file_size = int(reply[start:end])
                    while len(reply) < header_size + file_size:
                        r = c.recv(65536)
                        if len(r) == 0:
                            break
                        reply += r
                    if len(r) == 0:
                        continue
                    data = reply[header_size:]
                    if len(data) != file_size:
                        warning("file server %s: expecting %d,got %d bytes" %
                                (ip_address_and_port(URL), file_size, len(data)))
                except socket.error:
                    continue
                break
            result = data == "True\n"
    else:
        error(f"{URL!r}: IP address unknown")
        result = False
    return result


def wdir(URL):
    """List the contents of a directory
    URL: e.g. "//id14timing3.cars.aps.anl.gov:2001/tmp/*"
    Return value: list of strings
    """
    if has_ip_address(URL):
        with lock:  # Allow only one thread at a time inside this function.
            import socket
            s = b"DIR %s\n" % pathname(URL).encode("utf-8")
            s += b"\n"
            data = b""
            for attempt in range(0, 2):
                try:
                    c = connection(ip_address_and_port(URL))
                    if c is None:
                        break
                    c.sendall(s)
                    reply = b""
                    while b"\n\n" not in reply:
                        r = c.recv(65536)
                        if len(r) == 0:
                            break
                        reply += r
                    if len(r) == 0:
                        continue
                    header_size = reply.find(b"\n\n") + 2
                    keyword = b"Content-Length: "
                    if keyword not in reply:
                        return []
                    start = reply.find(keyword) + len(keyword)
                    end = start + reply[start:].find(b"\n")
                    file_size = int(reply[start:end])
                    while len(reply) < header_size + file_size:
                        r = c.recv(65536)
                        if len(r) == 0:
                            break
                        reply += r
                    if len(r) == 0:
                        continue
                    data = reply[header_size:]
                    if len(data) != file_size:
                        warning("file server %s: expecting %d,got %d bytes" %
                                (ip_address_and_port(URL), file_size, len(data)))
                except socket.error:
                    continue
                break
            data = data.decode("utf-8")
            data = data.strip("\n")
            file_list = data.split("\n") if len(data) > 0 else []
    else:
        error(f"{URL!r}: IP address unknown")
        file_list = []
    return file_list


def wsize(URL):
    """Download a file from the network
    URL: e.g. "//id14timing3.cars.aps.anl.gov:2001/tmp/test.txt"
    """
    if has_ip_address(URL):
        with lock:  # Allow only one thread at a time inside this function.
            import socket
            s = b"SIZE %s\n" % pathname(URL).encode("utf-8")
            s += b"\n"
            data = b""
            for attempt in range(0, 2):
                try:
                    c = connection(ip_address_and_port(URL))
                    if c is None:
                        break
                    c.sendall(s)
                    reply = b""
                    while b"\n\n" not in reply:
                        r = c.recv(65536)
                        if len(r) == 0:
                            break
                        reply += r
                    if len(r) == 0:
                        continue
                    header_size = reply.find(b"\n\n") + 2
                    keyword = b"Content-Length: "
                    if keyword not in reply:
                        return b""
                    start = reply.find(keyword) + len(keyword)
                    end = start + reply[start:].find(b"\n")
                    file_size = int(reply[start:end])
                    while len(reply) < header_size + file_size:
                        r = c.recv(65536)
                        if len(r) == 0:
                            break
                        reply += r
                    if len(r) == 0:
                        continue
                    data = reply[header_size:]
                    if len(data) != file_size:
                        warning("file server %s: expecting %d,got %d bytes" %
                                (ip_address_and_port(URL), file_size, len(data)))
                except socket.error:
                    continue
                break
            data = data.strip()
            try:
                size = int(data)
            except ValueError:
                warning("file server %s: expecting integer, got %r" %
                        (ip_address_and_port(URL), data))
                size = 0
    else:
        error(f"{URL!r}: IP address unknown")
        size = 0
    return size


def has_ip_address(URL):
    url = URL
    url = url.replace("http:", "")
    if url.startswith("//"):
        url = url[2:]
    ip_address_and_port = url.split("/")[0].split("@")[-1]
    if not ip_address_and_port:
        return False
    if ip_address_and_port.startswith(":"):
        return False
    return True


def ip_address_and_port(URL):
    default_port = 80 if URL.startswith("http:") else default_port_number
    URL = URL.replace("http:", "")
    if URL.startswith("//"):
        URL = URL[2:]
    ip_address_and_port = URL.split("/")[0].split("@")[-1]
    if not ip_address_and_port:
        error(f"{URL!r}: IP address unknown")
    if ":" not in ip_address_and_port:
        ip_address_and_port += ":" + str(default_port)
    return ip_address_and_port


def pathname(URL):
    URL = URL.replace("http:", "")
    if URL.startswith("//"):
        URL = URL[2:]
    pathname = "/" + "/".join(URL.split("/")[1:])
    return pathname


if __name__ == "__main__":
    from sys import argv, stderr

    if len(argv) != 3:
        stderr.write("Usage: %s test.txt http://id14timing3.cars.aps.anl.gov:2001/tmp/test.txt\n" % argv[0])
    else:
        filename, URL = argv[1], argv[2]
        wput(open(filename).read(), URL)

    # wput(b"test\n",'localhost:2001/tmp/test.txt')
    # wget('localhost:2001/tmp/test.txt')
    # wdir('localhost:2001/tmp/sequencer_fs/*')
