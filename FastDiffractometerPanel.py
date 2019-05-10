#!/usr/bin/env python
"""High-speed diffractometer.
F. Schotte, 31 Oct 2013 - 28 Jan 2016"""

__version__ = "1.0.3"
import wx
from MotorPanel import MotorWindow
# Needed to initialize WX library
if not "app" in globals(): app = wx.App(redirect=False)
from Ensemble import SampleX,SampleY,SampleZ,SamplePhi
window = MotorWindow([SampleX,SampleY,SampleZ,SamplePhi],
    title="Fast Diffractometer")
app.MainLoop()
