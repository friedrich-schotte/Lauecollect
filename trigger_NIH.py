#!/usr/bin/env python
"""
Substitute for the BioCARS timing system to use at the NIH for testing.

Friedrich Schotte, 11 Aug 2014 - 12 Aug 2014
"""
__version__ = "1.0"

from DG535 import DG535

class Pulses(object):
    """Number of pulses per acquisition"""
    from numpy import nan
    start = nan
    
    doc = "When read return the number of pulses remaining until the burst"\
        "ends. When set trigger a burst with the given number of pulses."
    def get_value(self):
        """Number of pulses remaining until the burst ends"""
        from numpy import ceil,isnan
        from time import time
        if isnan(self.start): return 0
        dt = time() - self.start
        period = 1/DG535.burst_frequency
        triggers_generated = int(ceil(dt/period))
        count = max(DG535.burst_count - triggers_generated,0)
        return count
    def set_value(self,count):
        from time import time
        DG535.start_burst(count)
        self.start = time()
    value = property(get_value,set_value,doc=doc)

pulses = Pulses()

class ContinuousTrigger(object):
    """Is continuous triggering enabled?"""
    def get_value(self):
        """Is continuous triggering enabled?"""
        return DG535.trigger_mode == "internal"
    def set_value(self,value):
        if bool(value) == True: DG535.trigger_mode = "internal"
        else: DG535.trigger_mode = "single shot"
    value = property(get_value,set_value)

continuous_trigger = ContinuousTrigger()

class TMode(object):
    """Trigger mode: 0 = continuous trigger, 1 = counted"""
    def get_value(self):
        """0 = continuous trigger, 1 = counted"""
        return not continuous_trigger.value
    def set_value(self,value): continuous_trigger.value = not value
    value = property(get_value,set_value)

tmode = TMode()

class Waitt(object):
    """Waiting time between pulses"""
    unit = "s"
    stepsize = 1e-6
    def get_value(self):
        """Time between susequent X-ray pulse in seconds"""
        if DG535.trigger_mode == "burst": return 1/DG535.burst_frequency
        else: return 1/DG535.trigger_frequency
    def set_value(self,value):
        DG535.burst_frequency = 1/value
        DG535.trigger_frequency = 1/value
    value = property(get_value,set_value)

    def get_min(self):
        """Lower limit in seconds"""
        return 1e-6
    min = property(get_min)
    
    def get_max(self):
        """Upper limit in seconds"""
        return 1000.0
    max = property(get_max)

    def get_choices(self):
        """Upper limit in seconds"""
        from numpy import arange
        return arange(0,1.05,0.05)
    choices = property(get_choices)

    def next(self,value):
        """Closest allowed value to the given waitting time in s"""
        from numpy import clip
        value = clip(value,self.min,self.max)
        return value

waitt = Waitt()

# Dummy for compatibility with 14-ID

class transon:
    """Sample translation enabled?"""
    value = False

class mson:
    """Millsecond X-ray shutter enabled?"""
    value = False

class laseron:
    """Laser trigger enabled?"""
    value = False

def toint(x):
    """Convert x to a floating point number.
    If not convertible return zero"""
    try: return int(x)
    except: return 0

def tofloat(x):
    """Convert x to a floating point number.
    If not convertible return 'Not a Number'"""
    from numpy import nan
    try: return float(x)
    except: return nan


if __name__ == "__main__": # for testing
    from time import sleep
    print ""
