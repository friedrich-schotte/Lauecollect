#!/bin/env python
""" This is a python script that will analyse images triggered by the FPGA.
The camera_image_analyzer can get images from the MicroscopeCamera and
convert them to 3D array 1024,1360,4 , where 4 stands for RGB + Total counts.

author: Valentyn Stadnytskyi
dates: March 10,2018 - March 11, 2018

The coordinate system is the following:
x - downstream positive
y - up positive
z - outboard positive
pixel space:
y (v - vertical) - down positive
z (h - horizontal) - inboard positive
results in:
positive direction in horizontal pixel space results in negative z
positive direction in vertical pixel space results in negative y but positive x

"""
import matplotlib.pyplot as plt
from numpy import mean, transpose, std,array,hypot , abs
from time import sleep, time
import PIL
from persistent_property import persistent_property
from datetime import datetime
from optical_image_analyzer import Image_analyzer
from Ensemble import SampleX, SampleY, SampleZ
from persistent_property import persistent_property
import DB

from logging import error,warn, info,debug

laue_image_analyzer = Image_analyzer(
    name = 'LAUE_image_analyzer'
    ) #for LAUE crystalography
laue_image_analyzer.init(camera_name = 'MicroscopeCamera')

class Laue_find_crystals(object):
    def __init__(self):
        self.background_flag = False
        self.save_every_image = False
        laue_image_analyzer.save_every_image = self.save_every_image
        self.global_idx = 0
        self.injection_idx = 0
        self.pixel_size =  float(DB.db("MicroscopeCamera.NominalPixelSize"))# in 0.000526mm
        self.x_scale = 1 #float(DB.db("MicroscopeCamera.x_scale")) #FIXIT: double check xyz grid
        self.y_scale = -1 #float( DB.db("MicroscopeCamera.y_scale")) #FIXIT: double check xyz grid
        self.z_scale = -1 #float( DB.db("MicroscopeCamera.z_scale")) #FIXIT: double check xyz grid

    def get_camera_orientation(self):
        """ returns camera orientation"""
        return 'horizontal'
    camera_orientation = property(get_camera_orientation)
    
    def get_camera_crosshair(self):
        """returns crosshair position of the microscope camera: FIXIT still under development"""
        return (680,512)
    camera_crosshair = property(get_camera_crosshair)
    
    def get_xyz_coordinates_crosshair(self):
        return (SampleX.value,SampleY.value,SampleZ.value)
    xyz_coordinates_crosshair = property(get_xyz_coordinates_crosshair)

    def abs_pixel_to_abs_xyz(self,pixel = (680,512)):
        """pixel = (h,v) absolute position of crosshair in pixel space"""
        curr_h = pixel[0]
        curr_v = pixel[1]
        (crosshair_h, crosshair_v) = self.camera_crosshair
        (dx,dy,dz) = self.dpixel_to_dxyz()
        z = (curr_h-crosshair_h)*dz
        x = (curr_v-crosshair_v)*dx
        y = (curr_v-crosshair_v)*dy
        return (x,y,z)

    def dpixel_to_dxyz(self):
        from numpy import cos, sin, pi
        """dpixel = (h,v)"""
        dh = 1.0 #change vertical
        dv = 1.0 #change horizontal
        dz = self.z_scale*dh*self.pixel_size
        dx = self.x_scale*dv*self.pixel_size*sin(pi/6.0)
        dy = self.y_scale*dv*self.pixel_size*cos(pi/6.0)
        return (dx,dy,dz)

    def get_image(self):
        image = laue_image_analyzer.get_image()
        return image
        
    def analyse_diff_image(self,curr = None,bckg = None):
        from random import random
        """ Analyse image and create the list of coordinates"""
        self.dic = {}
        self.injection_idx +=1
        """This will make a fake dictionary with random number of crystals"""
        number = 7
        for i in range(number):
            self.dic[str(i)] = (round(random(),3)-round(random(),3),
                                round(random(),3)-round(random(),3),
                                round(0,3)-round(0,3))
            self.global_idx += 1
            
        return self.dic

    
    def run_once(self):
        flag = self.get_difference_image()
        if flag:
            image = laue_image_analyzer.difference_array
            self.analyse_diff_image()
            self.save_in_file()
            res = True
        else:
            res = False
        return res
    
    class TSP_sorting(object):
        def __init__(self,dic):
            self.order = []
            self.sum = []
            self.dic = dic
            
        def run_first_time(self):
            dist = []
            self.order.append('start')
            for key in self.dic.keys():
                if key != 'start' and key != 'end':
                    self.order.append(key)
            self.calculate_distance_to_origin(self.order)
            
            self.sum = self.calculate_distance(self.order)
            
        def run_once(self):
            from random import shuffle
            temp_order = self.order[1:-1]   
            shuffle(temp_order)
            new_order = []
            new_order.append(self.order[0])
            for i in temp_order:
                new_order.append(i)
            new_order.append(self.order[-1])
            new_sum = self.calculate_distance(new_order)
            if new_sum < self.sum:
                self.sum = new_sum
                self.order = new_order
        
        def run(self, timeout = 1):
            from random import shuffle
            if len(self.order) == 0:
                self.run_first_time()
            t = time()
            while  time() - t < timeout:
                self.run_once()
        
        def pre_order(self):
            pass
        
        def calculate_distance(self,order):
            s = 0
            for i in range(len(order)-1):
                (x1,y1,z1) = self.dic[order[i]]
                (x2,y2,z2) = self.dic[order[i+1]]
                s = s + ((x2-x1)**2 + (y2-y1)**2 + (z2-z1)**2)**0.5
            return s
        
        def calculate_distance_to_origin(self):
            dist = []
            for key in self.dic.keys():
                (x , y , z) = self.dic[key]
                dist[1,i] = x**2+y**2+z**2
                dist[0,i] = key
                
            return dist
        
        def plot(self):
            from numpy import asarray
            lst = []
            for key in self.order:
               lst.append(self.dic[key])
            arr = asarray(lst)
            print arr
            plt.plot(arr[:,0],arr[:,1],'-o')
            plt.show()
            
    def save_in_file(self):
        import os       
        folder = "/Ensemble/"
        filename = 'PVT_LAUE_Optical_parameters'
        f = open(os.getcwd()+ folder + filename + '.abi','w')
        f.write('DECLARATIONS\n')
        f.write('GLOBAL N_Mode AS INTEGER = '+ str(0)+ '\n')
        f.write('GLOBAL N_period AS INTEGER = ' +str(108)+ '\n')
        f.write('GLOBAL N_repeat AS INTEGER = '+ str(36)+ '\n')
        f.write('GLOBAL N_xtal AS INTEGER = '+str(len(self.dic))+ '\n')
        f.write('GLOBAL XYZ() AS DOUBLE = {'+ '\n')
        for key in self.dic.keys():
            if key != 'msg':
               x, y, z = self.dic[key]
               f.write('{'+ str(x) + ','
                       + str(y) + ',' +
                       str(z) + '},'+ '\n')
        f.write('}'+ '\n')
        f.write('END DECLARATIONS'+ '\n')
        f.close()

    def plot_edges(self):
        plt.imshow(laue_image_analyzer.difference_array[:,:,0])
        plt.colorbar()
        plt.show(self)

    def log_start(self, beamtime_name = 'anfinrud_1807', sample_name = 'TEST'):
        import os
        from time import strftime, localtime, time
        from datetime import datetime
        self.logtime = time()
        self.beamtime_name = beamtime_name
        self.sample_name = sample_name
        self.log_folder = '//net//mx340hs.cars.aps.anl.gov/data/'+beamtime_name+'/Data/Laue/' + sample_name+'/'
        self.filename = self.log_folder + 'experiment_log_file.log'
        if os.path.isdir(self.log_folder):
            info('folder already exist')
        else:
            info("folder doesn't exist. Creating one...")
            os.mkdir(self.log_folder)
     
        f = open(self.filename ,'w')
        #timeRecord = str(datetime.now())
        timeRecord = self.logtime
        f.write('####This experiment started at: %r and other information %r \r\n'
                %(timeRecord,'Other Garbage'))
        f.write('time stamp,  sample name, injection index, crystal, pos \r\n')
        f.close()

    def log_append_crystal(self,crystal_dict = {}):
        """
        - logs events into a file if self.loggingState == True
        - always appends current value to the logVariable_buffers['#key#'] where #key#
            can be found in self.logVariables dictionary
        """
        from os import makedirs, path
        from time import strftime, localtime, time
        from datetime import datetime
        for key in crystal_dict.keys():
            pos = crystal_dict[key]
            time_stamp = time()
            txt = '%r , %r, %r, %r, %r\n' %(time_stamp,self.sample_name,self.injection_idx,key,pos)
            file(self.filename,'a').write(txt)

    def log_save_image(self):
        pass


        
        

        


laue_find_crystals = Laue_find_crystals()
laue_find_crystals.sample_name = 'TEST'
        
if __name__ == "__main__":
    import logging
    from tempfile import gettempdir
    logging.basicConfig(#filename=gettempdir()+'/Laue_find_crystals.log',
                        level=logging.DEBUG, format="%(asctime)s %(levelname)s: %(message)s")
    self = laue_find_crystals # for testing

        
    def run_find_xtals( N = 1):
        from numpy import asarray
        dic = self.analyse_diff_image();
        sor = self.TSP_sorting(dic);
        sor.run_first_time()
        lst = []
        for key in sor.order:
           lst.append(self.dic[key])
        arr = asarray(lst)
        #plt.subplot(121)
        #plt.plot(arr[:,0],arr[:,1],'-o')

        t1 = time();
        sor.run(t);
        t2 = time();
        print t2-t1;
         
        lst = []
        for key in sor.order:
           lst.append(self.dic[key])
        arr = asarray(lst)
        #plt.subplot(122)
        #plt.plot(arr[:,0],arr[:,1],'-o')
        #plt.show()

        print lst
        
    print('....LAUE find crystals code.....')

