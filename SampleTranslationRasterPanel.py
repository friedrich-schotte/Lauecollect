#!/usr/bin/env python
"""Grapical User Interface for photocrystallography chip.
Friedrich Schotte, 18 Nov 2013 - 19 Nov 2013"""

import wx
from sample_translation_raster import grid
from instrumentation import SampleX,SampleY,SampleZ
__version__ = "1.0"

class SampleTranslationRasterPanel (wx.Frame):
    """Grapical User Interface for photocrystallography chip.
    Author: Friedrich Schotte"""

    def __init__(self):
        """"""
        wx.Frame.__init__(self,parent=None,title="Sample Translation Raster",
            size=(410,460))

        # Menus
        menuBar = wx.MenuBar()
        menu = wx.Menu()
        menu.Append (121,"E&xit","Closes this window.")
        self.Bind (wx.EVT_MENU,self.OnClose,id=121)
        menuBar.Append (menu,"&File")
        menu = wx.Menu()
        menu.Append (402,"&Setup...","Parameters for sample alignment")
        self.Bind (wx.EVT_MENU,self.OnSetup,id=402)
        menuBar.Append (menu,"&More")
        menu = wx.Menu()
        menu.Append (501,"&About...","Version information")
        self.Bind (wx.EVT_MENU,self.OnAbout,id=501)
        menuBar.Append (menu,"&Help")
        self.SetMenuBar (menuBar)

        from ComboBox import ComboBox # A customized Combo Box control
        self.panel = wx.Panel(self)
        self.Image = Image(self.panel)
        choices = ["1000","500","200","100","50","20","10","5","2","1"]
        self.ScaleFactorControl = wx.ComboBox(self.panel,
            choices=choices,size=(88,-1))##,style=wx.TE_PROCESS_ENTER)
        self.ScaleFactorControl.Value = "%g" % self.Image.ScaleFactor
        self.Bind (wx.EVT_COMBOBOX,self.OnChangeScaleFactor,self.ScaleFactorControl)
        self.Bind (wx.EVT_TEXT,self.OnTypeScaleFactor,self.ScaleFactorControl)
        self.PointerFunctionControl = wx.Choice(self.panel,
            choices=["Info","Go to","Calibrate"],size=(88,-1))
        self.Bind (wx.EVT_CHOICE,self.OnPointerFunction,
            self.PointerFunctionControl)
        self.CreateStatusBar()
        # Layout
        self.layout = wx.BoxSizer(wx.VERTICAL)
        self.layout.Add (self.Image,proportion=1,flag=wx.EXPAND) # growable
        self.Controls = wx.BoxSizer(wx.HORIZONTAL)
        self.Controls.AddSpacer((5,5))
        self.Controls.Add(self.ScaleFactorControl,flag=wx.ALIGN_CENTER)
        self.Controls.AddSpacer((5,5))
        self.Controls.Add(self.PointerFunctionControl,flag=wx.ALIGN_CENTER)
        self.layout.Add (self.Controls,flag=wx.EXPAND)
        self.panel.SetSizer(self.layout)
        self.panel.Layout()

        self.Bind(wx.EVT_CLOSE,self.OnClose)
        self.Show()
        
        # Restore last saved settings.
        name = "SampleTranslationRaster"
        self.config_file=wx.StandardPaths.Get().GetUserDataDir()+"/"+name+".py"
        self.config = wx.FileConfig (localFilename=self.config_file)
        state = self.config.Read('State')
        if state:
            try: self.State = eval(state)
            except Exception,exception:
                print "Restore failed: %s: %s" % (exception,state)

        self.timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.update,self.timer)
        self.timer.Start(1000,oneShot=True)

    def update(self,event=None):
        """Periodocally called on timer"""
        self.Image.Refresh()
        self.timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.update,self.timer)
        self.timer.Start(1000,oneShot=True)

    def GetScaleFactor(self):
        """Current value of scale control as float"""
        return self.Image.ScaleFactor
    def SetScaleFactor(self,value):
        self.Image.ScaleFactor = value
        text = "%g" % value
        if self.ScaleFactorControl.StringSelection != text:
            self.ScaleFactorControl.StringSelection = text
    ScaleFactor = property (GetScaleFactor,SetScaleFactor)

    def OnChangeScaleFactor(self,event):
        """Callback for the ScaleFactor control"""
        from numpy import isnan
        ##print("OnChangeScaleFactor")
        ##print("event.String %r" % event.String)
        ##print("ScaleFactorControl.StringSelection %r" % self.ScaleFactorControl.StringSelection)
        ##print("ScaleFactorControl.Value %r" % self.ScaleFactorControl.Value)
        scale = tofloat(self.ScaleFactorControl.StringSelection)
        if not isnan(scale): self.Image.ScaleFactor = scale
        self.ScaleFactorControl.Value = "%g" % self.Image.ScaleFactor

    def OnTypeScaleFactor(self,event):
        """Callback for the ScaleFactor control"""
        from numpy import isnan
        ##print("OnTypeScaleFactor")
        ##print("event.String %r" % event.String)
        ##print("ScaleFactorControl.StringSelection %r" % self.ScaleFactorControl.StringSelection)
        ##print("ScaleFactorControl.Value %r" % self.ScaleFactorControl.Value)
        # Due ot a bug on MacOSX, settings a callback on Enter crashes
        # Python.
        # As a work-around wait for SPACE instead to "enter" the current value.
        if not event.String.endswith(" "): return
        scale = tofloat(event.String)
        ##print("scale = %r" % scale)        
        if not isnan(scale): self.Image.ScaleFactor = scale
        self.ScaleFactorControl.Value = "%g" % self.Image.ScaleFactor
        self.ScaleFactorControl.StringSelection = "%g" % self.Image.ScaleFactor

    def GetPointerFunction(self):
        """What happens at a mouse-click? type: string"""
        return self.Image.PointerFunction
    def SetPointerFunction(self,value):
        self.Image.PointerFunction = value
        self.PointerFunctionControl.StringSelection = value
    PointerFunction = property (GetPointerFunction,SetPointerFunction)

    def OnPointerFunction(self,event):
        """Callback for the PointerFunction control"""
        self.Image.PointerFunction = self.PointerFunctionControl.StringSelection

    def OnClose(self,event):
        """Clase the window and save settings"""
        self.Show(False)

        # Save settings for next time.
        self.config.Write ('State',repr(self.State))
        self.config.Flush()

        app.ExitMainLoop() # for debugging
        ##self.Destroy()

    def GetState(self):
        """The current settings of the window as dictionary"""
        state = {}
        state["Size"] = self.Size
        state["Position"] = self.Position
        state["ScaleFactor"] = self.ScaleFactor
        state["PointerFunction"] = self.PointerFunction
        state["Image.State"] = self.Image.State
        return state
    def SetState(self,state):
        ##print "MainWindow: restoring %r" % state
        for key in state:
            try: exec("self."+key+"="+repr(state[key]))
            except Exception,msg: print("%s = %s: %s" % (key,state[key],msg))
    State = property(GetState,SetState)

    def OnSetup(self,event):
        """Change parameters controlling click-centering procedure"""
        dlg = Setup(self)
        dlg.CenterOnParent()
        dlg.Show()

    def OnAbout(self,event):
        """Show version info"""
        info = self.__class__.__name__+" "+__version__+"\n"+__doc__
        dlg = wx.MessageDialog(self,info,"About",wx.OK|wx.ICON_INFORMATION)
        dlg.CenterOnParent()
        dlg.ShowModal()
        dlg.Destroy()


