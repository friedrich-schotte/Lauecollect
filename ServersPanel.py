#!/usr/bin/env python
"""Controls when data collection is suspended, in case the X-ray beam is
down

Author: Friedrich Schotte, Valentyn Stadnytskyi
Date created: 2017-11-13
Date modified: 2019-06-01
"""
__version__ = "1.2.1" # newline at last line

from logging import debug,info,warn,error
import traceback

from servers import servers
import wx, wx3_compatibility
from EditableControls import TextCtrl,ComboBox

class ServersPanel(wx.Frame):
    name = "ServersPanel"
    from setting import setting
    from collections import OrderedDict as odict
    AllView = range(0,20)
    CustomView = setting("CustomView",range(0,20))
    views = odict([("All","AllView"),("Custom","CustomView")])
    view = setting("view","All")
    attributes = "Nrunning",
    refresh_period = 10.0 # s

    def __init__(self,parent=None,title="IOCs & Servers"):
        wx.Frame.__init__(self,parent=parent,title=title)
        from Icon import SetIcon
        SetIcon(self,"Server")

        # Controls
        self.panel = wx.Panel(self)
        self.controls = []

        # Menus
        menuBar = wx.MenuBar()

        self.ViewMenu = wx.Menu()
        for i in range(0,len(self.views)):
            self.ViewMenu.AppendCheckItem(10+i,self.views.keys()[i])
        self.ViewMenu.AppendSeparator()
        menuBar.Append (self.ViewMenu,"&View")

        self.SetupMenu = wx.Menu()
        self.SetupMenu.AppendCheckItem(200,"Setup")
        self.SetupMenu.AppendSeparator()
        self.SetupMenu.Append(201,"Add Line")
        self.SetupMenu.Append(202,"Remove Line")
        menuBar.Append(self.SetupMenu,"&More")

        menu = wx.Menu()
        menu.Append(wx.ID_ABOUT,"About...")
        menuBar.Append(menu,"&Help")

        self.SetMenuBar(menuBar)

        # Callbacks
        self.Bind(wx.EVT_MENU_OPEN,self.OnOpenView)
        for i in range(0,len(self.views)):
            self.Bind(wx.EVT_MENU,self.OnSelectView,id=10+i)
        self.Bind(wx.EVT_MENU,self.OnSetup,id=200)
        self.Bind(wx.EVT_MENU,self.OnAdd,id=201)
        self.Bind(wx.EVT_MENU,self.OnRemove,id=202)
        self.Bind(wx.EVT_MENU,self.OnAbout,id=wx.ID_ABOUT)
        self.Bind(wx.EVT_CLOSE,self.OnClose)

        # Layout
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.sizer)
        self.update_controls()
        self.Show()

        # Refresh
        from numpy import nan
        self.values = {}
        self.old_values = {}

        self.Bind(wx.EVT_TIMER,self.OnUpdate)
        from threading import Thread
        self.thread = Thread(target=self.keep_updated,name=self.name)
        self.thread.daemon = True
        self.thread.start()

    def keep_updated(self):
        """Periodically refresh the displayed settings."""
        from time import time,sleep
        while True:
            try:
                t0 = time()
                while time() < t0+self.refresh_period: sleep(0.5)
                if self.Shown:
                    self.update_data()
                    if self.data_changed:
                        event = wx.PyCommandEvent(wx.EVT_TIMER.typeId,self.Id)
                        # call OnUpdate in GUI thread
                        wx.PostEvent(self.EventHandler,event)
            except wx.PyDeadObjectError: break

    def refresh(self):
        """Force update"""
        from threading import Thread
        self.thread = Thread(target=self.refresh_background,name=self.name+".refresh")
        self.thread.daemon = True
        self.thread.start()

    def refresh_background(self):
        """Force update"""
        self.update_data()
        if self.data_changed:
            event = wx.PyCommandEvent(wx.EVT_TIMER.typeId,self.Id)
            wx.PostEvent(self.EventHandler,event) # call OnUpdate in GUI thread

    def update_data(self):
        """Retreive status information"""
        self.old_values = dict(self.values) # make a copy
        for n in self.attributes:
            try: self.values[n] = getattr(servers,n)
            except Exception,msg: error("%s\n%s" % (msg,traceback.format_exc()))

    @property
    def data_changed(self):
        """Did the last 'update_data' change the data to be plotted?"""
        changed = (self.values != self.old_values)
        return changed

    def OnUpdate(self,event):
        """Periodically refresh the displayed settings."""
        self.refresh_status()

    def refresh_status(self,event=None):
        """Update title to show whether all checks passed"""
        if "Nrunning" in self.values:
            text = "%r of %r running locally" % (self.values["Nrunning"],servers.N)
            self.Title = self.Title.split(":")[0]+": %s" % text

    def update_controls(self):
        if len(self.controls) != servers.N:
            for control in self.controls: control.Destroy()
            ##self.sizer.DeleteWindows() # not compatible with wx 4.0
            self.controls = []
            for i in range(servers.N):
                self.controls += [ServerControl(self.panel,i)]
            for i in range(0,len(self.controls)):
                self.sizer.Add(self.controls[i],flag=wx.ALL|wx.EXPAND,proportion=1)
            setup = self.SetupMenu.IsChecked(200)
            for control in self.controls: control.setup = setup
            self.panel.Sizer.Fit(self)

        if not self.view in self.views: self.view = self.views.keys()[0]
        self.View = getattr(self,self.views[self.view])

    def get_View(self):
        """Which control to show? List of 0-based integers"""
        view = [i for (i,c) in enumerate(self.controls) if c.Shown]
        return view
    def set_View(self,value):
        currently_shown = [c.Shown for c in self.controls]
        shown = [False]*len(self.controls)
        for i in value:
            if i < len(shown): shown[i] = True
        if shown != currently_shown:
            for i in range(0,len(self.controls)):
                self.controls[i].Shown = shown[i]
            self.panel.Sizer.Fit(self)
    View = property(get_View,set_View)

    def OnOpenView(self,event):
        """Called if the "View" menu is selected"""
        for i in range(0,len(self.views)):
            self.ViewMenu.Check(10+i,self.views.keys()[i] == self.view)
        for i in range(0,len(self.controls)):
            try: self.ViewMenu.Remove(100+i)
            except Exception,msg: warn("ViewMenu.Remove(%d): %s" % (100+i,msg))
            title = self.controls[i].Title
            if title == "": title = "Untitled %d" % (i+1)
            ID = 100+i
            self.ViewMenu.AppendCheckItem(ID,title)
            self.ViewMenu.Check(ID,self.controls[i].Shown)
            self.ViewMenu.Enable(ID,self.view != "All")
            self.Bind(wx.EVT_MENU,self.OnView,id=100+i)

    def OnSelectView(self,event):
        """Called if the view is toogled between 'All' and 'Custome'
        from the 'View ' menu."""
        n =  event.Id-10
        self.view = self.views.keys()[n]
        self.View = getattr(self,self.views.values()[n])

    def OnView(self,event):
        """Called if one of the items of the "View" menu is checked or
        unchecked."""
        n =  event.Id-100
        self.controls[n].Shown = event.IsChecked()
        self.panel.Sizer.Fit(self)
        setattr(self,self.views[self.view],self.View) # save modified view

    def OnSetup(self,event):
        """Enable 'setup' mode, allowing the panel to be configured"""
        setup = self.SetupMenu.IsChecked(200)
        for control in self.controls: control.setup = setup
        self.panel.Sizer.Fit(self)

    def OnAdd(self,event):
        servers.N += 1
        self.update_controls()

    def OnRemove(self,event):
        if servers.N > 0: servers.N -= 1
        self.update_controls()

    def OnAbout(self,event):
        """Show panel with additional parameters"""
        from os.path import basename
        from inspect import getfile
        from os.path import getmtime
        from datetime import datetime
        filename = getfile(lambda x: None)
        info = basename(filename)+" "+__version__
        import servers as module
        filename = getfile(module)
        if hasattr(module,"__source_timestamp__"):
            timestamp = module.__source_timestamp__
            filename = filename.replace(".pyc",".py")
        else: timestamp = getmtime(getfile(module))
        info += "\n"+basename(filename)+" "+module.__version__
        info += " ("+str(datetime.fromtimestamp(timestamp))+")"
        info += "\nwx "+wx.__version__
        info += "\n\n"+__doc__
        dlg = wx.MessageDialog(self,info,"About",wx.OK|wx.ICON_INFORMATION)
        dlg.CenterOnParent()
        dlg.ShowModal()
        dlg.Destroy()

    def OnClose(self,event):
        """Called when the windows's close button is clicked"""
        self.Destroy()

