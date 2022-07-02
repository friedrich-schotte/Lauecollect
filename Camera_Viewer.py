#!/usr/bin/env python
"""Graphical User Interface for a video camera.
Designed for Prosilica GigE cameras.
Author: Friedrich Schotte
Date created: 2008-02-05
Date last modified: 2021-06-16
Revision comment: Added: domain_name
"""
__version__ = "1.6.2"

from logging import debug, warning
from math import sqrt, atan2, sin, cos, pi, log10
from os.path import exists, dirname, basename, splitext

# Turn off IEEE-754 warnings in numpy 1.6+ ("invalid value encountered in...")
import numpy
import wx
import wx.lib.colourselect
from numpy import nan, isnan

from Control_Panel import Control_Panel
from General_Controls import (
    TextCtrl_Control,
    ComboBox_Control,
    CheckBox_Control,
    Slider_Control,
    StaticText_Indicator,
)
from Panel import BasePanel
from Sample_Illumination_Panel import Sample_Illumination_Panel
from cached_function import cached_function
from handler import handler
from reference import reference

numpy.seterr(invalid="ignore", divide="ignore")


class Camera_Viewer(Control_Panel):
    """Control panel to show all configurations"""
    def __init__(self, name):
        super().__init__(name)

    icon = "camera"

    @property
    def title(self): return self.camera.title

    @property
    def camera(self): return camera(self.name)

    @property
    def ControlPanel(self):
        return Camera_Panel(self, self.name)

    @property
    def menuBar(self):
        return Camera_MenuBar(self, self.name)


class Camera_Panel(wx.Panel):
    property_names = [
        "has_zoom",
        "show_illumination_panel",
    ]

    def __init__(self, parent, name):
        """
        name: used for storing and retrieving settings
        """
        wx.Panel.__init__(self, parent=parent)
        self.name = name

        # Controls
        self.Image_Window = Image_Window(self, name=self.name)
        self.AcquiringControl = AcquiringControl(self, self.name, label="Live")
        self.ScaleFactorControl = ScaleFactorControl(self, self.name, size=(88, -1))
        self.ExposureTimeTextControl = ExposureTimeTextControl(self, self.name, size=(50, -1))
        self.ExposureTimeSliderControl = ExposureTimeSliderControl(self, self.name)
        self.AutoExposure = AutoExposureControl(self, self.name, label="Auto")
        self.ZoomLabel = wx.StaticText(self, label="Zoom:")
        self.ZoomLabel.Shown = False
        self.ZoomControl = ZoomControl(self, self.name, size=(55, -1))
        self.ZoomControl.Shown = False
        self.Illumination = Sample_Illumination_Panel(self, "BioCARS")
        self.Illumination.Shown = False
        self.StatusBar = StatusIndicator(self, self.name)
        # Layout
        self.layout = wx.BoxSizer(wx.VERTICAL)
        self.layout.Add(self.Image_Window, proportion=1, flag=wx.EXPAND)
        self.layout.AddSpacer(2)
        self.Controls = wx.BoxSizer(wx.HORIZONTAL)
        self.Controls.AddSpacer(5)
        self.Controls.Add(self.AcquiringControl, flag=wx.ALIGN_CENTER)
        self.Controls.AddSpacer(5)
        self.Controls.Add(self.ScaleFactorControl, flag=wx.ALIGN_CENTER)
        self.Controls.AddSpacer(5)
        self.Controls.Add(self.ExposureTimeTextControl, flag=wx.ALIGN_CENTER)
        self.Controls.AddSpacer(5)
        # Make exposure slider growable (proportion=1)
        self.Controls.Add(self.ExposureTimeSliderControl, proportion=1, flag=wx.ALIGN_CENTER)
        self.Controls.AddSpacer(5)
        self.Controls.Add(self.AutoExposure, flag=wx.ALIGN_CENTER)
        self.Controls.AddSpacer(5)
        self.Controls.Add(self.ZoomLabel, flag=wx.ALIGN_CENTER)
        self.Controls.AddSpacer(5)
        self.Controls.Add(self.ZoomControl, flag=wx.ALIGN_CENTER)
        self.layout.AddSpacer(2)
        self.layout.Add(self.Controls, flag=wx.EXPAND)
        self.layout.AddSpacer(2)
        self.layout.Add(self.Illumination, flag=wx.EXPAND)
        self.layout.AddSpacer(2)
        self.layout.Add(self.StatusBar, flag=wx.EXPAND)
        self.Sizer = self.layout
        self.Fit()  # needed?

        self.monitoring = True
        self.update()
        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroy)

    def OnDestroy(self, event):
        event.Skip()
        debug(f"{type(self).__name__} {self.name!r}: Window destroyed")
        self.monitoring = False

    @property
    def monitoring(self):
        return all([
            handler(self.handle_change, property_name)
            in reference(self.camera, property_name).monitors
            for property_name in self.property_names
        ])

    @monitoring.setter
    def monitoring(self, value):
        if value:
            for property_name in self.property_names:
                reference(self.camera, property_name).monitors.add(
                    handler(self.handle_change, property_name))
        else:
            for property_name in self.property_names:
                reference(self.camera, property_name).monitors.remove(
                    handler(self.handle_change, property_name))

    @property
    def camera(self):
        return camera(self.name)

    from run_async import run_async

    @run_async
    def update(self):
        for property_name in self.property_names:
            value = getattr(self.camera, property_name)
            wx.CallAfter(self.set_value, property_name, value)

    def handle_change(self, property_name):
        value = getattr(self.camera, property_name)
        debug(("%s = %.60r" % (property_name, value)).replace("\n", ""))
        wx.CallAfter(self.set_value, property_name, value)

    def set_value(self, property_name, value):
        if property_name == "has_zoom":
            self.ZoomControlShown = value
        if property_name == "show_illumination_panel":
            debug(f"Illumination.Shown = {value}")
            self.Illumination.Shown = value
            self.Layout()

    def GetZoomControlShown(self):
        """Are the zoom controls active?"""
        return self.ZoomControl.Shown

    def SetZoomControlShown(self, value):
        """value: True or False"""
        value = bool(value)
        if self.ZoomLabel.Shown != value or self.ZoomControl.Shown != value:
            self.ZoomLabel.Shown = value
            self.ZoomControl.Shown = value
            self.Controls.Layout()

    ZoomControlShown = property(GetZoomControlShown, SetZoomControlShown)

    def GetPointerFunction(self):
        """What does pressing the left mouse button on the image mean?"""
        return self.Image_Window.PointerFunction

    def SetPointerFunction(self, name):
        self.Image_Window.PointerFunction = name

    PointerFunction = property(GetPointerFunction, SetPointerFunction)

    def AddPointerFunction(self, name):
        """Add an item to the context menu"""
        self.Image_Window.AddPointerFunction(name)

    def AddObject(self, name, points=(), color=(0, 0, 255), object_type="squares"):
        """Add a custom shape to be drawn on top of the image.
        name: Displayed in show/hide context menu
        points: list if x,y pairs in mm coordinates relative to
        the crosshairs
        color: default color. Can be overridden from properties dialog."""
        self.Image_Window.AddObject(name, points, color, object_type)

    def DeleteObject(self, name):
        """Remove a custom shape to be drawn on top of the image.
        name: Displayed in show/hide context menu"""
        self.Image_Window.DeleteObject(name)

    def OnPointerFunction(self, name, x, y, event):
        """Called when the left mouse button is pressed and a custom pointer
        function is activated.
        (x,y) position of pointer relative to crosshairs
        event: 'down','drag' or 'up'"""
        # print("%s (%g,%g) mm" % (name,x,y))

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.name)


class AcquiringControl(CheckBox_Control):
    def __init__(self, parent, name, label="Live"):
        super().__init__(
            parent=parent,
            name=f"instrumentation.{camera(name).domain_name}.camera_controls.{camera(name).base_name}.acquiring",
            label=label,
        )


class ScaleFactorControl(ComboBox_Control):
    def __init__(self, parent, name, **kwargs):
        super().__init__(
            parent=parent,
            name=f"instrumentation.{camera(name).domain_name}.camera_controls.{camera(name).base_name}.scale_factor",
            choices_name=f"instrumentation.{camera(name).domain_name}.camera_controls.{camera(name).base_name}.scale_factors",
            **kwargs
        )

    def to_text(self, value):
        from numpy import isnan
        if isnan(value):
            text = "Fit Width"
        else:
            text = "%g%%" % (value * 100.)
        return text

    def from_text(self, text):
        from numpy import nan
        try:
            value = float(text.strip("%")) / 100
        except (ValueError, TypeError):
            value = nan
        return value


class ExposureTimeTextControl(TextCtrl_Control):
    def __init__(self, parent, name, **kwargs):
        super().__init__(
            parent=parent,
            name=f"instrumentation.{camera(name).domain_name}.camera_controls.{camera(name).base_name}.exposure_time",
            **kwargs,
        )

    def to_text(self, value):
        from numpy import isnan
        if isnan(value):
            text = ""
        else:
            text = "%.2g s" % value
        return text

    def from_text(self, text):
        from numpy import nan
        try:
            value = float(text.strip("s"))
        except (ValueError, TypeError):
            value = nan
        return value


class ExposureTimeSliderControl(Slider_Control):
    def __init__(self, parent, name, **kwargs):
        super().__init__(
            parent=parent,
            name=f"instrumentation.{camera(name).domain_name}.camera_controls.{camera(name).base_name}.exposure_time",
            **kwargs,
        )

    def to_count(self, value):
        fraction = value ** 0.5
        count = super().to_count(fraction)
        debug("%r s -> %r counts" % (value, count))
        return count

    def from_count(self, count):
        fraction = super().from_count(count)
        value = fraction ** 2
        debug("%r counts -> %r s" % (count, value))
        return value


class AutoExposureControl(CheckBox_Control):
    def __init__(self, parent, name, label="Auto"):
        super().__init__(
            parent=parent,
            name=f"instrumentation.{camera(name).domain_name}.camera_controls.{camera(name).base_name}.auto_exposure",
            label=label,
        )


class StatusIndicator(StaticText_Indicator):
    def __init__(self, parent, name):
        super().__init__(
            parent=parent,
            name=f"instrumentation.{camera(name).domain_name}.camera_controls.{camera(name).base_name}.state",
        )


class ZoomControl(ComboBox_Control):
    def __init__(self, parent, name, **kwargs):
        super().__init__(
            parent=parent,
            name=f"instrumentation.{camera(name).domain_name}.camera_controls.{camera(name).base_name}.zoom_level",
            choices_name=f"instrumentation.{camera(name).domain_name}.camera_controls.{camera(name).base_name}.zoom_levels",
            **kwargs
        )

    def to_text(self, value):
        text = str(value)
        return text

    def from_text(self, text):
        try:
            value = float(text)
        except (ValueError, TypeError):
            value = 1.0
        return value


