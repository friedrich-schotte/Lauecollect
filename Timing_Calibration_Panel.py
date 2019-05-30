#!/usr/bin/env python
"""
Grapical User Interface for FPGA Timing System.
Author: Friedrich Schotte
Date created: 2019-03-26
Date last modified: 2019-05-29
"""
__version__ = "1.1" # p0_shift, cleanup

from logging import debug,info,warn,error

import wx

from Panel import BasePanel
class Timing_Calibration_Panel(BasePanel):
    name = "Calibration"
    title = "Calibration"
    icon = "timing-system"
    update = None

    standard_view = [
        "X-ray Scope Trigger",
        "Laser to X-ray Delay",
        "Ps Laser Oscillator Phase",
        "Ps Laser Trigger",
        "Laser Scope Trigger",
        "High-Speed Chopper Phase",
    ]
    
    def __init__(self,parent=None,update=None,*args,**kwargs):
        if update is not None: self.update = update
        if self.update is None:
            from Ensemble_SAXS_pp import Ensemble_SAXS
            self.update = [Ensemble_SAXS.update]
            ##from timing_sequence import timing_sequencer
            ##update=[timing_sequencer.cache_clear,timing_sequencer.update]

        from timing_system import timing_system
        self.parameters = [
            [[timing_system.channels.xosct,    "X-ray Scope Trigger",          ],{"update": self.update}],
            [[timing_system.channels.delay,    "Laser to X-ray Delay",         ],{"update": self.update}],
            [[timing_system.channels.psod3,    "Ps Laser Osc. Delay",          ],{"update": self.update}],
            ##[[timing_system.channels.psd1,     "Ps Laser Osc. Delay GigaBaudics",],{"update": self.update}],
            [[timing_system.channels.pst,      "Ps Laser Trigger",             ],{"update": self.update}],
            [[timing_system.channels.nsq,      "Ns Laser Q-Switch Trigger",    ],{"update": self.update}],
            [[timing_system.channels.nsf,      "Ns Laser Flash Lamp Trigger",  ],{"update": self.update}],
            [[timing_system.channels.losct,    "Laser Scope Trigger",          ],{"update": self.update}],
            [[timing_system.channels.lcam,     "Laser Camera Trigger",         ],{"update": self.update}],
            [[timing_system.hlcnd,             "Heatload Chopper Phase",       ],{"keep_value": True}],
            [[timing_system.hlcad,             "Heatload Chop. Act. Phase",    ],{"keep_value": True}],
            [[timing_system.channels.hsc.delay,"High-Speed Chopper Phase",     ],{"update": self.update, "keep_value": True}],
            [[timing_system.p0_shift,          "P0 Shift",                     ],{}],
            [[timing_system.channels.ms,       "X-ray Shutter Delay",          ],{"update": self.update}],
            [[timing_system.channels.ms,       "X-ray Shutter Pulse Length",   ],{"update": self.update,"attribute": "pulse_length"}],
            [[timing_system.channels.xdet,     "X-ray Detector Delay",         ],{"update": self.update}],
            [[timing_system.channels.xdet,     "X-ray Detector Pulse Length",  ],{"update": self.update,"attribute": "pulse_length"}],
            [[timing_system.channels.trans,    "Sample Transl. Delay",         ],{"update": self.update}],
            [[timing_system.channels.trans,    "Sample Transl. Pulse Length",  ],{"update": self.update,"attribute": "pulse_length"}],
        ]
        BasePanel.__init__(self,
            parent=parent,
            name=self.name,
            icon=self.icon,
            title=self.title,
            component=CalibrationControl,
            parameters=self.parameters,
            standard_view=self.standard_view,
            label_width=250,
            refresh=False,
            live=False,
            *args,
            **kwargs
        )

from Panel import BasePanel

