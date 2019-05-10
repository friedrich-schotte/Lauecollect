#!/usr/bin/env python
"""SAXS-WAXS Methods
Author: Friedrich Schotte
Date created: 2018-08-22
Date last modified: 2018-09-13
"""
__version__ = "1.0.1" # autoreload

from SavedPositionsPanel_2 import SavedPositionsPanel

if __name__ == '__main__':
    from pdb import pm # for debugging
    import logging # for debugging
    from tempfile import gettempdir
    logfile = gettempdir()+"/SAXS_WAXS_Methods_Panel.log"
    logging.basicConfig(level=logging.INFO,filename=logfile,
        format="%(asctime)s %(levelname)s: %(message)s")
    import autoreload

    import wx
    app = wx.App(redirect=False) 
    from instrumentation import * # -> globals()
    panel = SavedPositionsPanel(name="SAXS_WAXS_methods",globals=globals())
    app.MainLoop()
