#!/usr/bin/env python
"""
A single-threaded network server using SSL protocol to process ASCII-encoded Python commands

Setup:
$ openssl req -new -x509 -days 365 -nodes -out servers.pem -keyout servers.pem
Country Name (2 letter code) []:US
State or Province Name (full name) []:MD
Locality Name (eg, city) []:Bethesda
Organization Name (eg, company) []:NIH
Organizational Unit Name (eg, section) []:NIDDK
Common Name (eg, fully qualified host name) []:pico5.niddk.nih.gov
Email Address []:schotte@nih.gov

Author: Friedrich Schotte
Date created: 2019-11-26
Date last modified: 2020-07-09
Revision comment: Dynamic port number if port number in use

Python version: 2.7 and 3.7
"""
__version__ = "1.12"

from logging import debug,info,warning,error
import traceback

class TCP_Server(object):    
    def __init__(self,
        ip_address_and_port_db="server.ip_address",
        globals=None,
        locals=None,
        idle_timeout=1,
        idle_callback=None
        ):
        """
        name: defines data base entry for port number
        globals: passed on to 'eval' or 'exec' when processing commands
        locals:  passed on to 'eval' or 'exec' when processing commands
        idle_timeout: wait time for idle_callback in s
        """
        self.ip_address_and_port_db = ip_address_and_port_db
        self.globals = globals
        self.locals = locals
        self.idle_callbacks = []
        if idle_callback is not None: self.idle_callbacks += [idle_callback]
        self.idle_timeout = idle_timeout
        self.nominal_port = 0
        self.listening_port = 0

    def get_protocol(self):
        """'tcp' or 'ssl'"""
        ip_address_and_port = self.ip_address_and_port
        protocol = 'tcp'
        if ip_address_and_port.startswith("ssl:"): protocol = 'ssl'
        if ip_address_and_port.startswith("tcp:"): protocol = 'tcp'
        return protocol
    protocol = property(get_protocol)

    def get_certfile(self):
        ip_address_and_port = self.ip_address_and_port
        ip_address_and_port = ip_address_and_port.replace("ssl:","")
        ip_address_and_port = ip_address_and_port.replace("tcp:","")
        ip_address_and_port = ip_address_and_port.replace("//","")
        if not "@" in ip_address_and_port:
            ip_address_and_port = "servers:servers@"+ip_address_and_port
        cert_key = ip_address_and_port.split("@")[0]
        cert = cert_key.split(":")[0]
        certfile = self.cert_dir+"/"+cert+".pem"
        from os.path import exists
        if not exists(certfile): warning("file %r not found" % certfile)
        return certfile
    certfile = property(get_certfile)

    def get_keyfile(self):
        ip_address_and_port = self.ip_address_and_port
        ip_address_and_port = ip_address_and_port.replace("ssl:","")
        ip_address_and_port = ip_address_and_port.replace("tcp:","")
        ip_address_and_port = ip_address_and_port.replace("//","")
        if not "@" in ip_address_and_port:
            ip_address_and_port = "servers:servers@"+ip_address_and_port
        cert_key = ip_address_and_port.split("@")[0]
        if not ":" in cert_key: cert_key += ":"+cert_key
        key = cert_key.split(":")[-1]
        keyfile = self.cert_dir+"/"+key+".pem"
        from os.path import exists
        if not exists(keyfile): warning("file %r not found" % keyfile)
        return keyfile
    keyfile = property(get_keyfile)

    @property
    def cert_dir(self):
        from module_dir import module_dir
        return module_dir(self)+"/certificates"

    def get_port(self):
        ip_address_and_port = self.ip_address_and_port
        ip_address_and_port = ip_address_and_port.replace("ssl:","")
        ip_address_and_port = ip_address_and_port.replace("tcp:","")
        ip_address_and_port = ip_address_and_port.replace("//","")
        ip_address_and_port = ip_address_and_port.split("@")[-1]
        if not ":" in ip_address_and_port: ip_address_and_port += ":2000"
        port = ip_address_and_port.split(":")[1]
        try: port = int(port)
        except: port = 2000
        return port
    def set_port(self,value):
        self.ip_address_and_port = \
            self.protocol+"://"+self.keyfile+":"+self.keyfile+"@"+self.ip_address+":"+str(value)
    port = property(get_port,set_port)

    def get_ip_address(self):
        ip_address_and_port = self.ip_address_and_port
        ip_address_and_port = ip_address_and_port.replace("ssl:","")
        ip_address_and_port = ip_address_and_port.replace("tcp:","")
        ip_address_and_port = ip_address_and_port.replace("//","")
        ip_address_and_port = ip_address_and_port.split("@")[-1]
        ip_address = ip_address_and_port.split(":")[0]
        return ip_address
    ip_address = property(get_ip_address)

    def get_ip_address_and_port(self):
        from DB import db
        default_value = "localhost:2000"
        return db(self.ip_address_and_port_db,default_value)
    def set_ip_address_and_port(self,value):
        from DB import dbset
        dbset(self.ip_address_and_port_db,value)
    ip_address_and_port = property(get_ip_address_and_port,set_ip_address_and_port)

    from thread_property_2 import thread_property

    def start(self): self.running = True
    def stop(self): self.running = False

    @thread_property
    def running(self):
        self.run()

    def run(self):
        try:
            self.nominal_port = 0
            clients = []
            self.running_cancelled = False
            while not self.running_cancelled:
                if self.nominal_port != self.port:
                    from socket import socket,AF_INET,SOCK_STREAM,SOL_SOCKET,SO_REUSEADDR
                    listening_socket = socket(AF_INET,SOCK_STREAM,0)
                    listening_socket.setsockopt(SOL_SOCKET,SO_REUSEADDR,1)
                    self.listening_port = self.port
                    while self.listening_port < 65536:
                        from socket import error as socket_error
                        try:
                            listening_socket.bind(("0.0.0.0",self.listening_port))
                        except socket_error:
                            warning("Port %r in use. Trying port %r instead..." 
                                % (self.listening_port,self.listening_port+1))
                            self.listening_port += 1
                        else: break
                    listening_socket.listen(20)
                    info("Started %s server %s listening on port %r." %
                        (self.protocol.upper(),__version__,self.listening_port))
                    self.nominal_port = self.port

                read_sockets = [listening_socket]+\
                    [client.socket for client in clients]
                write_sockets = \
                    [client.socket for client in clients if client.pending_replies]
                except_sockets = []

                from select import select,error as select_error
                try: ready_to_read,ready_to_write,in_error = \
                    select(read_sockets,write_sockets,except_sockets,self.idle_timeout)
                except select_error as msg:
                    if not 'Interrupted system call' in str(msg):
                        warning("select: %r" % msg)
                    ready_to_read,ready_to_write,in_error = [],[],[]

                if listening_socket in ready_to_read:
                    ##debug("Accepting connection...")
                    socket,address_port = listening_socket.accept()
                    address,port = address_port
                    address_port = "%s:%s" % (address,port)
                    debug("%s: connected" % address_port)
                    client = self.client(socket,address_port,self.protocol,self.certfile,self.keyfile)
                    if client.socket: clients += [client]

                for client in clients:
                    if client.socket in ready_to_read:
                        try:
                            input = client.socket.recv(65536)
                        except Exception as msg:
                            debug("%s: recv: %s" % (client.address_port,msg))
                            if client in clients: clients.remove(client)
                        else:
                            if len(input) > 0:
                                ##debug("%s: recv %r bytes" % (client.address_port,len(input)))
                                client.pending_input += input
                                self.process(client)
                            else: # count of zero indicates connection closed
                                debug("%s: disconnected" % address_port)
                                if client in clients: clients.remove(client)
                    if client.socket in ready_to_write:
                        n = len(client.pending_replies)
                        ##debug("%s: sending %r bytes..." % (client.address_port,n))
                        try: n = client.socket.send(client.pending_replies)
                        except Exception as x: 
                            warning("%s: send: %s" % (client.address_port,x))
                            if client in clients: clients.remove(client)
                        else:
                            if n > 0: client.pending_replies = client.pending_replies[n:]
                            ##debug("%s: sent %r bytes" % (client.address_port,n))

                if all([len(s) == 0 for s in (ready_to_read,ready_to_write,in_error)]):
                    self.handle_idle()
        except KeyboardInterrupt: pass
        info("Shutting down %s server on port %r." % (self.protocol.upper(),self.listening_port))
        self.nominal_port = 0
        self.listening_port = 0

    def process(self,client):
        while client.pending_input.find(b"\n") != -1:
            end = client.pending_input.index(b"\n")
            input = client.pending_input[0:end]
            client.pending_input = client.pending_input[end+1:]
            if input:
                ##debug("%s: recv %r" % (client.address_port,input))
                reply = self.reply(input)
                client.pending_replies += reply

    def reply(self,input):
        """Return a reply to a client process
        command: bytes (without newline termination)
        return value: bytes (without newline termination)"""
        try:
            value = eval(input,self.globals,self.locals)
        except Exception as msg:
            error_message_eval = "%r: %s\n%s" % (input,msg,traceback.format_exc())
        else:
            reply = self.bytes(value)
            error_message_eval = ""
        if error_message_eval:
            try:
                exec(input,self.globals,self.locals)
            except Exception as msg:
                error_message_exec = "%r: %s\n%s" % (input,msg,traceback.format_exc())
                error(error_message_eval)
                error(error_message_exec)
                reply = error_message_eval+error_message_exec
                reply = reply.encode("ASCII")
            else:
                info("Executed %.200r" % input)
                reply = b"\n"                
        return reply

    def bytes(self,value):
        """Format python value as string for network stransmission"""
        if isinstance(value,bytes) and len(value) > 1024: s = value
        elif isinstance(value,str) and len(value) > 1024: s = value.encode('Latin-1')
        else: s = repr(value).encode('ASCII')+b"\n"
        return s

    def handle_idle(self):
        for callback in self.idle_callbacks:
            try: callback()
            except Exception as msg: error("%s\n%s" % (msg,traceback.format_exc()))

    class client(object):
        def __init__(self,socket,address_port,protocol,certfile,keyfile):
            self.socket = socket
            self.address_port = address_port
            self.protocol = protocol
            self.certfile = certfile
            self.keyfile = keyfile
            self.pending_input = b""
            self.pending_replies = b""

            if self.protocol == "ssl":
                import ssl
                try:
                    self.socket = ssl.wrap_socket(
                        self.socket,
                        server_side=True,
                        certfile=self.certfile,
                        keyfile=self.keyfile,
                        ssl_version=ssl.PROTOCOL_TLSv1_2,
                        cert_reqs=ssl.CERT_REQUIRED,
                        ca_certs=certfile,
                    )
                except Exception as x:
                    debug("%s: %s" % (self.address_port,x))
                    from socket import error as socket_error
                    try:
                        from socket import SHUT_RDWR
                        self.socket.shutdown(SHUT_RDWR)
                    except socket_error as x:
                        debug("shutdown failed: %r: %s" % (self.address_port,x))
                    else:
                        debug("closed connection to %r" % self.address_port)
                    self.socket = None
                ##else: debug("SSL version: %r" % ssl_version(self.socket.version()))

tcp_server = TCP_Server


def ssl_version(version_id):
    version = str(version_id)
    import ssl
    for name in dir(ssl):
        if name.startswith("PROTOCOL_") and getattr(ssl,name) == version_id:
            version = name.replace("PROTOCOL_","")
    return version


if __name__ == "__main__":
    from pdb import pm
    import logging
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(funcName)s: %(message)s")

    self = TCP_Server()
    print('self.ip_address_and_port = %r' % self.ip_address_and_port)
    print('')
    print("self.ip_address_and_port = 'ssl://localhost:2000'")
    print("self.ip_address_and_port = 'tcp://localhost:2000'")
    print("self.ip_address_and_port = 'localhost:2000'")
    print('self.running = True')
    print('self.run() # Does not return. Hit Ctrl-C to end.')
    from tcp_client import query
    print('query(self.ip_address_and_port,"1+1")')
