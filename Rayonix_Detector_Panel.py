#!/usr/bin/env python
"""Rayonix detector control panel for continuous operation 
Author: Friedrich Schotte
Date created: 2017-05-10
Date last modified: 2019-06-02
"""
from rayonix_detector_client import rayonix_detector
from Panel import BasePanel,PropertyPanel,ButtonPanel,TogglePanel,TweakPanel
import wx
from numpy import inf

__version__ = "3.4" # Do not disable down temp file cleanup on close

class Rayonix_Detector_Panel(BasePanel):
    name = "Rayonix_Detector_Panel"
    title = "Rayonix Detector [new]"
    standard_view = [
        "Acquisition",
        "X-ray detector image count",
        "Image",
        "Images left to save",
        "Scratch directory",
        "Bin factor",
        "Server IP Address",
        "Detector IP Address",
    ]
    dirs = ["/net/mx340hs/data/tmp","/net/femto-data/C/Data/tmp","//femto-data/C/Data/tmp",
        "/Mirror/femto-data/C/Data/tmp"]
    server_ip_address_choices = [
        "localhost:2223",
        "id14b4.cars.aps.anl.gov:2223",
        "pico5.cars.aps.anl.gov:2223",
        "pico5.niddk.nih.gov:2223",
        "pico8.niddk.nih.gov:2223",
        "pico20.niddk.nih.gov:2223",
    ]
    detector_ip_address_choices = [
        "mx340hs.cars.aps.anl.gov:2222",
        "pico5.cars.aps.anl.gov:2222",
        "localhost:2222",
        "pico5.niddk.nih.gov:2222",
        "pico8.niddk.nih.gov:2222",
        "pico20.niddk.nih.gov:2222",
    ]
    parameters = [
        [[PropertyPanel,"Status",rayonix_detector,"online"],{"type":"Offline/Online","read_only":True,"refresh_period":1.0}],
        [[TogglePanel,  "Acquisition",rayonix_detector,"acquiring"],{"type":"Start/Cancel","refresh_period":1.0}],
        [[PropertyPanel,"X-ray detector image count",rayonix_detector,"last_image_number"],{"refresh_period":0.25}],
        [[PropertyPanel,"Image",rayonix_detector,"current_image_basename"],{"read_only":True,"refresh_period":1.0}],
        [[PropertyPanel,"Images left to save",rayonix_detector,"nimages"],{"read_only":True,"refresh_period":1.0}],
        [[PropertyPanel,"Scratch image",rayonix_detector,"last_filename"],{"read_only":True,"refresh_period":1.0}],
        [[PropertyPanel,"Bin factor",rayonix_detector,"bin_factor"],{"choices":[1,2,3,4,5,6,8],"refresh_period":1.0}],
        [[PropertyPanel,"Scratch directory",rayonix_detector,"scratch_directory"],{"choices":dirs,"refresh_period":1.0}],
        [[PropertyPanel,"Images to keep",rayonix_detector,"nimages_to_keep"],{"choices":[3,5,10,20],"refresh_period":1.0}],
        [[PropertyPanel,"Server IP address",rayonix_detector,"ip_address"],{"choices":server_ip_address_choices,"refresh_period":1.0}],
        [[PropertyPanel,"Detector IP address",rayonix_detector,"detector_ip_address"],{"choices":detector_ip_address_choices,"refresh_period":1.0}],
        [[PropertyPanel,"Timing mode",rayonix_detector,"timing_mode"],{"choices":rayonix_detector.timing_modes,"refresh_period":1.0}],
        [[PropertyPanel,"ADXV live image",rayonix_detector,"ADXV_live_image"],{"type":"Off/On","refresh_period":1.0}],
        [[PropertyPanel,"Live image",rayonix_detector,"live_image"],{"type":"Off/On","refresh_period":1.0}],
        [[PropertyPanel,"Limit images to keep",rayonix_detector,"limit_files_enabled"],{"type":"Off/On","refresh_period":1.0}],
        [[PropertyPanel,"Auto-start",rayonix_detector,"auto_start"],{"type":"Off/On","refresh_period":1.0}],
    ]
    
    def __init__(self,parent=None):
        BasePanel.__init__(self,
            parent=parent,
            name=self.name,
            title=self.title,
            icon="Rayonix Detector",
            parameters=self.parameters,
            standard_view=self.standard_view,
            label_width=180,
            refresh=False,
            live=False,
        )
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        rayonix_detector.limit_files_enabled = True

        
if __name__ == '__main__':
    from pdb import pm # for debugging
    from redirect import redirect
    redirect("Rayonix_Detector_Panel",level="INFO")
    import wx
    app = wx.App(redirect=False)
    panel = Rayonix_Detector_Panel()
    app.MainLoop()
