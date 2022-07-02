#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2022-05-01
Date last modified: 2022-06-30
Revision comment: Added: enabled
"""
__version__ = "1.2"

from Panel_3 import BasePanel
from monitored_property import monitored_property


class Scan_Panel(BasePanel):
    domain_name = "BioCARS"

    def __init__(self, domain_name=None, parent=None):
        if domain_name is not None:
            self.domain_name = domain_name
        BasePanel.__init__(self, parent=parent)

    @property
    def scan(self):
        return self.object_type(self.domain_name)

    @monitored_property
    def title(self):
        title = self.class_name.replace("_", " ").replace(" Panel", "")
        return f"{title} [{self.domain_name}]"

    icon = "Tool"
    label_width = 190
    dtype = "float"
    format = "%g"
    unit = ""

    @property
    def name(self):
        return f"{self.class_name}.{self.domain_name}"

    @property
    def object_type(self):
        return getattr(self.module, self.object_name)

    @property
    def module(self):
        return __import__(self.module_name)

    @property
    def module_name(self):
        return self.object_name

    @property
    def object_name(self):
        return self.base_name.lower()+"_client"

    @property
    def base_name(self):
        return self.class_name.replace("_Panel", "")

    @property
    def class_name(self):
        return type(self).__name__

    @property
    def parameters(self):
        return [
            [("Motor Name", self.scan, "motor_name", "str"), {}],
            [("Enabled", self.scan, "enabled", "Disabled/Enabled"), {}],
            [("Values String", self.scan, "values_string", "str"), {}],
            [("Wait", self.scan, "wait", "False/True"), {}],
            [("Return Value", self.scan, "return_value", self.dtype), {"unit": self.unit, "format": self.format}],
            [("Scan Point Divider", self.scan, "scan_point_divider", "int"), {}],
            [("Ready", self.scan, "ready", "Not Ready/Ready"), {"read_only": True}],
        ]

    standard_view = [
        "Motor Name",
        "Enabled",
        "Values String",
        "Wait",
        "Return Value",
        "Scan Point Divider",
        "Ready",
    ]

    @property
    def application_buttons(self):
        from Panel_3 import Application_Button
        from application import application
        return [
            Application_Button(
                "Diagnostics...",
                application(f"{self.domain_name}.{self.base_name}_Diagnostics_Panel.{self.base_name}_Diagnostics_Panel('{self.domain_name}')")
            ),
        ]

    @property
    def application_menu_items(self):
        from Panel_3 import Application_Menu_Item
        from application import application
        return [
            Application_Menu_Item(
                "Diagnostics...",
                application(f"{self.domain_name}.{self.base_name}_Diagnostics_Panel.{self.base_name}_Diagnostics_Panel('{self.domain_name}')")
            ),
        ]


if __name__ == '__main__':
    from redirect import redirect
    import wx

    domain_name = "BioCARS"

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"

    redirect(f"{domain_name}.{Scan_Panel.__name__}", format=msg_format)

    app = wx.GetApp() if wx.GetApp() else wx.App()
    self = Scan_Panel(domain_name)
    app.MainLoop()
