#!/usr/bin/env python
"""
Prosilica GigE CCD cameras.
Author: Friedrich Schotte
Python Version: 2.7, 3.6
Date created: 2020-04-02
Date last modified: 2021-06-18
Revision comment: Using db_property, domain_name
"""
__version__ = "3.4"

from logging import debug, warning


class Camera(object):
    from PV_property import PV_property
    from db_property import db_property
    from monitored_property import monitored_property
    from PV_info_property import PV_info_property

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.name)

    @property
    def name(self):
        return self.domain_name + "." + self.base_name

    @name.setter
    def name(self, value):
        if "." in value:
            self.domain_name, self.base_name = value.split(".", 1)
        else:
            self.domain_name, self.base_name = "BioCARS", value

    @property
    def default_prefix(self):
        prefix = f'NIH:CAMERA.{self.base_name}'
        # prefix = f'{self.domain_name}:CAMERA.{self.base_name}'
        prefix = prefix.upper()
        prefix = prefix.replace("BIOCARS:","NIH:")
        return prefix

    @property
    def db_name(self):
        return f"domains/{self.domain_name}/cameras/{self.base_name}"

    prefix = db_property("prefix", default_prefix)

    from numpy import zeros, int8
    rgb_array_flat = PV_property("rgb_array_flat", zeros(0, int8))
    camera_ip_address = PV_property("IP_addr", "")
    acquiring = PV_property("acquiring", False)
    state = PV_property("state", "Server offline")
    width = PV_property("width", 1360)
    height = PV_property("height", 1024)
    frame_count = PV_property("frame_count", 0)
    timestamp = PV_property("timestamp", 0.0)
    has_image = PV_property("has_image", False)
    exposure_time = PV_property("exposure_time", 0.0)
    auto_exposure = PV_property("auto_exposure", False)
    use_multicast = PV_property("use_multicast", False)
    external_trigger = PV_property("external_trigger", False)
    pixel_formats = PV_property("pixel_formats", [])
    pixel_format = PV_property("pixel_format", "")
    gain = PV_property("gain", 0)
    bin_factor = PV_property("bin_factor", 1)
    stream_bytes_per_second = PV_property("stream_bytes_per_second", 0)

    @monitored_property
    def RGB_array(self, rgb_array_flat, width, height):
        """Dimensions: (3, W, H) e.g. (3, 1360, 1024), datatype: uint8"""
        from numpy import uint8
        RGB_array = reshape(rgb_array_flat.view(uint8), (height, width, 3)).T
        return RGB_array

    server_ip_address = PV_info_property("pixel_format", "IP_address")

    bin_factors = ["1", "2", "4", "8"]

    camera_ip_addresses = [
        "id14b-prosilica1.cars.aps.anl.gov",
        "id14b-prosilica2.cars.aps.anl.gov",
        "id14b-prosilica3.cars.aps.anl.gov",
        "id14b-prosilica4.cars.aps.anl.gov",
        "id14b-prosilica5.cars.aps.anl.gov",
        "id14b-prosilica6.cars.aps.anl.gov",
        "pico3.niddk.nih.gov",
        "pico14.niddk.nih.gov",
        "pico22.niddk.nih.gov",
        "femto5.niddk.nih.gov",
        "femto9.niddk.nih.gov",
    ]

    # Camera Serial numbers:
    # 02-2131A-06331
    # 02-2131A-06353
    # 02-2131A-06043
    # 02-2131A-06108
    # 02-2131A-16516
    # 02-2131A-16519


def reshape(array, shape):
    """shape: (w,h,d)"""
    from numpy import product
    array = resize(array, product(shape)).reshape(shape)
    return array


def resize(array, size):
    if len(array) < size:
        if len(array) > 0:
            debug("Padding data from %d to %d bytes" % (len(array), size))
        from numpy import zeros, concatenate
        padding = zeros(size - len(array), array.dtype)
        array = concatenate([array, padding])
    if len(array) > size:
        warning("Truncating data from %d to %d bytes" % (len(array), size))
        array = array[0:size]
    return array


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s: %(message)s")

    from handler import handler as _handler
    from reference import reference as _reference

    self = Camera("BioCARS.MicroscopeCamera")
    # self = Camera("BioCARS.WideFieldCamera")
    # self = Camera("TestBench.Microscope")
    # self = Camera("TestBench.MicrofluidicsCamera")
    # self = Camera("LaserLab.LaserLabCamera")


    @_handler
    def report(event=None):
        logging.info(f"event={event}")


    _reference(self, "server_ip_address").monitors.add(report)
    print("self.server_ip_address")
    # print('camera.camera_ip_address')
    # print('camera.acquiring = True')
    # print('camera.state')
    # print('rgb_array_flat = camera.rgb_array_flat')
    # print('RGB_array = camera.RGB_array')
