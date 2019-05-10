#!/usr/bin/env python
"""EPICS server for ILX Lightwave LDT-5948 Precision Temperature Controller
Friedrich Schotte, Nov 8, 2016 - Jan 22, 2017"""
from temperature_controller_server import temperature_controller_IOC
from temperature_controller_driver import temperature_controller
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
        "Baud Rate",
    ]

    parameters = [
        [[TogglePanel,"Enabled",temperature_controller_IOC,"EPICS_enabled"],{"type":"Off/On","refresh_period":1.0}],
        [[PropertyPanel,"EPICS Record",temperature_controller_IOC,"prefix"],{"refresh_period":1.0,"choices":["NIH:TEMP","NIH_TEST:TEMP"]}],
        [[PropertyPanel,"Baud Rate",temperature_controller,"baudrate.value"],{"refresh_period":1.0,"choices":[9600,14400,19200,38400,57600]}],
        [[PropertyPanel,"Port",temperature_controller,"port_name"],{"read_only":True}],
        [[PropertyPanel,"ID String",temperature_controller,"id"],{"read_only":True}],
        [[PropertyPanel,"Set Point",temperature_controller,"setT.value"],{"digits":3,"unit":"C","choices":[100,80,22,20,0,-20]}],
        [[PropertyPanel,"Temperature",temperature_controller,"readT.value"],{"digits":3,"unit":"C","read_only":True}],
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
