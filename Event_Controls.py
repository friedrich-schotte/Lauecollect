#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2021-05-31
Date last modified: 2021-05-31
Revision comment:
"""
__version__ = "1.0"

import wx
from Event_Control_Base import Event_Control_Base


class CheckBox_Control(wx.CheckBox, Event_Control_Base):
    def __init__(self, parent, **kwargs):
        wx.CheckBox.__init__(self, parent, **kwargs)
        self.Parent.Bind(wx.EVT_CHECKBOX, self.OnChangeValue, self)
        Event_Control_Base.__init__(self)

    attributes = {
        "value": "Value",
        "label": "Label",
        "enabled": "Enabled",
        "size": "Size",
    }


class ToggleButton_Control(wx.ToggleButton, Event_Control_Base):
    def __init__(self, parent, **kwargs):
        wx.ToggleButton.__init__(self, parent, **kwargs)
        self.Parent.Bind(wx.EVT_TOGGLEBUTTON, self.OnChangeValue, self)
        Event_Control_Base.__init__(self)

    attributes = {
        "value": "Value",
        "label": "Label",
        "enabled": "Enabled",
        "size": "Size",
    }
