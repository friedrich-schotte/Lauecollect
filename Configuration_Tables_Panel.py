#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2019-07-16
Date last modified: 2022-06-28
Revision comment: Renamed: configuration_tables_driver
"""
__version__ = "1.6.2"

from logging import info

import wx

from Control_Panel import Control_Panel


class Configuration_Tables_Panel(Control_Panel):
    """Control panel to show all configurations"""
    icon = "Tool"
    title = "Modes/Configurations"
    auto_size = True
    domain_name = "BioCARS"

    def __init__(self, domain_name=None):
        if domain_name is not None:
            self.domain_name = domain_name
        self.title = "Modes/Configurations (%s)" % self.domain_name
        Control_Panel.__init__(self)

    @property
    def name(self):
        return type(self).__name__ + "." + self.domain_name

    @property
    def ControlPanel(self):
        from reference import reference
        from handler import handler

        # Controls and Layout
        panel = wx.Panel(self)
        panel.configure = False

        # sizer = wx.BoxSizer(wx.VERTICAL)
        sizer = wx.GridBagSizer(1, 1)

        flag = wx.ALIGN_CENTRE_VERTICAL | wx.ALL | wx.EXPAND
        buttons = []
        j = 0
        for i in range(0, self.count):
            if self.show_in_list(i):
                button = wx.Button(panel, label=self.label(i), id=i)
                button.Shown = self.show_in_list(i)
                # sizer.Add(button,flag=flag)
                sizer.Add(button, (j, 0), flag=flag)
                j += 1
                buttons += [button]
        panel.buttons = buttons
        panel.SetSizer(sizer)
        panel.Fit()

        self.Bind(wx.EVT_BUTTON, self.show)

        reference(self.configuration_tables, "names").monitors.add(
            handler(self.update_delayed))
        for configuration in self.configuration_tables:
            reference(configuration, "title").monitors.add(
                handler(self.update_delayed))

        return panel

    def update_delayed(self):
        self.schedule_update = True

    from thread_property_2 import thread_property

    @thread_property
    def schedule_update(self):
        from time import sleep
        sleep(0.5)
        wx.CallAfter(self.update)

    @property
    def menuBar(self):
        """MenuBar object"""
        # Menus
        menuBar = wx.MenuBar()
        # View
        self.ViewMenu = wx.Menu()
        for i in range(0, self.count):
            self.ViewMenu.AppendCheckItem(100 + i, " " + self.label(i) + " ")
        self.ViewMenu.AppendSeparator()
        menuBar.Append(self.ViewMenu, "&View")
        # More
        self.MoreMenu = wx.Menu()
        self.MoreMenu.AppendCheckItem(201, "Configure this Panel")
        menuBar.Append(self.MoreMenu, "&More")
        # Help
        menu = wx.Menu()
        menu.Append(wx.ID_ABOUT, "About...", "Show version number")
        menuBar.Append(menu, "&Help")

        # Callbacks
        self.Bind(wx.EVT_MENU_OPEN, self.OnOpenView)
        for i in range(0, self.count):
            self.Bind(wx.EVT_MENU, self.OnView, id=100 + i)

        self.Bind(wx.EVT_MENU, self.OnConfigure, id=201)
        self.Bind(wx.EVT_MENU, self.OnAbout, id=wx.ID_ABOUT)

        return menuBar

    def OnOpenView(self, event):
        """Called if the "View" menu is selected"""
        for i in range(0, self.count):
            self.ViewMenu.Check(100 + i, self.show_in_list(i))
        self.MoreMenu.Check(201, self.panel.configure)

    def OnView(self, event):
        """Called if one of the items of the "View" menu is selected"""
        i = event.Id - 100
        self.set_show_in_list(i, not self.show_in_list(i))
        self.update()

    def OnConfigure(self, event):
        self.panel.configure = not self.panel.configure
        self.update()

    def OnAbout(self, event):
        """Show panel with additional parameters"""
        from About import About
        About(self)

    @property
    def configuration_tables(self):
        from configuration_tables_driver import configuration_tables_driver
        return configuration_tables_driver(self.domain_name)

    def show(self, event):
        """Display control panel"""
        # info("event.Id=%r" % event.Id)
        name = self.configuration_tables.names[event.Id]
        application = self.configuration_panel(name)
        info(f"Starting {application}...")
        application.start()

    def configuration_panel(self, name):
        from application import application
        return application(
            domain_name=self.domain_name,
            module_name="Configuration_Table_Panel",
            command=f"Configuration_Table_Panel('{self.domain_name}.{name}')",
        )

    @property
    def count(self):
        return len(self.configuration_tables)

    def label(self, i):
        return self.configuration_tables[i].title

    def show_in_list(self, i):
        return self.configuration_tables[i].show_in_list

    def set_show_in_list(self, i, value):
        self.configuration_tables[i].show_in_list = value


if __name__ == '__main__':
    domain_name = "BioCARS"
    # domain_name = "LaserLab"

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    from redirect import redirect

    redirect(f"{domain_name}.Configuration_Tables_Panel", format=msg_format)

    # import autoreload

    app = wx.GetApp() if wx.GetApp() else wx.App()
    self = Configuration_Tables_Panel(domain_name)
    app.MainLoop()
