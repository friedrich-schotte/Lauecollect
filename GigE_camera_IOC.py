#!/usr/bin/env python
"""
Server for Prosilica GigE CCD cameras

Configuration:
    set_defaults()

Author: Friedrich Schotte
Date created: 2020-03-16
Date last modified: 2021-01-11
Revision comment: Issue: always simulated
"""
__version__ = "1.2.3"

from cached_function import cached_function
from IOC_single_threaded import IOC


@cached_function()
def camera_ioc(name, simulated=False):
    return Camera_IOC(name, simulated)


class Camera_IOC(IOC):
    from GigE_camera import GigE_camera
    from GigE_camera_simulator import GigE_camera_simulator

    def __init__(self, name, simulated=False):
        if simulated:
            self.camera = self.GigE_camera_simulator(name)
        else:
            self.camera = self.GigE_camera(name)

        self.add_idle_handler(0.05, self.resume)

    def __repr__(self):
        return f"{self.class_name}({self.name!r}, simulated={self.simulated})"

    @property
    def class_name(self):
        return type(self).__name__.lower()

    default_scan_period = 10.0

    @property
    def prefix(self):
        return "NIH:CAMERA.%s." % self.name.upper()

    @property
    def simulated(self):
        return self.camera_type != self.GigE_camera

    @simulated.setter
    def simulated(self, simulated):
        if simulated != self.simulated:
            if simulated:
                self.camera_type = self.GigE_camera_simulator
            else:
                self.camera_type = self.GigE_camera

    def get_camera_type(self):
        return type(self.camera)

    def set_camera_type(self, camera_type):
        if camera_type != self.camera_type:
            self.camera = camera_type(self.name)

    camera_type = property(get_camera_type, set_camera_type)

    def resume(self):
        self.camera.resume()

    property_names = [
        "rgb_array_flat",
        "acquiring",
        "IP_addr",
        "state",
        "width",
        "height",
        "frame_count",
        "timestamp",
        "has_image",
        "exposure_time",
        "auto_exposure",
        "use_multicast",
        "external_trigger",
        "pixel_formats",
        "pixel_format",
        "gain",
        "bin_factor",
        "stream_bytes_per_second",
    ]
    from alias_property import alias_property
    name = alias_property("camera.name")

    monitor = alias_property("camera.monitor")
    monitor_clear = alias_property("camera.monitor_clear")

    rgb_array_flat = alias_property("camera.rgb_array_flat")
    acquiring = alias_property("camera.acquiring")
    IP_addr = alias_property("camera.IP_addr")
    state = alias_property("camera.state")
    width = alias_property("camera.width")
    height = alias_property("camera.height")
    frame_count = alias_property("camera.frame_count")
    timestamp = alias_property("camera.timestamp")
    has_image = alias_property("camera.has_image")
    exposure_time = alias_property("camera.exposure_time")
    auto_exposure = alias_property("camera.auto_exposure")
    use_multicast = alias_property("camera.use_multicast")
    external_trigger = alias_property("camera.external_trigger")
    pixel_formats = alias_property("camera.pixel_formats")
    pixel_format = alias_property("camera.pixel_format")
    gain = alias_property("camera.gain")
    bin_factor = alias_property("camera.bin_factor")
    stream_bytes_per_second = alias_property("camera.stream_bytes_per_second")


def run(name, simulated=False):
    camera_ioc(name, simulated).run()


def start(name, simulated=False):
    camera_ioc(name, simulated).start()


def stop(name, simulated=False):
    camera_ioc(name, simulated).start()


def set_defaults():
    from DB import dbset
    dbset("GigE_camera.WideFieldCamera.camera.IP_addr", "pico3.niddk.nih.gov")
    dbset("GigE_camera.MicroscopeCamera.camera.IP_addr", "pico14.niddk.nih.gov")
    dbset("GigE_camera.Microscope.camera.IP_addr", 'pico22.niddk.nih.gov')
    dbset("GigE_camera.MicrofluidicsCamera.camera.IP_addr", 'femto5.niddk.nih.gov')
    dbset("GigE_camera.LaserLabCamera.camera.IP_addr", "femto9.niddk.nih.gov")
    dbset("GigE_camera.TestBenchCamera.camera.IP_addr", "femto9.niddk.nih.gov")


if __name__ == "__main__":
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)
    # logging.getLogger("EPICS_CA").level = logging.DEBUG

    # self = camera_ioc("MicroscopeCamera", simulated=False)
    # self = camera_ioc("LaserLabCamera", simulated=True)
    self = camera_ioc("LaserLabCamera", simulated=False)

    print(f'self.name = {self.name}')
    print(f'self.simulated = {self.simulated}')
    # print('camera_ioc.acquiring = True')
    print('')
    print(f'start({self.name!r}, simulated={self.simulated})')
    print('')

    print('from CA import caget; caget("%sSTATE")' % self.prefix)
    print('from CA import caput; caput("%sACQUIRING",1)' % self.prefix)
