#!/usr/bin/env python
"""
Control panel for thermoelectric circulating water chiller.
Author: Friedrich Schotte, Valentyn Stadnytskiy
Date created: 2009-06-01
Date last modified: 2021-12-03
Revision comment: Issue: Conflicting file names:
    settings/oasis_chiller_settings.txt
    settings/Oasis_Chiller_settings.txt
    (SMB file server cannot serve both files to a Windows client)
"""
__version__ = "2.4.3"

from Panel_3 import BasePanel


class Oasis_Chiller_Panel(BasePanel):
    domain_name = "BioCARS"

    def __init__(self, domain_name=None):
        if domain_name is not None:
            self.domain_name = domain_name
        BasePanel.__init__(self)

    icon = "Oasis Chiller"

    @property
    def title(self):
        return f"Oasis Chiller DL [{self.domain_name}]"

    @property
    def name(self):
        return "Oasis_Chiller_Panel.%s" % self.domain_name

    @property
    def parameters(self):
        return [
            [("Set Point", self.chiller, "VAL", "float"), {"unit": "C"}],
            [("Actual Temperature", self.chiller, "RBV", "float"), {"unit": "C", "read_only": True}],
            [("Faults", self.chiller, "faults", "str"), {}],
        ]

    standard_view = [
        "Set Point",
        "Actual Temperature",
        "Faults",
    ]

    @property
    def application_buttons(self):
        from Panel_3 import Application_Button
        from application import application
        return [
            Application_Button(
                "Parameters...",
                application(f"{self.domain_name}.Oasis_Chiller_Parameters_Panel.Oasis_Chiller_Parameters_Panel('{self.domain_name}')")
            ),
        ]

    @property
    def application_menu_items(self):
        from Panel_3 import Application_Menu_Item
        from application import application
        return [
            Application_Menu_Item(
                "Parameters...",
                application(f"{self.domain_name}.Oasis_Chiller_Parameters_Panel.Oasis_Chiller_Parameters_Panel('{self.domain_name}')")
            ),
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

    redirect(f"{domain_name}.{Oasis_Chiller_Panel.__name__}", format=msg_format)

    app = wx.GetApp() if wx.GetApp() else wx.App()
    panel = Oasis_Chiller_Panel(domain_name)
    app.MainLoop()
