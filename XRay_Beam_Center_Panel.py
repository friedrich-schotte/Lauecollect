#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2022-02-01
Date last modified: 2022-02-01
Revision comment:
"""
__version__ = "1.0"

from Panel_3 import BasePanel


class XRay_Beam_Center_Panel(BasePanel):
    from monitored_property import monitored_property
    domain_name = "BioCARS"

    def __init__(self, domain_name=None, parent=None):
        if domain_name is not None:
            self.domain_name = domain_name
        BasePanel.__init__(self, parent=parent)

    icon = "Rayonix Detector"

    @monitored_property
    def title(self):
        return f"X-Ray Beam Center [{self.domain_name}]"

    @property
    def name(self):
        return f"XRay_Beam_Center_Panel.{self.domain_name}"

    label_width = 50

    @property
    def parameters(self):
        return [
            [("X", self.instrument, "X", "float"), {"unit": "pixels", "format": "%.1f", "read_only": True}],
            [("Y", self.instrument, "Y", "float"), {"unit": "pixels", "format": "%.1f", "read_only": True}],
            [("I", self.instrument, "I", "float"), {"unit": "counts", "format": "%.1f", "read_only": True}],
        ]

    standard_view = [
        "X",
        "Y",
        "I",
    ]

    @property
    def application_buttons(self):
        from Panel_3 import Application_Button
        from application import application
        return [
            Application_Button(
                "Parameters...",
                application(f"{self.domain_name}.XRay_Beam_Center_Parameters_Panel.XRay_Beam_Center_Parameters_Panel('{self.domain_name}')")
            ),
        ]

    @property
    def application_menu_items(self):
        from Panel_3 import Application_Menu_Item
        from application import application
        return [
            Application_Menu_Item(
                "Parameters...",
                application(f"{self.domain_name}.XRay_Beam_Center_Parameters_Panel.XRay_Beam_Center_Parameters_Panel('{self.domain_name}')")
            ),
        ]

    @property
    def instrument(self):
        from xray_beam_center import xray_beam_center
        return xray_beam_center(self.domain_name)


if __name__ == '__main__':
    from redirect import redirect
    import wx

    domain_name = "BioCARS"

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"

    redirect(f"{domain_name}.{XRay_Beam_Center_Panel.__name__}", format=msg_format)

    app = wx.GetApp() if wx.GetApp() else wx.App()
    self = XRay_Beam_Center_Panel(domain_name)
    app.MainLoop()
