#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2019-03-26
Date last modified:  2019-03-26
"""
__version__ = "1.0" 

from logging import debug,info,warn,error
from traceback import format_exc

import wx

from instrumentation import timing_system # -> globals()

from Control_Panel import Control_Panel
class Timing_Configuration_Panel(Control_Panel):
    """Control panel for Lecroy Oscilloscope"""
    name = "Timing_Configuration_Panel"
    title = "Timing Configuration"

    @property
    def ControlPanel(self):
        from Controls import Control
        panel = wx.Panel(self)

        frame = wx.BoxSizer()
        panel.Sizer = frame
        
        layout = wx.BoxSizer(wx.VERTICAL)
        frame.Add(layout,flag=wx.EXPAND|wx.ALL,border=10,proportion=1)

        width = 160
        
        control = Control(panel,type=wx.ComboBox,
            globals=globals(),
            locals=locals(),
            name=self.name+".EPICS_Record",
            size=(width,-1),
        )
        layout.Add(control,flag=wx.ALIGN_CENTRE|wx.ALL)

        control = Control(panel,type=wx.TextCtrl,
            globals=globals(),
            locals=locals(),
            name=self.name+".IP_Address",
            size=(width,-1),
        )
        layout.Add(control,flag=wx.ALIGN_CENTRE|wx.ALL)

        control = Control(panel,type=wx.ComboBox,
            globals=globals(),
            locals=locals(),
            name=self.name+".Configuration",
            size=(width,-1),
        )
        layout.Add(control,flag=wx.ALIGN_CENTRE|wx.ALL)
        
        control = Control(panel,type=wx.Button,
            globals=globals(),
            locals=locals(),
            name=self.name+".Load",
            size=(width,-1),
        )
        layout.Add(control,flag=wx.ALIGN_CENTRE|wx.ALL)

        control = Control(panel,type=wx.Button,
            globals=globals(),
            locals=locals(),
            name=self.name+".Save",
            size=(width,-1),
        )
        layout.Add(control,flag=wx.ALIGN_CENTRE|wx.ALL)

        panel.Fit()
        return panel

if __name__ == '__main__':
    from pdb import pm
    import autoreload
    # Needed to initialize WX library
    wx.app = wx.App(redirect=False)
    panel = Timing_Configuration_Panel()
    wx.app.MainLoop()
