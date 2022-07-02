"""Author: Friedrich Schotte,
Date created: 2010-12-10
Date last modified: 2020-06-10
Revision comment: line 19, self.OSXDisableAllSmartSubstitutions(): NotImplementedError
"""
__version__ = "1.6.2"

import wx
from logging import debug,info,warn,error

class TextCtrl(wx.TextCtrl):
    """A customized editable text control"""
    def __init__ (self,parent,style=wx.TE_PROCESS_ENTER,require_enter=False,
        *args,**kwargs):
        wx.TextCtrl.__init__(self,parent,style=style,*args,**kwargs)
        # "..." -> Unicode Hoizonal Ellipsis (U+2026)
        # " -> Unicode Character 'LEFT DOUBLE QUOTATION MARK' (U+201C)
        try: self.OSXDisableAllSmartSubstitutions() # requires wx 4
        except: pass

        self.RequireEnter = require_enter # Is Enter is reqired to confirm a change?

        self.Edited = False
        self.NormalBackgroundColour = self.DiplayedBackgroundColour
        self.NormalForegroundColour = wx.TextCtrl.GetForegroundColour(self)
        self.EditedBackgroundColour = wx.Colour(255,255,220) # pale yellow
        self.EditedForegroundColour = wx.Colour(30,30,0) # dark brown
        self.CachedValue = self.DiplayedValue
        self.Bind (wx.EVT_KEY_DOWN,self.OnType)
        ##self.Bind (wx.EVT_TEXT_ENTER,self.OnEnter)
        self.Bind (wx.EVT_SET_FOCUS,self.OnReceiveFocus)
        self.Bind (wx.EVT_KILL_FOCUS,self.OnLooseFocus)

    def OnType(self,event):
        """Called when any text is typed"""
        debug("%s: Key %s" % (self.Name,key_name(event.KeyCode)))
        skip_event = True
        old_bkg = wx.TextCtrl.GetBackgroundColour(self)
        if event.KeyCode == wx.WXK_ESCAPE:
            # On ESC, cancel the editing and replace the original text.
            self.cancel_edit()
        elif event.KeyCode == wx.WXK_TAB:
            # Tab navigates between controls shifting the keyboard focus.
            if self.RequireEnter: self.cancel_edit()
            else:
                changed = (self.DiplayedValue != self.CachedValue)
                self.accept_edit()
        elif event.KeyCode == wx.WXK_RETURN:
            skip_event = False
            changed = (self.DiplayedValue != self.CachedValue)
            self.accept_edit()
            if changed:
                # Make sure the callback for EVT_TEXT_ENTER is called.
                new_event = wx.PyCommandEvent(wx.EVT_TEXT_ENTER.typeId,self.Id)
                wx.PostEvent(self.EventHandler,new_event)
        else:
            # Enter 'editing mode' by changing the background color.
            self.Edited = True
            wx.TextCtrl.SetBackgroundColour(self,self.EditedBackgroundColour)
            wx.TextCtrl.SetForegroundColour(self,self.EditedForegroundColour)
        if wx.TextCtrl.GetBackgroundColour(self) != old_bkg: self.Refresh()
        # Pass this event on to further event handlers bound to this event.
        # Otherwise, the typed text does not appear in the window.
        if skip_event: event.Skip()

    def OnEnter(self,event):
        """Called when Enter is pressed"""
        debug("%s: Enter" % self.Name)
        # Pressing Enter makes the edited text available as "Value" of
        # the control and exits "editing mode".
        self.accept_edit()
        # Pass this event on to further event handlers bound to this event.
        # Otherwise, the typed text does not appear in the window.
        event.Skip()

    def OnReceiveFocus(self,event):
        """Called when window receives keyboard focus"""
        ##debug("%s: Got keyboard focus" % self.Name)
        # Pass this event on to further event handlers bound to this event.
        # Otherwise, the typed text does not appear in the window.
        event.Skip()

    def OnLooseFocus(self,event):
        """Called when window looses keyboard focus"""
        ##debug("%s: Lost keyboard focus" % self.Name)
        # Is Enter is reqired to confirm a change?
        if self.RequireEnter: self.cancel_edit()
        else: self.accept_edit()
        # Pass this event on to further event handlers bound to this event.
        # Otherwise, the typed text does not appear in the window.
        event.Skip()

    def accept_edit(self):
        """Make the edited text available as "Value" of
        the control and exits "editing mode"."""
        old_bkg = wx.TextCtrl.GetBackgroundColour(self)
        wx.TextCtrl.SetBackgroundColour(self,self.NormalBackgroundColour)
        if wx.TextCtrl.GetBackgroundColour(self) != old_bkg: self.Refresh()
        value = self.DiplayedValue
        if value != self.CachedValue:
            debug("%s: Accepting '%s' (replacing '%s')" % (self.Name,value,self.CachedValue))
            # Make sure the callback for EVT_TEXT_ENTER is called.
            new_event = wx.PyCommandEvent(wx.EVT_TEXT_ENTER.typeId,self.Id)
            wx.PostEvent(self.EventHandler,new_event)
        self.CachedValue = value
        self.Edited = False

    def cancel_edit(self):
        """Cancel the editing and replace the original text."""
        debug("%s: Cancelling edit" % self.Name)
        old_bkg = wx.TextCtrl.GetBackgroundColour(self)
        wx.TextCtrl.SetBackgroundColour(self,self.NormalBackgroundColour)
        wx.TextCtrl.SetForegroundColour(self,self.NormalForegroundColour)
        if wx.TextCtrl.GetBackgroundColour(self) != old_bkg: self.Refresh()
        if self.DiplayedValue != self.CachedValue:
            debug("%s: Discarding '%s'" % (self.Name,self.DiplayedValue))
            debug("%s: Reverting to previous value '%s'" %
                (self.Name,self.CachedValue))
        self.DiplayedBackgroundColour = self.NormalBackgroundColour
        self.DiplayedValue = self.CachedValue
        self.Edited = False

    def GetValue(self):
        if not self.Edited: return self.DiplayedValue
        else: return self.CachedValue
    def SetValue(self,value):
        from ASCII import ASCII
        value = ASCII(value)
        self.CachedValue = value
        if not self.Edited:
            # Keep the current cursor position by no changing the updating
            # the control unless the text really changed.
            if self.CachedValue != self.DiplayedValue:
                ##debug("TextCtrl.Value: loading '%s'" % value)
                cursor,end = self.GetSelection()
                self.DiplayedBackgroundColour = self.NormalBackgroundColour
                self.DiplayedValue = self.CachedValue
                self.SetSelection(cursor,end)
    Value = property(GetValue,SetValue)

    def GetDiplayedValue(self):
        from ASCII import ASCII
        return ASCII(wx.TextCtrl.GetValue(self))
    def SetDiplayedValue(self,value):
        from ASCII import ASCII
        wx.TextCtrl.SetValue(self,ASCII(value))
    DiplayedValue = property(GetDiplayedValue,SetDiplayedValue)

    def GetDiplayedBackgroundColour(self):
        return wx.TextCtrl.GetBackgroundColour(self)
    def SetDiplayedBackgroundColour(self,value):
        wx.TextCtrl.SetBackgroundColour(self,value)
    DiplayedBackgroundColour = property(GetDiplayedBackgroundColour,SetDiplayedBackgroundColour)

    def GetForegroundColour(self):
        return wx.TextCtrl.GetForegroundColour(self)
    def SetForegroundColour(self,colour):
        self.NormalForegroundColour = colour
        if not self.Edited:
            wx.TextCtrl.SetForegroundColour(self,colour)
    ForegroundColour = property(GetForegroundColour,SetForegroundColour)

    def GetBackgroundColour(self):
        return wx.TextCtrl.GetBackgroundColour(self)
    def SetBackgroundColour(self,colour):
        if colour != self.NormalBackgroundColour:
            self.NormalBackgroundColour = colour
            if not self.Edited:
                self.DiplayedBackgroundColour = self.NormalBackgroundColour
                self.DiplayedValue = self.CachedValue
                self.Refresh()
    BackgroundColour = property(GetBackgroundColour,SetBackgroundColour)

