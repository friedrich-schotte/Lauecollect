"""
This is to remote control the sample translation stage for high repetinion
rate time-resolved WAXS experiments.

The stage is a linear motor with 25 mm travel, controlled by an Aerotech
Soloist MP server motor controller with an Etherner interface.

Communication is via TCP/IP port 8000. Using ASCII text commands terminated
with newline (ASCII 10). The connection is closed automatically by the operating
system after 10 seconds of inactivity. Several connections ay be active at one
time. However, the data send by the Soloist contorller is partitoned randomly
among the concurrently open connections.

The timeout can be changed with the parameter "InetSock1ActiveTimeSec"
(default: 10)

Friedrich Schotte, NIH, 24 Sep 2008 - 6 Mar 2013
"""
__version__ = "2.5.3"

import socket # TCP/IP communication
from numpy import nan
from DB import dbput,dbget
from logging import debug

class SampleStage(object):
    """Linear motor sample translations stage for time-resolved WAXS"""
    version = __version__

    unit = "mm"
    name = "sample stage"
    verbose_logging = True
    retries = 2

    def __init__(self):
        """ip_address may be given as address:port. If :port is omitted, port
        number 8000 is assumed."""
        object.__init__(self)
        self.connection = None

    def get_address(self):
        """Internet address, followed by TCP port number,separated with colon,
        e.g. 'id14b-samplex:8000'"""
        return self.ip_address+":"+str(self.port)
    def set_address(self,address):
        if address.find(":") >= 0:
            self.ip_address = address.split(":")[0]
            self.port = int(address.split(":")[1])
        else: self.ip_address = address; self.port = 8000
    address = property(get_address,set_address)

    def get_ip_address(self):
        """Network address of Soloist constroller, as DNS name or numeric as
        string"""
        ip_address = dbget("sample_translation/ip_address")
        if ip_address == "": ip_address = "id14b-samplex.cars.aps.anl.gov"
        return ip_address
    def set_ip_address(self,value):
        dbput("sample_translation/ip_address",value)
    ip_address = property(get_ip_address,set_ip_address)

    def get_port(self):
        """TCP port number rof network connection"""
        try: return int(dbget("sample_translation/port"))
        except ValueError: return 8000
    def set_port(self,value):
        dbput("sample_translation/port",repr(value))
    port = property(get_port,set_port)

    def send(self,command):
        """Sends a ASCII text command"""
        # Command should be terminated with a newline character.
        if len(command) == 0 or command[-1] != "\n": command += "\n"

        for attempt in range(0,self.retries):
            if self.connection == None:
                self.connection = socket.socket()
                self.connection.settimeout(1)
                try: self.connection.connect((self.ip_address,self.port))
                except Exception,message:
                    self.log_error("send %r connect attempt %d/%d  failed: %s" %
                        (command,attempt+1,self.retries,message))
                    self.connection = None
                    continue
            try: self.connection.sendall(command)
            except Exception,message:
                self.log_error("send %r send attempt %d/%d  failed: %s" %
                    (command,attempt+1,self.retries,message))
                self.connection = None
                continue
            self.log("send %r" % command)
            break
        self.disconnect() # Needed?

    def query(self,command):
        """To send a command that generates a reply. Returns the reply
        without trailing carriage return."""
        # Command should be terminated with a newline character.
        if len(command) == 0 or command[-1] != "\n": command += "\n"

        reply = ""
        for attempt in range(0,self.retries):
            if self.connection == None:
                self.connection = socket.socket()
                self.connection.settimeout(1)
                try: self.connection.connect((self.ip_address,self.port))
                except Exception,message:
                    self.log_error("query %r connect attempt %d/%d  failed: %s" %
                        (command,attempt+1,self.retries,message))
                    self.connection = None
                    continue

            # Clear receive buffer of old replies.
            self.connection.settimeout(0.05)
            while True:
                try: received = self.connection.recv(1024)
                except socket.timeout: break
                except Exception,message:
                    self.log_error("query %r empty queue attempt %d/%d  failed: %s" %
                        (command,attempt+1,self.retries,message))
                    self.connection = None
                    break
            if self.connection == None: continue

            try: self.connection.sendall(command)
            except Exception,message:
                self.log_error("query %r send attempt %d/%d  failed: %s" %
                    (command,attempt+1,self.retries,message))
                self.connection = None
                continue
            self.log("send %r" % command)

            reply = ""
            self.connection.settimeout(1)
            try: received = self.connection.recv(1024)
            except socket.timeout:
                self.log_error("query %r read attempt %d/%d  timed out" %
                    (command,attempt+1,self.retries))
                continue
            except Exception,message:
                self.log_error("query %r read attempt %d/%d  failed: %s" %
                    (command,attempt+1,self.retries,message))
                self.connection = None
                continue
            reply += received

            self.connection.settimeout(0.05)
            while len(received) > 0:
                try: received = self.connection.recv(1024)
                except socket.timeout: received = ""
                reply += received
            reply = reply.strip("\n")
            self.log("recv %r" % reply)
            break
        ##self.disconnect()
        return reply

    def disconnect(self):
        """Close TCP/IP connection to controller
        (will close automatically after 10 s of no communication)"""
        self.connection = None

    def get_position(self):
        """Current position in mm"""
        reply = self.query("Current position?")
        if reply.find("Current position is ") != 0: return nan
        try: return float(reply.strip("Current position is mm."))
        except ValueError: return nan 
    def set_position(self,position):
        self.query("Go to %.5f mm." % position)
    position = property(get_position,set_position,
        doc="""current position in mm, moves the stage if assigned""")
    value = position

    def get_command_position(self):
        """Nominal target position in mm, is different from actual position
        while moving"""
        reply = self.query("Command position?")
        if reply.find("Command position is ") != 0: return nan
        try: return float(reply.strip("Command position is mm."))
        except ValueError: return nan 
    command_position = property(get_command_position,set_position,
        doc="""current position in mm, moves the stage if assigned""")

    def get_software_command_position(self):
        """Nominal target position in mm maintained in a floating point
        variable, independently from the controllers 'command position'."""
        reply = self.query("Software command position?")
        if reply.find("Software command position is ") != 0: return nan
        try: return float(reply.strip("Software command position is mm."))
        except ValueError: return nan 
    software_command_position = property(get_software_command_position,
        set_position,
        doc="""current position in mm, moves the stage if assigned""")

    def is_moving(self):
        reply = self.query("Is the stage moving?")
        if reply == "The stage is moving.": return True
        else: return False
    def set_moving(self,moving):
        if not moving: stop()
    moving = property(is_moving,set_moving,doc="""Tell whether the stage is
         currently moving. If assigned False, stops the stage.""")

    def stop(self):
        """Cancels current move (and disables external trigger)."""
        self.query("Stop.")

    def get_calibrated(self):
        reply = self.query("Is the stage calibrated?")
        if reply == "The stage is calibrated.": return True
        else: return False  
    def set_calibrated(self,calibrate):
        if calibrate and not self.is_calibrated(): self.calibrate()
    calibrated = property(get_calibrated,set_calibrated,
        doc="Has the encoder has been set to zero at the home switch? "+
          "Runs calibration if False and assigned the value True.")

    def calibrate(self):
        """Drives stage to the home switch and sets enoder to zero"""
        self.query("Calibrate the stage.")

    def is_at_high_limit(self):
        reply = self.query("Is the stage at high limit?")
        if reply == "The stage is at high limit.": return True
        else: return False  
    at_high_limit = property(fget=is_at_high_limit,
        doc="Is the stage at end of travel?")

    def is_at_low_limit(self):
        reply = self.query("Is the stage at low limit?")
        if reply == "The stage is at low limit.": return True
        else: return False
    at_low_limit = property(fget=is_at_low_limit,
        doc="Is the stage at end of travel?")

    def get_controller_stepsize(self):
        """Amplitude of motion executed on external trigger"""
        reply = self.query("Step size?")
        if reply.find("Step size is ") != 0: return nan
        try: return float(reply.strip("Step size is ."))
        except ValueError: return nan 
    def set_controller_stepsize(self,value):
        self.query("Step size is %.5f." % value)
    controller_stepsize = property(get_controller_stepsize,
        set_controller_stepsize)

    def get_trigger_enabled(self):
        """Move stage on rising edge of digital input?"""
        reply = self.query("Is trigger enabled?")
        if reply == "Trigger is enabled.": return True
        else: return False
    def set_trigger_enabled(self,enabled):
        if enabled: self.query("Enable trigger.")
        else: self.query("Disable trigger.")
    trigger_enabled = property(get_trigger_enabled,set_trigger_enabled)

    def get_timer_enabled(self):
        """Move the stage periodically, based on an internal timer?"""
        reply = self.query("Is timer enabled?")
        if reply == "Timer is enabled.": return True
        else: return False
    def set_timer_enabled(self,enabled):
        if enabled: self.query("Enable timer.")
        else: self.query("Disable timer.")
    timer_enabled = property(get_timer_enabled,set_timer_enabled)

    def get_timer_period(self):
        """At which frequency to move based on internal timer?"""
        reply = self.query("Timer period?")
        if reply.find("Timer period is ") != 0: return nan
        try: return float(reply.strip("Timer period is s."))
        except ValueError: return nan 
    def set_timer_period(self,value):
        self.query("Timer period is %.3f." % value)
    timer_period = property(get_timer_period,set_timer_period)

    def get_auto_return(self):
        reply = self.query("Does the stage return to start at end of travel?")
        if reply == "The stage returns to start at end of travel.": return True
        else: return False
    def set_auto_return(self,enabled):
        if enabled: self.query("Return to start at end of travel.")
        else: self.query("Do not return to start at end of travel.")
    auto_return = property(get_auto_return,set_auto_return,doc="On exernal"+
        " trigger, does the stage return to start when it reaches a travel limit?")

    def get_return_time(self):
        """Time needed to move from the end to the start position or the travel
        range"""
        from math import sqrt
        a = self.acceleration
        start,end = self.start_position,self.end_position
        s = abs(end-start)
        return 2*sqrt(s/a)
    def set_return_time(self,t):
        """Change the acceleration to acheive the specified return time"""
        from numpy import nan
        start,end = self.start_position,self.end_position
        s = abs(end-start)
        a = 4*s/t**2
        ##debug("sample stage: acceleration = %r" % a)
        self.acceleration = a
    return_time = property(get_return_time,set_return_time)

    def travel_time(self,start,end):
        """How long does it take to move from start to end?"""
        from math import sqrt
        a = self.acceleration
        s = abs(end-start)
        return 2*sqrt(s/a)

    def get_controller_auto_reverse(self):
        """On exernal trigger, does the stage change stepping direction when it
        reaches a travel limit?"""
        reply = self.query("Does the stage change direction at travel limits?")
        if reply == "The stage changes direction at travel limits.": return True
        else: return False
    def set_controller_auto_reverse(self,enabled):
        if enabled: self.query("Change direction at travel limits.")
        else: self.query("Do not change direction.")
    controller_auto_reverse = property(get_controller_auto_reverse,
        set_controller_auto_reverse)

    def get_controller_start_position(self):
        """Start of scan range in external trigger mode"""
        reply = self.query("Start position?")
        if reply.find("Start position is ") != 0: return nan
        reply = reply.strip("Start position is mm.")
        try: return float(reply)
        except ValueError: return nan
    def set_controller_start_position(self,value):
        self.query("Start position %g mm." % value)
    controller_start_position = property(get_controller_start_position,
        set_controller_start_position)

    def get_controller_end_position(self):
        """End of scan range in external trigger mode"""
        """Start of scan range in external trigger mode"""
        reply = self.query("End position?")
        if reply.find("End position is ") != 0: return nan
        reply = reply.strip("End position is mm.")
        try: return float(reply)
        except ValueError: return nan
    def set_controller_end_position(self,value):
        self.query("End position %g mm." % value)
    controller_end_position = property(get_controller_end_position,set_controller_end_position)

    def is_drive_enabled(self):
        reply = self.query("Is the drive enabled?")
        if reply == "The drive is enabled.": return True
        else: return False
    def set_drive_enabled(self,enabled):
        if enabled: self.query("Enable drive.")
        else: self.query("Disable drive.")
    drive_enabled = property(is_drive_enabled,set_drive_enabled,
        doc="Is feedback active and holing current applied?")

    def get_speed(self):
        reply = self.query("Top speed?")
        if reply.find("Top speed ") != 0: return nan
        try: return float(reply.strip("Top speed is mm/s."))
        except ValueError: return nan 
    def set_speed(self,speed):
        self.query("Top speed %g." % speed)
    speed = property(get_speed,set_speed,doc="Maximum speed in mm/s")

    def get_controller_acceleration(self):
        """Acceleration in non-triggered mode in mm/s"""
        reply = self.query("Acceleration?")
        if reply.find("The acceleration is ") != 0: return nan
        reply = reply[len("The acceleration is "):]
        try: return float(reply.split()[0])
        except ValueError: return nan 
    def set_controller_acceleration(self,value):
        from numpy import isnan,isinf
        if isnan(value) or isinf(value) or value <= 0: return
        self.query("Acceleration %g." % value)
    controller_acceleration = property(get_controller_acceleration,
        set_controller_acceleration)

    def get_acceleration_in_triggered_mode(self):
        reply = self.query("Acceleration in triggered mode?")
        if reply.find("The acceleration in triggered mode is ") != 0: return nan
        reply = reply[len("The acceleration in triggered mode is "):]
        try: return float(reply.split()[0])
        except ValueError: return nan 
    def set_acceleration_in_triggered_mode(self,value):
        self.query("Acceleration in triggered mode %g." % value)
    acceleration_in_triggered_mode = property(get_acceleration_in_triggered_mode,
        set_acceleration_in_triggered_mode,
        doc="Acceleration in triggered mode in mm/s")

    def get_low_limit(self):
        """end of travel in negative direction in mm"""
        reply = self.query("Low limit?")
        if reply.find("The low limit is ") != 0: return nan
        try: return float(reply.strip("The low limit is mm."))
        except ValueError: return nan 
    def set_low_limit(self,value):
        self.query("Set the low limit to %.5f mm." % value)
    low_limit = property(get_low_limit,set_low_limit)

    def get_high_limit(self):
        """end of travel in positive direction in mm"""
        reply = self.query("High limit?")
        if reply.find("The high limit is ") != 0: return nan
        try: return float(reply.strip("The high limit is mm."))
        except ValueError: return nan 
    def set_high_limit(self,value):
        self.query("Set the high limit to %.5f mm." % value)
    high_limit = property(get_high_limit,set_high_limit)

    def get_limits(self):
        """travel range in mm"""
        return self.low_limit,self.high_limit
    def set_limits(self,limits):
        self.low_limit = limits[0]
        self.high_limit = limits[1]
    limits = property(get_limits,set_limits)

    def get_trigger_count(self):
        """Number if trigger pulses detected"""
        reply = self.query("Trigger count?")
        if reply.find("The trigger count is ") != 0: return nan
        try: return int(reply.strip("The trigger count is."))
        except ValueError: return nan 
    def set_trigger_count(self,value):
        self.query("Trigger count %d." % value)
    trigger_count = property(get_trigger_count,set_trigger_count,
        doc="""Number if trigger pulses detected""")

    def get_step_count(self):
        """Number of triggered motions executed"""
        reply = self.query("Step count?")
        if reply.find("The step count is ") != 0: return nan
        try: return int(reply.strip("The step count is."))
        except ValueError: return nan 
    def set_step_count(self,value):
        self.query("Step count %d." % value)
    step_count = property(get_step_count,set_step_count,
        doc="""Number of triggered motions executed.""")

    def save_parameters(self):
        """Saves start position, end position and stepsize in the non-
        volatile memory of the controller as defaults."""
        self.query("Save parameters.")

    def get_firmware_version(self):
        reply = self.query("Software version?")
        version = reply.strip("Software version is .")
        return version
    firmware_version = property(get_firmware_version,
        doc="""Release number of software running on motion controller""")

    def get_status(self):
        """Informational message for diagnostics."""
        # Is connection still active?
        if self.connection != None:
            try: self.connection.getpeername()
            except Exception: self.connection = None
        if self.connection == None:
            self.connection = socket.socket()
            self.connection.settimeout(1)
            try: self.connection.connect((self.ip_address,self.port))
            except socket.gaierror:
                self.connection = None
                return "IP address '%s' does not exist." % self.ip_address
            except socket.timeout:
                self.connection = None
                return "unresponsive"
            except socket.error:
                self.connection = None
                return "Is %d the correct port number?" % self.port
            except Exception,message:
                self.connection = None
                return "connect: %s" % message

        try: self.connection.sendall("Software version?\n")
        except socket.timeout:
            return "timed out"
        except Exception,message:
            self.connection = None
            return "send: %s" % message
        self.log("send %r" % "Software version?\n")

        reply = ""
        self.connection.settimeout(1)
        try: received = self.connection.recv(1024)
        except socket.timeout:
            self.connection = None
            return "Is server program running on controller?"
        except Exception,message:
            self.connection = None
            return "receive %s" % message
        reply += received

        self.connection.settimeout(0.05)
        while len(received) > 0:
            try: received = self.connection.recv(1024)
            except socket.timeout: received = ""
            reply += received
        reply = reply.strip("\n")
        self.log("recv %r" % reply)

        return "OK"
    status = property(get_status)
        
    def update(self):
        """Update the step size and travel range for the current temperature"""
        self.controller_start_position = self.start_position
        self.controller_end_position = self.end_position
        self.controller_stepsize = self.stepsize
        self.controller_acceleration = self.acceleration
        self.controller_auto_reverse = self.auto_reverse

    def get_start_position(self):
        """Amplitude of motion executed on external trigger"""
        if not self.temperature_correction: return self.normal_start_position
        else: return self.temperature_corrected_start_position
    def set_start_position(self,value):
        if not self.temperature_correction: self.normal_start_position = value
        else: self.temperature_corrected_start_position = value
    start_position = property(get_start_position,set_start_position)

    def get_end_position(self):
        """Amplitude of motion executed on external trigger"""
        if not self.temperature_correction: return self.normal_end_position
        else: return self.temperature_corrected_end_position
    def set_end_position(self,value):
        if not self.temperature_correction: self.normal_end_position = value
        else: self.temperature_corrected_end_position = value
    end_position = property(get_end_position,set_end_position)

    def get_travel(self):
        """On exernal trigger, the stage is stepping between these two
        positions. (start,end) tuple"""
        return self.start_position,self.end_position
    def set_travel(self,(start,end)):
        self.start_position,self.end_position = start,end
    travel = property(get_travel,set_travel)

    def get_stepsize(self):
        """Amplitude of motion executed on external trigger"""
        if self.steps == 0: return 0.2
        if self.end_position == self.start_position: return 0.2
        return (self.end_position-self.start_position)/self.steps
    def set_stepsize(self,stepsize):
        from numpy import isnan,floor
        if isnan(stepsize): return
        if stepsize == 0: return
        self.steps = floor((self.end_position-self.start_position)/stepsize)
    stepsize = property(get_stepsize,set_stepsize)

    def get_home_position(self):
        """Used for setup and alignment"""
        try: return float(dbget("sample_translation/home"))
        except ValueError: return 0.0
    def set_home_position(self,value):
        dbput("sample_translation/home",repr(value))
    home_position = property(get_home_position,set_home_position)

    def get_park_position(self):
        """Predefined position used for data collection"""
        try: return float(dbget("sample_translation/park"))
        except ValueError: return -12.5
    def set_park_position(self,value):
        dbput("sample_translation/park",repr(value))
    park_position = property(get_park_position,set_park_position)

    def get_normal_start_position(self):
        """Start position at calibration temperature"""
        try: return float(dbget("sample_translation/start_position"))
        except ValueError: return -2.0
    def set_normal_start_position(self,value):
        dbput("sample_translation/start_position",repr(value))
    normal_start_position = property(get_normal_start_position,
        set_normal_start_position)

    def get_normal_end_position(self):
        """Start position at calibration temperature"""
        try: return float(dbget("sample_translation/end_position"))
        except ValueError: return 10.0
    def set_normal_end_position(self,value):
        dbput("sample_translation/end_position",repr(value))
    normal_end_position = property(get_normal_end_position,
        set_normal_end_position)

    def get_acceleration(self):
        """Acceleration in non-triggered mode in mm/s"""
        try: return float(dbget("sample_translation/acceleration"))
        except ValueError: return 1372.8
    def set_acceleration(self,value):
        dbput("sample_translation/acceleration",repr(value))
    acceleration = property(get_acceleration,set_acceleration)

    def get_steps(self):
        """Start position at calibration temperature"""
        try: return int(dbget("sample_translation/steps"))
        except ValueError: return 50
    def set_steps(self,value):
        from numpy import rint
        value = int(rint(value))
        dbput("sample_translation/steps",repr(value))
    steps = nsteps = property(get_steps,set_steps)

    def get_auto_reverse(self):
        try: return bool(int(dbget("sample_translation/auto_reverse")))
        except ValueError: return False
    def set_auto_reverse(self,value):
        dbput("sample_translation/auto_reverse",repr(int(value)))
    auto_reverse = property(get_auto_reverse,set_auto_reverse)

    def get_move_when_idle(self):
        """Keep moving te stage when not triggered"""
        try: return bool(int(dbget("sample_translation/move_when_idle")))
        except ValueError: return False
    def set_move_when_idle(self,value):
        dbput("sample_translation/move_when_idle",repr(int(value)))
    move_when_idle = property(get_move_when_idle,set_move_when_idle)

    def get_temperature_correction(self):
        """Use temperatrue to adjust start and end position and stepsize?"""
        try: return bool(int(dbget("sample_translation/temperature_correction")))
        except ValueError: return False
    def set_temperature_correction(self,value):
        dbput("sample_translation/temperature_correction",repr(int(value)))
    temperature_correction = property(get_temperature_correction,
        set_temperature_correction)

    def get_calibration_temperature_1(self):
        """Temperature at which 'calibrated stepsize' and
        'calibrated starting position' are the actual stepsize and starting
        positions"""
        try: return float(dbget("sample_translation/calibration_temperature_1"))
        except ValueError: return 20.0
    def set_calibration_temperature_1(self,value):
        dbput("sample_translation/calibration_temperature_1",repr(value))
    calibration_temperature_1 = property(get_calibration_temperature_1,
        set_calibration_temperature_1)

    def get_calibrated_start_position_1(self):
        """Start position at calibration temperature"""
        try: return float(dbget("sample_translation/calibrated_start_position_1"))
        except ValueError: return -2.0
    def set_calibrated_start_position_1(self,value):
        dbput("sample_translation/calibrated_start_position_1",repr(value))
    calibrated_start_position_1 = property(get_calibrated_start_position_1,
        set_calibrated_start_position_1)

    def get_calibrated_end_position_1(self):
        """Start position at calibration temperature"""
        try: return float(dbget("sample_translation/calibrated_end_position_1"))
        except ValueError: return 10.0
    def set_calibrated_end_position_1(self,value):
        dbput("sample_translation/calibrated_end_position_1",repr(value))
    calibrated_end_position_1 = property(get_calibrated_end_position_1,
        set_calibrated_end_position_1)

    def get_calibration_temperature_2(self):
        """Temperature at which 'calibrated stepsize' and
        'calibrated starting position' are the actual stepsize and starting
        positions"""
        try: return float(dbget("sample_translation/calibration_temperature_2"))
        except ValueError: return 40.0
    def set_calibration_temperature_2(self,value):
        dbput("sample_translation/calibration_temperature_2",repr(value))
    calibration_temperature_2 = property(get_calibration_temperature_2,
        set_calibration_temperature_2)

    def get_calibrated_start_position_2(self):
        """Start position at calibration temperature"""
        try: return float(dbget("sample_translation/calibrated_start_position_2"))
        except ValueError: return -2.0
    def set_calibrated_start_position_2(self,value):
        dbput("sample_translation/calibrated_start_position_2",repr(value))
    calibrated_start_position_2 = property(get_calibrated_start_position_2,
        set_calibrated_start_position_2)

    def get_calibrated_end_position_2(self):
        """Start position at calibration temperature"""
        try: return float(dbget("sample_translation/calibrated_end_position_2"))
        except ValueError: return 10.0
    def set_calibrated_end_position_2(self,value):
        dbput("sample_translation/calibrated_end_position_2",repr(value))
    calibrated_end_position_2 = property(get_calibrated_end_position_2,
        set_calibrated_end_position_2)

    def get_temperature(self):
        """In degrees Celsius. Measured by temperature controller"""
        from temperature_controller import temperature_controller
        # Use the set point for reproducebilty rather than te measured
        # temperature.
        return temperature_controller.setT.value 
    def set_temperature(self,value):
        from temperature_controller import temperature_controller
        temperature_controller.setT.value = value
    temperature = property(get_temperature,set_temperature)

    def get_temperature_corrected_start_position(self):
        """Interpolated start_position for the current temperature"""
        T = self.temperature
        T1,T2 = self.calibration_temperature_1,self.calibration_temperature_2
        x1,x2 = self.calibrated_start_position_1,self.calibrated_start_position_2
        x = x1+(x2-x1)/(T2-T1)*(T-T1)
        return x
    def set_temperature_corrected_start_position(self,x):
        offset = x - self.temperature_corrected_start_position
        self.calibrated_start_position_1 += offset
        self.calibrated_start_position_2 += offset
    temperature_corrected_start_position = property(
        get_temperature_corrected_start_position,
        set_temperature_corrected_start_position)

    def get_temperature_corrected_end_position(self):
        """Interpolated start_position for the current temperature"""
        T = self.temperature
        T1,T2 = self.calibration_temperature_1,self.calibration_temperature_2
        x1,x2 = self.calibrated_end_position_1,self.calibrated_end_position_2
        x = x1+(x2-x1)/(T2-T1)*(T-T1)
        return x
    def set_temperature_corrected_end_position(self,x):
        offset = x - self.temperature_corrected_end_position
        self.calibrated_end_position_1 += offset
        self.calibrated_end_position_2 += offset
    temperature_corrected_end_position = property(
        get_temperature_corrected_end_position,
        set_temperature_corrected_end_position)

    def log_error(self,message):
        """For error messages.
        Display the message and append it to the error log file.
        If verbose logging is enabled, it is also added to the transcript."""
        from sys import stderr
        if len(message) == 0 or message[-1] != "\n": message += "\n"
        t = timestamp()
        file(self.error_logfile,"a").write("%s: %s" % (t,message))
        ##stderr.write("%s: %s: %s" % (t,self.ip_address,message))
        ##self.log(message)

    def get_error_logfile(self):
        """File name error messages."""
        from tempfile import gettempdir
        return gettempdir()+"/sample_translation_error.log"
    error_logfile = property(get_error_logfile)

    def log(self,message):
        """For non-critical messages.
        Append the message to the transcript, if verbose logging is enabled."""
        if not self.verbose_logging: return
        if len(message) == 0 or message[-1] != "\n": message += "\n"
        t = timestamp()
        file(self.logfile,"a").write("%s: %s" % (t,message))

    def get_logfile(self):
        """File name for transcript if verbose logging is enabled."""
        from tempfile import gettempdir
        return gettempdir()+"/sample_translation.log"
    logfile = property(get_logfile)


