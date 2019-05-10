"""Delay line linearity characterization
Friedrich Schotte, Jul 22, 2015 - Jul 30, 2015
Setup:
Ramsay-100B RF Generator, 351.93398 MHz +10 dBm -> FPGA RF IN
FPGA 1: X-scope trig -> CH1, DC50, 500 mV/div
FPGA 13: ps L oscill -> DC block -> 90-MHz low-pass -> CH2, DC50, 500 mV/div
Timebase 5 ns/div
Measurement P1 CH2, time@level, Absolute, 0, Slope Pos, Gate Start 4.5 div,
Stop 5.5 div
Waitting time: 97.8 ms
"""
__version__ = "3.0"
from instrumentation import timing_system,lecroy_scope
from timing_sequence import lxd,Sequence
from scan import rscan,timescan as tscan
from sleep import sleep
from numpy import arange
delay = lecroy_scope().measurement(1)
tmax = 5*timing_system.bct
npoints = tmax/timing_system.clk_shift.stepsize

def scan():
    lxd.value = 0
    data = rscan([lxd,delay.gate.start,delay.gate.stop],0,[tmax,-tmax,-tmax],
        npoints,delay,averaging_time=10.0,logfile="logfiles/scan.log")

def timescan():
    data = tscan(delay,averaging_time=10.0,logfile="logfiles/timescan.log")

def register_counts():
    trange = arange(0,tmax,tmax/50)
    pso = [Sequence(ps_lxd=t).register_counts[1][16][0] for t in trange]
    clk_shift = [Sequence(ps_lxd=t).register_counts[1][17][0] for t in trange]
    return pso,clk_shift

def peridiocally_reset_dcm(wait_time=20):
    while True:
        try:
            count = timing_system.clk_shift.count
            timing_system.clk_shift.count = count + 1
            sleep(0.05)
            timing_system.clk_shift.count = count
            sleep(wait_time)
        except KeyboardInterrupt:
            timing_system.clk_shift.count = count
            break

if __name__ == "__main__":
    print('timing_system.ip_address = %r' % timing_system.ip_address)
    print('lecroy_scope().ip_address = %r' % lecroy_scope().ip_address)
    print('peridiocally_reset_dcm(20)')
    print('timescan()')
    print('scan()')
    
