#!/usr/bin/env python
"""This is to run a second instance of the 'DataLogger_HS' application
Friedrich Schotte, 18 Jun 2011-30 Mar 2014
Hyun Sun Cho, 1 Feb 2015 """
__version__ = "1.1"

from DataLogger_HS import DataLogger
import wx

app = wx.App(redirect=False)
win = DataLogger(name="DataLogger_HS2")
app.MainLoop()
