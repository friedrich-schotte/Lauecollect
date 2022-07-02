"""
Author: Friedrich Schotte
Date created: 2022-04-05
Date last modified: 2022-04-10
Revision comment:
"""
__version__ = "1.0"

from cached_function import cached_function

from timing_system_dummy_register import dummy_register


@cached_function()
def dummy_channel(timing_system, count):
    return Dummy_Channel(timing_system, count)


class Dummy_Channel(object):
    def __init__(self, timing_system, name):
        """name:  channel
        """
        self.timing_system = timing_system
        self.name = name

    def __repr__(self):
        return "%s(%r,%r)" % (type(self).__name__, self.timing_system, self.name)

    @property
    def delay(self):
        return dummy_register(self.timing_system, self.register_name("delay"))

    @property
    def fine(self):
        return dummy_register(self.timing_system, self.register_name("file"))

    @property
    def enable(self):
        return dummy_register(self.timing_system, self.register_name("enable"))

    @property
    def state(self):
        return dummy_register(self.timing_system, self.register_name("state"))

    @property
    def pulse(self):
        return dummy_register(self.timing_system, self.register_name("pulse"))

    @property
    def input(self):
        return dummy_register(self.timing_system, self.register_name("input"))

    @property
    def override(self):
        return dummy_register(self.timing_system, self.register_name("override"))

    @property
    def override_state(self):
        return dummy_register(self.timing_system, self.register_name("override_state"))

    @property
    def trig_count(self):
        return dummy_register(self.timing_system, self.register_name("trig_count"))

    @property
    def acq_count(self):
        return dummy_register(self.timing_system, self.register_name("acq_count"))

    @property
    def acq(self):
        return dummy_register(self.timing_system, self.register_name("acq"))

    @property
    def specout(self):
        return dummy_register(self.timing_system, self.register_name("specout"))

    def register_name(self, name):
        """name: e.g. "state","delay" """
        return "%s_%s" % (self.name, name)

    stepsize = 0.0
    offset = 0.0
    pulse_length = 0.0
