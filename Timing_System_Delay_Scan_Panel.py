"""
Author: Friedrich Schotte
Date created: 2022-05-01
Date last modified: 2022-05-02
Revision comment:
"""
__version__ = "1.0"

from Scan_Panel import Scan_Panel


class Timing_System_Delay_Scan_Panel(Scan_Panel):
    dtype = "time"


if __name__ == '__main__':
    from redirect import redirect
    import wx

    domain_name = "BioCARS"

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"

    redirect(f"{domain_name}.{Timing_System_Delay_Scan_Panel.__name__}", format=msg_format)

    app = wx.GetApp() if wx.GetApp() else wx.App()
    self = Timing_System_Delay_Scan_Panel(domain_name)
    app.MainLoop()
