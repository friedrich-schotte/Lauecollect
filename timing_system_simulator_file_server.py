#!/usr/bin/env python
"""
Simulated network server for communicating wit the FPGA timing system.
Author: Friedrich Schotte
Date created: 2020-05-29
Date last modified: 2020-06-03
Revision comment: Added: module logger
"""
__version__ = "1.0.1"

import logging
logger = logging.getLogger(__name__)
if not logger.level: logger.level = logging.INFO
debug   = logger.debug
info    = logger.info
warning = logger.warning
error   = logger.error

from traceback import format_exc

class File_Server(object):
    def __init__(self,file_system=None):
        from EPICS_CA.server import Server
        ##Server.stop_all() # cleanup: release listening ports
        self.server = Server()
        self.server.add_handler("2001/tcp",self.process_data_received,self.handle_disconnect)
        self.buffers = {}
        self.file_system = file_system

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__,self.file_system)

    def run(self):
        self.server.run() # returns on Control-C or Server.stop_all()
    
    def start(self): 
        self.server.start()
    
    def stop(self): 
        self.server.stop()

    def process_data_received(self,addr,data_received):
        """Break up or reassemble raw network data as received into complete
        requests
        """
        replies = b""

        if not addr in self.buffers: 
            ##debug("Client %r connected" % addr)
            self.buffers[addr] = b""

        ##debug("%r,%.80r" % (addr,data_received))
        self.buffers[addr] += data_received
        buffer = self.buffers[addr]

        if len(buffer) >= self.message_size(buffer):
            message_size = self.message_size(buffer)
            message = buffer[0:message_size]
            replies += self.process(message)
            buffer = buffer[message_size:]

        self.buffers[addr] = buffer                   
        return replies

    def handle_disconnect(self,addr):
        ##debug("Client %r disconnected" % addr)
        if addr in self.buffers: del self.buffers[addr]

    def process(self,message):
        ##debug("Got request %.80r" % message)
        reply = b""
        command = self.command(message)
        filename = self.filename(message).decode("utf-8")
        payload = self.payload(message)
        if command == b"PUT":
            self.put_file(filename,payload)
        if command == b"GET":
            content = self.get_file(filename)
            reply = (b"Content-Length: %d\n\n" % len(content))+content
        if command == b"DEL":
            self.del_file(filename)
        if command == b"EXISTS":
            content = b"%r\n" % self.exists_file(filename)
            reply = (b"Content-Length: %d\n\n" % len(content))+content
        if command == b"DIR":
            filenames = self.expand_filename_pattern(filename)
            filenames = [f.encode("utf-8") for f in filenames]
            content = b"".join([f+b"\n" for f in filenames])
            reply = (b"Content-Length: %d\n\n" % len(content))+content
        if command == b"SIZE":
            content = b"%r\n" % self.file_size(filename)
            reply = (b"Content-Length: %d\n\n" % len(content))+content
        debug("Returning reply %.80r" % reply)
        return reply
    
    def command(self,message):
        command = b""
        for line in self.header(message).splitlines()[:1]:
            if b" " in line:
                command,filename = line.split(b" ",1)
        return command

    def filename(self,message):
        filename = b""
        for line in self.header(message).splitlines()[:1]:
            if b" " in line:
                command,filename = line.split(b" ",1)
        return filename
    
    def header_size(self,message):
        header_size = 0
        separator = b"\n\n"
        if separator in message:
            header_size = message.find(separator)+len(separator)
        return header_size
         
    def payload_size(self,message):
        header = self.header(message)
        payload_size = 0
        for line in header.splitlines():
            if line.startswith(b"Content-Length: "):
                payload_size = line[len(b"Content-Length: "):]
                try: payload_size = int(payload_size)
                except: payload_size = 0
        return payload_size

    def message_size(self,message):
        return self.header_size(message)+self.payload_size(message)
     
    def header(self,message):
        return message[0:self.header_size(message)]
         
    def payload(self,message):
        return message[self.header_size(message):self.message_size(message)]
   
    def put_file(self,filename,content):
        self.file_system_operation("put_file",filename,content)

    def get_file(self,filename):
        return self.file_system_operation("get_file",filename)
     
    def del_file(self,filename):
        self.file_system_operation("del_file",filename)

    def exists_file(self,filename):
        return self.file_system_operation("exists_file",filename)

    def file_size(self,filename):
        return self.file_system_operation("file_size",filename)
    
    def expand_filename_pattern(self,filename_pattern):
        return self.file_system_operation("expand_filename_pattern",filename_pattern)
    
    def file_system_operation(self,name,filename,*args,**kwargs):
        ##debug("%s %.80r,%.80r..." % (name,filename,args))
        result = self.default_values.get(name,None)
        try: result = self.file_system.operation(name,filename,*args,**kwargs)
        except: error("%s" % format_exc())
        debug("%s %.80r,%.80r: %.80r" % (name,filename,args,result))
        return result
 
    default_values = {
        "get_file": b"",    
        "exists_file": False,    
        "file_size": 0,
        "expand_filename_pattern": [],
    }
       

if __name__ == "__main__":
    from pdb import pm
    import logging
    for handler in logging.root.handlers: logging.root.removeHandler(handler)
    format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    level = logging.DEBUG
    logging.basicConfig(level=level,format=format)
    logging.getLogger("EPICS_CA").level = logging.DEBUG

    from timing_system_simulator import timing_system_simulator
    timing_system = timing_system_simulator("LaserLab")
    file_server = File_Server(timing_system.file_system) 
    
    self = file_server
    
    print('self.run()')
    print('self.start()')
    print('self.stop()')
