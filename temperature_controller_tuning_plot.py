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

def plot_data(temp_plot,lst):
    print lst
    from_t = floor(float(lst[5]))
    duration_t = floor(float(lst[6]))
    a = asarray(channel_archiver.history("NIH:TEMP.RBV",from_t,from_t+duration_t))
    
 #lst[7] - step
    #lst[2],3,4 - P I D parameters
    if float(lst[7]) == temp_plot:# and float(lst[7]) == 5 :
        plt.plot(a[0,:]-a[0,0],a[1,:]-a[1,0])
        #legend_lst.append('P = '+ round_p(lst[2]) + ' I = ' + round_p(lst[3])+ ' D = ' + round_p(lst[4]))
        legend_lst.append('dT = '+ lst[0]+'->'+lst[1])
plt.figure()
t_jump = 10
with open(getcwd()+"\\temperature_controller_tunning_data_PID_var_scan.txt",'r') as f:
    for line in f: 
        print line
        lst = line.split(',')
        plot_data(t_jump,lst)
plt.legend(legend_lst)
plt.title('temperature jump by ' + str(t_jump) + ' K;')
plt.xlabel('time. seconds')
plt.ylabel('Temperature change, K')
plt.draw()
plt.show()

