#!/usr/bin/env python
"""
Control panel for thermoelectric circulating water chiller.
Author: Friedrich Schotte, Jun 1, 2009 - Oct 31, 2017

Fault Codes:
The fault byte is a bit map (0 = OK, 1 = Fault):
value| CA number | bit   | fault
    0|  0        |       | no faults
    1|  1        | bit 0 | Tank Level Low
    4|  3        | bit 2 | Temperature above alarm range
   16|  5        | bit 4 | RTD Fault
   32|  6        | bit 5 | Pump Fault
  128|  8        | bit 7 | Temperature below alarm range

"""


import wx
##import CA; CA.monitor_always = False
from EditableControls import ComboBox,TextCtrl # customized versions
from oasis_chiller import chiller
from numpy import nan,isnan
from Panel import BasePanel,PropertyPanel

__version__ = "2.0.1" # SCAN, no "Live" and "Refresh" buttons
#Changed About field to include fault codes: Valentyn Stadnytskyi Oct 15 2018

class OasisChillerPanel(BasePanel):
    name = "OasisChiller"
    title = "Oasis Chiller"
    standard_view = [
        "Set Point",
        "Actual Temperature",
    ]

    def __init__(self,parent=None):        
        parameters = [
            [[PropertyPanel,"Set Point", chiller,"VAL" ],{"unit":"C","refresh_period":1.0}],
            [[PropertyPanel,"Actual Temperature", chiller,"RBV" ],{"unit":"C","read_only":True,"refresh_period":1.0}],
            [[PropertyPanel,"Faults",chiller,"faults"],{"refresh_period":1.0}],
        ]
        BasePanel.__init__(self,
            parent=parent,
            name=self.name,
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
        "High Limit",
        "Low Limit",
        "Nom. update rate",
        "Act. update rate",
    ]

    def __init__(self,parent=None):        
        parameters = [
            [[PropertyPanel,"Port",      chiller,"COMM" ],{"refresh_period":1.0}],
            [[PropertyPanel,"Low Limit", chiller,"LLM" ],{"unit":"C","refresh_period":1.0}],
            [[PropertyPanel,"High Limit",chiller,"HLM"],{"unit":"C","refresh_period":1.0}],
            [[PropertyPanel,"Nom. update rate",chiller,"SCAN"],{"format":"%.3f","unit":"s","refresh_period":1.0}],
            [[PropertyPanel,"Act. update rate",chiller,"SCANT"],{"format":"%.3f","unit":"s","refresh_period":1.0}],
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
    from pdb import pm
    # Needed to initialize WX library
    if not "app" in globals(): app = wx.App(redirect=False)
    panel = OasisChillerPanel()
    app.MainLoop()
