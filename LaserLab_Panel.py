#!/usr/bin/env python
"""
Top-level Panel for Anfinrud Laser Lab

Author: Friedrich Schotte
Date created: 2020-05-18
Date last modified: 2022-06-13
Revision comment: Using Configuration_Table_Panel
"""
__version__ = "1.13.2"

import wx

from Control_Panel import Control_Panel


class LaserLab_Panel(Control_Panel):
    name = "LaserLab_Panel"
    title = "Laser Lab"
    icon = "NIH"
    domain_name = "LaserLab"

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
            command="Servers_Panel('%s')" % self.domain_name,
            icon="Server",
        )
        layout.Add(control, flag=flag)

        layout.AddSpacer(space)

        control = Launch_Button(
            parent=panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="Timing System...",
            domain_name=self.domain_name,
            module_name="Timing_Panel",
            command="Timing_Panel('%s')" % self.domain_name,
            icon="Timing System",
        )
        layout.Add(control, flag=flag)

        layout.AddSpacer(space)

        control = Launch_Button(
            parent=panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="PP Acquire...",
            domain_name=self.domain_name,
            module_name="Acquisition_Panel",
            command="Acquisition_Panel('%s')" % self.domain_name,
            icon="Tool",
        )
        layout.Add(control, flag=flag)

        layout.AddSpacer(space)

        control = Launch_Button(
            parent=panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="Configurations...",
            domain_name=self.domain_name,
            module_name="Environment_Configurations_Panel",
            command=f"Environment_Configurations_Panel('{self.domain_name}')",
            icon="Utility",
        )
        layout.Add(control, flag=flag)

        layout.AddSpacer(space)

        control = Launch_Button(
            parent=panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="Modes / Configurations...",
            domain_name=self.domain_name,
            module_name="Configurations_Panel",
            command=f"Configurations_Panel('{self.domain_name}')",
            icon="Tool",
        )
        layout.Add(control, flag=flag)

        control = Launch_Button(
            parent=panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="Method Configuration...",
            domain_name=self.domain_name,
            module_name="Configuration_Table_Panel",
            command=f"Configuration_Table_Panel('{self.domain_name}.method')",
            icon="Tool",
        )
        layout.Add(control, flag=flag)

        layout.AddSpacer(space)

        control = Launch_Button(
            parent=panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="Laser Lab Camera...",
            domain_name=self.domain_name,
            module_name="Camera_Viewer",
            command=f"Camera_Viewer('{self.domain_name}.LaserLabCamera')",
            icon="camera",
        )
        layout.Add(control, flag=flag)

        layout.AddSpacer(space)

        control = Launch_Button(
            parent=panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="FLIR Camera 1...",
            domain_name=self.domain_name,
            module_name="Camera_Viewer",
            command=f"Camera_Viewer('{self.domain_name}.FLIR1')",
            icon="camera",
        )
        layout.Add(control, flag=flag)

        control = Launch_Button(
            parent=panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="FLIR Camera 2...",
            domain_name=self.domain_name,
            module_name="Camera_Viewer",
            command=f"Camera_Viewer('{self.domain_name}.FLIR2')",
            icon="camera",
        )
        layout.Add(control, flag=flag)

        control = Launch_Button(
            parent=panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="FLIR Camera 3...",
            domain_name=self.domain_name,
            module_name="Camera_Viewer",
            command=f"Camera_Viewer('{self.domain_name}.FLIR2')",
            icon="camera",
        )
        layout.Add(control, flag=flag)

        control = Launch_Button(
            parent=panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="FLIR Camera 4...",
            domain_name=self.domain_name,
            module_name="Camera_Viewer",
            command=f"Camera_Viewer('{self.domain_name}.FLIR4')",
            icon="camera",
        )
        layout.Add(control, flag=flag)

        control = Launch_Button(
            parent=panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="FLIR Camera 5...",
            domain_name=self.domain_name,
            module_name="Camera_Viewer",
            command=f"Camera_Viewer('{self.domain_name}.FLIR5')",
            icon="camera",
        )
        layout.Add(control, flag=flag)

        layout.AddSpacer(space)

        control = Launch_Button(
            parent=panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="Laser Oscilloscope...",
            domain_name=self.domain_name,
            module_name="Scope_Panel",
            command=f"Scope_Panel('{self.domain_name}.laser_scope')",
            icon="oscilloscope",
        )
        layout.Add(control, flag=flag)

        layout.AddSpacer(space)

        control = Launch_Button(
            parent=panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="Channel Archiver...",
            domain_name=self.domain_name,
            module_name="Channel_Archiver_Panel",
            command=f"Channel_Archiver_Panel('{self.domain_name}')",
            icon="Archiver",
        )
        layout.Add(control, flag=flag)

        control = Launch_Button(
            parent=panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="Channel Archiver Viewer...",
            domain_name=self.domain_name,
            module_name="Channel_Archiver_Viewer",
            command=f"Channel_Archiver_Viewer('{self.domain_name}')",
            icon="Archiver",
        )
        layout.Add(control, flag=flag)

        panel.Fit()
        return panel


if __name__ == '__main__':
    # import autoreload
    from redirect import redirect

    redirect("LaserLab.LaserLab_Panel")
    app = wx.GetApp() if wx.GetApp() else wx.App()
    panel = LaserLab_Panel()
    app.MainLoop()
