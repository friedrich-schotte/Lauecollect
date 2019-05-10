#!/usr/bin/env python
"""Friedrich Schotte, Dec 13 2017 - Dec 13 2017"""
from CameraViewer import CameraViewer
import wx
__version__ = "1.8"

wx.app = wx.App(redirect=False) # Needed to initialize WX library

viewer = CameraViewer (
    name="MicrofluidicsCamera",
    title="Microfluidics Camera",
    pixelsize=0.00465
)

wx.app.MainLoop()
