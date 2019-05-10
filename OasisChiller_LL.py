"""
Oasis Chiller Communication Low Level code

Author: Valentyn Stadnytskyi
Date:November - July 5 2018

avaiable properties:
    - target_temperature
    - actual_temperature
    - faults

version 1.0.0 - basic working version

"""

from serial import Serial
from time import time, sleep, clock
import sys
import os.path
from pdb import pm
from time import gmtime, strftime
import logging
from persistent_property import persistent_property
from struct import pack, unpack
from timeit import Timer

from numpy import nan

__version__ = '1.0.0' #


class Driver(object): #Oasis driver

    def __init__(self):
        #tested dec 17, 2017  
        print('bbb')
    def init(self):
        self.find_port()
        
        self.ser.flushInput()
        self.ser.flushOutput()
        print("initialization of the driver is complete")
    
    def find_port(self):
        import serial.tools.list_ports
        lst = serial.tools.list_ports.comports()
        for item in lst:
            port = item.device
            #print('trying ' + com_port)
            try:
                self.ser = Serial(port, baudrate=9600, timeout=0.1)
                sleep(0.5)
                try:
                    print('open Com port (%r) found (%r)' % (port,item.description))
                    if self._inquire('A',3)[0] == 'A':
                        print("the requested device is connected to COM Port %r" % self.ser.port)
                        break
                    else:
                        print("Oasis is not found")
                        self.ser.close()
                        print("closing com port")
                except:
                    self.ser.close()
            except:
                pass
        
    
    """Set and Get persistent_property"""
    # functions for persistent properties if needed
    
    """Basic serial communication functions"""   
    def _readall(self):
        #tested dec 17, 2017
        return self.ser.readall()

    def _readN(self,N):
        #tested dec 17, 2017
        from numpy import nan
        data = ""
        if self._waiting()[0] >= N:
            data = self.ser.read(N)
            if len(data) != N:
                print("%r where requested to read and only %N where read" % (N,len(data)))
                data = nan
        else:
            data = nan
        return data
    
    def _write(self,command):
        #tested dec 17, 2017
        self.ser.flushOutput()
        self.ser.write(command)
        
    def _flush(self):
        #tested dec 17, 2017
        self.ser.flushInput()
        self.ser.flushOutput()
        
    def _inquire(self,command, N):
        #tested dec 17, 2017
        from time import time
        from numpy import nan
        self.ser.write(command)
        tstart = time()
        while self.ser.inWaiting() < N:
            sleep(0.1)
            if time() - tstart > 10:
                break   
        if self.ser.inWaiting() == N:
            result = self._readN(N)
        else:
            result = nan
        return result
        
    def _waiting(self):
        #tested dec 17, 2017
        return [self.ser.in_waiting,self.ser.out_waiting]
        
    def _close_port(self):
        #tested dec 17, 2017
        self.ser.close()


    def _open_port(self):
        #tested dec 17, 2017
        self.ser.open()

    def set_target_temperature(self,temperature):
        local_byte = pack('h',round(temperature*10,0))
        byte_temp = local_byte[0]+local_byte[1]
        self._inquire('\xe1'+byte_temp,1)
    def get_target_temperature(self):  
        res = self._inquire('\xc1',3)
        temperature = unpack('h',res[1:3])[0]/10.
        return temperature
    target_temperature = property(get_target_temperature,set_target_temperature)
        
    def get_actual_temperature(self):
        res = self._inquire('\xc9',3)
        temperature = unpack('h',res[1:3])[0]/10.
        return temperature
    actual_temperature = property(get_actual_temperature)
    
    def get_faults(self):
        from numpy import log2
        res_temp = self._inquire('\xc8',2)
        res = unpack('b',res_temp[1])[0]
        
        if res == 0:
            result = (0,int(res))
        else:
            result = (1,int(log2(abs(res))))
        return result
    faults = property(get_faults)

    def get_PID(self):
        from time import sleep
        dic = {}
        res_dic = {}
        try:
            dic['p1'] = ('\xd0',3)
        except:
            dic['p1'] = nan
        try:
            dic['i1'] = ('\xd1',3)
        except:
            dic['p1'] = nan
        try:
            dic['d1'] = ('\xd2',3)
        except:
            dic['p1'] = nan
        try:
            dic['p2'] = ('\xd3',3)
        except:
            dic['p1'] = nan
        try:   
            dic['i2'] = ('\xd4',3)
        except:
            dic['p1'] = nan
        try:
            dic['d2'] = ('\xd5',3)
        except:
            dic['p1'] = nan
        for key in dic.keys():
            res = self._inquire(dic[key][0],dic[key][1])
            if res is not nan:
                res_dic[key] = unpack('H',res[1]+res[2])
            else:
                res = nan
            sleep(0.5)
        return res_dic

    def set_default_PID(self, pid_dic = ('','')):
        pid_dic = {}
        #factory settings: good settings
        pid_dic['p1'] = 90
        pid_dic['i1'] = 32
        pid_dic['d1'] = 2
        pid_dic['p2'] = 50
        pid_dic['i2'] = 35
        pid_dic['d2'] = 3
        dic = {}
        dic['p1'] = '\xf0'
        dic['i1'] = '\xf1'
        dic['d1'] = '\xf2'
        dic['p2'] = '\xf3'
        dic['i2'] = '\xf4'
        dic['d2'] = '\xf5'
        for key in pid_dic.keys():
            byte_temp =  pack('h',round(pid_dic[key],0))    
            self._inquire(dic[key]+byte_temp,1)
            sleep(0.5)

    def set_PID(self, pid_dic = ('','')):
        pid_dic = {}
        #factory settings: good settings
        pid_dic['p1'] = 90
        pid_dic['i1'] = 32
        pid_dic['d1'] = 2
        pid_dic['p2'] = 50
        pid_dic['i2'] = 35
        pid_dic['d2'] = 3
        dic = {}
        dic['p1'] = '\xf0'
        dic['i1'] = '\xf1'
        dic['d1'] = '\xf2'
        dic['p2'] = '\xf3'
        dic['i2'] = '\xf4'
        dic['d2'] = '\xf5'
        for key in pid_dic.keys():
            byte_temp =  pack('h',round(pid_dic[key],0))    
            self._inquire(dic[key]+byte_temp,1)
            sleep(0.5)
##            
        

        

oasis_driver = Driver()
        
if __name__ == "__main__": #for testing
    print('oasis_driver.find_port()')
    print('oasis_driver.actual_temperature')
    print('oasis_driver.target_temperature')
    print('oasis_driver.target_temperature = 25')
    print('oasis_driver.faults')
	
