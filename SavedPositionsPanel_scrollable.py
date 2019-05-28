#!/usr/bin/env python
"""Control panel to save and recall motor positions.
Author: Friedrich Schotte
Date created: 2010-12-13
Date last modified: 2019-05-28
"""
__version__ = "5.0" # scrollable

from logging import debug,info,warn,error
import traceback
import wx
from numpy import ndarray,isnan
# Turn off IEEE-754 warnings in numpy 1.6+ ("invalid value encountered in...")
import numpy; numpy.seterr(invalid="ignore",divide="ignore")

class SavedPositionsPanel(wx.Frame):
    """Control panel to save and recall motor positions"""
    icon = "Tool"
    name = None
    configuration = None
    
    def __init__(self,configuration=None,name=None,globals=None,locals=None,
        parent=None,title=None):
        """
        configuration: object of type "configuration" from "configuration.py"
        name: name of configuration, e.g. "alio_diffractometer_saved_positions",
            "timing_modes"
        globals: When using "name=...", dictionary containing available motor
            objects.
            e.g. "from instrumentation import *" populates the global names space,
            globals=globals() to make these available inside the SavedPositionsPanel
        title: overrides user-configurable title (for backward compatibility)
        """
        self.cache = {}

        self.locals = locals
        self.globals = globals

        if name is not None: self.name = name
        if configuration is not None: self.configuration = configuration

        if self.configuration is None and self.name is None: 
            raise RuntimeError("SavedPositionsPanel requires 'configuration' or 'name'")
        
        if self.configuration is None:
            from configuration import configuration
            self.configuration = configuration(self.name,globals=globals,locals=locals)

        if title is not None: self.configuration.title = title

        wx.Frame.__init__(self,parent=parent)

        # Icon
        from Icon import SetIcon
        SetIcon(self,self.icon,self.configuration.name)

        self.layout()
        self.Fit()
        self.Show()

        # Make sure "on_input" is called only after "update_settings".
        # Call the "on_input" routine whenever the user presses Enter.
        self.Bind (wx.EVT_TEXT_ENTER,self.on_input)

        # Periodically update the displayed fields.
        self.timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.OnTimer)
        self.timer.Start(5000,oneShot=True)

        from threading import Thread
        self.update_thread = Thread(target=self.keep_updated)
        self.update_thread.daemon = True
        self.update_thread.start()

    def OnTimer(self,event=None):
        """Called periodically every second triggered by a timer"""
        ##debug("Started  %r" % self.configuration.name)
        import traceback
        try: self.update_module()
        except Exception,msg: error("%s\n%s" % (msg,traceback.format_exc()))
        try: self.update_layout()
        except Exception,msg: error("%s\n%s" % (msg,traceback.format_exc()))
        try: self.update_date()
        except Exception,msg: error("%s\n%s" % (msg,traceback.format_exc()))
        self.timer.Start(5000,oneShot=True) # Need to restart the Timer
        ##debug("Finished %r" % self.configuration.name)

    def keep_updated(self):
        while True:
            try:
                self.check_for_updates()
                self.delay()
            except wx.PyDeadObjectError: break

    def delay(self):
        from time import sleep
        sleep(1)

    def check_for_updates(self):
        ##debug("Started %r" % self.configuration.name)
        names = []
        names += ["title"]
        names += ["description"]
        names += ["matching_description"]
        names += ["closest_descriptions"]
        names += ["command_description"]
        names += ["command_rows"]
        names += ["matching_rows"]
        names += ["closest_rows"]

        for j in range(0,self.configuration.n_motors):
            names += ["current_position[%d]" % j]
            names += ["motor_labels[%d]" % j]
            names += ["formats[%d]"  % j]            
        for i in range(0,self.configuration.nrows):
            names += ["descriptions[%d]" % i]
            names += ["updated[%d]" % i]
        for i in range(0,self.configuration.nrows):
            for j in range(0,self.configuration.n_motors):
                names += ["positions[%d][%d]" % (j,i)]
        for i in range(0,self.configuration.nrows):
            for j in range(0,self.configuration.n_motors):
                names += ["positions_match[%d][%d]" % (j,i)]

        from collections import OrderedDict
        changes = OrderedDict()
        for name in names:
            code = "self.configuration."+name
            try: value = eval(code)
            except Exception,msg:
                error("%r: %s\n%s" % (code,msg,traceback.format_exc()))
                value = None
            if value is not None:
                from same import same
                if name not in self.cache or not same(value,self.cache[name]):
                    changes[name] = value

        self.cache.update(changes)

        if changes:
            ##debug("%s: changes: %r" % (self.configuration.name,changes))
            myEVT_UPDATE = wx.NewEventType()
            EVT_UPDATE = wx.PyEventBinder(myEVT_UPDATE,1)
            self.Bind(EVT_UPDATE,self.OnUpdate)
            event = self.UpdateEvent(myEVT_UPDATE,value=changes)
            wx.PostEvent(self,event)
        ##debug("Finished %r" % self.configuration.name)

    class UpdateEvent(wx.PyCommandEvent):
        """Event to signal that a value changed"""
        def __init__(self,etype,eid=-1,value=""):
            wx.PyCommandEvent.__init__(self,etype,eid)
            self.value = value

    def OnUpdate(self,event):
        changes = event.value
        self.update(changes)

    @property
    def menu_bar(self):
        """MenuBar object"""
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
        for i in range(0,len(self.configuration.motor_labels)):
            self.ViewMenu.AppendCheckItem(100+i,self.configuration.motor_labels[i])
        self.ViewMenu.AppendSeparator()
        menuBar.Append (self.ViewMenu,"&View")
        # More
        menu = wx.Menu()
        menu.Append (201,"Configure this Panel...")
        menu.Append (202,"Modes/Configurations Panel...")
        menuBar.Append (menu,"&More")
        # Help
        menu = wx.Menu()
        menu.Append (wx.ID_ABOUT,"About...","Show version number")
        menuBar.Append (menu,"&Help")

        # Callbacks
        for i in range(0,len(self.configuration.motor_labels)):
            self.Bind(wx.EVT_MENU,self.OnView,id=100+i)
        self.Bind(wx.EVT_MENU_OPEN,self.OnOpenView)
        self.Bind(wx.EVT_MENU,self.OnConfiguration,id=201)
        self.Bind(wx.EVT_MENU,self.OnConfigurations,id=202)
        self.Bind(wx.EVT_MENU,self.OnAbout,id=wx.ID_ABOUT)

        return menuBar

    date_width = 160

    @property
    def ControlPanel(self):
        # Controls and Layout
        from EditableControls import TextCtrl
        panel = wx.Panel(self)

        panel.vertical = self.configuration.vertical
        def flip(i,j): return (j,i) if panel.vertical else (i,j)
        
        # Leave a 5 pixel wide border.
        border_box = wx.BoxSizer(wx.VERTICAL)
        # Labels
        grid = panel.grid = wx.GridBagSizer(1,1)

        flag = wx.ALIGN_CENTRE_VERTICAL|wx.ALIGN_CENTRE_HORIZONTAL|wx.ALL
        style = wx.TE_PROCESS_ENTER
        if not panel.vertical: style |= wx.TE_MULTILINE
        left,center,right = wx.ALIGN_LEFT,wx.ALIGN_CENTER_HORIZONTAL,wx.ALIGN_RIGHT

        row_height = self.configuration.row_height

        # Labels
        header_flag = wx.ALIGN_CENTRE_VERTICAL|wx.ALIGN_CENTRE_HORIZONTAL|wx.ALL|wx.ALIGN_TOP|wx.EXPAND

        width = self.configuration.description_width
        if panel.vertical: width = -1
        panel.DescriptionLabel = wx.Button(panel,label="Name",size=(width,row_height))
        panel.DescriptionLabel.Enabled = False
        grid.Add(panel.DescriptionLabel,flip(0,1),flag=header_flag)

        width = 100
        if panel.vertical: width = -1
        panel.DateLabel = wx.Button(panel,label="Updated",size=(width,row_height))
        panel.DateLabel.Enabled = False
        grid.Add(panel.DateLabel,flip(0,2),flag=header_flag)

        panel.PositionLabels = []
        for i in range(0,self.configuration.n_motors):
            label = self.configuration.motor_labels[i]
            width = self.configuration.widths[i]
            if panel.vertical: width = -1
            button = wx.Button(panel,label=label,size=(width,row_height),
                id=300+i*100+98)
            button.Enabled = self.configuration.are_configuration[i]
            self.Bind(wx.EVT_BUTTON,self.OnShowConfiguration,button)
            grid.Add(button,flip(0,i+3),flag=header_flag)
            panel.PositionLabels += [button]

        # Controls       
        panel.Descriptions = ndarray(self.configuration.nrows,object)
        for i in range(0,self.configuration.nrows):
            width = self.configuration.description_width
            if panel.vertical: width = self.configuration.description_width
            align = center if panel.vertical else left
            panel.Descriptions[i] = TextCtrl(panel,size=(width,row_height),
                style=style|align,id=100+i)
            grid.Add(panel.Descriptions[i],flip(i+1,1),flag=flag)
        self.NormalBackgroundColour = panel.Descriptions[0].BackgroundColour \
            if len(panel.Descriptions) > 0 else panel.BackgroundColour
                                      

        panel.Dates = ndarray(self.configuration.nrows,object)
        for i in range(0,self.configuration.nrows):
            width = self.date_width
            if panel.vertical: width = self.configuration.description_width
            panel.Dates[i] = TextCtrl(panel,size=(width,row_height),style=style,id=200+i)
            grid.Add(panel.Dates[i],flip(i+1,2),flag=flag)

        panel.Positions = ndarray((self.configuration.nrows,self.configuration.n_motors),object)
        for i in range(0,self.configuration.nrows):
            for j in range(0,self.configuration.n_motors):
                width = self.configuration.widths[j]
                align = right if self.configuration.are_numeric[j] else left
                panel.Positions[i,j] = TextCtrl(panel,size=(width,row_height),
                    style=style|align,id=300+j*100+i)
                panel.Positions[i,j].BackgroundColour = panel.BackgroundColour
                grid.Add(panel.Positions[i,j],flip(i+1,j+3),flag=flag|wx.EXPAND)

        header_flag = wx.ALIGN_CENTRE_VERTICAL|wx.ALIGN_CENTRE_HORIZONTAL|wx.ALL|wx.ALIGN_TOP|wx.EXPAND

        panel.SelectButtons = []
        height = panel.Descriptions[0].Size[1] if len(panel.Descriptions) > 0 else -1
        for i in range(0,self.configuration.nrows):
            label = self.configuration.apply_button_label
            width = int(20+6.5*len(label)) if len(label) <= 10 else -1
            if panel.vertical: width = self.configuration.description_width
            button = wx.ToggleButton(panel,label=label,size=(width,height),id=i)
            button.Shown = self.configuration.show_apply_buttons
            grid.Add(button,flip(i+1,0),flag=flag)
            self.Bind(wx.EVT_TOGGLEBUTTON,self.OnSelect,button)
            panel.SelectButtons += [button]

        panel.DefineButtons = []
        height = panel.Descriptions[0].Size[1] if len(panel.Descriptions) > 0 else -1
        for i in range(0,self.configuration.nrows):
            label = self.configuration.define_button_label
            width = 20+7*len(label) if len(label) <= 10 else -1
            if panel.vertical: width = self.configuration.description_width
            button = wx.Button(panel,label=label,size=(width,height),id=100+i)
            button.Shown = self.configuration.show_define_buttons
            grid.Add(button,flip(i+1,self.configuration.n_motors+3),flag=flag)
            self.Bind(wx.EVT_BUTTON,self.define_setting,button)
            panel.DefineButtons += [button]

        # Current values
        width = panel.SelectButtons[0].Size[0] if len(panel.SelectButtons) > 0 else -1
        if panel.vertical: width = self.configuration.description_width
        label = wx.StaticText(panel,label="Current",size=(width,row_height))
        label.Shown = self.configuration.show_apply_buttons
        grid.Add(label,flip(self.configuration.nrows+1,0),flag=flag)

        width = self.configuration.description_width
        align = center if panel.vertical else left
        panel.CurrentDescription = TextCtrl(panel,size=(width,row_height),
            style=style|align,id=100+99)
        panel.CurrentDescription.BackgroundColour = panel.BackgroundColour
        grid.Add(panel.CurrentDescription,flip(self.configuration.nrows+1,1),flag=flag)

        width = self.date_width
        if panel.vertical: width = self.configuration.description_width
        panel.CurrentDate = TextCtrl(panel,size=(width,row_height),style=style,id=200+99)
        panel.CurrentDate.BackgroundColour = panel.BackgroundColour
        panel.CurrentDate.Enabled = True
        grid.Add(panel.CurrentDate,flip(self.configuration.nrows+1,2),flag=flag)

        panel.CurrentPositions = ndarray(self.configuration.n_motors,object)
        for i in range(0,self.configuration.n_motors):
            width = self.configuration.widths[i]
            align = right if self.configuration.are_numeric[i] else left
            panel.CurrentPositions[i] = TextCtrl(panel,size=(width,row_height),
                style=style|align,id=300+i*100+99)
            panel.CurrentPositions[i].BackgroundColour = panel.BackgroundColour
            grid.Add(panel.CurrentPositions[i],flip(self.configuration.nrows+1,i+3),flag=flag)

        border_box.Add (grid,flag=wx.ALL|wx.EXPAND,border=5)

        panel.StopButton = wx.Button(panel,label="Stop")
        panel.StopButton.Shown = self.configuration.show_stop_button
        self.Bind(wx.EVT_BUTTON,self.stop,panel.StopButton)
        border_box.Add (panel.StopButton,flag=wx.ALL|wx.ALIGN_CENTRE_HORIZONTAL,border=2)
        
        panel.SetSizer(border_box)
        panel.Fit()
        return panel

    def layout(self):
        menu_bar = self.menu_bar
        old_menu_bar = self.MenuBar
        self.MenuBar = menu_bar
        if old_menu_bar: old_menu_bar.Destroy()
        
        panel = self.ControlPanel
        if hasattr(self,"panel"): self.panel.Destroy()
        self.panel = panel

        self.Fit()
        self.update()

    def update_module(self):
        from os.path import getmtime
        import SavedPositionsPanel_2 as module
        ##info("Checking file %r..." % module.__file__)
        if not hasattr(module,"__timestamp__"):
            module.__timestamp__ = getmtime(module.__file__)
        if getmtime(module.__file__) != module.__timestamp__:
            module.__timestamp__ = getmtime(module.__file__)
            reload(module)
            info('Reloaded module (version %s)' % module.__version__)
            self.__class__ = module.SavedPositionsPanel
            self.layout()

    @property
    def update_needed(self):
        """Has the configuration has changed?"""
        update_needed = False
        
        nrows = len(self.panel.Descriptions)
        if nrows != self.configuration.nrows: update_needed = True

        n_motors = self.panel.Positions.shape[1]
        if n_motors != self.configuration.n_motors: update_needed = True

        widths = []
        for i in range(0,self.panel.Positions.shape[1]):
            widths += [self.panel.Positions[0][i].Size[0] if i<len(self.panel.Positions[0]) else 0]
        if widths != self.configuration.widths: update_needed = True

        description_width = self.panel.Descriptions[0].Size[0] if len(self.panel.Descriptions)>0 else 0
        if description_width != self.configuration.description_width: update_needed = True

        row_height = self.panel.Descriptions[0].Size[1] if len(self.panel.Descriptions)>0 else 0
        if row_height != self.configuration.row_height: update_needed = True
        
        show_apply_buttons = self.panel.SelectButtons[0].Shown if len(self.panel.SelectButtons)>0 else False
        if show_apply_buttons != self.configuration.show_apply_buttons: update_needed = True
        
        apply_button_label = self.panel.SelectButtons[0].Label if len(self.panel.SelectButtons)>0 else ""
        if apply_button_label != self.configuration.apply_button_label: update_needed = True

        show_define_buttons = self.panel.DefineButtons[0].Shown if len(self.panel.DefineButtons)>0 else False
        if show_define_buttons != self.configuration.show_define_buttons: update_needed = True
        
        define_button_label = self.panel.DefineButtons[0].Label if len(self.panel.DefineButtons)>0 else ""
        if define_button_label != self.configuration.define_button_label: update_needed = True

        show_stop_button = self.panel.StopButton.Shown
        if show_stop_button != self.configuration.show_stop_button: update_needed = True

        vertical = self.panel.vertical
        if vertical != self.configuration.vertical: update_needed = True
        
        if update_needed: debug("update_needed: %r" % update_needed)
        return update_needed
        
    def update_layout(self):
        """Update the number of rows or columns if the configuration has changed"""
        if self.update_needed: self.layout()

    def update_date(self):
        self.panel.CurrentDate.Value = self.configuration.current_timestamp

    def update(self,changes={}):
        """Update the panel"""
        debug("Started %r" % self.configuration.name)
        from numpy import nan

        self.Title = self.cache.get("title","")

        for i in range(0,len(self.panel.PositionLabels)):
            value = self.cache.get("motor_labels[%d]"%i,"")
            self.panel.PositionLabels[i].Label = value

        for i in range(0,len(self.panel.Descriptions)):
            value = self.cache.get("descriptions[%d]"%i,"")
            self.panel.Descriptions[i].Value = value
        for i in range(0,len(self.panel.Dates)):
            value = self.cache.get("updated[%d]"%i,"")
            self.panel.Dates[i].Value = value

        for i in range(0,len(self.panel.Positions)):
            for j in range(0,len(self.panel.Positions[i])):
                ##if "positions[%d][%d]"%(j,i) in changes or "formats[%d]"%j in changes:
                    value = self.cache.get("positions[%d][%d]"%(j,i),nan)
                    format = self.cache.get("formats[%d]"%j,"%s")
                    self.panel.Positions[i,j].Value = tostr(value,format)

        # Update current description, date, motor positions
        for i in range(0,len(self.panel.CurrentPositions)):
            ##if "current_position[%d]"%i in changes or "formats[%d]"%i in changes:
                value = self.cache.get("current_position[%d]"%i,nan)
                format = self.cache.get("formats[%d]"%i,"%s")
                self.panel.CurrentPositions[i].Value = tostr(value,format)

        description = self.cache.get("description","")
        self.panel.CurrentDescription.Value = description

        # Highlight the current settings
        matching_description = self.cache.get("matching_description","")
        closest_descriptions = self.cache.get("closest_descriptions","")
        command_description  = self.cache.get("command_description","")
        matching_rows = self.cache.get("matching_rows",[])
        closest_rows  = self.cache.get("closest_rows",[])
        command_rows  = self.cache.get("command_rows",[])

        for i in range(0,len(self.panel.Positions)):
            selected = (i in command_rows)
            self.panel.SelectButtons[i].Value = \
                selected if self.configuration.multiple_selections else False
            if selected:
                color = self.matching_color if i in matching_rows else self.close_color
            else: color = self.NormalBackgroundColour
            self.panel.SelectButtons[i].BackgroundColour = color
            if i in matching_rows or i in closest_rows:
                if i in matching_rows: color = self.matching_color
                elif i in closest_rows: color = self.close_color
                self.panel.Descriptions[i].BackgroundColour = color
                self.panel.Dates[i].BackgroundColour = color
                for j in range(0,self.configuration.n_motors):
                    matches = self.cache.get("positions_match[%d][%d]"%(j,i),False)
                    color = self.matching_color if matches else self.close_color
                    self.panel.Positions[i,j].BackgroundColour = color
            elif i in command_rows:
                color = self.close_color
                self.panel.Descriptions[i].BackgroundColour = color
                self.panel.Dates[i].BackgroundColour = color
                for j in range(0,self.configuration.n_motors):
                    matches = self.cache.get("positions_match[%d][%d]"%(j,i),False)
                    color = self.close_color if matches else self.command_color
                    self.panel.Positions[i,j].BackgroundColour = color
            else:
                color = self.NormalBackgroundColour
                self.panel.Descriptions[i].BackgroundColour = color
                self.panel.Dates[i].BackgroundColour = color
                for j in range(0,self.configuration.n_motors): 
                    self.panel.Positions[i,j].BackgroundColour = color
        debug("Finished %r" % self.configuration.name)

    matching_color = wx.Colour(0,180,0)
    close_color = wx.Colour(255,200,0)
    command_color = wx.Colour(255,128,128)

    def on_input(self,event):
        """This is called when the use switches between fields and controls
        using Tab or the mouse, or presses Enter in a text entry. This does
        necessarily indicate that any value was changed. But it is a good
        opportunity the process any changes."""
        Id = event.Id
        info("event.Id=%r" % event.Id)
        
        nrows = self.panel.Descriptions.shape[0]
        for i in range(0,nrows):
            if self.panel.Descriptions[i].Id == Id:
                text = self.panel.Descriptions[i].Value
                info("%r.descriptions[%r] = %r" % (self.configuration,i,text))
                self.configuration.descriptions[i] = text
            if self.panel.Dates[i].Id == Id:
                text = self.panel.Dates[i].Value
                info("%r.updated[%r] = %r" % (self.configuration,i,text))
                self.configuration.updated[i] = text
            for j in range(0,len(self.configuration.positions)):
                if self.panel.Positions[i,j].Id == Id:
                    text = self.panel.Positions[i,j].Value
                    try: value = motor_position(text,self.configuration.formats[j])
                    except Exception,msg:
                        warn("%r,%r: %s: %s" % (i,j,text,msg))
                        continue
                    info("%r.positions[%r][%r] = %r" % (self.configuration,j,i,value))
                    self.configuration.positions[j][i] = value

        if self.panel.CurrentDescription.Id == Id:
            value = self.panel.CurrentDescription.Value
            info("%r.value = %r" % (self.configuration,value))
            self.configuration.value = value

        for j in range(0,len(self.configuration.positions)):
            if self.panel.CurrentPositions[j].Id == Id:
                text = self.panel.CurrentPositions[j].Value
                try: value = motor_position(text,self.configuration.formats[j])
                except Exception,msg:
                    warn("%r: %s: %s" % (j,text,msg))
                    continue
                info("%r.current_position[%r] = %r" % (self.configuration,j,value))
                self.configuration.current_position[j] = value

    def OnShowConfiguration(self,event):
        """Display the configuration panel for this configuration"""
        Id = event.Id
        ##info("event.Id=%r" % event.Id)
        
        for i in range(0,self.configuration.n_motors):
            if self.panel.PositionLabels[i].Id == Id:
                name = self.configuration.motor_configuration_names[i]
                info("Showing configration %r" % name)
                show_panel(name)

    def OnSelect(self,event):
        """Handle row select"""
        ##info("event.Id=%r" % event.Id)
        row = event.Id 
        selected = event.IsChecked()
        info("Select row %r,%r" % (row,selected))
        if self.configuration.multiple_selections:
            rows = self.configuration.command_rows
            if not selected and  row in rows: rows.remove(row)
            if selected and not row in rows: rows.append(row)
        else: rows = [row]
        info("rows = %r" % rows)
        self.configuration.command_rows = rows
        self.configuration.applying = True
        
        if not self.configuration.multiple_selections:
            # Make the toggle button behave like a command button
            button = event.EventObject
            button.Value = False

    def define_setting(self,event):
        """Copy the current motor settings in the row of the 'Set" button
        that was pressed."""
        info("event.Id=%r" % event.Id)
        row = event.Id-100 # Row number of "Set" button pressed
        info("self.configuration.matching_rows = [%r]" % row)
        self.configuration.matching_rows = [row]

    def stop(self,event):
        """To cancel any move should one hit the wrong button by mistake"""
        self.configuration.stop()

    from persistent_property import persistent_property
    __show__ = persistent_property("show",[])

    def get_show(self):
        """Which columns to show? list of boolean"""
        show = self.__show__
        while len(show) < len(self.configuration.motor_labels): show += [True]
        return show
    def set_show(self,value): self.__show__ = value
    show = property(get_show,set_show)

    def OnOpenView(self,event):
        """Called if the "View" menu is selected"""
        for i in range(0,len(self.configuration.motor_labels)):
            self.ViewMenu.Check(100+i,self.show[i])

    def OnView(self,event):
        """Called if one of the items of the "View" menu is selected"""
        i =  event.Id-100
        self.show[i] = not self.show[i]
        self.panel.Sizer.Fit(self)
        # To do: update panel

    def OnConfiguration(self,event):
        show_configuration(self.configuration.name)

    def OnConfigurations(self,event):
        show_configurations()

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

