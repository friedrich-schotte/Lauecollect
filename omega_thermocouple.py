"""
Omega UTC-USB Thermocouple Reader

Friedrich Schotte, 27 Apr 2016 - 22 Mar 2017

Communication Paramters: 38400 baud, 8 data bits, 1 stop bit, parity: none

The controller accepts ASCII text commands. Each command needs to by terminated
by a carriage return character, which may be followed by an optional newline.
Replies are terminated with carriage return, newline and an ">" (prompt
for the next command).

Commands:
ENQ       - Report identification, expecting: "UTCUSB2\r\n090712\r\n"
F         - Report the probe temperature in degress Fahrenheit, expecting "80\r\n" 
C         - Report the probe temperature in degress Celsius, expecting "27\r\n" 
PA        - Report probe and ambient temperatures in degrees Fahrenheit,
            expecting "257, 105 \r\n"
TCTYPE T  - Set thermocouple type to "T", expecting "TC = T\r\n"
            Supported types: B,C,E,J,K,N,R,S,T
            (This setting is retained after power cycling.)
TCTYPE    - Report Themocouple type, expecting "TC = T\r\n"
MFILTER 0 - Set moving average filter to 0, expecting "M = 0\r\n"
            Range 0 to 63
            (This setting is retained after power cycling.)
MFILTER   - Report moving average filter, expecting "M = 0\r\n"
IFILTER 0 - Set IIR (Infinite Impulse Response) filter, expecting "I = 0\r\n"
            Range 0 to 255, 0 = disabled.
            (This setting is retained after power cycling.)
IFILTER   - Report IIR (Infinite Impulse Response), expecting "I = 0\r\n"

Performance:
The controller replies to a query "F" reading the temperature within 120 ms,
when idle. However, when polled continuouly, it processes only 4 queries per
seconds.

Source:
"UTC-USB Command Reference"
ftp://ftp.omega.com/public/DASGroup/products/UTC-USB/UTC_USB-Command_Reference.pdf

Setup:
Install pyserial module: pip install pyserial

USB-serial interface:
FDTI (Future Technology Devices International) FT232 Serial (UART) IC
VID=0x0403, PID=0x6001

Windows driver details:
ftser2k.sys 4/10/2016, ftcserco.dll 2.01.03.1, ftserui.dll 2.12.2
ftser2k.sys 2.12.0, ftcserco.dll 2.01.03.1, ftserui.dll 2.12.0
"""
from logging import error,warn,debug,info
from persistent_property import persistent_property

__version__ = "1.4" # optimized IOC

