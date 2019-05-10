#!/usr/bin/env python
"""Grapical User Interface 
Author: Friedrich Schotte
Date created: 2008-11-23
Date last modified: 2019-03-26
"""
__version__ = "1.10" # subpanels items may be preceeded by labels
import wx, wx3_compatibility
from EditableControls import ComboBox,TextCtrl # customized versions
from logging import debug,info,warn,error
from traceback import format_exc
from numpy import inf

class BasePanel(wx.Frame):
    """Control Panel for FPGA Timing System"""
    from persistent_property import persistent_property
    from collections import OrderedDict as odict
    CustomView = persistent_property("CustomView",[])
    views = odict([("Standard","StandardView"),("Custom","CustomView")])
    view = persistent_property("view","Standard")
    from setting import setting
    refresh_period = setting("refresh_period",1.0)
    from numpy import inf
    refresh_period_choices_all = [0.1,0.2,0.5,1.,2.,5,10.,20.,30.,60.,inf]

    @property
    def refresh_period_choices(self):
        choices = self.refresh_period_choices_all
        if not self.refresh_period in choices:
            choices = sorted(choices + [self.refresh_period])
        return choices 

    def __init__(self,parent=None,name="BasePanel",title="Base Panel",
        component=object,parameters=[],standard_view=[],subpanels=[],buttons=[],
        subname=True,layout=[],label_width=150,object=None,
        refresh=False,live=False,update=[],
        icon=None,
        *common_args,**common_kwargs):
        wx.Frame.__init__(self,parent=parent)
        
        if hasattr(parent,"Title"): title = parent.Title+" "+title
        self.Title = title
        self.name = name
        self.component = component
        self.parameters = parameters
        self.StandardView = standard_view
        self.subpanels = subpanels
        self.buttons = buttons
        self.layout = layout
        self.object = object if object is not None else self
        self.update = update

        if subname and hasattr(parent,"name"):
            self.name = parent.name+"."+self.name
        if self.CustomView == []: self.CustomView = standard_view

        # Icon
        from Icon import SetIcon
        SetIcon(self,icon)

        # Controls
        self.panel = wx.Panel(self)
        self.controls = []
        for args,kwargs in self.parameters:
            args += common_args
            kwargs.update(common_kwargs)
            if hasattr(args[0],"WindowStyle"): component = args[0]; args = args[1:]
            else: component = self.component
            if live or refresh:
                if not "refresh_period" in kwargs: kwargs["refresh_period"] = inf
            kwargs["label_width"] = label_width
            self.controls += [component(self.panel,*args,**kwargs)]
        self.components = []
        for row in self.layout:
            panel = wx.Panel(self.panel)
            panel.title = ""
            layout = wx.BoxSizer()
            self.controls += [panel]
            self.components += [[]]
            for cell in row:
                if type(cell) == str:
                    component_type,args = wx.StaticText,[]
                    kwargs = {"label":cell,"size":(label_width,-1)}
                    panel.title = cell
                else:
                    component_type,args,kwargs = cell
                    if len(args) < 2 and not "object" in kwargs and component_type is not wx.StaticText:
                        kwargs["object"] = self.object
                    if live or refresh:
                        if not "refresh_period" in kwargs and component_type != wx.StaticText:
                            kwargs["refresh_period"] = inf
                component = component_type(panel,*args,**kwargs)
                flag = wx.ALIGN_CENTRE_VERTICAL|wx.EXPAND 
                layout.Add(component,flag=flag)
                self.components[-1] += [component]
            panel.SetSizer(layout)
            panel.Fit()

        self.LiveCheckBox = wx.CheckBox(self.panel,label="Live")
        style = wx.BU_EXACTFIT
        self.RefreshButton = wx.ToggleButton(self.panel,label="Refresh",style=style)
        self.ApplyButton = wx.ToggleButton(self.panel,label="Apply",style=style)
        self.Buttons = []
        for (i,(label,panel)) in enumerate(self.buttons):
            Button = wx.Button(self.panel,label=label,style=style,id=i)
            self.Buttons += [Button]

        # Menus
        menuBar = wx.MenuBar()
        # Edit
        menu = wx.Menu()
        menu.Append(wx.ID_CUT,"Cu&t\tCtrl+X","selection to clipboard")
        menu.Append(wx.ID_COPY,"&Copy\tCtrl+C","selection to clipboard")
        menu.Append(wx.ID_PASTE,"&Paste\tCtrl+V","clipboard to selection")
        menu.Append(wx.ID_DELETE,"&Delete\tDel","clear selection")
        menu.Append(wx.ID_SELECTALL,"Select &All\tCtrl+A")
        menuBar.Append(menu,"&Edit")
        # View
        self.ViewMenu = wx.Menu()
        for i in range(0,len(self.views)):
            self.ViewMenu.AppendCheckItem(10+i,self.views.keys()[i])
        self.ViewMenu.AppendSeparator()
        for i in range(0,len(self.controls)):
            self.ViewMenu.AppendCheckItem(100+i,Title(self.controls[i]))
        menuBar.Append(self.ViewMenu,"&View")
        # Refresh
        self.RefreshMenu = wx.Menu()
        menuBar.Append(self.RefreshMenu,"&Refresh")
        # More
        if len(self.subpanels) > 0:
            menu = wx.Menu()
            for i in range(0,len(self.subpanels)):
                if hasattr(subpanels[i],"__len__"):
                    title = self.subpanels[i][0]
                else:
                    if hasattr(self.subpanels[i],"title"):
                        title = self.subpanels[i].title+"..."
                    elif hasattr(self.subpanels[i],"name"):
                        title = self.subpanels[i].name.replace("_","").title()+"..."
                    elif hasattr(self.subpanels[i],"__name__"):
                        title = self.subpanels[i].__name__.replace("_","").title()+"..."
                    else: title = "Control Panel..."
                menu.Append (200+i,title)
            menuBar.Append (menu,"&More")
        # Help
        menu = wx.Menu()
        menu.Append (wx.ID_ABOUT,"About...","Show version number")
        menuBar.Append (menu,"&Help")
        self.SetMenuBar (menuBar)

        # Callbacks
        for i in range(0,len(self.views)):
            self.Bind(wx.EVT_MENU,self.OnSelectView,id=10+i)
        for i in range(0,len(self.controls)):
            self.Bind(wx.EVT_MENU,self.OnView,id=100+i)
        self.Bind(wx.EVT_MENU_OPEN,self.OnMenuOpen)
        ##self.ViewMenu.Bind(wx.EVT_MENU_OPEN,self.OnViewMenuOpen)
        ##self.RefreshMenu.Bind(wx.EVT_MENU_OPEN,self.OnRefreshMenuOpen)
        for i in range(0,len(self.refresh_period_choices)):
            self.Bind(wx.EVT_MENU,self.OnRefreshPeriod,id=300+i)
        self.Bind(wx.EVT_MENU,self.OnRefreshPeriodOther,id=399)
        for i in range(0,len(self.subpanels)):
            self.Bind(wx.EVT_MENU,self.OnSubpanel,id=200+i)
        self.Bind(wx.EVT_MENU,self.OnAbout,id=wx.ID_ABOUT)
        self.Bind(wx.EVT_SIZE,self.OnResize)
        self.Bind(wx.EVT_CHECKBOX,self.OnLive,self.LiveCheckBox)
        self.Bind(wx.EVT_TOGGLEBUTTON,self.OnRefresh,self.RefreshButton)
        self.Bind(wx.EVT_TOGGLEBUTTON,self.OnApply,self.ApplyButton)
        for Button in self.Buttons: self.Bind(wx.EVT_BUTTON,self.OnButton,Button)

        self.Bind(wx.EVT_CLOSE,self.OnClose)

        # Layout
        layout = wx.BoxSizer(wx.VERTICAL)
        flag = wx.ALL|wx.EXPAND
        for c in self.controls: layout.Add(c,flag=flag,border=0,proportion=1)
        for c in self.controls: c.Shown = Title(c) in self.view

        # Leave a 5-pixel wide border.
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(layout,flag=flag,border=5,proportion=1)

        buttons = wx.BoxSizer(wx.HORIZONTAL)
        buttons.Add(self.LiveCheckBox,flag=wx.ALIGN_CENTER_VERTICAL)
        buttons.AddSpacer(1)
        buttons.Add(self.RefreshButton)
        buttons.AddSpacer(1)
        buttons.Add (self.ApplyButton)
        buttons.AddSpacer(2)
        for Button in self.Buttons:
            buttons.AddSpacer(1)
            buttons.Add(Button)
        box.Add (buttons,flag=wx.ALL|wx.ALIGN_CENTER_HORIZONTAL,border=5)

        self.RefreshButton.Shown = refresh
        self.LiveCheckBox.Shown = live
        self.ApplyButton.Shown = True if self.update else False
 
        self.panel.Sizer = box
        self.panel.Fit()
        self.Fit()

        # Initialization
        if not self.view in self.views: self.view = self.views.keys()[0]
        self.View = getattr(self,self.views[self.view])

        self.Show()

        # Refresh
        self.timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.OnTimer,self.timer)
        self.timer.Start(200,oneShot=True)

    def OnTimer(self,event):
        """Perform periodic updates"""
        if self.Shown:
            self.UpdateRefreshButton()
            self.timer.Start(200,oneShot=True)        

    def UpdateRefreshButton(self):
        """Update the refresh button"""
        self.RefreshButton.Value = self.refreshing

    def OnResize(self,event):
        self.panel.Fit()
        event.Skip() # call default handler

    def get_View(self):
        """Which control to show? List of strings"""
        return [Title(c) for c in self.controls if c.Shown]
    def set_View(self,value):
        for c in self.controls: c.Shown = Title(c) in value
        self.panel.Sizer.Fit(self)
    View = property(get_View,set_View)
 
    def OnMenuOpen(self,event):
        debug("Menu opened: %r" % event.EventObject)
        if event.EventObject == self.ViewMenu: self.OnViewMenuOpen(event)
        if event.EventObject == self.RefreshMenu: self.OnRefreshMenuOpen(event)

    def OnViewMenuOpen(self,event):
        """Handle "View" menu display"""
        debug("View menu opened")
        for i in range(0,len(self.views)):
            self.ViewMenu.Check(10+i,self.views.keys()[i] == self.view)
        for i in range(0,len(self.controls)):
            self.ViewMenu.Check(100+i,self.controls[i].Shown)
            self.ViewMenu.Enable(100+i,self.view != "Standard")

    def OnSelectView(self,event):
        """Called if one of the items of the "View" menu is selected"""
        n =  event.Id-10
        self.view = self.views.keys()[n]
        self.View = getattr(self,self.views.values()[n])

    def OnView(self,event):
        """Called if one of the items of the "View" menu is selected"""
        n =  event.Id-100
        self.controls[n].Shown = not self.controls[n].Shown
        self.panel.Sizer.Fit(self)
        view = [Title(c) for c in self.controls if c.Shown]
        setattr(self,self.views[self.view],view)

    def OnRefreshMenuOpen(self,event):
        """Handle "Refresh" menu display"""
        debug("Refresh menu opened")
        menu = self.RefreshMenu
        for item in menu.MenuItems: menu.RemoveItem(item)

        from time_string import time_string
        for i,choice in enumerate(self.refresh_period_choices):
            label = time_string(choice)
            menu.AppendCheckItem(300+i,label)
        menu.AppendSeparator()
        menu.Append(399,"Other...")

        def same(x,y):
            from numpy import isinf
            return (x == y) or (isinf(x) and isinf(y))

        for i,choice in enumerate(self.refresh_period_choices):
            checked = same(choice,self.refresh_period)
            menu.Check(300+i,checked)

    def OnRefreshPeriod(self,event):
        """Called if one of the items of the "Refresh" menu is selected"""
        debug("Refresh ID=%r selected" % event.Id)
        n = event.Id-300
        if n in range(0,len(self.refresh_period_choices)):
            self.refresh_period = self.refresh_period_choices[n]
            debug("refresh_period %r" % self.refresh_period)

    def OnRefreshPeriodOther(self,event):
        panel = RefreshPeriodPanel(self)
        panel.CenterOnParent()

    def OnSubpanel(self,event):
        n = event.Id-200
        if 0 <= n < len(self.subpanels):
            if hasattr(self.subpanels[n],"__len__"):
                PanelType = self.subpanels[n][1]
            else: PanelType = self.subpanels[n]
            ##panel = PanelType(self)
            ##panel.CenterOnParent()
            from start import start,modulename
            start(modulename(PanelType),PanelType.__name__+"()")

    def OnAbout(self,event):
        """Show panel with additional parameters"""
        from os.path import basename
        from inspect import getfile,getmodule
        from os.path import getmtime
        from datetime import datetime
        filename = getfile(type(self))
        info = basename(filename)+" "+getmodule(type(self)).__version__
        info += "\n\n"+getmodule(type(self)).__doc__
        dlg = wx.MessageDialog(self,info,"About",wx.OK|wx.ICON_INFORMATION)
        dlg.CenterOnParent()
        dlg.ShowModal()
        dlg.Destroy()

    def OnRefresh(self,event):
        """Handle 'Refresh' button"""
        self.refresh()

    def OnLive(self,event):
        """Called when the 'Live' checkbox is either checked or unchecked."""
        ##self.RefreshButton.Enabled = not self.LiveCheckBox.Value
        if self.LiveCheckBox.Value == True: self.keep_alive()

    def OnApply(self,event):
        """Handle 'Apply' button."""
        #for proc in self.update: proc()
        self.apply()

    def OnButton(self,event):
        ##debug("Button %r pressed" % event.Id)
        n = event.Id
        if 0 <= n < len(self.buttons):
            PanelType = self.buttons[n][1]
            ##panel = PanelType(self)
            ##panel.CenterOnParent()
            from start import start,modulename
            start(modulename(PanelType),PanelType.__name__+"()")

    def apply(self):
        """Handle 'Apply' button."""
        if not hasattr(self,"applying"): self.applying = False
        if not self.applying:
            from wx.lib.newevent import NewEvent
            self.ApplyEvent = NewEvent()[1]
            self.Bind(self.ApplyEvent,self.UpdateApplyButton)
            from threading import Thread
            self.apply_thread = Thread(target=self.apply_background,
                name=self.name+".apply")
            self.apply_thread.daemon = True
            self.applying = True
            self.apply_thread.start()

    def apply_background(self):
        """Handle 'Apply' button."""
        try:
            for proc in self.update:
                try: proc()
                except Exception,msg:
                    error("Apply: %s\n%s" % (msg,format_exc()))
            self.applying = False
            # Refresh GUI. May be called from non-GUI thread"""
            event = wx.PyCommandEvent(self.ApplyEvent.typeId,self.Id)
            wx.PostEvent(self.EventHandler,event) # call UpdateApplyButton in GUI thread
        except wx.PyDeadObjectError: pass

    def UpdateApplyButton(self,event):
        """Handle 'Apply' button."""
        self.ApplyButton.Value = self.applying

    def refresh(self):
        """Updates the controls with current values"""
        for control in self.all_controls:
            if control.Shown and hasattr(control,"refresh"): control.refresh()

    @property
    def refreshing(self):
        """Is any of the controls still in the process of refreshing after a
        call of 'refresh'?"""
        refreshing = all([c.Shown and getattr(c,"refreshing",False) for c in
            self.all_controls])
        return refreshing

    @property
    def all_controls(self):
        """All controls as list of objects"""
        controls = []
        controls += self.controls
        for row in self.components: controls += [comp for comp in row]
        return controls
 
    def keep_alive(self,event=None):
        """Periodically refresh the displayed settings (every second)."""
        if self.Shown:
            if self.LiveCheckBox.Value == True: 
                self.RefreshButton.Value = True
                self.refresh()
                self.keep_alive_timer = wx.Timer(self)
                self.Bind(wx.EVT_TIMER,self.keep_alive,self.keep_alive_timer)
                self.keep_alive_timer.Start(int(self.refresh_period*1000),oneShot=True)

    def OnClose(self,event):
        """Called when the windows's close button is clicked"""
        self.Show(False)
        ##for control in self.all_controls: control.Destroy()
        ##self.Destroy() # might crash under Windows
        wx.CallLater(1000,self.Destroy)


