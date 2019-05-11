"""
Plot Window
Friedrich Schotte, Hyun Sun Cho, NIH, 19 Dec 2007 - 5 Nov 2010

Usage example:
app=wx.App(False)
from numpy import *
data = 2.*pi*arange(200)/200.; data.shape = (100, 2); data[:,1] = sin(data[:,0])
Plot(data)
"""
import wx
from PyPlot import * # tweaked version of wx.lib.plot

__version__ = "1.2"

class Plot(wx.Frame):
    def __init__(self,data=[[0,0]],title="",xaxis="",yaxis=""):
        # WX requires that before the first window is dsiplayed an wx.App
        # object needs to be created first.
        if not hasattr(wx,"app"): wx.app = wx.PySimpleApp(redirect=False)

        wx.Frame.__init__(self,None,title="Plot",size=(600, 400))

        self.data = data
        self.title = title
        self.xaxis = xaxis
        self.yaxis = yaxis

        # Now Create the menu bar and items
        self.mainmenu = wx.MenuBar()

        menu = wx.Menu()
        menu.Append(203, 'Save Image As...', 'Save current plot as bitmap image')
        self.Bind(wx.EVT_MENU, self.OnSaveImage, id=203)
        menu.Append(204, 'Save Data As...', 'Save current plot')
        self.Bind(wx.EVT_MENU, self.OnSaveData, id=204)
        menu.AppendSeparator()
        menu.Append(200, 'Page Setup...', 'Setup the printer page')
        self.Bind(wx.EVT_MENU, self.OnFilePageSetup, id=200)        
        menu.Append(201, 'Print Preview...', 'Show the current plot on page')
        self.Bind(wx.EVT_MENU, self.OnFilePrintPreview, id=201)
        menu.Append(202, 'Print...', 'Print the current plot')
        self.Bind(wx.EVT_MENU, self.OnFilePrint, id=202)
        menu.AppendSeparator()
        menu.Append(205, 'E&xit', 'Closes this Window')
        self.Bind(wx.EVT_MENU, self.OnFileExit, id=205)
        self.mainmenu.Append(menu, '&File')

        menu = wx.Menu()
        menu.Append(206, '&Plot Data', 'Plot data')
        self.Bind(wx.EVT_MENU,self.OnPlotData, id=206)

        menu.Append(211, '&Redraw', 'Redraw plots')
        self.Bind(wx.EVT_MENU,self.OnPlotRedraw, id=211)
        menu.Append(212, '&Clear', 'Clear canvas')
        self.Bind(wx.EVT_MENU,self.OnPlotClear, id=212)
        menu.Append(213, '&Scale', 'Scale canvas')
        self.Bind(wx.EVT_MENU,self.OnPlotScale, id=213) 
        menu.Append(214, 'Enable &Zoom', 'Enable Mouse Zoom', kind=wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU,self.OnEnableZoom, id=214) 
        menu.Append(215, 'Enable &Grid', 'Turn on Grid', kind=wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU,self.OnEnableGrid, id=215)
        menu.Append(217, 'Enable &Drag', 'Activates dragging mode', kind=wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU,self.OnEnableDrag, id=217)
        menu.Append(220, 'Enable &Legend', 'Turn on Legend', kind=wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU,self.OnEnableLegend, id=220)
        menu.Append(222, 'Enable &Point Label', 'Show Closest Point', kind=wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU,self.OnEnablePointLabel, id=222)
       
        menu.Append(225, 'Scroll Up 1', 'Move View Up 1 Unit')
        self.Bind(wx.EVT_MENU,self.OnScrUp, id=225) 
        menu.Append(230, 'Scroll Rt 2', 'Move View Right 2 Units')
        self.Bind(wx.EVT_MENU,self.OnScrRt, id=230)
        menu.Append(235, '&Plot Reset', 'Reset to original plot')
        self.Bind(wx.EVT_MENU,self.OnReset, id=235)

        self.mainmenu.Append(menu, '&Plot')

        menu = wx.Menu()
        menu.Append(300, '&About', 'About this thing...')
        self.Bind(wx.EVT_MENU, self.OnHelpAbout, id=300)
        self.mainmenu.Append(menu, '&Help')

        self.SetMenuBar(self.mainmenu)

        # A status bar to tell people what's happening
        self.CreateStatusBar(1)
        
        self.client = PlotCanvas(self)
        #define the function for drawing pointLabels
        self.client.SetPointLabelFunc(self.DrawPointLabel)
        # Create mouse event for showing cursor coords in status bar
        self.client.canvas.Bind(wx.EVT_LEFT_DOWN, self.OnMouseLeftDown)
        # Show closest point when enabled
        self.client.canvas.Bind(wx.EVT_MOTION, self.OnMotion)

        # This is to store and retrieve persistent settings, preferences, etc.
        self.config = wx.FileConfig ("Plot")

        self.Show(True)

        # If data is passed plot it now.
        self.update()

    def update(self):
        self.resetDefaults()
        if self.data != None:
          lines = PolyLine(self.data,colour='red')
          markers = PolyMarker(self.data,marker='circle',size=0.5,colour='red')
          graph = PlotGraphics([lines,markers],self.title,self.xaxis,self.yaxis)
          self.client.Draw(graph)

    def DrawPointLabel(self, dc, mDataDict):
        """This is the fuction that defines how the pointLabels are plotted
            dc - DC that will be passed
            mDataDict - Dictionary of data that you want to use for the pointLabel

            As an example I have decided I want a box at the curve point
            with some text information about the curve plotted below.
            Any wxDC method can be used.
        """
        # ----------
        dc.SetPen(wx.Pen(wx.BLACK))
        dc.SetBrush(wx.Brush( wx.BLACK, wx.SOLID ) )
        
        sx, sy = mDataDict["scaledXY"] #scaled x,y of closest point
        dc.DrawRectangle( sx-5,sy-5, 10, 10)  #10by10 square centered on point
        px,py = mDataDict["pointXY"]
        cNum = mDataDict["curveNum"]
        pntIn = mDataDict["pIndex"]
        legend = mDataDict["legend"]
        #make a string to display
        s = "Crv# %i, '%s', Pt. (%.2f,%.2f), PtInd %i" %(cNum, legend, px, py, pntIn)
        dc.DrawText(s, sx , sy+1)
        # -----------

    def OnMouseLeftDown(self,event):
        s= "Left Mouse Down at Point: (%.4f, %.4f)" % self.client._getXY(event)
        self.SetStatusText(s)
        event.Skip() # allows plotCanvas.OnMouseLeftDown to be called

    def OnMotion(self, event):
        #show closest point (when enbled)
        if self.client.GetEnablePointLabel() == True:
            #make up dict with info for the pointLabel
            #I've decided to mark the closest point on the closest curve
            dlst= self.client.GetClosestPoint( self.client._getXY(event), pointScaled= True)
            if dlst != []:    #returns [] if none
                curveNum, legend, pIndex, pointXY, scaledXY, distance = dlst
                #make up dictionary to pass to my user function (see DrawPointLabel) 
                mDataDict= {"curveNum":curveNum, "legend":legend, "pIndex":pIndex,\
                            "pointXY":pointXY, "scaledXY":scaledXY}
                #pass dict to update the pointLabel
                self.client.UpdatePointLabel(mDataDict)
        event.Skip() # allows plotCanvas.OnMotion to be called

    def OnSaveImage(self, event):
        "Save the content of the plot area as bitmap file."
        self.client.SaveFile()

    def OnSaveData(self, event):
        """Saves the numeric data of the displayed curve as two-column ASCII
        file"""
        filename = self.config.Read('filename')
        dlg = wx.FileDialog(self,"Save Data As",wildcard="*.txt",
            defaultFile=filename,style=wx.SAVE|wx.OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            self.save_xy (self.data,filename)
            self.config.Write ('filename',filename)
        dlg.Destroy()

    def save_xy(self,xy_data,filename):
        "Write (x,y) tuples as two-column tab separated ASCII file."
        output = file(filename,"w")
        for i in range(0,len(xy_data)):
            output.write("%g\t%g\n" % (xy_data[i][0],xy_data[i][1]))

    def OnFilePageSetup(self, event):
        self.client.PageSetup()
        
    def OnFilePrintPreview(self, event):
        self.client.PrintPreview()
        
    def OnFilePrint(self, event):
        self.client.Printout()
        
    def OnFileExit(self, event):
        self.Close()

    def OnPlotData(self, event):
        self.update()

    def OnPlotRedraw(self,event):
        self.client.Redraw()

    def OnPlotClear(self,event):
        self.client.Clear()
        
    def OnPlotScale(self, event):
        if self.client.last_draw != None:
            graphics, xAxis, yAxis= self.client.last_draw
            self.client.Draw(graphics,(1,3.05),(0,1))

    def OnEnableZoom(self, event):
        self.client.SetEnableZoom(event.IsChecked())
        self.mainmenu.Check(217, not event.IsChecked())
        
    def OnEnableGrid(self, event):
        self.client.SetEnableGrid(event.IsChecked())
        
    def OnEnableDrag(self, event):
        self.client.SetEnableDrag(event.IsChecked())
        self.mainmenu.Check(214, not event.IsChecked())
        
    def OnEnableLegend(self, event):
        self.client.SetEnableLegend(event.IsChecked())

    def OnEnablePointLabel(self, event):
        self.client.SetEnablePointLabel(event.IsChecked())

    def OnScrUp(self, event):
        self.client.ScrollUp(1)
        
    def OnScrRt(self,event):
        self.client.ScrollRight(2)

    def OnReset(self,event):
        self.client.Reset()

    def OnHelpAbout(self, event):
        from wx.lib.dialogs import ScrolledMessageDialog
        about = ScrolledMessageDialog(self, __doc__, "About...")
        about.ShowModal()

    def resetDefaults(self):
        """Just to reset the fonts back to the PlotCanvas defaults"""
        self.client.SetFont(wx.Font(10,wx.SWISS,wx.NORMAL,wx.NORMAL))
        self.client.SetFontSizeAxis(10)
        self.client.SetFontSizeLegend(7)
        self.client.setLogScale((False,False))
        self.client.SetXSpec('auto')
        self.client.SetYSpec('auto')


def plot(*args,**kwargs):
    """Display a plot window.
    Does not returns when the window is closed."""
    win = Plot(*args,**kwargs)
    wx.app.MainLoop()

        
if __name__ == "__main__":
    plot([[0,0],[1,1],[2,2],[3,3],[4,4],[5,5]])
