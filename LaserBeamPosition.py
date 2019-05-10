#!/usr/bin/env python
"""Active laser beam pointing stabilization.
Laser beam position measured on beam conditioning optics enclosure in
the 14IDB X-ray hutch.
Laser beam pointing corrected at the periscope mirror in the laser lab.

Calibration for PeriscopeH:
(7.612900 - 7.606900) mm / (-251 - 284) um = -0.000011 mm/um = -0.011 mm / mm
Calibration for PeriscopeV:
(8.230704 - 8.190704) mm / (-222 -190) um = -0.000097 mm/um = -0.097 mm / mm
"""

#from GigE_camera_SWIG import GigE_camera
from GigE_camera import GigE_camera
from CameraViewer import CameraViewer,xvals,yvals
from id14 import PeriscopeH,PeriscopeV
import wx

class LaserBeamPosition(CameraViewer):
    """An extension of the CameraViewer with controls for the laser beam position"
    Author: Friedrich Schotte, 11 Jun 2010 - 27 Sep 2014"""
    __version__ = "2.9.4" # wx.Colour

    settings = CameraViewer.settings + [
        "enable_beam_steering","enable_beam_stabilization","stepsize",
        "average_count","min_average_count","min_SN","postpone",
        "threshold","xthreshold","ythreshold",
        "xscale","yscale"]

    def __init__(self,*args,**keywords):
        # Defaults
        self.enable_beam_steering = True # show more controls below image
        self.enable_beam_stabilization = True # show more controls below image
        self.average_count = 10 # number of samples for running average
        self.min_average_count = 10 # number of samples to apply correction
        self.min_SN = 10.0 # signal/noise for center measurement to be valid
        self.threshold = 5.0 # multiple of sampling error to apply correction
        self.xthreshold = 0.050 # hor. error in mm on image to apply correction
        self.ythreshold = 0.010 # vert. error in mm on image to apply correction
        self.postpone = False # Wait until beam is off before moving the motor.
        self.xscale = -0.00733 # periscope mirror movement / beam movement
        self.yscale = -0.0833 # periscope mirror movement / beam movement
        self.stepsize = 0.01 # horiz. and vert. translation increment in mm

        CameraViewer.__init__(self,*args,**keywords)

        # Menus
        menuBar = self.GetMenuBar()
        menu = menuBar.GetMenu(3) # Camera menu
        menu.Append (402,"&Beam Steering/Stabilization...","Parameters for beam stabilization")
        self.Bind (wx.EVT_MENU,self.OnOptions,id=402)
        menu.Append (403,"&Enable Beam Steering",
            "Extra controls below image",wx.ITEM_CHECK)
        self.ShowBeamSteeringControlsMenuItem = menu.FindItemById(403)
        self.Bind (wx.EVT_MENU,self.OnShowBeamSteeringControls,id=403)
        menu.Append (404,"&Enable Beam Stabilization",
            "Extra controls below image",wx.ITEM_CHECK)
        self.ShowBeamStabilizationControlsMenuItem = menu.FindItemById(404)
        self.Bind (wx.EVT_MENU,self.OnShowBeamStabilizationControls,id=404)
        
        # Controls
        panel = self.beam_steering_panel = wx.Panel(self.panel)
        style = wx.TE_PROCESS_ENTER

        left = wx.ArtProvider.GetBitmap(wx.ART_GO_BACK)
        right = wx.ArtProvider.GetBitmap(wx.ART_GO_FORWARD)
        up = wx.ArtProvider.GetBitmap(wx.ART_GO_UP)
        down = wx.ArtProvider.GetBitmap(wx.ART_GO_DOWN)

        self.TranslateHLeft = wx.BitmapButton (panel,bitmap=left)
        self.Bind (wx.EVT_BUTTON,self.OnTranslateHLeft,self.TranslateHLeft)
        self.TranslateHRight = wx.BitmapButton (panel,bitmap=right)
        self.Bind (wx.EVT_BUTTON,self.OnTranslateHRight,self.TranslateHRight)
        
        self.TranslateVUp = wx.BitmapButton (panel,bitmap=up)
        self.Bind (wx.EVT_BUTTON,self.OnTranslateVUp,self.TranslateVUp)
        self.TranslateVDown = wx.BitmapButton (panel,bitmap=down)
        self.Bind (wx.EVT_BUTTON,self.OnTranslateVDown,self.TranslateVDown)

        choices = ["1000 um","500 um","200 um","100 um","50 um","20 um","10 um",
            "5 um","2 um","1 um"]
        self.StepSize = ComboBox (panel,style=style,choices=choices,
            size=(80,-1))
        self.Bind (wx.EVT_COMBOBOX,self.OnStepSize,self.StepSize)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnStepSize,self.StepSize)

        self.StabilizationActive = wx.ToggleButton (self.panel,
            label="Stabilization: Off      ")
        self.Bind (wx.EVT_TOGGLEBUTTON,self.OnStabilizationActive,
            self.StabilizationActive)

        self.Status = wx.StaticText(self.panel,size=(-1,35))

        # Layout
        self.layout.AddSpacer ((5,5))

        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        grid = wx.GridBagSizer (hgap=0,vgap=0)
        label = wx.StaticText(panel,label="Beam Steering:")
        grid.Add (label,(1,0),flag=wx.ALIGN_CENTER)
        grid.Add (self.TranslateHLeft,(1,1),flag=wx.ALIGN_CENTER)
        grid.Add (self.TranslateVUp,(0,2),flag=wx.ALIGN_CENTER)
        grid.Add (self.TranslateVDown,(2,2),flag=wx.ALIGN_CENTER)
        grid.Add (self.TranslateHRight,(1,3),flag=wx.ALIGN_CENTER)
        label = wx.StaticText(panel,label="Step:")
        grid.Add (label,(1,5),flag=wx.ALIGN_CENTER)
        grid.Add (self.StepSize,(1,6),flag=wx.ALIGN_CENTER)
        hbox.Add (grid,flag=wx.ALIGN_CENTER)
        panel.SetSizer(hbox)

        hbox2.Add (panel,flag=wx.ALIGN_CENTER)
        hbox2.AddSpacer ((5,5))
        hbox2.Add (self.StabilizationActive,flag=wx.ALIGN_CENTER)
        self.layout.Add (hbox2,flag=wx.ALIGN_CENTER)

        self.layout.Add (self.Status,flag=wx.ALIGN_CENTER|wx.EXPAND)

        self.layout.Layout()
        
        # Initialization
        self.StabilizationActive.DefaultForegroundColour = \
            self.StabilizationActive.ForegroundColour
        self.StabilizationActive.DefaultBackgroundColour = \
            self.StabilizationActive.BackgroundColour

        self.cancelled = False
        self.stabilization_active = False
        self.status = ""
        self.last_action = ""
        self.last_time = 0
        self.last = {"capturing": False,"stabilization_active": False}

        # Override the behaviour of 'CameraViewer' to keep acquiring even when
        # the window is minimized.
        self.image_update_needed = self.centering_image_update_needed

        self.log("Application started")
        self.log("Using "+self.settings_file())

        from threading import Thread
        self.task = Thread(target=self.monitor_beam_position)
        self.task.start()

        self.update()

    def update(self,event=None):
        # Show/Hide beam steering controls.
        self.ShowBeamSteeringControlsMenuItem.Check (
            self.enable_beam_steering)
        shown = self.beam_steering_panel.IsShown()
        if shown != self.enable_beam_steering:
            self.beam_steering_panel.Show (self.enable_beam_steering)
            self.layout.Layout()
        # Show/Hide beam stabilization controls.
        self.ShowBeamStabilizationControlsMenuItem.Check (
            self.enable_beam_stabilization)
        shown = self.StabilizationActive.IsShown()
        if shown != self.enable_beam_stabilization:
            self.StabilizationActive.Show (self.enable_beam_stabilization)
            self.Status.Show (self.enable_beam_stabilization)
            self.layout.Layout()
        # Update stepsize.
        value = "%g um" % (self.stepsize*1000)
        if self.StepSize.Value != value: self.StepSize.Value = value
        # Update button
        if self.stabilization_active:
            self.StabilizationActive.Label = "Stabilization: Active"
            self.StabilizationActive.BackgroundColour = (255,255,0)
            self.StabilizationActive.ForegroundColour = (255,0,0)
        else:
            self.StabilizationActive.Label = "Stabilization: Off      "
            self.StabilizationActive.BackgroundColour = \
                self.StabilizationActive.DefaultBackgroundColour
            self.StabilizationActive.ForegroundColour = \
                self.StabilizationActive.DefaultForegroundColour
        # Update status message.
        message = self.status.strip(", ")+"\n"
        from time import strftime,localtime,time
        if self.last_time:
            dt = time() - self.last_time
            if dt < 60: message += "%d s ago: " % dt
            elif dt < 3600: message += "%d:%02d min ago: " % (dt/60,dt%60)
            else: message += strftime("%b %d %H:%M:%S: ",localtime(self.last_time))
        message += self.last_action
        if self.Status.Label != message: self.Status.Label = message
        # Log activity
        capturing = self.camera.capturing
        if capturing != self.last["capturing"]:
            if capturing: self.log("Acquisistion started")
            else: self.log("Acquisistion stopped")
            self.last["capturing"] = capturing
        if self.stabilization_active != self.last["stabilization_active"]:
            if self.stabilization_active: self.log("Stabilization active")
            else: self.log("Stabilization off")
            self.last["stabilization_active"] = self.stabilization_active
        # Relaunch yourself.
        self.status_timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.update,self.status_timer)
        self.status_timer.Start(300,oneShot=True)

    # Override the behaviour of 'CameraViewer' to keep acquiring even when
    # the window is minimized.
    def centering_image_update_needed(self):
        """Do we need to read the camera periodcally?"""
        if self.StabilizationActive.Value == True: return self.LiveImage.Value
        return CameraViewer.image_update_needed(self)

    def OnStepSize(self,event):
        """Called the step size is changed"""
        value = self.StepSize.Value.replace("um","")
        try: self.stepsize = float(eval(value))/1000
        except ValueError: pass
        self.StepSize.Value = "%g um" % (self.stepsize*1000)

    def OnTranslateHLeft(self,event):
        "Tweak the position by -10 um horizontally"
        PeriscopeH.value = PeriscopeH.command_value - self.stepsize * self.xscale
        
    def OnTranslateHRight(self,event):
        "Tweak the position by +10 um horizontally"
        PeriscopeH.value = PeriscopeH.command_value + self.stepsize * self.xscale
        
    def OnTranslateVUp(self,event):
        "Tweak the position by -10 um vertically"
        PeriscopeV.value = PeriscopeV.command_value + self.stepsize * self.yscale
        
    def OnTranslateVDown(self,event):
        "Tweak the position by +10 um vertically"
        PeriscopeV.value = PeriscopeV.command_value - self.stepsize * self.yscale
        
    def OnStabilizationActive(self,event):
        "Continuously keep the beam centered on the crosshair"
        self.stabilization_active = self.StabilizationActive.Value

    def monitor_beam_position(self):
        "Center the beam profile on the crosshair"
        from time import sleep,time
        from numpy import sqrt,average,std,sort
        image_timestamp = 0.0
        last = PeriscopeH.command_value,PeriscopeV.command_value
        # Using a running average.
        X = []; Y = []; SNR = []
        while not self.cancelled:
            # Wait for a new image new image to be acquired.
            while not self.camera.has_image:
                sleep(0.1)
                if self.cancelled: break
            while self.image_timestamp == image_timestamp:
                sleep(0.1)
                if self.cancelled: break
            image_timestamp = self.image_timestamp
            # Reset the statistics if a beam steering motor moved.
            if (PeriscopeH.command_value,PeriscopeV.command_value) != last:
                X = []; Y = []; SNR = []
                last = PeriscopeH.command_value,PeriscopeV.command_value
            # Make sure that the profile is measured with sufficient
            # signal-to-noise ratio.
            snr = self.SNR()
            if snr > self.min_SN:
                x,y = self.ImageWindow.CFWHM
                N = self.average_count
                X = (X+[x])[-N:]
                Y = (Y+[y])[-N:]
                SNR = (SNR+[snr])[-N:]
            if len(X) > 0:
                # Outlier rejection: Reject the smallest and largest sample.
                # (Philip 6 Jun 2010)
                if len(X) >= 10:
                    X_ = sort(X)[1:-1] ; Y_ = sort(Y)[1:-1]; SNR_ = sort(SNR)[1:-1]
                else: X_ = X; Y_ = Y; SNR_ = SNR
                x = average(X_); y = average(Y_); snr = average(SNR_)
                # Standard deviation
                sdev_x = std(X_); sdev_y = std(Y_)
                # Error of the mean (sampling error)
                sx = sdev_x / sqrt(len(X_)-1); sy = sdev_y / sqrt(len(Y_)-1)
                self.status = "%d/%d, " % (len(X),self.average_count)
                self.status += "av. S/N %.3g, " % snr
                self.status += "center: av. (%+.1f,%+.1f) um, " % (x*1000,y*1000)
                self.status += "RMS (%.1f,%.1f) um, " % (sdev_x*1000,sdev_y*1000)
                self.status += "sampling error (%.1f,%.1f) um, " % (sx*1000,sy*1000)
            else: self.status = "insufficient signal/noise (%.3g < %.3g), " % \
                (snr,self.min_SN)

            if not self.stabilization_active: continue

            # Need a certain number of measurements before applying a correction.
            if len(X) < self.min_average_count: continue
            
            # The position error needs to exceed threshold before applying a correction.
            xthreshold = max(sx*self.threshold,self.xthreshold)
            ythreshold = max(sy*self.threshold,self.ythreshold)
            if abs(x) < xthreshold and abs(y) < ythreshold: continue
            
            postpone_correction = self.postpone and self.has_beam()
            if postpone_correction: self.status += "waiting for laser off, "; continue

            # Apply the correction.
            self.last_action = "Correction "
            if abs(x) > xthreshold:
                dx = -self.xscale * x
                PeriscopeH.value = PeriscopeH.value + dx
                self.last_action += "H %+.6f mm (%+.1f um), " % (dx,x*1000)
            if abs(y) > ythreshold:
                dy = -self.yscale * y
                PeriscopeV.value = PeriscopeV.value + dy
                self.last_action += "V %+.6f mm (%+.1f um), " % (dy,y*1000)
            self.last_action = self.last_action.rstrip(", ")
            self.last_time = time()
            self.log(self.last_action)           
    
            # Wait while the motors a moving.
            while PeriscopeH.moving or PeriscopeV.moving and not self.cancelled:
                sleep(0.1)
            # Skip the image that was collected while the motors were moving.
            image_timestamp = self.camera.timestamp
            while self.camera.timestamp == image_timestamp:
                sleep(0.1)
                if self.cancelled: break
            
            # Reset the statistics.
            X = []; Y = []; SNR = []
 
    def SNR(self):
        """signal-to-noise ratio the laser beam profile.
        Peak intensity divided by the noise of the background."""
        from numpy import nan
        if not hasattr(self.ImageWindow,"xprofile"): return nan
        xprofile,yprofile = self.ImageWindow.xprofile,self.ImageWindow.yprofile
        SN = min(SNR(xprofile),SNR(yprofile))
        return SN

    def has_beam(self):
        """Does the detector currently receive a beam?"""
        return (self.SNR() > self.min_SN)

    def OnOptions(self,event):
        "Change parameters controlling the centering procedure"
        dlg = CenteringOptions(self)
        dlg.CenterOnParent()
        dlg.Show()

    def OnShowBeamSteeringControls(self,event):
        "Show/hide extra controls related to sample aligment"
        self.enable_beam_steering = not self.enable_beam_steering

    def OnShowBeamStabilizationControls(self,event):
        "Show/hide extra controls related to sample aligment"
        self.enable_beam_stabilization = \
            not self.enable_beam_stabilization

    def OnExit(self,event):
        # Overrides CameraViewer's 'OnExit' method.
        self.log("Application closed")
        self.cancelled = True
        self.task.join(timeout=0.5)
        CameraViewer.OnExit(self,event)

    def log(self,message):
        "Append message to a log file"
        from tempfile import gettempdir
        from sys import stderr
        from datetime import datetime
        if len(message) == 0 or message[-1] != "\n": message += "\n"
        timestamp = str(datetime.now())[:-7] # omit ms and us
        timestamped_message = timestamp+" "+message
        ##stderr.write(timestamped_message)
        logfile = gettempdir()+"/"+self.name+".log"
        try: file(logfile,"a").write(timestamped_message)
        except IOError: pass
        

