"""Author: Friedrich Schotte, 29 Nov 2013 - 21 Feb 2016
"""
__version__ = "1.0.1"

from numpy import nan

class DummyCounter(object):
    def __init__(self,*args,**kwargs):
        if len(args)>0: self.name = args[0]

    name = "Dummy Counter"
    unit = ""

    value = nan
    average = nan
    stdev = nan
    count = 0
    def start(self): pass
    

dummy_counter = DummyCounter()
