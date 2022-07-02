#!/usr/bin/env python
"""
Control panel for variable laser attenuator
Author: Friedrich Schotte
Date created: 2009-06-08
Date last modified: 2022-03-23
Revision comment: Cleanup (formatting)
"""
__version__ = "1.3.1"

import wx
from LaserAttenuatorPanel import LaserAttenuatorPanel


class LaserAttenuatorXrayHutchPanel(LaserAttenuatorPanel):
    title = "Laser Attenuator [in X-Ray Hutch]"

    def __init__(self):
        from id14 import trans2
        LaserAttenuatorPanel.__init__(self, trans2, title=self.title)


if __name__ == "__main__":
    from redirect import redirect

    redirect("LaserAttenuatorXrayHutchPanel")
    app = wx.GetApp() if wx.GetApp() else wx.App()
    panel = LaserAttenuatorXrayHutchPanel()
    app.MainLoop()
