"""Delay line linearity characterization
Friedrich Schotte, Jul 22, 2015 - Jul 31, 2015
Setup:
Ramsay-100B RF Generator, 351.93398 MHz +10 dBm -> FPGA RF IN
FPGA 1: X-scope trig -> CH1, DC50, 500 mV/div
FPGA 13: ps L oscill -> DC block -> 90-MHz low-pass -> CH2, DC50, 500 mV/div
Timebase 5 ns/div
Measurement P1 CH2, time@level, Absulute, 0, Slope Pos, Gate Start 4.5 div, Stop 5.5 div
FPGA Frequency: 41 Hz
"""
__version__ = "4.0.1"
from instrumentation import lecroy_scope,timing_system
from Ensemble_SAXS_pp import Ensemble_SAXS
from scan import timescan as tscan
from sleep import sleep
scope = lecroy_scope()
delay = scope.measurement(1)

def timescan():
    tscan(delay,averaging_time=2.0,logfile="logfiles/delay.log")

if __name__ == "__main__":
    print('timing_system.ip_address = %r' % timing_system.ip_address)
    print('scope.ip_address = %r' % scope.ip_address)
    print('Ensemble_SAXS.resync()')
    print('timescan()')
