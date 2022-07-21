#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2020-05-23
Date last modified: 2021-07-18
Revision comment: Cleanup: Control_Panel
"""
__version__ = "3.3.7"

from logging import debug, warning
from traceback import format_exc

import wx.grid

from Control_Panel import Control_Panel


class Timing_Channel_Configuration_Panel(Control_Panel):
    icon = "Timing System"
    timing_system_name = "BioCARS"

    def __init__(self, timing_system_name=None):
        if timing_system_name is not None:
            self.timing_system_name = timing_system_name
        self.name = "Timing_Channel_Configuration_Panel.%s" % self.timing_system_name
        super().__init__(name=self.name)

    @property
    def title(self):
        return "Timing System - Channel Configuration [%s]" % self.timing_system_name

    @property
    def ControlPanel(self):
        return Panel(self, self.timing_system_name)


class Panel(wx.Panel):
    property_names = [
        "show_buttons",
    ]

    def __init__(self, parent, timing_system_name):
        wx.Panel.__init__(self, parent=parent)
        self.timing_system_name = timing_system_name

        self.Sizer = wx.BoxSizer(wx.VERTICAL)

        self.table = TableGrid(self.timing_system_name, self)
        self.Sizer.Add(self.table, flag=wx.ALIGN_LEFT | wx.ALL, proportion=1)

        self.buttons = wx.Panel(self)
        self.Sizer.Add(self.buttons, flag=wx.ALIGN_CENTER | wx.ALL, proportion=0)
        self.buttons.Sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.buttons.refresh = wx.Button(self.buttons, label="Refresh")
        self.buttons.Sizer.Add(self.buttons.refresh, flag=wx.ALIGN_CENTER | wx.ALL, border=4)
        self.Bind(wx.EVT_BUTTON, self.table.Refresh, self.buttons.refresh)

        self.buttons.apply = wx.Button(self.buttons, label="Apply")
        self.buttons.Sizer.Add(self.buttons.apply, flag=wx.ALIGN_CENTER | wx.ALL, border=4)
        self.Bind(wx.EVT_BUTTON, self.Apply, self.buttons.apply)

        self.Fit()

        from reference import reference
        from handler import handler
        for property_name in self.property_names:
            reference(self.config, property_name).monitors.add(handler(self.handle_change, property_name))

        self.update()

    from run_async import run_async

    @run_async
    def update(self):
        for property_name in self.property_names:
            value = getattr(self.config, property_name)
            wx.CallAfter(self.set_value, property_name, value)

    def handle_change(self, property_name):
        value = getattr(self.config, property_name)
        # debug(("%s = %.60r" % (property_name,value)).replace("\n",""))
        wx.CallAfter(self.set_value, property_name, value)

    def set_value(self, property_name, value):
        debug(("%s = %.60r" % (property_name, value)).replace("\n", ""))
        if property_name == "show_buttons":
            self.buttons.Shown = value
            self.Layout()

    def Apply(self, _event=None):
        self.config.update()

    @property
    def config(self):
        from timing_system_channel_configuration import timing_system_channel_configuration
        return timing_system_channel_configuration(self.timing_system_name)


class MenuBar(wx.MenuBar):
    property_names = [
        "show_buttons",
    ]

    def __init__(self, timing_system_name):
        wx.MenuBar.__init__(self)
        self.timing_system_name = timing_system_name

        # Edit
        menu = wx.Menu()
        menu.Append(wx.ID_CUT, "Cu&t\tCtrl+X", "selection to clipboard")
        menu.Append(wx.ID_COPY, "&Copy\tCtrl+C", "selection to clipboard")
        menu.Append(wx.ID_PASTE, "&Paste\tCtrl+V", "clipboard to selection")
        menu.Append(wx.ID_DELETE, "&Delete\tDel", "clear selection")
        menu.Append(wx.ID_SELECTALL, "Select &All\tCtrl+A")
        self.Append(menu, "&Edit")

        # Help
        menu = wx.Menu()
        menu.Append(wx.ID_ABOUT, "About...", "Show version number")
        self.Bind(wx.EVT_MENU, self.OnAbout, id=wx.ID_ABOUT)
        self.Append(menu, "&Help")

    def OnAbout(self, _event):
        """Show version info"""
        from About import About
        About(self.Window)


class TableGrid(wx.grid.Grid):
    def __init__(self, timing_system_name, parent):
        wx.grid.Grid.__init__(self, parent, -1)

        self.timing_system_name = timing_system_name

        self.SetTable(GridTable(self.timing_system_name), takeOwnership=True)
        self.SetColumnWidths()

        self.SetRowLabelSize(20)

        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroy)

        try:
            if not hasattr(wx._grid, "wxEVT_GRID_COL_AUTO_SIZE"):
                wx._grid.wxEVT_GRID_COL_AUTO_SIZE = 10263
            if not hasattr(wx.grid, "EVT_GRID_COL_AUTO_SIZE"):
                wx.grid.EVT_GRID_COL_AUTO_SIZE = \
                    wx.PyEventBinder(wx._grid.wxEVT_GRID_COL_AUTO_SIZE, 1)
            self.Bind(wx.grid.EVT_GRID_COL_AUTO_SIZE, self.OnColAutoSize)
        except Exception:
            warning("Column auto-size (double click) not supported")

        from monitor import monitor_all
        monitor_all(self.config.channels, self.handle_update, delay=0.25)

        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

    def OnKeyDown(self, event):
        """Prevent the selected cell from moving down when Enter is pressed"""
        # https://stackoverflow.com/questions/17124337/setting-focus-to-cell-wxgrid
        if event.KeyCode == wx.WXK_RETURN and not event.ControlDown():
            self.DisableCellEditControl()
        else:
            event.Skip()

    @property
    def config(self):
        from timing_system_channel_configuration import timing_system_channel_configuration
        return timing_system_channel_configuration(self.timing_system_name)

    def SetColumnWidths(self):
        for col in range(0, self.Table.GetNumberCols()):
            self.SetColSize(col, self.Table.GetColumnWidth(col))

    def OnColAutoSize(self, event):
        debug("ColAutoSize %r" % event.RowOrCol)
        col = event.RowOrCol
        self.AutoSizeColumn(col, setAsMin=False)

    def handle_update(self):
        debug("Got update")
        wx.CallAfter(self.Refresh)

    def OnDestroy(self, event):
        event.Skip()
        from monitor import monitor_clear_all
        monitor_clear_all(self.config.channels, self.handle_update)


class GridTable(wx.grid.GridTableBase):
    def __init__(self, timing_system_name):
        wx.grid.GridTableBase.__init__(self)
        self.timing_system_name = timing_system_name

    def GetNumberRows(self):
        # Unhandled exception in this method crashes Python interpreter in wx Library
        n_rows = 0
        try:
            n_rows = self.table.n_rows
        except Exception:
            warning(format_exc())
        return n_rows

    def GetNumberCols(self):
        # Unhandled exception in this method crashes Python interpreter in wx Library
        n_cols = 0
        try:
            n_cols = self.table.n_cols
        except Exception:
            warning(format_exc())
        return n_cols

    def IsEmptyCell(self, _row, _col):
        # Text from the cell to the left will extend into this cell if
        # IsEmptyCell returns True.
        # True is the default, if no IsEmptyCell method is provided.
        return False

    def GetColLabelValue(self, col):
        """Tell grid what to show as column header labels"""
        return self.table.col_label(col)

    def GetRowLabelValue(self, row):
        """Tell grid what to show as column header labels"""
        return self.table.row_label(row)

    def GetValue(self, row, col):
        """Tell grid what to display inside a cell"""
        # Unhandled exception in this method crashes Python interpreter in wx Library
        value = ""
        try:
            value = self.table.value(row, col)
        except Exception:
            warning(format_exc())
        return value

    def SetValue(self, row, col, value):
        """Process an entry made in a cell by the user"""
        self.table.set_value(row, col, value)

    def GetAttr(self, _row, _col, _kind):
        """Tell grid the color of a cell
        kind:  wx.grid.GridCellAttr.Any,Cell,Row,Col,Default,Merged"""
        attr = wx.grid.GridCellAttr()
        return attr

    # Called to determine the kind of editor/renderer to use by
    # default, doesn't necessarily have to be the same type used
    # natively by the editor/renderer if they know how to convert.
    # Example:
    # wx.grid.GRID_VALUE_CHOICE + ':minor,normal,major,critical'
    def GetTypeName(self, row, col):
        typeName = wx.grid.GRID_VALUE_STRING
        choices = self.table.choices(row, col)
        if len(choices) > 0:
            if "" not in choices:
                choices = [""] + choices
            typeName = wx.grid.GRID_VALUE_CHOICE + ":" + ",".join(choices)
        # debug("row %r,col %r: %r" % (row,col,typeName))
        return typeName

    # Called to determine how the data can be fetched and stored by the
    # editor and renderer.  This allows you to enforce some type-safety
    # in the grid.
    def CanGetValueAs(self, row, col, typeName):
        return typeName == self.GetTypeName(row, col).split(":")[0]

    def CanSetValueAs(self, row, col, typeName):
        return self.CanGetValueAs(row, col, typeName)

    def GetColumnWidth(self, col):
        return self.table.col_width(col)

    @property
    def table(self):
        return self.config.table

    @property
    def config(self):
        from timing_system_channel_configuration import timing_system_channel_configuration
        return timing_system_channel_configuration(self.timing_system_name)


if __name__ == '__main__':
    timing_system_name = "BioCARS"
    # timing_system_name = "LaserLab"

    from redirect import redirect

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    redirect("%s.Timing_Channel_Configuration_Panel" % timing_system_name, format=msg_format)
    import wx

    app = wx.GetApp() if wx.GetApp() else wx.App()
    self = Timing_Channel_Configuration_Panel(timing_system_name)
    app.MainLoop()
