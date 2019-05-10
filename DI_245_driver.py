#!/bin/env python
# -*- coding: utf-8 -*-
"""
Four-channel USB Voltage and Thermocouple DAQ driver,
Resolution: 14-bit
Sampleling rate: 8000 Hz max
Range: +/- 50 V to +/- 10 mV, in 3 steps per decade (1,2.5,5)
build in cold junction compensation (CJC) for thermocouples

Reference:
DI-245 Communication Protocol
www.dataq.com/resources/pdfs/support_articles/DI-245-protocol.pdf

COM Port Communication Settings:
Baud rate: 115200, Data bits: 8, Stop bits: 1, Parity: none

Installing the DI-245 driver package and connecting DI-245 hardware to the
host computer’s USB port results in a COM port being hooked by the operating
system and assigned to the DI-245 device.

Multiple DI-245 devices may be connected to the same PC without additional
driver installations, which results in a unique COM port number assignment to
each by the operating system.

The DI-245 employs a simple ASCII character command set that allows complete
control of the instrument.

Long commands and arguments (longer than two characters) are separated by a
space character (0x20), and each long command string must be terminated with
a carriage return character (x0D). Long commands do not echo until the 0x0D
character is received.

Short commands (2 characters or less) are preceded with a null character
(0x00), which is not echoed, but each command character is echoed as it is
sent.

<0x00>command<(0x20)<argument1>(0x20)<agrument2>(0x0D)>

For example, the command "\0A1" generates the following response: "A1 2450"

Commands:
"\0A1"
 
      Returns device name: "2450"
"chn 0 5120\r" Enable analog channel 0 to measure an N type TC as the first scan list member
"chn 1 514\r"  Enable analog channel 2 to measure +/-100 mV as the second scan list member
"chn 2 3331\r" Enable analog channel 3 to measure +/-1 V as the third scan list member
"xrate 1871 10\r" Burst rate is 10 Hz,
               sampling frequency SF=79, averaging frequency AF=7
               SF+AF*256 = 79+7*256 = 1971, burst rate B = 8000/((SF+1)*(AF+3))
"\0S1"         Start the scanning processes, causes the DI-245 to respond with a continuous binary
               stream of one 16-bit signed integers per enabled measurement.
               The stream sequence repeats until data acquisition is halted by the stop
               command.
"\0S0"         Stop the scanning processes

Valentyn Stadnytskyi,
October 2017 - July 2018
last update: July 2, 2018

"""

from numpy import concatenate,zeros,mean,std,uint16, nan
from CAServer import casput
from serial import Serial
from time import time, sleep,gmtime, strftime
from sys import stdout
import os.path
from pdb import pm
from persistent_property import persistent_property
from struct import unpack as struct_unpack

import traceback

import logging
from logging import error,warn,info,debug


__version__ = '2.0.1' #

