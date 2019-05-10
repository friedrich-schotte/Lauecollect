"""Data Collection for Wang Group
Author: Friedrich Schotte
Date created: 2018-05-24
Date last modified: 2018-05-24
"""
__version__ = "1.0" #

from pdb import pm # for debugging
import logging
logging.basicConfig(level=logging.INFO,format="%(asctime)s: %(levelname)s %(message)s")
from instrumentation import ccd,timing_sequencer,timing_system
from numpy import *

timepoints = [1]
nlaser = 0
directory = "/net/mx340hs/data/pub/junk/wang/"
file_basename = "Test5"

filenames = ["%s/%s_%gs.mccd" % (directory,file_basename,t) for t in timepoints]

dt = timing_system.hsct*48
it0 = max(nlaser,2)+1 # number seqeunces before t=0
N = it0 + int(rint(max(timepoints)/dt))+1+50
# Laser pulse burst is centered at t=0.
laser_on = array([0]*N)
nlaser1 = nlaser; nlaser2 = nlaser-nlaser1
laser_on[it0-nlaser1:it0+nlaser2] = 1

xray_on = array([0]*N)
for t in timepoints: xray_on[it0 + int(rint(t/dt))] = 1
ms_on = xray_on
# Trigger X-ray detector after X-ray ms shutter pulse
xdet_on = roll(ms_on,1) 
# Additional detector triggers to clear zingers (must be >100 ms ealier)
xdet_on += roll(ms_on,-2)

image_numbers = cumsum(xdet_on)
save_filenames = [""]*max(image_numbers)
j = 0
for i in range(0,N):
    if image_numbers[i] > 0 and xray_on[i-1]:
        save_filenames[image_numbers[i]-1] = filenames[j]
        j += 1
save_image_numbers = range(1,max(image_numbers)+1)

waitt = array([dt]*N)
npulses = array([1]*N)

def setup():
    timing_sequencer.acquire(laser_on=laser_on,
        npulses=npulses,waitt=waitt,burst_waitt=waitt,
        image_numbers=image_numbers,
        ms_on=ms_on,xdet_on=xdet_on,
        xosct_on=xray_on,losct_on=laser_on)
    ccd.acquire_images(save_image_numbers,save_filenames)

def start(): timing_sequencer.acquisition_start()

def finish():
    from time import sleep
    while timing_sequencer.image_number < max(save_image_numbers): sleep(dt)
    timing_sequencer.acquisition_cancel()

def cancel(): timing_sequencer.acquisition_cancel()

def collect():
    setup()
    start()
    finish()
    
#print("timing_system.ip_address = %r" % timing_system.ip_address)
#print("")
#print("setup()")
#print("start()")
#print("finish()")
#print("collect()")
collect()
