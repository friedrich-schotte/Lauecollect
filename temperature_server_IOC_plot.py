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
    a = asarray(channel_archiver.history("NIH:"+name,from_time-duration,from_time))
    
    return a
def temp_to_oasis(T):
    t_min = T*0+ 8
    t_max = T*0+ 45
    T_min = T*0+ -16
    T_max = T*0+ 120
    t = ((T-T_min)/(T_max-T_min))*(t_max-t_min) + t_min
    return t
temp_RBVT1 = get_data(name = 'TEMP.RBV',from_time = 1557934895.621, duration = 600)
temp_VALT1 = get_data(name = 'TEMP.VAL',from_time = 1557934895.621, duration = 600)

temp_RBVT2  = get_data(name = 'TEMP.RBV',from_time = 1557934739.735, duration = 600)
temp_VALT2  = get_data(name = 'TEMP.VAL',from_time = 1557934739.735, duration = 600)


oasis_cmdT  = get_data(name = 'CHILLER.VAL',from_time = time(), duration = 1200)
plt.plot(temp_RBVT2[0,:]-temp_RBVT2[0,0],temp_RBVT2[1,:],'o')
plt.plot(temp_VALT2[0,:]-temp_VALT2[0,0],temp_VALT2[1,:],'o')
plt.plot(temp_RBVT1[0,:]-temp_RBVT1[0,0],temp_RBVT1[1,:],'o')
plt.plot(temp_VALT1[0,:]-temp_VALT1[0,0],temp_VALT1[1,:],'o')
#plt.plot(oasis_T[0,:],oasis_T[1,:],'o')
#plt.plot(oasis_cmdT[0,:],oasis_cmdT[1,:],'o')
plt.show()


