"""
wxPython: TextCtrl doesn't ever receive focus when inside a panel inside
another panel inside a frame

http://stackoverflow.com/questions/10048564/wxpython-textctrl-doesnt-ever-receive-focus-when-inside-a-panel-inside-another

So I have the following code set up to demonstrate the problem:
"""

import wx


class testPanel(wx.Panel):
    def __init__(self, parent):
        super(testPanel, self).__init__(parent)
        self.hsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.txt = wx.TextCtrl(self, style=wx.TE_MULTILINE)

        self.hsizer.Add(self.txt, proportion=1,
            flag=wx.EXPAND)
        self.SetSizer(self.hsizer)

        self.hsizer.Fit(self)
        self.Show(True)


class testFrame(wx.Frame):
    def __init__(self, parent):
        super(testFrame, self).__init__(parent)
        self.mainPanel = wx.Panel(self)
        self.vsizer = wx.BoxSizer(wx.VERTICAL)

        ##self.txt1 = testPanel(self)
        ##self.txt2 = testPanel(self)
        # Use:
        self.txt1 = testPanel(self.mainPanel)
        self.txt2 = testPanel(self.mainPanel)
        # and they will get focus.

        self.vsizer.Add(self.txt1, proportion=1,
            flag=wx.EXPAND)
        self.vsizer.Add(self.txt2, proportion=1,
            flag=wx.EXPAND)
        self.mainPanel.SetSizer(self.vsizer)

        self.vsizer.Fit(self.mainPanel)

        self.mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.mainSizer.Add(self.mainPanel, proportion=1,
            flag=wx.EXPAND)
        self.SetSizer(self.mainSizer)
        self.mainSizer.Fit(self)

        self.Show(True)

app = wx.PySimpleApp()
frame = testFrame(None)
frame.Show(True)
app.MainLoop()