class DI245(object):

    def __init__(self):
        """        instance init command
        """
        self.available_ports = []
        self.ser = None
        self.timeout = 2
    

    def initialize(self, available_port = []):
        """
        looks for ports with find_com_ports() method
        and returns self.avaiable ports
        """
        if len(self.available_ports) == 0:
            self.available_ports = self.find_com_port()
        if len(self.available_ports) != 0:
            self.use_com_port(0)
            self.stop_scan()
            self.dict_DI245 = {}
            self.dict_DI245['Device name'] = self.inquire('A1',6)[2:]
            self.dict_DI245['Firmware version'] = int(self.inquire('A2',4)[2:],16)/100.
            self.dict_DI245['Last Calibration date in hex'] = self.inquire('A7',10)[2:]
            self.dict_DI245['Serial Number'] = self.inquire('NZ',12)[2:][:-2]
  
            for i in self.dict_DI245.keys():
                print i, self.dict_DI245[i]
            print 'Complete: Initialization of the DI-245 with S\N', self.dict_DI245['Serial Number']


        else:
            print('no DI-245 available')

        
    
    def use_com_port(self,N = 0):
        """
        1) connect to the serial port in self.available_ports(N)
        2) stops scanning if one is in progress
        3) tries to set buffer size
        """
        try:
            port = self.available_ports[N][0]
            self.ser = Serial(port, baudrate=115200, rtscts=True, timeout=0.1)
            self.stop_scan()
            self.ser.flushInput()
            self.ser.flushOutput()
            self.ser.set_buffer_size(rx_size = 409200)
            info('try: use_com_port N = %r' % N)
        except:
            error(traceback.format_exc())
            warn('failed to connect to the requested com port')

    def check_avaiable_ports(self):        
        import serial.tools.list_ports
        lst = serial.tools.list_ports.comports()
        for element in lst:
            print(element.device,element.description)
            
    def find_com_port(self):
        import serial.tools.list_ports
        lst = serial.tools.list_ports.comports()
        available_ports = []
        print('looking for DI245 available ....')
        for element in lst:
            debug('checking %r' % element.device)
            if element.description.find('DI245') > -1:
                debug("the DI-245 is available at %r" %(element.device))
                available_ports.append([element.device,element.serial_number])
        return available_ports
    
    def read(self, N):
        """
        reads N bytes from the serial buffer
        """
        from time import time, sleep
        tstart = time()
        sleep(self.timeout/10.)
        buff = 'timeout'
        while time() - tstart < self.timeout:
            debug('while loop %r %r' % (time(),1))
            if self.waiting()[0] == N:
                buff = self.ser.read(N)
            else:
                sleep(self.timeout)
        return buff
    
    def write(self,command):
        """
        write command to DI-245.
        flushed input/output first, then writes.
        """
        try:
            if self.ser.isOpen():
                self.ser.flushInput()
                self.ser.flushOutput()
                self.ser.write(command)
                result = True
            else:
                result = False
        except:
            error(traceback.format_exc())
            result = False
        return result    

    def inquire(self,command,Nbytes = 0):
        """
        write command and read Nbytes
        """
        self.write(command)
        return self.read(Nbytes)


    
    def close_port(self):    
        try:
            if self.ser.isOpen():
                self.ser.close()
                result = True
            else:
                result = False
        except:
            error(traceback.format_exc())
            result = False
        return result    

    #Scanning\data acquisition section
    #an example: chn(0x20)member(0x20)value(0x0D)
    #2-byte value needs to be converted from binary to int. The binary 2 byte start counting from right.
    #The values in the function definition are default values in case user does not specify them.
    def config_channels(self,scan_lst = ['0','1','2','3'],phys_ch_lst = ['0','1','2','3'],gain_lst = ['0.5','0.5','0.5','0.5'], rate = 0):
        """
        configures channels: maps physical channel list on the scan list with defined gains.
        configures readout rate.
        """
        
        self.scan_lst = scan_lst
        self.phys_ch_lst = phys_ch_lst
        self.gain_lst = gain_lst
        #This method needs to be rewritten to take a list instead of a set of parameters. This will help with scalability. 
        
        _config_dict_gain = {}
        _config_dict_gain['0.010'] = '00101'
        _config_dict_gain['0.025'] = '00100'
        _config_dict_gain['0.05'] = '00011'
        _config_dict_gain['0.1'] = '00010'
        _config_dict_gain['0.25'] = '00001' #works
        _config_dict_gain['0.5'] = '00000'
        _config_dict_gain['1'] = '01101'
        _config_dict_gain['2.5'] = '01100'
        _config_dict_gain['5'] = '01011' #
        _config_dict_gain['10'] = '01010'
        _config_dict_gain['25'] = '01001'
        _config_dict_gain['50'] = '01000'
        _config_dict_gain['B-thrmc'] = '10000'
        _config_dict_gain['E-thrmc'] = '10001'
        _config_dict_gain['J-thrmc'] = '10010'
        _config_dict_gain['K-thrmc'] = '10011'
        _config_dict_gain['N-thrmc'] = '10100'
        _config_dict_gain['R-thrmc'] = '10101'
        _config_dict_gain['S-thrmc'] = '10110'
        _config_dict_gain['T-thrmc'] = '10111'
        result = []
        for i in range(len(self.scan_lst)):
            config_byte = str(int('000'+_config_dict_gain[self.gain_lst[i]]+'0000' +
                                  bin(int(self.phys_ch_lst[i]))[2:].zfill(4),2))
            ch_config_command = 'chn '+self.scan_lst[i]+' '+config_byte+' \x0D'

            if self.inquire(ch_config_command,len(ch_config_command)) == ch_config_command:
                result.append(True)
            else:
                result.append(False)
                
        xrate_config_command = 'xrate 4099 2000 \x0D'
        if self.inquire(xrate_config_command,len(ch_config_command)) == xrate_config_command:
            result.append(True)
        else:
            result.append(False)
        return int(mean(result)), result
        
    #this method sends a proper command to start the scan.    
    def start_scan(self):
        """
        issues start command "S1" that initializes data stream from the DI 245
        """
        info('DRIVER: scan starts, inWaiting %r' % self.ser.inWaiting())
        self.ser.read(self.ser.inWaiting())
        read_byte_temp = ""        
        while read_byte_temp != 'S1':
            self.ser.write('(0x00) S1')
            sleep(1)
            read_byte_temp = self.ser.read(2) #read 2-byte echo response
        info('The configured measurement(s) has(have) started')
    
    def read_number(self, N_of_channels, N_of_points = 1):
        """
        reads N channels(N_of_channels) with N points(N_of_points)
        and puts them in an array (N channels x N points)
        """
        self.channels_to_read = N_of_channels
        self.datapoints_to_read = N_of_points
        value_array = zeros((self.channels_to_read,N_of_points)) 
        for j in range(self.channels_to_read):
            #value_array[2*j] = time.time()
            tempt_t = time()
            read_byte_temp = self.ser.read(2)
            try:
                read_byte = bin(struct_unpack("H", read_byte_temp)[0])[2:].zfill(16)
            except Exception as e:
                error('read_byte = %r and error %r' % (read_byte_temp,e))
            read_byte_lst = list(read_byte)
            sync_byte = read_byte_lst[15] #this is the byte 0 that is issued in DI-245 for sync. 0 stand for the beginning of channel(s) data stream. Hence, every set of readouts  starts with 0. 
            del(read_byte_lst[15]) #this needs to be used
            del(read_byte_lst[7])  #this needs to be used
            read_byte = ""
            for i in read_byte_lst:
                read_byte += str(i)
            int_val = float(int(read_byte,2))
            value_array[j] = int_val
        return value_array
        
    def waiting(self):
        """
        returns number of bytes waiting in the serail buffer
        (in, out)
        """
        try:
            result = (self.ser.inWaiting(),self.ser.out_waiting)
        except Exception,e:
            error(e)
            result = (nan,nan)
        return result
    
    def stop_scan(self):
        if self.ser.isOpen():
            self.write('S0') #S0\xfd\x7f <- reply
            result = True
        else:
            result = False
        return result    
        #print "aquired points",self.ser.inWaiting()
        #print "measurement ended"
        
    def full_stop(self):
        debug('full stop command executed')
        self.stop_scan()
        self.close_port()
    
di245_driver = DI245()
if __name__ == "__main__":
    from tempfile import gettempdir
    
    logging.basicConfig(filename = gettempdir()+'/di_245_driver.log',
                        level=logging.DEBUG,
                        format="%(asctime)s %(levelname)s: %(message)s")
    dev = di245_driver
    
    print('----- The driver for the DI-245 -----')
    print('*dev*  is already created instance')
        
			
