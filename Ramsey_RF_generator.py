"""
Ramsay RSG1000B RF Signal Generator, controlled via RS-323 interface
See: Ramsay RSG1000B RF Signal Generator User Guide, p.10-11

Settings: 9600 baud, 8 bits, parity none, stop bits 1, flow control none
DB09 connector pin 2 = TxD, 3 = RxD, 5 = Ground

The controller accepts unterminate ASCII text commands and generates newline-
terminated ASCII text replies.

Commands:
{255 - Initiate communication by addressing device number 255 (default device
       number). Reply "\r\n". (Before that command all command with be ignored.)
GO - Get " RF ON\r\n" or " RF OFF\r\n"
O - Toggle RF on/off, reply: " "

Cabling:
"Pico8" iMac -> Prolific USB-SErial 2303 cable -> DB--9 female gender changer ->
Ramsay RSG1000B RF Signal Generator, DB-9 male serial port

Authors: Friedrich Schotte
Date created: 2018-01-22
Date last modified: 20102-06-15
Revision comment: Always initializing VAL and COMM
"""

from logging import error,warn,info,debug

__version__ = "1.0.2"

class RamseyRFDriver(object):
    """Ramsay RSG1000B RF Signal Generator"""
    name = "Ramsey_RF"
    timeout = 1.0
    baudrate = 9600
    id_query = b"{255"
    id_reply = b"\r\n"
    id_reply_length = 2

    wait_time = 0 # bewteen commands 
    last_reply_time = 0.0
        
    def id_reply_valid(self,reply):
        valid = (reply == self.id_reply)
        debug("Reply %r valid? %r" % (reply,valid))
        return valid

    # Make multithread safe
    from threading import Lock
    __lock__ = Lock()
    
    port = None

    @property
    def port_name(self):
        """Serial port name"""
        if self.port is None: value = ""
        else: value = self.port.name
        return value
    COMM = port_name

    @property
    def connected(self): return self.port is not None

    @property
    def online(self):
        if self.port is None: self.init_communications()
        online = self.port is not None
        if online: debug("Device online")
        else: warn("Device offline")
        return online

    def query(self,command,count=None):
        """Send a command to the controller and return the reply"""
        with self.__lock__: # multithread safe
            for i in range(0,2):
                try: reply = self.__query__(command,count=count)
                except Exception as msg:
                    warn("query: %r: attempt %s/2: %s" % (command,i+1,msg))
                    reply = b""
                if reply: return reply
                self.init_communications()
            return reply

    def __query__(self,command,count=None):
        """Send a command to the controller and return the reply"""
        from time import time
        from sleep import sleep
        sleep(self.last_reply_time + self.wait_time - time())
        self.write(command)
        reply = self.read(count=count)
        self.last_reply_time = time()
        return reply

    def write(self,command):
        """Send a command to the controller"""
        if self.port is not None:
            self.port.write(command)
            debug("%s: Sent %r" % (self.port.name,command))

    def read(self,count=None,port=None):
        """Read a reply from the controller,
        count: from non-terminated replies: number of bytes expected
        If count is None, a newline or carriage return is expected to 
        terminate the reply"""
        ##debug("read count=%r,port=%r" % (count,port))
        if port is None: port = self.port
        if port is not None:
            port.timeout = self.timeout
            if count:
                #print("in wait:" + str(self.port.inWaiting()))
                debug("Trying to read %r bytes from %s..." % (count,port.name))
                reply = port.read(count)
            else:
                debug("Expecting newline terminated reply from %s..." % (port.name))
                reply = port.readline()
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
            except Exception as msg:
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
                    except Exception as msg: debug("%s: %s" % (Exception,msg))
                if self.port is not None: break

    def get_RF_on(self):
        """Is radiofrequency output enabled?"""
        debug("Reading radiofrequency output state")
        reply = self.query(b"GO") # ' RF OFF\r\n'
        value = b"RF ON" in reply
        if not b"RF " in reply:
            warn("Reading radiofrequency output state unreadable")
            from numpy import nan
            value = nan
        return value
    def set_RF_on(self,value):
        if value != self.RF_on: self.query(b"O",count=1)
    RF_on = property(get_RF_on,set_RF_on)
    VAL = RF_on
        
