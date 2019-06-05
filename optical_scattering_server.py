"""
Optical Freeze Detector Agent with on-axis laser

Authors: Valentyn Stadnytskyi
Date created: 26 Feb 2018 - original optical freeze detection agent
Date last modified: March 2 2019

Utilizes center 50x50 pixels to measure mean value within

The server connects to Microscope Camera and analyses every incoming image in the region of analysis.
The reported values are MEAN and STDEV. Based on MEAN and Threshold_mean the server can issue a command to
lunch an intervention.
"""
__version__ = "1.0" # write a comment


from CAServer import casput,casdel, casget
from CA import caget
from datetime import datetime
from thread import start_new_thread
from pdb import pm
import os
from time import sleep,time
from persistent_property import persistent_property
from numpy import nan
from logging import debug,info,warn,error
import traceback




class Optical_Scattering_Server(object):
    orientation = persistent_property('orientation', 'horizontal')
    on_axis_square_size =  persistent_property('on_axis_square_size', (25,25))
    warning_threshold = persistent_property('warning_threshold', 100.0)
    region_size_x =persistent_property('region_size_x', 10)
    region_offset_x =persistent_property('region_offset_x', 0)
    region_size_y =persistent_property('region_size_y', 10)
    region_offset_y =persistent_property('region_offset_y', 20)

    def __init__(self):
        self.name = 'sample_frozen_optical'
        self.prefix = self.prefix = 'NIH:OPTICAL_SCATTERING'
        self.running = False
        self.warning = False
        self.orient_dic = {}
        self.orient_dic['vertical'] ={'up': [(532,0),(732,1024)],
                                     'down':[(1040,0),(1240,1024)]}
        self.orient_dic['horizontal'] = {'up':[(697-75,0),(825-75,1360)],
                                        'down':[(865+20,0),(993+20,1360)]}

        self.orient_dic['horizontal2'] = {'up':[(0,0),(120,1360)],
                                          'middle':[(512,0),(632,1360)],
                                        'down':[(903,0),(1023,1360)]}

        #On-axis uses only middle part and disregards up and down.


        self.x_middle = 512 + self.region_offset_x
        self.y_middle = 680 + self.region_offset_y

        dx = self.region_size_x
        dy = self.region_size_y

        self.orient_dic['on-axis-h'] = {'up':[(0,0),(0,0)],
                                          'middle':[(self.x_middle-dx,self.y_middle-dy),(self.x_middle+dx,self.y_middle+dy)],
                                        'down':[(0,0),(0,0)]}

        self.orient_dic['on-axis-v'] = {'up':[(0,0),(0,0)],
                                          'middle':[(680-dy,512-dx),(680+dy,512+dx)],
                                        'down':[(0,0),(0,0)]}


        self.circular_buffer = []
        self.scattering = nan

    def init(self):
        """
        define parameters for current operation
        initializes image analyzer
        """
        from optical_image_analyzer import image_analyzer
        image_analyzer.init()


        from CAServer import casput,casmonitor
        from CA import caput,camonitor
        from numpy import nan
        info('initializing the %s server' %self.prefix)
        casput(self.prefix+".RBV",nan)
        casput(self.prefix+".VAL",nan)

        casput(self.prefix+".MEAN_TOP",nan)
        casput(self.prefix+".MEAN_BOTTOM",nan)
        casput(self.prefix+".MEAN_MIDDLE",nan)

        casput(self.prefix+".MEAN",nan)
        casput(self.prefix+".STDEV",nan)


        casput(self.prefix+'.RUNNING', self.running)

        #changable control parameters
        casput(self.prefix+'.region_offset_x', self.region_offset_x)
        casput(self.prefix+'.region_size_x', self.region_size_x)
        casput(self.prefix+'.region_offset_y', self.region_offset_y)
        casput(self.prefix+'.region_size_y', self.region_size_y)
        casput(self.prefix+'.warning', self.warning)
        casput(self.prefix+'.warning_threshold', self.warning_threshold)



        casput(self.prefix+".KILL",value = 'write password to kill the process')

        #PV with a list of all process variable registered at the current Channel Access Server
        casput(self.prefix+".LIST_ALL_PVS",value = self.get_pv_list())

        # Monitor client-writable PVs.
        casmonitor(self.prefix+".KILL",callback=self.monitor)

        casmonitor(self.prefix+".region_size_x",callback=self.monitor)
        casmonitor(self.prefix+".region_offset_x",callback=self.monitor)
        casmonitor(self.prefix+".region_size_y",callback=self.monitor)
        casmonitor(self.prefix+".region_offset_y",callback=self.monitor)
        casmonitor(self.prefix+".warning_threshold",callback=self.monitor)


    def monitor(self,PV_name,value,char_value):
        """Process PV change requests"""
        from CAServer import casput
        from CA import caput
        info("monitor: %s = %r" % (PV_name,value))
        if PV_name == self.prefix + ".KILL":
            if value == 'shutdown': #the secret word to shutdown the process is 'shutdown'
                self.shutdown()
        if PV_name == self.prefix + ".region_size_x":
            self.region_size_x = int(value)
        if PV_name == self.prefix + ".region_size_y":
            self.region_size_y = int(value)
        if PV_name == self.prefix + ".region_offset_x":
            self.region_offset_x = int(value)
        if PV_name == self.prefix + ".region_offset_y":
            self.region_offset_y = int(value)
        if PV_name == self.prefix + ".warning_threshold":
            try:
                temp = float(value)
                flag = True
            except:
                error(traceback.format_exc())
                flag = False
            if flag: self.warning_threshold = float(value)


    def shutdown(self):
        from CAServer import casdel
        info('SHUTDOWN command received. orderly exit initiated for %s' %self.prefix)
        self.running = False
        self.cleanup()
        del self

    def get_pv_list(self):
        from CAServer import PVs
        lst = list(PVs.keys())
        return lst



    def start(self):
        """run in background"""
        info('Freeze detector has started')
        from thread import start_new_thread
        start_new_thread(self.run,())

    def stop(self):
        self.running = False

    def close(self):
        self.running = False
        self.cleanup()

    def run(self):
        from time import sleep,time
        self.init()
        self.running = True
        while self.running:
            self.running_timestamp = time()
            try:
                self.run_once()
            except:
                error(traceback.format_exc())
                warn('Microscope camera is not working')
        self.running = False
        self.scattering = nan

    def run_once(self):
        from optical_image_analyzer import image_analyzer
        from CAServer import casput, casget
        from numpy import rot90

        img = image_analyzer.get_image()
        debug('image received: image counter %r, image dimensions %r' %(image_analyzer.imageCounter, img.shape))
        if self.orientation == 'horizontal2' or self.orientation == 'horizontal' or self.orientation == 'on-axis-h':
            img = rot90(img,3,axes=(1,2))


        res_dic = self.is_frozen(img)
        debug('res_dic = %r' %res_dic)
        is_frozen_flag = res_dic['flag']
        casput(self.prefix+".MEAN_TOP",round(res_dic['mean_top'],2))
        casput(self.prefix+".MEAN_BOTTOM",round(res_dic['mean_bottom'],2))
        casput(self.prefix+".MEAN_MIDDLE",round(res_dic['mean_middle'],2))
        casput(self.prefix+".MEAN",round(res_dic['mean_value'],2))
        casput(self.prefix+".RBV",round(res_dic['mean_value'],2))
        casput(self.prefix+".warning",res_dic['mean_value'] >= self.warning_threshold)
        casput(self.prefix+".STDEV",round(res_dic['stdev'],2))
        self.intervention_enabled = casget(self.prefix+'.INTERVENTION_ENABLED')
        casput(self.prefix+".VAL",is_frozen_flag)
        if is_frozen_flag and temperature.value < self.frozen_threshold_temperature:
            print('freezing detected')
            """Intervention"""
            if self.intervention_enabled:
                self.retract_intervention()
            else:
                print('Intervention was disabled')


    def is_frozen(self,img):
        """
        determines if the images is frozen or not
        """
        from optical_image_analyzer import image_analyzer
        from numpy import subtract, mean, std, rot90, array
        from freeze_intervention import freeze_intervention
        from temperature import temperature
        from PIL import Image

        dx = int(self.region_size_x)
        dy = int(self.region_size_y)

        self.orient_dic['on-axis-h'] = {'up':[(0,0),(0,0)],
                                          'middle':[(512-dx,680-dy),(512+dx,680+dy)],
                                        'down':[(0,0),(0,0)]}

        self.orient_dic['on-axis-v'] = {'up':[(0,0),(0,0)],
                                          'middle':[(680-dy,512-dx),(680+dy,512+dx)],
                                        'down':[(0,0),(0,0)]}

        section_up = image_analyzer.masked_section(img,anchors = self.orient_dic[self.orientation]['up'])
        section_middle = image_analyzer.masked_section(img,anchors = self.orient_dic[self.orientation]['middle'])
        section_down = image_analyzer.masked_section(img,anchors = self.orient_dic[self.orientation]['down'])
        flag = False

        dict0 = self.analyse(section_up)
        dict1 = self.analyse(section_down)
        dict2 = self.analyse(section_middle)
