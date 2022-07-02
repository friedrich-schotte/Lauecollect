#!/usr/bin/env python
"""Grapical User Interface for a video camera.
Designed for Prosilia GigE cameras.
Author: Friedrich Schotte
Date created: 2008-02-05
Date last modified: 2020-06-09
Revision comment: Cleanup: isstring
"""
__version__ = "6.4.4" 
from logging import debug,info,warning,error

import wx
import wx.lib.colourselect
from os import makedirs
from os.path import exists,dirname,basename,splitext
from math import sqrt,atan2,sin,cos,pi,log10
from numpy import nan,isnan
# Turn off IEEE-754 warnings in numpy 1.6+ ("invalid value encountered in...")
import numpy; numpy.seterr(invalid="ignore",divide="ignore")
from EditableControls import ComboBox,TextCtrl
from Panel import BasePanel,PropertyPanel

class CameraViewer(wx.Frame):
    icon = "camera"
    from persistent_property import persistent_property
    title = persistent_property("CameraViewer_{name}.title","Camera Viewer")
    zoom_level = persistent_property("CameraViewer_{name}.zoom_level",1.0)
    zoom_levels = persistent_property("CameraViewer_{name}.zoom_levels",[1.0])
    dt = persistent_property("CameraViewer_{name}.dt",0.5)

    def __init__(self,name="CameraViewer",title=None,
        pixelsize=1.0,
        orientation=None,default_orientation=None,mirror=None,show=True):
        """
        name: used for storing and retreiving settings
        pixelsize: default pixelsize in units of mm; used for measurements
        orientation: default image rotation in degrees
        default_orientation: same as "orientation" (for backward compatibility)
        positive = counter-clock wise
        allowed values: 0,-90,90,180
        only use at first invecation as default value, last saved value
        overrides this value.
        show: display the window immediately
        """
        self.name = name
        if title is not None: self.title = title
        wx.Frame.__init__(self,parent=None,title=self.title,size=(425,340))
        
        self.image_timestamp = 0.0
        self.filename = ""
        self.settings_timestamp = 0.0

        # Icon
        from Icon import SetIcon
        SetIcon(self,self.icon)
        # Menus
        menuBar = wx.MenuBar()
        menu = wx.Menu()
        menu.Append (101,"&Open Image...\tCtrl+O","Loads a saved JPEG file.")
        self.Bind (wx.EVT_MENU,self.OnOpen,id=101)
        menu.AppendSeparator()
        menu.Append (111,"&Save Image As...\tCtrl+S","Creates a full-resolution JPEG file.")
        self.Bind (wx.EVT_MENU,self.OnSave,id=111)
        menu.Append (112,"&Save Beam Profile As...","Creates text file with numerical data.")
        self.Bind (wx.EVT_MENU,self.OnSaveProfile,id=112)
        menu.AppendSeparator()
        menu.Append (121,"E&xit","Closes this window.")
        self.Bind (wx.EVT_MENU,self.OnExit,id=121)
        menuBar.Append (menu,"&File")
        menu = wx.Menu()
        menu.Append (201,"&Copy Image\tCtrl+C",
            "Places copy of full image in the clipboard")
        self.Bind (wx.EVT_MENU,self.CopyImage,id=201)
        menuBar.Append (menu,"&Edit")
        menu = self.OrienationMenu = wx.Menu()
        style = wx.ITEM_CHECK
        menu.Append (301,"As Camera","Do not rotate image",style)
        menu.Append (302,"Rotated Clockwise","Rotate image by -90 deg",style)
        menu.Append (303,"Rotated Counter-clockwise","Rotate image by +90 deg",style)
        menu.Append (304,"Upside down","Rotate image by 180 deg",style)
        menu.AppendSeparator()
        menu.Append (305,"Mirror","Flip image horizontal",style)
        for id in 301,302,303,304,305:
            self.Bind (wx.EVT_MENU,self.OnOrientation,id=id)
        menuBar.Append (menu,"&Orientation")
        menu = wx.Menu()
        menu.Append (399,"&Viewer...","Configures the viewer")
        self.Bind (wx.EVT_MENU,self.OnViewerOptions,id=399)
        menu.Append (401,"&Camera...","Configures the camera acqusition")
        self.Bind (wx.EVT_MENU,self.OnCameraOptions,id=401)
        menu.Append (400,"&Optics...","Configures the camera optics")
        self.Bind (wx.EVT_MENU,self.OnOpticsOptions,id=400)
        menuBar.Append (menu,"O&ptions")
        menu = wx.Menu()
        menu.Append (501,"&About...","Version information")
        self.Bind (wx.EVT_MENU,self.OnAbout,id=501)
        menuBar.Append (menu,"&Help")
        self.SetMenuBar (menuBar)
        # Controls
        self.CreateStatusBar()
        self.panel = wx.Panel(self)
        self.ImageWindow = ImageWindow (self.panel)
        self.LiveImage = wx.CheckBox (self.panel,label="Live")
        self.Bind(wx.EVT_CHECKBOX,self.OnLifeImage,self.LiveImage)
        choices = ["200%","100%","50%","33%","25%","Fit Width"]
        self.ScaleFactorControl = ComboBox(self.panel,value="100%",
            choices=choices,size=(88,-1),style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_COMBOBOX,self.OnChangeScaleFactor,self.ScaleFactorControl)
        self.Bind(wx.EVT_TEXT_ENTER,self.OnChangeScaleFactor,self.ScaleFactorControl)
        self.ExposureValue = TextCtrl (self.panel,size=(50,-1),
            style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER,self.OnEnterExposureValue,self.ExposureValue)
        self.ExposureControl = wx.Slider (self.panel,maxValue=1000)
        self.Bind(wx.EVT_SLIDER,self.OnMoveSlider,self.ExposureControl)
        self.AutoExposure = wx.CheckBox (self.panel,label="Auto")
        self.Bind(wx.EVT_CHECKBOX,self.OnAutoExposure,self.AutoExposure)
        self.ZoomLabel = wx.StaticText(self.panel,label="Zoom:")
        self.ZoomLabel.Show(False)
        self.ZoomControl = ComboBox(self.panel,style=wx.TE_PROCESS_ENTER)
        self.ZoomControl.Show(False)
        self.Bind(wx.EVT_COMBOBOX,self.OnChangeZoomLevel,self.ZoomControl)
        self.Bind(wx.EVT_TEXT_ENTER,self.OnChangeZoomLevel,self.ZoomControl)
        # Layout
        self.layout = wx.BoxSizer(wx.VERTICAL)
        self.layout.Add (self.ImageWindow,proportion=1,flag=wx.EXPAND) # growable
        self.layout.AddSpacer(2)
        self.Controls = wx.BoxSizer(wx.HORIZONTAL)
        self.Controls.AddSpacer(5)
        self.Controls.Add (self.LiveImage,flag=wx.ALIGN_CENTER)
        self.Controls.AddSpacer(5)
        self.Controls.Add (self.ScaleFactorControl,flag=wx.ALIGN_CENTER)
        self.Controls.AddSpacer(5)
        self.Controls.Add (self.ExposureValue,flag=wx.ALIGN_CENTER)
        self.Controls.AddSpacer(5)       
        # Make exposure slider growable (proportion=1)
        self.Controls.Add (self.ExposureControl,proportion=1,flag=wx.ALIGN_CENTER)
        self.Controls.AddSpacer(5)
        self.Controls.Add (self.AutoExposure,flag=wx.ALIGN_CENTER)
        self.Controls.AddSpacer(5)
        self.Controls.Add (self.ZoomLabel,flag=wx.ALIGN_CENTER)
        self.Controls.AddSpacer(5)
        self.Controls.Add (self.ZoomControl,flag=wx.ALIGN_CENTER)
        self.layout.Add (self.Controls,flag=wx.EXPAND)
        self.panel.SetSizer(self.layout)

        # Initialization
        from camera_client import Camera
        self.camera = Camera(self.name)
        if orientation != None: self.Orientation = orientation
        if mirror != None: self.Mirror = mirror
        if default_orientation != None: self.Orientation = default_orientation
        if orientation != None: self.Orientation = orientation
        if pixelsize != None: self.NominalPixelSize = pixelsize
                
        self.Bind (wx.EVT_CLOSE,self.OnClose)
        
        # Restore last saved settings
        self.settings_timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.update_settings,self.settings_timer)
        self.settings_timer.Start(1,oneShot=True)

        if show: self.Show()

        self.image_timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.update_image,self.image_timer)
        self.image_timer.Start(int(self.dt*1000),oneShot=True)

    def GetTitle(self):
        value = self.title
        ##value = wx.Frame.GetTitle(self)
        return value
    def SetTitle(self,value):
        warning("Title=%r" % value)
        wx.Frame.SetTitle(self,value)
        self.title = value
    Title = property(GetTitle,SetTitle)

    def update_image(self,event=None):
        if self.image_update_needed():                
            # Replace the currently display image with the last one
            # acquired by the camera, if the camera image has changed
            if self.camera.has_image and self.camera.timestamp != self.image_timestamp:
                self.show_image()

        # Update the slider indicating the exposure time
        self.ExposureTime_Slider = self.camera.exposure_time
        self.ExposureTime_Value = self.camera.exposure_time
        #  Update the "Auto" checkbox
        self.AutoExposure.Value = self.camera.auto_exposure
        self.LiveImage.Value = self.camera.acquiring
        # Update status bar
        self.SetStatusText(self.camera.state)
        self.ZoomLevels = self.zoom_levels
        self.ZoomLevel = self.zoom_level

        # Relaunch this procedure after 500 ms.
        self.image_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER,self.update_image,self.image_timer)
        self.image_timer.Start(int(self.dt*1000),oneShot=True)

    def image_update_needed(self):
        """Do we need to read the camera periodcally?"""
        # Save network bandwidth and CPU time if the Window is minimized.
        return (self.camera.acquiring and not self.IsIconized())

    def show_image(self):
        """Replaces the currently display image with the last one
        acquired by the camera"""
        self.ImageWindow.Image = self.camera.RGB_array
        self.image_timestamp = self.camera.timestamp

    def OnLifeImage(self,event):
        """Trn on or off image acquisition"""
        self.camera.acquiring = event.IsChecked()
        
    def OnChangeScaleFactor(self,event):
        """Called when a different zoom is selected"""
        self.ImageWindow.ScaleFactor = self.ScaleFactor

    def GetScaleFactor(self):
        """Reads the image scale control and returns is a number between 0
        and 1, or None if "Fit Width" is selected."""
        selection = self.ScaleFactorControl.Value
        try: return float(selection.strip("%"))/100
        except: return None
    def SetScaleFactor(self,scale):
        """Changes the scale control.
        scale is a number between 0 and 1, scale=None means "Fit Width" """
        if scale != None: self.ScaleFactorControl.SetValue("%g%%" % (scale*100.))
        else: self.ScaleFactorControl.SetValue("Fit Width")
    ScaleFactor = property (GetScaleFactor,SetScaleFactor)

    def GetOrientation(self):
        """Image rotation as defined by the "Orientation" menu"""
        return self.ImageWindow.Orientation
    def SetOrientation(self,value):
        # Update the displayed image.
        self.ImageWindow.Orientation = value
        # Update the "Orientation" menu.
        values = {301:0,302:-90,303:+90,304:180}
        for id in values: self.OrienationMenu.Check(id,value == values[id])
    Orientation = property (GetOrientation,SetOrientation)

    def GetMirror(self):
        """Is image flipped horizontally?"""
        return self.ImageWindow.Mirror
    def SetMirror(self,value):
        # Update the displayed image.
        self.ImageWindow.Mirror = value
        # Update the "Orientation" menu.
        self.OrienationMenu.Check(305,value)
    Mirror = property (GetMirror,SetMirror)

    def OnEnterExposureValue(self,event):
        """Called when Enter is pressed in the text box displaying the
        exposure time."""
        # Update the exposure time indicator
        self.ExposureTime_Slider = self.ExposureTime_Value
        # Apply the new exposure time to the camera.
        self.camera.exposure_time = self.ExposureTime_Value
        
    def GetExposureTime_Value(self):
        """CCD integration time in seconds as displayed numerically or typed"""
        text = self.ExposureValue.Value
        text = text.strip("s")
        try: return float(text)
        except: return 0.050 # default exposure time: 50 ms
    def SetExposureTime_Value(self,t):
        self.ExposureValue.Value = "%.2g s" % t
    ExposureTime_Value = property (GetExposureTime_Value,SetExposureTime_Value)

    def OnMoveSlider(self,event):
        """Called if the slider controlling the exposure time is moved."""
        # Update the exposure time indicator
        self.ExposureTime_Value = self.ExposureTime_Slider
        # Apply the new exposure time to the camera.
        self.camera.exposure_time = self.ExposureTime_Slider

    def GetExposureTime_Slider(self):
        """CCD integration time in seconds set by the slider"""
        # The slider position is an integer value from 0 to Max
        Max = self.ExposureControl.GetMax()
        fraction = float(self.ExposureControl.GetValue())/Max
        # This is translated into 0 to 1 seconds on a non-linear scale
        t = fraction**2
        return t
    def SetExposureTime_Slider(self,t):
        # This translates the range 0 to 1 seconds non-linearly to a fraction
        # of the slider range.
        fraction = t**0.5
        Max = self.ExposureControl.GetMax()
        self.ExposureControl.SetValue(fraction*Max)
    ExposureTime_Slider = property(GetExposureTime_Slider,
        SetExposureTime_Slider)

    def OnAutoExposure(self,event):
        """Called when the "Auto" Checkbox is clicked"""
        self.camera.auto_exposure = self.AutoExposure.GetValue()

    def OnChangeZoomLevel(self,event):
        """Called when a different zoom is selected"""
        self.zoom_level = self.ZoomLevel
        self.ImageWindow.PixelSize = self.NominalPixelSize/self.zoom_level

    def GetZoomLevel(self):
        """Scale factor for pixel size for microscope with variable
        magnification"""
        if not self.HasZoom: return 1.0
        text = self.ZoomControl.Value
        try: value = float(text)
        except: value = 1.0
        return value
    def SetZoomLevel(self,value):
        if not self.HasZoom: return
        self.ImageWindow.PixelSize = self.NominalPixelSize/value
        text = str(value)
        if self.ZoomControl.Value != text:
            self.ZoomControl.Value = text
    ZoomLevel = property (GetZoomLevel,SetZoomLevel)

    def GetHasZoom(self):
        """Are the zoom controls active?"""
        return self.ZoomControl.Shown
    def SetHasZoom(self,value):
        """value: True or False"""
        value = bool(value)
        if self.ZoomControl.Shown == value: return # nothing to do
        # Show or hide zoom control.
        self.ZoomLabel.Show(value)
        self.ZoomControl.Show(value)
        self.Controls.Layout()
    HasZoom = property(GetHasZoom,SetHasZoom)
    
    def GetZoomLevels(self):
        """Choices for microscope with variable magnification"""
        text_values = self.ZoomControl.Items
        values = []
        for text_value in text_values:
            try: value = eval(text_value)
            except Exception as msg:
                warning("Zoom level: %s: %s" % (text_value,msg))
                continue
            values += [value]
        return values
    def SetZoomLevels(self,choices):
        choices = [str(x) for x in choices]
        old_choices = self.ZoomControl.Items
        if choices != old_choices:
            self.ZoomControl.Items = choices
        shown = (len(choices) > 0)
        was_shown = (len(old_choices) > 0)
        if shown != was_shown:
            self.ZoomLabel.Shown = shown
            self.ZoomControl.Shown = shown
            self.Controls.Layout()
    ZoomLevels = property (GetZoomLevels,SetZoomLevels,)

    def GetPixelSize(self): return self.ImageWindow.PixelSize
    def SetPixelSize(self,pixelsize):
        if not self.HasZoom:
            self.ImageWindow.PixelSize = pixelsize
            self.NominalPixelSize = pixelsize
        else:
            self.ImageWindow.PixelSize = pixelsize
            self.NominalPixelSize = pixelsize*self.ZoomLevel
    PixelSize = property (GetPixelSize,SetPixelSize)

    def GetNominalPixelSize(self):
        """Pixelsize as Zoom = 1.0"""
        if not self.HasZoom: self.ImageWindow.PixelSize
        return getattr(self,"nominal_pixelsize",1.0)
    def SetNominalPixelSize(self,value):
        self.nominal_pixelsize = value
        if not self.HasZoom: self.ImageWindow.PixelSize = value
        else: self.ImageWindow.PixelSize = value/self.ZoomLevel
    NominalPixelSize = property (GetNominalPixelSize,SetNominalPixelSize)

    def GetPosition(self):
        x,y = wx.Frame.GetPosition(self)
        if x < 0 or y < 0:
            warning("Invalid window position %r,%r. using 0,0 instead" % (x,y))
            return 0,0
        return x,y
    def SetPosition(self,value):
        """Moves the window on the desktop.
        value: (x,y) top left corner coordindates"""
        # Set the window size programmatically only once at startup, never again.
        if hasattr(self,"Positioned"): return 
        # The reason I override WX's built-in "SetPosition" method is that
        # when non-sensical coordrinates are passed to it making the window
        # "invisble".
        x,y = value
        xmin,ymin = 0,20
        xmax,ymax = wx.DisplaySize()[0]-10,wx.DisplaySize()[1]-10
        if x<xmin: warning("Ignoring window x=%r. Using %r." % (x,xmax)); x = xmin
        if y<ymin: warning("Ignoring window y=%r. Using %r." % (y,ymin)); y = ymin
        if x>xmax: warning("Ignoring window x=%r. Using %r." % (x,xmax)); x = xmax
        if y>ymax: warning("Ignoring window y=%r. Using %r." % (y,ymax)); y = ymax
        wx.Frame.SetPosition(self,(x,y))
        self.Positioned = True
    Position = property(GetPosition,SetPosition)

    def GetSize(self):
        w,h = wx.Frame.GetSize(self)
        if w < 40 or h < 40:
            warning("Invalid window size %r,%r. using 400,400 instead"%(w,h))
            return 400,400
        return w,h
    def SetSize(self,value):
        """Resizes the window.
        value: (width,height) tuple"""
        # Set the window size programmatically only once at startup, never again.
        if hasattr(self,"Sized"): return 
        # The reason I override WX's built-in "SetSize" method is that
        # when non-sensical coordrinates are passed to it making the window
        # "invisble".
        w,h = value
        if w < 40 or h < 40: warning("Ignoring window size %r,%r"%(w,h)); return
        wx.Frame.SetSize(self,(w,h))
        self.Sized = True
    Size = property(GetSize,SetSize)

    def GetPointerFunction(self):
        "What does pressing the left mouse button on the image mean?"
        return  self.ImageWindow.PointerFunction
    def SetPointerFunction(self,name):
         self.ImageWindow.PointerFunction = name
    PointerFunction = property(GetPointerFunction,SetPointerFunction)

    def AddPointerFunction(self,name):
        """Add an item to the context menu"""
        self.ImageWindow.AddPointerFunction(name)

    def GetShowGrid(self): return self.ImageWindow.show_grid
    def SetShowGrid(self,value):
        if value != self.ImageWindow.show_grid:
            self.ImageWindow.show_grid = value
            self.ImageWindow.Refresh()
    ShowGrid = property(GetShowGrid,SetShowGrid)

    def GetGridXSpacing(self): return self.ImageWindow.GridXSpacing
    def SetGridXSpacing(self,value): self.ImageWindow.GridXSpacing = value
    GridXSpacing = property(GetGridXSpacing,SetGridXSpacing)

    def GetGridXOffset(self): return self.ImageWindow.GridXOffset
    def SetGridXOffset(self,value): self.ImageWindow.GridXOffset = value
    GridXOffset = property(GetGridXOffset,SetGridXOffset)

    def GetGridYSpacing(self): return self.ImageWindow.GridYSpacing
    def SetGridYSpacing(self,value): self.ImageWindow.GridYSpacing = value
    GridYSpacing = property(GetGridYSpacing,SetGridYSpacing)

    def GetGridYOffset(self): return self.ImageWindow.GridYOffset
    def SetGridYOffset(self,value): self.ImageWindow.GridYOffset = value
    GridYOffset = property(GetGridYOffset,SetGridYOffset)

    def AddObject(self,name,points=[],color=(0,0,255),type="squares"):
        """Add a custom shape to be drawn on top of the image.
        name: Displayed in show/hide context menu
        points: list if x,y pairs in mm coordinates relative to
        the crosshair
        color: default color. Can be overriden from properties dialog."""
        self.ImageWindow.AddObject(name,points,color,type)

    def DeleteObject(self,name):
        """Remove a custom shape to be drawn on top of the image.
        name: Displayed in show/hide context menu"""
        self.ImageWindow.DeleteObject(name)

    def OnOpen(self,event):
        "Called from menu File/Open Image..."
        dlg = wx.FileDialog(self,"Open Image",style=wx.FD_OPEN,
            defaultDir=dirname(self.filename),defaultFile=basename(self.filename),
            wildcard="JPEG Images (*.jpg)|*.jpg|TIFF Images (*.tif)|*.tif|"+
            "PNG Images (*.png)|*.png|All Files (*.*)|*.*")
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetPath()
            wximage = wx.Image(self.filename)
            # Get the image pixelsize.
            # (wx.Image.GetOptionInt (wx.IMAGE_OPTION_RESOLUTION) always returns 0
            # thus, using PIL.)
            from PIL import Image
            PIL_image = Image.open(self.filename)
            if "dpi" in PIL_image.info:
                self.ImageWindow.PixelSize = 25.4/PIL_image.info["dpi"][0]
            # Convert image from WX to numpy format.
            data = wximage.Data
            w,h = wximage.Width,wximage.Height
            from numpy import frombuffer,uint8
            image = frombuffer(data,uint8).reshape(h,w,3).T
            self.ImageWindow.TransformedImage = image
        dlg.Destroy()

    def OnSave(self,event):
        "Called from menu File/Save Image As..."
        filename = splitext(self.filename)[0]+".jpg"
        dlg = wx.FileDialog(self,"Save Image As",
            style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT,
            defaultFile=basename(filename),defaultDir=dirname(filename),
            wildcard="JPEG Images (*.jpg)|*.jpg|TIFF Images (*.tif)|*.tif|"+
            "PNG Images (*.png)|*.png|All Files (*.*)|*.*")
        if dlg.ShowModal() == wx.ID_OK:
            filename = str(dlg.GetPath())
            index = dlg.GetFilterIndex()
            extensions = [".jpg",".tif",".png",""]
            def_extension = extensions[index]
            extension = splitext(filename)[1]
            if extension == "" and def_extension != "": filename += "."+def_extension
            types = [wx.BITMAP_TYPE_JPEG,wx.BITMAP_TYPE_TIF,wx.BITMAP_TYPE_PNG,
                None]
            type = types[index]
            if type == None and extension in extensions:
                type = types[extensions.index(extension)]
            if type == None: type = types[0]
            image = self.ImageWindow.TransformedImage
            # Convert image from numpy to WX data format.
            d,w,h = image.shape
            wximage = wx.Image(w,h)
            data = image.T.tobytes()
            wximage.Data = data
            # Save pixelsize as DPI in image header.
            wximage.SetOptionInt (wx.IMAGE_OPTION_QUALITY,100)
            dpi = int(round(25.4/self.ImageWindow.PixelSize))
            wximage.SetOptionInt (wx.IMAGE_OPTION_RESOLUTION,dpi)
            wximage.SetOptionInt (wx.IMAGE_OPTION_RESOLUTIONUNIT,wx.IMAGE_RESOLUTION_INCHES)
            wximage.SaveFile (filename,type)
            self.filename = filename
        dlg.Destroy()

    def OnSaveProfile(self,event):
        "Called from menu File/Save Beam Profile As..."
        filename = splitext(self.filename)[0]+".txt"
        dlg = wx.FileDialog(self,"Save Profile As",
            style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT,
            defaultFile=basename(filename),defaultDir=dirname(filename),
            wildcard="Text Files (*.txt)|*.txt|All Files (*.*)|*.*")
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            x = xvals(self.ImageWindow.xprofile)
            Ix = yvals(self.ImageWindow.xprofile)
            y = xvals(self.ImageWindow.yprofile)
            Iy = yvals(self.ImageWindow.yprofile)
            header = "Beam size: %.3f x %.3f mm FWHM" % self.ImageWindow.FWHM
            header += ", Linearity correction: " + \
                str(self.ImageWindow.linearity_correction)
            labels="x[mm],Ix,y[mm],Iy"
            save ([x,Ix,y,Iy],filename,header,labels)
            self.filename = filename
        dlg.Destroy()

    def CopyImage(self,event):
        "Called from menu Edit/Copy Image"
        image = self.ImageWindow.TransformedImage
        # Convert image from numpy to WX data format.
        d,w,h = image.shape
        wximage = wx.Image(w,h)
        data = image.T.tobytes()
        wximage.Data = data
        # Put image data as "Bitmap" data object into the clipboard.
        bitmap = wx.Image (wximage)
        bmpdo = wx.BitmapDataObject(bitmap)
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(bmpdo)
            wx.TheClipboard.Close()
        else: wx.MessageBox("Unexpected clipboard problem","Error")

    def OnOrientation(self,event):
        id = event.GetId()
        if id == 301: self.Orientation = 0   # As camera
        if id == 302: self.Orientation = -90 # Rotated Clockwise
        if id == 303: self.Orientation = +90 # Rotated Counter-clockwise
        if id == 304: self.Orientation = 180 # Upside down
        if id == 305: self.Mirror = not self.Mirror # Toggle mirror image on/off

    def OnViewerOptions(self,event):
        """Configure scale and zoom"""
        dlg = ViewerOptions(self)
        dlg.CenterOnParent()
        dlg.Show()         

    def OnCameraOptions(self,event):
        """Configure acqusition"""
        dlg = CameraOptions(self)
        dlg.CenterOnParent()
        dlg.Show()         

    def OnOpticsOptions(self,event):
        """Configure scale and zoom"""
        dlg = OpticsOptions(self)
        dlg.CenterOnParent()
        dlg.Show()         

    def OnAbout(self,event):
        """Show version info"""
        from About import About
        About(self)
        
        # Using "AboutBox" (requires wxPython 2.8)
        #info = wx.AboutDialogInfo()
        #info.Name = "CameraViewer.py"
        #info.Version = self.version
        #info.Copyright = ""
        #info.Description = \
        #    "Grapical User Interface for Prosilia GigE cameras."
        #info.WebSite = ("http://femto.niddk.nih.gov/APS/Software/python", "Home Page")
        #info.Developers = [ "Friedrich Schotte"]
        #info.License = wordwrap("Public Domain", 500, wx.ClientDC(self))
        #wx.AboutBox(info)        

    def OnExit(self,event):
        """Called on File/Exit"""
        self.Show(False)
        self.Destroy()

    def OnClose(self,event):
        """Called when the widnows's close button is clicked"""
        self.Show(False)
        if DEBUG: app.ExitMainLoop() # for debugging
        else: self.Destroy()

    def OnPointerFunction(self,name,x,y,event):
        """Called when the left mouse button is pressed and a custom pointer
        Fcuntion is activated.
        (x,y) position of pointer relative to crosshair
        event: 'down','drag' or 'up'"""
        ##print("%s (%g,%g) mm" % (name,x,y))

    settings = ["Size","Position","ScaleFactor","ZoomLevel","Orientation","Mirror",
        "NominalPixelSize","filename",
        "ImageWindow.Center","ImageWindow.ViewportCenter",
        "ImageWindow.crosshair_color","ImageWindow.boxsize",
        "ImageWindow.box_color","ImageWindow.show_box","ImageWindow.Scale",
        "ImageWindow.show_scale","ImageWindow.scale_color",
        "ImageWindow.crosshair_size","ImageWindow.show_crosshair",
        "ImageWindow.show_profile","ImageWindow.show_FWHM",
        "ImageWindow.show_center","ImageWindow.calculate_section",
        "ImageWindow.profile_color","ImageWindow.FWHM_color",
        "ImageWindow.center_color","ImageWindow.ROI",
        "ImageWindow.ROI_color","ImageWindow.show_saturated_pixels",
        "ImageWindow.mask_bad_pixels","ImageWindow.saturation_threshold",
        "ImageWindow.saturated_color","ImageWindow.linearity_correction",
        "ImageWindow.bad_pixel_threshold","ImageWindow.bad_pixel_color",
        "ImageWindow.show_grid","ImageWindow.grid_type",
        "ImageWindow.grid_color",
        "ImageWindow.grid_x_spacing","ImageWindow.grid_x_offset",
        "ImageWindow.grid_y_spacing","ImageWindow.grid_y_offset",
        ]

    def update_settings(self,event=None):
        "Monitors the settings file and reloads it if it is updated."
        if mtime(self.settings_file()) != self.settings_timestamp:
            self.ReadSettings()
        elif not hasattr(self,"saved_state") or self.saved_state != self.State:
            self.SaveSettings()

        self.UpdateMask()

        # Relaunch this procedure after 2 s
        self.settings_timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.update_settings,self.settings_timer)
        self.settings_timer.Start(2000,oneShot=True)

    def ReadSettings(self):
        "Load preferences from a file"
        if exists(self.settings_file()):
            self.State = open(self.settings_file()).read()
        self.saved_state = self.State
        self.settings_timestamp = mtime(self.settings_file())
        
        self.ImageWindow.ScaleFactor = self.ScaleFactor
        
    def SaveSettings(self):
        "Save defaults for next time"
        if not exists(self.settings_dir()): makedirs(self.settings_dir())
        open(self.settings_file(),"w").write(self.State)
        
        self.saved_state = self.State
        self.settings_timestamp = mtime(self.settings_file())
        
    def UpdateMask(self):
        from os.path import exists; from os import remove
        if not hasattr(self,"mask_file_timestamp"): self.mask_file_timestamp = 0
        if not hasattr(self,"bad_pixel_count"): self.bad_pixel_count = 0

        mask_file = self.settings_file().replace("_settings.py",
            "_bad_pixel_mask.png")

        if exists(mask_file) and mtime(mask_file) != self.mask_file_timestamp:
            wximage = wx.Image(mask_file)
            data = wximage.Data
            w,h = wximage.Width,wximage.Height
            from numpy import frombuffer,uint8,any
            image = frombuffer(data,uint8).reshape(h,w,3).T
            mask = any(image > 0,axis=0)
            self.ImageWindow.Mask = mask
            self.mask_file_timestamp = mtime(mask_file)

        if self.bad_pixel_count != self.ImageWindow.BadPixelCount:
            if self.ImageWindow.BadPixelCount > 0:
                self.ImageWindow.Mask.SaveFile(mask_file,wx.BITMAP_TYPE_PNG)
                self.mask_file_timestamp = mtime(mask_file)
            self.bad_pixel_count != self.ImageWindow.BadPixelCount
        if self.ImageWindow.BadPixelCount == 0:
            if exists(mask_file): remove(mask_file)
            self.mask_file_timestamp = 0

    def GetState(self):
        state = ""
        for attr in self.settings:
            line = attr+" = "+repr(eval("self."+attr))
            state += line+"\n"
        return state
    def SetState(self,state):
        for line in state.split("\n"):
            line = line.strip(" \n\r")
            if line != "":
                try: exec("self."+line)
                except: warning("ignoring line %r" % line); pass
    State = property(GetState,SetState)
        
    def settings_file(self):
        """pathname of the file used to store persistent parameters"""
        return self.settings_dir()+"/"+self.name+"_settings.py"

    def settings_dir(self):
        """pathname of the file used to store persistent parameters"""
        from os.path import dirname
        path = module_dir()+"/settings"
        return path

    def __repr__(self): return "CameraViewer(%r)" % self.name
    
    
