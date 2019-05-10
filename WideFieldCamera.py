#!/usr/bin/env python
"""Low magnification, wide field of view video camera of the diffractometer,
used for aligning a crystal in the X-ray beam
Friedrich Schotte, 19 Feb 2008 - 26 Jun 2017"""
__version__ = "1.8.1" # name changed to WideFieldCamera

import logging; from tempfile import gettempdir
logfile = gettempdir()+"/WideFieldCamera.log"
logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s",
    filename=logfile)
logging.debug("WideFieldCamera started")
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
    name="WideFieldCamera",
    title="Wide-Field camera [advanced] (60 deg)",
    orientation=0,
    pixelsize=0.00465, # CCD pixel size 4.65 um, magnification ca. 1X
    camera_angle=60,
)

wx.app.MainLoop()

logging.debug("WideFieldCamera closed")

