#!/usr/bin/env python
"""High-speed X-ray Chopper
Control panel to save and restore motor positions.
Author: Friedrich Schotte
Date created: 10/30/2017
Date last modified: 03/05/2018
"""
__version__ = "2.0" # using name=

from SavedPositionsPanel_2 import SavedPositionsPanel

if __name__ == '__main__':
    from pdb import pm # for debugging
    import logging # for debugging
    from tempfile import gettempdir
    logfile = gettempdir()+"/HeatLoadChopperModesPanel.log"
    logging.basicConfig(level=logging.INFO,filename=logfile,
        format="%(asctime)s %(levelname)s: %(message)s")

    import wx
    app = wx.App(redirect=False) 
    from instrumentation import * # -> globals()
    panel = SavedPositionsPanel(name="heat_load_chopper_modes",globals=globals())
    app.MainLoop()
