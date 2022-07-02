#!/usr/bin/python
# -*- coding: utf-8 -*-


"""
Cavro Centris Syringe pump device/IOC module
author: Valentyn Stadnytskyi
Created: May 28 2019
Last modified: May 28 2019
"""

__version__ = '0.0.0'

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

class SyringeTower_SL(object):

    def __init__(self):
        self.prefix = 'NIH:SYRINGE_TOWER'
        self.name = 'syringe_tower'


    def init(self):
        raise NotImplementedError

    def start(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError

    def run(self):
        raise NotImplementedError

tower = SyringeTower_SL()

if __name__ == "__main__": #for testing
    from tempfile import gettempdir
    import logging
    logging.basicConfig(filename=gettempdir()+'/syringe_pump_DL.log',
                        level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
