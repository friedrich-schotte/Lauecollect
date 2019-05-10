#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Author: Philip Anfinrud, Brian Mahon, Friedrich Schotte
Date created: 12/8/2016
Date last modified: 10/17/2017

2017-06-02 1.5 Adapted for 3-way injection port
2017-10-06 1.6 Friedrich, Using IOC
2017-10-17 1.7 Brian, Friedrich, refill_1, refill_3

Setup:
Start desktop shortcut "Centris Syringe IOC"
(Target: python cavro_centris_syringe_pump_IOC.py run_IOC
Start in: %LAUECOLLECT%)
"""
__version__ = "1.0"

from time import sleep,time
from logging import debug,info,warn,error
from thread import start_new_thread
from pdb import pm
from tempfile import gettempdir
# Assign default parameters.

class Cavro_centris_syringe_pump_SL(object):
    """Cavro Centris Syringe Pumps"""
    def start_DL(self):
        pass
    
        
    
                          

    
if __name__ == "__main__":
    import logging; logging.basicConfig(filename=gettempdir()+'/suringe_pump_SL.log', level=logging.DEBUG, format="%(asctime)s %(levelname)s: %(message)s")
    server = Cavro_centris_syringe_pump_SL()


    
    # p.write_read({4:"/1?20R\r"}) # query valve position
    # p.write_read({1: "/1IR\r"}) # Move pump1 valve to Input
    # p.write_read({2: "/1V0.3,1F\r"}) # Change speed to 0.3 uL/s
    # sum(p.positions().values()[:2])  # Returns sum of first two values
