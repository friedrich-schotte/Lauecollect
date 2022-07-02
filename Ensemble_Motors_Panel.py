#!/usr/bin/env python
"""Ensemble motors panel
Author: Friedrich Schotte
Date created: 2013-10-31
Date last modified: 2021-07-21
Revision comment: Refactored
"""

__version__ = "1.0.6"

import wx
from MotorPanel import MotorWindow


class Ensemble_Motors_Panel(MotorWindow):
    def __init__(self):
        from Ensemble import SampleX, SampleY, SampleZ
        super().__init__([SampleX, SampleY, SampleZ], title="Ensemble Motors [BioCARS]")


if __name__ == '__main__':
    from redirect import redirect

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    redirect(f"BioCARS.Fast_Diffractometer_Panel", format=msg_format)

    app = wx.GetApp() if wx.GetApp() else wx.App()
    self = Ensemble_Motors_Panel()
    app.MainLoop()
