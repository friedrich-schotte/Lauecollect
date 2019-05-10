#!/usr/bin/env python
"""Camera to monitor the laser beam profile at the sample.
Installed by Hyun Sun Cho, May 20, 2009"""
from GigE_camera import GigE_camera
from CameraViewer import CameraViewer
import wx
__version__ = "1.3.1"

camera = GigE_camera("id14b-prosilica3.cars.aps.anl.gov")
#camera = GigE_camera("id14b-prosilica3.biocarsvideo.net")

# Needed to initialize WX library
if not "app" in globals(): app = wx.PySimpleApp(redirect=False)

def show():
    global viewer
    # 1:1 imaging: pixel size is same as CCD pixel, 4.65 um 
    viewer = CameraViewer (camera,
        title="Laser Beam Profile (at sample)",name="BeamProfile",
        pixelsize=0.00465,orientation=+90)
    app.MainLoop()

# The following is only executed when run as stand-alone application.
if __name__ == '__main__': show()
