#!/bin/env python
"""
More or Less generic python code for image analysis.

functions:
property: is_new_image returns True\False if there is new image
method: get_image return 4,X,Y image where 0 - R, 1 - G, 2 - B, 3 - K - colors

Valentyn Stadnytskyi
created: Feb 29 2018
last updated: July 2, 2018


Microscope Camera chip orientations:
NIH: vertical; APS: horizontal;
Vertical:
DxWxH = 3,1024,1360
*----
|   |
|   |
|   |
|   |
|---|
* is (0,0) pixel
Horizontal:
DxWxH = 3,1360,1024
|---------------|
|               |
|               |
*---------------|
* is (0,0) pixel
"""
__version__ = '0.1'


import matplotlib.pyplot as plt
from logging import info,warn,debug, error
from numpy import mean, transpose, std,array,hypot , abs, zeros, savetxt,loadtxt,save,load ,uint8, uint16, reshape, asarray
from numpy.ma import masked_array
from time import sleep, time
from PIL import Image
from threading import Thread, Condition
from persistent_property import persistent_property
from datetime import datetime
from scipy import ndimage, misc
import os
from thread import start_new_thread
from CAServer import casput,casdel
from CA import caget
import traceback


import os

class Image_analyzer(object):
    cameraName = persistent_property('camera name', '')
    fieldOfAnalysis = persistent_property('field of analysis', '')
    cameraSettingGain = persistent_property('camera Setting Gain', 6)
    cameraSettingExposureTime = persistent_property('camera Setting exposure time', 0.072)
    background_image_filename = persistent_property('background image filename', 'background_default')
    mask_image_filename = persistent_property('mask image filename', 'mask_default')
    frozen_threshold = persistent_property('freezing threshhold', 0.08)


    def __init__(self, name = 'freeze_detector'):
        self.name = name
        #camera.exposure_time = self.cameraSettingExposureTime
        #camera.gain = self.cameraSettingGain
