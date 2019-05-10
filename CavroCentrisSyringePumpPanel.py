#!/usr/bin/env python
"""Control panel for Cavro Centris Syringe Pumps
F. Schotte, Jun 7, 2017 - Jun 8, 2017"""

__version__ = "1.0"
import wx
from MotorPanel import MotorWindow
# Needed to initialize WX library
if not "app" in globals(): app = wx.App(redirect=False)
from cavro_centris_syringe_pump_IOC import volume,port
window = MotorWindow([port,volume],title="Centris Syringe Pumps")
app.MainLoop()
