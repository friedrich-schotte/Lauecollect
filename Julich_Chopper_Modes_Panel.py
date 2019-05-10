#!/usr/bin/env python
"""High-speed X-ray Chopper
Control panel to save and restore motor positions.
Author: Friedrich Schotte
Date created: 2017-10-16
Date last modified: 2018-09-13
"""
__version__ = "1.0" 

from SavedPositionsPanel_2 import SavedPositionsPanel

if __name__ == '__main__':
    from pdb import pm # for debugging
    import logging # for debugging
    from tempfile import gettempdir
    logfile = gettempdir()+"/Julich_Chopper_Modes_Panel.log"
    logging.basicConfig(level=logging.INFO,filename=logfile,
        format="%(asctime)s %(levelname)s: %(message)s")
    import autoreload

    import wx
    app = wx.App(redirect=False) 
    from instrumentation import * # -> globals()
    panel = SavedPositionsPanel(name="Julich_chopper_modes",globals=globals())
    app.MainLoop()
