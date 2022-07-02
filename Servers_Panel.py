#!/usr/bin/env python
"""Controls startup of servers

Authors: Friedrich Schotte
Date created: 2017-11-13
Date last modified: 2022-05-01
Revision comment: multiple local_machine_names
"""
__version__ = "2.6"

import logging
import traceback

import wx


class Servers_Panel(wx.Frame):
    domain_name = "BioCARS"
    title = "IOCs & Servers"  # for name of App bundle
    icon = "Server"

    @property
    def db_name(self):
        return "Servers_Panel/%s" % self.domain_name

    from db_property import db_property
    default_size = (300, 200)
    size = db_property("size", default_size, local=True)
    min_size = (150, 50)

    from collections import OrderedDict
    AllView = list(range(0, 30))
    CustomView = db_property("CustomView", list(range(0, 3)), local=True)
    views = OrderedDict([("All", "AllView"), ("Custom", "CustomView")])
    view = db_property("view", "All", local=True)

    attributes = [
        "N_running",
        "machine_names",
    ]
    refresh_period = 10.0  # s
    setup = db_property("setup", False, local=True)

    @property
    def default_filename(self):
        return self.servers.default_filename

    filename = db_property("filename", default_filename, local=True)

    def __init__(self, domain_name=None):
        if domain_name is not None:
            self.domain_name = domain_name

        wx.Frame.__init__(self, parent=None)
        self.title = "%s [%s]" % (self.title, self.domain_name)
        self.Title = self.title
        from Icon import SetIcon
        SetIcon(self, self.icon)

        # Controls
        self.panel = wx.Panel(self)
        self.controls = []

        # Menus
        menuBar = wx.MenuBar()

        menu = wx.Menu()
        menu.Append(wx.ID_OPEN, "&Open...\tCtrl+O")
        menu.Append(wx.ID_SEPARATOR)
        menu.Append(wx.ID_SAVEAS, "&Save As...\tCtrl+S")
        menuBar.Append(menu, "&File")

        self.ViewMenu = wx.Menu()
        for i, label in enumerate(self.views):
            self.ViewMenu.AppendCheckItem(10 + i, label)
        self.ViewMenu.AppendSeparator()
        menuBar.Append(self.ViewMenu, "&View")

        self.SetupMenu = wx.Menu()
        self.ID_SETUP = 200
        self.SetupMenu.AppendCheckItem(self.ID_SETUP, "Setup")
        self.SetupMenu.Check(self.ID_SETUP, self.setup)
        self.SetupMenu.AppendSeparator()
        self.SetupMenu.Append(201, "Add Line")
        self.SetupMenu.Append(202, "Remove Line")
        self.SetupMenu.AppendSeparator()
        self.SetupMenu.Append(203, "Server Setup...")
        menuBar.Append(self.SetupMenu, "&More")

        menu = wx.Menu()
        menu.Append(wx.ID_ABOUT, "About...")
        menuBar.Append(menu, "&Help")

        self.SetMenuBar(menuBar)

        # Callbacks
        self.Bind(wx.EVT_MENU, self.OnOpen, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.OnSaveAs, id=wx.ID_SAVEAS)

        self.Bind(wx.EVT_MENU_OPEN, self.OnOpenView)
        for i in range(0, len(self.views)):
            self.Bind(wx.EVT_MENU, self.OnSelectView, id=10 + i)
        self.Bind(wx.EVT_MENU, self.OnSetup, id=self.ID_SETUP)
        self.Bind(wx.EVT_MENU, self.OnAdd, id=201)
        self.Bind(wx.EVT_MENU, self.OnRemove, id=202)
        self.Bind(wx.EVT_MENU, self.OnServerSetup, id=203)

        self.Bind(wx.EVT_MENU, self.OnAbout, id=wx.ID_ABOUT)

        self.Bind(wx.EVT_SIZE, self.OnResize)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        # Layout
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel.Sizer = self.sizer
        self.update_controls()
        self.Show()

        # Refresh
        self.values = {}
        self.old_values = {}

        self.Bind(wx.EVT_TIMER, self.OnUpdate)
        from threading import Thread
        self.thread = Thread(target=self.keep_updated)
        self.thread.daemon = True
        self.thread.start()

    @property
    def servers(self):
        from servers import Servers
        return Servers(self.domain_name)

    def keep_updated(self):
        """Periodically refresh the displayed settings."""
        from time import time, sleep
        while True:
            try:
                t0 = time()
                while time() < t0 + self.refresh_period:
                    sleep(0.5)
                if self.Shown:
                    self.update_data()
                    if self.data_changed:
                        event = wx.PyCommandEvent(wx.EVT_TIMER.typeId, self.Id)
                        # call OnUpdate in GUI thread
                        wx.PostEvent(self.EventHandler, event)
            except RuntimeError:
                break

    def refresh(self):
        """Force update"""
        from threading import Thread
        self.thread = Thread(target=self.refresh_background)
        self.thread.daemon = True
        self.thread.start()

    def refresh_background(self):
        """Force update"""
        self.update_data()
        if self.data_changed:
            event = wx.PyCommandEvent(wx.EVT_TIMER.typeId, self.Id)
            wx.PostEvent(self.EventHandler, event)  # call OnUpdate in GUI thread

    def update_data(self):
        """Retrieve status information"""
        self.old_values = dict(self.values)  # make a copy
        for n in self.attributes:
            try:
                self.values[n] = getattr(self, n)
            except Exception as msg:
                logging.error("%s\n%s" % (msg, traceback.format_exc()))

    @property
    def N_running(self):
        return sum([c.server.running for c in self.controls_shown])

    @property
    def machine_names(self):
        return self.servers.local_machine_names

    @property
    def NShown(self):
        return len(self.controls_shown)

    @property
    def controls_shown(self):
        return [c for c in self.controls if c.Shown]

    @property
    def data_changed(self):
        """Did the last 'update_data' change the data to be plotted?"""
        changed = (self.values != self.old_values)
        return changed

    def OnUpdate(self, _event):
        """Periodically refresh the displayed settings."""
        self.refresh_status()

    def refresh_status(self, _event=None):
        """Update title to show whether all checks passed"""
        title = self.title
        if "machine_names" in self.values:
            title += ", " + ", ".join(self.values["machine_names"])
        if "N_running" in self.values:
            title += ", %r of %r running" % (self.values["N_running"], self.NShown)
        self.Title = title

    def update_controls(self):
        if len(self.controls) != self.servers.N:
            for control in self.controls:
                control.Destroy()
            self.controls = []
            for server in self.servers:
                self.controls += [Server_Control(self.panel, server.name)]
            for i in range(0, len(self.controls)):
                self.sizer.Add(self.controls[i], flag=wx.ALL | wx.EXPAND)
            self.setup = self.SetupMenu.IsChecked(self.ID_SETUP)
            for control in self.controls:
                control.setup = self.setup
            self.set_size()

        if self.view not in self.views:
            self.view = list(self.views)[0]
        self.View = getattr(self, self.views[self.view])

    def set_size(self):
        if self.size == self.default_size:
            self.panel.Sizer.Fit(self)
        else:
            # debug("Saved size: %r" % (self.size,))
            w, h = self.size
            w_min, h_min = self.min_size
            if w < w_min:
                w = w_min
            if h < h_min:
                h = h_min
            self.size = w, h
            # debug("Setting size to %r" % (self.size,))
            w, h = self.size
            self.Size = w, h + 1  # size change needed, otherwise panel does not fill window
            self.Size = w, h

    def get_View(self):
        """Which control to show? List of 0-based integers"""
        view = [i for (i, c) in enumerate(self.controls) if c.Shown]
        return view

    def set_View(self, value):
        currently_shown = [c.Shown for c in self.controls]
        shown = [False] * len(self.controls)
        for i in value:
            if i < len(shown):
                shown[i] = True
        if shown != currently_shown:
            for i in range(0, len(self.controls)):
                self.controls[i].Shown = shown[i]
            self.set_size()

    View = property(get_View, set_View)

    def OnOpen(self, _event):
        from os.path import exists, dirname, basename
        directory = dirname(self.filename)
        while not exists(directory) and len(directory) > 2:
            directory = dirname(directory)
        filename = directory + "/" + basename(self.filename)

        dlg = wx.FileDialog(
            parent=self,
            message="Load Settings",
            defaultDir=dirname(filename),
            defaultFile=basename(filename),
            wildcard="Text Files (*.txt)|*.txt",
            style=wx.FD_OPEN,
        )
        OK = (dlg.ShowModal() == wx.ID_OK)
        if OK:
            self.filename = dlg.GetPath()
        dlg.Destroy()
        if OK:
            self.servers.load(self.filename)
            self.update_controls()

    def OnSaveAs(self, _event):
        from os.path import exists, dirname, basename
        directory = dirname(self.filename)
        while not exists(directory) and len(directory) > 2:
            directory = dirname(directory)
        filename = directory + "/" + basename(self.filename)

        dlg = wx.FileDialog(
            parent=self,
            message="Save Settings As",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
            wildcard="Text Files (*.txt)|*.txt",
            defaultFile=basename(filename),
            defaultDir=dirname(filename),
        )
        OK = (dlg.ShowModal() == wx.ID_OK)
        if OK:
            self.filename = dlg.GetPath()
        dlg.Destroy()
        if OK:
            self.servers.save(self.filename)

    def OnOpenView(self, _event):
        """Called if the "View" menu is selected"""
        for i in range(0, len(self.views)):
            self.ViewMenu.Check(10 + i, list(self.views)[i] == self.view)
        for i in range(0, len(self.controls)):
            title = self.controls[i].Title
            if title == "":
                title = "Untitled %d" % (i + 1)
            ID = 100 + i
            if not self.ViewMenu.FindItemById(ID):
                self.ViewMenu.AppendCheckItem(ID, title)
            self.ViewMenu.SetLabel(ID, title)
            self.ViewMenu.Check(ID, self.controls[i].Shown)
            self.ViewMenu.Enable(ID, self.view != "All")
            self.Bind(wx.EVT_MENU, self.OnView, id=100 + i)
        for i in range(len(self.controls), 50):
            ID = 100 + i
            if self.ViewMenu.FindItemById(ID):
                self.ViewMenu.RemoveItem(ID)

    def OnSelectView(self, event):
        """Called if the view is toggled between 'All' and 'Custom'
        from the 'View ' menu."""
        n = event.Id - 10
        if 0 <= n < len(self.views):
            self.view = list(self.views)[n]
            self.View = getattr(self, list(self.views.values())[n])

    def OnView(self, event):
        """Called if one of the items of the "View" menu is checked or
        unchecked."""
        n = event.Id - 100
        self.controls[n].Shown = event.IsChecked()
        self.set_size()
        setattr(self, self.views[self.view], self.View)  # save modified view

    def OnSetup(self, _event):
        """Enable 'setup' mode, allowing the panel to be configured"""
        self.setup = self.SetupMenu.IsChecked(self.ID_SETUP)
        for control in self.controls:
            control.setup = self.setup
        self.set_size()

    def OnAdd(self, _event):
        self.servers.N += 1
        new_line = self.servers.N - 1
        if new_line not in self.CustomView:
            self.CustomView += [new_line]
        self.update_controls()

    def OnRemove(self, _event):
        if self.servers.N > 0:
            self.servers.N -= 1
        self.update_controls()

    def OnServerSetup(self, _event):
        self.server_setup_panel.start()

    @property
    def server_setup_panel(self):
        from application import application
        return application(
            domain_name=self.domain_name,
            module_name="Server_Setup_Panel",
            command=f"Server_Setup_Panel({self.domain_name!r})",
        )

    def OnAbout(self, _event):
        """Show panel with additional parameters"""
        from About import About
        About(self)

    def OnResize(self, event):
        # debug("%r" % event.Size)
        event.Skip()
        self.size = tuple(self.Size)

    def OnClose(self, _event):
        """Called when the window's close button is clicked"""
        self.Destroy()


