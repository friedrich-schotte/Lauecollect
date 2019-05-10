#!/usr/bin/env python
##Created on Oct 31 2017 to tune PID parameters of the Temperature Controller.
##
##There will be several different for loops and other things.
from temperature_controller import temperature_controller as dev
from time import time,sleep
import numpy as np
import matplotlib.pyplot as plt
import CA; CA.monitor_always = True
from channel_archiver import channel_archiver
from CA import caget, caput

##checking if I can read commands right
print "Current temperature", dev.readT
print "Set Temperature", dev.setT
print "Moving?", dev.moving
defP,defI,defD = 0.75,0.07,1.33

def _write_to_file(from_T,to_T,par_P,par_I,par_D,start_time,end_time,sizeStep):
    thefile = open('temperature_controller_tunning_data_PID_var2_scan.txt', 'a')
    lst = [from_T,to_T,par_P,par_I,par_D,start_time,end_time,sizeStep]
    string = ''
    for i in lst:
        string += str(i) +', '
    thefile.write("%s\n" % string)
    thefile.close()
def _scan():    
    
    dev.PCOF,dev.ICOF,dev.DCOF = defP,defI,defD 
    Nsteps = 1
    sizeStep = 10
    par_P = dev.PCOF
    par_I = dev.ICOF
    par_D = dev.DCOF
    print 'Start: PID parameters:', dev.PCOF, dev.ICOF, dev.DCOF
    lst = []
    while dev.moving:
        sleep(0.5)

    sleep(5)
    from_T = round(dev.readT,1)
    P_lst = [0.1,0.1778,0.3162,0.5622,0.75,1,1.33]
    I_lst = [0.01,0.01778,0.03162,0.0422,0.05622,0.1,0.133,0.3162]
    D_lst = [0.31,0.562,0.75,1,1.33,1.78]
    for k in P_lst:  
        for j in range(2):
            for i in range(Nsteps):
                dev.PCOF = float(k)
                Step = (1-2*j)*sizeStep
                to_T = from_T+Step
                dev.set_value(to_T)
                start_time = time()
                sleep(3)
                total_time = 0
                par_P = dev.PCOF
                par_I = dev.ICOF
                par_D = dev.DCOF
                print 'New --> PID parameters:', dev.PCOF, dev.ICOF, dev.DCOF
                flag = dev.moving
                while flag:
                    flag = dev.moving
                    sleep(0.5)
                    total_time += 0.5
                    if total_time > 90:
                        dev.PCOF,dev.ICOF,dev.DCOF = defP,defI,defD
                        total_time = 100
                        print 'to long of a wait'
                        flag = False
                end_time = time() - start_time
                _write_to_file(from_T,to_T,par_P,par_I,par_D,start_time,end_time,Step)
                print 'from ',from_T,'to ', to_T,'in ',time() - start_time,'seconds'
                total_time = 0
                if dev.moving:
                    sleep(0.5)
                from_T = to_T

                
def _t_dep_PID():
    dev.PCOF,dev.ICOF,dev.DCOF = defP,defI,defD
    Nsteps = 1
    sizeStep = 10
    coeff = 1
    print 'Start: PID parameters:', dev.PCOF, dev.ICOF, dev.DCOF
    lst = []
    while dev.moving:
        sleep(0.5)

    sleep(5)
    from_T = round(dev.readT,1)
    while dev.moving:
        sleep(0.5)
    sleep(5)
    for j in range(2):
            for i in range(Nsteps):
                dev.PCOF,dev.ICOF,dev.DCOF = defP,defI,defD
                Step = (1-2*j)*sizeStep
                to_T = from_T+15 + abs(Step*0.1*coeff)
                dev.set_value(to_T)
                print 'temperature changed to',to_T
                start_time = time()
                sleep(2)
                print 'New --> PID parameters:', dev.PCOF, dev.ICOF, dev.DCOF
                flag = dev.moving
                total_time = 0
                flag_I = True
                if coeff == 0:
                    flag_I= False
                
                while flag:
                    #print total_time
                    flag = dev.moving
                    sleep(0.1)
                    total_time += 0.1
                    if flag_I:
                        if abs(dev.readT - to_T) < abs(10):
                            dev.ICOF,dev.DCOF = 0.0562,0.5
                            #dev.DCOF = 0.5
                            to_T = from_T+15
                            dev.set_value(to_T)
                            flag_I = False
                            print 'integral term changed to ',dev.ICOF ,' at ', total_time
                            print 'temperature changed to',to_T
                    if total_time > 90:
                        dev.PCOF,dev.ICOF,dev.DCOF = defP,defI,defD
                        total_time = 100
                        print 'to long of a wait'
                        flag = False
                print 'End: PID parameters:', dev.PCOF, dev.ICOF, dev.DCOF
                end_time = time() - start_time
                _write_to_file(from_T,to_T,dev.PCOF,dev.ICOF,dev.DCOF,start_time,end_time,Step)
                print 'from ',from_T,'to ', to_T,'in ',time() - start_time,'seconds'
                total_time = 0
                dev.PCOF,dev.ICOF,dev.DCOF = defP,defI,defD
                if dev.moving:
                    sleep(0.5)
                from_T = to_T
                   
print 'DONE'
_t_dep_PID()
