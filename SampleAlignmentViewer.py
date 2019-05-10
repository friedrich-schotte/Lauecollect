#!/usr/bin/env python
"""An extension of the CameraViewer with controls for positioning the sample
Author: Friedrich Schotte,
Date created: 2010-07-22
Date last modified: 2019-03-25
"""
__version__ = "4.2" # Alignment_Panel_Shown setting

import wx
from CameraViewer import CameraViewer
from EditableControls import ComboBox,TextCtrl
from logging import debug,info,warn,error
deg = u"\xB0" # Unicode character for degree sign

class SampleAlignmentViewer(CameraViewer):
    __version__ = __version__ 
    __doc__ = __doc__ 
    from setting import setting
    Illumination_Panel_Shown = setting("Illumination_Panel_Shown",True)
    Alignment_Panel_Shown = setting("Alignment_Panel_Shown",False)

    settings = CameraViewer.settings + [
        "show_edge_controls",
        "stepsize",
        "camera_angle",
        "x_scale",
        "y_scale",
        "z_scale",
        "phi_stepsize",
        "learn_center",
        "click_center_enabled",
        ]

    sample_settings = [
        "x_motor_name","y_motor_name","z_motor_name","phi_motor_name",
        "xy_rotating",
        "rotation_center","calibration_z",
        "samples","sample_r",
        "support_points","GridOffset","GridSpacing",
        "click_center_x","click_center_y","click_center_z",
        "current_center_x","current_center_y",
        "learn_center_history",
        "show_mark_sample_controls","mark_sample_function",
        "keep_centered",
        ]

    def __init__(self,camera_angle=0.0,**kwargs):
        """
        camera_angle: [default value] phi angle at which Y translation is orthogonal
        to the camera viewing direction.
        """
        # Defaults
        self.stepsize = 0.01 # horiz. and vert. translation increment in mm
        self.camera_angle = camera_angle # viewing angle of camera with respect
        # to x translation at phi=0 in units of deg
        self.phi_stepsize = 90.0
        self.x_scale = -1 # X+ =  up at camera-angle + 90 deg?
        self.y_scale = 1 # Y+ = up at camera_angle?
        self.z_scale = -1 # Z+ = right?
        self.keep_centered = False
        self.x_motor_name = "SampleX"
        self.y_motor_name = "SampleY"
        self.z_motor_name = "SampleZ"
        self.phi_motor_name = "SamplePhi"
        self.xy_rotating = True
        # To which (X,Y) do you have to drive the motors for the rotation axis
        # to be on the crosshair?
        self.rotation_center = 0.0,0.0
        # To get reproducible positioning of objects mouned on the magnetic
        # based after disasambling and reassembing the the diffractmeter.
        # As part of recalibrating the rotation axis a reference z position 
        # is defined by the fiber tip of te alignment needle.
        # After the the saved coordinates of of other objects should be valid.
        self.calibration_z = 0.0 
        self.click_center_x = 0.0 # Sample center, for "Return to Center"
        self.click_center_y = 0.0 # Sample center, for "Return to Center"
        self.click_center_z = 0.0 # Sample center, for "Return to Center"
        self.current_center_x = 0.0 
        self.current_center_y = 0.0
        self.learn_center = False # Currently calibrating rotation axis?
        self.learn_center_history = []
        self.samples = [] # Marked positions of crystals
        self.current_sample = None
        self.current_sample_point = "start"
        self.sample_r = 0.0 # Radius of the sample (idealized as cylinder)
        self.support_points = [] # outline of the crystal for Lauecollect
        self.GridOffset = 0.0

        CameraViewer.__init__(self,**kwargs)
        # Menus
        menuBar = self.GetMenuBar()
        menu = menuBar.GetMenu(3) # 'Options' menu
        menu.Append(402,"&Alignment Setup...","Parameters for sample alignment")
        self.Bind(wx.EVT_MENU,self.OnAlignmentSetup,id=402)
        menu.Append(407,"&Center...","Sample Centering")
        self.Bind(wx.EVT_MENU,self.OnCenter,id=407)

        menu.AppendSeparator()
        
        menu.Append(409,"&Show Illumination Controls","Extra controls below image",
            wx.ITEM_CHECK)
        self.ShowIlluminationControlsMenuItem = menu.FindItemById(409)
        self.ShowIlluminationControlsMenuItem.Check(self.Illumination_Panel_Shown)
        self.Bind(wx.EVT_MENU,self.OnShowIlluminationControls,id=409)
        menu.Append(403,"&Show Alignment Controls","Extra controls below image",
            wx.ITEM_CHECK)
        self.ShowAlignmentControlsMenuItem = menu.FindItemById(403)
        self.ShowAlignmentControlsMenuItem.Check(self.Alignment_Panel_Shown)
        self.Bind(wx.EVT_MENU,self.OnShowAlignmentControls,id=403)
        menu.Append(404,"&Show Edge Controls","Extra controls below image",
            wx.ITEM_CHECK)
        self.ShowEdgeControlsMenuItem = menu.FindItemById(404)
        self.Bind(wx.EVT_MENU,self.OnShowEdgeControls,id=404)
        menu.Append(408,"&Show Mark Sample Controls","Extra controls below image",
            wx.ITEM_CHECK)
        self.ShowMarkSampleMenuItem = menu.FindItemById(408)
        self.Bind(wx.EVT_MENU,self.OnShowMarkSample,id=408)

        menu.AppendSeparator()
        
        menu.Append(405,"&Calibrate Rotation...",
            "Find the rotation center of the Phi axis")
        self.Bind(wx.EVT_MENU,self.OnCalibrateRotation,id=405)
        menu.Append(406,"&Sample Center...",
            "Define Rotation Center of an Object")
        self.Bind(wx.EVT_MENU,self.OnSampleCenter,id=406)
       
        self.Illumination_Panel = Illumination_Panel(self.panel)
        self.layout.AddSpacer(5)
        self.layout.Add (self.Illumination_Panel,flag=wx.EXPAND)
        self.Illumination_Panel.Shown = self.Illumination_Panel_Shown

        # Alignment Panel
        # Controls 
        panel = self.Alignment_Panel = wx.Panel(self.panel)
        style = wx.TE_PROCESS_ENTER
        choices = ["500 um","200 um","100 um","50 um","20 um","10 um","5 um",
            "2 um","1 um"]
        self.StepSize = ComboBox (panel,style=style,choices=choices,
            size=(80,-1))
        self.Bind (wx.EVT_COMBOBOX,self.OnStepSize,self.StepSize)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnStepSize,self.StepSize)

        left = wx.ArtProvider.GetBitmap(wx.ART_GO_BACK)
        right = wx.ArtProvider.GetBitmap(wx.ART_GO_FORWARD)
        up = wx.ArtProvider.GetBitmap(wx.ART_GO_UP)
        down = wx.ArtProvider.GetBitmap(wx.ART_GO_DOWN)

        self.TranslateFromCamera = wx.BitmapButton(panel,bitmap=left)
        self.TranslateFromCamera.ToolTip = wx.ToolTip("Move away from camera")
        self.Bind (wx.EVT_BUTTON,self.OnTranslateFromCamera,self.TranslateFromCamera)
        self.TranslateTowardCamera = wx.BitmapButton(panel,bitmap=right)
        self.TranslateTowardCamera.ToolTip = wx.ToolTip("Move closer to camera")
        self.Bind (wx.EVT_BUTTON,self.OnTranslateTowardCamera,self.TranslateTowardCamera)

        self.TranslateHLeft = wx.BitmapButton(panel,bitmap=left)
        self.Bind (wx.EVT_BUTTON,self.OnTranslateHLeft,self.TranslateHLeft)
        self.TranslateHRight = wx.BitmapButton(panel,bitmap=right)
        self.Bind (wx.EVT_BUTTON,self.OnTranslateHRight,self.TranslateHRight)
        
        self.TranslateVUp = wx.BitmapButton(panel,bitmap=up)
        self.Bind(wx.EVT_BUTTON,self.OnTranslateVUp,self.TranslateVUp)
        self.TranslateVDown = wx.BitmapButton (panel,bitmap=down)
        self.Bind(wx.EVT_BUTTON,self.OnTranslateVDown,self.TranslateVDown)

        self.Phi = TextCtrl(panel,size=(70,-1),style=style)
        self.Bind(wx.EVT_TEXT_ENTER,self.OnEnterPhi,self.Phi)

        choices = ["180"+deg,"90"+deg,"45"+deg,"30"+deg,"10"+deg,"5"+deg,"1"+deg]
        self.PhiStepSize = ComboBox (panel,style=style,choices=choices,
            size=(65,-1))
        self.Bind (wx.EVT_COMBOBOX,self.OnPhiStepSize,self.PhiStepSize)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnPhiStepSize,self.PhiStepSize)

        self.IncrPhi = wx.BitmapButton (panel,bitmap=up,size=(40,-1))
        self.Bind (wx.EVT_BUTTON,self.OnIncrPhi,self.IncrPhi)
        self.DecrPhi = wx.BitmapButton (panel,bitmap=down,size=(40,-1))
        self.Bind (wx.EVT_BUTTON,self.OnDecrPhi,self.DecrPhi)

        self.ClickCenteringButton = wx.ToggleButton(panel,
            label="Click Centering: Active")
        self.Bind (wx.EVT_TOGGLEBUTTON,self.OnClickCenteringButton,
            self.ClickCenteringButton)
        self.ClickCenteringButton.ToolTip = wx.ToolTip("When clicking in the "
            "image, translate clicked point to crosshair")
        self.KeepCentered = wx.CheckBox(panel,label="Keep centered")
        self.Bind (wx.EVT_CHECKBOX,self.OnKeepCentered,self.KeepCentered)
        self.LearnCenter = wx.CheckBox(panel,label="Learn center")
        self.Bind (wx.EVT_CHECKBOX,self.OnLearnCenter,self.LearnCenter)
        self.ReturnButton = wx.Button(panel,label="Return to Center")
        self.Bind (wx.EVT_BUTTON,self.OnReturnButton,self.ReturnButton)

        # Layout
        grid = wx.GridBagSizer (hgap=0,vgap=0)

        label = wx.StaticText(self.Alignment_Panel,label="Step:")
        grid.Add (label,(1,0),flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add (self.StepSize,(1,1),flag=wx.ALIGN_CENTER)

        label = wx.StaticText(self.Alignment_Panel,label="Focus:")
        grid.Add (label,(2,0),flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add (self.TranslateFromCamera,flag=wx.ALIGN_CENTER)
        hbox.Add (self.TranslateTowardCamera,flag=wx.ALIGN_CENTER)
        grid.Add (hbox,(2,1),flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)

        grid.Add (self.TranslateHLeft,(1,0+3),flag=wx.ALIGN_CENTER)
        grid.Add (self.TranslateHRight,(1,2+3),flag=wx.ALIGN_CENTER)
        grid.Add (self.TranslateVUp,(0,1+3),flag=wx.ALIGN_CENTER)
        grid.Add (self.TranslateVDown,(2,1+3),flag=wx.ALIGN_CENTER)

        label = wx.StaticText(self.Alignment_Panel,label="Phi:")
        grid.Add (label,(1,4+3),flag=wx.ALIGN_CENTER)
        grid.Add (self.IncrPhi,(0,5+3),flag=wx.ALIGN_CENTER)
        grid.Add (self.Phi,(1,5+3),flag=wx.ALIGN_CENTER)
        grid.Add (self.DecrPhi,(2,5+3),flag=wx.ALIGN_CENTER)
        label = wx.StaticText(self.Alignment_Panel,label="Step:")
        grid.Add (label,(1,7+3),flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add (self.PhiStepSize,(1,8+3),flag=wx.ALIGN_CENTER)

        grid.Add (self.ClickCenteringButton,(0,10+3),span=(1,2),flag=wx.ALIGN_CENTER|wx.EXPAND)
        grid.Add (self.KeepCentered,(1,10+3),flag=wx.ALIGN_CENTER|wx.EXPAND)
        grid.Add (self.LearnCenter,(1,11+3),flag=wx.ALIGN_CENTER|wx.EXPAND)
        grid.Add (self.ReturnButton,(2,10+3),span=(1,2),flag=wx.ALIGN_CENTER|wx.EXPAND)

        self.Alignment_Panel.SetSizer(grid)
        
        self.layout.AddSpacer(5)
        self.layout.Add (self.Alignment_Panel,flag=wx.EXPAND)
        self.Alignment_Panel.Shown = self.Alignment_Panel_Shown
        
        # Controls - Edge Panel
        panel = self.edge_panel = wx.Panel(self.panel)

        self.DefineEdgeButton = wx.ToggleButton(panel,label="Define Edge",
            size=(-1,-1))
        self.Bind (wx.EVT_TOGGLEBUTTON,self.OnDefineEdgeButton,
            self.DefineEdgeButton)
        self.UndoButton = wx.Button(panel,label="Undo",size=(50,-1))
        self.Bind (wx.EVT_BUTTON,self.OnUndoButton,self.UndoButton)
        self.ClearButton = wx.Button(panel,label="Clear All")
        self.Bind (wx.EVT_BUTTON,self.OnClearButton,self.ClearButton)

        self.ShowGridControl = wx.CheckBox (panel,label="Grid")
        self.Bind (wx.EVT_CHECKBOX,self.OnShowGrid,self.ShowGridControl)
        self.ShiftGridLeft = wx.BitmapButton (panel,bitmap=left)
        self.Bind (wx.EVT_BUTTON,self.OnShiftGridLeft,self.ShiftGridLeft)
        self.ShiftGridRight = wx.BitmapButton (panel,bitmap=right)
        self.Bind (wx.EVT_BUTTON,self.OnShiftGridRight,self.ShiftGridRight)
        choices = ["200 um","150 um","120 um","100 um","80 um"]
        self.GridSpacingControl = ComboBox (panel,style=style,choices=choices,
            size=(80,-1))
        self.Bind (wx.EVT_COMBOBOX,self.OnGridSpacing,self.GridSpacingControl)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnGridSpacing,self.GridSpacingControl)

        # Controls - Center Panel
        panel = self.center_panel = wx.Panel(self.panel)

        self.MarkSampleButton = wx.ToggleButton(panel,label="Mark",
            size=(-1,-1))
        self.MarkSampleDeleteButton = wx.ToggleButton(panel,label="Delete",
            size=(-1,-1))
        self.MarkSampleWidthButton = wx.ToggleButton(panel,label="Width",
            size=(-1,-1))
        self.Bind (wx.EVT_TOGGLEBUTTON,self.OnMarkSampleFunction,
            self.MarkSampleButton)
        self.Bind (wx.EVT_TOGGLEBUTTON,self.OnMarkSampleFunction,
            self.MarkSampleDeleteButton)
        self.Bind (wx.EVT_TOGGLEBUTTON,self.OnMarkSampleFunction,
            self.MarkSampleWidthButton)
        self.MarkSampleClearButton = wx.Button(panel,label="Clear All")
        self.Bind (wx.EVT_BUTTON,self.OnMarkSampleClear,self.MarkSampleClearButton)

        # Layout - Edge Panel
        self.layout.AddSpacer(5)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        grid = wx.GridBagSizer (hgap=0,vgap=0)

        grid.Add (self.DefineEdgeButton,(0,0),flag=wx.ALIGN_CENTER)
        grid.Add (self.UndoButton,(0,1),flag=wx.ALIGN_CENTER)
        grid.Add (self.ClearButton,(0,2),flag=wx.ALIGN_CENTER)

        grid.Add (self.ShowGridControl,(0,4),flag=wx.ALIGN_CENTER)
        label = wx.StaticText(self.edge_panel,label="Spacing:")
        grid.Add (label,(0,6),flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add (self.GridSpacingControl,(0,7),flag=wx.ALIGN_CENTER)
        label = wx.StaticText(self.edge_panel,label="Shift")
        grid.Add (label,(0,9),flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add (self.ShiftGridLeft,(0,11),flag=wx.ALIGN_CENTER)
        grid.Add (self.ShiftGridRight,(0,12),flag=wx.ALIGN_CENTER)

        hbox.Add (grid,flag=wx.ALIGN_CENTER)
        self.edge_panel.SetSizer(hbox)
        self.layout.Add (self.edge_panel,flag=wx.EXPAND)

        # Layout - Center Panel
        self.layout.AddSpacer(5)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        grid = wx.GridBagSizer (hgap=0,vgap=0)

        grid.Add (self.MarkSampleButton,(0,0),flag=wx.ALIGN_CENTER)
        grid.Add (self.MarkSampleDeleteButton,(0,1),flag=wx.ALIGN_CENTER)
        grid.Add (self.MarkSampleWidthButton,(0,2),flag=wx.ALIGN_CENTER)
        grid.Add (self.MarkSampleClearButton,(0,3),flag=wx.ALIGN_CENTER)

        hbox.Add (grid,flag=wx.ALIGN_CENTER)
        self.center_panel.SetSizer(hbox)
        self.layout.Add (self.center_panel,flag=wx.EXPAND)
        
        self.layout.Layout()
        
        # Initialization                
        self.edited = (255,255,220)
        self.ClickCenteringButton.DefaultForegroundColour = \
            self.ClickCenteringButton.ForegroundColour
        self.ClickCenteringButton.DefaultBackgroundColour = \
            self.ClickCenteringButton.BackgroundColour

        self.DefineEdgeButton.DefaultForegroundColour = \
            self.DefineEdgeButton.ForegroundColour
        self.DefineEdgeButton.DefaultBackgroundColour = \
            self.DefineEdgeButton.BackgroundColour

        self.AddPointerFunction("Click-Center")
        self.AddPointerFunction("Define Edge")
        self.AddPointerFunction("Mark Sample")
        self.stepsize_value = self.stepsize
        self.PhiStepSize.Value = "%g%s" % (self.phi_stepsize,deg)

        self.update_sample_settings()
        self.update()

    def get_show_edge_controls(self):
        """Is the control panel visible?"""
        return self.edge_panel.Shown
    def set_show_edge_controls(self,value):
        self.ShowEdgeControlsMenuItem.Check(value)
        self.edge_panel.Shown = value
        self.layout.Layout()
    show_edge_controls = \
        property(get_show_edge_controls,set_show_edge_controls)

    def get_show_mark_sample_controls(self):
        """Is the control panel visible?"""
        return self.center_panel.Shown
    def set_show_mark_sample_controls(self,value):
        self.ShowMarkSampleMenuItem.Check(value)
        self.center_panel.Shown = value
        self.layout.Layout()
    show_mark_sample_controls = \
        property(get_show_mark_sample_controls,set_show_mark_sample_controls)

    def update(self,event=None):
        """Update the annotations on the camera image"""
        from numpy import any,isnan,array,arange,concatenate

        # Update the "Grid" check box.
        self.ShowGridControl.Value = self.ShowGrid
        # Update the spacing indicator/control.
        self.GridSpacingControl.Value = "%.0f um" % (self.GridXSpacing*1000)

        # Show click center.
        cx,cy = self.sample_center_camera_xy
        self.AddObject("Click Center",[(cx,cy)],color=(0,255,0),type="squares")

        # Mark the sample position.
        for i in range(0,len(self.samples)):
            sample = self.samples[i]
            points = []
            points += [self.sample_camera_xy(*sample["start"])]
            points += [self.sample_camera_xy(*sample["end"])]
            self.AddObject("Sample %d End Points" % (i+1),points,color=(0,255,255),type="squares")
            if len(points) > 1:
                self.AddObject("Sample %d Center Line" % (i+1),points,color=(0,0,255),type="line")
            # Outline the sample shape.
            x1,y1 = self.sample_camera_xy(*sample["start"])
            x2,y2 = self.sample_camera_xy(*sample["end"])
            r = self.sample_r
            points = [[x1,y1-r],[x1,y1+r],[x2,y2+r],[x2,y2-r],[x1,y1-r]]
            self.AddObject("Sample %d Outline" % (i+1),points,color=(128,128,255),type="line")
            # To do: AddObjects - Add mutiple objects wth a single refresh
        for i in range(len(self.samples),20):
            self.DeleteObject("Sample %d End Points"  % (i+1))
            self.DeleteObject("Sample %d Center Line" % (i+1))
            self.DeleteObject("Sample %d Outline"     % (i+1))

        # Outline the sample shape.
        dz = self.GridXSpacing
        if len(self.support_points) > 0:
            z1,z2 = self.z_range()[0]-dz/2,self.z_range()[1]+dz/2
            Z = concatenate((arange(z1,z2,0.02),[z2]))
            phi = self.phi - self.camera_angle
            OFFSET = array([self.interpolated_offset(phi,z) for z in Z])
            points = [self.camera_position(z,o) for z,o in zip(Z,OFFSET)]
            # Shift the points, following the same translation.
            cy = self.sample_center_offset
            points = [(x,y+cy) for (x,y) in points]
        else: points = []
        self.AddObject("Edge",points,color=(0,0,255),type="line")

        # Show the support points.
        points = []
        dphi = max(getattr(self.phi_motor,"readback_slop",0),1.0)
        for phi,x,y,z,offset in self.support_points:
            if abs(phi % 360 - (self.phi - self.camera_angle) % 360) < dphi:
                points += [self.camera_position(z,offset)]
        # Shift the points, following the same translation.
        cy = self.sample_center_offset
        points = [(x,y+cy) for (x,y) in points]
        self.AddObject("Edge Points",points,color=(0,255,255),type="squares")

        # Update vertical grid lines.
        offset = (self.z * self.z_scale + self.GridOffset) % self.GridXSpacing
        if not isnan(offset): self.GridXOffset = offset

        # Show rotation axis.
        offset = self.rotation_axis_offset
        p1 = self.camera_position(-10,offset)
        p2 = self.camera_position(10,offset)
        self.AddObject("Rotation axis",[p1,p2],color=(128,128,255),type="line")
        
        # Update controls
        self.TranslateFromCamera.Enabled   = not isnan(self.zc)
        self.TranslateTowardCamera.Enabled = not isnan(self.zc)
        self.TranslateHLeft.Enabled        = not isnan(self.xc)
        self.TranslateHRight.Enabled       = not isnan(self.xc)
        self.TranslateVUp.Enabled          = not isnan(self.yc)
        self.TranslateVDown.Enabled        = not isnan(self.yc)

        self.Phi.Value = "%.3f%s" % (self.phi,deg) if not isnan(self.phi) else ""
        self.stepsize_value = self.stepsize
        self.PhiStepSize.Value = "%g%s" % (self.phi_stepsize,deg)

        self.Phi.Enabled         = not isnan(self.phi)
        self.PhiStepSize.Enabled = not isnan(self.phi)
        self.IncrPhi.Enabled     = not isnan(self.phi)
        self.DecrPhi.Enabled     = not isnan(self.phi)

        # Update Buttons
        self.KeepCentered.Value = self.keep_centered
        
        self.UndoButton.Enabled = (len(self.support_points) > 0)
        self.ClearButton.Enabled = (len(self.support_points) > 0)

        self.KeepCentered.Value = self.keep_centered

        self.LearnCenter.Value = self.learn_center

        # Update pointer
        if self.mark_sample_enabled: self.PointerFunction = "Mark Sample"
        elif self.click_center_enabled: self.PointerFunction = "Click-Center"
        elif self.define_edge_enabled: self.PointerFunction = "Define Edge"
        else: self.PointerFunction = ""

        # Relaunch yourself.
        self.update_timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.update,self.update_timer)
        self.update_timer.Start(1000,oneShot=True)

    def update_sample_settings(self,event=None):
        """Monitors the settings file and reloads it if it is updated.
        Or, updates the file, if settings changed."""
        from os import makedirs,remove,rename
        from os.path import exists
        def getmtime(filename): # Modification timestamp of a file
            from os.path import getmtime
            try: return getmtime(filename)
            except: return 0

        settings_file = self.settings_dir()+"/sample_settings.py"

        if not hasattr(self,"sample_timestamp"): self.sample_timestamp = 0
        if not hasattr(self,"saved_sample_state"):
            self.saved_sample_state = self.SampleState
        
        if exists(settings_file) and getmtime(settings_file) != self.sample_timestamp:
            # (Re)load settings file.
            try:
                settings = file(settings_file).read()
                self.SampleState = file(settings_file).read()
                self.saved_sample_state = self.SampleState
                self.sample_timestamp = getmtime(settings_file)
            except IOError,msg: error("Failed to read %s: %s\n" % (settings_file,msg))
        elif self.SampleState != self.saved_sample_state or not exists(settings_file):
            # Update settings file.
            if not exists(self.settings_dir()): makedirs(self.settings_dir())
            try:
                file(settings_file+".tmp","wb").write(self.SampleState)
                if exists(settings_file): remove(settings_file)
                rename(settings_file+".tmp",settings_file)
                self.saved_sample_state = self.SampleState
                self.sample_timestamp = getmtime(settings_file)
            except IOError:
                error("Failed to update %r" % settings_file)

        # Relaunch this procedure after 2 s
        self.sample_settings_timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.update_sample_settings,self.sample_settings_timer)
        self.sample_settings_timer.Start(2000,oneShot=True)

    def GetSampleState(self):
        state = ""
        for attr in self.sample_settings:
            line = attr+" = "+repr(eval("self."+attr))
            state += line+"\n"
        return state
    def SetSampleState(self,state):
        for line in state.split("\n"):
            line = line.strip(" \n\r")
            if line != "":
                try: exec("self."+line)
                except: warn("ignoring line %r" % line); pass
    SampleState = property(GetSampleState,SetSampleState)

    def get_x_motor(self):
        return self.motor(self.x_motor_name)
    x_motor = property(get_x_motor)

    def get_y_motor(self):
        return self.motor(self.y_motor_name)
    y_motor = property(get_y_motor)
    
    def get_z_motor(self):
        return self.motor(self.z_motor_name)
    z_motor = property(get_z_motor)

    def get_phi_motor(self):
        return self.motor(self.phi_motor_name)
    phi_motor = property(get_phi_motor)

    def motor(self,name):
        if not hasattr(self,"cache"): self.cache = {}
        if not name in self.cache: self.cache[name] = motor(name)
        return self.cache[name]
        
    def get_x(self): return self.x_motor.value
    def set_x(self,value): self.x_motor.value = value
    x = property(get_x,set_x)

    def get_y(self): return self.y_motor.value
    def set_y(self,value): self.y_motor.value = value
    y = property(get_y,set_y)

    def get_z(self): return self.z_motor.value
    def set_z(self,value): self.z_motor.value = value
    z = property(get_z,set_z)
    
    def get_phi(self): return self.phi_motor.value
    def set_phi(self,value): self.phi_motor.value = value
    phi = property(get_phi,set_phi)

    def get_xc(self): return self.x_motor.command_value
    def set_xc(self,value): self.x_motor.command_value = value
    xc = property(get_xc,set_xc)

    def get_yc(self): return self.y_motor.command_value
    def set_yc(self,value): self.y_motor.command_value = value
    yc = property(get_yc,set_yc)

    def get_zc(self): return self.z_motor.command_value
    def set_zc(self,value): self.z_motor.command_value = value
    zc = property(get_zc,set_zc)

    def get_phic(self): return self.phi_motor.command_value
    def set_phic(self,value): self.phi_motor.command_value = value
    phic = property(get_phic,set_phic)

    def rotate(self,phi):
        """Rotate the spindle to the new angle phi, keeping te sample
        centered"""
        if self.keep_centered:
            # While rotating, keep the sample centered on the cross hair.
            self.current_center_x,self.current_center_y = \
                self.sample_center_xy(self.xc,self.yc,self.phic)
            cx,cy = self.sample_center_xy_phi(phi)
            self.xc,self.yc = cx,cy

        self.phic = phi

    GridSpacing = CameraViewer.GridXSpacing

    def OnStepSize(self,event):
        """Change the step size to the value displayed by the control"""
        # Called when the user enters a new step size on the the control
        from numpy import isnan
        if not isnan(self.stepsize_value): self.stepsize = self.stepsize_value
        self.stepsize_value = self.stepsize

    def get_stepsize_value(self):
        """Step size as displayed by the stepsize control"""
        from numpy import nan
        value = self.StepSize.Value.replace("um","")
        try: value = float(eval(value))/1000
        except ValueError: value = nan
        return value
    def set_stepsize_value(self,value):
        from numpy import isnan        
        text = "%g um" % (value*1000) if not isnan(value) else ""
        self.StepSize.Value = text
    stepsize_value = property(get_stepsize_value,set_stepsize_value)

    def OnTranslateTowardCamera(self,event):
        """Move the same closer to the camera"""
        self.move_relative(0,0,-self.stepsize_value)
        if self.learn_center:
            self.camera_rotation_center_xc -= self.stepsize_value
        
    def OnTranslateFromCamera(self,event):
        """Move the same away from the camera"""
        self.move_relative(0,0,+self.stepsize_value)
        if self.learn_center:
            self.camera_rotation_center_xc += self.stepsize_value
        
    def OnTranslateHLeft(self,event):
        """Tweak the position horizontally"""
        self.move_relative(-self.stepsize_value,0,0)
        
    def OnTranslateHRight(self,event):
        """Tweak the position horizontally"""
        self.move_relative(+self.stepsize_value,0,0)
               
    def OnTranslateVUp(self,event):
        """Tweak the position vertically"""
        self.move_relative(0,+self.stepsize_value,0)
        if self.learn_center:
            self.camera_rotation_center_yc += self.stepsize_value
        
    def OnTranslateVDown(self,event):
        """Tweak the position vertically"""
        self.move_relative(0,-self.stepsize_value,0)
        if self.learn_center:
            self.camera_rotation_center_yc -= self.stepsize_value

    def move_relative(self,camera_dx,camera_dy,camera_dz):
        """Execute a relative move in the camera coordinate system.
        camera_dx: horizontal direction in  mm, pos = left
        camera_dy: vertical direction, in mm, pos = up
        camera_dz: along the viewing direction (focus direction) in mm, pos = farther
        """
        dx,dy,dz = self.dxdydz_of_camera_dxdydz(camera_dx,camera_dy,camera_dz)
        self.current_center_x,self.current_center_y = \
            self.sample_center_xy(self.xc+dx,self.yc+dy,self.phic)
        self.xc += dx; self.yc += dy;
        if dz != 0: self.zc += dz
        
    def OnEnterPhi(self,event):
        """Called when Enter is pressed in the text box."""
        value = self.Phi.Value.replace(deg,"")
        try: phi = float(eval(value))
        except ValueError: return
        self.rotate(phi)

    def OnPhiStepSize(self,event):
        """Called if the rotation step size is changed"""
        value = self.PhiStepSize.Value.replace(deg,"")
        try: self.phi_stepsize = float(eval(value))
        except ValueError: pass
        self.PhiStepSize.Value = "%g%s" % (self.phi_stepsize,deg)

    def OnDecrPhi(self,event):
        """Rotate the sample"""
        self.rotate(self.phic - self.phi_stepsize)

    def OnIncrPhi(self,event=None):
        """Rotate the sample"""
        self.rotate(self.phic + self.phi_stepsize)
        
    def OnClickCenteringButton(self,event):
        """Called when the 'Click Centering' button is pressed or released"""
        self.UpdateClickCenteringButton()

    def get_click_center_enabled(self):
        """Does clicking the image move the motors?"""
        return self.ClickCenteringButton.Value
    def set_click_center_enabled(self,enabled):
        self.ClickCenteringButton.Value = enabled
        self.UpdateClickCenteringButton()

    def UpdateClickCenteringButton(self):
        if self.ClickCenteringButton.Value == True:
            self.ClickCenteringButton.Label = "Click Centering: Active"
            self.ClickCenteringButton.BackgroundColour = (255,255,0)
            self.ClickCenteringButton.ForegroundColour = (255,0,0)
        else:
            self.ClickCenteringButton.Label = "Click Centering: Off      "
            self.ClickCenteringButton.BackgroundColour = \
                self.ClickCenteringButton.DefaultBackgroundColour
            self.ClickCenteringButton.ForegroundColour = \
                self.ClickCenteringButton.DefaultForegroundColour
    click_center_enabled = property(get_click_center_enabled,set_click_center_enabled) 

    def OnKeepCentered(self,event):
        """Called when the status of the 'Keep Centered' checkbox changes"""
        self.keep_centered = self.KeepCentered.Value

    def OnLearnCenter(self,event):
        """Called when the status of the 'Learn Center' checkbox changes"""
        self.learn_center = self.LearnCenter.Value

    def OnReturnButton(self,event):
        """Called when the 'Return to Center' button is pressed"""
        self.current_center_x,self.current_center_y = \
            self.click_center_x,self.click_center_y
        self.x,self.y = self.sample_centered_xy
        self.z = self.click_center_z+self.calibration_z

    def OnDefineEdgeButton(self,event):
        """Called when the 'Define Edge' button is pressed or released"""
        self.UpdateDefineEdgeButton()

    def get_define_edge_enabled(self):
        return self.DefineEdgeButton.Value
    def set_define_edge_enabled(self,value):
        self.DefineEdgeButton.Value = value
        self.UpdateDefineEdgeButton()
    define_edge_enabled = property(get_define_edge_enabled,set_define_edge_enabled)

    def UpdateDefineEdgeButton(self):
        if self.DefineEdgeButton.Value == True:
            self.DefineEdgeButton.BackgroundColour = (255,255,0)
            self.DefineEdgeButton.ForegroundColour = (255,0,0)
        else:
            self.DefineEdgeButton.BackgroundColour = \
                self.DefineEdgeButton.DefaultBackgroundColour
            self.DefineEdgeButton.ForegroundColour = \
                self.DefineEdgeButton.DefaultForegroundColour

    def OnUndoButton(self,event):
        """Called when the 'Undo' button is pressed"""
        self.UndoLastEdgeDefinition()

    def OnClearButton(self,event):
        """Called when the 'Reset' button is pressed"""
        self.ResetEdgeDefinition()

    def OnShowGrid(self,event):
        """Toggle vertical grid on/off"""
        self.ShowGrid = self.ShowGridControl.Value
        
    def OnShiftGridLeft(self,event):
        """Tweak the grid position horizontally"""
        stepsize = self.GridXSpacing*0.02
        self.GridOffset = (self.GridOffset - stepsize) % self.GridXSpacing
        
    def OnShiftGridRight(self,event):
        """Tweak the grid position horizontally"""
        stepsize = self.GridXSpacing*0.02
        self.GridOffset = (self.GridOffset + stepsize) % self.GridXSpacing
        
    def OnGridSpacing(self,event):
        "Change the horizontal grid spacing"
        value = self.GridSpacingControl.Value.replace("um","")
        try: self.GridXSpacing = float(eval(value))/1000
        except ValueError: pass
        self.GridSpacingControl.Value = "%.0f um" % (self.GridXSpacing*1000)
        
    def OnMarkSampleFunction(self,event):
        """Called when switching between 'Start','End','Width' """
        if event.EventObject == self.MarkSampleButton:
            mark_sample_function = "mark"
        if event.EventObject == self.MarkSampleDeleteButton:
            mark_sample_function = "delete"
        elif event.EventObject == self.MarkSampleWidthButton:
            mark_sample_function = "width"
        buttons = self.MarkSampleButton,self.MarkSampleWidthButton
        if not any([button.Value for button in buttons]):
            mark_sample_function = ""
        self.mark_sample_function = mark_sample_function

    def get_mark_sample_function(self):
        """What does a mouse click define?
        "mark" or "width"
        "" for nothing."""
        if self.MarkSampleButton.Value == True: return "mark"
        if self.MarkSampleDeleteButton.Value == True: return "delete"
        if self.MarkSampleWidthButton.Value == True: return "width"
        return ""
    def set_mark_sample_function(self,value):
        self.MarkSampleButton.Value = (value == "mark")
        self.MarkSampleDeleteButton.Value = (value == "delete")
        self.MarkSampleWidthButton.Value = (value == "width")
    mark_sample_function = property(get_mark_sample_function,set_mark_sample_function)

    def get_mark_sample_enabled(self):
        if not self.show_mark_sample_controls: return False
        if self.MarkSampleButton.Value == True: return True
        if self.MarkSampleDeleteButton.Value == True: return True
        if self.MarkSampleWidthButton.Value == True: return True
        return False
    def set_mark_sample_enabled(self,enabled):
        buttons = self.MarkSampleButton,self.MarkSampleWidthButton
        if not enabled:
            for button in buttons: button.Value = False
        else:
            if not any([button.Value for button in buttons]):
                self.MarkSampleButton.Value = True
    mark_sample_enabled = property(get_mark_sample_enabled,set_mark_sample_enabled)            
        
    def OnMarkSampleClear(self,event):
        """Called when the 'Clear' button is pressed"""
        self.samples = []

    def OnAlignmentSetup(self,event):
        """Change parameters controlling click-centering procedure"""
        dlg = AlignmentSetup(self)
        dlg.CenterOnParent()
        dlg.Show()

    def OnCenter(self,event):
        """Inspect parameters controlling sample centering"""
        dlg = Center(self)
        dlg.CenterOnParent()
        dlg.Show()

    def OnShowIlluminationControls(self,event):
        show = event.Checked()
        self.ShowIlluminationControlsMenuItem.Check(show)
        self.Illumination_Panel.Shown = show
        self.Illumination_Panel_Shown = show
        self.layout.Layout()

    def OnShowAlignmentControls(self,event):
        show = event.Checked()
        self.ShowAlignmentControlsMenuItem.Check(show)
        self.Alignment_Panel.Shown = show
        self.Alignment_Panel_Shown = show
        self.layout.Layout()

    def OnShowEdgeControls(self,event):
        """Show/hide extra controls related to sample aligment"""
        self.show_edge_controls = not self.show_edge_controls

    def OnShowMarkSample(self,event):
        """Show/hide extra controls related to sample aligment"""
        self.show_mark_sample_controls = not self.show_mark_sample_controls

    def OnCalibrateRotation(self,event):
        """"Find the rotation center of the Phi axis"""
        dlg = CalibrateRotation(self)
        dlg.CenterOnParent()
        dlg.Show()

    def OnSampleCenter(self,event):
        """Define Rotation Center of an Object"""
        dlg = SampleCenter(self)
        dlg.CenterOnParent()
        dlg.Show()

    def OnPointerFunction(self,name,x,y,event):
        """Called when click-centering is activated and the left mouse
        button is pressed.
        (x,y) position of pointer relative to crosshair in mm
        event: 'down','drag' or 'up'"""
        ##debug("OnPointerFunction:%r,%r,%r,%r" % (name,x,y,event))
        # Convert from 2D camera to 3D diffractometer coordinates.
        # assuming the object is clicked on is in the focal plane of the camera.
        dx,dy,dz = self.dxdydz_of_camera_dxdydz(x,y,0)
        cx,cy,cz = self.xc-dx,self.yc-dy,self.zc-dz
        self.learn_center_register(cx,cy,cz,self.phic)
        if self.click_center_enabled and event == "down":
            self.current_center_x,self.current_center_y = \
                self.sample_center_xy(cx,cy,self.phic)
            self.xc,self.yc,self.zc = cx,cy,cz
        if self.mark_sample_enabled:
            ##if self.mark_sample_function in ("mark"):
            ##    self.xc,self.yc,self.zc = cx,cy,cz
            self.MarkSample(self.mark_sample_function,x,y,event)
        if name == "Define Edge" and event == "down": self.DefineEdge(x,y)

    def learn_center_register(self,x,y,z,phi):
        """Build history of clicks"""
        # Eliminate entries with duplicate phi in the history.
        def matches(phi1,phi2): return phi1 % 360 == phi2 % 360
        self.learn_center_history = [entry for entry in self.learn_center_history
            if hasattr(entry,"keys") and "phi" in entry and not matches(entry["phi"],phi)]
        # Add new click event to history.
        self.learn_center_history += [{"x":x,"y":y,"z":z,"phi":phi}]
        # Limit the number of entries in the history.
        self.learn_center_history = self.learn_center_history[-4:]

    def accept_rotation_center(self):
        """Use the new rotation center from the 'learn center' history"""
        from numpy import isnan
        cx,cy = self.rotation_center_xy_based_on_history
        if not any(isnan([cy,cy])): self.rotation_center = cx,cy
        self.calibration_z = self.zc

    @property
    def rotation_center_xy_based_on_history(self):
        """rotation center calculated from 'learn center' history"""
        from numpy import nan, average,sort,allclose
        try:
            if len(self.learn_center_history) < 4: cx,cy = nan,nan
            else:
                # Make sure the four angles are 90 deg appart.
                phi = [entry["phi"] for entry in self.learn_center_history[0:4]]
                phi = sort(phi)-min(phi)
                if not allclose(phi,[0,90,180,270]): cx,cy = nan,nan
                else: 
                    # If the four phi angle are 90 deg appart, the center is the
                    # average of the x and y coordinates.
                    x = [entry["x"] for entry in self.learn_center_history[0:4]]
                    y = [entry["y"] for entry in self.learn_center_history[0:4]]
                    cx,cy = average(x),average(y)
        except Exception,msg:
            warn("rotation_center_xy_based_on_history: %r: %s" %
                 (self.learn_center_history,msg))
            cx,cy = nan,nan
        return cx,cy

    def get_camera_sample_xc(self):
        """The shift of the sample relative to the sample position at
        (X,Y) = (0,0), along the to the camera viewing direction"""
        x,y = self.camera_xy(self.xc,self.yc)
        return x
    def set_camera_sample_xc(self,value):
        x,y = self.camera_xy(self.xc,self.yc)
        x = value
        self.xc,self.yc = self.diffractometer_xy(x,y)
    camera_sample_xc = property(get_camera_sample_xc,set_camera_sample_xc)

    def get_camera_sample_yc(self):
        """The shift of the sample relative to the sample position at
        (X,Y) = (0,0), orthognal to the camera viewing direction"""
        x,y = self.camera_xy(self.xc,self.yc)
        return y
    def set_camera_sample_yc(self,value):
        x,y = self.camera_xy(self.xc,self.yc)
        y = value
        self.xc,self.yc = self.diffractometer_xy(x,y)
    camera_sample_yc = property(get_camera_sample_yc,set_camera_sample_yc)

    def get_camera_rotation_center_xc(self):
        """Phi motor rotation axis, at (X,Y) = (0,0),
        along the to the camera viewing direction"""
        x,y = self.camera_xy(*self.rotation_center)
        return x
    def set_camera_rotation_center_xc(self,value):
        x,y = self.camera_xy(*self.rotation_center)
        x = value
        self.rotation_center = self.diffractometer_xy(x,y)
    camera_rotation_center_xc = property(get_camera_rotation_center_xc,
        set_camera_rotation_center_xc)

    def get_camera_rotation_center_yc(self):
        """Phi motor rotation axis, at (X,Y) = (0,0),
        orthognal to the camera viewing direction"""
        x,y = self.camera_xy(*self.rotation_center)
        return y
    def set_camera_rotation_center_yc(self,value):
        x,y = self.camera_xy(*self.rotation_center)
        y = value
        self.rotation_center = self.diffractometer_xy(x,y)
    camera_rotation_center_yc = property(get_camera_rotation_center_yc,
        set_camera_rotation_center_yc)

    def get_camera_sample_center_xc(self):
        """Phi motor rotation axis, at (X,Y) = (0,0),
        along the to the camera viewing direction"""
        x,y = self.camera_xy(self.current_center_x,self.current_center_y)
        return x
    def set_camera_sample_center_xc(self,value):
        x,y = self.camera_xy(self.current_center_x,self.current_center_y)
        x = value
        self.current_center_x,self.current_center_y = self.diffractometer_xy(x,y)
    camera_sample_center_xc = property(get_camera_sample_center_xc,
        set_camera_sample_center_xc)

    def get_camera_sample_center_yc(self):
        """Phi motor rotation axis, at (X,Y) = (0,0),
        orthognal to the camera viewing direction"""
        x,y = self.camera_xy(self.current_center_x,self.current_center_y)
        return y
    def set_camera_sample_center_yc(self,value):
        x,y = self.camera_xy(self.current_center_x,self.current_center_y)
        y = value
        self.current_center_x,self.current_center_y = self.diffractometer_xy(x,y)
    camera_sample_center_yc = property(get_camera_sample_center_yc,
        set_camera_sample_center_yc)

    def camera_xy(self,x,y):
        """Transform from diffractometer to camera coordinates.
        Return value: (x',y')
        x': distance from the camera plane of focus in the camera viewing direction
        (positive = far, negative = close)
        y': projection in the camara plan of focus
        (positive = up in the image, negative = down in the image)"""
        from numpy import sin,cos,radians
        phi = -self.camera_angle
        xp = self.x_scale*x*cos(radians(phi)) - self.y_scale*y*sin(radians(phi))
        yp = self.x_scale*x*sin(radians(phi)) + self.y_scale*y*cos(radians(phi))
        return xp,yp

    def diffractometer_xy(self,xp,yp):
        """Transform from camera to diffractometer coordinates.
        Return value: (x,y)"""
        from numpy import sin,cos,radians
        phi = -self.camera_angle
        x = ( xp*cos(radians(phi)) + yp*sin(radians(phi))) / self.x_scale
        y = (-xp*sin(radians(phi)) + yp*cos(radians(phi))) / self.y_scale
        return x,y

    @property
    def rotation_axis_offset(self):
        """Vertical offset of the rotation axis with respect to
        the crosshair in units of mm"""
        from numpy import sin,cos,radians
        x,y = self.x,self.y
        cx,cy = self.rotation_center
        dx,dy = x-cx,y-cy
        phi = -self.camera_angle
        d = self.x_scale*dx*sin(radians(phi)) + self.y_scale*dy*cos(radians(phi))
        return d

    @property
    def rotation_axis_depth(self):
        """Distance of the rotation axis from the camera focal plane
        in viewing direction in units of mm"""
        from numpy import sin,cos,radians
        x,y = self.x,self.y
        cx,cy = self.rotation_center
        dx,dy = x-cx,y-cy
        phi = -self.camera_angle
        d = -self.x_scale*dx*cos(radians(phi)) + self.y_scale*dy*sin(radians(phi))
        return d

    @property
    def sample_centered_xy(self):
        """How does the sample need to be translated such that the click
        center is on the crosshair?"""
        return self.sample_center_xy_phi(self.phic)

    def sample_center_xy_phi(self,phi):
        """Where does the sample need to be translated such that the current
        center is on the crosshair?"""
        from numpy import degrees,arctan2,sqrt,sin,cos,radians
        x0,y0 = self.current_center_x,self.current_center_y
        r = sqrt(x0**2+y0**2)
        phi0 = degrees(arctan2(-y0,x0)) % 360
        phi1 = (phi0 + phi) % 360
        dx =   r*cos(radians(phi1))
        dy =  -r*sin(radians(phi1))
        cx,cy = self.rotation_center
        x,y = cx+dx,cy+dy
        return x,y

    @property
    def current_sample_center_xy(self):
        """x and y offset of the sample center from the rotation axis
        at phi = 0 based on the current values of x,y and phi,
        assuming the sample is centered in te crosshair and in focus."""
        return self.sample_center_xy(self.xc,self.yc,self.phic)

    def sample_center_xy(self,x,y,phi):
        """x and y offset of the sample center from the rotation axis
        at phi = 0 based
        assuming the sample is centered in the crosshair and in focus.
        as x,y,phi"""
        # Transform from x,y,phi to x0,y0,0
        from numpy import degrees,arctan2,sqrt,sin,cos,radians
        cx,cy = self.rotation_center
        dx,dy = x-cx,y-cy
        r = sqrt(dx**2+dy**2)
        phi1 = degrees(arctan2(-dy,dx)) % 360
        phi0 = phi1 - phi
        x0 =   r*cos(radians(phi0))
        y0 =  -r*sin(radians(phi0))
        return x0,y0

    def sample_camera_xy(self,x,y,z):
        """Vertical offset of the with respect to the crosshair
        of a sample a x,y with respect to the rotation axis at phi=0"""
        from numpy import sin,cos,radians,degrees,arctan2,sqrt
        r = sqrt(x**2+y**2)
        phi0 = degrees(arctan2(-y,x)) % 360
        phi = phi0 + self.phi - self.camera_angle
        d = r*sin(radians(phi))
        offset = d + self.rotation_axis_offset
        cz = z + self.calibration_z
        cx,cy = self.camera_position(cz,offset)
        return cx,cy

    def sample_camera_xyz(self,x,y,z):
        """Horizontal and vertical offset with respect to the crosshair
        of a sample a x,y with respect to the rotation axis at phi=0
        the Third coordinate if te out of plane distance in camera viewing
        direction, with respect to the focal plane of the camera."""
        from numpy import sin,cos,radians,degrees,arctan2,sqrt
        r = sqrt(x**2+y**2)
        phi0 = degrees(arctan2(-y,x)) % 360
        phi = phi0 + self.phi - self.camera_angle
        cy0 =  r*sin(radians(phi))
        cz0 = -r*cos(radians(phi))
        cy1 = cy0 + self.rotation_axis_offset
        cz  = cz0 + self.rotation_axis_depth
        cx1 = z + self.calibration_z
        cx,cy = self.camera_position(cx1,cy1)
        return cx,cy,cz

    @property
    def sample_center_camera_xy(self):
        """Position of sample with respect to the crosshair, as seen by the
        camera."""
        offset = self.sample_center_offset
        cz = self.click_center_z + self.calibration_z
        x,y = self.camera_position(cz,offset)
        return x,y

    @property
    def sample_center_r(self):
        """Distance of the sample center from the rotation axis"""
        from numpy import sqrt
        x,y = self.current_center_x,self.current_center_y
        r = sqrt(x**2+y**2)
        return r

    @property
    def sample_center_direction_angle(self):
        """Direction of the sameple from the roation center at phi=0"""
        from numpy import degrees,arctan2
        x,y = self.current_center_x,self.current_center_y
        phi = degrees(arctan2(-y,x)) % 360
        return phi

    @property
    def sample_center_offset(self):
        """Vertical offset of the sample center with respect to the crosshair"""
        from numpy import sin,cos,radians,degrees,arctan2,sqrt
        x,y = self.click_center_x,self.click_center_y
        r = sqrt(x**2+y**2)
        phi0 = degrees(arctan2(-y,x)) % 360
        phi = phi0 + self.phi - self.camera_angle
        d = r*sin(radians(phi))
        offset = d + self.rotation_axis_offset
        return offset

    def get_x_translation_angle(self):
        """The angle between the camera viewing direction and the
        X translation, in units of degrees"""
        if self.xy_rotating:
            phi = self.phic - self.camera_angle
        else:
            phi = -self.camera_angle
        return phi
    x_translation_angle = property(get_x_translation_angle)

    def get_y_translation_angle(self):
        """The angle between the camera viewing direction and the
        Y translation, in units of degrees"""
        if self.xy_rotating:
            phi = self.phic - self.camera_angle - 90
        else:
            phi = -self.camera_angle - 90
        return phi
    y_translation_angle = property(get_y_translation_angle)

    def dxdydz_of_camera_dxdydz(self,camera_dx,camera_dy,camera_dz):
        """Motor translation based on camera viewing plane translation.
        camera_dx: horizontal direction in  mm, pos = left
        camera_dy: vertical direction, in mm, pos = up
        camera_dz: along the viewing direction (focus direction) in mm, pos = farther
        return value: motor dx,dy,dz in mm"""
        dz = self.z_scale * camera_dx
        x0,y0 = self.camera_xy(0,0)
        dx,dy = self.diffractometer_xy(x0-camera_dz,y0+camera_dy)
        return dx,dy,dz

    def camera_xyz(self,x,y,z):
        """Where is the object the is centers at motor position (x,y,z)
        currently in the field of view of te camera?
        return value: x0,y0,z0
        x0 = horizonal offset from crosshair in mm
        y0 = vertical offset from crosshair in mm
        z0 = distance fro mcal place in camera direction in mm"""
        dx,dy,dz = x-self.xc,y-self.yc,z-self.zc
        z0,y0 = self.camera_xy(dx,dy) # depth, vertical offset, sign?
        x0 = -dz * self.z_scale # sign?
        return x0,y0,z0

    def DefineEdge(self,x,y):
        """x,y position of mouse clock with respect to cross hair in mm.
        x: positive = right, y: positive = up"""
        from numpy import rint
        phi = (self.phic - self.camera_angle) % 360
        z = self.zc - self.z_scale * x
        # Round to the next grid point
        z0 = self.GridOffset; dz = self.GridXSpacing
        z = rint((z-z0)/dz)*dz+z0
        offset = y
        self.AddSupportPoint(phi,z,offset)

    def AddSupportPoint(self,phi,z,offset):
        from numpy import array,where,concatenate
        x,y = self.xc,self.yc
        if len(self.support_points) > 0:
            PHI,X,Y,Z,OFFSET = array(self.support_points).T
        else: PHI,X,Y,Z,OFFSET = array([[],[],[],[],[]])
        existing_points = where((PHI == phi) & (Z == z))[0]
        if len(existing_points) > 0:
            OFFSET[existing_points] = offset
        else:
            PHI = concatenate((PHI,[phi]))
            X = concatenate((X,[x]))
            Y = concatenate((Y,[y]))
            Z = concatenate((Z,[z]))
            OFFSET = concatenate((OFFSET,[offset]))
        self.support_points = zip(PHI,X,Y,Z,OFFSET)
        
    def ResetEdgeDefinition(self):
        """Clear all support points"""
        self.support_points = []

    def UndoLastEdgeDefinition(self):
        "Clear last support point"
        if len(self.support_points) > 0: self.support_points.pop()
        
    def MarkSample(self,function,x,y,event):
        """x,y image coordinates wirth respect to the camera center.
        x: positive = right, y: positive = up
        event: 'up','drag' or 'down'"""
        ##debug("MarkSample %r,%+.3f,%+.3f,%r" % (self.mark_sample_function,x,y,event))

        click_dist = 0.02 # mm, should change with zoom
        # Convert from 2D camera to 3D diffractometer coordinates.
        # assuming the object is clicked on is in the focal plane of the camera.
        sx,sy,sz = self.sample_xyz_of_camera_xyz(x,y,0)

        if function  not in ["width","delete"]:
            if event == "down":
                # Find the closest control point
                self.current_sample = None
                dmin = 1e9
                for i in range(0,len(self.samples)):
                    for point in ["start","end"]:
                        tx,ty = self.sample_camera_xy(*self.samples[i][point])
                        d = distance((x,y),(tx,ty))
                        dmin = min(d,dmin)
                for i in range(0,len(self.samples)):
                    for point in ["start","end"]:
                        tx,ty = self.sample_camera_xy(*self.samples[i][point])
                        d = distance((x,y),(tx,ty))
                        if d == dmin and dmin < click_dist:                      
                             self.current_sample = i
                             self.current_sample_point = point
                if self.current_sample is None:
                    self.samples += [{"start":(sx,sy,sz),"end":(sx,sy,sz)}]
                    self.current_sample = len(self.samples) - 1
                    self.current_sample_point = "end"
            elif event == "drag" or event == "up":
                if self.current_sample is not None and len(self.samples) > 0:
                    # Maintain depth with respect to camera plane while dragging.
                    ##debug(" x, y, z = %+.3f,%+.3f,%+.3f" % ( x, y, 0))
                    sx,sy,sz = self.samples[self.current_sample][self.current_sample_point]
                    ##debug("sx,sy,sz = %+.3f,%+.3f,%+.3f" % (sx,sy,sz))
                    ox,oy,oz = self.sample_camera_xyz(sx,sy,sz)
                    ##debug("ox,oy,oz = %+.3f,%+.3f,%+.3f" % (ox,oy,oz))
                    x,y,z = x,y,oz
                    ##debug(" x, y, z = %+.3f,%+.3f,%+.3f" % ( x, y, 0))
                    sx,sy,sz = self.sample_xyz_of_camera_xyz(x,y,z)
                    ##debug("sx,sy,sz = %+.3f,%+.3f,%+.3f" % (sx,sy,sz))
                    self.samples[self.current_sample][self.current_sample_point] = sx,sy,sz
        if function == "width":
            if self.current_sample is not None and len(self.samples) > 0:
                sample = self.samples[self.current_sample]
                p1 = self.sample_camera_xy(*sample["start"])
                p2 = self.sample_camera_xy(*sample["end"])
                self.sample_r = point_line_distance((x,y),(p1,p2))
                ##self.sample_r = point_line_distance((sx,sy,sz),(sample["start"],sample["end"]))
        if function == "delete":
            self.current_sample = None
            dmin = 1e9
            for i in range(0,len(self.samples)):
                sample = self.samples[i]
                p1 = self.sample_camera_xy(*sample["start"])
                p2 = self.sample_camera_xy(*sample["end"])
                d = point_line_distance((x,y),(p1,p2))
                dmin = min(d,dmin)
            for i in range(0,len(self.samples)):
                sample = self.samples[i]
                p1 = self.sample_camera_xy(*sample["start"])
                p2 = self.sample_camera_xy(*sample["end"])
                d = point_line_distance((x,y),(p1,p2))
                if d == dmin and dmin < click_dist:
                    self.current_sample = i
            if self.current_sample is not None:
                i = self.current_sample
                self.samples = self.samples[0:i]+self.samples[i+1:]
            
    def sample_xyz_of_camera_xyz(self,x,y,z):
        """x,y,z coordinates in mm realtive to the rotation center.
        x camera horizonal in mm
        y camera vertical in mm
        z depth relative to the camera focal plane in viewing direction in mm
        """
        dx,dy,dz = self.dxdydz_of_camera_dxdydz(x,y,z)
        cx,cy,cz = self.xc-dx,self.yc-dy,self.zc-dz
        sx,sy,sz = list(self.sample_center_xy(cx,cy,self.phic))+[cz-self.calibration_z]
        return sx,sy,sz

    def z_range(self):
        """translation range along phi axis for data collection.
        Defined as range over which support points have been entered"""
        from numpy import array
        if len(self.support_points) == 0: return self.z,self.z
        PHI,X,Y,Z,OFFSET = array(self.support_points).T
        return min(Z),max(Z)

    def camera_position(self,Z,offset):
        """Transform from Z, offset to camera viewing plane 2D
        coordinates, using the current settigs of X,Y,Z, and Phi."""
        x = (self.z - Z) * self.z_scale
        y = offset
        return x,y

    def current_offset(self,phi,x0,y0,offset0):
        """Transform offset0 measured at (x0,y0) and angle phi0
        to offset at current position (X,Y)
        The inputs phi,x0,y0,offset0 may by numpy arrays."""
        cx,cy = self.xc,self.yc
        return self.relative_offset(phi,x0,y0,offset0,cx,cy)

    def relative_offset(self,phi,x0,y0,offset0,cx,cy):
        """Transform offset0 measured at (x0,y0) and angle phi0
        to offset with respect to position (cy,cy)"""
        from numpy import sin,cos,radians
        x = x0 + offset0*sin(radians(phi))
        y = y0 - offset0*cos(radians(phi))
        offset = (x-cx)*sin(radians(phi)) - (y-cy)*cos(radians(phi))
        return offset

    def interpolated_offset(self,phi,z):
        """Interpolate the offset as function of phi and z, using measured
        support points
        The returned offset are with respect to the center of the sample
        as defined by visual click centering."""
        from numpy import array,concatenate
        PHI,X,Y,Z,OFFSET = array(self.support_points).T
        PHI = concatenate((PHI-360,PHI,PHI+360))
        Z = concatenate((Z,Z,Z))
        OFFSET = concatenate((OFFSET,OFFSET,OFFSET))
        return interpolate_2D(PHI,Z,OFFSET,phi % 360,z)


class Illumination_Panel(wx.Panel):
    """Light switch for LED illuminator controlled by timing system"""
    def __init__(self,parent):
        wx.Panel.__init__(self,parent)
        # Controls - Illumination Panel
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.Sizer = hbox
        
        label = wx.StaticText(self,label="Illumination:")
        hbox.Add (label,flag=wx.ALIGN_CENTER)

        self.Illumination_State = wx.ToggleButton(self,label="On",size=(45,-1))
        hbox.Add (self.Illumination_State,flag=wx.ALIGN_CENTER)
        self.Bind (wx.EVT_TOGGLEBUTTON,self.OnIllumination_State,self.Illumination_State)
        from instrumentation import timing_system
        timing_system.scl.override_state.monitor(self.IlluminationUpdate)
   
        self.Illumination_PP_Control = wx.CheckBox(self,label="PP Controlled")
        hbox.Add (self.Illumination_PP_Control,flag=wx.ALIGN_CENTER)
        self.Bind (wx.EVT_CHECKBOX,self.OnIllumination_PP_Control,self.Illumination_PP_Control)
        from instrumentation import timing_system
        timing_system.scl.override.monitor(self.IlluminationUpdate)

    def IlluminationUpdate(self):
        """Handle register change"""
        State = self.Illumination_State
        PP_Control = self.Illumination_PP_Control
        from instrumentation import timing_system
        if timing_system.online:
            state = timing_system.scl.override_state.value
            PP_controlled = not timing_system.scl.override.value
            State.Value = state
            PP_Control.Value = PP_controlled
            State.Enabled = not PP_controlled
            State.Label = "On" if state == True else "Off"
        else:
            PP_Control.Enabled = False
            State.Enabled = False
            State.Label = "Offline"
            
    def OnIllumination_State(self,event):
        """Handle toogle button on/off"""
        value = event.IsChecked()
        info("Illumination_State: %r" % value)
        from instrumentation import timing_system
        timing_system.scl.override_state.value = value
    
    def OnIllumination_PP_Control(self,event):
        """Handle toogle button on/off"""
        value = event.IsChecked()
        info("Illumination_PP_Control: %r" % value)
        from instrumentation import timing_system
        timing_system.scl.override.value = not value


def motor(name):
    """name: EPICS PV or Python motor defined in 'id14.py'"""
    if not ":" in name:
        exec("from id14 import *")
        try: return eval(name)
        except: pass
    from EPICS_motor import motor
    return motor(name)

def interpolate_2D(X,Y,Z,x,y):
    """
    Z is a scalar function of the variables x and y.
    X,Y: vector of length N, support points
    Z: vector of length N, function values at support points
    x,y: where to evaluate the function Z
    """
    from numpy import array,unique
    X,Y,Z = array(X),array(Y),array(Z)
    UY = unique(Y)
    UZ = [interpolate(zip(X[Y==uy],Z[Y==uy]),x) for uy in UY]
    return interpolate(zip(UY,UZ),y)
    
def interpolate_2D_v1(X,Y,Z,x,y):
    """
    Z is a scalar function of the variables x and y.
    X,Y: vector of length N, support points
    Z: vector of length N, function values at support points
    x,y: where to evaluate the function Z
    """
    from numpy import array,unique
    X,Y,Z = array(X),array(Y),array(Z)
    UX = unique(X)
    UZ = [interpolate(zip(Y[X==ux],Z[X==ux]),y) for ux in UX]
    return interpolate(zip(UX,UZ),x)

def interpolate_2D_v2(X,Y,Z,x,y):
    """
    Z is a scalar function of the variables x and y.
    X,Y: vector of length N, support points
    Z: vector of length N, function values at support points
    x,y: where to evaluate the function Z
    """
    from numpy import array,argsort,isnan,nan
    from matplotlib.mlab import griddata

    X,Y,Z = array(X),array(Y),array(Z)
    if len(X) == 0: return nan
    # The Delauney triangulation routine used by 'griddata' cannot
    # handle the case of supprt points lying on a straight line.
    # In this case, use 1D intepolation.
    if all(X == X[0]): return interpolate(zip(Y,Z),y) 
    if all(Y == Y[0]): return interpolate(zip(X,Z),x) 
    try: z = griddata(X,Y,Z,array([x]),array([y]))
    except: z = nan
    # 'griddata' returnes a masked array
    z = float(array(z)) # avoid "Warning: converting a masked element to nan."
    # 'griddata' does no extrapolation.
    # If point is outside convex hull defined by input data, it returns nan.
    if not isnan(z): return z
    # Find the find closes support points in phi and z
    nearest = argsort((X-x)**2+(Y-y)**2)[0]
    return Z[nearest]

def interpolate(xy_data,xval):
    "Linear interpolation"
    from numpy import array,argsort,nan
    x = array(xvals(xy_data)); y = array(yvals(xy_data)); n = len(xy_data)
    if n == 0: return nan
    if n == 1: return y[0]
    order = argsort(x)
    x = x[order]; y= y[order]
    
    for i in range (1,n):
        if x[i]>xval: break
    if x[i-1]==x[i]: return (y[i-1]+y[i])/2. 
    yval = y[i-1]+(y[i]-y[i-1])*(xval-x[i-1])/(x[i]-x[i-1])
    return yval

def xvals(xy_data):
    "xy_data = list of (x,y)-tuples. Teturns list of x values only."
    xvals = []
    for i in range (0,len(xy_data)): xvals.append(xy_data[i][0])
    return xvals  

def yvals(xy_data):
    "xy_data = list of (x,y)-tuples. Returns list of y values only."
    yvals = []
    for i in range (0,len(xy_data)): yvals.append(xy_data[i][1])
    return yvals  


class AlignmentSetup (wx.Dialog):
    """Allows the use to configure camera properties"""
    def __init__ (self,parent):
        wx.Dialog.__init__(self,parent,-1,"Alignment Setup")
        # Controls
        style = wx.TE_PROCESS_ENTER

        self.X = ComboBox(self,size=(160,-1),style=style,
            choices=["SampleX","NIH:SAMPLEX","14IDB:ESP300X"])
        self.Y = ComboBox(self,size=(160,-1),style=style,
            choices=["SampleY","NIH:SAMPLEY","14IDB:ESP300Y"])
        self.Z = ComboBox(self,size=(160,-1),style=style,
            choices=["SampleZ","NIH:SAMPLEZ","14IDB:ESP300Z"])
        self.Phi = ComboBox(self,size=(160,-1),style=style,
            choices=["SamplePhi","NIH:SAMPLEPHI","14IDB:m16"])

        self.XYType = ComboBox(self,size=(160,-1),style=style,
            choices=["rotating","stationary"])

        self.CameraAngle = TextCtrl(self,size=(160,-1),style=style)
        self.XDesc = wx.StaticText(self)
        self.XSign = ComboBox(self,size=(160,-1),style=style,
            choices=["up","down"])
        self.YDesc = wx.StaticText(self)
        self.YSign = ComboBox(self,size=(160,-1),style=style,
            choices=["up","down"])
        self.ZSign = ComboBox(self,size=(160,-1),style=style,
            choices=["right","left"])
        self.PixelSize = TextCtrl(self,size=(160,-1),style=style)

        self.RotationCenterX = TextCtrl(self,size=(160,-1),style=style)
        self.RotationCenterY = TextCtrl(self,size=(160,-1),style=style)
        self.CalibrationZ = TextCtrl(self,size=(160,-1),style=style)
        # Callbacks
        self.Bind(wx.EVT_TEXT_ENTER,self.OnEnter)
        self.Bind(wx.EVT_COMBOBOX,self.OnEnter)

        # Layout
        layout = wx.BoxSizer()
        grid = wx.FlexGridSizer(cols=2,hgap=5,vgap=5)
        flag = wx.ALIGN_CENTER_VERTICAL
        
        label = "X Translation:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.X,flag=flag)
        label = "Y Translation:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.Y,flag=flag)
        label = "Z Translation:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.Z,flag=flag)
        label = "Phi Rotation:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.Phi,flag=flag)
        label = "XY Translation Type:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.XYType,flag=flag)
        
        label = "Y is orthogonal to viewing direction at:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.CameraAngle,flag=flag)
        grid.Add (self.YDesc,flag=flag)
        grid.Add (self.YSign,flag=flag)
        grid.Add (self.XDesc,flag=flag)
        grid.Add (self.XSign,flag=flag)
        label = "Z direction:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.ZSign,flag=flag)
        label = "Pixel size:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.PixelSize,flag=flag)

        label = "Rotation Axis X:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.RotationCenterX,flag=flag)
        label = "Rotation Axis Y:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.RotationCenterY,flag=flag)
        label = "Calibration Z:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.CalibrationZ,flag=flag)

        # Leave a 10-pixel wide space around the panel.
        layout.Add (grid,flag=wx.EXPAND|wx.ALL,border=10)

        self.SetSizer(layout)
        self.Fit()

        self.update()

    def update(self,Event=0):
        parent = self.Parent

        self.X.Value = parent.x_motor_name
        self.Y.Value = parent.y_motor_name
        self.Z.Value = parent.z_motor_name
        self.Phi.Value = parent.phi_motor_name
        self.XYType.Value = "rotating" if parent.xy_rotating else "stationary"

        self.CameraAngle.Value = str(parent.camera_angle)+deg
        self.XDesc.Label = "X direction at %g%s:" %\
            (parent.camera_angle-90,deg)
        self.XSign.Value = "up" if parent.x_scale > 0 else "down"
        self.YDesc.Label = "Y direction at %g%s:" %\
            (parent.camera_angle,deg)
        self.YSign.Value = "up" if parent.y_scale > 0 else "down"
        self.ZSign.Value = "right" if parent.z_scale > 0 else "left"
        self.PixelSize.Value = str(parent.PixelSize*1000)+" um"

        x,y = parent.rotation_center
        self.RotationCenterX.Value = "%.4f mm" % x
        self.RotationCenterY.Value = "%.4f mm" % y
        self.CalibrationZ.Value  = "%.4f mm" % parent.calibration_z

        # Relaunch yourself.
        self.update_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER,self.update,self.update_timer)
        self.update_timer.Start(2000,oneShot=True)

    def OnEnter(self,event):
        parent = self.Parent

        parent.x_motor_name = self.X.Value 
        parent.y_motor_name = self.Y.Value 
        parent.z_motor_name = self.Z.Value 
        parent.phi_motor_name = self.Phi.Value 
        parent.xy_rotating = True if self.XYType.Value == "rotating" else False

        value = self.CameraAngle.Value.replace(deg,"")
        try: parent.camera_angle = float(eval(value))
        except: pass

        parent.x_scale = 1 if self.XSign.Value == "up" else -1
        parent.y_scale = 1 if self.YSign.Value == "up" else -1
        parent.z_scale = 1 if self.ZSign.Value == "right" else -1
        
        value = self.PixelSize.Value.replace("um","")
        try: value = float(eval(value))/1000
        except: pass
        parent.PixelSize = value

        x,y = parent.rotation_center
        value = self.RotationCenterX.Value.replace("mm","")
        try: x = float(eval(value))
        except: pass
        value = self.RotationCenterY.Value.replace("mm","")
        try: y = float(eval(value))
        except: pass
        parent.rotation_center = x,y
        value = self.CalibrationZ.Value.replace("mm","")
        try: parent.calibration_z = float(eval(value))
        except: pass

        self.update()
        
class Center(wx.Dialog):
    """Click-Centering"""
    def __init__ (self,parent):
        wx.Dialog.__init__(self,parent,-1,"Center")
        # Controls
        style = wx.TE_PROCESS_ENTER

        self.SampleCenterX = TextCtrl(self,size=(160,-1),style=style)
        self.SampleCenterY = TextCtrl(self,size=(160,-1),style=style)
        self.SampleCenterZ = TextCtrl(self,size=(160,-1),style=style)

        self.CurrentCenterX = TextCtrl(self,size=(160,-1),style=style)
        self.CurrentCenterY = TextCtrl(self,size=(160,-1),style=style)
        self.CurrentCenterZ = TextCtrl(self,size=(160,-1),style=style)

        self.Bind(wx.EVT_TEXT_ENTER,self.OnEnter)

        # Layout
        layout = wx.BoxSizer()
        grid = wx.FlexGridSizer(cols=2,hgap=5,vgap=5)
        flag = wx.ALIGN_CENTER_VERTICAL

        label = "Sample Center X:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.SampleCenterX,flag=flag)
        label = "Sample Center Y:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.SampleCenterY,flag=flag)
        label = "Sample Center Z:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.SampleCenterZ,flag=flag)

        label = "Current Center X:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.CurrentCenterX,flag=flag)
        label = "Current Center Y:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.CurrentCenterY,flag=flag)
        label = "Current Center Z:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.CurrentCenterZ,flag=flag)

        # Leave a 10-pixel wide space around the panel.
        layout.Add (grid,flag=wx.EXPAND|wx.ALL,border=10)

        self.SetSizer(layout)
        self.Fit()

        self.update()

    def update(self,Event=0):
        parent = self.Parent

        self.SampleCenterX.Value = "%.4f mm" % parent.click_center_x
        self.SampleCenterY.Value = "%.4f mm" % parent.click_center_y
        self.SampleCenterZ.Value = "%.4f mm" % parent.click_center_z

        self.CurrentCenterX.Value = "%.4f mm" % parent.current_center_x
        self.CurrentCenterY.Value = "%.4f mm" % parent.current_center_y
        self.CurrentCenterZ.Value = "%.4f mm" % (parent.zc - parent.calibration_z)

        # Relaunch yourself.
        self.update_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER,self.update,self.update_timer)
        self.update_timer.Start(2000,oneShot=True)

    def OnEnter(self,event):
        parent = self.Parent

        value = self.SampleCenterX.Value.replace("mm","")
        try: parent.click_center_x = float(eval(value))
        except: pass
        value = self.SampleCenterY.Value.replace("mm","")
        try: parent.click_center_y = float(eval(value))
        except: pass
        value = self.SampleCenterZ.Value.replace("mm","")
        try: parent.click_center_z = float(eval(value))
        except: pass

        value = self.CurrentCenterX.Value.replace("mm","")
        try: parent.current_center_x = float(eval(value))
        except: pass
        value = self.CurrentCenterY.Value.replace("mm","")
        try: parent.current_center_y = float(eval(value))
        except: pass
        value = self.CurrentCenterZ.Value.replace("mm","")
        try: parent.zc = float(eval(value)) + parent.calibration_z
        except: pass

        self.update()

