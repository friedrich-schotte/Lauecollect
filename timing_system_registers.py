"""
Author: Friedrich Schotte
Date created: 2022-03-30
Date last modified: 2022-07-17
Revision comment: Made monitored_property: names
"""
__version__ = "1.0.2"

from alias_property import alias_property
from cached_function import cached_function


@cached_function()
def timing_system_registers(timing_system):
    return Timing_System_Registers(timing_system)


class Timing_System_Registers:
    def __init__(self, timing_system):
        self.timing_system = timing_system

    def __repr__(self):
        return "%r.registers" % self.timing_system

    def __hash__(self):
        return hash(repr(self))

    def __getattr__(self, name):
        if name == "__members__":
            attribute = self.names
        elif name.startswith("__") and name.endswith("__"):
            attribute = object.__getattribute__(self, name)
        elif name == "shape":
            raise AttributeError(f"'{type(self).__name__}' object has no attribute {name!r}")
        else:
            attribute = self.register(name)
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

    def register(self, name):
        if name in self.names:
            from timing_system_register import register
            reg = register(self.timing_system, name)
        else:
            from timing_system_dummy_register import dummy_register
            reg = dummy_register(self.timing_system, name)
        return reg

    names = alias_property("timing_system.all_register_names")


if __name__ == '__main__':  # for testing
    import logging
    from timing_system import timing_system

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = "BioCARS"
    self = timing_system_registers(timing_system(domain_name))

    print("self.image_number")
