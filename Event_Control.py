#!/usr/bin/env python
"""Controls for control panels
Author: Friedrich Schotte
Date created: 2020-09-18
Date last modified: 2022-06-09
Revision comment: Added: lock; fixed issue: 'Button' object has no attribute 'Value'
"""
__version__ = "1.1.1"

import logging
import wx
from handler import handler
from time_string import date_time


class Event_Control(wx.Panel):
    def __init__(
            self,
            parent,
            control_type,
            references,
            *args,
            **kwargs,
    ):
        from threading import Lock

        self.control_type = control_type
        self.references = references
        wx.Panel.__init__(self, parent)

        self.lock = Lock()

        # Controls
        self.control = self.control_type(self, *args, **kwargs)
        self.control.Enabled = False
        # Needed for wx.Button on MacOS, because Position defaults to 5,3:
        self.control.Position = (0, 0)
        for property_name in references:
            setattr(self.control, property_name + "_timestamp", 0.0)
            setattr(self.control, property_name + "_has_conflict", False)

        # Layout
        self.Sizer = wx.BoxSizer()
        self.Sizer.Add(self.control, flag=wx.EXPAND, proportion=1)
        self.Fit()

        # Callbacks
        events = [
            wx.EVT_TOGGLEBUTTON,
            wx.EVT_BUTTON,
            wx.EVT_TEXT_ENTER,
            wx.EVT_COMBOBOX,
            wx.EVT_CHOICE,
            wx.EVT_CHECKBOX,
        ]
        for event in events:
            self.Bind(event, self.handle_user_input, self.control)
        self.Bind(wx.EVT_WINDOW_DESTROY, self.handle_destroy, self)

        self.initialize()

    def __repr__(self):
        return f"{self.class_name}({self.control_type.__name__})"

    @property
    def class_name(self): return type(self).__name__

    from run_async import run_async

    @run_async
    def initialize(self, _event=None):
        from time import time
        self.subscribe_updates()
        for property_name, reference in self.references.items():
            value = reference.value
            timestamp = time()
            wx.CallAfter(self.set_value, property_name, value, timestamp)
        wx.CallAfter(self.control.Refresh)

    def handle_update(self, property_name, event):
        wx.CallAfter(self.set_value, property_name, event.value, event.time)
        wx.CallAfter(self.control.Refresh)

    def set_value(self, property_name, value, timestamp):
        with self.lock:
            logging.debug(f"{self}.{property_name} = {value!r}")
            from same import same

            old_value = getattr(self.control, property_name, False)
            old_timestamp = getattr(self.control, property_name+"_timestamp", False)
            reference = self.references[property_name]

            if timestamp == old_timestamp:
                if not same(value, old_value):
                    logging.warning(f"Conflict: {self}.{property_name}: {reference}: {value!r} vs {old_value!r} at {date_time(timestamp)}")
                    setattr(self.control, property_name + "_has_conflict", True)

            if timestamp >= old_timestamp:
                setattr(self.control, property_name, value)
                setattr(self.control, property_name + "_timestamp", timestamp)
                self.control.Refresh()  # work-around for a GenButton bug in Windows

            if timestamp > old_timestamp and getattr(self.control, property_name + "_has_conflict"):
                logging.info(f"Conflict resolved: {self}.{property_name}: {reference}: {value!r} (was {old_value!r} at {date_time(old_timestamp)})")
                setattr(self.control, property_name + "_has_conflict", False)

    def handle_user_input(self, _event):
        for property_name, reference in self.references.items():
            if property_name == "Value":
                value = getattr(self.control, "Value", False)
                logging.debug(f"{reference}.value = {value!r}")
                reference.value = value

    def handle_destroy(self, _event):
        self.unsubscribe_updates()

    def subscribe_updates(self):
        for property_name, reference in self.references.items():
            event_handler = handler(self.handle_update, property_name)
            # logging.debug(f"Subscribing to updates of {reference}...")
            reference.monitors.add(event_handler)

    @run_async
    def unsubscribe_updates(self):
        for property_name, reference in self.references.items():
            event_handler = handler(self.handle_update, property_name)
            # logging.debug(f"Unsubscribing from updates of {reference}...")
            reference.monitors.remove(event_handler)


def object_repr(obj):
    return type(obj).__name__


if __name__ == '__main__':
    fmt = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=fmt)
    app = wx.App()
    # app.MainLoop()