class ServerControl(wx.Panel):
    name = "ServersControl"
    attributes = "label","running","OK","test_code_OK","formatted_value",
    refresh_period = 1.0

    def __init__(self,parent,n,shown=False):
        self.values = {
            "label":"",
            "running":False,
            "formatted_value":"",
            "OK":True,
            "test_code_OK":False
        }
        self.old_values = {}

        wx.Panel.__init__(self,parent)
        self.Shown = shown
        self.Title = "Test %d" % n
        self.n = n
        self.myEnabled = wx.CheckBox(self,size=(470,-1))
        from wx.lib.buttons import GenButton
        self.State = GenButton(self,size=(25,20))
        self.Setup = wx.Button(self,size=(60,-1),label="More...")
        self.Setup.Shown = False
        self.Log = wx.Button(self,size=(50,-1),label="Log...")

        self.Bind(wx.EVT_CHECKBOX,self.OnEnable,self.myEnabled)
        self.Bind(wx.EVT_BUTTON,self.OnState,self.State)
        self.Bind(wx.EVT_BUTTON,self.OnSetup,self.Setup)
        self.Bind(wx.EVT_BUTTON,self.OnLog,self.Log)

        # Layout
        self.layout = wx.BoxSizer(wx.HORIZONTAL)
        flag = wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.EXPAND
        self.layout.Add(self.myEnabled,flag=flag,proportion=1)
        self.layout.Add(self.State,flag=flag)
        self.layout.Add(self.Setup,flag=flag)
        self.layout.Add(self.Log,flag=flag)

        # Leave a 10 pixel wide border.
        self.box = wx.BoxSizer(wx.VERTICAL)
        self.box.Add(self.layout,flag=wx.ALL,border=5)
        self.SetSizer(self.box)
        self.Fit()

        self.refresh_label()

        # Periodically refresh the displayed settings.
        self.Bind(wx.EVT_TIMER,self.OnUpdate)
        from threading import Thread
        self.thread = Thread(target=self.keep_updated,name=self.name)
        self.thread.daemon = True
        self.thread.start()

    @property
    def server(self): return servers[self.n]

    def keep_updated(self):
        """Periodically refresh the displayed settings."""
        from time import time,sleep
        while True:
            try:
                t0 = time()
                if self.Shown:
                    ##debug("ServerControl %s: Shown: %r" % (self.n,self.Shown))
                    self.update_data()
                    if self.data_changed:
                        event = wx.PyCommandEvent(wx.EVT_TIMER.typeId,self.Id)
                        # call OnUpdate in GUI thread
                        wx.PostEvent(self.EventHandler,event)
                while time() < t0+self.refresh_period: sleep(0.5)
            except wx.PyDeadObjectError: break

    def OnUpdate(self,event):
        """Periodically refresh the displayed settings."""
        self.refresh_status()

    def refresh(self):
        """Force update"""
        from threading import Thread
        self.thread = Thread(target=self.refresh_background,
            name=self.name+".refresh")
        self.thread.daemon = True
        self.thread.start()

    def refresh_background(self):
        """Force update"""
        self.update_data()
        if self.data_changed:
            event = wx.PyCommandEvent(wx.EVT_TIMER.typeId,self.Id)
            wx.PostEvent(self.EventHandler,event) # call OnUpdate in GUI thread

    def update_data(self):
        """Retreive status information"""
        self.old_values = dict(self.values) # make a copy
        for n in self.attributes:
            try: self.values[n] = getattr(self.server,n)
            except Exception,msg: error("%s\n%s" % (msg,traceback.format_exc()))

    @property
    def data_changed(self):
        """Did the last 'update_data' change the data to be plotted?"""
        changed = (self.values != self.old_values)
        return changed

    def refresh_label(self,event=None):
        """Update the controls with current values"""
        self.Title = self.server.label
        self.myEnabled.Value = self.server.enabled
        self.myEnabled.Label = self.server.label

    def refresh_status(self,event=None):
        """Update the controls with current values"""
        label = self.values["label"]
        running = self.values["running"]

        self.Title = label
        self.myEnabled.Value = running

        red = (255,0,0)
        green = (0,255,0)
        gray = (180,180,180)

        self.myEnabled.Label = "%s: %s" % (label,self.values["formatted_value"])
        color = green if self.values["OK"] else red
        if not self.values["test_code_OK"]: color = gray
        self.State.BackgroundColour = color
        self.State.ForegroundColour = color
        self.State.Refresh() # work-around for a GenButton bug in Windows

    def OnEnable(self,event):
        value = event.IsChecked()
        try: self.server.running = value
        except Exception,msg: error("%r\n%r" % (msg,traceback.format_exc()))
        self.refresh()

    def get_setup(self):
        """'Setup' mode enabled? (Allows reconfiguring parameters)"""
        value = self.Setup.Shown
        return value
    def set_setup(self,value):
        self.Setup.Shown = value
        self.Layout()
        self.Fit()
    setup = property(get_setup,set_setup)

    def OnState(self,event):
        """Start/Stop server"""
        try: self.server.running = not self.server.running
        except Exception,msg: error("%r\n%r" % (msg,traceback.format_exc()))
        self.refresh()

    def OnSetup(self,event):
        """Bring up configuration panel"""
        dlg = SetupPanel(self,self.n)
        dlg.CenterOnParent()
        dlg.Show()

    def OnLog(self,event):
        """Bring up configuration panel"""
        dlg = LogPanel(self,self.n)
        dlg.CenterOnParent()
        dlg.Show()

