#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2022-02-02
Date last modified: 2022-02-03
Revision comment:
"""
__version__ = "1.0"

import wx


class Camera_Viewer_Ensemble_Motors_Panel(wx.Panel):
    def __init__(self, parent):
        from EditableControls import ComboBox, TextCtrl
        super().__init__(parent)

        left = wx.ArtProvider.GetBitmap(wx.ART_GO_BACK)
        right = wx.ArtProvider.GetBitmap(wx.ART_GO_FORWARD)
        up = wx.ArtProvider.GetBitmap(wx.ART_GO_UP)
        down = wx.ArtProvider.GetBitmap(wx.ART_GO_DOWN)

        style = wx.TE_PROCESS_ENTER
        choices = ["500 um","200 um","100 um","50 um","20 um","10 um","5 um",
            "2 um","1 um"]
        self.StepSize = ComboBox(self,style=style,choices=choices,
            size=(80,-1))

        self.TranslateFromCamera = wx.BitmapButton(self,bitmap=left)
        self.TranslateTowardCamera = wx.BitmapButton(self,bitmap=right)

        self.TranslateHLeft = wx.BitmapButton(self,bitmap=left)
        self.TranslateHRight = wx.BitmapButton(self,bitmap=right)

        self.TranslateVUp = wx.BitmapButton(self,bitmap=up)
        self.TranslateVDown = wx.BitmapButton (self,bitmap=down)

        # Layout
        grid = wx.GridBagSizer (hgap=0,vgap=0)

        label = wx.StaticText(self,label="Step:")
        grid.Add (label,(1,0),flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add (self.StepSize,(1,1),flag=wx.ALIGN_CENTER)

        label = wx.StaticText(self,label="Focus:")
        grid.Add (label,(2,0),flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add (self.TranslateFromCamera,flag=wx.ALIGN_CENTER)
        hbox.Add (self.TranslateTowardCamera,flag=wx.ALIGN_CENTER)
        grid.Add (hbox,(2,1),flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)

        grid.Add (self.TranslateHLeft,(1,0+3),flag=wx.ALIGN_CENTER)
        grid.Add (self.TranslateHRight,(1,2+3),flag=wx.ALIGN_CENTER)
        grid.Add (self.TranslateVUp,(0,1+3),flag=wx.ALIGN_CENTER)
        grid.Add (self.TranslateVDown,(2,1+3),flag=wx.ALIGN_CENTER)
