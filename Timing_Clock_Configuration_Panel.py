#!/usr/bin/env python
"""
Grapical User Interface for FPGA Timing System.
Author: Friedrich Schotte
Date created: 2019-03-2
Date last modified: 2019-03-26
"""
__version__ = "1.0" 

from logging import debug,info,warn,error

from Panel import BasePanel
class Timing_Clock_Configuration_Panel(BasePanel):
    name = "Configuration"
    title = "Clock Configuration"
    icon = "timing-system"
    
    channels = dict([(i,"Channel %d"%i) for i in range(1,25)])
    RJ = dict([(24+i,"RJ45:%d"%i) for i in range(1,5)])
    input_sources = {0:'RF IN'}; input_sources.update(channels); input_sources.update(RJ)
    clock_sources = {}; clock_sources.update(input_sources); clock_sources.update({29:'int. 350 MHz'})
    sync_inton_sources = {0:'int. 10 Hz'}; sync_inton_sources.update(channels)
    from timing_sequence import timing_sequencer
    
    parameters = [
        [("RF clock in",                              timing_sequencer,  "clk_src",          repr(clock_sources)),{}],
        [("RF clock in frequency",                    timing_sequencer,  "clock_period",     "frequency.6"),{"choices": [1/351933980.,1/350e6,1/80e6]}],
        [("Clock manager",                            timing_sequencer,  "clk_on",           "Bypassed/Enabled"),{}],
        [("Clock multiplier",                         timing_sequencer,  "clock_multiplier", "integer"),{"choices": range(1,33)}],
        [("Clock divider",                            timing_sequencer,  "clock_divider",    "integer"),{"choices": range(1,33)}],
        [("Clock DFS frequency mode",                 timing_sequencer,  "clk_dfs_mode",     "Low freq./High freq."),{}],
        [("Clock DLL frequency mode",                 timing_sequencer,  "clk_dll_mode",     "Low freq./High freq."),{}],
        [("Clock multiplier status",                  timing_sequencer,  "clk_locked",       "Fault/Phase-locked"),{"read_only": True}],
        [("Internal clock frequency",                 timing_sequencer,  "bct",              "frequency.6"),{"choices": [1/351933980.,1/350000000.]}],
        [("SB clock in",                              timing_sequencer,  "sbclk_src",        repr(input_sources)),{}],
        [("SB clock frequency",                       timing_sequencer,  "P0t",              "frequency.6"),{"choices": [1/(351933980./1296),1/120.]}],
        [("Clock shift step size",                    timing_sequencer,  "clk_shift_stepsize","time.6"),{"choices": [8.594e-12,8.907e-12]}],
        [("1-kHz clock divider of RF/4",              timing_sequencer,  "clk_88Hz_div_1kHz","integer"),{"choices": [1296/4*275,91500,83333]}],
        [("1-kHz clock frequency",                    timing_sequencer,  "hsct",             "frequency.4"),{"choices": [1/(351933980./1296/275),1/960.]}],
        [("1-kHz clock phased by SB clock",           timing_sequencer,  "p0_phase_1kHz",    "Off/On"),{}],
        [("1-kHz clock divider of SB clock",          timing_sequencer,  "p0_div_1kHz",      "integer"),{"choices": [275,1]}],
        [("Heatload chopper encoder in",              timing_sequencer,  "hlc_src",          repr(input_sources)),{}],
        [("Heatload chopper slots count",             timing_sequencer,  "hlc_nslots",       "integer"),{"choices": [12,4,1]}],
        [("X-ray base frequency divider of 1-kHz clock",timing_sequencer,"hlc_div",          "integer"),{"choices": [12,4,1]}],
        [("X-ray base frequency",                     timing_sequencer,  "hlct",             "frequency.4"),{"choices": [1/(351933980./1296/275),1/(351933980./1296/275/4),1/(351933980./1296/275/12),1/120.]}],
        [("Ns laser divider of 1-kHz clock",          timing_sequencer,  "nsl_div",          "integer"),{"choices": [96,48]}],
        [("Ns laser frequency",                       timing_sequencer,  "nslt",             "frequency.4"),{"choices": [1/(351933980./1296/275/12/8),1/(351933980./1296/275/12/4)]}],
        [("Ps oscillator clock auto-lock",            timing_sequencer,  "clk_shift_auto_reset","Off/On"),{}],
    ]
    standard_view = [
        "RF clock in",
        "RF clock in frequency"
        "SB clock in",
        "Clock manager",
        "Clock multiplier",
        "Clock divider",
        "Clock DFS frequency mode",
        "Clock DLL frequency mode",
        "Clock multiplier status",
        "Internal clock frequency",
    ]
    def __init__(self,parent=None,update=lambda: None):
        from Panel import PropertyPanel
        BasePanel.__init__(self,parent=parent,
            name=self.name,
            title=self.title,
            icon=self.icon,
            component=PropertyPanel,
            parameters=self.parameters,
            standard_view=self.standard_view,
            label_width=250,
            refresh=True,
            live=True,
        )
       
if __name__ == '__main__':
    from pdb import pm # for debugging
    from redirect import redirect
    redirect("Timing_Clock_Configuration_Panel")
    import wx
    app = wx.App(redirect=False) 
    panel = System_Clock_Configuration_Panel()
    app.MainLoop()
