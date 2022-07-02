#!/usr/bin/env python
"""Lok-to-Clock: External synchronization of the Spectra Physics Tsunami
Ti:Sa laser

Author: Friedrich Schotte
Date created: 2013-06-26
Date last modified: 2019-11-15
"""

__version__ = "1.0.4" # renamed to Lok_To_Clock_Panel

import wx
from LokToClock import LokToClock

class Lok_To_Clock_Panel(wx.Frame):
    """Lok-to-Clock: External synchronization of the Spectra Physics Tsunami
    Ti:Sa laser"""
    def __init__(self):
        wx.Frame.__init__(self,parent=None,title="Lok-to-Clock")
        panel = wx.Panel(self)

        # Controls
        self.State = wx.StaticText(panel,size=(100,-1),label="?")
        OnButton = wx.Button (panel,label="Lock")
        OffButton = wx.Button (panel,label="Unlock")

        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnterVoltage,self.State)
        self.Bind (wx.EVT_BUTTON,self.OnOn,OnButton)
        self.Bind (wx.EVT_BUTTON,self.OnOff,OffButton)

        # Layout
        controls = wx.GridBagSizer(1,1)
        a = wx.ALIGN_CENTRE_VERTICAL
        e = wx.EXPAND

        t = wx.StaticText(panel,label="State:")
        controls.Add (t,(0,0),flag=a)
        controls.Add (self.State,(0,1),flag=a|e)

        # Leave a 5 pixel wide border.
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add (controls,flag=wx.ALL,border=5)
        buttons = wx.BoxSizer(wx.HORIZONTAL)
        buttons.Add (OnButton,flag=wx.ALL|wx.ALIGN_CENTER_HORIZONTAL)
        buttons.AddSpacer(5)
        buttons.Add (OffButton,flag=wx.ALL|wx.ALIGN_CENTER_HORIZONTAL)
        box.Add(buttons,flag=wx.ALL,border=5)
        panel.SetSizer(box)
        panel.Fit()
        self.Fit()
        self.Show()

        # Initialization
        self.timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.refresh,self.timer)
        self.timer.Start(1000,oneShot=True)

    def refresh(self,event=None):
        """Update the controls with current values"""
        locked = LokToClock.locked
        if locked == 1: state = "Locked"
        elif locked == 0: state = "Unlocked"
        else: state = "?"
        self.State.Label = state

        self.timer.Start(1000,oneShot=True)

    def OnEnterVoltage(self,event):
        """Set the voltage to a specific value."""
        text = self.State.Value
        try: value = (int(text) != 0)
        except: self.refresh(); return
        LokToClock.locked = value
        self.refresh()

    def OnOn(self,event):
        """Enable synchronization"""
        LokToClock.locked = 1
        self.refresh()

    def OnOff(self,event):
        """Disable synchronization"""
        LokToClock.locked = 0
        self.refresh()


if __name__ == '__main__':
    from redirect import redirect
    redirect("Lok_To_Clock_Panel")
    app = wx.App()
    panel = Lok_To_Clock_Panel()
    app.MainLoop()
