#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2019-11-13
Date last modified: 2022-05-01
Revision comment: multiple local_machine_names
"""
__version__ = "2.1"

import wx


class Server_Setup_Panel(wx.Frame):
    from thread_property_2 import thread_property

    domain_name = "BioCARS"
    icon = "Server"

    def __init__(self, domain_name=None):
        if domain_name is not None:
            self.domain_name = domain_name
        wx.Frame.__init__(self, parent=None, title=self.title)
        self.panel = wx.Panel(self)

        from Icon import SetIcon
        SetIcon(self, self.icon)

        # Controls
        style = wx.TE_PROCESS_ENTER
        width = 160

        from EditableControls import ComboBox
        self.MachineName = ComboBox(self.panel, style=style, size=(width, -1))
        self.LocalStartupServerRunning = wx.CheckBox(self.panel, label="Startup Server Running")
        self.StartupServers = Startup_Servers_Status_Panel(self.panel, self.domain_name)

        # Callbacks
        self.Bind(wx.EVT_TEXT_ENTER, self.OnEnterMachineName, self.MachineName)
        self.Bind(wx.EVT_COMBOBOX, self.OnEnterMachineName, self.MachineName)
        self.Bind(wx.EVT_CHECKBOX, self.OnLocalStartServerRunning, self.LocalStartupServerRunning)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        # Layout
        self.panel.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.layout = wx.BoxSizer(wx.VERTICAL)
        # Leave a 5-pixel wide border.
        self.panel.Sizer.Add(self.layout, flag=wx.ALL, border=5)

        a = wx.ALL
        e = wx.EXPAND

        label = wx.StaticText(self.panel, label="Local machine:")
        self.layout.Add(label, flag=wx.BOTTOM, border=5)
        self.layout.Add(self.MachineName, flag=a | e)
        self.layout.Add(self.LocalStartupServerRunning, flag=a | e)

        label = wx.StaticText(self.panel, label="All machines:")
        self.layout.Add(label, flag=wx.TOP | wx.BOTTOM, border=5)
        self.layout.Add(self.StartupServers, flag=a | e)

        self.panel.Fit()
        self.Fit()

        self.timer = wx.Timer(self)

        self.values = {}
        self.keep_updated = True

        self.Show()
        self.refresh()

    @property
    def title(self):
        return "Server Setup [%s]" % self.domain_name

    @property
    def servers(self):
        from servers import Servers
        return Servers(self.domain_name)

    @property
    def local_startup_server(self):
        from servers import Local_Startup_Server
        return Local_Startup_Server(self.domain_name)

    def OnEnterMachineName(self, _event):
        name_list = self.MachineName.Value
        names = name_list.split(",")
        names = [name.strip() for name in names]
        self.servers.local_machine_names = names
        self.refresh()

    def OnLocalStartServerRunning(self, event):
        # debug("event.IsChecked(): %s" % event.IsChecked())
        self.local_startup_server.running = event.IsChecked()
        self.refresh()

    def OnRefresh(self, _event=None):
        self.refresh()

    def refresh(self, _event=None):
        """Update the controls and indicators with current values"""
        if self.Shown:
            if "servers.local_machine_names" in self.values:
                name_list = ", ".join(self.values["servers.local_machine_names"])
                self.MachineName.Value = name_list
            if "servers.machine_names" in self.values:
                self.MachineName.Items = self.values["servers.machine_names"]
            if "local_startup_server.running" in self.values:
                self.LocalStartupServerRunning.Value = self.values["local_startup_server.running"]

            self.timer = wx.Timer(self)
            self.Bind(wx.EVT_TIMER, self.refresh, self.timer)
            self.timer.Start(1000, oneShot=True)

    def OnClose(self, _event):
        self.Shown = False
        # self.Destroy() # might crash under Windows
        wx.CallLater(2000, self.Destroy)

    @thread_property
    def keep_updated(self):
        """Periodically refresh the values to be displayed."""
        while True:
            try:
                self.update()
            except RuntimeError:
                break
            from time import sleep
            sleep(1)

    def update(self):
        self.values["servers.local_machine_names"] = self.servers.local_machine_names
        self.values["servers.machine_names"] = self.servers.machine_names
        self.values["local_startup_server.running"] = self.local_startup_server.running


class Startup_Servers_Status_Panel(wx.Panel):
    from thread_property_2 import thread_property

    domain_name = "BioCARS"

    def __init__(self, parent, domain_name=None):
        if domain_name is not None:
            self.domain_name = domain_name
        wx.Panel.__init__(self, parent)

        self.Controls = []
        self.Sizer = wx.BoxSizer(wx.VERTICAL)

        self.values = {}
        self.keep_updated = True

        self.refresh()

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
        self.timer.Start(1000, oneShot=True)

    @property
    def startup_servers(self):
        from servers import Startup_Servers
        return Startup_Servers(self.domain_name)

    def OnTimer(self, _event):
        self.refresh()
        self.timer.Start(1000, oneShot=True)

    def refresh(self):
        self.line_count = len(self.startup_servers)
        for i, server in enumerate(self.startup_servers):
            self.Controls[i].Label = server.machine_name
            key = "startup_servers.%s.running" % i
            if key in self.values:
                self.Controls[i].Enabled = True
                self.Controls[i].Value = self.values[key]

    def get_line_count(self):
        return len(self.Controls)

    def set_line_count(self, n):
        if len(self.Controls) != n:
            while len(self.Controls) < n:
                control = wx.CheckBox(self)
                control.Enabled = False
                flag = wx.EXPAND
                self.Sizer.Add(control, flag=flag)
                self.Controls.append(control)
            while len(self.Controls) > n:
                control = self.Controls.pop()
                control.Destroy()
            self.Sizer.Fit(self)

    line_count = property(get_line_count, set_line_count)

    @thread_property
    def keep_updated(self):
        """Periodically refresh the values to be displayed."""
        while True:
            try:
                self.update()
            except RuntimeError:
                break
            from time import sleep
            sleep(1)

    def update(self):
        for i in range(0, len(self.startup_servers)):
            self.values["startup_servers.%s.running" % i] = \
                self.startup_servers[i].running


if __name__ == '__main__':
    name = "BioCARS"
    # name = "LaserLab"
    # name = "WetLab"
    # name = "TestBench"

    from redirect import redirect

    redirect("Server_Setup_Panel.%s" % name)

    app = wx.GetApp() if wx.GetApp() else wx.App()
    panel = Server_Setup_Panel(name)
    app.MainLoop()