class Camera_MenuBar(wx.MenuBar):
    property_names = [
        "normalized_orientation",
        "mirror",
        "show_illumination_panel",
    ]

    ID_orientation = {
        0: 301,  # As camera
        270: 302,  # Rotated Clockwise
        90: 303,  # Rotated Counter-clockwise
        180: 304,  # Upside down
    }
    ID_Mirror = 305
    ID_Illumination = 500

    def __init__(self, viewer, name):
        wx.MenuBar.__init__(self)
        self.viewer = viewer
        self.name = name

        menu = wx.Menu()
        menu.Append(101, "&Open Image...\tCtrl+O", "Loads a saved JPEG file.")
        self.Bind(wx.EVT_MENU, self.OnOpen, id=101)
        menu.AppendSeparator()
        menu.Append(111, "&Save Image As...\tCtrl+S", "Creates a full-resolution JPEG file.")
        self.Bind(wx.EVT_MENU, self.OnSave, id=111)
        menu.Append(112, "&Save Beam Profile As...", "Creates text file with numerical data.")
        self.Bind(wx.EVT_MENU, self.OnSaveProfile, id=112)
        self.Append(menu, "&File")
        menu = wx.Menu()
        menu.Append(201, "&Copy Image\tCtrl+C",
                    "Places copy of full image in the clipboard")
        self.Bind(wx.EVT_MENU, self.CopyImage, id=201)
        self.Append(menu, "&Edit")
        self.OrientationMenu = wx.Menu()
        style = wx.ITEM_CHECK
        self.OrientationMenu.Append(self.ID_orientation[0], "As Camera", "Do not rotate image", style)
        self.OrientationMenu.Append(self.ID_orientation[270], "Rotated Clockwise", "Rotate image by -90 deg", style)
        self.OrientationMenu.Append(self.ID_orientation[90], "Rotated Counter-clockwise", "Rotate image by +90 deg", style)
        self.OrientationMenu.Append(self.ID_orientation[180], "Upside down", "Rotate image by 180 deg", style)
        self.OrientationMenu.AppendSeparator()
        self.OrientationMenu.Append(self.ID_Mirror, "Mirror", "Flip image horizontal", style)
        self.Append(self.OrientationMenu, "&Orientation")

        for ID in self.ID_orientation.values():
            self.Bind(wx.EVT_MENU, self.OnOrientation, id=ID)

        self.Bind(wx.EVT_MENU, self.OnMirror, id=self.ID_Mirror)

        self.OptionsMenu = wx.Menu()
        self.OptionsMenu.Append(399, "&Viewer...", "Configures the viewer")
        self.Bind(wx.EVT_MENU, self.OnViewerOptions, id=399)
        self.OptionsMenu.Append(401, "&Camera...", "Configures the camera acquisition")
        self.Bind(wx.EVT_MENU, self.OnCameraOptions, id=401)
        self.OptionsMenu.Append(400, "&Optics...", "Configures the camera optics")
        self.Bind(wx.EVT_MENU, self.OnOpticsOptions, id=400)
        self.OptionsMenu.AppendSeparator()
        style = wx.ITEM_CHECK
        self.OptionsMenu.Append(self.ID_Illumination, "Illumination", "Show Illumination Panel", style)
        self.Bind(wx.EVT_MENU, self.OnIllumination, id=self.ID_Illumination)
        self.Append(self.OptionsMenu, "Options")

        menu = wx.Menu()
        menu.Append(501, "&About...", "Version information")
        self.Bind(wx.EVT_MENU, self.OnAbout, id=501)
        self.Append(menu, "&Help")

        self.monitoring = True
        self.update()
        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroy)

    def OnDestroy(self, event):
        event.Skip()
        debug(f"{self}: Window destroyed")
        self.monitoring = False

    @property
    def monitoring(self):
        return all([
            handler(self.handle_change, property_name)
            in reference(self.camera, property_name).monitors
            for property_name in self.property_names
        ])

    @monitoring.setter
    def monitoring(self, value):
        if value:
            for property_name in self.property_names:
                reference(self.camera, property_name).monitors.add(
                    handler(self.handle_change, property_name))
        else:
            for property_name in self.property_names:
                reference(self.camera, property_name).monitors.remove(
                    handler(self.handle_change, property_name))

    @property
    def camera(self):
        return camera(self.name)

    from run_async import run_async

    @run_async
    def update(self):
        for property_name in self.property_names:
            value = getattr(self.camera, property_name)
            wx.CallAfter(self.set_value, property_name, value)

    def handle_change(self, property_name):
        value = getattr(self.camera, property_name)
        debug(("%s = %.60r" % (property_name, value)).replace("\n", ""))
        wx.CallAfter(self.set_value, property_name, value)

    def set_value(self, property_name, value):
        if property_name == "normalized_orientation":
            self.Orientation = value
        if property_name == "mirror":
            self.Mirror = value
        if property_name == "show_illumination_panel":
            self.OptionsMenu.Check(self.ID_Illumination, value)

    def OnOpen(self, _event):
        """Called from menu File/Open Image..."""
        dlg = wx.FileDialog(self, "Open Image", style=wx.FD_OPEN,
                            defaultDir=dirname(self.camera.filename), defaultFile=basename(self.camera.filename),
                            wildcard="JPEG Images (*.jpg)|*.jpg|TIFF Images (*.tif)|*.tif|" +
                                     "PNG Images (*.png)|*.png|All Files (*.*)|*.*")
        if dlg.ShowModal() == wx.ID_OK:
            self.camera.filename = dlg.GetPath()
            wx_image = wx.Image(self.camera.filename)
            # Get the image pixel size.
            # (wx.Image.GetOptionInt(wx.IMAGE_OPTION_RESOLUTION) always returns 0
            # thus, using PIL.)
            from PIL import Image
            PIL_image = Image.open(self.camera.filename)
            if "dpi" in PIL_image.info:
                self.camera.pixelsize = 25.4 / PIL_image.info["dpi"][0]
            # Convert image from WX to numpy format.
            data = wx_image.GetData()
            w, h = wx_image.Width, wx_image.Height
            from numpy import frombuffer, uint8
            image = frombuffer(data, uint8).reshape(h, w, 3).T
            self.camera.image = image
        dlg.Destroy()

    def OnSave(self, _event):
        """Called from menu File/Save Image As..."""
        filename = splitext(self.camera.filename)[0] + ".jpg"
        dlg = wx.FileDialog(
            parent=self,
            message="Save Image As",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
            defaultFile=basename(filename),
            defaultDir=dirname(filename),
            wildcard="JPEG Images (*.jpg)|*.jpg|"
                     "TIFF Images (*.tif)|*.tif|"
                     "PNG Images (*.png)|*.png|"
                     "All Files (*.*)|*.*"
        )
        if dlg.ShowModal() == wx.ID_OK:
            filename = str(dlg.GetPath())
            index = dlg.GetFilterIndex()
            extensions = [".jpg", ".tif", ".png", ""]
            def_extension = extensions[index]
            extension = splitext(filename)[1]
            if extension == "" and def_extension != "":
                filename += "." + def_extension
            self.camera.save_image(filename)
        dlg.Destroy()

    def OnSaveProfile(self, _event):
        """Called from menu File/Save Beam Profile As..."""
        filename = splitext(self.camera.filename)[0] + ".txt"
        dlg = wx.FileDialog(self, "Save Profile As",
                            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
                            defaultFile=basename(filename), defaultDir=dirname(filename),
                            wildcard="Text Files (*.txt)|*.txt|All Files (*.*)|*.*")
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            x = xvals(self.viewer.ControlPanel.ImageWindow.xprofile)
            Ix = yvals(self.viewer.ControlPanel.ImageWindow.xprofile)
            y = xvals(self.viewer.ControlPanel.ImageWindow.yprofile)
            Iy = yvals(self.viewer.ControlPanel.ImageWindow.yprofile)
            header = "Beam size: %.3f x %.3f mm FWHM" % self.camera.FWHM
            header += ", Linearity correction: " + \
                      str(self.camera.linearity_correction)
            labels = "x[mm],Ix,y[mm],Iy"
            save([x, Ix, y, Iy], filename, header, labels)
            self.camera.filename = filename
        dlg.Destroy()

    def CopyImage(self, _event):
        """Called from menu Edit/Copy Image"""
        image = self.camera.image
        # Convert image from numpy to WX data format.
        d, w, h = image.shape
        wx_image = wx.Image(w, h)
        data = image.T.tobytes()
        wx_image.Data = data
        # Put image data as "Bitmap" data object into the clipboard.
        bitmap = wx.Image(wx_image)
        bitmap_data_object = wx.BitmapDataObject(bitmap)
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(bitmap_data_object)
            wx.TheClipboard.Close()
        else:
            wx.MessageBox("Unexpected clipboard problem", "Error")

    def GetOrientation(self):
        orientation = 0
        for orientation_choice in self.ID_orientation:
            ID = self.ID_orientation[orientation_choice]
            if self.OrientationMenu.IsChecked(ID):
                orientation = orientation_choice
                break
        debug("Orientation = %r" % orientation)
        return orientation

    def SetOrientation(self, orientation):
        orientation = float(orientation)
        for orientation_choice in self.ID_orientation:
            ID = self.ID_orientation[orientation_choice]
            checked = orientation_choice == orientation
            self.OrientationMenu.Check(ID, checked)

    Orientation = property(GetOrientation, SetOrientation)

    def GetMirror(self):
        return self.OrientationMenu.IsChecked(self.ID_Mirror)

    def SetMirror(self, mirror):
        self.OrientationMenu.Check(self.ID_Mirror, mirror)

    Mirror = property(GetMirror, SetMirror)

    def OnOrientation(self, event):
        debug("Orientation menu item ID=%r selected" % event.Id)
        orientation = 0
        for orientation_choice in self.ID_orientation:
            ID = self.ID_orientation[orientation_choice]
            if ID == event.Id:
                orientation = orientation_choice
                break
        debug("normalized_orientation = %r" % orientation)
        self.camera.normalized_orientation = orientation

    def OnMirror(self, _event):
        debug("Mirror menu item selected")
        self.camera.mirror = self.Mirror

    def OnViewerOptions(self, _event):
        """Configure scale and zoom"""
        dlg = ViewerOptions(self.Window, self.name)
        dlg.CenterOnParent()
        dlg.Show()

    def OnCameraOptions(self, _event):
        """Configure acquisition"""
        dlg = CameraOptions(self.Window, self.name)
        dlg.CenterOnParent()
        dlg.Show()

    def OnOpticsOptions(self, _event):
        """Configure scale and zoom"""
        dlg = OpticsOptions(self.Window, self.name)
        dlg.CenterOnParent()
        dlg.Show()

    def OnIllumination(self, event):
        value = event.IsChecked()
        debug(f"show_illumination_panel = {value}")
        self.camera.show_illumination_panel = value

    def OnAbout(self, _event):
        """Show version info"""
        from About import About
        About(self.Window)

    @property
    def Window(self):
        return self.Parent

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.name)


def highlight(image, mask, color):
    """Substitutes the value of masked pixels with the specified color.
    image type: wx.Image, mask type: wx.Image, color type: (R,G,B)"""
    new_image = image.copy()
    R, G, B = new_image
    R[mask], G[mask], B[mask] = color[0:3]
    return new_image


