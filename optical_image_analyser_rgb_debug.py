
"""
This is a python script that will analyse images triggered by the FPGA
Valentyn Stadnytskyi, Feb 29 2018 - May 25 2018
"""
__version__ = '1.4'


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


import os

class Image_analyser(object):
    cameraName = persistent_property('camera name', '')
    fieldOfAnalysis = persistent_property('field of analysis', '')
    cameraSettingGain = persistent_property('camera Setting Gain', 6)
    cameraSettingExposureTime = persistent_property('camera Setting exposure time', 0.0089)
    background_image_filename = persistent_property('background image filename', 'background_default')
    mask_image_filename = persistent_property('mask image filename', 'mask_default')
    frozen_threshold = persistent_property('freezing threshhold', 0.08)
    pixels_to_use = persistent_property('pixels to use', (300,700))
    
    def __init__(self, name = 'sample_frozen_optical' , pixels_to_use = (509,515)):
        #info('Code has started')
        self.name = name
        self.cameraName = 'MicroscopeCamera' #Microfluidics camera #MicroscopeCamera
        self.imageCounter = camera.frame_count
        self.daemon = True  # OK for main thread to exit even if instance is still running
        self.paused = True  # start out paused
        #self.state = Condition() #<- Condition() is part of treading library
        #camera.exposure_time = self.cameraSettingExposureTime
        #camera.gain = self.cameraSettingGain
        self.frozen_threshold = 0.1
        self.frozen_threshold_temperature = -15.0
        self.pixels_to_use_1 =  (697-75,825-75)
        self.pixels_to_use_2 =  (865+20,993+20)
        
        self.difference_array = zeros((1,1))
        self.background_image_flag = False
        #self.logFolder = os.getcwd() + '/Optical_freeze_detector/' + self.name + '/'
        self.analyse_dict = {}
        #self.init()
        pass
        
    def init(self):    
        if os.path.exists(os.path.dirname(self.logFolder)):
            pass
        else:
            os.makedirs(os.path.dirname(self.logFolder))
        if os.path.exists(os.path.dirname(self.logFolder+ 'Archive/') ):
            pass
        else:
            os.makedirs(os.path.dirname(self.logFolder+ 'Archive/'))
        self.background_image_filename = 'background_default_rgb.tiff'
        try:
            #self.background_image = Image.open(self.logFolder + self.background_image_filename)
            self.background_array = load(self.logFolder + 'background_default_rgb.npy')
            self.background_image_flag = True
            info('got bckg image from the drive')
        except:
            warn('couldn"t load bckg image')
            self.background_image_flag = False
            
        self.logfile = self.logFolder +'sample_frozen_image_rgb.log'
        my_file = os.path.isfile(self.logfile )
        if my_file:
            pass
        else:
            f = open(self.logfile,'w')
            timeRecord = time()
            f.write('####This experiment started at: %r and other information %r \r\n'  %(timeRecord,'Other Garbage'))
            f.write('time,imageCounter, temperature, mean, mean_R,mean_G,mean_B,stdev,stdev_R,stdev_B,stdev_G\r\n')
            f.close()

    def run(self):
        while True:
            with self.state:
                if self.paused:
                    self.state.wait()
            sleep(1)
            info('Execujtable code goes here')
            
    def resume(self):
        with self.state:
            self.paused = False
            self.state.notify()  # unblock self if waiting see self.state.wait(). sends notification to the Thread

    def pause(self):
        with self.state:
            self.paused = True  # make self block and wait
            
    def get_image(self):
        camera.acquiring = True # make sure images get always updated
        img = camera.RGB_array
        self.imageCounter = camera.frame_count
        return img

    def frame_count(self):
        return camera.frame_count

    def get_masked_array(self):
        from numpy import zeros
        arr = self.get_image()
        arr_res = self.convert_masked_array(arr)
        return arr_res

        
    def convert_masked_array(self,arr,pixels_to_use):
        from numpy import zeros
        arr_res = zeros((arr.shape[0]+1,arr.shape[1],pixels_to_use[1]-pixels_to_use[0]+1))
        arr_R = arr_res[1,:,:] = arr[0,:,pixels_to_use[0]:pixels_to_use[1]+1]*1.0 #R
        arr_G = arr_res[2,:,:] = arr[1,:,pixels_to_use[0]:pixels_to_use[1]+1]*1.0 #G
        arr_B = arr_res[3,:,:] = arr[2,:,pixels_to_use[0]:pixels_to_use[1]+1]*1.0 #B
        arr_res[0,:,:] = arr_R + arr_G +arr_B #K
        return arr_res
    
    def save_array_as_image(self,arr, filename):
        image = Image.new('RGB',(1360,1024))
        image.frombytes(arr.T.tostring())
        image.save(filename)

        
    def rgb2gray(self,rgb):
        r, g, b = rgb[:,:,0], rgb[:,:,1], rgb[:,:,2]
        gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
        return gray

    def is_new_image(self):
        camera.acquiring = True
        idx = 0
        if self.imageCounter - camera.frame_count > 1000:
            self.imageCounter = 0
        while self.imageCounter >= camera.frame_count:
            sleep(0.1)
            idx += 1
            if idx > 10:
                break
        if idx > 9:
            res = False
        else:
            res = True
        return res

    def get_background_array(self, threshold = 230):
        from numpy.ma import masked_array
        info('Getting background image')
        if self.background_image_flag:
            save(self.logFolder+ 'Archive/background_default_rgb'+str(caget('NIH:TEMP.RBV'))+'.npy', self.background_array)
        while self.is_new_image() != True:
            sleep(0.1)
        self.background_array = self.convert_masked_array(self.get_image(),self.pixels_to_use_1)
        self.background_image_flag = True
        save(self.logFolder + 'background_default_rgb.npy', self.background_array)
        
    def set_background_array(self, filename = 'blank'):
       self.background_image_flag = False
       start_new_thread(self.get_background_array,())
    
    def get_difference_array(self):
        #wait for new image
        self.background_image_flag = True
        res = False
        if self.is_new_image() and self.background_image_flag:
            self.difference_array = []
            self.difference_array.append(self.convert_masked_array(self.get_image(),self.pixels_to_use_1))
            self.difference_array.append(self.convert_masked_array(self.get_image(),self.pixels_to_use_2))
            res = True
        else:
            res = False
        return res
    
    def analyse(self, diff_array):
        analyse_dict = {}
        
        analyse_dict['mean'] =  mean(diff_array[0,:,:])
        analyse_dict['mean_R'] =  mean(diff_array[1,:,:])
        analyse_dict['mean_G'] =  mean(diff_array[2,:,:])
        analyse_dict['mean_B'] =  mean(diff_array[3,:,:])
        analyse_dict['stdev'] = std(diff_array[0,:,:])
        analyse_dict['stdev_R'] = std(diff_array[1,:,:])
        analyse_dict['stdev_G'] = std(diff_array[2,:,:])
        analyse_dict['stdev_B'] = std(diff_array[3,:,:])
        return analyse_dict
            
                
    def analyse_frozen(self):
        if self.background_image_flag:
            
            print('analyse_dict', self.analyse_dict)
            self.analyse_dict['mean_bckg'] = mean(self.background_array[0,:,:])
            if self.difference_array.shape[1] > 5:
                for diff_array in self.difference_array:
                    self.analyse_dict['mean'] =  mean(diff_array[0,:,:])
                    self.analyse_dict['mean_R'] =  mean(diff_array[1,:,:])
                    self.analyse_dict['mean_G'] =  mean(diff_array[2,:,:])
                    self.analyse_dict['mean_B'] =  mean(diff_array[3,:,:])
                    self.analyse_dict['stdev'] = std(diff_array[0,:,:])
                    self.analyse_dict['stdev_R'] = std(diff_array[1,:,:])
                    self.analyse_dict['stdev_G'] = std(diff_array[2,:,:])
                    self.analyse_dict['stdev_B'] = std(diff_array[3,:,:])
                    ratio_val = (self.analyse_dict['mean'] - self.analyse_dict['mean_bckg'])/self.analyse_dict['mean_bckg']
                    debug('ratio %r' % ratio_val)
                    if ratio_val > self.frozen_threshold and caget('NIH:TEMP.RBV') < self.frozen_threshold_temperature:
                        res = True
                    else:
                        res = False
                        
                    # Diagnostic info for later inspection
                    self.analyse_dict['stdev'] = std(self.difference_array[0,:,:])
                    temperature = caget('NIH:TEMP.RBV')
                    txt = '%r ,%r, %r, %r , %r,  %r, %r, %r , %r,  %r, %r\n' %(time(),self.imageCounter,temperature,
                                                         self.analyse_dict['mean'], self.analyse_dict['mean_R'], self.analyse_dict['mean_G'],self.analyse_dict['mean_B'],
                                                         self.analyse_dict['stdev'],self.analyse_dict['stdev_R'],self.analyse_dict['stdev_G'],self.analyse_dict['stdev_B'])
                    debug("analyse_frozen:")
                    file(self.logfile,'a').write(txt)
            else:
                res = False
        else:
            res = False
        return res
        
    def is_frozen(self):
        from time import time
        from datetime import datetime
        self.get_difference_array()
        debug('got difference image. Analyzing....')
        res = self.analyse_frozen()
        if res:
            info('Sample froze! at %r' % datetime.now())
        return res
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
        
    def plot(self):
        plt.subplot(121)
        plt.imshow(self.difference_image)
        plt.colorbar()
        plt.subplot(122)
        plt.imshow(self.background_image)
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
            if self.is_new_image():
                img = Image.fromarray(camera.RGB_array.transpose((-1,0,1)).transpose((-1,0,1)))
                temp = str(caget("NIH:TEMP.RBV"))
                img.save(directory +'/_T_'+temp + '_t_' +str(time())+'.tiff')
                print('saving',directory +'_T_'+temp + '_t_' +str(time())+'.tiff')

    def scan_saved_images(self):
        pass
                
    def test_load_current_1_image(self):
        self.test_current_1 = Image.open(self.logFolder + 'current_rgb.tiff')
        
    def test_save_current_s_image(self):
        self.test_current_s.save(self.logFolder + 'current_test_saved.tiff')
        
    def test_load_current_s_image(self):
        self.test_current_s = Image.open(self.logFolder + 'current_test_saved.tiff')

    def test_load_current_2_image(self):
        self.test_current_2 = Image.open(self.logFolder + 'current_test_2.tiff')


        
from GigE_camera_client import Camera

#camera = Camera("MicroscopeCamera")
image_analyser = Image_analyser()

if __name__ == "__main__":
    import logging; from tempfile import gettempdir
    #/var/folders/y4/cw92kt415kz7wtk13fkjhh2r0000gn/T/samplr_frozen_opt.log'
    logfile = gettempdir()+"/optical_image_analyser_rgb.log"
    ##print(logfile)
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s %(levelname)s: %(message)s",
        #filename=logfile,
    )
    print('Time Start: %r' % str(datetime.now()))
    print('image_analyser.get_difference_array()')
    print('image_analyser.is_frozen()')
    print("image_analyser.plot()")
    print("image_analyser.plot_difference()")
    print('file_path = gettempdir() + "/Images/Optical_images/')
    debug('?')
