#!/usr/bin/env python
"""
Driver for Prosilica GigE CCD cameras.
Author: Friedrich Schotte
Date created: 2010-10-16
Date last modified: 2021-01-10
Revision comment: Issue: Exposure time not updating when auto-exposure
"""
__version__ = "2.13.7"

# Copied libPvAPI-1.22-OSX-x86.dylib from  AVT GigE SDK 1.22 for Mac OS X,
# bin-pc/x86/libPvAPI.dylib

# AVT PvAPI Programmer's Reference Manual, Version 1.22, March 10, 2010
# https://www.alliedvision.com/fileadmin/content/documents/products/software/software/PvAPI/docu/PvAPI_SDK_Manual.pdf
# Lauecollect/doc/PvAPI-1.22.pdf

# AVT PvAPI Programmer's Reference Manual, V1.28 20 March 2015
# https://www.alliedvision.com/fileadmin/content/documents/products/software/software/PvAPI/docu/PvAPI_SDK_Manual.pdf
# Lauecollect/doc/PvAPI-1.28.pdf

# AVT GigE Camera and Driver Attributes Firmware 1.38, April 7, 2010
# Lauecollect/doc/PvAPI_Attributes-1.38.pdf

# AVT GigE Camera and Driver Attributes, Prosilica Firmware version 01.54,
# V1.4.1 2017-June-19
# https://www.alliedvision.com/fileadmin/content/documents/products/cameras/various/features/Camera_and_Driver_Attributes.pdf
# Lauecollect/doc/PvAPI_Attributes-1.54.pdf

# ctypes Tutorial
# http://python.net/crew/theller/ctypes/tutorial.html
import warnings
from ctypes import Structure
from logging import debug, info, warning, error