class Server_Control(wx.Panel):
    refresh_period = 1.0

    def __init__(self, parent, name, shown=False):
        self.name = name
        self.values = {
            "label": "",
            "runnable": False,
            "running": False,
            "is_local": True,
            "formatted_value": "",
            "OK": True,
            "test_code_OK": False
        }
        self.old_values = {}

        wx.Panel.__init__(self, parent)
        self.Shown = shown
        self.Title = "Test %s" % self.name
        self.myEnabled = wx.CheckBox(self)
        self.myEnabled.Enabled = False
        style = wx.TE_READONLY | wx.BORDER_NONE  # | wx.TE_DONTWRAP
        self.myLabel = wx.TextCtrl(self, size=(470, -1), style=style)
        self.myLabel.BackgroundColour = self.BackgroundColour
        from wx.lib.buttons import GenButton
        self.State = GenButton(self, size=(25, 20))
        self.Setup = wx.Button(self, size=(60, -1), label="Setup...")
        self.Setup.Shown = False
        self.Log = wx.Button(self, size=(50, -1), label="Log...")

        self.Bind(wx.EVT_CHECKBOX, self.OnEnable, self.myEnabled)
        self.Bind(wx.EVT_BUTTON, self.OnState, self.State)
        self.Bind(wx.EVT_BUTTON, self.OnSetup, self.Setup)
        self.Bind(wx.EVT_BUTTON, self.OnLog, self.Log)

        # Layout
        self.layout = wx.BoxSizer(wx.HORIZONTAL)
        flag = wx.ALL | wx.EXPAND
        self.layout.Add(self.myEnabled, flag=flag)
        self.layout.Add(self.myLabel, flag=flag, proportion=1)
        self.layout.Add(self.State, flag=flag)
        self.layout.Add(self.Setup, flag=flag)
        self.layout.Add(self.Log, flag=flag)

        # Leave a 10 pixel wide border.
        self.box = wx.BoxSizer(wx.VERTICAL)
        self.box.Add(self.layout, flag=wx.ALL, border=5)
        self.SetSizer(self.box)
        self.Fit()

        self.refresh_label()

        # Periodically refresh the displayed settings.
        self.Bind(wx.EVT_TIMER, self.OnUpdate)
        from threading import Thread
        self.thread = Thread(target=self.keep_updated, name=self.name)
        self.thread.daemon = True
        self.thread.start()

    @property
    def attributes(self):
        return list(self.values.keys())

    @property
    def server(self):
        from servers import Server
        return Server(self.name)

    @property
    def domain_name(self):
        domain_name = "BioCARS"
        if "." in self.name:
            domain_name = self.name.split(".", 1)[0]
        return domain_name

    @property
    def base_name(self):
        return self.name.split(".", 1)[-1]

    def keep_updated(self):
        """Periodically refresh the displayed settings."""
        from time import time, sleep
        while True:
            try:
                t0 = time()
                if self.Shown:
                    self.update_data()
                    if self.data_changed:
                        event = wx.PyCommandEvent(wx.EVT_TIMER.typeId, self.Id)
                        # call OnUpdate in GUI thread
                        wx.PostEvent(self.EventHandler, event)
                while time() < t0 + self.refresh_period:
                    sleep(0.5)
            except RuntimeError:
                break

    def OnUpdate(self, _event):
        """Periodically refresh the displayed settings."""
        self.refresh_status()

    def refresh(self):
        """Force update"""
        from threading import Thread
        self.thread = Thread(target=self.refresh_background,
                             name=self.name + ".refresh")
        self.thread.daemon = True
        self.thread.start()

    def refresh_background(self):
        """Force update"""
        self.update_data()
        if self.data_changed:
            event = wx.PyCommandEvent(wx.EVT_TIMER.typeId, self.Id)
            wx.PostEvent(self.EventHandler, event)  # call OnUpdate in GUI thread

    def update_data(self):
        """Retrieve status information"""
        self.old_values = dict(self.values)  # make a copy
        for n in self.attributes:
            try:
                self.values[n] = getattr(self.server, n)
            except Exception as msg:
                logging.error("%s\n%s" % (msg, traceback.format_exc()))

    @property
    def data_changed(self):
        """Did the last 'update_data' change the data to be plotted?"""
        changed = (self.values != self.old_values)
        return changed

    def refresh_label(self, _event=None):
        """Update the controls with current values"""
        self.Title = self.server.label
        # self.myEnabled.Value = self.server.running
        self.myLabel.Value = self.server.label

    def refresh_status(self, _event=None):
        """Update the controls with current values"""
        self.Title = self.values["label"]
        self.myEnabled.Enabled = self.values["runnable"]
        self.myEnabled.Value = self.values["running"]

        red = (255, 0, 0)
        green = (0, 255, 0)
        gray = (180, 180, 180)
        black = (0, 0, 0)

        if self.values["is_local"]:
            color = (0, 0, 0)
        else:
            color = (64, 64, 64)
        self.myLabel.ForegroundColour = color
        self.myLabel.Value = "%s: %s" % ((self.values["label"]), self.values["formatted_value"])
        color = green if self.values["OK"] else red
        if not self.values["test_code_OK"]:
            color = gray
        self.State.BackgroundColour = color
        self.State.ForegroundColour = color
        self.State.Refresh()  # work-around for a GenButton bug in Windows

    def OnEnable(self, event):
        # logging.debug("%s.running = %r" % (self.server,value))
        value = event.IsChecked()
        try:
            self.server.running = value
        except Exception as msg:
            logging.error("%r\n%r" % (msg, traceback.format_exc()))
        self.myEnabled.Value = self.server.running
        self.refresh()

    def get_setup(self):
        """'Setup' mode enabled? (Allows reconfiguring parameters)"""
        value = self.Setup.Shown
        return value

    def set_setup(self, value):
        self.Setup.Shown = value
        self.Layout()
        self.Fit()

    setup = property(get_setup, set_setup)

    def OnState(self, _event):
        """Start/Stop server"""
        try:
            self.server.running = not self.server.running
        except Exception as msg:
            logging.error("%r\n%r" % (msg, traceback.format_exc()))
        self.refresh()

    def OnSetup(self, _event):
        """Bring up configuration panel"""
        dlg = SetupPanel(self, self.name)
        dlg.CenterOnParent()
        dlg.Show()

    def OnLog(self, _event):
        self.log_viewer.start()

    @property
    def log_viewer(self):
        from application import application
        return application(
            domain_name=self.domain_name,
            module_name="Log_Viewer",
            command=f"Log_Viewer({self.server.logfile_name!r})",
        )


