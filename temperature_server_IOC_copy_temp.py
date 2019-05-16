"""Temperature controller server

The server communicates with Lightwave( previously known as temperature controller IOC) and Oasis IOC to synchronize the temperature changes.
Authors: Valentyn Stadnydskyi, Friedrich Schotte
Date created: 2019-05-08
Date last modified: 2019-05-14
"""
__version__ = "0.1" # Friedrich Schotte: bug fixes

from logging import debug,warn,info,error

#from temperature_controller_driver import temperature_controller as lightwave
#from oasis_chiller import oasis_chiller_driver as oasis
#from temperature_controller_server import temperature_controller_IOC
from oasis_chiller_driver import driver as oasis_driver
from LDT_5900_driver import driver as lightwave_driver
from circular_buffer_LL import Server

from IOC import IOC
import traceback
from time import time,sleep
from numpy import empty, mean, std, zeros, abs, where
from scipy.interpolate import interp1d

from CA import caget
from CAServer import casput,casget,casdel

op_mode = 'local' # op_mode = 'IOC' or op_mode = 'direct'
class Lightwave_DL(object):
    """
    an wrapper object to communicate with lightwave temperature controller
    """


    def __init__(self,prefix = "NIH:TEMP.", name = 'lightwave'):
        self.name = name
        self.prefix = prefix
        self.stabilization_threshold_value = 0.050
        self.stabilization_threshold_N = 3
        self.readT_time_spacing = 0.5
        self.running = False

    def init(self):
        from circular_buffer_LL import Server
        self.buffers = {}
        self.buffers['actual_temperature'] = self.buffers['T'] = Server(size = (2,1*3600*2) , var_type = 'float64')
        self.buffers['target_temperature'] = self.buffers['cmdT'] = Server(size = (2,1*3600*2) , var_type = 'float64')
        self.buffers['current'] = self.buffers['I'] = Server(size = (2,1*3600*2) , var_type = 'float64')
        self.buffers['voltage'] = self.buffers['V'] = Server(size = (2,1*3600*2) , var_type = 'float64')
        self.buffers['power'] = self.buffers['P'] = Server(size = (2,1*3600*2) , var_type = 'float64')
        self.dev = self.driver = lightwave_driver
        self.start_CASmonitors()

        #get initial values
        self.read_cmd_temperature()
        self.read_TIP()

    def start(self):
        from thread import start_new_thread
        start_new_thread(self.run,())

    def run_once(self):
        self.read_TPIV()
        dmov = self.get_done_moving()
        casput(self.prefix+'DMOV',dmov)

    def run(self):
        from time import sleep,time
        self.running = True
        while self.running:
            self.run_once()
            sleep(self.readT_time_spacing )
        self.running = False

    def start_CASmonitors(self):
        from CAServer import casmonitor
        pass #casmonitor(self.prefix+'VAL',callback = self.monitor)

    def monitor(self,PV_name,value,char_value):
        """Process PV change requests"""
        from CAServer import casput
        info("PV arrived: %s = %r" % (PV_name,value))
        if PV_name == self.prefix+"VAL":
            self.set_adv_cmdT(float(value))


    def read_temperature(self):
        """reads current temperature from Lightwave temperature controller via serial port """
        from time import time
        import random
        from CAServer import casput
        value = self.dev.temperature.value # temporary for debugging purposes
        casput(self.prefix+'RBV',value)
        #update circular buffer
        arr = empty((2,1))*0
        arr[0] = time()
        arr[1] = value
        self.buffers['T'].append(arr)

    def read_cmd_temperature(self):
        """reads current temperature from Lightwave temperature controller via serial port """
        from time import time
        import random
        from CAServer import casput
        value = self.dev.setT.value # temporary for debugging purposes
        casput(self.prefix+'VAL',value)
        #update circular buffer
        arr = empty((2,1))*0
        arr[0] = time()
        arr[1] = value
        self.buffers['cmdT'].append(arr)

    def read_TIP(self):
        from CAServer import casput
        (T,I,P) = self.dev.TIP
        casput(self.prefix+'RBV',T)
        casput(self.prefix+'I',I)
        casput(self.prefix+'P',P)
        arr = empty((2,1))
        arr[0] = time()
        arr[1] = T
        self.buffers['T'].append(arr)
        arr[1] = I
        self.buffers['current'].append(arr)
        arr[1] = P
        self.buffers['power'].append(arr)

    def read_power(self):
        """reads current temperature from Lightwave temperature controller via serial port """
        from time import time
        import random
        from CAServer import casput
        value = self.dev.power.value # temporary for debugging purposes
        casput(self.prefix+'P',value)
        #update circular buffer
        arr = empty((2,1))*0
        arr[0] = time()
        arr[1] = value
        self.buffers['P'].append(arr)

    def read_current(self):
        """reads current temperature from Lightwave temperature controller via serial port """
        from time import time
        import random
        from CAServer import casput
        value = self.dev.current.value # temporary for debugging purposes
        casput(self.prefix+'I',value)
        #update circular buffer
        arr = empty((2,1))*0
        arr[0] = time()
        arr[1] = value
        self.buffers['I'].append(arr)

    def read_voltage(self):
        """reads current temperature from Lightwave temperature controller via serial port """
        from time import time
        import random
        from CAServer import casput
        value = self.dev.voltage.value# temporary for debugging purposes
        casput(self.prefix+'V',value)
        #update circular buffer
        arr = empty((2,1))*0
        arr[0] = time()
        arr[1] = value
        self.buffers['V'].append(arr)

    def read_TPIV(self):
        from time import time
        self.read_temperature()
        self.read_current()
        #self.read_voltage()
        self.read_power()

    def get_T(self):
        #for CA communication with existing IOC
        #from CA import caget
        #value = caget(self.prefix+'RBV')
        #for testing purposes
        value = self.buffers['T'].get_last_N(N = 1)[1,0]
        return value
    T = property(get_T)

    def get_power(self):
        #for CA communication with existing IOC
        #from CA import caget
        #value = caget(self.prefix+'RBV')
        #for testing purposes
        value = self.buffers['power'].get_last_N(N = 1)[1,0]
        return value
    power = property(get_power)

    def get_moving(self):
        #from CA import caget
        #value = caget(self.prefix+'DMOV')
        from numpy import mean
        N = self.stabilization_threshold_N
        meanT = mean(self.buffers['T'].get_last_N(N = N)[1,:])
        setT = mean(self.buffers['cmdT'].get_last_N(N = 1)[1,:])
        if abs(meanT - setT) <= self.stabilization_threshold_value:
            value = 0
        else:
            value = 1
        return value
    moving = property(get_moving)

    def get_done_moving(self):
        #from CA import caget
        #value = caget(self.prefix+'DMOV')
        from numpy import mean
        N = self.stabilization_threshold_N
        meanT = mean(self.buffers['T'].get_last_N(N = N)[1,:])
        setT = mean(self.buffers['cmdT'].get_last_N(N = 1)[1,:])
        if abs(meanT - setT) <= self.stabilization_threshold_value:
            value = 1
        else:
            value = 0
        return value
    done_moving = property(get_done_moving)



    def get_cmdT(self):
        from CA import caget
        value = self.buffers['cmdT'].get_last_N(N = 1)[1,0]
        #value = 22.0
        return value
    def set_cmdT(self,value):
        info('lightwave_dl: set_cmdT = %r' %value)
        #communicate with the devive and set value
        from CAServer import casget,casput
        self.dev.setT.value = value
        casput(self.prefix+'VAL',value)
        #update circular buffer
        arr = empty((2,1))*0
        arr[0] = time()
        arr[1] = value
        self.buffers['cmdT'].append(arr)
        ##
    cmdT = property(get_cmdT,set_cmdT)

    def set_adv_cmdT(self,T):
        info('lighwave: set_adv_cmdT: %r' % T)
        self.dev.feedback_loop.PID = (1.0,0.0,0.562)
        self.set_cmdT(T)
        while abs(T - self.get_T()) > 1:
            sleep(0.25)
        self.dev.feedback_loop.PID = (1.0,0.3,0.562)


    def get_status(self):
        from CA import caget
        value =nan #caget(self.prefix+'VAL')
        #value = 22.0
        return value
    def set_status(self,value):
        #communicate with the devive and set value
        #from CA import caget,caput
        #caput(self.prefix+'VAL',value)
        #update circular buffer
        ##
        pass
    status = property(get_status,set_status)

