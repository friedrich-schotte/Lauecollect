#!/usr/bin/env python
"""
Graphical User Interface for FPGA Timing System.
Author: Friedrich Schotte
Date created: 2015-05-27
Date last modified: 2022-06-13
Revision comment: Using: Configuration_Table_Panel
"""
__version__ = "7.3.1"

from logging import warning
from traceback import format_exc

from Panel_3 import BasePanel
from reference import reference


class Timing_Panel(BasePanel):
    """Control Panel for FPGA Timing System"""
    from monitored_property import monitored_property
    timing_system_name = "BioCARS"

    def __init__(self, timing_system_name=None):
        if timing_system_name is not None:
            self.timing_system_name = timing_system_name
        BasePanel.__init__(self)

    icon = "Timing System"

    @monitored_property
    def title(self):
        return "Timing System [%s]" % self.timing_system_name

    @property
    def name(self):
        return "Timing_Panel.%s" % self.timing_system_name

    label_width = 190

    @property
    def parameters(self):
        return [
            [("Delay", self.composer, "delay", "time"), {"choices": self.delay_choices}],
            [("Nom. Delay", self.composer, "nom_delay", "time"), {"choices": self.delay_choices}],
            [("Mode", self.composer, "mode", "str"), {"choices_reference": reference(self.composer, "modes")}],
            [("Period [1-kHz cycles]", self.composer, "trigger_period_in_1kHz_cycles", "int"), {}],
            [("Detector", self.composer, "xdet_on", "Off/On"), {}],
            [("Pump (laser)", self.composer, "laser_on", "Off/On"), {}],
            [("Probe (X-Ray)", self.composer, "ms_on", "Off/On"), {}],
            [("Trans", self.composer, "trans_on", "Off/On"), {}],
            [("Circulate", self.composer, "pump_on", "Off/On"), {}],
            [("Trigger code", self.composer, "transc", "binary"), {}],
            [("Image number", self.timing_system.registers.image_number, "count", "int"), {}],
            [("X-ray detector trigger count", self.timing_system.channels.xdet.trig_count, "count", "int"), {}],
            [("X-ray detector acquisition count", self.timing_system.channels.xdet.acq_count, "count", "int"), {}],
            [("X-ray scope trigger count", self.timing_system.channels.xosct.trig_count, "count", "int"), {}],
            [("X-ray scope acquisition count", self.timing_system.channels.xosct.acq_count, "count", "int"), {}],
            [("Laser scope trigger count", self.timing_system.channels.losct.trig_count, "count", "int"), {}],
            [("Laser scope acquisition count", self.timing_system.channels.losct.acq_count, "count", "int"), {}],
            [("Pass number", self.timing_system.registers.pass_number, "count", "int"), {}],
            [("Pulses", self.timing_system.registers.pulses, "count", "int"), {}],
            [("Image number increment", self.composer, "image_number_inc", "Off/On"), {}],
            [("Pass number increment", self.composer, "pass_number_inc", "Off/On"), {}],
            [("Queue active", self.sequencer, "queue_active", "Not Active/Active"), {}],
            [("Acquiring", self.sequencer, "acquiring", "Idle/Acquiring"), {}],
            [("Current queue length [seq]", self.sequencer, "current_queue_length", "int"), {}],
            [("Current queue sequence cnt", self.sequencer, "current_queue_sequence_count", "int"), {}],
            [("Current queue repeat count", self.sequencer, "current_queue_repeat_count", "int"), {}],
            [("Current queue max repeat", self.sequencer, "current_queue_max_repeat_count", "int"), {}],
            [("Queue length [sequences]", self.sequencer, "queue_length", "int"), {}],
            [("Queue sequence count", self.sequencer, "queue_sequence_count", "int"), {}],
            [("Queue repeat count", self.sequencer, "queue_repeat_count", "int"), {}],
            [("Queue max repeat count", self.sequencer, "queue_max_repeat_count", "int"), {}],
            [("Next queue sequence cnt", self.sequencer, "next_queue_sequence_count", "int"), {}],
            [("Cache", self.sequencer, "cache_enabled", "Disabled/Caching"), {}],
            [("Packets generated", self.sequencer, "cache_size", "int"), {}],
            [("Packets loaded", self.sequencer, "remote_cache_size", "int"), {}],
            [("Sequencer Configured", self.sequencer, "configured", "Not Configured/Configured"), {}],
            [("Sequencer Running", self.sequencer, "running", "Stopped/Running"), {}],
            [("Sequence generator", self.composer, "generator", "str"), {"read_only": True}],
            [("Sequence generator version", self.composer, "generator_version", "str"), {"read_only": True}],
            [("Timing sequence version", self.composer, "timing_sequence_version", "str"), {"read_only": True}],
            [("Heatload chopper phase", self.timing_system.registers.hlcnd, "value", "time.6"),
             {"choices": self.hlc_choices}],
            [("Heatload chop. act. phase", self.timing_system.registers.hlcad, "value", "time.6"),
             {"choices": self.hlc_choices}],
            [("High-speed chopper phase", self.timing_system.channels.hsc.delay, "value", "time.4"),
             {"choices": self.hsc_choices}],
            [("P0 shift", self.timing_system.p0_shift, "value", "time.4"), {}],
            [("X-ray delay", self.composer, "xd", "time.6"), {}],
        ]

    standard_view = [
        "Delay",
        "Mode",
        "Pump (laser)",
        "Acquiring",
        "Sequencer Running",
    ]

    @property
    def application_buttons(self):
        from Panel_3 import Application_Button
        from application import application
        return [
            Application_Button(
                "Channels...",
                application(f"{self.domain_name}.Timing_Channel_Configuration_Panel.Timing_Channel_Configuration_Panel('{self.domain_name}')")
            ),
            Application_Button(
                "Clock...",
                application(f"{self.domain_name}.Timing_Clock_Configuration_Panel.Timing_Clock_Configuration_Panel('{self.domain_name}')")
            ),
            Application_Button(
                "Sequence...",
                application(f"{self.domain_name}.Configuration_Table_Panel.Configuration_Table_Panel('{self.domain_name}.sequence_modes')")
            ),
            Application_Button(
                "PP Modes...",
                application(f"{self.domain_name}.Configuration_Table_Panel.Configuration_Table_Panel('{self.domain_name}.timing_modes')")
            ),
        ]

    @property
    def application_menu_items(self):
        from Panel_3 import Application_Menu_Item
        from application import application
        return [
            Application_Menu_Item(
                "Setup...",
                application(f"{self.domain_name}.Timing_Setup_Panel.Timing_Setup_Panel('{self.domain_name}')")
            ),
            Application_Menu_Item(
                "Channel Configuration...",
                application(f"{self.domain_name}.Timing_Channel_Configuration_Panel.Timing_Channel_Configuration_Panel('{self.domain_name}')")
            ),
            Application_Menu_Item(
                "Calibration...",
                application(f"{self.domain_name}.Timing_Calibration_Panel.Timing_Calibration_Panel('{self.domain_name}')")
            ),
            Application_Menu_Item(
                "Clock Configuration...",
                application(f"{self.domain_name}.Timing_Clock_Configuration_Panel.Timing_Clock_Configuration_Panel('{self.domain_name}')")
            ),
            Application_Menu_Item(
                "PP Modes...",
                application(f"{self.domain_name}.Configuration_Table_Panel.Configuration_Table_Panel('{self.domain_name}.timing_modes')")
            ),
            Application_Menu_Item(
                "Sequence Modes...",
                application(f"{self.domain_name}.Configuration_Table_Panel.Configuration_Table_Panel('{self.domain_name}.sequence_modes')")
            ),
            Application_Menu_Item(
                "Configuration...",
                application(f"{self.domain_name}.Timing_Configuration_Panel.Timing_Configuration_Panel('{self.domain_name}')")
            ),
            Application_Menu_Item(
                "Delay Scan...",
                application(f"{self.domain_name}.Timing_System_Delay_Scan_Panel.Timing_System_Delay_Scan_Panel('{self.domain_name}')")
            ),
            Application_Menu_Item(
                "Laser On Scan...",
                application(f"{self.domain_name}.Timing_System_Laser_On_Scan_Panel.Timing_System_Laser_On_Scan_Panel('{self.domain_name}')")
            ),
        ]

    @property
    def composer(self):
        return self.timing_system.composer

    @property
    def sequencer(self):
        return self.timing_system.sequencer

    @property
    def timing_system(self):
        from timing_system_client import timing_system_client
        return timing_system_client(self.timing_system_name)

    @property
    def domain_name(self):
        return self.timing_system_name

    @property
    def delay_choices(self):
        from numpy import concatenate, arange
        choices = concatenate(([-100e-12, 0], 10 ** (arange(-10, 1, 1.0))))
        return choices

    @property
    def hlc_choices(self):
        choices = []
        from numpy import arange, finfo
        eps = finfo(float).eps
        hsct = self.timing_system.hsct
        try:
            choices = arange(-12 * hsct, +12 * hsct + eps, hsct)
        except ValueError:
            warning(format_exc())
        return choices

    @property
    def hsc_choices(self):
        choices = []
        from numpy import arange, finfo
        eps = finfo(float).eps
        P0t = self.timing_system.P0t
        try:
            choices = arange(-12 * P0t / 24, 12 * P0t / 24 + eps, P0t / 24)
        except ValueError:
            warning(format_exc())
        return choices


if __name__ == '__main__':
    timing_system_name = "BioCARS"
    # timing_system_name = "LaserLab"
    # timing_system_name = "TestBench"

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    from redirect import redirect

    redirect("%s.Timing_Panel" % timing_system_name, format=msg_format)
    # import autoreload
    import wx

    app = wx.GetApp() if wx.GetApp() else wx.App()
    self = Timing_Panel(timing_system_name)
    app.MainLoop()