from Panel import BasePanel,PropertyPanel,TogglePanel,TweakPanel
class ConfigurationPanel(BasePanel):
    name = "configuration"
    title = "Configuration"
    standard_view = [
        "Rows",
        "Title",
        "Mnemonic",
        "Python code",
        "Column mnemonics",
        "Column labels",
        "Column widths",
        "Column formats",
        "Tolerances",
        "Name width",
        "Row height",
        "Apply buttons",
        "Apply button label",
        "Update buttons",
        "Update button label",
        "Stop button",
        "Go To",
        "Vertical",
        "Multiple Selections",
    ]

    def __init__(self,parent=None,configuration=None,name=None,
        globals=None,locals=None):
        if configuration is not None: self.configuration = configuration
        elif name is not None:
            from configuration import configuration
            self.configuration = configuration(name,globals=globals,locals=locals)
        else: raise RuntimeError("SavedPositionsPanel requires 'configuration' or 'name'")

        parameters = [
            [[PropertyPanel,"Rows",self.configuration,"nrows"],{}],
            [[PropertyPanel,"Title",self.configuration,"title"],{}],
            [[PropertyPanel,"Mnemonic",self.configuration,"name"],{}],
            [[PropertyPanel,"Python code",self.configuration,"motor_names"],{}],
            [[PropertyPanel,"Column mnemonics",self.configuration,"names"],{}],
            [[PropertyPanel,"Column labels",self.configuration,"motor_labels"],{}],
            [[PropertyPanel,"Column widths",self.configuration,"widths"],{}],
            [[PropertyPanel,"Column formats",self.configuration,"formats"],{}],
            [[PropertyPanel,"Tolerances",self.configuration,"tolerance"],{}],
            [[PropertyPanel,"Name width",self.configuration,"description_width"],{}],
            [[PropertyPanel,"Row height",self.configuration,"row_height"],{}],
            [[PropertyPanel,"Apply buttons",self.configuration,"show_apply_buttons"],{}],
            [[PropertyPanel,"Apply button label",self.configuration,"apply_button_label"],{}],
            [[PropertyPanel,"Update buttons",self.configuration,"show_define_buttons"],{}],
            [[PropertyPanel,"Update button label",self.configuration,"define_button_label"],{}],
            [[PropertyPanel,"Stop button",self.configuration,"show_stop_button"],{}],
            [[PropertyPanel,"Go To",self.configuration,"serial"],{"type":"All motors at once/One motor at a time (left to right)"}],
            [[PropertyPanel,"Vertical",self.configuration,"vertical"],{}],
            [[PropertyPanel,"Multiple Selections",self.configuration,"multiple_selections"],{}],
        ]
        from numpy import inf
        BasePanel.__init__(self,
            parent=parent,
            name=self.name,
            title=self.title,
            parameters=parameters,
            standard_view=self.standard_view,
            subname=True,
            label_width=130,
            width=250,
            refresh_period=1.0,
        )

