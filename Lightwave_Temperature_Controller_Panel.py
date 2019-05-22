#!/usr/bin/env python
"""Control panel for ILX Lighwave Precision Temperature Controller.
Author: Friedrich Schotte
Date created: 2009-10-14
Date last modified: 2019-05-21
"""
import wx,wx3_compatibility
from lightwave_temperature_controller import lightwave_temperature_controller
from EditableControls import ComboBox,TextCtrl
from logging import debug
from Panel import BasePanel,PropertyPanel,TogglePanel,TweakPanel

__version__ = "4.6" # title, renamed: lightwave_temperature_controller

class Lightwave_Temperature_Controller_Panel (wx.Frame):
    """Control panel for ILX Lighwave Precision Temperature Controller"""

    def __init__(self):
        wx.Frame.__init__(self,parent=None)
        self.Title = "Lightwave Temperature Controller DL"

        # Icon
        from Icon import SetIcon
        SetIcon(self,"Temperature Controller")

        # Controls
        panel = wx.Panel(self)
        style = wx.TE_PROCESS_ENTER
        self.SetPoint = ComboBox(panel,style=style)

        style = wx.TE_READONLY
        self.ActualTemperature = wx.TextCtrl(panel,style=style)
        self.CurrentPower = wx.TextCtrl(panel,style=style)

        self.Status = ComboBox(panel,style=style,choices=["On","Off",""])

        self.LiveCheckBox = wx.CheckBox (panel,label="Live")
        self.RefreshButton = wx.Button (panel,label="Refresh",size=(65,-1))
        self.MoreButton = wx.Button (panel,label="More...",size=(60,-1))
        self.RampButton = wx.Button (panel,label="Ramp...",size=(60,-1))
        w,h = self.MoreButton.Size
        self.AboutButton = wx.Button (panel,label="?",size=(h*1.25,h*0.75))

        # Callbacks
        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnterSetPoint,self.SetPoint)
        self.Bind (wx.EVT_COMBOBOX,self.OnEnterSetPoint,self.SetPoint)

        self.Bind (wx.EVT_TEXT_ENTER,self.OnChangeStatus,self.Status)
        self.Bind (wx.EVT_COMBOBOX,self.OnChangeStatus,self.Status)

        self.Bind (wx.EVT_CHECKBOX,self.OnLive,self.LiveCheckBox)
        self.Bind (wx.EVT_BUTTON,self.OnRefresh,self.RefreshButton)
        self.Bind (wx.EVT_BUTTON,self.OnMore,self.MoreButton)
        self.Bind (wx.EVT_BUTTON,self.OnAbout,self.AboutButton)
        self.Bind (wx.EVT_BUTTON,self.OnTemperatureRamp,self.RampButton)

        # Layout
        layout = wx.GridBagSizer(1,1)
        a = wx.ALIGN_CENTRE_VERTICAL
        e = wx.EXPAND

        # Under Linux, if the version of wxWidget is 2.6 or older,
        # the label size needs to be specified to prevent line wrapping.
        # (This bug has been corrected in version 2.8).
        layout.Add (wx.StaticText(panel,label="Set Point:"),(0,0),flag=a)
        layout.Add (self.SetPoint,(0,1),flag=a|e)

        t = wx.StaticText(panel,label="Actual Temperature:")
        layout.Add (t,(1,0),flag=a)
        layout.Add (self.ActualTemperature,(1,1),flag=a|e)

        t = wx.StaticText(panel,label="Current / Power:")
        layout.Add (t,(2,0),flag=a)
        layout.Add (self.CurrentPower,(2,1),flag=a|e)

        t = wx.StaticText(panel,label="Status:")
        layout.Add (t,(3,0),flag=a)
        layout.Add (self.Status,(3,1),flag=a|e)

        buttons = wx.BoxSizer(wx.HORIZONTAL)
        buttons.Add (self.LiveCheckBox,flag=wx.ALIGN_CENTER_VERTICAL)
        buttons.AddSpacer(5)
        buttons.Add (self.RefreshButton,flag=wx.ALIGN_CENTER_VERTICAL)
        buttons.AddSpacer(5)
        buttons.Add (self.MoreButton,flag=wx.ALIGN_CENTER_VERTICAL)
        buttons.AddSpacer(5)
        buttons.Add (self.RampButton,flag=wx.ALIGN_CENTER_VERTICAL)
        buttons.AddSpacer(5)
        buttons.Add (self.AboutButton,flag=wx.ALIGN_CENTER_VERTICAL)

        # Leave a 5 pixel wide border.
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add (layout,flag=wx.ALL,border=5)
        box.Add (buttons,flag=wx.ALL|wx.ALIGN_CENTER_HORIZONTAL,border=5)
        panel.SetSizer(box)
        panel.Fit()
        self.Fit()

        self.Show()

        # Restore saved history.
        config_dir = wx.StandardPaths.Get().GetUserDataDir()
        config_file = config_dir+"/TemperatureController.py"
        self.config = wx.FileConfig (localFilename=config_file)
        value = self.config.Read('History')
        if value: self.history = eval(value)
        else: self.history = []
        self.update_history()
        # Initialization
        self.timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.refresh,self.timer)
        self.timer.Start(1000,oneShot=True)

    def update_history(self):
        """Update the pull down menu for the set point."""
        self.SetPoint.Clear() # clears menu
        choices = []
        for T in sorted(set(self.history)): choices += [str(T)]
        self.SetPoint.AppendItems(choices)

    def OnEnterSetPoint(self,event):
        """Called when typing Enter in the position field.
        or selecting a choice from the combo box drop down menu"""
        text = self.SetPoint.Value
        try: T = float(eval(text.replace("C","")))
        except: self.refresh(); return
        lightwave_temperature_controller.command_value = T

        self.history = self.history[-20:]+[T]
        self.update_history()

        self.refresh()

        # Make sure the history gets saved.
        config_dir = wx.StandardPaths.Get().GetUserDataDir()
        from os.path import exists
        from os import makedirs
        if not exists(config_dir): makedirs(config_dir)
        self.config.Write ('history',repr(self.history))
        self.config.Flush()

    def OnChangeStatus(self,event):
        """Called when typing Enter in the position field.
        or selecting a choice from the combo box drop down menu"""
        text = self.Status.Value
        if text == "On": lightwave_temperature_controller.enabled = True
        if text == "Off": lightwave_temperature_controller.enabled = False
        self.refresh()

    def OnLive(self,event):
        """Called when the 'Live' checkbox is either checked or unchecked."""
        self.RefreshButton.Enabled = not self.LiveCheckBox.Value
        if self.LiveCheckBox.Value == True: self.keep_alive()

    def keep_alive(self,event=None):
        """Periodically refresh te displayed settings (every second)."""
        if self.LiveCheckBox.Value == False: return
        self.refresh()
        self.timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.keep_alive,self.timer)
        self.timer.Start(250,oneShot=True)

    def OnRefresh(self,event):
        """Called when refrsh button is pressed"""
        self.refresh()

    def refresh(self,event=None):
        """Update displayed values"""
        value = tofloat(lightwave_temperature_controller.command_value)
        self.SetPoint.Value = "%.3f C" % value if not isnan(value) else ""

        value = lightwave_temperature_controller.value
        self.ActualTemperature.Value = "%.3f C"%value if not isnan(value) else ""
        moving = lightwave_temperature_controller.moving
        self.ActualTemperature.ForegroundColour = (255,0,0) if moving else (0,0,0)
        ##self.ActualTemperature.BackgroundColour = (255,235,235) if moving else (255,255,255)

        current = lightwave_temperature_controller.I
        current = "%.3f A" % current if not isnan(current) else ""
        power = lightwave_temperature_controller.P
        power = "%.3f W" % power if not isnan(power) else ""
        self.CurrentPower.Value = "%s / %s" % (current,power)

        value = toint(lightwave_temperature_controller.enabled)
        if value == 0: text = "Off"
        elif value == 1: text = "On"
        else: text = ""
        self.Status.Value = text

    def OnMore(self,event):
        """Display panel with additional parameters."""
        self.parameter_panel = ParameterPanel(self)

    def OnTemperatureRamp(self,event):
        """Show panel with temperature ramp parameters"""
        self.temperature_ramp_panel = TemperatureRamp(self)

    def OnAbout(self,event):
        "Called from the Help/About"
        from os.path import basename
        from inspect import getfile
        filename = getfile(lambda x: None)
        info = basename(filename)+" "+__version__+"\n"+__doc__
        dlg = wx.MessageDialog(self,info,"About",wx.OK|wx.ICON_INFORMATION)
        dlg.CenterOnParent()
        dlg.ShowModal()
        dlg.Destroy()


