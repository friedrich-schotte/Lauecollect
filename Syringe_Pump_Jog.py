# Hyun Sun Cho, Feb 24 2015
#!/usr/bin/python
ver = 1.0

import wx
from time import sleep
from syringe_pump import SyringePump

from CA import Record
#p = SyringePump("syringe_pump")
p = Record("NIH:syringe_pump")
CurrentVolume = p.V
#print CurrentVolume

class JogPump(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size=(320,180))
        
        panel = wx.Panel(self, -1)
        wx.Button(panel, -1, "Pump Init", (10,120))
        wx.StaticText(panel, -1, "Jog Speed [uL/s] : ", (20,15), style=wx.ALIGN_CENTER_VERTICAL)
        wx.StaticText(panel, -1, "Jog Volume [uL] : ", (20,50), style=wx.ALIGN_CENTER_VERTICAL)
        wx.StaticText(panel, -1, "Current Volume [uL] : ", (20,85), style=wx.ALIGN_CENTER_VERTICAL)
        wx.StaticText(panel, -1, "Jog with < or > arrow key", (120,125), style=wx.ALIGN_CENTER_VERTICAL)

        self.JogValue = "2.0"
        self.JogSpeed = "2.0"
        JogSpeedList = ["1.0","2.0","5.0","10.0","50.0"]
        JogValueList = ["1.0","2.0","5.0","10.0","50.0"]
        self.CurrentVolume = p.V #
        
        self.CB1 = wx.ComboBox(panel, 1, self.JogSpeed, (200,10),(100, 30),JogSpeedList)
        self.CB2 = wx.ComboBox(panel, 2, self.JogValue, (200,45),(100, 30), JogValueList)
        self.CB3 = wx.ComboBox(panel, 3, str(self.CurrentVolume) , (200,80),(100, 30))        

        panel.Bind(wx.EVT_BUTTON, self.OnInit)
        panel.Bind(wx.EVT_COMBOBOX, self.OnJogSpeed, self.CB1)
        panel.Bind(wx.EVT_COMBOBOX, self.OnJogValue, self.CB2)
        panel.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        panel.SetFocus()
        
        self.Centre()
        self.Show(True)

    def OnInit(self, event):
        """ pump initialization """
        MB = wx.MessageBox('Are you sure?', 'Pump Initialization', wx.YES | wx.NO | wx.ICON_INFORMATION)
        if MB == wx.YES:
            p.set_speed(200.0)
            p.init()
            p.set_speed(float(self.JogSpeed))
            self.CurrentVolume = 0.0
            self.CB3.SetValue(str(self.CurrentVolume))
        
    def OnJogSpeed(self, event):
        p.set_speed(float(self.CB1.GetValue()))
        sleep(0.25)
        self.JogSpeed = str(p.get_speed())
        #print p.get_speed()

    def OnJogValue(self, event):
        self.JogValue = float(self.CB2.GetValue())

    def OnKeyDown(self, event):
        keycode = event.GetKeyCode()
        JogVal = float(self.JogValue)
        if keycode == wx.WXK_RIGHT:
            p.V += JogVal
        if keycode == wx.WXK_LEFT:
            p.V -= JogVal

        time_wait = JogVal/float(self.JogSpeed)
        #print JogVal
        sleep(max(.25,time_wait)) # RS232 lag time + Jog time
        self.CurrentVolume = p.V
        self.CB3.SetValue(str(self.CurrentVolume))

if __name__ == "__main__":
    app = wx.App()
    JogPump(None, -1, 'JogPump.py')
    app.MainLoop()
