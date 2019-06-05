#!/bin/env python
"""Framework for an instrument server that communicates via formatted text
ASCII commands.

Author: Friedrich Schotte
Date created: 2018-10-30
Date last modified: 2019-03-28
"""
__version__ = "1.4.1" # issue: select: interrupted system call 

from logging import debug,info,warn,error
import traceback
 
class TCP_Server(object):
    from persistent_property import persistent_property
    default_port = 2000

    def __init__(self,
        ip_address_and_port_db="server.ip_address",
        globals=None,
        locals=None,
        idle_timeout=1,
        idle_callback=None
        ):
        """
        name: defines data base entry for number
        globals: passed on to 'eval' or 'exec' when processing commands
        locals:  passed on to 'eval' or 'exec' when processing commands
        idle_timeout: wait time for idle_callback in s
        """
        self.ip_address_and_port_db = ip_address_and_port_db
        self.globals = globals
        self.locals = locals
        self.clients = []
        self.idle_callbacks = []
        if idle_callback is not None: self.idle_callbacks += [idle_callback] 
        self.idle_timeout = idle_timeout

        self.listing_port = 0

    def get_port(self):
        port = self.ip_address_and_port.split(":")[-1:][0]
        try: port = int(port)
        except: port = self.default_port
        return port
    def set_port(self,value):
        self.ip_address_and_port = self.ip_address+":"+str(value)
    port = property(get_port,set_port)

    def get_ip_address(self):
        ip_address = self.ip_address_and_port.split(":")[0:1][0]
        return ip_address
    ip_address = property(get_ip_address)

    def get_ip_address_and_port(self):
        from DB import db
        default_value = "localhost:%r" % self.default_port
        return db(self.ip_address_and_port_db,default_value)
    def set_ip_address_and_port(self,value):
        from DB import dbset
        dbset(self.ip_address_and_port_db,value)
    ip_address_and_port = property(get_ip_address_and_port,set_ip_address_and_port)

    def run(self):
        while True:
            import socket,select
            if self.listing_port != self.port:
                self.listen_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM,0)
                self.listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                try:
                    self.listen_socket.bind(("0.0.0.0",self.port))
                    self.listen_socket.listen(20)
                    debug("listening on port %r" % self.port)
                    self.listing_port = self.port
                except socket.error,msg:
                    error("bind/listen %r: %s" % (self.port,msg))
                    self.listing_port = 0

            read_sockets = [self.listen_socket]+\
                [client.socket for client in self.clients]
            write_sockets = \
                [client.socket for client in self.clients if client.pending_replies]
            except_sockets = []

            try: ready_to_read,ready_to_write,in_error = \
                select.select(read_sockets,write_sockets,except_sockets,self.idle_timeout)
            except select.error,msg:
                if not 'Interrupted system call' in str(msg):
                    warn("select: %r" % msg)
                ready_to_read,ready_to_write,in_error = [],[],[]

            if self.listen_socket in ready_to_read:
                ##debug("Accepting connection...")
                socket,address_port = self.listen_socket.accept()
                address,port = address_port
                address_port = "%s:%s" % (address,port)
                debug("%s: connected" % address_port)
                self.clients += [self.client(socket,address_port)]

            for client in self.clients:
                if client.socket in ready_to_read:
                    try:
                        input = client.socket.recv(65536)
                        if len(input) > 0:
                            ##debug("%s: recv %r bytes" % (client.address_port,len(input)))
                            client.pending_input += input
                            self.process(client)
                        else: # count of zero indicates connection closed
                            debug("%s: disconnected" % address_port)
                            self.clients.remove(client)
                    except socket.error,msg:
                        debug("%s: recv: %s" % (client.address_port,msg))
                        self.clients.remove(client)
                if client.socket in ready_to_write:
                    n = len(client.pending_replies)
                    ##debug("%s: sending %r bytes..." % (client.address_port,n))
                    n = client.socket.send(client.pending_replies)
                    if n > 0: client.pending_replies = client.pending_replies[n:]
                    ##debug("%s: sent %r bytes" % (client.address_port,n))

            if all([len(s) == 0 for s in (ready_to_read,ready_to_write,in_error)]):
                self.handle_idle()

    def process(self,client):
        while client.pending_input.find("\n") != -1:
            end = client.pending_input.index("\n")
            input = client.pending_input[0:end]
            client.pending_input = client.pending_input[end+1:]
            if input:
                ##debug("%s: recv %r" % (client.address_port,input))
                reply = self.reply(input)
                client.pending_replies += reply
   
    def reply(self,input):
        """Return a reply to a client process
        command: string (without newline termination)
        return value: string (without newline termination)"""
        try:
            value = eval(input,self.globals,self.locals)
            reply = self.string(value)
        except Exception,msg:
            error_message_eval = "%s\n%s" % (msg,traceback.format_exc())
            try:
                exec(input,self.globals,self.locals)
                reply = "\n"
            except Exception,msg:
                error_message_exec = "%s\n%s" % (msg,traceback.format_exc())
                error(error_message_eval)
                error(error_message_exec)
                reply = error_message_eval+error_message_exec
        return reply

    def string(self,value):
        """Format python value as string for network stransmission"""
        if isinstance(value,str) and len(value) > 1024: string = value
        else: string = repr(value)+"\n"
        return string

    def handle_idle(self):
        for callback in self.idle_callbacks:
            try: callback()
            except Exception,msg: error("%s\n%s" % (msg,traceback.format_exc()))

    class client(object):
        def __init__(self,socket=None,address_port=""):
            self.socket = socket
            self.address_port = address_port
            self.pending_input = ""
            self.pending_replies = ""

    
tcp_server = TCP_Server # alias

if __name__ == "__main__":
    from pdb import pm # for debugging
    import logging
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s %(levelname)s: %(message)s")
    from instrumentation import * # -> globals()
    def idle(): debug("idle")
    ip_address_and_port_db = "GigE_camera.MicroscopeCamera.ip_address"
    server = self = TCP_Server(ip_address_and_port_db=ip_address_and_port_db,
        globals=globals(),locals=locals())
    server.idle_timeout = 1.0
    ##server.idle_callbacks += [idle]
    print('self.port = %r' % self.port)
    print('Test: from tcp_client import query; print query("localhost:%s","hello")' % self.port)
    print('self.run() # does not return')
    ##self.run()
