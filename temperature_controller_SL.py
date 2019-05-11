#!/usr/bin/env python
"""Sub System Level with integrated EPICS server for ILX Lightwave LDT-5948 Precision Temperature Controller
Original EPICS code Friedrich Shotte, Nov 3, 2015 - Jul 25, 2017
Valentyn Stadnytskyi, Feb 12, 2018
"""
__version__ = "4.6.1" # high limit/low limit swapped when reading configuration

#from temperature_controller_driver import temperature_controller
from persistent_property import persistent_property
from CAServer import casput,casget,casmonitor,casdel
from time import time
#from logging import debug,info,warn,error
from thread import start_new_thread
from numpy import isfinite,nan

class Temperature_Controller_SL(object):
    name = "temperature_controller_SL"
    prefix = persistent_property("prefix","NIH:TEMP")
    scan_time = persistent_property("scan_time",0.5)
    running = False

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
        casput(self.prefix+".BAUD",temperature_controller.baudrate)
        # Monitor client-writable PVs.
        casmonitor(self.prefix+".SCAN",callback=self.monitor)
        casmonitor(self.prefix+".BAUD",callback=self.monitor)
        casmonitor(self.prefix+".VAL" ,callback=self.monitor)
        casmonitor(self.prefix+".CNEN",callback=self.monitor)
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
            #print('1 time: %r' % time())
            if self.scan_time > 0 and isfinite(self.scan_time):
                #print('2 time: %r' % time())
                if temperature_controller.max_time_between_replies > 3:
                    #print('3 time: %r' % time())
                    temperature_controller.max_time_between_replies = 0
                    #info("Reading configuration")
                    casput(self.prefix+".COMM",temperature_controller.port_name)
                    casput(self.prefix+".VAL",temperature_controller.setT.value)
                    casput(self.prefix+".CNEN",temperature_controller.enabled)
                    casput(self.prefix+".PCOF",temperature_controller.feedback_loop_P)
                    casput(self.prefix+".ICOF",temperature_controller.feedback_loop_I)
                    casput(self.prefix+".DCOF",temperature_controller.feedback_loop_D)
                    casput(self.prefix+".RDBD",temperature_controller.stabilization_threshold)
                    casput(self.prefix+".NSAM",temperature_controller.stabilization_nsamples)
                    casput(self.prefix+".IHLM",temperature_controller.current_high_limit)
                    casput(self.prefix+".ILLM",temperature_controller.current_low_limit)
                    casput(self.prefix+".TENA",temperature_controller.trigger_enabled)
                    casput(self.prefix+".ID",temperature_controller.id)
                    casput(self.prefix+".P1SP",temperature_controller.trigger_start)
                    casput(self.prefix+".P1EP",temperature_controller.trigger_stop)
                    casput(self.prefix+".P1SI",temperature_controller.trigger_stepsize)
                temperature_controller.max_time_between_replies += 1    
                t = time()
                casput(self.prefix+".RBV",temperature_controller.actual_temperature)
                casput(self.prefix+".DMOV",temperature_controller.stable)
                sleep(t+0.25*self.scan_time-time())
                casput(self.prefix+".I",temperature_controller.current)
                sleep(t+0.50*self.scan_time-time())
                casput(self.prefix+".P",temperature_controller.power)
                sleep(t+0.75*self.scan_time-time())
                ##if casget(self.prefix+".TENA"): # Set point may change on trigger.
                casput(self.prefix+".VAL",temperature_controller.setT.value)
                sleep(t+1.00*self.scan_time-time())
                casput(self.prefix+".SCANT",time()-t) # post actual scan time for diagnostics
            else:
                casput(self.prefix+".SCANT",nan)
                sleep(0.1)
        casdel(self.prefix)

    def monitor(self,PV_name,value,char_value):
        """callback for PV change requests"""
        #debug("%s = %r" % (PV_name,value))
        if PV_name == self.prefix+".SCAN":
            self.scan_time = value
            casput(self.prefix+".SCAN",self.scan_time)
        if PV_name == self.prefix+".BAUD":
            temperature_controller.baudrate = value
            casput(self.prefix+".BAUD",temperature_controller.baudrate)
        if PV_name == self.prefix+".VAL":
            temperature_controller.setT.value = value
            casput(self.prefix+".VAL",temperature_controller.setT.value )
        if PV_name == self.prefix+".CNEN":
            temperature_controller.enabled = value
            casput(self.prefix+".CNEN",temperature_controller.enabled)
        if PV_name == self.prefix+".PCOF":
            temperature_controller.feedback_loop_P = value
            casput(self.prefix+".PCOF",temperature_controller.feedback_loop_P)
        if PV_name == self.prefix+".ICOF":
            temperature_controller.feedback_loop_I = value
            casput(self.prefix+".ICOF",temperature_controller.feedback_loop_I)
        if PV_name == self.prefix+".DCOF":
            temperature_controller.feedback_loop_D = value
            casput(self.prefix+".DCOF",temperature_controller.feedback_loop_D)
        if PV_name == self.prefix+".COMM":
            temperature_controller.port_name = value
            casput(self.prefix+".COMM",temperature_controller.port_name)
        if PV_name == self.prefix+".RDBD":
            temperature_controller.stabilization_threshold = value
            casput(self.prefix+".RDBD",temperature_controller.stabilization_threshold)
        if PV_name == self.prefix+".NSAM":
            temperature_controller.stabilization_nsamples = value
            casput(self.prefix+".NSAM",temperature_controller.stabilization_nsamples)            
        if PV_name == self.prefix+".IHLM":
            temperature_controller.current_high_limit = value
            casput(self.prefix+".IHLM",temperature_controller.current_high_limit)
        if PV_name == self.prefix+".ILLM":
            temperature_controller.current_low_limit = value
            casput(self.prefix+".ILLM",temperature_controller.current_low_limit)
        if PV_name == self.prefix+".TENA":
            temperature_controller.trigger_enabled = value
            casput(self.prefix+".TENA",temperature_controller.trigger_enabled)
        if PV_name == self.prefix+".P1SP":
            temperature_controller.trigger_start = value
            casput(self.prefix+".P1SP",temperature_controller.trigger_start)
        if PV_name == self.prefix+".P1EP":
            temperature_controller.trigger_stop = value
            casput(self.prefix+".P1EP",temperature_controller.trigger_stop)
        if PV_name == self.prefix+".P1SI":
            temperature_controller.trigger_stepsize = value
            casput(self.prefix+".P1SI",temperature_controller.trigger_stepsize)

