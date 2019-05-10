"""Author: Friedrich Schotte, Oct 21, 2015 - Mar 11, 2018
"""
__version__ = "2.5" # optimize_queue

from pdb import pm # for debugging
from Ensemble_SAXS_pp import Ensemble_SAXS
from timing_system import timing_system
from timing_sequencer import timing_sequencer
from time import sleep,time
from numpy import *

import logging
logging.basicConfig(level=logging.DEBUG,format="%(asctime)s %(levelname)s: %(message)s")
self = Ensemble_SAXS # for debugging
##import timing_system as t; t.DEBUG=True

ps,ns,us,ms = 1e-12,1e-9,1e-6,1e-3

timepoints = array([
    -10*us,-10.1*us,
##    -10*us,-2.5*ns,-10*us,0,-10*us,2.5*ns,-10*us,5.62*ns,
##    -10*us,10*ns,-10*us,17.8*ns,-10*us,31.6*ns,-10*us,56.2*ns,-10*us,75*ns,
##    -10*us,100*ns,-10*us,133*ns,-10*us,178*ns,-10*us,316*ns,-10*us,562*ns,
##    -10*us,1*us,-10*us,1.78*us,-10*us,3.16*us,
##    -10*us,1*us,-10*us,1.78*us,-10*us,3.16*us,-10*us,5.62*us,
##    -10*us,10*us,-10*us,17.8*us,-10*us,31.6*us,-10*us,56.2*us,
##    -10*us,100*us,-10*us,178*us,-10*us,316*us,-10*us,562*us,
##    -10*us,1*ms,-10*us,1.78*ms,-10*us,3.16*ms,-10*us,5.62*ms,
    -10*us,10*ms,-10*us,17.8*ms,-10*us,31.6*ms,
])
repeats = 1
timepoints=timepoints*repeats
laser_mode = [1]
npasses = 2

delays = array([t for t in timepoints for l in laser_mode])
laser_ons = array([l for t in timepoints for l in laser_mode])
image_numbers = arange(1,len(delays)+1)
passes = array([npasses]*len(image_numbers))

##image_numbers = array([62,64,66,68,70])
##delays = delays[image_numbers-1]
##laser_ons = laser_ons[image_numbers-1]
##passes = passes[image_numbers-1]

def start():
    prepare()
    timing_sequencer.queue_active = True

def prepare():
    timing_sequencer.queue_active = False
    timing_system.image_number.count = 0
    timing_system.pass_number.count = 0
    timing_system.pulses.count = 0
    Ensemble_SAXS.acquire(delays,laser_ons,
        passes=passes,image_numbers=image_numbers)

def cancel(): Ensemble_SAXS.clear_queue()
    
def forever():
    """Continouly feed the queue, keeping collecting forever"""
    try:
        while True:
            start()
            while len(Ensemble_SAXS.queue) > 10: sleep(1)
    finally: cancel()

print("timing_system.ip_address = %r" % timing_system.ip_address)
print('timing_sequencer.optimize_queue = %r' % timing_sequencer.optimize_queue)
print('')
##print("Ensemble_SAXS.cache_enabled = %r" % Ensemble_SAXS.cache_enabled)
##print("Ensemble_SAXS.queue_length")
##print("Ensemble_SAXS.clear_queue()")
##print("Ensemble_SAXS.cache_size = 0")
##print("prepare()")
print("start()")
print("cancel()")
##print("forever()")
print("timing_sequencer.queue_length")
