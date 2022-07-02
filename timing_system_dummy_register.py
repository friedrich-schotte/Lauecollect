"""
Author: Friedrich Schotte
Date created: 2022-03-28
Date last modified: 2022-05-05
Revision comment:
"""
__version__ = "1.0"

from cached_function import cached_function


@cached_function()
def dummy_register(timing_system, name):
    return Dummy_Register(timing_system, name)


class Dummy_Register(object):
    def __init__(self, timing_system=None, name="dummy"):
        self.timing_system = timing_system
        self.name = name

    def __repr__(self):
        return "%s(%r,%r)" % (type(self).__name__, self.timing_system, self.name)

    description = ""
    address = 0
    bit_offset = 0
    bits = 0

    from monitored_value_property import monitored_value_property
    count = monitored_value_property(default_value=0)
    value = monitored_value_property(default_value=0.0)
    command_value = value

    min_count = 0
    max_count = 0
    stepsize = 0
    offset = 0
    PP_enabled = 0
