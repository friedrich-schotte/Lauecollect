#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2009-11-26
Date last modified: 2022-07-11
Revision comment: temperature_system requires domain_name
"""
__version__ = "1.0.1"

from Panel_3 import BasePanel


class Temperature_System_Panel(BasePanel):
    from monitored_property import monitored_property
    domain_name = "BioCARS"

    def __init__(self, domain_name=None, parent=None):
        if domain_name is not None:
            self.domain_name = domain_name
        BasePanel.__init__(self, parent=parent)

    icon = "temperature"

    @monitored_property
    def title(self):
        return f"Temperature System [{self.domain_name}]"

    @property
    def name(self):
        return f"Temperature_System_Panel.{self.domain_name}"

    label_width = 150

    @property
    def parameters(self):
        return [
            [("Set Point", self.instrument, "VAL", "float"), {"unit": "C", "format": "%.3f"}],
            [("Actual Temperature", self.instrument, "RBV", "float"), {"unit": "C", "format": "%.3f", "read_only": True}],
            [("Status", self.instrument, "DMOV", "Not Stable/Stable"), {"read_only": True}],
        ]

    standard_view = [
        "Set Point",
        "Actual Temperature",
        "Status",
    ]

    @property
    def application_buttons(self):
        from Panel_3 import Application_Button
        from application import application
        return [
            Application_Button(
                "TEC..",
                application(f"{self.domain_name}.Lightwave_Temperature_Controller_Panel.Lightwave_Temperature_Controller_Panel('{self.domain_name}')")
            ),
            Application_Button(
                "Chiller..",
                application(f"{self.domain_name}.Oasis_Chiller_Panel.Oasis_Chiller_Panel('{self.domain_name}')")
            ),
            Application_Button(
                "Par..",
                application(f"{self.domain_name}.Temperature_System_Parameters_Panel.Temperature_System_Parameters_Panel('{self.domain_name}')")
            ),
            Application_Button(
                "Diag..",
                application(f"{self.domain_name}.Temperature_System_Diagnostics_Panel.Temperature_System_Diagnostics_Panel('{self.domain_name}')")
            ),
            Application_Button(
                "Scan..",
                application(f"{self.domain_name}.Temperature_Scan_Panel.Temperature_Scan_Panel('{self.domain_name}')")
            ),
        ]

    @property
    def application_menu_items(self):
        from Panel_3 import Application_Menu_Item
        from application import application
        return [
            Application_Menu_Item(
                "TEC...",
                application(f"{self.domain_name}.Lightwave_Temperature_Controller_Panel.Lightwave_Temperature_Controller_Panel('{self.domain_name}')")
            ),
            Application_Menu_Item(
                "Chiller...",
                application(f"{self.domain_name}.Oasis_Chiller_Panel.Oasis_Chiller_Panel('{self.domain_name}')")
            ),
            Application_Menu_Item(
                "Parameters...",
                application(f"{self.domain_name}.Temperature_System_Parameters_Panel.Temperature_System_Parameters_Panel('{self.domain_name}')")
            ),
            Application_Menu_Item(
                "Diagnostics...",
                application(f"{self.domain_name}.Temperature_System_Diagnostics_Panel.Temperature_System_Diagnostics_Panel('{self.domain_name}')")
            ),
            Application_Menu_Item(
                "Scan...",
                application(f"{self.domain_name}.Temperature_Scan_Panel.Temperature_Scan_Panel('{self.domain_name}')")
            ),
        ]

    @property
    def instrument(self):
        from temperature_system import temperature_system
        return temperature_system(self.domain_name)


if __name__ == '__main__':
    from redirect import redirect
    import wx

    domain_name = "BioCARS"

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"

    redirect(f"{domain_name}.{Temperature_System_Panel.__name__}", format=msg_format)

    app = wx.GetApp() if wx.GetApp() else wx.App()
    self = Temperature_System_Panel(domain_name)
    app.MainLoop()
