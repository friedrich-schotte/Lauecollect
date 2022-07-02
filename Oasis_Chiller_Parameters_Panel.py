#!/usr/bin/env python
"""
Control panel for thermoelectric circulating water chiller.
Author: Friedrich Schotte, Valentyn Stadnytskiy
Date created: 2009-06-01
Date last modified: 2021-12-03
Revision comment: Added: timeout
"""
__version__ = "2.5"

from Panel_3 import BasePanel


class Oasis_Chiller_Parameters_Panel(BasePanel):
    domain_name = "BioCARS"

    def __init__(self, domain_name=None):
        if domain_name is not None:
            self.domain_name = domain_name
        BasePanel.__init__(self)

    icon = "Oasis Chiller"

    @property
    def title(self):
        return f"Oasis Chiller DL Parameters [{self.domain_name}]"

    @property
    def name(self):
        return "Oasis_Chiller_Parameters_Panel.%s" % self.domain_name

    standard_view = [
        "RS-323 Port",
        "RS-323 Timeout",
        "High Limit",
        "Low Limit",
        "Nom. Update Rate",
        "Act. Update Rate",
    ]

    @property
    def parameters(self):
        return [
            [("RS-323 Port", self.chiller, "COMM", "str"), {}],
            [("RS-323 Timeout", self.chiller, "timeout", "float"), {"format": "%.3f", "unit": "s"}],
            [("Low Limit", self.chiller, "LLM", "float"), {"unit": "C"}],
            [("High Limit", self.chiller, "HLM", "float"), {"unit": "C"}],
            [("Feedback P1", self.chiller, "P1", "float"), {"format": "%g", "choices": [90]}],
            [("Feedback I1", self.chiller, "I1", "float"), {"format": "%g", "choices": [32]}],
            [("Feedback D1", self.chiller, "D1", "float"), {"format": "%g", "choices": [2]}],
            [("Feedback P2", self.chiller, "P2", "float"), {"format": "%g", "choices": [50]}],
            [("Feedback I2", self.chiller, "I2", "float"), {"format": "%g", "choices": [35]}],
            [("Feedback D2", self.chiller, "D2", "float"), {"format": "%g", "choices": [3]}],
            [("Nom. Update Rate", self.chiller, "SCAN", "float"), {"format": "%.3f", "unit": "s", "choices": [0.5, 1.0, 2.0, 4.0]}],
            [("Act. Update Rate", self.chiller, "SCANT", "float"), {"format": "%.3f", "unit": "s"}],
        ]

    @property
    def chiller(self):
        from oasis_chiller import chiller
        return chiller


if __name__ == '__main__':
    # from pdb import pm
    import wx

    domain_name = "BioCARS"

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    from redirect import redirect

    redirect(f"{domain_name}.{Oasis_Chiller_Parameters_Panel.__name__}", format=msg_format)

    app = wx.GetApp() if wx.GetApp() else wx.App()
    panel = Oasis_Chiller_Parameters_Panel(domain_name)
    app.MainLoop()
