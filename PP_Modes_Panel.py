#!/usr/bin/env python
"""
Grapical User Interface for FPGA Timing System.
Author: Friedrich Schotte
Date created: 2019-03-26
Date last modified: 2019-03-26
"""
__version__ = "1.0" 

from logging import debug,info,warn,error

from SavedPositionsPanel_2 import SavedPositionsPanel
class PP_Modes_Panel(SavedPositionsPanel):
    name = "timing_modes"


if __name__ == '__main__':
    from pdb import pm # for debugging
    from redirect import redirect
    redirect("PP_Modes_Panel")
    import wx
    app = wx.App(redirect=False) 
    panel = PP_Modes_Panel()
    app.MainLoop()
