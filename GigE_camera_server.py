#!/usr/bin/env python
"""
Prosilica GigE CCD cameras.
Author: Friedrich Schotte
Date created: 2017-04-13
Date last modified: 2018-10-30

Configuration:
    from DB import dbset
    dbset("GigE_camera.WideFieldCamera.camera.IP_addr","pico3.niddk.nih.gov")
    dbset("GigE_camera.MicroscopeCamera.camera.IP_addr","pico14.niddk.nih.gov")
    dbset("GigE_camera.WideFieldCamera.ip_address","pico20.niddk.nih.gov:2001")
    dbset("GigE_camera.MicroscopeCamera.ip_address","pico20.niddk.nih.gov:2002")
"""
__version__ = "2.0.1" # logging 

from logging import debug,info,warn,error

from GigE_camera import GigE_camera

class Camera(GigE_camera):
    from persistent_property import persistent_property
    IP_addr = persistent_property("GigE_camera.{name}.camera.IP_addr",
        "pico3.niddk.nih.gov")
    use_multicast = persistent_property("GigE_camera.{name}.use_multicast",False)
    buffer_size = 10
    
    def __init__(self,name):
        GigE_camera.__init__(self)
        self.name = name
        self.filenames = {}

    def get_acquiring(self):
        return self.acquisition_started
    def set_acquiring(self,value):
        if value: self.start()
        else: self.stop()
    acquiring = property(get_acquiring,set_acquiring)
 
    def monitor(self):
        if self.auto_resume: self.resume()
        self.save_current_image()

    def acquire_sequence(self,framecounts,filenames):
        """Save a series of images"""
        for framecount,filename in zip(framecounts,filenames):
            if not framecount in self.filenames:
                self.filenames[framecount] = []
                if not filename in self.filenames[framecount]:
                    self.filenames[framecount] += [filename]

    def save_current_image(self):
        """Check whether the last acquired image needs to be saved
        and save it."""
        if len(self.filenames) > 0:
            frame_count = self.frame_count
            if frame_count in self.filenames:
                for filename in self.filenames[frame_count]:
                    self.save_image(self.rgb_data,filename)
                del self.filenames[frame_count]

    def save_image(self,rgb_data,filename):
        from PIL import Image
        image = Image.new('RGB',(self.width,self.height))
        image.frombytes(rgb_data)
        image = self.rotated_image(image)
        from os import makedirs; from os.path import dirname,exists
        if not exists(dirname(filename)): makedirs(dirname(filename))
        info("Saving %r" % filename)
        from thread import start_new_thread
        start_new_thread(image.save,(filename,))

    # in degrees counter-clockwise
    orientation = persistent_property("{name}.Orientation",0)

    def rotated_image(self,image):
        """image: PIL image object"""
        return image.rotate(self.orientation)
        
camera = Camera("MicroscopeCamera")
self = camera # for debugging

from tcp_server_single_threaded import tcp_server
server = tcp_server(globals=globals(),locals=locals())
server.ip_address_and_port_db = "GigE_camera.MicroscopeCamera.ip_address"
server.idle_timeout = 1.0
##server.idle_callbacks += [camera.monitor]
##server.idle_callbacks += [camera.resume]
##server.idle_callbacks += [camera.save_current_image]

def run(name):
    camera.name = name
    server.ip_address_and_port_db = "GigE_camera.%s.ip_address" % name
    server.run()

def set_defaults():
    from DB import dbset
    dbset("GigE_camera.WideFieldCamera.camera.IP_addr","pico3.niddk.nih.gov")
    dbset("GigE_camera.MicroscopeCamera.camera.IP_addr","pico14.niddk.nih.gov")
    dbset("GigE_camera.WideFieldCamera.ip_address","pico20.niddk.nih.gov:2001")
    dbset("GigE_camera.MicroscopeCamera.ip_address","pico20.niddk.nih.gov:2002")
    

if __name__ == "__main__":
    from time import time # for timing
    import logging
    logging.basicConfig(level=logging.INFO,format="%(asctime)s: %(message)s")
    from sys import argv
    if len(argv) > 1: run(argv[1])
    print('camera.acquiring = True')
    print('camera.monitor()')
    print('run("MicroscopeCamera")')
    ##run("MicroscopeCamera")
