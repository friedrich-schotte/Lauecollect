#!/usr/bin/env python
"""Control panel system level (SL) temperature control
Author: Friedrich Schotte
Date created: 2009-10-14
Date last modified: 2019-05-21
"""
import wx,wx3_compatibility
from temperature import temperature
from oasis_chiller import oasis_chiller as oasis
from EditableControls import ComboBox,TextCtrl
from logging import debug
from Panel import BasePanel,PropertyPanel,TogglePanel,TweakPanel

__version__ = "4.6" # title

class Temperature_Panel (wx.Frame):

    def __init__(self):
        wx.Frame.__init__(self,parent=None,title="Temperature SL")

        # Icon
        from Icon import SetIcon
        SetIcon(self,"temperature")

        # Controls
        panel = wx.Panel(self)
        style = wx.TE_PROCESS_ENTER
        self.SetPoint = ComboBox(panel,style=style)

        style = wx.TE_READONLY
        self.ActualTemperature = wx.TextCtrl(panel,style=style)
        self.OasisActualTemperature = wx.TextCtrl(panel,style=style)
        self.CurrentPower = wx.TextCtrl(panel,style=style)

        self.LiveCheckBox = wx.CheckBox (panel,label="Live")
        self.RefreshButton = wx.Button (panel,label="Refresh",size=(65,-1))
        self.MoreButton = wx.Button (panel,label="More...",size=(60,-1))
        self.SettingsButton = wx.Button (panel,label="Settings...",size=(60,-1))
        w,h = self.MoreButton.Size
        self.AboutButton = wx.Button (panel,label="?",size=(h*1.25,h*0.75))

        # Callbacks
        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnterSetPoint,self.SetPoint)
        self.Bind (wx.EVT_COMBOBOX,self.OnEnterSetPoint,self.SetPoint)

        self.Bind (wx.EVT_CHECKBOX,self.OnLive,self.LiveCheckBox)
        self.Bind (wx.EVT_BUTTON,self.OnRefresh,self.RefreshButton)
        self.Bind (wx.EVT_BUTTON,self.OnMore,self.MoreButton)
        self.Bind (wx.EVT_BUTTON,self.OnAbout,self.AboutButton)
        self.Bind (wx.EVT_BUTTON,self.OnTemperature,self.SettingsButton)

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

        t = wx.StaticText(panel,label="Oasis Temperature:")
        layout.Add (t,(1,2),flag=a)
        layout.Add (self.OasisActualTemperature,(1,3),flag=a|e)

        t = wx.StaticText(panel,label="Current / Power:")
        layout.Add (t,(2,0),flag=a)
        layout.Add (self.CurrentPower,(2,1),flag=a|e)

        buttons = wx.BoxSizer(wx.HORIZONTAL)
        buttons.Add (self.LiveCheckBox,flag=wx.ALIGN_CENTER_VERTICAL)
        buttons.AddSpacer(5)
        buttons.Add (self.RefreshButton,flag=wx.ALIGN_CENTER_VERTICAL)
        buttons.AddSpacer(5)
        buttons.Add (self.MoreButton,flag=wx.ALIGN_CENTER_VERTICAL)
        buttons.AddSpacer(5)
        buttons.Add (self.SettingsButton,flag=wx.ALIGN_CENTER_VERTICAL)
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
        temperature.command_value = T

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
        value = tofloat(temperature.command_value)
        self.SetPoint.Value = "%.3f C" % value if not isnan(value) else ""

        value = temperature.value
        self.ActualTemperature.Value = "%.3f C"%value if not isnan(value) else ""
        value = oasis.value
        self.OasisActualTemperature.Value = "%.3f C"%value if not isnan(value) else ""

        moving = temperature.moving
        self.ActualTemperature.ForegroundColour = (255,0,0) if moving else (0,0,0)

        moving = oasis.moving
        self.OasisActualTemperature.ForegroundColour = (255,0,0) if moving else (0,0,0)
        ##self.ActualTemperature.BackgroundColour = (255,235,235) if moving else (255,255,255)

        current = temperature.I
        current = "%.3f A" % current if not isnan(current) else ""
        power = temperature.P
        power = "%.3f W" % power if not isnan(power) else ""
        self.CurrentPower.Value = "%s / %s" % (current,power)

    def OnMore(self,event):
        """Display panel with additional parameters."""
        self.parameter_panel = ParameterPanel(self)

    def OnTemperature(self,event):
        """Show panel with temperature ramp parameters"""
        self.temperature_ramp_panel = Temperature(self)

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
    ]
    parameters = [
        [[PropertyPanel,"EPICS Record",temperature,"prefix"],{"choices":["NIH:TEMP","NIH:LIGHTWAVE"],"refresh_period":1.0}],
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

class Temperature(BasePanel):
    name = "temperature"
    title = "Temperature"
    standard_view = [
        "Temp Points",
        "Time Points",
        "P default",
        "I default",
        "D default",
        "Lightwave prefix",
        "Oasis subordinate (on/off)",
        "Oasis threshold T",
        "Oasis idle temperature (low limit) (C)",
        "Oasis temperature limit high (C)",
        "Oasis headstart time (s)",
        "Oasis prefix",
        "set point update period (s)",
    ]
    parameters = [
        [[PropertyPanel,"Temp Points",temperature,"temp_points" ],{}],
        [[PropertyPanel,"Time Points",temperature,"time_points" ],{}],

        [[PropertyPanel,"P default",temperature,"P_default" ],{}],
        [[PropertyPanel,"I default",temperature,"I_default" ],{}],
        [[PropertyPanel,"D default",temperature,"D_default" ],{}],
        [[PropertyPanel,"Lightwave prefix",temperature,"lightwave_prefix"],{}],
        [[PropertyPanel,"Oasis subordinate (on/off)",temperature,"oasis_subordinate" ],{}],
        [[PropertyPanel,"Oasis threshold T",temperature,"T_threshold" ],{}],
        [[PropertyPanel,"Oasis idle temperature (low limit) (C)",temperature,"idle_temperature_oasis" ],{}],
        [[PropertyPanel,"Oasis temperature limit high (C)",temperature,"temperature_oasis_limit_high" ],{}],
        [[PropertyPanel,"Oasis headstart time (s)",temperature,"oasis_headstart_time" ],{}],
        [[PropertyPanel,"Oasis prefix",temperature,"oasis_prefix" ],{}],
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
    logfile = gettempdir()+"/Temperature_Panel.log"
    logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s",
       filename=logfile)
    logging.debug("Temperature Panel started")
    # Needed to initialize WX library
    if not "app" in globals(): app = wx.App(redirect=False)
    panel = Temperature_Panel()
    app.MainLoop()
