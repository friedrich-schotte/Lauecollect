"""EPICS IOC prototype
Author: Friedrich Schotte
Date created: 2019-05-18
Date last modified: 2019-05-13
"""
__version__ = "1.1" # added: run

from logging import debug,warn,info,error

class IOC(object):
    name = "sample"
    prefix = "NIH:SAMPLE."

    from persistent_property import persistent_property
    from numpy import inf
    scan_period = persistent_property("scan_period",2.0)

    property_names = []

    def run(self):
        self.running = True
        from sleep import sleep
        while self.running: sleep(0.25)
    
    from thread_property_2 import thread_property
    @thread_property
    def running(self):
        info("Starting IOC: Prefix: %s ..." % self.prefix)
        from CAServer import casget,casput,casdel
        from time import time
        from sleep import sleep

        self.monitors_setup()
        
        while not self.running_cancelled:
            t = time()
            for name in self.property_names:
                if time() - self.last_updated(name) > self.update_period(name):
                    PV_name = self.prefix+name.upper()
                    value = getattr(self,name)
                    ##info("Update: %s=%r" % (PV_name,value))
                    casput(PV_name,value,update=False)
                    self.set_update_time(name)
            if not self.running_cancelled: sleep(t+self.min_update_period-time())
        casdel(self.prefix)

    last_updated_dict = {}
    def set_update_time(self,name):
        from time import time
        self.last_updated_dict[name] = time()
    def last_updated(self,name): return self.last_updated_dict.get(name,0)
    
    def update_period(self,name):
        from numpy import inf
        period = getattr(self,name+"_update_period",inf)
        period = min(period,self.scan_period)
        return period

    @property
    def min_update_period(self):
        update_periods = [self.update_period(name) for name in self.property_names]
        min_update_period =  min(update_periods) if len(update_periods) > 0 else self.scan_period
        return min_update_period

    def monitors_setup(self):
        """Monitor client-writable PVs."""
        from CAServer import casmonitor,casput
        for name in self.property_names:
            PV_name = self.prefix+name.upper()
            casmonitor(PV_name,callback=self.monitor)

    def monitor(self,PV_name,value,char_value):
        """Handle PV change requests"""
        info("%s = %r" % (PV_name,value))
        from CAServer import casput
        for name in self.property_names:
            if PV_name == self.prefix+name.upper():
                setattr(self,name,value)
                casput(PV_name,getattr(self,name))
