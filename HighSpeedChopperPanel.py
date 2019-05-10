#!/usr/bin/env python
"""High-speed diffractometer.
Friedrich Schotte, 8 Dec 2015 - 8 Dec 2015"""

__version__ = "1.0"
import wx
from MotorPanel import MotorWindow
# Needed to initialize WX library
if not "app" in globals(): app = wx.App(redirect=False)
from instrumentation import ChopX,ChopY
window = MotorWindow([ChopX,ChopY],
    title="High-Speed Chopper")
app.MainLoop()
