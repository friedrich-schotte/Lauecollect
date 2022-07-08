"""
Documentation:
HS High Speed Series X-ray Detector Manual by Ross A. Doyle and Justin Anderson
Chapter 8: Image Format (marccd), marccd Format Image Header Description, p. 50
File: Rayonix_HS_detector_manual-0.3a.pdf

Author: Friedrich Schotte
Date created: 2021-09-03
Date last modified: 2022-06-20
Revision comment: Fixed: Issue: timestamp not resetting to original when file closed
"""

__version__ = "2.8.2"

import logging

from rayonix_image_header_property import (
    packed_header_property,
    scaled_header_property,
    string_header_property,
    timestamp_header_property,
    optional_timestamp_header_property,
)
from date_time import date_time

logger = logging.getLogger(__name__)
if not logger.level:
    logger.level = logging.INFO


class rayonix_image:
    filename = ""
    header_size = 4096
    _header = None
    _data = None
    original_file_timestamp = 0
    original_file_timestamp_filename = ""

    def __init__(self, filename=None, shape=None, pixelsize=None):
        if filename is not None:
            self.open(filename)
        if shape is not None:
            self.shape = shape
        if pixelsize is not None:
            self.pixelsize = pixelsize

    def __repr__(self):
        return f"{type(self).__name__}({self.filename!r})"

    def __del__(self):
        # logging.debug(f"Closing {self}.")
        self.close()

    def __enter__(self): return self  # for "with" block

    def __exit__(self, exc_type, exc_value, exc_traceback): pass  # for "with" block

    @property
    def pixelsize(self): return self.pixelsize_x

    @pixelsize.setter
    def pixelsize(self, pixelsize):
        self.pixelsize_x = pixelsize
        self.pixelsize_y = pixelsize

    tiff_width = packed_header_property(18, 22, "<I")
    tiff_height = packed_header_property(30, 34, "<I")
    tiff_rows_per_strip = packed_header_property(102, 106, "<I")  # same as height

    rx_width = packed_header_property(1104, 1108, "<I")
    rx_height = packed_header_property(1108, 1112, "<I")
    strip_byte_count = packed_header_property(1116, 1120, "<I")  # width * 2

    xtal_to_detector = scaled_header_property(1664, 1668, "<I", 1000)  # mm
    beam_x = scaled_header_property(1668, 1672, "<I", 1000)  # pixels
    beam_y = scaled_header_property(1672, 1676, "<I", 1000)  # pixels
    integration_time = scaled_header_property(1676, 1680, "<I", 1000)  # s
    exposure_time = scaled_header_property(1680, 1684, "<I", 1000)  # s
    start_phi = scaled_header_property(1708, 1712, "<I", 1000)  # deg
    start_xtal_to_detector = scaled_header_property(1720, 1724, "<I", 1000)  # mm
    end_phi = scaled_header_property(1740, 1744, "<I", 1000)  # deg
    end_xtal_to_detector = scaled_header_property(1752, 1756, "<I", 1000)  # mm
    rotation_range = scaled_header_property(1760, 1764, "<I", 1000)  # deg

    pixelsize_x = scaled_header_property(1796, 1800, "<I", 1000000)  # mm
    pixelsize_y = scaled_header_property(1800, 1804, "<I", 1000000)  # mm

    source_wavelength = scaled_header_property(1932, 1936, "<I", 100000)  # A

    title = string_header_property(2048, 2176)
    header_filepath = string_header_property(2176, 2304)
    header_filename = string_header_property(2304, 2336)

    acquire_timestamp = timestamp_header_property(2368, 2400)
    header_timestamp = timestamp_header_property(2400, 2432)
    save_timestamp = timestamp_header_property(2432, 2464)

    optional_start_timestamp = optional_timestamp_header_property(3104, 3136)
    optional_end_timestamp = optional_timestamp_header_property(3136, 3168)

    @property
    def writable(self):
        writable = any([
            getattr(self._header, "writable", False),
            getattr(self._data, "mode", "r") == "r+",
        ])
        return writable

    @property
    def header(self):
        return self.get_header(ignore_error=False)

    @property
    def header_(self):
        return self.get_header(ignore_error=True, writable=False)

    def get_header(self, ignore_error=False, writable=True):
        from file_memory_map import File_Memory_Map
        if self.filename:
            if getattr(self._header, "filename", "") != self.filename or (writable and not getattr(self._header, "writable", False)):
                self.save_file_timestamp()
                try:
                    self._header = File_Memory_Map(self.filename, size=self.header_size, writable=writable)
                except (OSError, ValueError) as x:
                    if not ignore_error:
                        logger.error(f"{x}")
                    self._header = bytearray(self.header_size)
        else:
            if self._header is None:
                from rayonix_image_header import header
                self._header = bytearray(header)
                self.update_timestamps()
        return self._header

    @property
    def data(self):
        return self.get_data(mode="r+")

    @property
    def data_(self):
        return self.get_data(mode="r")

    def get_data(self, mode="r+"):
        if self.filename:
            if getattr(self._data, "filename", "") != self.filename or (mode == "r+" and not getattr(self._data, "mode", "r") == "r+"):
                from numpy import memmap, uint16
                self.save_file_timestamp()
                self._data = memmap(
                    self.filename,
                    dtype=uint16,
                    mode=mode,
                    offset=self.header_size,
                    shape=self.shape,
                    order='F',
                )
        else:
            if getattr(self._data, "shape", ()) != self.shape:
                from numpy import zeros, uint16
                self._data = zeros(self.shape, uint16)
        return self._data

    def close(self):
        restore_file_timestamp_needed = self.writable
        if hasattr(self._header, "close"):
            self._header.close()
        self._header = None
        self._data = None
        if restore_file_timestamp_needed:
            self.restore_file_timestamp()

    def save_file_timestamp(self):
        if not self.original_file_timestamp or self.original_file_timestamp_filename != self.filename:
            self.original_file_timestamp = self.file_timestamp
            self.original_file_timestamp_filename = self.filename

    def restore_file_timestamp(self):
        if self.original_file_timestamp and self.original_file_timestamp_filename == self.filename:
            self.file_timestamp = self.original_file_timestamp

    @property
    def file_timestamp(self):
        from os.path import getmtime
        refresh_NFS_cache(self.filename)
        try:
            file_timestamp = getmtime(self.filename)
        except OSError:
            file_timestamp = 0
        return file_timestamp

    @file_timestamp.setter
    def file_timestamp(self, file_timestamp):
        from os import utime
        from os.path import isfile
        if file_timestamp != self.file_timestamp:
            if file_timestamp and isfile(self.filename):
                logging.debug(f"Resetting timestamp of {self.filename!r} from {date_time(self.file_timestamp)} to {date_time(file_timestamp)}")
                try:
                    utime(self.filename, (file_timestamp, file_timestamp))
                except OSError as x:
                    logging.warning(f"Resetting timestamp of {self.filename!r} from {date_time(self.file_timestamp)} to {date_time(file_timestamp)}: {x}")

    def update_timestamps(self):
        from time import time
        timestamp = time()
        self.acquire_timestamp = timestamp
        self.header_timestamp = timestamp
        self.save_timestamp = timestamp

    def open(self, filename):
        self.filename = filename

    def save(self, filename):
        file = open(filename, "wb")
        file.write(self.header)
        file.write(self.data.tobytes())
        self.filename = filename

    @property
    def shape(self):
        return self.tiff_height, self.tiff_width

    @shape.setter
    def shape(self, shape):
        width, height = shape
        self.tiff_width = width
        self.tiff_height = height
        self.tiff_rows_per_strip = height
        self.rx_width = width
        self.rx_height = height
        self.strip_byte_count = width * 2

    @property
    def width(self):
        return self.shape[0]

    @property
    def height(self):
        return self.shape[1]

    def __getitem__(self, item):
        return self.data_[item]

    def __setitem__(self, item, value):
        self.data[item] = value
        return value