class GigE_camera(object):
    from persistent_property_new import persistent_property
    from cached import cached

    default_width = 1360
    default_height = 1024
    reception_timeout = 10.0
    retry_interval = 60
    auto_resume = True

    IP_addr = persistent_property("GigE_camera.{name}.camera.IP_addr",
                                  "pico3.niddk.nih.gov")
    # Can multiple computers on the network receive the same video stream 
    # simultaneously? (Requires 'sudoers' privileges under Linux)
    use_multicast = persistent_property("GigE_camera.{name}.use_multicast", False)

    def __init__(self, name="Camera"):
        """name: used to store persistent_properties"""
        self.name = name
        from ctypes import c_void_p
        from numpy import nan
        self.handle = c_void_p()
        self.last_error = ""
        self.last_mode = "not connected"
        self.last_connection_failed_time = 0
        self.acquisition_started = False
        self.capturing_images = True
        self.Frames = [self.Frame() for _ in range(0, 2)]
        # Mark all frames as been not "valid" (Status = 0).
        for i in range(0, len(self.Frames)):
            self.Frames[i].frame.Status = 99
        self.framerate = nan
        self.handlers = {}
        self.resume_active = 0

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.name)

    def handle_updates(self, property_names):
        for property_name in property_names:
            self.handle_update(property_name)

    def handle_update(self, property_name):
        event = self.event(property_name)
        self.__getattr_monitors__(property_name).call(event=event)

    def event(self, property_name):
        from event import event
        from time import time
        from reference import reference
        event = event(
            time=time(),
            value=getattr(self, property_name),
            reference=reference(self, property_name)
        )
        return event

    def __getattr_monitors__(self, property_name):
        if property_name not in self.handlers:
            from event_handlers import Event_Handlers
            self.handlers[property_name] = Event_Handlers()
        return self.handlers[property_name]

    class Frame(object):
        def __init__(self):
            from ctypes import c_char
            self.frame = tPvFrame()
            self.buffer = (c_char * 0)()
            self.queued_time = 0

        def mark_as_invalid(self):
            """Mark frame buffer as "not containing a valid image"""
            self.frame.FrameCount = 0
            self.frame.TimestampHi = 0
            self.frame.TimestampLo = 0
            self.frame.Status = 99  # 0 Status indicates "frame complete".
            self.buffer[0:2] = b"\xFE\xFE"  # marker for testing
            self.buffer[-2:] = b"\xFE\xFE"  # marker for testing
            from time import time
            self.queued_time = time()
            from numpy import nan
            self.reception_started_time = nan

        @property
        def reception_pending_time(self):
            from time import time
            from numpy import nan
            if self.reception_pending:
                value = time() - self.reception_started_time
            else:
                value = nan
            return value

        @property
        def reception_pending(self):
            value = self.reception_started and not self.reception_finished
            return value

        @property
        def reception_started(self):
            ImageBuffer = self.frame.ImageBuffer
            value = (ImageBuffer and len(ImageBuffer) >= 2
                     and ImageBuffer[0:2] != b"\xFE\xFE")
            return value

        @property
        def reception_finished(self):
            ImageBuffer = self.frame.ImageBuffer
            value = (ImageBuffer and len(ImageBuffer) >= 2 and
                     ImageBuffer[-2:] != b"\xFE\xFE")
            return value

        @property
        def reception_started_time(self):
            from numpy import nan, isnan
            value = getattr(self, "__reception_started_time__", nan)
            if isnan(value) and self.reception_started:
                from time import time
                value = time()
                self.reception_started_time = value
            return value

        @reception_started_time.setter
        def reception_started_time(self, value):
            setattr(self, "__reception_started_time__", value)

    def init(self, mode="control"):
        if self.mode != mode:
            # control is good for read-only too
            if not (mode == "read-only" and self.mode == "control"):
                self.mode = mode

    @property
    def mode(self):
        """ "control", "read-only", "not connected" """
        mode = "not connected"
        if self.handle_valid(self.handle):
            mode = self.last_mode
        return mode

    @mode.setter
    def mode(self, mode):
        if mode != self.mode:
            if mode in ["control", "read-only"]:
                from time import time
                if time() > self.last_connection_failed_time + self.retry_interval:
                    if self.handle:
                        # Even for handles no longer valid 'PvCameraClose' should be called.
                        debug("PvCameraClose")
                        self.PvAPI.PvCameraClose(self.handle)
                    self.handle.value = None
                    self.last_mode = "not connected"
                    self.last_error = ""

                    from socket import gethostbyname, gaierror
                    try:
                        dot_addr = gethostbyname(self.IP_addr)
                    except gaierror as x:
                        error("%s: %s" % (self.IP_addr, x))
                        dot_addr = None
                    if dot_addr:
                        from struct import unpack
                        from socket import inet_aton
                        int_addr, = unpack("I", inet_aton(dot_addr))
                        self.initialize_PvAPI()
                        debug("Connecting...")
                        from ctypes import byref
                        access = 4 if mode == "control" else 2
                        status = self.PvAPI.PvCameraOpenByAddr(int_addr, access, byref(self.handle))
                        # If failed to connect as 'master', try as 'monitor'.
                        if status == 0:
                            self.last_mode = mode
                        elif status == 7 and mode == "control":  # 7: cannot be opened in the specified mode
                            debug("init, first attempt: mode %r, status %r" % (mode, status))
                            access = 2
                            status = self.PvAPI.PvCameraOpenByAddr(int_addr, access, byref(self.handle))
                            if status == 0:
                                self.last_mode = "read-only"
                        if status != 0:
                            self.last_mode = "not connected"
                            self.last_error = "not connected: " + error_message(status)
                            self.last_connection_failed_time = time()
                        debug("Connection state: %s" % self.last_mode)
            if mode == "not connected":
                # Even for handles no longer valid 'PvCameraClose' should be called.
                if self.handle:
                    debug("PvCameraClose")
                    self.PvAPI.PvCameraClose(self.handle)
                self.handle.value = None
                self.last_mode = "not connected"
                self.last_error = ""

    def get_acquiring(self):
        return self.acquisition_started

    def set_acquiring(self, value):
        if value:
            self.start()
        else:
            self.stop()

    acquiring = property(get_acquiring, set_acquiring)

    def start(self):
        """Starts video streaming."""
        from ctypes import c_char, c_char_p, addressof

        if self.capturing:
            return  # already started
        self.init("control")
        if self.handle.value is None:
            return  # camera unusable

        # Enable multicast mode so the connection can be shared by other viewers.
        # It is the responsibility of the first view connecting to request
        # multicast. If the first viewer connects without it, no other viewer
        # can access the video stream while the first one is connected.
        if self.use_multicast and self.mode == "control":
            self.set_attr("MulticastEnable", "On")

        # Allocate two frame buffers.
        frame_size = self.get_attr("TotalBytesPerFrame", 1360 * 1024)
        for i in range(0, len(self.Frames)):
            self.Frames[i].buffer = (c_char * frame_size)()
            self.Frames[i].frame.ImageBuffer = c_char_p(addressof(self.Frames[i].buffer))
            self.Frames[i].frame.ImageBufferSize = frame_size

        # Initialize the image capture stream.
        status = self.PvAPI.PvCaptureStart(self.handle)
        if status != 0:
            self.last_error = "not capturing: " + error_message(status)
            return
        else:
            self.last_error = ""

        # Set the camera in acquisition mode.
        if self.mode == "control":
            # Make sure that the ethernet packet size is OK for a network
            # that does not support Jumbo frames. (Factory setting is 8228
            # bytes.)
            if self.get_attr("PacketSize", 1500) > 1500:
                self.set_attr("PacketSize", 1500)
            # Set the bandwidth appropriately for 2 cameras sharing
            # one 100-Mb connection.
            # self.set_attr("StreamBytesPerSecond",5000000)
            status = self.command("AcquisitionStart")
            if status != 0:
                self.acquisition_started = False
            else:
                self.acquisition_started = True

        if self.acquisition_started:
            # Start the capturing of the life video network packets sent by the
            # camera to be reassembled as images in local memory.
            # This is done in a background thread in the PvAPI library, started by
            # calling PvCaptureQueueFrame.

            for i in range(0, len(self.Frames)):
                self.Frames[i].mark_as_invalid()
                from ctypes import byref
                status = self.PvAPI.PvCaptureQueueFrame(
                    self.handle, byref(self.Frames[i].frame), None)
                if status != 0:
                    warning("PvCaptureQueueFrame: " + error_message(status))
                    self.last_error = "PvCaptureQueueFrame: " + error_message(status)
                    break
            # "PvCaptureQueueFrame" acquires only a single image.
            # After this need to periodically call "resume" to put back the
            # image buffers into the capture queue.
            if status == 0:
                self.capturing_images = True

    @property
    def reception_timed_out(self):
        return self.reception_pending_time > self.reception_timeout

    @property
    def reception_pending_time(self):
        return nanmax([Frame.reception_pending_time for Frame in self.Frames])

    def resume_auto(self):
        if self.auto_resume and not self.resume_active:
            self.resume()

    def resume(self):
        """To be called periodically when capturing images"""
        if not self.resume_active:
            self.resume_active += 1
            if self.reception_timed_out:
                info("Reception timed out.")
                self.restart()
            # Image stream stops at image #65535
            if self.current_frame_count >= 65000:
                info("Frame count reached %r." % self.current_frame_count)
                self.restart()

            self.calculate_framerate()

            if self.capturing_images:
                # Find buffers with images that were completed, except the current
                # frame, and put them back into the queue of capture buffers.
                for i in range(0, len(self.Frames)):
                    if not self.frame_in_use(i):
                        self.Frames[i].mark_as_invalid()
                        from ctypes import byref
                        status = self.PvAPI.PvCaptureQueueFrame(
                            self.handle, byref(self.Frames[i].frame), None)
                        if status != 0:
                            warning("PvCaptureQueueFrame: " + error_message(status))
                            self.last_error = "PvCaptureQueueFrame:" + error_message(status)
                        else:
                            self.handle_frame_update()
            self.resume_active -= 1

    def handle_frame_update(self):
        self.handle_updates(self.frame_properties)

    frame_properties = [
        "frame_count",
        "rgb_array",
        "rgb_array_flat",
        "state",
        "timestamp",
        "has_image",
        "exposure_time",
    ]

    def frame_in_use(self, frame_number):
        in_use = False
        i = frame_number
        from time import time
        # Do not overwrite the last acquired image.
        if self.Frames[i].frame.FrameCount == self.current_frame_count:
            in_use = True
        else:
            # Do not re-enqueue a buffer already in the queue.
            if self.Frames[i].frame.FrameCount == 0:
                in_use = True
            if self.Frames[i].frame.Status == 99:
                in_use = True
            # Data transfer timed out.
            if time() - self.Frames[i].queued_time > self.reception_timeout:
                info("Queued frame timed out.")
                in_use = False
        return in_use

    def restart(self):
        info("Restarting...")
        self.stop()
        self.start()

    def stop(self):
        """This is to disconnect for the camera and leave the Prosilica
        Video Library in an orderly state"""
        self.capturing_images = False
        self.acquisition_started = False
        if self.handle.value is not None:
            self.command("AcquisitionStop")
            self.PvAPI.PvCaptureEnd(self.handle)
            self.PvAPI.PvCaptureQueueClear(self.handle)
            self.PvAPI.PvCameraClose(self.handle)
        self.handle.value = None

    def get_capturing(self):
        """Has the image capture stream been started?
        That is, has PvCaptureStart been called successfully?"""
        from ctypes import c_uint32, byref
        if self.handle is None:
            return False
        is_started = c_uint32()
        status = self.PvAPI.PvCaptureQuery(self.handle, byref(is_started))
        if status != 0:
            return False
        return is_started.value != 0

    capturing = property(get_capturing)

    def get_state(self):
        """one-line status report"""
        self.resume_auto()
        if not self.handle_valid(self.handle):
            state = "not connected"
        else:
            state = self.mode
            if self.get_attr("MulticastEnable", "Off") == "On":
                state += ", multicast"
            capturing = self.capturing
            if capturing:
                state += ", capturing"
                if self.external_trigger:
                    state += " (ext. trig.)"
            if self.reception_pending_time > 0:
                state += ", pending %.1f s" % self.reception_pending_time
            elif self.acquisition_started:
                state += ", started"
            if capturing and self.current_frame_count > 0:
                state += (", %.3g fps" % self.framerate)
                state += (", #%d" % self.current_frame_count)
            state += ", " + self.pixel_format
            if self.pixel_format not in ["Bayer8", "Rgb24"]:
                state += ", unsupported format"
            error_codes = []
            for Frame in self.Frames:
                if Frame.frame.Status not in [0, 99]:
                    if Frame.frame.Status not in error_codes:
                        error_codes += [Frame.frame.Status]
            for error_code in error_codes:
                state += ", " + error_message(error_code)
        if self.last_error:
            state += ", " + self.last_error
        return state

    state = property(get_state)

    def get_rgb_array_flat(self):
        """Last read image as 1D numpy array.
        Size: 1360 * 1024 * 3 = 4177920, data type: int8
        (int8 rather than uint8 for compatibility with EPICS CA  array PVs)
        """
        from numpy import int8
        from numpy import frombuffer
        rgb_array_flat = frombuffer(self.rgb_data, int8)
        return rgb_array_flat

    rgb_array_flat = property(get_rgb_array_flat)

    def get_rgb_array(self):
        """Last read image as 3D numpy array. Dimensions: 3xWxH
        datatype: uint8
        Usage R,G,B = camera.rgb_array"""
        from numpy import frombuffer, uint8
        w, h = self.width, self.height
        return frombuffer(self.rgb_data, uint8).reshape(h, w, 3).T

    rgb_array = RGB_array = property(get_rgb_array)

    def get_rgb_data(self):
        """All this pixels of the last read image as one single chunk
        of contiguous data.
        The format is one byte per pixel, in the order R,G,B, by scan line,
        top left to bottom right.
        'PixelFormat' attribute of the camera needs to be set to 'Bayer8'
        or 'Rgb24'.
        """
        self.resume_auto()
        if not self.has_image:
            return self.default_rgb_data()
        if self.image_pixel_format == "Rgb24":
            return self.get_image_data()
        elif self.image_pixel_format == "Bayer8":
            return self.rgb_from_bayer8()
        else:
            return self.default_rgb_data()

    rgb_data = property(get_rgb_data)

    def default_rgb_data(self):
        rgb_size = self.width * self.height * 3
        from numpy import zeros, int8
        rgb_array_flat = zeros(rgb_size, int8)
        rgb_data = rgb_array_flat.tobytes()
        return rgb_data

    def get_image_data(self):
        """Returns all this pixels of the last read image as one single chunk
        of contiguous data."""
        from ctypes import string_at
        frame = self.Frames[self.current_buffer()].frame
        buffer = self.Frames[self.current_buffer()].buffer
        if frame.ImageBufferSize == 0:
            return ""
        return string_at(buffer, frame.ImageBufferSize)

    def rgb_from_bayer8(self):
        """Assuming BayerPattern = 0:  first line RGRG, second line GBGB..."""
        from ctypes import addressof, byref, c_char, c_char_p, string_at
        frame = self.Frames[self.current_buffer()].frame
        RGB_size = frame.ImageBufferSize * 3
        RGB = (c_char * RGB_size)()
        addr = addressof(RGB)
        R, G, B = c_char_p(addr), c_char_p(addr + 1), c_char_p(addr + 2)
        self.PvAPI.PvUtilityColorInterpolate(byref(frame), R, G, B, 2, 0)
        return string_at(RGB, RGB_size)
        # PvUtilityColorInterpolate converts 8-bit Bayer mosaic images into
        # RGB24 images. The first parameter is the input frame data structure,
        # the following three parameter are the starting addresses for the
        # output R,G and B value respectively. The number 2 is the number of
        # bytes to skip between subsequent of R values (same for G and B),
        # and the last parameter is the number of bytes the skip and the end
        # is a scan line as padding.
        # Although RGB data is contiguous in memory, Prosilica requires to
        # pass three pointers for the same chunk of memory.
        # This gives the function the flexibility to also generate BRG images.
        # The number of bytes between R values is also a parameter so the
        # function can generate also RGB32 or RGBA output (skipping 3 bytes)
        # or separate color planes (skipping 0 bytes).

    def save_image(self, filename):
        """Acquire a single image from the camera and save it as a file.
        filename: the extension determines the image format, may be '.jpg',
        '.png' or '.tif' or any other extension supported by the Python Image
        Library (PIL)"""
        from PIL import Image
        image = Image.new('RGB', (self.width, self.height))
        image.fromstring(self.rgb_data)
        image.save(filename)

    def get_width(self):
        """number of columns in the image.
        If smaller that the chip width and bin factor = 1, a region of interest
        is read"""
        frame = self.Frames[self.current_buffer()].frame
        if frame.FrameCount > 0:
            width = frame.Width
        else:
            width = self.get_attr("Width", self.default_width)
        if width == 0 or width is None:
            width = self.default_width
        return width

    def set_width(self, value):
        self.set_attr("Width", value)

    width = property(get_width, set_width)

    def get_height(self):
        """number of rows in the image.
        If smaller that the chip height and bin factor = 1, a region of interest
        is read"""
        frame = self.Frames[self.current_buffer()].frame
        if frame.FrameCount > 0:
            height = frame.Height
        else:
            height = self.get_attr("Height", self.default_height)
        if height == 0 or height is None:
            height = self.default_height
        return height

    def set_height(self, value):
        self.set_attr("Height", value)

    height = property(get_height, set_height)

    def get_bin_factor(self):
        """Common CCD row and column binning factor"""
        return self.get_attr("BinningX", 1)

    def set_bin_factor(self, value):
        previous_bin_factor = self.bin_factor
        previous_width = self.width
        previous_height = self.height
        self.set_attr("BinningX", value)
        self.set_attr("BinningY", value)
        # Adjust width and height, so the portion of the image read is
        # independent of bin factor.
        # (This happens automatically when increasing the bin factor, bot does
        # not when decreasing the bin factor.)
        if self.bin_factor < previous_bin_factor:
            scale = float(previous_bin_factor) / self.bin_factor
            self.width = previous_width * scale
            self.height = previous_height * scale

    bin_factor = property(get_bin_factor, set_bin_factor)

    def get_pixel_format(self):
        """Format name as string, e.g. "Bayer8","Rgb24"
        Last buffered image in local memory might be
        different. See 'image_pixel_format'"""
        return str(self.get_attr("PixelFormat", "Bayer8"))

    def set_pixel_format(self, value):
        self.set_attr("PixelFormat", value)

    pixel_format = property(get_pixel_format, set_pixel_format)

    def get_image_pixel_format(self):
        """Format (RGB,mono,YUV,Bayer) and number of bits per pixel for
        last acquired image stored in local memory.
        Camera might be currently setup to send images in a different format.
        See 'pixel_format'.
        Returns '' if no image was acquired so far"""
        frame = self.Frames[self.current_buffer()].frame
        if frame.FrameCount > 0:
            return self.pixel_format_name(frame.Format)
        else:
            return ""

    image_pixel_format = property(get_image_pixel_format)

    def pixel_format_name(self, pixel_format_code):
        """Readable form of GigE Vision image format number"""
        if pixel_format_code in self.pixel_format_names:
            name = self.pixel_format_names[pixel_format_code]
        else:
            name = "pixel type %d" % pixel_format_code
        return name

    @property
    def pixel_formats(self):
        return list(self.pixel_format_names.values())

    pixel_format_names = {
        0: "Mono8",
        1: "Mono16",
        2: "Bayer8",
        3: "Bayer16",
        4: "Rgb24",
        5: "Rgb48",
        6: "Yuv411",
        7: "Yuv422",
        8: "Yuv444",
        9: "Bgr24",
        10: "Rgba32",
        11: "Bgra32"
    }

    def frame_timestamp(self, i):
        """i =0,1. Returns a camera generated time stamp of an image
        in units of s"""
        lo = self.Frames[i].frame.TimestampLo
        hi = self.Frames[i].frame.TimestampHi
        count = (hi << 32) + lo
        # Timestamp frequency: 36,858,974 Hz for firmware 1.36.0
        # Starting from firmware 1.50.1 the timestamp in units of nanoseconds.
        # Is there a resource to read to get the timestamp clock frequency?
        dt = 1 / 36858974. if self.firmware_version < 1.50 else 1e-9
        t = count * dt
        return t

    @cached
    @property
    def firmware_version(self):
        """As floating point number in the format ii.jj,
        where ii is the major and jj is the minor version number"""
        from numpy import nan
        i = self.get_attr("FirmwareVerMajor", nan)
        j = self.get_attr("FirmwareVerMinor", nan)
        version = i + j * 0.01
        return version

    @property
    def timestamp(self):
        """Camera-generated time stamp of current image in seconds"""
        if not self.has_image:
            return 0.0
        return self.frame_timestamp(self.current_buffer())

    def calculate_framerate(self):
        """Calculate the image acquisition frequency in Hz and store it
        in the member variable 'framerate'"""
        # The "StatFrameRate" attribute always reads 0.0.
        # Called periodically from "resume".
        from numpy import argsort, array as a, nan
        if len(self.Frames) < 2:
            return nan
        # Find the last two image based on their frame count.
        counts = a([self.Frames[i].frame.FrameCount for i in range(0, len(self.Frames))])
        times = a([self.frame_timestamp(i) for i in range(0, len(self.Frames))])
        order = argsort(counts)
        count1, count2 = counts[order][-2:]
        time1, time2 = times[order][-2:]
        if count1 == 0 or count2 == 0:
            return nan  # not enough valid images.
        # Calculate the frame rate based on the last two images.
        if time2 == time1:
            return nan
        self.framerate = (count2 - count1) / (time2 - time1)

    def get_frame_count(self):
        """Camera-generated serial number the last acquired image in local
        memory which is transferred completely
        The first image acquired has a frame count of one.
        A return value of zero indicates that no images have been acquired
        so far."""
        self.resume_auto()
        return int(self.current_frame_count)

    frame_count = property(get_frame_count)

    def get_internal_frame_count(self):
        # frame count for internal usage
        counts = []
        for i in range(0, len(self.Frames)):
            if self.Frames[i].frame.Status == 0:
                counts += [self.Frames[i].frame.FrameCount]
        if len(counts) == 0:
            return 0
        return max(counts)

    current_frame_count = property(get_internal_frame_count)

    def get_exposure_time(self):
        """Current electronic shutter time (in both manual and automatic mode)
        The minimum value is 10 us, the maximum 60 s."""
        # The attribute ExposureValue is in units of microseconds.
        try:
            return self.get_attr("ExposureValue", 0) * 1e-6
        except TypeError:
            return 0.0

    def set_exposure_time(self, value):
        """Sets 'ExposureMode' to 'Manual' and changes electronic shutter time ."""
        # Also, make sure 'ExposureMode' is set to 'Manual', otherwise
        # the attribute 'ExposureValue' would not be changeable.
        self.set_attr("ExposureMode", "Manual")
        # The attribute ExposureValue is in units of microseconds.
        self.set_attr("ExposureValue", round(value * 1e6))

    exposure_time = property(get_exposure_time, set_exposure_time)

    def get_auto_exposure(self):
        """If True the camera dynamically adjusts its integration time"""
        if self.get_attr("ExposureMode", "") == "Auto":
            return True
        else:
            return False

    def set_auto_exposure(self, auto_exposure):
        if auto_exposure:
            self.set_attr("ExposureMode", "Auto")
        else:
            self.set_attr("ExposureMode", "Manual")

    auto_exposure = property(get_auto_exposure, set_auto_exposure)

    def current_buffer(self):
        """The index of the buffer that contains the last acquired complete image
        """
        # In order for an to be completely transferred its "Status" field must
        # be zero.
        current_frame_count = self.current_frame_count
        if current_frame_count == 0:
            return 0
        for i in range(0, len(self.Frames)):
            if self.Frames[i].frame.FrameCount != current_frame_count:
                continue
            if self.Frames[i].frame.Status != 0:
                continue
            return i
        return 0

    @property
    def has_image(self):
        """Is there currently a valid image?"""
        # In order for one image to be complete the frame count in both
        # buffers must be > 1.
        self.resume_auto()
        if self.current_frame_count == 0:
            return False
        if self.image_pixel_format not in ["Bayer8", "Rgb24"]:
            return False
        return True

    def get_center(self):
        """For displaying crosshairs on the image.
        In order for the crosshairs to be shared among viewers running on
        different machines, its coordinates are stored inside the camera
        itself. There is are no unused or general purpose variables that
        could be used for this purpose. However, the upper limits for the 'DSP
        Subregion' (2^32-1 pixels) are much larger that the actual chip size
        (1360x1024). Thus any value written to the variables larger than 1359
        will no change the effective subregion used for automatic exposure and
        automatic white balance.
        """
        self.resume_auto()
        val1 = self.get_attr("DSPSubregionRight")
        val2 = self.get_attr("DSPSubregionBottom")
        if val1 is None or val1 is None:
            return None
        max_val = 2 ** 32 - 1
        x = int(max_val - val1)
        y = int(max_val - val2)
        if x == 0 and y == 0:
            return None
        return x, y

    def set_center(self, center):
        """For displaying crosshairs on the image. 'Center' is an (x,y) tuple.
        """
        if center is None:
            return
        x = center[0]
        y = center[1]
        max_val = 2 ** 32 - 1
        self.set_attr("DSPSubregionRight", max_val - x)
        self.set_attr("DSPSubregionBottom", max_val - y)
        self.save_parameters()

    center = property(get_center, set_center)

    @property
    def stream_bytes_per_second(self):
        """Maximum transmission rate in Bytes/s"""
        return self.get_attr("StreamBytesPerSecond", 0)

    @stream_bytes_per_second.setter
    def stream_bytes_per_second(self, value):
        self.set_attr("StreamBytesPerSecond", value)

    def get_trigger_mode(self):
        """Possible values: "Freerun", "SyncIn1", "SyncIn2", "FixedRate",
        "Software" """
        return self.get_attr("FrameStartTriggerMode", "")

    def set_trigger_mode(self, value):
        self.set_attr("FrameStartTriggerMode", value)

    trigger_mode = property(get_trigger_mode, set_trigger_mode)

    def get_external_trigger(self):
        """Is external trigger enabled?"""
        mode = self.trigger_mode
        if mode is None:
            return False
        return "SyncIn" in mode

    def set_external_trigger(self, value):
        if value:
            self.trigger_mode = "SyncIn2"
        else:
            self.trigger_mode = "Freerun"

    external_trigger = property(get_external_trigger, set_external_trigger)

    def get_gain(self):
        """Defines the dynamic range, 0 = max. range, 22 = min. range"""
        return self.get_attr("GainValue", 0)

    def set_gain(self, value):
        self.set_attr("GainValue", value)

    gain = property(get_gain, set_gain)

    def get_attr(self, name, default_value=None):
        """Queries a camera attribute.
        Attributes are named variables inside the GigE camera, used to control
        and monitor it.
        name: string
        Return value: Can be of type int,float or string.
            None if the attribute is not readable
        """
        from ctypes import byref, c_uint32, c_float
        c_name = name.encode("utf-8")
        # from ctypes import c_char_p; c_name = c_char_p(c_name)
        self.init("read-only")
        if self.handle.value is None:
            return default_value
        info = tPvAttributeInfo()
        status = self.PvAPI.PvAttrInfo(self.handle, c_name, byref(info))
        if status != 0:
            return default_value
        if info.Datatype == ePvDatatypeUint32:
            c_value = c_uint32()
            status = self.PvAPI.PvAttrUint32Get(self.handle, c_name, byref(c_value))
            if status != 0:
                return default_value
            value = c_value.value
            return value
        if info.Datatype == ePvDatatypeFloat32:
            c_value = c_float()
            status = self.PvAPI.PvAttrFloat32Get(self.handle, c_name, byref(c_value))
            if status != 0:
                return default_value
            value = c_value.value
            return value
        if info.Datatype == ePvDatatypeEnum:
            c_value = b'\0' * 81
            status = self.PvAPI.PvAttrEnumGet(self.handle, c_name, c_value, 80, None)
            if status != 0:
                return default_value
            c_value = c_value.strip(b'\0')
            value = c_value.decode("latin-1")
            return value
        if info.Datatype == ePvDatatypeString:
            c_value = b'\0' * 81
            status = self.PvAPI.PvAttrStringGet(self.handle, c_name, c_value, 80, None)
            if status != 0:
                return default_value
            c_value = c_value.strip(b'\0')
            value = c_value.decode("latin-1")
            return value
        return default_value

    def set_attr(self, name, value):
        """Modifies a camera attribute.
        name: string
        value: can be of type int,float or string.
        """
        from ctypes import byref, c_uint32, c_float
        c_name = name.encode("utf-8")
        # from ctypes import c_char_p; c_name = c_char_p(c_name)
        self.init("control")
        if self.handle.value is None:
            return
        if self.mode != "control":
            return

        info = tPvAttributeInfo()
        status = self.PvAPI.PvAttrInfo(self.handle, c_name, byref(info))
        if status != 0:
            self.last_error = name + ": " + error_message(status)
            warning("self.PvAPI.PvAttrInfo: %r: %r" % (name, self.last_error))
        if info.Datatype == ePvDatatypeUint32:
            value = int(round(float(value)))
            v_min = c_uint32()
            v_max = c_uint32()
            status = self.PvAPI.PvAttrRangeUint32(self.handle, c_name, byref(v_min),
                                                  byref(v_max))
            if status == 0:
                if value < v_min.value:
                    value = v_min.value
                if value > v_max.value:
                    value = v_max.value
            status = self.PvAPI.PvAttrUint32Set(self.handle, c_name, value)
        elif info.Datatype == ePvDatatypeFloat32:
            value = float(value)
            v_min = c_float()
            v_max = c_float()
            status = self.PvAPI.PvAttrRangeFloat32(self.handle, c_name, byref(v_min),
                                                   byref(v_max))
            if status == 0:
                if value < v_min.value:
                    value = v_min.value
                if value > v_max.value:
                    value = v_max.value
            status = self.PvAPI.PvAttrFloat32Set(self.handle, c_name, value)
        elif info.Datatype == ePvDatatypeEnum:
            value = str(value)
            c_value = value.encode("utf-8")
            status = self.PvAPI.PvAttrEnumSet(self.handle, c_name, c_value)
        elif info.Datatype == ePvDatatypeString:
            value = str(value)
            c_value = value.encode("utf-8")
            status = self.PvAPI.PvAttrStringSet(self.handle, c_name, c_value)
        else:
            return
        if status != 0:
            self.last_error = name + ": " + error_message(status)
            # warning("self.PvAPI.PvAttrStringSet: %r: %r" % (name,self.last_error)
        else:
            self.last_error = ""

    def command(self, name):
        """Execute a named command inside the camera
        name: string"""
        self.init("control")
        if self.handle.value and self.mode == "control":
            c_name = name.encode("utf-8")
            status = self.PvAPI.PvCommandRun(self.handle, c_name)
        else:
            status = 20  # forbidden
        if status != 0:
            self.last_error = "Run Command %r: %s" % (name, error_message(status))
            warning("self.PvAPI.PvCommandRun: %r: %r" % (name, self.last_error))
        else:
            self.last_error = ""
        return status

    def save_parameters(self):
        """Writes current settings to non-volatile memory as default
        configuration to be loaded at power up."""
        self.set_attr("ConfigFileIndex", 1)
        self.set_attr("ConfigFilePowerUp", 1)
        self.command("ConfigFileSave")

    def get_buffer_status(self):
        """[for debugging] list which image buffers are in use and what their
        their frame number s and timestamps are"""
        status = ""
        for i in range(0, len(self.Frames)):
            status += "[%d] " % i
            if self.Frames[i].frame.FrameCount:
                status += "#%02d " % self.Frames[i].frame.FrameCount
            else:
                status += " -  "
            if self.Frames[i].frame.Status == 99:
                status += " - "
            elif self.Frames[i].frame.Status == 0:
                status += "OK "
            else:
                status += "%2.2d " % self.Frames[i].frame.Status
            if self.frame_timestamp(i):
                status += "%11.3fs " % self.frame_timestamp(i)
            else:
                status += "      -      "
        return status[:-1]

    buffer_status = property(get_buffer_status)

    @property
    def PvAPI(self):
        self.initialize_PvAPI()
        return self._PvAPI

    _PvAPI = None

    @classmethod
    def initialize_PvAPI(cls):
        if cls._PvAPI is None:
            debug("Loading PvAPI library...")
            # Try to load any of the libraries found, until successful.
            for filename in cls.library_pathnames():
                debug("Loading %r..." % filename)
                try:
                    cls._PvAPI = cls.LoadLibrary(filename)
                except Exception:
                    continue
                # debug("PvAPI library loaded: %r" % filename)
                break
        if cls._PvAPI is None:
            # Report which files was tried, but were not usable and why.
            message = "None of the following PvAPI was usable:\n"
            for filename in cls.library_pathnames():
                try:
                    cls.LoadLibrary(filename)
                    exception = "OK"
                except Exception as exception:
                    pass
                message += "%s: %s\n" % (filename, exception)
            message.rstrip("\n")
            raise RuntimeError(message)
        if not hasattr(cls._PvAPI, "initialized"):
            debug("Initializing PvAPI library...")
            status = cls._PvAPI.PvInitialize()
            if status != 0:
                raise RuntimeError("PvInitialize: " + error_message(status))
            cls._PvAPI.initialized = True
        return cls._PvAPI

    @staticmethod
    def LoadLibrary(filename):
        import os
        import ctypes
        if os.name == 'nt':
            LoadLibrary = ctypes.windll.LoadLibrary
        else:
            LoadLibrary = ctypes.cdll.LoadLibrary
        return LoadLibrary(filename)

    @staticmethod
    def library_pathnames():
        """location of the dynamic library as list of pathnames"""
        from sys import path
        from platform import system
        from glob import glob

        if "." not in path:
            path += ["."]

        if system() == "Darwin":
            filename = "libPvAPI*.dylib"
        elif system() == "Linux":
            filename = "libPvAPI*.so"
        elif system() == "Windows":
            filename = "PvAPI*.dll"
        else:
            filename = "libPvAPI*.so"

        pathnames = []
        for directory in path:
            for pathname in glob(directory + "/" + filename):
                if pathname not in pathnames:
                    pathnames += [pathname]
        if not pathnames:
            raise RuntimeError("Library %r not found in %r" % (filename, path))
        return pathnames

    def handle_valid(self, handle):
        """Does this handle refer to a connection that is alive?"""
        from ctypes import c_int32, byref
        if handle.value is None:
            return False

        is_started = c_int32()
        status = self.PvAPI.PvCaptureQuery(handle, byref(is_started))
        if status == 0:
            return True
        else:
            return False

    def monitor(self, property_name, procedure, *args, **kwargs):
        warnings.warn("monitor() is deprecated, use __getattr_monitors__().add",
                      DeprecationWarning, stacklevel=2)
        if "new_thread" not in kwargs:
            kwargs["new_thread"] = False
        from handler import handler
        handler = handler(procedure, *args, **kwargs)
        self.__getattr_monitors__(property_name).add(handler)

    def add_handler(self, property_name, procedure, *args, **kwargs):
        warnings.warn("add_handler() is deprecated, use __getattr_monitors__().add",
                      DeprecationWarning, stacklevel=2)
        if "new_thread" not in kwargs:
            kwargs["new_thread"] = False
        from handler import handler
        handler = handler(procedure, *args, **kwargs)
        self.__getattr_monitors__(property_name).add(handler)

    def monitor_clear(self, property_name, procedure, *args, **kwargs):
        warnings.warn("monitor_clear() is deprecated, use __getattr_monitors__().remove",
                      DeprecationWarning, stacklevel=2)
        if "new_thread" not in kwargs:
            kwargs["new_thread"] = False
        from handler import handler
        handler = handler(procedure, *args, **kwargs)
        self.__getattr_monitors__(property_name).remove(handler)

    def monitors(self, property_name):
        warnings.warn("monitors() is deprecated, __getattr_monitors__()",
                      DeprecationWarning, stacklevel=2)
        return self.__getattr_monitors__(property_name)


