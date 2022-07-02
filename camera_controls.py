#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2021-06-16
Date last modified: 2021-06-16
Revision comment:
"""
__version__ = "1.0"

from cached_function import cached_function
from camera_control import camera_control


@cached_function()
def camera_controls(domain_name):
    return Camera_Controls(domain_name)


class Camera_Controls(object):
    def __init__(self, domain_name):
        self.domain_name = domain_name

    def __getattr__(self, name):
        return camera_control(self.domain_name+"."+name)