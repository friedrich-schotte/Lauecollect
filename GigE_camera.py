#!/usr/bin/env python
"""
Driver for Prosilica GigE CCD cameras.
Author: Friedrich Schotte
Date created: 2010-10-16
Date last modified: 2018-10-30
"""
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

import ctypes

__version__ = "2.4" # Frame, queued_time

class GigE_camera(object):
    default_width = 1360
    default_height = 1024
    reception_timeout = 10.0
    
    def __init__(self,IP_addr="",use_multicast=True,auto_resume=True):
        """If IP_addr is omitted the first detected GigE camera in the local
        network is used.
        If use_multicast is True the other viewer can watch the same video stream 
        simulataneously.
        If False on this connection can receive live video. 
        Under Linux, python must by run with 'sudo' for Multicast to work.
        """
        from ctypes import c_void_p
        from numpy import nan
        self.IP_addr = IP_addr
        self.use_multicast = use_multicast
        self.auto_resume = auto_resume
        self.handle = c_void_p()
        self.last_error = ""
        self.mode = "not connected"
        self.acquisition_started = False
        self.capturing_images = True
        self.Frames = [self.Frame() for i in range(0,2)]
        # Mark all frames as been not "valid" (Status = 0).
        for i in range(0,len(self.Frames)): self.Frames[i].frame.Status = 99
        self.framerate = nan

    class Frame(object):
        def __init__(self):
            self.frame = tPvFrame()
            self.buffer = ""
            self.queued_time = 0

        @property
        def reception_pending_time(self):
            from time import time
            from numpy import nan
            if self.reception_pending:
                value = time() - self.reception_started_time
            else: value = nan
            return value

        @property
        def reception_pending(self):
            value = self.reception_started and not self.reception_finished
            return value

        @property
        def reception_started(self):
            ImageBuffer = self.frame.ImageBuffer
            value = ImageBuffer and len(ImageBuffer)>=2 and \
                ImageBuffer[0:2] != "\xFE\xFE"
            return value

        @property
        def reception_finished(self):
            ImageBuffer = self.frame.ImageBuffer
            value = ImageBuffer and len(ImageBuffer)>=2 and \
                ImageBuffer[-2:] != "\xFE\xFE"
            return value

        def get_reception_started_time(self):
            from numpy import nan,isnan
            value = getattr(self,"__reception_started_time__",nan)
            if isnan(value) and self.reception_started:
                from time import time
                value = time()
                self.set_reception_started_time(value)
            return value
        def set_reception_started_time(self,value):
            setattr(self,"__reception_started_time__",value)
        reception_started_time = property(get_reception_started_time,set_reception_started_time)

    def init(self,mode="control"):
        from socket import gethostbyname,inet_aton
        from struct import unpack
        from ctypes import c_void_p,byref

        # Is the current handle valid and is the current mode the right mode?
        if handle_valid(self.handle):
            if self.mode == mode: return # nothing to do
            if self.mode == "control": return # control is good for read-only too

        # Even for handles no longer valid 'PvCameraClose' should be called.
        if self.handle: PvAPI.PvCameraClose (self.handle)
        self.handle.value = None
        self.mode = "not connected"
        self.last_error = ""

        self.mode = mode
        dot_addr = gethostbyname(self.IP_addr)
        int_addr, = unpack("I",inet_aton(dot_addr))
        access = 4 if mode == "control" else 2 
        status = PvAPI.PvCameraOpenByAddr (int_addr,access,byref(self.handle))
        # If failed to connect as 'master', try as 'monitor'.
        ##print "init, first attempt: mode %r, status %r" % (mode,status)
        if mode == "control" and status == 7: # 7:cannot be opened in the specified mode
            self.mode = "read-only"
            status = PvAPI.PvCameraOpenByAddr (int_addr,2,byref(self.handle))
        if status != 0:
            self.mode = "not connected"
            self.last_error = "not connected: "+error(status)
        
    def start(self):
        """Starts video streaming."""
        from ctypes import byref,c_char,c_char_p,addressof
        
        if self.capturing: return # already started
        self.init("control")
        if self.handle.value == None: return # camera unusable

        # Enable multicast mode so the connection can be shared by other viewers.
        # It is the responibility of the first view conntecting to request
        # multicast. If the first viewer connects without it, no other viewer
        # can access the video stream while the first one is connected.
        if self.use_multicast and self.mode == "control":
            self.set_attr("MulticastEnable","On")

        # Allocate two frame buffers.
        frame_size = self.get_attr("TotalBytesPerFrame")
        for i in range(0,len(self.Frames)):
            self.Frames[i].buffer = (c_char*frame_size)()
            self.Frames[i].frame.ImageBuffer = c_char_p(addressof(self.Frames[i].buffer))
            self.Frames[i].frame.ImageBufferSize = frame_size

        # Initialize the image capture stream.
        status = PvAPI.PvCaptureStart(self.handle)
        if status != 0:
            self.last_error = "not capturing: "+error(status)
            return
        else: self.last_error = ""

        # Set the camera in acquisition mode.
        if self.mode == "control":
            # Make sure that the ethernet packet size is OK for a network
            # that does not support Jumbo frames. (Factory setting is 8228
            # bytes.)
            if self.get_attr("PacketSize") > 1500:
                self.set_attr("PacketSize",1500)
            # Set the bandwidth appropriately for 2 cameras sharing
            # one 100-Mb connection.
            #self.set_attr("StreamBytesPerSecond",5000000)
            status = PvAPI.PvCommandRun(self.handle,"AcquisitionStart")
            if status != 0:
                self.acquisition_started = False
                self.last_error = "not started: "+error(status)
                raise RuntimeError("AcquisitionStart: "+error(status))
            else: self.acquisition_started = True; self.last_error = ""

        # Start the capturing of the life video network packets sent by the
        # camera to be reassembled as images in local memory.
        # This is done in a background thread in the PvAPI library, started by
        # calling PvCaptureQueueFrame.
        
        for i in range(0,len(self.Frames)):
            # Mark frame buffer as "not containg a valid image".
            self.Frames[i].frame.FrameCount = 0
            self.Frames[i].frame.TimestampHi = 0
            self.Frames[i].frame.TimestampLo = 0
            self.Frames[i].frame.Status = 99 # 0 Status indicates "frame complete".
            self.Frames[i].buffer[0:2] = "\xFE\xFE" # marker for testing
            self.Frames[i].buffer[-2:] = "\xFE\xFE" # marker for testing
            from time import time
            self.Frames[i].queued_time = time()
            from numpy import nan
            self.Frames[i].reception_started_time = nan
            status = PvAPI.PvCaptureQueueFrame(self.handle,
                byref(self.Frames[i].frame),None)
            if status != 0:
                raise RuntimeError("PvCaptureQueueFrame: "+error(status))
        # "PvCaptureQueueFrame" acquires only a single image.
        # After this need to periodcally call "resume" to put back the
        # image buffers into the capture queue.
        self.capturing_images = True

    @property
    def reception_timed_out(self):
        return self.reception_pending_time > self.reception_timeout

    @property
    def reception_pending_time(self):
        return nanmax([Frame.reception_pending_time for Frame in self.Frames])

    def resume(self):
        """To be called periodically when captuting images"""
        if self.reception_timed_out: self.stop(); self.start()
        # Image stream stops at image #65535
        if self.current_frame_count >= 65000: self.stop(); self.start()
        
        self.calculate_framerate()
        from ctypes import byref
        if not self.capturing_images: return
        # Find buffers with images that were completed, except the current
        # frame, and put them back into the queue of capture buffers.
        current_frame_count = self.current_frame_count
        for i in range(0,len(self.Frames)):
            # Do not overwrite the last acquired image.
            if self.Frames[i].frame.FrameCount == current_frame_count: continue
            # Do not re-enqueue a buffer already in the queue.
            if self.Frames[i].frame.FrameCount == 0: continue
            if self.Frames[i].frame.Status == 99: continue
            # Mark frame buffer as "not containg a valid image".
            self.Frames[i].frame.FrameCount = 0
            self.Frames[i].frame.TimestampHi = 0
            self.Frames[i].frame.TimestampLo = 0
            self.Frames[i].frame.Status = 99 # 0 Status 0 indicates "frame complete".
            self.Frames[i].buffer[0:2] = "\xFE\xFE" # marker for testing
            self.Frames[i].buffer[-2:] = "\xFE\xFE" # marker for testing
            from time import time
            self.Frames[i].queued_time = time()
            from numpy import nan
            self.Frames[i].reception_started_time = nan
            status = PvAPI.PvCaptureQueueFrame(self.handle,
                byref(self.Frames[i].frame),None)
            if status != 0:
                raise RuntimeError("PvCaptureQueueFrame: "+error(status))
         
    def stop(self):
        """This is to disconnect for the camera and leave the Prosilica
        Video Libary in an orderly state"""
        self.capturing_images = False
        self.acquisition_started = False
        if self.handle.value != None:
            PvAPI.PvCommandRun (self.handle,"AcquisitionStop")
            PvAPI.PvCaptureEnd (self.handle)
            PvAPI.PvCaptureQueueClear (self.handle)
            PvAPI.PvCameraClose (self.handle)
        self.handle.value = None

    def get_capturing(self):
        """Has the image capture stream been started?
        That is, has PvCaptureStart been called successfully?"""
        from ctypes import c_uint32,byref
        if self.handle == None: return False
        is_started = c_uint32()
        status = PvAPI.PvCaptureQuery (self.handle,byref(is_started))
        if status != 0: return False
        return (is_started.value != 0)
    capturing = property(get_capturing)

    def get_state(self):
        if self.auto_resume: self.resume()
        if not handle_valid(self.handle): state = "not connected"
        else:
            state = self.mode
            if self.get_attr("MulticastEnable") == "On": state += ", multicast"
            capturing = self.capturing
            if capturing:
                state += ", capturing"
                if self.external_trigger: state += " (ext. trig.)"
            if self.reception_pending_time > 0:
                state += ", pending %.1f s" % self.reception_pending_time
            elif self.acquisition_started: state += ", started"
            if capturing and self.current_frame_count > 0:
                state += (", %.3g fps" % self.framerate)
                state += (", #%d" % self.current_frame_count)
            state += ", "+self.pixel_format
            if not self.pixel_format in ["Bayer8","Rgb24"]:
                state += ", unsupported format"
            error_codes = []
            for Frame in self.Frames:
                if Frame.frame.Status not in [0,99]:
                    if Frame.frame.Status not in error_codes:
                        error_codes+=[Frame.frame.Status]
            for error_code in error_codes: state += ", "+error(error_code)
        if self.last_error: state += ", "+self.last_error
        return state
    state = property (fget=get_state,doc="connection info")

    def get_rgb_array(self):
        """Last read image as 3D nmupy array. Dimensions: 3xWxH
        datatype: uint8
        Usage R,G,B = camera.rgb_array"""
        from numpy import frombuffer,uint8
        w,h = self.width,self.height
        return frombuffer(self.rgb_data,uint8).reshape(h,w,3).T
    rgb_array = RGB_array = property(get_rgb_array)

    def get_rgb_data(self):
        """All this pixels of the last read image as one single chunk
        of contiguous data.
        The format is one byte per pixel, in the order R,G,B, by scan line,
        top left to bottom right.
        'PixelFormat' attribute of the camera needs to be set to 'Bayer8'
        or 'Rgb24'.
        """
        if self.auto_resume: self.resume()
        if not self.has_image: return self.default_rgb_data()
        if self.image_pixel_format == "Rgb24": return self.get_image_data()
        elif self.image_pixel_format == "Bayer8": return self.rgb_from_bayer8()
        else: return ""
    rgb_data = property(get_rgb_data)

    def default_rgb_data(self):
        """ This is used in case RGB data is requested but no image is
        available yet. Returns a black image of appropriate size
        (CCD chip size with binning and ROI applied)."""
        rgb_size = self.width*self.height*3
        return "\0"*rgb_size

    def get_image_data(self):
        """Returns all this pixels of the last read image as one single chunk
        of contiguous data."""
        from ctypes import string_at
        frame = self.Frames[self.current_buffer()].frame
        buffer = self.Frames[self.current_buffer()].buffer
        if frame.ImageBufferSize == 0: return ""
        return string_at(buffer,frame.ImageBufferSize)
    
    def rgb_from_bayer8 (self):
        "Assuming BayerPattern = 0:  first line RGRG, second line GBGB..."
        from ctypes import addressof,byref,c_char,c_char_p,string_at
        frame = self.Frames[self.current_buffer()].frame
        RGB_size = frame.ImageBufferSize*3
        RGB = (c_char*RGB_size)()
        addr = addressof(RGB)
        R,G,B = c_char_p(addr),c_char_p(addr+1),c_char_p(addr+2)
        PvAPI.PvUtilityColorInterpolate(byref(frame),R,G,B,2,0)
        return string_at(RGB,RGB_size)
        # PvUtilityColorInterpolate converts 8-bit Bayer mosaic images into
        # RGB24 images. The first parameter is the input frame data structure,
        # the following three parameter are the strating addresses for the
        # output R,G and B value respectively. The number 2 is the number of
        # bytes to skip between subsequent of R values (same for G and B),
        # and the last parameter is the number of bytes the skip and the end
        # is a scan line as padding.
        # Although RGB data is continguous in memory, Prosilica requires to
        # pass three pointers for the same chunck of memory.
        # This gives the function the flexibility to also generate BRG images.
        # The number of bytes between R values is also a parameter so the
        # function can generate also RGB32 or RGBA output (skipping 3 bytes)
        # or separate color planes (skpping 0 bytes).

    def save_image(self,filename):
        """Acquire a single image from the camera and save it as a file.
        filename: the exension determines the image format, may be '.jpg',
        '.png' or '.tif' or any other extensino supported by the Python Image
        Library (PIL)"""
        from PIL import Image
        image = Image.new('RGB',(self.width,self.height))
        image.fromstring(self.rgb_data)
        image.save(filename)

    def get_width(self):
        frame = self.Frames[self.current_buffer()].frame
        if frame.FrameCount > 0: width = frame.Width
        else: width = self.get_attr("Width")
        if width == 0 or width == None: width = self.default_width
        return width
    def set_width(self,value): self.set_attr("Width",value)
    width = property(get_width,set_width,doc="""number of columns in the image.
        If smaller that the chip width and bin factor = 1, a region of interest
        if read""")

    def get_height(self):
        frame = self.Frames[self.current_buffer()].frame
        if frame.FrameCount > 0: height = frame.Height
        else: height = self.get_attr("Height")
        if height == 0 or height == None: height = self.default_height
        return height
    def set_height(self,value): self.set_attr("Height",value)
    height = property(get_height,set_height,doc="""number of rows in the image.
        If smaller that the chip height and bin factor = 1, a region of interest
        if read""")

    def get_bin_factor(self):
        return max(self.get_attr("BinningX"),self.get_attr("BinningY"))
    def set_bin_factor(self,value):
        previous_bin_factor = self.bin_factor
        previous_width = self.width
        previous_height = self.height
        self.set_attr("BinningX",value)
        self.set_attr("BinningY",value)
        # Adjust width and height, so the portion of the image read is 
        # independent of bin factor.
        # (This happens atomatically when increasing the bin factor, bot does
        # not when decreasing the bin factor.)
        if self.bin_factor < previous_bin_factor:
            scale = float(previous_bin_factor) / self.bin_factor
            self.width  = previous_width  * scale
            self.height = previous_height * scale
    bin_factor = property(get_bin_factor,set_bin_factor,
        doc="common CCD row and column binning factor")

    def get_pixel_format(self):
        """Format (RGB,mono,YUV,Bayer) and number of bits per pixel as
        set up in the camera. Last buffered image in local memory might be
        different. See 'image_pixel_format'"""
        return str(self.get_attr("PixelFormat"))
    def set_pixel_format(self,value): self.set_attr("PixelFormat",value)
    pixel_format = property(get_pixel_format,set_pixel_format)

    def get_image_pixel_format(self):
        """Format (RGB,mono,YUV,Bayer) and number of bits per pixel for
        last acquired image stored in local memory.
        Camera might be currently setup to send images in a different format.
        See 'pixel_format'.
        Returns '' if no image was acquired so far"""
        frame = self.Frames[self.current_buffer()].frame
        if frame.FrameCount > 0: return self.pixel_format_name(frame.Format)
        else: return ""
    image_pixel_format = property(get_image_pixel_format)

    def pixel_format_name(self,pixel_format):
        "Translates GigE Vision image format numbers to a readable form"
        formats = {
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
        try: return formats[pixel_format]
        except: return "unknown pixel type (%d)" % format

    pixel_formats = ["Mono8","Bayer8","Bayer16","Rgb24","Rgb48","Yuv411",
            "Yuv422","Yuv444","Bgr24","Rgba32","Bgra32"]

    def frame_timestamp(self,i):
        """i =0,1. Returns a camera generated time stamp of an image
        in units of s"""
        lo = self.Frames[i].frame.TimestampLo
        hi = self.Frames[i].frame.TimestampHi
        count = (hi<<32)+lo
        # Timestamp frequency: 36,858,974 Hz for firmware 1.36.0
        # Starting from firmware 1.50.1 the timestamp in units of nanoseconds.
        # Is there a resource to read to get the timestamp clock frequency?
        dt = 1/36858974. if self.firmware_version < 1.50 else 1e-9
        t = count*dt
        return t

    @property
    def firmware_version(self):
        """As floating point number in the format ii.jj,
        where ii is the major and jj is the minor version number"""
        from numpy import nan
        if not hasattr(self,"__firmware_version__"):
            i = self.get_attr("FirmwareVerMajor")
            if i is None: return nan
            j = self.get_attr("FirmwareVerMinor")
            self.__firmware_version__ = i+j*0.01
        return self.__firmware_version__

    def get_timestamp(self):
        if not self.has_image: return 0.0
        return self.frame_timestamp(self.current_buffer())
    timestamp = property(get_timestamp,doc="""camera-generated
        time stamp of current image in seconds""")

    def calculate_framerate(self):
        """Calculate the image acquisition frequency in Hz and store it
        in the member variable 'framerate'"""
        # The "StatFrameRate" attribute always reads 0.0.
        # Called preiodically from "resume".
        from numpy import argsort,array as a,nan
        if len(self.Frames) < 2: return nan
        # Find the last two image based on their frame count.
        counts = a([self.Frames[i].frame.FrameCount for i in range(0,len(self.Frames))])
        times = a([self.frame_timestamp(i) for i in range(0,len(self.Frames))])
        order = argsort(counts)
        count1,count2 = counts[order][-2:]
        time1,time2 = times[order][-2:]
        if count1 == 0 or count2 == 0: return nan # not enough valid images.
        # Calculate the frame rate based on the last two images.
        if time2 == time1: return nan 
        self.framerate = (count2-count1)/(time2-time1)

    def get_frame_count(self):
        """Camera-generated serial number the last acquired image in local
        memory which is transferred completely
        The first image aquired has a frame count of one.
        A return value of zero indicates that no images have been acquired
        so far."""
        if self.auto_resume: self.resume()
        return self.current_frame_count
    frame_count = property(get_frame_count)

    def get_internal_frame_count(self):
        # frame count for internal usage
        counts = []
        for i in range(0,len(self.Frames)):
            if self.Frames[i].frame.Status == 0: counts += [self.Frames[i].frame.FrameCount]
        if len(counts) == 0: return 0
        return max(counts)
    current_frame_count = property(get_internal_frame_count)

    def get_exposure_time (self):
        "Current electronic shutter time (in both manual and automatic mode)"
        # The attribute ExposureValue is in units of microseconds.
        try: return self.get_attr("ExposureValue")*1e-6
        except TypeError: return 0.0
    def set_exposure_time (self,value):
        "Sets 'ExposureMode' to 'Manual' and changes electronic shutter time ."
        # Also, make sure 'ExposureMode' is set to 'Manual', otherwise
        # the attribute 'ExposureValue' would not be changable.
        self.set_attr("ExposureMode","Manual")
        # The attribute ExposureValue is in units of microseconds.
        self.set_attr("ExposureValue",round(value*1e6))
    exposure_time = property(get_exposure_time,set_exposure_time,
        doc="""Electronic shutter time (in both manual and automatic mode).
        If set, the exposure mode is set to 'Manual'.
        The minimum value is 10 us, the maximum 60 s.""")

    def get_auto_exposure(self):
        if self.get_attr("ExposureMode") == "Auto": return True
        else: return False
    def set_auto_exposure(self,value):
        if value == True: self.set_attr("ExposureMode","Auto")
        else: self.set_attr("ExposureMode","Manual")
    auto_exposure = property(get_auto_exposure,set_auto_exposure,
        doc="If True the camera dynamically adjusts its integration time")

    def current_buffer(self):
        """The index of the buffer that contains the last aquired complete image
        """
        # In order for an to be completely transfered its "Status" field must
        # be zero.
        current_frame_count = self.current_frame_count
        if current_frame_count == 0: return 0
        for i in range(0,len(self.Frames)):
            if self.Frames[i].frame.FrameCount != current_frame_count: continue
            if self.Frames[i].frame.Status != 0: continue
            return i
        return 0

    def get_has_image(self):
        # In order for one image to be complete the frame count in both
        # buffers must be > 1.
        if self.auto_resume: self.resume()
        if self.current_frame_count == 0: return False
        if not self.image_pixel_format in ["Bayer8","Rgb24"]: return False
        return True
    has_image = property(get_has_image,doc="Is there currently a valid image?")

    def get_center(self):
        """For displaying a crosshair on the image.
        In order for the crosshair to be shared among viewers running on
        different machines, its coordinates are stored inside the camera
        itself. There is are no unused or general purpose variables that
        could be used for this purpose. However, the upper limits for the 'DSP
        Subregion' (2^32-1 pixels) are much larger that the actual chip size
        (1360x1024). Thus any value written to the variables larger than 1359
        will no change the effective subregion used for automatic exposure and
        automatic white balance.
        """
        if self.auto_resume: self.resume()
        val1 = self.get_attr("DSPSubregionRight")
        val2 = self.get_attr("DSPSubregionBottom")
        if val1 == None or val1 == None: return None
        maxval = 2**32-1
        x = int(maxval - val1)
        y = int(maxval - val2)
        if x == 0 and y == 0: return None
        return x,y
    def set_center(self,center):
        """For displaying a crosshair on the image. 'Center' is an (x,y) tuple.
        """
        if center == None: return
        x = center[0]; y = center[1]
        maxval = 2**32-1
        self.set_attr("DSPSubregionRight",maxval-x)
        self.set_attr("DSPSubregionBottom",maxval-y)
        self.save_parameters()
    center = property (get_center,set_center,doc=
        "Crosshair position saved in non-volatile memory of camera")

    def get_stream_bytes_per_second (self):
        return self.get_attr("StreamBytesPerSecond")
    def set_stream_bytes_per_second (self,value):
        self.set_attr("StreamBytesPerSecond",value)
    stream_bytes_per_second = property(get_stream_bytes_per_second,
        set_stream_bytes_per_second,
        doc="Maximum transmission rate in Bytes/s")

    def get_trigger_mode(self):
        """Possible values: "Freerun", "SyncIn1", "SyncIn2", "FixedRate",
        "Software" """
        return self.get_attr("FrameStartTriggerMode")
    def set_trigger_mode(self,value): self.set_attr("FrameStartTriggerMode",value)
    trigger_mode = property(get_trigger_mode,set_trigger_mode)
 
    def get_external_trigger(self):
        "Is external trigger enabled?"
        mode = self.trigger_mode
        if mode == None: return False
        return ("SyncIn" in mode)
    def set_external_trigger(self,value):
        if value: self.trigger_mode = "SyncIn2"
        else: self.trigger_mode = "Freerun"
    external_trigger = property(get_external_trigger,set_external_trigger)

    def get_gain(self):
        "Defines the dynamic range, 0 = max. range, 22 = min. range"
        return self.get_attr("GainValue")
    def set_gain(self,value): self.set_attr("GainValue",value)
    gain = property(get_gain,set_gain)

    def get_attr(self,name):
        """Queries a camera attribute.
        Attributes are named variables inside the GigE camera, used to control
        and monitor it.
        The return value can be of type int,float or string.
        The return value is None is the attribute is not readable"""
        from ctypes import byref,c_uint32,c_float
        self.init("read-only")
        if self.handle.value == None: return None
        info = tPvAttributeInfo()
        status = PvAPI.PvAttrInfo (self.handle,name,byref(info))
        if status != 0: return None
        if info.Datatype == ePvDatatypeUint32:
            value = c_uint32()
            status = PvAPI.PvAttrUint32Get (self.handle,name,byref(value))
            if status != 0: return None
            return value.value
        if info.Datatype == ePvDatatypeFloat32:
            value = c_float()
            status = PvAPI.PvAttrFloat32Get (self.handle,name,byref(value))
            if status != 0: return None
            return value.value
        if info.Datatype == ePvDatatypeEnum:
            value = '\0'*81
            status = PvAPI.PvAttrEnumGet (self.handle,name,value,80,None)
            if status != 0: return None
            return value.strip('\0')
        if info.Datatype == ePvDatatypeString:
            value = '\0'*81
            status = PvAPI.PvAttrStringGet (self.handle,name,value,80,None)
            if status != 0: return None
            return value.strip('\0')

    def set_attr (self,name,value):
        """Modifies a camera attribute.
        value can be of type int,float or string."""
        from ctypes import byref,c_uint32,c_float
        self.init("control")
        if self.handle.value == None: return
        if self.mode != "control": return

        info = tPvAttributeInfo()
        status = PvAPI.PvAttrInfo (self.handle,name,byref(info))
        if status != 0:
             self.last_error = name+": "+error(status)
             print self.last_error
        if info.Datatype == ePvDatatypeUint32:
            value = int(round(float(value)))
            vmin = c_uint32(); vmax = c_uint32()
            status = PvAPI.PvAttrRangeUint32 (self.handle,name,byref(vmin),
                byref(vmax))
            if status == 0:
                if value < vmin.value: value = vmin.value
                if value > vmax.value: value = vmax.value
            status = PvAPI.PvAttrUint32Set (self.handle,name,value)
        elif info.Datatype == ePvDatatypeFloat32:
            value = float(value)
            vmin = c_float(); vmax = c_float()
            status = PvAttrRangeFloat32 (self.handle,name,byref(vmin),
                byref(vmax))
            if status == 0:
                if value < vmin.value: value = vmin.value
                if value > vmax.value: value = vmax.value
            status = PvAPI.PvAttrFloat32Set (self.handle,name,value)
        elif info.Datatype == ePvDatatypeEnum:
            status = PvAPI.PvAttrEnumSet (self.handle,name,str(value))
        elif info.Datatype == ePvDatatypeString:
            status = PvAPI.PvAttrStringSet (self.handle,name,str(value))
        else: return
        if status != 0:
             self.last_error = name+": "+error(status)
             ##print self.last_error
        else: self.last_error = ""

    def command (self,name):
        "Executes a named command inside the camera"
        self.init("control")
        if self.handle.value == None: return
        if self.mode != "control": return

        status = PvAPI.PvCommandRun (self.handle,name)
        if status != 0:
            self.last_error = "Run Command %r: %s" % (name,error(status))
            ##print self.last_error

    def save_parameters(self):
        """Writes current settings to non-volatile memory as default
        configuration to be loaded at power up."""
        self.set_attr("ConfigFileIndex",1)
        self.set_attr("ConfigFilePowerUp",1)
        self.command("ConfigFileSave")

    def get_buffer_status(self):
        """[for debugging] list which image buffers are in use and what their
        their frame number s and timestamps are"""
        status = ""
        for i in range(0,len(self.Frames)):
            status += "[%d] " % i
            if self.Frames[i].frame.FrameCount:
                status +=   "#%02d " % self.Frames[i].frame.FrameCount
            else: status += " -  "
            if self.Frames[i].frame.Status == 99: status += " - "
            elif self.Frames[i].frame.Status == 0: status += "OK "
            else: status += "%2.2d " % self.Frames[i].frame.Status
            if self.frame_timestamp(i):
                status += "%11.3fs " % self.frame_timestamp(i)
            else: status += "      -      "
        return status[:-1]
    buffer_status = property(get_buffer_status)


def initialize():
    load_library()
    if hasattr(PvAPI,"initialized"): return 
    status = PvAPI.PvInitialize()
    if status != 0: raise RuntimeError("PvInitialize: "+error(status))
    PvAPI.initialized = True

def load_library():
    global PvAPI
    import os,ctypes
    if os.name == 'nt': LoadLibrary = ctypes.windll.LoadLibrary
    else: LoadLibrary = ctypes.cdll.LoadLibrary
    # Try to load any of the libraries found, until sucessful.
    library_loaded = ""
    for filename in library_pathnames():
        try: PvAPI = LoadLibrary(filename)
        except: continue
        library_loaded = filename
        break
    ##print "PvAPI library loaded: %r" % library_loaded
    if not library_loaded:
        # Report which files was tried, but were not usable and why. 
        message = "None of the following PvAPI was usable:\n"
        for filename in library_pathnames():
            try: LoadLibrary(filename); exception = "OK"
            except Exception,exception: pass
            message += "%s: %s\n" % (filename,exception)
        message.rstrip("\n")
        raise RuntimeError(message)

def library_pathnames():
    """location of the dynamic library as lsit of pathnames"""
    from sys import path
    from os.path import exists
    from platform import system,machine
    from glob import glob

    if not "." in path: path += ["."]
    pathnames = []
    for directory in path:
        if system() == "Darwin": filename = "libPvAPI*.dylib"
        elif system() == "Linux": filename = "libPvAPI*.so"
        elif system() == "Windows": filename = "PvAPI*.dll"
        else: filename = "libPvAPI*.so"
        for pathname in glob(directory+"/"+filename):
            if not pathname in pathnames: pathnames += [pathname]
    if pathnames == []:
        raise RuntimeError("Library %r not found in %r" % (filename,path))
    return pathnames

def handle_valid(handle):
    "Does this handle refer to a connection that is alive?"
    from ctypes import c_int32,byref
    if handle.value == None: return False
    
    is_started = c_int32()
    status = PvAPI.PvCaptureQuery (handle,byref(is_started))
    if status == 0: return True
    else: return False


def error (status):
    "Readable error message from PvAPI call return status"
    msg = {
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
    try: return msg[status]
    except: return "unknown error (%d)" % status

# Attribute data types
ePvDatatypeUnknown  = 0
ePvDatatypeCommand  = 1
ePvDatatypeRaw      = 2
ePvDatatypeString   = 3
ePvDatatypeEnum     = 4
ePvDatatypeUint32   = 5
ePvDatatypeFloat32  = 6

from ctypes import Structure

class tPvAttributeInfo(Structure):
    from ctypes import c_int32,c_char_p
    _fields_ = [
         ("Datatype", c_int32),
         ("Flags", c_int32),
         ("Category", c_char_p),
         ("Impact", c_char_p),
         ("_reserved", c_int32*4)
    ]

class tPvFrame(Structure):
    from ctypes import c_ulong,c_void_p,c_char_p
    
    _fields_ = [
        ("ImageBuffer",c_char_p),        # Your image buffer (was: c_void_p)
        ("ImageBufferSize",c_ulong),     # Size of your image buffer in bytes
        ("AncillaryBuffer",c_void_p),    # Your buffer to capture associated 
                                         #   header & trailer data for this image.
        ("AncillaryBufferSize",c_ulong), # Size of your ancillary buffer in bytes
                                         #   (can be 0 for no buffer).
        ("Context",c_void_p*4),          # For your use (valuable for your
                                         # frame-done callback).
        ("_reserved1",c_ulong*8), 
        ("Status",c_ulong),              # Status of this frame
        ("ImageSize",c_ulong),           # Image size, in bytes
        ("AncillarySize",c_ulong),       # Ancillary data size, in bytes
        ("Width",c_ulong),               # Image width
        ("Height",c_ulong),              # Image height
        ("RegionX",c_ulong),             # Start of readout region (left)
        ("RegionY",c_ulong),             # Start of readout region (top)
        ("Format",c_ulong),              # Image format
        ("BitDepth",c_ulong),            # Number of significant bits
        ("BayerPattern",c_ulong),        # Bayer pattern, if bayer format
        ("FrameCount",c_ulong),          # Rolling frame counter
        ("TimestampLo",c_ulong),         # Time stamp, lower 32-bits
        ("TimestampHi",c_ulong),         # Time stamp, upper 32-bits
        ("_reserved2",c_ulong*32), 
    ]


def sleep(seconds):
    """Return after for the specified number of seconds"""
    # After load and initializing the PvAPI Python's built-in 'sleep' function
    # stops working (returns too early). The is a replacement.
    from time import sleep,time
    t = t0 = time()
    while t < t0+seconds: sleep(t0+seconds - t); t = time()

def nanmax(a):
    from numpy import max,nan,isnan,any,asarray
    a = asarray(a)
    try:
        valid = ~isnan(a)
        return max(a[valid]) if any(valid) else nan
    except: return nan


initialize()

def test():
    global camera,self,i
    
    camera = GigE_camera("id14b-prosilica4.cars.aps.anl.gov",
        use_multicast=False)
    self = camera # for debugging
    i = 0 # for debugging

    camera.start()    
    sleep(1)
    print camera.state  

def test_buffering():
    global camera,self,i
    
    camera = GigE_camera("id14b-prosilica4.cars.aps.anl.gov",
        use_multicast=False)
    self = camera # for debugging

    camera.start()    
    for i in range(0,20):
        print "%s" % (camera.buffer_status)
        camera.resume()
        sleep(0.1)
    print camera.state
    
    i = 0 # for debugging

def test_buffering_and_intensity():
    from numpy import average,sum
    global camera,self,i
    
    camera = GigE_camera("id14b-prosilica4.cars.aps.anl.gov",
        use_multicast=False)
    self = camera # for debugging

    camera.start()    
    for i in range(0,20):
        image = camera.rgb_array
        I = float(sum(image))/image.size
        print "%d %s %8.2f" % (camera.has_image,camera.buffer_status,I)
        sleep(0.2)
    print camera.state
    
    i = 0 # for debugging


def test_GUI(): 
    from CameraViewer import CameraViewer
    import wx
    app = wx.PySimpleApp(redirect=False) # Needed to initialize WX library
    camera = GigE_camera("id14b-prosilica4.cars.aps.anl.gov")
    camera.use_multicast = True
    viewer = CameraViewer (camera,title="Microscope Test",name="Camera_Test",
        pixelsize=0.00465)
    app.MainLoop()

def test_framerate():
    camera = GigE_camera("id14b-prosilica4.cars.aps.anl.gov",
        use_multicast=False)
    self = camera # for debugging

    camera.start()
    sleep(2)
    print camera.state
    sleep(2)
    print camera.state
    print "StatFrameRate",camera.get_attr("StatFrameRate")

def test_single_image():
    from time import time
    from numpy import average,sum

    global camera,image,I
    
    camera = GigE_camera("id14b-prosilica4.cars.aps.anl.gov",
        use_multicast=False)
    camera.start()
    t = time()
    while not camera.has_image:
        if time()-t > 2.0 and not "started" in camera.state:
            print ("Prosilica image unreadable (%s)" % camera.state)
            break
        if time()-t > 5.0:
            print ("image acquistion timed out (%s)" % camera.state)
            break
        sleep(0.1)
    print "Status", camera.frames[0].Status,camera.frames[1].Status
    print "acquisition time %.3fs" % (time()-t)
    image = camera.rgb_array
    I = float(sum(image))/image.size
    print "average: %g counts/pixel" % I
    print "fraction of pixels >0: %g" % average(image != 0)
    

if __name__ == "__main__": ## for tseting
    camera = GigE_camera("pico3.niddk.nih.gov",use_multicast=False)
    self = camera
    print "camera.start()"
    print "camera.state"