class ConfigurationsPanel(wx.Frame):
    """Control panel to show all configurations"""
    icon = "Tool"
    title = "Modes/Configurations"
    
    def __init__(self,parent=None):
        wx.Frame.__init__(self,parent=parent)

        self.configure = False

        self.layout()
        self.Show()

        # Periodically update the displayed fields.
        self.timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.OnTimer)
        self.timer.Start(1000,oneShot=True)

    def OnTimer(self,event=None):
        """Called periodically every second triggered by a timer"""
        import traceback
        try: self.refresh_layout()
        except Exception,msg: error("%s" % msg); traceback.print_exc()
        self.timer.Start(1000,oneShot=True) # Need to restart the Timer

    def update_layout(self):
        """Update the number of rows or columns if the configuration has changed"""
        self.layout()

    def refresh_layout(self):
        """Update the number of rows or columns if the configuration has changed"""
        if self.update_needed: self.layout()

    @property
    def update_needed(self):
        update_needed = False
        labels = [self.label(i) for i in range(0,self.count) if self.show_in_list(i)]
        button_labels = [button.Label for button in self.panel.buttons]
        if labels != button_labels: update_needed = True
        if update_needed: debug("update_needed")
        return update_needed

    def layout(self):
        self.Title = self.title
        from Icon import SetIcon
        SetIcon(self,self.icon)

        if not self.MenuBar: self.MenuBar = self.menu_bar

        panel = self.ControlPanel
        if hasattr(self,"panel"): self.panel.Destroy()
        self.panel = panel
        self.Fit()

    @property
    def ControlPanel(self):
        # Controls and Layout
        panel = wx.Panel(self)

        ##sizer = wx.BoxSizer(wx.VERTICAL)
        sizer = wx.GridBagSizer(1,1)

        flag = wx.ALIGN_CENTRE_VERTICAL|wx.ALL|wx.EXPAND
        buttons = []
        j = 0
        for i in range(0,self.count):
            if self.show_in_list(i):
                button = wx.Button(panel,label=self.label(i),id=i)
                button.Shown = self.show_in_list(i)
                ##sizer.Add(button,flag=flag)        
                sizer.Add(button,(j,0),flag=flag)
                j += 1
                buttons += [button]
        panel.buttons = buttons
        panel.SetSizer(sizer)
        panel.Fit()

        self.Bind(wx.EVT_BUTTON,self.show)

        return panel

    @property
    def menu_bar(self):
        """MenuBar object"""
        # Menus
        menuBar = wx.MenuBar()
        # View
        self.ViewMenu = wx.Menu()
        for i in range(0,self.count):
            self.ViewMenu.AppendCheckItem(100+i," "+self.label(i)+" ")
        self.ViewMenu.AppendSeparator()
        menuBar.Append (self.ViewMenu,"&View")
        # More
        self.MoreMenu = wx.Menu()
        self.MoreMenu.AppendCheckItem(201,"Configure this Panel")
        menuBar.Append (self.MoreMenu,"&More")
        # Help
        menu = wx.Menu()
        menu.Append (wx.ID_ABOUT,"About...","Show version number")
        menuBar.Append (menu,"&Help")

        # Callbacks
        self.Bind(wx.EVT_MENU_OPEN,self.OnOpenView)
        for i in range(0,self.count):
            self.Bind(wx.EVT_MENU,self.OnView,id=100+i)
            
        self.Bind(wx.EVT_MENU,self.OnConfigure,id=201)
        self.Bind(wx.EVT_MENU,self.OnAbout,id=wx.ID_ABOUT)

        return menuBar

    def OnOpenView(self,event):
        """Called if the "View" menu is selected"""
        for i in range(0,self.count):
            self.ViewMenu.Check(100+i,self.show_in_list(i))
        self.MoreMenu.Check(201,self.configure)

    def OnView(self,event):
        """Called if one of the items of the "View" menu is selected"""
        i =  event.Id-100
        self.set_show_in_list(i,not self.show_in_list(i))
        self.layout()

    def OnConfigure(self,event):
        self.configure = not self.configure
        self.layout

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

    def show(self,event):
        """Display control panel"""
        ##info("event.Id=%r" % event.Id)
        from configuration import configuration
        name = configuration.configuration_names[event.Id]
        info("name=%r" % name)
        show_panel(name)

    @property
    def count(self):
        from configuration import configuration
        return len(configuration.configurations)
        
    def label(self,i):
        from configuration import configuration
        return configuration.configurations[i].title

    def show_in_list(self,i):
        from configuration import configuration
        return configuration.configurations[i].show_in_list

    def set_show_in_list(self,i,value):
        from configuration import configuration
        configuration.configurations[i].show_in_list = value


