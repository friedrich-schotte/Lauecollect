#!/usr/bin/env python
"""Friedrich Schotte, Dec 13 2017 - Feb 7 2018"""
from CameraViewer import CameraViewer
import wx
__version__ = "1.8"

wx.app = wx.App(redirect=False) # Needed to initialize WX library

viewer = CameraViewer(name="TestBenchCamera")

wx.app.MainLoop()
