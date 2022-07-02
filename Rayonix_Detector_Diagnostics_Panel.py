#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2022-02-07
Date last modified: 2022-05-13
Revision comment: Trigger count offset (median): Changed format
"""
from Panel_3 import BasePanel

__version__ = "1.0.1"


class Rayonix_Detector_Diagnostics_Panel(BasePanel):
    def __init__(self, domain_name):
        self.domain_name = domain_name
        BasePanel.__init__(self)

    @property
    def title(self): return f"Rayonix Detector Diagnostics [{self.domain_name}]"

    icon = "Rayonix Detector"

    @property
    def name(self): return f"{self.domain_name}/Rayonix_Detector_Diagnostics_Panel"

    @property
    def parameters(self):
        return [
            [["Detector trigger count", self.rayonix_detector, "last_image_number", "int"], {"read_only": True}],
            [["Timing system trigger count", self.rayonix_detector, "xdet_trig_count", "int"], {}],
            [["Trigger count offset", self.rayonix_detector, "xdet_trig_count_offset", "int"], {}],
            [["Trigger count offset (median)", self.rayonix_detector, "xdet_trig_count_offset_mean", "float"], {"format": "%.1f"}],
            [["Trigger count offset error", self.rayonix_detector, "xdet_trig_count_offset_error", "float"], {"format": "%.3f"}],
            [["Acquire timestamp offset", self.rayonix_detector, "acquire_timestamp_offset", "float"], {"format": "%.3f", "unit": "s"}],
            [["Collecting dataset", self.rayonix_detector, "collecting_dataset", "Idle/Active"], {}],
        ]

    label_width = 230
    width = 140

    standard_view = [
        "Detector trigger count",
        "Timing system trigger count",
        "Trigger count offset",
        "Trigger count offset (median)",
        "Trigger count offset error",
        "Acquire timestamp offset",
        "Collecting dataset",
    ]

    @property
    def rayonix_detector(self):
        from rayonix_detector_client import rayonix_detector
        return rayonix_detector(self.domain_name)

    @property
    def application_buttons(self):
        from Panel_3 import Application_Button
        from application import application
        return [
            Application_Button(
                "Beam Center...",
                application(f"{self.domain_name}.XRay_Beam_Center_Panel.XRay_Beam_Center_Panel('{self.domain_name}')")
            ),
        ]

    @property
    def application_menu_items(self):
        from Panel_3 import Application_Menu_Item
        from application import application
        return [
            Application_Menu_Item(
                "Beam Center...",
                application(f"{self.domain_name}.XRay_Beam_Center_Panel.XRay_Beam_Center_Panel('{self.domain_name}')")
            ),
        ]


if __name__ == '__main__':
    from redirect import redirect
    import wx

    redirect("Rayonix_Detector_Diagnostics_Panel", level="INFO")

    domain_name = "BioCARS"

    app = wx.App()
    panel = Rayonix_Detector_Diagnostics_Panel(domain_name)
    app.MainLoop()