class PropertyPanel(wx.Panel):
    """A component for 'BasePanel'"""
    
    def __init__(self,parent=None,title="",object=None,name="",type="",choices=[],format="",
        read_only=False,digits=None,refresh_period=1.0,width=120,unit="",label_width=180):
        """title: descriptive label
        name: property name of object
        """
        wx.Panel.__init__(self,parent)
        self.title = title
        self.object = object
        self.name = name
        self.choices = choices
        self.type = type
        self.format = format
        self.unit = unit
        self.read_only = read_only
        if digits is not None: self.format = "%%.%df" % digits
        self.refresh_period = refresh_period

        self.changing = False

        # Controls
        style = wx.TE_PROCESS_ENTER
        if not self.read_only: 
            self.Current = ComboBox(self,size=(width,-1),style=style)
        else: self.Current = wx.TextCtrl(self,size=(width,-1),style=wx.TE_READONLY)
        # Callbacks
        self.Bind(wx.EVT_TEXT_ENTER,self.OnChange,self.Current)
        self.Bind(wx.EVT_COMBOBOX,self.OnChange,self.Current)
        # Layout
        layout = wx.BoxSizer()
        av = wx.ALIGN_CENTRE_VERTICAL
        e = wx.EXPAND
        if self.title:
            label = wx.StaticText(self,label=self.title+":",size=(label_width,-1))
            layout.Add(label,flag=av)
        layout.Add(self.Current,flag=av|e,proportion=1)
        self.SetSizer(layout)
        self.Fit()

        # Refresh
        self.attributes = [self.name]
        from numpy import nan
        self.values = {} ##dict([(n,nan) for n in self.attributes])
        self.old_values = {}
        
        from threading import Thread
        self.refresh_thread = Thread(target=self.refresh_background,
            name=self.name+".refresh")
        self.refresh_thread.daemon = True
        self.refreshing = False

        from wx.lib.newevent import NewEvent
        self.EVT_THREAD = NewEvent()[1]
        self.Bind(self.EVT_THREAD,self.OnUpdate)
        self.thread = Thread(target=self.keep_updated,name=self.name)
        self.thread.daemon = True
        self.thread.start()

    def keep_updated(self):
        """Periodically refresh the displayed settings."""
        from time import time,sleep
        try:
            while True:
                t0 = time()
                while time() < t0+self.refresh_period: sleep(0.1)
                if self.Shown:
                    self.update_data()
                    if self.data_changed: self.force_refresh()
        except wx.PyDeadObjectError: pass

    def refresh(self):
        """Force update"""
        from threading import Thread
        if not self.refreshing and self.Shown:
            self.refresh_thread = Thread(target=self.refresh_background,
                name=self.name+".refresh")
            self.refresh_thread.daemon = True
            self.refreshing = True
            self.refresh_thread.start()

    def refresh_background(self):
        """Force update"""
        try:
            self.update_data()
            if self.data_changed: self.force_refresh()
            self.refreshing = False
        except wx.PyDeadObjectError: pass

    def force_refresh(self):
        """MAke the control update. May be called from non-GUI thread"""
        event = wx.PyCommandEvent(self.EVT_THREAD.typeId,self.Id)
        wx.PostEvent(self.EventHandler,event) # call OnUpdate in GUI thread

    def update_data(self):
        """Retreive status information"""
        from numpy import nan
        self.old_values = dict(self.values) # make a copy
        self.values[self.name] = self.getattr(self.object,self.name,nan)
        from time import time
        self.changed = time()

    from numpy import nan
    @staticmethod
    def getattr(object,attribute,default_value=nan):
        """Get a propoerty of an object
        attribute: e.g. 'value' or 'member.value'"""
        try: return eval("object."+attribute)
        except Exception,msg:
            error("%s.%s: %s\n%s" % (object,attribute,msg,format_exc()))
            return default_value

    @property
    def data_changed(self):
        """Did the last 'update_data' change the data to be plotted?"""
        changed = (self.values != self.old_values)
        return changed

    def OnUpdate(self,event=None):
        """Periodically refresh the displayed settings."""
        self.refresh_status()

    def refresh_status(self):
        """Update the displayed value in the indicator"""
        value = self.formatted_text(self.values[self.name]) \
            if self.name in self.values else ""
        if self.changing: value += " > "+self.formatted_text(self.new_value)

        choices = self.formatted_choices(self.choices)
        if not "" in choices: choices += [""]
        
        self.Current.Items = choices
        self.Current.Value = value
        self.Current.BackgroundColour = \
            (255,200,200) if self.changing else (255,255,255) 

    def formatted_text(self,value):
        """Value as text"""
        if isnan(value): text = ""
        elif self.type.startswith("time") or self.type.startswith("frequency"):
            from numpy import asarray,concatenate,arange,unique
            from time_string import time_string
            precision = self.type.split(".")[-1][0]
            try: precision = int(precision)
            except: precision = 3
            if self.type.startswith("time"):
                def my_format(x): return time_string(x,precision)
            else:
                def my_format(x): return to_SI_format(1./x,precision)+"Hz"
            text = my_format(value)
        elif self.type == "date":
            from time_string import date_time
            text = date_time(value)
        elif self.type == "binary":
            text = "%g (%s)"%(value,format(value,"#08b"))
        elif self.type == "boolean":
            text = "On" if value else "Off"
        elif self.type == "integer":
            text = "%d" % value
        elif self.type == "float":
            text = "%g" % value
        elif self.type == "list":
            text = ",".join([str(x) for x in value])
        elif self.type.startswith("{"): # dictionary
            try:
                map = eval(self.type)
                text = map[value]
            except: text = str(value)
        elif "/" in self.type: # list of names
            choices = self.type.split("/")
            try: text = choices[int(value)]
            except Exception,msg:
                debug("PropertyPanel.refresh: %r: type %r, value %r" %
                    (self.name,self.type,value))
                text = str(value)
        else:
            if isnan(value): text = ""
            elif type(value) == str: text = value
            elif type(value) == bool: text = "On" if value else "Off"
            elif self.format:
                try: text = self.format % value
                except Exception,msg: text = ""
            else: text = str(value) 

        if self.unit and text: text += " "+self.unit
        return text

    def formatted_choices(self,choices):
        """Choices as text"""
        if hasattr(choices,"__call__"): choices = choices()
        if self.type.startswith("time") or self.type.startswith("frequency"):
            from numpy import asarray,concatenate,arange,unique
            from time_string import time_string
            precision = self.type.split(".")[-1][0]
            try: precision = int(precision)
            except: precision = 3
            if self.type.startswith("time"):
                def my_format(x): return time_string(x,precision)
            else:
                def my_format(x): return to_SI_format(1./x,precision)+"Hz"
            choices = asarray(choices)
            if len(choices) == 0:
                choices = concatenate(([0],10**(arange(-11,1,0.25))))
            if "delay" in self.name and hasattr(self.object,"next_delay"):
                choices = unique([self.object.next_delay(t) for t in choices])
            choices = [my_format(t) for t in choices]
        elif self.type == "date": pass
        elif self.type == "binary": pass
        elif self.type == "boolean":
            choices = ["On","Off"]
        elif self.type == "integer":
            choices = ["0"]
        elif self.type.startswith("{"): # dictionary
            try:
                map = eval(self.type)
                if not choices: choices = map.values()
            except: pass
        elif "/" in self.type: # list of names
            choices = self.type.split("/")
        else:
            if len(choices) == 0 and not self.read_only:
                if hasattr(self.object,self.name+"s") \
                    and getattr(self.object,self.name+"s") is not None:
                    choices = list(getattr(self.object,self.name+"s"))

        if len(choices) == 0 and not self.read_only:
            if hasattr(self.object,self.name+"_choices") \
                and getattr(self.object,self.name+"_choices") is not None:
                choices = list(getattr(self.object,self.name+"_choices"))

        choices = [str(x) for x in choices]
        return choices

    def OnChange(self,event):
        from numpy import nan,inf # for "eval"
        text = str(self.Current.Value)
        text = text.replace(self.unit,"")
        text = text.rstrip() # ignore trailing blanks
        if self.type.startswith("time") or self.type.startswith("frequency"):
            if not self.type.startswith("frequency"):
                from time_string import seconds
                value = seconds(text)
            else: value = 1/from_SI_format(text.replace("Hz",""))
        elif self.type == "binary":
            # If both decimal and binary values are given,
            # use the value that has been modified as the nwe value.
            if "(0b" in text:
                i = text.index("(0b")
                text1,text2 = text[0:i],text[i:]
                try: value1,value2 = int(eval(text1)),int(eval(text2))
                except Exception,msg: debug("%r"%msg); return
                old_value = getattr(self.object,self.name)
                value = value1 if value1 != old_value else value2
            else:
                try: value = int(eval(text))
                except: return
        elif self.type == "boolean": value = (text == "On")
        elif self.type == "integer":
            if text == "": value = nan
            else:
                try: value = int(eval(text))
                except: return
        elif self.type == "float":
            if text == "": value = nan
            else:
                try: value = float(eval(text))
                except: return
        elif self.type.startswith("{"): # dictionary
            try:
                map = eval(self.type)
                inv_map = {v: k for k, v in map.items()}
                value = inv_map[text]
            except: return
        elif "/" in self.type: # list of choices
            choices = self.type.split("/")
            try: value = choices.index(text)
            except:
                try: value = eval(text)
                except: return
        else:
            old_value = getattr(self.object,self.name)
            if type(old_value) == str: value = text
            elif type(old_value) == bool: value = (text == "On")
            else:
              try: value = eval(text)
              except: return

        from threading import Thread
        if not self.changing:
            self.change_thread = Thread(target=self.change_background,
                args=(),name=self.name+".change")
            self.change_thread.daemon = True
            self.changing = True
            self.new_value = value
            self.change_thread.start()
        self.refresh_status()

    def change_background(self):
        """If the control has changed apply the change to the object is
        is controlling."""
        try:
            debug("Starting %r.%s = %r..." % (self.object,self.name,self.new_value))
            setattr(self.object,self.name,self.new_value)
            debug("Finished %r.%s = %r" % (self.object,self.name,self.new_value))
            self.update_data()
            debug("Updated %r.%s = %r" % (self.object,self.name,self.values[self.name]))
            self.changing = False
            self.force_refresh()      
        except wx.PyDeadObjectError: pass

