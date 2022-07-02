#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2020-04-24
Date last modified: 2021-06-19
Revision comment: Updated documentation
"""
__version__ = "1.5.8"

from logging import debug
import wx
from handler import handler

from EditableControls import TextCtrl, ComboBox


class Control_Base(object):
    def __init__(self, name):
        """name: e.g. "instrumentation.BioCARS.camera_controls.MicroscopeCamera.acquiring" """
        self.name = name

    def __repr__(self):
        return f"{type(self).__name__}({self.name!r})"

    def get_value(self):
        value = getattr(self.object, self.property_name)
        return value

    def set_value(self, value):
        setattr(self.object, self.property_name, value)

    value = property(get_value, set_value)

    @property
    def monitors(self):
        return self.reference.monitors

    @property
    def reference(self):
        from reference import reference
        return reference(self.object, self.property_name)

    @property
    def object(self):
        names = self.object_name.split(".")
        module_name = names[0]
        obj = __import__(module_name)
        for name in names[1:]:
            obj = getattr(obj, name)
        return obj

    @property
    def object_name(self):
        object_name = ".".join(self.name.split(".")[0:-1])
        return object_name

    @property
    def property_name(self):
        property_name = self.name.split(".")[-1]
        return property_name


class CheckBox_Control(Control_Base, wx.CheckBox):
    def __init__(self, parent, name, label=""):
        Control_Base.__init__(self, name)
        wx.CheckBox.__init__(self, parent, label=label)
        self.Parent.Bind(wx.EVT_CHECKBOX, self.OnChangeValue, self)
        self.monitors.add(handler(self.handle_change))
        self.update()
        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroy)

    def OnDestroy(self, event):
        event.Skip()
        debug(f"{self} destroyed")
        debug(f"Unsubscribing from {self.reference}")
        self.monitors.remove(handler(self.handle_change))

    from run_async import run_async

    @run_async
    def update(self):
        wx.CallAfter(self.SetValue, self.value)

    def handle_change(self):
        value = self.value
        debug(("%s = %.60r" % (self.name, value)).replace("\n", ""))
        wx.CallAfter(self.SetValue, value)

    def OnChangeValue(self, _event):
        value = self.Value
        debug(("%s = %.60r" % (self.name, value)).replace("\n", ""))
        self.value = value


class TextCtrl_Control(Control_Base, TextCtrl):
    def __init__(self, parent, name, **kwargs):
        if "style" not in kwargs:
            kwargs["style"] = 0
        kwargs["style"] |= wx.TE_PROCESS_ENTER
        Control_Base.__init__(self, name)
        TextCtrl.__init__(self, parent=parent, **kwargs)
        self.Parent.Bind(wx.EVT_TEXT_ENTER, self.OnChangeValue, self)
        self.monitors.add(handler(self.handle_change))
        self.update()
        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroy)

    def OnDestroy(self, event):
        event.Skip()
        debug(f"{self} destroyed")
        debug(f"Unsubscribing from {self.reference}")
        self.monitors.remove(handler(self.handle_change))

    def to_text(self, value):
        text = str(value)
        return text

    def from_text(self, text):
        value = text
        return value

    from run_async import run_async

    @run_async
    def update(self):
        value = self.value
        debug(("%s = %.60r" % (self.name, value)).replace("\n", ""))
        wx.CallAfter(self.SetValue, value)

    def SetValue(self, value):
        self.Value = self.to_text(value)

    def handle_change(self):
        value = self.value
        debug(("%s = %.60r" % (self.name, value)).replace("\n", ""))
        wx.CallAfter(self.SetValue, value)

    def OnChangeValue(self, _event):
        value = self.from_text(self.Value)
        debug(("%s = %.60r" % (self.name, value)).replace("\n", ""))
        self.value = value


class ComboBox_Control(Control_Base, ComboBox):
    def __init__(self, parent, name, choices_name, **kwargs):
        Control_Base.__init__(self, name)
        self.choices = Control_Base(choices_name)
        ComboBox.__init__(
            self,
            parent=parent,
            style=wx.TE_PROCESS_ENTER,
            **kwargs
        )
        self.Parent.Bind(wx.EVT_COMBOBOX, self.OnChangeValue, self)
        self.Parent.Bind(wx.EVT_TEXT_ENTER, self.OnChangeValue, self)
        self.monitors.add(handler(self.handle_change))
        self.choices.monitors.add(handler(self.handle_choices_change))
        self.update()
        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroy)

    def OnDestroy(self, event):
        event.Skip()
        debug(f"{self} destroyed")
        debug(f"Unsubscribing from {self.reference}")
        self.monitors.remove(handler(self.handle_change))
        debug(f"Unsubscribing from {self.choices.reference}")
        self.choices.monitors.remove(handler(self.handle_choices_change))

    def to_text(self, value):
        text = str(value)
        return text

    def from_text(self, text):
        value = text
        return value

    @property
    def value_as_text(self):
        text = self.to_text(self.value)
        return text

    @property
    def choices_as_text(self):
        text = [self.to_text(x) for x in self.choices.value]
        return text

    from run_async import run_async

    @run_async
    def update(self):
        wx.CallAfter(self.SetValue, self.value_as_text)
        wx.CallAfter(self.SetItems, self.choices_as_text)

    def handle_change(self):
        debug(("%s = %.60r" % (self.name, self.value)).replace("\n", ""))
        wx.CallAfter(self.SetValue, self.value_as_text)

    def handle_choices_change(self):
        debug(("%s = %.60r" % (self.choices.name, self.choices.value)).replace("\n", ""))
        wx.CallAfter(self.SetItems, self.choices_as_text)

    def OnChangeValue(self, _event):
        value = self.from_text(self.Value)
        debug(("%s = %.60r" % (self.name, value)).replace("\n", ""))
        self.value = value


class StaticText_Indicator(Control_Base, wx.TextCtrl):
    def __init__(self, parent, name, **kwargs):
        Control_Base.__init__(self, name)
        style = kwargs.pop("style", 0)
        style |= wx.TE_READONLY | wx.BORDER_NONE
        wx.TextCtrl.__init__(self, parent=parent, style=style, **kwargs)
        self.monitors.add(handler(self.handle_change))
        self.update()
        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroy)

    def OnDestroy(self, event):
        event.Skip()
        debug(f"{self} destroyed")
        debug(f"Unsubscribing from {self.reference}")
        self.monitors.remove(handler(self.handle_change))

    def to_text(self, value):
        text = str(value)
        return text

    from run_async import run_async

    @run_async
    def update(self):
        wx.CallAfter(self.SetValue, self.value)

    def SetValue(self, value):
        self.Value = self.to_text(value)

    def handle_change(self):
        value = self.value
        debug(("%s = %.60r" % (self.name, value)).replace("\n", ""))
        wx.CallAfter(self.SetValue, value)


class Slider_Control(Control_Base, wx.Slider):
    min_value = 0.0
    max_value = 1.0
    min_count = 0
    max_count = 1000

    def __init__(
            self,
            parent,
            name,
            min_value=None,
            max_value=None,
            min_count=None,
            max_count=None,
            **kwargs
    ):
        if min_value is not None:
            self.min_value = min_value
        if max_value is not None:
            self.max_value = max_value
        if min_count is not None:
            self.min_count = min_count
        if max_count is not None:
            self.max_count = max_count

        Control_Base.__init__(self, name)
        wx.Slider.__init__(
            self,
            parent=parent,
            minValue=self.min_count,
            maxValue=self.max_count,
            **kwargs
        )
        self.Parent.Bind(wx.EVT_SLIDER, self.OnChangeValue, self)
        self.monitors.add(handler(self.handle_change))
        self.update()
        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroy)

    def OnDestroy(self, event):
        event.Skip()
        debug(f"{self} destroyed")
        debug(f"Unsubscribing from {self.reference}")
        self.monitors.remove(handler(self.handle_change))

    def to_count(self, value):
        from numpy import rint, clip
        fraction = float(value - self.min_value) / (self.max_value - self.min_value)
        count = self.min_count + fraction * (self.max_count - self.min_count)
        count = int(rint(count))
        count = clip(count, self.min_count, self.max_count)
        return count

    def from_count(self, count):
        fraction = float(count - self.min_count) / (self.max_count - self.min_count)
        value = self.min_value + fraction * (self.max_value - self.min_value)
        return value

    from run_async import run_async

    @run_async
    def update(self):
        wx.CallAfter(self.SetValue, self.value)

    def SetValue(self, value):
        self.Value = self.to_count(value)

    def handle_change(self):
        value = self.value
        debug(("%s = %.60r" % (self.name, value)).replace("\n", ""))
        wx.CallAfter(self.SetValue, value)

    def OnChangeValue(self, _event):
        value = self.from_count(self.Value)
        debug(("%s = %.60r" % (self.name, value)).replace("\n", ""))
        self.value = value