class CalibrateRotation(wx.Dialog):
    """Find the rotation center of the Phi axis"""
    def __init__ (self,parent):
        wx.Dialog.__init__(self,parent,-1,"Calibrate Rotation")
        # Controls
        self.History = TextCtrl(self,size=(180,75),
            style=wx.TE_MULTILINE|wx.TE_PROCESS_ENTER)
        self.Current = TextCtrl(self,size=(160,-1),style=wx.TE_PROCESS_ENTER)
        self.New = TextCtrl(self,size=(160,-1),style=wx.TE_PROCESS_ENTER)
        self.ClearButton = wx.Button (self,label="Clear")
        self.AcceptButton = wx.Button (self,label="Accept")
        # Callbacks
        self.Bind (wx.EVT_TEXT_ENTER,self.OnHistory,self.History)
        self.Bind (wx.EVT_BUTTON,self.OnClear,self.ClearButton)
        self.Bind (wx.EVT_BUTTON,self.OnAccept,self.AcceptButton)
        self.Bind (wx.EVT_CLOSE,self.OnClose)
        # Layout
        layout = wx.BoxSizer(wx.VERTICAL)
        layout.Add (self.History,flag=wx.EXPAND|wx.ALL,border=10)

        grid = wx.FlexGridSizer(cols=2,hgap=5,vgap=5)
        flag = wx.ALIGN_CENTER_VERTICAL
        grid.Add (wx.StaticText(self,label="New:"),flag=flag)
        grid.Add (self.New,flag=flag)
        grid.Add (wx.StaticText(self,label="Current:"),flag=flag)
        grid.Add (self.Current,flag=flag)
        layout.Add (grid,flag=wx.EXPAND|wx.ALL,border=10)
                   
        buttons = wx.BoxSizer(wx.HORIZONTAL)
        buttons.Add (self.ClearButton)
        buttons.AddSpacer(5)
        buttons.Add (self.AcceptButton)
        layout.Add (buttons,flag=wx.EXPAND|wx.ALL,border=10)

        self.SetSizer(layout)
        self.Fit()

        self.update()

    def update(self,Event=0):
        """Update displayed history"""
        self.History.Value = self.format_history(self.Parent.learn_center_history)
        xc,yc = self.Parent.rotation_center
        zc = self.Parent.calibration_z
        xn,yn = self.Parent.rotation_center_xy_based_on_history
        zn = self.Parent.zc
        self.New.Value     = "%.3f,%.3f,%.3f mm" % (xn,yn,zn)
        self.Current.Value = "%.3f,%.3f,%.3f mm" % (xc,yc,zc)
        self.ClearButton.Enabled = len(self.Parent.learn_center_history) > 0
        from numpy import allclose,isnan
        self.AcceptButton.Enabled = not allclose([xc,yc],[xn,yn]) and \
                                    not any(isnan([xn,yn]))

        # Relaunch yourself.
        self.update_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER,self.update,self.update_timer)
        self.update_timer.Start(2000,oneShot=True)

    def OnHistory(self,event):
        """Accept Edits"""
        try:
            history = self.parse_history(self.History.Value)
            self.Parent.learn_center_history = history
        except: pass
        self.update()
        
    def OnClear(self,event):
        """Reset click-center history"""
        self.Parent.learn_center_history = []
        self.update()

    def OnAccept(self,event):
        """Update sample center, using click-center history"""
        self.Parent.accept_rotation_center()
        self.update()

    def OnClose(self,event):
        """Called when the widnows's close button is clicked"""
        self.Destroy()

    @staticmethod
    def format_history(learn_center_history):
        """Convert history from list to string"""
        from numpy import nan
        keys = "x","y","z","phi"
        lines = []
        for entry in learn_center_history:
            values = []
            for key in keys:
                try: value = entry[key]
                except: value = nan
                values += [value]
            lines += [", ".join(["%.3f" % value for value in values])]
        s = "\n".join(lines)
        return s

    @staticmethod
    def parse_history(s):
        """Convert history from string to list"""
        from numpy import nan
        keys = "x","y","z","phi"
        learn_center_history = []
        for line in split(s,"\n"):
            values = line.split(",")
            entry = {}
            for i in range(0,len(keys)):
                try: entry[keys[i]] = eval(values[i])
                except: entry[keys[i]] = nan
            learn_center_history += [entry]            
        return learn_center_history