class TweakPanel(wx.Panel):
    """A component for 'BasePanel'"""
    def __init__(self,parent=None,title="",object=None,name="",digits=3,
        width=90,refresh_period=1.0,label_width=180,**kwargs):
        """title: descriptive label
        name: name of a callable member function of object
        """
        wx.Panel.__init__(self,parent)
        self.title = title
        self.object = object
        self.name = name
        self.digits = digits
        self.refresh_period = refresh_period

        # Standardize vertical size of controls
        test = wx.ComboBox(self)
        w,h = test.Size 
        test.Destroy()

        # Controls
        style = wx.TE_PROCESS_ENTER
        self.Control = TextCtrl(self,size=(width,h),style=style)
        self.TweakControl = wx.SpinButton(self,size=(-1,h))
        self.TweakControl.SetRange(-100000,100000)
        # Callbacks
        self.Bind(wx.EVT_TEXT_ENTER,self.OnChange,self.Control)
        self.Bind(wx.EVT_SPIN_DOWN,self.OnTweakDown,self.TweakControl)
        self.Bind(wx.EVT_SPIN_UP,self.OnTweakUp,self.TweakControl)
        # Layout
        layout = wx.BoxSizer()
        av = wx.ALIGN_CENTRE_VERTICAL
        e = wx.EXPAND
        if self.title:
            label = wx.StaticText(self,label=self.title+":",size=(label_width,-1))
            layout.Add(label,flag=av)
        layout.Add(self.Control,flag=av|e,proportion=1)
        layout.Add(self.TweakControl,flag=av|e)
        self.SetSizer(layout)
        self.Fit()

        # Refresh
        self.refreshing = False
        from threading import Thread
        from wx.lib.newevent import NewEvent
        self.EVT_THREAD = NewEvent()[1]
        self.Bind(self.EVT_THREAD,self.OnUpdate)
        thread = Thread(target=self.keep_updated,name=self.name+".keep_updated")
        thread.daemon = True
        thread.start()

    def keep_updated(self):
        """Periodically refresh the displayed settings."""
        from time import time,sleep
        while True:
            try:
                t0 = time()
                while time() < t0+self.refresh_period: sleep(0.1)
                if self.Shown:
                    self.value = getattr(self.object,self.name)
                    event = wx.PyCommandEvent(self.EVT_THREAD.typeId,self.Id)
                    wx.PostEvent(self.EventHandler,event)
            except wx.PyDeadObjectError: break

    def refresh(self):
        """Refresh the displayed settings."""
        if not self.refreshing and self.Shown:
            from threading import Thread
            thread = Thread(target=self.refresh_background,
                name=self.name+".refresh")
            thread.daemon = True
            self.refreshing = True
            thread.start()        

    def refresh_background(self):
        """Refresh the displayed settings."""
        self.value = getattr(self.object,self.name)
        event = wx.PyCommandEvent(self.EVT_THREAD.typeId,self.Id)
        wx.PostEvent(self.EventHandler,event)
        self.refreshing = False

    def update_data(self):
        """Retreive status information"""
        self.old_values = dict(self.values) # make a copy
        for n in self.attributes: self.values[n] = getattr(self.object,n)

    @property
    def data_changed(self):
        """Did the last 'update_data' change the data to be plotted?"""
        changed = (self.values != self.old_values)
        return changed

    def OnUpdate(self,event=None):
        """Refresh the displayed settings."""
        text = "%.*f" % (self.digits,self.value)
        self.Control.Value = text

    def OnChange(self,event):
        text = self.Control.Value
        try: value = eval(text)
        except Exception,msg:
            warn("TweakPanel %r: %r: %s" % (self.name,text,msg))
            self.refresh()
            return
        setattr(self.object,self.name,value)
        self.refresh()

    def OnTweakUp(self,event):
        self.Tweak(+1)

    def OnTweakDown(self,event):
        self.Tweak(-1)

    def Tweak(self,sign):
        text = str(self.Control.Value)
        cursor,end = self.Control.Selection
        if cursor == end and cursor>0: cursor -= 1
        if cursor == len(text) and len(text)>0: cursor = len(text) - 1
        if "." in text:
            n = text.find(".")-cursor-1
            if n<0: n += 1
        else: n = len(text)-cursor-1
        ##debug("Tweak %+g,%r,cur %r,end %r,digit %r" % (sign,text,cursor,end,n))
        incr = 10**n
        try: value = eval(text)
        except Exception,msg: self.refresh(); return
        value += sign*incr
        text = "%.*f" % (self.digits,value)
        if "." in text:
            if n>=0: cursor = text.find(".")-n-1
            else: cursor = text.find(".")-n
        else: cursor = len(text)-n-1
        if cursor<0: cursor = 0
        end = cursor+1
        
        ##debug("Tweak %+g,%r,cur %r,end %r,digit %r" % (sign,text,cursor,end,n))
        setattr(self.object,self.name,value)
        self.Control.SetFocus()
        self.Control.Value = text
        self.Control.SetSelection(cursor,end)