class SetupPanel(wx.Frame):
    def __init__(self, parent, name):
        self.name = name
        wx.Frame.__init__(self, parent=parent, title="Setup")
        from Icon import SetIcon
        SetIcon(self, "Server")
        self.panel = wx.Panel(self)

        # Controls
        from EditableControls import TextCtrl, ComboBox
        style = wx.TE_PROCESS_ENTER
        self.Mnemonic = TextCtrl(self.panel, size=(320, -1), style=style)
        self.myLabel = TextCtrl(self.panel, size=(320, -1), style=style)
        self.Command = TextCtrl(self.panel, size=(320, -1), style=style)

        self.MachineName = ComboBox(self.panel, size=(320, -1), style=style)
        self.AutoStart = wx.CheckBox(self.panel, size=(320, -1))
        self.LogfileBasename = TextCtrl(self.panel, size=(320, -1), style=style)
        self.LogLevel = ComboBox(self.panel, size=(320, -1), style=style)
        self.Value = TextCtrl(self.panel, size=(320, -1), style=style)
        self.Format = TextCtrl(self.panel, size=(320, -1), style=style)
        self.Test = TextCtrl(self.panel, size=(320, -1), style=style)

        # Callbacks
        self.Bind(wx.EVT_TEXT_ENTER, self.OnMnemonic, self.Mnemonic)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnLabel, self.myLabel)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnCommand, self.Command)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnMachineName, self.MachineName)
        self.Bind(wx.EVT_CHECKBOX, self.OnAutoStart, self.AutoStart)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnLogfileBasename, self.LogfileBasename)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnLogLevel, self.LogLevel)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnValue, self.Value)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnFormat, self.Format)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnTest, self.Test)
        self.Bind(wx.EVT_SIZE, self.OnResize)

        # Layout
        self.layout = wx.BoxSizer()
        grid = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
        flag = wx.ALIGN_BOTTOM | wx.ALL | wx.EXPAND

        label = "Mnemonic:"
        grid.Add(wx.StaticText(self.panel, label=label), flag=flag)
        grid.Add(self.Mnemonic, flag=flag, proportion=1)
        label = "Label:"
        grid.Add(wx.StaticText(self.panel, label=label), flag=flag)
        grid.Add(self.myLabel, flag=flag, proportion=1)
        label = "Command:"
        grid.Add(wx.StaticText(self.panel, label=label), flag=flag)
        grid.Add(self.Command, flag=flag, proportion=1)
        label = "Machine name:"
        grid.Add(wx.StaticText(self.panel, label=label), flag=flag)
        grid.Add(self.MachineName, flag=flag, proportion=1)
        label = "Auto start:"
        grid.Add(wx.StaticText(self.panel, label=label), flag=flag)
        grid.Add(self.AutoStart, flag=flag, proportion=1)
        label = "Logfile basename:"
        grid.Add(wx.StaticText(self.panel, label=label), flag=flag)
        grid.Add(self.LogfileBasename, flag=flag, proportion=1)
        label = "Log level:"
        grid.Add(wx.StaticText(self.panel, label=label), flag=flag)
        grid.Add(self.LogLevel, flag=flag, proportion=1)
        label = "Value:"
        grid.Add(wx.StaticText(self.panel, label=label), flag=flag)
        grid.Add(self.Value, flag=flag, proportion=1)
        label = "Format:"
        grid.Add(wx.StaticText(self.panel, label=label), flag=flag)
        grid.Add(self.Format, flag=flag, proportion=1)
        label = "Test:"
        grid.Add(wx.StaticText(self.panel, label=label), flag=flag)
        grid.Add(self.Test, flag=flag, proportion=1)
        # Leave a 10-pixel wide space around the panel.
        self.layout.Add(grid, flag=wx.EXPAND | wx.ALL, proportion=1, border=10)

        self.panel.SetSizer(self.layout)
        self.panel.Fit()
        self.Fit()

        # Initialization
        self.refresh()

    @property
    def server(self):
        from servers import Server
        return Server(self.name)

    @property
    def domain_name(self):
        domain_name = "BioCARS"
        if "." in self.name:
            domain_name = self.name.split(".", 1)[0]
        return domain_name

    @property
    def base_name(self):
        return self.name.split(".", 1)[-1]

    def refresh(self):
        self.myLabel.Value = self.server.label
        self.Mnemonic.Value = self.server.mnemonic
        self.Command.Value = self.server.command
        self.MachineName.Value = self.server.machine_name
        self.MachineName.Choices = self.server.machine_names
        self.AutoStart.Value = self.server.auto_start
        self.LogfileBasename.Value = self.server.logfile_basename
        self.LogLevel.Value = self.server.log_level
        self.LogLevel.Choices = ["DEBUG", "INFO", "WARNING", "ERROR"]
        self.Value.Value = self.server.value_code
        self.Format.Value = self.server.format_code
        self.Test.Value = self.server.test_code

    def OnMnemonic(self, _event):
        self.server.mnemonic = self.Mnemonic.Value
        self.refresh()

    def OnLabel(self, _event):
        self.server.label = self.myLabel.Value
        self.refresh()

    def OnCommand(self, _event):
        self.server.command = self.Command.Value
        self.refresh()

    def OnMachineName(self, _event):
        self.server.machine_name = self.MachineName.Value
        self.refresh()

    def OnAutoStart(self, _event):
        self.server.auto_start = self.AutoStart.Value
        self.refresh()

    def OnLogfileBasename(self, _event):
        self.server.logfile_basename = self.LogfileBasename.Value
        self.refresh()

    def OnLogLevel(self, _event):
        self.server.log_level = self.LogLevel.Value
        self.refresh()

    def OnValue(self, _event):
        self.server.value_code = self.Value.Value
        self.refresh()

    def OnFormat(self, _event):
        self.server.format_code = self.Format.Value
        self.refresh()

    def OnTest(self, _event):
        self.server.test_code = self.Test.Value
        self.refresh()

    def OnResize(self, event):
        """Rearrange contents to fit best into new size"""
        # debug("%r" % event.Size)
        self.panel.Fit()
        event.Skip()


if __name__ == '__main__':
    from redirect import redirect

    domain_name = "BioCARS"
    # domain_name = "LaserLab"
    # domain_name = "WetLab"
    # domain_name = "TestBench"

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    redirect(f"{domain_name}.{Servers_Panel.__name__}", format=msg_format)
    logging.info("Started")  # Needed, otherwise panel locks up

    app = wx.GetApp() if wx.GetApp() else wx.App()
    self = Servers_Panel(domain_name)
    app.MainLoop()
