"""EPICS Channel Access Process Variable as class property for the client object
Originally designed by F.Schotte and later modified by V.Stadnytskyi.

This version doesn't change PV name to upper case as it was originally done in
PV_property.

Author: Friedrich Schotte, Valentyn Stadnytskyi
Date created: 2019-05-18 (originally came from PV_property)
Date last modified: 2021-29-29
Revision comment: Cleanup
"""
__version__ = "1.2.1"

from numpy import nan


def PV_property_client(name, default_value=nan):
    """EPICS Channel Access Process Variable as class property.
    this property class doesn't change the name to upper case."""

    def prefix(self):
        prefix = ""
        if hasattr(self, "prefix"):
            prefix = self.prefix
        if hasattr(self, "__prefix__"):
            prefix = self.__prefix__
        if prefix and not prefix.endswith("."):
            prefix += "."
        return prefix

    def fget(self):
        from CA import caget
        value = caget(prefix(self) + name)
        if value is None:
            value = default_value
        if type(value) != type(default_value):
            if type(default_value) == list:
                value = [value]
            else:
                try:
                    value = type(default_value)(value)
                except (ValueError, TypeError):
                    value = default_value
        return value

    def fset(self, value):
        from CA import caput
        caput(prefix(self) + name, value)

    return property(fget, fset)