class Oasis_DL(object):
    """
    an wrapper object to communicate with Oasis Chiller
    """


    def __init__(self,prefix = "NIH:CHILLER.", name = 'oasis'):
        self.name = name
        self.prefix = prefix
        self.readT_time_spacing = 2
        self.idle_playlist = [self.read_temperature]*100+[self.read_faults]
        self.idle_playlist_pointer = 0
        self.playlist = []
        self.idle_playlist_pointer = -1
        self.running = False
        self.headstart_time = 15.0

    def init(self):
        """
        initializes Oasis DL: creates circular buffers, starts communication with oasis chiller and starts CAServer monitors
        """
        from circular_buffer_LL import Server
        self.buffers = {}
        self.buffers['actual_temperature'] = self.buffers['T'] = Server(size = (2,1*3600*2) , var_type = 'float64')
        self.buffers['target_temperature'] = self.buffers['cmdT'] = Server(size = (2,1*3600*2) , var_type = 'float64')
        self.buffers['faults'] = self.buffers['faults'] = Server(size = (2,1*3600*2) , var_type = 'float64')
        self.driver = self.dev = oasis_driver
        self.dev.init()
        self.start_CASmonitors()



        self.read_cmd_temperature()
        sleep(self.readT_time_spacing)
        self.read_temperature()
        sleep(self.readT_time_spacing)
        self.read_faults()
        sleep(self.readT_time_spacing)

    def start_CASmonitors(self):
        from CAServer import casmonitor
        casmonitor(self.prefix+'VAL',callback = self.monitor)

    def monitor(self,PV_name,value,char_value):
        """Process PV change requests"""
        from CAServer import casput
        info("oasis monitor: %s = %r" % (PV_name,value))
        if PV_name == self.prefix+"VAL":
            self.set_cmdT(float(value))

    def start(self):
        from thread import start_new_thread
        start_new_thread(self.run,())

    def run_once(self):
        #if cainfo('NIH:OASIS.VAL',"timestamp") > time();
        #    value = casget('NIH:OASIS.VAL')
        #    self.set_setT(NIH)
        #if casget('NIH:CHILLER.VAL') != self.get_cmdT():
            #self.set_cmdT(casget('NIH:CHILLER.VAL'))
        #else:
        if len(self.playlist) != 0:
            self.playlist[0][0](self.playlist[0][1])
            self.playlist.pop(0)
        else:
            self.idle_playlist[self.idle_playlist_pointer]()
            self.idle_playlist_pointer +=1
            if self.idle_playlist_pointer == len(self.idle_playlist):
                self.idle_playlist_pointer = 0


    def run(self):
        self.running = True
        while self.running:
            self.run_once()
            sleep(self.readT_time_spacing)
        self.running = False



    def read_temperature(self):
        from CAServer import casput
        value = self.dev.actual_temperature
        casput(self.prefix+'RBV',value)
        arr = empty((2,1))
        arr[0] = time()
        arr[1] = value
        self.buffers['T'].append(arr)

    def read_cmd_temperature(self):
        from CAServer import casput
        value = self.dev.get_nominal_temperature()
        casput(self.prefix+'VAL',value)
        arr = empty((2,1))
        arr[0] = time()
        arr[1] = value
        self.buffers['cmdT'].append(arr)

    def read_faults(self):
        from CAServer import casput
        value = self.dev.fault_code
        casput(self.prefix+'faults_code',value)
        arr = empty((2,1))
        arr[0] = time()
        arr[1] = value
        self.buffers['faults'].append(arr)

    def get_T(self):
        value = self.buffers['T'].get_last_N(1)[1,0]
        return value
    T = property(get_T)

    def get_cmdT(self):
        value = self.buffers['cmdT'].get_last_N(1)[1,0]
        return value
    def set_cmdT(self,value):
        info('Oasis: set_cmdT = %r' %value)
        value = float(value)
        from CAServer import casput
        if value != self.get_cmdT():
            casput(self.prefix+'VAL',value)
            self.playlist.append([self.dev.set_nominal_temperature,round(value,1)])
        arr = empty((2,1))
        arr[0] = time()
        arr[1] = value
        self.buffers['cmdT'].append(arr)
    cmdT = property(get_cmdT,set_cmdT)

    def get_faults(self):
        value = self.buffers['faults'].get_last_N(1)[1,0]
        return value
    faults = property(get_faults)



