#!/usr/bin/env python
"""Communication with a network server using SSL protocol

Setup:
$ openssl req -new -x509 -days 365 -nodes -out servers.pem -keyout certificates/servers.pem
Country Name (2 letter code) []:US
State or Province Name (full name) []:MD
Locality Name (eg, city) []:Bethesda
Organization Name (eg, company) []:NIH
Organizational Unit Name (eg, section) []:NIDDK
Common Name (eg, fully qualified host name) []:femto.niddk.nih.gov
Email Address []:schotte@nih.gov

Maximum expiration time for a self-signed certificate is 12 months.
The file needs to be updated every 12 months.

Author: Friedrich Schotte
Date created: 2019-11-26
Date last modified: 2021-07-16
Python version: 2.7 and 3.7
Revision comment: Debug messages
"""
__version__ = "1.10.7"

from logging import debug, warning
from numpy import nan


class tcp_client_object(object):
    name = "tcp_client"
    from persistent_property import persistent_property
    ip_address = persistent_property("ip_address", "localhost:2000")

    def __init__(self, name=None):
        if name:
            self.name = name

    def query(self, command, terminator="\n", count=None):
        """Evaluate a command in the server and return the result.
        """
        reply = query(self.ip_address, command, terminator, count)
        return reply

    def send(self, command):
        """Evaluate a command in server.
        """
        send(self.ip_address, command)

    def get_connected(self):
        return connected(self.ip_address)

    connected = property(get_connected)
    online = connected

    def __repr__(self): return "%s(%r)" % (type(self).__name__, self.name)


def tcp_property(query_string, default_value=nan):
    """A property object to be used inside a class"""

    def fget(self):
        # Performs a query and returns the result as a number
        value = self.query("self." + query_string)
        dtype = type(default_value)
        try:
            value = dtype(eval(value))
        except Exception:
            value = default_value
        return value

    def fset(self, value):
        self.query("self.%s = %r" % (query_string, value))

    return property(fget, fset)


connections = {}
timeout = 5.0


def send(ip_address_and_port, command):
    """Send a command that does not generate a reply.
    ip_address_and_port: e.g. '164.54.161.34:2001'
    command: string, will by '\n' terminated"""
    query(ip_address_and_port, command, count=0)


write = send


def clear_input_queue(ip_address_and_port):
    import ssl
    c = connection(ip_address_and_port)
    if c is not None:
        c.settimeout(1e-6)
        discard = ""
        while True:
            try:
                discard += c.recv(65536)
                c.settimeout(0.1)
            except ssl.SSLError as x:
                if "timed out" not in str(x):
                    debug("%s: recv: %s" % (ip_address_and_port, x))
                break
        if len(discard) > 0:
            warning("ignoring unexpected reply %.200r (%d bytes)" %
                    (discard[0:80], len(discard)))
        c.settimeout(3)


def query(ip_address_and_port, command, terminator="\n", count=None):
    """Send a command that generates a reply.
    ip_address_and_port: e.g. '164.54.161.34:2001'
    command: string, will by '\n' terminated
    count: if given, number of bytes to read as reply, overrides terminator
    Return value: reply
    """
    with lock(ip_address_and_port):
        reply = b""
        command = as_bytes(command)
        terminator = as_bytes(terminator)
        if not ip_address_valid(ip_address_and_port):
            warning(f"{ip_address_and_port!r}: IP address unknown")
        else:
            import socket  # for exception
            if not command.endswith(b"\n"):
                command += b"\n"
            for attempt in range(0, 2):
                if attempt > 0:
                    warning("query %.200r, attempt %d..." % (command, attempt+1))
                try:
                    c = connection(ip_address_and_port)
                    if c is None:
                        break
                    # clear_input_queue(ip_address_and_port)
                    # debug("Sending %.200r" % command)
                    c.sendall(command)
                    reply = b""
                    if count is not None:
                        disconnected = False
                        while len(reply) < count:
                            r = c.recv(count - len(reply))
                            reply += r
                            if len(r) == 0:
                                disconnected = True
                                break
                        if len(reply) > count:
                            warning("query %.200r, count=%d: discarding %d bytes" %
                                    (command, count, len(reply) - count))
                            reply = reply[0:count]
                        if disconnected:
                            warning("disconnected")
                            continue
                    elif terminator:
                        while terminator not in reply:
                            r = c.recv(65536)
                            reply += r
                            if len(r) == 0:
                                break
                        if len(r) == 0:
                            warning("disconnected")
                            continue
                except socket.error as msg:
                    warning("query %.200r, error %s" % (command, msg))
                    if ip_address_and_port in connections:
                        # debug("resetting connection to %s" % ip_address_and_port)
                        del connections[ip_address_and_port]
                    continue
                break
                # if count is not None: debug("query %.200r, count=%d, got %d bytes" % (command,count,len(reply)))
            # elif terminator: debug("query %.200r, %.23r" % (command,reply))
        # reply = as_string(reply)
        return reply


