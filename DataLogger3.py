#!/usr/bin/env python
"""This is to run a third instance of the 'DataLogger' application
Friedrich Schotte, 18 Jun 2011"""

from DataLogger import DataLogger
import wx

app = wx.PySimpleApp(0)
win = DataLogger(name="DataLogger3")
app.MainLoop()
