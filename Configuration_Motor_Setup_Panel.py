#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2020-12-30
Date last modified: 2022-06-13
Revision comment: Added: Item: object
"""
__version__ = "1.4.3"

import wx

from Panel_3 import BasePanel
from alias_property import alias_property


class Configuration_Motor_Setup_Panel(BasePanel):
    name = "configuration_motor"
    icon = "Utility"

    def __init__(self, name):
        self.name = name
        BasePanel.__init__(self)

    title = alias_property("configuration.window_title")

    subname = True
    label_width = 120
    width = 200

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
        from configuration_motor_setup_control import configuration_motor_setup_control
        return configuration_motor_setup_control(self.name)


if __name__ == '__main__':
    from redirect import redirect

    name = "BioCARS.method.motor1"

    # name = "LaserLab.timing_modes.motor1"
    # name = "LaserLab.sequence_modes.motor1"
    # name = "LaserLab.delay_configuration.motor1"
    # name = "LaserLab.temperature_configuration.motor1"
    # name = "LaserLab.power_configuration.motor1"
    # name = "LaserLab.scan_configuration.motor1"
    # name = "LaserLab.diagnostics_configuration.motor1"
    # name = "LaserLab.detector_configuration.motor1"
    # name = "LaserLab.method.motor1"

    domain_name, base_name = name.split(".", 1)
    redirect(f"{domain_name}.Configuration_Motor_Setup_Panel.{base_name}")

    app = wx.App()
    Configuration_Motor_Setup_Panel(name)
    app.MainLoop()
