#!/bin/env python
"""Framework for an insturment server that comminitcates via
formatted text ASCII commands.

Author: Friedrich Schotte
Date created: 2016-01-18
Date last modified: 2019-06-01
"""
__version__ = "1.0.1" # issue: debug messages too long

from logging import debug,info,warn,error
import traceback
 
class TCP_Server(object):
    name = "tcp_server"
    from persistent_property import persistent_property
    port = persistent_property("port",2222)
    
    def __init__(self,
        name=None,
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
        if name: self.name = name
        self.globals = globals
        self.locals = locals

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
                info("Executed %.200r" % input)
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

    def get_running(self):
        return getattr(self.server,"active",False)
    def set_running(self,value):
        if self.running != value:
            if value: self.start()
            else: self.stop()
    running = property(get_running,set_running)
    
    server = None

    def start(self):
        from threading import Thread
        self.thread = Thread(target=self.run)
        self.thread.start()

    def stop(self):
        if getattr(self.server,"active",False):
            self.server.server_close()
            self.server.active = False

    def run(self):
        try:
            # make a threaded server, listen/handle clients forever
            self.server = self.ThreadingTCPServer(("",self.port),self.ClientHandler)
            self.server.active = True
            info("%s: server version %s started, listening on port %d." % (self.name,__version__,self.port))
            self.server.serve_forever()
        except Exception,msg: info("%s: server: %s" % (self.name,msg))
        info("%s: server shutting down" % self.name)

    # By default, the "ThreadingTCPServer" class binds to the sever port
    # without the option SO_REUSEADDR. The consequence of this is that
    # when the server terminates you have to let 60 seconds pass, for the
    # socket to leave to "CLOSED_WAIT" state before it can be restarted,
    # otherwise the next bind call would generate the error
    # 'Address already in use'.
    # Setting allow_reuse_address to True makes "ThreadingTCPServer" use to
    # SO_REUSEADDR option when calling "bind".
    import SocketServer
    class ThreadingTCPServer(SocketServer.ThreadingTCPServer):
        allow_reuse_address = True

    @property
    def ClientHandler(self):
        myself = self
        import SocketServer
        class ClientHandler(SocketServer.BaseRequestHandler):
             def handle(self):
                 """Called when a client connects. 'self.request' is the client socket""" 
                 info("%s: accepted connection from %s" % (myself.name,self.client_address[0]))
                 import socket
                 input_queue = ""
                 while self.server.active:
                     # Commands from a client are not necessarily received as one packet
                     # but each command is terminated by a newline character.
                     # If 'recv' returns an empty string it means client closed the
                     # connection.
                     while input_queue.find("\n") == -1:
                         self.request.settimeout(1.0)
                         received = ""
                         while self.server.active:
                             try: received = self.request.recv(2*1024*1024)
                             except socket.timeout: continue
                             except Exception,msg:
                                 error("%s: %s" % (myself.name,msg))
                             if received == "": info("%s: client disconnected" % myself.name)
                             break
                         if received == "": break
                         input_queue += received
                     if input_queue == "": break
                     if input_queue.find("\n") != -1:
                         end = input_queue.index("\n")
                         query = input_queue[0:end]
                         input_queue = input_queue[end+1:]
                     else: query = input_queue; input_queue = ""
                     query = query.strip("\r ")
                     debug("%s: evaluating query: %.200r" % (myself.name,query))
                     try: reply = myself.reply(query)
                     except Exception,msg: error("%s: %s" % (myself.name,msg)); reply = ""
                     if reply:
                         reply = reply.replace("\n","") # "\n" = end of reply
                         reply += "\n"
                         debug("%s: sending reply: %.200r" % (myself.name,reply))
                         self.request.sendall(reply)
                 info("%s: closing connection to %s" % (myself.name,self.client_address[0]))
                 self.request.close()
        return ClientHandler

tcp_server = TCP_Server


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s %(levelname)s: %(message)s")
    x = 1.2
    self = TCP_Server("test",globals(),locals()) # for debugging
    from tcp_client import query
    print('self.port = %r' % self.port)
    print('self.running = True')
    print('query("localhost:%s","x")' % self.port)
