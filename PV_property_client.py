"""EPICS Channel Access Process Variable as class property for the client object
Author: Friedrich Schotte, Valentyn Stadnytskyi
Date created: 2019-05-18 (originally came from PV_property)
Date last modified: 2019-05-26
"""
__version__ = "1.2" # added alias for PV_property_client

from numpy import nan
def PV_property_client(name,default_value=nan):
    """EPICS Channel Access Process Variable as class property.
        this property class doesn't change the name to upper case.
    """
    def prefix(self):
        prefix = ""
        if hasattr(self,"prefix"): prefix = self.prefix
        if hasattr(self,"__prefix__"): prefix = self.__prefix__
        if prefix and not prefix.endswith("."): prefix += "."
        return prefix
    def get(self):
        from CA import caget
        value = caget(prefix(self)+name)
        if value is None: value = default_value
        if type(value) != type(default_value):
            if type(default_value) == list: value = [value]
            else:
                try: value = type(default_value)(value)
                except: value = default_value
        return value
    def set(self,value):
        from CA import caput
        value = caput(prefix(self)+name,value)
    return property(get,set)
