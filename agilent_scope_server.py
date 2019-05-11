from __future__ import with_statement
"""
Intermediate server for Agilent Infiniium oscilloscope.
Translate VXI-11.2 requests into simple TCP/IP transactions.
The program is intended to run on the Agilent oscilloscope PC
"id14b-scope" as auto-start program.

Friedrich Schotte, APS, 20-23 Oct 2009
"""

import SocketServer
from vxi_11 import vxi_11_connection,VXI_11_Error # also requires rpc.py
from thread import allocate_lock

__version__ = "1.1"

ip_address = "id14b-scope.cars.aps.anl.gov" # for instrument (or "localhost")
timeout = 0.5 # instrument reply timeout in seconds
port = 2000 # listen port number of this server script
# True: write complete transcript to log file, False: errors only
verbose_logging = False 

def run_server():
    # make a threaded server, listen/handle clients forever 
    server = ThreadingTCPServer(("",port),ClientHandler)
    log("server started, listening on port "+str(port))
    log("verbose logging: %r" % verbose_logging)
    server.serve_forever()

class ThreadingTCPServer(SocketServer.ThreadingTCPServer):
    # By default, the "ThreadingTCPServer" class binds to the sever port
    # without the option SO_REUSEADDR. The consequence of this is that
    # when the server terminates you have to let 60 seconds pass, for the
    # socket to leave to "CLOSED_WAIT" state before it can be restarted,
    # otherwise the next bind call would generate the error
    # 'Address already in use'.
    # Setting allow_reuse_address to True makes "ThreadingTCPServer" use to
    # SO_REUSEADDR option when calling "bind".
    allow_reuse_address = True

class ClientHandler(SocketServer.BaseRequestHandler):
     def handle(self):
         "Called when a client connects. 'self.request' is the client socket"
         addr = "%s:%d" % self.client_address
         log("%s: accepted connection" % addr)
         input_queue = ""
         while 1:
             # Commands from a client are not necessarily received as one packet
             # but each command is terminated by a newline character.
             # If 'recv' returns an empty string it means client closed the
             # connection.
             while input_queue.find("\n") == -1:
                 try: received = self.request.recv(1024)
                 except: received = "" # in case of connection reset
                 if received: log("%s: received %r" % (addr,received))
                 if received == "":
                     log ("%s: client disconnected" % addr)
                     break
                 input_queue += received
             if input_queue == "": break
             if input_queue.find("\n") != -1:
                 end = input_queue.index("\n")
                 command = input_queue[0:end]
                 input_queue = input_queue[end+1:]
             else: command = input_queue; input_queue = ""
             command = command.rstrip("\r\n")
             if command.endswith("?"):
                 log("%s: processing query %r" % (addr,command))
                 reply = query(command)
                 reply += "\n"
                 log ("%s: returning reply %r" % (addr,reply))
                 self.request.sendall(reply)
             elif command != "":
                 log("%s: sending command %r" % (addr,command))
                 write(command)
         log ("%s: closing connection" % addr)
         self.request.close()

connection = None
lock = allocate_lock()

def query(command):
    """Send a command an return the reply received."""
    with lock:
        global connection
        for attempt in range(1,3):
            try:
                if connection == None: connection = vxi_11_connection(
                    ip_address,timeout=int(timeout*1000))
                err,bytes_sent = connection.write (command)
                if err:
                    log_error("query %r attempt %d: write error %s" %
                        (command,attempt,VXI_11_Error(err)))
                    continue
                err,reason,reply = connection.read()
                if err:
                    log_error("query %r attempt %d: read error %s" %
                        (command,attempt,VXI_11_Error(err)))
                    continue
                return reply.rstrip("\n")
            except Exception,message:
                log_error("query %r attempt %d failed: %s" %
                    (command,attempt,message))
                connection = None
        return ""

def write(command):
    """Send a command an returns the reply received"""
    with lock:
        global connection
        for attempt in range(1,3):
            try:
                if connection == None: connection = vxi_11_connection(
                    ip_address,timeout=int(timeout*1000))
                err,bytes_sent = connection.write (command)
                if err:
                    log_error("write %r attempt %d: error %s" %
                        (command,attempt,VXI_11_Error(err)))
            except Exception,message:
                log_error("write %r, attempt %d, failed: %s" %
                    (command,attempt,message))
                connection = None
        return ""

def log(message):
    "Append a message to the log file (/tmp/agilent_scope_server.log)"
    from tempfile import gettempdir
    from sys import stderr
    if len(message) == 0 or message[-1] != "\n": message += "\n"
    timestamped_message = timestamp()+": "+message
    stderr.write(timestamped_message)
    if verbose_logging:
        logfile = gettempdir()+"/agilent_scope_server.log"
        try: file(logfile,"a").write(timestamped_message)
        except IOError: pass

def log_error(message):
    """Append a message to the error log file
    /tmp/agilent_scope_server_error.log.
    Also log the message the normal way.
    """
    from tempfile import gettempdir
    from sys import stderr
    if len(message) == 0 or message[-1] != "\n": message += "\n"
    if len(message) == 0 or message[-1] != "\n": message += "\n"
    timestamped_message = timestamp()+": "+message
    stderr.write(timestamped_message)
    logfile = gettempdir()+"/agilent_scope_server_error.log"
    try: file(logfile,"a").write(timestamped_message)
    except IOError: pass
    log(message)

def timestamp():
    """Current date and time as formatted ASCCI text, precise to 1 ms"""
    from datetime import datetime
    timestamp = str(datetime.now())
    return timestamp[:-3] # omit microsconds

run_server()