class ImageWindow(wx.ScrolledWindow):
    def __init__(self,parent,pixelsize=1.0,**options):
        """pixelsize: in units of mm; used for measurements"""
        wx.ScrolledWindow.__init__(self,parent,**options)

        from numpy import zeros,uint8
        self.source_image = zeros((3,1360,1024),uint8)
        self.mask = zeros((1360,1024),bool)
        self.image_scale = 1.0
        self.pixelsize = pixelsize
        
        self.show_crosshair = True
        self.crosshair_size = (0.05,0.05) # default crosshair size: 50x50 um
        self.crosshair_color = (255,0,255) # magenta
        self.dragging = ""
        self.scale = [(-0.1,-0.1),(-0.1,0.1)] # Measuement line drawn on the image, unit: mm
        self.scale_color = (128,128,255) # light blue
        self.show_scale = False # Draw measurement line drawn on the image?
        self.scale_selected = False
        self.boxsize = (0.1,0.06) # default box size: 100x60 um
        self.box_color = (128,128,255)
        self.show_box = False
        self.show_profile = False
        self.calculate_section = False # if False calculate projection
        self.section_width = 0.3 # fraction of FWHM
        self.profile_color = (255,0,255)
        self.show_FWHM = False
        self.FWHM_color = (0,0,255)
        self.show_center = False
        self.center_color = (0,0,255)
        self.click_centering_available = False
        self.show_grid = False
        self.grid_type = "xy"
        self.grid_x_spacing = 1.0 # mm
        self.grid_x_offset = 0.0 # mm with respect to the crosshair
        self.grid_y_spacing = 1.0 # mm
        self.grid_y_offset = 0.0 # mm with respect to the crosshair
        self.grid_color = (0,0,255)
        # Region of interest in mm (xmin,ymin),(xmax,ymax)
        self.ROI = [[-0.2,-0.2],[0.2,0.2]] 
        self.ROI_color = (255,255,0)
        self.show_saturated_pixels = False
        self.saturation_threshold = 233 # uncorrectable nonliniearity starts here
        self.saturated_color = (255,0,0) # used for marking saturated pixels
        self.linearity_correction = False # compensate signal compression of CCD
        self.use_channels = (1,1,1) # use all channels R,G,B
        self.mask_bad_pixels = False
        self.bad_pixel_threshold = 233 # used for masking of damaged pixels
        self.bad_pixel_color = (30,30,30) # used for marking damaged pixels
        self.pointer_functions = [] # use define actions of the mouse
        self.tool = "" # Role of mouse pointer: measure, move crosshair
        self.objects = {} # custom shapes to be drawn on top of the image
        self.object_colors = {} # color for each member of objects
        self.object_type = {} # "square" or "line"
        self.show_object = {} # whether each object is shown or not

        self.SetVirtualSize((self.ImageWidth,self.ImageHeight))
        self.SetScrollRate(1,1)

        self.Bind (wx.EVT_PAINT, self.OnPaint)
        self.Bind (wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind (wx.EVT_SIZE, self.OnResize)
        self.Bind (wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind (wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind (wx.EVT_MOTION, self.OnMotion)
        self.Bind (wx.EVT_CONTEXT_MENU, self.OnContextMenu)

    @property
    def scale_unit(self):
        if self.pixelsize == 1.0: return "pixels"
        else: return "mm"

    def GetImageWidth(self):
        """Horizonal size of rotated image in pixels"""
        angle = self.Orientation
        from numpy import rint
        angle = rint((angle % 360)/90.)*90
        d,w,h = self.source_image.shape
        if angle == 0 or angle == 180: return w
        else: return h
    ImageWidth = property(GetImageWidth)

    def GetImageHeight(self):
        """Vertical size of rotated image in pixels"""
        angle = self.Orientation
        from numpy import rint
        angle = rint((angle % 360)/90.)*90
        d,w,h = self.source_image.shape
        if angle == 0 or angle == 180: return h
        else: return w
    ImageHeight = property(GetImageHeight)

    def GetImage(self):
        """Image without rotation applied."""
        return self.source_image
    def SetImage(self,image):
        self.source_image = image
        w = self.ImageWidth * self.ScaleFactor
        h = self.ImageHeight * self.ScaleFactor
        self.SetVirtualSize ((w,h))
        if self.show_profile or self.show_FWHM or self.show_center:
            self.calculate_profile()
        self.Refresh()
    Image = property(GetImage,SetImage)

    def GetTransformedImage(self):
        """Image in orientation as displayed"""
        return self.transform_image(self.Image,self.Orientation,self.Mirror)
    def SetTransformedImage(self,image):
        self.Image = self.back_transform_image(image,self.Orientation,self.Mirror)
    TransformedImage = property(GetTransformedImage,SetTransformedImage)

    def GetMask(self):
        """bitmap identifing "bad pixels" """
        return self.mask
    def SetMask(self,mask):
        self.mask = mask
        self.Refresh()
    Mask = property(GetMask,SetMask)

    def GetBadPixelCount(self):
        """How many bad pixels are there?"""
        from numpy import sum
        return sum(self.Mask != 0)
    BadPixelCount = property(GetBadPixelCount)

    def GetTransformedMask(self):
        """Bad pixel bitmap in orientation as displayed"""
        return self.transform_mask(self.Mask,self.Orientation,self.Mirror)
    def SetTransformedMask(self,mask):
        self.Mask = self.back_transform_mask(mask,-self.Orientation,self.Mirror)
    TransformedMask = property(GetTransformedMask,SetTransformedMask)

    def GetOrientation(self):
        """Image rotation in deg: 0, -90, 90 or 180"""
        if hasattr(self,"orientation"): return self.orientation
        else: return 0
    def SetOrientation(self,value):
        self.orientation = value
        if self.show_profile or self.show_FWHM or self.show_center:
            self.calculate_profile()
        self.Refresh()
    Orientation = property (GetOrientation,SetOrientation)

    def GetMirror(self):
        if hasattr(self,"mirror"): return self.mirror
        else: return 0
    def SetMirror(self,value):
        self.mirror = value
        if self.show_profile or self.show_FWHM or self.show_center:
            self.calculate_profile()
        self.Refresh()
    Mirror = property (GetMirror,SetMirror)

    def GetPixelSize(self):
        """in mm"""
        return self.pixelsize
    def SetPixelSize(self,value):
        self.pixelsize = value
        if self.show_profile or self.show_FWHM or self.show_center:
            self.calculate_profile()
        self.Refresh()
    PixelSize = property (GetPixelSize,SetPixelSize)

    def GetScaleFactor(self):
        """Scale factor applied to image for display"""
        scale = self.image_scale
        if scale == None: # Fit image into the width of the window
            if self.ImageWidth != 0:
                scale = float(self.GetClientSize().x)/self.ImageWidth
            else: scale = 1.0
        return scale
    def SetScaleFactor (self,value):
        # Preserve the viewport center when zooming in and out.
        center = self.ViewportCenter
        self.image_scale = value
        w = self.ImageWidth * self.ScaleFactor
        h = self.ImageHeight * self.ScaleFactor
        self.SetVirtualSize ((w,h))
        self.ViewportCenter = center
        self.Refresh()
    ScaleFactor = property(GetScaleFactor,SetScaleFactor)

    def GetViewportCenter(self):
        """Center (x,y) coordinates of the part of the image displayed in the
        window in mm with respect to the top left corner of the image."""
        w,h = self.GetClientSize()
        x0,y0 = self.GetViewStart()
        sx,sy = self.GetScrollPixelsPerUnit()
        ox,oy = self.origin()
        s = self.ScaleFactor
        dx = self.PixelSize
        cx,cy = (x0*sx-ox+w/2)/s*dx, (y0*sy-oy+h/2)/s*dx
        return cx,cy
    def SetViewportCenter(self,center):
        """Scroll such than the center the window is x mm from the
        left edge and y mm from the top edge of the image."""
        cx,cy = center
        w,h = self.GetClientSize()
        sx,sy = self.GetScrollPixelsPerUnit()
        ox,oy = self.origin()
        s = self.ScaleFactor
        dx = self.PixelSize
        
        x0 = cx/sx/dx*s-w/2+ox
        y0 = cy/sx/dx*s-h/2+oy
        self.Scroll(x0,y0)
    ViewportCenter = property(GetViewportCenter,SetViewportCenter)

    def GetImageSize(self):
        """Width and height of image in mm"""
        w,h = (self.ImageWidth,self.ImageHeight)
        return w*self.pixelsize,h*self.pixelsize
    ImageSize = property(GetImageSize)
    
    def GetImageOrigin(self):
        """Image center defined by crosshair in mm for botoom left corner"""
        x,y = self.Crosshair
        w,h = (self.ImageWidth,self.ImageHeight)
        return -x*self.pixelsize,-(h-y)*self.pixelsize
    ImageOrigin = property(GetImageOrigin)

    def GetCenter(self):
        """Coordinates of image center
        in pixels, as read from the center, without rotation applied"""
        if hasattr(self,"center"): return self.center
        else: return None
    def SetCenter (self,center):
        if not hasattr(self,"center") or self.center != center:
            self.center = center
            if self.show_profile or self.show_FWHM or self.show_center:
                self.calculate_profile()
            self.Refresh()
    Center = property(GetCenter,SetCenter)

    def GetCrosshair(self):
        """Coordinates of cross displayed on the image, in pixels, from top
        left, with rotation applied"""
        if self.Center: return self.transform(self.Center)
        else: return (self.ImageWidth/2,self.ImageHeight/2)
    def SetCrosshair (self,position):
        x,y = position
        if self.Center == None or self.Center != self.back_transform((x,y)):
            self.Center = self.back_transform((x,y))
    Crosshair = property(GetCrosshair,SetCrosshair)
    
    def GetScale(self):
        """Movable measurement line drawn
        on the image, format: list of tuples [(x1,y1),(x2,y2)]"""
        return self.scale
    def SetScale (self,line):
        self.scale = line
        self.Refresh()
    Scale = property(GetScale,SetScale)

    def GetGridXSpacing(self): return self.grid_x_spacing
    def SetGridXSpacing(self,value):
        if value != self.grid_x_spacing:
            self.grid_x_spacing = value
            self.Refresh()
    GridXSpacing = property(GetGridXSpacing,SetGridXSpacing)

    def GetGridXOffset(self): return self.grid_x_offset
    def SetGridXOffset(self,value):
        if value != self.grid_x_offset:
            self.grid_x_offset = value
            self.Refresh()
    GridXOffset = property(GetGridXOffset,SetGridXOffset)

    def GetGridYSpacing(self): return self.grid_y_spacing
    def SetGridYSpacing(self,value):
        if value != self.grid_y_spacing:
            self.grid_y_spacing = value
            self.Refresh()
    GridYSpacing = property(GetGridYSpacing,SetGridYSpacing)

    def GetGridYOffset(self): return self.grid_y_offset
    def SetGridYOffset(self,value):
        if value != self.grid_y_offset:
            self.grid_y_offset = value
            self.Refresh()
    GridYOffset = property(GetGridYOffset,SetGridYOffset)

    def GetPointerFunction(self):
        return self.tool
    def SetPointerFunction(self,name):
        if name: self.AddPointerFunction(name)
        self.tool = name
    PointerFunction = property(GetPointerFunction,SetPointerFunction)

    def AddPointerFunction(self,name):
        """Shows up as choice in the context menu"""
        if not name in self.pointer_functions:
            self.pointer_functions += [name]

    def AddObject(self,name,points=[],color=(0,0,255),type="squares"):
        """Add a custom shape to be drawn on top of the image.
        name: Displayed in show/hide context menu
        points: list if x,y pairs in mm corrdinates relative to
        the crosshair
        color: default color. Can be overriden from properties dialog.
        type: "squares" or "lines" """
        # Check if update is needed.
        if name in self.objects and self.objects[name] == points: return

        self.objects[name] = points
        if not name in self.object_colors: self.object_colors[name] = color
        if not name in self.object_type: self.object_type[name] = type
        if not name in self.show_object: self.show_object[name] = True
        self.Refresh()

    # To do: AddObjects - Add mutiple objects wth a single refresh

    def DeleteObject(self,name):
        """Remove a custom shape to be drawn on top of the image.
        name: Displayed in show/hide context menu"""
        if not name in self.objects: return # Check if update is needed.
        del self.objects[name]
        self.Refresh()

    def transform_image(self,image,angle,mirror):
        """Transform from raw to displayed to displayed image.
        image: 3D numpy array with dimensions 3 x width x height
        angle: in units of deg, positive = counterclockwise, must be a multiple
        of 90 deg
        Return value: rotated version of the input image"""
        from numpy import rint
        angle = rint((angle % 360)/90.)*90
        if mirror: image = image[:,::-1,:] # flip horizonally
        if angle == 90:  image = image.transpose(0,2,1)[:,:,::-1]
        if angle == 180: image = image[:,::-1,::-1]
        if angle == 270: image = image.transpose(0,2,1)[:,::-1,:]
        return image

    def back_transform_image(self,image,angle,mirror):
        """Transform from displayed to raw image.
        image: 3D numpy array with dimensions 3 x width x height
        angle: in units of deg, positive = counterclockwise, must be a multiple
        of 90 deg
        Return value: rotated version of the input image"""
        from numpy import rint
        angle = rint((angle % 360)/90.)*90
        if angle == 90: image = image.transpose(0,2,1)[:,::-1,:]
        if angle == 180: image = image[:,::-1,::-1]
        if angle == 270:  image = image.transpose(0,2,1)[:,:,::-1]
        if mirror: image = image[:,::-1,:] # flip horizonally
        return image

    def transform_mask(self,mask,angle,mirror):
        """Transform from raw to displayed to displayed image.
        mask: 2D numpy array dimensions width x height
        angle: in units of deg, positive = counterclockwise,
        must be a multiple of 90 deg
        Return value: rotated version of the input image"""
        from numpy import rint
        angle = rint((angle % 360)/90.)*90
        if mirror: mask = mask[::-1,:] # flip horizonally
        if angle == 90:  mask = mask.transpose(1,0)[:,::-1]
        if angle == 180: mask = mask[::-1,::-1]
        if angle == 270: mask = mask.transpose(1,0)[::-1,:]
        return mask

    def back_transform_mask(self,mask,angle,mirror):
        """Transform from raw to displayed to displayed image.
        mask: 2D numpy array dimensions width x height
        angle: in units of deg, positive = counterclockwise,
        must be a multiple of 90 deg
        Return value: rotated version of the input image"""
        from numpy import rint
        angle = rint((angle % 360)/90.)*90
        if angle == 90: mask = mask.transpose(1,0)[::-1,:]
        if angle == 180: mask = mask[::-1,::-1]
        if angle == 270:  mask = mask.transpose(1,0)[:,::-1]
        if mirror: mask = mask[::-1,:] # flip horizonally
        return mask

    def transform(self,position):
        """Transform coordinates (x,y) from raw to rotated image.
        Return value: (x,y)"""
        x,y = position
        angle = self.Orientation
        from numpy import rint
        angle = rint((angle % 360)/90.)*90
        w,h = self.source_image.shape[1:]
        if self.Mirror: x = w - x # flip horizonally
        if angle == 90:  x,y = y,w-x
        if angle == 180: x,y = w-x,h-y
        if angle == 270: x,y = h-y,x
        return x,y
        
    def back_transform(self,position):
        """Transform coordinates (x,y) from rotated image to raw image.
        Return value: (x,y)"""
        x,y = position
        angle = self.Orientation
        from numpy import rint
        angle = rint((angle % 360)/90.)*90
        w,h = self.source_image.shape[1:]
        if angle == 90:  x,y = w-y,x
        if angle == 180: x,y = w-x,h-y
        if angle == 270: x,y = y,h-x
        if self.Mirror: x = w - x # flip horizonally
        return x,y

    def origin(self):
        """By default, a Scrolled Window places its active area in the top
        left, if it is smaller than the window size.
        Instead, I want it centered in the window.
        The fucntion calculates the active area origin as function of window
        size."""
        width,height = self.ClientSize
        x = (width  - self.ImageWidth *self.ScaleFactor)/2
        y = (height - self.ImageHeight*self.ScaleFactor)/2
        if x<0: x = 0
        if y<0: y = 0
        return x,y

    def OnPaint (self,event):
        """Called by WX whenever the contents of the window
        needs re-rendering. E.g. when the window is brought to front,
        uncovered, restored from minimized state."""

        dc = wx.PaintDC(self)
        dc = wx.BufferedDC(dc) # avoids flickering
        self.PrepareDC(dc)
        
        # Need to fill the area no covered by the image
        # because automatic background erase was turned off.
        dc.SetBrush (wx.Brush("GREY"))
        dc.SetPen (wx.Pen("GREY",0))
        width,height = self.ClientSize
        dc.DrawRectangle (0,0,width,height)

        # This centers the image in the window, if the window is larger than
        # the image.
        ##debug("OnPaint: dc.DeviceOrigin: %r,%r" % dc.DeviceOrigin)
        xdo,ydo = dc.DeviceOrigin
        xo,yo = self.origin()
        if xdo == 0: xdo = xo
        if ydo == 0: ydo = yo
        dc.SetDeviceOrigin(xdo,ydo)
        ##debug("OnPaint: dc.DeviceOrigin: %r,%r" % dc.DeviceOrigin)
    
        self.draw(dc)

    def OnEraseBackground(self, event):
        "Overrides default background fill, avoiding flickering"

    def draw (self,dc):
        "This function is responsible for drawing the contents of the window."
        image = self.TransformedImage
        if self.show_saturated_pixels: image = self.highlight_saturated(image)
        if self.mask_bad_pixels:
            image = self.highlight(image,self.TransformedMask,self.bad_pixel_color)
        
        # Convert image from numpy to WX data format.
        ##wximage = wx.Image(self.ImageWidth,self.ImageHeight) # wx 4.0
        wximage = wx.Image(self.ImageWidth,self.ImageHeight)
        # wx 4.0: "deprecated item EmptyImage. Use class wx.Image instead."
        data = image.T.tobytes()
        wximage.SetData(data)
        # Scale the image.
        w = self.ImageWidth * self.ScaleFactor
        h = self.ImageHeight * self.ScaleFactor
        # Use "quality=wx.IMAGE_QUALITY_HIGH" for bicubic and box averaging
        # resampling methods for upsampling and downsampling respectively.
        wximage = wximage.Scale(w,h)

        ##bitmap = wx.Bitmap(wximage) # wx 4.0
        bitmap = wx.Image(wximage)
        # wx 4.0: "deprecated item BitmapFromImage. Use class wx.Bitmap instead."
        dc.DrawBitmap(bitmap,0,0)
        self.draw_objects(dc)
        self.draw_grid(dc)
        self.draw_crosshair(dc)
        self.draw_box(dc)
        #self.draw_circle(dc) : FIXIT
        self.draw_scale(dc)
        self.draw_profile(dc)

    def draw_grid (self,dc):
        "Indicates the X-ray beam position as a cross"
        if not self.show_grid: return
        dc.SetPen (wx.Pen(self.grid_color,1))
        w,h = self.ImageWidth*self.ScaleFactor,self.ImageHeight*self.ScaleFactor

        dx = self.grid_x_spacing; x0 = self.grid_x_offset
        if "x" in self.grid_type and dx != 0 and not isnan(dx):
            i = 0
            x = self.pixel((x0+i*dx,0))[0]
            while 0 <= x < w:
                dc.DrawLine(x,0,x,h)
                i += 1
                x = self.pixel((x0+i*dx,0))[0]
            i = -1
            x = self.pixel((x0+i*dx,0))[0]
            while 0 <= x < w:
                dc.DrawLine(x,0,x,h)
                i -= 1
                x = self.pixel((x0+i*dx,0))[0]

        dy = self.grid_y_spacing; y0 = self.grid_y_offset
        if "y" in self.grid_type and dy != 0 and not isnan(dy):
            i = 0
            y = self.pixel((0,y0+i*dy))[1]
            while 0 <= y < h:
                dc.DrawLine(0,y,w,y)
                i += 1
                y = self.pixel((0,y0+i*dy))[1]
            i = -1
            y = self.pixel((0,y0+i*dy))[1]
            while 0 <= y < h:
                dc.DrawLine(0,y,w,y)
                i -= 1
                y = self.pixel((0,y0+i*dy))[1]

    def draw_crosshair (self,dc):
        "Indicates the X-ray beam position as a cross"
        if self.show_crosshair:
            dc.SetPen (wx.Pen(self.crosshair_color,1))
            w,h = self.crosshair_size
            x1,y1 = self.pixel((-w/2,0)); x2,y2 = self.pixel((+w/2,0))
            dc.DrawLine (x1,y1,x2,y2)
            x1,y1 = self.pixel((0,-h/2)); x2,y2 = self.pixel((0,+h/2))
            dc.DrawLine (x1,y1,x2,y2)
            
    def draw_box (self,dc):      
        "Draws a box around the cross hair to indicate X-ray beam size."
        if self.show_box:
            w,h = self.boxsize
            x1,y1 = self.pixel((w/2,h/2))
            x2,y2 = self.pixel((-w/2,-h/2))
            dc.SetPen (wx.Pen(self.box_color,1))
            dc.DrawLines ([(x1,y1),(x2,y1),(x2,y2),(x1,y2),(x1,y1)])

    def draw_scale (self,dc):
        "draw a line labeled with its length in um or mm"
        if not self.show_scale: return
        P1,P2 = self.scale
        x1,y1 = self.pixel(P1)
        x2,y2 = self.pixel(P2)
        dc.SetPen (wx.Pen(self.scale_color,1))
        dc.DrawLine (x1,y1,x2,y2)

        length = distance(P1,P2)
        if self.scale_unit == "mm":
            if length < 1: label = "%.0f um" % (length*1000)
            else: label = "%.3f mm" % length
        else: label = "%g %s" % (length,self.scale_unit)
        font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        font.SetPointSize(10)
        dc.SetFont(font)
        dc.SetTextForeground(self.scale_color)
        w,h = dc.GetTextExtent(label)
        cx = (x1+x2)/2; cy = (y1+y2)/2
        phi = atan2(y2-y1,x2-x1)
        tx = cx - (w/2*cos(phi) - h*sin(phi))
        ty = cy - (h*cos(phi) + w/2*sin(phi)) 
        dc.DrawRotatedText (label,tx,ty,-phi/pi*180)

        if self.scale_selected: # Highlight the end points by 5x5 pixel squares
            dc.DrawRectangle(x1-2,y1-2,4,4)
            dc.DrawRectangle(x2-2,y2-2,4,4)

    def draw_circle (self, dc): #FIXIT: function is not tested. Sept 28, 2018
        """
        draws a circle
        the circle can be drawn by passing the center coordinates: x,y and radius
        """
        if self.show_circle:
            w,h = self.circlesize
            dc.SetPen (wx.Pen(self.box_color,1))
            dc.DrawCircle(x = 0 , y = 0, radius = 1)
            

    def draw_objects (self,dc):
        "Draw custom shapes on top of the image"
        # Draw it as a cloud of points, without connecting them.
        for name in self.objects:
            if not self.show_object[name]: continue
            color = self.object_colors[name]
            type = self.object_type[name]
            dc.SetPen(wx.Pen(color,1))
            dc.SetBrush(wx.Brush(color))
            points = self.objects[name]
            if type == "squares":
                for point in points:
                    x,y = self.pixel(point)
                    dc.DrawRectangle(int32(x-1),int32(y-1),3,3)
            if type == "line":
                segments = [self.pixel(p) for p in points]
                if len(segments) > 1: dc.DrawLines(segments)

    def calculate_profile(self):
        "Updates the beam profile"
        from numpy import array,nan,isnan,minimum,log,where,sum,nansum
        
        RGB = self.TransformedImage
        
        # Get the region of interest
        ROI = self.ROI
        cx,cy = self.Crosshair
        dx = dy = self.pixelsize
        xmin = int(round(ROI[0][0]/dx+cx)) ; xmax = int(round(ROI[1][0]/dx+cx))
        ymin = int(round(cy-ROI[1][1]/dy)) ; ymax = int(round(cy-ROI[0][1]/dy))
        if xmin > xmax: xmin,xmax = xmax,xmin
        if ymin > ymax: ymin,ymax = ymax,ymin
        ##print("ROI [%d:%d,%d:%d]" % (xmin,xmax,ymin,ymax))
        RGB = RGB[:,xmin:xmax,ymin:ymax]

        # Mask bad pixels by setting them to NaN.
        RGB = RGB.astype(float)
        if self.mask_bad_pixels: 
            mask = self.TransformedMask[xmin:xmax,ymin:ymax]
            R,G,B = RGB
            R[mask],G[mask],B[mask] = nan,nan,nan
        
        # Apply linearity correction individually to R,G,and B channels,
        # then add up the intensities of the channels.
        if self.linearity_correction:
            # Build linearity correction table
            T = float(self.saturation_threshold) # 0 to 255
            def linearize(i): return -log(1-minimum(i,T)/(T+1))*(T+1)
            RGB = linearize(RGB)

        # Select which channels to use.
        r,g,b = self.use_channels
        R,G,B = RGB
        I = r*R + b*B + g*G

        # Generate projection on the X and Y axis.
        xproj = nansum(I,axis=1)/sum(~isnan(I),axis=1)
        yproj = nansum(I,axis=0)/sum(~isnan(I),axis=0)
        # Scale projections in units of mm.
        xscale = [(xmin+i-cx)*dx for i in range(0,len(xproj))]
        yscale = [(cy-(ymin+i))*dy for i in range(0,len(yproj))]
        self.xprofile = list(zip(xscale,xproj))
        self.yprofile = list(zip(yscale,yproj))
        
        if self.calculate_section:
            # Calculate X and Y sections through the peak.
            # This is done by intergrating of a strip that is a certain fraction
            # of the FWHM wide, detemined by the parameter "section_width".
            xprofile = list(zip(list(range(0,len(xproj))),xproj))
            yprofile = list(zip(list(range(0,len(yproj))),yproj))
            W,H = FWHM(xprofile),FWHM(yprofile)
            CX,CY = CFWHM(xprofile),CFWHM(yprofile)
            frac = self.section_width/2
            x1,x2 = int(round(CX-W*frac)),int(round(CX+W*frac))
            y1,y2 = int(round(CY-H*frac)),int(round(CY+H*frac))
            xstrip = I[:,y1:y2+1]
            ystrip = I[x1:x2+1,:]
            xsect = nansum(xstrip,axis=1)/sum(~isnan(xstrip),axis=1)
            ysect = nansum(ystrip,axis=0)/sum(~isnan(ystrip),axis=0)
            self.xprofile = list(zip(xscale,xsect))
            self.yprofile = list(zip(yscale,ysect))
            (xr1,yr1),(xr2,yr2) = self.ROI
            left,bottom = min(xr1,xr2),min(yr1,yr2)
            self.section = left+x1*dx,left+x2*dx,bottom+y1*dy,bottom+y2*dy

        self.FWHM = (FWHM(self.xprofile),FWHM(self.yprofile))
        self.CFWHM =(CFWHM(self.xprofile),CFWHM(self.yprofile))

    def draw_profile (self,dc):
        """Beam profile analyzer.
        Draws a FWHM with dimensions box around the beam center,
        horzontal and vertcal beam projections or sections on the left and
        bottom edge of the image"""

        if (self.show_profile or self.show_FWHM) and self.calculate_section and hasattr(self,"section"):
            # Mark the width of the strip that was used to calculate a section
            dc.SetPen (wx.Pen(self.profile_color,1,wx.DOT))
            x1,x2,y1,y2 = self.section
            left,bottom = self.ROI[0]
            right,top = self.ROI[1]
            dc.DrawLines ([self.pixel((x1,bottom)),self.pixel((x1,top))])
            dc.DrawLines ([self.pixel((x2,bottom)),self.pixel((x2,top))])
            dc.DrawLines ([self.pixel((left,y1)),self.pixel((right,y1))])
            dc.DrawLines ([self.pixel((left,y2)),self.pixel((right,y2))])

        if self.show_profile and hasattr(self,"xprofile") and hasattr(self,"yprofile"):
            # Draw beam profiles at the edge of the image.
            dc.SetPen (wx.Pen(self.profile_color,1))
            w = self.ImageWidth*self.pixelsize
            h = self.ImageHeight*self.pixelsize
            cx = self.Crosshair[0]*self.pixelsize
            cy = h-self.Crosshair[1]*self.pixelsize
            # Draw horizontal profile at the bottom edge of the ROI box.
            try: scale = 0.35*(self.ROI[1][1]-self.ROI[0][1])/max(yvals(self.xprofile))
            except: scale = 1
            offset = self.ROI[0][1]
            x = xvals(self.xprofile); y = yvals(self.xprofile)
            lines = []
            for i in range(0,len(x)-1):
                if not isnan(y[i]) and not isnan(y[i+1]):
                    p1 = self.pixel((x[i],y[i]*scale+offset))
                    p2 = self.pixel((x[i+1],y[i+1]*scale+offset))
                    lines += [(p1[0],p1[1],p2[0],p2[1])]
            dc.DrawLineList(lines)
            # Draw vertical profile at the left edge of the ROI box.
            try: scale = 0.35*(self.ROI[1][0]-self.ROI[0][0])/max(yvals(self.yprofile))
            except: scale = 1
            offset = self.ROI[0][0]
            x = xvals(self.yprofile); y = yvals(self.yprofile)
            lines = []
            for i in range(0,len(x)-1):
                if not isnan(y[i]) and not isnan(y[i+1]):
                    p1 = self.pixel((y[i]*scale+offset,x[i]))
                    p2 = self.pixel((y[i+1]*scale+offset,x[i+1]))
                    lines += [(p1[0],p1[1],p2[0],p2[1])]
            dc.DrawLineList(lines)

        if self.show_FWHM and hasattr(self,"FWHM") and hasattr(self,"CFWHM"):
            # Draw a box around center of the beam, with the size of the FWHM.
            width,height = self.FWHM
            cx,cy = self.CFWHM
            x1,y1 = self.pixel((cx-width/2,cy-height/2))
            x2,y2 = self.pixel((cx+width/2,cy+height/2))
            dc.SetPen (wx.Pen(self.FWHM_color,1))
            dc.DrawLines ([(x1,y1),(x2,y1),(x2,y2),(x1,y2),(x1,y1)])

            # Annotate the FWHM box with dimensions.
            font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
            font.SetPointSize(10)
            dc.SetFont(font)
            dc.SetTextForeground(self.FWHM_color)

            if self.scale_unit == "mm":
                if width < 1: label = "%.0f um" % (width*1000)
                else: label = "%.3f mm" % width
            else: label = "%g %s" % (width,self.scale_unit)
            w,h = dc.GetTextExtent(label)
            cx = (x1+x2)/2; cy = y2
            dc.DrawRotatedText (label,cx-w/2,cy-h,0)
            
            if self.scale_unit == "mm":
                if width < 1: label = "%.0f um" % (height*1000)
                else: label = "%.3f mm" % height
            else: label = "%g %s" % (height,self.scale_unit)
            w,h = dc.GetTextExtent(label)
            cx = x2; cy = (y1+y2)/2
            dc.DrawRotatedText (label,cx+h,cy-w/2,-90)

        if self.show_center and hasattr(self,"CFWHM"):
            # Draw a vertical and horizontal line throught the center.
            cx,cy = self.CFWHM
            left,bottom = self.ROI[0]
            right,top = self.ROI[1]
            dc.SetPen (wx.Pen(self.center_color,1))
            dc.DrawLines ([self.pixel((cx,bottom)),self.pixel((cx,top))])
            dc.DrawLines ([self.pixel((left,cy)),self.pixel((right,cy))])

            # Annotate the lines.
            font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
            font.SetPointSize(10)
            dc.SetFont(font)
            dc.SetTextForeground(self.center_color)

            if self.scale_unit == "mm":
                if abs(cx) < 1: label = "%+.0f um" % (cx*1000)
                else: label = "%+.3f mm" % cx
            else: label = "%+g %s" % (cx,self.scale_unit)
            x,y = self.pixel((cx,0.825*bottom+0.175*top))
            w,h = dc.GetTextExtent(label)
            dc.DrawRotatedText (label,x+2,y-h/2,0)

            if self.scale_unit == "mm":
                if abs(cy) < 1: label = "%+.0f um" % (cy*1000)
                else: label = "%+.3f mm" % cy
            else: label = "%+g %s" % (cy,self.scale_unit)
            x,y = self.pixel((0.825*left+0.175*right,cy))
            w,h = dc.GetTextExtent(label)
            dc.DrawRotatedText (label,x-h/2,y+2,-90)
            
        if self.show_profile or self.show_FWHM:
            # Draw box around Region of Interest
            x1,y1 = self.pixel(self.ROI[0])
            x2,y2 = self.pixel(self.ROI[1])
            dc.SetPen (wx.Pen(self.ROI_color,1))
            dc.DrawLines ([(x1,y1),(x2,y1),(x2,y2),(x1,y2),(x1,y1)])

    def highlight(self,image,mask,color):
        """Substitutes the value of masked pixels with the specified color.
        image type: wx.Image, mask type: wx.Image, color type: (R,G,B)"""
        new_image = image.copy()
        R,G,B = new_image
        R[mask],G[mask],B[mask] = color[0:3]
        return new_image

    def highlight_saturated(self,image):
        """Substitute the value of saturated pixels with the color specified
        by "saturated_color".
        image: RGB pixel data as 3D numpy array with dimensions
        3 x width x height."""
        from numpy import any,array
        threshold = self.saturation_threshold
        # Pixel not saturated: mask = 0, saturated: mask = 1
        mask = any(image > threshold,axis=0)
        return self.highlight(image,mask,self.saturated_color)

    def bad_pixel_mask(self,image):
        """Pixels of which either R,G or B exceed the intensity defined by
        "bad_pixel_threshold".
        This is intended to mask "damaged" pixels with an unusually high dark
        current, which show up as "hot spots" in a dark image.
        image: RGB pixel data as 3D numpy array with dimensions
        3 x width x height.
        Return value: 2D numpy array of type boolean
        with the same width and height as the input image.
        """
        from numpy import any
        threshold = self.bad_pixel_threshold
        # Pixel not saturated: mask = 0, saturated: mask = 1
        mask = any(image > threshold,axis=0)
        return mask

    def update_bad_pixels (self):
        """This defined all saturated pixels as bad pixels and updates the mask.
        """
        self.TransformedMask = self.bad_pixel_mask(self.TransformedImage)
        self.calculate_profile()
        self.Refresh()
        
    def pixel(self,position):
        """Convert from mm to pixel coordinates"""
        x,y = position
        from numpy import rint,nan_to_num
        cx,cy = self.Crosshair
        px = int32(nan_to_num(rint((x/self.pixelsize+cx)*self.ScaleFactor)))
        py = int32(nan_to_num(rint((-y/self.pixelsize+cy)*self.ScaleFactor)))
        return [px,py]

    def point(self,position):
        """Convert from pixel coordinates to mm"""
        px,py = position
        cx,cy = self.Crosshair
        x = (px/self.ScaleFactor-cx)*self.pixelsize
        y = -(py/self.ScaleFactor-cy)*self.pixelsize
        return [x,y]

    def OnResize (self,event):
        w = self.ImageWidth * self.ScaleFactor
        h = self.ImageHeight * self.ScaleFactor
        self.SetVirtualSize ((w,h))
        self.Refresh()

    def OnLeftDown (self,event):
        """for dragging the crosshair or scale
        called when the left mouse button is pressed or relased or the
        mouse is moved.
        """
        
        p = self.cursor_pos(event)

        if self.MoveCrosshair:    
            self.SetFocus()
            self.set_crosshair(event)
            self.CaptureMouse()
            self.dragging = "crosshair"
        else:
            if self.tool == "measure":
                P = self.point(p)
                self.scale = [P,P]
                self.show_scale = True
                self.dragging = "scale end"
                self.scale_selected = False
            if self.tool in self.pointer_functions:
                x,y = self.point(self.cursor_pos(event))
                self.Parent.Parent.OnPointerFunction(self.tool,x,y,"down")
            else:
                self.scale_selected = (self.shape(p).find("scale") >= 0)
                self.dragging = self.shape(p)
                self.drag_info = (self.point(p),list(self.scale))
            if self.dragging:
                self.SetFocus()
                self.drag_shape(event)
                self.CaptureMouse()
        self.set_cursor(event)

    def OnMotion (self,event):
        """for dragging the crosshair or scale
        called when the left mouse button is pressed or relased or the
        mouse is moved.
        """
        self.set_cursor(event)

        if self.MoveCrosshair and event.Dragging() and self.dragging:
            self.set_crosshair(event)
        elif event.Dragging() and self.dragging:
            self.drag_shape(event)
        if event.Dragging() and self.tool in self.pointer_functions:
            x,y = self.point(self.cursor_pos(event))
            self.Parent.Parent.OnPointerFunction(self.tool,x,y,"drag")

    def OnLeftUp (self,event):
        """for dragging the crosshair or scale
        called when the left mouse button is pressed or relased or the
        mouse is moved.
        """        
        self.set_cursor(event)

        if self.dragging: self.ReleaseMouse()
        self.dragging = ""

        if self.tool in self.pointer_functions:
            x,y = self.point(self.cursor_pos(event))
            self.Parent.Parent.OnPointerFunction(self.tool,x,y,"up")

        if self.show_profile or self.show_FWHM or self.show_center:
            self.calculate_profile()

        self.Refresh()
    
    def set_cursor(self,event):        
        "Updates the pointer shape to reflect the mouse function."
        p = self.cursor_pos(event)
        shape = self.shape(p)
        if self.MoveCrosshair:    
            self.SetCursor (wx.Image(wx.CURSOR_PENCIL))
        elif self.tool == "measure":
            self.SetCursor (wx.Image(wx.CURSOR_PENCIL))
        elif self.tool in self.pointer_functions:    
            self.SetCursor (crosshair_cursor())
        elif self.dragging == "scale start" or self.dragging == "scale end":
            self.SetCursor (wx.Image(wx.CURSOR_SIZENESW))
        elif self.dragging: self.SetCursor(wx.Image(wx.CURSOR_SIZING))
        elif self.scale_selected and (self.shape(p) == "scale start" or self.shape(p) == "scale end"):
            self.SetCursor(wx.Image(wx.CURSOR_SIZENESW))
        elif shape == "scale":
            self.SetCursor(wx.Image(wx.CURSOR_SIZING))
        elif shape == "ROI xmin,ymin" or shape == "ROI xmax,ymax":
            self.SetCursor(wx.Image(wx.CURSOR_SIZENESW))
        elif shape == "ROI xmax,ymin" or shape == "ROI xmin,ymax":
            self.SetCursor(wx.Image(wx.CURSOR_SIZENWSE))
        elif shape.find("ROI x") != -1:
            self.SetCursor(wx.Image(wx.CURSOR_SIZEWE))
        elif shape.find("ROI y") != -1:
            self.SetCursor(wx.Image(wx.CURSOR_SIZENS))
        else: self.SetCursor (wx.Image(wx.CURSOR_DEFAULT))

        # CURSOR_CROSS would be better than CURSOR_PENCIL.
        # However, under Windows, the cross cursor does not have a white
        # border and is hard to see on black background.
        # CURSOR_SIZENESW would be better when the pointer is hovering over
        # the end of the end point.
        # However, under Linux, the pointer shape does not update
        # to CURSOR_PENCIL while dragging, only after the mouse button is
        # released.
        # CURSOR_CROSS would be better than CURSOR_PENCIL.
        # However, under Windows, the cross cursor does not have a white
        # border and is hard to see on black background.

    def drag_shape (self,event):
        "Updates the scale based on the last mouse event"
        p = self.cursor_pos(event)
        P = self.point(p)

        if self.dragging   == "scale start": self.scale[0] = P
        elif self.dragging == "scale end": self.scale[1] = P
        elif self.dragging == "scale":
            P0,(P1,P2) = self.drag_info
            self.scale[0] = translate(P1,vector(P0,P))
            self.scale[1] = translate(P2,vector(P0,P))
        elif self.dragging == "ROI xmin": self.ROI[0][0] = P[0]
        elif self.dragging == "ROI xmax": self.ROI[1][0] = P[0]
        elif self.dragging == "ROI ymin": self.ROI[0][1] = P[1]
        elif self.dragging == "ROI ymax": self.ROI[1][1] = P[1]
        elif self.dragging == "ROI xmin,ymin": self.ROI[0] = P
        elif self.dragging == "ROI xmax,ymax": self.ROI[1] = P
        elif self.dragging == "ROI xmax,ymin": self.ROI[1][0],self.ROI[0][1] = P
        elif self.dragging == "ROI xmin,ymax": self.ROI[0][0],self.ROI[1][1] = P
        self.Refresh()

    def shape (self,cursor_pos):
        """Tell over which which of the displayed object, like scale, ROI the
        cursor_pos is close to (within 4 pixels).
        cursor_pos is in units of pixels
        "scale" = line of scale
        "scale start","scale end" = endpoints of scale
        "ROI xmin" = side of Region of interest
        "ROI xmin,ymin" = corner of Region of interest
        """
        p = cursor_pos
        if self.show_scale and self.scale != None:
            p1,p2 = self.pixel(self.scale[0]),self.pixel(self.scale[1])
            if distance(p1,p) < 4: return "scale start"
            if distance(p2,p) < 4: return "scale end"
            if point_line_distance(p,(p1,p2)) < 5: return "scale"
        if self.show_profile or self.show_FWHM  or self.show_FWHM:
            xmin,ymin = self.pixel(self.ROI[0])
            xmax,ymax = self.pixel(self.ROI[1])
            if distance((xmin,ymin),p) < 4: return "ROI xmin,ymin"
            if distance((xmax,ymin),p) < 4: return "ROI xmax,ymin"
            if distance((xmin,ymax),p) < 4: return "ROI xmin,ymax"
            if distance((xmax,ymax),p) < 4: return "ROI xmax,ymax"
            if point_line_distance(p,((xmin,ymin),(xmax,ymin))) < 5: return "ROI ymin"
            if point_line_distance(p,((xmax,ymin),(xmax,ymax))) < 5: return "ROI xmax"
            if point_line_distance(p,((xmax,ymax),(xmin,ymax))) < 5: return "ROI ymax"
            if point_line_distance(p,((xmin,ymax),(xmin,ymin))) < 5: return "ROI xmin"
        return ""
                                    
    def set_crosshair (self,event):
        "Updates the crosshair position based on the last mouse event"
        x,y = self.cursor_pos(event)
        self.Crosshair = (int(round(x/self.ScaleFactor)),int(round(y/self.ScaleFactor)))

    def cursor_pos (self,event):
        """Returns the cursorposition during the given event, taking into
        account the scrollbar position (but not the image scale factor)"""
        x,y = self.CalcUnscrolledPosition (event.GetX(),event.GetY())
        ox,oy = self.origin()
        return x-ox,y-oy

    def OnContextMenu (self,event):
        menu = wx.Menu()
        menu.Append (1,"Show Scale","",wx.ITEM_CHECK)
        if self.show_scale: menu.Check(1,True)
        self.Bind (wx.EVT_MENU,self.OnShowScale,id=1)
        menu.Append (2,"Show Box","",wx.ITEM_CHECK)
        if self.show_box: menu.Check(2,True)
        self.Bind (wx.EVT_MENU,self.OnShowBox,id=2)
        menu.Append (6,"Show Crosshair","",wx.ITEM_CHECK)
        if self.show_crosshair: menu.Check(6,True)
        self.Bind (wx.EVT_MENU,self.OnShowCrosshair,id=6)
        menu.Append (22,"Show Grid","",wx.ITEM_CHECK)
        if self.show_grid: menu.Check(22,True)
        self.Bind (wx.EVT_MENU,self.OnShowGrid,id=22)
        menu.Append (9,"Show Beam Profile","",wx.ITEM_CHECK)
        if self.show_profile: menu.Check(9,True)
        self.Bind (wx.EVT_MENU,self.OnShowProfile,id=9)
        menu.Append (14,"Show Beam FWHM","",wx.ITEM_CHECK)
        if self.show_FWHM: menu.Check(14,True)
        self.Bind (wx.EVT_MENU,self.OnShowFWHM,id=14)
        menu.Append (17,"Show Center Line","",wx.ITEM_CHECK)
        if self.show_center: menu.Check(17,True)
        self.Bind (wx.EVT_MENU,self.OnShowCenter,id=17)
        menu.Append (11,"Show Saturated Pixels","",wx.ITEM_CHECK)
        if self.show_saturated_pixels: menu.Check(11,True)
        self.Bind (wx.EVT_MENU,self.OnShowSaturatedPixels,id=11)
        menu.Append (18,"Mask Bad Pixels","",wx.ITEM_CHECK)
        if self.mask_bad_pixels: menu.Check(18,True)
        self.Bind (wx.EVT_MENU,self.OnMaskBadPixels,id=18)

        for i in range(0,len(self.objects)):
            name = list(self.objects.keys())[i]
            id = 200+i
            menu.Append (id,name,"",wx.ITEM_CHECK)
            if self.show_object[name]: menu.Check(id,True)
            self.Bind (wx.EVT_MENU,self.OnShowObject,id=id)

        menu.AppendSeparator()

        menu.Append (7,"Measure","",wx.ITEM_CHECK)
        self.Bind (wx.EVT_MENU,self.OnMeasure,id=7)
        if self.tool == "measure": menu.Check(7,True)
        for i in range(0,len(self.pointer_functions)):
            name = self.pointer_functions[i]
            id = 100+i
            menu.Append (id,name,"",wx.ITEM_CHECK)
            if name == self.PointerFunction: menu.Check(id,True)
            self.Bind (wx.EVT_MENU,self.OnSelectPointerFunction,id=id)

        menu.AppendSeparator()

        if self.show_scale: menu.Append (8,"Scale...","")
        self.Bind (wx.EVT_MENU,self.OnScaleProperties,id=8)
        if self.show_crosshair: menu.Append (4,"Crosshair...","")
        self.Bind (wx.EVT_MENU,self.OnCrosshairProperties,id=4)
        if self.show_box: menu.Append (5,"Box...","")
        self.Bind (wx.EVT_MENU,self.OnBoxProperties,id=5)
        if self.show_grid: menu.Append (23,"Grid...","")
        self.Bind (wx.EVT_MENU,self.OnGridProperties,id=23)
        if self.show_profile or self.show_FWHM: menu.Append (10,"Beam Profile...","")
        self.Bind (wx.EVT_MENU,self.OnProfileProperties,id=10)
        if self.show_profile: menu.Append (13,"Channels...","")
        self.Bind (wx.EVT_MENU,self.OnChannelProperties,id=13)
        if self.show_saturated_pixels: menu.Append (12,"Saturated Pixels...","")
        self.Bind (wx.EVT_MENU,self.OnSaturatedPixelProperties,id=12)
        if self.mask_bad_pixels: menu.Append (20,"Bad Pixels...","")
        self.Bind (wx.EVT_MENU,self.OnBadPixelProperties,id=20)
        
        # Display the menu. If an item is selected then its handler will
        # be called before "PopupMenu" returns.
        self.PopupMenu(menu)
        menu.Destroy()

    def OnShowScale (self,event):
        """Called if "Show Scale" is selected from the context menu"""
        self.show_scale = not self.show_scale
        if self.show_scale: self.set_default_scale()
        self.Refresh()

    def set_default_scale(self):
        """Set default position for scale"""
        w,h = self.ImageSize; x,y = self.ImageOrigin 
        l = 0.4*w; l = round(l,int(round(-log10(l)+0.5)))
        self.scale = [(x+w*0.5-l/2,y+h*0.05),(x+w*0.5+l/2,y+h*0.05)]

    def OnShowBox (self,event):
        """Called if "Show Box" is selected from the context menu"""
        self.show_box = not self.show_box
        self.Refresh()

    def OnShowCrosshair (self,event):
        """Called if "Show Crosshair" is selected from the context menu"""
        self.show_crosshair = not self.show_crosshair
        self.Refresh()

    def OnShowGrid (self,event):
        """Called if "Show Crosshair" is selected from the context menu"""
        self.show_grid = not self.show_grid
        self.Refresh()

    def OnShowProfile (self,event):
        """Called if "Show Crosshair" is selected from the context menu"""
        self.show_profile = not self.show_profile
        if self.show_profile: self.calculate_profile()
        self.Refresh()

    def OnShowFWHM (self,event):
        """Called if "Show Crosshair" is selected from the context menu"""
        self.show_FWHM = not self.show_FWHM
        if self.show_FWHM: self.calculate_profile()
        self.Refresh()

    def OnShowCenter (self,event):
        """Called if "Show Crosshair" is selected from the context menu"""
        self.show_center = not self.show_center
        if self.show_center: self.calculate_profile()
        self.Refresh()

    def OnShowSaturatedPixels (self,event):
        """Called if "Show Crosshair" is selected from the context menu"""
        self.show_saturated_pixels = not self.show_saturated_pixels
        self.Refresh()

    def OnMaskBadPixels (self,event):
        """Called if "Mask Bad Pixels" is selected from the context menu"""
        self.mask_bad_pixels = not self.mask_bad_pixels
        self.Refresh()

    def GetMoveCrosshair (self):
        """Is the crosshair is movable or locked?"""
        return (self.tool == "move crosshair")
    def SetMoveCrosshair (self,value):
        if value == True: self.tool = "move crosshair"
        else: self.tool = ""
    MoveCrosshair = property(GetMoveCrosshair,SetMoveCrosshair)

    def OnShowObject (self,event):
        """Called if any of the user-defined objects is selected from the
        context menu"""
        i = event.GetId() - 200
        if 0 <= i < len(self.objects):
            name = list(self.objects.keys())[i]
            self.show_object[name] = True if event.IsChecked() else False

    def OnMeasure (self,event):
        """Called if "Measure" is selected from the context menu"""
        if self.tool == "measure": self.tool = ""
        else: self.tool = "measure"

    def OnSelectPointerFunction (self,event):
        """Called if any of the user-defined pointer functions is selected
        from the context menu"""
        if event.IsChecked():
            i = event.GetId() - 100
            if 0 <= i < len(self.pointer_functions):
                self.tool = self.pointer_functions[i]
        else: self.tool = ""

    def OnScaleProperties (self,event):
        dlg = ScaleProperties(self)
        dlg.CenterOnParent()
        pos = dlg.GetPosition(); pos.y += 100; dlg.SetPosition(pos)
        dlg.Show() 

    def OnCrosshairProperties (self,event):
        dlg = CrosshairProperties(self)
        dlg.CenterOnParent()
        pos = dlg.GetPosition(); pos.y += 100; dlg.SetPosition(pos)
        dlg.Show() 
            
    def OnBoxProperties (self,event):
        dlg = BoxProperties(self)
        dlg.CenterOnParent()
        pos = dlg.GetPosition(); pos.y += 100; dlg.SetPosition(pos)
        dlg.Show() 
            
    def OnGridProperties (self,event):
        dlg = GridProperties(self)
        dlg.CenterOnParent()
        pos = dlg.GetPosition(); pos.y += 100; dlg.SetPosition(pos)
        dlg.Show() 
            
    def OnProfileProperties (self,event):
        dlg = ProfileProperties(self)
        dlg.CenterOnParent()
        pos = dlg.GetPosition(); pos.y += 100; dlg.SetPosition(pos)
        dlg.Show() 

    def OnSaturatedPixelProperties (self,event):
        dlg = SaturatedPixelProperties(self)
        dlg.CenterOnParent()
        pos = dlg.GetPosition(); pos.y += 100; dlg.SetPosition(pos)
        dlg.Show() 

    def OnBadPixelProperties (self,event):
        dlg = BadPixelProperties(self)
        dlg.CenterOnParent()
        pos = dlg.GetPosition(); pos.y += 100; dlg.SetPosition(pos)
        dlg.Show() 

    def OnChannelProperties (self,event):
        dlg = ChannelProperties(self)
        dlg.CenterOnParent()
        pos = dlg.GetPosition(); pos.y += 100; dlg.SetPosition(pos)
        dlg.Show() 

class CrosshairProperties (wx.Dialog):
    """Allows the user to to read the cross position, enter the position
    numerically and change its color."""
    def __init__ (self,parent):
        wx.Dialog.__init__(self,parent,-1,"Crosshair")
        # Controls
        self.Coordinates = TextCtrl(self,size=(75,-1),
            style=wx.TE_PROCESS_ENTER)
        self.Movable = wx.CheckBox(self,label="Movable")
        self.CrosshairSize = TextCtrl (self,size=(75,-1),
            style=wx.TE_PROCESS_ENTER)
        self.ShowCrosshair = wx.CheckBox(self,label="Show")
        h = self.Coordinates.GetSize().y
        self.Color = wx.lib.colourselect.ColourSelect(self,-1,"",
            parent.crosshair_color,size=(h,h))
        # Callbacks
        self.Bind(wx.EVT_TEXT_ENTER,self.OnEnterCoordinates,self.Coordinates)
        self.Bind(wx.EVT_CHECKBOX,self.OnMovable,self.Movable)
        self.Bind(wx.EVT_TEXT_ENTER,self.OnEnterCrosshairSize,
            self.CrosshairSize)
        self.Bind(wx.EVT_CHECKBOX,self.OnShowCrosshair,self.ShowCrosshair)
        self.Color.Bind(wx.lib.colourselect.EVT_COLOURSELECT,
            self.OnSelectColour)
        self.Bind (wx.EVT_CLOSE,self.OnClose)
        # Layout
        layout = wx.FlexGridSizer (cols=3,hgap=5,vgap=5)
        label = wx.StaticText (self,label="Position (x,y) [pixels]:")
        layout.Add (label,flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add (self.Coordinates,flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add (self.Movable,flag=wx.ALIGN_CENTER_VERTICAL)
        label = wx.StaticText (self,label="Size (w,h) [mm]:")
        layout.Add (label,flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add (self.CrosshairSize,flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add (self.ShowCrosshair,flag=wx.ALIGN_CENTER_VERTICAL)
        label = wx.StaticText (self,label="Line color:")
        layout.Add (label,flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add (self.Color,flag=wx.ALIGN_CENTER_VERTICAL)
        self.SetSizer(layout)
        self.Fit()
        self.update()

    def update(self,event=None):
        """Fill the fields"""
        self.Coordinates.Value = "%d,%d" % self.Parent.Crosshair
        self.CrosshairSize.Value = "%.3f,%.3f" % self.Parent.crosshair_size
        self.ShowCrosshair.Value = self.Parent.show_crosshair
        self.Movable.Value = self.Parent.MoveCrosshair
        self.Color.SetValue(self.Parent.crosshair_color)
        # Relaunch yourself.
        self.update_timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.update,self.update_timer)
        self.update_timer.Start(1000,oneShot=True)

    def OnEnterCoordinates(self,event):
        text = self.Coordinates.GetValue()
        try:
            (tx,ty) = text.split(",")
            self.Parent.Crosshair = (float(tx),float(ty))
        except ValueError: return

    def OnMovable(self,event):
        self.Parent.MoveCrosshair = self.Movable.GetValue()

    def OnEnterCrosshairSize(self,event):
        text = self.CrosshairSize.GetValue()
        try:
            (tx,ty) = text.split(",")
            self.Parent.crosshair_size = (float(tx),float(ty))
        except ValueError: return
        self.Parent.Refresh()

    def OnShowCrosshair(self,event): 
        self.Parent.show_crosshair = self.ShowCrosshair.GetValue()
        self.Parent.Refresh()

    def OnSelectColour(self,event): 
        self.Parent.crosshair_color = event.GetValue().Get()
        self.Parent.Refresh()

    def OnClose(self,event):
        """Called when the close button is clocked.
        When the dialog is closed automatically lock the crosshair."""
        self.Parent.MoveCrosshair = False
        self.Destroy()

class BoxProperties (wx.Dialog):
    """Allows the user to change the box size and color"""
    def __init__ (self,parent):
        wx.Dialog.__init__(self,parent,-1,"Box")
        # Controls
        self.BoxSize = TextCtrl (self,size=(75,-1),
            style=wx.TE_PROCESS_ENTER)
        self.ShowBox = wx.CheckBox(self,label="Show")
        h = self.BoxSize.GetSize().y
        self.Color = wx.lib.colourselect.ColourSelect (self,-1,"",
            parent.box_color,size=(h,h))
        # Callbacks
        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnterBoxSize,self.BoxSize)
        self.Bind (wx.EVT_CHECKBOX,self.OnShowBox,self.ShowBox)
        self.Color.Bind (wx.lib.colourselect.EVT_COLOURSELECT,self.OnSelectColour)
        # Layout
        layout = wx.FlexGridSizer (cols=3,hgap=5,vgap=5)
        label = wx.StaticText (self,label="Width,Height [mm]:")
        layout.Add (label,flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add (self.BoxSize,flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add (self.ShowBox,flag=wx.ALIGN_CENTER_VERTICAL)
        label = wx.StaticText (self,label="Line color:")
        layout.Add (label,flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add (self.Color,flag=wx.ALIGN_CENTER_VERTICAL)
        self.SetSizer(layout)
        self.Fit()
        self.update()

    def update(self,event=None):
        """Fill the fields"""
        self.BoxSize.Value = "%.3f,%.3f" % self.Parent.boxsize
        self.ShowBox.Value = self.Parent.show_box
        self.Color.SetValue(self.Parent.box_color)
        # Relaunch yourself.
        self.update_timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.update,self.update_timer)
        self.update_timer.Start(1000,oneShot=True)
        
    def OnEnterBoxSize(self,event):
        text = self.BoxSize.GetValue()
        try:
            (tx,ty) = text.split(",")
            self.Parent.boxsize = (float(tx),float(ty))
        except ValueError: return
        self.Parent.Refresh()

    def OnShowBox(self,event): 
        self.Parent.show_box = self.ShowBox.Value
        self.Parent.Refresh()

    def OnSelectColour(self,event): 
        self.Parent.box_color = event.GetValue().Get()
        self.Parent.Refresh()


class ScaleProperties (wx.Dialog):
    """Allows the user to enter the length of the measurement scale numerically,
    make the line exactly horizonal or vertical and change its color.
    """
    def __init__ (self,parent):
        wx.Dialog.__init__(self,parent,-1,"Scale")
        # Controls
        self.Length = TextCtrl (self,size=(60,-1),style=wx.TE_PROCESS_ENTER)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnterLength,self.Length)
        self.Horizontal = wx.CheckBox (self,label="Horizontal")
        self.Bind (wx.EVT_CHECKBOX,self.OnHorizontal,self.Horizontal)
        self.Vertical = wx.CheckBox (self,label="Vertical")
        self.Bind (wx.EVT_CHECKBOX,self.OnVertical,self.Vertical)
        h = self.Length.GetSize().y
        self.Color = wx.lib.colourselect.ColourSelect (self,size=(h,h))
        self.Color.Bind (wx.lib.colourselect.EVT_COLOURSELECT,self.OnSelectColour)
        # Layout
        layout = wx.FlexGridSizer (cols=2,hgap=5,vgap=5)
        label = wx.StaticText (self,label="Length [mm]:")
        layout.Add (label,flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add (self.Length,flag=wx.ALIGN_CENTER_VERTICAL)
        label = wx.StaticText (self,label="Direction:")
        layout.Add (label,flag=wx.ALIGN_CENTER_VERTICAL)
        group = wx.BoxSizer()
        group.Add (self.Horizontal)
        group.AddSpacer(5)
        group.Add (self.Vertical)
        layout.Add (group)
        label = wx.StaticText (self,label="Line color:")
        layout.Add (label,flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add (self.Color,flag=wx.ALIGN_CENTER_VERTICAL)
        self.SetSizer(layout)
        self.Fit()
        self.update()
        
    def update(self,event=None):
        """Fill the fields"""
        (P1,P2) = self.Parent.scale
        length = distance(P1,P2)
        self.Length.Value = "%.3f" % length
        v = vector(P1,P2)
        self.Horizontal.Value = (v[1] == 0)
        self.Vertical.Value = (v[0] == 0)

        self.Color.SetValue(self.Parent.scale_color)

        # Relaunch yourself.
        self.update_timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.update,self.update_timer)
        self.update_timer.Start(1000,oneShot=True)

    def OnEnterLength(self,event):
        text = self.Length.GetValue()
        try: length = float(text)
        except ValueError: return
        parent = self.Parent
        (P1,P2) = parent.scale
        P2 = translate(P1,scale(direction(vector(P1,P2)),length))
        parent.scale = [P1,P2]
        parent.Refresh()

    def OnHorizontal(self,event): 
        self.Horizontal.SetValue(True); self.Vertical.SetValue(False)
        parent = self.Parent
        (P1,P2) = parent.scale; length = distance(P1,P2)
        P2 = translate(P1,(length,0))
        parent.scale = [P1,P2]
        parent.Refresh()

    def OnVertical(self,event): 
        self.Horizontal.SetValue(False); self.Vertical.SetValue(True)
        parent = self.Parent
        (P1,P2) = parent.scale; length = distance(P1,P2)
        P2 = translate(P1,(0,length))
        parent.scale = [P1,P2]
        parent.Refresh()

    def OnSelectColour(self,event): 
        self.Parent.scale_color = event.GetValue().Get()
        self.Parent.Refresh()


class GridProperties (wx.Dialog):
    """Allows the user to change the box size and color"""
    def __init__ (self,parent):
        wx.Dialog.__init__(self,parent,-1,"Grid")
        # Controls
        style = wx.TE_PROCESS_ENTER
        size = (75,-1)
        self.Type = ComboBox(self,size=size,choices=["X","Y","XY"])
        self.Bind (wx.EVT_COMBOBOX,self.OnEnterType,self.Type)
        self.XSpacing = TextCtrl(self,size=size,style=style)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnterXSpacing,self.XSpacing)
        self.XOffset = TextCtrl(self,size=size,style=style)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnterXOffset,self.XOffset)

        self.YSpacing = TextCtrl(self,size=size,style=style)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnterYSpacing,self.YSpacing)
        self.YOffset = TextCtrl(self,size=size,style=style)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnterYOffset,self.YOffset)

        w,h = self.XSpacing.Size
        self.Color = wx.lib.colourselect.ColourSelect (self,size=(h,h))
        self.Color.Bind (wx.lib.colourselect.EVT_COLOURSELECT,
            self.OnSelectColour)
        # Layout
        layout = wx.FlexGridSizer (cols=2,hgap=5,vgap=5)

        label = wx.StaticText (self,label="Type:")
        layout.Add (label,flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add (self.Type,flag=wx.ALIGN_CENTER_VERTICAL)

        self.XSpacingLabel = wx.StaticText (self,label="Horizontal spacing:")
        layout.Add (self.XSpacingLabel,flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add (self.XSpacing,flag=wx.ALIGN_CENTER_VERTICAL)
        self.XOffsetLabel = wx.StaticText (self,label="Horizontal offset:")
        layout.Add (self.XOffsetLabel,flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add (self.XOffset,flag=wx.ALIGN_CENTER_VERTICAL)

        self.YSpacingLabel = wx.StaticText (self,label="Vertical spacing:")
        layout.Add (self.YSpacingLabel,flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add (self.YSpacing,flag=wx.ALIGN_CENTER_VERTICAL)
        self.YOffsetLabel = wx.StaticText (self,label="Vertical offset:")
        layout.Add (self.YOffsetLabel,flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add (self.YOffset,flag=wx.ALIGN_CENTER_VERTICAL)
        
        label = wx.StaticText (self,label="Color:")
        layout.Add (label,flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add (self.Color,flag=wx.ALIGN_CENTER_VERTICAL)
        self.SetSizer(layout)
        self.Fit()
        self.update()

    def update(self,event=None):
        """Fill the fields"""
        type = self.Parent.grid_type
        self.Type.Value = type.upper()

        # Show only those controls actually needed for the selected grid type.
        self.XSpacingLabel.Show("x" in type)
        self.XSpacing.Show("x" in type)
        self.XOffsetLabel.Show("x" in type)
        self.XOffset.Show("x" in type)

        self.YSpacingLabel.Show("y" in type)
        self.YSpacing.Show("y" in type)
        self.YOffsetLabel.Show("y" in type)
        self.YOffset.Show("y" in type)

        self.Fit()
        
        dx = self.Parent.grid_x_spacing
        self.XSpacing.Value  = "%.3f mm" % dx if not isnan(dx) else ""
        x0 = self.Parent.grid_x_offset
        self.XOffset.Value  = "%.3f mm" % x0 if not isnan(x0) else ""

        dy = self.Parent.grid_y_spacing
        self.YSpacing.Value  = "%.3f mm" % dy if not isnan(dy) else ""
        y0 = self.Parent.grid_y_offset
        self.YOffset.Value  = "%.3f mm" % y0 if not isnan(y0) else ""

        self.Color.SetValue(self.Parent.grid_color)
        # Relaunch yourself.
        self.update_timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.update,self.update_timer)
        self.update_timer.Start(1000,oneShot=True)
        
    def OnEnterType(self,event):
        self.Parent.grid_type = self.Type.Value.lower()
        self.Parent.Refresh()
        self.update()

    def OnEnterXSpacing(self,event):
        text = self.XSpacing.Value.replace("mm","")
        try: value = float(eval(text))
        except: self.update(); return
        self.Parent.grid_x_spacing = value
        self.Parent.Refresh()
        self.update()

    def OnEnterXOffset(self,event):
        text = self.XOffset.Value.replace("mm","")
        try: value = float(eval(text))
        except: self.update(); return
        self.Parent.grid_x_offset = value
        self.Parent.Refresh()
        self.update()

    def OnEnterYSpacing(self,event):
        text = self.YSpacing.Value.replace("mm","")
        try: value = float(eval(text))
        except: self.update(); return
        self.Parent.grid_y_spacing = value
        self.Parent.Refresh()
        self.update()

    def OnEnterYOffset(self,event):
        text = self.YOffset.Value.replace("mm","")
        try: value = float(eval(text))
        except: self.update(); return
        self.Parent.grid_y_offset = value
        self.Parent.Refresh()
        self.update()

    def OnSelectColour(self,event): 
        self.Parent.grid_color = event.GetValue().Get()
        self.Parent.Refresh()


class ProfileProperties (wx.Dialog):
    """Allows the user to change the beam profile box color"""
    def __init__ (self,parent):
        wx.Dialog.__init__(self,parent,-1,"Beam Profile")
        # Controls
        self.Correction = wx.Choice (self,size=(60,-1),choices=["on","off"])
        self.Bind (wx.EVT_CHOICE,self.OnCorrection,self.Correction)
        
        self.Projection = wx.RadioButton (self,label="Projection",
            style=wx.RB_GROUP)
        self.Bind (wx.EVT_RADIOBUTTON,self.OnProfileType,self.Projection)
        self.Section = wx.RadioButton (self,label="Section")
        self.Bind (wx.EVT_RADIOBUTTON,self.OnProfileType,self.Section)

        self.Threshold = TextCtrl (self,size=(60,-1),
            style=wx.TE_PROCESS_ENTER)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnterThreshold,self.Threshold)

        h = self.Threshold.GetSize().y
        self.ProfileColor = wx.lib.colourselect.ColourSelect (self,size=(h,h))
        self.ProfileColor.Bind (wx.lib.colourselect.EVT_COLOURSELECT,
            self.OnSelectProfileColor)
        self.FWHMColor = wx.lib.colourselect.ColourSelect (self,size=(h,h))
        self.FWHMColor.Bind (wx.lib.colourselect.EVT_COLOURSELECT,
            self.OnSelectFWHMColor)
        self.CenterColor = wx.lib.colourselect.ColourSelect (self,size=(h,h))
        self.CenterColor.Bind (wx.lib.colourselect.EVT_COLOURSELECT,
            self.OnSelectCenterColor)
        self.ROIColor = wx.lib.colourselect.ColourSelect (self,size=(h,h))
        self.ROIColor.Bind (wx.lib.colourselect.EVT_COLOURSELECT,
            self.OnSelectROIColor)
        # Layout
        layout = wx.FlexGridSizer (cols=2,hgap=5,vgap=5)
        label = wx.StaticText (self,label="Linearity correction:")
        layout.Add (label,flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add (self.Correction,flag=wx.ALIGN_CENTER_VERTICAL)
        label = wx.StaticText (self,label="Saturation threshold [0-255]:")
        layout.Add (label,flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add (self.Threshold,flag=wx.ALIGN_CENTER_VERTICAL)
        label = wx.StaticText (self,label="Profile type:")
        layout.Add (label,flag=wx.ALIGN_CENTER_VERTICAL)
        group = wx.BoxSizer(); group.Add (self.Projection)
        group.AddSpacer(5); group.Add (self.Section)
        layout.Add (group)
        label = wx.StaticText (self,label="Profile color:")
        layout.Add (label,flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add (self.ProfileColor,flag=wx.ALIGN_CENTER_VERTICAL)
        label = wx.StaticText (self,label="FWHM box color:")
        layout.Add (label,flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add (self.FWHMColor,flag=wx.ALIGN_CENTER_VERTICAL)
        label = wx.StaticText (self,label="Center line color:")
        layout.Add (label,flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add (self.CenterColor,flag=wx.ALIGN_CENTER_VERTICAL)
        label = wx.StaticText (self,label="Region:")
        layout.Add (label,flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add (self.ROIColor,flag=wx.ALIGN_CENTER_VERTICAL)
        self.SetSizer(layout)
        self.Fit()
        self.update()
        
    def update(self,event=None):
        """Fill the fields"""
        text = "on" if self.Parent.linearity_correction else "off"
        self.Correction.SetStringSelection(text)
        self.Section.Value = self.Parent.calculate_section

        self.Threshold.Value = "%d" % self.Parent.saturation_threshold

        self.Section.Value = self.Parent.calculate_section
        self.Projection.Value = not self.Parent.calculate_section
 
        self.ProfileColor.SetValue(self.Parent.profile_color)
        self.FWHMColor.SetValue(self.Parent.FWHM_color)
        self.CenterColor.SetValue(self.Parent.center_color)
        self.ROIColor.SetValue(self.Parent.ROI_color)

        # Relaunch yourself.
        self.update_timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.update,self.update_timer)
        self.update_timer.Start(1000,oneShot=True)

    def OnEnterThreshold(self,event):
        parent = self.Parent
        text = self.Threshold.GetValue()
        try: parent.saturation_threshold = min(max(0,int(text)),255)
        except ValueError: pass
        self.Threshold.Value = "%d" % parent.saturation_threshold
        parent.calculate_profile()
        parent.Refresh()

    def OnCorrection(self,event):
        parent = self.Parent
        text = self.Correction.GetStringSelection()
        parent.linearity_correction = (text == "on")
        parent.calculate_profile()
        parent.Refresh()

    def OnProfileType(self,event):
        parent = self.Parent
        parent.calculate_section = self.Section.Value
        parent.calculate_profile()
        parent.Refresh()

    def OnSelectProfileColor(self,event):
        parent = self.Parent
        parent.profile_color = event.GetValue().Get()
        parent.Refresh()

    def OnSelectFWHMColor(self,event):
        parent = self.Parent
        parent.FWHM_color = event.GetValue().Get()
        parent.Refresh()

    def OnSelectCenterColor(self,event):
        parent = self.Parent
        parent.center_color = event.GetValue().Get()
        parent.Refresh()

    def OnSelectROIColor(self,event):
        parent = self.Parent
        parent.ROI_color = event.GetValue().Get()
        parent.Refresh()


class SaturatedPixelProperties (wx.Dialog):
    """Allows the user to change the color with which saturated pixels are
    marked"""
    def __init__ (self,parent):
        wx.Dialog.__init__(self,parent,-1,"Saturated Pixels")
        # Controls
        self.Threshold = TextCtrl(self,size=(60,-1),style=wx.TE_PROCESS_ENTER)
        self.Color = wx.lib.colourselect.ColourSelect(self,-1,"",size=(20,20))
        # Callbacks
        self.Bind(wx.EVT_TEXT_ENTER,self.OnEnterThreshold,self.Threshold)
        self.Color.Bind(wx.lib.colourselect.EVT_COLOURSELECT,
            self.OnSelectColour)
        # Layout
        layout = wx.FlexGridSizer (cols=2,hgap=5,vgap=5)
        label = wx.StaticText (self,label="Threshold [0-255]:")
        layout.Add (label,flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add (self.Threshold,flag=wx.ALIGN_CENTER_VERTICAL)
        label = wx.StaticText (self,label="Highlight Color:")
        layout.Add (label,flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add (self.Color,flag=wx.ALIGN_CENTER_VERTICAL)
        self.SetSizer(layout)
        self.Fit()
        self.update()

    def update(self,event=None):
        """Fill the fields."""
        self.Threshold.Value = "%d" % self.Parent.saturation_threshold
        self.Color.SetValue(self.Parent.saturated_color)
        # Relaunch yourself.
        self.update_timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.update,self.update_timer)
        self.update_timer.Start(1000,oneShot=True)
         
    def OnSelectColour(self,event): 
        self.Parent.saturated_color = event.GetValue().Get()
        self.Parent.Refresh()

    def OnEnterThreshold(self,event):
        parent = self.Parent
        text = self.Threshold.GetValue()
        try: parent.saturation_threshold = min(max(0,int(text)),255)
        except ValueError: pass
        self.Threshold.SetValue("%d" % parent.saturation_threshold)
        parent.calculate_profile()
        parent.Refresh()


class BadPixelProperties (wx.Dialog):
    """Allows the user to change the color with which saturated pixels are
    marked"""
    def __init__ (self,parent):
        wx.Dialog.__init__(self,parent,-1,"Bad Pixels")
        # Controls
        self.Threshold = TextCtrl (self,size=(60,-1),
            style=wx.TE_PROCESS_ENTER)
        self.Color = wx.lib.colourselect.ColourSelect(self,-1,"",size=(20,20))
        UpdateButton = wx.Button(self,label="Update")
        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnterThreshold,self.Threshold)
        # Callbacks
        self.Color.Bind (wx.lib.colourselect.EVT_COLOURSELECT,
            self.OnSelectColour)
        self.Bind (wx.EVT_BUTTON,self.OnUpdate,UpdateButton)
        # Layout
        layout = wx.BoxSizer(wx.VERTICAL)
        
        grid = wx.FlexGridSizer (cols=2,hgap=5,vgap=5)
        label = wx.StaticText (self,label="Threshold [0-255]:")
        grid.Add (label,flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add (self.Threshold,flag=wx.ALIGN_CENTER_VERTICAL)
        label = wx.StaticText (self,label="Highlight Color:")
        grid.Add (label,flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add (self.Color,flag=wx.ALIGN_CENTER_VERTICAL)

        layout.Add (grid,flag=wx.ALIGN_CENTER,border=10)
        layout.AddSpacer(10)
        layout.Add (UpdateButton,flag=wx.ALIGN_CENTER,border=10)

        self.SetSizer(layout)
        self.Fit()
        self.update()

    def update(self,event=None):
        """Fill the fields"""
        self.Threshold.Value = "%d" % self.Parent.bad_pixel_threshold
        self.Color.SetValue(self.Parent.bad_pixel_color)
        # Relaunch yourself.
        self.update_timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.update,self.update_timer)
        self.update_timer.Start(1000,oneShot=True)

    def OnSelectColour(self,event): 
        self.Parent.bad_pixel_color = event.GetValue().Get()
        self.Parent.Refresh()

    def OnEnterThreshold(self,event=0):
        parent = self.Parent
        text = self.Threshold.GetValue()
        try: parent.bad_pixel_threshold = min(max(0,int(text)),255)
        except ValueError: pass
        self.Threshold.SetValue("%d" % parent.bad_pixel_threshold)

    def OnUpdate(self,event):
        self.OnEnterThreshold()
        self.Parent.update_bad_pixels()

class ChannelProperties (wx.Dialog):
    """Allows the user to select which of the channels R,G,B to use"""
    def __init__ (self,parent):
        wx.Dialog.__init__(self,parent,-1,"Channels")
        # Controls
        self.Red = wx.CheckBox (self,label="Red")
        self.Bind (wx.EVT_CHECKBOX,self.OnChannel,self.Red)
        self.Green = wx.CheckBox (self,label="Green")
        self.Bind (wx.EVT_CHECKBOX,self.OnChannel,self.Green)
        self.Blue = wx.CheckBox (self,label="Blue")
        self.Bind (wx.EVT_CHECKBOX,self.OnChannel,self.Blue)
        R,G,B = parent.use_channels
        self.Red.SetValue(R)
        self.Green.SetValue(G)
        self.Blue.SetValue(B)
        # Layout
        layout = wx.FlexGridSizer (cols=2,hgap=5,vgap=5)
        label = wx.StaticText (self,label="Use Channels:")
        layout.Add (label,flag=wx.ALIGN_CENTER_VERTICAL)
        group = wx.BoxSizer()
        group.Add (self.Red); group.AddSpacer(5)
        group.Add (self.Green); group.AddSpacer(5)
        group.Add (self.Blue)
        layout.Add (group)
        self.SetSizer(layout)
        self.Fit()
        
    def OnChannel(self,event):
        parent = self.Parent
        R = self.Red.GetValue()
        G = self.Green.GetValue()
        B = self.Blue.GetValue()
        parent.use_channels = (R,G,B)
        parent.calculate_profile()
        parent.Refresh()

class ViewerOptions(BasePanel):
    name = "viewer"
    title = "Viewer Options"
    standard_view = [
        "Title",
        "Min. update time",
    ]

    def __init__(self,viewer):
        parameters = [
            [[PropertyPanel,"Title",viewer,"Title"],{"refresh_period":1.0,"width":240}],
            [[PropertyPanel,"Min. update time",viewer,"dt"],{"unit":"s","refresh_period":1.0}],
        ]
        BasePanel.__init__(self,
            parent=viewer,
            name=self.name,
            title=self.title,
            parameters=parameters,
            standard_view=self.standard_view,
            subname=True,
            refresh=False,
            live=False,
            label_width=90,
        )
        
class CameraOptions (wx.Dialog):
    """Configure the camera"""
    def __init__ (self,parent):
        wx.Dialog.__init__(self,parent,-1,"Camera Options")
        camera = self.Parent.camera
        # Controls
        self.ServerIPAddress = ComboBox(self,choices=ip_addresses,
                                style=wx.TE_PROCESS_ENTER)
        self.Bind (wx.EVT_COMBOBOX,self.OnServerIPAddress,self.ServerIPAddress)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnServerIPAddress,self.ServerIPAddress)
        
        self.CameraIPAddress = ComboBox(self,choices=ip_addresses,
                                style=wx.TE_PROCESS_ENTER)
        self.Bind (wx.EVT_COMBOBOX,self.OnCameraIPAddress,self.CameraIPAddress)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnCameraIPAddress,self.CameraIPAddress)

        self.Multicast = ComboBox(self,choices=["Yes","No"])
        self.Bind (wx.EVT_COMBOBOX,self.OnMulticast,self.Multicast)

        self.ExternalTrigger = ComboBox (self,choices=["Yes","No"])
        self.Bind (wx.EVT_COMBOBOX,self.OnExternalTrigger,self.ExternalTrigger)

        self.Gain = TextCtrl (self,size=(80,-1),style=wx.TE_PROCESS_ENTER)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnGain,self.Gain)
        
        self.PixelFormat = ComboBox (self,choices=camera.pixel_formats)
        self.Bind (wx.EVT_COMBOBOX,self.OnPixelFormat,self.PixelFormat)
        self.BinFactor = ComboBox (self,choices=["1","2","4","8"])
        self.Bind (wx.EVT_COMBOBOX,self.OnBinFactor,self.BinFactor)
        self.StreamBytesPerSecond = TextCtrl (self,size=(80,-1),
            style=wx.TE_PROCESS_ENTER)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnStreamBytesPerSecond,
            self.StreamBytesPerSecond)
        RefreshButton = wx.Button (self,label="Refresh")
        self.Bind (wx.EVT_BUTTON,self.refresh,RefreshButton)
        SaveAsDefaultButton = wx.Button (self,label="Save As Default")
        self.Bind (wx.EVT_BUTTON,self.SaveAsDefault,SaveAsDefaultButton)

        # Layout
        layout = wx.BoxSizer(wx.VERTICAL)

        grid = wx.FlexGridSizer (cols=2,hgap=5,vgap=5)
        flag = wx.ALIGN_CENTER_VERTICAL
        grid.Add (wx.StaticText(self,label="Server Address:"),flag=flag)
        grid.Add (self.ServerIPAddress,flag=flag)
        grid.Add (wx.StaticText(self,label="Camera Address:"),flag=flag)
        grid.Add (self.CameraIPAddress,flag=flag)
        grid.Add (wx.StaticText(self,label="Multicast:"),flag=flag)
        grid.Add (self.Multicast,flag=flag)
        grid.Add (wx.StaticText(self,label="External Trigger:"),flag=flag)
        grid.Add (self.ExternalTrigger,flag=flag)
        grid.Add (wx.StaticText(self,label="Gain:"),flag=flag)
        grid.Add (self.Gain,flag=flag)
        grid.Add (wx.StaticText(self,label="Pixel format:"),flag=flag)
        grid.Add (self.PixelFormat,flag=flag)
        grid.Add (wx.StaticText(self,label="Bin Factor:"),flag=flag)
        grid.Add (self.BinFactor,flag=flag)
        grid.Add (wx.StaticText(self,label="Stream Bytes/s:"),flag=flag)
        grid.Add (self.StreamBytesPerSecond,flag=flag)
        layout.Add (grid,flag=wx.ALIGN_CENTER|wx.ALL,border=10)

        buttons = wx.BoxSizer(wx.HORIZONTAL)
        buttons.Add (RefreshButton)
        buttons.AddSpacer(5)
        buttons.Add (SaveAsDefaultButton)
        layout.Add (buttons,flag=wx.ALIGN_CENTER|wx.ALL,border=10)

        self.SetSizer(layout)
        self.Fit()

        self.update()

    def update(self,event=None):
        """Static configuration parameters"""
        camera = self.Parent.camera
        self.ServerIPAddress.Value = str(camera.ip_address)
        self.CameraIPAddress.Value = str(camera.camera_ip_address)
        self.Multicast.Value = "Yes" if camera.use_multicast else "No"
        # Relaunch yourself.
        self.update_timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.update,self.update_timer)
        self.update_timer.Start(1000,oneShot=True)

    def refresh(self,event=None):
        """Live parameters read from the camera"""
        camera = self.Parent.camera
        self.ExternalTrigger.Value = "Yes" if camera.external_trigger else "No"
        self.Gain.Value = str(camera.gain)
        self.PixelFormat.Value = camera.pixel_format
        self.BinFactor.Value = str(camera.bin_factor)
        self.StreamBytesPerSecond.Value = str(camera.stream_bytes_per_second)

    def OnServerIPAddress(self,event):
        camera = self.Parent.camera
        camera.ip_address = self.ServerIPAddress.Value
        self.update()

    def OnCameraIPAddress(self,event):
        camera = self.Parent.camera
        camera.camera_ip_address = self.CameraIPAddress.Value
        self.update()

    def OnMulticast(self,event):
        camera = self.Parent.camera
        camera.use_multicast = (self.Multicast.Value == "Yes")
        self.update()

    def OnExternalTrigger(self,event):
        camera = self.Parent.camera
        camera.external_trigger = (self.ExternalTrigger.Value == "Yes")
        self.refresh()

    def OnGain(self,event):
        camera = self.Parent.camera
        camera.gain = int(self.Gain.Value)
        self.refresh()

    def OnPixelFormat(self,event):
        camera = self.Parent.camera
        camera.pixel_format = self.PixelFormat.Value
        self.refresh()

    def OnBinFactor(self,event):
        camera = self.Parent.camera
        camera.bin_factor = self.BinFactor.Value
        self.refresh()

    def OnStreamBytesPerSecond(self,event):
        camera = self.Parent.camera
        camera.stream_bytes_per_second = self.StreamBytesPerSecond.Value
        self.refresh()

    def SaveAsDefault(self,event):
        "Writes current parameters to non-volatile memory"
        camera = self.Parent.camera
        camera.save_parameters()
        self.refresh()

class OpticsOptions(BasePanel):
    name = "optics"
    title = "Optics Options"
    standard_view = [
        "Nominal pixel size",
        "Zoom levels",
    ]

    def __init__(self,viewer):        
        parameters = [
            [[PropertyPanel,"Nominal pixel size",viewer,"NominalPixelSize"],{"unit":"mm","refresh_period":1.0,"width":240}],
            [[PropertyPanel,"Zoom levels",viewer,"zoom_levels"],{"type":"list","refresh_period":1.0,"width":240}],
        ]
        BasePanel.__init__(self,
            parent=viewer,
            name=self.name,
            title=self.title,
            parameters=parameters,
            standard_view=self.standard_view,
            subname=True,
            refresh=False,
            live=False,
            label_width=90,
        )
        
ip_addresses = [
    "nih-instrumentation.cars.aps.anl.gov:2001",
    "nih-instrumentation.cars.aps.anl.gov:2002",
    "pico20.niddk.nih.gov:2001",
    "pico20.niddk.nih.gov:2002",
]

# IP addresses:
# id14b-prosilica1.cars.aps.anl.gov
# id14b-prosilica2.cars.aps.anl.gov
# id14b-prosilica3.cars.aps.anl.gov
# id14b-prosilica4.cars.aps.anl.gov
# id14b-prosilica5.cars.aps.anl.gov
# id14b-prosilica6.cars.aps.anl.gov
# pico3.niddk.nih.gov
# pico22.niddk.nih.gov

# Serial numbers:
# 02-2131A-06331
# 02-2131A-06353
# 02-2131A-06043
# 02-2131A-06108
# 02-2131A-16516
# 02-2131A-16519

def distance (p1,p2):
    """Distance between two points"""
    x1,y1 = p1
    x2,y2 = p2
    return sqrt((x2-x1)**2+(y2-y1)**2)

def point_line_distance (P,line):
    "Distance of a point to a line segment of finite length"
    # Source: softsurfer.com/Archive/algorithm_0102/algorithm_0102.htm
    # 18 May 2007
    P0 = line[0]; P1 = line[1]
    v = vector(P0,P1); w0 = vector(P0,P); w1 = vector(P1,P)
    # If the angle (P,P0,P1) is obtuse (>=90 deg), it is the distance to P0.
    if dot(w0,v) <= 0: return distance(P,P0)
    # If the angle(P,P1,P0) is obtuse (>=90 deg), it is the distance to P1.
    if dot(w1,v) >= 0: return distance(P,P1) 
    # Otherwise, it is the orthognal distance to the line.
    b = dot(w0,v) / float(dot(v,v))
    Pb = translate(P0,scale(v,b))
    return distance(P,Pb)

def vector(p1,p2):
    """Vector from point p1=(x1,y1) to point p2=(x2,y2)"""
    x1,y1 = p1
    x2,y2 = p2
    return (x2-x1,y2-y1)
    
def translate(p,v):
    """Apply the vector v=(vx,vy) to point p=(x,y)"""
    x,y = p
    vx,vy = v
    return (x+vx,y+vy)

def scale(v,a):
    """Mulitplies vector v=(x,y) with scalar"""
    x,y = v
    return (a*x,a*y)

def direction(v):
    """Vector v=(x,y) scaled to unit length"""
    x,y = v
    l = sqrt(x**2+y**2)
    if l == 0: return (1.,0.)
    return (x/l,y/l)

def dot(v1,v2):
    "Scalar product between vectors (x1,y1) and (x2,y2)"
    x1,y1 = v1
    x2,y2 = v2
    return x1*x2+y1*y2

def FWHM(data):
    """Calculates full-width at half-maximum of a positive peak of a curve
    given as list of [x,y] values"""
    x = xvals(data); y = yvals(data); n = len(data)
    if n == 0: return nan
    HM = (min(y)+max(y))/2
    for i in range (0,n):
        if y[i]>HM: break
    if i == 0: x1 = x[0]
    else: x1 = interpolate_x((x[i-1],y[i-1]),(x[i],y[i]),HM)
    r = list(range(0,n)); r.reverse()
    for i in r:
        if y[i]>HM: break
    if i == n-1: x2 = x[n-1]
    else: x2 = interpolate_x((x[i+1],y[i+1]),(x[i],y[i]),HM)
    return abs(x2-x1)

def CFWHM(data):
    """Calculates the center of the full width half of the positive peak of
    a curve given as list of [x,y] values"""
    x = xvals(data); y = yvals(data); n = len(data)
    if n == 0: return nan
    HM = (min(y)+max(y))/2
    for i in range (0,n):
        if y[i]>HM: break
    if i == 0: x1 = x[0]
    else: x1 = interpolate_x((x[i-1],y[i-1]),(x[i],y[i]),HM)
    r = list(range(0,n)); r.reverse()
    for i in r:
        if y[i]>HM: break
    if i == n-1: x2 = x[n-1]
    else: x2 = interpolate_x((x[i+1],y[i+1]),(x[i],y[i]),HM)
    return (x2+x1)/2.

def interpolate_x(p1,p2,y):
    """Linear inteposition between two points"""
    x1,y1 = p1
    x2,y2 = p2
    # In case result is undefined, midpoint is as good as any value.
    if y1==y2: return (x1+x2)/2. 
    x = x1+(x2-x1)*(y-y1)/float(y2-y1)
    ##print("interpolate_x [%g,%g,%g][%g,%g,%g]" % (x1,x,x2,y1,y,y2))
    return x

def xvals(xy_data):
    "xy_data = list of (x,y)-tuples. Returns list of x values only."
    xvals = []
    for i in range (0,len(xy_data)): xvals.append(xy_data[i][0])
    return xvals

def yvals(xy_data):
    "xy_data = list of (x,y)-tuples. Returns list of y values only."
    yvals = []
    for i in range (0,len(xy_data)): yvals.append(xy_data[i][1])
    return yvals

def save(columns,filename,header="",labels=None):
    """Usage: save([x,y],"test.txt",labels="x,y")
    Write lists of numbers as tab-separated ASCII file.
    "columns" must be a list containing lists of numeric values of the same
    length.
    "labels" can be given as comma-spearated string or as list of strings.
    """
    from isstring import isstring
    output = open(filename,"w")
    for line in header.split("\n"):
        if line: output.write("# "+line+"\n")
    if labels:
        if isstring(labels): labels = labels.split(",")
        output.write("#")
        for col in range(0,len(labels)-1): output.write(labels[col]+"\t")
        output.write(labels[len(labels)-1]+"\n")
    Ncol = len(columns)
    Nrow = 0
    for col in range(0,Ncol): Nrow = max(Nrow,len(columns[col]))
    for row in range(0,Nrow):
        for col in range(0,Ncol):
            try: val = columns[col][row]
            except: val = ""
            if isstring(val): output.write(val)
            else: output.write("%g" % val)
            if col < Ncol-1: output.write("\t")
            else: output.write("\n")

def module_dir():
    """directory of the current module"""
    from os.path import dirname
    module_dir = dirname(module_path())
    if module_dir == "": module_dir = "."
    return module_dir

def module_path():
    """full pathname of the current module"""
    from sys import path
    from os import getcwd
    from os.path import basename,exists
    from inspect import getmodulename,getfile
    # "getfile" retreives the source file name name compiled into the .pyc file.
    pathname = getfile(lambda x: None)
    ##print("module_path: pathname: %r" % pathname)
    if exists(pathname): return pathname
    # The module might have been compiled on a different machine or in a
    # different directory.
    pathname = pathname.replace("\\","/")
    filename = basename(pathname)
    ##print("module_path: filename: %r" % filename)
    dirs = [dir for dir in [getcwd()]+path if exists(dir+"/"+filename)]
    if len(dirs) == 0: error("pathname of file %r not found" % filename)
    dir = dirs[0] if len(dirs) > 0 else "."
    pathname = dir+"/"+filename
    ##print("module_path: pathname: %r" % pathname)
    return pathname

def icon_dir():
    """pathname of the directory from which to load custom icons"""
    return module_dir()+"/icons"


def crosshair_cursor():
    """A black crosshair cursor of size 13x13 pixels with white border
    as wx.Cursor object"""
    # This is a replacement for wx.Image(wx.CURSOR_CROSS)
    # Under Windows, the wxPython's built-in crosshair cursor does not have a
    # white border and is hard to see on a black background.
    global crosshair_cursor_object
    if "crosshair_cursor_object" in globals(): return crosshair_cursor_object
    filename = icon_dir()+"/crosshair.png"
    if exists(filename):
        image = wx.Image(filename)
        image.SetOptionInt(wx.IMAGE_OPTION_CUR_HOTSPOT_X,7)
        image.SetOptionInt(wx.IMAGE_OPTION_CUR_HOTSPOT_Y,7)
        crosshair_cursor_object = wx.CursorFromImage(image)
    else:
        warning("%s not found" % filename)
        crosshair_cursor_object = wx.Image(wx.CURSOR_CROSS)
    return crosshair_cursor_object

def mtime(filename):
    """Modication timestamp of a file, in seconds since 1 Jan 1970 12:00 AM GMT
    """
    from os.path import getmtime
    try: return getmtime(filename)
    except: return 0 # file does not exist


def int32(x):
    """Force conversion of x to 32-bit signed integer"""
    x = int(x)
    maxint = int(2**31-1)
    minint = int(-2**31)
    if x > maxint: x = maxint
    if x < minint: x = minint
    return x

DEBUG = False # for debugging

if __name__ == "__main__": # for testing
    from pdb import pm # for debugging
    name = "MicroscopeCamera"
    from redirect import redirect
    redirect(name)
    DEBUG = True
    app = wx.GetApp() if wx.GetApp() else wx.App()
    self = CameraViewer(name=name)
    app.MainLoop()
