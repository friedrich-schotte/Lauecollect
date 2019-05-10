#!/usr/bin/env python
"""Timing System Simulator

Author: Friedrich Schotte
Date created: Oct 19, 2016
Date last modified: Oct 19, 2017
"""
from timing_system_simulator import timing_system_simulator
t = timing_system_simulator
from Panel import BasePanel,PropertyPanel,ButtonPanel,TogglePanel,TweakPanel
import wx
from numpy import inf

__version__ = "1.0"

class TimingSystemSimulatorPanel(BasePanel):
    name = "TimingSystemSimulatorPanel"
    title = "Timing System Simulator"
    icon = "timing-system"
    standard_view = [
        "TCP server",
        "TCP port",
    ]

    parameters = [
        [[TogglePanel,  "TCP server",t,"server_running"],{"type":"Offline/Online","refresh_period":1.0}],
        [[PropertyPanel,"TCP port",t,"port"],{"choices":[2000,2001,2002,2003],"refresh_period":1.0}],
    ]
    
    def __init__(self,parent=None):
        BasePanel.__init__(self,
            parent=parent,
            name=self.name,
            title=self.title,
            icon=self.icon,
            parameters=self.parameters,
            standard_view=self.standard_view,
            label_width=90,
            refresh=False,
            live=False,
        )
        self.Bind(wx.EVT_CLOSE,self.OnClose)

    def OnClose(self,event=None):
        t.server_running = False
        self.Destroy()
        ##if hasattr(wx,"app"): wx.app.Exit()
        
if __name__ == '__main__':
    from pdb import pm # for debugging
    import logging
    from tempfile import gettempdir
    import rayonix_detector_simulator

    logfile = gettempdir()+"/TimingSystemSimulatorPanel.log"
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s (levelname)s: %(message)s",
        filename=logfile,
    )
    
    if not hasattr(wx,"app"): wx.app = wx.App(redirect=False) # initialize WX
    panel = RayonixDetectorSimulatorPanel()
    wx.app.MainLoop()
