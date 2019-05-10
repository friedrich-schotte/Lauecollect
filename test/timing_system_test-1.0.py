from pdb import pm
from instrumentation import *
import timing_system
import logging
from tempfile import gettempdir
from logging import debug,error,warn
from time import sleep
logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s")

class Laseron_wrapper(object):
    """"Work-around for a but in the FPGA firmeware for the "laseron"
    register"""
    def __init__(self,laseron):
        """laseron: original FPGA register object"""
        self.laseron = laseron

    def get_value(self): return self.laseron.value
    def set_value(self,value):
        self.laseron.value = value
        if self.laseron.value != value:
            # Toggle the bit on and off until the value get accepted.
            attempt = 0; attempts = 10
            while self.laseron.value != value and attempt<attempts:    
                self.laseron.value = not value
                self.laseron.value = value
                attempt += 1
            warn("laseron: expected %d,got %d after %r/%r retries" %
                (value,self.laseron.value,attempt,attempts))
            if self.laseron.value != value:
                error("laseron: expected %d, got %d" %
                (value,self.laseron.value))
    value = property(get_value,set_value)

laseron = Laseron_wrapper(timing_system.laseron1)
        
def test():
    value = True
    for i in range(0,100):
        timing_system.laseron.value = value
        sleep(1)
        value = not value

def test2():
    value = True
    for i in range(0,100):
        laseron.value = value
        sleep(1)
        value = not value

def test1():
    value = True
    for i in range(0,100):
        laseron.value = value
        if laseron.value != value:
            n = 0
            while laseron.value != value and n<10:    
                laseron.value = not value
                laseron.value = value
                n += 1
            warn("%d. expected %d,got %d, retries=%r"% (i,value,laseron.value,n))
        if laseron.value != value: warn("%d. failed to set %d" % value)
        sleep(1)
        value = not value


print("test()")
