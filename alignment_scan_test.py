"""Friedrich Schotte, Jan 29, 2016 - Jan 31, 2016"""
from pdb import pm
from logging import warn
try: from rayonix_detector_XPP import ccd
except: warn("module 'rayonix_detector_XPP' not imported")
from timing_sequence import timing_sequencer
from timing_system import timing_system
from ImageViewer import show_images
from xppdaq import xppdaq # for xppdaq.endrun()
__version__ = "1.1.1"

import logging
from tempfile import gettempdir
logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s",
    filename=gettempdir()+"/lauecollect_debug.log")

nimages = 20
dir = "/reg/neh/operator/xppopr/experiments/xppj1216/Data/Test/Test3/alignment"
filenames = [dir+"/%03d.mccd" % i for i in range(0,nimages)]
image_numbers = range(1,nimages+1)
laser_on = [0]*nimages
ms_on = [0]*nimages
xatt_on = [1]*nimages
npulses = [10]*nimages

def test_FPGA():
    timing_sequencer.inton_sync = 0
    timing_system.image_number.value = 0
    timing_system.pulses.value = 0
    timing_sequencer.acquire(laser_on=laser_on,ms_on=ms_on,xatt_on=xatt_on,
        npulses=npulses,image_numbers=image_numbers)

def test_DAQ():
    ccd.acquire_images_triggered(filenames)
    show_images(filenames)

def test():
    test_FPGA()
    test_DAQ()

print("test_FPGA()")
print("test_DAQ()")
print("test()")