##        dict0 = {}
##        dict1 = {}
##        dict2 = {}
##        dict0['mean'] = 0
##        dict1['mean'] = 0
##        dict2['mean'] = 0
        mean_top = dict0['mean']
        mean_bottom = dict1['mean']
        mean_middle = dict2['mean']
        if self.orientation == 'on-axis-h' or self.orientation == 'on-axis-v' :
            mean_value = dict2['mean']
            stdev = dict2['stdev']
        else:
            mean_value = dict2['mean']-(dict0['mean']/2.)-(dict1['mean']/2.)
            stdev = (dict2['stdev']**2-(dict0['stdev']/2)**2-(dict1['stdev']/2)**2)**0.5
        self.scattering = round(mean_value,3)

        res_dic = {}
        res_dic['flag'] = flag
        res_dic['mean_top']=mean_top
        res_dic['mean_bottom']=mean_bottom
        res_dic['mean_middle']=mean_middle
        res_dic['mean_value']=mean_value
        res_dic['stdev'] = stdev

        return res_dic

    def analyse(self,array):
        from numpy import mean, std
        dic = {}
        dic['mean'] =  mean(array[0,:,:]*1.0+array[1,:,:]*1.0+array[2,:,:]*1.0)
        dic['mean_R'] =  mean(array[0,:,:])
        dic['mean_G'] =  mean(array[1,:,:])
        dic['mean_B'] =  mean(array[2,:,:])
        dic['stdev'] = std(array[0,:,:]*1.0+array[1,:,:]*1.0+array[2,:,:]*1.0)
        dic['stdev_R'] = std(array[0,:,:])
        dic['stdev_G'] = std(array[1,:,:])
        dic['stdev_B'] = std(array[2,:,:])
        return dic


    def cleanup(self):
        """orderly cleanup of all channel access server process variables."""
        from CAServer import casdel
        lst = self.get_pv_list()
        for item in lst:
            info('delete PV: %s' % item )
            casdel(item)



    ###Libraries for testing and data processing

    def test_folder(self):
        folder = '//volumes/data/anfinrud_1810/Test/Laue/opt_images/freezing/Microscope/'
        return folder

    def get_filenames(self,folder):
        import os
        from numpy import zeros,asarray
        lst_temp = os.listdir(folder)
        lst = []
        for i in lst_temp:
            if '.tiff' in i:
                lst.append(i.split('_'))
        sorted_lst = sorted(lst,key=lambda x: (x[0],x[1]))
        lst_s = []
        for i in sorted_lst:
            lst_s.append([i[0],folder + '_'.join(i)])
        return lst_s

    def get_image_from_file(self,filename):
        from PIL import Image
        from numpy import rot90, array, zeros,flipud, mean, flip, sum
        img = array(Image.open(filename))
        gray = sum(img,2)
        arr = zeros((4,1024,1360))
        for i in range(3):
            for j in range(1024):
                for k in range(1360):
                    arr[i,j,k] = img[j,k,i]
        i = 3
        for j in range(1024):
            for k in range(1360):
                arr[i,j,k] = gray[j,k]
        arr = flip(arr,1)
        return arr

    def get_vector(self,img):
        from numpy import mean, sum
        dic = {}
        dic['mean_total'] = mean(img[3,:,:],axis = 1)
        dic['sum_total'] = sum(img[3,:,:],axis = 1)
        dic['mean_R'] = mean(img[0,:,:],axis = 1)
        dic['sum_R'] = sum(img[0,:,:],axis = 1)
        dic['mean_G'] = mean(img[1,:,:],axis = 1)
        dic['sum_G'] = sum(img[1,:,:],axis = 1)
        dic['mean_B'] = mean(img[2,:,:],axis = 1)
        dic['sum_B'] = sum(img[2,:,:],axis = 1)

        return dic

    def run_test(self):
        from time import time
        folder = self.test_folder()
        filenames = self.get_filenames(folder)
        res_lst = []
        t1 = time()
        i = 0
        for name in filenames:
            img = self.get_image_from_file(name[1])
            result = self.get_vector(img)
            self.save_obj(result,name[1].split('.tiff')[0]+'.pickle')
            res_lst.append(self.get_vector(img))
            print(time()-t1,len(filenames)-i)
            i+=1

    def save_obj(self,obj, name ):
        import pickle
        with open(name, 'wb') as f:
            pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

    def load_obj(self,name):
        import pickle
        with open(name, 'rb') as f:
            return pickle.load(f)

    def get_all_pickle(self,folder):
        lst_temp = os.listdir(folder)
        lst = []
        for item in lst_temp:
            i = item.split('.pickle')[0]
            lst.append(i.split('_'))
        sorted_lst = sorted(lst,key=lambda x: (x[0],x[1],x[2],x[3]))
        lst_s = []
        for i in sorted_lst:
            lst_s.append([i[0],folder + '_'.join(i),i[2],i[3]])
        return lst_s

    def test2(self,fr,to, folder = ''):
        from matplotlib import pyplot as plt
        from time import time
        i = 0
        if folder =='':
            lst = self.get_all_pickle(self.test_folder())
        else:
            lst = self.get_all_pickle(folder)
        for item in lst[fr:to]:
            item[1] = item[1] + '.pickle'
            arr = self.load_obj(item[1])['mean_total']
            plt.plot(arr)

    def plot_mean_values(self,folder):
        from matplotlib import pyplot as plt
        from time import time
        from numpy import std
        from numpy import asarray
        i = 0
        arr = []
        arrT = []
        if folder =='':
            lst = self.get_all_pickle(self.test_folder())
        else:
            lst = self.get_all_pickle(folder)
        for item in lst:
            item[1] = item[1] + '.pickle'
            arr.append(self.load_obj(item[1])['frozen']['mean_value'])
            arrT.append(float(item[3])*0.1)
        arr = asarray(arr)
        arrT = asarray(arrT)
        plt.plot(arr)
        plt.plot(arrT)
        plt.show()

    def process_data(self,folder):
        from matplotlib import pyplot as plt
        from time import time
        from numpy import std
        from numpy import asarray
        result = []
        if folder =='':
            lst = self.get_all_pickle(self.test_folder())
        else:
            lst = self.get_all_pickle(folder)
        for item in lst:
            dic = {}
            item[1] = item[1] + '.pickle'
            dic['temperature'] = float(item[3])
            dic['inserted'] = item[2]
            dic['frozen'] = self.load_obj(item[1])['frozen']['flag']
            dic['frozen_data'] = self.load_obj(item[1])['frozen']
            dic['data'] = self.load_obj(item[1])
            result.append(dic)
        return result

    def plot_all_T(self,T = [0,1],folder = ''):
        from matplotlib import pyplot as plt
        i =0
        for item in T:
            num = len(T)*100 +10 +i+1
            plt.subplot(num)
            self.plot_fixed_temperature(0,2631,folder,T[i])
            plt.ylim(30,150)
            i+=1
        plt.show()

    def plot_N_image_slice(self,N,folder):
        from matplotlib import pyplot as plt
        from time import time
        from numpy import std
        i = 0
        temp_lst
        if folder =='':
            lst = self.get_all_pickle(self.test_folder())
        else:
            lst = self.get_all_pickle(folder)
        for item in lst[fr:to]:
            item[1] = item[1] + '.pickle'
        temperature = item[3]
        arr = self.load_obj(item[1])['mean_total']
        arrG = self.load_obj(item[1])['mean_G']
        arrR = self.load_obj(item[1])['mean_R']
        arrB = self.load_obj(item[1])['mean_B']
        plt.plot(arr, label = 'total', color= 'k')
        plt.plot(arrR, label = 'Red', color = 'r')
        plt.plot(arrG, label = 'Green' , color = 'g')
        plt.plot(arrB, label = 'Blue', color = 'b')
        plt.title('Image = %r @ T = %r C' %(N,temperature))

    def plot_fixed_temperature(self,fr,to, folder = '',temperature = 0):
        from matplotlib import pyplot as plt
        from time import time
        from numpy import std
        i = 0
        if folder =='':
            lst = self.get_all_pickle(self.test_folder())
        else:
            lst = self.get_all_pickle(folder)
        for item in lst[fr:to]:
            item[1] = item[1] + '.pickle'
            arr = self.load_obj(item[1])['mean_total']
            if temperature == 999 and std(arr) != 0:
                plt.plot(arr, label = str(self.load_obj(item[1])['frozen']['mean_value']))
            elif abs(float(item[3]) - temperature) < 0.2 and std(arr) != 0:
                plt.plot(arr, label = str(self.load_obj(item[1])['frozen']['mean_value']))
                i +=1
        plt.title('N of images = %r @ T = %r C' %(i,temperature))


    def test3(self):
        from matplotlib import pyplot as plt
        from time import time
        lst = self.get_all_pickle(self.test_folder())
        lsttt = []
        for item in lst:
            lsttt.append(self.load_obj(item[1])['frozen']['mean_value'])
            #plt.plot(lsttt)

        return lsttt


optical_scattering_server = Optical_Scattering_Server()


if __name__ == "__main__":
    import autoreload
    import logging
    from tempfile import gettempdir
    import matplotlib.pyplot as plt

    logging.basicConfig(level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        filename=gettempdir()+"/optical_scattering.log",
    )
    self = optical_scattering_server # for testing
    print('self.start()')
    print('self.stop()')
    print('self.close()')
    print('self.is_running = True')
    print('self.is_running = False')
