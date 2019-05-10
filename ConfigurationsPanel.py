#!/usr/bin/env python
"""Manage settings for different locations / instruments
Author: Friedrich Schotte
Date created: 2015-06-15
Date last modified: 2018-09-10
"""
from configurations import configurations
import wx
import  wx.lib.scrolledpanel
from EditableControls import TextCtrl,ComboBox
__version__ = "1.1" # ScrolledPanel

class ConfigurationPanel(wx.Frame):
    """Manage settings for different locations / instruments"""
    from setting import setting
    size = setting("size",(600,800))

    def __init__ (self,parent=None):        
        wx.Frame.__init__(self,parent,title="Configurations",size=self.size)
        from Icon import SetIcon
        SetIcon(self,"Tool")
        # Controls
        self.panel =   wx.lib.scrolledpanel.ScrolledPanel(self)
        
        style = wx.TE_PROCESS_ENTER

        self.Configuration = ComboBox(self.panel,size=(240,-1),style=style)
        self.SavedToCurrent = wx.Button(self.panel,label="           Saved          ->",size=(160,-1))
        self.CurrentToSaved = wx.Button(self.panel,label="<-        Current           ",size=(160,-1))

        N = len(configurations.parameters.descriptions)
        self.Descriptions = [TextCtrl(self.panel,size=(240,-1),style=style) for i in range(0,N)]
        self.CurrentValues = [ComboBox(self.panel,size=(160,-1),style=style) for i in range(0,N)]
        self.SavedValues = [ComboBox(self.panel,size=(160,-1),style=style) for i in range(0,N)]

        # Callbacks
        self.Configuration.Bind(wx.EVT_TEXT_ENTER,self.OnConfiguration)
        self.Configuration.Bind(wx.EVT_COMBOBOX,self.OnConfiguration)
        self.SavedToCurrent.Bind(wx.EVT_BUTTON,self.OnSavedToCurrent)
        self.CurrentToSaved.Bind(wx.EVT_BUTTON,self.OnCurrentToSaved)
        self.Bind(wx.EVT_TEXT_ENTER,self.OnEnter)
        self.Bind(wx.EVT_COMBOBOX,self.OnEnter)
        self.Bind(wx.EVT_SIZE,self.OnResize)
        ##self.Bind(wx.EVT_CLOSE,self.OnClose)

        # Layout
        layout = wx.BoxSizer()
        
        grid = wx.FlexGridSizer(cols=3,hgap=2,vgap=2)
        flag = wx.ALIGN_LEFT

        grid.Add (self.Configuration,flag=flag)
        grid.Add (self.SavedToCurrent,flag=flag)
        grid.Add (self.CurrentToSaved,flag=flag)

        for i in range(0,N):
            grid.Add (self.Descriptions[i],flag=flag)
            grid.Add (self.SavedValues[i],flag=flag)
            grid.Add (self.CurrentValues[i],flag=flag)
        
        # Leave a 10-pixel wide space around the panel.
        border_box = wx.BoxSizer(wx.VERTICAL)
        border_box.Add (grid,flag=wx.EXPAND|wx.ALL)
        layout.Add (border_box,flag=wx.EXPAND|wx.ALL,border=10)

        self.panel.SetSizer(layout)
        ##self.panel.SetAutoLayout(True)
        self.panel.SetupScrolling()
        ##self.panel.Fit()
        ##self.Fit()
        self.Show()

        self.keep_alive()

    def keep_alive(self,event=None):
        """Periodically refresh the displayed settings (every second)."""
        self.refresh()
        self.timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.keep_alive,self.timer)
        self.timer.Start(1000,oneShot=True)

    def refresh(self,Event=None):
        """Update all controls"""
        configuration_names = configurations.configuration_names
        if not self.Configuration.Value in configuration_names:
            self.Configuration.Value = configurations.current_configuration
        self.Configuration.Items = configuration_names
        configuration_name = self.Configuration.Value
        
        ##self.SavedLabel.Label =  configuration_name

        descriptions = configurations.parameters.descriptions
        values       = [str(v) for v in configurations[""]]
        saved_values = [str(v) for v in configurations[configuration_name]]
        choices      = [[str(c) for c in l] for l in configurations.choices]
        agree        = [v1 == v2 for v1,v2 in zip(values,saved_values)]
        N = len(descriptions)
        for i in range(0,N):
            self.Descriptions[i].Value = descriptions[i]
            self.SavedValues[i].Value = saved_values[i]
            self.SavedValues[i].Items = choices[i]
            self.SavedValues[i].BackgroundColour = (255,255,255) if agree[i] else (255,190,190)
            self.SavedValues[i].ForegroundColour = (100,100,100)
            self.CurrentValues[i].Value = values[i]
            self.CurrentValues[i].Items = choices[i]

        self.Configuration. BackgroundColour = (255,255,255) if all(agree) else (255,190,190)
        self.SavedToCurrent.BackgroundColour = (255,255,255) if all(agree) else (255,190,190)
        self.SavedToCurrent.Enabled = not all(agree)
        self.CurrentToSaved.Enabled = not all(agree)

    def OnConfiguration(self,event):
        """Called if the configration is switched"""
        self.refresh()

    def OnSavedToCurrent(self,event):
        """Make the named saved configuration active"""
        name = self.Configuration.Value
        configurations[""] = configurations[name]
        self.refresh()

    def OnCurrentToSaved(self,event):
        """Save the active configuration under the selected name"""
        name = self.Configuration.Value
        configurations[name] = configurations[""]
        self.refresh()

    def OnEnter(self,event):
        """Called it a entry is modified"""
        N = len(configurations.parameters.descriptions)
        name = self.Configuration.Value
        configurations[name] = [eval(self.SavedValues  [i].Value) for i in range(0,N)]        
        configurations[""]   = [eval(self.CurrentValues[i].Value) for i in range(0,N)]        
        self.refresh()

    def OnResize(self,event):
        event.Skip()
        self.size = tuple(self.Size)

    def OnClose(self,event):
        """Handle Window closed event"""
        self.Destroy()
        

def eval(x):
    """Convert x to a built-in Python data type, by default to string"""
    try: return __builtins__.eval(x)
    except: return str(x)

    
if __name__ == '__main__': # for testing
    from pdb import pm
    app = wx.App(redirect=False)
    win = ConfigurationPanel()
    app.MainLoop()