class ParameterPanel(BasePanel):
    name = "parameters"
    title = "Parameters"
    standard_view = [
        "EPICS Record",
        "Baud Rate",
        "Serial Port",
        "ID String",
        "Act. Update Period",
        "Nom. Update Period",
        "Proportional Gain (P)",
        "Integral Gain (I)",
        "Differential Gain (D)",
        "Stabilization Threshold",
        "Stabilization N Samples",
        "Current Low Limit",
        "Current High Limit",
    ]
    parameters = [
        [[PropertyPanel,"EPICS Record",lightwave_temperature_controller,"prefix"],{"choices":["NIH:TEMP","NIH:LIGHTWAVE"],"refresh_period":1.0}],
        [[PropertyPanel,"Baud Rate",lightwave_temperature_controller,"BAUD"],{"choices":[9600,14400,19200,38400,56700]}],
        [[PropertyPanel,"Serial Port",lightwave_temperature_controller,"port_name"],{"read_only":True}],
        [[PropertyPanel,"ID String",lightwave_temperature_controller,"id"],{"read_only":True}],
        [[PropertyPanel,"Nom. Update Period",lightwave_temperature_controller,"SCAN"],{"choices":[0,0.2,0.5,1.0,2.0],"unit":"s","format":"%g"}],
        [[PropertyPanel,"Act. Update Period",lightwave_temperature_controller,"SCANT"],{"read_only":True,"unit":"s","format":"%g"}],
        [[PropertyPanel,"Proportional Gain (P)",lightwave_temperature_controller,"PCOF"],{"choices":[0.75]}],
        [[PropertyPanel,"Integral Gain (I)"    ,lightwave_temperature_controller,"ICOF"],{"choices":[0.3],"format":"%g"}],
        [[PropertyPanel,"Differential Gain (D)",lightwave_temperature_controller,"DCOF"],{"choices":[0.3],"format":"%g"}],
        [[PropertyPanel,"Stabilization Threshold",lightwave_temperature_controller,"stabilization_threshold"],{"digits":3,"unit":"C","choices":[0.01,0.008]}],
        [[PropertyPanel,"Stabilization N Samples",lightwave_temperature_controller,"stabilization_nsamples"],{"choices":[3]}],
        [[PropertyPanel,"Current Low Limit",lightwave_temperature_controller,"current_low_limit"],{"digits":3,"unit":"A","choices":[3.5,4,5]}],
        [[PropertyPanel,"Current High Limit",lightwave_temperature_controller,"current_high_limit"],{"digits":3,"unit":"A","choices":[-3.5,-4,-5]}],
    ]

    def __init__(self,parent=None):
        BasePanel.__init__(self,
            parent=parent,
            name=self.name,
            title=self.title,
            parameters=self.parameters,
            standard_view=self.standard_view,
            subname=True,
            refresh=True,
            live=True,
            label_width=90,
        )

