"""
EPICS Input/Output Controller

Author: Friedrich Schotte
Date created: 2021-11-26
Date last modified: 2021-11-26
Revision comment:
"""
__version__ = "1.0"

from cached_function import cached_function
from IOC_auto_hierarchical import IOC


@cached_function()
def temperature_system_IOC(name): return Temperature_System_IOC(name)


class Temperature_System_IOC(IOC):
    name = "BioCARS"

    def __init__(self, name):
        super().__init__()
        if name is not None:
            self.name = name

    def __repr__(self):
        return f"{self.class_name}({self.name!r})"

    @property
    def class_name(self):
        return type(self).__name__.lower()

    @property
    def object(self):
        from temperature_system_driver import temperature_system
        return temperature_system(self.name)


def run(name): temperature_system_IOC(name).run()


def start(name): temperature_system_IOC(name).start()


def stop(name): temperature_system_IOC(name).stop()


if __name__ == "__main__":
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    from handler import handler as _handler
    from CA import PV

    name = "BioCARS"

    self = temperature_system_IOC(name)


    @_handler
    def report(event): logging.info(f"event={event}")


    pv = PV(f"{self.prefix}RBV")

    print('start(name)')
    # start(name)

    print(f'pv.value')
