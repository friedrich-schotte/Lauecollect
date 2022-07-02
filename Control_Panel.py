#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2019-03-26
Date last modified: 2022-06-09
Revision comment: Added: panel_type
"""
__version__ = "1.7"

from logging import debug, info, error

import wx


class Control_Panel(wx.Frame):
    """General-purpose toplevel window"""
    name = "BioCARS.test"

    from setting import setting
    default_size = (300, 200)
    size = setting("size", default_size)
    auto_size = False

    from persistent_property import persistent_property
    icon = persistent_property("icon", "Tool")

    panel = None

    def __init__(self, name=None, parent=None, panel_type=None):
        self.panel_type = Test_Panel
        if name is not None:
            self.name = name
        if panel_type is not None:
            self.panel_type = panel_type

        info(f"{self} started")
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

    @property
    def title(self):
        from capitalize import capitalize
        if not self.saved_title:
            class_name = self.panel_type.__name__
            class_name = class_name.replace("_", " ")
            class_name = capitalize(class_name)

            name = self.name
            name = name.replace(".", " ")
            name = name.replace("_", " ")
            name = capitalize(name)

            title = f"{class_name} [{name}]"
        else:
            title = self.saved_title
        return title

    @title.setter
    def title(self, title):
        self.saved_title = title

    saved_title = persistent_property("title", "")

    def OnDestroy(self, event):
        event.Skip()
        info(f"{self}: Window destroyed")

    def OnTimer(self, _event):
        """Perform periodic updates"""
        self.update_title()
        try:
            self.update_controls()
        except Exception as msg:
            error("%s" % msg)
            import traceback
            traceback.print_exc()
        self.timer.Start(5000, oneShot=True)

    def update_controls(self):
        module = __import__(self.module_name)
        my_class = getattr(module, self.class_name, None)
        if my_class and self.__class__ != my_class:
            debug("Code change detected, updating panel")
            self.__class__ = my_class
            self.update()

    def update(self):
        from Icon import SetIcon
        SetIcon(self, self.icon)

        menuBar = self.menuBar
        old_menu_bar = self.MenuBar
        self.MenuBar = menuBar
        if old_menu_bar:
            old_menu_bar.Destroy()

        panel = self.ControlPanel
        if self.panel is not None:
            self.panel.Destroy()
        self.panel = panel

        if self.auto_size:
            self.Fit()
        elif self.size == self.default_size:
            self.Fit()
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
        class_name = self.__class__.__name__
        return class_name

    def OnResize(self, event):
        # debug("%r" % event.Size)
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
