"""Temperature controller server

The server communicates with Lightwave( previously known as temperature controller IOC) and Oasis IOC to synchronize the temperature changes.
Authors: Valentyn Stadnydskyi, Friedrich Schotte
Date created: 2019-05-08
Date last modified: 2019-05-14
"""
__version__ = "0.1" # Friedrich Schotte: bug fixes

from logging import debug,warn,info,error
import os
from IOC import IOC
import traceback
from time import time,sleep
from numpy import empty, mean, std, zeros, abs, where, nan , isnan
import numpy.polynomial.polynomial as poly

from scipy.interpolate import interp1d
from CA import caget, caput
from CAServer import casput,casget,casdel

class Temperature_Server_IOC(object):

    name = "temperature_server_IOC"
    from persistent_property import persistent_property
    prefix = persistent_property("prefix","NIH:TEMP")
    SCAN = persistent_property("SCAN",0.5)
    P_default = persistent_property("P_default",1.000)
    I_default = persistent_property("I_default",0.316)
    D_default = persistent_property("D_default",0.562)
    oasis_slave = persistent_property("oasis_slave",1)
    temperature_oasis_switch = persistent_property("T_threshold",83.0)
    idle_temperature_oasis = persistent_property("idle_temperature_oasis",8.0)
    temperature_oasis_limit_high = persistent_property("temperature_oasis_limit_high",45.0)
    oasis_headstart_time = persistent_property("oasis_headstart_time",15.0)
    lightwave_prefix = persistent_property("lightwave_prefix",'NIH:LIGHTWAVE')
    oasis_prefix = persistent_property("oasis_prefix",'NIH:CHILLER')
    set_point_update_period = persistent_property("set_point_update_period",0.5)

    running = False
    last_valid_reply = 0
    was_online = False
    ramping_cancelled = False
    idle_temperature = 22.0

    time_points = []
    temp_points = []

    def get_EPICS_enabled(self):
        return self.running
    def set_EPICS_enabled(self,value):
        from thread import start_new_thread
        if value:
            if not self.running: start_new_thread(self.run,())
        else: self.running = False
    EPICS_enabled = property(get_EPICS_enabled,set_EPICS_enabled)

    def startup(self):
        from CAServer import casput,casmonitor
        from CA import caput,camonitor
        from numpy import nan
        #self.P_default , self.I_default , self.D_default = 1.0,0.316,0.562
        #print('startup with prefix = %r' %self.prefix)
        casput(self.prefix+".SCAN",self.SCAN)
        casput(self.prefix+".DESC",value = "Temperature server IOC: a System Layer server that orchestrates setting on Lightwave IOC and Oasis IOC.", update = False)
        casput(self.prefix+".EGU",value = "C")
        # Set defaults
        casput(self.prefix+".VAL",value = nan)
        casput(self.prefix+".VAL_ADV",value = nan)
        casput(self.prefix+".RBV",value = nan)
        casput(self.prefix+".P",value = nan)
        casput(self.prefix+".I",value = nan)
        casput(self.prefix+".TIME_POINTS",self.time_points)
        casput(self.prefix+".TEMP_POINTS",self.temp_points)
        casput(self.prefix+".FAULTS"," ")
        casput(self.prefix+".DMOV",value = nan)
        casput(self.prefix+".KILL",value = 'write password to kill the process')

        casput(self.prefix+".P_default",value = self.P_default)
        casput(self.prefix+".I_default",value = self.I_default)
        casput(self.prefix+".D_default",value = self.D_default)


        casput(self.prefix+".oasis_slave",value = self.oasis_slave)
        casput(self.prefix+".temperature_oasis_switch",value = self.temperature_oasis_switch)
        casput(self.prefix+".idle_temperature_oasis",value = self.idle_temperature_oasis)
        casput(self.prefix+".temperature_oasis_limit_high",value = self.temperature_oasis_limit_high)
        casput(self.prefix+".oasis_headstart_time",value = self.oasis_headstart_time)
        casput(self.prefix+".lightwave_prefix",value = self.lightwave_prefix)
        casput(self.prefix+".oasis_prefix",value = self.oasis_prefix)
        casput(self.prefix+".set_point_update_period",value = self.set_point_update_period)

        casput(self.prefix+".oasis_RBV",value = nan)
        casput(self.prefix+".oasis_VAL",value = nan)

        #PV with a list of all process variable registered at the current Channel Access Server
        casput(self.prefix+".LIST_ALL_PVS",value = self.get_pv_list())

        # Monitor client-writable PVs.
        casmonitor(self.prefix+".VAL",callback=self.monitor)
        casmonitor(self.prefix+".VAL_ADV",callback=self.monitor)
        casmonitor(self.prefix+".TIME_POINTS",callback=self.monitor)
        casmonitor(self.prefix+".TEMP_POINTS",callback=self.monitor)
        casmonitor(self.prefix+".KILL",callback=self.monitor)

        casmonitor(self.prefix+".P_default",callback=self.monitor)
        casmonitor(self.prefix+".I_default",callback=self.monitor)
        casmonitor(self.prefix+".D_default",callback=self.monitor)

        casmonitor(self.prefix+".oasis_slave",callback=self.monitor)
        casmonitor(self.prefix+".temperature_oasis_switch",callback=self.monitor)
        casmonitor(self.prefix+".idle_temperature_oasis",callback=self.monitor)
        casmonitor(self.prefix+".temperature_oasis_limit_high",callback=self.monitor)
        casmonitor(self.prefix+".oasis_headstart_time",callback=self.monitor)
        casmonitor(self.prefix+".lightwave_prefix",callback=self.monitor)
        casmonitor(self.prefix+".oasis_prefix",callback=self.monitor)
        casmonitor(self.prefix+".set_point_update_period",callback=self.monitor)

        #############################################################################
        ## Monitor server-writable PVs that come other servers

        ## Monitor Timing system IOC
        from timing_system import timing_system
        camonitor(timing_system.acquiring.PV_name,callback=self.on_acquire)

        ## Lightwave Temperature controller server
        prefix = self.lightwave_prefix
        camonitor(prefix+".VAL",callback=self.lightwave_monitor)
        camonitor(prefix+".RBV",callback=self.lightwave_monitor)
        camonitor(prefix+".P",callback=self.lightwave_monitor)
        camonitor(prefix+".I",callback=self.lightwave_monitor)
        camonitor(prefix+".DMOV",callback=self.lightwave_monitor)

        ## Oasis chiller server
        prefix = self.oasis_prefix
        camonitor(prefix+".VAL",callback=self.oasis_monitor)
        camonitor(prefix+".RBV",callback=self.oasis_monitor)

        ## Create local circular buffers
        from circular_buffer_LL import Server
        self.buffers = {}
        self.buffers['oasis_RBV'] = Server(size = (2,1*3600*2) , var_type = 'float64')
        self.buffers['oasis_VAL'] = Server(size = (2,1*3600*2) , var_type = 'float64')
        self.buffers['oasis_FAULTS'] = Server(size = (2,1*3600*2) , var_type = 'float64')

        self.buffers['lightwave_RBV'] = Server(size = (2,1*3600*2) , var_type = 'float64')
        self.buffers['lightwave_P'] = Server(size = (2,1*3600*2) , var_type = 'float64')
        self.buffers['lightwave_I'] = Server(size = (2,1*3600*2) , var_type = 'float64')
        self.buffers['lightwave_VAL'] = Server(size = (2,1*3600*2) , var_type = 'float64')


    def update_once(self):
        from CAServer import casput
        from numpy import isfinite,isnan,nan
        from time import time
        from sleep import sleep
        pass

    def run(self):
        """Run EPICS IOC"""
        self.startup()
        self.running = True
        while self.running:
            sleep(0.1)
        self.running = False

    def start(self):
        """Run EPCIS IOC in background"""
        from threading import Thread
        task = Thread(target=self.run,name="temperature_server_IOC.run")
        task.daemon = True
        task.start()



    def shutdown(self):
        from CAServer import casdel
        print('SHUTDOWN command received')
        self.running = False
        casdel(self.prefix)
        del self

    def get_pv_list(self):
        from CAServer import PVs
        lst = list(PVs.keys())
        #lst_new = []
        #for item in lst:
        #    lst_new.append(item.replace(self.prefix,'').replace('.',''))
        return lst#lst_new




    def monitor(self,PV_name,value,char_value):
        """Process PV change requests"""
        from CAServer import casput
        from CA import caput
        print("monitor: %s = %r" % (PV_name,value))
        if PV_name == self.prefix+".VAL_ADV":
            if self.get_set_lightwaveT() != value or self.get_set_oasisT() != self.temp_to_oasis(value):
                self.set_T(value)
        if PV_name == self.prefix+".VAL":
            if self.get_set_lightwaveT() != value or self.get_set_oasisT() != self.temp_to_oasis(value):
                self.set_adv_T(value)
        if PV_name == self.prefix + ".oasis_VAL":
            if self.get_set_oasisT() != value:
                self.set_set_oasisT(value)

        if PV_name == self.prefix + ".TIME_POINTS":
            self.time_points = value
        if PV_name == self.prefix + ".TEMP_POINTS":
            self.temp_points = value
        if PV_name == self.prefix + ".KILL":
            if value == 'shutdown':
                self.shutdown()

        if PV_name == self.prefix + ".P_default":
            self.P_default = value
            self.set_PIDCOF((self.P_default,self.I_default,self.D_default))
        if PV_name == self.prefix + ".I_default":
            self.I_default = value
            self.set_PIDCOF((self.P_default,self.I_default,self.D_default))
        if PV_name == self.prefix + ".D_default":
            self.D_default = value
            self.set_PIDCOF((self.P_default,self.I_default,self.D_default))

        if PV_name == self.prefix + ".oasis_slave":
            self.oasis_slave = value
        if PV_name == self.prefix + ".temperature_oasis_switch":
            self.temperature_oasis_switch = value
        if PV_name == self.prefix + ".idle_temperature_oasis":
            self.idle_temperature_oasis = value
        if PV_name == self.prefix + ".temperature_oasis_limit_high":
            self.temperature_oasis_limit_high = value
        if PV_name == self.prefix + ".oasis_headstart_time":
            self.oasis_headstart_time = value
        if PV_name == self.prefix + ".lightwave_prefix":
            self.lightwave_prefix = value
        if PV_name == self.prefix + ".oasis_prefix":
            self.oasis_prefix = value
        if PV_name == self.prefix + ".set_point_update_period":
            self.set_point_update_period = value


    def lightwave_monitor(self,PV_name,value,char_value):
        #print('time: %r, PV_name = %r,value= %r,char_value = %r' %(time(),PV_name,value,char_value) )
        from CA import cainfo
        from CAServer import casput
        prefix = self.lightwave_prefix
        if PV_name == prefix+".VAL":
            arr = empty((2,1))
            arr[0] = cainfo(prefix+".VAL","timestamp")
            arr[1] = float(value)
            self.buffers['lightwave_VAL'].append(arr)
            casput(self.prefix +'.VAL',value = float(value))
        if PV_name == prefix+".RBV":
            arr = empty((2,1))
            arr[0] = cainfo(prefix+".RBV","timestamp")
            arr[1] = float(value)
            self.buffers['lightwave_RBV'].append(arr)
            casput(self.prefix +'.RBV',value = float(value))
        if PV_name == prefix+".P":
            arr = empty((2,1))
            arr[0] = cainfo(prefix+".P","timestamp")
            arr[1] = float(value)
            self.buffers['lightwave_P'].append(arr)
            casput(self.prefix +'.P',value = float(value))
        if PV_name == prefix+".I":
            arr = empty((2,1))
            arr[0] = cainfo(prefix+".I","timestamp")
            arr[1] = float(value)
            self.buffers['lightwave_I'].append(arr)
            casput(self.prefix +'.I',value = float(value))
        #Done Move PV
        if PV_name == prefix+".DMOV":
            casput(self.prefix +'.DMOV',value = float(value))

    def oasis_monitor(self,PV_name,value,char_value):
        #print('oasis_monitor: time: %r, PV_name = %r,value= %r,char_value = %r' %(time(),PV_name,value,char_value) )
        from CA import cainfo
        prefix = self.oasis_prefix
        if PV_name == prefix+".VAL":
            arr = empty((2,1))
            arr[0] = cainfo(prefix+".VAL","timestamp")
            arr[1] = float(value)
            self.buffers['oasis_VAL'].append(arr)
            casput(self.prefix +'.oasis_VAL',value = float(value))
        if PV_name == prefix+".RBV":
            arr = empty((2,1))
            arr[0] = cainfo(prefix+".RBV","timestamp")
            arr[1] = float(value)
            self.buffers['oasis_RBV'].append(arr)
            casput(self.prefix +'.oasis_RBV',value = float(value))

    ## Temperature trajectory
    def on_acquire(self):
        """
        starts T-Ramp.
        Usually called from monitor()
        """
        print('on acquire')
        self.ramping = self.acquiring
        self.start_ramping()

    def start_ramping(self):
        """
        starts T-Ramp run_ramping_once method in a separate thread
        """
        from thread import start_new_thread
        start_new_thread(self.run_ramping_once,())

    def run_ramping_once(self):
        """
        runs ramping trajectory defined by self.time_points and self.temperatures
        """
        from time_string import date_time
        info("Ramp start time: %s" % date_time(self.start_time))
        from time import time,sleep
        from numpy import where, asarray
        if len(self.temperatures) != 0:
            max_set_T = max(self.temperatures)
            min_set_T = min(self.temperatures)
        else:
            min_set_T = nan
            max_set_T = nan
        for (t,T, grad_T) in zip(self.times,self.temperatures,self.grad_temperatures):
            dt = self.start_time + t - time()
            if dt > 0:
                sleep(dt)
                current_setT = self.get_setT()
                debug('t = %r, T = %r,dt = %r' %(t,T,dt))
                if len(self.temp_points)>0:
                    self.set_ramp_T(T)
                else:
                    info("The TEMP_POINTS list is empty. No temperature to set in the temperature trajectory.")
                # if T == max_set_T or T == min_set_T:
                    # self.set_PIDCOF((self.P_default,self.I_default,self.D_default))
                # else:
                    # (self.P_default,0.0,0.0)
                    # if grad_T > 0:
                        # self.set_PIDCOF((self.proportional_vs_sample_temperature(T,'up'),0.0,0.0))
                    # elif grad_T < 0:
                        # self.set_PIDCOF((self.proportional_vs_sample_temperature(T,'down'),0.0,0.0))
                    # else:
                        # self.set_PIDCOF((self.P_default,0.0,0.0))

                try:
                    indices = where(self.times >= t+self.oasis_headstart_time)[0][0:1]
                    debug('current index in the trajectory = %r' %indices)
                    if len(indices) > 0:
                        idx = indices[0]
                        self.set_set_oasisT(self.oasis_temperatures[idx])
                        debug('time = %r, oasis T = %r' %(t,self.temp_to_oasis(self.temperatures[idx])))
                except:
                    error(traceback.format_exc())
            if self.ramping_cancelled: break

        info("Ramp ended")
        self.set_PIDCOF((self.P_default,self.I_default,self.D_default))
        self.ramping_cancelled = False
        self.ramping = False

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
        """
        converts self.time_points to an array of values with specified spacing (readT_time_spacing0
        """
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
            f = interp1d(time_points,temp_points, kind='linear',bounds_error=False)
            temperatures = f(self.times)
        if len(temp_points) == 1:
            from numpy import array
            temperatures = array(temp_points)
        return temperatures

    @property
    def grad_temperatures(self):
        from numpy import gradient,array
        temp_points = self.temp_points[0:self.N_points]
        if len(temp_points) > 1:
            grad = gradient(self.temperatures)
        else:
            grad = array([0])
        return grad

    @property
    def oasis_temperatures(self):
        from numpy import max
        if len(self.temperatures) == 0:
            t_oasis = []
        else:
            temp_points = self.temperatures
            first_temp = self.temperatures[0]
            max_temp = max(temp_points)
            t_oasis = []
            idx = 0
            for temp in temp_points:
                oasis_temp = self.temp_to_oasis(temp)
                if max_temp >=self.temperature_oasis_switch:
                    if idx <=1:
                        t_oasis.append(oasis_temp)
                    elif idx > 1:
                        if temp > temp_points[idx-1] and temp_points[idx-1] > temp_points[idx-2]:
                            t_oasis.append(self.temperature_oasis_limit_high)
                        elif temp < temp_points[idx-1] and temp_points[idx-1] < temp_points[idx-2]:
                            t_oasis.append(self.idle_temperature_oasis)
                        else:
                            t_oasis.append(t_oasis[idx-2])
                else:
                    t_oasis.append(oasis_temp)
                idx +=1


        return t_oasis

    @property
    def oasis_times(self):
        time_points = self.times
        time_oasis = []
        for time in time_points:
            time_oasis.append(time - self.oasis_dl.headstart_time)
        return time_oasis

    @property
    def N_points(self):
        return min(len(self.time_points),len(self.temp_points))

    def get_setT(self):
        value = self.buffers['lightwave_VAL'].get_last_N(N = 1)[1,0]
        return value
    def set_setT(self,value):
        debug("set_point = %r" % value)
        value = float(value)
        if self.get_setT() != value:
            self.lightwave_dl.set_cmdT(value)
            self.oasis_dl.set_cmdT(self.temp_to_oasis(value))
    setT = property(get_setT,set_setT)


    def get_lightwaveT(self):
        value = self.buffers['lightwave_RBV'].get_last_N(N = 1)[1,0]
        return value
    lightwaveT = property(get_lightwaveT)

    def get_set_lightwaveT(self):
        value = self.buffers['lightwave_VAL'].get_last_N(N = 1)[1,0]
        return value
    def set_set_lightwaveT(self,value):
        from CA import caput, cawait
        from numpy import isnan
        if value is not isnan:
            caput(self.lightwave_prefix + '.VAL', value = float(value))
            cawait(self.lightwave_prefix + '.VAL')
    set_lightwaveT = property(get_set_lightwaveT,set_set_lightwaveT)

    def get_oasisT(self):
        value = self.buffers['oasis_RBV'].get_last_N(N = 1)[1,0]
        return value
    oasisT = property(get_oasisT)

    def get_set_oasisT(self):
        value = self.buffers['oasis_VAL'].get_last_N(N = 1)[1,0]
        return value
    def set_set_oasisT(self,value):
        from CA import caput
        from numpy import isnan
        if self.get_set_oasisT() != float(value):
            if value is not isnan:
                caput(self.oasis_prefix+'.VAL', value = float(value))
    set_oasisT = property(get_set_oasisT,set_set_oasisT)

    def set_T(self,value):
        value = float(value)
        if value != self.get_set_lightwaveT() or self.temp_to_oasis(value) != self.get_set_oasisT():
            if self.oasis_slave:
                self.set_set_oasisT(self.temp_to_oasis(value))
            self.set_set_lightwaveT(value)

    def set_ramp_T(self,value):
        value = float(value)
        if value != self.get_lightwaveT():
            self.set_set_lightwaveT(value)

    def set_adv_T(self,value):
        value = float(value)

        if value != self.get_lightwaveT() or self.temp_to_oasis(value) != self.get_set_oasisT() :
            self.set_set_oasisT(self.temp_to_oasis(value))
            self.set_PIDCOF((self.P_default,0.0,self.D_default))
            self.set_set_lightwaveT(value)
            info('set_set_lightwaveT %r at %r' %(value , time()))
            info(abs(self.get_lightwaveT() - self.get_set_lightwaveT()))
            if value >= self.temperature_oasis_switch:
                t_diff = 3.0
            else:
                t_diff = 3.0
            timeout = abs(self.get_lightwaveT() - self.get_set_lightwaveT())*1.5
            t1 = time()
            while abs(self.get_lightwaveT() - self.get_set_lightwaveT()) > t_diff:
                sleep(0.05)
                if time() - t1 > timeout:
                    break
            self.set_PIDCOF((self.P_default,self.I_default,self.D_default))

    def set_PCOF(self,value):
        from CA import caput, cawait
        if self.get_PCOF() != value:
            caput(self.lightwave_prefix + '.PCOF',value)
            cawait(self.lightwave_prefix + '.PCOF')
    def get_PCOF(self):
        from CA import caget
        value = caget(self.lightwave_prefix + '.PCOF')
        return value

    def set_ICOF(self,value):
        from CA import caput, cawait
        if self.get_ICOF() != value:
            caput(self.lightwave_prefix + '.ICOF',value)
            cawait(self.lightwave_prefix + '.ICOF')
    def get_ICOF(self):
        from CA import caget
        value = caget(self.lightwave_prefix + '.ICOF')
        return value

    def set_DCOF(self,value):
        from CA import caput,cawait
        if self.get_DCOF() != value:
            caput(self.lightwave_prefix + '.DCOF',value)
            cawait(self.lightwave_prefix + '.DCOF')
    def get_DCOF(self):
        from CA import caget
        value = caget(self.lightwave_prefix + '.DCOF')
        return value

    def set_PIDCOF(self,value):
        from CA import caput,cawait
        if self.get_PIDCOF() != value:
            print('setting PIDCOF: %r -> %r' %(self.get_PIDCOF(),value))
            caput(self.lightwave_prefix + '.PIDCOF',value)
            cawait(self.lightwave_prefix + '.PIDCOF')
    def get_PIDCOF(self):
        from CA import caget
        value = caget(self.lightwave_prefix + '.PIDCOF')
        return value

    def temp_to_oasis(self,T, mode = 'bistable'):
        if mode == 'bistable':
            if T >= self.temperature_oasis_switch:
                t = self.temperature_oasis_limit_high
            else:
                t = self.idle_temperature_oasis
        else:
            oasis_min = t_min= self.idle_temperature_oasis
            oasis_max = t_max = self.temperature_oasis_limit_high
            T_max= 120.0
            T_min= -16
            if T <=T_max or T >=T_min:
                t = ((T-T_min)/(T_max-T_min))*(t_max-t_min) + t_min
            elif T>T_max:
                t = self.temperature_oasis_limit_high
            elif T<T_min:
                t = self.idle_temperature_oasis

        if self.oasis_slave:
            return round(t,1)
        else:
            return self.idle_temperature_oasis
    def proportional_vs_sample_temperature(self, temperature = 0.0, direction = ''):
            T = temperature
            if direction == 'down':
                P = 4e-8*T**4 - 1e-5*T**3 + 0.0012*T**2 - 0.0723*T + 3.3001
            elif direction == 'up':
                P = 7e-9*T**4 - 3e-6*T**3 + 0.0004*T**2 - 0.0003*T + 1.6942
            else:
                P = self.P_default
            return round(P,3)

temperature_server_IOC = Temperature_Server_IOC()

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO,
        format="%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s",
    )
    from timing_sequencer import timing_sequencer

    print("timing_sequencer.queue_active = %r" % timing_sequencer.queue_active)
    print("timing_sequencer.queue_active = False # cancel acquistion")
    print("timing_sequencer.queue_active = True  # simulate acquistion")
    print("timing_sequencer.queue_repeat_count = 0 # restart acquistion")
    print("timing_sequencer.queue_active = True  # simulate acquistion")
    print("self.start_time = time(); self.start_ramping()")
    self =  temperature_server_IOC
    ##from matplotlib import pyplot as plt
    self.time_points = [0.0,30.0,302.0,332.0,634.0,30.0+634.0,302.0+634.0,332.0+634.0,634.0+634.0]
    self.temp_points = [-16,-16,120,120,-16,-16,120,120,-16]
    ##print("self.lightwave_dl.driver.feedback_loop.PID = (1.0, 0.300000012, 0.561999977)")
    ##print('plt.plot(self.times,self.temperatures); plt.plot(self.oasis_times,self.oasis_temperatures); plt.show()')
    ##plt.plot(self.times,self.temperatures); plt.plot(self.oasis_times,self.oasis_temperatures); plt.show()
