#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2021-07-28
Date last modified: 2022-06-20
Revision comment: Fixed: Issue: Copy & Paste from Excel inserts blank lines
    between rows.
"""
__version__ = "1.5.11"

import logging
import wx
import wx.grid

from run_async import run_async
from thread_property_2 import thread_property


class Spreadsheet(wx.grid.Grid):
    def __init__(self, parent, name, autosize=True, fast_text=False):
        from collections import defaultdict
        from event import event

        super().__init__(parent)
        self.name = name
        self.autosize = autosize
        self.fast_text = fast_text

        self.menu_item_handlers = {}
        self.text_events = defaultdict(lambda: event(0))
        self.background_color_events = defaultdict(lambda: event(0))

        self.updating_table = False  # for "Instance attribute defined outside __init__"
        self.refreshing_delayed = False  # for "Instance attribute defined outside __init__"

        self.Bind(wx.grid.EVT_GRID_LABEL_RIGHT_CLICK, self.OnLabelRightClick)
        self.Bind(wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.OnRightClick)
        self.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.OnCellChanged)
        self.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.OnLeftClick)

        self.Bind(wx.EVT_MENU, self.OnCut, id=wx.ID_CUT)
        self.Bind(wx.EVT_MENU, self.OnCopy, id=wx.ID_COPY)
        self.Bind(wx.EVT_MENU, self.OnPaste, id=wx.ID_PASTE)
        self.Bind(wx.EVT_MENU, self.OnDelete, id=wx.ID_DELETE)
        self.Bind(wx.EVT_MENU, self.OnSelectAll, id=wx.ID_SELECTALL)

        self.TopLevelWindow.Bind(wx.EVT_MENU, self.OnCut, id=wx.ID_CUT)
        self.TopLevelWindow.Bind(wx.EVT_MENU, self.OnCopy, id=wx.ID_COPY)
        self.TopLevelWindow.Bind(wx.EVT_MENU, self.OnPaste, id=wx.ID_PASTE)
        self.TopLevelWindow.Bind(wx.EVT_MENU, self.OnDelete, id=wx.ID_DELETE)
        self.TopLevelWindow.Bind(wx.EVT_MENU, self.OnSelectAll, id=wx.ID_SELECTALL)

        self.CreateGrid(1, 1)
        self.RowLabelSize = 20
        self.initialize()
        logging.debug(f"{self} Initialized")

    def __repr__(self):
        return f"{type(self).__name__}({self.name!r})"

    def initialize(self):
        n_rows = self.table.n_rows - 1
        n_columns = self.table.n_columns - 1
        self.SetNRows(n_rows)
        self.SetNColumns(n_columns)
        if self.fast_text:
            logging.debug(f"{self} Initializing cell text started")
            self.InitializeCellText(0, n_rows, 0, n_columns)
            logging.debug(f"{self} Initializing cell text done")
        self.initialize_stage_2()

    @run_async
    def initialize_stage_2(self):
        n_rows = self.table.n_rows - 1
        n_columns = self.table.n_columns - 1
        if not self.fast_text:
            logging.debug(f"{self} Initializing cell text started")
            self.initialize_cell_text(0, n_rows, 0, n_columns)
            logging.debug(f"{self} Initializing cell text done")
        logging.debug(f"{self} Initializing cell background colors started")
        self.initialize_cell_background_colors(0, n_rows, 0, n_columns)
        logging.debug(f"{self} Initialize cell background colors done")
        self.monitor_cells(0, n_rows, 0, n_columns)
        self.monitor_size()

    @property
    def TopLevelWindow(self):
        window = self
        while window.Parent is not None:
            window = window.Parent
        return window

    @property
    def NumberCols(self):
        return super().NumberCols

    @NumberCols.setter
    def NumberCols(self, n_columns):
        self.table.n_columns = n_columns + 1
        self.SetNColumnsCompleteAsync(n_columns)

    @property
    def table(self):
        from spreadsheet_control import spreadsheet_control
        return spreadsheet_control(self.name)

    def monitor_size(self):
        from reference import reference
        reference(self.table, "n_rows").monitors.add(self.update_handler)
        reference(self.table, "n_columns").monitors.add(self.update_handler)

    def update_table(self):
        self.updating_table = True

    @thread_property
    def updating_table(self):
        n_rows, n_columns = self.NumberRows, self.NumberCols

        # Erase cells no longer needed.
        new_table_n_rows = n_rows + 1
        new_table_n_columns = n_columns + 1
        for row in range(new_table_n_rows, self.table.n_rows):
            for column in range(0, self.table.n_columns):
                self.table.cell(row, column).text = ""
        for column in range(new_table_n_columns, self.table.n_columns):
            for row in range(0, self.table.n_rows):
                self.table.cell(row, column).text = ""
        self.table.n_rows = new_table_n_rows
        self.table.n_columns = new_table_n_columns

        for row in range(0, n_rows):
            for column in range(0, n_columns):
                value = self.GetCellValue(row, column)
                cell = self.table.cell(row + 1, column + 1)
                if value != cell.text:
                    logging.debug(f"{cell}.text = {value!r}")
                    from reference import reference
                    if not reference(cell, "text").monitors:
                        logging.warning(f"{cell} has no monitors")
                    cell.text = value

    def initialize_cells(self, row1, row2, col1, col2):
        self.initialize_cell_text(row1, row2, col1, col2)
        self.initialize_cell_background_colors(row1, row2, col1, col2)

    def InitializeCellText(self, row1, row2, col1, col2):
        if col1 == 0:
            for row in range(row1, row2):
                text = self.table.cell(row + 1, 0).text
                self.SetRowLabelText(row, text)

        if row1 == 0:
            for column in range(col1, col2):
                text = self.table.cell(0, column + 1).text
                self.SetColumnLabelText(column, text)

        for row in range(row1, row2):
            for column in range(col1, col2):
                text = self.table.cell(row + 1, column + 1).text
                self.SetCellText(row, column, text)

        if self.autosize:
            for column in range(col1, col2):
                self.AutoSizeColumn(column, setAsMin=False)

    def initialize_cell_text(self, row1, row2, col1, col2):
        if col1 == 0:
            for row in range(row1, row2):
                text = self.table.cell(row + 1, 0).text
                wx.CallAfter(self.SetRowLabelText, row, text)

        if row1 == 0:
            for column in range(col1, col2):
                text = self.table.cell(0, column + 1).text
                wx.CallAfter(self.SetColumnLabelText, column, text)

        for row in range(row1, row2):
            for column in range(col1, col2):
                text = self.table.cell(row + 1, column + 1).text
                wx.CallAfter(self.SetCellText, row, column, text)

        if self.autosize:
            for column in range(col1, col2):
                wx.CallAfter(self.AutoSizeColumn, column, setAsMin=False)

    def initialize_cell_background_colors(self, row1, row2, col1, col2):
        for row in range(row1, row2):
            for column in range(col1, col2):
                color = self.table.cell(row + 1, column + 1).background_color
                wx.CallAfter(self.SetCellBackgroundColor, row, column, color)

    def monitor_cells(self, row1, row2, col1, col2):
        from reference import reference

        if col1 == 0:
            for row in range(row1, row2):
                reference(self.table.cell(row + 1, 0), "text").monitors.add(self.update_handler)

        if row1 == 0:
            for column in range(col1, col2):
                reference(self.table.cell(0, column + 1), "text").monitors.add(self.update_handler)

        for row in range(row1, row2):
            for column in range(col1, col2):
                reference(self.table.cell(row + 1, column + 1), "text").monitors.add(self.update_handler)
                reference(self.table.cell(row + 1, column + 1), "background_color").monitors.add(self.update_handler)

    @property
    def update_handler(self):
        from handler import handler
        return handler(self.handle_update)

    def handle_update(self, event):
        wx.CallAfter(self.HandleUpdate, event)

    def HandleUpdate(self, event):
        from reference import reference
        if event.reference == reference(self.table, "n_rows"):
            n_rows = event.value - 1
            self.SetNRowsComplete(n_rows)
        if event.reference == reference(self.table, "n_columns"):
            n_columns = event.value - 1
            self.SetNColumnsComplete(n_columns)

        if event.reference.attribute_name == "text":
            if hasattr(event.reference.object, "row") and hasattr(event.reference.object, "column"):
                if event.reference.object.column == 0:
                    row = event.reference.object.row - 1
                    text = event.value
                    self.SetRowLabelText(row, text)
                elif event.reference.object.row == 0:
                    column = event.reference.object.column - 1
                    text = event.value
                    self.SetColumnLabelText(column, text)
                else:
                    events = self.text_events
                    row = event.reference.object.row - 1
                    column = event.reference.object.column - 1
                    last_event = events[row, column]
                    events[row, column] = event

                    if event.time >= last_event.time:
                        text = event.value
                        self.SetCellText(row, column, text)

                    if event.time < last_event.time:
                        logging.info(f"{self}: Events out order: Text: Ignoring {event.value!r}, {last_event.time-event.time:.9f} s older than {last_event.value!r}, for cell {event.reference.object.row}, {event.reference.object.column}")
                    if event.time == last_event.time and event.value != last_event.value:
                        logging.warning(f"{self}: Conflict: Text: {event.value!r} versus {last_event.value!r} for cell {event.reference.object.row},{event.reference.object.column}")
                    if event.time == last_event.time and event.value == last_event.value:
                        logging.debug(f"{self}: Duplicate event: Text: {event.value!r} for cell {event.reference.object.row},{event.reference.object.column}")

        if event.reference.attribute_name == "background_color":
            if hasattr(event.reference.object, "row") and hasattr(event.reference.object, "column"):
                events = self.background_color_events
                row = event.reference.object.row - 1
                column = event.reference.object.column - 1
                last_event = events[row, column]
                events[row, column] = event

                if event.time >= last_event.time:
                    color = event.value
                    self.SetCellBackgroundColor(row, column, color)

                if event.time < last_event.time:
                    logging.info(f"{self}: Events out order: Background color: Ignoring {event.value!r}, {last_event.time-event.time:.9f} s older than {last_event.value!r}, for cell {event.reference.object.row},{event.reference.object.column}")
                if event.time == last_event.time and event.value != last_event.value:
                    logging.warning(f"{self}: Conflict: Background color: {event.value!r} versus {last_event.value!r} for cell {event.reference.object.row},{event.reference.object.column}")
                if event.time == last_event.time and event.value == last_event.value:
                    logging.debug(f"{self}: Duplicate event: Background color: {event.value!r} for cell {event.reference.object.row},{event.reference.object.column}")

    def SetRowLabelText(self, row, value):
        if 0 <= row < self.NumberRows:
            self.SetRowLabelValue(row, value)

    def SetColumnLabelText(self, column, value):
        if 0 <= column < self.NumberCols:
            self.SetColLabelValue(column, value)

    def SetCellText(self, row, column, text):
        if type(text) != str:
            logging.warning(f"{self}: Cell({row}, {row}): {text!r}: expecting str")
            text = ""
        if 0 <= row < self.NumberRows and 0 <= column < self.NumberCols:
            if self.GetCellValue(row, column) != text:
                self.SetCellValue(row, column, text)

    def SetCellBackgroundColor(self, row, column, color):
        # logging.debug(f"{row}, {column}, {color}")
        if 0 <= row < self.NumberRows and 0 <= column < self.NumberCols:
            if self.GetCellBackgroundColour(row, column) != color:
                self.SetCellBackgroundColour(row, column, color)
                if self.GetCellBackgroundColour(row, column) != self.DefaultCellBackgroundColour:
                    from Spreadsheet_Cell_Renderer import Spreadsheet_Cell_Renderer
                    # logging.debug(f"{row}, {column}: Need custom renderer")
                    self.SetCellRenderer(row, column, Spreadsheet_Cell_Renderer())
                else:
                    default_renderer = self.GetDefaultRendererForType(wx.grid.GRID_VALUE_TEXT)
                    if self.GetCellRenderer(row, column) != default_renderer:
                        # logging.debug(f"{row}, {column}: Resetting to default renderer")
                        self.SetCellRenderer(row, column, default_renderer)
                self.refresh_delayed()

    def refresh_delayed(self):
        self.refreshing_delayed = True

    @thread_property
    def refreshing_delayed(self):
        from time import sleep
        sleep(0.2)
        # logging.debug("Refresh")
        wx.CallAfter(self.Refresh)

    def force_cell_refresh(self, column, row):
        text = self.GetCellValue(row, column)
        self.SetCellValue(row, column, text + " ")
        self.SetCellValue(row, column, text)

    def set_cell_choices(self, row, column, choices):
        if 0 <= row < self.NumberRows and 0 <= column < self.NumberCols:
            if choices:
                typeName = wx.grid.GRID_VALUE_CHOICE + ":" + ",".join(choices)
                # logging.debug(f"{row}, {column}, {typeName}")
            else:
                typeName = wx.grid.GRID_VALUE_STRING
            editor = self.GetDefaultEditorForType(typeName)
            if self.GetCellEditor(row, column) != editor:
                self.SetCellEditor(row, column, editor)

    def SetNRows(self, n_rows):
        if n_rows > self.NumberRows:
            self.AppendRows(n_rows - self.NumberRows)
        elif n_rows < self.NumberRows:
            self.DeleteRows(n_rows, self.NumberRows - n_rows)

    def SetNColumns(self, n_columns):
        if n_columns > self.NumberCols:
            self.AppendCols(n_columns - self.NumberCols)
        elif n_columns < self.NumberCols:
            self.DeleteCols(n_columns, self.NumberCols - n_columns)

    def SetNRowsComplete(self, n_rows):
        n_rows_old = self.NumberRows
        logging.debug(f"Changing number of rows from {n_rows_old} to {n_rows}")
        self.SetNRows(n_rows)
        if n_rows > n_rows_old:
            self.initialize_cells(n_rows_old, n_rows, 0, self.NumberCols)
            self.monitor_cells(n_rows_old, n_rows, 0, self.NumberCols)
        self.RefreshLayout()

    def SetNColumnsComplete(self, n_columns):
        n_columns_old = self.NumberCols
        if n_columns != n_columns_old:
            logging.debug(f"Changing number of columns from {n_columns_old} to {n_columns}")
            self.SetNColumns(n_columns)
            if n_columns > n_columns_old:
                self.initialize_cells(0, self.NumberRows, n_columns_old, n_columns)
                self.monitor_cells(0, self.NumberRows, n_columns_old, n_columns)
            self.RefreshLayout()

    def SetNColumnsCompleteAsync(self, n_columns):
        n_columns_old = self.NumberCols
        if n_columns != n_columns_old:
            logging.debug(f"Changing number of columns from {n_columns_old} to {n_columns}")
            self.SetNColumns(n_columns)
            if n_columns > n_columns_old:
                self.set_n_columns_complete_stage_2(n_columns_old, n_columns)

    @run_async
    def set_n_columns_complete_stage_2(self, n_columns_old, n_columns):
        if n_columns > n_columns_old:
            self.initialize_cells(0, self.NumberRows, n_columns_old, n_columns)
            self.monitor_cells(0, self.NumberRows, n_columns_old, n_columns)

    def RefreshLayout(self):
        # logging.debug("Forcing refresh")
        self.Parent.Layout()

    def OnLabelRightClick(self, event):
        event.Skip()
        if event.Row != -1:
            if event.Row not in self.SelectedRows:
                self.ClearSelection()
                self.SelectRow(event.Row)
            self.ShowRowMenu()
        if event.Col != -1:
            if event.Col not in self.SelectedCols:
                self.ClearSelection()
                self.SelectCol(event.Col)
            self.ShowColumnMenu()

    def OnRightClick(self, event):
        # logging.debug(f"RightClick: row {event.Row}, column {event.Col}")
        event.Skip()
        if event.Row != -1:
            if event.Row not in self.SelectedRows:
                self.ClearSelection()
                self.SelectRow(event.Row)
            self.ShowRowMenu()
        self.ShowRowMenu()

    def OnCellChanged(self, event):
        row, column = event.Row, event.Col
        value = self.GetCellValue(row, column)
        event.Skip()  # Call default handler (needed?)
        old_value = self.table.cell(row+1, column+1).text
        logging.debug(f"{self}: Cell {row}, {column}: Changing from {old_value!r} to {value!r}")
        self.SetCellValue(row, column, old_value)
        self.table.cell(row+1, column+1).text = value

    def OnLeftClick(self, event):
        row, column = event.Row, event.Col
        # logging.debug(f"{self}: Cell {row}, {column}")
        choices = self.table.cell(row + 1, column + 1).choices
        self.set_cell_choices(row, column, choices)
        event.Skip()  # Call default handler (needed?)

    ID_CUT = 1
    ID_COPY = 2
    ID_PASTE = 3
    ID_INSERT = 4
    ID_INSERT_COPIED_CELLS = 5
    ID_DUPLICATE = 6
    ID_DELETE = 7

    def ShowRowMenu(self):
        menu = self.RowMenu
        self.PopupMenu(menu)
        menu.Destroy()

    @property
    def RowMenu(self):
        menu = wx.Menu()
        if len(self.SelectedRows) == 1:
            selected_row = self.SelectedRows[0]
            row_menu_items = self.table.row_menu_items(selected_row + 1)
            if row_menu_items:
                self.menu_item_handlers = {}
                item_id = 2100
                for menu_item in row_menu_items:
                    menu.Append(item_id, menu_item.label)
                    menu.Enable(item_id, menu_item.enabled)
                    self.menu_item_handlers[item_id] = menu_item.handler
                    self.Bind(wx.EVT_MENU, self.OnMenuItem, id=item_id)
                    item_id += 1
            menu.AppendSeparator()
        label = "Cu&t Row\tCtrl+X"
        if len(self.SelectedRows) > 1:
            label = label.replace("Row", "Rows")
        menu.Append(self.ID_CUT, label)
        self.Bind(wx.EVT_MENU, self.OnCutRow, id=self.ID_CUT)
        menu.Enable(self.ID_CUT, self.IsSelection())
        label = "&Copy Row\tCtrl+C"
        if len(self.SelectedRows) > 1:
            label = label.replace("Row", "Rows")
        menu.Append(self.ID_COPY, label)
        self.Bind(wx.EVT_MENU, self.OnCopyRow, id=self.ID_COPY)
        menu.Enable(self.ID_COPY, self.IsSelection())
        label = "&Paste Row\tCtrl+V"
        if len(self.ClipboardText.splitlines()) > 1:
            label = label.replace("Row", "Rows")
        menu.Append(self.ID_PASTE, label)
        self.Bind(wx.EVT_MENU, self.OnPasteRow, id=self.ID_PASTE)
        menu.Enable(self.ID_PASTE, len(self.ClipboardText) > 0)
        menu.AppendSeparator()
        label = "Insert Row"
        if len(self.SelectedRows) > 1:
            label = label.replace("Row", "Rows")
        menu.Append(self.ID_INSERT, label)
        menu.Enable(self.ID_INSERT, len(self.SelectedRows) > 0)
        self.Bind(wx.EVT_MENU, self.OnInsertRow, id=self.ID_INSERT)
        label = "Insert Row from Clipboard"
        if len(self.ClipboardText.splitlines()) > 1:
            label = label.replace("Row", "Rows")
        menu.Append(self.ID_INSERT_COPIED_CELLS, label)
        menu.Enable(self.ID_INSERT_COPIED_CELLS, len(self.ClipboardText) > 0)
        self.Bind(wx.EVT_MENU, self.OnInsertCopiedRows, id=self.ID_INSERT_COPIED_CELLS)
        label = "Duplicate Row"
        if len(self.SelectedRows) > 1:
            label = label.replace("Row", "Rows")
        menu.Append(self.ID_DUPLICATE, label)
        menu.Enable(self.ID_DUPLICATE, len(self.SelectedRows) > 0)
        self.Bind(wx.EVT_MENU, self.OnDuplicateRow, id=self.ID_DUPLICATE)
        label = "&Delete Row\tDel"
        if len(self.SelectedRows) > 1:
            label = label.replace("Row", "Rows")
        menu.Append(self.ID_DELETE, label)
        menu.Enable(self.ID_DELETE, len(self.SelectedRows) > 0)
        self.Bind(wx.EVT_MENU, self.OnDeleteRow, id=self.ID_DELETE)
        return menu

    def ShowColumnMenu(self):
        menu = self.ColumnMenu
        self.PopupMenu(menu)
        menu.Destroy()

    @property
    def ColumnMenu(self):
        menu = wx.Menu()

        if len(self.SelectedCols) == 1:
            selected_column = self.SelectedCols[0]
            column_menu_items = self.table.column_menu_items(selected_column + 1)
            if column_menu_items:
                self.menu_item_handlers = {}
                item_id = 2100
                for menu_item in column_menu_items:
                    menu.Append(item_id, menu_item.label)
                    menu.Enable(item_id, menu_item.enabled)
                    self.menu_item_handlers[item_id] = menu_item.handler
                    self.Bind(wx.EVT_MENU, self.OnMenuItem, id=item_id)
                    item_id += 1
            menu.AppendSeparator()

        ID = 1
        menu.Append(ID, "Sort by this Column")
        self.Bind(wx.EVT_MENU, self.OnSort, id=ID)
        return menu

    def OnMenuItem(self, event):
        if event.Id in self.menu_item_handlers:
            handler = self.menu_item_handlers[event.Id]
            logging.debug(f"Calling {handler}")
            handler()
        else:
            logging.error(f"{event.Id} not in {self.menu_item_handlers}")

    def OnCut(self, _event):
        selected_text = self.selected_text
        logging.debug(f"{self}: Cut {selected_text!r}")
        self.ClipboardText = selected_text
        self.ClearSelectedCells()
        self.update_table()

    def OnCopy(self, _event):
        selected_text = self.selected_text
        logging.debug(f"{self}: Copy {selected_text!r}")
        self.ClipboardText = selected_text

    def OnPaste(self, _event):
        logging.debug(f"{self}: Paste")
        row1, column1 = None, None
        if self.SelectionBlockTopLeft:
            row1, column1 = self.SelectionBlockTopLeft[0]
        elif self.GridCursorRow >= 0 and self.GridCursorCol >= 0:
            row1, column1 = self.GridCursorRow, self.GridCursorCol
        if row1 is not None and column1 is not None:
            for row_offset, line in enumerate(self.ClipboardText.splitlines()):
                row = row1 + row_offset
                for column_offset, text in enumerate(line.split("\t")):
                    column = column1 + column_offset
                    logging.debug(f"Pasting {text!r} to cell {row}, {column}")
                    self.SetCellText(row, column, text)
            self.update_table()

    def OnDelete(self, _event):
        logging.debug(f"{self}: Delete")
        self.ClearSelectedCells()
        self.update_table()

    def OnSelectAll(self, _event):
        logging.debug(f"{self}: select_all")
        self.SelectAll()

    def OnCutRow(self, _event):
        if self.SelectedRows:
            self.ClipboardText = self.selected_rows_text
            self.DeleteRows(self.SelectedRows[0], len(self.SelectedRows))
            self.update_table()

    def OnCopyRow(self, _event):
        logging.debug(f"{self}: Copy row {self.selected_rows_text!r}")
        self.ClipboardText = self.selected_rows_text

    def OnPasteRow(self, _event):
        if self.SelectedRows:
            for row_offset, line in enumerate(self.ClipboardText.splitlines()):
                row = self.SelectedRows[0] + row_offset
                for column, text in enumerate(line.split("\t")):
                    self.SetCellText(row, column, text)
            self.update_table()

    @property
    def selected_text(self):
        lines = []
        for row_cells in self.AllSelectedCells:
            lines.append("\t".join(row_cells))
        text = "\n".join(lines)
        return text

    @property
    def selected_rows_text(self):
        lines = []
        for row_cells in self.SelectedRowsCells:
            lines.append("\t".join(row_cells))
        text = "\n".join(lines)
        return text

    @property
    def Cells(self):
        cells = []
        for row in range(0, self.NumberRows):
            row_cells = []
            for column in range(0, self.NumberCols):
                row_cells.append(self.GetCellValue(row, column))
            cells.append(row_cells)
        return cells

    @Cells.setter
    def Cells(self, cells):
        for row, row_cells in enumerate(cells):
            for column, value in enumerate(row_cells):
                self.SetCellText(row, column, value)

    @property
    def AllSelectedCells(self):
        selected_cells = []
        if self.SelectionBlockTopLeft and self.SelectionBlockBottomRight:
            for top_left, bottom_right in zip(self.SelectionBlockTopLeft, self.SelectionBlockBottomRight):
                row1, column1 = top_left
                row2, column2 = bottom_right
                for row in range(row1, row2 + 1):
                    row_cells = []
                    for column in range(column1, column2 + 1):
                        row_cells.append(self.GetCellValue(row, column))
                    if row_cells:
                        selected_cells.append(row_cells)
            logging.debug(f"Selected cells{selected_cells}")
        else:
            row, column = self.GridCursorRow, self.GridCursorCol
            if row >= 0 and column >= 0:
                row_cells = [self.GetCellValue(row, column)]
                selected_cells.append(row_cells)
        return selected_cells

    def ClearSelectedCells(self):
        if self.SelectionBlockTopLeft and self.SelectionBlockBottomRight:
            for top_left, bottom_right in zip(self.SelectionBlockTopLeft, self.SelectionBlockBottomRight):
                row1, column1 = top_left
                row2, column2 = bottom_right
                for row in range(row1, row2 + 1):
                    for column in range(column1, column2 + 1):
                        self.SetCellValue(row, column, "")
        else:
            row, column = self.GridCursorRow, self.GridCursorCol
            if row >= 0 and column >= 0:
                self.SetCellValue(row, column, "")

    @property
    def SelectedRowsCells(self):
        cells = []
        for row in self.SelectedRows:
            row_cells = []
            for column in range(0, self.NumberCols):
                row_cells.append(self.GetCellValue(row, column))
            cells.append(row_cells)
        return cells

    @property
    def SelectedColumnsCells(self):
        cells = []
        if self.SelectedCols:
            for row in range(0, self.NumberRows):
                row_cells = []
                for column in self.SelectedCols:
                    row_cells.append(self.GetCellValue(row, column))
                cells.append(row_cells)
        return cells

    def OnInsertRow(self, _event):
        if self.SelectedRows:
            self.InsertRows(self.SelectedRows[0], len(self.SelectedRows))
        self.update_table()

    def OnInsertCopiedRows(self, _event):
        if self.SelectedRows:
            n_rows_insert = len(self.ClipboardText.splitlines())
            self.InsertRows(self.SelectedRows[0], n_rows_insert)
            starting_row = self.SelectedRows[0] - n_rows_insert
            for row_offset, line in enumerate(self.ClipboardText.splitlines()):
                row = starting_row + row_offset
                for column, text in enumerate(line.split("\t")):
                    self.SetCellText(row, column, text)
            self.update_table()

    def OnDuplicateRow(self, _event):
        if self.SelectedRows:
            cells_to_duplicate = self.SelectedRowsCells
            n_rows_insert = len(self.SelectedRows)
            self.InsertRows(self.SelectedRows[0], len(self.SelectedRows))
            starting_row = self.SelectedRows[0] - n_rows_insert
            for row_offset, row_cells in enumerate(cells_to_duplicate):
                row = starting_row + row_offset
                for column, text in enumerate(row_cells):
                    self.SetCellText(row, column, text)
            self.update_table()

    def OnDeleteRow(self, _event):
        if self.SelectedRows:
            self.DeleteRows(self.SelectedRows[0], len(self.SelectedRows))
            self.update_table()

    def OnSort(self, _event):
        if self.SelectedCols:
            logging.debug(f"{self}: Sorting by columns {self.SelectedCols}")
            self.Cells = self.reordered(self.Cells, self.sort_order)
            self.update_table()

    @staticmethod
    def reordered(values, order):
        from numpy import array
        return array(values)[order].tolist()

    @property
    def sort_order(self):
        from natural_order import natural_order
        cells = self.SelectedColumnsCells
        if cells:
            order = natural_order(cells)
        else:
            order = []
        return order

    @property
    def ClipboardText(self):
        text = ""
        data_object = wx.TextDataObject()
        if wx.TheClipboard.Open():
            success = wx.TheClipboard.GetData(data_object)
            wx.TheClipboard.Close()
            if success:
                text = data_object.Text
        # Remove empty lines (needed for Excel on MacOS)
        while "\n\n" in text:
            text = text.replace("\n\n","\n")
        return text

    @ClipboardText.setter
    def ClipboardText(self, text):
        if wx.TheClipboard.Open():
            logging.debug(f"Putting in clipboard: {text!r}")
            wx.TheClipboard.SetData(wx.TextDataObject(text))
            wx.TheClipboard.Close()
        else:
            logging.error("Failed update clipboard")


if __name__ == '__main__':
    from Control_Panel import Control_Panel

    # name = "BioCARS.sequence_modes"
    # name = "BioCARS.detector_configuration"
    name = "BioCARS.method"

    domain_name, base_name = name.split(".", 1)

    from redirect import redirect

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    redirect(f"{domain_name}.Spreadsheet.{name}", format=msg_format, level="DEBUG")

    app = wx.GetApp() if wx.GetApp() else wx.App()
    self = Control_Panel(name, panel_type=Spreadsheet)
    app.MainLoop()
