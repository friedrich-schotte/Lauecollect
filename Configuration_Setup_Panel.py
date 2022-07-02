#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2019-07-16
Date last modified: 2022-07-13
Date last modified: 2022-06-24
Revision comment: Adjusted label_width
"""
__version__ = "1.5.1"

import wx

from Panel_3 import BasePanel
from alias_property import alias_property


class Configuration_Setup_Panel(BasePanel):
    name = "configuration"
    icon = "Utility"

    def __init__(self, name):
        self.name = name
        BasePanel.__init__(self)

    title = alias_property("configuration.window_title")

    subname = True
    label_width = 45
    width = 180

    @property
    def parameters(self):
        return [
            [(item.label, item.object, item.attribute_name, item.type_name), {}]
            for item in self.configuration.parameters
        ]

    @property
    def standard_view(self):
        return [item.label for item in self.configuration.parameters if item.show]

    @property
    def configuration(self):
        from configuration_setup_control import configuration_setup_control
        return configuration_setup_control(self.name)


if __name__ == '__main__':
    from redirect import redirect

    # name = "BioCARS.timing_modes"
    # name = "BioCARS.sequence_modes"
    # name = "BioCARS.delay_configuration"
    # name = "BioCARS.temperature_configuration"
    # name = "BioCARS.power_configuration"
    # name = "BioCARS.scan_configuration"
    # name = "BioCARS.diagnostics_configuration"
    # name = "BioCARS.detector_configuration"
    name = "BioCARS.method"

    domain_name, base_name = name.split(".", 1)
    redirect(f"{domain_name}.Configuration_Setup_Panel.{base_name}")

    app = wx.App()
    Configuration_Setup_Panel(name)
    app.MainLoop()
