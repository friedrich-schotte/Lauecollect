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

The 2-byte value is a 16-bit binary number encoding the temperature in units
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

Authors: Friedrich Schotte, Nara Dashdorj, Valentyn Stadnytskyi
Date created: 2009-05-28
Date last modified: 2021-12-03
Revision comment: Issue: Conflicting file names:
    settings/oasis_chiller_settings.txt
    settings/Oasis_Chiller_settings.txt
    (SMB file server cannot serve both files to a Windows client)
    Default timeout too short
"""
__version__ = "3.0.5"

from logging import warning, info, debug
from struct import pack, unpack


def parameter_property(parameter_number, scale_factor=1.0):
    """A 16-bit parameter"""

    def fget(self): return self.get_16bit_value(parameter_number) / scale_factor

    def fset(self, value): self.set_16bit_value(parameter_number, value * scale_factor)

    return property(fget, fset)


class Oasis_Chiller_Driver(object):
    """Oasis thermoelectric chiller by Solid State Cooling Systems"""
    from persistent_property import persistent_property

    name = "oasis_chiller_driver"

    timeout = persistent_property("timeout", 1.0)
    wait_time = persistent_property("wait_time", 1.0)  # between commands

    baudrate = 9600
    id_query = b"A"
    id_reply_length = 3

    last_reply_time = 0.0

    def id_reply_valid(self, reply):
        valid = reply.startswith(b"A") and len(reply) == 3
        debug("Reply %r valid? %r" % (reply, valid))
        return valid

    # Make multithreading safe
    from threading import Lock
    __lock__ = Lock()

    port = None

    nominal_temperature = parameter_property(1, scale_factor=10.0)
    actual_temperature = parameter_property(9, scale_factor=10.0)
    low_limit = parameter_property(6, scale_factor=10.0)
    high_limit = parameter_property(7, scale_factor=10.0)

    VAL = nominal_temperature
    RBV = actual_temperature
    LLM = low_limit
    HLM = high_limit

    P1 = parameter_property(208, scale_factor=1.0)  # 16
    I1 = parameter_property(209, scale_factor=1.0)  # 17
    D1 = parameter_property(210, scale_factor=1.0)  # 18
    P2 = parameter_property(211, scale_factor=1.0)  # 19
    I2 = parameter_property(212, scale_factor=1.0)  # 20
    D2 = parameter_property(213, scale_factor=1.0)  # 21

    def set_factory_PID(self):
        """Reset PID parameters to factory settings"""
        self.P1 = 90
        self.I1 = 32
        self.D1 = 2
        self.P2 = 50
        self.I2 = 35
        self.D2 = 3

    @property
    def port_name(self):
        """Serial port name"""
        if self.port is None:
            value = ""
        else:
            value = self.port.name
        return value

    COMM = port_name

    @property
    def connected(self):
        return self.port is not None

    @property
    def online(self):
        if self.port is None:
            self.discover_port()
        online = self.port is not None
        if online:
            debug("Device online")
        else:
            warning("Device offline")
        return online

    @property
    def fault_code(self):
        """Report faults as number
        0: no fault
        1: Tank Level Low
        2: Temp above alarm range
        5: RTD Fault
        6: Pump Fault
        8: Temp below alarm range
        """
        fault_code = self.faults_byte
        if fault_code == 2.0 ** 7:
            fault_code = 8
        elif fault_code == 2.0 ** 6:
            fault_code = 7
        elif fault_code == 2.0 ** 5:
            fault_code = 6
        elif fault_code == 2.0 ** 4:
            fault_code = 5
        elif fault_code == 2.0 ** 3:
            fault_code = 4
        elif fault_code == 2.0 ** 2:
            fault_code = 3
        elif fault_code == 2.0 ** 1:
            fault_code = 2
        elif fault_code == 2.0 ** 0:
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
        from numpy import isnan

        faults = ""
        bits = self.faults_byte
        if not isnan(bits):
            for i in range(0, 8):
                if (bits >> i) & 1:
                    if i in self.fault_names:
                        faults += self.fault_names[i] + ", "
                    else:
                        faults += str(i) + ", "
            faults = faults.strip(", ")
            if faults == "":
                faults = "none"
        if faults == "":
            faults = " "
        debug("Faults %s" % faults)
        return faults

    fault_names = {
        0: "Tank Level Low",
        2: "Temp above alarm range",
        4: "RTD Fault",
        5: "Pump Fault",
        7: "Temp below alarm range",
    }

    @property
    def faults_byte(self):
        return self.get_8bit_value(8)

    def get_8bit_value(self, parameter_number):
        """Read an 8-bit value
        parameter_number: 0-255
          8 = fault
        """
        from numpy import nan

        code = int("01000000", 2) | parameter_number
        command = pack('B', code)
        reply = self.query(command, count=2)
        # The reply is 0xC8 followed by a faults status byte.
        count = nan
        if len(reply) != 2:
            if len(reply) > 0:
                warning("%r: expecting 2-byte reply, got %r" % (command, reply))
            elif self.connected:
                warning("%r: expecting 2-byte reply, got no reply" % command)
        else:
            reply_code, count = unpack('<BB', reply)
            if reply_code != code:
                warning("reply %r: expecting 0x%X(%s), got 0x%X(%s)" %
                        (reply, code, bin(code), reply_code, bin(reply_code)))
                count = nan
        return count

    def get_16bit_value(self, parameter_number):
        """Read a 16-bit value
        parameter_number: 0-255
          1=set point, 6=low limit, 7=high limit, 9=coolant temp.
          208-213=PID parameter P1,I1,D1,P2,I2,D2
        """
        from struct import pack
        from numpy import nan

        code = int("01000000", 2) | parameter_number
        command = pack('B', code)
        reply = self.query(command, count=3)
        # The reply is 0xC1 followed by 1 16-bit binary count on little-endian byte
        # order. The count is the temperature in degrees Celsius, times 10.
        if len(reply) != 3:
            if len(reply) > 0:
                warning("%r: expecting 3-byte reply, got %r" % (command, reply))
            elif self.connected:
                warning("%r: expecting 3-byte reply, got no reply" % command)
            return nan
        reply_code, count = unpack('<BH', reply)
        if reply_code != code:
            warning("reply %r: expecting 0x%X(%s), got 0x%X(%s)" %
                    (reply, code, bin(code), reply_code, bin(reply_code)))
            return nan
        return count

    def set_16bit_value(self, parameter_number, value):
        """Set a 16-bit value"""
        from numpy import rint
        from struct import pack
        code = int("01100000", 2) | parameter_number
        command = pack('<BH', code, int(rint(value)))
        reply = self.query(command, count=1)
        if len(reply) != 1:
            warning("expecting 1, got %d bytes" % len(reply))
            return
        reply_code, = unpack('B', reply)
        if reply_code != code:
            warning("expecting 0x%X, got 0x%X" % (code, reply_code))

    def query(self, command, count=1):
        """Send a command to the controller and return the reply"""
        with self.__lock__:  # multithreading safe
            for i in range(0, 2):
                try:
                    reply = self.__query__(command, count)
                except Exception as msg:
                    warning("query: %r: attempt %s/2: %s" % (command, i + 1, msg))
                    reply = ""
                if reply:
                    return reply
                self.discover_port()
            return reply

    def __query__(self, command, count=1):
        """Send a command to the controller and return the reply"""
        from time import time
        from sleep import sleep
        sleep(self.last_reply_time + self.wait_time - time())
        self.write(command)
        reply = self.read(count=count)
        self.last_reply_time = time()
        return reply

    def flush(self):
        if self.port is not None:
            self.port.flushInput()
            self.port.flushOutput()

    def write(self, command):
        """Send a command to the controller"""
        if self.port is not None:
            self.flush()
            self.port.write(command)
            debug("%s: Sent %r" % (self.port.name, command))

    def read(self, count=None, port=None):
        """Read a reply from the controller,
        terminated with the given terminator string"""
        # debug("read count=%r,port=%r" % (count,port))
        if port is None:
            port = self.port
        if port is not None:
            # print("in wait:" + str(self.port.inWaiting()))
            debug("Trying to read %r bytes from %s..." % (count, port.name))
            port.timeout = self.timeout
            reply = port.read(count)
            debug("%s: Read %r" % (port.name, reply))
        else:
            reply = ""
        return reply

    discover_time = 0

    def discover_port(self):
        """To do before communicating with the controller"""
        from serial_ports import serial_ports
        from serial import Serial
        from time import time

        if self.port is not None:
            try:
                info("Checking whether device is still responsive...")
                self.port.write(self.id_query)
                debug("%s: Sent %r" % (self.port.name, self.id_query))
                reply = self.read(count=self.id_reply_length)
                if not self.id_reply_valid(reply):
                    debug("%s: %r: invalid reply %r" % (self.port.name, self.id_query, reply))
                    info("%s: lost connection" % self.port.name)
                    self.port = None
                else:
                    info("Device is still responsive.")
            except Exception as msg:
                debug("%s: %s" % (Exception, msg))
                self.port = None

        if self.port is None:
            if time() - self.discover_time > 1.0:
                for port_name in serial_ports():
                    debug(f"Trying port {port_name}...")
                    try:
                        port = Serial(port_name)
                        try:
                            port.baudrate = self.baudrate
                        except OSError as x:
                            warning(f"{port_name}: Baud rate {self.baudrate}: {x}")
                        port.timeout = self.timeout
                        port.write(self.id_query)
                        debug("%s: Sent %r" % (port.name, self.id_query))
                        reply = self.read(count=self.id_reply_length, port=port)
                        if self.id_reply_valid(reply):
                            self.port = port
                            info("Discovered device at %s based on reply %r" % (self.port.name, reply))
                            break
                    except Exception as x:
                        debug(f"{x}")
                    if self.port is not None:
                        break
                    self.discover_time = time()


oasis_chiller_driver = Oasis_Chiller_Driver()


if __name__ == "__main__":
    import logging

    msg_format = "%(asctime)s %(levelname)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    self = oasis_chiller_driver  # for debugging
    print('self.discover_port()')
    print("self.port_name")
    print("self.nominal_temperature = 40")
    print("self.nominal_temperature = 5")
    print("self.actual_temperature")
    print("self.low_limit")
    print("self.high_limit")
    print("self.fault_code")
    print("self.faults")