class TogglePanel(wx.Panel):
    """A component for 'BasePanel'"""
    def __init__(self,parent=None,title="",object=None,name="",type="Off/On",
        width=None,refresh_period=1.0,label="",size=None,label_width=180):
        """title: descriptive label
        name: name of a callable member function of object
        label: default label, if object.name failes
        """
        wx.Panel.__init__(self,parent)
        self.title = title
        self.object = object
        self.name = name
        self.type = type
        self.refresh_period = refresh_period
        self.label = label
        self.width = -1
        if width is not None: self.width = width 
        if size is not None: self.width = size[0] 

        # Standardize vertical size of controls
        test = wx.ComboBox(self)
        w,h = test.Size 
        test.Destroy()

        # Controls
        style = wx.TE_PROCESS_ENTER
        self.Control = wx.ToggleButton(self,size=(self.width,h),label=label)
        # Callbacks
        self.Bind(wx.EVT_TOGGLEBUTTON,self.OnChange,self.Control)
        # Layout
        layout = wx.BoxSizer()
        av = wx.ALIGN_CENTRE_VERTICAL
        e = wx.EXPAND
        if self.title:
            label = wx.StaticText(self,label=self.title+":",size=(label_width,-1))
            layout.Add(label,flag=av)
        layout.Add(self.Control,flag=av|e,proportion=1)
        self.SetSizer(layout)
        self.Fit()

        # Refresh
        self.attributes = [self.name]
        from numpy import nan
        self.values = dict([(n,nan) for n in self.attributes])
        self.old_values = {}

        self.refreshing = False
        self.changing = False

        from wx.lib.newevent import NewEvent
        self.EVT_THREAD = NewEvent()[1]
        self.Bind(self.EVT_THREAD,self.OnUpdate)
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
                while time() < t0+self.refresh_period: sleep(0.1)
                if self.Shown:
                    self.update_data()
                    if self.data_changed: 
                        event = wx.PyCommandEvent(self.EVT_THREAD.typeId,self.Id)
                        # call OnUpdate in GUI thread
                        wx.PostEvent(self.EventHandler,event)
            except wx.PyDeadObjectError: break
            
    def refresh(self):
        """Force update"""
        from threading import Thread
        if not self.refreshing and self.Shown:
            self.refresh_thread = Thread(target=self.refresh_background,
                name=self.name+".refresh")
            self.refresh_thread.daemon = True
            self.refreshing = True
            self.refresh_thread.start()

    def refresh_background(self):
        """Force update"""
        try:
            self.update_data()
            if self.data_changed: 
                event = wx.PyCommandEvent(self.EVT_THREAD.typeId,self.Id)
                wx.PostEvent(self.EventHandler,event) # call OnUpdate in GUI thread
            self.refreshing = False
        except wx.PyDeadObjectError: pass

    def update_data(self):
        """Retreive status information"""
        self.old_values = dict(self.values) # make a copy
        for n in self.attributes: self.values[n] = getattr(self.object,n)

    @property
    def data_changed(self):
        """Did the last 'update_data' change the data to be plotted?"""
        changed = (self.values != self.old_values)
        return changed

    def OnUpdate(self,event):
        """Periodically refresh the displayed settings."""
        self.refresh_status()

    def refresh_status(self):
        value = self.values[self.name]
        try:
            value = int(value)
            valid = True
        except Exception,msg:
            debug("PropertyPanel.refresh: %r: value %r" % (self.name,value))
            valid = False
        self.Control.Value = value if valid else False
        self.Control.Enabled = valid
        choices = self.type.split("/")
        if valid:
            try: text = choices[value]
            except Exception,msg:
                debug("PropertyPanel.refresh_status: %r: type %r, value %r" %
                        (self.name,self.type,value))
                text = str(value)
        else: text = self.label
        self.Control.Label = text

    def OnChange(self,event):
        from threading import Thread
        if not self.changing:
            self.change_thread = Thread(target=self.change_background,
                name=self.name+".change")
            self.change_thread.daemon = True
            self.changing = True
            self.change_thread.start()

    def change_background(self):
        """If the control has changed apply the change to the object is
        is controlling."""
        value = self.Control.Value
        setattr(self.object,self.name,value)
        self.changing = False
        self.refresh()        


