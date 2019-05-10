#!/usr/bin/env python
"""
SAXS/WAXS data collection setup for Aerotech Ensemble motion controller.
"Fly-thru" and "Setting" mode are implemented using "piano player" mode
for the FPGA.
Author: Friedrich Schotte
Date created: May 27, 2015
Date last modified: Jun 15, 2018
"""
import wx, wx3_compatibility
from Ensemble_SAXS_pp import Ensemble_SAXS
from timing_sequence import timing_sequencer
from timing_system import timing_system
from EditableControls import ComboBox # customized version of wx.ComboBox
from numpy import nan
from logging import warn,debug
from persistent_property import persistent_property
from collections import OrderedDict as odict
from Panel import PropertyPanel
import autoreload

__version__ = "3.6.5" # repeats

class Panel(wx.Frame):
    """Control Panel for FPGA Timing System"""
    name = "EnsembleSAXS_PP_Panel"

    def hlc_choices():
        from timing_system import timing_system
        from numpy import arange,finfo
        eps = finfo(float).eps
        hsct = timing_system.hsct
        choices = arange(-6*hsct,+6*hsct+eps,hsct)
        return choices

    def hsc_choices():
        from timing_system import timing_system
        from numpy import arange,finfo
        eps = finfo(float).eps
        P0t = timing_system.P0t
        choices = arange(-12*P0t/24,12*P0t/24+eps,P0t/24)
        return choices

    parameters = [
        [("Delay",                 Ensemble_SAXS,"delay",    "time"  ),{}],
        [("Mode",                  Ensemble_SAXS,"mode"              ),{}],
        [("Period [1-kHz cycles]", Ensemble_SAXS,"trigger_period_in_1kHz_cycles"),{}],
        [("Laser",                 Ensemble_SAXS,"laser_on", "Off/On"),{}],
        [("X-ray ms shutter",      Ensemble_SAXS,"ms_on",    "Off/On"),{}],
        [("Camera shutter mode",   Ensemble_SAXS,"s1_on",    "Manual/Auto"),{}],
        [("Camera shutter state",  Ensemble_SAXS,"s1_state", "Open/Close"),{}],
        [("Pump",                  Ensemble_SAXS,"pump_on",  "Off/On"),{}],
        [("Trigger code",          Ensemble_SAXS,"transc",   "binary"),{}],
        [("X-ray detector trigger",Ensemble_SAXS,"xdet_on",  "Off/On"),{}],
        [("X-ray scope trigger",   Ensemble_SAXS,"xosct_on", "Off/On"),{}],
        [("Laser scope trigger",   Ensemble_SAXS,"losct_on", "Off/On"),{}],
        [("Temperature steps",     Ensemble_SAXS,"temp_inc"          ),{}],
        [("X-ray detector trigger count",Ensemble_SAXS,"xdet_count","integer"),{}],
        [("Image number",          Ensemble_SAXS,"image_number"      ),{}],
        [("Passes",                Ensemble_SAXS,"passes"            ),{}],
        [("Pass number",           Ensemble_SAXS,"pass_number"       ),{}],
        [("Pulses",                Ensemble_SAXS,"pulses"            ),{}],
        [("Image number increment",Ensemble_SAXS,"image_number_inc","Off/On"),{}],
        [("Pass number increment", Ensemble_SAXS,"pass_number_inc" ,"Off/On"),{}],
        [("Acquiring",               timing_sequencer,  "acquiring",       "Idle/Acquiring"),{}],
        [("Queue active",            timing_sequencer,  "queue_active"    ,"Not Active/Active"),{}],
        [("Queue repeat count"      ,timing_sequencer,  "queue_repeat_count","integer"),{}],
        [("Current queue repeat count",timing_sequencer,"current_queue_repeat_count","integer"),{}],
        [("Queue max repeat count",  timing_sequencer,  "queue_max_repeat_count","integer"),{}],
        [("Current queue max repeat",timing_sequencer,"current_queue_max_repeat_count","integer"),{}],
        [("Queue sequence count"    ,timing_sequencer,  "queue_sequence_count","integer"),{}],
        [("Current queue sequence cnt",timing_sequencer,"current_queue_sequence_count","integer"),{}],
        [("Queue length [sequences]",timing_sequencer,  "queue_length",    "integer"),{}],
        [("Current queue length [seq]",timing_sequencer,"current_queue_length","integer"),{}],
        [("Cache",                 timing_sequencer,"cache_enabled","Disabled/Caching"),{}],
        [("Cache size [passes]",   timing_sequencer,"cache_size"),{}],
        [("Sequencer Running",     Ensemble_SAXS,"running","Stopped/Running"),{}],
        [("Sequence generator",    Ensemble_SAXS,"generator"),{"read_only":True}],
        [("Sequence generator version",Ensemble_SAXS,"generator_version"),{"read_only":True}],
        [("Heatload chopper phase",Ensemble_SAXS,"hlcnd","time.6"  ),{"choices":hlc_choices}],
        [("Heatload chop. act. phase",Ensemble_SAXS,"hlcad","time.6"  ),{"choices":hlc_choices}],
        [("High-speed chopper phase",Ensemble_SAXS,"hsc_delay","time.4"),{"choices":hsc_choices}],
    ]
    StandardView = [
        "Delay",
        "Mode",
        "Period [1-kHz cycles]",
        "Laser",
        "X-ray ms shutter","Pump",
        "Trigger code",
        "X-ray detector trigger",
        "X-ray scope trigger",
        "Laser scope trigger",
        "Sequencer Running",
    ]
    CustomView = persistent_property("CustomView",StandardView)
    views = odict([("Standard","StandardView"),("Custom","CustomView")])
    view = persistent_property("view","Standard")

    refresh_period = persistent_property("refresh_period",1.0)

    def __init__(self):
        from numpy import inf
        wx.Frame.__init__(self,parent=None,title="Ensemble SAXS-WAXS PP")

        # Icon
        from Icon import SetIcon
        SetIcon(self,"timing-system")

        # Controls
        self.panel = wx.Panel(self)
        self.controls = []
        for args,kwargs in self.parameters:
            self.controls += [PropertyPanel(self.panel,*args,
                refresh_period=inf,**kwargs)]

        self.LiveCheckBox = wx.CheckBox(self.panel,label="Live")
        self.RefreshButton = wx.Button (self.panel,label="Refresh",size=(62,-1))
        CalibrateButton = wx.Button (self.panel,label="Cal..",size=(45,-1))
        ConfigureButton = wx.Button (self.panel,label="Conf..",size=(50,-1))
        SetupButton = wx.Button (self.panel,label="Setup..",size=(55,-1))
        ParametersButton = wx.Button (self.panel,label="Param..",size=(60,-1))
        w,h = SetupButton.Size
        AboutButton = wx.Button (self.panel,label="?",size=(22,-1))

        # Menus
        menuBar = wx.MenuBar()
        self.ViewMenu = wx.Menu()
        for i in range(0,len(self.views)):
            self.ViewMenu.AppendCheckItem(10+i,self.views.keys()[i])
        self.ViewMenu.AppendSeparator()
        for i in range(0,len(self.controls)):
            self.ViewMenu.AppendCheckItem(100+i,self.controls[i].title)
        menuBar.Append (self.ViewMenu,"&View")
        menu = wx.Menu()
        menu.Append (wx.ID_ABOUT,"About...","Show version number")
        menuBar.Append (menu,"&Help")
        self.SetMenuBar (menuBar)

        # Callbacks
        for i in range(0,len(self.views)):
            self.Bind(wx.EVT_MENU,self.OnSelectView,id=10+i)
        for i in range(0,len(self.controls)):
            self.Bind(wx.EVT_MENU,self.OnView,id=100+i)
        self.Bind(wx.EVT_MENU_OPEN,self.OnOpenView)
        self.Bind(wx.EVT_MENU,self.OnAbout,id=wx.ID_ABOUT)
        self.Bind(wx.EVT_CHECKBOX,self.OnLive,self.LiveCheckBox)
        self.Bind(wx.EVT_BUTTON,self.OnRefresh,self.RefreshButton)
        self.Bind(wx.EVT_BUTTON,self.OnCalibrate,CalibrateButton)
        self.Bind(wx.EVT_BUTTON,self.OnConfigure,ConfigureButton)
        self.Bind(wx.EVT_BUTTON,self.OnSetup,SetupButton)
        self.Bind(wx.EVT_BUTTON,self.OnParameters,ParametersButton)
        self.Bind(wx.EVT_BUTTON,self.OnAbout,AboutButton)

        # Layout
        box = wx.BoxSizer(wx.VERTICAL)
        flag = wx.ALL|wx.ALIGN_CENTRE_HORIZONTAL
        for c in self.controls: box.Add (c,flag=flag,border=0)
        for c in self.controls: c.Shown = c.title in self.view
        buttons = wx.BoxSizer(wx.HORIZONTAL)
        buttons.Add (self.LiveCheckBox,flag=wx.ALIGN_CENTER_VERTICAL)
        buttons.Add (self.RefreshButton)
        buttons.AddSpacer(5)
        buttons.Add (CalibrateButton)
        buttons.AddSpacer(5)
        buttons.Add (ConfigureButton)
        buttons.AddSpacer(5)
        buttons.Add (SetupButton)
        buttons.AddSpacer(5)
        buttons.Add (ParametersButton)
        buttons.AddSpacer(5)
        buttons.Add (AboutButton)
        box.Add (buttons,flag=flag,border=5)
        self.panel.Sizer = box
        self.panel.Fit()
        self.Fit()

        # Initialization
        if not self.view in self.views: self.view = self.views.keys()[0]
        self.View = getattr(self,self.views[self.view])

        self.Show()

    def get_View(self):
        """Which control to show? List of strings"""
        return [c.title for c in self.controls if c.Shown]
    def set_View(self,value):
        for c in self.controls: c.Shown = c.title in value
        self.panel.Sizer.Fit(self)
    View = property(get_View,set_View)

    def refresh(self):
        """Updates the controls with current values"""
        global Ensemble_SAXS
        from Ensemble_SAXS_pp import Ensemble_SAXS

        from timing_system import timing_system
        ##timing_system.clear_cache()
        timing_system.cache += 1
        for control in self.controls:
            if control.Shown:
                control.refresh()
        timing_system.cache -= 1

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
        self.timer.Start(int(self.refresh_period*1000),oneShot=True)

    def OnRefresh(self,event=None):
        """Check whether the network connection is OK."""
        self.refresh()

    def OnCalibrate(self,event):
        """Show panel with additional parameters"""
        from TimingPanel import CalibrationPanel
        self.parameter_panel = CalibrationPanel(self,
            update=[Ensemble_SAXS.update])

    def OnConfigure(self,event):
        """Show panel with additional parameters"""
        from TimingConfigurationPanel import TimingConfigurationPanel
        self.configuration_panel = TimingConfigurationPanel(self,
            update=[Ensemble_SAXS.update])

    def OnSetup(self,event):
        """Show panel with configuration parameters"""
        from TimingPanel import SetupPanel
        self.set_panel = SetupPanel(self)

    def OnOpenView(self,event):
        """Called if the "View" menu is selected"""
        for i in range(0,len(self.views)):
            self.ViewMenu.Check(10+i,self.views.keys()[i] == self.view)
        for i in range(0,len(self.controls)):
            self.ViewMenu.Check(100+i,self.controls[i].Shown)
            self.ViewMenu.Enable(100+i,self.view != "Standard")

    def OnSelectView(self,event):
        """Called if one of the items of the "View" menu is selected"""
        n =  event.Id-10
        self.view = self.views.keys()[n]
        self.View = getattr(self,self.views.values()[n])

    def OnView(self,event):
        """Called if one of the items of the "View" menu is selected"""
        n =  event.Id-100
        self.controls[n].Shown = not self.controls[n].Shown
        self.panel.Sizer.Fit(self)
        view = [c.title for c in self.controls if c.Shown]
        setattr(self,self.views[self.view],view)

    def OnParameters(self, event):
        "Show dialog box for more diagnostics"
        dlg = ParameterPanel(self)
        dlg.CenterOnParent()
        dlg.Show()

    def OnAbout(self,event):
        """Show panel with additional parameters"""
        from os.path import basename
        from inspect import getfile
        from os.path import getmtime
        from datetime import datetime
        filename = getfile(lambda x: None)
        info = basename(filename)+" "+__version__
        import Ensemble_SAXS_pp as module
        filename = getfile(module)
        if hasattr(module,"__source_timestamp__"):
            timestamp = module.__source_timestamp__
            filename = filename.replace(".pyc",".py")
        else: timestamp = getmtime(getfile(module))
        info += "\n"+basename(filename)+" "+module.__version__
        info += " ("+str(datetime.fromtimestamp(timestamp))+")"
        info += "\n\n"+__doc__
        dlg = wx.MessageDialog(self,info,"About",wx.OK|wx.ICON_INFORMATION)
        dlg.CenterOnParent()
        dlg.ShowModal()
        dlg.Destroy()

