"""
Author: Friedrich Schotte
Date created: 2010-12-09
Date last modified: 2022-06-30
Revision comment: Using monitored_value_property
"""
__version__ = "1.1"

from monitored_value_property import monitored_value_property


class Dummy_Motor(object):
    name = "Dummy Motor"

    def __init__(self, *args, **kwargs):
        if len(args) > 0 and args[0]:
            self.name = args[0]

    def __repr__(self):
        return f"{self.class_name}({self.name!r})"

    @property
    def class_name(self):
        return type(self).__name__

    value = monitored_value_property(0.0)
    command_value = monitored_value_property(0.0)
    moving = monitored_value_property(False)
    readback_slop = monitored_value_property(False)
    unit = monitored_value_property("")

    def stop(self):
        pass


dummy_motor = Dummy_Motor()
