#!/usr/bin/env python
"""Friedrich Schotte, 13 Dec 2012 - 16 Mar 2018"""
from CameraViewer import CameraViewer
import wx
__version__ = "1.8" # no hard-coded paramneters

wx.app = wx.App(redirect=False) # Needed to initialize WX library
viewer = CameraViewer(name="Microscope")
wx.app.MainLoop()