class CenteringOptions (wx.Dialog):
    "Allows the use to configure camera properties"
    def __init__ (self,parent):
        wx.Dialog.__init__(self,parent,-1,"Beam Steering/Stabilization Options")
        # Controls
        style = wx.TE_PROCESS_ENTER

        self.MinSN = TextCtrl (self,size=(80,-1),style=style)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnter,self.MinSN)

        self.AverageCount = TextCtrl (self,size=(80,-1),style=style)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnter,self.AverageCount)

        style = wx.TE_PROCESS_ENTER
        self.MinAverageCount = TextCtrl (self,size=(80,-1),style=style)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnter,self.AverageCount)

        self.Threshold = TextCtrl (self,size=(80,-1),style=style)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnter,self.Threshold)

        self.XThreshold = TextCtrl (self,size=(80,-1),style=style)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnter,self.XThreshold)

        self.YThreshold = TextCtrl (self,size=(80,-1),style=style)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnter,self.YThreshold)

        self.Postpone = wx.ComboBox (self,choices=["Yes","No"],size=(80,-1))
        self.Bind (wx.EVT_COMBOBOX,self.OnEnter,self.Postpone)

        self.XScale = TextCtrl (self,size=(80,-1),style=style)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnter,self.XScale)

        self.YScale = TextCtrl (self,size=(80,-1),style=style)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnter,self.YScale)

        # Layout
        layout = wx.BoxSizer()
        grid = wx.FlexGridSizer (cols=2,hgap=5,vgap=5)
        flag = wx.ALIGN_CENTER_VERTICAL
        # Work-around for a bug on wx 2.6, fixed in 2.8.
        # (Size of label calculated from text one pixel too small to hold text,
        # causing text to be wrapped.)
        ##size = (400,-1) 
        size = (-1,-1) 
        
        label = "Signal/noise for center measurement to be valid:"
        grid.Add (wx.StaticText(self,label=label,size=size),flag=flag)
        grid.Add (self.MinSN,flag=flag)

        label = "Running average count:"
        grid.Add (wx.StaticText(self,label=label,size=size),flag=flag)
        grid.Add (self.AverageCount,flag=flag)

        label = "Measurements to average before applying a correction:"
        grid.Add (wx.StaticText(self,label=label,size=size),flag=flag)
        grid.Add (self.MinAverageCount,flag=flag)

        label = "Correction threshold (multiples of sampling error):"
        grid.Add (wx.StaticText(self,label=label,size=size),flag=flag)
        grid.Add (self.Threshold,flag=flag)

        label = "Minimum error before correcting horizontal position:"
        grid.Add (wx.StaticText(self,label=label,size=size),flag=flag)
        grid.Add (self.XThreshold,flag=flag)

        label = "Minimum error before correcting vertical position:"
        grid.Add (wx.StaticText(self,label=label,size=size),flag=flag)
        grid.Add (self.YThreshold,flag=flag)

        label = "Postpone correction until laser off:"
        grid.Add (wx.StaticText(self,label=label,size=size),flag=flag)
        grid.Add (self.Postpone,flag=flag)

        label = "Calibration: Periscope H translation / beam x movement:"
        grid.Add (wx.StaticText(self,label=label,size=size),flag=flag)
        grid.Add (self.XScale,flag=flag)

        label = "Calibration: Periscope V translation / beam y movement:"
        grid.Add (wx.StaticText(self,label=label,size=size),flag=flag)
        grid.Add (self.YScale,flag=flag)

        # Leave a 10-pixel wide space around the panel.
        layout.Add (grid,flag=wx.EXPAND|wx.ALL,border=10)

        self.SetSizer(layout)
        self.Fit()

        self.update()

    def update(self,event=None):
        parent = self.GetParent()
        self.AverageCount.SetValue(str(parent.average_count))
        self.MinAverageCount.SetValue(str(parent.min_average_count))
        self.MinSN.SetValue(str(parent.min_SN))
        self.Threshold.SetValue(str(parent.threshold))
        self.XThreshold.SetValue("%g um" % (parent.xthreshold*1000))
        self.YThreshold.SetValue("%g um" % (parent.ythreshold*1000))
        self.Postpone.SetValue("Yes" if parent.postpone else "No")
        self.XScale.SetValue(str(parent.xscale))
        self.YScale.SetValue(str(parent.yscale))
        # Relaunch yourself.
        self.update_timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.update,self.update_timer)
        self.update_timer.Start(2000,oneShot=True)

    def OnEnter(self,event):
        parent = self.GetParent()
        try: parent.average_count = int(eval(self.AverageCount.Value))
        except: pass
        try: parent.min_average_count = int(eval(self.MinAverageCount.Value))
        except: pass
        try: parent.min_SN = float(eval(self.MinSN.Value))
        except: pass
        try: parent.threshold = float(eval(self.Threshold.Value))
        except: pass
        value = self.XThreshold.Value
        try: parent.xthreshold = float(eval(value.replace("um","")))/1000
        except: pass
        value = self.YThreshold.Value
        try: parent.ythreshold = float(eval(value.replace("um","")))/1000
        except: pass
        parent.postpone = (self.Postpone.Value == "Yes")
        try: parent.xscale = float(eval(self.XScale.Value))
        except: pass
        try: parent.yscale = float(eval(self.YScale.Value))
        except: pass
        self.update()