class Thermocouple(object):
    """Omega UTC-USB Thermocouple Reader"""
    name = "thermocouple"
    id_query = "ENQ\r"
    id_reply = "UTCUSB2"
    terminator = "\r\n>"
    baudrate = persistent_property("baudrate",38400)
    timeout = persistent_property("timeout",1.0)
    verbose_logging = True
    logging = False

    port = None

    def __init__(self):
        # Make multithread safe
        from threading import Lock
        self.__lock__ = Lock()

    @property
    def id(self): return self.query(self.id_query)

    @property
    def T(self):
        """Temperature in degrees Celsius"""
        return (self.TF-32)/1.8
    VAL = T

    @property
    def TF(self):
        """Temperature in degrees Fahrenheit"""
        from numpy import nan
        reply = self.query("F")
        try: value = eval(reply)
        except: value = nan
        return value

    def get_MFILTER(self):
        """Moving average filter setting (range 0-63)"""
        from numpy import nan
        reply = self.query("MFILTER") # reply: "M = 0"
        try: value = eval(reply.replace("M = ",""))
        except: value = nan
        return value
    def set_MFILTER(self,value): self.query("MFILTER %r" % value)
    MFILTER = property(get_MFILTER,set_MFILTER)
        
    def get_IFILTER(self):
        """IIR (Infinite Impulse Response) filter setting (range 0-63)"""
        from numpy import nan
        reply = self.query("IFILTER") # reply: "I = 0"
        try: value = eval(reply.replace("I = ",""))
        except: value = nan
        return value
    def set_IFILTER(self,value): self.query("IFILTER %r" % value)
    IFILTER = property(get_IFILTER,set_IFILTER)

    def get_TCTYPE(self):
        """Thermocouple type (B,C,E,J,K,N,R,S,T)'"""
        from numpy import nan
        reply = self.query("TCTYPE") # reply: "TC = 0"
        value = reply.replace("TC = ","")
        return value
    def set_TCTYPE(self,value): self.query("TCTYPE %s" % value)
    TCTYPE = property(get_TCTYPE,set_TCTYPE)

    @property
    def COMM(self):
        """Serial port name"""
        if self.port is None: value = ""
        else: value = self.port.name
        return value

    def query(self,command):
        """Send a command to the controller and return the reply"""
        with self.__lock__: # multithread safe
            for i in range(0,2):
                try: reply = self.__query__(command)
                except Exception as msg:
                    info("query: %r: attempt %s/2: %s" % (command,i+1,msg))
                    reply = ""
                if reply: return reply
                self.init_communications()
            return reply

    def __query__(self,command):
        """Send a command to the controller and return the reply"""
        if not (command.endswith("\n") or command.endswith("\r")):
            command = command+"\r"
        self.write(command)
        reply = self.read()
        if self.terminator in reply: reply = reply[0:reply.index(self.terminator)]
        return reply

    def write(self,command):
        """Send a command to the controller"""
        if self.port is not None:
            self.port.write(command)
            self.log_comm("%s: Sent %r" % (self.port.name,command))

    def read(self,port=None):
        """Read a reply from the controller,
        terminated with the given terminator string"""
        if port is None: port = self.port
        if port is not None:
            from time import time
            t0 = time()
            port.timeout = 0.001
            reply = ""
            while not self.terminator in reply and time()-t0 < self.timeout:
                s = port.read(256)
                reply += s
            port.timeout = self.timeout
            self.log_comm("%s: Read %r" % (port.name,reply))
        else: reply = ""
        return reply

    def init_communications(self):
        """To do before communncating with the controller"""
        from os.path import exists
        from serial import Serial

        if self.port is not None:
            try:
                self.port.write(self.id_query)
                debug("%s: Sent %r" % (self.port.name,self.id_query))
                reply = self.read()
                if not self.id_reply in reply:
                    debug("%s: %r: reply %r" % (self.port.name,self.id_query,reply))
                    info("%s: lost connection" % self.port.name)
                    self.port = None 
            except Exception as msg:
                debug("%s: %s" % (Exception,msg))
                self.port = None 

        if self.port is None:
            port_basenames = ["COM"] if not exists("/dev") \
                else ["/dev/tty.usbserial","/dev/ttyUSB"]
            for i in range(-1,20):
                for port_basename in port_basenames:
                    port_name = port_basename+("%d" % i if i>=0 else "")
                    debug("Trying port %s..." % port_name)
                    try: 
                        port = Serial(port_name,baudrate=self.baudrate)
                        port.write(self.id_query)
                        debug("%s: Sent %r" % (port.name,self.id_query))
                        reply = self.read(port)
                        if self.id_reply in reply: 
                           self.port = port
                           info("%s: Found %r" % (self.port.name,self.id_reply))
                           break
                    except Exception as msg: debug("%s: %s" % (Exception,msg))
                if self.port is not None: break
            

    def log(self,message):
        """For non-critical messages.
        Append the message to the transcript, if verbose logging is enabled."""
        if not self.verbose_logging: return
        if len(message) == 0 or message[-1] != "\n": message += "\n"
        t = timestamp()
        file(self.logfile,"a").write("%s: %s" % (t,message))

    def log_error(self,message):
        """For error messages.
        Display the message and append it to the error log file.
        If verbose logging is enabled, it is also added to the transcript."""
        error(message)
        from sys import stderr
        if len(message) == 0 or message[-1] != "\n": message += "\n"
        t = timestamp()
        stderr.write("%s: %s" % (t,message))
        file(self.error_logfile,"a").write("%s: %s" % (t,message))
        if self.verbose_logging:
            file(self.logfile,"a").write("%s: %s" % (t,message))

    def log_comm(self,message):
        """For error messages.
        Display the message and append it to the error log file.
        If verbose logging is enabled, it is also added to the transcript."""
        info(message)
        if self.logging:
            if len(message) == 0 or message[-1] != "\n": message += "\n"
            t = timestamp()
            file(self.comm_logfile,"a").write("%s: %s" % (t,message))

    @property
    def logfile(self):
        """File name for transcript if verbose logging is enabled."""
        from tempfile import gettempdir
        return gettempdir()+"/"+self.name+".log"

    @property
    def error_logfile(self):
        """File name error messages."""
        from tempfile import gettempdir
        return gettempdir()+"/"+self.name+"_error.log"

    @property
    def comm_logfile(self):
        """File name error messages."""
        from tempfile import gettempdir
        return gettempdir()+"/"+self.name+"_comm.log"

thermocouple_driver = Thermocouple()


