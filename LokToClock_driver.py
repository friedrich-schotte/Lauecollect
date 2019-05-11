"""
This is to remote monitor and enable to Spectra Physics 3930 Lok-to-Clock
frequency stabilizer for the Tsunami laser.

Reference:
Tsunami Mode-locked Ti:Sapphire Laser User's Manual, Spectra Physics, June 2002
Chapter 8 "Lok-to-Clock Electronics", 8-16 "The Model 3930 Command Set"

Commands:
:LOOP 1 - enable locking
:LOOP 0 - disable locking
:LOOP? - returns "1" is locked, "0" if not locked
*IDN? - for testing, returns identy string 'Spectra Physics Lasers,3930A,0,1.02' 

Setup:
Window PC "id14l-spitfire", COM1 (serial port on mother board) -> DB9 cross-over
cable, labeled "RS4" -> Model 3390 "Lok-to-Clock" back panel.

F. Schotte, 3 Jun 2013 - 3 Jun 2013
"""
# Need to install the package "pyserial" from pypi.python.org/pypi/serial
from serial import *

__version__ = "1.0"

class LokToClock_object(object):
    port_name = "COM1"
    port = None
    
    def get_locked(self):
        """Is phase lock loop active"""
        reply = self.query(":LOOP?")
        if reply == "1": return 1
        else: return 0
    def set_locked(self,lock):
        """enable or disable phase lock loop"""
        if lock: self.send(":LOOP 1")
        else: self.send(":LOOP 0")
    locked = property(get_locked,set_locked)

    def send(self,command):
        self.init_communications()
        self.port.write("%s\r" % command)

    def query(self,command):
        self.init_communications()
        self.port.write("%s\r" % command)
        self.port.timeout = 0.1
        reply = self.port.read(80)
        reply = reply.strip("\n\r")
        return reply

    def init_communications(self):
        if self.port is not None and self.port.port == self.port_name: return
        self.port = Serial(self.port_name)
        self.port.baudrate = 9600
        self.port.bytesize = EIGHTBITS
        self.port.parity = PARITY_NONE
        self.port.stopbits = STOPBITS_ONE
        self.port.xonxoff = 1 # Software flow control: on
        self.port.rtscts = 0 # Hardware flow control: off
        self.port.dsrdtr = None # Modem handshake: off
            

LokToClock = LokToClock_object()

if __name__ == "__main__": # for testing
    self = LokToClock # for debugging
    print 'LokToClock.query("*IDN?")'
    print 'LokToClock.locked'
