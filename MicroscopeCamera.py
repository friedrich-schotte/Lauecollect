#!/usr/bin/env python
"""High-magnification, small field of view video camera of the diffractometer,
used for aligneing a crystal in the X-ray beam
Friedrich Schotte, 19 Feb 2008 - 6 Jul 2017"""
__version__ = "1.8.1" # __main__

import logging; from tempfile import gettempdir
logfile = gettempdir()+"/MicroscopeCamera.log"
logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s",
    filename=logfile)
logging.debug("MicroscopeCamera started")
from os import chmod
try: chmod(logfile,0666)
except Exception,msg: print("%s: %s" % (logfile,msg))

import wx
wx.app = wx.App(redirect=False)

from SampleAlignmentViewer import SampleAlignmentViewer
# Except "name" and "title" the parameters passed to "SampleAlignmentViewer"
# are just default values that can be overridden by user-editable settings
# within the Camera application. The default values are noly used at first run,
# or when the settigns file is lost or otherwise unusable.
viewer = SampleAlignmentViewer(
    name="MicroscopeCamera",
    title="Microscope [advanced] (-30 deg)",
    orientation=0,mirror=True,
    pixelsize=0.000526, 
    camera_angle=-30,
)

wx.app.MainLoop()

logging.debug("MicroscopeCamera closed")
