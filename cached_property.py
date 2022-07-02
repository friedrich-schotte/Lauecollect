"""Make a property of a class cached

Usage:
class Banana(obj):
  def __init__(self): self.color = "green"
  @cached
  @property
  def ripe(self): return True if self.color == "yellow" else False
banana = Banana()

class Banana(obj):
  def __init__(self): self.color = "green"
  def get_ripe(self): return True if self.color == "yellow" else False
  def set_ripe(self,value): self.color = "yellow" if value else "green"
  ripe = cached(property(get_ripe,set_ripe))
banana = Banana()

class Banana(obj):
  def __init__(self): self.color = "green"
  def get_ripe(self): return True if self.color == "yellow" else False
  def set_ripe(self,value): self.color = "yellow" if value else "green"
  ripe = property(get_ripe,set_ripe)

class Cached_Banana(Banana):
  ripe = cached(Banana.ripe)
banana = Cached_Banana()  
  
Author: Friedrich Schotte
Date created: 2017-07-28
Date last modified: 2022-05-14
Revision comment: Issue: line 61, in cache_clear
    del self.__cached_properties__[property_object]
    KeyError: <property object at 0x0000021EF8AEC4A0>
"""
__version__ = "1.1.2"

import logging
from numpy import inf


def cached_property(property_object, timeout=inf):
    """Make a property cached
    timeout: expiration time in seconds
    """

    def cached(self, property_object):
        from time import time
        if not hasattr(self, "__cached_properties__"):
            return None
        if property_object not in self.__cached_properties__:
            return None
        if time() - self.__cached_properties__[property_object]["time"] > timeout:
            return None
        return self.__cached_properties__[property_object]["value"]

    def cache(self, property_object, value):
        from time import time
        if not hasattr(self, "__cached_properties__"):
            self.__cached_properties__ = {}
        self.__cached_properties__[property_object] = {"time": time(), "value": value}

    def cache_clear(self, property_object):
        if hasattr(self, "__cached_properties__"):
            try:
                del self.__cached_properties__[property_object]
            except KeyError:
                logging.info(f"{property_object!r} not in {self}.__cached_properties__")

    def fget(self):
        value = cached(self, property_object)
        # if value: debug("cached_property: Cached %28.28r" % value)
        if value is None:
            value = property_object.__get__(self)
            # debug("cached_property: Updated %s=%28.28r" % (name(property_object),value))
            cache(self, property_object, value)
        return value

    def fset(self, value):
        cache_clear(self, property_object)
        property_object.__set__(self, value)

    cached_property = property(fget, fset)

    return cached_property


cached = cached_property


def name(obj):
    if hasattr(obj, "__doc__"):
        return obj.__doc__
    return repr(obj)
