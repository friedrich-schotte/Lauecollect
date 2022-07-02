#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2020-09-22
Date last modified: 2020-09-22
Revision comment:
"""
__version__ = "1.0"

from logging import debug, info, warning, error
import wx


class Directory_Browse_Control(wx.Panel):
    def __init__(self, parent, *args, **kwargs):
        size = kwargs.pop("size",(-1,-1))
        wx.Panel.__init__(self, parent, size=size)

        # Controls
        from EditableControls import TextCtrl
        self.control = TextCtrl(self,require_enter=False, *args, **kwargs)
        # Needed for wx.Button on MacOS, because Position defaults to 5,3:
        self.control.Position = (0,0) 
        self.button = wx.Button(self,label="Browse...")

        # Callbacks
        self.Bind(wx.EVT_BUTTON,self.OnBrowse,self.button)
        self.Bind(wx.EVT_TEXT_ENTER,self.OnEnter,self.control)

        # Layout
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.control,proportion=1)
        sizer.Add(self.button,proportion=0)
        self.Sizer = sizer
        self.Fit()

    def GetValue(self):
        return self.control.Value
    def SetValue(self, value):
        self.control.Value = value
    Value = property(GetValue, SetValue)

    def OnEnter(self,event):
        debug("Received event %s" % event_repr(event))
        info("User entered %r" % self.Value)
        self.generate_event()

    def OnBrowse(self,event):
        pathname = str(self.control.Value)
        from os.path import exists,dirname
        while pathname and not exists(pathname): pathname = dirname(pathname)
        dlg = wx.DirDialog(self,"Choose a directory:",style=wx.DD_DEFAULT_STYLE)
        # ShowModal pops up a dialog box and returns control only after the user
        # has selects OK or Cancel.
        dlg.Path = pathname
        if dlg.ShowModal() == wx.ID_OK:
            from normpath import normpath
            value = normpath(str(dlg.Path))
            self.Value = value
            info("User selected %r" % self.Value)
            self.generate_event()
        dlg.Destroy()

    def generate_event(self):
        event = wx.PyCommandEvent(wx.EVT_TEXT_ENTER.typeId, self.Id)
        event.SetString(self.Value)
        debug("Generating event %s" % event_repr(event))
        wx.PostEvent(self.EventHandler, event)


def event_repr(event):
    name = type(event).__name__
    return f'{name}(String={event.String!r})'


if __name__ == '__main__':
    from pdb import pm
    import logging
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)


    app = wx.GetApp() if wx.GetApp() else wx.App()
    frame = wx.Frame(None)
    self = Directory_Browse_Control(frame, size=(500,-1))
    self.Enabled = True
    frame.Fit()
    frame.Show()
    app.MainLoop()
