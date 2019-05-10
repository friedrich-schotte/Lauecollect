#!/usr/bin/env python
"""Needed for wxPython 4.0 for backward compatibility 3.0
Author: Friedrich Schotte
Date created: 2018-03-09
Date last modified: 2018-03-21
"""
__version__ = "1.0" 
import wx
# When trying to access a closed window object 3.0 raised a PyDeadObjectError
# exception. 4.0 raises RuntimeError instead.
if not hasattr(wx,"PyDeadObjectError"): wx.PyDeadObjectError = RuntimeError

# wximage = wx.EmptyImage(self.ImageWidth,self.ImageHeight)
# "Call to deprecated item EmptyImage. Use class wx.Image instead."
if wx.__version__.startswith("4"): wx.EmptyImage = wx.Image

# "Call to deprecated item BitmapFromImage. Use class wx.Bitmap instead."
if wx.__version__.startswith("4"): wx.BitmapFromImage = wx.Bitmap

# self.SetCursor(wx.StockCursor(wx.CURSOR_SIZING))
# "wxPyDeprecationWarning: Using deprecated class. Use Cursor instead."
if wx.__version__.startswith("4"): wx.StockCursor = wx.Cursor

# self.Bind(wx.grid.EVT_GRID_CELL_CHANGE,self.apply)
# AttributeError: 'module' object has no attribute 'EVT_GRID_CELL_CHANGE'
import wx.grid
if not hasattr(wx.grid,"EVT_GRID_CELL_CHANGE"):
    wx.grid.EVT_GRID_CELL_CHANGE = wx.grid.EVT_GRID_CELL_CHANGED

# buttons.AddSpacer((5,5))
# TypeError: BoxSizer.AddSpacer(): argument 1 has unexpected type 'tuple'
if wx.__version__.startswith("4"):
    wx.BoxSizer.AddSpacer_v4 = wx.BoxSizer.AddSpacer
    def AddSpacer(self,size,*args,**kwargs):
        if type(size) == tuple: size = size[0]
        return wx.BoxSizer.AddSpacer_v4(self,size,*args,**kwargs)
    wx.BoxSizer.AddSpacer = AddSpacer

# ComboBox(self,style=wx.CB_DROPDOWN|wx.PROCESS_ENTER)
# AttributeError: 'module' object has no attribute 'PROCESS_ENTER'
if not hasattr(wx,"PROCESS_ENTER"): wx.PROCESS_ENTER = wx.TE_PROCESS_ENTER

# dlg = wx.FileDialog(self,"Load Settings",style=wx.OPEN,
# AttributeError: 'module' object has no attribute 'OPEN'
if not hasattr(wx,"OPEN"): wx.OPEN = wx.FD_OPEN
# wx.FileDialog(self,"Save Settings As",
#   style=wx.SAVE|wx.OVERWRITE_PROMPT,
# AttributeError: 'module' object has no attribute 'OVERWRITE_PROMPT'
if not hasattr(wx,"SAVE"): wx.SAVE = wx.FD_SAVE
if not hasattr(wx,"OVERWRITE_PROMPT"): wx.OVERWRITE_PROMPT = wx.FD_OVERWRITE_PROMPT

# event.Checked()
# AttributeError: 'CommandEvent' object has no attribute 'Checked'
if not hasattr(wx.CommandEvent,"Checked"):
    def Checked(self): return wx.CommandEvent.IsChecked(self)
    wx.CommandEvent.Checked = Checked
       
