#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2021-11-26
Date last modified: 2022-07-11
Revision comment: temperature_system requires domain_name
"""
__version__ = "1.4.1"

from Panel_3 import BasePanel
from monitored_property import monitored_property


class Temperature_System_Diagnostics_Panel(BasePanel):
    icon = "temperature"
    domain_name = "BioCARS"
    label_width = 160

    def __init__(self, domain_name=None, parent=None):
        if domain_name is not None:
            self.domain_name = domain_name

        self.parameters = [
            [("TEC Mode", self.instrument, "slewing", "Holding/Slewing"), {}],
            [("TEC Slew PID", self.instrument, "slew", "--/Slew"), {}],
            [("TEC Hold PID", self.instrument, "hold", "--/Hold"), {}],
            [("TEC PID Status", self.instrument, "TEC_PID_OK", "Bad/OK"), {}],
            [("TEC P", self.instrument, "TEC_P", "float"), {}],
            [("TEC I", self.instrument, "TEC_I", "float"), {}],
            [("TEC D", self.instrument, "TEC_D", "float"), {}],
            [("TEC Set Point", self.instrument, "TEC_set_T", "float"), {"unit": "C", "format": "%.3f"}],
            [("Chiller Set Point Status", self.instrument, "chiller_set_T_OK", "Bad/OK"), {}],
            [("Chiller Nom. Set Point", self.instrument, "chiller_nominal_set_T", "float"), {"unit": "C", "format": "%.3f"}],
            [("Chiller Act. Set Point", self.instrument, "chiller_set_T", "float"), {"unit": "C", "format": "%.3f"}],
            [("Chiller Act. Temp.", self.instrument, "chiller_T", "float"), {"unit": "C", "format": "%.3f", "read_only": True}],
        ]

        BasePanel.__init__(self, parent=parent)

    standard_view = [
        "TEC Mode",
        "TEC Slew PID",
        "TEC Hold PID",
        "TEC PID Status",
        "TEC P",
        "TEC I",
        "TEC D",
        "TEC Set Point",
        "Chiller Set Point Status",
        "Chiller Nom. Set Point",
        "Chiller Act. Set Point",
        "Chiller Act. Temp.",
    ]

    @property
    def name(self):
        return "Temperature_System_Diagnostics_Panel.%s" % self.domain_name

    @monitored_property
    def title(self):
        return self.title_template % self.domain_name

    title_template = "Temperature System Diagnostics [%s]"

    @property
    def instrument(self):
        from temperature_system import temperature_system
        return temperature_system(self.domain_name)


if __name__ == '__main__':
    from redirect import redirect
    import wx

    domain_name = "BioCARS"

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"

    redirect(f"{domain_name}.{Temperature_System_Diagnostics_Panel.__name__}", format=msg_format)

    app = wx.GetApp() if wx.GetApp() else wx.App()
    self = Temperature_System_Diagnostics_Panel(domain_name)
    app.MainLoop()
