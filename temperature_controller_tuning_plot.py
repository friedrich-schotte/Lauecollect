from channel_archiver import channel_archiver
from time import time,sleep
from numpy import asarray
from time import time
import matplotlib.pyplot as plt
from math import floor
from os import getcwd
legend_lst = []

def round_p(lst):
    return str(round(float(lst),3))

def get_data(name = 'TEMP',from_time = 0, duration = 0):
    a = asarray(channel_archiver.history("NIH:"+name+".RBV",from_time-duration,from_time))
    
    return a
def temp_to_oasis(T):
    t_min = T*0+ 8
    t_max = T*0+ 45
    T_min = T*0+ -16
    T_max = T*0+ 120
    t = ((T-T_min)/(T_max-T_min))*(t_max-t_min) + t_min
    return t
temp  = get_data(name = 'TEMP',from_time = time(), duration = 1200)
oasis  = get_data(name = 'CHILLER',from_time = time(), duration = 1200)

plt.plot(temp[0,:],temp_to_oasis(temp[1,:]),'o')
plt.plot(oasis[0,:],oasis[1,:],'o')
plt.show()


