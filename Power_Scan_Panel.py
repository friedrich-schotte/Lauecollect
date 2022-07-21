"""
Author: Friedrich Schotte
Date created: 2022-07-14
Date last modified: 2022-07-14
Revision comment:
"""
__version__ = "1.0"

from Scan_Panel import Scan_Panel


class Power_Scan_Panel(Scan_Panel):
    format = "%.4f"


if __name__ == '__main__':
    from redirect import redirect
    import wx

    domain_name = "BioCARS"

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"

    redirect(f"{domain_name}.Power_Scan_Panel", format=msg_format)

    app = wx.GetApp() if wx.GetApp() else wx.App()
    self = Power_Scan_Panel(domain_name)
    app.MainLoop()
