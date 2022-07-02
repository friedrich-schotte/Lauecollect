#!/usr/bin/env python
"""
Top-level Panel for Anfinrud Wet Lab

Author: Friedrich Schotte
Date created: 2020-05-18
Date last modified: 2021-06-19
Revision comment: Added: Camera_Viewer: domain_name
"""
__version__ = "1.4"

import wx

from Control_Panel import Control_Panel


class WetLab_Panel(Control_Panel):
    name = "WetLab_Panel"
    title = "Wet Lab"
    icon = "NIH"
    domain_name = "WetLab"

    @property
    def ControlPanel(self):
        panel = wx.Panel(self)

        frame = wx.BoxSizer()
        panel.Sizer = frame
        layout = wx.BoxSizer(wx.VERTICAL)
        frame.Add(layout, flag=wx.EXPAND | wx.ALL, border=5, proportion=1)

        from Launch_Button import Launch_Button
        size = (400, -1)
        icon_size = 24
        style = wx.BU_LEFT
        flag = wx.ALIGN_CENTRE | wx.ALL
        space = 10

        control = Launch_Button(
            parent=panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="IOCs && Servers...",
            domain_name=self.domain_name,
            module_name="Servers_Panel",
            command=f"Servers_Panel('{self.domain_name}')",
            icon="Server",
        )
        layout.Add(control, flag=flag)

        layout.AddSpacer(space)

        control = Launch_Button(
            parent=panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="Lab Microscope...",
            domain_name=self.domain_name,
            module_name="Camera_Viewer",
            command=f"Camera_Viewer('{self.domain_name}.Microscope')",
            icon="camera",
        )
        layout.Add(control, flag=flag)

        control = Launch_Button(
            parent=panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="Microfluidics Camera...",
            domain_name=self.domain_name,
            module_name="Camera_Viewer",
            command=f"Camera_Viewer('{self.domain_name}.MicrofluidicsCamera')",
            icon="camera",
        )
        layout.Add(control, flag=flag)

        layout.AddSpacer(space)

        panel.Fit()
        return panel


if __name__ == '__main__':
    from redirect import redirect

    redirect("WetLab.WetLab_Panel")
    app = wx.GetApp() if wx.GetApp() else wx.App()
    panel = WetLab_Panel()
    app.MainLoop()