def tostr(x,format="%g"):
    """Converts a number to a string.
    This is needed to handle "not a number" and infinity properly.
    Under Windows, 'str()','repr()' and '%' format 'nan' as '-1.#IND' and 'inf'
    as '1.#INF', which is inconsistent with Linux ('inf' and 'nan').
    """
    from numpy import isnan,isinf
    from time_string import time_string
    try:
        if isnan(x): return ""
        elif isinf(x) and x>0: return "inf"
        elif isinf(x) and x<0: return "-inf"
        elif "time" in format:
            precision = format.split(".")[-1][0]
            try: precision = int(precision)
            except: precision = 3
            return time_string(x,precision)
        else: return format % x
    except TypeError: return str(x)

def motor_position(s,format="%g"):
    """Convert string to float and return 'not a number' if not possiple"""
    from time_string import seconds
    from numpy import nan
    if "time" in format: value = seconds(s)
    elif "s" in format: value = s # "%s" -> keep as string
    else:
        try: value = float(eval(s))
        except Exception: value = nan
    return value


def show_panel(name):
    ##exec("from instrumentation import *") # -> locals()
    ##SavedPositionsPanel(name=name,globals=globals(),locals=locals())
    from start import start
    start("SavedPositionsPanel_2","SavedPositionsPanel(name=%r,globals=globals(),locals=locals())" % name)
    
