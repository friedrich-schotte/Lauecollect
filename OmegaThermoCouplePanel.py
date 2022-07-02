#!/usr/bin/env python
"""Control panel for Omega Thermocoule Reader
Friedrich Schotte, Nov 10, 2009 - Mar 28, 2017"""
import wx
from omega_thermocouple import thermocouple
from EditableControls import ComboBox,TextCtrl
from logging import debug
from Panel import BasePanel,PropertyPanel,TogglePanel,TweakPanel

__version__ = "1.3.1" # Title, icon

class OmegaThermocouplePanel(BasePanel):
    name = "OmegaThermocouplePanel"
    title = "Thermocouple"
    standard_view = [
        "Temperature",
    ]
    parameters = [
        [[PropertyPanel,"Temperature",thermocouple,"VAL"],{"read_only":True,"unit":"C","digits":1}],
        [[PropertyPanel,"EPICS Record",thermocouple,"__prefix__"],{"choices":["NIH:TC"],"refresh_period":1.0}],
        [[PropertyPanel,"Serial port",thermocouple,"COMM"],{"read_only":True}],
        [[PropertyPanel,"Type",thermocouple,"TCTYPE"],{"choices":["B","C","E","J","K","N","R","S","T"]}],
        [[PropertyPanel,"Moving average",thermocouple,"MFILTER"],{"choices":[0,1,2,4,8,16,32,63]}],
        [[PropertyPanel,"Impulse filter",thermocouple,"IFILTER"],{"choices":[0,1,2,4,8,16,32,63]}],
    ]

    def __init__(self,parent=None):        
        BasePanel.__init__(self,
            parent=parent,
            name=self.name,
            title=self.title,
            parameters=self.parameters,
            standard_view=self.standard_view,
            refresh=True,
            live=True,
            label_width=90,
            icon="Omega Thermocouple Reader",
        )

if __name__ == '__main__':
    from pdb import pm
    ##import logging; logging.basicConfig(level=logging.DEBUG)

    app = wx.GetApp() if wx.GetApp() else wx.App()
    panel = OmegaThermocouplePanel()
    app.MainLoop()