class ComboBox (wx.ComboBox):
    """A customized Combo Box control"""
    def __init__ (self,parent,style=wx.TE_PROCESS_ENTER,*args,**kwargs):
        wx.ComboBox.__init__(self,parent,style=style,*args,**kwargs)

        self.RequireEnter = False # Is Enter is reqired to confirm a change?
        if "require_enter" in kwargs: self.RequireEnter = kwargs["require_enter"]

        self.Edited = False
        self.NormalBackgroundColour = wx.ComboBox.GetBackgroundColour(self)
        self.NormalForegroundColour = wx.ComboBox.GetForegroundColour(self)
        self.EditedBackgroundColour = wx.Colour(255,255,220) # pale yellow
        self.EditedForegroundColour = wx.Colour(30,30,0) # dark brown
        self.CachedValue = self.Value
        self.Bind (wx.EVT_KEY_DOWN,self.OnType)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnter)
        self.Bind (wx.EVT_SET_FOCUS,self.OnReceiveFocus)
        self.Bind (wx.EVT_KILL_FOCUS,self.OnLooseFocus)

    def OnType(self,event):
        """Called when any text is typed"""
        ##debug("%s: Key %s" % (self.Name,key_name(event.KeyCode)))
        old_bkg = wx.ComboBox.GetBackgroundColour(self)
        if event.KeyCode == wx.WXK_ESCAPE:
            # On ESC, cancel the editing and replace the original text.
            self.cancel_edit()
        elif event.KeyCode == wx.WXK_TAB:
            # Tab navigates between controls shifting the keyboard focus.
            if self.RequireEnter: self.cancel_edit()
            else:
                changed = (wx.ComboBox.GetValue(self) != self.CachedValue)
                self.accept_edit()
                if changed:
                    # Make sure the callback for EVT_COMBOBOX is called.
                    new_event = wx.PyCommandEvent(wx.EVT_COMBOBOX.typeId,self.Id)
                    wx.PostEvent(self.EventHandler,new_event)
        else:
            # Enter 'editing mode' by changing the background color.
            self.Edited = True
            wx.ComboBox.SetBackgroundColour(self,self.EditedBackgroundColour)
            wx.ComboBox.SetForegroundColour(self,self.EditedForegroundColour)
            if wx.ComboBox.GetBackgroundColour(self) != old_bkg: self.Refresh()
        # Pass this event on to further event handlers bound to this event.
        # Otherwise, the typed text does not appear in the window.
        event.Skip()

    def OnEnter(self,event):
        """Called when Enter is pressed"""
        debug("%s: Enter" % self.Name)
        # Pressing Enter makes the edited text available as "Value" of
        # the control and exits "editing mode".
        self.accept_edit()
        # Pass this event on to further event handlers bound to this event.
        # Otherwise, the typed text does not appear in the window.
        event.Skip()

    def OnReceiveFocus(self,event):
        """Called when window receives keyboard focus"""
        ##debug("%s: Got keyboard focus" % self.Name)
        # Pass this event on to further event handlers bound to this event.
        # Otherwise, the typed text does not appear in the window.
        event.Skip()

    def OnLooseFocus(self,event):
        """Called when window looses keyboard focus"""
        ##debug("%s: Lost keyboard focus" % self.Name)
        # Is Enter is reqired to confirm a change?
        if self.RequireEnter: self.cancel_edit()
        else: self.accept_edit()
        # Pass this event on to further event handlers bound to this event.
        # Otherwise, the typed text does not appear in the window.
        event.Skip()

    def accept_edit(self):
        """Make the edited text available as "Value" of
        the control and exits "editing mode"."""
        old_bkg = wx.ComboBox.GetBackgroundColour(self)
        wx.ComboBox.SetBackgroundColour(self,self.NormalBackgroundColour)
        if wx.ComboBox.GetBackgroundColour(self) != old_bkg: self.Refresh()
        value = wx.ComboBox.GetValue(self)
        if value != self.CachedValue:
            debug("%s: Accepting '%s' (replacing '%s')" % (self.Name,value,self.CachedValue))
        self.CachedValue = value
        self.Edited = False

    def cancel_edit(self):
        """Cancel the editing and replace the original text."""
        debug("%s: Cancelling edit" % self.Name)
        old_bkg = wx.ComboBox.GetBackgroundColour(self)
        wx.ComboBox.SetBackgroundColour(self,self.NormalBackgroundColour)
        wx.ComboBox.SetForegroundColour(self,self.NormalForegroundColour)
        if wx.ComboBox.GetBackgroundColour(self) != old_bkg: self.Refresh()
        if wx.ComboBox.GetValue(self) != self.CachedValue:
            debug("%s: Discarding '%s'" % (self.Name,wx.ComboBox.GetValue(self)))
            debug("%s: Reverting to previous value '%s'" % (self.Name,self.CachedValue))
        wx.ComboBox.SetValue(self,self.CachedValue)
        self.Edited = False

    def GetValue(self):
        if not self.Edited: return wx.ComboBox.GetValue(self)
        else: return self.CachedValue
    def SetValue(self,value):
        self.CachedValue = value
        if not self.Edited:
            # Keep the current cursor position by no changing the updating
            # the control unless the text really changed.
            if wx.ComboBox.GetValue(self) != value:
                ##debug("ComboBox.Value: loading '%s'" % value)
                wx.ComboBox.SetValue(self,value)
        ##elif self.CachedValue != value:
        ##    debug("ComboBox.Value: caching '%s'" % value)
    Value = property(GetValue,SetValue)

    def GetItems(self):
        return wx.ComboBox.GetItems(self)
    def SetItems(self,values):
        if values != wx.ComboBox.GetItems(self):
            if not self.Edited:
                value = wx.ComboBox.GetValue(self)
                wx.ComboBox.SetItems(self,values)
                wx.ComboBox.SetValue(self,value)
    Items = property(GetItems,SetItems)
    Choices = Items

    def GetForegroundColour(self):
        return wx.ComboBox.GetForegroundColour(self)
    def SetForegroundColour(self,colour):
        self.NormalForegroundColour = colour
        if not self.Edited:
            wx.ComboBox.SetForegroundColour(self,colour)
    ForegroundColour = property(GetForegroundColour,SetForegroundColour)

    def GetBackgroundColour(self):
        return wx.ComboBox.GetBackgroundColour(self)
    def SetBackgroundColour(self,colour):
        self.NormalBackgroundColour = colour
        if not self.Edited:
            old_bkg = wx.ComboBox.GetBackgroundColour(self)
            wx.ComboBox.SetBackgroundColour(self,colour)
            if wx.ComboBox.GetBackgroundColour(self) != old_bkg: self.Refresh()
    BackgroundColour = property(GetBackgroundColour,SetBackgroundColour)


