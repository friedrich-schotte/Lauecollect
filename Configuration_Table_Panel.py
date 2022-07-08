#!/usr/bin/env python
"""
Table-like client side interface for configurations
Author: Friedrich Schotte
Date created: 2021-07-07
Date last modified: 2022-07-07
Revision comment: Updated example
"""
__version__ = "1.0.9"

import wx

from Configuration_Table import Configuration_Table
from Control_Panel import Control_Panel


class Configuration_Table_Panel(Control_Panel):
    def __init__(self, name):
        self.name = name
        super().__init__(name=name)

    @property
    def ControlPanel(self):
        panel = wx.Panel(self)

        layout = wx.BoxSizer(wx.VERTICAL)
        panel.Sizer = layout

        panel.table = Configuration_Table(panel, self.name)
        layout.Add(panel.table, flag=wx.ALIGN_LEFT | wx.ALL, proportion=1)

        panel.Fit()
        return panel

    @property
    def menuBar(self):
        menuBar = super().menuBar

        # More
        menu = wx.Menu()
        menuBar.Append(menu, "&More")
        ID = 201
        menu.Append(ID, "Configure this Panel...")
        self.Bind(wx.EVT_MENU, self.OnConfiguration, id=ID)
        ID += 1
        menu.Append(ID, "Modes/Configurations Panel...")
        self.Bind(wx.EVT_MENU, self.OnConfigurations, id=ID)

        return menuBar

    def OnConfiguration(self, _event):
        self.configuration_setup_panel.start()

    def OnConfigurations(self, _event):
        self.configurations_panel.start()

    @property
    def configuration_setup_panel(self):
        from application import application
        return application(
            domain_name=self.domain_name,
            module_name="Configuration_Setup_Panel",
            command=f"Configuration_Setup_Panel('{self.name}')",
        )

    @property
    def configurations_panel(self):
        from application import application
        return application(
            domain_name=self.domain_name,
            module_name="Configuration_Tables_Panel",
            command=f"Configuration_Tables_Panel('{self.domain_name}')",
        )

    @property
    def configuration(self):
        from configuration_client import configuration_client
        return configuration_client(self.name)

    @property
    def title(self):
        title = f"{self.configuration.title} [{self.domain_name}]"
        if not self.configuration.online:
            title += " (Offline)"
        return title

    @property
    def domain_name(self):
        return self.configuration.domain_name


if __name__ == '__main__':
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

    from redirect import redirect

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, %(message)s"
    redirect(f"{domain_name}.Configuration_Table_Panel.{base_name}", format=msg_format, level="DEBUG")

    from DebugApp import DebugApp
    wx.App = DebugApp
    app = wx.GetApp() if wx.GetApp() else wx.App()
    self = Configuration_Table_Panel(f"{domain_name}.{base_name}")
    app.MainLoop()
    # >>> from reference import reference
    # >>> reference(self.panel.table.table.table.cell(6,1), "background_color").event_history.all_events
