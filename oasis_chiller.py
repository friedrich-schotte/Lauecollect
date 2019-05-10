"""
Remote control of thermoelectric chiller by Solid State Cooling Systems,
www.sscooling.com, via RS-323 interface
Model: Oasis 160
See: Oasis Thermoelectric Chiller Manual, Section 7 "Oasis RS-232
communication", p. 15-16

Settings: 9600 baud, 8 bits, parity none, stop bits 1, flow control none
DB09 connector pin 2 = TxD, 3 = RxD, 5 = Ground

The controller accepts binary commands and generates binary replies.
Commands are have the length of one to three bytes.
Replies have a length of either one or two bytes, depending on the command.

Command byte: bit 7: remote control active (1 = remote control,0 = local control)
              bit 6  remote on/off (1 = Oasis running, 0 = Oasis in standby mode)
              bit 5: communication direction (1 = write,0 = read)
              bits 4-0: 00001: [1] Set-point temperature (followed by 2 bytes: temperature in C * 10)
                        00110: [6] Temperature low limit (followed by 2 bytes: temperature in C * 10)
                        00111: [7] Temperature high limit(followed by 2 bytes: temperature in C * 10)
                        01000: [8] Faults (followed by 1 byte)
                        01001: [9] Actual temperature (followed by 2 bytes: temperature in C * 10)

The 2-byte value is a 16-bit binary number enoding the temperature in units
of 0.1 degrees Celsius (range 0-400 for 0-40.0 C)

The fault byte is a bit map (0 = OK, 1 = Fault):
bit 0: Tank Level Low
bit 2: Temperature above alarm range
bit 4: RTD Fault
bit 5: Pump Fault
bit 7: Temperature below alarm range

Undocumented commands:
C6:       Receive the lower limit. (should receive back C6 14 00)
E6 14 00: Set set point low limit to 2C
C7:       Receive the upper limit. (should receive back C7 C2 01)
E7 C2 01: Set set point high limit to 45C
E-mail by John Kissam <jkissam@sscooling.com>, May 31, 2016,
"RE: Issue with Oasis 160 (S/N 8005853)"

Cabling:
"NIH-Instrumentation" MacBook Pro -> 3-port USB hub ->
"ICUSB232 SM3" UBS-Serial cable -> Oasis chiller

Setup to run IOC:
Windows 7 > Control Panel > Windows Firewall > Advanced Settings > Inbound Rules
> New Rule... > Port > TCP > Specific local ports > 5064-5070
> Allow the connection > When does the rule apply? Domain, Private, Public
> Name: EPICS CA IOC
Inbound Rules > python > General > Allow the connection
Inbound Rules > pythonw > General > Allow the connection

Authors: Friedrich Schotte, Nara Dashdorj
Date created: 2009-05-28
Date last modified: 2018-10-15 Valentyn Stadnytskyi
"""

from struct import pack,unpack
from numpy import nan,rint,isnan
from logging import error,warn,info,debug

__version__ = "2.1" # fault code

