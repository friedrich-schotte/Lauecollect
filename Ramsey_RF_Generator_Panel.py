#!/usr/bin/env python
"""
Ramsay RSG1000B RF Signal Generator

Authors: Friedrich Schotte
Date created: 2018-01-23
Date last modified: 2018-01-23
"""
import wx
##import CA; CA.monitor_always = False
from EditableControls import ComboBox,TextCtrl # customized versions
from Ramsey_RF_generator import Ramsey_RF_generator as device
from Panel import BasePanel,PropertyPanel

__version__ = "2.0.1" # SCAN, no "Live" and "Refresh" buttons

class ControlPanel(BasePanel):
    name = "Ramsay_RF_Generator"
    title = "Ramsay RF Generator"
    icon = "Ramsay RF Generator"
    standard_view = [
        "RF output",
    ]

    def __init__(self,parent=None):        
        parameters = [
            [[PropertyPanel,"RF output", device,"VAL" ],{"type":"OFF/ON","refresh_period":1.0}],
            [[PropertyPanel,"Scan Time", device,"SCAN" ],{"unit":"s","refresh_period":1.0}],
        ]
        BasePanel.__init__(self,
            parent=parent,
            name=self.name,
            icon=self.icon,
            title=self.title,
            parameters=parameters,
            standard_view=self.standard_view,
            subname=True,
            subpanels=[SettingsPanel],
        )

class SettingsPanel(BasePanel):
    name = "settings"
    title = "Settings"
    standard_view = [
        "Port",
        "Nom. update rate",
        "Act. update rate",
    ]

    def __init__(self,parent=None):        
        parameters = [
            [[PropertyPanel,"Port",      device,"COMM" ],{"refresh_period":1.0}],
            [[PropertyPanel,"Nom. update rate",device,"SCAN"],{"format":"%.3f","unit":"s","refresh_period":1.0}],
            [[PropertyPanel,"Act. update rate",device,"SCANT"],{"format":"%.3f","unit":"s","refresh_period":1.0}],
        ]
        BasePanel.__init__(self,
            parent=parent,
            name=self.name,
            title=self.title,
            parameters=parameters,
            standard_view=self.standard_view,
            subname=True,
        )


if __name__ == '__main__': 
    # Needed to initialize WX library
    if not "app" in globals(): app = wx.App(redirect=False)
    panel = ControlPanel()
    app.MainLoop()
