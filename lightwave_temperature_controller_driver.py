"""
# ILX Lightwave LDT-5948 Precision Temperature Controller

Communication Parameters: 115200 baud, 8 data bits, 1 stop bit, parity: none
flow control: none
2 = TxD, 3 = RxD, 5 = Gnd (DCE = Data Circuit-terminating Equipment)
9600 baud is the factory setting, but can be changed from the front panel:
MAIN/LOCAL - COMMUNICATION 1/7 - down - RS323 Baud
Possible baud rates are: 1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200,
and 230400.

The controller accepts ASCII text commands. Each command needs to by terminated
with a newline or carriage return character.
Replies are terminated with carriage return and newline.
Command that are not queries generate the reply "Ready".
If a query is not understood, the controller replies with "Ready" as well.

Commands:
*IDN? identification, expecting: "ILX Lightwave,LDT-5948,59481287,01.02.06"
MEASURE:Temp? - Report the actual temperature.
SET:Temp?     - Report the temperature set point.
SET:Temp 37.0 - Change temperature set point to 37 degrees C.
MEASURE:PTE?  - Read heater power in W

Cabling: Instrumentation MacBook -> USB-Serial cable ->
temperature controller

Documentation:
LDT-5900 Series Temperature Controllers User's Guide
www.newport.com/medias/sys_master/images/images/h75/h4e/8797193273374/LDT-59XX-User-Manual.pdf

Authors: Friedrich Schotte, Valentyn Stadnytskyi
Date created: 14 Dec 2009
Date last modified: 2021-04-21
Revision comment: Fixed: Issue: PID must be of type float
"""
__version__ = "3.2.4"

from logging import warning, debug, info
from persistent_property import persistent_property


def instantiate(x):
    return x()


