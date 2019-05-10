#!/usr/bin/env python
"""High-speed diffractometer
Control panel to save and motor positions.
Friedrich Schotte 31 Oct 2013 - 1 Nov 2013"""
__version__ = "1.1"

from SavedPositionsPanel import SavedPositionsPanel
from id14 import SampleX,SampleY,SampleZ,SamplePhi
import wx

# Needed to initialize WX library
if not hasattr(wx,"app"): wx.app = wx.PySimpleApp(redirect=False)
panel = SavedPositionsPanel(
    title="Fast Diffractometer Saved Positions (LCLS)",
    name="goniometer_saved_LCLS",
    motors=[SampleX,SampleY,SampleZ,SamplePhi],
    motor_names=["SampleX","SampleY","SampleZ","SamplePhi"],
    formats = ["%+6.3f","%+6.3f","%+6.3f","%+8.3f"],
    nrows=13)
wx.app.MainLoop()
