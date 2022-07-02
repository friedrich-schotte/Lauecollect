#!/usr/bin/env python
"""
Instrumentation for Testing in Friedrich's Office

Author: Friedrich Schotte
Date created: 2020-06-15
Date last modified: 2022-06-13
Revision comment: Using Configuration_Table_Panel
"""
__version__ = "1.5.2"

import wx

from Control_Panel import Control_Panel


class TestBench_Panel(Control_Panel):
    name = "TestBench_Panel"
    title = "Test Bench"
    icon = "NIH"
    domain_name = "TestBench"

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
            label="Timing System...",
            domain_name=self.domain_name,
            module_name="Timing_Panel",
            command=f"Timing_Panel('{self.domain_name}')",
            icon="Timing System",
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
            module_name="ConfigurationsPanel",
            command=f"ConfigurationsPanel('{self.domain_name}')",
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
            label="Timing Modes...",
            domain_name=self.domain_name,
            module_name="Configuration_Table_Panel",
            command=f"Configuration_Table_Panel('{self.domain_name}.timing_modes')",
            icon="Tool",
        )
        layout.Add(control, flag=flag)

        layout.AddSpacer(space)

        control = Launch_Button(
            parent=panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="Test Bench Camera...",
            domain_name=self.domain_name,
            module_name="Camera_Viewer",
            command=f"Camera_Viewer('{self.domain_name}.TestBenchCamera')",
            icon="camera",
        )
        layout.Add(control, flag=flag)

        layout.AddSpacer(space)

        control = Launch_Button(
            parent=panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="Ramsey RF Generator...",
            domain_name=self.domain_name,
            module_name="Ramsey_RF_Generator_Panel",
            command="Ramsey_RF_Generator_Panel()",
            icon="Ramsey RF Generator",
        )
        layout.Add(control, flag=flag)

        panel.Fit()
        return panel


if __name__ == '__main__':
    from redirect import redirect

    redirect("TestBench.TestBench_Panel")
    app = wx.GetApp() if wx.GetApp() else wx.App()
    panel = TestBench_Panel()
    app.MainLoop()
