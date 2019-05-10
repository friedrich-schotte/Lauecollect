#!/usr/bin/env python
"""Control panel for all motor controlled by the Aerotech Ensemble EPAQ.
F. Schotte, 31 Oct 2013 - Jun 30, 2017"""

__version__ = "1.0.2" # msShut
import wx
from MotorPanel import MotorWindow
# Needed to initialize WX library
if not "app" in globals(): app = wx.App(redirect=False)
from instrumentation import SampleX,SampleY,SampleZ,SamplePhi,PumpA,PumpB,msShut
window = MotorWindow([SampleX,SampleY,SampleZ,SamplePhi,PumpA,PumpB,msShut],
    title="Ensemble")
app.MainLoop()
