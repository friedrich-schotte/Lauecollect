"""

Authors: Friedrich Schotte
Date created: 2019-05-20
Date last modified: 2019-05-20
"""
__version__ = "1.0" 
from logging import error,warn,info,debug

class Serial_Device(object):
    name = "serial_device"
    timeout = 1.0
    baudrate = 9600

    # Make multithread safe
    from thread import allocate_lock
    __lock__ = allocate_lock()

    port = None

    id_query = ""
    id_reply_length = 0

    def id_reply_valid(self,reply):
        valid = len(reply) == self.id_reply_length
        debug("Reply %r valid? %r" % (reply,valid))
        return valid

    @property
    def connected(self): return self.port is not None

    @property
    def online(self):
        if self.port is None: self.init_communications()
        online = self.port is not None
        if online: debug("Device online")
        else: warn("Device offline")
        return online

    @property
    def port_name(self):
        """Serial port name"""
        if self.port is None: value = ""
        else: value = self.port.name
        return value
    COMM = port_name

    def query(self,command,count=1):
        """Send a command to the controller and return the reply"""
        with self.__lock__: # multithread safe
            for i in range(0,2):
                try: reply = self.__query__(command,count)
                except Exception,msg:
                    warn("query: %r: attempt %s/2: %s" % (command,i+1,msg))
                    reply = ""
                if reply: return reply
                self.init_communications()
            return reply

    def __query__(self,command,count=1):
        """Send a command to the controller and return the reply"""
        from time import time
        from sleep import sleep
        sleep(self.last_reply_time + self.wait_time - time())
        self.write(command)
        reply = self.read(count=count)
        self.last_reply_time = time()
        return reply

    from persistent_property import persistent_property
    wait_time = persistent_property("wait_time",1.0) # bewteen commands
    last_reply_time = 0.0

    def write(self,command):
        """Send a command to the controller"""
        if self.port is not None:
            self.port.write(command)
            debug("%s: Sent %r" % (self.port.name,command))

    def read(self,count=None,port=None):
        """Read a reply from the controller,
        terminated with the given terminator string"""
        ##debug("read count=%r,port=%r" % (count,port))
        if port is None: port = self.port
        if port is not None:
            #print("in wait:" + str(self.port.inWaiting()))
            debug("Trying to read %r bytes from %s..." % (count,port.name))
            port.timeout = self.timeout
            reply = port.read(count)
            debug("%s: Read %r" % (port.name,reply))
        else: reply = ""
        return reply

    def init_communications(self):
        """To do before communncating with the controller"""
        from os.path import exists
        from serial import Serial

        if self.port is not None:
            try:
                info("Checking whether device is still responsive...")
                self.port.write(self.id_query)
                debug("%s: Sent %r" % (self.port.name,self.id_query))
                reply = self.read(count=self.id_reply_length)
                if not self.id_reply_valid(reply):
                    debug("%s: %r: invalid reply %r" % (self.port.name,self.id_query,reply))
                    info("%s: lost connection" % self.port.name)
                    self.port = None
                else: info("Device is still responsive.")
            except Exception,msg:
                debug("%s: %s" % (Exception,msg))
                self.port = None

        if self.port is None:
            port_basenames = ["COM"] if not exists("/dev") \
                else ["/dev/tty.usbserial","/dev/ttyUSB"]
            for i in range(-1,50):
                for port_basename in port_basenames:
                    port_name = port_basename+("%d" % i if i>=0 else "")
                    ##debug("Trying port %s..." % port_name)
                    try:
                        port = Serial(port_name,baudrate=self.baudrate)
                        port.write(self.id_query)
                        debug("%s: Sent %r" % (port.name,self.id_query))
                        reply = self.read(count=self.id_reply_length,port=port)
                        if self.id_reply_valid(reply):
                           self.port = port
                           info("Discovered device at %s based on reply %r" % (self.port.name,reply))
                           break
                    except Exception,msg: debug("%s: %s" % (Exception,msg))
                if self.port is not None: break

if __name__ == "__main__":
    from pdb import pm
    import logging
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s %(levelname)s: %(message)s")

    class Oasis_Chiller_Device(Serial_Device):
        id_query = "A"
        id_reply_length = 3

        def id_reply_valid(self,reply):
            valid = reply.startswith("A") and len(reply) == 3
            debug("Reply %r valid? %r" % (reply,valid))
            return valid

    self = Oasis_Chiller_Device()
    print("self.init_communications()")
    