class Temperature_Server(object):
    name = "temperature"
    prefix = "NIH:TEMP."

    from persistent_property import persistent_property
    time_points = persistent_property("time_points",[0.0,0.0])
    temp_points = persistent_property("temp_points",[22.0,22.0])
    set_point_update_period = persistent_property("set_point_update_period",1)
    idle_temperature = persistent_property("idle_temperature",22.0)
    idle_temperature_oasis = persistent_property("idle_temperature_oasis",8.0)
    temperature_limits = persistent_property("idle_temperature",(-16,120))
    temperature_oasis_limit_high= persistent_property("temperature_oasis_limit_high",45.0)
    temperature_oasis_switch = persistent_property("temperature_oasis_switch",83.0)

    def __init__(self):
        self.ramping_cancelled = True

    def init(self):
        """
        initializes temperature server
        """
        ## initialize and start lightwave DL
        self.lightwave_dl.init()
        self.lightwave_dl.start()
        ## initialize and start Oasis DL
        self.oasis_dl.init()
        self.oasis_dl.start()

        #Start CAmonitors
        from CA import camonitor
        from CAServer import casget
        from timing_system import timing_system
        camonitor(timing_system.acquiring.PV_name,callback=self.on_acquire)
        camonitor(self.prefix + 'VAL',callback=self.monitor)
        casput("NIH:TRAMP.TIME_POINTS",self.time_points)
        casput("NIH:TRAMP.TEMP_POINTS",self.temp_points)
        camonitor("NIH:TRAMP.TIME_POINTS",callback=self.monitor)
        camonitor("NIH:TRAMP.TEMP_POINTS",callback=self.monitor)

    def monitor(self,PV_name,value,char_value):
        """Process PV change requests"""
        from CAServer import casput
        #info("%s = %r" % (PV_name,value))
        if PV_name == self.prefix+"VAL":
            if self.ramping != True:
                self.set_adv_setT(float(value))
        if PV_name == "NIH:TRAMP.TIME_POINTS":#self.prefix+"TIME_POINTS":
            info("%s = %r" % (PV_name,value))
            self.time_points = value
        if PV_name == "NIH:TRAMP.TEMP_POINTS":#self.prefix+"TEMP_POINTS":
            self.temp_points = value
            info("%s = %r" % (PV_name,value))

    def on_acquire(self):
        """
        starts T-Ramp.
        Usually called from monitor()
        """
        self.ramping = self.acquiring
        self.start_ramping()

    def start_ramping(self):
        """starts T-Ramp run_ramping_once method in a separate thread
        """
        from thread import start_new_thread
        start_new_thread(self.run_ramping_once,())

    def run_ramping_once(self):
        """
        runs ramping trajectory defined by self.time_points and self.temperaturs
        """
        from time_string import date_time
        info("Ramp start time: %s" % date_time(self.start_time))
        from time import time,sleep
        from numpy import where, asarray
        for (t,T) in zip(self.times,self.temperatures):
            dt = self.start_time+t - time()
            if dt > 0:
                sleep(dt)
                debug('t = %r, T = %r,dt = %r' %(t,T,dt))
                self.set_ramp_setT(T)
                try:
                    indices = where(self.times >= t+self.oasis_dl.headstart_time)[0][0:1]
                    print(indices)
                    if len(indices) > 0:
                        idx = indices[0]
                        self.oasis_dl.set_cmdT(self.oasis_temperatures[idx])
                        info('time = %r, oasis T = %r' %(t,self.temp_to_oasis(self.temperatures[idx])))
                except:
                    error(traceback.format_exc())
            if self.ramping_cancelled: break
        self.temp_points = []
        self.time_points = []

        info("Ramp ended")
        self.set_adv_setT(self.idle_temperature)
        self.ramping_cancelled = False
        self.ramping = False

    @property
    def acquiring(self):
        from timing_system import timing_system
        return timing_system.acquiring.value

    @property
    def start_time(self):
        """
        requests T-Ramp start time from the timing system module
        """
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
        """
        converts
        """
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
        value = self.lightwave_dl.cmdT
        return value
    def set_setT(self,value):
        debug("set_point = %r" % value)
        value = float(value)
        if self.get_setT() != value:
            self.lightwave_dl.set_cmdT(value)
            self.oasis_dl.set_cmdT(self.temp_to_oasis(value))
    setT = property(get_setT,set_setT)

    def set_adv_setT(self,value):
        debug("set_adv_Tpoint = %r" % value)
        value = float(value)
        if self.get_setT() != value:
            self.oasis_dl.set_cmdT(self.temp_to_oasis(value))
            self.lightwave_dl.set_adv_cmdT(value)


    def set_ramp_setT(self,value):
        info("set_point = %r" % value)
        value = float(value)
        if self.get_setT() != value:
            self.lightwave_dl.set_cmdT(value)
            #self.oasis_dl.set_cmdT(self.temp_to_oasis(value))

    def get_T(self):
        value = self.lightwave_dl.T
        return value
    T = property(get_T)

    def get_oasis_cmdT(self):
        """gets oasis commanded temperature"""
        value = self.oasis_dl.cmdT
        return value
    def set_oasis_cmdT(self,value):
        """sets oasis commanded temperature"""
        debug("set_point = %r" % value)
        self.oasis_dl.set_cmdT(value)
    oasis_cmdT = property(get_oasis_cmdT,set_oasis_cmdT)

    def get_oasis_T(self):
        value = self.oasis_dl.T
        return value
    oasis_T = property(get_oasis_T,set_oasis_cmdT)


    def temp_to_oasis(self,T, mode = 'bistable'):
        if mode == 'bistable':
            if T >= self.temperature_oasis_switch:
                t = 45.0
            else:
                t =8.0
        else:
            oasis_min = t_min= 8.0
            oasis_max = t_max = 45.0
            T_max= 120.0
            T_min= -16
            if T <=T_max or T >=T_min:
                t = ((T-T_min)/(T_max-T_min))*(t_max-t_min) + t_min
            elif T>T_max:
                t = 45.0
            elif T<T_min:
                t = 8

        return round(t,1)

    @property
    def temperature_controller(self):
        from temperature_controller import temperature_controller
        return temperature_controller



temperature_server = Temperature_Server()
temperature_server.oasis_dl = oasis_dl = Oasis_DL()
temperature_server.lightwave_dl = lightwave_dl = Lightwave_DL()


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO,
        format="%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s",
    )
    from timing_sequencer import timing_sequencer

    print("timing_sequencer.queue_active = %r" % timing_sequencer.queue_active)
    print("timing_sequencer.queue_active = False # cancel acquistion")
    print("timing_sequencer.queue_active = True  # simulate acquistion")
    print("self.start_time = time(); self.start_ramping()")
    self = temperature_server # for debugging
    self.init()


    ##from matplotlib import pyplot as plt
    self.time_points = [0.0,30.0,302.0,332.0,634.0,30.0+634.0,302.0+634.0,332.0+634.0,634.0+634.0]
    self.temp_points = [-16,-16,120,120,-16,-16,120,120,-16]
    ##print("self.lightwave_dl.driver.feedback_loop.PID = (1.0, 0.300000012, 0.561999977)")
    ##print('plt.plot(self.times,self.temperatures); plt.plot(self.oasis_times,self.oasis_temperatures); plt.show()')
    ##plt.plot(self.times,self.temperatures); plt.plot(self.oasis_times,self.oasis_temperatures); plt.show()
