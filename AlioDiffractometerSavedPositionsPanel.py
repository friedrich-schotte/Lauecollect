#!/usr/bin/env python
"""Alio diffractometer
Control panel to save and motor positions.
Author: Friedrich Schotte
Date created: 2009-10-18
Date last modified: 2019-01-27
"""
__version__ = "1.3.1" # logging

from pdb import pm # for debugging

from redirect import redirect
redirect("AlioDiffractometerSavedPositionsPanel")

import wx
app = wx.App(redirect=False) 
from instrumentation import * # -> globals()
from SavedPositionsPanel_2 import SavedPositionsPanel
panel = SavedPositionsPanel(name="alio_diffractometer_saved",globals=globals())
app.MainLoop()
