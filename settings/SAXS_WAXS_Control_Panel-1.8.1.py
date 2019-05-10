#!/usr/bin/env python
"""Control panel for SAXS/WAXS Experiments.
Author: Friedrich Schotte
Date created: 2017-06-12
Date last modified: 2019-02-27
"""
__version__ = "1.8.1" # using wx.lib.buttons 

from logging import debug,info,warn,error
import wx
from SAXS_WAXS_control import SAXS_WAXS_control,control # passed on in "globals()"

class SAXS_WAXS_Control_Panel(wx.Frame):
    """Control panel for SAXS/WAXS Experiments"""
    name = "SAXS_WAXS_Control_Panel"
    def __init__(self):
        wx.Frame.__init__(self,parent=None,title="SAXS-WAXS Control")

        # Icon
        from Icon import SetIcon
        SetIcon(self,"SAXS-WAXS Control")

        self.panel = self.ControlPanel
        self.Fit()
        self.Show()

        # Refresh
        self.timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.OnTimer,self.timer)
        self.timer.Start(5000,oneShot=True)

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
            panel = self.ControlPanel
            self.panel.Destroy()
            self.panel = panel
            self.Fit()

    @property
    def code_outdated(self):
        outdated = False
        try:
            from inspect import getfile
            from os.path import getmtime,basename
            filename = getfile(self.__class__)
            ##debug("module: %s" % filename)
            if self.timestamp == 0: self.timestamp = getmtime(filename)
            outdated = getmtime(filename) != self.timestamp
        except Exception,msg: pass ##debug("code_outdated: %s" % msg)
        return outdated

    def update_code(self):
        from inspect import getfile
        from os.path import getmtime,basename
        filename = getfile(self.__class__)
        ##debug("module: %s" % filename)
        self.timestamp = getmtime(filename)
        module_name = basename(filename).replace(".pyc",".py").replace(".py","")
        module = __import__(module_name)
        reload(module)
        debug("Reloaded module %r" % module.__name__)
        debug("Updating class of %r instance" % self.__class__.__name__)
        self.__class__ = getattr(module,self.__class__.__name__)
            
    timestamp = 0

    @property
    def ControlPanel(self):
        panel = wx.Panel(self)
        from EditableControls import ComboBox,TextCtrl
        from Controls import Control
        ##from wx.lib.buttons import GenButton as Button, GenToggleButton as ToggleButton
        from wx import Button,ToggleButton

        style = wx.ALIGN_CENTRE_HORIZONTAL

        self.Environment = Control(panel,type=ComboBox,
            name="SAXS_WAXS_Control_Panel.Environment",globals=globals(),
            size=(80,-1),choices=["0 (NIH)","1 (APS)","2 (LCLS)"])

        self.XRayDetector = Control(panel,type=wx.StaticText,
            name="SAXS_WAXS_Control_Panel.XRayDetector",globals=globals(),
            size=(170,-1),label="X-Ray Detector",style=style)

        self.XRayDetectorInserted = Control(panel,type=ToggleButton,
            name="SAXS_WAXS_Control_Panel.XRayDetectorInserted",globals=globals(),
            size=(130,-1),label="Insert/Retract")

        self.Home = Control(panel,type=ToggleButton,
            name="SAXS_WAXS_Control_Panel.Home",globals=globals(),
            size=(100,-1),label="Home")
        self.Home.ToolTip = wx.ToolTip("Calibrate motor positions")

        self.ProgramRunning = Control(panel,type=ToggleButton,
            name="SAXS_WAXS_Control_Panel.ProgramRunning",globals=globals(),
            size=(100,-1),label="Running")

        self.GotoSaved = Control(panel,type=Button,
            name="SAXS_WAXS_Control_Panel.GotoSaved",globals=globals(),
            label="Go To Saved Position",
            size=(180,-1))
        self.Save = Control(panel,type=Button,
            name="SAXS_WAXS_Control_Panel.Save",globals=globals(),
            label="Save Current X,Y Positions",size=(180,-1))
        self.Inserted = Control(panel,type=ToggleButton,
            name="SAXS_WAXS_Control_Panel.Inserted",globals=globals(),
            size=(160,-1),label="Insert/Retract")
        
        self.XRayShutter = Control(panel,type=ToggleButton,
            name="SAXS_WAXS_Control_Panel.XRayShutter",globals=globals(),
            size=(60,-1),label="Disabled")
        self.XRayShutterAutoOpen = Control(panel,type=wx.CheckBox,
            name="SAXS_WAXS_Control_Panel.XRayShutterAutoOpen",globals=globals(),
            size=(-1,-1),label="auto")

        self.LaserShutter = Control(panel,type=ToggleButton,
            name="SAXS_WAXS_Control_Panel.LaserShutter",globals=globals(),
            size=(60,-1),label="Disabled")
        self.LaserShutterAutoOpen = Control(panel,type=wx.CheckBox,
            name="SAXS_WAXS_Control_Panel.LaserShutterAutoOpen",globals=globals(),
            size=(-1,-1),label="auto")

        self.Mode = Control(panel,type=wx.ComboBox,
            name="SAXS_WAXS_Control_Panel.Mode",globals=globals(),
            size=(100,-1),choices=SAXS_WAXS_control.modes)
        
        self.PumpEnabled = Control(panel,type=wx.CheckBox,
            name="SAXS_WAXS_Control_Panel.PumpEnabled",globals=globals(),
            size=(80,-1))

        self.PumpStep = Control(panel,type=ComboBox,
            name="SAXS_WAXS_Control_Panel.PumpStep",globals=globals(),
            size=(80,-1),choices=SAXS_WAXS_control.pump_step_choices)

        self.PumpPosition = Control(panel,type=TextCtrl,
            name="SAXS_WAXS_Control_Panel.PumpPosition",globals=globals(),
            size=(70,-1))
        self.PumpHomed = Control(panel,type=ToggleButton,
            name="SAXS_WAXS_Control_Panel.PumpHomed",globals=globals(),
            size=(140,-1),label="Homed")

        choices = ["500","600","700","800","1000"]
        self.LoadSampleStep = Control(panel,type=ComboBox,
            name="SAXS_WAXS_Control_Panel.LoadSampleStep",globals=globals(),
            size=(70,-1),choices=choices)
        self.LoadSample = Control(panel,type=ToggleButton,
            name="SAXS_WAXS_Control_Panel.LoadSample",globals=globals(),
            label="Load Sample",size=(140,-1))

        choices = ["-500","-600","-700","-800","-1000"]
        self.ExtractSampleStep = Control(panel,type=ComboBox,
            name="SAXS_WAXS_Control_Panel.ExtractSampleStep",globals=globals(),
            size=(70,-1),choices=choices)
        self.ExtractSample = Control(panel,type=ToggleButton,
            name="SAXS_WAXS_Control_Panel.ExtractSample",globals=globals(),
            label="Extract Sample",size=(140,-1))

        choices = ["500","600","700","800","1000"]
        self.CirculateSampleStep = Control(panel,type=ComboBox,
            name="SAXS_WAXS_Control_Panel.CirculateSampleStep",globals=globals(),
            size=(70,-1),choices=choices)
        self.CirculateSample = Control(panel,type=ToggleButton,
            name="SAXS_WAXS_Control_Panel.CirculateSample",globals=globals(),
            label="Circulate Sample",size=(140,-1))

        self.PumpSpeed = Control(panel,type=TextCtrl,
            name="SAXS_WAXS_Control_Panel.PumpSpeed",globals=globals(),
            size=(70,-1))

        # Layout
        flag = wx.ALIGN_CENTRE_HORIZONTAL|wx.ALL
        border = 2

        layout = wx.BoxSizer(wx.HORIZONTAL)
        left_panel = wx.BoxSizer(wx.VERTICAL)

        group = wx.BoxSizer(wx.HORIZONTAL)        
        text = wx.StaticText(panel,label="Environment:")
        group.Add (text,flag=flag,border=border)
        group.Add (self.Environment,flag=flag,border=border)
        left_panel.Add (group,flag=flag,border=border)

        group = wx.BoxSizer(wx.VERTICAL)        
        group.Add (self.XRayDetector,flag=flag,border=border)
        group.Add (self.XRayDetectorInserted,flag=flag,border=border)
        left_panel.Add (group,flag=flag,border=border)

        group = wx.BoxSizer(wx.VERTICAL)        
        text = wx.StaticText(panel,label="Ensemble Operation")
        group.Add (text,flag=flag,border=border)
        group.Add (self.Home,flag=flag,border=border)
        group.Add (self.ProgramRunning,flag=flag,border=border)
        left_panel.Add (group,flag=flag,border=border)

        group = wx.BoxSizer(wx.VERTICAL)        
        text = wx.StaticText(panel,label="Capillary Position")
        group.Add (text,flag=flag,border=border)
        group.Add (self.GotoSaved,flag=flag,border=border)
        group.Add (self.Save,flag=flag,border=border)
        group.Add (self.Inserted,flag=flag,border=border)
        left_panel.Add (group,flag=flag,border=border)

        layout.Add (left_panel,flag=flag,border=border)

        right_panel = wx.BoxSizer(wx.VERTICAL)

        group = wx.GridBagSizer(4,2)
        l = wx.ALIGN_LEFT; r = wx.ALIGN_RIGHT; cv = wx.ALIGN_CENTER_VERTICAL
        a = wx.ALL; e = wx.EXPAND

        row = 0
        text = wx.StaticText(panel,label="X-Ray Beam Shutter:")        
        group.Add (text,(row,0),flag=r|cv)
        subgroup = wx.BoxSizer(wx.HORIZONTAL)
        subgroup.Add (self.XRayShutter,flag=cv)
        subgroup.Add (self.XRayShutterAutoOpen,flag=cv)
        group.Add (subgroup,(row,1),flag=l|cv)

        row += 1
        text = wx.StaticText(panel,label="Laser Beam Shutter:")        
        group.Add (text,(row,0),flag=r|cv)
        subgroup = wx.BoxSizer(wx.HORIZONTAL)
        subgroup.Add (self.LaserShutter,flag=cv)
        subgroup.Add (self.LaserShutterAutoOpen,flag=cv)
        group.Add (subgroup,(row,1),flag=l|cv)

        row += 1
        text = wx.StaticText(panel,label="Mode:")
        group.Add (text,(row,0),flag=r|cv)
        group.Add (self.Mode,(row,1),flag=l|cv)

        row += 1
        text = wx.StaticText(panel,label="Pump:")
        group.Add (text,(row,0),flag=r|cv)
        group.Add (self.PumpEnabled,(row,1),flag=l|cv)

        row += 1
        text = wx.StaticText(panel,label="Pump Steps/Stroke:")        
        group.Add (text,(row,0),flag=r|cv)
        group.Add (self.PumpStep,(row,1),flag=l|cv)

        right_panel.Add (group,flag=flag,border=border)

        text = wx.StaticText(panel,label="Peristaltic Pump Operation [motor steps]")
        right_panel.Add (text,flag=flag,border=border)

        group = wx.GridBagSizer(1,1)
        
        group.Add (self.PumpPosition,(0,0),flag=r|cv|a,border=border)
        group.Add (self.PumpHomed,(0,1),flag=l|cv|a,border=border)

        group.Add (self.LoadSampleStep,(1,0),flag=r|cv|a,border=border)
        group.Add (self.LoadSample,(1,1),flag=l|cv|a,border=border)

        group.Add (self.ExtractSampleStep,(2,0),flag=r|cv|a,border=border)
        group.Add (self.ExtractSample,(2,1),flag=l|cv|a,border=border)

        group.Add (self.CirculateSampleStep,(3,0),flag=r|cv|a,border=border)
        group.Add (self.CirculateSample,(3,1),flag=l|cv|a,border=border)

        group.Add (self.PumpSpeed,(4,0),flag=r|cv|a,border=border)
        text = wx.StaticText(panel,label="Pump Speed [steps/s]",size=(140,-1))
        group.Add (text,(4,1),flag=l|cv|a,border=border)

        right_panel.Add (group,flag=flag,border=border)
        layout.Add (right_panel,flag=flag,border=border)

        panel.SetSizer(layout)
        panel.Fit()
        return panel


if __name__ == '__main__':
    from pdb import pm
    import logging; from tempfile import gettempdir
    logfile = gettempdir()+"/SAXS_WAXS_Control_Panel.log"
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s %(levelname)s: %(message)s",
        filename=logfile,
    )
    import autoreload
    # Needed to initialize WX library
    if not hasattr(wx,"app"): wx.app = wx.App(redirect=False)
    panel = SAXS_WAXS_Control_Panel()
    wx.app.MainLoop()