class OasisChillerDriver(object):
    """Oasis thermoelectric chiller by Solid State Cooling Systems"""
    name = "oasis_chiller"
    timeout = 1.0
    baudrate = 9600
    id_query = "A"
    id_reply_length = 3

    wait_time = 0 # bewteen commands 
    last_reply_time = 0.0
        
    def id_reply_valid(self,reply):
        valid = reply.startswith("A") and len(reply) == 3
        debug("Reply %r valid? %r" % (reply,valid))
        return valid

    # Make multithread safe
    from thread import allocate_lock
    __lock__ = allocate_lock()
    
    port = None

    def get_nominal_temperature(self):
        """Temperature set point"""
        debug("Getting nominal temperature...")
        value = self.get_value(1)/10.
        if not isnan(value): debug("Nominal temperature %r C" % value)
        else: warn("Nominal temperature unreadable")
        return value
    
    def set_nominal_temperature(self,value): self.set_value(1,value*10)
    nominal_temperature = property(get_nominal_temperature,set_nominal_temperature)
    VAL = nominal_temperature

    @property
    def actual_temperature(self):
        """Temperature read value"""
        debug("Getting actual temperature...")
        value = self.get_value(9)/10.
        if not isnan(value): debug("Actual temperature %r C" % value)
        else: warn("Actual temperature unreadable")
        return value
    RBV = actual_temperature
    
    def get_low_limit(self):
        """Not supported early firmware (serial number 1)"""
        info("Getting low limit...")
        value = self.get_value(6)/10.
        if not isnan(value): info("Low limit %r C" % value)
        else: warn("Low limit unreadable (old firmware?)")
        return value
    def set_low_limit(self,value): self.set_value(6,value*10)
    low_limit = property(get_low_limit,set_low_limit)
    LLM = low_limit
    
    def get_high_limit(self):
        """Not supported early firmware (serial number 1)"""
        info("Getting high limit...")
        value = self.get_value(7)/10.
        if not isnan(value): info("High limit %r C" % value)
        else: warn("High limit unreadable (old firmware?)")
        return value
    def set_high_limit(self,value): self.set_value(7,value*10)
    high_limit = property(get_high_limit,set_high_limit)
    HLM = high_limit
    
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

    @property
    def fault_code(self):
        """Report faults as number
        bit 0: Tank Level Low
        bit 2: Temperature above alarm range
        bit 4: RTD Fault
        bit 5: Pump Fault
        bit 7: Temperature below alarm range
        """
        from numpy import nan
        debug("Getting faults...")
        code = int("01001000",2)
        command = pack('B',code)
        reply = self.query(command,count=2)
        fault_code = nan
        # The reply is 0xC8 followed by a faults status byte.
        if len(reply) != 2:
            if len(reply)>0:
                warn("%r: expecting 2-byte reply, got %r" % (command,reply))
            elif self.connected:
                warn("%r: expecting 2-byte reply, got no reply" % command)
        else:
            reply_code,fault_code = unpack('<BB',reply)
            if reply_code != code:
                warn("reply %r: expecting 0x%X(%s), got 0x%X(%s)" %
                     (reply,code,bin(code),reply_code,bin(reply_code)))
                fault_code = nan
        if fault_code == 2.0**7:
            fault_code = 8
        elif fault_code == 2.0**6:
            fault_code = 7
        elif fault_code == 2.0**5:
            fault_code = 6
        elif fault_code == 2.0**4:
            fault_code = 5
        elif fault_code == 2.0**3:
            fault_code = 4
        elif fault_code == 2.0**2:
            fault_code = 3
        elif fault_code == 2.0**1:
            fault_code = 2
        elif fault_code == 2.0**0:
            fault_code = 1
        elif fault_code == 0:
            fault_code = 0
        else:
            fault_code = -1
        debug("Fault code %s" % fault_code)
        return fault_code

    @property
    def faults(self):
        """Report list of faults as string"""
        debug("Getting faults...")
        code = int("01001000",2)
        command = pack('B',code)
        reply = self.query(command,count=2)
        faults = " "
        # The reply is 0xC8 followed by a faults status byte.
        if len(reply) != 2:
            if len(reply)>0:
                warn("%r: expecting 2-byte reply, got %r" % (command,reply))
            elif self.connected:
                warn("%r: expecting 2-byte reply, got no reply" % command)
        else:
            reply_code,bits = unpack('<BB',reply)
            if reply_code != code:
                warn("reply %r: expecting 0x%X(%s), got 0x%X(%s)" %
                     (reply,code,bin(code),reply_code,bin(reply_code)))
            else:
                fault_names = {0:"Tank Level Low",2:"Temperature above alarm range",
                    4:"RTD Fault",5:"Pump Fault",7:"Temperature below alarm range"}
                faults = ""
                for i in range(0,8):
                    if (bits >> i) & 1:
                        if i in fault_names: faults += fault_names[i]+", "
                        else: faults += str(i)+", "
                faults = faults.strip(", ")
                if faults == "": faults = "none"
        debug("Faults %s" % faults)
        return faults

    def get_value(self,parameter_number):
        """Read a 16-bit value
        parameter_number: 1-15 (1=set point, 6=low limit, 7=high limit, 9=coolant temp.)
        """
        code = int("01000000",2) | parameter_number
        command = pack('B',code)
        reply = self.query(command,count=3)
        # The reply is 0xC1 followed by 1 16-bit binary count on little-endian byte
        # order. The count is the temperature in degrees Celsius, times 10.
        if len(reply) != 3:
            if len(reply)>0:
                warn("%r: expecting 3-byte reply, got %r" % (command,reply))
            elif self.connected:
                warn("%r: expecting 3-byte reply, got no reply" % command)
            return nan
        reply_code,count = unpack('<BH',reply)
        if reply_code != code:
            warn("reply %r: expecting 0x%X(%s), got 0x%X(%s)" %
                 (reply,code,bin(code),reply_code,bin(reply_code)))
            return nan
        return count

    def set_value(self,parameter_number,value):
        """Set a 16-bit value"""
        code = int("01100000",2) | parameter_number
        command = pack('<BH',code,int(rint(value)))
        reply = self.query(command,count=1)
        if len(reply) != 1:
            warn("expecting 1, got %d bytes" % len(reply)); return
        reply_code, = unpack('B',reply)
        if reply_code != code: warn("expecting 0x%X, got 0x%X" % (code,reply_code))

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

