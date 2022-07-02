"""
Render selected cells differently according to their background color
Usage:

import wx.grid
grid = wx.grid.Grid(parent)
grid.CreateGrid(1, 1)
grid.SetCellRenderer(0, 0, Spreadsheet_Cell_Renderer())

Author: Friedrich Schotte
Date created: 2022-06-01
Date last modified: 2022-06-20
Revision comment:
"""
__version__ = "1.0"

import logging

import wx
import wx.grid


class Spreadsheet_Cell_Renderer(wx.grid.GridCellRenderer):
    def __init__(self):
        """Render data in the specified color and font and fontsize"""
        wx.grid.GridCellRenderer.__init__(self)

    # Based on wxPython-demo-4.0.6/demo/Grid_MegaExample.py, class MegaFontRenderer (2019-05-21)
    def Draw(self, grid, attr, dc, rect, row, col, isSelected):
        from color import mix_colors, lightened_color
        # Set clipping region, otherwise the text spills over to the next cell
        dc.SetClippingRegion(rect)

        background_color = lightened_color(attr.BackgroundColour, 0.5)

        if isSelected:
            background_color = mix_colors(grid.SelectionBackground, background_color)

        # Fill background
        dc.SetBackgroundMode(wx.BRUSHSTYLE_SOLID)
        dc.SetBrush(wx.Brush(background_color, wx.BRUSHSTYLE_SOLID))
        dc.SetPen(wx.Pen(background_color, 1, wx.PENSTYLE_SOLID))
        dc.DrawRectangle(rect)

        # Render text
        text = grid.GetCellValue(row, col)
        dc.SetFont(attr.Font)
        dc.SetTextBackground(background_color)
        dc.SetTextForeground(attr.TextColour)
        dc.DrawText(text, rect.x + 1, rect.y + 1)

        dc.DestroyClippingRegion()


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    app = wx.GetApp() if wx.GetApp() else wx.App()
    parent = wx.Frame(None)
    grid = wx.grid.Grid(parent)
    grid.CreateGrid(2, 2)
    grid.SetCellBackgroundColour(0, 0, [128, 255, 128])
    grid.SetCellBackgroundColour(0, 1, [128, 255, 128])
    grid.SetCellValue(0, 0, "00")
    grid.SetCellValue(0, 1, "01")
    grid.SetCellValue(1, 0, "10")
    grid.SetCellValue(1, 1, "11")
    grid.SetCellRenderer(0, 0, Spreadsheet_Cell_Renderer())
    grid.SetCellRenderer(1, 0, Spreadsheet_Cell_Renderer())
    parent.Show()
    print("app.MainLoop()")
