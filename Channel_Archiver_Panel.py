#!/usr/bin/env python
"""
Archive EPICS process variable via Channel Access
Author: Friedrich Schotte
Date created: 2017-10-04
Date last modified: 2022-03-10
Revision comment: Cleanup: from channel_archiver import channel_archiver
"""
__version__ = "1.2.4"

from logging import debug

import wx


class Channel_Archiver_Panel(wx.Frame):
    domain_name = "BioCARS"
    icon = "Archiver"

    @property
    def db_name(self):
        return "channel_archiver/%s" % self.domain_name

    from db_property import db_property
    names = db_property("names", {})
    known_PVs = db_property("known_PVs", [])

    def __init__(self, domain_name=None):
        if domain_name is not None:
            self.domain_name = domain_name

        wx.Frame.__init__(self, parent=None)

        self.Title = self.title
        from Icon import SetIcon
        SetIcon(self, self.icon)

        self.panel = wx.Panel(self)

        border = wx.BoxSizer(wx.VERTICAL)

        flag = wx.ALL | wx.EXPAND
        box = wx.BoxSizer(wx.VERTICAL)
        from wx import grid
        self.Table = grid.Grid(self.panel)
        nrows = max(len(self.PVs), 1)
        self.Table.CreateGrid(nrows, 4)
        self.Table.SetRowLabelSize(20)  # 1,2,...
        self.Table.SetColLabelSize(20)
        self.Table.SetColLabelValue(0, "Log")
        self.Table.SetColLabelValue(1, "Description")
        self.Table.SetColLabelValue(2, "Process Variable")
        self.Table.SetColLabelValue(3, "Value")

        for i in range(0, min(nrows, len(self.PVs))):
            if i < len(self.PVs_use) and self.PVs_use[i]:
                text = "Yes"
            else:
                text = "No"
            self.Table.SetCellValue(i, 0, text)
            if i < len(self.PV_names):
                self.Table.SetCellValue(i, 1, self.PV_names[i])
            self.Table.SetCellValue(i, 2, self.PVs[i])

        self.Table.AutoSize()
        self.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.OnEnterCell, self.Table)
        box.Add(self.Table, flag=flag, proportion=1)

        buttons = wx.BoxSizer()
        button = wx.Button(self.panel, label="+", style=wx.BU_EXACTFIT)
        self.Bind(wx.EVT_BUTTON, self.add_row, button)
        buttons.Add(button, flag=flag)
        size = button.GetSize()
        button = wx.Button(self.panel, label="-", size=size)
        self.Bind(wx.EVT_BUTTON, self.delete_row, button)
        buttons.Add(button, flag=flag)
        box.Add(buttons, flag=flag)

        # Leave a 10-pixel wide space around the panel.
        border.Add(box, flag=flag, border=10, proportion=1)

        flag = wx.ALL | wx.EXPAND
        group = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, label="Destination:")
        group.Add(label, flag=flag)
        style = wx.TE_PROCESS_ENTER
        from EditableControls import TextCtrl
        self.Directory = TextCtrl(self.panel, size=(250, -1), style=style)
        self.Directory.Value = self.channel_archiver.directory
        self.Bind(wx.EVT_TEXT_ENTER, self.OnDirectory, self.Directory)
        group.Add(self.Directory, flag=flag, proportion=1)
        button = wx.Button(self.panel, label="Browse...")
        self.Bind(wx.EVT_BUTTON, self.OnBrowse, button)
        group.Add(button, flag=flag)
        # Leave a 10-pixel wide space around the panel.
        flag = wx.ALL | wx.EXPAND
        border.Add(group, flag=flag, border=10)

        buttons = wx.BoxSizer()
        self.ActiveToggle = wx.ToggleButton(self.panel, label="Active")
        self.Bind(wx.EVT_TOGGLEBUTTON, self.OnActive, self.ActiveToggle)
        buttons.Add(self.ActiveToggle, flag=flag)
        buttons.AddSpacer(10)
        button = wx.Button(self.panel, label="Test")
        self.Bind(wx.EVT_BUTTON, self.test, button)
        buttons.Add(button, flag=flag)
        # Leave a 10-pixel wide space around the panel.
        border.Add(buttons, flag=flag, border=10)

        self.panel.Sizer = border
        self.panel.Fit()
        self.Fit()
        self.Show()

        self.Bind(wx.EVT_SIZE, self.OnResize)

        # Periodically refresh the displayed settings.
        self.refresh_period = 1.0
        self.Bind(wx.EVT_TIMER, self.OnUpdate)
        from threading import Thread
        self.thread = Thread(target=self.keep_updated, name="keep_updated")
        self.thread.daemon = True
        self.thread.start()

    @property
    def channel_archiver(self):
        from channel_archiver import channel_archiver
        return channel_archiver(self.domain_name)

    @property
    def title(self):
        return "Channel Archiver [%s]" % self.domain_name

    def keep_updated(self):
        """Periodically refresh the displayed settings."""
        from time import time, sleep
        while True:
            try:
                t0 = time()
                if self.Shown:
                    event = wx.PyCommandEvent(wx.EVT_TIMER.typeId, self.Id)
                    # call OnUpdate in GUI thread
                    wx.PostEvent(self.EventHandler, event)
                while time() < t0 + self.refresh_period:
                    sleep(0.5)
            except RuntimeError:
                break

    def OnUpdate(self, _event):
        self.RefreshStatus()

    def RefreshStatus(self):
        from numpy import isnan
        self.ActiveToggle.Enabled = not isnan(self.channel_archiver.running)
        self.ActiveToggle.Value = self.channel_archiver.running and not isnan(self.channel_archiver.running)

    def OnResize(self, event):
        self.update_layout()
        event.Skip()  # call default handler

    def update_layout(self):
        """Resize components"""
        self.Table.AutoSize()
        self.panel.Fit()
        self.Fit()

    def add_row(self, _event):
        """Add one more row at the end of the table"""
        self.Table.AppendRows(1)
        self.Table.AutoSize()
        self.update_layout()

    def delete_row(self, _event):
        """"Remove the last row of the table"""
        n = self.Table.GetNumberRows()
        self.Table.DeleteRows(n - 1, 1)
        self.Table.AutoSize()
        self.update_layout()

    def OnDirectory(self, _event):
        """Set destination folder for archive"""
        debug("self.channel_archiver.directory = %r" % str(self.Directory.Value))
        self.channel_archiver.directory = str(self.Directory.Value)

    def OnBrowse(self, _event):
        """Set destination folder for archive"""
        from os.path import exists, dirname
        from normpath import normpath
        pathname = self.channel_archiver.directory
        while pathname and not exists(pathname):
            pathname = dirname(pathname)
        dlg = wx.DirDialog(
            parent=self,
            message="Choose a directory:",
            style=wx.DD_DEFAULT_STYLE,
        )
        # ShowModal pops up a dialog box and returns control only after the user
        # has selects OK or Cancel.
        dlg.Path = pathname
        if dlg.ShowModal() == wx.ID_OK:
            self.Directory.Value = normpath(str(dlg.Path))
        dlg.Destroy()
        debug("self.channel_archiver.directory = %r" % str(self.Directory.Value))
        self.channel_archiver.directory = str(self.Directory.Value)

    def OnActive(self, event):
        """Start/stop archiving"""
        # debug("self.channel_archiver.running = %r" % event.IsChecked())
        self.channel_archiver.running = event.IsChecked()

    def OnEnterCell(self, _event):
        """Accept current values"""
        PVs_use = []
        PV_names = []
        PVs = []
        for i in range(0, self.Table.GetNumberRows()):
            PV_use = (self.Table.GetCellValue(i, 0).lower() == "yes")
            PV_name = str(self.Table.GetCellValue(i, 1))
            PV = str(self.Table.GetCellValue(i, 2))
            if PV:
                PVs_use += [PV_use]
                PV_names += [PV_name]
                PVs += [PV]
        self.PVs_use = PVs_use
        self.PV_names = PV_names
        self.PVs = PVs

    def test(self, _event):
        """Check if PVs are working by reading their current value"""
        from CA import caget
        for i in range(0, self.Table.GetNumberRows()):
            enabled = self.Table.GetCellValue(i, 0) == "Yes"
            PV = str(self.Table.GetCellValue(i, 2))
            value = str(caget(PV)) if (PV and enabled) else ""
            self.Table.SetCellValue(i, 3, value)
        self.update_layout()

    def get_PVs(self):
        self.update_known_PVs()
        return self.known_PVs

    def set_PVs(self, PVs):
        self.known_PVs = PVs
        # debug("known_PVs = %r" % self.known_PVs)

    PVs = property(get_PVs, set_PVs)

    def get_PVs_use(self):
        active_PVs = self.channel_archiver.PVs
        use = [PV in active_PVs for PV in self.known_PVs]
        return use

    def set_PVs_use(self, use_list):
        PVs = [PV for (PV, use) in zip(self.known_PVs, use_list) if use]
        self.channel_archiver.PVs = PVs
        debug("self.channel_archiver.PVs = %r" % self.channel_archiver.PVs)

    PVs_use = property(get_PVs_use, set_PVs_use)

    def get_PV_names(self):
        names = [self.names[PV] if PV in self.names else ""
                 for PV in self.PVs]
        return names

    def set_PV_names(self, names):
        PV_names = self.names
        for PV, name in zip(self.PVs, names):
            PV_names[PV] = name
        self.names = PV_names
        # debug("names = %r" % self.names)

    PV_names = property(get_PV_names, set_PV_names)

    def update_known_PVs(self):
        known_PVs = self.known_PVs
        for PV in self.channel_archiver.PVs:
            if PV not in known_PVs:
                known_PVs += [PV]
        self.known_PVs = known_PVs


if __name__ == "__main__":  # for testing

    domain_name = "BioCARS"
    # domain_name = "LaserLab"

    from redirect import redirect

    redirect(f"{domain_name}.Channel_Archiver_Panel")

    app = wx.GetApp() if wx.GetApp() else wx.App()
    self = Channel_Archiver_Panel(domain_name)
    app.MainLoop()
