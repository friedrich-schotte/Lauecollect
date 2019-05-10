"""Author: Friedrich Schotte,
Date created: Oct 21, 2015
Date last modified: Jun 6, 2018
"""
__version__ = "5.4.1" # resume

from pdb import pm # for debugging
from timing_system import timing_system
from timing_sequence import timing_sequencer
from time import sleep,time
from numpy import *
import logging
from tempfile import gettempdir
logfile = None ##gettempdir()+"/lauecollect_debug.log"
logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s",
    filename=logfile)

timepoints = [
    100e-12,178e-12,316e-12,562e-12,
    1e-9,1.78e-9,3.16e-9,5.62e-9,
    10e-9,17.8e-9,31.6e-9,56.2e-9,
    100e-9,178e-9,316e-9,562e-9,
    1e-6,1.78e-6,3.16e-6,5.62e-6,
    10e-6,17.8e-6,31.6e-6,56.2e-6,
    100e-6,178e-6,316e-6,562e-6,
    1e-3,1.78e-3,3.16e-3,5.62e-3,
    10e-3,17.8e-3,31.6e-3,
    32*timing_system.hsct,64*timing_system.hsct,128*timing_system.hsct
]
timepoints=timepoints[:]
laser_mode = [0,1]
npulses = 1

delays = array([t for t in timepoints for l in laser_mode])
laser_on = array([l for t in timepoints for l in laser_mode])
image_numbers = arange(1,len(delays)+1)
npulses = [1 if l else 1 for l in laser_on]
waitt = [984*timing_system.hsct if l else 984*timing_system.hsct for l in laser_on]
burst_waitt = [t*n for (t,n) in zip(waitt,npulses)]
ms_on = [1 if l else 1 for l in laser_on]

# for debugging
##laser_on = delays = lxd = nsq_on = s3_on = None
self = timing_sequencer

##image_numbers = array([62,64,66,68,70])
##delays = delays[image_numbers-1]
##laser_ons = laser_ons[image_numbers-1]
##npulses = npulses[image_numbers-1]

def update():
    timing_sequencer.acquire(delays=delays,laser_on=laser_on,
        npulses=npulses,waitt=waitt,burst_waitt=burst_waitt,
        image_numbers=image_numbers,
        ms_on=ms_on)
    
def start():
    update()
    timing_system.image_number.value = 0
    timing_system.pass_number.value = 0
    timing_system.pulses.value = 0
    timing_sequencer.queue_sequence_count = 0
    timing_sequencer.queue_repeat_count = 0
    timing_sequencer.queue_active = True

def cancel():
    timing_sequencer.queue_active = False

def resume():
    update()
    timing_sequencer.queue_active = True

print("timing_system.ip_address = %r" % timing_system.ip_address)
##print("timing_sequencer.cache_enabled = %r" % timing_sequencer.cache_enabled)
print("")
print("timing_sequencer.running = True")
print("update()")
print("start()")
print("cancel()")
print("resume()")
