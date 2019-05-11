"""Temperature controller server

The server communicates with Lightwave( previously known as temperature controller IOC) and Oasis IOC to synchronize the temperature changes.
Authors: Valentyn Stadnydskyi, Friedrich Schotte
Date created: 2019-05-18
Date last modified: 2019-05-18
"""
__version__ = "0.0"

from logging import debug,warn,info,error

#from temperature_controller_driver import temperature_controller as lightwave
#from oasis_chiller import oasis_chiller_driver as oasis
#from temperature_controller_server import temperature_controller_IOC
from oasis_chiller_driver import driver as oasis_driver
from LDT_5900_driver import driver as lightwave_driver

from IOC import IOC


class Lightwave_DL():
    """
    an wrapper object to communicate with lightwave temperature controller
    """


    def __init__(self,prefix = "NIH:TEMP.", name = 'lightwave'):
        self.name = name
        self.prefix = prefix
    def init(self):
        pass

    def get_T(self):
        from CA import caget
        value = caget(self.prefix+'RBV')
        return value
    T = property(get_T)

    def get_moving(self):
        from CA import caget
        value = caget(self.prefix+'DMOV')
        return value
    moving = property(get_moving)
    
    def get_setT(self):
        from CA import caget
        value = caget(self.prefix+'VAL')
        return value
    def set_setT(self,value):
        from CA import caget
        caget(self.prefix+'VAL',value)
    setT = property(get_setT,set_setT)

class Oasis_DL():
    """
    an wrapper object to communicate with Oasis Chiller
    """


    def __init__(self,prefix = "NIH:CHILLER.", name = 'oasis'):
        self.name = name
        self.prefix = prefix
        
    def init(self):
        from circular_buffer_LL import Server
        self.buffer = Server()

    def run_once(self):
        pass

    def run(self):
        pass

    def get_T(self):
        from CA import caget
        value = caget(self.prefix+'RBV')
        return value
    T = property(get_T)
    
    def get_setT(self):
        from CA import caget
        value = caget(self.prefix+'VAL')
        return value
    def set_setT(self,value):
        from CA import caget
        caget(self.prefix+'VAL',value)
    setT = property(get_setT,set_setT)

    
class Temperature_Server():
    name = "temperature"
    prefix = "NIH:TRAMP."

    from persistent_property import persistent_property
    time_points = persistent_property("time_points",[0.0,5.0,10.0])
    temp_points = persistent_property("temp_points",[22.0,22.5,23.0])
    set_point_update_period = persistent_property("set_point_update_period",0.5)

    def __init__(self):
        pass

    def init(self):
        lightwave.init_communications()
        oasis.init_communications()

        from CA import camonitor
        from timing_system import timing_system
        camonitor(timing_system.acquiring.PV_name,callback=self.on_acquire)
        
    def on_acquire(self):
        self.ramping = self.acquiring

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

    def get_setT(self):
        value = self.lightwave.setT
        return value
    def set_setT(self,value):
        info("set_point = %r" % value)
        self.lightwave.setT = value
    setT = property(get_setT,set_setT)

    def get_T(self):
        value = self.lightwave.T
        return value
    T = property(get_T)

    @property
    def temperature_controller(self):
        from temperature_controller import temperature_controller
        return temperature_controller



temperature_server = Temperature_Server()
temperature_server.oasis = oasis_dl = Oasis_DL()
temperature_server.lightwave = lightwave_dl = Lightwave_DL()


if __name__ == "__main__": 
    import logging
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s",
    )

    self = temperature_server # for debugging


