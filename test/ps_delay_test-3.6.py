"""Delay line linearity characterization
Friedrich Schotte, Jul 22, 2015 - May 2, 2015
Setup:
Ramsay-100B RF Generator, 351.93398 MHz +10 dBm -> FPGA RF IN
FPGA 1: X-scope trig -> CH1, DC50, 500 mV/div
FPGA 13: ps L oscill -> DC block -> 90-MHz low-pass -> CH2, DC50, 500 mV/div
Timebase 5 ns/div
Measurement P1 CH2, time@level, Absolute, 0, Slope Pos, Gate Start 4.5 div,
Stop 5.5 div
Waitting time: 97.8 ms
"""
__version__ = "3.6"
from instrumentation import timing_system,timing_sequencer,round_next
from timing_sequence import Sequence
from instrumentation import actual_delay,lecroy_scope,agilent_scope
from LokToClock import LokToClock
from timing_sequence import lxd,Sequence
from scan import rscan,timescan as tscan
from motor_wrapper import motor_wrapper
from sleep import sleep
from numpy import arange

locked = motor_wrapper(LokToClock,"locked")
psod3_count = motor_wrapper(timing_system.psod3,"count")
psod2_count = motor_wrapper(timing_system.psod2,"count")

scope = lecroy_scope()
delay = scope.measurement(1)
dt = timing_system.psod2.stepsize
tmax = round_next(5*timing_system.bct,dt)
nsteps = tmax/dt

def scan():
    lxd.value = 0
    data = rscan([lxd,delay.gate.start,delay.gate.stop],[0,0,0],
        [tmax,-tmax,-tmax],nsteps,[psod3_count,psod2_count,delay],
        averaging_time=10.0,logfile="logfiles/scan.log")

def scan_fast():
    timing_sequencer.running = False
    timing_system.xosct.enable.count = 1
    lxd_fast.value = 0
    data = rscan([lxd_fast,delay.gate.start,delay.gate.stop],[0,0,0],
        [tmax,-tmax,-tmax],nsteps,[psod3_count,psod2_count,delay],
        averaging_time=10.0,logfile="logfiles/scan.log")

def scan_delayline():
    tmax = timing_system.psod2.max_dial
    nsteps = tmax/dt
    timing_sequencer.running = False
    timing_system.xosct.enable.count = 1
    timing_system.psod2.dial = 0
    data = rscan([timing_system.psod2,delay.gate.start,delay.gate.stop],
        [0,0,0],[tmax,tmax,tmax],nsteps,[psod2_count,delay],
        averaging_time=10.0,logfile="logfiles/scan_delayline.log")

def timescan():
    data = tscan(delay,averaging_time=10.0,logfile="logfiles/timescan.log")

class Lxd(object):
    from numpy import nan
    __value__ = nan
    def get_value(self):
        return self.__value__
    def set_value(self,value):
        self.__value__ = value
        timing_system.cache = 1
        psod3,psod2 = Sequence(ps_lxd=value).register_counts[1][13:15]
        timing_system.psod3.count = psod3[0]
        timing_system.psod2.count = psod2[0]
    value = property(get_value,set_value)

lxd_fast = Lxd()
        

if __name__ == "__main__":
    print('timing_system.ip_address = %r' % timing_system.ip_address)
    print('delay.scope.ip_address = %r' % delay.scope.ip_address)
    print('timing_system.reset_dcm()')
    print('scan_fast()')
    print('scan()')
    
