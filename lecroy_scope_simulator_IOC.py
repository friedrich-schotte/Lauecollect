"""
Author: Friedrich Schotte
Date created: 2021-07-15
Date last modified: 2021-07-15
Revision comment:
"""
__version__ = "1.0"

from cached_function import cached_function
from IOC_auto_hierarchical import IOC


@cached_function()
def lecroy_scope_simulator_ioc(name): return Configuration_IOC(name)


class Configuration_IOC(IOC):
    name = "BioCARS"
    object_class_name = ""

    def __init__(self, name=None):
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
        from lecroy_scope_simulator import lecroy_scope_simulator
        return lecroy_scope_simulator(self.name)


def run(name): lecroy_scope_simulator_ioc(name).run()


def start(name): lecroy_scope_simulator_ioc(name).start()


def stop(name): lecroy_scope_simulator_ioc(name).stop()


if __name__ == "__main__":
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    name = "BioCARS.xray_scope"
    # name = "BioCARS.laser_scope"
    # name = "BioCARS.diagnostics_scope"
    # name = "LaserLab.laser_scope"

    self = lecroy_scope_simulator_ioc(name)

    print(f'start({name!r})')
    print('')
    print('from CA import caget')
    print(f'caget("{self.prefix}ACQUIRING_WAVEFORMS")')
