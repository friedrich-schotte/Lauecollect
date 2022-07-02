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
        self.position = 0.0
        self.velocity = 0.0
        self.dpos = 0.002

        self.low_level_limit_alarm = 5.0
        self.low_level_limit_warning = 10.0
        self.running = 0

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
        from threading import RLock as Lock
        self.lock = Lock()
        from devices.Cavro_Centris_Pump import Driver
        self.pump_id = pump_id
        self.driver = Driver()
        self.prefix = 'NIH:SYRINGE' + str(pump_id)
        if pump_id is not None:
            self.driver.init(pump_id)
        self.startup()


    def abort(self):
        """orderly abort of the current operation"""
        from CAServer import casput
        with self.lock:
            self.set_status('aborting...')
            self.driver.abort()
            prefix = self.prefix
            while self.isbusy:
                sleep(0.1)
            casput(prefix+".cmd_ABORT",value = 0)
            casput(prefix+".VAL",value = self.position)
            self.set_status('')

    def close(self):
        """orderly close\shutdown"""
        self.stop()
        self.abort()
        self.driver.close()

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
        from CAServer import casput
        self.running = False
        casput(self.prefix+".RUNNING",value = self.running, update = False)


    def run_once(self):
        """"""
        from CAServer import casput
        self.get_position()
        casput(self.prefix+".DMOV",value = self.isdonemoving, update = False)
        casput(self.prefix+".MOVN",value = self.ismoving, update = False)
        casput(self.prefix+".RBV",value = self.position, update = False)

        casput(self.prefix+".ERR",value = self.error_code, update = False)
        casput(self.prefix+".ALARM",value = self.get_alarm(), update = False)
        casput(self.prefix+".WARN",value = self.get_warning(), update = False)


    def run(self):
        """"""
        from CAServer import casput
        self.running = True
        casput(self.prefix+".RUNNING",value = self.running, update = False)

        while self.running:
            self.run_once()
        self.running = False
        casput(self.prefix+".RUNNING",value = self.running, update = False)


    def IOC_run(self):
        """"""
        raise NotImplementedError




    def startup(self):
        from CAServer import casput, casmonitor, PV_names
        prefix = self.prefix

        #Indicator PVs
        casput(prefix+".DESC",value = self.description, update = False)
        casput(prefix+".EGU",value = "uL")
        casput(prefix+".ALARM",value = '')
        casput(prefix+".ERR",value = '')
        casput(prefix+".WARN",value = '')
        casput(prefix+".LLIM_ALARM",value = self.low_level_limit_alarm)
        casput(prefix+".LLIM_WARN",value = self.low_level_limit_warning)
        casput(prefix+".RUNNING",value = self.running, update = False)
        casput(prefix+".RBV",value = self.position)
        casput(prefix+".LIST_ALL_PVS", value = self.list_all_pvs())

        #Control PVs
        casput(prefix+".cmd_ABORT",value = 0)
        casmonitor(prefix+".cmd_ABORT",callback=self.command_monitor)
        casput(prefix+".cmd_HOME",value = 0)
        casmonitor(prefix+".cmd_HOME",callback=self.command_monitor)

        casput(prefix+".VAL",value = self.cmd_position)
        casmonitor(prefix+".VAL",callback=self.monitor)


        casput(prefix+".VELO",value = self.speed)
        casmonitor(prefix+".VELO", callback=self.monitor)

        casput(prefix+".VALVE",value = self.valve)
        casmonitor(prefix+".VALVE", callback=self.monitor)

        from auxiliary.circular_buffer_LL import CBServer as Server
        self.buffers = {}
        self.buffers['position'] = Server(size = (2,1*3600*2) , var_type = 'float64')

    def monitor(self,PV_name,value,char_value):
        """Process PV change requests"""
        from CAServer import casput
        info("monitor: %s = %r" % (PV_name,value))
        if PV_name == self.prefix + ".VAL":
            self.set_cmd_position(value)
        if PV_name == self.prefix + ".VELO":
            self.set_speed(value)
        if PV_name == self.prefix + ".VALVE":
            self.set_valve(value)

    def command_monitor(self,PV_name,value,char_value):
        """Process PV change requests"""
        from CAServer import casput
        info("command_monitor: %s = %r" % (PV_name,value))
        if PV_name == self.prefix+".cmd_ABORT":
            self.abort()
        if PV_name == self.prefix+".cmd_HOME":
            self.home()



    def cleanup(self):
        from CAServer import casdel

    def list_all_pvs(self):
        from CAServer import PVs
        result = list(PVs.keys())
        return result


