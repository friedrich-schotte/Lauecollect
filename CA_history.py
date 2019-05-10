"""Caching of Channel Access
Author: Friedrich Schotte
Date created: 2018-10-24
Date last modified: 2018-11-01
"""
__version__ = "1.0" 

from logging import debug,info,warn,error

PV_history = {}
max_count = 1000

def CA_history(PV_name):
    """Value of Channel Access (CA) Process Variable (PV)"""
    from CA import camonitor
    camonitor(PV_name,callback=update)
    history = PV_history.get(PV_name,([],[]))
    return history

def update(PV_name,value,formatted_value,timestamp):
    """Handle Process Variable (PV) update"""
    t,v = PV_history.get(PV_name,([],[]))
    t = (t+[timestamp])[-max_count:]
    v = (v+[value])[-max_count:]
    PV_history[PV_name] = t,v

def filter(history,tmin,tmax):
    t,v = history
    t_filtered =  [ti for ti in t if tmin <= ti <= tmax]
    v_filtered =  [vi for ti,vi in zip(t,v) if tmin <= ti <= tmax]
    history = t_filtered,v_filtered
    return history
    
if __name__ == "__main__":
    from pdb import pm # for debugging
    import logging # for debugging
    from time import time # for timing
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s",
    )
    ##PV_name = "NIH:TIMING.registers.ch1_trig_count.count"
    PV_name = "TESTBENCH:TIMING.registers.ch1_trig_count.count"
    PV_names = [
        "TESTBENCH:TIMING.registers.ch1_trig_count.count",
        "TESTBENCH:TIMING.registers.ch1_acq_count.count",
        "TESTBENCH:TIMING.registers.ch1_acq.count",
    ]
    from CA import caget,cainfo,camonitor
    from time import sleep
    
    def delays(PV_name,dt=0.01,T=1.0):
        from numpy import rint
        delays = []
        for i in range(0,int(rint(T/dt))):
            delays.append(cainfo(PV_name,"timestamp")-time())
            sleep(dt)
        return delays
    
    print('caget(PV_name)')
    print('cainfo(PV_name,["timestamp","value"])')
    print('cainfo(PV_name,"timestamp")-time()')
    print('CA_history(PV_name)')
    print('filter(CA_history(PV_name),time()-10,time())')
    print('max(delays(PV_name,0.005,2.5))')
    print('for n in PV_names: camonitor(n)')
