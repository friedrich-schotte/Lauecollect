#!/usr/bin/env python
"""
Table-like client side interface for configurations
Author: Friedrich Schotte
Date created: 2021-07-07
Date last modified: 2022-06-12
Revision comment: Fast initialization
"""
__version__ = "1.2.4"

import logging
import wx
from Spreadsheet import Spreadsheet


class Configuration_Table(wx.Panel):
    def __init__(self, parent, name):
        import wx.grid
        self.name = name
        super().__init__(parent)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.table = Configuration_Table_Spreadsheet(self, name, fast_text=True)
        self.table.ShowScrollbars(wx.SHOW_SB_NEVER, wx.SHOW_SB_ALWAYS)
        self.Sizer.Add(self.table, flag=wx.EXPAND | wx.TOP, proportion=1)

        self.status = Configuration_Status_Spreadsheet(self, name, autosize=False)
        self.status.ShowScrollbars(wx.SHOW_SB_ALWAYS, wx.SHOW_SB_ALWAYS)
        self.status.ColLabelSize = 1
        self.status.MinSize = -1, 35
        self.Sizer.Add(self.status, flag=wx.EXPAND)

        logging.debug(f"{self} Synchronizing number of columns started")
        self.status.NumberCols = self.table.NumberCols
        logging.debug(f"{self} Synchronizing number of columns done")
        logging.debug(f"{self} Synchronizing column widths started")
        self.synchronize_column_widths(self.table, self.status)
        logging.debug(f"{self} Synchronizing column widths done")
        self.table.Bind(wx.grid.EVT_GRID_COL_SIZE, self.on_table_column_resize)
        self.status.Bind(wx.grid.EVT_GRID_COL_SIZE, self.on_status_column_resize)
        self.table.Bind(wx.EVT_SCROLLWIN, self.on_scroll_table)
        self.status.Bind(wx.EVT_SCROLLWIN, self.on_scroll_status)

        logging.debug(f"{self} Initialized")

    def __repr__(self):
        return f"{type(self).__name__}({self.name!r})"

    def on_table_column_resize(self, event):
        event.Skip()
        self.synchronize_column_widths(self.table, self.status)

    def on_status_column_resize(self, event):
        event.Skip()
        self.synchronize_column_widths(self.status, self.table)

    @staticmethod
    def synchronize_column_widths(source, destination):
        column_widths = source.ColSizes
        destination.SetColSizes(column_widths)

    def on_scroll_table(self, event):
        event.Skip()
        table_x, table_y = self.table.GetViewStart()
        status_x, status_y = self.status.GetViewStart()
        self.status.Scroll(table_x, status_y)

    def on_scroll_status(self, event):
        event.Skip()
        status_x, status_y = self.status.GetViewStart()
        table_x, table_y = self.table.GetViewStart()
        self.table.Scroll(status_x, table_y)


class Configuration_Status_Spreadsheet(Spreadsheet):
    @property
    def table(self):
        from configuration_status_control import configuration_status_control
        return configuration_status_control(self.name)


class Configuration_Table_Spreadsheet(Spreadsheet):
    @property
    def table(self):
        from configuration_table_control import configuration_table_control
        return configuration_table_control(self.name)


if __name__ == '__main__':
    from Control_Panel import Control_Panel

    # name = "BioCARS.beamline_configuration"
    # name = "BioCARS.Julich_chopper_modes"
    # name = "BioCARS.heat_load_chopper_modes"
    # name = "BioCARS.timing_modes"
    # name = "BioCARS.sequence_modes"
    # name = "BioCARS.delay_configuration"
    # name = "BioCARS.temperature_configuration"
    # name = "BioCARS.power_configuration"
    # name = "BioCARS.scan_configuration"
    # name = "BioCARS.detector_configuration"
    # name = "BioCARS.diagnostics_configuration"
    name = "BioCARS.method"
    # name = "BioCARS.laser_optics_modes"
    # name = "BioCARS.alio_diffractometer_saved"

    # name = "LaserLab.timing_modes"
    # name = "LaserLab.sequence_modes"
    # name = "LaserLab.delay_configuration"
    # name = "LaserLab.temperature_configuration"
    # name = "LaserLab.power_configuration"
    # name = "LaserLab.scan_configuration"
    # name = "LaserLab.detector_configuration"
    # name = "LaserLab.diagnostics_configuration"
    # name = "LaserLab.method"

    domain_name, base_name = name.split(".", 1)

    from redirect import redirect

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    redirect(f"{domain_name}.Configuration_Table_Panel.{base_name}", format=msg_format, level="DEBUG")

    app = wx.GetApp() if wx.GetApp() else wx.App()
    self = Control_Panel(name, panel_type=Configuration_Table)
    app.MainLoop()