class TextCtrl (wx.TextCtrl):
    "A customized editable text control"
    def __init__ (self,*args,**kwargs):
        wx.TextCtrl.__init__(self,*args,**kwargs)
        self.NormalBackgroundColour = self.BackgroundColour
        self.EditedBackgroundColour = wx.Colour(255,255,220) # pale yellow
        self.CachedValue = self.Value
        self.Bind (wx.EVT_CHAR,self.OnType)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnter)
        self.Bind (wx.EVT_SET_FOCUS,self.OnReceiveFocus)
        self.Bind (wx.EVT_KILL_FOCUS,self.OnLooseFocus)

    def OnType(self,event):
        """Called when any text is typed"""
        bkg = self.BackgroundColour
        if event.KeyCode == wx.WXK_ESCAPE:
            # On ESC, cancel the editing and replace the original text.
            self.BackgroundColour = self.NormalBackgroundColour
            wx.TextCtrl.SetValue(self,self.CachedValue)
        elif event.KeyCode == wx.WXK_TAB:
            # Tab navigates between controls shifting the keyboard focus.
            self.BackgroundColour = self.NormalBackgroundColour
            wx.TextCtrl.SetValue(self,self.CachedValue)
        else:
            # Enter 'editing mode' by changing the background color.
            self.BackgroundColour = self.EditedBackgroundColour
        if self.BackgroundColour != bkg: self.Refresh()
        # Pass this event on to further event handlers bound to this event.
        # Otherwise, the typed text does not appear in the window.
        event.Skip()
        
    def OnEnter(self,event):
        """Called when Enter is pressed"""
        # Pressing Enter makes the edited text available as "Value" of
        # the control and exits "editing mode".
        bkg = self.BackgroundColour
        self.BackgroundColour = self.NormalBackgroundColour
        if self.BackgroundColour != bkg: self.Refresh()
        self.CachedValue = self.Value
        # Pass this event on to further event handlers bound to this event.
        # Otherwise, the typed text does not appear in the window.
        event.Skip()

    def OnReceiveFocus(self,event):
        """Called when window receives keyboard focus"""
        # Pass this event on to further event handlers bound to this event.
        # Otherwise, the typed text does not appear in the window.
        event.Skip()

    def OnLooseFocus(self,event):
        """Called when window looses keyboard focus"""
        # Cancel the editing and replace the original text.
        bkg = self.BackgroundColour
        self.BackgroundColour = self.NormalBackgroundColour
        if self.BackgroundColour != bkg: self.Refresh()
        wx.TextCtrl.SetValue(self,self.CachedValue)
        # Pass this event on to further event handlers bound to this event.
        # Otherwise, the typed text does not appear in the window.
        event.Skip()

    def GetValue(self):
        if self.BackgroundColour == self.NormalBackgroundColour: 
            return wx.TextCtrl.GetValue(self)
        else: return self.CachedValue
    def SetValue(self,value):
        self.CachedValue = value
        if self.BackgroundColour == self.NormalBackgroundColour:
            # Keep the current cursor position by no changing the updating
            # the control unless the text really changed.
            if wx.TextCtrl.GetValue(self) != value:
                wx.TextCtrl.SetValue(self,value)
    Value = property(GetValue,SetValue)