def error_message(status):
    """Readable error message from PvAPI call return status"""
    messages = {
        0: "no error",
        1: "unexpected camera fault",
        2: "unexpected fault in PvApi or driver",
        3: "camera handle is invalid",
        4: "bad parameter to API call",
        5: "sequence of API calls is incorrect",
        6: "camera or attribute not found",
        7: "camera cannot be opened in the specified mode",
        8: "camera was unplugged",
        9: "setup is invalid (an attribute is invalid)",
        10: "system/network resources or memory not available",
        11: "1394 bandwidth not available",
        12: "too many frames on queue",
        13: "frame buffer is too small",
        14: "frame cancelled by user",
        15: "the data for the frame was lost",
        16: "some data in the frame is missing",
        17: "timeout during wait",
        18: "attribute value is out of the expected range",
        19: "attribute is not this type (wrong access function)",
        20: "attribute write forbidden at this time",
        21: "attribute is not available at this time",
        22: "a firewall is blocking the traffic"
    }
    message = messages.get(status, f"unknown error ({status})")
    return message


# Attribute data types
ePvDatatypeUnknown = 0
ePvDatatypeCommand = 1
ePvDatatypeRaw = 2
ePvDatatypeString = 3
ePvDatatypeEnum = 4
ePvDatatypeUint32 = 5
ePvDatatypeFloat32 = 6


