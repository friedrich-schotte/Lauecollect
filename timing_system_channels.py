"""
Author: Friedrich Schotte
Date created: 2022-03-30
Date last modified: 2022-07-17
Revision comment: Addressed Issue:
    alias_property.py, line 104, in attributes
    if name not in attributes_cache:
    TypeError: argument of type 'Dummy_Channel' is not iterable
"""
__version__ = "1.0.2"

import logging
from alias_property import alias_property
from cached_function import cached_function
from collections.abc import MutableMapping


@cached_function()
def timing_system_channels(timing_system):
    return Timing_System_Channels(timing_system)


class Timing_System_Channels(MutableMapping):
    def __init__(self, timing_system):
        self.timing_system = timing_system

    def __repr__(self):
        return "%r.channels" % self.timing_system

    def __hash__(self):
        return hash(repr(self))

    def __getitem__(self, i):
        return self.channel(i)

    def __getattr__(self, name):
        if name.startswith("__") and name.endswith("__"):
            result = object.__getattribute__(self, name)
        elif name in self.names:
            i = self.timing_system.channel_mnemonics.index(name)
            result = self.channel(i)
        else:
            from timing_system_dummy_channel import dummy_channel
            result = dummy_channel(self.timing_system, name)
        return result

    def __len__(self):
        return self.timing_system.channels_count

    def __iter__(self):
        for i in range(0, len(self)):
            if i < len(self):
                yield self[i]

    def __setitem__(self, name, value):
        pass

    def __delitem__(self, name):
        pass

    def __dir__(self):
        return sorted(set(self.names + super().__dir__() + list(self.__dict__.keys())))

    def channel(self, i):
        from timing_system_channel import channel
        return channel(self.timing_system, i)

    names = alias_property("timing_system.channel_mnemonics")


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    from timing_system import timing_system

    domain_name = "BioCARS"
    self = timing_system_channels(timing_system(domain_name))

    print("self.xdet")
