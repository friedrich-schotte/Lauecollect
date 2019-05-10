
from id14 import *
from time import sleep,strftime,time
from os import getcwd,remove,makedirs,listdir,chmod


# Online diagnostics:

# Setup required:
# Agilent 6-GHz oscilloscope in X-ray hutch:
# C2 = photodiode, C3 = MCP-PMT, C4 = trigger
# The first measurement needs to be defined as Delta-Time(2,3) with
# rising edge on C2 and falling edge in C3.
# The timing skews of each channel need to be set such the measured
# time delay is 0 when the nominal  time delay is zero.
# The second measurement needs defined as Area(3).
# msm delay will be measured as a time between rising edges of laser and
#

f = open("/data/pub/rob/test_timing.log",'w')
f.write("Scew: Timing error, sdev, samples, sampling error,MSM: Timing error, sdev, samples, sampling error\n")

actual_delay=id14b_scope.measurement(1)
msm_delay=id14b_scope.measurement(2)

n=1
actual_delay.time_range = 0.00000002
while n<100000000:
   
    
    actual_delay.start()
    start = time()
    while time()-start < 10 :
                sleep (0.1)
    t  = actual_delay.average
    sdev = actual_delay.stdev
    N = actual_delay.count
    err = sdev/sqrt(N-1)

    msmt  = msm_delay.average
    msmsdev = msm_delay.stdev
    msmN = msm_delay.count
    msmerr = msmsdev/sqrt(msmN-1)
    f.write(str(t)+" "+str(sdev)+" "+str(N)+" "+ str(err)+" "+str(msmt)+" "+str(msmsdev)+" "+str(smsN)+" "+ str(msmerr)+"\n")
               




    n=n+1
f.close
