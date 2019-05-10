"""EPICS Channel Access Process Variable as class property
Author: Friedrich Schotte
Date created: 2019-05-18
Date last modified: 2019-05-18
"""
__version__ = "1.0"

from numpy import nan
def PV_property(name,default_value=nan):
    """EPICS Channel Access Process Variable as class property"""
    def get(self):
        from CA import caget
        value = caget(self.prefix+name.upper())
        if value is None: value = default_value
        if type(value) != type(default_value):
            if type(default_value) == list: value = [value]
            else:
                try: value = type(default_value)(value)
                except: value = default_value
        return value
    def set(self,value):
        from CA import caput
        value = caput(self.prefix+name.upper(),value)
    return property(get,set)
