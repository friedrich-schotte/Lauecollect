"""Author: Friedrich Schotte, Oct 21, 2015 - Feb 1, 2017
"""
__version__ = "2.4" # sequencer_packets speedup

from pdb import pm # for debugging
from Ensemble_SAXS_pp import Ensemble_SAXS
from timing_system import timing_system,ps,ns,us,ms
from time import sleep,time
from numpy import *

import logging; logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s")
self = Ensemble_SAXS # for debugging
##import timing_system as t; t.DEBUG=True

timepoints = [
##    100*ps,178*ps,316*ps,562*ps,
##    1*ns,1.78*ns,3.16*ns,5.62*ns,
    10*ns,17.8*ns,31.6*ns,56.2*ns,
    100*ns,178*ns,316*ns,562*ns,
    1*us,1.78*us,3.16*us,5.62*us,
    10*us,17.8*us,31.6*us,56.2*us,
    100*us,178*us,316*us,562*us,
    1*ms,1.78*ms,3.16*ms,5.62*ms,
    10*ms,17.8*ms,31.6*ms,
##    32*timing_system.hsct,64*timing_system.hsct,128*timing_system.hsct,
]
repeats = 40
timepoints=timepoints*repeats
laser_mode = [0,1]
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
    timing_system.image_number.value = 0
    timing_system.pass_number.value = 0
    timing_system.pulses.value = 0
    upload()

def upload():
    Ensemble_SAXS.acquire(delays,laser_ons,
        passes=passes,image_numbers=image_numbers)

def stop(): Ensemble_SAXS.clear_queue()
    
def forever():
    """Continouly feed the queue, keeping collecting forever"""
    while True:
        start()
        while len(Ensemble_SAXS.queue) > 10: sleep(1)

print("timing_system.ip_address = %r" % timing_system.ip_address)
##print("Ensemble_SAXS.cache_enabled = %r" % Ensemble_SAXS.cache_enabled)
##print("Ensemble_SAXS.queue_length")
##print("Ensemble_SAXS.clear_queue()")
##print("Ensemble_SAXS.cache_size = 0")
##print("upload()")
print("start()")
print("stop()")
