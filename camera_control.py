#!/usr/bin/env python
"""
Author: Friedrich Schotte
Python Version: 2.7, 3.6
Date created: 2020-04-15
Date last modified: 2021-06-16
Revision comment: Cleanup
"""
__version__ = "1.6.1"

from logging import info

from cached_function import cached_function
from camera_client import Camera
from reference import reference


@cached_function()
def camera_control(name):
    return Camera_Control(name)


class Camera_Control(Camera):
    from db_property import db_property
    from local_property import local_property
    from monitored_property import monitored_property
    from monitored_method import monitored_method
    from numpy import nan

    @property
    def default_title(self): return f"{self.base_name} [{self.domain_name}]"

    title = db_property("title", default_title)
    nominal_pixelsize = db_property("NominalPixelSize", 0.00465)
    orientation = db_property("Orientation", 0.0)
    mirror = db_property("Mirror", False)
    center = db_property("ImageWindow.Center", [680, 512])
    scale_factor = db_property("scale_factor", 1.0)
    scale_factors = db_property("scale_factors", [2.0, 1.0, 0.5, 0.33, 0.25, nan])
    has_zoom = db_property("has_zoom", False)
    zoom_levels = db_property("zoom_levels", [1.0])
    zoom_level = db_property("zoom_level", 1.0)

    filename = local_property("filename", "image.jpg")

    show_crosshairs = local_property("show_crosshairs", True)
    crosshairs_size = local_property("crosshairs_size", (0.2, 0.2))
    crosshairs_color = local_property("crosshairs_color", (255, 0, 255))
    move_crosshairs = local_property("move_crosshairs", False)
    show_scale = local_property("show_scale", False)
    scale = local_property("scale", [(-0.1, -0.1), (-0.1, 0.1)])
    scale_color = local_property("scale_color", (128, 128, 255))
    show_box = local_property("show_box", False)
    box_size = local_property("box_size", (0.1, 0.06))
    box_color = local_property("box_color", (128, 128, 255))
    show_profile = local_property("show_profile", False)
    calculate_section = local_property("calculate_section", False)
    profile_color = local_property("profile_color", (255, 0, 255))
    show_FWHM = local_property("show_FWHM", False)
    FWHM_color = local_property("FWHM_color", (255, 196, 0))
    show_center = local_property("show_center", False)
    center_color = local_property("center_color", (255, 196, 0))
    show_grid = local_property("show_grid", False)
    grid_type = local_property("grid_type", "xy")
    grid_x_spacing = local_property("grid_x_spacing", 1.0)  # mm
    grid_x_offset = local_property("grid_x_offset", 0.0)  # mm with respect to the crosshairs
    grid_y_spacing = local_property("grid_y_spacing", 1.0)  # mm
    grid_y_offset = local_property("grid_y_offset", 0.0)  # mm with respect to the crosshairs
    grid_color = local_property("grid_color", (0, 0, 255))

    ROI = local_property("ROI", [[-0.2, -0.2], [0.2, 0.2]])  # (xmin,ymin),(xmax,ymax)
    ROI_color = local_property("ROI_color", (255, 196, 0))
    show_saturated_pixels = local_property("show_saturated_pixels", False)
    saturation_threshold = local_property("saturation_threshold", 233)
    saturated_color = local_property("saturated_color", (255, 0, 0))
    mask_bad_pixels = local_property("mask_bad_pixels", False)
    linearity_correction = local_property("linearity_correction", False)
    bad_pixel_threshold = local_property("bad_pixel_threshold", 233)
    bad_pixel_color = local_property("bad_pixel_color", (30, 30, 30))

    viewport_center = local_property("viewport_center", [0.0, 0.0])
    pointer_function = local_property("pointer_function", "")

    show_illumination_panel = local_property("show_illumination_panel", False)

    @monitored_property
    def pixelsize(self, nominal_pixelsize, has_zoom, zoom_level):
        """Scaled pixelsize if camera optics have zoom"""
        if has_zoom:
            pixelsize = nominal_pixelsize / zoom_level
        else:
            pixelsize = nominal_pixelsize
        return pixelsize

    @pixelsize.setter
    def pixelsize(self, pixelsize):
        if self.has_zoom:
            self.nominal_pixelsize = pixelsize * self.zoom_level
        else:
            self.nominal_pixelsize = pixelsize

    @monitored_property
    def image_width(self, width, height, normalized_orientation):
        """Horizontal size of rotated image in pixels"""
        if normalized_orientation in [0, 180]:
            return width
        else:
            return height

    @monitored_property
    def image_height(self, width, height, normalized_orientation):
        """Vertical size of rotated image in pixels"""
        if normalized_orientation in [0, 180]:
            return height
        else:
            return width

    @monitored_property
    def image(self, RGB_array):
        """Image in orientation as displayed (rotated, mirrored)"""
        return self.transform_image(RGB_array)

    @image.dependency_references
    def image(self):
        return [reference(self, "transform_image")]

    @monitored_property
    def image_center(self, center):
        """Coordinates of cross displayed on the image, in pixels, from top
        left, with rotation/mirror applied"""
        return self.transform(center)

    @image_center.dependency_references
    def image_center(self):
        return [reference(self, "transform")]

    @image_center.setter
    def image_center(self, center):
        self.center = self.back_transform(center)

    @property
    def mask(self):
        """Bad pixel bitmap in orientation as displayed"""
        return self.transform_mask(self.mask_array)

    @mask.setter
    def mask(self, mask):
        self.mask_array = self.back_transform_mask(mask)

    _mask = None

    @property
    def mask_array(self):
        """bitmap identifying "bad pixels" """
        if self._mask is not None:
            mask = self._mask
        else:
            mask = self.default_mask
        return mask

    @mask_array.setter
    def mask_array(self, mask):
        self._mask = mask

    @property
    def default_mask(self):
        from numpy import zeros
        return zeros((self.width, self.height), bool)

    def save_image(self, filename):
        """Saves last acquired image in a file
        filename: destination 
           Extension (.jpg, .png, .tif) determines file format
        """
        from PIL import Image
        image = Image.new('RGB', (self.image_width, self.image_height))
        image.frombytes(self.image.T.tobytes())
        from os import makedirs
        from os.path import dirname, exists
        if dirname(filename) and not exists(dirname(filename)):
            makedirs(dirname(filename))
        info("Saving %r" % filename)
        image.save(filename)

    @monitored_method
    def transform(self, position):
        """Transform coordinates (x,y) from raw to rotated image.
        Return value: (x,y)"""
        x, y = position
        w, h = self.width, self.height
        if self.mirror:
            x = w - x  # flip horizontally
        if self.normalized_orientation == 90:
            x, y = y, w - x
        if self.normalized_orientation == 180:
            x, y = w - x, h - y
        if self.normalized_orientation == 270:
            x, y = h - y, x
        return x, y

    @transform.dependencies
    def transform(self):
        return [
            reference(self, "width"),
            reference(self, "height"),
            reference(self, "mirror"),
            reference(self, "normalized_orientation"),
        ]

    def back_transform(self, position):
        """Transform coordinates (x,y) from rotated image to raw image.
        Return value: (x,y)"""
        x, y = position
        w, h = self.width, self.height
        if self.normalized_orientation == 90:
            x, y = w - y, x
        if self.normalized_orientation == 180:
            x, y = w - x, h - y
        if self.normalized_orientation == 270:
            x, y = y, h - x
        if self.mirror:
            x = w - x  # flip horizontally
        return x, y

    @monitored_method
    def transform_image(self, image):
        """Transform from raw to displayed to displayed image.
        image: 3D numpy array with dimensions 3 x width x height
        Return value: rotated version of the input image"""
        if self.mirror:
            image = image[:, ::-1, :]  # flip horizontally
        if self.normalized_orientation == 90:
            image = image.transpose(0, 2, 1)[:, :, ::-1]
        if self.normalized_orientation == 180:
            image = image[:, ::-1, ::-1]
        if self.normalized_orientation == 270:
            image = image.transpose(0, 2, 1)[:, ::-1, :]
        return image

    @transform_image.dependencies
    def transform_image(self):
        return [
            reference(self, "mirror"),
            reference(self, "normalized_orientation"),
        ]

    def back_transform_image(self, image):
        """Transform from displayed to raw image.
        image: 3D numpy array with dimensions 3 x width x height
        Return value: rotated version of the input image"""
        if self.normalized_orientation == 90:
            image = image.transpose(0, 2, 1)[:, ::-1, :]
        if self.normalized_orientation == 180:
            image = image[:, ::-1, ::-1]
        if self.normalized_orientation == 270:
            image = image.transpose(0, 2, 1)[:, :, ::-1]
        if self.mirror:
            image = image[:, ::-1, :]  # flip horizontally
        return image

    def transform_mask(self, mask):
        """Transform from raw to displayed to displayed image.
        mask: 2D numpy array dimensions width x height
        Return value: rotated version of the input image"""
        if self.mirror:
            mask = mask[::-1, :]  # flip horizontally
        if self.normalized_orientation == 90:
            mask = mask.transpose(1, 0)[:, ::-1]
        if self.normalized_orientation == 180:
            mask = mask[::-1, ::-1]
        if self.normalized_orientation == 270:
            mask = mask.transpose(1, 0)[::-1, :]
        return mask

    def back_transform_mask(self, mask):
        """Transform from raw to displayed to displayed image.
        mask: 2D numpy array dimensions width x height
        Return value: rotated version of the input image"""
        if self.normalized_orientation == 90:
            mask = mask.transpose(1, 0)[::-1, :]
        if self.normalized_orientation == 180:
            mask = mask[::-1, ::-1]
        if self.normalized_orientation == 270:
            mask = mask.transpose(1, 0)[:, ::-1]
        if self.mirror:
            mask = mask[::-1, :]  # flip horizontally
        return mask

    @monitored_property
    def normalized_orientation(self, orientation):
        """Angle in units of deg
        positive = counterclockwise, must be a multiple of 90 deg
        Values: 0, 90, 128, 270"""
        from numpy import rint
        return rint((orientation % 360) / 90.) * 90

    @normalized_orientation.setter
    def normalized_orientation(self, value):
        self.orientation = value


if __name__ == "__main__":
    import logging

    level = logging.DEBUG
    msg_format = "%(asctime)s: %(message)s"
    logging.basicConfig(level=level, format=msg_format)

    from handler import handler as _handler
    from reference import reference as _reference

    # self = camera_control("BioCARS.MicroscopeCamera")
    self = camera_control("BioCARS.WideFieldCamera")
    # self = camera_control("TestBench.Microscope")
    # self = camera_control("TestBench.MicrofluidicsCamera")
    # self = camera_control("LaserLab.LaserLabCamera")
    # self = camera_control("LaserLab.FLIR1")


    @_handler
    def report(event=None):
        logging.info(f"event={event}")


    _reference(self, "scale_factor").monitors.add(report)
