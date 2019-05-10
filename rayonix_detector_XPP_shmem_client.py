#!/bin/env python
"""
Acquire a series of images using the XPP Rayonix detector with the
LCLS data acquisition system and a server running on a "mond" node

Setup: 
source ~schotte/Software/Lauecollect/setup_env.sh

DAQ Control: check Sync Sequence 3 - Target State: Allocate
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

Author: Friedrich Schotte, Jan 26, 2016 - Feb 1, 2016
"""
from time import time
import zmq
from logging import error,warn,info,debug
from numpy import nan,argsort,array
from threading import Thread
from os.path import basename
from thread import start_new_thread
__version__ = "1.0.2" # multiple command port number

class DAQImages(object):
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    servers = ["daq-xpp-mon05","daq-xpp-mon06"]
    ports = range(12300,12300+12)
    cmd_ports = range(12399,12399+5)
    for server in servers:
        for port in ports: socket.connect("tcp://%s:%d" % (server,port)) 
    socket.setsockopt(zmq.SUBSCRIBE, 'rayonix')
    socket.setsockopt(zmq.RCVTIMEO,1000) # ms

    cancelled = False
    completed = False

    def __init__(self):
        self.cmd_socket = self.context.socket(zmq.PUB)
        for port in self.cmd_ports:
            try: self.cmd_socket.bind("tcp://*:%s" % port); break
            except zmq.ZMQError: pass # Address already in use

    def get(self,nimages):
        """nimages: number of images to retreive"""
        images = []; fiducials = []
        for i in range(0,nimages):
            try:
                topic = self.socket.recv()
            except Exception,msg:
                error("Rayonix shmem: Image %2d/%d: recv: %s" % (i+1,nimages,msg))
                break
            fiducial = self.socket.recv_pyobj()
            image = self.socket.recv_pyobj()
            t = "Rayonix shmem: Image %d/%d %r: %d" % (i+1,nimages,image.shape,fiducial)
            if len(fiducials)>0: t += " (%+g)" % (fiducial-fiducials[-1])
            info(t)
            images.append(image); fiducials.append(fiducial)
        # The images are not guaranteed to be received in the order acquired.
        # Sort the images by "fiducials" timestamp.
        order = argsort(fiducials)
        images = [images[i] for i in order]
        return images

    def save_images(self,filenames):
        """Receive a series images from a server running on the
        "mond" nodes and save them as TIFF files.
        filename: list of absolute pathnames
        Returns immediately. Cancel with "abort".
        """
        self.completed = False
        start_new_thread(self.__save_images__,(filenames,))

    def __save_images__(self,filenames):
        """Receive a series images from a server running on the
        "mond" nodes and save them as TIFF files.
        filename: list of absolute pathnames
        Returns after the requested nuumber of images have been received or
        a timeout (1 s) has occured.
        """
        self.cancelled = False
        self.completed = False
        nimages = len(filenames)
        images = []; fiducials = []; threads = []
        for i in range(0,nimages):
            if self.cancelled:
                info("Rayonix shmem: Image reception cancelled.")
                break
            try:
                topic = self.socket.recv()
            except Exception,msg:
                error("Image %d/%d: recv: %s" % (i+1,nimages,msg))
                break
            fiducial = self.socket.recv_pyobj()
            image = self.socket.recv_pyobj()
            t = "Image %2d/%d %r: %d" % (i+1,nimages,image.shape,fiducial)
            if len(fiducials)>0: t += " (%+g)" % (fiducial-fiducials[-1])
            info(t)
            images.append(image); fiducials.append(fiducial)
            thread = Thread(target=save_image,args=(image,filenames[i]))
            thread.start()
            threads.append(thread)
        debug("Rayonix shmem: Waiting for all images to be saved...")
        for thread in threads: thread.join()
        debug("Rayonix shmem: All images saved.")
        # The images are not guaranteed to be received in the order acquired.
        # Sort the images by "fiducials" timestamp.
        # The "fiducial" timestamp in a 17-bit counter running at 360 Hz.
        # It wraps back to 0 from 131039, exactly every 364 seconds. 
        ##fiducials = array(fiducials)
        period = 131040
        if len(fiducials)>0 and max(fiducials)-min(fiducials) > period/2:
            fiducials[fiducials<period/2] += period
        order = argsort(fiducials)
        if not all(sorted(order) == order):
            debug("Rayonix shmem: Resorting images...")
            temp_names = [f+".tmp" for f in filenames]
            for f,t in zip(filenames,temp_names): move(f,t)
            temp_names = [temp_names[i] for i in order]
            for t,f in zip(temp_names,filenames): move(t,f)
            debug("Rayonix shmem: Images resorted...")
        self.completed = True

    def abort(self):
        """Cancel series acquisition"""
        info("Cancelling image reception...")
        self.cancelled = True

    __bin_factor__ = 4

    def get_bin_factor(self):
        """binning: integer, e.g. 1,2,4,8"""
        return self.__bin_factor__
    def set_bin_factor(self,binning):
        """binning: integer, e.g. 1,2,4,8"""
        debug("Rayonix shmem: bin factor %s" % binning)
        self.cmd_socket.send("cmd",zmq.SNDMORE)
        self.cmd_socket.send_pyobj(binning)
        self.__bin_factor__ = binning
    bin_factor = property(get_bin_factor,set_bin_factor)

daq_shmem_client = DAQImages()


def move(src,dest):
    """Rename of move a file or a different directory, overwriting an exising
    file"""
    from os.path import basename,exists
    from os import rename,remove
    try:
        if exists(dest): remove(dest)
        rename(src,dest)
    except OSError,msg: warn("Failed to move %r to %r: %s" % (src,dest,msg))

def save_image(image,filename):
    from numimage import numimage
    ##debug("Saving image %r..." % basename(filename))
    numimage(image).save(filename,"MCCD")
    ##debug("Image saved %r" % basename(filename))
    

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s")
    print("images = daq_shmem_client.get(20)")
    print("daq_shmem_client.bin_factor = 4")
