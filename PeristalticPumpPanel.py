#!/usr/bin/env python
"""High-speed diffractometer.
F. Schotte, 31 Oct 2013 - 2 Jul 2014"""

__version__ = "1.1"
import wx
from MotorPanel import MotorWindow

app = wx.GetApp() if wx.GetApp() else wx.App()
from peristaltic_pump import PumpA,PumpB,peristaltic_pump
window = MotorWindow([PumpA,PumpB,peristaltic_pump.V,peristaltic_pump.dV],
    title="Peristaltic Pump")
app.MainLoop()
