#!/usr/bin/env python
"""Make a property of a class cached

Usage:
class Banana(object):
  def __init__(self): self.color = "green"
  @cached
  @property
  def ripe(self): return True if self.color == "yellow" else False
banana = Banana()

Author: Friedrich Schotte
Date created: 2020-05-30
Date last modified: 2021-08-30
Revision comment: Cleanup
"""
__version__ = "1.0.1"


def cached(property_object):
    from cached_property import cached_property
    from numpy import inf
    return cached_property(property_object, timeout=inf)
