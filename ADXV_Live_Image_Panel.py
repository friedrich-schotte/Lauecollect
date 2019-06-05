#!/usr/bin/env python
"""Instruct the ADXV image display application to display a live image during
data collection

Author: Friedrich Schotte
Date created: 2019-06-02
Date last modified: 2019-06-02
"""
from ADXV_live_image import ADXV_live_image
from Panel import BasePanel,PropertyPanel,ButtonPanel,TogglePanel,TweakPanel
import wx
from numpy import inf

__version__ = "1.0" 

class ADXV_Live_Image_Panel(BasePanel):
    name = "ADXV_Live_Image_Panel"
    title = "ADXV Live Image"
    standard_view = [
        "Live image",
        "ADXV status",
        "Filename",
        "Live filename",
        "Refresh interval",
    ]
    parameters = [
        [[TogglePanel,  "Live image",ADXV_live_image,"live_image"],{"type":"Off/On","refresh_period":0.25}],
        [[PropertyPanel,"ADXV status",ADXV_live_image,"online"],{"type":"Offline/Online","read_only":True,"refresh_period":0.25}],
        [[PropertyPanel,"Filename",ADXV_live_image,"image_filename"],{"read_only":True,"refresh_period":1.0}],
        [[PropertyPanel,"Live filename",ADXV_live_image,"live_image_filename"],{"read_only":True,"refresh_period":0.25}],
        [[PropertyPanel,"IP Address",ADXV_live_image,"ip_address"],{"refresh_period":1.0}],
        [[PropertyPanel,"Refresh interval",ADXV_live_image,"refresh_interval"],{"format":"%g","unit":"s","refresh_period":1.0}],
    ]
    
    def __init__(self,parent=None):
        BasePanel.__init__(self,
            parent=parent,
            name=self.name,
            title=self.title,
            icon="ADXV",
            parameters=self.parameters,
            standard_view=self.standard_view,
            label_width=140,
            width=260,
            refresh=False,
            live=False,
        )
        self.Bind(wx.EVT_CLOSE,self.OnClose)

    def OnClose(self,event=None):
        # Shut down background tasks.
        ADXV_live_image.live_image = False
        self.Destroy()
        
if __name__ == '__main__':
    from pdb import pm # for debugging
    from redirect import redirect
    redirect("ADXV_Live_Image_Panel")
    import wx
    app = wx.App(redirect=False) 
    panel = ADXV_Live_Image_Panel()
    app.MainLoop()
