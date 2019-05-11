"""Aerotech Ensemble Motion Controller
Communication via Aeroch's C library interface using a proprietary
protocol by Aerotech.
Friedrich Schotte, NIH, 26 Oct 2013 - 12 Jul 2014"""

__version__ = "1.5"

from CA import caget,caput

class Ensemble_motor(object):
    """Individual axes if the Aerotech Ensemble multi-axis controller"""
    # 'stepsize' is to strip unnecessary digits after the decimal point that
    # arise from float32 to float64 conversion.
    stepsize = 0.0
    
    def __init__(self,motor_number,**kwargs):
        self.motor_number = motor_number
        for key in kwargs: setattr(self,key,kwargs[key])

    def get_command_dial(self):
        """Target position in dial units"""
        n = self.motor_number
        value = tofloat(caget("NIH:ENSEMBLE.command_dial_values[%d]" % n))
        value = round_next(value,self.stepsize)
        return value
    def set_command_dial(self,value):
        from numpy import isnan
        if isnan(value): return
        n = self.motor_number
        caput("NIH:ENSEMBLE.command_dial_values[%d]" % n,value)
    command_dial = property(get_command_dial,set_command_dial)

    def get_dial(self):
        """Current position in dial units"""
        n = self.motor_number
        value = tofloat(caget("NIH:ENSEMBLE.dial_values[%d]" % n))
        value = round_next(value,self.stepsize)
        return value
    def set_dial(self,value): self.set_command_dial(value)
    dial = property(get_dial,set_dial)

    def get_command_value(self):
        """Target position in user units"""
        n = self.motor_number
        value = tofloat(caget("NIH:ENSEMBLE.command_values[%d]" % n))
        value = round_next(value,self.stepsize)
        return value
    def set_command_value(self,value):
        from numpy import isnan
        if isnan(value): return
        n = self.motor_number
        caput("NIH:ENSEMBLE.command_values[%d]" % n,value)
    command_value = property(get_command_value,set_command_value)
        
    def get_value(self):
        """Current position in user units"""
        n = self.motor_number
        value = tofloat(caget("NIH:ENSEMBLE.values[%d]" % n))
        value = round_next(value,self.stepsize)
        return value
    value = property(get_value,set_command_value)

    def get_moving(self):
        """Target position"""
        n = self.motor_number
        return tobool(caget("NIH:ENSEMBLE.moving[%d]" % n))
    def set_moving(self,value):
        n = self.motor_number
        caput("NIH:ENSEMBLE.moving[%d]" % n,value)
    moving = property(get_moving,set_moving)

    unit = "mm"
    name = "Ensemble"
    has_home = False

    def stop():
        """If the motor is moving, abort the current move."""
        self.moving = False

    def wait(self):
        """If the motor is moving, returns control after current move is
        complete."""
        from time import sleep
        while self.moving: sleep(0.01)

    def get_enabled(self):
        """Is holding the current turned on?"""
        n = self.motor_number
        return tobool(caget("NIH:ENSEMBLE.enabled[%d]" % n))
    def set_enabled(self,value):
        n = self.motor_number
        caput("NIH:ENSEMBLE.enabled[%d]" % n,value)
    enabled = property(get_enabled,set_enabled)

    def enable():
        """Turn the holding current on."""
        self.enabled = True

    def disable():
        """Turn the holding current off."""
        self.enabled = False

    def get_speed(self):
        """How fast does the motor move?"""
        n = self.motor_number
        return tofloat(caget("NIH:ENSEMBLE.speeds[%d]" % n))
    def set_speed(self,value):
        n = self.motor_number
        caput("NIH:ENSEMBLE.speeds[%d]" % n,value)
    speed = property(get_speed,set_speed)

    def get_homing(self):
        """Currently performing a home run?"""
        from numpy import nan
        if not self.has_home: return nan
        n = self.motor_number
        return tobool(caget("NIH:ENSEMBLE.homing[%d]" % n))
    def set_homing(self,value):
        n = self.motor_number
        caput("NIH:ENSEMBLE.homing[%d]" % n,value)
    homing = property(get_homing,set_homing)

    def home():
        """Calibrate te position by performing a home run."""
        self.homing = True

    def get_homed(self):
        """Has home run been done? Is motor calibrated?"""
        from numpy import nan
        if not self.has_home: return nan
        n = self.motor_number
        return tobool(caget("NIH:ENSEMBLE.homed[%d]" % n))
    def set_homed(self,value):
        n = self.motor_number
        caput("NIH:ENSEMBLE.homed[%d]" % n,value)
    homed = property(get_homed,set_homed)

    def get_sign(self):
        """Dial-to-user converion sign, maybe either 1 or -1"""
        n = self.motor_number
        return tofloat(caget("NIH:ENSEMBLE.signs[%d]" % n))
    def set_sign(self,value):
        n = self.motor_number
        caput("NIH:ENSEMBLE.signs[%d]" % n,value)
    sign = property(get_sign,set_sign)
    
    def get_offset(self):
        """Dial-to-user converion offset, maybe either 1 or -1"""
        from numpy import isnan
        n = self.motor_number
        return tofloat(caget("NIH:ENSEMBLE.offsets[%d]" % n))
    def set_offset(self,value):
        n = self.motor_number
        caput("NIH:ENSEMBLE.offsets[%d]" % n,value)
    offset = property(get_offset,set_offset)
    
    def get_dial_low_limit(self):
        """Soft limit. Disable soft limits by settings this value to nan"""
        n = self.motor_number
        return tofloat(caget("NIH:ENSEMBLE.dial_low_limits[%d]" % n))
    def set_dial_low_limit(self,value):
        n = self.motor_number
        caput("NIH:ENSEMBLE.dial_low_limits[%d]" % n,value)
    dial_low_limit = property(get_dial_low_limit,set_dial_low_limit)
    
    def get_dial_high_limit(self):
        """Soft limit. Disable soft limits by settings this value to nan"""
        n = self.motor_number
        return tofloat(caget("NIH:ENSEMBLE.dial_high_limits[%d]" % n))
    def set_dial_high_limit(self,value):
        n = self.motor_number
        caput("NIH:ENSEMBLE.dial_high_limits[%d]" % n,value)
    dial_high_limit = property(get_dial_high_limit,set_dial_high_limit)

    def get_low_limit(self):
        """Soft limit. Disable soft limits by settings this value to nan"""
        n = self.motor_number
        return tofloat(caget("NIH:ENSEMBLE.low_limits[%d]" % n))
    def set_low_limit(self,value):
        n = self.motor_number
        caput("NIH:ENSEMBLE.low_limits[%d]" % n,value)
    low_limit = property(get_low_limit,set_low_limit)

    def get_high_limit(self):
        """Soft limit. Disable soft limits by settings this value to nan"""
        n = self.motor_number
        return tofloat(caget("NIH:ENSEMBLE.high_limits[%d]" % n))
    def set_high_limit(self,value):
        n = self.motor_number
        caput("NIH:ENSEMBLE.high_limits[%d]" % n,value)
    high_limit = property(get_high_limit,set_high_limit)
    

