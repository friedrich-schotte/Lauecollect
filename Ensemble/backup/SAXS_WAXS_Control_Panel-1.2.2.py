#!/usr/bin/env python
"""Control panel for SAXS-WAXS Experiments.
Friedrich Schotte, Jun 12, 2017 - Jun 25, 2017"""
__version__ = "1.2.2" # passing "globals()" environment to "Control", Mode

from logging import debug,info,warn,error
import wx
from SAXS_WAXS_control import SAXS_WAXS_control # passed on in "globals()"

class SAXS_WAXS_Control_Panel(wx.Frame):
    """Control panel for SAXS-WAXS Experiments"""
    def __init__(self):
        wx.Frame.__init__(self,parent=None,title="SAXS-WAXS Control")

        # Icon
        from Icon import SetIcon
        SetIcon(self,"SAXS-WAXS Control")
        
        # Controls
        panel = wx.Panel(self)
        from EditableControls import ComboBox,TextCtrl
        from Controls import Control

        self.Environment = Control(panel,type=ComboBox,
            name="SAXS_WAXS_Control_Panel.Environment",globals=globals(),
            size=(80,-1),choices=["0 (NIH)","1 (APS)","2 (LCLS)"])

        self.Home = Control(panel,type=wx.ToggleButton,
            name="SAXS_WAXS_Control_Panel.Home",globals=globals(),
            size=(100,-1))

        self.ProgramRunning = Control(panel,type=wx.ToggleButton,
            name="SAXS_WAXS_Control_Panel.ProgramRunning",globals=globals(),
            size=(100,-1))

        self.GotoSaved = Control(panel,type=wx.Button,
            name="SAXS_WAXS_Control_Panel.GotoSaved",globals=globals(),
            label="Go To Saved Position",
            size=(180,-1))
        self.Save = Control(panel,type=wx.Button,
            name="SAXS_WAXS_Control_Panel.Save",globals=globals(),
            label="Save Current X,Y Positions",size=(180,-1))
        self.Inserted = Control(panel,type=wx.ToggleButton,
            name="SAXS_WAXS_Control_Panel.Inserted",globals=globals(),
            size=(150,-1))
        

        self.Mode = Control(panel,type=wx.ComboBox,
            name="SAXS_WAXS_Control_Panel.Mode",globals=globals(),
            size=(100,-1),choices=SAXS_WAXS_control.modes)
        
        self.ShutterEnabled = Control(panel,type=wx.CheckBox,
            name="SAXS_WAXS_Control_Panel.ShutterEnabled",globals=globals(),
            size=(80,-1))
        self.PumpEnabled = Control(panel,type=wx.CheckBox,
            name="SAXS_WAXS_Control_Panel.PumpEnabled",globals=globals(),
            size=(80,-1))

        self.PumpStep = Control(panel,type=ComboBox,
            name="SAXS_WAXS_Control_Panel.PumpStep",globals=globals(),
            size=(80,-1),choices=SAXS_WAXS_control.pump_step_choices)

        self.PumpPosition = Control(panel,type=TextCtrl,
            name="SAXS_WAXS_Control_Panel.PumpPosition",globals=globals(),
            size=(70,-1))
        self.PumpHomed = Control(panel,type=wx.ToggleButton,
            name="SAXS_WAXS_Control_Panel.PumpHomed",globals=globals(),
            size=(140,-1))

        choices = ["500","600","700","800","1000"]
        self.LoadSampleStep = Control(panel,type=ComboBox,
            name="SAXS_WAXS_Control_Panel.LoadSampleStep",globals=globals(),
            size=(70,-1),choices=choices)
        self.LoadSample = Control(panel,type=wx.ToggleButton,
            name="SAXS_WAXS_Control_Panel.LoadSample",globals=globals(),
            label="Load Sample",size=(140,-1))

        choices = ["-500","-600","-700","-800","-1000"]
        self.ExtractSampleStep = Control(panel,type=ComboBox,
            name="SAXS_WAXS_Control_Panel.ExtractSampleStep",globals=globals(),
            size=(70,-1),choices=choices)
        self.ExtractSample = Control(panel,type=wx.ToggleButton,
            name="SAXS_WAXS_Control_Panel.ExtractSample",globals=globals(),
            label="Extract Sample",size=(140,-1))

        choices = ["500","600","700","800","1000"]
        self.CirculateSampleStep = Control(panel,type=ComboBox,
            name="SAXS_WAXS_Control_Panel.CirculateSampleStep",globals=globals(),
            size=(70,-1),choices=choices)
        self.CirculateSample = Control(panel,type=wx.ToggleButton,
            name="SAXS_WAXS_Control_Panel.CirculateSample",globals=globals(),
            label="Circulate Sample",size=(140,-1))

        self.PumpSpeed = Control(panel,type=TextCtrl,
            name="SAXS_WAXS_Control_Panel.PumpSpeed",globals=globals(),
            size=(70,-1))

        # Layout
        flag = wx.ALIGN_CENTRE_HORIZONTAL|wx.ALL
        border = 5

        layout = wx.BoxSizer(wx.HORIZONTAL)
        left_panel = wx.BoxSizer(wx.VERTICAL)

        group = wx.BoxSizer(wx.HORIZONTAL)        
        text = wx.StaticText(panel,label="Environment:")
        group.Add (text,flag=flag,border=border)
        group.Add (self.Environment,flag=flag,border=border)
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
        a = wx.ALL
        
        text = wx.StaticText(panel,label="Mode:  ")        
        group.Add (text,(0,0),flag=r|cv)
        group.Add (self.Mode,(0,1),flag=l|cv)

        text = wx.StaticText(panel,label="X-ray ms shutter:  ")        
        group.Add (text,(1,0),flag=r|cv)
        group.Add (self.ShutterEnabled,(1,1),flag=l|cv)

        text = wx.StaticText(panel,label="Pump:  ")        
        group.Add (text,(2,0),flag=r|cv)
        group.Add (self.PumpEnabled,(2,1),flag=l|cv)

        text = wx.StaticText(panel,label="Pump Steps/Stroke:  ")        
        group.Add (text,(3,0),flag=r|cv)
        group.Add (self.PumpStep,(3,1),flag=l|cv)

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
        self.Fit()

        # Settings
        self.Environment.defaults = {"Value":"offline?","Enabled":False} 
        self.Environment.value = "SAXS_WAXS_control.environment"
        self.Environment.properties = {
            "Enabled": [
                (True, "SAXS_WAXS_control.ensemble_online"),
            ],
        }

        self.Home.defaults = {"Label":"Home","Enabled":False}
        self.Home.action = {
            False: "SAXS_WAXS_control.ensemble_homing = True",
            True:  "SAXS_WAXS_control.ensemble_homing = True",
        }
        self.Home.properties = {
            "Value": [
                (False, "SAXS_WAXS_control.ensemble_homed == False"),
                (True,  "SAXS_WAXS_control.ensemble_homed == True"),
            ],
            "Enabled": [
                (False, "SAXS_WAXS_control.ensemble_program_running == True"),
                (True,  "SAXS_WAXS_control.ensemble_program_running == False"),
            ],
            "Label": [
                ("Homing","SAXS_WAXS_control.ensemble_homing == True"),
                ("Home",  "SAXS_WAXS_control.ensemble_homed == False"),
                ("Homed", "SAXS_WAXS_control.ensemble_homed == True"),
            ],
            "BackgroundColour": [
                ("yellow", "SAXS_WAXS_control.ensemble_homing == True"),
                ("green", "SAXS_WAXS_control.ensemble_homed == True"),
                ("red",   "SAXS_WAXS_control.ensemble_homed == False"),
            ],
        }
        
        self.ProgramRunning.defaults = {"Label":"Start [Stop]","Enabled":False}
        self.ProgramRunning.action = {
            False: "SAXS_WAXS_control.ensemble_program_running = False",
            True:  "SAXS_WAXS_control.ensemble_program_running = True",
        }
        self.ProgramRunning.properties = {
            "Value": [
                (False, "SAXS_WAXS_control.ensemble_program_running == False"),
                (True,  "SAXS_WAXS_control.ensemble_program_running == True"),
            ],
            "Enabled": [
                (False, "SAXS_WAXS_control.fault == True"),
                (True,  "SAXS_WAXS_control.fault == False"),
            ],
            "Label": [
                ("Fault","SAXS_WAXS_control.fault == True"),
                ("Start","SAXS_WAXS_control.ensemble_program_running == False"),
                ("Stop" ,"SAXS_WAXS_control.ensemble_program_running == True"),
            ],
            "BackgroundColour": [
                ("green", "SAXS_WAXS_control.ensemble_program_running == True"),
                ("red",   "SAXS_WAXS_control.ensemble_program_running == False"),
            ],
        }

        self.GotoSaved.action = {
            True:  "SAXS_WAXS_control.inserted = True",
        }
        self.GotoSaved.defaults = {"Enabled":False}
        self.GotoSaved.properties = {
            "Enabled": [
                (True,"1-SAXS_WAXS_control.inserted"),
            ],
            "BackgroundColour": [
                ("red","SAXS_WAXS_control.XY_enabled == False"),
            ],
        }
        self.Save.action = {
            True:  "SAXS_WAXS_control.at_inserted_position = True",
        }
        self.Save.defaults = {"Enabled":False}
        self.Save.properties = {
            "Enabled": [
                (True,  "SAXS_WAXS_control.at_inserted_position == False"),
            ],
        }
        self.Inserted.action = {
            True:  "SAXS_WAXS_control.inserted = True",
            False:  "SAXS_WAXS_control.retracted = True",
        }
        self.Inserted.defaults = {"Enabled":False,"Label":"Inserted [Withdrawn]"}
        self.Inserted.properties = {
            "Value": [
                (True, "SAXS_WAXS_control.inserted == True"),
                (False,"SAXS_WAXS_control.retracted == True"),
            ],
            "Enabled": [
                (True,  "SAXS_WAXS_control.XY_enabled"),
            ],
            "Label": [
                ("Inserted", "SAXS_WAXS_control.inserted == True"),
                ("Retracted","SAXS_WAXS_control.retracted == True"),
                ("Insert","SAXS_WAXS_control.inserted == SAXS_WAXS_control.retracted"),
            ],
            "BackgroundColour": [
                ("green", "SAXS_WAXS_control.inserted == True"),
                ("yellow","SAXS_WAXS_control.retracted == True"),
                ("red","SAXS_WAXS_control.inserted == SAXS_WAXS_control.retracted"),
            ],
        }
        
        self.Mode.defaults = {"Value":"offline","Enabled":False}
        self.Mode.value = "SAXS_WAXS_control.mode"
        self.Mode.properties = {
            "Enabled": [
                (True,"SAXS_WAXS_control.timing_system_running == True"),
            ],
        }
        self.ShutterEnabled.defaults = {"Enabled":False,"Label":"offline"}
        self.ShutterEnabled.action = {
            False: "SAXS_WAXS_control.ms_on = False",
            True:  "SAXS_WAXS_control.ms_on = True",
        }
        self.ShutterEnabled.properties = {
            "Value": [
                (False, "SAXS_WAXS_control.ms_on == False"),
                (True,  "SAXS_WAXS_control.ms_on == True"),
            ],
            "Label": [
                ("", "SAXS_WAXS_control.timing_system_running == True"),
                ("stopped", "SAXS_WAXS_control.timing_system_running == False"),
            ],
            "Enabled": [
                (True,  "SAXS_WAXS_control.timing_system_running == True"),
            ],
        }
        self.PumpEnabled.defaults = {"Enabled":False,"Label":"offline"}
        self.PumpEnabled.action = {
            False: "SAXS_WAXS_control.pump_on = False",
            True:  "SAXS_WAXS_control.pump_on = True",
        }
        self.PumpEnabled.properties = {
            "Value": [
                (False, "SAXS_WAXS_control.pump_on == False"),
                (True,  "SAXS_WAXS_control.pump_on == True"),
            ],
            "Label": [
                ("", "SAXS_WAXS_control.timing_system_running == True"),
                ("stopped", "SAXS_WAXS_control.timing_system_running == False"),
            ],
            "Enabled": [
                (True,  "SAXS_WAXS_control.timing_system_running == True"),
            ],
        }
        self.PumpStep.defaults = {"Value":"offline","Enabled":False}
        self.PumpStep.value = "SAXS_WAXS_control.pump_step"
        self.PumpStep.properties = {
            "Enabled": [
                (True,"SAXS_WAXS_control.ensemble_online"),
            ],
        }

        self.PumpPosition.defaults = {"Value":"offline","Enabled":False}
        self.PumpPosition.value = "SAXS_WAXS_control.pump_position"
        self.PumpPosition.format = "%.1f"
        self.PumpPosition.properties = {
            "Enabled": [
                (True,"SAXS_WAXS_control.ensemble_online"),
            ],
        }
        
        self.PumpHomed.defaults = {"Label":"Home","Enabled":False}
        self.PumpHomed.action = {
            False: "SAXS_WAXS_control.pump_homed = True",
            True:  "SAXS_WAXS_control.pump_homed = True",
        }
        self.PumpHomed.properties = {
            "Value": [
                (True,  "SAXS_WAXS_control.pump_homed == True"),
            ],
            "Enabled": [
                (True,  "SAXS_WAXS_control.pump_movable"),
            ],
            "Label": [
                ("Home",  "SAXS_WAXS_control.pump_homed == False"),
                ("Homed", "SAXS_WAXS_control.pump_homed == True"),
            ],
            "BackgroundColour": [
                ("green", "SAXS_WAXS_control.pump_homed == True"),
                ("red",   "SAXS_WAXS_control.pump_homed == False"),
            ],
        }
        self.LoadSampleStep.value = "SAXS_WAXS_control.load_step"
        self.ExtractSampleStep.value = "SAXS_WAXS_control.extract_step"
        self.CirculateSampleStep.value = "SAXS_WAXS_control.circulate_step"

        self.LoadSample.action = {
            False: "SAXS_WAXS_control.sample_loading = False",
            True:  "SAXS_WAXS_control.sample_loading = True",
        }
        self.LoadSample.defaults = {"Enabled":False}
        self.LoadSample.properties = {
            "Value": [
                (True,"SAXS_WAXS_control.sample_loading == True"),
            ],
            "Enabled": [
                (True,  "SAXS_WAXS_control.pump_movable"),
            ],
            "Label": [
                ("Load Sample","not SAXS_WAXS_control.sample_loading"),
                ("Cancel Load","SAXS_WAXS_control.sample_loading"),
            ],
            "BackgroundColour": [
                ("yellow", "SAXS_WAXS_control.sample_loading"),
                ("red", "SAXS_WAXS_control.pump_enabled == False"),
            ],
        }
        self.ExtractSample.action = {
            False: "SAXS_WAXS_control.sample_extracting = False",
            True:  "SAXS_WAXS_control.sample_extracting = True",
        }
        self.ExtractSample.defaults = {"Enabled":False}
        self.ExtractSample.properties = {
            "Value": [
                (True,"SAXS_WAXS_control.sample_extracting == True"),
            ],
            "Enabled": [
                (True,  "SAXS_WAXS_control.pump_movable"),
            ],
            "Label": [
                ("Extract Sample","not SAXS_WAXS_control.sample_extracting"),
                ("Cancel Extract","SAXS_WAXS_control.sample_extracting"),
            ],
            "BackgroundColour": [
                ("yellow", "SAXS_WAXS_control.sample_extracting == True"),
                ("red", "SAXS_WAXS_control.pump_enabled == False"),
            ],
        }
        self.CirculateSample.action = {
            False: "SAXS_WAXS_control.sample_circulating = False",
            True:  "SAXS_WAXS_control.sample_circulating = True",
        }
        self.CirculateSample.defaults = {"Enabled":False}
        self.CirculateSample.properties = {
            "Value": [
                (True,"SAXS_WAXS_control.sample_circulating == True"),
            ],
            "Enabled": [
                (True,  "SAXS_WAXS_control.pump_movable"),
            ],
            "Label": [
                ("Circulate Sample","not SAXS_WAXS_control.sample_circulating"),
                ("Cancel Circulate","SAXS_WAXS_control.sample_circulating"),
            ],
            "BackgroundColour": [
                ("yellow", "SAXS_WAXS_control.sample_circulating"),
                ("red", "SAXS_WAXS_control.pump_enabled == False"),
            ],
        }
        self.PumpSpeed.defaults = {"Value":"offline","Enabled":False}
        self.PumpSpeed.value = "SAXS_WAXS_control.pump_speed"
        self.PumpSpeed.properties = {
            "Enabled": [
                (True,"SAXS_WAXS_control.ensemble_online"),
            ],
        }

        self.Show()

if __name__ == '__main__':
    from pdb import pm
    import logging; from tempfile import gettempdir
    logfile = gettempdir()+"/SAXS_WAXS_Control_Panel.log"
    logging.basicConfig(level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",filename=None)
    # Needed to initialize WX library
    if not hasattr(wx,"app"): wx.app = wx.App(redirect=False)
    panel = SAXS_WAXS_Control_Panel()
    wx.app.MainLoop()
