#!/usr/bin/env python
"""
Table-like client side interface for configurations
Author: Friedrich Schotte
Date created: 2021-07-07
Date last modified: 2022-06-28
Revision comment: Renamed: Configuration_Tables_Panel
"""
__version__ = "1.0.7"

import wx

from Configuration_Table import Configuration_Table
from Control_Panel import Control_Panel


class Configuration_Table_Panel(Control_Panel):
    def __init__(self, name):
        self.name = name
        super().__init__(name=name)

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

    @property
    def ControlPanel(self):
        panel = wx.Panel(self)

        layout = wx.BoxSizer(wx.VERTICAL)
        panel.Sizer = layout

        control = Configuration_Table(panel, self.name)
        layout.Add(control, flag=wx.ALIGN_LEFT | wx.ALL, proportion=1)

        panel.Fit()
        return panel


if __name__ == '__main__':
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

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, %(message)s"
    redirect(f"{domain_name}.Configuration_Table_Panel.{base_name}", format=msg_format, level="DEBUG")

    app = wx.GetApp() if wx.GetApp() else wx.App()
    self = Configuration_Table_Panel(name)
    app.MainLoop()
