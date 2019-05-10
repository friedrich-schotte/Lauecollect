"""Author: Friedrich Schotte, Oct 21, 2015 - Mar 11, 2016
"""
__version__ = "1.6" # 1/hscf -> timing_system.hsct

from pdb import pm # for debugging
from timing_system import timing_system,ps,ns,us,ms
from timing_sequence import timing_sequencer
from time import sleep,time
from numpy import *
import logging
from tempfile import gettempdir
logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s",
    filename=gettempdir()+"/lauecollect_debug.log")

timepoints = [
    100*ps,178*ps,316*ps,562*ps,
    1*ns,1.78*ns,3.16*ns,5.62*ns,
    10*ns,17.8*ns,31.6*ns,56.2*ns,
    100*ns,178*ns,316*ns,562*ns,
    1*us,1.78*us,3.16*us,5.62*us,
    10*us,17.8*us,31.6*us,56.2*us,
    100*us,178*us,316*us,562*us,
    1*ms,1.78*ms,3.16*ms,5.62*ms,
    10*ms,17.8*ms,31.6*ms,
    32*timing_system.hsct,64*timing_system.hsct,128*timing_system.hsct
]
timepoints=timepoints
laser_mode = [0,1]
npulses = 2

ps_lxd = array([t for t in timepoints for l in laser_mode])
pst_on = array([l for t in timepoints for l in laser_mode])
image_numbers = arange(1,len(ps_lxd)+1)
npulses = [1 if l else 12 for l in pst_on]
waitt = [96*timing_system.hsct if l else 8*timing_system.hsct for l in pst_on]
ms_on = [1 if l else 0 for l in pst_on]
xatt_on = [0 if l else 1 for l in pst_on]

# for debugging
laser_on = delays = lxd = nsq_on = s3_on = None
self = timing_sequencer

##image_numbers = array([62,64,66,68,70])
##ps_lxd = ps_lxd[image_numbers-1]
##laser_ons = laser_ons[image_numbers-1]
##npulses = npulses[image_numbers-1]

def start():
    timing_system.image_number.value = 0
    timing_system.pass_number.value = 0
    timing_system.pulses.value = 0
    upload()

def upload():
    timing_sequencer.acquire(ps_lxd=ps_lxd,pst_on=pst_on,
        npulses=npulses,waitt=waitt,
        image_numbers=image_numbers,
        ms_on=ms_on,xatt_on=xatt_on)
    
def test():
    while True:
        start()
        while len(timing_sequencer.queue) > 10: sleep(1)

print("timing_system.ip_address = %r" % timing_system.ip_address)
print("timing_sequencer.cache_enabled = %r" % timing_sequencer.cache_enabled)
print("timing_sequencer.queue_length")
print("timing_sequencer.clear_queue()")
print("timing_sequencer.abort()")
print("timing_sequencer.update()")
print("timing_sequencer.cache_clear()")
print("t=time(); upload(); time()-t")
print("t=time(); start(); time()-t")
print("test()")
