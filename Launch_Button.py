#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2020-02-04
Date last modified: 2022-06-13
Revision comment: Updated example
"""
__version__ = "1.1.1"

from logging import debug, warning

import wx


class Launch_Button(wx.Button):
    def __init__(
            self,
            parent,
            domain_name="",
            module_name="",
            command="",
            icon="",
            icon_size=32,
            *args,
            **kwargs
    ):
        wx.Button.__init__(self, parent, *args, **kwargs)
        self.domain_name = domain_name
        self.module_name = module_name
        self.command = command
        self.icon_name = icon
        self.icon_size = icon_size
        self.Bind(wx.EVT_BUTTON, self.OnButton)

        self.check_parameters()

        if self.icon:
            self.SetBitmap(self.icon, wx.LEFT)
        # self.SetBitmapMargins((8,8)) # default: 4

    def __repr__(self):
        name = type(self).__name__
        return f"{name}(module_name={self.module_name!r}, command={self.command!r})"

    def OnButton(self, _event):
        debug("starting %r" % self.application)
        self.application.start()

    @property
    def application(self):
        from application import application
        return application(
            domain_name=self.domain_name,
            module_name=self.module_name,
            command=self.command,
        )

    @property
    def icon(self):
        icon = None
        if self.icon_filename:
            try:
                icon = wx.Image(self.icon_filename)
            except Exception as msg:
                warning("%s: %s" % (self.icon_filename, msg))
        if icon:
            icon = icon.Rescale(self.icon_size, self.icon_size, wx.IMAGE_QUALITY_HIGH)
            icon = wx.Bitmap(icon)
        return icon

    @property
    def icon_filename(self):
        filename = ""
        if self.icon_name:
            from os.path import exists
            basename = self.icon_dir + "/" + self.icon_name
            if exists(basename + ".ico"):
                filename = basename + ".ico"
            elif exists(basename + ".png"):
                filename = basename + ".png"
            else:
                warning("%r.{ico,png}: neither file found" % basename)
        return filename

    @property
    def icon_dir(self):
        from module_dir import module_dir
        return module_dir(type(self)) + "/icons"

    def check_parameters(self):
        if not self.domain_name:
            warning(f"{self}: domain_name not specified")
        if not self.module_name:
            self.module_name, self.command = self.command.split(".", 1)
            warning(f"{self}: Assuming module_name={self.module_name!r}, command={self.command!r}")


if __name__ == '__main__':
    from redirect import redirect

    domain_name = "BioCARS"
    redirect(f"{domain_name}.Launch_Button")

    from Control_Panel import Control_Panel


    class Test_Panel(Control_Panel):
        name = "Test_Panel"
        title = "Test"
        domain_name = "BioCARS"

        @property
        def ControlPanel(self):
            from Controls import Control
            panel = wx.Panel(self)

            frame = wx.BoxSizer()
            panel.Sizer = frame
            layout = wx.BoxSizer(wx.VERTICAL)
            frame.Add(layout, flag=wx.EXPAND | wx.ALL, border=10, proportion=1)

            panel.controls = []
            size = (400, -1)
            style = wx.BU_LEFT
            flag = wx.ALIGN_CENTRE | wx.ALL

            control = Launch_Button(
                parent=panel,
                size=size,
                style=style,
                label="PP Acquire...",
                domain_name=self.domain_name,
                module_name="Acquisition_Panel",
                command=f"Acquisition_Panel('{self.domain_name}')",
                icon="Tool",
            )
            layout.Add(control, flag=flag)
            panel.controls.append(control)

            control = Launch_Button(
                parent=panel,
                size=size,
                style=style,
                label="Heat-Load Chopper Modes...",
                domain_name=self.domain_name,
                module_name="Configuration_Table_Panel",
                command=f"Configuration_Table_Panel('{self.domain_name}.heat_load_chopper_modes')",
                icon="Utility",
            )
            layout.Add(control, flag=flag)
            panel.controls.append(control)

            panel.Fit()
            return panel


    app = wx.App()
    test_panel = Test_Panel()
    app.MainLoop()
