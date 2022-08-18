"""
Author: Friedrich Schotte
Date created: 2022-03-28
Date last modified: 2022-06-21
Revision comment: Fixed: Issue:
    2022-07-21 16:22:36,209 DEBUG Panel_3.start_monitoring: Subscribing to Dummy_Register(timing_system_client(domain_name='BioCARS'),'image_number').count
    2022-07-21 16:22:36,335 DEBUG Panel_3.start_monitoring: Subscribing to Dummy_Register(timing_system_client(domain_name='BioCARS'),'hlcnd').value
"""
__version__ = "1.0.3"

from PV_record import PV_record
from cached_function import cached_function
from collections.abc import MutableMapping
from PV_property import PV_property


@cached_function()
def timing_system_registers_client(timing_system, base_name="registers"):
    return Timing_System_Registers_Client(timing_system, base_name)


class Timing_System_Registers_Client(PV_record, MutableMapping):
    base_name = "registers"

    def __init__(self, timing_system, base_name):
        super().__init__(name=timing_system.name+"."+base_name)
        self.timing_system = timing_system
        self.basename_suffix = base_name

    def __repr__(self):
        return f"{self.timing_system}.{self.basename_suffix}"

    def __hash__(self): return hash(repr(self))

    def __getitem__(self, name):
        return self.register(name)

    def __getattr__(self, name):
        if name.startswith("__") and name.endswith("__"):
            return object.__getattribute__(self, name)

        return self.register(name)

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

    def register(self, name):
        from timing_system_register_client import timing_system_register_client
        return timing_system_register_client(self, name)

    names = PV_property("names", [])


if __name__ == '__main__':  # for testing
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = "BioCARS"
    from timing_system_client import timing_system_client

    timing_system = timing_system_client(domain_name)
    self = timing_system_registers_client(timing_system, "registers")

    print("self.image_number")
