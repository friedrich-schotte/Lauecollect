#!/usr/bin/env python
##Created on Oct 31 2017 to tune PID parameters of the Temperature Controller.
##
##There will be several different for loops and other things.
from time import time,sleep
from numpy import savetxt, loadtxt, mean, max, asarray
import matplotlib.pyplot as plt
plt.ion()
from channel_archiver import channel_archiver
from CA import caget, caput, cawait
from time import sleep,time
from thread import start_new_thread
import pickle
default_P,default_I,default_D = 1, 0.3, 0.562
T_step = 4 #in degree C
T_start = 22
T_lst = []
(P,I,D) = caget('NIH:LIGHTWAVE.PCOF'),caget('NIH:LIGHTWAVE.ICOF'),caget('NIH:LIGHTWAVE.DCOF')

scan_PID = []
for I in [0.177,0.316,0.421]:
    for P in [0.75,1,1.33]:
        for D in [0.421,0.562,0.75]:
            scan_PID.append([P,I,D])

data_folder = '/Volumes/C-1/Data/2019.05/temperature_controller/'
file = open(data_folder+"data.pickle",'r')
g_result = pickle.load(file)
# g_result_new = []
# for item in g_result:
#     item['oasis_T'] = 8.0
#     g_result_new.append(item)

def set_PID( P = 1, I = 0.3, D = 0.562):
    sleep(0.2)
    caput('NIH:LIGHTWAVE.PCOF',P)
    sleep(0.2)
    caput('NIH:LIGHTWAVE.ICOF',I)
    sleep(0.2)
    caput('NIH:LIGHTWAVE.DCOF',D)

def scan_once(dT = 5, T = 22.0, mode = ''):
    (P,I,D) = caget('NIH:LIGHTWAVE.PCOF'),caget('NIH:LIGHTWAVE.ICOF'),caget('NIH:LIGHTWAVE.DCOF')
    if mode == 'advance':
        caput('NIH:TEMP.VAL_ADV',T)
        cawait('NIH:TEMP.VAL_ADV')
    else:
        caput('NIH:TEMP.VAL',T)
        cawait('NIH:TEMP.VAL')
    sleep(1)

    while not caget('NIH:TEMP.DMOV'):
        sleep(0.05)
    sleep(1)
    caget('NIH:TEMP.DMOV')

    t_start = time()
    if mode == 'advance':
        caput('NIH:TEMP.VAL_ADV',T+dT)
        cawait('NIH:TEMP.VAL_ADV')
    else:
        caput('NIH:TEMP.VAL',T+dT)
        cawait('NIH:TEMP.VAL')
    sleep(1)

    while not caget('NIH:TEMP.DMOV'):
        sleep(0.05)
    t_end = time()
    sleep(5)
    current = caget('NIH:TEMP.I')
    res = {}
    res['temperature'] = T+dT
    res['current'] = current
    res['t start'] = t_start
    res['t end'] = t_end
    res['dt'] = t_end - t_start
    res['dT'] = dT
    res['P'] = P
    res['I'] = I
    res['D'] = D
    res['oasis_T'] = caget('NIH:CHILLER.VAL')
    if mode == 'advance':
        res['mode'] = 1
    else:
        res['mode'] = 0
    res['data_rbv'] = asarray(channel_archiver.history( 'NIH:LIGHTWAVE.RBV', t_start, t_end))
    res['data_current'] = asarray(channel_archiver.history( 'NIH:LIGHTWAVE.I', t_start, t_end))
    res['data_val'] = asarray(channel_archiver.history( 'NIH:LIGHTWAVE.VAL', t_start, t_end))
    return res

def plot(lst = [0,time()-600,time()], N = 0):
    lightwave_rbv = asarray(channel_archiver.history( 'NIH:LIGHTWAVE.RBV', lst[N][1], lst[N][2]))
    lightwave_current= asarray(channel_archiver.history( 'NIH:TEMP.I', lst[N][1], lst[N][2]))
    lightwave_val = asarray(channel_archiver.history( 'NIH:LIGHTWAVE.VAL', lst[N][1], lst[N][2]))
    temp_rbv = asarray(channel_archiver.history( 'NIH:TEMP.RBV', lst[N][1], lst[N][2]))
    temp_val = asarray(channel_archiver.history( 'NIH:TEMP.VAL', lst[N][1], lst[N][2]))

def scan(T_start = -16, dT = 4, N = 20,P = 1,I = 0.3,D = 0.562, mode = ''):
    global g_result
    temperature = []

    for i in range(N):
        temperature.append(T_start+i*dT)

    set_PID(P,I,D)
    for T in temperature:
        res = scan_once(T = T, dT = dT, mode = mode)
        g_result.append(res)


def scan_up_and_down(T_start,dT):
    for PID in scan_PID:
        scan(T_start = T_start ,dT =  dT,N = 1,P = PID[0],I = PID[1],D = PID[2])
        sleep(1)
        scan(T_start = T_start+dT,dT = -dT,N = 1,P = PID[0],I = PID[1],D = PID[2])
        sleep(1)
    pickle.dump(g_result,open(data_folder + "data.pickle","wb"))


def test_ramp():
    pass

def lst_to_array(lst = []):
    x = []
    for item in lst:
        #x.append([item['P'],item['I'],item['D'],item['temperature'],item['current'],item['dt']])
        x.append([item['temperature'],item['dT'],item['current'],item['dt'],item['P'],item['I'],item['D']])
    return asarray(x)

    plt.figure()
    plt.subplot(311)
    plt.plot(lightwave_rbv[0,:],lightwave_rbv[1,:])
    plt.plot(temp_rbv[0,:],temp_rbv[1,:])

    plt.subplot(312)
    plt.plot(lightwave_current[0,:],lightwave_current[1,:])

    plt.subplot(313)
    plt.plot(lightwave_val[0,:],lightwave_val[1,:])
    plt.plot(temp_val[0,:],temp_val[1,:])

if __name__ == "__main__":
    print("result = scan(T_start = -20.0, N = 20, dT = 5.0)")
    print("start_new_thread(scan,(-20,4,20,1,0.3,0.75))")
    print("plt.plot(data[:,0],data[:,1],'o');plt.xlabel('temperature in C');plt.ylabel('current in A')")
