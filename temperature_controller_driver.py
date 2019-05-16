"""
ILX Lightwave LDT-5948 Precision Temperature Controller
Friedrich Schotte, 14 Dec 2009 - Jul 5, 2017

Communication Paramters: 115200 baud, 8 data bits, 1 stop bit, parity: none
flow control: none
2 = TxD, 3 = RxD, 5 = Gnd (DCE = Data Circuit-terminating Equipment)
9600 baud is the factory setting, but can be changed from the fron panel:
MAIN/LOCAL - COMMUNICATION 1/7 - down - RS323 Baud
Possible baud rates are: 1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200,
and 230400.

The controller accpts ASCII text commands. Each command needs to by terminated
with a newline or carriage return character.
Replies are terminated with carriage return and newline.
Command that are not queries generate the reply "Ready".
If a query is not understood, the controller replies with "Ready" as well.

Commands:
*IDN? identification, expecting: "ILX Lightwave,LDT-5948,59481287,01.02.06"
MEASure:Temp? - Report the actual temperature.
SET:Temp?     - Report the temperature set point.
SET:Temp 37.0 - Change temperature set point to 37 degrees C.
MEASure:PTE?  - Read heater power in W

Cabling: VME crate "iocidb", back panel "14IDB:serial1" -> STRAIGHT TRU
adapter -> black ethernet cable -> STRAIGHT TRU adapter ->
temperature controller

Documentation:
LDT-5900 Series Temperature Controllers User's Guide
www.newport.com/medias/sys_master/images/images/h75/h4e/8797193273374/LDT-59XX-User-Manual.pdf
"""
from __future__ import with_statement
from persistent_property import persistent_property
from logging import warn,debug,info,error

__version__ = "3.0.9" # multi-thread safe history

