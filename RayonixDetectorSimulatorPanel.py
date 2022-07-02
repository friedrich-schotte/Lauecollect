#!/usr/bin/env python
"""Rayonix Detector Simulator
Author: Friedrich Schotte
Date created: 2017-03-20
Date last modified: 2019-06-01
"""
from rayonix_detector_simulator import det
from Panel import BasePanel,PropertyPanel,ButtonPanel,TogglePanel,TweakPanel
import wx
from numpy import inf

__version__ = "1.2.4" # label_width, trigger_PV_choices

trigger_PV_choices = [
    "NIH:TIMING.registers.ch7_state.count",
    "NIH:TESTBENCH.registers.ch7_state.count",
]

class RayonixDetectorSimulatorPanel(BasePanel):
    name = "RayonixDetectorSimulatorPanel"
    title = "Rayonix Detector Simulator"
    standard_view = [
        "TCP server",
        "Acquisition",
        "Image number",
        "Bin factor",
        "Trigger period",
    ]

    parameters = [
        [[TogglePanel,  "TCP server",det,"server_running"],{"type":"Offline/Online","refresh_period":1.0}],
        [[PropertyPanel,"TCP port",det,"port"],{"choices":[2222,2000,2001],"refresh_period":1.0}],
        [[PropertyPanel,"Bin factor",det,"bin_factor"],{"choices":[1,2,3,4,5,6,8],"refresh_period":1.0}],
        [[TogglePanel,  "Acquisition",det,"acquiring"],{"type":"Start/Cancel","refresh_period":1.0}],
        [[PropertyPanel,"Image number",det,"frame_number"],{"refresh_period":0.25}],
        [[PropertyPanel,"Images to acquire",det,"n_frames"],{"refresh_period":1.0}],
        [[PropertyPanel,"First frame number",det,"first_frame_number"],{"refresh_period":1.0}],
        [[PropertyPanel,"Filename base",det,"filename_base"],{"refresh_period":1.0}],
        [[PropertyPanel,"Filename suffix",det,"filename_suffix"],{"refresh_period":1.0}],
        [[PropertyPanel,"Number field width",det,"number_field_width"],{"refresh_period":1.0}],
        [[PropertyPanel,"Current image",det,"last_filename"],{"read_only":True,"refresh_period":1.0}],
        [[PropertyPanel,"Trigger",det,"external_trigger"],{"type":"Timer/EPICS PV","refresh_period":1.0}],
        [[PropertyPanel,"Trigger EPICS PV",det,"trigger_PV"],{"choices":trigger_PV_choices,"refresh_period":1.0}],
        [[PropertyPanel,"Trigger EPICS status",det,"trigger_PV_OK"],{"type":"Offline/Online","read_only":True,"refresh_period":1.0}],
        [[PropertyPanel,"Trigger period",det,"trigger_period"],{"digits":3,"unit":"s","choices":[2.0,1.0,0.1],"refresh_period":1.0}],
    ]
    
    def __init__(self,parent=None):
        BasePanel.__init__(self,
            parent=parent,
            name=self.name,
            title=self.title,
            icon="Rayonix Detector",
            parameters=self.parameters,
            standard_view=self.standard_view,
            label_width=120,
            refresh=False,
            live=False,
        )
        self.Bind(wx.EVT_CLOSE,self.OnClose)

    def OnClose(self,event=None):
        det.server_running = False
        self.Destroy()
        ##if hasattr(wx,"app"): app.Exit()
        
if __name__ == '__main__':
    from pdb import pm # for debugging
    import logging
    from tempfile import gettempdir
    import rayonix_detector_simulator

    logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s",
        filename=gettempdir()+"/RayonixDetectorSimulatorPanel.log")
    rayonix_detector_simulator.verbose_logging = True
    
    app = wx.GetApp() if wx.GetApp() else wx.App()
    panel = RayonixDetectorSimulatorPanel()
    app.MainLoop()
