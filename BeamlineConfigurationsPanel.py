#!/usr/bin/env python
"""Control panel to save and restore motor positions.
Author: Friedrich Schotte
Date created: 2017-06-28
Date last modified: 2018-10-25
"""
__version__ = "2.0" # using SavedPositionsPanel_2

import wx
from SavedPositionsPanel_2 import SavedPositionsPanel
app = wx.App(redirect=False) 
from instrumentation import * # -> globals()
name = "beamline_configuration"
SavedPositionsPanel(name=name,globals=globals())
app.MainLoop()
