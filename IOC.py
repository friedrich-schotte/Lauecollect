"""
EPICS Input/Output Controller

Usage:
from IOC import *; run('BioCARS.channel_archiver')

Author: Friedrich Schotte
Date created: 2022-03-04
Date last modified: 2022-06-16
Revision comment: logging
"""
__version__ = "2.2.2"

import logging

from cached_function import cached_function
import IOC_auto_hierarchical


@cached_function()
def ioc(name, module_suffix=None): return IOC(name, module_suffix)


class IOC(IOC_auto_hierarchical.IOC):
    name = "BioCARS"
    module_suffix = ""

    def __init__(self, name, module_suffix=None):
        """e.g. BioCARS.channel_archiver"""
        super().__init__()
        self.name = name
        if module_suffix is not None:
            self.module_suffix = module_suffix

    def __repr__(self):
        if self.module_suffix:
            name = f"{self.class_name}({self.name!r}, {self.module_suffix!r})"
        else:
            name = f"{self.class_name}({self.name!r})"
        return name

    @property
    def domain_name(self):
        return self.name.split(".")[0]

    @property
    def object_base_name(self):
        name = self.name.replace(self.domain_name, "", 1).strip(".")
        name = name.split(".")[0]
        return name

    @property
    def object_class_name(self):
        return self.object_base_name

    @property
    def base_name(self):
        name = self.name
        name = name.replace(self.domain_name, "", 1).strip(".")
        name = name.replace(self.object_base_name, "", 1).strip(".")
        return name

    def start(self):
        if hasattr(self.object, "start"):
            logging.debug(f"{self.object}.start()")
            self.object.start()
        if hasattr(self.object, "running"):
            logging.debug(f"{self.object}.running = True")
            self.object.running = True
        super().start()

    def stop(self):
        if hasattr(self.object, "stop"):
            logging.debug(f"{self.object}.stop()")
            self.object.stop()
        if hasattr(self.object, "running"):
            logging.debug(f"{self.object}.running = False")
            self.object.running = False
        super().stop()

    @property
    def object(self):
        return self.object_type(self.object_name)

    @property
    def object_type(self):
        return getattr(self.object_module, self.object_type_name)

    @property
    def object_name(self):
        if self.base_name:
            name = f"{self.domain_name}.{self.base_name}"
        else:
            name = self.domain_name
        return name

    @property
    def object_module(self):
        return __import__(self.object_module_name)

    @property
    def object_module_name(self):
        base_name = self.object_base_name
        name = base_name+"_driver"
        if self.module_suffix:
            name += "_" + self.module_suffix
        return name

    @property
    def object_type_name(self):
        return self.object_class_name+"_driver"

    @property
    def class_name(self):
        return type(self).__name__.lower()


def run(name, module_suffix=None): ioc(name, module_suffix).run()


def start(name, module_suffix=None): ioc(name, module_suffix).start()


def stop(name, module_suffix=None): ioc(name, module_suffix).stop()


if __name__ == "__main__":
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    from handler import handler as _handler
    from CA import PV

    # name = "BioCARS.rayonix_detector"
    # name = "BioCARS.timing_system"
    name = 'BioCARS.configuration.method'
    module_suffix = "new"
    # module_suffix = None

    self = ioc(name, module_suffix)


    @_handler
    def report(event): logging.info(f"event={event}")


    pv = PV(f"{self.prefix}ONLINE")

    print('start(name, module_suffix)')
    # start(name, module_suffix)

    print(f'pv.value')