class Image_Window(wx.ScrolledWindow):
    property_names = [
        "image",
        "scale_factor",
        "pixelsize",
        "image_center",
        "show_crosshairs",
        "crosshairs_size",
        "crosshairs_color",
        "show_scale",
        "scale",
        "scale_color",
        "show_box",
        "box_size",
        "box_color",
        "show_profile",
        "calculate_section",
        "profile_color",
        "show_FWHM",
        "FWHM_color",
        "show_center",
        "center_color",
        "show_grid",
        "grid_type",
        "grid_x_spacing",
        "grid_x_offset",
        "grid_y_spacing",
        "grid_y_offset",
        "grid_color",
        "ROI",
        "ROI_color",
        "show_saturated_pixels",
        "saturation_threshold",
        "saturated_color",
        "mask_bad_pixels",
        "linearity_correction",
        "bad_pixel_threshold",
        "bad_pixel_color",
    ]

    def __init__(self, parent, name):
        wx.ScrolledWindow.__init__(self, parent)
        self.name = name

        self.dragging = ""
        self.scale_selected = False
        self.drag_info = None
        self.section_width = 0.3  # fraction of FWHM
        self.click_centering_available = False
        self.use_channels = (1, 1, 1)  # use all channels R,G,B
        self.pointer_functions = []  # use define actions of the mouse
        self.tool = ""  # Role of mouse pointer: measure, move crosshairs
        self.objects = {}  # custom shapes to be drawn on top of the image
        self.object_colors = {}  # color for each member of objects
        self.object_type = {}  # "square" or "line"
        self.show_object = {}  # whether each object is shown or not
        self.wx_image = None
        self.bitmap = None
        self.transformed_mask = None

        self.set_virtual_size()
        self.SetScrollRate(1, 1)

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_SIZE, self.OnResize)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)

        self.monitoring = True
        self.update()
        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroy)

    def OnDestroy(self, event):
        event.Skip()
        debug(f"{type(self).__name__} {self.name!r}: Window destroyed")
        self.monitoring = False

    @property
    def monitoring(self):
        return all([
            handler(self.handle_change, property_name)
            in reference(self.camera, property_name).monitors
            for property_name in self.property_names
        ])

    @monitoring.setter
    def monitoring(self, value):
        if value:
            for property_name in self.property_names:
                reference(self.camera, property_name).monitors.add(
                    handler(self.handle_change, property_name))
        else:
            for property_name in self.property_names:
                reference(self.camera, property_name).monitors.remove(
                    handler(self.handle_change, property_name))

    @property
    def camera(self):
        return camera(self.name)

    from run_async import run_async

    @run_async
    def update(self):
        for property_name in self.property_names:
            value = getattr(self.camera, property_name)
            wx.CallAfter(self.set_value, property_name, value)

        if self.profile_needed:
            self.calculate_profile()
        wx.CallAfter(self.refresh)

    def handle_change(self, property_name):
        value = getattr(self.camera, property_name)
        debug(("%s = %.60r" % (property_name, value)).replace("\n", ""))
        self.set_value(property_name, value)

        if property_name in ["image", "ROI", "calculate_section", "linearity_correction"]:
            if self.profile_needed:
                self.calculate_profile()
        if property_name == "scale_factor":
            self.scale_image()

        wx.CallAfter(self.refresh)

    def set_value(self, property_name, value):
        if property_name == "image":
            self.set_image(value)

    def refresh(self):
        if not self.dragging:
            self.set_virtual_size()
        self.Refresh()

    @property
    def scale_unit(self):
        if self.camera.pixelsize == 1.0:
            return "pixels"
        else:
            return "mm"

    def GetBadPixelCount(self):
        """How many bad pixels are there?"""
        from numpy import sum
        return sum(self.camera.mask != 0)

    BadPixelCount = property(GetBadPixelCount)

    @property
    def scale_factor(self):
        from numpy import isnan
        scale = self.camera.scale_factor
        if isnan(scale):
            scale = self.auto_scale_factor
        return scale

    @property
    def auto_scale_factor(self):
        if self.camera.image_width != 0:
            scale = float(self.ClientSize.x) / self.camera.image_width
        else:
            scale = 1.0
        return scale

    def handle_scale_factor_change(self):
        center = self.ViewportCenter
        self.set_virtual_size()
        self.ViewportCenter = center
        self.refresh()

    def set_virtual_size(self):
        from numpy import rint
        w = self.camera.image_width * self.scale_factor
        h = self.camera.image_height * self.scale_factor
        w, h = int(rint(w)), int(rint(h))
        self.SetVirtualSize((w, h))

    def GetViewportCenter(self):
        """Center(x,y) coordinates of the part of the image displayed in the
        window in mm with respect to the top left corner of the image."""
        w, h = self.GetClientSize()
        x0, y0 = self.GetViewStart()
        sx, sy = self.GetScrollPixelsPerUnit()
        ox, oy = self.Origin
        s = self.scale_factor
        dx = self.camera.pixelsize
        cx, cy = (x0 * sx - ox + w / 2) / s * dx, (y0 * sy - oy + h / 2) / s * dx
        return cx, cy

    def SetViewportCenter(self, center):
        """Scroll such than the center the window is x mm from the
        left edge and y mm from the top edge of the image."""
        cx, cy = center
        w, h = self.GetClientSize()
        sx, sy = self.GetScrollPixelsPerUnit()
        ox, oy = self.Origin
        s = self.scale_factor
        dx = self.camera.pixelsize

        x0 = cx / sx / dx * s - w / 2 + ox
        y0 = cy / sx / dx * s - h / 2 + oy
        self.Scroll(x0, y0)
        self.camera.viewport_center = center

    ViewportCenter = property(GetViewportCenter, SetViewportCenter)

    def GetImageSize(self):
        """Width and height of image in mm"""
        w, h = (self.camera.image_width, self.camera.image_height)
        return w * self.camera.pixelsize, h * self.camera.pixelsize

    ImageSize = property(GetImageSize)

    def GetImageOrigin(self):
        """Image center defined by crosshairs in mm for bottom left corner"""
        x, y = self.camera.image_center
        h = self.camera.image_height
        return -x * self.camera.pixelsize, -(h - y) * self.camera.pixelsize

    ImageOrigin = property(GetImageOrigin)

    def GetPointerFunction(self):
        return self.tool

    def SetPointerFunction(self, name):
        if name:
            self.AddPointerFunction(name)
        self.tool = name

    PointerFunction = property(GetPointerFunction, SetPointerFunction)

    def AddPointerFunction(self, name):
        """Shows up as choice in the context menu"""
        if name not in self.pointer_functions:
            self.pointer_functions += [name]

    def AddObject(self, name, points=(), color=(0, 0, 255), object_type="squares"):
        """Add a custom shape to be drawn on top of the image.
        name: Displayed in show/hide context menu
        points: list if x,y pairs in mm coordinates relative to
        the crosshairs
        color: default color. Can be overridden from properties dialog.
        type: "squares" or "lines" """
        # Check if update is needed.
        if name in self.objects and self.objects[name] == points:
            return

        self.objects[name] = points
        if name not in self.object_colors:
            self.object_colors[name] = color
        if name not in self.object_type:
            self.object_type[name] = object_type
        if name not in self.show_object:
            self.show_object[name] = True
        self.refresh()

    def DeleteObject(self, name):
        """Remove a custom shape to be drawn on top of the image.
        name: Displayed in show/hide context menu"""
        if name not in self.objects:
            return  # Check if update is needed.
        del self.objects[name]
        self.refresh()

    @property
    def Origin(self):
        """By default, a Scrolled Window places its active area in the top
        left, if it is smaller than the window size.
        Instead, I want it centered in the window.
        The function calculates the active area origin as function of window
        size."""
        from numpy import rint
        width, height = self.ClientSize
        x = (width - self.camera.image_width * self.scale_factor) / 2
        y = (height - self.camera.image_height * self.scale_factor) / 2
        if x < 0:
            x = 0
        if y < 0:
            y = 0
        x, y = int(rint(x)), int(rint(y))
        return x, y

    def OnPaint(self, _event):
        """Called by WX whenever the contents of the window
        needs re-rendering. E.g. when the window is brought to front,
        uncovered, restored from minimized state."""

        dc = wx.PaintDC(self)
        dc = wx.BufferedDC(dc)  # avoids flickering
        self.PrepareDC(dc)

        # Need to fill the area no covered by the image
        # because automatic background erase was turned off.
        dc.SetBrush(wx.Brush("GREY"))
        dc.SetPen(wx.Pen("GREY", 0))
        width, height = self.ClientSize
        dc.DrawRectangle(0, 0, width, height)

        # This centers the image in the window, if the window is larger than
        # the image.
        # debug("OnPaint: dc.DeviceOrigin: %r,%r" % dc.DeviceOrigin)
        xdo, ydo = dc.DeviceOrigin
        xo, yo = self.Origin
        if xdo == 0:
            xdo = xo
        if ydo == 0:
            ydo = yo
        dc.SetDeviceOrigin(xdo, ydo)
        # debug("OnPaint: dc.DeviceOrigin: %r,%r" % dc.DeviceOrigin)

        self.draw(dc)

    def OnEraseBackground(self, event):
        """Overrides default background fill, avoiding flickering"""

    def set_image(self, image):
        if self.camera.show_saturated_pixels:
            image = self.highlight_saturated(image)
        if self.camera.mask_bad_pixels:
            image = highlight(image, self.transformed_mask, self.camera.bad_pixel_color)

        # Convert image from numpy to WX data format.
        self.wx_image = wx.Image(self.camera.image_width, self.camera.image_height)
        data = image.T.tobytes()
        self.wx_image.SetData(data)
        self.scale_image()

    def scale_image(self):
        from numpy import rint
        if self.wx_image is not None:
            # Scale the image.
            w = self.camera.image_width * self.scale_factor
            h = self.camera.image_height * self.scale_factor
            # Use "quality=wx.IMAGE_QUALITY_HIGH" for bicubic and box averaging
            # resampling methods for up-sampling and down-sampling respectively.
            w, h = int(rint(w)), int(rint(h))
            scaled_image = self.wx_image.Scale(w, h)
            self.bitmap = wx.Bitmap(scaled_image)

    def draw(self, dc):
        """Re-draw the contents of the window."""
        # debug("Redrawing started")
        if self.bitmap is not None:
            dc.DrawBitmap(self.bitmap, 0, 0)
        self.draw_objects(dc)
        self.draw_grid(dc)
        self.draw_crosshairs(dc)
        self.draw_box(dc)
        self.draw_scale(dc)
        self.draw_profile(dc)
        # debug("Redrawing finished")

    def draw_grid(self, dc):
        """Indicates the X-ray beam position as a cross"""
        if not self.camera.show_grid:
            return
        dc.SetPen(wx.Pen(self.camera.grid_color, 1))
        w, h = self.camera.image_width * self.scale_factor, self.camera.image_height * self.scale_factor

        dx = self.camera.grid_x_spacing
        x0 = self.camera.grid_x_offset
        if "x" in self.camera.grid_type and dx != 0 and not isnan(dx):
            i = 0
            x = self.pixel((x0 + i * dx, 0))[0]
            while 0 <= x < w:
                dc.DrawLine(x, 0, x, h)
                i += 1
                x = self.pixel((x0 + i * dx, 0))[0]
            i = -1
            x = self.pixel((x0 + i * dx, 0))[0]
            while 0 <= x < w:
                dc.DrawLine(x, 0, x, h)
                i -= 1
                x = self.pixel((x0 + i * dx, 0))[0]

        dy = self.camera.grid_y_spacing
        y0 = self.camera.grid_y_offset
        if "y" in self.camera.grid_type and dy != 0 and not isnan(dy):
            i = 0
            y = self.pixel((0, y0 + i * dy))[1]
            while 0 <= y < h:
                dc.DrawLine(0, y, w, y)
                i += 1
                y = self.pixel((0, y0 + i * dy))[1]
            i = -1
            y = self.pixel((0, y0 + i * dy))[1]
            while 0 <= y < h:
                dc.DrawLine(0, y, w, y)
                i -= 1
                y = self.pixel((0, y0 + i * dy))[1]

    def draw_crosshairs(self, dc):
        """Indicates the X-ray beam position as a cross"""
        if self.camera.show_crosshairs:
            dc.SetPen(wx.Pen(self.camera.crosshairs_color, 1))
            w, h = self.camera.crosshairs_size
            x1, y1 = self.pixel((-w / 2, 0))
            x2, y2 = self.pixel((+w / 2, 0))
            dc.DrawLine(x1, y1, x2, y2)
            x1, y1 = self.pixel((0, -h / 2))
            x2, y2 = self.pixel((0, +h / 2))
            dc.DrawLine(x1, y1, x2, y2)

    def draw_box(self, dc):
        """Draws a box around the cross hair to indicate X-ray beam size."""
        if self.camera.show_box:
            w, h = self.camera.box_size
            x1, y1 = self.pixel((w / 2, h / 2))
            x2, y2 = self.pixel((-w / 2, -h / 2))
            dc.SetPen(wx.Pen(self.camera.box_color, 1))
            dc.DrawLines([(x1, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1)])

    def draw_scale(self, dc):
        """Draw a line labelled with its length in um or mm"""
        if self.camera.show_scale:
            P1, P2 = self.camera.scale
            x1, y1 = self.pixel(P1)
            x2, y2 = self.pixel(P2)
            dc.SetPen(wx.Pen(self.camera.scale_color, 1))
            dc.DrawLine(x1, y1, x2, y2)

            length = distance(P1, P2)
            if self.scale_unit == "mm":
                if length < 1:
                    label = "%.0f um" % (length * 1000)
                else:
                    label = "%.3f mm" % length
            else:
                label = "%g %s" % (length, self.scale_unit)
            font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
            font.SetPointSize(10)
            dc.SetFont(font)
            dc.SetTextForeground(self.camera.scale_color)
            w, h = dc.GetTextExtent(label)
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            phi = atan2(y2 - y1, x2 - x1)
            tx = cx - (w / 2 * cos(phi) - h * sin(phi))
            ty = cy - (h * cos(phi) + w / 2 * sin(phi))
            dc.DrawRotatedText(label, tx, ty, -phi / pi * 180)

            if self.scale_selected:  # Highlight the end points by 5x5 pixel squares
                dc.DrawRectangle(x1 - 2, y1 - 2, 4, 4)
                dc.DrawRectangle(x2 - 2, y2 - 2, 4, 4)

    def draw_objects(self, dc):
        """Draw custom shapes on top of the image"""
        # Draw it as a cloud of points, without connecting them.
        for name in self.objects:
            if not self.show_object[name]:
                continue
            color = self.object_colors[name]
            object_type = self.object_type[name]
            dc.SetPen(wx.Pen(color, 1))
            dc.SetBrush(wx.Brush(color))
            points = self.objects[name]
            if object_type == "squares":
                for point in points:
                    x, y = self.pixel(point)
                    dc.DrawRectangle(int32(x - 1), int32(y - 1), 3, 3)
            if object_type == "line":
                segments = [self.pixel(p) for p in points]
                if len(segments) > 1:
                    dc.DrawLines(segments)

    @property
    def profile_needed(self):
        return any([
            self.camera.show_profile,
            self.camera.show_FWHM,
            self.camera.show_center,
        ])

    def calculate_profile(self):
        """Update the beam profile"""
        # from traceback import format_stack
        # debug("Calculating profile\n"+"".join(format_stack(limit=5)))
        # debug("Calculating profile started")

        from numpy import nan, isnan, minimum, log, sum, nansum

        RGB = self.camera.image

        # Get the region of interest
        ROI = self.camera.ROI
        cx, cy = self.camera.image_center
        dx = dy = self.camera.pixelsize
        xmin = int(round(ROI[0][0] / dx + cx))
        xmax = int(round(ROI[1][0] / dx + cx))
        ymin = int(round(cy - ROI[1][1] / dy))
        ymax = int(round(cy - ROI[0][1] / dy))
        if xmin > xmax:
            xmin, xmax = xmax, xmin
        if ymin > ymax:
            ymin, ymax = ymax, ymin
        # print("ROI [%d:%d,%d:%d]" % (xmin,xmax,ymin,ymax))
        RGB = RGB[:, xmin:xmax, ymin:ymax]

        # Mask bad pixels by setting them to NaN.
        RGB = RGB.astype(float)
        if self.camera.mask_bad_pixels:
            mask = self.transformed_mask[xmin:xmax, ymin:ymax]
            R, G, B = RGB
            R[mask], G[mask], B[mask] = nan, nan, nan

        # Apply linearity correction individually to R,G,and B channels,
        # then add up the intensities of the channels.
        if self.camera.linearity_correction:
            # Build linearity correction table
            T = float(self.camera.saturation_threshold)  # 0 to 255

            def linearize(i): return -log(1 - minimum(i, T) / (T + 1)) * (T + 1)

            RGB = linearize(RGB)

        # Select which channels to use.
        r, g, b = self.use_channels
        R, G, B = RGB
        image = r * R + b * B + g * G

        # Generate projection on the X and Y axis.
        x_proj = nansum(image, axis=1) / sum(~isnan(image), axis=1)
        y_proj = nansum(image, axis=0) / sum(~isnan(image), axis=0)
        # Scale projections in units of mm.
        x_scale = [(xmin + i - cx) * dx for i in range(0, len(x_proj))]
        y_scale = [(cy - (ymin + i)) * dy for i in range(0, len(y_proj))]
        self.x_profile = list(zip(x_scale, x_proj))
        self.y_profile = list(zip(y_scale, y_proj))

        if self.camera.calculate_section:
            # Calculate X and Y sections through the peak.
            # This is done by integrating of a strip that is a certain fraction
            # of the FWHM wide, determined by the parameter "section_width".
            x_profile = list(zip(list(range(0, len(x_proj))), x_proj))
            y_profile = list(zip(list(range(0, len(y_proj))), y_proj))
            W, H = FWHM(x_profile), FWHM(y_profile)
            CX, CY = CFWHM(x_profile), CFWHM(y_profile)
            fraction = self.section_width / 2
            x1, x2 = int(round(CX - W * fraction)), int(round(CX + W * fraction))
            y1, y2 = int(round(CY - H * fraction)), int(round(CY + H * fraction))
            x_strip = image[:, y1:y2 + 1]
            y_strip = image[x1:x2 + 1, :]
            x_sect = nansum(x_strip, axis=1) / sum(~isnan(x_strip), axis=1)
            y_sect = nansum(y_strip, axis=0) / sum(~isnan(y_strip), axis=0)
            self.x_profile = list(zip(x_scale, x_sect))
            self.y_profile = list(zip(y_scale, y_sect))
            (xr1, yr1), (xr2, yr2) = self.camera.ROI
            left, bottom = min(xr1, xr2), min(yr1, yr2)
            self.section = left + x1 * dx, left + x2 * dx, bottom + y1 * dy, bottom + y2 * dy

        self.FWHM = (FWHM(self.x_profile), FWHM(self.y_profile))
        self.CFWHM = (CFWHM(self.x_profile), CFWHM(self.y_profile))
        # debug("Calculating profile done")

    x_profile = []
    y_profile = []
    section = nan, nan, nan, nan
    FWHM = nan, nan
    CFWHM = nan, nan

    def draw_profile(self, dc):
        """Beam profile analyzer.
        Draws a FWHM with dimensions box around the beam center,
        horizontal and vertical beam projections or sections on the left and
        bottom edge of the image"""

        if (self.camera.show_profile or self.camera.show_FWHM) and self.camera.calculate_section and hasattr(self, "section"):
            # Mark the width of the strip that was used to calculate a section
            dc.SetPen(wx.Pen(self.camera.profile_color, 1, wx.PENSTYLE_DOT))
            x1, x2, y1, y2 = self.section
            left, bottom = self.camera.ROI[0]
            right, top = self.camera.ROI[1]
            dc.DrawLines([self.pixel((x1, bottom)), self.pixel((x1, top))])
            dc.DrawLines([self.pixel((x2, bottom)), self.pixel((x2, top))])
            dc.DrawLines([self.pixel((left, y1)), self.pixel((right, y1))])
            dc.DrawLines([self.pixel((left, y2)), self.pixel((right, y2))])

        if self.camera.show_profile and self.x_profile and self.y_profile:
            from numpy import array
            # Draw beam profiles at the edge of the image.
            dc.SetPen(wx.Pen(self.camera.profile_color, 1))

            def valid(val):
                return val != 0

            # Draw horizontal profile at the bottom edge of the ROI box.
            try:
                scale = 0.35 * (self.camera.ROI[1][1] - self.camera.ROI[0][1]) / max(yvals(self.x_profile))
            except (ValueError, IndexError):
                scale = 1
            offset = self.camera.ROI[0][1]
            x, y = array(self.x_profile).T
            px, py = self.pixel((x, y * scale + offset))
            lines = []
            for i in range(0, len(px) - 1):
                line = px[i], py[i], px[i + 1], py[i + 1]
                if all(valid(array(line))):
                    lines.append(line)
            dc.DrawLineList(lines)
            # Draw vertical profile at the left edge of the ROI box.
            try:
                scale = 0.35 * (self.camera.ROI[1][0] - self.camera.ROI[0][0]) / max(yvals(self.y_profile))
            except (ValueError, IndexError):
                scale = 1
            offset = self.camera.ROI[0][0]
            x, y = array(self.y_profile).T
            px, py = self.pixel((y * scale + offset, x))
            lines = []
            for i in range(0, len(px) - 1):
                line = px[i], py[i], px[i + 1], py[i + 1]
                if all(valid(array(line))):
                    lines.append(line)
            dc.DrawLineList(lines)

        if self.camera.show_FWHM and hasattr(self, "FWHM") and hasattr(self, "CFWHM"):
            # Draw a box around center of the beam, with the size of the FWHM.
            width, height = self.FWHM
            cx, cy = self.CFWHM
            x1, y1 = self.pixel((cx - width / 2, cy - height / 2))
            x2, y2 = self.pixel((cx + width / 2, cy + height / 2))
            dc.SetPen(wx.Pen(self.camera.FWHM_color, 1))
            dc.DrawLines([(x1, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1)])

            # Annotate the FWHM box with dimensions.
            font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
            font.SetPointSize(10)
            dc.SetFont(font)
            dc.SetTextForeground(self.camera.FWHM_color)

            if self.scale_unit == "mm":
                if width < 1:
                    label = "%.0f um" % (width * 1000)
                else:
                    label = "%.3f mm" % width
            else:
                label = "%g %s" % (width, self.scale_unit)
            w, h = dc.GetTextExtent(label)
            cx = (x1 + x2) / 2
            cy = y2
            dc.DrawRotatedText(label, cx - w / 2, cy - h, 0)

            if self.scale_unit == "mm":
                if width < 1:
                    label = "%.0f um" % (height * 1000)
                else:
                    label = "%.3f mm" % height
            else:
                label = "%g %s" % (height, self.scale_unit)
            w, h = dc.GetTextExtent(label)
            cx = x2
            cy = (y1 + y2) / 2
            dc.DrawRotatedText(label, cx + h, cy - w / 2, -90)

        if self.camera.show_center and hasattr(self, "CFWHM"):
            # Draw a vertical and horizontal line through the center.
            cx, cy = self.CFWHM
            left, bottom = self.camera.ROI[0]
            right, top = self.camera.ROI[1]
            dc.SetPen(wx.Pen(self.camera.center_color, 1))
            dc.DrawLines([self.pixel((cx, bottom)), self.pixel((cx, top))])
            dc.DrawLines([self.pixel((left, cy)), self.pixel((right, cy))])

            # Annotate the lines.
            font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
            font.SetPointSize(10)
            dc.SetFont(font)
            dc.SetTextForeground(self.camera.center_color)

            if self.scale_unit == "mm":
                if abs(cx) < 1:
                    label = "%+.0f um" % (cx * 1000)
                else:
                    label = "%+.3f mm" % cx
            else:
                label = "%+g %s" % (cx, self.scale_unit)
            x, y = self.pixel((cx, 0.825 * bottom + 0.175 * top))
            w, h = dc.GetTextExtent(label)
            dc.DrawRotatedText(label, x + 2, y - h / 2, 0)

            if self.scale_unit == "mm":
                if abs(cy) < 1:
                    label = "%+.0f um" % (cy * 1000)
                else:
                    label = "%+.3f mm" % cy
            else:
                label = "%+g %s" % (cy, self.scale_unit)
            x, y = self.pixel((0.825 * left + 0.175 * right, cy))
            w, h = dc.GetTextExtent(label)
            dc.DrawRotatedText(label, x - h / 2, y + 2, -90)

        if self.camera.show_profile or self.camera.show_FWHM:
            # Draw box around Region of Interest
            x1, y1 = self.pixel(self.camera.ROI[0])
            x2, y2 = self.pixel(self.camera.ROI[1])
            dc.SetPen(wx.Pen(self.camera.ROI_color, 1))
            dc.DrawLines([(x1, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1)])

    def highlight_saturated(self, image):
        """Substitute the value of saturated pixels with the color specified
        by "saturated_color".
        image: RGB pixel data as 3D numpy array with dimensions
        3 x width x height."""
        from numpy import any
        threshold = self.camera.saturation_threshold
        # Pixel not saturated: mask = 0, saturated: mask = 1
        mask = any(image > threshold, axis=0)
        return highlight(image, mask, self.camera.saturated_color)

    def bad_pixel_mask(self, image):
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
        threshold = self.camera.bad_pixel_threshold
        # Pixel not saturated: mask = 0, saturated: mask = 1
        mask = any(image > threshold, axis=0)
        return mask

    def update_bad_pixels(self):
        """This defined all saturated pixels as bad pixels and updates the mask.
        """
        self.transformed_mask = self.bad_pixel_mask(self.camera.image)
        self.refresh()

    def pixel(self, position):
        """Convert from mm to pixel coordinates"""
        x, y = position
        from numpy import rint, nan_to_num
        cx, cy = self.camera.image_center
        px = int32(nan_to_num(rint((x / self.camera.pixelsize + cx) * self.scale_factor)))
        py = int32(nan_to_num(rint((-y / self.camera.pixelsize + cy) * self.scale_factor)))
        return [px, py]

    def point(self, position):
        """Convert from pixel coordinates to mm"""
        px, py = position
        cx, cy = self.camera.image_center
        x = (px / self.scale_factor - cx) * self.camera.pixelsize
        y = -(py / self.scale_factor - cy) * self.camera.pixelsize
        return [x, y]

    def OnResize(self, _event):
        self.scale_image()
        self.refresh()

    def OnLeftDown(self, event):
        """for dragging the crosshairs or scale
        called when the left mouse button is pressed or released or the
        mouse is moved.
        """

        p = self.cursor_pos(event)

        if self.camera.move_crosshairs:
            self.SetFocus()
            self.set_crosshairs(event)
            self.CaptureMouse()
            self.dragging = "crosshairs"
        else:
            if self.tool == "measure":
                P = self.point(p)
                self.camera.scale = [P, P]
                self.camera.show_scale = True
                self.dragging = "scale end"
                self.scale_selected = False
            if self.tool in self.pointer_functions:
                x, y = self.point(self.cursor_pos(event))
                self.Parent.OnPointerFunction(self.tool, x, y, "down")
            else:
                self.scale_selected = (self.shape(p).find("scale") >= 0)
                self.dragging = self.shape(p)
                self.drag_info = (self.point(p), list(self.camera.scale))
            if self.dragging:
                self.SetFocus()
                self.drag_shape(event)
                self.CaptureMouse()
        self.set_cursor(event)

    def OnMotion(self, event):
        """for dragging the crosshairs or scale
        called when the left mouse button is pressed or released or the
        mouse is moved.
        """
        self.set_cursor(event)

        if self.camera.move_crosshairs and event.Dragging() and self.dragging:
            self.set_crosshairs(event)
        elif event.Dragging() and self.dragging:
            self.drag_shape(event)
        if event.Dragging() and self.tool in self.pointer_functions:
            x, y = self.point(self.cursor_pos(event))
            self.Parent.OnPointerFunction(self.tool, x, y, "drag")

    def OnLeftUp(self, event):
        """for dragging the crosshairs or scale
        called when the left mouse button is pressed or released or the
        mouse is moved.
        """
        self.set_cursor(event)

        if self.dragging:
            self.ReleaseMouse()
        self.dragging = ""

        if self.tool in self.pointer_functions:
            x, y = self.point(self.cursor_pos(event))
            self.Parent.OnPointerFunction(self.tool, x, y, "up")

    def set_cursor(self, event):
        """Updates the pointer shape to reflect the mouse function."""
        p = self.cursor_pos(event)
        shape = self.shape(p)
        if self.camera.move_crosshairs:
            self.SetCursor(wx.Cursor(wx.CURSOR_PENCIL))
        elif self.tool == "measure":
            self.SetCursor(wx.Cursor(wx.CURSOR_PENCIL))
        elif self.tool in self.pointer_functions:
            self.SetCursor(crosshairs_cursor())
        elif self.dragging == "scale start" or self.dragging == "scale end":
            self.SetCursor(wx.Cursor(wx.CURSOR_SIZENESW))
        elif self.dragging:
            self.SetCursor(wx.Cursor(wx.CURSOR_SIZING))
        elif self.scale_selected and (self.shape(p) == "scale start" or self.shape(p) == "scale end"):
            self.SetCursor(wx.Cursor(wx.CURSOR_SIZENESW))
        elif shape == "scale":
            self.SetCursor(wx.Cursor(wx.CURSOR_SIZING))
        elif shape == "ROI xmin,ymin" or shape == "ROI xmax,ymax":
            self.SetCursor(wx.Cursor(wx.CURSOR_SIZENESW))
        elif shape == "ROI xmax,ymin" or shape == "ROI xmin,ymax":
            self.SetCursor(wx.Cursor(wx.CURSOR_SIZENWSE))
        elif shape.find("ROI x") != -1:
            self.SetCursor(wx.Cursor(wx.CURSOR_SIZEWE))
        elif shape.find("ROI y") != -1:
            self.SetCursor(wx.Cursor(wx.CURSOR_SIZENS))
        else:
            self.SetCursor(wx.Cursor(wx.CURSOR_DEFAULT))

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

    def drag_shape(self, event):
        """Update the scale based on the last mouse event"""
        # debug("Dragging shape: %r" % self.dragging)
        p = self.cursor_pos(event)
        P = self.point(p)

        if self.dragging == "scale start":
            scale = self.camera.scale
            scale[0] = P
            self.camera.scale = scale

        if self.dragging == "scale end":
            scale = self.camera.scale
            scale[1] = P
            self.camera.scale = scale

        if self.dragging == "scale":
            scale = self.camera.scale
            P0, (P1, P2) = self.drag_info
            scale[0] = translate(P1, vector(P0, P))
            scale[1] = translate(P2, vector(P0, P))
            self.camera.scale = scale

        if self.dragging == "ROI xmin":
            ROI = self.camera.ROI
            ROI[0][0] = P[0]
            self.camera.ROI = ROI

        if self.dragging == "ROI xmax":
            ROI = self.camera.ROI
            ROI[1][0] = P[0]
            self.camera.ROI = ROI

        if self.dragging == "ROI ymin":
            ROI = self.camera.ROI
            ROI[0][1] = P[1]
            self.camera.ROI = ROI

        if self.dragging == "ROI ymax":
            ROI = self.camera.ROI
            ROI[1][1] = P[1]
            self.camera.ROI = ROI

        if self.dragging == "ROI xmin,ymin":
            ROI = self.camera.ROI
            ROI[0] = P
            self.camera.ROI = ROI

        if self.dragging == "ROI xmax,ymax":
            ROI = self.camera.ROI
            ROI[1] = P
            self.camera.ROI = ROI

        if self.dragging == "ROI xmax,ymin":
            ROI = self.camera.ROI
            ROI[1][0], ROI[0][1] = P
            self.camera.ROI = ROI

        if self.dragging == "ROI xmin,ymax":
            ROI = self.camera.ROI
            ROI[0][0], ROI[1][1] = P
            self.camera.ROI = ROI

    def shape(self, cursor_pos):
        """Tell over which which of the displayed object, like scale, ROI the
        cursor_pos is close to (within 4 pixels).
        cursor_pos is in units of pixels
        "scale" = line of scale
        "scale start","scale end" = endpoints of scale
        "ROI xmin" = side of Region of interest
        "ROI xmin,ymin" = corner of Region of interest
        """
        p = cursor_pos
        if self.camera.show_scale and self.camera.scale is not None:
            p1, p2 = self.pixel(self.camera.scale[0]), self.pixel(self.camera.scale[1])
            if distance(p1, p) < 4:
                return "scale start"
            if distance(p2, p) < 4:
                return "scale end"
            if point_line_distance(p, (p1, p2)) < 5:
                return "scale"
        if self.camera.show_profile or self.camera.show_FWHM or self.camera.show_FWHM:
            xmin, ymin = self.pixel(self.camera.ROI[0])
            xmax, ymax = self.pixel(self.camera.ROI[1])
            if distance((xmin, ymin), p) < 4:
                return "ROI xmin,ymin"
            if distance((xmax, ymin), p) < 4:
                return "ROI xmax,ymin"
            if distance((xmin, ymax), p) < 4:
                return "ROI xmin,ymax"
            if distance((xmax, ymax), p) < 4:
                return "ROI xmax,ymax"
            if point_line_distance(p, ((xmin, ymin), (xmax, ymin))) < 5:
                return "ROI ymin"
            if point_line_distance(p, ((xmax, ymin), (xmax, ymax))) < 5:
                return "ROI xmax"
            if point_line_distance(p, ((xmax, ymax), (xmin, ymax))) < 5:
                return "ROI ymax"
            if point_line_distance(p, ((xmin, ymax), (xmin, ymin))) < 5:
                return "ROI xmin"
        return ""

    def set_crosshairs(self, event):
        """Updates the crosshairs position based on the last mouse event"""
        x, y = self.cursor_pos(event)
        self.camera.image_center = (int(round(x / self.scale_factor)), int(round(y / self.scale_factor)))

    def cursor_pos(self, event):
        """Returns the cursor position during the given event, taking into
        account the scrollbar position (but not the image scale factor)"""
        x, y = self.CalcUnscrolledPosition(event.GetX(), event.GetY())
        ox, oy = self.Origin
        return x - ox, y - oy

    def OnContextMenu(self, _event):
        menu = wx.Menu()
        menu.Append(1, "Show Scale", "", wx.ITEM_CHECK)
        if self.camera.show_scale:
            menu.Check(1, True)
        self.Bind(wx.EVT_MENU, self.OnShowScale, id=1)
        menu.Append(2, "Show Box", "", wx.ITEM_CHECK)
        if self.camera.show_box:
            menu.Check(2, True)
        self.Bind(wx.EVT_MENU, self.OnShowBox, id=2)
        menu.Append(6, "Show Crosshairs", "", wx.ITEM_CHECK)
        if self.camera.show_crosshairs:
            menu.Check(6, True)
        self.Bind(wx.EVT_MENU, self.OnShowCrosshairs, id=6)
        menu.Append(22, "Show Grid", "", wx.ITEM_CHECK)
        if self.camera.show_grid:
            menu.Check(22, True)
        self.Bind(wx.EVT_MENU, self.OnShowGrid, id=22)
        menu.Append(9, "Show Beam Profile", "", wx.ITEM_CHECK)
        if self.camera.show_profile:
            menu.Check(9, True)
        self.Bind(wx.EVT_MENU, self.OnShowProfile, id=9)
        menu.Append(14, "Show Beam FWHM", "", wx.ITEM_CHECK)
        if self.camera.show_FWHM:
            menu.Check(14, True)
        self.Bind(wx.EVT_MENU, self.OnShowFWHM, id=14)
        menu.Append(17, "Show Center Line", "", wx.ITEM_CHECK)
        if self.camera.show_center:
            menu.Check(17, True)
        self.Bind(wx.EVT_MENU, self.OnShowCenter, id=17)
        menu.Append(11, "Show Saturated Pixels", "", wx.ITEM_CHECK)
        if self.camera.show_saturated_pixels:
            menu.Check(11, True)
        self.Bind(wx.EVT_MENU, self.OnShowSaturatedPixels, id=11)
        menu.Append(18, "Mask Bad Pixels", "", wx.ITEM_CHECK)
        if self.camera.mask_bad_pixels:
            menu.Check(18, True)
        self.Bind(wx.EVT_MENU, self.OnMaskBadPixels, id=18)

        for i in range(0, len(self.objects)):
            name = list(self.objects.keys())[i]
            ID = 200 + i
            menu.Append(ID, name, "", wx.ITEM_CHECK)
            if self.show_object[name]:
                menu.Check(ID, True)
            self.Bind(wx.EVT_MENU, self.OnShowObject, id=ID)

        menu.AppendSeparator()

        menu.Append(7, "Measure", "", wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.OnMeasure, id=7)
        if self.tool == "measure":
            menu.Check(7, True)
        for i in range(0, len(self.pointer_functions)):
            name = self.pointer_functions[i]
            ID = 100 + i
            menu.Append(ID, name, "", wx.ITEM_CHECK)
            if name == self.PointerFunction:
                menu.Check(ID, True)
            self.Bind(wx.EVT_MENU, self.OnSelectPointerFunction, id=ID)

        menu.AppendSeparator()

        if self.camera.show_scale:
            menu.Append(8, "Scale...", "")
        self.Bind(wx.EVT_MENU, self.OnScaleProperties, id=8)
        if self.camera.show_crosshairs:
            menu.Append(4, "Crosshairs...", "")
        self.Bind(wx.EVT_MENU, self.OnCrosshairsProperties, id=4)
        if self.camera.show_box:
            menu.Append(5, "Box...", "")
        self.Bind(wx.EVT_MENU, self.OnBoxProperties, id=5)
        if self.camera.show_grid:
            menu.Append(23, "Grid...", "")
        self.Bind(wx.EVT_MENU, self.OnGridProperties, id=23)
        if self.camera.show_profile or self.camera.show_FWHM:
            menu.Append(10, "Beam Profile...", "")
        self.Bind(wx.EVT_MENU, self.OnProfileProperties, id=10)
        if self.camera.show_profile:
            menu.Append(13, "Channels...", "")
        self.Bind(wx.EVT_MENU, self.OnChannelProperties, id=13)
        if self.camera.show_saturated_pixels:
            menu.Append(12, "Saturated Pixels...", "")
        self.Bind(wx.EVT_MENU, self.OnSaturatedPixelProperties, id=12)
        if self.camera.mask_bad_pixels:
            menu.Append(20, "Bad Pixels...", "")
        self.Bind(wx.EVT_MENU, self.OnBadPixelProperties, id=20)

        # Display the menu. If an item is selected then its handler will
        # be called before "PopupMenu" returns.
        self.PopupMenu(menu)
        menu.Destroy()

    def OnShowScale(self, _event):
        """Called if "Show Scale" is selected from the context menu"""
        self.camera.show_scale = not self.camera.show_scale
        if self.camera.show_scale:
            self.set_default_scale()
        self.refresh()

    def set_default_scale(self):
        """Set default position for scale"""
        w, h = self.ImageSize
        x, y = self.ImageOrigin
        length = 0.4 * w
        length = round(length, int(round(-log10(length) + 0.5)))
        self.camera.scale = [(x + w * 0.5 - length / 2, y + h * 0.05), (x + w * 0.5 + length / 2, y + h * 0.05)]

    def OnShowBox(self, _event):
        """Called if "Show Box" is selected from the context menu"""
        self.camera.show_box = not self.camera.show_box
        self.refresh()

    def OnShowCrosshairs(self, _event):
        """Called if "Show Crosshairs" is selected from the context menu"""
        self.camera.show_crosshairs = not self.camera.show_crosshairs
        self.refresh()

    def OnShowGrid(self, _event):
        """Called if "Show Crosshairs" is selected from the context menu"""
        self.camera.show_grid = not self.camera.show_grid
        self.refresh()

    def OnShowProfile(self, _event):
        """Called if "Show Crosshairs" is selected from the context menu"""
        self.camera.show_profile = not self.camera.show_profile
        self.refresh()

    def OnShowFWHM(self, _event):
        """Called if "Show Crosshairs" is selected from the context menu"""
        self.camera.show_FWHM = not self.camera.show_FWHM
        self.refresh()

    def OnShowCenter(self, _event):
        """Called if "Show Crosshairs" is selected from the context menu"""
        self.camera.show_center = not self.camera.show_center
        self.refresh()

    def OnShowSaturatedPixels(self, _event):
        """Called if "Show Crosshairs" is selected from the context menu"""
        self.camera.show_saturated_pixels = not self.camera.show_saturated_pixels
        self.refresh()

    def OnMaskBadPixels(self, _event):
        """Called if "Mask Bad Pixels" is selected from the context menu"""
        self.camera.mask_bad_pixels = not self.camera.mask_bad_pixels
        self.refresh()

    def GetMoveCrosshairs(self):
        """Are the crosshairs is movable or locked?"""
        return self.tool == "move crosshairs"

    def SetMoveCrosshairs(self, value):
        if value:
            self.tool = "move crosshairs"
        else:
            self.tool = ""

    MoveCrosshairs = property(GetMoveCrosshairs, SetMoveCrosshairs)

    def OnShowObject(self, event):
        """Called if any of the user-defined objects is selected from the
        context menu"""
        i = event.Id - 200
        if 0 <= i < len(self.objects):
            name = list(self.objects.keys())[i]
            self.show_object[name] = True if event.IsChecked() else False

    def OnMeasure(self, _event):
        """Called if "Measure" is selected from the context menu"""
        if self.tool == "measure":
            self.tool = ""
        else:
            self.tool = "measure"

    def OnSelectPointerFunction(self, event):
        """Called if any of the user-defined pointer functions is selected
        from the context menu"""
        if event.IsChecked():
            i = event.Id - 100
            if 0 <= i < len(self.pointer_functions):
                self.tool = self.pointer_functions[i]
        else:
            self.tool = ""

    def OnScaleProperties(self, _event):
        dlg = ScaleProperties(self, self.name)
        dlg.CenterOnParent()
        pos = dlg.GetPosition()
        pos.y += 100
        dlg.SetPosition(pos)
        dlg.Show()

    def OnCrosshairsProperties(self, _event):
        dlg = CrosshairsProperties(self, self.name)
        dlg.CenterOnParent()
        pos = dlg.GetPosition()
        pos.y += 100
        dlg.SetPosition(pos)
        dlg.Show()

    def OnBoxProperties(self, _event):
        dlg = BoxProperties(self, self.name)
        dlg.CenterOnParent()
        pos = dlg.GetPosition()
        pos.y += 100
        dlg.SetPosition(pos)
        dlg.Show()

    def OnGridProperties(self, _event):
        dlg = GridProperties(self, self.name)
        dlg.CenterOnParent()
        pos = dlg.GetPosition()
        pos.y += 100
        dlg.SetPosition(pos)
        dlg.Show()

    def OnProfileProperties(self, _event):
        dlg = ProfileProperties(self, self.name)
        dlg.CenterOnParent()
        pos = dlg.GetPosition()
        pos.y += 100
        dlg.SetPosition(pos)
        dlg.Show()

    def OnSaturatedPixelProperties(self, _event):
        dlg = SaturatedPixelProperties(self, self.name)
        dlg.CenterOnParent()
        pos = dlg.GetPosition()
        pos.y += 100
        dlg.SetPosition(pos)
        dlg.Show()

    def OnBadPixelProperties(self, _event):
        dlg = BadPixelProperties(self, self.name)
        dlg.CenterOnParent()
        pos = dlg.GetPosition()
        pos.y += 100
        dlg.SetPosition(pos)
        dlg.Show()

    def OnChannelProperties(self, _event):
        dlg = ChannelProperties(self, self.name)
        dlg.CenterOnParent()
        pos = dlg.GetPosition()
        pos.y += 100
        dlg.SetPosition(pos)
        dlg.Show()

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.name)