class Image(wx.ScrolledWindow):
    scale_factor = 50.0
    color = (100,100,100)
    support_point_color = (255,0,0)
    support_point_location_color = (0,0,255)
    highlight_color = (255,255,0)
    current_position_color = (0,255,0)
    dotsize = 0.03 # in mm
    x_axis = [0,0,1] # coordinate selector for horizontal direction in image
    y_axis = [0,1,0] # coordinate selector for vertical direction in image
    current = 0 # highlight this spot
    PointerFunction = "Info"
    
    def __init__(self,parent):
        wx.ScrolledWindow.__init__(self,parent)
        self.SetScrollRate(1,1)
        self.Bind (wx.EVT_PAINT, self.OnPaint)
        self.Bind (wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind (wx.EVT_SIZE, self.OnResize)
        self.Bind (wx.EVT_LEFT_DOWN,self.OnLeftDown)
        self.Bind (wx.EVT_KEY_DOWN,self.OnKey)

    def OnPaint (self,event):
        """Called by WX whenever the contents of the window
        needs re-rendering. E.g. when the window is brought to front,
        uncovered, restored from minimized state."""

        dc = wx.PaintDC(self)
        # Needed to set the origin according to the scrollbar positions.
        self.PrepareDC(dc)
            
        # Display scroll bars if the window is smaller than the space needed.
        w = self.ImageWidth * self.ScaleFactor
        h = self.ImageHeight * self.ScaleFactor
        self.VirtualSize = w,h

        self.draw(dc)

    def OnEraseBackground(self, event):
        """Overrides default background fill, avoiding flickering"""

    def OnResize (self,event):
        w = self.ImageWidth * self.ScaleFactor
        h = self.ImageHeight * self.ScaleFactor
        self.VirtualSize = w,h
        self.Refresh()

    def OnLeftDown(self,event):
        """Show information about the feature the mouse was clicked on"""
        from numpy import argmin,sqrt,dot
        xi,yi = event.Position
        x,y = self.ScaledPosition(xi,yi)
        XYZ = grid.xyz
        if len(XYZ) > 0:
            X,Y = dot(XYZ,self.x_axis),dot(XYZ,self.y_axis)
            i = argmin(sqrt((x-X)**2+(y-Y)**2))
            indices = tuple(grid.indices[i])
            self.current = i
            if self.PointerFunction == "Info":
                xyz = grid.xyz[i]
            elif self.PointerFunction == "Go to":
                xyz = grid.xyz[i]
                self.current_position = xyz
            elif self.PointerFunction == "Calibrate":
                xyz = self.current_position
                if not grid.has_support_indices(indices):
                    ##print("add %r,%r" % (indices,xyz))
                    grid.add_support_point(indices,xyz)
                else: grid.remove_support_indices(indices)
            x,y,z = xyz
            text = "#%r %r" % (i+1,indices)
            text += " %+.3f,%+.3f,%+.3f" % (x,y,z)
        else:
            self.current = 0
            text = ""
        self.Refresh()
        self.Parent.Parent.SetStatusText(text)

    def OnKey(self,event):
        """Navigate from spot to spot"""
        ##print("Key %r" % event.KeyCode)
        from numpy import clip
        n = len(grid.indices)
        step = grid.n[-1]
        if event.KeyCode == wx.WXK_LEFT:
            print("left")
            self.current = clip(self.current-1,0,n-1)
        if event.KeyCode == wx.WXK_RIGHT:
            print("right")
            self.current = clip(self.current+1,0,n-1)
        if event.KeyCode == wx.WXK_UP:
            print("up")
            self.current = clip(self.current-step,0,n-1)
        if event.KeyCode == wx.WXK_DOWN:
            print("down")
            self.current = clip(self.current+step,0,n-1)
        self.Refresh()

    def get_current_position(self):
        """Current position (x,y,z)"""
        return SampleX.value,SampleY.value,SampleZ.value
    def set_current_position(self,xyz):
        SampleX.value,SampleY.value,SampleZ.value = xyz
    current_position = property(get_current_position,set_current_position)

    def draw (self,dc):
        """This function is responsible for drawing the contents of the window.
        """
        from numpy import dot,isnan,array,where,all
        gc = wx.GraphicsContext.Create(dc)
        x,y,z = grid.xyz.T
        s = self.ScaleFactor
        ox,oy = self.Offset
        gc.Scale(s,s)
        gc.Translate(ox,oy)

        d = self.dotsize
        gc.SetBrush(wx.TRANSPARENT_BRUSH)
        gc.SetPen (wx.Pen(self.color,d/4))
        xyz = grid.xyz
        XY = array(zip(dot(xyz,self.x_axis),dot(xyz,self.y_axis)))
        for x,y in XY: gc.DrawRectangle(x-d/2,y-d/2,d,d)

        # Show support point location.
        gc.SetPen (wx.Pen(self.support_point_location_color,d/4))
        xyz = grid.support_xyz
        X,Y = dot(xyz,self.x_axis),dot(xyz,self.y_axis)
        for (x,y) in zip(X,Y):
            gc.DrawRectangle(x-d/2,y-d/2,d,d)

        # Highlight support points in grid.
        indices = grid.indices
        ns = []
        for si in grid.support_indices:
            if any(all(indices==si,axis=1)): ns += [where(all(indices==si,axis=1))[0][0]]
        gc.SetPen (wx.Pen(self.support_point_color,d/4))
        for x,y in XY[ns]: gc.DrawRectangle(x-d/2,y-d/2,d,d)

        # Highlight current point.
        if len(grid.xyz) > 0:
            from numpy import clip
            i = clip(self.current,0,len(grid.xyz)-1)
            xyz = grid.xyz[i]
            gc.SetPen (wx.Pen(self.highlight_color,d/8))
            x,y = dot(xyz,self.x_axis),dot(xyz,self.y_axis)
            d2 = d/2
            gc.DrawRectangle(x-d2/2,y-d2/2,d2,d2)

        # Show current position
        xyz = self.current_position
        if not any(isnan(xyz)): 
            gc.SetPen (wx.Pen(self.current_position_color,d/8))
            x,y = dot(xyz,self.x_axis),dot(xyz,self.y_axis)
            d2 = d/2
            gc.DrawRectangle(x-d2/2,y-d2/2,d2,d2)
        
    def ScaledPosition(self,x,y):
        """x,y: pixel coordinates
        Return value: real (x,y) coordinates in mm"""
        xu,yu = self.CalcUnscrolledPosition(x,y)
        s = self.ScaleFactor
        ox,oy = self.Offset
        xs,ys = xu/s-ox,yu/s-oy
        return xs,ys

    @property
    def Offset(self):
        """For drawing, in mm"""
        x,y,z = grid.xyz.T
        w,h = max(z)-min(z),max(y)-min(y)
        ox,oy = -min(z)+w*0.025,-min(y)+h*0.025
        return ox,oy

    @property
    def ImageWidth(self):
        """in mm"""
        x,y,z = grid.xyz.T
        width = max(z)-min(z)
        return width

    @property
    def ImageHeight(self):
        """in mm"""
        x,y,z = grid.xyz.T
        height = max(y)-min(y)
        return height

    def GetScaleFactor(self):
        return self.scale_factor
    def SetScaleFactor(self,value):
        self.scale_factor = value
        self.Refresh()
    ScaleFactor = property(GetScaleFactor,SetScaleFactor)

    def GetState(self):
        """The current settings of the window as dictionary"""
        state = {}
        state["ScaleFactor"] = self.ScaleFactor
        state["PointerFunction"] = self.PointerFunction
        state["current"] = self.current
        return state
    def SetState(self,state):
        for key in state:
            try: exec("self."+key+"="+repr(state[key]))
            except Exception,msg: print("%s = %s: %s" % (key,state[key],msg))
    State = property(GetState,SetState)


class Setup (wx.Dialog):
    """Allows the use to configure camera properties"""
    def __init__ (self,parent):
        from TextCtrl import TextCtrl
        wx.Dialog.__init__(self,parent,-1,"Setup")
        # Controls
        style = wx.TE_PROCESS_ENTER

        self.N = TextCtrl (self,size=(160,-1),style=style)
        self.Origin = TextCtrl (self,size=(160,-1),style=style)
        self.BaseVectors = TextCtrl (self,size=(160,80),style=style)

        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnter)

        # Layout
        layout = wx.BoxSizer()
        grid = wx.FlexGridSizer (cols=2,hgap=5,vgap=5)
        flag = wx.ALIGN_CENTER_VERTICAL
        
        label = "Number:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.N,flag=flag)
        label = "Origen:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.Origin,flag=flag)
        label = "Base vectors:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.BaseVectors,flag=flag)

        # Leave a 10-pixel wide space around the panel.
        layout.Add (grid,flag=wx.EXPAND|wx.ALL,border=10)

        self.SetSizer(layout)
        self.Fit()

        self.update()

    def update(self,Event=0):
        """Update the controls from the parameters"""
        self.N.Value = ",".join([str(n) for n in grid.n])
        def format(v): return "%+.3f,%+.3f,%+.3f" % tuple(v)
        self.Origin.Value =  format(grid.origin)
        self.BaseVectors.Value = "\n".join([format(b) for b in grid.base_vectors])

    def OnEnter(self,event):
        """Update the parameters from the controls"""
        from numpy import asarray
        t = self.N.Value
        t = t.replace("x",",")
        try: grid.n = asarray(eval(t))
        except Exception,msg: print("%r: %r" % (t,msg))        
        t = self.Origin.Value
        try: grid.origin = asarray(eval(t))
        except Exception,msg: print("%r: %r" % (t,msg))        
        t = self.BaseVectors.Value
        t = t.replace("\r","\n")
        try: grid.base_vectors = asarray([eval(v) for v in t.split("\n")])
        except Exception,msg: print("%r: %r" % (v,msg))
        ##print("grid.n = %r" % n)
        ##print("grid.origin = %r" % origin)
        ##print("grid.base_vectors = %r" % base_vectors)
        self.update()
       

def tofloat(x):
    from numpy import nan
    try: return float(x)
    except: return nan



if __name__ == '__main__': # for testing
    from pdb import pm
    app = wx.PySimpleApp(redirect=False) # Needed to initialize WX library
    window = SampleTranslationRasterPanel()
    app.MainLoop()
    self = window # for debugging
