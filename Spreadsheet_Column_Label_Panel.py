#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2022-07-07
Date last modified: 2022-07-07
Revision comment:
"""
__version__ = "1.0"

import wx

from Panel_3 import BasePanel
from alias_property import alias_property


class Spreadsheet_Column_Label_Panel(BasePanel):
    name = "spreadsheet_column_label"
    icon = "Utility"

    def __init__(self, table, column):
        self.table = table
        self.column = column
        BasePanel.__init__(self)

    @property
    def title(self):
        return f"{self.table.name}, column {self.column+1}"

    subname = True
    label_width = 50
    width = 150

    @property
    def parameters(self):
        return [[("Label", self.table.cell(0, self.column+1), "text", "str"), {}]]

    @property
    def standard_view(self):
        return ["Label"]


if __name__ == '__main__':
    from redirect import redirect
    from spreadsheet_control import spreadsheet_control

    domain_name = "BioCARS"
    # domain_name = "LaserLab"
    # base_name = "beamline_configuration"
    # base_name = "Julich_chopper_modes"
    # base_name = "heat_load_chopper_modes"
    # base_name = "timing_modes"
    # base_name = "sequence_modes"
    # base_name = "delay_configuration"
    # base_name = "temperature_configuration"
    # base_name = "power_configuration"
    base_name = "scan_configuration"
    # base_name = "detector_configuration"
    # base_name = "diagnostics_configuration"
    # base_name = "method"
    # base_name = "laser_optics_modes"
    # base_name = "alio_diffractometer_saved"
    column = 0

    redirect(f"{domain_name}.Configuration_Motor_Setup_Panel.{base_name}")

    name = f"{domain_name}.{base_name}"
    table = spreadsheet_control(name)

    app = wx.App()
    Spreadsheet_Column_Label_Panel(table, column)
    app.MainLoop()
