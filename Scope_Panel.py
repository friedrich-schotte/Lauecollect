#!/usr/bin/env python
"""Control panel for Lecroy Oscilloscope
Author: Friedrich Schotte
Date created: 2018-10-26
Date last modified: 2022-03-28
Revision comment: Cleanup
"""
__version__ = "1.8.4"

import wx


class Scope_Panel(wx.Frame):
    """Control panel for Lecroy Oscilloscope"""
    name = "Scope_Panel"
    icon = "Scope"

    def __init__(self, name, parent=None):
        """name: """
        wx.Frame.__init__(self, parent=parent)

        self.scope_name = name

        self.Title = self.title
        from Icon import SetIcon
        SetIcon(self, self.icon)
        self.panel = self.ControlPanel
        self.Fit()

        self.Show()

        # Refresh
        self.timer = wx.Timer(self)
        self.timer.Start(5000, oneShot=True)

    @property
    def scope(self):
        from lecroy_scope import lecroy_scope
        scope = lecroy_scope(self.scope_name)
        return scope

    @property
    def title(self):
        title = self.scope_name
        title = title.replace("xray", "X-Ray")
        title = title.replace("_", " ")
        title = title.title()
        return title

    @property
    def ControlPanel(self):
        # Controls and Layout
        panel = wx.Panel(self)
        from EditableControls import ComboBox
        from Controls import Control

        flag = wx.ALIGN_CENTRE_HORIZONTAL | wx.ALL
        border = 2
        l = wx.ALIGN_LEFT
        r = wx.ALIGN_RIGHT
        cv = wx.ALIGN_CENTER_VERTICAL
        a = wx.ALL
        e = wx.EXPAND
        c = wx.ALIGN_CENTER

        frame = wx.BoxSizer()
        panel.SetSizer(frame)

        layout = wx.BoxSizer(wx.VERTICAL)
        frame.Add(layout, flag=e | a, border=10, proportion=1)

        layout_flag = wx.ALIGN_CENTRE | wx.ALL
        border = 0
        width, height = 220, 25

        control = Control(panel, type=ComboBox,
                          globals=globals(),
                          locals=locals(),
                          name=self.name + ".setup",
                          size=(width, height),
                          style=wx.ALIGN_CENTER_HORIZONTAL | wx.TE_PROCESS_ENTER,
                          )
        layout.Add(control, flag=layout_flag, border=border)

        control = Control(panel, type=wx.ToggleButton,
                          globals=globals(),
                          locals=locals(),
                          name=self.name + ".recall",
                          label="Recall",
                          size=(width, height),
                          )
        layout.Add(control, flag=layout_flag, border=border)

        control = Control(panel, type=wx.ToggleButton,
                          globals=globals(),
                          locals=locals(),
                          name=self.name + ".save",
                          label="Save",
                          size=(width, height),
                          )
        layout.Add(control, flag=layout_flag, border=border)

        control = Control(panel, type=wx.StaticText,
                          globals=globals(),
                          locals=locals(),
                          name=self.name + ".trace_directory_size",
                          size=(width, height),
                          style=wx.ALIGN_CENTER_HORIZONTAL,
                          )
        layout.Add(control, flag=layout_flag, border=border)

        control = Control(panel, type=wx.ToggleButton,
                          globals=globals(),
                          locals=locals(),
                          name=self.name + ".emptying_trace_directory",
                          size=(width, height),
                          )
        layout.Add(control, flag=layout_flag, border=border)

        control = Control(panel, type=wx.ToggleButton,
                          globals=globals(),
                          locals=locals(),
                          name=self.name + ".acquiring_waveforms",
                          label="Auto Save",
                          size=(width, height),
                          )
        layout.Add(control, flag=layout_flag, border=border)

        control = Control(panel, type=wx.CheckBox,
                          globals=globals(),
                          locals=locals(),
                          name=self.name + ".auto_acquire",
                          label="Auto Record Traces",
                          size=(width, height),
                          style=wx.ALIGN_CENTER_HORIZONTAL,
                          )
        layout.Add(control, flag=layout_flag, border=border)

        control = Control(panel, type=wx.StaticText,
                          globals=globals(),
                          locals=locals(),
                          name=self.name + ".trace_count",
                          size=(width, height),
                          style=wx.ALIGN_CENTER_HORIZONTAL,
                          )
        layout.Add(control, flag=layout_flag, border=border)

        control = Control(panel, type=wx.StaticText,
                          globals=globals(),
                          locals=locals(),
                          name=self.name + ".trigger_count",
                          size=(width, height),
                          style=wx.ALIGN_CENTER_HORIZONTAL,
                          )
        layout.Add(control, flag=layout_flag, border=border)

        control = Control(panel, type=wx.StaticText,
                          globals=globals(),
                          locals=locals(),
                          name=self.name + ".trace_count_offset",
                          size=(width, height),
                          style=wx.ALIGN_CENTER_HORIZONTAL,
                          )
        layout.Add(control, flag=layout_flag, border=border)

        control = Control(panel, type=wx.StaticText,
                          globals=globals(),
                          locals=locals(),
                          name=self.name + ".timing_jitter",
                          size=(width, height),
                          style=wx.ALIGN_CENTER_HORIZONTAL,
                          )
        layout.Add(control, flag=layout_flag, border=border)

        control = Control(panel, type=wx.StaticText,
                          globals=globals(),
                          locals=locals(),
                          name=self.name + ".timing_offset",
                          size=(width, height),
                          style=wx.ALIGN_CENTER_HORIZONTAL,
                          )
        layout.Add(control, flag=layout_flag, border=border)

        control = Control(panel, type=wx.ToggleButton,
                          globals=globals(),
                          locals=locals(),
                          name=self.name + ".trace_count_synchronized",
                          label="Synchronized",
                          size=(width, height),
                          )
        layout.Add(control, flag=layout_flag, border=border)

        control = Control(panel, type=wx.CheckBox,
                          globals=globals(),
                          locals=locals(),
                          name=self.name + ".auto_synchronize",
                          label="Auto Synchronize",
                          size=(width, height),
                          style=wx.ALIGN_CENTER_HORIZONTAL,
                          )
        layout.Add(control, flag=layout_flag, border=border)

        control = Control(panel, type=wx.ToggleButton,
                          globals=globals(),
                          locals=locals(),
                          name=self.name + ".trace_acquisition_running",
                          label="Data Collection Running",
                          size=(width, height),
                          )
        layout.Add(control, flag=layout_flag, border=border)

        panel.Fit()
        return panel


if __name__ == '__main__':
    from redirect import redirect

    redirect("Scope_Panel")

    app = wx.GetApp() if wx.GetApp() else wx.App()

    # name = "BioCARS.xray_scope"
    name = "BioCARS.laser_scope"
    # name = "BioCARS.diag_scope"
    # name = "BioCARS.timing_scope"
    # name = "LaserLab.laser_scope"

    self = Scope_Panel(name)
    app.MainLoop()