class CrosshairsProperties(wx.Dialog):
    """Allows the user to to read the cross position, enter the position
    numerically and change its color."""

    def __init__(self, parent, name):
        wx.Dialog.__init__(self, parent, -1, "Crosshairs")
        self.name = name
        # Controls
        from EditableControls import TextCtrl
        self.Coordinates = TextCtrl(
            self, size=(75, -1), style=wx.TE_PROCESS_ENTER)
        self.Movable = wx.CheckBox(self, label="Movable")
        self.CrosshairsSize = TextCtrl(
            self, size=(75, -1), style=wx.TE_PROCESS_ENTER)
        self.ShowCrosshairs = wx.CheckBox(self, label="Show")
        h = self.Coordinates.GetSize().y
        self.Color = wx.lib.colourselect.ColourSelect(
            self, colour=self.camera.crosshairs_color, size=(h, h))
        # Callbacks
        self.Bind(wx.EVT_TEXT_ENTER, self.OnEnterCoordinates, self.Coordinates)
        self.Bind(wx.EVT_CHECKBOX, self.OnMovable, self.Movable)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnEnterCrosshairsSize,
                  self.CrosshairsSize)
        self.Bind(wx.EVT_CHECKBOX, self.OnShowCrosshairs, self.ShowCrosshairs)
        self.Color.Bind(wx.lib.colourselect.EVT_COLOURSELECT,
                        self.OnSelectColour)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        # Layout
        layout = wx.FlexGridSizer(cols=3, hgap=5, vgap=5)
        label = wx.StaticText(self, label="Position (x,y) [pixels]:")
        layout.Add(label, flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add(self.Coordinates, flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add(self.Movable, flag=wx.ALIGN_CENTER_VERTICAL)
        label = wx.StaticText(self, label="Size (w,h) [mm]:")
        layout.Add(label, flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add(self.CrosshairsSize, flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add(self.ShowCrosshairs, flag=wx.ALIGN_CENTER_VERTICAL)
        label = wx.StaticText(self, label="Line color:")
        layout.Add(label, flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add(self.Color, flag=wx.ALIGN_CENTER_VERTICAL)
        self.SetSizer(layout)
        self.Fit()
        self.update()

    @property
    def camera(self):
        return camera(self.name)

    def update(self, _event=None):
        """Fill the fields"""
        self.Coordinates.Value = "%d,%d" % self.camera.image_center
        self.CrosshairsSize.Value = "%.3f,%.3f" % self.camera.crosshairs_size
        self.ShowCrosshairs.Value = self.camera.show_crosshairs
        self.Movable.Value = self.camera.move_crosshairs
        self.Color.Value = self.camera.crosshairs_color
        # Relaunch yourself.
        self.update_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update, self.update_timer)
        self.update_timer.Start(1000, oneShot=True)

    update_timer = None

    def OnEnterCoordinates(self, _event):
        text = self.Coordinates.GetValue()
        try:
            (tx, ty) = text.split(",")
            self.camera.image_center = (float(tx), float(ty))
        except ValueError:
            return

    def OnMovable(self, _event):
        self.camera.move_crosshairs = self.Movable.Value

    def OnEnterCrosshairsSize(self, _event):
        text = self.CrosshairsSize.GetValue()
        try:
            (tx, ty) = text.split(",")
            self.camera.crosshairs_size = (float(tx), float(ty))
        except ValueError:
            return

    def OnShowCrosshairs(self, _event):
        self.camera.show_crosshairs = self.ShowCrosshairs.Value

    def OnSelectColour(self, event):
        self.camera.crosshairs_color = event.GetValue().Get()

    def OnClose(self, _event):
        """Called when the close button is clocked.
        When the dialog is closed automatically lock the crosshairs."""
        self.camera.move_crosshairs = False
        self.Destroy()

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.name)


class BoxProperties(wx.Dialog):
    """Allows the user to change the box size and color"""

    def __init__(self, parent, name):
        wx.Dialog.__init__(self, parent, title="Box")
        self.name = name
        # Controls
        from EditableControls import TextCtrl
        self.BoxSize = TextCtrl(self, size=(75, -1),
                                style=wx.TE_PROCESS_ENTER)
        self.ShowBox = wx.CheckBox(self, label="Show")
        h = self.BoxSize.GetSize().y
        self.Color = wx.lib.colourselect.ColourSelect(self, -1, "",
                                                      self.camera.box_color, size=(h, h))
        # Callbacks
        self.Bind(wx.EVT_TEXT_ENTER, self.OnEnterBoxSize, self.BoxSize)
        self.Bind(wx.EVT_CHECKBOX, self.OnShowBox, self.ShowBox)
        self.Color.Bind(wx.lib.colourselect.EVT_COLOURSELECT, self.OnSelectColour)
        # Layout
        layout = wx.FlexGridSizer(cols=3, hgap=5, vgap=5)
        label = wx.StaticText(self, label="Width,Height [mm]:")
        layout.Add(label, flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add(self.BoxSize, flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add(self.ShowBox, flag=wx.ALIGN_CENTER_VERTICAL)
        label = wx.StaticText(self, label="Line color:")
        layout.Add(label, flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add(self.Color, flag=wx.ALIGN_CENTER_VERTICAL)
        self.SetSizer(layout)
        self.Fit()
        self.update()

    @property
    def camera(self):
        return camera(self.name)

    def update(self, _event=None):
        """Fill the fields"""
        self.BoxSize.Value = "%.3f,%.3f" % self.camera.box_size
        self.ShowBox.Value = self.camera.show_box
        self.Color.Value = self.camera.box_color
        # Relaunch yourself.
        self.update_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update, self.update_timer)
        self.update_timer.Start(1000, oneShot=True)

    update_timer = None

    def OnEnterBoxSize(self, _event):
        text = self.BoxSize.GetValue()
        try:
            (tx, ty) = text.split(",")
            self.camera.box_size = (float(tx), float(ty))
        except ValueError:
            return

    def OnShowBox(self, _event):
        self.camera.show_box = self.ShowBox.Value

    def OnSelectColour(self, event):
        self.camera.box_color = event.GetValue().Get()

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.name)


class ScaleProperties(wx.Dialog):
    """Allows the user to enter the length of the measurement scale numerically,
    make the line exactly horizontal or vertical and change its color.
    """

    def __init__(self, parent, name):
        wx.Dialog.__init__(self, parent, title="Scale")
        self.name = name
        # Controls
        from EditableControls import TextCtrl
        self.Length = TextCtrl(self, size=(60, -1), style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnEnterLength, self.Length)
        self.Horizontal = wx.CheckBox(self, label="Horizontal")
        self.Bind(wx.EVT_CHECKBOX, self.OnHorizontal, self.Horizontal)
        self.Vertical = wx.CheckBox(self, label="Vertical")
        self.Bind(wx.EVT_CHECKBOX, self.OnVertical, self.Vertical)
        h = self.Length.GetSize().y
        self.Color = wx.lib.colourselect.ColourSelect(self, size=(h, h))
        self.Color.Bind(wx.lib.colourselect.EVT_COLOURSELECT, self.OnSelectColour)
        # Layout
        layout = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
        label = wx.StaticText(self, label="Length [mm]:")
        layout.Add(label, flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add(self.Length, flag=wx.ALIGN_CENTER_VERTICAL)
        label = wx.StaticText(self, label="Direction:")
        layout.Add(label, flag=wx.ALIGN_CENTER_VERTICAL)
        group = wx.BoxSizer()
        group.Add(self.Horizontal)
        group.AddSpacer(5)
        group.Add(self.Vertical)
        layout.Add(group)
        label = wx.StaticText(self, label="Line color:")
        layout.Add(label, flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add(self.Color, flag=wx.ALIGN_CENTER_VERTICAL)
        self.SetSizer(layout)
        self.Fit()
        self.update()

    @property
    def camera(self):
        return camera(self.name)

    def update(self, _event=None):
        """Fill the fields"""
        (P1, P2) = self.camera.scale
        length = distance(P1, P2)
        self.Length.Value = "%.3f" % length
        v = vector(P1, P2)
        self.Horizontal.Value = (v[1] == 0)
        self.Vertical.Value = (v[0] == 0)

        self.Color.Value = self.camera.scale_color

        # Relaunch yourself.
        self.update_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update, self.update_timer)
        self.update_timer.Start(1000, oneShot=True)

    update_timer = None

    def OnEnterLength(self, _event):
        text = self.Length.GetValue()
        try:
            length = float(text)
        except ValueError:
            return
        (P1, P2) = self.camera.scale
        P2 = translate(P1, scale(direction(vector(P1, P2)), length))
        self.camera.scale = [P1, P2]

    def OnHorizontal(self, _event):
        self.Horizontal.SetValue(True)
        self.Vertical.SetValue(False)
        (P1, P2) = self.camera.scale
        length = distance(P1, P2)
        P2 = translate(P1, (length, 0))
        self.camera.scale = [P1, P2]

    def OnVertical(self, _event):
        self.Horizontal.SetValue(False)
        self.Vertical.SetValue(True)
        (P1, P2) = self.camera.scale
        length = distance(P1, P2)
        P2 = translate(P1, (0, length))
        self.camera.scale = [P1, P2]

    def OnSelectColour(self, event):
        self.camera.scale_color = event.GetValue().Get()

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.name)


class GridProperties(wx.Dialog):
    """Allows the user to change the box size and color"""

    def __init__(self, parent, name):
        wx.Dialog.__init__(self, parent, title="Grid")
        self.name = name
        # Controls
        from EditableControls import ComboBox, TextCtrl
        style = wx.TE_PROCESS_ENTER
        size = (75, -1)
        self.Type = ComboBox(self, size=size, choices=["X", "Y", "XY"])
        self.Bind(wx.EVT_COMBOBOX, self.OnEnterType, self.Type)
        self.XSpacing = TextCtrl(self, size=size, style=style)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnEnterXSpacing, self.XSpacing)
        self.XOffset = TextCtrl(self, size=size, style=style)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnEnterXOffset, self.XOffset)

        self.YSpacing = TextCtrl(self, size=size, style=style)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnEnterYSpacing, self.YSpacing)
        self.YOffset = TextCtrl(self, size=size, style=style)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnEnterYOffset, self.YOffset)

        w, h = self.XSpacing.Size
        self.Color = wx.lib.colourselect.ColourSelect(self, size=(h, h))
        self.Color.Bind(wx.lib.colourselect.EVT_COLOURSELECT,
                        self.OnSelectColour)
        # Layout
        layout = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)

        label = wx.StaticText(self, label="Type:")
        layout.Add(label, flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add(self.Type, flag=wx.ALIGN_CENTER_VERTICAL)

        self.XSpacingLabel = wx.StaticText(self, label="Horizontal spacing:")
        layout.Add(self.XSpacingLabel, flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add(self.XSpacing, flag=wx.ALIGN_CENTER_VERTICAL)
        self.XOffsetLabel = wx.StaticText(self, label="Horizontal offset:")
        layout.Add(self.XOffsetLabel, flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add(self.XOffset, flag=wx.ALIGN_CENTER_VERTICAL)

        self.YSpacingLabel = wx.StaticText(self, label="Vertical spacing:")
        layout.Add(self.YSpacingLabel, flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add(self.YSpacing, flag=wx.ALIGN_CENTER_VERTICAL)
        self.YOffsetLabel = wx.StaticText(self, label="Vertical offset:")
        layout.Add(self.YOffsetLabel, flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add(self.YOffset, flag=wx.ALIGN_CENTER_VERTICAL)

        label = wx.StaticText(self, label="Color:")
        layout.Add(label, flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add(self.Color, flag=wx.ALIGN_CENTER_VERTICAL)
        self.SetSizer(layout)
        self.Fit()
        self.update()

    @property
    def camera(self):
        return camera(self.name)

    def update(self, _event=None):
        """Fill the fields"""
        grid_type = self.camera.grid_type
        self.Type.Value = grid_type.upper()

        # Show only those controls actually needed for the selected grid type.
        self.XSpacingLabel.Show("x" in grid_type)
        self.XSpacing.Show("x" in grid_type)
        self.XOffsetLabel.Show("x" in grid_type)
        self.XOffset.Show("x" in grid_type)

        self.YSpacingLabel.Show("y" in grid_type)
        self.YSpacing.Show("y" in grid_type)
        self.YOffsetLabel.Show("y" in grid_type)
        self.YOffset.Show("y" in grid_type)

        self.Fit()

        dx = self.camera.grid_x_spacing
        self.XSpacing.Value = "%.3f mm" % dx if not isnan(dx) else ""
        x0 = self.camera.grid_x_offset
        self.XOffset.Value = "%.3f mm" % x0 if not isnan(x0) else ""

        dy = self.camera.grid_y_spacing
        self.YSpacing.Value = "%.3f mm" % dy if not isnan(dy) else ""
        y0 = self.camera.grid_y_offset
        self.YOffset.Value = "%.3f mm" % y0 if not isnan(y0) else ""

        self.Color.Value = self.camera.grid_color
        # Relaunch yourself.
        self.update_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update, self.update_timer)
        self.update_timer.Start(1000, oneShot=True)

    update_timer = None

    def OnEnterType(self, _event):
        self.camera.grid_type = self.Type.Value.lower()
        self.update()

    def OnEnterXSpacing(self, _event):
        text = self.XSpacing.Value.replace("mm", "")
        try:
            value = float(eval(text))
        except Exception:
            pass
        else:
            self.camera.grid_x_spacing = value
        self.update()

    def OnEnterXOffset(self, _event):
        text = self.XOffset.Value.replace("mm", "")
        try:
            value = float(eval(text))
        except Exception:
            pass
        else:
            self.camera.grid_x_offset = value
        self.update()

    def OnEnterYSpacing(self, _event):
        text = self.YSpacing.Value.replace("mm", "")
        try:
            value = float(eval(text))
        except Exception:
            pass
        else:
            self.camera.grid_y_spacing = value
        self.update()

    def OnEnterYOffset(self, _event):
        text = self.YOffset.Value.replace("mm", "")
        try:
            value = float(eval(text))
        except Exception:
            pass
        else:
            self.camera.grid_y_offset = value
        self.update()

    def OnSelectColour(self, event):
        self.camera.grid_color = event.GetValue().Get()

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.name)


class ProfileProperties(wx.Dialog):
    """Allows the user to change the beam profile box color"""

    def __init__(self, parent, name):
        wx.Dialog.__init__(self, parent, title="Beam Profile")
        self.name = name
        # Controls
        from EditableControls import TextCtrl
        self.Correction = wx.Choice(self, size=(60, -1), choices=["on", "off"])
        self.Bind(wx.EVT_CHOICE, self.OnCorrection, self.Correction)

        self.Projection = wx.RadioButton(self, label="Projection",
                                         style=wx.RB_GROUP)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnProfileType, self.Projection)
        self.Section = wx.RadioButton(self, label="Section")
        self.Bind(wx.EVT_RADIOBUTTON, self.OnProfileType, self.Section)

        self.Threshold = TextCtrl(self, size=(60, -1),
                                  style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnEnterThreshold, self.Threshold)

        h = self.Threshold.GetSize().y
        self.ProfileColor = wx.lib.colourselect.ColourSelect(self, size=(h, h))
        self.ProfileColor.Bind(wx.lib.colourselect.EVT_COLOURSELECT,
                               self.OnSelectProfileColor)
        self.FWHMColor = wx.lib.colourselect.ColourSelect(self, size=(h, h))
        self.FWHMColor.Bind(wx.lib.colourselect.EVT_COLOURSELECT,
                            self.OnSelectFWHMColor)
        self.CenterColor = wx.lib.colourselect.ColourSelect(self, size=(h, h))
        self.CenterColor.Bind(wx.lib.colourselect.EVT_COLOURSELECT,
                              self.OnSelectCenterColor)
        self.ROIColor = wx.lib.colourselect.ColourSelect(self, size=(h, h))
        self.ROIColor.Bind(wx.lib.colourselect.EVT_COLOURSELECT,
                           self.OnSelectROIColor)
        # Layout
        layout = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
        label = wx.StaticText(self, label="Linearity correction:")
        layout.Add(label, flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add(self.Correction, flag=wx.ALIGN_CENTER_VERTICAL)
        label = wx.StaticText(self, label="Saturation threshold [0-255]:")
        layout.Add(label, flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add(self.Threshold, flag=wx.ALIGN_CENTER_VERTICAL)
        label = wx.StaticText(self, label="Profile type:")
        layout.Add(label, flag=wx.ALIGN_CENTER_VERTICAL)
        group = wx.BoxSizer()
        group.Add(self.Projection)
        group.AddSpacer(5)
        group.Add(self.Section)
        layout.Add(group)
        label = wx.StaticText(self, label="Profile color:")
        layout.Add(label, flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add(self.ProfileColor, flag=wx.ALIGN_CENTER_VERTICAL)
        label = wx.StaticText(self, label="FWHM box color:")
        layout.Add(label, flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add(self.FWHMColor, flag=wx.ALIGN_CENTER_VERTICAL)
        label = wx.StaticText(self, label="Center line color:")
        layout.Add(label, flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add(self.CenterColor, flag=wx.ALIGN_CENTER_VERTICAL)
        label = wx.StaticText(self, label="Region:")
        layout.Add(label, flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add(self.ROIColor, flag=wx.ALIGN_CENTER_VERTICAL)
        self.SetSizer(layout)
        self.Fit()
        self.update()

    @property
    def camera(self):
        return camera(self.name)

    def update(self, _event=None):
        """Fill the fields"""
        text = "on" if self.camera.linearity_correction else "off"
        self.Correction.SetStringSelection(text)
        self.Section.Value = self.camera.calculate_section

        self.Threshold.Value = "%d" % self.camera.saturation_threshold

        self.Section.Value = self.camera.calculate_section
        self.Projection.Value = not self.camera.calculate_section

        self.ProfileColor.Value = self.camera.profile_color
        self.FWHMColor.Value = self.camera.FWHM_color
        self.CenterColor.Value = self.camera.center_color
        self.ROIColor.Value = self.camera.ROI_color

        # Relaunch yourself.
        self.update_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update, self.update_timer)
        self.update_timer.Start(1000, oneShot=True)

    update_timer = None

    def OnEnterThreshold(self, _event):
        text = self.Threshold.Value
        try:
            self.camera.saturation_threshold = min(max(0, int(text)), 255)
        except ValueError:
            pass
        self.Threshold.Value = "%d" % self.camera.saturation_threshold

    def OnCorrection(self, _event):
        text = self.Correction.GetStringSelection()
        self.camera.linearity_correction = (text == "on")

    def OnProfileType(self, _event):
        self.camera.calculate_section = self.Section.Value

    def OnSelectProfileColor(self, _event):
        self.camera.Refresh()

    def OnSelectFWHMColor(self, event):
        self.camera.FWHM_color = event.GetValue().Get()

    def OnSelectCenterColor(self, event):
        self.camera.center_color = event.GetValue().Get()

    def OnSelectROIColor(self, event):
        self.camera.ROI_color = event.GetValue().Get()

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.name)


class SaturatedPixelProperties(wx.Dialog):
    """Allows the user to change the color with which saturated pixels are
    marked"""

    def __init__(self, parent, name):
        wx.Dialog.__init__(self, parent, title="Saturated Pixels")
        self.name = name
        # Controls
        from EditableControls import TextCtrl
        self.Threshold = TextCtrl(self, size=(60, -1), style=wx.TE_PROCESS_ENTER)
        self.Color = wx.lib.colourselect.ColourSelect(self, -1, "", size=(20, 20))
        # Callbacks
        self.Bind(wx.EVT_TEXT_ENTER, self.OnEnterThreshold, self.Threshold)
        self.Color.Bind(wx.lib.colourselect.EVT_COLOURSELECT,
                        self.OnSelectColour)
        # Layout
        layout = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
        label = wx.StaticText(self, label="Threshold [0-255]:")
        layout.Add(label, flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add(self.Threshold, flag=wx.ALIGN_CENTER_VERTICAL)
        label = wx.StaticText(self, label="Highlight Color:")
        layout.Add(label, flag=wx.ALIGN_CENTER_VERTICAL)
        layout.Add(self.Color, flag=wx.ALIGN_CENTER_VERTICAL)
        self.SetSizer(layout)
        self.Fit()
        self.update()

    @property
    def camera(self):
        return camera(self.name)

    def update(self, _event=None):
        """Fill the fields."""
        self.Threshold.Value = "%d" % self.camera.saturation_threshold
        self.Color.Value = self.camera.saturated_color
        # Relaunch yourself.
        self.update_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update, self.update_timer)
        self.update_timer.Start(1000, oneShot=True)

    update_timer = None

    def OnSelectColour(self, event):
        self.camera.saturated_color = event.GetValue().Get()

    def OnEnterThreshold(self, _event):
        text = self.Threshold.GetValue()
        try:
            self.camera.saturation_threshold = min(max(0, int(text)), 255)
        except ValueError:
            pass
        self.Threshold.Value = "%d" % self.camera.saturation_threshold

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.name)


class BadPixelProperties(wx.Dialog):
    """Allows the user to change the color with which saturated pixels are
    marked"""

    def __init__(self, parent, name):
        wx.Dialog.__init__(self, parent, title="Bad Pixels")
        self.name = name
        # Controls
        from EditableControls import TextCtrl
        self.Threshold = TextCtrl(self, size=(60, -1),
                                  style=wx.TE_PROCESS_ENTER)
        self.Color = wx.lib.colourselect.ColourSelect(self, -1, "", size=(20, 20))
        UpdateButton = wx.Button(self, label="Update")
        self.Bind(wx.EVT_TEXT_ENTER, self.OnEnterThreshold, self.Threshold)
        # Callbacks
        self.Color.Bind(wx.lib.colourselect.EVT_COLOURSELECT,
                        self.OnSelectColour)
        self.Bind(wx.EVT_BUTTON, self.OnUpdate, UpdateButton)
        # Layout
        layout = wx.BoxSizer(wx.VERTICAL)

        grid = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
        label = wx.StaticText(self, label="Threshold [0-255]:")
        grid.Add(label, flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.Threshold, flag=wx.ALIGN_CENTER_VERTICAL)
        label = wx.StaticText(self, label="Highlight Color:")
        grid.Add(label, flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.Color, flag=wx.ALIGN_CENTER_VERTICAL)

        layout.Add(grid, flag=wx.ALIGN_CENTER, border=10)
        layout.AddSpacer(10)
        layout.Add(UpdateButton, flag=wx.ALIGN_CENTER, border=10)

        self.SetSizer(layout)
        self.Fit()
        self.update()

    @property
    def camera(self):
        return camera(self.name)

    def update(self, _event=None):
        """Fill the fields"""
        self.Threshold.Value = "%d" % self.camera.bad_pixel_threshold
        self.Color.Value = self.camera.bad_pixel_color
        # Relaunch yourself.
        self.update_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update, self.update_timer)
        self.update_timer.Start(1000, oneShot=True)

    update_timer = None

    def OnSelectColour(self, event):
        self.camera.bad_pixel_color = event.GetValue().Get()

    def OnEnterThreshold(self, _event=0):
        text = self.Threshold.Value
        try:
            self.camera.bad_pixel_threshold = min(max(0, int(text)), 255)
        except ValueError:
            pass
        self.Threshold.Value = "%d" % self.camera.bad_pixel_threshold

    def OnUpdate(self, _event):
        self.OnEnterThreshold()
        self.camera.update_bad_pixels()

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.name)


class ChannelProperties(wx.Dialog):
    """Allows the user to select which of the channels R,G,B to use"""

    def __init__(self, parent, name):
        wx.Dialog.__init__(self, parent, title="Channels")
        self.name = name
        # Controls
        self.Red = wx.CheckBox(self, label="Red")
        self.Bind(wx.EVT_CHECKBOX, self.OnChannel, self.Red)
        self.Green = wx.CheckBox(self, label="Green")
        self.Bind(wx.EVT_CHECKBOX, self.OnChannel, self.Green)
        self.Blue = wx.CheckBox(self, label="Blue")
        self.Bind(wx.EVT_CHECKBOX, self.OnChannel, self.Blue)
        R, G, B = self.camera.use_channels
        self.Red.SetValue(R)
        self.Green.SetValue(G)
        self.Blue.SetValue(B)
        # Layout
        layout = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
        label = wx.StaticText(self, label="Use Channels:")
        layout.Add(label, flag=wx.ALIGN_CENTER_VERTICAL)
        group = wx.BoxSizer()
        group.Add(self.Red)
        group.AddSpacer(5)
        group.Add(self.Green)
        group.AddSpacer(5)
        group.Add(self.Blue)
        layout.Add(group)
        self.SetSizer(layout)
        self.Fit()

    @property
    def camera(self): return camera(self.name)

    def OnChannel(self, _event):
        R = self.Red.GetValue()
        G = self.Green.GetValue()
        B = self.Blue.GetValue()
        self.camera.use_channels = (R, G, B)

    def __repr__(self): return "%s(%r)" % (type(self).__name__, self.name)


class ViewerOptions(BasePanel):
    title = "Viewer Options"
    standard_view = [
        "Title",
    ]

    def __init__(self, parent, name):
        self.name = name
        from Panel import PropertyPanel
        parameters = [
            [[PropertyPanel, "Title", self.camera, "title"], {"refresh_period": 1.0, "width": 240}],
        ]
        BasePanel.__init__(
            self,
            parent=parent,
            name=self.name,
            title=self.title,
            parameters=parameters,
            standard_view=self.standard_view,
            subname=True,
            refresh=False,
            live=False,
            label_width=90,
        )

    @property
    def camera(self): return camera(self.name)

    def __repr__(self): return "%s(%r)" % (type(self).__name__, self.name)


class CameraOptions(wx.Dialog):
    title = "Camera Options"

    def __init__(self, parent, name):
        wx.Dialog.__init__(self, parent, title=self.title)
        self.name = f"instrumentation.{camera(name).domain_name}.camera_controls.{camera(name).base_name}"
        # Controls
        self.Prefix = TextCtrl_Control(
            self,
            self.name + ".prefix",
            size=(250, -1),
        )
        self.ServerIPAddress = TextCtrl_Control(
            self,
            self.name + ".server_ip_address",
            style=wx.TE_READONLY,
            size=(110, -1),
        )
        self.CameraIPAddress = ComboBox_Control(
            self,
            name=self.name + ".camera_ip_address",
            choices_name=self.name + ".camera_ip_addresses",
            size=(250, -1),
        )
        self.Multicast = CheckBox_Control(
            self,
            self.name + ".use_multicast",
        )
        self.ExternalTrigger = CheckBox_Control(
            self,
            self.name + ".external_trigger",
        )
        self.Gain = TextCtrl_Control(
            self,
            name=self.name + ".gain",
            size=(40, -1),
        )
        self.PixelFormat = ComboBox_Control(
            self,
            name=self.name + ".pixel_format",
            choices_name=self.name + ".pixel_formats",
            size=(80, -1),
        )
        self.BinFactor = ComboBox_Control(
            self,
            name=self.name + ".bin_factor",
            choices_name=self.name + ".bin_factors",
            size=(40, -1),
        )
        self.StreamBytesPerSecond = TextCtrl_Control(
            self,
            name=self.name + ".stream_bytes_per_second",
            size=(100, -1),
        )

        layout = wx.BoxSizer(wx.VERTICAL)
        grid = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
        flag = wx.ALIGN_CENTER_VERTICAL
        grid.Add(wx.StaticText(self, label="Prefix:"), flag=flag)
        grid.Add(self.Prefix, flag=flag)
        grid.Add(wx.StaticText(self, label="Server Address:"), flag=flag)
        grid.Add(self.ServerIPAddress, flag=flag)
        grid.Add(wx.StaticText(self, label="Camera Address:"), flag=flag)
        grid.Add(self.CameraIPAddress, flag=flag)
        grid.Add(wx.StaticText(self, label="Multicast:"), flag=flag)
        grid.Add(self.Multicast, flag=flag)
        grid.Add(wx.StaticText(self, label="External Trigger:"), flag=flag)
        grid.Add(self.ExternalTrigger, flag=flag)
        grid.Add(wx.StaticText(self, label="Gain:"), flag=flag)
        grid.Add(self.Gain, flag=flag)
        grid.Add(wx.StaticText(self, label="Pixel format:"), flag=flag)
        grid.Add(self.PixelFormat, flag=flag)
        grid.Add(wx.StaticText(self, label="Bin Factor:"), flag=flag)
        grid.Add(self.BinFactor, flag=flag)
        grid.Add(wx.StaticText(self, label="Stream Bytes/s:"), flag=flag)
        grid.Add(self.StreamBytesPerSecond, flag=flag)
        layout.Add(grid, flag=wx.ALIGN_CENTER | wx.ALL, border=10)

        self.Sizer = layout
        self.Fit()

    def __repr__(self): return "%s(%r)" % (type(self).__name__, self.name)


class OpticsOptions(BasePanel):
    name = "optics"
    title = "Optics Options"
    standard_view = [
        "Nominal pixel size",
        "Zoom",
        "Zoom levels",
    ]

    def __init__(self, parent, name):
        self.name = name
        from Panel import PropertyPanel
        parameters = [
            [[PropertyPanel, "Nominal pixel size", self.camera, "nominal_pixelsize"], {"unit": "mm", "refresh_period": 1.0, "width": 240}],
            [[PropertyPanel, "Zoom", self.camera, "has_zoom"], {"refresh_period": 1.0, "width": 240}],
            [[PropertyPanel, "Zoom levels", self.camera, "zoom_levels"], {"type": "list", "refresh_period": 1.0, "width": 240}],
        ]
        BasePanel.__init__(self,
                           parent=parent,
                           name=self.name,
                           title=self.title,
                           parameters=parameters,
                           standard_view=self.standard_view,
                           subname=True,
                           refresh=False,
                           live=False,
                           label_width=90,
                           )

    @property
    def camera(self): return camera(self.name)

    def __repr__(self): return "%s(%r)" % (type(self).__name__, self.name)


def camera(name):
    from camera_control import camera_control
    return camera_control(name)


def distance(p1, p2):
    """Distance between two points"""
    x1, y1 = p1
    x2, y2 = p2
    return sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def point_line_distance(P, line):
    """Distance of a point to a line segment of finite length"""
    # Source: http://softsurfer.com/Archive/algorithm_0102/algorithm_0102.htm
    # 18 May 2007
    P0 = line[0]
    P1 = line[1]
    v = vector(P0, P1)
    w0 = vector(P0, P)
    w1 = vector(P1, P)
    # If the angle (P,P0,P1) is obtuse (>=90 deg), it is the distance to P0.
    if dot(w0, v) <= 0:
        return distance(P, P0)
    # If the angle(P,P1,P0) is obtuse (>=90 deg), it is the distance to P1.
    if dot(w1, v) >= 0:
        return distance(P, P1)
    # Otherwise, it is the orthogonal distance to the line.
    b = dot(w0, v) / float(dot(v, v))
    Pb = translate(P0, scale(v, b))
    return distance(P, Pb)


def vector(p1, p2):
    """Vector from point p1=(x1,y1) to point p2=(x2,y2)"""
    x1, y1 = p1
    x2, y2 = p2
    return x2 - x1, y2 - y1


def translate(p, v):
    """Apply the vector v=(vx,vy) to point p=(x,y)"""
    x, y = p
    vx, vy = v
    return x + vx, y + vy


def scale(v, a):
    """Multiply vector v=(x,y) with scalar"""
    x, y = v
    return a * x, a * y


def direction(v):
    """Vector v=(x,y) scaled to unit length"""
    x, y = v
    length = sqrt(x ** 2 + y ** 2)
    if length == 0:
        return 1., 0.
    return x / length, y / length


def dot(v1, v2):
    """Scalar product between vectors (x1,y1) and (x2,y2)"""
    x1, y1 = v1
    x2, y2 = v2
    return x1 * x2 + y1 * y2


def FWHM(data):
    """Calculates full-width at half-maximum of a positive peak of a curve
    given as list of [x,y] values"""
    x = xvals(data)
    y = yvals(data)
    n = len(data)
    if n > 0:
        HM = (min(y) + max(y)) / 2
        i = 0
        for i in range(0, n):
            if y[i] > HM:
                break
        if i == 0:
            x1 = x[0]
        else:
            x1 = interpolate_x((x[i - 1], y[i - 1]), (x[i], y[i]), HM)
        r = list(range(0, n))
        r.reverse()
        for i in r:
            if y[i] > HM:
                break
        if i == n - 1:
            x2 = x[n - 1]
        else:
            x2 = interpolate_x((x[i + 1], y[i + 1]), (x[i], y[i]), HM)
        FWHM = abs(x2 - x1)
    else:
        FWHM = nan
    return FWHM


def CFWHM(data):
    """Calculates the center of the full width half of the positive peak of
    a curve given as list of [x,y] values"""
    x = xvals(data)
    y = yvals(data)
    n = len(data)
    if n > 0:
        HM = (min(y) + max(y)) / 2
        i = 0
        for i in range(0, n):
            if y[i] > HM:
                break
        if i == 0:
            x1 = x[0]
        else:
            x1 = interpolate_x((x[i - 1], y[i - 1]), (x[i], y[i]), HM)
        r = list(range(0, n))
        r.reverse()
        for i in r:
            if y[i] > HM:
                break
        if i == n - 1:
            x2 = x[n - 1]
        else:
            x2 = interpolate_x((x[i + 1], y[i + 1]), (x[i], y[i]), HM)
        CFWHM = (x2 + x1) / 2.
    else:
        CFWHM = nan
    return CFWHM


def interpolate_x(p1, p2, y):
    """Linear interpolation between two points"""
    x1, y1 = p1
    x2, y2 = p2
    # In case result is undefined, midpoint is as good as any value.
    if y1 == y2:
        return (x1 + x2) / 2.
    x = x1 + (x2 - x1) * (y - y1) / float(y2 - y1)
    # print("interpolate_x [%g,%g,%g][%g,%g,%g]" % (x1,x,x2,y1,y,y2))
    return x


def xvals(xy_data):
    """xy_data = list of (x,y)-tuples. Returns list of x values only."""
    xvals = []
    for i in range(0, len(xy_data)):
        xvals.append(xy_data[i][0])
    return xvals


def yvals(xy_data):
    """xy_data = list of (x,y)-tuples. Returns list of y values only."""
    yvals = []
    for i in range(0, len(xy_data)):
        yvals.append(xy_data[i][1])
    return yvals


def save(columns, filename, header="", labels=None):
    """Usage: save([x,y],"test.txt",labels="x,y")
    Write lists of numbers as tab-separated ASCII file.
    "columns" must be a list containing lists of numeric values of the same
    length.
    "labels" can be given as comma-separated string or as list of strings.
    """
    from isstring import isstring
    output = open(filename, "w")
    for line in header.split("\n"):
        if line:
            output.write("# " + line + "\n")
    if labels:
        if isstring(labels):
            labels = labels.split(",")
        output.write("#")
        for col in range(0, len(labels) - 1):
            output.write(labels[col] + "\t")
        output.write(labels[len(labels) - 1] + "\n")
    N_col = len(columns)
    N_row = 0
    for col in range(0, N_col):
        N_row = max(N_row, len(columns[col]))
    for row in range(0, N_row):
        for col in range(0, N_col):
            try:
                val = columns[col][row]
            except IndexError:
                val = ""
            if isstring(val):
                output.write(val)
            else:
                output.write("%g" % val)
            if col < N_col - 1:
                output.write("\t")
            else:
                output.write("\n")


@cached_function()
def crosshairs_cursor():
    """A black crosshairs cursor of size 13x13 pixels with white border
    as wx.Cursor object"""
    # This is a replacement for wx.Cursor(wx.CURSOR_CROSS)
    # Under Windows, the wxPython's built-in crosshairs cursor does not have a
    # white border and is hard to see on a black background.
    filename = icon_dir() + "/crosshairs.png"
    if exists(filename):
        image = wx.Image(filename)
        image.SetOption(wx.IMAGE_OPTION_CUR_HOTSPOT_X, 7)
        image.SetOption(wx.IMAGE_OPTION_CUR_HOTSPOT_Y, 7)
        crosshairs_cursor = wx.Cursor(image)
    else:
        warning("%s not found" % filename)
        crosshairs_cursor = wx.Cursor(wx.CURSOR_CROSS)
    return crosshairs_cursor


def icon_dir():
    """pathname of the directory from which to load custom icons"""
    from module_dir import module_dir
    return module_dir(icon_dir) + "/icons"


def int32(x):
    """Force conversion of x to 32-bit signed integer"""
    if hasattr(x, "astype"):
        x = x.astype(int)
    else:
        x = int(x)
    maxint = int(2 ** 31 - 1)
    minint = int(-2 ** 31)
    from numpy import clip
    x = clip(x, minint, maxint)
    return x


if __name__ == "__main__":  # for testing
    # from pdb import pm  # for debugging

    # _name = "BioCARS.MicroscopeCamera"
    _name = "BioCARS.WideFieldCamera"
    # _name = "TestBench.Microscope"
    # _name = "TestBench.MicrofluidicsCamera"
    # _name = "LaserLab.LaserLabCamera"
    # _name = "LaserLab.FLIR1"

    from redirect import redirect
    domain_name = camera(_name).domain_name
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    redirect(f"{domain_name}.Camera_Viewer", level="DEBUG", format=msg_format)

    # import logging
    # logging.getLogger("EPICS_CA.EPICS_CA").level = logging.DEBUG

    from wx_init import wx_init
    wx_init()

    app = wx.GetApp() if wx.GetApp() else wx.App()
    self = Camera_Viewer(name=_name)
    app.MainLoop()
