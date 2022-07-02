#!/usr/bin/env python
"""
Graphical User Interface for FPGA Timing System.
Author: Friedrich Schotte
Date created: 2019-03-26
Date last modified: 2022-04-11
Revision comment: Using timing system server
"""
__version__ = "1.4"

import logging
import wx
from Panel import BasePanel


class Timing_Calibration_Panel(BasePanel):
    timing_system_name = "BioCARS"
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

    def __init__(self, timing_system_name=None, parent=None, *args, **kwargs):
        if timing_system_name is not None:
            self.timing_system_name = timing_system_name

        self.name = "Timing_Calibration_Panel.%s" % self.timing_system_name
        self.title = "Timing System Calibration (%s)" % self.timing_system_name

        if self.update is None:
            self.update = [self.timing_system.composer.update]

        self.parameters = [
            [[self.timing_system.channels.xosct, "X-ray Scope Trigger", ], {"update": self.update}],
            [[self.timing_system.delay, "Laser to X-ray Delay", ], {"update": self.update}],
            [[self.timing_system.channels.psod3, "Ps Laser Osc. Delay", ], {"update": self.update}],
            [[self.timing_system.channels.pst, "Ps Laser Trigger", ], {"update": self.update}],
            [[self.timing_system.channels.nsq, "Ns Laser Q-Switch Trigger", ], {"update": self.update}],
            [[self.timing_system.channels.nsf, "Ns Laser Flash Lamp Trigger", ], {"update": self.update}],
            [[self.timing_system.channels.losct, "Laser Scope Trigger", ], {"update": self.update}],
            [[self.timing_system.channels.lcam, "Laser Camera Trigger", ], {"update": self.update}],
            [[self.timing_system.registers.hlcnd, "Heatload Chopper Phase", ], {"keep_value": True}],
            [[self.timing_system.registers.hlcad, "Heatload Chop. Act. Phase", ], {"keep_value": True}],
            [[self.timing_system.channels.hsc.delay, "High-Speed Chopper Phase", ], {"keep_value": True}],  # "update": self.update,
            [[self.timing_system.registers.p0_shift, "P0 Shift", ], {}],
            [[self.timing_system.channels.ms, "X-ray Shutter Delay", ], {"update": self.update}],
            [[self.timing_system.channels.ms, "X-ray Shutter Pulse Length", ], {"update": self.update, "attribute": "pulse_length"}],
            [[self.timing_system.channels.xdet, "X-ray Detector Delay", ], {"update": self.update}],
            [[self.timing_system.channels.xdet, "X-ray Detector Pulse Length", ], {"update": self.update, "attribute": "pulse_length"}],
            [[self.timing_system.channels.trans, "Sample Transl. Delay", ], {"update": self.update}],
            [[self.timing_system.channels.trans, "Sample Transl. Pulse Length", ], {"update": self.update, "attribute": "pulse_length"}],
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

    @property
    def timing_system(self):
        from timing_system_client import timing_system_client
        return timing_system_client(self.timing_system_name)


class CalibrationControl(wx.Panel):
    """A component for calibration window"""
    from persistent_property import persistent_property
    step = persistent_property("step", 10e-9)
    icon = "timing-system"

    update = []

    def __init__(self, parent, register, title, update=None,
                 pre_update=None, post_update=None, keep_value=False, attribute="offset",
                 *_args, **_kwargs):
        """
        update: list of procedures to be called after tweaking the offset
        pre_update: procedure to be called before tweaking the offset
        """
        wx.Panel.__init__(self, parent)
        self.title = title
        self.register = register
        if update is not None:
            self.update = update
        if pre_update is not None:
            self.pre_update = pre_update
        if post_update is not None:
            self.post_update = post_update
        self.keep_value = keep_value
        self.attribute = attribute

        self.name = "TimingPanel.Calibration." + str(register)
        from Icon import SetIcon
        SetIcon(self, self.icon)

        # Controls
        style = wx.TE_PROCESS_ENTER
        from EditableControls import TextCtrl
        self.Current = TextCtrl(self, size=(155, -1), style=style)
        self.Decr = wx.Button(self, label="<", size=(30, -1))
        self.Incr = wx.Button(self, label=">", size=(30, -1))
        self.Set = wx.Button(self, label="Set...", size=(50, -1))

        from numpy import arange, unique
        choices = 10 ** arange(-11.0, -2.01, 1)
        dt = self.register.stepsize
        choices = [round_next(t, dt) for t in choices]
        choices = unique(choices)
        choices = choices[choices > 0]
        from time_string import time_string
        choices = [time_string(t) for t in choices]

        from EditableControls import ComboBox
        self.Step = ComboBox(self, size=(80, -1), choices=choices, style=style,
                             value=time_string(self.next_step(self.step)))
        # Callbacks
        self.Bind(wx.EVT_TEXT_ENTER, self.OnChange, self.Current)
        self.Bind(wx.EVT_COMBOBOX, self.OnChange, self.Current)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnStep, self.Step)
        self.Bind(wx.EVT_COMBOBOX, self.OnStep, self.Step)
        self.Bind(wx.EVT_BUTTON, self.OnDecr, self.Decr)
        self.Bind(wx.EVT_BUTTON, self.OnIncr, self.Incr)
        self.Bind(wx.EVT_BUTTON, self.OnSet, self.Set)
        # Layout
        layout = wx.GridBagSizer(1, 1)
        layout.SetEmptyCellSize((0, 0))
        av = wx.ALIGN_CENTRE_VERTICAL
        ah = wx.ALIGN_CENTRE_HORIZONTAL
        e = wx.EXPAND
        t = wx.StaticText(self, label=self.title, size=(110, -1))
        t.Wrap(110)
        layout.Add(t, (0, 0), span=(2, 1), flag=av)
        layout.Add(self.Decr, (0, 2), flag=av)
        layout.Add(self.Current, (0, 3), flag=av | e)
        layout.Add(self.Incr, (0, 4), flag=av)
        group = wx.BoxSizer(wx.HORIZONTAL)
        t = wx.StaticText(self, label="Step")
        group.Add(t, flag=av)
        group.AddSpacer(5)
        group.Add(self.Step, flag=av)
        group.AddSpacer(5)
        group.Add(self.Set, flag=av)
        layout.Add(group, (1, 2), span=(1, 3), flag=ah)
        self.SetSizer(layout)
        self.Fit()

        self.timer = wx.Timer(self)
        self.keep_alive()

    def keep_alive(self, _event=None):
        """Periodically refresh the displayed settings (every second)."""
        self.refresh()
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.keep_alive, self.timer)
        self.timer.Start(1000, oneShot=True)

    def refresh(self):
        from numpy import isnan
        value = getattr(self.register, self.attribute)
        self.Current.Value = self.format(value, 12) + " s" if not isnan(value) else ""

    @staticmethod
    def format(x, precision=12):
        """Arrange the digits places after the decimal point in groups of three
        for easy reading.
        t: time in seconds"""
        s = "%+.*f" % (precision, x)
        i, f = s.split(".")[0], s.split(".")[-1]
        s = i + "." + " ".join([f[i:i + 3] for i in range(0, len(f), 3)])
        return s

    def OnChange(self, _event):
        from time_string import seconds
        value = seconds(self.Current.Value.replace(" ", ""))
        self.pre_update()
        setattr(self.register, self.attribute, value)
        for proc in self.update:
            proc()
        self.refresh()

    def OnStep(self, _event):
        from time_string import time_string, seconds
        step = self.next_step(seconds(self.Step.Value))
        self.step = step
        self.Step.Value = time_string(self.step)
        self.refresh()

    def OnDecr(self, _event):
        self.tweak(-1)

    def OnIncr(self, _event):
        self.tweak(+1)

    def tweak(self, sign):
        from time_string import seconds
        from time import sleep

        self.pre_update()

        step = self.next_step(seconds(self.Step.Value))
        value = getattr(self.register, self.attribute)
        value += sign * step

        # logging.debug(f"{self.register}.value = {self.register.value}")
        logging.debug(f"{self.register}.{self.attribute} = {getattr(self.register, self.attribute)}")

        logging.debug(f"{self.register}.{self.attribute} -> {value}")
        setattr(self.register, self.attribute, value)

        logging.debug(f"{self.register}.{self.attribute} = {getattr(self.register, self.attribute)}")
        sleep(0.5)
        logging.debug(f"{self.register}.{self.attribute} = {getattr(self.register, self.attribute)}")
        # logging.debug(f"{self.register}.value = {self.register.value}")

        self.post_update()
        for proc in self.update:
            proc()
        self.refresh()

    def OnSet(self, _event):
        from time_string import time_string, seconds
        from numpy import isnan
        dlg = wx.TextEntryDialog(self, "New user value",
                                 "Redefine User Value", "")
        dlg.Value = time_string(self.register.value)
        OK = (dlg.ShowModal() == wx.ID_OK)
        if not OK:
            return
        value = seconds(dlg.Value)
        if isnan(value):
            return
        setattr(self.register, self.attribute, value - self.register.dial)
        # self.register.define_value(value)
        self.refresh()

    def pre_update(self):
        """Keep the user value constant while tweaking the dial"""
        if self.keep_value:
            logging.debug(f"{self.register}.value = {self.register.value}")
            new_value = self.register.value
            stepsize = getattr(self.register, "stepsize", 0)
            if not abs(new_value - self.value) < stepsize:
                self.value = new_value

    def post_update(self):
        """Keep the user value constant while tweaking the dial"""
        from numpy import isnan
        from time import sleep
        if self.keep_value and not isnan(self.value):
            logging.debug(f"{self.register}.value = {self.register.value}")
            logging.debug(f"{self.register}.value -> {self.value}")
            self.register.value = self.value
            logging.debug(f"{self.register}.value = {self.register.value}")
            sleep(0.5)
            logging.debug(f"{self.register}.value = {self.register.value}")

    from numpy import nan
    value = nan

    def next_step(self, step):
        """Closest possible value for the offset increment
        step: offset increment in seconds"""
        stepsize = self.register.stepsize
        if step > 0.5 * stepsize:
            step = max(round_next(step, stepsize), stepsize)
        return step


def round_next(x, step):
    """Rounds x up or down to the next multiple of step."""
    if step == 0:
        return x
    return round(x / step) * step


if __name__ == '__main__':
    timing_system_name = "BioCARS"
    from redirect import redirect

    redirect("Timing_Calibration_Panel.%s" % timing_system_name)
    import wx

    app = wx.GetApp() if wx.GetApp() else wx.App()
    self = Timing_Calibration_Panel(timing_system_name)
    app.MainLoop()