oasis_chiller_driver = OasisChillerDriver()


class OasisChiller_IOC(object):
    name = "oasis_chiller_IOC"
    from persistent_property import persistent_property
    prefix = persistent_property("prefix","NIH:CHILLER")
    SCAN = persistent_property("SCAN",0.5)
    running = False
    last_valid_reply = 0
    was_online = False

    def get_EPICS_enabled(self):
        return self.running
    def set_EPICS_enabled(self,value):
        from thread import start_new_thread
        if value:
            if not self.running: start_new_thread(self.run,())
        else: self.running = False
    EPICS_enabled = property(get_EPICS_enabled,set_EPICS_enabled)

    def start(self):
        """Run EPCIS IOC in background"""        
        from threading import Thread
        task = Thread(target=self.run,name="oasis_chiller_IOC.run")
        task.daemon = True
        task.start()

    def run(self):
        """Run EPICS IOC"""
        self.startup()
        self.running = True
        while self.running: self.update_once()
        self.shutdown()

    def startup(self):
        from CAServer import casput,casmonitor
        from numpy import nan
        casput(self.prefix+".SCAN",self.SCAN)
        casput(self.prefix+".DESC","Temp")
        casput(self.prefix+".EGU","C")
        # Set defaults
        casput(self.prefix+".VAL",nan)
        casput(self.prefix+".RBV",nan)
        casput(self.prefix+".LLM",nan)        
        casput(self.prefix+".HLM",nan)        
        casput(self.prefix+".faults"," ")
        casput(self.prefix+".fault_code",0)
        casput(self.prefix+".COMM"," ")
        casput(self.prefix+".SCANT",nan)
        # Monitor client-writable PVs.
        casmonitor(self.prefix+".SCAN",callback=self.monitor)
        casmonitor(self.prefix+".VAL",callback=self.monitor)
        casmonitor(self.prefix+".LLM",callback=self.monitor)
        casmonitor(self.prefix+".HLM",callback=self.monitor)

    def update_once(self):
        from CAServer import casput
        from numpy import isfinite,isnan,nan
        from time import time
        from sleep import sleep
        if self.SCAN > 0 and isfinite(self.SCAN):
            SCAN = self.SCAN
            online = oasis_chiller_driver.online
            if online:
                if online and not self.was_online:
                    info("Reading configuration...")
                    casput(self.prefix+".COMM",oasis_chiller_driver.COMM)
                    casput(self.prefix+".VAL",oasis_chiller_driver.VAL)
                    casput(self.prefix+".RBV",oasis_chiller_driver.RBV)
                    casput(self.prefix+".fault_code",oasis_chiller_driver.fault_code)
                    casput(self.prefix+".faults",oasis_chiller_driver.faults+" ")
                    casput(self.prefix+".LLM",oasis_chiller_driver.LLM)
                    casput(self.prefix+".HLM",oasis_chiller_driver.HLM)
                    casput(self.prefix+".SCANT",nan)
                t = time()
                RBV = oasis_chiller_driver.RBV
                if not isnan(RBV): self.last_valid_reply = time()
                casput(self.prefix+".RBV",RBV)
                sleep(t+0.25*SCAN-time())
                casput(self.prefix+".VAL",oasis_chiller_driver.VAL)
                sleep(t+0.5*SCAN-time())
                casput(self.prefix+".fault_code",oasis_chiller_driver.fault_code)
                sleep(t+0.75*SCAN-time())
                casput(self.prefix+".faults",oasis_chiller_driver.faults+" ")
                sleep(t+1.00*SCAN-time())
                casput(self.prefix+".SCANT",time()-t) # post actual scan time for diagnostics
            else: sleep(SCAN)
            self.was_online = online 
        else:
            casput(self.prefix+".SCANT",nan)
            sleep(0.1)
            
    def shutdown(self):
        from CAServer import casdel
        casdel(self.prefix)

    def monitor(self,PV_name,value,char_value):
        """Process PV change requests"""
        from CAServer import casput
        info("%s = %r" % (PV_name,value))
        if PV_name == self.prefix+".SCAN":
            self.SCAN = float(value)
            casput(self.prefix+".SCAN",self.SCAN)
        if PV_name == self.prefix+".VAL":
            oasis_chiller_driver.VAL = float(value)
            casput(self.prefix+".VAL",oasis_chiller_driver.VAL)
        if PV_name == self.prefix+".LLM":
            oasis_chiller_driver.LLM = float(value)
            casput(self.prefix+".LLM",oasis_chiller_driver.LLM)
        if PV_name == self.prefix+".HLM":
            oasis_chiller_driver.HLM = float(value)
            casput(self.prefix+".HLM",oasis_chiller_driver.HLM)

