#!/bin/env python
"""
CA robustness test
July 7 2018


"""

__version__ = "1.0.2"


def diff_time_stamp(self):
    from CA import camonitor
dic = {}
def monitor_PVS(pv):
    from numpy import nan
    from CA import caget
    from time import sleep
    dic[pv] = (0,0)
    while True:
            sleep(0.5) 
            value = caget(pv)
            if type(value) == None or value == nan:
                    print('WARNING: %r IS %r' % (pv,value))
                    dic[pv] = (dic[pv][0],dic[pv][1]+1)
            else:
                    dic[pv] = (dic[pv][0]+1,dic[pv][1])

def add_thread_PV(pv):
    from thread import start_new_thread
    start_new_thread(monitor_PVS,(pv,))
# Run the main program
if __name__ == "__main__":
    from thread import start_new_thread
    add_thread_PV('BNCHI.BunchCurrentAI.VAL')
    add_thread_PV('NIH:TEMP.P')
    add_thread_PV('NIH:TEMP.I')
    add_thread_PV('NIH:SAMPLE_FROZEN_OPT_RGB.MEAN')
    add_thread_PV('NIH:SAMPLE_FROZEN_OPT_RGB.STDEV')
    add_thread_PV('NIH:CHILLER.VAL')
    add_thread_PV('NIH:TEMP.VAL')
    add_thread_PV('NIH:CHILLER.RBV')
    add_thread_PV('NIH:TEMP.RBV')
