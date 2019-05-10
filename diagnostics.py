"""Data Collection diagnostics
Author: Friedrich Schotte
Date created: 2018-10-27
Date last modified: 2019-01-18
"""
__version__ = "1.1.1" # import isfinite, average: len(self.image_numbers) > 0

from logging import debug,info,warn,error
import traceback

class Diagnostics(object):
    """Data Collection diagnostics"""
    from persistent_property import persistent_property
    list = persistent_property("list","")
    values = {}
    images = {}

    def get_running(self):
        return self.monitoring_variables and self.monitoring_image_number
    def set_running(self,value):
        if value and not self.running: self.clear()
        self.monitoring_variables = value
        self.monitoring_image_number = value
    running = property(get_running,set_running)

    def started(self,image_number):
        from numpy import nan
        time = nan
        if image_number in self.images: time = self.images[image_number].started
        return time

    def finished(self,image_number):
        from numpy import nan
        time = nan
        if image_number in self.images: time = self.images[image_number].finished
        return time

    def average_values(self,image_number):
        values = [self.average_value(image_number,v) for v in self.variable_names]
        return values

    def average_value(self,image_number,variable):
        # Make sure to have at least one sample even if none was measured
        # during the image.
        samples = []
        while len(samples) < 1 and len(self.image_numbers) > 0 and image_number >= min(self.image_numbers):
            samples += self.samples(image_number,variable)
            image_number -= 1
            
        value = nanmean(samples)
        return value

    def samples(self,image_number,variable):
        values = []
        if image_number in self.images and variable in self.values:
            image = self.images[image_number]
            all_values = self.values[variable]
            values = [tval.value for tval in all_values
                     if image.matches(tval.time)]
        return values

    @property
    def image_numbers(self): return self.images.keys()

    def clear(self):
        self.values = {}
        self.images = {}

    @property
    def variable_names(self):
        names = self.list.replace(" ","").split(",")
        return names

    @property
    def count(self): return len(self.variable_names)

    @property
    def vars(self):
        vars = []
        exec("from instrumentation import *") # -> eval
        for variable_name in self.variable_names:
            try: var = eval(variable_name)
            except Exception,msg:
                error("%r: %s" % (variable_name,msg))
                from CA import PV
                var = PV("")
            vars += [var]
        return vars
    
    def get_monitoring_variables(self):
        return self.__monitoring_variables__
    def set_monitoring_variables(self,value):
        if value:
            for (variable_name,var) in zip(self.variable_names,self.vars):
                var.monitor(self.handle_variables_update)
        else:
            for var in self.vars: var.monitor_clear()
        self.__monitoring_variables__ = value
    monitoring_variables = property(get_monitoring_variables,set_monitoring_variables)
    __monitoring_variables__ = False

    def handle_variables_update(self,PV_name,value,string_value):
        from time import time
        variable_name = ""
        for (name,var) in zip(self.variable_names,self.vars):
            if var.name == PV_name: variable_name = name
        if variable_name:
            if not variable_name in self.values: self.values[variable_name] = []
            self.values[variable_name] += [self.timestamped_value(time(),value)]

    def get_monitoring_image_number(self):
        from timing_system import timing_system
        monitoring_image_number = self.handle_image_number_update in timing_system.image_number.monitors
        monitoring_acquiring = self.handle_acquiring_update in timing_system.acquiring.monitors
        monitoring = monitoring_image_number and monitoring_acquiring
        return monitoring
    def set_monitoring_image_number(self,value):
        from timing_system import timing_system
        if value:
            timing_system.image_number.monitor(self.handle_image_number_update)
            timing_system.acquiring.monitor(self.handle_acquiring_update)
        else:
            timing_system.image_number.monitor_clear(self.handle_image_number_update)
            timing_system.acquiring.monitor_clear(self.handle_acquiring_update)
    monitoring_image_number = property(get_monitoring_image_number,set_monitoring_image_number)

    def handle_image_number_update(self):
        from time import time
        t = time()
        from timing_system import timing_system
        i = timing_system.image_number.count
        acquiring = timing_system.acquiring.count
        if acquiring:
            if not i in self.images: self.images[i] = self.interval()
            self.images[i].started = t
            from numpy import isfinite
            if i-1 in self.images and \
               (not isfinite(self.images[i].finished) or
                not self.images[i-1].finished >= self.images[i-1].started):
                self.images[i-1].finished = t

    def handle_acquiring_update(self):
        from time import time
        t = time()
        from timing_system import timing_system
        i = timing_system.image_number.count
        acquiring = timing_system.acquiring.count
        if acquiring:
            if not i in self.images: self.images[i] = self.interval()
            self.images[i].started  = t
        if not acquiring:
            from numpy import isfinite
            if i in self.images and \
               (not isfinite(self.images[i].finished) or
                not self.images[i].finished >= self.images[i].started):
                self.images[i].finished  = t

    class timestamped_value(object):
        def __init__(self,time,value):
            self.time = time
            self.value = value
        def __repr__(self):
            from time_string import date_time 
            return "(%s,%r)" % (date_time(self.time),self.value)

    class interval(object):
        from numpy import inf
        def __init__(self,started=-inf,finished=inf):
            self.started = started
            self.finished = finished
        def matches(self,time):
            return self.started <= time <= self.finished
        def __repr__(self):
            from time_string import date_time 
            return "(%s,%s)" % (date_time(self.started),date_time(self.finished))

diagnostics = Diagnostics()

def nanmean(a):
    from numpy import nansum,nan
    if len(a) > 0: return nansum(a)/len(a)
    else: return nan


if __name__ == '__main__':
    from pdb import pm # for debugging
    import logging # for debugging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s",
    )
    self = diagnostics # for debugging
    from instrumentation import ring_current,bunch_current,temperature
    variable = "ring_current"

    ##print("self.variable_names")
    ##print("self.running = True")
    ##print("self.running = False")
    ##print("self.values")
    ##print("self.image_numbers")
    ##print('self.average_values(self.image_numbers[2])')
    from CA import camonitors
    from timing_system import timing_system
    print("self.monitoring_image_number = True")
    print("timing_system.acquiring.count = 1")
    print("timing_system.image_number.count += 1")
    print("timing_system.acquiring.count = 0")
    print("self.images")
    print("camonitors(timing_system.image_number.PV_name)")
    ##print("camonitors(timing_system.acquiring.PV_name)")