oasis_chiller_IOC = OasisChiller_IOC()

def run_IOC():
    """Serve the Ensemble IPAQ up on the network as EPICS IOC"""
    import logging
    from tempfile import gettempdir
    logfile = gettempdir()+"/oasis_chiller.log"
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s %(levelname)s: %(message)s",
        filename=logfile,
    )
    oasis_chiller_IOC.run()


def alias(name):
    """Make property given by name be known under a different name"""
    def get(self): return getattr(self,name)
    def set(self,value): setattr(self,name,value)
    return property(get,set)

from EPICS_motor import EPICS_motor
class OasisChiller(EPICS_motor):
    """Thermoelectric water cooler"""
    command_value = alias("VAL") # EPICS_motor.command_value not changable
    port_name = alias("COMM")
    prefix = alias("__prefix__") # EPICS_motor.prefix not changable
    nominal_temperature = alias("VAL") # for backward compatbility 
    actual_temperature = alias("RBV") # for backward compatbility 

oasis_chiller = OasisChiller(prefix="NIH:CHILLER",name="oasis_chiller")
chiller = oasis_chiller # for backward compatbility


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
    from numpy import nan
    import CAServer
    from CAServer import casput,casmonitor,PVs,PV_info
    CAServer.DEBUG = True
    logging.basicConfig(level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s")
    self = oasis_chiller_IOC # for debugging
    PV_name = "NIH:CHILLER.VAL"
    ##print('oasis_chiller_driver.init_communications()')
    ##print("oasis_chiller_driver.port_name")
    print("oasis_chiller_driver.nominal_temperature = 40")
    print("oasis_chiller_driver.nominal_temperature = 5")
    ##print("oasis_chiller_driver.actual_temperature")
    ##print("oasis_chiller_driver.low_limit")
    ##print("oasis_chiller_driver.high_limit")
    print("oasis_chiller_driver.fault_code")
    print("oasis_chiller_driver.faults")
    ##print('CAServer.DEBUG = %r' % CAServer.DEBUG)
    print('oasis_chiller_IOC.run()')
    print('oasis_chiller_IOC.start()')
    print("oasis_chiller.fault_code")
    print("oasis_chiller.faults")
    ##print('oasis_chiller_IOC.startup()')
    ##print('oasis_chiller_IOC.update_once()')
    ##print('casput(self.prefix+".VAL",nan)')
    ##print('casmonitor(self.prefix+".VAL",callback=self.monitor)')
    ##print('CAServer.start_server()')
    ##rint('CAServer.PVs[PV_name] = CAServer.PV_info()')
    ##print('CAServer.PVs')
    ##print("run_IOC()")
