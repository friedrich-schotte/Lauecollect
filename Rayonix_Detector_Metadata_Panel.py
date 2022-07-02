#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2022-06-14
Date last modified: 2022-06-14
Revision comment:
"""
__version__ = "1.0"

from Panel_3 import BasePanel


class Rayonix_Detector_Metadata_Panel(BasePanel):
    from monitored_property import monitored_property
    domain_name = "BioCARS"

    def __init__(self, domain_name=None, parent=None):
        if domain_name is not None:
            self.domain_name = domain_name
        BasePanel.__init__(self, parent=parent)

    icon = "Rayonix Detector"

    @monitored_property
    def title(self):
        return f"Rayonix Detector Metadata [{self.domain_name}]"

    @property
    def name(self):
        return f"Rayonix_Detector_Metadata_Panel.{self.domain_name}"

    label_width = 90

    @property
    def parameters(self):
        return [
            [("Distance", self.instrument, "xtal_to_detector", "float"), {"unit": "mm", "format": "%.3f", "read_only": False}],
            [("Phi", self.instrument, "phi", "float"), {"unit": "deg", "format": "%.3f", "read_only": False}],
            [("Beam X", self.instrument, "beam_x", "float"), {"unit": "pixels", "format": "%g"}],
            [("Beam Y", self.instrument, "beam_y", "float"), {"unit": "pixels", "format": "%g"}],
            [("Wavelength", self.instrument, "source_wavelength", "float"), {"unit": "A", "format": "%.3f"}],
        ]

    standard_view = [
        "Distance",
        "Phi",
        "Beam X",
        "Beam Y",
        "Wavelength",
    ]

    @property
    def instrument(self):
        from rayonix_detector_metadata import rayonix_detector_metadata
        return rayonix_detector_metadata(self.domain_name)


if __name__ == '__main__':
    from redirect import redirect
    import wx

    domain_name = "BioCARS"

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"

    redirect(f"{domain_name}.{Rayonix_Detector_Metadata_Panel.__name__}", format=msg_format)

    app = wx.GetApp() if wx.GetApp() else wx.App()
    self = Rayonix_Detector_Metadata_Panel(domain_name)
    app.MainLoop()
