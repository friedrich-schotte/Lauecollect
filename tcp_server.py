#!/bin/env python
"""Framework for an insturment server that comminitcates via
formatted text ASCII commands.

Author: Friedrich Schotte
Date created: Oct 18, 2016
Date last modified: Oct 19, 2017
"""
__version__ = "1.0" # 

from logging import debug,info,warn,error
 
class TCP_Server(object):
    name = "tcp_server"
    from persistent_property import persistent_property
    port = persistent_property("port",2222)
    
    def reply(self,query):
        """Return a reply to a client process
        command: string (without newline termination)
        return value: string (without newline termination)"""
        if query == "?": reply = "supported commands: ?, hello"
        elif query == "hello": reply = "Greetings, stranger!"
        else: reply = "command %r not implemented" % query
        return reply

    def get_server_running(self):
        return getattr(self.server,"active",False)
    def set_server_running(self,value):
        if self.server_running != value:
            if value: self.start_server()
            else: self.stop_server()
    server_running = property(get_server_running,set_server_running)
    
    server = None

    def start_server(self):
        # make a threaded server, listen/handle clients forever
        try:
            self.server = self.ThreadingTCPServer(("",self.port),self.ClientHandler)
            self.server.active = True
            info("%s: server version %s started, listening on port %d." % (self.name,__version__,self.port))
            from threading import Thread
            self.thread = Thread(target=self.run_server)
            self.thread.start() # Stop with: "self.server.shutdown()"
        except Exception,msg: error("%s: start_server: %r" % (self.name,msg))

    def stop_server(self):
        if getattr(self.server,"active",False):
            self.server.server_close()
            self.server.active = False

    def run_server(self):
        try: self.server.serve_forever()
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
                             except Exception,x: error("%s: %r %r" % (myself.name,x,str(x)))
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
                     error("%s: evaluating query: '%s'" % (myself.name,query))
                     try: reply = myself.reply(query)
                     except Exception,x: error("%s: %r %r" % (self.name,x,str(x))); reply = ""
                     if reply:
                         reply = reply.replace("\n","") # "\n" = end of reply
                         reply += "\n"
                         info("%s: sending reply: %r" % (myself.name,reply))
                         self.request.sendall(reply)
                 info("%s: closing connection to %s" % (myself.name,self.client_address[0]))
                 self.request.close()
        return ClientHandler
        
tcp_server = TCP_Server

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s %(levelname)s: %(message)s")
    self = TCP_Server() # for debugging
    from tcp_client import query
    print('self.port = %r' % self.port)
    print('self.server_running = True')
    print('query("localhost:%s","hello")' % self.port)