class Choice (wx.Choice):
    """A customized Choice control
    Enhancements:
    - "Value" property
    - Preseving state when updating choices
    - "Choices" property
    - Every string value is accepted, event when not in list of choices
    """
    def GetValue(self): return self.StringSelection
    def SetValue(self,value): self.StringSelection = value
    Value = property(GetValue,SetValue)

    def GetStringSelection(self): return wx.Choice.GetStringSelection(self)
    def SetStringSelection(self,value):
        # Keep the current state by no changing or updating
        # the control unless the text really changed.
        if wx.Choice.GetStringSelection(self) != value:
            # Make sure that the strign in in the list of selectable items
            if not value in self.Items: self.Items += [value]
            wx.Choice.SetStringSelection(self,value)
    StringSelection = property(GetStringSelection,SetStringSelection)

    def GetItems(self): return wx.Choice.GetItems(self)
    def SetItems(self,values):
        # Keep the current state by no changing or updating
        # the control unless the text really changed.
        if wx.Choice.GetItems(self) != values:
            # Updating the list of choices will, asa  side effect, reset the
            # current selection to the first item.
            # Make sure that the selection is restored.
            value = wx.Choice.GetStringSelection(self)
            if not value in values: values += [value]
            wx.Choice.SetItems(self,values)
            wx.Choice.SetStringSelection(self,value)
    Items = property(GetItems,SetItems)
    Choices = Items


def key_name(key_code): # for debugging
    """The name for a key code"""
    import wx
    names = ",".join([x[4:] for x in dir(wx) if x.startswith("WXK_") and
        getattr(wx,x) == key_code and not x.startswith("WXK_CONTROL_")])
    if names != "": return names
    if 32 <= key_code <= 255: return chr(key_code)
    return "key code %r" % key_code


if __name__ == "__main__": # for testing
    import logging; logging.basicConfig(log_level=logging.DEBUG)

