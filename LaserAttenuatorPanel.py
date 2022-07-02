#!/usr/bin/env python
"""
Control panel for variable laser attenuator
Author: Friedrich Schotte
Date created: 2009-06-08
Date last modified: 2022-03-23
Revision comment: line 77, in __init__
    buttons.Add(self.RefreshButton, flag=wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, border=5)
    wx._core.wxAssertionError: C++ assertion "!(flags & wxALIGN_CENTRE_HORIZONTAL)"
    failed at wxWidgets/src/common/sizer.cpp(2176) in DoInsert(): Horizontal alignment flags are ignored in horizontal sizers
"""

import wx
from EditableControls import ComboBox

__version__ = "1.2.5"


class LaserAttenuatorPanel(wx.Frame):
    """variable laser attenuator control panel"""

    def __init__(self, trans, title="Laser Attenuator"):
        """trans: attenuator objects"""
        wx.Frame.__init__(self, parent=None, title=title)

        self.trans = trans
        self.timer = wx.Timer(self)

        # Highlight an Edit control if its contents have been modified
        # but not applied yet by hitting the Enter key.
        self.edited = wx.Colour(255, 255, 220)

        panel = wx.Panel(self)
        # Controls
        style = wx.TE_PROCESS_ENTER
        size = (100, -1)
        choices = ["0"]
        self.Angle = ComboBox(panel, choices=choices, size=size, style=style)

        choices = ["1", "0.5", "0.2", "0.1", "0.05", "0.02", "0.01"]
        self.Transmission = ComboBox(panel, choices=choices, size=size, style=style)

        self.LiveCheckBox = wx.CheckBox(panel, label="Live")
        self.RefreshButton = wx.Button(panel, label="Refresh")

        # Callbacks
        self.Angle.Bind(wx.EVT_CHAR, self.OnEditAngle)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnEnterAngle, self.Angle)
        self.Bind(wx.EVT_COMBOBOX, self.OnEnterAngle, self.Angle)

        self.Transmission.Bind(wx.EVT_CHAR, self.OnEditTransmission)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnEnterTransmission, self.Transmission)
        self.Bind(wx.EVT_COMBOBOX, self.OnEnterTransmission, self.Transmission)

        self.Bind(wx.EVT_CHECKBOX, self.OnLive, self.LiveCheckBox)
        self.Bind(wx.EVT_BUTTON, self.OnRefresh, self.RefreshButton)

        # Layout
        layout = wx.GridBagSizer(1, 1)
        a = wx.ALIGN_CENTRE_VERTICAL
        e = wx.EXPAND
        # Specified a label length to prevent line wrapping.
        # This is a bug in the Linux version of wxPython 2.6, fixed in 2.8.
        size = (160, -1)

        t = wx.StaticText(panel, label="Angle [deg]:", size=size)
        layout.Add(t, (0, 0), flag=a)
        layout.Add(self.Angle, (0, 1), flag=a | e)

        t = wx.StaticText(panel, label="Transmission:", size=size)
        layout.Add(t, (1, 0), flag=a)
        layout.Add(self.Transmission, (1, 1), flag=a | e)

        # Leave a 10 pixel wide border.
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(layout, flag=wx.ALL, border=5)
        buttons = wx.BoxSizer(wx.HORIZONTAL)
        buttons.Add(self.LiveCheckBox, flag=wx.ALIGN_CENTER_VERTICAL)
        buttons.AddSpacer(5)
        buttons.Add(self.RefreshButton, flag=wx.ALL, border=5)
        box.Add(buttons, flag=wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, border=5)
        panel.SetSizer(box)
        panel.Fit()
        self.Fit()

        self.Show()

        # Initialization
        self.refresh()

    def refresh(self):
        """Updates the controls with current values"""

        self.Angle.Value = ("%.1f" % self.trans.angle)
        self.Transmission.Value = ("%.3g" % self.trans.value)

    def OnLive(self, _event):
        """Called when the 'Live' checkbox is either checked or unchecked."""
        self.RefreshButton.Enabled = not self.LiveCheckBox.Value
        if self.LiveCheckBox.Value:
            self.keep_alive()

    def keep_alive(self, _event=None):
        """Periodically refresh the displayed settings (every second)."""
        if self.LiveCheckBox.Value:
            self.refresh()
            self.timer = wx.Timer(self)
            self.Bind(wx.EVT_TIMER, self.keep_alive, self.timer)
            self.timer.Start(1000, oneShot=True)

    def OnEditAngle(self, event):
        """Called when typing in the position field."""
        self.Angle.BackgroundColour = self.edited
        # Pass this event on to further event handlers bound to this event.
        # Otherwise, the typed text does not appear in the window.
        event.Skip()

    def OnEnterAngle(self, _event):
        """Called when typing 'Enter' in the position field."""
        self.Angle.BackgroundColour = wx.WHITE
        text = self.Angle.GetValue()
        # noinspection PyBroadException
        try:
            value = float(eval(text))
        except Exception:
            self.refresh()
            return
        self.trans.angle = value
        self.refresh()

    def OnEditTransmission(self, event):
        """Called when typing in the position field."""
        self.Transmission.BackgroundColour = self.edited
        # Pass this event on to further event handlers bound to this event.
        # Otherwise, the typed text does not appear in the window.
        event.Skip()

    def OnEnterTransmission(self, _event):
        """Called when typing 'Enter' in the position field."""
        self.Transmission.BackgroundColour = wx.WHITE
        text = self.Transmission.GetValue()
        # noinspection PyBroadException
        try:
            value = float(eval(text))
        except Exception:
            self.refresh()
            return
        self.trans.value = value
        self.refresh()

    def OnRefresh(self, _event=None):
        """Check whether the network connection is OK."""
        # Reset pending status of entered new position 
        self.Angle.BackgroundColour = wx.WHITE
        self.Transmission.BackgroundColour = wx.WHITE
        self.refresh()


if __name__ == '__main__':
    from id14 import trans

    app = wx.GetApp() if wx.GetApp() else wx.App()
    panel = LaserAttenuatorPanel(trans, title="Laser Attenuator")
    app.MainLoop()
