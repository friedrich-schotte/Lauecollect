#!/usr/bin/env python
"""Control panel for ILX Lightwave Precision Temperature Controller.
Author: Friedrich Schotte
Date created: 2021-04-01
Date last modified: 2021-04-22
Revision comment: Refactored
"""
__version__ = "1.0.3"

from Panel_3 import BasePanel


class Lightwave_Temperature_Controller_Parameters_Panel(BasePanel):
    from monitored_property import monitored_property

    domain_name = "BioCARS"

    def __init__(self, domain_name=None):
        if domain_name is not None:
            self.domain_name = domain_name
        BasePanel.__init__(self)

    @monitored_property
    def title(self):
        return f"Lightwave Temperature Controller Parameters [{self.domain_name}]"

    @property
    def name(self):
        return f"Lightwave_Temperature_Controller_Parameters_Panel.{self.domain_name}"

    icon = "Lightwave Temperature Controller"

    @property
    def parameters(self):
        return [
            [("EPICS Record", self.device, "prefix", "str"), {"choices": ["NIH:LIGHTWAVE"]}],
            [("Baud Rate", self.device, "BAUD", "int"), {"choices": [9600, 14400, 19200, 38400, 57600, 115200, 230400], "unit": "baud"}],
            [("Serial Port", self.device, "port_name", "str"), {"read_only": True}],
            [("ID String", self.device, "id", "str"), {"read_only": True}],
            [("Nom. Update Period", self.device, "SCAN", "float"), {"choices": [0, 0.2, 0.5, 1.0, 2.0], "unit": "s", "format": "%g"}],
            [("Act. Update Period", self.device, "SCANT", "float"), {"read_only": True, "unit": "s", "format": "%.3f"}],
            [("Proportional Gain (P)", self.device, "PCOF", "float"), {"choices": [0.75]}],
            [("Integral Gain (I)", self.device, "ICOF", "float"), {"choices": [0.3], "format": "%g"}],
            [("Differential Gain (D)", self.device, "DCOF", "float"), {"choices": [0.3], "format": "%g"}],
            [("Stabilization Threshold", self.device, "stabilization_threshold", "float"), {"digits": 3, "unit": "C", "choices": [0.01, 0.008]}],
            [("Stabilization N Samples", self.device, "stabilization_nsamples", "int"), {"choices": [3]}],
            [("Current Low Limit", self.device, "current_low_limit", "float"), {"digits": 3, "unit": "A", "choices": [-3.5, -4, -5]}],
            [("Current High Limit", self.device, "current_high_limit", "float"), {"digits": 3, "unit": "A", "choices": [3.5, 4, 5]}],
        ]

    label_width = 140

    standard_view = [
        "EPICS Record",
        "Baud Rate",
        "Serial Port",
        "ID String",
        "Act. Update Period",
        "Nom. Update Period",
        "Proportional Gain (P)",
        "Integral Gain (I)",
        "Differential Gain (D)",
        "Stabilization Threshold",
        "Stabilization N Samples",
        "Current Low Limit",
        "Current High Limit",
    ]

    @property
    def device(self):
        from lightwave_temperature_controller import lightwave_temperature_controller
        return lightwave_temperature_controller


if __name__ == '__main__':
    from redirect import redirect
    import wx

    domain_name = "BioCARS"

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"

    redirect(f"{domain_name}.{Lightwave_Temperature_Controller_Parameters_Panel.__name__}", format=msg_format)

    app = wx.GetApp() if wx.GetApp() else wx.App()
    self = Lightwave_Temperature_Controller_Parameters_Panel(domain_name)
    app.MainLoop()
