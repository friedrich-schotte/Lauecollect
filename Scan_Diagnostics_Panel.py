#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2022-05-01
Date last modified: 2022-07-14
Revision comment: Using formatted_value and formatted_command_value
"""
__version__ = "1.0"

from Panel_3 import BasePanel
from monitored_property import monitored_property


class Scan_Diagnostics_Panel(BasePanel):
    domain_name = "BioCARS"

    def __init__(self, domain_name=None, parent=None):
        if domain_name is not None:
            self.domain_name = domain_name
        BasePanel.__init__(self, parent=parent)

    @property
    def scan(self):
        return self.object_type(self.domain_name)

    icon = "Tool"

    @monitored_property
    def title(self):
        title = self.class_name.replace("_", " ").replace(" Panel", "")
        return f"{title} [{self.domain_name}]"

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
    def class_name(self):
        return type(self).__name__

    @property
    def base_name(self):
        return self.class_name.replace("_Panel", "").replace("_Diagnostics", "")

    label_width = 150

    @property
    def parameters(self):
        return [
            [("Scan Point Number", self.scan, "scan_point_number", "int"), {}],
            [("Values Count", self.scan, "value_count", "int"), {"read_only": True}],
            [("Values Index", self.scan, "values_index", "int"), {"read_only": True}],
            [("Command Value", self.scan, "formatted_command_value", "str"), {}],
            [("Value", self.scan, "formatted_value", "str"), {}],
            [("Status", self.scan, "motor_moving", "Stopped/Moving"), {}],
            [("Enabled", self.scan, "enabled", "False/True"), {}],
            [("Collecting Dataset", self.scan, "collecting_dataset", "False/True"), {}],
            [("Acquiring", self.scan, "acquiring", "False/True"), {}],
            [("Scanning", self.scan, "scanning", "False/True"), {}],
            [("Slewing", self.scan, "slewing", "False/True"), {"read_only": True}],
            [("Scan point Acquisition Time", self.scan, "scan_point_acquisition_time", "float"),
             {"unit": "s", "format": "%.3f", "read_only": True}],
            [("Start Time", self.scan, "start_time", "date"), {"read_only": True}],
        ]

    standard_view = [
        "Scan Point Number",
        "Values Count",
        "Values Index",
        "Command Value",
        "Value",
        "Status",
        "Enabled",
        "Collecting Dataset",
        "Acquiring",
        "Scanning",
        "Slewing",
        "Scan Point Acquisition Time",
        "Start Time",
    ]

    @property
    def application_buttons(self):
        from Panel_3 import Application_Button
        from application import application
        return [
            Application_Button(
                "Main...",
                application(f"{self.domain_name}.{self.base_name}_Panel.{self.base_name}_Panel('{self.domain_name}')")
            ),
        ]

    @property
    def application_menu_items(self):
        from Panel_3 import Application_Menu_Item
        from application import application
        return [
            Application_Menu_Item(
                "Main...",
                application(f"{self.domain_name}.{self.base_name}_Panel.{self.base_name}_Panel('{self.domain_name}')")
            ),
        ]


if __name__ == '__main__':
    from redirect import redirect
    import wx

    domain_name = "BioCARS"

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"

    redirect(f"{domain_name}.{Scan_Diagnostics_Panel.__name__}", format=msg_format)

    app = wx.GetApp() if wx.GetApp() else wx.App()
    self = Scan_Diagnostics_Panel(domain_name)
    app.MainLoop()
