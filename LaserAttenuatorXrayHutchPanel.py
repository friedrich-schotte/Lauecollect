#!/usr/bin/env python
"""
Control panel for variable laser attenuator
Friedrich Schotte, APS, 8 Jun 2009 - 16 Nov 2014
"""
__version__ = "1.2" # trans -> trans2
import wx
from LaserAttenuatorPanel import LaserAttenuatorPanel
from id14 import trans2

wx.app = wx.App(redirect=False) # Needed to initialize WX library
panel = LaserAttenuatorPanel(trans2,title="Laser Attenuator [in X-ray Hutch]")
wx.app.MainLoop()
