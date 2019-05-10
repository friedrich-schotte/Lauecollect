#!/bin/env python
"""
Acquire a series of images using the XPP Rayonix detector with the
LCLS data acquisition system and a server running on a "mond" node

Setup: 
source ~schotte/Software/Lauecollect/setup_env.sh

DAQ Control: Configuration - Type BEAM_PP - check Sync Sequence 3 - Target State: Allocate
(if grayed out: daq.diconnect())

xpphome -> LSLS tab -> Event Sequencer -> Event Code Sequence 3 -> Start

ssh daq-xpp-mon05
ssh daq-xpp-mon06

~xppopr/experiments/xppj1216/software/start_zmqsend.sh:
source /reg/d/iocCommon/All/xpp_env.sh
export TIME=`date +%s`
export NAME="zmqsend.$HOSTNAME.$TIME"
source /reg/g/psdm/etc/ana_env.sh
$PROCSERV --logfile /tmp/$NAME --name zmqsend 40000 ./zmqsend.cmd

~xppopr/experiments/xppj1216/software/start_zmqsend.sh:
source /reg/g/psdm/etc/ana_env.sh
`which mpirun` -n 12 python /reg/neh/home/cpo/ipsana/xppj1216/zmqpub.py

Monitor status of servers:
telnet daq-xpp-mon05 40000
telnet daq-xpp-mon06 40000
Control-X, Control-R to restart

Author: Friedrich Schotte, Jan 26, 2016 - Jan 31, 2016
"""
from xppdaq import xppdaq
from time import time,sleep
from logging import info,warn,debug
from rayonix_detector_XPP_shmem_client import daq_shmem_client
from numimage import numimage
from thread import start_new_thread
from os.path import dirname
__version__ = "1.1.1" # hardware bin factor

class rayonix_detector(object):
    __state__ = "idle"
    cancelled = False
    
    def __init__(self,*args,**kwargs):
        # for compatibility with "rayonix_detector" module
        pass
    
    def acquire_images_triggered(self,filenames):
        """filename: list of absolute pathnames"""
        start_new_thread(self.__acquire_images_triggered__,(filenames,))

    def __acquire_images_triggered__(self,filenames):
        """filename: list of absolute pathnames"""
        self.cancelled = False

        # The first image in frame transfer mode has a lot of zingers and needs to be
        # discarded.
        # The detector trigger is connected as external trigger to the FPGA.
        # The trigger pulse for the first image starts the timing seqence.
        dir = dirname(filenames[0]) if len(filenames) > 0 else ""
        if dir == "": dir = "."
        filenames = [dir+"/discard.mccd"]+filenames

        Nimages = len(filenames)
        Nevents = (Nimages)*12 

        info("DAQ begin...")
        xppdaq.begin(Nevents)
        info("DAQ started...")
        self.__state__ = "acquiring series"

        if not self.cancelled: daq_shmem_client.save_images(filenames)
        while not daq_shmem_client.completed and not self.cancelled: sleep(0.05)
        if self.cancelled: daq_shmem_client.abort()

        info("DAQ waiting...")
        xppdaq.wait()
        info("DAQ ending run...")
        xppdaq.endrun()
        info("DAQ run done.")
        self.__state__ = "idle"

    hardware_bin_factor = 2

    def get_bin_factor(self):
        """Software bin factor x hardware bin factor"""
        return daq_shmem_client.bin_factor*self.hardware_bin_factor
    def set_bin_factor(self,value):
        daq_shmem_client.bin_factor = value/self.hardware_bin_factor
    bin_factor = property(get_bin_factor,set_bin_factor)

    def filesize(self,bin_factor):
        """Image file size in bytes including headers
        bin_facor: 2,4,8,16"""
        image_size = 3840/bin_factor # MS170HS
        headersize = 4096
        image_nbytes = 2*image_size**2
        filesize = headersize+image_nbytes
        return filesize
    
    def state(self):
        """What is the detector currently doing?"""
        return self.__state__

    def abort(self):
        """Cancel series acquisition"""
        self.cancelled = True

    def read_bkg(self):
        """Reads a fresh the backgound image, which is substracted from every
        image after readout before the correction is applied."""
        # for compatibility with "rayonix_detector.py" module
        return True

    def bkg_valid(self):
        """Does detector software have a the backgound image for the current
        bin mode, which is substracted from every image after readout before
        the correction is applied."""
        # for compatibility with "rayonix_detector.py" module
        return True

ccd = rayonix_detector()
    

if __name__ == "__main__":
    import logging
    from tempfile import gettempdir
    logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s",
        filename=gettempdir()+"/lauecollect_debug.log")
    dir = "/reg/neh/operator/xppopr/experiments/xppj1216/Data/Test/Test1/alignment"
    filenames = [dir+"/%03d.mccd" % i for i in range(0,20)]
    print("ccd.bin_factor = 8")
    print("ccd.acquire_images_triggered(filenames)")
    print("ccd.acquire_images_triggered(filenames); sleep(1); ccd.abort()")
    print("ccd.state()")
    print("ccd.abort()")
