"""
DATAQ 4108 device level code

date: Nov 2017 - July 6 2018
author: Valentyn Stadnytskyi

version 1.0.0 - basic DL with 3 functions
                - set temperature
                - get temperature
                - get faults
                - 3 circular buffers
                - the read-back-value circular buffer is constantly
                populated with data unless set temperature or faults requests
                were submitted. 

"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from numpy import nan, mean, std, asarray, array, concatenate, delete, round, vstack, hstack, zeros, transpose, split, unique, nonzero, take, savetxt, min, max
from serial import Serial
from time import time, sleep, clock
import sys
import os.path
import struct
from pdb import pm
from time import gmtime, strftime, time
import logging
from logging import debug, info, warn, error

from persistent_property import persistent_property
from DB import dbput, dbget
from module_dir import module_dir
from normpath import normpath

from struct import pack, unpack
from timeit import Timer, timeit
from OasisChiller_LL import oasis_driver #this is DI4108 driver imported from communication LL python file
from circular_buffer_LL import server
from threading import Thread, Timer
import thread
from datetime import datetime

#plt.ion()

__version__ = '1.0.0' #


class OasisChiller_DL(object):

    pr_start_set_temperature = persistent_property('start set temperature', 0.0)
    pr_meas_period = persistent_property('period, s (how often to measure)', 10.0)
    pr_broadcast_period = persistent_property('broadcast_period, s (how often to measure)', 10.0)
    pr_buffer_size = persistent_property('circular buffer size',(2,1))
    pr_broadcast = persistent_property('broadcast flag',False)
    
    def __init__(self):

        self.name = 'Oasis_DL'
        self.CAS_prefix = 'NIH:OASIS_DL'
        self.pr_start_set_temperature = 4.0
        self.pr_meas_period = 5.0
        self.pr_broadcast_period = 5.0
        self.pr_broadcast = True
        
        self.pr_buffer_size = (2,int(86400/self.pr_meas_period))
        self.dev = oasis_driver
        self.queue = []
        self.running = False
        
    def connect(self):
        from CAServer import casput
        self.dev.init()
        print('init done')
        self.circular_buffer = {}
        self.circular_buffer['actual_temperature'] = server(size = self.pr_buffer_size, var_type = 'float64')
        self.circular_buffer['target_temperature'] = server(size = (2,100), var_type = 'float64')
        self.circular_buffer['faults'] = server(size = (2,100), var_type = 'float64')

        self.get_actual_temperature()
        sleep(1)
        self.get_target_temperature()
        sleep(1)
        self.get_faults()
        sleep(1)
        self.monitor()
        
        
    def init(self):
        from time import time
        self.connect()
        print('Measurement thread has started')
        self.running = True
        self.fault_check_time = time()
        while self.running == True:
            tstart = time()
            if time() - self.fault_check_time > 30 and len(self.queue) == 0:
                self.fault_check_time = time()
                self.queue.append('self.get_faults(broadcast = True)')
            self.run_once()
            sleep(self.pr_meas_period-(time()-tstart))
        self.shutdown()   
        
        
    def stop(self):
        self.running = False
        self.dev.ser.flushInput()
        self.dev.ser.flushOutput()
        del self

    def reboot(self):
        self.dev._write('\xFF')
    
 
    def set_target_temperature(self,temperature, broadcast = True):
        from time import time
        from CAServer import casput
        from numpy import nan,isnan
        print('set temperature %r' % temperature)
        buff = self.circular_buffer['target_temperature'].buffer[1,:]
        pointer = self.circular_buffer['target_temperature'].pointer
        if buff[pointer] != temperature and not isnan(temperature):
            self.dev.target_temperature = temperature
            data = zeros((2,1), dtype = 'float64')
            data[0] = time()
            data[1] = temperature
            self.circular_buffer['target_temperature'].append(data)
            if broadcast:
                value = temperature
                print('broadcasting target T = %r' % value)
                casput(self.CAS_prefix + '.VAL', value)

    def get_target_temperature(self):
        from CAServer import casput
        temperature = self.dev.target_temperature        
        if self.pr_broadcast:
            value = temperature
            print('broadcasting target T = %r' % value)
            casput(self.CAS_prefix + '.VAL', value)

    def add_to_queue(self, pvname = '', value = '' , char_val = ''):
        if pvname == self.CAS_prefix + '.VAL':
            self.queue = ['self.set_target_temperature(' +
                          str(value)+')']
        elif pvname == self.CAS_prefix + '.GET_FLT':
            self.queue = ['self.get_faults()']
            

    def get_actual_temperature(self):
        from time import time
        from CAServer import casput
        data = zeros((2,1))
        data[0] = time()
        data[1] = self.dev.actual_temperature
        self.circular_buffer['actual_temperature'].append(data)
        if self.pr_broadcast:
            value = data[1] 
            casput(self.CAS_prefix + '.RBV', value)
            

    def get_faults(self, broadcast = False):
        from time import time
        from CAServer import casput
        data = zeros((2,1))
        data[0] = time()
        arr = self.dev.faults
        print('getting faults. faults = %r' % arr[1])
        if arr[0]:
            data[1] = arr[0]*arr[1]
            self.circular_buffer['faults'].append(data)
            if broadcast:
                value = data[1]
                casput(self.CAS_prefix + '.FLT', value)
        
        
    
    def status(self): #
        if dev.faults[0]  == 0:
            res = True
        else:
            res = False
        return res #0 is good , 1 is bad

    def exec_queue(self):
        for idx in self.queue:
            exec(idx)
            self.queue = []

    def run_thread(self):
        from thread import start_new_thread
        start_new_thread(self.init,())


    

    def stop(self):
        from CAServer import casdel
        casdel(self.CAS_prefix)
        del self
        print('thread is done')

    def run_once(self):
        """
        This function collects data and puts it in the Ring Buffer.
        It is run in a separate thread(See main priogram)
        """
        if len(self.queue) ==0:
            info('reading actual temperature')
            self.get_actual_temperature()
        else:
            info('executing queue: %r' % self.queue)
            self.exec_queue()

    def monitor(self):
        from CAServer import casmonitor,casput
        if not self.running:
            value = self.dev.target_temperature
            casput(self.CAS_prefix+ ".VAL",value)
            
        casmonitor(self.CAS_prefix+ ".VAL",callback = self.add_to_queue)
        #casmonitor(self.CAS_prefix+ "SET_VAL",callback = self.add_to_queue)
        #casmonitor(self.CAS_prefix+ "SET_VAL",callback = self.add_to_queue)

                  
        

        
    

def TimeItFunc(string, number):
    arr = zeros(number)
    for i in range(number):
        start_time = clock()
        exec(string)
        arr[i] = clock() - start_time
    print('mean: %.5f \n std: %.5f \n min: %.5f\n max: %.5f' % (mean(arr), std(arr), min(arr), max(arr)))
oasis_DL = OasisChiller_DL()

if __name__ == "__main__": #for testing
    print('oasis_DL.run_thread()')

