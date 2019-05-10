#!/bin/env python
# AMO data collection
# 4/3/2011 RH

# To Do
# 82.3 Hz? Need to force open shutter. EPICS control?
# Could copy function update_bkg_image() to close shutter.
# Use 11 bunch. 41Hz.

from id14 import *
from time import sleep, time, strftime
from epics import caget,caput,PV

# This will overwrite old images
#base_filename="test_file_"
#base_filename="CF3Br_last_14keV_"
base_filename="nogas_last_14keV_"


# Number of pulses per image
num_pulses=25000

extension=".mccd"
directory="/data/young_1103/CF3Br/" # Need to create manually
images=1 #How many images to collect

# Log to file
filename_log=directory+base_filename+".log"
f = open(filename_log,'w')

#EPICS PV's
p1_mean=PV('14IDB:waveSurfer:P1:mean.VAL')
p1_sdev=PV('14IDB:waveSurfer:P1:sdev.VAL')
p2_mean=PV('14IDB:waveSurfer:P2:mean.VAL')
p2_sdev=PV('14IDB:waveSurfer:P2:sdev.VAL')
p1_num=PV('14IDB:waveSurfer:P1:num.VAL')
p1_read=PV('14IDB:waveSurfer:P1:read.PROC')
p2_read=PV('14IDB:waveSurfer:P2:read.PROC')
Wave_Clear=PV('14IDB:waveSurfer:clearSweeps.PROC')

f.write("BackgroundDate BackgroundTime Filename FileDate FileTime Pulses I0_mean I0_sdev BS_mean BS_sdev Triggers\n")

# Readout detector.
for image in range(1,(images+1)):
    Wave_Clear.value=1
    back_time=strftime("%Y-%m-%d %H:%M:%S")
    print "Reading background "+back_time
    ccd.read_bkg() # Read background

    ccd.start() # Start integrating

    pulses.value=num_pulses
#    tmode.value=0 # Continous
#    sleep(exposure_time)
#    tmode.value=1 # Counted

    while(pulses.value > 0): sleep(0.5)
   
    filename=directory+base_filename+str(image)+extension
    read_msg=filename+" "+strftime("%Y-%m-%d %H:%M:%S")
    print read_msg
    ccd.readout(filename)

    p1_read.value=1
    p2_read.value=1
    sleep(5) # time to readout detector
    f.write(back_time+" "+read_msg+" "+str(num_pulses)+" "+str(p1_mean.value)+" "+str(p1_sdev.value)+" "+str(p2_mean.value)+" "+str(p2_sdev.value)+" "+str(p1_num.value)+"\n")

sleep(1)  
f.close()
