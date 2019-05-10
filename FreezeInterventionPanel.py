#!/usr/bin/env python
"""
Control panel for optical freeze detector
Runs code to retract the sample from the cooling stream and operate the pump
at high speed as an AeroBasic program "Freeze_Intervention.ab".

Authors: Valentyn Stadnytskyi, Friedrich Schotte
Date created: 8 Mar 2018
Date last modified: 8 Mar 2018

"""
__version__ = "1.0" 

from logging import debug,info,warn,error
import wx
from freeze_intervention import freeze_intervention # passed on in "globals()"

class FreezeInterventionPanel(wx.Frame):
    title = "Freeze Intervention"
    def __init__(self):
        wx.Frame.__init__(self,parent=None,title=self.title)

        # Icon
        from Icon import SetIcon
        SetIcon(self,"Tool")

        self.panel = self.ControlPanel
        self.Fit()
        self.Show()

        # Refresh
        self.timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.OnTimer,self.timer)
        self.timer.Start(5000,oneShot=True)

    def OnTimer(self,event):
        """Perform periodic updates"""
        try: self.update_controls()
        except Exception,msg:
            error("%s" % msg)
            import traceback
            traceback.print_exc()
        self.timer.Start(5000,oneShot=True)

    def update_controls(self):
        if self.code_outdated:
            self.update_code()
            panel = self.ControlPanel
            self.panel.Destroy()
            self.panel = panel
            self.Fit()

    @property
    def code_outdated(self):
        from inspect import getfile
        from os.path import getmtime,basename
        filename = getfile(self.__class__)
        ##debug("module: %s" % filename)
        if self.timestamp == 0: self.timestamp = getmtime(filename)
        outdated = getmtime(filename) != self.timestamp
        return outdated

    def update_code(self):
        from inspect import getfile
        from os.path import getmtime,basename
        filename = getfile(self.__class__)
        ##debug("module: %s" % filename)
        self.timestamp = getmtime(filename)
        module_name = basename(filename).replace(".pyc",".py").replace(".py","")
        module = __import__(module_name)
        reload(module)
        debug("Reloaded module %r" % module.__name__)
        debug("Updating class of %r instance" % self.__class__.__name__)
        self.__class__ = getattr(module,self.__class__.__name__)
            
    timestamp = 0

    @property
    def ControlPanel(self):
        # Controls and Layout
        panel = wx.Panel(self)
        from EditableControls import ComboBox,TextCtrl
        from Controls import Control
        from BeamProfile_window import BeamProfile

        flag = wx.ALIGN_CENTRE_HORIZONTAL|wx.ALL
        border = 2
        l = wx.ALIGN_LEFT; r = wx.ALIGN_RIGHT; cv = wx.ALIGN_CENTER_VERTICAL
        a = wx.ALL

        layout = wx.BoxSizer(wx.HORIZONTAL)
        left_panel = wx.BoxSizer(wx.VERTICAL)

        group = wx.BoxSizer(wx.VERTICAL)        
        text = wx.StaticText(panel,label="Status")
        group.Add (text,flag=flag,border=border)
        control = Control(panel,type=wx.ToggleButton,
            name="FreezeInterventionPanel.Enabled",
            globals=globals(),
            label="Disabled/Enabled",
            size=(180,-1))
        group.Add (control,flag=flag,border=border)
        control = Control(panel,type=wx.ToggleButton,
            name="FreezeInterventionPanel.Active",
            globals=globals(),
            label="Inactive/Active",
            size=(180,-1))
        group.Add (control,flag=flag,border=border)
        left_panel.Add (group,flag=flag,border=border)

        layout.Add (left_panel,flag=flag,border=border)

        panel.SetSizer(layout)
        panel.Fit()
        return panel


if __name__ == '__main__':
    from pdb import pm
    import logging; from tempfile import gettempdir
    logfile = gettempdir()+"/FreezeInterventionPanel.log"
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s %(levelname)s: %(message)s",
        filename=logfile,
    )
    # Needed to initialize WX library
    if not hasattr(wx,"app"): wx.app = wx.App(redirect=False)
    panel = FreezeInterventionPanel()
    wx.app.MainLoop()
