#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2019-03-20
Date last modified:  2019-03-26
"""
__version__ = "1.0" # cleanup

from logging import debug,info,warn,error
from traceback import format_exc

import wx
from dataset_check import dataset # passed on in "globals()"

class Dataset_Check_Panel(wx.Frame):
    """Control panel for Lecroy Oscilloscope"""
    title = "Dataset Check"
    name = "Dataset_Check_Panel"
    icon = "Tool"
    
    def __init__(self,parent=None):
        wx.Frame.__init__(self,parent=parent)

        self.update()
        self.Show()

        # Refresh
        self.timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.OnTimer,self.timer)
        self.timer.Start(5000,oneShot=True)

    def update(self):
        self.Title = self.title
        from Icon import SetIcon
        SetIcon(self,self.icon)
        panel = self.ControlPanel
        if hasattr(self,"panel"): self.panel.Destroy()
        self.panel = panel
        self.Fit()

    def OnTimer(self,event):
        """Perform periodic updates"""
        update_globals()        
        try: self.update_controls()
        except Exception,msg: error("%s\n%s" % (msg,format_exc()))
        self.timer.Start(5000,oneShot=True)

    def update_controls(self):
        if self.code_outdated:
            self.update_code()
            self.update()

    @property
    def code_outdated(self): 
        if not hasattr(self,"timestamp"): self.timestamp = self.module_timestamp
        outdated = self.module_timestamp != self.timestamp
        return outdated

    @property
    def module_timestamp(self):
        from inspect import getfile
        from os.path import getmtime,basename
        filename = getfile(self.__class__).replace(".pyc",".py")
        ##debug("module: %s" % basename(filename))
        timestamp = getmtime(filename)
        return timestamp
        
    def update_code(self):
        from inspect import getfile
        from os.path import getmtime,basename
        filename = getfile(self.__class__).replace(".pyc",".py")
        ##debug("module: %s" % basename(filename))
        module_name = basename(filename).replace(".pyc",".py").replace(".py","")
        module = __import__(module_name)
        reload(module)
        self.timestamp = self.module_timestamp
        debug("Reloaded module %r" % module.__name__)
        debug("Updating class of %r instance" % self.__class__.__name__)
        self.__class__ = getattr(module,self.__class__.__name__)
            
    @property
    def ControlPanel(self):
        from Controls import Control
        panel = wx.Panel(self)

        frame = wx.BoxSizer()
        panel.Sizer = frame
        
        layout = wx.BoxSizer(wx.VERTICAL)
        frame.Add(layout,flag=wx.EXPAND|wx.ALL,border=10,proportion=1)
        
        control = Control(panel,type=wx.StaticText,
            globals=globals(),
            locals=locals(),
            name=self.name+".report",
            size=(420,160),
        )
        layout.Add(control,flag=wx.ALIGN_CENTRE|wx.ALL)

        panel.Fit()
        return panel


def update_globals():
    global dataset
    try:
        import dataset_check
        reload(dataset_check)
        from dataset_check import dataset
        globals()["dataset"] = dataset
    except Exception,msg: error("%s\n%s" % (msg,format_exc()))


if __name__ == '__main__':
    from pdb import pm
    from redirect import redirect
    redirect("Check_Dataset_Panel")

    import autoreload
    # Needed to initialize WX library
    wx.app = wx.App(redirect=False)
    panel = Dataset_Check_Panel()
    wx.app.MainLoop()
