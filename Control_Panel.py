#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2019-03-26
Date last modified: 2022-07-19
Revision comment: No auto-size by default
"""
__version__ = "1.8.1"

import logging
import wx

from db_property import db_property


class Control_Panel(wx.Frame):
    """General-purpose toplevel window"""
    name = "BioCARS.test"

    auto_size = False

    panel = None

    def __init__(self, name=None, parent=None, panel_type=None):
        self.panel_type = Test_Panel
        if name is not None:
            self.name = name
        if panel_type is not None:
            self.panel_type = panel_type

        logging.info(f"{self} started")
        wx.Frame.__init__(self, parent=parent)

        self.update()
        self.update_title()
        self.Show()

        self.Bind(wx.EVT_SIZE, self.OnResize)
        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroy)

        # Refresh
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
        self.timer.Start(5000, oneShot=True)

    def __repr__(self):
        return f"{self.class_name}({self.name!r})"

    icon = "Tool"

    default_size = (300, 200)
    size = db_property("size", default_size, local=True)

    @property
    def db_name(self):
        if "." in self.name:
            domain_name, base_name = self.name.split(".", 1)
            db_name = f"domains/{domain_name}/{self.class_name.lower()}/{base_name}"
        else:
            domain_name = self.name
            db_name = f"domains/{domain_name}/{self.class_name.lower()}"
        return db_name

    @property
    def title(self):
        if not self.saved_title:
            title = self.default_title
        else:
            title = self.saved_title
        return title

    @title.setter
    def title(self, title):
        self.saved_title = title

    saved_title = ""

    @property
    def default_title(self):
        from capitalize import capitalize
        class_name = self.panel_type.__name__
        class_name = class_name.replace("_", " ")
        class_name = capitalize(class_name)
        name = self.name
        name = name.replace(".", " ")
        name = name.replace("_", " ")
        name = capitalize(name)
        title = f"{class_name} [{name}]"
        return title

    def OnDestroy(self, event):
        event.Skip()
        logging.info(f"{self}: Window destroyed")

    def OnTimer(self, _event):
        """Perform periodic updates"""
        self.update_title()
        try:
            self.update_controls()
        except Exception as msg:
            logging.error("%s" % msg)
            import traceback
            traceback.print_exc()
        self.timer.Start(5000, oneShot=True)

    def update_controls(self):
        module = __import__(self.module_name)
        my_class = getattr(module, self.class_name, None)
        if my_class and self.__class__ != my_class:
            logging.debug("Code change detected, updating panel")
            self.__class__ = my_class
            self.update()

    def update(self):
        from Icon import SetIcon
        SetIcon(self, self.icon)

        panel = self.ControlPanel
        if self.panel is not None:
            self.panel.Destroy()
        self.panel = panel

        menuBar = self.menuBar
        old_menu_bar = self.MenuBar
        self.MenuBar = menuBar
        if old_menu_bar:
            old_menu_bar.Destroy()

        min_size = (100, 50)
        max_size = (1024, 768)

        if self.auto_size:
            logging.debug(f"{self}: Auto-sizing because auto-size requested")
            auto_size = True
        elif self.size[0] < min_size[0] or self.size[1] < min_size[1]:
            logging.debug(f"{self}: Auto-sizing because size {self.size} is smaller than minimum size {min_size}")
            auto_size = True
        else:
            auto_size = False

        if auto_size:
            self.panel.Fit()
            self.Fit()
            logging.debug(f"{self}: Auto-sized to {self.Size}")
            size = self.Size
            size = (min(size[0], max_size[0]), min(size[1], max_size[1]))
            if size != self.Size:
                logging.debug(f"{self}: Auto-size {self.Size} is larger than {max_size}. Shrinking to {size}")
                self.Size = size
            if self.Size[0] < min_size[0] or self.Size[1] < min_size[1]:
                size = self.Size
                if size[0] < min_size[0]:
                    size = self.default_size[0], size[1]
                if size[1] < min_size[1]:
                    size = size[0], self.default_size[1]
                logging.debug(f"{self}: Auto-size {self.Size} is smaller than {min_size}. Growing to {size}")
                self.Size = size
        else:
            w, h = self.size
            self.Size = w, h + 1  # size change needed, otherwise panel does not fill window
            self.Size = w, h

    def update_title(self):
        title = self.title
        if self.Title != title:
            self.Title = title

    @property
    def module_name(self):
        from inspect import getmodule
        module_name = getmodule(self).__name__
        return module_name

    @property
    def class_name(self):
        return type(self).__name__

    def OnResize(self, event):
        # logging.debug("%r" % event.Size)
        if self.auto_size:
            self.Fit()
        else:
            event.Skip()
        self.size = tuple(self.Size)

    @property
    def menuBar(self):
        """MenuBar object"""
        # Menus
        menuBar = wx.MenuBar()

        # Edit
        menu = wx.Menu()
        menu.Append(wx.ID_CUT, "Cu&t\tCtrl+X", "selection to clipboard")
        menu.Append(wx.ID_COPY, "&Copy\tCtrl+C", "selection to clipboard")
        menu.Append(wx.ID_PASTE, "&Paste\tCtrl+V", "clipboard to selection")
        menu.Append(wx.ID_DELETE, "&Delete\tDel", "clear selection")
        menu.Append(wx.ID_SELECTALL, "Select &All\tCtrl+A")
        menuBar.Append(menu, "&Edit")
        # Help
        menu = wx.Menu()
        menu.Append(wx.ID_ABOUT, "About...", "Show version number")
        menuBar.Append(menu, "&Help")
        self.Bind(wx.EVT_MENU, self.OnAbout, id=wx.ID_ABOUT)

        return menuBar

    @property
    def ControlPanel(self):
        return self.panel_type(self, self.name)

    def OnAbout(self, event):
        """Show version info"""
        from About import About
        About(self)


class Test_Panel(wx.Panel):
    def __init__(self, parent, name):
        self.name = name
        super().__init__(parent)

        self.Sizer = wx.BoxSizer()

        v_box = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(v_box, flag=wx.EXPAND | wx.ALL, border=10, proportion=1)

        control = wx.TextCtrl(self)
        control.Label = self.name
        v_box.Add(control, flag=wx.EXPAND)
        control = wx.TextCtrl(self)
        v_box.Add(control, flag=wx.EXPAND | wx.TOP, border=2, proportion=1)


if __name__ == '__main__':
    from redirect import redirect

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    redirect("Control_Panel", format=msg_format)

    app = wx.GetApp() if wx.GetApp() else wx.App()
    self = Control_Panel()
    app.MainLoop()