def disconnect(ip_address_and_port):
    """Make sure no connection is open to the specified port.
    ip_address_and_port: e.g. '164.54.161.34:2001'
    """
    with lock(ip_address_and_port):
        if ip_address_and_port in connections:
            # debug("disconnecting %s" % ip_address_and_port)
            del connections[ip_address_and_port]


def connected(ip_address_and_port):
    """Is server online?
    ip_address_and_port: e.g. '164.54.161.34:2001'
    """
    with lock(ip_address_and_port):
        connected = False
        if not ip_address_valid(ip_address_and_port):
            warning(f"{ip_address_and_port!r}: IP address unknown")
        else:
            connected = connection(ip_address_and_port) is not None
        return connected


def connection(ip_address_and_port):
    """Cached IP socket connection"""
    connection = None
    if not ip_address_valid(ip_address_and_port):
        warning(f"{ip_address_and_port!r}: IP address unknown")
    else:
        from threading import Thread
        from time import time, sleep

        if ip_address_and_port not in connecting:
            connecting[ip_address_and_port] = False

        if not connection_alive(ip_address_and_port):
            if ip_address_and_port not in first_attempt:
                first_attempt[ip_address_and_port] = time()
            if not connecting[ip_address_and_port]:
                connecting[ip_address_and_port] = True
                thread = Thread(target=connect, args=(ip_address_and_port,))
                thread.daemon = True
                thread.start()
            while not connection_alive(ip_address_and_port):
                sleep(0.010)
                if time() - first_attempt[ip_address_and_port] > 1.0:
                    break

        if connection_alive(ip_address_and_port) and ip_address_and_port in connections:
            # reset timeout
            if ip_address_and_port in first_attempt:
                del first_attempt[ip_address_and_port]
            connection = connections[ip_address_and_port]
        else:
            connection = None
    return connection


def connect(ip_address_and_port):
    """Establish IP socket connection"""
    import socket
    if not connection_alive(ip_address_and_port):
        if ip_address_and_port in connections:
            warning("tcp client: %s: reconnecting" % ip_address_and_port)
        connection = socket.socket()
        connection.settimeout(timeout)
        request_keep_alive(connection)
        if protocol(ip_address_and_port) == "ssl":
            # based on:
            # https://stackoverflow.com/questions/26851034/opening-a-ssl-socket-connection-in-python
            import ssl
            try:
                connection = ssl.wrap_socket(
                    connection,
                    certfile=connection_cert_file(ip_address_and_port),
                    keyfile=connection_keyfile(ip_address_and_port),
                    ssl_version=ssl.PROTOCOL_TLSv1_2,
                    cert_reqs=ssl.CERT_REQUIRED,
                    ca_certs=connection_cert_file(ip_address_and_port),
                )
            except ssl.SSLError as msg:
                warning("%s: connect: %s" % (ip_address_and_port, msg))
                connection = None
        if connection:
            # debug("tcp client: %s connecting" % ip_address_and_port)
            ip_address = connection_ip_address(ip_address_and_port)
            port = connection_port(ip_address_and_port)
            try:
                connection.connect((ip_address, port))
            except Exception as msg:
                warning("%s: connect: %s" % (ip_address_and_port, msg))
                connection = None
        if connection:
            # debug("tcp client: %s: connected" % ip_address_and_port)
            connection.settimeout(timeout)
            connections[ip_address_and_port] = connection
        elif ip_address_and_port in connections:
            del connections[ip_address_and_port]
    connecting[ip_address_and_port] = False


def protocol(ip_address_and_port):
    """'tcp' or 'ssl'"""
    protocol = 'tcp'
    if ip_address_and_port.startswith("ssl:"):
        protocol = 'ssl'
    if ip_address_and_port.startswith("tcp:"):
        protocol = 'tcp'
    return protocol


def connection_cert_file(ip_address_and_port):
    ip_address_and_port = ip_address_and_port.replace("ssl:", "")
    ip_address_and_port = ip_address_and_port.replace("tcp:", "")
    ip_address_and_port = ip_address_and_port.replace("//", "")
    if "@" not in ip_address_and_port:
        ip_address_and_port = "servers:servers@" + ip_address_and_port
    cert_key = ip_address_and_port.split("@")[0]
    cert = cert_key.split(":")[0]
    cert_file = cert_dir() + "/" + cert + ".pem"
    from os.path import exists
    if not exists(cert_file):
        warning("file %r not found" % cert_file)
    return cert_file


def connection_keyfile(ip_address_and_port):
    ip_address_and_port = ip_address_and_port.replace("ssl:", "")
    ip_address_and_port = ip_address_and_port.replace("tcp:", "")
    ip_address_and_port = ip_address_and_port.replace("//", "")
    if "@" not in ip_address_and_port:
        ip_address_and_port = "servers:servers@" + ip_address_and_port
    cert_key = ip_address_and_port.split("@")[0]
    if ":" not in cert_key:
        cert_key += ":" + cert_key
    key = cert_key.split(":")[-1]
    keyfile = cert_dir() + "/" + key + ".pem"
    from os.path import exists
    if not exists(keyfile):
        warning("file %r not found" % keyfile)
    return keyfile


