#!/usr/bin/env python
"""Control panel for serial Laue crystallography.
Friedrich Schotte, Jul 2, 2017 - Oct 28, 2017"""
__version__ = "1.1" # update

from logging import debug,info,warn,error
import wx
from Laue_crystallography import control # passed on in "globals()"

class LaueCrystallographyControl(wx.Frame):
    """Control panel for serial Laue crystallography"""
    def __init__(self):
        wx.Frame.__init__(self,parent=None,title="Laue Crystallography Control")

        # Icon
        from Icon import SetIcon
        SetIcon(self,"Laue Crystallography Control")

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
        from inspect import getfile
        filename = getfile(self.__class__)
        ##debug("module: %s" % filename)
        from os.path import getmtime
        if self.timestamp == 0: self.timestamp = getmtime(filename)
        if getmtime(filename) != self.timestamp:
            self.timestamp = getmtime(filename)
            import LaueCrystallographyControlPanel
            reload(LaueCrystallographyControlPanel)
            from LaueCrystallographyControlPanel import LaueCrystallographyControl
            self.__class__ = LaueCrystallographyControl
            panel = self.ControlPanel
            self.panel.Destroy()
            self.panel = panel
            self.Fit()
            
    timestamp = 0

    @property
    def ControlPanel(self):
        # Controls and Layout
        panel = wx.Panel(self)
        from EditableControls import ComboBox,TextCtrl
        from Controls import Control
        from BeamProfile_window import BeamProfile

        flag = wx.ALIGN_CENTRE_HORIZONTAL|wx.ALL
        border = 2
        l = wx.ALIGN_LEFT; r = wx.ALIGN_RIGHT; cv = wx.ALIGN_CENTER_VERTICAL
        a = wx.ALL

        layout = wx.BoxSizer(wx.HORIZONTAL)
        left_panel = wx.BoxSizer(wx.VERTICAL)

        group = wx.BoxSizer(wx.VERTICAL)        
        text = wx.StaticText(panel,label="X-ray Detector:")
        group.Add (text,flag=flag,border=border)
        control = Control(panel,type=wx.ToggleButton,
            name="LaueCrystallographyControl.XRayDetectorInserted",
            globals=globals(),
            label="Retract/Insert",
            size=(180,-1))
        group.Add (control,flag=flag,border=border)
        left_panel.Add (group,flag=flag,border=border)

        group = wx.BoxSizer(wx.VERTICAL)        
        text = wx.StaticText(panel,label="Raster Scan Center:")
        group.Add (text,flag=flag,border=border)
        control = Control(panel,type=wx.Button,
            name="LaueCrystallographyControl.GotoSaved",globals=globals(),
            label="Go To Saved XYZ Position",
            size=(180,-1))
        group.Add (control,flag=flag,border=border)
        control = Control(panel,type=wx.Button,
            name="LaueCrystallographyControl.Save",globals=globals(),
            label="Save Current XYZ Positions",size=(180,-1))
        group.Add (control,flag=flag,border=border)
        control = Control(panel,type=wx.ToggleButton,
            name="LaueCrystallographyControl.Inserted",globals=globals(),
            label="Retract/Insert",
            size=(180,-1))
        group.Add (control,flag=flag,border=border)
        left_panel.Add (group,flag=flag,border=border)

        group = wx.BoxSizer(wx.VERTICAL)        
        text = wx.StaticText(panel,label="Raster Scan Controls:")
        group.Add (text,flag=flag,border=border)

        subgroup = wx.GridBagSizer(1,1)

        text = wx.StaticText(panel,label="Step Size [um]")
        subgroup.Add (text,(0,0),flag=l|cv|a,border=border)
        control = Control(panel,type=TextCtrl,
            name="LaueCrystallographyControl.StepSize",globals=globals(),
            size=(70,-1))
        subgroup.Add (control,(0,1),flag=l|cv|a,border=border)

        text = wx.StaticText(panel,label="Vertical Range [um]")
        subgroup.Add (text,(1,0),flag=l|cv|a,border=border)
        control = Control(panel,type=TextCtrl,
            name="LaueCrystallographyControl.VerticalRange",globals=globals(),
            size=(70,-1))
        subgroup.Add (control,(1,1),flag=l|cv|a,border=border)

        text = wx.StaticText(panel,label="Horizontal Range [um]")
        subgroup.Add (text,(2,0),flag=l|cv|a,border=border)
        control = Control(panel,type=TextCtrl,
            name="LaueCrystallographyControl.HorizontalRange",globals=globals(),
            size=(70,-1))
        subgroup.Add (control,(2,1),flag=l|cv|a,border=border)

        group.Add (subgroup,flag=flag,border=border)
        
        left_panel.Add (group,flag=flag,border=border)

        border = 4
        control = Control(panel,type=wx.ToggleButton,
            name="LaueCrystallographyControl.StartRasterScan",globals=globals(),
            label="Start Raster Scan",size=(180,-1))
        left_panel.Add (control,flag=flag,border=border)

        group = wx.BoxSizer(wx.VERTICAL)        
        text = wx.StaticText(panel,label="Crystal Coordinates:")
        group.Add (text,flag=flag,border=border)
        control = Control(panel,type=TextCtrl,
            name="LaueCrystallographyControl.CrystalCoordinates",globals=globals(),
            size=(180,120),style=wx.TE_MULTILINE)
        group.Add (control,flag=flag,border=border)
        left_panel.Add (group,flag=flag,border=border)

        layout.Add (left_panel,flag=flag,border=border)


        middle_panel = wx.BoxSizer(wx.VERTICAL)

        border = 5
        group = wx.BoxSizer(wx.VERTICAL)        
        text = wx.StaticText(panel,label="Syringe Pump Operation:")
        group.Add (text,flag=flag,border=border)
        border = 0
        control = Control(panel,type=wx.Button,
            name="LaueCrystallographyControl.Initialize",globals=globals(),
            label="Initialize",
            size=(120,-1))
        group.Add (control,flag=flag,border=border)
        control = Control(panel,type=wx.ToggleButton,
            name="LaueCrystallographyControl.Flow",globals=globals(),
            label="Suspend/Resume",
            size=(120,-1))
        group.Add (control,flag=flag,border=border)
        control = Control(panel,type=wx.ToggleButton,
            name="LaueCrystallographyControl.Inject",globals=globals(),
            label="Inject",
            size=(120,-1))
        group.Add (control,flag=flag,border=border)
        middle_panel.Add (group,flag=flag,border=border)

        border = 3

        group = wx.BoxSizer(wx.VERTICAL)        
        text = wx.StaticText(panel,label="Mother Liquor Syringe (250 uL)")
        group.Add (text,flag=flag,border=border)
        text = wx.StaticText(panel,label="Volume Expended (uL):")
        group.Add (text,flag=flag,border=border)

        subgroup = wx.GridBagSizer(1,1)

        control = Control(panel,type=TextCtrl,
            name="LaueCrystallographyControl.MotherLiquorSyringeVolume",
            globals=globals(),size=(70,-1))
        subgroup.Add (control,(0,0),flag=l|cv|a,border=border)
        control = Control(panel,type=wx.ToggleButton,
            name="LaueCrystallographyControl.MotherLiquorSyringeRefill",
            globals=globals(),label="Refill",size=(70,-1))
        subgroup.Add (control,(0,1),flag=l|cv|a,border=border)

        control = Control(panel,type=ComboBox,
            name="LaueCrystallographyControl.MotherLiquorSyringeStepsize",
            globals=globals(),size=(70,-1))
        subgroup.Add (control,(1,0),flag=l|cv|a,border=border)
        control = Control(panel,type=wx.ToggleButton,
            name="LaueCrystallographyControl.MotherLiquorSyringeDispense",
            globals=globals(),label="Dispense",size=(70,-1))
        subgroup.Add (control,(1,1),flag=l|cv|a,border=border)

        group.Add (subgroup,flag=flag,border=border)

        middle_panel.Add (group,flag=flag,border=border)

        group = wx.BoxSizer(wx.VERTICAL)        
        text = wx.StaticText(panel,label="Crystal Liquor Syringe (250 uL)")
        group.Add (text,flag=flag,border=border)
        text = wx.StaticText(panel,label="Volume Expended (uL):")
        group.Add (text,flag=flag,border=border)

        subgroup = wx.GridBagSizer(1,1)

        control = Control(panel,type=TextCtrl,
            name="LaueCrystallographyControl.CrystalLiquorSyringeVolume",
            globals=globals(),size=(70,-1))
        subgroup.Add (control,(0,0),flag=l|cv|a,border=border)
        control = Control(panel,type=wx.ToggleButton,
            name="LaueCrystallographyControl.CrystalLiquorSyringeRefill",
            globals=globals(),label="Refill",size=(70,-1))
        subgroup.Add (control,(0,1),flag=l|cv|a,border=border)

        control = Control(panel,type=ComboBox,
            name="LaueCrystallographyControl.CrystalLiquorSyringeStepsize",
            globals=globals(),size=(70,-1))
        subgroup.Add (control,(1,0),flag=l|cv|a,border=border)
        control = Control(panel,type=wx.ToggleButton,
            name="LaueCrystallographyControl.CrystalLiquorSyringeDispense",
            globals=globals(),label="Dispense",size=(70,-1))
        subgroup.Add (control,(1,1),flag=l|cv|a,border=border)

        group.Add (subgroup,flag=flag,border=border)

        middle_panel.Add (group,flag=flag,border=border)

        layout.Add (middle_panel,flag=flag,border=border)

        group = wx.BoxSizer(wx.VERTICAL)        
        text = wx.StaticText(panel,label="Pressure [atm]:")
        group.Add (text,flag=flag,border=border)

        subgroup = wx.GridBagSizer(1,1)

        text = wx.StaticText(panel,label="Upstream")
        subgroup.Add (text,(0,0),flag=l|cv|a,border=border)
        text = wx.StaticText(panel,label="Downstream")
        subgroup.Add (text,(0,1),flag=l|cv|a,border=border)
        
        control = Control(panel,type=TextCtrl,
            name="LaueCrystallographyControl.UpstreamPressure",
            globals=globals(),size=(70,-1))
        subgroup.Add (control,(1,0),flag=l|cv|a,border=border)
        control = Control(panel,type=TextCtrl,
            name="LaueCrystallographyControl.DownstreamPressure",
            globals=globals(),size=(70,-1))
        subgroup.Add (control,(1,1),flag=l|cv|a,border=border)

        control = Control(panel,type=ComboBox,
            name="LaueCrystallographyControl.TweakStepsize",
            globals=globals(),size=(70,-1))
        subgroup.Add (control,(2,0),flag=l|cv|a,border=border)
        control = Control(panel,type=wx.Button,
            name="LaueCrystallographyControl.Tweak",
            globals=globals(),label="Tweak",size=(70,-1))
        subgroup.Add (control,(2,1),flag=l|cv|a,border=border)

        group.Add (subgroup,flag=flag,border=border)

        middle_panel.Add (group,flag=flag,border=border)


        right_panel = wx.BoxSizer(wx.VERTICAL)
        border = 5

        text = wx.StaticText(panel,label="Microscope Image:")
        right_panel.Add (text,flag=flag,border=border)
        from CameraViewer import ImageWindow
        control = Control(panel,type=ImageWindow,
            name="LaueCrystallographyControl.Image",globals=globals(),
            size=(250,300))
        right_panel.Add (control,flag=flag,border=border)
        control = Control(panel,type=wx.ToggleButton,
            name="LaueCrystallographyControl.AcquireImage",globals=globals(),
            label="Acquire Image",
            size=(250,-1))
        right_panel.Add (control,flag=flag,border=border)

        group = wx.BoxSizer(wx.HORIZONTAL)        
        text = wx.StaticText(panel,label="Root name:")
        group.Add (text,flag=flag,border=border)
        control = Control(panel,type=TextCtrl,
            name="LaueCrystallographyControl.ImageRootName",globals=globals(),
            size=(170,-1))
        group.Add (control,flag=flag,border=border)
        right_panel.Add (group,flag=flag,border=border)

        control = Control(panel,type=wx.Button,
            name="LaueCrystallographyControl.SaveImage",globals=globals(),
            label="Save Image",
            size=(250,-1))
        right_panel.Add (control,flag=flag,border=border)
        layout.Add (right_panel,flag=flag,border=border)

        panel.SetSizer(layout)
        panel.Fit()
        return panel


if __name__ == '__main__':
    from pdb import pm
    import logging; from tempfile import gettempdir
    logfile = gettempdir()+"/LaueCrystallographyControlPanel.log"
    logging.basicConfig(level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        filename=logfile,
    )
    # Needed to initialize WX library
    if not hasattr(wx,"app"): wx.app = wx.App(redirect=False)
    panel = LaueCrystallographyControl()
    wx.app.MainLoop()
