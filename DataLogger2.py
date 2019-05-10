#!/usr/bin/env python
"""This is to run a second instance of the 'DataLogger' application
Friedrich Schotte, 18 Jun 2011-30 Mar 2014"""
__version__ = "1.1"

from DataLogger import DataLogger
import wx

app = wx.App(redirect=False)
win = DataLogger(name="DataLogger2")
app.MainLoop()
