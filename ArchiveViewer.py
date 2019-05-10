#!/usr/bin/env python
"""
Archive EPICS process variable via Channel Access
Author: Friedrich Schotte
Date created: 10/4/2017
Date last modified: 10/5/2017
"""
__version__ = "1.0" 

import wx
from Panel import BasePanel
from TimeChart import TimeChart

class ArchiveViewer(BasePanel):
    name = "ArchiveViewer"
    title = "Archive Viewer"
    standard_view = ["Data"]
    def __init__(self,PV,parent=None):        
        from channel_archiver import channel_archiver
        log = channel_archiver.logfile(PV)
        parameters = [
            [[TimeChart,"Data",log,"date time","value"],{"refresh_period":2}],
        ]
        BasePanel.__init__(self,
            name=self.name,
            title=self.title,
            icon="Archiver",
            parent=parent,
            parameters=parameters,
            standard_view=self.standard_view,
            refresh=False,
            live=False,
        )

if __name__ == "__main__":
    from pdb import pm # for debugging
    import autoreload
    import logging # for debugging
    from tempfile import gettempdir
    logfile = gettempdir()+"/ArchiveViewer.log"
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s %(levelname)s: %(message)s",
        filename=logfile,
    )
    
    from sys import argv
    if len(argv) > 1: PV = argv[1]
    else: PV = "NIH:TEMP.RBV"
    
    app = wx.App(redirect=False)
    panel = ArchiveViewer(PV)
    app.MainLoop()
