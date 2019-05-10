#!/usr/bin/env python
"""Controls when data collection is suspended, in case the X-ray beam is
down
    
Friedrich Schotte,
Date created: 2017-02-24
Date last modified: 2018-03-15
"""
__version__ = "1.2.9" # logging
from checklist import checklist
import wx, wx3_compatibility
from EditableControls import TextCtrl,ComboBox
from logging import debug,info,warn,error

class ChecklistPanel(wx.Frame):
    name = "ChecklistPanel"
    from persistent_property import persistent_property
    from collections import OrderedDict as odict
    AllView = range(0,20)
    CustomView = persistent_property("CustomView",range(0,20))
    views = odict([("All","AllView"),("Custom","CustomView")])
    view = persistent_property("view","All")
    attributes = ["OK"]
    refresh_period = 1.0 # s

    def __init__(self,parent=None,title="Suspend Checklist"):
        wx.Frame.__init__(self,parent=parent,title=title)
        from Icon import SetIcon
        SetIcon(self,"Checklist")

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

        menu = wx.Menu()
        menu.AppendCheckItem(200,"Setup")
        menu.AppendSeparator()
        menu.Append(201,"Add Line")
        menu.Append(202,"Remove Line")
        menuBar.Append(menu,"&More")

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
        self.values = {"OK": nan}
        self.old_values = {}

        self.Bind(wx.EVT_TIMER,self.OnUpdate)
        from threading import Thread
        self.thread = Thread(target=self.keep_updated,name=self.name)
        self.thread.start()

    def keep_updated(self):
        """Periodically refresh the displayed settings."""
        from time import time,sleep
        while True:
            try:
                t0 = time()
                while time() < t0+self.refresh_period: sleep(0.1)
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
        for n in self.attributes: self.values[n] = getattr(checklist,n)

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
        from numpy import isnan
        OK = self.values["OK"]
        status = "?" if isnan(OK) else "OK" if  OK else "not OK"
        self.Title = self.Title.split(":")[0]+": %s" % status

    def update_controls(self):
        if len(self.controls) != checklist.N:
            for control in self.controls: control.Destroy()
            ##self.sizer.DeleteWindows() # not compatible with wx 4.0
            self.controls = []
            for i in range(checklist.N):
                self.controls += [ChecklistControl(self.panel,i)]
            for i in range(0,len(self.controls)):
                self.sizer.Add(self.controls[i],flag=wx.ALL|wx.EXPAND,proportion=1)
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
            except: pass
            self.ViewMenu.AppendCheckItem(100+i,self.controls[i].Title)
            self.ViewMenu.Check(100+i,self.controls[i].Shown)
            self.ViewMenu.Enable(100+i,self.view != "All")
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
        self.controls[n].Shown = event.Checked()
        self.panel.Sizer.Fit(self)
        setattr(self,self.views[self.view],self.View) # save modified view

    def OnSetup(self,event):
        """Enable 'setup' mode, allowing the panel to be configured"""
        for control in self.controls: control.setup = event.Checked()
        self.panel.Sizer.Fit(self)

    def OnAdd(self,event):
        checklist.N += 1
        self.update_controls()

    def OnRemove(self,event):
        if checklist.N > 0: checklist.N -= 1
        self.update_controls()

    def OnAbout(self,event):
        """Show panel with additional parameters"""
        from os.path import basename
        from inspect import getfile
        from os.path import getmtime
        from datetime import datetime
        filename = getfile(lambda x: None)
        info = basename(filename)+" "+__version__
        import checklist as module
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

