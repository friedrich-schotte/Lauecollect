"""
Load an image and convert it into a numpy array for processing.

Author: Friedrich Schotte
Date created: 2013-09-04
Date last modified: 2021-08-10
Revision comment: Cleanup
"""
__version__ = "1.9.8"

from logging import debug, warning

import numpy

DEBUG = False


class numimage(numpy.ndarray):
    """An image represented as a 2D image numpy array."""
    from numpy import nan

    # "numimage" is a subclass of "recarray".
    # Because "recarray" uses a __new__ rather than an __init__ constructor,
    # __new__ rather than __init__ needs to be overridden.

    def __new__(cls, arg=None, filename="", dtype=numpy.float32, shape=(0, 0),
                file_format="", array=None, pixelsize=nan):
        """filename: TIFF,PNG,JPEG or GIF image."""
        # debug("numimage.__new__(%r,%r)" % (cls,filename))
        from numpy import zeros, ndarray, nan
        import numpy

        if isinstance(arg, str):
            filename = arg
        elif isinstance(arg, ndarray):
            array = arg
        elif isinstance(arg, tuple) and len(arg) == 2:
            shape = arg
        else:
            raise (RuntimeError, "%s: expecting str,array or (w,h)" % type(arg))

        info = {}

        self = None

        if filename:
            from normpath import normpath
            filename = normpath(filename)
            # A MAR CCD or Rayonix image is a TIFF image with NxN pixels,
            # depth 16 bit and a fixed-size 4096-byte TIFF header.
            # N = N_max/bin_factor
            # N_max = 7680 for MX340HS
            # N_max = 4096 for MAR CCD
            image_sizes = [3840, 1920, 960, 480, 2048, 1024, 512]  # pixels
            header_size = 4096  # bytes
            TIFF_header_size = 1024
            from os.path import getsize
            filesize = getsize(filename)
            for image_size in image_sizes:
                image_n_bytes = 2 * image_size ** 2
                if filesize == header_size + image_n_bytes:
                    file_format = "RX"
                    if DEBUG:
                        debug("using memmap")
                    from numpy import memmap, uint16, int32
                    self = memmap(filename, uint16, 'r', header_size, (image_size, image_size), 'F')
                    # Read TIFF header.
                    from struct import pack, unpack
                    header = open(filename, "rb").read(header_size)
                    offset, = unpack("I", header[4:8])
                    n_tags, = unpack("h", header[offset:offset + 2])
                    offset = offset + 2
                    size = 12

                    class tag:
                        def __init__(self, tag_type, dtype, length, data):
                            self.tag_type, self.dtype, self.length, self.data = tag_type, dtype, length, data

                        def __repr__(self):
                            return "%r,%r,%r,%r" % (self.tag_type, self.dtype, self.length, self.data)

                    tags = {}
                    for i in range(0, n_tags):
                        data = header[offset + i * size:offset + (i + 1) * size]
                        tag_type, dtype, length, data = unpack("<HHII", data)
                        tags[tag_type] = tag(tag_type, dtype, length, data)
                    res = nan
                    if 283 in tags:  # x resolution, tag_type rational, data = pointer
                        offset = tags[283].data
                        num, den = unpack("II", header[offset:offset + 8])
                        res = float(num) / den  # in dpi
                        if DEBUG:
                            debug("TIFF: 283: resolution num/den %r/%r=%g" % (num, den, res))
                    unit = nan
                    if 296 in tags:  # resolution unit, code 2 = inch, 3 = cm
                        code = tags[296].data
                        if code == 2:
                            unit = 25.4  # inch
                        elif code == 3:
                            unit = 10  # cm
                        if DEBUG:
                            debug("TIFF: 296: resolution unit %r = %r mm" % (code, unit))
                    pixelsize = unit / res
                    if DEBUG:
                        debug("TIFF: pixelsize (%r mm)/%g = %.6f mm" % (unit, res, pixelsize))
                    # Rayonix High Speed Detector Manual v. 0.3, Ross Doyle, Justin Anderson
                    # Chapter 8: Image Format (marccd)
                    # Rayonix_HS_detector_manual-0.3a.pdf
                    start = TIFF_header_size + 193 * 4
                    end = start + 4
                    if DEBUG:
                        debug("RX: pixelsize [nm]: header[%r:%r] = %r" % (start, end, header[start:end]))
                    frame_header = memmap(filename, dtype=int32, mode='r', offset=TIFF_header_size,
                                          shape=(header_size - TIFF_header_size,), order='F')
                    pixelsize_nm = frame_header[193]
                    pixelsize = pixelsize_nm * 1e-9 / 1e-3  # convert from nm to mm
                    if DEBUG:
                        debug("RX: int 193: pixelsize = %r nm = %.6f mm" % (pixelsize_nm, pixelsize))
            if self is None:
                if filename.upper().endswith(".EDF"):
                    w = 0
                    h = 0
                    header = open(filename).read(1024)
                    header_size = header.find("}\n") + 2
                    header = header[0:header_size]
                    lines = header.split("\n")
                    for line in lines:
                        line = line.strip(" ;")
                        if line.startswith("Dim_1 = "):
                            w = int(line.replace("Dim_1 = ", ""))
                        if line.startswith("Dim_2 = "):
                            h = int(line.replace("Dim_2 = ", ""))
                    from numpy import memmap, uint16, int32
                    self = memmap(filename, uint16, 'r', header_size, (w, h), 'F')
                    file_format = "EDF"
                else:
                    from PIL import Image
                    from numpy import uint8, uint16, uint32, float32
                    PIL_image = Image.open(filename)
                    mode = PIL_image.mode
                    # PIL_image = PIL_image.convert("I")
                    if mode == "1":
                        self = numpy.array(PIL_image, bool).T
                    elif mode == "I;8":
                        self = numpy.array(PIL_image, uint8).T
                    elif mode == "I;16":
                        self = numpy.array(PIL_image, uint16).T
                    elif mode == "I;32":
                        self = numpy.array(PIL_image, uint32).T
                    elif mode == "F;32":
                        self = numpy.array(PIL_image, float32).T
                    else:
                        warning("Unknown data type %s" % mode)
                    file_format = PIL_image.format
                    info = PIL_image.info
                    if "dpi" in info:
                        pixelsize = 25.4 / info["dpi"][0]  # convert from DPI to mm
        elif array is not None:
            self = array
        else:
            self = zeros(shape, dtype)

        self = self.view(cls)
        self.filename = filename
        self.format = file_format
        self.info = info
        self.pixelsize = pixelsize
        return self

    def __array_finalize__(self, x):
        """Called after an object has been copied.
        Passes non-array attributes from the original to the new 
        object."""
        from numpy import nan
        self.filename = getattr(x, "filename", "")
        self.format = getattr(x, "file_format", "")
        self.info = getattr(x, "info", {})
        self.pixelsize = getattr(x, "pixelsize", nan)

    def get_width(self):
        return self.shape[0]

    width = property(get_width)

    def get_height(self):
        return self.shape[1]

    height = property(get_height)

    def save(self, filename=None, file_format=""):
        from numpy import array, uint16, uint32, uint8, rint, clip, nan_to_num, nanmax, isnan
        from PIL import Image
        from os.path import splitext, dirname
        from os import makedirs
        if filename is not None:
            self.filename = filename
        directory = dirname(self.filename)
        if directory:
            try:
                makedirs(directory)
            except OSError:
                pass
        if file_format == "":
            file_format = self.format
        file_format = file_format.upper()
        if file_format == "":
            file_format = splitext(self.filename)[-1].strip(".").upper()
            if file_format == "TIF":
                file_format = "TIFF"
            if file_format == "":
                file_format = self.format
        if file_format in ("TIFF", "TIF"):
            if nanmax(self) > 255:
                data_16bit = array(clip(nan_to_num(rint(self)), 0, 65535), uint16)
                PIL_image = Image.fromarray(data_16bit.T, "I;16")
            elif nanmax(self) > 1:
                data_8bit = array(clip(nan_to_num(rint(self)), 0, 255), uint8)
                PIL_image = Image.fromarray(data_8bit.T, "L")
            else:
                # When converting 8-bit to 1-bit, the threshold is 128.
                data_8bit = array(clip(nan_to_num(rint(self)), 0, 1) * 255, uint8)
                PIL_image = Image.fromarray(data_8bit.T, "L").convert("1")
            if not isnan(self.pixelsize):
                dpi = 25.4 / self.pixelsize
                PIL_image.info["dpi"] = (dpi, dpi)
            # PIL only generates uncompressed TIFF image. There are no options.
            PIL_image.save(self.filename, file_format)
        elif file_format in ("MCCD", "RX", "RAYONIX"):
            # Rayonix images have a 4096-byte TIFF-compatible header,
            # with a custom non-standard tag containing diffractometer
            # information (phi angle, oscillation range, detector distance...).
            # The program "ADXV" reads only images with Rayonix header,
            # not plain TIFF images.
            from rayonix_image_header import header  # for size 1920x1920
            # Update header for current image size:
            # offset   18: width (4-byte little-endian integer)
            # offset   30: height (4-byte integer)
            # offset  102: rows per strip (=height) (4-byte integer)
            # offset 1104: width (4-byte integer)
            # offset 1108: height (4-byte integer)
            # offset 1116: strip byte count (4-byte integer)
            w, h = self.shape
            from struct import pack
            width, height = pack("<I", w), pack("<I", h)
            rows_per_strip = height
            strip_byte_count = pack("<I", w * 2)
            # Convert pixel size from mm to nm.
            pixelsize_nm = to_int(rint(self.pixelsize * 1e-3 / 1e-9))
            # if DEBUG: debug("pixelsize [nm] = %r" % pixelsize_nm)
            pixelsize = pack("<I", pixelsize_nm)
            # if DEBUG: debug("pixelsize [nm] = %r" % pixelsize)
            from time import time
            t = time()
            from datetime import datetime
            timestamp = datetime.fromtimestamp(t).strftime("%m%d%H%M%Y.%S %f") \
                .encode("ASCII").replace(b" ", b"\0").ljust(32, b"\0")
            acquire_timestamp = header_timestamp = save_timestamp = timestamp
            header = \
                header[0:  18] + width + \
                header[22:  30] + height + \
                header[34: 102] + rows_per_strip + \
                header[106:1104] + width + height + \
                header[1112:1116] + strip_byte_count + \
                header[1120:1796] + pixelsize + \
                header[1800:2048 + 320] + acquire_timestamp + \
                header_timestamp + \
                save_timestamp + \
                header[2048 + 416:]
            # Convert image to 16-bit depth
            data_16bit = array(clip(nan_to_num(rint(self)), 0, 65535), uint16)
            image_data = header + data_16bit.tobytes()
            open(self.filename, "wb").write(image_data)
        else:  # e.g. PNG
            if nanmax(self) > 255:
                # PNG driver of PIL does not support mode I;16 but I (32-bit)
                data_32bit = array(clip(nan_to_num(rint(self)), 0, 2 ** 32 - 1), uint32)
                PIL_image = Image.fromarray(data_32bit.T, "I")
            elif nanmax(self) > 1:
                data_8bit = array(clip(nan_to_num(rint(self)), 0, 255), uint8)
                PIL_image = Image.fromarray(data_8bit.T, "L")
            else:
                # When converting 8-bit to 1-bit, the threshold is 128.
                data_8bit = array(clip(nan_to_num(rint(self)), 0, 1) * 255, uint8)
                PIL_image = Image.fromarray(data_8bit.T, "L").convert("1")
            # Optimize = True: the PNG output driver will try different
            # output filters to achieve the optimal compression.
            PIL_image.save(self.filename, file_format, optimize=True)
        self.format = file_format

    write = save


def to_int(x):
    """Convert x to an integer value without throwing an exception"""
    try:
        return int(x)
    except (ValueError, TypeError):
        return 0


if __name__ == "__main__":  # for testing
    from numpy import uint16

    # import logging; logging.basicConfig(level=logging.DEBUG)
    size = 1920
    pixelsize = 0.08
    self = numimage((size, size), dtype=uint16, pixelsize=pixelsize)
    filename = "/afp/femto-data2/C/Data/2021.07/WAXS/RNA-Poly-U12_Tramp_PC2-1/xray_images/RNA-Poly-U12_Tramp_PC2-1_0003_-16.000C_01.mccd"
    temp_filename = "/tmp/test.mccd"
    print('filename = %r' % filename)
    print('temp_filename = %r' % temp_filename)
    print('')
    print('self = numimage(filename)')
    print('self.save(temp_filename)')
