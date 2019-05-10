"""Customized version of the WX text control (wx.TextCtrl)
Friedrich Schotte, 10 Mar 2011 - 15 Nov 2013"""

__version__ = "1.0.2"
import wx
from logging import debug

class TextCtrl (wx.TextCtrl):
    """A customized editable text control"""
    def __init__ (self,*args,**kwargs):
        wx.TextCtrl.__init__(self,*args,**kwargs)
        self.NormalForegroundColour = self.ForegroundColour
        self.NormalBackgroundColour = self.BackgroundColour
        self.EditedForegroundColour = wx.Colour(80,40,0) # reddish brown
        self.EditedBackgroundColour = wx.Colour(255,255,220) # pale yellow
        self.CachedValue = wx.TextCtrl.GetValue(self)
        self.Bind (wx.EVT_KEY_DOWN,self.OnKey)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnter)
        self.Bind (wx.EVT_SET_FOCUS,self.OnReceiveFocus)
        self.Bind (wx.EVT_KILL_FOCUS,self.OnLooseFocus)
        
    def OnKey(self,event):
        """Called when any text is typed"""
        debug("OnKey: KeyCode %s" % (event.KeyCode))
        debug("BackgroundColour %r" % self.BackgroundColour)
        bkg = self.BackgroundColour
        fg = self.ForegroundColour
        if event.KeyCode == wx.WXK_ESCAPE:
            debug("OnKey: ESC")
            # On ESC, cancel the editing and replace the original text.
            self.ForegroundColour = self.NormalForegroundColour
            self.BackgroundColour = self.NormalBackgroundColour
            wx.TextCtrl.SetValue(self,self.CachedValue)
        elif event.KeyCode == wx.WXK_TAB:
            debug("OnKey: TAB")
            # Tab navigates between controls shifting the keyboard focus.
            self.ForegroundColour = self.NormalForegroundColour
            self.BackgroundColour = self.NormalBackgroundColour
            wx.TextCtrl.SetValue(self,self.CachedValue)
        elif event.KeyCode == wx.WXK_RETURN:
            debug("OnKey: Enter")
            debug("Value = %r" % wx.TextCtrl.GetValue(self))
            # Pressing Enter makes the edited text available as "Value" of
            # the control and exits "editing mode".
            self.ForegroundColour = self.NormalForegroundColour
            self.BackgroundColour = self.NormalBackgroundColour
            self.CachedValue = wx.TextCtrl.GetValue(self)
        else:
            debug("OnKey: Enter 'editing mode'")
            # Enter 'editing mode' by changing the background color.
            self.ForegroundColour = self.EditedForegroundColour
            self.BackgroundColour = self.EditedBackgroundColour
        if self.BackgroundColour != bkg or self.ForegroundColour != fg:
            debug("OnKey: Refresh")
            self.Refresh()
        # Pass this event on to further event handlers bound to this event.
        # Otherwise, the typed text does not appear in the window.
        event.Skip()

    def OnEnter(self,event):
        """Called when Enter is pressed"""
        debug("OnEnter")
        debug("BackgroundColour %r" % self.BackgroundColour)
        debug("Value = %r" % wx.TextCtrl.GetValue(self))
        has_focus = self.HasFocus() if hasattr(self,"HasFocus") else False
        debug("HasFocus? %r" % has_focus)
        # Pass this event on to further event handlers bound to this event.
        # Otherwise, the typed text does not appear in the window.
        if has_focus: event.Skip()

    def OnReceiveFocus(self,event):
        """Called when window receives keyboard focus"""
        debug("Received focus")
        debug("BackgroundColour %r" % self.BackgroundColour)
        # Pass this event on to further event handlers bound to this event.
        # Otherwise, the typed text does not appear in the window.
        event.Skip()

    def OnLooseFocus(self,event):
        """Called when window looses keyboard focus"""
        debug("Lost focus")
        debug("BackgroundColour %r" % self.BackgroundColour)
        # Cancel the editing and replace the original text.
        bkg = self.BackgroundColour
        fg = self.ForegroundColour
        self.BackgroundColour = self.NormalBackgroundColour
        if self.BackgroundColour != bkg or self.ForegroundColour != fg:
            debug("Refresh")
            self.Refresh()
        wx.TextCtrl.SetValue(self,self.CachedValue)
        # Pass this event on to further event handlers bound to this event.
        # Otherwise, the typed text does not appear in the window.
        event.Skip()

    def GetValue(self):
        if self.ForegroundColour == self.NormalForegroundColour and \
            self.BackgroundColour == self.NormalBackgroundColour:
            value = wx.TextCtrl.GetValue(self)
        else: value = self.CachedValue
        debug("GetValue %r" % value)
        return value
    def SetValue(self,value):
        ##debug("SetValue %r" % value)
        self.CachedValue = value
        if self.ForegroundColour == self.NormalForegroundColour and \
            self.BackgroundColour == self.NormalBackgroundColour:
            # Keep the current cursor position by no changing the updating
            # the control unless the text really changed.
            if wx.TextCtrl.GetValue(self) != value:
                wx.TextCtrl.SetValue(self,value)
    Value = property(GetValue,SetValue)


##def debug(x): print(x) # for debugging

if __name__ == "__main__": # for testing
    import logging
    ##logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s")


