"""
Author: Friedrich Schotte
Date created: 2021-06-19
Date last modified: 2021-06-19
Revision comment:
"""
__version__ = "1.0"

from camera_control import camera_control


class Cameras(object):
    def __getattr__(self, name): return camera_control(name)


cameras = Cameras()