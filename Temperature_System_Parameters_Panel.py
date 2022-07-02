#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2021-11-26
Date last modified: 2021-12-02
Revision comment: Added parameter TEC_slew_dT
"""
__version__ = "1.5"

from Panel_3 import BasePanel
from monitored_property import monitored_property


class Temperature_System_Parameters_Panel(BasePanel):
    icon = "temperature"
    domain_name = "BioCARS"
    label_width = 110

    def __init__(self, domain_name=None, parent=None):
        if domain_name is not None:
            self.domain_name = domain_name

        self.parameters = [
            [("Chiller T min", self.instrument, "chiller_T_min", "float"), {"unit": "C"}],
            [("Chiller T max", self.instrument, "chiller_T_max", "float"), {"unit": "C"}],
            [("Chiller head-start time", self.instrument, "chiller_headstart_time", "float"), {"unit": "s"}],
            [("TEC default P", self.instrument, "TEC_default_P", "float"), {}],
            [("TEC default I", self.instrument, "TEC_default_I", "float"), {}],
            [("TEC default D", self.instrument, "TEC_default_D", "float"), {}],
            [("TEC slew P", self.instrument, "TEC_slew_P", "float"), {}],
            [("TEC slew I", self.instrument, "TEC_slew_I", "float"), {}],
            [("TEC slew D", self.instrument, "TEC_slew_D", "float"), {}],
            [("TEC slew dT", self.instrument, "TEC_slew_dT", "float"), {"unit": "C"}],
        ]

        BasePanel.__init__(self, parent=parent)

    standard_view = [
        "Chiller T min",
        "Chiller T max",
        "Chiller head-start time",
        "TEC default P",
        "TEC default I",
        "TEC default D",
        "TEC slew P",
        "TEC slew I",
        "TEC slew D",
        "TEC slew dT",
    ]

    @property
    def name(self):
        return "Temperature_System_Parameters_Panel.%s" % self.domain_name

    @monitored_property
    def title(self):
        return self.title_template % self.domain_name

    title_template = "Temperature System Parameters [%s]"

    @property
    def instrument(self):
        from temperature_system import temperature_system
        return temperature_system


if __name__ == '__main__':
    from redirect import redirect
    import wx

    domain_name = "BioCARS"

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"

    redirect(f"{domain_name}.{Temperature_System_Parameters_Panel.__name__}", format=msg_format)

    app = wx.GetApp() if wx.GetApp() else wx.App()
    self = Temperature_System_Parameters_Panel(domain_name)
    app.MainLoop()
