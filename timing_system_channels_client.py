"""
Author: Friedrich Schotte
Date created: 2022-03-28
Date last modified: 2022-08-03
Revision comment: Added: mnemonics
"""
__version__ = "1.1"

from cached_function import cached_function
from PV_record import PV_record
from collections.abc import MutableMapping
from PV_property import PV_property


@cached_function()
def timing_system_channels_client(timing_system, base_name="channels"):
    return Timing_System_Channels_Client(timing_system, base_name)


class Timing_System_Channels_Client(PV_record, MutableMapping):
    base_name = "channels"

    def __init__(self, timing_system, base_name):
        super().__init__(domain_name=timing_system.name)
        self.timing_system = timing_system
        self.base_name = base_name

    def __repr__(self):
        return f"{self.timing_system}.{self.base_name}"

    def __hash__(self): return hash(repr(self))

    @property
    def prefix(self):
        return f'{self.timing_system.prefix}.{self.base_name}'.upper()

    def __getitem__(self, i):
        from timing_system_channel_client import timing_system_channel_client
        return timing_system_channel_client(self.timing_system, f"channels{i + 1}")

    def __getattr__(self, name):
        if name.startswith("__") and name.endswith("__"):
            attribute = object.__getattribute__(self, name)
        else:
            from timing_system_channel_client import timing_system_channel_client
            attribute = timing_system_channel_client(self, name)
        return attribute

    def __len__(self):
        return len(self.names)

    def __contains__(self, name):
        return name in self.names

    def __iter__(self):
        for name in self.names:
            yield name

    def __setitem__(self, name, value):
        pass

    def __delitem__(self, name):
        pass

    def __dir__(self):
        return sorted(set(self.names + super().__dir__() + list(self.__dict__.keys())))

    names = PV_property(dtype=list)
    mnemonics = PV_property(dtype=list)


if __name__ == '__main__':
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = "BioCARS"
    from timing_system_client import timing_system_client

    timing_system = timing_system_client(domain_name)
    self = timing_system_channels_client(timing_system, "channels")

    print("self.xdet")
    print("self[0]")
