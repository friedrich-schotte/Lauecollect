"""Customized version of the WX text control
Friedrich Schotte, 10 Mar 2011 - 29 Sep 2013"""

import wx

__version__ = "1.0.2"

class ComboBox (wx.ComboBox):
    "A customized Combo Box control"
    def __init__ (self,*args,**kwargs):
        # Work-around for a bug in the Mac OS X version of wxPython 2.9.1.1
        # (osx-cocoa-unicode)
        # wx.TE_PROCESS_ENTER make it either crash when  hitting Enter key
        # of when selecting an item from the drop down menu.
        if "style" in kwargs: kwargs["style"] &= ~wx.TE_PROCESS_ENTER
        wx.ComboBox.__init__(self,*args,**kwargs)
        self.NormalBackgroundColour = self.BackgroundColour
        self.EditedBackgroundColour = wx.Colour(255,255,220) # pale yellow
        self.CachedValue = self.Value
        self.Bind (wx.EVT_CHAR,self.OnType)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnter)
        self.Bind (wx.EVT_SET_FOCUS,self.OnReceiveFocus)
        self.Bind (wx.EVT_KILL_FOCUS,self.OnLooseFocus)

    def OnType(self,event):
        """Called when any text is typed"""
        bkg = self.BackgroundColour
        if event.KeyCode == wx.WXK_ESCAPE:
            # On ESC, cancel the editing and replace the original text.
            self.BackgroundColour = self.NormalBackgroundColour
            wx.ComboBox.SetValue(self,self.CachedValue)
        elif event.KeyCode == wx.WXK_TAB:
            # Tab navigates between controls shifting the keyboard focus.
            self.BackgroundColour = self.NormalBackgroundColour
            wx.ComboBox.SetValue(self,self.CachedValue)
        else:
            # Enter 'editing mode' by changing the background color.
            self.BackgroundColour = self.EditedBackgroundColour
        if self.BackgroundColour != bkg: self.Refresh()
        # Pass this event on to further event handlers bound to this event.
        # Otherwise, the typed text does not appear in the window.
        event.Skip()
        
    def OnEnter(self,event):
        """Called when Enter is pressed"""
        # Pressing Enter makes the edited text available as "Value" of
        # the control and exits "editing mode".
        bkg = self.BackgroundColour
        self.BackgroundColour = self.NormalBackgroundColour
        if self.BackgroundColour != bkg: self.Refresh()
        self.CachedValue = self.Value
        # Pass this event on to further event handlers bound to this event.
        # Otherwise, the typed text does not appear in the window.
        event.Skip()

    def OnReceiveFocus(self,event):
        """Called when window receives keyboard focus"""
        # Pass this event on to further event handlers bound to this event.
        # Otherwise, the typed text does not appear in the window.
        event.Skip()

    def OnLooseFocus(self,event):
        """Called when window looses keyboard focus"""
        # Cancel the editing and replace the original text.
        bkg = self.BackgroundColour
        self.BackgroundColour = self.NormalBackgroundColour
        if self.BackgroundColour != bkg: self.Refresh()
        wx.ComboBox.SetValue(self,self.CachedValue)
        # Pass this event on to further event handlers bound to this event.
        # Otherwise, the typed text does not appear in the window.
        event.Skip()

    def GetValue(self):
        if self.BackgroundColour == self.NormalBackgroundColour: 
            return wx.ComboBox.GetValue(self)
        else: return self.CachedValue
    def SetValue(self,value):
        self.CachedValue = value
        if self.BackgroundColour == self.NormalBackgroundColour:
            # Keep the current cursor position by no changing the updating
            # the control unless the text really changed.
            if wx.ComboBox.GetValue(self) != value:
                wx.ComboBox.SetValue(self,value)
    Value = property(GetValue,SetValue)

