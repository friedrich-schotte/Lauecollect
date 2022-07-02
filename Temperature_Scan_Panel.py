"""
Author: Friedrich Schotte
Date created: 2021-11-30
Date last modified: 2022-05-02
Revision comment: Refactored
"""
__version__ = "1.0.2"

from Scan_Panel import Scan_Panel


class Temperature_Scan_Panel(Scan_Panel):
    format = "%.3f"
    unit = "C"


if __name__ == '__main__':
    from redirect import redirect
    import wx

    domain_name = "BioCARS"

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"

    redirect(f"{domain_name}.Temperature_Scan_Panel", format=msg_format)

    app = wx.GetApp() if wx.GetApp() else wx.App()
    self = Temperature_Scan_Panel(domain_name)
    app.MainLoop()
