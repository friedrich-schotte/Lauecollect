"""Temperature System Level (SL) Server
Capabilities:
- Time-based Temperature ramping
- EPICS IOC

Authors: Valentyn Stadnydskyi, Friedrich Schotte
Date created: 2019-05-08
Date last modified: 2019-05-21
"""
__version__ = "1.3" # lightwave_temperature_controller

from logging import debug,warn,info,error

from IOC import IOC
class Temperature_Server(IOC):
    name = "temperature"
    prefix = "NIH:TEMP."
    property_names = [
        "time_points",
        "temp_points",
        "VAL",
        "RBV",
        "set_point_update_period",
    ]

    from persistent_property import persistent_property
    time_points = persistent_property("time_points",[])
    temp_points = persistent_property("temp_points",[])
    set_point_update_period = persistent_property("set_point_update_period",0.5) 

    def run(self):
        self.monitoring = True
        self.running = True        
        from sleep import sleep
        while self.running: sleep(0.25)
    
    def get_monitoring(self):
        from timing_system import timing_system
        return self.on_acquire in timing_system.acquiring.monitors
    def set_monitoring(self,value):
        value = bool(value)
        from timing_system import timing_system
        if value != self.monitoring:
            if value == True:  timing_system.acquiring.monitor(self.on_acquire)
            if value == False: timing_system.acquiring.monitor_clear(self.on_acquire)
    monitoring = property(get_monitoring,set_monitoring)
        
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
                self.VAL = T
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
        times = [[]]
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
        temperatures = []
        time_points = self.time_points[0:self.N_points]
        temp_points = self.temp_points[0:self.N_points]
        if len(temp_points) > 1:
            from scipy.interpolate import interp1d
            f = interp1d(time_points,temp_points,kind='linear',bounds_error=False)
            temperatures = f(self.times)
        if len(temp_points) == 1:
            from numpy import array
            temperatures = array(temp_points)
        return temperatures

    @property
    def N_points(self):
        return min(len(self.time_points),len(self.temp_points))

    def get_VAL(self): return self.temperature_controller.VAL
    def set_VAL(self,value):
        info("VAL = %r" % value)
        self.temperature_controller.VAL = value
    VAL = property(get_VAL,set_VAL)

    def get_RBV(self): return self.temperature_controller.RBV
    RBV = property(get_RBV,set_VAL)

    @property
    def temperature_controller(self):
        from lightwave_temperature_controller import lightwave_temperature_controller
        return lightwave_temperature_controller
    
temperature_server = Temperature_Server()


if __name__ == "__main__": 
    import logging
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s",
    )

    ##from time import sleep
    ##sleep(0.5)

    from collect import collect
    print('collect.temperature_start()')
    print('')

    from temperature import temperature
    from numpy import nan
    ##print('temperature.VAL = %r' % temperature.VAL)
    ##print('temperature.RBV = %r' % temperature.RBV)
    print('temperature.time_points = %r' % temperature.time_points)
    print('temperature.temp_points = %r' % temperature.temp_points)
    ##print('temperature.time_points = [nan]')
    ##print('temperature.temp_points = [nan]')
    print('')

    from timing_sequencer import timing_sequencer
    print("timing_sequencer.queue_active = %r" % timing_sequencer.queue_active)
    print("timing_sequencer.queue_active = False # cancel acquistion")
    print("timing_sequencer.queue_repeat_count = 0 # restart acquistion")
    print("timing_sequencer.queue_active = True  # simulate acquistion")
    print ('')

    print ('temperature_server.monitoring = True')
    print ('temperature_server.running = True')

    self = temperature_server # for debugging


