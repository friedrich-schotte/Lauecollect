"""Make a property of a class cached

Usage:
class Banana(object):
  def __init__(self): self.color = "green"
  @cached
  @property
  def ripe(self): return True if self.color == "yellow" else False
banana = Banana()

class Banana(object):
  def __init__(self): self.color = "green"
  def get_ripe(self): return True if self.color == "yellow" else False
  def set_ripe(self,value): self.color = "yellow" if value else "green"
  ripe = cached(property(get_ripe,set_ripe))
banana = Banana()

class Banana(object):
  def __init__(self): self.color = "green"
  def get_ripe(self): return True if self.color == "yellow" else False
  def set_ripe(self,value): self.color = "yellow" if value else "green"
  ripe = property(get_ripe,set_ripe)

class Cached_Banana(Banana):
  ripe = cached(Banana.ripe)
banana = Cached_Banana()  
  
Date created: 2017-07-28
Date last modified: 2019-01-24
"""
__authors__ = ["Friedrich Schotte"]
__version__ = "1.0.2" # clear cache on set, forcing re-read

from logging import debug,info,warn,error

def cached_property(property_object,timeout=1.0):
    """Make a property cached
    timeout: expiration time in seconds
    """
    def cached(self,property_object):
        from time import time
        if not hasattr(self,"__cached_properties__"): return None
        if property_object not in self.__cached_properties__: return None
        if time() - self.__cached_properties__[property_object]["time"] > timeout:
            return None
        return self.__cached_properties__[property_object]["value"]

    def cache(self,property_object,value):
        from time import time
        if not hasattr(self,"__cached_properties__"):
            self.__cached_properties__ = {}
        self.__cached_properties__[property_object] = {"time":time(),"value":value}

    def cache_clear(self,property_object):
        if hasattr(self,"__cached_properties__"):
            del self.__cached_properties__[property_object]

    def get(self):
        value = cached(self,property_object);
        ##if value: debug("cached_property: Cached %28.28r" % value)
        if value is None:
            value = property_object.__get__(self)
            ##debug("cached_property: Updated %s=%28.28r" % (name(property_object),value))
            cache(self,property_object,value)
        return value

    def name(object):
        if hasattr(object,"__doc__"): return object.__doc__
        return repr(object)

    def set(self,value):
        cache_clear(self,property_object)
        property_object.__set__(self,value)

    cached_property = property(get,set)
    
    return cached_property 
     

cached = cached_property
