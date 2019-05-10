"""
Record multiple images at different Laue cell positions.
- depth scans


Author: Valentyn Stadnytskyi
Date created: 2018-10-25
Date last modified: 2018-03-28
"""
__version__ = "0.0.2" # Friedrich Schotte, WideFieldCamera with uppercase F
from GigE_camera_client import Camera
from Ensemble import ensemble
from EPICS_motor import EPICS_motor
from sleep import sleep
from time import time
from os.path import basename
from numpy import sin,cos,pi,asarray
import os
import PIL
from thread import start_new_thread
from matplotlib import pyplot as plt

template_APS = "//mx340hs/data/anfinrud_1810/Archive/Laue_pictures/"\
               "%r_%r_%r.tiff"

template_APS_MAC_folder = "//volumes/data/anfinrud_1810/Archive/Laue_pictures/"
template_APS_MAC = template_APS_MAC_folder+ "%r_%r_%r.tiff"


template_NIH= "//femto/C/All Projects/Crystallization/2018/test/"\
    "%r_%r_%00d.tiff"
x_scale = 1 #float(DB.db("MicroscopeCamera.x_scale")) #FIXIT: double check xyz grid
y_scale = -1 #float( DB.db("MicroscopeCamera.y_scale")) #FIXIT: double check xyz grid
z_scale = -1 #float( DB.db("MicroscopeCamera.z_scale")) #FIXIT: double check xyz grid

from EPICS_motor import motor
motorX = motor("NIH:SAMPLEX")
motorY = motor("NIH:SAMPLEY")
motorZ = motor("NIH:SAMPLEZ")

def saved_position():
    
    motorX.value, motorY.value, motorZ.value = (0.21, 0.05, 0.8)

class MotorD(object):
    def __init__(self):
        pass
    def get_value(self):
        return round((motorX.value-0.261)*sin(pi/3.0),4)
    def set_value(self,value):
        motorX.value = value*cos(-pi/12.0) + 0.261
        motorY.value = value*sin(-pi/12.0) -0.039
    value = property(get_value,set_value)
    
class MotorH(object):
    def __init__(self):
        pass
    def get_value(self):
        return motorZ.value
    def set_value(self, value):
        motorZ.value = value
    value = property(get_value,set_value)
    
class MotorV(object):
    def __init__(self):
        pass
    def get_value(self):
        return round((motorX.value-0.261)*cos(pi/3.0),4)
    def set_value(self,value):
        motorX.value = -value*cos(pi/6.0) + 0.261
        motorY.value = value*sin(pi/6.0) -0.039
    value = property(get_value,set_value)

motorD = MotorD()
motorV = MotorV()
motorH = MotorH()
def get_XYZ_position():
    return (motorX.value,motorY.value,motorZ.value)

def get_DVH_position():
    from numpy import sin,cos,pi
    V = round(motorY.value*sin(pi/6.0),3)
    H = motorZ.value
    D = round(motorY.value*cos(pi/6.0),3)
    return (D,V,H)

    
    
    
template = template_APS_MAC
delay = 0.0025 #in seconds
i = 0

camere_Microscope = Camera("MicroscopeCamera")
camere_Microscope.acquiring = True
camera_WideField = Camera('WideFieldCamera')
camera_WideField.acquiring = True
g_res = []
def analyze(g_res):
    from PIL import Image
    import numpy as np
    import traceback
    from time import time
    list_of_files = os.listdir(template_APS_MAC_folder)
    res = []
    t1 = time()
    for i in range(len(list_of_files)):
        filename = template_APS_MAC_folder+list_of_files[i]
        try:
            im = Image.open(filename).convert('L') # to grayscale
            array = np.asarray(im, dtype=np.int32)
            gy, gx = np.gradient(array)
            max_gy,min_gy= np.max(gy),np.min(gy)
            max_gx,min_gx = np.max(gx),np.min(gx)
            gnorm = np.sqrt(gx**2 + gy**2)
            sharpness = np.average(gnorm)
            g_res.append([i,max_gy,min_gy,max_gx,min_gx,sharpness])
            #os.rename(template_APS_MAC_folder+list_of_files[i], template_APS_MAC_folder+"processed/"+list_of_files[i])
            
        except:
            print(traceback.format_exc())
            print('filename = %r' % filename)
    print('The Analysis thread has finished')

def plot(N = 0):
    from PIL import Image
    import numpy as np
    list_of_files = os.listdir(template_APS_MAC_folder)
    filename = template_APS_MAC_folder+list_of_files[N]
    im = Image.open(filename).convert('L') # to grayscale
    array = np.asarray(im, dtype=np.int32)

    gy, gx = np.gradient(array)
    gnorm = np.sqrt(gx**2 + gy**2)
    sharpness = np.average(gnorm)
    from matplotlib import pyplot as plt
    plt.subplot(131)
    plt.imshow(array)
    plt.colorbar()
    plt.title('image %r' % N)
    plt.subplot(132)
    plt.imshow(gx)
    plt.colorbar()
    plt.title('gradient x')
    plt.subplot(133)
    plt.imshow(gy)
    plt.colorbar()
    plt.title('gradient y')
    plt.show()
    
def delete_file(N):
    list_of_files = os.listdir(template_APS_MAC_folder)
    filename = template_APS_MAC_folder+list_of_files[N]
    os.remove(filename)
    
def record():
    try:
        i=0
        while True:
            filename = template % (time(),i,"M")
            print("%s" % basename(filename))
            camere_Microscope.save_image(filename)
            filename = template % (time(),i,"W")
            print("%s" % basename(filename))
            camera_WideField.save_image(filename)
            i += 1
            sleep(delay)
    except KeyboardInterrupt: pass

def motor_test(dvalue = 0.01):
    from time import time
    value = motorZ.value
    motorZ.value = value + dvalue
    t1 = time()
    while motorZ.value != round(value + dvalue,3):
        sleep(0.01)
    t2 = time()
    motorZ.value = value
    while motorZ.value != value:
        sleep(0.01)
    t3 = time()
    print(t2-t1,t3-t2)


def server_record(N = 10,camera_name = 'MicroscopeCamera'):
    camera = Camera(camera_name)
    camera.acquiring = True
    # Offload the image saving to the camera server for performance
    filenames = [template % i for i in range(N)]
    frame_counts = [camera.frame_count+1+i for i in range(len(filenames))]
    camera.send("camera.acquire_sequence(%r,%r)" %(frame_counts,filenames))

print("server_record(20)")
print("record(camera_name = 'WideFieldCamera')")
print("start_new_thread(analyze,(g_res,))")

