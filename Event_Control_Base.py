#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2021-05-31
Date last modified: 2021-05-31
Revision comment:
"""
__version__ = "1.0"

from logging import debug, error
import wx


class Event_Control_Base():
    from run_async import run_async

    def __init__(self):
        if hasattr(self, "Bind"):
            self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroy)
        self.start_monitoring()
        self.update()

    def __repr__(self):
        return f"{self.class_name}()"

    @property
    def class_name(self):
        return type(self).__name__

    attributes = {
        "value": "Value",
        "label": "Label",
        "enabled": "Enabled",
        "size": "Size",
    }

    def start_monitoring(self):
        for attribute_name in self.attributes:
            if hasattr(self, attribute_name+"_reference"):
                reference = getattr(self, attribute_name+"_reference")
                reference.monitors.add(self.change_handler(attribute_name))

    def stop_monitoring(self):
        for attribute_name in self.attributes:
            if hasattr(self, attribute_name+"_reference"):
                reference = getattr(self, attribute_name+"_reference")
                reference.monitors.remove(self.change_handler(attribute_name))

    def change_handler(self, attribute_name):
        from handler import handler
        return handler(self.handle_change, attribute_name)

    def handle_change(self, attribute_name, event):
        my_attribute_name = self.attributes[attribute_name]
        self.set_attribute(my_attribute_name, event.value)

    @run_async
    def update(self):
        for attribute_name in self.attributes:
            if hasattr(self, attribute_name):
                my_attribute_name = self.attributes[attribute_name]
                value = getattr(self, attribute_name)
                debug(f"{self}: {my_attribute_name!r} = {value!r}")
                self.set_attribute(my_attribute_name, value)
            if hasattr(self, attribute_name+"_reference"):
                my_attribute_name = self.attributes[attribute_name]
                reference = getattr(self, attribute_name + "_reference")
                value = reference.value
                debug(f"{self}: {my_attribute_name!r} = {value!r}")
                self.set_attribute(my_attribute_name, value)

    def set_attribute(self, attribute_name, value):
        wx.CallAfter(self._set_attribute, attribute_name, value)

    def _set_attribute(self, attribute_name, value):
        try:
            setattr(self, attribute_name, value)
        except Exception as x:
            error(f"{self}: {attribute_name!r} = {value!r}: {x}")
        if hasattr(self,"Fit"):
            self.Fit()

    def OnChangeValue(self, _event):
        if hasattr(self, "Value"):
            value = self.Value
            formatted_value = ("%.60r" % value).replace("\n", "")
            debug(f"{self}.Value = {formatted_value}")
            if hasattr(self, "value_reference"):
                self.value_reference.value = value
        else:
            debug(f"{self} has not attribute 'Value'")

    def OnDestroy(self, event):
        event.Skip()
        debug(f"{self} destroyed")
        self.stop_monitoring()