class Thermocouple_IOC(object):
    name = "thermocouple_IOC"
    prefix = persistent_property("prefix","NIH:TC")
    SCAN = persistent_property("SCAN",0.5)
    running = False
    last_valid_reply = 0

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
        from numpy import isfinite,isnan
        from time import time
        self.running = True
        casput(self.prefix+".SCAN",self.SCAN)
        casput(self.prefix+".DESC","Temp")
        casput(self.prefix+".EGU","C")
        # Monitor client-writable PVs.
        casmonitor(self.prefix+".SCAN",callback=self.monitor)
        casmonitor(self.prefix+".MFILTER",callback=self.monitor)
        casmonitor(self.prefix+".IFILTER",callback=self.monitor)
        casmonitor(self.prefix+".TCTYPE", callback=self.monitor)
        while self.running:
            if self.SCAN > 0 and isfinite(self.SCAN): 
                if time() - self.last_valid_reply > 10:
                    if not isnan(thermocouple_driver.VAL):
                        info("Reading configuration")
                        casput(self.prefix+".COMM",thermocouple_driver.COMM)
                        casput(self.prefix+".MFILTER",thermocouple_driver.MFILTER)
                        casput(self.prefix+".IFILTER",thermocouple_driver.IFILTER)
                        casput(self.prefix+".TCTYPE",thermocouple_driver.TCTYPE)
                t = time()
                VAL = thermocouple_driver.VAL
                if not isnan(VAL): self.last_valid_reply = time()
                casput(self.prefix+".VAL",VAL)
                sleep(t+1.00*self.SCAN-time())
                casput(self.prefix+".SCANT",time()-t) # post actual scan time for diagnostics
            else:
                casput(self.prefix+".SCANT",nan)
                sleep(0.1)
        casdel(self.prefix)

    def monitor(self,PV_name,value,char_value):
        """Process PV change requests"""
        from CAServer import casput
        debug("%s = %r" % (PV_name,value))
        if PV_name == self.prefix+".SCAN":
            self.SCAN = value
            casput(self.prefix+".SCAN",self.SCAN)
        if PV_name == self.prefix+".MFILTER":
            thermocouple_driver.MFILTER = value
            casput(self.prefix+".MFILTER",thermocouple_driver.MFILTER)
        if PV_name == self.prefix+".IFILTER":
            thermocouple_driver.IFILTER = value
            casput(self.prefix+".IFILTER",thermocouple_driver.IFILTER)
        if PV_name == self.prefix+".TCTYPE":
            thermocouple_driver.TCTYPE = value
            casput(self.prefix+".TCTYPE",thermocouple_driver.TCTYPE)

thermocouple_IOC = Thermocouple_IOC()

def sleep(seconds):
    """Delay execution by the given number of seconds"""
    # This version of "sleep" does not throw an excpetion if passed a negative
    # waiting time, but instead returns immediately.
    from time import sleep
    if seconds > 0: sleep(seconds)

def timestamp():
    """Current date and time as formatted ASCCI text, precise to 1 ms"""
    from datetime import datetime
    timestamp = str(datetime.now())
    return timestamp[:-3] # omit microsconds

def run_IOC():
    """Serve the Ensemble IPAQ up on the network as EPICS IOC"""
    ##import CAServer
    ##CAServer.register_object(thermocouple_driver, "NIH:TC")
    ##CAServer.update_interval = 0.25

    ##CAServer.verbose_logging = True
    ##CAServer.verbose = True
    ##CAServer.DEBUG = True
    ##CAServer.LOG = True
    thermocouple_driver.logging = True
    from tempfile import gettempdir
    logfile = gettempdir()+"/thermocouple_debug.log"
    import logging
    logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s",
        filename=logfile)
    thermocouple_IOC.run()

# Ensemble client, using EPICS channel access.
from CA import Record
thermocouple = Record("NIH:TC")

if __name__ == "__main__":
    from sys import argv
    if "run_IOC" in argv: run_IOC()

    # For testing
    import logging
    logging.basicConfig(level=logging.INFO,format="%(asctime)s: %(message)s")
    from time import time
    from timeit import timeit
    import __builtin__; __builtin__.__dict__.update(locals()) # needed for "timeit"
    thermocouple_driver.logging = True
    self = thermocouple_driver # for debugging
    print('run_IOC()')
    print('thermocouple.VAL')
    print('thermocouple_driver.VAL')
    print('thermocouple_driver.COMM')
    print('thermocouple_driver.MFILTER')
    print('thermocouple_driver.IFILTER')
    print('thermocouple_driver.TCTYPE')
