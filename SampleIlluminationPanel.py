#!/usr/bin/env python
"""Sample illumination for the high-speed diffractometer.
F. Schotte, 26 Jun 2013 - 28 Oct 2014"""

__version__ = "1.1.1"
import wx
from sample_illumination_Ensemble import illuminator_voltage,illuminator_on
from EditableControls import TextCtrl

class SampleIlluminationPanel(wx.Frame):
    """Sample illumination for the high-speed diffractometer."""
    def __init__(self):
        wx.Frame.__init__(self,parent=None,
            title="Sample Illumination (Ensemble)")
        panel = wx.Panel(self)

        # Controls
        self.Voltage = TextCtrl(panel,size=(100,-1),style=wx.TE_PROCESS_ENTER)
        OnButton = wx.Button (panel,label="On")
        OffButton = wx.Button (panel,label="Off")

        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnterVoltage,self.Voltage)
        self.Bind (wx.EVT_BUTTON,self.OnOn,OnButton)
        self.Bind (wx.EVT_BUTTON,self.OnOff,OffButton)

        # Layout
        controls = wx.GridBagSizer(1,1)
        a = wx.ALIGN_CENTRE_VERTICAL
        e = wx.EXPAND

        t = wx.StaticText(panel,label="Voltage [V]:")
        controls.Add (t,(0,0),flag=a)
        controls.Add (self.Voltage,(0,1),flag=a|e)

        # Leave a 10 pixel wide border.
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add (controls,flag=wx.ALL,border=5)
        buttons = wx.BoxSizer(wx.HORIZONTAL)
        buttons.Add (OnButton,flag=wx.ALL|wx.ALIGN_CENTER_HORIZONTAL,border=5)
        buttons.AddSpacer(5)
        buttons.Add (OffButton,flag=wx.ALL|wx.ALIGN_CENTER_HORIZONTAL,border=5)
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
        self.Voltage.Value = "%.3f" % illuminator_voltage.value

        self.timer.Start(1000,oneShot=True)

    def OnEnterVoltage(self,event):
        """Set the voltage to a specific value."""
        text = self.Voltage.Value
        try: value = float(eval(text))
        except: self.refresh(); return
        illuminator_voltage.value = value
        self.refresh()

    def OnOn(self,event):
        """Turn the light on."""
        illuminator_on.value = True
        self.refresh()

    def OnOff(self,event):
        """Turn the light off."""
        illuminator_on.value = False
        self.refresh()


if __name__ == '__main__':

    app = wx.GetApp() if wx.GetApp() else wx.App()
    panel = SampleIlluminationPanel()
    app.MainLoop()
