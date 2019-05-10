"""Prototype for temperature ramp server
Authors: Valentyn Stadnydskyi, Friedrich Schotte
Date created: 2019-05-18
Date last modified: 2019-05-18
"""
__version__ = "0.0"

from logging import debug,warn,info,error

from IOC import IOC
class Temperature_Server(IOC):
    name = "temperature"
    prefix = "NIH:TRAMP."
    property_names = [
        "time_points",
        "temp_points",
        "set_point",
        "temperature",
        "set_point_update_period",
    ]

    from persistent_property import persistent_property
    time_points = persistent_property("time_points",[0.0,5.0,10.0])
    temp_points = persistent_property("temp_points",[22.0,22.5,23.0])
    set_point_update_period = persistent_property("set_point_update_period",0.5) 

    def __init__(self):
        from CA import camonitor
        from timing_system import timing_system
        camonitor(timing_system.acquiring.PV_name,callback=self.on_acquire)
        
    def on_acquire(self):
        self.ramping = self.acquiring

    from thread_property_2 import thread_property
    @thread_property
    def ramping(self):
        from time_string import date_time
        info("Ramp start time: %s" % date_time(self.start_time))
        from time import time,sleep
        for (t,T) in zip(self.times,self.temperatures):
            dt = self.start_time+t - time()
            if dt > 0:
                sleep(dt)
                self.set_point = T
            if self.ramping_cancelled: break
        info("Ramp ended")

    @property
    def acquiring(self):
        from timing_system import timing_system
        return timing_system.acquiring.value        

    @property
    def start_time(self):
        from numpy import nan
        start_time = nan
        from timing_system import timing_system
        if timing_system.acquiring.value == 1:
            from CA import cainfo
            start_time = cainfo(timing_system.acquiring.PV_name,"timestamp")
        return start_time

    @property
    def times(self):
        from numpy import arange,concatenate
        min_dt = self.set_point_update_period
        times = []
        for i in range(0,len(self.time_points)-1):
            T0,T1 = self.time_points[i],self.time_points[i+1]
            DT = T1-T0
            N = max(int(DT/min_dt),1)
            dt = DT/N
            T = T0 + arange(0,N)*dt
            times.append(T)
        if len(self.time_points) > 0:
            times.append([self.time_points[-1]])
        times = concatenate(times)
        return times

    @property
    def temperatures(self):
        from scipy.interpolate import interp1d
        T = interp1d(
            self.time_points[0:self.N_points],
            self.temp_points[0:self.N_points],
            kind='linear',
            bounds_error=False,
        )
        return T(self.times)

    @property
    def N_points(self):
        return min(len(self.time_points),len(self.temp_points))

    def get_set_point(self):
        return self.temperature_controller.command_value
    def set_set_point(self,value):
        info("set_point = %r" % value)
        self.temperature_controller.command_value = value
    set_point = property(get_set_point,set_set_point)

    def get_temperature(self):
        return self.temperature_controller.value
    temperature = property(get_temperature,set_set_point)

    @property
    def temperature_controller(self):
        from temperature_controller import temperature_controller
        return temperature_controller
    
temperature_server = Temperature_Server()

class Temperature(object):
    prefix = Temperature_Server.prefix
    from PV_property import PV_property
    time_points = PV_property("time_points",[])
    temp_points = PV_property("temp_points",[])
    from numpy import nan
    set_point = PV_property("set_point",nan)
    temperature = PV_property("temperature",nan)

temperature = Temperature()


if __name__ == "__main__": 
    import logging
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s",
    )
    temperature_server.running = True

    from time import sleep
    sleep(0.5)

    print('temperature.set_point = %r' % temperature.set_point)
    print('temperature.temperature = %r' % temperature.temperature)
    print('temperature.time_points = %r' % temperature.time_points)
    print('temperature.temp_points = %r' % temperature.temp_points)

    from timing_sequencer import timing_sequencer
    print("timing_sequencer.queue_active = %r" % timing_sequencer.queue_active)
    print("timing_sequencer.queue_active = False # cancel acquistion")
    print("timing_sequencer.queue_active = True  # simulate acquistion")

    self = temperature_server # for debugging


