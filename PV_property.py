"""EPICS Channel Access Process Variable as class property
Author: Friedrich Schotte
Date created: 2019-05-18
Date last modified: 2019-05-21
"""
__version__ = "1.1" # prefix may not end with "."

from numpy import nan
def PV_property(name,default_value=nan):
    """EPICS Channel Access Process Variable as class property"""
    def prefix(self):
        prefix = ""
        if hasattr(self,"prefix"): prefix = self.prefix
        if hasattr(self,"__prefix__"): prefix = self.__prefix__
        if prefix and not prefix.endswith("."): prefix += "."
        return prefix
    def get(self):
        from CA import caget
        value = caget(prefix(self)+name.upper())
        if value is None: value = default_value
        if type(value) != type(default_value):
            if type(default_value) == list: value = [value]
            else:
                try: value = type(default_value)(value)
                except: value = default_value
        return value
    def set(self,value):
        from CA import caput
        value = caput(prefix(self)+name.upper(),value)
    return property(get,set)