class SetupPanel(wx.Frame):
    def __init__(self,parent,n):
        self.n = n
        wx.Frame.__init__(self,parent=parent,title="Setup")
        from Icon import SetIcon
        SetIcon(self,"Server")
        self.panel = wx.Panel(self)

        # Controls
        style = wx.TE_PROCESS_ENTER
        self.myLabel         = TextCtrl(self.panel,size=(320,-1),style=style)
        self.Command         = TextCtrl(self.panel,size=(320,-1),style=style)
        self.LogfileBasename = TextCtrl(self.panel,size=(320,-1),style=style)
        self.Value           = TextCtrl(self.panel,size=(320,-1),style=style)
        self.Format          = TextCtrl(self.panel,size=(320,-1),style=style)
        self.Test            = TextCtrl(self.panel,size=(320,-1),style=style)

        # Callbacks
        self.Bind(wx.EVT_TEXT_ENTER,self.OnLabel,self.myLabel)
        self.Bind(wx.EVT_TEXT_ENTER,self.OnCommand,self.Command)
        self.Bind(wx.EVT_TEXT_ENTER,self.OnLogfileBasename,self.LogfileBasename)
        self.Bind(wx.EVT_TEXT_ENTER,self.OnValue,self.Value)
        self.Bind(wx.EVT_TEXT_ENTER,self.OnFormat,self.Format)
        self.Bind(wx.EVT_TEXT_ENTER,self.OnTest,self.Test)
        self.Bind(wx.EVT_SIZE,self.OnResize)

        # Layout
        self.layout = wx.BoxSizer()
        grid = wx.FlexGridSizer(cols=2,hgap=5,vgap=5)
        flag = wx.ALIGN_CENTER_VERTICAL|wx.ALL|wx.EXPAND

        label = "Name:"
        grid.Add(wx.StaticText(self.panel,label=label),flag=flag)
        grid.Add(self.myLabel,flag=flag,proportion=1)
        label = "Command:"
        grid.Add(wx.StaticText(self.panel,label=label),flag=flag)
        grid.Add(self.Command,flag=flag,proportion=1)
        label = "Logfile basename:"
        grid.Add(wx.StaticText(self.panel,label=label),flag=flag)
        grid.Add(self.LogfileBasename,flag=flag,proportion=1)
        label = "Value:"
        grid.Add(wx.StaticText(self.panel,label=label),flag=flag)
        grid.Add(self.Value,flag=flag,proportion=1)
        label = "Format:"
        grid.Add(wx.StaticText(self.panel,label=label),flag=flag)
        grid.Add(self.Format,flag=flag,proportion=1)
        label = "Test:"
        grid.Add(wx.StaticText(self.panel,label=label),flag=flag)
        grid.Add(self.Test,flag=flag,proportion=1)
        # Leave a 10-pixel wide space around the panel.
        self.layout.Add(grid,flag=wx.EXPAND|wx.ALL,proportion=1,border=10)

        self.panel.SetSizer(self.layout)
        self.panel.Fit()
        self.Fit()

        # Intialization
        self.refresh()

    @property
    def server(self): return servers[self.n]

    def refresh(self,Event=0):
        self.myLabel.Value = self.server.label
        self.Command.Value = self.server.command
        self.LogfileBasename.Value = self.server.logfile_basename
        self.Value.Value = self.server.value_code
        self.Format.Value = self.server.format_code
        self.Test.Value = self.server.test_code

    def OnLabel(self,event):
        self.server.label = self.myLabel.Value
        self.refresh()

    def OnCommand(self,event):
        self.server.command = self.Command.Value
        self.refresh()

    def OnLogfileBasename(self,event):
        self.server.logfile_basename = self.LogfileBasename.Value
        self.refresh()

    def OnValue(self,event):
        self.server.value_code = self.Value.Value
        self.refresh()

    def OnFormat(self,event):
        self.server.format_code = self.Format.Value
        self.refresh()

    def OnTest(self,event):
        self.server.test_code = self.Test.Value
        self.refresh()

    def OnResize(self,event):
        """Rearange contents to fit best into new size"""
        self.panel.Fit()
        event.Skip()

