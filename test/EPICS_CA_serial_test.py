"""This script is to test various implementations of the Python to EPICS interface.
It checks wether these are multi-thread safe. That means that a caput and caget
to the same process valiable succeeds both from the forground and from a background
thread.

EpicsCA: Matt Newille, U Chicago
epics: Matt Newille, U Chicago
CA: Friedrich Schotte, NIH

Friedrich Schotte, APS, 14 Apr 2010
"""

##import epics; epics.ca.PREEMPTIVE_CALLBACK = False
from epics import caput,caget # choices: EpicsCA, epics, CA
from time import sleep
from threading import Thread

def run_test(count=1):
    # Communicate with SSCS Oasis 160 Thermoelectric chiller using a serial
    # interface.
    fail_count = 0
    for i in range(0,count):
        # Faults
        caput("14IDB:serial13.NRRD",2,wait=True,timeout=1)
        caput("14IDB:serial13.AOUT","H",wait=True,timeout=1)
        ##sleep(0.2)
        result = caget("14IDB:serial13.TINP")
        expected = 'H\\000'
        print "expecting %r, got %r" % (expected,result)
        if result != expected: fail_count += 1
        # Nominal temperature 
        caput("14IDB:serial13.NRRD",3,wait=True,timeout=1)
        caput("14IDB:serial13.AOUT","A",wait=True,timeout=1)
        ##sleep(0.2)
        result = caget("14IDB:serial13.TINP")
        expected = 'A\\226\\000'
        print "expecting %r, got %r" % (expected,result)
        if result != expected: fail_count += 1
    if fail_count: print "[Test failed (%d/%d).]" % (fail_count,count*2)

print "Foreground:"
run_test(2)
print "Background:"
thread = Thread(target=run_test,args=(2,))
thread.start()
thread.join()