def refresh_NFS_cache(filename):
    from os.path import dirname
    from os import listdir
    directory = dirname(filename)
    try:
        _ = listdir(directory)
    except OSError:
        pass


if __name__ == "__main__":
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    # filename = "/net/femto-data2/C/Data/2021.07/WAXS/RNA-Poly-U12_Tramp_B-1/xray_images/RNA-Poly-U12_Tramp_B-1_0001_-16.000C_01.mccd"
    # filename = "/net/femto-data2/C/Data/2022.02/WAXS/Ca-CaM/Ca-CaM_PumpProbe_PC0-1/xray_images/Ca-CaM_PumpProbe_PC0-1_0001_-20us_01_-16.000C_01.mccd"
    # filename = "/net/femto-data2/C/Data/2022.03/WAXS/GB3/GB3_PumpProbe_PC0-1/xray_images/GB3_PumpProbe_PC0-1_0001_-10us_01_74.040C_01.mccd"
    # filename = "/mx340hs/data/anfinrud_2203/Data/WAXS/RNA-Dumbbell-8BP/RNA-Dumbell-8BP_PumpProbe_PC0-2/xray_images/RNA-Dumbell-8BP_PumpProbe_PC0-2_0001_-10us_01_95.040C_01.mccd"
    filename = "/net/femto-data2/C/Data/2021.11/Test/WAXS/Reference/Reference-1_A/xray_images/Reference-1_A_0002_02.mccd"
    print("self = rayonix_image(filename)")
    # print("self.save('/tmp/test.rx')")
    self = rayonix_image(filename)