class LogPanel(wx.Frame):
    name = "LogPanel"
    attributes = "log","label"
    refresh_period = 1.0
    levels = ["DEBUG","INFO","WARNING","ERROR"]
    from persistent_property import persistent_property
    level = persistent_property("level","DEBUG")

    def __init__(self,parent,n):
        self.n = n
        wx.Frame.__init__(self,parent=parent,title="Log",size=(640,240))
        from Icon import SetIcon
        SetIcon(self,"Server")
        self.panel = wx.Panel(self)

        # Controls
        from EditableControls import TextCtrl,ComboBox
        style = wx.TE_PROCESS_ENTER|wx.TE_MULTILINE|wx.TE_DONTWRAP
        self.Log = TextCtrl(self.panel,size=(-1,-1),style=style)
        self.Log.Font = wx.Font(pointSize=10,family=wx.TELETYPE,style=wx.NORMAL,
            weight=wx.NORMAL)
        self.Clear = wx.Button(self.panel,size=(-1,-1),label="Clear Log")
        self.Level = ComboBox(self.panel,size=(-1,-1),choices=self.levels)

        # Callbacks
        self.Bind(wx.EVT_TEXT_ENTER,self.OnLog,self.Log)
        self.Bind(wx.EVT_BUTTON,self.OnClear,self.Clear)
        self.Bind(wx.EVT_COMBOBOX,self.OnLevel,self.Level)
        self.Bind(wx.EVT_TEXT_ENTER,self.OnLevel,self.Level)

        # Layout
        self.layout = wx.BoxSizer(wx.VERTICAL)
        self.layout.Add(self.Log,flag=wx.ALL|wx.EXPAND,proportion=1,border=2)
        self.controls = wx.BoxSizer(wx.HORIZONTAL)
        self.layout.Add(self.controls,flag=wx.ALL|wx.EXPAND,proportion=0,border=2)
        self.controls.Add(self.Clear,flag=wx.ALL|wx.EXPAND,proportion=0,border=2)
        self.controls.Add(self.Level,flag=wx.ALL|wx.EXPAND,proportion=0,border=2)
        self.panel.SetSizer(self.layout)
        self.Layout()

        # Periodically refresh the displayed settings.
        self.values = {}
        self.Bind(wx.EVT_TIMER,self.OnUpdate)
        from threading import Thread
        self.thread = Thread(target=self.keep_updated,name=self.name)
        self.thread.daemon = True
        self.thread.start()

    def keep_updated(self):
        """Periodically refresh the displayed settings."""
        from time import time,sleep
        while True:
            try:
                t0 = time()
                if self.Shown:
                    self.update_data()
                    if self.data_changed:
                        event = wx.PyCommandEvent(wx.EVT_TIMER.typeId,self.Id)
                        # call OnUpdate in GUI thread
                        wx.PostEvent(self.EventHandler,event)
                while time() < t0+self.refresh_period: sleep(0.5)
            except wx.PyDeadObjectError: break

    def OnUpdate(self,event):
        """Periodically refresh the displayed settings."""
        self.refresh_status()

    def refresh(self):
        """Force update"""
        from threading import Thread
        self.thread = Thread(target=self.refresh_background,
            name=self.name+".refresh")
        self.thread.daemon = True
        self.thread.start()

    def refresh_background(self):
        """Force update"""
        self.update_data()
        if self.data_changed:
            event = wx.PyCommandEvent(wx.EVT_TIMER.typeId,self.Id)
            wx.PostEvent(self.EventHandler,event) # call OnUpdate in GUI thread

    def update_data(self):
        """Retreive status information"""
        self.old_values = dict(self.values) # make a copy
        for n in self.attributes:
            try: self.values[n] = getattr(self.server,n)
            except Exception,msg: error("%s\n%s" % (msg,traceback.format_exc()))

    @property
    def data_changed(self):
        """Did the last 'update_data' change the data to be plotted?"""
        changed = (self.values != self.old_values)
        return changed

    @property
    def server(self): return servers[self.n]

    def refresh_status(self):
        if "label" in self.values:
            self.Title = "Log: "+self.values["label"]
        if "log" in self.values:
            text = self.values["log"]
            text = self.filter(text)
            text = last_lines(text)
            self.Log.Value = text
            # Scroll to the end
            self.Log.ShowPosition(self.Log.LastPosition)
        self.Level.StringSelection = self.level

    def OnLog(self,event):
        self.server.log = self.Log.Value
        self.refresh()

    def OnClear(self,event):
        self.server.log = ""
        self.refresh()

    def OnLevel(self,event):
        self.level = self.Level.StringSelection
        self.refresh_status()

    def filter(self,text):
        words_to_filter = []
        if self.level in self.levels:
            i = self.levels.index(self.level)
            words_to_filter = self.levels[0:i]
        debug("level: %r, filtering %r" % (self.level,words_to_filter))
        if words_to_filter:
            lines = text.splitlines()
            for word in words_to_filter:
                lines = [line for line in lines if not word in line]
            text = "\n".join(lines)+"\n"
        return text

    
def last_lines(text,max_line_count=1000):
    line_count = text.count("\n")
    if line_count > max_line_count:
        text = text[-160*max_line_count:]
        lines = text.splitlines()
        lines = lines[-max_line_count-2:][1:]
        text = "\n".join(lines)+"\n"
    debug("Reduced line count from from %r to %r" % (line_count,text.count("\n")))
    return text


if __name__ == '__main__':
    from pdb import pm
    import autoreload
    import logging
    from tempfile import gettempdir
    logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s",
        filename=gettempdir()+"/ServersPanel.log")
    # Needed to initialize WX library
    if not "app" in globals(): app = wx.App(redirect=False)
    window = ServersPanel()
    app.MainLoop()
