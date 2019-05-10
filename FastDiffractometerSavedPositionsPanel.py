#!/usr/bin/env python
"""High-speed diffractometer
Control panel to save and motor positions.
Friedrich Schotte 31 Oct 2013 - 26 Sep 2014"""
__version__ = "1.2.1"

from pdb import pm
from SavedPositionsPanel import SavedPositionsPanel
from id14 import SampleX,SampleY,SampleZ,SamplePhi,diffractometer as d
import wx

# Needed to initialize WX library
if not hasattr(wx,"app"): wx.app = wx.App(redirect=False)
panel = SavedPositionsPanel(
    title="Fast Diffractometer Saved Positions",
    name="goniometer_saved",
    motors=[SampleX,SampleY,SampleZ,SamplePhi,
            d.ClickCenterX,d.ClickCenterY,d.ClickCenterZ],
    motor_names=["SampleX","SampleY","SampleZ","SamplePhi",
                 "Center X","Center Y","Center Z"],
    formats = ["%+6.3f","%+6.3f","%+6.3f","%+8.3f","%+6.3f","%+6.3f","%+6.3f"],
    nrows=13)
wx.app.MainLoop()
