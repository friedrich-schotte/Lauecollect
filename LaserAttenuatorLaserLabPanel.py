#!/usr/bin/env python
"""
Control panel for variable laser attenuator
Author: Friedrich Schotte
Date created: 2009-06-08
Date last modified: 2020-03-23
Revision comment: Cleanup (formatting)
"""
__version__ = "1.2.1"

import wx
from LaserAttenuatorPanel import LaserAttenuatorPanel


class LaserAttenuatorLaserLabPanel(LaserAttenuatorPanel):
    title = "Laser Attenuator [in Laser Lab]"

    def __init__(self):
        from id14 import trans1
        LaserAttenuatorPanel.__init__(self, trans1, title=self.title)


if __name__ == "__main__":
    from redirect import redirect

    redirect("LaserAttenuatorLaserLabPanel")
    app = wx.GetApp() if wx.GetApp() else wx.App()
    panel = LaserAttenuatorLaserLabPanel()
    app.MainLoop()
