#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Cavro Centris Syringe pump device/IOC module

Authors: Valentyn Stadnytskyi, Friedrich Schotte
Created: 2019-05-28
Last modified: 2020-06-10

Revision history:
1.0: Friedrich: backward compatibility with existing “Laue_Crystallography” module:
     - Added "value" and "command_value"
     - Return floating point properties should be nan (not None) if device is offline
     - Return Boolean properties should be False (not None) if device is offline
1.0.3: Friedrich: Fixed issue: ImportError: cannot import name 'clock' from 'time'
"""

__version__ = "1.0.3" 

import traceback
import psutil, os
import platform #https://stackoverflow.com/questions/110362/how-can-i-find-the-current-os-in-python
p = psutil.Process(os.getpid()) #source: https://psutil.readthedocs.io/en/release-2.2.1/


from numpy import nan, mean, std, asfarray, asarray, hstack, array, concatenate, delete, round, vstack, hstack, zeros, transpose, split, unique, nonzero, take, savetxt, min, max
from time import time, sleep
import sys
import os.path
import struct
from pdb import pm
from time import gmtime, strftime, time
from logging import debug,info,warning,error
from _thread import start_new_thread



from struct import pack, unpack
from timeit import Timer, timeit

from threading import Thread, Event, Timer, Condition

class Syring_Pump_DL_Client(object):
    def __init__(self, pump_id):
        self.pump_id = pump_id
        self.prefix = "NIH:SYRINGE" + str(pump_id)

    def init(self):
        from CA import camonitor
        camonitor(self.prefix + '.VELO', callback = self._callback)
        #raise NotImplementedError

    def _callback(self, PV_name, value,char_val,timestamp):
        print("PV_name = %r, value = %r, and timestamp = %r"  % (PV_name,value,timestamp))
        pass

    @property
    def position(self):
        from CA import caget
        pos = caget(self.prefix+'.RBV')
        if pos is None: pos = nan
        return pos
    
    value = position

    def get_speed(self):
        from CA import caget
        velo = caget(self.prefix+'.VELO')
        if velo is None: velo = nan
        return velo
    def set_speed(self,velo):
        from CA import caput
        caput(self.prefix+'.VELO',velo, wait = True)
    speed = property(get_speed,set_speed)

    def get_cmd_position(self):
        from CA import caget
        cmd_pos = caget(self.prefix+'.VAL')
        if cmd_pos is None: cmd_pos = nan
        return cmd_pos
    def set_cmd_position(self,value):
        from CA import caput, cawait
        caput(self.prefix+'.VAL',value, wait = True)
    cmd_position = property(get_cmd_position,set_cmd_position)

    command_value = cmd_position

    def get_cmd(self):
        from CA import caget
        from pickle import loads as load_string
        in_cmd = load_string(caget(self.prefix+'.CMD'))
        return in_cmd
    def set_cmd_abort(self,value = None):
        from CA import caput, cawait
        from pickle import dumps as dump_string
        out_cmd = dump_string({'abort':{}})
        caput(self.prefix+'.CMD',out_cmd, wait = True)
    def set_cmd_prime(self,value = 1):
        from CA import caput, cawait
        from pickle import dumps as dump_string
        out_cmd = dump_string({'prime':{'N':value}})
        caput(self.prefix+'.CMD',out_cmd, wait = True)
    def set_cmd_fill(self,value = None):
        from CA import caput, cawait
        from pickle import dumps as dump_string
        out_cmd = dump_string({'fill':{}})
        caput(self.prefix+'.CMD',out_cmd, wait = True)
    def set_cmd_empty(self,value = None):
        from CA import caput, cawait
        from pickle import dumps as dump_string
        out_cmd = dump_string({'empty':{}})
        caput(self.prefix+'.CMD',out_cmd, wait = True)
    def set_cmd_flow(self,position = 0, speed = 0.1):
        from CA import caput, cawait
        from pickle import dumps as dump_string
        out_cmd = dump_string({'flow':{'position':position,'speed':speed}})
        caput(self.prefix+'.CMD',out_cmd, wait = True)

    @property
    def error(self):
        from CA import caget
        error = caget(self.prefix+'.ERROR')
        return error

    @property
    def error_code(self):
        from CA import caget
        error = caget(self.prefix+'.ERROR_CODE')
        return error

    @property
    def donemoving(self):
        from CA import caget
        donemoving = caget(self.prefix+'.DMOV')
        return donemoving

    @property
    def moving(self):
        from CA import caget
        moving = caget(self.prefix+'.MOVN')
        if moving is None: moving = False
        return moving

    @property
    def alarm(self):
        from CA import caget
        alarm = caget(self.prefix+'.LLIM_ALARM')
        return alarm

    @property
    def warn(self):
        from CA import caget
        warn = caget(self.prefix+'.LLIM_WARN')
        return warn

    def status(self):
        from CA import caget
        var = caget(self.prefix+'.STATUS')
        return var

    def get_valve(self):
        from CA import caget
        valve = caget(self.prefix+'.VALVE')
        return valve
    def set_valve(self,value):
        from CA import caput
        allowed_valve = 'oib'
        if value in allowed_valve:
            caput(self.prefix+'.VALVE',value, wait = True)
    valve = property(get_valve,set_valve)



class SyringeTower_DL_client(object):
    def __init__(self):
        self.name = 'syringe_tower'


tower_DL_client = SyringeTower_DL_client()
pump_motherliquor = Syring_Pump_DL_Client(pump_id = 1)
pump_waste = Syring_Pump_DL_Client(pump_id = 2)
pump_xtals = Syring_Pump_DL_Client(pump_id = 3)
pump_aux = Syring_Pump_DL_Client(pump_id = 4)

if __name__ == "__main__": #for testing
    from tempfile import gettempdir
    import logging
    logging.basicConfig(filename=gettempdir()+'/syringe_pump_DL_client.log',
                        level=logging.DEBUG, format="%(asctime)s %(levelname)s: %(message)s")
