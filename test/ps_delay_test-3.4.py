"""Delay line linearity characterization
Friedrich Schotte, Jul 22, 2015 - Apr 27, 2015
Setup:
Ramsay-100B RF Generator, 351.93398 MHz +10 dBm -> FPGA RF IN
FPGA 1: X-scope trig -> CH1, DC50, 500 mV/div
FPGA 13: ps L oscill -> DC block -> 90-MHz low-pass -> CH2, DC50, 500 mV/div
Timebase 5 ns/div
Measurement P1 CH2, time@level, Absolute, 0, Slope Pos, Gate Start 4.5 div,
Stop 5.5 div
Waitting time: 97.8 ms
"""
__version__ = "3.4"
from instrumentation import timing_system,timing_sequencer,round_next
from instrumentation import actual_delay,lecroy_scope
from LokToClock import LokToClock
from timing_sequence import lxd,Sequence
from scan import rscan,timescan as tscan
from motor_wrapper import motor_wrapper
from sleep import sleep
from numpy import arange

locked = motor_wrapper(LokToClock,"locked")
clk_shift_count = motor_wrapper(timing_system.clk_shift,"count")

delay = actual_delay
dt = timing_system.clk_shift.stepsize*32
tmax = round_next(5*timing_system.bct,dt)
nsteps = tmax/dt

def scan():
    tmax = round_next(5*timing_system.bct,dt)
    nsteps = tmax/dt
    lxd.value = 0
    data = rscan([lxd,locked],[0,1],[tmax,1],nsteps,[clk_shift_count,delay],
        averaging_time=1.0,logfile="logfiles/scan.log")

def scan_delayline():
    tmax = timing_system.clk_shift.max_dial
    nsteps = tmax/dt
    timing_sequencer.running = False
    timing_system.xosct.enable.count = 1
    timing_system.clk_shift.dial = 0
    data = rscan([timing_system.clk_shift,delay.gate.start,delay.gate.stop],
        [0,0,0],[tmax,tmax,tmax],nsteps,[clk_shift_count,delay],
        averaging_time=10.0,logfile="logfiles/scan_delayline.log")

def timescan():
    data = tscan(delay,averaging_time=10.0,logfile="logfiles/timescan.log")

def register_counts():
    trange = arange(0,tmax,tmax/50)
    pso = [Sequence(ps_lxd=t).register_counts[1][16][0] for t in trange]
    clk_shift = [Sequence(ps_lxd=t).register_counts[1][17][0] for t in trange]
    return pso,clk_shift

def reset_dcm():
    timing_system.clk_shift_reset.count = 1 
    sleep(0.2)
    timing_system.clk_shift_reset.count = 0
    
def peridiocally_reset_dcm(wait_time=60):
    while True:
        try:
            reset_dcm()
            sleep(wait_time)
        except KeyboardInterrupt:
            timing_system.clk_shift_reset.count = 0
            break

if __name__ == "__main__":
    print('timing_system.ip_address = %r' % timing_system.ip_address)
    print('delay.scope.ip_address = %r' % delay.scope.ip_address)
    print('reset_dcm()')
    print('scan_delayline()')
    print('scan()')
    
