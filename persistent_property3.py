"""
A propery object to be used inside a class, it value is kept in a permanent
storage in a file.

Usage example:
class EnsembleSAXS(object):
    name = "Ensemble_SAXS"
    mode_changed = persistent_property("mode_changed")

Friedrich Schotte, Mar 7, 2015 - Jul 6, 2017

Updated:
Valentyn Stadnytksyi minor updates Dec 4, 2017
changed debug statement to print statements
"""
from logging import debug,warn,info,error
import sys
__version__ = "1.2.2" # eval: -OrderdDict +wx

def persistent_property(name,default_value=0.0):
    """A propery object to be used inside a class"""
    def get(self):
        class_name = getattr(self,"name",self.__class__.__name__)
        if not "{name}" in name: 
            if class_name: dbname = class_name+"."+name
            else: dbname = name
        else: dbname = name.replace("{name}",class_name)
        #print("persistent_property.get: %s: %r, %r: %r" % (name,self,class_name,dbname))
        if sys.version_info[0] ==3:
            from DB3 import dbget
        else:
            from DB import dbget
        t = dbget(dbname)
        if type(default_value) == str and default_value.startswith("self."):
            def_val = getattr(self,default_value[len("self."):])
        else: def_val = default_value
        dtype = type(def_val)
        try: from numpy import nan,inf,array # for "eval"
        except: pass
        try: import wx # for "eval"
        except: pass
        try: t = dtype(eval(t))
        except: t = def_val
        return t
    def set(self,value):
        class_name = getattr(self,"name",self.__class__.__name__)
        if not "{name}" in name: 
            if class_name: dbname = class_name+"."+name
            else: dbname = name
        else: dbname = name.replace("{name}",class_name)
        #print("persistent_property.set: %s: %r, %r: %r" % (name,self,class_name,dbname))
        if sys.version_info[0] ==3:
            from DB3 import dbput
        else:
            from DB import dbput
        dbput(dbname,repr(value))
    return property(get,set)
