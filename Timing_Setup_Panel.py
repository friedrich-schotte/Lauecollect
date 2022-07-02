#!/usr/bin/env python
"""
Graphical User Interface for FPGA Timing System.
Author: Friedrich Schotte
Date created: 2018-12-04
Date last modified: 2022-04-12
Revision comment: Using timing system server
"""
__version__ = "1.5"

import wx


class Timing_Setup_Panel(wx.Frame):
    icon = "timing-system"
    domain_name = "BioCARS"

    def __init__(self, domain_name=None):
        if domain_name is not None:
            self.domain_name = domain_name

        wx.Frame.__init__(self, parent=None)

        self.timer = wx.Timer(self)

        self.name = "Timing_Setup_Panel.%s" % self.domain_name
        self.title = "Timing System Setup (%s)" % self.domain_name

        self.Title = self.title

        panel = wx.Panel(self)

        from Icon import SetIcon
        SetIcon(self, self.icon)

        # Controls
        from EditableControls import ComboBox
        style = wx.TE_PROCESS_ENTER
        width = 160

        self.Prefix = ComboBox(panel, style=style, size=(width, -1))

        self.Address = wx.TextCtrl(panel, style=wx.TE_READONLY, size=(width, -1))
        self.Address.Enabled = False

        # Callbacks
        self.Bind(wx.EVT_TEXT_ENTER, self.OnEnterPrefix, self.Prefix)
        self.Bind(wx.EVT_COMBOBOX, self.OnEnterPrefix, self.Prefix)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        # Layout
        layout = wx.GridBagSizer(1, 1)
        a = wx.ALIGN_CENTRE_VERTICAL
        e = wx.EXPAND

        row = 0
        label = wx.StaticText(panel, label="EPICS Record:")
        layout.Add(label, (row, 0), flag=a)
        layout.Add(self.Prefix, (row, 1), flag=a | e)

        row += 1
        label = wx.StaticText(panel, label="IP Address (auto detect):")
        layout.Add(label, (row, 0), flag=a)
        layout.Add(self.Address, (row, 1), flag=a | e)

        # Leave a 5-pixel wide border.
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(layout, flag=wx.ALL, border=5)
        panel.SetSizer(box)
        panel.Fit()
        self.Fit()

        self.Show()
        self.refresh()

    @property
    def timing_system(self):
        from timing_system_client import timing_system_client
        return timing_system_client(self.domain_name)

    def OnEnterPrefix(self, _event):
        """Called if EPICS record prefix is changed"""
        self.timing_system.timing_system_prefix = self.Prefix.Value
        self.refresh()

    def OnRefresh(self, _event=None):
        self.refresh()

    def refresh(self, _event=None):
        """Update the controls and indicators with current values"""
        if self.Shown:
            self.Prefix.Value = self.timing_system.timing_system_prefix
            self.Prefix.Items = self.timing_system.prefixes
            self.Address.Value = self.timing_system.ip_address
            self.timer = wx.Timer(self)
            self.Bind(wx.EVT_TIMER, self.refresh, self.timer)
            self.timer.Start(1000, oneShot=True)

    def OnClose(self, _event):
        self.Shown = False
        wx.CallLater(2000, self.Destroy)  # calling self.Destroy() directly might crash on Windows


if __name__ == '__main__':
    from redirect import redirect

    redirect("Timing_Setup_Panel")
    app = wx.GetApp() if wx.GetApp() else wx.App()
    panel = Timing_Setup_Panel("BioCARS")
    app.MainLoop()