class ButtonPanel(wx.Panel):
    """A component for 'BasePanel'"""
    def __init__(self,parent=None,title="",object=None,name="",label="",
        refresh_period=1.0,label_width=180):
        """title: descriptive label
        name: name of a callable member function of object
        """
        wx.Panel.__init__(self,parent)
        self.title = title
        self.object = object
        self.name = name
        self.label = label

        # Standardize vertical size of controls
        test = wx.ComboBox(self)
        w,h = test.Size 
        test.Destroy()

        # Controls
        self.Control = wx.ToggleButton(self,size=(120,h),label=self.label)
        # Callbacks
        self.Bind(wx.EVT_TOGGLEBUTTON,self.OnButton,self.Control)
        # Layout
        layout = wx.BoxSizer()
        av = wx.ALIGN_CENTRE_VERTICAL
        e = wx.EXPAND
        if self.title:
            label = wx.StaticText(self,label=self.title+":",size=(label_width,-1))
            layout.Add(label,flag=av)
        layout.Add(self.Control,flag=av|e,proportion=1)
        self.SetSizer(layout)
        self.Fit()

        # Refresh
        from wx.lib.newevent import NewEvent
        self.EVT_THREAD = NewEvent()[1]
        self.Bind(self.EVT_THREAD,self.OnUpdate)
        self.running = False

    def OnButton(self,event):
        from threading import Thread
        if self.Control.Value:
            self.thread = Thread(target=self.run_in_background,name=self.name)
            self.thread.daemon = True
            self.running = True
            self.thread.start()
        self.OnUpdate()

    def run_in_background(self):
        """Execute the procedure"""
        getattr(self.object,self.name)()
        self.running = False

        event = wx.PyCommandEvent(self.EVT_THREAD.typeId,self.Id)
        wx.PostEvent(self.EventHandler,event) # call OnUpdate in GUI thread

    def OnUpdate(self,event=None):
        """Update button state to reflect if the procedure is running"""
        self.Control.Value = self.running

    # for compatibility with other controls
    def refresh(self): pass 
    refreshing = False


