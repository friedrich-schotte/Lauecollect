"""
Persistent property of WX GUI applications that are specific for each computer,
not global line "persistent_property"

Example:
A window that remembers its size.

    app = wx.App()

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
    app.MainLoop()
    
Author: Friedrich Schotte
Date created: 2017-11-20
Date last modified: 2020-10-09
Revision comment: Fixed: Issue: NameError: name 'wx' is not defined
"""
__version__ = "1.1.7"

from logging import debug, info, warning, error

import wx


def setting(name, default_value=0.0):
    """A persistent property of a class"""

    def class_name(self):
        if "." in name:
            class_name = name.split(".")[0]
        else:
            class_name = getattr(self, "name", self.__class__.__name__)
        return class_name

    def my_name():
        if "." in name:
            my_name = name.split(".")[1]
        else:
            my_name = name
        return my_name

    def fget(self):
        from time import time
        if not hasattr(self, "__config__") or getattr(self.__config__, "last_read", 0) < time() - 1:
            self.__config__ = wx.Config(class_name(self))
            self.__config__.last_read = time()
        value = self.__config__.Read(my_name())
        # debug("self.__config__.Read(%r): %r" % (my_name(),value))
        dtype = type(default_value)
        from numpy import nan, inf  # for eval
        try:
            value = dtype(eval(value))
        except:
            value = default_value
        # debug("%s.%s = %r" % (class_name(self),my_name(),value))
        return value

    def fset(self, value):
        # debug("%s.%s = %r" % (class_name(self),my_name(),value))
        from time import time
        if not hasattr(self, "__config__"):
            self.__config__ = wx.Config(class_name(self))
            self.__config__.last_read = time()
        # debug("self.__config__.Write(%r,%r)" % (my_name(),repr(value)))
        self.__config__.Write(my_name(), repr(value))
        self.__config__.Flush()

    return property(fget, fset)


if __name__ == "__main__":
    from pdb import pm  # for debugging
    import logging  # for debugging

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s: %(message)s",
    )

    import wx

    app = wx.App()

    # config = wx.Config("TimingPanel")

    class Servers_Panel(object):
        name = "Servers_Panel"
        CustomView = setting("CustomView", list(range(0, 20)))


    panel = Servers_Panel()

    # print('config.Read("refresh_period")')
    # print('config.Write("refresh_period","1.0"); config.Flush()')
    # print('config.Write("refresh_period","2.0"); config.Flush()')
    print('panel.CustomView')
    print('panel.CustomView = [0, 1, 2, 3, 9, 11, 15, 16, 18, 19, 23, 24, 25, 26]')
    print('panel.CustomView = range(0,20)')