def timestamp():
    """Current date and time as formatted ASCII text, precise to 1 ms"""
    from datetime import datetime
    timestamp = str(datetime.now())
    return timestamp[:-3] # omit microsconds


sample_stage = SampleStage()

cancelled = True # to top "run_test"
delay_time = 2.5 # to simulate detector readout
repeat_count = 4 # number of strokes before delay

def run_test():
    """Stand-alone operation simulating Lauecollect"""
    from id14 import transon,tmode,waitt,pulses,mson,laseron
    from time import sleep,time
    from numpy import rint

    global cancelled; cancelled = False
    
    # Make sure laser and X-ray are not firing
    old_laseron = laseron.value; old_mson = mson.value; old_tmode = tmode.value
    laseron.value = False; mson.value = False

    tmode.value = 1 # counted
    transon.value = 1 # Tell FPGA to output trigger pulses for stage.    
    sample_stage.trigger_enabled = True
    sample_stage.step_count = 0

    while not cancelled:
        sample_stage.timer_enabled = False
        for repeat in range(0,repeat_count):
            sample_stage.position = sample_stage.start_position
            sample_stage.update()        
            while sample_stage.moving: sleep(0.05)
            pulses.value = sample_stage.nsteps+1 # Start triggering
            wait_time = sample_stage.nsteps*waitt.value + sample_stage.return_time
            t0 = time()
            while time()-t0 < wait_time and not cancelled: sleep(0.02)
        # Either keep moving or park the stage.
        if delay_time > 0:
            if sample_stage.move_when_idle: sample_stage.timer_enabled = True
            else: sample_stage.position = sample_stage.park_position
        # Simulate delay for detector readout.
        t0 = time()
        while time()-t0 < delay_time and not cancelled: sleep(0.02)

    sample_stage.trigger_enabled = False
    pulses.value = 0
    sample_stage.position = sample_stage.park_position
    laseron.value = old_laseron; mson.value = old_mson; tmode.value = old_tmode

def start_test():
    """Start stand-alone operation simlating Lauecollect"""
    global cancelled
    cancelled = False
    from thread import start_new_thread
    start_new_thread(run_test,())

def stop_test():
    """Stop stand-alone operation simlating Lauecollect"""
    global cancelled
    cancelled = True

def test_running():
    return not cancelled


if __name__ == '__main__': # test program
    from pdb import pm
    import logging
    ##logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s")
    self = sample_stage
