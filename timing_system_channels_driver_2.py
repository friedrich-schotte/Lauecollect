"""
Author: Friedrich Schotte
Date created: 2022-03-30
Date last modified: 2022-07-29
Revision comment:
"""
__version__ = "2.0"

import logging
from alias_property import alias_property
from cached_function import cached_function
from collections.abc import MutableMapping


@cached_function()
def timing_system_channels_driver(timing_system):
    return Timing_System_Channels_Driver(timing_system)


class Timing_System_Channels_Driver(MutableMapping):
    def __init__(self, timing_system):
        self.timing_system = timing_system

    def __repr__(self):
        return f"{self.timing_system}.channels"

    @property
    def db_name(self):
        return f"{self.timing_system.db_name}"

    def __hash__(self):
        return hash(repr(self))

    def __getitem__(self, i):
        return self.channel(i)

    def __getattr__(self, name):
        if name.startswith("__") and name.endswith("__"):
            result = object.__getattribute__(self, name)
        elif name in self.names:
            i = self.mnemonics.index(name)
            result = self.channel(i)
        else:
            from timing_system_dummy_channel import dummy_channel
            result = dummy_channel(self.timing_system, name)
        return result

    def __len__(self):
        return 24

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
        from timing_system_channel_driver_2 import timing_system_channel_driver
        return timing_system_channel_driver(self, i)

    @property
    def mnemonics(self):
        return [channel.mnemonic for channel in self]

    names = alias_property("mnemonics")


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = "BioCARS"

    from timing_system_driver_9 import timing_system_driver
    timing_system = timing_system_driver(domain_name)
    self = timing_system_channels_driver(timing_system)

    print("self.xdet")