class CalibrationControl(wx.Panel):
    """A component for calibration window"""
    from persistent_property import persistent_property
    step = persistent_property("step",10e-9)
    icon = "timing-system"

    def __init__(self,parent,register,title,update=[lambda: None],
        pre_update=None,post_update=None,keep_value=False,attribute="offset",
        *args,**kwargs):
        """
        update: list of procedures to be called after tweeking the offset
        pre_update: procedure to be called before tweeking the offset
        """
        wx.Panel.__init__(self,parent)
        self.title = title
        self.register = register
        if update is not None:      self.update = update
        if pre_update is not None:  self.pre_update = pre_update
        if post_update is not None: self.post_update = post_update
        self.keep_value = keep_value
        self.attribute = attribute
        
        self.name = "TimingPanel.Calibration."+str(register)
        from Icon import SetIcon
        SetIcon(self,self.icon)

        # Controls
        style = wx.TE_PROCESS_ENTER
        from EditableControls import TextCtrl
        self.Current = TextCtrl(self,size=(155,-1),style=style)
        self.Decr = wx.Button(self,label="<",size=(30,-1))
        self.Incr = wx.Button(self,label=">",size=(30,-1))
        self.Set = wx.Button(self,label="Set...",size=(50,-1))

        from numpy import arange,unique
        from timing_system import round_next 
        choices = 10**arange(-11.0,-2.01,1)
        dt = self.register.stepsize
        choices = [round_next(t,dt) for t in choices]
        choices = unique(choices)
        choices = choices[choices>0]
        from time_string import time_string
        choices = [time_string(t) for t in choices]

        from EditableControls import ComboBox
        self.Step = ComboBox(self,size=(80,-1),choices=choices,style=style,
            value=time_string(self.next_step(self.step)))
        # Callbacks
        self.Bind(wx.EVT_TEXT_ENTER,self.OnChange,self.Current)
        self.Bind(wx.EVT_COMBOBOX,self.OnChange,self.Current)
        self.Bind(wx.EVT_TEXT_ENTER,self.OnStep,self.Step)
        self.Bind(wx.EVT_COMBOBOX,self.OnStep,self.Step)
        self.Bind(wx.EVT_BUTTON,self.OnDecr,self.Decr)
        self.Bind(wx.EVT_BUTTON,self.OnIncr,self.Incr)
        self.Bind(wx.EVT_BUTTON,self.OnSet,self.Set)
        # Layout
        layout = wx.GridBagSizer(1,1)
        layout.SetEmptyCellSize((0,0))
        av = wx.ALIGN_CENTRE_VERTICAL
        ah = wx.ALIGN_CENTRE_HORIZONTAL
        e = wx.EXPAND
        t = wx.StaticText(self,label=self.title,size=(110,-1))
        t.Wrap(110)
        layout.Add (t,(0,0),span=(2,1),flag=av)
        layout.Add (self.Decr,(0,2),flag=av)
        layout.Add (self.Current,(0,3),flag=av|e)
        layout.Add (self.Incr,(0,4),flag=av)
        group = wx.BoxSizer(wx.HORIZONTAL)
        t = wx.StaticText(self,label="Step")
        group.Add (t,flag=av)
        group.AddSpacer ((5,5))
        group.Add (self.Step,flag=av)
        group.AddSpacer ((5,5))
        group.Add (self.Set,flag=av)
        layout.Add (group,(1,2),span=(1,3),flag=ah)
        self.SetSizer(layout)
        self.Fit()

        self.keep_alive()

    def keep_alive(self,event=None):
        """Periodically refresh the displayed settings (every second)."""
        self.refresh()
        self.timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.keep_alive,self.timer)
        self.timer.Start(1000,oneShot=True)

    def refresh(self):
        from numpy import isnan
        value = getattr(self.register,self.attribute)
        self.Current.Value = self.format(value,12)+" s" if not isnan(value) else ""

    @staticmethod    
    def format(x,precision=12):
        """Arrage the digits places after the decimal point in groups of three
        for easy reading.
        t: time in seconds"""
        s = "%+.*f" % (precision,x)
        i,f = s.split(".")[0],s.split(".")[-1]
        s = i+"."+" ".join([f[i:i+3] for i in range(0,len(f),3)])
        return s

    def OnChange(self,event):
        from time_string import seconds
        value = seconds(self.Current.Value.replace(" ",""))
        self.pre_update()
        setattr(self.register,self.attribute,value)
        for proc in self.update: proc()
        self.refresh()

    def OnStep(self,event):
        from time_string import time_string,seconds
        step = self.next_step(seconds(self.Step.Value))
        self.step = step
        self.Step.Value = time_string(self.step)
        self.refresh()
       
    def OnDecr(self,event):
        from time_string import seconds
        step = self.next_step(seconds(self.Step.Value))
        self.pre_update()
        value = getattr(self.register,self.attribute)
        value -= step
        setattr(self.register,self.attribute,value)
        self.post_update()
        for proc in self.update: proc()
        self.refresh()

    def OnIncr(self,event):
        from time_string import seconds
        step = self.next_step(seconds(self.Step.Value))
        self.pre_update()
        value = getattr(self.register,self.attribute)
        value += step
        setattr(self.register,self.attribute,value)
        self.post_update()
        for proc in self.update: proc()
        self.refresh()

    def OnSet(self,event):
        from time_string import time_string,seconds
        from numpy import isnan
        dlg = wx.TextEntryDialog(self,"New user value",
            "Redefine User Value","")
        dlg.Value = time_string(self.register.value)
        OK = (dlg.ShowModal() == wx.ID_OK)
        if not OK: return 
        value = seconds(dlg.Value)
        if isnan(value): return
        setattr(self.register,self.attribute,value - self.register.dial)
        ##self.register.define_value(value)
        self.refresh()

    def pre_update(self):
        """Keep the user value constant while tweeking the dial"""
        if self.keep_value:
            new_value = self.register.value
            stepsize = getattr(self.register,"stepsize",0)
            if not abs(new_value-self.value) < stepsize:
                self.value = new_value
    def post_update(self):
        """Keep the user value constant while tweeking the dial"""
        from numpy import isnan
        if self.keep_value and not isnan(self.value):
            self.register.value = self.value
    from numpy import nan
    value = nan

    def next_step(self,step):
        """Closest possible value for the offset increment
        step: offset increment in seconds"""
        from timing_system import round_next
        stepsize = self.register.stepsize
        if step > 0.5*stepsize:
            step = max(round_next(step,stepsize),stepsize)
        return step


if __name__ == '__main__':
    from pdb import pm # for debugging
    from redirect import redirect
    redirect("Timing_Calibration_Panel")
    import wx
    app = wx.App(redirect=False) 
    panel = Timing_Calibration_Panel()
    app.MainLoop()