class ChecklistControl(wx.Panel):
    name = "ChecklistControl"
    attributes = "formatted_value","OK","test_code_OK"
    refresh_period = 1.0
    def __init__(self,parent,n):
        self.values = {"formatted_value":"","OK":True,"test_code_OK":False}
        self.old_values = {}
        
        wx.Panel.__init__(self,parent)
        self.Title = "Test %d" % n
        self.n = n
        self.myEnabled = wx.CheckBox(self,size=(320,-1))
        from wx.lib.buttons import GenButton
        self.State = GenButton(self,size=(25,20))
        self.Setup = wx.Button(self,size=(60,-1),label="More...")
        self.Setup.Shown = False

        self.Bind(wx.EVT_CHECKBOX,self.OnEnable,self.myEnabled)
        self.Bind(wx.EVT_BUTTON,self.OnSetup,self.State)
        self.Bind(wx.EVT_BUTTON,self.OnSetup,self.Setup)

        # Layout
        self.layout = wx.BoxSizer(wx.HORIZONTAL)
        flag = wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.EXPAND
        self.layout.Add(self.myEnabled,flag=flag,proportion=1)
        self.layout.Add(self.State,flag=flag)
        self.layout.Add(self.Setup,flag=flag)

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
        self.thread.start()

    def keep_updated(self):
        """Periodically refresh the displayed settings."""
        from time import time,sleep
        while True:
            try:
                t0 = time()
                while time() < t0+self.refresh_period: sleep(0.1)
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
        for n in self.attributes: self.values[n] = getattr(checklist.test(self.n),n)

    @property
    def data_changed(self):
        """Did the last 'update_data' change the data to be plotted?"""
        changed = (self.values != self.old_values)
        return changed

    def OnUpdate(self,event):
        """Periodically refresh the displayed settings."""
        self.refresh_status()

    def refresh_label(self,event=None):
        """Update the controls with current values"""
        self.Title = checklist.test(self.n).label
        self.myEnabled.Value = checklist.test(self.n).enabled
        self.myEnabled.Label = checklist.test(self.n).label

    def refresh_status(self,event=None):
        """Update the controls with current values"""
        red = (255,0,0)
        green = (0,255,0)
        gray = (180,180,180)
        
        label = checklist.test(self.n).label
        self.myEnabled.Label = "%s: %s" % (label,self.values["formatted_value"])
        color = green if self.values["OK"] else red
        if not self.values["test_code_OK"]: color = gray
        self.State.BackgroundColour = color
        self.State.ForegroundColour = color
        self.State.Refresh() # work-around for a GenButton bug in Windows

    def OnEnable(self,event):
        checklist.test(self.n).enabled = event.Checked()
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

    def OnSetup(self,event):
        """"""
        dlg = SetupPanel(self,self.n)
        dlg.CenterOnParent()
        dlg.Show()

class SetupPanel(wx.Frame):
    def __init__(self,parent,n):
        self.n = n
        wx.Frame.__init__(self,parent=parent,title="Setup")
        self.panel = wx.Panel(self)

        # Controls
        style = wx.TE_PROCESS_ENTER
        self.myLabel = ComboBox(self.panel,size=(320,-1),style=style)
        self.Value = ComboBox(self.panel,size=(320,-1),style=style)
        self.Format = ComboBox(self.panel,size=(320,-1),style=style)
        self.Test = ComboBox(self.panel,size=(320,-1),style=style)

        # Callbacks
        self.Bind (wx.EVT_COMBOBOX,self.OnLabel,self.myLabel)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnLabel,self.myLabel)
        self.Bind (wx.EVT_COMBOBOX,self.OnValue,self.Value)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnValue,self.Value)
        self.Bind (wx.EVT_COMBOBOX,self.OnFormat,self.Format)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnFormat,self.Format)
        self.Bind (wx.EVT_COMBOBOX,self.OnTest,self.Test)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnTest,self.Test)
        self.Bind (wx.EVT_SIZE,self.OnResize)

        # Layout
        self.layout = wx.BoxSizer()
        grid = wx.FlexGridSizer(cols=2,hgap=5,vgap=5)
        flag = wx.ALIGN_CENTER_VERTICAL|wx.ALL|wx.EXPAND
        
        label = "Label:"
        grid.Add(wx.StaticText(self.panel,label=label),flag=flag)
        grid.Add(self.myLabel,flag=flag,proportion=1)
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
        labels,values,formats,tests = [],[],[],[]
        for label in checklist.defaults:
            labels  += [label]
            values  += [checklist.defaults[label]["value"]]
            formats += [checklist.defaults[label]["format"]]
            tests   += [checklist.defaults[label]["test"]]
        self.myLabel.Items = labels
        self.Value.Items = values
        self.Format.Items = formats
        self.Test.Items = tests

        self.refresh()

    def refresh(self,Event=0):
        self.myLabel.Value = checklist.test(self.n).label
        self.Value.Value = checklist.test(self.n).value_code
        self.Format.Value = checklist.test(self.n).format
        self.Test.Value = checklist.test(self.n).test_code

    def OnLabel(self,event):
        checklist.test(self.n).label = self.myLabel.Value
        self.refresh()

    def OnValue(self,event):
        checklist.test(self.n).value_code = self.Value.Value
        self.refresh()

    def OnFormat(self,event):
        checklist.test(self.n).format = self.Format.Value
        self.refresh()

    def OnTest(self,event):
        checklist.test(self.n).test_code = self.Test.Value
        self.refresh()

    def OnResize(self,event):
        """Rearange contents to fit best into new size"""
        self.panel.Fit()
        event.Skip()
        

if __name__ == '__main__':
    from pdb import pm
    import logging
    from tempfile import gettempdir
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s",
        filename=gettempdir()+"/ChecklistPanel.log",
    )
    import autoreload
    # Needed to initialize WX library
    app = wx.App(redirect=False)
    ChecklistPanel()
    app.MainLoop()
