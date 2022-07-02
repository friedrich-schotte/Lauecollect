#!/usr/bin/env python
"""Control panel for ILX Lightwave Precision Temperature Controller.
Author: Friedrich Schotte
Date created: 2009-10-14
Date last modified: 2021-10-09
Revision comment: Changed Status label: Stable/Not Stable
"""
__version__ = "5.0.2"

from Panel_3 import BasePanel


class Lightwave_Temperature_Controller_Panel(BasePanel):
    from monitored_property import monitored_property
    domain_name = "BioCARS"

    def __init__(self, domain_name=None):
        if domain_name is not None:
            self.domain_name = domain_name
        BasePanel.__init__(self)

    @monitored_property
    def title(self):
        return f"Lightwave Temperature Controller [{self.domain_name}]"

    icon = "Lightwave Temperature Controller"

    @property
    def name(self):
        return "Lightwave_Temperature_Controller_Panel.%s" % self.domain_name

    @property
    def parameters(self):
        return [
            [("Set Point", self.device, "command_value", "float"), {"unit": "C", "format": "%.3f"}],
            [("Actual Temperature", self.device, "value", "float"), {"unit": "C", "format": "%.3f", "read_only": True}],
            [("Status", self.device, "moving", "Stable/Not Stable"), {"read_only": True}],
            [("Current", self.device, "I", "float"), {"unit": "A", "format": "%.3f", "read_only": True}],
            [("Power", self.device, "P", "float"), {"unit": "W", "format": "%.3f", "read_only": True}],
            [("Enabled", self.device, "enabled", "Off/On"), {}],
        ]

    label_width = 190

    standard_view = [
        "Set Point",
        "Actual Temperature",
        "Current",
        "Power",
        "Enabled",
    ]

    @property
    def application_buttons(self):
        from Panel_3 import Application_Button
        from application import application
        return [
            Application_Button(
                "Parameters...",
                application(
                    f"{self.domain_name}.Lightwave_Temperature_Controller_Parameters_Panel.Lightwave_Temperature_Controller_Parameters_Panel('{self.domain_name}')")
            ),
        ]

    @property
    def application_menu_items(self):
        from Panel_3 import Application_Menu_Item
        from application import application
        return [
            Application_Menu_Item(
                "Parameters...",
                application(
                    f"{self.domain_name}.Lightwave_Temperature_Controller_Parameters_Panel.Lightwave_Temperature_Controller_Parameters_Panel('{self.domain_name}')")
            ),
        ]

    @property
    def device(self):
        from lightwave_temperature_controller import lightwave_temperature_controller
        return lightwave_temperature_controller


if __name__ == '__main__':
    from redirect import redirect
    import wx

    domain_name = "BioCARS"

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"

    redirect(f"{domain_name}.{Lightwave_Temperature_Controller_Panel.__name__}", format=msg_format)

    app = wx.GetApp() if wx.GetApp() else wx.App()
    self = Lightwave_Temperature_Controller_Panel(domain_name)
    app.MainLoop()
