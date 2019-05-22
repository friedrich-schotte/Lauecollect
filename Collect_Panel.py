#!/usr/bin/env python
"""Control panel for data dollection.
Author: Friedrich Schotte
Date created: 2018-10-17
Date last modified: 2019-05-21
"""
__version__ = "1.1.2" #  changed pperiodic update timer from 5000 to 10000 ms Valentyn

from logging import debug,info,warn,error
import wx
from instrumentation import * # passed on in "globals()"

class Collect_Panel(wx.Frame):
    """Control panel for data dollection"""
    name = "Collect_Panel"
    title = "PP Acquire"
    icon = "Tool"

    def __init__(self,parent=None):
        wx.Frame.__init__(self,parent=parent)

        self.update()
        self.Show()

        # Refresh
        self.timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.OnTimer,self.timer)
        self.timer.Start(10000,oneShot=True)

    def update(self):
        self.Title = self.title
        from Icon import SetIcon
        SetIcon(self,self.icon)
        panel = self.ControlPanel
        if hasattr(self,"panel"): self.panel.Destroy()
        self.panel = panel
        self.Fit()

    def OnTimer(self,event):
        """Perform periodic updates"""
        try: self.update_controls()
        except Exception,msg:
            error("%s" % msg)
            import traceback
            traceback.print_exc()
        self.timer.Start(10000,oneShot=True)

    def update_controls(self):
        if self.code_outdated:
            self.update_code()
            self.update()

    @property
    def code_outdated(self):
        outdated = False
        try:
            from inspect import getfile
            from os.path import getmtime,basename
            filename = getfile(self.__class__).replace(".pyc",".py")
            ##debug("module: %s" % basename(filename))
            if self.timestamp == 0: self.timestamp = getmtime(filename)
            outdated = getmtime(filename) != self.timestamp
        except Exception,msg: pass ##debug("code_outdated: %s" % msg)
        return outdated

    def update_code(self):
        from inspect import getfile
        from os.path import getmtime,basename
        filename = getfile(self.__class__).replace(".pyc",".py")
        ##debug("module: %s" % basename(filename))
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
        from EditableControls import ComboBox,TextCtrl,Choice
        from Controls import Control
        from DirectoryControl import DirectoryControl

        flag = wx.ALIGN_CENTRE_HORIZONTAL|wx.ALL
        border = 2
        l = wx.ALIGN_LEFT; r = wx.ALIGN_RIGHT; cv = wx.ALIGN_CENTER_VERTICAL
        a = wx.ALL; e = wx.EXPAND

        frame = wx.BoxSizer()
        panel.SetSizer(frame)

        layout = wx.BoxSizer(wx.VERTICAL)
        frame.Add(layout,flag=wx.EXPAND|wx.ALL,border=10,proportion=1)
        layout_flag = wx.EXPAND

        group = wx.FlexGridSizer(cols=2)
        layout.Add(group,flag=layout_flag,border=border,proportion=1)

        label = wx.StaticText(panel,label="Method:")
        group.Add(label,flag=cv,border=0,proportion=1)
        subgroup = wx.BoxSizer(wx.HORIZONTAL)
        control = Control(panel,type=ComboBox,
            globals=globals(),
            locals=locals(),
            name="Collect_Panel.Method",
            size=(395,-1),
        )
        subgroup.Add(control,flag=l|cv|a,border=0,proportion=1)
        control = Control(panel,type=wx.Button,
            globals=globals(),
            locals=locals(),
            name="Collect_Panel.Show_Methods",
            label="Methods...",
        )
        subgroup.Add(control,flag=l|cv|a,border=0)
        group.Add(subgroup,flag=l|cv|a,border=border)

        label = wx.StaticText(panel,label="Time to Finish [s]:")
        group.Add(label,flag=cv,border=0,proportion=1)
        control = Control(panel,type=TextCtrl,
            globals=globals(),
            locals=locals(),
            name="Collect_Panel.Time_to_Finish",
            size=(350,-1),
        )
        group.Add(control,flag=l|cv|a|e,border=border,proportion=1)

        group.AddSpacer(20)
        group.AddSpacer(20)

        label = wx.StaticText(panel,label="File:")
        group.Add(label,flag=cv,border=0,proportion=1)
        subgroup = wx.BoxSizer(wx.HORIZONTAL)
        control = Control(panel,type=TextCtrl,
            globals=globals(),
            locals=locals(),
            name="Collect_Panel.File",
            size=(200,-1),
        )
        subgroup.Add(control,flag=l|cv|a,border=0)
        label = wx.StaticText(panel,label="Extension:")
        subgroup.Add(label,flag=cv,border=0)
        control = Control(panel,type=wx.TextCtrl,
            globals=globals(),
            locals=locals(),
            name="Collect_Panel.Extension",
            size=(60,-1),
        )
        subgroup.Add(control,flag=l|cv|a,border=0)
        group.Add(subgroup,flag=l|cv|a,border=border)

        label = wx.StaticText(panel,label="Description:")
        group.Add(label,flag=cv,border=0,proportion=1)
        control = Control(panel,type=TextCtrl,
            globals=globals(),
            locals=locals(),
            name="Collect_Panel.Description",
            size=(480,-1),
        )
        group.Add(control,flag=l|cv|a,border=border)

        label = wx.StaticText(panel,label="Logfile:")
        group.Add(label,flag=cv,border=0,proportion=1)
        control = Control(panel,type=TextCtrl,
            globals=globals(),
            locals=locals(),
            name="Collect_Panel.Logfile",
            size=(200,-1),
        )
        group.Add(control,flag=l|cv|a,border=border)

        label = wx.StaticText(panel,label="Path:")
        group.Add(label,flag=cv,border=0,proportion=1)
        control = DirectoryControl(panel,
            globals=globals(),
            locals=locals(),
            name="Collect_Panel.Path",
            size=(390,-1),
        )
        group.Add(control,flag=l|cv|a,border=border)

        indicator = Control(panel,type=wx.StaticText,
            globals=globals(),
            locals=locals(),
            name="Collect_Panel.Info",
            size=(600,-1),
            label="-"*100,
        )
        layout.Add(indicator,flag=layout_flag,border=border,proportion=0)

        indicator = Control(panel,type=wx.StaticText,
            globals=globals(),
            locals=locals(),
            name="Collect_Panel.Status",
            size=(600,-1),
            label="-"*100,
        )
        layout.Add(indicator,flag=layout_flag,border=border,proportion=0)

        indicator = Control(panel,type=wx.StaticText,
            globals=globals(),
            locals=locals(),
            name="Collect_Panel.Actual",
            size=(600,-1),
            label="-"*100,
        )
        layout.Add(indicator,flag=layout_flag,border=border,proportion=0)

        group = wx.BoxSizer(wx.HORIZONTAL)
        layout.Add(group,flag=layout_flag,border=border)
        width,height = 115,27
        flag = wx.EXPAND
        control = Control(panel,type=wx.ToggleButton,
            globals=globals(),
            locals=locals(),
            name="Collect_Panel.Generate_Packets",
            label="Generate Packets",
            size=(width,height),
        )
        group.Add(control,flag=flag,border=border,proportion=1)
        control = Control(panel,type=wx.ToggleButton,
            globals=globals(),
            locals=locals(),
            name="Collect_Panel.Collect_Dataset",
            label="Collect Dataset",
            size=(width,height),
        )
        group.Add(control,flag=flag,border=border,proportion=1)
        control = Control(panel,type=wx.ToggleButton,
            globals=globals(),
            locals=locals(),
            name="Collect_Panel.Erase_Dataset",
            label="Erase Dataset",
            size=(width,height),
        )
        group.Add(control,flag=flag,border=border,proportion=1)
        control = Control(panel,type=wx.ToggleButton,
            globals=globals(),
            locals=locals(),
            name="Collect_Panel.Finish_Series",
            label="Finish Series",
            size=(width,height),
        )
        group.Add(control,flag=flag,border=border,proportion=1)
        control = Control(panel,type=Choice,
            globals=globals(),
            locals=locals(),
            name="Collect_Panel.Finish_Series_Variable",
            size=(width,height),
        )
        group.Add(control,flag=flag,border=border,proportion=1)

        panel.Fit()
        return panel

    @staticmethod
    def show_methods():
        from SavedPositionsPanel_2 import show_panel
        show_panel("method")

    @staticmethod
    def play_sound():
        from sound import play_sound
        play_sound("ding")


if __name__ == '__main__':
    from pdb import pm
    from redirect import redirect
    redirect("Collect_Panel")
    ##import autoreload
    # Needed to initialize WX library
    if not hasattr(wx,"app"): wx.app = wx.App(redirect=False)
    panel = Collect_Panel()
    wx.app.MainLoop()
