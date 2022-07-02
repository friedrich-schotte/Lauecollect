#!/usr/bin/env python
"""High-speed diffractometer.
Friedrich Schotte, 8 Dec 2015 - 8 Dec 2015"""

__version__ = "1.0"
import wx
from MotorPanel import MotorWindow

app = wx.GetApp() if wx.GetApp() else wx.App()
from instrumentation import ChopX,ChopY
window = MotorWindow([ChopX,ChopY],
    title="High-Speed Chopper")
app.MainLoop()
