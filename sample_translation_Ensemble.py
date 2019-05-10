"""
This is to remote control the sample translation stage for high repetinion
rate time-resolved WAXS experiments.

The stage is a linear motor with 25 mm travel, controlled by an Aerotech
Soloist MP server motor controller with an Etherner interface.

Friedrich Schotte, NIH, 24 Sep 2008 - 15 Nov 2014
"""
__version__ = "3.3.3"

import socket # TCP/IP communication
from numpy import nan,isnan
from DB import dbput,dbget
from logging import debug

class SampleStage(object):
    """Linear motor sample translations stage for time-resolved WAXS"""
    from Ensemble import SampleZ as motor
    from Ensemble_triggered_motion import triggered_motion
    version = __version__

    unit = "mm"
    name = "sample stage"
    verbose_logging = True

    def get_position(self):
        """Current position in mm"""
        return self.motor.value
    def set_position(self,position):
        # Change the command position of axis 2 only
        # (nan is ignored)
        self.motor.command_value = position
    position = property(get_position,set_position,
        doc="""current position in mm, moves the stage if assigned""")
    value = position

    def get_command_position(self):
        """Nominal target position in mm, is different from actual position
        while moving"""
        return self.motor.command_value 
    command_position = property(get_command_position,set_position,
        doc="""current position in mm, moves the stage if assigned""")

    def get_moving(self):
        return self.motor.moving
    def set_moving(self,value):
        if not moving: self.motor.moving = value
    moving = property(get_moving,set_moving,doc="""Tell whether the stage is
         currently moving. If assigned False, stops the stage.""")

    def stop(self):
        """Cancels current move (and disables external trigger)."""
        self.moving = False

    def get_calibrated(self):
        return self.motor.homed
    def set_calibrated(self,value):
        self.motor.home = value
    calibrated = property(get_calibrated,set_calibrated,
        doc="Has the encoder has been set to zero at the home switch? "+
          "Runs calibration if False and assigned the value True.")

    def calibrate(self):
        """Drives stage to the home switch and sets enoder to zero"""
        self.calibrated = True

    def get_at_high_limit(self):
        """Is the stage at end of travel?"""
        return self.motor.at_high_limit
    at_high_limit = property(get_at_high_limit)

    def get_at_low_limit(self):
        """Is the stage at end of travel?"""
        return self.motor.at_low_limit
    at_low_limit = property(get_at_low_limit)

    def get_trigger_enabled(self):
        """Move stage on rising edge of digital input?"""
        return self.triggered_motion.trigger_enabled
    def set_trigger_enabled(self,value):
        self.triggered_motion.trigger_enabled = value
    trigger_enabled = property(get_trigger_enabled,set_trigger_enabled)

    def get_timer_enabled(self):
        """Move the stage periodically, based on an internal timer?"""
        return self.triggered_motion.timer_enabled
    def set_timer_enabled(self,value):
        self.triggered_motion.timer_enabled = value
    timer_enabled = property(get_timer_enabled,set_timer_enabled)

    def get_timer_period(self):
        """At which frequency to move based on internal timer?"""
        return self.triggered_motion.timer_period
    def set_timer_period(self,value):
        self.triggered_motion.timer_period = value
    timer_period = property(get_timer_period,set_timer_period)

    def get_auto_return(self):
        return self.triggered_motion.auto_return
    def set_auto_return(self,value):
        self.triggered_motion.auto_return = value
    auto_return = property(get_auto_return,set_auto_return,doc="On external"+
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

    def get_enabled(self):
        """Holding current applied and feedback loop active?"""
        return self.motor.enabled
    def set_enabled(self,value):
        self.motor.enabled = value
    enabled = property(get_enabled,set_enabled)
    drive_enabled = enabled

    def get_speed(self):
        """Speed in triggered mode in mm/s"""
        return self.motor.speed
    def set_speed(self,value):
        self.motor.speed = value
    speed = property(get_speed,set_speed)

    def get_acceleration(self):
        """Acceleration in non-triggered mode in mm/s2"""
        return self.motor.acceleration
    def set_acceleration(self,value):
        self.motor.acceleration = value
    acceleration = property(get_acceleration,set_acceleration)
    acceleration_in_triggered_mode = acceleration
    
    def get_homed(self):
        """Is the axis homed?"""
        return self.motor.homed
    def set_homed(self,value):
        self.motor.homed = value
    homed = property(get_homed,set_homed)

    def get_homing(self):
        """Is the axis currently executing the "find home" calibration?"""
        return self.motor.homing
    def set_homing(self,value):
        self.motor.homing = value
    homing = property(get_homing,set_homing)

    def get_low_limit(self):
        """End of travel in negative direction in mm"""
        return self.motor.low_limit
    def set_low_limit(self,value):
        self.motor.low_limit = value
    low_limit = property(get_low_limit,set_low_limit)

    def get_high_limit(self):
        """end of travel in positive direction in mm"""
        return self.motor.high_limit
    def set_high_limit(self,value):
        self.motor.high_limit = value
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
        return self.triggered_motion.trigger_count
    def set_trigger_count(self,value):
        self.triggered_motion.trigger_count = value
    trigger_count = property(get_trigger_count,set_trigger_count,
        doc="""Number if trigger pulses detected""")

    def get_step_count(self):
        """Number of triggered motions executed"""
        return self.triggered_motion.step_count
    def set_step_count(self,value):
        self.triggered_motion.step_count = value
    step_count = property(get_step_count,set_step_count,
        doc="""Number of triggered motions executed.""")

    def get_firmware_version(self):
        return self.triggered_motion.version
    firmware_version = property(get_firmware_version,
        doc="""Release number of software running on motion controller""")

    @property
    def status(self):
        """Informational message for diagnostics."""
        try: value = self.motor.value
        except: value = nan
        if isnan(value): return "Ensemble IOC not running"
        if self.firmware_version == "":
            return "AeroBasic program not loaded on Ensemble" 
        if not self.triggered_motion.enabled:
            return "AeroBasic program not running on Ensemble"
        return "OK"
        
    @property
    def online(self):
        """Is instrument usable?"""
        try: value = self.motor.value
        except: value = nan
        return not isnan(value)

    def update(self):
        """Update the step size and travel range for the current temperature"""
        # Download positions into the controller.
        ##from numpy import array,concatenate
        ##Z = concatenate([self.positions]*self.repeats)
        self.triggered_motion.Z.enabled = 1
        self.triggered_motion.Z.trigger_divisor = 1
        self.triggered_motion.Z.relative_move = 0
        self.triggered_motion.Z.positions = self.positions
        self.triggered_motion.enabled = True

    @property
    def positions(self):
        """Where the stage stops after triggered transtation.
        list of z values."""
        # Calculate the positions.
        from numpy import arange
        stepsize = abs(self.stepsize)
        if self.end_position < self.start_position: stepsize *= -1
        nsteps = (self.end_position - self.start_position)/stepsize
        z = self.start_position+arange(0,nsteps+1)*stepsize
        return z

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
        try: return float(dbget("sample_translation.home"))
        except ValueError: return 0.0
    def set_home_position(self,value):
        dbput("sample_translation.home",repr(value))
    home_position = property(get_home_position,set_home_position)

    def get_park_position(self):
        """Predefined position used for data collection"""
        try: return float(dbget("sample_translation.park"))
        except ValueError: return -12.5
    def set_park_position(self,value):
        dbput("sample_translation.park",repr(value))
    park_position = property(get_park_position,set_park_position)

    def get_normal_start_position(self):
        """Start position at calibration temperature"""
        try: return float(dbget("sample_translation.start_position"))
        except ValueError: return -2.0
    def set_normal_start_position(self,value):
        dbput("sample_translation.start_position",repr(value))
    normal_start_position = property(get_normal_start_position,
        set_normal_start_position)

    def get_normal_end_position(self):
        """Start position at calibration temperature"""
        try: return float(dbget("sample_translation.end_position"))
        except ValueError: return 10.0
    def set_normal_end_position(self,value):
        dbput("sample_translation.end_position",repr(value))
    normal_end_position = property(get_normal_end_position,
        set_normal_end_position)

    def get_steps(self):
        """Start position at calibration temperature"""
        try: return int(dbget("sample_translation.steps"))
        except ValueError: return 50
    def set_steps(self,value):
        from numpy import rint
        value = int(rint(value))
        dbput("sample_translation.steps",repr(value))
    steps = nsteps = property(get_steps,set_steps)

    def get_auto_reverse(self):
        try: return bool(int(dbget("sample_translation.auto_reverse")))
        except ValueError: return False
    def set_auto_reverse(self,value):
        dbput("sample_translation.auto_reverse",repr(int(value)))
    auto_reverse = property(get_auto_reverse,set_auto_reverse)

    def get_move_when_idle(self):
        """Keep moving te stage when not triggered"""
        try: return bool(int(dbget("sample_translation.move_when_idle")))
        except ValueError: return False
    def set_move_when_idle(self,value):
        dbput("sample_translation.move_when_idle",repr(int(value)))
    move_when_idle = property(get_move_when_idle,set_move_when_idle)

    def get_temperature_correction(self):
        """Use temperatrue to adjust start and end position and stepsize?"""
        try: return bool(int(dbget("sample_translation.temperature_correction")))
        except ValueError: return False
    def set_temperature_correction(self,value):
        dbput("sample_translation.temperature_correction",repr(int(value)))
    temperature_correction = property(get_temperature_correction,
        set_temperature_correction)

    def get_calibration_temperature_1(self):
        """Temperature at which 'calibrated stepsize' and
        'calibrated starting position' are the actual stepsize and starting
        positions"""
        try: return float(dbget("sample_translation.calibration_temperature_1"))
        except ValueError: return 20.0
    def set_calibration_temperature_1(self,value):
        dbput("sample_translation.calibration_temperature_1",repr(value))
    calibration_temperature_1 = property(get_calibration_temperature_1,
        set_calibration_temperature_1)

    def get_calibrated_start_position_1(self):
        """Start position at calibration temperature"""
        try: return float(dbget("sample_translation.calibrated_start_position_1"))
        except ValueError: return -2.0
    def set_calibrated_start_position_1(self,value):
        dbput("sample_translation.calibrated_start_position_1",repr(value))
    calibrated_start_position_1 = property(get_calibrated_start_position_1,
        set_calibrated_start_position_1)

    def get_calibrated_end_position_1(self):
        """Start position at calibration temperature"""
        try: return float(dbget("sample_translation.calibrated_end_position_1"))
        except ValueError: return 10.0
    def set_calibrated_end_position_1(self,value):
        dbput("sample_translation.calibrated_end_position_1",repr(value))
    calibrated_end_position_1 = property(get_calibrated_end_position_1,
        set_calibrated_end_position_1)

    def get_calibration_temperature_2(self):
        """Temperature at which 'calibrated stepsize' and
        'calibrated starting position' are the actual stepsize and starting
        positions"""
        try: return float(dbget("sample_translation.calibration_temperature_2"))
        except ValueError: return 40.0
    def set_calibration_temperature_2(self,value):
        dbput("sample_translation.calibration_temperature_2",repr(value))
    calibration_temperature_2 = property(get_calibration_temperature_2,
        set_calibration_temperature_2)

    def get_calibrated_start_position_2(self):
        """Start position at calibration temperature"""
        try: return float(dbget("sample_translation.calibrated_start_position_2"))
        except ValueError: return -2.0
    def set_calibrated_start_position_2(self,value):
        dbput("sample_translation.calibrated_start_position_2",repr(value))
    calibrated_start_position_2 = property(get_calibrated_start_position_2,
        set_calibrated_start_position_2)

    def get_calibrated_end_position_2(self):
        """Start position at calibration temperature"""
        try: return float(dbget("sample_translation.calibrated_end_position_2"))
        except ValueError: return 10.0
    def set_calibrated_end_position_2(self,value):
        dbput("sample_translation.calibrated_end_position_2",repr(value))
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

    def get_repeats(self):
        """Start position at calibration temperature"""
        try: return int(dbget("sample_translation.repeats"))
        except ValueError: return 1
    def set_repeats(self,value):
        dbput("sample_translation.repeats",repr(value))
    repeats = property(get_repeats,set_repeats)

    @property
    def address(self):
        """Network identifier"""
        return ""

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
delay_time = 0 # 2.5 to simulate detector readout
repeat_count = 4 # number of strokes before delay

def run_test():
    """Stand-alone operation simulating Lauecollect"""
    from instrumentation import transon,tmode,waitt,pulses,mson,laseron
    from time import sleep,time
    from numpy import rint

    global cancelled; cancelled = False

    # Make sure laser and X-ray are not firing
    old_laseron = laseron.value; old_mson = mson.value; old_tmode = tmode.value
    laseron.value = False; mson.value = False

    tmode.value = 1 # counted
    transon.value = 1 # Tell FPGA to output trigger pulses for stage.    
    sample_stage.timer_enabled = False
    sample_stage.update()        
    sample_stage.step_count = 1
    sample_stage.position = sample_stage.start_position
    while sample_stage.moving: sleep(0.05)
    sample_stage.trigger_enabled = True

    while not cancelled and sample_stage.homed:
        pulses.value = sample_stage.nsteps+1 # Start triggering
        wait_time = sample_stage.nsteps*waitt.value + sample_stage.return_time\
            + 0.2
        t0 = time()
        while time()-t0 < wait_time and not cancelled: sleep(0.02)

    if not sample_stage.homed: cancelled = True
    
    sample_stage.trigger_enabled = False
    pulses.value = 0
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
    sample_stage.trigger_enabled = False
    from instrumentation import pulses
    pulses.value = 0

def test_running():
    return not cancelled


if __name__ == '__main__': # test program
    from pdb import pm
    import logging
    ##logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s")
    self = sample_stage
    print 'self.update()'
    print 'self.triggered_motion.pos'