class RefreshPeriodPanel(wx.Frame):
    title = "Refresh Period"
    def __init__(self,parent):
        wx.Frame.__init__(self,parent=parent,title=self.title)
        panel = wx.Panel(self)
        # Controls
        style = wx.TE_PROCESS_ENTER
        width = 160
        choices = getattr(self.Parent,"refresh_period_choices",[])
        from time_string import time_string
        choices = [time_string(choice) for choice in choices]
        self.RefreshPeriod = ComboBox(panel,style=style,choices=choices,
            size=(width,-1))
        
        # Callbacks
        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnterRefreshPeriod,self.RefreshPeriod)
        self.Bind (wx.EVT_COMBOBOX  ,self.OnEnterRefreshPeriod,self.RefreshPeriod)
        self.Bind (wx.EVT_CLOSE     ,self.OnClose)

        # Layout
        layout = wx.GridBagSizer(1,1)
        a = wx.ALIGN_CENTRE_VERTICAL
        e = wx.EXPAND

        label = wx.StaticText(panel,label="Refresh Period:")
        layout.Add (label,(0,0),flag=a)
        layout.Add (self.RefreshPeriod,(0,1),flag=a|e)

        # Leave a 5-pixel wide border.
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add (layout,flag=wx.ALL,border=5)
        panel.SetSizer(box)
        panel.Fit()
        self.Fit()

        self.Show()
        self.refresh()

    def OnEnterRefreshPeriod(self,event):
        """Called if IP address is changed"""
        from time_string import seconds
        from numpy import isnan
        value = seconds(self.RefreshPeriod.Value)
        if not isnan(value): self.Parent.refresh_period = value
        self.refresh()

    def OnRefresh(self,event=None):
        """Check whether the network connection is OK."""
        self.refresh()

    def refresh(self,event=None):
        """Update the controles and indicators with current values"""
        if self.Shown:
            from time_string import time_string
            from numpy import nan
            value = getattr(self.Parent,"refresh_period",nan)
            self.RefreshPeriod.Value = time_string(value)
            self.timer = wx.Timer(self)
            self.Bind(wx.EVT_TIMER,self.refresh,self.timer)
            self.timer.Start(1000,oneShot=True)
            
    def OnClose(self,event):
        self.Shown = False
        ##self.Destroy() # might crash under Windows
        wx.CallLater(2000,self.Destroy)