class ParameterPanel(wx.Dialog):
    def __init__ (self,parent):
        import wx.grid
        wx.Dialog.__init__(self,parent,-1,"Ensemble SAXS-WAXS Parameters")

        # Controls
        self.Table = wx.grid.Grid(self)
        self.Table.SetRowLabelSize(0) # Hide row labels (1,2,...).
        self.Table.CreateGrid(0,0)
        self.Table.AutoSize()

        AddButton = wx.Button(self,label="+",style=wx.BU_EXACTFIT)
        DelButton = wx.Button(self,label="-",size=AddButton.Size)

        OkButton = wx.Button(self,wx.ID_OK)
        OkButton.SetDefault()
        ApplyButton = wx.Button(self,wx.ID_APPLY)
        RefreshButton = wx.Button(self,wx.ID_REFRESH)
        CancelButton = wx.Button(self,wx.ID_CANCEL)

        # Callbacks
        self.Bind(wx.EVT_BUTTON,self.add_row,AddButton)
        self.Bind(wx.EVT_BUTTON,self.delete_row,DelButton)
        self.Bind(wx.EVT_BUTTON,self.OnOK,OkButton)
        self.Bind(wx.EVT_BUTTON,self.apply,ApplyButton)
        self.Bind(wx.EVT_BUTTON,self.refresh,RefreshButton)
        self.Bind(wx.grid.EVT_GRID_CELL_CHANGED,self.apply) # wx 4.0

        # Layout
        border = wx.BoxSizer(wx.VERTICAL)
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add (self.Table)

        buttons = wx.BoxSizer()
        buttons.Add (AddButton)
        buttons.Add (DelButton)
        box.Add (buttons)
        # Leave a 10-pixel wide space around the panel.
        border.Add (box,0,wx.ALL,10)

        buttons = wx.BoxSizer()
        buttons.Add (OkButton)
        buttons.AddSpacer(10) # wx 4.0
        buttons.Add (ApplyButton)
        buttons.AddSpacer(10) # wx 4.0
        buttons.Add (RefreshButton)
        buttons.AddSpacer(10) # wx 4.0
        buttons.Add (CancelButton)
        # Leave a 10-pixel wide space around the panel.
        border.Add (buttons,0,wx.ALL,10)

        self.SetSizer(border)
        self.Fit()
        self.refresh()

    def refresh(self,event=None):
        parameters = Ensemble_SAXS.mode_parameters
        labels = parameters[0]
        values = parameters[1:]
        ncols = len(labels)
        nrows = len(values)
        if nrows > self.Table.NumberRows: self.Table.AppendRows(nrows-self.Table.NumberRows)
        if nrows < self.Table.NumberRows: self.Table.DeleteRows(self.Table.NumberRows-nrows)
        if ncols > self.Table.NumberCols: self.Table.AppendCols(ncols-self.Table.NumberCols)
        if ncols < self.Table.NumberCols: self.Table.AppendCols(self.Table.NumberCols-ncols)
        for j in range(0,ncols): self.Table.SetColLabelValue(j,labels[j])
        for i in range(0,nrows):
            for j in range(0,ncols): self.Table.SetCellValue(i,j,str(values[i][j]))
        self.Table.AutoSize()
        self.Fit()

    def add_row(self,event):
        """Add one more row at the end of the table"""
        self.Table.AppendRows(1)
        self.Table.AutoSize()
        self.Fit()

    def delete_row(self,event):
        """Remove the last row of the table"""
        n = self.Table.NumberRows
        self.Table.DeleteRows(n-1,1)
        self.Table.AutoSize()
        self.Fit()

    def OnOK(self,event):
        """Called if the OK button is pressed"""
        self.apply()
        self.Destroy()

    def apply(self,event=None):
        nrows = self.Table.NumberRows
        ncols = self.Table.NumberCols
        labels = [str(self.Table.GetColLabelValue(j)) for j in range(0,ncols)]
        values = [[fromstr(self.Table.GetCellValue(i,j)) for j in range(0,ncols)]
                  for i in range(0,nrows)]
        parameters = [labels]+values
        Ensemble_SAXS.mode_parameters = parameters


def fromstr(value):
    """Convert a string to a Python data type, if possilbe"""
    try: value = eval(value)
    except: value = str(value)
    return value

if __name__ == '__main__':
    from pdb import pm # for debugging
    import logging # for debugging
    from tempfile import gettempdir
    logfile = gettempdir()+"/EnsembleSAXS_PP_Panel.log"
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s %(levelname)s: %(message)s",
        filename=logfile,
    )
    # Needed to initialize WX library
    if not hasattr(wx,"app"): wx.app = wx.App(redirect=False)
    panel = Panel()
    wx.app.MainLoop()