class TemperatureController(object):
    """ILX Lightwave LDT-5948 precision temperature controller"""
    name = "temperature_controller"
    verbose_logging = True
    last_reply_time = 0.0
    max_time_between_replies = 0.0

    def __init__(self):
        # Make multithread safe
        from thread import allocate_lock
        self.__lock__ = allocate_lock()

        # When read, read actual temperature, when changed, change set point.
        self.actual_temperature = self.property_object(self,"MEAS:T",unit="C",
            name="Temperature")
        self.nominal_temperature = self.property_object(self,"SET:TEMP",unit="C",
            name="set-point")
        self.heating_power = self.property_object(self,"MEASure:PTE",unit="W",
            name="power")
        self.current = self.property_object(self,"MEASure:ITE",unit="A",
            name="current")
        self.voltage = self.property_object(self,"MEASure:VTE",unit="V",
            name="voltage")
        # enabled: Is the feed-back loop for regulating the temperature active?
        self.enabled = self.property_object(self,"OUTPUT",unit="",
            name="enabled")
        self.Tmin = self.property_object(self,"LIMIT:TEMP:LOW",unit="C",
            name="low-limit")
        self.Tmax = self.property_object(self,"LIMIT:TEMP:HIGH",unit="C",
            name="high-limit")
        self.temperature = self.temperature_object(self)
        self.feedback_loop = self.feedback_loop_object(self)
        self.status = self.status_object(self)
        # Define some shortcuts.
        self.T = self.temperature
        self.setT = self.nominal_temperature
        self.readT = self.actual_temperature
        self.P = self.power = self.heating_power
        self.I = self.current
        self.U = self.voltage
        self.on = self.enabled

    def get(self,name):
        """Query the numeric value of a parameter.
        name: e.g. 'SET:TEMP'"""
        from numpy import nan
        try: value = float(self.query(name+"?"))
        except ValueError: value = nan
        if abs(value) >= 9.8e+37: value = nan
        ##self.record_value(name,value)
        return value
    def set(self,name,value):
        """Change the value of a parameter.
        name: e.g. 'SET:TEMP'"""
        self.query("%s %s" % (name,value))

    def __getitem__(self,name):
        """Usage: temperature_controller['SET:TEMP']"""
        return self.get(name)

    def __setitem__(self,name,value):
        """Usage: temperature_controller['SET:TEMP'] = 22.0"""
        self.set(name,value)

    def query(self,command):
        """Send a command to the controller and return the reply"""
        if not command.endswith("\n"): command = command+"\n"
        with self.__lock__: # multithread safe
            for attempts in range(0,3):
                reply = self.__query__(command)
                error = "?" in command and "Ready" in reply
                if not error: break
                sleep(0.1)
        reply = reply.rstrip("\r\n")
        return reply

    def __query__(self,command):
        """Send a command to the controller and return the reply"""
        self.write(command)
        reply = self.readline()
        return reply

    def write(self,command):
        """Send a command to the controller"""
        self.init_communications()
        if self.port is not None:
            self.port.write(command)
            self.log_comm("Sent %r" % command)

    def readline(self):
        """Read a reply from the controller,
        terminated with either new line or carriage return"""
        from time import time
        if self.port is not None:
            try: reply = self.port.readline()
            except Exception,msg: warn("readline: %s" % msg); reply = ""
            self.log_comm("Read %r" % reply)
        else: reply = ""
        if reply:
            t = time()
            self.max_time_between_replies = max(t-self.last_reply_time,self.max_time_between_replies)
            self.last_reply_time = t
        return reply

    def init_communications(self):
        """To do before communncating with the controller"""
        from os.path import exists
        from serial import Serial
        id_query = "*IDN?\n"

        if self.port is not None:
            try:
                self.port.write(id_query)
                reply = self.port.readline()
                if not self.id_string in reply:
                    debug("Port %s: %r: reply %r" % (self.__port_name__,id_query,reply))
                    info("Port %s: lost connection" % self.__port_name__)
                    self.port = None
                    self.__port_name__ = ""
            except Exception,msg:
                debug("%s: %s" % (Exception,msg))
                self.port = None
                self.__port_name__ = ""

        if self.port is None:
            port_basename = "COM" if not exists("/dev") else "/dev/tty.usbserial"
            for i in range(0,64):
                port_name = port_basename+("%d" % i if i>0 else "")
                debug("Trying port %s..." % port_name)
                try:
                    temp = Serial(port_name,timeout=self.comm_timeout,
                        baudrate=self.baudrate.value)
                    temp.write(id_query)
                    reply = temp.readline()
                    debug("Port %s: %r: reply %r" % (port_name,id_query,reply))
                    if self.id_string in reply:
                       self.port = temp
                       self.__port_name__ = port_name
                       info("Port %s: found %s" % (port_name,self.id_string))
                       break
                except Exception,msg: debug("%s: %s" % (Exception,msg))

    id_string = "LDT-5948"
    port = None
    __port_name__ = ""

    def get_port_name(self):
        """Serial port device filename"""
        self.init_communications()
        return self.__port_name__
    def set_port_name(self,value): pass
    port_name = property(get_port_name,set_port_name)

    def get_id(self): return self.query("*IDN?")
    def set_id(self,value): pass
    id = property(get_id,set_id)

    def instantiate(x): return x()

    @instantiate
    class baudrate(object):
        """Serial port EPICS record name"""
        name = "temperature_contoller.baudrate"
        value = persistent_property("value",9600)

    def get_comm_timeout(self):
        """For scans, to provide feedback whether the temperature 'motor'
        is still 'moving'"""
        from DB import dbget
        s = dbget("temperature_controller.temperature.comm_timeout")
        try: return float(s)
        except: return 0.2
    def set_comm_timeout(self,value):
        from DB import dbput
        dbput("temperature_controller.temperature.moving_timeout",str(value))
    comm_timeout = property(get_comm_timeout,set_comm_timeout)

    class temperature_object(object):
        """For logging and scanning, can be used as counter"""
        unit = "C"
        name = "Temp."

        def __init__(self,controller):
            self.controller = controller
            self.last_change = 0
            # Define shortcuts
            self.T = self.controller.actual_temperature
            self.setT = self.controller.nominal_temperature
        def get_value(self): return self.T.value
        def set_value(self,value):
            from time import time
            self.controller.enabled.value = True
            old_value = self.setT.value
            self.setT.value = value
            if value != old_value: self.last_change = time()
        value = property(get_value,set_value)

        @property
        def values(self): return self.T.values
        @property
        def timestamps(self): return self.T.timestamps
        @property
        def RMS(self): return self.T.RMS
        @property
        def average(self): return self.T.average

        def get_moving(self):
            """Has the actual temperature not yet reached the set point within
            tolerance?
            For scans, to provide feedback whether the temperature 'motor'
            is still 'moving'"""
            return self.T.moving
        def set_moving(self,value):
            """If value = False, cancel the current temperature ramp."""
            if abs(self.setT.value - self.T.value) > self.tolerance:
                self.setT.value = self.T.value
        moving = property(get_moving,set_moving)

        def stop(self):
            """Cancel the current temperature ramp."""
            self.moving = False

        def get_timeout(self):
            """For scans, to provide feedback whether the temperature 'motor'
            is still 'moving'"""
            from DB import dbget
            s = dbget("temperature_controller.temperature.moving_timeout")
            try: return float(s)
            except: return 0.0
        def set_timeout(self,value):
            from DB import dbput
            dbput("temperature_controller.temperature.moving_timeout",str(value))
        timeout = property(get_timeout,set_timeout)

        def get_tolerance(self):
            """For scans, to provide feedback whether the temperature 'motor'
            is still 'moving'"""
            from DB import dbget
            s = dbget("temperature_controller.temperature.tolerance")
            try: return float(s)
            except: return 3.0
        def set_tolerance(self,value):
            from DB import dbput
            dbput("temperature_controller.temperature.tolerance",str(value))
        tolerance = property(get_tolerance,set_tolerance)

        def __repr__(self): return "temperature_controller.temperature_object"

    class property_object(object):
        """For logging and scanning, can be used as counter"""
        from numpy import array
        timestamps = array([])
        values = array([])
        # How long is the temperature log, in seconds?
        history_length = persistent_property("history_length",300)
        # Criteria for deciding whether the temperature has stabilized.
        stabilization_time = persistent_property("stabilization_time",0.0) # seconds
        stabilization_RMS  = persistent_property("stabilization_RMS" ,0.0)

        def __init__(self,controller,read,unit="",name="",write=""):
            """read: e.g. 'SET:TEMP?'.
            If write is omitted, will use 'SET:TEMP' to write."""
            self.controller = controller
            self.read = read
            self.unit = unit
            self.name = name
            self.write = write
            if not self.read.endswith("?"): self.read += "?"
            if self.write == "": self.write = self.read.rstrip("?")
            # To make history multi-thread safe
            from thread import allocate_lock
            self.lock = allocate_lock()

        def get_value(self):
            from numpy import nan
            try: value = float(self.controller.query(self.read))
            except ValueError: value = nan
            if abs(value) >= 9.8e+37: value = nan
            self.record_value(value)
            return value
        def set_value(self,value):
            self.controller.query("%s %s" % (self.write,value))
        value = property(get_value,set_value)

        def record_value(self,value):
            with self.lock: # needs to be multi-thread safe
                from time import time
                from numpy import concatenate
                timestamp = time()
                # Make sure values and timestamp have the saame length (FS Oct 29, 2016)
                N = min(len(self.values),len(self.timestamps))
                self.values,self.timestamps = self.values[0:N],self.timestamps[0:N]
                # Discard old values.
                keep = self.timestamps >= timestamp-self.history_length
                self.values,self.timestamps = self.values[keep],self.timestamps[keep]
                # Ignore duplicates.
                if len(self.values)>0 and value == self.values[-1]: return
                self.values = concatenate((self.values,[value]))
                self.timestamps = concatenate((self.timestamps,[timestamp]))

        @property
        def average(self):
            from time import time
            from numpy import average,nan
            dt = self.stabilization_time
            values = self.values[self.timestamps > time()-dt]
            average = average(values) if len(values)>0 else nan
            return average

        @property
        def RMS(self):
            from time import time
            from numpy import std,nan
            dt = self.stabilization_time
            values = self.values[self.timestamps > time()-dt]
            RMS = std(values) if len(values)>0 else nan
            return RMS

        def get_moving(self):
            """Has the value been stable for some time?"""
            moving = self.RMS > self.stabilization_RMS
            return moving
        def set_moving(self,value): pass
        moving = property(get_moving,set_moving,doc="This is so it can be"
            "scanned like a motor")

        def stop(self): pass

    class feedback_loop_object(object):
        """Feedback loop parameters.
        P = proportional feedback constant
        I = integralfeedback constant
        D = differential  feedback constant"""
        def __init__(self,controller):
            """name: one of "P","I","D" """
            self.controller = controller
            self.unit = ""
            self.P = self.parameter(self,"P")
            self.I = self.parameter(self,"I")
            self.D = self.parameter(self,"D")

        def get_PID(self):
            from numpy import nan
            reply = self.controller.query("PID?")
            try: P,I,D = eval(reply)
            except: return nan,nan,nan
            return P,I,D
        def set_PID(self,(P,I,D)):
            self.controller.query("PID %s,%s,%s" % (P,I,D))
        PID = property(get_PID,set_PID)

        class parameter(object):
            def __init__(self,feedback_loop,name):
                self.feedback_loop = feedback_loop
                self.name = name
            def get_value(self):
                P,I,D = self.feedback_loop.PID
                if self.name == "P": return P
                if self.name == "I": return I
                if self.name == "D": return D
                from numpy import nan
                return nan
            def set_value(self,value):
                P,I,D = self.feedback_loop.PID
                if self.name == "P": P = value
                if self.name == "I": I = value
                if self.name == "D": D = value
                self.feedback_loop.PID = P,I,D
            value = property(get_value,set_value)
            def get_moving(self): return False
            def set_moving(self,value): pass
            moving = property(get_moving,set_moving,doc="This is so it can be"
                "scanned like a motor")
            def stop(self): pass
            def __repr__(self):
                return "temperature_controller.feedback_loop."+self.name

        def __repr__(self):
            return "temperature_controller.feedback_loop"

    class status_object(object):
        """Diagnostics message"""
        def __init__(self,controller):
            self.controller = controller

        def get_value(self):
            """Diagnostics message"""
            reply = self.controller.query("OUTPUT?")
            if len(reply) == 0: return "unresponsive"
            if reply.strip() == "0": return "Off"
            if reply.strip() == "1": return "On"
            return "OUTPUT? %r" % reply
        value = property(get_value)

    @property
    def stable(self):
        """Has temperature stabilized?"""
        from numpy import array,std
        dT = self.stabilization_threshold
        nsamples = self.stabilization_nsamples
        T = array(self.readT.values[-nsamples:])
        setT = self.setT.value
        if len(T) > 0:
            stable = std(T) < dT and all(abs(T-setT) < dT)
        else: stable = False
        return stable

    stabilization_threshold  = persistent_property("stabilization_threshold",0.01)
    stabilization_nsamples  = persistent_property("stabilization_nsamples",3)

    @property
    def TIU(self):
        """Temperature, current and voltage, measured simultanously"""
        from numpy import nan
        reply = self.query("MEAS:T?; MEASure:ITE?; MEASure:VTE?")
        try: TIU = eval(reply.replace(";",","))
        except: TIU = nan,nan,nan
        return TIU

    @property
    def TIP(self):
        """Temperature, current and power, measured simultanously"""
        from numpy import nan
        reply = self.query("MEAS:T?; MEASure:ITE?; MEASure:PTE?")
        try: TIP = eval(reply.replace(";",","))
        except: TIP = nan,nan,nan
        return TIP

    def get_trigger_enabled(self):
        """Ramp temperature in external trigger?"""
        from numpy import nan
        reply = self.query("TRIGger:IN:ENABle?")
        try: value = eval(reply)
        except: value = nan
        return value
    def set_trigger_enabled(self,value):
        self.query("TRIGger:IN:ENABle %d" % toint(value))
    trigger_enabled = property(get_trigger_enabled,set_trigger_enabled)

    def get_trigger_start(self):
        """Starting value in externally triggered tempeature ramp"""
        from numpy import nan
        reply = self.query("TRIGger:IN:START?")
        try: value = eval(reply)
        except: value = nan
        return value
    def set_trigger_start(self,value):
        self.query("TRIGger:IN:START %r" % value)
    trigger_start = property(get_trigger_start,set_trigger_start)

    def get_trigger_stop(self):
        """Starting value in externally triggered tempeature ramp"""
        from numpy import nan
        reply = self.query("TRIGger:IN:STOP?")
        try: value = eval(reply)
        except: value = nan
        return value
    def set_trigger_stop(self,value):
        self.query("TRIGger:IN:STOP %r" % value)
    trigger_stop = property(get_trigger_stop,set_trigger_stop)

    # When ramping from 20C to 80C, TRIGger:IN:STOP needs to be 20, and
    # TRIGger:IN:START 80, otherwise the temperature wraps jumps back to 20
    # after it reaches 80.
    ramp_from = trigger_stop
    ramp_to = trigger_start

    def get_trigger_stepsize(self):
        """Starting value in externally triggered tempeature ramp"""
        from numpy import nan
        reply = self.query("TRIGger:IN:STEPsize?")
        try: value = eval(reply)
        except: value = nan
        return value
    def set_trigger_stepsize(self,value):
        self.query("TRIGger:IN:STEPsize %r" % value)
    trigger_stepsize = property(get_trigger_stepsize,set_trigger_stepsize)

    def get_current_low_limit(self):
        """TE current limit"""
        from numpy import nan
        reply = self.query("LIMit:ITE:LOw?")
        try: value = eval(reply)
        except: value = nan
        return value
    def set_current_low_limit(self,value):
        self.query("LIMit:ITE:LOw %r" % value)
    current_low_limit = property(get_current_low_limit,set_current_low_limit)

    def get_current_high_limit(self):
        """TE current limit"""
        from numpy import nan
        reply = self.query("LIMit:ITE:HIgh?")
        try: value = eval(reply)
        except: value = nan
        return value
    def set_current_high_limit(self,value):
        self.query("LIMit:ITE:HIgh %r" % value)
    current_high_limit = property(get_current_high_limit,set_current_high_limit)

    def get_errors(self):
        """Reset error state"""
        return self.query("ERRors?")
    def set_errors(self,value): pass
    errors = property(get_errors,set_errors)

    def get_clear_error(self):
        """Reset error state"""
        return False
    def set_clear_error(self,value):
        if value: self.query("*CLS")
    clear_error = property(get_clear_error,set_clear_error)

    def log(self,message):
        """For non-critical messages.
        Append the message to the transcript, if verbose logging is enabled."""
        if not self.verbose_logging: return
        if len(message) == 0 or message[-1] != "\n": message += "\n"
        t = timestamp()
        file(self.logfile,"a").write("%s: %s" % (t,message))

    def log_error(self,message):
        """For error messages.
        Display the message and append it to the error log file.
        If verbose logging is enabled, it is also added to the transcript."""
        from sys import stderr
        if len(message) == 0 or message[-1] != "\n": message += "\n"
        t = timestamp()
        stderr.write("%s: %s" % (t,message))
        file(self.error_logfile,"a").write("%s: %s" % (t,message))
        if self.verbose_logging:
            file(self.logfile,"a").write("%s: %s" % (t,message))

    logging = False

    def log_comm(self,message):
        """For error messages.
        Display the message and append it to the error log file.
        If verbose logging is enabled, it is also added to the transcript."""
        if self.logging:
            if len(message) == 0 or message[-1] != "\n": message += "\n"
            t = timestamp()
            file(self.comm_logfile,"a").write("%s: %s" % (t,message))

    def get_logfile(self):
        """File name for transcript if verbose logging is enabled."""
        from tempfile import gettempdir
        return gettempdir()+"/temperature_controller.log"
    logfile = property(get_logfile)

    def get_error_logfile(self):
        """File name error messages."""
        from tempfile import gettempdir
        return gettempdir()+"/temperature_controller_error.log"
    error_logfile = property(get_error_logfile)

    def get_comm_logfile(self):
        """File name error messages."""
        from tempfile import gettempdir
        return gettempdir()+"/temperature_controller_comm.log"
    comm_logfile = property(get_comm_logfile)

def toint(x):
    """Convert x to interger type"""
    try: return int(x)
    except: return 0

def timestamp():
    """Current date and time as formatted ASCCI text, precise to 1 ms"""
    from datetime import datetime
    timestamp = str(datetime.now())
    return timestamp[:-3] # omit microsconds

temperature_controller = TemperatureController()
# Define some shortcuts.
SampleT = temperature_controller
temperature = temperature_controller.temperature
set_point = temperature_controller.nominal_temperature
power = temperature_controller.power

def test_ramp():
    from time import sleep
    from numpy import arange
    fail_count = 0
    T0 = set_point.value
    for T in arange(4,111,0.871):
        set_point.value = T
        setT = set_point.value
        print T,setT,abs(setT-T)
        if abs(setT - T) > 0.0005: fail_count += 1
    if fail_count: print "failed %d times" % fail_count
    set_point.value = T0

if __name__ == "__main__":
    """For testing"""
    import logging; logging.basicConfig(level=logging.DEBUG)
    from time import time,sleep
    temperature_controller.logging = True
    self = temperature_controller
    print('self.stabilization_nsamples')
    ##print('temperature_controller["SET:TEMP"]')
    ##print('temperature_controller["MEAS:T"]')