class TemperatureRamp(BasePanel):
    name = "temperature_ramp"
    title = "Temperature Ramp"
    standard_view = [
        "Trigger Enabled",
        "Start",
        "Stepsize",
        "Stop",
    ]
    parameters = [
        [[TogglePanel,"Trigger Enabled",lightwave_temperature_controller,"trigger_enabled" ],{"type":"Off/On"}],
        [[TweakPanel,"Start"   ,lightwave_temperature_controller,"trigger_start"   ],{"digits":3,"unit":"C"}],
        [[TweakPanel,"Stop"    ,lightwave_temperature_controller,"trigger_stop"    ],{"digits":3,"unit":"C"}],
        [[TweakPanel,"Stepsize",lightwave_temperature_controller,"trigger_stepsize"],{"digits":3,"unit":"C"}],
    ]

    def __init__(self,parent=None):
        BasePanel.__init__(self,
            parent=parent,
            name=self.name,
            title=self.title,
            parameters=self.parameters,
            standard_view=self.standard_view,
            subname=True,
            refresh=True,
            live=True,
            label_width=90,
        )

def isnan(x):
    """Is x 'not a number' or 'None'"""
    from numpy import isnan
    try: return isnan(float(x))
    except: return True

def tostr(x):
    """Convert x to string."""
    if x is None: return ""
    return str(x)

def tofloat(x):
    """Convert x to float if possible, else return nan"""
    from numpy import nan
    try: x = float(x)
    except: x = nan
    return x

def toint(x):
    """Convert x to int if possible, else return nan"""
    from numpy import nan
    try: x = int(x)
    except: x = nan
    return x

if __name__ == '__main__':
    from pdb import pm
    import logging; from tempfile import gettempdir
    logfile = gettempdir()+"/Lightwave_Temperature_Controller_Panel.log"
    logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s",
       filename=logfile)
    logging.debug("Lightwave Temperature Controller Panel started")
    # Needed to initialize WX library
    if not "app" in globals(): app = wx.App(redirect=False)
    panel = Lightwave_Temperature_Controller_Panel()
    app.MainLoop()
