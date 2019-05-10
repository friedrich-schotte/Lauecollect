#!/usr/bin/env python
"""
Grapical User Interface for inspecting images.
Author: Friedrich Schotte, 16 Jan 2009 - 29 Jun 2017
"""

import wx
from math import sqrt,atan2,sin,cos,pi,log10
from numpy import *
__version__ = "4.2.2" # show_image 

class ImageViewer_Window (wx.Frame):
    image_timestamp = 0
    
    def __init__(self,show=True,image_file="",mask_file=""):
        """
        default_orientation: default image rotation in degrees
          positive = counter-clock wise
          allowed values: 0,-90,90,180
          only use at first invecation as default value, last saved value
          overrides this value.
        show: display the window immediately
        """
        wx.Frame.__init__(self,parent=None,size=(425,340))

        self.Bind (wx.EVT_CLOSE,self.OnClose)
        # Menus
        menuBar = wx.MenuBar()
        menu = wx.Menu()
        menu.Append (101,"&Open Image...\tCtrl+O","File formats: TIFF,JPEG,PNG")
        self.Bind (wx.EVT_MENU,self.OpenImage,id=101)
        menu.Append (111,"&New Window...\tCtrl+N","Open Image in a new window")
        self.Bind (wx.EVT_MENU,self.NewWindow,id=111)
        menu.Append (102,"&Overlay Mask...","File formats: TIFF,JPEG,PNG")
        self.Bind (wx.EVT_MENU,self.OpenMask,id=102)
        menu.Append (103,"&Close Image")
        self.Bind (wx.EVT_MENU,self.CloseImage,id=103)
        menu.Append (104,"&Close Mask")
        self.Bind (wx.EVT_MENU,self.CloseMask,id=104)
        menu.AppendSeparator()
        menu.Append (107,"&Save Image As...\tCtrl+S","File formats: TIFF,JPEG,PNG")
        self.Bind (wx.EVT_MENU,self.SaveImage,id=107)
        menu.Append (108,"&Save Mask As...","File formats: TIFF,JPEG,PNG")
        self.Bind (wx.EVT_MENU,self.SaveMask,id=108)
        menu.AppendSeparator()
        menu.Append (110,"E&xit","Terminates this application.")
        self.Bind (wx.EVT_MENU,self.OnExit,id=110)
        menuBar.Append (menu,"&File")
        menu = wx.Menu()
        menu.Append (201,"&Copy Image","Puts full image into clipboard")
        self.Bind (wx.EVT_MENU,self.CopyImage,id=201)
        menuBar.Append (menu,"&Edit")
        menu = self.OrientationMenu = wx.Menu()
        style = wx.ITEM_RADIO
        menu.Append (301,"Original","Do not rotate image",style)
        menu.Append (302,"Rotated Clockwise","Rotate image by -90 deg",style)
        menu.Append (303,"Rotated Counter-clockwise","Rotate image by +90 deg",style)
        menu.Append (304,"Upside down","Rotate image by 180 deg",style)
        for id in range(301,305): self.Bind (wx.EVT_MENU,self.OnOrientation,id=id)
        menuBar.Append (menu,"&Orientation")
        self.SetMenuBar (menuBar)
        # Controls
        self.CreateStatusBar()
        self.panel = wx.Panel(self)
        self.ImageViewer = ImageViewer (self.panel)
        self.LiveImage = wx.CheckBox (self.panel,label="Live")
        self.LiveImage.ToolTip = wx.ToolTip("Follow the data collection, show latest image")
        self.First = wx.Button(self.panel,label="|<",size=(40,-1))
        self.First.ToolTip = wx.ToolTip("Go to the first image in current directory")
        self.Bind (wx.EVT_BUTTON,self.OnFirst,self.First)
        self.Back = wx.Button(self.panel,label="< Back")
        self.Back.ToolTip = wx.ToolTip("Go to the previous image in current directory")
        self.Bind (wx.EVT_BUTTON,self.OnBack,self.Back)
        self.Next = wx.Button(self.panel,label="Next >")
        self.Next.ToolTip = wx.ToolTip("Go to the next image in current directory")
        self.Bind (wx.EVT_BUTTON,self.OnNext,self.Next)
        self.Last = wx.Button(self.panel,label=">|",size=(40,-1))
        self.Last.ToolTip = wx.ToolTip("Go to the last image in current directory")
        self.Bind (wx.EVT_BUTTON,self.OnLast,self.Last)
        self.Order = wx.Choice(self.panel,choices=["By Name","By Time"])
        self.Order.ToolTip = wx.ToolTip("Step through images by name or timestamp?")
        self.Filter = wx.ComboBox(self.panel,size=(85,-1),style=wx.TE_PROCESS_ENTER,
            choices=["*.*","*.mccd","*.rx","*.tif","*.tiff"])
        self.Filter.Value = "*.*"
        self.Filter.ToolTip = wx.ToolTip("Filter pattern for image files, e.g. *.tif")
        # Layout
        self.layout = wx.BoxSizer(wx.VERTICAL)
        self.layout.Add (self.ImageViewer,proportion=1,flag=wx.EXPAND) # growable
        self.Controls = wx.BoxSizer(wx.HORIZONTAL)
        self.Controls.AddSpacer((5,5))
        self.Controls.Add (self.LiveImage,flag=wx.ALIGN_CENTER)
        self.Controls.AddSpacer((5,5))
        self.Controls.Add (self.First,flag=wx.ALIGN_CENTER)
        self.Controls.Add (self.Back,flag=wx.ALIGN_CENTER)
        self.Controls.Add (self.Next,flag=wx.ALIGN_CENTER)
        self.Controls.Add (self.Last,flag=wx.ALIGN_CENTER)
        self.Controls.AddSpacer((5,5))
        self.Controls.Add (self.Order,flag=wx.ALIGN_CENTER)
        self.Controls.AddSpacer((5,5))
        self.Controls.Add (self.Filter,flag=wx.ALIGN_CENTER)
        self.Controls.AddSpacer((5,5))
        self.layout.Add (self.Controls,flag=wx.EXPAND)
        self.panel.SetSizer(self.layout)
        # Restore last saved settings.
        name = "ImageViewer"
        self.config_file=wx.StandardPaths.Get().GetUserDataDir()+"/"+name+".py"
        self.config = wx.FileConfig (localFilename=self.config_file)
        state = self.config.Read('State')
        if state:
            try: self.State = eval(state)
            except Exception,exception:
                print "Restore failed: %s: %s" % (exception,state)
        # Display images.
        from os.path import exists
        if exists(image_file): self.image_file = image_file
        if exists(mask_file): self.mask_file = mask_file
        # Initialization
        self.Orientation = self.ImageViewer.Orientation
        self.update_title()

        if show: self.Show()

        self.timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.update,self.timer)
        self.timer.Start(1000,oneShot=True)

    def OnFirst(self,event):
        """Go to the previous (older) image in current directory"""
        self.live_image = False
        next = newer_file if self.order == "By Time" else next_file
        self.image_file = next(self.image_file,-1e6,self.filter)

    def OnBack(self,event):
        """Go to the previous (older) image in current directory"""
        self.live_image = False
        next = newer_file if self.order == "By Time" else next_file
        self.image_file = next(self.image_file,-1,self.filter)

    def OnNext(self,event):
        """Go to the next (newer) image in current directory"""
        self.live_image = False
        next = newer_file if self.order == "By Time" else next_file
        self.image_file = next(self.image_file,+1,self.filter)
    
    def OnLast(self,event):
        """Go to the previous (older) image in current directory"""
        self.live_image = False
        next = newer_file if self.order == "By Time" else next_file
        self.image_file = next(self.image_file,+1e6,self.filter)

    def update(self,event=None):
        """Periodocally called on timer"""
        if self.live_image and self.image_to_show and \
           (self.image_to_show != self.image_file\
            or getmtime(self.image_to_show) != self.image_timestamp):
            ##print "loading",self.image_to_show
            self.image_file = self.image_to_show
        self.timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.update,self.timer)
        self.timer.Start(1000,oneShot=True)

    def get_live_image(self):
        """Follow the data collection"""
        return self.LiveImage.Value
    def set_live_image(self,value):
        self.LiveImage.Value = value
    live_image = property(get_live_image,set_live_image)        

    def get_order(self):
        """Follow the data collection"""
        return self.Order.StringSelection
    def set_order(self,value):
        self.Order.StringSelection = value
    order = property(get_order,set_order)        

    def get_filter(self):
        """Follow the data collection"""
        return self.Filter.Value
    def set_filter(self,value):
        self.Filter.Value = value
    filter = property(get_filter,set_filter)        

    def get_image_file(self):
        return getattr(self,"__image_file__","")
    def set_image_file(self,image_file):
        from os.path import exists
        from numimage import numimage
        try: image = numimage(image_file)
        except Exception,message:
            from sys import stderr
            stderr.write("%s: %s\n" % (image_file,message))
            image = None
        self.ImageViewer.Image = image
        self.image_timestamp = getmtime(image_file)
        self.__image_file__ = image_file
        self.update_title()
        ##print "image file: %r" % image_file
    image_file = property(get_image_file,set_image_file)

    def get_mask_file(self):
        return getattr(self.ImageViewer.Mask,"filename","")
    def set_mask_file(self,mask_file):
        from os.path import exists
        from numimage import numimage
        if not exists(mask_file): mask = None
        else:
            try: mask = numimage(mask_file)
            except Exception,message:
                from sys import stderr
                stderr.write("%s: %s\n" % (mask_file,message))
                mask = None
        self.ImageViewer.Mask = mask
        self.update_title()
    mask_file = property(get_mask_file,set_mask_file)

    def update_title(self):
        """Displays the file name of the current image in the title bar of the
        window."""
        from os.path import basename
        title = ""
        if self.image_file: title += self.image_file[-80:]+", "
        if self.mask_file:  title += "mask "+basename(self.mask_file)
        if len(title) < 40: title = "Image Viever - "+title
        title = title.strip("-, ")
        self.Title = title

    def OpenImage(self,event):
        """Open an image in te current Window"""
        from os.path import dirname,basename
        dlg = wx.FileDialog(self,"Open Image",
            wildcard="Image Files (*.mccd;*.tif;*.tiff;*.rx;*.png;*.jpg)|"\
                "*.mccd;*.tif;*.tiff;*.rx;*.png;*.jpg",
            defaultDir=dirname(self.image_file),
            defaultFile=basename(self.image_file),
            style=wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename = str(dlg.Path)
            self.image_file = filename
        dlg.Destroy()

    def NewWindow(self,event):
        """Open an image in a new Window"""
        from os.path import dirname,basename
        dlg = wx.FileDialog(self,"Open Image",
            wildcard="Image Files (*.mccd;*.tif;*.tiff;*.png;*.jpg)|"\
                "*.mccd;*.tif;*.tiff;*.png;*.jpg",
            defaultDir=dirname(self.image_file),
            defaultFile=basename(self.image_file),
            style=wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename = str(dlg.Path)
            app.OpenFile(filename)
        dlg.Destroy()


    @property
    def image_to_show(self):
        """Automatically load this image"""
        from DB import dbget
        from os.path import exists
        from numpy import array
        filenames = dbget("ImageViewer.images")
        try: filenames = array(eval(filenames))
        except: return ""
        filenames = filenames[array(exist_files(filenames))]
        if len(filenames) == 0: return ""
        return filenames[-1]

    def OpenMask(self,event):
        "Called from menu File/Open Mask..."
        from os.path import dirname,basename
        dlg = wx.FileDialog(self,"Open Image",
            wildcard="Image Files (*.png;*.tif;*.tiff;*.jpg)|"\
                "*.png;*.tif;*.tiff;*.jpg",
            defaultDir=dirname(self.mask_file),
            defaultFile=basename(self.mask_file),
            style=wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK: self.mask_file = str(dlg.Path)
        dlg.Destroy()

    def CloseImage(self,event):
        "Called from menu File/Close Mask..."
        self.ImageViewer.Image = None
        self.image_file = ""
        self.image_timestamp = 0
        self.update_title()

    def CloseMask(self,event):
        "Called from menu File/Close Mask..."
        self.mask_file = ""
        self.update_title()

    def SaveImage(self,event):
        "Called from menu File/Save Mask As..."
        dlg = wx.FileDialog(self,"Save Image As",wildcard="*.tif;*.png;*.jpg",
            defaultFile=self.image_file,style=wx.SAVE|wx.OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            self.image_file = str(dlg.Path)
            image = self.ImageViewer.Image
            image.save (self.image_file)
        dlg.Destroy()

    def SaveMask(self,event):
        "Called from menu File/Save Mask As..."
        if not self.ImageViewer.Mask: return
        dlg = wx.FileDialog(self,"Save Mask As",wildcard="*.png;*.tif;*.jpg",
            defaultFile=self.mask_file,style=wx.SAVE|wx.OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            self.mask_file = str(dlg.Path)
            mask = self.ImageViewer.Mask
            mask.save (self.mask_file)
        dlg.Destroy()

    def CopyImage(self,event):
        "Called from menu Edit/Copy Image"
        bitmap = wx.BitmapFromImage (self.ImageViewer.Image)
        bmpdo = wx.BitmapDataObject(bitmap)
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(bmpdo)
            wx.TheClipboard.Close()
        else: wx.MessageBox("Unexpected clipboard problem","Error")

    def OnOrientation(self,event):
        id = event.GetId()
        if id == 301: orientation = 0   # As image
        if id == 302: orientation = -90 # Rotated Clockwise
        if id == 303: orientation = +90 # Rotated Counter-clockwise
        if id == 304: orientation = 180 # Upside down
        self.Orientation = orientation
        self.ImageViewer.Orientation = orientation

    def GetOrientation(self):
        """Reads the image rotation as selected by the 'Orientation' menu.
        Returns either 0,-90,90 or 180"""
        if self.OrientationMenu.IsChecked(301): return 0
        if self.OrientationMenu.IsChecked(302): return -90
        if self.OrientationMenu.IsChecked(303): return 90
        if self.OrientationMenu.IsChecked(304): return 180

    def SetOrientation(self,value):
        """Updates the'Orientation' menu and the displayed image"""
        if value == 0:   self.OrientationMenu.Check(301,True)
        if value == -90: self.OrientationMenu.Check(302,True)
        if value == +90: self.OrientationMenu.Check(303,True)
        if value == 180: self.OrientationMenu.Check(304,True)

    Orientation = property (GetOrientation,SetOrientation,doc=
        "Image rotation as defined by the 'Orientation' menu")

    def GetState(self):
        "This is to save the current settings of the window"
        state = {}
        state["Size"] = self.Size
        state["Position"] = self.Position
        state["ImageViewer.State"] = self.ImageViewer.State
        state["mask_file"] = self.mask_file
        state["order"] = self.order
        state["filter"] = self.filter
        return state

    def SetState(self,state):
        "This is to restore the current state of the window"
        ##print "MainWindow: restoring %r" % state
        for key in state: exec("self."+key+"="+repr(state[key]))

    State = property(GetState,SetState,doc="settings of the window")

    def OnClose(self,event):
        "Called on File/Exit or when the widnows's close button is clicked"
        # Save settings for next time.
        from os.path import exists,dirname
        from os import makedirs
        directory = dirname(self.config_file)
        if not exists(directory): makedirs(directory)
        self.config.Write ('State',repr(self.State))
        self.config.Flush()

        app.CloseWindow(self)

    def OnExit(self,event):
        "Called on File/Exit or when the widnows's close button is clicked"
        # Save settings for next time.
        self.config.Write ('State',repr(self.State))
        self.config.Flush()

        app.ExitApp()


class ImageViewer (wx.Panel):
    """Grapical User Interface for inspecting images."""

    def __init__(self,parent):
        """Parent: top level window"""
        wx.Panel.__init__(self,parent)

        # Controls
        self.ImageWindow = ImageWindow(self)
        choices = ["200%","100%","50%","33%","25%","Fit Width"]
        self.ScaleFactorControl = wx.ComboBox(self,value="100%",
            choices=choices,style=wx.CB_DROPDOWN|wx.TE_PROCESS_ENTER)
        self.SaturationLevelText = wx.TextCtrl (self,size=(50,-1),
            style=wx.TE_PROCESS_ENTER)
        self.SaturationValue_modified = False
        self.SaturationLevelText.Bind (wx.EVT_CHAR,self.OnTypeSaturationValue)
        self.SaturationLevelSlider = wx.Slider (self,maxValue=1000)
        self.AutoContrastControl = wx.CheckBox (self,label="Auto")
        # Layout
        layout = wx.BoxSizer(wx.VERTICAL)
        layout.Add (self.ImageWindow,proportion=1,flag=wx.EXPAND) # growable
        layout.AddSpacer((2,2))
        controls = wx.BoxSizer(wx.HORIZONTAL)
        controls.AddSpacer((5,5))
        controls.Add (self.ScaleFactorControl,flag=wx.ALIGN_CENTER)
        controls.AddSpacer((5,5))
        controls.Add (self.SaturationLevelText,flag=wx.ALIGN_CENTER)
        controls.AddSpacer((5,5))
        # Make exposure slider growable (proportion=1)
        controls.Add (self.SaturationLevelSlider,proportion=1,flag=wx.ALIGN_CENTER)
        controls.AddSpacer((5,5))
        controls.Add (self.AutoContrastControl,flag=wx.ALIGN_CENTER)
        controls.AddSpacer((5,5))
        layout.Add (controls,flag=wx.EXPAND)
        self.SetSizer(layout)
        # Callbacks
        self.Bind (wx.EVT_COMBOBOX,self.OnChangeScaleFactor,self.ScaleFactorControl)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnChangeScaleFactor,self.ScaleFactorControl)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnterSaturationValue,self.SaturationLevelText)
        self.Bind (wx.EVT_SLIDER,self.OnMoveSlider,self.SaturationLevelSlider)
        self.Bind(wx.EVT_CHECKBOX,self.OnAutoContrast,self.AutoContrastControl)
        self.ImageWindow.Bind (wx.EVT_MOUSEWHEEL,self.OnMouseWheel)
        
        # Initialization
        self.ScaleFactor = self.ImageWindow.ScaleFactor
        self.SaturationLevelTextValue = self.ImageWindow.SaturationLevel
        self.SaturationLevelSliderValue = self.ImageWindow.SaturationLevel       

    def GetImage(self): return self.ImageWindow.Image

    def SetImage(self,image): self.ImageWindow.Image = image

    Image = property(GetImage,SetImage,doc="displayed image")

    def GetMask(self): return self.ImageWindow.Mask

    def SetMask(self,mask): self.ImageWindow.Mask = mask

    Mask = property(GetMask,SetMask,doc="bitmap overlaid to image")

    def GetPixelSize(self): return self.ImageWindow.PixelSize

    def SetPixelSize(self,value): self.ImageWindow.PixelSize = value

    PixelSize = property(GetPixelSize,SetPixelSize,doc="image raster in mm")

    def GetCenter(self): return self.ImageWindow.Crosshair

    def SetCenter(self,value): self.ImageWindow.Crosshair = value

    Center = property(GetCenter,SetCenter,doc="crosshair position in pixels")

    def OnChangeScaleFactor(self,event):
        "Called when a different zoom is selected"
        self.ImageWindow.ScaleFactor = self.ScaleFactorValue

    def GetScaleFactorValue(self):
        """Reads the image scale control and returns is a number between 0
        and 1, or None if 'Fit Width' is selected'."""
        selection = self.ScaleFactorControl.GetValue()
        try: return float(selection.strip("%"))/100
        except: return None

    def SetScaleFactorValue(self,scale):
        """Changes the scale control.
        scale is a number between 0 and 1, scale=None means 'Fit Width'"""
        if scale != None: self.ScaleFactorControl.SetValue("%.3g%%" % (scale*100.))
        else: self.ScaleFactorControl.SetValue("Fit Width")

    ScaleFactorValue = property (GetScaleFactorValue,SetScaleFactorValue,
        doc="Current value of scale control as float or None")

    def GetScaleFactor(self): return self.ImageWindow.ScaleFactor

    def SetScaleFactor (self,value):
        self.ImageWindow.ScaleFactor = value
        self.ScaleFactorValue = value

    ScaleFactor = property(GetScaleFactor,SetScaleFactor,doc=
        "Scale factor applied to image for display")

    def OnTypeSaturationValue(self,event):
        """Called when any test is typed in the exposure time field"""
        self.SaturationValue_modified = True
        # Pass this event on to further event handlers bound to this event.
        # Otherwise, the typed text does not appear in the window.
        event.Skip() 
        
    def OnEnterSaturationValue(self,event):
        """Called when Enter is pressed in the text box displaying the
        exposure time."""
        # Update the exposure time indicator
        self.SaturationLevelSliderValue = self.SaturationLevelTextValue
        # Apply the new exposure time to the image.
        self.ImageWindow.SaturationLevel = self.SaturationLevelTextValue
        self.ImageWindow.AutoContrast = False
        self.AutoContrastControl.SetValue(False)

        self.SaturationValue_modified = False
        
    def SetSaturationLevelTextValue(self,count):
        if not self.SaturationValue_modified:
            self.SaturationLevelText.SetValue("%.0f" % count)

    def GetSaturationLevelTextValue(self):
        text = self.SaturationLevelText.GetValue()
        try: return float(text)
        except: return 500.0 # default value: 500 counts

    SaturationLevelTextValue = property (GetSaturationLevelTextValue,
        SetSaturationLevelTextValue,
        doc="Count beyond which a pixel is rendred white")

    def OnMoveSlider(self,event):
        "Called if the slider controlling the exposure time is moved."
        # Update the exposure time indicator
        self.SaturationLevelTextValue = self.SaturationLevelSliderValue
        self.AutoContrastControl.SetValue(False)
        # Apply the new exposure time to the image.
        self.ImageWindow.AutoContrast = False
        self.ImageWindow.SaturationLevel = self.SaturationLevelSliderValue

    def GetSaturationLevelSliderValue(self):
        "Reads the exposure time in seconds from the slder position"
        # The slider position is an integer value from 0 to Max
        Max = self.SaturationLevelSlider.GetMax()
        fraction = float(self.SaturationLevelSlider.GetValue())/Max
        # This is translated into 0 to 65535 counts on a non-linear scale
        count = 65535 * fraction**2
        return count
    
    def SetSaturationLevelSliderValue(self,count):
        "Changes the slider position and exposure time indicator"
        # This translates the range 0 to 1 seconds non-linearly to a fraction
        # of the slider range.
        fraction = (count/65535.0)**0.5
        Max = self.SaturationLevelSlider.GetMax()
        self.SaturationLevelSlider.SetValue(fraction*Max)
        
    SaturationLevelSliderValue = property (GetSaturationLevelSliderValue,
        SetSaturationLevelSliderValue,
        doc="Count beyond which a pixel is rendred white")

    def GetSaturationLevel(self): return self.ImageWindow.SaturationLevel

    def SetSaturationLevel (self,value):
        self.ImageWindow.SaturationLevel = value
        self.SaturationLevelSliderValue = value
        self.SaturationLevelTextValue = value

    SaturationLevel = property(GetSaturationLevel,SetSaturationLevel,doc=
        "Count beyond which a pixel is rendered white")

    def OnAutoContrast(self,event):
        "Called when the 'Auto' Checkbox is clicked"
        self.ImageWindow.AutoContrast = self.AutoContrastControl.GetValue()
        self.SaturationLevelSliderValue = self.ImageWindow.SaturationLevel
        self.SaturationLevelTextValue = self.ImageWindow.SaturationLevel

    def GetAutoContrast(self): return self.ImageWindow.AutoContrast

    def SetAutoContrast (self,value):
        self.ImageWindow.AutoContrast = value
        self.AutoContrastControl.SetValue(value)

    AutoContrast = property(GetAutoContrast,SetAutoContrast,doc=
        "Automatically scale the image intensity")

    def GetOrientation(self): return self.ImageWindow.orientation

    def SetOrientation(self,value):
        self.ImageWindow.orientation = value
        self.ImageWindow.Refresh()

    Orientation = property (GetOrientation,SetOrientation,doc=
        "Image rotation as defined by the 'Orientation' menu")

    def GetState(self):
        "This is to save the current settings of the window"
        state = {}
        state["ScaleFactor"] = self.ScaleFactor
        state["SaturationLevel"] = self.SaturationLevel
        state["AutoContrast"] = self.AutoContrast
        state["ImageWindow.State"] = self.ImageWindow.State
        return state

    def SetState(self,state):
        "This is to restore the current state of the window"
        ##print "ImageView: restoring %r" % state
        for key in state: exec("self."+key+"="+repr(state[key]))

    State = property(GetState,SetState,doc="settings of the window")

    def OnMouseWheel(self,event):
        "Zoom in or out with the middle mouse scroll button."
        nsteps = event.GetWheelRotation()/event.GetWheelDelta()
        self.ScaleFactor *= 2**(0.25*nsteps)

    
class ImageWindow(wx.ScrolledWindow):
    def __init__(self,parent,pixelsize=None,**options):
        "pixelsize: in units of mm; used for measurements"
        wx.ScrolledWindow.__init__(self,parent,**options)

        from numpy import zeros,uint16
        from numimage import numimage
        self.image = numimage(zeros((2048,2048),uint16))
        self.mask = None
        self.scale_factor = 1.0
        # Crosshair coordinates in pixels from the top left
        self.crosshair = (1024,1024)
        self.pixelsize = 1.0
        if pixelsize: self.PixelSize = pixelsize;
        
        self.orientation = 0
        self.show_crosshair = True
        self.crosshair_size = (0.05,0.05) # default crosshair size: 50x50 um
        self.crosshair_color = wx.Colour(255,0,255) # magenta
        self.dragging = None
        self.scale = None # Measuement line drawn on the image
        self.scale_color = wx.Colour(128,128,255) # light blue
        self.show_scale = False # Draw measurement line drawn on the image?
        self.scale_selected = False
        self.boxsize = (0.1,0.06) # default box size: 100x60 um
        self.box_color = wx.Colour(128,128,255)
        self.show_box = False
        self.tool = None # Role of mouse pointer: measure, move crosshair
        self.saturation = 1000 # count beyond which a pixel is rendered white
        self.auto_contrast = False # automtically set contrast
        self.show_mask = True
        self.mask_color = (255,0,0) # red
        self.mask_opacity = 0.5 # 1 = opaque, 0 = invisible

        self.SetVirtualSize((self.Image.shape[-1],self.Image.shape[-2]))
        self.SetScrollRate(1,1)
        w,h = self.ImageSize
        self.ViewportCenter = w/2,h/2
        # Callbacks
        self.Bind (wx.EVT_PAINT, self.OnPaint)
        self.Bind (wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind (wx.EVT_SIZE, self.OnResize)
        self.Bind (wx.EVT_SCROLLWIN, self.OnScroll)
        self.Bind (wx.EVT_LEFT_DOWN, self.OnLeftButtonEvent)
        self.Bind (wx.EVT_LEFT_UP, self.OnLeftButtonEvent)
        self.Bind (wx.EVT_MOTION, self.OnLeftButtonEvent)
        self.Bind (wx.EVT_CONTEXT_MENU, self.OnContextMenu)

    def GetState(self):
        "This is to save the current settings of the window"
        state = {}
        state["orientation"] = self.orientation
        state["ViewportCenter"] = self.ViewportCenter
        state["tool"] = self.tool
        state["show_box"] = self.show_box
        state["boxsize"] = self.boxsize
        state["box_color"] = self.box_color
        state["show_scale"] = self.show_scale
        state["Scale"] = self.Scale
        state["pixelsize"] = self.PixelSize
        state["scale_color"] = self.scale_color
        state["show_crosshair"] = self.show_crosshair
        state["crosshair"] = self.crosshair
        state["crosshair_size"] = self.crosshair_size
        state["crosshair_color"] = self.crosshair_color
        state["show_mask"] = self.show_mask
        state["mask_color"] = self.mask_color
        state["mask_opacity"] = self.mask_opacity
        return state

    def SetState(self,state):
        "This is to restore the current state of the window"
        ##print "ImageWindow: Restoring %r" % state
        for key in state: exec("self."+key+"="+repr(state[key]))

    State = property(GetState,SetState,doc="settings of the window")

    def GetImage(self):
        """Displayed image as numpy array"""
        return self.image
    def SetImage(self,image):
        """Replaces to currently displayed image by a new image.
        The image size should not by 0."""
        self.image = image
        if self.image == None:
            from numpy import zeros,uint16
            from numimage import numimage
            self.image = numimage(zeros((2048,2048),uint16))
        if hasattr(image,"pixelsize") and not isnan(image.pixelsize):
            self.PixelSize = image.pixelsize
        self.adjust_contrast()
        w = self.image.shape[-2] * self.ScaleFactor
        h = self.image.shape[-1] * self.ScaleFactor
        self.SetVirtualSize ((w,h))
        # Preserve the viewport center.
        if hasattr(self,"viewport_center"):
            self.ViewportCenter = self.viewport_center
        self.Refresh()
    Image = property(GetImage,SetImage)

    def GetMask(self):
        """Bitmap overlayed to image as 2D numpy array of type boolean or 'None'
        """
        return self.mask
    def SetMask(self,mask):
        if mask != None: self.mask = (mask != 0)
        else: self.mask = None
        self.Refresh()
    Mask = property(GetMask,SetMask)

    def GetPixelSize(self): return self.pixelsize

    def SetPixelSize(self,value):
        if not value: value = 1.0
        if value != self.pixelsize:
            self.pixelsize = value
            self.Refresh()

    PixelSize = property(GetPixelSize,SetPixelSize,doc="image raster in mm")

    def GetScaleFactor(self):
        "Returns the scale factor to be applied to image for display"
        scale = self.scale_factor
        if scale == None: # Fit image into the width of the window
            if self.Image.shape[-2] != 0:
                scale = float(self.GetClientSize().x)/self.Image.shape[-2]
            else: scale = 1.0
        return scale

    def SetScaleFactor (self,value):
        if value != self.scale_factor:
            self.scale_factor = value
            w = self.Image.shape[-2] * self.ScaleFactor
            h = self.Image.shape[-1] * self.ScaleFactor
            self.SetVirtualSize ((w,h))
            # Preserve the viewport center.
            if hasattr(self,"viewport_center"):
                self.ViewportCenter = self.viewport_center
            self.Refresh()

    ScaleFactor = property(GetScaleFactor,SetScaleFactor,doc=
        "Scale factor applied to image for display")

    def OnResize (self,event):
        w = self.Image.shape[-2] * self.ScaleFactor
        h = self.Image.shape[-1] * self.ScaleFactor
        self.SetVirtualSize ((w,h))
        # Preserve the viewport center.
        if hasattr(self,"viewport_center"):
            self.ViewportCenter = self.viewport_center
        self.Refresh()

    def OnScroll (self,event):
        "Called on every scroll event"
        event.Skip() # call default event handler
        # Only by scrolling the viewport center is allowed to change, not by
        # resizing or zooming.
        if hasattr(self,"viewport_center"):
            self.viewport_center = self.ViewportCenter

    def GetSaturationLevel(self): return self.saturation

    def SetSaturationLevel (self,value):
        if value != self.saturation:
            self.saturation = value
            self.Refresh()

    SaturationLevel = property(GetSaturationLevel,SetSaturationLevel,doc=
        "Count beyond which a pixel is rendered white")

    def GetAutoContrast (self): return self.auto_contrast

    def SetAutoContrast (self,value):
        if value != self.auto_contrast:
            self.auto_contrast = value
            self.adjust_contrast()
            self.Refresh()

    AutoContrast = property(GetAutoContrast,SetAutoContrast,doc=
        "Automatically scale the image intensity")

    def adjust_contrast (self):
        "This automatically scales the intensity of the image."
        if not self.AutoContrast: return
        from numpy import average,histogram
        image = self.Image
        # Convert to grayscale if needed.
        if image.ndim > 2: image = average(image,axis=0)
        # Set the saturation level such that 99% of all pixels are
        # below saturation level.
        hist = histogram(image,bins=65536,range=[0,65535],normed=True)[0]
        ##print "sum(hist) = %g" % sum(hist)
        integral = 0
        for i in range(0,65536):
            integral += hist[i]
            if integral > 0.99: break
        ##print "sum(hist[0:%d]) = %g" % (i,sum(hist[0:i]))
        self.SaturationLevel = i

    def GetImageSize(self):
        w,h = self.Image.shape[-2:]
        return w*self.PixelSize,h*self.PixelSize

    ImageSize = property(GetImageSize,doc="width and height of image in mm")

    def GetViewportCenter(self):
        """Center (x,y) coordinates of the part of the image displayed in the
        window in mm with respect to the top left corner of the image.
        """
        w,h = self.ClientSize
        x0,y0 = self.ViewStart
        sx,sy = self.GetScrollPixelsPerUnit()
        ox,oy = self.origin()
        s = self.ScaleFactor
        dx = self.PixelSize
        cx,cy = (x0*sx-ox+w/2)/s*dx, (y0*sy-oy+h/2)/s*dx
        return cx,cy
    
    def SetViewportCenter(self,(cx,cy)):
        """Scroll such than the center the window is x mm from the
        left edge and y mm from the top edge of the image.
        """
        w,h = self.ClientSize
        sx,sy = self.GetScrollPixelsPerUnit()
        ox,oy = self.origin()
        s = self.ScaleFactor
        dx = self.PixelSize
        
        x0 = cx/sx/dx*s-w/2+ox
        y0 = cy/sx/dx*s-h/2+oy
        self.Scroll(x0,y0)

        self.viewport_center = self.GetViewportCenter()

    ViewportCenter = property(GetViewportCenter,SetViewportCenter,
        doc=GetViewportCenter.__doc__)

    def GetImageOrigin(self):
        if self.crosshair != None: x,y = self.crosshair
        else: x,y = (self.Image.shape[-2]/2,self.Image.shape[-1]/2)
        w,h = self.Image.shape[-2:]
        return -x*self.PixelSize,-(h-y)*self.PixelSize

    ImageOrigin = property(GetImageOrigin,doc="image center defined by crosshair")

    def GetCrosshair(self):
        "Returns the crosshair coordinates in pixels from the top left as (x,y) tuple"
        return self.crosshair

    def SetCrosshair (self,position):
        "position must be a tuple (x,y)"
        self.crosshair = position
        self.Refresh()

    Crosshair = property(GetCrosshair,SetCrosshair,doc=
        "Coordinates of cross displayed on the image in pixels from top left")
    
    def GetScale(self):
        "Returns list of tuples [(x1,y1),(x2,y2)]"
        return self.scale

    def SetScale (self,line):
        "'line' must be a list of tuples [(x1,y1),(x2,y2)]"
        self.scale = line
        self.Refresh()

    Scale = property(GetScale,SetScale,doc="""movable measurement line drawn
        on the image, format [(x1,y1),(x2,y2)]""")

    def GetScaleUnit(self):
        "mm or pixels"
        if self.PixelSize != 1: return "mm"
        else: return "pixels"

    ScaleUnit = property(GetScaleUnit)

    def origin(self):
        """
        Top left corner of the image in virtual pixel coordinates.
        (Orgin: top left of the vitual scrolling area = (0,0)).
        By default, a Scrolled Window places its active area in the top
        left, if it is smaller than the window size.
        Instead, I want it centered in the window.
        The function calculates the active area origin as function of window
        size.
        """
        width,height = self.GetSizeTuple()
        x = (width  - self.Image.shape[-2]*self.ScaleFactor)/2
        y = (height - self.Image.shape[-1]*self.ScaleFactor)/2
        if x<0: x = 0
        if y<0: y = 0
        return x,y
    
    def rotate(self,point):
        "used to apply the rotation to the image center to the cross-hair"
        if point == None: return
        (x,y) = point
        (w,h) = (self.Image.shape[-2],self.Image.shape[-1])
        if self.orientation == 0: return (x,y)
        if self.orientation == -90: return (h-y,x)
        if self.orientation == 90: return (y,w-x)
        if self.orientation == 180: return (w-x,h-y)
        return (x,y)
        
    def unrotate(self,point):
        "used to apply the rotation to the image center to the cross-hair"
        if point == None: return
        (x,y) = point
        (w,h) = (self.Image.shape[-2],self.Image.shape[-1])
        if self.orientation == 0: return (x,y)
        if self.orientation == -90: return (y,h-x)
        if self.orientation == 90: return (w-y,x)
        if self.orientation == 180: return (w-x,h-y)
        return (x,y)

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
        width,height = self.GetSizeTuple()
        dc.DrawRectangle (0,0,width,height)

        # This centers the image in the window, if the window is larger than
        # the image.
        if dc.GetDeviceOriginTuple() == (0,0):
            dc.SetDeviceOrigin(*self.origin())
    
        self.draw(dc)

    def OnEraseBackground(self, event):
        """Override default background fill, avoiding flickering"""

    def draw (self,dc):
        """Render the contents of the window."""
        from numpy import uint8,ndarray

        from time import time; t = [time()]; m = ""
        # Compress the dynamic range from 0...SaturationLevel to 0...256.
        scale = 255./max(self.SaturationLevel,1)
        image = minimum(self.Image*scale,255).astype(uint8)
        t += [time()]; m += "Scale to 8 bits %.3f s\n" % (t[-1]-t[-2])

        # Convert from gray scale to  RGB format if needed.        
        if image.ndim < 3:
            w,h = self.Image.shape[-2:]
            RGB = ndarray((3,w,h),uint8,order="F")
            RGB[0],RGB[1],RGB[2] = image,image,image
            image = RGB
        t += [time()]; m += "RGB array %.3f s\n" % (t[-1]-t[-2])

        # Superimpose the mask if present.
        if self.show_mask and self.Mask != None:
            mask = self.Mask
            R,G,B = image
            r,g,b = self.mask_color
            x = self.mask_opacity
            R[mask] = (1-x)*R[mask]+x*r
            G[mask] = (1-x)*G[mask]+x*g
            B[mask] = (1-x)*B[mask]+x*b
        t += [time()]; m += "Mask %.3f s\n" % (t[-1]-t[-2])

        # Convert image from numpy to WX image format.
        ##data = image.T.tostring()
        ##t += [time()]; m += "Transpose %.3f s\n" % (t[-1]-t[-2])
        data = image
        w,h = self.Image.shape[-2:]
        image = wx.ImageFromData(w,h,data)
        t += [time()]; m += "WX image %.3f s\n" % (t[-1]-t[-2])

        # Scale the image.
        w = image.Width  * self.ScaleFactor
        h = image.Height * self.ScaleFactor
        # Use 'quality=wx.IMAGE_QUALITY_HIGH' for bicubic and box averaging
        # resampling methods for upsampling and downsampling respectively.
        if self.ScaleFactor < 1: quality = wx.IMAGE_QUALITY_HIGH
        else: quality = wx.IMAGE_QUALITY_NORMAL
        image = image.Scale(w,h) ## quality=quality
        t += [time()]; m += "Resample %.3f s\n" % (t[-1]-t[-2])

        if self.orientation == 90:  image=image.Rotate90(clockwise=False)
        if self.orientation == -90: image=image.Rotate90(clockwise=True)
        if self.orientation == 180: image=image.Rotate90().Rotate90()
        t += [time()]; m += "Rotate %.3f s\n" % (t[-1]-t[-2])

        bitmap = wx.BitmapFromImage(image)
        t += [time()]; m += "WX bitmap %.3f s\n" % (t[-1]-t[-2])
        dc.DrawBitmap (bitmap,0,0)
        t += [time()]; m += "Render %.3f s\n" % (t[-1]-t[-2])

        self.draw_crosshair(dc)
        self.draw_box(dc)
        self.draw_scale(dc)
        t += [time()]; m += "Annotate %.3f s\n" % (t[-1]-t[-2])

        m += "Total %.3f s\n" % (t[-1]-t[0])

        ##print m

    def draw_crosshair (self,dc):
        "Indicates the X-ray beam position as a cross"
        if self.show_crosshair and self.crosshair != None:
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
        if not self.show_scale or self.scale == None: return
        P1,P2 = self.scale
        x1,y1 = self.pixel(P1)
        x2,y2 = self.pixel(P2)
        dc.SetPen (wx.Pen(self.scale_color,1))
        dc.DrawLine (x1,y1,x2,y2)

        length = distance(P1,P2)
        if self.ScaleUnit == "mm":
            if length < 1: label = "%.0f um" % (length*1000)
            else: label = "%.3f mm" % length
        else: label = "%g %s" % (length,self.ScaleUnit)
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
        
    def pixel(self,(x,y)):
        "Converts from mm (x,y) to virtual pixel coordinates"
        if self.crosshair != None: center = self.crosshair
        else: center = (self.Image.shape[-2]/2,self.Image.shape[-1]/2)
        px = int(round((x/self.PixelSize+center[0])*self.ScaleFactor))
        py = int(round((-y/self.PixelSize+center[1])*self.ScaleFactor))
        return px,py

    def point(self,(px,py)):
        "Converts from pixel virtual (px,py) to mm (x,y) coordinates"
        if self.crosshair != None: center = self.crosshair
        else: center = (self.Image.shape[-2]/2,self.Image.shape[-1]/2)
        x =  (px/self.ScaleFactor-center[0])*self.PixelSize
        y = -(py/self.ScaleFactor-center[1])*self.PixelSize
        return x,y

    def SetStatusText(self,status_text):
        "display the in the status bar of te top level window"
        window = self.Parent
        while not hasattr(window,"SetStatusText"): window = window.Parent
        window.SetStatusText(status_text)        

    def OnLeftButtonEvent (self,event):
        "for dragging the crosshair or scale"
        # This makes sure that keyboard input goes to this window seleting
        # it by clicking the mouse button inside.
        # It makes also sure that mouse wheel events are received.
        if event.LeftDown(): self.SetFocus()
        
        p = self.cursor_pos(event)

        if event.LeftDown() or event.Dragging():
            # Report the image pixle coordinates and pixel intenity at the
            # Cursor position in the window's status bar.
            from math import floor
            x,y = int(floor(p[0]/self.ScaleFactor)),int(floor(p[1]/self.ScaleFactor))
            w,h = self.Image.shape[-2:]
            if x >= 0 and x < w and y >= 0 and y < h:
                if self.Image.ndim == 2: count = self.Image[x,y]
                elif self.Image.ndim == 3: count = self.Image[:,x,y]
                self.SetStatusText("(%d,%d) count %s" % (x,y,count))
            else: self.SetStatusText("")
        
        if self.scale != None:
            p1,p2 = self.pixel(self.scale[0]),self.pixel(self.scale[1])
        else: p1,p2 = ((-100,-100),(-100,-100))

        if self.MoveCrosshair:    
            if event.LeftDown():
                self.SetFocus()
                self.set_crosshair(event)
                self.CaptureMouse()
                self.dragging = "crosshair"
                self.Refresh()
            elif event.Dragging() and self.dragging:
                self.set_crosshair(event)
                self.Refresh()
            elif event.LeftUp() and self.dragging:
                self.ReleaseMouse()
                self.dragging = None
                self.Refresh()
        elif self.show_scale or self.tool == "measure":
            if event.LeftDown():
                if self.tool == "measure":
                    P = self.point(p)
                    self.scale = [P,P]
                    self.show_scale = True
                    self.dragging = "scale2"
                    self.scale_selected = False
                else:
                    if point_line_distance(p,(p1,p2)) < 5: self.scale_selected = True
                    else: self.scale_selected = False
                    if point_line_distance(p,(p1,p2)) < 5:
                        self.dragging = (self.point(p),list(self.scale))
                    if distance(p1,p) < 5: self.dragging = "scale1"
                    if distance(p2,p) < 5: self.dragging = "scale2"
                if self.dragging:
                    self.SetFocus()
                    self.set_scale(event)
                    self.CaptureMouse()
                self.Refresh()
            elif event.Dragging() and self.dragging:
                self.set_scale(event)
                self.Refresh()
            elif event.LeftUp() and self.dragging:
                self.ReleaseMouse()
                self.dragging = None
                self.Refresh()
                
        # Update the pointer shape to reflect the mouse function.
        if self.MoveCrosshair:    
            self.SetCursor (wx.StockCursor(wx.CURSOR_PENCIL))
            #self.SetCursor (self.crosshair_cursor) # garbled under Linux
            # CURSOR_CROSS would be better than CURSOR_PENCIL.
            # However, under Windows, the cross cursor does not have a white
            # border and is hard to see on black background.
        elif self.tool == "measure":
            self.SetCursor (wx.StockCursor(wx.CURSOR_PENCIL))
        elif self.dragging == "scale1" or self.dragging == "scale2":
            self.SetCursor (wx.StockCursor(wx.CURSOR_SIZENESW))
        elif self.dragging: self.SetCursor(wx.StockCursor(wx.CURSOR_SIZING))
        elif self.scale_selected and (distance(p1,p) < 5 or distance(p2,p) < 5):
            self.SetCursor(wx.StockCursor(wx.CURSOR_SIZENESW))
        elif point_line_distance(p,(p1,p2)) < 5:
            self.SetCursor(wx.StockCursor(wx.CURSOR_SIZING))
        else: self.SetCursor (wx.StockCursor(wx.CURSOR_DEFAULT))
        # CURSOR_SIZENESW would be better when the pointer is hovering over
        # the and of the end point.
        # However, under Linux, the pointer shape does not update
        # to CURSOR_PENCIL while dragging, only after the mouse button is
        # released.
        # CURSOR_CROSS would be better than CURSOR_PENCIL.
        # However, under Windows, the cross cursor does not have a white
        # border and is hard to see on black background.
                
    def set_crosshair (self,event):
        "Updates the crosshair position based on the last mouse event"
        x,y = self.cursor_pos(event)
        self.crosshair = (int(round(x/self.ScaleFactor)),int(round(y/self.ScaleFactor)))

    def set_scale (self,event):
        "Updates the scale based on the last mouse event"
        p = self.cursor_pos(event)
        if self.dragging == "scale1": self.scale[0] = self.point(p)
        elif self.dragging == "scale2": self.scale[1] = self.point(p)
        else:
            P = self.point(p)
            P0,(P1,P2) = self.dragging
            self.scale[0] = translate(P1,vector(P0,P))
            self.scale[1] = translate(P2,vector(P0,P))

    def cursor_pos (self,event):
        """cursor position (x,y) during the given event, in virtual pixel
        coordinates, relative to the top left corner of the image, in units
        of screen pixels (not image pixels).
        """
        x,y = self.CalcUnscrolledPosition (event.GetX(),event.GetY())
        ox,oy = self.origin()
        return x-ox,y-oy

    def OnContextMenu (self,event):
        menu = wx.Menu()
        menu.Append (10,"Show Mask","",wx.ITEM_CHECK)
        if self.show_mask: menu.Check(10,True)
        self.Bind (wx.EVT_MENU,self.OnShowMask,id=10)
        menu.Append (1,"Show Scale","",wx.ITEM_CHECK)
        if self.show_scale: menu.Check(1,True)
        self.Bind (wx.EVT_MENU,self.OnShowScale,id=1)
        menu.Append (2,"Show Box","",wx.ITEM_CHECK)
        if self.show_box: menu.Check(2,True)
        self.Bind (wx.EVT_MENU,self.OnShowBox,id=2)
        menu.Append (6,"Show Crosshair","",wx.ITEM_CHECK)
        if self.show_crosshair: menu.Check(6,True)
        self.Bind (wx.EVT_MENU,self.OnShowCrosshair,id=6)
        menu.AppendSeparator()
        menu.Append (7,"Measure","",wx.ITEM_CHECK)
        self.Bind (wx.EVT_MENU,self.OnMeasure,id=7)
        if self.tool == "measure": menu.Check(7,True)
        menu.AppendSeparator()
        if self.show_scale: menu.Append (8,"Scale...","")
        self.Bind (wx.EVT_MENU,self.OnScaleProperties,id=8)
        if self.show_crosshair: menu.Append (4,"Crosshair...","")
        self.Bind (wx.EVT_MENU,self.OnCrosshairProperties,id=4)
        if self.show_box: menu.Append (5,"Box...","")
        self.Bind (wx.EVT_MENU,self.OnBoxProperties,id=5)
        
        # Display the menu. If an item is selected then its handler will
        # be called before 'PopupMenu' returns.
        self.PopupMenu(menu)
        menu.Destroy()

    def OnShowMask (self,event):
        "Called if 'Show Scale' is selected from the context menu"
        self.show_mask = not self.show_mask
        self.Refresh()

    def OnShowScale (self,event):
        "Called if 'Show Scale' is selected from the context menu"
        self.show_scale = not self.show_scale
        if self.show_scale and self.scale == None: self.set_default_scale()
        self.Refresh()

    def set_default_scale(self):
        "Set default position for scale"
        w,h = self.ImageSize; x,y = self.ImageOrigin 
        l = 0.4*w; l = round(l,int(round(-log10(l)+0.5)))
        self.scale = [(x+w*0.5-l/2,y+h*0.05),(x+w*0.5+l/2,y+h*0.05)]

    def OnShowBox (self,event):
        "Called if 'Show Box' is selected from the context menu"
        self.show_box = not self.show_box
        self.Refresh()

    def OnShowCrosshair (self,event):
        "Called if 'Show Crosshair' is selected from the context menu"
        self.show_crosshair = not self.show_crosshair
        self.Refresh()

    def GetMoveCrosshair (self): return (self.tool == "move crosshair")
    
    def SetMoveCrosshair (self,value):
        if value == True: self.tool = "move crosshair"
        else: self.tool = None

    MoveCrosshair = property(GetMoveCrosshair,SetMoveCrosshair,doc=
        "Determines whether the crosshair is movable or locked")

    def OnMeasure (self,event):
        "Called if 'Measure' is selected from the context menu"
        if self.tool != "measure": self.tool = "measure"
        else: self.tool = None

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
            

class CrosshairProperties (wx.Dialog):
    """Allows the user to to read the cross position, enter the position
    numerically and change its color."""
    def __init__ (self,parent):
        wx.Dialog.__init__(self,parent,-1,"Crosshair")
        # Controls
        self.Coordinates = wx.TextCtrl (self,size=(75,-1),
            style=wx.TE_PROCESS_ENTER)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnterCoordinates,self.Coordinates)
        self.Coordinates.SetValue("%d,%d" % parent.Crosshair)
        self.Movable = wx.CheckBox(self,label="Movable")
        self.Bind (wx.EVT_CHECKBOX,self.OnMovable,self.Movable)
        if parent.MoveCrosshair: self.Movable.SetValue(True)
        self.CrosshairSize = wx.TextCtrl (self,size=(75,-1),
            style=wx.TE_PROCESS_ENTER)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnterCrosshairSize,
            self.CrosshairSize)
        self.CrosshairSize.SetValue("%.3f,%.3f" % parent.crosshair_size)
        self.ShowCrosshair = wx.CheckBox(self,label="Show")
        self.Bind (wx.EVT_CHECKBOX,self.OnShowCrosshair,self.ShowCrosshair)
        if parent.show_crosshair: self.ShowCrosshair.SetValue(True)
        h = self.Coordinates.GetSize().y
        from wx.lib.colourselect import ColourSelect,EVT_COLOURSELECT
        self.Color = ColourSelect (self,colour=parent.crosshair_color,size=(h,h))
        self.Color.Bind (EVT_COLOURSELECT,self.OnSelectColour)
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

        self.Bind (wx.EVT_CLOSE,self.OnClose)
        
    def OnEnterCoordinates(self,event):
        text = self.Coordinates.GetValue()
        try:
            (tx,ty) = text.split(",")
            self.GetParent().Crosshair = (float(tx),float(ty))
        except ValueError: return

    def OnMovable(self,event):
        self.GetParent().MoveCrosshair = self.Movable.GetValue()

    def OnEnterCrosshairSize(self,event):
        text = self.CrosshairSize.GetValue()
        try:
            (tx,ty) = text.split(",")
            self.GetParent().crosshair_size = (float(tx),float(ty))
        except ValueError: return
        self.GetParent().Refresh()

    def OnShowCrosshair(self,event): 
        self.GetParent().show_crosshair = self.ShowCrosshair.GetValue()
        self.GetParent().Refresh()

    def OnSelectColour(self,event): 
        self.GetParent().crosshair_color = event.GetValue()
        self.GetParent().Refresh()

    def OnClose(self,event):
        """Called when the close button is clocked.
        When the dialog is closed automatically lock the crosshair."""
        self.GetParent().MoveCrosshair = False
        self.Destroy()

class BoxProperties (wx.Dialog):
    """Allows the user to change the box size and color"""
    def __init__ (self,parent):
        wx.Dialog.__init__(self,parent,-1,"Box")
        # Controls
        self.BoxSize = wx.TextCtrl (self,size=(75,-1),
            style=wx.TE_PROCESS_ENTER)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnterBoxSize,self.BoxSize)
        self.BoxSize.SetValue("%.3f,%.3f" % parent.boxsize)
        self.ShowBox = wx.CheckBox(self,label="Show")
        self.Bind (wx.EVT_CHECKBOX,self.OnShowBox,self.ShowBox)
        if parent.show_box: self.ShowBox.SetValue(True)
        h = self.BoxSize.GetSize().y
        from wx.lib.colourselect import ColourSelect,EVT_COLOURSELECT
        self.Color = ColourSelect (self,colour=parent.box_color,size=(h,h))
        self.Color.Bind (EVT_COLOURSELECT,self.OnSelectColour)
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
        
    def OnEnterBoxSize(self,event):
        text = self.BoxSize.GetValue()
        try:
            (tx,ty) = text.split(",")
            self.GetParent().boxsize = (float(tx),float(ty))
        except ValueError: return
        self.GetParent().Refresh()

    def OnShowBox(self,event): 
        self.GetParent().show_box = self.ShowBox.GetValue()
        self.GetParent().Refresh()

    def OnSelectColour(self,event): 
        self.GetParent().box_color = event.GetValue()
        self.GetParent().Refresh()


class ScaleProperties (wx.Dialog):
    """Allows the user to enter the length of the measurement scale numerically,
    make the line exactly horizonal or vertical and change its color.
    """
    def __init__ (self,parent):
        wx.Dialog.__init__(self,parent,-1,"Scale")
        # Controls
        self.Length = wx.TextCtrl (self,size=(60,-1),style=wx.TE_PROCESS_ENTER)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnterLength,self.Length)
        (P1,P2) = parent.scale; length = distance(P1,P2)
        self.Length.SetValue("%.3f" % length)
        self.Pixelsize = wx.TextCtrl (self,size=(60,-1),
            style=wx.TE_PROCESS_ENTER)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnterPixelsize,self.Pixelsize)
        self.Pixelsize.SetValue("%.3f" % parent.pixelsize)
        self.Horizontal = wx.CheckBox (self,label="Horizontal")
        self.Bind (wx.EVT_CHECKBOX,self.OnHorizontal,self.Horizontal)
        self.Vertical = wx.CheckBox (self,label="Vertical")
        self.Bind (wx.EVT_CHECKBOX,self.OnVertical,self.Vertical)
        v = vector(P1,P2)
        if v[1] == 0: self.Horizontal.SetValue(True)
        if v[0] == 0: self.Vertical.SetValue(True)
        h = self.Length.GetSize().y
        from wx.lib.colourselect import ColourSelect,EVT_COLOURSELECT
        self.Color = ColourSelect (self,-1,"",parent.scale_color,size=(h,h))
        self.Color.Bind (EVT_COLOURSELECT,self.OnSelectColour)
        # Layout
        layout = wx.FlexGridSizer (cols=2,hgap=5,vgap=5)
        label = wx.StaticText (self,label="Length ["+parent.ScaleUnit+"]:")
        layout.Add (label,flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add (self.Length,flag=wx.ALIGN_CENTER_VERTICAL)
        label = wx.StaticText (self,label="Pixel size [mm]:")
        layout.Add (label,flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add (self.Pixelsize,flag=wx.ALIGN_CENTER_VERTICAL)
        label = wx.StaticText (self,label="Direction:")
        layout.Add (label,flag=wx.ALIGN_CENTER_VERTICAL)
        group = wx.BoxSizer()
        group.Add (self.Horizontal)
        group.AddSpacer((5,5))
        group.Add (self.Vertical)
        layout.Add (group)
        label = wx.StaticText (self,label="Line color:")
        layout.Add (label,flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add (self.Color,flag=wx.ALIGN_CENTER_VERTICAL)
        self.SetSizer(layout)
        self.Fit()
        
    def OnEnterLength(self,event):
        text = self.Length.GetValue()
        try: length = float(text)
        except ValueError: return
        parent = self.GetParent()
        (P1,P2) = parent.scale
        P2 = translate(P1,scale(direction(vector(P1,P2)),length))
        parent.scale = [P1,P2]
        parent.Refresh()

    def OnEnterPixelsize(self,event):
        text = self.Pixelsize.Value
        try: value = float(text)
        except ValueError: self.Pixelsize.Value = "1.000"; return
        parent = self.Parent
        parent.pixelsize = value
        parent.Refresh()

    def OnHorizontal(self,event): 
        self.Horizontal.SetValue(True); self.Vertical.SetValue(False)
        parent = self.GetParent()
        (P1,P2) = parent.scale; length = distance(P1,P2)
        P2 = translate(P1,(length,0))
        parent.scale = [P1,P2]
        parent.Refresh()

    def OnVertical(self,event): 
        self.Horizontal.SetValue(False); self.Vertical.SetValue(True)
        parent = self.GetParent()
        (P1,P2) = parent.scale; length = distance(P1,P2)
        P2 = translate(P1,(0,length))
        parent.scale = [P1,P2]
        parent.Refresh()

    def OnSelectColour(self,event): 
        self.GetParent().scale_color = event.GetValue()
        self.GetParent().Refresh()


def distance ((x1,y1),(x2,y2)):
    "Distance between two points"
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

def vector((x1,y1),(x2,y2)):
    "Vector from point (x1,y1) to point (x2,y2)"
    return (x2-x1,y2-y1)
    
def translate((x,y),(vx,vy)):
    "Applies the vector (vx,vy) to point (x,y)"
    return (x+vx,y+vy)

def scale((x,y),a):
    "Multiplies vector with scalar"
    return (a*x,a*y)

def direction((x,y)):
    "Vector (x,y) scaled to unit length"
    l = sqrt(x**2+y**2)
    if l == 0: return (1.,0.)
    return (x/l,y/l)

def dot((x1,y1),(x2,y2)):
    "Scalar product between vectors (x1,y1) and (x2,y2)"
    return x1*x2+y1*y2

class ImageViewer_App(wx.App):
    windows = []
    
    def OnInit(self):
        image_file = mask_file = ""
        # Check whether command line argumuments have been passed.
        from sys import argv
        ##print "argv: %r" % argv
        # Take the first parameter as the file name of an image to be displayed.
        if len(argv) > 1 and argv[1]!= "" and not argv[1].startswith("-"):
            image_file = argv[1]
        # If a second image file name is given, use this image as mask.
        if len(argv) > 2 and argv[2]!= "" and not argv[2].startswith("-"):
            mask_file = argv[2]

        self.windows  += [ImageViewer_Window(image_file=image_file,mask_file=mask_file)]
        self.SetTopWindow(self.windows[0])
        return True

    def MacOpenFile (self,filename):
        """Callback handler for OpenFile events.
        In order to have your application handle files that are dropped
        on the application icon, and respond to double-clicking on some file
        types from the Finder, override this method in your wxApp"""
        from sys import stderr
        ##stderr.write("MacOpenFile %r\n" % filename)
        from os.path import isfile
        if not isfile(filename) or filename.endswith(".py"):
            ##stderr.write("MacOpenFile: Spurious OpenFile event %r" % filename)
            return
        # Check if image is already open. If yes, bring its window to front.
        for window in self.windows:
            if window.image_file == filename: window.Raise(); return
        # If the first window was opened as empty window without image, use
        # that window to display the image.
        if len(self.windows)>0 and not self.windows[0].image_file:
            self.windows[0].set_image_file (filename); return
        # Open image in a new window.
        self.windows  += [ImageViewer_Window(image_file=filename)]

    def OpenFile (self,filename):
        """Open the image 'filename' in a new window."""
        from os.path import exists
        if not exists(filename):
            from sys import stderr
            stderr.write("OpenFile: File %r not found" % filename)
            return
        # Check if image is already open. If yes, bring its window to front.
        for window in self.windows:
            if window.image_file == filename: window.Raise(); return
        # If the first window was opened as empty window without image, use
        # that window to display the image.
        if len(self.windows)>0 and not self.windows[0].image_file:
            self.windows[0].set_image_file (filename); return
        # Open image in a new window.
        self.windows  += [ImageViewer_Window(image_file=filename)]

    def CloseWindow(self,window):
        """"""
        window.Show(False)
        window.Destroy()
        if window in self.windows: self.windows.remove(window)
        ##if len(self.windows) == 0: self.Exit() - does not seem to be needed

    def ExitApp(self):
        for window in self.windows: window.Show(False)
        for window in self.windows: window.Destroy()
        self.windows = []
        ##wx.App.Exit(self)

class ImageViewerInterface(object):
    def get_images(self):
        """filenames: list of pathnames"""
        from DB import dbget
        images = dbget("ImageViewer.images")
        try: images = eval(images)
        except: images = []
        return images
    def set_images(self,filenames):
        """filenames: list of pathnames"""
        from DB import dbput
        dbput("ImageViewer.images",repr(filenames).replace("\n",""))
    images = property(get_images,set_images)

image_viewer = ImageViewerInterface()

def newer_file(filename,count=1,filter="*"):
    """the file with the higher(newer) timestamp in the same directory.
    If the is none return the current filename.
    count: 1 for newer file (default), -1 for older file"""
    from os.path import dirname,exists,isdir
    from glob import glob
    from numpy import argsort,array,where,clip
    dir = dirname(filename)
    files = glob(dir+"/"+filter)
    files = array([f for f in files if not isdir(f)])
    timestamps = array([getmtime(f) for f in files])
    order = argsort(timestamps)
    timestamps = timestamps[order]
    files = files[order]
    if len(files) == 0: return filename
    if not filename in files: return files[0]
    i = where(files == filename)[0][0]
    i = clip(i+count,0,len(files)-1)
    next_filename = files[i]
    return next_filename

def next_file(filename,count=1,filter="*"):
    """The file next alphabetically in the same directory.
    If the is none return the current filename.
    count: 1 for next next file (default), -1 for the proevious file"""
    from os.path import dirname,exists,isdir
    from glob import glob
    from numpy import argsort,array,where,clip
    dir = dirname(filename)
    files = glob(dir+"/"+filter)
    files = array([f for f in files if not isdir(f)])
    order = argsort(files)
    files = files[order]
    if len(files) == 0: return filename
    if not filename in files: return files[0]
    i = where(files == filename)[0][0]
    i = clip(i+count,0,len(files)-1)
    next_filename = files[i]
    return next_filename

def getmtime(filename):
    # Work-around for a strange problem with "MacDust" files (._*) where
    # "listdir" lists the file, but "getmtime" throws an exception
    # (OSError [errno 2]: No such file or directory)
    from os.path import getmtime
    try: return getmtime(filename)
    except OSError: return 0

def exist_files(filenames):
    """filenames: list of pathnames"""
    from os import listdir
    from os.path import exists,dirname,basename
    directories = {}
    exist_files = []
    for f in filenames:
        if not dirname(f) in directories:
            try: files = listdir(dirname(f) if dirname(f) else ".")
            except OSError: files = []
            directories[dirname(f)] = files
        exist_files += [basename(f) in directories[dirname(f)]]
    return exist_files


def show_image(filename):
    """Signal the viewer to load an image for display.
    filename: pathname"""
    show_images([filename])

def show_images(filenames):
    """Signal the viewer to check a list if image file an display the
    last one that exists.
    filenames: list of pathnames"""
    from DB import dbput
    dbput("ImageViewer.images",repr(filenames).replace("\n",""))


if __name__ == "__main__":
   from os.path import exists
   filenames = ["/mnt/rayonix/data/xpp40312/Anfinrud/MbCO-L29F/MbCO-L29F-28-3"\
        "/alignment/scan_phi=-0.000_z=-0.758/001.mccd"]
   filename = filenames[0]
   ##show_images(filenames)
   app = ImageViewer_App(redirect=False)
   app.MainLoop()