def show_configuration(name):
    ##exec("from instrumentation import *") # -> locals()
    ##ConfigurationPanel(name=self.configuration.name,globals=self.globals,locals=self.locals)
    from start import start
    start("SavedPositionsPanel_2","ConfigurationPanel(name=%r,globals=globals(),locals=locals())" % name)

def show_configurations():
    ##ConfigurationsPanel()
    from start import start
    start("SavedPositionsPanel_2","ConfigurationsPanel()")


if __name__ == '__main__':
    from pdb import pm # for debugging

    from redirect import redirect
    format="%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    redirect("SavedPositionsPanel_2",format=format)

    import autoreload
    ##name = ""
    ##name = "beamline_configuration"
    ##name = "sequence_modes"
    name = "high_speed_chopper_modes"
    ##name = "Julich_chopper_modes"
    ##name = "timing_modes"
    ##name = "delay_configuration"
    ##name = "power_configuration"
    ##name = "detector_configuration"
    ##name = "method"
    # Allow commandline argument to specifiy which configuration to use.
    from sys import argv
    if len(argv) >= 2: name = argv[1]

    if not hasattr(wx,"app"): wx.app = wx.App(redirect=False) 
    exec("from instrumentation import *") # -> globals()
    ##from instrumentation import * # -> globals()
    ##t = timing_sequencer # shortcut
    if name: SavedPositionsPanel(name=name,globals=globals(),locals=locals())
    else: ConfigurationsPanel()
    wx.app.MainLoop()
