"""Record photos using a Prosilica GigE camera
Author: Friedrich Schotte, Valentyn Stadnytskyi
Date created: 2017-04-012
Date last modified: 2019-02-22
"""
__version__ = "2.4" # temperature
from GigE_camera_client import Camera
from sleep import sleep
from time import time
from os.path import basename

template_APS = "//mx340hs/data/anfinrud_1810/Test/Laue/opt_images/CypA_round2/%s"\
               "%r_%r_%s_%r_%r_%r.tiff"

template_APS_temperature = "//mx340hs/data/anfinrud_1810/Test/Laue/opt_images/freezing_T_ramp_NCBD_TAD/%s"\
               "%r_%r_%s_%r.pickle"

#template_APS = "C:/CypA/%r"\
 #              "%r_%r_%r_%r_%r_%r.tiff"


template_APS_MAC = "//volumes/data/anfinrud_1810/Archive/Laue_pictures/%s"\
               "%r_%r_%r.tiff"


template_NIH= "//femto/C/All Projects/Crystallization/2019/TRamp-red-laser/"\
    "%s_%00d_%r_%r_%r.tiff"

template = template_NIH
delay = 0.0025 #in seconds
i = 0

from EPICS_motor import motor
from instrumentation import temperature
from sample_frozen_optical import sample_frozen_optical as sfo
motorX = motor("NIH:SAMPLEX")
motorY = motor("NIH:SAMPLEY")
motorZ = motor("NIH:SAMPLEZ")

#camera = Camera("Microscope")
camera1 = Camera('MicroscopeCamera') 
camera1.acquiring = True
#camera = Camera("MicroscopeCamera")
def record_T_once(l):
    from numpy import zeros,flip
    from SAXS_WAXS_control import SAXS_WAXS_control
    ins = 0#str(SAXS_WAXS_control.inserted)
    filename = template % ("Microscope/",time(),l,int(ins),temperature.value)
    print("%s" % basename(filename))
    img = camera1.RGB_array
    gray = sum(img,2)
    arr = zeros((4,1024,1360))
    for i in range(3):
        for j in range(1024):
            for k in range(1360):
                arr[i,j,k] = img[i,k,j]
    i = 3
    for j in range(1024):
        for k in range(1360):
            arr[i,j,k] = gray[k,j]
    arr = flip(arr,1)
    vector = sfo.get_vector(arr)
    sfo.save_obj(vector,filename)
def record_temperature():
    from sample_frozen_optical2 import sample_frozen_optical as sfo
    from numpy import zeros

    try:
        l=0
        while True:
            record_T_once(l)
            l += 1
            sleep(0.3)
    except KeyboardInterrupt: pass
 
def record(camera_name = 'MicroscopeCamera'):
    camera1 = Camera('MicroscopeCamera') 
    camera1.acquiring = True
    camera2 = Camera('WideFieldCamera')
    #camera2.ip_address = '164.54.161.34:2001'
    camera2.acquiring = True
    try:
        i=0
        while True:
            ins = 0
            filename = template % ("Microscope/",time(),i,int(ins),temperature.value)
            print("%s" % basename(filename))
            camera1.save_image(filename)
            filename = template % ("WideField/",time(),i,int(ins),temperature.value)
            print("%s" % basename(filename))
            camera2.save_image(filename)
            i += 1
            sleep(delay)
    except KeyboardInterrupt: pass

def record1(camera_name = 'MicroscopeCamera'):
    template_NIH= "//femto/C/All Projects/Crystallization/2019/Lysozyme3/"\
    "%s_%r.tiff"
    camera1 = Camera('LabMicroscope') 
    camera1.acquiring = True
    i=0
    while True:
        filename = template % (time(),i)
        print("%s" % basename(filename))
        camera1.save_image(filename)
        i+=1
        
def server_record(N = 10,camera_name = 'MicroscopeCamera'):
    camera = Camera(camera_name) 
    camera.acquiring = True
    # Offload the image saving to the camera server for performance
    filenames = [template % i for i in range(N)]
    frame_counts = [camera.frame_count+1+i for i in range(len(filenames))]
    camera.send("camera.acquire_sequence(%r,%r)" %(frame_counts,filenames))

print("server_record(20)")
print("record(camera_name = 'WideFieldCamera')")
