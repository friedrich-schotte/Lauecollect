#!/bin/env python
"""
Acquire a series of images using the XPP Rayonix detector with the
LCLS data acquisition system and a server running on a "mond" node

Setup: 
source ~schotte/Software/Lauecollect/setup_env.sh
"""
from xppdaq import xppdaq
from time import time
from time import sleep
from logging import info,warn,debug
import logging; logging.basicConfig(level=logging.DEBUG)
from rayonix_detector_XPP_client import daq_images

Nimages = 20
Nevents = (Nimages+1)*12 # Sometimes the last image is not recorded.

info("DAQ begin...")
xppdaq.begin(Nevents)

images = daq_images.get(Nimages+1)[:Nimages]

info("waiting for DAQ to finish...")
xppdaq.wait()
info("DAQ finished...")
xppdaq.disconnect()
info("disconnect from DAQ ...")
