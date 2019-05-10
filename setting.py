"""
Persistent property of WX GUI applications that are specific for each computer,
not global line "persistent_property"

Example:
A window that remembers its size.

    wx.app = wx.App(redirect=False)

    class Window(wx.Frame):
        size = setting("size",(400,250))
        def __init__(self):
            wx.Frame.__init__(self,parent=None,size=self.size)
            self.Bind(wx.EVT_SIZE,self.OnResize)
            self.Layout()
            self.Show()
        def OnResize(self,event):
            event.Skip()
            self.size = tuple(self.Size)
    win = Window()
    wx.app.MainLoop()
    
Author: Friedrich Schotte
Date created: 2017-11-20
Date last modified: 2018-12-04
"""
__version__ = "1.1" # name: accepting "TimingPanel.refresh_period"

import wx
from logging import debug,info,warn,error

def setting(name,default_value=0.0):
    """A presistent property of a class"""
    def class_name(self):
        if "." in name: class_name = name.split(".")[0]
        else: class_name = getattr(self,"name",self.__class__.__name__)
        return class_name
    def my_name():
        if "." in name: my_name = name.split(".")[1]
        else: my_name = name
        return my_name
        
    def get(self):
        from time import time
        if not hasattr(self,"config") or self.config.last_read < time()-1: 
            self.config = wx.Config(class_name(self))
            self.config.last_read = time()
        value = self.config.Read(my_name())
        dtype = type(default_value)
        from numpy import nan,inf # for eval
        try: value = dtype(eval(value))
        except: value = default_value
        return value
    def set(self,value):
        debug("%s.%s = %r" % (class_name(self),my_name(),value))
        from time import time
        if not hasattr(self,"config"):
            self.config = wx.Config(class_name(self))
            self.config.last_read = time()
        self.config.Write(my_name(),repr(value))
        self.config.Flush()
    return property(get,set)


if __name__ == "__main__":
    from pdb import pm # for debugging
    import logging # for debugging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s: %(message)s",
    )

    import wx
    app = wx.App(redirect=False) 
    ##config = wx.Config("TimingPanel")
     
    class Timing_Setup_Panel(object):
        refresh_period = setting("TimingPanel.refresh_period",1.0)
    TimingPanel = Timing_Setup_Panel()
    self = TimingPanel # for debugging

    ##print('config.Read("refresh_period")')
    ##print('config.Write("refresh_period","1.0"); config.Flush()')
    ##print('config.Write("refresh_period","2.0"); config.Flush()')
    print('TimingPanel.refresh_period')
    print('TimingPanel.refresh_period = 1.0')
    print('TimingPanel.refresh_period = 2.0')
