#!/usr/bin/env python
"""
Control panel
Author: Friedrich Schotte
Date created: 2018-10-26
Date last modified: 2018-10-26
"""
__version__ = "1.0"

from SavedPositionsPanel_2 import SavedPositionsPanel

if __name__ == '__main__':
    from pdb import pm # for debugging
    import logging # for debugging
    from tempfile import gettempdir
    logfile = gettempdir()+"/Methods_Configuration_Panel.log"
    logging.basicConfig(level=logging.INFO,filename=logfile,
        format="%(asctime)s %(levelname)s: %(message)s")

    import wx
    app = wx.App(redirect=False) 
    from instrumentation import * # -> globals()
    panel = SavedPositionsPanel(name="method",globals=globals())
    app.MainLoop()
