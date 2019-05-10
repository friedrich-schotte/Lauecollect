#!/usr/bin/env python
"""
Python interface for the LCLS XPP laser timing system

Laser-to-X-ray time delay + Timing Tool correction
Laser-to-X-ray time delay: electronic phase shift
Timing Tool correction: mechanical delay stage

What is the current value? m.lxt_ttc.wm()
Change value: m.lxt_ttc.mv()
Is it changing? m.las_tt_delay.ismoving()

Friedrich Schotte, 19 Oct 2010 - 27 Jan 2016
"""

__version__ = "2.1" # replaced "lxt_tt" with "lxt"

from numpy import isnan,nan,inf,array
from DB import dbput,dbget
from time import sleep,time
from thread import start_new_thread
from logging import debug,info,warn,error
try: import xppbeamline
except: warn("module 'xppbeamline' not available")
from numpy import isnan

class Lxd(object):
    """Laser x-ray time delay in seconds"""
    sign = 1
    unit = "s"

    # This is to make sure that this command is called in main thread first.
    # If is called from a different thread the first time, it raises an
    # Exception:
    # channel already created in create_channel() file pyca/pyca.cc at line
    # 25 PV XPP:USER:VIT:T0
    if "xppbeamline" in globals():
        t = xppbeamline.m.lxt.wm()
        xppbeamline.m.lxt.mv(t)

    def get_command_dial(self):
        """Uncalibrated nominal time delay in units of seconds."""
        try: value = xppbeamline.m.lxt_ttc.wm()
        except Exception,msg:
            warn("Timing_XPP: lxd: m.lxt_ttc.wm(): %s" % msg); value = nan
        return value
    def set_command_dial(self,value):
        if not isnan(value):
            start_new_thread(xppbeamline.m.lxt.mv,(value,))
    command_dial = property(get_command_dial,set_command_dial)

    def get_readback_dial(self):
        """Uncalibrated actual time delay in units of s."""
        try: value = xppbeamline.m.lxt_ttc.wm()
        except Exception,msg:
            warn("Timing_XPP: lxd: m.lxt_ttc.wm(): %s" % msg); value = nan
        return value
    readback_dial = property(get_readback_dial)

    dial = property(get_readback_dial,set_command_dial)

    def get_moving(self):
        """Is timing still shifting?"""
        return False
    def set_moving(self,value):
        """Is value = False stop the ramping"""
        pass
    moving = property(get_moving,set_moving)

    def stop():
        """If the phase shift is still ramping, stop the ramping"""
        self.moving = False

    def user_to_dial(self,value):
        "Convert calibrated to uncalibrated time delay"
        dial_value = (value - self.offset) * self.sign
        return dial_value

    def dial_to_user(self,dial_value):
        "Convert uncalibrated to calibrated time delay"
        user_value = dial_value*self.sign + self.offset
        return user_value

    def get_command_value(self):
        """Calibrated Laser to X-ray time delay in units of seconds.
        Positive value means X-ray comes after laser"""
        return self.dial_to_user(self.command_dial)
    def set_command_value(self,value):
        self.command_dial = self.user_to_dial(value)
    command_value = property(get_command_value,set_command_value)

    def get_readback_value(self):
        """Calibrated Laser to X-ray time delay in units of seconds.
        Positive value means X-ray comes after laser"""
        return self.dial_to_user(self.dial)
    readback_value = property(get_readback_value)

    value = property(get_readback_value,set_command_value)

    def define_value(self,value):
        """Modify the user-to-dial offset such that the new user value is
        'value'"""
        self.offset = value - self.dial * self.sign
        # user = dial*sign + offset; offset = user - dial*sign

    def get_min(self):
        """Smallest possible time delay in s"""
        return min(self.dial_to_user(self.min_dial),self.dial_to_user(self.max_dial))
    min = property(get_min)

    def get_max(self):
        """Largest possible time delay in s"""
        return max(self.dial_to_user(self.min_dial),self.dial_to_user(self.max_dial))
    max = property(get_max)

    def get_offset(self):
        """Calibration offset in seconds"""
        offset = dbget("timing.lxd.offset")
        try: return float(offset)
        except Exception: return 0.0
    def set_offset(self,value):
        dbput("timing.lxd.offset",str(value))
    offset = property(get_offset,set_offset)

    def get_min_dial(self):
        """Calibration min_dial in seconds"""
        min_dial = dbget("timing.lxd.min_dial")
        try: return float(min_dial)
        except Exception: return -inf
    def set_min_dial(self,value):
        dbput("timing.lxd.min_dial",str(value))
    min_dial = property(get_min_dial,set_min_dial)

    def get_max_dial(self):
        """Calibration max_dial in seconds"""
        max_dial = dbget("timing.lxd.max_dial")
        try: return float(max_dial)
        except Exception: return inf
    def set_max_dial(self,value):
        dbput("timing.lxd.max_dial",str(value))
    max_dial = property(get_max_dial,set_max_dial)
    
lxd = Lxd()

if __name__ == "__main__": # for testing
    from time import sleep
    self = lxd
    delays = [0,100e-15,1e-12,10e-12,100e-12,1e-9]

