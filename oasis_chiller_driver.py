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

Authors: Friedrich Schotte, Nara Dashdorj, Valentyn Stadnytskyi
Date created: 2009-05-28
Date last modified: 2018-10-15 Valentyn Stadnytskyi
"""

from struct import pack,unpack
from numpy import nan,rint,isnan
from logging import error,warn,info,debug
import sys
if sys.version[0] == '3':
    from _thread import allocate_lock
else:
    from thread import allocate_lock
__lock__ = allocate_lock()
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
    last_command_execution_time = 0.0

    # Make multithread safe


    ser = None

    def __init__(self):
        pass

    def init(self):
        self.init_communications()

    def close(self):
        self.ser.close()
        self.ser = None

    def init_communications(self):
        """To do before communncating with the controller"""
        from os.path import exists
        from serial import Serial
        import serial.tools.list_ports
        if self.ser is not None:
            try:
                info("Checking whether device is still responsive...")
                self.ser.write(self.id_query)
                debug("%s: Sent %r" % (self.ser.name,self.id_query))
                reply = self.read(count=self.id_reply_length)
                if not self.id_reply_valid(reply):
                    debug("%s: %r: invalid reply %r" % (self.ser.name,self.id_query,reply))
                    info("%s: lost connection" % self.ser.name)
                    self.ser = None
                else: info("Device is still responsive.")
            except Exception as msg:
                debug("%s: %s" % (Exception,msg))
                self.ser = None

        if self.ser is None:
            devices = serial.tools.list_ports.comports()
            debug('devices: %r' % devices)
            for item in devices:
                debug('device: %r' % item)
                try:
                    ser = Serial(item.device,baudrate=self.baudrate)
                    ser.write(self.id_query)
                    debug("%s: Sent %r" % (ser.name,self.id_query))
                    reply = self.read(count=self.id_reply_length,ser=ser)
                    if self.id_reply_valid(reply):
                       self.ser = ser
                       info("Discovered device at %s based on reply %r" % (self.ser.name,reply))
                       break
                except Exception as msg:
                    debug("%s: %s" % (Exception,msg))
                if self.ser is not None: break

    def query(self,command = None,count=1,ser = None):
        """Send a command to the controller and return the reply"""
        from time import time
        from time import sleep
        if ser is None:
            ser = self.ser

        if ser is not None:
            t1 = time()
            self.write(command)
            i = 0
            while self.waiting(ser)[0] != count:
                if i >int(self.timeout/0.015):
                    break
                sleep(0.015)
                i+=1
            reply = self.read(ser = ser,count=count)
            t2 = time()
            self.last_command_execution_time = t2-t1
            self.last_reply_time = time()
        else:
            reply = ''
        return reply

    def write(self,command,ser = None):
        """Send a command to the controller"""
        if ser is None:
            ser = self.ser
        if ser is not None:
            self.flush(ser = ser)
            ser.write(command)
            debug("%s: Sent %r" % (ser.name,command))

    def read(self,count=None, ser = None):
        """Read a reply from the controller,
        terminated with the given terminator string"""
        from time import time
        ##debug("read count=%r,ser=%r" % (count,ser))
        if ser is None:
            ser = self.ser
        if ser is not None:
            #print("in wait:" + str(self.ser.inWaiting()))
            debug("Trying to read %r bytes from %s..." % (count,ser.name))
            ser.timeout = self.timeout
            reply = ser.read(count)
            debug("%s: Read %r" % (ser.name,reply))
            self.last_reply_time = time()
        else: reply = ""
        return reply

    def flush(self, ser = None):
        if ser is not None:
            ser.flushInput()
            ser.flushOutput()

    def waiting(self, ser = None):
        if ser is None:
            ser = self.ser
        if ser is not None:
            value = (driver.ser.in_waiting,driver.ser.out_waiting)
        else:
            value = None
        return value

    def id_reply_valid(self,reply):
        valid = reply.startswith("A") and len(reply) == 3
        debug("Reply %r valid? %r" % (reply,valid))
        return valid


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
        debug("Getting low limit...")
        value = self.get_value(6)/10.
        if not isnan(value): info("Low limit %r C" % value)
        else: warn("Low limit unreadable (old firmware?)")
        return value
    def set_low_limit(self,value): self.set_value(6,value*10)
    low_limit = property(get_low_limit,set_low_limit)
    LLM = low_limit

    def get_high_limit(self):
        """Not supported early firmware (serial number 1)"""
        debug("Getting high limit...")
        value = self.get_value(7)/10.
        if not isnan(value): info("High limit %r C" % value)
        else: warn("High limit unreadable (old firmware?)")
        return value
    def set_high_limit(self,value): self.set_value(7,value*10)
    high_limit = property(get_high_limit,set_high_limit)
    HLM = high_limit

    def get_PID(self):
        """get PID parameters"""
        from time import sleep
        dic = {}
        res_dic = {}
        try:
            dic['p1'] = ('\xd0',3)
        except:
            dic['p1'] = nan
        try:
            dic['i1'] = ('\xd1',3)
        except:
            dic['p1'] = nan
        try:
            dic['d1'] = ('\xd2',3)
        except:
            dic['p1'] = nan
        try:
            dic['p2'] = ('\xd3',3)
        except:
            dic['p1'] = nan
        try:
            dic['i2'] = ('\xd4',3)
        except:
            dic['p1'] = nan
        try:
            dic['d2'] = ('\xd5',3)
        except:
            dic['p1'] = nan
        for key in dic.keys():
            res = self.query(command = dic[key][0], count = dic[key][1])
            if res is not nan:
                res_dic[key] = unpack('H',res[1]+res[2])
            else:
                res = nan
            sleep(0.1)
        return res_dic

    def set_factory_PID(self):
        pid_dic = {}
        #factory settings: good settings
        pid_dic['p1'] = 90
        pid_dic['i1'] = 32
        pid_dic['d1'] = 2
        pid_dic['p2'] = 50
        pid_dic['i2'] = 35
        pid_dic['d2'] = 3
        dic = {}
        dic['p1'] = '\xf0'
        dic['i1'] = '\xf1'
        dic['d1'] = '\xf2'
        dic['p2'] = '\xf3'
        dic['i2'] = '\xf4'
        dic['d2'] = '\xf5'
        for key in pid_dic.keys():
            byte_temp =  pack('h',round(pid_dic[key],0))
            self.query(command = dic[key]+byte_temp,count = 1)
            sleep(0.1)

    def set_PID(self, pid_in = {}):
        """
        sets PID parameters.
        input as dictionary with keys p1,i1,d1,p2,i2,d2
        """
        try:
            dic = {}
            dic['p1'] = '\xf0'
            dic['i1'] = '\xf1'
            dic['d1'] = '\xf2'
            dic['p2'] = '\xf3'
            dic['i2'] = '\xf4'
            dic['d2'] = '\xf5'
            for key in pid_in.keys():
                byte_temp =  pack('h',round(pid_in[key],0))
                self.query(command = dic[key]+byte_temp,count = 1)
                sleep(0.1)
        except:
            error('Oasis driver set_PID wrong input dictionary structure')

    @property
    def port_name(self):
        """Serial port name"""
        if self.ser is None: value = ""
        else: value = self.ser.name
        return value
    COMM = port_name

    @property
    def connected(self): return self.ser is not None

    @property
    def online(self):
        if self.ser is None: self.init_communications()
        online = self.ser is not None
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
        reply = self.query(command = command,ser = self.ser,count=3)
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
        reply = self.query(command = command,ser = self.ser, count=1)
        if len(reply) != 1:
            warn("expecting 1, got %d bytes" % len(reply)); return
        reply_code, = unpack('B',reply)
        if reply_code != code: warn("expecting 0x%X, got 0x%X" % (code,reply_code))


driver = OasisChillerDriver()



if __name__ == "__main__": # for testing
    import logging
    from time import sleep, time
    logging.basicConfig(level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s")
    self = driver #for debugging
