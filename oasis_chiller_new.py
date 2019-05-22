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
Date last modified: 2018-05-21
"""
__version__ = "2.4" # using Serial_Device as base classs
from logging import error,warn,info,debug

from serial_device import Serial_Device
class Oasis_Chiller_Device(Serial_Device):
    id_query = "A"
    id_reply_length = 3

    def id_reply_valid(self,reply):
        valid = reply.startswith("A") and len(reply) == 3
        debug("Reply %r valid? %r" % (reply,valid))
        return valid

    def parameter_property(parameter_number,scale_factor=1):
        """A 16-bit parameter"""
        def get(self): return self.get_value(parameter_number)/scale_factor
        def set(self,value): self.set_value(parameter_number,value*scale_factor)
        return property(get,set)

    command_value = parameter_property(1,scale_factor=10.0)
    value = parameter_property(9,scale_factor=10.0)
    low_limit = parameter_property(6,scale_factor=10.0)
    high_limit = parameter_property(7,scale_factor=10.0)

    P1 = parameter_property(0xD0)
    I1 = parameter_property(0xD1)
    D1 = parameter_property(0xD2)
    P2 = parameter_property(0xD3)
    I2 = parameter_property(0xD4)
    D2 = parameter_property(0xD5)

    def set_factory_PID(self):
        """Reset PID parameters to factory settings"""
        self.P1 = 90
        self.I1 = 32
        self.D1 = 2
        self.P2 = 50
        self.I2 = 35
        self.D2 = 3

    @property
    def faults(self):
        """Report list of faults as string"""
        faults = ""
        bits = self.faults_byte
        if not isnan(bits):
            for i in range(0,8):
                if (bits >> i) & 1:
                    if i in self.fault_names: faults += self.fault_names[i]+", "
                    else: faults += str(i)+", "
            faults = faults.strip(", ")
            if faults == "": faults = "none"
        if faults == "": faults = " "
        debug("Faults %s" % faults)
        return faults

    fault_names = {
        0:"Tank Level Low",
        1:"Pump Fault",
        2:"Temp above alarm range",
        4:"RTD Fault",
        5:"Pump Fault",
        7:"Temp below alarm range",
    }

    @property
    def fault_code(self):
        """Report faults as number
        0: no fault
        1: Tank Level Low
        2: Pump Fault
        3: Temp above alarm range
        5: RTD Fault
        6: Pump Fault
        8: Temp below alarm range
        """
        faults_byte = self.faults_byte
        if faults_byte == 0: fault_code = 0
        else: fault_code = highest_bit(faults_byte)+1
        debug("Fault code %s" % fault_code)
        return fault_code

    @property
    def faults_byte(self): return self.get_byte(8)

    def get_byte(self,parameter_number):
        """Read an 8-bit value
        parameter_number: 0-255
          8 = fault
        """
        from struct import pack,unpack
        from numpy import nan
        code = int("01000000",2) | parameter_number
        command = pack('B',code)
        reply = self.query(command,count=2)
        count = nan
        if len(reply) != 2:
            if len(reply)>0:
                warn("%r: expecting 2-byte reply, got %r" % (command,reply))
            elif self.connected:
                warn("%r: expecting 2-byte reply, got no reply" % command)
        else:
            reply_code,count = unpack('<BB',reply)
            if reply_code != code:
                warn("reply %r: expecting 0x%X(%s), got 0x%X(%s)" %
                     (reply,code,bin(code),reply_code,bin(reply_code)))
                count = nan
        return count

    def get_value(self,parameter_number):
        """Read a 16-bit value
        parameter_number: 0-255
          1=set point, 6=low limit, 7=high limit, 9=coolant temp.
          208-213=PID parameter P1,I1,D1,P2,I2,D2
        """
        from struct import pack,unpack
        from numpy import nan
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
        from struct import pack,unpack
        code = int("01100000",2) | parameter_number
        command = pack('<BH',code,int(rint(value)))
        reply = self.query(command,count=1)
        if len(reply) != 1:
            warn("expecting 1, got %d bytes" % len(reply)); return
        reply_code, = unpack('B',reply)
        if reply_code != code: warn("expecting 0x%X, got 0x%X" % (code,reply_code))

oasis_chiller_device = Oasis_Chiller_Device()


def highest_bit(count):
    """Which is the nost significate bit in the binary number "count" that has been
    set? 0-based index"""
    highest_bit = -1
    for i in range(0,32):
        if (count & (1<<i)) != 0: highest_bit = i
    return highest_bit


if __name__ == "__main__":
    from pdb import pm
    import logging
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s %(levelname)s: %(message)s")

    self = oasis_chiller_device
    print("self.init_communications()")
    print("self.command_value")
    print("self.value")
    print("self.low_limit")
    print("self.high_limit")
