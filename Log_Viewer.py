#!/usr/bin/env python
"""
Viewer for log messages

Authors: Friedrich Schotte
Date created: 2019-11-15
Date last modified: 2020-11-12
Revision comment: Issue:
    Module 'monitor' is deprecated, use 'monitors' instead
"""
__version__ = "1.6.2"

from logging import debug

import wx
from handler import handler

from reference import reference

from Control_Panel import Control_Panel
from monitors import monitors


class Log_Viewer(Control_Panel):
    icon = "Server"

    @property
    def title(self): return "Log: %s" % self.name

    @property
    def ControlPanel(self):
        return Log_Control_Panel(self, self.name)


class Log_Control_Panel(wx.Panel):
    property_names = [
        "text",
        "level",
        "clear_enabled",
    ]

    def __init__(self, parent, name):
        wx.Panel.__init__(self, parent=parent)
        self.name = name

        # Controls
        from EditableControls import ComboBox
        style = wx.TE_MULTILINE | wx.TE_DONTWRAP | wx.TE_READONLY
        self.Log = wx.TextCtrl(self, style=style)
        self.Log.Font = wx.Font(
            pointSize=10,
            family=wx.FONTFAMILY_TELETYPE,
            style=wx.FONTSTYLE_NORMAL,
            weight=wx.FONTWEIGHT_NORMAL,
        )
        self.Clear = wx.Button(self, label="Clear Log")
        self.Level = ComboBox(self, choices=self.log.levels)

        # Callbacks
        self.Bind(wx.EVT_BUTTON, self.OnClear, self.Clear)
        self.Bind(wx.EVT_COMBOBOX, self.OnLevel, self.Level)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnLevel, self.Level)

        # Layout
        self.layout = wx.BoxSizer(wx.VERTICAL)
        self.layout.Add(self.Log, flag=wx.ALL | wx.EXPAND, proportion=1, border=2)
        self.controls = wx.BoxSizer(wx.HORIZONTAL)
        self.layout.Add(self.controls, flag=wx.ALL | wx.EXPAND, border=2)
        self.controls.Add(self.Clear, flag=wx.ALL | wx.EXPAND, border=2)
        self.controls.Add(self.Level, flag=wx.ALL | wx.EXPAND, border=2)
        self.Sizer = self.layout
        self.Layout()

        # Refresh
        for property_name in self.property_names:
            monitors(reference(self.log, property_name)).add(handler(self.handle_change, property_name))

        self.update()

    from run_async import run_async

    @run_async
    def update(self):
        for property_name in self.property_names:
            value = getattr(self.log, property_name)
            wx.CallAfter(self.set_value, property_name, value)

    def handle_change(self, property_name):
        value = getattr(self.log, property_name)
        wx.CallAfter(self.set_value, property_name, value)

    def set_value(self, property_name, value):
        if property_name == "text":
            self.Log.Value = value
            self.Log.SetInsertionPointEnd()
            self.Log.Refresh()
        if property_name == "level":
            self.Level.Value = value
        if property_name == "clear_enabled":
            self.Clear.Enabled = value

    def OnClear(self, _event):
        self.log.clear()

    def OnLevel(self, event):
        debug("event.String: %r" % getattr(event, "String", None))
        self.log.level = event.String

    @property
    def log(self):
        from log_control import log_control
        return log_control(self.name)


if __name__ == '__main__':
    # from pdb import pm

    # import autoreload

    name = "LaserLab.acquisition_IOC"
    domain_name, base_name = name.split(".")

    from redirect import redirect

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    redirect(f"{domain_name}.Log_Viewer.{base_name}", format=msg_format)

    app = wx.GetApp() if wx.GetApp() else wx.App()
    self = Log_Viewer(name)
    app.MainLoop()
