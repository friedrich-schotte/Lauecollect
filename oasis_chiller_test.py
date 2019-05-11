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

Friedrich Schotte, Nara Dashdorj, NIH, 28 May 2009 - NIH, 25 Oct 2017
"""

from struct import pack,unpack
from numpy import nan,rint
from logging import error,warn,info,debug
from persistent_property import persistent_property

__version__ = "1.9" # discover serial port

class OasisChiller(object):
    """Oasis thermoelectric chiller by Solid State Cooling Systems"""
    name = "oasis_chiller"
    timeout = 0.5
    baudrate = 9600
    id_query = "A"
    id_reply_length = 3
    
    port = None
    # Make multithread safe
    from thread import allocate_lock
    __lock__ = allocate_lock()
    
    def id_reply_valid(self,reply):
        valid = reply.startswith("A") and len(reply) == 3
        #--#debug("Reply %r valid? %r" % (reply,valid))
        return valid

    def __init__(self):
        # When read, read actual temperature, when changed, change set point.
        self.temperature = self.temperature_object(self)
        self.T = self.temperature # Define a shortcut.
        self.setT = self.nominal_temperature_object(self)

    def get_nominal_temperature(self):
        return self.get_value(1)/10.
    def set_nominal_temperature(self,value):
        return self.set_value(1,value*10)
    nominal_temperature = property(get_nominal_temperature,set_nominal_temperature)

    @property
    def actual_temperature(self):
        return self.get_value(9)/10.
    
    def get_low_limit(self):
        return self.get_value(6)/10.
    def set_low_limit(self,value):
        return self.set_value(6,value*10)
    low_limit = property(get_low_limit,set_low_limit)
    
    def get_high_limit(self):
        return self.get_value(7)/10.
    def set_high_limit(self,value):
        return self.set_value(7,value*10)
    high_limit = property(get_high_limit,set_high_limit)
    

    @property
    def faults(self):
        """Read faults table"""
        code = int("01001000",2)
        command = pack('B',code)
        reply = self.query(command,count=2)
        # The reply is 0xC8 followed by a fauts status byte.
        if len(reply) != 2: return "unresponsive"
        reply_code,bits = unpack('<BB',reply)
        if reply_code != code: return "reply not understood"
        faults = {0:"Tank Level Low",2:"Temperature above alarm range",
            4:"RTD Fault",5:"Pump Fault",7:"Temperature below alarm range"}
        info = ""
        for i in range(0,8):
            if (bits >> i) & 1:
                if i in faults: info += faults[i]+", "
                else: info += str(i)+", "
        info = info.strip(", ")
        return info

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
            warn("%r: expecting 3-byte reply, got %r" % (command,reply))
            return nan
        reply_code,count = unpack('<BH',reply)
        if reply_code != code:
            warn("%r: expecting 0xC1, got 0x%X" % (reply,code))
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

    @property
    def port_name(self):
        """Serial port name"""
        if self.port is None: value = ""
        else: value = self.port.name
        return value

    def query(self,command,count=1):
        """Send a command to the controller and return the reply"""
        with self.__lock__: # multithread safe
            for i in range(0,2):
                try: reply = self.__query__(command,count)
                except Exception,msg:
                    info("query: %r: attempt %s/2: %s" % (command,i+1,msg))
                    reply = ""
                if reply: return reply
                self.init_communications()
            return reply

    def __query__(self,command,count=1):
        """Send a command to the controller and return the reply"""
        self.write(command)
        reply = self.read(count=count)
        return reply
    
    def write(self,command):
        """Send a command to the controller"""
        if self.port is not None:
            self.port.write(command)
            #--#debug("%s: Sent %r" % (self.port.name,command))

    def read(self,count=None,port=None):
        """Read a reply from the controller,
        terminated with the given terminator string"""
        ###--#debug("read count=%r,port=%r" % (count,port))
        if port is None: port = self.port
        if port is not None:
            #--#debug("Trying to read %r bytes from %s..." % (count,port.name))
            port.timeout = self.timeout
            reply = port.read(count)
            #--#debug("%s: Read %r" % (port.name,reply))
        else: reply = ""
        return reply

    def init_communications(self):
        """To do before communncating with the controller"""
        from os.path import exists
        from serial import Serial

        if self.port is not None:
            try:
                self.port.write(self.id_query)
                #--#debug("%s: Sent %r" % (self.port.name,self.id_query))
                reply = self.read(count=self.id_reply_length)
                if not self.id_reply in reply:
                    #--#debug("%s: %r: reply %r" % (self.port.name,self.id_query,reply))
                    info("%s: lost connection" % self.port.name)
                    self.port = None 
            except Exception,msg:
                #--#debug("%s: %s" % (Exception,msg))
                self.port = None 

        if self.port is None:
            port_basenames = ["COM"] if not exists("/dev") \
                else ["/dev/tty.usbserial","/dev/ttyUSB"]
            for i in range(-1,40):
                for port_basename in port_basenames:
                    port_name = port_basename+("%d" % i if i>=0 else "")
                    ###--#debug("Trying port %s..." % port_name)
                    try: 
                        port = Serial(port_name,baudrate=self.baudrate)
                        port.write(self.id_query)
                        #--#debug("%s: Sent %r" % (port.name,self.id_query))
                        reply = self.read(count=self.id_reply_length,port=port)
                        if self.id_reply_valid(reply): 
                           self.port = port
                           info("Found port %s based on reply %r" % (self.port.name,reply))
                           break
                    except Exception,msg: pass #--#debug("%s: %s"  % (Exception,msg))
                if self.port is not None: break

    class temperature_object(object):
        """For logging and scanning, can be used as counter"""
        def __init__(self,controller):
            self.controller = controller
            self.unit = "C"
            self.name = "Chiller-T"
            self.tolerance = 0.2
            
        def get_value(self): return self.controller.actual_temperature
        def set_value(self,value): self.controller.nominal_temperature = value
        value = property(get_value,set_value)
        
        def get_moving(self):
            """Has the actual temperature not yet reached the set point within
            tolerance?"""
            return abs(self.controller.nominal_temperature -
                self.controller.actual_temperature) > self.tolerance
        def set_moving(self,value):
            """If value = False, cancel the current temperature ramp."""
            if bool(value) == False:
                self.controller.nominal_temperature = \
                    self.controller.actual_temperature
        moving = property(get_moving,set_moving)

        def stop():
            """Cancel the current temperature ramp."""
            self.moving = False

    class nominal_temperature_object(object):
        """For logging and scanning, can be used as counter"""
        def __init__(self,controller):
            self.controller = controller
            self.unit = "C"
            self.name = "Chiller-setT"
            self.tolerance = 0.2
            
        def get_value(self): return self.controller.nominal_temperature
        def set_value(self,value): self.controller.nominal_temperature = value
        value = property(get_value,set_value)
        
        def get_moving(self): return False
        def set_moving(self,value): pass
        moving = property(get_moving,set_moving)

        def stop(): pass


def binstr(n):
    """binary number representation of n"""
    s = ""
    for i in range(31,-1,-1):
        if (n >> i) & 1: s += "1"
        elif s != "": s += "0"
    return s


chiller = OasisChiller()

if __name__ == "__main__": # for testing 
    from pdb import pm
    import logging
    logging.basicConfig(level=logging.DEBUG)
    self = chiller # for debugging
    print('chiller.init_communications()')
    print("chiller.port_name")
    print("chiller.nominal_temperature")
    print("chiller.actual_temperature")
    print("chiller.low_limit")
    print("chiller.high_limit")
    print("chiller.faults")

import matplotlib.pyplot as plt
import time
chiller = OasisChiller()
print chiller.actual_temperature


print 'Nominal temperature', chiller.nominal_temperature
time_start = time.time()
y = []
x = []
target_temp = float(raw_input('Temperature?'))
while target_temp >3:     
    chiller.set_nominal_temperature(target_temp)
    if target_temp > chiller.actual_temperature:
        while chiller.actual_temperature < target_temp:
            print chiller.actual_temperature, chiller.nominal_temperature
            y.append(chiller.actual_temperature)
            x.append(time.time() - time_start)
    else:
        while chiller.actual_temperature > target_temp:
            print chiller.actual_temperature, chiller.nominal_temperature
            y.append(chiller.actual_temperature)
            x.append(time.time() - time_start)
    for i in range(1):
        y.append(chiller.actual_temperature)
        x.append(time.time() - time_start)
    target_temp = float(raw_input('Temperature?'))
import numpy as np
plt.figure(1)
plt.plot(x,y)
plt.title('Oasis from 4*C to 45*C')
plt.ylabel('Temperature, *C')
plt.xlabel('time, sec')
plt.show()

#np.savetxt('data')

