#!/usr/bin/env python
"""Control panel for Lecroy Oscilloscope
Author: Friedrich Schotte
Date created: 2018-10-26
Date last modified: 2018-03-22
"""
__version__ = "1.6" # auto_acquire

from logging import debug,info,warn,error
import wx
from instrumentation import * # passed on in "globals()"

class Scope_Panel(wx.Frame):
    """Control panel for Lecroy Oscilloscope"""
    name = "Scope_Panel"
    icon = "Tool"
    
    def __init__(self,parent=None,scope_name="xray_scope"):
        wx.Frame.__init__(self,parent=parent)

        self.scope_name = scope_name

        self.update()
        self.Show()

        # Refresh
        self.timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.OnTimer,self.timer)
        self.timer.Start(5000,oneShot=True)

    @property
    def scope(self):
        scope = eval(self.scope_name)
        return scope

    @property
    def title(self):
        title = self.scope_name
        title = title.replace("xray","X-Ray")
        title = title.replace("_"," ")
        title = title.title()
        return title

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
        try: self.update_controls()
        except Exception,msg:
            error("%s" % msg)
            import traceback
            traceback.print_exc()
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
        # Controls and Layout
        panel = wx.Panel(self)
        from EditableControls import ComboBox,TextCtrl,Choice
        from Controls import Control
        from BeamProfile_window import BeamProfile

        flag = wx.ALIGN_CENTRE_HORIZONTAL|wx.ALL
        border = 2
        l = wx.ALIGN_LEFT; r = wx.ALIGN_RIGHT; cv = wx.ALIGN_CENTER_VERTICAL
        a = wx.ALL; e = wx.EXPAND; c = wx.ALIGN_CENTER

        frame = wx.BoxSizer()
        panel.SetSizer(frame)
        
        layout = wx.BoxSizer(wx.VERTICAL)
        frame.Add(layout,flag=e|a,border=10,proportion=1)

        layout_flag = wx.ALIGN_CENTRE|wx.ALL
        border = 0
        width,height = 220,25
        
        control = Control(panel,type=wx.ComboBox,
            globals=globals(),
            locals=locals(),
            name=self.name+".setup",
            size=(width,height),
            style=wx.ALIGN_CENTER_HORIZONTAL,
        )
        layout.Add(control,flag=layout_flag,border=border)

        control = Control(panel,type=wx.ToggleButton,
            globals=globals(),
            locals=locals(),
            name=self.name+".recall",
            label="Recall",
            size=(width,height),
        )
        layout.Add(control,flag=layout_flag,border=border)

        control = Control(panel,type=wx.ToggleButton,
            globals=globals(),
            locals=locals(),
            name=self.name+".save",
            label="Save",
            size=(width,height),
        )
        layout.Add(control,flag=layout_flag,border=border)

        control = Control(panel,type=wx.StaticText,
            globals=globals(),
            locals=locals(),
            name=self.name+".trace_directory_size",
            size=(width,height),
            style=wx.ALIGN_CENTER_HORIZONTAL,
        )
        layout.Add(control,flag=layout_flag,border=border)

        control = Control(panel,type=wx.ToggleButton,
            globals=globals(),
            locals=locals(),
            name=self.name+".emptying_trace_directory",
            size=(width,height),
        )
        layout.Add(control,flag=layout_flag,border=border)
        
        control = Control(panel,type=wx.ToggleButton,
            globals=globals(),
            locals=locals(),
            name=self.name+".acquiring_waveforms",
            label="Auto Save",
            size=(width,height),
        )
        layout.Add(control,flag=layout_flag,border=border)

        control = Control(panel,type=wx.CheckBox,
            globals=globals(),
            locals=locals(),
            name=self.name+".auto_acquire",
            label="Auto Record Traces",
            size=(width,height),
            style=wx.ALIGN_CENTER_HORIZONTAL,
        )
        layout.Add(control,flag=layout_flag,border=border)

        control = Control(panel,type=wx.StaticText,
            globals=globals(),
            locals=locals(),
            name=self.name+".trace_count",
            size=(width,height),
            style=wx.ALIGN_CENTER_HORIZONTAL,
        )
        layout.Add(control,flag=layout_flag,border=border)

        control = Control(panel,type=wx.StaticText,
            globals=globals(),
            locals=locals(),
            name=self.name+".trigger_count",
            size=(width,height),
            style=wx.ALIGN_CENTER_HORIZONTAL,
        )
        layout.Add(control,flag=layout_flag,border=border)

        control = Control(panel,type=wx.StaticText,
            globals=globals(),
            locals=locals(),
            name=self.name+".trace_count_offset",
            size=(width,height),
            style=wx.ALIGN_CENTER_HORIZONTAL,
        )
        layout.Add(control,flag=layout_flag,border=border)

        control = Control(panel,type=wx.StaticText,
            globals=globals(),
            locals=locals(),
            name=self.name+".timing_jitter",
            size=(width,height),
            style=wx.ALIGN_CENTER_HORIZONTAL,
        )
        layout.Add(control,flag=layout_flag,border=border)

        control = Control(panel,type=wx.StaticText,
            globals=globals(),
            locals=locals(),
            name=self.name+".timing_offset",
            size=(width,height),
            style=wx.ALIGN_CENTER_HORIZONTAL,
        )
        layout.Add(control,flag=layout_flag,border=border)

        control = Control(panel,type=wx.ToggleButton,
            globals=globals(),
            locals=locals(),
            name=self.name+".trace_count_synchronized",
            label="Synchronized",
            size=(width,height),
        )
        layout.Add(control,flag=layout_flag,border=border)

        control = Control(panel,type=wx.CheckBox,
            globals=globals(),
            locals=locals(),
            name=self.name+".auto_synchronize",
            label="Auto Synchronize",
            size=(width,height),
            style=wx.ALIGN_CENTER_HORIZONTAL,
        )
        layout.Add(control,flag=layout_flag,border=border)

        control = Control(panel,type=wx.ToggleButton,
            globals=globals(),
            locals=locals(),
            name=self.name+".trace_acquisition_running",
            label="Data Collection Running",
            size=(width,height),
        )
        layout.Add(control,flag=layout_flag,border=border)

        panel.Fit()
        return panel


if __name__ == '__main__':
    from pdb import pm
    import logging; from tempfile import gettempdir
    logfile = gettempdir()+"/Scope_Panel.log"
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s",
        filename=logfile,
    )

    from sys import argv
    scope_name = "xray_scope"
    ##scope_name = "laser_scope"
    if len(argv) >= 2: scope_name = argv[1]

    import autoreload
    # Needed to initialize WX library
    wx.app = wx.App(redirect=False)
    panel = Scope_Panel(scope_name=scope_name)
    wx.app.MainLoop()