####################################################################################################
### device specific functions
####################################################################################################
    def home(self):
        with self.lock:
            self.set_status('homing...')
            if value == 1:
                self.driver.home()
            casput(prefix+".cmd_HOME",value = 0)
            casput(prefix+".VELOCITY",value = self.cmd_position)
            casput(prefix+".VAL",value = self.speed)
            self.set_status('homing complete')

    def get_position(self):
        """
        get position of the pump
        """
        from CAServer import casput
        with self.lock:
            position = self.driver.position
            self.position = position
        return position
    def set_position(self, value):
        with lock:
            self.set_cmd_position(value)



    def get_cmd_position(self):
        """
        get position of the pump
        """
        return self.driver.cmd_position
    def set_cmd_position(self,value):
        from CAServer import casput
        self.move_abs(position = value, speed = self.speed)
        value = self.driver.cmd_position
        casput(self.prefix+".VAL", value, update = False)
    cmd_position = property(get_cmd_position, set_cmd_position)

    def get_speed(self):
        """
        get position of the pump
        """
        speed = self.driver.get_speed()
        return speed
    def set_speed(self,value):
        """
        set speed of the pump
        """
        from CAServer import casput
        self.driver.set_speed(value)
        speed = self.driver.get_speed()
        casput(self.prefix+".VELO", speed, update = False)
    speed = property(get_speed,set_speed)

    def set_status(self, value = ''):
        from CAServer import casput
        value = str(value)
        casput(self.prefix + '.STATUS', value, update = False)
        self.status = value

    @property
    def isbusy(self):
        response = self.driver.busy
        return response

    @property
    def isdonemoving(self):
        """
        return flag if motion is complete. It will compare the cmd_position and actual position
        """
        flag = abs(self.cmd_position - self.position) < self.dpos
        return flag

    @property
    def ismoving(self):
        response = self.driver.busy
        return response

    @property
    def error_code(self):
        response = self.driver.error_code
        return response

    def move_abs(self,position = 0, speed = None):
        self.driver.abort()
        if speed is None:
            speed = self.speed
        response = self.driver.move_abs(position = position, speed = speed)
        return response

    def get_valve(self):
        return self.driver.valve
    def set_valve(self,value):
        from CAServer import casput
        self.driver.valve = value
        casput(self.prefix+".VALVE", value)
    valve = property(get_valve,set_valve)

    def get_alarm(self):
        """
        returns integer if alarm conditions are met
        """
        if self.position <= self.low_level_limit_alarm:
            string = 'current position {} below low level limit {}'.format(self.position, self.low_level_limit_alarm)
        else:
            string = ''
        return string

    def get_warning(self):
        """
        returns integer if alarm conditions are met
        """
        if self.position <= self.low_level_limit_warning:
            flag = 'current position {} below low level limit {}'.format(self.position, self.low_level_limit_warning)
        else:
            flag = ''
        return flag

class SyringeTower_DL(object):
    def __init__(self):
        self.name = 'syringe_tower'
        self.prefix = 'NIH:SYRINGE_TOWER'
        self.description = 'description of this server'

    def init(self):
        self.pumps = {}
        self.pumps[1] = self.pump1 = CavroCentrisSyringePump();
        self.pump1.init(1)
        self.pumps[2] = self.pump2 = CavroCentrisSyringePump();
        self.pump2.init(2);
        self.pumps[3] = self.pump3 = CavroCentrisSyringePump();
        self.pump3.init(3);
        self.pumps[4] = self.pump4 = CavroCentrisSyringePump();
        self.pump4.init(4);

        self.startup()

        sleep(2)

    def start(self):
        for self.pump in self.pumps.values(): self.pump.start()

    def stop(self):
        for self.pump in self.pumps.values(): self.pump.stop()

    def close(self):
        for self.pump in self.pumps.values(): self.pump.close()

    def run(self):
        self.init()
        self.start()
        while True:
            sleep(1)


    def startup(self):
        from CAServer import casput, casmonitor, PV_names
        prefix = self.prefix

        #Indicator PVs
        casput(prefix+".DESC",value = self.description, update = False)

        #Control PV

        casput(prefix+".cmd_PRIME",value = 0)
        casmonitor(prefix+".cmd_PRIME", callback=self.command_monitor)

    def command_monitor(self,PV_name,value,char_value):
        """Process PV change requests"""
        from CAServer import casput
        info("command_monitor: %s = %r" % (PV_name,value))
        if PV_name == self.prefix+".cmd_PRIME":
            self.prime(pump_id = value)



    #######
    def create_low_pressure(self):
        """
        """
        raise NotImplementedError

    def prime(self,pump_id = 2):
        """
        """
        from thread import start_new_thread
        info('prime command is executed for pump {}'.format(pump_id))
        start_new_thread(self.prime_local,(pump_id,))

    def prime_local(self,pump_id):
        from CAServer import casput
        pump = self.pumps[pump_id]
        pump.velocity = 75.0
        pump.valve = 'i'
        for i in range(5):
            pump.cmd_position = 0.0;
            sleep(0.34)
            while not pump.isdonemoving:
                sleep(0.34)
            pump.cmd_position = 250.0
            sleep(0.34)
            while not pump.isdonemoving:
                sleep(0.34)
        pump.velocity = 25.0
        pump.valve = 'o'
        casput(self.prefix+".cmd_PRIME",value = 0)


tower = SyringeTower_DL()

if __name__ == "__main__": #for testing
    from tempfile import gettempdir
    import logging
    logging.basicConfig(filename=gettempdir()+'/syringe_pump_DL.log',
                        level=logging.DEBUG, format="%(asctime)s %(levelname)s: %(message)s")


    #tower.init()
    #tower.start()