class SampleCenter(wx.Dialog):
    """Define Rotation Center of an Object"""
    def __init__ (self,parent):
        wx.Dialog.__init__(self,parent,-1,"Sample Center")
        # Controls
        self.Current = TextCtrl(self,size=(175,-1),style=wx.TE_PROCESS_ENTER)
        self.New = TextCtrl(self,size=(175,-1),style=wx.TE_PROCESS_ENTER)
        self.AcceptButton = wx.Button (self,label="Accept")
        # Callbacks
        self.Bind (wx.EVT_BUTTON,self.OnAccept,self.AcceptButton)
        self.Bind (wx.EVT_CLOSE,self.OnClose)
        # Layout
        layout = wx.BoxSizer(wx.VERTICAL)
        grid = wx.FlexGridSizer(cols=2,hgap=5,vgap=5)
        flag = wx.ALIGN_CENTER_VERTICAL
        grid.Add (wx.StaticText(self,label="New:"),flag=flag)
        grid.Add (self.New,flag=flag)
        grid.Add (wx.StaticText(self,label="Current:"),flag=flag)
        grid.Add (self.Current,flag=flag)
        layout.Add (grid,flag=wx.EXPAND|wx.ALL,border=10)
                   
        buttons = wx.BoxSizer(wx.HORIZONTAL)
        buttons.Add (self.AcceptButton)
        layout.Add (buttons,flag=wx.EXPAND|wx.ALL,border=10)

        self.SetSizer(layout)
        self.Fit()

        self.update()

    def update(self,Event=0):
        """Update displayed history"""
        x1,y1,z1 = self.Parent.click_center_x,self.Parent.click_center_y,\
            self.Parent.click_center_z
        x2,y2 = self.Parent.current_sample_center_xy
        z2 = self.Parent.zc - self.Parent.calibration_z
        self.Current.Value = "%.3f,%.3f,%.3f mm" % (x1,y1,z1)
        self.New.Value = "%.3f,%.3f,%.3f mm" % (x2,y2,z2)
        from numpy import allclose,isnan
        self.AcceptButton.Enabled = not allclose([x1,y1,z1],[x2,y2,z2]) \
            and not any(isnan([x2,y2,z2]))

        # Relaunch yourself.
        self.update_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER,self.update,self.update_timer)
        self.update_timer.Start(2000,oneShot=True)

    def OnAccept(self,event):
        """Update sample center, using  history"""
        self.Parent.current_center_x,self.Parent.current_center_y = \
            self.Parent.click_center_x,self.Parent.click_center_y = \
            self.Parent.current_sample_center_xy
        self.Parent.click_center_z = self.Parent.zc - self.Parent.calibration_z
        self.update()

    def OnClose(self,event):
        """Called when the widnows's close button is clicked"""
        self.Destroy()

    @staticmethod
    def parse_history(s):
        """Convert history from string to list"""
        return eval(s)


