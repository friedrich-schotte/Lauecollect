#!/usr/bin/env python
"""Graphical User Interface for X-ray beam stabilization
Author: Friedrich Schotte
Date created: 2015-11-23
Date last modified: 2020-03-09
Revision comment: Cleanup
"""
__version__ = "1.2"

import wx

from Panel import BasePanel, PropertyPanel, ButtonPanel, TogglePanel, TweakPanel
from TimeChart import TimeChart


class XRay_Beam_Check_Panel(BasePanel):
    title = "X-Ray Beam Check"
    icon = "Tool"

    standard_view = [
        "X [mrad]",
        "Y [V]",
        "X Corr. [mrad]",
        "Y Corr. [V]",
        "X Scan",
        "Y Scan",
        "X Correction",
        "Y Correction",
    ]

    def __init__(self, parent=None):
        self.parameters = [
            [[PropertyPanel, "Timing Mode", self.settings, "timing_mode"], {"choices": self.settings.timing_modes}],
            [[PropertyPanel, "Beamline Mode", self.settings, "beamline_mode"], {"choices": self.settings.beamline_modes}],
            [[TimeChart, "X Control History", self.xray_beam_check.log, "date time", "x_control"],
             {"axis_label": "Control X [mrad]", "name": self.name + ".TimeChart"}],
            [[TimeChart, "Y Control History", self.xray_beam_check.log, "date time", "y_control"],
             {"axis_label": "Control Y [V]", "name": self.name + ".TimeChart"}],
            [[PropertyPanel, "Logfile", self.xray_beam_check.log, "filename"], {}],
            [[TweakPanel, "X [mrad]", self.xray_beam_check, "x_control"], {"digits": 4}],
            [[TweakPanel, "Y [V]", self.xray_beam_check, "y_control"], {"digits": 4}],
            [[PropertyPanel, "X Corr. [mrad]", self.xray_beam_check, "x_control_corrected"], {"digits": 4, "read_only": True}],
            [[PropertyPanel, "Y Corr. [V]", self.xray_beam_check, "y_control_corrected"], {"digits": 4, "read_only": True}],
            [[TogglePanel, "X Scan", self.xray_beam_check, "x_scan_running"], {"type": "Start/Cancel"}],
            [[TogglePanel, "Y Scan", self.xray_beam_check, "y_scan_running"], {"type": "Start/Cancel"}],
            [[ButtonPanel, "X Correction", self.xray_beam_check, "apply_x_correction"], {"label": "Apply"}],
            [[ButtonPanel, "Y Correction", self.xray_beam_check, "apply_y_correction"], {"label": "Apply"}],
        ]
        self.subpanels = [Settings]

        BasePanel.__init__(self, parent=parent)

    @property
    def xray_beam_check(self):
        from xray_beam_check import xray_beam_check
        return xray_beam_check

    @property
    def settings(self):
        return self.xray_beam_check.settings


class Settings(BasePanel):
    title = "Settings"
    standard_view = [
        "X1 Motor",
        "X2 Motor",
        "Y Motor",
        "X Resolution [mrad]",
        "Y Resolution [V]",
        "X Scan Step [mrad]",
        "Y Scan Step [V]",
        "X Aperture Motor",
        "Y Aperture Motor",
        "X Aperture (scan) [mm]",
        "Y Aperture (scan) [mm]",
        "X Aperture (norm) [mm]",
        "Y Aperture (norm) [mm]",
    ]
    subname = False

    def __init__(self, parent=None):
        self.parameters = [
            [[PropertyPanel, "Timing System", self.settings, "timing_system_ip_address"], {}],
            [[PropertyPanel, "Oscilloscope", self.settings, "scope_ip_address"], {}],
            [[PropertyPanel, "X1 Motor", self.settings, "x1_motor"], {}],
            [[PropertyPanel, "X2 Motor", self.settings, "x2_motor"], {}],
            [[PropertyPanel, "Y Motor", self.settings, "y_motor"], {}],
            [[TweakPanel, "X Resolution [mrad]", self.settings, "x_resolution"], {"digits": 4}],
            [[TweakPanel, "Y Resolution [V]", self.settings, "y_resolution"], {"digits": 4}],
            [[TweakPanel, "X Scan Step [mrad]", self.settings, "dx_scan"], {"digits": 4}],
            [[TweakPanel, "Y Scan Step [V]", self.settings, "dy_scan"], {"digits": 4}],
            [[PropertyPanel, "X Aperture Motor", self.settings, "x_aperture_motor"], {}],
            [[PropertyPanel, "Y Aperture Motor", self.settings, "y_aperture_motor"], {}],
            [[TweakPanel, "X Aperture [mm]", self.settings, "x_aperture"], {"digits": 4}],
            [[TweakPanel, "Y Aperture [mm]", self.settings, "y_aperture"], {"digits": 4}],
            [[TweakPanel, "X Aperture (scan) [mm]", self.settings, "x_aperture_scan"], {"digits": 4}],
            [[TweakPanel, "Y Aperture (scan) [mm]", self.settings, "y_aperture_scan"], {"digits": 4}],
            [[TweakPanel, "X Aperture (norm) [mm]", self.settings, "x_aperture_norm"], {"digits": 4}],
            [[TweakPanel, "Y Aperture (norm) [mm]", self.settings, "y_aperture_norm"], {"digits": 4}],
        ]
        BasePanel.__init__(self, parent=parent)

    @property
    def xray_beam_check(self):
        from xray_beam_check import xray_beam_check
        return xray_beam_check

    @property
    def settings(self):
        return self.xray_beam_check.settings


if __name__ == '__main__':
    # from pdb import pm

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    from redirect import redirect

    redirect("XRay_Beam_Check_Panel", format=msg_format)
    app = wx.GetApp() if wx.GetApp() else wx.App()
    panel = XRay_Beam_Check_Panel()
    app.MainLoop()
