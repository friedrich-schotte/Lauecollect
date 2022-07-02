#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2020-12-22
Date last modified: 2020-12-22
Revision comment:
"""
__version__ = "1.0"

from cached_function import cached_function


@cached_function
def configuration_property(configuration, name):
    return Configuration_Property(configuration, name)


class Configuration_Property(object):
    """Usage example: SAXS_WAXS_methods.passes_per_image.value"""

    def __init__(self, configuration, name):
        self.configuration = configuration
        self.name = name

    def get_value(self):
        return self.configuration.motor[self.motor_num].current_position

    def set_value(self, value):
        self.configuration.motor[self.motor_num].current_position = value

    value = property(get_value, set_value)

    def get_command_value(self):
        return self.configuration.motor[self.motor_num].nominal_position

    command_value = property(get_command_value, set_value)

    @property
    def motor_num(self): return self.configuration.names.index(self.name)

    def __repr__(self): return "%r.%s" % (self.configuration, self.name)
