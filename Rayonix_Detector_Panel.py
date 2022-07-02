#!/usr/bin/env python
"""Rayonix detector control panel for continuous operation
Author: Friedrich Schotte
Date created: 2017-05-10
Date last modified: 2022-06-22
Revision comment: Added: last_saved_image_filename
"""
from Panel_3 import BasePanel

__version__ = "5.10"


class Rayonix_Detector_Panel(BasePanel):
    def __init__(self, domain_name):
        self.domain_name = domain_name
        BasePanel.__init__(self)

    @property
    def title(self): return f"Rayonix Detector [{self.domain_name}]"

    icon = "Rayonix Detector"

    @property
    def name(self): return f"{self.domain_name}/Rayonix_Detector_Panel"

    @property
    def parameters(self):
        from reference import reference

        return [
            [["Detector status", self.rayonix_detector, "detector_online", "Offline/Online"], {"read_only": True}],
            [["Server status", self.rayonix_detector, "IOC_online", "Offline/Online"], {"read_only": True}],
            [["Continuous readout", self.rayonix_detector, "acquiring", "Stopped/Running"], {}],
            [["Image acquisition", self.rayonix_detector, "acquiring_images", "Idle/Acquiring"], {}],
            [["Ready", self.rayonix_detector, "ready", "Not Ready/Ready"], {}],
            [["Update background", self.rayonix_detector, "update_background", "Update Now/Cancel"], {}],
            [["X-ray detector image count", self.rayonix_detector, "last_image_number", "int"], {}],
            [["Timing system image count", self.rayonix_detector, "xdet_acq_count", "int"], {}],
            [["Data collection current image", self.rayonix_detector, "current_image_basename", "str"], {"read_only": True}],
            [["Data collection last image", self.rayonix_detector, "last_saved_image_basename", "str"], {"read_only": True}],
            [["Data collection images left", self.rayonix_detector, "nimages", "int"], {"read_only": True}],
            [["Bin factor", self.rayonix_detector, "bin_factor", "int"], {"choices": [1, 2, 3, 4, 5, 6, 8]}],
            [["Readout Mode", self.rayonix_detector, "readout_mode", "str"], {"choices": ['Normal', 'High Gain', 'Low Noise', 'HDR', 'Turbo']}],
            [["Readout Mode Number", self.rayonix_detector, "readout_mode_number", "int"], {"choices": [0, 1, 2, 3, 4]}],
            [["Scratch image", self.rayonix_detector, "last_filename", "str"], {"read_only": True}],
            [["Scratch image basename", self.rayonix_detector, "last_basename", "str"], {"read_only": True}],
            [["Scratch images directory requested", self.rayonix_detector, "scratch_directory_requested", "str"], {"choices_reference": reference(self.rayonix_detector, "scratch_directory_choices")}],
            [["Scratch images directory", self.rayonix_detector, "scratch_directory", "str"], {"choices_reference": reference(self.rayonix_detector, "scratch_directory_choices")}],
            [["Scratch images", self.rayonix_detector, "temp_image_count", "int"], {"choices": [10, 20, 50, 100, 200, 500, 1000]}],
            [["Scratch images limit count", self.rayonix_detector, "nimages_to_keep", "int"], {"choices": [10, 20, 50, 100, 200, 500, 1000]}],
            [["Scratch images limit", self.rayonix_detector, "limiting_files", "Off/On"], {}],
            [["Scratch images limit requested", self.rayonix_detector, "limiting_files_requested", "Off/On"], {}],
            [["Detector IP address", self.rayonix_detector, "ip_address", "str"], {"choices_reference": reference(self.rayonix_detector, "ip_address_choices")}],
        ]

    label_width = 230
    width = 140

    standard_view = [
        "Continuous readout",
        "Image acquisition",
        "X-ray detector image count",
        "Timing system image count",
        "Data collection last image",
        "Data collection images left",
        "Scratch images directory",
        "Bin factor",
        "Readout mode",
        "Detector IP address",
    ]

    scratch_directory_choices = [
        "/net/mx340hs/data/tmp",
        "/net/femto-data/C/Data/tmp",
        "//femto-data/C/Data/tmp",
        "/Mirror/femto-data/C/Data/tmp",
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
                "Metadata...",
                application(f"{self.domain_name}.Rayonix_Detector_Metadata_Panel.Rayonix_Detector_Metadata_Panel('{self.domain_name}')")
            ),
            Application_Button(
                "Beam Center...",
                application(f"{self.domain_name}.XRay_Beam_Center_Panel.XRay_Beam_Center_Panel('{self.domain_name}')")
            ),
            Application_Button(
                "Diagnostics...",
                application(f"{self.domain_name}.Rayonix_Detector_Diagnostics_Panel.Rayonix_Detector_Diagnostics_Panel('{self.domain_name}')")
            ),
        ]

    @property
    def application_menu_items(self):
        from Panel_3 import Application_Menu_Item
        from application import application
        return [
            Application_Menu_Item(
                "Metadata...",
                application(f"{self.domain_name}.Rayonix_Detector_Metadata_Panel.Rayonix_Detector_Metadata_Panel('{self.domain_name}')")
            ),
            Application_Menu_Item(
                "Beam Center...",
                application(f"{self.domain_name}.XRay_Beam_Center_Panel.XRay_Beam_Center_Panel('{self.domain_name}')")
            ),
            Application_Menu_Item(
                "Diagnostics...",
                application(f"{self.domain_name}.Rayonix_Detector_Diagnostics_Panel.Rayonix_Detector_Diagnostics_Panel('{self.domain_name}')")
            ),
        ]


if __name__ == '__main__':
    from redirect import redirect
    import wx

    redirect("Rayonix_Detector_Panel", level="INFO")

    domain_name = "BioCARS"

    app = wx.App()
    panel = Rayonix_Detector_Panel(domain_name)
    app.MainLoop()
