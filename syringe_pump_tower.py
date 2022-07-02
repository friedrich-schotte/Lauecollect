#!/usr/bin/python
# -*- coding: utf-8 -*-


"""
Cavro Centris Syringe pump device/IOC module
author: Valentyn Stadnytskyi
Created: May 28 2019
Last modified: May 28 2019
"""

__version__ = '0.0.0'

from devices.Cavro_Centris_Pump import Driver
from auxiliary import autoreload

import traceback
import psutil, os
import platform #https://stackoverflow.com/questions/110362/how-can-i-find-the-current-os-in-python
p = psutil.Process(os.getpid()) #source: https://psutil.readthedocs.io/en/release-2.2.1/


from numpy import nan, mean, std, nanstd, asfarray, asarray, hstack, array, concatenate, delete, round, vstack, hstack, zeros, transpose, split, unique, nonzero, take, savetxt, min, max
from serial import Serial
from time import time, sleep, clock
import sys
import os.path
import struct
from pdb import pm
from time import gmtime, strftime, time
from logging import debug,info,warning,error
from thread import start_new_thread



from struct import pack, unpack
from timeit import Timer, timeit

from threading import Thread, Event, Timer, Condition

class CavroCentrisSyringePump(object):

    """circular buffers dictionary contains information about all circular buffers and their type (Server, Client or Queue)"""
    circular_buffers = {}

    def __init__(self):
        #Thread.__init__(self)
        self.running = False
        #self.daemon = False # OK for main thread to exit even if instance is still running
        self.description = ''

        self.command_queue = []

####################################################################################################
### Basic IOC operations
####################################################################################################
    def first_time_setup(self):
        """default factory setting or first time setup"""
        raise NotImplementedError

    def init(self, pump_id = None):
        """
        initialize the server\IOC
        """
        from devices.Cavro_Centris_Pump import Driver
        self.pump_id = pump_id
        self.driver = Driver()
        self.prefix = 'NIH:SYRINGE' + str(pump_id)
        if pump_id is not None:
            self.driver.init(pump_id)
        self.startup()


    def abort(self):
        """orderly abort of the current operation"""
        from pyCA.CAServer import casput
        self.driver.abort()
        while self.ismoving:
            sleep(0.1)
        casput(prefix+".STOP",value = 0)
        casput(prefix+".VAL",value = self.position)


    def close(self):
        """orderly close\shutdown"""
        raise NotImplementedError

    def help(self):
        """returns help  information in a string format."""
        raise NotImplementedError

    def snapshot(self):
        """returns snapshot of current PVs and their values in a dictionary format"""
        raise NotImplementedError

    def start(self):
        """starts a separate thread"""
        from thread import start_new_thread
        start_new_thread(self.run,())

    def stop(self):
        """stop a separate thread"""
        self.running = False
        self.driver.close()

    def run_once(self):
        """"""
        if len(self.command_queue) == 0:
            self.get_position()
        else:
            try:
                exec(self.command_queue[0][0]+'('+str(self.command_queue[0][1])+')')
                self.command_queue.pop(0)
            except:
                error(traceback.format_exc())

    def run(self):
        """"""
        self.running = True
        while self.running:
            self.run_once()

    def IOC_run(self):
        """"""
        raise NotImplementedError


    def startup(self):
        from pyCA.CAServer import casput, casmonitor
        prefix = self.prefix
        casput(prefix+".DESC",value = self.description, update = False)
        casput(prefix+".EGU",value = "uL")
        casput(prefix+".RBV",value = self.position)

        casput(prefix+".VAL",value = self.cmd_position)
        casput(prefix+".VELO",value = self.speed)

        #Command_button PVs

        casput(prefix+".STOP",value = 0)
        casmonitor(prefix+".STOP",callback=self.command_monitor)


        casmonitor(prefix+".VAL",callback=self.monitor)
        casmonitor(prefix+".VELO",callback=self.monitor)


        from auxiliary.circular_buffer_LL import CBServer as Server
        self.buffers = {}
        self.buffers['position'] = Server(size = (2,1*3600*2) , var_type = 'float64')

    def monitor(self,PV_name,value,char_value):
        """Process PV change requests"""
        from pyCA.CAServer import casput
        info("monitor: %s = %r" % (PV_name,value))
        if PV_name == self.prefix+".VAL":
            self.set_cmd_position(value)
        if PV_name == self.prefix+".VELO":
            self.set_speed(value)

    def command_monitor(self,PV_name,value,char_value):
        """Process PV change requests"""
        from pyCA.CAServer import casput
        info("monitor: %s = %r" % (PV_name,value))
        if PV_name == self.prefix+".STOP":
            self.abort()


    def cleanup(self):
        from pyCA.CAServer import casdel

####################################################################################################
### device specific functions
####################################################################################################


    def get_position(self):
        """
        get position of the pump
        """
        from pyCA.CAServer import casput
        position = self.driver.position
        casput(self.prefix+".ERR",value = self.error_code, update = False, )
        casput(self.prefix+".DMOV",value = self.isdonemoving, update = False)
        casput(self.prefix+".MOVN",value = self.ismoving, update = False)
        casput(self.prefix+".RBV",value = position, update = False)
        return position
    def set_position(self, value):
        response = self.move_abs(position = value,speed = self.VELO)
    position = property(get_position,set_position)



    def get_cmd_position(self):
        """
        get position of the pump
        """
        return self.driver.cmd_position
    def set_cmd_position(self,value):
        from pyCA.CAServer import casput
        #casput(self.prefix+".VAL",value = self.position)
        self.move_abs(position = value)
        value = self.driver.cmd_position
        casput(self.prefix+".VAL", value)
    cmd_position = property(get_cmd_position, set_cmd_position)

    def get_speed(self):
        """
        get position of the pump
        """
        speed = self.driver.get_speed()
        return speed
    def set_speed(self,value):
        """
        get position of the pump
        """
        from pyCA.CAServer import casput
        self.driver.set_speed(value)
        speed = self.driver.get_speed()
        casput(self.prefix+".VELO", speed)
    speed = property(get_speed,set_speed)



    @property
    def isbusy(self):
        response = self.driver.busy
        return response

    @property
    def isdonemoving(self):
        response = not self.driver.busy
        return response
    @property
    def ismoving(self):
        response = self.driver.busy
        return response

    @property
    def error_code(self):
        response = self.driver.error_code
        return response

    def move_abs(self,position = 0, speed = None):
        #self.driver.abort()
        if speed is None:
            speed = self.speed
        response = self.driver.move_abs(position = position, speed = speed)
        return response

    def get_valve(self):
        return self.driver.valve
    def set_valve(self,value):
        self.driver.valve = value
    valve = property(get_valve,set_valve)

def init():
    global pumps,pump1,pump2,pump3,pump4
    pumps = {}
    pumps[1] = pump1 = CavroCentrisSyringePump();pump1.init(1);
    pumps[2] = pump2 = CavroCentrisSyringePump();pump2.init(2);
    pumps[3] = pump3 = CavroCentrisSyringePump();pump3.init(3);
    pumps[4] = pump4 = CavroCentrisSyringePump();pump4.init(4);

    sleep(2)

    for pump in pumps.values(): pump.start()
    return pumps

if __name__ == "__main__": #for testing
    from tempfile import gettempdir
    import logging
    logging.basicConfig(filename=gettempdir()+'/syringe_pump_DL.log',
                        level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

    pumps = init()
