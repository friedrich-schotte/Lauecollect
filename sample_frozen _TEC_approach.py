#!/usr/bin/env python
"""Monitor TEC temperature. If unexpected jump detected return freezing detected (flag TRUE).

Author: Valentyn Stadnytskyi
Date created: 2017-10-31
Date last modified: 2017-11-01
"""
#1509598102 <- Lowest temperature of -30C
#1509609600 11/02/2017 @ 8:00am (UTC)
__version__ = "0.1" #
from logging import debug,info,warn,error
import CA; CA.monitor_always = True
from channel_archiver import channel_archiver
from CA import caget, caput
from time import time
from numpy import asarray
import matplotlib.pyplot as plt
import numpy as np
plt.ion()
import warnings
warnings.simplefilter('ignore', np.RankWarning)

class Sample_Frozen_TEC(object):
    def __init__(self):
        name = "sample_frozen_TEC_approach"
        TMINUS = 10 # seconds
        self.ca_name_monitor = "NIH:TEMP.RBV"

    def _data(self):
         data =   dev._get_history(1509599167+10000,10000)
    def _sample_frozen(self):
        flag = False
        return flag
    def _get_history(self,time,duration):
        x = asarray(channel_archiver.history(self.ca_name_monitor,time-duration,time))[0,:]
        y = asarray(channel_archiver.history(self.ca_name_monitor,time-duration,time))[1,:]
        return (x,y)
    def _fit_curve(self,(x,y)):        # calculate polynomial

        fit_par = np.polyfit(x, y, 4)
        func = np.poly1d(fit_par)
        res_mean = np.mean(y)
        res_std = np.std(y)

        # calculate new x's and y's
        x_fit = np.arange(x[0], x[-1]+4, 1)
        y_fit = func(x_fit)
        
        return x_fit,y_fit, res_mean,res_std

    def _detect_change(x_fit,y_fit, res_mean,res_std):
        lst = []
        
    
    def _plot(self,pointer):
        future_points = 3
        x,y = dev._get_history(pointer-future_points,20)
        #print('got data: ', time.time()-time_start)
        future_x,future_y = dev._get_history(pointer+30,50) #reshape(dev._get_history(pointer+30,150))
        #print('got future data: ', time.time()-time_start)
        next_point = []
        for j in range(3):
            try:
                (next_x , next_y) = reshape(dev._get_history(pointer-future_points+j+1,1))
            #print 'next_x , next_y',next_x , next_y
                next_point.append([np.mean(next_x),np.mean(next_y)])
            except:
                pass
        res_x, res_y = reshape((x,y))
        x_fit,y_fit,res_mean,res_std = dev._fit_curve(reshape((x,y))) 
        plt.figure()
        plt.plot(x,y,'go')
        plt.plot(future_x,future_y,'ko')
        plt.plot(res_x,res_y,'ro')
        plt.plot(x_fit,y_fit,'bo')
        plt.title(str(pointer))
        plt.draw()
        plt.pause(0.01)
        plt.show()


    def frozen(self,pointer):
        #pointer = 1509599167 # just before the icing occured
        #pointer = 1509599165 - 10
        future_points = 3
        
        x,y = dev._get_history(pointer-future_points,20)

        #dev._get_history(pointer-future_points,5)
        #print('got data: ', time.time()-time_start)
        future_x,future_y = dev._get_history(pointer+30,50) #reshape(dev._get_history(pointer+30,150))
        #print('got future data: ', time.time()-time_start)
        next_point = []
        for j in range(3):
            try:
                (next_x , next_y) = reshape(dev._get_history(pointer-future_points+j+1,1))
                #print 'next_x , next_y',next_x , next_y
                next_point.append([np.mean(next_x),np.mean(next_y)])
            except:
                pass
        res_x, res_y = reshape((x,y))
        x_fit,y_fit,res_mean,res_std = dev._fit_curve(reshape((x,y)))

        error = []
        for i in range(3):
            error.append((next_point[i][1] - res_y[i])>0.01)
        #print error
            result = False
        if error[0] == True and error[1] == True and error[2] == True:
            result = True
        return result    
    def _find_nearest(array,value):
        idx = (np.abs(array-value)).argmin()
        return array[idx]
    def _find_lowest_index(array):
        return np.argmin(array)


    
sample_frozen = Sample_Frozen_TEC()


#time stamps where freezing occured or not
time_1 = time()-1000
time_2 = time()-1000
time_3 = time()-1000
time_4 = time()-1000

def test():
    # Load a test image.
    from time import time
    
    print("sample frozen file1: %r" % is_sample_frozen1)
    print("sample frozen file2: %r" % is_sample_frozen2)
    print("sample frozen file3: %r" % is_sample_frozen3)
    print("sample frozen file4: %r" % is_sample_frozen4)

    
def reshape((arr_x,arr_y)):
    import numpy as np
    res_x = np.arange(round(arr_x[0]),round(arr_x[-1]),1)
    res_y = res_x*0
    for i in res_x:
        #print 'i',i
        indices = np.argwhere((arr_x>=i-0.6) & (arr_x<=i+0.6))
        #print 'indices',indices
        sum_y = 0
        for j in indices:
            #print 'j',j
            sum_y = sum_y + arr_y[j]
            #print 'sum_y ,arr_y[j]',sum_y , arr_y[j]
        res_y[np.argwhere(res_x == i)] = sum_y/len(indices)  
        #print res_y[np.argwhere(res_x == i)]
    return (res_x, res_y)
    
if __name__ == "__main__": # for testing
    from pdb import pm # for debugging
    import logging
    logging.basicConfig(level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s")
    import time
    dev = Sample_Frozen_TEC()
    time_start = time.time()
    time_ice_detected = []
    for i in range(10): #360
        j = 1509950420+i
        print 'scanning',j, 'time', time.time()
        if dev.frozen(j):
            time_ice_detected.append(j)
            print 'froze at',j
            dev._plot(j)
    raw_input('type something')
    #for i in range(3):
    #    plt.plot(next_point[i][0],next_point[i][1],'o')
    #plt.show()
