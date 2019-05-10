#!/usr/bin/env python
"""
Software elulation of the BioCARS timing system to use at the NIH for testing.

Friedrich Schotte, 18 Sep 2014 - 18 Sep 2014
"""
__version__ = "1.0"

class Pulses(object):
    """Acquiation pulse count (software emulated)"""
    from numpy import nan
    start = nan
    initial_count = 0
    
    def get_value(self):
        """When read return the number of pulses remaining until the burst
        ends. When set trigger a burst with the given number of pulses."""
        from numpy import ceil,isnan
        from time import time
        if isnan(self.start): return 0
        dt = time() - self.start
        period = waitt.value
        triggers_generated = int(ceil(dt/period))
        count = max(self.initial_count - triggers_generated,0)
        return count
    def set_value(self,count):
        from time import time
        self.initial_count = count
        self.start = time()
    value = property(get_value,set_value)

pulses = Pulses()

class continuous_trigger:
    """Is continuous triggering enabled?"""
    value = False

class tmode:
    """Trigger mode: 0 = continuous trigger, 1 = counted"""
    value = False

class Waitt(object):
    """Waiting time between pulses"""
    unit = "s"
    stepsize = 1e-6
    value = 0.024
    min = 1e-6
    max = 1000
    from numpy import arange
    choices = arange(0,1.05,0.05)

    def next(self,value):
        """Closest allowed value to the given waitting time in s"""
        from numpy import clip
        value = clip(value,self.min,self.max)
        return value

waitt = Waitt()

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
