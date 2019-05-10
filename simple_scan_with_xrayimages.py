from id14 import LaserX,LaserY,LaserZ
from rayonix_detector_continuous import rayonix_detector

import os
from shutil import copyfile
from time import time,sleep
destination_folder = '/Volumes/data/anfinrud_1810/Data/WAXS/Scan/'
print('LaserX %r ,LaserY %r ,LaserZ %r' %(LaserX.value,LaserY.value,LaserZ.value))
os.path.exists(destination_folder)

def copyfile_image(value,motor = 'X'):
    image_file = rayonix_detector.current_temp_filename
    copyfile(image_file, destination_folder+str(time())+'_'+motor+'.'+str(value) +'.mccd')

def current_LaserX():
    return  LaserX.value

def current_LaserZ():
    return  LaserZ.value

def get_scan_list(width,step,motor = 'X'):
    from numpy import arange
    if motor == 'X':
        x = arange(current_LaserX()-width,current_LaserX()+width,step)
    elif motor == 'Z':
        x = arange(current_LaserZ()-width,current_LaserZ()+width,step)
    return x

def move_to(value,motor = 'X'):
    from time import sleep
    if motor == 'X':
        LaserX.value = value
        sleep(0.5)
        while abs(LaserX.value - value) > 0.004:
            sleep(0.02)
    elif motor == 'Z':
        LaserZ.value = value
        sleep(0.5)
        while abs(LaserZ.value - value) > 0.004:
            sleep(0.02)
    sleep(0.05)
    
def scan(width,step,motor = 'X'):
    if motor == 'X':
        start_pos = LaserX.value
    elif motor == 'Z':
        start_pos = LaserZ.value
    try:
        for pos in get_scan_list(width,step,motor = motor):
            move_to(pos,motor = motor)
            sleep(2.1)
            print('current positions %r,%r' %(current_LaserX(),current_LaserZ()))
            if motor == 'Y':
                copyfile_image(value = LaserY.value, motor = 'Y')
            if motor == 'Z':
                copyfile_image(value = LaserZ.value, motor = 'Z')
    except KeyboardInterrupt:
        print("Returning motors to the starting positions.")
        if motor == 'X':
            LaserX.value = start_pos
        elif motor == 'Z':
            LaserZ.value = start_pos
    finally:
        print("Returning motors to the starting positions.")
        if motor == 'X':
            LaserX.value = start_pos
            print('LaserX.value = start_pos')#LaserX.value = start_pos
        elif motor == 'Z':
            LaserZ.value = start_pos
            print('LaserZ.value = start_pos')
    print("Returning motors to the starting positions.")
    if motor == 'X':
        LaserX.value = start_pos
        print('LaserX.value = start_pos')#LaserX.value = start_pos
    elif motor == 'Z':
        LaserZ.value = start_pos
    print('LaserZ.value = start_pos')

    
        
