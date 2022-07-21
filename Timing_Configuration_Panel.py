#!/usr/bin/env python
"""
Configuration panel for the BioCARS FPGA timing system.
Saving and restoring settings

Author: Friedrich Schotte
Date created: 2019-03-26
Date last modified: 2022-07-18
Revision comment: Cleanup
"""
__version__ = "1.2.1"

import wx

from Control_Panel import Control_Panel


class Timing_Configuration_Panel(Control_Panel):
    name = "Timing_Configuration_Panel"
    icon = "Timing System"
    timing_system_name = "BioCARS"

    def __init__(self, timing_system_name=None):
        if timing_system_name is not None:
            self.timing_system_name = timing_system_name
        super().__init__()

    @property
    def timing_system(self):
        from timing_system_client import timing_system_client
        return timing_system_client(self.timing_system_name)

    @property
    def title(self):
        return "Timing Configuration [%s]" % self.timing_system_name

    @property
    def ControlPanel(self):
        from Controls import Control
        from EditableControls import ComboBox, TextCtrl
        panel = wx.Panel(self)

        frame = wx.BoxSizer()
        panel.Sizer = frame

        layout = wx.BoxSizer(wx.VERTICAL)
        frame.Add(layout, flag=wx.EXPAND | wx.ALL, border=10, proportion=1)

        width = 160

        control = Control(panel, type=ComboBox,
                          globals=globals(),
                          locals=locals(),
                          name=self.name + ".EPICS_Record",
                          size=(width, -1),
                          style=wx.TE_PROCESS_ENTER,
                          )
        layout.Add(control, flag=wx.ALIGN_CENTRE | wx.ALL)

        control = Control(panel, type=TextCtrl,
                          globals=globals(),
                          locals=locals(),
                          name=self.name + ".IP_Address",
                          size=(width, -1),
                          )
        layout.Add(control, flag=wx.ALIGN_CENTRE | wx.ALL)

        control = Control(panel, type=ComboBox,
                          globals=globals(),
                          locals=locals(),
                          name=self.name + ".Configuration",
                          size=(width, -1),
                          style=wx.TE_PROCESS_ENTER,
                          )
        layout.Add(control, flag=wx.ALIGN_CENTRE | wx.ALL)

        control = Control(panel, type=wx.Button,
                          globals=globals(),
                          locals=locals(),
                          name=self.name + ".Load",
                          size=(width, -1),
                          )
        layout.Add(control, flag=wx.ALIGN_CENTRE | wx.ALL)

        control = Control(panel, type=wx.Button,
                          globals=globals(),
                          locals=locals(),
                          name=self.name + ".Save",
                          size=(width, -1),
                          )
        layout.Add(control, flag=wx.ALIGN_CENTRE | wx.ALL)

        panel.Fit()
        return panel


if __name__ == '__main__':
    timing_system_name = "BioCARS"
    # timing_system_name = "LaserLab"

    from redirect import redirect

    redirect("Timing_Configuration_Panel")
    app = wx.GetApp() if wx.GetApp() else wx.App()
    self = Timing_Configuration_Panel(timing_system_name)
    app.MainLoop()
