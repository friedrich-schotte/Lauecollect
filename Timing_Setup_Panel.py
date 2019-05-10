#!/usr/bin/env python
"""
Grapical User Interface for FPGA Timing System.
Author: Friedrich Schotte
Date created: 2018-12-04
Date last modified: 2019-03-26
"""
__version__ = "1.3" # using timing_system.prefixes for choices

from logging import debug,info,warn,error
import wx

class Timing_Setup_Panel(wx.Frame):
    title = "Timing System Setup"
    icon = "timing-system"
    
    def __init__(self,parent=None,name="TimingPanel"):
        wx.Frame.__init__(self,parent=parent,title=self.title)
        self.name = name
        panel = wx.Panel(self)

        from Icon import SetIcon
        SetIcon(self,self.icon)

        # Controls
        from EditableControls import ComboBox
        style = wx.TE_PROCESS_ENTER
        width = 160
        
        self.Prefix = ComboBox(panel,style=style,size=(width,-1))
        
        self.Address = wx.TextCtrl(panel,style=wx.TE_READONLY,size=(width,-1))
        self.Address.Enabled = False
        
        # Callbacks
        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnterPrefix,self.Prefix)
        self.Bind (wx.EVT_COMBOBOX  ,self.OnEnterPrefix,self.Prefix)
        self.Bind (wx.EVT_CLOSE     ,self.OnClose)

        # Layout
        layout = wx.GridBagSizer(1,1)
        a = wx.ALIGN_CENTRE_VERTICAL
        e = wx.EXPAND

        row = 0
        label = wx.StaticText(panel,label="EPICS Record:")
        layout.Add (label,(row,0),flag=a)
        layout.Add (self.Prefix,(row,1),flag=a|e)

        row += 1
        label = wx.StaticText(panel,label="IP Address (auto detect):")
        layout.Add (label,(row,0),flag=a)
        layout.Add (self.Address,(row,1),flag=a|e)

        # Leave a 5-pixel wide border.
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add (layout,flag=wx.ALL,border=5)
        panel.SetSizer(box)
        panel.Fit()
        self.Fit()

        self.Show()
        self.refresh()

    def OnEnterPrefix(self,event):
        """Called if EPICS record prefix is changed"""
        from timing_system import timing_system
        timing_system.prefix = self.Prefix.Value
        self.refresh()

    def OnRefresh(self,event=None):
        self.refresh()

    def refresh(self,event=None):
        """Update the controles and indicators with current values"""
        if self.Shown:
            from timing_system import timing_system
            self.Prefix.Value = timing_system.prefix
            self.Prefix.Items = timing_system.prefixes
            self.Address.Value = timing_system.ip_address
            self.timer = wx.Timer(self)
            self.Bind(wx.EVT_TIMER,self.refresh,self.timer)
            self.timer.Start(1000,oneShot=True)
            
    def OnClose(self,event):
        self.Shown = False
        ##self.Destroy() # might crash under Windows
        wx.CallLater(2000,self.Destroy)

SetupPanel = Timing_Setup_Panel # for backward compatibility


if __name__ == '__main__':
    from pdb import pm # for debugging
    from tempfile import gettempdir
    logfile = gettempdir()+"/Timing_Setup_Panel.log"
    import logging # for debugging
    logging.basicConfig(
        level=logging.DEBUG,
        filename=logfile,
        format="%(asctime)s %(levelname)s: %(message)s",
    )

    app = wx.App(redirect=False) 
    panel = Timing_Setup_Panel()
    app.MainLoop()
