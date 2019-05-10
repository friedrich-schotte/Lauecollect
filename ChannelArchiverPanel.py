#!/usr/bin/env python
"""
Archive EPICS process variable via Channel Access
Author: Friedrich Schotte
Date created: 10/4/2017
Date last modified: 11/2/2017
"""
__version__ = "1.0.2" # wx 4.0

import wx,wx3_compatibility
from logging import debug,info,warn,error
from channel_archiver import channel_archiver
from EditableControls import TextCtrl

class ChannelArchiverPanel(wx.Frame):
    name = "ChannelArchiver"
    def __init__ (self,parent=None):
        wx.Frame.__init__(self,parent=parent,title="Channel Archiver")
        from Icon import SetIcon
        SetIcon(self,"Archiver")

        self.panel = wx.Panel(self)

        border = wx.BoxSizer(wx.VERTICAL)

        flag = wx.ALL|wx.EXPAND
        box = wx.BoxSizer(wx.VERTICAL)        
        from wx import grid
        self.Table = grid.Grid(self.panel)
        nrows = max(len(self.PVs),1)
        self.Table.CreateGrid(nrows,4)
        self.Table.SetRowLabelSize(20) # 1,2,...
        self.Table.SetColLabelSize(20) 
        self.Table.SetColLabelValue(0,"Log")
        self.Table.SetColLabelValue(1,"Description")
        self.Table.SetColLabelValue(2,"Process Variable")
        self.Table.SetColLabelValue(3,"Value")
        
        for i in range(0,min(nrows,len(self.PVs))):
            if i<len(self.PVsuse) and self.PVsuse[i]: text = "Yes"
            else: text = "No"
            self.Table.SetCellValue(i,0,text)
            if i<len(self.PVnames):
                self.Table.SetCellValue(i,1,self.PVnames[i])
            self.Table.SetCellValue(i,2,self.PVs[i])

        self.Table.AutoSize()
        self.Bind(wx.grid.EVT_GRID_CELL_CHANGE,self.OnEnterCell,self.Table)
        self.Bind(wx.grid.EVT_GRID_SELECT_CELL,self.OnSelectCell,self.Table)
        box.Add (self.Table,flag=flag,proportion=1) 

        buttons = wx.BoxSizer()
        button = wx.Button(self.panel,label="+",style=wx.BU_EXACTFIT)
        self.Bind(wx.EVT_BUTTON,self.add_row,button)
        buttons.Add (button,flag=flag) 
        size = button.GetSize()
        button = wx.Button(self.panel,label="-",size=size)
        self.Bind(wx.EVT_BUTTON,self.delete_row,button)
        buttons.Add (button,flag=flag) 
        box.Add (buttons,flag=flag)

        # Leave a 10-pixel wide space around the panel.
        border.Add (box,flag=flag,border=10,proportion=1)

        flag = wx.ALL|wx.EXPAND
        group = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self,label="Destination:")
        group.Add (label,flag=flag)
        style = wx.TE_PROCESS_ENTER
        self.Directory = TextCtrl(self.panel,size=(250,-1),style=style)
        self.Directory.Value = channel_archiver.directory
        self.Bind(wx.EVT_TEXT_ENTER,self.OnDirectory,self.Directory)
        group.Add (self.Directory,flag=flag,proportion=1)
        button = wx.Button(self.panel,label="Browse...")
        self.Bind(wx.EVT_BUTTON,self.OnBrowse,button)
        group.Add (button,flag=flag)
        # Leave a 10-pixel wide space around the panel.
        flag = wx.ALL|wx.EXPAND
        border.Add (group,flag=flag,border=10)

        buttons = wx.BoxSizer()
        button = wx.ToggleButton(self.panel,label="Active")
        self.Bind(wx.EVT_TOGGLEBUTTON,self.OnActive,button)
        buttons.Add (button,flag=flag)
        buttons.AddSpacer((10,10))
        button = wx.Button(self.panel,label="Test")
        self.Bind(wx.EVT_BUTTON,self.test,button)
        buttons.Add (button,flag=flag) 
        # Leave a 10-pixel wide space around the panel.
        border.Add (buttons,flag=flag,border=10)
        
        self.panel.Sizer = border
        self.panel.Fit()
        self.Fit()
        self.Show()

        self.Bind(wx.EVT_SIZE,self.OnResize)

    def OnResize(self,event):
        self.update_layout()
        event.Skip() # call default handler

    def update_layout(self):
        """Resize componenets"""
        self.Table.AutoSize()
        self.panel.Fit()
        self.Fit()        

    def add_row(self,event):
        """Add one more row at the end of the table"""
        self.Table.AppendRows(1)
        self.Table.AutoSize()
        self.update_layout()

    def delete_row(self,event):
        """"Remove the last row of the table"""
        n = self.Table.GetNumberRows()
        self.Table.DeleteRows(n-1,1)
        self.Table.AutoSize()
        self.update_layout()

    def OnDirectory(self,event):
        """Set destination folder for archive"""
        debug("channel_archiver.directory = %r" % str(self.Directory.Value))
        channel_archiver.directory = str(self.Directory.Value)
        
    def OnBrowse(self,event):
        """Set destination folder for archive"""
        from os.path import exists,dirname
        from normpath import normpath
        pathname = channel_archiver.directory
        while pathname and not exists(pathname): pathname = dirname(pathname)
        dlg = wx.DirDialog(self, "Choose a directory:",style=wx.DD_DEFAULT_STYLE)
        # ShowModal pops up a dialog box and returns control only after the user
        # has selects OK or Cancel.
        dlg.Path = pathname
        if dlg.ShowModal() == wx.ID_OK:
            self.Directory.Value = normpath(str(dlg.Path))
        dlg.Destroy()
        debug("channel_archiver.directory = %r" % str(self.Directory.Value))
        channel_archiver.directory = str(self.Directory.Value)

    def OnActive(self,event):
        """Start/stop archiving"""
        ##debug("channel_archiver.running = %r" % event.IsChecked())
        channel_archiver.running = event.IsChecked()

    def OnSelectCell(self,event):
        """Show Options"""
        debug("Select")

    def OnEnterCell(self,event):
        """Accept current values"""
        PVsuse = []
        PVnames = []
        PVs = []
        for i in range (0,self.Table.GetNumberRows()):
            PVuse = (self.Table.GetCellValue(i,0).lower() == "yes")
            PVname = str(self.Table.GetCellValue(i,1))
            PV = str(self.Table.GetCellValue(i,2))
            if PV:
                PVsuse += [PVuse]
                PVnames += [PVname]
                PVs += [PV]
        self.PVsuse = PVsuse
        self.PVnames = PVnames
        self.PVs = PVs

    def test(self,event):
        """Check if PVs are working b yreading their current value"""
        from CA import caget
        for i in range (0,self.Table.GetNumberRows()):
            enabled = self.Table.GetCellValue(i,0) == "Yes"
            PV = str(self.Table.GetCellValue(i,2))
            value = str(caget(PV)) if (PV and enabled) else ""
            self.Table.SetCellValue(i,3,value)
        self.update_layout()

    def get_PVs(self):
        self.update_known_PVs()
        return self.known_PVs
    def set_PVs(self,PVs):
        self.known_PVs = PVs
        ##debug("known_PVs = %r" % self.known_PVs)
    PVs = property(get_PVs,set_PVs)

    def get_PVsuse(self):
        active_PVs = channel_archiver.PVs
        use = [PV in active_PVs for PV in self.known_PVs]
        return use
    def set_PVsuse(self,use_list):
        PVs = [PV for (PV,use) in zip(self.known_PVs,use_list) if use]
        channel_archiver.PVs = PVs
        debug("channel_archiver.PVs = %r" % channel_archiver.PVs)
    PVsuse = property(get_PVsuse,set_PVsuse)

    def get_PVnames(self):
        names = [self.names[PV] if PV in self.names else ""
            for PV in self.PVs]
        return names
    def set_PVnames(self,names):
        PV_names = self.names
        for PV,name in zip(self.PVs,names):
            PV_names[PV] = name
        self.names = PV_names
        ##debug("names = %r" % self.names)
    PVnames = property(get_PVnames,set_PVnames)

    from persistent_property import persistent_property
    names = persistent_property("names",{})
    known_PVs = persistent_property("known_PVs",[])

    def update_known_PVs(self):
        known_PVs = self.known_PVs
        for PV in channel_archiver.PVs:
            if not PV in known_PVs: known_PVs += [PV]
        self.known_PVs = known_PVs        

  
if __name__ == "__main__": # for testing
    from pdb import pm # for debugging
    import logging # for debugging
    from tempfile import gettempdir
    logfile = gettempdir()+"/ChannelArchiverPanel.log"
    logging.basicConfig(level=logging.DEBUG,
        filename=logfile,
        format="%(asctime)s %(levelname)s: %(message)s")
    app = wx.App(redirect=False) 
    panel = ChannelArchiverPanel()
    app.MainLoop()
