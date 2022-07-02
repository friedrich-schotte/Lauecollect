#!/usr/bin/env python
"""
Manage settings for different locations and instruments
Author: Friedrich Schotte
Date created: 2015-06-15
Date last modified: 2020-11-06
Revision comment: Cleanup: redirect domain_name
"""
__version__ = "2.0.1"

from logging import debug

import wx
import wx.lib.scrolledpanel

from Control_Panel import Control_Panel


class ConfigurationsPanel(Control_Panel):
    icon = "Utility"
    domain_name = "BioCARS"

    def __init__(self, domain_name=None):
        if domain_name is not None:
            self.domain_name = domain_name
        Control_Panel.__init__(self)

    @property
    def title(self):
        return "Configurations (%s)" % self.domain_name

    @property
    def name(self):
        return type(self).__name__ + "." + self.domain_name

    @property
    def ControlPanel(self):
        return Configurations_Subpanel(self, self.domain_name)


class Configurations_Subpanel(wx.Panel):
    def __init__(self, parent, domain_name):
        wx.Panel.__init__(self, parent)
        self.domain_name = domain_name
        # Controls
        self.Header = wx.lib.scrolledpanel.ScrolledPanel(self)
        self.Body = wx.lib.scrolledpanel.ScrolledPanel(self)

        sample = wx.TextCtrl(self)
        w, h = sample.Size
        sample.Destroy()

        desc_width = 260
        val_width = 100
        button_size = (30, h)
        bitmap_size = (23, 16)

        def rescale(bitmap):
            w, h = bitmap_size
            return bitmap.ConvertToImage().Rescale(w, h, wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()

        left = rescale(wx.ArtProvider.GetBitmap(wx.ART_GO_BACK))
        right = rescale(wx.ArtProvider.GetBitmap(wx.ART_GO_FORWARD))

        def Button(parent, bitmap, **kwargs):
            button = wx.Button(parent, size=button_size, **kwargs)
            button.Label = " "  # Needed for Windows, otherwise button is invisible
            direction = 0
            if bitmap == left:
                direction = wx.RIGHT
            if bitmap == right:
                direction = wx.LEFT
            button.SetBitmap(bitmap, dir=direction)
            return button

        from EditableControls import TextCtrl, ComboBox
        style = wx.TE_PROCESS_ENTER
        self.Configuration = ComboBox(self.Header, size=(desc_width, -1), style=style)
        self.SavedLabel = wx.TextCtrl(self.Header, value="Saved", size=(val_width, -1), style=wx.TE_READONLY)
        self.AllSavedToCurrent = Button(self.Header, right)
        self.AllCurrentToSaved = Button(self.Header, left)
        self.CurrentLabel = wx.TextCtrl(self.Header, value="Current", size=(val_width, -1), style=wx.TE_READONLY)

        N = len(self.configurations.parameters.descriptions)
        style = wx.TE_PROCESS_ENTER
        self.Descriptions = [TextCtrl(self.Body, id=i, size=(desc_width, -1), style=style) for i in range(0, N)]
        self.SavedValues = [ComboBox(self.Body, id=i, size=(val_width, -1), style=style) for i in range(0, N)]
        self.SavedToCurrent = [Button(self.Body, right, id=i) for i in range(0, N)]
        self.CurrentToSaved = [Button(self.Body, left, id=i) for i in range(0, N)]
        self.CurrentValues = [ComboBox(self.Body, id=i, size=(val_width, -1), style=style) for i in range(0, N)]

        # Callbacks
        self.Configuration.Bind(wx.EVT_TEXT_ENTER, self.OnConfiguration)
        self.Configuration.Bind(wx.EVT_COMBOBOX, self.OnConfiguration)
        self.AllSavedToCurrent.Bind(wx.EVT_BUTTON, self.OnAllSavedToCurrent)
        self.AllCurrentToSaved.Bind(wx.EVT_BUTTON, self.OnAllCurrentToSaved)
        for i in range(0, N):
            self.SavedValues[i].Bind(wx.EVT_TEXT_ENTER, self.OnEnterSaved)
            self.SavedValues[i].Bind(wx.EVT_COMBOBOX, self.OnEnterSaved)
            self.SavedToCurrent[i].Bind(wx.EVT_BUTTON, self.OnSavedToCurrent)
            self.CurrentToSaved[i].Bind(wx.EVT_BUTTON, self.OnCurrentToSaved)
            self.CurrentValues[i].Bind(wx.EVT_TEXT_ENTER, self.OnEnterCurrent)
            self.CurrentValues[i].Bind(wx.EVT_COMBOBOX, self.OnEnterCurrent)

        # Layout
        self.spacer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer = self.spacer
        self.spacer.sizer = wx.BoxSizer(wx.VERTICAL)
        self.spacer.Add(self.spacer.sizer, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.TOP, border=10)
        self.spacer.sizer.Add(self.Header, proportion=0, flag=wx.EXPAND)
        self.spacer.sizer.Add(self.Body, proportion=1, flag=wx.EXPAND)

        flag = wx.EXPAND | wx.ALIGN_LEFT

        self.Header.grid = wx.FlexGridSizer(cols=5)
        self.Header.grid.AddGrowableCol(1, proportion=1)
        self.Header.grid.AddGrowableCol(4, proportion=1)
        self.Header.Sizer = self.Header.grid
        self.Header.grid.Add(self.Configuration, flag=flag)
        self.Header.grid.Add(self.SavedLabel, flag=flag)
        self.Header.grid.Add(self.AllSavedToCurrent, flag=flag)
        self.Header.grid.Add(self.AllCurrentToSaved, flag=flag)
        self.Header.grid.Add(self.CurrentLabel, flag=flag)
        self.Header.SetInitialSize((-1, h - 1))
        self.Header.SetupScrolling(scroll_x=False, scroll_y=True)

        self.Body.grid = wx.FlexGridSizer(cols=5)
        self.Body.grid.AddGrowableCol(1, proportion=1)
        self.Body.grid.AddGrowableCol(4, proportion=1)
        for i in range(0, N):
            self.Body.grid.Add(self.Descriptions[i], flag=flag)
            self.Body.grid.Add(self.SavedValues[i], flag=flag)
            self.Body.grid.Add(self.SavedToCurrent[i], flag=flag)
            self.Body.grid.Add(self.CurrentToSaved[i], flag=flag)
            self.Body.grid.Add(self.CurrentValues[i], flag=flag)
        self.Body.Sizer = self.Body.grid
        self.Body.SetupScrolling(scroll_x=False, scroll_y=True)

        self.timer = wx.Timer(self)
        self.keep_alive()

    @property
    def configurations(self):
        from configurations import configurations
        return configurations(domain_name=self.domain_name)

    def keep_alive(self, _event=None):
        """Periodically refresh the displayed settings (every second)."""
        self.refresh()
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.keep_alive, self.timer)
        self.timer.Start(1000, oneShot=True)

    def refresh(self):
        """Update all controls"""
        configuration_names = self.configurations.configuration_names
        if self.Configuration.Value not in configuration_names:
            self.Configuration.Value = self.configurations.current_configuration
        self.Configuration.Items = configuration_names
        configuration_name = self.Configuration.Value

        descriptions = self.configurations.parameters.descriptions
        values = [str(v) for v in self.configurations[""]]
        saved_values = [str(v) for v in self.configurations[configuration_name]]
        choices = [[str(c) for c in C] for C in self.configurations.choices]
        agree = [v1 == v2 for v1, v2 in zip(values, saved_values)]

        self.Configuration.BackgroundColour = (255, 255, 255) if all(agree) else (255, 190, 190)
        self.SavedLabel.BackgroundColour = (255, 255, 255) if all(agree) else (255, 190, 190)
        self.AllSavedToCurrent.BackgroundColour = (255, 255, 255) if all(agree) else (255, 190, 190)
        self.AllSavedToCurrent.Enabled = not all(agree)
        self.AllCurrentToSaved.Enabled = not all(agree)

        N = len(descriptions)
        for i in range(0, N):
            self.Descriptions[i].Value = descriptions[i]
            self.SavedValues[i].Value = saved_values[i]
            self.SavedValues[i].Items = choices[i]
            self.SavedValues[i].BackgroundColour = (255, 255, 255) if agree[i] else (255, 190, 190)
            # The following renders the button invisible on Windows
            # self.SavedToCurrent[i].BackgroundColour = (255,255,255) if agree[i] else (255,190,190)
            self.SavedToCurrent[i].Enabled = not agree[i]
            self.CurrentToSaved[i].Enabled = not agree[i]
            self.SavedValues[i].ForegroundColour = (100, 100, 100)
            self.CurrentValues[i].Value = values[i]
            self.CurrentValues[i].Items = choices[i]

    def OnConfiguration(self, _event):
        """Called if the configuration is switched"""
        self.refresh()

    def OnAllSavedToCurrent(self, _event):
        """Make the named saved configuration active"""
        name = self.Configuration.Value
        self.configurations[""] = self.configurations[name]
        self.refresh()

    def OnAllCurrentToSaved(self, _event):
        """Save the active configuration under the selected name"""
        name = self.Configuration.Value
        self.configurations[name] = self.configurations[""]
        self.refresh()

    def OnSavedToCurrent(self, event):
        """Make the named saved configuration active"""
        i = event.Id
        name = self.Configuration.Value
        # self.configurations[""][i] = self.configurations[name][i]
        conf = self.configurations[""]
        conf[i] = self.configurations[name][i]
        self.configurations[""] = conf
        self.refresh()

    def OnCurrentToSaved(self, event):
        """Save the active configuration under the selected name"""
        i = event.Id
        name = self.Configuration.Value
        # self.configurations[name][i] = self.configurations[""][i]
        conf = self.configurations[name]
        conf[i] = self.configurations[""][i]
        self.configurations[name] = conf
        self.refresh()

    def OnEnterSaved(self, event):
        """Handle entry modification"""
        # debug("event.Id = %r" % event.Id)
        # debug("event.String = %r" % str(event.String))
        i = event.Id
        name = self.Configuration.Value
        value = self.eval(event.String)
        # self.configurations[name][i] = value
        conf = self.configurations[name]
        debug("conf[%r] = %r" % (i, value))
        conf[i] = value
        debug("self.configurations[%r] = conf" % name)
        self.configurations[name] = conf
        self.refresh()

    def OnEnterCurrent(self, event):
        """Handle entry modification"""
        # debug("event.Id = %r" % event.Id)
        # debug("event.String = %r" % str(event.String))
        i = event.Id
        value = self.eval(event.String)
        # self.configurations[""][i] = value
        conf = self.configurations[""]
        conf[i] = value
        self.configurations[""] = conf
        self.refresh()

    @staticmethod
    def eval(x):
        """Convert x to a built-in Python data type, by default to string"""
        try:
            return eval(x)
        except Exception:
            return str(x)


if __name__ == '__main__':
    # from pdb import pm  # for debugging
    from redirect import redirect

    # import autoreload

    domain_name = "BioCARS"
    # domain_name = "LaserLab"
    # domain_name = "TestBench"

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    redirect(f"{domain_name}.ConfigurationPanel", format=msg_format)

    app = wx.GetApp() if wx.GetApp() else wx.App()
    self = ConfigurationsPanel(domain_name)
    app.MainLoop()
