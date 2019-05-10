#!/usr/bin/env python
"""High-speed diffractometer.
F. Schotte, 31 Oct 2013 - 2 Jul 2014"""

__version__ = "1.1"
import wx
from MotorPanel import MotorWindow
# Needed to initialize WX library
if not "app" in globals(): app = wx.App(redirect=False)
from peristaltic_pump import PumpA,PumpB,peristaltic_pump
window = MotorWindow([PumpA,PumpB,peristaltic_pump.V,peristaltic_pump.dV],
    title="Peristaltic Pump")
app.MainLoop()
