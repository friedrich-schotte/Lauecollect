#!/usr/bin/env python
"""Test cross platform compatibility of the "EditableControls" module
Friedrich Schotte, APS, 27 Sep 2014 - 27 Sep 2014
"""
__version__ = "1.0"
import wx
from EditableControls import TextCtrl,ComboBox
from logging import debug

class EditableControls_Test (wx.Frame):

    def __init__(self):
        wx.Frame.__init__(self,parent=None,title="Editable Controls Test")

        panel = wx.Panel(self)
        # Controls
        choices = ["Hydrogen","Helium","Lithium","Beryllium"]
        self.ComboBox = ComboBox(panel,choices=choices,
            style=wx.TE_PROCESS_ENTER,name="Sample ComboBox")
        self.TextCtrl = TextCtrl(panel,style=wx.TE_PROCESS_ENTER,
            name="Sample TextCtrl")
        # Callbacks
        self.Bind (wx.EVT_TEXT_ENTER,self.OnComboBox,self.ComboBox)
        self.Bind (wx.EVT_COMBOBOX,self.OnComboBox,self.ComboBox)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnTextCtrl,self.TextCtrl)
        # Layout
        layout = wx.GridBagSizer(1,1)
        a = wx.ALIGN_CENTRE_VERTICAL
        e = wx.EXPAND
        layout.Add (wx.StaticText(panel,label="ComboBox:"),(0,0),flag=a)
        layout.Add (self.ComboBox,(0,1),flag=a|e)
        layout.Add (wx.StaticText(panel,label="TextCtrl:"),(1,0),flag=a)
        layout.Add (self.TextCtrl,(1,1),flag=a|e)
        # Leave a 5 pixel wide border.
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add (layout,flag=wx.ALL,border=5)
        panel.SetSizer(box)
        panel.Fit()
        self.Fit()
        self.Show()
        # Initialization
        self.timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.refresh,self.timer)
        self.timer.Start(1000,oneShot=True)

    def refresh(self,event=None):
        """Update displayed values"""
        from DB import dbget
        self.ComboBox.Value = dbget("EditableControls_Test.ComboBox")
        self.TextCtrl.Value = dbget("EditableControls_Test.TextCtrl")
        self.timer.Start(1000,oneShot=True)

    def OnComboBox(self,event):
        """ComboxBox was meodified..."""
        debug("ComboBox: '%s'" % self.ComboBox.Value)
        from DB import dbput
        dbput("EditableControls_Test.ComboBox",self.ComboBox.Value)

    def OnTextCtrl(self,event):
        """TextCtrl was modified..."""
        debug("TextCtrl: '%s'" % self.TextCtrl.Value)
        from DB import dbput
        dbput("EditableControls_Test.TextCtrl",self.TextCtrl.Value)

if __name__ == '__main__':
    from pdb import pm
    import logging; logging.basicConfig(level=logging.DEBUG)
    # Needed to initialize WX library
    wx.app = wx.App(redirect=False)
    panel = EditableControls_Test()
    wx.app.MainLoop()
