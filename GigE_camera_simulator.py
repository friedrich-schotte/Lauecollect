#!/usr/bin/env python
"""
Simulator for Prosilica GigE CCD cameras.
Author: Friedrich Schotte
Date created: 2020-05-07
Date last modified: 2022-07-19
Revision comment: Cleanup: logging, f-strings
"""
__version__ = "1.0.8"

import warnings
import logging


class GigE_camera_simulator(object):
    from persistent_property_new import persistent_property
    from db_property import db_property

    IP_addr = persistent_property("GigE_camera.{name}.camera.IP_addr",
                                  "pico3.niddk.nih.gov")

    width = db_property("width", 1360)
    height = db_property("height", 1024)

    manual_exposure_time = db_property("exposure_time", 1.0)
    auto_exposure = db_property("auto_exposure", True)
    use_multicast = db_property("GigE_camera.{name}.use_multicast", False)
    external_trigger = db_property("external_trigger", False)
    pixel_format = db_property("pixel_format", "Bayer8")
    gain = db_property("gain", 0)
    bin_factor = db_property("bin_factor", 1)
    stream_bytes_per_second = db_property("stream_bytes_per_second", 11250000)

    def __init__(self, name="Camera"):
        """name: used to store persistent properties"""
        self.name = name
        from repeated_timer import repeated_timer
        self.frame_timer = repeated_timer(self.frame_period, self.handle_frame_timer)
        self.frame_count = 0
        self.timestamp = 0.0
        self.handlers = {}
        self.rgb_array = self.default_rgb_array

    def __repr__(self):
        return f"{self.class_name}({self.name!r})"

    @property
    def db_name(self):
        return f"domains/{self.domain_name}/{self.class_name}/{self.base_name}"

    @property
    def class_name(self):
        return type(self).__name__

    @property
    def domain_name(self):
        domain_name = "BioCARS"
        if "." in self.name:
            domain_name = self.name.split(".", 1)[0]
        return domain_name

    @property
    def base_name(self):
        return self.name.split(".", 1)[-1]

    def get_acquiring(self):
        return self.frame_timer.running

    def set_acquiring(self, acquiring):
        acquiring = bool(acquiring)
        if acquiring != self.acquiring:
            if acquiring:
                self.frame_count = 0
        self.frame_timer.interval = self.frame_period
        self.frame_timer.running = acquiring

    acquiring = property(get_acquiring, set_acquiring)

    def handle_frame_timer(self):
        self.frame_timer.interval = self.frame_period
        self.update_image()
        self.frame_count += 1
        from time import time
        self.timestamp = time()
        self.handle_frame_update()

    def handle_frame_update(self):
        from time import time
        self.handle_updates(self.frame_properties, time())

    frame_properties = [
        "frame_count",
        "rgb_array",
        "rgb_array_flat",
        "state",
        "timestamp",
        "has_image",
        "exposure_time",
    ]

    def handle_updates(self, property_names, time):
        for property_name in property_names:
            self.handle_update(property_name, time)

    def handle_update(self, property_name, time):
        event = self.event(property_name, time)
        self.__getattr_monitors__(property_name).call(event=event)

    def event(self, property_name, time):
        from event import Event
        from reference import reference
        event = Event(
            time=time,
            value=getattr(self, property_name),
            reference=reference(self, property_name)
        )
        return event

    def __getattr_monitors__(self, property_name):
        if property_name not in self.handlers:
            from event_handlers import Event_Handlers
            self.handlers[property_name] = Event_Handlers()
        return self.handlers[property_name]

    def update_image(self):
        self.rgb_array = self.simulated_image

    @property
    def simulated_image(self):
        """Image as 3D numpy array. Dimensions: 3xWxH, data type: uint8
        Usage R,G,B = image
        """
        from numpy import uint8
        image = noise(1, shape=(3, self.width, self.height), dtype=uint8)
        return image

    @property
    def default_rgb_array(self):
        """Image as 3D numpy array. Dimensions: 3xWxH, data type: uint8
        Usage R,G,B = image
        """
        from numpy import zeros, uint8
        image = zeros((3, self.width, self.height), uint8)
        return image

    @property
    def rgb_array_flat(self):
        """Last read image as 1D numpy array.
        Size: 1360 * 1024 * 3 = 4177920, data type: int8
        (int8 rather than uint8 for compatibility with EPICS CA array PVs)
        """
        from numpy import int8
        return self.rgb_array.T.flatten().astype(int8)

    @property
    def rgb_data(self):
        return self.rgb_array_flat.tobytes()

    @property
    def state(self):
        """Single line status message"""
        state = ""
        state += self.mode
        if self.capturing:
            state += ", capturing"
            if self.external_trigger:
                state += " (ext. trig.)"
        elif self.acquiring:
            state += ", started"
        if self.capturing and self.frame_count > 0:
            state += (", %.3g fps" % self.framerate)
            state += (", #%d" % self.frame_count)
        state += ", " + self.pixel_format
        if self.pixel_format not in ["Bayer8", "Rgb24"]:
            state += ", unsupported format"
        return state

    @property
    def has_image(self):
        return self.frame_count > 0

    mode = "control"

    @property
    def capturing(self):
        return self.acquiring

    @property
    def framerate(self):
        from numpy import nan
        dt = self.frame_period
        framerate = 1 / dt if dt != 0 else nan
        return framerate

    @property
    def frame_period(self):
        return max([
            self.exposure_time,
            self.min_frame_period,
        ])

    def get_exposure_time(self):
        if self.auto_exposure:
            exposure_time = 0.5
        else:
            exposure_time = self.manual_exposure_time
        return exposure_time

    def set_exposure_time(self, exposure_time):
        self.auto_exposure = False
        self.manual_exposure_time = exposure_time

    exposure_time = property(get_exposure_time, set_exposure_time)

    @property
    def min_frame_period(self):
        period = self.bytes_per_image / self.stream_bytes_per_second
        return period

    @property
    def bytes_per_image(self):
        return self.width * self.height * self.bytes_per_pixel

    @property
    def bytes_per_pixel(self):
        return self.pixel_format_bytes(self.pixel_format)

    def pixel_format_bytes(self, pixel_format):
        return self.pixel_bytes.get(pixel_format, 1)

    @property
    def pixel_formats(self):
        return list(self.pixel_bytes.keys())

    pixel_bytes = {
        "Mono8": 1,
        "Mono16": 2,
        "Bayer8": 1,
        "Bayer16": 2,
        "Rgb24": 3,
        "Rgb48": 6,
        "Yuv411": 1,
        "Yuv422": 8,
        "Yuv444": 2,
        "Bgr24": 3,
        "Rgba32": 4,
        "Bgra32": 4
    }

    def resume(self):
        pass

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


GigE_camera = GigE_camera_simulator


def noise(average, shape, dtype=int):
    """Simulated shot noise"""
    from numpy import product
    size = product(shape)
    from numpy.random import poisson
    from numpy import ceil, tile
    block_size = 40000
    block_count = int(ceil(float(size) / block_size))
    block = poisson(average, block_size).astype(dtype)
    noise = tile(block, block_count)[0:size]
    noise = noise.reshape(shape)
    return noise


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")
    camera = GigE_camera_simulator("MicroscopeCamera")
    self = camera
    print(f"camera.IP_addr = {camera.IP_addr!r}")
    print("camera.acquiring = True")
    print("camera.state")
    print('f"{camera.rgb_array_flat!r:.70}"')


    def report(name):
        logging.info(f"{name} = {getattr(camera, name)!r:.70}")


    print("camera.monitor('state',report,'state')")
    print("camera.monitor_clear('state',report,'state')")
    print("camera.monitor('rgb_array_flat',report,'rgb_array_flat')")
