"""Delay line linearity characterization
Friedrich Schotte, Jul 22, 2015 - Jul 23, 2015
Setup:
Ramsay-100B RF Generator, 351.93398 MHz +10 dBm -> FPGA RF IN
FPGA 1: X-scope trig -> CH1, DC50, 500 mV/div
FPGA 13: ps L oscill -> DC block -> 90-MHz low-pass -> CH2, DC50, 500 mV/div
Timebase 5 ns/div
Measurement P1 CH2, time@level, Percent, 50%, Slope Pos, Gate Start 4.5 div, Stop 5.5 div
FPGA Frequency: 41 Hz
"""
__version__ = "2.1"
from instrumentation import timing_system,lxd,bcf,clksrc,lecroy_scope
from scan import rscan,timescan as tscan
from sleep import sleep
delay = lecroy_scope("pico21").measurement(1)
tmax = 5/bcf

def scan():
    lxd.value = 0
    data = rscan([lxd,delay.gate.start,delay.gate.stop],0,[tmax,-tmax,-tmax],
        640,delay,averaging_time=60.0,logfile="logfiles/delay.log")

def timescan():
    data = tscan(delay,averaging_time=4.0,logfile="logfiles/delay.log")

def peridiocally_interrupt_clock():
    while True:
        try:
            clksrc.state = 'RJ45:1'
            sleep(4)
            clksrc.state = 'RF IN'
            sleep(60-4)
        except KeyboardInterrupt: break
    clksrc.state = 'RF IN'

if __name__ == "__main__":
    print('timing_system.ip_address = %r' % timing_system.ip_address)
    print('scan()')
    print('peridiocally_interrupt_clock()')
    print('timescan()')
