"""
Author: Friedrich Schotte
Date created: 2021-11-30
Date last modified: 2022-07-14
Revision comment: Simplified
"""
__version__ = "1.2.3"

from Scan_Diagnostics_Panel import Scan_Diagnostics_Panel


class Temperature_Scan_Diagnostics_Panel(Scan_Diagnostics_Panel):
    pass


if __name__ == '__main__':
    from redirect import redirect
    import wx

    domain_name = "BioCARS"

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"

    redirect(f"{domain_name}.Temperature_Scan_Diagnostics_Panel", format=msg_format)

    app = wx.GetApp() if wx.GetApp() else wx.App()
    self = Temperature_Scan_Diagnostics_Panel(domain_name)
    app.MainLoop()
