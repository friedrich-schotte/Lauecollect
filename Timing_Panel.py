#!/usr/bin/env python
"""
Grapical User Interface for FPGA Timing System.
Author: Friedrich Schotte
Date created: 2015-05-27
Date last modified: 2019-05-29
"""
__version__ = "5.3" # hsc_delay, cleanup

from logging import debug,info,warn,error

import wx, wx3_compatibility

from Panel import BasePanel
class Timing_Panel(BasePanel):
    """Control Panel for FPGA Timing System"""
    name = "Timing_Panel"
    title = "Timing"
    icon = "timing-system"

    def hlc_choices():
        from timing_system import timing_system
        from numpy import arange,finfo
        eps = finfo(float).eps
        hsct = timing_system.hsct
        choices = arange(-12*hsct,+12*hsct+eps,hsct)
        return choices

    def hsc_choices():
        from timing_system import timing_system
        from numpy import arange,finfo
        eps = finfo(float).eps
        P0t = timing_system.P0t
        choices = arange(-12*P0t/24,12*P0t/24+eps,P0t/24)
        return choices

    from Ensemble_SAXS_pp import Ensemble_SAXS
    from timing_sequence import timing_sequencer
    parameters = [
        [("Delay",                 Ensemble_SAXS,"delay",    "time"  ),{}],
        [("Nom. Delay",            Ensemble_SAXS,"nom_delay","time"  ),{}],
        [("Mode",                  Ensemble_SAXS,"mode"              ),{}],
        [("Period [1-kHz cycles]", Ensemble_SAXS,"trigger_period_in_1kHz_cycles"),{}],
        [("Laser",                 Ensemble_SAXS,"laser_on", "Off/On"),{}],
        [("X-ray ms shutter",      Ensemble_SAXS,"ms_on",    "Off/On"),{}],
        [("Pump",                  Ensemble_SAXS,"pump_on",  "Off/On"),{}],
        [("Trigger code",          Ensemble_SAXS,"transc",   "binary"),{}],
        [("X-ray detector trigger",Ensemble_SAXS,"xdet_on",  "Off/On"),{}],
        [("Image number",          Ensemble_SAXS,"image_number"      ),{}],
        [("X-ray detector count",  Ensemble_SAXS,"xdet_count",      "integer"),{}],
        [("X-ray detector trigger count",   timing_sequencer,"xdet_trig_count", "integer"),{}],
        [("X-ray detector acquistion count",timing_sequencer,"xdet_acq_count",  "integer"),{}],
        [("X-ray scope trigger count",      timing_sequencer,"xosct_trig_count","integer"),{}],
        [("X-ray scope acquistion count",   timing_sequencer,"xosct_acq_count", "integer"),{}],
        [("Laser scope trigger count",      timing_sequencer,"losct_trig_count","integer"),{}],
        [("Laser scope acquistion count",   timing_sequencer,"losct_acq_count", "integer"),{}],
        [("Passes",                Ensemble_SAXS,"passes"            ),{}],
        [("Pass number",           Ensemble_SAXS,"pass_number"       ),{}],
        [("Pulses",                Ensemble_SAXS,"pulses"            ),{}],
        [("Image number increment",Ensemble_SAXS,"image_number_inc","Off/On"),{}],
        [("Pass number increment", Ensemble_SAXS,"pass_number_inc" ,"Off/On"),{}],
        [("Acquiring",               timing_sequencer,  "acquiring",       "Idle/Acquiring"),{}],
        [("Queue active",            timing_sequencer,  "queue_active"    ,"Not Active/Active"),{}],
        [("Queue length [sequences]",timing_sequencer,  "queue_length",    "integer"),{}],
        [("Current queue length [seq]",timing_sequencer,"current_queue_length","integer"),{}],
        [("Queue sequence count"    ,timing_sequencer,  "queue_sequence_count","integer"),{}],
        [("Current queue sequence cnt",timing_sequencer,"current_queue_sequence_count","integer"),{}],
        [("Queue repeat count"      ,timing_sequencer,  "queue_repeat_count","integer"),{}],
        [("Current queue repeat count",timing_sequencer,"current_queue_repeat_count","integer"),{}],
        [("Queue max repeat count",  timing_sequencer,  "queue_max_repeat_count","integer"),{}],
        [("Current queue max repeat",timing_sequencer,"current_queue_max_repeat_count","integer"),{}],
        [("Next queue sequence cnt",timing_sequencer,"next_queue_sequence_count","integer"),{}],
        [("Cache",                 timing_sequencer,"cache_enabled","Disabled/Caching"),{}],
        [("Packets generated",     timing_sequencer,"cache_size"),{}],
        [("Packets loaded",        timing_sequencer,"remote_cache_size"),{}],
        [("Sequencer Running",     Ensemble_SAXS,"running","Stopped/Running"),{}],
        [("Sequence generator",    Ensemble_SAXS,"generator"),{"read_only":True}],
        [("Sequence generator version",Ensemble_SAXS,"generator_version"),{"read_only":True}],
        [("Heatload chopper phase",Ensemble_SAXS,"hlcnd","time.6"  ),{"choices":hlc_choices}],
        [("Heatload chop. act. phase",Ensemble_SAXS,"hlcad","time.6"  ),{"choices":hlc_choices}],
        [("High-speed chopper phase",Ensemble_SAXS,"hsc_delay","time.4"),{"choices":hsc_choices}],
        [("P0 shift",                timing_sequencer,"p0_shift","time.4"),{}],
        [("X-ray delay",             Ensemble_SAXS,"xd","time.6"),{}],
    ]
    standard_view = [
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
    def __init__(self,parent=None):
        from Panel import PropertyPanel
        from Timing_Setup_Panel import Timing_Setup_Panel
        from Timing_Channel_Configuration_Panel import Timing_Channel_Configuration_Panel
        from Timing_Calibration_Panel import Timing_Calibration_Panel
        from Timing_Clock_Configuration_Panel import Timing_Clock_Configuration_Panel
        from PP_Modes_Panel import PP_Modes_Panel
        from Sequence_Modes_Panel import Sequence_Modes_Panel
        from Timing_Configuration_Panel import Timing_Configuration_Panel

        BasePanel.__init__(self,parent=parent,
            name=self.name,
            title=self.title,
            icon=self.icon,
            component=PropertyPanel,
            parameters=self.parameters,
            standard_view=self.standard_view,
            label_width=180,
            refresh=True,
            live=True,
            subpanels=[
                ["Setup...",                Timing_Setup_Panel],
                ["Channel Configuration...",Timing_Channel_Configuration_Panel],
                ["Calibration...",          Timing_Calibration_Panel],
                ["Clock Configuration...",  Timing_Clock_Configuration_Panel],
                ["PP Modes...",             PP_Modes_Panel],
                ["Sequence Modes...",       Sequence_Modes_Panel],
                ["Configuration...",        Timing_Configuration_Panel],
            ],
            buttons=[
                ["Cal..",Timing_Calibration_Panel],
                ["Conf..",Timing_Channel_Configuration_Panel],
                ["Setup..",Timing_Setup_Panel],
                ["Modes..",PP_Modes_Panel],
            ],
        )


if __name__ == '__main__':
    from pdb import pm # for debugging
    from redirect import redirect
    redirect("Timing_Panel")
    import autoreload
    import wx
    wx.app = wx.App(redirect=False)
    panel = Timing_Panel()
    wx.app.MainLoop()
