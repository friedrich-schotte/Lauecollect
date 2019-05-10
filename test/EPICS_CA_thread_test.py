"""This script is to test various implementations of the Python to EPICS interface.
It checks wether these are multi-thread safe. That means that a caput and caget
to the same process valiable succeeds both from the forground and from a background
thread.

EpicsCA: Matt Newille, U Chicago
epics: Matt Newille, U Chicago
CA: Friedrich Schotte, NIH

Friedrich Schotte, APS, 14 Apr 2010
"""
import sys
sys.path += ["/Femto/C/All Projects/APS/Instrumentation/Software/Python"]
from epics import caget,caput,PV # choices: EpicsCA, epics, CA
from time import sleep
from threading import Thread

def run_test(count=1):
    for i in range(0,count):
        x = caget("14IDB:m3.VAL")
        caput("14IDB:m3.VAL",x+0.001)
        print x,caget("14IDB:m3.RBV")

print "Foreground:"
run_test(2)
print "Background:"
thread = Thread(target=run_test,args=(2,))
thread.start()
thread.join()

print 'Done'
