#!/usr/bin/env python
"""Application Icon
author: Friedrich Schotte
Date created: 2017-03-28
Date last modified: 2020-00-23
Revision comment: Added: Icon
"""
__version__ = "1.2"

from logging import debug, info, warning, error
import traceback

import wx


def SetIcon(window, name, tooltip=""):
    """Set application icon
    window: wx.Frame object
    name: e.g. "Checklist"
    """
    icon = Icon(name)
    if icon:
        if window: window.Icon = icon
        try:
            if hasattr(wx, "TaskBarIcon"):
                if not hasattr(wx, "taskbar_icon"):
                    wx.taskbar_icon = wx.TaskBarIcon(iconType=wx.TBI_DOCK)
                wx.taskbar_icon.SetIcon(icon, tooltip)
        except Exception as msg:
            warning("%s\n%s" % (msg, traceback.format_exc()))


def Icon(name):
    icon = None
    filename = icon_filename(name)
    if filename:
        try:
            icon = wx.Icon(filename)
        except Exception as msg:
            warning("%s: %s" % (filename, msg))
    return icon


def icon_filename(name):
    filename = ""
    if name:
        from module_dir import module_dir
        from os.path import exists
        basename = module_dir(SetIcon) + "/icons/%s" % name
        if exists(basename + ".ico"):
            filename = basename + ".ico"
        elif exists(basename + ".png"):
            filename = basename + ".png"
        else:
            warning("%r.{ico,png}: neither file found" % basename)
    return filename


if __name__ == "__main__":

    app = wx.App()
    window = wx.Frame(None)
    name = "Tool"
    tooltip = "Icon"
    SetIcon(window, name, tooltip)
    window.Show()
    app.MainLoop()
