#!/usr/bin/env python
"""Control panel for simulated beamline environment of APS 14-IDB 
Author: Friedrich Schotte,
Date created: 2016-06-13
Date last modified: 2019-10-04
Revision comment: Cleanup
"""
__version__ = "1.9.2"

import wx

from Panel import BasePanel


class ID14_Simulator_Panel(BasePanel):
    name = "sim_id14"
    title = "14ID-B Simulator"

    def __init__(self, parent=None):
        from sim_id14 import sim_id14

        self.standard_view = [
            motor.description for motor in sim_id14.motors]

        from Panel import PropertyPanel, TogglePanel, TweakPanel
        self.layout = [[
            motor.description,
            [TweakPanel, [], {"object": sim_id14, "name": motor.name + ".value", "digits": 4, "width": 60}],
            [TogglePanel, [], {"object": sim_id14, "name": motor.name + ".EPICS_autostart", "type": "Off/On", "width": 40}],
            [PropertyPanel, [], {"object": sim_id14, "name": motor.name + ".prefix", "width": 120}]
        ] for motor in sim_id14.motors]

        BasePanel.__init__(self,
                           parent=parent,
                           name=self.name,
                           title=self.title,
                           layout=self.layout,
                           standard_view=self.standard_view,
                           label_width=170,
                           icon="BioCARS",
                           )


if __name__ == '__main__':
    from redirect import redirect

    redirect("BioCARS.SimID14Panel")

    app = wx.GetApp() if wx.GetApp() else wx.App()
    panel = ID14_Simulator_Panel()
    app.MainLoop()