def point_line_distance (P,line):
    """Distance of a point to a line segment of finite length
    P: (x,y,z)
    line: ((x1,y1,z1),(x2,y2,z2))"""
    # Source: softsurfer.com/Archive/algorithm_0102/algorithm_0102.htm
    # 18 May 2007
    from numpy import dot
    P0 = line[0]; P1 = line[1]
    v = vector(P0,P1); w0 = vector(P0,P); w1 = vector(P1,P)
    # If the angle (P,P0,P1) is obtuse (>=90 deg), it is the distance to P0.
    if dot(w0,v) <= 0: return distance(P,P0)
    # If the angle(P,P1,P0) is obtuse (>=90 deg), it is the distance to P1.
    if dot(w1,v) >= 0: return distance(P,P1) 
    # Otherwise, it is the orthognal distance to the line.
    b = dot(w0,v) / float(dot(v,v))
    Pb = translate(P0,scale(v,b))
    return distance(P,Pb)

def vector(p1,p2):
    """Vector from point p1 to point p2
    p1: (x1,y1,z1)
    p2: (x2,y2,z2)"""
    from numpy import asarray
    p1,p2 = asarray(p1),asarray(p2)
    return p2-p1
    
def translate(p,v):
    """Applies the vector (vx,vy) to point (x,y)
    p: (x,y,z)
    v: (vx,vy,vz)"""
    from numpy import asarray
    p,v = asarray(p),asarray(v)
    return p+v