class ComboBox (wx.ComboBox):
    """A customized Combo Box control"""
    def __init__ (self,*args,**kwargs):
        wx.ComboBox.__init__(self,*args,**kwargs)
        self.NormalBackgroundColour = self.BackgroundColour
        self.EditedBackgroundColour = wx.Colour(255,255,220) # pale yellow
        self.CachedValue = self.Value
        self.Bind (wx.EVT_CHAR,self.OnType)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnter)
        self.Bind (wx.EVT_SET_FOCUS,self.OnReceiveFocus)
        self.Bind (wx.EVT_KILL_FOCUS,self.OnLooseFocus)

    def OnType(self,event):
        """Called when any text is typed"""
        bkg = self.BackgroundColour
        if event.KeyCode == wx.WXK_ESCAPE:
            # On ESC, cancel the editing and replace the original text.
            self.BackgroundColour = self.NormalBackgroundColour
            wx.ComboBox.SetValue(self,self.CachedValue)
        elif event.KeyCode == wx.WXK_TAB:
            # Tab navigates between controls shifting the keyboard focus.
            self.BackgroundColour = self.NormalBackgroundColour
            wx.ComboBox.SetValue(self,self.CachedValue)
        else:
            # Enter 'editing mode' by changing the background color.
            self.BackgroundColour = self.EditedBackgroundColour
        if self.BackgroundColour != bkg: self.Refresh()
        # Pass this event on to further event handlers bound to this event.
        # Otherwise, the typed text does not appear in the window.
        event.Skip()
        
    def OnEnter(self,event):
        """Called when Enter is pressed"""
        # Pressing Enter makes the edited text available as "Value" of
        # the control and exits "editing mode".
        bkg = self.BackgroundColour
        self.BackgroundColour = self.NormalBackgroundColour
        if self.BackgroundColour != bkg: self.Refresh()
        self.CachedValue = self.Value
        # Pass this event on to further event handlers bound to this event.
        # Otherwise, the typed text does not appear in the window.
        event.Skip()

    def OnReceiveFocus(self,event):
        """Called when window receives keyboard focus"""
        # Pass this event on to further event handlers bound to this event.
        # Otherwise, the typed text does not appear in the window.
        event.Skip()

    def OnLooseFocus(self,event):
        """Called when window looses keyboard focus"""
        # Cancel the editing and replace the original text.
        bkg = self.BackgroundColour
        self.BackgroundColour = self.NormalBackgroundColour
        if self.BackgroundColour != bkg: self.Refresh()
        wx.ComboBox.SetValue(self,self.CachedValue)
        # Pass this event on to further event handlers bound to this event.
        # Otherwise, the typed text does not appear in the window.
        event.Skip()

    def GetValue(self):
        if self.BackgroundColour == self.NormalBackgroundColour: 
            return wx.ComboBox.GetValue(self)
        else: return self.CachedValue
    def SetValue(self,value):
        self.CachedValue = value
        if self.BackgroundColour == self.NormalBackgroundColour:
            # Keep the current cursor position by no changing the updating
            # the control unless the text really changed.
            if wx.ComboBox.GetValue(self) != value:
                wx.ComboBox.SetValue(self,value)
    Value = property(GetValue,SetValue)


def SNR(data):
    """Calculate the signal-to-noise ratio of a beam profile.
    It is defined as the ratio the peak height relative to the baseline and the
    RMS of the base line.
    The base line is the outer 20% of the profile on either end."""
    from numpy import rint,std,mean,mean,nan
    y = yvals(data); n = len(data)
    # Assume that the base line is the outer 20% of the data.
    n1 = int(rint(n*0.2)) ; n2 = int(rint(n*0.8))
    baseline = y[0:n1]+y[n2:-1]
    signal = max(y)-mean(baseline)
    noise = std(baseline)
    if noise != 0: return signal/noise
    else: return nan


# The following is only executed when run as stand-alone application.
if __name__ == '__main__':
    wx.app = wx.App(redirect=False)
    camera = GigE_camera("id14b-prosilica5.cars.aps.anl.gov")
    ##camera = GigE_camera("id14b-prosilica5.biocarsvideo.net")
    # Direct imaging: pixel size is same as CCD pixel, 4.65 um 
    viewer = LaserBeamPosition(camera,
        "Laser Beam Position (in beam conditioning box)",
        name="LaserBeamPosition",
        pixelsize=0.00465)
    wx.app.MainLoop()