class temperature_controller_DL(object):
    def __init__(self):
        self.port_name = 1    
        self.setT = 1
        self.enabled = 0
        self.feedback_loop_P = 1
        self.feedback_loop_I = 1
        self.feedback_loop_D = 1 
        self.stabilization_threshold = 1
        self.stabilization_nsamples = 1
        self.current_high_limit = 1
        self.current_low_limit = 1
        self.trigger_enabled = 1
        self.id = 1
        self.trigger_start = 1
        self.trigger_stop = 1
        self.trigger_stepsize = 1
        self.current = 99
        self.power = 99
        self.actual_temperature = 99
        self.max_time_between_replies = 0
        self.stable = False
        self.scan_time = 1
        self.baudrate = 9600

    def get_setT(self):
        return value

    def set_setT(self,value):
        return value

    setT = property(get_setT,set_setT)
    
    def run(self):
        self.enabled.value = 0
    

def sleep(seconds):
    """Delay execution by the given number of seconds"""
    # This version of "sleep" does not throw an excpetion if passed a negative
    # waiting time, but instead returns immediately.
    from time import sleep
    if seconds > 0: sleep(seconds)
    
temperature_controller_SL = Temperature_Controller_SL()
temperature_controller = temperature_controller_DL()

if __name__ == "__main__":
    from pdb import pm
    #self = temperature_controller_DL # for debugging
    #import logging;
    #logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s")
    import CAServer
    ##CAServer.LOG = True; CAServer.verbose = True
    temperature_controller.logging = True
    from sys import argv
    if "run_SL" in argv: temperature_controller_SL.run()
    temperature_controller_SL.start()
    print('temperature_controller_SL.prefix = %r' % temperature_controller_SL.prefix)
    print('temperature_controller_SL.EPICS_enabled = True')
    print('temperature_controller_SL.EPICS_enabled = False')
    print('temperature_controller_SL.run()')
    print('temperature_controller_SL.start()')
    print('temperature_controller_SL.stop()')