def scale(v,a):
    """Multiplies vector with scalar
    v: (x,y,z)"""
    from numpy import asarray
    v = asarray(v)
    return v*a

def distance(p1,p2):
    """Distance between two points p1 and p2
    p1: (x1,y1,z1)
    p2: (x2,y2,z2)"""
    from numpy import asarray
    p1,p2 = asarray(p1),asarray(p2)
    from numpy.linalg import norm
    return norm(p2-p1)


def interpreter():
    """For debugging: run a python interpreter"""
    from sys import stdin,stdout,stderr
    import readline
    readline.parse_and_bind("tab: complete")
    while True:
        try: command = raw_input(">>> ")
        except EOFError: break
        if command == "": break
        try: print("%r" % eval(command))
        except:
            try: exec(command)
            except Exception,msg: stderr.write("%s\n" % msg)


# The following is only executed when run as stand-alone application.
if __name__ == '__main__': # for testing
    from pdb import pm # for debugging
    name = "MicroscopeCamera"
    from redirect import redirect
    redirect(name,format="%(asctime)s %(levelname)s %(module)s.py, "
        "line %(lineno)d, %(funcName)s: %(message)s")
    ##import CameraViewer as x; x.DEBUG = True # for debugging
    ##import logging
    ##logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s")
    wx.app = wx.App(redirect=False)
    viewer = SampleAlignmentViewer(name=name)
    self = viewer # for debugging
    ##from thread import start_new_thread
    ##start_new_thread(interpreter,())
    wx.app.MainLoop()