def Title(object):
    """The name of a window component"""
    if getattr(object,"Title","") != "": return object.Title
    if getattr(object,"title","") != "": return object.title
    if getattr(object,"Value","") != "": return str(object.Value)
    if getattr(object,"Label","") != "": return object.Label
    for child in getattr(object,"Children",[]):
        t = Title(child)
        if t != "": return t
    return ""

def IsInVisibleWindow(object):
    """Is object inside a visible window?"""
    # Find toplevel Frame object
    def Parent(object): return getattr(object,"Parent",None)
    def IsFrame(object): return hasattr(object,"Title")

    ##debug("IsInVisibleWindow: object=%r" % object)
    while not IsFrame(object) and Parent(object) is not None:
      object = Parent(object)
      ##debug("IsInVisibleWindow: object -> %r" % object)
    IsInVisibleWindow = getattr(object,"Shown",False)
    return IsInVisibleWindow
            
def getattr(object,attribute,default_value=None):
    """Get a propoerty of an object
    attribute: e.g. 'value' or 'member.value'"""
    if default_value is None: return eval("object."+attribute)
    try: return eval("object."+attribute)
    except: return default_value

def hasattr(object,attribute):
    """Does a property of an object exists?
    attribute: e.g. 'value' or 'member.value'"""
    try: eval("object."+attribute); return True
    except: return False

