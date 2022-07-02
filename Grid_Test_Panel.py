#!/usr/bin/env python
"""
Configuration panel for the BioCARS FPGA timing system.
Saving and restoring settings

Author: Friedrich Schotte
Date created: 2019-06-18
Date last modified: 2019-06-18
"""
__version__ = "1.0"  

from logging import debug,info,warn,error
from traceback import format_exc

import wx
import wx.grid

from Control_Panel import Control_Panel
class Grid_Test_Panel(Control_Panel):
    name = "Grid_Test_Panel"
    title = "Grid Test"

    @property
    def ControlPanel(self):
        from Controls import Control
        panel = wx.Panel(self)

        frame = wx.BoxSizer()
        panel.Sizer = frame
        layout = wx.BoxSizer(wx.VERTICAL)
        frame.Add(layout,flag=wx.EXPAND|wx.ALL,border=10,proportion=1)

        ##import wx.grid
        control = wx.grid.Grid(panel)
        ##control.SetRowLabelSize(0) # Hide row labels (1,2,...).
        control.CreateGrid(5,5)
        ##control.AutoSize()
        layout.Add(control,flag=wx.ALIGN_CENTRE|wx.ALL)

        panel.Fit()
        return panel

if __name__ == '__main__':
    from pdb import pm
    import autoreload
    from redirect import redirect
    redirect("Grid_Test_Panel")

    import wx
    app = wx.App()
    panel = Grid_Test_Panel()
    app.MainLoop()
