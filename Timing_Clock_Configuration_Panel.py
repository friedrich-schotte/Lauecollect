#!/usr/bin/env python
"""
Configuration panel for the BioCARS FPGA timing system
Clock settings

Author: Friedrich Schotte
Date created: 2019-03-02
Date last modified: 2022-04-05
Revision comment: Renamed: timing_system_client
"""
__version__ = "1.8.1"

from Panel_3 import BasePanel


class Timing_Clock_Configuration_Panel(BasePanel):
    icon = "timing-system"
    timing_system_name = "BioCARS"
    label_width = 270

    @property
    def title(self):
        return "Timing System - Clock Configuration [%s]" % self.timing_system_name

    @property
    def name(self):
        return "Timing_Clock_Configuration_Panel.%s" % self.timing_system_name

    channels = dict([(i, "Channel %d" % i) for i in range(1, 25)])
    RJ = dict([(24 + i, "RJ45:%d" % i) for i in range(1, 5)])
    input_sources = {0: 'RF IN'}
    input_sources.update(channels)
    input_sources.update(RJ)
    clock_sources = {}
    clock_sources.update(input_sources)
    clock_sources.update({29: 'int. 350 MHz'})
    sync_inton_sources = {0: 'int. 10 Hz'}
    sync_inton_sources.update(channels)

    def __init__(self, timing_system_name=None, parent=None):
        if timing_system_name is not None:
            self.timing_system_name = timing_system_name

        self.parameters = [
            [("RF clock in", self.timing_system.registers.clk_src, "count", repr(self.clock_sources)), {}],
            [("RF clock in frequency", self.timing_system, "clock_period", "frequency.6"), {"choices": [1 / 351933980., 1 / 350e6, 1 / 80e6]}],
            [("Clock manager", self.timing_system.registers.clk_on, "count", "Bypassed/Enabled"), {}],
            [("Clock multiplier", self.timing_system, "clock_multiplier", "int"), {"choices": range(1, 33)}],
            [("Clock divider", self.timing_system, "clock_divider", "int"), {"choices": range(1, 33)}],
            [("Clock DFS frequency mode", self.timing_system.registers.clk_dfs_mode, "count", "Low freq./High freq."), {}],
            [("Clock DLL frequency mode", self.timing_system.registers.clk_dll_mode, "count", "Low freq./High freq."), {}],
            [("Clock multiplier auto lock", self.timing_system.registers.clk_autolock, "count", "Off/On"), {}],
            [("Clock multiplier status", self.timing_system.registers.clk_locked, "count", "Fault/Phase-locked"), {"read_only": True}],
            [("Internal clock frequency", self.timing_system, "bct", "frequency.6"), {"choices": [1 / 351933980., 1 / 350000000.]}],
            [("SB clock in", self.timing_system.registers.sbclk_src, "count", repr(self.input_sources)), {}],
            [("SB clock frequency", self.timing_system, "P0t", "frequency.6"), {"choices": [1 / (351933980. / 1296), 1 / 120.]}],
            [("Clock shift step size", self.timing_system, "clk_shift_stepsize", "time.6"), {"choices": [8.594e-12, 8.907e-12]}],
            [("1-kHz clock divider of RF/4", self.timing_system.registers.clk_88Hz_div_1kHz, "count", "int"), {"choices": [1296 / 4 * 275, 91500, 83333]}],
            [("1-kHz clock frequency", self.timing_system, "hsct", "frequency.4"), {"choices": [1 / (351933980. / 1296 / 275), 1 / 960.]}],
            [("1-kHz clock phased by SB clock", self.timing_system.registers.p0_phase_1kHz, "count", "Off/On"), {}],
            [("1-kHz clock divider of SB clock", self.timing_system.registers.p0_div_1kHz, "count", "int"), {"choices": [275, 1]}],
            [("Heatload chopper encoder in", self.timing_system.registers.hlc_src, "count", repr(self.input_sources)), {}],
            [("Heatload chopper slots count", self.timing_system, "hlc_nslots", "int"), {"choices": [12, 4, 1]}],
            [("Heatload chopper phase matching period", self.timing_system, "phase_matching_period", "int"), {"choices": [12, 4, 1]}],
            [("Sequencer phase matching period", self.timing_system.sequencer, "phase_matching_period", "int"), {"choices": [12, 4, 1]}],
            [("X-ray base frequency divider of 1-kHz clock", self.timing_system, "hlc_div", "int"), {"choices": [12, 4, 1]}],
            [("X-ray base frequency", self.timing_system, "hlct", "frequency.4"),
             {"choices": [1 / (351933980. / 1296 / 275), 1 / (351933980. / 1296 / 275 / 4), 1 / (351933980. / 1296 / 275 / 12), 1 / 120.]}],
            [("Ns laser divider of 1-kHz clock", self.timing_system, "nsl_div", "int"), {"choices": [96, 48]}],
            [("Ns laser frequency", self.timing_system, "nslt", "frequency.4"),
             {"choices": [1 / (351933980. / 1296 / 275 / 12 / 8), 1 / (351933980. / 1296 / 275 / 12 / 4)]}],
            [("Ps oscillator clock auto-lock", self.timing_system.registers.clk_shift_auto_reset, "count", "Off/On"), {}],
        ]

        BasePanel.__init__(self, parent=parent)

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

    @property
    def timing_system(self):
        from timing_system_client import timing_system_client
        return timing_system_client(self.timing_system_name)


if __name__ == '__main__':
    # from pdb import pm  # for debugging

    name = "BioCARS"
    # name = "LaserLab"
    from redirect import redirect

    redirect("Timing_Clock_Configuration_Panel.%s" % name)
    import wx

    app = wx.App()
    panel = Timing_Clock_Configuration_Panel(name)
    app.MainLoop()