##        self.frozen_threshold = 0.1
##        self.frozen_threshold_temperature = -15.0
##
##        #orientation of the camera
##        #self.orientation = 'vertical' #
##        self.orientation = 'horizontal' #
##
##
##        self.difference_array = zeros((1,1))
##        self.background_array = zeros((1,1))
##        self.mask_array = zeros((1,1))
##        self.background_image_flag = False

        #self.analyse_dict = {}

    def init(self, camera_name = 'MicroscopeCamera'):
        self.camera_name = camera_name #Microfluidics camera #MicroscopeCamera
        self.imageCounter = camera.frame_count
        #camera.exposure_time = self.cameraSettingExposureTime
        #camera.gain = self.cameraSettingGain
        # self.logFolder = os.getcwd() + '/optical_image_analyzer/' + self.name + '/'
        # if os.path.exists(os.path.dirname(self.logFolder)):
        #     pass
        # else:
        #     os.makedirs(os.path.dirname(self.logFolder))
        # if os.path.exists(os.path.dirname(self.logFolder+ 'Archive/') ):
        #     pass
        # else:
        #     os.makedirs(os.path.dirname(self.logFolder+ 'Archive/'))
        # self.background_image_filename = 'background_default_rgb.tiff'
        # try:
        #     #self.background_image = Image.open(self.logFolder + self.background_image_filename)
        #     self.background_array = load(self.logFolder + 'background_default_rgb.npy')
        #     self.background_image_flag = True
        #     info('got bckg image from the drive')
        # except:
        #     warn('couldn"t load bckg image')
        #     self.background_image_flag = False
        #
        # self.logfile = self.logFolder +'sample_frozen_image_rgb.log'
        # my_file = os.path.isfile(self.logfile )
        # if my_file:
        #     pass
        # else:
        #     f = open(self.logfile,'w')
        #     timeRecord = time()
        #     f.write('####This experiment started at: %r and other information %r \r\n'  %(timeRecord,'Other Garbage'))
        #     f.write('time,imageCounter, temperature, mean, mean_R,mean_G,mean_B,stdev,stdev_R,stdev_B,stdev_G\r\n')
        #     f.close()
    def get_is_new_image(self):
        """
        """
        try:
            temp = camera.acquiring
            if temp != True and temp != False:
                print("Camera status: %r" %(temp))
                camera.acquiring = False
                sleep(0.1)
        except:
            print('error at this line: if camera.acquiring != True and camera.acquiring != False: camera.acquiring = Flase')
        if not camera.acquiring: camera.acquiring = True
        idx = 0
        frame_count = camera.frame_count
        if self.imageCounter - frame_count > 100:
            self.imageCounter = 0
        if self.imageCounter < frame_count:
            flag = True
        else:
            flag = False
        info('Image counter: %r' % self.imageCounter)
        return flag
    is_new_image = property(get_is_new_image)

    def get_image(self, timeout = 5, image = None):
        """
        return an array with RGBK colors and convers it to int 16 instead of int 8, for the K array
        """
        from time import time
        from numpy import insert
        flag_fail = False
        if image == None:
            t = time()
            while t + timeout > time():
                if self.is_new_image:
                    tmp = camera.RGB_array.astype('int16')
                    img = zeros(shape = (tmp.shape[0]+1,tmp.shape[1],tmp.shape[2]), dtype = 'int16')
                    img[0,:,:] = tmp[0,:,:]
                    img[1,:,:] = tmp[1,:,:]
                    img[2,:,:] = tmp[2,:,:]
                    img[3,:,:] = tmp[0,:,:]+tmp[1,:,:]+tmp[2,:,:]
                    self.imageCounter = camera.frame_count
                    flag_fail = False
                    break
                else:
                    img = None
                    flag_fail = True

                sleep(0.250)
            if flag_fail:
                info('get_image has timed-out: restarting the camera.acquiring')
                camera.acquiring = False
                sleep(2)
                camera.acquiring = True
                sleep(0.25)
        else:
            img = img.astype('int16')
            img[3,:,:] = img[0,:,:] + img[1,:,:] + img[2,:,:]

        return img

    def frame_count(self):
        try:
            count = camera.frame_count
        except:
            error(traceback.format_exc())
            count = -1
        return count

    def create_mask(self,arr, anchors = [(0,0),(1,1)]):
        """
        defines region of interest between anchor points defined by anchors. Yields rectangular shape
        """
        from numpy import ma, zeros, ones
        shape = arr.shape
        mask = ones(shape, dtype = 'int16')
        try:
            for i in range(anchors[0][0],anchors[1][0]):
                for j in range(anchors[0][1],anchors[1][1]):
                    mask[:,i,j] = 0
        except:
            error(traceback.format_exc())
            mask = None
        return mask

    def mask_array(self,array,mask):
        from numpy import ma
        arr_res = ma.masked_array(array, mask)
        return arr_res

    def masked_section(self,array, anchors = [(0,0),(1,1)]):
        x1 = anchors[0][0]
        y1 = anchors[0][1]
        x2 = anchors[1][0]
        y2 = anchors[1][1]
        return array[:,x1:x2,y1:y2]




    def save_array_as_image(self,arr, filename):
        image = Image.new('RGB',(1360,1024))
        image.frombytes(arr.T.tostring())
        image.save(filename)


    def rgb2gray(self,rgb):
        r, g, b = rgb[:,:,0], rgb[:,:,1], rgb[:,:,2]
        gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
        return gray



    def get_background_array(self):
        arr = self.get_image()
        self.background_array = arr
        return True


    def set_background_array(self, filename = 'blank'):
       self.background_image_flag = False
       start_new_thread(self.get_background_array,())


    def plot_slices_difference(self):
        for i in range(7):
            plt.plot(image_analyser.difference_array[0,:,i])
        plt.show()
    def plot_difference(self):
        plt.subplot(121)
        plt.imshow(self.difference_image)
        plt.colorbar()
        plt.subplot(122)
        plt.imshow(abs(self.difference_image))
        plt.colorbar()
        plt.show()

    def plot_background(self):
        plt.subplot(121)
        plt.imshow(self.background_image)
        plt.colorbar()
        plt.subplot(122)
        plt.imshow(self.mask_image)
        plt.colorbar()
        plt.show()

    def plot(self,image):

        plt.imshow(image)
        plt.colorbar()
        plt.show()

    def save_images(self):
        from PIL import Image
        import logging; from tempfile import gettempdir
        #/var/folders/y4/cw92kt415kz7wtk13fkjhh2r0000gn/T/samplr_frozen_opt.log'
        import os

        file_path = gettempdir() + "/Images/Optical_images_march4/log.log" # gettempdir + "/Optical_images/log.log"
        directory = os.path.dirname(file_path)

        try:
            os.stat(directory)
        except:
            os.mkdir(directory)

        for i in range(360):
            sleep(10)
            while self.is_new_image() != True:
                sleep(0.05)
            if self.is_new_image():
                img = Image.fromarray(camera.RGB_array.transpose((-1,0,1)).transpose((-1,0,1)))
                temp = str(caget("NIH:TEMP.RBV"))
                img.save(directory +'/_T_'+temp + '_t_' +str(time())+'.tiff')
                print('saving',directory +'_T_'+temp + '_t_' +str(time())+'.tiff')

    def scan_saved_images(self):
        pass

    def load_image_from_file(self, filename = ""):
        if len(filename)>0:
            img = Image.open(filename)
            arr = asarray(img, dtype="int16" ).transpose((-1,0,1))
            return arr
        else:
            return None


    def test_load_current_1_image(self):
        self.test_current_1 = Image.open(self.logFolder + 'current_rgb.tiff')

    def test_save_current_s_image(self):
        self.test_current_s.save(self.logFolder + 'current_test_saved.tiff')

    def test_load_current_s_image(self):
        self.test_current_s = Image.open(self.logFolder + 'current_test_saved.tiff')

    def test_load_current_2_image(self):
        self.test_current_2 = Image.open(self.logFolder + 'current_test_2.tiff')



from GigE_camera_client import Camera

#camera = Camera("LabMicroscope")
camera = Camera("MicroscopeCamera")
image_analyzer = Image_analyzer()

if __name__ == "__main__":
    import logging; from tempfile import gettempdir
    #/var/folders/y4/cw92kt415kz7wtk13fkjhh2r0000gn/T/samplr_frozen_opt.log'
    logfile = gettempdir()+"/optical_image_analyser.log"
    ##print(logfile)
    logging.basicConfig( level=logging.DEBUG,
        format="%(asctime)s %(levelname)s: %(message)s",
        filename=logfile,
    )
    self = image_analyzer
    print('Time Start: %r' % str(datetime.now()))
    print('arr = image_analyzer.get_image()')
    print("image_analyzer.plot()")
    print("image_analyzer.plot_difference()")
    print('file_path = gettempdir() + "/Images/Optical_images/')
    debug('?')
