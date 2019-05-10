"""Application Icon
author: Friedrich Schotte
Date created: Mar 28, 2017
Date last modified: 2019-03-20
"""
__version__ = "1.1.1" # Issue: "You should never have more than one dock icon!"
import wx
from logging import debug,info,warn,error
import traceback

def SetIcon(window,name,tooltip=""):
    """Set application icon
    window: wx.Frame object
    name: e.g. "Checklist"
    """
    filename = ""
    icon = None
    if name:
        from module_dir import module_dir
        from os.path import exists
        basename = module_dir(SetIcon)+"/icons/%s" % name
        if exists(basename+".ico"): filename = basename+".ico"
        elif exists(basename+".png"): filename = basename+".png"
        else: warn("%r.{ico,png}: neither file found" % basename)
    if filename:
        try: icon = wx.Icon(filename)
        except Exception,msg: warn("%s: %s" % (filename,msg))
    if icon:
        if window: window.Icon = icon
        try:
            if hasattr(wx,"TaskBarIcon"):
                if not hasattr(wx,"taskbar_icon"):
                    wx.taskbar_icon = wx.TaskBarIcon(iconType=wx.TBI_DOCK)
                wx.taskbar_icon.SetIcon(icon,tooltip)
        except Exception,msg: warn("%s\n%s" % (msg,traceback.format_exc()))

if __name__ == "__main__":
    # Needed to initialize WX library
    wx.app = wx.App(redirect=False)
    window = wx.Frame(None)
    name = "Tool"
    tooltip = "Icon"
    SetIcon(window,name,tooltip)
    window.Show()
    wx.app.MainLoop()
