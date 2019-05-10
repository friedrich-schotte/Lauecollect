#!/bin/env python
""" This is a python script that will analyse images triggered by the FPGA
    It will be a standalone unit that can be called from either "Optical Sample Freeze Detector" or
    LAUE Crystalography image analyser.
    
    Core functions:
    - get background array
    - get current array
    - get difference array
    - save array as image


Author: Valentyn Stadnytskyi
Date created: 2018-03-08
Date last modified: 2018-03-28

This used to be optical_image_analyser_rgb
but I need to have a generalized code to use it for both LAUE and SAXS|WAXS

The images are saved in correct orientation. This was achieved by rotating the array camera.RGB_array provides.
The arrays dimensionality is (vertical, horizontal, depth) or (y,x, depth) where depth is RGB or RGBK depending on dimensionality.
"""
__version__ = "1.1" # Friedrich Schotte: WideFieldCamera (with uppercase F)

import matplotlib.pyplot as plt
from numpy import mean, transpose, std,array,hypot , abs, zeros, savetxt, loadtxt,save ,load ,uint8, uint16, reshape, asarray
from numpy.ma import masked_array
#import numpy.ma as ma
#plt.ion()
from time import sleep, time
from PIL import Image
from persistent_property import persistent_property
from datetime import datetime
from scipy import ndimage, misc
import os
from logging import debug,info,warn,error
from thread import start_new_thread
from CA import caget


class Camera_image_analyser(object):
    camera_name = persistent_property('camera name', '')
    cameraSettingGain = persistent_property('camera Setting Gain', 6)
    cameraSettingExposureTime = persistent_property('camera Setting exposure time', 0.072)
    pixels_to_use_h = persistent_property('pixels_to_use_h', (300,700))
    pixels_to_use_v = persistent_property('pixels_to_use_v', (300,700))
    
    def __init__(self, name = 'camera_image_analyser', camera_name = 'MicroscopeCamera'):
        self.name = name
        self.camera_name = camera_name #WideFieldCamera #MicroscopeCamera
        self.frame_count = camera.frame_count
        self.image_timeout = 10
        #self.pixels_to_use_v =  (509,515)
        #self.pixels_to_use_h =  (0,1360)
        self.difference_array = zeros((self.pixels_to_use_v[1]-self.pixels_to_use_v[0],self.pixels_to_use_h[1]-self.pixels_to_use_h[0]))
        self.background_image_flag = False
        self.logFolder = os.getcwd() + '/' + self.name +'/'
        self.save_every_image = False
        if os.path.exists(os.path.dirname(self.logFolder)):
            pass
        else:
            os.makedirs(os.path.dirname(self.logFolder))
        if os.path.exists(os.path.dirname(self.logFolder+ 'Laue/Archive/') ):
            pass
        else:
            os.makedirs(os.path.dirname(self.logFolder+ 'Laue/Archive/'))
        if os.path.exists(os.path.dirname(self.logFolder+ 'Laue/Images/') ):
            pass
        else:
            os.makedirs(os.path.dirname(self.logFolder+ 'Laue/Images/'))
        try:
            self.background_array_filename = 'background_default'
            self.background_array = load(self.logFolder + self.background_array_filename + '.npy')
            self.background_image_flag = True
            debug('got bckg image from the drive')
        except:
            debug('couldn"t load bckg image')
            self.background_image_flag = False
            
        self.logfile = self.logFolder + self.name + '.log'
        if os.path.isfile(self.logfile):
            pass
        else:
            f = open(self.logfile,'w')
            timeRecord = time()
            f.write('####This experiment started at: %r and other information %r \r\n'  %(timeRecord,'Other Garbage'))
            f.write('time,\r\n')
            f.close()
            
    def get_image(self):
        from  numpy import rot90, float16, flipud
        if self.is_new_image():
            self.current_image = flipud(rot90(camera.RGB_array, k = 1, axes = (0,2)))
            self.frame_count = camera.frame_count
            if self.save_every_image:
               start_new_thread(self.save_array_as_image,(self.current_image,))
            res = True
        else:
            res = False
        return res

    def mask_current_image(self):
        debug('mask_current_image function')
        self.current_array = self.mask_array(self.current_image)

    
    def mask_array(self,arr):
        from numpy import zeros, float16
        arr_res = zeros((self.pixels_to_use_v[1]-self.pixels_to_use_v[0],self.pixels_to_use_h[1]-self.pixels_to_use_h[0],arr.shape[2]+1))
        arr_R = arr_res[:,:,0] = arr[self.pixels_to_use_v[0]:self.pixels_to_use_v[1],self.pixels_to_use_h[0]:self.pixels_to_use_h[1],0] #R
        arr_G = arr_res[:,:,1] = arr[self.pixels_to_use_v[0]:self.pixels_to_use_v[1],self.pixels_to_use_h[0]:self.pixels_to_use_h[1],1] #G
        arr_B = arr_res[:,:,2] = arr[self.pixels_to_use_v[0]:self.pixels_to_use_v[1],self.pixels_to_use_h[0]:self.pixels_to_use_h[1],2] #B
        arr_res[:,:,3] = arr_R + arr_G +arr_B #K
        return arr_res

 

    def is_new_image(self):
        from time import time
        if self.frame_count > camera.frame_count: #this is for wrapping arround
            self.frame_count = 0
        t0 = time()
        while self.frame_count >= camera.frame_count and time() - t0 < self.image_timeout:
            sleep(0.2)
        if self.frame_count < camera.frame_count:
            res = True
        else:
            res = False
        return res

    def get_background_array(self):
        debug('getting bacgkround array')
        self.get_current_array()
        self.background_array = self.current_array
        self.background_image_flag = True
        self.save_to_pickle_file(filename = self.background_array_filename, data = self.background_array)
        
    def run_get_background_array(self):
       self.background_image_flag = False
       start_new_thread(self.get_background_array,())
    
    def get_difference_array(self):
        #wait for new image
        if self.background_image_flag:
            self.get_current_array()
            self.difference_array = self.current_array - self.background_array
            res = True 
        else:
            res = False
        return res
    
    def get_current_array(self):
        #wait for new image
        debug('getting bacgkround array')
        self.get_image()
        self.mask_current_image()


    def save_array_as_image(self,arr, filename = ''):
        import PIL
        from numpy import uint8, rot90
        from time import time
        image = PIL.Image.fromarray(arr, 'RGB')
        if len(filename) == 0:
            filename = str(time()) + '.tiff'
        image.save(self.logFolder+'Images/'+ filename)
    
    def save_to_pickle_file(self,data, filename = "current_array"):
        import numpy
        numpy.save(self.logFolder + filename, data, allow_pickle = True)
    """plotting functions"""
    def plot_array(self,  arr):
        from numpy import float32
        if arr.min()<0: #for difference image to be plotted properly
            plt.imshow(arr[:,:,0:3]-arr.min())
        else:
            plt.imshow(arr[:,:,0:3])
        plt.colorbar()
        plt.show()

        
from GigE_camera_client import Camera
camera = Camera("MicroscopeCamera")
laue_image_analyser = Camera_image_analyser(name = 'LAUE_image_analyser', camera_name = 'MicroscopeCamera') #for LAUE crystalography


if __name__ == "__main__":
    import logging
    from tempfile import gettempdir
    import logging

    logfile = gettempdir() + "/logging/camera_image_analyser.log"
    logger = logging.getLogger('camera_image_analyser')
    hdlr = logging.FileHandler(logfile)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr) 
    logger.setLevel(logging.DEBUG)

    self = camera_image_analyser #for testing
    info('Time Start: %r' % str(datetime.now()))



