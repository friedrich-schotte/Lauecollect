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
__version__ = "2.0"
from instrumentation import psod,lecroy_scope
from scan import rscan
delay = lecroy_scope("pico21").measurement(1)

def scan():
    psod.value = 0
    global data
    data = rscan([psod,delay.gate.start,delay.gate.stop],psod.min,psod.max,640,
        delay,averaging_time=60.0,logfile="test/delay.log")

print('scan()')
