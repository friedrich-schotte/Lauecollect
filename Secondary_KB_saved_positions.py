#!/usr/bin/env python
"""BioCARS Methods
Author: Friedrich Schotte, Robert Henning
Date created: 2018-09-21
Date last modified: 2018-09-21
"""
__version__ = "1.0.1" # autoreload

from SavedPositionsPanel_2 import SavedPositionsPanel

if __name__ == '__main__':
    from pdb import pm # for debugging
    import logging # for debugging
    from tempfile import gettempdir
    logfile = gettempdir()+"/Secondary_KB_saved_positions.log"
    logging.basicConfig(level=logging.INFO,filename=logfile,
        format="%(asctime)s %(levelname)s: %(message)s")
    import autoreload

    import wx
    app = wx.App(redirect=False) 
    from instrumentation import * # -> globals()
    panel = SavedPositionsPanel(name="Secondary KB Saved Positions",globals=globals())
    app.MainLoop()
