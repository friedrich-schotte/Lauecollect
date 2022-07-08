#!/usr/bin/env python
"""Show version info
Author: Friedrich Schotte
Date created: 2020-01-30
Date last modified: 2020-02-12
"""
__version__ = "1.1"

import wx
import wx.adv

def About(window):
    """Show panel with additional parameters"""
    info = about_info(window)
    dlg = wx.MessageDialog(window,info,"About",wx.OK|wx.ICON_INFORMATION)
    dlg.CenterOnParent()
    dlg.ShowModal()
    dlg.Destroy()

def about_info(object):
    from os.path import basename
    from inspect import getfile,getmodule
    from os.path import getmtime,exists
    from datetime import datetime
    try: filename = getfile(type(object))
    except: filename = ""
    filename = filename.replace(".pyc",".py")
    if exists(filename): mtime = getmtime(filename)
    else: mtime = 0
    from date_time import date_time
    last_modified = date_time(mtime) if mtime else ""
    try: module_version = getmodule(type(object)).__version__
    except: module_version = ""
    info = basename(filename)
    if module_version: info += " "+module_version
    if last_modified: info += " (%s)" % last_modified
    info += "\n\n"
    docstring = getmodule(type(object)).__doc__
    if docstring: info += docstring.strip("\n")+"\n\n"
    from sys import version as python_version
    info += "Python %s\n" % python_version.split("\n")[0]
    info += "wxPython %s\n" % wx.__version__
    return info

def About2(window):
    """Show panel with additional parameters"""
    # Using "AboutBox" (requires wxPython 2.8)
    from os.path import basename
    from inspect import getfile,getmodule
    from os.path import getmtime
    from datetime import datetime
    try: filename = getfile(type(window))
    except: filename = ""
    module_name = basename(filename)
    try: module_version = getmodule(type(window)).__version__
    except: module_version = ""
    desc = ""
    docstring = getmodule(type(window)).__doc__
    if docstring: desc += docstring.strip("\n")+"\n\n"
    from sys import version as python_version
    desc += "Python %s\n" % python_version.split("\n")[0]
    desc += "wxPython %s\n" % wx.__version__

    info = wx.adv.AboutDialogInfo()
    info.Name = module_name
    info.Version = module_version
    info.Copyright = ""
    info.Description = desc
    url = "https://femto.niddk.nih.gov/APS/Instrumentation/Software/Lauecollect"
    info.WebSite = (url, "Home Page")
    info.Developers = []
    info.License = ""
    wx.adv.AboutBox(info)        

if __name__ == "__main__":
    from pdb import pm # for debugging
    import logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(module)s, line %(lineno)d: %(funcName)s: %(message)s",
    )

    class Window(wx.Frame): pass
    
    app = wx.App()
    window = Window()
    About(window)
    app.MainLoop()
