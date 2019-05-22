#!/usr/bin/env python
"""EPICS server for ILX Lightwave LDT-5948 Precision Temperature Controller
Author: Friedrich Schotte
Date created: 2015-11-03
Date last modified: 2017-06-25
"""
__version__ = "4.7" # renamed: lightwave_temperature_controller

from lightwave_temperature_controller_driver import lightwave_temperature_controller
from persistent_property import persistent_property
from CAServer import casput,casget,casmonitor,casdel
from time import time
from logging import debug,info,warn,error
from thread import start_new_thread
from numpy import isfinite, nan
import platform
computer_name = platform.node()
import os

class Lightwave_Temperature_Controller_IOC(object):
    name = "lightwave_temperature_controller_IOC"
    prefix = persistent_property("prefix","NIH:LIGHTWAVE")
    scan_time = persistent_property("scan_time",0.5)
    running = False
    prefix = 'NIH:LIGHTWAVE'
    def get_EPICS_enabled(self):
        return self.running
    def set_EPICS_enabled(self,value):
        if value:
            if not self.running: start_new_thread(self.run,())
        else: self.running = False
    EPICS_enabled = property(get_EPICS_enabled,set_EPICS_enabled)

    def start(self):
        """Start EPICS IOC for temperature controller in background"""
        from thread import start_new_thread
        start_new_thread(self.run,())

    def stop(self):
        """Stop EPICS IOC for temperature controller runninig in background"""
        self.running = False

    def run(self):
        """Start EPICS IOC for temperature controller (does not return)"""
        self.running = True
        casput(self.prefix+".SCAN",self.scan_time)
        casput(self.prefix+".DESC","Temp")
        casput(self.prefix+".EGU","C")
        casput(self.prefix+".BAUD",lightwave_temperature_controller.baudrate.value)
        # Complex Actions
        casput(self.prefix+".ACTION",'')
        # Monitor client-writable PVs.
        casmonitor(self.prefix+".SCAN",callback=self.monitor)
        casmonitor(self.prefix+".BAUD",callback=self.monitor)
        casmonitor(self.prefix+".VAL" ,callback=self.monitor)
        casmonitor(self.prefix+".CNEN",callback=self.monitor)
        casmonitor(self.prefix+".PIDCOF",callback=self.monitor)
        casmonitor(self.prefix+".PCOF",callback=self.monitor)
        casmonitor(self.prefix+".ICOF",callback=self.monitor)
        casmonitor(self.prefix+".DCOF",callback=self.monitor)
        casmonitor(self.prefix+".RDBD",callback=self.monitor)
        casmonitor(self.prefix+".NSAM",callback=self.monitor)
        casmonitor(self.prefix+".IHLM",callback=self.monitor)
        casmonitor(self.prefix+".ILLM",callback=self.monitor)
        casmonitor(self.prefix+".TENA",callback=self.monitor)
        casmonitor(self.prefix+".P1SP",callback=self.monitor)
        casmonitor(self.prefix+".P1EP",callback=self.monitor)
        casmonitor(self.prefix+".P1SI",callback=self.monitor)
        while self.running:
            if self.scan_time > 0 and isfinite(self.scan_time):

                if lightwave_temperature_controller.max_time_between_replies > 10:
                    lightwave_temperature_controller.max_time_between_replies = 0
                    info("Reading configuration")
                    casput(self.prefix+".COMM",lightwave_temperature_controller.port_name, update = False)
                    #casput(self.prefix+".VAL",lightwave_temperature_controller.setT.value)
                    casput(self.prefix+".CNEN",lightwave_temperature_controller.enabled.value, update = False)
                    casput(self.prefix+".PIDCOF",lightwave_temperature_controller.feedback_loop.PID, update = False)
                    casput(self.prefix+".PCOF",lightwave_temperature_controller.feedback_loop.P.value, update = False)
                    casput(self.prefix+".ICOF",lightwave_temperature_controller.feedback_loop.I.value, update = False)
                    casput(self.prefix+".DCOF",lightwave_temperature_controller.feedback_loop.D.value, update = False)
                    casput(self.prefix+".RDBD",lightwave_temperature_controller.stabilization_threshold, update = False)
                    casput(self.prefix+".NSAM",lightwave_temperature_controller.stabilization_nsamples, update = False)
                    casput(self.prefix+".IHLM",lightwave_temperature_controller.current_high_limit, update = False)
                    casput(self.prefix+".ILLM",lightwave_temperature_controller.current_low_limit, update = False)
                    casput(self.prefix+".TENA",lightwave_temperature_controller.trigger_enabled, update = False)
                    casput(self.prefix+".ID",lightwave_temperature_controller.id, update = False)
                    casput(self.prefix+".P1SP",lightwave_temperature_controller.trigger_start, update = False)
                    casput(self.prefix+".P1EP",lightwave_temperature_controller.trigger_stop, update = False)
                    casput(self.prefix+".P1SI",lightwave_temperature_controller.trigger_stepsize, update = False)
                    casput(self.prefix+".processID",value = os.getpid(), update = False)
                    casput(self.prefix+".computer_name",value = computer_name, update = False)
                t = time()
                casput(self.prefix+".RBV",lightwave_temperature_controller.actual_temperature.value, update = True)
                casput(self.prefix+".DMOV",lightwave_temperature_controller.stable, update = False)
                sleep(t+0.25*self.scan_time-time())
                casput(self.prefix+".I",lightwave_temperature_controller.current.value, update = True)
                sleep(t+0.50*self.scan_time-time())
                casput(self.prefix+".P",lightwave_temperature_controller.power.value, update = True)
                sleep(t+0.75*self.scan_time-time())
                ##if casget(self.prefix+".TENA"): # Set point may change on trigger.
                casput(self.prefix+".VAL",lightwave_temperature_controller.setT.value, update = False)
                sleep(t+1.00*self.scan_time-time())
                casput(self.prefix+".SCANT",time()-t, update = False) # post actual scan time for diagnostics
            else:
                casput(self.prefix+".SCANT",nan, update = False)
                sleep(0.1)
        casdel(self.prefix)

    def monitor(self,PV_name,value,char_value):
        """callback for PV change requests"""
        debug("%s = %r" % (PV_name,value))
        if PV_name == self.prefix+".SCAN":
            self.scan_time = value
            casput(self.prefix+".SCAN",self.scan_time)
        if PV_name == self.prefix+".BAUD":
            lightwave_temperature_controller.baudrate.value = value
            casput(self.prefix+".BAUD",lightwave_temperature_controller.baudrate.value)
        if PV_name == self.prefix+".VAL":
            lightwave_temperature_controller.setT.value = value
            #recalculate if motor is moving or not. This should allow to use cawait function
            casput(self.prefix+".DMOV",lightwave_temperature_controller.stable, update = False)
            #update PV:
            casput(self.prefix+".VAL",lightwave_temperature_controller.setT.value)
        if PV_name == self.prefix+".CNEN":
            lightwave_temperature_controller.enabled.value = value
            casput(self.prefix+".CNEN",lightwave_temperature_controller.enabled.value)
        if PV_name == self.prefix+".PIDCOF":
            lightwave_temperature_controller.feedback_loop.PID = value
            casput(self.prefix+".PIDCOF",lightwave_temperature_controller.feedback_loop.PID)
            casput(self.prefix+".PCOF",lightwave_temperature_controller.feedback_loop.PID[0])
            casput(self.prefix+".ICOF",lightwave_temperature_controller.feedback_loop.PID[1])
            casput(self.prefix+".DCOF",lightwave_temperature_controller.feedback_loop.PID[2])
        if PV_name == self.prefix+".PCOF":
            lightwave_temperature_controller.feedback_loop.P.value = value
            casput(self.prefix+".PCOF",lightwave_temperature_controller.feedback_loop.P.value)
        if PV_name == self.prefix+".ICOF":
            lightwave_temperature_controller.feedback_loop.I.value = value
            casput(self.prefix+".ICOF",lightwave_temperature_controller.feedback_loop.I.value)
        if PV_name == self.prefix+".DCOF":
            lightwave_temperature_controller.feedback_loop.D.value = value
            casput(self.prefix+".DCOF",lightwave_temperature_controller.feedback_loop.D.value)
        if PV_name == self.prefix+".COMM":
            lightwave_temperature_controller.port_name.value = value
            casput(self.prefix+".COMM",lightwave_temperature_controller.port_name)
        if PV_name == self.prefix+".RDBD":
            lightwave_temperature_controller.stabilization_threshold = value
            casput(self.prefix+".RDBD",lightwave_temperature_controller.stabilization_threshold)
        if PV_name == self.prefix+".NSAM":
            lightwave_temperature_controller.stabilization_nsamples = value
            casput(self.prefix+".NSAM",lightwave_temperature_controller.stabilization_nsamples)
        if PV_name == self.prefix+".IHLM":
            lightwave_temperature_controller.current_high_limit = value
            casput(self.prefix+".IHLM",lightwave_temperature_controller.current_high_limit)
        if PV_name == self.prefix+".ILLM":
            lightwave_temperature_controller.current_low_limit = value
            casput(self.prefix+".ILLM",lightwave_temperature_controller.current_low_limit)
        if PV_name == self.prefix+".TENA":
            lightwave_temperature_controller.trigger_enabled = value
            casput(self.prefix+".TENA",lightwave_temperature_controller.trigger_enabled)
        if PV_name == self.prefix+".P1SP":
            lightwave_temperature_controller.trigger_start = value
            casput(self.prefix+".P1SP",lightwave_temperature_controller.trigger_start)
        if PV_name == self.prefix+".P1EP":
            lightwave_temperature_controller.trigger_stop = value
            casput(self.prefix+".P1EP",lightwave_temperature_controller.trigger_stop)
        if PV_name == self.prefix+".P1SI":
            lightwave_temperature_controller.trigger_stepsize = value
            casput(self.prefix+".P1SI",lightwave_temperature_controller.trigger_stepsize)

lightwave_temperature_controller_IOC = Lightwave_Temperature_Controller_IOC()

def sleep(seconds):
    """Delay execution by the given number of seconds"""
    # This version of "sleep" does not throw an excpetion if passed a negative
    # waiting time, but instead returns immediately.
    from time import sleep
    if seconds > 0: sleep(seconds)

if __name__ == "__main__":
    from pdb import pm
    self = lightwave_temperature_controller # for debugging
    import logging;
    logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s")
    import CAServer
    ##CAServer.LOG = True; CAServer.verbose = True
    lightwave_temperature_controller.logging = True
    from sys import argv
    if "run_IOC" in argv: lightwave_temperature_controller_IOC.run()

    print('lightwave_temperature_controller_IOC.prefix = %r' % lightwave_temperature_controller_IOC.prefix)
    print('lightwave_temperature_controller_IOC.EPICS_enabled = True')
    print('lightwave_temperature_controller_IOC.EPICS_enabled = False')
    print('lightwave_temperature_controller_IOC.run()')
    print('lightwave_temperature_controller_IOC.start()')
    print('lightwave_temperature_controller_IOC.stop()')