class tPvAttributeInfo(Structure):
    from ctypes import c_int32, c_char_p
    _fields_ = [
        ("Datatype", c_int32),
        ("Flags", c_int32),
        ("Category", c_char_p),
        ("Impact", c_char_p),
        ("_reserved", c_int32 * 4)
    ]


class tPvFrame(Structure):
    from ctypes import c_ulong, c_void_p, c_char_p

    _fields_ = [
        ("ImageBuffer", c_char_p),  # Your image buffer (was: c_void_p)
        ("ImageBufferSize", c_ulong),  # Size of your image buffer in bytes
        ("AncillaryBuffer", c_void_p),  # Your buffer to capture associated
        #   header & trailer data for this image.
        ("AncillaryBufferSize", c_ulong),  # Size of your ancillary buffer in bytes
        #   (can be 0 for no buffer).
        ("Context", c_void_p * 4),  # For your use (valuable for your
        # frame-done callback).
        ("_reserved1", c_ulong * 8),
        ("Status", c_ulong),  # Status of this frame
        ("ImageSize", c_ulong),  # Image size, in bytes
        ("AncillarySize", c_ulong),  # Ancillary data size, in bytes
        ("Width", c_ulong),  # Image width
        ("Height", c_ulong),  # Image height
        ("RegionX", c_ulong),  # Start of readout region (left)
        ("RegionY", c_ulong),  # Start of readout region (top)
        ("Format", c_ulong),  # Image format
        ("BitDepth", c_ulong),  # Number of significant bits
        ("BayerPattern", c_ulong),  # Bayer pattern, if bayer format
        ("FrameCount", c_ulong),  # Rolling frame counter
        ("TimestampLo", c_ulong),  # Time stamp, lower 32-bits
        ("TimestampHi", c_ulong),  # Time stamp, upper 32-bits
        ("_reserved2", c_ulong * 32),
    ]


def sleep(seconds):
    """Return after for the specified number of seconds"""
    # After load and initializing the PvAPI Python's built-in 'sleep' function
    # stops working (returns too early). The is a replacement.
    from time import sleep, time
    t = t0 = time()
    while t < t0 + seconds:
        sleep(t0 + seconds - t)
        t = time()


def nanmax(a):
    from numpy import max, nan, isnan, any, asarray
    a = asarray(a)
    try:
        valid = ~isnan(a)
        return max(a[valid]) if any(valid) else nan
    except (ValueError, TypeError, IndexError, ArithmeticError):
        return nan


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")
    camera = GigE_camera("MicroscopeCamera")
    self = camera
    print("self.IP_addr = %r" % camera.IP_addr)
    print("self.acquiring = True")
    print("self.state")
    print("")


    def report(obj, name): info(f'{obj}.{name} = {getattr(obj, name)}')


    print("from monitor import monitor; monitor(self,'acquiring',report,self,'acquiring')")
    print("from monitor import monitors; monitors(self,'acquiring')")
    print("from monitor import monitor_clear; monitor_clear(self,'acquiring',report,self,'acquiring')")
