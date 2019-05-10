#!/usr/bin/env python
"""
Control panel to save and restore motor positions.
Author: Friedrich Schotte
Date created: 2017-02-17
Date last modified: 2017-02-17
"""
__version__ = "1.0" 

from SavedPositionsPanel_2 import SavedPositionsPanel
from instrumentation import laser_optics_modes

class LaserOpticsModesPanel(SavedPositionsPanel):
    title = "Laser Optics Modes"
    configuration = laser_optics_modes
    def __init__(self):
        SavedPositionsPanel.__init__(self,
            configuration=self.configuration,
            title=self.title,
        )

if __name__ == '__main__':
    from pdb import pm # for debugging
    import logging # for debugging
    from tempfile import gettempdir
    logfile = gettempdir()+"/LaserOpticsModesPanel.log"
    logging.basicConfig(level=logging.INFO,filename=logfile,
        format="%(asctime)s %(levelname)s: %(message)s")

    import wx
    app = wx.App(redirect=False) 
    panel = LaserOpticsModesPanel()
    app.MainLoop()