def setattr(object,attribute,value):
    """Set a propoerty of an object
    attribute: e.g. 'value' or 'member.value'"""
    from numpy import nan,inf
    command = "object.%s = %r" % (attribute,value)
    try: exec(command)
    except Exception,msg:
        error("Panel: %s: %s\n%s" % (command,msg,format_exc()))

def to_SI_format(t,precision=3):
    """Convert number to string using "p" for 1e-12, "n" for 1 e-9, etc..."""
    def format(precision,t):
        s = "%.*g" % (precision,t)
        # Add trailing zeros if needed
        if not "e" in s:
            if not "." in s and len(s) < precision:
                s += "."+"0"*(precision-len(s))
            if "." in s and len(s)-1 < precision:
                s += "0"*(precision-(len(s)-1))
        return s

    try: t=float(t)
    except: return ""
    if t != t: return "" # not a number
    if t == 0: return "0"
    if abs(t) < 0.5e-12: return "0"
    if abs(t) < 999e-12: return format(precision,t*1e+12)+" p"
    if abs(t) < 999e-09: return format(precision,t*1e+09)+" n"
    if abs(t) < 999e-06: return format(precision,t*1e+06)+" u"
    if abs(t) < 999e-03: return format(precision,t*1e+03)+" m"
    if abs(t) < 999e+00: return format(precision,t*1e+00)+" "
    if abs(t) < 999e+03: return format(precision,t*1e-03)+" k"
    if abs(t) < 999e+06: return format(precision,t*1e-06)+" M"
    if abs(t) < 999e+09: return format(precision,t*1e-09)+" G"
    return "%.*g" % (precision,t)

def from_SI_format(text):
    """Convert a text string as "1k" to the number 1000.
    SI prefixes accepted are P, E, T, G, M, k, m, u, n, p, f, a."""
    text = text.replace("P","*1e+18")
    text = text.replace("E","*1e+15")
    text = text.replace("T","*1e+12")
    text = text.replace("G","*1e+09")
    text = text.replace("M","*1e+06")
    text = text.replace("k","*1e+03")
    text = text.replace("m","*1e-03")
    text = text.replace("u","*1e-06")
    text = text.replace("n","*1e-09")
    text = text.replace("p","*1e-12")
    text = text.replace("f","*1e-15")
    text = text.replace("a","*1e-18")
    try: return float(eval(text))
    except: return nan

def isnan(x):
    """Is x an invalid floating point value? ('Not a Number')"""
    return x!= x

if __name__ == "__main__":
    from pdb import pm # for debugging
    import logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(module)s, line %(lineno)d: %(funcName)s: %(message)s",
    )
    from instrumentation import SAXS_WAXS_methods as configuration

    class ConfigurationPanel(BasePanel):
        name = "configuration"
        title = "Configuration"
        standard_view = [
            "Title",
            "Motor names",
            "Motor labels",
            "Formats",
            "Tolerance",
            "Rows",
            "Go To",
        ]

        def __init__(self,parent,configuration):
            parameters = [
                [[PropertyPanel,"Title",configuration,"title"],{}],
                [[PropertyPanel,"Motor names",configuration,"motor_names"],{}],
                [[PropertyPanel,"Motor labels",configuration,"motor_labels"],{}],
                [[PropertyPanel,"Formats",configuration,"formats"],{}],
                [[PropertyPanel,"Tolerance",configuration,"tolerance"],{}],
                [[PropertyPanel,"Rows",configuration,"nrows"],{}],
                [[PropertyPanel,"Go To",configuration,"serial"],{"type":"All motors at once/One motor at a time (left to right)"}],
            ]
            from numpy import inf
            BasePanel.__init__(self,
                parent=parent,
                name=self.name,
                title=self.title,
                parameters=parameters,
                standard_view=self.standard_view,
                subname=True,
                label_width=90,
                width=230,
                refresh_period=1.0,
            )

    app = wx.App(redirect=False) 
    self = ConfigurationPanel(parent=None,configuration=configuration)
    app.MainLoop()