class Lightwave_Temperature_Controller(object):
    """ILX Lightwave LDT-5948 precision temperature controller"""
    name = "lightwave_temperature_controller"
    verbose_logging = True
    last_reply_time = 0.0
    max_time_between_replies = 0.0

    def __init__(self):
        # Make multithreading safe
        from threading import RLock
        self.__lock__ = RLock()

        # When read, read actual temperature, when changed, change set point.
        self.actual_temperature = self.property_object(self, "MEAS:T", unit="C",
                                                       name="Temperature")
        self.nominal_temperature = self.property_object(self, "SET:TEMP", unit="C",
                                                        name="set-point")
        self.heating_power = self.property_object(self, "MEASURE:PTE", unit="W",
                                                  name="power")
        self.current = self.property_object(self, "MEASURE:ITE", unit="A",
                                            name="current")
        self.voltage = self.property_object(self, "MEASURE:VTE", unit="V",
                                            name="voltage")
        # enabled: Is the feed-back loop for regulating the temperature active?
        self.enabled = self.property_object(self, "OUTPUT", unit="",
                                            name="enabled")
        self.Tmin = self.property_object(self, "LIMIT:TEMP:LOW", unit="C",
                                         name="low-limit")
        self.Tmax = self.property_object(self, "LIMIT:TEMP:HIGH", unit="C",
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

    def get(self, name):
        """Query the numeric value of a parameter.
        name: e.g. 'SET:TEMP'"""
        from numpy import nan
        try:
            value = float(self.query(name + "?"))
        except ValueError:
            value = nan
        if abs(value) >= 9.8e+37:
            value = nan
        # self.record_value(name,value)
        return value

    def set(self, name, value):
        """Change the value of a parameter.
        name: e.g. 'SET:TEMP'"""
        self.query("%s %s" % (name, value))

    def __getitem__(self, name):
        """Usage: lightwave_temperature_controller['SET:TEMP']"""
        return self.get(name)

    def __setitem__(self, name, value):
        """Usage: lightwave_temperature_controller['SET:TEMP'] = 22.0"""
        self.set(name, value)

    def query(self, command):
        """Send a command to the controller and return the reply"""
        if not command.endswith("\n"):
            command = command + "\n"
        with self.__lock__:  # multithreading safe
            for attempts in range(0, 3):
                reply = self.__query__(command)
                error = "?" in command and "Ready" in reply
                if not error:
                    break
                from time import sleep
                sleep(0.1)
        reply = reply.rstrip("\r\n")
        return reply

    def __query__(self, command):
        """Send a command to the controller and return the reply"""
        self.write(command)
        reply = self.readline()
        return reply

    def write(self, command):
        """Send a command to the controller"""
        self.discover_port()
        command = command.encode('Latin-1')
        if self.port is not None:
            self.port.write(command)
            debug("Sent %r" % command)

    def readline(self):
        """Read a reply from the controller,
        terminated with either new line or carriage return"""
        from time import time
        if self.port is not None:
            try:
                reply = self.port.readline()
            except Exception as msg:
                warning("readline: %s" % msg)
                reply = b""
            debug("Read %r" % reply)
        else:
            reply = b""
        if reply:
            t = time()
            self.max_time_between_replies = max(t - self.last_reply_time, self.max_time_between_replies)
            self.last_reply_time = t
        reply = reply.decode("Latin-1")
        return reply

    discover_time = 0

    def discover_port(self):
        """To do before communicating with the controller"""
        from serial import Serial
        from serial_ports import serial_ports
        from time import time

        if self.port is not None:
            try:
                self.port.write(self.id_query)
                reply = self.port.readline()
                if self.id_string not in reply:
                    debug("Port %s: %r: reply %r" % (self.__port_name__, self.id_query, reply))
                    info("Port %s: lost connection" % self.__port_name__)
                    self.port = None
                    self.__port_name__ = ""
            except Exception as msg:
                debug("%s: %s" % (Exception, msg))
                self.port = None
                self.__port_name__ = ""

        if self.port is None:
            if time() - self.discover_time > 1.0:
                for port_name in serial_ports():
                    debug(f"Trying port {port_name}...")
                    try:
                        port = Serial(port_name, timeout=self.comm_timeout)
                        try:
                            port.baudrate = self.baudrate.value
                        except OSError as x:
                            warning(f"{port_name}: Baud rate {self.baudrate.value}: {x}")
                        port.write(self.id_query)
                        reply = port.readline()
                        debug("Port %s: %r: reply %r" % (port_name, self.id_query, reply))
                        if self.id_reply_valid(reply):
                            self.port = port
                            self.__port_name__ = port_name
                            info("Port %s: found %s" % (port_name, self.id_string))
                            break
                    except Exception as x:
                        debug(f"{x}")
                    self.discover_time = time()

    id_query = b"*IDN?\n"

    id_string = b"LDT-5948"

    def id_reply_valid(self, reply):
        valid = self.id_string in reply
        debug("Reply %r valid? %r" % (reply, valid))
        return valid

    port = None
    __port_name__ = ""

    def get_port_name(self):
        """Serial port device filename"""
        self.discover_port()
        return self.__port_name__

    def set_port_name(self, value):
        pass

    port_name = property(get_port_name, set_port_name)

    def get_id(self):
        return self.query("*IDN?")

    def set_id(self, value):
        pass

    id = property(get_id, set_id)

    @instantiate
    class baudrate(object):
        """Serial port EPICS record name"""
        name = "temperature_controller.baudrate"
        value = persistent_property("value", 57600)

    def get_comm_timeout(self):
        """For scans, to provide feedback whether the temperature 'motor'
        is still 'moving'"""
        from DB import dbget
        s = dbget("lightwave_temperature_controller.temperature.comm_timeout")
        try:
            return float(s)
        except ValueError:
            return 0.2

    def set_comm_timeout(self, value):
        from DB import dbput
        dbput("lightwave_temperature_controller.temperature.comm_timeout", str(value))

    comm_timeout = property(get_comm_timeout, set_comm_timeout)

    class temperature_object(object):
        """For logging and scanning, can be used as counter"""
        unit = "C"
        name = "Temp."

        def __init__(self, controller):
            self.controller = controller
            self.last_change = 0
            # Define shortcuts
            self.T = self.controller.actual_temperature
            self.setT = self.controller.nominal_temperature

        def get_value(self):
            return self.T.value

        def set_value(self, value):
            from time import time
            self.controller.enabled.value = True
            old_value = self.setT.value
            self.setT.value = value
            if value != old_value:
                self.last_change = time()

        value = property(get_value, set_value)

        @property
        def values(self):
            return self.T.values

        @property
        def timestamps(self):
            return self.T.timestamps

        @property
        def RMS(self):
            return self.T.RMS

        @property
        def average(self):
            return self.T.average

        def get_moving(self):
            """Has the actual temperature not yet reached the set point within
            tolerance?
            For scans, to provide feedback whether the temperature 'motor'
            is still 'moving'"""
            return self.T.moving

        def set_moving(self, moving):
            """If value = False, cancel the current temperature ramp."""
            if not moving:
                if abs(self.setT.value - self.T.value) > self.tolerance:
                    self.setT.value = self.T.value

        moving = property(get_moving, set_moving)

        def stop(self):
            """Cancel the current temperature ramp."""
            self.moving = False

        def get_timeout(self):
            """For scans, to provide feedback whether the temperature 'motor'
            is still 'moving'"""
            from DB import dbget
            s = dbget("lightwave_temperature_controller.temperature.moving_timeout")
            try:
                return float(s)
            except ValueError:
                return 0.0

        def set_timeout(self, value):
            from DB import dbput
            dbput("lightwave_temperature_controller.temperature.moving_timeout", str(value))

        timeout = property(get_timeout, set_timeout)

        def get_tolerance(self):
            """For scans, to provide feedback whether the temperature 'motor'
            is still 'moving'"""
            from DB import dbget
            s = dbget("lightwave_temperature_controller.temperature.tolerance")
            try:
                return float(s)
            except ValueError:
                return 3.0

        def set_tolerance(self, value):
            from DB import dbput
            dbput("lightwave_temperature_controller.temperature.tolerance", str(value))

        tolerance = property(get_tolerance, set_tolerance)

        def __repr__(self):
            return "lightwave_temperature_controller.temperature_object"

    class property_object(object):
        """For logging and scanning, can be used as counter"""
        from numpy import array
        timestamps = array([])
        values = array([])
        # How long is the temperature log, in seconds?
        history_length = persistent_property("history_length", 300)
        # Criteria for deciding whether the temperature has stabilized.
        stabilization_time = persistent_property("stabilization_time", 0.0)  # seconds
        stabilization_RMS = persistent_property("stabilization_RMS", 0.0)

        def __init__(self, controller, read, unit="", name="", write=""):
            """read: e.g. 'SET:TEMP?'.
            If write is omitted, will use 'SET:TEMP' to write."""
            self.controller = controller
            self.read = read
            self.unit = unit
            self.name = name
            self.write = write
            if not self.read.endswith("?"):
                self.read += "?"
            if self.write == "":
                self.write = self.read.rstrip("?")
            # To make history multi-thread safe
            from threading import RLock
            self.lock = RLock()

        def get_value(self):
            from numpy import nan
            try:
                value = float(self.controller.query(self.read))
            except ValueError:
                value = nan
            if abs(value) >= 9.8e+37:
                value = nan
            self.record_value(value)
            return value

        def set_value(self, value):
            self.controller.query("%s %s" % (self.write, value))

        value = property(get_value, set_value)

        def record_value(self, value):
            with self.lock:  # needs to be multi-thread safe
                from time import time
                from numpy import concatenate
                timestamp = time()
                # Make sure values and timestamp have the same length (FS Oct 29, 2016)
                N = min(len(self.values), len(self.timestamps))
                self.values, self.timestamps = self.values[0:N], self.timestamps[0:N]
                # Discard old values.
                keep = self.timestamps >= timestamp - self.history_length
                self.values, self.timestamps = self.values[keep], self.timestamps[keep]
                # Ignore duplicates.
                if len(self.values) > 0 and value == self.values[-1]:
                    return
                self.values = concatenate((self.values, [value]))
                self.timestamps = concatenate((self.timestamps, [timestamp]))

        @property
        def average(self):
            from time import time
            from numpy import average, nan
            dt = self.stabilization_time
            values = self.values[self.timestamps > time() - dt]
            average = average(values) if len(values) > 0 else nan
            return average

        @property
        def RMS(self):
            from time import time
            from numpy import std, nan
            dt = self.stabilization_time
            values = self.values[self.timestamps > time() - dt]
            RMS = std(values) if len(values) > 0 else nan
            return RMS

        def get_moving(self):
            """Has the value been stable for some time?"""
            moving = self.RMS > self.stabilization_RMS
            return moving

        def set_moving(self, value):
            pass

        moving = property(get_moving, set_moving, doc="This is so it can be"
                                                      "scanned like a motor")

        def stop(self):
            pass

    class feedback_loop_object(object):
        """Feedback loop parameters.
        P = proportional feedback constant
        I = integral feedback constant
        D = differential  feedback constant"""

        def __init__(self, controller):
            """name: one of "P","I","D" """
            self.controller = controller
            self.unit = ""
            self.P = self.parameter(self, "P")
            self.I = self.parameter(self, "I")
            self.D = self.parameter(self, "D")

        def get_PID(self):
            from numpy import nan
            reply = self.controller.query("PID?")
            try:
                P, I, D = eval(reply)
            except Exception as x:
                warning(f"{reply!r}: {x}")
                P, I, D = nan, nan, nan
            P, I, D = float(P), float(I), float(D)
            P, I, D = round(P, 4), round(I, 4), round(D, 4)
            return P, I, D

        def set_PID(self, PID):
            P = PID[0]
            I = PID[1]
            D = PID[2]
            self.controller.query("PID %s,%s,%s" % (P, I, D))

        PID = property(get_PID, set_PID)

        class parameter(object):
            def __init__(self, feedback_loop, name):
                self.feedback_loop = feedback_loop
                self.name = name

            def get_value(self):
                P, I, D = self.feedback_loop.PID
                if self.name == "P":
                    return P
                if self.name == "I":
                    return I
                if self.name == "D":
                    return D
                from numpy import nan
                return nan

            def set_value(self, value):
                P, I, D = self.feedback_loop.PID
                if self.name == "P":
                    P = value
                if self.name == "I":
                    I = value
                if self.name == "D":
                    D = value
                self.feedback_loop.PID = P, I, D

            value = property(get_value, set_value)

            def get_moving(self):
                return False

            def set_moving(self, value):
                pass

            moving = property(get_moving, set_moving, doc="This is so it can be"
                                                          "scanned like a motor")

            def stop(self):
                pass

            def __repr__(self):
                return "lightwave_temperature_controller.feedback_loop." + self.name

        def __repr__(self):
            return "lightwave_temperature_controller.feedback_loop"

    class status_object(object):
        """Diagnostics message"""

        def __init__(self, controller):
            self.controller = controller

        def get_value(self):
            """Diagnostics message"""
            reply = self.controller.query("OUTPUT?")
            if len(reply) == 0:
                return "unresponsive"
            if reply.strip() == "0":
                return "Off"
            if reply.strip() == "1":
                return "On"
            return "OUTPUT? %r" % reply

        value = property(get_value)

    @property
    def stable(self):
        """Has temperature stabilized?"""
        from numpy import array, std, all
        dT = self.stabilization_threshold
        nsamples = self.stabilization_nsamples
        T = array(self.readT.values[-nsamples:])
        setT = self.setT.value
        if len(T) > 0:
            stable = std(T) < dT and all(abs(T - setT) < dT)
        else:
            stable = False
        return stable

    stabilization_threshold = persistent_property("stabilization_threshold", 0.01)
    stabilization_nsamples = persistent_property("stabilization_nsamples", 3)

    @property
    def TIU(self):
        """Temperature, current and voltage, measured simultaneously"""
        from numpy import nan
        reply = self.query("MEAS:T?; MEASURE:ITE?; MEASURE:VTE?")
        try:
            TIU = eval(reply.replace(";", ","))
        except Exception:
            TIU = nan, nan, nan
        return TIU

    @property
    def TIP(self):
        """Temperature, current and power, measured simultaneously"""
        from numpy import nan
        reply = self.query("MEAS:T?; MEASURE:ITE?; MEASURE:PTE?")
        try:
            TIP = eval(reply.replace(";", ","))
        except Exception:
            TIP = nan, nan, nan
        return TIP

    def get_trigger_enabled(self):
        """Ramp temperature in external trigger?"""
        from numpy import nan
        reply = self.query("TRIGGER:IN:ENABle?")
        try:
            value = eval(reply)
        except Exception:
            value = nan
        return value

    def set_trigger_enabled(self, value):
        self.query("TRIGGER:IN:ENABle %d" % to_int(value))

    trigger_enabled = property(get_trigger_enabled, set_trigger_enabled)

    def get_trigger_start(self):
        """Starting value in externally triggered temperature ramp"""
        from numpy import nan
        reply = self.query("TRIGGER:IN:START?")
        try:
            value = eval(reply)
        except Exception:
            value = nan
        return value

    def set_trigger_start(self, value):
        self.query("TRIGGER:IN:START %r" % value)

    trigger_start = property(get_trigger_start, set_trigger_start)

    def get_trigger_stop(self):
        """Starting value in externally triggered temperature ramp"""
        from numpy import nan
        reply = self.query("TRIGGER:IN:STOP?")
        try:
            value = eval(reply)
        except Exception:
            value = nan
        return value

    def set_trigger_stop(self, value):
        self.query("TRIGGER:IN:STOP %r" % value)

    trigger_stop = property(get_trigger_stop, set_trigger_stop)

    # When ramping from 20C to 80C, TRIGGER:IN:STOP needs to be 20, and
    # TRIGGER:IN:START 80, otherwise the temperature wraps jumps back to 20
    # after it reaches 80.
    ramp_from = trigger_stop
    ramp_to = trigger_start

    def get_trigger_stepsize(self):
        """Starting value in externally triggered temperature ramp"""
        from numpy import nan
        reply = self.query("TRIGGER:IN:STEPSIZE?")
        try:
            value = eval(reply)
        except Exception:
            value = nan
        return value

    def set_trigger_stepsize(self, value):
        self.query("TRIGGER:IN:STEPSIZE %r" % value)

    trigger_stepsize = property(get_trigger_stepsize, set_trigger_stepsize)

    def get_current_low_limit(self):
        """TE current limit"""
        from numpy import nan
        reply = self.query("LIMIT:ITE:LOw?")
        try:
            value = eval(reply)
        except Exception:
            value = nan
        return value

    def set_current_low_limit(self, value):
        self.query("LIMIT:ITE:LOw %r" % value)

    current_low_limit = property(get_current_low_limit, set_current_low_limit)

    def get_current_high_limit(self):
        """TE current limit"""
        from numpy import nan
        reply = self.query("LIMIT:ITE:HIGH?")
        try:
            value = eval(reply)
        except Exception:
            value = nan
        return value

    def set_current_high_limit(self, value):
        self.query("LIMIT:ITE:HIGH %r" % value)

    current_high_limit = property(get_current_high_limit, set_current_high_limit)

    @property
    def get_errors(self):
        """Reset error state"""
        return self.query("ERRORS?")

    @property
    def clear_error(self):
        """Reset error state"""
        return False

    @clear_error.setter
    def clear_error(self, value):
        if value:
            self.query("*CLS")

    logging = False


def to_int(x):
    """Convert x to integer type"""
    try:
        return int(x)
    except (ValueError, TypeError):
        return 0


def timestamp():
    """Current date and time as formatted ASCII text, precise to 1 ms"""
    from datetime import datetime
    timestamp = str(datetime.now())
    return timestamp[:-3]  # omit microseconds


lightwave_temperature_controller = Lightwave_Temperature_Controller()
# Define some shortcuts.
SampleT = lightwave_temperature_controller
temperature = lightwave_temperature_controller.temperature
set_point = lightwave_temperature_controller.nominal_temperature
power = lightwave_temperature_controller.power

if __name__ == "__main__":
    """For testing"""
    import logging

    msg_format = "%(asctime)s %(levelname)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    lightwave_temperature_controller.logging = True
    self = lightwave_temperature_controller
    print('self.discover_port()')
