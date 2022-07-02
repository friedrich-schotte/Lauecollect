#!/usr/bin/env python
"""
Based on Samples/demo/GridCustTable.py
Author: Friedrich Schotte
Date created: 2019-06-20
Date last modified: 2019-06-20
"""
__version__ = "1.0"  
from logging import debug,info,warn,error

import  wx
import  wx.grid as gridlib

class TableGrid(gridlib.Grid):
    def __init__(self,parent):
        gridlib.Grid.__init__(self, parent, -1)

        table = GridTable()

        # The second parameter means that the grid is to take ownership of the
        # table and will destroy it when done.  Otherwise you would need to keep
        # a reference to it and call it's Destroy method later.
        self.SetTable(table, True)

        self.SetRowLabelSize(0)
        self.SetMargins(0,0)
        self.AutoSizeColumns(False)

        gridlib.EVT_GRID_CELL_LEFT_DCLICK(self, self.OnLeftDClick)

    # I do this because I don't like the default behaviour of not starting the
    # cell editor on double clicks, but only a second click.
    def OnLeftDClick(self, evt):
        if self.CanEnableCellControl():
            self.EnableCellEditControl()


class GridTable(gridlib.PyGridTableBase):
    def __init__(self):
        gridlib.PyGridTableBase.__init__(self)
        import sys
        self.log = sys.stdout

        self.colLabels = ['ID', 'Description', 'Severity', 'Priority', 'Platform',
                          'Opened?', 'Fixed?', 'Tested?', 'TestFloat']

        self.dataTypes = [gridlib.GRID_VALUE_NUMBER,
                          gridlib.GRID_VALUE_STRING,
                          gridlib.GRID_VALUE_CHOICE + ':only in a million years!,wish list,minor,normal,major,critical',
                          gridlib.GRID_VALUE_NUMBER + ':1,5',
                          gridlib.GRID_VALUE_CHOICE + ':all,MSW,GTK,other',
                          gridlib.GRID_VALUE_BOOL,
                          gridlib.GRID_VALUE_BOOL,
                          gridlib.GRID_VALUE_BOOL,
                          gridlib.GRID_VALUE_FLOAT + ':6,2',
                          ]

        self.data = [
            [1010, "The foo doesn't bar", "major", 1, 'MSW', 1, 1, 1, 1.12],
            [1011, "I've got a wicket in my wocket", "wish list", 2, 'other', 0, 0, 0, 1.50],
            [1012, "Rectangle() returns a triangle", "critical", 5, 'all', 0, 0, 0, 1.56]

            ]

    def GetNumberRows(self):
        return len(self.data) + 1

    def GetNumberCols(self):
        return len(self.data[0])

    def IsEmptyCell(self, row, col):
        try:
            return not self.data[row][col]
        except IndexError:
            return True

    # Get/Set values in the table.  The Python version of these
    # methods can handle any data-type, (as long as the Editor and
    # Renderer understands the type too,) not just strings as in the
    # C++ version.
    def GetValue(self, row, col):
        try:
            return self.data[row][col]
        except IndexError:
            return ''

    def SetValue(self, row, col, value):
        def innerSetValue(row, col, value):
            try:
                self.data[row][col] = value
            except IndexError:
                # add a new row
                self.data.append([''] * self.GetNumberCols())
                innerSetValue(row, col, value)

                # tell the grid we've added a row
                msg = gridlib.GridTableMessage(self,            # The table
                        gridlib.GRIDTABLE_NOTIFY_ROWS_APPENDED, # what we did to it
                        1                                       # how many
                        )

                self.GetView().ProcessTableMessage(msg)
        innerSetValue(row, col, value) 

    # Called when the grid needs to display labels
    def GetColLabelValue(self, col):
        return self.colLabels[col]

    # Called to determine the kind of editor/renderer to use by
    # default, doesn't necessarily have to be the same type used
    # natively by the editor/renderer if they know how to convert.
    def GetTypeName(self, row, col):
        return self.dataTypes[col]

    # Called to determine how the data can be fetched and stored by the
    # editor and renderer.  This allows you to enforce some type-safety
    # in the grid.
    def CanGetValueAs(self, row, col, typeName):
        colType = self.dataTypes[col].split(':')[0]
        if typeName == colType:
            return True
        else:
            return False

    def CanSetValueAs(self, row, col, typeName):
        return self.CanGetValueAs(row, col, typeName)


if __name__ == '__main__':
    from pdb import pm
    from Control_Panel import Control_Panel
    class Test_Panel(Control_Panel):
        name = "Grid_Test_Panel"
        title = "Grid Test"

        @property
        def ControlPanel(self):
            from Controls import Control
            panel = wx.Panel(self)

            frame = wx.BoxSizer()
            panel.Sizer = frame
            layout = wx.BoxSizer(wx.VERTICAL)
            frame.Add(layout,flag=wx.EXPAND|wx.ALL,border=10,proportion=1)

            control = TableGrid(panel)
            layout.Add(control,flag=wx.ALIGN_CENTRE|wx.ALL,proportion=1)

            panel.Fit()
            return panel


    app = wx.App()
    panel = Test_Panel()
    app.MainLoop()
