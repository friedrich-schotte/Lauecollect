#!/usr/bin/env python
"""Cavro Centris Syringe Pump
Friedrich Schotte, Jun 8, 2017 - Jun 8, 2017
"""
from cavro_centris_syringe_pump_IOC import syringe_pump_IOC
from Panel import BasePanel,PropertyPanel,ButtonPanel,TogglePanel,TweakPanel
import wx
from numpy import inf

__version__ = "1.0.2" # baud rate

class TemperatureControllerIOCPanel(BasePanel):
    name = "TemperatureControllerIOCPanel"
    title = "Temperature Controller IOC"
    standard_view = [
        "Enabled",
        "EPICS Record",
        "Port",
    ]

    parameters = [
        [[TogglePanel,"Enabled",syringe_pump_IOC,"EPICS_enabled"],{"type":"Off/On","refresh_period":1.0}],
        [[PropertyPanel,"EPICS Record",syringe_pump_IOC,"prefix"],{"refresh_period":1.0,"choices":["NIH:PUMP","TEST:PUMP"]}],
        [[PropertyPanel,"Port",syringe_pump_IOC,"port_name"],{"read_only":True}],
    ]
    
    def __init__(self,parent=None):
        BasePanel.__init__(self,
            parent=parent,
            name=self.name,
            title=self.title,
            parameters=self.parameters,
            standard_view=self.standard_view,
            label_width=90,
            refresh=True,
            live=True,
        )
        self.Bind(wx.EVT_CLOSE,self.OnClose)

    def OnClose(self,event=None):
        temperature_controller_IOC.EPICS_enabled = False
        self.Destroy()
        
if __name__ == '__main__':
    from pdb import pm # for debugging
    import logging
    from tempfile import gettempdir
    
    logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s",
        filename=gettempdir()+"/temperature_controller_debug.log")
    temperature_controller.logging = True
    
    if not "app" in globals(): app = wx.App(redirect=False) # to initialize WX...
    panel = TemperatureControllerIOCPanel()
    app.MainLoop()
