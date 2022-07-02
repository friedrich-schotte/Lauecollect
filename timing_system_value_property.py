"""
Author: Friedrich Schotte
Date created: 2021-06-03
Date last modified: 2022-04-05
Revision comment: Renamed to timing_system_value_property
"""
__version__ = "1.1"


def timing_system_value_property(name):
    def fget(self): return self.timing_system_value(name)

    def fset(self, value): self.set_timing_system_value(name, value)

    return property(fget, fset)