def cert_dir():
    from module_dir import module_dir
    return module_dir(cert_dir) + "/certificates"


def connection_ip_address(ip_address_and_port):
    ip_address_and_port = ip_address_and_port.replace("ssl:", "")
    ip_address_and_port = ip_address_and_port.replace("tcp:", "")
    ip_address_and_port = ip_address_and_port.replace("//", "")
    ip_address_and_port = ip_address_and_port.split("@")[-1]
    ip_address = ip_address_and_port.split(":")[0]
    return ip_address


def connection_port(ip_address_and_port):
    ip_address_and_port = ip_address_and_port.replace("ssl:", "")
    ip_address_and_port = ip_address_and_port.replace("tcp:", "")
    ip_address_and_port = ip_address_and_port.replace("//", "")
    ip_address_and_port = ip_address_and_port.split("@")[-1]
    if ":" not in ip_address_and_port:
        ip_address_and_port += ":2000"
    port = ip_address_and_port.split(":")[1]
    try:
        port = int(port)
    except ValueError:
        port = 2000
    return port


def ip_address_valid(ip_address_and_port):
    valid = (connection_ip_address(ip_address_and_port) != "")
    return valid


def request_keep_alive(connection):
    """Requests that the OS periodically sends "keep alive" packets to check
    whether a TCP connection is still active"""
    import socket
    connection.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    try:  # MacOS, Linux?
        TCP_KEEPALIVE = 0x10  # idle time
        TCP_KEEPINTVL = 0x101
        TCP_KEEPCNT = 0x102
        connection.setsockopt(socket.IPPROTO_TCP, TCP_KEEPALIVE, 3)
        connection.setsockopt(socket.IPPROTO_TCP, TCP_KEEPINTVL, 3)
        connection.setsockopt(socket.IPPROTO_TCP, TCP_KEEPCNT, 1)
        # debug("Linux-style keep_alive request succeeded")
    except OSError:
        pass
    try:  # Windows
        connection.ioctl(socket.SIO_KEEPALIVE_VALS, (1, 1000, 1000))
        # debug("Windows-style keep_alive request succeeded")
    except (AttributeError, OSError):
        pass


def connection_alive(ip_address_and_port):
    """Is socket in usable state?"""
    import socket

    if ip_address_and_port not in connections:
        return False
    c = real_socket(connections[ip_address_and_port])

    try:
        c.getpeername()
    except socket.error as msg:
        warning("tcp client: %s alive? peer name: %s" % (ip_address_and_port, msg))
        return False

    timeout = c.gettimeout()
    c.settimeout(0.000001)
    try:
        if len(c.recv(1)) == 0:
            warning("tcp client: %s alive? disconnected" % ip_address_and_port)
            return False
    except socket.timeout:
        pass
    except socket.error as msg:
        warning("tcp client: %s alive? recv: %s" % (ip_address_and_port, msg))
        return False
    c.settimeout(timeout)
    try:
        c.send(b"")
    except socket.error as msg:
        warning("tcp client: %s alive? send: %s" % (ip_address_and_port, msg))
        return False
    return True


def real_socket(c):
    import socket
    if hasattr(c, "_sock"):
        c = c._sock
    elif type(c) is not socket.socket:
        c = super(type(c), c)
    return c


def lock(ip_address_and_port):
    """A per-connection thread synchronization lock
    ip_address_and_port: e.g. '164.54.161.34:2001'
    """
    from threading import Lock
    if ip_address_and_port not in locks:
        locks[ip_address_and_port] = Lock()
    lock = locks[ip_address_and_port]
    return lock


locks = {}
first_attempt = {}
connecting = {}


def as_bytes(string):
    as_bytes = string
    if type(bytes) != bytes:
        if hasattr(string, "encode"):
            as_bytes = string.encode("latin-1")
    return as_bytes


def as_string(bytes_object):
    as_string = bytes_object
    if type(bytes_object) != str:
        if hasattr(bytes_object, "decode"):
            as_string = bytes_object.decode("latin-1")
    return as_string


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s %(levelname)s: %(message)s")
    from time import time

    # ip_address_and_port = 'ssl://pico7.niddk.nih.gov:2000'
    ip_address_and_port = "ssl://localhost:2000"
    print('connect(%r)' % ip_address_and_port)
    print('query(%r,"1+1")' % ip_address_and_port)
    print('connection_alive(%r)' % ip_address_and_port)
    print('connected(%r)' % ip_address_and_port)
    # print('clear_input_queue(%r)' % ip_address_and_port)
    print('disconnect(%r)' % ip_address_and_port)