def tofloat(x):
    from numpy import nan
    try: return float(x)
    except: return nan

def tobool(x):
    from numpy import nan,isnan
    if x is None: return nan
    if isnan(x): return nan
    try: return bool(x)
    except: return nan

def round_next (x,step):
    """Rounds x up or down to the next multiple of step."""
    if step == 0: return x
    x = round(x/step)*step
    # Avoid "negative zero" (-0.0), which is different from +0.0 by IEEE standard
    if x == 0: x = abs(x)
    return x


SampleX   = Ensemble_motor(0,name="Sample X"  ,unit="mm", stepsize=0.001,has_home=True)
SampleY   = Ensemble_motor(1,name="Sample Y"  ,unit="mm", stepsize=0.001,has_home=True)
SampleZ   = Ensemble_motor(2,name="Sample Z"  ,unit="mm", stepsize=0.001,has_home=True)
SamplePhi = Ensemble_motor(3,name="Sample Phi",unit="deg",stepsize=0.001,has_home=False)
PumpA     = Ensemble_motor(4,name="PumpA"     ,unit="deg",stepsize=0.001,has_home=False)
PumpB     = Ensemble_motor(5,name="PumpB"     ,unit="deg",stepsize=0.001,has_home=False)

# SampleX.sign   = -1
# SampleY.sign   = -1
# SampleZ.sign   =  1
# SamplePhi.sign = -1
# PumpA.sign     = -1
# PumpB.sign     = -1

if __name__ == "__main__":
    from numpy import nan
    self = SampleX # for debugging