Ramsey_RF_driver = RamseyRFDriver()


class RamseyRF_IOC(object):
    name = "Ramsey_RF_IOC"
    from persistent_property import persistent_property
    prefix = persistent_property("prefix","NIH:RF")
    SCAN = persistent_property("SCAN",1.0)
    running = False

    def get_EPICS_enabled(self):
        return self.running
    def set_EPICS_enabled(self,value):
        from thread import start_new_thread
        if value:
            if not self.running: start_new_thread(self.run,())
        else: self.running = False
    EPICS_enabled = property(get_EPICS_enabled,set_EPICS_enabled)

    def run(self):
        """Run EPICS IOC"""
        from CAServer import casput,casmonitor,casdel
        from numpy import isfinite,nan
        from time import time
        from sleep import sleep
        self.running = True
        casput(self.prefix+".SCAN",self.SCAN)
        casput(self.prefix+".DESC","State")
        casput(self.prefix+".EGU","")
        casput(self.prefix+".VAL",nan)
        casput(self.prefix+".COMM","")
        # Monitor client-writable PVs.
        casmonitor(self.prefix+".SCAN",callback=self.monitor)
        casmonitor(self.prefix+".VAL",callback=self.monitor)
        was_online = False
        while self.running:
            if self.SCAN > 0 and isfinite(self.SCAN):
                SCAN = self.SCAN
                online = Ramsey_RF_driver.online
                if online:
                    if online and not was_online:
                        info("Reading configuration...")
                        casput(self.prefix+".COMM",Ramsey_RF_driver.COMM)
                        casput(self.prefix+".SCANT",nan)
                    t = time()
                    casput(self.prefix+".VAL",float(Ramsey_RF_driver.VAL))
                    sleep(t+1.0*SCAN-time())
                    casput(self.prefix+".SCANT",time()-t) # post actual scan time for diagnostics
                else:
                    casput(self.prefix+".VAL",nan)
                    sleep(SCAN)
                was_online = online 
            else:
                casput(self.prefix+".SCANT",nan)
                sleep(0.1)
        casdel(self.prefix)

    def monitor(self,PV_name,value,char_value):
        """Process PV change requests"""
        from CAServer import casput
        info("%s = %r" % (PV_name,value))
        if PV_name == self.prefix+".SCAN":
            self.SCAN = float(value)
            casput(self.prefix+".SCAN",self.SCAN)
        if PV_name == self.prefix+".VAL":
            Ramsey_RF_driver.VAL = float(value)
            casput(self.prefix+".VAL",float(Ramsey_RF_driver.VAL))

Ramsey_RF_IOC = RamseyRF_IOC()

def run_IOC():
    """Serve the Ensemble IPAQ up on the network as EPICS IOC"""
    import logging
    from tempfile import gettempdir
    logfile = gettempdir()+"/Ramsey_RF.log"
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s %(levelname)s: %(message)s",
        filename=logfile,
    )
    Ramsey_RF_IOC.run()


def alias(name):
    """Make property given by name be known under a different name"""
    def get(self): return getattr(self,name)
    def set(self,value): setattr(self,name,value)
    return property(get,set)

from EPICS_motor import EPICS_motor
class RamseyRF(EPICS_motor):
    """Thermoelectric water cooler"""
    command_value = alias("VAL") # EPICS_motor.command_value not changable
    port_name = alias("COMM")
    prefix = alias("__prefix__") # EPICS_motor.prefix not changable
    RF_on = alias("VAL") # for backward compatbility 

Ramsey_RF_generator = RamseyRF(prefix="NIH:RF",name="Ramsey_RF")


def binstr(n):
    """binary number representation of n"""
    s = ""
    for i in range(31,-1,-1):
        if (n >> i) & 1: s += "1"
        elif s != "": s += "0"
    return s

if __name__ == "__main__": # for testing 
    from sys import argv
    if "run_IOC" in argv: run_IOC()
    from pdb import pm
    import logging
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(module)s, line %(lineno)d: %(message)s")
    self = Ramsey_RF_driver # for debugging
    print('Ramsey_RF_driver.init_communications()')
    print("Ramsey_RF_driver.port_name")
    print("Ramsey_RF_driver.RF_on")
    print("Ramsey_RF_IOC.run()")
    print("run_IOC()")
